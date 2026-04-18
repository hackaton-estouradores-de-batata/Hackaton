from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

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
    extract_autos_structured,
    extract_case_context_structured,
    extract_features_structured,
    extract_subsidios_structured,
    heuristic_extract_case_context,
)
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.agreement_policy_v5 import (
    PolicyCaseInputV5,
    calculate_policy_v5,
    classify_micro_result_economic,
    resolve_policy_backtest_cost,
)
from app.services import analyze_case_documents
from app.services.case_processing import initialize_case_processing
from app.services.case_maintenance import apply_analysis_to_case
from app.services.case_sanitizer import repair_case, sanitize_cases
from app.services.decision_engine import build_recommendation_payload
from app.services.judge import review_recommendation_with_judge
from app.services.justifier import generate_recommendation_justification
from app.services.recommendation_pipeline import build_recommendation_for_case, derive_case_status
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
        "qtd_docs": 6,
        "documentos_presentes": [
            "contrato",
            "comprovante_credito",
            "extrato",
            "demonstrativo_evolucao_divida",
            "dossie",
            "laudo_referenciado",
        ],
        "subsidios_expected": {
            "assinatura_validada": True,
        },
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
        "qtd_docs": 3,
        "documentos_presentes": [
            "comprovante_credito",
            "demonstrativo_evolucao_divida",
            "laudo_referenciado",
        ],
        "subsidios_expected": {
            "assinatura_validada": False,
        },
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
        assert payload["embedding"] == []
        assert payload["document_inventory"]["qtd_docs"] == fixture["qtd_docs"]
        assert payload["document_inventory"]["documentos_presentes"] == fixture["documentos_presentes"]
        assert payload["subsidios_data"]["assinatura_validada"] == fixture["subsidios_expected"]["assinatura_validada"]


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


def test_llm_extractors_normalize_nested_payloads() -> None:
    with patch("app.llm.client.chat_json_prompt") as mocked_chat:
        mocked_chat.side_effect = [
            {
                "numero_processo": "0801234-56.2024.8.10.0001",
                "autor_nome": "MARIA DAS GRAÇAS SILVA PEREIRA",
                "autor_cpf": "456.789.123-45",
                "valor_causa": "R$ 20.000,00",
                "alegacoes": "não reconhece a contratação; desconto indevido",
                "pedidos": "dano moral; repetição de indébito; inversão do ônus da prova",
                "valor_danos_morais": "R$ 15.000,00",
            },
            {
                "tem_contrato": "sim",
                "tem_extrato": "sim",
                "tem_dossie": True,
                "tem_comprovante": "presente",
                "assinatura_validada": True,
                "canal_contratacao": "Correspondente bancário - Canal Telefônico (Telemarketing)",
                "valor_emprestimo": "R$ 5.000,00",
            },
            {
                "red_flags": [
                    "Há forte ênfase em vulnerabilidade da autora idosa.",
                    "A narrativa fala em fraude, embora existam documentos contrários.",
                ],
                "vulnerabilidade_autor": {"nivel": "alto", "fatores": ["idosa", "aposentada"]},
                "indicio_fraude": {"nivel": "medio", "elementos": ["conjunto documental contraditório"]},
                "forca_narrativa_autor": {"nivel": "media", "pontos_fortes": ["petição coerente"]},
                "inconsistencias_temporais": [
                    {"ponto": "Descoberta apenas em 2024", "analise": "lapso relevante"}
                ],
            },
        ]

        autos_data = extract_autos_structured("texto autos")
        subsidios_data = extract_subsidios_structured("texto subsidios")
        features_data = extract_features_structured("texto autos", autos_data, subsidios_data)

    assert autos_data["valor_causa"] == 20000.0
    assert autos_data["valor_danos_morais"] == 15000.0
    assert autos_data["alegacoes"] == ["não reconhece a contratação", "desconto indevido"]
    assert autos_data["pedidos"] == [
        "dano moral",
        "repetição de indébito",
        "inversão do ônus da prova",
    ]
    assert subsidios_data["tem_comprovante"] is True
    assert subsidios_data["assinatura_validada"] is True
    assert subsidios_data["canal_contratacao"] == "correspondente"
    assert subsidios_data["valor_emprestimo"] == 5000.0
    assert features_data["red_flags"] == [
        "autor_potencialmente_idoso",
        "indicio_fraude_autor",
    ]
    assert features_data["vulnerabilidade_autor"] == "idoso"
    assert features_data["indicio_fraude"] == 0.49
    assert features_data["forca_narrativa_autor"] == 0.55
    assert features_data["inconsistencias_temporais"] == [
        "Descoberta apenas em 2024: lapso relevante"
    ]


