---
artifact: DIAGNOSIS_F-26
stream: S5 · MŪLA
lane: F-26 (CL-03 no-op params, sibling of F-10 exemplar)
stage: D (DIAGNOSE)
status: CONFIRMED-LIVE — NOT FIXED
owns_conflict: PAR-F-26-NEEDS-LEASE (fix point is L3_kala, not in S5's OWNS list)
updated: 2026-08-16
---

# F-26 DIAGNOSIS — `kala_life_arc_get` `include_lel_events` no-op

## 1. Live reproduction

Called `mcp__marsys-jis-direct__kala_life_arc_get` with
`{chart_id: '482012f1-710e-4a25-994a-93821f5871aa', include_lel_events: true}`.

Result: 50 `parvas[]` rows returned (native's real chart, 1984–2060+ span). Every parva
object was inspected; the field set on each is exactly: `id, parva_index, dasha_planet,
dominant_signal_class, start_year, end_year, parva_quality, theme_keywords,
high_convergence_count, avg_effective_score, narrative, source_citation, computed_at`.

**No `lel_events` field is present on any parva**, despite `include_lel_events:true` being
passed. `grounding.fact_ids` in the response envelope is also `[]` — consistent with no LEL
join occurring anywhere in the request path. Raw JSON saved to
`00_ARCHITECTURE/briefs/parisesa/lanes/F-26/repro_raw.json` (one full parva object preserved
verbatim + a note confirming the field-absence check ran across all 50).

**Verdict: CONFIRMED-LIVE, not already-fixed.** Proceeding to full diagnosis.

## 2. Claim decomposition

| # | Claim | Verified |
|---|---|---|
| (a) | `include_lel_events` param exists on the tool and defaults to `true` | **TRUE** — declared in `platform-mcp/src/tools/register_p1_synthesis.ts:678-679` as `z.boolean().optional()`, and the call site at line 692 computes `include_lel_events !== false` (i.e. undefined → true), matching the MCP tool schema I pulled live (`"description":"Include Life Event Log matches for each Parva (default: true)."`). |
| (b) | It's never read in code | **TRUE** — see §3. The underlying capability handler (`query_life_arc.ts`) destructures `mahadasha_lord, quality_label, domain, date_from, date_to, top_k, offset` from `args` (lines 99-105) and never touches `args['include_lel_events']`. It isn't even declared in the capability's own `input_schema` (lines 45-81). |
| (c) | The SQL never joins any LEL table | **TRUE** — the full SQL (now lines 147-177, unchanged from the finding's cited range) selects only from `kala_jivana_parva` (CTEs `leveled`/`deduped`), zero LEL reference anywhere in the query text. `provenance.tables` in the live response confirms: `["kala_jivana_parva"]`. |
| (d) | The capability descriptor self-declares `lel_capable:false` | **TRUE** — `query_life_arc.ts:39`: `lel_capable: false,` inside `queryLifeArcCapability`. The gap is internally self-documented, not merely absent. |

## 3. Mechanism, file:line, current code

**Descriptor self-declaration** — `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts:39`:
```ts
lel_capable: false,
```

**Handler never reads the param** — `query_life_arc.ts:93-105` (args destructuring; note
`include_lel_events` is absent from this list entirely):
```ts
async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    ...
    const mahadasha_lord = args['mahadasha_lord'] as string | undefined
    const quality_label  = args['quality_label'] as string | undefined
    const domain         = args['domain'] as string | undefined
    const date_from      = args['date_from'] as string | undefined
    const date_to        = args['date_to'] as string | undefined
    const top_k          = Math.min(Number(args['top_k'] ?? 739), 739)
    const offset         = Math.max(Number(args['offset'] ?? 0), 0)
```

**SQL never joins LEL** — `query_life_arc.ts:147-177` (`sql` template), `FROM` clauses only
reference `kala_jivana_parva` (CTE `leveled`) and the deduped CTE built from it; no
`LEFT JOIN`/`INNER JOIN` to any `life_event_log`/`lel_*` table exists anywhere in the file.

Lines have **not** drifted from the finding's cited 147-177 range — matches exactly.

**Corroborating internal admission (not part of the original finding, found during this
diagnosis):** `platform-mcp/src/tools/kala_views/story.ts:59-61` already documents this exact
defect in its own header comment, independently of this audit:
> "`query_life_arc.ts`'s `include_lel_events` param remains a documented no-op (verified: its
> SQL never joins an LEL table despite the param name) — this facade does NOT route through
> it."
and at `story.ts:700`, the STORY facade explicitly passes `include_lel_events: false` with an
inline comment `// honestly not consumed downstream (no-op upstream — see file header)` —
i.e. a sibling caller in the same codebase has already worked around this exact gap rather
than fix it, confirming the defect is known and live, not hypothetical.

## 4. Sibling census

**`grep -rn "lel_capable"` across `platform/src`:** ~190 hits total (declarations + tests).
Restricting to capability descriptors that self-declare `lel_capable: false` while their
*name* or *description* references LEL/life-events (the "advertised but self-declared
unsupported" pattern the finding exhibits) — none found beyond `query_life_arc.ts` itself.
Every other `lel_capable: false` capability in the corpus is either (i) a tool with no
LEL-adjacent param at all (the overwhelming majority — L0/L1/most L2/L3/L4 query files), or
(ii) explicitly and correctly declared false with no advertised LEL param (e.g.
`traverse_chart_graph.ts` — test asserts `false` deliberately, "no LEL signals in CGM graph
layer"). `lel_capable: true` capabilities (`query_signals.ts`, `query_ucd.ts`,
`lel_intake_checklist.ts`, `prediction_lifecycle_sweep.ts`, `query_insights.ts`,
`query_life_events.ts`, `query_mechanism_retrodiction.ts`) are out of scope — they claim
capability, this finding is about the false/no-op mismatch.

**`grep -rn "include_lel_events"` across the whole repo (not just L3_kala):** exactly 4 real
sites, all already inspected above:
1. `platform-mcp/src/tools/kala_views/ahead.ts:826` — calls `query_life_arc` with
   `include_lel_events: false` explicitly (never requests it — consistent with the caller
   already knowing it's a no-op, though no comment here explains why).
2. `platform-mcp/src/tools/kala_views/story.ts:59` (doc comment) / `:700` (call site,
   `include_lel_events: false` with explicit no-op comment).
3. `platform-mcp/src/tools/register_p1_synthesis.ts:678,683,692` — the ONE call site that
   actually forwards the user-supplied value (`include_lel_events !== false`) into the
   broken capability, i.e. **this is the sole path where the defect is user-visible** (both
   `ahead.ts` and `story.ts` have self-defensively hardcoded `false` and bypassed it).

**Sibling count: 0 other capabilities exhibit this exact defect pattern** (advertised
LEL-linking param name at the MCP-tool layer, forwarded to a capability whose own descriptor
says `lel_capable:false` and whose handler silently drops the param). F-26 is a singleton
within CL-03's no-op-params class for the LEL-specific variant, though every other file:line
in `LEDGER_S5.md`'s CL-03 row (F-03, F-06, F-08, F-10, F-27, F-133) is a same-class defect
on a *different* parameter — not re-litigated here, out of this lane's scope.

## 5. Blast radius / ownership determination

`00_ARCHITECTURE/briefs/parisesa/LEDGER_S5.md` **Owns** line (verbatim):
> `platform-mcp/src/tools/register_p1_aliases.ts` … `platform-mcp/src/tools/
> register_p1_synthesis.ts` … capability SQL under `layers/L0_*`, `L1_ganita/**`,
> `L2_bodha/**` query files.

**`layers/L3_kala/**` is absent from this list.** The actual fix point —
`platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts` (both the missing
`include_lel_events` schema/handler wiring and, if a real fix is authorized, the LEL join
itself) — sits outside S5's OWNS scope as currently declared. S5 *does* own
`register_p1_synthesis.ts`, which is the call site that forwards the param (line 678-692) —
S5 could patch the symptom there (e.g. stop advertising/forwarding a param the backend
ignores, mirroring `ahead.ts`/`story.ts`'s defensive `false`), but the root cause and the
`lel_capable:false` descriptor correction both live in `L3_kala`, unowned by S5.

**Flag raised: `PAR-F-26-NEEDS-LEASE`** — the stream lead must obtain a lease over
`platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts` from whichever stream
(or the conductor) actually owns `L3_kala` before Stage B/build can touch the root-cause file.
The `register_p1_synthesis.ts` half of any fix is unblocked (S5-owned) and could proceed
independently if the resolution is "stop advertising the no-op param" rather than "wire up
the join."
