import 'server-only'
/**
 * SAMĪKṢĀ prediction-ledger writer DAL — PB-3 lane L-1.
 *
 * The typed write half for `brahma_mimamsa_prediction_ledger`. Enforces the ONE legal-
 * transition matrix (via transitions.ts) on every lifecycle move; illegal moves are
 * REJECTED before any DB write. The DB additionally backstops immutability
 * (trg_bmpl_freeze_confirmed) and the enum domain (CHECK) — this DAL never depends on the
 * caller to respect either.
 *
 * DB access goes through an injectable `LedgerExecutor` (defaulting to the shared pool). The
 * injection point exists so the integration test drives these functions against a REAL
 * throwaway Postgres with the REAL migration applied — not an in-memory mock of the writer
 * agreeing with itself (the PB-2 false-confidence-gate lesson). Production callers (L-2/L-3/
 * L-5) simply omit `exec` and get the shared client.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { assertLegalTransition } from './transitions'
import {
  CreateLedgerRowInputSchema,
  LEDGER_TABLE,
  LifecycleStateSchema,
  OutcomeSchema,
  toDaterangeLiteral,
  toNumrangeLiteral,
  type CreateLedgerRowInput,
  type LedgerRow,
  type LedgerStamp,
  type LifecycleState,
  type Outcome,
} from './schema'

/** A minimal query executor: anything that runs parameterized SQL and returns `{ rows }`.
 *  Satisfied by the shared client's `query` AND by a raw `pg.Pool`/`pg.PoolClient`. */
export type LedgerExecutor = <T = Record<string, unknown>>(
  sql: string,
  params?: unknown[],
) => Promise<{ rows: T[]; rowCount?: number | null }>

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

const RETURNING_COLS = `
  id, chart_id, message_part_id, claim_text, domain,
  "window"::text AS window, confidence::text AS confidence, direction,
  technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status,
  build_id, priors_version, formula_versions, ranking_config,
  now_context_date::text AS now_context_date, stamp_copied_at,
  outcome, outcome_value, outcome_note, outcome_recorded_at,
  confirmed_at, dismissed_reason, created_at, updated_at
`

// ── Create ──────────────────────────────────────────────────────────────────

/**
 * Insert a ledger row. Born state is `detected` (candidate shadow) by default, or `confirmed`
 * (the primary path — confirmation writes the row). When born `confirmed`, `input.stamp` is
 * REQUIRED and its five D-16 fields are COPIED onto the row (never referenced/joined).
 */
