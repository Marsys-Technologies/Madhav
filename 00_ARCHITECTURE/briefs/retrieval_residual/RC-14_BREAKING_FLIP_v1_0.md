---
artifact: RC-14_BREAKING_FLIP_v1_0.md
residual_id: RC-14
title: The impl/w5-breaking flip — alias cutover + single-bootstrap default + query_spine_bundle activation
version: 1.0
status: PARTIAL — Pieces 2+3 LANDED & tested; Piece 1 (alias cutover) BLOCKED on a one-line DIRECTION ruling
authored_by: Claude (Opus 4.8), RC-14 execution session
date: 2026-07-23
branch: res/rc14-breaking-flip
governing_brief: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-14
---

# RC-14 — Breaking Flip: execution report

## TL;DR

- **Piece 2 (single-bootstrap default flip) — DONE, tested, tsc-green.** `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` default flipped `false → true`. Registration now routes exclusively through `getCatalog()`. Superset diff re-verified: the catalog path is a strict superset of the legacy hand-list; the ONLY catalog-only additions are the two known/accepted items (`query_spine_bundle` + `synth/compose_large_n`). **No new gap** introduced by the 178 commits.
- **Piece 3 (query_spine_bundle activation) — DONE, tested.** Auto-activates via the Piece-2 flip (registered only via `catalog.ts:87` side-effect import → `registerCapability` at `register_spine_bundle.ts:126`). No new wiring needed. New default-path test proves it is reachable with no env override.
- **notifications/tools/list_changed — INVESTIGATED, remediation specified.** The vidhi capability-version hash keys off `VIDHI_PRIMITIVES`/`VIDHI_INTENT_FLOORS` + `COMPILER_VERSION` only — NOT the MCP tool list. Pieces 2/3 do NOT change the MCP tool list, so no bump is needed for them. A future Piece-1 tool-name removal would NOT reliably auto-bump the hash and REQUIRES a manual `COMPILER_VERSION` bump (see §4).
- **Piece 1 (alias cutover + 6 deferred renames) — NOT EXECUTED. BLOCKED on a direction ruling.** The task's literal mechanic ("remove `registerP1AliasTools`") is **inverted** relative to the codebase's own authoritative dedup registry (`canonical_faces.json`) and the naming standard's Phase-3 gate. Executing it verbatim would DELETE the canonical `layer_noun_verb` faces and leave only the legacy short names — the exact opposite of this residual's DONE bar ("canonical-only tool names resolving"). Full evidence, an executable manifest for the CORRECT direction, and the single blocking question are in §3.

---

## §1 — Alias census (before)

