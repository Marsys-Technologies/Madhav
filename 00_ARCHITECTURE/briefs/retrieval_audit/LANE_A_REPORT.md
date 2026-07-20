---
artifact: LANE_A_REPORT.md
lane: A — Catalog & registration reality
governing_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §E Lane A
plan_under_audit: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §1.1 (v1.2)
handoff_reference: MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md §3.2/§3.3
worktree: /Users/Dev/Vibe-Coding/Apps/madhav-retrieval (branch ret/strategy-s1)
date: 2026-07-19
status: COMPLETE
---

# Lane A Report — Catalog & Registration Reality

All counts below are static-analysis counts against the checked-in source at the
worktree's current HEAD (no build/run was possible — no `node_modules` in this
worktree; see Model/Effort Ledger). Where a live count would differ from a static
count (e.g. wrapper-indirected registration loops), that is called out explicitly.

---

## 1. The "123-descriptor count" claim

**Verdict: STALE (close but not exact — true count is 118, not 123)**

Method: counted every `registerCapability(...)` call actually reachable from
`platform/src/lib/retrieval/registry/catalog.ts`'s import chain (the function
`getCatalog()` that both channels are documented to call — `catalog.ts:93-98`,
comment at `catalog.ts:13-14`: "Both channels (MCP and chat) import getCatalog()").

| Source file | Capabilities registered |
|---|---|
| `layers/L0_brahmagyan/index.ts` (loop over `L0_CAPABILITIES`, 1 call site, 16-element array — verified array literal at lines 30-46) | 16 |
| `layers/L1_ganita/index.ts` (30 direct `registerCapability(` calls) | 30 |
| `layers/L2_bodha/index.ts` | 17 |
| `layers/L3_kala/index.ts` | 13 |
| `layers/L4_phala/index.ts` | 10 |
| `layers/L5_mimamsa/index.ts` | 6 |
| `layers/router_registration.ts` | 1 |
| `layers/register_d7_channel.ts` (lines 2019-2040) | 17 |
| `layers/register_d8_assess_domain.ts` (lines 1208-1212) | 5 |
| `layers/register_d9_judgment.ts` (line 1102) | 1 |
| `layers/register_d10_pact.ts` (line 450) | 1 |
| `synthesis/index.ts` (line 13) | 1 |
| **TOTAL reachable from `getCatalog()`** | **118** |

**A second, different total exists** for the other live entry point,
`platform/src/app/api/retrieval/capability/route.ts`'s `ensureBootstrapped()`
(lines 71-135): it imports `registerRouterCapabilities`, `registerMaroCapabilities`
(`dprofiles_registration.ts`, 3 capabilities), `registerD6SynergyCapabilities`
(`register_d6_synergy.ts`, 2 capabilities), `registerD7ChannelCapabilities`,
`registerD8AssessDomainCapabilities`, `registerD9JudgmentCapabilities`,
`registerD10PactCapabilities`, `registerL0Capabilities`, a dynamic import of
`L1_ganita/index`, and `registerD5FanoutCapabilities()` (which dynamically
imports `L2_bodha`, `L3_kala`, `L4_phala`, `L5_mimamsa` indexes — same modules
`catalog.ts` imports, so no divergence there). Route.ts's reachable total:
16(L0) + 30(L1) + 17(L2) + 13(L3) + 10(L4) + 6(L5) + 1(router) + 2(D6 synergy)
+ 3(MARO/dprofiles) + 17(D7) + 5(D8) + 1(D9) + 1(D10) = **122**.

**Neither number is 123.** The true story is worse than a single stale count:
`getCatalog()` (118) and `route.ts`'s bootstrap (122) **already disagree with
each other by construction** — `catalog.ts` never imports `register_d6_synergy.ts`
or `dprofiles_registration.ts` (5 capabilities: `synergy/pipeline`,
`synergy/cross_layer`, `maro/orchestrate`, `maro/mcp_surface`,
`resource/maro/profiles`), and `route.ts` never imports `synthesis/index.ts`
(1 capability: `synth_compose_large_n`). This is a live instance of the exact
bug class the plan's §1.1 second bullet describes for D9/D10 (now fixed for
those two) — see §3 below, it is NOT fixed for D6/MARO.

