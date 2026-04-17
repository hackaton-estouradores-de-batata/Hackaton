import { getDashboardMetrics } from "@/lib/api"

export default async function DashboardPage() {
  const metrics = await getDashboardMetrics()

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard — Banco UFMG</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Monitoramento de aderência e efetividade da política de acordos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard
          title="Aderência à política"
          value={`${metrics.adherence_pct.toFixed(1)}%`}
          sub="% advogados seguiram recomendação"
        />
        <MetricCard
          title="Acordos aceitos"
          value={`${metrics.agreement_acceptance_pct.toFixed(1)}%`}
          sub="% dos outcomes com negociação aceita"
        />
        <MetricCard
          title="Disagreement IA"
          value={`${metrics.judge_disagreement_pct.toFixed(1)}%`}
          sub="Taxa de divergência do judge"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard title="Casos" value={String(metrics.total_cases)} sub="Total de casos cadastrados" />
        <MetricCard
          title="Recomendações"
          value={String(metrics.total_recommendations)}
          sub="Total de recomendações geradas"
        />
        <MetricCard
          title="Outcomes"
          value={String(metrics.total_outcomes)}
          sub="Total de desfechos registrados"
        />
      </div>

      <div className="rounded-lg border bg-muted/30 p-6 text-sm text-muted-foreground">
        {metrics.has_enough_data
          ? "Dashboard parcial da Sprint 5 ativo com métricas reais agregadas do backend."
          : "Ainda não há dados suficientes para análises robustas; os cards acima refletem o estado atual do sistema."}
      </div>
    </div>
  )
}

function MetricCard({ title, value, sub }: { title: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border bg-card p-5">
      <p className="text-xs text-muted-foreground font-medium">{title}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{sub}</p>
    </div>
  )
}
