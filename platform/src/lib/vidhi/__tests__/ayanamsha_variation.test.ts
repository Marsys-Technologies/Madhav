import { describe, it, expect } from 'vitest';
import {
  REAL_AYANAMSHAS,
  AYANAMSHA_SENTINEL,
  AYANAMSHA_AGREEMENT_DENOMINATOR,
  computeAyanamshaAgreement,
  ayanamshaFamilyKey,
  type AyanamshaRead,
} from '@/lib/vidhi/ayanamsha_variation';

describe('cross-ayanamsha agreement engine (EL-27 + EL-56)', () => {
  it('scores over the 5 REAL ayanamshas — the INVARIANT sentinel is excluded (n/5, not n/6)', () => {
    expect(REAL_AYANAMSHAS).toHaveLength(5);
    expect(AYANAMSHA_AGREEMENT_DENOMINATOR).toBe(5);
    expect((REAL_AYANAMSHAS as readonly string[])).not.toContain(AYANAMSHA_SENTINEL);
  });

  it('unanimous reads compress to 5/5', () => {
    const reads: AyanamshaRead[] = REAL_AYANAMSHAS.map((a) => ({
      ayanamsha: a,
      dignity_state: 'friend',
      house: 2,
      sign: 'Taurus',
      vargottama: false,
    }));
    const v = computeAyanamshaAgreement('JUPITER', reads);
    expect(v.ayanamsha_agreement).toBe('5/5');
    expect(v.unanimous).toBe(true);
    expect(v.dignity_delta).toEqual([]);
    expect(v.house_shift).toEqual([]);
    expect(v.divergent_ayanamshas).toEqual([]);
  });

  it('a near-cusp house/dignity flip under ONE ayanamsha surfaces as disagreement (not collapsed away)', () => {
    const reads: AyanamshaRead[] = REAL_AYANAMSHAS.map((a) => ({
      ayanamsha: a,
      dignity_state: a === 'raman' ? 'enemy' : 'friend',
      house: a === 'raman' ? 3 : 2,
      sign: a === 'raman' ? 'Gemini' : 'Taurus',
      vargottama: false,
    }));
    const v = computeAyanamshaAgreement('SATURN', reads);
    expect(v.ayanamsha_agreement).toBe('4/5');
    expect(v.unanimous).toBe(false);
    expect(v.divergent_ayanamshas).toEqual(['raman']);
    expect(v.dignity_delta).toEqual(expect.arrayContaining(['friend', 'enemy']));
    expect(v.house_shift).toEqual([2, 3]);
  });

  it('a missing read shrinks the numerator honestly, never back-filled — denominator stays 5', () => {
    const reads: AyanamshaRead[] = REAL_AYANAMSHAS.filter((a) => a !== 'true_chitra').map((a) => ({
      ayanamsha: a,
      dignity_state: 'own',
      house: 10,
      sign: 'Capricorn',
      vargottama: true,
    }));
    const v = computeAyanamshaAgreement('SUN', reads);
    expect(v.agreement_denominator).toBe(5);
    expect(v.missing_ayanamshas).toEqual(['true_chitra']);
    expect(v.unanimous).toBe(false); // a missing read is not unanimous agreement
  });

  it('family_key folds the agreement in so a naive dedup cannot flatten disagreement (EL-56)', () => {
    const agree = ayanamshaFamilyKey('JUPITER', 'dignity', '5/5');
    const disagree = ayanamshaFamilyKey('JUPITER', 'dignity', '3/5');
    // Same graha × signal_type, but the agreement score keeps agreeing/disagreeing rows distinct.
    expect(agree).not.toBe(disagree);
    expect(agree).toContain('ayanamsha_agreement=5/5');
  });

  it('is deterministic — identical input yields byte-identical output', () => {
    const reads: AyanamshaRead[] = REAL_AYANAMSHAS.map((a) => ({
      ayanamsha: a,
      dignity_state: 'neutral',
      house: 7,
      sign: 'Libra',
      vargottama: false,
    }));
    expect(JSON.stringify(computeAyanamshaAgreement('MARS', reads))).toBe(
      JSON.stringify(computeAyanamshaAgreement('MARS', reads)),
    );
  });
});