def test_extract_features_enforces_subsidy_consistency() -> None:
    subsidios_data = {
        "tem_contrato": True,
        "tem_extrato": True,
        "tem_dossie": True,
        "tem_comprovante": True,
        "assinatura_validada": True,
        "canal_contratacao": "correspondente",
        "valor_emprestimo": 5000.0,
    }

    with patch(
        "app.llm.client.chat_json_prompt",
        return_value={
            "red_flags": [
                "tem_comprovante",
                "ausencia_comprovante_credito",
                "assinatura_validada",
                "indicio_fraude_autor",
            ],
            "vulnerabilidade_autor": "idoso",
            "indicio_fraude": 0.91,
            "forca_narrativa_autor": 0.7,
            "inconsistencias_temporais": [],
        },
    ):
        features_data = extract_features_structured(
            "texto autos sem marcador objetivo de golpe",
            {"alegacoes": [], "pedidos": []},
            subsidios_data,
        )

    assert features_data["red_flags"] == ["indicio_fraude_autor"]
    assert features_data["indicio_fraude"] == 0.49


def test_extract_subsidios_rejects_validated_signature_without_contract_or_dossie() -> None:
    with patch(
        "app.llm.client.chat_json_prompt",
        return_value={
            "tem_contrato": False,
            "tem_extrato": False,
            "tem_dossie": False,
            "tem_comprovante": True,
            "tem_laudo_referenciado": True,
            "assinatura_validada": True,
            "canal_contratacao": "digital",
            "valor_emprestimo": "R$ 8.500,00",
        },
    ):
        subsidios_data = extract_subsidios_structured("laudo menciona biometria, sem contrato e sem dossie")

    assert subsidios_data["tem_contrato"] is False
    assert subsidios_data["tem_dossie"] is False
    assert subsidios_data["assinatura_validada"] is False


def test_extract_context_prefers_generico_with_robust_subsidios() -> None:
    autos_text = (
        "Autora aposentada e idosa afirma que nao reconhece a contratacao do emprestimo consignado, "
        "com descontos em beneficio previdenciario, mas os subsidios indicam contrato, comprovante, dossie "
        "e assinatura validada. "
    ) * 4
    subsidios_text = (
        "Contrato celebrado por correspondente, com comprovante de credito, dossie e validacao de assinatura. "
    ) * 4

    with patch(
        "app.llm.client.chat_json_prompt",
        return_value={
            "uf": "MA",
            "assunto": "Não reconhece operação",
            "sub_assunto": "Golpe",
            "case_text": "resumo",
        },
    ):
        context = extract_case_context_structured(
            autos_text,
            subsidios_text,
            {
                "numero_processo": "0801234-56.2024.8.10.0001",
                "alegacoes": ["não reconhece a contratação"],
                "pedidos": ["declaração de inexistência do débito"],
            },
            {
                "tem_contrato": True,
                "tem_extrato": True,
                "tem_dossie": True,
                "tem_comprovante": True,
                "assinatura_validada": True,
                "canal_contratacao": "correspondente",
            },
            {
                "red_flags": ["autor_potencialmente_idoso", "indicio_fraude_autor"],
                "indicio_fraude": 0.49,
            },
            filenames=["01_Autos_Processo.pdf", "02_Contrato.pdf"],
        )

    assert context["assunto"] == HISTORY_ASSUNTO_DEFAULT
    assert context["sub_assunto"] == HISTORY_SUBASSUNTO_GENERIC


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
    assert case.source_folder.endswith("/data/processos_cadastrados/case_closed-case")


