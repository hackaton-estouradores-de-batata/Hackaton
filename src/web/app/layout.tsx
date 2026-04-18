import Link from "next/link"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "EnterOS — Banco UFMG",
  description: "Política de acordos automatizada para triagem jurídica",
}

function ScalesIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4"
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="min-h-full bg-background text-foreground overflow-x-hidden">
        <div className="min-h-screen flex flex-col">

          {/* ─── Header ──────────────────────────────────────────────────── */}
          <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
            <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-6">

              {/* Brand */}
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/15 text-primary border border-primary/25 transition-colors group-hover:bg-primary/25">
                  <ScalesIcon />
                </div>
                <div className="leading-none">
                  <span className="block text-sm font-bold tracking-tight text-foreground">
                    EnterOS
                  </span>
                  <span className="block text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
                    Banco UFMG · Jurídico
                  </span>
                </div>
              </Link>

              {/* Nav */}
              <nav className="flex items-center gap-1">
                <NavLink href="/inbox">Advogado</NavLink>
                <NavLink href="/dashboard">Dashboard</NavLink>
                <Link
                  href="/casos/novo"
                  className="ml-3 inline-flex h-8 items-center rounded bg-primary px-4 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  Novo caso
                </Link>
              </nav>
            </div>
            {/* Gold accent line */}
            <div className="h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
          </header>

          <main className="flex-1 w-full animate-in fade-in duration-300">
            {children}
          </main>

          {/* ─── Footer ──────────────────────────────────────────────────── */}
          <footer className="border-t border-border/60 bg-background py-5">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <ScalesIcon />
                <span>EnterOS · Banco UFMG · Política V5</span>
              </div>
              <span>Sistema de triagem jurídica automatizada</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex h-8 items-center rounded px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
    >
      {children}
    </Link>
  )
}
