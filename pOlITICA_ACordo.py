from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from typing import Any, Dict, List, Optional


getcontext().prec = 28


MatrixRow = Dict[str, Any]
Matrix = Dict[str, MatrixRow]


SUB_GENERICO = "generico"
SUB_GOLPE = "golpe"
SUB_INDEFINIDO = "indefinido"


MIN_SUCCESS = Decimal("0.01")
MAX_SUCCESS = Decimal("0.98")


W_DOC = {
	0: Decimal("0.05"),
	1: Decimal("0.15"),
	2: Decimal("0.30"),
	3: Decimal("0.45"),
	4: Decimal("0.60"),
	5: Decimal("0.75"),
	6: Decimal("0.90"),
}


DISCOUNT_BY_UF: Dict[str, Decimal] = {
	"AC": Decimal("0.32"),
	"AL": Decimal("0.31"),
	"AM": Decimal("0.16"),
	"AP": Decimal("0.16"),
	"BA": Decimal("0.20"),
	"CE": Decimal("0.32"),
	"DF": Decimal("0.31"),
	"ES": Decimal("0.32"),
	"GO": Decimal("0.28"),
	"MA": Decimal("0.40"),
	"MT": Decimal("0.39"),
	"MS": Decimal("0.39"),
	"MG": Decimal("0.32"),
	"PA": Decimal("0.32"),
	"PB": Decimal("0.32"),
	"PR": Decimal("0.31"),
	"PE": Decimal("0.32"),
	"PI": Decimal("0.31"),
	"RJ": Decimal("0.32"),
	"RN": Decimal("0.31"),
	"RS": Decimal("0.27"),
	"RO": Decimal("0.31"),
	"SC": Decimal("0.31"),
	"SP": Decimal("0.31"),
	"SE": Decimal("0.33"),
	"TO": Decimal("0.31"),
}


def _row(d0: str, d1: str, d2: str, d3: str, d4: str, d5: str, d6: str, total: str) -> MatrixRow:
	return {
		"D": [Decimal(d0), Decimal(d1), Decimal(d2), Decimal(d3), Decimal(d4), Decimal(d5), Decimal(d6)],
		"T": Decimal(total),
	}


MATRIZ_GERAL_6D: Matrix = {
	"AC": _row("0.00", "0.07", "0.12", "0.38", "0.70", "0.87", "0.98", "0.72"),
	"AL": _row("0.00", "0.00", "0.10", "0.34", "0.63", "0.87", "0.98", "0.69"),
	"AM": _row("0.00", "0.02", "0.05", "0.17", "0.47", "0.77", "0.93", "0.52"),
	"AP": _row("0.00", "0.00", "0.05", "0.18", "0.45", "0.77", "0.92", "0.52"),
	"BA": _row("0.00", "0.00", "0.10", "0.30", "0.58", "0.87", "0.96", "0.65"),
	"CE": _row("0.00", "0.00", "0.12", "0.40", "0.65", "0.89", "0.95", "0.72"),
	"DF": _row("0.00", "0.00", "0.16", "0.32", "0.63", "0.85", "0.96", "0.67"),
	"ES": _row("0.00", "0.00", "0.08", "0.30", "0.62", "0.86", "0.95", "0.67"),
	"GO": _row("0.00", "0.03", "0.11", "0.27", "0.57", "0.84", "0.97", "0.62"),
	"MA": _row("0.00", "0.00", "0.16", "0.43", "0.75", "0.92", "0.98", "0.79"),
	"MG": _row("0.00", "0.00", "0.18", "0.37", "0.66", "0.85", "0.96", "0.70"),
	"MS": _row("0.00", "0.00", "0.18", "0.36", "0.70", "0.91", "0.98", "0.75"),
	"MT": _row("0.00", "0.14", "0.20", "0.42", "0.69", "0.90", "0.97", "0.76"),
	"PA": _row("0.00", "0.10", "0.15", "0.34", "0.66", "0.87", "0.98", "0.72"),
	"PB": _row("0.00", "0.00", "0.17", "0.36", "0.66", "0.89", "0.96", "0.71"),
	"PE": _row("0.00", "0.03", "0.11", "0.33", "0.64", "0.87", "0.97", "0.69"),
	"PI": _row("0.00", "0.00", "0.20", "0.45", "0.76", "0.92", "0.97", "0.77"),
	"PR": _row("0.00", "0.07", "0.17", "0.40", "0.70", "0.89", "0.98", "0.74"),
	"RJ": _row("0.00", "0.03", "0.09", "0.32", "0.58", "0.86", "0.92", "0.65"),
	"RN": _row("0.00", "0.05", "0.17", "0.45", "0.69", "0.89", "0.96", "0.76"),
	"RO": _row("0.00", "0.00", "0.19", "0.40", "0.70", "0.89", "0.99", "0.74"),
	"RS": _row("0.00", "0.04", "0.14", "0.28", "0.57", "0.80", "0.93", "0.62"),
	"SC": _row("0.00", "0.05", "0.17", "0.36", "0.67", "0.89", "0.97", "0.73"),
	"SE": _row("0.00", "0.09", "0.10", "0.34", "0.63", "0.88", "0.96", "0.71"),
	"SP": _row("0.00", "0.08", "0.08", "0.34", "0.64", "0.88", "0.95", "0.69"),
	"TO": _row("0.00", "0.00", "0.13", "0.41", "0.71", "0.88", "0.97", "0.75"),
	"TOTAL": _row("0.00", "0.03", "0.13", "0.34", "0.64", "0.87", "0.96", "0.70"),
}


