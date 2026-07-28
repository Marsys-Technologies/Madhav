/**
 * SAMĪKṢĀ prediction-ledger schema — PB-3 (SAMĪKṢĀ) lane L-1.
 *
 * SINGLE SOURCE OF TRUTH for the `brahma_mimamsa_prediction_ledger` row shape, its lifecycle
 * state set, the legal-transition matrix, and the immutable-once-confirmed field lists.
 * Backs migration 470 (supabase/migrations/470_pariprashna_samiksha_prediction_ledger.sql):
 * the DB CHECK enforces the lifecycle enum domain and the `trg_bmpl_freeze_confirmed` trigger
 * enforces immutability; THIS module enforces the transition matrix (the brief's "DAL
 * enforcing one legal-transition matrix") and validates row inputs.
 *
 * ISOMORPHIC on purpose — pure TypeScript + Zod, no `server-only`, no `pg` — so the writer,
 * reader, and transition helper share exactly these definitions and so the transition matrix
 * can be unit-tested with zero DB dependency.
 *
 * Table name is FIXED by MEMO_PB-3_0 (OT-11 ruling): brahma_mimamsa_prediction_ledger.
 */

import { z } from 'zod'

// ---------------------------------------------------------------------------
// Lifecycle states — the 9 tokens BRIEF_PB-3 §F1 names (it labels this an "8-state
// lifecycle" but enumerates nine; see migration 470's header for why all nine are kept).
// MUST stay in lockstep with migration 470's CHECK constraint.
// ---------------------------------------------------------------------------

export const LIFECYCLE_STATES = [
  'detected',
  'confirmed',
  'open',
  'window_closed',
  'outcome_recorded',
  'dismissed',
  'lapsed',
  'unverifiable',
  'lapsed_unconfirmed',
] as const

export const LifecycleStateSchema = z.enum(LIFECYCLE_STATES)
export type LifecycleState = z.infer<typeof LifecycleStateSchema>

/**
 * The ONE legal-transition matrix (single source of truth). Maps each state to the set of
 * states it may legally advance to. Any (from → to) pair NOT listed here is illegal and is
 * REJECTED by the DAL (transitions.ts / writer.ts), never silently applied.
 *
 * Faithful to the §14 lifecycle described across BRIEF_PB-3 (§F1, §5 W-1/W-2) + LEDGER_MAP:
 *   detected            → confirmed (human "Log to Samīkṣā" act; W-1 forbids auto-promotion)
 *                       → dismissed (candidate dismissed-with-reason)
 *                       → lapsed_unconfirmed (candidate ages out unconfirmed; W-1)
 *   confirmed           → open (row live, window being tracked)
 *                       → dismissed (undo an erroneous just-confirmed row)
 *   open                → window_closed (L-4 daily job: window_end < now)
 *   window_closed       → outcome_recorded (resolved: happened/did-not/partial → Brier)
 *                       → unverifiable (can't-tell → Brier-excluded; L-3 Resolve)
 *                       → lapsed (unresolved after close; W-2, non-shameful coverage gap)
 *   outcome_recorded, dismissed, lapsed, unverifiable, lapsed_unconfirmed → (terminal)
 */
export const LEGAL_TRANSITIONS: Readonly<Record<LifecycleState, readonly LifecycleState[]>> = {
  detected: ['confirmed', 'dismissed', 'lapsed_unconfirmed'],
  confirmed: ['open', 'dismissed'],
  open: ['window_closed'],
  window_closed: ['outcome_recorded', 'unverifiable', 'lapsed'],
  outcome_recorded: [],
  dismissed: [],
  lapsed: [],
  unverifiable: [],
  lapsed_unconfirmed: [],
} as const

/**
 * States a ledger row may be BORN in (INSERT). A row enters either as a `detected` shadow of
 * a candidate part, or directly as a `confirmed` claim (the primary path — confirmation
 * writes the L-1 row). A row can never be inserted straight into `open` / `outcome_recorded`
 * / a terminal exit — those are only reachable through a transition.
 */
export const LEGAL_INITIAL_STATES = ['detected', 'confirmed'] as const
export type LegalInitialState = (typeof LEGAL_INITIAL_STATES)[number]

// ---------------------------------------------------------------------------
// Immutable-once-confirmed field sets (mirror migration 470's trg_bmpl_freeze_confirmed).
// Kept here so code + tests reference the same authoritative lists as the DB trigger.
// ---------------------------------------------------------------------------

/** The five D-16 stamp fields, COPIED at confirmation, frozen thereafter. */
export const STAMP_FIELDS = [
  'build_id',
  'priors_version',
  'formula_versions',
  'ranking_config',
  'now_context_date',
] as const

/** The settled claim core, frozen once the row is past `detected`. */
export const SETTLED_CLAIM_FIELDS = ['claim_text', 'domain', 'window', 'confidence', 'direction'] as const

/** Every field the DB freezes once a row is confirmed. */
export const IMMUTABLE_AFTER_CONFIRM_FIELDS = [...STAMP_FIELDS, ...SETTLED_CLAIM_FIELDS] as const

