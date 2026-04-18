import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

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
