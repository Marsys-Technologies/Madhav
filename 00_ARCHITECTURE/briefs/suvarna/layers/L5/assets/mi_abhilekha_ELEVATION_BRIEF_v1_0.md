---
asset_id: mi_abhilekha
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Strategic Suvarṇa (R5)"
risk_class: "high (people outcomes; irreversible status writes; must not be probed on real data)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-48, TI-L5-49, TI-L5-50]
ledger_gap_ids: ["mi_abhilekha-Idem.pattern", "mi_abhilekha-Earn.build_record", "mi_abhilekha-Cost.baseline", "mi_abhilekha-Complete.depth", "mi_abhilekha-Vocab.identity", "mi_abhilekha-Build.history", "mi_abhilekha-Build.dep_liveness", "mi_abhilekha-Carr.detector", "new: abh-N1", "new: abh-N2", "new: abh-N3", "new: abh-N4", "new: abh-N5", "new: abh-N6"]
---

# mi_abhilekha — Journal re-sync: native answers to prediction lifecycle status (service, DRAFT)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_abhilekha.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :37). Counts the rows of `mimamsa_journal` **over all charts** (:44-52), then, for every answered, event-linked journal row of any chart, sets `mimamsa_predictions.lifecycle_status` to `confirmed` if the lower-cased `native_answer` contains the substring `yes` or `confirmed`, else `denied`, for a prediction in that chart that is still `pending` (:58-76). It reports the number of updates as `rows_inserted` (the effect contract records this: 'rows_inserted_reports_updated_prediction_count'). The docstring says it 're-syncs ... back into mimamsa_calibration'; the code never touches `mimamsa_calibration`. `mimamsa_journal` has no writer in the repository (`git grep`: reads only; migration 691 records it), so the input path does not exist.

