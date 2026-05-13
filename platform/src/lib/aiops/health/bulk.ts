import 'server-only'
import { MODELS } from '@/lib/models/registry'
import { probeModel, type HealthResult } from './prober'

export interface HealthReport {
  total:   number
  pass:    number
  fail:    number
  timeout: number
  results: HealthResult[]
}

export async function probeAllModels(): Promise<HealthReport> {
  const modelIds = [...new Set(MODELS.map(m => m.id))]

  const results: HealthResult[] = await Promise.all(
    modelIds.map(id => probeModel(id)),
  )

  const report: HealthReport = {
    total:   results.length,
    pass:    results.filter(r => r.status === 'pass').length,
    fail:    results.filter(r => r.status === 'fail').length,
    timeout: results.filter(r => r.status === 'timeout').length,
    results,
  }

  return report
}
