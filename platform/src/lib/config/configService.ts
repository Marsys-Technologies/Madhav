/**
 * Stream C / Unit 2d — configService gate extension.
 *
 * Layered on top of the existing `configService` singleton in `./index.ts`.
 * Adds the DB-backed gate plane:
 *
 *   getGate(key, opts?) →
 *     1. cache hit?           → return cached
 *     2. runtime_config row?  → cache + return parsed value
 *     3. env-var override?    → cache + return coerced env
 *     4. gate_registry default
 *
 *   setGate(key, value, principalUid, opts?) →
 *     - validates key against gate_registry
 *     - enforces AYANAMSHA_CANONICAL_ENABLED=false guard
 *     - upserts runtime_config
 *     - appends gate_change_log
 *     - invalidates cache for key
 *
 * The reader is cached in-process; writers invalidate. There is no
 * cross-instance pub/sub here — that lands when 2d hooks into the existing
 * configService.subscribe pipe in a follow-up.
 */

import 'server-only'
import { query } from '@/lib/db/client'
import { GATE_REGISTRY, getGateSpec, type GateSpec, type GateValueType } from '@/lib/gates/gate_registry'

// ────────────────────────────────────────────────────────────────────────────
// Cache
// ────────────────────────────────────────────────────────────────────────────

type CacheKey = string // `${key}::${chartId ?? '__global__'}`
const _cache = new Map<CacheKey, unknown>()

function cacheKey(key: string, chartId?: string): CacheKey {
  return `${key}::${chartId ?? '__global__'}`
}

/** Test-only / reset hook. */
export function _clearGateCache(): void {
  _cache.clear()
}

// ────────────────────────────────────────────────────────────────────────────
// Coercion
// ────────────────────────────────────────────────────────────────────────────

function coerceFromJsonb(value: unknown, valueType: GateValueType): unknown {
  // pg returns JSONB as native JS already, so this is mostly an assertion shim.
  switch (valueType) {
    case 'boolean':
      return typeof value === 'boolean' ? value : Boolean(value)
    case 'number':
      return typeof value === 'number' ? value : Number(value)
    case 'string':
      return typeof value === 'string' ? value : String(value)
    case 'json':
      return value
  }
}

