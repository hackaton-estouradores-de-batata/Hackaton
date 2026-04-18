"use client"

import { startTransition, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Bot,
  BrainCircuit,
  CheckCircle2,
  CircleDashed,
  Clock3,
  FileSearch,
  LoaderCircle,
  Scale,
  Sparkles,
  TriangleAlert,
} from "lucide-react"

import { getCase } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn, formatBRL } from "@/lib/utils"
import type { Case, CaseProcessingStage, CaseProcessingStatus } from "@/lib/types"

const STATE_LABEL: Record<string, string> = {
  pending: "Pendente",
  queued: "Na fila",
  running: "Em execucao",
  completed: "Concluido",
  failed: "Falha",
}

const KIND_LABEL: Record<string, string> = {
  system: "Sistema",
  llm: "LLM",
  policy: "V5",
}

function isTerminalState(state: string | null | undefined): boolean {
  return state === "completed" || state === "failed"
}

function formatDuration(durationMs: number | null | undefined): string {
  if (typeof durationMs !== "number" || Number.isNaN(durationMs) || durationMs <= 0) {
    return "instante"
  }
  if (durationMs < 1000) return `${durationMs} ms`
  if (durationMs < 60_000) return `${(durationMs / 1000).toFixed(1)} s`
  return `${Math.round(durationMs / 1000 / 60)} min`
}

function stageIcon(stageId: string, state: string) {
  if (state === "failed") return <TriangleAlert className="h-5 w-5" />
  if (state === "completed") return <CheckCircle2 className="h-5 w-5" />
  if (state === "running") return <LoaderCircle className="h-5 w-5 animate-spin" />

  switch (stageId) {
    case "document_intake":
      return <Sparkles className="h-5 w-5" />
    case "document_read":
      return <FileSearch className="h-5 w-5" />
    case "case_structuring":
      return <BrainCircuit className="h-5 w-5" />
    case "policy_decision":
      return <Scale className="h-5 w-5" />
    default:
      return <CircleDashed className="h-5 w-5" />
  }
}

function stageTone(stage: CaseProcessingStage): string {
  if (stage.status === "completed") return "border-emerald-500/20 bg-emerald-500/5"
  if (stage.status === "running") return "border-primary/25 bg-primary/5"
  if (stage.status === "failed") return "border-destructive/30 bg-destructive/10"
  return "border-border/50 bg-background/40"
}

function badgeTone(state: string): "default" | "secondary" | "destructive" | "outline" {
  if (state === "completed") return "default"
  if (state === "failed") return "destructive"
  if (state === "running") return "secondary"
  return "outline"
}

function currentThought(processing: CaseProcessingStatus): string {
  const stage = processing.stages.find((item) => item.id === processing.current_stage)
  return (
    stage?.thought ??
    processing.summary ??
    "Os agentes estao consolidando o caso para liberar a recomendacao."
  )
}

function ResultSnapshot({ processing }: { processing: CaseProcessingStatus }) {
  if (!processing.result) return null

  const decisao = processing.result.decisao?.toUpperCase()
  const confianca = Math.round((processing.result.confianca ?? 0) * 100)

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border border-border/50 bg-background/55 p-4">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">Estrategia</p>
        <p className="mt-2 text-lg font-semibold">{decisao ?? "—"}</p>
      </div>
      <div className="rounded-2xl border border-border/50 bg-background/55 p-4">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">Confianca</p>
        <p className="mt-2 text-lg font-semibold">{confianca}%</p>
      </div>
      <div className="rounded-2xl border border-border/50 bg-background/55 p-4">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">VEJ</p>
        <p className="mt-2 text-lg font-semibold">{formatBRL(processing.result.vej)}</p>
      </div>
      <div className="rounded-2xl border border-border/50 bg-background/55 p-4">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">Alvo tecnico</p>
        <p className="mt-2 text-lg font-semibold">{formatBRL(processing.result.alvo)}</p>
      </div>
    </div>
  )
}

