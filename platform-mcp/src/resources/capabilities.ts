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
| \`multi_school_bundle\` | Degraded — per-school evidence active; \`cross_school_lookup\` sub-tool PARKED (F-WP17-1) |

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
| \`cross_school_lookup\` | PARKED — no backing capability (WS-0 stub); pending native review (F-WP17-1) |

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

## THE ASTROLOGICAL SURFACE (R5 W3 — \`judgment_query\` + \`graha_portrait\`)

**Estate consolidation (design §5/§29): ~70 legacy tool names → 15 substrate instruments +
\`judgment_query\` + \`graha_portrait\` = 17.** Every legacy/absorbed name SURVIVES as a live
alias — nothing is ever removed, only superseded by a richer entry point. When two tools can
answer the same question, prefer the CONSOLIDATED one below for new work; the narrower legacy
name remains correct for an existing integration that already depends on its exact response
shape.

**\`judgment_query\`** — the classical bhava-adhyaya judgment recipe as ONE instrument (design
§28.1) — the acharya's own working method for ANY bhava-question, not hardcoded to marriage.
Pass \`domain\` (marriage/relationship/career/wealth/health/progeny/education/spirituality) or a
bare \`bhava\` (1-12). One call returns the COMPLETE classical checklist: bhava condition (sign +
occupants + aspecting grahas) · bhāveśa (lord) condition + placement + dignity + strength ·
kāraka condition · judged from BOTH lagna AND chandra (Sudarshana discipline) · operative-varga
confirmation (e.g. D9 for marriage) · bearing yogas/doshas · timing hooks (dasha windows) · a
deterministic promise-register verdict · a classical-units completeness **receipt**:
\`{bhava, bhavesha, karaka, from_moon, varga_confirmed, yogas_checked, bhanga_checked, timing_anchored}\`.
Astrologically typed \`drill_pointers\` (design §28.4) point to the next classical move —
\`confirm_in_varga\`, \`opposing_yoga\`, \`dasha_of_promise\`, \`dispositor_chain\`, \`tail_dissent\`,
etc. — not generic "more data" pointers.

**WHEN TO USE \`judgment_query\` vs a narrower tool:** use it for ANY "how is X" bhava-question
(marriage/career/health/wealth/progeny/education/spirituality, or a bare house). Use a narrower
tool instead when you already know exactly which single fact you need and want to avoid the
fuller checklist's cost — e.g. \`get_dashas\` alone for "what dasha am I in", \`get_positions\`
alone for "what sign is Saturn in".

**\`graha_portrait\`** — the mirror recipe for graha-questions (design §28.2), "how is my
Saturn?" as ONE call. Supersedes the pattern of separately calling \`get_positions\` +
\`get_dignity\` + \`get_strength\` + \`get_avasthas\` + \`get_yoga_dosha\` + \`get_dashas\` +
\`query_signals\` + \`traverse_graph\` one at a time for a single-graha question — all eight
stay independently callable (nothing removed), but \`graha_portrait\` is the one-call synthesis.
Returns: current position · dignity chain across operative vargas (D1/D9/D10/D60 highlighted) ·
shadbala decomposition · avasthas · yogas/configurations it participates in (parivartana
exchanges are real chart-specific data; catalog yoga/dosha matches are honestly labeled
"not confirmed firings," JL-004/JL-016) · its dasha periods (past/next Mahadashas) · its CGM
neighborhood · functional nature for this lagna. \`chart_id\` + \`graha\` required (accepts
English/Sanskrit names, 2-letter shorthand, or the stored fact_subject code). Use \`include\` to
narrow to a subset of sections when only one is needed.

**THE SHASTRA MAP** (domain → bhava/kāraka/operative varga, design §28.5 — this is the ONLY
domain vocabulary \`judgment_query\`'s \`domain\` param accepts; it is a closed classical set, not
whatever \`bodha_msr_signals.domain\` happens to contain — see R5_JUDGMENT_LEDGER JL-018 for why
it was NOT further widened this wave. Anything not on this list is still fully reachable via a
bare \`bhava\` 1-12, e.g. siblings=3rd, parents=4th/9th, longevity=8th, disputes/litigation=6th,
foreign residence=12th — the classical bhava signification the tradition already assigns them):

| Domain | Bhava | Kāraka(s) | Varga |
|---|---|---|---|
| marriage / relationship / partnership | 7th | Venus | D9 |
| career / vocation | 10th | Sun, Mercury, Saturn | D10 |
| wealth / finance | 2nd | Jupiter | D2 |
| health / vitality | 1st | Sun | D6 |
| progeny / children | 5th | Jupiter | D7 |
| education | 4th | Mercury, Jupiter | D24 |
| spirituality | 9th | Jupiter, Ketu | D20 |

**DOMAIN ASSESSMENT — canonical tools.** \`assess_marriage\` / \`assess_career\` /
\`assess_health\` / \`assess_wealth\` return the domain-reading + temporal-activation +
contradiction bundle for their domain. (The redundant \`apex_*_assess\` aliases — which
resolved to the SAME capability — were retired per WP-1.3(i)/LCA-11; their two tuning params,
\`max_signals_per_lens\` / \`max_contradictions\`, are now on the canonical \`assess_*\` tools, so
no capability was lost.) \`judgment_query\` is the richer, shastra-shaped successor (design §29: apex folds INTO
judgment_query as an alias RELATIONSHIP, not a code-identical replacement — the two are verified
astrologically consistent, R5_JUDGMENT_LEDGER JL-015(a)/JL-017, but each keeps its own response
shape so neither breaks an existing caller) — prefer \`judgment_query\` for new bhava-judgment
questions; the apex_* names are safe to keep calling for existing integrations, and are the
right choice when you specifically want the apex bundle's own contradiction/convergence framing.

---

${PROVENANCE_STAMP_HYGIENE_SECTION}

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

/**
 * SESSION HYGIENE + SESSION PIN (R5 W4 — design §10.6 SESSION STABILITY +
 * §31.3 SESSION-PIN COLLISION + §31.5 BUILD PROVENANCE AT SERVE TIME).
 * Shared between the live and placeholder markdown so this teaching surface
 * never silently regresses when perf-data wiring fails.
 */
const PROVENANCE_STAMP_HYGIENE_SECTION = `## SESSION HYGIENE + PROVENANCE STAMP (design §10.6 / §31.3 / §31.5)

