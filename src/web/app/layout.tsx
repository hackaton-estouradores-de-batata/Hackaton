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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="min-h-full bg-background text-foreground relative overflow-x-hidden selection:bg-primary/30 selection:text-primary">
        <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))] mix-blend-screen pointer-events-none" />
        <div className="min-h-screen flex flex-col relative z-0">
          <header className="sticky top-0 z-50 border-b border-border/40 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/40">
            <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(var(--primary),0.2)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                </div>
                <div>
                  <Link href="/" className="text-sm font-semibold tracking-tight text-foreground transition-colors hover:text-primary">
                    EnterOS
                  </Link>
                  <p className="text-[10px] uppercase font-medium tracking-wider text-muted-foreground">Banco UFMG · Jurídico</p>
                </div>
              </div>

              <nav className="flex items-center gap-6 text-sm font-medium">
                <Link href="/inbox" className="text-muted-foreground transition-all hover:text-foreground hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
                  Inbox do advogado
                </Link>
                <Link href="/dashboard" className="text-muted-foreground transition-all hover:text-foreground hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
                  Dashboard banco
                </Link>
              </nav>
            </div>
          </header>

          <main className="flex-1 w-full mx-auto animate-in fade-in duration-500">{children}</main>
        </div>
      </body>
    </html>
  )
}
