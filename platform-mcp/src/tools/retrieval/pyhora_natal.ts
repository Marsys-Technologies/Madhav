/**
 * pyhora_natal.ts — MCP tools: compute_natal_positions, query_dasha_periods, query_special_lagnas
 *
 * Registers 3 PyJHora capabilities as MCP tools that call the python-sidecar
 * /api/pyhora/compute endpoint.
 *
 * These tools expose the L1 Gaṇita PyJHora computation engine to MCP clients
 * (Claude Desktop, ChatGPT, etc.) for per-chart natal analysis.
 *
 * Stream G deliverable (BRAHMA-G-1).
 * Engine: PyJHora 4.8.6.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

// ── Shared birth data schema ──────────────────────────────────────────────────

const BirthDataSchema = {
  datetime_iso: z.string().describe(
    "Birth datetime in local wall-clock ISO format, e.g. '1984-02-05T10:43:00'"
  ),
  latitude_deg: z.number().describe('Geographic latitude in decimal degrees (N positive)'),
  longitude_deg: z.number().describe('Geographic longitude in decimal degrees (E positive)'),
  tz_offset_hours: z.number().default(5.5).describe('Timezone offset hours (e.g. 5.5 for IST)'),
  place_name: z.string().optional().describe('Place name (informational)'),
  ayanamsha_id: z
    .enum(['lahiri', 'raman', 'kp', 'true_citra'])
    .default('lahiri')
    .describe('Ayanamsha to use for sidereal computation'),
}

// ── Sidecar caller ────────────────────────────────────────────────────────────

function sidecarUrl(): string {
  const base = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8000'
  return base.replace(/\/$/, '')
}

async function callPyHora(params: Record<string, unknown>): Promise<Record<string, unknown>> {
  const url = `${sidecarUrl()}/api/pyhora/compute`
  const apiKey = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'x-api-key': apiKey } : {}),
    },
    body: JSON.stringify(params),
    signal: AbortSignal.timeout(30_000),
  })

  if (!resp.ok) {
    const body = await resp.text().catch(() => '')
    throw new Error(`pyhora/compute HTTP ${resp.status}: ${body.slice(0, 200)}`)
  }

  return resp.json() as Promise<Record<string, unknown>>
}

// ── Tool registrations ────────────────────────────────────────────────────────

/**
 * Register compute_natal_positions MCP tool.
 * Returns graha_sthana: all 9 planets + Lagna with sign, nakshatra, pada, house, longitude.
 */
export function registerComputeNatalPositionsTool(server: McpServer): void {
  server.tool(
    'compute_natal_positions',
    {
      ...BirthDataSchema,
    },
    async (params) => {
      try {
        const data = await callPyHora(params)

        const grahas = Array.isArray(data.graha_sthana) ? data.graha_sthana : []
        const bhava_lagna = data.bhava_lagna ?? {}

        const planetTable = grahas
          .map((g: Record<string, unknown>) =>
            `${String(g.name).padEnd(8)} | ${String(g.sign).padEnd(11)} | ` +
            `${String(g.nakshatra ?? '').padEnd(18)} | P${g.pada} | H${g.house} | ` +
            `${Number(g.longitude_deg ?? 0).toFixed(2)}° ` +
            `${g.is_retrograde ? '[R]' : '   '}`
          )
          .join('\n')

        const text =
          `# Natal Chart — graha_sthana\n` +
          `Engine: ${data.engine ?? 'PyJHora'} | Ayanamsha: ${params.ayanamsha_id ?? 'lahiri'}\n\n` +
          `Planet   | Sign        | Nakshatra          | Pd | Hs | Longitude\n` +
          `---------|-------------|--------------------|----|----|-----------\n` +
          planetTable +
          `\n\nLagna: ${(bhava_lagna as Record<string, unknown>).sign ?? 'N/A'} ` +
          `(${Number((bhava_lagna as Record<string, unknown>).longitude_deg ?? 0).toFixed(2)}°)`

        return {
          content: [{ type: 'text', text }],
        }
      } catch (err) {
        return {
          content: [
            {
              type: 'text',
              text: `Error computing natal positions: ${err instanceof Error ? err.message : String(err)}`,
            },
          ],
          isError: true,
        }
      }
    }
  )
}

