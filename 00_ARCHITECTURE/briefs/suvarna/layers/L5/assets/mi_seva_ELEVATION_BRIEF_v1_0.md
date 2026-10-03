---
asset_id: mi_seva
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
disposition: "retire"
disposition_proposal_approver: "Strategic Suvarṇa (R5: retirement)"
risk_class: "low (no rows; registry/DAG change; the table `mimamsa_preferences` stays unless SS also retires it)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-46, TI-L5-47]
ledger_gap_ids: ["mi_seva-Idem.pattern", "mi_seva-Earn.build_record", "mi_seva-Cost.baseline", "mi_seva-Complete.depth", "mi_seva-Vocab.identity", "mi_seva-Build.history", "mi_seva-Build.dep_liveness", "mi_seva-Carr.detector", "new: seva-N1", "new: seva-N2", "new: seva-N3", "new: seva-N4", "new: seva-N5", "new: seva-N6"]
---

# mi_seva — Serve-time apply handler: a four-table readiness check for overlays (service, DRAFT)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_seva.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :34). The docstring says it 'applies calibration overlays at serve time ... writes a journal entry to mimamsa_journal when a prediction is surfaced' and points at `services/mi_seva/handler.py (TypeScript retrieval layer)`. **No such file exists** (`platform/python-sidecar/services` holds `mi_bhara`, `mi_sankalpa`, `mimamsa`); `git grep` finds no serve-time code that applies overlays and no writer of `mimamsa_journal` (migration 691 line 900 records the same). What the writer actually does: query `information_schema.tables` for four tables (`mimamsa_multipliers`, `mimamsa_signal_adjustment`, `mimamsa_insight_units`, `mimamsa_journal`) and raise `RuntimeError` if one is absent (A1, :70); otherwise return `rows_inserted = 0`. The declared target `mimamsa_preferences` is read and written by nobody (0 rows).

