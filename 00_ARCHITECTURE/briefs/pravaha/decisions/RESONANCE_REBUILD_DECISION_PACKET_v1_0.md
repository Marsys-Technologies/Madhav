---
artifact: RESONANCE_REBUILD_DECISION_PACKET
version: "1.1"
status: "READY FOR NATIVE — 2026-10-01 native decision: the §1 snapshot is a CERTIFIED FILE BACKUP (no reachable role can CREATE in schema public); the steward took it read-only (certificates below, unchanged); rollback is the rehearsed §4a file-mode restore (PR pending, B6.0 PART 0). The native's remaining writes: the §2 rebuild enqueue only."
date: 2026-09-30
author: Stream B (Śāstra), item B6.0
decision_needed: "Native authorises and personally executes the production resonance-map rebuild (A5.4 runbook). No agent performs any write. DECIDED 2026-10-01: certified file backup; rebuild execution delegated to the steward's one-command script with the native supplying the write credential."
---

# Decision packet — production resonance-map rebuild (R-1..R-6)

## The question, in plain language

The production **resonance map** — the table that says which chart factors each life-event
class listens to — was built before the WP3c honesty corrections. Independent review
(FABLE v3.0, finding #9 / T0-12) found that **154 of its 176 sensitive-degree targets point
at checks that came back negative** ("not_fired", "not_gandanta", …): the map claims
authority from things that are not true of this chart. The corrected writer (R-1..R-6) is
merged (#2769) and the runbook's verification layer was hardened by the merged follow-up
#2804 (mechanism_node `'resolved'` contract; M-6 stored state re-derived from operand
presence; both proven live by three new detector controls — 16 in all — in the disposable
rehearsal, counts 1/4/1 against a clean 0/0 baseline). What then remains
is the **one-time data rebuild** of the production table so the served map becomes honest.

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
   (`resonance_rebuild_R1_R6_runbook.md`, merged on main via #2769 + #2804). Consequence: the
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

**Update 2026-10-01 (native decision): §1 is now a CERTIFIED FILE BACKUP, already
taken read-only — see §"File-mode backup and rollback (v1.1)" below. The §2 rebuild and
§3 verification are unchanged.** Full text: `platform/python-sidecar/scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md`
(merged on main; 704 lines). In outline:

1. **§0 preconditions (read-only):** migration 1080 columns present (already verified);
   the `brahma-build-pipeline-job` image `fedc5ae50` carries writer FORMULA_VERSION
   `ka_gochara_resonance_v2.2` (steward-verified 2026-10-01 — the rebuild runs in the
   pipeline job, not the sidecar); render this run's statements with
   `resonance_rebuild_backup_sql.py` (fresh UTC stamp).
2. **§1 snapshot (your write, storage only):** `CREATE TABLE
   gochara_resonance_map_snap_482012f1_<stamp> AS SELECT * … WHERE chart_id=…`, then record
   the preimage certificate of live and snapshot and confirm they are EQUAL and count > 0.
   Baseline counts as measured above (765 rows; 154/176; digests above).
3. **§2 rebuild:** enqueue an asset-scope rebuild of `ka_gochara_resonance` for the chart
   through the governed pipeline (build_runs row, `scope='asset'`, `action='rebuild'`,
   `plan.asset_ids=["ka_gochara_resonance"]`; the normal Cloud Run job path). Capture the
   writer's `WriterResult.notes` JSON into the evidence file.
4. **§3 verification (read-only):** every MUST in the merged runbook, by name —
   **R-1** 0 negative-result/out-of-vocabulary sensitive targets, its positive control
   (kept rows > 0 and equal to the positive-fact count), and the class-associated
   ayanāṃśa-pinned R-1 identity (both EXCEPT directions 0);
   **chart-scoped TEXT fact-ref resolution:** 0 NULL/malformed/dangling refs;
   **R-6** every row a valid stored state and the partition non-empty;
   **R-2** arudha rows > 0, all keyed to this chart's `fact_key='sign'` facts, and the
   class-associated R-2 identity (both directions 0);
   **R-3** yoga rows > 0, 0 refs unbacked by a live fired firing, and the
   class-associated R-3 identity (both directions 0);
   **R-4** lord rows > 0 and all `'resolved'`, the ALL-lord identity (both directions 0);
   **R-5** afflicted-lord qualifier identity (both directions 0);
   **value invariants:** 0 rows violating the writer's declared weight/provenance/state/
   qualifier invariants, including the #2804 additions — the mechanism_node weight
   contract, mechanism_node `'resolved'` state, and the M-6 operand-presence state;
   **mechanism identity:** (event_class, source_rule_id) rows ≡ eligible bg_transit_rules
   (both directions 0);
   **post-rebuild content digest** recorded (a rerun MUST reproduce it).
   Where this outline is shorter, the runbook text is authoritative.
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

**Option 1: execute.** #2769 and #2804 are merged, and the `brahma-build-pipeline-job`
image `fedc5ae50` carries `ka_gochara_resonance_v2.2` (steward-verified 2026-10-01).
The steward re-measured the read-only certificates 2026-10-01: **unchanged** — full-row
preimage certificate `(765, 3d270ef0a2db00b240a2acb4d45171c0)`, 765 rows all
`'resolved'`, 176 sensitive_degree (the baseline above stands). Re-run the §1
certificate as part of the snapshot step, substitute the fresh stamp, and proceed.
Expected wall time: minutes for the snapshot, one governed build for the writer,
minutes for §3 verification.

## File-mode backup and rollback (v1.1, 2026-10-01)

**Why:** the §1 snapshot cannot be a table — data-plane hardening leaves no reachable
role that can CREATE in schema public (even Cloud SQL `postgres` gets `permission denied
for schema public`). The native chose a **certified file backup**.

**Already taken (read-only, steward):**
`/Users/Dev/pravaha/run/backups/gochara_resonance_map_482012f1_20261001071822.jsonl`
(+ `.sha256`), mirrored to `gs://gochara-century-stream/backups/resonance_map/`. 765
lines, one `row_to_json(t)::text` per row ordered by id; **the md5 of the lines joined
by `\n` = `3d270ef0a2db00b240a2acb4d45171c0` = the DB preimage certificate exactly** —
the file and the live partition are comparable byte-for-byte, and the pair above
re-verified equal to the live §1 certificate on 2026-10-01.

**Rollback (runbook §4a):** `resonance_restore_from_file.py` (B6.0 PART 0) — verifies,
before any DELETE, the file's sha256 against its sidecar, the line count and joined-md5
against the recorded pair, and that every row belongs to this chart; then in ONE
transaction deletes the chart's partition, inserts each row via
`json_populate_record(NULL::gochara_resonance_map, line)` keeping the exact ids,
recomputes the live full-row certificate and ROLLS BACK unless it equals the recorded
pair, and proves every other chart's certificate unchanged. DSN from the environment
only (`RESONANCE_RESTORE_DATABASE_URL`, the data_plane_builder role); default dry-run
(full procedure, then deliberate rollback); `--execute` commits. Rehearsed on a
disposable PG against the migration-derived schema: success reproduces the certificate;
tampered-file, truncated-file, wrong-chart-line, digest-mismatch and sha-mismatch
controls each refuse with the live partition provably untouched.

**Consequence for this packet:** the only remaining production writes are the §2 rebuild
enqueue and the rebuild itself. Execution is delegated to the steward's one-command
script with the native supplying the write credential (steward note 2026-10-01).
