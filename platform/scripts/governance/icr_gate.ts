#!/usr/bin/env tsx
/**
 * icr_gate.ts — CI conflict gate
 * ICR-S6 (2026-05-21): Fail if new unresolved Class A conflicts are detected.
 *
 * Usage (from repo root):
 *   npx tsx platform/scripts/governance/icr_gate.ts
 *
 * Exit codes:
 *   0 — all detected conflicts are already in RESOLVED/
 *   1 — one or more conflicts NOT in RESOLVED/ were found
 */

import { readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { IntraSignalDetector } from '../../src/lib/icr/detector';
import type { ConflictRecord } from '../../src/lib/icr/types';

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
const RESOLVED_DIR = resolve(REPO_ROOT, '00_ARCHITECTURE', 'CONFLICT_PATCHES', 'RESOLVED');

// ─────────────────────────────────────────────────────────────────────────────
// Exported pure helpers (used by tests)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parse the conflict_id out of a RESOLVED/ filename.
 *
 * Convention: `{conflict_id}_{signal_id_dotless}_resolved.yaml`
 * Examples:
 *   DIS.013_MSR_377_resolved.yaml → "DIS.013"
 *   DIS.AUTO.42_MSR_42_resolved.yaml → "DIS.AUTO.42"
 *
 * Strategy: strip the `_resolved.yaml` suffix, then find the last segment
 * starting with `MSR_` or `UCN_` or similar and take everything before it.
 */
export function parseResolvedId(filename: string): string {
  const withoutSuffix = filename.replace(/_resolved\.yaml$/, '');

  // Split on the first occurrence of a known signal-id prefix pattern
  // e.g. "_MSR_", "_UCN_", "_CDLM_", "_RM_"
  const signalIdSepRe = /_(MSR|UCN|CDLM|RM|CGM|LEL)_/;
  const sepIdx = withoutSuffix.search(signalIdSepRe);
  if (sepIdx !== -1) {
    return withoutSuffix.slice(0, sepIdx);
  }

  // Fallback: take everything before the second underscore segment
  // e.g. "DIS_013_something" → "DIS.013" (replace first _ with .)
  const parts = withoutSuffix.split('_');
  if (parts.length >= 2 && parts[0] === 'DIS') {
    return `${parts[0]}.${parts[1]}`;
  }

  return withoutSuffix;
}

/**
 * Read the RESOLVED/ directory and return the set of conflict_ids that are
 * already resolved.
 */
export function loadResolvedIds(resolvedDir: string): Set<string> {
  const ids = new Set<string>();
  if (!existsSync(resolvedDir)) return ids;

  for (const filename of readdirSync(resolvedDir)) {
    if (!filename.endsWith('_resolved.yaml')) continue;
    ids.add(parseResolvedId(filename));
  }
  return ids;
}

/**
 * Filter a conflict list, returning only those NOT in the resolved set.
 */
export function filterUnresolved(
  conflicts: ConflictRecord[],
  resolvedIds: Set<string>,
): ConflictRecord[] {
  return conflicts.filter(c => !resolvedIds.has(c.conflict_id));
}

// ─────────────────────────────────────────────────────────────────────────────
// Main gate logic
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('[icr-gate] ICR-S6 — Intra-Signal Conflict Gate');
  console.log(`[icr-gate] RESOLVED dir: ${RESOLVED_DIR}`);

  const detector = new IntraSignalDetector({
    msr_path: MSR_PATH,
    forensic_path: FORENSIC_PATH,
  });

  const conflicts = await detector.detectAll();
  console.log(`[icr-gate] Detector found ${conflicts.length} total conflict(s).`);

  const resolvedIds = loadResolvedIds(RESOLVED_DIR);
  console.log(`[icr-gate] Resolved conflict IDs: ${[...resolvedIds].join(', ') || '(none)'}`);

  const unresolved = filterUnresolved(conflicts, resolvedIds);

  if (unresolved.length === 0) {
    console.log(
      `[icr-gate] PASS — ${conflicts.length} conflict(s) detected, all present in RESOLVED/.`,
    );
    process.exit(0);
  }

  console.error(
    `[icr-gate] FAIL — ${unresolved.length} unresolved conflict(s) not in RESOLVED/:`,
  );
  for (const c of unresolved) {
    console.error(`  ${c.conflict_id} [Class ${c.conflict_class}] — ${c.description}`);
  }
  process.exit(1);
}

// Only execute when run directly (not when imported by tests)
const isMain =
  typeof process !== 'undefined' &&
  process.argv[1] != null &&
  (process.argv[1].endsWith('icr_gate.ts') || process.argv[1].endsWith('icr_gate.js'));

if (isMain) {
  main().catch(err => {
    console.error('[icr-gate] Fatal error:', err);
    process.exit(1);
  });
}
