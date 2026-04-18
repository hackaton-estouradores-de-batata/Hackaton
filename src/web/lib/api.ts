import type {
  Case,
  Recommendation,
  OutcomePayload,
  DashboardMetrics,
  DashboardAnalytics,
  CaseDocument,
  CaseIngestResponse,
  CaseProcessingResult,
  CaseProcessingStage,
  CaseProcessingStatus,
} from "./types"

const SERVER_API_BASE_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000"

function resolveUrl(path: string): string {
  if (typeof window !== "undefined") return path
  return `${SERVER_API_BASE_URL}${path}`
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers)
  if (!headers.has("Content-Type") && !(options?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  const res = await fetch(resolveUrl(path), {
    cache: "no-store",
    ...options,
    headers,
  })
  if (!res.ok) throw new Error(`API ${res.status} — ${path}`)
  return res.json()
}

function toNumberOrNull(value: unknown): number | null {
  if (value == null || value === "") return null
  if (typeof value === "number") return Number.isFinite(value) ? value : null
  if (typeof value === "string") {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function normalizeProcessingStage(stage: CaseProcessingStage): CaseProcessingStage {
  return {
    ...stage,
    thought: typeof stage.thought === "string" ? stage.thought : null,
    started_at: typeof stage.started_at === "string" ? stage.started_at : null,
    completed_at: typeof stage.completed_at === "string" ? stage.completed_at : null,
    duration_ms: toNumberOrNull(stage.duration_ms as unknown),
    meta: stage.meta && typeof stage.meta === "object" && !Array.isArray(stage.meta) ? stage.meta : {},
  }
}

function normalizeProcessingResult(result: CaseProcessingResult): CaseProcessingResult {
  return {
    ...result,
    confianca: toNumberOrNull(result.confianca as unknown),
    vej: toNumberOrNull(result.vej as unknown),
    alvo: toNumberOrNull(result.alvo as unknown),
    teto: toNumberOrNull(result.teto as unknown),
    revisao_humana: typeof result.revisao_humana === "boolean" ? result.revisao_humana : null,
  }
}

function normalizeProcessingStatus(processingStatus: CaseProcessingStatus | null | undefined): CaseProcessingStatus | null {
  if (!processingStatus) return null

  return {
    ...processingStatus,
    progress_pct: toNumberOrNull(processingStatus.progress_pct as unknown) ?? 0,
    current_stage: typeof processingStatus.current_stage === "string" ? processingStatus.current_stage : null,
    current_label: typeof processingStatus.current_label === "string" ? processingStatus.current_label : null,
    summary: typeof processingStatus.summary === "string" ? processingStatus.summary : null,
    error_message: typeof processingStatus.error_message === "string" ? processingStatus.error_message : null,
    started_at: typeof processingStatus.started_at === "string" ? processingStatus.started_at : null,
    completed_at: typeof processingStatus.completed_at === "string" ? processingStatus.completed_at : null,
    stages: Array.isArray(processingStatus.stages) ? processingStatus.stages.map(normalizeProcessingStage) : [],
    result:
      processingStatus.result && typeof processingStatus.result === "object"
        ? normalizeProcessingResult(processingStatus.result)
        : null,
  }
}

function normalizeCase(casePayload: Case): Case {
  return {
    ...casePayload,
    valor_causa: toNumberOrNull(casePayload.valor_causa as unknown),
    valor_pedido_danos_morais: toNumberOrNull(casePayload.valor_pedido_danos_morais as unknown),
    processing_status: normalizeProcessingStatus(casePayload.processing_status),
  }
}

function normalizeRecommendation(recommendationPayload: Recommendation): Recommendation {
  const trace = recommendationPayload.policy_trace
  return {
    ...recommendationPayload,
    valor_sugerido_min: toNumberOrNull(recommendationPayload.valor_sugerido_min as unknown),
    valor_sugerido_max: toNumberOrNull(recommendationPayload.valor_sugerido_max as unknown),
    policy_trace: trace
      ? {
          ...trace,
          qtd_docs: Number(trace.qtd_docs ?? 0),
          p_suc: Number(trace.p_suc ?? 0),
          p_per: Number(trace.p_per ?? 0),
          vej: Number(trace.vej ?? 0),
          abertura: Number(trace.abertura ?? 0),
          alvo: Number(trace.alvo ?? 0),
          teto: Number(trace.teto ?? 0),
          teto_pct: Number(trace.teto_pct ?? 0),
          documentos_presentes: Array.isArray(trace.documentos_presentes) ? trace.documentos_presentes : [],
          revisao_humana: Boolean(trace.revisao_humana),
          uf_sem_historico_proprio: Boolean(trace.uf_sem_historico_proprio),
        }
      : null,
  }
}

export async function getCases(): Promise<Case[]> {
  return (await request<Case[]>("/api/cases")).map(normalizeCase)
}

export async function getCase(id: string): Promise<Case> {
  return normalizeCase(await request<Case>(`/api/cases/${id}`))
}

export async function getRecommendation(id: string): Promise<Recommendation> {
  return normalizeRecommendation(await request<Recommendation>(`/api/cases/${id}/recommendation`))
}

export async function postOutcome(id: string, data: OutcomePayload): Promise<{ ok: boolean }> {
  return request(`/api/cases/${id}/outcome`, { method: "POST", body: JSON.stringify(data) })
}

export async function getCaseDocuments(id: string): Promise<CaseDocument[]> {
  return request<CaseDocument[]>(`/api/cases/${id}/documents`)
}

export async function createCase(formData: FormData): Promise<CaseIngestResponse> {
  const payload = await request<CaseIngestResponse>("/api/cases", { method: "POST", body: formData })
  return {
    ...payload,
    processing_status: normalizeProcessingStatus(payload.processing_status),
  }
}

export async function getDashboardAnalytics(uf?: string, subAssunto?: string): Promise<DashboardAnalytics> {
  const params = new URLSearchParams()
  if (uf) params.set("uf", uf)
  if (subAssunto) params.set("sub_assunto", subAssunto)
  const qs = params.toString()
  try {
    return await request<DashboardAnalytics>(`/api/dashboard/analytics${qs ? `?${qs}` : ""}`)
  } catch {
    return {
      pareto: [],
      valor_pedido_vs_pago: { total_pedido: 0, total_pago: 0, percentual_pago: 0, count: 0 },
      kpi_economia_nao_exito_defesa: 0,
      resultado_macro: { exito_pct: 0, nao_exito_pct: 0, total: 0 },
      resultado_micro: [],
      matrix: [],
      ufs_disponiveis: [],
      sub_assuntos_disponiveis: [],
    }
  }
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  try {
    return await request<DashboardMetrics>("/api/dashboard/metrics")
  } catch {
    return {
      total_cases: 0,
      total_recommendations: 0,
      total_outcomes: 0,
      adherence_pct: 0,
      agreement_acceptance_pct: 0,
      judge_disagreement_pct: 0,
      has_enough_data: false,
    }
  }
}
