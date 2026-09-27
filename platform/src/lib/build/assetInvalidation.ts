import 'server-only'
import { deriveDeleteSqlFromCountSql, EXPLICIT_CLEAR_OPS } from '@/lib/cockpit/assetClearSpec'
import type { ClearPolicy, Queryable, RegistryEntryWithScope } from '@/lib/build/runPreparation'

/**
 * Chart-scoped asset invalidation (Jātaka chart workspace, Task 5).
 *
 * Two policies over the same governed clear specifications
 * (`EXPLICIT_CLEAR_OPS`, `deriveDeleteSqlFromCountSql`, registry `target_table`):
 *
 *   operator-best-effort    — the cockpit's existing behaviour, unchanged: each
 *                             asset in its own savepoint; a failing DELETE is
 *                             rolled back to its savepoint and the clear goes on.
 *   chart-correction-strict — a birth-detail correction. Every applicable clear
 *                             must succeed on the caller's transaction; no
 *                             savepoints; any failure throws so the whole
 *                             correction (conversation archive, chart update,
 *                             invalidation, run) rolls back. Only chart-scoped
 *                             statements ever run.
 *
 * Preservation boundary for a correction: data that no build regenerates is
 * never erased — the governed skip-clean assets listed below, and any per-chart
 * asset with no writer. Answered journal rows and confirmed/denied outcomes
 * survive through the governed scoped operations for mi_abhilekha/mi_bhavisya.
 * Ownership, grants and consent live outside the asset registry and are never
 * touched here.
 */

export const CORRECTION_PRESERVATION = {
  lel_events: 'user-authored life events and chart-state index',
  mi_seva: 'user preferences are not chart-derived output',
  mi_vistara: 'global append-only export log',
} as const

export const CORRECTION_NOTHING_TO_CLEAR = {
  bo_samvada: 'derived view over other bodha tables; owns no rows',
} as const

export type InvalidationErrorCode = 'CLEAR_SPEC_MISSING' | 'INVALID_TABLE'

export class InvalidationError extends Error {
  constructor(
    readonly code: InvalidationErrorCode,
    message: string,
    readonly assetId: string,
  ) {
    super(message)
    this.name = 'InvalidationError'
  }
}

export interface InvalidationResult {
  clearedAssetIds: string[]
  preservedAssetIds: string[]
  /** Operator policy only: assets whose DELETE failed and was rolled back to its savepoint. */
  failedAssetIds: string[]
}

const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/

type ClearStatement = { sql: string; params: unknown[] }

function withParams(sql: string, chartId: string): ClearStatement {
  return { sql, params: sql.includes('$1') ? [chartId] : [] }
}

/** Mirrors the cockpit's historical resolution, including global clears for force_l0. */
function operatorStatements(asset: RegistryEntryWithScope, chartId: string): ClearStatement[] | null {
  if (asset.asset_id in EXPLICIT_CLEAR_OPS) {
    const explicit = EXPLICIT_CLEAR_OPS[asset.asset_id]
    return explicit === null ? null : explicit.map((op) => withParams(op.sql, chartId))
  }
  if (asset.count_sql) {
    const deleteSql = deriveDeleteSqlFromCountSql(asset.count_sql)
    if (deleteSql) return [withParams(deleteSql, chartId)]
  }
  if (asset.target_table) {
    if (!TABLE_NAME_RE.test(asset.target_table)) {
      throw new InvalidationError('INVALID_TABLE', `Invalid target_table: ${asset.target_table}`, asset.asset_id)
    }
    return asset.scope === 'global'
      ? [{ sql: `DELETE FROM ${asset.target_table}`, params: [] }]
      : [{ sql: `DELETE FROM ${asset.target_table} WHERE chart_id = $1`, params: [chartId] }]
  }
  return null
}

type StrictDecision = { kind: 'clear'; statements: ClearStatement[] } | { kind: 'preserve' } | { kind: 'skip' }

