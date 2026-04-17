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
  const [selectedName, setSelectedName] = useState(documents[0]?.name ?? null)

  const selectedDocument = documents.find((doc) => doc.name === selectedName) ?? documents[0] ?? null

  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-5 shadow-sm">
        <p className="mb-2 text-xs font-medium text-muted-foreground">Documentos do caso</p>
        <p className="text-sm text-muted-foreground">Nenhum PDF disponível para visualização neste caso.</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border bg-background p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground">Documentos do caso</p>
          <p className="text-sm text-muted-foreground">Selecione um PDF para visualizar ou abrir em nova aba.</p>
        </div>
        {selectedDocument && (
          <div className="flex items-center gap-2">
            <a
              href={selectedDocument.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Abrir
            </a>
            <a
              href={selectedDocument.url}
              download
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted"
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

        <div className="rounded-xl border bg-muted/20 p-4">
          {selectedDocument ? (
            <div className="mx-auto w-full max-w-[820px]">
              <div className="aspect-[210/297] overflow-hidden rounded-lg border bg-white shadow-sm">
                <iframe
                  key={selectedDocument.name}
                  src={selectedDocument.url}
                  title={selectedDocument.display_name}
                  className="h-full w-full bg-white"
                />
              </div>
            </div>
          ) : (
            <div className="flex h-[720px] items-center justify-center text-sm text-muted-foreground">
              Selecione um documento para visualizar.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