MATRIZ_GENERICO_6D: Matrix = {
	"AC": _row("0.00", "0.22", "0.20", "0.49", "0.83", "0.95", "0.99", "0.85"),
	"AL": _row("0.00", "0.00", "0.21", "0.55", "0.77", "0.94", "0.98", "0.83"),
	"AM": _row("0.00", "0.06", "0.06", "0.25", "0.60", "0.89", "0.95", "0.66"),
	"AP": _row("0.00", "0.00", "0.15", "0.28", "0.61", "0.86", "0.96", "0.68"),
	"BA": _row("0.00", "0.00", "0.15", "0.39", "0.71", "0.94", "0.98", "0.77"),
	"CE": _row("0.00", "0.00", "0.22", "0.51", "0.80", "0.95", "0.98", "0.84"),
	"DF": _row("0.00", "0.00", "0.24", "0.50", "0.77", "0.91", "0.99", "0.80"),
	"ES": _row("0.00", "0.00", "0.17", "0.35", "0.79", "0.92", "0.92", "0.79"),
	"GO": _row("0.00", "0.00", "0.15", "0.45", "0.70", "0.90", "0.99", "0.75"),
	"MA": _row("0.00", "0.00", "0.50", "0.56", "0.90", "0.97", "0.99", "0.92"),
	"MG": _row("0.00", "0.00", "0.27", "0.59", "0.78", "0.95", "0.98", "0.83"),
	"MS": _row("0.00", "0.00", "0.47", "0.55", "0.85", "0.95", "0.98", "0.89"),
	"MT": _row("0.00", "0.25", "0.43", "0.79", "0.85", "0.97", "1.00", "0.91"),
	"PA": _row("0.00", "0.00", "0.29", "0.53", "0.83", "0.94", "0.99", "0.85"),
	"PB": _row("0.00", "0.00", "0.35", "0.55", "0.82", "0.94", "0.96", "0.84"),
	"PE": _row("0.00", "0.00", "0.27", "0.49", "0.80", "0.93", "0.99", "0.83"),
	"PI": _row("0.00", "0.00", "0.48", "0.68", "0.90", "0.96", "0.99", "0.90"),
	"PR": _row("0.00", "0.14", "0.48", "0.63", "0.88", "0.97", "1.00", "0.90"),
	"RJ": _row("0.00", "0.00", "0.20", "0.43", "0.71", "0.93", "0.95", "0.77"),
	"RN": _row("0.00", "0.20", "0.41", "0.75", "0.86", "0.94", "0.97", "0.89"),
	"RO": _row("0.00", "0.00", "0.42", "0.60", "0.86", "0.94", "1.00", "0.87"),
	"RS": _row("0.00", "0.14", "0.23", "0.40", "0.72", "0.91", "0.95", "0.77"),
	"SC": _row("0.00", "0.00", "0.39", "0.53", "0.82", "0.94", "0.99", "0.86"),
	"SE": _row("0.00", "0.25", "0.33", "0.56", "0.79", "0.94", "0.98", "0.85"),
	"SP": _row("0.00", "0.11", "0.13", "0.47", "0.80", "0.95", "0.98", "0.83"),
	"TO": _row("0.00", "0.00", "0.26", "0.65", "0.87", "0.94", "0.99", "0.88"),
	"TOTAL": _row("0.00", "0.06", "0.26", "0.50", "0.80", "0.94", "0.98", "0.83"),
}


