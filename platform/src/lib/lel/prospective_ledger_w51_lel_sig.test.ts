/**
 * prospective_ledger_w51_lel_sig.test.ts — W5.1 LEL signature regression test.
 *
 * GOCHARA-UTKARSA campaign, wave W5.1 (serving elevation — §N.6 density contract).
 *
 * I3 requirement (W5.1 brief): every new flag/status must have a real detector.
 * This file IS that detector for the LEL signature function over generation='3.0'
 * (g3_utkarsha) window data.
 *
 * What is asserted:
 *   1. computeConfigurationSignature is DETERMINISTIC: the same g3-sourced inputs
 *      always produce the same fingerprint across calls (idempotency).
 *   2. computeConfigurationSignature is STABLE across input ORDERINGS: active_sentences
 *      and contributing_systems may arrive in any order from the DB; the signature
 *      must be identical regardless (sort-then-hash property).
 *   3. computeConfigurationSignature is SENSITIVE to generation-tier content:
 *      a g3 window with different fact_ids or system_ids produces a DIFFERENT
 *      fingerprint from the otherwise-identical v1 window.
 *   4. computeConfigurationSignature is WELL-FORMED: the output is always a
 *      non-empty string matching the expected `${peak_basis}:<hex>` format.
 *   5. computeConfigurationSignature handles EMPTY arrays correctly (g3 windows
 *      with no active_sentences or contributing_systems — honest empty inputs
 *      produce a valid, non-crashing signature, not a fabricated one).
 *
 * These tests are pure/structural — no DB access. They run in every CI pass.
 * A W6.3 probe is NOT a substitute for this detector (I3).
 */
import { describe, it, expect } from 'vitest'
import {
  computeConfigurationSignature,
  type EngineConfigurationSource,
} from './prospective_ledger.js'

// ── Shared g3-sourced specimen inputs ────────────────────────────────────────
// These represent a realistic kala_gochara_windows row as it would arrive from
// the W3.4 ka_gochara_v3_century_materialize writer (generation='g3_utkarsha',
// era_slice_key='g3_1984_1994'). The active_sentences.fact_ids and
// contributing_systems.system_id fields are the inputs computeConfigurationSignature
// actually reads — everything else (era_slice_key, generation, calibration_state)
// is carried in the window but NOT part of the signature computation (the function
// contracts on chart_id / event_class / shape / dates / peak_basis / fact_ids /
// system_ids only, per its own docstring).

const G3_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const G3_EVENT_CLASS = 'career_advancement'

/** Canonical g3 source: the minimum viable EngineConfigurationSource for a g3 window. */
function makeG3Source(overrides: Partial<EngineConfigurationSource> = {}): EngineConfigurationSource {
  return {
    chart_id: G3_CHART_ID,
    event_class: G3_EVENT_CLASS,
    temporal_shape: 'interval',
    window_start: '1984-02-05',
    window_end: '1994-02-05',
    peak_date: '1989-08-12',
    peak_basis: 'gochara_lambda_v3',
    active_sentences: [
      { fact_ids: ['ga_sen_001', 'ga_sen_002'] },
      { fact_ids: ['ga_sen_003'] },
    ],
    contributing_systems: [
      { system_id: 'vimshottari' },
      { system_id: 'guru_shani_double_transit' },
    ],
    ...overrides,
  }
}

// ── 1. Determinism ────────────────────────────────────────────────────────────

