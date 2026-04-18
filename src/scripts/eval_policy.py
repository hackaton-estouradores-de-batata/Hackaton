from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
API_DIR = ROOT_DIR / "src" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.agreement_policy_v5 import (  # noqa: E402
    PolicyCaseInputV5,
    calculate_policy_v5,
    classify_micro_result_economic,
    micro_result_rules_payload,
    normalize_sub_assunto_v5,
    resolve_policy_backtest_cost,
)

CSV_PATH = ROOT_DIR / "data" / "sentencas_60k.csv"
PROCESSO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "processo" in name.lower()
)
UF_COLUMN = "UF"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"
VALOR_CONDENACAO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "indeniza" in name.lower()
)

CENTS = Decimal("0.01")


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def parse_decimal(value: Any) -> Decimal | None:
    normalized = normalize_text(str(value or "")).replace(",", ".")
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def parse_scenarios(raw: str) -> list[int]:
    if raw.strip().lower() == "all":
        return list(range(7))

    scenarios: list[int] = []
    for chunk in raw.split(","):
        cleaned = chunk.strip()
        if not cleaned:
            continue
        value = int(cleaned)
        if value < 0 or value > 6:
            raise ValueError("Cada cenário de qtd_docs deve estar entre 0 e 6.")
        scenarios.append(value)

    if not scenarios:
        raise ValueError("Nenhum cenário de qtd_docs foi informado.")
    return sorted(set(scenarios))


def _new_scenario_bucket(qtd_docs: int) -> dict[str, Any]:
    return {
        "qtd_docs": qtd_docs,
        "eligible_cases": 0,
        "recommendations": Counter(),
        "historical_reference_decisions": Counter(),
        "micro_results": Counter(),
        "comparavel_matches": 0,
        "comparavel_mismatches": 0,
        "referencia_nula": 0,
        "sum_policy_expected_cost": Decimal("0.00"),
        "sum_historical_realized_cost": Decimal("0.00"),
        "sum_estimated_economy": Decimal("0.00"),
        "sum_policy_preserved": Decimal("0.00"),
        "sum_history_preserved": Decimal("0.00"),
        "by_uf": defaultdict(Counter),
        "by_sub_assunto": defaultdict(Counter),
    }


def _counter_payload(counter: Counter[str]) -> dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter)}


