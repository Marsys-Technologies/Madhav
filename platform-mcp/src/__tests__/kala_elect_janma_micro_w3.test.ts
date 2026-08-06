/**
 * kala_elect_janma_micro_w3.test.ts — ṢAḌ-DARŚANA W3, Lane w3-muh, Item 14
 * (SHAD_DARSHANA_BRIEF_v2_0.md §1 item 14 — Janma-anchored election micro-rules).
 *
 * TDD: written BEFORE lib/kala_janma_micro_rules.ts exists. All tests must FAIL
 * until the implementation is created, then PASS.
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §3.2:
 *   "Personal star overlay: tārā-bala from janma-nakṣatra (vadha/vipat/pratyak = veto),
 *    chandra-bala (transit Moon house from natal Moon), and BUILD: janma-anchored
 *    micro-rules — janma-tithi/vara/nakṣatra returns as personally-potent days."
 *
 * NATIVE FORENSIC ANCHORS (CLAUDE.md §B, FORENSIC 7/7 PASS):
 *   - janma nakshatra: Purva Bhadrapada (id=25, 0-indexed=24)
 *   - janma tithi: Shukla Tritiya (tithi number 3)
 *   - janma vara: Ravivara (Sunday, index 0)
 *   - janma lagna sign: Aries (sign index 0, sign id 1)
 *
 * TARA BALA ACCURACY ANCHORS (verified against panchang_engine/tara_bala.py):
 *   A14-1: Purva Bhadrapada (id=25) vs Purva Bhadrapada (id=25): count=1 → Janma (neutral)
 *   A14-2: Purva Bhadrapada (id=25) vs Ashwini (id=1): count=4 → Kshema (auspicious)
 *   A14-3: Purva Bhadrapada (id=25) vs Uttara Phalguni (id=12): count=15 → position 6 → Sadhaka (auspicious)
 *   A14-4: Purva Bhadrapada (id=25) vs Ardra (id=6): count=9 → Ati-Mitra (auspicious)
 *   A14-5: Purva Bhadrapada (id=25) vs Krittika (id=3): count=6 → position 6 → Sadhaka (auspicious)
 *   A14-6 ADVERSE: Purva Bhadrapada (id=25) vs Rohini (id=4): count=7 → position 7 → Vadha (inauspicious, severe)
 *
 * HOW count IS COMPUTED: ((current_id - janma_id + 27) % 27) + 1 (1-indexed inclusive)
 *   Purva Bhadrapada→Ashwini: ((1 - 25 + 27) % 27) + 1 = (3 % 27) + 1 = 4 → Kshema ✓
 *   Purva Bhadrapada→Uttara Phalguni: ((12 - 25 + 27) % 27) + 1 = 14+1 = 15
 *     tara_index = ((15-1) % 9) + 1 = 5+1 = 6 → Sadhaka ✓
 *   Purva Bhadrapada→Ardra: ((6 - 25 + 27) % 27) + 1 = 8+1 = 9 → Ati-Mitra ✓
 *   Purva Bhadrapada→Rohini: ((4 - 25 + 27) % 27) + 1 = 6+1 = 7 → Vadha ✓
 *
 * §N.5: this module contains NO new astrological computation — the tāra formula is
 * REFERENCED from panchang_engine/tara_bala.py's own `_TARA_QUALITY` table and the
 * `computeTaraBala` helper in muhurta_finder.ts. The micro-rule output is a
 * DETERMINISTIC restatement of that formula applied to the native's fixed janma anchor.
 *
 * §N.6 / §N.8: the coverage entry for `janma_anchored_micro_rules` is `computed` only
 * when the janma anchor was actually supplied and the micro-rules were applied;
 * `honest_empty` when no janma anchor is available. Never fabricated.
 */
import { describe, it, expect } from 'vitest'
import {
  computeTaraMicroRule,
  computeJanmaMicroRules,
  applyJanmaMicroRulesOrNull,
  ADVERSE_TARA_INDICES,
  SEVERE_TARA_INDICES,
  type TaraMicroRule,
  type JanmaMicroRules,
  type JanmaMicroRuleContext,
} from '../lib/kala_janma_micro_rules.js'

// ── Accuracy anchor helpers ───────────────────────────────────────────────────────────

/** Purva Bhadrapada (janma nakshatra id, 1-indexed per tara_bala.py convention) */
const JANMA_NAK_ID = 25  // Purva Bhadrapada

