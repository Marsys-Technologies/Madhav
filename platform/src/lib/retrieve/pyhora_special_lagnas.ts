/**
 * pyhora_special_lagnas.ts — RetrievalTool: query_special_lagnas
 *
 * Calls /api/pyhora/compute and returns special lagnas (bhava_lagna, ascendant,
 * and upagrahas/sensitive points: gulika, maandi, kaala, mrityu, etc.)
 *
 * Capability: query_special_lagnas
 * Engine: PyJHora 4.8.6
 * Layer: L1 Gaṇita — bhava_lagna + sensitive_points
 *
 * Stream G deliverable (BRAHMA-G-1).
 */

import { createHash } from 'crypto'
import type { RetrievalTool, ToolBundle, ToolBundleResult, QueryPlan } from './types'

function sha256(data: string): string {
  return 'sha256:' + createHash('sha256').update(data).digest('hex')
}

function sidecarUrl(): string {
  const base = process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000'
  return base.replace(/\/$/, '')
}

async function callPyHoraCompute(input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const url = `${sidecarUrl()}/api/pyhora/compute`
  const apiKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'x-api-key': apiKey } : {}),
    },
    body: JSON.stringify(input),
    signal: AbortSignal.timeout(30_000),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`pyhora/compute HTTP ${response.status}: ${body.slice(0, 200)}`)
  }

  return response.json() as Promise<Record<string, unknown>>
}

export const tool: RetrievalTool = {
  name: 'query_special_lagnas',
  version: '1.0',
  description:
    'Retrieve special lagnas (ascendant/bhava_lagna + upagrahas: Gulika, Maandi, Kaala, ' +
    'Mrityu, Artha Prabhakara, Yama) for a chart via PyJHora. ' +
    'Returns sign, sign_id, longitude_deg for each special point. ' +
    'Engine: PyJHora 4.8.6. Layer: L1 Gaṇita / ganita.bhava_lagna.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {}
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const input = {
      datetime_iso: String(params.datetime_iso ?? ''),
      latitude_deg: Number(params.latitude_deg ?? 0),
      longitude_deg: Number(params.longitude_deg ?? 0),
      tz_offset_hours: Number(params.tz_offset_hours ?? 5.5),
      place_name: typeof params.place_name === 'string' ? params.place_name : '',
      ayanamsha_id: typeof params.ayanamsha_id === 'string' ? params.ayanamsha_id : 'lahiri',
    }

    const data = await callPyHoraCompute(input)

    const results: ToolBundleResult[] = []

    // Lagna / Ascendant (bhava_lagna)
    const bhava_lagna = (data.bhava_lagna ?? {}) as Record<string, unknown>
    if (bhava_lagna && Object.keys(bhava_lagna).length > 0) {
      results.push({
        content: JSON.stringify({
          point: 'Lagna',
          sign: bhava_lagna.sign,
          sign_id: bhava_lagna.sign_id,
          longitude_deg: bhava_lagna.longitude_deg,
          nakshatra: bhava_lagna.nakshatra,
          pada: bhava_lagna.pada,
          ayanamsha_id: input.ayanamsha_id,
        }),
        confidence: 0.98,
      })
    }

    // Special points / upagrahas
    const specialPoints = (data.special_lagnas ?? {}) as Record<string, unknown>
    for (const [name, point] of Object.entries(specialPoints)) {
      if (point && typeof point === 'object') {
        const p = point as Record<string, unknown>
        results.push({
          content: JSON.stringify({
            point: name,  // gulika, maandi, kaala, mrityu, artha_prabhakara, yama
            sign: p.sign,
            sign_id: p.sign_id,
            longitude_deg: p.longitude_deg,
            nakshatra: p.nakshatra,
            ayanamsha_id: input.ayanamsha_id,
          }),
          confidence: 0.90,
        })
      }
    }

    const resultJson = JSON.stringify(results)

    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'query_special_lagnas',
      tool_version: '1.0',
      invocation_params: { ...input },
      results,
      served_from_cache: false,
      latency_ms: Date.now() - startMs,
      result_hash: sha256(resultJson),
      schema_version: '1.0',
    }
  },
}
