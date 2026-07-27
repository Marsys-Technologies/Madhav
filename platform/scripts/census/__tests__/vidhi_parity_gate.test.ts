/**
 * vidhi_parity_gate.test.ts — PARIŚODHANA B2 (Ω8 floor-wiring) induced-drift test.
 * ================================================================================
 * Proves the anti-drift gate (check_vidhi_registry_parity.mjs) actually FAILS on drift, not just
 * passes on the current tree — the "CI gate present AND failing on an induced drift" requirement.
 *
 * Hermetic: feeds the gate SYNTHETIC dump/regen fixtures via its env-override hooks
 * (VIDHI_TS_DUMP_FILE / VIDHI_PY_PRIMS_FILE / VIDHI_PY_FLOORS_FILE / VIDHI_REGEN_FILE) with
 * VIDHI_PARITY_SKIP_COVERAGE=1, so it needs neither python3, tsx, nor a DB — it runs in any CI job.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const GATE = resolve(fileURLToPath(import.meta.url), '../../check_vidhi_registry_parity.mjs')

const item = (primitive_id: string, order: number, args_override: Record<string, unknown> = {}) =>
  ({ primitive_id, order, band: 'acharya_floor', args_override, hard_floor: false })

// A matched, gate-clean synthetic registry: one wealth floor carrying every Ω8-required family +
// the two floor_vargas the regen fixture below demands.
const PRIMITIVES = [
  { primitive_id: 'divisional_facts', version: 1, definition: 'x', category: 'structural', live_tool: 'ganita_chart_facts_get', tool_args: {}, fallback_face: null, known_gap: null, mandatory_tags: [], cr27_prevents: [] },
  { primitive_id: 'argala_read', version: 1, definition: 'y', category: 'structural', live_tool: 'ganita_chart_facts_get', tool_args: {}, fallback_face: null, known_gap: null, mandatory_tags: [], cr27_prevents: [] },
]
const WEALTH_FLOOR = {
  intent: 'wealth_deepdive', version: 1, cr27_coverage: [], notes: null,
  floor_items: [
    item('divisional_facts', 1, { varga: 'D1' }),
    item('divisional_facts', 2, { varga: 'D9' }),
    item('ashtakavarga_scan', 3),
    item('special_lagna_read', 4),
    item('argala_read', 5),
    item('dispositor_closure_read', 6),
    item('mechanism_read', 7),
    item('cross_ayanamsha_variation', 8, { point: 'JUPITER' }),
  ],
}
const REGEN = {
  domains: [{
    domain: 'wealth', intent: 'wealth_deepdive', floor_vargas: ['D1', 'D9'],
    floor_items: [
      { floor_tool: 'divisional_facts' }, { floor_tool: 'ashtakavarga_scan' },
      { floor_tool: 'special_lagna_read' }, { floor_tool: 'argala_read' },
      { floor_tool: 'dispositor_closure_read' }, { floor_tool: 'mechanism_read' },
      { floor_tool: 'cross_ayanamsha_agreement' },
    ],
  }],
}

let dir: string
function fixture(name: string, obj: unknown): string {
  const p = join(dir, name)
  writeFileSync(p, JSON.stringify(obj))
  return p
}
/** Run the gate with the given fixture files; return its exit code (0 = pass). */
function runGate(tsDump: unknown, pyPrims: unknown, pyFloors: unknown, regen: unknown): number {
  const env = {
    ...process.env,
    VIDHI_TS_DUMP_FILE: fixture('ts.json', tsDump),
    VIDHI_PY_PRIMS_FILE: fixture('pp.json', pyPrims),
    VIDHI_PY_FLOORS_FILE: fixture('pf.json', pyFloors),
    VIDHI_REGEN_FILE: fixture('regen.json', regen),
    VIDHI_PARITY_SKIP_COVERAGE: '1',
  }
  try {
    execFileSync('node', [GATE], { env, encoding: 'utf8', stdio: 'pipe' })
    return 0
  } catch (e) {
    return (e as { status?: number }).status ?? 1
  }
}

beforeAll(() => { dir = mkdtempSync(join(tmpdir(), 'vidhi-parity-')) })
afterAll(() => { rmSync(dir, { recursive: true, force: true }) })

describe('vidhi registry parity gate — induced-drift', () => {
  it('PASSES (exit 0) on a matched, Ω8-complete registry', () => {
    const ts = { primitives: PRIMITIVES, floors: [WEALTH_FLOOR] }
    expect(runGate(ts, { primitives: PRIMITIVES }, { floors: [WEALTH_FLOOR] }, REGEN)).toBe(0)
  })

  it('FAILS (exit 1) when the Python primitive dump drops one primitive (TS↔Python drift)', () => {
    const ts = { primitives: PRIMITIVES, floors: [WEALTH_FLOOR] }
    const pyPrimsDrifted = { primitives: [PRIMITIVES[0]] } // dropped argala_read
    expect(runGate(ts, pyPrimsDrifted, { floors: [WEALTH_FLOOR] }, REGEN)).not.toBe(0)
  })

  it('FAILS (exit 1) when a floor drops a regen-required floor_varga (TS↔Ω8-regen coverage drift)', () => {
    // Drop divisional_facts(D9) from BOTH TS and Python floors so assertion 1 stays clean and this
    // exercises assertion 2 (the regen-coverage check) specifically.
    const floorNoD9 = { ...WEALTH_FLOOR, floor_items: WEALTH_FLOOR.floor_items.filter((i) => (i.args_override as { varga?: string }).varga !== 'D9') }
    const ts = { primitives: PRIMITIVES, floors: [floorNoD9] }
    expect(runGate(ts, { primitives: PRIMITIVES }, { floors: [floorNoD9] }, REGEN)).not.toBe(0)
  })
})
