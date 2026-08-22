/**
 * consumption_protocol.ts — MCP resource: marsys://consumption-protocol
 *
 * WP-1.6 (P-12), REMEDIATION_PLAN_v3_0 §1 E3 + §5 (WP-1.6 widened). The served
 * consumption PROTOCOL: an MCP-exposed instruction surface that teaches ANY
 * consuming LLM the demand-side posture, so E3 is operative from the moment W1
 * deploys — ahead of the doctrine campaign's full planner.
 *
 * The posture, verbatim in intent (native): on receiving a query, FORM the most
 * extensive set of evidence you EXPECT first (from the capability map + the
 * question's domain), CHASE every item across ALL appropriate tools, TRACK
 * received-vs-needed with the acquisition tracker, DECLARE honest exhaustion per
 * item, and treat whatever arrives beyond the plan as BONUS — never the frame.
 * "Not finding everything is acceptable; not chasing is not. The approach is the
 * requirement."
 *
 * This resource is static teaching text (no chart data, no entitlement surface) —
 * it pairs with:
 *   - the capability MAP (00_ARCHITECTURE/llm_consumption_audit/capability_map/
 *     CONCEPT_CAPABILITY_MAP.json) — which tool serves concept X;
 *   - the acquisition-tracker schema (platform/src/lib/retrieval/demand/
 *     acquisition_tracker.ts) — the received/needed/exhausted record it fills in;
 *   - the guided prompt `demand_side_chase` (platform-mcp/src/prompts/index.ts) —
 *     the executable, chart-parametrized version of this same protocol.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const CONSUMPTION_PROTOCOL_MARKDOWN = `# MARSYS-JIS Served Consumption Protocol (E3 — Demand-Side Chase)
**MCP Resource: \`marsys://consumption-protocol\`**

This protocol governs HOW you consume this instrument's tools. It is not optional
styling — it is the requirement. Supply-side satisfaction ("I called a tool, it
answered, done") is the failure mode this instrument was built to defeat. You are
in **demand-side** mode: you decide what evidence a good answer needs, then you go
get it.

---

## The one rule

> **Form the most extensive set of evidence you EXPECT first — then chase every
> item across ALL appropriate tools until each is fetched or honestly exhausted.
> Whatever arrives beyond your plan is bonus, never the frame. Not finding
> everything is acceptable; not chasing is not.**

---

## The five moves

### 1. FORM the expected-evidence set (before calling any tool)
From the question's domain and the **capability map**, write down the extensive
set of evidence a complete answer would rest on — the classical checklist, not the
usual suspects.
- Narrow question → a narrow but *comprehensive* list (every fact that bears on it).
- Broad question → a wide, comprehensive list spanning layers and systems.
- Anchor each expected item to a **concept family** from the capability map so you
  know which tool/service is supposed to serve it. The map is keyed
  concept-family → route(s), per channel (deployed-MCP vs surgical).

Classical grounding (Whole-Chart-Read, B.11): a bhava judgment expects, at minimum,
the bhava condition, the bhāveśa (lord) condition + placement + dignity + strength,
the kāraka condition, the reading from BOTH lagna and chandra (the chandra leg's own
\`ayanamsha_frame_sensitivity\` — F-159 — discloses, never rules on, whether the Moon's
sign itself agrees across the 5 real ayanamshas), operative-varga
confirmation, bearing yogas/doshas, and timing hooks (dasha windows). Form the
*whole* set up front; do not let the first tool's payload define the frame.

### 2. TRACK received-vs-needed (the acquisition tracker)
Instantiate an **acquisition tracker** (schema:
\`platform/src/lib/retrieval/demand/acquisition_tracker.ts\`): one record per
expected item, each \`needed\` / \`received\` / \`exhausted\`. This is your working
memory of the chase — keep it current as evidence arrives.

### 3. CHASE across ALL appropriate tools
For each \`needed\` item, walk its candidate routes from the map. A concept may be
served by several tools (e.g. an MSR signal via \`query_signals\`, \`query_domain_reading\`,
or \`traverse_chart_graph\`) — the map lists them; pick and call. When a tool returns
**drill_pointers**, follow the ones that advance an outstanding item. Continue until
each item is either received or you can state, honestly, why it is exhausted.

### 4. DECLARE honest exhaustion per item (never silent)
An item leaves the chase only via a stated reason:
- \`no_route\` — the map exposes no tool for it (truly-unreachable / down-pipeline);
- \`route_empty\` — the route was called and honestly returned nothing for this chart;
- \`route_error\` — the route errored/timed out;
- \`not_applicable\` — on inspection it does not apply to this chart/question;
- \`budget_exhausted\` — the call/latency budget ran out before this item;
- \`superseded\` — a broader item's arrival subsumed it.
Report the exhausted items alongside the received ones. A gap you disclose is
honest; a gap you hide is the failure this protocol exists to prevent.

### 5. TREAT extras as bonus
Evidence that arrives inside a payload without having been planned is **volunteered**
— record it (\`provenance: 'volunteered'\`), use it, but never let it stand in for the
plan. The frame is the expected set you formed in move 1.

---

## What "done" means
You are done when **no item remains \`needed\`** — every expected item is either
\`received\` or \`exhausted\` with a reason (\`chase_complete === true\` in the tracker).
Coverage = received / total; report it. Answering before the chase is complete, or
letting the tools' volunteered output define what you looked for, is a protocol
violation equivalent to a red-team finding (B.11).

---

## Companion surfaces
- **Capability map** — \`00_ARCHITECTURE/llm_consumption_audit/capability_map/CONCEPT_CAPABILITY_MAP.json\`
  (concept-family → route(s), per channel; regenerated post-W1).
- **Acquisition tracker schema** — \`platform/src/lib/retrieval/demand/acquisition_tracker.ts\`.
- **Guided prompt** — invoke the \`demand_side_chase\` prompt for a chart-parametrized,
  step-by-step run of this protocol.
- **Capabilities snapshot** — \`marsys://capabilities\` for the live tool inventory.

*E3 is operative from W1 deploy. The full demand-side planner is the doctrine campaign;
this protocol is its servable core.*
`

export function registerConsumptionProtocol(server: McpServer): void {
  server.resource(
    'consumption-protocol',
    new ResourceTemplate('marsys://consumption-protocol', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://consumption-protocol',
          mimeType: 'text/markdown',
          text: CONSUMPTION_PROTOCOL_MARKDOWN,
        },
      ],
    })
  )
}

/** Exported for the registration test (retrievability without a live server). */
export const CONSUMPTION_PROTOCOL_TEXT = CONSUMPTION_PROTOCOL_MARKDOWN
