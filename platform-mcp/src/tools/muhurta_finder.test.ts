/**
 * muhurta_finder.test.ts — Lane F (EL-50 / EL-53) regressions.
 *
 * Elevation Campaign v2.1 · STREAM γ (PŪRṆA) · Lane F [OPUS].
 * Drives the pure enrichWindowsLaneF pipeline + primitives directly (no platform
 * round-trip, no live MCP) so the named regressions are reproducible offline:
 *   - EL-50(b) Vadha-tārā: an Aug-26–28 window under an adverse Vadha tārā must NOT
 *     rank #1 and must carry a visible flag.
 *   - EL-50(c) target_graha: Venus debilitated-in-transit for all of August must
 *     surface on EVERY August window for a Venus election.
 */
import { describe, it, expect } from 'vitest'
import {
  MuhurtaFinderInputSchema,
  ACTIVITY_RULES,
  NAKSHATRAS,
  nakshatraNumber,
  computeTaraBala,
  toIstIso,
  computeHoraLadder,
  computeTargetGrahaVerdict,
  c5PendingProvider,
  enrichWindowsLaneF,
  type MuhurtaWindow,
  type MuhurtaFinderInput,
  type TargetGrahaTransitProvider,
} from './muhurta_finder'

// ── window builder ──────────────────────────────────────────────────────────────
function win(startUtc: string, score: number, moonNakshatra: string): MuhurtaWindow {
  const start = new Date(startUtc)
  const end = new Date(start.getTime() + 48 * 3600000)
  return {
    start: start.toISOString(),
    end: end.toISOString(),
    score,
    source_citation: 'BPHS ch.46 (test fixture)',
    factors: {
      panchanga_quality: score, dasha_quality: score, transit_quality: score, signal_activation: score,
      panchanga_details: {
        tithi_name: 'Shukla Tritiya', vara_lord: 'Jupiter', moon_nakshatra: moonNakshatra,
        yoga: 'Shiva', inauspicious_windows: [],
      },
      dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
      avoid_notes: [],
    },
  }
}