describe('computeConfigurationSignature — g3 window data (W5.1 LEL sig regression)', () => {
  it('is deterministic: same g3 inputs → same fingerprint on every call', () => {
    const source = makeG3Source()
    const sig1 = computeConfigurationSignature(source)
    const sig2 = computeConfigurationSignature(source)
    expect(sig1).toBe(sig2)
  })

  // ── 2. Input-order stability ──────────────────────────────────────────────

  it('is stable across active_sentences ORDER: reversed array → same fingerprint', () => {
    const sourceAB = makeG3Source({
      active_sentences: [
        { fact_ids: ['ga_sen_001', 'ga_sen_002'] },
        { fact_ids: ['ga_sen_003'] },
      ],
    })
    const sourceBA = makeG3Source({
      active_sentences: [
        { fact_ids: ['ga_sen_003'] },
        { fact_ids: ['ga_sen_001', 'ga_sen_002'] },
      ],
    })
    // fact_ids are merged, deduped, and sorted before hashing — ORDER MUST NOT MATTER.
    expect(computeConfigurationSignature(sourceAB)).toBe(computeConfigurationSignature(sourceBA))
  })

  it('is stable across fact_id ORDER within a single sentence', () => {
    const sourceAB = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_001', 'ga_sen_002'] }],
    })
    const sourceBA = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_002', 'ga_sen_001'] }],
    })
    expect(computeConfigurationSignature(sourceAB)).toBe(computeConfigurationSignature(sourceBA))
  })

  it('is stable across contributing_systems ORDER', () => {
    const sourceAB = makeG3Source({
      contributing_systems: [
        { system_id: 'vimshottari' },
        { system_id: 'guru_shani_double_transit' },
      ],
    })
    const sourceBA = makeG3Source({
      contributing_systems: [
        { system_id: 'guru_shani_double_transit' },
        { system_id: 'vimshottari' },
      ],
    })
    expect(computeConfigurationSignature(sourceAB)).toBe(computeConfigurationSignature(sourceBA))
  })

  // ── 3. Content sensitivity ────────────────────────────────────────────────

  it('changes fingerprint when fact_ids differ (g3 vs v1 data pool)', () => {
    const g3Source = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_001', 'ga_sen_002'] }],
    })
    const differentFactSource = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_999'] }],
    })
    expect(computeConfigurationSignature(g3Source)).not.toBe(
      computeConfigurationSignature(differentFactSource)
    )
  })

  it('changes fingerprint when contributing_systems differ', () => {
    const sourceWithVimshottari = makeG3Source({
      contributing_systems: [{ system_id: 'vimshottari' }],
    })
    const sourceWithYogini = makeG3Source({
      contributing_systems: [{ system_id: 'yogini' }],
    })
    expect(computeConfigurationSignature(sourceWithVimshottari)).not.toBe(
      computeConfigurationSignature(sourceWithYogini)
    )
  })

  it('changes fingerprint when event_class changes (g3 career vs g3 marriage window)', () => {
    const careerSource = makeG3Source({ event_class: 'career_advancement' })
    const marriageSource = makeG3Source({ event_class: 'marriage' })
    expect(computeConfigurationSignature(careerSource)).not.toBe(
      computeConfigurationSignature(marriageSource)
    )
  })

  it('changes fingerprint when era_slice decade window changes (g3_1984_1994 vs g3_1994_2004)', () => {
    // The era_slice decade is reflected in window_start/window_end — these ARE
    // part of the signature computation (the function hashes dates explicitly).
    const decade1 = makeG3Source({
      window_start: '1984-02-05',
      window_end: '1994-02-05',
      peak_date: '1989-08-12',
    })
    const decade2 = makeG3Source({
      window_start: '1994-02-05',
      window_end: '2004-02-05',
      peak_date: '1999-08-12',
    })
    expect(computeConfigurationSignature(decade1)).not.toBe(
      computeConfigurationSignature(decade2)
    )
  })

  it('changes fingerprint when peak_basis changes (v3 engine vs v1 engine label)', () => {
    // peak_basis is the generation-level distinguisher written by the engine:
    // W3.4 uses 'gochara_lambda_v3'; D-5 v1 uses 'gochara_lambda_e_v1'.
    const g3Sig = computeConfigurationSignature(
      makeG3Source({ peak_basis: 'gochara_lambda_v3' })
    )
    const v1Sig = computeConfigurationSignature(
      makeG3Source({ peak_basis: 'gochara_lambda_e_v1' })
    )
    expect(g3Sig).not.toBe(v1Sig)
  })

  // ── 4. Output well-formedness ─────────────────────────────────────────────

  it('returns a non-empty string in the expected `peak_basis:<hex>` format', () => {
    const sig = computeConfigurationSignature(makeG3Source())
    expect(typeof sig).toBe('string')
    expect(sig.length).toBeGreaterThan(0)
    // Format: `${peak_basis}:${64-hex-char sha256}`
    expect(sig).toMatch(/^[^:]+:[0-9a-f]{64}$/)
  })

  it('includes the peak_basis as a human-legible prefix (generation-identifiable)', () => {
    const sig = computeConfigurationSignature(makeG3Source({ peak_basis: 'gochara_lambda_v3' }))
    expect(sig.startsWith('gochara_lambda_v3:')).toBe(true)
  })

  // ── 5. Empty-input robustness ─────────────────────────────────────────────

  it('handles empty active_sentences — g3 window with no gram sentences (honest zero)', () => {
    const source = makeG3Source({ active_sentences: [] })
    const sig = computeConfigurationSignature(source)
    expect(typeof sig).toBe('string')
    expect(sig.length).toBeGreaterThan(0)
    expect(sig).toMatch(/^[^:]+:[0-9a-f]{64}$/)
  })

  it('handles empty contributing_systems — g3 window with no timing systems (honest zero)', () => {
    const source = makeG3Source({ contributing_systems: [] })
    const sig = computeConfigurationSignature(source)
    expect(typeof sig).toBe('string')
    expect(sig.length).toBeGreaterThan(0)
    expect(sig).toMatch(/^[^:]+:[0-9a-f]{64}$/)
  })

  it('deduplicates fact_ids: repeated facts → same fingerprint as unique facts', () => {
    // The function uses `new Set(...)` on fact_ids — duplicates are removed.
    const withDuplicates = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_001', 'ga_sen_001', 'ga_sen_002'] }],
    })
    const withoutDuplicates = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_001', 'ga_sen_002'] }],
    })
    expect(computeConfigurationSignature(withDuplicates)).toBe(
      computeConfigurationSignature(withoutDuplicates)
    )
  })

  it('handles sentences with no fact_ids key (g3 uncited-extension sentences)', () => {
    // Some g3 sentences may not carry fact_ids (uncited_extension sentences).
    // The function guards with Array.isArray — these contribute nothing to the hash.
    const sourceWithMixedSentences = makeG3Source({
      active_sentences: [
        { fact_ids: ['ga_sen_001'] },
        // Sentence with no fact_ids field (g3 uncited extension)
        {} as { fact_ids?: unknown[] },
      ],
    })
    const sourceOnlyCited = makeG3Source({
      active_sentences: [{ fact_ids: ['ga_sen_001'] }],
    })
    // Both should produce the same fingerprint (the no-fact_ids sentence contributes nothing).
    expect(computeConfigurationSignature(sourceWithMixedSentences)).toBe(
      computeConfigurationSignature(sourceOnlyCited)
    )
  })

  it('handles contributing_systems entries with null system_id (filtered out by real detector)', () => {
    // The function filters null system_ids — a null entry contributes nothing.
    const sourceWithNull = makeG3Source({
      contributing_systems: [
        { system_id: 'vimshottari' },
        { system_id: undefined as unknown as string },
      ],
    })
    const sourceWithoutNull = makeG3Source({
      contributing_systems: [{ system_id: 'vimshottari' }],
    })
    expect(computeConfigurationSignature(sourceWithNull)).toBe(
      computeConfigurationSignature(sourceWithoutNull)
    )
  })
})