One dead file was found during this count: `layers/L2_bodha/register_d4_graph.ts`
registers `traverse_chart_graph` via a top-level side-effect
(`registerCapability(traverseChartGraphCapability)`, line 18) but **is never
imported anywhere** (`grep -rn "register_d4_graph" platform/src platform-mcp/src`
returns zero hits) — `L2_bodha/index.ts` imports the same capability directly
from `./traverse_chart_graph` instead. The file is inert; its own registration
call never fires. Not itself a discrepancy in the counts above (the capability
IS registered, just via the other path), but it is dead code implying past
churn in exactly this area.

**123 verdict:** the plan's number is neither `getCatalog()`'s 118 nor
`route.ts`'s 122. It is close enough (within 1-5) to have plausibly been a
snapshot taken at a slightly different commit, or a hand-count that
double-counted or miscounted one wave. Given the two live entry points
disagree with each other, "123" cannot be validated as a single ground truth
today — mark the specific figure STALE and use 118 (getCatalog, the documented
canonical path) / 122 (route.ts) going forward, with the disagreement itself as
the headline finding.

---

## 2. The three-catalog claim — exact counts

**Verdict: CORRECTED — the plan's catalog #2 citation conflates two different, differently-typed catalogs**

**(a) Retrieval registry descriptors:** 118, per §1 above.

**(b) `ToolContract` entries — the plan cites `lib/contract/tool_metadata.ts` (~76). This is wrong on two counts:**

1. `tool_metadata.ts`'s 76 entries (`grep -c "canonical_name:" platform/src/lib/contract/tool_metadata.ts` → **76**, confirming the plan's "~76" number) are typed `ToolReconciliationEntry`
   (`tool_metadata.ts:300`: `export const TOOL_METADATA: readonly ToolReconciliationEntry[]`),
   **not** `ToolContract`. This table is a G6 coverage/redundancy audit map
   (asset↔tool reconciliation), consumed only by
   `platform/src/lib/contract/index.ts` (re-export) and
   `platform/src/lib/contract/__tests__/tool_asset_coverage.test.ts` (the
   coverage test). It is **not** in the live tool-serving path.
