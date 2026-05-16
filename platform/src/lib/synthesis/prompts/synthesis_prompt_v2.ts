/**
 * Chat V2 synthesis system prompt — fork of consumeSystemPrompt with
 * citation rendering instructions for the [N] superscript UI.
 *
 * Extends the base prompt with a directive to emit SIG.MSR.NNN citations
 * so the V2 renderer can substitute them with inline numbered badges.
 * Does NOT change the citation format (gate remains valid).
 */

import { consumeSystemPrompt, type ConsumeStyle } from '@/lib/claude/system-prompts'

interface ChartContext {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
}

interface ReportEntry {
  domain: string
  title: string
  version: string
}

export const CITATION_APPENDIX = `

---
CITATION FORMAT (V2 UI):
When you reference MSR signals in your answer, use the inline format (→ SIG.MSR.NNN).
The UI will automatically number them [1], [2], … in order of first appearance and show a
citation side panel. Do NOT use numeric footnotes like [^1] — use the SIG.MSR.NNN format.`

export function consumeSystemPromptV2(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false,
): string {
  return consumeSystemPrompt(chart, reports, style, blindMode) + CITATION_APPENDIX
}
