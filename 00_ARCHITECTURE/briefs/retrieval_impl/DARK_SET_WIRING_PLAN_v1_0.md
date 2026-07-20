---
artifact: DARK_SET_WIRING_PLAN_v1_0.md
canonical_id: DARK_SET_WIRING_PLAN
version: 1.2
status: PARTIALLY IMPLEMENTED — 2 of 2 compute-service items + 4 table items wired W2 (2026-07-20); remainder still design-only
authored_by: Claude (Cowork), Lane L1d, W1; `ka_muhurta_seva` row added by W1 addendum (§F gate ruling item 6), 2026-07-20; W2 wiring log added 2026-07-20
changelog:
  - v1.3 (2026-07-20, disclosure correction): the CDLM rollup-tier row and the
    `bodha_cgm_sub_graphs` row below WERE ALSO wired in the same W2 dark-set
    wiring pass that did `ka_graha_sancara`/`ka_muhurta_seva` — the v1.2 entry
    below omitted them from its own summary despite the working tree already
    containing both implementations (found by the W2 phase-1 independent
    verifier via `git diff`, not disclosed by the implementing lane's own
    report). Corrected here so the doc matches the diff. Both rows now marked
    WIRED with real file:line citations; original design text retained beneath
    each for audit trail, matching the `ka_muhurta_seva` pattern below.
  - v1.2 (2026-07-20, W2 dark-set wiring lane): `ka_graha_sancara` (GT-50) and
    `ka_muhurta_seva` WIRED FOR REAL — sidecar routes + TS handlers + tests, no
    longer design-only for these two. See "W2 WIRING LOG" section below and the
    `ka_muhurta_seva` table row (now marked WIRED, original design text retained
    below it for audit trail). Two additional SERVE-gap table items
    (`bg_graha_naisargika_friendship`, `bg_combustion_orbs` — not previously rows
    in THIS document, tracked in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` instead)
    were also wired this pass; see that document's §9 addendum for those two.
  - v1.1 (2026-07-20, W1 addendum, §F gate ruling item 6): added `ka_muhurta_seva`
    row to the W2 scope table — same stub shape as `ka_graha_sancara`/GT-50,
    surfaced by W1's L1c service-manifest lane but not previously named in this
    plan. Design only, no implementation.
  - v1.0 (W1, Lane L1d): initial dark-set wiring design.
---

# Dark-Set Wiring Plan v1.0/v1.2 (v1.0 design only; v1.2 records the first real W2 wiring)

Hand-authored design note. Every table/stratum here is real (confirmed present in the
live DB via L1b's E2 extractor or L1c's service manifest). As of v1.2, two
compute-service items (below) have been wired for real; everything else in this
document remains design-only — "how would W2 do it," not yet built.

## W2 WIRING LOG (2026-07-20)

**`ka_graha_sancara` (GT-50) — WIRED.** New sidecar endpoint `POST
/api/compute/ephemeris_at_t` (`platform/python-sidecar/routers/ephemeris.py`'s
`compute_router`, mounted in `main.py`), following `DESIGN_KA_GRAHA_SANCARA_WIRING.md`
§3 exactly (shared `_position_from_lon`/`PLANETS` helpers, no second swisseph
integration, ayanamsha fails loud on an unrecognized id per §3 item 5). TS handler
`callEphemerisAtTCapability.handler` (`call_service_wrappers.ts`) replaced the
unconditional-error stub with a real `fetch()`, mirroring `callTransitSearchCapability`'s
existing pattern per §3 item 4. Real-compute proof (no mocks):
`platform/python-sidecar/tests/l3/test_ephemeris_at_t_sidecar_route.py` (6 tests, all
pass — includes a Rahu/Ketu-180°-apart invariant and a two-instants-differ-by-a-full-day
Moon-motion check, both of which only pass against genuine live compute). TS wiring-seam
tests (mocked fetch): `platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/
w2_dark_set_wiring.test.ts`.

**`ka_muhurta_seva` — WIRED.** See the table row below (now flagged WIRED, with the
original W1 design text retained beneath it for audit trail).

**CDLM rollup tiers — WIRED.** `query_cdlm_summary.ts`'s existing capability extended
with a 5th `tier` facet reaching `bodha_cdlm_domain_rollups`/`pattern_clusters`/
`evolution_gradients` — exactly the "extend the existing capability with a facet, don't
build 3 new tools" shape this plan's own row (below) already prescribed. Test:
`platform/src/lib/retrieval/registry/layers/L2_bodha/__tests__/query_cdlm_summary.test.ts`.
See the table row below for full detail (now marked WIRED, original design text
retained for audit trail).

**`bodha_cgm_sub_graphs` — WIRED.** `traverse_chart_graph.ts`'s existing capability
extended with a 5th `sub_graphs` mode — the investigation this plan's own row (below)
called for was run, and it confirmed the table genuinely had zero prior TS-registry
route (the CGM-plane false-dark hypothesis did NOT hold for this specific table, unlike
its siblings `bodha_cgm_nodes`/`edges`/`chart_topology_summary`, which the same
investigation confirmed ARE already served via this same tool's other modes). Test:
`platform/src/lib/retrieval/registry/layers/L2_bodha/__tests__/traverse_chart_graph.test.ts`
(extended). See the table row below for full detail (now marked WIRED, original design
text retained for audit trail).

**Not wired this pass (honestly still open):** the RM prescription tables,
`bodha_triangulation`, the L0 `bg_prashna_*`/`bg_transit_*` `NEEDS-OWNER` set (now
re-labeled genuine SERVE gap per the §F gate ruling — see `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`),
`chart_ayanamsha_reports` (naming question resolved — see `RETRIEVAL_STRATEGY_v1_0.md`
§5.2's footnote — but no wiring done), and the L5 Mīmāṃsā calibration tables (still
flag-not-wire per this document's own caution, and per the native's §F gate ruling
pre-disposing the two largest ones GATED). `bg_graha_naisargika_friendship` and
`bg_combustion_orbs` (2 more genuine SERVE-gap table items) were also wired this pass —
tracked in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §9, not as rows in this document.

| item | current state (real, verified) | proposed capability shape | est. effort |
|---|---|---|---|
| `bodha_rm_dasha_windowed_prescriptions` | Real L2 table, 0 rows on the live chart (DARK-033, `NEEDS-OWNER`). Zero TS-registry route. Sibling RM tables (`bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`) are also DARK — this is a whole unwired RM sub-plane, not one orphan table. | A `bodha_remedy_prescriptions_get` drill tool (leaf, `traversal_level=L-SOURCE`) hung off the existing `bodha_remedies_get`/`bodha_remedies_search` umbrella (already served, per `mcp__marsys-jis-direct__bodha_remedies_get`) — filtered by `dasha_period_id`/`chart_id`, `emits_references=true` (resolves to `mimamsa_fact_adjustment`/RM fact_ids). Row-count is 0 on the current chart — **first confirm this is a real build gap and not a genuinely-empty-by-design table** before writing a tool against it (B.10: don't build a retrieval surface for data that was never meant to populate). | M — one new leaf tool + a build-gap investigation (is 0 rows correct for this chart, or a writer bug); ~1-2 days incl. the investigation. |
| CDLM rollup tiers (`bodha_cdlm_domain_rollups` 60 rows, `bodha_cdlm_evolution_gradients` 0 rows, `bodha_cdlm_pattern_clusters` 10 rows) | **WIRED — W2 (2026-07-20).** `query_cdlm_summary.ts` (`platform/src/lib/retrieval/registry/layers/L2_bodha/`) extended with a `tier` facet param reaching all 3 tables — exactly as proposed in the "proposed capability shape" column below, not a new standalone tool. Test: `__tests__/query_cdlm_summary.test.ts`. Original analysis below, retained for audit trail. | ~~Extend the existing CDLM-serving capability...~~ **Done — see WIRED note.** | ~~S~~ **Actual: S**, as estimated. |
| ~~CDLM rollup tiers — original W1 analysis (superseded by the WIRED row above)~~ | All 3 real L2 tables, all `NEEDS-OWNER` DARK. `bodha_cdlm_cells` and `bodha_cdlm_chart_summary` (siblings, not in the DARK list) ARE served, per L1b's cross-diff — so the CDLM plane is **partially** wired, not wholly dark. This is a coverage gap in an existing served family, the cheapest kind to close. | Extend the existing CDLM-serving capability (whichever registered tool already touches `bodha_cdlm_cells`/`chart_summary` — identify via `table_hint` cross-reference, not re-guessed) with a `tier` or `rollup_level` facet param that reaches `domain_rollups`/`pattern_clusters`/`evolution_gradients` rather than adding 3 new standalone tools — matches strategy §2's "which move does it serve" doctrine (these are depth-tiers of ONE concept, not 3 new concepts). | S — extend one existing capability's `about`/facet handling + SQL branch per tier; ~0.5-1 day given the sibling tables are already wired (the query pattern exists, just needs to be generalized). |
| `bodha_triangulation` | Real L2 table, 200 rows (populated, not empty — DARK-037, `NEEDS-OWNER`, L1b's own rationale flags this as "the most consequential DARK class: real data with no discovered TS-registry route"). | A `bodha_triangulation_get` leaf tool (or a facet on `bodha_discoveries_get`/`bodha_signals_get` if triangulation rows reference `bodha_discoveries`/`bodha_msr_signals` fact_ids — check the FK shape before deciding standalone-vs-facet). `emits_references=true`, `traversal_level=L-SOURCE`. Given 200 real rows already exist, this is pure serving-surface work, no build-gap investigation needed first (unlike the RM item above). | M — one new leaf tool + FK/shape investigation to decide standalone vs. facet-on-existing; ~1 day. |
| `bodha_cgm_sub_graphs` | **WIRED — W2 (2026-07-20).** The W1 addendum's widened-surface re-scan ran the investigation this row itself called for (confirmed: zero references to `bodha_cgm_sub_graphs` anywhere in the TS codebase, unlike its siblings which ARE served) — so the false-dark hypothesis did NOT hold for this table specifically. `traverse_chart_graph.ts` extended with a 5th `sub_graphs` mode, per the "if genuinely a gap, extend the existing CGM tool" branch of this row's own proposal. Test: `__tests__/traverse_chart_graph.test.ts` (extended). Original analysis below, retained for audit trail. | ~~Investigation first...~~ **Done — investigation ran (W1 addendum), gap confirmed real, wired via the "extend, don't build a 4th tool" branch.** | ~~S or M~~ **Actual: M**, as the row's own estimate anticipated for the genuine-gap case. |
| `bodha_cgm_sub_graphs` — original W1 analysis (superseded by the WIRED row above) | Real L2 table, 10 rows (DARK-029, `NEEDS-OWNER`, same "most consequential" flag as triangulation). Siblings `bodha_cgm_nodes`/`bodha_cgm_edges`/`bodha_cgm_chart_topology_summary` are ALSO DARK (77-row set), but `get_cgm_subgraph`/`bodha_graph_subgraph_get`/`bodha_graph_traverse_get` already exist as live MCP tools (per the deployed connector's face) — meaning the CGM graph plane likely IS served via a route this TS-registry-only scan couldn't see (platform-mcp's own tool files, or a Python-sidecar route), matching the exact GT-51 false-dark pattern this lane already caught twice (`bg_dignity_reference`, `chart_panchanga`). **Before wiring anything new here: re-run the census with platform-mcp's tool directory included in the scan** — this may turn out to be SERVED already, not DARK. | Investigation first (near-zero cost, high value): grep `platform-mcp/src/tools/` + `platform-mcp/src/resources/` for `bodha_cgm_sub_graphs`/`bodha_cgm_nodes`/`bodha_cgm_edges`. If genuinely unserved after that: a `sub_graph_id` facet on the existing `get_cgm_subgraph`/`bodha_graph_subgraph_get` tool. | S (if the investigation confirms it's actually served — likely, given live sibling tools exist) or M (if genuinely a gap — extend the existing CGM tool, don't build a 4th standalone one). |
| L0 `bg_*` catalog stratum (21 of the 29 `bg_*` DARK tables are `INTERNAL-BY-DESIGN` per L1b's naming-pattern rule; 8 are `NEEDS-OWNER`: `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_transit_av_gates`, `bg_transit_engine`) | Real L0 tables, small (3-16 rows), classical-rule/reference-constant shape. `INTERNAL-BY-DESIGN` disposition (sidecar computation inputs, not caller-facing concepts) is plausible for most but **not independently verified per-table this lane** — L1b's own caveat: "this extractor did NOT verify the sidecar consumption for each table individually." The 8 `NEEDS-OWNER` `bg_prashna_*`/`bg_transit_*` tables are the ones most likely to be genuinely caller-relevant (prashna/transit are live query domains — `mcp__marsys-jis-direct__prashna_undertaking_get`, `ganita_av_transit_gating_get` already exist) rather than pure sidecar plumbing. | Owner-assignment pass first: for the 8 `NEEDS-OWNER` rows, check whether `prashna_undertaking_get`/`ganita_av_transit_gating_get`'s existing handlers already join these tables server-side (would make them correctly `INTERNAL-BY-DESIGN`, just missed by the table_hint regex) before proposing any new tool. The 21 `INTERNAL-BY-DESIGN` rows need no wiring — confirm-only. | S — mostly a verification/confirmation pass (a few hours), not new tool-building, unless the 8 `NEEDS-OWNER` investigation surfaces a genuine caller-facing gap. |
| `chart_ayanamsha_reports` | **Table does not exist in the live DB** — verified against L1b's E2 extractor's full 247-table live scan (zero match for `chart_ayanamsha_reports` or any close variant). The closest real tables are `concordance_ayanamsha_flags` (2 rows) and `concordance_ayanamsha_flags_staging` (0 rows), neither named this in any source this lane read. | **Flag for the conductor before any wiring plan is written** — either the brief's naming is stale/aspirational (the table was renamed, retired, or never built) or it refers to a computed report (not a table) that `chart_facts_query`'s `ayanamsha_id` filter + the 6 stored ayanamshas already serve without a dedicated table. No effort estimate is meaningful until this is resolved — estimating wiring work for a table that doesn't exist would be fabrication. | **N/A — resolve the naming question first.** |
| `ka_muhurta_seva` (`call_muhurta_score`) | **WIRED — W2 (2026-07-20).** Real sidecar route `POST /api/compute/muhurta_score` (`platform/python-sidecar/routers/muhurta_score.py`, new file, mounted in `platform/python-sidecar/main.py`), reuses `panchang_engine.muhurat.score_muhurat()` — the SAME scoring primitive `ph_muhurta`/`muhurta_finder` already calls internally, not a second engine (`EVENTS_MVP`'s `upaya_ritual`/`sadhana_initiation` additions were already added specifically for this service — `muhurat/finder.py`'s own comment cites "ka_muhurta_seva, 2026-06-21"). TS handler in `call_service_wrappers.ts` (`callMuhurtaScoreCapability.handler`) now does a real `fetch()`. **Contract correction made this pass:** the descriptor's pre-wiring `event_class` enum (`marriage, travel, business, medical, education, ceremony`) was copy-pasted from `ph_muhurta`'s unrelated `action_type` vocabulary and had never had a live caller (handler always errored) — replaced with the real `EVENTS_MVP` vocabulary `score_muhurat()` actually accepts (`vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation, upaya_ritual, sadhana_initiation`) rather than fabricating an inaccurate mapping. No chart_id/lat/lng (scope: global) — panchang computed at the same canonical default location (Bhubaneswar, IST) already used elsewhere in this sidecar for chart-less lookups. Tests: `platform/python-sidecar/tests/l3/test_muhurta_score_sidecar_route.py` (7 real-compute tests, no mocks, 7/7 pass — corrected 2026-07-20; this row originally overclaimed 13/13, which was actually the combined ephemeris+muhurta figure, see `STATE.md`) + `platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/w2_dark_set_wiring.test.ts` (TS wiring-seam tests, mocked fetch). Original plan text below, retained for audit trail. | ~~Same design shape as `ka_graha_sancara`~~ **Done.** | ~~S/M~~ **Actual: S** — the scoring primitive already existed (and was already extended for this exact service); only the sidecar route + TS wiring were net-new. |
| `ka_muhurta_seva` — original W1 plan text (superseded by the WIRED row above) | **New W1 addendum item, added per §F gate ruling item 6** (native ruling: "joins W2's dark-set wiring scope, same stub shape as `ka_graha_sancara`, GT-50 sibling"). Sibling dark L3 service to `ka_graha_sancara`/GT-50 — same unconditional-error stub shape, discovered incidentally during W1's L1c service-manifest lane but not named in GT-50 or the plan's original dark-set list. Stub lives at `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` (lines ~411-421) — the handler returns an error unconditionally, never attempts a network call, exactly like `call_ephemeris_at_t`. Documented in `platform/src/lib/retrieval/registry/service_manifest/service_manifest.json` (`logical_service_id: "ka_muhurta_seva"`, entries around lines 657-661 and 683-684). **Important disambiguation the manifest lane already flagged:** a DIFFERENT, already-wired muhurta endpoint exists at the sidecar's `/api/compute/phala/muhurta_finder` (L4 Phala's electional finder, `brahmagyan/phala/muhurta.py`, served MCP-side as `muhurta_finder`/`kala_muhurta_get`) — that is a distinct logical service (`ph_muhurta`, electional/purpose-scored search) from `ka_muhurta_seva` (a raw per-datetime muhurta SCORE, no electional search). Do not conflate the two when wiring. | Same design shape as `ka_graha_sancara` (see `DESIGN_KA_GRAHA_SANCARA_WIRING.md` for the template this should mirror): identify or build the sidecar compute primitive for a raw per-datetime muhurta score (tithi/vara/nakshatra/yoga/karana-based scoring at an arbitrary UTC instant, no chart/electional search), then replace the unconditional-error stub in `call_service_wrappers.ts` with a real network call. **Design only this wave — no implementation.** Per the §F gate ruling and this plan's own frame, this is in-scope for W2, not W1. `must_not_touch: kala_* serving semantics` (doctrine-campaign-owned) still applies — any actual wiring touches L3 Kāla serving surface and must coordinate with the doctrine campaign's D-5 cadence before landing, same as `ka_graha_sancara`. | S/M — same size class as `ka_graha_sancara` (design already has a template to follow); actual estimate depends on whether a matching sidecar compute primitive already exists (not audited this wave) or needs to be built from panchanga primitives already used elsewhere (`ga_panchanga_writer.py`, `pyjhora_adapter/panchanga.py`). |
| Mīmāṃsā (L5) read candidates (19 `mimamsa_*` DARK tables: 6 `INTERNAL-BY-DESIGN` bookkeeping/log tables — `adjudication_log`, `calibration_snapshot`, `export_log`, `pool_contributions`, `resonance_feedback`, `snapshot_cosign` — + 13 `NEEDS-OWNER`, incl. `mimamsa_fact_adjustment` at 121,100 rows and `mimamsa_signal_adjustment` at 97,504 rows — the two largest DARK tables in the entire 77-row set) | L5 Mīmāṃsā is SEALED in **STRUCTURAL mode** per CLAUDE.md §E ("empirical calibration values fill in as prediction→outcome data accrues — by design, not unfinished work"). Live tools already exist (`mimamsa_calibration_get`, `mimamsa_insight_get`, `mimamsa_outcome_record`, `mimamsa_lel_query`). `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment` (the two big ones) are almost certainly the row-level calibration deltas those umbrella tools already aggregate over — i.e. likely correctly `INTERNAL-BY-DESIGN` (raw adjustment ledger, not a caller-facing concept) rather than a coverage gap. **Do not build new leaf tools against calibration-ledger internals without native/L5-owner sign-off** — L5's calibration substrate is explicitly a "fills in as outcome data accrues" surface, and B.10/B.1 both caution against exposing raw adjustment rows as if they were settled facts. | Owner-assignment pass, same shape as the L0 item: confirm `mimamsa_calibration_get`'s existing handler already reads `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment` server-side (would make them correctly internal). If it doesn't, this is a genuine question for the L5 seal-owner, not a mechanical wiring task — flag, don't wire. |

## W2b WIRING LOG (2026-07-20)

The `bodha_triangulation` and `bodha_rm_dasha_windowed_prescriptions` rows above (plus their
three RM-family siblings `bodha_rm_chart_summary`/`bodha_rm_dosha_remedy_bundles`/
`bodha_rm_pattern_remedies`, and all 30 remaining rows from `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`
§8's SERVE-gap list) are now **WIRED** — see `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §11 for the
full 36-item batch-wiring log (real `CapabilityDescriptor` code + tests + disposition-table
flips for every item), including the standalone-vs-facet FK-shape check `bodha_triangulation`'s
row above called for (no FK found — wired standalone) and the B.10 empty-table investigation
`bodha_rm_dasha_windowed_prescriptions` called for (genuine not-yet-populated concept, real
writer contract exists — wired with honest `empty_reason` discipline). This document's own
per-row size estimates (M for triangulation, M for the RM slice) held roughly — see §11 for
the real files/tests landed.

## What this plan deliberately does not do

No SQL was written, no capability descriptor was added, no `WriterBase`/orchestrator
code was touched (FROZEN, must_not_touch) and no `kala_*` serving semantics were
touched (doctrine-campaign-owned while both campaigns are active, per this lane's
`must_not_touch`). Every effort estimate above is a rough size class (S/M), not a
committed schedule — sizing a piece of work you haven't started is inherently
approximate; this is flagged rather than dressed up as precise.

---

*End of DARK_SET_WIRING_PLAN v1.0 — Lane L1d, W1. Design only; W2 (or a later wave) is
where any of this actually gets built.*
