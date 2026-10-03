---
asset_id: mi_sankalpa
layer: L5 Mīmāṃsā (mi_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna (lane track-a-l5)
produced_on: 2026-10-03
plan_item: A.L5 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION). Offline rollup under main REGISTRY_REVISION 16. Live registry, row counts, receipts and fact queries re-read 2026-10-03 (read-only)."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main adb0db29d"
disposition: "qualify"
disposition_proposal_approver: "Strategic Suvarṇa (R5: N-46 behaviour change)"
risk_class: "medium (people-entered rows; no data exists yet, so the change is risk-free to make now and costly later)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-55, TI-L5-56, TI-L5-57]
ledger_gap_ids: ["mi_sankalpa-Idem.pattern", "mi_sankalpa-Build.completion", "mi_sankalpa-Earn.build_record", "mi_sankalpa-Cost.baseline", "mi_sankalpa-Complete.depth", "mi_sankalpa-Vocab.identity", "mi_sankalpa-Build.history", "mi_sankalpa-Build.dep_liveness", "mi_sankalpa-Carr.detector", "new: sank-N1", "new: sank-N2", "new: sank-N3", "new: sank-N4", "new: sank-N5", "new: sank-N6"]
---

# mi_sankalpa — Unified intervention ledger maintenance: falsifier resolution, study-arm reclassification, arm-4 origination

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_sankalpa.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

The ledger `mimamsa_intervention_ledger` is **filed live by the native** through `platform-mcp/src/lib/intervention_filing.ts` (`fileInterventionFalsifier`) and the writes action `intervention_ledger_record` -> `platform/src/lib/mcp/intervention_ledger_writer.ts`; this writer never inserts a filed row. Its per-build job over rows that already exist (`run(ctx)`, :83): (1) score every `elected_pending` row with no outcome against the chart's LEL (reusing `living_lel.score_predictions_against_event`) and link `outcome_event_id` on a HIT; (2) **delete-then-reinsert** the rows matching `study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL` (`db.delete_unresolved`, `db.reinsert_rows`, :161-162), each read first and re-inserted with all 28 columns; (3) reclassify the `study_arm` of already-attested rows from their own `performed` fields; (4) originate `acted_without_election` rows from LEL events of classes the chart has already filed (`ON CONFLICT DO NOTHING`). Table is empty (0 rows, all charts); registry state `dormant`.

