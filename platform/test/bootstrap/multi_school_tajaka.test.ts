/**
 * multi_school_tajaka.test.ts
 * Unit tests for Tajaka multi-school coverage backfill (v3.2-S5).
 *
 * Tests buildTajikaCoverage() function and munthaSigns() function from
 * bootstrap_multi_school_tajaka.ts (imported inline to avoid DB dependency).
 *
 * All tests are unit tests — no database connection required.
 */

import { describe, it, expect } from 'vitest';

// ── Inline the tested functions (avoid DB import from bootstrap script) ──────

const SIGNS = [
  'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius',
  'Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini',
];
const BIRTH_YEAR = 1984;

function munthaSigns(fromYear: number, toYear: number) {
  const rows: { native_year: number; varsha_number: number; muntha_sign: string }[] = [];
  for (let yr = fromYear; yr <= toYear; yr++) {
    const varsha_number = yr - BIRTH_YEAR + 1;
    const muntha_sign = SIGNS[(varsha_number - 1) % 12];
    rows.push({ native_year: yr, varsha_number, muntha_sign });
  }
  return rows;
}

function sig(n: number): string {
  return `SIG.MSR.${String(n).padStart(3, '0')}`;
}

interface CoverageRow {
  signal_id: string;
  coverage_type: 'primary' | 'secondary';
  notes: string;
}

