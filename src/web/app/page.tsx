import Link from "next/link"

const steps = [
  {
    title: "Triar casos",
    description: "Visualize rapidamente os processos atribuídos ao advogado e priorize a análise.",
  },
  {
    title: "Revisar recomendação",
    description: "Compare a sugestão de acordo ou defesa com justificativa e sinais do caso.",
  },
  {
    title: "Registrar outcome",
    description: "Salve a decisão final do advogado para alimentar aderência e efetividade.",
  },
]

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-10">
      <section className="grid gap-6 rounded-3xl border bg-background p-8 shadow-sm lg:grid-cols-[1.6fr_1fr] lg:p-10">
        <div className="space-y-5">
          <span className="inline-flex rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">
            Sprint 4 · Fluxo do advogado
          </span>
          <div className="space-y-3">
            <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-balance">
              Interface do advogado para analisar casos e registrar decisões.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground">
              O fluxo está preparado para ingestão real de PDFs, consulta da recomendação e registro
              do outcome diretamente contra a API da stack local.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href="/inbox"
              className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
            >
              Abrir inbox
            </Link>
            <Link
              href="/casos/novo"
              className="inline-flex h-11 items-center justify-center rounded-md border px-5 text-sm font-medium transition-colors hover:bg-muted"
            >
              Ingerir caso
            </Link>
          </div>
        </div>

        <div className="rounded-2xl border bg-muted/40 p-5">
          <p className="text-sm font-medium">Fluxo validado para teste local</p>
          <div className="mt-4 space-y-3 text-sm text-muted-foreground">
            <div className="rounded-xl border bg-background p-4">
              <p className="font-medium text-foreground">Entrada por documentos</p>
              <p className="mt-1">Upload de autos e subsídios, persistência dos PDFs e abertura automática do caso.</p>
            </div>
            <div className="rounded-xl border bg-background p-4">
              <p className="font-medium text-foreground">Painel do advogado</p>
              <p className="mt-1">Consulta do caso, recomendação atualizada e formulário de decisão final.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {steps.map((step, index) => (
          <article key={step.title} className="rounded-2xl border bg-background p-6 shadow-sm">
            <p className="text-xs font-medium text-muted-foreground">Etapa 0{index + 1}</p>
            <h2 className="mt-2 text-lg font-semibold">{step.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{step.description}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
