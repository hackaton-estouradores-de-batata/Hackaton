"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { Slide } from "@/components/slides-data"
import { slides } from "@/components/slides-data"

const STATUS_CONFIG = {
  entregue: { label: "Entregue", color: "#54d2b1", bg: "rgba(84, 210, 177, 0.12)", border: "rgba(84, 210, 177, 0.3)" },
  misto: { label: "Entregue + visão", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.1)", border: "rgba(245, 158, 11, 0.28)" },
  visao: { label: "Visão / roadmap", color: "#9ab2ff", bg: "rgba(124, 156, 255, 0.1)", border: "rgba(124, 156, 255, 0.28)" },
} as const

function CoverSlide({ slide }: { slide: Extract<Slide, { type: "cover" }> }) {
  return (
    <section style={coverCardStyle} className="slide-enter">
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 32 }}>
        <div>
          <div style={coverTaglineStyle}>{slide.tagline}</div>
          <h1 style={coverTitleStyle}>{slide.title}</h1>
          <div style={coverSubtitleStyle}>{slide.subtitle}</div>
        </div>

        <div style={coverDividerStyle} />

        <div style={coverMetaStyle}>
          <div style={coverBadgeStyle}>
            <span style={coverBadgeDotStyle} />
            Banco UFMG
          </div>
          <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{slide.team}</div>
        </div>
      </div>

      <div style={coverDecorStyle} aria-hidden="true">
        <div style={coverGlowStyle} />
        <svg width="320" height="320" viewBox="0 0 320 320" fill="none" opacity={0.08}>
          <circle cx="160" cy="160" r="150" stroke="#9ab2ff" strokeWidth="1" />
          <circle cx="160" cy="160" r="110" stroke="#54d2b1" strokeWidth="1" />
          <circle cx="160" cy="160" r="70" stroke="#9ab2ff" strokeWidth="1" />
          <line x1="160" y1="10" x2="160" y2="310" stroke="#9ab2ff" strokeWidth="0.5" />
          <line x1="10" y1="160" x2="310" y2="160" stroke="#9ab2ff" strokeWidth="0.5" />
        </svg>
      </div>
    </section>
  )
}

function DefaultSlide({ slide }: { slide: Extract<Slide, { type?: "default" }> }) {
  const statusConf = slide.status ? STATUS_CONFIG[slide.status] : null
  const cols = slide.bullets.length <= 3 ? 1 : 2

  return (
    <section style={slideCardStyle} className="slide-enter">
      <div style={headlineRowStyle}>
        <span style={chipStyle}>{slide.eyebrow}</span>
        {statusConf && (
          <span style={{ ...statusChipStyle, color: statusConf.color, background: statusConf.bg, borderColor: statusConf.border }}>
            <span style={{ width: 7, height: 7, borderRadius: 999, background: statusConf.color, display: "inline-block", flexShrink: 0 }} />
            {statusConf.label}
          </span>
        )}
      </div>

      <h2 style={titleStyle}>{slide.title}</h2>
      <p style={leadStyle}>{slide.lead}</p>

      <div style={{ ...bulletsWrapperStyle, gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
        {slide.bullets.map((bullet, i) => (
          <article key={i} style={bulletCardStyle}>
            <span style={bulletIndexStyle}>{String(i + 1).padStart(2, "0")}</span>
            <p style={bulletTextStyle}>{bullet}</p>
          </article>
        ))}
      </div>

      {slide.footer && <div style={footerBoxStyle}>{slide.footer}</div>}
    </section>
  )
}

export function SlidesApp() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [animKey, setAnimKey] = useState(0)
  const mainRef = useRef<HTMLDivElement>(null)
  const total = slides.length

  const goNext = useCallback(() => {
    setCurrentIndex((v) => {
      if (v >= total - 1) return v
      setAnimKey((k) => k + 1)
      return v + 1
    })
  }, [total])

  const goPrev = useCallback(() => {
    setCurrentIndex((v) => {
      if (v <= 0) return v
      setAnimKey((k) => k + 1)
      return v - 1
    })
  }, [])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " ") {
        e.preventDefault()
        goNext()
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault()
        goPrev()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [goNext, goPrev])

  const current = slides[currentIndex]
  const progressPct = ((currentIndex + 1) / total) * 100

  return (
    <div style={rootStyle} ref={mainRef}>
      {/* Progress bar */}
      <div style={progressBarTrackStyle}>
        <div style={{ ...progressBarFillStyle, width: `${progressPct}%` }} />
      </div>

      <main style={mainStyle}>
        {/* Topbar */}
        <div style={topbarStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={logoStyle}>
              <span style={logoDotStyle} />
              EnterOS
            </div>
            <div style={topbarSepStyle} />
            <div>
              <div style={slideCountStyle}>
                {String(currentIndex + 1).padStart(2, "0")}
                <span style={{ color: "var(--muted)", fontWeight: 400 }}> / {String(total).padStart(2, "0")}</span>
              </div>
            </div>
          </div>

          <div style={controlsStyle}>
            <button type="button" onClick={goPrev} disabled={currentIndex === 0} style={navButtonStyle} aria-label="Slide anterior">
              <ArrowLeft /> Anterior
            </button>
            <button
              type="button"
              onClick={goNext}
              disabled={currentIndex === total - 1}
              style={{ ...navButtonStyle, ...navButtonPrimaryStyle }}
              aria-label="Próximo slide"
            >
              Próximo <ArrowRight />
            </button>
          </div>
        </div>

        {/* Slide */}
        <div key={animKey} style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {current.type === "cover" ? (
            <CoverSlide slide={current} />
          ) : (
            <DefaultSlide slide={current as Extract<Slide, { type?: "default" }>} />
          )}
        </div>

        {/* Dot navigation */}
        <nav style={dotsStyle} aria-label="Navegação de slides">
          {slides.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { setCurrentIndex(i); setAnimKey((k) => k + 1) }}
              style={{
                ...dotStyle,
                ...(i === currentIndex ? dotActiveStyle : {}),
              }}
              aria-label={`Slide ${i + 1}`}
            />
          ))}
        </nav>
      </main>
    </div>
  )
}

