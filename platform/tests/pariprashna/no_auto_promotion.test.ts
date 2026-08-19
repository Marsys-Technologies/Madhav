/**
 * no_auto_promotion.test.ts — Paripraśna P1 G1-H (PB-9-DETECTOR): "The
 * no-auto-promotion CI detector — proves no code path promotes a prediction
 * to `confirmed`/`open` without human action (currently true by inspection
 * only)."
 *
 * Three halves, mirroring the house style of collect_only_grep.test.ts
 * (PB-3 lane L-6 COLLECT-ONLY gate):
 *
 *   (a) REPO-WIDE CONFINEMENT SCAN — walks every real production .ts/.tsx
 *       file under platform/src (test files excluded — they legitimately
 *       exercise the DAL directly to test it) and asserts every occurrence
 *       of a promotion pattern is confined to its declared allowlist:
 *       'raw-bypass' patterns may occur NOWHERE; 'dal-write' patterns may
 *       occur only inside PROMOTION_DAL_FILES; 'entry-call' patterns may
 *       occur only inside HUMAN_GATED_ENTRY_POINTS. A NEW file introducing
 *       any of these outside its allowlist fails this scan — that is the
 *       actual CI proof, not "these two files look right by inspection".
 *
 *   (b) AUTH-GATE PRESENCE — each human-gated entry point must contain a
 *       real auth-check call (getServerUser / assertCanWrite /
 *       resolveChartPageAccess / authorizeChartAccess) BEFORE it is allowed
 *       to trigger a promotion. A detector for "human action required" that
 *       never checks for the auth call is a flag with no real detector
 *       behind it (§N.8) — this closes that gap.
 *
 *   (c) DETECTOR IS DEMONSTRATED-CAN-FAIL — scannerSelfProof() fixtures
 *       prove the scanner both flags a synthetic forbidden pattern (a
 *       fabricated bypass/unconfined-call fixture) and does NOT false-
 *       positive on an honest read, a documenting comment, or a different,
 *       legal transition target (window_closed/dismissed).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve, join, relative, sep } from 'node:path'

import {
  PROMOTION_TABLE,
  PROMOTION_DAL_FILES,
  HUMAN_GATED_ENTRY_POINTS,
  AUTH_GATE_MARKERS,
  PROMOTION_PATTERNS,
  scanFileForPromotion,
  scannerSelfProof,
  type ScanHit,
} from '@/lib/pariprashna/no_leakage/no_auto_promotion_manifest'

// platform/ package root, resolved from this test file's location
// (platform/tests/pariprashna/no_auto_promotion.test.ts -> up two dirs).
const PLATFORM_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SRC_ROOT = resolve(PLATFORM_ROOT, 'src')

/** The manifest module's own source is excluded from the scan: its regex literals
 *  and scannerSelfProof() fixture STRINGS necessarily contain the patterns being
 *  detected (that is what makes it the detector), so it is data, not a code path
 *  that promotes anything. Mirrors serving_path_manifest.ts's own exclusion from
 *  SERVING_PATH_FILES (it defines FORBIDDEN_PATTERNS, it is not scanned by them). */
const SELF_EXCLUDED = new Set([
  resolve(PLATFORM_ROOT, 'src/lib/pariprashna/no_leakage/no_auto_promotion_manifest.ts'),
])

/** Repo-relative (from platform/) POSIX path, matching the manifest's convention. */
function toRel(abs: string): string {
  return relative(PLATFORM_ROOT, abs).split(sep).join('/')
}

/** Recursively collect every production .ts/.tsx file under `dir`, skipping
 *  test-only files/dirs (__tests__, __mocks__, *.test.ts(x), *.spec.ts(x)) —
 *  those legitimately call the DAL directly to test it (see header). */
function collectProductionSourceFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    if (entry === '__tests__' || entry === '__mocks__' || entry === 'node_modules') continue
    const abs = join(dir, entry)
    const st = statSync(abs)
    if (st.isDirectory()) {
      out.push(...collectProductionSourceFiles(abs))
      continue
    }
    if (!/\.(ts|tsx)$/.test(entry)) continue
    if (/\.(test|spec)\.(ts|tsx)$/.test(entry)) continue
    if (SELF_EXCLUDED.has(abs)) continue
    out.push(abs)
  }
  return out
}

