/**
 * pyhora_natal_positions.ts — RetrievalTool: compute_natal_positions
 *
 * Calls the python-sidecar /api/pyhora/compute endpoint to retrieve per-chart
 * natal graha positions computed by PyJHora.
 *
 * Capability: compute_natal_positions
 * Engine: PyJHora 4.8.6 (native decision: PyJHora IS the JH logic)
 * Layer: L1 Gaṇita — ga_positions
 *
 * Stream G deliverable (BRAHMA-G-1).
 */

import { createHash } from 'crypto'
import type { RetrievalTool, ToolBundle, ToolBundleResult, QueryPlan } from './types'

function sha256(data: string): string {
  return 'sha256:' + createHash('sha256').update(data).digest('hex')
}

/** Birth data for natal computation. */
export interface NatalPositionsInput {
  /** ISO datetime local wall-clock: '1984-02-05T10:43:00' */
  datetime_iso: string
  /** Decimal latitude (N positive) */
  latitude_deg: number
  /** Decimal longitude (E positive) */
  longitude_deg: number
  /** Timezone offset hours (e.g. 5.5 for IST) */
  tz_offset_hours: number
  /** Optional place name */
  place_name?: string
  /** Ayanamsha: lahiri|raman|kp|true_citra (default: lahiri) */
  ayanamsha_id?: string
}

function sidecarUrl(): string {
  const base = process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000'
  return base.replace(/\/$/, '')
}

async function callPyHoraCompute(input: NatalPositionsInput): Promise<Record<string, unknown>> {
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
  name: 'compute_natal_positions',
  version: '1.0',
  description:
    'Compute per-chart natal graha positions (graha_sthana) via PyJHora. ' +
    'Returns Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu + Lagna ' +
    'with sign, nakshatra, pada, house, longitude. Engine: PyJHora 4.8.6. ' +
    'Layer: L1 Gaṇita / ga_positions.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {}
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const input: NatalPositionsInput = {
      datetime_iso: String(params.datetime_iso ?? ''),
      latitude_deg: Number(params.latitude_deg ?? 0),
      longitude_deg: Number(params.longitude_deg ?? 0),
      tz_offset_hours: Number(params.tz_offset_hours ?? 5.5),
      place_name: typeof params.place_name === 'string' ? params.place_name : '',
      ayanamsha_id: typeof params.ayanamsha_id === 'string' ? params.ayanamsha_id : 'lahiri',
    }

    const data = await callPyHoraCompute(input)

    const grahas = Array.isArray(data.graha_sthana) ? data.graha_sthana : []
    const results: ToolBundleResult[] = grahas.map((g: Record<string, unknown>) => ({
      content: JSON.stringify({
        planet: g.name,
        sign: g.sign,
        sign_id: g.sign_id,
        nakshatra: g.nakshatra,
        pada: g.pada,
        house: g.house,
        longitude_deg: g.longitude_deg,
        is_retrograde: g.is_retrograde,
        ayanamsha_id: input.ayanamsha_id,
      }),
      confidence: 0.95,
    }))

    const resultJson = JSON.stringify(results)

    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'compute_natal_positions',
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
