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
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inbox" className="hover:text-foreground transition-colors">← Inbox</Link>
        <span>/</span>
        <span className="font-mono text-xs">{caso.numero_processo ?? id}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <CaseViewer caso={caso} />
          <div className="rounded-lg border bg-muted/30 p-4 text-sm">
            <p className="text-xs text-muted-foreground font-medium mb-2">Documentos</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>📄 Autos do processo</li>
              <li>📄 Contrato</li>
              <li>📄 Extrato bancário</li>
              <li>📄 Comprovante de crédito BACEN</li>
              <li>📄 Dossiê Veritas</li>
              <li>📄 Demonstrativo de evolução da dívida</li>
              <li>📄 Laudo referenciado</li>
            </ul>
            <p className="text-xs text-muted-foreground mt-3 italic">
              Visualizador de PDF disponível após integração com backend (Sprint 4).
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
