from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from app.analytics.historical import (
    SemanticIndexMetadata,
    _build_query_embedding,
    load_semantic_index_metadata,
    summarize_mock_file,
)
from app.analytics.semantic import (
    LOCAL_EMBEDDING_DIMENSIONS,
    LOCAL_EMBEDDING_MODEL,
    SEMANTIC_TEXT_STRATEGY,
    build_local_embedding_list,
    build_runtime_case_text,
)
from app.core.config import get_settings
from app.llm.client import (
    HISTORY_ASSUNTO_DEFAULT,
    HISTORY_SUBASSUNTO_GENERIC,
    HISTORY_SUBASSUNTO_GOLPE,
    heuristic_extract_case_context,
)
from app.models.case import Case
from app.services import analyze_case_documents
from app.services.case_maintenance import apply_analysis_to_case
from app.services.case_sanitizer import repair_case, sanitize_cases
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
        "autor_nome": "MARIA DAS GRAÇAS SILVA PEREIRA",
        "autor_cpf": "456.789.123-45",
        "uf": "MA",
        "assunto": HISTORY_ASSUNTO_DEFAULT,
        "sub_assunto": HISTORY_SUBASSUNTO_GENERIC,
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
        "autor_nome": "JOSÉ RAIMUNDO OLIVEIRA COSTA",
        "autor_cpf": "789.123.456-78",
        "uf": "AM",
        "assunto": HISTORY_ASSUNTO_DEFAULT,
        "sub_assunto": HISTORY_SUBASSUNTO_GOLPE,
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
        assert payload["autos_data"]["autor_nome"] == fixture["autor_nome"]
        assert payload["autos_data"]["autor_cpf"] == fixture["autor_cpf"]
        assert payload["autos_data"]["valor_causa"] is not None
        assert payload["subsidios_data"]
        assert payload["features_data"]["red_flags"] is not None
        assert payload["structured_features"]["case_text"]
        assert payload["structured_features"]["uf"] == fixture["uf"]
        assert payload["structured_features"]["assunto"] == fixture["assunto"]
        assert payload["structured_features"]["sub_assunto"] == fixture["sub_assunto"]
        assert len(payload["embedding"]) == LOCAL_EMBEDDING_DIMENSIONS


def test_historical_summary_for_mock_cases_has_similares() -> None:
    for case_name in ("caso_001", "caso_002"):
        summary = summarize_mock_file(
            DATA_DIR / "processos_exemplo" / case_name / "mock_case.json",
            k=3,
        )

        assert summary["casos_similares_ids"]
        assert "prob_vitoria" in summary["stats"]


def test_context_fallback_handles_missing_text_without_false_positive() -> None:
    payload = heuristic_extract_case_context(
        "",
        "",
        {
            "numero_processo": "0000001-00.2024.8.01.0001",
            "autor_nome": "FULANO DE TAL",
            "alegacoes": [],
            "pedidos": [],
        },
        {},
        {"red_flags": [], "indicio_fraude": 0.0},
        filenames=["01_Autos_Processo.pdf", "02_Contrato.pdf"],
    )

    assert payload["uf"] is None
    assert payload["assunto"] is None
    assert payload["sub_assunto"] is None
    assert payload["ocr_recommended"] is True
    assert "Documentos recebidos" in payload["case_text"]


def test_apply_analysis_preserves_terminal_status_and_embedding_metadata() -> None:
    case = Case(
        id="closed-case",
        status="closed",
        source_folder="/app/data/processos_exemplo/case_closed-case",
    )
    apply_analysis_to_case(
        case,
        {
            "autos_data": {
                "numero_processo": "0000001-00.2024.8.01.0001",
                "autor_nome": "FULANO DE TAL",
                "autor_cpf": "123.456.789-00",
                "valor_causa": 1000,
                "alegacoes": ["teste"],
                "pedidos": ["pedido"],
                "valor_danos_morais": 500,
            },
            "subsidios_data": {"tem_contrato": True},
            "features_data": {
                "red_flags": ["flag"],
                "vulnerabilidade_autor": "idoso",
                "indicio_fraude": 0.2,
                "forca_narrativa_autor": 0.4,
                "inconsistencias_temporais": [],
            },
            "embedding": [0.1] * LOCAL_EMBEDDING_DIMENSIONS,
            "embedding_provider": "local",
            "embedding_model": LOCAL_EMBEDDING_MODEL,
            "embedding_dimensions": LOCAL_EMBEDDING_DIMENSIONS,
            "embedding_source": SEMANTIC_TEXT_STRATEGY,
            "autos_text": "texto autos",
            "subsidios_text": "texto subsidios",
            "structured_features": {
                "uf": "MA",
                "assunto": HISTORY_ASSUNTO_DEFAULT,
                "sub_assunto": HISTORY_SUBASSUNTO_GENERIC,
                "case_text": "resumo semantico",
            },
        },
    )

    assert case.status == "closed"
    assert case.embedding_source == SEMANTIC_TEXT_STRATEGY
    assert case.embedding_model == LOCAL_EMBEDDING_MODEL
    assert case.source_folder.endswith("/data/processos_exemplo/case_closed-case")


