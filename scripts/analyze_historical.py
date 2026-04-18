from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import duckdb

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "src" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.agreement_policy_v5 import (  # noqa: E402
    MICRO_RESULT_OUTRO,
    classify_micro_result_economic,
    micro_result_rules_payload,
    normalize_micro_result_v5,
)

CSV_PATH = ROOT_DIR / "data" / "sentencas_60k.csv"
PROCESSO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "processo" in name.lower()
)
UF_COLUMN = "UF"
ASSUNTO_COLUMN = "Assunto"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"
VALOR_CONDENACAO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="utf-8", newline="").readline().strip().split(",") if "indeniza" in name.lower()
)

VALUE_BUCKETS = [
    (Decimal("0"), Decimal("5000"), "0-5k"),
    (Decimal("5000"), Decimal("15000"), "5k-15k"),
    (Decimal("15000"), Decimal("50000"), "15k-50k"),
]


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def parse_decimal(value: str) -> Decimal | None:
    normalized = normalize_text(value).replace(",", ".")
    if not normalized:
        return None

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def bucket_for_value(value: Decimal | None) -> str:
    if value is None:
        return "missing"

    for lower, upper, label in VALUE_BUCKETS:
        if lower <= value < upper:
            return label
    return "50k+"


def most_common(counter: Counter[str], limit: int = 5) -> list[dict[str, int]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def _fetch_dicts(connection: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, object]]:
    result = connection.execute(query)
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def _build_duckdb_views() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    connection = duckdb.connect(database=":memory:")
    csv_path = str(CSV_PATH).replace("'", "''")
    connection.execute(
        f"""
        CREATE OR REPLACE VIEW historical_cases AS
        SELECT
            "{PROCESSO_COLUMN}" AS numero_processo,
            "{UF_COLUMN}" AS uf,
            "{ASSUNTO_COLUMN}" AS assunto,
            "{SUBASSUNTO_COLUMN}" AS sub_assunto,
            "{RESULTADO_MACRO_COLUMN}" AS resultado_macro,
            "{RESULTADO_MICRO_COLUMN}" AS resultado_micro,
            TRY_CAST("{VALOR_CAUSA_COLUMN}" AS DOUBLE) AS valor_causa,
            TRY_CAST("{VALOR_CONDENACAO_COLUMN}" AS DOUBLE) AS valor_condenacao
        FROM read_csv_auto('{csv_path}', HEADER=TRUE, SAMPLE_SIZE=-1, ENCODING='utf-8');
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE VIEW historical_cases_enriched AS
        SELECT
            *,
            CASE
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%parcial%' AND lower(coalesce(resultado_micro, '')) LIKE '%proced%' THEN 'parcial_procedencia'
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%improced%' THEN 'improcedente'
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%extint%' THEN 'extinto'
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%acordo%' THEN 'acordo'
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%proced%' THEN 'procedente'
                ELSE 'outro'
            END AS resultado_micro_normalizado,
            CASE
                WHEN valor_causa IS NULL THEN 'missing'
                WHEN valor_causa < 5000 THEN '0-5k'
                WHEN valor_causa < 15000 THEN '5k-15k'
                WHEN valor_causa < 50000 THEN '15k-50k'
                ELSE '50k+'
            END AS faixa_valor,
            CASE
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%improced%'
                    OR lower(coalesce(resultado_micro, '')) LIKE '%extint%'
                THEN 1.0
                WHEN (lower(coalesce(resultado_micro, '')) LIKE '%parcial%' AND lower(coalesce(resultado_micro, '')) LIKE '%proced%')
                    OR lower(coalesce(resultado_micro, '')) LIKE '%proced%'
                    OR lower(coalesce(resultado_micro, '')) LIKE '%acordo%'
                THEN 0.0
                WHEN lower(coalesce(resultado_macro, '')) IN ('êxito', 'exito')
                THEN 1.0
                WHEN lower(coalesce(resultado_macro, '')) IN ('não êxito', 'nao exito')
                THEN 0.0
                ELSE NULL
            END AS vitoria,
            CASE
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%improced%'
                    OR lower(coalesce(resultado_micro, '')) LIKE '%extint%'
                THEN 1.00
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%acordo%'
                THEN 0.70
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%parcial%' AND lower(coalesce(resultado_micro, '')) LIKE '%proced%'
                THEN 0.38
                WHEN lower(coalesce(resultado_micro, '')) LIKE '%proced%'
                THEN 0.10
                ELSE 0.0
            END AS desconto_ped_referencia
        FROM historical_cases;
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE VIEW taxa_vitoria_por_faixa AS
        SELECT
            faixa_valor,
            COUNT(*) AS total_casos,
            ROUND(AVG(vitoria), 4) AS prob_vitoria
        FROM historical_cases_enriched
        WHERE vitoria IS NOT NULL
        GROUP BY 1
        ORDER BY 1;
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE VIEW valor_condenacao_medio_por_faixa AS
        SELECT
            faixa_valor,
            COUNT(*) AS total_casos,
            ROUND(AVG(valor_condenacao), 2) AS valor_condenacao_medio,
            ROUND(quantile_cont(valor_condenacao, 0.25), 2) AS percentil_25,
            ROUND(quantile_cont(valor_condenacao, 0.50), 2) AS percentil_50
        FROM historical_cases_enriched
        WHERE valor_condenacao IS NOT NULL
        GROUP BY 1
        ORDER BY 1;
        """
    )
    taxa_vitoria = _fetch_dicts(connection, "SELECT * FROM taxa_vitoria_por_faixa;")
    valor_medio = _fetch_dicts(connection, "SELECT * FROM valor_condenacao_medio_por_faixa;")
    connection.close()
    return taxa_vitoria, valor_medio