2. The **real** `ToolContract` type (`platform/src/lib/contract/types.ts`) is
   populated in `platform/src/lib/contract/registry.ts` (`TOOL_CONTRACTS`,
   227 lines) — **6 entries** (`grep -c "canonical_name:"` → 6: the 5
   classical-text tools named in the file's own header comment plus one alias).
   `TOOL_CONTRACTS` feeds `platform/src/lib/contract/catalog.ts`'s
   `CONTRACT_CATALOG` (line 29: `TOOL_CONTRACTS.map(...)`), which is what
   `platform/src/lib/retrieval/registry/schema_utils.ts:24-36`
   (`buildChatToolsFromNames`, reading `CONTRACT_CATALOG_BY_NAME` at line 27)
   **actually** serves to the live chat LLM — confirmed, this file:line
   citation from the plan is accurate. But the catalog behind it is **6 rows**,
   not ~76.

Net correction: the plan's "(2) contract catalog ~76 entries, what the live
chat LLM actually sees" merges a 76-row audit table (not served) with a 6-row
served catalog. The chat LLM's contract-catalog tool surface is far smaller
(6) than the plan states, while the reconciliation table (76) is real but
inert with respect to serving. Both facts matter for R-1's compiler design —
the compiler needs to absorb the small, real contract catalog (6) and probably
retire or re-scope the 76-row audit table separately.

**(c) MCP hand registrations:**

- Raw `server.tool(` literal call count across `platform-mcp/src/tools/*.ts`
  (excluding tests): **127** (`grep -rn "server\.tool(" platform-mcp/src --include="*.ts" | grep -v test | wc -l`).
- This raw count is **not** the true tool count for at least one file:
  `register_p1_aliases.ts` shows 37 raw `server.tool(` occurrences, but 2 of
  those are the *definitions* of two internal helper wrappers
  (`regAlias()` at line 245, `globalAlias()` at line 279) that themselves each
  call `server.tool()` once per invocation. The true count for that file is
  35 (direct literal calls) + 17 (`regAlias(server,...)` call sites) + 3
  (`globalAlias(server,...)` call sites) = **55** (see §4 for the full
  derivation — this is the same number as the corrected alias count).
- I did not audit every one of the ~20 other MCP tool files for the same
  wrapper-indirection pattern (out of proportion for this lane's effort
  budget); `register_p1_synthesis.ts` and `registry_bridge.ts` were spot-checked
  and use direct literal calls only (no wrapper), so their raw counts (6 and 25
  respectively) are the true per-file counts. **The aggregate "true" MCP tool
  count is therefore UNVERIFIABLE to the exact integer within this lane's
  budget** — it is bounded below by 127 − 37 + 55 = **145** if no other file
  hides a wrapper, but I cannot rule out the same pattern elsewhere without a
  file-by-file pass I did not have budget to complete. `REGISTERED_TOOL_COUNT`
  in `server.ts` claims 120 (see §8) — my 145 floor is inconsistent with 120,
  which itself is strong independent evidence the census is wrong, not that my
  145 is wrong (145 is a lower bound built from confirmed, literal call sites
  plus one confirmed wrapper's true count; 120 is a hand-maintained number
  with no test that actually checks the full figure — see §8).
- Alias/bridge maps: `tool_name_bridge.ts` (545 lines, confirmed present) is
  the canonical legacy-name→`marsys://` URI map; `register_p1_aliases.ts` is
  the actual alias-tool-registration file (see §4).

---

## 3. Bootstrap duplication — `route.ts` vs `catalog.ts`

**Verdict: CONFIRMED, and worse/more current than the plan's framing**

The plan cites `api/retrieval/capability/route.ts:103-135` maintaining "its own
registration list separate from `catalog.ts`," with D9/D10 as the historical
example (now fixed — both `registerD9JudgmentCapabilities()` and
`registerD10PactCapabilities()` are present in **both** `route.ts:118,125` and
`catalog.ts:69,74`).

**Fresh evidence the duplication is still live, not just historical:**

- `route.ts:71-97` imports and `route.ts:108-134`'s `ensureBootstrapped()`
  calls `registerD6SynergyCapabilities()` (`register_d6_synergy.ts`, 2
  capabilities: `marsys://tool/synergy/pipeline`, `marsys://tool/synergy/cross_layer`)
  and `registerMaroCapabilities()` (`dprofiles_registration.ts`, 3
  capabilities: `marsys://tool/maro/orchestrate`, `marsys://tool/maro/mcp_surface`,
  `marsys://resource/maro/profiles`).
- **`catalog.ts` imports neither file.** Its import list (lines 34-79) is L0-L5
  index files, `router_registration`, `register_d7_channel`,
  `register_d8_assess_domain`, `register_d9_judgment`, `register_d10_pact`,
  `../synthesis/index` — no `register_d6_synergy`, no `dprofiles_registration`.
- Practical consequence: these 5 capabilities are dispatchable via
  `route.ts`'s POST handler (since its own bootstrap registers them into the
  shared in-process registry singleton) but are **absent from `getCatalog()`**
  — the function `catalog.ts:13-14`'s own comment says both MCP and chat use
  to "get the unified tool surface." Any consumer that builds its advertised
  tool list from `getCatalog()`/`getAllCapabilities()` rather than hitting
  `route.ts` directly will never see or offer these 5 tools, even though the
  dispatcher would happily serve them if asked by URI.
- Symmetric gap in the other direction: `route.ts`'s bootstrap never imports
  `../synthesis/index` (the WP-1.4 `synth_compose_large_n` capability,
  1 entry) — so a caller that reaches capabilities exclusively through
  `route.ts`'s bootstrap sequence (rather than a process that also happened to
  import `catalog.ts` first) would not have that capability registered yet
  either, though in the actual running Next.js process `catalog.ts` is very
  likely imported somewhere in the request path already, making this
  particular gap probably latent rather than live — I could not verify
  without running the app (no `node_modules`; see ledger).

