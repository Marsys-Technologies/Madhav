---
artifact: RESONANCE_REBUILD_DECISION_PACKET
version: "1.0"
status: READY FOR NATIVE (awaiting PR #2769 merge; pre-counts measured 2026-09-30)
date: 2026-09-30
author: Stream B (Śāstra), item B6.0
decision_needed: "Native authorises and personally executes the production resonance-map rebuild (A5.4 runbook). No agent performs any write."
---

# Decision packet — production resonance-map rebuild (R-1..R-6)

## The question, in plain language

The production **resonance map** — the table that says which chart factors each life-event
class listens to — was built before the WP3c honesty corrections. Independent review
(FABLE v3.0, finding #9 / T0-12) found that **154 of its 176 sensitive-degree targets point
at checks that came back negative** ("not_fired", "not_gandanta", …): the map claims
authority from things that are not true of this chart. The corrected writer (R-1..R-6) is
already merged and reviewed; what remains is the **one-time data rebuild** of the production
table so the served map becomes honest.

Only you can do this: it is a production write, explicitly native-only. This packet gives
you the measured current state, what the rebuild will change, the exact commands, and the
verified rollback.

## The evidence (all read-only, measured today against production)

Chart `482012f1-710e-4a25-994a-93821f5871aa`, table `gochara_resonance_map`:

- **Partition size: 765 rows.** Full-row preimage certificate
  (count, md5 over `row_to_json` ordered by id): `(765, 3d270ef0a2db00b240a2acb4d45171c0)`.
- **By type:** sensitive_degree 176, yoga_constituent 220, mechanism_node 93, arudha 68,
  bhava 68, lord 52, karaka 44, dasha_lord_portfolio 44.
- **Finding-#9 baseline: 154 of 176** sensitive-degree rows key to negative-result
  `sensitive_degree_check` facts (predicate: `fact_value_text IN
  ('not_fired','not_gandanta','not_pushkara','none') OR NULL OR NOT IN
  ('fired','gandanta','papa_kartari','shubha_kartari','pushkara')`). Only **22** key to
  positive results. Matches the sealed figure exactly.
- **Reference integrity (pre-state): 244 rows** have a NULL, malformed, or dangling
  `target_ref` (NOT EXISTS against `chart_facts`) — the class the rebuild's R-2/R-3
  reference checks drive to 0.
- **Every one of the 765 rows currently claims `target_resolution_state = 'resolved'`** —
  including the 154 negative-keyed ones. That is the dishonesty the rebuild removes.
- Precondition already true in production: migration 1080's columns
  (`target_resolution_state`, `target_qualifier` + CHECK) exist (verified above).
- ID-independent content digest of the current partition (for rerun comparison only):
  `(765, 8b6b5e158ab246c76931f4374aeefea9)`.

## The options

1. **Rebuild now (recommended).** Run the A5.4 runbook
   (`resonance_rebuild_R1_R6_runbook.md` on PR #2769) once #2769 merges. Consequence: the
   154 negative-keyed rows and the 244 dangling/mis-keyed refs are replaced by an honestly
   keyed map whose every row carries a real resolution state; the postconditions in §3 of
   the runbook MUST all hold (0 negative-keyed rows, identity of the kept set with the
   positive-fact set, 0 dangling refs, per-type positive controls) or the rebuild did not
   happen. Until this runs, every downstream score that reads the map inherits the
   pre-WP3c dishonesty.
2. **Defer.** Keep serving the dishonest map. Consequence: finding #9 stays open; the
   campaign's own doctrine (F-32, no rule without the count) is violated by the served
   product; B4.x scoring of any generation that consumes the map inherits the defect.
3. **Partial rebuild (per-type).** Not offered by the runbook; the writer is per-chart
   delete-then-insert inside one transaction. Rejected as needless surgery.

## The exact commands (governed path, you execute)

Full text: `platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md`
(PR #2769; 351 lines). In outline:

1. **§0 preconditions (read-only):** migration 1080 columns present (already verified
   today); deployed sidecar image carries writer FORMULA_VERSION
   `ka_gochara_resonance_v2.2`; render this run's statements with
   `resonance_rebuild_backup_sql.py` (fresh UTC stamp).
2. **§1 snapshot (your write, storage only):** `CREATE TABLE
   gochara_resonance_map_snap_482012f1_<stamp> AS SELECT * … WHERE chart_id=…`, then record
   the preimage certificate of live and snapshot and confirm they are EQUAL and count > 0.
   Baseline counts as measured above (765 rows; 154/176; digests above).
3. **§2 rebuild:** enqueue an asset-scope rebuild of `ka_gochara_resonance` for the chart
   through the governed pipeline (build_runs row, `scope='asset'`, `action='rebuild'`,
   `plan.asset_ids=["ka_gochara_resonance"]`; the normal Cloud Run job path). Capture the
   writer's `WriterResult.notes` JSON into the evidence file.
4. **§3 verification (read-only):** every MUST in the runbook — 0 negative-keyed rows;
   kept-set ≡ positive-fact set (both EXCEPT directions empty); 0 NULL/dangling refs;
   every row carries a valid state and partition non-empty; arudha/yoga/lord positive
   controls; R-5 afflicted-lord identity both directions empty; record after-counts and the
   new content digest.
5. **§4 rollback (refuse-unless-verified):** restores the exact §1 preimage from the
   snapshot table; refuses before any DELETE if the snapshot is absent, empty, foreign, or
   certificate-mismatched; re-verifies after restore. The block was rehearsed
   (`resonance_rebuild_disposable_rehearsal.py`, acceptance block fails on any violated
   postcondition) and is held byte-for-byte by `tests/l3/test_resonance_rebuild_rehearsal.py`.

## What the rebuild deliberately does NOT do

No flip, no serving-authority change, no tracker writes, no L1 re-derivation (stale L1
inputs surface as honest `unavailable` states — data for the LEL/T0-13 pass, not defects
patched here). Rollback restores the pre-WP3c rows and is a pause for diagnosis, never an
end state.

## Recommendation

**Option 1, immediately after #2769 merges and CI is green.** The pre-counts above are the
§1 baseline already measured; on merge day, re-run the two certificate queries, substitute
the fresh stamp, and proceed. Expected wall time: minutes for the snapshot, one governed
build for the writer, minutes for §3 verification.
