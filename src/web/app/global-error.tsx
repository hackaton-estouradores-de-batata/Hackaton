"use client"

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="pt-BR">
      <body style={{ background: "#0a0e1a", color: "#e2e8f0", fontFamily: "sans-serif", display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", margin: 0 }}>
        <div style={{ textAlign: "center", gap: 16, display: "flex", flexDirection: "column" }}>
          <p style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "#c9973c" }}>Erro inesperado</p>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Algo deu errado</h1>
          <button onClick={reset} style={{ marginTop: 8, padding: "8px 20px", background: "#c9973c", color: "#0a0e1a", border: "none", borderRadius: 4, fontWeight: 700, cursor: "pointer" }}>
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  )
}
