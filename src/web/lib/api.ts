import type { Case, Recommendation, OutcomePayload } from "./types"
import { MOCK_CASES, MOCK_RECOMMENDATION } from "./mock"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"
const SERVER_API_BASE_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000"

function resolveUrl(path: string): string {
  if (typeof window !== "undefined") return path
  return `${SERVER_API_BASE_URL}${path}`
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(resolveUrl(path), {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...options,
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
