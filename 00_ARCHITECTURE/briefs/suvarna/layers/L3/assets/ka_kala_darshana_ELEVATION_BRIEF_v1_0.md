---
asset_id: ka_kala_darshana
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
disposition_proposal_approver: "Steward (G16); the narration fix (FD-3) goes to SS as a text-only output change (R5)"
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-01, TI-L3-02, TI-L3-03, TI-L3-07, TI-L3-10, TI-L3-11, TI-L3-17, TI-L3-19, TI-L3-20]
ledger_gap_ids: ["ka_kala_darshana-Build.completion", "ka_kala_darshana-Earn.build_record", "ka_kala_darshana-Cost.baseline", "ka_kala_darshana-Count.floor", "ka_kala_darshana-Dens.served", "ka_kala_darshana-Build.history", "ka_kala_darshana-Build.dep_liveness", "ka_kala_darshana-Carr.detector", "new: darshana-N1", "new: darshana-N2", "new: darshana-N3", "new: darshana-N4", "new: darshana-N5"]
---

# ka_kala_darshana — Display-ready temporal view: effective score, net label and narrative per convergence window

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py`.*

`ka_kala_darshana.py`: for up to 750 `kala_convergence` windows of the chart (`:31`) it joins the chart's `kala_obstruction` rows by `convergence_id` (`:42`) and stores per window `effective_score = convergence_score × (1 − max override_score)` (`:146`), a `net_label` (`obstructed_severe / obstructed / auspicious_strong / auspicious_moderate / auspicious_speculative / neutral`, cuts 0.70 / 0.45 / 0.20 and a moderate-obstruction cut at 0.4, `:159`), an `obstruction_summary` copy and a three-field `narrative` (`headline`, `context`, `caution`, `:181`). The M9 note records a real fix: a computed convergence score of 0 is no longer rewritten to 0.5 (`:78`). Light writer; read by `ka_bhavishya_lekha` and `ka_jivana_parva`, and served by `query_temporal_view.ts:87` and the `kala_views/now.ts` view.

**Canonical chart: `stale`, 0 rows (cascade-shaped).** `kala_darshana` has 0 canonical rows while `asset_throughput` reads `stale`, `rows_written` 750 (08-13 01:15); Abhinandan holds 750, the third chart 0 (I-6). 0 of 3 declared dependencies lit (`ka_sangam`, `ka_vighnakara`, `ka_kalasutra` stale — and all three tables are empty for the chart, I-6). Wave 5 of the rebuild plan (v1.0 numbering, v1.1.1 keeps the order), after `ka_vighnakara` (it reads `kala_obstruction`); it feeds `ka_bhavishya_lekha` and `ka_jivana_parva`. Not Nirmāṇa-frozen; output-digest spec present. Cause of the empty table: CF-24.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2401` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py:9`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_darshana`; count_sql tables: kala_darshana | census |
| live rows / floor | 0 / 750 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_sangam`, `ka_vighnakara`, `ka_kalasutra` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 3 / transitive 21 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_tulana` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/now.ts`, `platform-mcp/src/tools/retrieval/kala_temporal.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/index.ts`, `registry/layers/L3_kala/query_temporal_view.ts`, `registry/layers/register_d5_fanout.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `bodha_writers/_idempotency.py`, `pipeline/orchestrator/kala_derivation_completeness_guard.py`, `pipeline/orchestrator/writers/ka_bhavishya_lekha.py`, `pipeline/orchestrator/writers/ka_jivana_parva.py`, `services/ka_tulana/__init__.py`, `services/ka_tulana/ranker.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts:87` reads `kala_darshana`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=750); build record rows_written=750 |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | FAIL | live=0, floor=750, delta=-750 |
| Dens | Dens.served † | FAIL | 1 module(s): query_temporal_view.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 28 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_kalasutra, ka_sangam, ka_vighnakara did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 0/3 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_sangam (stale, chart 482012f1)', 'ka_vighnakara (stale, chart 482012f1)', 'ka_kalasutra (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ["narrative.$.headline", "narrative.$.context", "narrative.$.caution"] (the cells would be measured by a fresh census; the Null check needs the database, so none could be run offline) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Complete.depth; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 3 module(s) reach it by code: L3_kala/query_temporal_view.ts, platform-mcp/src/tools/kala_views/now.ts, platform-mcp/src/tools/retrieval/kala_temporal.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_kala_darshana is on no dependency cycle (registry-wide graph); reads-match: 2 read(s) of other assets' tables, every one covered by a declared edge; static scan of 1 code unit(s), 3 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_kala_darshana-Build.completion | Build | real (cascade-shaped) | empty: live 0, floor 750, `rows_written` 750; cause I-6; clears with the chain (CF-24) |
| ka_kala_darshana-Count.floor | Count | information | live 0 vs floor 750; floor equals the writer cap (`LIMIT 750`) |
| ka_kala_darshana-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (3 modules, 2 served selects, no `density_contract`) |
| ka_kala_darshana-Build.history | Build | history | 28 errors, 12 aborts; latest error cascade `BLOCKED` 2026-08-12 (CF-10) |
| ka_kala_darshana-Build.dep_liveness | Build | stale | 0 of 3 declared dependencies lit; one of the three edges is never read (CF-23) |
| ka_kala_darshana-Earn.build_record | Earn | detector | CF-05 |
| ka_kala_darshana-Cost.baseline | Cost | information | CF-05 |
| ka_kala_darshana-Carr.detector | Carr | detector | D2: registry integrity conjuncts (b)-(e) restate-checks (CF-07) |
| census: Ldgr | Ldgr | information | PASS on `source_citation` populated 750/750 rows — table-wide (Abhinandan's rows) and a build tag `ka_kala_darshana:v1.0:conv=<id>`; CF-08 |
| new: darshana-N1 | Idem / Build | real | DELETE (`:19`) precedes the "No convergence windows" return (`:36`): CF-21 |
| new: darshana-N2 | Idem | real | `ORDER BY kc.convergence_score DESC NULLS LAST LIMIT 750` has no tiebreak (`:30`), with 793 zero-score rows on record (CF-22) |
| new: darshana-N3 | Narr | real | `context` is built as `(f"..." f"..." f"orb strength: ..." if orb_strength else f"confidence: ...")` (`:219-223`): Python applies the conditional to the whole concatenation, so when `orb_strength` is falsy — NULL or a computed 0.0 — the rarity and the mode label are dropped and only the confidence text remains (the falsy-coalescing class of M9, here in narration) |
| new: darshana-N4 | honesty | information | a NULL `convergence_score` is substituted by 0.5 with a logged warning that the path never fired (793 zeros, 0 NULLs at the M9 fix, `:92`): honest as logged, a constant standing for a missing value (CF-27) |
| new: darshana-N5 | Build.dag | real | declares `ka_kalasutra` and never reads `kala_activation` (CF-23) |
| census: Null/Narr | Null, Narr | detector | declared `narrative.$.headline\|context\|caution`; no fidelity test measured; CF-25 |

## 3 · Disposition

**keep (P)** — a faithful restatement layer (effective score is a documented function of cited columns; the M9 fix corrected a real invention). Defects are order-of-statements and one expression-precedence bug, plus an unread edge; none argues for a different disposition.

Approver under Track A brief §10: **Steward (G16); the narration fix (FD-3) goes to SS as a text-only output change (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Replace-after-candidate

- **Answers:** new darshana-N1; CF-21
- **Change:** read the convergence windows first, return the precondition note without touching the table when there are none and rows exist (or refuse), and delete only once `rows` is non-empty (`:132`)
- **Files / declaration / migration:** `ka_kala_darshana.py:19-132`
- **Failing-first test and mutation:** CF-21 test shape on `tests/l3/test_ka_kala_darshana.py`: seed a partition, run with empty `kala_convergence`, rows survive; mutation: restore order → fails.
- **Output change:** none on a healthy rebuild
- **Blast radius:** readers `ka_bhavishya_lekha`, `ka_jivana_parva`, `query_temporal_view.ts`, `now.ts`, `kala_temporal.ts` stop losing rows on an empty upstream
- **Rebuild:** none (exercised by the next rebuild)
- **Gate it moves:** Idem / Build
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Total ORDER BY on the 750 intake

- **Answers:** new darshana-N2; CF-22
- **Change:** append `peak_date, convergence_id` to the ORDER BY
- **Files / declaration / migration:** `ka_kala_darshana.py:30-31`
- **Failing-first test and mutation:** CF-22 test shape
- **Output change:** the stored subset may change once on tied data
- **Blast radius:** `kala_darshana` readers as above; `ka_bhavishya_lekha` reads the top 100 by effective score of the future windows
- **Rebuild:** rides the planned rebuild
- **Gate it moves:** Idem
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Fix the `context` expression and the falsy orb strength

- **SS ruling (2026-10-01) (R):** accepted (Q-L3-07); latent on present data (0 of 750 stored rows). TI-L3-03.
- **Answers:** new darshana-N3; CF-25
- **Change:** parenthesise the conditional so only the orb-strength clause is conditional, and test `orb_strength is not None` (a computed 0.0 prints as 0.00); keep rarity and mode in every context string
- **Files / declaration / migration:** `ka_kala_darshana.py:219-223`
- **Failing-first test and mutation:** Failing-first: a window with `orb_strength` None and one with 0.0 both keep the mode label and cycle length; mutation: restore the expression → fails.
- **Output change:** yes — `narrative.context` text of affected rows (a text-only correction) → SS (R5)
- **Blast radius:** served as is by `query_temporal_view.ts:87` and `now.ts`; no python reader of `narrative` (the bhavishya writer assigns `row['narrative']` and builds its own `proj_narrative`, `ka_bhavishya_lekha.py:298`)
- **Rebuild:** rides the planned rebuild
- **Gate it moves:** Narr
- **Fix class:** writer code (+ SS text approval); **buildable before J1:** tier-independent

### FD-4 · Narr golden-value tests

- **Answers:** census Narr; CF-25
- **Change:** fixtures for each label branch and each caution branch; assert the headline, context and caution equal what the cited row carries (mode label from the four-value enum, rarity, confidence)
- **Files / declaration / migration:** `tests/l3/test_ka_kala_darshana.py`, `test_m9_darshana_computed_zero.py` (extend)
- **Failing-first test and mutation:** Failing-first: reproduce the N3 defect; mutation: change one composed value → fails.
- **Output change:** none
- **Blast radius:** none (tests)
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (tests); **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset; it is downstream of the I-2 consumer (`ka_vighnakara`) and of F-3 (CF-24).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* build tag; table-wide
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 28/12
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* FD-1
- **CF-22** — Capped intakes without a total ORDER BY (LIMIT 750 / LIMIT 500). *This asset:* FD-2
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* unread `ka_kalasutra` edge
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* emptied table; wave 5
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* FD-3, FD-4
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* label cuts; NULL → 0.5 logged
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `convergence_id` (one darshana row per convergence window: migration 973 records a live UNIQUE index `idx_kala_darshana_convergence` on `convergence_id` WHERE NOT NULL and sets the registry `natural_key_partition` to `(chart_id, convergence_id)`; the census's declared key reads the surrogate `id`, layer instance 5.2). Volatile columns excluded: `id`, `computed_at`. `convergence_id` is a BIGSERIAL of `kala_convergence` regenerated by every `ka_sangam` rebuild (migration 1212 header), so the cross-rebuild comparison key is `(signal_id, peak_date)`. Rebuild expectation: up to 750 rows, a function of the convergence set and the obstruction set.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the effective-score definition (convergence × (1 − max override)), the four-value mode vocabulary, the honest NULL/zero handling.
- **Carriage check chosen (T4 §4.1; one only):** D2 (witness carriage): the row restates its convergence and obstruction rows; the registry integrity conjuncts (b)-(e) already assert the restatements and are registered as the detector.
- **Opportunities (never blocking):** serve the obstruction `detail.reason` strings next to the label; dasha-anchored obstruction rows (NULL `convergence_id`) are not joined by design (they exist for signals without a convergence window): a question for the serving layer, not a defect.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **Q-L3-07 (R) — accepted.** FD-3 text-only correction of `narrative.context` (parenthesise the conditional; test `orb_strength is not None`); latent: 0 of 750 stored rows are affected on present data. Track I: TI-L3-03.
- **Q-L3-08 — accepted.** Remove the unread `ka_kalasutra` edge. Track I: TI-L3-07.

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-07** — FD-3: approve the text-only correction of `narrative.context`?

**Track I items arising (see INDEX section 10):** TI-L3-01, TI-L3-02, TI-L3-03, TI-L3-07, TI-L3-10, TI-L3-11, TI-L3-17, TI-L3-19, TI-L3-20.
