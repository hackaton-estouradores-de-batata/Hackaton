"use client"

import { useEffect, useState } from "react"
import { getDashboardMetrics, getDashboardAnalytics } from "@/lib/api"
import type {
  DashboardMetrics,
  DashboardAnalytics,
  ParetoItem,
  ResultadoMicroItem,
  MatrixCell,
} from "@/lib/types"

// ─── formatters ──────────────────────────────────────────────────────────────
const fmtBRL = (n: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n)
const fmtPct = (n: number) => `${n.toFixed(1)}%`

// ─── SVG helpers ─────────────────────────────────────────────────────────────
function polarToCartesian(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function pieSlicePath(cx: number, cy: number, r: number, start: number, end: number) {
  if (end - start >= 359.9)
    return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
  const s = polarToCartesian(cx, cy, r, start)
  const e = polarToCartesian(cx, cy, r, end)
  const large = end - start > 180 ? 1 : 0
  return `M ${cx} ${cy} L ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y} Z`
}

// Paleta judicial: naval, ouro, verde-floresta, bordô, púrpura
const PIE_COLORS = ["#5b8dee", "#c9973c", "#2d8a58", "#b84040", "#7058c4"]

// ─── small UI atoms ───────────────────────────────────────────────────────────
function MetricCard({ title, value, sub }: { title: string; value: string; sub: string }) {
  return (
    <div className="rounded border border-border bg-card p-5">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{title}</p>
      <p className="mt-2 text-3xl font-bold tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
    </div>
  )
}

function KPICard({
  title,
  value,
  description,
  highlight,
}: {
  title: string
  value: string
  description: string
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded border p-5 ${
        highlight
          ? "border-primary/40 bg-primary/8"
          : "border-border bg-card"
      }`}
    >
      <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{title}</p>
      <p className={`mt-2 text-4xl font-bold tracking-tight ${highlight ? "text-primary" : ""}`}>{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="h-px flex-1 bg-border/60" />
      <h2 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground whitespace-nowrap">
        {children}
      </h2>
      <div className="h-px flex-1 bg-border/60" />
    </div>
  )
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-32 rounded border border-dashed border-border text-muted-foreground text-sm">
      {label}
    </div>
  )
}

// ─── Pareto Chart ─────────────────────────────────────────────────────────────
function ParetoChart({ data }: { data: ParetoItem[] }) {
  if (!data.length) return <EmptyState label="Sem dados de Pareto" />

  // Dimensões generosas para que nada seja cortado pelo viewBox
  const W = 760
  const H = 420
  const pad = { top: 30, right: 70, bottom: 150, left: 95 }
  const cW = W - pad.left - pad.right   // 595
  const cH = H - pad.top - pad.bottom   // 240

  const maxVal = Math.max(...data.map((d) => d.total_valor_pedido), 1)
  const total = data.reduce((s, d) => s + d.total_valor_pedido, 0) || 1

  const barW = cW / data.length
  const yTicks = [0, 25, 50, 75, 100]

  // Pré-computar barras e pontos da linha acumulada fora do render
  type BarItem = { x: number; y: number; barH: number; lx: number; ly: number; label: string; px: number; py: number; key: string }
  const bars = data.reduce<{ cum: number; items: BarItem[] }>(
    ({ cum, items }, d, i) => {
      const barH = (d.total_valor_pedido / maxVal) * cH
      const x = pad.left + i * barW
      const newCum = cum + (d.total_valor_pedido / total) * 100
      const px = x + barW / 2
      return {
        cum: newCum,
        items: [
          ...items,
          {
            x,
            y: pad.top + cH - barH,
            barH,
            lx: px,
            ly: pad.top + cH + 10,  // anchor just below baseline
            label: d.sub_assunto.length > 16 ? d.sub_assunto.slice(0, 16) + "…" : d.sub_assunto,
            px,
            py: pad.top + cH - (newCum / 100) * cH,
            key: d.sub_assunto,
          },
        ],
      }
    },
    { cum: 0, items: [] }
  ).items

  const linePoints = bars.map((b) => `${b.px},${b.py}`).join(" ")

  // Posição dos rótulos dos eixos (rotação ao redor do centro da área do gráfico)
  const midY = pad.top + cH / 2

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ display: "block" }}>
      {/* linhas de grade */}
      {yTicks.map((t) => {
        const gy = pad.top + cH - (t / 100) * cH
        return (
          <g key={t}>
            <line
              x1={pad.left} x2={pad.left + cW} y1={gy} y2={gy}
              stroke="#2a3550" strokeWidth={t === 0 ? 1.5 : 1}
              strokeDasharray={t === 0 ? "0" : "4,4"}
            />
            {/* eixo esquerdo: valor */}
            <text x={pad.left - 6} y={gy + 4} textAnchor="end" fontSize={11} fill="#7a8aa8">
              {t === 0 ? "0" : fmtBRL((t / 100) * maxVal)}
            </text>
            {/* eixo direito: percentual */}
            <text x={pad.left + cW + 6} y={gy + 4} textAnchor="start" fontSize={11} fill="#c9973c">
              {t}%
            </text>
          </g>
        )
      })}

      {/* barras */}
      {bars.map((b) => (
        <rect key={b.key} x={b.x + 4} y={b.y} width={barW - 8} height={b.barH} fill="#4a72c4" opacity={0.85} rx={2} />
      ))}

      {/* rótulos do eixo X — rotacionados -45° a partir da baseline */}
      {bars.map((b) => (
        <text
          key={`lbl-${b.key}`}
          x={b.lx}
          y={b.ly}
          textAnchor="end"
          fontSize={11}
          fill="#7a8aa8"
          transform={`rotate(-45 ${b.lx} ${b.ly})`}
        >
          {b.label}
        </text>
      ))}

      {/* linha cumulativa */}
      <polyline points={linePoints} fill="none" stroke="#c9973c" strokeWidth={2.5} strokeLinejoin="round" />
      {bars.map((b) => (
        <circle key={`pt-${b.key}`} cx={b.px} cy={b.py} r={4} fill="#c9973c" stroke="#111827" strokeWidth={1.5} />
      ))}

      {/* eixos */}
      <line x1={pad.left} x2={pad.left} y1={pad.top} y2={pad.top + cH} stroke="#3a4a6a" strokeWidth={1.5} />
      <line x1={pad.left} x2={pad.left + cW} y1={pad.top + cH} y2={pad.top + cH} stroke="#3a4a6a" strokeWidth={1.5} />
      <line x1={pad.left + cW} x2={pad.left + cW} y1={pad.top} y2={pad.top + cH} stroke="#3a4a6a" strokeWidth={1} strokeDasharray="4,4" />

      {/* rótulo eixo Y esquerdo */}
      <text
        x={14} y={midY}
        textAnchor="middle" fontSize={11} fill="#7a8aa8"
        transform={`rotate(-90 14 ${midY})`}
      >
        Valor Pedido (R$)
      </text>

      {/* rótulo eixo Y direito */}
      <text
        x={W - 14} y={midY}
        textAnchor="middle" fontSize={11} fill="#c9973c"
        transform={`rotate(90 ${W - 14} ${midY})`}
      >
        Acumulado (%)
      </text>
    </svg>
  )
}

// ─── Pie Chart ────────────────────────────────────────────────────────────────
function PieChart({ data }: { data: ResultadoMicroItem[] }) {
  if (!data.length) return <EmptyState label="Sem dados de Resultado Micro" />

  const cx = 90
  const cy = 90
  const r = 75

  const slices = data.reduce<{ start: number; items: (ResultadoMicroItem & { path: string; color: string })[] }>(
    ({ start, items }, d, i) => {
      const deg = (d.pct / 100) * 360
      const path = pieSlicePath(cx, cy, r, start, start + deg)
      return { start: start + deg, items: [...items, { ...d, path, color: PIE_COLORS[i % PIE_COLORS.length] }] }
    },
    { start: 0, items: [] }
  ).items

  const LABEL_MAP: Record<string, string> = {
    procedente: "Procedente",
    improcedente: "Improcedente",
    parcial: "Parcial",
  }

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <svg viewBox="0 0 180 180" className="w-44 h-44 shrink-0">
        {slices.map((s) => (
          <path key={s.resultado_micro} d={s.path} fill={s.color} stroke="white" strokeWidth={1} />
        ))}
      </svg>
      <div className="space-y-2">
        {slices.map((s) => (
          <div key={s.resultado_micro} className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-full shrink-0" style={{ background: s.color }} />
            <span className="text-muted-foreground">{LABEL_MAP[s.resultado_micro] ?? s.resultado_micro}</span>
            <span className="font-semibold ml-auto pl-4">
              {s.count} <span className="text-muted-foreground font-normal">({fmtPct(s.pct)})</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Matrix ───────────────────────────────────────────────────────────────────
function SuccessMatrix({ data }: { data: MatrixCell[] }) {
  if (!data.length) return <EmptyState label="Sem dados de matriz (requer outcomes com recomendação V5)" />

  const ufs = [...new Set(data.map((d) => d.uf))].sort()
  const qtdDocs = [...new Set(data.map((d) => d.qtd_docs))].sort((a, b) => a - b)

  function cellValue(qtd: number, uf: string) {
    return data.find((d) => d.qtd_docs === qtd && d.uf === uf)
  }

  function cellStyle(taxa: number): React.CSSProperties {
    if (taxa >= 80) return { background: "#0f3d22", color: "#6ee7a0" }
    if (taxa >= 60) return { background: "#1a3a28", color: "#86efac" }
    if (taxa >= 40) return { background: "#3b2c0a", color: "#fbbf24" }
    if (taxa >= 20) return { background: "#3d1508", color: "#fb923c" }
    return { background: "#3d0e0e", color: "#f87171" }
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border-collapse">
        <thead>
          <tr>
            <th className="border border-border/30 px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-widest text-muted-foreground whitespace-nowrap bg-secondary/40">
              Docs ↓ / UF →
            </th>
            {ufs.map((u) => (
              <th key={u} className="border border-border/30 px-3 py-2.5 text-[10px] font-semibold uppercase tracking-widest text-center text-muted-foreground bg-secondary/40">
                {u}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {qtdDocs.map((qtd) => (
            <tr key={qtd}>
              <td className="border border-border/30 px-3 py-2 font-mono text-[11px] font-semibold text-center text-muted-foreground bg-secondary/20">{qtd}d</td>
              {ufs.map((u) => {
                const cell = cellValue(qtd, u)
                const cs = cell ? cellStyle(cell.taxa_sucesso) : { background: "#161e2e", color: "#374151" }
                return (
                  <td
                    key={u}
                    className="border border-border/30 px-3 py-2 text-center text-sm"
                    style={cs}
                  >
                    {cell ? (
                      <div>
                        <div className="font-bold">{fmtPct(cell.taxa_sucesso)}</div>
                        <div className="text-[10px] opacity-70">{cell.count}c</div>
                      </div>
                    ) : (
                      <span className="opacity-30">—</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-muted-foreground mt-2">
        Taxa de Sucesso = % de casos com sentença improcedente (êxito do banco). &quot;c&quot; = nº de casos com outcome.
      </p>
    </div>
  )
}

// ─── Filters ──────────────────────────────────────────────────────────────────
function FilterBar({
  ufs,
  subAssuntos,
  uf,
  subAssunto,
  onUf,
  onSubAssunto,
}: {
  ufs: string[]
  subAssuntos: string[]
  uf: string
  subAssunto: string
  onUf: (v: string) => void
  onSubAssunto: (v: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-3 mb-6">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-muted-foreground">UF</label>
        <select
          value={uf}
          onChange={(e) => onUf(e.target.value)}
          className="rounded border border-border bg-secondary px-3 py-1.5 text-sm min-w-[100px] focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">Todas</option>
          {ufs.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-muted-foreground">Sub-assunto</label>
        <select
          value={subAssunto}
          onChange={(e) => onSubAssunto(e.target.value)}
          className="rounded border border-border bg-secondary px-3 py-1.5 text-sm min-w-[200px] focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">Todos</option>
          {subAssuntos.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [uf, setUf] = useState("")
  const [subAssunto, setSubAssunto] = useState("")
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      const [m, a] = await Promise.all([
        getDashboardMetrics(),
        getDashboardAnalytics(uf || undefined, subAssunto || undefined),
      ])
      if (!cancelled) {
        setMetrics(m)
        setAnalytics(a)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [uf, subAssunto])

  const loading = metrics === null

  const macro = analytics?.resultado_macro
  const vp = analytics?.valor_pedido_vs_pago

  return (
    <div className="px-6 py-10 max-w-7xl mx-auto space-y-10">
      {/* header */}
      <div className="border-b border-border/60 pb-6">
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-primary">Dashboard</p>
        <h1 className="text-2xl font-bold tracking-tight">Banco UFMG — Gestão de Processos</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Aderência, efetividade econômica e distribuição de resultados da Política V5
        </p>
      </div>

      {/* operational KPIs */}
      <section>
        <SectionTitle>Métricas Operacionais</SectionTitle>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <MetricCard title="Casos" value={String(metrics?.total_cases ?? "—")} sub="Total cadastrados" />
          <MetricCard
            title="Recomendações"
            value={String(metrics?.total_recommendations ?? "—")}
            sub="Total geradas"
          />
          <MetricCard title="Outcomes" value={String(metrics?.total_outcomes ?? "—")} sub="Total registrados" />
          <MetricCard
            title="Aderência"
            value={metrics ? fmtPct(metrics.adherence_pct) : "—"}
            sub="Seguiram recomendação"
          />
          <MetricCard
            title="Acordos aceitos"
            value={metrics ? fmtPct(metrics.agreement_acceptance_pct) : "—"}
            sub="% outcomes negociados"
          />
          <MetricCard
            title="Disagreement IA"
            value={metrics ? fmtPct(metrics.judge_disagreement_pct) : "—"}
            sub="Divergência do judge"
          />
        </div>
      </section>

      {/* filters */}
      <section>
        <SectionTitle>Segmentação</SectionTitle>
        <FilterBar
          ufs={analytics?.ufs_disponiveis ?? []}
          subAssuntos={analytics?.sub_assuntos_disponiveis ?? []}
          uf={uf}
          subAssunto={subAssunto}
          onUf={setUf}
          onSubAssunto={setSubAssunto}
        />
      </section>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          Carregando análises…
        </div>
      )}

      {/* KPIs analíticos */}
      <section>
        <SectionTitle>KPIs Financeiros</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <KPICard
            title="Economia — Não Êxito com Defesa"
            value={analytics ? fmtPct(analytics.kpi_economia_nao_exito_defesa) : "—"}
            description="% poupado sobre o valor pedido quando banco foi à defesa e perdeu (parcialmente)"
            highlight
          />
          <KPICard
            title="Êxito judicial"
            value={macro ? fmtPct(macro.exito_pct) : "—"}
            description={`Improcedente — banco venceu · ${macro ? Math.round(macro.total * macro.exito_pct / 100) : 0} casos`}
          />
          <KPICard
            title="Não Êxito judicial"
            value={macro ? fmtPct(macro.nao_exito_pct) : "—"}
            description={`Procedente/Parcial — banco perdeu · ${macro ? Math.round(macro.total * macro.nao_exito_pct / 100) : 0} casos`}
          />
        </div>
      </section>

      {/* Valor Pedido vs Pago */}
      <section>
        <SectionTitle>Valor Pedido × Valor Pago</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <KPICard
            title="Total pedido"
            value={vp ? fmtBRL(vp.total_pedido) : "—"}
            description={`${vp?.count ?? 0} casos com valor informado`}
          />
          <KPICard
            title="Total efetivamente pago"
            value={vp ? fmtBRL(vp.total_pago) : "—"}
            description="Soma de acordos + condenações registradas"
          />
          <KPICard
            title="% do pedido pago"
            value={vp ? fmtPct(vp.percentual_pago) : "—"}
            description="Percentual do valor pedido que foi desembolsado"
            highlight={!!vp && vp.percentual_pago < 60}
          />
        </div>
      </section>

      {/* Pareto */}
      <section>
        <SectionTitle>Pareto — Sub-assunto × Valor Pedido</SectionTitle>
        <div className="rounded border border-border bg-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-medium text-muted-foreground">
              Top 10 sub-assuntos por valor total pedido
            </p>
            <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-4 rounded-sm bg-[#4a72c4]" /> Valor pedido
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-0.5 w-4 bg-[#c9973c]" /> Acumulado %
              </span>
            </div>
          </div>
          <ParetoChart data={analytics?.pareto ?? []} />
        </div>
      </section>

      {/* Resultado Macro + Micro */}
      <section>
        <SectionTitle>Distribuição de Resultados</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Resultado Macro */}
          <div className="rounded border border-border bg-card p-5">
            <p className="mb-5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              Resultado Macro
            </p>
            {macro && macro.total > 0 ? (
              <div className="space-y-5">
                <div>
                  <div className="flex items-baseline justify-between mb-1.5">
                    <span className="text-sm font-medium" style={{ color: "#2d8a58" }}>Êxito · Improcedente</span>
                    <span className="text-xl font-bold" style={{ color: "#2d8a58" }}>{fmtPct(macro.exito_pct)}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${macro.exito_pct}%`, background: "#2d8a58" }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline justify-between mb-1.5">
                    <span className="text-sm font-medium" style={{ color: "#b84040" }}>Não Êxito · Proc./Parcial</span>
                    <span className="text-xl font-bold" style={{ color: "#b84040" }}>{fmtPct(macro.nao_exito_pct)}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${macro.nao_exito_pct}%`, background: "#b84040" }}
                    />
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground border-t border-border/60 pt-3">
                  Base: {Math.round(macro.total)} casos com sentença registrada
                </p>
              </div>
            ) : (
              <EmptyState label="Sem sentenças registradas" />
            )}
          </div>

          {/* Resultado Micro */}
          <div className="rounded border border-border bg-card p-5">
            <p className="mb-5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              Resultado Micro
            </p>
            <PieChart data={analytics?.resultado_micro ?? []} />
          </div>
        </div>
      </section>

      {/* Matrix */}
      <section>
        <SectionTitle>Matriz de Sucesso — Qtd. Documentos × UF</SectionTitle>
        <div className="rounded border border-border bg-card p-5">
          <p className="mb-4 text-xs text-muted-foreground">
            Taxa de sucesso (sentença improcedente) por quantidade de documentos e estado.
            <span className="ml-2 inline-flex gap-2">
              <span style={{ color: "#6ee7a0" }}>■ Alto (≥80%)</span>
              <span style={{ color: "#fbbf24" }}>■ Médio</span>
              <span style={{ color: "#f87171" }}>■ Baixo</span>
            </span>
          </p>
          <SuccessMatrix data={analytics?.matrix ?? []} />
        </div>
      </section>
    </div>
  )
}
