/**
 * detector.test.ts — Unit tests for ICR Class A detector
 *
 * ICR-S3 (2026-05-21)
 *
 * Tests use SYNTHETIC MSR fixtures — the real MSR file is NOT read.
 * Gate: Test 3 (intra_signal_munta_detected) must pass for ICR-S3 to close.
 */

import { describe, it, expect } from 'vitest';
import {
  parseMsrSignals,
  detectSignHouseMismatch,
} from '../detector';

// ─────────────────────────────────────────────────────────────────────────────
// Synthetic fixtures
// ─────────────────────────────────────────────────────────────────────────────

/**
 * A minimal synthetic MSR block with 3 signals.
 * Follows the same YAML-in-Markdown format as MSR_v3_0.md.
 */
const SYNTHETIC_MSR_3_SIGNALS = `
SIG.MSR.100:
  signal_name: "Yoga — Sun in Leo 5H = Royal Creative Power"
  signal_type: graha-yoga
  classical_source: "BPHS (Sun in own sign)"
  supporting_rules:
    - Sun owns Leo; Sun in Leo = svakshetra placement = maximum dignity
    - 5H = intelligence, creativity, children
  falsifier: "FORENSIC §3.2: Sun is in Leo. Confirmed by Jagannatha Hora output. Leo = confirmed."

SIG.MSR.200:
  signal_name: "Tajika — Muntha in Aries 1H at Age 12"
  signal_type: tajika-pattern
  classical_source: "Tajika Neelakanthi (Muntha = natal Lagna at birth)"
  supporting_rules:
    - Age 0 = Muntha in Aries 1H. Age 12 = Muntha cycles back to Aries 1H.
  falsifier: "Muntha at age 12: 12 mod 12 = 0 remainder, full cycle = back to Aries 1H = confirmed."

SIG.MSR.300:
  signal_name: "Graha — Mercury Exalted in Virgo 6H"
  signal_type: graha-placement
  classical_source: "BPHS (Mercury exalted in Virgo)"
  supporting_rules:
    - Mercury is exalted in Virgo; maximum strength
    - 6H: service, health, enemies
  falsifier: "FORENSIC §4.1: Mercury is placed in Virgo. Virgo = confirmed exaltation placement."
`;

/**
 * Synthetic 2-signal MSR where signal 1 has a Gemini/Virgo mismatch
 * (mirrors DIS.013 / MSR.377) and signal 2 is clean.
 */
const SYNTHETIC_MSR_2_SIGNALS_ONE_CONFLICT = `
SIG.MSR.377:
  signal_name: "Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation"
  signal_type: tajika-pattern
  classical_source: "Tajika Neelakanthi (Muntha moves 30/year)"
  supporting_rules:
    - Age 42 mod 12 = 6. 6th sign from Aries = Virgo 6H.
  falsifier: "Muntha calculation: Age 42 mod 12 = 6; 6th sign from Aries = Virgo (Aries=1, Taurus=2, Gemini=3, Cancer=4, Leo=5, Virgo=6). Muntha at 42 = Virgo 6H = confirmed."

SIG.MSR.378:
  signal_name: "Tajika — Ithasala Yoga: Mercury-Saturn convergence"
  signal_type: tajika-pattern
  classical_source: "Tajika Neelakanthi (Ithasala Yoga)"
  supporting_rules:
    - Mercury faster than Saturn; Ithasala when within 13 degrees
  falsifier: "Ithasala yoga requires actual annual chart positions to confirm. [FRAMEWORK SIGNAL]."
`;

// ─────────────────────────────────────────────────────────────────────────────
// Test 1: parser extracts signal_name and falsifier from a 3-signal block
// ─────────────────────────────────────────────────────────────────────────────

