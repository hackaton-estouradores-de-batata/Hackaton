import Link from "next/link"
import { getCase, getRecommendation } from "@/lib/api"
import { CaseViewer } from "@/components/CaseViewer"
import { RecommendationCard } from "@/components/RecommendationCard"
import { OutcomeForm } from "@/components/OutcomeForm"

export const dynamic = "force-dynamic"

interface Props {
  params: Promise<{ id: string }>
}

export default async function CasoPage({ params }: Props) {
  const { id } = await params
  const [caso, rec] = await Promise.all([getCase(id), getRecommendation(id)])

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inbox" className="transition-colors hover:text-foreground">
          ← Inbox
        </Link>
        <span>/</span>
        <span className="font-mono text-xs">{caso.numero_processo ?? id}</span>
      </div>

      <section className="rounded-2xl border bg-background p-6 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Análise do caso</p>
            <h1 className="mt-1 text-2xl font-semibold">Painel do advogado</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Revise os sinais do caso, a recomendação atual e registre a decisão final.
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <CaseViewer caso={caso} />
          <div className="rounded-2xl border bg-background p-5 shadow-sm">
            <p className="mb-2 text-xs font-medium text-muted-foreground">Documentos</p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Autos do processo</li>
              <li>Contrato</li>
              <li>Extrato bancário</li>
              <li>Comprovante de crédito</li>
              <li>Dossiê documental</li>
              <li>Demonstrativo da dívida</li>
            </ul>
            <p className="mt-3 text-xs italic text-muted-foreground">
              A visualização direta dos PDFs entra quando a origem real dos arquivos estiver estável.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <RecommendationCard rec={rec} />
          <OutcomeForm caseId={id} recomendacao={rec.decisao} />
        </div>
      </div>
    </div>
  )
}
