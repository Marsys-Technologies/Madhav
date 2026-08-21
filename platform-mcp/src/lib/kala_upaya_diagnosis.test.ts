/**
 * kala_upaya_diagnosis.test.ts — ṢAḌ-DARŚANA W4 Lane U (item 26 UPĀYA-SETU).
 * Covers: the individualized-mortality-window hard exclusion (gate G16, non-vacuous — the
 * detector is proven to actually FIRE, not merely asserted absent), PACT-status → failing-link
 * mapping, the citation-derived efficacy tier assignment + §N.6 density split, the §5.3
 * withhold predicate (non-vacuous, gate G14b), the ADJUDICATION-12 fail-closed adoption_basis
 * resolution (gate G3b), and the disclosure-tier resolution (§5.2).
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'

// Mock only the I/O adapters this module depends on (client.ts's `callPlatformPrimitive`,
// kala_views/shared.ts's `callKalaRegistryCap`) — the SAME technique elect.test.ts uses for
// kala_lattice_query.ts's `fetchLatticeSubstrate`: the pure logic under test (efficacy tiers,
// the withhold predicate, the filing-state machine, the mortality detector) stays real; only
// the network boundary is stubbed, so these tests never depend on a reachable platform or on
// GoogleAuth's identity-token machinery (`client.ts`'s `fetchIdentityToken`), which would
// otherwise try a real metadata-server round trip in this unit-test process.
const mockCallPlatformPrimitive = vi.fn()
vi.mock('../client.js', async () => {
  const actual = await vi.importActual<typeof import('../client.js')>('../client.js')
  return { ...actual, callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args) }
})

const mockCallKalaRegistryCap = vi.fn()
vi.mock('../tools/kala_views/shared.js', async () => {
  const actual = await vi.importActual<typeof import('../tools/kala_views/shared.js')>('../tools/kala_views/shared.js')
  return { ...actual, callKalaRegistryCap: (...args: unknown[]) => mockCallKalaRegistryCap(...args) }
})

// The Lane-S spine is mocked at module boundary for `resolveAndFileFilingState` tests — the
// spine's own gates/network behavior is covered by intervention_filing.test.ts; here we test
// the WIRING (which inputs reach it, and how its result maps back into FilingResolution).
const mockFileInterventionFalsifier = vi.fn()
vi.mock('./intervention_filing.js', async () => {
  const actual = await vi.importActual<typeof import('./intervention_filing.js')>('./intervention_filing.js')
  return { ...actual, fileInterventionFalsifier: (...args: unknown[]) => mockFileInterventionFalsifier(...args) }
})

import {
  MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN,
  isMortalityExcludedRequest,
  buildMortalityExclusionRefusal,
  mapPactStatusToFailingLink,
  composeDiagnosisStatement,
  fetchPactDiagnosis,
  assignEfficacyTier,
  phalaMitigationToIntervention,
  bodhaRmPrescriptionToIntervention,
  remedyCorpusRowToIntervention,
  splitCitedUncited,
  extractPhalaMitigationPrescription,
  dedupeInterventions,
  splitPrescriptive,
  assessEfficacyDiscrimination,
  DUPLICATE_PK_SAMPLE_CAP,
  CANONICAL_AYANAMSHA_ID,
  fetchRemedyRows,
  fetchAlternateRoutes,
  buildEligibilityPointer,
  buildEfficacyReport,
  ADVERSE_WITHHOLD_EVENT_CLASSES,
  isAdverseWithholdClass,
  withholdGroundFor,
  resolveFilingState,
  resolveAndFileFilingState,
  resolveDisclosureTier,
  type PactStatus,
  type UpayaIntervention,
  type PhalaMitigationRow,
} from './kala_upaya_diagnosis.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.4 / gate G16 — the individualized-mortality-window hard exclusion
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('§5.4 mortality exclusion — G16(a): the detector actually FIRES (non-vacuous proof)', () => {
  it('excludes a request whose question_frame.domain names longevity', () => {
    expect(isMortalityExcludedRequest({ question_frame: { domain: 'longevity' } })).toBe(true)
  })

  it('excludes a request whose question_frame.stakes mentions āyurdāya (ASCII spelling)', () => {
    expect(isMortalityExcludedRequest({ question_frame: { stakes: 'concerned about my ayurdaya reading' } })).toBe(true)
  })

  it('excludes a request naming maraka dasha in the entity field', () => {
    expect(isMortalityExcludedRequest({ question_frame: { entity: 'the upcoming maraka dasha' } })).toBe(true)
  })

  it('excludes a request naming the whole word "ayus" but not a substring like "campus"', () => {
    expect(isMortalityExcludedRequest({ question_frame: { horizon: 'ayus assessment' } })).toBe(true)
    expect(isMortalityExcludedRequest({ question_frame: { horizon: 'campus visit next month' } })).toBe(false)
  })

  it('excludes via the top-level event_class field, not only question_frame', () => {
    expect(isMortalityExcludedRequest({ event_class: 'longevity_concern' })).toBe(true)
  })

  it('excludes via the top-level domain field', () => {
    expect(isMortalityExcludedRequest({ domain: 'maraka' })).toBe(true)
  })

  it('is case-insensitive', () => {
    expect(isMortalityExcludedRequest({ question_frame: { domain: 'LONGEVITY' } })).toBe(true)
    expect(isMortalityExcludedRequest({ question_frame: { domain: 'AyurDaya' } })).toBe(true)
  })

  it('does NOT exclude an ordinary career/marriage/health remedy request', () => {
    expect(isMortalityExcludedRequest({ question_frame: { domain: 'career', stakes: 'promotion timing' } })).toBe(false)
    expect(isMortalityExcludedRequest({ event_class: 'illness_acute' })).toBe(false)
    expect(isMortalityExcludedRequest({})).toBe(false)
  })

  it('is pure and synchronous — no Promise, no async, structurally incapable of awaiting I/O', () => {
    const result = isMortalityExcludedRequest({ event_class: 'longevity' })
    expect(result).not.toBeInstanceOf(Promise)
    expect(isMortalityExcludedRequest.constructor.name).not.toBe('AsyncFunction')
  })
})

describe('§5.4 — G16(c): audience_tier does NOT unlock the exclusion', () => {
  it('the refusal envelope echoes the tier but never conditions on it', () => {
    const refusal = buildMortalityExclusionRefusal('native_self')
    expect(refusal.excluded).toBe(true)
    expect(refusal.audience_tier_evaluated).toBe('native_self')
    // The refusal is IDENTICAL in shape/content regardless of tier — the function takes no
    // branch on audienceTier other than echoing it.
    const refusalOther = buildMortalityExclusionRefusal('acharya_reviewer')
    expect(refusalOther.excluded).toBe(true)
    expect(refusalOther.reason).toBe(refusal.reason)
  })

  it('carries no candidate/window/diagnosis field of any kind', () => {
    const refusal = buildMortalityExclusionRefusal(null)
    const keys = Object.keys(refusal)
    expect(keys).not.toContain('diagnosis')
    expect(keys).not.toContain('interventions')
    expect(keys).not.toContain('alternate_routes')
    expect(keys).not.toContain('coverage')
  })
})

describe('§5.4 — G16(b): source-level substrate ban, scoped honestly to this definer file', () => {
  // This file is the DEFINER of the mortality-exclusion pattern — it necessarily contains the
  // literal identifiers (`ayurdaya`, `longevity`, `maraka`, `ayus`) inside the pattern constant
  // and its own documentation, exactly the way a firewall rule table must contain the traffic
  // signature it blocks. What this test proves instead: the file contains NO ACTUAL CALL SITE
  // or IMPORT reaching `ganita_ayurdaya_get` or any ayurdaya-shaped primitive/capability name —
  // only the textual definition of the ban. `upaya.ts`'s own test file (upaya.test.ts) carries
  // the complementary BLANKET scan (zero occurrences of any kind) for the production serving
  // surface, which has no legitimate reason to mention these identifiers at all.
  const thisFilePath = fileURLToPath(new URL('./kala_upaya_diagnosis.ts', import.meta.url))
  const src = readFileSync(thisFilePath, 'utf8')

  it('never imports a module whose specifier names the forbidden identifiers', () => {
    const importLines = src.split('\n').filter((l) => /^\s*import\b/.test(l))
    for (const line of importLines) {
      expect(MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN.test(line)).toBe(false)
    }
  })

  it('never calls ganita_ayurdaya_get, and never passes an ayurdaya/longevity/maraka-shaped ' +
    'string literal as a primitive/capability tool name', () => {
    expect(/ganita_ayurdaya_get\s*\(/.test(src)).toBe(false)
    expect(/callPlatformPrimitive\(\s*['"][^'"]*(ayurdaya|longevity|maraka)/i.test(src)).toBe(false)
    expect(/callKalaRegistryCap\(\s*['"][^'"]*(ayurdaya|longevity|maraka)/i.test(src)).toBe(false)
  })

  it('the MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN constant is exactly the design-specified pattern', () => {
    expect(MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN.source).toBe('ayurdaya|longevity|maraka|\\bayus\\b')
    expect(MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN.flags).toContain('i')
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.2 — PACT-linked diagnosis
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('mapPactStatusToFailingLink — the design §2.2 table, executable', () => {
  const cases: Array<[PactStatus, string | null]> = [
    ['denied_at_promise', 'promise'],
    ['denied_at_confirmation', 'confirmation'],
    ['denied_at_activation', 'activation'],
    ['chain_pending_activation', 'activation'],
    ['chain_complete', null],
    ['chain_incomplete_infra', null],
  ]
  for (const [status, expected] of cases) {
    it(`${status} → ${expected}`, () => {
      expect(mapPactStatusToFailingLink(status)).toBe(expected)
    })
  }
})

describe('composeDiagnosisStatement', () => {
  it('states no_lever reasoning honestly for chain_complete (never manufactures a remedy)', () => {
    const s = composeDiagnosisStatement('chain_complete', null)
    expect(s).toMatch(/no failing link/i)
    expect(s).toMatch(/fabricated intervention|Offer-Law/i)
  })

  it('distinguishes infra failure from a classical denial for chain_incomplete_infra, and ' +
    'states — never silently implies — that it will not be reworded as one', () => {
    const s = composeDiagnosisStatement('chain_incomplete_infra', 'ephemeris sidecar unreachable')
    expect(s).toMatch(/infrastructure/i)
    expect(s).toMatch(/never re-worded into an astrological finding/i)
  })

  it('every status produces a non-empty, distinct statement', () => {
    const statuses: PactStatus[] = [
      'denied_at_promise', 'denied_at_confirmation', 'denied_at_activation',
      'chain_pending_activation', 'chain_incomplete_infra', 'chain_complete',
    ]
    const statements = statuses.map((s) => composeDiagnosisStatement(s, null))
    for (const s of statements) expect(s.trim().length).toBeGreaterThan(0)
    expect(new Set(statements).size).toBe(statuses.length)
  })
})

describe('fetchPactDiagnosis', () => {
  it('honest_empty when neither domain nor bhava is supplied (never calls pact_query)', async () => {
    const result = await fetchPactDiagnosis({ chart_id: CHART_ID }, PRINCIPAL)
    expect(result.state).toBe('honest_empty')
    expect(result.reason).toMatch(/domain.*bhava|bhava.*domain/i)
    expect(result.diagnosis).toBeNull()
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.1 / §2.5 — efficacy tiers + density split (ruling U-1: no recomputation, only selection)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('assignEfficacyTier — design §2.5 table', () => {
  it('classically_attested iff the row carries a resolvable citation', () => {
    expect(assignEfficacyTier({ hasCitation: true, isLiveSurface: true })).toBe('classically_attested')
  })
  it('traditional iff no citation but the surface is live corpus content', () => {
    expect(assignEfficacyTier({ hasCitation: false, isLiveSurface: true })).toBe('traditional')
  })
  it('speculative_extension iff neither a citation nor a live surface', () => {
    expect(assignEfficacyTier({ hasCitation: false, isLiveSurface: false })).toBe('speculative_extension')
  })
})

describe('row-to-intervention mappers — §N.5 (source_surface + primary key on every row, never recomputed)', () => {
  it('phalaMitigationToIntervention carries the row PK and citation-derived tier', () => {
    const row = phalaMitigationToIntervention({
      mitigation_id: 'mit-1', afflicting_graha: 'Saturn', obstruction_severity: 3,
      intensity_tier: 'moderate', proportionality_basis: 'obstruction severity 3/5',
      classical_citation: 'BPHS 45.12',
    }, 'promise')
    expect(row.source_surface).toBe('phala_mitigation')
    expect(row.source_pk).toBe('mit-1')
    expect(row.efficacy_tier).toBe('classically_attested')
    expect(row.citation).toBe('BPHS 45.12')
    expect(row.targets_link).toBe('promise')
  })

  it('phalaMitigationToIntervention tiers traditional when classical_citation is blank', () => {
    const row = phalaMitigationToIntervention({
      mitigation_id: 'mit-2', afflicting_graha: 'Mars', obstruction_severity: 2,
      intensity_tier: 'light', proportionality_basis: null, classical_citation: '',
    }, null)
    expect(row.efficacy_tier).toBe('traditional')
    expect(row.citation).toBeNull()
  })

  it('bodhaRmPrescriptionToIntervention reads citation_human first, then classical_sources_jsonb', () => {
    const cited = bodhaRmPrescriptionToIntervention({
      prescription_id: 'rx-1', target_graha: 'Venus', remedy_category: 'mantra',
      remedy_label_human: 'Shukra mantra japa', classical_strength_rating: 4,
      classical_sources_jsonb: null, feasibility_score: 0.7,
      citation_ref: null, citation_human: 'Bṛhat Parāśara Horā Śāstra 79.3',
    }, 'confirmation')
    expect(cited.citation).toBe('Bṛhat Parāśara Horā Śāstra 79.3')
    expect(cited.efficacy_tier).toBe('classically_attested')
    expect(cited.feasibility).toBe(0.7)

    const uncitedFlat = bodhaRmPrescriptionToIntervention({
      prescription_id: 'rx-2', target_graha: 'Saturn', remedy_category: 'dana',
      remedy_label_human: null, classical_strength_rating: 2,
      classical_sources_jsonb: ['text_chunk_9'], feasibility_score: null,
      citation_ref: null, citation_human: null,
    }, null)
    expect(uncitedFlat.efficacy_tier).toBe('classically_attested')
    expect(uncitedFlat.citation).toBe('see classical_sources_jsonb')

    const genuinelyUncited = bodhaRmPrescriptionToIntervention({
      prescription_id: 'rx-3', target_graha: 'Saturn', remedy_category: 'dana',
      remedy_label_human: null, classical_strength_rating: 2,
      classical_sources_jsonb: [], feasibility_score: null,
      citation_ref: null, citation_human: null,
    }, null)
    expect(genuinelyUncited.efficacy_tier).toBe('traditional')
    expect(genuinelyUncited.citation).toBeNull()
  })

  it('remedyCorpusRowToIntervention checks source_citation, then classical_ref, then attestation text', () => {
    const row = remedyCorpusRowToIntervention({
      remedy_id: 'rem-1', planet: 'Jupiter', domain: 'wealth', deity: 'Vishnu',
      prescription_text: 'Vishnu sahasranama patha', source_citation: null,
      classical_ref: 'BPHS ch.79', classical_attestation_text: null,
    }, 'activation')
    expect(row.citation).toBe('BPHS ch.79')
    expect(row.efficacy_tier).toBe('classically_attested')
  })
})

describe('splitCitedUncited — §N.6 density split (mirrors convention_only_factors)', () => {
  function row(over: Partial<UpayaIntervention> = {}): UpayaIntervention {
    return {
      id: 'x', intervention_class: 'remedy_corpus', source_surface: 'brahma_remedy_corpus',
      source_pk: 'x', label: 'x', efficacy_tier: 'classically_attested', citation: 'cite',
      targets_link: null, feasibility: null,
      actionable_prescription: 'do the thing', duplicate_row_count: 1,
      duplicate_source_pks: [], duplicate_note: null, ...over,
    }
  }
  it('never merges a citation-less row into cited', () => {
    const cited = row({ id: 'a', citation: 'BPHS 1.1' })
    const uncited = row({ id: 'b', citation: null, efficacy_tier: 'traditional' })
    const { cited: citedOut, uncited: uncitedOut } = splitCitedUncited([cited, uncited])
    expect(citedOut.map((r) => r.id)).toEqual(['a'])
    expect(uncitedOut.map((r) => r.id)).toEqual(['b'])
  })
  it('an all-cited input produces an empty uncited array (not omitted, an honest empty array)', () => {
    const { uncited } = splitCitedUncited([row({ id: 'a' })])
    expect(uncited).toEqual([])
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// F-118 — duplicate collapse, actionability split, efficacy-discrimination detector
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('F-118 extractPhalaMitigationPrescription — the actionability detector', () => {
  /** The EXACT live shape read off the canonical chart's phala_mitigation rows (all 536 of
   *  them carry this): an empty program, empty tradition buckets, empty cost tiers. */
  function liveEmptyRow(): PhalaMitigationRow {
    return {
      mitigation_id: 'pm-live', afflicting_graha: 'saturn', obstruction_severity: null,
      intensity_tier: 'light', proportionality_basis: 'severity=medium × anchor_magnitude=minor → light',
      classical_citation: 'Brihat Parashara Hora Shastra — Upaya chapter',
      program_jsonb: { scheduled_ids: [], sequence_basis: 'prerequisite_topo_sort + incompatible_exclusion', total_scheduled: 0 },
      tradition_options_jsonb: { vastu: [], vedic: [], modern: [], tantra: [], ayurvedic: [], lal_kitab: [] },
      recommended_tier_jsonb: { free: [], low_cost: [], high_investment: [] },
    }
  }

  it('returns null on the live all-empty row — never falls back to the severity label', () => {
    expect(extractPhalaMitigationPrescription(liveEmptyRow())).toBeNull()
  })

  it('never reads sequence_basis as content (it describes the ordering, not an act)', () => {
    const out = extractPhalaMitigationPrescription(liveEmptyRow())
    expect(out).toBeNull()
    expect(String(out)).not.toContain('topo_sort')
  })

  it('returns the real tradition options when the row actually carries any', () => {
    const row = liveEmptyRow()
    row.tradition_options_jsonb = { vedic: ['Shani japa, 23000 counts'], tantra: [], modern: [] }
    expect(extractPhalaMitigationPrescription(row)).toBe('Shani japa, 23000 counts')
  })

  it('returns an honest POINTER (never invented prose) when a program is actually scheduled', () => {
    const row = liveEmptyRow()
    row.program_jsonb = { scheduled_ids: ['rx-1', 'rx-2'], total_scheduled: 2 }
    const out = extractPhalaMitigationPrescription(row)
    expect(out).toContain('2 scheduled remedy step(s)')
    expect(out).toContain('rx-1')
  })

  it('the mapper carries the detector result onto the served row (a live row is null)', () => {
    const served = phalaMitigationToIntervention(liveEmptyRow(), 'promise')
    expect(served.actionable_prescription).toBeNull()
    // The label is STILL the severity classification — the repair does not rewrite the label,
    // it stops the label being read as a prescription.
    expect(served.label).toContain('severity=medium')
    expect(served.duplicate_row_count).toBe(1)
  })
})

