from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

from app.models.case import Case

ROOT_DIR = Path(__file__).resolve().parents[4]
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


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    uf: str
    assunto: str
    sub_assunto: str
    resultado_macro: str
    resultado_micro: str
    valor_causa: Decimal | None
    valor_condenacao: Decimal | None
    source_index: int


@dataclass(frozen=True)
class SimilarCasesStats:
    prob_vitoria: float
    custo_medio_defesa: Decimal
    percentil_25: Decimal
    percentil_50: Decimal


RESULTADOS_VITORIA = {
    "êxito",
    "exito",
    "procedente",
    "parcial procedência",
    "parcial procedencia",
}


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


@lru_cache
def load_historical_cases() -> tuple[HistoricalCase, ...]:
    records: list[HistoricalCase] = []

    with CSV_PATH.open("r", encoding="latin-1", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_index, row in enumerate(reader):
            records.append(
                HistoricalCase(
                    case_id=normalize_text(row[PROCESSO_COLUMN]),
                    uf=normalize_text(row[UF_COLUMN]),
                    assunto=normalize_text(row[ASSUNTO_COLUMN]),
                    sub_assunto=normalize_text(row[SUBASSUNTO_COLUMN]),
                    resultado_macro=normalize_text(row[RESULTADO_MACRO_COLUMN]),
                    resultado_micro=normalize_text(row[RESULTADO_MICRO_COLUMN]),
                    valor_causa=parse_decimal(row[VALOR_CAUSA_COLUMN]),
                    valor_condenacao=parse_decimal(row[VALOR_CONDENACAO_COLUMN]),
                    source_index=row_index,
                )
            )

    return tuple(records)


def _cause_bounds(valor_causa: Decimal | None) -> tuple[Decimal | None, Decimal | None]:
    if valor_causa is None:
        return None, None
    lower = valor_causa * Decimal("0.7")
    upper = valor_causa * Decimal("1.3")
    return lower, upper


def _score_similarity(case: Case, item: HistoricalCase) -> tuple[int, Decimal, int]:
    score = 0
    if case.uf and item.uf.casefold() == case.uf.casefold():
        score += 3
    if case.assunto and item.assunto.casefold() == case.assunto.casefold():
        score += 4
    if case.sub_assunto and item.sub_assunto.casefold() == case.sub_assunto.casefold():
        score += 2

    distance = abs((item.valor_causa or Decimal("0")) - (case.valor_causa or Decimal("0")))
    return (-score, distance, item.source_index)



def casos_similares(case: Case, k: int = 50) -> list[HistoricalCase]:
    lower_bound, upper_bound = _cause_bounds(case.valor_causa)
    candidates = load_historical_cases()

    if lower_bound is not None and upper_bound is not None:
        filtered = [
            item
            for item in candidates
            if item.valor_causa is not None and lower_bound <= item.valor_causa <= upper_bound
        ]
        if filtered:
            candidates = tuple(filtered)

    ordered = sorted(candidates, key=lambda item: _score_similarity(case, item))
    return ordered[:k]


def _is_victory(item: HistoricalCase) -> bool:
    macro = item.resultado_macro.casefold()
    micro = item.resultado_micro.casefold()
    return macro in RESULTADOS_VITORIA or micro in RESULTADOS_VITORIA


def _percentile(values: list[Decimal], percentile: Decimal) -> Decimal:
    if not values:
        return Decimal("0")

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    return lower_value + (upper_value - lower_value) * fraction


def stats_similares(casos: list[HistoricalCase]) -> SimilarCasesStats:
    if not casos:
        return SimilarCasesStats(
            prob_vitoria=0.0,
            custo_medio_defesa=Decimal("0"),
            percentil_25=Decimal("0"),
            percentil_50=Decimal("0"),
        )

    victories = sum(1 for item in casos if _is_victory(item))
    condenacoes = [item.valor_condenacao for item in casos if item.valor_condenacao is not None]
    custo_medio = sum(condenacoes, Decimal("0")) / Decimal(len(condenacoes)) if condenacoes else Decimal("0")

    return SimilarCasesStats(
        prob_vitoria=victories / len(casos),
        custo_medio_defesa=custo_medio,
        percentil_25=_percentile(condenacoes, Decimal("0.25")),
        percentil_50=_percentile(condenacoes, Decimal("0.5")),
    )


def summarize_case_history(case: Case, k: int = 5) -> dict[str, object]:
    similares = casos_similares(case, k=k)
    stats = stats_similares(similares)
    return {
        "casos_similares_ids": [item.case_id for item in similares],
        "stats": {
            "prob_vitoria": stats.prob_vitoria,
            "custo_medio_defesa": str(stats.custo_medio_defesa),
            "percentil_25": str(stats.percentil_25),
            "percentil_50": str(stats.percentil_50),
        },
    }


def summarize_mock_file(mock_file: Path, k: int = 5) -> dict[str, object]:
    payload = json.loads(mock_file.read_text(encoding="utf-8"))
    case = Case(
        id=payload["id"],
        numero_processo=payload.get("numero_processo"),
        valor_causa=Decimal(str(payload.get("valor_causa"))) if payload.get("valor_causa") is not None else None,
        autor_nome=payload.get("autor_nome"),
        status=payload.get("status", "analyzed"),
    )
    return summarize_case_history(case, k=k)
