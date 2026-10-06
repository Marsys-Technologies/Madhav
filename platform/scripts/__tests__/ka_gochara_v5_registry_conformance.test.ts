import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * A5.3 writerbase_conformance — the REGISTRY-ROW item of ORCHESTRATOR_CONVERGENCE_CLOSE §5, executed
 * against the seed row of `ka_gochara_v5` (the Python half is
 * `python-sidecar/tests/l3/gochara/test_a53_writerbase_conformance.py`).
 *
 * §5: "Registry row with correct scope, asset_type, layer, populated depends_on (real edges, not []),
 * count_sql + target_floor, sort_order; has_substeps=true if heavy".
 *
 * The seed row was written for the INERT skeleton (`light`, `depends_on: []`, count over windows); migration 1304
 * (PR 3101) brought depends_on, has_substeps, the 8-hour cap and the eval-window truth counter into line, so every gap this file once
 * carried as a strict expected-failure is now a plain positive assertion (no `it.fails` remains).
 */
const WRITER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py'
)

const row = () => {
  const r = ASSETS.find(a => a.asset_id === 'ka_gochara_v5')
  expect(r, 'ka_gochara_v5 must have a seed row').toBeDefined()
  return r!
}

describe('ka_gochara_v5 registry-row conformance (ORCHESTRATOR_CONVERGENCE_CLOSE §5)', () => {
  it('names the asset the writer registers, per_chart, layer kala, with a writer', () => {
    const src = readFileSync(WRITER_PATH, 'utf8')
    expect(src).toMatch(/^ASSET_ID\s*=\s*"ka_gochara_v5"/m)
    expect(row().layer).toBe('kala')
    expect(row().scope).toBe('per_chart')
    expect(row().has_writer).toBe(true)
  })

  it('is INERT to every planner (is_active=false) until the steward activates it', () => {
    expect(row().is_active).toBe(false)
  })

  it('carries count_sql, target_floor and sort_order', () => {
    expect(row().count_sql).toMatch(/chart_id=\$1/)
    expect(typeof row().target_floor).toBe('number')
    expect(typeof row().sort_order).toBe('number')
  })

  // §5 "populated depends_on — real edges, not []": CLOSED by migration 1304 (PR 3101), whose seed row now says what the writer truly reads.
  it('declares real depends_on edges (closed by migration 1304)', () => {
    expect(row().depends_on).toEqual(['ga_positions', 'ga_dashas'])
  })

  // §5 "has_substeps=true if heavy": CLOSED by migration 1304 (PR 3101). The writer's class sets `has_substeps = True` and plans
  // rules → convention → body×8 → manifest → snapshot → per-class inventory/coverage/record/verify. The timeout is the one
  // small-test AND measuring-build cap (steward TIMEOUT-RULING, 8 h): a healthy run must never be ended by it.
  it('declares has_substeps=true and the 8-hour writer cap (closed by migration 1304)', () => {
    expect(row().has_substeps).toBe(true)
    expect((row() as unknown as { writer_timeout_seconds?: number }).writer_timeout_seconds).toBe(28800)
  })

  // CLAUDE.md §N.4 — count_sql must count what the writer writes (the ka_gochara cockpit-count defect, migration 1230, in miniature):
  // v5 writes the evaluation windows into ka_gochara_eval_window, not kala_gochara_windows; migration 1304 landed that counter.
  it("counts what the writer writes: the chart-scoped '5.0' evaluation windows (closed by migration 1304)", () => {
    expect(row().count_sql).toMatch(/^SELECT COUNT\(\*\) FROM ka_gochara_eval_window WHERE chart_id=\$1 AND generation='5\.0'$/)
    expect(row().count_sql).not.toMatch(/kala_gochara_windows/)
    expect((row() as unknown as { target_table?: string }).target_table).toBe('ka_gochara_eval_window')
  })
})