**Canonical chart state (read-only, 2026-10-03).** `mimamsa_intervention_ledger`: 0 rows in total (`ledger`: 0 rows, 0 charts). The writer has never processed a row. `dormant` is the registry's state for an asset that is built but has produced nothing.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3217` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_sankalpa.py:76` `@register(ASSET_ID)` (constant id); registry `has_writer` = t; light writer with `services/mi_sankalpa/{arms,db}.py` | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_intervention_ledger`; count_sql tables: `mimamsa_intervention_ledger` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_intervention_ledger WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 0 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 300s | registry |
| registry build state (canonical chart) | throughput `dormant`, rows_written 0, last_built_at 2026-08-13T01:02:38Z; recent canonical runs: complete 2026-08-13; complete 2026-08-12; complete 2026-08-12; complete 2026-08-12 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `ka_kshetra` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no dependents); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `ka_kshetra` (unread; the writer reads no `kala_*` table). Reads: `mimamsa_intervention_ledger` (its own), `life_events` (`db.py:64`, undeclared), `services/mi_bhara/living_lel` (shared pure functions). The table's foreign keys: `brahma_prospective_ledger(prediction_id)`, `life_events(id)`, `brahma_event_ontology(event_class_id)`. | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `platform-mcp/src/tools/kala_views/upaya.ts` (`kala_upaya_get`), `platform-mcp/src/lib/kala_upaya_diagnosis.ts`; written by `intervention_filing.ts` / `intervention_ledger_writer.ts` / `writes/[action]/route.ts`. Census: Dens.served N/A (0 modules; the readers are in platform-mcp), width 0.0. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `writers/tests/test_mi_sankalpa.py` (19 tests, including a fixture `DELETE FROM life_events` at `test_mi_sankalpa.py:246` on a disposable DB), `services` tests for `arms`; no test of a concurrent native update during the round trip | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T17:12Z); throughput `dormant` (2026-08-13T01:02Z; writer last complete the same minute); history 3 aborts, 0 errors; `built_against_writer_hash` unknown | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (35) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_intervention_ledger (services/mi_sankalpa/db.py:208 via mi_sankalpa.py → services/mi_sankalpa/db.py:delete_unresolved) |
| Build | Build.target † | PASS | target_table=mimamsa_intervention_ledger |
| Build | Build.dag † | PASS | 1 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='dormant' is not a completed build (rows_written=0, live=0, chart 482012f1) — see Build.history |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete (information) | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 28 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (chart_id, intervention_class, rite_or_activity_class, elected_window) is vacuous on 0 rows |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Build | Build.dep_liveness | FAIL | 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['ka_kshetra (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> NO_DETECTOR.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_sankalpa-Idem.pattern | Idem.pattern | detector | measured: no idempotency pattern in the writer's own SQL — it likely delegates; verify there / required: the Idem gate's claim |
| mi_sankalpa-Build.completion | Build.completion | stale | measured: build record state='dormant' is not a completed build (rows_written=0, live=0, chart 482012f1) — see Build.history / required: the Build ... |
| mi_sankalpa-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_sankalpa-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_sankalpa-Complete.depth | Complete.depth | information | measured: NO_DETECTOR — table empty (0 rows, 28 cols): column population cannot be measured on no rows / required: the Complete gate's claim |
| mi_sankalpa-Vocab.identity | Vocab.identity | detector | measured: NO_DETECTOR — table empty: uniqueness under (chart_id, intervention_class, rite_or_activity_class, elected_window) is vacuous on 0 rows /... |
| mi_sankalpa-Build.history | Build.history | history | measured: latest run complete, but 0 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  / requir... |
| mi_sankalpa-Build.dep_liveness | Build.dep_liveness | stale | measured: 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['ka_kshetra (error, chart 482012f1)'] — a DEP-ASSERT trap if no w... |
| mi_sankalpa-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: sank-N1 | people data (N-46) | real (by reasoning; not exercised) | the round trip deletes native-filed rows and re-inserts them verbatim (:161-162). It is column-complete (all 28 columns) and runs inside the orchestrator's transaction, so a failure rolls back. Two residual hazards: (a) a native update (`performed`, attestation) committed between the writer's SELECT and its DELETE leaves a stale copy to be re-inserted over the new row (primary-key conflict -> the build fails, safe); (b) a native UPDATE that blocks on the row lock while the writer deletes and re-inserts affects 0 rows after commit (the old tuple is gone) — an attestation can be silently lost. N-46: an agent deletes information people typed, even if it re-inserts it. The alternative needs no delete: UPDATE `outcome_event_id` / `outcome_linked_at` in place for the HIT rows and touch nothing else |
| new: sank-N2 | Build.dag | real | declared `ka_kshetra` unread; `life_events` read undeclared; `brahma_prospective_ledger` is a foreign-key target and a semantic source (the prediction spine) with no asset (TG-L5-006) (CF-L5-07) |
| new: sank-N3 | Earn (HIT) | information | a HIT is computed by the shared matcher (`living_lel`); with 0 rows nothing is exercised; the first row will test the matcher on interval windows where `float(w_start)` of a NULL/empty range previously failed in `mi_bhara` (the same helper style, `db.py:100-103`); `to_open_predictions` excludes rows with no `event_class` |
| new: sank-N4 | design (study arms) | information | arms 1-4 are an observational classification, not a randomised design: the T2c delta says "observational arms are not randomized or causal-efficacy proof". `acted_without_election` is originated from LEL events of an already-filed class, with `adoption_basis = session_inferred` and `precision_basis = derived_from_lel_no_covering_election` — labelled, not claimed as efficacy |
| new: sank-N5 | window handling | information | `window_end = event_date + 1 day` for originated rows because a `[)` range with equal bounds is empty (comment :207-209): a fix of a real earlier bug, with a regression comment but no test of a second rebuild reading the row back (the test file covers it only by name; not checked) |
| new: sank-N6 | Dens | information | no served module in `platform/src` selects the table; readers are in `platform-mcp` (outside the census roots), so Dens N/A and Reach width 0 under-state its use |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `study_arm` | which observational arm the intervention belongs to | `classify_study_arm` over the row's own `performed` / `performed_at` / window (`arms.py`) | **earned**: a deterministic function of native-attested fields; `None` leaves unchanged |
| `outcome_event_id` link | the LEL event that resolved the falsifier | first HIT from the shared matcher | earned by the matcher; depends on `event_class` agreement |
| `acted_without_election` row | the native acted without a covering election | LEL event of an already-filed class, no covering window | **derived and labelled** (`session_inferred`, `derived_from_lel_…`); idempotent `ON CONFLICT DO NOTHING` |
| `performed`, `performed_attested_by` | the native performed the rite | native-attested only; **never touched** by this writer | earned by construction; the writer cannot set it |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: `performed` / `performed_at` are never written by the writer; rows are re-inserted verbatim; the missing-table case raises (A2) instead of reading as 'no interventions filed'; `NOTE_NO_LEL` and `NOTE_NO_INTERVENTIONS` are named notes.
- NOTE: with 0 rows every notes-only path is untested on production data.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id = ctx.config.get("chart_id")` (:97) is a `uuid.UUID` on the real path; used as a SQL parameter in `services/mi_sankalpa/db.py`. `intervention_id`, `outcome_event_id` are carried as `str()` in the link dict (`outcome_links`); `reinsert_rows` json-dumps only `adjudication_record` / `score_vector` that were read back as parsed JSON (`services/mi_sankalpa/db.py:256`); `adjudication_record = json.dumps({"derived_from_lel": True, "outcome_event_id": outcome_event_id})` (`services/mi_sankalpa/db.py:286`) with `outcome_event_id` a `str`. **No raw UUID reaches `json.dumps`**; a `str`/`UUID` mixture in `already_linked` vs `ev.event_id` set membership (`mi_sankalpa.py:199`) was not traced.
- **Outcome-leakage guard:** falsifier resolution reads the LEL only to link outcomes to filed interventions; it writes no prediction and generates nothing; the `acted_without_election` arm is derived from outcomes by design and is labelled as such.
- **People-entered data (N-46) / LEL data contract:** **`mimamsa_intervention_ledger` is people-entered (INV: non-regenerable, 'user input, then updated by L5')**. This writer's deletion predicate is exactly the rows the native filed and has not yet attested; the loss-free round trip is correct by intent but is an agent deleting people-typed rows. FD-1 replaces it with an in-place update so that no entered row is ever deleted by an agent.

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_sankalpa.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — the logic is careful and conservative, and the table is empty; the one thing to change before the first real row exists is the delete-then-reinsert of native-filed rows (N-46). Qualify = in-place update, no deletion.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5: N-46 behaviour change)**. Risk class: **medium (people-entered rows; no data exists yet, so the change is risk-free to make now and costly later)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Update in place; never delete a filed row (N-46)

- **Answers:** sank-N1; Q-L5-16
- **Change:** replace `delete_unresolved` + `reinsert_rows` with `UPDATE ... SET outcome_event_id, outcome_linked_at WHERE intervention_id = ... AND outcome_event_id IS NULL AND performed IS NULL` for HIT rows only; no row is read-then-deleted; keep the idempotency predicate as the UPDATE's guard
- **Files / declaration / migration:** `mi_sankalpa.py:132-162`; `services/mi_sankalpa/db.py:121-160,166-200`
- **Failing-first test and mutation:** failing-first (disposable DB): a concurrent attestation committed during the build is preserved; mutation: restore delete/reinsert -> the interleaving test loses it
- **Output change:** none on current data (0 rows)
- **Blast radius:** kala_upaya readers
- **Rebuild:** none
- **Gate it moves:** N-46 / Idem
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-55

### FD-2 · Declare the real reads

- **Answers:** sank-N2; CF-L5-07
- **Change:** remove the unread `ka_kshetra` edge; add `lel_events`; give the prospective ledger an asset or a declared external source
- **Files / declaration / migration:** registry migration
- **Failing-first test and mutation:** reads-match; mutation: remove edge -> FAIL
- **Output change:** none
- **Blast radius:** DAG
- **Rebuild:** none
- **Gate it moves:** Build.dag
- **Fix class:** registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-56

### FD-3 · Pin the matcher on interval windows with a regression test

- **Answers:** sank-N3, N5
- **Change:** add tests for empty/NULL bounds in `to_open_predictions` and for a second rebuild reading an originated row
- **Files / declaration / migration:** `writers/tests/test_mi_sankalpa.py`, `services/mi_sankalpa/db.py:96-120`
- **Failing-first test and mutation:** failing-first: the pre-guard query raises on an empty range; mutation: remove the guard -> FAIL
- **Output change:** none
- **Blast radius:** this asset
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** test; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-57

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-07** — sank-N2
- **CF-L5-08** — sank-N1: agent deletes people-entered rows
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history; dormant state
- **CF-L5-14** — Dens/reach under-statement for platform-mcp readers

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. The writer's observable effect on a populated chart: `outcome_event_id`, `outcome_linked_at`, `study_arm` of existing rows and originated `acted_without_election` rows. Exclude `created_at`, `build_id`, `outcome_linked_at` (build clock). Never fingerprint `performed*` (native).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the status-preserving idempotency predicate (without the delete), `performed` never touched, falsifier-before-transition ordering, the labelled arm-4 origination.
- **Carriage check chosen (T4 §4.1; one only):** D3: recompute `study_arm` for every attested row from its own fields with a second implementation of the arm table (`arms.py`); recompute HIT links from the LEL.
- **Opportunities (never blocking):** the ledger is where prospective, falsifiable, native-filed predictions live (T2 section 9.1); linking it to `brahma_prospective_ledger` ids and to `mimamsa_predictions` is the route by which L5 acquires genuine prospective outcomes.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-16** — Replace the delete-then-reinsert of native-filed `elected_pending` rows by an in-place UPDATE of the outcome link (N-46)? The table is empty now, so the change costs nothing today. *Recommendation:* Yes.
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