MATRIZ_GOLPE_6D: Matrix = {
	"AC": _row("0.00", "0.00", "0.10", "0.35", "0.64", "0.84", "0.98", "0.67"),
	"AL": _row("0.00", "0.00", "0.07", "0.29", "0.56", "0.83", "0.98", "0.63"),
	"AM": _row("0.00", "0.00", "0.05", "0.15", "0.41", "0.71", "0.91", "0.46"),
	"AP": _row("0.00", "0.00", "0.03", "0.14", "0.39", "0.72", "0.89", "0.44"),
	"BA": _row("0.00", "0.00", "0.09", "0.28", "0.53", "0.83", "0.94", "0.59"),
	"CE": _row("0.00", "0.00", "0.09", "0.36", "0.59", "0.86", "0.94", "0.66"),
	"DF": _row("0.00", "0.00", "0.12", "0.26", "0.56", "0.82", "0.94", "0.62"),
	"ES": _row("0.00", "0.00", "0.06", "0.28", "0.53", "0.82", "0.97", "0.61"),
	"GO": _row("0.00", "0.03", "0.09", "0.21", "0.51", "0.81", "0.96", "0.56"),
	"MA": _row("0.00", "0.00", "0.12", "0.39", "0.68", "0.89", "0.97", "0.74"),
	"MG": _row("0.00", "0.00", "0.15", "0.30", "0.59", "0.80", "0.95", "0.64"),
	"MS": _row("0.00", "0.00", "0.14", "0.31", "0.63", "0.88", "0.98", "0.69"),
	"MT": _row("0.00", "0.11", "0.16", "0.33", "0.62", "0.87", "0.95", "0.70"),
	"PA": _row("0.00", "0.12", "0.13", "0.28", "0.59", "0.84", "0.97", "0.66"),
	"PB": _row("0.00", "0.00", "0.13", "0.29", "0.59", "0.87", "0.96", "0.66"),
	"PE": _row("0.00", "0.04", "0.08", "0.28", "0.57", "0.85", "0.95", "0.64"),
	"PI": _row("0.00", "0.00", "0.15", "0.36", "0.69", "0.90", "0.96", "0.72"),
	"PR": _row("0.00", "0.05", "0.10", "0.34", "0.63", "0.85", "0.97", "0.68"),
	"RJ": _row("0.00", "0.03", "0.07", "0.27", "0.52", "0.83", "0.91", "0.60"),
	"RN": _row("0.00", "0.00", "0.12", "0.34", "0.60", "0.87", "0.96", "0.70"),
	"RO": _row("0.00", "0.00", "0.14", "0.34", "0.63", "0.86", "0.98", "0.69"),
	"RS": _row("0.00", "0.00", "0.11", "0.24", "0.51", "0.75", "0.92", "0.56"),
	"SC": _row("0.00", "0.06", "0.13", "0.31", "0.61", "0.87", "0.95", "0.67"),
	"SE": _row("0.00", "0.05", "0.05", "0.28", "0.56", "0.86", "0.95", "0.65"),
	"SP": _row("0.00", "0.06", "0.07", "0.30", "0.57", "0.84", "0.94", "0.63"),
	"TO": _row("0.00", "0.00", "0.10", "0.34", "0.65", "0.86", "0.96", "0.70"),
	"TOTAL": _row("0.00", "0.02", "0.10", "0.29", "0.57", "0.84", "0.95", "0.64"),
}


