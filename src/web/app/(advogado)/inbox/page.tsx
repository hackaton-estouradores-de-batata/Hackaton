import Link from "next/link"
import { getCases } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { STATUS_LABEL, STATUS_VARIANT } from "@/lib/case-status"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export const dynamic = "force-dynamic"

export default async function InboxPage() {
  const cases = await getCases()
  const pendingCount = cases.filter((c) => c.status === "pending").length
  const reviewCount = cases.filter((c) => c.status === "needs_review").length
  const inProgressCount = cases.filter((c) => c.status === "analyzed" || c.status === "decided").length
  const closedCount = cases.filter((c) => c.status === "closed").length

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
      <section className="rounded-2xl border bg-background p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Inbox do advogado
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Caixa de entrada</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {cases.length} processo(s) disponível(is) para análise.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm md:w-[520px] md:grid-cols-4">
            <div className="rounded-xl border bg-muted/40 p-3">
              <p className="text-xs text-muted-foreground">Pendentes</p>
              <p className="mt-1 text-2xl font-semibold">{pendingCount}</p>
            </div>
            <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-3">
              <p className="text-xs text-muted-foreground">Revisão humana</p>
              <p className="mt-1 text-2xl font-semibold text-destructive">{reviewCount}</p>
            </div>
            <div className="rounded-xl border bg-muted/40 p-3">
              <p className="text-xs text-muted-foreground">Em fluxo</p>
              <p className="mt-1 text-2xl font-semibold">{inProgressCount}</p>
            </div>
            <div className="rounded-xl border bg-muted/40 p-3">
              <p className="text-xs text-muted-foreground">Encerrados</p>
              <p className="mt-1 text-2xl font-semibold">{closedCount}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border bg-background p-4 shadow-sm">
        {cases.length === 0 ? (
          <div className="rounded-xl border border-dashed bg-muted/30 px-6 py-12 text-center text-sm text-muted-foreground">
            Nenhum processo disponível no momento.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nº do processo</TableHead>
                <TableHead>Autor</TableHead>
                <TableHead>Contexto</TableHead>
                <TableHead className="text-right">Valor da causa</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
              <TableBody>
              {cases.map((c) => (
                <TableRow key={c.id} className={c.status === "needs_review" ? "bg-destructive/5" : undefined}>
                  <TableCell className="font-mono text-xs">{c.numero_processo ?? "—"}</TableCell>
                  <TableCell>{c.autor_nome ?? "—"}</TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <p className="text-sm">{c.assunto ?? "Assunto não identificado"}</p>
                      <p className="text-xs text-muted-foreground">
                        {[c.uf, c.sub_assunto].filter(Boolean).join(" · ") || "Sem contexto adicional"}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {c.valor_causa != null
                      ? c.valor_causa.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[c.status]}>{STATUS_LABEL[c.status]}</Badge>
                  </TableCell>
                  <TableCell>
                    <Link href={`/caso/${c.id}`} className="text-sm font-medium text-primary hover:underline">
                      Analisar →
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  )
}
