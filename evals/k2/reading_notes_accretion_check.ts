#!/usr/bin/env tsx
/**
 * evals/k2/reading_notes_accretion_check.ts — Lane K2 item 7 (EL-60a).
 *
 * Checks whether `reading_notes_get` (platform-mcp/src/tools/reading_notes.ts) auto-accretes
 * per-domain-per-session notes, per ELEVATION_REGISTER_v1_0.md EL-60: "accrete reading notes
 * automatically per domain per session so the appendix compounds."
 *
 * This is a READ-ONLY static/structural check — platform-mcp/src/lib/**, platform-mcp/tools/**
 * are OUTSIDE γ's Lane K2 manifest (evals/**, bench/**, platform/scripts/answer_eval.ts,
 * 00_ARCHITECTURE/llm_consumption_audit/capability_map/**), so this script reads the tool's
 * source to VERIFY the gap mechanically rather than fix it. See EL60A_PARKED_HONEST_v1_0.md for
 * the disposition.
 *
 * Live corroboration: this lane also called `mcp__marsys-jis-direct__reading_notes_get` live
 * against chart 482012f1 during authoring and confirmed the returned `reading_notes_markdown`
 * is byte-identical to the hardcoded `READING_NOTES_482012F1` constant in the tool's source —
 * i.e. the live server is genuinely serving the static string this check inspects, not
 * something this check would miss by only reading source.
 *
 * Usage:
 *   npx tsx evals/k2/reading_notes_accretion_check.ts [path-to-reading_notes.ts]
 */
import { existsSync, readFileSync } from 'fs'
import { join } from 'path'
import { REPO_ROOT } from './transcript_utils.js'

const DEFAULT_SOURCE_PATH = join(REPO_ROOT, 'platform-mcp/src/tools/reading_notes.ts')

export interface AccretionCheckResult {
  source_path: string
  source_readable: boolean
  has_write_call: boolean // INSERT/UPDATE/db write pattern
  has_session_scoping_param: boolean // session_id / domain param on the tool schema
  has_per_domain_param: boolean
  is_pure_static_lookup: boolean // readingNotesFor() keyed only by chart_id, no accumulation
  verdict: 'ACCRETES_PER_DOMAIN_PER_SESSION' | 'STATIC_MANUAL_LOOKUP_ONLY' | 'INDETERMINATE_SOURCE_UNREADABLE'
  evidence: string[]
}

const WRITE_PATTERNS = [/INSERT\s+INTO/i, /UPDATE\s+\w+\s+SET/i, /\.insert\(/i, /\.upsert\(/i, /db_conn\.query.*INSERT/i]
const SESSION_PARAM_PATTERNS = [/session_id/i, /sessionId/]
const DOMAIN_PARAM_PATTERNS = [/\bdomain\s*:\s*z\./i, /\bdomain\s*:\s*string/i]

export function checkReadingNotesAccretion(sourcePath: string = DEFAULT_SOURCE_PATH): AccretionCheckResult {
  const evidence: string[] = []
  if (!existsSync(sourcePath)) {
    return {
      source_path: sourcePath,
      source_readable: false,
      has_write_call: false,
      has_session_scoping_param: false,
      has_per_domain_param: false,
      is_pure_static_lookup: false,
      verdict: 'INDETERMINATE_SOURCE_UNREADABLE',
      evidence: [`source file not found at ${sourcePath} — cannot verify structurally`],
    }
  }

  const source = readFileSync(sourcePath, 'utf-8')
  const has_write_call = WRITE_PATTERNS.some((p) => p.test(source))
  const has_session_scoping_param = SESSION_PARAM_PATTERNS.some((p) => p.test(source))
  const has_per_domain_param = DOMAIN_PARAM_PATTERNS.some((p) => p.test(source))

  // The specific accretion-negative signature this codebase's implementation carries: a single
  // exported markdown constant + a pure `chartId === CANONICAL_CHART_ID ? CONST : null` lookup,
  // with the tool schema declaring only `chart_id` as input.
  const hasHardcodedConstant = /export const READING_NOTES_\w+\s*=\s*`/.test(source)
  const toolSchemaChartIdOnly = /\{\s*chart_id:\s*z\.string\(\)\.uuid\(\)/.test(source) && !has_session_scoping_param && !has_per_domain_param
  const is_pure_static_lookup = hasHardcodedConstant && toolSchemaChartIdOnly && !has_write_call

  if (hasHardcodedConstant) evidence.push('found a hardcoded exported markdown constant (READING_NOTES_*)')
  if (toolSchemaChartIdOnly) evidence.push('tool schema declares chart_id as the ONLY input parameter — no session_id, no domain')
  if (!has_write_call) evidence.push('no INSERT/UPDATE/db-write call found anywhere in the source — nothing this tool does can persist a new note')
  if (has_write_call) evidence.push('a write call WAS found — accretion may be present; re-inspect manually before trusting the static verdict')

  const verdict: AccretionCheckResult['verdict'] =
    is_pure_static_lookup ? 'STATIC_MANUAL_LOOKUP_ONLY' : has_write_call ? 'ACCRETES_PER_DOMAIN_PER_SESSION' : 'STATIC_MANUAL_LOOKUP_ONLY'

  return {
    source_path: sourcePath,
    source_readable: true,
    has_write_call,
    has_session_scoping_param,
    has_per_domain_param,
    is_pure_static_lookup,
    verdict,
    evidence,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [sourcePathArg] = process.argv.slice(2)
  const result = checkReadingNotesAccretion(sourcePathArg)
  console.log(JSON.stringify(result, null, 2))
  if (result.verdict === 'STATIC_MANUAL_LOOKUP_ONLY') {
    console.warn(
      '\nEL-60a GAP CONFIRMED: reading_notes_get is a static, manual/on-demand lookup — it does ' +
        'NOT auto-accrete per-domain-per-session notes. See evals/k2/EL60A_PARKED_HONEST_v1_0.md.',
    )
  }
}
