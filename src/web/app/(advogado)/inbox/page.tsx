import Link from "next/link"
import { getCases } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { STATUS_LABEL, STATUS_VARIANT } from "@/lib/case-status"
import { formatBRL } from "@/lib/utils"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowRight, ExternalLink, Inbox, SearchCode } from "lucide-react"

export const dynamic = "force-dynamic"

export default async function InboxPage() {
  const cases = await getCases()
  const pendingCount = cases.filter((c) => c.status === "pending").length
  const reviewCount = cases.filter((c) => c.status === "needs_review").length
  const inProgressCount = cases.filter((c) => c.status === "analyzed" || c.status === "decided").length
  const closedCount = cases.filter((c) => c.status === "closed").length

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <section className="relative overflow-hidden rounded-3xl border border-border/50 bg-background/50 p-8 shadow-2xl shadow-primary/5 backdrop-blur-xl">
        <div className="absolute top-0 right-0 -m-32 h-64 w-64 rounded-full bg-primary/10 blur-[80px]" />
        
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between relative z-10">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <div className="rounded-lg bg-primary/20 p-2 text-primary ring-1 ring-primary/30">
                <Inbox className="h-4 w-4" />
              </div>
              <p className="text-xs font-semibold uppercase tracking-widest text-primary">
                Inbox do advogado
              </p>
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Caixa de entrada</h1>
            <p className="mt-2 text-sm text-muted-foreground/80 max-w-md">
              Você possui <strong className="text-foreground">{cases.length} processo(s)</strong> disponíveis. Priorize os casos aguardando revisão humana.
            </p>
          </div>

          <div className="flex flex-col items-stretch gap-4 md:items-end">
            <Link
              href="/casos/novo"
              className="group inline-flex h-10 items-center justify-center gap-2 rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90 hover:shadow-[0_0_20px_rgba(var(--primary),0.4)]"
            >
              Novo caso
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <div className="grid grid-cols-2 gap-3 text-sm md:w-[560px] md:grid-cols-4">
              {[
                { label: "Pendentes", count: pendingCount, styling: "bg-background/40 border-border/40 hover:border-primary/30" },
                { label: "Revisão Humana", count: reviewCount, styling: "bg-destructive/5 text-destructive border-destructive/20 hover:border-destructive/40" },
                { label: "Em fluxo", count: inProgressCount, styling: "bg-background/40 border-border/40 hover:border-primary/30" },
                { label: "Encerrados", count: closedCount, styling: "bg-background/40 border-border/40 hover:border-primary/30" },
              ].map((m) => (
                <div key={m.label} className={`rounded-xl border p-4 transition-colors ${m.styling}`}>
                  <p className="text-xs font-medium text-muted-foreground">{m.label}</p>
                  <p className="mt-2 text-3xl font-light tracking-tighter">{m.count}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-border/50 bg-background/50 shadow-xl shadow-black/5 backdrop-blur-xl overflow-hidden">
        {cases.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 px-6 py-24 text-center">
            <div className="rounded-full bg-muted/50 p-4 text-muted-foreground">
              <SearchCode className="h-8 w-8" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Nenhum processo disponível no momento.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow className="hover:bg-transparent border-border/50">
                <TableHead className="py-4 pl-6 text-xs uppercase tracking-wider text-muted-foreground">Nº do processo</TableHead>
                <TableHead className="py-4 text-xs uppercase tracking-wider text-muted-foreground">Autor</TableHead>
                <TableHead className="py-4 text-xs uppercase tracking-wider text-muted-foreground">Contexto</TableHead>
                <TableHead className="py-4 text-right text-xs uppercase tracking-wider text-muted-foreground">Valor da causa</TableHead>
                <TableHead className="py-4 text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                <TableHead className="py-4 pr-6 text-right" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {cases.map((c) => (
                <TableRow 
                  key={c.id} 
                  className={`group transition-colors border-border/30 hover:bg-muted/30 ${
                    c.status === "needs_review" ? "bg-destructive/5 hover:bg-destructive/10" : ""
                  }`}
                >
                  <TableCell className="pl-6 font-mono text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                    {c.numero_processo ?? "—"}
                  </TableCell>
                  <TableCell className="font-medium">
                    {c.autor_nome ?? "—"}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{c.assunto ?? "Assunto não identificado"}</p>
                      <p className="text-xs text-muted-foreground">
                        {[c.uf, c.sub_assunto].filter(Boolean).join(" · ") || "Sem contexto adicional"}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatBRL(c.valor_causa)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[c.status]} className="rounded-full px-3 py-0.5 font-medium shadow-sm">
                      {STATUS_LABEL[c.status]}
                    </Badge>
                  </TableCell>
                  <TableCell className="pr-6 text-right">
                    <Link 
                      href={`/caso/${c.id}`} 
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary/80 transition-colors hover:text-primary"
                    >
                      Analisar
                      <ExternalLink className="h-3.5 w-3.5" />
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