function strictDecision(asset: RegistryEntryWithScope, chartId: string): StrictDecision {
  const missing = (why: string) =>
    new InvalidationError('CLEAR_SPEC_MISSING', `${asset.asset_id}: ${why}`, asset.asset_id)

  if (asset.asset_id in CORRECTION_PRESERVATION) return { kind: 'preserve' }
  if (asset.asset_id in CORRECTION_NOTHING_TO_CLEAR) return { kind: 'skip' }
  // No writer ⇒ no build regenerates it ⇒ a correction must not erase it.
  if (asset.has_writer === false) return { kind: 'preserve' }
  if (asset.scope !== 'per_chart') throw missing('a chart correction never clears a global asset')

  let statements: ClearStatement[] | null = null
  if (asset.asset_id in EXPLICIT_CLEAR_OPS) {
    const explicit = EXPLICIT_CLEAR_OPS[asset.asset_id]
    if (explicit === null) throw missing('skip-clean asset has no correction preservation classification')
    statements = explicit.map((op) => withParams(op.sql, chartId))
  } else if (asset.count_sql && deriveDeleteSqlFromCountSql(asset.count_sql)) {
    statements = [withParams(deriveDeleteSqlFromCountSql(asset.count_sql)!, chartId)]
  } else if (asset.target_table) {
    if (!TABLE_NAME_RE.test(asset.target_table)) throw missing(`invalid target_table ${asset.target_table}`)
    statements = [{ sql: `DELETE FROM ${asset.target_table} WHERE chart_id = $1`, params: [chartId] }]
  }

  if (!statements || statements.length === 0) throw missing('writer asset has no safe clear specification')
  if (statements.some((statement) => !/\bchart_id\s*=\s*\$1\b/i.test(statement.sql))) {
    throw missing('clear specification is not scoped to this chart')
  }
  return { kind: 'clear', statements }
}

export async function invalidateAssets(args: {
  db: Queryable
  chartId: string
  /** In dependency order (upstream first); cleared in reverse so dependants go first. */
  assets: RegistryEntryWithScope[]
  policy: Exclude<ClearPolicy, 'none'>
}): Promise<InvalidationResult> {
  const { db, chartId, policy } = args
  const ordered = [...args.assets].reverse()
  const result: InvalidationResult = { clearedAssetIds: [], preservedAssetIds: [], failedAssetIds: [] }

  if (policy === 'chart-correction-strict') {
    // Resolve every decision before the first DELETE so an unsafe or missing
    // specification fails without issuing any statement.
    const decisions = ordered.map((asset) => ({ asset, decision: strictDecision(asset, chartId) }))
    for (const { asset, decision } of decisions) {
      if (decision.kind === 'preserve') {
        result.preservedAssetIds.push(asset.asset_id)
        continue
      }
      if (decision.kind === 'skip') continue
      for (const statement of decision.statements) {
        await db.query(statement.sql, statement.params)
      }
      result.clearedAssetIds.push(asset.asset_id)
    }
    return result
  }

  let savepointIndex = 0
  for (const asset of ordered) {
    const statements = operatorStatements(asset, chartId)
    if (!statements) continue // no clear spec or skip-clean — non-destructive
    const savepoint = `cb_${savepointIndex++}`
    await db.query(`SAVEPOINT ${savepoint}`)
    let failed = false
    for (const statement of statements) {
      try {
        await db.query(statement.sql, statement.params)
      } catch (error) {
        console.warn(`[runs/clear-before] DELETE failed for ${asset.asset_id}:`, (error as Error).message)
        await db.query(`ROLLBACK TO SAVEPOINT ${savepoint}`)
        await db.query(`RELEASE SAVEPOINT ${savepoint}`)
        failed = true
        break
      }
    }
    if (failed) {
      result.failedAssetIds.push(asset.asset_id)
    } else {
      await db.query(`RELEASE SAVEPOINT ${savepoint}`)
      result.clearedAssetIds.push(asset.asset_id)
    }
  }
  return result
}
