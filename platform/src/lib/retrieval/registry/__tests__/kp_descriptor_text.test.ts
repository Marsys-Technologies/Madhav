/**
 * kp_descriptor_text.test.ts: the LLM-visible descriptor text of every capability that can serve a
 * KP-frame read agrees with what the handlers do (Lahiri-primary combined batch, KP_FRAME_SWEEP.md).
 *
 * The rule the handlers apply (SS N-342 / N-358 / N-362): by KP doctrine (one frame) the six KP
 * categories, the dedicated KP cusp tool and the KP dasha system are read at krishnamurti and labelled
 * "KP frame (Krishnamurti ayanamsha)" whatever ayanamsha_id is passed; everything else is read at the
 * requested ayanamsha, the Lahiri primary on omission. This file pins the TEXT to that rule so a
 * descriptor cannot go back to "pass ayanamsha_id to select any ayanamsha" / "Omit for all".
 * Behaviour itself is pinned by get_karakas.kp_frame.test.ts, get_dashas_kp_frame.test.ts,
 * kp_categories_pin.test.ts and the other KP handler tests.
 */
import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { KP_FRAME_CATEGORIES } from '../kp_categories'
import { KP_FRAME_DESCRIPTOR_NOTE, KP_AWARE_AYANAMSHA_ID_TEXT, PRIMARY_AYANAMSHA_ID_INPUT_TEXT } from '../handler_ayanamsha'
import { KP_FRAME_LABEL } from '../../kp_frame'
import type { CapabilityDescriptor } from '../types'

function cap(name: string): CapabilityDescriptor {
  const c = getCatalog().find((x) => x.uri.endsWith(`/${name}`))
  expect(c, `capability ${name}`).toBeDefined()
  return c as CapabilityDescriptor
}

function ayanamshaText(c: CapabilityDescriptor): string {
  const prop = (c.input_schema as Record<string, { description?: string }>)['ayanamsha_id']
  expect(prop, `${c.name} declares ayanamsha_id`).toBeDefined()
  return String(prop?.description ?? '')
}

/** Readers that take a caller category list (or a KP system/domain) and so can reach a KP-frame category. */
const KP_REACHING_READERS = [
  'get_aspects', 'get_ashtakavarga', 'get_avasthas', 'get_bhava_bala', 'get_dignity', 'get_dispositors',
  'get_sensitive_points', 'get_positions', 'get_nakshatra', 'get_karakas', 'get_structural',
  'get_sade_sati', 'get_panchanga', 'get_strength', 'get_yoga_dosha',
] as const

/** Handlers that cannot reach a KP-frame category (no caller category list): the plain primary-ayanamsha text. */
const PRIMARY_TEXT_HANDLERS = [
  'get_argala', 'get_ayurdaya', 'get_condition_composite', 'get_divisionals', 'get_graha_yuddha', 'get_medical_indications',
  'get_prashna_lagna', 'get_sensitive_degrees', 'get_tajik', 'get_tara_chandra_bala', 'get_transit_anchors',
  'get_vastu_directions', 'get_vichara', 'get_yoga_firings', 'query_planet', 'query_cdlm_summary', 'query_cgm_motifs',
  'query_cgm_paths', 'query_chart_gestalt', 'query_discoveries', 'query_mechanisms', 'query_pratijna',
  'query_question_lenses', 'query_rm_chart_summary', 'query_rm_dasha_windowed_prescriptions',
  'query_rm_dosha_remedy_bundles', 'query_rm_pattern_remedies', 'query_rm_prescriptions', 'query_rm_resonances',
  'query_triangulation', 'traverse_chart_graph',
] as const

