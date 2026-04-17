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
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-muted/30 text-foreground">
        <div className="min-h-screen flex flex-col">
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
            <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6">
              <div>
                <Link href="/" className="text-sm font-semibold tracking-tight">
                  EnterOS
                </Link>
                <p className="text-xs text-muted-foreground">Banco UFMG · Política de acordos</p>
              </div>

              <nav className="flex items-center gap-3 text-sm">
                <Link href="/inbox" className="text-muted-foreground transition-colors hover:text-foreground">
                  Inbox do advogado
                </Link>
                <Link href="/dashboard" className="text-muted-foreground transition-colors hover:text-foreground">
                  Dashboard banco
                </Link>
              </nav>
            </div>
          </header>

          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  )
}