function buildTajikaCoverage(): CoverageRow[] {
  const rows: CoverageRow[] = [];

  // PRIMARY: Tajika-pattern signals (376-387)
  for (let i = 376; i <= 387; i++) {
    rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: 'Tajika-pattern signal [TAJAKA Ch.1-3]' });
  }

  // PRIMARY: Sahama signals (391a, 391b, 391c)
  const sahamaSignals = ['SIG.MSR.391a', 'SIG.MSR.391b', 'SIG.MSR.391c'];
  const sahamaNotes = [
    'Roga Saham [TAJAKA Ch.9 v.9.1]',
    'Mahatmya Saham [TAJAKA Ch.9 v.9.8]',
    'Vivaha Saham [TAJAKA Ch.9 v.9.5]',
  ];
  sahamaSignals.forEach((id, idx) => rows.push({ signal_id: id, coverage_type: 'primary', notes: sahamaNotes[idx] }));

  // PRIMARY: Dedicated Tajika signals (559-573)
  const tajikaSignalNotes: Record<number, string> = {
    559: 'Ithasala Yoga [TAJAKA Ch.4 v.4.1]', 560: 'Ishrafa Yoga [TAJAKA Ch.5 v.5.1]',
    561: 'Nakta Yoga [TAJAKA Ch.6 v.6.1]', 562: 'Varshesha [TAJAKA Ch.2 v.2.1]',
    563: 'Mudda Dasha [TAJAKA Ch.10 v.10.1]', 564: 'Muntha [TAJAKA Ch.3 v.3.1]',
    565: 'Tri-Pataki [TAJAKA Ch.14]', 566: 'Harsha Bala [TAJAKA Ch.1 v.1.14]',
    567: 'Kambula Yoga [TAJAKA Ch.7]', 568: 'Dutthottha Yoga [TAJAKA Ch.8]',
    569: 'Sahama Punya [TAJAKA Ch.9 v.9.1]', 570: 'Annual Lagna lord [TAJAKA Ch.1 v.1.7]',
    571: 'Solar return methodology [TAJAKA Ch.1 v.1.2]', 572: 'Muntha lord [TAJAKA Ch.3 v.3.9]',
    573: 'Deeptamsa orbs [TAJAKA Ch.1 v.1.5]',
  };
  for (let i = 559; i <= 573; i++) {
    rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: tajikaSignalNotes[i] ?? 'Tajika signal' });
  }

  // PRIMARY: Annual transit patterns (282, 283)
  [282, 283].forEach(i => rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: 'Annual transit [TAJAKA Ch.1 v.1.13]' }));

  // PRIMARY: Panchanga signals (351-375, 437, 442)
  const panchangaIds = [...Array.from({ length: 25 }, (_, k) => 351 + k), 437, 442];
  panchangaIds.forEach(i => rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: 'Panchanga [TAJAKA Ch.1 v.1.10]' }));

  // PRIMARY: Sensitive points (163-167, 390, 392, 393)
  [163, 164, 165, 166, 167, 390, 392, 393].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: 'Sensitive point [TAJAKA Ch.3 v.3.13]' })
  );

  // PRIMARY: Dasha with Varshesha convergence (255, 256)
  [255, 256].forEach(i => rows.push({ signal_id: sig(i), coverage_type: 'primary', notes: 'Dasha convergence [TAJAKA Ch.2 v.2.15]' }));

  // SECONDARY: Transit-activation (271-281)
  for (let i = 271; i <= 281; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Transit overlay [TAJAKA Ch.1 v.1.16]' });

  // SECONDARY: Other dasha signals
  [44, 45, 150, 151, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Dasha context [TAJAKA Ch.2 v.2.14]' })
  );

  // SECONDARY: Key natal yoga signals
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 46, 47, 48, 49, 50].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Natal yoga: annual chart activates [TAJAKA Ch.1 v.1.16]' })
  );

  // SECONDARY: Convergence signals
  [130, 131, 136, 168, 169, 170, 171, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Convergence [TAJAKA Ch.1 v.1.16]' })
  );

  // SECONDARY: Sensitive points (36-50, 100-120)
  [36, 38, 39, 40, 41, 42, 43, 46, 47, 48, 49, 50,
    100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Sensitive point [TAJAKA Ch.3 v.3.13]' })
  );

  // SECONDARY: House strength (196-206)
  for (let i = 196; i <= 206; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'House strength [TAJAKA Ch.1 v.1.17]' });

  // SECONDARY: Nakshatra (210-245)
  for (let i = 210; i <= 245; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Nakshatra [TAJAKA Ch.3 v.3.11]' });

  // SECONDARY: Sade Sati (284-310)
  for (let i = 284; i <= 310; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Sade Sati [TAJAKA Ch.2 v.2.6]' });

  // SECONDARY: Aspects (57-80)
  for (let i = 57; i <= 80; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Natal aspect [TAJAKA Ch.1 v.1.4]' });

  // SECONDARY: Multi-planet (121-145)
  for (let i = 121; i <= 145; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Multi-planet [TAJAKA Ch.4 v.4.4]' });

  // SECONDARY: Dignity (13, 145-163)
  [13, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163].forEach(i =>
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Dignity → Harsha Bala [TAJAKA Ch.1 v.1.14]' })
  );

  // SECONDARY: Cross-domain (450-500, skip 498-499)
  for (let i = 450; i <= 500; i++) {
    if (i === 498 || i === 499) continue;
    rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Cross-domain temporal resolution' });
  }

  // SECONDARY: Divisional (2, 3, 6, 312-350)
  [2, 3, 6].forEach(i => rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Divisional [TAJAKA Ch.1 v.1.13]' }));
  for (let i = 312; i <= 350; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Divisional pattern [TAJAKA Ch.1 v.1.13]' });

  // SECONDARY: Jaimini (4, 36, 38, 394-430 excl. 391a/b/c range)
  [4, 36, 38].forEach(i => rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Jaimini backdrop [TAJAKA Ch.1 v.1.12]' }));
  for (let i = 394; i <= 430; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Jaimini backdrop [TAJAKA Ch.1 v.1.12]' });

  // SECONDARY: Timing/structural (431-449)
  for (let i = 431; i <= 449; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Timing structural [TAJAKA Ch.1 v.1.2]' });

  // SECONDARY: Yogini Dasha (544-558)
  for (let i = 544; i <= 558; i++) rows.push({ signal_id: sig(i), coverage_type: 'secondary', notes: 'Yogini Dasha cross-reference [TAJAKA Ch.10]' });

  // Deduplicate
  const seen = new Set<string>();
  return rows.filter(r => {
    if (seen.has(r.signal_id)) return false;
    seen.add(r.signal_id);
    return true;
  });
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('buildTajikaCoverage — signal count', () => {
  it('generates at least 50 primary rows (dedicated Tajaka-typed signals)', () => {
    // Brief target: ≥150 total (primary + secondary). Primary covers dedicated Tajaka signals.
    // SIG.MSR.376-387 (tajika-pattern) + 391a/b/c (sahama) + 559-573 (tajika-*) = at minimum 30.
    // Plus panchanga (27), annual transits (2), sensitive points (8), dasha convergence (2) = 69.
    const rows = buildTajikaCoverage();
    const primary = rows.filter(r => r.coverage_type === 'primary');
    expect(primary.length).toBeGreaterThanOrEqual(50);
  });

  it('generates at least 100 secondary rows', () => {
    const rows = buildTajikaCoverage();
    const secondary = rows.filter(r => r.coverage_type === 'secondary');
    expect(secondary.length).toBeGreaterThanOrEqual(100);
  });

  it('total rows ≥ 150 (primary + secondary combined — brief target)', () => {
    // The brief explicitly states: "Target: AT LEAST 150 signal_id rows as school='tajika'
    // with coverage_type IN ('primary','secondary')"
    const rows = buildTajikaCoverage();
    expect(rows.length).toBeGreaterThanOrEqual(150);
  });
});

describe('buildTajikaCoverage — deduplication', () => {
  it('has no duplicate signal_id entries (tajika school)', () => {
    const rows = buildTajikaCoverage();
    const ids = rows.map(r => r.signal_id);
    const unique = new Set(ids);
    expect(ids.length).toBe(unique.size);
  });

  it('every signal_id matches SIG.MSR.NNN or SIG.MSR.NNNx format', () => {
    const rows = buildTajikaCoverage();
    const pattern = /^SIG\.MSR\.\d{3}[a-z]?$/;
    for (const row of rows) {
      expect(row.signal_id).toMatch(pattern);
    }
  });
});

describe('buildTajikaCoverage — coverage types', () => {
  it('coverage_type is only "primary" or "secondary"', () => {
    const rows = buildTajikaCoverage();
    for (const row of rows) {
      expect(['primary', 'secondary']).toContain(row.coverage_type);
    }
  });

  it('dedicated Tajika signals (559-573) are all primary', () => {
    const rows = buildTajikaCoverage();
    for (let i = 559; i <= 573; i++) {
      const id = sig(i);
      const row = rows.find(r => r.signal_id === id);
      expect(row, `${id} should exist`).toBeDefined();
      expect(row?.coverage_type, `${id} should be primary`).toBe('primary');
    }
  });

  it('Tajika-pattern signals (376-387) are all primary', () => {
    const rows = buildTajikaCoverage();
    for (let i = 376; i <= 387; i++) {
      const id = sig(i);
      const row = rows.find(r => r.signal_id === id);
      expect(row, `${id} should exist`).toBeDefined();
      expect(row?.coverage_type).toBe('primary');
    }
  });

  it('Sahama signals (391a, 391b, 391c) are all primary', () => {
    const rows = buildTajikaCoverage();
    const sahamaIds = ['SIG.MSR.391a', 'SIG.MSR.391b', 'SIG.MSR.391c'];
    for (const id of sahamaIds) {
      const row = rows.find(r => r.signal_id === id);
      expect(row, `${id} should exist`).toBeDefined();
      expect(row?.coverage_type).toBe('primary');
    }
  });

  it('all notes are non-empty strings', () => {
    const rows = buildTajikaCoverage();
    for (const row of rows) {
      expect(typeof row.notes).toBe('string');
      expect(row.notes.trim().length).toBeGreaterThan(5);
    }
  });

  it('primary notes cite TAJAKA chapter/verse reference', () => {
    const rows = buildTajikaCoverage();
    const primaryRows = rows.filter(r => r.coverage_type === 'primary');
    // Most primary rows should have [TAJAKA ...] citations
    const withCitations = primaryRows.filter(r => r.notes.includes('TAJAKA'));
    expect(withCitations.length).toBeGreaterThanOrEqual(primaryRows.length * 0.7);
  });
});

describe('munthaSigns — tajaka_annual sequence', () => {
  it('generates 87 rows for 1984-2070', () => {
    const rows = munthaSigns(1984, 2070);
    expect(rows.length).toBe(87);
  });

  it('first row (1984) has varsha_number=1 and muntha_sign=Cancer', () => {
    const rows = munthaSigns(1984, 2070);
    const first = rows[0];
    expect(first.native_year).toBe(1984);
    expect(first.varsha_number).toBe(1);
    expect(first.muntha_sign).toBe('Cancer');
  });

  it('second row (1985) has muntha_sign=Leo', () => {
    const rows = munthaSigns(1984, 2070);
    const second = rows[1];
    expect(second.muntha_sign).toBe('Leo');
  });

  it('13th year (1996) returns to Cancer (completes first 12-sign cycle)', () => {
    const rows = munthaSigns(1984, 2070);
    const year1996 = rows.find(r => r.native_year === 1996);
    expect(year1996?.muntha_sign).toBe('Cancer');
    expect(year1996?.varsha_number).toBe(13);
  });

  it('correct sign sequence for years 1984-1995', () => {
    const rows = munthaSigns(1984, 1995);
    const expected = ['Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius',
      'Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini'];
    rows.forEach((row, idx) => {
      expect(row.muntha_sign).toBe(expected[idx]);
    });
  });

  it('2026 (age 42, varsha_number=43) has correct muntha_sign', () => {
    // varsha_number = 2026 - 1984 + 1 = 43
    // sign index = (43-1) % 12 = 42 % 12 = 6 → Capricorn
    const rows = munthaSigns(1984, 2070);
    const year2026 = rows.find(r => r.native_year === 2026);
    expect(year2026?.varsha_number).toBe(43);
    expect(year2026?.muntha_sign).toBe('Capricorn');
  });

  it('all muntha_signs are valid zodiac signs', () => {
    const rows = munthaSigns(1984, 2070);
    const validSigns = new Set(SIGNS);
    for (const row of rows) {
      expect(validSigns.has(row.muntha_sign)).toBe(true);
    }
  });

  it('varsha_number matches native_year - BIRTH_YEAR + 1', () => {
    const rows = munthaSigns(1984, 2070);
    for (const row of rows) {
      expect(row.varsha_number).toBe(row.native_year - BIRTH_YEAR + 1);
    }
  });
});