// ── Unit tests: computeTaraMicroRule ─────────────────────────────────────────────────

describe('computeTaraMicroRule — pure tārā computation from janma nakshatra', () => {
  it('accuracy anchor A14-1: janma star itself → count=1, Janma, neutral (not favorable, not adverse)', () => {
    // Purva Bhadrapada vs Purva Bhadrapada: ((25-25+27)%27)+1 = 0+1 = 1 → Janma
    const r = computeTaraMicroRule(JANMA_NAK_ID, 25)
    expect(r.count_from_janma).toBe(1)
    expect(r.tara_index).toBe(1)
    expect(r.tara_name).toBe('Janma')
    expect(r.favorable).toBe(false)
    expect(r.adverse).toBe(false)  // Janma is neutral — not adverse, but also not favorable
    expect(r.severity).toBe('none')
    expect(r.citation).toMatch(/Nava Tara|tara_bala|Muhurta Chintamani/)
  })

  it('accuracy anchor A14-2: Ashwini (id=1) → count=4, Kshema, auspicious (favorable)', () => {
    // ((1-25+27)%27)+1 = 3+1 = 4 → tara_index=4 → Kshema
    const r = computeTaraMicroRule(JANMA_NAK_ID, 1)
    expect(r.count_from_janma).toBe(4)
    expect(r.tara_index).toBe(4)
    expect(r.tara_name).toBe('Kshema')
    expect(r.favorable).toBe(true)
    expect(r.adverse).toBe(false)
    expect(r.severity).toBe('none')
  })

  it('accuracy anchor A14-3: Uttara Phalguni (id=12) → count=15, tara_index=6, Sadhaka, auspicious', () => {
    // ((12-25+27)%27)+1 = 14+1 = 15; ((15-1)%9)+1 = 5+1 = 6 → Sadhaka
    const r = computeTaraMicroRule(JANMA_NAK_ID, 12)
    expect(r.count_from_janma).toBe(15)
    expect(r.tara_index).toBe(6)
    expect(r.tara_name).toBe('Sadhaka')
    expect(r.favorable).toBe(true)
    expect(r.adverse).toBe(false)
  })

  it('accuracy anchor A14-4: Ardra (id=6) → count=9, Ati-Mitra, auspicious (max strength)', () => {
    // ((6-25+27)%27)+1 = 8+1 = 9 → Ati-Mitra (9th position)
    const r = computeTaraMicroRule(JANMA_NAK_ID, 6)
    expect(r.count_from_janma).toBe(9)
    expect(r.tara_index).toBe(9)
    expect(r.tara_name).toBe('Ati-Mitra')
    expect(r.favorable).toBe(true)
    expect(r.adverse).toBe(false)
  })

  it('accuracy anchor A14-5: Krittika (id=3) → count=6, Sadhaka, auspicious', () => {
    // ((3-25+27)%27)+1 = 5+1 = 6 → tara_index=6 → Sadhaka
    const r = computeTaraMicroRule(JANMA_NAK_ID, 3)
    expect(r.count_from_janma).toBe(6)
    expect(r.tara_index).toBe(6)
    expect(r.tara_name).toBe('Sadhaka')
    expect(r.favorable).toBe(true)
    expect(r.adverse).toBe(false)
  })

  it('accuracy anchor A14-6: Rohini (id=4) → count=7, Vadha, ADVERSE (severe veto)', () => {
    // ((4-25+27)%27)+1 = 6+1 = 7 → tara_index=7 → Vadha (severe)
    const r = computeTaraMicroRule(JANMA_NAK_ID, 4)
    expect(r.count_from_janma).toBe(7)
    expect(r.tara_index).toBe(7)
    expect(r.tara_name).toBe('Vadha')
    expect(r.favorable).toBe(false)
    expect(r.adverse).toBe(true)
    expect(r.severity).toBe('severe')
  })

  it('Vipat (count=3, tara_index=3) is adverse with severity=caution', () => {
    // janma=1 (Ashwini), current=3 (Krittika): ((3-1+27)%27)+1 = 3
    const r = computeTaraMicroRule(1, 3)
    expect(r.tara_index).toBe(3)
    expect(r.tara_name).toBe('Vipat')
    expect(r.adverse).toBe(true)
    expect(r.severity).toBe('caution')
  })

  it('Pratyari (tara_index=5) is adverse with severity=caution', () => {
    // janma=1, current=5 (Mrigashira): ((5-1+27)%27)+1 = 5
    const r = computeTaraMicroRule(1, 5)
    expect(r.tara_index).toBe(5)
    expect(r.tara_name).toBe('Pratyari')
    expect(r.adverse).toBe(true)
    expect(r.severity).toBe('caution')
  })

  it('secondary cycle (count=10..18) wraps correctly — Sampat repeats at count=11 as tara_index=2', () => {
    // janma=25, some current that gives count=11: janma=1, current=(1+10)%27 = 11
    // janma=1, current=11 (Purva Phalguni): ((11-1+27)%27)+1 = 11 → tara_index=((11-1)%9)+1=1+1=2 → Sampat
    const r = computeTaraMicroRule(1, 11)
    expect(r.count_from_janma).toBe(11)
    expect(r.tara_index).toBe(2)
    expect(r.tara_name).toBe('Sampat')
    expect(r.favorable).toBe(true)
  })

  it('count_from_janma is always in 1..27 for any valid input pair', () => {
    for (let janma = 1; janma <= 27; janma++) {
      for (let current = 1; current <= 27; current++) {
        const r = computeTaraMicroRule(janma, current)
        expect(r.count_from_janma, `janma=${janma}, current=${current}`).toBeGreaterThanOrEqual(1)
        expect(r.count_from_janma, `janma=${janma}, current=${current}`).toBeLessThanOrEqual(27)
        expect(r.tara_index, `janma=${janma}, current=${current}`).toBeGreaterThanOrEqual(1)
        expect(r.tara_index, `janma=${janma}, current=${current}`).toBeLessThanOrEqual(9)
      }
    }
  })

  it('throws a RangeError for nakshatra ids outside 1..27', () => {
    expect(() => computeTaraMicroRule(0, 5)).toThrow()
    expect(() => computeTaraMicroRule(28, 5)).toThrow()
    expect(() => computeTaraMicroRule(5, 0)).toThrow()
    expect(() => computeTaraMicroRule(5, 28)).toThrow()
  })
})

