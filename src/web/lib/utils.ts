import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

const TECHNICAL_LABEL_OVERRIDES: Record<string, string> = {
  analfabeto: "Analfabeto",
  assinatura_divergente: "Assinatura divergente",
  ausencia_comprovante_credito: "Ausência de comprovante de crédito",
  ausencia_contrato: "Ausência de contrato",
  autor_potencialmente_idoso: "Autor potencialmente idoso",
  baixa_renda: "Baixa renda",
  correspondente: "Correspondente",
  digital: "Digital",
  indicio_fraude_autor: "Indício de fraude do autor",
  nao_exito: "Não êxito",
  nao_exito_parcial: "Não êxito parcial",
  nenhuma: "Nenhuma",
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBRL(value: number | null | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—"
  }

  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  })
}

function normalizeLabelKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
}

function toSentenceCase(value: string): string {
  if (!value) return "—"
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function formatTechnicalLabel(value: string | null | undefined): string {
  if (!value) return "—"

  const override = TECHNICAL_LABEL_OVERRIDES[normalizeLabelKey(value)]
  if (override) return override

  const normalized = value.trim().replace(/[_-]+/g, " ").replace(/\s+/g, " ").toLowerCase()
  return toSentenceCase(normalized)
}

export function formatMatrixLabel(value: string | null | undefined): string {
  if (!value) return "—"

  const match = value.trim().match(/^MATRIZ_(.+?)_(\d+)D$/i)
  if (match) {
    const profile = formatTechnicalLabel(match[1]).toLowerCase()
    const count = Number(match[2])
    return `Matriz ${profile} (${count} documentos)`
  }

  return formatTechnicalLabel(value)
}

export function formatAppliedRuleLabel(value: string | null | undefined): string {
  if (!value) return "—"

  if (value === "V5-MISSING-PED") {
    return "Política V5: pedido base ausente"
  }

  const judgeMatch = value.match(/^JUDGE-\d+:\s*(.+)$/i)
  if (judgeMatch) {
    return `Judge: ${toSentenceCase(judgeMatch[1].trim().toLowerCase())}`
  }

  const matrixMatch = value.match(/^V5-MATRIZ:(.+)$/i)
  if (matrixMatch) {
    return `Política V5: ${formatMatrixLabel(matrixMatch[1])}`
  }

  const subMatch = value.match(/^V5-SUB:(.+)$/i)
  if (subMatch) {
    return `Política V5: subgrupo ${formatTechnicalLabel(subMatch[1]).toLowerCase()}`
  }

  const docsMatch = value.match(/^V5-QTD_DOCS:(\d+)$/i)
  if (docsMatch) {
    const count = Number(docsMatch[1])
    const suffix = count === 1 ? "" : "s"
    return `Política V5: ${count} documento${suffix} válido${suffix}`
  }

  const decisaoMatch = value.match(/^V5-DECISAO:(.+)$/i)
  if (decisaoMatch) {
    return `Política V5: decisão ${formatTechnicalLabel(decisaoMatch[1]).toLowerCase()}`
  }

  return formatTechnicalLabel(value)
}
