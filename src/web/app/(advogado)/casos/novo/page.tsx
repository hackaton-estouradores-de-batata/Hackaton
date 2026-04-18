import Link from "next/link"
import { NewCaseForm } from "@/components/NewCaseForm"

export const dynamic = "force-dynamic"

export default function NovoCasoPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inbox" className="transition-colors hover:text-foreground">
          ← Inbox
        </Link>
        <span>/</span>
        <span>Novo caso</span>
      </div>

      <section className="rounded-2xl border bg-background p-6 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Ingestão</p>
        <h1 className="mt-1 text-2xl font-semibold">Cadastrar novo caso</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Envie os autos e os subsídios em PDF. O backend extrai número do processo, autor, CPF, valor da causa e contexto jurídico a partir dos documentos.
        </p>
      </section>

      <NewCaseForm />
    </div>
  )
}