// ── Exported constants ────────────────────────────────────────────────────────────────

describe('ADVERSE_TARA_INDICES and SEVERE_TARA_INDICES constants', () => {
  it('ADVERSE_TARA_INDICES contains exactly {3,5,7} — Vipat, Pratyari, Vadha', () => {
    expect(ADVERSE_TARA_INDICES).toContain(3)
    expect(ADVERSE_TARA_INDICES).toContain(5)
    expect(ADVERSE_TARA_INDICES).toContain(7)
    expect(ADVERSE_TARA_INDICES.size).toBe(3)
  })

  it('SEVERE_TARA_INDICES contains exactly {7} — only Vadha is severe (election disqualifier)', () => {
    // Classical authority: Muhurta Chintamani grades Vadha as the hardest veto.
    // Vipat and Pratyari are caution, not severe.
    expect(SEVERE_TARA_INDICES).toContain(7)
    expect(SEVERE_TARA_INDICES.size).toBe(1)
  })
})

// ── computeJanmaMicroRules (the composite composer called by elect.ts) ────────────────

describe('computeJanmaMicroRules — composite janma micro-rule for one election window', () => {
  const CONTEXT_PURVA_BHADRAPADA: JanmaMicroRuleContext = {
    janma_nakshatra_id: 25,            // Purva Bhadrapada
    janma_tithi_num: 3,                // Shukla Tritiya
    janma_vara_index: 0,               // Sunday (Ravivara)
  }

  it('returns tara_micro_rule with auspicious tārā when election window nakshatra is Kshema-class', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 1,    // Ashwini → count=4, Kshema, favorable
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.tara_micro_rule).not.toBeNull()
    expect(rules.tara_micro_rule!.favorable).toBe(true)
    expect(rules.tara_micro_rule!.tara_name).toBe('Kshema')
    expect(rules.tara_micro_rule!.adverse).toBe(false)
  })

  it('returns tara_micro_rule with adverse tārā and hard_veto=true when window is Vadha', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 4,   // Rohini → count=7, Vadha, severe
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.tara_micro_rule!.adverse).toBe(true)
    expect(rules.tara_micro_rule!.severity).toBe('severe')
    expect(rules.hard_veto).toBe(true)
    expect(rules.hard_veto_reason).toMatch(/Vadha|vadha|tara|veto/)
  })

  it('returns hard_veto=false for non-severe adverse tārā (Vipat, Pratyari)', () => {
    // Vipat: caution, not severe → hard_veto stays false, but tara is flagged adverse
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 27,  // Revati: ((27-25+27)%27)+1 = 3 → Vipat, caution
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.tara_micro_rule!.tara_name).toBe('Vipat')
    expect(rules.tara_micro_rule!.severity).toBe('caution')
    expect(rules.hard_veto).toBe(false)  // caution, not severe
  })

  it('janma_tithi_resonance is true when window tithi matches native janma tithi', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: 3,       // Shukla Tritiya — matches janma tithi
      window_vara_index: null,
    })
    expect(rules.janma_tithi_resonance).toBe(true)
  })

  it('janma_tithi_resonance is false when window tithi does not match native janma tithi', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: 7,       // not Shukla Tritiya
      window_vara_index: null,
    })
    expect(rules.janma_tithi_resonance).toBe(false)
  })

  it('janma_tithi_resonance is null when window tithi is not available', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: null,     // no tithi data
      window_vara_index: null,
    })
    expect(rules.janma_tithi_resonance).toBeNull()
  })

  it('janma_vara_resonance is true when window vara matches native janma vara (Sunday=0)', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: null,
      window_vara_index: 0,      // Sunday — matches janma vara
    })
    expect(rules.janma_vara_resonance).toBe(true)
  })

  it('janma_vara_resonance is false when window vara does not match native janma vara', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: null,
      window_vara_index: 3,      // Wednesday — not Sunday
    })
    expect(rules.janma_vara_resonance).toBe(false)
  })

  it('janma_vara_resonance is null when window vara is not available', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.janma_vara_resonance).toBeNull()
  })

  it('janma_nakshatra_resonance is true when window nakshatra matches janma nakshatra', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 25,   // Purva Bhadrapada — matches janma
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.janma_nakshatra_resonance).toBe(true)
    // Also: tara is Janma (count=1), not favorable, not adverse
    expect(rules.tara_micro_rule!.tara_name).toBe('Janma')
  })

  it('janma_nakshatra_resonance is false when window nakshatra does not match janma nakshatra', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 1,    // Ashwini — not Purva Bhadrapada
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.janma_nakshatra_resonance).toBe(false)
  })

  it('janma_nakshatra_resonance is null when window_nakshatra_id is null', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: null,
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(rules.janma_nakshatra_resonance).toBeNull()
    expect(rules.tara_micro_rule).toBeNull()
  })

  it('resonance_count counts the non-null resonances that are true', () => {
    // All three match: nakshatra=25, tithi=3, vara=0
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 25,
      window_tithi_num: 3,
      window_vara_index: 0,
    })
    // nakshatra matches → janma_nakshatra_resonance=true (tara=Janma, neutral)
    // tithi matches → janma_tithi_resonance=true
    // vara matches → janma_vara_resonance=true
    expect(rules.resonance_count).toBe(3)
  })

  it('resonance_count=0 when no resonances match', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 1,   // Ashwini, not Purva Bhadrapada
      window_tithi_num: 7,      // not Shukla Tritiya
      window_vara_index: 3,     // Wednesday, not Sunday
    })
    expect(rules.janma_nakshatra_resonance).toBe(false)
    expect(rules.janma_tithi_resonance).toBe(false)
    expect(rules.janma_vara_resonance).toBe(false)
    expect(rules.resonance_count).toBe(0)
  })

  it('result carries a classical citation string (non-empty)', () => {
    const rules = computeJanmaMicroRules(CONTEXT_PURVA_BHADRAPADA, {
      window_nakshatra_id: 1,
      window_tithi_num: null,
      window_vara_index: null,
    })
    expect(typeof rules.citation).toBe('string')
    expect(rules.citation.length).toBeGreaterThan(10)
  })

  it('null context (no janma anchor) produces an honest null result from applyJanmaMicroRulesOrNull', () => {
    // The caller must be able to pass null for the context (no janma anchor available)
    // and receive null back — never a fabricated result. Uses the top-level import.
    const w = { window_nakshatra_id: 1, window_tithi_num: 1, window_vara_index: 1 }
    expect(applyJanmaMicroRulesOrNull(null, w)).toBeNull()
    expect(applyJanmaMicroRulesOrNull(undefined, w)).toBeNull()
  })
})