**Session key collision risk (§31.3):** \`mcp_sessions\` is keyed by (user, session_key), and
\`session_key\` defaults to \`"default"\` when a client sends none. Two CONCURRENT conversations by
the same user that both omit \`session_key\` share ONE session row — including one
\`active_chart_id\` and one set of provenance stamps. **Client hygiene rule: pass a stable, distinct
\`session_key\` per conversation/thread** (e.g. a conversation/thread id) whenever more than one
conversation for the same user may be live at once. Never rely on \`active_chart_id\` for
correctness — it is a convenience default only; pass \`chart_id\` explicitly on every chart-scoped
call regardless of what was last selected.

**Provenance stamp** (\`recall_session\`, \`select_chart\`): resolves/refreshes, per EXPLICIT chart_id,
\`provenance_stamp = {priors_version, formula_versions, ranking_config, build_id, build_status,
now_context_date, pinned_at}\` — captured once per (session_key, chart_id) pair (re-keyed inside
the session's state, so two chart contexts under one session_key get independent stamps, mitigating
part of §31.3). This is NOT a mechanism to keep reading an OLDER chart build's data — L1+ storage
is delete-then-insert per chart (a rebuild REPLACES rows in place; no historical snapshot is kept).
It is an honesty mechanism: if the chart's \`build_id\` changes mid-session (a rebuild happened
while you were mid-conversation), the stamp is refreshed to the NEW build and the response carries
\`judgment_flags: ["chart_rebuilt_mid_provenance_stamp_refreshed"]\` plus a plain-language advisory —
never a silent blend of pre-rebuild assumptions with post-rebuild data.

**Full fix scope note:** per-conversation session keys are ultimately a CLIENT concern (the MCP
client, not this server, knows which calls belong to the same conversation) — the full fix rides
the MCP-elevation workstream. This wave ships the mitigations available at the serving layer:
explicit chart_id everywhere, chart_id-rekeyed stamps, and this documented hygiene rule.`

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
| \`multi_school_bundle\` | Per-school evidence (Parashara + Jaimini + KP + Tajaka); \`cross_school_lookup\` sub-tool PARKED pending native review (F-WP17-1) |

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
| \`cross_school_lookup\` | PARKED — WS-0 stub, no backing capability; pending native review (F-WP17-1) |

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

## THE ASTROLOGICAL SURFACE (R5 W3 — \`judgment_query\` + \`graha_portrait\`)

Estate consolidation (design §5/§29): ~70 legacy names → 15 substrate instruments +
\`judgment_query\` + \`graha_portrait\` = 17. Every absorbed legacy name survives as a live alias.

\`judgment_query\` — the classical bhava-adhyaya judgment recipe as ONE instrument (design §28.1),
for ANY bhava-question ("how is the marriage?", "how is my career?", or a bare house number).
Pass \`domain\` (marriage/relationship/career/wealth/health/progeny/education/spirituality — the
shastra map, design §28.5) or \`bhava\` (1-12). Returns the full classical checklist — bhava
condition, bhāveśa condition, kāraka condition, judged from lagna AND chandra, operative-varga
confirmation, bearing yogas, timing hooks, a deterministic verdict, a completeness receipt
(\`{bhava, bhavesha, karaka, from_moon, varga_confirmed, yogas_checked, bhanga_checked, timing_anchored}\`),
and astrologically typed \`drill_pointers\` (design §28.4).

\`graha_portrait\` — the mirror recipe for graha-questions (design §28.2), "how is my Saturn?" as
ONE call: position, dignity chain, shadbala, avasthas, yoga participation, dasha periods, CGM
neighborhood, functional nature — synthesized over the already-built L1/L2 tools (\`get_positions\`,
\`get_dignity\`, \`get_strength\`, \`get_avasthas\`, \`get_yoga_dosha\`, \`get_dashas\`, \`query_signals\`,
\`traverse_graph\`, all still independently callable) so a single-graha question is one call, not eight.

The canonical \`assess_marriage\` / \`assess_career\` / \`assess_health\` / \`assess_wealth\` domain
tools remain fully answerable — \`judgment_query\` is their richer successor (design §29), not a
replacement that breaks existing callers. (The redundant \`apex_*_assess\` aliases were retired per
WP-1.3(i)/LCA-11; capability preserved on the canonical \`assess_*\` tools.)

---

${PROVENANCE_STAMP_HYGIENE_SECTION}

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
