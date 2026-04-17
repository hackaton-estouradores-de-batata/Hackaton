"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { createCase } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { UploadCloud, FileText, X, Loader2, Gavel } from "lucide-react"

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

  const autosInputRef = useRef<HTMLInputElement>(null)
  const subsidiosInputRef = useRef<HTMLInputElement>(null)

  const hasAnyFile = autosFiles.length > 0 || subsidiosFiles.length > 0

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hasAnyFile) {
      setError("Selecione ao menos um PDF em autos ou subsídios para análise.")
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
      // Small artificially visible delay for smoother transition
      setTimeout(() => {
        setLoading(false)
        router.push(`/caso/${created.id}`)
        router.refresh()
      }, 500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar o caso.")
      setLoading(false)
    }
  }

  const handleRemoveFile = (type: "autos" | "subsidios", index: number) => {
    if (type === "autos") {
      setAutosFiles(prev => prev.filter((_, i) => i !== index))
    } else {
      setSubsidiosFiles(prev => prev.filter((_, i) => i !== index))
    }
  }

  const handleFileChange = (type: "autos" | "subsidios", selectedFiles: FileList | null) => {
    if (!selectedFiles) return
    const newFiles = Array.from(selectedFiles)
    if (type === "autos") setAutosFiles(prev => [...prev, ...newFiles])
    else setSubsidiosFiles(prev => [...prev, ...newFiles])
  }

  return (
    <>
      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-lg transition-all animate-in fade-in duration-300">
          <div className="flex flex-col items-center max-w-sm text-center p-8 rounded-3xl bg-card border border-border/50 shadow-2xl shadow-primary/20">
            <div className="relative mb-6">
              <div className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
              <div className="relative rounded-full bg-primary/10 p-5 ring-1 ring-primary/20">
                <Gavel className="h-10 w-10 text-primary animate-pulse" />
              </div>
            </div>
            <h3 className="text-xl font-bold tracking-tight text-foreground mb-2">Analisando o Processo</h3>
            <p className="text-sm text-muted-foreground mb-6">
              A nossa Inteligência Artificial está lendo os autos e extraindo os subsídios. Isso pode levar alguns instantes.
            </p>
            <div className="flex items-center gap-2 text-primary text-sm font-medium">
              <Loader2 className="h-4 w-4 animate-spin" /> Processando...
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8 pb-12">
        <section className="rounded-3xl border border-border/50 bg-background/50 p-8 shadow-xl shadow-black/5 backdrop-blur-xl transition-all hover:bg-background/80">
          <div className="mb-6 border-b border-border/50 pb-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-primary flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Identificação
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">Dados do caso</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Número do processo</label>
              <input
                type="text"
                value={numeroProcesso}
                onChange={(e) => setNumeroProcesso(e.target.value)}
                className="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-sm transition-all focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-4 focus:ring-primary/10"
                placeholder="0801234-56.2024.8.10.0001"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Valor da causa</label>
              <input
                type="number"
                value={valorCausa}
                onChange={(e) => setValorCausa(e.target.value)}
                className="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-sm transition-all focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-4 focus:ring-primary/10"
                placeholder="15000"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Autor</label>
              <input
                type="text"
                value={autorNome}
                onChange={(e) => setAutorNome(e.target.value)}
                className="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-sm transition-all focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-4 focus:ring-primary/10"
                placeholder="Maria Aparecida Silva"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">CPF do autor</label>
              <input
                type="text"
                value={autorCpf}
                onChange={(e) => setAutorCpf(e.target.value)}
                className="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-sm transition-all focus:border-primary/50 focus:bg-background focus:outline-none focus:ring-4 focus:ring-primary/10"
                placeholder="123.456.789-00"
              />
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-border/50 bg-emerald-500/5 p-8 shadow-xl shadow-black/5 backdrop-blur-xl transition-all">
          <div className="mb-6 border-b border-border/50 pb-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Ingestão de Documentos
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">Upload dos PDFs</h2>
          </div>

          <div className="grid gap-8 lg:grid-cols-2">
            <div className="flex flex-col gap-3">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Autos do processo</label>
              <div 
                onClick={() => autosInputRef.current?.click()}
                className="group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-border/50 bg-background p-8 transition-all hover:border-emerald-500/50 hover:bg-emerald-500/5"
              >
                <div className="rounded-full bg-muted/50 p-3 group-hover:bg-emerald-500/10 group-hover:text-emerald-600 transition-colors">
                  <UploadCloud className="h-6 w-6 text-muted-foreground group-hover:text-emerald-500" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">Clique para selecionar</p>
                  <p className="mt-1 text-xs text-muted-foreground">Arraste múltiplos arquivos PDF</p>
                </div>
                <input
                  ref={autosInputRef}
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={(e) => handleFileChange("autos", e.target.files)}
                  className="hidden"
                />
              </div>

              {autosFiles.length > 0 && (
                <div className="mt-2 flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
                  {autosFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between rounded-xl border border-border/50 bg-background p-3 text-sm shadow-sm animate-in zoom-in-95 duration-200">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <FileText className="h-4 w-4 shrink-0 text-emerald-500" />
                        <span className="truncate font-medium text-muted-foreground">{file.name}</span>
                      </div>
                      <button type="button" onClick={() => handleRemoveFile("autos", index)} className="rounded-full p-1.5 hover:bg-muted text-muted-foreground hover:text-destructive transition-colors">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Subsídios do banco</label>
              <div 
                onClick={() => subsidiosInputRef.current?.click()}
                className="group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-border/50 bg-background p-8 transition-all hover:border-primary/50 hover:bg-primary/5"
              >
                <div className="rounded-full bg-muted/50 p-3 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                  <UploadCloud className="h-6 w-6 text-muted-foreground group-hover:text-primary" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">Clique para selecionar</p>
                  <p className="mt-1 text-xs text-muted-foreground">Arraste múltiplos arquivos PDF</p>
                </div>
                <input
                  ref={subsidiosInputRef}
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={(e) => handleFileChange("subsidios", e.target.files)}
                  className="hidden"
                />
              </div>

              {subsidiosFiles.length > 0 && (
                <div className="mt-2 flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
                  {subsidiosFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between rounded-xl border border-border/50 bg-background p-3 text-sm shadow-sm animate-in zoom-in-95 duration-200">
                      <div className="flex items-center gap-3 overflow-hidden">
                        <FileText className="h-4 w-4 shrink-0 text-primary" />
                        <span className="truncate font-medium text-muted-foreground">{file.name}</span>
                      </div>
                      <button type="button" onClick={() => handleRemoveFile("subsidios", index)} className="rounded-full p-1.5 hover:bg-muted text-muted-foreground hover:text-destructive transition-colors">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive animate-in slide-in-from-top-2">
            <strong>Erro: </strong> {error}
          </div>
        )}

        <div className="flex justify-end pt-4">
          <Button 
            type="submit" 
            disabled={loading || !hasAnyFile} 
            size="lg" 
            className="h-14 rounded-2xl px-10 text-base font-semibold tracking-wide shadow-xl shadow-primary/20 transition-all hover:scale-105 active:scale-95 disabled:scale-100"
          >
            Analisar Contrato e Iniciar I.A.
          </Button>
        </div>
      </form>
    </>
  )
}
