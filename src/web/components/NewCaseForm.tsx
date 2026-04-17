"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createCase } from "@/lib/api"
import { Button } from "@/components/ui/button"

export function NewCaseForm() {
  const router = useRouter()
  const [numeroProcesso, setNumeroProcesso] = useState("")
  const [valorCausa, setValorCausa] = useState("")
  const [autorNome, setAutorNome] = useState("")
  const [autorCpf, setAutorCpf] = useState("")
  const [autosFiles, setAutosFiles] = useState<File[]>([])
  const [subsidiosFiles, setSubsidiosFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasAnyFile = autosFiles.length > 0 || subsidiosFiles.length > 0

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hasAnyFile) {
      setError("Selecione ao menos um PDF em autos ou subsídios.")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      if (numeroProcesso.trim()) formData.append("numero_processo", numeroProcesso.trim())
      if (valorCausa.trim()) formData.append("valor_causa", valorCausa.trim())
      if (autorNome.trim()) formData.append("autor_nome", autorNome.trim())
      if (autorCpf.trim()) formData.append("autor_cpf", autorCpf.trim())

      autosFiles.forEach((file) => formData.append("autos_files", file))
      subsidiosFiles.forEach((file) => formData.append("subsidios_files", file))

      const created = await createCase(formData)
      setLoading(false)
      router.push(`/caso/${created.id}`)
      router.refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar o caso.")
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <section className="rounded-2xl border bg-background p-6 shadow-sm">
        <div className="mb-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Dados do caso</p>
          <h2 className="mt-1 text-lg font-semibold">Informações básicas</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs text-muted-foreground">Número do processo</label>
            <input
              type="text"
              value={numeroProcesso}
              onChange={(e) => setNumeroProcesso(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="0801234-56.2024.8.10.0001"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Valor da causa</label>
            <input
              type="number"
              value={valorCausa}
              onChange={(e) => setValorCausa(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="15000"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Autor</label>
            <input
              type="text"
              value={autorNome}
              onChange={(e) => setAutorNome(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Maria Aparecida Silva"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">CPF do autor</label>
            <input
              type="text"
              value={autorCpf}
              onChange={(e) => setAutorCpf(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="123.456.789-00"
            />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border bg-background p-6 shadow-sm">
        <div className="mb-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Documentos</p>
          <h2 className="mt-1 text-lg font-semibold">Upload dos PDFs</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs text-muted-foreground">Autos do processo</label>
            <input
              type="file"
              accept="application/pdf"
              multiple
              onChange={(e) => setAutosFiles(Array.from(e.target.files ?? []))}
              className="mt-1 block w-full text-sm"
            />
            <p className="mt-2 text-xs text-muted-foreground">{autosFiles.length} arquivo(s) selecionado(s).</p>
            {autosFiles.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                {autosFiles.map((file) => (
                  <li key={file.name}>{file.name}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Subsídios do banco</label>
            <input
              type="file"
              accept="application/pdf"
              multiple
              onChange={(e) => setSubsidiosFiles(Array.from(e.target.files ?? []))}
              className="mt-1 block w-full text-sm"
            />
            <p className="mt-2 text-xs text-muted-foreground">{subsidiosFiles.length} arquivo(s) selecionado(s).</p>
            {subsidiosFiles.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                {subsidiosFiles.map((file) => (
                  <li key={file.name}>{file.name}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex justify-end">
        <Button type="submit" disabled={loading || !hasAnyFile}>
          {loading ? "Criando caso..." : "Criar caso"}
        </Button>
      </div>
    </form>
  )
}