export async function createLedgerRow(
  input: CreateLedgerRowInput,
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow> {
  const v = CreateLedgerRowInputSchema.parse(input)
  const status: LifecycleState = v.initial_status ?? 'detected'

  if (status === 'confirmed' && !v.stamp) {
    throw new Error('createLedgerRow: initial_status "confirmed" requires a copied D-16 stamp')
  }
  const stamp = status === 'confirmed' ? v.stamp! : undefined

  const { rows } = await exec<LedgerRow>(
    `INSERT INTO ${LEDGER_TABLE} (
       chart_id, message_part_id, claim_text, domain, "window", confidence, direction,
       technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status,
       build_id, priors_version, formula_versions, ranking_config, now_context_date,
       stamp_copied_at, confirmed_at
     ) VALUES (
       $1, $2, $3, $4, $5::daterange, $6::numrange, $7,
       $8::text[], $9::text[], $10, $11,
       $12, $13, $14::jsonb, $15::jsonb, $16::date,
       ${stamp ? 'now()' : 'NULL'}, ${status === 'confirmed' ? 'now()' : 'NULL'}
     )
     RETURNING ${RETURNING_COLS}`,
    [
      v.chart_id,
      v.message_part_id ?? null,
      v.claim_text,
      v.domain ?? null,
      toDaterangeLiteral(v.window),
      toNumrangeLiteral(v.confidence),
      v.direction ?? null,
      v.technique_refs ?? [],
      v.grounding_fact_ids ?? [],
      v.created_from_channel ?? 'pariprashna',
      status,
      stamp?.build_id ?? null,
      stamp?.priors_version ?? null,
      stamp ? JSON.stringify(stamp.formula_versions ?? null) : null,
      stamp ? JSON.stringify(stamp.ranking_config ?? null) : null,
      stamp?.now_context_date ?? null,
    ],
  )
  return rows[0]
}

// ── Transition ──────────────────────────────────────────────────────────────

async function currentStatus(
  id: string,
  exec: LedgerExecutor,
): Promise<LifecycleState> {
  const { rows } = await exec<{ lifecycle_status: string }>(
    `SELECT lifecycle_status FROM ${LEDGER_TABLE} WHERE id = $1`,
    [id],
  )
  if (rows.length === 0) throw new Error(`ledger row ${id} not found`)
  return LifecycleStateSchema.parse(rows[0].lifecycle_status)
}

/**
 * Move a row to `to`. Reads the current state, asserts (current → to) is legal (throws
 * IllegalTransitionError otherwise — BEFORE any write), then applies it with an optimistic
 * `WHERE lifecycle_status = current` guard (rejects a concurrent change). `extras` carries the
 * columns a given transition also sets (stamp on detected→confirmed; dismissed_reason;
 * outcome columns) — validated per target by the callers below.
 */
export async function transitionLifecycle(
  id: string,
  to: LifecycleState,
  extras: {
    stamp?: LedgerStamp
    dismissed_reason?: string
    outcome?: Outcome
    outcome_value?: number | null
    outcome_note?: string | null
  } = {},
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow> {
  const from = await currentStatus(id, exec)
  assertLegalTransition(from, to)

  const sets: string[] = ['lifecycle_status = $2']
  const params: unknown[] = [id, to]
  let p = 3

  if (to === 'confirmed') {
    if (!extras.stamp) throw new Error('transition → confirmed requires a copied D-16 stamp')
    sets.push(
      `build_id = $${p++}`,
      `priors_version = $${p++}`,
      `formula_versions = $${p++}::jsonb`,
      `ranking_config = $${p++}::jsonb`,
      `now_context_date = $${p++}::date`,
      `stamp_copied_at = now()`,
      `confirmed_at = now()`,
    )
    params.push(
      extras.stamp.build_id,
      extras.stamp.priors_version,
      JSON.stringify(extras.stamp.formula_versions ?? null),
      JSON.stringify(extras.stamp.ranking_config ?? null),
      extras.stamp.now_context_date,
    )
  }
  if (to === 'dismissed' && extras.dismissed_reason !== undefined) {
    sets.push(`dismissed_reason = $${p++}`)
    params.push(extras.dismissed_reason)
  }
  if (to === 'outcome_recorded' || to === 'unverifiable') {
    const outcome: Outcome = to === 'unverifiable' ? 'unverifiable' : OutcomeSchema.parse(extras.outcome)
    // Brier-exclusion: 'unverifiable' carries no numeric value (also DB-enforced).
    const value = outcome === 'unverifiable' ? null : (extras.outcome_value ?? null)
    sets.push(
      `outcome = $${p++}`,
      `outcome_value = $${p++}`,
      `outcome_note = $${p++}`,
      `outcome_recorded_at = now()`,
    )
    params.push(outcome, value, extras.outcome_note ?? null)
  }

  const { rows, rowCount } = await exec<LedgerRow>(
    `UPDATE ${LEDGER_TABLE} SET ${sets.join(', ')}
      WHERE id = $1 AND lifecycle_status = '${from}'
      RETURNING ${RETURNING_COLS}`,
    params,
  )
  if (!rows.length || rowCount === 0) {
    throw new Error(`ledger row ${id} changed concurrently (expected ${from}); transition aborted`)
  }
  return rows[0]
}

// ── Convenience wrappers ──────────────────────────────────────────────────────

/** Confirm a `detected` shadow row: detected → confirmed, copying the D-16 stamp. */
export async function confirmDetectedRow(
  id: string,
  stamp: LedgerStamp,
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow> {
  return transitionLifecycle(id, 'confirmed', { stamp }, exec)
}

/**
 * Record an outcome (L-5's write; DAL support lives here). Resolves a `window_closed` row to
 * `outcome_recorded` (happened/did_not_happen/partial, with a numeric Brier value) or, for
 * can't-tell, to `unverifiable` (Brier-excluded, value forced null).
 */
export async function recordOutcome(
  id: string,
  args: { outcome: Outcome; outcome_value?: number | null; outcome_note?: string | null },
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow> {
  const to: LifecycleState = args.outcome === 'unverifiable' ? 'unverifiable' : 'outcome_recorded'
  return transitionLifecycle(id, to, { ...args }, exec)
}

// ── Count (the §N.4 count_sql, exposed as a function since this table is not an asset) ──

export async function countLedgerRows(
  chartId: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<number> {
  const { rows } = await exec<{ count: string }>(
    `SELECT count(*) AS count FROM ${LEDGER_TABLE} WHERE chart_id = $1`,
    [chartId],
  )
  return Number(rows[0]?.count ?? 0)
}
