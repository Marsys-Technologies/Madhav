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
CITATION FORMAT — GFM FOOTNOTES:
When you cite an MSR signal, use a GFM footnote reference inline and add the corresponding footnote definition at the end of your response.

Inline (inside prose): place [^N] immediately after the word or phrase it supports.
Example: "Mercury's eight-system convergence[^1] is the chart's primary operational force."

Footnote block (at the end of the response, after all prose):
[^1]: SIG.MSR.413
[^2]: SIG.MSR.042

Number footnotes in order of first appearance. Each footnote definition maps exactly one index to one canonical signal ID.

STRICT OUTPUT RULES — violations degrade the UI:
• Use [^N] inline footnote syntax. Do NOT use (→ SIG.MSR.NNN) wrappers or bare SIG.MSR.NNN IDs in visible prose.
• No F.CORE.NNN, F.HSE.NNN, or any non-SIG.MSR reference in visible prose.
• No custom markup tags such as ‹sanskrit›, <cite>, or similar. Write Sanskrit terms in plain text with a brief inline gloss if needed: "Sasha Mahapurusha Yoga (Saturn exalted in a Kendra)".
• Do not invent SIG.MSR.NNN IDs. Only cite signal IDs that appear in the retrieved context.
• Each [^N] must have a corresponding [^N]: SIG.MSR.NNN definition at the end.`

export function consumeSystemPromptV2(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false,
): string {
  return consumeSystemPrompt(chart, reports, style, blindMode) + CITATION_APPENDIX
}
