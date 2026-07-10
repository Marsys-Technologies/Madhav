/**
 * tap6_method_grep.ts — TAP-6 (TOTAL_AUDIT_PROTOCOL_v1_0.md §3, "Method
 * audit") CI implementation — the standing grep list called for at §3:
 * "the implementing function is checked against its cited shastra/spec —
 * specifically hunting the Approximation/simplified/TODO/hardcoded-default
 * pattern (KP-2's `# Approximation`, S-8's 15°-orb, Y-1's fall-through were
 * ALL greppable)."
 *
 * Patterns below are drawn directly from MARSYS_DEFECT_GAP_REGISTER_v2_0.md
 * §11.1 (M-1..M-22) — the exact substrings the audit cited as evidence for
 * "non-canonical methods wearing canonical labels".
 *
 * Discipline (ratchet, not a one-off): every hit is classified against
 * tap6_baseline.json.
 *   - hit's file is in the baseline for that pattern → QUARANTINED (known,
 *     tracked by an OPEN register row; the fixing lane deletes the baseline
 *     entry when it lands, which makes the grep start enforcing the fix).
 *   - hit's file is NOT in the baseline → FAIL (a NEW instance of a banned
 *     pattern was introduced — this is what protects the fixes other lanes
 *     land from regressing).
 *
 * No DB required — runs anywhere, always (never quarantined by "no DATABASE_URL").
 * Run: npx tsx platform/scripts/audit/tap/tap6_method_grep.ts
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import type { LawResult } from './lib/tap_db'
import { printReport } from './lib/tap_db'

const REPO_ROOT = path.join(__dirname, '../../../..')

type Pattern = {
  id: string
  description: string
  root: string // directory to search, relative to repo root
  pattern: RegExp
  excludeDirNames?: string[]
}

const PATTERNS: Pattern[] = [
  {
    id: 'two_pass_verified_literal',
    description: "'two_pass_verified' assigned as a string literal at an emit site (M-22: verification status must be computed by a verifier, never passed as a literal)",
    pattern: /(=|:)\s*['"]two_pass_verified['"]/,
    root: 'platform/python-sidecar',
    excludeDirNames: ['__tests__', 'tests'],
  },
  {
    id: 'rough_estimate_comment',
    description: 'Inline comment admitting a rough/approximate proxy formula (M-14 shadbala_proxy)',
    pattern: /#\s*rough\b/,
    root: 'platform/python-sidecar/ga_writers',
  },
  {
    id: 'safe_fallback_comment',
    description: "'# safe fallback' comment on a hardcoded value substituting for real computation (M-7)",
    pattern: /#\s*safe fallback/,
    root: 'platform/python-sidecar',
  },
  {
    id: 'falling_back_to_forensic',
    description: 'Native-fallback contamination — any chart silently receiving the NATIVE hardcoded params on error (M-7)',
    pattern: /falling back to FORENSIC/,
    root: 'platform/python-sidecar',
  },
  {
    id: 'native_fallback_longitudes',
    description: 'NATIVE_FALLBACK_LONGITUDES hardcoded table serving wrong-even-for-the-native values on a live endpoint (M-8)',
    pattern: /NATIVE_FALLBACK_LONGITUDES/,
    root: 'platform/python-sidecar',
  },
  {
    id: 'fabricated_citation_bphs_pranapada',
    description: "Formula cites 'BPHS' for a non-BPHS Pranapada Sphuta derivation (M-9, B.10 violation)",
    pattern: /BPHS: Pranapada Sphuta/,
    root: 'platform/python-sidecar',
  },
  {
    id: 'fabricated_citation_jaimini_sutram_trikona',
    description: "Formula cites 'Jaimini Sutram' for an invented 'Trikona Dasha Sphuta' (no such sphuta exists in that text) (M-9, B.10 violation)",
    pattern: /Jaimini Sutram: Trikona Dasha Sphuta/,
    root: 'platform/python-sidecar',
  },
]

type BaselineEntry = { pattern: string; file: string; register_row: string; note: string }

function loadBaseline(): BaselineEntry[] {
  const raw = readFileSync(path.join(__dirname, 'tap6_baseline.json'), 'utf-8')
  return JSON.parse(raw).entries as BaselineEntry[]
}

function walk(dir: string, excludeDirNames: string[], out: string[]): void {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git' || excludeDirNames.includes(entry)) continue
    const full = path.join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) {
      walk(full, excludeDirNames, out)
    } else if (entry.endsWith('.py') || entry.endsWith('.ts')) {
      out.push(full)
    }
  }
}

function runSearch(p: Pattern): string[] {
  const rootAbs = path.join(REPO_ROOT, p.root)
  const files: string[] = []
  walk(rootAbs, p.excludeDirNames ?? [], files)
  const hits: string[] = []
  for (const f of files) {
    const content = readFileSync(f, 'utf-8')
    if (p.pattern.test(content)) {
      hits.push(path.relative(REPO_ROOT, f))
    }
  }
  return hits
}

function main() {
  const baseline = loadBaseline()
  const results: LawResult[] = []

  for (const p of PATTERNS) {
    const hits = runSearch(p)
    const baselineFiles = new Set(baseline.filter((b) => b.pattern === p.id).map((b) => b.file))
    const newHits = hits.filter((h) => !baselineFiles.has(h))
    const knownHits = hits.filter((h) => baselineFiles.has(h))
    const missingBaseline = [...baselineFiles].filter((f) => !hits.includes(f))

    if (newHits.length > 0) {
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'FAIL',
        detail: `NEW hit(s) not in baseline: ${newHits.join(', ')}. (Known/tracked hits: ${knownHits.length})`,
      })
    } else if (knownHits.length > 0) {
      const rows = [...new Set(baseline.filter((b) => b.pattern === p.id && knownHits.includes(b.file)).map((b) => b.register_row))]
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'QUARANTINED',
        detail: `${knownHits.length} known hit(s), all tracked: ${knownHits.join(', ')}.`,
        register_rows: rows,
      })
    } else {
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'PASS',
        detail: missingBaseline.length > 0 ? `Zero hits — baseline entries for ${missingBaseline.join(', ')} are stale (fix landed); delete them from tap6_baseline.json.` : 'Zero hits.',
      })
    }
  }

  process.exit(printReport('TAP-6 Method Audit (grep set)', results))
}

main()
