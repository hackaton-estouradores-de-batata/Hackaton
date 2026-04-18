"use client"

import { AlertTriangle, Bot, BrainCircuit, CheckCircle2, FileStack } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { formatAppliedRuleLabel, formatBRL, formatMatrixLabel, formatTechnicalLabel } from "@/lib/utils"
import type { Recommendation } from "@/lib/types"

const DOCUMENT_LABELS: Record<string, string> = {
  contrato: "Contrato",
  comprovante_credito: "Comprovante",
  extrato: "Extrato",
  demonstrativo_evolucao_divida: "Demonstrativo",
  dossie: "Dossie",
  laudo_referenciado: "Laudo",
}

function formatDocumentLabel(value: string): string {
  return DOCUMENT_LABELS[value] ?? formatTechnicalLabel(value)
}

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const pct = Math.round(rec.confianca * 100)
  const isAcordo = rec.decisao === "acordo"
  const trace = rec.policy_trace

  return (
    <Card className="border-none bg-transparent shadow-none">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${isAcordo ? "bg-emerald-500/10 text-emerald-500 ring-1 ring-emerald-500/20" : "bg-blue-500/10 text-blue-500 ring-1 ring-blue-500/20"}`}>
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
                Decisao da IA
              </CardTitle>
              <div className="mt-1 flex items-center gap-2">
                <span className={`text-2xl font-bold tracking-tight ${isAcordo ? "text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]" : "text-blue-500 drop-shadow-[0_0_8px_rgba(59,130,246,0.4)]"}`}>
                  {isAcordo ? "ACORDO" : "DEFESA"}
                </span>
              </div>
            </div>
          </div>
          <Badge variant="outline" className="text-[10px] uppercase font-mono tracking-wider bg-background/50">
            {rec.policy_version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {rec.judge_concorda === false && rec.judge_observacao && (
          <Alert variant="destructive" className="border-destructive/30 bg-destructive/10 text-destructive shadow-sm">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle className="font-semibold tracking-tight">Revisao Sugerida</AlertTitle>
            <AlertDescription className="text-xs leading-relaxed mt-1 opacity-90">{rec.judge_observacao}</AlertDescription>
          </Alert>
        )}

        {isAcordo && rec.valor_sugerido_min != null && rec.valor_sugerido_max != null && (
          <div className="relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 px-5 py-4">
            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-emerald-500/10 blur-2xl" />
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-500/80 mb-1">Faixa de Acordo Sugerida</p>
            <p className="text-3xl font-light tracking-tighter text-emerald-600 dark:text-emerald-400">
              {formatBRL(rec.valor_sugerido_min)}
              <span className="text-emerald-500/40 font-normal mx-2">a</span>
              {formatBRL(rec.valor_sugerido_max)}
            </p>
          </div>
        )}

        <div className="rounded-2xl border border-border/40 bg-background/40 p-4">
          <div className="flex items-end justify-between mb-2">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Nivel de Confianca
            </p>
            <span className="text-xl font-bold tracking-tight">{pct}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${isAcordo ? "bg-emerald-500" : "bg-blue-500"}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {trace && (
          <div className="rounded-2xl border border-border/40 bg-background/35 p-4 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold flex items-center gap-2">
                <FileStack className="h-4 w-4 text-primary" />
                Trace V5
              </p>
              <Badge variant="secondary" className="text-[10px] tracking-wide bg-primary/10 text-primary">
                {formatMatrixLabel(trace.matriz_escolhida)}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl border border-border/40 bg-background/50 p-3">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Docs validos</p>
                <p className="mt-1 text-lg font-semibold">{trace.qtd_docs}/6</p>
              </div>
              <div className="rounded-xl border border-border/40 bg-background/50 p-3">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">VEJ</p>
                <p className="mt-1 text-lg font-semibold">{formatBRL(trace.vej)}</p>
              </div>
              <div className="rounded-xl border border-border/40 bg-background/50 p-3">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Exito defensivo</p>
                <p className="mt-1 text-lg font-semibold">{Math.round(trace.p_suc * 100)}%</p>
              </div>
              <div className="rounded-xl border border-border/40 bg-background/50 p-3">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Subtipo</p>
                <p className="mt-1 text-lg font-semibold">{formatTechnicalLabel(trace.sub_estatistico)}</p>
              </div>
            </div>

            {isAcordo && (
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-sm">
                <p className="text-[11px] uppercase tracking-wider text-emerald-500/80">Alvo e teto</p>
                <p className="mt-1 font-medium">
                  Alvo {formatBRL(trace.alvo)} • Teto {formatBRL(trace.teto)}
                </p>
              </div>
            )}

            {trace.documentos_presentes.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Documentos considerados</p>
                <div className="flex flex-wrap gap-2">
                  {trace.documentos_presentes.map((documento) => (
                    <Badge key={documento} variant="outline" className="bg-background/50 text-xs font-medium border-primary/20 text-foreground">
                      {formatDocumentLabel(documento)}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <Separator className="opacity-50" />

        <div className="space-y-3">
          <p className="text-sm font-semibold flex items-center gap-2">
            <Bot className="h-4 w-4 text-primary" />
            Justificativa Tecnica
          </p>
          <div className="rounded-xl bg-muted/40 p-4 text-sm leading-relaxed text-muted-foreground shadow-inner border border-border/30">
            {rec.justificativa ?? "A justificativa detalhada sera exibida quando o motor estiver disponivel."}
          </div>
        </div>

        {rec.regras_aplicadas && rec.regras_aplicadas.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Regras Aplicadas</p>
            <div className="flex flex-wrap gap-2">
              {rec.regras_aplicadas.map((r) => (
                <Badge key={r} variant="outline" className="bg-background/50 text-xs font-medium border-primary/20 text-foreground">
                  {formatAppliedRuleLabel(r)}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