`registerP1AliasTools` (`platform-mcp/src/tools/register_p1_aliases.ts`) registers **56** MCP tool names (re-derived by parsing every `regAlias`/`globalAlias`/`server.tool` call in the file — do not trust the header's "47" or the server.ts "45"):

- **45** are the P1 naming aliases enumerated in the `server.ts:562-586` census comment (D7/D8 17, L0 Ephemeris 5, L0 Brahmagyan 5, L0 Remedy 8, L4 Phala 4, L5 Mīmāṃsā 3, L1 PyJHora 3).
- **+11** additional canonical-named tools NOT in that comment — these are the SOLE serving surface for previously-dark assets (no legacy twin exists): `ganita_av_transit_gating_get`, `ganita_ayurdaya_get`, `ganita_medical_get`, `ganita_sensitive_degrees_get`, `ganita_vastu_get`, `ganita_vichara_get`, `ganita_yoga_firings_get`, `kala_priority_ranking_get`, `phala_predictive_anchors_get`, `ref_sign_medical_get`, `query_dasha_periods` (repointed baseline).

**Every one of these 56 names is a `layer_noun_verb` CANONICAL face** (verified against `canonical_faces.json.canonical_faces`), each delegating to the same handler as a pre-existing legacy tool. **The legacy short names** (`get_positions`, `get_signals`, `query_chart_facts`, `vector_search`, …) are registered ELSEWHERE — `registry_bridge.ts`, `l0_ephemeris.ts`, `l0_brahmagyan.ts`, `retrieval/remedy_tools.ts`, `retrieval/pyhora_natal.ts`, the phala/mimamsa tool files — and are the `deprecated_aliases` KEYS in `canonical_faces.json`.

## §2 — The authoritative end-state (why the task mechanic is inverted)

Three independent authorities agree on the target state, and all three contradict "remove `registerP1AliasTools`":

1. **`platform/src/lib/retrieval/registry/canonical_faces.json`** (`$schema_note`: "canonical_faces = go-forward LLM-visible faces; deprecated_aliases[legacy]=canonical namespaced twin"). It lists all 56 `*_get`/`layer_noun_verb` names as `canonical_faces` (KEEP) and lists the 43 legacy short names as `deprecated_aliases` KEYS mapping TO those canonical faces (REMOVE). e.g. `"get_positions": "ganita_positions_get"`, `"query_chart_facts": "ganita_chart_facts_get"`, `"vector_search": "ref_vector_search"`, `"list_assets": "catalog_assets_list"`.
2. **`00_ARCHITECTURE/MCP_TOOL_NAMING_STANDARD_v1_0.md §4 Phase 3** (line 159): "remove the **old-name** registrations." The survivors are the new canonical `layer_noun_verb` names.
3. **`tool_name_bridge.ts`** (web replay bridge, KEPT per task) + `canonical_faces.deprecated_aliases` both map **legacy → canonical**, i.e. canonical is the survivor.

The task's OWN acceptance criteria are consistent with this ("test a: the 45 legacy alias names now unresolvable"; "test b: the 6 NEW canonical names resolve and the 6 OLD names do not"). Only the Piece-1-step-3 *mechanic* is wrong: it assumes `register_p1_aliases.ts` holds the legacy names. It holds the CANONICAL faces. Removing it would delete the go-forward surface and leave the legacy names live in the other ~9 registrars — the inverse of the DONE bar, and a capability regression for the 11 dark-asset fronting tools that have no legacy twin at all.

## §3 — Piece 1: the CORRECT-direction manifest (for the conductor to execute after a direction ruling)

**Do NOT remove `registerP1AliasTools`.** Instead:

### 3a. Remove the 43 legacy short names (the `deprecated_aliases` keys)

| Registrar file | Legacy names to unregister |
|---|---|
| `tools/registry_bridge.ts` | `get_chart_orientation`, `get_domain_reading`, `get_signals`, `traverse_graph`, `get_positions`, `get_dashas`, `get_temporal_windows`, `get_projections`, `get_classical_citation`, `get_remedies`, `get_chart_quality`, `list_assets`, `get_cgm_subgraph`, `query_chart_facts`, `vector_search` (KEEP the canonical faces in this file: `assess_*`, `judgment_query`, `graha_portrait`, `pact_query`, `chart_snapshot`, `get_graha_yuddha`, `tool_search`) |
| `tools/l0_ephemeris.ts` | `query_planet_position`, `query_planet_transit`, `query_aspects_at_time`, `query_retrograde_periods`, `ephemeris_cache_year` |
| `tools/l0_brahmagyan.ts` | `asset_registry_all`, `asset_registry_l0` (KEEP `resolve_entity`, `list_entities` — both are canonical faces, NOT deprecated) |
| `tools/retrieval/remedy_tools.ts` | `query_remedies`, `query_remedies_for_chart`, `list_remedies_by_category`, `read_remedy`, `query_tantric_remedies`, `query_remedies_by_planet`, `query_mantras` |
| `tools/retrieval/pyhora_natal.ts` | `compute_natal_positions`, `query_special_lagnas` |
| `tools/phala_event_anchors.ts` | `event_anchors` |
| `tools/phala_mitigation_map.ts` | `mitigation_map` |
| `tools/phala_outlook.ts` | `phala_outlook` |
| `tools/muhurta_finder.ts` | `muhurta_finder` |
| `tools/mimamsa_lel_intake.ts` | `lel_query` |
| `tools/mimamsa_outcome.ts` | `record_outcome`, `query_calibration` |
| `tools/register_p1_aliases.ts` (in-file deprecated names) | `bodha_remedies_search`, `query_dasha_periods`, `ref_remedies_search`, `util_intent_classify` |

Total = 43 legacy names → the corresponding canonical faces already resolve and survive.

### 3b. The 6 DEFERRED renames — HAVE A SEPARATE CONFLICT (needs its own ruling)

The task's 6 renames (`recall_session→session_recall`, `list_my_sessions→session_list`, `list_my_charts→catalog_charts_list`, `select_chart→catalog_chart_select`, `holistic_bundle_chart_facts→bodha_bundle_get`, `kala_temporal_bundle→kala_bundle_get`) rename AWAY from names that `canonical_faces.json` currently lists as **canonical faces** (`recall_session`, `list_my_sessions`, `list_my_charts`, `select_chart`, `holistic_bundle_chart_facts`, `kala_temporal_bundle`). The target names (`session_recall`, etc.) are NOT in `canonical_faces.json` at all — the "deferral doc" in `register_p1_aliases.ts:8-16` PROPOSED them but they were never ratified into the dedup registry.

So executing the 6 renames requires ALSO updating `canonical_faces.json` (move the 6 from `canonical_faces` to the new names) AND every consumer of that registry (`doctrine_harness/lib/alias_check.ts`, any conformance/census test). These 6 tools are registered at: `session_tools.ts` (recall_session, list_my_sessions), `chart_selection.ts` (list_my_charts, select_chart), the holistic-bundle registrar (`holistic_bundle_chart_facts`), the kala-temporal registrar (`kala_temporal_bundle`).

### 3c. Consumers to update when 3a/3b land

- `platform/src/lib/retrieval/registry/tool_name_bridge.ts` — **KEEP** (web replay bridge for old persisted conversations). Its `TOOL_NAME_TO_URI` already maps the legacy names → URIs, so old web-channel transcripts still resolve after the MCP names are gone. For the 6 renames, ADD `oldname→newURI` entries if not already present (the generated projection may already cover them — verify against `web_tool_bridge.generated.json`).
- `platform/src/lib/retrieval/registry/canonical_faces.json` — for the 6 renames only (3b).
- `server.ts:561` census comment + `REGISTERED_TOOL_COUNT` + `/health` tool list.
- MCP-level tests asserting legacy names resolve (e.g. `alias_conformance_check.ts`, `whitelist_resolution_invariant.test.ts`, MCP E2E) — update to assert legacy names are now unresolvable and canonical faces resolve.
- `platform-mcp/src/resources/vidhi/compiler.ts` — bump `COMPILER_VERSION` (see §4).

## §4 — notifications/tools/list_changed (mechanism + remediation)

`VIDHI_CAPABILITY_VERSION = vidhi-${COMPILER_VERSION}+r${sha256(VIDHI_PRIMITIVES + VIDHI_INTENT_FLOORS).slice(12)}` (`platform-mcp/src/resources/vidhi/capability_version.ts:42`). `notifyIfCapabilityStale()` fires `server.sendToolListChanged()` only when a client presents a version that differs from the live one — i.e. only when this hash moves.

**Finding:** the hash is NOT derived from the MCP tool list. I checked `registry_data.ts` for the affected names: most legacy names (`traverse_graph`, `query_chart_facts`, `vector_search`, `get_dashas`, …) and ALL 6 deferred old names are ABSENT from `VIDHI_PRIMITIVES`/`VIDHI_INTENT_FLOORS` (which reference the CANONICAL names as recommended tools). Only `get_positions`, `get_signals`, `kala_temporal_bundle` happen to appear. So a Piece-1 removal would NOT reliably bump the hash.

**Remediation (when Piece 1 lands):** bump `COMPILER_VERSION` in `compiler.ts` (`1.0.0 → 2.0.0`). This deterministically changes `VIDHI_CAPABILITY_VERSION`, firing `tools/list_changed` for every client presenting the old version — the correct "staleness kill" for a breaking tool-name change. I did NOT bump it in this session because bumping without the actual breaking change would be a false signal.

## §5 — Pieces 2 & 3 (what LANDED this session)

- `platform/src/lib/config/feature_flags.ts` — `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED: false → true` (+ updated rationale comment).
- `platform/src/app/api/retrieval/capability/__tests__/single_bootstrap_flag.test.ts` — default assertions flipped to `true`; added a no-override "default path" describe proving `query_spine_bundle` + `synth/compose_large_n` are reachable BY DEFAULT; the flag=false block retitled as the emergency-rollback path. The existing superset-diff test (re-derives catalog-vs-hand-list) is unchanged and passes — confirming no new gap.

**Verification:** `npx vitest run single_bootstrap_flag.test.ts capability_cache_wiring.test.ts` → **23 passed**. `npx tsc --noEmit` (platform) → **exit 0**.

**query_spine_bundle activation confirmed by code trace:** `catalog.ts:87` `import './layers/register_spine_bundle'` (side-effect) → `register_spine_bundle.ts:126` `registerCapability(querySpineBundleCapability)` (uri `marsys://tool/L-SPINE/query_spine_bundle`). Under flag=true, `ensureBootstrapped()` (`route.ts:108`) calls `getCatalog()`, which pulls that side-effect import. No new wiring required.

## §6 — D-4b gate status

RC-14's original blocker (D-4b active) appears resolved: `cd5ad175 docs(d4b): CAMPAIGN CLOSE (#723)` and the campaign-close merge are on main. Stale local `wave/D-4b/*` experiment branches still exist but the campaign is closed. Pieces 2/3 are additive (allowed under the deploy mutex without waiting per brief §J.4). Piece 1 is now blocked on the DIRECTION ruling below, not on D-4b. Live-verification of "no active D-4b work on the connector" before any deploy remains the conductor's job (brief §J.3) — I cannot verify the live deployed connector from this environment.

## §7 — The single blocking question for the conductor / native

> **Confirm the Piece-1 direction:** the breaking flip should REMOVE the 43 legacy short names (the `canonical_faces.json` `deprecated_aliases` keys, per the §3a manifest) and KEEP `registerP1AliasTools` (the canonical faces) — NOT remove `registerP1AliasTools`. AND: ratify the 6 deferred renames — do we adopt `session_recall`/`session_list`/`catalog_charts_list`/`catalog_chart_select`/`bodha_bundle_get`/`kala_bundle_get` (updating `canonical_faces.json` accordingly), or keep the current canonical faces (`recall_session` etc.) that `canonical_faces.json` already ratifies and drop the deferral doc?

Once ruled, §3's manifest + §4's `COMPILER_VERSION` bump make Piece 1 a mechanical, fully-specified change.
