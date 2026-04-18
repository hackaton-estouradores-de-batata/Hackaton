import type { CaseStatus } from "@/lib/types"

export const STATUS_LABEL: Record<CaseStatus, string> = {
  pending: "Em processamento",
  analyzed: "Analisado",
  needs_review: "Revisão humana",
  decided: "Decidido",
  closed: "Encerrado",
}

export const STATUS_VARIANT: Record<CaseStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "secondary",
  analyzed: "default",
  needs_review: "destructive",
  decided: "outline",
  closed: "outline",
}
