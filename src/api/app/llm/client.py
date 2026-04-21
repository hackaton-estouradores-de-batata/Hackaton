from collections import Counter
from functools import lru_cache
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.analytics.semantic import LOCAL_EMBEDDING_MODEL, build_local_embedding_list
from app.core.config import get_settings
from app.services.case_normalization import (
    coerce_bool,
    coerce_canal_contratacao,
    coerce_list,
    coerce_vulnerabilidade,
    enforce_subsidios_consistency,
)

logger = logging.getLogger(__name__)


@lru_cache
def get_openai_client() -> OpenAI | None:
    api_key = get_settings().openai_api_key
    if not api_key:
        logger.warning("OpenAI desabilitado: OPENAI_API_KEY não foi carregada no processo da API.")
        return None
    if _looks_like_placeholder_secret(api_key):
        logger.warning("OpenAI desabilitado: OPENAI_API_KEY está com valor placeholder e precisa ser substituída por uma chave real.")
        return None
    return OpenAI(api_key=api_key)


def has_active_openai_credentials() -> bool:
    return get_openai_client() is not None


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
BRAZILIAN_UFS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}
HISTORY_ASSUNTO_DEFAULT = "Não reconhece operação"
HISTORY_SUBASSUNTO_GENERIC = "Genérico"
HISTORY_SUBASSUNTO_GOLPE = "Golpe"
MIN_CONTEXT_TEXT_CHARS = 120
MAX_CASE_TEXT_LENGTH = 12000

PLACEHOLDER_SECRETS = {
    "your-openai-api-key",
    "your_api_key_here",
    "yourkey",
    "<yourkey>",
    "<your_api_key>",
}
POSITIVE_EVIDENCE_FLAGS = {
    "tem_contrato",
    "tem_extrato",
    "tem_dossie",
    "tem_comprovante",
    "assinatura_validada",
    "canal_correspondente",
    "contrato_existe_nos_subsidios",
    "extrato_existe_nos_subsidios",
    "dossie_existe_nos_subsidios",
    "comprovante_credito_existe_nos_subsidios",
    "contratacao_por_correspondente",
    "contrato_existente",
    "comprovante_credito_presente",
}
OBJECTIVE_FRAUD_FLAGS = {
    "ausencia_contrato",
    "ausencia_extrato",
    "ausencia_dossie",
    "ausencia_comprovante_credito",
    "assinatura_divergente",
    "assinatura_nao_validada",
    "ausencia_liveness",
    "canal_digital_incompativel",
    "conta_destino_divergente",
    "conta_credito_divergente",
    "registro_boletim_ocorrencia",
    "reclamacao_bacen",
}


def _looks_like_placeholder_secret(value: str) -> bool:
    normalized = value.strip().strip("\"'").lower()
    return normalized in PLACEHOLDER_SECRETS


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def _clean_json_payload(raw_text: str) -> dict[str, Any]:
    payload = raw_text.strip()
    fenced = re.search(r"```json\s*(.*?)```", payload, re.DOTALL)
    if fenced:
        payload = fenced.group(1).strip()
    return json.loads(payload)


def chat_json_prompt(model: str, prompt_name: str, user_payload: str) -> dict[str, Any] | None:
    client = get_openai_client()
    if client is None:
        return None

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": load_prompt(prompt_name)},
                {"role": "user", "content": user_payload},
            ],
        )
        content = completion.choices[0].message.content
    except Exception as exc:
        logger.warning(
            "OpenAI chat_json_prompt falhou para prompt=%s model=%s: %s",
            prompt_name,
            model,
            exc,
        )
        return None

    if not content:
        return None
    return _clean_json_payload(content)


def _parse_brl_value(text: str) -> float | None:
    match = re.search(r"R\$\s*([\d\.\,]+)", text)
    if not match:
        return None
    normalized = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_numeric_token(text: str) -> float | None:
    cleaned = re.sub(r"[^\d,\.\-]", "", str(text or ""))
    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        decimals = cleaned.rsplit(",", 1)[-1]
        if len(decimals) <= 2:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def _score_from_level(value: Any) -> float | None:
    lowered = _compact_text(value).casefold()
    if not lowered:
        return None
    if any(marker in lowered for marker in ("muito alto", "muito alta", "elevado", "elevada")):
        return 0.9
    if any(marker in lowered for marker in ("alto", "alta")):
        return 0.8
    if any(marker in lowered for marker in ("médio", "medio", "média", "media", "moderado", "moderada")):
        return 0.55
    if any(marker in lowered for marker in ("baixo", "baixa")):
        return 0.25
    if any(marker in lowered for marker in ("nenhum", "nenhuma", "ausente", "inexistente")):
        return 0.0
    return None