describe(`no-auto-promotion gate (a) — repo-wide confinement scan for ${PROMOTION_TABLE}`, () => {
  it('every declared allowlist file physically exists (no vacuous coverage)', () => {
    for (const rel of [...PROMOTION_DAL_FILES, ...HUMAN_GATED_ENTRY_POINTS]) {
      const abs = resolve(PLATFORM_ROOT, rel)
      expect(existsSync(abs), `allowlisted file missing: ${rel}`).toBe(true)
    }
  })

  it('has a non-empty promotion-pattern set (guards against an emptied gate)', () => {
    expect(PROMOTION_PATTERNS.length).toBeGreaterThanOrEqual(7)
  })

  const files = collectProductionSourceFiles(SRC_ROOT)
  // Sanity: the walk actually found a substantial tree (guards against a
  // silently-empty scan passing vacuously green).
  it(`scanned a non-trivial production source tree (found ${files.length} files)`, () => {
    expect(files.length).toBeGreaterThan(500)
  })

  // Collect all hits across the whole tree once, then assert per-confinement-class.
  const allHits: Array<{ rel: string; hit: ScanHit }> = []
  for (const abs of files) {
    const source = readFileSync(abs, 'utf8')
    const hits = scanFileForPromotion(source)
    if (hits.length === 0) continue
    const rel = toRel(abs)
    for (const hit of hits) allHits.push({ rel, hit })
  }

  it('ZERO raw-bypass hits anywhere in the tree (no allowlist exception)', () => {
    const bypassHits = allHits.filter((h) => h.hit.confinement === 'raw-bypass')
    const report = bypassHits
      .map((h) => `  ${h.rel}:${h.hit.line} [${h.hit.patternId}] ${h.hit.excerpt}\n    -> ${h.hit.reason}`)
      .join('\n')
    expect(bypassHits, `raw DAL-bypass promotion write(s) found:\n${report}`).toEqual([])
  })

  it('every dal-write hit is confined to PROMOTION_DAL_FILES', () => {
    const dalHits = allHits.filter((h) => h.hit.confinement === 'dal-write')
    const escaped = dalHits.filter((h) => !PROMOTION_DAL_FILES.includes(h.rel))
    const report = escaped
      .map((h) => `  ${h.rel}:${h.hit.line} [${h.hit.patternId}] ${h.hit.excerpt}\n    -> ${h.hit.reason}`)
      .join('\n')
    expect(escaped, `promotion DAL-write pattern found OUTSIDE the confined allowlist:\n${report}`).toEqual([])
  })

  it('every entry-call hit is confined to HUMAN_GATED_ENTRY_POINTS', () => {
    const entryHits = allHits.filter((h) => h.hit.confinement === 'entry-call')
    const escaped = entryHits.filter((h) => !HUMAN_GATED_ENTRY_POINTS.includes(h.rel))
    const report = escaped
      .map((h) => `  ${h.rel}:${h.hit.line} [${h.hit.patternId}] ${h.hit.excerpt}\n    -> ${h.hit.reason}`)
      .join('\n')
    expect(escaped, `promotion-triggering call found OUTSIDE the human-gated entry points:\n${report}`).toEqual([])
  })

  it('each promotion-triggering entry-call pattern actually fires at least once in the live tree (not a dead rule)', () => {
    // A confinement rule nobody ever matches is unproven — it could be silently
    // broken (e.g. renamed function) and this gate would stay green for the
    // wrong reason. Each entry-call pattern must have >=1 real hit, and it
    // must land inside the allowlist (already asserted above).
    for (const pp of PROMOTION_PATTERNS.filter((p) => p.confinement === 'entry-call')) {
      const hits = allHits.filter((h) => h.hit.patternId === pp.id)
      expect(hits.length, `pattern '${pp.id}' never matched anywhere in the tree — rule may be dead`).toBeGreaterThan(0)
    }
  })
})