@dataclass
class CaseInput:
	ped: Decimal
	uf: str
	sub: Optional[str] = None
	contrato: bool = False
	comprovante_credito: bool = False
	extrato: bool = False
	demonstrativo_evolucao_divida: bool = False
	dossie: bool = False
	laudo_referenciado: bool = False
	documento_contraditorio: bool = False
	qtd_docs_override: Optional[int] = None


@dataclass
class PoliticaResultadoV5:
	decisao: str
	justificativa_curta: str
	ped: Decimal
	uf: str
	sub: str
	matriz_escolhida: str
	uf_sem_historico_proprio: bool
	revisao_humana: bool
	qtd_docs: int
	p_raw: List[Decimal]
	p_corr: List[Decimal]
	p_suc: Decimal
	p_per: Decimal
	desc_uf: Decimal
	f_pag: Decimal
	vpc: Decimal
	vej: Decimal
	f_ab: Decimal
	f_al: Decimal
	f_tet: Decimal
	abertura_bruta: Decimal
	alvo_bruto: Decimal
	teto_bruto: Decimal
	abertura: Decimal
	alvo: Decimal
	teto: Decimal
	teto_pct: Decimal

	def to_dict(self) -> Dict[str, Any]:
		return _to_jsonable(asdict(self))


def _to_jsonable(value: Any) -> Any:
	if isinstance(value, Decimal):
		return float(value)
	if isinstance(value, dict):
		return {k: _to_jsonable(v) for k, v in value.items()}
	if isinstance(value, list):
		return [_to_jsonable(v) for v in value]
	return value


def _clamp(value: Decimal, min_value: Decimal, max_value: Decimal) -> Decimal:
	return max(min_value, min(value, max_value))


