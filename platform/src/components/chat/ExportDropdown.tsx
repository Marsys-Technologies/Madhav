'use client'

import { useState } from 'react'
import { Download, FileText, FileJson, FileType2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'

interface Props {
  conversationId: string
  chartId?: string
  messageId?: string
}

export function ExportDropdown({ conversationId, chartId, messageId }: Props) {
  const [copied, setCopied] = useState(false)

  const base = `/api/conversations/${conversationId}/export`
  const scope = messageId ? `&messageId=${encodeURIComponent(messageId)}` : ''

  function downloadMd() {
    window.location.href = `${base}?format=md${scope}`
  }

  function downloadPdf() {
    if (chartId) window.open(`/clients/${encodeURIComponent(chartId)}/pariprashna/print?conversationId=${encodeURIComponent(conversationId)}${scope}`, '_blank', 'noopener,noreferrer')
    else window.open(`${base}?format=pdf${scope}`, "_blank", "noopener,noreferrer")
  }

  async function copyJson() {
    try {
      const resp = await fetch(`${base}?format=json${scope}`)
      if (!resp.ok) return
      const text = await resp.text()
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard access may fail in non-secure contexts
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="Export conversation"
        title="Export conversation"
        className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        {copied ? (
          <span className="text-[10px] text-emerald-400 font-medium">Copied!</span>
        ) : (
          <Download className="size-4" />
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={downloadMd}>
          <FileText className="h-3.5 w-3.5" aria-hidden />
          Download Markdown
        </DropdownMenuItem>
        <DropdownMenuItem onClick={downloadPdf}>
          <FileType2 className="h-3.5 w-3.5" aria-hidden />
          {chartId ? 'Print / Save PDF' : 'Download PDF'}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => { void copyJson() }}>
          <FileJson className="h-3.5 w-3.5" aria-hidden />
          {copied ? 'Copied!' : 'Copy JSON'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
