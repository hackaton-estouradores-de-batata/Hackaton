"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { createCase } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { UploadCloud, FileText, X, Loader2, Gavel } from "lucide-react"

export function NewCaseForm() {
  const router = useRouter()
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
      autosFiles.forEach((file) => formData.append("autos_files", file))
      subsidiosFiles.forEach((file) => formData.append("subsidios_files", file))

      const created = await createCase(formData)
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
              <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Fluxo esperado
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">Ingestão orientada por documentos</h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              Nesta etapa o advogado só envia os PDFs. Número do processo, autor, CPF, valor da causa, alegações
              e contexto jurídico são extraídos automaticamente dos autos e dos subsídios durante a análise.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-border/50 bg-muted/20 p-5 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
                <UploadCloud className="h-5 w-5" />
              </div>
              <p className="text-sm font-semibold">1. Envio dos PDFs</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Separe autos do processo e subsídios do banco para o backend persistir os documentos corretamente.
              </p>
            </div>
            <div className="rounded-2xl border border-border/50 bg-muted/20 p-5 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 ring-1 ring-emerald-500/20 dark:text-emerald-400">
                <FileText className="h-5 w-5" />
              </div>
              <p className="text-sm font-semibold">2. Extração automática</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                O pipeline lê os PDFs e preenche os dados do caso sem cadastro manual de número, autor, CPF ou valor.
              </p>
            </div>
            <div className="rounded-2xl border border-border/50 bg-muted/20 p-5 shadow-sm">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600 ring-1 ring-blue-500/20 dark:text-blue-400">
                <Gavel className="h-5 w-5" />
              </div>
              <p className="text-sm font-semibold">3. Caso pronto para revisão</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Quando o processamento termina, o sistema já abre o painel do caso com documentos, recomendação e outcome.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-border/50 bg-emerald-500/5 p-8 shadow-xl shadow-black/5 backdrop-blur-xl transition-all">
          <div className="mb-6 border-b border-border/50 pb-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Ingestão de Documentos
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">Upload dos PDFs</h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              Envie ao menos um PDF de autos ou de subsídios. O backend organiza os arquivos por categoria e inicia a
              extração assim que o caso é criado.
            </p>
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
            Enviar PDFs e iniciar análise
          </Button>
        </div>
      </form>
    </>
  )
}