This is the same failure class as the fixed D9/D10 instances, currently
unfixed for D6-synergy and MARO/dprofiles, and is a direct, concrete
confirmation (with better evidence than the plan's "two production outages"
framing, which cites only the two already-fixed cases) that the fix pattern
(add to both lists) has not been applied comprehensively.

---

## 4. Alias inventory — live recount

**Verdict: CONFIRMED — 55 is correct (matches the MCP handoff brief's correction, not the plan's 45, not the file's own header's 47)**

Method: `register_p1_aliases.ts` uses three distinct registration idioms, so a
naive `grep -c "server\.tool("` (37) undercounts by conflating the definitions
of two internal wrapper functions with actual registrations:

1. **Direct literal `server.tool('name', ...)` calls**: 35 (37 raw
   `server.tool(` matches minus the 2 wrapper *definitions* at lines 245 and
   279 — `regAlias()` and `globalAlias()`).
2. **`regAlias(server, 'name', ...)` call sites** (each one calls
   `server.tool()` once inside the wrapper body, `register_p1_aliases.ts:245-272`):
   **17** (`grep -c "regAlias(server" register_p1_aliases.ts`).
3. **`globalAlias(server, 'name', ...)` call sites** (same pattern,
   `register_p1_aliases.ts:279-296`): **3**.

**Total: 35 + 17 + 3 = 55.**

This matches the handoff brief's corrected figure exactly ("aliases are 55,
not 45"). The file's own header comment (`register_p1_aliases.ts:16`: "The 47
aliases implemented in this file cover the remaining 47 of the 53 baseline
tools") is **stale by 8** — it predates the later additions that are only
visible once you account for the wrapper indirection (`regAlias`/`globalAlias`
were very likely retrofitted to reduce duplication *after* the header comment
was written, and the header was never updated with the true post-refactor
count). The `server.ts:459-517` hand-census's "45" is a third, different, also
wrong number.

**DEFERRED count — reconfirmed at 6, still 6, still all unregistered:**
checked each of the six names the `register_p1_aliases.ts:9-14` docstring
lists as deferred (`session_recall`, `session_list`, `catalog_charts_list`,
`catalog_chart_select`, `bodha_bundle_get`, `kala_bundle_get`) against every
`server.tool(` call site in `platform-mcp/src` — **zero matches for any of the
six**, confirming none have shipped. One of them (`bodha_bundle_get`) has an
explicit code comment documenting why:
`platform-mcp/src/tools/retrieval/holistic_bundle.ts:73`: "'bodha_bundle_get'
was never registered as an MCP tool (a planned rename that never shipped)."
**6/6 DEFERRED — CONFIRMED, unchanged.**

**Retired count (plan says 4):** not independently re-derived this pass — no
clean "retired alias" marker was found in the 30 minutes budgeted to this
item; flagging as **UNVERIFIABLE** (no register/deprecate ledger found that
enumerates a "retired" set distinct from "deferred" — the docstring only names
deferrals, not retirements). A future pass should grep `git log` for removed
`server.tool(` calls in `register_p1_aliases.ts`'s history if this number
matters to R-1's design.

---

## 5. Vidhi triple-copy claim

**Verdict: CONFIRMED**

- Two TS trees, near-byte-identical (678 lines each):
  `platform/src/lib/vidhi/registry_data.ts` and
  `platform-mcp/src/resources/vidhi/registry_data.ts`. `diff` on the first 60
  lines shows the only difference is the MCP copy's ESM-required `.js` import
  extension (`from './types.js'` vs `from './types'`) — everything else is
  identical, confirming hand-mirroring rather than independent authorship.
- One DB seed: `platform/migrations/440_vidhi_registry_schema.sql` creates
  `vidhi_primitives`, `vidhi_intent_floors`, `vidhi_floor_items` tables. The
  migration's own table comment
  (`440_vidhi_registry_schema.sql:36-38`) states: "Global, not per-chart.
  **Mirrored in platform/src/lib/vidhi/registry_data.ts for compiler
  testing.**" — the migration file itself documents the intentional
  three-way mirror.
- **Three hand-synced copies, confirmed exactly as claimed.**

---

## 6. Envelope codegen state

