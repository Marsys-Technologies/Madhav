#!/usr/bin/env tsx
/**
 * icr_pr_gate.ts — ICR-S6 PR gate for MSR signal citation hygiene
 *
 * Validates that every signal in MSR_v3_0.md has a non-empty `sources:` block
 * containing at least one FORENSIC or LEL citation. Intended to run on PRs
 * that touch MSR_v3_0.md.
 *
 * Usage:
 *   npx tsx platform/scripts/governance/icr_pr_gate.ts [--msr-path PATH] [--dry-run] [--synthetic]
 *
 * Exit codes:
 *   0 — all signals pass (or --dry-run mode)
 *   1 — one or more signals lack a FORENSIC/LEL citation
 */

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface GateViolation {
  signal_id: string;
  signal_name: string;
  reason: string;
}

export interface GateResult {
  pass: boolean;
  violations: GateViolation[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Synthetic MSR fragment (for --synthetic / CI smoke testing)
// ─────────────────────────────────────────────────────────────────────────────

const SYNTHETIC_MSR = `
## MSR.001
signal_name: "Test Signal"
sources:
  - BPHS Chapter 1

## MSR.002
signal_name: "Grounded Signal"
sources:
  - FORENSIC VRS.TEST: value
`;

// ─────────────────────────────────────────────────────────────────────────────
// Core gate logic (exported for unit tests)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parse MSR content and check each signal for FORENSIC or LEL citation.
 *
 * MSR signal blocks are delimited by `## MSR.NNN` headers.
 * Within each block, we look for a `sources:` section and check if any line
 * in that section contains the string "FORENSIC" or "LEL".
 */
export function runGate(msrContent: string): GateResult {
  const violations: GateViolation[] = [];

  // Split on ## MSR.NNN boundaries
  const SIGNAL_HEADER = /^## (MSR\.\d+)\s*$/m;

  // Split the content into blocks using the header pattern
  const parts = msrContent.split(/^(?=## MSR\.\d+\s*$)/m);

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    // Extract signal ID
    const headerMatch = trimmed.match(/^## (MSR\.\d+)/);
    if (!headerMatch) continue;

    const signal_id = headerMatch[1];

    // Extract signal_name
    const nameMatch = trimmed.match(/^signal_name:\s*"?([^"\n]+)"?\s*$/m);
    const signal_name = nameMatch ? nameMatch[1].trim() : '(unknown)';

    // Find the sources: section
    const sourcesMatch = trimmed.match(/^sources:\s*\n((?:[ \t]+.*\n?)*)/m);

    if (!sourcesMatch) {
      // No sources: section at all
      violations.push({
        signal_id,
        signal_name,
        reason: 'No sources: section found',
      });
      continue;
    }

    const sourcesBlock = sourcesMatch[1];

    // Check if any line in sources block contains FORENSIC or LEL
    const hasGrounding = /\bFORENSIC\b|\bLEL\b/.test(sourcesBlock);

    if (!hasGrounding) {
      violations.push({
        signal_id,
        signal_name,
        reason: 'sources: block contains no FORENSIC or LEL citation',
      });
    }
  }

  return {
    pass: violations.length === 0,
    violations,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI entrypoint
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const synthetic = args.includes('--synthetic');

  // Resolve MSR path
  let msrContent: string;

  if (synthetic) {
    console.log('[icr_pr_gate] Running in --synthetic mode (hardcoded mini-MSR).');
    msrContent = SYNTHETIC_MSR;
  } else {
    const msrPathIdx = args.indexOf('--msr-path');
    let msrPath: string;

    if (msrPathIdx !== -1 && args[msrPathIdx + 1]) {
      msrPath = resolve(args[msrPathIdx + 1]);
    } else {
      // Default: relative to script dir → ../025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
      const scriptDir = dirname(new URL(import.meta.url).pathname);
      msrPath = resolve(scriptDir, '..', '..', '..', '025_HOLISTIC_SYNTHESIS', 'MSR_v3_0.md');
    }

    console.log(`[icr_pr_gate] MSR path: ${msrPath}`);

    try {
      msrContent = readFileSync(msrPath, 'utf-8');
    } catch (err) {
      console.error(`[icr_pr_gate] ERROR: Could not read MSR file at ${msrPath}`);
      console.error(err);
      process.exit(1);
    }
  }

  // Run the gate
  const result = runGate(msrContent);

  if (result.pass) {
    console.log('[icr_pr_gate] ICR PR gate: PASS — all signals have FORENSIC/LEL citations.');
    if (!dryRun) {
      process.exit(0);
    }
  } else {
    console.error(`[icr_pr_gate] ICR PR gate: FAIL — ${result.violations.length} signal(s) lack FORENSIC/LEL citation.`);
    for (const v of result.violations) {
      console.error(`  VIOLATION: ${v.signal_id} — "${v.signal_name}" — ${v.reason}`);
    }
    if (dryRun) {
      console.log('[icr_pr_gate] --dry-run mode: would exit 1 but skipping.');
    } else {
      process.exit(1);
    }
  }
}

// Only execute main() when this file is run directly (not imported as a module).
// This guard prevents process.exit() from firing when vitest imports runGate().
const isMain =
  typeof process !== 'undefined' &&
  process.argv[1] &&
  (process.argv[1].endsWith('icr_pr_gate.ts') || process.argv[1].endsWith('icr_pr_gate.js'));

if (isMain) {
  main().catch((err) => {
    console.error('[icr_pr_gate] Unhandled error:', err);
    process.exit(1);
  });
}
