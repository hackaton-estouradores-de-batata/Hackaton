from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.analytics.semantic import build_local_embedding_list
from app.core.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI | None:
    api_key = get_settings().openai_api_key
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


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


def heuristic_extract_autos(text: str) -> dict[str, Any]:
    numero_match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", text)
    numero_processo = numero_match.group(0) if numero_match else None

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


def embed_peticao(text: str) -> list[float]:
    client = get_openai_client()
    settings = get_settings()
    if client is not None:
        try:
            embedding = client.embeddings.create(
                model=settings.embedding_model,
                input=text[:20000],
            )
            return embedding.data[0].embedding
        except Exception:
            pass

    return build_local_embedding_list(text)
