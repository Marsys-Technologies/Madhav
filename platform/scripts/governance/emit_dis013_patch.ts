#!/usr/bin/env npx tsx
/**
 * emit_dis013_patch.ts — ICR-S4 one-shot script
 *
 * Reads DIS.013 from ICR_DETECTOR_OUTPUT_v1_0.json and emits
 * PROPOSED/DIS.013_MSR_377_proposed.yaml describing the correction to
 * MSR.377's signal_name.
 *
 * The emitted artifact requires native human review before ICR-S5 can apply it.
 * This script NEVER modifies MSR_v3_0.md or any other synthesis file.
 *
 * Usage:
 *   cd platform && npx tsx scripts/governance/emit_dis013_patch.ts
 */

import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import { emitProposePatch } from '../../src/lib/icr/patch_emitter';
import type { ConflictRecord } from '../../src/lib/icr/types';

// ─────────────────────────────────────────────────────────────────────────────
// Paths
// ─────────────────────────────────────────────────────────────────────────────

// Script lives at platform/scripts/governance/emit_dis013_patch.ts
// Repo root is two levels up from platform/
const PLATFORM_DIR = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(PLATFORM_DIR, '..');
const DETECTOR_OUTPUT_PATH = path.join(
  REPO_ROOT,
  '06_LEARNING_LAYER',
  'ICR_DETECTOR_OUTPUT_v1_0.json',
);

// ─────────────────────────────────────────────────────────────────────────────
// Load detector output
// ─────────────────────────────────────────────────────────────────────────────

interface DetectorOutput {
  generated_at: string;
  corpus_version: string;
  conflict_count: number;
  conflicts: ConflictRecord[];
}

const raw = readFileSync(DETECTOR_OUTPUT_PATH, 'utf-8');
const output: DetectorOutput = JSON.parse(raw);

const dis013 = output.conflicts.find(c => c.conflict_id === 'DIS.013');
if (!dis013) {
  console.error('ERROR: DIS.013 not found in detector output');
  process.exit(1);
}

// ─────────────────────────────────────────────────────────────────────────────
// Extract current (wrong) signal_name from evidence field
// ─────────────────────────────────────────────────────────────────────────────

// Evidence format: `signal_name: "..." | falsifier: "..." | ...`
const evidenceSignalNameMatch = dis013.evidence.match(/signal_name:\s*"([^"]+)"/);
if (!evidenceSignalNameMatch) {
  console.error('ERROR: Could not extract signal_name from DIS.013 evidence');
  process.exit(1);
}
const currentSignalName = evidenceSignalNameMatch[1];

// ─────────────────────────────────────────────────────────────────────────────
// Emit patch
// ─────────────────────────────────────────────────────────────────────────────

const writtenPath = emitProposePatch(
  REPO_ROOT,
  dis013,
  {
    conflict_id: dis013.conflict_id,
    signal_id: 'MSR.377',
    field: 'signal_name',
    current_value: currentSignalName,
    proposed_value:
      'Tajika — Muntha Position at Age 42 (2026): Muntha in Virgo 6H = Dusthana Annual Activation (6H: Health/Service/Conflict)',
    rationale:
      'Muntha year = birth_year + age = 1984 + 42 = 2026; 42 mod 12 = 6; ' +
      '6th sign from Aries = Virgo (Aries=1, Taurus=2, Gemini=3, Cancer=4, Leo=5, Virgo=6); ' +
      '6th house in this chart. signal_name incorrectly states Gemini 3H. ' +
      'Falsifier confirms Virgo 6H. The supporting_rules block within the same signal also ' +
      'correctly states Virgo 6H — the error is confined to signal_name only.',
    propagation_chain: [
      'MSR.377 signal_name (primary correction target)',
      'any downstream signal that references Muntha sign as Gemini (search MSR for "Muntha" + "Gemini")',
      'UCN sections referencing Muntha position in 2026 annual layer',
      'CDLM cells that link Muntha-Gemini to 3H domains (UL/spouse-domain framing would need revision to 6H health/service framing)',
    ],
  },
);

console.log(`PROPOSED artifact written: ${writtenPath}`);
console.log('');
console.log('--- REVIEW REQUIRED ---');
console.log('This patch requires native human review before ICR-S5 can apply it.');
console.log('Artifact path:', writtenPath);
