import type { Case, Recommendation, OutcomePayload, DashboardMetrics, CaseDocument, CaseIngestResponse } from "./types"
import { MOCK_CASES, MOCK_CASE_DOCUMENTS, MOCK_RECOMMENDATION } from "./mock"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"
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

export async function getCases(): Promise<Case[]> {
  if (USE_MOCK) return MOCK_CASES
  return request<Case[]>("/api/cases")
}

export async function getCase(id: string): Promise<Case> {
  if (USE_MOCK) return MOCK_CASES.find((c) => c.id === id) ?? MOCK_CASES[0]
  return request<Case>(`/api/cases/${id}`)
}

export async function getRecommendation(id: string): Promise<Recommendation> {
  if (USE_MOCK) return { ...MOCK_RECOMMENDATION, case_id: id }
  return request<Recommendation>(`/api/cases/${id}/recommendation`)
}

export async function postOutcome(id: string, data: OutcomePayload): Promise<{ ok: boolean }> {
  if (USE_MOCK) return { ok: true }
  return request(`/api/cases/${id}/outcome`, { method: "POST", body: JSON.stringify(data) })
}

export async function getCaseDocuments(id: string): Promise<CaseDocument[]> {
  if (USE_MOCK) return MOCK_CASE_DOCUMENTS.map((doc) => ({ ...doc, name: `${id}-${doc.name}` }))
  return request<CaseDocument[]>(`/api/cases/${id}/documents`)
}

export async function createCase(formData: FormData): Promise<CaseIngestResponse> {
  if (USE_MOCK) {
    return {
      id: "mock-created-case",
      status: "analyzed",
      source_folder: "/mock/case-created",
      autos_count: formData.getAll("autos_files").length,
      subsidios_count: formData.getAll("subsidios_files").length,
      uf: "MG",
      assunto: "Empréstimo consignado",
      sub_assunto: "Não reconhecimento da contratação",
    }
  }
  return request<CaseIngestResponse>("/api/cases", { method: "POST", body: formData })
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  if (USE_MOCK) {
    return {
      total_cases: MOCK_CASES.length,
      total_recommendations: MOCK_CASES.length,
      total_outcomes: 1,
      adherence_pct: 100,
      agreement_acceptance_pct: 100,
      judge_disagreement_pct: 0,
      has_enough_data: true,
    }
  }

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
