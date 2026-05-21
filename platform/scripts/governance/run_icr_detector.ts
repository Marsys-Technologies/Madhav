#!/usr/bin/env tsx
/**
 * run_icr_detector.ts — Governance runner for the ICR intra-signal conflict detector
 *
 * ICR-S3 (2026-05-21): Runs IntraSignalDetector against the live MSR corpus
 * and writes the conflict list to 06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json.
 *
 * Usage (from repo root):
 *   npx tsx platform/scripts/governance/run_icr_detector.ts
 *
 * Exit codes:
 *   0 — always (this script is an emitter, not a CI gate)
 */

import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { IntraSignalDetector } from '../../src/lib/icr/detector';

// ─────────────────────────────────────────────────────────────────────────────
// Paths (resolved from repo root — two levels up from scripts/governance/)
// ─────────────────────────────────────────────────────────────────────────────

const SCRIPT_DIR = dirname(new URL(import.meta.url).pathname);
const REPO_ROOT = resolve(SCRIPT_DIR, '..', '..', '..');

const MSR_PATH = resolve(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md');
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
// Run
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('[run_icr_detector] ICR-S3 — Intra-Signal Conflict Detector');
  console.log(`[run_icr_detector] MSR path:     ${MSR_PATH}`);
  console.log(`[run_icr_detector] Forensic path: ${FORENSIC_PATH}`);
  console.log(`[run_icr_detector] Output path:  ${OUTPUT_PATH}`);
  console.log('');

  const detector = new IntraSignalDetector({
    msr_path: MSR_PATH,
    forensic_path: FORENSIC_PATH,
  });

  const conflicts = await detector.detectAll();

  console.log(`[run_icr_detector] Detection complete.`);
  console.log(`ICR-S3: ${conflicts.length} conflicts detected`);
  console.log('');

  if (conflicts.length > 0) {
    console.log('Conflicts found:');
    for (const c of conflicts) {
      console.log(
        `  ${c.conflict_id} [Class ${c.conflict_class}] — ${c.signal_ids_affected.join(', ')} — ${c.description.slice(0, 80)}...`,
      );
    }
    console.log('');
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Write output JSON
  // ─────────────────────────────────────────────────────────────────────────

  const output = {
    generated_at: new Date().toISOString(),
    corpus_version: 'MSR_v3_0.md',
    conflict_count: conflicts.length,
    conflicts,
  };

  mkdirSync(dirname(OUTPUT_PATH), { recursive: true });
  writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2) + '\n', 'utf-8');

  console.log(`[run_icr_detector] Output written to: ${OUTPUT_PATH}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Entry point
// ─────────────────────────────────────────────────────────────────────────────

main().then(() => process.exit(0)).catch((err) => {
  console.error('[run_icr_detector] Fatal error:', err);
  process.exit(1);
});
