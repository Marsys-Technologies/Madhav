# Domain F — Consumer Surfaces

Method note: budget-capped run (≤35 tool calls). Built directly on `_work/F5.md`'s
23-identity consumer-path trace — not redone here, only corroborated/extended for the
specific consumer-surface files this packet was asked to inventory. Read
`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` lines 441-451 for the U01-U11 definitions
(paraphrased/redacted language in the source — see there for exact wording).

## Consumer surface inventory (file | reads table/capability | LIVE/DARK/DIVERGENT | evidence)

| File | Reads | Status | Evidence |
|---|---|---|---|
| `platform-mcp/src/tools/kala_views/register_all.ts` | registers 9 tools: kala_now_get, kala_ahead_get, kala_upaya_get, kala_ritual_get, kala_priority_get, kala_explain_get, kala_elect_get, kala_story_get, kala_dasha_sandhi_get | **LIVE** | `registerAllKalaViews` imported `registry_bridge.ts:94`, called `registry_bridge.ts:5163` — confirmed wired into the actual server bootstrap function. |
| `platform-mcp/src/tools/kala_views/now.ts` (`kala_now_get`) | `marsys://tool/L3/query_temporal_activation` via local `callRegistryCapability` (`now.ts:128`) | **LIVE** | Same capability URI `kala_windows_get` calls (see below) — confirmed same-code at registry-capability level. |
| `platform-mcp/src/tools/register_p1_aliases.ts` (`kala_windows_get`) | `marsys://tool/L3/query_temporal_activation` via `callRegistryCap` (`:1103`) | **LIVE**, with a disclosed asymmetry | `:1082-1137`. R-18 fix note (param-name mismatch, previously silent-fallback bug, now fixed) and F-176 note: this tool's empty-activation fallback reads UNGATED `kala_bhavishya` rows (same table `kala_projections_get`/`kala_ahead_get` read) and applies the PACT promise-gate ONLY when that fallback actually fires — by design, to avoid paying `pact_query`'s cost on every call. Documented trade-off, not a hidden bug. |
| `platform-mcp/src/tools/register_p1_aliases.ts` (`kala_projections_get`, `:1141-1210`) | `kala_bhavishya` (per in-file comment `:1120`) | **LIVE** | Comment at `:1120` self-confirms `kala_windows_get`'s fallback and `kala_projections_get` read the "SAME table". |
| `platform-mcp/src/tools/register_p1_aliases.ts` (`kala_yoga_activation_get`, `:1403-1423+`) | not independently traced to a table this pass | **LIVE (wiring confirmed), table COULD NOT VERIFY** | Tool registration found at `:1409`; target-table read not opened within budget. |
| `platform-mcp/src/tools/register_p1_synthesis.ts` (`kala_life_arc_get`, `:726-764`) | `marsys://tool/L3/query_life_arc` (per header `:10`) | **LIVE** | `query_life_arc.ts` → `ka_jivana_parva` per F5 (same-code, medium-high confidence). |
| `platform-mcp/src/tools/kala_timeline.ts` (asset id `kala.timeline`, would-be tool `timeline_query`) | claims table `kala_timeline` via `callPlatformPrimitive('kala_timeline', ...)` (`:1-30`) | **DARK — confirmed** | Three independent confirmations: (1) `grep -n registerKalaTimeline` on `platform-mcp/src/server.ts` returns **zero hits** — the file's own docstring claim ("Wiring: registerKalaTimeline(server, getPrincipal) → server.ts") is stale/false, the tool is never registered on the MCP server. (2) Even if it were called, `MCP_TO_RETRIEVAL_TOOL` in `platform/src/lib/retrieval/registry/tool_name_bridge.ts` has no `kala_timeline` entry — the primitives-route whitelist (`platform/src/app/api/mcp/primitives/[tool]/route.ts`) would 400 the call. (3) `grep -rln kala_timeline` over `pipeline/` and `services/` (the writer trees) returns **zero hits** — no `ka_*` writer targets a `kala_timeline` table at all. |
| `platform-mcp/src/tools/retrieval/kala_temporal.ts` (`kala.temporal` composite) | `query_dasha_dossier` → `kala_avadhi`; `query_convergence_windows` → `kala_convergence`; `query_obstruction_periods` → `kala_obstruction`; `query_temporal_view` → `kala_darshana` (per its own header `:1-28`) | **LIVE — and is the file that supersedes kala_timeline.ts** | Header explicitly documents CR-40/T-1 (2026-07-16): this tool previously called 4 sidecar HTTP routes that were **never mounted** (`/kala/timeline` etc., confirmed by the author's own grep of `python-sidecar/main.py`'s router includes), silently degrading to an empty fallback forever. Fixed by repointing to the same registry capabilities the `L3_kala/` query files already serve through. So the asset labeled "KA-3-1 kala.timeline" is genuinely served — but via `kala_avadhi`/`query_dasha_dossier`, **not** via the separate, still-dead `kala_timeline.ts`/`kala_timeline` table pair above. Two files claim the same asset id with two different, non-reconciled table names — one dark, one live. |
| `platform-mcp/src/lib/promise_spine.ts` (`interpretPactJoin`) | pure function over `pact_query` capability output, no DB read itself | **LIVE** | File's own header lists PRODUCTION CALLERS and states it was previously a false claim (`grep -rn interpretPactJoin` found only itself until 2026-08-21) — corrected in place. Confirmed present-day callers: `tools/kala_views/ahead.ts` (via `promise_gate.ts`, `grep` confirmed) and `tools/registry_bridge.ts` (`assess_*` tools). |
| `platform-mcp/src/tools/kala_views/promise_gate.ts` | wraps `interpretPactJoin` for `kala_ahead_get`'s forward projections | **LIVE** | `grep -rln promise_spine` hit on this file; matches `promise_spine.ts`'s own PRODUCTION CALLERS list. |
| `platform-mcp/src/tools/kala_views/{ahead,priority,ritual,story}.ts` | per F5: `ka_kshetra`/`ka_yojaka`/`ka_bhavishya_lekha` family (asset_id co-occurrence, table not independently re-verified this pass) | **LIVE (F5 corroborated)** | See F5.md rows for `ka_kshetra`, `ka_bhavishya_lekha`. Not re-traced here — F5 already did per-file greps. |
| `platform-mcp/src/tools/kala_views/dasha_sandhi.ts` (`kala_dasha_sandhi_get`) | L1 `chart_dashas` via §N.5 JOIN (per `register_all.ts:52-53` docstring) | **LIVE** | Registered at `register_all.ts:64`; not independently re-opened this pass (budget). |

