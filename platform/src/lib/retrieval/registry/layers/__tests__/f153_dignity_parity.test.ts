/**
 * f153_dignity_parity.test.ts — F-153 regression guard.
 *
 * Before this fix, `DIGNITY_WEIGHT.moolatrikona` (register_d9_judgment.ts) and its
 * hand-duplicated copy in register_d10_pact.ts both scored moolatrikona identically to
 * `own` (1.5 == 1.5). Classically these are NOT equal — BPHS Ch.27 Saptavargaja/Sthāna
 * Bala gives moolatrikona 45 ṣaṣṭyaṃśa vs own's 30
 * (`platform/python-sidecar/ga_writers/ga_vargas_writer.py:1774-1786`), and every Python
 * consumer map already asserted moolatrikona > own before this TS surface caught up
 * (`ga_condition_writer.DIGNITY_SCORES`, `formulas.DIGNITY_SCORE`, `bo_laksana._DIGNITY_SCORE`,
 * `bo_pratijna_v4_engine.DIGNITY_BAND`).
 *
 * This test (a) asserts the strict ordering on the fixed TS scale, (b) asserts d10 no
 * longer hand-duplicates the map (one registry, not two — the defect's own propagation
 * mechanism), and (c) cross-checks *ordering* (not value equality — the scales genuinely
 * differ, 0-1 vs -2..2) against the live Python source of truth.
 *
 * Deliberately python-free (same rationale as `signal_glossary.parity.test.ts`'s own
 * docstring: "must fail on a CI runner that has no Python interpreter at all" — the repo's
 * `unit-tests` CI job runs bare `python3` with no sidecar deps installed, and
 * `ga_condition_writer.py` unconditionally imports `psycopg` at module load, so actually
 * executing it here is not viable). Instead this parses the `DIGNITY_SCORES` dict literal
 * straight out of the .py source text, the same text-based approach
 * `signal_glossary.parity.test.ts` uses for its own cross-language check.
 *
 * Companion Python-side test: `platform/python-sidecar/tests/
 * test_f62_moolatrikona_downstream_vocabulary.py` (`test_moolatrikona_outranks_own_in_every_score_map`).
 * Band regression (own/moolatrikona must both still clear the classical-extreme gate):
 * `significator_condition.f113.test.ts`.
 */
import { describe, expect, it } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { DIGNITY_WEIGHT } from '../register_d9_judgment'

// platform/src/lib/retrieval/registry/layers/__tests__ → platform/
const PLATFORM_DIR = path.resolve(__dirname, '..', '..', '..', '..', '..', '..')
const GA_CONDITION_WRITER_PATH = path.join(
  PLATFORM_DIR, 'python-sidecar', 'ga_writers', 'ga_condition_writer.py',
)
const D10_PACT_PATH = path.resolve(__dirname, '..', 'register_d10_pact.ts')

describe('F-153 — moolatrikona strictly outranks own (dignity weighting)', () => {
  it('DIGNITY_WEIGHT: exalted > moolatrikona > own, own unchanged at the isDignityExtreme band floor', () => {
    expect(DIGNITY_WEIGHT.moolatrikona).toBeGreaterThan(DIGNITY_WEIGHT.own)
    expect(DIGNITY_WEIGHT.exalted).toBeGreaterThan(DIGNITY_WEIGHT.moolatrikona)
    // Hard constraint from the F-153 finding: own must NOT be lowered — it gates
    // isDignityExtreme()'s |weight| >= 1.5 band in significator_condition.ts.
    expect(DIGNITY_WEIGHT.own).toBe(1.5)
    expect(DIGNITY_WEIGHT.moolatrikona).toBeGreaterThanOrEqual(1.5)
  })

  it('register_d10_pact.ts imports DIGNITY_WEIGHT rather than redefining it', () => {
    const src = fs.readFileSync(D10_PACT_PATH, 'utf8')
    expect(src).toMatch(/import\s*\{\s*DIGNITY_WEIGHT\s*\}\s*from\s*['"]\.\/register_d9_judgment['"]/)
    // No local re-declaration of the constant (the pre-fix defect's own propagation
    // mechanism — a hand-duplicated copy that could silently drift from the original).
    expect(src).not.toMatch(/const\s+DIGNITY_WEIGHT\s*:/)
  })

  it('matches the ordering (not value) of the live Python source of truth', () => {
    expect(fs.existsSync(GA_CONDITION_WRITER_PATH)).toBe(true)
    const py = fs.readFileSync(GA_CONDITION_WRITER_PATH, 'utf8')
    const dictMatch = py.match(/DIGNITY_SCORES:\s*dict\[str,\s*float\]\s*=\s*\{([^}]*)\}/)
    expect(dictMatch, 'DIGNITY_SCORES dict literal not found — has ga_condition_writer.py been restructured?').not.toBeNull()
    const body = dictMatch![1]
    const tierOf = (key: string): number => {
      const m = body.match(new RegExp(`"${key}":\\s*([\\d.]+)`))
      expect(m, `key "${key}" not found in DIGNITY_SCORES`).not.toBeNull()
      return Number(m![1])
    }
    const exalted = tierOf('exalted')
    const moolatrikona = tierOf('moolatrikona')
    const own = tierOf('own')
    expect(exalted).toBeGreaterThan(moolatrikona)
    expect(moolatrikona).toBeGreaterThan(own)
    // Cross-check the TS scale reproduces the SAME ordering (ordering parity, not value
    // parity — 0-1 Python scale vs -2..2 TS scale).
    expect(DIGNITY_WEIGHT.exalted).toBeGreaterThan(DIGNITY_WEIGHT.moolatrikona)
    expect(DIGNITY_WEIGHT.moolatrikona).toBeGreaterThan(DIGNITY_WEIGHT.own)
  })
})
