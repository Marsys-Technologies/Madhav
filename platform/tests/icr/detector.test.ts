/**
 * detector.test.ts — ICR-S3 unit tests for the Class A conflict detector
 *
 * Uses synthetic MSR fragment + synthetic FORENSIC content written to temp
 * files. Does NOT read the live corpus — fully self-contained.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { IntraSignalDetector, parseMsrSignals } from '@/lib/icr/detector';

// ─────────────────────────────────────────────────────────────────────────────
// Temp fixture directory
// ─────────────────────────────────────────────────────────────────────────────

const FIXTURE_DIR = resolve(tmpdir(), `icr-s3-test-${Date.now()}`);
const SYNTHETIC_MSR_PATH = resolve(FIXTURE_DIR, 'MSR_synthetic.md');
const SYNTHETIC_FORENSIC_PATH = resolve(FIXTURE_DIR, 'FORENSIC_synthetic.md');

/**
 * Synthetic MSR fragment: two signals.
 *
 * Signal A (MSR.901): Muntha asserted as "Taurus" — FORENSIC says Libra → CONFLICT
 * Signal B (MSR.902): Muntha asserted as "Libra" — FORENSIC says Libra → NO CONFLICT
 * Signal C (MSR.903): No Muntha placement in name → NO CONFLICT
 */
const SYNTHETIC_MSR_CONTENT = `
SIG.MSR.901:
  signal_name: "Tajika — Muntha Position at Age 42: Muntha in Taurus 2H = Wealth-Domain Annual Activation"
  signal_type: tajika-pattern
  classical_source: "Tajika Neelakanthi"
  entities_involved: [HSE.2]
  strength_score: 0.80
  valence: context-dependent
  temporal_activation: annual
  supporting_rules:
    - Natal Lagna = Aries 1H. Muntha moves 30 degrees per year.
    - Synthetic test signal — Muntha in Taurus disagrees with FORENSIC Libra.
  falsifier: "If FORENSIC VRS.MUNTHA.SIGN is not Taurus, this signal name is in error."
  provenance: synthetic-test
  domains_affected: [wealth]
  confidence: 0.75

SIG.MSR.902:
  signal_name: "Tajika — Muntha Position at Age 42: Muntha in Libra 7H = Partnership-Domain Annual Activation"
  signal_type: tajika-pattern
  classical_source: "Tajika Neelakanthi"
  entities_involved: [HSE.7]
  strength_score: 0.82
  valence: context-dependent
  temporal_activation: annual
  supporting_rules:
    - Muntha in Libra 7H = partnership and spouse-domain activation.
  falsifier: "If FORENSIC VRS.MUNTHA.SIGN is not Libra, this signal name is in error."
  provenance: synthetic-test
  domains_affected: [relationships]
  confidence: 0.80

SIG.MSR.903:
  signal_name: "Mercury — Analytical Intelligence as Career Engine: Mercury 10H Exalted = Career via Intellect"
  signal_type: parashari-pattern
  classical_source: "Brihat Parasara Hora Sastra"
  entities_involved: [PLN.MERCURY, HSE.10]
  strength_score: 0.90
  valence: positive
  temporal_activation: natal
  supporting_rules:
    - Mercury in Virgo 10H is exalted — maximum analytical power in career house.
  falsifier: "If Mercury is not in Virgo 10H, this signal is in error."
  provenance: synthetic-test
  domains_affected: [career]
  confidence: 0.88
`;

/**
 * Synthetic FORENSIC fragment: just the Varshaphal table entry.
 * VRS.MUNTHA.SIGN = Libra (7th House)
 */
const SYNTHETIC_FORENSIC_CONTENT = `
## §22 — VARSHAPHAL (ANNUAL CHART) DATA

| ID | Component | Value |
| --- | --- | --- |
| \`VRS.VALIDITY\` | Validity | 2026-02-05 to 2027-02-05 |
| \`VRS.MUNTHA.SIGN\` | Muntha | Libra (7th House) |
| \`VRS.MUNTHA.LORD\` | Muntha Lord | Venus |
`;

