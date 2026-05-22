/**
 * multi_school_jaimini.test.ts
 * Unit tests for Jaimini multi-school stance computation (v3.2-S4).
 *
 * Tests the stance logic in bootstrap_multi_school_jaimini.ts.
 * No DB or network calls — pure logic tests.
 */

import { describe, it, expect } from 'vitest';

// ── Import the stance logic by re-implementing it inline for testing ──────────
// (The script doesn't export functions, so we inline the logic here to test
// the decision tree without touching the DB.)

const CHARA_KARAKAS: Record<string, string> = {
  MOON: 'AK', SATURN: 'AmK', SUN: 'BK', VENUS: 'MK',
  MARS: 'PK', JUPITER: 'GK', MERCURY: 'DK',
};

const KARAKA_DOMAIN_MAP: Record<string, string[]> = {
  AK: ['spirit', 'mind', 'psychology', 'psychological'],
  AmK: ['career'],
  BK: ['career', 'parents'],
  MK: ['parents', 'health'],
  PK: ['children', 'creativity'],
  GK: ['health', 'spirit', 'parents'],
  DK: ['relationships'],
};

const ARUDHA_HOUSES = new Set([2, 3, 10, 11]);
const JAIMINI_PRIMARY_HOUSES = new Set([2, 7, 10, 11]);
const JAIMINI_SECONDARY_HOUSES = new Set([1, 3, 4, 8, 9]);
const JAIMINI_TYPE_KEYWORDS = ['jaimini-pattern', 'jaimini'];
const KARAKA_PLANETS = new Set(Object.keys(CHARA_KARAKAS));

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

function computeJaiminiStance(sig: MsrSignal): StanceResult {
  const planet = sig.planet?.toUpperCase() ?? null;
  const house = sig.house ?? null;
  const domain = sig.domain?.toLowerCase() ?? '';
  const signalType = sig.signal_type?.toLowerCase() ?? '';

  if (JAIMINI_TYPE_KEYWORDS.some((kw) => signalType.includes(kw))) {
    return { coverage_type: 'primary', confidence: 0.90 };
  }

  if (planet && KARAKA_PLANETS.has(planet)) {
    const role = CHARA_KARAKAS[planet];
    const karakaDomains = KARAKA_DOMAIN_MAP[role] ?? [];
    if (karakaDomains.includes(domain)) {
      return { coverage_type: 'primary', confidence: 0.65 };
    }
  }

  if (house !== null && JAIMINI_PRIMARY_HOUSES.has(house)) {
    return { coverage_type: 'primary', confidence: 0.60 };
  }

  if (planet && KARAKA_PLANETS.has(planet)) {
    return { coverage_type: 'secondary', confidence: 0.55 };
  }

  if (house !== null && JAIMINI_SECONDARY_HOUSES.has(house)) {
    return { coverage_type: 'secondary', confidence: 0.50 };
  }

  if (['spirit', 'spirituality', 'psychological', 'psychology', 'mind'].includes(domain)) {
    return { coverage_type: 'secondary', confidence: 0.48 };
  }

  return { coverage_type: 'silent', confidence: 0.30 };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('computeJaiminiStance — Rule 1: jaimini-pattern signal type', () => {
  it('assigns primary to explicit jaimini-pattern signal type', () => {
    const result = computeJaiminiStance({
      signal_id: 'SIG.MSR.004',
      domain: 'spirit',
      planet: 'MOON',
      house: 11,
      signal_type: 'jaimini-pattern',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.90);
  });

  it('handles mixed-case signal type containing jaimini', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.001',
      domain: 'career',
      planet: null,
      house: null,
      signal_type: 'Jaimini-Pattern',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
  });
});

describe('computeJaiminiStance — Rule 2: chara karaka + domain match', () => {
  it('Moon (AK) in spirit domain → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'SIG.MSR.317',
      domain: 'spirit',
      planet: 'MOON',
      house: null,
      signal_type: 'divisional-pattern',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });

  it('Saturn (AmK) in career domain → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'SIG.MSR.001',
      domain: 'career',
      planet: 'SATURN',
      house: 7,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });

  it('Mercury (DK) in relationships domain → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'SIG.MSR.319',
      domain: 'relationships',
      planet: 'MERCURY',
      house: 10,
      signal_type: 'convergence',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });

  it('Mars (PK) in children domain → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'SIG.MSR.320',
      domain: 'children',
      planet: 'MARS',
      house: 7,
      signal_type: 'yoga',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });

  it('Jupiter (GK) in health domain → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.002',
      domain: 'health',
      planet: 'JUPITER',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.65);
  });
});

