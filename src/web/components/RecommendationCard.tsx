"use client"

import { useState } from "react"
import { AlertTriangle, ChevronDown, ChevronUp, BrainCircuit, ShieldAlert, CheckCircle2, Bot } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import { formatBRL } from "@/lib/utils"
import type { Recommendation } from "@/lib/types"

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false)
  const pct = Math.round(rec.confianca * 100)
  const isAcordo = rec.decisao === "acordo"

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
                Decisão da IA
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
          <Alert variant="destructive" className="border-destructive/30 bg-destructive/10 text-destructive shadow-sm animate-pulse">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle className="font-semibold tracking-tight">Revisão Sugerida pelo Juiz IA</AlertTitle>
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
              Nível de Confiança
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

        <Separator className="opacity-50" />

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              Justificativa Técnica
            </p>
            {rec.policy_version.includes("hist") && (
              <Badge variant="secondary" className="text-[10px] uppercase tracking-widest bg-primary/10 text-primary">
                Modo Histórico
              </Badge>
            )}
          </div>
          <div className="rounded-xl bg-muted/40 p-4 text-sm leading-relaxed text-muted-foreground shadow-inner border border-border/30">
            {rec.justificativa ?? "A justificativa detalhada será exibida quando a integração final do motor estiver disponível."}
          </div>
        </div>

        {rec.regras_aplicadas && rec.regras_aplicadas.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Regras Aplicadas</p>
            <div className="flex flex-wrap gap-2">
              {rec.regras_aplicadas.map((r) => (
                <Badge key={r} variant="outline" className="bg-background/50 text-xs font-medium border-primary/20 text-foreground">
                  {r}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {rec.casos_similares_ids && rec.casos_similares_ids.length > 0 && (
          <Collapsible open={open} onOpenChange={setOpen} className="rounded-xl border border-border/40 bg-background/30 p-3 transition-colors hover:bg-background/50">
            <CollapsibleTrigger className="flex w-full items-center justify-between text-xs font-medium text-foreground transition-colors">
              <span className="flex items-center gap-2">
                <ShieldAlert className="h-3.5 w-3.5 text-muted-foreground" />
                Baseado em {rec.casos_similares_ids.length} casos similares
              </span>
              <div className="rounded-full hover:bg-muted/80 p-1">
                {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-3 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                {rec.casos_similares_ids.map((id) => (
                  <div key={id} className="flex items-center gap-2 rounded-lg bg-background p-2 ring-1 ring-border/50">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary/50" />
                    <p className="text-xs font-mono text-muted-foreground">{id}</p>
                  </div>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  )
}
