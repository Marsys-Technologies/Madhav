#!/usr/bin/env tsx
/**
 * icr_pr_gate.ts — ICR-S6 PR gate for MSR signal citation hygiene
 *
 * Validates that every signal in the canonical MSR has a non-empty `sources:`
 * block containing at least one FORENSIC or LEL citation. Intended to run on PRs
 * that touch the MSR, and weekly via icr_weekly_scan.yml.
 *
 * Usage:
 *   npx tsx platform/scripts/governance/icr_pr_gate.ts [--msr-path PATH] [--dry-run] [--synthetic]
 *
 * Exit codes:
 *   0 — all signals pass (or --dry-run mode)
 *   1 — one or more signals lack a FORENSIC/LEL citation, or the MSR could not
 *       be located/read
 *
 * SAMĀPTI B-N8-CI-GATES / finding F-27 (2026-07-30): the default MSR path was
 * hardcoded to `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`, which has not existed since
 * the MSR advanced to v5.0 (CLAUDE.md §D). Any invocation relying on the default
 * therefore died on an unreadable file rather than scanning anything. The default
 * is now DISCOVERED — highest-numbered `MSR_v*.md` in 025_HOLISTIC_SYNTHESIS/ —
 * so it cannot rot the same way on the next version bump. `--dry-run` still
 * suppresses the non-zero exit, by design, but it is no longer what the weekly
 * scheduled scan runs (see icr_weekly_scan.yml).
 */

