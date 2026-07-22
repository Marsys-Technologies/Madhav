---
artifact: VERIFY_RC-10.md
residual: RC-10 (R-9) — Re-measure the MCP↔web namespace gap
verifier: independent VERIFIER agent (opus, high effort) — NOT the implementer
branch_verified: res/rc10-namespace-gap @ f8d84fea (base local main @ 132f883b)
date: 2026-07-23
verdict: REJECT
---

# VERIFY RC-10 — MCP↔web namespace-gap re-measure

**VERDICT: REJECT.** Tests pass, scope is clean, and 9 of the 10 new bridge
mappings are genuine 1:1 matches — but one new mapping
(`ganita_condition_get → marsys://tool/L1/get_condition_composite`) is a
wrong-data laundering defect that (a) the codebase's own source documentation
contradicts, (b) violates the anti-laundering doctrine every lane is bound to
(§G → §N.6 / B.10), and (c) directly contradicts the implementer's OWN deferral
standard applied to the structurally identical `ganita_structural_get`. Because
of it, the headline coverage number **21/23 is overstated — the honest figure is
20/23, with 3 DEFERRED (not 2)**.

---

## (a) Tests re-run independently — PASS (reproduced exactly)

Ran in the branch worktree (`node_modules` symlinked from main; vitest 4.1.7):

| Suite | Result | Implementer claim |
|---|---|---|
| `vitest run src/lib/pipeline src/lib/vidhi` | **151 passed** (17 files) | (151 + 3 bridge = 154) ✓ |
| `vitest run tool_name_bridge_r6_0b` | **3 passed** | ✓ |
| `vitest run src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts` | **31 passed** | ✓ |
| `vitest run src/lib/retrieval src/app/api/chat` | **1474 passed, 137 skipped** (132 files) | 1474 / 137 skips ✓ |
| `tsc --noEmit` | **clean (exit 0)** | ✓ |

All test claims reproduce. Tests are NOT the reason for rejection.

## (d) must_not_touch — CLEAN

Diff (`132f883b..f8d84fea`) touches exactly 4 files:
- `00_ARCHITECTURE/briefs/retrieval_residual/NAMESPACE_COVERAGE_v2_0.md` — may_touch ✓
- `00_ARCHITECTURE/briefs/retrieval_residual/RESOLVER_RULINGS.md` — may_touch ✓
- `platform/src/lib/pipeline/compiled_floor_adapter.ts` — may_touch (`platform/**`) ✓
- `platform/src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts` — may_touch ✓

No touch to: FROZEN orchestrator / WriterBase / `ga_*`/`bo_*`/… writer build
logic; `CLAUDECODE_BRIEF.md`; D-4b briefs/branches; chart_facts semantics;
`kala_*`/gochara **serving** semantics. (The `kala_windows_get` bridge entry adds
a web alias in the pipeline adapter; it does not edit the L3 serving primitive.)
No migration. Scope is clean.

## (c) Coverage recomputed independently — reported 21/23 is OVERSTATED (true 20/23)

**Metric confirmed:** 23 distinct `live_tool` values in
`platform/src/lib/vidhi/registry_data.ts` (enumerated independently; count = 23).

**Resolution path:** `resolveLiveTool()` = `LIVE_TOOL_TO_RETRIEVAL[t] ??
resolveGeneratedToolUri(t)`. I computed the union of (i) the hand map's 14 keys
and (ii) the generated bridge's 11 mapped names
(`web_tool_bridge.generated.json` → `GENERATED_NAME_TO_URI`):

- Generated-bridge mapped (11): bodha_discoveries_get, ganita_chart_facts_get,
  ganita_dasha_periods_get, ganita_positions_get, ganita_special_lagnas_get,
  ganita_yoga_firings_get, get_cgm_subgraph, kala_muhurta_get,
  kala_yoga_activation_get, lel_query, mimamsa_calibration_get.
- Hand-map-only additions (10, all in the generated-unmapped set → additive):
  ganita_condition_get, ganita_dasha_lord_capability_get,
  ganita_sensitive_degrees_get, ganita_strength_get, ganita_nakshatra_get,
  ref_doshas_get, bodha_signals_get, bodha_remedies_get, bodha_remedies_search,
  kala_windows_get.

Mechanical union = **21 names resolve; 2 never resolve** (`ganita_structural_get`,
`kala_temporal_bundle`). The 21/23 arithmetic is correct **as raw resolvability**,
and the 11/23 baseline is confirmed. **But one of the 21 resolves to the WRONG
capability (see below), so it is not an honest bridge. Honest coverage = 20/23
bridged + 3 DEFERRED.**

## The defect — `ganita_condition_get → get_condition_composite` launders wrong data

The new hand-map entry claims (code comment + `NAMESPACE_COVERAGE_v2_0.md` line 85)
that every new mapping "calls the exact registry URI on the right via
`callRegistryCapability(...)` … the SAME underlying data the MCP door already
serves under this name." **For `ganita_condition_get` this is false on three
independent counts:**

1. **The MCP door never calls `get_condition_composite`.** The MCP handler
   (`platform-mcp/src/tools/register_p1_ganita.ts` L663) is itself a **facet
   dispatcher** over `CONDITION_FACET_URI = { dignity → marsys://tool/L1/get_dignity,
   avasthas → …/get_avasthas, karakas → …/get_karakas }`, default facet `dignity`.
   It resolves to `get_dignity` / `get_avasthas` / `get_karakas` — **never** to
   `get_condition_composite`.

2. **The codebase's own source documentation contradicts the mapping.**
   `get_condition_composite.ts` header (lines 10–12) states verbatim:
   *"`ganita_condition_get`'s dignity/avasthas/karakas facets all read chart_facts
   directly, not this composite — this tool exposes the composite rollup itself."*
   `get_condition_composite` reads a **different table** (`ga_condition_composite`,
   90 rows), not the chart_facts dignity/avastha/karaka rows the MCP tool serves.

