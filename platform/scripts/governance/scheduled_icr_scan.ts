#!/usr/bin/env tsx
/**
 * scheduled_icr_scan.ts — Scheduled ICR conflict scanner
 * ICR-S6 (2026-05-21): Run detectAll(), filter already-handled conflicts,
 * and emit PROPOSED/ artifacts for each new conflict.
 *
 * Usage (from repo root):
 *   npx tsx platform/scripts/governance/scheduled_icr_scan.ts
 *
 * Exit codes:
 *   0 — scan complete (regardless of number of conflicts found)
 *   1 — unexpected error
 *
 * Designed to run on a cron schedule (e.g. nightly).
 * NEVER modifies MSR, UCN, CDLM, RM, or any L1/L2.5 synthesis file.
 */

import { readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { IntraSignalDetector } from '../../src/lib/icr/detector';
import { emitProposePatch } from '../../src/lib/icr/patch_emitter';

// ─────────────────────────────────────────────────────────────────────────────
// Paths
// ─────────────────────────────────────────────────────────────────────────────

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(SCRIPT_DIR, '..', '..', '..');

const MSR_PATH = resolve(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md');
const FORENSIC_PATH = resolve(
  REPO_ROOT,
  '01_FACTS_LAYER',
  'FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
);

// ─────────────────────────────────────────────────────────────────────────────
// Helper: collect already-handled conflict IDs from PROPOSED/ and RESOLVED/
// ─────────────────────────────────────────────────────────────────────────────

function collectHandledIds(repoRoot: string): Set<string> {
  const seen = new Set<string>();

  for (const dirName of ['PROPOSED', 'RESOLVED']) {
    const dirPath = resolve(repoRoot, '00_ARCHITECTURE', 'CONFLICT_PATCHES', dirName);
    if (!existsSync(dirPath)) continue;

    for (const filename of readdirSync(dirPath)) {
      if (!filename.endsWith('.yaml')) continue;

      // Parse conflict_id from filename.
      // Conventions:
      //   DIS.013_MSR_377_proposed.yaml  → DIS.013
      //   DIS.013_MSR_377_resolved.yaml  → DIS.013
      //   DIS.AUTO.42_MSR_42_proposed.yaml → DIS.AUTO.42
      const withoutSuffix = filename
        .replace(/_proposed\.yaml$/, '')
        .replace(/_resolved\.yaml$/, '');

      const signalIdSepRe = /_(MSR|UCN|CDLM|RM|CGM|LEL)_/;
      const sepIdx = withoutSuffix.search(signalIdSepRe);
      if (sepIdx !== -1) {
        seen.add(withoutSuffix.slice(0, sepIdx));
        continue;
      }

      // Fallback
      const parts = withoutSuffix.split('_');
      if (parts.length >= 2 && parts[0] === 'DIS') {
        seen.add(`${parts[0]}.${parts[1]}`);
      } else {
        seen.add(withoutSuffix);
      }
    }
  }

  return seen;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('[scheduled-icr-scan] ICR-S6 — Scheduled Conflict Scan');

  const detector = new IntraSignalDetector({
    msr_path: MSR_PATH,
    forensic_path: FORENSIC_PATH,
  });

  const conflicts = await detector.detectAll();
  console.log(`[scheduled-icr-scan] ${conflicts.length} total conflict(s) detected.`);

  const handled = collectHandledIds(REPO_ROOT);
  console.log(
    `[scheduled-icr-scan] Already-handled IDs: ${[...handled].join(', ') || '(none)'}`,
  );

  let emitted = 0;

  for (const conflict of conflicts) {
    if (handled.has(conflict.conflict_id)) {
      console.log(`[scheduled-icr-scan] Skipping ${conflict.conflict_id} (already handled).`);
      continue;
    }

    // Emit a minimal PROPOSED/ artifact for native human review.
    // Values marked [REVIEW REQUIRED] must be filled in by a human or a
    // more context-aware session before ICR-S5 can apply the patch.
    const signalId = conflict.signal_ids_affected[0] ?? 'UNKNOWN';

    const filePath = emitProposePatch(REPO_ROOT, conflict, {
      conflict_id: conflict.conflict_id,
      signal_id: signalId,
      field: 'signal_name',
      current_value: '[REVIEW REQUIRED — extract current value from MSR]',
      proposed_value: '[REVIEW REQUIRED — determine correct value from FORENSIC]',
      rationale: conflict.description,
      propagation_chain: [
        '[REVIEW REQUIRED — identify downstream signals referencing this value]',
      ],
    });

    console.log(`[scheduled-icr-scan] Emitted PROPOSED/ for ${conflict.conflict_id}: ${filePath}`);
    emitted++;
  }

  console.log(
    `[scheduled-icr-scan] Scan complete: ` +
      `${conflicts.length} conflict(s) found, ` +
      `${emitted} new PROPOSED/ artifact(s) emitted, ` +
      `${handled.size} already handled.`,
  );
}

main().catch(err => {
  console.error('[scheduled-icr-scan] Fatal error:', err);
  process.exit(1);
});
