// Conflict detection types for the ICR stream
// ICR-S1: scaffold session (2026-05-21)

export type ConflictClass = 'A' | 'B' | 'C';

export interface ConflictRecord {
  conflict_id: string;            // e.g. "DIS.013"
  conflict_class: ConflictClass;
  signal_ids_affected: string[];  // e.g. ["MSR.377"]
  description: string;
  detected_at: string;            // ISO timestamp
  evidence: string;               // what the detector found
}

export type ProposePathStatus = 'pending' | 'confirmed' | 'rejected' | 'escalated';

export interface ProposePatchArtifact {
  conflict_id: string;
  conflict_class: ConflictClass;
  signal_ids_affected: string[];
  proposed_change: string;               // diff-format string
  propagation_chain: PropagationChainTier[];
  confidence: number;                    // 0–1
  authored_by: string;
  authored_on: string;                   // ISO date
  status: ProposePathStatus;
}

export interface PropagationChainTier {
  tier: 1 | 2 | 3 | 4 | 5;
  tier_name: 'signal' | 'ucn_edges' | 'cdlm_links' | 'rm_paths' | 'synthesis_cache';
  mandatory: boolean;
  affected_ids: string[];
}
