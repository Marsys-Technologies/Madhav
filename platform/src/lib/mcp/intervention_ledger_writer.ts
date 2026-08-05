/**
 * intervention_ledger_writer.ts — the serve-time write path into
 * `mimamsa_intervention_ledger` (ṢAḌ-DARŚANA W4 item 42, gate G7).
 *
 * Spec: KALA_W4_UPAYA_DESIGN_v1_0.md (v1.1) §4.1 ruling S-1 + §4.2 (the table) + migration
 * 532's own comments: rows are "FILED live, at serve time, through the sanctioned HTTP
 * action" — the Python writer `mi_sankalpa` never ORIGINATES a row from an elected/adopted
 * candidate, it only re-classifies/links already-filed rows. Until this module landed there
 * was no such action anywhere (the gap PR #1055's harness lane disclosed); this is that
 * write path's server half, called only by `/api/mcp/writes/intervention_ledger_record`.
 *
 * Provenance: `filed_by` is stamped by the ROUTE from the resolved principal (X-MCP-User),
 * never trusted from the caller body — identical rule to `prospective_ledger_file`.
 *
 * Idempotency: the table's natural key UNIQUE (chart_id, intervention_class,
 * rite_or_activity_class, elected_window) makes re-recording the same adoption a no-op —
 * reported as `created: false` with the existing row's id, never an error and never a
 * duplicate. This function performs NO delete (§N.3's status-preserving rule belongs to the
 * `mi_sankalpa` rebuild path, not to serve-time filing, which only ever appends).
 *
 * Validation posture: beyond field-presence (the route's job) this module adds no
 * validation of its own — the table's CHECK constraints, FKs (`brahma_event_ontology`,
 * `brahma_prospective_ledger`), and the ADJUDICATION-12 `_inferred_never_sealed` CHECK are
 * the authorities, and their verbatim errors are surfaced to the caller (duplicating a
 * validator is how two copies drift — KALA_W4_UPAYA_DESIGN §4.4's own rule).
 */

import 'server-only'
import { query } from '@/lib/db/client'

export interface InterventionLedgerEntryInput {
  chart_id: string
  intent: string
  intervention_class: 'upaya' | 'yajna' | 'elected_activity'
  rite_or_activity_class: string
  event_class: string | null
  window_start: string
  window_end: string
  precision_regime: 'intra_day' | 'day_grade'
  precision_basis: string
  adjudication_record: Record<string, unknown>
  score_vector: Record<string, unknown>
  efficacy_tier: 'classically_attested' | 'traditional' | 'speculative_extension'
  source_citation: string
  paddhati_version: string
  predicted_differential: string
  prediction_id: string | null
  adoption_basis: 'native_directed' | 'session_inferred'
  authority_basis: string | null
  engine_version: string
  /** Stamped by the route from the resolved principal — never from the caller body. */
  filed_by: string
}

export interface InterventionLedgerRecordResult {
  intervention_id: string
  /** false ⇒ the natural key already existed (idempotent re-record). */
  created: boolean
}

export async function recordInterventionLedgerEntry(
  input: InterventionLedgerEntryInput
): Promise<InterventionLedgerRecordResult> {
  const inserted = await query<{ intervention_id: string }>(
    `INSERT INTO mimamsa_intervention_ledger (
        chart_id, intent, intervention_class, rite_or_activity_class, event_class,
        elected_window, precision_regime, precision_basis,
        adjudication_record, score_vector, efficacy_tier, source_citation,
        paddhati_version, predicted_differential, prediction_id,
        adoption_basis, authority_basis, filed_by, engine_version
     ) VALUES (
        $1, $2, $3, $4, $5,
        tstzrange($6::timestamptz, $7::timestamptz, '[)'), $8, $9,
        $10::jsonb, $11::jsonb, $12, $13,
        $14, $15, $16,
        $17, $18, $19, $20
     )
     ON CONFLICT ON CONSTRAINT mimamsa_intervention_ledger_natural_key DO NOTHING
     RETURNING intervention_id`,
    [
      input.chart_id,
      input.intent,
      input.intervention_class,
      input.rite_or_activity_class,
      input.event_class,
      input.window_start,
      input.window_end,
      input.precision_regime,
      input.precision_basis,
      JSON.stringify(input.adjudication_record),
      JSON.stringify(input.score_vector),
      input.efficacy_tier,
      input.source_citation,
      input.paddhati_version,
      input.predicted_differential,
      input.prediction_id,
      input.adoption_basis,
      input.authority_basis,
      input.filed_by,
      input.engine_version,
    ]
  )

  if (inserted.rows.length > 0) {
    return { intervention_id: inserted.rows[0]!.intervention_id, created: true }
  }

  // Natural-key conflict — idempotent re-record. Resolve the existing row's id.
  const existing = await query<{ intervention_id: string }>(
    `SELECT intervention_id FROM mimamsa_intervention_ledger
      WHERE chart_id = $1
        AND intervention_class = $2
        AND rite_or_activity_class = $3
        AND elected_window = tstzrange($4::timestamptz, $5::timestamptz, '[)')`,
    [
      input.chart_id,
      input.intervention_class,
      input.rite_or_activity_class,
      input.window_start,
      input.window_end,
    ]
  )
  if (existing.rows.length === 0) {
    // ON CONFLICT DO NOTHING fired but the natural-key row is not findable — surface loudly
    // rather than fabricating success (§N.8: a signal needs a real detector behind it).
    throw new Error(
      'intervention_ledger_record: insert conflicted on the natural key but the existing row ' +
        'could not be resolved — nothing recorded'
    )
  }
  return { intervention_id: existing.rows[0]!.intervention_id, created: false }
}
