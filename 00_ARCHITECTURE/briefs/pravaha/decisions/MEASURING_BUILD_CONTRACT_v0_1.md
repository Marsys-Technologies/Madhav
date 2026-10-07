---
artifact: MEASURING_BUILD_CONTRACT
version: "0.1"
status: DRAFT CONTRACT for the steward — authorises nothing; decides nothing that is the owner's
date: 2026-10-06
scope: the ONE unsealed measuring build (run shape `all_classes_full`) of ka_gochara_v5 for chart 482012f1-710e-4a25-994a-93821f5871aa, generation `5.0`, horizon 1998-01-01 → 2084-02-05, today's rules; nothing else
closes: the six "prerequisites for the measuring build" of ASTRA_REVIEW_FINAL_BUILD_SCOPE_v1_2.md (its last table) — and nothing more
code_anchor: origin/main 091362f315a2d2f7e9c44cc205aac54440c8f6a9 (2026-10-05); in-flight branches named where read
abbreviations: W = platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py · K/ = platform/python-sidecar/services/gochara_kernel/ · AR = …/orchestrator/asset_runner.py · RN = …/orchestrator/runner.py · M/ = platform/migrations/ · MR = K/measuring_report.py on origin/pravaha/b11-measuring-verifier (head 2bfdb1c7b) · TD = platform/scripts/teardown_v5_small_test_job.py on origin/pravaha/c38-v5-smalltest-teardown (PR 3098) · DP = platform/scripts/dispatch_v5_small_test_job.py on origin/pravaha/c37-v5-smalltest-dispatch (PR 3097) · CK = runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md v1.7 · TR = V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md v1.2 (c38 branch) · EP = measurement/EVALUATION_PROTOCOL_v2_3.md · FBS = decisions/FINAL_BUILD_SCOPE_v1_0.md v1.2 · FAB = reviews/FABLE_REVIEW_FINAL_BUILD_SCOPE_v1_1.md · AST = reviews/ASTRA_REVIEW_FINAL_BUILD_SCOPE_v1_2.md
---

# Measuring build — contract v0.1

## 0. What this is

One UNSEALED build on production, for the pinned chart only, in the existing test-slice mode (steward MEASURING_BUILD_RULING item 1: "a THIRD SHAPE of the existing test-slice mode, not a new mechanism"): a validated `gochara_v5_test_slice` marker in `build_runs.plan_manifest` (W:160-176, 206-263), run `all_classes_full` beside the existing `all_classes_1y` / `one_class_full` (W:173), all 26 scored classes over 1998-01-01 → 2084-02-05 under the rule versions bound on main today (`BOUND_PATH_REFS` = 1.0.0, FBS FB-30), stamped `stored_scope = 'test_slice'` (W:174, 386-392) so the verification job (K/verification_job.py:175-183), publication (K/ledger.py:623-636, 741-742) and everything downstream refuse it by name; near-misses reported, not raised (W:1046-1060); results read from the database and the job log (CK:118-145); removed afterwards by the reviewed teardown (TD). It MEASURES: timings per phase and class, admitted-day share per class and path, counts of near-misses, seams, 0/360 wrap cases, UNRESOLVED stretches, and it captures regression evidence before teardown.

Every clause below has (i) the rule, (ii) refusals by name, (iii) an acceptance test that FAILS if the clause were false, (iv) the implementer: **A** = Stream A (builder: W, DP, TD), **B** = Stream B (verifier: MR and its tests), **S** = steward (sitting). Where FAB and AST disagree, AST is followed where it corrected FAB and this is said; where the code contradicts either review, the code is followed and cited.

Stream A's measuring-build branch (`a-mb-horizon`, tracker 2026-10-05) is NOT on origin: every A-clause here specifies what it must do. Stream B's side IS on origin (MR); §10 lists where it already departs from this contract.

## 1. MB-1 — HORIZON

**MB-1.1 The ruled horizon (rule).** For the pinned chart the owner approved START = 1998-01-01, END = 2084-02-05 (OWNER_RULING_13.txt, point 2). The owner's verbatim rule (Ruling 7, FBS FB-1): start = the first event of the person's life event log if a log exists, else the rebuild date; end = birth + 100 years. The build horizon is the half-open instant pair `[1998-01-01T00:00Z, 2084-02-05T00:00Z)` — calendar dates rendered as UTC-midnight instants, the same convention as `DEFAULT_HORIZON` today (W:157-158) and the dispatch's `+00:00` timestamps (DP:73-79). (The protocol's IST 18:30-UTC day anchor, EP §3, is NOT applied to the build horizon; OS-3.) Day counts are half-open: 31,446 build-horizon days (MR test `H_DAYS`, re-derived here: 86×365 + 21 leap days + 35).

