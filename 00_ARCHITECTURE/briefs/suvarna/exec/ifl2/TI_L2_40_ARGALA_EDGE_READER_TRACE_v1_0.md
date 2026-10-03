---
version: 1.0
status: CURRENT
lane: TI-i-fl2-006
item: TI-L2-40 (reader trace before TI-L2-37 / -38 / -39)
branch: suvarna/land/TI-i-fl2-006
basis: origin/main adb0db29d (code read); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.0 -- trace of every reader found of L2 argala edges and bodha_cgm_edges.cancelled_flag, with what TI-L2-37 (cancelled_flag semantics for argala end; `undetermined` its own state) does to each. Evidence only.
---

# TI-L2-40: readers of L2 argala edges and of `cancelled_flag`

Track A A.L2 item TI-L2-40 (argala outcome ruling, L1 N-61/N-66): "trace and list every reader of argala
edges and `cancelled_flag` BEFORE coding". The coded changes it precedes: TI-L2-37 (`bo_karanajala` reads the
L1 `outcome_by_count`; `unobstructed` and `argala_prevails` are active, `undetermined` is its own state and not
active; "the old `cancelled_flag` semantics for argala end"), TI-L2-38 (`bo_pramana_mapa` scorecard), TI-L2-39
(migration 763 conjunct 6; digest spec 976). This note builds none of them.

## What the data is today (production, chart 482012f1)

`bodha_cgm_edges` has 849 rows; 119 are `edge_type = 'argala'`:

| relationship_class | cancelled_flag | valence | rows |
|---|---|---|---|
| argala_positive | false | antagonistic / harmonious / mixed / neutral | 10 / 10 / 30 / 25 |
| argala_virodha | false | antagonistic | 34 |
| argala_virodha | **true** | antagonistic | **10** |

Those 10 are the only `cancelled_flag = true` rows of the whole table (all other edge types: 0). The
`cancelled_by_jsonb` payload carries `original_polarity`, `resulting_role`, `cancelling_roots[]`, `cancelling_actors`,
`target`.

## Readers found (file:line at origin/main adb0db29d) and the effect of TI-L2-37

