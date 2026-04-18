from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.case import Case
from app.models.recommendation import Recommendation
from app.services.case_maintenance import apply_analysis_to_case, list_case_document_paths, upsert_case_recommendation
from app.services.extractor import analyze_case_bundles, bundle_case_documents

logger = logging.getLogger(__name__)

PROCESSING_STAGES = [
    {
        "id": "document_intake",
        "label": "Documentos recebidos",
        "agent": "Orquestrador",
        "kind": "system",
        "description": "Arquivos persistidos e caso preparado para iniciar o pipeline.",
    },
    {
        "id": "document_read",
        "label": "Leitura documental",
        "agent": "Leitor de PDFs",
        "kind": "system",
        "description": "Leitura dos autos e dos subsidios para consolidar o texto bruto do caso.",
    },
    {
        "id": "case_structuring",
        "label": "Estruturacao juridica",
        "agent": "Analista juridico",
        "kind": "llm",
        "description": "Extracao de fatos, pedidos, sinais de risco e contexto juridico.",
    },
    {
        "id": "policy_decision",
        "label": "Politica V5 e valor",
        "agent": "Motor V5",
        "kind": "policy",
        "description": "Decisao, faixa economica, confianca e necessidade de revisao humana.",
    },
]
ACTIVE_PROCESSING_STATES = {"queued", "running"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utcnow().isoformat()


def _to_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _duration_ms(started_at: Any, completed_at: Any) -> int | None:
    start = _to_datetime(started_at)
    end = _to_datetime(completed_at)
    if start is None or end is None:
        return None
    elapsed = int((end - start).total_seconds() * 1000)
    return max(elapsed, 0)


def _format_brl(value: Any) -> str:
    if value in (None, "", "None"):
        return "R$ 0,00"
    try:
        number = float(value)
    except Exception:
        return str(value)
    return f"R$ {number:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _empty_stage(stage: dict[str, str]) -> dict[str, Any]:
    return {
        **stage,
        "status": "pending",
        "thought": None,
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "meta": {},
    }


def _base_processing_status() -> dict[str, Any]:
    return {
        "state": "queued",
        "progress_pct": 0,
        "current_stage": None,
        "current_label": None,
        "summary": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "stages": [_empty_stage(stage) for stage in PROCESSING_STAGES],
        "result": None,
    }


def _stage_index(stage_id: str) -> int:
    for index, stage in enumerate(PROCESSING_STAGES):
        if stage["id"] == stage_id:
            return index
    raise KeyError(f"Stage desconhecido: {stage_id}")


def normalize_processing_status(payload: dict[str, Any] | None) -> dict[str, Any]:
    status = _base_processing_status()
    if not isinstance(payload, dict):
        return status

    status["state"] = str(payload.get("state") or status["state"])
    status["progress_pct"] = int(payload.get("progress_pct") or 0)
    status["current_stage"] = payload.get("current_stage")
    status["current_label"] = payload.get("current_label")
    status["summary"] = payload.get("summary")
    status["error_message"] = payload.get("error_message")
    status["started_at"] = payload.get("started_at")
    status["completed_at"] = payload.get("completed_at")
    status["result"] = dict(payload.get("result") or {}) or None

    incoming_stages = {
        str(stage.get("id")): stage
        for stage in payload.get("stages") or []
        if isinstance(stage, dict) and stage.get("id")
    }
    merged: list[dict[str, Any]] = []
    for stage in PROCESSING_STAGES:
        current = incoming_stages.get(stage["id"], {})
        merged.append(
            {
                **_empty_stage(stage),
                **current,
                "meta": dict(current.get("meta") or {}),
            }
        )
    status["stages"] = merged
    return status


def initialize_case_processing(case: Case, *, autos_count: int, subsidios_count: int) -> dict[str, Any]:
    now = _iso_now()
    status = normalize_processing_status(case.processing_status)
    intake = status["stages"][0]
    intake["status"] = "completed"
    intake["thought"] = "Recebi os arquivos e organizei autos e subsidios para iniciar a analise."
    intake["started_at"] = now
    intake["completed_at"] = now
    intake["duration_ms"] = 0
    intake["meta"] = {
        "autos_count": autos_count,
        "subsidios_count": subsidios_count,
        "total_files": autos_count + subsidios_count,
    }

    status["state"] = "queued"
    status["progress_pct"] = 12
    status["current_stage"] = "document_read"
    status["current_label"] = "Agentes inicializando"
    status["summary"] = "Os arquivos foram recebidos. O pipeline vai abrir os PDFs em instantes."
    status["error_message"] = None
    status["started_at"] = now
    status["completed_at"] = None
    status["result"] = None
    case.processing_status = deepcopy(status)
    case.status = "pending"
    return status


def get_processing_status(case: Case) -> dict[str, Any] | None:
    if case.processing_status is None:
        return None
    return normalize_processing_status(case.processing_status)


def get_processing_state(case: Case) -> str | None:
    status = get_processing_status(case)
    if status is None:
        return None
    return str(status.get("state") or "")


def case_processing_active(case: Case) -> bool:
    return get_processing_state(case) in ACTIVE_PROCESSING_STATES


class CaseProcessingTracker:
    def __init__(self, db: Session, case: Case):
        self.db = db
        self.case = case
        self.status = normalize_processing_status(case.processing_status)

    def _save(self) -> None:
        self.case.processing_status = deepcopy(self.status)
        self.db.add(self.case)
        self.db.commit()
        self.db.refresh(self.case)

    def start_stage(self, stage_id: str, *, thought: str, meta: dict[str, Any] | None = None) -> None:
        index = _stage_index(stage_id)
        stage = self.status["stages"][index]
        now = _iso_now()
        stage["status"] = "running"
        stage["started_at"] = stage["started_at"] or now
        stage["completed_at"] = None
        stage["duration_ms"] = None
        stage["thought"] = thought
        stage["meta"] = dict(meta or {})

        self.status["state"] = "running"
        self.status["current_stage"] = stage_id
        self.status["current_label"] = stage["label"]
        self.status["summary"] = thought
        self.status["error_message"] = None
        self.status["progress_pct"] = min(98, round(((index + 0.45) / len(PROCESSING_STAGES)) * 100))
        self._save()

    def complete_stage(
        self,
        stage_id: str,
        *,
        thought: str,
        meta: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        index = _stage_index(stage_id)
        stage = self.status["stages"][index]
        now = _iso_now()
        stage["status"] = "completed"
        stage["started_at"] = stage["started_at"] or now
        stage["completed_at"] = now
        stage["duration_ms"] = _duration_ms(stage["started_at"], now)
        stage["thought"] = thought
        stage["meta"] = dict(meta or {})

        is_last_stage = index == len(PROCESSING_STAGES) - 1
        self.status["summary"] = thought
        self.status["progress_pct"] = round(((index + 1) / len(PROCESSING_STAGES)) * 100)
        if result is not None:
            self.status["result"] = dict(result)

        if is_last_stage:
            self.status["state"] = "completed"
            self.status["current_stage"] = stage_id
            self.status["current_label"] = "Caso pronto"
            self.status["completed_at"] = now
        else:
            next_stage = self.status["stages"][index + 1]
            self.status["state"] = "running"
            self.status["current_stage"] = next_stage["id"]
            self.status["current_label"] = next_stage["label"]

        self._save()

    def fail(self, stage_id: str, *, error_message: str) -> None:
        safe_stage_id = stage_id if any(stage["id"] == stage_id for stage in PROCESSING_STAGES) else "policy_decision"
        index = _stage_index(safe_stage_id)
        stage = self.status["stages"][index]
        now = _iso_now()
        stage["status"] = "failed"
        stage["started_at"] = stage["started_at"] or now
        stage["completed_at"] = now
        stage["duration_ms"] = _duration_ms(stage["started_at"], now)
        stage["thought"] = "O pipeline encontrou um bloqueio e encaminhou o caso para revisao humana."
        stage["meta"] = {**dict(stage.get("meta") or {}), "error_message": error_message}

        self.status["state"] = "failed"
        self.status["current_stage"] = safe_stage_id
        self.status["current_label"] = "Falha no processamento"
        self.status["summary"] = "O caso precisa de revisao humana antes de liberar a recomendacao."
        self.status["error_message"] = error_message
        self.status["completed_at"] = now
        self.status["progress_pct"] = max(self.status["progress_pct"], round(((index + 0.5) / len(PROCESSING_STAGES)) * 100))
        if self.case.status not in {"decided", "closed"}:
            self.case.status = "needs_review"
        self._save()


def _analysis_summary(analysis: dict[str, Any]) -> str:
    features = analysis.get("structured_features") or {}
    inventory = analysis.get("document_inventory") or {}
    uf = str(features.get("uf") or "UF nao identificada")
    sub_assunto = str(features.get("sub_assunto") or "subgrupo em consolidacao")
    qtd_docs = int(inventory.get("qtd_docs") or 0)
    return (
        f"Consolidei o caso em {uf}, classifiquei o subgrupo como {sub_assunto} "
        f"e encontrei {qtd_docs} documento(s) aproveitaveis para a politica."
    )


def _analysis_meta(analysis: dict[str, Any]) -> dict[str, Any]:
    inventory = analysis.get("document_inventory") or {}
    features = analysis.get("structured_features") or {}
    return {
        "uf": features.get("uf"),
        "assunto": features.get("assunto"),
        "sub_assunto": features.get("sub_assunto"),
        "qtd_docs": int(inventory.get("qtd_docs") or 0),
        "documentos_presentes": len(inventory.get("documentos_presentes") or []),
        "red_flags": len(analysis.get("features_data", {}).get("red_flags") or []),
    }


def _decision_summary(recommendation: Recommendation) -> str:
    trace = dict(recommendation.policy_trace or {})
    decisao = str(recommendation.decisao or "").upper()
    qtd_docs = int(trace.get("qtd_docs") or 0)
    matrix = str(trace.get("matriz_escolhida") or "matriz V5")
    if decisao == "ACORDO":
        base = (
            f"A matriz {matrix} com {qtd_docs} documento(s) sugeriu ACORDO, "
            f"com alvo em {_format_brl(trace.get('alvo'))} e teto em {_format_brl(trace.get('teto'))}."
        )
    else:
        base = (
            f"A matriz {matrix} com {qtd_docs} documento(s) sustentou DEFESA, "
            f"com VEJ estimado em {_format_brl(trace.get('vej'))}."
        )

    if recommendation.judge_concorda is False:
        return base + " O judge pediu revisao humana por coerencia factual."
    return base + " A recomendacao ficou consistente para seguir ao painel do advogado."


def _decision_meta(recommendation: Recommendation) -> dict[str, Any]:
    trace = dict(recommendation.policy_trace or {})
    return {
        "decisao": recommendation.decisao,
        "matriz_escolhida": trace.get("matriz_escolhida"),
        "qtd_docs": int(trace.get("qtd_docs") or 0),
        "revisao_humana": bool(trace.get("revisao_humana") or recommendation.judge_concorda is False),
    }


def _decision_result(recommendation: Recommendation) -> dict[str, Any]:
    trace = dict(recommendation.policy_trace or {})
    return {
        "decisao": recommendation.decisao,
        "confianca": round(float(recommendation.confianca or 0.0), 2),
        "vej": float(trace.get("vej") or 0.0),
        "alvo": float(trace.get("alvo") or 0.0),
        "teto": float(trace.get("teto") or 0.0),
        "revisao_humana": bool(trace.get("revisao_humana") or recommendation.judge_concorda is False),
    }


def process_case_in_background(case_id: str) -> None:
    db = SessionLocal()
    tracker: CaseProcessingTracker | None = None
    current_stage = "document_read"

    try:
        case = db.get(Case, case_id)
        if case is None:
            return

        tracker = CaseProcessingTracker(db, case)
        autos_paths, subsidios_paths = list_case_document_paths(case)

        tracker.start_stage(
            "document_read",
            thought="Estou abrindo os PDFs para consolidar autos, subsidios e inventario documental.",
            meta={"autos_count": len(autos_paths), "subsidios_count": len(subsidios_paths)},
        )
        bundled = bundle_case_documents(autos_paths, subsidios_paths)
        tracker.complete_stage(
            "document_read",
            thought=(
                f"Li {len(autos_paths) + len(subsidios_paths)} arquivo(s) "
                "e consolidei o texto base que alimenta os agentes seguintes."
            ),
            meta={
                "autos_files": len(bundled["autos_bundle"]["filenames"]),
                "subsidios_files": len(bundled["subsidios_bundle"]["filenames"]),
                "autos_chars": len(bundled["autos_bundle"]["combined_text"]),
                "subsidios_chars": len(bundled["subsidios_bundle"]["combined_text"]),
            },
        )

        current_stage = "case_structuring"
        tracker.start_stage(
            "case_structuring",
            thought="Agora extraio fatos, pedidos, subsidios e sinais que ajudam a enquadrar o caso.",
        )
        analysis = analyze_case_bundles(bundled)
        tracker.complete_stage(
            "case_structuring",
            thought=_analysis_summary(analysis),
            meta=_analysis_meta(analysis),
        )

        current_stage = "policy_decision"
        tracker.start_stage(
            "policy_decision",
            thought="Cruzei a estrutura do caso com a politica V5 para decidir estrategia, risco e faixa economica.",
        )
        apply_analysis_to_case(case, analysis)
        recommendation = upsert_case_recommendation(db, case)
        tracker.complete_stage(
            "policy_decision",
            thought=_decision_summary(recommendation),
            meta=_decision_meta(recommendation),
            result=_decision_result(recommendation),
        )
    except Exception as exc:
        logger.exception("Falha ao processar caso %s", case_id)
        if tracker is not None:
            tracker.fail(current_stage, error_message=str(exc))
    finally:
        db.close()