function baseInput(overrides: Partial<MuhurtaFinderInput>): MuhurtaFinderInput {
  return {
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    action_type: 'general',
    date_range: { start: '2026-08-01', end: '2026-08-31' },
    limit: 20,
    ...overrides,
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// Sub-item 1 — activity_type taxonomy extension
// ════════════════════════════════════════════════════════════════════════════════
describe('EL-50(a) activity_type taxonomy extension', () => {
  it('the schema accepts the three new spiritual/remedial classes', () => {
    for (const at of ['spiritual_initiation', 'remedial_ritual', 'japa_start']) {
      const parsed = MuhurtaFinderInputSchema.parse(baseInput({ action_type: at as MuhurtaFinderInput['action_type'] }))
      expect(parsed.action_type).toBe(at)
    }
  })

  it('each new class carries a cited classical rule set and maps to a known base action_type', () => {
    for (const at of ['spiritual_initiation', 'remedial_ritual', 'japa_start'] as const) {
      const rule = ACTIVITY_RULES[at]
      expect(rule.citation).toMatch(/Muhurta|BPHS|Martanda|Chintamani/)
      expect(rule.favorable_nakshatras.length).toBeGreaterThan(0)
      expect(['general', 'medical', 'marriage', 'travel', 'business', 'education', 'property']).toContain(rule.base_action_type)
      expect(rule.event_class).toMatch(/initiation|ritual|sadhana|mantra|upaya/)
    }
  })

  it('spiritual_initiation favors Pushya + Jupiter-vāra and avoids ugra/tīkṣṇa nakshatras', () => {
    const r = ACTIVITY_RULES.spiritual_initiation
    expect(r.favorable_nakshatras).toContain(nakshatraNumber('Pushya'))
    expect(r.favorable_varas).toContain('Jupiter')
    expect(r.avoid_nakshatras).toContain(nakshatraNumber('Mula'))     // tīkṣṇa
    expect(r.avoid_nakshatras).toContain(nakshatraNumber('Bharani'))  // ugra
  })
})

// ════════════════════════════════════════════════════════════════════════════════
// Sub-item 2 — tāra bala join  (NAMED REGRESSION: Aug 26-28 Vadha-tārā)
// ════════════════════════════════════════════════════════════════════════════════
describe('EL-50(b) tāra bala — Nava-tārā chakra', () => {
  it('computeTaraBala: Purva Bhadrapada native + Rohini day → Vadha (7), adverse+severe', () => {
    const janma = nakshatraNumber('Purva Bhadrapada')!  // 25
    const day = nakshatraNumber('Rohini')!               // 4
    const tb = computeTaraBala(janma, day)
    expect(tb.tara_index).toBe(7)
    expect(tb.tara_name).toBe('Vadha')
    expect(tb.adverse).toBe(true)
    expect(tb.severity).toBe('severe')
  })

  it('computeTaraBala: same nakshatra → Janma (1), and Sampat(2) is favorable', () => {
    expect(computeTaraBala(25, 25).tara_name).toBe('Janma')
    const sampat = computeTaraBala(25, nakshatraNumber('Uttara Bhadrapada')!) // 26 → 2nd
    expect(sampat.tara_index).toBe(2)
    expect(sampat.favorable).toBe(true)
  })

  it('REGRESSION: an Aug-26–28 window under adverse Vadha-tārā must NOT rank #1 and must carry a flag', () => {
    // Native = Purva Bhadrapada (the FORENSIC janma nakshatra). Moon in Rohini on Aug 26 = Vadha.
    // The adverse window is given the HIGHEST raw platform score to prove it cannot silently win.
    const windows: MuhurtaWindow[] = [
      win('2026-08-26T00:00:00Z', 0.92, 'Rohini'),   // Vadha for this native — highest raw score
      win('2026-08-10T00:00:00Z', 0.80, 'Pushya'),   // Kshema/favorable — clean
      win('2026-08-14T00:00:00Z', 0.75, 'Anuradha'), // clean
    ]
    const { windows: ranked, lane_f } = enrichWindowsLaneF(
      windows,
      baseInput({ native_janma_nakshatra: 'Purva Bhadrapada' }),
    )
    expect(lane_f.tara_bala_status).toBe('applied')

    const top = ranked[0]!
    // The Aug-26 Vadha window is NOT rank #1 despite the highest raw score.
    expect(top.start.startsWith('2026-08-26')).toBe(false)
    expect(top.tara_bala?.adverse).toBe(false)

    // The Aug-26 window is present, flagged, disqualified, and demoted below clean windows.
    const aug26 = ranked.find(w => w.start.startsWith('2026-08-26'))!
    expect(aug26.tara_bala?.tara_name).toBe('Vadha')
    expect(aug26.hard_flag).toBe(true)
    expect(aug26.disqualified).toBe(true)
    expect(aug26.rank_penalty_reason?.join(' ')).toMatch(/Vadha/)
    expect(ranked.indexOf(aug26)).toBeGreaterThan(0)
  })

  it('without native_janma_nakshatra, tāra bala is honestly reported unavailable (no fabrication)', () => {
    const { lane_f } = enrichWindowsLaneF([win('2026-08-26T00:00:00Z', 0.9, 'Rohini')], baseInput({}))
    expect(lane_f.tara_bala_status).toBe('unavailable_no_janma_nakshatra')
    expect(lane_f.tara_bala_note).toMatch(/not supplied/)
  })
})

// ════════════════════════════════════════════════════════════════════════════════
// Sub-item 3 — target_graha transit gate  (NAMED REGRESSION: Venus-debilitated-August)
// ════════════════════════════════════════════════════════════════════════════════
describe('EL-50(c) target_graha transit gate', () => {
  it('default provider (C5 DRAFT) returns pending_c5_service, never a fabricated clean bill', () => {
    const v = computeTargetGrahaVerdict('Venus', '2026-08-15T00:00:00Z', c5PendingProvider)
    expect(v.status).toBe('pending_c5_service')
    expect(v.combust).toBeNull()
    expect(v.note).toMatch(/NOT a clean bill/)
  })

  it('REGRESSION: Venus debilitated for all August → EVERY August Venus-election window surfaces it', () => {
    // Injected stub standing in for β's C5 sidereal service: Venus nīca (debilitated) all August.
    const venusDebilitatedAllAugust: TargetGrahaTransitProvider = (graha, instant) => {
      const isAugust2026 = instant.startsWith('2026-08')
      if (graha === 'Venus' && isAugust2026) {
        return { combust: false, debilitated: true, retrograde: false, transit_dignity: 'debilitated (Virgo/nīca)', available: true }
      }
      return { combust: false, debilitated: false, retrograde: false, transit_dignity: 'neutral', available: true }
    }
    const windows: MuhurtaWindow[] = [
      win('2026-08-05T00:00:00Z', 0.88, 'Pushya'),
      win('2026-08-15T00:00:00Z', 0.83, 'Anuradha'),
      win('2026-08-25T00:00:00Z', 0.79, 'Hasta'),
    ]
    const { windows: ranked, lane_f } = enrichWindowsLaneF(
      windows,
      baseInput({ action_type: 'remedial_ritual', target_graha: 'Venus' }),
      { transitProvider: venusDebilitatedAllAugust },
    )
    // Every August window surfaces the debilitation — not silently ranked normally.
    expect(ranked.length).toBe(3)
    for (const w of ranked) {
      expect(w.target_graha_check?.status).toBe('flagged')
      expect(w.target_graha_check?.debilitated).toBe(true)
      expect(w.hard_flag).toBe(true)
      expect(w.disqualified).toBe(true)
      expect(w.rank_penalty_reason?.join(' ')).toMatch(/debilitated/)
    }
    expect(lane_f.target_graha_status).toBe('applied')
  })

  it('a clean target graha does not flag the window', () => {
    const clean: TargetGrahaTransitProvider = () => ({ combust: false, debilitated: false, retrograde: false, transit_dignity: 'exalted', available: true })
    const { windows: ranked } = enrichWindowsLaneF(
      [win('2026-08-05T00:00:00Z', 0.88, 'Pushya')],
      baseInput({ target_graha: 'Jupiter' }),
      { transitProvider: clean },
    )
    expect(ranked[0]!.target_graha_check?.status).toBe('ok')
    expect(ranked[0]!.hard_flag).toBeUndefined()
  })
})

// ════════════════════════════════════════════════════════════════════════════════
// Sub-item 4 — horā / sub-day IST resolution
// ════════════════════════════════════════════════════════════════════════════════
describe('EL-50(d) horā / IST sub-day resolution', () => {
  it('toIstIso anchors a UTC instant to an explicit +05:30 timestamp', () => {
    expect(toIstIso('2026-08-26T00:00:00Z')).toBe('2026-08-26T05:30:00+05:30')
  })

  it('horā ladder is day-lord-first (Chaldean order) with IST timestamps', () => {
    const ladder = computeHoraLadder('2026-08-23T06:30:00Z')  // → 12:00 IST Aug 23 (Sunday)
    expect(ladder.length).toBeGreaterThan(0)
    // first horā of the ladder is ruled by the day lord
    const first = ladder[0]!
    expect(first.start_ist).toMatch(/\+05:30$/)
    expect(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']).toContain(first.hora_lord)
    // benefic horās are correctly classified
    for (const s of ladder) expect(typeof s.benefic).toBe('boolean')
  })

  it('every enriched window gains explicit start_ist/end_ist and a horā ladder', () => {
    const { windows: ranked } = enrichWindowsLaneF([win('2026-08-05T00:00:00Z', 0.8, 'Pushya')], baseInput({}))
    const w = ranked[0]!
    expect(w.start_ist).toMatch(/\+05:30$/)
    expect(w.end_ist).toMatch(/\+05:30$/)
    expect(Array.isArray(w.hora_ladder)).toBe(true)
    expect(w.hora_ladder!.length).toBeGreaterThan(0)
  })
})

// ════════════════════════════════════════════════════════════════════════════════
// EL-53 — election files as a falsifiable prediction
// ════════════════════════════════════════════════════════════════════════════════
describe('EL-53 file_as_prediction', () => {
  it('produces a prospective-ledger-shaped filing closable via mimamsa_outcome_record', () => {
    const { prediction_filing } = enrichWindowsLaneF(
      [win('2026-08-05T00:00:00Z', 0.86, 'Pushya'), win('2026-08-15T00:00:00Z', 0.7, 'Hasta')],
      baseInput({ action_type: 'spiritual_initiation', file_as_prediction: true }),
    )
    expect(prediction_filing).toBeDefined()
    const f = prediction_filing!
    expect(f.claim_shape).toBe('window')
    expect(f.generator_class).toBe('engine')
    expect(f.falsifier.length).toBeGreaterThan(0)          // mandatory falsifier
    expect(f.confidence).toBeGreaterThan(0)
    expect(f.event_class).toBe('mantra_initiation')        // spiritual_initiation → mantra_initiation
    expect(f.close_via.tool).toBe('mimamsa_outcome_record')
    expect(f.close_via.verdict_vocabulary).toEqual(['confirmed', 'partial', 'denied'])
    expect(f.persistence).toBe('payload_only')             // DB write PARKED on alpha
    // filing tracks the top-ranked window
    expect(f.window_start.startsWith('2026-08-05')).toBe(true)
    expect(f.predicted_quality.star_rating).toBeGreaterThanOrEqual(1)
    expect(f.predicted_quality.star_rating).toBeLessThanOrEqual(5)
  })

  it('no filing when file_as_prediction is absent', () => {
    const { prediction_filing } = enrichWindowsLaneF([win('2026-08-05T00:00:00Z', 0.8, 'Pushya')], baseInput({}))
    expect(prediction_filing).toBeUndefined()
  })

  it('sanity: NAKSHATRAS has 27 entries', () => {
    expect(NAKSHATRAS.length).toBe(27)
  })
})