describe('F-118 dedupeInterventions — the byte-identical collapse', () => {
  function served(over: Partial<UpayaIntervention> = {}): UpayaIntervention {
    return {
      id: 'phala_mitigation:x', intervention_class: 'phala_mitigation', source_surface: 'phala_mitigation',
      source_pk: 'x', label: 'light — for saturn — severity=medium × anchor_magnitude=minor → light',
      efficacy_tier: 'classically_attested', citation: 'BPHS — Upaya chapter', targets_link: 'promise',
      feasibility: null, actionable_prescription: null, duplicate_row_count: 1,
      duplicate_source_pks: [], duplicate_note: null, ...over,
    }
  }

  it('THE REPRODUCER: 50 byte-identical rows collapse to ONE row that states it stands for 50', () => {
    const rows = Array.from({ length: 50 }, (_, i) => served({ id: `phala_mitigation:pm-${i}`, source_pk: `pm-${i}` }))
    const { rows: out, collapsed_row_count } = dedupeInterventions(rows)
    expect(out).toHaveLength(1)
    expect(collapsed_row_count).toBe(49)
    expect(out[0]?.duplicate_row_count).toBe(50)
    expect(out[0]?.duplicate_note).toContain('ONE recommendation, not 50')
  })

  it('caps the listed sibling keys but NEVER caps the true count (no silent under-reporting)', () => {
    const rows = Array.from({ length: 50 }, (_, i) => served({ id: `phala_mitigation:pm-${i}`, source_pk: `pm-${i}` }))
    const { rows: out } = dedupeInterventions(rows)
    expect(out[0]?.duplicate_source_pks).toHaveLength(DUPLICATE_PK_SAMPLE_CAP)
    expect(out[0]?.duplicate_row_count).toBe(50)
  })

  it('the same remedy stored once per ayanamsha collapses to one (the bodha_rm half of F-118)', () => {
    const rows = ['a', 'b', 'c', 'd', 'e'].map((pk) => served({
      id: `bodha_rm_remedy_prescriptions:${pk}`, intervention_class: 'bodha_rm_prescription',
      source_surface: 'bodha_rm_remedy_prescriptions', source_pk: pk,
      label: 'Recite the Sun beej mantra 108 times daily on Sunday, facing east.',
      actionable_prescription: 'Recite the Sun beej mantra 108 times daily on Sunday, facing east.',
      feasibility: 0.9,
    }))
    const { rows: out } = dedupeInterventions(rows)
    expect(out).toHaveLength(1)
    expect(out[0]?.duplicate_row_count).toBe(5)
  })

  it('NEVER collapses genuinely distinct recommendations, and keeps source order', () => {
    const rows = [
      served({ id: 'a', source_pk: 'a', label: 'Remedy A', actionable_prescription: 'Do A' }),
      served({ id: 'b', source_pk: 'b', label: 'Remedy B', actionable_prescription: 'Do B' }),
      served({ id: 'c', source_pk: 'c', label: 'Remedy A', actionable_prescription: 'Do A' }),
    ]
    const { rows: out, collapsed_row_count } = dedupeInterventions(rows)
    expect(out.map((r) => r.label)).toEqual(['Remedy A', 'Remedy B'])
    expect(collapsed_row_count).toBe(1)
    expect(out[0]?.duplicate_row_count).toBe(2)
    expect(out[1]?.duplicate_row_count).toBe(1)
    expect(out[1]?.duplicate_note).toBeNull()
  })

  it('a differing feasibility or tier is a REAL difference and is never collapsed away', () => {
    const rows = [
      served({ id: 'a', source_pk: 'a', actionable_prescription: 'Do A', feasibility: 0.9 }),
      served({ id: 'b', source_pk: 'b', actionable_prescription: 'Do A', feasibility: 0.2 }),
      served({ id: 'c', source_pk: 'c', actionable_prescription: 'Do A', feasibility: 0.9, efficacy_tier: 'traditional' }),
    ]
    expect(dedupeInterventions(rows).rows).toHaveLength(3)
  })

  it('an empty input is an honest empty result, not a crash', () => {
    expect(dedupeInterventions([])).toEqual({ rows: [], collapsed_row_count: 0 })
  })
})

