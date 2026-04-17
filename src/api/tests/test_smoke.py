from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from app.analytics.historical import load_semantic_index_metadata, summarize_mock_file
from app.analytics.semantic import LOCAL_EMBEDDING_DIMENSIONS
from app.core.config import get_settings
from app.services import analyze_case_documents
from app.services.decision_engine import build_recommendation_payload
from app.services.judge import review_recommendation_with_judge
from app.services.justifier import generate_recommendation_justification
from app.services.policy import load_policy
from app.services.recommendation_pipeline import derive_case_status
from main import app

DATA_DIR = Path(get_settings().case_storage_dir).parent
PROJECT_DIR = DATA_DIR.parent
EXAMPLE_CASES = {
    "caso_001": {
        "autos": [
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "01_Autos_Processo_0801234-56-2024-8-10-0001.pdf",
        ],
        "subsidios": [
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "02_Contrato_502348719.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "03_Extrato_Bancario.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "04_Comprovante_de_Credito_BACEN.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "05_Dossie_Veritas.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "06_Demonstrativo_Evolucao_Divida.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_01_0801234-56-2024-8-10-0001"
            / "07_Laudo_Referenciado.pdf",
        ],
        "numero_processo": "0801234-56.2024.8.10.0001",
    },
    "caso_002": {
        "autos": [
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_02_0654321-09-2024-8-04-0001"
            / "01_Autos_Processo_0654321-09-2024-8-04-0001.pdf",
        ],
        "subsidios": [
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_02_0654321-09-2024-8-04-0001"
            / "02_Comprovante_de_Credito_BACEN.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_02_0654321-09-2024-8-04-0001"
            / "03_Demonstrativo_Evolucao_Divida.pdf",
            PROJECT_DIR
            / "arquivos_adicionais"
            / "Caso_02_0654321-09-2024-8-04-0001"
            / "04_Laudo_Referenciado.pdf",
        ],
        "numero_processo": "0654321-09.2024.8.04.0001",
    },
}


def _history_summary(
    *,
    prob_vitoria: float,
    custo_medio_defesa: str,
    percentil_25: str,
    percentil_50: str,
) -> dict[str, object]:
    return {
        "casos_similares_ids": ["hist-001", "hist-002", "hist-003"],
        "total_casos_similares": 3,
        "stats": {
            "prob_vitoria": prob_vitoria,
            "custo_medio_defesa": custo_medio_defesa,
            "percentil_25": percentil_25,
            "percentil_50": percentil_50,
        },
    }


def test_app_metadata() -> None:
    assert app.title == "Hackathon UFMG 2026 API"


def test_extraction_pipeline_runs_on_example_cases_without_llm() -> None:
    for fixture in EXAMPLE_CASES.values():
        with patch("app.llm.client.chat_json_prompt", return_value=None), patch(
            "app.llm.client.get_openai_client",
            return_value=None,
        ):
            payload = analyze_case_documents(fixture["autos"], fixture["subsidios"])

        assert payload["autos_data"]["numero_processo"] == fixture["numero_processo"]
        assert payload["autos_data"]["valor_causa"] is not None
        assert payload["subsidios_data"]
        assert payload["features_data"]["red_flags"] is not None
        assert payload["structured_features"]["case_text"]
        assert len(payload["embedding"]) == LOCAL_EMBEDDING_DIMENSIONS


def test_historical_summary_for_mock_cases_has_similares() -> None:
    for case_name in ("caso_001", "caso_002"):
        summary = summarize_mock_file(
            DATA_DIR / "processos_exemplo" / case_name / "mock_case.json",
            k=3,
        )

        assert summary["casos_similares_ids"]
        assert "prob_vitoria" in summary["stats"]


def test_semantic_index_metadata_is_available() -> None:
    metadata = load_semantic_index_metadata()
    assert metadata is not None
    assert metadata.dimensions > 0
    assert metadata.row_count > 1000