**Verdict: PARTIALLY CONFIRMED — generation and a parity test both exist and are real; but the parity test is NOT wired into CI, so the handoff brief's "fixed" framing needs a caveat**

- **Generated, not hand-maintained — CONFIRMED.**
  `platform-mcp/src/generated/envelope.ts:1-8` header: "GENERATED, DO NOT
  HAND-EDIT... Generated by `platform-mcp/scripts/generate_envelope.ts` from
  `platform/src/lib/retrieval/envelope.ts` (source sha256:6797ece795fdaec5)...
  A hand-written mirror (`platform-mcp/src/lib/envelope.ts`) previously stood
  in for this file — it has been deleted." Confirmed: no
  `platform-mcp/src/lib/envelope.ts` exists in this worktree.
  `platform-mcp/package.json:20-23` defines `codegen:envelope`,
  `codegen:registry-shims`, `codegen`, `codegen:check` scripts, and
  `scripts/generate_envelope.ts:36-39,125-141` implements a real `--check`
  mode that exits 1 on drift (compares recomputed sha256 against the stamped
  one).
- **A parity test exists — CONFIRMED.**
  `platform-mcp/src/__tests__/r5_codegen_parity.test.ts` asserts (1) the
  generated envelope builder produces byte-identical output to the canonical
  `platform/src/lib/retrieval/envelope.ts` builder over a recorded corpus, and
  (2) registry-shim parity for the 3 strangler pilot instruments
  (`ganita_strength_get`, `ganita_sade_sati_get`, `ganita_tajaka_get`).