**Canonical chart state (read-only, 2026-10-03).** `mimamsa_journal`: 0 rows, 0 charts (`jrn`); so the writer has never changed a status on real data. Catalog `DRAFT`. By the repository's own effect contract the behaviour is recorded, not ratified, and may not be exercised on real outcomes — yet the orchestrator executes it in every chart build (34 complete runs).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | service / per_chart / service | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3078` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_abhilekha.py:28` `@register("mi_abhilekha")`; registry `has_writer` = t, `asset_kind` = service | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_journal`; count_sql tables: `mimamsa_journal` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_journal WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 0 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | DRAFT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `stale`, rows_written 0, last_built_at 2026-08-13T01:16:30Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_bhavisya` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no dependents); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `mi_bhavisya` (it writes that asset's table, so the edge is real). Undeclared: it reads `mimamsa_journal` (no owner asset) and writes another asset's column (`mimamsa_predictions.lifecycle_status`, declared in `cross_asset_writes`). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | `query_journal.ts:80` (`marsys://tool/L5/query_journal`, served); the writes it performs are read by `query_predictions.ts`, `mi_pramana` (stale-filter only), the sweep. Census Dens.served PASS (1 module); effect contract `fixture_scoped_effect`, `authority_state: source_observed_unratified`, `execution_boundary: disposable_fixture_only_until_product_review`, and "This effect contract must never be probed against real user outcomes" (`scripts/nirmana_service_effect_contracts.json`). | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_purna_anvesana_service_effect_contracts.py::test_mi_abhilekha_effect_contract_matches_source_and_stays_unratified` (source-text lock), `L5_mimamsa/__tests__/query_journal.test.ts`, `platform/docs/evidence/purna_anvesana_wave1_disposable.json` | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | none: no receipt, no freshness row, no digest spec; `service_health` NULL, no self-test; throughput `stale` 2026-08-13T01:16:30Z; history 34 complete / 26 errors / 9 aborts | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (58) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) ['mimamsa_journal'] anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: mi_abhilekha.py] |
| Build | Build.target † | PASS | target_table=mimamsa_journal |
| Build | Build.dag † | PASS | 1 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | PARTIAL | rows_written=0 = live=0 (count_sql over the target table; chart 482012f1); target_floor=0 declares zero rows complete, but this is a writer-backed data asset (has_writer=true) with no layer-plan claim that the emptiness is by design — indistinguishable from a writer that has never produced a row |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete (information) | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 9 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (chart_id, journal_id) is vacuous on 0 rows |
| Dens | Dens.served † | PASS | 1 module(s): query_journal.ts; declaring density_contract: 1 |
| Build | Build.history | PARTIAL | latest run complete, but 26 error(s) and 9 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) mi_bhavisya did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_bhavisya (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved PASS -> PARTIAL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_abhilekha-Idem.pattern | Idem.pattern | detector | measured: no idempotency pattern in the writer's own SQL — it likely delegates; verify there / required: the Idem gate's claim |
| mi_abhilekha-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_abhilekha-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_abhilekha-Complete.depth | Complete.depth | information | measured: NO_DETECTOR — table empty (0 rows, 9 cols): column population cannot be measured on no rows / required: the Complete gate's claim |
| mi_abhilekha-Vocab.identity | Vocab.identity | detector | measured: NO_DETECTOR — table empty: uniqueness under (chart_id, journal_id) is vacuous on 0 rows / required: the Vocab gate's claim |
| mi_abhilekha-Build.history | Build.history | history | measured: latest run complete, but 26 error(s) and 9 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest e... |
| mi_abhilekha-Build.dep_liveness | Build.dep_liveness | stale | measured: 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_bhavisya (error, chart 482012f1)'] — a DEP-ASSERT trap if no ... |
| mi_abhilekha-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: abh-N1 | Earn / classification (N-46 adjacent) | real (central; SS question R) | answer text becomes a lifecycle status by substring: "yes" or "confirmed" anywhere gives `confirmed` ("unconfirmed", "eyes", "yes and no" all qualify; "no, not yet", "partly", "maybe", "I don't know", "wait" give `denied`). The `denied` default is a verdict invented for every non-matching answer, including non-answers. Only `pending` rows are updated and no code reverts a status, so the first run fixes the outcome of a claim from free text. T2c: "structured explicit adjudication instead of substring outcomes; unknown/partial/disputed/unobserved retained". The effect contract says the same in its own words |
| new: abh-N2 | scope | real | the journal select is not chart-scoped (:60-65) and the writer is a per-chart asset in the registry: a build for chart A applies chart B's journal answers to chart B's predictions. The UPDATE is keyed `(chart_id, prediction_id)` from the journal row itself so rows are not mixed up, but the effect is global and the build of one chart is not idempotent with respect to another's data. (`scope` says per_chart; the docstring says GLOBAL.) |
| new: abh-N3 | phantom input | real | no code writes `mimamsa_journal`: the asset is wired to an input nobody can produce (CF-L5-09). `mi_seva` claims to write journal entries; it does not |
| new: abh-N4 | Earn (rows_inserted) | real | `rows_inserted` = number of status updates (:76-79): a count of changes reported as inserts; with `target_floor 0` a zero reads `complete`. Combined with a `denied` default, a journal row with an unrelated answer reads as a built row |
| new: abh-N5 | doc | information | docstring says it syncs into `mimamsa_calibration`; the code updates `mimamsa_predictions` and the calibration table is only rebuilt by `mi_pramana` (which excludes nothing by lifecycle status) |
| new: abh-N6 | Build.dag / registry | real | kind service with no health or self-test; no digest spec; `catalog_status DRAFT`; the declarations file lists `cross_asset_writes: [mimamsa_predictions.lifecycle_status]` (CF-L5-07, CF-L5-09) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `lifecycle_status = confirmed / denied` | the native confirmed or denied the prediction | substring test on free text (:67) | **proxy of two words**; `denied` is the default for everything else |
| `rows_inserted` | rows built | number of UPDATEs | relabelled count |
| build state `complete` | the journal is synced | completed without error even with 0 journal rows | proxy of "did not crash" |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: the contract file records the known limits and bars real-outcome probing.
- BAD: a free-text answer is never allowed to stay ambiguous: there is no `unknown` / `partial` / `unobserved` outcome path (the tool enum for `mimamsa_outcome_record` offers `partial`, this writer cannot produce it).

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** No `chart_id` read from `ctx.config` (the writer processes all charts); `entry["chart_id"]` is a `uuid.UUID` (dict-row) passed back as a SQL parameter (:69-72). No `json.dumps`/hash of an id. Not exposed.
- **Outcome-leakage guard:** a status set from a journal answer is an outcome entering the prediction table; it is the one writer in L5 that does so. Its rows are excluded from rebuild deletion by design (`mi_bhavisya` keeps non-pending rows), which is correct for N-46 but means a wrong substring verdict is permanent.
- **People-entered data (N-46) / LEL data contract:** **This writer is the closest L5 comes to touching people-entered outcomes**: it reads the native's typed answers (`mimamsa_journal`, unclassified, protected by default) and writes a derived status onto `mimamsa_predictions` (a mixed table whose confirmed/denied/partial outcomes are not regenerable, INV). It never modifies or deletes a journal row. The proposed fixes keep that: structured answer captured additively, ambiguous text leaves the prediction `pending`, nothing already typed is rewritten.

## 3 · Disposition

**qualify (Q)** — the intent (a native answer closes a claim) is right and necessary for calibration; the implementation guesses outcomes from substrings and acts on all charts. Qualify = structured explicit adjudication, chart scope, ambiguity preserved; the retire alternative applies only if SS decides the journal path is replaced by the learning API (`/api/clients/[id]/learning` adjudicate).

Approver under Track A brief section 10: **Strategic Suvarṇa (R5)**. Risk class: **high (people outcomes; irreversible status writes; must not be probed on real data)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Structured adjudication, no guessing (R)

- **Answers:** abh-N1, N3, N4; Q-L5-12
- **Change:** capture the native's answer in an additive structured column (`answer_code` in {confirmed, partial, denied, unobserved, disputed}; existing text untouched); set `lifecycle_status` only from `answer_code`, never from text; text without a code leaves the prediction `pending` and is reported; report updates as `rows_updated`
- **Files / declaration / migration:** `mi_abhilekha.py:58-79`; additive migration on `mimamsa_journal`; the journal intake (to be written: no writer exists)
- **Failing-first test and mutation:** failing-first (disposable DB only): "unconfirmed" and "maybe" leave the prediction pending; `answer_code = partial` sets `partial`; mutation: restore the substring test -> "unconfirmed" becomes `confirmed`
- **Output change:** none on current data (0 rows); behaviour change for future answers -> SS (R5)
- **Blast radius:** mimamsa_predictions readers
- **Rebuild:** none
- **Gate it moves:** Earn, Null
- **Fix class:** writer code + additive migration + (new) intake; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-48

### FD-2 · Scope the journal read to the chart being built

- **Answers:** abh-N2
- **Change:** add `WHERE j.chart_id = %s` (the writer is per-chart in the registry) or declare it global and idempotent across charts
- **Files / declaration / migration:** `mi_abhilekha.py:44-65`
- **Failing-first test and mutation:** failing-first (disposable two-chart fixture): chart A's build leaves chart B's predictions untouched; mutation: remove the filter -> B changes
- **Output change:** none on current data
- **Blast radius:** this asset
- **Rebuild:** none
- **Gate it moves:** Idem, scope
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-49

### FD-3 · Declare the real edges and the service contract

- **Answers:** abh-N6; CF-L5-07, CF-L5-09
- **Change:** edge to the journal producer once one exists; probe/self-test for the service; digest spec after FD-1
- **Files / declaration / migration:** registry migration; declarations
- **Failing-first test and mutation:** contract test updated from `unratified` to ratified only on SS approval
- **Output change:** none
- **Blast radius:** registry rows
- **Rebuild:** none
- **Gate it moves:** Build.dag, Earn
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-50

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-07** — abh-N6
- **CF-L5-08** — people outcomes; irreversible status writes
- **CF-L5-09** — phantom input, DRAFT service
- **CF-L5-11** — no receipt, no spec
- **CF-L5-12** — Build.history record; completion by non-crash

## 5 · Semantic fingerprint contract (for E5.5)

No build rows; the observable effect is a status transition on `mimamsa_predictions`. For E5.5, fingerprint the transition rule on a disposable fixture (the contract file already holds the fixture evidence). Never run on real outcomes.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the idea of a native answer closing a claim; the pending-only guard (a status that has moved is never rewritten); no journal row is modified.
- **Carriage check chosen (T4 §4.1; one only):** Carr N/A by cause (people-entered input to a derived status); D3: the transition table (answer code -> status) must be re-derivable from the stored codes.
- **Opportunities (never blocking):** the learning API already records adjudications (`mimamsa_adjudication_log`, 0 rows); one adjudication path instead of two (journal and API) would remove the substring guess entirely.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-12** — Journal adjudication: replace the substring rule ("yes"/"confirmed" -> confirmed, else denied) by a structured additive answer code, leave ambiguous text `pending`, scope the read to the chart, and build the missing journal intake (no writer exists)? Or retire the journal path in favour of the learning API's adjudication (`mimamsa_adjudication_log`)? *Recommendation:* Structured code + chart scope; choose one adjudication path (the API) and retire the other. (R)
- **Q-L5-13** — Service assets: retire `mi_seva` (a four-table existence check describing a handler that does not exist and that, as described, would apply learned multipliers at serve time against the collect-only doctrine)? Keep `mi_vistara` and bind it to a working exporter? Mark `mi_abhilekha` per Q-L5-12? *Recommendation:* Retire mi_seva; keep mi_vistara with an exporter aligned to the live ledger DDL; qualify mi_abhilekha. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
