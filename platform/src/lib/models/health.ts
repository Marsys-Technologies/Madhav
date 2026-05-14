/**
 * BHISMA-B1 §3.5 — Model health check system
 *
 * On-demand ping of each FAMILY_WORKER model with a minimal prompt. Results are
 * stored in an in-memory MODEL_HEALTH map so the router can fast-fail before
 * attempting a call against a known-degraded provider.
 *
 * Usage at request time:
 *   assertWorkerHealthy(workerModelId)   // throws PipelineError if degraded
 *
 * Admin endpoint trigger:
 *   GET /api/admin/model-health           // returns current statuses (cached)
 *   GET /api/admin/model-health?refresh=true  // re-pings all FAMILY_WORKERs
 */
import 'server-only'
import { runAdapter } from '@/lib/adapters'
import { FAMILY_WORKER } from './registry'
import { PipelineError } from '@/lib/router/errors'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type HealthStatus = 'healthy' | 'degraded' | 'unknown'

export interface ModelHealthEntry {
  model_id: string
  status: HealthStatus
  last_checked_at: string | null
  /** Present only when status === 'degraded'. Human-readable failure reason. */
  error?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// In-memory store (survives within a single server process; cleared on restart)
// ─────────────────────────────────────────────────────────────────────────────

const MODEL_HEALTH = new Map<string, ModelHealthEntry>()

// ─────────────────────────────────────────────────────────────────────────────
// Read accessors
// ─────────────────────────────────────────────────────────────────────────────

/** Returns the current in-memory health status for a model (never throws). */
export function getHealthStatus(modelId: string): HealthStatus {
  return MODEL_HEALTH.get(modelId)?.status ?? 'unknown'
}

/** Returns all recorded health entries. */
export function getAllHealthStatuses(): ModelHealthEntry[] {
  return Array.from(MODEL_HEALTH.values())
}

// ─────────────────────────────────────────────────────────────────────────────
// Health check execution
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Ping a single model with a minimal 1-token prompt. Records the result in
 * MODEL_HEALTH and returns the entry.
 */
export async function checkWorkerHealth(modelId: string): Promise<ModelHealthEntry> {
  try {
    await runAdapter({
      callType: 'worker',
      modelOverride: { modelId },
      systemPrompt: '',
      messages: [{ role: 'user', content: 'Reply with the single word: ok' }],
      maxOutputTokens: 5,
    })
    const entry: ModelHealthEntry = {
      model_id: modelId,
      status: 'healthy',
      last_checked_at: new Date().toISOString(),
    }
    MODEL_HEALTH.set(modelId, entry)
    return entry
  } catch (err) {
    const entry: ModelHealthEntry = {
      model_id: modelId,
      status: 'degraded',
      last_checked_at: new Date().toISOString(),
      error: err instanceof Error ? err.message : String(err),
    }
    MODEL_HEALTH.set(modelId, entry)
    return entry
  }
}

/**
 * Ping all FAMILY_WORKER models in parallel. Returns an array of health entries.
 * Safe to call at startup or from the admin endpoint — never throws.
 */
export async function runHealthChecks(): Promise<ModelHealthEntry[]> {
  const workerIds = Object.values(FAMILY_WORKER) as string[]
  // Deduplicate in case any two providers share a worker ID (edge case)
  const unique = [...new Set(workerIds)]
  const settled = await Promise.allSettled(unique.map(id => checkWorkerHealth(id)))
  return settled.map((r, i) => {
    if (r.status === 'fulfilled') return r.value
    const entry: ModelHealthEntry = {
      model_id: unique[i],
      status: 'degraded',
      last_checked_at: new Date().toISOString(),
      error: r.reason instanceof Error ? r.reason.message : String(r.reason),
    }
    MODEL_HEALTH.set(unique[i], entry)
    return entry
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Runtime assertion (used by the pipeline before each LLM call)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Throws a `PipelineError` (ADR-3 hard-fail) if the given worker model has a
 * confirmed-degraded status in MODEL_HEALTH. Status 'unknown' is allowed
 * through (avoids failing cold-start requests before any health check has run).
 */
export function assertWorkerHealthy(workerModelId: string): void {
  const entry = MODEL_HEALTH.get(workerModelId)
  if (entry?.status === 'degraded') {
    throw new PipelineError({
      stage: 'classify',
      reason: `Worker model ${workerModelId} is known-unhealthy (last checked: ${entry.last_checked_at ?? 'never'}). ${entry.error ?? ''}`.trim(),
      model_id: workerModelId,
    })
  }
}