**MB-1.2 The detector over REAL `life_events` rows (rule; A implements `derive_chart_horizon`, B implements its own `MR.derive_chart_horizon_detail`; neither imports the other).** The table is `public.life_events`: baseline columns `event_id TEXT UNIQUE, event_date DATE, category TEXT, description, significance, chart_state, source_section, build_id, provenance` (M/001_baseline.sql:463-474); shape columns `shape ∈ {point, interval, chain}`, `date_confidence ∈ {exact, month_known, year_only}`, `interval_start, interval_end DATE`, `chain_parent_event_id TEXT`, `milestone_label`, `date_tightened_at` (M/457_lel_schema_v2_event_shapes.sql:19-45); and a per-chart key `chart_id uuid NOT NULL REFERENCES charts(id)` (platform/supabase/migrations/423_ba_lel_r2_2_step1_chart_scope.sql:19-20; the MCP writer upserts `ON CONFLICT (chart_id, event_id)`, platform/src/lib/mcp/lel_event_writer.ts:171-179, and also writes `event_type`, `domain`). **Code over review:** FBS FB-1 and FAB 1.3 say the table carries no `chart_id` (citing the comment at M/958:75); migration 423 says it does. The detector reads `WHERE chart_id = <pinned chart>`. Not verified live: that production carries 423's column (R-LEL below proves it or refuses).
Inputs: `birth_date` = the civil date of `ctx.config['birth_params']['datetime_iso']` in its own offset (AR:1114-1122; …/orchestrator/birth_params.py:105-111) = 1984-02-05; `build_date` = the UTC date of the dispatch (`build_runs.created_at`).
1. END = `birth_date.replace(year + 100)`; refuse `horizon_birth_anniversary_undefined` if the day does not exist (29 February).
2. Rows = every row of the chart. ZERO rows ⇒ basis `build_date` (the owner's "else"). Otherwise the BIRTH ROW is the unique row with `event_date = birth_date` AND whose birth word (OS-1: the column is pinned from readback R-LEL — `category`, `event_type` or a `provenance` key — the YAML source has `category: other, subcategory: birth`, 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:146-150) equals `birth`; zero or several ⇒ refuse `lel_birth_row_unidentifiable`. It is set aside, never counted.
3. FULLY DATED = `date_confidence = 'exact'`. The event's date is the row's own `event_date` for EVERY shape — the most literal reading of "the first event" (each log entry carries one `date:`); `interval_start` and the chain root are NOT consulted for the choice (OO-2: FBS FB-55 reads `interval_start` / chain root; MR reads `interval_start` and refuses chains; this contract takes the literal row date and makes the choice CHECKABLE, item 6). `month_known`/`year_only` rows open nothing (their `event_date` is a proxy such as YYYY-07-01, FBS FB-1). Unknown words ⇒ `lel_date_confidence_unknown`, `lel_shape_unknown`; an exact row with NULL `event_date` ⇒ `lel_date_missing`.
4. START = 1 January of the year of the earliest fully dated non-birth row, basis `first_dated_event`; none ⇒ `build_date`, basis `build_date`.
5. START-side refusals (FAB 1.3/4.6, AST 1.3 — added by both; MV_FABLE_1 P1-1 ruled them): `horizon_empty` (start ≥ end); `horizon_start_before_birth`; `horizon_start_before_substrate_domain` (start < 1998-01-01, K/substrate.py:170); `horizon_start_in_future` (start > build_date). END-side: `horizon_outside_substrate_domain` (end > 2085-01-01, K/substrate.py:171). Never clipped.
6. SHAPE-SENSITIVITY CHECK: the detector also computes START under the two other readings (interval_start for intervals; chain-root `event_date` for chains, a cycle or missing parent ⇒ `lel_chain_unresolvable`); if any reading gives a different START ⇒ refuse `lel_shape_reading_sensitive` (the owner's open point would then change the build; OO-2). For the pinned log the three coincide (the earliest exact row is EVT.1998.02.16.01, a point; the 1993/1995 rows are year_only — LIFE_EVENT_LOG_v1_2.md:179-180, 212-214; event_registry_v2_3.json rows EVT.1993.XX.XX.01, EVT.1995.XX.XX.01/02 `pre-horizon`). Not verified live.
7. RULING GUARD: for `PINNED_CHART_ID` (W:457) the derived pair must equal the ruled pair of MB-1.1; else refuse `horizon_derivation_disagrees_with_ruling` at PLAN time (a log change before the build surfaces as a refusal, never a silently different build).

**MB-1.3 Where the horizon lives in the build (A).** `all_classes_full` marker: `classes` = all 26 scored classes, `horizon` = the derived pair; the writer's `_validate_test_slice` (W:318-361) gains the shape: all classes (as `all_classes_1y`, W:346-349) AND `horizon == derive_chart_horizon(...)` (else `TestSliceRefusal`); the outer bound of `_parse_slice_horizon` (W:312-314, today `DEFAULT_HORIZON`) and the `one_class_full` rule (W:355) become the derived horizon (FBS FB-2/FB-4). The dispatch (DP:225, 345) gains `--run all_classes_full` (no horizon flags; it derives the same pair with the writer's function and prints it in the dry run). `_require_manifest_horizon` (W:560-579) and the manifest `tstzrange` (W:904-908) are unchanged.

**MB-1.4 Evidence pinned so a verifier can RE-DERIVE after the live log changes (A pins, B reads).** The manifest's input vector (W:879-891; `assemble_vector`, K/input_vector.py:469-481) gains `horizon_basis` = `{schema: "horizon_basis/1", rule: "ruling7+ruling13", birth_date, build_date, basis, chosen: {event_id, event_date, date_confidence, shape} | null, birth_row: {event_id, column_used} | null, consumed_rows: [ {event_id, event_date, date_confidence, shape, interval_start, interval_end, chain_parent_event_id} for EVERY row of the chart, sorted by event_id ], consumed_rows_digest: sha256 of the canonical JSON of consumed_rows, excluded_not_fully_dated: n, readings: {event_date: start, interval_start: start, chain_root: start} }`. The CONSUMED ROWS THEMSELVES are pinned (AST P1-2: a digest cannot reconstruct the selection), ~60 rows × 7 fields. Because the candidate is torn down, the same object is exported to the capture of MB-3 before teardown.

**MB-1.5 Drift rule (B).** The verifier re-derives START/END from `horizon_basis.consumed_rows` ALONE and compares with the manifest horizon (`horizon_mismatch` is a refusal, MR `measuring_refusals`). It then reads the LIVE log and re-derives again: a difference (rows added/removed/tightened, a different START) is `lel_drift`, a REPORT LINE naming the differing event_ids — for a test-slice build never a gate (FBS FB-2 drift rule, retained).

**Refusals (named):** horizon_empty · horizon_start_before_birth · horizon_start_before_substrate_domain · horizon_start_in_future · horizon_outside_substrate_domain · horizon_birth_anniversary_undefined · lel_birth_row_unidentifiable · lel_date_confidence_unknown · lel_shape_unknown · lel_date_missing · lel_chain_unresolvable · lel_shape_reading_sensitive · horizon_derivation_disagrees_with_ruling · horizon_mismatch (verifier) · TestSliceRefusal on a marker horizon ≠ derived.

**Acceptance tests (each fails if the clause were false):**
- T1.1 (A, B, pure): real-column fixture rows (birth row 1984-02-05; year_only 1993-07-01 and 1995-07-01; exact point 1998-02-16; later exact rows) ⇒ `(1998-01-01, 2084-02-05, first_dated_event)`, excluded = 2. Reordering the rows changes nothing. Removing the 1998 row ⇒ START 1 January of the next exact row's year.
- T1.2 (A, B): each refusal above produced by exactly one mutation of the fixture (1983-05-01 exact ⇒ before_birth; 1990-05-05 ⇒ before_substrate_domain; 2030 ⇒ in_future; birth 2000-02-29 ⇒ anniversary_undefined; two birth rows / none ⇒ unidentifiable; `date_confidence='circa'` ⇒ unknown; exact interval with `interval_start` 1996-01-01 and `event_date` 1998-06-01 ⇒ `lel_shape_reading_sensitive`).
- T1.3 (A): a marker with horizon `(1998-02-16, 2084-02-05)` or the old `DEFAULT_HORIZON` end is refused by name; the derived pair validates; `all_classes_full` with 25 classes is refused.
- T1.4 (B, DB): a stored manifest whose `horizon_basis.consumed_rows` re-derive to a different pair than the stored `horizon` ⇒ `horizon_mismatch`; a live log with the 1995 row tightened to exact after the build ⇒ `lel_drift` reported, acceptance unchanged (FBS FB-55 oracle, soft half).
- T1.5 (S, read-only, pre-dispatch) **R-LEL**: `SELECT event_id, event_date, category, event_type, shape, date_confidence, interval_start, interval_end, chain_parent_event_id, provenance ? 'subcategory' FROM life_events WHERE chart_id = '482012f1-…' ORDER BY event_date, event_id;` — proves the 423 column exists, shows which column carries `birth`, and shows the first exact row is in 1998. Output saved verbatim; the birth-word column is then pinned as a constant in BOTH sides (OS-1) before dispatch.

## 2. MB-2 — STRUCTURED SINK (near-misses, unresolved, seams, wraps, clipped)

**MB-2.1 Today (fact).** Under a validated slice the in-build certifier is handed `graze_sink` (W:1049-1052); `compare_contact_sets` appends a dict per graze and drops it from the omission check (K/contact_certify.py:185-196); the writer renders them into ONE free-text note and ONE `logger.warning` line `GRAZES REPORTED, NOT RAISED (validated test slice; N): …` (W:1054-1060) that reaches the job log via `_log_verify_outcome` (W:364-376); the runner never reads notes (CK:12). Nothing is stored. `classify_graze` returns `None` in SIX cases, not three (AST P1-6 corrects FAB 1.4/FBS FB-56): non-point target or relation (K/contact_certify.py:126-127); extension not settled (:142-143 via `_full_stretch` :99-100, :105); a real crossing detected (:154-155); no-crossing not proved (:156-157); no sampled level within orb (`best is None`, :161); closest approach below `GRAZE_MIN_APPROACH_DEG = 5e-3` (:67, :161-162).

**MB-2.2 Record shape (rule; A emits, B recounts).** One JSON object per record:
`{schema: "stretch_sink/1", record_id, kind, reason, event_class, body, relation, canonical_target, level_deg, orb_deg, horizon_interval: [t_in, t_out], full_interval: [A, B] | null, clipped_by_horizon: [] | ["start"] | ["end"] | ["start","end"], closest_approach_deg | null, closest_approach_at | null, peak_activity | null, episode_count | null, detail}`.
`record_id` = uuid8 (K/substrate.py:46-55) over `"stretch_sink/1|{kind}|{body}|{relation}|{canonical_target}|{orb_deg}|{horizon_lo}|{horizon_hi}|{stretch_ordinal}"`, where `stretch_ordinal` is the 1-based position of the stretch among the obligation's in-band stretches over the horizon ordered by `t_in` (`band_intervals`, K/contact_reconstruct.py:136-158, is deterministic to `BISECT_SECONDS = 1.0`, :29) — stable under input order and under sub-second jitter; the horizon is in the bytes because ordinals are horizon-relative.
Closed lists:
| kind | reason (closed) | code path |
|---|---|---|
| near_miss | certified_positive_clearance | classify_graze returns a dict (:163-170) |
| unresolved | clearance_below_min_approach | :161-162 |
| unresolved | extension_unsettled (detail: `ambiguous_extension` :99-100 / `exceeds_1500_days` :105) | :142-143 |
| unresolved | no_crossing_unproved | :156-157 |
| omission | crossing_detected (a real root the builder did not mint) | :154-155 |
| omission | unsupported_target (span/residence interval with no ledger contact) | :126-127 |
| anomaly | no_relevant_level (no ray within orb of the sampled interval) | :161 `best is None` |
| seam | multi_episode_stretch (`episode_count` ≥ 2 ledger episodes inside one reconstructed stretch) | the union step :200-203 |
| wrap | ray_band_contains_wrap_cut (`min(level, 360−level) ≤ orb`), detail `body_wrapped_inside: bool` | WRAP_CUT_EVIDENCE_20261005.txt:11-12 definition |
| horizon_clipped | clipped_at_start / clipped_at_end / clipped_both | :138-146 |
A stretch may yield several records (e.g. seam + wrap + horizon_clipped), each with its own `record_id`. `omission` and `anomaly` records are emitted BEFORE the certifier raises (OS-6: an omission is a builder defect and still fails `verify:<class>`; only near-misses are "not raised", MEASURING_BUILD_RULING item 1).

**MB-2.3 Where it is stored for a test-slice build (rule, A).** Not in any table (FBS FB-56 (a): report-only). Each record is one job-log line `STRETCH_SINK/1 <json>` (WARNING for near_miss/unresolved/omission/anomaly, INFO for seam/wrap/horizon_clipped); per class one line `STRETCH_SINK_SUMMARY/1 {event_class, counts_by_kind_reason, record_ids_digest}`; the free-text `GRAZES REPORTED…` note is kept for humans. The steward exports the run's log (`gcloud logging read … --format=json`) to `/Users/Dev/pravaha/run/measuring-<date>/stretch_sink.jsonl` with its sha256 (OS-8: Cloud Logging retention is finite; export the same day).

**MB-2.4 Independent recount and "agree" (B).** The verifier recomputes the set from the ephemeris and the stored contacts of the candidate (same reads as K/contact_certify.py:224-240, read-only), with its OWN band logic pinned equal AS DATA to the kernel's: orb 1.0° (`_POINT_ORB_DEG`, K/window_verifier.py:526), aspect angles (:527-529), `VMAX_DPS` (K/contact_reconstruct.py:25-26), min-excursion 60 s, bisect 1 s, graze step 3600 s, min approach 5e-3, max extension 1500 d. AGREE = identical set of `record_id`; per id identical `kind` and `reason`; `horizon_interval` bounds within 2 s; `closest_approach_deg` within 2e-3°, `closest_approach_at` within 6 h (sampling grids differ). Anything else is a `sink_disagreement` report line listing the ids — for the measuring build a report, not a gate (AST on FAB 3.2: the two sides are cooperating routines, not independent-by-construction; FB-67's pinned accuracy object belongs to the final build).

