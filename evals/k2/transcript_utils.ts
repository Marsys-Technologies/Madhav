/**
 * evals/k2/transcript_utils.ts — shared loading/normalization helpers for Lane K2 graders.
 */
import { readFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import type { AccountingFile, NormalizedTranscript, RawTranscript, TranscriptCall } from './types.js'

export const __dirname = dirname(fileURLToPath(import.meta.url))
// evals/k2/ -> repo root is two levels up (evals/ -> repo root)
export const REPO_ROOT = join(__dirname, '..', '..')
export const CAPABILITY_MAP_DIR = join(
  REPO_ROOT,
  '00_ARCHITECTURE/llm_consumption_audit/capability_map',
)

/** Lenient JSON parse: strict → trailing-comma repair. Mirrors Ω7's darkcorpus matcher so K2
 * graders tolerate the same class of truncated/almost-valid transcript files. */
export function lenientParseJson<T>(raw: string): T {
  try {
    return JSON.parse(raw) as T
  } catch {
    const repaired = raw.replace(/,(\s*[}\]])/g, '$1')
    return JSON.parse(repaired) as T
  }
}

export function loadTranscript(path: string): NormalizedTranscript {
  const raw = lenientParseJson<RawTranscript>(readFileSync(path, 'utf-8'))
  return normalizeTranscript(raw)
}

export function normalizeTranscript(raw: RawTranscript): NormalizedTranscript {
  if (Array.isArray(raw)) {
    return { calls: raw, final_answer: deriveFinalAnswerFromCalls(raw) }
  }
  return {
    calls: raw.calls ?? [],
    final_answer: raw.final_answer ?? deriveFinalAnswerFromCalls(raw.calls ?? []),
    query: raw.query,
    domain: raw.domain,
    chart_id: raw.chart_id,
    t_query_posed_ms: raw.t_query_posed_ms,
    t_answer_complete_ms: raw.t_answer_complete_ms,
    t_first_signal_ms: raw.t_first_signal_ms,
    followups_needed: raw.followups_needed,
    friction_notes: raw.friction_notes,
  }
}

/**
 * The bare Ω7 harness-run format (tool/arguments/result_raw only) does not capture the
 * consumer's final prose answer as a distinct field — the sealed harness (§1) says the final
 * answer IS captured, but the reused Ω7 capture path only logged tool traffic. Rather than
 * silently pretending an answer exists, K2 graders that need final-answer text should be
 * given it explicitly (see CLI --final-answer flag in each script). This fallback marks the
 * gap honestly instead of fabricating prose from tool output.
 */
function deriveFinalAnswerFromCalls(_calls: TranscriptCall[]): string {
  return ''
}

const chart8 = (chartId: string) => chartId.slice(0, 8)

export function loadAccounting(domain: string, chartId: string): AccountingFile {
  const path = join(
    CAPABILITY_MAP_DIR,
    `COMPLETENESS_ACCOUNTING_${domain}_${chart8(chartId)}_v1_0.json`,
  )
  return JSON.parse(readFileSync(path, 'utf-8')) as AccountingFile
}

/** Normalizes an mcp tool name for loose matching: strips the mcp__<server>__ prefix. */
export function bareToolName(tool: string): string {
  const parts = tool.split('__')
  return parts[parts.length - 1] ?? tool
}

/** Concatenates every result_raw for calls to a given (bare) tool name, for substring search. */
export function resultTextByTool(calls: TranscriptCall[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const c of calls) {
    const bare = bareToolName(c.tool)
    const prev = map.get(bare) ?? ''
    map.set(bare, prev + '\n' + (c.result_raw ?? ''))
  }
  return map
}