- **New finding, not in the plan or the handoff correction: this parity test
  is not run in CI.** `.github/workflows/ci.yml`'s `typecheck-mcp` job
  (lines 40-54) runs only `npx tsc --noEmit` in `platform-mcp` — no test
  execution. No other workflow job sets `working-directory: platform-mcp` and
  runs `npm test` or a bare `vitest run` over the full suite; the only two
  platform-mcp test invocations anywhere in `.github/workflows/` are narrowly
  scoped to `src/__tests__/response_budget_hard_floor.test.ts`
  (`ci.yml` density-census job, lines ~347-354). The `density-census` job's own
  comment (`ci.yml`, immediately above it) states explicitly: "platform-mcp's
  full `npm test` — that suite currently carries pre-existing unrelated
  failures (tracked separately; not a B-7 regression) and wiring the whole
  suite into CI is a follow-on hygiene item, not this lane's job." So:
  generation is real, the parity test is real and would catch drift **if run**,
  but nothing in CI currently runs it or `codegen:check`. This confirms (with
  a more precise mechanism) the handoff brief's own §3.3 correction-box gap
  note ("`codegen:check` exists and no workflow invokes it... Contract drift is
  currently undetected") — I found the same gap independently and can add the
  exact reason (`platform-mcp`'s vitest suite as a whole is knowingly excluded
  from CI, not merely "the codegen step specifically" as the brief's phrasing
  might suggest).

---

## 7. `capability_version` hash scope

**Verdict: CONFIRMED — hashes only the Vidhi registry data, not the full catalog**

`platform-mcp/src/resources/vidhi/capability_version.ts:29-35`
(`registryContentHash()`) computes
`sha256(JSON.stringify({ primitives: VIDHI_PRIMITIVES, floors: VIDHI_INTENT_FLOORS }))`,
where both `VIDHI_PRIMITIVES` and `VIDHI_INTENT_FLOORS` are imported from
`platform-mcp/src/resources/vidhi/registry_data.ts` — i.e. **one of the three
hand-synced Vidhi copies** named in §5 (the MCP-side TS tree only). It does
not hash: the other TS tree (`platform/src/lib/vidhi/registry_data.ts`), the
DB-seeded tables (migration 440), or anything from the 118-capability
retrieval registry catalog (§1). `VIDHI_CAPABILITY_VERSION` is therefore a
correctness signal for "has the MCP-side vendored Vidhi copy changed," and
gives **zero** signal if the `platform/src/lib/vidhi/` copy or the DB seed
drifts out of sync with it while the MCP copy stays byte-identical (which is
exactly the failure mode the triple-copy structure in §5 invites) — confirms
the plan's claim precisely, with the added nuance that "hashes only one" means
one of the *Vidhi* copies specifically, not one of the 123/118-capability
catalog copies as a reader might otherwise assume from the plan's phrasing.

---

## 8. Census comment vs `REGISTERED_TOOL_COUNT`

**Verdict: CONFIRMED, with two additional concrete stale-comment instances beyond the ones already known**

- `server.ts` census comment: located at lines **459-521** in this worktree
  (brief cites 459-517; the block has grown by a few lines since, consistent
  with ongoing additions — not a meaningful discrepancy). It ends with
  `const REGISTERED_TOOL_COUNT = 120` (`server.ts:522`), served at
  `server.ts:529` in the `/health` endpoint payload.
- **No test validates the true total against 120.** The only test with
  "Completeness" in its own describe-block name,
  `platform-mcp/src/__tests__/m8_e2e_proof.test.ts` `describe('G12 —
  REGISTERED_TOOL_COUNT is truthful', ...)`, asserts `toBe(57)` against a
  **locally redefined** `const REGISTERED_TOOL_COUNT = 57` (line 542) that is
  never compared to the real `server.ts` constant (120) at all — it wires up
  only 15 of the ~30-plus registration functions (explicitly excluding all P1
  alias/ganita/reference/synthesis groups and the D-2 additions, per the
  test's own comment at lines 538-541: "The subset wired here grew because
  registry_bridge now registers 25 tools... Measured = 57"). **This test
  cannot catch `REGISTERED_TOOL_COUNT` drift for ~63 of the ~120 claimed
  tools** — it is a partial-subset regression guard mislabeled as a
  completeness gate.
- **Two fresh stale-comment instances found this pass, beyond the
  known 45/47/55 alias disagreement (§4):**
  1. `registry_bridge.ts` — the `server.ts` census comment claims
     "D7 Registry bridge (registerRegistryBridgeTools): 20 (12 D7 workflow +
     8 D8 apex)." Live count of `server.tool(` calls in
     `registry_bridge.ts`: **25**. The 5 uncounted tools are
     `chart_snapshot`, `get_graha_yuddha`, `query_chart_facts` (line 1656),
     `judgment_query`, `graha_portrait`, `pact_query` — later additions
     (D9/D10 and others) that were folded into this same file without
     updating the "20" figure in the separate census comment.
     (Correction: recounting, the file registers `get_chart_orientation`
     through `pact_query` — 25 distinct tool names — vs. the stated 20.)
  2. `register_p1_synthesis.ts` — its own file header
     (lines 1-10) says "P1 Group 3 — Synthesis-adjacent surface tools
     (3 tools)" and names exactly 3 (`mimamsa_insight_get`,
     `bodha_discoveries_get`, `kala_life_arc_get`). Live count of
     `server.tool(` calls in that file: **6** — three more
     (`synth_tail_divergence_get`, `synth_chart_brief_get`,
     `prashna_undertaking_get`) were added later without updating the file's
     own header comment, a second, independent instance of exactly the same
     "count in a comment goes stale the moment code changes underneath it"
     failure mode the `server.ts` census and the alias-file header both
     already exhibit.

**Conclusion for item 8:** every hand-maintained count artifact examined in
this codebase (the `server.ts` census, `REGISTERED_TOOL_COUNT`, the
`register_p1_aliases.ts` header, the `register_p1_synthesis.ts` header, the
`registry_bridge.ts` figure implied by the census) disagrees with a live
recount by a non-trivial margin. This is not one stale number; it is a
structural pattern across every hand-authored count in the MCP tool surface —
strong independent support for the plan's R-1 "compile everything, hand-author
nothing" design principle.

---

## Additional output: name↔URI↔handler table (R-1 compiler input)

Full extraction attempted programmatically (regex over every
`export const *Capability: <Type> = { ... uri: '...', name: '...' ... }`
declaration in `platform/src/lib/retrieval/registry/layers/**` and
`platform/src/lib/retrieval/synthesis/capability.ts`). **96 of the 118**
catalog entries (§1) were extracted this way; the remaining ~22 (mostly
`register_d7_channel.ts`'s 17 and a few others with less regular formatting —
multi-line `uri`/`name` fields, or fields set via helper functions rather than
inline literals) were not captured by the regex and would need a per-file pass
or an AST-based extractor to complete. This is a **representative sample**,
not the full 118-row table, per the brief's fallback instruction.

