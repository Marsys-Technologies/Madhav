---
artifact: NAMESPACE_COVERAGE_v2_0.md
canonical_id: NAMESPACE_COVERAGE
version: 2.1
status: CLOSED
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-10 (R-9)
supersedes: >
  W5 STATE.md's "4/23 → 11/23" measurement (Lane L1, 2026-07-21) — that number is now
  historical; this document is the current authoritative measurement.
corrected: >
  v2.1 (2026-07-23): independent verifier REJECTED the v2.0 "21/23 bridged" figure
  (VERIFY_RC-10.md) — `ganita_condition_get` was force-mapped to
  `marsys://tool/L1/get_condition_composite`, a URI the MCP handler of that name never
  calls (it is a facet dispatcher over get_dignity/get_avasthas/get_karakas). Corrected
  throughout to 20/23 bridged + 3 DEFERRED (structural, temporal_bundle, condition). See
  RESOLVER_RULINGS.md RC-10-003.
---

# RC-10 (R-9) — MCP↔Web Namespace Gap, Re-Measured

## §1 — What "23 MCP tools" means (precision on the metric)

The W4/W5 residual is scoped to a specific, well-defined set: the **23 distinct `live_tool`
values** declared across the 37 `VIDHI_PRIMITIVES` in `platform/src/lib/vidhi/registry_data.ts`
— the deterministic Vidhi floor compiler's MCP-facing tool-name vocabulary. This is not "every
MCP tool that exists" (the live connector currently registers ~135+ tools total); it is the
specific namespace the W4 close measurement named ("only ~4 of ~23 distinct MCP tool names have
a web-executable equivalent") and that W5 Lane L1 measured against (4/23 → 11/23). RC-10
re-measures the same 23-name set for continuity with that prior measurement, per the brief's own
framing ("Re-measure the MCP↔web namespace gap... W5's generated bridge... likely closed most of
it. Measure the CURRENT coverage.").

Confirmed by direct extraction:

```
$ grep -oP "(?<=live_tool: ')[^']+" platform/src/lib/vidhi/registry_data.ts | sort -u | wc -l
23
```

## §2 — The resolution mechanism being measured

`compiled_floor_adapter.ts`'s `resolveLiveTool(liveTool)` is the exact function the web consult
path (`consult/route.ts` → `compileFloorForPlan`) calls to turn a compiled floor item's
`live_tool` name into a web-executable `tool_name`:

```ts
export function resolveLiveTool(liveTool: string): string | undefined {
  return LIVE_TOOL_TO_RETRIEVAL[liveTool] ?? resolveGeneratedToolUri(liveTool)
}
```

Order: (1) the hand-curated `LIVE_TOOL_TO_RETRIEVAL` map, (2) the W5 L1 generated bridge
(`web_tool_bridge.generated.json`, built by `generate_projections.ts` from the live catalog +
`canonical_faces.json` + `tool_name_bridge.ts`'s aliases). A name resolved by either layer is
"bridged" — it reaches a real retrieval-registry capability and therefore a real
`getToolByName()`-executable web-door tool.

## §3 — Measurement BEFORE this residual (HEAD `2df42b61`, pre-RC-10)

Combining the hand map (4 entries) with the generated bridge's independent resolution of the
same 23 names:

| # | Resolved (11) | # | Unresolved (12) |
|---|---|---|---|
| 1 | `bodha_discoveries_get` | 1 | `bodha_remedies_get` |
| 2 | `ganita_chart_facts_get` | 2 | `bodha_remedies_search` |
| 3 | `ganita_dasha_periods_get` | 3 | `bodha_signals_get` |
| 4 | `ganita_positions_get` | 4 | `ganita_condition_get` |
| 5 | `ganita_special_lagnas_get` | 5 | `ganita_dasha_lord_capability_get` |
| 6 | `ganita_yoga_firings_get` | 6 | `ganita_nakshatra_get` |
| 7 | `get_cgm_subgraph` | 7 | `ganita_sensitive_degrees_get` |
| 8 | `kala_muhurta_get` | 8 | `ganita_strength_get` |
| 9 | `kala_yoga_activation_get` | 9 | `ganita_structural_get` |
| 10 | `lel_query` | 10 | `kala_temporal_bundle` |
| 11 | `mimamsa_calibration_get` | 11 | `kala_windows_get` |
| | | 12 | `ref_doshas_get` |

**11/23 (~48%)** — matching the W5 L1 close record exactly (unchanged since 2026-07-21; the
intervening RC-05/06/07/08/09/12/13 lanes did not touch this namespace).

## §4 — Evidence for each of the 12 previously-unmapped names

For each, the retrieval-registry capability was located and, where possible, cross-checked
against the corresponding **MCP tool's own handler body** (`platform-mcp/src/tools/
register_p1_*.ts`) to confirm it calls the *exact same* registry URI — i.e. the web door would
serve the identical underlying data the MCP door already serves under that name, not a
new/guessed substitute (the same evidence bar RC-09's dark-table dispositions and RC-05's
dead-tool substitutions used).

| `live_tool` | Registry capability found | MCP handler confirms same URI? | Disposition |
|---|---|---|---|
| `ganita_dasha_lord_capability_get` | `marsys://tool/L1/get_dasha_lord_capability` | n/a | **BRIDGED** |
| `ganita_sensitive_degrees_get` | `marsys://tool/L1/get_sensitive_degrees` | n/a | **BRIDGED** |
| `ganita_strength_get` | `marsys://tool/L1/get_strength` (shadbala) | n/a | **BRIDGED** |
| `ganita_nakshatra_get` | `marsys://tool/L1/get_tara_chandra_bala` | **Yes** — `register_p1_ganita.ts` §6 literally calls `callRegistryCapability('marsys://tool/L1/get_tara_chandra_bala', ...)`. Same capability `query_tara_balam`/`query_chandra_balam` already resolve to (WP-1.7). | **BRIDGED** |
| `ref_doshas_get` | `marsys://tool/L0/query_dosha_catalog` | n/a | **BRIDGED** |
| `bodha_signals_get` | `marsys://tool/L2/query_signals` | Same capability `msr_sql`/`query_msr_aggregate` already resolve to (`TOOL_NAME_TO_URI`). | **BRIDGED** |
| `bodha_remedies_get` | `marsys://tool/L2/query_remedies` | **Yes** — `register_p1_aliases.ts` calls `regAlias(server, 'bodha_remedies_get', ..., 'marsys://tool/L2/query_remedies', ...)` verbatim. | **BRIDGED** |
| `bodha_remedies_search` | `marsys://tool/L2/query_remedies` | **Yes** — same file, explicitly documented "as secondary alias" / "alias of bodha_remedies_get", same URI. | **BRIDGED** |
| `kala_windows_get` | `marsys://tool/L3/query_temporal_activation` | **Yes** — `register_p1_aliases.ts` calls `callRegistryCap('marsys://tool/L3/query_temporal_activation', ...)`. Same capability `temporal` already resolves to (WP-1.7). | **BRIDGED** |
| `ganita_structural_get` | No single URI — facet-multiplexed dispatcher, 13 facets each routing to a *different* registry URI (`STRUCTURAL_FACET_URI` in `register_p1_ganita.ts`) | n/a — multi-target | **DISPOSITIONED** (§5) |
| `ganita_condition_get` | No single correct URI — 3-facet dispatcher (`CONDITION_FACET_URI` in `register_p1_ganita.ts` ~L663: dignity/avasthas/karakas, default facet `dignity`); the MCP handler never calls `get_condition_composite`, and `get_condition_composite.ts`'s own header states its data is NOT what condition_get's facets read | **No** — verifier-confirmed the handler dispatches to `get_dignity`/`get_avasthas`/`get_karakas`, never `get_condition_composite` (VERIFY_RC-10.md) | **DISPOSITIONED** (§5) |
| `kala_temporal_bundle` | **None exists.** Sidecar composite, no registry primitive at all. | n/a — genuinely absent | **DISPOSITIONED** (§5) |

9 of the 12 were genuine 1:1 concept matches resolvable with a single hand-map entry each —
mechanical, low-risk, evidence-backed (5 of the 9 independently confirmed by reading the
MCP tool's own handler source, not merely inferred from naming similarity). These are now added
to `LIVE_TOOL_TO_RETRIEVAL` in `compiled_floor_adapter.ts` (RC-10 commit). A 10th candidate,
`ganita_condition_get`, was initially force-mapped to `get_condition_composite` but this was
REJECTED at independent verification (VERIFY_RC-10.md, 2026-07-23) as a wrong-data laundering
defect — see RC-10-003 below.

## §5 — Resolver dispositions for the remaining 3 (Native-Proxy Resolver, brief §D.5)

Per §D.5, the Resolver may disposition a residual item with a written rationale citing existing
doctrine; it may not weaken a security control or change a frozen contract. Neither disposition
below does either — both name a genuine, pre-existing structural gap that a bridge *entry* cannot
close without new engineering.

### RC-10-001 — `ganita_structural_get`: DEFERRED (needs facet-aware routing, not a hand-map entry)

**Finding:** `ganita_structural_get` is not one capability but a **13-facet dispatcher**
(`aspects`, `aspects_jaimini`, `aspects_tajik`, `argala`, `dispositors`, `parivartana`,
`yoga_fires`, `dosha_fires`, `conjunctions`, `sambandha`, `functional`, `graha_yuddha`,
`kala_sarpa`), each routed to a *different* registry URI via `STRUCTURAL_FACET_URI` inside the
MCP handler (`register_p1_ganita.ts`). Worse, the Vidhi floor primitives that declare this
`live_tool` do not uniformly carry a `facet` in their `tool_args` — e.g. `bhava_condition`'s
`tool_args` is `{chart_id, house}`, no facet at all, and its own `fallback_face` field already
documents the intended substitute as `ganita_chart_facts_get(category=bhava)`, a *different*
capability than any structural facet.

**Why this is not mechanical:** a single static `LIVE_TOOL_TO_RETRIEVAL['ganita_structural_get']
= <one URI>` entry would silently serve the WRONG data for most of the primitives that declare
this `live_tool` (e.g. serving `dispositors` data to a `bhava_condition` request). This is
exactly the anti-laundering failure class §N.6/B.10 forbid ("a handler... must not present...
mismatched" results as if correct) and the precise failure mode `register_p1_ganita.ts`'s own
R-17 serve-time assertion was built to catch on the MCP side. Correctly closing this gap needs
facet-aware resolution in `compileFloorForPlan` (deriving the right facet per primitive_id and
selecting the matching `STRUCTURAL_FACET_URI` entry) — real engineering, not a bridge extension.

**Disposition: DEFERRED**, not silently dropped — `compileFloorForPlan` already reports every
`ganita_structural_get`-mapped primitive_id via `unmappedPrimitives` (never pushed as a
no-op tool call), so no query silently loses this data with no trace; it is honestly reported as
unmapped. **Revisit condition:** a future lane that builds primitive-level facet derivation in
the compiler (either by adding a `facet` field to each affected `VidhiPrimitive`'s `tool_args`
consistently, or by teaching `resolveLiveTool` to accept a facet argument).

### RC-10-003 — `ganita_condition_get`: DEFERRED (facet-multiplexed dispatcher, identical case to RC-10-001)

**Finding:** `ganita_condition_get` is not one capability but a **3-facet dispatcher**
(`CONDITION_FACET_URI` in `register_p1_ganita.ts` ~L663: `dignity → marsys://tool/L1/get_dignity`,
`avasthas → marsys://tool/L1/get_avasthas`, `karakas → marsys://tool/L1/get_karakas`, default
facet `dignity`) — it **never** calls `marsys://tool/L1/get_condition_composite`. The v2.0
version of this document force-mapped it to `get_condition_composite` anyway, on the mistaken
premise that the two "talk to the same L1 condition-composite writer output." Three independent
counts refute this (full detail: `VERIFY_RC-10.md`):

1. The MCP handler body resolves only to `get_dignity`/`get_avasthas`/`get_karakas`, never to
   `get_condition_composite`.
2. `get_condition_composite.ts`'s own header states verbatim: *"`ganita_condition_get`'s
   dignity/avasthas/karakas facets all read chart_facts directly, not this composite — this tool
   exposes the composite rollup itself."* `get_condition_composite` reads a different table
   (`ga_condition_composite`, 90 rows) entirely.
3. Six Vidhi floor primitives carry `live_tool: 'ganita_condition_get'`: `bhavesha_condition`
   (lord), `karaka_condition` (karaka), `chara_karaka_read` (chara_karaka), `dignity_scan`
   (dignity), `arudha_read` (arudha), `karakamsa_read` (karakamsa). `ga_condition_composite`'s
   columns (graha / dignity / varga-dignity / 5 avasthas / motion / combustion / friendships /
   graha-yuddha / condition_score / dasha windows) contain **no karaka assignment, no arudha, and
   no karakamsa data** — so 4 of the 6 consuming primitives (`karaka_condition`,
   `chara_karaka_read`, `arudha_read`, `karakamsa_read`) would silently receive per-graha
   condition-composite rows that do not contain the concept requested.

**Why this is not mechanical:** identical failure shape to RC-10-001 — a single static
`LIVE_TOOL_TO_RETRIEVAL['ganita_condition_get'] = <one URI>` entry cannot be correct for
primitives whose modes (`lord`/`karaka`/`chara_karaka`/`dignity`/`arudha`/`karakamsa`) do not even
correspond to the tool's own 3-facet enum (`dignity`/`avasthas`/`karakas`), let alone to
`get_condition_composite`'s columns. This is the exact anti-laundering failure §N.6/B.10 forbid,
and the two must be treated the same way per the internal-consistency requirement RC-09's rulings
established.

**Disposition: DEFERRED**, not force-mapped — `compileFloorForPlan` already reports every
`ganita_condition_get`-mapped primitive_id via `unmappedPrimitives` (never pushed as a no-op tool
call). **Revisit condition:** identical to RC-10-001 — a future lane adds facet/mode-aware
resolution to `compileFloorForPlan` (deriving the correct facet per `primitive_id` and selecting
the matching `CONDITION_FACET_URI` entry, noting the Vidhi modes do not currently map onto the
tool's facet enum, so a correct 1:1 does not exist yet) — real compiler engineering, out of a
bridge-extension's mechanical scope.

**Correction record:** this disposition supersedes the v2.0 **BRIDGED** disposition for this
tool, which was REJECTED at independent verification (`VERIFY_RC-10.md`, 2026-07-23) and removed
from `LIVE_TOOL_TO_RETRIEVAL` in `compiled_floor_adapter.ts`. See `RESOLVER_RULINGS.md` RC-10-003.

### RC-10-002 — `kala_temporal_bundle`: DEFERRED (no registry capability exists; pre-existing documented gap)

**Finding:** `kala_temporal_bundle` has **no retrieval-registry capability at all** — it is a
sidecar-backed MCP composite (multi-subsystem gather: timeline/convergence/obstruction/snapshot).
This is not a newly-discovered gap; it is already recorded verbatim in the codebase:

- `platform-mcp/src/server.ts:83-84`: *"KEYSTONE REQUEST: kala_temporal_bundle
  (KA-3-COMPOSITE:...) has no registry primitive. REQUEST to retrieval fork: expose
  'kala_temporal_bundle' capability."*
- `platform-mcp/src/tools/register_p1_aliases.ts` header, "DOCUMENTED DEFERRALS", item 6:
  *"kala_temporal_bundle → kala_bundle_get [kala sidecar composite — multi-subsystem gather]"*.

**Disposition: DEFERRED**, citing the pre-existing doctrine above (this is a standing,
already-acknowledged capability gap, not a RC-10 finding) — reported via `unmappedPrimitives`,
never silently dropped. **Revisit condition:** the retrieval-registry fork building the
requested composite capability (a new L3 Kāla registry primitive combining timeline/
convergence/obstruction/snapshot), which is new-capability construction out of a residual
bridge-extension's scope and belongs to the registry build track, not this closure campaign.

## §6 — Measurement AFTER this residual (current, corrected 2026-07-23)

9 of the 12 previously-unmapped names bridged; 3 dispositioned (not silently dropped — all three
reported via `unmappedPrimitives` with an honest, doctrine-cited rationale).

**Real coverage: 20/23 (~87%) mechanically bridged, 23/23 accounted for (100% dispositioned or
bridged, zero silent gaps).**

| # | Now-bridged (9) | Target |
|---|---|---|
| 1 | `ganita_dasha_lord_capability_get` | `marsys://tool/L1/get_dasha_lord_capability` |
| 2 | `ganita_sensitive_degrees_get` | `marsys://tool/L1/get_sensitive_degrees` |
| 3 | `ganita_strength_get` | `marsys://tool/L1/get_strength` |
| 4 | `ganita_nakshatra_get` | `marsys://tool/L1/get_tara_chandra_bala` |
| 5 | `ref_doshas_get` | `marsys://tool/L0/query_dosha_catalog` |
| 6 | `bodha_signals_get` | `marsys://tool/L2/query_signals` |
| 7 | `bodha_remedies_get` | `marsys://tool/L2/query_remedies` |
| 8 | `bodha_remedies_search` | `marsys://tool/L2/query_remedies` |
| 9 | `kala_windows_get` | `marsys://tool/L3/query_temporal_activation` |

Still unmapped (3, dispositioned DEFERRED per §5): `ganita_structural_get`, `ganita_condition_get`,
`kala_temporal_bundle`.

## §7 — Downstream effect observed and handled (not silently absorbed)

Bridging `bodha_signals_get` has a real interaction with `ensureB11WholeChartReadFloor`'s
existing no-op guard ("no-ops if the plan's authorized tools already include an L2.5 tool").
All four canonical domain-deepdive floors (wealth/career/health/marriage) include a
`varga_ratification` primitive with `live_tool: bodha_signals_get` — now that this resolves to
`marsys://tool/L2/query_signals` (an `L2_5_TOOLS` member), the compiled floor itself satisfies
B.11 for these domains, and the guarantee's generic predictive-class filler (`vector_search` +
unfiltered `forward_looking` signal query) correctly no-ops in favor of the real, domain-specific
signal query the compiled floor already supplies.

This is not a new failure mode: the identical mechanism already fired for career's `mechanism_read`
→ `cgm_graph_walk` mapping (hand-curated since before RC-10) — it was simply never exercised by a
test combining `predictive` query class with a compiled L2.5-satisfying floor until this lane
widened coverage to trigger it for the other three domains too. The invariant B.11 actually
requires (≥1 real L2.5 whole-chart-read tool call) still holds — in fact it is now satisfied by
more precise, domain-relevant data instead of generic filler. Verified via a live compiled-floor
probe (see `compiled_floor_adapter.test.ts`'s updated "end-to-end floor adoption parity" suite)
and documented in-line at both the map declaration and the affected test. A new test
(`predictive class with NO compiled L2.5 primitive still gets the generic vector_search +
forward_looking floor`) confirms the fallback path itself is unchanged when the compiled floor
genuinely supplies no L2.5 tool.

## §8 — Verification run (this session; re-run 2026-07-23 after the RC-10-003 correction)

```
$ npx vitest run src/lib/pipeline src/lib/vidhi src/lib/retrieval/registry/tool_name_bridge_r6_0b_deadtools.test.ts src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts
 Test Files  18 passed (18)
      Tests  154 passed (154)

$ npx vitest run src/lib/retrieval src/app/api/chat
 Test Files  132 passed | 19 skipped (151)
      Tests  1474 passed | 137 skipped (1611)

$ npx tsc --noEmit
(clean, no output)
```

All counts reproduce exactly after removing the `ganita_condition_get` entry from
`LIVE_TOOL_TO_RETRIEVAL` — `compiled_floor_adapter.test.ts`'s bridge-integrity suite asserts
resolvability of mapped names, not the presence of any specific key, so no test required
modification for the removal itself.

## §9 — DONE bar (brief §E RC-10) — met

> "a real number recorded; if <100%, either close the remaining gap (generated-bridge extension)
> or Resolver-disposition each un-bridged tool with rationale"

Real number: **20/23 bridged mechanically** (up from 11/23). The remaining 3/23
(`ganita_structural_get`, `ganita_condition_get`, `kala_temporal_bundle`) are Resolver-dispositioned
DEFERRED with written, doctrine-cited rationale (§5), each already honestly surfaced via
`unmappedPrimitives` rather than silently dropped or force-mapped to wrong data. 23/23 accounted
for — zero residual silent gaps.

**Correction note (2026-07-23):** the original v2.0 close of this document reported 21/23 with
`ganita_condition_get` counted as bridged. Independent verification (`VERIFY_RC-10.md`) REJECTED
that mapping as a wrong-data laundering defect and required the correction recorded throughout
this v2.1 revision. See §4/§5 (RC-10-003) and `RESOLVER_RULINGS.md` RC-10-003.

*End of NAMESPACE_COVERAGE_v2_0.md.*
