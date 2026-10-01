---
asset_id: ka_dasha_kala
layer: L3 Kāla (ka_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 066c58587"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy (Q2, Q11, Q13), PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-17, TI-L3-19, TI-L3-21, TI-L3-22]
ledger_gap_ids: ["ka_dasha_kala-Idem.pattern", "ka_dasha_kala-Build.count_integrity", "ka_dasha_kala-Earn.build_record", "ka_dasha_kala-Cost.baseline", "ka_dasha_kala-Dens.served", "ka_dasha_kala-Build.history", "ka_dasha_kala-Carr.detector", "new: dasha_kala-N1", "new: dasha_kala-N2", "new: dasha_kala-N3", "new: dasha_kala-N4"]
---

# ka_dasha_kala — Dasha-eligibility service (7-system tree walk) and its self-test writer

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/services/ka_dasha_kala/writer.py`.*

Registry: kind service, per-chart, no `target_table`, no `count_sql`. The service (`services/ka_dasha_kala/`: `service.py`, `tree_walk.py`, `eligibility.py`; read-only, "NEVER writes to DB") walks `chart_dashas` lazily across the seven systems (`vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra`) and returns eligible windows with an eligibility band (exact / related / neutral, scores 0.85 / 0.50 / 0.20 in `eligibility.py`) and a cross-system agreement count; it is served by `call_dasha_eligibility` in `call_service_wrappers.ts`. The registered writer (`services/ka_dasha_kala/writer.py:113`; `pipeline/orchestrator/writers/ka_dasha_kala.py` is a side-effect import) is a SELF-TEST: it asserts that `chart_dashas` holds all seven systems for the canonical chart (`_EXPECTED_SYSTEMS`, `:27`), that a Saturn/Rahu query over 2010-2030 returns non-empty windows with `start_date < end_date`, and writes `service_health`, `last_selftest_at`, `selftest_detail` to its own `asset_registry` row; it raises when degraded so the orchestrator cannot promote it (`:156`, the M11 fix). It declares `source_paths` for its whole package (`:124`).

**Canonical chart: `lit`, freshness `unknown`, `service_health` healthy** (registry state read for the rebuild plan, 2026-10-01). Latest run `8e00f2cd` complete/build 2026-09-10; 6 errors and 7 aborts on record, the latest error (2026-09-10) "post-write integrity check failed: integrity_check_sql → False" on a service that writes no table. No output-digest spec yet (I-5 adds one: PR #2826, migration 1213, NOT merged at base): its receipt carries no `output_digest`, which makes `ka_sangam`'s upstream digest NULL (rebuild plan B-2). Not in the 26-asset plan of rebuild-plan v1.0 (the planner accepts its freshness `unknown` as the writer-self-test shape); **rebuild-plan v1.1.1 adds it to the launch set (27 assets) in wave 1 / stage S1, strictly before `ka_sangam` and `ka_kshetra` (its section 1.6)**, after migration 1213 is deployed and the `selftest_detail` grant exists. Nirmāṇa-frozen under t0 (2026-09-07). **None of the five emptied tables is this asset's.**

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2272` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_dasha_kala/writer.py:113`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `none (service)`; count_sql tables: none | census |
| live rows / floor | n/a (service) / 0 (service) | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness `unknown`; output-digest spec ABSENT; service_health `healthy` | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_dashas` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 3 / transitive 29 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_jivana_parva`, `ka_kshetra`, `ka_sangam` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: none; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | service: served by `call_service_wrappers.ts` (a service call, not a read of rows); declarations `served_surface` null | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-07 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) (none declared) anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: services/ka_dasha_kala/writer.py] |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=True |
| Build | Build.count_integrity | PARTIAL | count_sql=no, integrity_check_sql=yes |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=True, asset_kind='service', no target_table; build state='lit' |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8e00f2cd complete/build (2026-09-10) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8e00f2cd complete/build (2026-09-10) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=unmeasured) |
| Dens | Dens.served † | FAIL | 1 module(s): call_service_wrappers.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 6 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-10): post-write integrity check failed: integrity_check_sql → False |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Build.dag †; Build.exercised; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: L3_kala/call_service_wrappers.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 1 declared edge(s); exists: all 1 are active registry assets (every layer); cycle: ka_dasha_kala is on no dependency cycle (registry-wide graph); reads-match: 1 read(s) of other assets' tables, every one covered by a declared edge; static scan of 8 code unit(s), 3 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_dasha_kala-Idem.pattern | Idem | detector | service writes no data row (only its registry health row): "nothing to replace", PARTIAL by the rev-2 reading; an N-22 service rule, not a defect (CF-26 / TI-L3-21) |
| ka_dasha_kala-Build.count_integrity | Build | detector | `count_sql` none by design for a service; `integrity_check_sql` present; declaration question |
| ka_dasha_kala-Dens.served | Dens | Dens rev-1 reading | offline rev-7 reading NO_DETECTOR (a service call, no served select of rows); declared `served_surface: null` |
| ka_dasha_kala-Build.history | Build | history | 6 errors, 7 aborts; latest error 2026-09-10 an integrity-check false on a service (CF-31); no edit changes it |
| ka_dasha_kala-Earn.build_record | Earn | detector | instrument absent; the `service_health` claim does have a real detector (the self-test, which raises) |
| ka_dasha_kala-Cost.baseline | Cost | information | CF-05 |
| ka_dasha_kala-Carr.detector | Carr | detector | D3 re-derivation: a minimal independent walk over `chart_dashas` for a sample window |
| new: dasha_kala-N1 | honesty | real | the self-test is pinned to the canonical chart (`_CANONICAL_CHART_ID`, `:25`; a build of another chart only logs a warning, `:140`), so `service_health` is a statement about one chart's data and the engine, not about the chart being built |
| new: dasha_kala-N2 | honesty | real + SS question | band scores 0.85 / 0.50 / 0.20 are literals (`services/ka_dasha_kala/eligibility.py` `BAND_SCORE`), served as `eligibility_score`; the module calls them "deliberately soft/probabilistic"; no ratification is recorded (CF-27) |
| new: dasha_kala-N3 | Build.dag | real | declared dependents: `ka_jivana_parva` and `ka_kshetra` never reference the service (CF-23 and the layer-instance Appendix A.3); the real code importers are `ka_sangam` (`KaDashaKalaService`), `ka_avadhi` (the `ALL_DASHA_SYSTEMS` constant, `ka_avadhi.py:29`), and `services/ph_nimitta/dasha_consensus.py:106,163` (an L4 reader with no declared edge) |
| new: dasha_kala-N4 | registry | real | the builder role cannot write `asset_registry.selftest_detail` (migration 1070 grants UPDATE on three other columns); `ka_dasha_kala/writer.py:97` writes it unguarded, so under `data_plane_builder` the asset errors (1213 header limit (e)); not in PR #2826 |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: the service composes no stored text (it writes `service_health` and a JSON payload of system lists and counts); proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — the service has a real engine and a real detector behind its status (the self-test raises). The gaps are declarations (N-22 service rules, `prose_fields: []`), a chart-pinned health claim, one ratification question on the band scores, a missing digest spec (I-5, in flight) and a builder grant.

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Output-digest spec and the builder grant (I-5)

- **Answers:** rebuild plan B-2; CF-26; new dasha_kala-N4
- **Change:** land migration 1213 as written (spec over `service_health` and `selftest_detail`, scoped by `where_equals asset_id`, `last_selftest_at` excluded); confirm `selftest_detail` is deterministic across two runs before relying on the digest; the `GRANT UPDATE (selftest_detail)` for `data_plane_builder` is a grants item (BUILDER_GRANT_PLAN v1.1)
- **Files / declaration / migration:** `platform/migrations/1213_nirmana_l3_service_selftest_output_digest_specs.sql` (PR #2826); grant migration not in this lane
- **Failing-first test and mutation:** PR #2826's `tests/l3/test_i4_i5_output_digest_specs.py` (static always; behavioural when `I45_DIGEST_DSN` is set); failing-first here: two consecutive self-test runs digest equal. Mutation: add `last_selftest_at` to the hashed set → the determinism check fails.
- **Output change:** none (a registry spec row)
- **Blast radius:** `ka_sangam` (7 in-plan dependents) and the Phala chain behind it: their receipts turn 'proven' only once both `ka_dasha_kala` and `ka_muhurta_seva` have rebuilt after 1213 (limit (b)); delta-skip starts to apply to the service (it declares `source_paths`, so a code change still re-runs it)
- **Rebuild:** a service run (production dispatch, REVIEW for SS; per-chart scope, no data rows)
- **Gate it moves:** Earn / Build
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent

### FD-2 · Say what the health claim covers

- **Answers:** new dasha_kala-N1; CF-26
- **Change:** either run the self-test against the chart being built (when that chart has all seven systems) in addition to the canonical one, or declare `service_health` as an engine-level claim in the declarations file (`carriage`/`evidence`) so no reader takes it for a per-chart statement
- **Files / declaration / migration:** `services/ka_dasha_kala/writer.py:25-142` or `asset_declarations.json`
- **Failing-first test and mutation:** Failing-first: a build for a chart missing one system reports a per-chart finding; mutation: pin back to the canonical chart → fails.
- **Output change:** none (health payload may gain a per-chart section)
- **Blast radius:** `selftest_detail` content feeds the 1213 digest: a new section changes the digest once
- **Rebuild:** none
- **Gate it moves:** Earn honesty
- **Fix class:** writer code or declaration; **buildable before J1:** tier-independent

### FD-3 · Ratify or compute the band scores

- **Answers:** new dasha_kala-N2; CF-27
- **Change:** record 0.85 / 0.50 / 0.20 as ratified approximations with a decision id and say so in the response (`eligibility_basis`), or return only the band (exact / related / neutral) and leave scoring to the caller (the module says callers may layer their own weights)
- **Files / declaration / migration:** `services/ka_dasha_kala/eligibility.py`; `call_service_wrappers.ts` response shape
- **Failing-first test and mutation:** Failing-first: the served response carries `eligibility_basis` naming the decision; mutation: remove → fails.
- **Output change:** yes if the score is dropped (SS); none if only annotated
- **Blast radius:** `call_dasha_eligibility` consumers (serving) and `ph_nimitta/dasha_consensus.py` (reads the service in code)
- **Rebuild:** none
- **Gate it moves:** Null (constant for an uncomputed term)
- **Fix class:** writer/served code (+ SS ruling); **buildable before J1:** tier-dependent: the Null rule (SS 2026-10-01)

### FD-4 · Service declarations (N-22) and `prose_fields: []`

- **Answers:** census Idem PARTIAL, count_integrity PARTIAL, Null/Narr; CF-06, CF-26
- **Change:** declare the asset a service in the registry/declarations sense the rev-2 `Build.target` already reads; declare `prose_fields: []` with `evidence.prose_fields` pointing at `writer.py` (it writes health and counts only); propose Idem N/A by measured cause (the service writes no own-table rows)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (already `kind: service`); `NA_RULE_DECISIONS` entries only via SS approval
- **Failing-first test and mutation:** declarations validation test; mutation: declare `[]` for a writer that composes text → Narr.lint flags it.
- **Output change:** none
- **Blast radius:** none (census inputs)
- **Rebuild:** none
- **Gate it moves:** Idem, Build, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-5 · Carr: a re-derivation check on the walk

- **Answers:** census Carr NO_DETECTOR; CF-07
- **Change:** D3: for a sampled (target lords, window) pair, re-derive the eligible intervals by a minimal independent query over `chart_dashas` and compare to the service result
- **Files / declaration / migration:** detector (Track E), a test beside `tests/l3/test_ka_dasha_kala.py`
- **Failing-first test and mutation:** Failing-first: a seeded wrong interval is reported; zero on the real data; mutation: perturb a boundary → count ≥ 1.
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Landed or in flight (not designs of this lane)

- **I-5 (digest spec) — PR #2826 / migration 1213 NOT merged at base** (FD-1). 
- No I-item changes the service's code.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline NO_DETECTOR; declare N/A by cause `no-served-surface`
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 re-derivation of the walk
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 6 errors / 7 aborts
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* two declared dependents never reference the service; one undeclared L4 code reader
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* FD-1
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* FD-3 band scores
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* latest error is an integrity-check false on a service

## 5 · Semantic fingerprint contract (for E5.5)

No table. The only stored output is the registry health row: `service_health` and `selftest_detail` (deterministic given the canonical chart's `chart_dashas`); `last_selftest_at` is volatile and excluded. A rebuild must leave `service_health = healthy` and an identical `selftest_detail` (systems found, windows returned, high-agreement count).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the seven-system lazy tree walk with pruning and cross-system agreement, the raise-on-degraded self-test.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation): an independent minimal walk over `chart_dashas` for a sampled query; the existing self-test already asserts structure (7 systems, non-empty, `start < end`), not equality.
- **Opportunities (never blocking):** level-4 sookshma floor and in-memory prana are documented in the service; a per-chart health surface; none blocking.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-01** — CF-27: are the band scores 0.85 / 0.50 / 0.20 a ratified approximation?
- **Q-L3-10** — CF-26: extend digest specs to the same-class services?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-17, TI-L3-19, TI-L3-21, TI-L3-22.