def test_repair_case_reanalyzes_legacy_payload_with_canonical_source_folder() -> None:
    case = Case(
        id="legacy-repair",
        status="pending",
        source_folder="/app/data/processos_exemplo/case_legacy-repair",
    )
    analysis = {
        "autos_data": {
            "numero_processo": "0654321-09.2024.8.04.0001",
            "autor_nome": "JOSÉ RAIMUNDO OLIVEIRA COSTA",
            "autor_cpf": "789.123.456-78",
            "valor_causa": 25000,
            "alegacoes": ["não reconhece contratação"],
            "pedidos": ["declaração de inexistência de débito"],
            "valor_danos_morais": 15000,
        },
        "subsidios_data": {
            "tem_contrato": False,
            "tem_comprovante": True,
            "tem_dossie": False,
        },
        "features_data": {
            "red_flags": ["ausencia_contrato"],
            "vulnerabilidade_autor": "nenhuma",
            "indicio_fraude": 0.25,
            "forca_narrativa_autor": 0.7,
            "inconsistencias_temporais": [],
        },
        "embedding": [0.1] * LOCAL_EMBEDDING_DIMENSIONS,
        "embedding_provider": "local",
        "embedding_model": LOCAL_EMBEDDING_MODEL,
        "embedding_dimensions": LOCAL_EMBEDDING_DIMENSIONS,
        "embedding_source": SEMANTIC_TEXT_STRATEGY,
        "autos_text": "texto autos",
        "subsidios_text": "texto subsidios",
        "structured_features": {
            "uf": "AM",
            "assunto": HISTORY_ASSUNTO_DEFAULT,
            "sub_assunto": HISTORY_SUBASSUNTO_GOLPE,
            "case_text": "resumo semântico",
        },
    }
    canonical_dir = DATA_DIR / "processos_exemplo" / "case_legacy-repair"

    with patch(
        "app.services.case_sanitizer.canonical_case_directory",
        return_value=canonical_dir,
    ), patch(
        "app.services.case_sanitizer.list_case_document_paths",
        return_value=([canonical_dir / "autos" / "01.pdf"], [canonical_dir / "subsidios" / "02.pdf"]),
    ), patch(
        "app.services.case_sanitizer._analyze_case_documents",
        return_value=analysis,
    ):
        result = repair_case(case, allow_llm=False)

    assert result["reanalyzed"] is True
    assert result["autos_count"] == 1
    assert result["subsidios_count"] == 1
    assert case.status == "analyzed"
    assert case.source_folder == str(canonical_dir)
    assert case.uf == "AM"
    assert case.assunto == HISTORY_ASSUNTO_DEFAULT
    assert case.sub_assunto == HISTORY_SUBASSUNTO_GOLPE
    assert case.embedding_source == SEMANTIC_TEXT_STRATEGY