describe('parseMsrSignals', () => {
  it('Test 1 — extracts signal_name and falsifier from a 3-signal synthetic block', () => {
    const signals = parseMsrSignals(SYNTHETIC_MSR_3_SIGNALS);

    expect(signals).toHaveLength(3);

    expect(signals[0].id).toBe('SIG.MSR.100');
    expect(signals[0].signal_name).toContain('Royal Creative Power');
    expect(signals[0].falsifier).toContain('Leo = confirmed');

    expect(signals[1].id).toBe('SIG.MSR.200');
    expect(signals[1].signal_name).toContain('Muntha in Aries 1H at Age 12');
    expect(signals[1].falsifier).toContain('Aries 1H = confirmed');

    expect(signals[2].id).toBe('SIG.MSR.300');
    expect(signals[2].signal_name).toContain('Mercury Exalted in Virgo 6H');
    expect(signals[2].falsifier).toContain('Virgo = confirmed');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 2: no conflict when signal_name and falsifier agree on the same sign
// ─────────────────────────────────────────────────────────────────────────────

describe('detectSignHouseMismatch', () => {
  it('Test 2 — returns null when signal_name and falsifier agree on the same sign', () => {
    const result = detectSignHouseMismatch(
      'SIG.MSR.100',
      'Sun in Leo 5H = Royal Creative Power',
      'Sun is in Leo. Leo = confirmed by Jagannatha Hora.',
    );
    expect(result).toBeNull();
  });

  // ─────────────────────────────────────────────────────────────────────────
  // Test 3: intra_signal_munta_detected gate
  // signal_name says Gemini, falsifier says Virgo + confirmed → Class A
  // ─────────────────────────────────────────────────────────────────────────

  it('Test 3 (intra_signal_munta_detected) — returns ConflictRecord when signal_name says Gemini and falsifier says Virgo + confirmed', () => {
    const result = detectSignHouseMismatch(
      'SIG.MSR.377',
      'Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation',
      'Muntha calculation: Age 42 mod 12 = 6; 6th sign from Aries = Virgo (Aries=1, Taurus=2, Gemini=3, Cancer=4, Leo=5, Virgo=6). Muntha at 42 = Virgo 6H = confirmed.',
    );

    expect(result).not.toBeNull();
    expect(result!.conflict_id).toBe('DIS.013');
    expect(result!.conflict_class).toBe('A');
    expect(result!.signal_ids_affected).toContain('MSR.377');
    expect(result!.description).toContain('Gemini');
    expect(result!.description).toContain('Virgo');
    expect(result!.evidence).toContain('Gemini');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // Test 4: no flag when falsifier has no "confirmed"
  // ─────────────────────────────────────────────────────────────────────────

  it('Test 4 — returns null when falsifier has no "confirmed" (ambiguous case)', () => {
    const result = detectSignHouseMismatch(
      'SIG.MSR.378',
      'Tajika — Ithasala Yoga: Mercury-Saturn Gemini convergence',
      'Ithasala yoga requires actual Virgo chart positions to confirm only with real data.',
    );
    // falsifier mentions Virgo but the word "confirmed" is not present
    // Note: "confirm" is present but "confirmed" is not — should return null
    expect(result).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Test 5: detectAll() on synthetic 2-signal MSR returns exactly 1 ConflictRecord
//
// We test the full pipeline (parse + detect) without touching the filesystem,
// by calling detectClassA-equivalent logic directly:
//   parseMsrSignals → detectSignHouseMismatch per signal → collect conflicts
// This verifies the integration path that detectAll() exercises in production.
// ─────────────────────────────────────────────────────────────────────────────

describe('IntraSignalDetector pipeline (synthetic)', () => {
  it('Test 5 — detectAll pipeline on synthetic 2-signal MSR with one conflict returns exactly 1 ConflictRecord', () => {
    // Replicate what detectClassA() does internally, but on synthetic content
    const signals = parseMsrSignals(SYNTHETIC_MSR_2_SIGNALS_ONE_CONFLICT);

    // Should have parsed 2 signals
    expect(signals).toHaveLength(2);

    const conflicts = signals
      .map((s) => detectSignHouseMismatch(s.id, s.signal_name, s.falsifier))
      .filter((c): c is NonNullable<typeof c> => c !== null);

    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].conflict_id).toBe('DIS.013');
    expect(conflicts[0].conflict_class).toBe('A');
    expect(conflicts[0].signal_ids_affected).toContain('MSR.377');
  });
});