def test_apply_analysis_accepts_brazilian_currency_strings() -> None:
    case = Case(
        id="currency-case",
        status="pending",
        source_folder="/app/data/processos_exemplo/case_currency-case",
    )
    apply_analysis_to_case(
        case,
        {
            "autos_data": {
                "numero_processo": "0801234-56.2024.8.10.0001",
                "autor_nome": "MARIA DAS GRAÇAS SILVA PEREIRA",
                "autor_cpf": "456.789.123-45",
                "valor_causa": "R$ 20.000,00",
                "alegacoes": ["não reconhece a contratação"],
                "pedidos": ["dano moral"],
                "valor_danos_morais": "R$ 15.000,00",
            },
            "subsidios_data": {
                "tem_contrato": "sim",
                "tem_extrato": True,
                "tem_dossie": True,
                "tem_comprovante": True,
                "assinatura_validada": True,
                "canal_contratacao": "Correspondente bancário - Canal Telefônico (Telemarketing)",
                "valor_emprestimo": "R$ 5.000,00",
            },
            "features_data": {
                "red_flags": ["autor_potencialmente_idoso"],
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

    assert case.valor_causa == Decimal("20000.00")
    assert case.valor_pedido_danos_morais == Decimal("15000.00")
    assert case.subsidios["canal_contratacao"] == "correspondente"
    assert case.subsidios["valor_emprestimo"] == 5000.0


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
    canonical_dir = DATA_DIR / "processos_cadastrados" / "case_legacy-repair"

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
        target_case.source_folder = "/workspace/data/processos_cadastrados/case_legacy-dry-run"
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
        "after": "/workspace/data/processos_cadastrados/case_legacy-dry-run",
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


def test_v5_payload_matches_oracle_for_sparse_golpe_case() -> None:
    expected = calculate_policy_v5(
        PolicyCaseInputV5(
            ped=Decimal("18000"),
            uf="AM",
            sub="golpe",
            contrato=False,
            comprovante_credito=True,
            extrato=False,
            demonstrativo_evolucao_divida=True,
            dossie=False,
            laudo_referenciado=True,
            documento_contraditorio=False,
        )
    )
    payload = build_recommendation_payload(
        {
            "valor_causa": 25000,
            "valor_pedido_danos_morais": 18000,
            "uf": "AM",
            "sub_assunto": "Golpe",
            "subsidios": {
                "tem_contrato": False,
                "tem_extrato": False,
                "tem_dossie": False,
                "tem_comprovante": True,
                "tem_demonstrativo_evolucao_divida": True,
                "tem_laudo_referenciado": True,
                "assinatura_validada": False,
                "documento_contraditorio": False,
            },
        },
    )

    assert payload["decisao"] == expected.decisao.lower()
    assert payload["valor_sugerido_min"] == expected.abertura
    assert payload["valor_sugerido_max"] == expected.teto
    assert payload["policy_version"] == "v5"
    assert payload["casos_similares_ids"] == []
    assert payload["regras_aplicadas"] == [
        f"V5-MATRIZ:{expected.matriz_escolhida}",
        f"V5-SUB:{expected.sub}",
        f"V5-QTD_DOCS:{expected.qtd_docs}",
        f"V5-DECISAO:{expected.decisao}",
    ]
    assert payload["policy_trace"]["qtd_docs"] == expected.qtd_docs
    assert payload["policy_trace"]["matriz_escolhida"] == expected.matriz_escolhida
    assert payload["policy_trace"]["documentos_presentes"] == [
        "comprovante_credito",
        "demonstrativo_evolucao_divida",
        "laudo_referenciado",
    ]
    assert payload["valor_sugerido_min"] == Decimal("6000.00")
    assert payload["policy_trace"]["alvo"] == pytest.approx(7500.0, rel=0, abs=1e-9)
    assert payload["valor_sugerido_max"] == Decimal("9000.00")
    assert payload["policy_trace"]["p_suc"] == pytest.approx(float(expected.p_suc), rel=0, abs=1e-9)
    assert payload["policy_trace"]["vej"] == pytest.approx(float(expected.vej), rel=0, abs=1e-9)


def test_v5_payload_matches_oracle_for_full_generico_case() -> None:
    expected = calculate_policy_v5(
        PolicyCaseInputV5(
            ped=Decimal("15000"),
            uf="MA",
            sub="generico",
            contrato=True,
            comprovante_credito=True,
            extrato=True,
            demonstrativo_evolucao_divida=True,
            dossie=True,
            laudo_referenciado=True,
            documento_contraditorio=False,
        )
    )
    payload = build_recommendation_payload(
        {
            "valor_causa": 20000,
            "valor_pedido_danos_morais": 15000,
            "uf": "MA",
            "sub_assunto": "Generico",
            "subsidios": {
                "tem_contrato": True,
                "tem_extrato": True,
                "tem_dossie": True,
                "tem_comprovante": True,
                "tem_demonstrativo_evolucao_divida": True,
                "tem_laudo_referenciado": True,
                "documento_contraditorio": False,
            },
        },
    )

    assert payload["decisao"] == expected.decisao.lower()
    assert payload["valor_sugerido_min"] is None
    assert payload["valor_sugerido_max"] is None
    assert payload["policy_trace"]["qtd_docs"] == 6
    assert payload["policy_trace"]["p_suc"] == pytest.approx(float(expected.p_suc), rel=0, abs=1e-9)
    assert payload["confianca"] == pytest.approx(min(0.95, float(expected.p_suc)), rel=0, abs=1e-9)


def test_v5_missing_ped_returns_review_payload() -> None:
    payload = build_recommendation_payload(
        {
            "valor_causa": None,
            "valor_pedido_danos_morais": None,
            "subsidios": {
                "tem_contrato": True,
                "tem_comprovante": True,
            },
        },
    )

    assert payload["decisao"] == "defesa"
    assert payload["valor_sugerido_min"] is None
    assert payload["valor_sugerido_max"] is None
    assert payload["regras_aplicadas"] == ["V5-MISSING-PED"]
    assert payload["policy_trace"]["revisao_humana"] is True
    assert payload["casos_similares_ids"] == []


def test_initialize_case_processing_creates_visible_timeline() -> None:
    case = Case(id="case-processing", status="pending")

    status = initialize_case_processing(case, autos_count=2, subsidios_count=3)

    assert status["state"] == "queued"
    assert status["current_stage"] == "document_read"
    assert status["progress_pct"] == 12
    assert case.status == "pending"
    assert status["stages"][0]["id"] == "document_intake"
    assert status["stages"][0]["status"] == "completed"
    assert status["stages"][0]["meta"]["autos_count"] == 2
    assert status["stages"][0]["meta"]["subsidios_count"] == 3


def test_recommendation_pipeline_reuses_payload_when_snapshot_is_unchanged() -> None:
    case = Case(
        id="case-reuse",
        status="analyzed",
        valor_causa=Decimal("20000"),
        valor_pedido_danos_morais=Decimal("18000"),
        uf="AM",
        sub_assunto="Golpe",
        subsidios={
            "tem_contrato": False,
            "tem_extrato": False,
            "tem_dossie": False,
            "tem_comprovante": True,
            "tem_demonstrativo_evolucao_divida": True,
            "tem_laudo_referenciado": True,
            "documento_contraditorio": False,
        },
    )

    with patch(
        "app.services.recommendation_pipeline.review_recommendation_with_judge",
        return_value={"concorda": True, "observacao": None, "confianca_calibrada": 0.64},
    ), patch(
        "app.services.recommendation_pipeline.generate_recommendation_justification",
        return_value="Justificativa sintetica",
    ):
        first_payload, first_meta = build_recommendation_for_case(case)

    recommendation = Recommendation(case_id=case.id, **first_payload)

    with patch("app.services.recommendation_pipeline.build_recommendation_payload") as mocked_build:
        reused_payload, reused_meta = build_recommendation_for_case(
            case,
            existing_recommendation=recommendation,
        )

    mocked_build.assert_not_called()
    assert first_meta["reused"] is False
    assert reused_meta["reused"] is True
    assert reused_payload["decisao"] == first_payload["decisao"]
    assert reused_payload["source_snapshot_signature"] == first_payload["source_snapshot_signature"]
    assert reused_payload["justificativa"] == "Justificativa sintetica"


def test_micro_result_classification_follows_v5_national_rules() -> None:
    procedente = classify_micro_result_economic("Procedente", Decimal("10000"))
    parcial = classify_micro_result_economic("Parcial Procedência", Decimal("10000"))
    improcedente = classify_micro_result_economic("improcedente", Decimal("10000"))
    extinto = classify_micro_result_economic("Extinto sem resolução do mérito", Decimal("10000"))
    acordo = classify_micro_result_economic("Acordo homologado", Decimal("10000"))

    assert procedente is not None
    assert procedente.decisao_referencia == "defesa"
    assert procedente.exito_financeiro is False
    assert procedente.desconto_ped == Decimal("0.10")
    assert procedente.valor_pago == Decimal("9000.00")

    assert parcial is not None
    assert parcial.decisao_referencia == "defesa"
    assert parcial.exito_financeiro is False
    assert parcial.desconto_ped == Decimal("0.38")
    assert parcial.valor_preservado == Decimal("3800.00")

    assert improcedente is not None
    assert improcedente.decisao_referencia == "defesa"
    assert improcedente.exito_financeiro is True
    assert improcedente.valor_pago == Decimal("0.00")

    assert extinto is not None
    assert extinto.decisao_referencia == "nula"
    assert extinto.exito_financeiro is True
    assert extinto.valor_preservado == Decimal("10000.00")

    assert acordo is not None
    assert acordo.decisao_referencia == "acordo"
    assert acordo.exito_financeiro is False
    assert acordo.desconto_ped == Decimal("0.70")
    assert acordo.valor_pago == Decimal("3000.00")


def test_backtest_cost_uses_alvo_for_acordo_and_vej_for_defesa() -> None:
    acordo = calculate_policy_v5(
        PolicyCaseInputV5(
            ped=Decimal("18000"),
            uf="AM",
            sub="golpe",
            qtd_docs_override=1,
        )
    )
    defesa = calculate_policy_v5(
        PolicyCaseInputV5(
            ped=Decimal("15000"),
            uf="MA",
            sub="generico",
            qtd_docs_override=6,
        )
    )

    assert acordo.decisao == "ACORDO"
    assert defesa.decisao == "DEFESA"
    assert resolve_policy_backtest_cost(acordo) == acordo.alvo
    assert resolve_policy_backtest_cost(defesa) == defesa.vej


def test_judge_fallback_requests_review_for_risky_defesa() -> None:
    judge = review_recommendation_with_judge(
        {},
        {
            "decisao": "defesa",
            "confianca": 0.88,
            "valor_sugerido_min": None,
            "valor_sugerido_max": None,
            "regras_aplicadas": ["V5-DECISAO:DEFESA"],
            "policy_trace": {
                "mode": "v5",
                "revisao_humana": True,
            },
        },
        allow_llm=False,
    )

    assert judge["concorda"] is False
    assert "revisao humana" in judge["observacao"].lower()
    assert judge["confianca_calibrada"] <= 0.55


def test_justifier_fallback_mentions_v5_trace_and_judge() -> None:
    justification = generate_recommendation_justification(
        case_data={},
        recommendation_payload={
            "decisao": "acordo",
            "valor_sugerido_min": Decimal("3000.00"),
            "valor_sugerido_max": Decimal("4200.00"),
            "policy_trace": {
                "matriz_escolhida": "MATRIZ_GOLPE_6D",
                "qtd_docs": 3,
                "documentos_presentes": ["comprovante_credito", "demonstrativo_evolucao_divida", "laudo_referenciado"],
                "p_suc": 0.41,
                "vej": 5100,
                "alvo": 3700,
            },
        },
        history_summary=None,
        judge_result={
            "concorda": False,
            "observacao": "Faixa exige revisao humana por contradicao documental.",
            "confianca_calibrada": 0.54,
        },
        allow_llm=False,
    )

    assert "MATRIZ_GOLPE_6D" in justification
    assert "revisao humana" in justification.lower()
    assert "R$ 3.000,00" in justification


def test_case_status_moves_to_needs_review_when_judge_disagrees() -> None:
    assert derive_case_status("analyzed", {"judge_concorda": False}) == "needs_review"
    assert derive_case_status("pending", {"judge_concorda": True}) == "analyzed"
    assert derive_case_status("closed", {"judge_concorda": False}) == "closed"
    assert derive_case_status("pending", {"judge_concorda": True, "policy_trace": {"revisao_humana": True}}) == "needs_review"
