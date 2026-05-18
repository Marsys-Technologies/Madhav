import 'server-only'
import { STACK_ROUTING, DEFAULT_STACK_ID, type CallType, type ModelStack } from './registry'
import { getFlag } from '@/lib/config'
import { query } from '@/lib/db/client'
import type {
  LlmStackConfigRow,
  LlmStackRoutingOverrideRow,
  LlmParamOverrideRow,
} from '@/lib/db/schema/aiops'

// ─────────────────────────────────────────────────────────────────────────────
// In-memory cache (60s TTL)
// ─────────────────────────────────────────────────────────────────────────────

type ParamName = 'max_output_tokens' | 'temperature' | 'thinkingBudget' | 'timeout_ms'

interface RuntimeCache {
  stack:          ModelStack
  routing:        Record<string, Record<string, { primary: string; fallback: string }>>
  params:         Record<string, Record<string, Record<string, unknown>>>
  fetched_at:     number
}

let _cache: RuntimeCache | null = null
const CACHE_TTL_MS = 60_000

function isCacheValid(): boolean {
  return _cache !== null && Date.now() - _cache.fetched_at < CACHE_TTL_MS
}

/** Call after every write in the Control Panel to bust the 60s cache immediately. */
export function invalidateRuntimeConfigCache(): void {
  _cache = null
}

// ─────────────────────────────────────────────────────────────────────────────
// DB fetchers
// ─────────────────────────────────────────────────────────────────────────────

async function fetchFromDb(): Promise<RuntimeCache> {
  const [stackRows, routingRows, paramRows] = await Promise.all([
    query<LlmStackConfigRow>(`SELECT * FROM llm_stack_config WHERE scope = 'global' LIMIT 1`),
    query<LlmStackRoutingOverrideRow>(`SELECT * FROM llm_stack_routing_override WHERE scope = 'global' AND (expires_at IS NULL OR expires_at > NOW())`),
    query<LlmParamOverrideRow>(`SELECT * FROM llm_param_override WHERE scope = 'global'`),
  ])

  const stack = (stackRows.rows[0]?.active_stack ?? DEFAULT_STACK_ID) as ModelStack

  const routing: RuntimeCache['routing'] = {}
  for (const row of routingRows.rows) {
    if (!routing[row.stack]) routing[row.stack] = {}
    routing[row.stack][row.call_type] = {
      primary:  row.primary_model,
      fallback: row.fallback_model,
    }
  }

  const params: RuntimeCache['params'] = {}
  for (const row of paramRows.rows) {
    if (!params[row.stack]) params[row.stack] = {}
    if (!params[row.stack][row.call_type]) params[row.stack][row.call_type] = {}
    params[row.stack][row.call_type][row.param_name] = row.param_value
  }

  return { stack, routing, params, fetched_at: Date.now() }
}

async function getCache(): Promise<RuntimeCache> {
  if (isCacheValid()) return _cache!
  _cache = await fetchFromDb()
  return _cache
}

// ─────────────────────────────────────────────────────────────────────────────
// Per-request header override parsing
// ─────────────────────────────────────────────────────────────────────────────

function getHeaderStack(req?: Request): ModelStack | null {
  const val = req?.headers.get('x-aiops-stack')
  if (!val) return null
  // Validate it's a known stack value — don't trust arbitrary header input.
  const knownStacks: ModelStack[] = ['nim', 'anthropic', 'gemini', 'gpt', 'deepseek', 'marsys']
  return knownStacks.includes(val as ModelStack) ? (val as ModelStack) : null
}

function getHeaderModel(req: Request | undefined, callType: CallType, role: 'primary' | 'fallback'): string | null {
  const key = `x-aiops-model-${callType}-${role}`
  return req?.headers.get(key) ?? null
}

function getHeaderParam(req: Request | undefined, callType: CallType, paramName: string): unknown | null {
  const key = `x-aiops-param-${callType}-${paramName}`
  const val = req?.headers.get(key)
  if (val === null || val === undefined) return null
  try { return JSON.parse(val) } catch { return val }
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Resolution priority (top wins):
 * 1. Per-request header (x-aiops-stack)
 * 2. DB override (llm_stack_config)
 * 3. Static DEFAULT_STACK_ID from registry
 *
 */
export async function getEffectiveStack(req?: Request): Promise<ModelStack> {
  // 1. Per-request header
  const headerStack = getHeaderStack(req)
  if (headerStack) return headerStack

  // 2. DB
  const cache = await getCache()
  return cache.stack
}

/**
 * Resolution priority:
 * 1. Per-request header (x-aiops-model-<callType>-<role>)
 * 2. DB override (llm_stack_routing_override)
 * 3. Static STACK_ROUTING registry entry
 *
 */
export async function getEffectiveModel(
  stack: ModelStack,
  callType: CallType,
  role: 'primary' | 'fallback',
  req?: Request,
): Promise<string> {
  const registryDefault = STACK_ROUTING[stack]?.[callType]?.[role]
    ?? STACK_ROUTING[DEFAULT_STACK_ID][callType][role]

  // 1. Per-request header
  const headerModel = getHeaderModel(req, callType, role)
  if (headerModel) return headerModel

  // 2. DB
  const cache = await getCache()
  return cache.routing[stack]?.[callType]?.[role] ?? registryDefault
}

/**
 * Resolution priority:
 * 1. Per-request header (x-aiops-param-<callType>-<paramName>)
 * 2. DB override (llm_param_override)
 * 3. Caller-supplied fallback value
 *
 */
export async function getEffectiveParam<T = unknown>(
  stack: ModelStack,
  callType: CallType,
  paramName: ParamName,
  fallback: T,
  req?: Request,
): Promise<T> {
  // 1. Per-request header
  const headerVal = getHeaderParam(req, callType, paramName)
  if (headerVal !== null) return headerVal as T

  // 2. DB
  const cache = await getCache()
  const dbVal = cache.params[stack]?.[callType]?.[paramName]
  if (dbVal !== undefined) return dbVal as T

  return fallback
}
