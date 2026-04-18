import Link from "next/link"
import { getCase, getCaseDocuments, getRecommendation } from "@/lib/api"
import { CaseViewer } from "@/components/CaseViewer"
import { CaseDocumentsViewer } from "@/components/CaseDocumentsViewer"
import { CaseProcessingPanel } from "@/components/CaseProcessingPanel"
import { RecommendationCard } from "@/components/RecommendationCard"
import { OutcomeForm } from "@/components/OutcomeForm"
import { AlertTriangle, ArrowLeft, ChevronRight, FileWarning, Scale } from "lucide-react"

export const dynamic = "force-dynamic"

interface Props {
  params: Promise<{ id: string }>
}

export default async function CasoPage({ params }: Props) {
  const { id } = await params
  const [caseResult, recommendationResult, documentsResult] = await Promise.allSettled([
    getCase(id),
    getRecommendation(id),
    getCaseDocuments(id),
  ])

  if (caseResult.status !== "fulfilled") {
    throw caseResult.reason
  }

  const caso = caseResult.value
  const rec = recommendationResult.status === "fulfilled" ? recommendationResult.value : null
  const documents = documentsResult.status === "fulfilled" ? documentsResult.value : []
  const processingState = caso.processing_status?.state
  const recommendationError =
    recommendationResult.status === "rejected"
      ? processingState === "queued" || processingState === "running"
        ? "Os agentes ainda estao concluindo a analise. A recomendacao sera liberada quando a politica V5 terminar."
        : processingState === "failed"
          ? "O pipeline encontrou um bloqueio e encaminhou o caso para revisao humana antes de liberar a recomendacao."
          : "A recomendação deste caso não pôde ser carregada agora."
      : null
  const documentsError = documentsResult.status === "rejected" ? "Os documentos deste caso não puderam ser carregados agora." : null
  const headerStatus =
    processingState === "queued" || processingState === "running"
      ? (caso.processing_status?.current_label ?? "Em processamento")
      : caso.status.replace("_", " ")

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
            <p className="mt-1 text-sm font-semibold capitalize text-foreground">{headerStatus}</p>
          </div>
        </div>
      </div>

      <CaseProcessingPanel
        key={[
          caso.id,
          caso.status,
          caso.processing_status?.state ?? "none",
          caso.processing_status?.current_stage ?? "none",
          caso.processing_status?.completed_at ?? "open",
        ].join(":")}
        initialCase={caso}
      />

      {/* Main Grid Workspace */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 relative z-10">
        
        {/* Left Column (Main Info & Documents) */}
        <div className="flex flex-col gap-6 lg:col-span-7 xl:col-span-8">
          <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-sm backdrop-blur-md">
            <CaseViewer caso={caso} />
          </div>
          <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-sm backdrop-blur-md">
            {documentsError && <DocumentsWarning message={documentsError} />}
            <CaseDocumentsViewer documents={documents} />
          </div>
        </div>

        {/* Right Column (AI Recommendation & Outcome) */}
        <div className="flex flex-col gap-6 lg:col-span-5 xl:col-span-4">
          <div className="sticky top-24 space-y-6">
            <div className="rounded-3xl border border-primary/20 bg-primary/5 p-1 shadow-2xl shadow-primary/10 backdrop-blur-md">
              {rec ? <RecommendationCard rec={rec} /> : <RecommendationUnavailable message={recommendationError} />}
            </div>
            <div className="rounded-3xl border border-border/50 bg-background/50 p-1 shadow-lg shadow-black/5 backdrop-blur-md">
              <OutcomeForm
                caseId={id}
                recomendacao={rec?.decisao}
                caseStatus={caso.status}
                processingState={processingState}
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

function RecommendationUnavailable({ message }: { message: string | null }) {
  return (
    <div className="rounded-3xl border border-yellow-500/20 bg-yellow-500/5 p-6 text-sm text-yellow-900 dark:text-yellow-100">
      <div className="flex items-start gap-3">
        <div className="rounded-xl bg-yellow-500/10 p-2 text-yellow-600 dark:text-yellow-300">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-yellow-700 dark:text-yellow-300">
            Recomendação indisponível
          </p>
          <p className="font-medium">
            {message ?? "A recomendação deste caso não está disponível no momento."}
          </p>
          <p className="text-xs text-yellow-700/80 dark:text-yellow-200/80">
            O caso continua acessível para consulta e você ainda pode registrar a decisão final.
          </p>
        </div>
      </div>
    </div>
  )
}

function DocumentsWarning({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 px-4 py-3 text-sm text-yellow-900 dark:text-yellow-100">
      <div className="flex items-start gap-2">
        <FileWarning className="mt-0.5 h-4 w-4 shrink-0 text-yellow-600 dark:text-yellow-300" />
        <p>{message}</p>
      </div>
    </div>
  )
}