def _round_to_nearest_100(value: Decimal) -> Decimal:
	return (value / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("100")


def _max_hundred_below(value: Decimal) -> Decimal:
	if value <= 0:
		return Decimal("0")
	base = ((value - Decimal("0.01")) / Decimal("100")).to_integral_value(rounding=ROUND_FLOOR)
	return max(Decimal("0"), base * Decimal("100"))


def _normalize_uf(uf: str) -> str:
	return uf.strip().upper()


def _normalize_sub(sub: Optional[str]) -> str:
	if sub is None:
		return SUB_INDEFINIDO
	sub_norm = sub.strip().lower()
	if sub_norm in {SUB_GENERICO, SUB_GOLPE}:
		return sub_norm
	return SUB_INDEFINIDO


def _count_qtd_docs(case: CaseInput) -> int:
	if case.qtd_docs_override is not None:
		if case.qtd_docs_override < 0 or case.qtd_docs_override > 6:
			raise ValueError("qtd_docs_override deve estar entre 0 e 6")
		return case.qtd_docs_override

	return (
		int(case.contrato)
		+ int(case.comprovante_credito)
		+ int(case.extrato)
		+ int(case.demonstrativo_evolucao_divida)
		+ int(case.dossie)
		+ int(case.laudo_referenciado)
	)


def _select_matrix(sub: str) -> tuple[str, Matrix]:
	if sub == SUB_GENERICO:
		return "MATRIZ_GENERICO_6D", MATRIZ_GENERICO_6D
	if sub == SUB_GOLPE:
		return "MATRIZ_GOLPE_6D", MATRIZ_GOLPE_6D
	return "MATRIZ_GERAL_6D", MATRIZ_GERAL_6D


def _build_justificativa(decisao: str, ped: Decimal, vej: Decimal, alvo: Decimal, teto: Decimal) -> str:
	if decisao == "ACORDO":
		ganho = vej - alvo
		return f"ACORDO porque o ALVO fica abaixo do VEJ em R$ {ganho:.2f}."

	piso_comercial = ped * Decimal("0.25")
	diff = piso_comercial - vej
	return f"DEFESA porque o TETO racional fica abaixo do piso comercial em R$ {diff:.2f}."


def _enforce_offer_invariants(
	abertura: Decimal,
	alvo: Decimal,
	teto: Decimal,
	vej: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
	alvo = max(alvo, abertura)
	teto = max(teto, alvo)

	if teto >= vej:
		teto = _max_hundred_below(vej)
		alvo = min(alvo, teto)
		abertura = min(abertura, alvo)

	return max(abertura, Decimal("0")), max(alvo, Decimal("0")), max(teto, Decimal("0"))


def calcular_politica_v5(case: CaseInput) -> PoliticaResultadoV5:
	if case.ped <= 0:
		raise ValueError("PED deve ser maior que zero")

	uf = _normalize_uf(case.uf)
	sub = _normalize_sub(case.sub)
	qtd_docs = _count_qtd_docs(case)

	matrix_name, matrix = _select_matrix(sub)
	uf_key = uf if uf in matrix else "TOTAL"
	uf_sem_historico_proprio = uf_key == "TOTAL" and uf != "TOTAL"

	desc_uf = DISCOUNT_BY_UF.get(uf, Decimal("0.30"))
	total_row = matrix["TOTAL"]
	uf_row = matrix[uf_key]

	p_raw: List[Decimal] = [Decimal("0") for _ in range(7)]

	for d in range(1, 7):
		p_total_d = total_row["D"][d]
		p_cel_d = uf_row["D"][d]
		p_raw[d] = p_total_d + W_DOC[d] * (p_cel_d - p_total_d)

	p1_proxy = p_raw[1]
	gap0 = total_row["D"][1] - total_row["D"][0]
	uf_shift = uf_row["T"] - total_row["T"]
	p0_context = total_row["D"][0] + Decimal("0.15") * uf_shift
	p_raw[0] = _clamp(min(p0_context, p1_proxy - gap0), Decimal("0"), p1_proxy)

	p_corr: List[Decimal] = [Decimal("0") for _ in range(7)]
	p_corr[0] = _clamp(p_raw[0], Decimal("0"), MAX_SUCCESS)
	for d in range(1, 7):
		p_corr[d] = _clamp(max(p_raw[d], p_corr[d - 1]), Decimal("0"), MAX_SUCCESS)

	p_suc = _clamp(p_corr[qtd_docs], MIN_SUCCESS, MAX_SUCCESS)
	p_per = Decimal("1") - p_suc

	f_pag = Decimal("1") - desc_uf
	vpc = case.ped * f_pag
	vej = vpc * p_per

	f_ab = _clamp(Decimal("0.90") - Decimal("0.05") * Decimal(qtd_docs), Decimal("0.60"), Decimal("0.95"))
	f_al = _clamp(f_ab + Decimal("0.08"), Decimal("0.65"), Decimal("0.97"))
	f_tet = _clamp(f_ab + Decimal("0.15"), Decimal("0.70"), Decimal("0.99"))

	abertura_bruta = vej * f_ab
	alvo_bruto = vej * f_al
	teto_bruto = vej * f_tet

	abertura = _round_to_nearest_100(abertura_bruta)
	alvo = _round_to_nearest_100(alvo_bruto)
	teto = _round_to_nearest_100(teto_bruto)
	abertura, alvo, teto = _enforce_offer_invariants(abertura, alvo, teto, vej)

	teto_pct = teto / case.ped
	decisao = "ACORDO" if teto_pct >= Decimal("0.25") else "DEFESA"
	justificativa = _build_justificativa(decisao, case.ped, vej, alvo, teto)

	return PoliticaResultadoV5(
		decisao=decisao,
		justificativa_curta=justificativa,
		ped=case.ped,
		uf=uf,
		sub=sub,
		matriz_escolhida=matrix_name,
		uf_sem_historico_proprio=uf_sem_historico_proprio,
		revisao_humana=case.documento_contraditorio,
		qtd_docs=qtd_docs,
		p_raw=p_raw,
		p_corr=p_corr,
		p_suc=p_suc,
		p_per=p_per,
		desc_uf=desc_uf,
		f_pag=f_pag,
		vpc=vpc,
		vej=vej,
		f_ab=f_ab,
		f_al=f_al,
		f_tet=f_tet,
		abertura_bruta=abertura_bruta,
		alvo_bruto=alvo_bruto,
		teto_bruto=teto_bruto,
		abertura=abertura,
		alvo=alvo,
		teto=teto,
		teto_pct=teto_pct,
	)


def _is_monotonic(values: List[Decimal]) -> bool:
	return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def trace_case_v5(case: CaseInput) -> Dict[str, Any]:
	"""Retorna rastreio detalhado da pipeline para auditoria de fallback e depuracao."""
	if case.ped <= 0:
		raise ValueError("PED deve ser maior que zero")

	uf = _normalize_uf(case.uf)
	sub = _normalize_sub(case.sub)
	qtd_docs = _count_qtd_docs(case)
	matrix_name, matrix = _select_matrix(sub)
	uf_key = uf if uf in matrix else "TOTAL"
	total_row = matrix["TOTAL"]
	uf_row = matrix[uf_key]

	p_raw: List[Decimal] = [Decimal("0") for _ in range(7)]
	for d in range(1, 7):
		p_raw[d] = total_row["D"][d] + W_DOC[d] * (uf_row["D"][d] - total_row["D"][d])

	p1_proxy = p_raw[1]
	gap0 = total_row["D"][1] - total_row["D"][0]
	uf_shift = uf_row["T"] - total_row["T"]
	p0_context = total_row["D"][0] + Decimal("0.15") * uf_shift
	p_raw[0] = _clamp(min(p0_context, p1_proxy - gap0), Decimal("0"), p1_proxy)

	p_corr: List[Decimal] = [Decimal("0") for _ in range(7)]
	p_corr[0] = _clamp(p_raw[0], Decimal("0"), MAX_SUCCESS)
	for d in range(1, 7):
		p_corr[d] = _clamp(max(p_raw[d], p_corr[d - 1]), Decimal("0"), MAX_SUCCESS)

	p_suc = _clamp(p_corr[qtd_docs], MIN_SUCCESS, MAX_SUCCESS)
	p_per = Decimal("1") - p_suc
	desc_uf = DISCOUNT_BY_UF.get(uf, Decimal("0.30"))
	f_pag = Decimal("1") - desc_uf
	vpc = case.ped * f_pag
	vej = vpc * p_per

	f_ab = _clamp(Decimal("0.90") - Decimal("0.05") * Decimal(qtd_docs), Decimal("0.60"), Decimal("0.95"))
	f_al = _clamp(f_ab + Decimal("0.08"), Decimal("0.65"), Decimal("0.97"))
	f_tet = _clamp(f_ab + Decimal("0.15"), Decimal("0.70"), Decimal("0.99"))
	abertura = _round_to_nearest_100(vej * f_ab)
	alvo = _round_to_nearest_100(vej * f_al)
	teto = _round_to_nearest_100(vej * f_tet)
	abertura, alvo, teto = _enforce_offer_invariants(abertura, alvo, teto, vej)
	teto_pct = teto / case.ped

	return _to_jsonable(
		{
			"input": {
				"ped": case.ped,
				"uf": uf,
				"sub": sub,
				"qtd_docs": qtd_docs,
			},
			"fallback": {
				"matriz_escolhida": matrix_name,
				"uf_key": uf_key,
				"uf_sem_historico_proprio": uf_key == "TOTAL" and uf != "TOTAL",
				"desconto_usado": desc_uf,
				"desconto_fallback_30": uf not in DISCOUNT_BY_UF,
			},
			"probabilidade": {
				"p_raw": p_raw,
				"p_corr": p_corr,
				"p_suc": p_suc,
				"p_per": p_per,
				"monotonicidade": _is_monotonic(p_corr),
				"p1_proxy": p1_proxy,
				"gap0": gap0,
				"uf_shift": uf_shift,
				"p0_context": p0_context,
			},
			"economico": {
				"f_pag": f_pag,
				"vpc": vpc,
				"vej": vej,
				"f_ab": f_ab,
				"f_al": f_al,
				"f_tet": f_tet,
				"abertura": abertura,
				"alvo": alvo,
				"teto": teto,
				"teto_pct": teto_pct,
			},
			"decisao": "ACORDO" if teto_pct >= Decimal("0.25") else "DEFESA",
		}
	)