// ─────────────────────────────────────────────────────────────────────────────
// Setup / teardown
// ─────────────────────────────────────────────────────────────────────────────

beforeAll(() => {
  mkdirSync(FIXTURE_DIR, { recursive: true });
  writeFileSync(SYNTHETIC_MSR_PATH, SYNTHETIC_MSR_CONTENT, 'utf-8');
  writeFileSync(SYNTHETIC_FORENSIC_PATH, SYNTHETIC_FORENSIC_CONTENT, 'utf-8');
});

afterAll(() => {
  rmSync(FIXTURE_DIR, { recursive: true, force: true });
});

// ─────────────────────────────────────────────────────────────────────────────
// Parser unit tests
// ─────────────────────────────────────────────────────────────────────────────

describe('parseMsrSignals', () => {
  it('parses all three synthetic signals', () => {
    const signals = parseMsrSignals(SYNTHETIC_MSR_CONTENT);
    expect(signals).toHaveLength(3);
  });

  it('assigns correct IDs', () => {
    const signals = parseMsrSignals(SYNTHETIC_MSR_CONTENT);
    expect(signals[0].id).toBe('MSR.901');
    expect(signals[1].id).toBe('MSR.902');
    expect(signals[2].id).toBe('MSR.903');
  });

  it('extracts signal_name for MSR.901', () => {
    const signals = parseMsrSignals(SYNTHETIC_MSR_CONTENT);
    const s901 = signals.find((s) => s.id === 'MSR.901')!;
    expect(s901.signal_name).toContain('Muntha in Taurus');
  });

  it('extracts signal_name for MSR.902', () => {
    const signals = parseMsrSignals(SYNTHETIC_MSR_CONTENT);
    const s902 = signals.find((s) => s.id === 'MSR.902')!;
    expect(s902.signal_name).toContain('Muntha in Libra');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Class A detector tests
// ─────────────────────────────────────────────────────────────────────────────

describe('IntraSignalDetector.detectClassA', () => {
  it('detects exactly one conflict (MSR.901 vs Libra FORENSIC)', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    expect(conflicts).toHaveLength(1);
  });

  it('emitted conflict has class A', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    expect(conflicts[0].conflict_class).toBe('A');
  });

  it('emitted conflict signal_ids_affected contains MSR.901', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    expect(conflicts[0].signal_ids_affected).toContain('MSR.901');
  });

  it('emitted conflict has non-empty evidence', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    expect(conflicts[0].evidence).toBeTruthy();
    expect(conflicts[0].evidence).toContain('Taurus');
    expect(conflicts[0].evidence).toContain('Libra');
  });

  it('does NOT flag MSR.902 (Libra matches FORENSIC Libra)', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    const ids = conflicts.flatMap((c) => c.signal_ids_affected);
    expect(ids).not.toContain('MSR.902');
  });

  it('does NOT flag MSR.903 (no Muntha placement in name)', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    const ids = conflicts.flatMap((c) => c.signal_ids_affected);
    expect(ids).not.toContain('MSR.903');
  });

  it('conflict_id is DIS.013', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    expect(conflicts[0].conflict_id).toBe('DIS.013');
  });

  it('detected_at is a valid ISO timestamp', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const conflicts = await detector.detectClassA();
    const ts = conflicts[0].detected_at;
    expect(() => new Date(ts)).not.toThrow();
    expect(new Date(ts).getFullYear()).toBeGreaterThanOrEqual(2026);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// detectAll wraps detectClassA results
// ─────────────────────────────────────────────────────────────────────────────

describe('IntraSignalDetector.detectAll', () => {
  it('returns the same conflicts as detectClassA (B and C are empty stubs)', async () => {
    const detector = new IntraSignalDetector({
      msr_path: SYNTHETIC_MSR_PATH,
      forensic_path: SYNTHETIC_FORENSIC_PATH,
    });
    const [allConflicts, classAConflicts] = await Promise.all([
      detector.detectAll(),
      detector.detectClassA(),
    ]);
    expect(allConflicts).toHaveLength(classAConflicts.length);
  });
});