def test_sanitize_cases_dry_run_rolls_back_changes() -> None:
    case = Case(
        id="legacy-dry-run",
        status="pending",
        source_folder="/app/data/processos_exemplo/case_legacy-dry-run",
    )

    class FakeQuery:
        def __init__(self, rows):
            self._rows = rows

        def order_by(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return self._rows

    class FakeSession:
        def __init__(self, rows):
            self._rows = rows
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def query(self, _model):
            return FakeQuery(self._rows)

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    fake_session = FakeSession([case])

    def fake_repair(target_case: Case, *, allow_llm: bool) -> dict[str, object]:
        assert allow_llm is False
        before = {
            "status": target_case.status,
            "source_folder": target_case.source_folder,
            "uf": target_case.uf,
            "assunto": target_case.assunto,
            "sub_assunto": target_case.sub_assunto,
            "embedding_source": getattr(target_case, "embedding_source", None),
        }
        target_case.status = "analyzed"
        target_case.source_folder = "/workspace/data/processos_exemplo/case_legacy-dry-run"
        target_case.uf = "MA"
        target_case.assunto = HISTORY_ASSUNTO_DEFAULT
        target_case.sub_assunto = HISTORY_SUBASSUNTO_GENERIC
        target_case.embedding_source = SEMANTIC_TEXT_STRATEGY
        return {
            "before": before,
            "autos_count": 1,
            "subsidios_count": 0,
            "reanalyzed": True,
        }

    with patch(
        "app.services.case_sanitizer.SessionLocal",
        return_value=fake_session,
    ), patch(
        "app.services.case_sanitizer.repair_case",
        side_effect=fake_repair,
    ), patch(
        "app.services.case_sanitizer.upsert_case_recommendation",
        return_value=None,
    ):
        payload = sanitize_cases(dry_run=True)

    assert payload["dry_run"] is True
    assert payload["total_cases"] == 1
    assert fake_session.rolled_back is True
    assert fake_session.committed is False
    assert fake_session.closed is True
    assert payload["updated_cases"][0]["changed"]["status"] == {
        "before": "pending",
        "after": "analyzed",
    }
    assert payload["updated_cases"][0]["changed"]["source_folder"] == {
        "before": "/app/data/processos_exemplo/case_legacy-dry-run",
        "after": "/workspace/data/processos_exemplo/case_legacy-dry-run",
    }


def test_semantic_index_metadata_is_available() -> None:
    metadata = load_semantic_index_metadata()
    assert metadata is not None
    assert metadata.dimensions > 0
    assert metadata.row_count > 1000


def test_query_embedding_recomputes_for_legacy_case_representation() -> None:
    case = Case(
        id="legacy-case",
        numero_processo="0801234-56.2024.8.10.0001",
        valor_causa=Decimal("20000"),
        uf="MA",
        assunto=HISTORY_ASSUNTO_DEFAULT,
        sub_assunto=HISTORY_SUBASSUNTO_GENERIC,
        alegacoes=["nao reconhece a contratacao"],
        pedidos=["declaracao de inexistencia de debito"],
        red_flags=["ausencia_contrato"],
        vulnerabilidade_autor="idoso",
        subsidios={"tem_contrato": True, "tem_comprovante": True},
        case_text="autora contesta emprestimo consignado com descontos no beneficio",
        embedding=[0.5] * LOCAL_EMBEDDING_DIMENSIONS,
        embedding_provider="local",
        embedding_model=LOCAL_EMBEDDING_MODEL,
        embedding_dimensions=LOCAL_EMBEDDING_DIMENSIONS,
        embedding_source="legacy-raw-text-v1",
        status="analyzed",
    )
    metadata = SemanticIndexMetadata(
        provider="local",
        model=LOCAL_EMBEDDING_MODEL,
        dimensions=LOCAL_EMBEDDING_DIMENSIONS,
        row_count=60000,
        text_strategy=SEMANTIC_TEXT_STRATEGY,
    )

    expected_text = build_runtime_case_text(
        numero_processo=case.numero_processo,
        uf=case.uf,
        assunto=case.assunto,
        sub_assunto=case.sub_assunto,
        valor_causa=case.valor_causa,
        alegacoes=case.alegacoes,
        pedidos=case.pedidos,
        red_flags=case.red_flags,
        vulnerabilidade_autor=case.vulnerabilidade_autor,
        subsidios=case.subsidios,
        case_text=case.case_text,
    )
    expected_vector = build_local_embedding_list(expected_text)
    query_vector = _build_query_embedding(case, metadata)

    assert query_vector is not None
    assert query_vector.tolist() == expected_vector


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


def test_policy_engine_is_null_safe_for_legacy_case_data() -> None:
    payload = build_recommendation_payload(
        {
            "valor_causa": None,
            "valor_pedido_danos_morais": None,
            "red_flags": None,
            "vulnerabilidade_autor": None,
            "indicio_fraude": None,
            "forca_narrativa_autor": None,
            "subsidios": None,
        },
        load_policy(),
        history_summary=_history_summary(
            prob_vitoria=0.20,
            custo_medio_defesa="2500",
            percentil_25="1000",
            percentil_50="2000",
        ),
    )

    assert payload["decisao"] in {"acordo", "defesa"}
    assert isinstance(payload["regras_aplicadas"], list)
    assert payload["confianca"] >= 0.35


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
