import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Slides · Hackathon UFMG 2026",
  description: "Apresentação do projeto de política de acordos assistida por IA.",
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
