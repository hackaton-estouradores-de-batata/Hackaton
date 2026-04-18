import type { Case, Recommendation, OutcomePayload, DashboardMetrics, CaseDocument, CaseIngestResponse } from "./types"

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

function normalizeCase(casePayload: Case): Case {
  return {
    ...casePayload,
    valor_causa: toNumberOrNull(casePayload.valor_causa as unknown),
    valor_pedido_danos_morais: toNumberOrNull(casePayload.valor_pedido_danos_morais as unknown),
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
  return request<CaseIngestResponse>("/api/cases", { method: "POST", body: formData })
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