**Refusals:** `stretch_sink_unparseable` (a line that is not the schema); `stretch_sink_summary_digest_mismatch` (records vs summary digest); `sink_disagreement` (report).

**Acceptance tests:** T2.1 (A, pure) nine stub `position_at` curves, one per reason row above (constant signed distance 0.0008° for Mercury ⇒ `no_crossing_unproved`, since 0.0016 < 2.6/86400×60; a dip to 0.002° ⇒ `clearance_below_min_approach`; a dip to 0.3° ⇒ `near_miss`; a stretch in band > 1500 d at the horizon edge ⇒ `extension_unsettled`; a sign change ⇒ `omission/crossing_detected`; a `span:` target ⇒ `unsupported_target`; two overlapping ledger episodes ⇒ `seam`; level 359.6° ⇒ `wrap`; a stretch straddling `lo` that resolves ⇒ `near_miss` + `horizon_clipped`). Each asserts kind, reason and that `record_id` is unchanged when the obligations and intervals are fed in reverse order. T2.2 (A) the log line parses back to the record; the summary digest equals sha256 of the sorted ids. T2.3 (B) the recount on the same stubs yields the same ids; moving one stub's dip by 7 h makes `sink_disagreement` fire (the detector is not vacuous). T2.4 (B, DB) a candidate with 0 near-miss store rows and N sink records ⇒ `near_miss_rows_stored` = 0 and the counts come from the sink only (MR `near_miss_counts` is a tally, MR docstring; the recount of MB-2.4 is the independent half).

