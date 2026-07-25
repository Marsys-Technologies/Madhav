#!/usr/bin/env tsx
/**
 * absence_lint_gate.ts — Elevation Campaign, Stream α (SATYA), Lane K1, Task 4 (if-time).
 *
 * Static, grep-based scan over `platform-mcp/src/tools/**` and
 * `platform/src/lib/retrieval/registry/**` source for ontological-absence phrasing (see
 * `_absence_patterns.ts`'s header for the exact definition — a string telling the caller a
 * fact/record DOES NOT EXIST, as opposed to "not on this page"/"filtered out") that is NOT
 * backed by a resolver-miss code path nearby in the same file.
 *
 * DELIBERATELY HEURISTIC, per the K1 task-3 spec ("flag candidates for human/Verifier review
 * rather than trying to be a perfect static analyzer") — false positives are expected and
 * acceptable, false silence is not. Two structural limitations, both documented rather than
 * hidden:
 *   1. "Nearby in the same source function" is approximated by a same-file line-WINDOW
 *      (±`ABSENCE_LINT_WINDOW` lines, default 25) around the absence-phrase line, not a real
 *      AST function-boundary walk — this file has no TypeScript parser dependency (same
 *      self-containment discipline as every other script in this directory; see
 *      `_mcp_client.ts`'s header for why). A grounding token far outside the phrase's actual
 *      function but inside the line window can produce a false "grounded" verdict; a grounding
 *      token just outside the window can produce a false "ungrounded" flag. Both directions are
 *      accepted per the heuristic mandate above.
 *   2. A string literal containing absence phrasing that is itself a *documentation comment*
 *      (like the one you are reading right now, or `_absence_patterns.ts`'s own note strings)
 *      will match the regex — this file's own source, and `_absence_patterns.ts` itself, WILL
 *      appear as candidate hits. That is correct behavior for a grep-based tool, not a bug;
 *      the point of a lint is to surface candidates for a human, not to silently special-case
 *      itself.
 *
 * Default behavior is REPORT-ONLY (never fails CI — `ABSENCE_LINT_STRICT` unset or not
 * "true"): every candidate is reported with a WARN status (never counted against the gate's
 * exit code by `_report.ts`'s convention) so a caller sees the full candidate list without a
 * heuristic false-positive redlining every stream's build. Setting `ABSENCE_LINT_STRICT=true`
 * upgrades every UNGROUNDED candidate (no grounding token found in its line window) to FAIL —
 * an opt-in stricter mode for a lane that wants to hard-gate on this, mirroring the informational-
 * vs-blocking split `budget_census_gate.ts`'s C1 clamp spot-check already establishes in this
 * same directory.
 *
 * Single-mode script — this is a pure source-tree lint (no MCP tool calls, no PLAN/LIVE split
 * the way smoke_gate.ts/budget_census_gate.ts/receipt_gate.ts need one).
 *
 * Run (from `platform/`):
 *   npx tsx scripts/census/elev_gates/absence_lint_gate.ts
 * Run (strict mode):
 *   ABSENCE_LINT_STRICT=true npx tsx scripts/census/elev_gates/absence_lint_gate.ts
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { MCP_TOOLS_ROOT } from './_tool_enumeration'
import { ABSENCE_PATTERNS, GROUNDING_TOKENS, scanLineForAbsenceClaims } from './_absence_patterns'
import { printGateReport, type GateResult } from './_report'
import { envOrDefault } from './_mcp_client'

// This file lives at platform/scripts/census/elev_gates/ — four levels up is the repo root
// (same computation _tool_enumeration.ts's MCP_TOOLS_ROOT uses).
const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..')
const REGISTRY_ROOT = path.join(REPO_ROOT, 'platform/src/lib/retrieval/registry')

const WINDOW = Number(envOrDefault('ABSENCE_LINT_WINDOW', '25'))
const STRICT = envOrDefault('ABSENCE_LINT_STRICT', 'false').toLowerCase() === 'true'

function walkTs(dir: string, out: string[]): void {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue
    const full = path.join(dir, entry)
    let st
    try {
      st = statSync(full)
    } catch {
      continue
    }
    if (st.isDirectory()) walkTs(full, out)
    else if ((entry.endsWith('.ts') || entry.endsWith('.tsx')) && !entry.endsWith('.test.ts') && !entry.endsWith('.test.tsx')) out.push(full)
  }
}

function listScanRoots(): string[] {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  walkTs(REGISTRY_ROOT, files)
  return files.sort()
}

export type AbsenceCandidate = {
  file: string
  line_number: number
  line_text: string
  pattern_ids: string[]
  grounded: boolean
  grounding_evidence: string[] // which GROUNDING_TOKENS matched, within window
}

/** Scans one file's lines for absence-claim phrasing, then checks a ±WINDOW line window
 *  around each hit for any GROUNDING_TOKENS token (Task 4's "resolver-miss code path nearby"
 *  heuristic — see header for the documented limitations of this approximation). */
