"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { postOutcome } from "@/lib/api"
import type { Decisao, OutcomePayload, ResultadoNegociacao, Sentenca } from "@/lib/types"
import { Save, CheckCircle, Scale, Gavel, Handshake, AlertCircle } from "lucide-react"

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
  icons,
  colorScheme = "primary"
}: {
  options: T[]
  value: T | null
  onChange: (v: T) => void
  labels?: Record<T, string>
  icons?: Record<T, React.ReactNode>
  colorScheme?: "primary" | "emerald" | "blue"
}) {
  const getActiveColors = () => {
    if (colorScheme === "emerald") return "bg-emerald-500 text-white shadow-md shadow-emerald-500/20"
    if (colorScheme === "blue") return "bg-blue-500 text-white shadow-md shadow-blue-500/20"
    return "bg-primary text-primary-foreground shadow-md shadow-primary/20"
  }

  return (
    <div className="flex w-full overflow-hidden rounded-xl bg-muted/40 p-1 border border-border/50">
      {options.map((op) => (
        <button
          key={op}
          type="button"
          onClick={() => onChange(op)}
          className={`relative flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-xs font-semibold transition-all duration-300 ${
            value === op
              ? getActiveColors()
              : "text-muted-foreground hover:bg-background/80 hover:text-foreground"
          }`}
        >
          {icons?.[op] && <span className="mr-0.5">{icons[op]}</span>}
          {labels?.[op] ?? op.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  )
}

function InputField({ label, value, onChange, placeholder, prefix }: any) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{label}</label>
      <div className="relative">
        {prefix && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">{prefix}</div>}
        <input
          type="number"
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full rounded-xl border border-border/50 bg-background/50 px-4 py-2.5 text-sm transition-all placeholder:text-muted-foreground/50 focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-4 focus:ring-primary/10 ${prefix ? 'pl-9' : ''}`}
        />
      </div>
    </div>
  )
}

export function OutcomeForm({ caseId, recomendacao, onSubmitted }: Props) {
  const [decisao, setDecisao] = useState<Decisao | null>(null)
  const [valor, setValor] = useState("")
  const [resultado, setResultado] = useState<ResultadoNegociacao | null>(null)
  const [sentenca, setSentenca] = useState<Sentenca | null>(null)
  const [condenacao, setCondenacao] = useState("")
  const [custos, setCustos] = useState("")
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
      sentenca,
      valor_condenacao: condenacao ? parseFloat(condenacao) : null,
      custos_processuais: custos ? parseFloat(custos) : null,
    }
    await postOutcome(caseId, payload)
    setLoading(false)
    setDone(true)
    onSubmitted?.()
  }

  if (done) {
    return (
      <Card className="border-none bg-transparent shadow-none">
        <CardContent className="flex flex-col items-center justify-center space-y-4 py-12 text-center">
          <div className="rounded-full bg-emerald-500/10 p-4 ring-1 ring-emerald-500/20">
            <CheckCircle className="h-10 w-10 text-emerald-500 animate-in zoom-in duration-500" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-foreground">Decisão Registrada</h3>
            <p className="text-sm text-muted-foreground max-w-[250px] mx-auto">O outcome foi salvo e está retroalimentando o modelo para maior aderência.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-none bg-transparent shadow-none">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold tracking-tight">Qual sua decisão?</CardTitle>
        <CardDescription>O sistema registrará seu outcome para melhorar a IA.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-3">
            <ToggleGroup
              options={["acordo", "defesa"] as Decisao[]}
              value={decisao}
              onChange={(next) => {
                setDecisao(next)
                if (next === "acordo") {
                  setSentenca(null)
                  setCondenacao("")
                  setCustos("")
                  return
                }
                setResultado(null)
                setValor("")
              }}
              labels={{ acordo: "ACORDO", defesa: "DEFESA" }}
              icons={{ acordo: <Handshake className="h-4 w-4" />, defesa: <Scale className="h-4 w-4" /> }}
            />
            {decisao && (
              <div className={`flex items-center gap-2 rounded-xl border p-3 text-sm transition-colors ${seguiu ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400" : "border-yellow-500/20 bg-yellow-500/5 text-yellow-600 dark:text-yellow-400"}`}>
                {seguiu ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                <span className="font-medium">{seguiu ? "Você seguiu a recomendação da IA" : "Você divergiu da recomendação da IA"}</span>
              </div>
            )}
          </div>

          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            {decisao === "acordo" && (
              <div className="space-y-5 rounded-2xl border border-emerald-500/10 bg-emerald-500/5 p-5">
                <InputField 
                  label="Valor proposto" 
                  value={valor} 
                  onChange={(e: any) => setValor(e.target.value)} 
                  placeholder="0,00" 
                  prefix="R$"
                />
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Resultado da negociação</label>
                  <ToggleGroup
                    options={["aceito", "recusado", "em_andamento"] as ResultadoNegociacao[]}
                    value={resultado}
                    onChange={setResultado}
                    labels={{ aceito: "Aceito", recusado: "Recusado", em_andamento: "Andamento" }}
                    colorScheme="emerald"
                  />
                </div>
              </div>
            )}

            {decisao === "defesa" && (
              <div className="space-y-5 rounded-2xl border border-blue-500/10 bg-blue-500/5 p-5">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5"><Gavel className="h-3.5 w-3.5" /> Sentença</label>
                  <ToggleGroup
                    options={["procedente", "improcedente", "parcial"] as Sentenca[]}
                    value={sentenca}
                    onChange={(next) => {
                      setSentenca(next)
                      if (next === "improcedente") {
                        setCondenacao("")
                        setCustos("")
                      }
                    }}
                    labels={{ procedente: "Procedente", improcedente: "Improcedente", parcial: "Parcial" }}
                    colorScheme="blue"
                  />
                </div>
                {sentenca && sentenca !== "improcedente" && (
                  <div className="grid grid-cols-2 gap-4 animate-in fade-in duration-300">
                    <InputField label="Condenação" value={condenacao} onChange={(e: any) => setCondenacao(e.target.value)} placeholder="0,00" prefix="R$" />
                    <InputField label="Custos" value={custos} onChange={(e: any) => setCustos(e.target.value)} placeholder="0,00" prefix="R$" />
                  </div>
                )}
              </div>
            )}
          </div>

          <Button 
            type="submit" 
            disabled={!decisao || loading} 
            className="w-full h-12 rounded-xl text-sm font-semibold tracking-wide transition-all data-[disabled=false]:hover:scale-[1.02] shadow-lg shadow-primary/20"
            data-disabled={!decisao || loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Spinner className="h-4 w-4" /> Salvando...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Save className="h-4 w-4" /> Registrar Decisão Final
              </span>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function Spinner({ className }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  )
}
