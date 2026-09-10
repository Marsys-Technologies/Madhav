import 'server-only'
/**
 * Paripraśna NO-LEAKAGE arm-1 — the serving-side half of the role/RLS wall.
 * Lane G1-C · NCD-5 (RULED (a), 2026-08-18) · PPR-21 / PPR-22.
 *
 * The DB half is migration 576 (`576_pariprashna_roles_rls_arm3.sql`): five
 * NOLOGIN group roles with grant walls, an `app_chart_context()` accessor, and
 * chart-scoped RLS policies on every C1/C3 table — policies CREATED but RLS not
 * ENABLED, so the database side is inert until an operator runs
 * `platform/scripts/pariprashna/g1c_arm_rls.sql`.
 *
 * This module is the other half: the connection path that CAN serve on
 * `role_web_serve`, and the mechanism that sets the `app.chart_context` session
 * variable those policies read.
 *
 * ── NOTHING HERE IS LIVE UNTIL A FLAG FLIPS ──────────────────────────────────
 * With `PARIPRASHNA_ROLE_SEPARATION` OFF (the default):
 *   · `getServeReadPool()` returns the ONE existing shared pool from
 *     `@/lib/db/client` — the same object, not a copy — so no new connection,
 *     no new credential, no behaviour change;
 *   · `withChartContext()` still opens its transaction (so callers get identical
 *     transactional semantics either way) but sets NO GUC, because setting a GUC
 *     that no enabled policy reads is theatre, and theatre is how a signal ends
 *     up green with nothing behind it (CLAUDE.md §N.8).
 *
 * ── WHY THE FLAG-ON PATH THROWS INSTEAD OF FALLING BACK ──────────────────────
 * If the flag is ON but no `role_web_serve` credential is configured, this module
 * throws `ServeRoleNotConfiguredError`. It does NOT quietly reuse the legacy
 * credential. A flag named "role separation" that reads `true` while every query
 * still runs as `amjis_app` is precisely the defect §N.8 names: a status with no
 * detector behind it. Loud failure at startup of the first serve is the honest
 * behaviour, and the runbook's pre-flight is what stops it happening in prod.
 */

import { Pool } from 'pg'
import type { PoolClient } from 'pg'

import { configService } from '@/lib/config/index'
import { getPool } from '@/lib/db/client'

// ── The five roles, named once ───────────────────────────────────────────────

/**
 * The five NO-LEAKAGE roles (TA §7.4). Named here so application code, tests and
 * the governance census refer to the same strings the migration creates, rather
 * than re-typing them (§N.7 item 3: a constant that shadows a source can drift;
 * a single shared constant cannot drift from itself).
 */
export const PARIPRASHNA_DB_ROLES = {
  /** Web app serving reads + conversation store R/W. No ledger write, no calibration. */
  WEB_SERVE: 'role_web_serve',
  /** Chart-build path: layer-table DML. No conversation store, no ledger. */
  ORCHESTRATOR: 'role_orchestrator',
  /** arm-3 ONLY: the sole holder of ledger/outcome/calibration write. */
  LEDGER_WRITE: 'role_ledger_write',
  /** Scheduled jobs: model health, summaries, digests. */
  JOBS: 'role_jobs',
  /** python-sidecar: minimal compute-support read. */
  SIDECAR: 'role_sidecar',
} as const

export type PariprashnaDbRole =
  (typeof PARIPRASHNA_DB_ROLES)[keyof typeof PARIPRASHNA_DB_ROLES]

/** The GUC every chart-scoped RLS policy in migration 576 compares against. */
export const CHART_CONTEXT_GUC = 'app.chart_context' as const

/**
 * The GUC the PRE-EXISTING baseline policies on `public.charts` compare against
 * (`0001_brahma_baseline.sql`: chart_owner_policy / chart_grant_policy /
 * chart_service_policy). Nothing in the codebase sets it today, which is why
 * `chart_service_policy USING (current_setting('app.principal_id', true) IS NULL
 * OR = '')` is unconditionally true and those policies are a no-op-shaped signal.
 * `withChartContext()` will set it when a caller passes `principalId`, which
 * makes them real — an opt-in, because turning them on for every caller is a live
 * behaviour change that is not this lane's to make.
 */
export const PRINCIPAL_ID_GUC = 'app.principal_id' as const

export const ROLE_SEPARATION_FLAG = 'PARIPRASHNA_ROLE_SEPARATION' as const

/** The single read site for this lane's serving-side flag. */
export function isRoleSeparationEnabled(): boolean {
  return configService.getFlag(ROLE_SEPARATION_FLAG)
}

// ── Chart-context validation ─────────────────────────────────────────────────

const UUID_RE =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/

export class InvalidChartContextError extends Error {
  constructor(readonly received: unknown) {
    super(
      `INVALID_CHART_CONTEXT: app.chart_context must be a uuid, received ` +
        `${JSON.stringify(received)}. Refusing to open a chart-scoped session on a value the ` +
        `RLS policies would silently treat as "no chart" (app_chart_context() returns NULL on a ` +
        `malformed value, and NULL denies every row). Failing here makes the bug visible instead ` +
        `of turning it into an empty result set.`,
    )
    this.name = 'InvalidChartContextError'
  }
}

export class ServeRoleNotConfiguredError extends Error {
  constructor() {
    super(
      `SERVE_ROLE_NOT_CONFIGURED: ${ROLE_SEPARATION_FLAG} is ON but no ${PARIPRASHNA_DB_ROLES.WEB_SERVE} ` +
        `credential is configured. Set SERVE_DATABASE_URL, or DB_SERVE_USER + DB_SERVE_PASSWORD ` +
        `alongside the existing INSTANCE_CONNECTION_NAME/DB_NAME. This does NOT fall back to the ` +
        `legacy application credential on purpose: a flag that reports role separation while every ` +
        `query still runs on the old credential is a green signal with no detector behind it ` +
        `(CLAUDE.md §N.8).`,
    )
    this.name = 'ServeRoleNotConfiguredError'
  }
}

