/**
 * pyhora_dasha_periods.ts — RetrievalTool: query_dasha_periods
 *
 * Calls /api/pyhora/compute and returns the Vimshottari dasha chain
 * (mahadasha sequence with start/end dates) for a given birth data.
 *
 * Capability: query_dasha_periods
 * Engine: PyJHora 4.8.6
 * Layer: L1 Gaṇita — ganita.dasakrama
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
  name: 'query_dasha_periods',
  version: '1.0',
  description:
    'Compute Vimshottari dasha mahadasha chain for a chart via PyJHora. ' +
    'Returns mahadasha sequence with lord, start_date, end_date, antardasha tree. ' +
    'Engine: PyJHora 4.8.6. Layer: L1 Gaṇita / ganita.dasakrama.',

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

    // Extract dasha chain from pyhora response
    const dashaData = (data.vimshottari_dasha ?? {}) as Record<string, unknown>
    const mahadasha_sequence = Array.isArray(dashaData.mahadasha_sequence)
      ? dashaData.mahadasha_sequence
      : Array.isArray((dashaData as Record<string, unknown>).mahadashas)
        ? (dashaData as Record<string, unknown>).mahadashas
        : []

    const results: ToolBundleResult[] = (mahadasha_sequence as Record<string, unknown>[]).map(
      (md) => ({
        content: JSON.stringify({
          lord: md.lord,
          start_date: md.start_date ?? md.start_iso,
          end_date: md.end_date ?? md.end_iso,
          years: md.years,
          antardashas: Array.isArray(md.antardashas)
            ? (md.antardashas as Record<string, unknown>[]).slice(0, 3)  // first 3 ADs for brevity
            : [],
        }),
        confidence: 0.95,
      })
    )

    // Also include summary metadata
    results.unshift({
      content: JSON.stringify({
        moon_nakshatra: dashaData.moon_nakshatra,
        moon_nakshatra_lord: dashaData.moon_nakshatra_lord,
        balance_years: dashaData.balance_years,
        total_mahadashas: mahadasha_sequence.length,
        ayanamsha_id: input.ayanamsha_id,
      }),
      confidence: 0.98,
    })

    const resultJson = JSON.stringify(results)

    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'query_dasha_periods',
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