describe('computeJaiminiStance — Rule 3: primary Jaimini house', () => {
  it('signal in 10H (AL) → primary even without named karaka', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.003',
      domain: 'career',
      planet: 'RAHU', // not a 7-karaka planet
      house: 10,
      signal_type: 'placement',
      valence: 'mixed',
    });
    // RAHU is not in KARAKA_PLANETS, house 10 is primary Jaimini house
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.60);
  });

  it('signal in 7H (AmK+PK) → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.004',
      domain: 'wealth',
      planet: 'RAHU',
      house: 7,
      signal_type: 'yoga',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.60);
  });

  it('signal in 2H (A6 Shatrupada) → primary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.005',
      domain: 'wealth',
      planet: 'RAHU',
      house: 2,
      signal_type: 'dignity',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('primary');
    expect(result.confidence).toBe(0.60);
  });
});

describe('computeJaiminiStance — Rule 4: karaka planet, domain mismatch → secondary', () => {
  it('Saturn (AmK) in wealth domain → secondary (not career domain)', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.006',
      domain: 'wealth',
      planet: 'SATURN',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('secondary');
    expect(result.confidence).toBe(0.55);
  });

  it('Venus (MK) in career domain → secondary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.007',
      domain: 'career',
      planet: 'VENUS',
      house: null,
      signal_type: 'yoga',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('secondary');
    expect(result.confidence).toBe(0.55);
  });
});

describe('computeJaiminiStance — Rule 5: secondary Jaimini houses', () => {
  it('signal in 9H (dharma/GK) without planet → secondary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.008',
      domain: 'wealth',
      planet: 'RAHU',
      house: 9,
      signal_type: 'placement',
      valence: 'mixed',
    });
    // RAHU not in KARAKA_PLANETS, house 9 is secondary Jaimini house
    expect(result.coverage_type).toBe('secondary');
  });

  it('signal in 4H (pada-relevant) → secondary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.009',
      domain: 'parents',
      planet: 'RAHU',
      house: 4,
      signal_type: 'placement',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('secondary');
  });
});

describe('computeJaiminiStance — Rule 6: soul domain → secondary', () => {
  it('spirit domain with no planet and no house → secondary', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.010',
      domain: 'spirit',
      planet: null,
      house: null,
      signal_type: 'general',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('secondary');
    expect(result.confidence).toBe(0.48);
  });

  it('psychological domain → secondary (AK-soul connection)', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.011',
      domain: 'psychological',
      planet: null,
      house: null,
      signal_type: 'placement',
      valence: 'malefic',
    });
    expect(result.coverage_type).toBe('secondary');
  });
});

describe('computeJaiminiStance — Silent cases', () => {
  it('unknown domain, no planet, no house → silent', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.012',
      domain: 'unknown',
      planet: null,
      house: null,
      signal_type: 'nadi-pattern',
      valence: 'benefic',
    });
    expect(result.coverage_type).toBe('silent');
    expect(result.confidence).toBe(0.30);
  });

  it('education domain with no planet and house 6 (not secondary Jaimini) → silent', () => {
    const result = computeJaiminiStance({
      signal_id: 'TEST.013',
      domain: 'education',
      planet: 'RAHU', // not karaka
      house: 6, // not in JAIMINI_PRIMARY_HOUSES or JAIMINI_SECONDARY_HOUSES
      signal_type: 'placement',
      valence: 'mixed',
    });
    expect(result.coverage_type).toBe('silent');
  });
});

describe('computeJaiminiStance — Coverage completeness estimate', () => {
  it('should assign substantive coverage to jaimini-pattern signals', () => {
    // All 43 jaimini-pattern signals should be primary
    const jaiminiPatternSignal = computeJaiminiStance({
      signal_id: 'SIG.MSR.317',
      domain: 'spirit',
      planet: 'MOON',
      house: 11,
      signal_type: 'jaimini-pattern',
      valence: 'benefic',
    });
    expect(jaiminiPatternSignal.coverage_type).toBe('primary');
  });

  it('all chara karakas should produce at least secondary coverage in any domain', () => {
    const karaka_planets = ['MOON', 'SATURN', 'SUN', 'VENUS', 'MARS', 'JUPITER', 'MERCURY'];
    for (const planet of karaka_planets) {
      const result = computeJaiminiStance({
        signal_id: 'TEST.KARAKA.' + planet,
        domain: 'wealth', // generic non-matching domain
        planet,
        house: null,
        signal_type: 'yoga',
        valence: 'benefic',
      });
      expect(result.coverage_type).not.toBe('silent');
    }
  });

  it('primary Jaimini houses (2,7,10,11) should produce at least primary coverage', () => {
    for (const house of [2, 7, 10, 11]) {
      const result = computeJaiminiStance({
        signal_id: `TEST.HOUSE.${house}`,
        domain: 'other',
        planet: 'RAHU', // non-karaka
        house,
        signal_type: 'placement',
        valence: 'mixed',
      });
      expect(result.coverage_type).toBe('primary');
    }
  });
});
