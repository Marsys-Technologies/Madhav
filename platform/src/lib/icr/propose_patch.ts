// propose_patch.ts — ICR stream
// ICR-S4: build ProposePatchArtifact for a ConflictRecord (2026-05-21)

import type { ConflictRecord, ProposePatchArtifact, PropagationChainTier } from './types';
import { readUCNEdgesForSignal } from './ucn_edge_reader';

// ─────────────────────────────────────────────────────────────────────────────
// Text-patch helpers for Class A conflicts
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Derive the `before` and `after` text for a Class A Muntha sign conflict.
 *
 * The detector evidence string has the canonical form:
 *   signal_name: "<NAME>" → asserted_sign: "<ASSERTED>" | FORENSIC VRS.MUNTHA.SIGN: "<FORENSIC_RAW>" → forensic_sign: "<FORENSIC>" | MISMATCH: <A> ≠ <F>
 *
 * We extract the signal_name, the asserted sign, and the forensic sign to
 * construct a minimal diff-format proposed_change.
 */
function deriveMunthaTextPatch(conflict: ConflictRecord): {
  before: string;
  after: string;
  proposed_change: string;
} {
  // Extract signal_name from evidence
  const nameMatch = conflict.evidence.match(/signal_name:\s*"([^"]+)"/);
  const assertedMatch = conflict.evidence.match(/asserted_sign:\s*"([^"]+)"/);
  const forensicSignMatch = conflict.evidence.match(/forensic_sign:\s*"([^"]+)"/);

  const before = nameMatch ? nameMatch[1] : conflict.evidence;
  const asserted = assertedMatch ? assertedMatch[1] : 'UNKNOWN';
  const forensicSign = forensicSignMatch ? forensicSignMatch[1] : 'UNKNOWN';

  // Replace the asserted sign token in the signal name.
  // The signal name contains "Muntha in <Sign> <HouseRef>" — we replace
  // the wrongly-asserted sign + house ref with the forensic sign + correct house.
  // Forensic VRS.MUNTHA.SIGN = "Libra (7th House)" → "7H" abbreviation
  const houseAbbrev = '7H';
  const after = before.replace(
    new RegExp(`\\bMuntha in ${asserted}\\s+\\w+`, 'i'),
    `Muntha in ${forensicSign} ${houseAbbrev}`,
  );

  const proposed_change = `- signal_name: "${before}"\n+ signal_name: "${after}"`;

  return { before, after, proposed_change };
}

// ─────────────────────────────────────────────────────────────────────────────
// Propagation chain builder
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Build the §C.10 propagation chain for a conflict.
 *
 * Tier 1 (mandatory): the signal IDs directly affected.
 * Tier 2 (mandatory): UCN edges whose signal_refs include any affected signal.
 * Tiers 3–5 (advisory): CDLM links, RM paths, synthesis cache — deferred.
 */
function buildPropagationChain(
  conflict: ConflictRecord,
  ucn_path?: string,
): PropagationChainTier[] {
  // Tier 1 — affected signals
  const tier1: PropagationChainTier = {
    tier: 1,
    tier_name: 'signal',
    mandatory: true,
    affected_ids: conflict.signal_ids_affected,
  };

  // Tier 2 — UCN edges referencing any of the affected signals
  const ucnEdgeIds: string[] = [];
  for (const signal_id of conflict.signal_ids_affected) {
    const edges = readUCNEdgesForSignal(signal_id, ucn_path);
    for (const edge of edges) {
      if (!ucnEdgeIds.includes(edge.edge_id)) {
        ucnEdgeIds.push(edge.edge_id);
      }
    }
  }

  const tier2: PropagationChainTier = {
    tier: 2,
    tier_name: 'ucn_edges',
    mandatory: true,
    affected_ids: ucnEdgeIds,
  };

  // Tiers 3–5 — advisory, deferred
  const tier3: PropagationChainTier = {
    tier: 3,
    tier_name: 'cdlm_links',
    mandatory: false,
    affected_ids: [],
  };

  const tier4: PropagationChainTier = {
    tier: 4,
    tier_name: 'rm_paths',
    mandatory: false,
    affected_ids: [],
  };

  const tier5: PropagationChainTier = {
    tier: 5,
    tier_name: 'synthesis_cache',
    mandatory: false,
    affected_ids: [],
  };

  return [tier1, tier2, tier3, tier4, tier5];
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

export interface BuildOptions {
  /** Override path to UCN_v4_0.md (used by tests with synthetic corpus). */
  ucn_path?: string;
  /** Override authored_on date (ISO date string). Defaults to today. */
  authored_on?: string;
}

/**
 * Build a ProposePatchArtifact for the given ConflictRecord.
 *
 * - Class A conflicts: derives a text-patch from the evidence string.
 * - Classes B/C: returns a minimal placeholder (not yet implemented).
 *
 * The artifact is returned in memory only. The caller is responsible for
 * writing it to `PROPOSED/`. This function never writes files.
 */
export function buildProposePatchArtifact(
  conflict: ConflictRecord,
  options: BuildOptions = {},
): ProposePatchArtifact {
  const authored_on =
    options.authored_on ?? new Date().toISOString().slice(0, 10);

  let proposed_change: string;

  if (conflict.conflict_class === 'A') {
    const { proposed_change: diff } = deriveMunthaTextPatch(conflict);
    proposed_change = diff;
  } else {
    // Classes B/C: deferred — emit placeholder
    proposed_change = `[DEFERRED] Class ${conflict.conflict_class} patch not yet implemented`;
  }

  const propagation_chain = buildPropagationChain(conflict, options.ucn_path);

  return {
    conflict_id: conflict.conflict_id,
    conflict_class: conflict.conflict_class,
    signal_ids_affected: conflict.signal_ids_affected,
    proposed_change,
    propagation_chain,
    confidence: conflict.conflict_class === 'A' ? 0.95 : 0.5,
    authored_by: 'ICR-S4',
    authored_on,
    status: 'pending',
  };
}