**Canonical chart state (read-only, 2026-10-03).** 0 rows in the target table (whole table). Catalog `DRAFT` live and in the seed. Throughput `stale` since 2026-08-13; the census reads Build.completion FAIL for it (a state, not a fault: nothing to count).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | service / per_chart / service | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3060` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_seva.py:25` `@register("mi_seva")`; registry `has_writer` = t, `asset_kind` = service | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_preferences`; count_sql tables: `mimamsa_preferences` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_preferences` | registry |
| live rows (canonical chart) / floor | 0 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | DRAFT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `stale`, rows_written 0, last_built_at 2026-08-13T01:17:19Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-07-28; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_adhilepa` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no dependents); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `mi_adhilepa` (live). The writer reads no `mi_adhilepa` output, only table existence; it names tables owned by `mi_gunanaka`, `mi_adhilepa`, `mi_darshana` and `mi_abhilekha`'s input `mimamsa_journal` (no owner). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | none: no code selects `mimamsa_preferences` (`git grep`: seed and `assetClearSpec.ts` only). The effect contract is checked by `tests/test_purna_anvesana_service_effect_contracts.py` against `scripts/nirmana_service_effect_contracts.json` (`readiness_read`, `writes: []`). | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_purna_anvesana_service_effect_contracts.py::test_mi_seva_readiness_contract_matches_source` (source-text lock), `platform/docs/evidence/purna_anvesana_wave1_disposable.json` (disposable-fixture evidence) | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | none: no receipt, no freshness row, no digest spec; `service_health` and `last_selftest_at` NULL in the registry (the service self-test fields that `ka_*` services use are unused); throughput `stale` 2026-08-13T01:17:19Z; build history 28 errors / 10 aborts on record, last run complete | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (62) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) ['mimamsa_preferences'] anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: mi_seva.py] |
| Build | Build.target † | PASS | target_table=mimamsa_preferences |
| Build | Build.dag † | PASS | 1 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | PARTIAL | rows_written=0 = live=0 (count_sql over the target table; chart 482012f1 (global count_sql; no global build row)); target_floor=0 declares zero rows complete, but this is a writer-backed data asset (has_writer=true) with no layer-plan claim that the emptiness is by design — indistinguishable from a writer that has never produ... |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete (information) | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 4 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (user_id, channel_id) is vacuous on 0 rows |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 28 error(s) and 10 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) mi_adhilepa did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_adhilepa (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> NO_DETECTOR.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_seva-Idem.pattern | Idem.pattern | detector | measured: no idempotency pattern in the writer's own SQL — it likely delegates; verify there / required: the Idem gate's claim |
| mi_seva-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_seva-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_seva-Complete.depth | Complete.depth | information | measured: NO_DETECTOR — table empty (0 rows, 4 cols): column population cannot be measured on no rows / required: the Complete gate's claim |
| mi_seva-Vocab.identity | Vocab.identity | detector | measured: NO_DETECTOR — table empty: uniqueness under (user_id, channel_id) is vacuous on 0 rows / required: the Vocab gate's claim |
| mi_seva-Build.history | Build.history | history | measured: latest run complete, but 28 error(s) and 10 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest ... |
| mi_seva-Build.dep_liveness | Build.dep_liveness | stale | measured: 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_adhilepa (error, chart 482012f1)'] — a DEP-ASSERT trap if no ... |
| mi_seva-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: seva-N1 | Earn (the asset's claim) | real (earned-signal) | the asset's name and docstring claim serve-time application of calibration; the detector behind its `complete` state is a table-existence check. Even the layer instance's T2c says: "four-table existence check proves only that; require actual authorized service and consumer-effect proof later". A complete build of this asset proves nothing about overlays being applied (§N.8) |
| new: seva-N2 | phantom pointer | real | `services/mi_seva/handler.py` does not exist; `mimamsa_journal` has no writer anywhere; `mimamsa_preferences` has no reader or writer. The asset is the stub of a service that was never built (CF-L5-09) |
| new: seva-N3 | doctrine | real + SS question | if a serve-time handler were built as described ("applies calibration overlays ... to produce an adjusted reading bundle"), it would put learned personal multipliers into served readings — the T2 section 6.6 / collect-only rule says calibration must not reach serving envelopes, and the `calibration_leak_guard.ts` exists to fail that. The described design conflicts with the doctrine; retiring the description is the safe resolution (Q-L5-13) |
| new: seva-N4 | registry | real | kind `service` but `service_health`, `last_selftest_at`, `selftest_detail` NULL and no self-test; no digest spec (12 other L5 assets have one); `catalog_status DRAFT` while 14 sibling assets are CURRENT |
| new: seva-N5 | Build.dag | real | declared `mi_adhilepa` edge is not a read; the four tables it checks belong to other assets (CF-L5-07) |
| new: seva-N6 | history | history | 28 errors / 10 aborts / many queued rows on record (Build.history FAIL on the saved census): a record of past blocking and reaping, no edit changes it (CF-L5-12) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| build state `complete` | serve-time apply infrastructure is verified | 4-table `information_schema` check (:39-70) | **proxy of existence** (explicitly "build-time readiness only" in the effect contract) |
| `rows_inserted = 0` | no build-time rows | literal | earned |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: the missing-table case raises (A1) instead of a note nothing read; the effect contract states the limit in its own words: "This verifies build-time service readiness only; it does not prove serve-time overlay behavior or deployment."
- `mimamsa_preferences` is empty because nothing writes it: an honest empty, but with no producer the table cannot ever be non-empty.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** Global handler (`scope` per_chart in the registry, no use of `chart_id` in the code): no id is read from `ctx.config` or serialised. Not exposed.
- **Outcome-leakage guard:** N/A as built (reads no data). As described, it would apply learned multipliers at serve time: see seva-N3.
- **People-entered data (N-46) / LEL data contract:** writes nothing; the tables it names include `mimamsa_journal` (unclassified, protected by default, INV) which it neither reads nor writes.

## 3 · Disposition

DISPOSITION: retire

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_seva.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**retire (R) proposed** — the asset verifies four tables exist and describes a handler that does not exist and, as described, would conflict with the collect-only doctrine. Proposal: retire the asset and keep the existence check as a layer self-test inside `mi_vistara` / `mi_abhilekha` or the census; SS decides (Q-L5-13). If SS prefers to keep it, the minimum is renaming it a readiness check and declaring it so.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5: retirement)**. Risk class: **low (no rows; registry/DAG change; the table `mimamsa_preferences` stays unless SS also retires it)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Retire the asset (R)

- **Answers:** seva-N1, N2, N3, N4; Q-L5-13
- **Change:** mark `mi_seva` retired (registry `is_active = false`, `superseded_by` the layer self-test); drop the dependents (none) and the `mi_adhilepa` edge; keep the four-table check as a function in the census or in `mi_vistara`; leave `mimamsa_preferences` in place pending a separate table decision
- **Files / declaration / migration:** registry migration (surgical, verified applied); `mi_seva.py` kept or moved; `nirmana_service_effect_contracts.json`; `tests/test_purna_anvesana_service_effect_contracts.py`
- **Failing-first test and mutation:** failing-first: the census sees one fewer active L5 asset and the self-test still raises on a missing table; mutation: remove a table in a disposable DB -> the self-test fails
- **Output change:** none (no rows)
- **Blast radius:** no dependents; Nirmāṇa manifest of this asset (not frozen)
- **Rebuild:** none
- **Gate it moves:** Build, Earn
- **Fix class:** registry/declaration (retirement); **buildable before J1:** tier-independent in content; retirement is R5 for SS
- **Track I item:** TI-L5-46

### FD-2 · If kept: say what it is

- **Answers:** seva-N1, N4
- **Change:** rename/describe as a readiness check; add a probe contract and a self-test (`service_health`) so the success signal is a probe, not a table list; set `catalog_status` honestly
- **Files / declaration / migration:** `mi_seva.py` docstring; registry row; declarations
- **Failing-first test and mutation:** the service-probe test; mutation: break a table -> `unhealthy`
- **Output change:** none
- **Blast radius:** registry rows
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** declaration/registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-47

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-09** — seva-N2: stub of an unbuilt service
- **CF-L5-07** — seva-N5
- **CF-L5-10** — doctrine conflict if built as described
- **CF-L5-11** — no receipt, no spec
- **CF-L5-12** — Build.history record

## 5 · Semantic fingerprint contract (for E5.5)

No output rows. Nothing to fingerprint; the contract file `nirmana_service_effect_contracts.json` entry is the specification.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the raise-on-missing-relation check (A1) as a layer self-test.
- **Carriage check chosen (T4 §4.1; one only):** Carr N/A by cause (no derivation); the effect contract already records the limit.
- **Opportunities (never blocking):** a single layer self-test that raises when any `mimamsa_*` relation the served tools read is absent would replace three half-services.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-13** — Service assets: retire `mi_seva` (a four-table existence check describing a handler that does not exist and that, as described, would apply learned multipliers at serve time against the collect-only doctrine)? Keep `mi_vistara` and bind it to a working exporter? Mark `mi_abhilekha` per Q-L5-12? *Recommendation:* Retire mi_seva; keep mi_vistara with an exporter aligned to the live ledger DDL; qualify mi_abhilekha. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