## 3. MB-3 — REGRESSION EVIDENCE before teardown

**MB-3.1 What cannot be compared (fact).** `generation` is in the record's hashed natural key (K/evaluator.py:133-158: `"generation": generation` at :139; `record_uuid` :161-166), so record ids across generations differ by construction (AST P1-5 corrects FAB §11.2/FBS FB-69). Contact ids are generation-free: `hash(physical_object_id, occurrence_ordinal)` over `body|relation|target|convention_id|ordinal` (K/substrate.py:130-139), ordinals assigned over the full-domain crossing set, append-only (:142-162). Manifest, snapshot, registry and state digests change by construction in the final build (G12, G8, 1.2.0 rows, generation label).

**MB-3.2 Comparison key and fields (rule).** `gkey` = the natural key MINUS `chart_id` and `generation` (fields at K/evaluator.py:137-157: event_class, affected_person, frame, agent, relation, object_id, object_role, contact_id, path_id, rule_version, prerequisites, source_text, + period_anchor_lord/level for P1), canonical JSON, `gkey_sha256`. Compared per record: `gkey` + `admission_state` + `temporal_support_intervals` (instants). Contacts: `contact_id` + `t_in, t_out, t_exact, delta_lambda`. Windows: `(event_class, path_id, rule_version, lower(interval), upper(interval))` (M/1156_gochara_eval_window.sql:247-261).

**MB-3.3 Which classes and paths the planned final-build changes leave UNCHANGED (enumeration; AST P1-5 corrects FAB "all 18"):**
| population | expected in the final build | why |
|---|---|---|
| contacts, all obligations (98 point + span) | EQUAL ids and instants | append-only ordinals; natal-Sun targets are NEW objects (FBS FB-45) |
| 17 H-classes (the 18 with H minus bereavement): P2, P3, P4 | EQUAL | no 1.2.0 selection (FBS FB-30); K-B touches only parental_event, psychological_arc, bereavement (FB-37/FB-45) |
| 17 H-classes: P1 | EQUAL only if karakatva stays limited to the eight (OO-8 / FBS OD-6); else CHANGED (new admitted records) | FB-46 |
| bereavement: P1, P3, P4 | CHANGED (1.2.0, natal Sun) | FB-30, FB-45 |
| bereavement: P2 | EQUAL | P2 has no 1.2.0 row |
| the eight ND-H classes: P2 | EQUAL except parental_event (P2 → excluded, FB-39) | |
| the eight: P1, P3, P4 | today ZERO rows (ST-H-UNKNOWN, K/inventory.py:42, 392) → NEW; the capture records the zero | |
| manifest / snapshot / registry / state digests | CHANGED by construction | captured for information only |
The 18 H-classes: bereavement, career_advancement, career_change, career_entry, career_setback, childbirth, chronic_onset, education_milestone, exam_outcome, illness_acute, major_gain, major_loss, marriage, relocation, romantic_start, separation, surgery, travel_event (MR `SCORED_CLASSES` minus `EXCLUDED_EIGHT`).

**MB-3.4 Capture (B produces from read-only SQL; S stores).** Before teardown: `/Users/Dev/pravaha/run/measuring-<date>/golden/` with `contacts.jsonl`, `records.jsonl` (gkey, gkey_sha256, admission_state, supports), `windows.jsonl`, `horizon_basis.json` (MB-1.4), `stretch_sink.jsonl` (MB-2.3), `digests.json` (per (class, path): sha256 of the sorted `gkey_sha256` list with the fields above; per obligation: sha256 of the sorted contact rows; the informational manifest/snapshot/registry digests), and `MANIFEST.sha256` over every file. Stream B commits `digests.json` + `MANIFEST.sha256` + `horizon_basis.json` under `00_ARCHITECTURE/briefs/pravaha/measurement/fixtures/measuring_golden_<date>/` (the row files stay in the run folder; their hashes are in the manifest). **Teardown is gated** on the commit hash being recorded in the sitting log (FBS FB-69 gate, retained; the comparison it gates is now the possible one).

**Refusals:** `golden_missing` / `golden_digest_mismatch` at the end-state readback; `golden_key_not_generation_free` (test).

**Acceptance tests:** T3.1 (B, pure) the same `RecordEdge` natural key under generations `5.0` and `5.1` gives equal `gkey_sha256` and different `record_uuid`. T3.2 (B) moving one support interval by one second changes the (class, path) digest. T3.3 (B, DB on the stub chart) the capture script run twice on an unchanged candidate reproduces byte-identical `digests.json`. T3.4 (S) end-state: re-hashing the run folder reproduces `MANIFEST.sha256`; the committed fixture's hash equals the one in the sitting log; else the teardown is reported as having run without evidence (a finding, not repairable).

## 4. MB-4 — TIMEOUT AND FAILURE

