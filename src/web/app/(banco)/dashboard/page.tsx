export default function DashboardPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard — Banco UFMG</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Monitoramento de aderência e efetividade da política de acordos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard title="Aderência à política" value="—" sub="% advogados seguiram recomendação" />
        <MetricCard title="Economia estimada" value="—" sub="Recomendado vs. realizado" />
        <MetricCard title="Disagreement IA" value="—" sub="Taxa de divergência do judge" />
      </div>

      <div className="rounded-lg border bg-muted/30 p-8 text-center text-sm text-muted-foreground">
        Gráficos de aderência, efetividade e qualidade da IA serão implementados no Sprint 5.
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
