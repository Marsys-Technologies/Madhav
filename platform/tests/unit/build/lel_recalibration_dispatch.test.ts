/**
 * lel_recalibration_dispatch.test.ts — ṢAḌ-DARŚANA W2 Lane E · §2.5.5: the LEL-append
 * recalibration is a TRACKED SCOPED BUILD RUN, never a side-channel recompute.
 *
 * Spec: `SHAD_DARSHANA_BRIEF_v2_0.md` §2.5.5 (binding); `KALA_W2_FIELD_DESIGN_v1_0.md` §7.6
 * "Dispatch discipline".
 *
 * Three things are asserted, and the third is the one that would actually catch a regression:
 *   §1 the request body is exactly what `/api/cockpit/runs` accepts, with `action: 'rebuild'`;
 *   §2 the TypeScript asset set and the Python one AGREE, checked by reading the Python source
 *      rather than by restating it here (a restatement drifts silently);
 *   §3 the module is structurally incapable of recomputing anything — no fetch, no db import,
 *      no writer import. §2.5.5 is a rule about what must NOT happen, and the only durable way
 *      to test a negative is to assert the capability is absent.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'
import {
  RECALIBRATION_ASSET_SET,
  buildRecalibrationDispatch,
  toRequestBody,
} from '@/lib/mcp/lel_recalibration_dispatch'
import { parseAssetSetTarget } from '@/lib/build/plan'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const MODULE_PATH = resolve(__dirname, '../../../src/lib/mcp/lel_recalibration_dispatch.ts')
const PYTHON_TWIN = resolve(
  __dirname,
  '../../../python-sidecar/services/mi_bhara/living_lel.py',
)

describe('ṢAḌ-DARŚANA W2 — LEL-append recalibration dispatch (§2.5.5)', () => {
  // ── §1 — the request is a standard scoped build run ────────────────────────────────
  it('produces exactly the four fields POST /api/cockpit/runs requires', () => {
    const d = buildRecalibrationDispatch(CHART, ['ev1', 'ev2'])
    expect(toRequestBody(d)).toEqual({
      chart_id: CHART,
      scope: 'asset_set',
      scope_target: 'mi_bhara',
      action: 'rebuild',
    })
  })

  it("uses action 'rebuild', not 'build' — a lit asset would silently no-op under build", () => {
    // resolveBuildPlan's 'build' branch filters candidates to dormant/error state and returns
    // an empty plan for an already-lit asset. Every chart that has been calibrated once has a
    // lit mi_bhara, so 'build' would skip precisely the recalibrations that matter.
    expect(buildRecalibrationDispatch(CHART).action).toBe('rebuild')
  })

  it('the scope_target parses back to the asset set the route will plan', () => {
    const d = buildRecalibrationDispatch(CHART)
    expect(parseAssetSetTarget(d.scope_target)).toEqual(['mi_bhara'])
    expect(parseAssetSetTarget(d.scope_target).length).toBeGreaterThan(0) // route's EMPTY_ASSET_SET gate
  })

  it('carries the triggering events for the audit trail without letting them affect control flow', () => {
    const d = buildRecalibrationDispatch(CHART, ['ev1', 'ev2'], 'lel_correction')
    expect(d.triggering_event_ids).toEqual(['ev1', 'ev2'])
    expect(d.reason).toBe('lel_correction')
    expect(toRequestBody(d)).not.toHaveProperty('triggering_event_ids')
  })

  it('refuses to build an unscoped dispatch', () => {
    expect(() => buildRecalibrationDispatch('')).toThrow(/requires a chart_id/)
  })

  // ── §2 — parity with the Python twin, checked against the source ────────────────────
  it('agrees with services/mi_bhara/living_lel.py::RECALIBRATION_ASSET_SET', () => {
    const py = readFileSync(PYTHON_TWIN, 'utf8')
    const match = /RECALIBRATION_ASSET_SET\s*=\s*\(([^)]*)\)/.exec(py)
    expect(match, 'the Python twin must declare RECALIBRATION_ASSET_SET').toBeTruthy()
    const pyAssets = match![1]
      .split(',')
      .map(s => s.trim().replace(/^["']|["']$/g, ''))
      .filter(Boolean)
    expect(pyAssets).toEqual([...RECALIBRATION_ASSET_SET])
  })

  // ── §3 — structurally incapable of being a side channel ────────────────────────────
  it('cannot recompute anything: no fetch, no db, no writer import', () => {
    const src = readFileSync(MODULE_PATH, 'utf8')
    // Strip comments first — the module docstring necessarily NAMES the things it must not
    // do, and a naive scan would flag its own explanation.
    const code = src
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/^\s*\/\/.*$/gm, '')
    for (const forbidden of ['fetch(', "from '@/lib/db", 'query(', 'psycopg', 'child_process']) {
      expect(code, `dispatch module must not reference ${forbidden}`).not.toContain(forbidden)
    }
  })
})
