---
asset_id: mi_jivanaghatana
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
disposition_proposal_approver: "Steward (G16); label and flag changes to Strategic Suvarṇa (R5)"
risk_class: "high (output change: reason text and possibly `admissible_clean` / `held_out` on 63 rows; downstream re-score)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-05, TI-L5-06, TI-L5-07, TI-L5-08]
ledger_gap_ids: ["mi_jivanaghatana-Earn.build_record", "mi_jivanaghatana-Cost.baseline", "mi_jivanaghatana-Complete.depth", "mi_jivanaghatana-Build.history", "mi_jivanaghatana-Carr.detector", "new: jiva-N1", "new: jiva-N2", "new: jiva-N3", "new: jiva-N4", "new: jiva-N5", "new: jiva-N6", "new: jiva-N7", "new: jiva-N8"]
---

# mi_jivanaghatana — Clean-evidence vault and leakage partition: the admissible / held-out projection of the LEL

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_jivanaghatana.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :184). Reads the chart's `life_events` rows (`SELECT * ... WHERE chart_id = %s`, :215), builds one `mimamsa_event_provenance` row per event (63 for the canonical chart) and replaces the chart's rows (delete-then-insert, :356). The columns it computes: `shaped_predictor` (:310), `disclosure_timing` (:305), `admissible_clean` + `admissibility_reason` (`_admissibility`, :100-107), `held_out` (`MD5(event_id) mod 10 >= 8`, `_held_out`, :94-98), `event_class_id` (a documented declared NULL, :124-169). It is the root of the L5 calibration loop: `mi_pramana`, `mi_pariksha`, `mi_bhavisya` and `mi_darshana` declare it as a dependency. It raises when the chart has LEL rows but built zero provenance rows (A8, :244) and when every event was dropped (A9, :368) — a real detector, not a note.

