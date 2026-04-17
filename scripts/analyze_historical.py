from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "sentencas_60k.csv"
PROCESSO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="latin-1", newline="").readline().strip().split(",") if "processo" in name.lower()
)
UF_COLUMN = "UF"
ASSUNTO_COLUMN = "Assunto"
SUBASSUNTO_COLUMN = "Sub-assunto"
RESULTADO_MACRO_COLUMN = "Resultado macro"
RESULTADO_MICRO_COLUMN = "Resultado micro"
VALOR_CAUSA_COLUMN = "Valor da causa"
VALOR_CONDENACAO_COLUMN = next(
    name for name in CSV_PATH.open("r", encoding="latin-1", newline="").readline().strip().split(",") if "indeniza" in name.lower()
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


def main() -> None:
    resultado_macro_counter: Counter[str] = Counter()
    resultado_micro_counter: Counter[str] = Counter()
    assunto_counter: Counter[str] = Counter()
    subassunto_counter: Counter[str] = Counter()
    uf_counter: Counter[str] = Counter()
    value_bucket_counter: Counter[str] = Counter()
    missing_counter: Counter[str] = Counter()

    row_count = 0
    cause_values: list[Decimal] = []
    condenacao_values: list[Decimal] = []

    with CSV_PATH.open("r", encoding="latin-1", newline="") as csv_file:
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

            value_bucket_counter[bucket_for_value(valor_causa)] += 1

            if valor_causa is not None:
                cause_values.append(valor_causa)
            if valor_condenacao is not None:
                condenacao_values.append(valor_condenacao)

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
        "missing_fields": dict(missing_counter),
    }

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