export function CaseProcessingPanel({ initialCase }: { initialCase: Case }) {
  const router = useRouter()
  const [liveCase, setLiveCase] = useState(initialCase)
  const [requestedRefresh, setRequestedRefresh] = useState(
    initialCase.processing_status?.state === "completed",
  )

  const processing = liveCase.processing_status
  const processingState = processing?.state

  useEffect(() => {
    if (!processingState || isTerminalState(processingState)) return

    let active = true
    const intervalId = window.setInterval(async () => {
      try {
        const nextCase = await getCase(liveCase.id)
        if (!active) return
        setLiveCase(nextCase)

        if (
          nextCase.processing_status?.state === "completed" &&
          initialCase.processing_status?.state !== "completed" &&
          !requestedRefresh
        ) {
          setRequestedRefresh(true)
          startTransition(() => {
            router.refresh()
          })
        }
      } catch {
        // Keep the last known state and try again in the next interval.
      }
    }, 1800)

    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [initialCase.processing_status?.state, liveCase.id, processingState, requestedRefresh, router])

  if (!processing) return null

  const stage = processing.stages.find((item) => item.id === processing.current_stage) ?? processing.stages[0]
  const autoRefreshing = !isTerminalState(processing.state)

  return (
    <Card className="overflow-hidden border-primary/20 bg-[radial-gradient(circle_at_top_left,_rgba(199,162,84,0.14),_transparent_32%),linear-gradient(135deg,rgba(12,20,44,0.04),transparent_65%)] shadow-xl shadow-primary/10">
      <CardHeader className="border-b border-border/40 pb-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.28em] text-primary">
              <Bot className="h-3.5 w-3.5" />
              Pipeline dos Agentes
            </p>
            <CardTitle className="text-2xl font-semibold tracking-tight">Status do processamento do caso</CardTitle>
            <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
              {processing.summary ?? "O pipeline registra cada etapa da analise para o advogado acompanhar a evolucao do caso."}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={badgeTone(processing.state)} className="rounded-full px-3 py-1 text-xs uppercase tracking-wider">
              {STATE_LABEL[processing.state] ?? processing.state}
            </Badge>
            {autoRefreshing && (
              <Badge variant="outline" className="rounded-full px-3 py-1 text-xs uppercase tracking-wider">
                Atualizacao automatica
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 px-6 py-6">
        <div className="rounded-3xl border border-border/50 bg-background/55 p-5 shadow-sm">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">Etapa atual</p>
              <p className="mt-1 text-lg font-semibold">{processing.current_label ?? stage?.label ?? "Pipeline"}</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">Progresso</p>
              <p className="mt-1 text-lg font-semibold">{processing.progress_pct}%</p>
            </div>
          </div>
          <Progress value={processing.progress_pct} className="w-full" />
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-primary/15 bg-primary/5 px-4 py-3">
            <div className="mt-0.5 rounded-2xl bg-primary/10 p-2 text-primary">
              {stageIcon(stage?.id ?? "pipeline", processing.state === "failed" ? "failed" : stage?.status ?? "pending")}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold">Pensamento simplificado</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{currentThought(processing)}</p>
            </div>
          </div>
        </div>

        <ResultSnapshot processing={processing} />

        {processing.error_message && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <div className="flex items-start gap-2">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{processing.error_message}</p>
            </div>
          </div>
        )}

        <div className="grid gap-3">
          {processing.stages.map((item) => (
            <div
              key={item.id}
              className={cn(
                "flex flex-col gap-4 rounded-3xl border p-4 transition-colors lg:flex-row lg:items-start lg:justify-between",
                stageTone(item),
              )}
            >
              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl",
                    item.status === "completed" && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
                    item.status === "running" && "bg-primary/10 text-primary",
                    item.status === "failed" && "bg-destructive/10 text-destructive",
                    item.status === "pending" && "bg-muted text-muted-foreground",
                  )}
                >
                  {stageIcon(item.id, item.status)}
                </div>
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-base font-semibold">{item.label}</p>
                    <Badge variant="outline" className="rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider">
                      {item.agent}
                    </Badge>
                    <Badge variant="secondary" className="rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider">
                      {KIND_LABEL[item.kind] ?? item.kind}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                  <p className="text-sm leading-relaxed text-foreground/80">
                    {item.thought ?? "Etapa aguardando execucao."}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-6 text-sm text-muted-foreground lg:flex-col lg:items-end lg:text-right">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em]">Status</p>
                  <p className="mt-1 font-semibold text-foreground">{STATE_LABEL[item.status] ?? item.status}</p>
                </div>
                <div>
                  <p className="flex items-center gap-1 text-[11px] uppercase tracking-[0.22em] lg:justify-end">
                    <Clock3 className="h-3.5 w-3.5" />
                    Duracao
                  </p>
                  <p className="mt-1 font-semibold text-foreground">{formatDuration(item.duration_ms)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
