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
 * tap6_baseline.json, keyed on (pattern, file, line-hash) — NOT just
 * (pattern, file). Ring-2 review (post-bacade1c) demonstrated that a
 * file-level key lets a SECOND, unrelated occurrence of an already-banned
 * pattern slip in uncaught anywhere in an already-baselined file (e.g. a new
 * `# safe fallback` hardcode added to a different function in the same file
 * that already has one baselined line). Keying on a hash of the matched
 * line's trimmed content instead means:
 *   - (pattern, file, line-hash) is in the baseline → QUARANTINED (known,
 *     tracked by an OPEN register row; the fixing lane deletes the baseline
 *     entry when it lands, which makes the grep start enforcing the fix).
 *   - the exact matched line is NOT in the baseline → FAIL (a NEW instance —
 *     could be a genuinely new pattern, OR a second unrelated occurrence in
 *     an already-baselined file; either way it must be looked at, not
 *     silently absorbed by a coarser file-level match).
 *
 * No DB required — runs anywhere, always (never quarantined by "no DATABASE_URL").
 * Run: npx tsx platform/scripts/audit/tap/tap6_method_grep.ts
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import type { LawResult } from './lib/tap_db'
import { printReport, lineHash } from './lib/tap_db'

const REPO_ROOT = path.join(__dirname, '../../../..')

type Pattern = {
  id: string
  description: string
  root: string // directory to search, relative to repo root
  pattern: RegExp
  excludeDirNames?: string[]
  /** Repo-relative FILE paths exempt from this pattern. File-level, deliberately not a
   *  directory: a directory exemption would silently cover future files dropped beside
   *  the sanctioned one. Keep this list to modules that are, by design, the only
   *  sanctioned producer of the string the pattern hunts. */
  exemptFiles?: string[]
}

const PATTERNS: Pattern[] = [
  {
    id: 'two_pass_verified_literal',
    // DESCRIPTION REWRITTEN 2026-08-01 to say exactly what the regex measures, no more.
    // It previously claimed "must be computed by a verifier, never passed as a literal" —
    // but the regex matches `= "two_pass_verified"` whether the RHS is an assertion or a
    // computed conditional, so it could not tell those apart. It went RED on `main` over
    // ga_nakshatra.py's M-22 *fix*: anti-correlated with code health. Teaching it to parse
    // conditionals would not help (`"two_pass_verified" if True else ...` asserts too), so
    // the honest path was instead made lexically distinct: callers use
    // brahmagyan.verification_vocab.two_pass_verdict(), which demands both values, and that
    // one file is exempt below.
    // RESIDUAL, named not solved: `two_pass_verdict(x, x)` still fabricates a pass. That is
    // a separate grep (call sites whose two arguments are the same expression) for a later
    // lane — going through the helper is not proof a detector ran.
    description: "the 'two_pass_verified' literal assigned OUTSIDE the sanctioned verification module (brahmagyan/verification_vocab.py). Sanctioned production is two_pass_verdict(engine, derived), which requires both values; a bare literal anywhere else is unearned (M-22 / CLAUDE.md §N.8)",
    pattern: /(=|:)\s*['"]two_pass_verified['"]/,
    root: 'platform/python-sidecar',
    excludeDirNames: ['__tests__', 'tests'],
    exemptFiles: ['platform/python-sidecar/brahmagyan/verification_vocab.py'],
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

type BaselineEntry = { pattern: string; file: string; line_hash: string; register_row: string; note: string }

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

type Hit = { file: string; line: number; hash: string; text: string }

function runSearch(p: Pattern): Hit[] {
  const rootAbs = path.join(REPO_ROOT, p.root)
  const files: string[] = []
  walk(rootAbs, p.excludeDirNames ?? [], files)
  const exempt = new Set(p.exemptFiles ?? [])
  const hits: Hit[] = []
  for (const f of files) {
    if (exempt.has(path.relative(REPO_ROOT, f))) continue
    const content = readFileSync(f, 'utf-8')
    const lines = content.split('\n')
    for (let i = 0; i < lines.length; i++) {
      if (p.pattern.test(lines[i])) {
        hits.push({ file: path.relative(REPO_ROOT, f), line: i + 1, hash: lineHash(lines[i]), text: lines[i].trim() })
      }
    }
  }
  return hits
}

function main() {
  const baseline = loadBaseline()
  const results: LawResult[] = []

  for (const p of PATTERNS) {
    const hits = runSearch(p)
    const baselineForPattern = baseline.filter((b) => b.pattern === p.id)
    const baselineKeys = new Set(baselineForPattern.map((b) => `${b.file}:${b.line_hash}`))
    const hitKeys = new Set(hits.map((h) => `${h.file}:${h.hash}`))
    const newHits = hits.filter((h) => !baselineKeys.has(`${h.file}:${h.hash}`))
    const knownHits = hits.filter((h) => baselineKeys.has(`${h.file}:${h.hash}`))
    const staleBaseline = baselineForPattern.filter((b) => !hitKeys.has(`${b.file}:${b.line_hash}`))

    if (newHits.length > 0) {
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'FAIL',
        detail: `NEW hit(s) not in baseline (new pattern instance, OR a second unrelated occurrence in an already-baselined file): ${newHits.map((h) => `${h.file}:${h.line}`).join(', ')}. (Known/tracked hits: ${knownHits.length})`,
      })
    } else if (knownHits.length > 0) {
      const rows = [...new Set(baselineForPattern.filter((b) => hitKeys.has(`${b.file}:${b.line_hash}`)).map((b) => b.register_row))]
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'QUARANTINED',
        detail: `${knownHits.length} known hit(s), all tracked: ${knownHits.map((h) => `${h.file}:${h.line}`).join(', ')}.`,
        register_rows: rows,
      })
    } else {
      results.push({
        id: `TAP6:${p.id}`,
        title: p.description,
        status: 'PASS',
        detail: staleBaseline.length > 0 ? `Zero hits — baseline entries for ${staleBaseline.map((b) => `${b.file}:${b.line_hash}`).join(', ')} are stale (fix landed); delete them from tap6_baseline.json.` : 'Zero hits.',
      })
    }
  }

  process.exit(printReport('TAP-6 Method Audit (grep set)', results))
}

main()
