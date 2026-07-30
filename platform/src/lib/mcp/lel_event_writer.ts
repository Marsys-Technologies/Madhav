/**
 * lel_event_writer.ts — LEL (Life Event Log) intake WRITE path for MCP.
 *
 * Records a NEW life event for one chart into the chart-scoped `life_events`
 * table (chart-scoped since migration 423; unique key (chart_id, event_id)).
 *
 * This is the TypeScript sibling of the Python canonical intake in
 * `python-sidecar/brahmagyan/mimamsa/lel_intake.py`. The Python path back-fills
 * the historical 57 events and stamps them with the PRE_INSTRUMENT sentinel
 * `recorded_at`. THIS path is for real, going-forward events captured through
 * the instrument — so `recorded_at = now()` (a true observation timestamp,
 * NOT the sentinel).
 *
 * Prod `life_events` is a HYBRID schema: the brahma columns (domain,
 * outcome_observed, event_type, …) coexist with the legacy NOT-NULL columns
 * (category, source_section, build_id, chart_state, provenance). So the INSERT
 * writes the UNION superset — mirroring lel_intake.py's brahma branch — or it
 * fails a NOT-NULL constraint against prod.
 *
 * Validation: the event's class MUST be a known `brahma_event_ontology`
 * event_class_id (22 classes). Unknown classes are rejected — an intake payload
 * cannot invent a new event taxonomy.
 *
 * Idempotency: ON CONFLICT (chart_id, event_id) DO UPDATE refreshes the mutable
 * fields but NEVER clobbers `recorded_at` — the first observation time is
 * sacrosanct (a re-submit is a correction, not a new observation).
 *
 * ── ṢAḌ-DARŚANA W2 (Lane E): THIS IS THE LEL-APPEND HOOK ─────────────────────
 * An append here is what triggers the Living-LEL recalibration plane (registry
 * item 39). Per brief §2.5.5 — BINDING — that recalibration is dispatched as a
 * **standard, tracked, scoped build run** through the orchestrator, NEVER as a
 * side-channel recompute: the orchestrator stays the sole build-state writer and
 * Nirmāṇa must see state/progress/throughput for a recalibration exactly as for
 * any other build.
 *
 * The request body is built by `./lel_recalibration_dispatch.ts`
 * (`buildRecalibrationDispatch(chartId, [eventId])` → POST it to
 * `/api/cockpit/runs`). It is deliberately NOT called from inside this function:
 * this module is a pure write path with no HTTP client and no auth context, and
 * putting the dispatch here would give the write path the ability to drive a
 * build, which is the shape §2.5.5 exists to prevent. The caller owns the
 * hand-off. A 409 `RUN_ACTIVE` from that route is CORRECT behaviour — the append
 * is picked up by the next run — and must not be routed around.
 *
 * @module lel_event_writer
 */

import 'server-only'
import { v5 as uuidv5 } from 'uuid'
import { query } from '@/lib/db/client'

// DNS namespace — same base as lel_intake.py's _LEL_UUID_NAMESPACE so IDs are
// stable and collision-free across the two intake paths (distinct name prefix).
const LEL_UUID_NAMESPACE = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'

const BUILD_ID = 'lel_intake-api'

// ── Interfaces ────────────────────────────────────────────────────────────────

/**
 * A single life event submitted for intake.
 *
 * `event_class` is the load-bearing field: it must be a valid
 * brahma_event_ontology.event_class_id. `event_type` is the free-text label
 * stored on the row (defaults to `event_class`); `category` mirrors event_type.
 */
export interface LelEvent {
  /** Deterministic uuid5 is generated if absent; a caller may supply one. */
  event_id?: string
  /** MUST match a brahma_event_ontology.event_class_id. Validated. */
  event_class: string
  /** ISO date (YYYY-MM-DD). */
  event_date: string
  /** Free-text event label. Defaults to event_class. */
  event_type?: string
  /** Prose description of the event. */
  description: string
  /** Life domain (career, health, relationships, …). */
  domain: string
  /**
   * Has the outcome already been observed? For a not-yet-observed future event
   * this is false (the default). A past event being logged sets it true.
   */
  outcome_observed?: boolean
  /** Provenance citation string. Defaults to the build id. */
  source_citation?: string
}

/** Provenance stamped from the resolved principal (never from caller body). */
export interface LelEventProvenance {
  key_id: string
  trace_id: string | null
  caller_context?: string | null
}

