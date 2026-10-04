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
 * The seed row was written for the INERT skeleton (`light`, `depends_on: []`, count over windows) and
 * has not followed the writer, which is now a heavy substep writer. The two gaps below are asserted
 * as STRICT expected-failures (`it.fails`): the day the row is brought into line they turn red and
 * force the marker's removal — never a silent pass, never a silent drift. They are reported, not
 * patched here: changing a registry row for a live asset needs a routine migration (the seed owns only
 * `target_table` on conflict) and belongs with the activation step, which is the steward's.
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

  // GAP 1 (§5 "populated depends_on — real edges, not []"): the heavy writer reads L1 facts + daśā rows,
  // the rule registry, and the A2 boundary substrate; the seed still says [].
  it.fails('declares real depends_on edges (GAP: the seed row still says [])', () => {
    expect(row().depends_on?.length ?? 0).toBeGreaterThan(0)
  })

  // GAP 2 (§5 "has_substeps=true if heavy"): the writer's class sets `has_substeps = True` and plans
  // rules → convention → body×8 → manifest → snapshot → per-class inventory/coverage/record/verify.
  it.fails('declares has_substeps=true (GAP: the seed row still says false)', () => {
    expect(row().has_substeps).toBe(true)
  })

  // GAP 3 (CLAUDE.md §N.4 — count_sql must count what the writer writes; the ka_gochara cockpit-count
  // defect, migration 1230, in miniature): the row counts kala_gochara_windows at '5.0', but this
  // writer does not write windows yet (the window sweep is pending); it writes contacts + records.
  it.fails("counts what the writer writes (GAP: counts windows '5.0'; the writer writes records)", () => {
    expect(row().count_sql).toMatch(/ka_gochara_relationship_record|kala_gochara_contacts/)
  })
})
