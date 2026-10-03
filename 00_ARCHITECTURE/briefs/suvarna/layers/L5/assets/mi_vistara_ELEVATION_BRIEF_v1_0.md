---
asset_id: mi_vistara
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); a decision to retire or bind it to the exporter goes to Strategic Suvarṇa (R5)"
risk_class: "low (no rows; exporter schema alignment is a code change on a manual CLI)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-44, TI-L5-45]
ledger_gap_ids: ["mi_vistara-Idem.pattern", "mi_vistara-Earn.build_record", "mi_vistara-Cost.baseline", "mi_vistara-Complete.depth", "mi_vistara-Vocab.identity", "mi_vistara-Carr.detector", "new: vis-N1", "new: vis-N2", "new: vis-N3", "new: vis-N4", "new: vis-N5", "new: vis-N6"]
---

# mi_vistara — Export-integrity ledger: a readiness verifier for `mimamsa_export_log` (global, append-only)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_vistara.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT, **global** writer (`run(ctx)`, :38). It writes nothing. It checks that `mimamsa_export_log` exists (raises `RuntimeError` if not, :51) and counts its rows (:56), returning `rows_inserted = 0` with a note. The module docstring says the ledger's rows are 'inserted by the mi_seva service handler when exports are actually delivered' — no such handler exists (see `mi_seva`). The only code that inserts into the table is the CLI exporter `brahmagyan/mimamsa/export_to_bigquery.py:342`, whose INSERT column list (`export_id, export_at, table_name, row_count, gcs_path, source_citation`) **does not match the live table** (`export_id, chart_id, exported_at, export_format, recipient_ref, included_insight_ids, contribution_state, calibration_mode, disclosures_attached, payload_hash, lel_version, export_formula_version`). So, by code reading against the live column list, no code path in the repository can write a row of the live shape (not exercised: write path). The table is 0 rows.

**Canonical chart state (read-only, 2026-10-03).** 0 rows (whole table; `exp`). Build state: complete every time. The asset has never held a row and nothing can currently put one there.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / global / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3043` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_vistara.py:29` `@register("mi_vistara")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_export_log`; count_sql tables: `mimamsa_export_log` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_export_log` | registry |
| live rows (canonical chart) / floor | 0 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | no throughput row for the canonical chart; recent canonical runs: complete 2026-09-06; complete 2026-09-06; complete 2026-09-05; complete 2026-09-05 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | none | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no `depends_on`, no dependents); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | No declared dependencies; the writer reads only `information_schema.tables` and `COUNT(*)` of its own table. Declarations: kind NOT DECLARED (sources disagree: registry `data`, seed default, service-like behaviour). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | none: no capability module, tool, or writer reads `mimamsa_export_log` except the verifiers `mi_seva.py:39-43` (existence check of other tables, not this one) and this writer; `asset_registry_seed.ts` and `assetClearSpec.ts` name it. Census: Dens.served N/A, 0 modules; width 0.0. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mimamsa_export.py` (exporter, against the phantom column list), `platform/scripts/governance/__tests__/test_w2_3_deeper_detectors.py` (mentions only); no test of `mi_vistara.run` | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | `proven` global receipt (`__global__`) observed 2026-09-06T10:31:45Z with output digest and spec sha; freshness `fresh` (observed 2026-09-05T16:56Z); digest spec reviewed 2026-09-05T14:28Z — a digest spec for a writer that writes no output, so the receipt proves a run happened, not that an export ledger exists; last run complete 2026-09-06 (39 complete runs, 0 errors) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-NO-ROUTE (0 unfrozen ancestors, no W2 analysis/verdict) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) ['mimamsa_export_log'] anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: mi_vistara.py] |
| Build | Build.target † | PASS | target_table=mimamsa_export_log |
| Build | Build.dag † | PASS | 0 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | PARTIAL | rows_written=0 = live=0 (count_sql over the target table; global); target_floor=0 declares zero rows complete, but this is a writer-backed data asset (has_writer=true) with no layer-plan claim that the emptiness is by design — indistinguishable from a writer that has never produced a row |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run e812179e complete/skip_no_delta (2026-09-06) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run e812179e complete/skip_no_delta (2026-09-06) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete (information) | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 12 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (export_id) is vacuous on 0 rows |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PASS | 39 complete, no error or abort; 3 skip_no_delta (healthy) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> NO_DETECTOR.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_vistara-Idem.pattern | Idem.pattern | detector | measured: no idempotency pattern in the writer's own SQL — it likely delegates; verify there / required: the Idem gate's claim |
| mi_vistara-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run e812179e com... |
| mi_vistara-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run e812179e com... |
| mi_vistara-Complete.depth | Complete.depth | information | measured: NO_DETECTOR — table empty (0 rows, 12 cols): column population cannot be measured on no rows / required: the Complete gate's claim |
| mi_vistara-Vocab.identity | Vocab.identity | detector | measured: NO_DETECTOR — table empty: uniqueness under (export_id) is vacuous on 0 rows / required: the Vocab gate's claim |
| mi_vistara-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: vis-N1 | phantom schema | real | `export_to_bigquery.py:342-365` INSERTs into columns the table does not have (same defect class as the retired `record_outcome`, CR-115/CR-128); its docstring (:11-14) also describes an older log shape. Either the exporter or the table is out of date; the live table (migration 355) is the richer one (payload hash, included insight ids, disclosure bundle, calibration mode), i.e. the one the product definition needs for export integrity |
| new: vis-N2 | Earn (completion) | real (earned-signal) | the asset reads `lit`/complete on every run while holding 0 rows and having no writer path for the live shape: the success signal is "the table exists", not "an export ledger is being kept" (§N.8; layer-instance T2c: "verify exporter wiring, payload identity/scope and delivered artifact") |
| new: vis-N3 | Earn (receipt) | real | a digest spec and a `proven` receipt exist for an asset whose output is nothing; the receipt's `output_digest` is the digest of an empty set |
| new: vis-N4 | doc | information | the module docstring names `mi_seva` as the inserter; no `mi_seva` insert exists (CF-L5-09) |
| new: vis-N5 | kind | information | kind not declared (registry `data`, behaves as a service); `scope: global` but the ledger is keyed `chart_id` in its columns (a global verifier of a per-chart ledger) |
| new: vis-N6 | people data | information | the exporter has `--include-life-events` (export of `life_events` to BigQuery, "calibration only"); it is a manual CLI, not wired to any route; recorded because it is the one path by which the people-entered LEL could leave the database (CF-L5-08) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| build state `lit` / complete | an export ledger is ready and kept | table exists (:46-56) | **proxy of existence**; no row, no writer for the live shape |
| `rows_inserted = 0` | no build-time rows | literal | earned: the asset is declared no-rows-at-build |
| receipt `proven` | the output is proven | digest of the empty table | proves a run, not content |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: the missing-table case raises (not a note), the same discipline as `mi_seva`.
- NOTE: 0 rows is an honest state for STRUCTURAL mode; the defect is that the success signal would read the same with a broken exporter.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** Global asset: no `chart_id` in `ctx.config`; the writer touches no id. Not exposed.
- **Outcome-leakage guard:** The exporter carries its own guard (`_assert_not_prediction_feed`, `export_to_bigquery.py:365`: a table-name gate keeping `life_events` out of prediction feeds); it is a name check, not a data-flow check. No outcome data is touched by this writer.
- **People-entered data (N-46) / LEL data contract:** no people-entered data written. The exporter's `--include-life-events` option would copy entered rows out; it does not modify them.

