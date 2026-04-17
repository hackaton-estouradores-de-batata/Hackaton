// Alinhado com src/api/app/schemas/ e src/api/app/models/

export type CaseStatus = "pending" | "analyzed" | "decided" | "closed"
export type Decisao = "acordo" | "defesa"
export type ResultadoNegociacao = "aceito" | "recusado" | "em_andamento"
export type Sentenca = "procedente" | "improcedente" | "parcial"
export type Vulnerabilidade = "idoso" | "analfabeto" | "baixa_renda" | "nenhuma"

// Espelha CaseRead + campos extras planejados (Sprint 1)
export interface Case {
  id: string
  numero_processo: string | null
  valor_causa: number | null
  autor_nome: string | null
  autor_cpf: string | null
  uf?: string | null
  assunto?: string | null
  sub_assunto?: string | null
  case_text?: string | null
  status: CaseStatus
  data_distribuicao?: string
  alegacoes?: string[]
  pedidos?: string[]
  valor_pedido_danos_morais?: number | null
  red_flags?: string[]
  vulnerabilidade_autor?: Vulnerabilidade | null
  indicio_fraude?: number
  forca_narrativa_autor?: number
  inconsistencias_temporais?: string[]
  subsidios?: Record<string, string | number | boolean | null> | null
  source_folder?: string
  created_at?: string
}

// Espelha RecommendationRead + campos extras planejados (Sprint 3)
export interface Recommendation {
  id: string
  case_id: string
  decisao: Decisao
  valor_sugerido_min: number | null
  valor_sugerido_max: number | null
  justificativa: string | null
  confianca: number
  policy_version: string
  // campos adicionados pelo judge/retrieval (Sprint 3)
  regras_aplicadas?: string[]
  casos_similares_ids?: string[]
  judge_concorda?: boolean
  judge_observacao?: string | null
  created_at?: string
}

// Espelha OutcomeRead para POST
export interface OutcomePayload {
  decisao_advogado: Decisao
  valor_proposto: number | null
  valor_acordado: number | null
  resultado_negociacao: ResultadoNegociacao | null
  sentenca?: Sentenca | null
  valor_condenacao: number | null
  custos_processuais?: number | null
}

export interface DashboardMetrics {
  total_cases: number
  total_recommendations: number
  total_outcomes: number
  adherence_pct: number
  agreement_acceptance_pct: number
  judge_disagreement_pct: number
  has_enough_data: boolean
}