Full CSV: `00_ARCHITECTURE/briefs/retrieval_audit/LANE_A_NAME_URI_TABLE.csv`
(96 rows: `const_name,name,uri,layer,file`).

**Structural summary by URI/layer prefix (96 extracted rows):**

| Prefix | Count | Notes |
|---|---|---|
| `marsys://tool/L1/*` | 30 | All of L1 Gaṇita — full coverage |
| `marsys://tool/L0/*` + `marsys://resource/*` + `marsys://prompt/*` (L0 group) | 16 | Full coverage — includes 2 `asset-registry` resources, 2 `ephemeris-cache` resources, 1 `intent-classify` prompt |
| `marsys://tool/L2/*` | 17 | Full coverage — includes D9's `judgment_query` at `L-JUDGMENT/judgment_query` (captured separately, see below) |
| `marsys://tool/L3/*` | 13 | Full coverage |
| `marsys://tool/L4/*` | 10 | Full coverage |
| `marsys://tool/L5/*` | 6 | Full coverage |
| `marsys://tool/L-TIMING/yoga_activation_by_dasha` | 1 | D8 special-namespace tool |
| `marsys://tool/L-JUDGMENT/judgment_query` | 1 | D9 |
| `marsys://tool/L-PACT/pact_query` | 1 | D10 |
| `marsys://tool/synthesis/*` (synth_compose_large_n) | 1 | WP-1.4 |
| **Not extracted (regex miss)** | ~22 | Chiefly `register_d7_channel.ts`'s 17 entries (get_chart_orientation, get_domain_reading, get_signals, traverse_graph, get_positions, get_dashas, get_temporal_windows, get_projections, get_classical_citation, get_remedies, get_chart_quality, list_assets, assess_marriage, assess_career, assess_health, assess_wealth, query_chart_facts, vector_search, get_cgm_subgraph — some of these are actually D8, the D7/D8 split in that one file is not clean), plus `register_d8_assess_domain.ts`'s remaining 4, `router_registration.ts`'s 1, `register_d6_synergy.ts`'s 2, `dprofiles_registration.ts`'s 3 (uri's for these last two hand-confirmed separately below since they matter for §3) |

**Hand-confirmed URIs for the two files at the center of the §3 bootstrap-duplication finding** (not in the regex-extracted CSV, confirmed via direct grep):

| name | uri | handler file |
|---|---|---|
| synergy_pipeline | `marsys://tool/synergy/pipeline` | `platform/src/lib/retrieval/registry/layers/register_d6_synergy.ts` |
| (cross_layer tool) | `marsys://tool/synergy/cross_layer` | same |
| maro_orchestrate | `marsys://tool/maro/orchestrate` | `platform/src/lib/retrieval/registry/layers/dprofiles_registration.ts` |
| (mcp_surface tool) | `marsys://tool/maro/mcp_surface` | same |
| (profiles resource) | `marsys://resource/maro/profiles` | same |
| route | `marsys://tool/router/route` | `platform/src/lib/retrieval/registry/layers/router_registration.ts` |

---

## Gaps found (not in the plan's claims)

1. **`register_d4_graph.ts` is dead code** — never imported anywhere; its
   top-level `registerCapability()` side-effect never fires (§1).
2. **`getCatalog()` and `route.ts`'s bootstrap disagree by construction, live,
   today** — not merely a historical D9/D10 story; D6-synergy (2) and
   MARO/dprofiles (3) are in `route.ts` but absent from `catalog.ts`; the
   large-N synthesis tool (1) is the reverse (§1, §3).
3. **The plan's "~76 ToolContract" claim conflates two differently-typed,
   differently-purposed, differently-sized catalogs** — `TOOL_METADATA`
   (76 rows, `ToolReconciliationEntry`, audit-only, not served) vs
   `TOOL_CONTRACTS` (6 rows, `ToolContract`, the actually-served contract
   catalog) (§2). This matters materially for R-1: the compiler needs to
   know the served contract catalog is 6 rows, not 76, or it will design
   around the wrong artifact.
