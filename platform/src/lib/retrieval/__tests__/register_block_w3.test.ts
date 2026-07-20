/**
 * register_block_w3.test.ts — W3-L3 "One Envelope" register block + reading_contract +
 * signal_reader_text (C-3). Proves:
 *   1. the register block resolves REAL tokens present in a sample envelope to REAL labels
 *      (signal_class, signal_ref, drill_uri, epistemic_grade, flag, pointer_type, pact_stage);
 *   2. the reading_contract text VARIES with content shape (a confirmed-grounded response vs a
 *      sparse/floored one produce visibly different paragraphs — §N.6 density-signaling);
 *   3. signal_reader_text covers EVERY enumerated signal class (19), and is response-scoped;
 *   4. the whole thing rides on the v3 envelope additively (legacy envelope is unaffected).
 */
import { describe, it, expect } from 'vitest'
import { buildRetrievalEnvelope, type V3Envelope } from '@/lib/retrieval/envelope'
import {
  buildRegisterBlock,
  buildReadingContract,
  collectSignalReaderText,
  SIGNAL_CLASS_LABELS,
  SIGNAL_READER_TEXT,
  SIGNAL_CLASS_COUNT,
  drillUriFamily,
} from '@/lib/retrieval/register_block'

// The 19 live signal classes enumerated from bodha_msr_signals.signal_type_class (2026-07-20).
const LIVE_SIGNAL_CLASSES = [
  'composite_state', 'karaka_alignment', 'sade_sati', 'varga_pattern', 'panchanga',
  'tradition_specific', 'annual', 'parivartana', 'configuration', 'yoga', 'dosha',
  'bhavat_bhavam_amplifier', 'nakshatra_semantic', 'sudarshana_agreement',
  'varga_ratification_divergence', 'arudha', 'special_lagna', 'dhana_axis', 'vargottama_amplification',
]

describe('W3-L3 register block — resolves real tokens to real labels', () => {
  it('resolves signal-class, SIG.MSR, marsys:// URI, grade, flag, pointer + pact tokens present in a sample envelope', () => {
    const content = {
      rows: [
        { signal_id: 'SIG.MSR.142', signal_type_class: 'composite_state', note: 'dispositor chain' },
        { signal_id: 'SIG.MSR.207', signal_type_class: 'yoga' },
      ],
      pointer: 'marsys://tool/L2/bodha_signals_get',
    }
    const register = buildRegisterBlock({
      content,
      epistemicGrade: 'verified_signal',
      judgmentFlags: ['karaka_unresolved: Jupiter not placed', 'timing_hook_failed: x'],
      drillPointers: [
        { instrument: 'marsys://tool/L-JUDGMENT/judgment_query', pointer_type: 'confirm_in_varga', pact_stage: 'confirmation' },
      ],
    })

    const byKind = (k: string) => register.filter(e => e.kind === k)
    // Every kind is populated with a non-empty label.
    expect(register.every(e => e.label.length > 0)).toBe(true)

    // signal_class: composite_state + yoga, real labels.
    const classes = byKind('signal_class')
    expect(classes.map(e => e.token).sort()).toEqual(['composite_state', 'yoga'])
    expect(classes.find(e => e.token === 'composite_state')!.label).toBe(SIGNAL_CLASS_LABELS['composite_state'])

    // signal_ref: both SIG.MSR ids.
    expect(byKind('signal_ref').map(e => e.token).sort()).toEqual(['SIG.MSR.142', 'SIG.MSR.207'])

    // drill_uri: both from content and from the drill pointer instrument, family-labelled.
    const uris = byKind('drill_uri')
    expect(uris.map(e => e.token).sort()).toEqual([
      'marsys://tool/L-JUDGMENT/judgment_query',
      'marsys://tool/L2/bodha_signals_get',
    ])
    expect(uris.find(e => e.token.includes('L2'))!.label).toMatch(/L2 Bodha/)

    // epistemic_grade.
    expect(byKind('epistemic_grade')).toEqual([
      expect.objectContaining({ token: 'verified_signal', kind: 'epistemic_grade' }),
    ])

    // flag: codes only (before the ':'), both flags.
    expect(byKind('flag').map(e => e.token).sort()).toEqual(['karaka_unresolved', 'timing_hook_failed'])

    // pointer_type + pact_stage.
    expect(byKind('pointer_type').map(e => e.token)).toEqual(['confirm_in_varga'])
    expect(byKind('pact_stage').map(e => e.token)).toEqual(['confirmation'])
  })

  it('labels an injected W3-L2 flag code from the flag_labels map (coordination: no hardcoding)', () => {
    const register = buildRegisterBlock({
      content: {},
      judgmentFlags: ['L2_ENUM_CODE_XYZ: some detail'],
      flag_labels: { L2_ENUM_CODE_XYZ: 'W3-L2 closed-enum flag: the matter failed the XYZ gate.' },
    })
    const entry = register.find(e => e.kind === 'flag' && e.token === 'L2_ENUM_CODE_XYZ')
    expect(entry).toBeDefined()
    expect(entry!.label).toBe('W3-L2 closed-enum flag: the matter failed the XYZ gate.')
  })

  it('an unknown flag code still gets a labelled entry (no token left unlabelled)', () => {
    const register = buildRegisterBlock({ content: {}, judgmentFlags: ['brand_new_code: x'] })
    const entry = register.find(e => e.token === 'brand_new_code')
    expect(entry).toBeDefined()
    expect(entry!.label.length).toBeGreaterThan(0)
  })

  it('drillUriFamily extracts the primitive/segment family', () => {
    expect(drillUriFamily('marsys://tool/L1/ganita_positions_get')).toBe('tool/L1')
    expect(drillUriFamily('marsys://resource/asset-registry/all')).toBe('resource/asset-registry')
    expect(drillUriFamily('not-a-uri')).toBeNull()
  })
})

