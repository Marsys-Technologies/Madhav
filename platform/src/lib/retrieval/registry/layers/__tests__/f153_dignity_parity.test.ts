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
 * differ, 0-1 vs -2..2) against the live Python source of truth, the same drift-detection
 * pattern `signal_glossary.parity.test.ts` / `coverage_gate.test.ts` use for their own
 * cross-language checks.
 *
 * Companion Python-side test: `platform/python-sidecar/tests/
 * test_f62_moolatrikona_downstream_vocabulary.py` (`test_moolatrikona_outranks_own_in_every_score_map`).
 * Band regression (own/moolatrikona must both still clear the classical-extreme gate):
 * `significator_condition.f113.test.ts`.
 */
import { describe, expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { DIGNITY_WEIGHT } from '../register_d9_judgment'

// platform/src/lib/retrieval/registry/layers/__tests__ → platform/
const PLATFORM_DIR = path.resolve(__dirname, '..', '..', '..', '..', '..', '..')
const PYTHON_SIDECAR_DIR = path.join(PLATFORM_DIR, 'python-sidecar')
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
    const result = spawnSync(
      'python3',
      ['-c', 'from ga_writers.ga_condition_writer import DIGNITY_SCORES; ' +
        'print(DIGNITY_SCORES["exalted"], DIGNITY_SCORES["moolatrikona"], DIGNITY_SCORES["own"])'],
      { encoding: 'utf-8', cwd: PYTHON_SIDECAR_DIR },
    )
    expect(result.status, `python3 failed: ${result.stderr}`).toBe(0)
    // Some sidecar modules print sys.path debug noise on import (unrelated to this test) —
    // the values we want are on the LAST non-empty stdout line.
    const lines = result.stdout.trim().split('\n')
    const lastLine = lines[lines.length - 1]
    const [exalted, moolatrikona, own] = lastLine.trim().split(/\s+/).map(Number)
    expect(exalted).toBeGreaterThan(moolatrikona)
    expect(moolatrikona).toBeGreaterThan(own)
    // Cross-check the TS scale reproduces the SAME ordering (ordering parity, not value
    // parity — 0-1 Python scale vs -2..2 TS scale).
    expect(DIGNITY_WEIGHT.exalted).toBeGreaterThan(DIGNITY_WEIGHT.moolatrikona)
    expect(DIGNITY_WEIGHT.moolatrikona).toBeGreaterThan(DIGNITY_WEIGHT.own)
  })
})