3. **It silently serves wrong data for 4 of 6 consuming primitives.** Six Vidhi
   floor primitives carry `live_tool: 'ganita_condition_get'`
   (`registry_data.ts` L47/59/107/230/350/472): `bhavesha_condition` (lord),
   `karaka_condition` (karaka), `chara_karaka_read` (chara_karaka),
   `dignity_scan` (dignity), `arudha_read` (arudha), `karakamsa_read` (karakamsa).
   The `ga_condition_composite` SELECT columns are graha / dignity / varga-dignity /
   5 avasthas / motion / combustion / friendships / graha-yuddha / condition_score /
   dasha windows — with **no karaka assignment, no arudha, and no karakamsa
   columns**. So `karaka_condition`, `chara_karaka_read`, `arudha_read`, and
   `karakamsa_read` compiled onto the web door would return per-graha
   condition-composite rows that **do not contain the concept the primitive asked
   for** — precisely the "silently serve the WRONG data for some primitives"
   anti-laundering failure §N.6 / B.10 forbid.

**Internal inconsistency:** RC-10-001 correctly DEFERS `ganita_structural_get`
because it is a facet-multiplexed dispatcher whose primitives don't uniformly
carry a facet, so "a single static URI would silently serve the WRONG data."
**`ganita_condition_get` is the identical case** (3-facet dispatcher; consuming
primitives pass modes lord/karaka/chara_karaka/dignity/arudha/karakamsa that do
not even correspond to the tool's facet enum), yet it was force-mapped instead of
deferred. The two must be treated the same way. `RESOLVER_RULINGS.md` disposition
RC-10-001/002 covers only structural + temporal_bundle; condition is undocumented
as a risk and is presented as a clean mechanical bridge.

### What is verified CLEAN (do not re-touch)

The other **9** new mappings are genuine 1:1 — I read each MCP handler body and
confirmed it calls exactly the mapped URI:

| live_tool | mapped URI | MCP handler call site — confirmed |
|---|---|---|
| ganita_strength_get | …/L1/get_strength | register_p1_ganita.ts L440 ✓ |
| ganita_sensitive_degrees_get | …/L1/get_sensitive_degrees | register_p1_aliases.ts L552 (regAlias) ✓ |
| ganita_dasha_lord_capability_get | …/L1/get_dasha_lord_capability | register_p2_dasha_lord.ts L104 ✓ |
| ganita_nakshatra_get | …/L1/get_tara_chandra_bala | register_p1_ganita.ts L747 ✓ |
| ref_doshas_get | …/L0/query_dosha_catalog | register_p1_reference.ts L273 ✓ |
| bodha_signals_get | …/L2/query_signals | register_p1_aliases.ts L370 ✓ |
| bodha_remedies_get | …/L2/query_remedies | register_p1_aliases.ts L774 ✓ |
| bodha_remedies_search | …/L2/query_remedies | register_p1_aliases.ts L785 (documented alias) ✓ |
| kala_windows_get | …/L3/query_temporal_activation | register_p1_aliases.ts L677 ✓ |

The behavior side-effect the implementer flagged (bridging `bodha_signals_get`
makes the four domain-deepdive predictive floors satisfy the B.11 L2.5 invariant
via the compiled `varga_ratification` primitive, so `ensureB11WholeChartReadFloor`
no longer injects the generic `vector_search` filler for those cases) is **real
but defensible** — same no-op path career's `cgm_graph_walk` already used, the
≥1-L2.5-tool invariant still holds, and it is covered by an added regression test
proving the fallback path still fires when no compiled L2.5 primitive exists.
This is not a reason for rejection.

---

## Required changes to reach ACCEPT

1. **Remove the `ganita_condition_get → 'marsys://tool/L1/get_condition_composite'`
   entry from `LIVE_TOOL_TO_RETRIEVAL`** (`compiled_floor_adapter.ts`). It is not a
   mechanical 1:1 bridge; the MCP tool of that name dispatches to
   get_dignity/get_avasthas/get_karakas, never to the composite.
2. **DEFER `ganita_condition_get`** exactly like `ganita_structural_get`: add a
   Resolver ruling (RC-10-003) recording it as a facet-multiplexed dispatcher whose
   consuming primitives target karaka/chara_karaka/arudha/karakamsa concepts absent
   from any single facet URI, honestly reported via `unmappedPrimitives`, with the
   same "needs facet/mode-aware routing in `compileFloorForPlan`" revisit condition.
   (Alternative, if pursued instead of deferral: build facet/mode-aware resolution
   so each primitive maps to its correct facet URI — but note the Vidhi modes do not
   map onto the tool's facet enum, so a correct 1:1 does not currently exist and
   deferral is the honest disposition.)
3. **Correct the headline number to 20/23 mechanically bridged + 3 DEFERRED**
   (structural, temporal_bundle, condition) across
   `NAMESPACE_COVERAGE_v2_0.md` (fix line 85's false "talks to the same L1
   condition-composite writer output" claim and the summary/count lines) and the
   `compiled_floor_adapter.ts` comment block (the "10 … each verified as a genuine
   1:1 concept match … calls the exact registry URI" claim must drop condition).
4. Re-run the compiled_floor_adapter test suite (the current test asserts the map's
   values resolve, which they do — resolvability is not the issue; the removed entry
   simply moves condition to `unmappedPrimitives`, matching structural's existing
   handling).

None of RC-10's other work is in question. Fixing item 1 is a one-line deletion
plus doc/ruling updates; re-verify and this closes.
