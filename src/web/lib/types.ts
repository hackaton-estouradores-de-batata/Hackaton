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
  status: CaseStatus
  // campos adicionados pela extração LLM (Sprint 1)
  data_distribuicao?: string
  alegacoes?: string[]
  pedidos?: string[]
  valor_pedido_danos_morais?: number | null
  red_flags?: string[]
  vulnerabilidade_autor?: Vulnerabilidade | null
  indicio_fraude?: number
  forca_narrativa_autor?: number
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
  valor_condenacao: number | null
}
