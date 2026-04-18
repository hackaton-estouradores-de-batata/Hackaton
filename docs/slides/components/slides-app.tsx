"use client"

import { useMemo, useState } from "react"
import type { Slide } from "@/components/slides-data"
import { slides } from "@/components/slides-data"

const statusLabel: Record<NonNullable<Slide["status"]>, string> = {
  entregue: "Entregue",
  misto: "Entregue + visão",
  visao: "Visão / roadmap",
}

export function SlidesApp() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const currentSlide = slides[currentIndex]

  const progressLabel = useMemo(() => {
    return `${String(currentIndex + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`
  }, [currentIndex])

  function goNext() {
    setCurrentIndex((value) => Math.min(value + 1, slides.length - 1))
  }

  function goPrevious() {
    setCurrentIndex((value) => Math.max(value - 1, 0))
  }

  return (
    <div style={stylesRoot}>
      <main style={mainStyle}>
        <div style={topbarStyle}>
          <div>
            <div style={progressStyle}>{progressLabel}</div>
            <div style={topbarTitleStyle}>{currentSlide.eyebrow}</div>
          </div>

          <div style={controlsStyle}>
            <button type="button" onClick={goPrevious} disabled={currentIndex === 0} style={navButtonStyle}>
              Anterior
            </button>
            <button
              type="button"
              onClick={goNext}
              disabled={currentIndex === slides.length - 1}
              style={{ ...navButtonStyle, ...navButtonPrimaryStyle }}
            >
              Próximo
            </button>
          </div>
        </div>

        <section style={slideCardStyle}>
          <div style={headlineRowStyle}>
            <span style={chipStyle}>{currentSlide.eyebrow}</span>
            {currentSlide.status ? <span style={statusChipStyle}>{statusLabel[currentSlide.status]}</span> : null}
          </div>

          <h2 style={titleStyle}>{currentSlide.title}</h2>
          <p style={leadStyle}>{currentSlide.lead}</p>

          <div style={bulletsWrapperStyle}>
            {currentSlide.bullets.map((bullet) => (
              <article key={bullet} style={bulletCardStyle}>
                <span style={bulletMarkerStyle} />
                <p style={bulletTextStyle}>{bullet}</p>
              </article>
            ))}
          </div>

          {currentSlide.footer ? <div style={footerBoxStyle}>{currentSlide.footer}</div> : null}
        </section>
      </main>
    </div>
  )
}

const stylesRoot: React.CSSProperties = {
  minHeight: "100vh",
}

const chipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "6px 10px",
  borderRadius: 999,
  background: "rgba(124, 156, 255, 0.12)",
  border: "1px solid rgba(124, 156, 255, 0.25)",
  color: "var(--primary-strong)",
  fontSize: "0.78rem",
  fontWeight: 700,
}

const mainStyle: React.CSSProperties = {
  width: "100%",
  maxWidth: "1440px",
  margin: "0 auto",
  padding: "28px",
  display: "flex",
  flexDirection: "column",
  gap: 18,
}

const topbarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 18,
}

const progressStyle: React.CSSProperties = {
  fontSize: "0.85rem",
  color: "var(--primary-strong)",
  fontWeight: 700,
}

const topbarTitleStyle: React.CSSProperties = {
  fontSize: "0.95rem",
  color: "var(--muted)",
  marginTop: 4,
}

const controlsStyle: React.CSSProperties = {
  display: "flex",
  gap: 10,
}

const navButtonStyle: React.CSSProperties = {
  borderRadius: 12,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  background: "rgba(15, 23, 42, 0.42)",
  color: "var(--foreground)",
  padding: "10px 14px",
  cursor: "pointer",
}

const navButtonPrimaryStyle: React.CSSProperties = {
  background: "linear-gradient(180deg, rgba(124, 156, 255, 0.28), rgba(124, 156, 255, 0.16))",
  border: "1px solid rgba(124, 156, 255, 0.42)",
}

const slideCardStyle: React.CSSProperties = {
  flex: 1,
  borderRadius: 28,
  border: "1px solid rgba(148, 163, 184, 0.14)",
  background: "linear-gradient(180deg, rgba(11, 18, 32, 0.86), rgba(7, 12, 22, 0.92))",
  boxShadow: "0 24px 60px rgba(2, 6, 16, 0.42)",
  padding: "36px",
  display: "flex",
  flexDirection: "column",
  gap: 22,
  minHeight: "calc(100vh - 110px)",
}

const headlineRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
}

const statusChipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid rgba(84, 210, 177, 0.28)",
  background: "rgba(84, 210, 177, 0.1)",
  color: "var(--accent)",
  fontSize: "0.78rem",
  fontWeight: 700,
}

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "clamp(2.4rem, 5vw, 4.8rem)",
  lineHeight: 1.02,
  maxWidth: "15ch",
}

const leadStyle: React.CSSProperties = {
  margin: 0,
  color: "#d4dceb",
  fontSize: "1.15rem",
  lineHeight: 1.7,
  maxWidth: "72ch",
}

const bulletsWrapperStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: 14,
  marginTop: 8,
}

const bulletCardStyle: React.CSSProperties = {
  display: "flex",
  gap: 12,
  alignItems: "flex-start",
  borderRadius: 18,
  border: "1px solid rgba(148, 163, 184, 0.14)",
  background: "rgba(15, 23, 42, 0.42)",
  padding: "16px 16px",
}

const bulletMarkerStyle: React.CSSProperties = {
  width: 10,
  height: 10,
  borderRadius: 999,
  marginTop: 7,
  background: "linear-gradient(180deg, var(--primary-strong), var(--accent))",
  flexShrink: 0,
}

const bulletTextStyle: React.CSSProperties = {
  margin: 0,
  lineHeight: 1.65,
  color: "#e8edf8",
  fontSize: "1rem",
}

const footerBoxStyle: React.CSSProperties = {
  marginTop: "auto",
  borderRadius: 20,
  border: "1px solid rgba(124, 156, 255, 0.18)",
  background: "rgba(124, 156, 255, 0.08)",
  padding: "16px 18px",
  color: "#eef2ff",
  fontSize: "1rem",
  lineHeight: 1.6,
}
