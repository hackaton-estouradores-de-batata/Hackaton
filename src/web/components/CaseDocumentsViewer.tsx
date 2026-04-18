"use client"

import { useState } from "react"
import { ExternalLink, FileText, Download } from "lucide-react"
import type { CaseDocument } from "@/lib/types"

interface Props {
  documents: CaseDocument[]
}

const CATEGORY_LABEL: Record<string, string> = {
  autos: "Autos",
  subsidios: "Subsídios",
}

export function CaseDocumentsViewer({ documents }: Props) {
  const [selectedName, setSelectedName] = useState<string | null>(null)

  const selectedDocument = documents.find((doc) => doc.name === selectedName) ?? documents[0] ?? null
  const previewUrl = selectedDocument ? encodeURI(selectedDocument.url) : null
  const downloadUrl = selectedDocument ? encodeURI(`${selectedDocument.url}?download=1`) : null

  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-5 shadow-sm">
        <p className="mb-2 text-xs font-medium text-muted-foreground">Documentos do caso</p>
        <p className="text-sm text-muted-foreground">Nenhum PDF disponível para visualização neste caso.</p>
      </div>
    )
  }

  return (
    <div className="rounded-3xl border border-border/50 bg-background/50 p-6 shadow-xl shadow-black/5 backdrop-blur-xl">
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-primary">Documentos do caso</p>
          <p className="mt-1 text-sm text-muted-foreground">Selecione um documento para exibir no painel lateral ou abra-o integralmente.</p>
        </div>
        {selectedDocument && (
          <div className="flex flex-wrap items-center gap-2">
            <a
              href={previewUrl ?? "#"}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl bg-muted/50 px-4 py-2 text-xs font-semibold text-foreground transition-all hover:bg-muted hover:shadow-sm"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Abrir
            </a>
            <a
              href={downloadUrl ?? "#"}
              download={selectedDocument.display_name}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border/50 bg-background px-4 py-2 text-xs font-semibold text-foreground shadow-sm transition-all hover:bg-muted"
            >
              <Download className="h-3.5 w-3.5" />
              Baixar
            </a>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {documents.map((doc) => {
            const active = doc.name === selectedDocument?.name
            return (
              <button
                key={doc.name}
                type="button"
                onClick={() => setSelectedName(doc.name)}
                className={`flex w-full items-start gap-2 rounded-xl border px-3 py-3 text-left transition-colors ${
                  active ? "border-primary bg-primary/5" : "hover:bg-muted"
                }`}
              >
                <FileText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{doc.display_name}</p>
                  <p className="text-xs text-muted-foreground">{CATEGORY_LABEL[doc.category] ?? doc.category}</p>
                </div>
              </button>
            )
          })}
        </div>

        <div className="rounded-2xl border border-border/50 bg-muted/20 p-4 shadow-inner ring-1 ring-background/50">
          {selectedDocument ? (
            <div className="mx-auto w-full">
              <div className="aspect-[210/297] overflow-hidden rounded-xl border border-border/40 bg-zinc-100 shadow-sm sm:h-[800px] sm:aspect-auto">
                <iframe
                  key={selectedDocument.name}
                  src={previewUrl ?? undefined}
                  title={selectedDocument.display_name}
                  className="h-full w-full bg-transparent"
                />
              </div>
            </div>
          ) : (
            <div className="flex h-[720px] items-center justify-center rounded-xl border border-dashed border-border/50 text-sm font-medium text-muted-foreground">
              Selecione um documento na tabela acima para visualizá-lo aqui.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
