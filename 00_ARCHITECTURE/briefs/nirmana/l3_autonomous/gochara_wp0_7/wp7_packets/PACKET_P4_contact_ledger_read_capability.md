---
artifact: WP7_PACKET_P4
packet_id: P-4
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of the serving/read-capability stream (platform-mcp retrieval layer / platform src retrieval registry; new capability, not an edit to a sibling-owned file)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 P-4, §4.3–4.4, §6.1 (contact-ledger consumers row); the codebase's §N.6 density-layering discipline (hard_floor convention as used in platform/src/lib/vidhi/registry_data.ts:1025-1036)
authority_note: "Owed to its owner. Relation shapes referenced from WP1_CONTRACTS.md §3.1/§4.1 (pinned)."
---

# P-4 — Contact-ledger + coverage read capability (density-layered)

## 1. Purpose

A new read capability over `kala_gochara_contacts` + `kala_gochara_coverage` (the two
WP6 relations; shapes pinned in `WP1_CONTRACTS.md` §3.1 and §4.1 — this packet does not
restate every column, it references them). No consumer exists yet; this is the
interface future readers (S-2's Saṅgam path, the reading checklist, MCP drill tools)
opt into. It is §N.6-shaped from the start: **confirmed episodes are never flattened
with catalog-only rows, and a budget trim must never sacrifice the confirmed floor.**

## 2. Request shape

```ts
interface ContactLedgerQuery {
  chart_id: string
  generation?: string            // default: chart's authoritative generation
                                // (explicit kala_gochara_authority read; ABSENT row =
                                // 'unpublished' coverage object, never a 'v1' default — N-10)
  partition?: {                 // all optional; omitted = whole ledger
    body?: string                // 'Saturn', 'Moon', ...
    target_type?: string         // WP1 §5.3 vocabulary
    target_ref?: string
    relation?: string            // conjunction|drishti_contact|sign_ingress|...
    event_class?: string         // projection partitions (coverage side)
    interval?: [string, string]  // overlaps t_in/t_out
  }
  horizon?: { start: string; end: string }   // for moon_on_demand: the searched interval
  moon?: 'on_demand'             // R7: Moon is not persisted by default; an on-demand
                                // search derives episodes live AND returns/derives the
                                // moon_on_demand coverage record for the interval
  include_context?: boolean      // default false: context layer omitted unless asked
  page?: { limit: number; cursor?: string }  // cursor = (t_exact, contact_id)
}
```

## 3. Response shape (density-layered, hardFloor on confirmed)

```ts
interface ContactLedgerResult {
  status: 'ok' | 'unpublished' | 'not_computed'
  generation: string | null
  manifest: { manifest_id: string; convention_id: string; content_digest: string;
              status: string } | null        // null for legacy generations
  hard_floor: {
    confirmed: ContactEpisode[]             // completeness_state in the confirmed set
                                             // AND target_resolution_state='resolved'.
                                             // NEVER paged away: a trim that cannot
                                             // preserve the full confirmed floor returns
                                             // status='not_computed' + floor_overflow:true
                                             // instead of truncating (hardFloor semantics,
                                             // cf. registry_data.ts hard_floor:true usage)
    count: number                           // true count, independent of page
  }
  context_layer?: {                          // present iff include_context
    catalog_only: ContactEpisode[]          // unqualified / unavailable / unexplored
    unqualified_count: number
    note: string                             // "catalog-only rows are structural context,
                                            //  not timing claims" (§N.6 wording)
  }
  coverage: {
    partitions: CoveragePartition[]          // kala_gochara_coverage rows for
                                            // (chart, generation, requested partitions)
    searched_horizon: string | null          // moon_on_demand: the interval ACTUALLY
                                            // searched (requested vs completed — H-3),
                                            // so L3-Q08 is answerable for Moon classes
    unavailable_inputs: Record<string, unknown>
  }
  page: { returned: number; next_cursor: string | null; confirmed_returned: number }
}

interface ContactEpisode {                   // one kala_gochara_contacts row, served shape
  contact_id: string
  independence_group: string
  body: string; relation: string; aspect_deg: number | null
  target_type: string; target_ref: string; target_resolution_state: string
  t_in: string; t_exact: string; t_out: string
  branch: string; orb_max_deg: number; completeness_state: string
  epistemic_class: string; operator_role: string; claim_grain: string
  comparable_with: string                    // WP1 §6 enum, quoted verbatim
  convention_id: string; classical_citation: string | null; uncited_extension: boolean
  truncated_at_horizon: 'start' | 'end' | null
}
```

Layering rules (normative):

1. `hard_floor.confirmed` and `context_layer.catalog_only` are **disjoint by
   construction** — the query filters, the caller never re-separates. Serving them
   interleaved is a defect, not a style choice.
2. `hard_floor` is trim-proof: budget pressure trims `context_layer` and the page
   size, never the confirmed floor. If the confirmed set exceeds the transport budget,
   return `not_computed` with `floor_overflow` — an honest refusal, not a silent tail
   cut (the H-5/§N.6 discipline: trim at serve time, never truncate as absence).
3. `coverage.searched_horizon` is exposed per request, and a `moon_on_demand`
   partition's `requested_horizon`/`completed_horizon` are quoted exactly (H-3) — a
   Moon search that completed less than requested carries `unsearched_reason`.
4. `status='unpublished'` is served as a full coverage object (empty partitions +
   manifest null + note), never as an error and never as `v1`.

## 4. Plumbing the owner must also handle

- **Whitelist:** when this capability reads via `/api/mcp/db/query`, add
  `kala_gochara_contacts` to `ALLOWED_TABLES` (`route.ts:41`) with a dated read-only
  comment — P-1's packet adds only coverage + publication.
- **Index reliance:** the covering indexes are specified in WP1_CONTRACTS §3.1
  (`idx_kgc_serve` etc.); the capability's query shapes should use (chart_id,
  generation, body, t_exact) prefix order so WP6's latency measurement covers them.

## 5. Acceptance test

Fixture (disposable DB): contacts in three completeness states + one `moon_on_demand`
coverage row whose `completed_horizon ⊊ requested_horizon`. Assert: layers disjoint;
`hard_floor.count` correct under a page size smaller than the confirmed set (expect
`not_computed` + `floor_overflow`, never a truncated confirmed list); `searched_horizon`
equals the requested Moon interval with `unsearched_reason` present; chart with no
authority row returns `status='unpublished'` with a full coverage object.

## 6. What this packet does NOT do

- It does not create the tables (WP6 owns the relations) and does not write any row.
- It does not define the write/build path, the projection, or the windows shape.
- It does not change `fetchGocharaSweep` (P-2) or the gochara serving tools (P-1).
- It does not serve a confidence scalar; density is expressed as typed layers and
  counts.