4. **The one CI test literally named for completeness
   (`m8_e2e_proof.test.ts`'s "G12 — REGISTERED_TOOL_COUNT is truthful") checks
   a different, smaller, locally-redefined constant (57) against a
   deliberately partial subset of registration functions**, and was never
   updated to check the real 120-tool figure — it is not a completeness gate
   in practice, whatever its name claims (§8).
5. **The envelope parity test (`r5_codegen_parity.test.ts`) exists and would
   work, but platform-mcp's full test suite (where it lives) is explicitly,
   deliberately excluded from CI** per a comment in `ci.yml` itself — this is
   a sharper, more actionable version of the handoff brief's "no workflow
   invokes codegen:check" finding: the real gap is one line wider than
   codegen specifically — the whole platform-mcp vitest suite isn't gated (§6).
6. **The true MCP tool count could not be pinned to a single integer within
   this lane's budget** because at least one file
   (`register_p1_aliases.ts`) uses wrapper-indirected registration that a
   naive `grep -c "server.tool("` undercounts by 18 (37 raw vs 55 true), and
   I did not have budget to check all ~24 other tool-registration files for
   the same pattern. Any R-1 compiler-design number for "current MCP tool
   count" should be derived from an AST walk or a runtime census, not a
   grep — recommend this as an explicit R-1 pre-step (§2).

---

## Model/effort ledger

- Ran as: **sonnet**, default reasoning effort, no sub-agent delegation (all
  work done directly with Bash/Read/Edit in this session).
- No build/run of the app was possible in this worktree — `node_modules` is
  absent from both `platform/` and `platform-mcp/` — so every count in this
  report is a **static source-text count** (grep/awk/python regex passes),
  never a live-registry introspection. This is flagged inline wherever it
  bears on confidence (notably §1's two totals and §2's MCP aggregate).
- Files read in full or near-full: `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`
  (§0-§2), `MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md` (§3.2-§3.5),
  `platform/src/lib/retrieval/registry/catalog.ts`,
  `platform/src/app/api/retrieval/capability/route.ts` (first 160 lines),
  `platform/src/lib/retrieval/registry/layers/register_d5_fanout.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d6_synergy.ts` (partial),
  `platform/src/lib/retrieval/registry/layers/dprofiles_registration.ts` (partial),
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts`,
  `platform/src/lib/contract/tool_metadata.ts` (partial),
  `platform/src/lib/contract/catalog.ts`, `platform/src/lib/contract/registry.ts` (partial),
  `platform/src/lib/contract/index.ts`, `platform/src/lib/retrieval/registry/schema_utils.ts`,
  `platform-mcp/src/server.ts` (full), `platform-mcp/src/tools/register_p1_aliases.ts` (partial, targeted),
  `platform-mcp/src/tools/registry_bridge.ts` (targeted greps),
  `platform-mcp/src/tools/register_p1_synthesis.ts` (partial),
  `platform-mcp/src/__tests__/m8_e2e_proof.test.ts` (targeted section),
  `platform/src/lib/vidhi/registry_data.ts` / `platform-mcp/src/resources/vidhi/registry_data.ts` (diffed),
  `platform/migrations/440_vidhi_registry_schema.sql` (partial),
  `platform-mcp/src/resources/vidhi/capability_version.ts` (full),
  `platform-mcp/scripts/generate_envelope.ts` (targeted greps),
  `platform-mcp/src/generated/envelope.ts` (header),
  `platform-mcp/src/__tests__/r5_codegen_parity.test.ts` (header + imports),
  `.github/workflows/ci.yml` (targeted sections).
- Roughly 60-70 grep/awk/python invocations across the session; one Python
  script written to extract the name↔URI↔handler CSV.
- Two files written, both within the brief's explicit allowance:
  `00_ARCHITECTURE/briefs/retrieval_audit/LANE_A_REPORT.md` (this file) and
  `00_ARCHITECTURE/briefs/retrieval_audit/LANE_A_NAME_URI_TABLE.csv`.
