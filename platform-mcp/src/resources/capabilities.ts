/**
 * capabilities.ts — MCP resource: marsys://capabilities
 *
 * PLACEHOLDER in S3. S4 replaces the hardcoded section with live
 * tool_health() + data_coverage() calls.
 *
 * Structure per perf brief §6.3. Super_admin + acharya: full snapshot.
 * Client: tool names + caveats only.
 *
 * MCPT v3.1.0-S3 (PLACEHOLDER — "perf data pending S4 wiring")
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

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
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://capabilities',
          mimeType: 'text/markdown',
          text: CAPABILITIES_PLACEHOLDER,
        },
      ],
    })
  )
}
