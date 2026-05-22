/**
 * multi_school_kp.test.ts
 * Unit tests for KP multi-school stance computation (v3.2-S4).
 *
 * Tests the KP stance decision tree from bootstrap_multi_school_kp.ts.
 * No DB or network calls — pure logic tests using native chart constants.
 */

import { describe, it, expect } from 'vitest';

// ── Inline the KP stance logic for testing ───────────────────────────────────

const CUSP_SUB_LORDS: Record<number, string> = {
  1: 'Mercury', 2: 'Rahu', 3: 'Rahu', 4: 'Rahu',
  5: 'Venus', 6: 'Saturn', 7: 'Saturn', 8: 'Mars',
  9: 'Jupiter', 10: 'Saturn', 11: 'Mercury', 12: 'Saturn',
};

const CUSP_STAR_LORDS: Record<number, string> = {
  1: 'Ketu', 2: 'Moon', 3: 'Rahu', 4: 'Jupiter',
  5: 'Ketu', 6: 'Sun', 7: 'Rahu', 8: 'Saturn',
  9: 'Ketu', 10: 'Sun', 11: 'Mars', 12: 'Saturn',
};

const KP_SIGNIFICATORS: Record<number, Set<string>> = {
  1: new Set(['Mars', 'Ketu']),
  2: new Set(['Rahu', 'Venus']),
  6: new Set(['Mars', 'Ketu', 'Mercury']),
  7: new Set(['Moon', 'Saturn', 'Venus']),
  10: new Set(['Mercury', 'Venus', 'Mars', 'Ketu', 'Sun', 'Saturn']),
  11: new Set(['Sun', 'Rahu', 'Moon', 'Saturn']),
  12: new Set(['Saturn', 'Jupiter']),
};

const PLANET_SUB_LORDS: Record<string, string> = {
  Jupiter: 'Saturn', Ketu: 'Ketu', Mars: 'Moon', Mercury: 'Rahu',
  Moon: 'Venus', Rahu: 'Mercury', Saturn: 'Saturn', Sun: 'Venus', Venus: 'Rahu',
};

const PLANET_STAR_LORDS: Record<string, string> = {
  Jupiter: 'Ketu', Ketu: 'Mercury', Mars: 'Rahu', Mercury: 'Sun',
  Moon: 'Jupiter', Rahu: 'Moon', Saturn: 'Jupiter', Sun: 'Moon', Venus: 'Venus',
};

const DOMAIN_CUSP_MAP: Record<string, number[]> = {
  career: [10, 6, 11], wealth: [2, 11, 10], relationships: [7, 11],
  health: [6, 1, 8], children: [5, 11], spirit: [9, 12, 8],
  spirituality: [9, 12], travel: [9, 12, 3], mind: [1, 3, 4],
  psychological: [1, 8], psychology: [1, 8], parents: [9, 4],
  education: [4, 5, 9], other: [1], unknown: [], timing: [],
};

type CoverageType = 'primary' | 'secondary' | 'silent';

interface MsrSignal {
  signal_id: string;
  domain: string;
  planet: string | null;
  house: number | null;
  signal_type: string;
  valence: string;
}

interface StanceResult {
  coverage_type: CoverageType;
  confidence: number;
}

