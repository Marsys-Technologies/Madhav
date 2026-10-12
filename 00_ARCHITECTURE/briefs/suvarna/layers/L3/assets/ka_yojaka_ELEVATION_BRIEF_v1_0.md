---
asset_id: ka_yojaka
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
disposition_proposal_approver: "Steward (G16); CF-27 items go to SS (R5). Ownership: a claimed Saṅgam prerequisite (Track A section 6): if the Saṅgam brief claims it, it moves from this set to A.L3f evaluation"
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-16, TI-L3-17, TI-L3-19, TI-L3-24]
ledger_gap_ids: ["ka_yojaka-Earn.build_record", "ka_yojaka-Cost.baseline", "ka_yojaka-Dens.served", "ka_yojaka-Build.history", "ka_yojaka-Build.dep_liveness", "ka_yojaka-Carr.detector", "new: yojaka-N1", "new: yojaka-N2", "new: yojaka-N3", "new: yojaka-N4"]
---

# ka_yojaka — Activation-predicate bridge: one dasha/transit/strength predicate per MSR signal

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py`.*

`ka_yojaka.py` + `services/ka_yojaka/` (`classifier.py`, `binder.py`): reads every `bodha_msr_signals` row of the chart (`:85`), classifies each signal (`classify_signal`) and binds the ratified predicate template (`build_predicate`), then enriches the predicate: the activating daśā lords resolved from L1 (YOGA forming grahas from `ga_yoga_firings`, Kāla-sarpa through the nodal axis, fired-dosha grahas; a distribution yoga formed by six or more grahas is left undated with `always_on_reason`, `DISTRIBUTION_YOGA_MIN_GRAHAS = 6`, `:58`; otherwise lords from the configuration, house/varga bhava lord, or tokens of the constituent fact's subject, each with its `constituent_lords_source`), the real per-signal `dignity_score` and a chart-normalised `shadbala_norm` as the hook's `non_affliction` (`:99`), a CGM centrality weight and CDLM domain strengths, and the signed multi-domain structure (DP-SD-019). One row per signal into `kala_activation_predicates` (50,678 canonical rows: one per MSR signal row the writer read; the L2 index counts 50,678 MSR chart rows), `ON CONFLICT DO NOTHING` after a chart-wide delete that runs only once the whole candidate exists (`:441`). Read by `ka_kalasutra`, `ka_vighnakara`, `ka_jivana_parva`, `ka_sangam` and `ph_nimitta` (code), served by `query_temporal_activation.ts:388`.

**Canonical chart: 50,678 rows present, throughput `stale`, freshness `stale`.** The table has no signal key, so the cascade did not delete it, but its `signal_id` references are dead after the MSR replacement (I-6; F-3 measured 79 dangling references for the canonical chart and 49,730 of 49,875 on `cb73cd3d`, the `unconstrained` tier of its detector). Latest run `a085a8b7` complete/build 2026-09-10; 16 errors and 8 aborts, the latest error (2026-09-10) "post-write integrity check failed"; the check was scoped to the canonical chart by migrations 1019 and 1022 and an output-digest spec added by 1024 (all merged 2026-09-10), and the latest run is a complete one; dependencies 6 of 7 lit (`bo_pratijna` stale). Wave 2 of the rebuild plan (v1.0 numbering, v1.1.1 keeps the order), 'SS wave' (with `bo_pratijna`). Nirmāṇa-frozen under t2 (2026-09-10), and that manifest is already stale after migration 1210 (`ka_yojaka → ga_yoga` added). Prerequisite named by the focus document for the Saṅgam rebuild; flagged in the layer instance Appendix A as a claimed family prerequisite, not adjudicated here.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2382` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py:61`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_activation_predicates`; count_sql tables: kala_activation_predicates | census |
| live rows / floor | 50,678 / 50,104 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness `stale`; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `bo_laksana`, `bg_transit_rules`, `ga_dashas`, `bo_bimba`, `bo_sangati`, `bo_pratijna`, `bg_ghatana`, `ga_yoga (migration 1210)` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 4 / transitive 26 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_jivana_parva`, `ka_kalasutra`, `ka_sangam`, `ka_vighnakara` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/lib/ahead_autofile.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/now.ts`, `src/lib/retrieval/registry/knowledge/editorial.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_temporal_activation.ts`, `registry/layers/register_d8_assess_domain.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `pipeline/orchestrator/writers/ka_jivana_parva.py`, `pipeline/orchestrator/writers/ka_kalasutra.py`, `pipeline/orchestrator/writers/ka_sangam.py`, `pipeline/orchestrator/writers/ka_vighnakara.py`, `pipeline/orchestrator/writers/ph_nimitta.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:388` reads `kala_activation_predicates`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t2, 2026-09-10 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a085a8b7 complete/build (2026-09-10) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a085a8b7 complete/build (2026-09-10) |
| Dens | Dens.served † | FAIL | 1 module(s): query_temporal_activation.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 16 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-10): post-write integrity check failed: integrity_check_sql → False |
| Build | Build.dep_liveness | PARTIAL | 6/7 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_pratijna (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Build.exercised.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 4 module(s) reach it by code: L3_kala/query_temporal_activation.ts, register_d8_assess_domain.ts, platform-mcp/src/tools/kala_views/ahead.ts, platform-mcp/src/tools/kala_views/now.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **FAIL** — 7 declared edge(s); exists: all 7 are active registry assets (every layer); cycle: ka_yojaka is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ka_yojaka -> ga_yoga (reads ga_yoga_firings at ka_yojaka.py:607; the producer is reachable transitively via bo_bimba, bo_laksana, bo_pratijna, bo_sangati, so ordering holds but the edge is undeclared)

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_yojaka-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (4 modules reach it, 1 served select, no contract) |
| ka_yojaka-Build.history | Build | history | 16 errors, 8 aborts; latest error 2026-09-10 integrity-check false (scoped afterwards by 1019/1022); CF-10 |
| ka_yojaka-Build.dep_liveness | Build | stale | 6 of 7 lit; `bo_pratijna` stale; chain order clears it |
| ka_yojaka-Earn.build_record | Earn | detector | CF-05 |
| ka_yojaka-Cost.baseline | Cost | information | CF-05 |
| ka_yojaka-Carr.detector | Carr | detector | D2: every resolved lord traces to a cited L1 source (`constituent_lords_source`); D3: re-resolve a sample from `ga_yoga_firings` (CF-07) |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column; the carriage is `derivation_ledger_jsonb` (CF-08) |
| new: yojaka-N1 | Null / honesty | real + SS question | `non_affliction` stored in the hook is `shadbala_norm / max(shadbala_norm over the chart's signals)` (`:99`): a strength fraction under an affliction name, relative to the chart's strongest signal; it is absent when `shadbala_norm` is NULL, and then the resolver defaults it to 1.0 (favourable) and `dignity_score` to 0.5; `cgm_centrality_weight` defaults to 0.5 (`:315`); the L2 satellite constants (`dignity_score = 0.50`, `shadbala_norm = 1.0`) arrive here as inputs (CF-27) |
| new: yojaka-N2 | Carr | information | `DISTRIBUTION_YOGA_MIN_GRAHAS = 6` is justified in a comment as separating point yogas from distribution yogas "on the observed data" (`:57`): a threshold fitted to observation, declared as a documented approximation (CF-27) |
| new: yojaka-N3 | Idem / honesty | real | the predicate set is a function of the CURRENT MSR identity set; after an MSR replacement every stored predicate whose signal changed identity dangles until this asset is rebuilt (F-3 measured 79 for the canonical chart): the asset is the pivot between L2 and the whole Kāla chain, and the detector that finds the dangling ones is advisory-tier only (CF-24) |
| new: yojaka-N4 | honesty | information | soft SAVEPOINT-guarded reads for the pratijna linkage and several L1 prefetches degrade to empty with a debug log (CF-29); each carries a `*_source` provenance token when it succeeds, so a missing token is the only trace of a skipped read |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: only snake_case tokens and rule expressions are stored (`:407`, `services/ka_yojaka/binder.py`); proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — the writer follows the replace-after-candidate pattern, records the source of every resolved lord, and discloses undatable predicates instead of dating them. Open items are the constants/defaults ruling (CF-27) and the F-3 linkage (CF-24); it is the asset every Kāla table downstream of MSR depends on.

Approver under Track A brief §10: **Steward (G16); CF-27 items go to SS (R5). Ownership: a claimed Saṅgam prerequisite (Track A section 6): if the Saṅgam brief claims it, it moves from this set to A.L3f evaluation**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Ratify or null the hook defaults (`non_affliction`, `cgm_centrality_weight`)

- **SS ruling (2026-10-01):** accepted (Q-L3-01): option 2 for these defaults. TI-L3-17.
- **Answers:** new yojaka-N1; CF-27
- **Change:** per the CF-27 ruling: store NULL (not an absent key that the resolver defaults to 1.0) when `shadbala_norm` is NULL; rename or document `non_affliction` as a normalised strength fraction; record 0.5 for the missing centrality as a ratified approximation or NULL
- **Files / declaration / migration:** `ka_yojaka.py:99-101`, `:315`; `services/ka_temporal/date_resolver.py:674`
- **Failing-first test and mutation:** CF-27 test shape: a signal without `shadbala_norm` stores NULL and the proximity score is NULL or the documented function; mutation: restore the default → fails.
- **Output change:** yes for NULL/rename (the hook JSON of affected rows) → SS (R5)
- **Blast radius:** `kala_activation_predicates` hook values (50,678 rows) → `ka_kalasutra` proximity scores → served windows; `ph_nimitta` reads `multi_system_confirmation_count` from the same table (not the hook)
- **Rebuild:** needs production rebuild of `ka_yojaka` then `ka_kalasutra` (REVIEW for SS); the rebuild is already in wave 2
- **Gate it moves:** Null
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent: the Null rule

### FD-2 · Extend the dangling-reference detector to the predicate table

- **Answers:** new yojaka-N3; CF-24
- **Change:** promote `kala_activation_predicates.signal_id` from the advisory `unconstrained` tier to a checked post-wave site (F-3's detector already scans it advisory-only) and add it to the rebuild-order guard's derived dependents so an MSR wave cannot end with dangling predicates unnoticed
- **Files / declaration / migration:** `platform/scripts/governance/msr_dangling_signal_refs.py` (F-3 branch; Track I/E), the order guard map
- **Failing-first test and mutation:** F-3 proof shape: a changed signal id leaves N dangling predicates and the detector reports exactly N; mutation: drop the site → fails.
- **Output change:** none
- **Blast radius:** governance tooling only
- **Rebuild:** none
- **Gate it moves:** Earn honesty
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent

### FD-3 · Declare `prose_fields: []`

- **Answers:** census Null/Narr; CF-06
- **Change:** declare `[]` with `evidence.prose_fields` → `ka_yojaka.py:407` and `services/ka_yojaka/binder.py` (rule expressions are template tokens, not narration)
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation: declare `[]` on `ka_kala_darshana` → Narr.lint flags it
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-4 · Carr: lord-resolution re-derivation

- **Answers:** census Carr; CF-07
- **Change:** D3: for a sample of YOGA/DOSHA signals, re-resolve the forming grahas from `ga_yoga_firings` and the constituent facts by an independent query and compare to `constituent_lords`; D2: every non-empty lord list has a `constituent_lords_source` naming a real L1 table
- **Files / declaration / migration:** detector (Track E); `tests/l3/test_ka_yojaka_cr37_activation.py` (the model)
- **Failing-first test and mutation:** Failing-first: a seeded wrong lord is reported; zero on the real data; mutation: perturb one lord → count ≥ 1.
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Landed or in flight (not designs of this lane)

- **Migration 1210 (merged, #2810) added `ka_yojaka → ga_yoga`** (the `ga_yoga_firings` soft read at `ka_yojaka.py:17`); the held `ph_nimitta → ka_yojaka` edge (migration 1211) waits for this asset to be lit and fresh.
- Migrations 1019/1022 scope its integrity check to the canonical chart; 1024 adds its digest spec.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2/D3
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* carriage in `derivation_ledger_jsonb`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 16 / 8
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* unconstrained dangling set (79 canonical)
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* FD-1; threshold 6
- **CF-29** — Honest absence versus unavailable: swallowed detector failures, proxy fallbacks and soft reads that degrade to empty. *This asset:* soft reads
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* already scoped (1019/1022)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, signal_id, ayanamsha_id)` (DB UNIQUE index `idx_kap_chart_signal_ayan`; migration 670 header). Volatile columns excluded: `id`, `bound_at`. Content is a function of the MSR set (identity and columns), the L1 firing sets and the CGM/CDLM prefetches; the digest spec 1024 already defines the hashed projection (proven 2026-09-10, receipt `3fd3b490ecc1`). Rebuild expectation: 50,678 rows if the MSR set is unchanged; digest equal if `bo_pratijna` is unchanged (rebuild plan 4.2).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** lord resolution traced to L1 rows with a recorded source per predicate, the `always_on_reason` disclosure, replace-after-candidate, the signed multi-domain structure preserved losslessly.
- **Carriage check chosen (T4 §4.1; one only):** D2: each resolved lord list names a real L1 source; D3: re-resolve a sample of YOGA/DOSHA predicates from `ga_yoga_firings` and the constituent facts independently.
- **Opportunities (never blocking):** expose the undated share (`always_on_reason` counts) in the served view; none blocking.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **Q-L3-01 — accepted** (FD-1: the `cgm_centrality_weight` 0.5 and `non_affliction` defaults follow option 2). Track I: TI-L3-17.
- **Q-L3-15 — accepted.** `ka_yojaka` stays in this (non-family) set; its Saṅgam prerequisite status is a build-order fact, not an ownership transfer.

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-01** — CF-27: ratify, null or compute the hook defaults?
- **Q-L3-15** — ownership: does the Saṅgam brief claim `ka_yojaka` (moving it to A.L3f evaluation)?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-16, TI-L3-17, TI-L3-19, TI-L3-24.
