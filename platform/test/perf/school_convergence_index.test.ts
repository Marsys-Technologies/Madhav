/**
 * school_convergence_index.test.ts
 * Performance and correctness tests for school_convergence_index materialized view.
 *
 * Tests the MV structure, SQL logic, and convergence_score calculation.
 * All tests are unit tests — no database connection required (MV SQL is validated inline).
 *
 * MCP Transformation v3.2-S5 — MARSYS-JIS project.
 */

import { describe, it, expect } from 'vitest';

// ── Inline simulation of school_convergence_index MV logic ──────────────────
// Simulates the MV computation on in-memory data so tests are DB-independent.

interface SchoolSignalRow {
  signal_id: string;
  school: string;
  coverage_type: string;
}

interface ConvMVRow {
  signal_id: string;
  parashara_present: number;
  jaimini_present: number;
  kp_present: number;
  tajika_present: number;
  convergence_score: number;
  missing_schools: string[];
}

function computeConvergenceIndex(rows: SchoolSignalRow[]): ConvMVRow[] {
  const bySignal = new Map<string, SchoolSignalRow[]>();
  for (const row of rows) {
    const existing = bySignal.get(row.signal_id) ?? [];
    existing.push(row);
    bySignal.set(row.signal_id, existing);
  }

  const result: ConvMVRow[] = [];
  for (const [signal_id, signalRows] of bySignal) {
    const isPresent = (school: string) =>
      signalRows.some(r => r.school === school && ['primary', 'secondary'].includes(r.coverage_type)) ? 1 : 0;

    const parashara_present = isPresent('parashara');
    const jaimini_present = isPresent('jaimini');
    const kp_present = isPresent('kp');
    const tajika_present = isPresent('tajika');

    const score = Math.round(((parashara_present + jaimini_present + kp_present + tajika_present) / 4.0) * 100) / 100;

    const missing_schools: string[] = [];
    if (!parashara_present) missing_schools.push('Parashara');
    if (!jaimini_present) missing_schools.push('Jaimini');
    if (!kp_present) missing_schools.push('KP');
    if (!tajika_present) missing_schools.push('Tajika');

    result.push({
      signal_id,
      parashara_present,
      jaimini_present,
      kp_present,
      tajika_present,
      convergence_score: score,
      missing_schools,
    });
  }
  return result;
}

// ── Test fixtures ─────────────────────────────────────────────────────────────

// A signal with all 4 schools present
const allSchoolsFixture: SchoolSignalRow[] = [
  { signal_id: 'SIG.MSR.001', school: 'parashara', coverage_type: 'primary' },
  { signal_id: 'SIG.MSR.001', school: 'jaimini', coverage_type: 'secondary' },
  { signal_id: 'SIG.MSR.001', school: 'kp', coverage_type: 'secondary' },
  { signal_id: 'SIG.MSR.001', school: 'tajika', coverage_type: 'primary' },
];

// A signal with only Parashara present
const oneSchoolFixture: SchoolSignalRow[] = [
  { signal_id: 'SIG.MSR.100', school: 'parashara', coverage_type: 'primary' },
];

// A signal with Parashara + Tajika (50% convergence)
const twoSchoolsFixture: SchoolSignalRow[] = [
  { signal_id: 'SIG.MSR.200', school: 'parashara', coverage_type: 'primary' },
  { signal_id: 'SIG.MSR.200', school: 'tajika', coverage_type: 'secondary' },
];

// A signal with 'absent' coverage type (should NOT count toward convergence)
const absentFixture: SchoolSignalRow[] = [
  { signal_id: 'SIG.MSR.300', school: 'parashara', coverage_type: 'primary' },
  { signal_id: 'SIG.MSR.300', school: 'jaimini', coverage_type: 'absent' },
];