describe('ayanamsha_id input text follows the Lahiri-primary rule on every capability', () => {
  it('no registered capability says "Omit for all/unfiltered/default" about ayanamsha_id (live registry, no allowlist)', () => {
    const bad = getCatalog()
      .map((c) => ({ name: c.name, text: String(((c.input_schema as Record<string, { description?: string }> | undefined)?.['ayanamsha_id'])?.description ?? '') }))
      .filter((x) => /omit for (all|unfiltered|default)/i.test(x.text))
    expect(bad.map((b) => `${b.name}: ${b.text}`)).toEqual([])
  })

  it.each(PRIMARY_TEXT_HANDLERS)('%s: ayanamsha_id says omitted = Lahiri primary, "all" = explicit raw opt-out', (name) => {
    expect(ayanamshaText(cap(name))).toBe(PRIMARY_AYANAMSHA_ID_INPUT_TEXT)
  })

  it('the KP-aware text is the primary text plus the KP exception, nothing else', () => {
    expect(KP_AWARE_AYANAMSHA_ID_TEXT).toBe(PRIMARY_AYANAMSHA_ID_INPUT_TEXT + ' ' + KP_FRAME_DESCRIPTOR_NOTE)
  })

  it('descriptions no longer claim a default call returns every ayanamsha', () => {
    expect(cap('get_transit_anchors').description).toMatch(/a default call returns the 9 Lahiri rows/)
    expect(cap('get_ayurdaya').description).not.toMatch(/omit\s+for all 5/i)
    expect(cap('query_cdlm_summary').description).toMatch(/a default call serves the Lahiri primary/)
    expect(cap('query_chart_gestalt').description).toMatch(/a default call serves the Lahiri primary/)
  })
})

describe('KP descriptor text follows the one-frame rule', () => {
  it('the shared note names exactly the KP-frame categories, the krishnamurti id and the frame label', () => {
    for (const category of KP_FRAME_CATEGORIES) expect(KP_FRAME_DESCRIPTOR_NOTE).toContain(category)
    expect(KP_FRAME_DESCRIPTOR_NOTE).toContain('krishnamurti')
    expect(KP_FRAME_DESCRIPTOR_NOTE).toContain(KP_FRAME_LABEL)
  })

  it.each(KP_REACHING_READERS)('%s: ayanamsha_id says omitted = Lahiri primary and carries the KP exception (no "Omit for all")', (name) => {
    const text = ayanamshaText(cap(name))
    expect(text).toBe(KP_AWARE_AYANAMSHA_ID_TEXT)
    expect(text).toMatch(/Omitted = lahiri_chitrapaksha/)
    expect(text).not.toMatch(/omit for (all|unfiltered|default)/i)
  })

  it('chart_facts_query: ayanamsha_id and the description carry the KP exception, not "single ayanamsha"', () => {
    const c = cap('chart_facts_query')
    expect(ayanamshaText(c)).toContain(KP_FRAME_DESCRIPTOR_NOTE)
    expect(c.description).toContain(KP_FRAME_DESCRIPTOR_NOTE)
    expect(c.description).not.toMatch(/single ayanamsha/i)
  })

  it('get_kp_cusps: always krishnamurti; the id is accepted but NOT applied (no "select any of the 5")', () => {
    const c = cap('get_kp_cusps')
    expect(c.description).toMatch(/ALWAYS reads the\s+Krishnamurti ayanamsha/)
    expect(c.description).toContain(KP_FRAME_LABEL)
    expect(c.description).not.toMatch(/select any of the 5/i)
    expect(c.description).not.toMatch(/Defaults to the KP-canonical/i)
    expect(ayanamshaText(c)).toMatch(/NOT applied/)
    expect(ayanamshaText(c)).not.toMatch(/Others: lahiri_chitrapaksha/)
  })

  it('get_dashas: system=vimshottari_kp is read in the KP frame at krishnamurti, named in the description, ayanamsha_id and system facet', () => {
    const c = cap('get_dashas')
    expect(c.description).toMatch(/system="vimshottari_kp"[^.]*always read at krishnamurti/)
    expect(c.description).toContain(KP_FRAME_LABEL)
    expect(ayanamshaText(c)).toMatch(/system=vimshottari_kp\) is always read at krishnamurti/)
    const system = (c.input_schema as Record<string, { description?: string }>)['system']?.description ?? ''
    expect(system).toMatch(/vimshottari_kp/)
  })

  it('get_karakas / get_nakshatra: the description states which categories are KP-frame', () => {
    for (const name of ['get_karakas', 'get_nakshatra']) {
      const c = cap(name)
      expect(c.description, name).toMatch(/always read at krishnamurti/)
      expect(c.description, name).toContain(KP_FRAME_LABEL)
    }
  })

  it('get_prashna_lagna: does not claim a kp_sub_lord for kp_249 (ga_prashna never computes one: the column is always NULL)', () => {
    const c = cap('get_prashna_lagna')
    expect(c.description).not.toMatch(/kp_sub_lord \(for kp_249\)/)
    expect(c.description).toMatch(/kp_sub_lord\s+column that is ALWAYS NULL today/)
    expect(c.description).toMatch(/never computes a KP sub-lord/)
    expect(c.description).toMatch(/ordinary ascendant/)
  })
})