**DIVERGENT carryover from F5 (not re-derived, cited for completeness):** `ka_gochara` writer targets `kala_gochara_windows_v2`, but `register_gochara_windows.ts:573-598`'s `buildSourceCitation()` reads/cites the un-suffixed `kala_gochara_windows`. `ka_tulana`'s consumer wrapper (`call_service_wrappers.ts` `call_priority_ranking`, used by `kala_priority_ranking_get`/`kala_priority_get`) reads `kala_activation` — a table owned by `ka_kalasutra`, not `ka_tulana`. `ka_dasha_kala`'s consumer wrapper (`call_dasha_eligibility`) reads L1 `chart_dashas` directly, bypassing `KaDashaKalaService` entirely. All three affect tools inventoried above (`kala_priority_get`, `kala_priority_ranking_get`, `kala_ahead_get`'s ka_gochara-sourced rows).

## Channel parity trace (≥2 tools)

**Architecture, as found:**
- **Portal Paripraśna** and **managed MCP `prashna_ask`** are confirmed to hit the *identical* engine. `platform-mcp/src/lib/prashna_ask_bridge.ts` (`:1-14`) states explicitly: "The REAL engine invocation (`callPipelinePlanner`, budget arbitration, NO-LEAKAGE enforcement, cost-cap tracking) lives on the `platform` side at `platform/src/app/api/mcp/prashna_ask/route.ts` — investigation ... found `platform-mcp` has no import path to the FROZEN engine." So the managed-MCP `prashna_ask` tool is a thin HTTP bridge to the exact same route the Portal UI calls (`platform/src/app/api/mcp/prashna_ask/route.ts`) — by construction these two channels cannot diverge in logic, only in transport.
- **Raw MCP** (e.g. `kala_windows_get`, `kala_now_get`) is architecturally, and by design, a shortcut around the planner. `platform/src/app/api/mcp/primitives/[tool]/route.ts:1-6` states: "Surgical calls bypass the planner and B.11 floor; they are tagged `surgical: true` in the epistemics block." This is the RS-4 carve-out already recorded in `CLAUDE.md §I` (proportionality carve-out for `depth: retrieval` pinpointed lookups), not an undocumented gap.

