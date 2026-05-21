#!/usr/bin/env tsx
/**
 * run_icr_detector.ts — Governance script for the ICR Class A conflict detector
 *
 * ICR-S3 (2026-05-21): Runs the IntraSignalDetector against the live corpus
 * (MSR_v3_0.md + FORENSIC_ASTROLOGICAL_DATA_v8_0.md) and writes the output
 * to 06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json.
 *
 * Usage:
 *   cd platform && npx tsx scripts/governance/run_icr_detector.ts
 *
 * Exit codes:
 *   0 — at least one conflict detected (PASS — smoke gate requires ≥1)
 *   1 — no conflicts detected or error
 */

import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { IntraSignalDetector } from '../../src/lib/icr/detector';
import type { ConflictRecord } from '../../src/lib/icr/types';

// ─────────────────────────────────────────────────────────────────────────────
// Paths
// ─────────────────────────────────────────────────────────────────────────────

const SCRIPT_DIR = dirname(new URL(import.meta.url).pathname);
const REPO_ROOT = resolve(SCRIPT_DIR, '..', '..', '..');

const MSR_PATH = resolve(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v3_0.md');
const FORENSIC_PATH = resolve(
  REPO_ROOT,
  '01_FACTS_LAYER',
  'FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
);
const OUTPUT_PATH = resolve(
  REPO_ROOT,
  '06_LEARNING_LAYER',
  'ICR_DETECTOR_OUTPUT_v1_0.json',
);

// ─────────────────────────────────────────────────────────────────────────────
// Output schema (matches §G of ICR-S3_BRIEF_v1_0.md)
// ─────────────────────────────────────────────────────────────────────────────

interface DetectorOutput {
  generated_at: string;
  corpus_version: string;
  conflict_count: number;
  conflicts: ConflictRecord[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('[run_icr_detector] ICR-S3 — Class A conflict detector');
  console.log(`[run_icr_detector] MSR path:     ${MSR_PATH}`);
  console.log(`[run_icr_detector] FORENSIC path: ${FORENSIC_PATH}`);

  const detector = new IntraSignalDetector({
    msr_path: MSR_PATH,
    forensic_path: FORENSIC_PATH,
  });

  console.log('[run_icr_detector] Running detectAll()...');
  let conflicts: ConflictRecord[];
  try {
    conflicts = await detector.detectAll();
  } catch (err) {
    console.error('[run_icr_detector] ERROR during detection:', err);
    process.exit(1);
  }

  console.log(`[run_icr_detector] Detection complete. ${conflicts.length} conflict(s) found.`);

  if (conflicts.length === 0) {
    console.error('[run_icr_detector] FAIL — intra_signal_munta_detected gate: 0 conflicts detected.');
    console.error('[run_icr_detector] Expected at least 1 conflict (DIS.013 / MSR.377).');
    process.exit(1);
  }

  // Print summary
  for (const c of conflicts) {
    console.log(
      `  [${c.conflict_class}] ${c.conflict_id} — signal(s): ${c.signal_ids_affected.join(', ')}`,
    );
    console.log(`      ${c.description}`);
  }

  // Check smoke gate: MSR.377 must be present with class A
  const msr377 = conflicts.find(
    (c) =>
      c.signal_ids_affected.includes('MSR.377') && c.conflict_class === 'A',
  );
  if (msr377) {
    console.log('[run_icr_detector] PASS — MSR.377 detected as Class A conflict (DIS.013).');
  } else {
    console.warn('[run_icr_detector] WARNING — MSR.377 / Class A not in output. Smoke gate may fail.');
    console.warn('[run_icr_detector] Conflict IDs found:', conflicts.map((c) => c.signal_ids_affected).flat().join(', '));
  }

  // Serialise output
  const output: DetectorOutput = {
    generated_at: new Date().toISOString(),
    corpus_version: 'MSR_v3_0.md v3.1 (514 signals)',
    conflict_count: conflicts.length,
    conflicts,
  };

  // Ensure output directory exists
  mkdirSync(dirname(OUTPUT_PATH), { recursive: true });
  writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`[run_icr_detector] Output written to: ${OUTPUT_PATH}`);
}

main().catch((err) => {
  console.error('[run_icr_detector] Unhandled error:', err);
  process.exit(1);
});
