#!/usr/bin/env tsx
/**
 * evals/k2/classical_attribution_checker.ts — Lane K2 item 6 (EL-09).
 *
 * Pattern-style checker over served prose against `classical_attribution_table_v1_0.json`'s ~20
 * core classical Jyotish attributions. Flags a response that makes one of these well-known
 * classical misattributions (Sun/Moon karakatva swap, Sade-Sati phase inversion, 9th-house
 * over-read, etc.) — the EL-09 "precision class" of confident-but-checkable error.
 *
 * This is a GREP-STYLE check, not a full NLP claim verifier: it flags CANDIDATE misattributions
 * for a human/Opus reviewer, the same way answer_eval.ts's FABRICATION_PATTERNS flag candidate
 * fabrications. A hit means "this text matches a known-wrong phrasing shape," not an infallible
 * verdict — some entries carry negative lookaheads to reduce false positives on already-hedged,
 * correct prose (e.g. ATTR-02 doesn't fire on "Jupiter's dharma-karakatva indirectly supports
 * wealth expression" because that sentence never says "Jupiter is the wealth karaka").
 *
 * Usage:
 *   npx tsx evals/k2/classical_attribution_checker.ts <text-file-or-transcript.json>
 */
import { readFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { loadTranscript } from './transcript_utils.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const TABLE_PATH = join(__dirname, 'classical_attribution_table_v1_0.json')

export interface AttributionEntry {
  id: string
  claim_family: string
  wrong_patterns: string[]
  correct_attribution: string
  classical_basis: string
  severity: 'T' | 'V' | 'C'
  note?: string
}

export interface AttributionTableFile {
  artifact: 'CLASSICAL_ATTRIBUTION_TABLE'
  version: string
  entries: AttributionEntry[]
}

export function loadAttributionTable(path: string = TABLE_PATH): AttributionTableFile {
  return JSON.parse(readFileSync(path, 'utf-8')) as AttributionTableFile
}

export interface AttributionFlag {
  id: string
  claim_family: string
  severity: 'T' | 'V' | 'C'
  matched_pattern: string
  matched_snippet: string
  correct_attribution: string
  classical_basis: string
}

/**
 * Scans `text` against every entry's wrong_patterns. Each entry fires at most once (first
 * matching pattern wins) so a single misattribution doesn't inflate the flag count.
 */
export function checkClassicalAttributions(text: string, table: AttributionTableFile = loadAttributionTable()): AttributionFlag[] {
  const flags: AttributionFlag[] = []
  for (const entry of table.entries) {
    for (const patternSrc of entry.wrong_patterns) {
      let re: RegExp
      try {
        re = new RegExp(patternSrc, 'i')
      } catch {
        continue // malformed pattern in the table — skip rather than crash the checker
      }
      const match = re.exec(text)
      if (match) {
        flags.push({
          id: entry.id,
          claim_family: entry.claim_family,
          severity: entry.severity,
          matched_pattern: patternSrc,
          matched_snippet: match[0].length > 200 ? match[0].slice(0, 197) + '...' : match[0],
          correct_attribution: entry.correct_attribution,
          classical_basis: entry.classical_basis,
        })
        break // one entry, one flag max
      }
    }
  }
  return flags
}

export interface ClassicalAttributionResult {
  entries_checked: number
  flags: AttributionFlag[]
  flag_count: number
  trust_breaking_count: number
  value_losing_count: number
  cosmetic_count: number
  clean: boolean
}

export function gradeClassicalAttributions(text: string, table?: AttributionTableFile): ClassicalAttributionResult {
  const tbl = table ?? loadAttributionTable()
  const flags = checkClassicalAttributions(text, tbl)
  return {
    entries_checked: tbl.entries.length,
    flags,
    flag_count: flags.length,
    trust_breaking_count: flags.filter((f) => f.severity === 'T').length,
    value_losing_count: flags.filter((f) => f.severity === 'V').length,
    cosmetic_count: flags.filter((f) => f.severity === 'C').length,
    clean: flags.length === 0,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [inputPath] = process.argv.slice(2)
  if (!inputPath) {
    console.error('Usage: npx tsx evals/k2/classical_attribution_checker.ts <text-file-or-transcript.json>')
    process.exit(1)
  }
  let text: string
  if (inputPath.endsWith('.json')) {
    const t = loadTranscript(inputPath)
    text = t.final_answer
  } else {
    text = readFileSync(inputPath, 'utf-8')
  }
  const result = gradeClassicalAttributions(text)
  console.log(JSON.stringify(result, null, 2))
}