**Trace 1 — `kala_windows_get` (raw MCP) vs `prashna_ask` (managed/Portal):**
`kala_windows_get`'s handler (`register_p1_aliases.ts:1081-1139`) calls `callRegistryCap('marsys://tool/L3/query_temporal_activation', ...)` directly — no planner, no floor check, no NO-LEAKAGE pass. `prashna_ask`, by contrast, routes through `callPipelinePlanner` on the `platform` side, which (per the primitives-route docstring) enforces the planner + B.11 floor before any capability is called. **Both ultimately read the same underlying capability/table** (`query_temporal_activation` → `kala_activation`), but raw MCP gets there with none of the planner-level gating prashna_ask applies. This is the documented, intentional shortcut, not a silent divergence — but it means a raw-MCP caller can retrieve L3 Kāla data that a Portal/managed-MCP query on the same chart might floor-gate or trim differently.

**Trace 2 — `kala_now_get` (kala_views, raw MCP tool) vs the same underlying capability via prashna_ask:**
`kala_now_get` (`kala_views/now.ts:128`, header `:10-11`) explicitly documents that it and `kala_bundle_get`'s snapshot half both call `marsys://tool/L3/query_temporal_activation` / `query_temporal_view` — i.e. this tool is deliberately built as a re-presentation of the same raw primitive `kala_windows_get` calls, "on the elevated argument-shaped envelope." Same capability, same bypass-the-planner channel characteristics as Trace 1.

**Parity verdict:** Portal ↔ managed-MCP `prashna_ask` are architecturally identical (same route, confirmed). Raw MCP is a documented, intentional bypass of the planner/floor layer that both other channels enforce — same underlying L3 data/capability is reached, but without the planner-level completeness/leakage/floor guarantees. This matches the RS-4 carve-out CLAUDE.md already records; it is a real difference in guarantees, not a difference in which table gets read.

## U01-U11 testability table

Strategy doc language (`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md:441-451`) is deliberately
paraphrased/abstracted in the source file, not a literal spec — descriptions below are read off
that table's actual wording, mapped to the concrete code found this pass.

| U-id | one-line description (per strategy doc) | testable today Y/N | evidence |
|---|---|---|---|
| U01 | L2→Yojaka/Kshetra binding (producer fields, generations, signed routes) | **Y** | `ka_kshetra`/`ka_yojaka` served via `kala_views/{ahead,priority,ritual,story}.ts` per F5 (same-code, medium confidence) — tools are registered and callable. |
| U02 | Clocks→concordance (simultaneous interval intersection, no date-equality shortcuts) | **Y (tool exists), logic depth COULD NOT VERIFY** | `kala_dasha_sandhi_get` is registered (`register_all.ts:64`) and callable; whether its interval-intersection logic actually avoids the date-equality/union-of-disjoint-systems failure modes the strategy doc warns against was not opened this pass. |
| U03 | Vedha/TRIGGER/Vighnakara→integrators (persist obstruction target/role/interval/source/state) | **Y** | Per F5: `ka_vighnakara` → `query_obstruction_periods.ts` (`FROM kala_obstruction`, high confidence); `ka_vedha_gochara` → `query_vedha_gochara.ts` (`FROM kala_vedha_gochara`, high confidence). Both registered/reachable. |
| U04 | Kalasutra/Tulana→AHEAD/NOW (nearest future recurrence, coverage) | **Y, with a known gap** | `kala_ahead_get`/`kala_now_get` are live and registered. But per F5, `ka_tulana`'s consumer wrapper reads `kala_activation` (owned by `ka_kalasutra`), not any table traceable to `ka_tulana`'s own writer — so the "Tulana" half of this U-item has an open §N.8-flagged gap even though the tool itself is callable. |
| U05 | L3 registry/fallback (preserve filters on fallback, no silent domain substitution) | **Y** | `kala_windows_get`'s fallback behavior is directly inspectable — F-176 comment (`register_p1_aliases.ts:1118-1125`) documents the fallback reads `kala_bhavishya` and is gated only when it actually fires. Testable and its exact behavior is disclosed in-code. |
| U06 | Qualified stages→PACT/promise spine (no categorical denial from partial checks) | **Y** | `promise_spine.ts`'s `interpretPactJoin` has confirmed live callers (`kala_views/ahead.ts` via `promise_gate.ts`; `registry_bridge.ts`'s `assess_*` tools) — both registered, callable tools. |
| U07 | L3→Phala manifestation (separate activity/intensity/valence/priors from calibrated probability) | **N — only a documentation-level pointer found** | `phala_outlook.ts:64` references `kala_muhurta_get` only inside a `recover`/drill-pointer hint string, not as a functional data-fusion call. No actual cross-domain data pull from L3 into a Phala manifestation computation was found within budget. Flagged, not asserted absent — COULD NOT VERIFY beyond this one reference. |
| U08 | L3→Phala cross-domain timing (post-"L2 timing retirement") | **COULD NOT VERIFY** | The strategy doc's own wording implies a dependency (L2 timing) was retired and needs a replacement supply path; no code trace attempted this pass (budget) — flag for a dedicated follow-up. |
| U09 | Historical comparison→prospective firewall (AHEAD echoes stay out of historical rows) | **Y (tool exists), firewall logic COULD NOT VERIFY** | `kala_ahead_get` is live/registered; whether it actually firewalls historical-comparison poisoning as the strategy doc requires was not traced this pass. |
| U10 | L3→claim issuance/L5 (stable temporal IDs reach claim authority) | **COULD NOT VERIFY** | `standing_predictions_read`/`mimamsa_outcome_record` tools exist in the MCP tool surface, but no direct trace was made this pass from an L3 Kāla window/table into a specific claim-issuance write path. |
| U11 | Every producer→capability/inquiry (fields, access path, prerequisites published) | **Y (partial)** | `catalog_assets_list`/`catalog_assets_all` tools exist and are part of the standard MCP surface; whether every one of the 22 active `ka_*` identities has a complete, accurate catalog entry (vs. e.g. the `kala_timeline` dark-asset case found above, which would be exactly the kind of catalog/reality mismatch this U-item exists to prevent) was not exhaustively checked. |

