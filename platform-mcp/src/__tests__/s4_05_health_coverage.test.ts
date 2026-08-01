/**
 * S4-05 serving-side regression — `computeGocharaCoverage` must never let a
 * health question read an empty scan as an all-clear.
 *
 * ṢAḌ-DARŚANA registry item 9 (closes DP-4). The Python half of this suite is
 * `platform/python-sidecar/tests/l3/test_s4_05_health_adverse_class.py`, which
 * guards the GRAMMAR (the sweep now covers the ontology's health domain). This
 * file guards the SECOND door item 9 opens: once the grammar names health
 * classes, `domains_not_covered` would drop 'health' the instant G-1 wrote
 * resonance targets — even on a chart whose sweep has never run a single health
 * substep, leaving `kala_gochara_windows` empty for health while the tool now
 * claims the domain is covered. That is S4-05 exactly, one build cycle later.
 *
 * The fix: a class counts as covered only when BOTH axes hold for that chart —
 * resonance targets exist AND the sweep has committed at least one substep for
 * it (`build_substep_progress.substep_key` = `{event_class}:year:{n}`).
 *
 * Query provenance (`UAT_BATTERY_v1_0.md` §S4-05):
 *   "Is there a rough patch coming for my health in the near future?
 *    I'd rather know than not know."
 * Failure provenance (`UAT_DARPANA_REPORT_v1_0.md` §2): the answer said the
 * health side "comes back clean — no adverse window flagged across roughly the
 * next three years", from a scan structurally incapable of seeing health.
 *
 * `fetch` is mocked — no live PLATFORM_URL/DB required.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }
const CHART_ABHISEK = '482012f1-710e-4a25-994a-93821f5871aa'

/** The 13-value `brahma_event_ontology.domain` CHECK universe (migration 388). */
const DOMAIN_UNIVERSE = [
  'career', 'character', 'education', 'family', 'general', 'health', 'progeny',
  'relationship', 'residence', 'spirituality', 'transition', 'travel', 'wealth',
]

const DOMAIN_OF: Record<string, string> = {
  marriage: 'relationship',
  major_gain: 'wealth',
  career_advancement: 'career',
  illness_acute: 'health',
  chronic_onset: 'health',
  surgery: 'health',
}

/**
 * Routes the three queries `computeGocharaCoverage` fires, by SQL substring.
 * `targeted` = classes with gochara_resonance_map rows; `swept` = classes with
 * committed ka_gochara_sweep substeps.
 */
function mockDb(targeted: string[], swept: string[]) {
  mockFetch.mockImplementation(async (_url: string, init: { body: string }) => {
    const { sql } = JSON.parse(init.body) as { sql: string }
    let rows: Record<string, unknown>[] = []
    if (sql.includes('FROM gochara_resonance_map')) {
      rows = targeted.map((ec) => ({ event_class: ec, domain: DOMAIN_OF[ec] ?? null }))
    } else if (sql.includes('FROM brahma_event_ontology')) {
      rows = DOMAIN_UNIVERSE.map((d) => ({ domain: d }))
    } else if (sql.includes('FROM build_substep_progress')) {
      rows = [{ substeps_committed: swept.length * 101, swept_event_classes: swept }]
    }
    return { ok: true, status: 200, json: async () => ({ rows }), text: async () => JSON.stringify({ rows }) }
  })
}

async function coverageFor(targeted: string[], swept: string[]) {
  mockDb(targeted, swept)
  const { computeGocharaCoverage } = await import('../tools/retrieval/register_gochara_windows.js')
  return computeGocharaCoverage(CHART_ABHISEK, principal)
}

describe('S4-05 / DP-4 — gochara coverage attestation for the health domain', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('reproduces the pre-item-9 state: health is structurally dark, and says so', async () => {
    const legacy = ['career_advancement', 'major_gain', 'marriage']
    const { coverage, ok } = await coverageFor(legacy, legacy)
    expect(ok).toBe(true)
    expect(coverage.event_classes_covered).toEqual(legacy.sort())
    // This is the machine-readable form of the veto: the scan cannot see health.
    expect(coverage.domains_not_covered).toContain('health')
  })

  it('item 9 GREEN: with health classes targeted AND swept, health leaves the dark set', async () => {
    const all = ['career_advancement', 'chronic_onset', 'illness_acute', 'major_gain', 'marriage', 'surgery']
    const { coverage } = await coverageFor(all, all)
    expect(coverage.event_classes_covered).toEqual(all)
    expect(coverage.event_classes_targeted_not_swept).toEqual([])
    expect(coverage.domains_not_covered).not.toContain('health')
  })

  it('THE SECOND DOOR: health targets built but never swept must NOT read as covered', async () => {
    // The state every existing chart is in the moment item 9 merges and G-1
    // re-runs, before the (expensive) sweep column for the new classes exists.
    const all = ['career_advancement', 'chronic_onset', 'illness_acute', 'major_gain', 'marriage', 'surgery']
    const swept = ['career_advancement', 'major_gain', 'marriage']
    const { coverage } = await coverageFor(all, swept)

    expect(coverage.event_classes_covered).toEqual(swept.sort())
    expect(coverage.event_classes_targeted_not_swept).toEqual(['chronic_onset', 'illness_acute', 'surgery'])
    expect(coverage.domains_not_covered).toContain('health')
  })

  it('a partially-swept health class (one substep committed) does count as covered', async () => {
    const all = ['career_advancement', 'chronic_onset', 'illness_acute', 'major_gain', 'marriage', 'surgery']
    const swept = ['career_advancement', 'chronic_onset', 'illness_acute', 'major_gain', 'marriage', 'surgery']
    const { coverage } = await coverageFor(all, swept)
    expect(coverage.domains_not_covered).not.toContain('health')
    // Execution completeness stays a SEPARATE, honestly-reported axis — coverage
    // never implies the sweep finished.
    expect(coverage.sweep_completeness.substeps_committed).toBeGreaterThan(0)
    expect(coverage.sweep_completeness.note).toMatch(/Execution completeness ONLY/)
  })

  it('degrades honestly when coverage itself cannot be computed', async () => {
    mockFetch.mockImplementation(async () => ({
      ok: false, status: 500, json: async () => ({}), text: async () => 'boom',
    }))
    const { computeGocharaCoverage } = await import('../tools/retrieval/register_gochara_windows.js')
    const { coverage, ok } = await computeGocharaCoverage(CHART_ABHISEK, principal)
    expect(ok).toBe(false)
    expect(coverage.event_classes_covered).toEqual([])
    // Nothing is claimed as covered when nothing could be read.
    expect(coverage.domains_not_covered).toEqual([])
  })
})
