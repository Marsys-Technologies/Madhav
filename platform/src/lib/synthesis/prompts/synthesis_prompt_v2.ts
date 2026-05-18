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
CITATION FORMAT:
When you cite an MSR signal, place its ID directly after the word or phrase it supports — no wrapper, no arrow, no parentheses. Example: "Mercury's eight-system convergence SIG.MSR.413 is the chart's primary operational force." The UI replaces each SIG.MSR.NNN with a numbered superscript badge [1], [2], … in order of first appearance; a citation panel shows the signal name when the user clicks a badge.

STRICT OUTPUT RULES — violations degrade the UI:
• No (→ SIG.MSR.NNN) wrappers. Bare ID only: SIG.MSR.NNN.
• No F.CORE.NNN, F.HSE.NNN, or any non-SIG.MSR reference in visible prose.
• No custom markup tags such as ‹sanskrit›, <cite>, or similar. Write Sanskrit terms in plain text with a brief inline gloss if needed: "Sasha Mahapurusha Yoga (Saturn exalted in a Kendra)".
• No markdown footnote syntax ([^1], [^1]: …).
• Do not invent SIG.MSR.NNN IDs. Only cite signal IDs that appear in the retrieved context.`

export function consumeSystemPromptV2(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false,
): string {
  return consumeSystemPrompt(chart, reports, style, blindMode) + CITATION_APPENDIX
}