/**
 * Validate a chart id destined for `app.chart_context`. THIS is the loud detector
 * (§N.8); the SQL-side `app_chart_context()` deliberately returns NULL on a
 * malformed value rather than raising, because raising inside a row-security
 * predicate turns one bad value into a per-row exception storm.
 */
export function assertChartContextValue(chartId: unknown): string {
  if (typeof chartId !== 'string' || !UUID_RE.test(chartId)) {
    throw new InvalidChartContextError(chartId)
  }
  return chartId
}

// ── The role_web_serve-capable read pool ─────────────────────────────────────

const g = globalThis as typeof globalThis & { __pgServePool?: Pool }

/**
 * Build the `role_web_serve` pool. Mirrors `client.ts`'s own two-branch shape
 * (explicit DSN vs. Cloud SQL connector) rather than inventing a third
 * connection idiom, so there is one thing to reason about at cutover.
 */
async function initServePool(): Promise<Pool> {
  const keepalive = {
    keepAlive: true,
    keepAliveInitialDelayMillis: 10_000,
    idleTimeoutMillis: 15_000,
    connectionTimeoutMillis: 5_000,
    options: '-c statement_timeout=25000',
  }

  if (process.env.SERVE_DATABASE_URL) {
    return new Pool({
      connectionString: process.env.SERVE_DATABASE_URL,
      max: 10,
      ...keepalive,
    })
  }

  if (process.env.DB_SERVE_USER && process.env.DB_SERVE_PASSWORD) {
    const { Connector } = await import('@google-cloud/cloud-sql-connector')
    const connector = new Connector()
    const clientOpts = await connector.getOptions({
      instanceConnectionName: process.env.INSTANCE_CONNECTION_NAME!,
    })
    return new Pool({
      ...clientOpts,
      user: process.env.DB_SERVE_USER,
      password: process.env.DB_SERVE_PASSWORD,
      database: process.env.DB_NAME!,
      max: 10,
      ...keepalive,
    })
  }

  throw new ServeRoleNotConfiguredError()
}

/**
 * The pool serving reads should use.
 *
 * Flag OFF → the existing shared pool, returned by identity. Flag ON → a separate
 * `role_web_serve`-backed pool, cached on `globalThis` exactly as `client.ts`
 * caches its own (same HMR reasoning).
 *
 * A future deliberate cutover is therefore a config flip plus provisioning a
 * credential — not a code change.
 */
export async function getServeReadPool(): Promise<Pool> {
  if (!isRoleSeparationEnabled()) return getPool()
  if (!g.__pgServePool) {
    const pool = await initServePool()
    pool.on('error', (err) => {
      console.error('[pg serve pool] idle client error (evicted)', err)
    })
    g.__pgServePool = pool
  }
  return g.__pgServePool
}

// ── The chart-context session mechanism (PPR-22) ─────────────────────────────

export interface ChartContextOptions {
  /**
   * Optionally also pin `app.principal_id`, which activates the PRE-EXISTING
   * baseline policies on `public.charts`. Opt-in: see PRINCIPAL_ID_GUC's note.
   */
  principalId?: string | null
  /** Override the pool (tests, and the arm-3 worker, which runs on its own role). */
  pool?: Pool
}

/**
 * Run `fn` inside a transaction whose `app.chart_context` is pinned to `chartId`.
 *
 * `set_config(..., is_local => true)` scopes the setting to THIS transaction, so
 * the pin cannot leak onto the next request that borrows the same pooled
 * connection. That is the whole reason this is a transaction and not a bare
 * `SET` — a session-scoped pin on a pooled connection is a cross-tenant bug
 * waiting to happen, and it is the exact failure this wall exists to prevent.
 *
 * The chart id goes in as a BIND PARAMETER via `set_config`, never string-
 * interpolated into a `SET` statement (which cannot be parameterised at all).
 */
export async function withChartContext<T>(
  chartId: string,
  fn: (client: PoolClient) => Promise<T>,
  opts: ChartContextOptions = {},
): Promise<T> {
  const pinned = assertChartContextValue(chartId)
  const pool = opts.pool ?? (await getServeReadPool())
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    // Only actually pin when the wall is armed. See the module header.
    if (isRoleSeparationEnabled()) {
      await client.query('SELECT set_config($1, $2, true)', [CHART_CONTEXT_GUC, pinned])
      if (opts.principalId) {
        await client.query('SELECT set_config($1, $2, true)', [
          PRINCIPAL_ID_GUC,
          opts.principalId,
        ])
      }
    }
    const out = await fn(client)
    await client.query('COMMIT')
    return out
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {})
    throw err
  } finally {
    client.release()
  }
}

/**
 * Set `app.chart_context` on a client the caller already owns and has already put
 * in a transaction. For call sites that manage their own BEGIN/COMMIT (the arm-3
 * worker does) and cannot hand control to `withChartContext`.
 *
 * `is_local => true` again: this is only correct inside a transaction. Calling it
 * outside one silently does nothing in Postgres, so the doc comment is the only
 * guard there is — which is why this is the narrow, explicitly-named escape hatch
 * and `withChartContext` is the one everything else should use.
 */
export async function setChartContext(
  client: PoolClient,
  chartId: string,
): Promise<void> {
  const pinned = assertChartContextValue(chartId)
  await client.query('SELECT set_config($1, $2, true)', [CHART_CONTEXT_GUC, pinned])
}
