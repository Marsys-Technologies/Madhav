import 'server-only'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { query } from '@/lib/db/client'
import type { LlmModelHealthRow } from '@/lib/db/schema/aiops'
import { guardAiopsRoute } from '@/app/api/admin/aiops/_guard'

export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const url = new URL(req.url)
  const modelId = url.searchParams.get('model_id')

  const sql = modelId
    ? `SELECT * FROM llm_model_health WHERE model_id = $1 ORDER BY last_probe_at DESC`
    : `SELECT * FROM llm_model_health ORDER BY last_probe_at DESC LIMIT 200`
  const params = modelId ? [modelId] : []

  try {
    const result = await query<LlmModelHealthRow>(sql, params)
    return Response.json({ rows: result.rows })
  } catch {
    return res.dbError()
  }
}

export async function POST(req: Request) {
  const guard = await guardAiopsRoute()
  if (guard instanceof NextResponse) return guard

  const url = new URL(req.url)
  const modelId = url.searchParams.get('model_id')
  if (!modelId) return res.badRequest('model_id is required')

  const { probeModel } = await import('@/lib/aiops/health/prober')
  const result = await probeModel(modelId)
  return Response.json(result)
}
