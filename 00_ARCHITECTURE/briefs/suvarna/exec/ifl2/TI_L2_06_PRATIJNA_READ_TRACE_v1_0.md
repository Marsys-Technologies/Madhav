---
version: 1.0
status: CURRENT
lane: TI-i-fl2-005
item: TI-L2-06 (Q-L2-07: trace the two reads the brief missed; research half only)
branch: suvarna/land/TI-i-fl2-005
basis: origin/main adb0db29d; production DB read 2026-10-03, reader-only SELECT
changelog:
  - 1.0 -- trace of chart_fact_identity and "brahma_reference_planets" for bo_pratijna; finds that chart_fact_identity has no producing asset and is nearly empty for the canonical chart. Evidence only.
---

# TI-L2-06: what does `bo_pratijna` really read, and who produces it?

SS ruling Q-L2-07 (N-59): the two declared-but-unread L2 edges of `bo_pratijna` (`bo_laksana`,
`bo_sangati`) are replaced by direct L1 edges "only after the two untraced reads
(`chart_fact_identity`, `brahma_reference_planets`) are traced; first-pass set `ga_vargas`,
`ga_positions`, `ga_structural`, `ga_sensitive`". This is the trace. The registry edit itself (a
migration) is not built here.

## Answer in four lines

1. **`brahma_reference_planets` does not exist.** The `bo_pratijna.py:153` docstring names it; the code reads
   `reference_planets` (L0 static table, `chart_reader_v4.py:455, 462`; `bo_pratijna_v4_engine.py:830`),
   written by the registered L0 asset `bg_reference` (`depends_on = {bg_ontology}`). It is a bedrock
   table: migration 1210's scope rule (header lines 11-13) deliberately adds no edge for bedrock reads.
2. **`chart_fact_identity` has no producing asset.** It is filled only by the standalone script
   `platform/python-sidecar/scripts/build_fact_identity_index.py` (header: "standalone (NOT a
   `WriterBase`/`@register` orchestrator writer)"), run by hand per chart. No registry row, no dispatch,
   no CI call. A DAG edge cannot name it.
3. **On the canonical chart it is almost empty**: 1,205 of 143,299 `chart_facts` rows (0.84%) have an
   identity row, all of kinds `graha` (845) and `house` (360), none of `graha_in_varga` or any
   varga-tagged kind; the other canonical chart `1c826d5a` has 125,873 of 139,717 (90.1%) across 17
   kinds. The 1,205 rows are one build (`1c092ffb`, 2026-09-07); the chart's facts are 10 builds
   (2026-09-07 to 2026-09-08). `chart_fact_identity.fact_id` is `ON DELETE CASCADE`, so a rebuild of
   `chart_facts` deletes the index rows of every replaced fact, and nothing re-creates them.
4. **The visible effect is a silent hole in the derivation ledger, not (by code reading) in the grade.**
   `bodha_pratijna.derivation.provenance` on 482012f1 cites 150 `fact_id` entries, all
   `bhava_cusps/sripati_madhya`; on `1c826d5a` (same 135 rows) it cites 445: those 150 plus **295
   `graha_dignity_per_varga/dignity_state`**. The 295 come from the identity-joined dignity attach in
   `ChartReaderV4.lord_of` (`chart_reader_v4.py:308-326`); with no identity rows the join returns
   nothing and the reader simply omits the L1 dignity fact link (`dignity_state` stays None). The engine
   computes its own dignity from positions (`bo_pratijna_v4_engine.py:886-905`) and uses only
   `lord_info["lord"]` and `["provenance"]`, so the grade is not changed by this reading of the code;
   the provenance (CLAUDE.md B.3, N.5) is.

## What the engine actually executes (the per-category audit, closed)

| read | source | executed by the engine | producing asset | edge status today |
|---|---|---|---|---|
| `chart_divisionals` (D1 occupants / signs / lords, D9) | `chart_reader_v4.py:186, 214, 247, 297, 500` | yes (`occupants`, `sign_of`, `lord_of`) | `ga_vargas` | declared (added by 1210) |
| `chart_facts` `bhava_cusps/sripati_madhya` | `chart_reader_v4.py:268-272` | yes (`lord_of`, house to sign) | `ga_positions` (`ga_positions_writer.py:468`) | not declared (1210 drops chart_facts-only edges) |
| `chart_facts` `graha_dignity_per_varga/dignity_state` joined through `chart_fact_identity` | `chart_reader_v4.py:312-319` | yes (provenance attach only) | `ga_structural` (`ga_structural_writer.py:5317`); index: **no asset** | n/a for the index |
| `reference_planets` | `chart_reader_v4.py:455, 462` | yes (`reference_planets()`) | `bg_reference` (L0 bedrock) | no edge by 1210 rule (b) |
| `chart_facts` aspect families (`aspect_parashari_given`, `_per_varga`), `graha_in_varga` identity rows, `special_points` (upapada / special_lagna / karaka) | `graha_state`, `aspect_between`, `special_points` | **no**: no caller outside tests | `ga_structural` / `ga_sensitive` | not needed |
| `bodha_msr_signals` | none | **no**: `supporting_signal_ids` / `contradicting_signal_ids` are always NULL (`bo_pratijna.py:132-134`, `:372-373`) | n/a | `bo_laksana`, `bo_sangati` edges are unread |

So of the "first-pass set" the engine really reads `ga_vargas` (declared) and `ga_positions`
(soft, chart_facts only); `ga_structural` only through the identity-joined provenance attach;
`ga_sensitive` not at all on the executed path.

## Consequences for the Q-L2-07 plan (for SS; nothing is built here)

* Replacing `bo_laksana, bo_sangati` by direct L1 edges is sound for `ga_vargas` (already present) and
  is optional for `ga_positions` (a chart_facts-only read is satisfied by any producer in the closure,
  per 1210's own rule). `ga_sensitive` has no executed read and would be an unread edge, the same
  defect the ruling is removing.
* **The real hidden dependency cannot be expressed as an edge.** `chart_fact_identity` is a derived,
  non-bedrock table with no asset. Until SS rules, `bo_pratijna`'s ledger completeness on a chart
  depends on a manual script having been run after the last `chart_facts` rebuild. Options (not chosen
  here): (a) register an asset for the identity index (a writer plus a migration; contract-conformant,
  new asset); (b) drop the identity join from `ChartReaderV4.lord_of` and read the dignity fact
  directly by `(chart_id, ayanamsha, fact_subject = '<varga>_<graha>', fact_category, fact_key)` (code
  change, rebuild of `bo_pratijna`, and it makes the provenance independent of a hand-run script);
  (c) document the pre-step and add a detector. (b) removes the hazard without a new asset.
* Any rebuild of `bo_pratijna` on 482012f1 before this is settled reproduces the 150-entry ledger.
  A one-chart run of the script would restore the other 295 entries but is itself a data write and not
  part of this lane.

## What was run / not done

Reader-only SELECTs (`ti_l2_06_queries.sql`); code read at origin/main adb0db29d. Not done: the registry
migration (needs a number from SS), the reader change, the script run, any `bo_pratijna` rebuild. The
effect on `grade` was established by reading the engine, not by re-running it.
