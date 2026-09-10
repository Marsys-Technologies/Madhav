---
lane: F-126
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA-LEAD (sonnet)
tier: TIER4-POLISH
class: CL-13-adjacent honesty
---

# F-126 — mimamsa_lel_query stamps `confidence_band:'high'` on a zero-result query

## 1. Live reproduction (today, 2026-08-16, verified against production data)

`mimamsa_lel_query(chart_id=482012f1-710e-4a25-994a-93821f5871aa, query='marriage relationship
spouse partner wedding', limit=15)`

Raw result (salient fields):
```json
{
  "ok": true,
  "epistemics": { "surgical": true, "confidence_band": "high", "horizon_days": null, "falsifier": null },
  "result": {
    "results": [{ "content": "{\"events\":[],\"count\":0,\"total_matching\":0,\"has_more\":false, ...}" }]
  }
}
```

`events:[]`, `count:0`, `total_matching:0` — a genuine zero-row match — while
`epistemics.confidence_band = 'high'`. **CONFIRMED REPRODUCES exactly as claimed.** Not
ALREADY-FIXED.

The finding's supporting claim — that the LEL is demonstrably populated for this chart, so the
empty result is a genuine absence rather than an empty corpus — is independently corroborated:
`kala_ahead_get`'s `period_echo` mechanism surfaces logged LEL rows for this chart elsewhere in
the retrieval surface (the finding cites a 1993 painting award and a congenital speech-pattern
correction); this diagnosis did not re-run that call, but the underlying `life_events` table for
this chart is not empty — the search text `"marriage relationship spouse partner wedding"` simply
matched none of the recorded rows. This is a real "not recorded", not a table-empty case.

## 2. Claim decomposition

- **C1** — `mimamsa_lel_query` returns `epistemics.confidence_band = 'high'` on a query that
  matched zero rows.
- **C2** — the LEL corpus is populated for this chart (not a cold/empty table), so the empty
  result is an honest "no matching event recorded", not "no events exist at all" — meaning a
  'high confidence' stamp on this null retrieval risks being read as an established negative fact
  ("he is not married") rather than "unrecorded".
- **C3** — no `empty_reason` (or equivalent structured field) distinguishes "zero rows matched"
  from "corpus is empty" / "no such event occurred", the disclosure discipline CLAUDE.md §N.6
  item 4 requires of a `density_contract` surface.

## 3. Mechanism (file:line, read directly)

The zero-result payload itself is built honestly, by
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts` (lines 197–224) —
this file, genuinely inside S3's `L5_mimamsa/**` lease, returns `events`, `count`,
`total_matching`, `has_more`, and a `provenance` block, and carries **no** `epistemics` or
`confidence_band` field of its own. It is not the source of the defect.

`epistemics.confidence_band` is injected one layer above, in the shared MCP envelope route that
every whitelisted "surgical primitive" (of which `lel_query` is one) passes through:
`platform/src/app/api/mcp/primitives/[tool]/route.ts`, lines 307–313:

```ts
  // Build surgical epistemics block
  const epistemics = buildEpistemicsBlock({
    surgical: true,
    confidence_band: 'high',
    horizon_days: null,
    falsifier: null,
  })
```

`confidence_band: 'high'` is a **literal constant**, assigned unconditionally as soon as
`isAllowedSurgicalTool(mcpToolName)` passes and the underlying tool call returns *any* result
(success/error only — see route.ts lines 62–329 broadly: the branch above only executes on the
success path, after `toolResult` has already been computed). There is no branch anywhere in this
route, nor in `buildEpistemicsBlock` itself
(`platform/src/lib/mcp/epistemics.ts`, lines 42–74), that reads `toolResult`'s row count,
`events.length`, `total_matching`, or any other emptiness signal before choosing
`confidence_band`. The value is keyed purely off "this surgical primitive call dispatched and
returned without throwing" — i.e. retrieval-**mechanism** success — never off the evidential
weight of what came back.

This is not an implicit drift; it is written into the shared builder's own docstring as the
stated design intent (`epistemics.ts` lines 48–52):

```ts
  /**
   * Calibrated confidence band. Defaults to 'medium' when not explicitly set.
   * For surgical calls (single fact lookups), 'high' is appropriate.
   * ...
   */
