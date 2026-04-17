import Link from "next/link"
import { getCases } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { CaseStatus } from "@/lib/types"

export const dynamic = "force-dynamic"

const STATUS_LABEL: Record<CaseStatus, string> = {
  pending: "Aguardando",
  analyzed: "Analisado",
  decided: "Decidido",
  closed: "Encerrado",
}

const STATUS_VARIANT: Record<CaseStatus, "default" | "secondary" | "outline"> = {
  pending: "secondary",
  analyzed: "default",
  decided: "outline",
  closed: "outline",
}

export default async function InboxPage() {
  const cases = await getCases()

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Caixa de entrada</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {cases.length} processo(s) atribuído(s)
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nº do processo</TableHead>
            <TableHead>Autor</TableHead>
            <TableHead className="text-right">Valor da causa</TableHead>
            <TableHead>Status</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {cases.map((c) => (
            <TableRow key={c.id}>
              <TableCell className="font-mono text-xs">{c.numero_processo ?? "—"}</TableCell>
              <TableCell>{c.autor_nome ?? "—"}</TableCell>
              <TableCell className="text-right">
                {c.valor_causa != null
                  ? c.valor_causa.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                  : "—"}
              </TableCell>
              <TableCell>
                <Badge variant={STATUS_VARIANT[c.status]}>{STATUS_LABEL[c.status]}</Badge>
              </TableCell>
              <TableCell>
                <Link href={`/caso/${c.id}`} className="text-sm text-primary hover:underline font-medium">
                  Analisar →
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