**MB-4.1 The cap (fact).** `asset_registry.writer_timeout_seconds = 28800` in the 1304 row (M/1304 on origin/pravaha/c41-v5-registry-row:15-16, 82; DP/TD `EXPECTED_REGISTRY_ROW` 28800). The runner reads the registry value (RN:885-888); `WRITER_TIMEOUT_SECONDS` (RN:111, default 600) is only the fallback (RN:679) — observed live by Suvarna (SS_TIMEOUT_FACTS_20261005.txt (1): registry 600 won over env 7200). It is a wall-clock cap on the WHOLE asset from dispatch (RN:721-741). CK row R1's "7200" (CK:240) is stale; CK row 2.4 (CK:81) has the current value. **Cloud Run task timeout must be strictly above the cap** (86400 s per CK:63, 108; not verified here).

**MB-4.2 What a fired cap does (fact, code over review).** The scheduler marks the asset error and adds it to `failed` (RN:727-741) via `_mark_asset_timeout` (RN:558-581) with the text `TIMEOUT: writer exceeded its writer_timeout_seconds budget (Ns) — this asset is the failure, not a blocked dependent`, disposition NULL (landed a043398c6, 2026-09-30). CK:128 and TR §6 quote `BLOCKED: upstream dependency(ies) timeout:…` — an older text; which the deployed image writes is not verified. **The detector is state, never text:** `build_runs.state = 'failed'` (RN:331) with `build_run_assets.state = 'error'` and no `asset.substep` event at `index = total`. The writer THREAD IS NOT CANCELLED (daemon pool RN:35-36, 682; "daemon thread will die on process exit", RN:733) and keeps committing substeps until the process exits (SS_TIMEOUT_FACTS (2): 13 s after the mark).

**MB-4.3 State-check guard (rule, A; GUARD-PRECHECK accepted by the steward 2026-10-05).** At the top of every `run_substep` (W:775) the writer reads `asset_throughput.state` for `(chart_id, asset_id)` on `ctx.db_conn` (a READ is inside the frozen contract; the prohibition is on WRITING it, CLAUDE.md §N.2): skip when `ctx.dry_run` or when NO row exists (direct unit tests); refuse by name `asset_not_building` when a row exists and `state <> 'building'`. `run_asset` commits the `building` row before the first substep (AR:1032-1034, 1535); `mark_asset_error` writes `error` and COMMITS (AR:577-605), which READ COMMITTED makes visible to the next substep. Residual, accepted: the substep in flight when the cap fires still commits.

**MB-4.4 Lit-over-error (fact + rule).** The finish path UPDATEs `asset_throughput` and `build_run_assets` with no predicate on the current state (AR:1348-1375: `SET state = %s … WHERE chart_id … AND asset_id`; then `state = 'complete', disposition = 'build'`), so a writer that completes its plan after the cap OVERWRITES the error mark; the run row stays `failed`. Rule: the verdict is read from `build_runs.state` FIRST (CK:130 "never trust an asset row alone"); the guard of MB-4.3 bounds the case to a cap firing during the LAST substep. The verifier's verdict reader refuses `asset_lit_under_failed_run` by name.

**MB-4.5 Teardown only after the writer process has exited (rule, S).** Observed as: the Cloud Run execution is terminal (`gcloud run jobs executions describe <exec> --format='value(status.completionTime)'` non-empty) AND the job log shows no `asset.substep` event after that instant. NOT the advisory lock: the scheduler releases the chart lock at run end (RN:1324, 1338; …/orchestrator/locks.py:5-21), so a still-alive daemon writer is not excluded by it; the teardown's active-run refusal (TD:43, 115) reads `build_runs.state`, which is already `failed`. Hence the rule is procedural and tested by T4.4.