def _decision_grid_payload(grid: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    payload: dict[str, dict[str, int]] = {}
    for key in sorted(grid):
        payload[key] = {decision: int(grid[key][decision]) for decision in sorted(grid[key])}
    return payload


def _decimal_payload(value: Decimal, *, places: str = "0.01") -> float:
    return float(value.quantize(Decimal(places)))


def _scenario_payload(bucket: dict[str, Any]) -> dict[str, Any]:
    eligible = bucket["eligible_cases"]
    policy_cost_total = bucket["sum_policy_expected_cost"]
    history_cost_total = bucket["sum_historical_realized_cost"]
    estimated_economy_total = bucket["sum_estimated_economy"]
    policy_preserved_total = bucket["sum_policy_preserved"]
    history_preserved_total = bucket["sum_history_preserved"]

    return {
        "qtd_docs": bucket["qtd_docs"],
        "eligible_cases": eligible,
        "recommendations": _counter_payload(bucket["recommendations"]),
        "historical_reference_decisions": _counter_payload(bucket["historical_reference_decisions"]),
        "micro_results": _counter_payload(bucket["micro_results"]),
        "comparavel_matches": int(bucket["comparavel_matches"]),
        "comparavel_mismatches": int(bucket["comparavel_mismatches"]),
        "referencia_nula": int(bucket["referencia_nula"]),
        "policy_expected_cost_total": _decimal_payload(policy_cost_total),
        "policy_expected_cost_mean": _decimal_payload(policy_cost_total / eligible) if eligible else 0.0,
        "historical_realized_cost_total": _decimal_payload(history_cost_total),
        "historical_realized_cost_mean": _decimal_payload(history_cost_total / eligible) if eligible else 0.0,
        "estimated_economy_total": _decimal_payload(estimated_economy_total),
        "estimated_economy_mean": _decimal_payload(estimated_economy_total / eligible) if eligible else 0.0,
        "policy_preserved_total": _decimal_payload(policy_preserved_total),
        "historical_preserved_total": _decimal_payload(history_preserved_total),
        "by_uf": _decision_grid_payload(bucket["by_uf"]),
        "by_sub_assunto": _decision_grid_payload(bucket["by_sub_assunto"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aplica a V5 em cenarios de qtd_docs sobre o CSV historico e compara com o resultado micro observado."
    )
    parser.add_argument(
        "--docs-scenarios",
        default="all",
        help="Lista de qtd_docs para simular (ex: 0,3,6) ou 'all'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limita o numero de linhas processadas. 0 significa sem limite.",
    )
    args = parser.parse_args()

    scenarios = parse_scenarios(args.docs_scenarios)
    scenario_buckets = {qtd_docs: _new_scenario_bucket(qtd_docs) for qtd_docs in scenarios}

    total_rows = 0
    eligible_rows = 0
    inconclusive_rows = 0
    missing_counter: Counter[str] = Counter()
    micro_result_counter: Counter[str] = Counter()
    sub_counter: Counter[str] = Counter()
    uf_counter: Counter[str] = Counter()

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            total_rows += 1
            if args.limit and total_rows > args.limit:
                break

            uf = normalize_text(row.get(UF_COLUMN, "")).upper() or "TOTAL"
            sub = normalize_sub_assunto_v5(row.get(SUBASSUNTO_COLUMN))
            ped = parse_decimal(row.get(VALOR_CAUSA_COLUMN))
            resultado_micro = row.get(RESULTADO_MICRO_COLUMN, "")
            micro_outcome = classify_micro_result_economic(resultado_micro, ped)

            if ped is None or ped <= 0:
                missing_counter["ped_invalido"] += 1
                inconclusive_rows += 1
                continue
            if micro_outcome is None:
                missing_counter["resultado_micro_inconclusivo"] += 1
                inconclusive_rows += 1
                continue

            eligible_rows += 1
            micro_result_counter[micro_outcome.resultado_micro_normalizado] += 1
            sub_counter[sub] += 1
            uf_counter[uf] += 1

            historical_realized_cost = micro_outcome.valor_pago
            historical_preserved = micro_outcome.valor_preservado

            for qtd_docs, bucket in scenario_buckets.items():
                result = calculate_policy_v5(
                    PolicyCaseInputV5(
                        ped=ped,
                        uf=uf,
                        sub=sub,
                        qtd_docs_override=qtd_docs,
                    )
                )
                expected_policy_cost = resolve_policy_backtest_cost(result).quantize(CENTS)
                estimated_economy = (historical_realized_cost - expected_policy_cost).quantize(CENTS)
                policy_preserved = (ped - expected_policy_cost).quantize(CENTS)

                bucket["eligible_cases"] += 1
                bucket["recommendations"][result.decisao.lower()] += 1
                bucket["historical_reference_decisions"][micro_outcome.decisao_referencia] += 1
                bucket["micro_results"][micro_outcome.resultado_micro_normalizado] += 1
                bucket["sum_policy_expected_cost"] += expected_policy_cost
                bucket["sum_historical_realized_cost"] += historical_realized_cost
                bucket["sum_estimated_economy"] += estimated_economy
                bucket["sum_policy_preserved"] += policy_preserved
                bucket["sum_history_preserved"] += historical_preserved
                bucket["by_uf"][uf][result.decisao.lower()] += 1
                bucket["by_sub_assunto"][sub][result.decisao.lower()] += 1

                if micro_outcome.decisao_referencia == "nula":
                    bucket["referencia_nula"] += 1
                elif result.decisao.lower() == micro_outcome.decisao_referencia:
                    bucket["comparavel_matches"] += 1
                else:
                    bucket["comparavel_mismatches"] += 1

    payload = {
        "csv_path": str(CSV_PATH),
        "assumptions": {
            "ped_proxy": VALOR_CAUSA_COLUMN,
            "policy_expected_cost_for_defesa": "VEJ",
            "policy_expected_cost_for_acordo": "ALVO",
            "qtd_docs_mode": "scenario_analysis",
            "docs_scenarios": scenarios,
            "micro_result_rules": micro_result_rules_payload(),
        },
        "layers": {
            "camada_1_cobertura": {
                "total_rows": total_rows if not args.limit else min(total_rows, args.limit),
                "eligible_rows": eligible_rows,
                "inconclusive_rows": inconclusive_rows,
                "missing_or_inconclusive": dict(missing_counter),
                "ufs_eligiveis": _counter_payload(uf_counter),
                "sub_assuntos_eligiveis": _counter_payload(sub_counter),
            },
            "camada_2_resultado_micro": {
                "micro_results_normalizados": _counter_payload(micro_result_counter),
            },
            "camada_3_backtest_v5": {
                "cenarios": [_scenario_payload(scenario_buckets[qtd_docs]) for qtd_docs in scenarios],
            },
        },
    }

    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
