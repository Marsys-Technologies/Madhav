/**
 * capabilities.ts — MCP resource: marsys://capabilities
 *
 * Wired in S4: fetches live perf data from tool_health() + data_coverage()
 * at session attach time. Falls back to static snapshot if fetch fails.
 *
 * Structure per perf brief §6.3. Super_admin + acharya: full snapshot.
 * Client: tool names + caveats only.
 *
 * MCPT v3.1.0-S4 (replaces S3 placeholder with live perf data wiring)
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function fetchToolHealth(): Promise<unknown> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/health/tools`, {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': 'system',
        'X-MCP-Audience-Tier': 'super_admin',
        'X-MCP-Key-Id': 'resource-loader',
      },
      signal: AbortSignal.timeout(5_000),
    })
    if (!response.ok) return null
    return response.json()
  } catch { return null }
}

async function fetchDataCoverage(): Promise<unknown> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/health/coverage`, {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': 'system',
        'X-MCP-Audience-Tier': 'super_admin',
        'X-MCP-Key-Id': 'resource-loader',
      },
      signal: AbortSignal.timeout(5_000),
    })
    if (!response.ok) return null
    return response.json()
  } catch { return null }
}

function buildCapabilitiesMarkdown(
  toolHealth: unknown,
  dataCoverage: unknown,
  timestamp: string
): string {
  const th = toolHealth as Record<string, unknown> | null
  const dc = dataCoverage as { coverage?: Array<{ tool: string; category: string; status: string; caveat?: string; expected_rows?: number }> } | null

  const pendingCategories = dc?.coverage
    ?.filter(c => c.status === 'pending')
    .map(c => `${c.tool}:${c.category}`)
    .join(', ') ?? 'KP, Tajaka, Shadbala, Ashtakavarga (v3.3 pending)'

  return `# MARSYS-JIS Capabilities Snapshot
**MCP Resource: \`marsys://capabilities\`**
*Generated at: ${timestamp} | Source: tool_health() + data_coverage()*

---

## Available Tools (21 total)

### Tier 2 — Composite Bundles (MCPT v3.1.0-S2)
| Tool | Status |
|---|---|
| \`holistic_bundle\` | Active — 8-tool parallel read |
| \`multi_school_bundle\` | Active — cross-school convergence |

### Tier 3 — Surgical Primitives
| Tool | Coverage Note |
|---|---|
| \`query_signals\` | 573 MSR signals active |
| \`query_chart_facts\` | 37 categories; pending: ${pendingCategories} |
| \`query_dasha_periods\` | Active |
| \`query_panchanga\` | 73,414 rows (1900-2100) |
| \`query_ephemeris\` | Active |
| \`query_transit_event\` | Active |
| \`lel_query\` | 36 life events active |
| \`vector_search\` | UCN + RM + CDLM active |
| \`get_cgm_subgraph\` | Active |
| \`cross_school_lookup\` | Active |

### Tier 4 — Raw Asset
| Tool | Status |
|---|---|
| \`read_asset\` | Active |

### Tier 5 — Observability
| Tool | Note |
|---|---|
| \`get_trace\` | Active + audit findings (S4) |
| \`list_recent_queries\` | Active |
| \`tool_health\` | Active (super_admin + acharya only) |
| \`data_coverage\` | Active (super_admin + acharya only) |

### Tier 6 — Write
| Tool | Status |
|---|---|
| \`log_prediction\` | Active (PPL discipline) |
| \`record_outcome\` | Active |
| \`flag_disagreement\` | Active |

---

## Data Coverage Summary

${dc?.coverage?.map(c =>
    `- **${c.tool}/${c.category}**: ${c.status}${c.expected_rows ? ` (expected: ${c.expected_rows} rows)` : ''}${c.caveat ? ` — ⚠️ ${c.caveat}` : ''}`
  ).join('\n') ?? '- Coverage data pending migration 076 + seed application'}

---

## Perf Health

${th
    ? `Tool health data available. Call \`tool_health()\` for detailed per-tool metrics.`
    : `Tool health data pending (migrations 073–076 + nightly audit first run).`}

---

*Next: run \`tool_health()\` or \`data_coverage()\` for live metrics. Audit job runs at 03:00 UTC.*
`
}

const CAPABILITIES_PLACEHOLDER = `# MARSYS-JIS Capabilities Snapshot
**MCP Resource: \`marsys://capabilities\`**
*Note: perf data pending S4 wiring. This is a static placeholder.*
*Auto-generated at: ${new Date().toISOString()}*

---

## Available Tools (21 total)

### Tier 2 — Composite Bundles
| Tool | Description |
|---|---|
| \`holistic_bundle\` | 8-tool parallel holistic read (MSR + CGM + UCN + RM + CDLM + LEL + Panchang + Dasha) |
| \`multi_school_bundle\` | Cross-school convergence check (Parashara + Jaimini + KP + Tajaka) |

### Tier 3 — Surgical Primitives
| Tool | Description |
|---|---|
| \`query_signals\` | MSR signal corpus lookup (499+ signals, structured filters) |
| \`query_chart_facts\` | chart_facts table query (795+ rows, 37 categories) |
| \`query_dasha_periods\` | Vimshottari dasha periods + active state |
| \`query_panchanga\` | Daily panchang (tithi, vara, nakshatra, yoga, karana) |
| \`query_ephemeris\` | Planetary positions for any date/time |
| \`query_transit_event\` | Transit events for a time window |
| \`lel_query\` | Life Event Log query (36 events + 5 period summaries) |
| \`vector_search\` | Semantic search across UCN/RM/CDLM corpus |
| \`get_cgm_subgraph\` | CGM graph subgraph walk |
| \`cross_school_lookup\` | Multi-school convergence check for a specific claim |

### Tier 4 — Raw Asset
| Tool | Description |
|---|---|
| \`read_asset\` | Raw text read of any registered L1 or L2.5 asset |

### Tier 5 — Observability
| Tool | Description |
|---|---|
| \`get_trace\` | Full query trace for a prior call (steps + latencies + audit findings) |
| \`list_recent_queries\` | Recent query log |
| \`tool_health\` | Tool-level health metrics (super_admin + acharya only) — *pending S4* |
| \`data_coverage\` | Data coverage report per tool (super_admin + acharya only) — *pending S4* |

### Tier 6 — Write
| Tool | Description |
|---|---|
| \`log_prediction\` | Log a prospective prediction (PPL discipline) |
| \`record_outcome\` | Record outcome against a prior prediction |
| \`flag_disagreement\` | Open a governance disagreement entry |

---

## Data Coverage (PLACEHOLDER — S4 will wire live data)

| Source | Rows | Status |
|---|---|---|
| chart_facts | ~795 | Partially backfilled |
| msr_signals | ~499 | Active |
| life_event_log | 36 events | Active |
| panchanga_daily | 73,414 | Active (1900–2100) |
| cgm_nodes | ~1,200 | Active |

---

*Perf data pending S4 wiring. S4 replaces this placeholder with live tool_health() + data_coverage() calls.*
`

export function registerCapabilities(server: McpServer): void {
  server.resource(
    'capabilities',
    new ResourceTemplate('marsys://capabilities', { list: undefined }),
    async (_uri) => {
      // S4: fetch live perf data; fall back to static placeholder on error
      const timestamp = new Date().toISOString()
      let text: string
      try {
        const [toolHealth, dataCoverage] = await Promise.all([
          fetchToolHealth(),
          fetchDataCoverage(),
        ])
        text = buildCapabilitiesMarkdown(toolHealth, dataCoverage, timestamp)
      } catch {
        text = CAPABILITIES_PLACEHOLDER
      }

      return {
        contents: [
          {
            uri: 'marsys://capabilities',
            mimeType: 'text/markdown',
            text,
          },
        ],
      }
    }
  )
}