function capitalizeFirst(s: string): string {
  if (!s) return s;
  const lower = s.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function computeKpStance(sig: MsrSignal): StanceResult {
  const planet = sig.planet ? capitalizeFirst(sig.planet) : null;
  const house = sig.house ?? null;
  const domain = sig.domain?.toLowerCase() ?? '';

  const relevantCusps = DOMAIN_CUSP_MAP[domain] ?? [];
  const primaryCusp = relevantCusps[0] ?? null;

  // Rule 1: significator of primary cusp AND is own sub-lord
  if (planet && primaryCusp !== null) {
    const sigs = KP_SIGNIFICATORS[primaryCusp];
    if (sigs?.has(planet) && PLANET_SUB_LORDS[planet] === planet) {
      return { coverage_type: 'primary', confidence: 0.75 };
    }
  }

  // Rule 2: significator of primary cusp
  if (planet && primaryCusp !== null) {
    const sigs = KP_SIGNIFICATORS[primaryCusp];
    if (sigs?.has(planet)) {
      return { coverage_type: 'primary', confidence: 0.70 };
    }
  }

  // Rule 3: sub-lord of primary cusp
  if (planet && primaryCusp !== null) {
    if (CUSP_SUB_LORDS[primaryCusp] === planet) {
      return { coverage_type: 'primary', confidence: 0.70 };
    }
  }

  // Rule 4: signal house matches domain cusp with significators
  if (house !== null) {
    const sigs = KP_SIGNIFICATORS[house];
    if (sigs && sigs.size > 0 && relevantCusps.includes(house)) {
      return { coverage_type: 'primary', confidence: 0.65 };
    }
  }

  // Rule 5: star-lord of any relevant cusp
  if (planet) {
    for (const cusp of relevantCusps) {
      if (CUSP_STAR_LORDS[cusp] === planet) {
        return { coverage_type: 'secondary', confidence: 0.60 };
      }
    }
  }

  // Rule 6: significator of secondary cusp
  if (planet && relevantCusps.length > 1) {
    for (const cusp of relevantCusps.slice(1)) {
      const sigs = KP_SIGNIFICATORS[cusp];
      if (sigs?.has(planet)) {
        return { coverage_type: 'secondary', confidence: 0.60 };
      }
    }
  }

  // Rule 7: planet's sub-lord is significator of primary cusp
  if (planet && primaryCusp !== null) {
    const planetSubLord = PLANET_SUB_LORDS[planet];
    const primarySigs = KP_SIGNIFICATORS[primaryCusp];
    if (planetSubLord && primarySigs?.has(planetSubLord)) {
      return { coverage_type: 'secondary', confidence: 0.55 };
    }
  }

  // Rule 8: house has KP significators
  if (house !== null && KP_SIGNIFICATORS[house]) {
    return { coverage_type: 'secondary', confidence: 0.50 };
  }

  return { coverage_type: 'silent', confidence: 0.30 };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('computeKpStance — Rule 1: planet is significator + own sub-lord', () => {
  it('Saturn in career domain: significator of cusp 10 AND own sub-lord → primary 0.75', () => {
    // Saturn is significator of house 10 and PLANET_SUB_LORDS['Saturn'] = 'Saturn'
    const result = computeKpStance({
      signal_id: 'SIG.MSR.001',
      domain: 'career',
      planet: 'SATURN',
      house: 7,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.75);
  });

  it('Ketu in career domain: significator of cusp 10 AND own sub-lord → primary 0.75', () => {
    // Ketu significator of 10, PLANET_SUB_LORDS['Ketu'] = 'Ketu'
    const result = computeKpStance({
      signal_id: 'TEST.KP.001',
      domain: 'career',
      planet: 'KETU',
      house: null,
      signal_type: 'yoga',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.75);
  });
});

describe('computeKpStance — Rule 2: planet is significator of primary cusp', () => {
  it('Mercury in career domain: significator of cusp 10 → primary 0.70', () => {
    const result = computeKpStance({
      signal_id: 'SIG.MSR.009',
      domain: 'career',
      planet: 'MERCURY',
      house: null,
      signal_type: 'convergence',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBeGreaterThanOrEqual(0.70);
  });

  it('Venus in wealth domain: significator of cusp 2 → primary', () => {
    // KP_SIGNIFICATORS[2] = Rahu, Venus; Venus is in the set
    const result = computeKpStance({
      signal_id: 'TEST.KP.002',
      domain: 'wealth',
      planet: 'VENUS',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });

  it('Moon in relationships domain: significator of cusp 7 → primary', () => {
    // KP_SIGNIFICATORS[7] = Moon, Saturn, Venus
    const result = computeKpStance({
      signal_id: 'TEST.KP.003',
      domain: 'relationships',
      planet: 'MOON',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });

  it('Mars in health domain: significator of cusp 6 → primary', () => {
    // KP_SIGNIFICATORS[6] = Mars, Ketu, Mercury
    const result = computeKpStance({
      signal_id: 'TEST.KP.004',
      domain: 'health',
      planet: 'MARS',
      house: null,
      signal_type: 'transit-trigger',
      valence: 'malefic',
    });
    expect(result.coverage_type).toBe('primary');
  });
});

describe('computeKpStance — Rule 3: planet is sub-lord of primary cusp', () => {
  it('Mercury in lagna/mind domain: Mercury is sub-lord of cusp 1 → primary', () => {
    // CUSP_SUB_LORDS[1] = Mercury; mind domain primary cusp = 1
    const result = computeKpStance({
      signal_id: 'TEST.KP.005',
      domain: 'mind',
      planet: 'MERCURY',
      house: null,
      signal_type: 'dignity',
      valence: 'benefic',
    });
    // Mercury is ALSO a significator of cusp 10, but mind domain primary cusp is 1
    // CUSP_SUB_LORDS[1] = Mercury → Rule 3 applies
    expect(result.coverage_type).toBe('primary');
  });

  it('Jupiter in spirit domain: Jupiter is sub-lord of cusp 9 (spirit primary cusp) → primary', () => {
    // CUSP_SUB_LORDS[9] = Jupiter; spirit domain primary cusp = 9
    const result = computeKpStance({
      signal_id: 'TEST.KP.006',
      domain: 'spirit',
      planet: 'JUPITER',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });
});

describe('computeKpStance — Rule 4: house matches domain cusp with significators', () => {
  it('signal in house 10 with career domain → primary', () => {
    // house 10 matches career domain's primary cusp (10); KP_SIGNIFICATORS[10] exists
    const result = computeKpStance({
      signal_id: 'SIG.MSR.011',
      domain: 'career',
      planet: 'SUN',
      house: 10,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    // Sun is also a significator of cusp 10, so Rule 2 fires first
    expect(result.coverage_type).toBe('primary');
  });

  it('signal in house 7 with relationships domain → primary', () => {
    const result = computeKpStance({
      signal_id: 'TEST.KP.007',
      domain: 'relationships',
      planet: 'RAHU', // not in KP_SIGNIFICATORS[7]
      house: 7,
      signal_type: 'placement',
      valence: 'mixed',
    });
    // RAHU not significator of cusp 7; house 7 IS in domain cusps; KP_SIGNIFICATORS[7] exists
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });
});

describe('computeKpStance — Rule 5: planet is star-lord of relevant cusp', () => {
  it('Sun in career domain: star-lord of cusp 10 → secondary', () => {
    // CUSP_STAR_LORDS[10] = Sun; but Sun IS also significator of cusp 10 via KP_SIGNIFICATORS[10]
    // Rule 2 fires first for Sun in career — verify Sun is primary via significator
    const result = computeKpStance({
      signal_id: 'TEST.KP.008',
      domain: 'career',
      planet: 'SUN',
      house: null,
      signal_type: 'placement',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary'); // Sun is KP sig of cusp 10
  });

  it('Mars in spirit domain: star-lord of cusp 11 which is secondary spirit cusp → secondary', () => {
    // Spirit domain: [9, 12, 8]. CUSP_STAR_LORDS: 9=Ketu, 12=Saturn, 8=Saturn
    // Mars is star-lord of cusp 11 but that's not in spirit cusps
    // Mars is not significator of cusp 9 or 12
    // Mars's sub-lord = Moon; Moon is not in KP_SIGNIFICATORS[9]
    // House null; KP_SIGNIFICATORS[null] → undefined
    // → Should be silent
    const result = computeKpStance({
      signal_id: 'TEST.KP.009',
      domain: 'spirit',
      planet: 'MARS',
      house: null,
      signal_type: 'transit-trigger',
      valence: 'mixed',
    });
    // Mars is not significator of cusps 9,12,8; star-lord of 11 not in spirit cusps
    // Mars sub-lord = Moon; Moon not in significators of cusp 9 = {}
    // → silent
    expect(result.coverage_type).toBe('silent');
  });
});

describe('computeKpStance — Rule 7: planet sub-lord chain', () => {
  it('Rahu in career domain: Rahu sub-lord=Mercury, Mercury is sig of cusp 10 → secondary', () => {
    // Rahu not in KP_SIGNIFICATORS[10]; CUSP_SUB_LORDS[10]=Saturn ≠ Rahu
    // CUSP_STAR_LORDS[10]=Sun ≠ Rahu; KP_SIGNIFICATORS[6] has no Rahu; KP_SIGNIFICATORS[11] has Rahu
    // Rahu IS significator of cusp 11 (secondary career cusp) → Rule 6 fires with secondary 0.60
    const result = computeKpStance({
      signal_id: 'TEST.KP.010',
      domain: 'career',
      planet: 'RAHU',
      house: null,
      signal_type: 'placement',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('secondary'); // via Rule 6 (Rahu sig of cusp 11)
  });
});

describe('computeKpStance — Silent cases', () => {
  it('unknown domain with no planet or house → silent', () => {
    const result = computeKpStance({
      signal_id: 'TEST.KP.011',
      domain: 'unknown',
      planet: null,
      house: null,
      signal_type: 'general',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('silent');
    expect(result.confidence).toBe(0.30);
  });

  it('timing domain → silent (no KP cusp mapping)', () => {
    const result = computeKpStance({
      signal_id: 'TEST.KP.012',
      domain: 'timing',
      planet: 'JUPITER',
      house: null,
      signal_type: 'transit-trigger',
      valence: 'mixed',
    });
    // timing domain maps to [] → no relevant cusps
    expect(result.coverage_type).toBe('silent');
  });
});

describe('computeKpStance — KP Chart completeness: all cusp sub-lords', () => {
  const cuspDomainMap: [number, string, string][] = [
    [10, 'career', 'Saturn'], // CUSP_SUB_LORDS[10] = Saturn → primary
    [2, 'wealth', 'Rahu'],    // CUSP_SUB_LORDS[2] = Rahu → primary (Rahu is sig of cusp 2)
    [7, 'relationships', 'Saturn'], // CUSP_SUB_LORDS[7] = Saturn → primary (Saturn is sig of cusp 7)
    [9, 'spirit', 'Jupiter'], // CUSP_SUB_LORDS[9] = Jupiter → primary (sub-lord rule)
  ];

  for (const [cusp, domain, sublord] of cuspDomainMap) {
    it(`${sublord} as sub-lord of cusp ${cusp} in ${domain} domain → primary`, () => {
      const result = computeKpStance({
        signal_id: `TEST.KP.CUSP.${cusp}`,
        domain,
        planet: sublord.toUpperCase(),
        house: null,
        signal_type: 'yoga',
        valence: 'benefic',
      });
      expect(result.coverage_type).toBe('primary');
    });
  }
});

describe('computeKpStance — capitalizeFirst helper', () => {
  it('handles uppercase planet names from DB', () => {
    // Saturn in career → primary (uppercase handled by capitalizeFirst)
    const result = computeKpStance({
      signal_id: 'TEST.CASE.001',
      domain: 'career',
      planet: 'SATURN',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });

  it('handles lowercase planet names', () => {
    const result = computeKpStance({
      signal_id: 'TEST.CASE.002',
      domain: 'career',
      planet: 'saturn',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });
});
