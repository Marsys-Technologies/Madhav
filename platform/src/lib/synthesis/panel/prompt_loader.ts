/**
 * MARSYS-JIS Phase 7 — Panel prompt loader
 * schema_version: 1.1 (Phase 12: FUB-1/2/3 parity — chart_context + content blocks)
 *
 * Loads prompt templates from src/lib/prompts/panel/ and injects
 * synthesis request context. Kept separate so member_runner and
 * adjudicator share the same loading logic.
 */

import 'server-only'

import fs from 'fs'
import path from 'path'
import type { SynthesisRequest } from '../types'
import type { AnonymizedMemberOutput } from './types'

const MAX_CHART_CONTEXT_TOKENS = 32768
const MAX_TOOL_RESULTS_TOKENS = 16384
const CHARS_PER_TOKEN = 4

function loadTemplate(filename: string): string {
  const templatePath = path.join(
    process.cwd(),
    'src/lib/prompts/panel',
    filename,
  )
  return fs.readFileSync(templatePath, 'utf-8')
}

export function loadPanelMemberPrompt(
  variant_tag: string,
  request: SynthesisRequest,
): string {
  const template = loadTemplate(`${variant_tag}.md`)
  const bundleSummary = request.bundle.mandatory_context
    .map(e => `${e.canonical_id} (${e.role})`)
    .join(', ')

  // FUB-1 parity: inject canonical birth particulars
  const chartName = request.chart_context?.name ?? 'the native'
  const birthDate = request.chart_context?.birth_date ?? '<birth date unavailable>'
  const birthTime = request.chart_context?.birth_time ?? '<birth time unavailable>'
  const birthPlace = request.chart_context?.birth_place ?? '<birth place unavailable>'

  // FUB-2 parity: build chart context block from vector_search results
  const hasFloor = request.bundle.mandatory_context.some(e => e.role === 'floor')
  const vsResults = request.tool_results
    .filter(tb => tb.tool_name === 'vector_search')
    .flatMap(tb => tb.results)

  let chartContextBlock = ''
  if (vsResults.length > 0 && hasFloor) {
    const maxChars = MAX_CHART_CONTEXT_TOKENS * CHARS_PER_TOKEN
    const chunks = vsResults
      .map(r => `[chunk:${r.signal_id ?? 'unknown'}]\n${r.content}`)
      .join('\n\n---\n\n')
    const truncated = chunks.length > maxChars ? chunks.slice(0, maxChars) + '\n[...truncated]' : chunks
    chartContextBlock = `<CHART_CONTEXT_BLOCK source="vector_search">\n${truncated}\n</CHART_CONTEXT_BLOCK>`
  }

  // FUB-3 parity: inject pre-fetched non-vector_search tool results
  const nonVsResults = request.tool_results.filter(tb => tb.tool_name !== 'vector_search')
  let toolResultsBlock = ''
  if (nonVsResults.length > 0) {
    const maxChars = MAX_TOOL_RESULTS_TOKENS * CHARS_PER_TOKEN
    const blocks = nonVsResults
      .map(tb =>
        tb.results
          .map(r => `[signal:${r.signal_id ?? tb.tool_name}] ${r.content}`)
          .join('\n')
      )
      .join('\n\n')
    const truncated = blocks.length > maxChars ? blocks.slice(0, maxChars) + '\n[...truncated]' : blocks
    toolResultsBlock = `<PRE_FETCHED_TOOL_RESULTS>\n${truncated}\n</PRE_FETCHED_TOOL_RESULTS>`
  }

  return template
    .replace('{{query}}', request.query)
    .replace('{{query_class}}', request.query_plan.query_class)
    .replace('{{bundle_summary}}', bundleSummary)
    .replace('{{style}}', request.style)
    .replace('{{audience_tier}}', request.audience_tier)
    .replace('{{chart_name}}', chartName)
    .replace('{{birth_date}}', birthDate)
    .replace('{{birth_time}}', birthTime)
    .replace('{{birth_place}}', birthPlace)
    .replace('{{chart_context_block}}', chartContextBlock)
    .replace('{{tool_results_block}}', toolResultsBlock)
}

export function loadAdjudicatorPrompt(
  variant_tag: string,
  anonymized: AnonymizedMemberOutput[],
  request: SynthesisRequest,
): string {
  const template = loadTemplate(`${variant_tag}.md`)

  const membersBlock = anonymized
    .map(m => `## ${m.member_label}\n\n${m.answer}`)
    .join('\n\n---\n\n')

  return template
    .replace('{{query}}', request.query)
    .replace('{{query_class}}', request.query_plan.query_class)
    .replace('{{style}}', request.style)
    .replace('{{audience_tier}}', request.audience_tier)
    .replace('{{panel_members_block}}', membersBlock)
}
