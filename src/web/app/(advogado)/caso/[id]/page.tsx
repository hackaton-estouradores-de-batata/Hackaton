import Link from "next/link"
import { getCase, getCaseDocuments, getRecommendation } from "@/lib/api"
import { CaseViewer } from "@/components/CaseViewer"
import { CaseDocumentsViewer } from "@/components/CaseDocumentsViewer"
import { RecommendationCard } from "@/components/RecommendationCard"
import { OutcomeForm } from "@/components/OutcomeForm"
import { ArrowLeft, ChevronRight, Scale } from "lucide-react"

export const dynamic = "force-dynamic"

interface Props {
  params: Promise<{ id: string }>
}

export default async function CasoPage({ params }: Props) {
  const { id } = await params
  const [caso, rec, documents] = await Promise.all([getCase(id), getRecommendation(id), getCaseDocuments(id)])

  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-8 px-6 py-8">
      {/* Breadcrumb & Header */}
      <div className="flex flex-col gap-4 relative z-10">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Link href="/inbox" className="group flex items-center gap-1 transition-colors hover:text-foreground">
            <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1" />
            Inbox
          </Link>
          <ChevronRight className="h-3 w-3" />
          <span className="font-mono">{caso.numero_processo ?? id}</span>
        </div>

        <div className="flex items-start justify-between rounded-3xl border border-border/50 bg-background/50 p-6 shadow-xl shadow-black/5 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary shadow-inner">
              <Scale className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-primary">Análise do caso</p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight">Painel do Advogado</h1>
            </div>
          </div>
          <div className="hidden text-right md:block">
            <p className="text-sm font-medium text-muted-foreground">Status atual</p>
            <p className="mt-1 text-sm font-semibold capitalize text-foreground">{caso.status.replace("_", " ")}</p>
          </div>
        </div>
      </div>

      {/* Main Grid Workspace */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 relative z-10">
        
        {/* Left Column (Main Info & Documents) */}
        <div className="flex flex-col gap-6 lg:col-span-7 xl:col-span-8">
          <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-sm backdrop-blur-md">
            <CaseViewer caso={caso} />
          </div>
          <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-sm backdrop-blur-md">
            <CaseDocumentsViewer documents={documents} />
          </div>
        </div>

        {/* Right Column (AI Recommendation & Outcome) */}
        <div className="flex flex-col gap-6 lg:col-span-5 xl:col-span-4">
          <div className="sticky top-24 space-y-6">
            <div className="rounded-3xl border border-primary/20 bg-primary/5 p-1 shadow-2xl shadow-primary/10 backdrop-blur-md">
              <RecommendationCard rec={rec} />
            </div>
            <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-lg shadow-black/5 backdrop-blur-md">
              <OutcomeForm caseId={id} recomendacao={rec.decisao} />
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