export function scanFileForAbsenceCandidates(filePath: string, fileText: string, windowSize = WINDOW): AbsenceCandidate[] {
  const lines = fileText.split('\n')
  const candidates: AbsenceCandidate[] = []
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!
    const matches = scanLineForAbsenceClaims(line)
    if (matches.length === 0) continue
    const windowStart = Math.max(0, i - windowSize)
    const windowEnd = Math.min(lines.length, i + windowSize + 1)
    const windowText = lines.slice(windowStart, windowEnd).join('\n')
    const groundingEvidence = GROUNDING_TOKENS.filter((tok) => windowText.includes(tok))
    candidates.push({
      file: filePath,
      line_number: i + 1,
      line_text: line.trim().slice(0, 200),
      pattern_ids: matches.map((m) => m.id),
      grounded: groundingEvidence.length > 0,
      grounding_evidence: groundingEvidence,
    })
  }
  return candidates
}

function relPath(f: string): string {
  return path.relative(REPO_ROOT, f)
}

function main(): void {
  const files = listScanRoots()
  const results: GateResult[] = []
  let totalCandidates = 0
  let ungroundedCount = 0

  results.push({
    id: 'absence-lint:scan-scope',
    title: `Static absence-phrasing scan scope`,
    status: files.length > 0 ? 'PASS' : 'FAIL',
    detail: `${files.length} .ts/.tsx files scanned across platform-mcp/src/tools/** + platform/src/lib/retrieval/registry/** (excluding *.test.ts). ${ABSENCE_PATTERNS.length} absence patterns, ${GROUNDING_TOKENS.length} grounding tokens. Window=±${WINDOW} lines. Strict mode=${STRICT}.`,
  })

  for (const file of files) {
    let text: string
    try {
      text = readFileSync(file, 'utf-8')
    } catch (err) {
      results.push({
        id: `absence-lint:read-error:${relPath(file)}`,
        title: `Could not read ${relPath(file)}`,
        status: 'QUARANTINED',
        detail: String(err),
      })
      continue
    }
    const candidates = scanFileForAbsenceCandidates(file, text)
    for (const c of candidates) {
      totalCandidates++
      if (!c.grounded) ungroundedCount++
      results.push({
        id: `absence-lint:${relPath(file)}:${c.line_number}`,
        title: `${relPath(file)}:${c.line_number} — absence phrasing [${c.pattern_ids.join(',')}]${c.grounded ? ' (grounded)' : ' (UNGROUNDED — candidate)'}`,
        status: c.grounded ? 'PASS' : STRICT ? 'FAIL' : 'WARN',
        detail: c.grounded
          ? `Line: "${c.line_text}" — grounding token(s) found within ±${WINDOW} lines: ${c.grounding_evidence.join(', ')}.`
          : `Line: "${c.line_text}" — NO grounding token (${GROUNDING_TOKENS.slice(0, 4).join('/')}/...) found within ±${WINDOW} lines. Candidate for human/Verifier review: confirm this absence claim traces to a real resolver-miss code path (a query that ran and returned zero rows) rather than a generic/stub message. ${STRICT ? 'STRICT mode: counted as a gate FAIL.' : 'Non-blocking (WARN) — set ABSENCE_LINT_STRICT=true to hard-gate on this.'}`,
      })
    }
  }

  results.push({
    id: 'absence-lint:summary',
    title: `Absence-phrasing candidates: ${totalCandidates} total, ${ungroundedCount} ungrounded`,
    status: 'PASS',
    detail: `Informational summary row — the individual per-line rows above carry the actual PASS/WARN/FAIL verdicts. ${ungroundedCount} of ${totalCandidates} candidates had no grounding token in their line window.`,
  })

  process.exit(printGateReport(`absence_lint_gate${STRICT ? ' (STRICT)' : ''}`, results))
}

main()