**MB-4.6 Restart-from-zero (fact).** The production caller passes no `completed_keys` (AR:1119-1122 builds the ctx; the substep loop's skip exists only for callers that pass them, AR:867-878); a failed run cannot be re-executed (CK:166). A retry = teardown (TD) then re-dispatch; the `snapshot` substep replaces the whole chain (W:917-934). The global substrate rows (`rules`, `convention`, `body:*`; CK R2b:264-278) persist and make the re-run's first ten substeps cheap.

**MB-4.7 Rows read to decide the outcome (rule, S then B).** CK R7c (CK:133-145) verbatim: `build_runs.state, last_error`; `build_run_assets.state, disposition, error`; `asset_throughput.state`; `kala_gochara_publication.status` and `input_generation_vector->>'stored_scope'`; inventory counts (26/26). Plus the job log's last `asset.substep` `index/total` (AR:918-925; total = 298 for 26 classes, CK:123). SUCCESS iff `completed | complete | build | lit | candidate | test_slice | 26 | 26` and `index = total = 298`. `incomplete` (AR:1319-1334) is not a pass.

**Refusals:** asset_not_building (writer) · asset_lit_under_failed_run (verifier) · run_not_terminal_for_teardown (sitting; also TD's `planned/running/paused` refusal) · substep_plan_incomplete (verdict: `index < total`).

**Acceptance tests:** T4.1 (A, DB) a seeded `error` row makes the next `run_substep` raise `asset_not_building`; a `building` row proceeds; no row proceeds; `dry_run` skips. T4.2 (A) the 1304 row readback (CK R1 with 28800) — the dispatch refuses a row with 7200 (DP `EXPECTED_REGISTRY_ROW`). T4.3 (B) the verdict reader on a fixture `{run failed, asset lit, complete}` returns `asset_lit_under_failed_run`; on `{completed, …, index 297 of 298}` returns `substep_plan_incomplete`. T4.4 (S, pre-dispatch) CK row 6.0: task timeout and cap recorded verbatim; task timeout > 28800 or STOP. T4.5 (S, written before dispatch; OS-5) Stream A's expected run length from the small test (run 2: one class × 10,333 d; run 1: 26 classes × 365 d), scaled to 26 × 31,446 d minus the substrate phase; if the projection exceeds 0.8 × 28800 s the steward rules before dispatch.

## 5. MB-5 — WHAT CAN BE MEASURED AND READ from a test-slice candidate

**MB-5.1 Readers that refuse the stamp (fact).** Verification job: `test_slice_candidate` (K/verification_job.py:175-183). Publication: `TestSlicePublicationRefusal` (K/ledger.py:623-636); the authority flip's selection excludes the stamp (K/ledger.py:741-742). Seal flow needs the approved brief and verification first (K/seal_flow.py:36-72 per AST), never reached. The MCP contact-ledger reader refuses the stamp (CK:33; not re-verified here). Therefore NO existing reader computes any reported number; every number comes from one of three read-only sources:
| number | tool | reads |
|---|---|---|
| timings per phase / class | job log `asset.substep` events (AR:918-925: substep_key, index, total, rows_written, timestamps); totals from CK R7a | log + build_run_assets |
| admitted-day share per class × path, fast/slow split, P4-alone, class union, window-length distribution, per-agent contribution | MR `read_records` + `class_share_report` (b11), half-open day arithmetic (MR docstring "Day arithmetic") | ka_gochara_relationship_record (admission_state='admitted', temporal_support_intervals), ka_gochara_eval_window |
| near-miss / unresolved / omission / seam / wrap / clipped counts | the sink export (MB-2.3) and B's recount (MB-2.4) | job log + ka_gochara_contact + ephemeris |
| class census, stamp, horizon, rule versions, sealed/published | MR `read_measuring_view` + `measuring_refusals` | kala_gochara_publication, ka_gochara_generation_seal, record/window tables |
| row counts per table and class | CK R2 / R8b SQL | all `5.0` tables |
| horizon basis and drift | MB-1.4/1.5 reader (B) | manifest vector + life_events |

**MB-5.2 The scorer cannot read it, for a reason independent of the stamp (fact; closes AST prerequisite 5 by relocation).** `gochara_eval/extract.py` consumes an EXTRACT document and requires `float(r["si"])` and `pk` (:106-139); no extractor over `ka_gochara_eval_window` exists on main (AST "additional checks"). The measuring build runs under `DEFAULT_RESULT_POLICY = all_null_candidate/1` (W:888; K/result_policy.py:19-26): every score, peak and valence is NULL (:6-9). So FB-5's oracle ("same extracts as a scored-horizon build") CANNOT run on the measuring build, nor on any all-null candidate (AST P2-1 corrects FBS FB-5's fallback to FB-66). It moves to the first build under a numerical policy — OD-1, the owner's (OO-5). Admitted-day BURDEN is nevertheless real on all-null windows (AST P2-1 corrects FAB "vacuous") and is what MR computes.

**MB-5.3 What the measuring build CANNOT establish (rule: the report says so verbatim).** Nothing about the eight ND-H classes beyond their P2 rows (P1/P3/P4 are excluded today); nothing about K-B, karakatva, the natal-Sun target, DVI members or the 40% guard (FBS FB-41/FB-48/FB-66: the final-rules candidate); no near-miss STORAGE (no tables exist; a count only); no scoring, endpoints, retrodiction or 3.0 comparison; nothing about sealing, publication, serving, 1236, rollback or 1984-1998 behaviour; no final-build run length (a LOWER BOUND, FBS FB-58); no verification rows (the build writes none, CK:12); no G12 copy or G8 census behaviour (1305-1308 not applied).

**Refusals:** every MR refusal by name on read (`unknown_path_id`, `unknown_agent`, `rule_version_not_in_scope`, `support_interval_unbounded`, `horizon_bound_not_midnight`, `naive_datetime`, `interval_inverted`, `unknown_via`) — a report built over a refused reader is itself refused.

**Acceptance tests:** T5.1 (B, DB) `verification_job` on a stub test-slice candidate raises `test_slice_candidate`; `ledger.publish` raises `TestSlicePublicationRefusal` (expected to exist in tests/l3/gochara/test_c46_v5_test_slice.py — not verified). T5.2 (B) `extract.py` on rows with `si = None` raises (proves MB-5.2). T5.3 (B) a stored agent `"Jupiter"` or a `rule_version "1.2.0"` makes `read_records` refuse by name (MV_FABLE_1 P1-3/P2-1). T5.4 (B) the report document contains the MB-5.3 paragraph verbatim (a string test; a report without it is refused `report_scope_statement_missing`).

## 6. MB-6 — ACCEPTANCE of the measuring build as what it claims to be

**Rule (B's `measuring_refusals`, extended):** accepted iff ALL hold — (a) `stored_scope = 'test_slice'` and the `test_slice` component carries `run = 'all_classes_full'`, `marker_digest` recomputable by the writer's own validator (TD/shared `stamp_proof` imports it; v5_small_test_shared.py:148-175); (b) manifest horizon = marker horizon = the derived horizon of MB-1 = the ruled pair; (c) rule versions with any stored record or window ⊆ {1.0.0} — an ALLOWLIST of BOUND versions (AST on FAB 1.13: registered-but-unbound 1.1.0 rows are not inventoried); (d) class census: the marker names exactly the 26 scored classes and no row belongs to a class outside them; (e) the eight ND-H classes hold rows ONLY on P2 — a P1/P3/P4 row for them is `excluded_path_has_rows` (ST-H-UNKNOWN excludes PATHS, K/inventory.py:42, 392; MR's `excluded_class_has_rows` must be narrowed, §10); (f) zero reader refusals (MB-5 list) over every stored row; (g) no near-miss table exists, or it exists and holds 0 rows for the candidate (absent = `unknown`, reported, MR test "absent near-miss store is unknown not zero"); (h) `ka_gochara_generation_seal` has no row; `kala_gochara_publication.status = 'candidate'`; `kala_gochara_authority` does not name 5.0 (CK R2); (i) the run verdict of MB-4.7 is SUCCESS; (j) `horizon_basis` present and re-derivable (MB-1.5).

**Refusals (MR names, plus this contract's):** measuring_scope_not_test_slice · measuring_run_not_all_classes_full · measuring_build_sealed · measuring_build_published · horizon_mismatch · marker_horizon_mismatch · horizon_problem family · rule_version_not_in_scope · near_miss_rows_stored · excluded_path_has_rows · unknown_class_has_rows · class_census_mismatch · measuring_manifest_missing / _ambiguous · horizon_basis_missing · verdict_not_success.

**Acceptance tests:** T6.1 (B) MR's parametrised departure table (one mutation ⇒ one named refusal; "several departures are all named"). T6.2 (B) a view with a P2 record for `spiritual_turn` is ACCEPTED and one with a P3 record for it is refused `excluded_path_has_rows` (fails against MR today). T6.3 (B, DB) a candidate with two publication rows ⇒ `measuring_manifest_ambiguous`. T6.4 (S) R7c equals the SUCCESS line and R2 counts are recorded before any read of rows.

## 7. MB-7 — THE REPORT to the owner (fixed list; B drafts from the raw files, S signs)

Denominators: build horizon 31,446 days half-open; scored horizon 10,333 days half-open (`[1998-01-01, 2026-04-17)`, FB-5 "t_in < 2026-04-17") — the protocol states 10,334 INCLUSIVE days (EP:60-61) and uses H = 10,334 in its T-FP arithmetic (EP:189-192). Both are printed; shares use half-open; the one-day difference is 0.0097% relative; which convention the protocol amendment adopts is OS-2 (MR already names both: `PROTOCOL_SCORED_DAYS = 10334`).
| # | number | source / tool | denominator |
|---|---|---|---|
| 1 | wall time: run; asset; per phase (rules, convention, each body, manifest, snapshot); per class (inventory, coverage, 4 record grains, 4 window grains, verify) | R7a + `asset.substep` timestamps | seconds; share of asset time |
| 2 | substeps completed / planned | last `asset.substep` index/total | 298 |
| 3 | rows per table and per class | CK R2 / R8b | counts |
| 4 | admitted-day share per class × {P1, P2, P3_fast, P3_slow, P3_union, P4, class_union} over the BUILD horizon | MR `class_share_report(…, H)` | 31,446 |
| 5 | the same over the SCORED horizon (informational for the protocol band 0.5-40%, EP:199-205; the band is a GAIN-class criterion, OD-10) | MR `class_share_report(…, SCORED_HORIZON)` | 10,333 (10,334 shown beside) |
| 6 | window count, median, p90, max length per class × path | MR `length_distribution` | days |
| 7 | per-agent admitted days and exclusive days per class | MR `per_agent` | days |
| 8 | near-miss count per (class, relation, body); unresolved count by reason; omission/anomaly count; seam count; wrap count; horizon-clipped count | sink export (MB-2.3) + recount (MB-2.4) + `sink_disagreement` list | counts; FBS FB-6 expectation (≈58 / 52 / 5 over the horizon, from the work order, not verified) shown beside |
| 9 | the eight classes: P2-only rows, P1/P3/P4 = 0, stated | MR census + CK OQ14 | — |
| 10 | horizon basis: chosen event, excluded undated count, the three shape readings, `lel_drift` lines | MB-1.4/1.5 | — |
| 11 | golden capture: file list, `MANIFEST.sha256`, commit hash | MB-3.4 | — |
| 12 | teardown: dry-run counts, execute outcome, end state (CK R1/R2/R2b/R3/R9) | TD output | — |
| 13 | the MB-5.3 statement of what this build cannot establish, verbatim | this contract | — |
| 14 | bereavement's share beside its 2.61% budget, labelled "structural-saturation finding, not a decision" (FBS §12, STRATEGY_OPEN_ITEMS item 4) | MR | 10,333 |
Refusals: `report_number_missing:<n>` (any of 1-14 absent), `report_scope_statement_missing`. Acceptance: T7.1 (B) a report rendered from fixtures with one number removed fails the schema check by name; T7.2 (B) every share in the report equals days ÷ the printed denominator (recomputed in the test).

## 8. MB-8 — SITTING SEQUENCE (one page; CK rows govern, not restated)

0. **Pre-conditions (S):** small test (CK runs 1 and 2) completed and torn down with R2 all zero; Stream A's measuring PR (MB-1.3, MB-1.4, MB-2.2/2.3, MB-4.3, dispatch value) and Stream B's MR amendments (§10) merged, deployed, image = checkout (CK row 0.3); R-LEL (T1.5) run and the birth-word column pinned (OS-1); T4.5 run-length statement filed; owner items CK row 1 (teardown role — OO-9; global rows — OO-10) decided.
1. **Dry run (S):** `dispatch … --run all_classes_full --classes all` (no horizon flags) prints the derived horizon = `1998-01-01T00:00:00+00:00 … 2084-02-05T00:00:00+00:00`, 26 classes, `plan_manifest_digest`; CK rows 2-5 (1304 shape with 28800; R2/R2b/R3/R4 zero-state; teardown dry run on the empty state; dispatch dry run; R2 unchanged).
2. **Launch window (S):** CK row 6.0 (task timeout > cap, recorded), 6.1-6.3 (`--execute`, then `gcloud run jobs execute … --args=--run-id,<id>` within 10 minutes of `created_at`, R6).
3. **Watch (S):** CK row 7: R7a/R7c, `asset.substep` progress (298), the `STRETCH_SINK/1` lines; a fired cap = MB-4.2/4.5 (stop, wait for process exit, read the committed prefix, teardown, no re-dispatch before teardown is confirmed); a P1 anchor failure or any `omission` record that fails `verify:<class>` STOPS the sitting (CK:162; OS-6).
4. **Read results (S, read-only):** R7c verdict recorded verbatim FIRST; R2/R8b counts; export the job log (sink + substep events) to `/Users/Dev/pravaha/run/measuring-<date>/`.
5. **Capture (B, read-only prod connection):** MB-3.4 golden + MB-1.4 `horizon_basis` + MB-6 acceptance run (`read_measuring_view`, `measuring_refusals`, `read_records`, `class_share_report`) + MB-2.4 recount; commit the fixture; record the hash in the sitting log.
6. **Teardown (S):** only after MB-4.5 is observed and step 5's hash is recorded: CK rows 9.1-9.5 (dry run, `--execute --i-am-steward`, end-state R1/R2/R2b/R3/R9).
7. **Read-back (S, B):** CK row 11 end state; the report of MB-7; STRATEGY_OPEN_ITEMS items 4-6 updated with numbers, not decisions.

## 9. The six prerequisites of the second review → clauses

| AST prerequisite ("Sufficient now?") | closed by | how |
|---|---|---|
| 1 Exact horizon detector, shapes, START refusal, pinned basis, drift rule — No | MB-1.1-1.5, T1.1-T1.5 | real columns incl. `chart_id` (423), literal shape reading + sensitivity refusal, five START/END refusals, consumed rows pinned, soft drift |
| 2 Structured unresolved sink — No | MB-2.1-2.4, T2.1-T2.4 | six None-cases separated into near_miss / unresolved(3) / omission(2) / anomaly; stable ids; log-line store; recount and "agree" |
| 3 Golden before teardown — No | MB-3.1-3.4, T3.1-T3.4 | generation-normalised key; per class × path enumeration of what stays equal; teardown gated on the commit |
| 4 Cap, Cloud Run timeout, fired-cap procedure — Partly | MB-4.1-4.7, T4.1-T4.5 | state guard, writer-exit observation, restart-from-zero, lit-over-error, rows read |
| 5 Test-slice extractor or relocated oracle — No | MB-5.2, T5.2 | no DB extractor exists and all-null windows cannot be extracted regardless of the stamp: the oracle moves to the first numerical-policy build (OO-5) |
| 6 Reconcile 1307 before scheduling the window — Partly | MB-5.1, MB-6(h), OS-4 | the measuring build does not depend on 1307 (FBS §13 "not needed"); unpublishability rests on the code refusals cited; the mechanism/class reconciliation (FBS FB-19 CHECK + freeze trigger, PROTECTED vs SECOND_WINDOW_PLAN §1 item 3 / §2 "replaces a status-transition guard function") is the second window's and is carried as OS-4, not closed here |

## 10. In-flight code that already departs from this contract (to reconcile before dispatch)

- MR `fully_dated_events` (b11 head 2bfdb1c7b:126-156): reads `interval_start` for intervals and REFUSES exact chains (`lel_chain_shape_not_ruled`); this contract reads `event_date` for every shape and refuses only when the readings differ (MB-1.2 items 3, 6). Also `BIRTH_CATEGORY = "birth"` on `category` (MR:83, 133) — the YAML source has `category: other`; the column is OS-1.
- MR `measuring_refusals` → `excluded_class_has_rows` refuses ANY row of the eight classes (MR docstring "must hold no record and no window for them"); the eight legitimately hold P2 rows today (CK OQ14; K/inventory.py:42 excludes paths P1/P3/P4 only) — a faithful measuring build would be refused. Narrow to `excluded_path_has_rows` (MB-6(e)).
- MR has no `horizon_basis` reader, no verdict reader, no sink recount (its docstring says so, "not done"): MB-1.5, MB-4.4/4.7, MB-2.4 are new B work.
- Writer (origin/main): no `all_classes_full`, no `derive_chart_horizon`, no `horizon_basis`, no structured sink, no state guard; `DEFAULT_HORIZON` still bounds slices (W:157-158, 312-314, 355): all MB-1.3/1.4, MB-2.2/2.3, MB-4.3 are new A work. Stream A's branch is not on origin and was not read.
- CK/TR quote the fired-cap text `BLOCKED: upstream dependency(ies) timeout…`; origin/main writes `TIMEOUT: writer exceeded…` (RN:574-578). MB-4.2 keys on state.
- FBS FB-1/FAB 1.3: "`life_events` carries no `chart_id`" — contradicted by supabase migration 423:19-20 (MB-1.2).

## 11. OPEN-OWNER (nothing here is decided by this contract)

| # | decision | contract position for THIS build |
|---|---|---|
| OO-1 | the GENERAL horizon rule's three narrowings ("birth entry aside", "fully dated only", "1 January of the year") — FBS OD-3 | uses the owner-approved pinned pair (Ruling 13); the detector is evidence, guarded by `horizon_derivation_disagrees_with_ruling` |
| OO-2 | the date of an INTERVAL or CHAIN event for "the first event" | literal row `event_date`; refuses if the readings differ; no effect on the pinned chart |
| OO-3 | 1 January vs 16 February 1998 (STRATEGY_OPEN_ITEMS item 6; FBS §12) | 1 January, as approved; put back to the owner stands |
| OO-4 | disposition of UNRESOLVED stretches if the count over 1998-2084 is non-zero (FBS OD-5) | counted only (MB-2); the final seal's default refusal is not this build's |
| OO-5 | result policy (FBS OD-1) — determines where FB-5's oracle can ever run | all-null here; the oracle cannot run (MB-5.2) |
| OO-6 | leap-day birth and future-start refusals (steward flagged, MV_FABLE_1 rulings b, c) | refusals by name; not reachable for the pinned chart |
| OO-7 | a log tightening that moves START before 1998: refuse or extend the domain (FBS OD-11) | refuse by name |
| OO-8 | density / fast-planet decisions on the measuring build vs the final-rules candidate (FBS OD-4); karakatva breadth (OD-6) | the report carries numbers for the 18 classes only and says what it cannot establish (MB-5.3) |
| OO-9 | the teardown role (CK row 1.1, TR §4) | required before dispatch; no recommendation changed here |
| OO-10 | global rows the sitting leaves behind (CK row 1.4, R2b) | the owner is told before dispatch |

## 12. OPEN-STEWARD (only the steward can rule)

| # | item | default in this contract |
|---|---|---|
| OS-1 | which stored column carries the birth word (`category` / `event_type` / `provenance`), pinned from R-LEL | refuse `lel_birth_row_unidentifiable` until pinned |
| OS-2 | the scored-horizon day convention for the protocol amendment: 10,333 half-open vs 10,334 inclusive | report both; shares half-open |
| OS-3 | horizon instants: calendar date → UTC midnight (as `DEFAULT_HORIZON`) vs IST midnight (EP §3) | UTC midnight |
| OS-4 | 1307 mechanism and class (FBS FB-19 vs SECOND_WINDOW_PLAN §1 item 3 / §2) | not a precondition of this build |
| OS-5 | the run-length projection and the go/no-go threshold against 28800 s (T4.5) | 0.8 × cap |
| OS-6 | whether an `omission` found by the certifier stops the build (builder defect) or is sunk for counting | stops (`verify:<class>` raises after emitting the record) |
| OS-7 | reconciliation of MR's departures (§10) before the verifier is used for acceptance | required |
| OS-8 | the sink store: job-log JSON lines exported the same day vs another store | job log + export |
| OS-9 | whether B's recount (MB-2.4) runs against production read-only while the candidate exists, or against the exported contacts after teardown | while the candidate exists, read-only |

## 13. Not verified here

No database, production, Cloud Run, credential or `gh` access: production's `life_events` columns (423 applied? which column holds `birth`), live row contents, the 1304 row as applied, the task timeout (86400 s), which fired-cap text the deployed image writes, whether the MCP contact-ledger reader refuses the stamp, whether `test_c46_v5_test_slice.py` tests the publish refusal, the FBS FB-6 expected counts (≈5,900 / 58 / 52 / 5), the merge state of PRs 3097/3098/3101/3143/3156/3177 (the scripts and 1304 were read on their branches, not on main), and the small test's outcome (not yet run as of the tracker snapshot). Stream A's `a-mb-horizon` branch was not read (not on origin). ND-H / ND-P2 were read only as carried in FBS. TR v1.2 was read from the c38 branch and may be behind its PR.