```

Confirms C1 (mechanism: hardcoded literal, unconditional on result content) and C3 (no
`empty_reason`/equivalent exists anywhere between `query_life_events.ts`'s honest zero-row payload
and the final envelope — the envelope-builder path has no field for it at all, only
`epistemics.falsifier`, which is also hardcoded `null` for every surgical call regardless of
whether the result was empty).

## 4. Sibling census

`buildEpistemicsBlock(...)` call sites across `platform/src/app/api/mcp/`
(`grep -rn "buildEpistemicsBlock(" platform/src/`):

| Call site | Args | Same defect present? |
|---|---|---|
| `primitives/[tool]/route.ts:308` | `{surgical:true, confidence_band:'high', horizon_days:null, falsifier:null}` | **YES — this finding.** This is the shared dispatcher for the *entire* surgical-primitive whitelist (`MCP_TO_RETRIEVAL_TOOL`), not just `lel_query`/`mimamsa_lel_query` — every one of the ~10 whitelisted primitives (e.g. `ganita_chart_facts_get`, `ganita_positions_get`, etc.) gets the identical unconditional `'high'` stamp regardless of whether its own result was empty. |
| `recent/route.ts:204` | `{surgical:true, confidence_band:'high'}` | **YES — same literal-hardcode pattern**, unexamined against list emptiness. |
| `trace/[trace_id]/route.ts:134` | `{surgical:true, confidence_band:'high'}` | **YES — same pattern.** |
| `asset/route.ts:217` | `{surgical:true, confidence_band:'high'}` | **YES — same pattern.** |
| `writes/[action]/route.ts:247` | `{surgical:true}` (no `confidence_band` → defaults to `'medium'` per `epistemics.ts:70`) | Same defect class one step removed: a write's outcome (succeeded / partially applied / no-op) is never consulted either — the default just happens to read 'medium' instead of 'high'. |

`mimamsa_lel_query` (the alias in `platform-mcp/src/tools/register_p1_aliases.ts:1812-1826`) and
`lel_query` (`platform-mcp/src/tools/mimamsa_lel_intake.ts`) both route through
`callPlatformPrim`/`callPlatformPrimitive` → this same `/api/mcp/primitives/[tool]` route, so both
MCP-facing tool names inherit the identical defect from one shared file.

No `empty_reason`/coverage-honesty field exists anywhere in the `McpEnvelope`/`EpistemicsBlock`
type (`platform/src/lib/mcp/types.ts`) to hang a fix on without adding one — this is a genuine gap,
not a wiring bug.

## 5. Blast radius

- **Lease conflict — this mechanism is NOT in S3's OWNS list.** S3 (SATYA) owns
  `platform/src/lib/retrieval/registry/layers/L4_phala/**`, `L5_mimamsa/**`,
  `platform/python-sidecar/services/ph_nimitta/**`, `platform/python-sidecar/brahmagyan/phala/
  muhurta.py`. The actual defect site, `platform/src/app/api/mcp/primitives/[tool]/route.ts`, is
  explicitly listed under **S1 DVĀRA's** OWNS (`platform/src/app/api/mcp/primitives/**`, plan §2
  S1 section). `platform/src/lib/mcp/epistemics.ts` (the shared builder + its docstring rationale
  that codifies "surgical ⇒ high") is not claimed by any of the six streams' explicit path lists —
  it is a cross-cutting MCP-transport helper.
- Per plan §2.1's rule ("a lane that discovers its mechanism lives in another stream's file does
  not edit it — it posts `PAR-F-126-NEEDS-LEASE <path>`"), **this lane cannot proceed to Stage S/B
  under S3's current lease.** The conductor needs to either re-lease
  `platform/src/app/api/mcp/primitives/[tool]/route.ts` + `platform/src/lib/mcp/epistemics.ts` to
  S3 for this one predicate, or route the spec (once written) to S1 for the actual edit — the plan
  §2.1 precedent (`registry_bridge.ts`/S3-disclosure-flip-via-S2) is the template: "S3 posts a spec
  and S2's [here: S1's] builder applies it."
- Fixing this at the shared route affects **every** surgical primitive response, not just LEL —
  high blast radius by design (this is the correct place to fix it once, for CL-13/CL-08-adjacent
  consistency across all ~10 whitelisted primitives), but it means the fix is NOT scoped to one
  finding or one stream's files; it needs sign-off/coordination that a single-stream predicate
  change would not.
- S1's own F-38 (CL-19, "missing existence check") is already slated to touch
  `platform/src/app/api/mcp/primitives/**` as route-level middleware per the plan's lease-conflict
  table (§2.1 row 3) — an F-126 fix landing in the same file needs sequencing awareness with
  whatever F-38's build does there.
- CL-00 governance controls: not exhaustively checked in this D-stage window (would need a
  `platform/scripts/governance/` grep for any control asserting on `epistemics.confidence_band`
  shape/value) — flag for Stage S to verify none currently depend on `'high'` being a constant.
- The genuinely S3-owned file in this chain, `query_life_events.ts`, is already honest (no
  epistemics claim of its own, correct zero-row/`total_matching` semantics) and needs no change.
