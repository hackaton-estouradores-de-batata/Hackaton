"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { postOutcome } from "@/lib/api"
import type { Decisao, OutcomePayload, ResultadoNegociacao, Sentenca } from "@/lib/types"

interface Props {
  caseId: string
  recomendacao: Decisao
  onSubmitted?: () => void
}

function ToggleGroup<T extends string>({
  options,
  value,
  onChange,
  labels,
}: {
  options: T[]
  value: T | null
  onChange: (v: T) => void
  labels?: Record<T, string>
}) {
  return (
    <div className="flex gap-2">
      {options.map((op) => (
        <button
          key={op}
          type="button"
          onClick={() => onChange(op)}
          className={`flex-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
            value === op
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border hover:bg-muted"
          }`}
        >
          {labels?.[op] ?? op.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  )
}

export function OutcomeForm({ caseId, recomendacao, onSubmitted }: Props) {
  const [decisao, setDecisao] = useState<Decisao | null>(null)
  const [valor, setValor] = useState("")
  const [resultado, setResultado] = useState<ResultadoNegociacao | null>(null)
  const [sentenca, setSentenca] = useState<Sentenca | null>(null)
  const [condenacao, setCondenacao] = useState("")
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const seguiu = decisao === recomendacao

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!decisao) return
    setLoading(true)
    const payload: OutcomePayload = {
      decisao_advogado: decisao,
      valor_proposto: valor ? parseFloat(valor) : null,
      valor_acordado: resultado === "aceito" && valor ? parseFloat(valor) : null,
      resultado_negociacao: resultado,
      valor_condenacao: condenacao ? parseFloat(condenacao) : null,
    }
    await postOutcome(caseId, payload)
    setLoading(false)
    setDone(true)
    onSubmitted?.()
  }

  if (done) {
    return (
      <Card>
        <CardContent className="space-y-2 pt-6 text-center text-sm text-muted-foreground">
          <p>✓ Decisão registrada com sucesso.</p>
          <p className="text-xs">Fluxo validado em modo mock e pronto para integração do backend.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Registrar decisão</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <p className="text-xs text-muted-foreground mb-2">Sua decisão</p>
            <ToggleGroup
              options={["acordo", "defesa"] as Decisao[]}
              value={decisao}
              onChange={setDecisao}
              labels={{ acordo: "ACORDO", defesa: "DEFESA" }}
            />
            {decisao && (
              <p className="text-xs mt-1.5 flex items-center gap-1 text-muted-foreground">
                {seguiu ? "✓ Seguiu a recomendação" : "⚠ Divergiu da recomendação"}
                <Badge variant={seguiu ? "default" : "destructive"} className="text-xs ml-1">
                  {seguiu ? "aderente" : "divergente"}
                </Badge>
              </p>
            )}
          </div>

          {decisao === "acordo" && (
            <>
              <div>
                <label className="text-xs text-muted-foreground">Valor proposto (R$)</label>
                <input
                  type="number"
                  value={valor}
                  onChange={(e) => setValor(e.target.value)}
                  placeholder="0,00"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-2">Resultado da negociação</p>
                <ToggleGroup
                  options={["aceito", "recusado", "em_andamento"] as ResultadoNegociacao[]}
                  value={resultado}
                  onChange={setResultado}
                />
              </div>
            </>
          )}

          {decisao === "defesa" && (
            <>
              <Separator />
              <div>
                <p className="text-xs text-muted-foreground mb-2">Sentença (se houver)</p>
                <ToggleGroup
                  options={["procedente", "improcedente", "parcial"] as Sentenca[]}
                  value={sentenca}
                  onChange={setSentenca}
                />
              </div>
              {sentenca && sentenca !== "improcedente" && (
                <div>
                  <label className="text-xs text-muted-foreground">Valor de condenação (R$)</label>
                  <input
                    type="number"
                    value={condenacao}
                    onChange={(e) => setCondenacao(e.target.value)}
                    placeholder="0,00"
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              )}
            </>
          )}

          <Button type="submit" disabled={!decisao || loading} className="w-full">
            {loading ? "Salvando..." : "Registrar decisão"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