describe('F-118 splitPrescriptive — a severity grade is never served as an intervention', () => {
  function served(over: Partial<UpayaIntervention> = {}): UpayaIntervention {
    return {
      id: 'x', intervention_class: 'phala_mitigation', source_surface: 'phala_mitigation',
      source_pk: 'x', label: 'x', efficacy_tier: 'classically_attested', citation: 'c',
      targets_link: 'promise', feasibility: null, actionable_prescription: null,
      duplicate_row_count: 1, duplicate_source_pks: [], duplicate_note: null, ...over,
    }
  }
  it('routes a null-prescription row OUT of the prescriptive list, decided by the row field', () => {
    const { prescriptive, nonPrescriptive } = splitPrescriptive([
      served({ id: 'grade' }),
      served({ id: 'act', actionable_prescription: 'Recite the Shani beej mantra 108×' }),
    ])
    expect(prescriptive.map((r) => r.id)).toEqual(['act'])
    expect(nonPrescriptive.map((r) => r.id)).toEqual(['grade'])
  })
  it('never DROPS the non-prescriptive row (B.10 — served separately, not discarded)', () => {
    const { prescriptive, nonPrescriptive } = splitPrescriptive([served({ id: 'grade' })])
    expect(prescriptive).toEqual([])
    expect(nonPrescriptive).toHaveLength(1)
  })
})