function ArrowLeft() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ display: "inline-block" }}>
      <path d="M9 2L4 7L9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ArrowRight() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ display: "inline-block" }}>
      <path d="M5 2L10 7L5 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// ── Styles ─────────────────────────────────────────────────────────────────

const rootStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  flexDirection: "column",
}

const progressBarTrackStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  height: 3,
  background: "rgba(148, 163, 184, 0.1)",
  zIndex: 100,
}

const progressBarFillStyle: React.CSSProperties = {
  height: "100%",
  background: "linear-gradient(90deg, var(--primary), var(--accent))",
  transition: "width 0.35s cubic-bezier(0.22, 1, 0.36, 1)",
}

const mainStyle: React.CSSProperties = {
  width: "100%",
  maxWidth: 1440,
  margin: "0 auto",
  padding: "20px 28px 16px",
  display: "flex",
  flexDirection: "column",
  gap: 14,
  flex: 1,
}

const topbarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 18,
}

const logoStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: "0.9rem",
  fontWeight: 700,
  color: "var(--foreground)",
  letterSpacing: "-0.01em",
}

const logoDotStyle: React.CSSProperties = {
  width: 8,
  height: 8,
  borderRadius: 999,
  background: "linear-gradient(135deg, var(--primary), var(--accent))",
  flexShrink: 0,
}

const topbarSepStyle: React.CSSProperties = {
  width: 1,
  height: 20,
  background: "rgba(148, 163, 184, 0.2)",
}

const slideCountStyle: React.CSSProperties = {
  fontSize: "0.85rem",
  fontWeight: 700,
  color: "var(--foreground)",
  fontVariantNumeric: "tabular-nums",
}

const controlsStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
}

const navButtonStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  borderRadius: 10,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  background: "rgba(15, 23, 42, 0.5)",
  color: "var(--foreground)",
  padding: "8px 14px",
  cursor: "pointer",
  fontSize: "0.85rem",
  fontWeight: 600,
  transition: "opacity 0.15s",
}

const navButtonPrimaryStyle: React.CSSProperties = {
  background: "linear-gradient(180deg, rgba(124, 156, 255, 0.22), rgba(124, 156, 255, 0.12))",
  border: "1px solid rgba(124, 156, 255, 0.38)",
  color: "var(--primary-strong)",
}

// Cover

const coverCardStyle: React.CSSProperties = {
  flex: 1,
  borderRadius: 28,
  border: "1px solid rgba(148, 163, 184, 0.14)",
  background: "linear-gradient(140deg, rgba(11, 18, 32, 0.92), rgba(7, 12, 22, 0.96))",
  boxShadow: "0 24px 80px rgba(2, 6, 16, 0.5)",
  padding: "64px 72px",
  display: "flex",
  alignItems: "center",
  gap: 0,
  minHeight: "calc(100vh - 130px)",
  position: "relative",
  overflow: "hidden",
}

const coverTaglineStyle: React.CSSProperties = {
  fontSize: "0.82rem",
  fontWeight: 700,
  color: "var(--accent)",
  textTransform: "uppercase",
  letterSpacing: "0.12em",
  marginBottom: 20,
}

const coverTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "clamp(2.4rem, 5vw, 4.2rem)",
  fontWeight: 800,
  lineHeight: 1.04,
  letterSpacing: "-0.03em",
  background: "linear-gradient(135deg, #fff 30%, var(--primary-strong) 70%, var(--accent) 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
}

