// patch_emitter.ts — ICR stream, propose-patch protocol
// ICR-S4 (2026-05-21): ProposePatch type + emitProposePatch() function
//
// PROPOSED/ artifacts require native human review before ICR-S5 can apply them.
// This module NEVER writes to MSR, UCN, CDLM, RM, or any L1/L2.5 synthesis file.

import { writeFileSync, mkdirSync } from 'node:fs';
import * as path from 'node:path';
import type { ConflictRecord } from './types';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ProposePatch {
  conflict_id: string;
  signal_id: string;            // e.g. "MSR.377"
  field: string;                // field being corrected, e.g. "signal_name"
  current_value: string;        // current (incorrect) value
  proposed_value: string;       // corrected value
  rationale: string;            // why this correction
  propagation_chain: readonly string[];  // other fields/signals that may need updating
  proposed_at: string;          // ISO timestamp
  status: 'proposed';           // always 'proposed' at emit time
}

// ─────────────────────────────────────────────────────────────────────────────
// YAML serializer (manual — avoids introducing a new dependency)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Escape a string value for inline YAML double-quoted scalar.
 * Handles backslash and double-quote characters.
 */
function yamlEscapeString(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

/**
 * Serialize a ProposePatch to a YAML string.
 * Produces a flat, human-readable YAML document.
 */
export function serializeProposePatch(artifact: ProposePatch): string {
  const lines: string[] = [
    `conflict_id: ${artifact.conflict_id}`,
    `signal_id: ${artifact.signal_id}`,
    `field: ${artifact.field}`,
    `current_value: "${yamlEscapeString(artifact.current_value)}"`,
    `proposed_value: "${yamlEscapeString(artifact.proposed_value)}"`,
    `rationale: "${yamlEscapeString(artifact.rationale)}"`,
    `propagation_chain:`,
    ...artifact.propagation_chain.map(s => `  - "${yamlEscapeString(s)}"`),
    `proposed_at: ${artifact.proposed_at}`,
    `status: ${artifact.status}`,
  ];
  return lines.join('\n') + '\n';
}

// ─────────────────────────────────────────────────────────────────────────────
// Filename convention
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Derive the canonical PROPOSED/ filename for a patch.
 *
 * Convention: `{conflict_id}_{signal_id_dotless}_proposed.yaml`
 * e.g. DIS.013 + MSR.377 → "DIS.013_MSR_377_proposed.yaml"
 */
export function proposedFilename(conflictId: string, signalId: string): string {
  const safeSignalId = signalId.replace(/\./g, '_');
  return `${conflictId}_${safeSignalId}_proposed.yaml`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main emitter
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Emit a PROPOSED/ patch artifact for a conflict.
 *
 * @param repoRoot  Absolute path to the repository root (PROPOSED/ is created here)
 * @param conflict  The ConflictRecord from the ICR detector
 * @param patch     Patch details (without proposed_at and status — those are set here)
 * @returns         Absolute path to the written file
 *
 * Side-effects:
 *  - Creates `{repoRoot}/PROPOSED/` if it does not exist
 *  - Writes `{repoRoot}/PROPOSED/{conflict_id}_{signal_id}_proposed.yaml`
 *
 * NEVER modifies MSR, UCN, CDLM, RM, or any L1/L2.5 synthesis file.
 */
export function emitProposePatch(
  repoRoot: string,
  conflict: ConflictRecord,
  patch: Omit<ProposePatch, 'proposed_at' | 'status'>,
): string {
  const proposedDir = path.join(repoRoot, 'PROPOSED');
  mkdirSync(proposedDir, { recursive: true });

  const filename = proposedFilename(conflict.conflict_id, patch.signal_id);
  const fullPath = path.join(proposedDir, filename);

  const artifact: ProposePatch = {
    ...patch,
    proposed_at: new Date().toISOString(),
    status: 'proposed',
  };

  writeFileSync(fullPath, serializeProposePatch(artifact), 'utf-8');
  return fullPath;
}
