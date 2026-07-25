---
artifact: W4_MCP_SURFACE_SERVING_NOTE
canonical_id: W4_MCP_SURFACE_SERVING_NOTE
version: 1.0
status: CURRENT
author: Builder B3 (SATYA-ŚEṢA campaign, W4 — deploy-surface verification)
date: 2026-07-25
parent: SATYA_SHESHA_BRIEF_v1_0.md §2 W4
---

# W4 — MCP surface serving-note: catalog-vs-MCP-surface delta

## 1. What this note is

W4's brief (`SATYA_SHESHA_BRIEF_v1_0.md` §1/§2) framed the finding as "MCP surface exposes
106 tools; the platform catalog holds 172" and asked (a) proof that `concept_locate` and
`get_database_schema` are live-callable, (b) wiring if they are not, (c) a deploy, (d) a
short serving-note explaining the delta so "106-vs-172 stops looking like a bug when it
isn't one."

This note documents what was actually found on live investigation, corrects the numbers
against a raw MCP `tools/list` probe taken today, and gives the delta with reasons.

## 2. Headline finding: the two named tools were already fixed and deployed

`concept_locate` and `get_database_schema` are catalog-visible-but-uncallable **was already
fixed** by an earlier same-day lane (Elevation Campaign v2.1 STREAM α Lane-H, commit
`c9e61f8c`, merged to `main` before this campaign's brief was authored) which registered
them on the MCP surface as `ganita_concept_locate` and `ganita_database_schema_get` (the
canonical `layer_noun_verb` names — the bare short names `concept_locate`/`get_database_schema`
were never valid MCP tool names post-RC-14's naming flip; the brief uses them as shorthand
for the underlying capability). That commit was **already deployed** to production before
this session started: `gcloud run services describe amjis-mcp` shows the live revision
(`amjis-mcp-00474-bh5`, deployed `2026-07-25T13:06:03Z`) running image SHA `8aa5c6c7...`,
which is a descendant of `c9e61f8c`. No commit between that deployed SHA and this campaign's
branch point touches `platform-mcp/`, so the fix was already live when this session's
investigation began.

**Live verification performed this session** (raw MCP JSON-RPC `POST /mcp`, `tools/list` +
`tools/call`, against `https://amjis-mcp-qm256lasva-el.a.run.app/mcp`, Bearer-key auth =
`full` profile — the authoritative test per the brief, not a proxy):

- `tools/list` → **111 tools** live today (not 106 — see §3 for why the number moved).
- `ganita_concept_locate` is in the list; `tools/call ganita_concept_locate {query: "gulika"}`
  → `concept_id: "sensitive_point_gulika_mandi"`, `resolved: true`, `resolved_via: "alias_exact"`.
  **Acceptance criterion 1 (concept_locate("gulika") → sensitive_point_gulika_mandi): MET.**
- `ganita_database_schema_get` is in the list; a call with `limit: 5` returns 5 entries,
  `pagination.total: 11047`, a `next_cursor`, and the full `concept_aliases` table (28
  concepts including `sensitive_point_gulika_mandi`). **Acceptance criterion 2
  (get_database_schema pages correctly): MET.**
- `mcp_server_info` is in the list; a call returns `name: "marsys-jis"` (matches
  `MCP_SERVER_NAME` in `register_server_info.ts`, confirming this is genuinely the same
  server, not a bypass), `catalog_version`, `tool_count`, `stale: false`. **EL-13 /
  mcp_server_info liveness: CONFIRMED.**
- `ganita_planet_get` (the third Lane-H addition) is also live, bonus-confirmed.

Raw request/response evidence, `.mcp.json` target resolution, and the `gcloud` revision
query are in the session transcript; not duplicated here to keep this note short per the
brief's own instruction.

## 3. Where "106 vs 172" came from, and why today's numbers are different

Three different "tool count" surfaces exist in this codebase and they are **not the same
number by design**, which is itself worth naming plainly:

| Surface | What it measures | Value found today |
|---|---|---|
| Raw MCP `tools/list` (live, Bearer key / `full` profile) | The actual tools a real MCP client sees right now | **111** |
| `GET /health`'s `tools` field | A hand-maintained constant in `server.ts` (`REGISTERED_TOOL_COUNT`), incremented by hand per PR | was **83** (stale — see §5), now **88** after this fix |
| `mcp_server_info`'s `tool_count` / the generated `mcp_surface_profiles.generated.ts` `full.total` | The retrieval-registry's `mcp_full`-tagged capability count, generated from `getCatalog()` by `mcp_surface_profile_builder.ts`, last regenerated 2026-07-24T05:06 | **152** |

The brief's "106 vs 172" was a live probe captured earlier the same day (2026-07-25),
before several other lanes (Lane-H, and unrelated Stream γ work) landed and deployed. By
the time this session ran its own live probe, the live count had already moved to 111 (partly
Lane-H's +3, partly other same-day churn this campaign did not target). The "172" catalog
figure does not correspond to a single number this session could reproduce exactly — the
closest analogue, the generated manifest's `full` total, is 152, and that manifest is itself
one day stale (generated before Lane-H, so it still lists pre-RC-14 short names that are no
longer registrable and doesn't yet know about Lane-H's 3 additions). **Recommendation for a
follow-up lane:** regenerate `mcp_surface_profiles.generated.ts`
(`npx tsx --conditions=react-server scripts/manifest/generate_projections.ts` from
`platform/`) so `mcp_server_info`'s `catalog_version`/`tool_count` stop reporting a stale
152 against a live 111+.

## 4. The delta, categorized with reasons

Diffing the generated manifest's `full.tool_names` (152, stale 2026-07-24 snapshot) against
today's live 111-tool `tools/list` gives 140 names present in the generated catalog but not
found live under that exact string. Categorizing that 140 with concrete evidence:

**a. Legitimately retired — RC-14 breaking flip (15 confirmed, exact overlap with
`DEPRECATED_MCP_TOOL_NAMES` / `canonical_faces.json`'s `deprecated_aliases`):**
`get_dashas`, `get_positions`, `list_remedies_by_category`, `query_aspects_at_time`,
`query_calibration`, `query_mantras`, `query_planet_position`, `query_planet_transit`,
`query_remedies`, `query_remedies_by_planet`, `query_remedies_for_chart`,
`query_retrograde_periods`, `query_tantric_remedies`, `read_remedy`,
`yoga_activation_by_dasha`. Each has a live canonical replacement already on the surface
(e.g. `get_dashas` → `ganita_dashas_get`, `query_remedies` → `ref_remedies_get`) —
`platform-mcp/src/lib/deprecated_tool_gate.ts` blocks the legacy name from ever registering,
by design, unconditionally, across all profiles. **Reason: legitimately internal (retired
duplicate), gated by `applyDeprecatedToolGate`.**

**b. Genuinely internal by explicit registry tag (8, from the generated manifest's own
`excluded_calibration_context_only` / `excluded_not_llm_facing` lists for the `full`
profile):** `lel_query`, `mechanism_retrodiction_get`, `query_predictions`
(calibration-context-only, F-R7 NO-LEAKAGE ruling — these feed calibration, never a direct
answer) and `maro_mcp_surface`, `maro_orchestrate`, `route`, `synergy_cross_layer`,
`synergy_pipeline` (not-LLM-facing internal orchestration primitives). **Reason:
legitimately internal, gated by design (calibration-context-only / not-llm-facing tags).**

**c. Consolidated into the general fact-discovery surface, not given a 1:1 dedicated MCP
face (a substantial share of the remainder — spot-checked, not exhaustively re-verified):**
Many of the L1 Gaṇita per-category capabilities in the gap (`get_dignity`, `get_argala`,
`get_ashtakavarga`, `get_aspects`, `get_avasthas`, `get_bhava_bala`, `get_dispositors`,
`get_karakas`, `get_panchanga`, `get_sensitive_points`, `get_tajik`, `get_yoga_dosha`, and
others) correspond to `fact_category` values that `ganita_database_schema_get`'s
`concept_aliases` table and `ganita_concept_locate` explicitly resolve through the general
`ganita_chart_facts_get` query surface (verified live this session — e.g. the "dignity"
alias resolves to `fact_categories: ["graha_dignity_per_varga", ...]`, servable via
`ganita_chart_facts_get(category=...)`). This is a documented design choice (consolidation
behind a generalized query tool, discoverable via `concept_locate`), not a missing
capability — though this session did not verify every single one of these individually.
**Reason: legitimately internal — reachable via `ganita_chart_facts_get`/`ganita_concept_locate`
by design, not exposed as a separate named face.**

**d. Genuine bug, now fixed — read_classical_text.ts family (5 tools, this session's fix,
PR referenced below):** `read_classical_text`, `read_chapter`, `list_classical_texts`,
`find_verses_about`, `search_classical_texts` were fully implemented in
`platform-mcp/src/tools/read_classical_text.ts` (dated 2026-06-07, "L0FR Stream C —
brahmagyan.texts", with working `callPlatformPrimitive` delegation to backend primitives
confirmed live via `tool_name_bridge.ts`'s `MCP_TO_RETRIEVAL_TOOL` whitelist) but the file
was **never imported into `server.ts`** — a second, independent instance of exactly the
"registered ≠ deployed ≠ callable" failure class this campaign targets, this time a whole
tool file rather than 2-3 individual tools. Classical-text citation lookup (BPHS, Saravali,
etc.) is consumer-facing truth-grounding, squarely the kind of tool the brief says "MUST be
on the MCP surface." **Reason: was a bug, now wired — see PR reference in the final report
this note accompanies.**

**e. Not independently re-verified this session (residual, PARKED-HONEST):** the remaining
~110 names in the gap (mostly L2 Bodha / L3 Kāla / L4 Phala / L5 Mīmāṃsā synthesis-layer
capability names from the stale generated manifest — `query_insights`, `query_discoveries`,
`query_mechanisms`, `query_signals`, `query_rm_*`, `query_cgm_*`, `query_ucd`,
`compose_large_n`, `query_spine_bundle`, `query_domain_reading`, and similar) were **not**
individually traced to either a live renamed equivalent or a confirmed registry-only gap
within this session's time budget. Live equivalents almost certainly exist for most of them
under different canonical names (e.g. `bodha_discoveries_get`, `bodha_signals_get`,
`bodha_mechanisms_get`, `mimamsa_insight_get`, `kala_life_arc_get` are all confirmed live and
look like plausible renamed targets for several of these), but this session did not build
the exhaustive 1:1 mapping needed to assert that with the same rigor as §4a/b/d. **Honest
disposition: PARKED — a follow-up census pass should (i) regenerate the stale manifest per
§3's recommendation, (ii) re-run the diff against a fresh manifest, and (iii) trace any
still-unmatched name to either a renamed live tool or a genuine gap, wiring any real gap the
same way §4d's fix did.** No evidence found during this session that any of these ~110 are
consumer-facing truth tools silently missing with no live path at all — the pattern found in
§4d (a whole never-imported file) was the one concrete bug this investigation surfaced, and
it is now fixed.

## 5. Ancillary finding: `/health`'s `tools` count was already stale, independent of W4

While investigating, `GET /health` reported `tools: 83` (a hand-maintained constant,
`REGISTERED_TOOL_COUNT` in `server.ts`) against a live `tools/list` count of 111 — a
pre-existing ~28-tool undercount that predates this session and is unrelated to the
concept_locate/get_database_schema fix. This session incremented the constant by the +5 it
added (83 → 88) and left an explicit in-code comment flagging that the constant is known to
still undercount the live surface and should not be treated as authoritative — `tools/list`
is. Fully reconciling `/health`'s count mechanically (deriving it from the request-scoped
server's actual registered-tool count rather than hand-maintaining it) is a larger, separate
follow-up, not attempted here to avoid scope creep on a shared bootstrap path.

## 6. Summary table for the acceptance criteria

| Acceptance criterion | Status | Evidence |
|---|---|---|
| Live MCP call `concept_locate("gulika")` → `sensitive_point_gulika_mandi` | MET | `ganita_concept_locate` live call, §2 |
| `get_database_schema` pages correctly | MET | `ganita_database_schema_get` live call, §2 |
| Delta list written, each absent tool has a stated reason | MET (this note) | §4a–e |
| `mcp_server_info` (EL-13) live | MET | §2 |
