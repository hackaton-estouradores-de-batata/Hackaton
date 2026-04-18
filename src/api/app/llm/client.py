from collections import Counter
from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.analytics.semantic import LOCAL_EMBEDDING_MODEL, build_local_embedding_list
from app.core.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI | None:
    api_key = get_settings().openai_api_key
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


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
            messages=[
                {"role": "system", "content": load_prompt(prompt_name)},
                {"role": "user", "content": user_payload},
            ],
        )
        content = completion.choices[0].message.content
    except Exception:
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
    indicio_fraude = float(features_data.get("indicio_fraude", 0.0) or 0.0)
    has_strong_marker = any(marker in lowered for marker in fraud_markers)
    has_signature_issue = "assinatura_divergente" in red_flags
    has_high_fraud_signal = indicio_fraude >= 0.55 and has_strong_marker

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
            "não reconhece opera",
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
) -> str | None:
    cleaned = _compact_text(value)
    lowered = cleaned.casefold()

    if not cleaned:
        return _infer_sub_assunto(combined_text, features_data, assunto)

    if any(marker in lowered for marker in ("golpe", "fraude", "assinatura", "biometria", "liveness")):
        return HISTORY_SUBASSUNTO_GOLPE
    if any(marker in lowered for marker in ("genérico", "generico", "contratação", "contratacao", "desconto")):
        return HISTORY_SUBASSUNTO_GENERIC if assunto == HISTORY_ASSUNTO_DEFAULT else cleaned[:255]

    inferred = _infer_sub_assunto(combined_text, features_data, assunto)
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
        "sub_assunto": _infer_sub_assunto(combined_text, features_data, assunto),
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
    return {
        "tem_contrato": "contrato" in lowered,
        "tem_extrato": "extrato" in lowered,
        "tem_dossie": "dossi" in lowered or "dossie" in lowered,
        "tem_comprovante": "comprovante" in lowered or "bacen" in lowered,
        "assinatura_validada": "assinatura validada" in lowered or "biometria" in lowered,
        "canal_contratacao": (
            "digital"
            if "digital" in lowered
            else "correspondente"
            if "correspondente" in lowered
            else "presencial"
            if "agência" in lowered or "agencia" in lowered
            else None
        ),
        "valor_emprestimo": _parse_brl_value(text),
    }


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
    settings = get_settings()
    payload = chat_json_prompt(settings.extract_model, "extract_autos.txt", text)
    return payload if payload else heuristic_extract_autos(text)


def extract_subsidios_structured(text: str) -> dict[str, Any]:
    settings = get_settings()
    payload = chat_json_prompt(settings.extract_model, "extract_subsidios.txt", text)
    return payload if payload else heuristic_extract_subsidios(text)


def extract_features_structured(
    autos_text: str,
    autos_data: dict[str, Any],
    subsidios_data: dict[str, Any],
) -> dict[str, Any]:
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
    return payload if payload else heuristic_extract_features(autos_text, autos_data, subsidios_data)


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
        except Exception:
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
