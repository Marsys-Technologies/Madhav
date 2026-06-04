import { tool } from 'ai'
import { z } from 'zod'
import { query } from '@/lib/db/client'

// list_documents, read_document, create_document, update_document,
// append_to_document, search_in_document removed in WS-0C Sub-E:
// they referenced the dropped 'documents' table. Rebuild under Brahma.

export const buildTools = {
  update_layer_status: tool({
    description: 'Update the status of a pyramid layer/sublayer.',
    inputSchema: z.object({
      chart_id: z.string().describe('The chart UUID'),
      layer: z.string().describe('Layer designation (L1, L2, L2.5, L3, L4)'),
      sublayer: z.string().describe('Sublayer name'),
      status: z.enum(['not_started', 'in_progress', 'complete']).describe('New status'),
    }),
    execute: async ({ chart_id, layer, sublayer, status }) => {
      try {
        await query(
          `INSERT INTO pyramid_layers (chart_id, layer, sublayer, status, updated_at)
           VALUES ($1,$2,$3,$4,now())
           ON CONFLICT (chart_id, layer, sublayer) DO UPDATE
           SET status=$4, updated_at=now()`,
          [chart_id, layer, sublayer, status]
        )
        return { layer, sublayer, status }
      } catch (e) {
        return { error: e instanceof Error ? e.message : String(e) }
      }
    },
  }),

  run_ephemeris: tool({
    description: 'Run ephemeris calculation for a birth chart via the Python sidecar.',
    inputSchema: z.object({
      birth_date: z.string().describe('Birth date in YYYY-MM-DD format'),
      birth_time: z.string().describe('Birth time in HH:MM format'),
      lat: z.number().describe('Birth latitude in decimal degrees'),
      lng: z.number().describe('Birth longitude in decimal degrees'),
      ut_offset: z.number().optional().describe('UTC offset in hours (default: 5.5 for IST)'),
    }),
    execute: async ({ birth_date, birth_time, lat, lng, ut_offset = 5.5 }) => {
      try {
        const url = process.env.PYTHON_SIDECAR_URL + '/ephemeris'
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': process.env.PYTHON_SIDECAR_API_KEY ?? '',
          },
          body: JSON.stringify({ birth_date, birth_time, lat, lng, ut_offset }),
        })
        if (!res.ok) return { error: `Ephemeris request failed: ${res.status} ${res.statusText}` }
        return await res.json()
      } catch (e) {
        return { error: e instanceof Error ? e.message : String(e) }
      }
    },
  }),

  run_computation: tool({
    description: 'Run an arbitrary computation endpoint on the Python sidecar.',
    inputSchema: z.object({
      type: z.string().describe('Computation type / endpoint path (e.g. dashas, transits)'),
      params: z.record(z.string(), z.unknown()).describe('Parameters to pass as the request body'),
    }),
    execute: async ({ type, params }) => {
      try {
        const url = process.env.PYTHON_SIDECAR_URL + '/' + type
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': process.env.PYTHON_SIDECAR_API_KEY ?? '',
          },
          body: JSON.stringify(params),
        })
        if (!res.ok) return { error: `Computation request failed: ${res.status} ${res.statusText}` }
        return await res.json()
      } catch (e) {
        return { error: e instanceof Error ? e.message : String(e) }
      }
    },
  }),

  get_pyramid_status: tool({
    description: 'Get the status of all pyramid layers for a chart.',
    inputSchema: z.object({
      chart_id: z.string().describe('The chart UUID'),
    }),
    execute: async ({ chart_id }) => {
      try {
        const { rows } = await query(
          'SELECT layer, sublayer, status, version, updated_at FROM pyramid_layers WHERE chart_id=$1 ORDER BY layer ASC, sublayer ASC',
          [chart_id]
        )
        return rows
      } catch (e) {
        return { error: e instanceof Error ? e.message : String(e) }
      }
    },
  }),
}