import { readFileSync, readdirSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';

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
  /** F-27: how many signal blocks the parser actually recognised. Zero is a FAILURE,
   *  never a pass — a scan that matched nothing has not verified anything. */
  signals_scanned: number;
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

  // ── Format A (current corpus): `SIG.MSR.NNN:` blocks whose grounding lives in
  //    derivation_ledger.l1_sources[].ref. This is what MSR_v5_0.md actually is.
  // ── Format B (legacy / the --synthetic fixture): `## MSR.NNN` headers with a
  //    flat `sources:` list.
  // Before F-27 only Format B was implemented, so a scan of the real MSR matched
  // ZERO signal blocks, produced ZERO violations, and printed
  // "PASS — all signals have FORENSIC/LEL citations" over an empty set. A gate
  // that parses nothing must never report a pass; see the signals_scanned === 0
  // guard in main().
  // NB: the trailing \b in the original /\bFORENSIC\b/ could never match the corpus's
  // own citation style, `FORENSIC_v8.0 §2.1 ...` — `_` is a word character, so there is
  // no boundary after FORENSIC. Under the legacy parser this was invisible (0 blocks
  // matched at all); once Format A started parsing 569 blocks it reported all of them
  // ungrounded. Leading boundary only.
  const groundedRe = /\bFORENSIC|\bLEL\b/;

  const parseFormatA = (): number => {
    const parts = msrContent.split(/^(?=SIG\.MSR\.\d+:)/m);
    let seen = 0;
    for (const part of parts) {
      const headerMatch = part.match(/^(SIG\.MSR\.\d+):/);
      if (!headerMatch) continue;
      seen++;
      const signal_id = headerMatch[1]!;
      const nameMatch = part.match(/^\s*signal_name:\s*"?([^"\n]+)"?\s*$/m);
      const signal_name = nameMatch ? nameMatch[1]!.trim() : '(unknown)';

      // NB: the block runs to the first line that starts at column 0. An earlier
      // draft used /([\s\S]*?)(?=\n\S|$)/m, where `$` under the m flag matches at the
      // end of the FIRST line — so the ledger body came back empty and every one of
      // the 569 signals was reported ungrounded. Caught by reading the output instead
      // of trusting the exit code.
      const ledgerMatch = part.match(/^[ \t]*derivation_ledger:[ \t]*\n((?:[ \t]+.*\n?)*)/m);
      if (!ledgerMatch) {
        violations.push({ signal_id, signal_name, reason: 'No derivation_ledger: block found' });
        continue;
      }
      const ledger = ledgerMatch[1]!;
      if (!/^\s*l1_sources:/m.test(ledger)) {
        violations.push({
          signal_id,
          signal_name,
          reason: 'derivation_ledger has no l1_sources: list',
        });
        continue;
      }
      if (!groundedRe.test(ledger)) {
        violations.push({
          signal_id,
          signal_name,
          reason: 'derivation_ledger.l1_sources contains no FORENSIC or LEL citation',
        });
      }
    }
    return seen;
  };

  const parseFormatB = (): number => {
    const parts = msrContent.split(/^(?=## MSR\.\d+\s*$)/m);
    let seen = 0;
    for (const part of parts) {
      const trimmed = part.trim();
      if (!trimmed) continue;
      const headerMatch = trimmed.match(/^## (MSR\.\d+)/);
      if (!headerMatch) continue;
      seen++;
      const signal_id = headerMatch[1]!;
      const nameMatch = trimmed.match(/^signal_name:\s*"?([^"\n]+)"?\s*$/m);
      const signal_name = nameMatch ? nameMatch[1]!.trim() : '(unknown)';

      const sourcesMatch = trimmed.match(/^sources:\s*\n((?:[ \t]+.*\n?)*)/m);
      if (!sourcesMatch) {
        violations.push({ signal_id, signal_name, reason: 'No sources: section found' });
        continue;
      }
      if (!groundedRe.test(sourcesMatch[1]!)) {
        violations.push({
          signal_id,
          signal_name,
          reason: 'sources: block contains no FORENSIC or LEL citation',
        });
      }
    }
    return seen;
  };

  const signals_scanned = parseFormatA() + parseFormatB();

  return { pass: violations.length === 0, violations, signals_scanned };
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
      // F-27: discover the canonical MSR instead of hardcoding a version that
      // silently goes stale. Highest MSR_v<major>_<minor>.md wins.
      const scriptDir = dirname(new URL(import.meta.url).pathname);
      const synthDir = resolve(scriptDir, '..', '..', '..', '025_HOLISTIC_SYNTHESIS');
      let candidates: string[] = [];
      try {
        candidates = readdirSync(synthDir).filter((f) => /^MSR_v\d+_\d+\.md$/.test(f));
      } catch (err) {
        console.error(`[icr_pr_gate] ERROR: Could not read ${synthDir}`);
        console.error(err);
        process.exit(1);
      }
      if (candidates.length === 0) {
        console.error(
          `[icr_pr_gate] ERROR: No MSR_v<major>_<minor>.md found in ${synthDir}. ` +
            'This gate has nothing to scan — failing loudly rather than passing on an absent corpus.',
        );
        process.exit(1);
      }
      const rank = (f: string): number => {
        const m = /^MSR_v(\d+)_(\d+)\.md$/.exec(f)!;
        return Number(m[1]) * 1000 + Number(m[2]);
      };
      candidates.sort((a, b) => rank(b) - rank(a));
      msrPath = join(synthDir, candidates[0]!);
      console.log(`[icr_pr_gate] Discovered canonical MSR: ${candidates[0]} (from ${candidates.length} candidate(s))`);
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

  // F-27: a scan that recognised zero signal blocks has verified nothing. Before
  // this guard, runGate()'s parser (written for a `## MSR.NNN` layout the corpus
  // does not use) matched 0 of MSR_v5_0.md's 569 `SIG.MSR.NNN:` blocks and the
  // gate printed PASS over an empty set — green because it stopped looking.
  if (result.signals_scanned === 0) {
    console.error(
      '[icr_pr_gate] ICR PR gate: FAIL — parsed 0 signal blocks. Either the MSR is ' +
        'empty or its layout no longer matches this gate\'s parser. An unperformed ' +
        'scan is not a pass.',
    );
    process.exit(1);
  }

  console.log(`[icr_pr_gate] Scanned ${result.signals_scanned} signal block(s).`);

  if (result.pass) {
    console.log(
      `[icr_pr_gate] ICR PR gate: PASS — all ${result.signals_scanned} signal(s) carry a FORENSIC/LEL citation.`,
    );
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
