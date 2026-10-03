---
asset_id: mi_bhara
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
disposition_proposal_approver: "Steward (G16); envelope and DDL changes to Strategic Suvarṇa (R5)"
risk_class: "medium (served `calibration_maturity` fields; DDL for nullable skill columns)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-51, TI-L5-52, TI-L5-53, TI-L5-54]
ledger_gap_ids: ["mi_bhara-Idem.pattern", "mi_bhara-Build.completion", "mi_bhara-Earn.build_record", "mi_bhara-Cost.baseline", "mi_bhara-Complete.depth", "mi_bhara-Build.history", "mi_bhara-Build.dep_liveness", "mi_bhara-Carr.detector", "new: bhara-N1", "new: bhara-N2", "new: bhara-N3", "new: bhara-N4", "new: bhara-N5", "new: bhara-N6", "new: bhara-N7", "new: bhara-N8"]
---

# mi_bhara — Kāla Bhāra: skill and goodness-of-fit of the temporal field against the LEL (research kernel, no refit yet)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

Stage 9 of the ṢAḌ-DARŚANA temporal-field pipeline, seated in L5 because it is the one place that may read the LEL (circularity guard; `tests/l5/test_mi_bhara_circularity_guard_w2.py`). `run(ctx)` (:94): pins the weights version once (`resolve_weights_version`, :115), requires `kala_field` (raises if absent, :128), loads the LEL events and open prospective-ledger predictions (:143-144), scores open predictions against events (`living_lel`), and — if the chart has events — `_fit_and_publish` (:227): per event class, skill against a deterministic circular-shift null (256 replicates, no RNG) and a time-rescaling GOF test, plus an aggregate row, into `kala_field_skill` and `kala_field_gof` (replace-prior scoped to chart x weights version x snapshot, `db.py:203-221`). The parameter **refit is not performed**: the docstring (:236-244) says it publishes skill and GOF against the as-built field until `kala_field` carries the basis columns; `weights_version` stays `v0_classical`. It also refreshes `kala_insights` (`upsert_biographical_echo_insights(conn, chart_id, [])`, :366: an empty list, which deletes the chart's `lel_derived` insights). Registry target `kala_field_skill`; the writer touches five tables (F-03 of the layer instance).

**Canonical chart state (read-only, 2026-10-03).** **7 `kala_field_skill` rows** (6 event classes + 1 aggregate; released 2026-08-09, `weights_version v0_classical`): `n_events` 1, 1, 1, 2, 1, 1 (aggregate 7), `n_prospective` 0 everywhere, `n_backfill` = `n_events`, `skill_state = underpowered` everywhere (the table's own CHECK ties `underpowered` to `n_events < 8`), `skill_prospective` NULL, **`skill_score` between -3.6e-15 and +5.3e-15** (floating-point noise around 0, forced by the NOT NULL column, stored beside the honest state). 6 GOF rows, all `underpowered`, with `ks_p` values from 0.0058 to 0.975 computed on n = 1 or 2 events. `kala_field_weight_versions`: 1 row (`v0_classical`, active, global). `kala_insights`: 0 rows for the chart. `kala_field`: 8,570,075 rows for the chart (`kfield`). `brahma_prospective_ledger`: 18 rows, all `open` (`pl`). None of the 7 skill rows is from the 2026-08-13 L5 build: the latest successful writer run produced them four days earlier.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3178` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py:87` `@register(ASSET_ID)` (constant id); registry `has_writer` = t; light writer with a `services/mi_bhara/` package (`weights.py`, `field.py`, `skill.py`, `gof.py`, `likelihood.py`, `fit.py`, `living_lel.py`, `basis.py`, `db.py`) | writers dir / census `Build.registered` |
| target table(s) (live registry) | `kala_field_skill`; count_sql tables: `kala_field_skill` | registry / census |
| count_sql (live) | `SELECT COUNT(*) FROM kala_field_skill WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 7 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 0, last_built_at 2026-08-21T02:28:16Z; recent canonical runs: error 2026-08-21; error 2026-08-13; error 2026-08-12; error 2026-08-12 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `ka_kshetra` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no dependents); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `ka_kshetra`. Reads: `kala_field` (`ka_kshetra`), `life_events` (undeclared, `lel_events`), `brahma_prospective_ledger` (open rows, `db.py:177-195`; unowned in the registry, TG-L5-006), `kala_field_weight_versions` (seeded by migration 476). Writes: `kala_field_skill`, `kala_field_gof`, `kala_insights` (and `kala_field_weight_versions` / `kala_field_weights` only on a refit that does not run). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `platform-mcp/src/lib/kala_envelope.ts:540-575` (`calibration_maturity.skill_score`, `n_events`, `n_prospective`, `weights_version` in every `kala_*` envelope), `platform-mcp/src/tools/kala_views/priority.ts` (comment/aggregate), `platform/src/app/api/mcp/db/query/route.ts`. Census: Dens.served N/A (0 modules; the reader lives in platform-mcp, outside `CAPS_ROOTS`); width 0.125. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/l5/test_mi_bhara_{skill,gof,fit,living_lel,field_likelihood,weights_acyclicity,circularity_guard_w2}.py`, `tests/test_mi_bhara_context_stale_filter.py`, `tests/l5/test_kala_timeline_spec.py`; the writer-level failure below has no regression test | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T17:50Z); throughput `error` 2026-08-21 (message: 'BLOCKED: upstream dependency(ies) timeout:600s did not complete' — the failed upstream is rendered as the timeout string, not an asset id; the declared upstream `ka_kshetra` is itself `error`, worker_crash 2026-09-11); `built_against_writer_hash` empty; last three writer-level runs (2026-08-12/13) errored `TypeError: float() argument must be a string or a real number, not 'NoneType'` at `services/mi_bhara/db.py:189` of the deployed code (`float(r["w_start"])`, now :191) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (35) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): kala_field_skill (services/mi_bhara/db.py:215 via mi_bhara.py → services/mi_bhara/db.py:replace_prior_skill_and_gof) |
| Build | Build.target † | PASS | target_table=kala_field_skill |
| Build | Build.dag † | PASS | 1 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=0, live=7, chart 482012f1) — see Build.history |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 257eb0c2 error/no disposition (2026-08-21) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 257eb0c2 error/no disposition (2026-08-21) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=7) |
| Complete (information) | Complete.depth | PARTIAL | 7 rows, 17 cols; fully populated 15; NEVER populated ['skill_prospective'] |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 19 error(s), 4 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) timeout:600s did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['ka_kshetra (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved N/A -> FAIL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_bhara-Idem.pattern | Idem.pattern | detector | measured: no idempotency pattern in the writer's own SQL — it likely delegates; verify there / required: the Idem gate's claim |
| mi_bhara-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=0, live=7, chart 482012f1) — see Build.history / required: the Build ga... |
| mi_bhara-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 257eb0c2 error/no disposition... |
| mi_bhara-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 257eb0c2 error/no disposition... |
| mi_bhara-Complete.depth | Complete.depth | information | measured: 7 rows, 17 cols; fully populated 15; NEVER populated ['skill_prospective'] / required: the Complete gate's claim |
| mi_bhara-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 19 error(s), 4 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_bhara-Build.dep_liveness | Build.dep_liveness | stale | measured: 0/1 declared dependencies lit at chart 482012f1 (or global); not live: ['ka_kshetra (error, chart 482012f1)'] — a DEP-ASSERT trap if no w... |
| mi_bhara-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: bhara-N1 | Earn / Null (skill_score) | real (consumer-visible) | `skill_score` is a float-noise number (|x| < 6e-15) on every row whose state is `underpowered`; the column is NOT NULL, the state column carries the truth, and `kala_envelope.ts:550,569` passes `skill_score` through numerically into every `kala_*` envelope's `calibration_maturity` without `skill_state` (the envelope has `n_events` and `prospective_resolutions` but not the state). A reader sees `skill_score: -5.15e-16, n_events: 7` and no word "underpowered". An underpowered skill should be null at the source (DDL) or masked at the envelope |
| new: bhara-N2 | Earn (GOF) | real | `kala_field_gof.ks_p` and `ljung_box_p` are published with n = 1..2 (e.g. `ks_p` 0.9750 for one childbirth event, 0.0066 for one foreign-settlement event); `gof_state = underpowered` is stored, the p-values are not nulled. Same class as bhara-N1 |
| new: bhara-N3 | Earn (n_prospective) | real | `n_prosp = min(n_prospective_resolutions, skill.n_events)` (:291) assigns the chart-wide count of resolved prospective predictions to **every** event class, capped by that class's n; `n_backfill = n_events - n_prosp`. A per-class split that is not per class: 0 today, but it would overstate prospective evidence in every class as soon as one prediction resolves |
| new: bhara-N4 | real defect (history) | real (production) | three consecutive production runs (2026-08-12/13) failed with `TypeError` at `services/mi_bhara/db.py:189`: `fetch_open_predictions` converted a NULL window bound to float. Main now filters `observation_window IS NOT NULL AND NOT isempty(...)` (`db.py:181`, commit 44d5ff5a7, #1299); whether the deployed container ran that code on the later attempts is not established (the latest record is the BLOCKED error). No regression test for an empty/NULL window was found |
| new: bhara-N5 | registry | real | declares one target table, writes five tables (`kala_field_skill`, `_gof`, `kala_insights`, and `kala_field_weight_versions` / `kala_field_weights` on a refit); the seed target (`kala_field_weight_versions`) differs from the live registry (`kala_field_skill`); `kala_field_weight_versions` is append-only and in INV as non-regenerable; census `reach` lists one module while `Dens.served` lists none (CF-L5-13) |
| new: bhara-N6 | scope of the work | information | the "research kernel" does not refit: with n_events = 1 per class no fit would be meaningful; the docstring is explicit that the refit is pending the basis columns. Honest, and consistent with STRUCTURAL mode; recorded so that nobody reads `weights_version v0_classical` as a fitted value |
| new: bhara-N7 | Build.dag | real | `life_events` and `brahma_prospective_ledger` read with no declared edge (`lel_events` has no asset; the ledger has no asset: TG-L5-006); the single declared edge `ka_kshetra` is in `error` and its 1,183,134 rows were written before a `worker_crash` (CF-L5-07, CF-L5-12) |
| new: bhara-N8 | biographical join | information | `upsert_biographical_echo_insights(conn, chart_id, [])` is called with an empty list (:366): it deletes the chart's `lel_derived` rows from `kala_insights` and inserts none, and the result `-1` (table absent) is the only signal; the Living-LEL join is declared deferred (`NOTE_BIO_JOIN_DEFERRED`). 0 rows now; if rows ever exist, a rebuild deletes them |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `skill_state` | power class of the skill estimate | `n_events < 8 -> underpowered` (DB CHECK + `skill.py`) | **earned**: explicit, DB-enforced |
| `skill_score`, `skill_lo`, `skill_hi` | model skill over the null | bootstrap / null replicates on n = 1..7 events | numbers of float noise beside an `underpowered` state; NOT NULL forces them (bhara-N1) |
| `ks_p`, `ljung_box_p` | GOF of the field | time-rescaling tests on n = 1..2 | p-values without power; `gof_state` carries the caveat |
| `n_prospective` / `n_backfill` | how many events were forecast before they occurred | min(global resolutions, class n) (:291) | **mis-attributed by construction**, 0 today |
| `skill_prospective` | skill on prospective resolutions only | NULL constant (:306, :357) | **earned null**: never populated, stated |
| `weights_version = v0_classical` | the field's weights version | pinned from the registry (§7.5), no refit | **earned**: reads the pin, does not invent a fit |
| `maturity` (envelope `calibration_maturity`) | calibration maturity of the chart | `compute_calibration_maturity` from counts; honest zero with no LEL | earned as counts; skill_score passes through un-masked (bhara-N1) |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: every upstream absence is a named state (`kala_field_absent`, `no_lel_events`, `skill_tables_absent`, now raising where the declared dependency makes absence a defect); the chart with no LEL serves the classical priors with maturity zero and says so; `skill_prospective` stays NULL; the null replicates are a deterministic shift grid (no RNG) so hash-replay holds.
- BAD: the float-noise score and the n = 1 p-values are numbers where null is the honest value.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id = ctx.config.get("chart_id")` (:108) is a `uuid.UUID` on the real path and is passed to the `services/mi_bhara` helpers as a SQL parameter; `WeightsPin.to_payload` serialises `fitted_from_chart_id` after an explicit `str(fitted)` (`weights.py:160`); `skill.py:77` hashes `f"{chart_id}|{weights_version}|{event_class}"` (an f-string renders a UUID canonically, so the bootstrap seed is identical for `str` and `UUID`). No `json.dumps`/`canonical_json`/`stable_uuid` of a raw `UUID` (`weights.py:111` dumps strings). **Not exposed.**
- **Outcome-leakage guard:** the circularity guard is the best-evidenced leakage control in L5: `tests/l5/test_mi_bhara_circularity_guard_w2.py` enforces both halves (stages 0-8 never read the LEL; this writer reads it only through `services/mi_bhara/db.py`); falsifier resolution runs before any weight moves (§7.6); weights are INSERT-only versions. It controls LEL-into-field circularity, not prediction-versus-outcome chronology; chronology is carried by the ledger's `as_of` and the falsifier fixed at filing.
- **People-entered data (N-46) / LEL data contract:** reads `life_events` and `brahma_prospective_ledger` (people-entered / filed); writes only derived tables. **`kala_field_weight_versions` is append-only and non-regenerable (INV)**: the code only INSERTs a version and UPDATEs the previous to `superseded` (`db.py:235`, `:283`) on a refit that does not run today. `kala_insights` `lel_derived` rows are deleted and re-derived (derived, regenerable).

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_bhara.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — not keep: this brief states must-fix defects with a rebuild or data migration (float-noise `skill_score` / p-values stored and served on `underpowered` rows, bhara-N1/N2; a chart-wide `n_prospective` attributed to every class, bhara-N3; a registry row that under-declares five written tables). The kernel is careful and honest (deterministic nulls, named degradations, circularity guard, no pretended refit), so the change is a light qualify: keep the asset, null the numbers its own state column says are not established.

Approver under Track A brief section 10: **Steward (G16); envelope and DDL changes to Strategic Suvarṇa (R5)**. Risk class: **medium (served `calibration_maturity` fields; DDL for nullable skill columns)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Underpowered skill is null (R)

- **Answers:** bhara-N1, N2; CF-L5-04
- **Change:** write `skill_score`, `skill_lo`, `skill_hi` and the GOF p-values as NULL when the state is `underpowered` (drop the NOT NULL and relax `kala_field_skill_interval_ck` / `state_ck` accordingly), or mask in the envelope: add `skill_state` to `calibration_maturity` and send `skill_score: null` when underpowered
- **Files / declaration / migration:** `services/mi_bhara/skill.py`, `gof.py`; migration on `kala_field_skill` / `kala_field_gof`; `platform-mcp/src/lib/kala_envelope.ts:540-575`
- **Failing-first test and mutation:** failing-first: an `underpowered` row serves `skill_score: null` and carries the state; mutation: remove the mask -> a 1e-15 number is served
- **Output change:** yes: 7 + 6 stored values and the envelope field -> SS (R5)
- **Blast radius:** all kala_* envelope consumers
- **Rebuild:** needs production rebuild or a data migration of 13 derived rows (REVIEW)
- **Gate it moves:** Null, Earn
- **Fix class:** writer code + DDL + served surface (TS); **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-51

### FD-2 · Per-class prospective counts

- **Answers:** bhara-N3
- **Change:** attribute resolved prospective predictions to their own event class (the `OpenPrediction.event_class` already exists) instead of a chart-wide min
- **Files / declaration / migration:** `mi_bhara.py:285-300`; `living_lel.py`
- **Failing-first test and mutation:** failing-first: a resolution in class A raises only A's `n_prospective`; mutation: restore the min -> every class changes
- **Output change:** none on current data (0)
- **Blast radius:** this asset
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-52

### FD-3 · Regression test and verification for the NULL-window failure

- **Answers:** bhara-N4
- **Change:** add a test with an empty `observation_window` and a NULL-bounded row through `fetch_open_predictions`; verify (by a deploy-level check, not assumed) that the container ran the guarded query; record in the build record
- **Files / declaration / migration:** `tests/l5/test_mi_bhara_living_lel.py`; `services/mi_bhara/db.py:158-196`
- **Failing-first test and mutation:** failing-first: the pre-#1299 query raises on an empty range; main's passes; mutation: remove the `isempty` guard -> FAIL
- **Output change:** none
- **Blast radius:** this asset
- **Rebuild:** none
- **Gate it moves:** Build.history (future)
- **Fix class:** test; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-53

### FD-4 · Register what the writer writes; declare its reads

- **Answers:** bhara-N5, N7; CF-L5-07, CF-L5-13
- **Change:** declare all written tables (clear_tables / count_sql / seed target consistent), add `lel_events` and the ledger as sources, correct the seed target
- **Files / declaration / migration:** registry migration; `asset_registry_seed.ts:3178`; declarations
- **Failing-first test and mutation:** registry census check; mutation: drop a table from the declaration -> the written-tables check fails
- **Output change:** none
- **Blast radius:** registry rows
- **Rebuild:** none
- **Gate it moves:** Build.target, Build.dag
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-54

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-04** — bhara-N1/N2: numbers on underpowered states
- **CF-L5-07** — bhara-N7
- **CF-L5-08** — kala_field_weight_versions is append-only people-adjacent history
- **CF-L5-10** — envelope passes skill_score without state
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history: TypeError x3 then BLOCKED
- **CF-L5-13** — one declared table, five written; seed vs live target

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: `kala_field_skill(event_class, weights_version, field_snapshot_id, n_events, n_prospective, n_backfill, skill_state, null_replicates, bootstrap_resamples, bootstrap_seed)` and, once masked, `skill_*`; exclude `released_at`, `id`. The null grid and bootstrap seed are deterministic (`skill.py:77`); pin the field snapshot id (`kfs_…`) and the weights version.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the deterministic null grid, the named-degradation notes, the circularity guard, falsifier-before-fit ordering, INSERT-only weights versions, `skill_prospective` kept NULL until real prospective resolutions exist.
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): recompute skill and GOF for the 6 event classes with a second implementation from `kala_field` segments and the 7 events; the writer's tests already hold a reference implementation to compare.
- **Opportunities (never blocking):** the maturity envelope is the natural place to say "underpowered" in words; a per-class `n_prospective` makes the first real prospective resolution visible exactly where it lands.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-05** — Status flags: replace the constant / proxy flags (`admissible_clean`, `shaped_predictor`, `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear`, `leakage_status = clean`, `skill_score` on underpowered rows) by detectors or NULL / `not_assessed`; allow the DDL changes this needs (nullable columns, additive basis columns)? *Recommendation:* Yes; unverified admissibility stays calibration-eligible but labelled `unverified_inputs`. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