const coverSubtitleStyle: React.CSSProperties = {
  marginTop: 16,
  fontSize: "1.35rem",
  fontWeight: 500,
  color: "#c0cce0",
  letterSpacing: "-0.01em",
}

const coverDividerStyle: React.CSSProperties = {
  width: 64,
  height: 3,
  borderRadius: 999,
  background: "linear-gradient(90deg, var(--primary), var(--accent))",
}

const coverMetaStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 20,
}

const coverBadgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 14px",
  borderRadius: 999,
  border: "1px solid rgba(84, 210, 177, 0.28)",
  background: "rgba(84, 210, 177, 0.08)",
  color: "var(--accent)",
  fontSize: "0.85rem",
  fontWeight: 700,
}

const coverBadgeDotStyle: React.CSSProperties = {
  width: 7,
  height: 7,
  borderRadius: 999,
  background: "var(--accent)",
}

const coverDecorStyle: React.CSSProperties = {
  position: "absolute",
  right: 64,
  top: "50%",
  transform: "translateY(-50%)",
  pointerEvents: "none",
}

const coverGlowStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  borderRadius: 999,
  background: "radial-gradient(circle, rgba(124, 156, 255, 0.15), transparent 70%)",
}

// Default slide

const slideCardStyle: React.CSSProperties = {
  flex: 1,
  borderRadius: 28,
  border: "1px solid rgba(148, 163, 184, 0.13)",
  background: "linear-gradient(180deg, rgba(11, 18, 32, 0.88), rgba(7, 12, 22, 0.94))",
  boxShadow: "0 24px 60px rgba(2, 6, 16, 0.42)",
  padding: "40px 44px",
  display: "flex",
  flexDirection: "column",
  gap: 20,
  minHeight: "calc(100vh - 130px)",
}

const headlineRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
}

const chipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "5px 10px",
  borderRadius: 999,
  background: "rgba(124, 156, 255, 0.1)",
  border: "1px solid rgba(124, 156, 255, 0.22)",
  color: "var(--primary-strong)",
  fontSize: "0.78rem",
  fontWeight: 700,
  letterSpacing: "0.02em",
}

const statusChipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 7,
  padding: "5px 10px",
  borderRadius: 999,
  border: "1px solid",
  fontSize: "0.78rem",
  fontWeight: 700,
}

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "clamp(1.75rem, 3.2vw, 3rem)",
  fontWeight: 800,
  lineHeight: 1.1,
  letterSpacing: "-0.025em",
  maxWidth: "22ch",
}

const leadStyle: React.CSSProperties = {
  margin: 0,
  color: "#c8d4e8",
  fontSize: "1.1rem",
  lineHeight: 1.72,
  maxWidth: "74ch",
  fontWeight: 400,
}

const bulletsWrapperStyle: React.CSSProperties = {
  display: "grid",
  gap: 12,
  marginTop: 4,
}

const bulletCardStyle: React.CSSProperties = {
  display: "flex",
  gap: 14,
  alignItems: "flex-start",
  borderRadius: 16,
  border: "1px solid rgba(148, 163, 184, 0.12)",
  background: "rgba(15, 23, 42, 0.45)",
  padding: "14px 18px",
}

const bulletIndexStyle: React.CSSProperties = {
  fontVariantNumeric: "tabular-nums",
  fontSize: "0.72rem",
  fontWeight: 700,
  color: "var(--primary-strong)",
  opacity: 0.7,
  marginTop: 3,
  flexShrink: 0,
  letterSpacing: "0.04em",
}

const bulletTextStyle: React.CSSProperties = {
  margin: 0,
  lineHeight: 1.65,
  color: "#e4eaf6",
  fontSize: "0.97rem",
}

const footerBoxStyle: React.CSSProperties = {
  marginTop: "auto",
  borderRadius: 18,
  border: "1px solid rgba(124, 156, 255, 0.16)",
  background: "rgba(124, 156, 255, 0.06)",
  padding: "14px 18px",
  color: "#dde5f8",
  fontSize: "0.95rem",
  lineHeight: 1.6,
  fontStyle: "italic",
}

const dotsStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "center",
  gap: 6,
  paddingTop: 2,
  paddingBottom: 4,
}

const dotStyle: React.CSSProperties = {
  width: 6,
  height: 6,
  borderRadius: 999,
  border: "none",
  background: "rgba(148, 163, 184, 0.28)",
  cursor: "pointer",
  padding: 0,
  transition: "background 0.2s, width 0.2s",
}

const dotActiveStyle: React.CSSProperties = {
  background: "var(--primary-strong)",
  width: 20,
}
