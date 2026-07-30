/**
 * surface_gateway_gestalt_shape.test.ts — SAMĀPTI B-N8-FIX serving-layer consequence
 * ==================================================================================
 * DVĀRAPĀLA Ruling 76. B-N8-FIX stopped `bo_chart_gestalt.py` storing a verdict:
 * `domain_verdict_map_jsonb` rows now carry a `signal_id` POINTER plus whole-domain
 * `evidence` counts and a `verdict_note` — and NO `verdict_class` / `confidence`.
 *
 * `RegistrySurfaceGateway.gestalt()` used to set `signal_id` unconditionally, which kept
 * `instrument.ts`'s `if (verdict && verdict.signal_id)` guard passing on the new shape and
 * rendered a fabricated "…is unknown (confidence 0)" verdict. This test pins BOTH shapes:
 *
 *   (1) OLD/full shape (verdict_class present) → normal verdict prose + grounded ledger.
 *   (2) NEW evidence-only shape (no verdict_class) → the pre-existing honest-empty branch
 *       ("no pre-computed gestalt verdict was available … disclosed, not fabricated"),
 *       and NEVER the words "unknown (confidence 0)".
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { registerCapability } from '../../registry/index'
import type { CapabilityDescriptor } from '../../registry/types'
import { RegistrySurfaceGateway, type SurfaceGateway, type FamilyDrill, type DispositorPath, type TensionResult } from '../surface_gateway'
import { composeLargeN } from '../instrument'
import type { GestaltOrientation } from '../surface_gateway'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const GESTALT_URI = 'marsys://tool/L2/query_chart_gestalt'
const SIGNAL = 'sig-gestalt-pointer-1'

/** Register a stub gestalt capability returning one row with the given verdict map. */
function registerGestaltRow(domainVerdictMap: Record<string, unknown>): void {
  registerCapability({
    uri: GESTALT_URI,
    name: 'query_chart_gestalt',
    handler: async () => ({
      content: {
        rows: [{
          domain_verdict_map_jsonb: domainVerdictMap,
          central_question_jsonb: { note: 'stub' },
        }],
      },
    }),
  } as unknown as CapabilityDescriptor)
}

/** The post-fix (evidence-only) row shape emitted by bo_chart_gestalt.py after B-N8-FIX. */
const EVIDENCE_ONLY_ROW = {
  signal_id: SIGNAL,
  evidence: {
    signal_count: 768,
    benefic_count: 136,
    malefic_count: 632,
    mixed_count: 0,
    neutral_count: 0,
    major_tier_count: 41,
    top_signal_valence: 'benefic',
    top_signal_signature_tier: 'chart_defining',
    top_signal_salience: 9.1,
  },
  verdict_note: 'no verdict stored — this writer carries pointers and deterministic evidence only',
}

/** The pre-fix (full) row shape — must keep working unchanged. */
const FULL_VERDICT_ROW = {
  signal_id: SIGNAL,
  verdict_class: 'strong_challenge',
  confidence: 0.77,
}

/** Gateway that delegates gestalt to the real RegistrySurfaceGateway; other stages stubbed thin. */
class GestaltOnlyGateway implements SurfaceGateway {
  private real = new RegistrySurfaceGateway()
  gestalt(chartId: string, aya: string): Promise<GestaltOrientation> {
    return this.real.gestalt(chartId, aya)
  }
  async familyDrill(): Promise<FamilyDrill> {
    return { exemplars: [], total_in_family: 0, linkages: [] }
  }
  async dispositorPaths(): Promise<DispositorPath[]> {
    return []
  }
  async tension(): Promise<TensionResult> {
    return { contradiction_count: 0, contradictions: [], note: '' }
  }
}

function orientationSection(answer: { narrative: Array<{ heading: string; body: string; ledger: unknown[] }> }) {
  return answer.narrative.find(s => s.heading.startsWith('Orientation'))!
}

describe('RegistrySurfaceGateway.gestalt — verdict_map shape (Ruling 76)', () => {
  beforeEach(() => {
    // Each case re-registers the stub (registry is idempotent per URI).
  })

  it('OLD shape (verdict_class present) keeps the signal_id pointer', async () => {
    registerGestaltRow({ relationship: FULL_VERDICT_ROW })
    const o = await new RegistrySurfaceGateway().gestalt(CHART, 'lahiri_chitrapaksha')
    expect(o.found).toBe(true)
    expect(o.verdict_map['relationship']).toEqual({
      signal_id: SIGNAL,
      confidence: 0.77,
      verdict_class: 'strong_challenge',
    })
  })

  it('NEW evidence-only shape (no verdict_class) empties signal_id', async () => {
    registerGestaltRow({ relationship: EVIDENCE_ONLY_ROW })
    const o = await new RegistrySurfaceGateway().gestalt(CHART, 'lahiri_chitrapaksha')
    expect(o.found).toBe(true)
    // pointer suppressed so instrument.ts's `verdict.signal_id` guard falls through
    expect(o.verdict_map['relationship'].signal_id).toBe('')
    expect(o.verdict_map['relationship'].verdict_class).toBe('unknown')
  })
})

describe('instrument narrative — orientation branch selection (Ruling 76)', () => {
  const QUESTION = 'Map the whole marriage universe for this native'

  it('case 1: row WITH verdict_class → normal verdict prose + grounded ledger', async () => {
    registerGestaltRow({ relationship: FULL_VERDICT_ROW })
    const answer = await composeLargeN({ chart_id: CHART, question: QUESTION }, new GestaltOnlyGateway())
    const orient = orientationSection(answer)
    expect(orient.body).toContain('primary domain "relationship" is strong_challenge (confidence 0.77)')
    expect(orient.body).not.toMatch(/not fabricated/)
    // the claim is grounded in the gestalt pointer
    expect(answer.derivation_ledger.some(e => e.signal_ids.includes(SIGNAL))).toBe(true)
  })

  it('case 2: row WITHOUT verdict_class → honest-empty prose, never "unknown (confidence 0)"', async () => {
    registerGestaltRow({ relationship: EVIDENCE_ONLY_ROW })
    const answer = await composeLargeN({ chart_id: CHART, question: QUESTION }, new GestaltOnlyGateway())
    const orient = orientationSection(answer)
    expect(orient.body).toContain('no pre-computed gestalt verdict was available')
    expect(orient.body).toContain('disclosed, not fabricated')
    // the regression this fix exists to prevent
    expect(orient.body).not.toMatch(/unknown/)
    expect(orient.body).not.toMatch(/confidence 0/)
    // and nothing is grounded in a pointer that carries no verdict
    expect(orient.ledger).toHaveLength(0)
    expect(answer.derivation_ledger.some(e => e.signal_ids.includes(SIGNAL))).toBe(false)
  })
})
