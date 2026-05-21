/**
 * disagreement_writer.ts — MCP disagreement flagging, writing to the in-DB
 * disagreement log (mcp_disagreements table, migration 071).
 *
 * Per DISAGREEMENT_REGISTER_v1_0.md §0 (LIVING artifact):
 *   The register is "the mechanical trace that silent overwriting is forbidden."
 *   This module provides a formal channel for MCP callers (Cowork sessions,
 *   Claude Chat integrations) to flag disagreements — signal contradictions,
 *   inter-session conflicts, or structural inconsistencies — to the native
 *   via the MARSYS governance surface.
 *
 * Persistence strategy (MCP-4-S1):
 *   Per IMPORTANT_CONTEXT override in the session brief: disagreements are
 *   written to the `mcp_disagreements` Postgres table (migration 071).
 *   The in-DB table is the machine-queryable surface; the human-readable
 *   DISAGREEMENT_REGISTER_v1_0.md markdown file is the governance surface.
 *   Significant MCP-sourced disagreements should be promoted to the markdown
 *   register by a governance session after native review.
 *
 * TODO(MCP-MIGRATION): A future governance session should review mcp_disagreements
 *   rows with status='open' and promote significant ones to the markdown
 *   DISAGREEMENT_REGISTER_v1_0.md as formal DR entries (DIS.NNN). The DR entry
 *   schema is in DISAGREEMENT_REGISTER_v1_0.md §2. Promotion criteria:
 *     - class = 'factual' touching an L1 fact (B.10 violation)
 *     - class = 'mirror_desync' (per ND.1 / §K.3)
 *     - Any disagreement the native identifies as requiring cross-register tracking
 *
 * Disagreement classes supported (DR §1 + §1a):
 *   'factual'            — contested fact (wrong house, planet, dasha date, etc.)
 *   'interpretive'       — same facts, different meaning assigned
 *   'structural'         — disagreement about architecture or scope
 *   'mirror_desync'      — mirror pair out of semantic parity (ND.1)
 *   'scope'              — in-scope vs out-of-scope dispute
 *   'output_conflict'    — two agents reach conflicting conclusions on same input
 *   'version_disagreement' — two surfaces claim different CURRENT versions
 *   'scope_disagreement' — proposal scope dispute
 *   'closure_disagreement' — whether a close criterion is met
 *   'l3_zero_supports'   — L3 report yields zero accepted SUPPORTS edges
 *   'panel_divergence'   — LLM panel members disagree
 *   'school_disagreement' — astrological tradition dispute
 *   'acceptance_rate_anomaly' — reconciler acceptance rate out of band
 *
 * @module disagreement_writer
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Disagreement class type ───────────────────────────────────────────────────

export type DisagreementClass =
  | 'factual'
  | 'interpretive'
  | 'structural'
  | 'mirror_desync'
  | 'scope'
  | 'output_conflict'
  | 'version_disagreement'
  | 'scope_disagreement'
  | 'closure_disagreement'
  | 'l3_zero_supports'
  | 'panel_divergence'
  | 'school_disagreement'
  | 'acceptance_rate_anomaly'

// ── Interface ─────────────────────────────────────────────────────────────────

/**
 * A disagreement entry to be logged via flag_disagreement.
 *
 * The native reviews entries in the mcp_disagreements table and promotes
 * significant ones to the formal DISAGREEMENT_REGISTER_v1_0.md as DR entries.
 */
export interface DisagreementEntry {
  /**
   * Generated: "DIS.MCP." + nanoid(8). Caller may provide; generated if absent.
   * Note: DR sequential IDs (DIS.001, DIS.002…) are reserved for the markdown
   * register. MCP entries use "DIS.MCP." prefix to distinguish them.
   */
  disagreement_id?: string
  /**
   * Class of disagreement. Must be one of the supported DR classes.
   * Matches the taxonomy in DISAGREEMENT_REGISTER_v1_0.md §1.
   */
  class: DisagreementClass
  /** 2–5 sentence description of the disagreement, when it was noticed, and why it cannot be silently resolved. */
  description: string
  /** The caller's session label (e.g. "Cowork_2026-05-21_career_reading"). */
  source_session: string
  /** Optional proposed resolution (Claude's recommendation for native review). */
  proposed_resolution: string | null
  /** Provenance. */
  source: {
    key_id: string
    trace_id: string | null
  }
  /** Optional: ISO timestamp. Defaults to now(). */
  logged_at?: string
}

// ── ID generation ─────────────────────────────────────────────────────────────

/**
 * Generate a new MCP disagreement ID.
 * Format: "DIS.MCP." + 8 uppercase alphanumeric chars.
 *
 * Separate from the DR sequential IDs (DIS.001…) to avoid namespace collision.
 */
function generateDisagreementId(): string {
  const uuid = crypto.randomUUID().replace(/-/g, '')
  return `DIS.MCP.${uuid.slice(0, 8).toUpperCase()}`
}

// ── flagDisagreement ──────────────────────────────────────────────────────────

/**
 * Log a disagreement to the mcp_disagreements table.
 *
 * This is a formal governance channel: MCP callers (Cowork, Claude Chat)
 * can surface signal contradictions, inter-session conflicts, or structural
 * issues without out-of-band communication.
 *
 * The entry is immediately queryable in the DB. The native reviews open
 * entries and promotes significant ones to DISAGREEMENT_REGISTER_v1_0.md.
 *
 * @param entry  The disagreement to log.
 * @returns      The disagreement_id (either provided or generated).
 */
export async function flagDisagreement(entry: DisagreementEntry): Promise<string> {
  const disagreement_id = entry.disagreement_id ?? generateDisagreementId()
  const logged_at = entry.logged_at ?? new Date().toISOString()

  try {
    await query(
      `INSERT INTO mcp_disagreements (
        disagreement_id, logged_at, class, description,
        source_session, proposed_resolution,
        key_id, trace_id
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT (disagreement_id) DO NOTHING`,
      [
        disagreement_id,
        logged_at,
        entry.class,
        entry.description,
        entry.source_session,
        entry.proposed_resolution ?? null,  // normalize undefined → null for DB
        entry.source.key_id,
        entry.source.trace_id,
      ]
    )
  } catch (err) {
    // Log but do not throw — a write failure should be surfaced to the caller
    // via the error envelope, not as a thrown exception that crashes the route.
    console.error('[disagreement_writer] flagDisagreement DB error', err)
    // Re-throw so the dispatcher can return an error envelope.
    throw err
  }

  return disagreement_id
}