## Verdict: NOT READY

Grounds: two concrete defects found independently of F5's three (which this packet corroborates
rather than re-derives):
1. `kala_timeline.ts` / the `kala_timeline` table is fully DARK on three independent axes
   (never registered on the MCP server; not whitelisted on the primitives route; no writer
   anywhere targets the table) while a *second* file (`kala_temporal.ts`) claims the same asset
   id ("KA-3-1 kala.timeline") and genuinely serves it via a completely different table
   (`kala_avadhi`). Two non-reconciled implementations of the same declared asset is a real
   consumer-surface integrity gap, not a stylistic issue.
2. Channel parity holds for Portal↔managed-MCP (architecturally identical route) but raw MCP is
   a confirmed, intentional bypass of the planner/floor/NO-LEAKAGE layer — acceptable per the
   documented RS-4 carve-out, but combined with finding #1 and F5's three divergences
   (`ka_gochara`, `ka_tulana`, `ka_dasha_kala`), a raw-MCP caller today can retrieve L3 data
   through at least 4 distinct paths where the served table does not match what governance
   artifacts (or the asset's own docstring) claim it should be.
3. Of U01-U11, only 5/11 (U01, U03, U05, U06, and U04-with-caveat) have both a live code path
   *and* enough in-code disclosure to trust what they actually do; 2/11 (U08, U10) could not be
   traced at all this pass; U07 shows only a drill-pointer reference, not a real data fusion.

## Evidence that could have flipped this verdict

- If `registerKalaTimeline` turns out to be called from a bootstrap path other than
  `platform-mcp/src/server.ts` (e.g. a second server entrypoint not searched this pass), the DARK
  classification for `kala_timeline.ts` would need to soften to "redundant-but-live" rather than
  "dead code" — though the missing `MCP_TO_RETRIEVAL_TOOL` whitelist entry and the absent writer
  would still stand as independent defects.
- If U07/U08/U10's cross-layer data fusion is implemented somewhere under `platform/src/lib/`
  outside the `L3_kala/` and `tools/` directories searched this pass (e.g. inside a Phala or
  Mīmāṃsā writer that reads L3 tables directly, not through the MCP tool surface), those three
  U-items could move from "COULD NOT VERIFY" / "N" to "Y" — this pass only searched the
  MCP-tool-facing consumer surfaces named in the task, not every L4/L5 writer.
- If `ka_tulana`'s and `ka_dasha_kala`'s writers turn out to be intentionally-shared/co-writer
  designs (F5's own open question, not resolved here or there), U04's "known gap" caveat would
  soften.
