"use client"

import { useState } from "react"
import { AlertTriangle, ChevronDown, ChevronUp, Scale } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import type { Recommendation } from "@/lib/types"

function formatBRL(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false)
  const pct = Math.round(rec.confianca * 100)
  const isAcordo = rec.decisao === "acordo"

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Scale className="h-4 w-4" />
            Recomendação
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant={isAcordo ? "default" : "secondary"}>
              {isAcordo ? "ACORDO" : "DEFESA"}
            </Badge>
            <Badge variant="outline" className="text-xs">{rec.policy_version}</Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {rec.judge_concorda === false && rec.judge_observacao && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Revisão sugerida pelo juiz IA</AlertTitle>
            <AlertDescription>{rec.judge_observacao}</AlertDescription>
          </Alert>
        )}

        {isAcordo && rec.valor_sugerido_min != null && rec.valor_sugerido_max != null && (
          <div className="rounded-lg bg-muted px-4 py-3">
            <p className="text-xs text-muted-foreground mb-1">Faixa sugerida</p>
            <p className="text-2xl font-bold">
              {formatBRL(rec.valor_sugerido_min)}
              <span className="text-muted-foreground font-normal text-base"> – </span>
              {formatBRL(rec.valor_sugerido_max)}
            </p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-muted-foreground">Confiança</p>
            <span className="text-xs font-medium">{pct}%</span>
          </div>
          <Progress value={pct} className="h-2" />
        </div>

        <Separator />

        <div>
          <p className="text-xs text-muted-foreground mb-1">Justificativa</p>
          <p className="text-sm leading-relaxed">
            {rec.justificativa ?? "A justificativa detalhada será exibida quando a integração final do motor estiver disponível."}
          </p>
        </div>

        {rec.regras_aplicadas && rec.regras_aplicadas.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-2">Regras aplicadas</p>
            <ul className="space-y-1">
              {rec.regras_aplicadas.map((r) => (
                <li key={r} className="text-xs bg-muted rounded px-2 py-1">{r}</li>
              ))}
            </ul>
          </div>
        )}

        {rec.casos_similares_ids && rec.casos_similares_ids.length > 0 && (
          <Collapsible open={open} onOpenChange={setOpen}>
            <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {rec.casos_similares_ids.length} casos similares usados como base
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-1">
              {rec.casos_similares_ids.map((id) => (
                <p key={id} className="text-xs font-mono bg-muted rounded px-2 py-1">{id}</p>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  )
}
