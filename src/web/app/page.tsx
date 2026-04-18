import Link from "next/link"

// ─── Ícone Balança ───────────────────────────────────────────────────────────
function ScalesIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 3v18" />
      <path d="M8 21h8" />
      <path d="M12 3l-6 3.5" />
      <path d="M12 3l6 3.5" />
      <path d="M6 6.5L3 14h6l-3-7.5z" />
      <path d="M18 6.5L15 14h6l-3-7.5z" />
    </svg>
  )
}

// ─── Dados de apoio ──────────────────────────────────────────────────────────
const stats = [
  { value: "60k+", label: "processos históricos", desc: "base de calibração da Política V5" },
  { value: "V5",   label: "versão ativa",          desc: "motor determinístico por UF e sub-assunto" },
  { value: "<3s",  label: "por recomendação",       desc: "extração, análise e justificativa jurídica" },
]

const features = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    tag: "Advogado",
    title: "Fluxo do Advogado",
    description:
      "Inbox de processos, visualização de PDFs, recomendação com trace V5 e registro do outcome tudo em um painel.",
    cta: "Abrir inbox",
    href: "/inbox",
    primary: true,
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M3 9h18M9 21V9"/>
      </svg>
    ),
    tag: "Banco",
    title: "Dashboard do Banco",
    description:
      "KPIs de aderência, economia na defesa, distribuição de resultados, Pareto por sub-assunto e matriz de sucesso por documentos × UF.",
    cta: "Ver dashboard",
    href: "/dashboard",
    primary: false,
  },
]

const pipeline = [
  {
    step: "01",
    title: "Ingestão",
    description: "Upload de autos e subsídios em PDF. Extração estruturada via LLM com contratos validados.",
  },
  {
    step: "02",
    title: "Análise V5",
    description: "Inventário documental determinístico. Motor de política V5 calibrado por UF e sub-assunto.",
  },
  {
    step: "03",
    title: "Recomendação",
    description: "Decisão accord/defesa com VEJ, faixa de acordo, justificativa jurídica e revisão do judge.",
  },
  {
    step: "04",
    title: "Outcome",
    description: "Advogado registra a decisão final. Dados alimentam aderência, efetividade e backtest.",
  },
]

// ─── Página ──────────────────────────────────────────────────────────────────
export default function Home() {
  return (
    <div className="flex flex-col">

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative isolate overflow-hidden border-b border-border/60 bg-background px-6 py-20 lg:py-28">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 -translate-x-1/2 h-[500px] w-[900px] rounded-full bg-primary/6 blur-[120px]" />
        </div>

        <div className="mx-auto max-w-7xl">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-sm border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <ScalesIcon className="h-3.5 w-3.5" />
            Política V5 · Banco UFMG
          </div>

          {/* Headline */}
          <h1 className="max-w-3xl text-5xl font-bold tracking-tight text-balance lg:text-6xl">
            Gestão Inteligente de{" "}
            <span className="text-primary">Processos Judiciais</span>
          </h1>

          <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground">
            Recomendação automática de acordo ou defesa para contratos de empréstimo —
            calibrada em histórico real, com justificativa jurídica rastreável e
            dashboards de aderência para o banco.
          </p>

          {/* CTAs */}
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Link
              href="/inbox"
              className="inline-flex h-11 items-center gap-2 rounded bg-primary px-6 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              Inbox do Advogado
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
                <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex h-11 items-center gap-2 rounded border border-border px-6 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
            >
              Dashboard do Banco
            </Link>
            <Link
              href="/casos/novo"
              className="inline-flex h-11 items-center gap-2 px-4 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              + Ingerir caso
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats ────────────────────────────────────────────────────────── */}
      <section className="border-b border-border/60 bg-card">
        <div className="mx-auto grid max-w-7xl grid-cols-1 divide-y divide-border/40 px-6 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          {stats.map((s) => (
            <div key={s.value} className="flex flex-col gap-1 py-8 sm:px-8">
              <span className="text-3xl font-bold tracking-tight text-primary">{s.value}</span>
              <span className="text-sm font-semibold text-foreground">{s.label}</span>
              <span className="text-xs text-muted-foreground">{s.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────────── */}
      <section className="border-b border-border/60 bg-background px-6 py-16">
        <div className="mx-auto max-w-7xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">Módulos</p>
          <h2 className="mb-10 text-2xl font-bold">Dois fluxos, um sistema unificado</h2>

          <div className="grid gap-6 lg:grid-cols-2">
            {features.map((f) => (
              <div
                key={f.title}
                className="group flex flex-col rounded border border-border/60 bg-card p-7 transition-colors hover:border-primary/30"
              >
                <div className="mb-5 flex items-start justify-between">
                  <div className="rounded bg-primary/10 p-2.5 text-primary ring-1 ring-primary/20">
                    {f.icon}
                  </div>
                  <span className="rounded-sm bg-secondary px-2.5 py-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    {f.tag}
                  </span>
                </div>
                <h3 className="mb-2 text-lg font-bold">{f.title}</h3>
                <p className="flex-1 text-sm leading-6 text-muted-foreground">{f.description}</p>
                <Link
                  href={f.href}
                  className={`mt-6 inline-flex h-9 w-fit items-center gap-1.5 rounded px-4 text-sm font-semibold transition-opacity hover:opacity-85 ${
                    f.primary
                      ? "bg-primary text-primary-foreground"
                      : "border border-border text-foreground hover:bg-secondary"
                  }`}
                >
                  {f.cta}
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" className="h-3.5 w-3.5">
                    <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pipeline ─────────────────────────────────────────────────────── */}
      <section className="bg-card px-6 py-16">
        <div className="mx-auto max-w-7xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">Pipeline</p>
          <h2 className="mb-10 text-2xl font-bold">Do PDF ao desfecho registrado</h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {pipeline.map((p, i) => (
              <div key={p.step} className="relative flex flex-col gap-3 rounded border border-border/60 bg-background p-5">
                {/* connector arrow */}
                {i < pipeline.length - 1 && (
                  <div className="absolute -right-px top-1/2 z-10 hidden -translate-y-1/2 text-border lg:block">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4 translate-x-2">
                      <path d="M4 8h8M8 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                )}
                <span className="font-mono text-xs font-semibold text-primary">{p.step}</span>
                <h3 className="font-bold">{p.title}</h3>
                <p className="text-sm leading-6 text-muted-foreground">{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA final ────────────────────────────────────────────────────── */}
      <section className="border-t border-border/60 bg-background px-6 py-14">
        <div className="mx-auto max-w-7xl flex flex-col items-center gap-5 text-center">
          <ScalesIcon className="h-8 w-8 text-primary opacity-60" />
          <h2 className="text-xl font-bold">Pronto para analisar um processo?</h2>
          <p className="max-w-md text-sm text-muted-foreground">
            Ingira os documentos, aguarde a extração e obtenha a recomendação com
            justificativa jurídica em segundos.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/casos/novo"
              className="inline-flex h-10 items-center gap-2 rounded bg-primary px-5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              Ingerir primeiro caso
            </Link>
            <Link
              href="/inbox"
              className="inline-flex h-10 items-center gap-2 rounded border border-border px-5 text-sm font-medium transition-colors hover:bg-secondary"
            >
              Ver inbox
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
