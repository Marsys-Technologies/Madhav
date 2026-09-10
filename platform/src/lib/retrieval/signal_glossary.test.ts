/**
 * signal_glossary.test.ts — F-131 unit tests for serve-time labelling + marker classification.
 *
 * The strings asserted here are REAL, not invented for the test: every headline below was read
 * live out of `bodha_msr_signals.signal_headline_text` for the native chart
 * 482012f1-710e-4a25-994a-93821f5871aa on 2026-08-21, which is what makes these regression
 * guards rather than round-trips of my own assumptions.
 */
import { describe, expect, it } from 'vitest'
import {
  ABSTENTION_MARKER_PATTERNS,
  CATALOG_ONLY_MARKER_PATTERNS,
  FACT_CATEGORY_DISPLAY_LABEL,
  INTERNAL_MARKER_PATTERNS,
  classifySignalMarker,
  humanizeSignalHeadline,
} from './signal_glossary'

/** The exact row F-131 was raised on — it ranked #5 by priority_score on the native's chart. */
const F131_ABSTENTION_ROW =
  'graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]'

/** The other F-131 exhibit: a real astrological finding, but served as a raw schema key. */
const F131_RAW_TEMPLATE_ROW = 'SAT: arudha pada: sign = Aquarius [ga_sensitive]'

describe('classifySignalMarker — F-131 abstention exclusion', () => {
  it('classifies the exact F-131 row as an abstention marker, not a signal', () => {
    const c = classifySignalMarker(F131_ABSTENTION_ROW)
    expect(c.disposition).toBe('abstention')
    // Glossary order is load-bearing: the most specific pattern must be the one reported.
    expect(c.matched_pattern).toBe('floored: no_canonical_per_varga_method')
  })

  it('catches the wider floored:-prefixed family, not just the D14 cheshta-bala case', () => {
    // Also live rows on the native chart — the same abstention discipline, prose reasons.
    const others = [
      'graha avastha jagradadi per varga: D ALL = floored: waking/dreaming state is a single D1 ' +
        'concept with no canonical varga extension (BPHS) [ga_structural]',
      'graha avastha sayanadi per varga: D ALL = floored: 12 sleeping-posture states are D1-only ' +
        'per Parashara; no canonical varga method exists [ga_structural]',
    ]
    for (const row of others) {
      expect(classifySignalMarker(row).disposition).toBe('abstention')
    }
  })

  it('classifies every abstention pattern in the glossary as abstention', () => {
    for (const p of ABSTENTION_MARKER_PATTERNS) {
      expect(classifySignalMarker(`some headline ${p} tail`).disposition).toBe('abstention')
    }
    expect(ABSTENTION_MARKER_PATTERNS.length).toBeGreaterThan(0)
  })

  it('is case-insensitive and treats [ and _ as literals, not metacharacters', () => {
    expect(classifySignalMarker('X = [COMPUTATION-ABSTENTION: ...]').disposition).toBe('abstention')
    expect(classifySignalMarker('x = [computation-abstention: ...]').disposition).toBe('abstention')
    // `floor_reason=` must not match `floorXreason=` (it would if `_` were a LIKE wildcard).
    expect(classifySignalMarker('floorXreason=none').disposition).toBeNull()
    expect(classifySignalMarker('floor_reason=none').disposition).toBe('abstention')
  })

  it('does NOT exclude a genuine astrological headline', () => {
    expect(classifySignalMarker(F131_RAW_TEMPLATE_ROW)).toEqual({
      disposition: null, matched_pattern: null,
    })
    expect(classifySignalMarker('ashtakavarga bindu per varga: D16 = 4 [ga_structural]').disposition)
      .toBeNull()
    expect(classifySignalMarker(null).disposition).toBeNull()
    expect(classifySignalMarker('').disposition).toBeNull()
  })

  it('gives requires_pass the catalog_only disposition, NOT abstention (§N.6)', () => {
    // A catalog-only yoga row is a real candidate awaiting a second pass — it must stay served
    // and flagged, never dropped as if it were a computation abstention.
    const c = classifySignalMarker('yoga label: fire reason = requires_pass [ga_structural]')
    expect(c.disposition).toBe('catalog_only')
    expect(c.matched_pattern).toBe('requires_pass')
    expect(CATALOG_ONLY_MARKER_PATTERNS).toContain('requires_pass')
    expect(ABSTENTION_MARKER_PATTERNS).not.toContain('requires_pass')
  })

  it('partitions the glossary list exhaustively — no pattern is silently dropped', () => {
    expect([...ABSTENTION_MARKER_PATTERNS, ...CATALOG_ONLY_MARKER_PATTERNS].sort())
      .toEqual([...INTERNAL_MARKER_PATTERNS].sort())
  })
})