/**
 * Register query_dasha_periods MCP tool.
 * Returns Vimshottari mahadasha chain with lord, start/end dates.
 */
export function registerQueryDashaPeriodsTool(server: McpServer): void {
  server.tool(
    'query_dasha_periods',
    {
      ...BirthDataSchema,
    },
    async (params) => {
      try {
        const data = await callPyHora(params)

        const dashas = (data.vimshottari_dasha ?? {}) as Record<string, unknown>
        const mahadashas = Array.isArray(dashas.mahadasha_sequence)
          ? dashas.mahadasha_sequence
          : Array.isArray(dashas.mahadashas)
            ? dashas.mahadashas
            : []

        const rows = (mahadashas as Record<string, unknown>[])
          .slice(0, 9)
          .map((md) =>
            `${String(md.lord ?? '').padEnd(9)} | ${String(md.start_date ?? md.start_iso ?? '').slice(0, 10)} → ` +
            `${String(md.end_date ?? md.end_iso ?? '').slice(0, 10)} | ${Number(md.years ?? 0).toFixed(1)}y`
          )
          .join('\n')

        const text =
          `# Vimshottari Dasha — mahadasha chain\n` +
          `Engine: ${data.engine ?? 'PyJHora'} | Ayanamsha: ${params.ayanamsha_id ?? 'lahiri'}\n` +
          `Moon nakshatra: ${dashas.moon_nakshatra ?? 'N/A'} (lord: ${dashas.moon_nakshatra_lord ?? 'N/A'})\n` +
          `Balance at birth: ${Number(dashas.balance_years ?? 0).toFixed(2)}y\n\n` +
          `Lord      | Start      → End        | Duration\n` +
          `----------|---------------------------|---------\n` +
          rows

        return {
          content: [{ type: 'text', text }],
        }
      } catch (err) {
        return {
          content: [
            {
              type: 'text',
              text: `Error querying dasha periods: ${err instanceof Error ? err.message : String(err)}`,
            },
          ],
          isError: true,
        }
      }
    }
  )
}

/**
 * Register query_special_lagnas MCP tool.
 * Returns ascendant + upagrahas (Gulika, Maandi, Kaala, Mrityu, etc.)
 */
export function registerQuerySpecialLagnasTool(server: McpServer): void {
  server.tool(
    'query_special_lagnas',
    {
      ...BirthDataSchema,
    },
    async (params) => {
      try {
        const data = await callPyHora(params)

        const lagna = (data.bhava_lagna ?? {}) as Record<string, unknown>
        const specialPoints = (data.special_lagnas ?? {}) as Record<string, unknown>

        const lagnaLine =
          `Lagna       | ${String(lagna.sign ?? 'N/A').padEnd(11)} | ` +
          `${Number(lagna.longitude_deg ?? 0).toFixed(2)}°`

        const specialLines = Object.entries(specialPoints)
          .map(([name, pt]) => {
            const p = (pt ?? {}) as Record<string, unknown>
            return (
              `${name.padEnd(12)}| ${String(p.sign ?? 'N/A').padEnd(11)} | ` +
              `${Number(p.longitude_deg ?? 0).toFixed(2)}°`
            )
          })
          .join('\n')

        const text =
          `# Special Lagnas & Upagrahas\n` +
          `Engine: ${data.engine ?? 'PyJHora'} | Ayanamsha: ${params.ayanamsha_id ?? 'lahiri'}\n\n` +
          `Point        | Sign        | Longitude\n` +
          `-------------|-------------|----------\n` +
          lagnaLine +
          (specialLines ? '\n' + specialLines : '')

        return {
          content: [{ type: 'text', text }],
        }
      } catch (err) {
        return {
          content: [
            {
              type: 'text',
              text: `Error querying special lagnas: ${err instanceof Error ? err.message : String(err)}`,
            },
          ],
          isError: true,
        }
      }
    }
  )
}
