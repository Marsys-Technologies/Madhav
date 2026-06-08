/**
 * l1_truth_index.test.ts — ICR-S2 unit tests for the L1 Truth Index Scorer
 *
 * Uses a synthetic 10-signal fixture (5 grounded, 5 ungrounded).
 * Does NOT read the live MSR file.
 */

import { describe, it, expect } from 'vitest';
import { parseMsrFile, computeReport, isGrounded } from '@/lib/icr/l1_truth_index';

// ─────────────────────────────────────────────────────────────────────────────
// Synthetic fixture: 10 signals — 5 grounded, 5 ungrounded
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Build a minimal MSR-format string with 10 signals.
 *
 * Grounded signals (L1 citations present):
 *   SIG.MSR.001 — references FORENSIC §2.1
 *   SIG.MSR.002 — references FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
 *   SIG.MSR.003 — references LIFE_EVENT_LOG
 *   SIG.MSR.004 — references LEL (word-bounded)
 *   SIG.MSR.005 — references EVT.2023
 *
 * Ungrounded signals (no L1 citations):
 *   SIG.MSR.006 — classical-only, no L1 ref
 *   SIG.MSR.007 — classical-only, no L1 ref
 *   SIG.MSR.008 — contains "paralleled" (must NOT match \bLEL\b)
 *   SIG.MSR.009 — classical-only, no L1 ref
 *   SIG.MSR.010 — classical-only, no L1 ref
 */
const FIXTURE = `---
artifact: MSR_fixture_test
version: "0.1"
signal_count: 10
---

# MSR fixture for ICR-S2 tests

SIG.MSR.001:
  signal_name: "Test Signal A — FORENSIC grounded"
  classical_source: "BPHS Ch.1"
  supporting_rules:
    - Confirmed by FORENSIC §2.1 planetary placement table
  falsifier: "If FORENSIC §2.1 disagrees, claim fails"
  confidence: 0.90

SIG.MSR.002:
  signal_name: "Test Signal B — FORENSIC_ASTROLOGICAL_DATA grounded"
  classical_source: "BPHS Ch.2"
  supporting_rules:
    - Data pulled from FORENSIC v8.0 §3.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
  falsifier: "No canonical source => ungrounded"
  confidence: 0.85

SIG.MSR.003:
  signal_name: "Test Signal C — LIFE_EVENT_LOG grounded"
  classical_source: "BPHS Ch.3"
  supporting_rules:
    - Event density confirmed by LIFE_EVENT_LOG §2.2
  falsifier: "If LIFE_EVENT_LOG shows no matching event, claim fails"
  confidence: 0.80

SIG.MSR.004:
  signal_name: "Test Signal D — LEL grounded"
  classical_source: "BPHS Ch.4"
  supporting_rules:
    - 22 LEL events in Mercury MD confirm this
  falsifier: "If fewer than 10 events recorded, ratio changes"
  confidence: 0.88

SIG.MSR.005:
  signal_name: "Test Signal E — EVT grounded"
  classical_source: "BPHS Ch.5"
  supporting_rules:
    - Retrodictively matches EVT.2023.05.XX.01 (Marsys contract)
  falsifier: "If EVT.2023 event is reclassified, correlation drops"
  confidence: 0.82

SIG.MSR.006:
  signal_name: "Test Signal F — ungrounded (classical only)"
  classical_source: "BPHS Ch.6"
  supporting_rules:
    - Saturn exalted in Libra is a classical rule
  falsifier: "Classical falsifier only"
  confidence: 0.75

SIG.MSR.007:
  signal_name: "Test Signal G — ungrounded (classical only)"
  classical_source: "Phaladeepika Ch.7"
  supporting_rules:
    - Neecha Bhanga Raja Yoga formation rules
  falsifier: "If dispositor is weak, NBRY does not activate"
  confidence: 0.70

SIG.MSR.008:
  signal_name: "Test Signal H — ungrounded (paralleled text, no grounding match)"
  classical_source: "BPHS Ch.8"
  supporting_rules:
    - This rule is paralleled by classical texts (no grounding reference present)
    - The word paralleled must not trigger the word-boundary check
  falsifier: "No canonical data to falsify this"
  confidence: 0.65

SIG.MSR.009:
  signal_name: "Test Signal I — ungrounded (no L1 citation)"
  classical_source: "Saravali Ch.9"
  supporting_rules:
    - Moon in 11H equals gains (classical rule)
  falsifier: "Classical only"
  confidence: 0.60

SIG.MSR.010:
  signal_name: "Test Signal J — ungrounded (no L1 citation)"
  classical_source: "Jaimini Sutras 1.1.5"
  supporting_rules:
    - Atmakaraka placement rules
  falsifier: "If a different planet has higher degrees, AK changes"
  confidence: 0.55
`;

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe('l1_truth_index scorer (ICR-S2)', () => {
  it('parseMsrFile extracts exactly 10 signals from the fixture', () => {
    const signals = parseMsrFile(FIXTURE);
    expect(signals).toHaveLength(10);
  });

  it('fixture produces exactly 50% coverage (5 grounded, 5 ungrounded)', () => {
    const signals = parseMsrFile(FIXTURE);
    const report = computeReport(signals);
    expect(report.total_signals).toBe(10);
    expect(report.grounded_signals).toBe(5);
    expect(report.ungrounded_signals).toBe(5);
    expect(report.coverage_score).toBe(50);
    expect(report.passes_gate).toBe(false);
  });

  it('ungrounded_ids contains exactly the 5 ungrounded signal IDs', () => {
    const signals = parseMsrFile(FIXTURE);
    const report = computeReport(signals);
    expect(report.ungrounded_ids).toEqual([
      'SIG.MSR.006',
      'SIG.MSR.007',
      'SIG.MSR.008',
      'SIG.MSR.009',
      'SIG.MSR.010',
    ]);
  });

  it('isGrounded word-boundary check: standalone word matching works correctly', () => {
    // "paralleled" contains substring "lel" but the pattern \bLEL\b is case-sensitive
    // and matches word boundaries — "paralleled" should NOT trigger it
    expect(isGrounded('This rule is paralleled by classical texts')).toBe(false);
    // Bare "LEL" (word-bounded) should match
    expect(isGrounded('22 LEL events confirm this signal')).toBe(true);
    // FORENSIC should match
    expect(isGrounded('Confirmed by FORENSIC §2.1')).toBe(true);
    // Classical-only text with no L1 refs must not match
    expect(isGrounded('Saturn exalted in Libra is a classical rule only')).toBe(false);
  });
});
