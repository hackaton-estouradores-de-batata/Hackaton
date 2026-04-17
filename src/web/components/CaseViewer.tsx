import { AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { STATUS_LABEL, STATUS_VARIANT } from "@/lib/case-status"
import type { Case } from "@/lib/types"

function brl(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export function CaseViewer({ caso }: { caso: Case }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-sm font-mono">{caso.numero_processo ?? "—"}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{caso.autor_nome ?? "—"}</p>
          </div>
          <Badge variant={STATUS_VARIANT[caso.status]}>{STATUS_LABEL[caso.status]}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 text-sm">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-muted-foreground">Valor da causa</p>
            <p className="font-semibold">{caso.valor_causa != null ? brl(caso.valor_causa) : "—"}</p>
          </div>
          {caso.data_distribuicao && (
            <div>
              <p className="text-xs text-muted-foreground">Distribuído em</p>
              <p className="font-semibold">
                {new Date(caso.data_distribuicao).toLocaleDateString("pt-BR")}
              </p>
            </div>
          )}
          {caso.valor_pedido_danos_morais != null && (
            <div>
              <p className="text-xs text-muted-foreground">Pedido danos morais</p>
              <p className="font-semibold">{brl(caso.valor_pedido_danos_morais)}</p>
            </div>
          )}
          {caso.vulnerabilidade_autor && caso.vulnerabilidade_autor !== "nenhuma" && (
            <div>
              <p className="text-xs text-muted-foreground">Vulnerabilidade</p>
              <p className="font-semibold capitalize">{caso.vulnerabilidade_autor}</p>
            </div>
          )}
          {caso.uf && (
            <div>
              <p className="text-xs text-muted-foreground">UF</p>
              <p className="font-semibold">{caso.uf}</p>
            </div>
          )}
          {caso.assunto && (
            <div>
              <p className="text-xs text-muted-foreground">Assunto</p>
              <p className="font-semibold">{caso.assunto}</p>
            </div>
          )}
          {caso.sub_assunto && (
            <div className="col-span-2">
              <p className="text-xs text-muted-foreground">Sub-assunto</p>
              <p className="font-semibold">{caso.sub_assunto}</p>
            </div>
          )}
        </div>

        {caso.alegacoes && caso.alegacoes.length > 0 && (
          <>
            <Separator />
            <div>
              <p className="text-xs text-muted-foreground mb-1">Alegações</p>
              <ul className="space-y-1">
                {caso.alegacoes.map((a) => <li key={a}>• {a}</li>)}
              </ul>
            </div>
          </>
        )}

        {caso.pedidos && caso.pedidos.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Pedidos</p>
            <div className="flex flex-wrap gap-1">
              {caso.pedidos.map((p) => (
                <Badge key={p} variant="outline" className="text-xs">{p}</Badge>
              ))}
            </div>
          </div>
        )}

        {caso.red_flags && caso.red_flags.length > 0 ? (
          <div className="rounded-lg border border-yellow-300 bg-yellow-50 px-3 py-2 dark:border-yellow-800 dark:bg-yellow-950">
            <div className="mb-1 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-yellow-600" />
              <p className="text-xs font-medium text-yellow-700 dark:text-yellow-400">Red flags</p>
            </div>
            {caso.red_flags.map((f) => (
              <p key={f} className="text-xs font-mono text-yellow-700 dark:text-yellow-400">{f}</p>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed bg-muted/30 px-3 py-3 text-xs text-muted-foreground">
            Nenhuma red flag disponível para este caso no modo atual.
          </div>
        )}

        {caso.inconsistencias_temporais && caso.inconsistencias_temporais.length > 0 && (
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Inconsistências temporais</p>
            <ul className="space-y-1">
              {caso.inconsistencias_temporais.map((item) => (
                <li key={item} className="rounded bg-muted px-2 py-1 text-xs">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {caso.subsidios && Object.keys(caso.subsidios).length > 0 && (
          <div>
            <p className="mb-2 text-xs text-muted-foreground">Subsídios estruturados</p>
            <div className="space-y-1">
              {Object.entries(caso.subsidios).map(([key, value]) => (
                <div key={key} className="flex items-start justify-between gap-3 rounded bg-muted px-2 py-1 text-xs">
                  <span className="font-medium">{key}</span>
                  <span className="text-right text-muted-foreground">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
