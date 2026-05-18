/**
 * Chat V2 synthesis system prompt — fork of consumeSystemPrompt with
 * citation rendering instructions for the [N] superscript UI.
 *
 * R6.2 (2026-05-18): switched from → SIG.MSR.NNN inline markers to GFM
 * footnote syntax ([^N] inline + [^N]: SIG.MSR.NNN definitions at end).
 * The UI renders [^N] as inline numbered badges and suppresses the
 * definition block — matching CITATION_APPENDIX format below.
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
When you reference MSR signals in your answer, use GFM footnote syntax:
- Inline: place [^N] at the point of reference (e.g. "Saturn activates the 7th [^1]").
- Definitions: at the very end of your response list each one as [^N]: SIG.MSR.NNN.
Number citations in order of first appearance. The UI renders [^N] as a numbered badge
and hides the definition block. Do NOT use the → SIG.MSR.NNN inline format.`

export function consumeSystemPromptV2(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false,
): string {
  return consumeSystemPrompt(chart, reports, style, blindMode) + CITATION_APPENDIX
}