def main() -> None:
    resultado_macro_counter: Counter[str] = Counter()
    resultado_micro_counter: Counter[str] = Counter()
    resultado_micro_normalizado_counter: Counter[str] = Counter()
    leitura_economica_counter: Counter[str] = Counter()
    exito_counter: Counter[str] = Counter()
    assunto_counter: Counter[str] = Counter()
    subassunto_counter: Counter[str] = Counter()
    uf_counter: Counter[str] = Counter()
    value_bucket_counter: Counter[str] = Counter()
    missing_counter: Counter[str] = Counter()

    row_count = 0
    cause_values: list[Decimal] = []
    condenacao_values: list[Decimal] = []

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            row_count += 1
            processo = normalize_text(row[PROCESSO_COLUMN])
            uf = normalize_text(row[UF_COLUMN])
            assunto = normalize_text(row[ASSUNTO_COLUMN])
            subassunto = normalize_text(row[SUBASSUNTO_COLUMN])
            resultado_macro = normalize_text(row[RESULTADO_MACRO_COLUMN])
            resultado_micro = normalize_text(row[RESULTADO_MICRO_COLUMN])
            valor_causa = parse_decimal(row[VALOR_CAUSA_COLUMN])
            valor_condenacao = parse_decimal(row[VALOR_CONDENACAO_COLUMN])
            micro_outcome = classify_micro_result_economic(resultado_micro, valor_causa)
            normalized_micro = normalize_micro_result_v5(resultado_micro)

            if not processo:
                missing_counter["numero_processo"] += 1
            if not uf:
                missing_counter["uf"] += 1
            if not assunto:
                missing_counter["assunto"] += 1
            if not subassunto:
                missing_counter["sub_assunto"] += 1
            if not resultado_macro:
                missing_counter["resultado_macro"] += 1
            if not resultado_micro:
                missing_counter["resultado_micro"] += 1
            if valor_causa is None:
                missing_counter["valor_causa"] += 1
            if valor_condenacao is None:
                missing_counter["valor_condenacao"] += 1

            if uf:
                uf_counter[uf] += 1
            if assunto:
                assunto_counter[assunto] += 1
            if subassunto:
                subassunto_counter[subassunto] += 1
            if resultado_macro:
                resultado_macro_counter[resultado_macro] += 1
            if resultado_micro:
                resultado_micro_counter[resultado_micro] += 1
            if normalized_micro != MICRO_RESULT_OUTRO:
                resultado_micro_normalizado_counter[normalized_micro] += 1
            else:
                missing_counter["resultado_micro_inconclusivo"] += 1

            if micro_outcome is not None:
                leitura_economica_counter[micro_outcome.leitura] += 1
                exito_counter["exito" if micro_outcome.exito_financeiro else "nao_exito"] += 1

            value_bucket_counter[bucket_for_value(valor_causa)] += 1

            if valor_causa is not None:
                cause_values.append(valor_causa)
            if valor_condenacao is not None:
                condenacao_values.append(valor_condenacao)

    taxa_vitoria, valor_medio = _build_duckdb_views()

    summary = {
        "csv_path": str(CSV_PATH),
        "row_count": row_count,
        "valor_causa": {
            "present": len(cause_values),
            "missing": missing_counter["valor_causa"],
            "min": str(min(cause_values)) if cause_values else None,
            "max": str(max(cause_values)) if cause_values else None,
            "bucket_distribution": dict(value_bucket_counter),
        },
        "valor_condenacao": {
            "present": len(condenacao_values),
            "missing": missing_counter["valor_condenacao"],
            "min": str(min(condenacao_values)) if condenacao_values else None,
            "max": str(max(condenacao_values)) if condenacao_values else None,
        },
        "top_ufs": most_common(uf_counter),
        "top_assuntos": most_common(assunto_counter),
        "top_subassuntos": most_common(subassunto_counter),
        "top_resultados_macro": most_common(resultado_macro_counter),
        "top_resultados_micro": most_common(resultado_micro_counter),
        "top_resultados_micro_normalizados": most_common(resultado_micro_normalizado_counter),
        "resultado_micro_economico": {
            "regras_v5": micro_result_rules_payload(),
            "leituras": dict(leitura_economica_counter),
            "exito_vs_nao_exito": dict(exito_counter),
        },
        "missing_fields": dict(missing_counter),
        "duckdb_views": {
            "taxa_vitoria_por_faixa": taxa_vitoria,
            "valor_condenacao_medio_por_faixa": valor_medio,
        },
    }

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