export interface RecordLelEventArgs {
  chartId: string
  event: LelEvent
  provenance?: LelEventProvenance
}

export interface RecordLelEventResult {
  event_id: string
  /**
   * life_events.id (uuid PK) — added D-4a Lane A-4 so callers (the outcome-matching
   * hook in prospective_ledger.ts) can reference the row as matched_event_id without
   * a second lookup. Distinct from `event_id`, which is a text natural key.
   */
  id: string
  recorded_at: string
  /** true when a new row was inserted; false when an existing row was updated. */
  created: boolean
}

// ── event_id derivation ─────────────────────────────────────────────────────

/**
 * Deterministic uuid5 for an API-intake event. Re-submitting the same
 * (chart, class, date, description) coalesces via ON CONFLICT rather than
 * spawning a duplicate row.
 */
export function deriveLelEventId(chartId: string, event: LelEvent): string {
  const name = `LEL-INTAKE-API:${chartId}:${event.event_class}:${event.event_date}:${event.description}`
  return uuidv5(name, LEL_UUID_NAMESPACE)
}

// ── recordLelEvent ────────────────────────────────────────────────────────────

/**
 * Record a new life event for a chart.
 *
 * @throws if `event.event_class` is not a known brahma_event_ontology class.
 */
export async function recordLelEvent(
  { chartId, event, provenance }: RecordLelEventArgs
): Promise<RecordLelEventResult> {
  // 1. Validate the event class against the ontology (22 classes).
  const { rows: classRows } = await query<{ event_class_id: string }>(
    `SELECT event_class_id FROM brahma_event_ontology WHERE event_class_id = $1`,
    [event.event_class]
  )
  if (classRows.length === 0) {
    throw new Error(
      `Unknown event class '${event.event_class}': not present in brahma_event_ontology. ` +
      `Submit one of the ratified event classes.`
    )
  }

  const event_id = event.event_id ?? deriveLelEventId(chartId, event)
  const event_type = event.event_type ?? event.event_class
  const outcome_observed = event.outcome_observed ?? false
  const source_citation = event.source_citation ?? BUILD_ID

  const chart_state = JSON.stringify({ recorded_via: BUILD_ID })
  const row_provenance = JSON.stringify({
    source: source_citation,
    event_class: event.event_class,
    key_id: provenance?.key_id ?? null,
    trace_id: provenance?.trace_id ?? null,
    caller_context: provenance?.caller_context ?? null,
  })

  // 2. INSERT the full NOT-NULL superset (brahma + legacy columns).
  //    recorded_at = now() — a REAL observation, NOT the pre_instrument sentinel.
  //    ON CONFLICT DO UPDATE refreshes mutable fields but NEVER recorded_at.
  //    (xmax = 0) distinguishes a fresh insert (created) from an update.
  const { rows } = await query<{ id: string; event_id: string; recorded_at: string; created: boolean }>(
    `INSERT INTO life_events
        (chart_id, event_id, event_date, event_type, description,
         domain, outcome_observed, source_citation, recorded_at,
         category, source_section, build_id, chart_state, provenance)
     VALUES ($1::uuid, $2::uuid, $3::date, $4, $5,
             $6, $7, $8, now(),
             $9, $10, $11, $12::jsonb, $13::jsonb)
     ON CONFLICT (chart_id, event_id) DO UPDATE SET
        event_date       = EXCLUDED.event_date,
        event_type       = EXCLUDED.event_type,
        description      = EXCLUDED.description,
        domain           = EXCLUDED.domain,
        outcome_observed = EXCLUDED.outcome_observed,
        source_citation  = EXCLUDED.source_citation,
        category         = EXCLUDED.category,
        source_section   = EXCLUDED.source_section,
        chart_state      = EXCLUDED.chart_state,
        provenance       = EXCLUDED.provenance
     RETURNING id, event_id, recorded_at, (xmax = 0) AS created`,
    [
      chartId,
      event_id,
      event.event_date,
      event_type,
      event.description,
      event.domain,
      outcome_observed,
      source_citation,
      event_type,          // category (=event_type)
      source_citation,     // source_section
      BUILD_ID,            // build_id
      chart_state,         // chart_state (jsonb)
      row_provenance,      // provenance (jsonb)
    ]
  )

  const result = rows[0]
  return {
    event_id: result?.event_id ?? event_id,
    id: result?.id ?? event_id,
    recorded_at: result?.recorded_at ?? new Date().toISOString(),
    created: result?.created ?? true,
  }
}
