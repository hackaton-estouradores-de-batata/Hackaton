import type { Case, Recommendation } from "./types"

export const MOCK_CASES: Case[] = [
  {
    id: "1",
    numero_processo: "0801234-56.2024.8.10.0001",
    valor_causa: 15000,
    autor_nome: "Maria Aparecida Silva",
    autor_cpf: "123.456.789-00",
    status: "pending",
    data_distribuicao: "2024-09-15",
    alegacoes: ["Não reconhece contratação de empréstimo consignado de R$12.000"],
    pedidos: ["Dano moral", "Repetição de indébito"],
    valor_pedido_danos_morais: 10000,
    red_flags: ["assinatura_divergente_dossie"],
    vulnerabilidade_autor: "idoso",
    indicio_fraude: 0.3,
    forca_narrativa_autor: 0.75,
  },
  {
    id: "2",
    numero_processo: "0654321-09.2024.8.04.0001",
    valor_causa: 8500,
    autor_nome: "João Carlos Ferreira",
    autor_cpf: "987.654.321-00",
    status: "analyzed",
    data_distribuicao: "2024-10-02",
    alegacoes: ["Afirma que nunca esteve na agência e não assinou nenhum contrato"],
    pedidos: ["Dano moral", "Repetição de indébito", "Tutela antecipada"],
    valor_pedido_danos_morais: 5000,
    red_flags: [],
    vulnerabilidade_autor: "nenhuma",
    indicio_fraude: 0.1,
    forca_narrativa_autor: 0.45,
  },
]

export const MOCK_RECOMMENDATION: Recommendation = {
  id: "rec-001",
  case_id: "1",
  decisao: "acordo",
  valor_sugerido_min: 2500,
  valor_sugerido_max: 4000,
  justificativa:
    "Com base em 47 casos similares (valor R$12k–R$18k, autor idoso, dossiê contestado), a taxa histórica de vitória do banco é 31%. O custo esperado de defesa (R$5.200) supera o valor sugerido de acordo (R$3.200, percentil 25). A assinatura divergente reduz a robustez dos subsídios. Recomenda-se acordo entre R$2.500 e R$4.000.",
  confianca: 0.82,
  policy_version: "v1",
  regras_aplicadas: [
    "AP-01: subsídios frágeis (assinatura não validada)",
    "CDC: multiplicador 1.10 (autor idoso)",
  ],
  casos_similares_ids: ["caso_12301", "caso_8874", "caso_44210"],
  judge_concorda: false,
  judge_observacao:
    "Indício de fraude (0.3) combinado com vulnerabilidade CDC sugere risco de condenação majorada. Considerar proposta no limite superior da faixa.",
}