// ---------------------------------------------------------------------------
// Outcome vocabulary (mirrors migration 470's `outcome` CHECK).
// ---------------------------------------------------------------------------

export const OUTCOME_VALUES = ['happened', 'did_not_happen', 'partial', 'unverifiable'] as const
export const OutcomeSchema = z.enum(OUTCOME_VALUES)
export type Outcome = z.infer<typeof OutcomeSchema>

// ---------------------------------------------------------------------------
// Range types — serialized as Postgres range literal strings at the DAL boundary.
// ---------------------------------------------------------------------------

/** A daterange, as inclusive-lower / exclusive-upper ISO dates (Postgres `[lo,hi)` default). */
export interface DateWindow {
  /** ISO yyyy-mm-dd, inclusive lower bound. */
  start: string
  /** ISO yyyy-mm-dd, exclusive upper bound. */
  end: string
}

/** A numrange for a confidence band, `[lo,hi)` in [0,1]. */
export interface ConfidenceBand {
  low: number
  high: number
}

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/
export const DateWindowSchema = z
  .object({ start: z.string().regex(ISO_DATE_RE), end: z.string().regex(ISO_DATE_RE) })
  .strict()
export const ConfidenceBandSchema = z
  .object({ low: z.number().min(0).max(1), high: z.number().min(0).max(1) })
  .strict()
  .refine((b) => b.low <= b.high, { message: 'confidence low must be <= high' })

// ---------------------------------------------------------------------------
// Row shapes
// ---------------------------------------------------------------------------

const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/
export const UuidLikeSchema = z.string().regex(UUID_RE, 'must be an 8-4-4-4-12 hex UUID')

/**
 * The D-16 provenance stamp COPIED onto a ledger row at confirmation. Structurally mirrors
 * `TurnProvenanceStamp` (provenance/stamp.ts) — the read API getLastTurnStamp() returns this.
 * D-16(d): these values are COPIED into the row's columns, never FK'd / joined live.
 */
export interface LedgerStamp {
  build_id: string | null
  priors_version: string
  formula_versions: unknown
  ranking_config: unknown
  now_context_date: string
}

/** Input to create a ledger row (insert). */
export const CreateLedgerRowInputSchema = z
  .object({
    chart_id: UuidLikeSchema,
    message_part_id: UuidLikeSchema.nullable().optional(),
    claim_text: z.string().min(1),
    domain: z.string().nullable().optional(),
    window: DateWindowSchema.nullable().optional(),
    confidence: ConfidenceBandSchema.nullable().optional(),
    direction: z.string().nullable().optional(),
    technique_refs: z.array(z.string()).optional(),
    grounding_fact_ids: z.array(z.string()).optional(),
    created_from_channel: z.string().optional(),
    /** Born state: 'detected' (candidate shadow) or 'confirmed' (primary path). */
    initial_status: z.enum(LEGAL_INITIAL_STATES).optional(),
    /** Required when initial_status === 'confirmed' (the stamp is copied at confirmation). */
    stamp: z
      .object({
        build_id: z.string().nullable(),
        priors_version: z.string(),
        formula_versions: z.unknown(),
        ranking_config: z.unknown(),
        now_context_date: z.string(),
      })
      .optional(),
  })
  .strict()
export type CreateLedgerRowInput = z.infer<typeof CreateLedgerRowInputSchema>

/** A ledger row as read back from the DB. */
export interface LedgerRow {
  id: string
  chart_id: string
  message_part_id: string | null
  claim_text: string
  domain: string | null
  window: string | null // raw daterange literal, e.g. "[2026-01-01,2026-12-31)"
  confidence: string | null // raw numrange literal, e.g. "[0.6,0.8)"
  direction: string | null
  technique_refs: string[]
  grounding_fact_ids: string[]
  created_from_channel: string
  lifecycle_status: LifecycleState
  build_id: string | null
  priors_version: string | null
  formula_versions: unknown
  ranking_config: unknown
  now_context_date: string | null
  stamp_copied_at: string | null
  outcome: Outcome | null
  outcome_value: number | null
  outcome_note: string | null
  outcome_recorded_at: string | null
  confirmed_at: string | null
  dismissed_reason: string | null
  created_at: string
  updated_at: string
}

export const LEDGER_TABLE = 'brahma_mimamsa_prediction_ledger' as const

// ---------------------------------------------------------------------------
// Range literal helpers (TS object <-> Postgres range literal string).
// ---------------------------------------------------------------------------

/** `{start,end}` → Postgres daterange literal `[start,end)`. */
export function toDaterangeLiteral(w: DateWindow | null | undefined): string | null {
  if (!w) return null
  return `[${w.start},${w.end})`
}

/** `{low,high}` → Postgres numrange literal `[low,high)`. */
export function toNumrangeLiteral(c: ConfidenceBand | null | undefined): string | null {
  if (!c) return null
  return `[${c.low},${c.high})`
}
