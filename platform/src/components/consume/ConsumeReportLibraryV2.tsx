'use client'

/**
 * ConsumeReportLibraryV2 — trigger button + slide-over wrapper for ReportLibrary.
 *
 * Designed for import into ConsumeChatV2 (or any V2 orchestrator) without
 * modifying ConsumeChatV2.tsx itself. Manages its own open/selectedDomain state
 * so the parent only needs to pass the `reports` array.
 *
 * Part of Chat V2 Chrome Parity Phase C — item C.6.
 */

import { useState } from 'react'
import { BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Report } from '@/lib/db/types'
import { ReportLibrary } from './ReportLibrary'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

// ─── Props ────────────────────────────────────────────────────────────────────

interface Props {
  reports: Report[]
  className?: string
}

// ─── Component ───────────────────────────────────────────────────────────────

export function ConsumeReportLibraryV2({ reports, className }: Props) {
  const [open, setOpen] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)

  return (
    <>
      {/* Trigger button — consistent with ConversationHistoryButton brand styling */}
      <button
        type="button"
        data-testid="v2-report-library-trigger"
        aria-label="Open report library"
        title="Report library"
        onClick={() => setOpen(true)}
        className={cn(
          'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors',
          open
            ? 'border-[var(--brand-gold)]/60 bg-[var(--brand-gold)]/10 text-[var(--brand-gold)]'
            : 'border-border text-muted-foreground hover:border-[var(--brand-gold)]/40 hover:text-foreground',
          className,
        )}
      >
        <BookOpen className="h-3 w-3" />
        <span>Reports</span>
        {reports.length > 0 && (
          <span className="ml-1 rounded-full bg-muted px-1 font-mono text-[10px]">
            {reports.length}
          </span>
        )}
      </button>

      {/* Slide-over panel */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="right"
          data-testid="v2-report-library-panel"
          className="w-80 border-l border-zinc-800 bg-[var(--brand-charcoal)] p-0 sm:w-96"
        >
          <SheetHeader className="border-b border-zinc-800 px-4 pb-3 pt-4">
            <SheetTitle className="flex items-center gap-2 text-[var(--brand-gold)]">
              <BookOpen className="h-4 w-4" />
              Report Library
            </SheetTitle>
          </SheetHeader>

          <div className="overflow-y-auto">
            <ReportLibrary
              reports={reports}
              selectedDomain={selectedDomain}
              onSelect={(domain) => {
                setSelectedDomain(domain)
                // Keep panel open so the user can see their selection;
                // orchestrator can close it by controlling `open` if needed.
              }}
            />
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}
