#!/usr/bin/env tsx
/**
 * run_icr_propose_patch.ts — Governance script for the ICR propose-patch step
 *
 * ICR-S4 (2026-05-21): Reads ICR_DETECTOR_OUTPUT_v1_0.json, builds a
 * ProposePatchArtifact for each ConflictRecord, and writes YAML files to
 * 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/.
 *
 * Usage:
 *   cd platform && npx tsx scripts/governance/run_icr_propose_patch.ts
 *
 * Exit codes:
 *   0 — all patch artifacts written successfully
 *   1 — error (no detector output, write failure, etc.)
 *
 * IMPORTANT: this script NEVER applies patches to canonical corpus files.
 * Patches land in PROPOSED/ only and require NATIVE_REVIEW before apply.
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { buildProposePatchArtifact } from '../../src/lib/icr/propose_patch';
import type { ConflictRecord } from '../../src/lib/icr/types';

// ─────────────────────────────────────────────────────────────────────────────
// Paths
// ─────────────────────────────────────────────────────────────────────────────

const SCRIPT_DIR = dirname(new URL(import.meta.url).pathname);
const REPO_ROOT = resolve(SCRIPT_DIR, '..', '..', '..');

const DETECTOR_OUTPUT_PATH = resolve(
  REPO_ROOT,
  '06_LEARNING_LAYER',
  'ICR_DETECTOR_OUTPUT_v1_0.json',
);

const UCN_PATH = resolve(
  REPO_ROOT,
  '025_HOLISTIC_SYNTHESIS',
  'UCN_v4_0.md',
);

const PROPOSED_DIR = resolve(
  REPO_ROOT,
  '00_ARCHITECTURE',
  'CONFLICT_PATCHES',
  'PROPOSED',
);

// ─────────────────────────────────────────────────────────────────────────────
// YAML serialiser (minimal — avoids yaml dep, outputs valid YAML for flat docs)
// ─────────────────────────────────────────────────────────────────────────────

function toYaml(artifact: ReturnType<typeof buildProposePatchArtifact>): string {
  const lines: string[] = [];

  lines.push(`conflict_id: ${artifact.conflict_id}`);
  lines.push(`conflict_class: ${artifact.conflict_class}`);
  lines.push(`signal_ids_affected:`);
  for (const id of artifact.signal_ids_affected) {
    lines.push(`  - ${id}`);
  }

  // proposed_change as multiline block scalar
  lines.push(`proposed_change: |`);
  for (const l of artifact.proposed_change.split('\n')) {
    lines.push(`  ${l}`);
  }

  lines.push(`confidence: ${artifact.confidence}`);
  lines.push(`authored_by: ${artifact.authored_by}`);
  lines.push(`authored_on: "${artifact.authored_on}"`);
  lines.push(`status: ${artifact.status}`);

  // propagation_chain
  lines.push(`propagation_chain:`);
  for (const tier of artifact.propagation_chain) {
    lines.push(`  - tier: ${tier.tier}`);
    lines.push(`    tier_name: ${tier.tier_name}`);
    lines.push(`    mandatory: ${tier.mandatory}`);
    lines.push(`    affected_ids:`);
    if (tier.affected_ids.length === 0) {
      lines.push(`      []`);
    } else {
      for (const id of tier.affected_ids) {
        lines.push(`      - ${id}`);
      }
    }
  }

  lines.push(`native_review_required: true`);
  lines.push(`auto_apply: false`);

  return lines.join('\n') + '\n';
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

interface DetectorOutput {
  generated_at: string;
  corpus_version: string;
  conflict_count: number;
  conflicts: ConflictRecord[];
}

async function main(): Promise<void> {
  console.log('[run_icr_propose_patch] ICR-S4 — propose-patch generator');
  console.log(`[run_icr_propose_patch] Detector output: ${DETECTOR_OUTPUT_PATH}`);
  console.log(`[run_icr_propose_patch] PROPOSED dir:    ${PROPOSED_DIR}`);

  // Read detector output
  let detectorOutput: DetectorOutput;
  try {
    const raw = readFileSync(DETECTOR_OUTPUT_PATH, 'utf-8');
    detectorOutput = JSON.parse(raw) as DetectorOutput;
  } catch (err) {
    console.error('[run_icr_propose_patch] ERROR: Cannot read detector output:', err);
    process.exit(1);
  }

  console.log(
    `[run_icr_propose_patch] Found ${detectorOutput.conflict_count} conflict(s) in detector output.`,
  );

  if (detectorOutput.conflicts.length === 0) {
    console.log('[run_icr_propose_patch] No conflicts to process. Exiting cleanly.');
    process.exit(0);
  }

  // Ensure PROPOSED/ directory exists
  mkdirSync(PROPOSED_DIR, { recursive: true });

  let written = 0;

  for (const conflict of detectorOutput.conflicts) {
    console.log(
      `[run_icr_propose_patch] Building patch for ${conflict.conflict_id} (signal: ${conflict.signal_ids_affected.join(', ')})...`,
    );

    const artifact = buildProposePatchArtifact(conflict, {
      ucn_path: UCN_PATH,
      authored_on: '2026-05-21',
    });

    // File name: DIS.NNN_<SIGNAL_ID>_proposed.yaml
    const signalSlug = conflict.signal_ids_affected[0]?.replace('.', '_') ?? 'UNKNOWN';
    const fileName = `${conflict.conflict_id}_${signalSlug}_proposed.yaml`;
    const outputPath = resolve(PROPOSED_DIR, fileName);

    try {
      writeFileSync(outputPath, toYaml(artifact), 'utf-8');
      console.log(`[run_icr_propose_patch] Written: ${outputPath}`);
      written++;
    } catch (err) {
      console.error(`[run_icr_propose_patch] ERROR: Cannot write ${outputPath}:`, err);
      process.exit(1);
    }
  }

  console.log(`[run_icr_propose_patch] Done. ${written} patch artifact(s) written to PROPOSED/.`);
  console.log('[run_icr_propose_patch] NATIVE_REVIEW_REQUIRED — patches must not be auto-applied.');
}

main().catch((err) => {
  console.error('[run_icr_propose_patch] Unhandled error:', err);
  process.exit(1);
});