describe('W3-L3 reading_contract — varies with content shape (§N.6 density signaling)', () => {
  const confirmed = buildReadingContract({
    epistemicGrade: 'ganita_fact',
    verifiedFraction: 1.0,
    groundingFactCount: 12,
    coverage: { served: 12, total: 12 },
    moreAvailable: false,
    judgmentFlags: [],
    hasCatalogOnlyRows: false,
    hasDensityContract: true,
    registerKinds: ['signal_class', 'epistemic_grade', 'drill_uri'],
  })

  const sparse = buildReadingContract({
    epistemicGrade: 'floored_null',
    verifiedFraction: 0,
    groundingFactCount: 0,
    coverage: { served: 0, total: null },
    moreAvailable: false,
    judgmentFlags: ['karaka_unresolved: Jupiter', 'varga_confirmation_failed: D9'],
    hasCatalogOnlyRows: true,
    hasDensityContract: false,
    registerKinds: ['flag'],
  })

  it('produces two visibly different paragraphs', () => {
    expect(confirmed).not.toEqual(sparse)
    expect(confirmed.length).toBeGreaterThan(40)
    expect(sparse.length).toBeGreaterThan(40)
  })

  it('the confirmed paragraph reads as grounded + complete + confirmed', () => {
    expect(confirmed).toMatch(/ganita_fact/)
    expect(confirmed).toMatch(/grounded in 12 resolvable L1 fact/)
    expect(confirmed).toMatch(/complete family/)
    expect(confirmed).toMatch(/density contract/)
    expect(confirmed).not.toMatch(/HONEST EMPTY/)
  })

  it('the sparse paragraph honestly reports the empty gap + catalog-only caution + flags (never a hollow envelope)', () => {
    expect(sparse).toMatch(/floored_null/)
    expect(sparse).toMatch(/HONEST EMPTY/)
    expect(sparse).toMatch(/CATALOG-ONLY/)
    expect(sparse).toMatch(/2 judgment flag/)
    // §N.6: absence is never a negative finding.
    expect(sparse).toMatch(/do not read the absence as a negative finding/)
  })

  it('a no-grade response says so explicitly rather than implying confidence', () => {
    const ungraded = buildReadingContract({ epistemicGrade: null, groundingFactCount: 0 })
    expect(ungraded).toMatch(/no computed epistemic grade/)
  })
})

