/**
 * icr_pr_gate.test.ts — ICR-S6 unit tests for the PR citation gate
 *
 * Tests the runGate() function exported from icr_pr_gate.ts.
 * Does NOT exec the script — imports the function directly.
 */

import { describe, it, expect } from 'vitest';
import { execSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runGate } from '../../scripts/governance/icr_pr_gate';

// ─────────────────────────────────────────────────────────────────────────────
// Test fixtures
// ─────────────────────────────────────────────────────────────────────────────

const MSR_ALL_GROUNDED = `
## MSR.010
signal_name: "Fully Grounded Signal"
sources:
  - FORENSIC VRS.MUNTHA.SIGN: Libra (7th House)
  - BPHS Chapter 5

## MSR.011
signal_name: "LEL Grounded Signal"
sources:
  - LEL.EVENT.023: first job
  - Some classical text
`;

const MSR_WITH_VIOLATION = `
## MSR.001
signal_name: "Test Signal"
sources:
  - BPHS Chapter 1

## MSR.002
signal_name: "Grounded Signal"
sources:
  - FORENSIC VRS.TEST: value
`;

const MSR_MISSING_SOURCES = `
## MSR.050
signal_name: "Signal Without Sources Block"
signal_type: parashari-pattern
strength_score: 0.80
`;

const MSR_MULTIPLE_VIOLATIONS = `
## MSR.100
signal_name: "First Bad Signal"
sources:
  - BPHS Chapter 3
  - Saravali

## MSR.101
signal_name: "Second Bad Signal"
sources:
  - Classical text only

## MSR.102
signal_name: "Good Signal"
sources:
  - FORENSIC PTN.SUN.SIGN: Aquarius
`;

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe('runGate — synthetic_pr_conflict_gate_fails', () => {
  it('detects MSR.001 as violation in synthetic input (no FORENSIC/LEL)', () => {
    const result = runGate(MSR_WITH_VIOLATION);
    expect(result.pass).toBe(false);
    const violationIds = result.violations.map((v) => v.signal_id);
    expect(violationIds).toContain('MSR.001');
  });

  it('does NOT flag MSR.002 (has FORENSIC citation)', () => {
    const result = runGate(MSR_WITH_VIOLATION);
    const violationIds = result.violations.map((v) => v.signal_id);
    expect(violationIds).not.toContain('MSR.002');
  });

  it('violation has correct signal_name', () => {
    const result = runGate(MSR_WITH_VIOLATION);
    const v = result.violations.find((x) => x.signal_id === 'MSR.001');
    expect(v).toBeDefined();
    expect(v!.signal_name).toBe('Test Signal');
  });

  it('violation has non-empty reason', () => {
    const result = runGate(MSR_WITH_VIOLATION);
    const v = result.violations.find((x) => x.signal_id === 'MSR.001');
    expect(v!.reason).toBeTruthy();
    expect(v!.reason.length).toBeGreaterThan(5);
  });
});

describe('runGate — gate_passes_on_grounded_signals', () => {
  it('passes when all signals have FORENSIC citations', () => {
    const result = runGate(MSR_ALL_GROUNDED);
    expect(result.pass).toBe(true);
    expect(result.violations).toHaveLength(0);
  });

  it('accepts LEL citations as valid grounding', () => {
    const result = runGate(MSR_ALL_GROUNDED);
    // MSR.011 uses LEL — should not be flagged
    const violationIds = result.violations.map((v) => v.signal_id);
    expect(violationIds).not.toContain('MSR.011');
  });
});

describe('runGate — gate_detects_missing_sources_section', () => {
  it('flags signal with no sources: block at all', () => {
    const result = runGate(MSR_MISSING_SOURCES);
    expect(result.pass).toBe(false);
    const violationIds = result.violations.map((v) => v.signal_id);
    expect(violationIds).toContain('MSR.050');
  });

  it('reason mentions missing sources section', () => {
    const result = runGate(MSR_MISSING_SOURCES);
    const v = result.violations.find((x) => x.signal_id === 'MSR.050');
    expect(v).toBeDefined();
    expect(v!.reason).toMatch(/sources/i);
  });
});

describe('runGate — multiple violations', () => {
  it('collects all violations across the MSR', () => {
    const result = runGate(MSR_MULTIPLE_VIOLATIONS);
    expect(result.pass).toBe(false);
    expect(result.violations).toHaveLength(2);
    const ids = result.violations.map((v) => v.signal_id);
    expect(ids).toContain('MSR.100');
    expect(ids).toContain('MSR.101');
    expect(ids).not.toContain('MSR.102');
  });
});

describe('runGate — empty MSR', () => {
  it('passes on empty content (no signals to check)', () => {
    const result = runGate('');
    expect(result.pass).toBe(true);
    expect(result.violations).toHaveLength(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// scheduled_job_smoke — exec the script via child_process
// ─────────────────────────────────────────────────────────────────────────────

describe('scheduled_job_smoke', () => {
  /**
   * Helper: run the gate script and return combined stdout+stderr output.
   * Uses `2>&1` shell redirect so execSync captures both streams together.
   */
  function runScript(extraArgs = ''): { output: string; exitCode: number } {
    const scriptPath = resolve(
      dirname(fileURLToPath(import.meta.url)),
      '../../scripts/governance/icr_pr_gate.ts',
    );
    const cwd = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

    let output = '';
    let exitCode = 0;

    try {
      // Redirect stderr→stdout so execSync captures everything
      output = execSync(
        `npx tsx "${scriptPath}" ${extraArgs} 2>&1`,
        { encoding: 'utf-8', cwd, shell: '/bin/sh' },
      );
    } catch (err: unknown) {
      const spawnError = err as { status?: number; stdout?: string; stderr?: string };
      exitCode = spawnError.status ?? 1;
      output = (spawnError.stdout ?? '') + (spawnError.stderr ?? '');
    }

    return { output, exitCode };
  }

  it('outputs MSR.001 violation in --dry-run --synthetic mode', () => {
    // --dry-run suppresses exit(1); --synthetic uses hardcoded mini-MSR.
    // Output must contain the violation signal ID and FAIL/VIOLATION marker.
    const { output } = runScript('--dry-run --synthetic');
    expect(output).toMatch(/MSR\.001/);
    expect(output).toMatch(/VIOLATION|FAIL/i);
  });

  it('mentions the synthetic violation signal name in output', () => {
    const { output } = runScript('--dry-run --synthetic');
    // "Test Signal" is the signal_name in the synthetic MSR fixture
    expect(output).toMatch(/Test Signal/);
  });

  it('exits 1 without --dry-run (synthetic has a violation)', () => {
    // Without --dry-run the script calls process.exit(1) on violation
    const { exitCode } = runScript('--synthetic');
    expect(exitCode).toBe(1);
  });
});