function coerceFromEnv(raw: string, valueType: GateValueType): unknown {
  switch (valueType) {
    case 'boolean':
      return raw.toLowerCase() === 'true'
    case 'number':
      return Number(raw)
    case 'string':
      return raw
    case 'json':
      try {
        return JSON.parse(raw)
      } catch {
        return raw
      }
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Reader
// ────────────────────────────────────────────────────────────────────────────

export interface GetGateOptions {
  chartId?: string
  /** Skip the in-process cache; force a DB read. */
  bypassCache?: boolean
}

/**
 * Returns the effective value of a gate. Three layers:
 *   runtime_config row → env override → gate_registry.default
 *
 * For `per_chart` gates, pass `opts.chartId`. The composite lookup falls back
 * to the global row when no per-chart row exists.
 */
export async function getGate<T = unknown>(
  key: string,
  opts: GetGateOptions = {},
): Promise<T> {
  const spec = getGateSpec(key)
  const ck = cacheKey(key, opts.chartId)
  if (!opts.bypassCache && _cache.has(ck)) {
    return _cache.get(ck) as T
  }

  // Lookup precedence: per_chart row → global row → env → default.
  let value: unknown | undefined

  if (spec.scope === 'per_chart' && opts.chartId) {
    const { rows } = await query<{ value: unknown; value_type: GateValueType }>(
      `SELECT value, value_type FROM runtime_config
       WHERE key = $1 AND chart_id = $2
       LIMIT 1`,
      [key, opts.chartId],
    )
    if (rows[0]) value = coerceFromJsonb(rows[0].value, rows[0].value_type)
  }

  if (value === undefined) {
    const { rows } = await query<{ value: unknown; value_type: GateValueType }>(
      `SELECT value, value_type FROM runtime_config
       WHERE key = $1 AND chart_id IS NULL
       LIMIT 1`,
      [key],
    )
    if (rows[0]) value = coerceFromJsonb(rows[0].value, rows[0].value_type)
  }

  if (value === undefined) {
    const envRaw = process.env[key]
    if (envRaw !== undefined) value = coerceFromEnv(envRaw, spec.value_type)
  }

  if (value === undefined) {
    value = spec.default
  }

  _cache.set(ck, value)
  return value as T
}

// ────────────────────────────────────────────────────────────────────────────
// Writer
// ────────────────────────────────────────────────────────────────────────────

export interface SetGateOptions {
  chartId?: string
  reason?: string
}

export class GateWriteError extends Error {
  constructor(public code: string, message: string) {
    super(message)
    this.name = 'GateWriteError'
  }
}

/**
 * Persists a new value for a gate and appends a row to gate_change_log.
 *
 * Throws GateWriteError for:
 *   - unknown gate key
 *   - AYANAMSHA_CANONICAL_ENABLED set to false (hard guard; canonical role
 *     cannot be disabled — see brief AC.5)
 *   - per_chart write without chartId
 */
export async function setGate(
  key: string,
  value: unknown,
  principalUid: string,
  opts: SetGateOptions = {},
): Promise<void> {
  const spec = getGateSpec(key)

  // Hard guard: canonical ayanamsha cannot be turned off.
  if (key === 'AYANAMSHA_CANONICAL_ENABLED' && value === false) {
    throw new GateWriteError(
      'CANONICAL_AYANAMSHA_LOCKED',
      'AYANAMSHA_CANONICAL_ENABLED cannot be disabled — canonical role is required.',
    )
  }

  if (spec.scope === 'per_chart' && !opts.chartId) {
    throw new GateWriteError(
      'CHART_ID_REQUIRED',
      `Gate "${key}" is per_chart and requires opts.chartId.`,
    )
  }

  // Read old value for the change log (cache-bypass to capture exact prior state).
  const oldValue = await getGate(key, { chartId: opts.chartId, bypassCache: true })

  // Upsert into runtime_config.
  await query(
    `INSERT INTO runtime_config (key, value, value_type, scope, chart_id, updated_by, updated_at)
     VALUES ($1, $2::jsonb, $3, $4, $5, $6, now())
     ON CONFLICT (key, COALESCE(chart_id, '__global__'))
     DO UPDATE SET value = EXCLUDED.value,
                   value_type = EXCLUDED.value_type,
                   scope = EXCLUDED.scope,
                   updated_by = EXCLUDED.updated_by,
                   updated_at = now()`,
    [
      key,
      JSON.stringify(value),
      spec.value_type,
      spec.scope,
      opts.chartId ?? null,
      principalUid,
    ],
  )

  // Append to gate_change_log.
  await query(
    `INSERT INTO gate_change_log (gate_key, chart_id, old_value, new_value, changed_by, reason)
     VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6)`,
    [
      key,
      opts.chartId ?? null,
      JSON.stringify(oldValue ?? null),
      JSON.stringify(value),
      principalUid,
      opts.reason ?? null,
    ],
  )

  // Invalidate cache for this composite key.
  _cache.delete(cacheKey(key, opts.chartId))
}

/**
 * Reset a gate to its registry default (removes any runtime_config override).
 */
export async function resetGate(
  key: string,
  principalUid: string,
  opts: SetGateOptions = {},
): Promise<void> {
  const spec = getGateSpec(key)

  // Hard guard mirrors setGate.
  if (key === 'AYANAMSHA_CANONICAL_ENABLED' && spec.default === false) {
    throw new GateWriteError(
      'CANONICAL_AYANAMSHA_LOCKED',
      'AYANAMSHA_CANONICAL_ENABLED canonical default must be true.',
    )
  }

  const oldValue = await getGate(key, { chartId: opts.chartId, bypassCache: true })

  await query(
    `DELETE FROM runtime_config
     WHERE key = $1 AND COALESCE(chart_id, '__global__') = COALESCE($2, '__global__')`,
    [key, opts.chartId ?? null],
  )

  await query(
    `INSERT INTO gate_change_log (gate_key, chart_id, old_value, new_value, changed_by, reason)
     VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6)`,
    [
      key,
      opts.chartId ?? null,
      JSON.stringify(oldValue ?? null),
      JSON.stringify(spec.default),
      principalUid,
      opts.reason ?? 'reset_to_default',
    ],
  )

  _cache.delete(cacheKey(key, opts.chartId))
}

/**
 * Read the current value of every gate (global scope) in one round-trip-ish call.
 * Used by the Command Center landing page.
 */
export async function readAllGatesGlobal(): Promise<
  Array<{ spec: GateSpec; value: unknown; overridden: boolean }>
> {
  const { rows } = await query<{ key: string; value: unknown; value_type: GateValueType }>(
    `SELECT key, value, value_type FROM runtime_config WHERE chart_id IS NULL`,
  )
  const overrides = new Map<string, unknown>()
  for (const r of rows) overrides.set(r.key, coerceFromJsonb(r.value, r.value_type))

  return GATE_REGISTRY.map((spec) => {
    const override = overrides.get(spec.key)
    if (override !== undefined) {
      return { spec, value: override, overridden: true }
    }
    const envRaw = process.env[spec.key]
    if (envRaw !== undefined) {
      return { spec, value: coerceFromEnv(envRaw, spec.value_type), overridden: false }
    }
    return { spec, value: spec.default, overridden: false }
  })
}