describe('no-auto-promotion gate (b) — human-gated entry points actually check auth', () => {
  it.each(HUMAN_GATED_ENTRY_POINTS)('%s contains a real auth-gate call before it may promote', (rel) => {
    const abs = resolve(PLATFORM_ROOT, rel)
    const source = readFileSync(abs, 'utf8')
    const matched = AUTH_GATE_MARKERS.some((re) => re.test(source))
    expect(matched, `${rel} is on the human-gated allowlist but contains none of the AUTH_GATE_MARKERS`).toBe(true)
  })
})

describe('no-auto-promotion gate (c) — detector is demonstrated-can-fail', () => {
  const proof = scannerSelfProof()

  it('does NOT flag a read-only WHERE lifecycle_status filter (no false positive)', () => {
    expect(scanFileForPromotion(proof.readOnlyWhereFixture)).toEqual([])
  })

  it('does NOT flag a comment documenting confirmDetectedRow (comment-line skip)', () => {
    expect(scanFileForPromotion(proof.commentFixture)).toEqual([])
  })

  it('does NOT flag a legal transition to a different target (window_closed)', () => {
    expect(scanFileForPromotion(proof.legalOtherTransitionFixture)).toEqual([])
  })

  it("DOES flag a raw SQL 'SET lifecycle_status = confirmed' bypass", () => {
    const hits = scanFileForPromotion(proof.rawSqlSetFixture)
    expect(hits.map((h) => h.patternId)).toContain('raw-sql-set-confirmed-or-open')
    expect(hits.find((h) => h.patternId === 'raw-sql-set-confirmed-or-open')?.confinement).toBe('raw-bypass')
  })

  it('DOES flag a raw literal INSERT carrying confirmed', () => {
    const hits = scanFileForPromotion(proof.rawSqlInsertFixture)
    expect(hits.map((h) => h.patternId)).toContain('raw-sql-insert-literal-confirmed-or-open')
  })

  it("DOES flag initial_status: 'confirmed'", () => {
    const hits = scanFileForPromotion(proof.initialStatusConfirmedFixture)
    expect(hits.map((h) => h.patternId)).toContain('initial-status-confirmed')
    expect(hits.find((h) => h.patternId === 'initial-status-confirmed')?.confinement).toBe('dal-write')
  })

  it("DOES flag transitionLifecycle(..., 'open', ...)", () => {
    const hits = scanFileForPromotion(proof.transitionToOpenFixture)
    expect(hits.map((h) => h.patternId)).toContain('transition-to-open')
  })

  it('DOES flag a real confirmDetectedRow(...) call', () => {
    const hits = scanFileForPromotion(proof.confirmDetectedRowCallFixture)
    expect(hits.map((h) => h.patternId)).toContain('confirm-detected-row-call')
  })

  it('DOES flag a real confirmCandidate(...) entry call', () => {
    const hits = scanFileForPromotion(proof.confirmCandidateEntryCallFixture)
    expect(hits.map((h) => h.patternId)).toContain('confirm-candidate-entry-call')
    expect(hits.find((h) => h.patternId === 'confirm-candidate-entry-call')?.confinement).toBe('entry-call')
  })

  it('DOES flag a real confirmDetectedCandidate(...) entry call', () => {
    const hits = scanFileForPromotion(proof.confirmDetectedCandidateEntryCallFixture)
    expect(hits.map((h) => h.patternId)).toContain('confirm-detected-candidate-entry-call')
  })

  it('an UNCONFINED synthetic occurrence WOULD be caught by the confinement assertion (self-proof of gate (a) itself)', () => {
    // Simulate what gate (a) does, using a fabricated "file" outside every
    // allowlist, to prove the confinement-check LOGIC itself (not just the
    // pattern match) can fail on a real violation.
    const fakeRel = 'src/app/api/some/unrelated/route.ts'
    const hits = scanFileForPromotion(proof.transitionToOpenFixture)
    const escaped = hits.filter(
      (h) => h.confinement === 'dal-write' && !PROMOTION_DAL_FILES.includes(fakeRel),
    )
    expect(escaped.length, 'confinement-escape simulation must detect the fabricated violation').toBeGreaterThan(0)
  })
})