describe('humanizeSignalHeadline — acharya-grade labelling', () => {
  it('translates the F-131 raw template row, preserving subject, key, value and provenance', () => {
    const h = humanizeSignalHeadline(F131_RAW_TEMPLATE_ROW)
    expect(h.label_mapped).toBe(true)
    expect(h.matched_fact_category).toBe('arudha_pada')
    expect(h.headline_label).toBe('SAT: Arudha Pāda: sign = Aquarius [ga_sensitive]')
  })

  it('translates a category at the start of the string (no subject prefix)', () => {
    const h = humanizeSignalHeadline('argala natal matrix: house 4 = 2 [ga_structural]')
    expect(h.headline_label).toBe('Argala (Intervention) Matrix: house 4 = 2 [ga_structural]')
    expect(h.matched_fact_category).toBe('argala_natal_matrix')
  })

  it('handles the subject-with-location prefix form (H#, varga)', () => {
    const h = humanizeSignalHeadline('SAT (H10, D9): graha dignity per varga: dignity state = neutral [ga_structural]')
    expect(h.headline_label)
      .toBe('SAT (H10, D9): Graha Dignity per Varga: dignity state = neutral [ga_structural]')
  })

  it('anchors the category segment — "graha position" does not match inside "upagraha position"', () => {
    const h = humanizeSignalHeadline('SAT: upagraha position: sign = Capricorn [ga_sensitive]')
    expect(h.matched_fact_category).toBe('upagraha_position')
    expect(h.headline_label)
      .toBe('SAT: Upagraha (Shadow Planet) Position: sign = Capricorn [ga_sensitive]')
  })

  it('prefers the longest matching category over a shorter one', () => {
    // 'graha_nakshatra' and 'graha_nakshatra_join' are both glossary keys.
    const h = humanizeSignalHeadline('SAT: graha nakshatra join: yoni en = Tiger [ga_sensitive]')
    expect(h.matched_fact_category).toBe('graha_nakshatra_join')
    expect(h.headline_label).toBe('SAT: Graha–Nakshatra Junction: yoni en = Tiger [ga_sensitive]')
  })

  it('passes an unmapped headline through VERBATIM and flags it — never invents a label', () => {
    // Real live category with no glossary entry (confirmed against the live category census).
    const raw = 'kp planet significations: star lord = Mercury [ga_sensitive]'
    const h = humanizeSignalHeadline(raw)
    expect(h.label_mapped).toBe(false)
    expect(h.matched_fact_category).toBeNull()
    expect(h.headline_label).toBe(raw)   // byte-identical, not title-cased or prettified
  })

  it('leaves an abstention marker untouched when asked to label it (labelling never launders)', () => {
    const h = humanizeSignalHeadline(F131_ABSTENTION_ROW)
    // The category IS in the glossary, so the label applies — but the floor reason survives
    // intact, so a caller that (wrongly) skipped the exclusion still sees the marker.
    expect(h.headline_label).toContain('floored: no_canonical_per_varga_method')
  })

  it('handles null/empty input without throwing', () => {
    expect(humanizeSignalHeadline(null).headline_label).toBe('')
    expect(humanizeSignalHeadline(undefined).label_mapped).toBe(false)
  })
})

describe('FACT_CATEGORY_DISPLAY_LABEL — domain-correctness spot-checks', () => {
  it('carries the corrected midpoint label — no invented Sanskrit', () => {
    // Was "Midpoint (Sandhya Bindu)". "Sandhya bindu" is not a classical Jyotish term
    // (sandhyā = twilight; a junction is sandhi). Corrected in the Python SSoT against the
    // live facts: fact_category='midpoint' on the canonical chart has 55 distinct
    // fact_subject values, every one a PAIR — and they are NOT all graha pairs. Nine are
    // ASC-* (ASC-JUP, ASC-SUN, …) and nine are MC-*, i.e. chart ANGLES rather than grahas,
    // so "graha-pair" would misdescribe a third of the family. The label is scoped to what
    // the data actually holds.
    expect(FACT_CATEGORY_DISPLAY_LABEL['midpoint']).toBe(
      'Chart-Point Pair Midpoint (graha/lagna/MC)',
    )
    expect(JSON.stringify(FACT_CATEGORY_DISPLAY_LABEL)).not.toContain('Sandhya Bindu')
    // The angle-bearing pairs are precisely why the label may not say "graha".
    expect(FACT_CATEGORY_DISPLAY_LABEL['midpoint']).not.toBe('Graha-Pair Midpoint')
  })

  it('uses the correct classical term for each spot-checked category', () => {
    expect(FACT_CATEGORY_DISPLAY_LABEL['graha_shadbala_total']).toContain('Ṣaḍbala')
    expect(FACT_CATEGORY_DISPLAY_LABEL['maitri_graha_natural']).toContain('Naisargika')
    expect(FACT_CATEGORY_DISPLAY_LABEL['saham_position']).toContain('Saham')
    expect(FACT_CATEGORY_DISPLAY_LABEL['virodha_argala_natal_matrix']).toContain('Virodha Argala')
  })

  it('never labels a category with its own raw snake_case key', () => {
    for (const [k, v] of Object.entries(FACT_CATEGORY_DISPLAY_LABEL)) {
      expect(v).not.toBe(k)
      expect(v).not.toContain('_')
    }
  })
})