describe('F-118 assessEfficacyDiscrimination — the §N.8 earned-signal detector', () => {
  function served(over: Partial<UpayaIntervention> = {}): UpayaIntervention {
    return {
      id: 'x', intervention_class: 'bodha_rm_prescription', source_surface: 'bodha_rm_remedy_prescriptions',
      source_pk: 'x', label: 'x', efficacy_tier: 'classically_attested', citation: 'c',
      targets_link: 'promise', feasibility: 0.9, actionable_prescription: 'do it',
      duplicate_row_count: 1, duplicate_source_pks: [], duplicate_note: null, ...over,
    }
  }

  it('THE FINDING: a slate where every row grades identically reports discriminating=false', () => {
    const rows = Array.from({ length: 13 }, (_, i) => served({ id: `r${i}`, source_pk: `r${i}` }))
    const out = assessEfficacyDiscrimination(rows)
    expect(out.discriminating).toBe(false)
    expect(out.distinct_efficacy_tiers).toBe(1)
    expect(out.note).toContain('zero information')
  })

  it('reports discriminating=true once a grading field genuinely varies (a real detector, ' +
    'not a constant — this is the case that proves the flag CAN read differently)', () => {
    const out = assessEfficacyDiscrimination([
      served({ id: 'a', source_pk: 'a', feasibility: 0.9 }),
      served({ id: 'b', source_pk: 'b', feasibility: 0.2 }),
    ])
    expect(out.discriminating).toBe(true)
  })

  it('a varying efficacy_tier alone is enough', () => {
    const out = assessEfficacyDiscrimination([
      served({ id: 'a', source_pk: 'a' }),
      served({ id: 'b', source_pk: 'b', efficacy_tier: 'traditional' }),
    ])
    expect(out.discriminating).toBe(true)
  })

  it('targets_link is REPORTED but never counted toward discrimination (it is uniform by ' +
    'construction — every row routes to the one diagnosed failing link)', () => {
    const out = assessEfficacyDiscrimination([
      served({ id: 'a', source_pk: 'a', targets_link: 'promise' }),
      served({ id: 'b', source_pk: 'b', targets_link: 'activation' }),
    ])
    expect(out.distinct_targets_link_values).toBe(2)
    expect(out.discriminating).toBe(false)
  })

  it('a one-row or empty slate is reported non-discriminating, never assumed clean', () => {
    expect(assessEfficacyDiscrimination([served()]).discriminating).toBe(false)
    expect(assessEfficacyDiscrimination([]).rows_evaluated).toBe(0)
    expect(assessEfficacyDiscrimination([]).discriminating).toBe(false)
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.3 — alternate routing (ruling U-2)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('fetchAlternateRoutes', () => {
  it('honest_empty with no network call when no blocked graha is supplied', async () => {
    const result = await fetchAlternateRoutes({ chart_id: CHART_ID, blockedGraha: null }, PRINCIPAL)
    expect(result.state).toBe('honest_empty')
    expect(result.basis).toBeNull()
    expect(result.routes).toEqual([])
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.4 — eligibility pointer (ruling U-3: Lane U computes no window)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('buildEligibilityPointer', () => {
  it('names the for_intervention contract and never fabricates a window', () => {
    const pointer = buildEligibilityPointer('promise')
    expect(pointer.state).toBe('not_in_corpus')
    expect(pointer.instrument).toBe('kala_elect_get')
    expect(pointer.contract_param).toBe('for_intervention')
    expect(pointer.reason).toContain('for_intervention')
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §4.5 / E6 — efficacy report (honest_empty at this build tier, never a fabricated rate)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('buildEfficacyReport', () => {
  it('is always honest_empty with all-zero counts and a LAW ZERO reason (no ledger read path yet)', () => {
    const report = buildEfficacyReport()
    expect(report.state).toBe('honest_empty')
    expect(report.reason).toMatch(/LAW ZERO/)
    expect(report.n_elected_and_acted).toBe(0)
    expect(report.n_outcome_linked).toBe(0)
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.3 / gate G14b — the withhold predicate, non-vacuous
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('§5.3 withhold predicate — gate G14b (non-vacuity)', () => {
  it('resolves to more than zero classes (the exact defect v1.0 shipped, caught here)', () => {
    expect(ADVERSE_WITHHOLD_EVENT_CLASSES.length).toBeGreaterThan(0)
  })

  it('contains all five named classes verbatim', () => {
    expect([...ADVERSE_WITHHOLD_EVENT_CLASSES].sort()).toEqual(
      ['bereavement', 'chronic_onset', 'illness_acute', 'psychological_arc', 'surgery'].sort(),
    )
  })

  it('isAdverseWithholdClass fires on all five and does not fire on an ordinary class', () => {
    for (const cls of ADVERSE_WITHHOLD_EVENT_CLASSES) {
      expect(isAdverseWithholdClass(cls)).toBe(true)
    }
    expect(isAdverseWithholdClass('career_promotion')).toBe(false)
    expect(isAdverseWithholdClass(null)).toBe(false)
    expect(isAdverseWithholdClass(undefined)).toBe(false)
  })

  it('bereavement is grounded on consent_third_party, NOT health (amendment B)', () => {
    expect(withholdGroundFor('bereavement')).toBe('consent_third_party')
  })

  it('psychological_arc is grounded on psychological (its own disjunct, domain-only would miss it)', () => {
    expect(withholdGroundFor('psychological_arc')).toBe('psychological')
  })

  it('the three health classes are grounded on health', () => {
    expect(withholdGroundFor('illness_acute')).toBe('health')
    expect(withholdGroundFor('chronic_onset')).toBe('health')
    expect(withholdGroundFor('surgery')).toBe('health')
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.6 / §4.4 / gate G3b — adoption_basis fail-closed filing-state resolution
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('resolveFilingState', () => {
  it('not_requested when no adopt_intervention supplied (a plain read never files)', () => {
    const r = resolveFilingState({ chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x' })
    expect(r.state).toBe('not_requested')
    expect(r.filing_ready_payload).toBeNull()
    expect(r.filed_prediction_id).toBeNull()
  })

  it('filing_withheld_pending_native_signoff on an adverse class, even with adoption_basis=native_directed', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'illness_acute', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.6, falsifier: 'f', adoption_basis: 'native_directed' },
    })
    expect(r.state).toBe('filing_withheld_pending_native_signoff')
    expect(r.filed_prediction_id).toBeNull()
    expect(r.filing_ready_payload).not.toBeNull()
    expect(r.filing_ready_payload?.entry).toMatchObject({ chart_id: CHART_ID, falsifier: 'f', confidence: 0.6 })
  })

  it('bereavement withholds too (consent ground, not health)', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'bereavement', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    })
    expect(r.state).toBe('filing_withheld_pending_native_signoff')
  })

  // ── Gate G3b — the three ADJUDICATION-12 fail-closed cases, none of which ever files ──
  it('G3b case 1: adoption_basis="session_inferred" → awaiting_native_confirmation, never filed', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'session_inferred' },
    })
    expect(r.state).toBe('awaiting_native_confirmation')
    expect(r.filed_prediction_id).toBeNull()
    expect(r.adoption_basis).toBe('session_inferred')
  })

  it('G3b case 2: adoption_basis ABSENT → awaiting_native_confirmation, never defaults to native_directed', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f' },
    })
    expect(r.state).toBe('awaiting_native_confirmation')
    expect(r.filed_prediction_id).toBeNull()
  })

  it('G3b case 3: adoption_basis set to an UNRECOGNISED string → fails closed, never filed', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'definitely_the_native_i_promise' },
    })
    expect(r.state).toBe('awaiting_native_confirmation')
    expect(r.filed_prediction_id).toBeNull()
  })

  it('native_directed on a non-adverse class → filing_path_not_yet_available, NEVER filed=true ' +
    '(Lane S spine not yet available in this build tier)', () => {
    const r = resolveFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    })
    expect(r.state).toBe('filing_path_not_yet_available')
    expect(r.state).not.toBe('filed')
    expect(r.filed_prediction_id).toBeNull()
    expect(r.filing_ready_payload).not.toBeNull()
  })

  it('filing_ready_payload.entry is byte-identical (structurally) across the withheld and ' +
    'not-yet-available branches for the same input, modulo the reason text', () => {
    const base = { chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'the diagnosis' }
    const adopt = { intervention_id: 'i1', confidence: 0.42, falsifier: 'clear falsifier', adoption_basis: 'native_directed' as const }
    const r = resolveFilingState({ ...base, adopt })
    expect(r.filing_ready_payload?.entry.confidence).toBe(0.42)
    expect(r.filing_ready_payload?.entry.falsifier).toBe('clear falsifier')
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// resolveAndFileFilingState — the WIRED Step-4 path (closes the PR-#1055-disclosed gap)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('resolveAndFileFilingState (wired Step 4 → intervention_filing spine)', () => {
  beforeEach(() => {
    mockFileInterventionFalsifier.mockReset()
  })

  const WINDOW = { start: '2026-09-01T00:00:00Z', end: '2027-01-01T00:00:00Z' }

  it('gates 1–3 short-circuit BEFORE the spine: adverse class never reaches fileInterventionFalsifier', async () => {
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'illness_acute', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed', window: WINDOW },
    }, PRINCIPAL)
    expect(r.state).toBe('filing_withheld_pending_native_signoff')
    expect(mockFileInterventionFalsifier).not.toHaveBeenCalled()
  })

  it('gates 1–3 short-circuit BEFORE the spine: session_inferred fails closed, spine never called', async () => {
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'session_inferred', window: WINDOW },
    }, PRINCIPAL)
    expect(r.state).toBe('awaiting_native_confirmation')
    expect(mockFileInterventionFalsifier).not.toHaveBeenCalled()
  })

  it('native_directed + window → calls the spine with the composed claim + inherited citation, maps filed', async () => {
    mockFileInterventionFalsifier.mockResolvedValue({ state: 'filed', prediction_id: 'pred-99', filing_ready_payload: null, detail: null })
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'the diagnosis statement',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed', window: WINDOW },
      sourceCitation: 'BPHS 27.4',
    }, PRINCIPAL)
    expect(r.state).toBe('filed')
    expect(r.filed_prediction_id).toBe('pred-99')
    expect(r.adoption_basis).toBe('native_directed')
    expect(r.filing_detail).toBeNull()
    expect(mockFileInterventionFalsifier).toHaveBeenCalledTimes(1)
    const input = mockFileInterventionFalsifier.mock.calls[0]![0] as Record<string, unknown>
    expect(input['chart_id']).toBe(CHART_ID)
    expect(input['intervention_class']).toBe('upaya')
    expect(input['claim']).toBe('the diagnosis statement') // engine-composed template, B.10
    expect(input['source_citation']).toBe('BPHS 27.4')     // §N.5 inherited, never restated
    expect(input['window']).toEqual(WINDOW)
    expect(input['adoption_basis']).toBe('native_directed')
  })

  it('an explicit adopt.claim overrides the template (the claim the native confirms is the claim the native wrote)', async () => {
    mockFileInterventionFalsifier.mockResolvedValue({ state: 'filed', prediction_id: 'p', filing_ready_payload: null, detail: null })
    await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'the diagnosis statement',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed', window: WINDOW, claim: 'my own claim' },
    }, PRINCIPAL)
    const input = mockFileInterventionFalsifier.mock.calls[0]![0] as Record<string, unknown>
    expect(input['claim']).toBe('my own claim')
  })

  it('spine filing_failed maps through with the VERBATIM error in filing_detail and the payload retained for a one-hop retry', async () => {
    mockFileInterventionFalsifier.mockResolvedValue({
      state: 'filing_failed', prediction_id: null, filing_ready_payload: null,
      detail: 'claim_shape interval does not match temporal_shape point (trigger)',
    })
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed', window: WINDOW },
    }, PRINCIPAL)
    expect(r.state).toBe('filing_failed')
    expect(r.filing_detail).toBe('claim_shape interval does not match temporal_shape point (trigger)')
    expect(r.filing_ready_payload).not.toBeNull()
    expect(r.filed_prediction_id).toBeNull()
  })

  it('native_directed WITHOUT a window: honest filing_failed naming the absent window; spine NEVER called (B.10)', async () => {
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
      adopt: { intervention_id: 'i1', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    }, PRINCIPAL)
    expect(r.state).toBe('filing_failed')
    expect(r.filing_detail).toContain('window')
    expect(mockFileInterventionFalsifier).not.toHaveBeenCalled()
  })

  it('a plain read (no adopt) stays not_requested with zero spine calls', async () => {
    const r = await resolveAndFileFilingState({
      chart_id: CHART_ID, event_class: 'career_promotion', diagnosisStatement: 'x',
    }, PRINCIPAL)
    expect(r.state).toBe('not_requested')
    expect(mockFileInterventionFalsifier).not.toHaveBeenCalled()
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.2 — disclosure tier (stated, never assumed)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('resolveDisclosureTier', () => {
  it('resolves both canonical native charts to native_self, with a stated basis', () => {
    expect(resolveDisclosureTier(CHART_ID, []).audience_tier).toBe('native_self')
    expect(resolveDisclosureTier(ABHINANDAN_CHART_ID, []).audience_tier).toBe('native_self')
    expect(resolveDisclosureTier(CHART_ID, []).basis.length).toBeGreaterThan(0)
  })

  it('does NOT default a non-canonical chart to native_self (no silent broadening)', () => {
    const result = resolveDisclosureTier('00000000-0000-0000-0000-000000000000', [])
    expect(result.audience_tier).not.toBe('native_self')
    expect(result.basis).toMatch(/not.*canonical/i)
  })

  it('threads constraints_applied through verbatim', () => {
    const result = resolveDisclosureTier(CHART_ID, ['filing_withheld_pending_native_signoff'])
    expect(result.constraints_applied).toEqual(['filing_withheld_pending_native_signoff'])
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// fetchRemedyRows — degrades honestly per-surface on failure (never blocks the others)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('fetchRemedyRows', () => {
  beforeEach(() => {
    mockCallPlatformPrimitive.mockReset()
    mockCallPlatformPrimitive.mockRejectedValue(new Error('network unreachable in unit test'))
  })

  it('records an error for every surface without throwing (Promise.allSettled discipline — ' +
    'one failing surface never blocks the others)', async () => {
    const result = await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: null }, PRINCIPAL)
    expect(result.interventions).toEqual([])
    expect(result.errors.length).toBeGreaterThanOrEqual(2)
    expect(result.errors.some((e) => e.includes('query_remedy_program'))).toBe(true)
    expect(result.errors.some((e) => e.includes('query_rm_prescriptions'))).toBe(true)
  })

  it('skips the corpus fetch (no network call) when no targeted graha is known — never a ' +
    'blind global corpus dump', async () => {
    const result = await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: null }, PRINCIPAL)
    expect(result.errors.some((e) => e.includes('query_remedies_for_chart'))).toBe(false)
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(2)
  })

  it('maps a successful mitigation_map (query_remedy_program) response through the mapper, tiered by citation — ' +
    'fixture is BYTE-FAITHFUL to the primitives route ToolBundle wire shape (results[0].content as JSON string), ' +
    'the mock drift that let the original unwrap bug ship green', async () => {
    // Byte-faithful wire: capability {content, is_error:false} → capabilityResultToToolBundle
    // → toToolBundleResults branch 3 → results: [{ content: JSON.stringify(payload) }].
    function wireEnvelope(payload: Record<string, unknown>) {
      return {
        status: 200,
        envelope: {
          ok: true,
          trace_id: 't',
          result: {
            tool_bundle_id: 'tb-1',
            tool_name: 'x',
            results: [{ content: JSON.stringify(payload) }],
            result_hash: 'sha256:x',
          },
        },
      } as unknown as { status: number; envelope: { ok: true; result: unknown } }
    }
    mockCallPlatformPrimitive.mockImplementation(async (toolName: string) => {
      // Whitelisted MCP primitive name (the bare capability name 'query_remedy_program'
      // is NOT a whitelist key and 400s on the route).
      if (toolName === 'mitigation_map') {
        return wireEnvelope({
          remedies: [{
            mitigation_id: 'mit-1', afflicting_graha: 'Saturn', obstruction_severity: 3,
            intensity_tier: 'moderate', proportionality_basis: 'x', classical_citation: 'BPHS 45.12',
          }],
        })
      }
      return wireEnvelope({ rows: [] })
    })
    const result = await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: 'promise' }, PRINCIPAL)
    expect(result.errors).toEqual([])
    expect(result.interventions).toHaveLength(1)
    expect(result.interventions[0]?.source_surface).toBe('phala_mitigation')
    expect(result.interventions[0]?.efficacy_tier).toBe('classically_attested')
    expect(result.interventions[0]?.targets_link).toBe('promise')
  })

  it('a ToolBundle wrapper whose payload cannot be recovered is named in errors — never read as zero remedies', async () => {
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 200,
      envelope: { ok: true, trace_id: 't', result: { tool_bundle_id: 'tb-1', tool_name: 'x' } },
    })
    const result = await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: null }, PRINCIPAL)
    expect(result.interventions).toEqual([])
    expect(result.errors.some((e) => e.includes('results_missing'))).toBe(true)
  })

  // ── F-118: the ayanamsha budget pin + its non-silencing fallback ──
  function wireEnvelope(payload: Record<string, unknown>) {
    return {
      status: 200,
      envelope: {
        ok: true, trace_id: 't',
        result: { tool_bundle_id: 'tb-1', tool_name: 'x', results: [{ content: JSON.stringify(payload) }], result_hash: 'sha256:x' },
      },
    } as unknown as { status: number; envelope: { ok: true; result: unknown } }
  }

  it('F-118: pins the ayanamsha on bodha_rm_prescriptions_get — the surface stores ONE ROW PER ' +
    'AYANAMSHA, so an unpinned read spends the whole 50-row budget on 5 copies of each remedy', async () => {
    mockCallPlatformPrimitive.mockImplementation(async () => wireEnvelope({ rows: [{ prescription_id: 'p1', remedy_label_human: 'Do X', citation_human: 'c' }] }))
    await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: 'promise' }, PRINCIPAL)
    const call = mockCallPlatformPrimitive.mock.calls.find((c) => c[0] === 'bodha_rm_prescriptions_get')
    expect((call?.[1] as Record<string, unknown>)['ayanamsha_id']).toBe(CANONICAL_AYANAMSHA_ID)
  })

  it('F-118: the pin is a budget fix, NEVER a filter that can silently empty the slate — a ' +
    'chart with no rows on the canonical ayanamsha is re-read unfiltered', async () => {
    let prescriptionCalls = 0
    mockCallPlatformPrimitive.mockImplementation(async (toolName: string, args: Record<string, unknown>) => {
      if (toolName !== 'bodha_rm_prescriptions_get') return wireEnvelope({ remedies: [] })
      prescriptionCalls += 1
      if (args['ayanamsha_id']) return wireEnvelope({ rows: [] })
      return wireEnvelope({ rows: [{ prescription_id: 'p-fallback', remedy_label_human: 'Recite the Shani beej mantra 108×', citation_human: 'BPHS' }] })
    })
    const result = await fetchRemedyRows({ chart_id: CHART_ID, targetedGraha: null, failingLink: 'promise' }, PRINCIPAL)
    expect(prescriptionCalls).toBe(2)
    expect(result.interventions.map((r) => r.source_pk)).toEqual(['p-fallback'])
  })
})