describe('W3-L3 signal_reader_text — covers every enumerated signal class', () => {
  it('SIGNAL_READER_TEXT covers all 19 live signal classes, 1:1, no extras', () => {
    expect(SIGNAL_CLASS_COUNT).toBe(19)
    expect(Object.keys(SIGNAL_READER_TEXT).sort()).toEqual([...LIVE_SIGNAL_CLASSES].sort())
    // every class also has a compact label.
    expect(Object.keys(SIGNAL_CLASS_LABELS).sort()).toEqual([...LIVE_SIGNAL_CLASSES].sort())
    // every reader-text paragraph is a non-trivial, native-polish-flagged draft.
    for (const cls of LIVE_SIGNAL_CLASSES) {
      expect(SIGNAL_READER_TEXT[cls].length).toBeGreaterThan(80)
      expect(SIGNAL_READER_TEXT[cls]).toMatch(/native-polish-pending/)
    }
  })

  it('collectSignalReaderText is response-scoped by default, full-map on all:true', () => {
    const scoped = collectSignalReaderText(['yoga', 'dosha'])
    expect(Object.keys(scoped).sort()).toEqual(['dosha', 'yoga'])
    const all = collectSignalReaderText([], { all: true })
    expect(Object.keys(all)).toHaveLength(19)
  })
})

describe('W3-L3 envelope wiring — additive on v3, absent on legacy', () => {
  const params = {
    tool: 'bodha_signals_get',
    content: { rows: [{ signal_id: 'SIG.MSR.142', signal_type_class: 'karaka_alignment' }] },
    epistemic: { grade: 'verified_signal' as const, verified_fraction: 0.8, note: 'n' },
    grounding: { fact_ids: ['F1', 'F2'], citations: [], grounding_score: 0.8 },
    coverage: { family: 'msr_signals[domain=career]', served: 1, total: 5 },
    drill_pointers: [{ instrument: 'marsys://tool/L2/bodha_signals_get', hint: 'drill', pointer_type: 'karaka_condition' as const }],
  }

  it('legacy envelope has NO register/reading_contract/signal_reader_text fields', () => {
    const legacy = buildRetrievalEnvelope(params, 'legacy') as unknown as Record<string, unknown>
    expect(legacy.register).toBeUndefined()
    expect(legacy.reading_contract).toBeUndefined()
    expect(legacy.signal_reader_text).toBeUndefined()
  })

  it('v3 envelope carries a populated register, a reading_contract paragraph, and scoped signal_reader_text', () => {
    const v3 = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    expect(v3.register!.length).toBeGreaterThan(0)
    // real tokens resolved: the signal class, the SIG.MSR id, the grade, the drill URI, the pointer type.
    const tokens = v3.register!.map(e => e.token)
    expect(tokens).toContain('karaka_alignment')
    expect(tokens).toContain('SIG.MSR.142')
    expect(tokens).toContain('verified_signal')
    expect(tokens).toContain('karaka_condition')
    // reading_contract is a generated paragraph mentioning the grade + partial slice.
    expect(v3.reading_contract).toMatch(/verified_signal/)
    expect(v3.reading_contract).toMatch(/1 of 5/)
    // signal_reader_text scoped to the one class present.
    expect(Object.keys(v3.signal_reader_text!)).toEqual(['karaka_alignment'])
  })

  it('emit_register_block:false suppresses the three fields on v3', () => {
    const v3 = buildRetrievalEnvelope({ ...params, emit_register_block: false }, 'v3') as V3Envelope
    expect(v3.register).toBeUndefined()
    expect(v3.reading_contract).toBeUndefined()
    expect(v3.signal_reader_text).toBeUndefined()
  })
})