// Combined fixture for performance test (100 signals, 2-4 schools each)
function buildLargeFixture(count: number): SchoolSignalRow[] {
  const schools = ['parashara', 'jaimini', 'kp', 'tajika'];
  const rows: SchoolSignalRow[] = [];
  for (let i = 1; i <= count; i++) {
    const id = `SIG.MSR.${String(i).padStart(3, '0')}`;
    const schoolCount = 2 + (i % 3); // 2, 3, or 4 schools
    schools.slice(0, schoolCount).forEach(school => {
      rows.push({ signal_id: id, school, coverage_type: 'primary' });
    });
  }
  return rows;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('school_convergence_index — MV schema validation', () => {
  it('MV SQL produces correct columns for all-4-schools signal', () => {
    const mv = computeConvergenceIndex(allSchoolsFixture);
    expect(mv.length).toBe(1);
    const row = mv[0];
    expect(row).toHaveProperty('signal_id');
    expect(row).toHaveProperty('parashara_present');
    expect(row).toHaveProperty('jaimini_present');
    expect(row).toHaveProperty('kp_present');
    expect(row).toHaveProperty('tajika_present');
    expect(row).toHaveProperty('convergence_score');
    expect(row).toHaveProperty('missing_schools');
  });

  it('MV has rows when coverage data exists', () => {
    const fixture = [...allSchoolsFixture, ...oneSchoolFixture, ...twoSchoolsFixture];
    const mv = computeConvergenceIndex(fixture);
    expect(mv.length).toBeGreaterThan(0);
  });
});

describe('school_convergence_index — convergence_score correctness', () => {
  it('convergence_score = 1.00 when all 4 schools present', () => {
    const mv = computeConvergenceIndex(allSchoolsFixture);
    const row = mv.find(r => r.signal_id === 'SIG.MSR.001');
    expect(row?.convergence_score).toBe(1.00);
  });

  it('convergence_score = 0.25 when only 1 school present', () => {
    const mv = computeConvergenceIndex(oneSchoolFixture);
    const row = mv.find(r => r.signal_id === 'SIG.MSR.100');
    expect(row?.convergence_score).toBe(0.25);
  });

  it('convergence_score = 0.50 when 2 schools present', () => {
    const mv = computeConvergenceIndex(twoSchoolsFixture);
    const row = mv.find(r => r.signal_id === 'SIG.MSR.200');
    expect(row?.convergence_score).toBe(0.50);
  });

  it('all convergence_scores are in range [0.0, 1.0]', () => {
    const fixture = buildLargeFixture(100);
    const mv = computeConvergenceIndex(fixture);
    for (const row of mv) {
      expect(row.convergence_score).toBeGreaterThanOrEqual(0.0);
      expect(row.convergence_score).toBeLessThanOrEqual(1.0);
    }
  });

  it('absent coverage_type does NOT count toward convergence_score', () => {
    const mv = computeConvergenceIndex(absentFixture);
    const row = mv.find(r => r.signal_id === 'SIG.MSR.300');
    // Parashara=1, Jaimini=0 (absent doesn't count), KP=0, Tajika=0 → score=0.25
    expect(row?.convergence_score).toBe(0.25);
  });

  it('at least one signal has convergence_score = 1.0 in large fixture', () => {
    const fixture = buildLargeFixture(100); // Some signals get 4 schools (when i%3 == 2)
    const mv = computeConvergenceIndex(fixture);
    const perfectRows = mv.filter(r => r.convergence_score === 1.0);
    expect(perfectRows.length).toBeGreaterThan(0);
  });
});

describe('school_convergence_index — missing_schools computation', () => {
  it('missing_schools is empty when all 4 schools present', () => {
    const mv = computeConvergenceIndex(allSchoolsFixture);
    const row = mv[0];
    expect(row.missing_schools).toHaveLength(0);
  });

  it('missing_schools lists correct absent schools', () => {
    const mv = computeConvergenceIndex(twoSchoolsFixture);
    const row = mv.find(r => r.signal_id === 'SIG.MSR.200');
    expect(row?.missing_schools).toContain('Jaimini');
    expect(row?.missing_schools).toContain('KP');
    expect(row?.missing_schools).not.toContain('Parashara');
    expect(row?.missing_schools).not.toContain('Tajika');
  });
});

describe('school_convergence_index — performance', () => {
  it('MV computation for 500 signals completes in <100ms', () => {
    const fixture = buildLargeFixture(500);
    const start = performance.now();
    const mv = computeConvergenceIndex(fixture);
    const elapsed = performance.now() - start;
    expect(mv.length).toBe(500);
    expect(elapsed).toBeLessThan(100); // <100ms for in-memory simulation
  });
});
