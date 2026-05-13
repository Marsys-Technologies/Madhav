import 'server-only'
import { runProbe } from '@/lib/aiops/probe/runner'
import { query } from '@/lib/db/client'
import type { AiopsModelHealthStatus } from '@/lib/db/schema/aiops'

export interface HealthResult {
  model_id:   string
  status:     AiopsModelHealthStatus
  latency_ms: number | null
  error?:     string
}

export async function probeModel(modelId: string): Promise<HealthResult> {
  try {
    const result = await runProbe({
      stack:         'gemini',
      callType:      'worker',
      role:          'primary',
      modelOverride: modelId,
    })

    const status: AiopsModelHealthStatus = result.status === 'pass'
      ? 'pass'
      : result.status === 'timeout' ? 'timeout' : 'fail'

    const row: HealthResult = {
      model_id:   modelId,
      status,
      latency_ms: result.latency_ms,
      error:      result.error,
    }

    await upsertHealth(row)
    return row
  } catch (err) {
    const row: HealthResult = {
      model_id:   modelId,
      status:     'fail',
      latency_ms: null,
      error:      err instanceof Error ? err.message : String(err),
    }
    await upsertHealth(row)
    return row
  }
}

async function upsertHealth(row: HealthResult): Promise<void> {
  await query(
    `INSERT INTO llm_model_health (model_id, status, latency_ms, last_probe_at, last_error)
     VALUES ($1, $2, $3, now(), $4)
     ON CONFLICT (model_id) DO UPDATE SET
       status        = EXCLUDED.status,
       latency_ms    = EXCLUDED.latency_ms,
       last_probe_at = EXCLUDED.last_probe_at,
       last_error    = EXCLUDED.last_error`,
    [row.model_id, row.status, row.latency_ms ?? null, row.error ?? null],
  )
}