## 3 · Disposition

**keep (P)** — a small honest verifier; the fix is to give it something real to verify (a working exporter path against the live schema, or an explicit `not_built` state), not to remove it.

Approver under Track A brief section 10: **Steward (G16); a decision to retire or bind it to the exporter goes to Strategic Suvarṇa (R5)**. Risk class: **low (no rows; exporter schema alignment is a code change on a manual CLI)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Align the exporter with the live ledger or retire the exporter log

- **Answers:** vis-N1, vis-N4; Q-L5-13
- **Change:** either rewrite `_write_export_log` to the live columns (`export_id, chart_id, exported_at, export_format, recipient_ref, included_insight_ids, contribution_state, calibration_mode, disclosures_attached, payload_hash, lel_version, export_formula_version`) with a real payload hash, or declare the ledger `not_built` and have `mi_vistara` report that state
- **Files / declaration / migration:** `export_to_bigquery.py:325-365`; `tests/test_mimamsa_export.py`
- **Failing-first test and mutation:** failing-first: the exporter's log insert succeeds against a disposable DB with the live DDL; mutation: restore a phantom column -> the insert fails
- **Output change:** none (0 rows)
- **Blast radius:** manual CLI only
- **Rebuild:** none
- **Gate it moves:** Build.completion honesty
- **Fix class:** writer code (manual CLI) + test; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-44

### FD-2 · Make completion mean something

- **Answers:** vis-N2, vis-N3
- **Change:** return a note/state `no_exports_recorded` readable by the census (or declare the asset a service with a probe contract) instead of reading complete on existence; do not hold a digest spec for a no-output asset until a ledger exists
- **Files / declaration / migration:** `mi_vistara.py:39-70`; `asset_declarations.json` (kind); digest spec
- **Failing-first test and mutation:** declarations validation; the census reads the state
- **Output change:** none
- **Blast radius:** registry rows
- **Rebuild:** none
- **Gate it moves:** Earn, Build.completion
- **Fix class:** declaration/registry; **buildable before J1:** tier-independent; N/A rule needs SS approval
- **Track I item:** TI-L5-45

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-09** — service/verifier assets with no consumer
- **CF-L5-08** — LEL export option
- **CF-L5-11** — receipt/spec for a no-output asset
- **CF-L5-12** — Earn/Cost instrument absent
- **CF-L5-13** — kind not declared

## 5 · Semantic fingerprint contract (for E5.5)

Global, no output rows. Nothing to fingerprint beyond the table's DDL; exclude the receipt timestamps.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the raise-on-missing-table verifier and the append-only ledger design (the live DDL is the product-relevant part).
- **Carriage check chosen (T4 §4.1; one only):** Carr N/A by cause (no derivation; ledger of delivered exports); D3 not applicable.
- **Opportunities (never blocking):** the ledger columns (payload hash, included insight ids, disclosures attached, calibration mode) are exactly the export-integrity record T2 section 12 needs; a real exporter writing them is the opportunity.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-13** — Service assets: retire `mi_seva` (a four-table existence check describing a handler that does not exist and that, as described, would apply learned multipliers at serve time against the collect-only doctrine)? Keep `mi_vistara` and bind it to a working exporter? Mark `mi_abhilekha` per Q-L5-12? *Recommendation:* Retire mi_seva; keep mi_vistara with an exporter aligned to the live ledger DDL; qualify mi_abhilekha. (R)
- **Q-L5-15** — LEL write-path guards (N-46): `lel_intake seed` and `lel_event_writer` use ON CONFLICT DO UPDATE over event_date / description; ids are content-derived. Accept code-only guards (never overwrite a tightened/corrected row; correction ids derived from the original id; no seed re-run on a populated chart without a flag), with no data change? *Recommendation:* Yes. No entered row is changed or deleted by this lane or by the proposed fixes.
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