def _parse_numeric_value(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("valor", "value", "amount", "score", "indice", "índice", "percentual", "percent"):
            parsed = _parse_numeric_value(value.get(key))
            if parsed is not None:
                return parsed
        return _score_from_level(value.get("nivel"))
    if isinstance(value, list):
        return None

    text = _compact_text(value)
    if not text:
        return None

    brl_value = _parse_brl_value(text)
    if brl_value is not None:
        return brl_value

    match = re.search(r"-?\d[\d\.\,]*", text)
    if not match:
        return None
    return _parse_numeric_token(match.group(0))


def _normalize_unit_interval(value: Any, default: float = 0.0) -> float:
    parsed = _parse_numeric_value(value)
    if parsed is None:
        return default
    if parsed > 1 and parsed <= 100:
        parsed = parsed / 100.0
    return round(max(0.0, min(1.0, parsed)), 2)


def _extract_nested_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _compact_text(value)
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return _compact_text(" ".join(part for part in (_extract_nested_text(item) for item in value) if part))
    if isinstance(value, dict):
        preferred_keys = (
            "nivel",
            "fatores",
            "elementos",
            "observacao",
            "observação",
            "avaliacao",
            "avaliação",
            "ponto",
            "analise",
            "análise",
            "pontos_fortes",
            "pontos_fracos",
            "direcao",
            "direção",
        )
        collected: list[str] = []
        for key in preferred_keys:
            text = _extract_nested_text(value.get(key))
            if text:
                collected.append(text)
        if not collected:
            for nested in value.values():
                text = _extract_nested_text(nested)
                if text:
                    collected.append(text)
        return _compact_text(" ".join(collected))
    return _compact_text(value)


def _pick_payload_value(
    payload: dict[str, Any],
    key: str,
    fallback: Any = None,
    *,
    aliases: tuple[str, ...] = (),
) -> Any:
    for candidate in (key, *aliases):
        if candidate not in payload:
            continue
        value = payload.get(candidate)
        if isinstance(value, bool):
            return value
        if value not in (None, "", [], {}):
            return value
    return fallback


def _canonical_red_flag(value: Any) -> str | None:
    text = _extract_nested_text(value)
    lowered = text.casefold()
    if not lowered:
        return None
    compact_lowered = lowered.replace(" ", "_")
    if compact_lowered in POSITIVE_EVIDENCE_FLAGS:
        return None
    if compact_lowered.startswith("tem_"):
        return None
    if any(marker in compact_lowered for marker in ("_existe_nos_subsidios", "assinatura_validada", "canal_correspondente")):
        return None
    if re.fullmatch(r"[a-z0-9_]+", lowered):
        if lowered == "conta_credito_divergente":
            return "conta_destino_divergente"
        if lowered in {"baixa_renda_alegada", "hipossuficiencia_alegada"}:
            return "baixa_renda"
        if lowered in POSITIVE_EVIDENCE_FLAGS:
            return None
        return lowered[:96]
    if "assinatura" in lowered and any(
        marker in lowered for marker in ("diverg", "falsa", "incompat", "não confere", "nao confere")
    ):
        return "assinatura_divergente"
    if "assinatura" in lowered and any(marker in lowered for marker in ("não valid", "nao valid", "ausente")):
        return "assinatura_nao_validada"
    if "contrato" in lowered and any(
        marker in lowered for marker in ("ausência", "ausencia", "sem ", "falt", "inexist")
    ):
        return "ausencia_contrato"
    if "extrato" in lowered and any(
        marker in lowered for marker in ("ausência", "ausencia", "sem ", "falt", "inexist")
    ):
        return "ausencia_extrato"
    if "dossi" in lowered and any(
        marker in lowered for marker in ("ausência", "ausencia", "sem ", "falt", "inexist")
    ):
        return "ausencia_dossie"
    if ("comprovante" in lowered or "crédito" in lowered or "credito" in lowered) and any(
        marker in lowered for marker in ("ausência", "ausencia", "sem ", "falt", "inexist")
    ):
        return "ausencia_comprovante_credito"
    if "liveness" in lowered and any(
        marker in lowered for marker in ("não foi localizado", "nao foi localizado", "ausência", "ausencia", "sem ")
    ):
        return "ausencia_liveness"
    if "canal digital" in lowered and any(
        marker in lowered for marker in ("incompat", "não possui", "nao possui", "jamais utilizou", "sem smartphone")
    ):
        return "canal_digital_incompativel"
    if ("conta" in lowered or "caixa econômica federal" in lowered or "caixa economica federal" in lowered) and any(
        marker in lowered
        for marker in ("não possui", "nao possui", "diverg", "terceiro", "não lhe pertence", "nao lhe pertence")
    ):
        return "conta_destino_divergente"
    if "boletim de ocorrência" in lowered or "boletim de ocorrencia" in lowered:
        return "registro_boletim_ocorrencia"
    if "banco central" in lowered or "rdr" in lowered or "reclamação" in lowered or "reclamacao" in lowered:
        return "reclamacao_bacen"
    if "idos" in lowered:
        return "autor_potencialmente_idoso"
    if "hipossuf" in lowered or "baixa renda" in lowered:
        return "baixa_renda"
    if "fraud" in lowered or "golpe" in lowered:
        return "indicio_fraude_autor"
    return text[:160]


def _normalize_red_flags(value: Any) -> list[str]:
    raw_items = value if isinstance(value, list) else coerce_list(value)
    normalized: list[str] = []
    for item in raw_items:
        flag = _canonical_red_flag(item)
        if flag and flag not in normalized:
            normalized.append(flag)
    return normalized


def _normalize_inconsistencias_temporais(value: Any) -> list[str]:
    raw_items = value if isinstance(value, list) else coerce_list(value)
    normalized: list[str] = []
    for item in raw_items:
        if isinstance(item, dict):
            ponto = _compact_text(item.get("ponto"))
            analise = _compact_text(item.get("analise") or item.get("análise") or item.get("observacao"))
            text = f"{ponto}: {analise}" if ponto and analise else ponto or analise
        else:
            text = _extract_nested_text(item)
        if text and text not in normalized:
            normalized.append(text[:280])
    return normalized


def _has_robust_defense_subsidios(subsidios_data: dict[str, Any]) -> bool:
    channel = coerce_canal_contratacao(subsidios_data.get("canal_contratacao"))
    return (
        bool(subsidios_data.get("tem_contrato"))
        and bool(subsidios_data.get("tem_comprovante"))
        and bool(subsidios_data.get("tem_dossie"))
        and bool(subsidios_data.get("assinatura_validada"))
        and channel in {"correspondente", "presencial"}
    )


def _has_objective_fraud_signal(red_flags: list[str]) -> bool:
    return any(flag in OBJECTIVE_FRAUD_FLAGS for flag in red_flags)


def _consistent_red_flags(red_flags: list[str], subsidios_data: dict[str, Any]) -> list[str]:
    normalized: list[str] = []
    actual_channel = coerce_canal_contratacao(subsidios_data.get("canal_contratacao"))

    for flag in red_flags:
        if flag == "ausencia_contrato" and subsidios_data.get("tem_contrato"):
            continue
        if flag == "ausencia_extrato" and subsidios_data.get("tem_extrato"):
            continue
        if flag == "ausencia_dossie" and subsidios_data.get("tem_dossie"):
            continue
        if flag == "ausencia_comprovante_credito" and subsidios_data.get("tem_comprovante"):
            continue
        if flag in {"assinatura_divergente", "assinatura_nao_validada"} and subsidios_data.get("assinatura_validada"):
            continue
        if flag == "canal_digital_incompativel" and actual_channel != "digital":
            continue
        if flag not in normalized:
            normalized.append(flag)

    return normalized


def _normalize_features_with_subsidios(
    payload: dict[str, Any],
    fallback: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> dict[str, Any]:
    normalized = _normalize_features_payload(payload, fallback)
    normalized["red_flags"] = _consistent_red_flags(normalized["red_flags"], subsidios_data)

    if _has_robust_defense_subsidios(subsidios_data) and not _has_objective_fraud_signal(normalized["red_flags"]):
        normalized["indicio_fraude"] = min(normalized["indicio_fraude"], 0.49)

    return normalized


def _normalize_autos_payload(payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    return {
        "numero_processo": _compact_text(_pick_payload_value(payload, "numero_processo", fallback.get("numero_processo")))
        or fallback.get("numero_processo"),
        "autor_nome": _compact_text(_pick_payload_value(payload, "autor_nome", fallback.get("autor_nome")))
        or fallback.get("autor_nome"),
        "autor_cpf": _compact_text(_pick_payload_value(payload, "autor_cpf", fallback.get("autor_cpf")))
        or fallback.get("autor_cpf"),
        "valor_causa": _parse_numeric_value(_pick_payload_value(payload, "valor_causa", fallback.get("valor_causa")))
        if _pick_payload_value(payload, "valor_causa", fallback.get("valor_causa")) is not None
        else fallback.get("valor_causa"),
        "alegacoes": coerce_list(_pick_payload_value(payload, "alegacoes", fallback.get("alegacoes")))
        or list(fallback.get("alegacoes") or []),
        "pedidos": coerce_list(_pick_payload_value(payload, "pedidos", fallback.get("pedidos")))
        or list(fallback.get("pedidos") or []),
        "valor_danos_morais": _parse_numeric_value(
            _pick_payload_value(
                payload,
                "valor_danos_morais",
                fallback.get("valor_danos_morais"),
                aliases=("valor_pedido_danos_morais",),
            )
        )
        if _pick_payload_value(
            payload,
            "valor_danos_morais",
            fallback.get("valor_danos_morais"),
            aliases=("valor_pedido_danos_morais",),
        )
        is not None
        else fallback.get("valor_danos_morais"),
    }


def _normalize_subsidios_payload(payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in (
        "tem_contrato",
        "tem_extrato",
        "tem_dossie",
        "tem_comprovante",
        "tem_demonstrativo_evolucao_divida",
        "tem_laudo_referenciado",
        "assinatura_validada",
        "documento_contraditorio",
    ):
        value = _pick_payload_value(payload, key, fallback.get(key))
        normalized[key] = coerce_bool(value)

    normalized["canal_contratacao"] = (
        coerce_canal_contratacao(_pick_payload_value(payload, "canal_contratacao", fallback.get("canal_contratacao")))
        or fallback.get("canal_contratacao")
    )
    value_emprestimo = _pick_payload_value(payload, "valor_emprestimo", fallback.get("valor_emprestimo"))
    normalized["valor_emprestimo"] = (
        _parse_numeric_value(value_emprestimo) if value_emprestimo is not None else fallback.get("valor_emprestimo")
    )
    return enforce_subsidios_consistency(normalized)


def _normalize_features_payload(payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    vulnerabilidade_raw = _pick_payload_value(
        payload,
        "vulnerabilidade_autor",
        fallback.get("vulnerabilidade_autor"),
    )
    return {
        "red_flags": _normalize_red_flags(_pick_payload_value(payload, "red_flags", fallback.get("red_flags")))
        or list(fallback.get("red_flags") or []),
        "vulnerabilidade_autor": coerce_vulnerabilidade(_extract_nested_text(vulnerabilidade_raw)),
        "indicio_fraude": _normalize_unit_interval(
            _pick_payload_value(payload, "indicio_fraude", fallback.get("indicio_fraude")),
            fallback.get("indicio_fraude", 0.0) or 0.0,
        ),
        "forca_narrativa_autor": _normalize_unit_interval(
            _pick_payload_value(payload, "forca_narrativa_autor", fallback.get("forca_narrativa_autor")),
            fallback.get("forca_narrativa_autor", 0.0) or 0.0,
        ),
        "inconsistencias_temporais": _normalize_inconsistencias_temporais(
            _pick_payload_value(
                payload,
                "inconsistencias_temporais",
                fallback.get("inconsistencias_temporais"),
            )
        )
        or list(fallback.get("inconsistencias_temporais") or []),
    }


def _compact_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalize_uf(value: Any) -> str | None:
    cleaned = re.sub(r"[^A-Za-z]", "", str(value or "")).upper()
    if cleaned in BRAZILIAN_UFS:
        return cleaned
    return None


def _has_usable_text(text: str) -> bool:
    return len(re.findall(r"[A-Za-zÀ-ÿ0-9]", text or "")) >= MIN_CONTEXT_TEXT_CHARS


def _build_case_text(
    autos_text: str,
    subsidios_text: str,
    autos_data: dict[str, Any],
    filenames: list[str] | None = None,
) -> str | None:
    combined = _compact_text("\n".join(part for part in (autos_text, subsidios_text) if part))
    if combined:
        return combined[:MAX_CASE_TEXT_LENGTH]

    fragments: list[str] = []
    if autos_data.get("numero_processo"):
        fragments.append(f"Processo {autos_data['numero_processo']}")
    if autos_data.get("autor_nome"):
        fragments.append(f"Autor {autos_data['autor_nome']}")
    if autos_data.get("alegacoes"):
        fragments.append(f"Alegações: {'; '.join(map(str, autos_data['alegacoes'][:3]))}")
    if autos_data.get("pedidos"):
        fragments.append(f"Pedidos: {'; '.join(map(str, autos_data['pedidos'][:3]))}")
    if filenames:
        fragments.append(f"Documentos recebidos: {', '.join(filenames[:6])}")

    built = ". ".join(fragment for fragment in fragments if fragment)
    return built[:MAX_CASE_TEXT_LENGTH] if built else None


def _infer_uf_from_texts(*texts: str) -> str | None:
    weights = Counter()
    patterns = [
        (r"\bCOMARCA DE [A-ZÀ-Ý0-9\s\-'ªº]+/([A-Z]{2})\b", 10),
        (r"\bVARA [A-ZÀ-Ý0-9\s\-'ªº]+ DA COMARCA DE [A-ZÀ-Ý0-9\s\-'ªº]+/([A-Z]{2})\b", 8),
        (r"\b(?:RESIDENTE|DOMICILIAD[OA])[^/\n]{0,140}/([A-Z]{2})\b", 7),
        (r"\bENDEREÇO(?: CADASTRADO)?[^/\n]{0,140}/([A-Z]{2})\b", 6),
        (r"\bNATURALIDADE\s+[A-ZÀ-Ý\s\-'ªº]+/([A-Z]{2})\b", 5),
        (r"\bUF DE RESID[ÊE]NCIA\s+([A-Z]{2})\b", 8),
        (r"\bSSP/([A-Z]{2})\b", 5),
        (r"\bOAB/([A-Z]{2})\b", 4),
    ]

    for text in texts:
        upper_text = str(text or "").upper()
        for pattern, weight in patterns:
            for match in re.finditer(pattern, upper_text):
                uf = _normalize_uf(match.group(1))
                if uf:
                    weights[uf] += weight

    return weights.most_common(1)[0][0] if weights else None


def _infer_assunto(
    combined_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> str | None:
    haystacks = [
        str(combined_text or "").casefold(),
        " ".join(map(str, autos_data.get("alegacoes") or [])).casefold(),
        " ".join(map(str, autos_data.get("pedidos") or [])).casefold(),
    ]
    markers = (
        "não reconhece a contratação",
        "não reconhece contratação",
        "não reconhece opera",
        "desconhece a contratação",
        "nunca contratou",
        "inexistência de débito",
        "inexistencia de débito",
        "inexistencia de debito",
        "inexistência de contrato",
        "inexistencia de contrato",
        "desconto indevido",
        "empréstimo consignado",
        "emprestimo consignado",
    )

    if any(marker in haystack for haystack in haystacks for marker in markers):
        return HISTORY_ASSUNTO_DEFAULT

    if subsidios_data and any(
        subsidios_data.get(key) for key in ("tem_contrato", "tem_extrato", "tem_comprovante", "tem_dossie")
    ):
        if autos_data.get("numero_processo") and autos_data.get("pedidos"):
            return HISTORY_ASSUNTO_DEFAULT

    return None


def _infer_sub_assunto(
    combined_text: str,
    features_data: dict[str, Any],
    assunto: str | None,
    subsidios_data: dict[str, Any] | None = None,
) -> str | None:
    lowered = str(combined_text or "").casefold()
    fraud_markers = (
        "golpe",
        "boletim de ocorrência",
        "boletim de ocorrencia",
        "delegacia",
        "conta de terceiros",
        "conta de titularidade supostamente",
        "uso indevido de sua identidade",
        "não foi localizado",
        "nao foi localizado",
        "vídeo de liveness",
        "video de liveness",
        "assinatura falsa",
        "assinatura diverg",
    )
    red_flags = {str(flag).casefold() for flag in features_data.get("red_flags") or []}
    indicio_fraude = _normalize_unit_interval(features_data.get("indicio_fraude"), 0.0)
    has_strong_marker = any(marker in lowered for marker in fraud_markers)
    has_signature_issue = "assinatura_divergente" in red_flags
    has_high_fraud_signal = indicio_fraude >= 0.55 and has_strong_marker
    if _has_robust_defense_subsidios(subsidios_data or {}) and not _has_objective_fraud_signal(list(red_flags)):
        has_strong_marker = False
        has_signature_issue = False
        has_high_fraud_signal = False

    if has_strong_marker or has_signature_issue or has_high_fraud_signal:
        return HISTORY_SUBASSUNTO_GOLPE

    if assunto == HISTORY_ASSUNTO_DEFAULT:
        return HISTORY_SUBASSUNTO_GENERIC

    return None


def _normalize_assunto(
    value: Any,
    *,
    combined_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> str | None:
    cleaned = _compact_text(value)
    lowered = cleaned.casefold()

    if not cleaned:
        return _infer_assunto(combined_text, autos_data, subsidios_data)

    if any(
        marker in lowered
        for marker in (
            "não reconhece",
            "nao reconhece",
            "não reconhece opera",
            "nao reconhece opera",
            "inexistência de débito",
            "inexistencia de debito",
            "inexistência de contrato",
            "inexistencia de contrato",
            "empréstimo consignado",
            "emprestimo consignado",
            "contratação indevida",
            "contratacao indevida",
        )
    ):
        return HISTORY_ASSUNTO_DEFAULT

    return cleaned[:255]


def _normalize_sub_assunto(
    value: Any,
    *,
    combined_text: str,
    features_data: dict[str, Any],
    assunto: str | None,
    subsidios_data: dict[str, Any] | None = None,
) -> str | None:
    cleaned = _compact_text(value)
    lowered = cleaned.casefold()
    prefer_generic = _has_robust_defense_subsidios(subsidios_data or {}) and not _has_objective_fraud_signal(
        list(features_data.get("red_flags") or [])
    )

    if not cleaned:
        return _infer_sub_assunto(combined_text, features_data, assunto, subsidios_data)

    if any(marker in lowered for marker in ("golpe", "fraude", "assinatura", "biometria", "liveness")) and not prefer_generic:
        return HISTORY_SUBASSUNTO_GOLPE
    if any(marker in lowered for marker in ("genérico", "generico", "contratação", "contratacao", "desconto")):
        return HISTORY_SUBASSUNTO_GENERIC if assunto == HISTORY_ASSUNTO_DEFAULT else cleaned[:255]

    inferred = _infer_sub_assunto(combined_text, features_data, assunto, subsidios_data)
    return inferred or cleaned[:255]


def heuristic_extract_case_context(
    autos_text: str,
    subsidios_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
    features_data: dict[str, Any],
    filenames: list[str] | None = None,
) -> dict[str, Any]:
    combined_text = "\n\n".join(part for part in (autos_text, subsidios_text) if part).strip()
    assunto = _infer_assunto(combined_text, autos_data, subsidios_data)

    return {
        "uf": _infer_uf_from_texts(autos_text, subsidios_text),
        "assunto": assunto,
        "sub_assunto": _infer_sub_assunto(combined_text, features_data, assunto, subsidios_data),
        "case_text": _build_case_text(autos_text, subsidios_text, autos_data, filenames),
        "text_quality": "ok" if _has_usable_text(combined_text) else "low" if combined_text else "missing",
        "ocr_recommended": not _has_usable_text(combined_text),
    }


def extract_case_context_structured(
    autos_text: str,
    subsidios_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
    features_data: dict[str, Any],
    filenames: list[str] | None = None,
) -> dict[str, Any]:
    heuristic_payload = heuristic_extract_case_context(
        autos_text,
        subsidios_text,
        autos_data,
        subsidios_data,
        features_data,
        filenames=filenames,
    )

    combined_text = "\n\n".join(part for part in (autos_text, subsidios_text) if part).strip()
    if not _has_usable_text(combined_text):
        return heuristic_payload

    settings = get_settings()
    user_payload = json.dumps(
        {
            "autos_text": autos_text[:18000],
            "subsidios_text": subsidios_text[:18000],
            "autos_data": autos_data,
            "subsidios_data": subsidios_data,
            "features_data": features_data,
            "filenames": filenames or [],
        },
        ensure_ascii=False,
    )
    payload = chat_json_prompt(settings.analysis_model, "extract_context.txt", user_payload) or {}
    assunto = _normalize_assunto(
        payload.get("assunto"),
        combined_text=combined_text,
        autos_data=autos_data,
        subsidios_data=subsidios_data,
    )
    return {
        "uf": _normalize_uf(payload.get("uf")) or heuristic_payload["uf"],
        "assunto": assunto,
        "sub_assunto": _normalize_sub_assunto(
            payload.get("sub_assunto"),
            combined_text=combined_text,
            features_data=features_data,
            assunto=assunto,
            subsidios_data=subsidios_data,
        ),
        "case_text": (_compact_text(payload.get("case_text")) or heuristic_payload["case_text"]),
        "text_quality": heuristic_payload["text_quality"],
        "ocr_recommended": heuristic_payload["ocr_recommended"],
    }


def heuristic_extract_autos(text: str) -> dict[str, Any]:
    numero_match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", text)
    numero_processo = numero_match.group(0) if numero_match else None

    autor_nome = None
    autor_match = re.search(
        r"(?m)^\s*([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s]{5,}?),\s+brasileir[ao]\b",
        text,
    )
    if autor_match:
        autor_nome = " ".join(autor_match.group(1).split())

    autor_cpf = None
    cpf_match = re.search(r"CPF(?:/MF)?[^0-9]{0,20}([\d\.\-]{11,14})", text, re.IGNORECASE)
    if cpf_match:
        autor_cpf = cpf_match.group(1)

    valor_causa = None
    for pattern in (
        r"valor da causa[^R\n]*R\$\s*([\d\.\,]+)",
        r"à causa o valor de[^R\n]*R\$\s*([\d\.\,]+)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            valor_causa = float(match.group(1).replace(".", "").replace(",", "."))
            break

    pedidos = []
    for keyword in (
        "dano moral",
        "repetição de indébito",
        "tutela antecipada",
        "inversão do ônus da prova",
        "declaração de inexistência",
    ):
        if keyword in text.lower():
            pedidos.append(keyword)

    alegacoes = []
    for keyword in (
        "não reconhece a contratação",
        "não reconhece contratação",
        "assinatura falsa",
        "desconto indevido",
        "fraude",
        "golpe",
    ):
        if keyword in text.lower():
            alegacoes.append(keyword)

    valor_danos = None
    for pattern in (
        r"danos morais[^R\n]*R\$\s*([\d\.\,]+)",
        r"dano moral[^R\n]*R\$\s*([\d\.\,]+)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            valor_danos = float(match.group(1).replace(".", "").replace(",", "."))
            break

    return {
        "numero_processo": numero_processo,
        "autor_nome": autor_nome,
        "autor_cpf": autor_cpf,
        "valor_causa": valor_causa or _parse_brl_value(text),
        "alegacoes": alegacoes,
        "pedidos": pedidos,
        "valor_danos_morais": valor_danos,
    }


def heuristic_extract_subsidios(text: str) -> dict[str, Any]:
    lowered = text.lower()
    has_positive_auth = (
        "assinatura validada" in lowered
        or ("assinatura" in lowered and ("compatível" in lowered or "compativel" in lowered))
        or ("assinatura" in lowered and "conformidade" in lowered)
        or ("biometria" in lowered and ("validada" in lowered or "compatível" in lowered or "compativel" in lowered))
    )
    has_negative_auth = (
        "assinatura diverg" in lowered
        or "assinatura falsa" in lowered
        or "nao validada" in lowered
        or "não validada" in lowered
    )
    return enforce_subsidios_consistency(
        {
        "tem_contrato": "contrato" in lowered,
        "tem_extrato": "extrato" in lowered,
        "tem_dossie": "dossi" in lowered or "dossie" in lowered,
        "tem_comprovante": "comprovante" in lowered or "bacen" in lowered,
        "tem_demonstrativo_evolucao_divida": (
            "demonstrativo" in lowered and ("evolução" in lowered or "evolucao" in lowered or "dívida" in lowered or "divida" in lowered)
        ),
        "tem_laudo_referenciado": "laudo referenciado" in lowered or ("laudo" in lowered and "liveness" in lowered),
        "assinatura_validada": has_positive_auth,
        "canal_contratacao": coerce_canal_contratacao(lowered),
        "valor_emprestimo": _parse_brl_value(text),
        "documento_contraditorio": has_positive_auth and has_negative_auth,
        }
    )


def heuristic_extract_features(
    autos_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> dict[str, Any]:
    lowered = autos_text.lower()
    red_flags: list[str] = []
    if "fraude" in lowered or "golpe" in lowered:
        red_flags.append("indicio_fraude_autor")
    if "idos" in lowered:
        red_flags.append("autor_potencialmente_idoso")
    if "assinatura" in lowered and "diverg" in lowered:
        red_flags.append("assinatura_divergente")
    if not subsidios_data.get("tem_contrato"):
        red_flags.append("ausencia_contrato")
    if not subsidios_data.get("tem_comprovante"):
        red_flags.append("ausencia_comprovante_credito")

    vulnerabilidade = "idoso" if "idos" in lowered else "analfabeto" if "analfabet" in lowered else "nenhuma"
    indicio = 0.2
    if "fraude" in lowered or "golpe" in lowered:
        indicio += 0.35
    if not subsidios_data.get("tem_contrato"):
        indicio += 0.1
    if not subsidios_data.get("tem_comprovante"):
        indicio += 0.1
    narrativa = min(0.9, 0.35 + len(autos_data.get("alegacoes", [])) * 0.12 + len(autos_data.get("pedidos", [])) * 0.08)

    return {
        "red_flags": red_flags,
        "vulnerabilidade_autor": vulnerabilidade,
        "indicio_fraude": round(min(indicio, 0.95), 2),
        "forca_narrativa_autor": round(narrativa, 2),
        "inconsistencias_temporais": [],
    }


def extract_autos_structured(text: str) -> dict[str, Any]:
    fallback = heuristic_extract_autos(text)
    settings = get_settings()
    payload = chat_json_prompt(settings.extract_model, "extract_autos.txt", text)
    if not payload:
        return fallback
    return _normalize_autos_payload(payload, fallback)


def extract_subsidios_structured(text: str) -> dict[str, Any]:
    fallback = heuristic_extract_subsidios(text)
    settings = get_settings()
    payload = chat_json_prompt(settings.extract_model, "extract_subsidios.txt", text)
    if not payload:
        return fallback
    return _normalize_subsidios_payload(payload, fallback)


def extract_features_structured(
    autos_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> dict[str, Any]:
    fallback = heuristic_extract_features(autos_text, autos_data, subsidios_data)
    settings = get_settings()
    user_payload = json.dumps(
        {
            "autos_text": autos_text[:18000],
            "autos_data": autos_data,
            "subsidios_data": subsidios_data,
        },
        ensure_ascii=False,
    )
    payload = chat_json_prompt(settings.analysis_model, "extract_features.txt", user_payload)
    if not payload:
        return fallback
    return _normalize_features_with_subsidios(payload, fallback, subsidios_data)


def build_embedding_payload(
    text: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    allow_local_fallback: bool = True,
) -> dict[str, Any] | None:
    client = get_openai_client()
    settings = get_settings()
    requested_provider = (provider or "").strip().lower()
    requested_model = model or settings.embedding_model

    if requested_provider.startswith("legacy"):
        requested_provider = "local"

    should_use_openai = requested_provider in {"", "openai"} and client is not None
    if should_use_openai:
        try:
            embedding = client.embeddings.create(
                model=requested_model,
                input=text[:20000],
            )
            vector = embedding.data[0].embedding
            return {
                "vector": vector,
                "provider": "openai",
                "model": requested_model,
                "dimensions": len(vector),
            }
        except Exception as exc:
            logger.warning(
                "OpenAI embeddings falhou para model=%s provider=%s: %s",
                requested_model,
                requested_provider or "default",
                exc,
            )
            if not allow_local_fallback:
                return None

    if requested_provider == "openai" and not allow_local_fallback:
        return None

    vector = build_local_embedding_list(text)
    return {
        "vector": vector,
        "provider": "local",
        "model": LOCAL_EMBEDDING_MODEL,
        "dimensions": len(vector),
    }


def embed_peticao(text: str) -> list[float]:
    payload = build_embedding_payload(text)
    return list(payload["vector"]) if payload else []