**Canonical chart state (read-only, 2026-10-03).** 63 provenance rows for 63 `life_events` rows, one-to-one in both directions (`prov_vs_le_ids`: 0 unmatched). `admissible_clean` true 63/63; `held_out` 13 (20.6%); `shaped_predictor` false 63/63; `disclosure_timing` `unknown` 63/63; `event_class_id` NULL 63/63; `event_magnitude` NULL 63/63; one distinct `admissibility_reason` for all 63 (`prov`). Built 2026-09-06, i.e. after the 2026-08-13 downstream L5 builds, so those rows were built against an earlier provenance generation (inferred from timestamps; 4 calibration rows now point at an event id absent from both tables, CF-L5-02).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2865` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_jivanaghatana.py:173` `@register("mi_jivanaghatana")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_event_provenance`; count_sql tables: `mimamsa_event_provenance` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_event_provenance WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 63 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `lit`, rows_written 63, last_built_at 2026-09-06T10:55:02Z; recent canonical runs: complete 2026-09-06; complete 2026-09-06; error 2026-09-05; complete 2026-08-08 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `bg_ghatana` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_bhavisya`, `mi_darshana`, `mi_pariksha`, `mi_pramana` (registry); census transitive blocking radius 9 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | `bg_ghatana` is declared but never read: `_lookup_event_class` is a documented no-op (`del conn, category, subcategory`, :169) and the writer reads only `life_events` (undeclared, see `lel_events`) and `information_schema.columns` (:206, no schema filter). The unscoped fallback `SELECT * FROM life_events ORDER BY event_id` (:219) is dead while `life_events.chart_id` exists, but would read every chart if reached. | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | `mi_pramana.py:333-340` (the matching input), `mi_pariksha.py` retrodiction (:150-160) and control_windows (:290-300), views `vw_mimamsa_admissible_clean` / `vw_mimamsa_held_out` (`facts.views`). **No served capability module selects `mimamsa_event_provenance`** (census reach: none; Dens.served N/A, 0 modules; declarations `served_surface: None`); `outcome.py` and `producer_editorial_review.ts` only mention it. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_jivanaghatana.py` (12 tests), `tests/test_lel_calibration.py`; the B04 honesty tests (`writers/tests/test_b04_mi_honesty.py`) are source-text checks | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | the only L5 asset with a canonical-chart receipt: `proven`, observed 2026-09-06T10:55:02Z, output digest and spec sha both present (`asset_provenance_receipts`); freshness `fresh` (`asset_freshness`, same instant); digest spec reviewed 2026-09-06T10:49Z (`asset_output_digest_specs`); throughput `lit`, `built_against_writer_hash` ab15008f71f8… . History: run 21e3d6e6 (2026-09-05) errored `provenance: Object of type UUID is not JSON serializable` — the orchestrator's `canonical_upstream_hash` (`asset_runner.py:157-181`, error raised at `asset_runner.py:1135`) before the writer ran; two completes on 2026-09-06 after the fix (#1856). | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (1 unfrozen ancestor) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). Line numbers inside quoted census text are as of the saved run (older code), not main. NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_event_provenance (mi_jivanaghatana.py:356) |
| Build | Build.target † | PASS | target_table=mimamsa_event_provenance |
| Build | Build.dag † | PASS | 1 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | PASS | rows_written=63 = live=63 (count_sql over the target table; chart 482012f1) |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4c4ed2c4 complete/build (2026-09-06) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4c4ed2c4 complete/build (2026-09-06) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=63) |
| Complete (information) | Complete.depth | PARTIAL | 63 rows, 20 cols; fully populated 14; NEVER populated ['shaped_predictor_refs', 'disclosure_date', 'domain_secondary', 'event_magnitude', 'lel_file_sha', 'event_class_id'] |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 2 error(s) and 4 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-05): provenance: Object of type UUID is not JSON serializable |
| Build | Build.dep_liveness | PASS | 1/1 declared dependencies lit at chart 482012f1 (or global) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> NO_DETECTOR.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_jivanaghatana-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4c4ed2c4 complete/build (2026... |
| mi_jivanaghatana-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4c4ed2c4 complete/build (2026... |
| mi_jivanaghatana-Complete.depth | Complete.depth | information | measured: 63 rows, 20 cols; fully populated 14; NEVER populated ['shaped_predictor_refs', 'disclosure_date', 'domain_secondary', 'event_magnitude',... |
| mi_jivanaghatana-Build.history | Build.history | history | measured: latest run complete, but 2 error(s) and 4 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest er... |
| mi_jivanaghatana-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: jiva-N1 | Earn / Null | real (earned-signal) | `admissible_clean` and its reason "clean: not a predictor, not post-hoc undated, has event_date" assert two negatives the source cannot tell. `life_events` has none of the columns the writer reads for them (`shaped_predictor`, `shaped_predictor_refs`, `disclosure_timing` / `disclosure_type`, `disclosure_date`, `event_magnitude` / `magnitude`, `subcategory`, `attestation_source`, `event_class`: 0 of 10 exist, `le_missing_cols`), so :310 `bool(ev.get("shaped_predictor", False))` is always False and :305 always yields `unknown`; `_admissibility` can exclude only on a missing `event_date` (0 of 63). The flag is true on 63/63 by construction and the two exclusions can never fire (T1 section 7.3: an observation reported after the person has seen the forecast is not automatically independent). The schema makes the honest form impossible: `shaped_predictor` and `admissible_clean` are NOT NULL booleans (table profile) — the HONEST-FIX-BLOCKED-BY-DISHONEST-SCHEMA class |
| new: jiva-N2 | Null / design | real + SS question | the held-out vault is a hash split, not a sealed test: `MD5(event_id) mod 10 >= 8` (:94-98) puts 13 events in `held_out`, all of which pre-date the latest training event (`prov_heldout_chrono`: latest held-out event 2025-07-01, latest training event 2026-04-17; 49 of the 50 training events also pre-date the latest one): the held-out events are a random 20% drawn from the same period as the training events, not a later sealed period; `mechanism_retrodiction_get` uses a different rule (sealed `event_date < 2020-01-01`, `query_mechanism_retrodiction.ts:59`). Two holdout rules in one layer (CF-L5-06, Q-L5-07) |
| new: jiva-N3 | leakage | real | the `recorded_at` leakage routing is computed in memory only: `self.leakage_partitions` (:193, :319) is never persisted and no downstream writer reads it (grep), and `snapshot_at` comes from `ctx.config["prediction_snapshot_at"]` (:61-71), a key the orchestrator never sets (its config is `{chart_id, birth_params}`, `asset_runner.py:1121`), so every event partitions `training`. The two-key blind path described in the docstring is not wired into `mi_pramana`, which matches every non-held-out clean event whatever its `recorded_at` (CF-L5-03) |
| new: jiva-N4 | Build.dag | real | declared `bg_ghatana` unread; `lel_events` read undeclared (CF-L5-07) |
| new: jiva-N5 | event_class_id | real | permanent declared NULL (:124-169): honest, but it blocks every downstream base rate (`mi_pramana._load_base_rates` returns {} for this reason); `brahma_event_ontology.lel_category` maps one-to-many (career -> 5 classes) and its `matching_rules` jsonb is consumed by no writer |
| new: jiva-N6 | code | information | dead unscoped fallback (:219) and an unfiltered `information_schema` query (:206); T2c delta already asks to remove the legacy fallback |
| new: jiva-N7 | Dens / Reach | information | no served module reads the table; 6 columns never populated (`shaped_predictor_refs`, `disclosure_date`, `domain_secondary`, `event_magnitude`, `lel_file_sha`, `event_class_id`; census Complete.depth) |
| new: jiva-N8 | Null / Narr | detector | declarations: `prose_fields: None`; `admissibility_reason` is generated text (a fixed sentence); propose `prose_fields: ["admissibility_reason"]` with a golden-value test once FD-1 lands (CF-L5-14) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `admissible_clean` / `admissibility_reason` | the event is not predictor-shaped, not post-hoc undated, has a date | `_admissibility` (:100-107) over a constant `shaped=False` and `disclosure_timing="unknown"` | **constant / unearned**: true on 63/63 by construction; no code path can make it false except a missing date |
| `shaped_predictor` | the event shaped a predictor | `bool(ev.get("shaped_predictor", False))` on a column that does not exist (:310) | **constant False** — a proxy of nothing |
| `disclosure_timing` | when the event was disclosed relative to the framework | `ev.get("disclosure_timing") or ... or "unknown"` (:305) | honest null written as the word `unknown` (earned) — but then ignored by `_admissibility`, which only tests `post_framework_undated` |
| `held_out` | the event is held out for validation | `md5(event_id) mod 10 >= 8` (:94-98) | earned as a hash; **not earned as a validation vault** (not chronological, not blind: drawn from the same period as the training events) |
| `event_class_id` NULL | class unresolved | declared no-op (:124-169) | **earned null** with a stated reason in the docstring (the model for the layer) |
| leakage partition (in memory) | event is training vs outcome evidence for a snapshot | `recorded_at_partition` (`lel_calibration.py:135-157`) with `snapshot_at=None` | computed, never stored, never read: a detector with no consumer |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: `event_class_id` and `event_magnitude` are NULL with a stated reason; the empty-chart case returns zero rows with a note (:228-236) and the wrongly-empty case raises (:244).
- BAD: the same honesty was not applied to `shaped_predictor` and `admissible_clean`, which are written as measured values from inputs that do not exist.
- `disclosure_timing = 'unknown'` on 63/63 is the truthful state and should be what downstream reads (FD-1).

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** The writer coerces `chart_id = str(ctx.config.get("chart_id") or "")` (:187) and uses it only as a SQL parameter and in log text; no `json.dumps`, `canonical_json` or `stable_uuid` takes it (grep over all 14 `mi_*` writers and `services/mi_bhara`, `services/mi_sankalpa`: none). The only UUID-in-JSON failure recorded for L5 is the orchestrator's: run 21e3d6e6 (2026-09-05), fixed on main by an explicit `str(chart_id)` in `canonical_upstream_hash` (#1856); this asset then completed twice on 2026-09-06. **It is the only canonical-chart L5 asset that has run through the fixed path**: `mi_kula` and `mi_vistara` (global, `chart_id` None) ran on 2026-09-06; the other 11 chart-scoped assets last executed their writers on or before 2026-08-13 (completes; `mi_bhara`'s last executions errored), and eight of them were then recorded `error` on 2026-08-21 as BLOCKED without running, so the fixed provenance path is unproven for them.
- **Outcome-leakage guard:** see jiva-N3: the firewall's partition function exists and is tested but its result is not stored and `snapshot_at` is never supplied; the leakage controls that actually operate in L5 are the held_out hash and the `chart_context_stale_at` filter, neither of which compares an event's `recorded_at` to a prediction's `emitted_at`. L5 has no build-time detector that reads false when an outcome pre-dates its prediction (CF-L5-03). The Paripraśna `calibration_leak_guard.ts` is a key-name check on served envelopes and is not this control.
- **People-entered data (N-46) / LEL data contract:** Reads `life_events` and writes only `mimamsa_event_provenance`, which INV lists as regenerable (rebuilt freely). No people-entered column is written. Because the partition and flags are derived, FD-1..FD-3 may change them without touching any entered row.

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_jivanaghatana.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — the projection is deterministic, chart-scoped and raises on a wrongly empty build, but its two headline flags (`admissible_clean`, `held_out`) claim more than the code can know. Qualify = keep the asset, make the flags say what they establish.

Approver under Track A brief section 10: **Steward (G16); label and flag changes to Strategic Suvarṇa (R5)**. Risk class: **high (output change: reason text and possibly `admissible_clean` / `held_out` on 63 rows; downstream re-score)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make admissibility say what it establishes (R)

- **Answers:** jiva-N1; CF-L5-04; Q-L5-05
- **Change:** write `admissibility_reason` as `unverified: shaped_predictor and disclosure_timing are not recorded in life_events` when the inputs are absent; add an additive nullable `admissibility_basis` ('verified' | 'unverified_inputs') and make `shaped_predictor` nullable (NULL = unknown) so the honest value is storable; downstream decides (Q-L5-05) whether unverified rows are calibration-eligible (recommended: eligible, labelled)
- **Files / declaration / migration:** `mi_jivanaghatana.py:100-107,305-317`; one additive migration (nullable columns); digest spec re-review (`asset_output_digest_specs`)
- **Failing-first test and mutation:** failing-first: an event with no disclosure inputs yields basis `unverified_inputs` and a reason beginning `unverified`; mutation: restore the constant sentence -> FAIL. Golden-value test for the reason text (CF-L5-04)
- **Output change:** yes: reason text on 63 rows; `shaped_predictor` NULL on 63 rows; `admissible_clean` unchanged under the recommended option -> SS (R5)
- **Blast radius:** mi_pramana, mi_pariksha, mi_bhavisya, mi_darshana read these columns
- **Rebuild:** needs production rebuild (mi_jivanaghatana, then dependents) — REVIEW for SS
- **Gate it moves:** Earn, Null, Narr
- **Fix class:** data (output change) + writer code + additive migration; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-05

### FD-2 · Persist the recorded-at partition so the firewall can be applied from stored data (R)

- **Answers:** jiva-N3; CF-L5-03
- **Change:** store `recorded_at` (copy) on each provenance row (additive, nullable) so `mi_pramana` can compare it with `mimamsa_predictions.emitted_at`; stop computing a partition that nothing reads, or wire `prediction_snapshot_at` from the predictions table instead of `ctx.config`
- **Files / declaration / migration:** `mi_jivanaghatana.py:61-71,190-193,319`; additive migration
- **Failing-first test and mutation:** failing-first: provenance carries `recorded_at`; mutation: drop the column write -> the `mi_pramana` chronology test (FD-1 there) fails
- **Output change:** additive column; no existing value changes
- **Blast radius:** mi_pramana consumes it
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn (leakage)
- **Fix class:** writer code + additive migration; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-06

### FD-3 · One holdout rule (R)

- **Answers:** jiva-N2; CF-L5-06; Q-L5-07
- **Change:** replace the md5 20% split by the pre-registered sealed date split already used by `mechanism_retrodiction_get` (event_date < 2020-01-01 is training; later is sealed) or declare both rules by name and stop calling the hash split 'held out'
- **Files / declaration / migration:** `mi_jivanaghatana.py:94-98`; `asset_declarations.json`
- **Failing-first test and mutation:** failing-first: membership of `held_out` equals the declared rule on the 63 events; mutation: change the cutoff -> membership changes
- **Output change:** yes: `held_out` membership changes for some of the 63 events -> SS (R5)
- **Blast radius:** mi_pramana, mi_pariksha read `held_out = false`
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Null, Vocab
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-07

### FD-4 · Remove dead code, declare the real reads

- **Answers:** jiva-N4, jiva-N6; CF-L5-07
- **Change:** delete the unscoped fallback (:219), schema-qualify the `information_schema` query, drop the unread `bg_ghatana` edge, add `lel_events`
- **Files / declaration / migration:** `mi_jivanaghatana.py:206-219`; registry migration (with the `lel_events` FD-1)
- **Failing-first test and mutation:** failing-first: a table without `chart_id` raises instead of reading all charts; mutation: restore the fallback -> FAIL
- **Output change:** none
- **Blast radius:** DAG only
- **Rebuild:** none
- **Gate it moves:** Build.dag, Idem
- **Fix class:** writer code + registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-08

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — control case: rebuilt 2026-09-06, its rows match main's current code (unlike the 2026-08-13 assets)
- **CF-L5-03** — jiva-N3: no chronology control reaches calibration
- **CF-L5-04** — jiva-N1: constant status flag
- **CF-L5-06** — jiva-N2: two holdout rules
- **CF-L5-07** — jiva-N4
- **CF-L5-11** — only asset with a canonical-chart receipt
- **CF-L5-14** — prose_fields for `admissibility_reason`

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped; deterministic. Stable columns: every column except `created_at` (insertion clock). `held_out` is a pure function of `event_id` (md5), `admissible_clean` of the constant inputs; a re-run on an unchanged LEL must be byte-identical. Exclude `created_at`; pin nothing else.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** The one-row-per-event provenance projection, the deterministic partition function, the declared-null `event_class_id`, and the two RuntimeError guards (A8, A9).
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): recompute `held_out` from `event_id` with an independent md5 and compare for all 63 rows; the admissibility flags have no classical source to correspond to.
- **Opportunities (never blocking):** derive `event_class_id` where the ontology mapping is one-to-one (5 `lel_category` values per the docstring) as real derivation work, not a pick; a `learned_at` input from the LEL (see `lel_events`) would make admissibility computable.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-05** — Status flags: replace the constant / proxy flags (`admissible_clean`, `shaped_predictor`, `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear`, `leakage_status = clean`, `skill_score` on underpowered rows) by detectors or NULL / `not_assessed`; allow the DDL changes this needs (nullable columns, additive basis columns)? *Recommendation:* Yes; unverified admissibility stays calibration-eligible but labelled `unverified_inputs`. (R)
- **Q-L5-07** — One holdout rule: the hash split `md5(event_id) mod 10 >= 8` (13 events, not chronological), the sealed date split `event_date < 2020-01-01` used by `mechanism_retrodiction_get`, and the `recorded_at` partition exist side by side. Which is THE pre-registered holdout? *Recommendation:* The sealed date split; the hash split is retired or renamed `sample_split`. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