| # | reader | what it does | effect if `cancelled_flag` stops being set for argala (and `undetermined` is added) |
|---|---|---|---|
| E-1 | `bo_karanajala.py:609-613` (writer), INSERT at `:65-79`; other sites hard-code `False` (`:692, :775, :1014, :1137, :1189, :1258, :1716`) | produces the flag and payload | this is the change itself |
| E-2 | `bo_pramana_mapa.py:589-606` (`_SIGNED_RELATION_SQL`, the signed-relation scorecard) | counts violations: `valence IS NULL OR valence NOT IN (harmonious, antagonistic, mixed, neutral, benefic, malefic)` or `cancelled_flag IS TRUE AND <payload incomplete>` | (a) the `cancelled_flag IS TRUE AND ...` conjunct would never fire once the flag is not set: it keeps passing but checks nothing (the N.8 pattern); (b) a new edge `valence` such as `undetermined` would count as a violation, so the closed set must change in the same batch if `undetermined` is stored in `valence` (TI-L2-38 says "own state"; where it is stored decides this) |
| E-3 | `services/ka_kshetra/stage2_promise.py:330-340` (`_fetch_cgm_edges`, Kāla L3, read only) | `WHERE ... cancelled_flag = FALSE`; maps `argala` edges into the promise graph with `computed_strength` | **the 10 cancelled `argala_virodha` edges are excluded today. If the flag is no longer set they enter the promise graph** with their stored strength: a change in an L3 input that no L2 change note currently lists. Kāla files are not touched here; the owner of the Kāla spec (SAMĀPTI hand-off to ṢAḌ-DARŚANA) must decide whether `undetermined`/obstructed edges should be excluded in Kāla by a different test |
| E-4 | `src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts:1195-1210` | selects `e.cancelled_flag`, `e.valence`, `e.edge_type` and others (not `relationship_class`); passes them to the caller; `valence_filter` normalises via `VALENCE_ALIASES` (`:106-113`: harmonious / antagonistic / neutral and the D4 aliases) | served value changes from true to false for the 10 rows; a new `valence` word is not in `VALENCE_ALIASES` and would pass through un-normalised (a served-descriptor change, so the capability census regenerates; PR #2984's file) |
| E-5 | `platform-mcp/src/tools/registry_bridge.ts` (`get_cgm_subgraph`, around `:3598-3600`) and `src/lib/retrieval/synergy/orchestrator.ts:363-368` | wrappers over E-4 | pass-through |
| E-6 | `scripts/validate_data_plane_l2_contract.py:183` | asserts the text of `bo_karanajala.py` contains `%(cancelled_by_jsonb)s::jsonb`, `cancelling_roots`, `original_polarity` (violation `cancellation_contract_missing:<token>`) | removing the cancellation payload from the writer would raise these violations. The script is **not referenced** from `.github/`, `platform/scripts/` or `package.json` in this tree, so it would fail only when run by hand; update it in the same change |
| E-7 | migration `763_bo_karanajala_integrity_check.sql:45-50, 106` (live `integrity_check_sql`) | `NOT EXISTS (... cancelled_flag = true AND relationship_class <> 'argala_virodha')` | stays true (vacuous once the flag is never set): TI-L2-39 replaces it |
| E-8 | migration `976_nirmana_l2_bo_karanajala_output_digest_spec.sql:65` | `cancelled_flag` is a value column of the `bodha_cgm_edges` digest | the digest moves with the values; re-state only if the column set changes |
| E-9 | tests: `tests/l2/test_bo_a2_fixes.py:376` (flag false for a positive argala), `:433-441` (asserts `cancelled_flag is True` and the payload for Saturn-on-Sun); `services/ka_kshetra/tests/test_stage2_promise.py:357` (fixture) | assert today's semantics | `:433-441` must be rewritten |
| E-10 | stored copies: `platform-mcp/src/resources/vidhi/dossier_slices/{career,wealth}_{482012f1,1c826d5a}.json` hold the served vocabulary lists for `edge_type` and `relationship_class` (including `argala`, `argala_positive`, `argala_virodha`); `evals/omega7/harness_runs*/DC-*.json` hold served edge rows with `cancelled_flag` | static snapshots | stale after a vocabulary or flag change; not consumers of a live value |

Edge-table readers examined and **not** affected (they read `bodha_cgm_edges` but never select argala edges or the
flag): `bo_cgm_paths.py` (dispositor edges), `bo_cgm_motifs.py:803-816` (loads all edges, uses only dispositor /
yoga_member / conjunction / aspect types), `bo_yantra_mechanism.py` (dispositor, lordship, occupancy; motif members by
edge id), `bo_drishti.py:129, :197` (`underlying_msr_signal_ids_array`, empty on argala edges), `bo_anveshana.py:338`
(`is_cross_subsystem = TRUE`; argala is `False`), `ph_phaladesa.py` (names the table in a docstring, no query),
`address_resolver.ts` (comment only), `graha_portrait.ts:90` (a fencing label). Fixtures that only contain the word
(`flip_detector/hooks_old_schema/argala.json`, `dens_scan_inputs_2026-10-02.json`) are not readers.

## Findings for SS / the batch (nothing built here)

1. **E-3 is the one cross-layer consequence**: the Kāla promise graph currently drops exactly the 10 cancelled edges.
   TI-L2-37's "cancelled_flag semantics for argala end" would put them back. The batch needs a decision on how Kāla
   should treat `undetermined` and obstructed argala, made with the Kāla owner, before the rebuild; otherwise the L2
   rebuild silently changes an L3 input.
2. **E-2 has two couplings**: the payload conjunct goes vacuous, and the valence closed set must match wherever
   `undetermined` is stored. TI-L2-38 should say which column carries `undetermined`.
3. **E-6 and E-9 are code that encodes the old semantics** and move with TI-L2-37; E-6 is not wired into CI, so it
   would not catch the change.
4. The L1 canonical vocabulary excludes `obstructed` (no strength basis), so after the change `cancelled_flag`
   would be false on every argala edge. The 10 live `true` rows are therefore the whole measurable effect of the flag
   removal on this chart.

## Limits

Reader list by text search for `cancelled_flag`, `cancelled_by_jsonb` and for `bodha_cgm_edges` / `argala` in code,
migrations, tests and stored files; readers outside this repository, and a reader building the column name
dynamically, would be missed (none seen). Counts are a live reading and move at the next rebuild. Queries:
`ti_l2_40_queries.sql`.