def test_policy_priority_rule_applies_for_fragile_subsidies() -> None:
    payload = build_recommendation_payload(
        {
            "valor_causa": 15000,
            "valor_pedido_danos_morais": 10000,
            "red_flags": ["ausencia_contrato"],
            "vulnerabilidade_autor": "idoso",
            "indicio_fraude": 0.2,
            "forca_narrativa_autor": 0.7,
            "subsidios": {
                "tem_contrato": False,
                "tem_extrato": True,
                "tem_dossie": False,
                "tem_comprovante": False,
                "assinatura_validada": False,
                "canal_contratacao": "correspondente",
            },
        },
        load_policy(),
        history_summary=_history_summary(
            prob_vitoria=0.45,
            custo_medio_defesa="5500",
            percentil_25="4000",
            percentil_50="6000",
        ),
    )

    assert payload["decisao"] == "acordo"
    assert "AP-01" in payload["regras_aplicadas"]
    assert payload["valor_sugerido_min"] == Decimal("6072.00")
    assert payload["valor_sugerido_max"] == Decimal("7590.00")
    assert "VAL-CORRESP" in payload["regras_aplicadas"]
    assert "VAL-IDOSO" in payload["regras_aplicadas"]
    assert payload["casos_similares_ids"] == ["hist-001", "hist-002", "hist-003"]


def test_ev_prefers_defesa_when_robustez_is_high_and_risk_is_lower() -> None:
    payload = build_recommendation_payload(
        {
            "valor_causa": 25000,
            "valor_pedido_danos_morais": 18000,
            "red_flags": [],
            "vulnerabilidade_autor": "nenhuma",
            "indicio_fraude": 0.8,
            "forca_narrativa_autor": 0.1,
            "subsidios": {
                "tem_contrato": True,
                "tem_extrato": True,
                "tem_dossie": True,
                "tem_comprovante": True,
                "assinatura_validada": False,
                "canal_contratacao": "digital",
            },
        },
        load_policy(),
        history_summary=_history_summary(
            prob_vitoria=0.10,
            custo_medio_defesa="9000",
            percentil_25="15000",
            percentil_50="18000",
        ),
    )

    assert payload["decisao"] == "defesa"
    assert payload["valor_sugerido_min"] is None
    assert payload["valor_sugerido_max"] is None
    assert "EV-DF-01: robustez alta e EV_defesa inferior ao acordo conservador" in payload["regras_aplicadas"]
    assert payload["casos_similares_ids"] == ["hist-001", "hist-002", "hist-003"]


def test_judge_fallback_requests_review_for_risky_defesa() -> None:
    judge = review_recommendation_with_judge(
        {
            "red_flags": ["ausencia_contrato", "assinatura_divergente"],
            "vulnerabilidade_autor": "idoso",
            "indicio_fraude": 0.1,
        },
        {
            "decisao": "defesa",
            "confianca": 0.88,
            "valor_sugerido_min": None,
            "valor_sugerido_max": None,
        },
        _history_summary(
            prob_vitoria=0.72,
            custo_medio_defesa="8000",
            percentil_25="5000",
            percentil_50="7000",
        ),
        allow_llm=False,
    )

    assert judge["concorda"] is False
    assert "revisão humana" in judge["observacao"].lower()
    assert judge["confianca_calibrada"] <= 0.55


def test_justifier_fallback_mentions_history_and_judge() -> None:
    justification = generate_recommendation_justification(
        {
            "red_flags": ["ausencia_contrato"],
            "vulnerabilidade_autor": "idoso",
        },
        {
            "decisao": "acordo",
            "valor_sugerido_min": Decimal("3000.00"),
            "valor_sugerido_max": Decimal("4200.00"),
        },
        _history_summary(
            prob_vitoria=0.48,
            custo_medio_defesa="5300",
            percentil_25="3000",
            percentil_50="4500",
        ),
        {
            "concorda": False,
            "observacao": "Faixa exige revisão do gestor.",
            "confianca_calibrada": 0.54,
        },
        allow_llm=False,
    )

    assert "hist-001" in justification
    assert "revisão humana" in justification.lower()
    assert "R$ 3.000,00" in justification


def test_case_status_moves_to_needs_review_when_judge_disagrees() -> None:
    assert derive_case_status("analyzed", {"judge_concorda": False}) == "needs_review"
    assert derive_case_status("pending", {"judge_concorda": True}) == "analyzed"
    assert derive_case_status("closed", {"judge_concorda": False}) == "closed"
