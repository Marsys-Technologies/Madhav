---
asset_id: ka_moorti_nirnaya
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
disposition_proposal_approver: "Steward (G16); any output change goes to SS (R5) and, because `ka_gochara` reads this table, SS notifies Pravāha before a wave touches it (the L0 route for R9 assets, by analogy)"
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-13, TI-L3-20, TI-L3-35, TI-L3-37]
ledger_gap_ids: ["ka_moorti_nirnaya-Build.completion", "ka_moorti_nirnaya-Earn.build_record", "ka_moorti_nirnaya-Cost.baseline", "ka_moorti_nirnaya-Dens.served", "ka_moorti_nirnaya-Build.history", "ka_moorti_nirnaya-Carr.detector", "new: moorti-N4", "new: moorti-N1", "new: moorti-N2", "new: moorti-N3"]
---

# ka_moorti_nirnaya — Moorti-nirṇaya: classical gold/silver/copper/iron quality of each transit sign-stay

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/services/ka_moorti_nirnaya/writer.py`.*

`services/ka_moorti_nirnaya/writer.py` (+ `logic.py`): for the eight grahas other than the Moon (`MOORTI_GRAHAS`, a disclosed scope choice) it reads daily tropical positions from `ephemeris_daily` over a horizon of 60 days back to 400 days forward (the default window, `:73-74`, from `today = date.today()` at `:293`; the caller can already pin the window through `ctx.config['horizon_start']` / `['horizon_end']`, `:296-301`), corrects to sidereal with one ayanamsha offset, detects contiguous sign runs, and for each run grades the stay by the Moon's nakshatra at the ingress, counted from the native's janma nakshatra (the L1 fact, `janma_nakshatra_fact_id`), There are two grading regimes: with `KERNEL_INSTANT_GRADING = True` (`:82`) each non-truncated run is graded at the true kernel sign-ingress instant and stamped `precision_regime = 'instant_grain'`; if the instant does not solve, that run falls back to the ingress date's daily Moon and is stamped `date_grain`. The quality is then looked up verbatim in L0 `bg_transit_moorti` (27 rows; Phaladeepika Ch.26, BPHS Ch.28; `:99`). Honesty discipline is built in: a run whose start touches the horizon edge cannot be graded (`moorti_computed = false`, the moorti fields NULL, `source_qualification = 'unsourced'`), a computed row is stamped `algorithmic_approximation` and `corpus_verifiable = false` because the mūrti rule form is not in the served corpus (`logic.py:70-107`), and every row carries an `upstream_fingerprint`. Light writer; served by `query_moorti_nirnaya.ts:107` and the `now` view. **Read by `ka_gochara` (declared) and by Pravāha-owned code**: `services/gochara_v3/mechanisms/w22_moorti_nirnaya.py`, `gochara_v3/context.py` (`_fetch_moorti_rows`, `:581`, SQL at `:605`), and `services/ka_vedha_gochara/freshness.py:83-102` (a freshness check on this table's `upstream_fingerprint`).

**Canonical chart: `lit`, fresh, 74 rows.** Registry state: throughput `lit`, freshness `fresh`, spec present; latest run `8d74930c` complete/skip_no_delta 2026-09-07; 3 errors and 3 aborts (latest error 2026-08-08, the `KeyError: 1` fixed in the writer). Live 74 against floor 72 (+2) and a build record of 71 rows: consistent with a window that moves with the build date (CF-28; an inference from the code). The rebuild plan (section 1.4) names two assets at risk of a DEP-ASSERT failure (`bo_sangati` and `ka_vedha_gochara`) and says `ka_moorti_nirnaya` and `ka_gochara_resonance` likewise follow `bg_transit_rules`: this asset goes `stale` if `bg_transit_rules` completes with `output_changed` true, and `ka_moorti_nirnaya` is a dependency of `ka_gochara` (family, Pravāha). Nirmāṇa-frozen under t0 (2026-09-07).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2585` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_moorti_nirnaya/writer.py:261`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_moorti_nirnaya`; count_sql tables: kala_moorti_nirnaya | census |
| live rows / floor | 74 / 72 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness `fresh`; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_positions`, `bg_ephemeris`, `bg_transit_rules` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 1 / transitive 27 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_gochara` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/now.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_moorti_nirnaya.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `scripts/kala_gochara_cutover/step04_apply_verify.py`, `services/gochara_v3/context.py`, `services/gochara_v3/mechanisms/w22_moorti_nirnaya.py`, `services/ka_vedha_gochara/freshness.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_moorti_nirnaya.ts:107` reads `kala_moorti_nirnaya`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-07 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | build record rows_written=71 disagrees with live=74 (count_sql over the target table; chart 482012f1) |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Dens | Dens.served † | FAIL | 1 module(s): query_moorti_nirnaya.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-08): KeyError: 1 Traceback (most recent call last):   File "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 562, in _run_data_writer     rows_inserte |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Count.floor; Complete.depth; Vocab.identity; Build.exercised; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_moorti_nirnaya.ts, platform-mcp/src/tools/kala_views/now.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L3_kala/query_moorti_nirnaya.ts

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_moorti_nirnaya is on no dependency cycle (registry-wide graph); reads-match: 2 read(s) of other assets' tables, every one covered by a declared edge; static scan of 26 code unit(s), 4 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_moorti_nirnaya-Build.completion | Build | real (rolling window) | build record `rows_written = 71` disagrees with live 74 (chart 482012f1): consistent with a skip_no_delta run after the window moved (an inference from the code; the cell does not give the cause); CF-28 |
| ka_moorti_nirnaya-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL: "a tier column is selected without a contract" (`quality_tier`): the case where a contract plus tier gives PASS (CF-04) |
| new: moorti-N4 | Vocab | information | the state vocabularies are local tuples in `logic.py` (`SOURCE_QUALIFICATIONS`, `PRECISION_REGIMES`, `:90-91`) mirroring a migration-1082 CHECK, while the writer stamps `precision_regime` with the string literals `date_grain` / `instant_grain` (`:380`) rather than importing them; low severity (the CHECK catches a wrong value at insert) |
| ka_moorti_nirnaya-Build.history | Build | history | 3 errors, 3 aborts; latest 2026-08-08 `KeyError: 1` (fixed); CF-10 |
| ka_moorti_nirnaya-Earn.build_record | Earn | detector | CF-05 |
| ka_moorti_nirnaya-Cost.baseline | Cost | information | CF-05 |
| ka_moorti_nirnaya-Carr.detector | Carr | detector | D3: re-count nakshatra offsets for a sample from the janma nakshatra and the ingress Moon position (CF-07) |
| census: Ldgr (no reading) | Ldgr | detector | `moorti_classical_citation` not in `CITATION_COLUMNS` (CF-08); the row also carries `source_qualification`/`corpus_verifiable`, the honest state the gate has no field for |
| new: moorti-N1 | Idem | real | default horizon from the build date (CF-28; a config pin exists but the build does not pass one); edge rows (`start_truncated`) change with the as-of by design, and `rows_written` differs from live after a window move |
| new: moorti-N2 | Build.dag | information | downstream coupling is wider than the registry shows: `ka_gochara` is the declared dependent (census radius 1/27), and Pravāha-owned python reads the table and its `upstream_fingerprint` (above); a change here is a change to the Gochara family's inputs |
| new: moorti-N3 | honesty | information | computed moorti is 'algorithmic_approximation', `corpus_verifiable = false` on every row by doctrine N7: the asset cannot reach a verse-cited state until the rule form is in the corpus (an L0 question: `bg_texts`/`bg_rules`) |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: `phala_brief` is copied verbatim from L0 `bg_transit_moorti` (`:421`), not composed; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — the best-qualified L3 writer on provenance (a stamped approximation state, an `unsourced` state for ungradable runs, an upstream fingerprint). Open items are declarations, the rolling window and the family coupling.

Approver under Track A brief §10: **Steward (G16); any output change goes to SS (R5) and, because `ka_gochara` reads this table, SS notifies Pravāha before a wave touches it (the L0 route for R9 assets, by analogy)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Pin the as-of date and state the rolling floor

- **SS ruling (2026-10-01) (R):** as for `ka_kota_chakra` (Q-L3-12). TI-L3-13, TI-L3-35.
- **Answers:** new moorti-N1; CF-28, CF-03
- **Change:** as for `ka_kota_chakra` FD-1, but the writer already accepts `ctx.config` `horizon_start`/`horizon_end`: the fix is to pass those from the build and record them in the build note (no writer change needed for the pin itself); floor 72 declared rolling (N/A by cause, CF-28) rather than refreshed to a build-date count
- **Files / declaration / migration:** `services/ka_moorti_nirnaya/writer.py:293`
- **Failing-first test and mutation:** CF-28 shape
- **Output change:** none for a fixed as-of
- **Blast radius:** `ka_gochara` (Pravāha) reads the rows and the `upstream_fingerprint`: a pinned as-of that is not today would make Gochara's freshness check compare against an older window — the default must remain today; any wave notifies Pravāha first
- **Rebuild:** none
- **Gate it moves:** Build.completion, Count (information)
- **Fix class:** writer code + declaration; **buildable before J1:** tier-dependent for the floor declaration

### FD-2 · Declare carriage and prose

- **Answers:** census Ldgr (no reading), Null/Narr; CF-06, CF-08
- **Change:** `carriage` declaration naming `moorti_classical_citation` as the source column and `source_qualification`/`corpus_verifiable` as the state; `prose_fields: []` with evidence `writer.py` (verbatim copy of `phala_brief`)
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** inspector reads Ldgr on the declared column; declarations validation
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Ldgr, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01

### FD-3 · Declare the family coupling

- **SS ruling (2026-10-01):** accepted (Q-L3-13, Q-L3-15); SS notifies Pravāha before a rebuild. TI-L3-37.
- **Answers:** new moorti-N2; CF-23
- **Change:** record in the declarations/registry notes that Pravāha-owned python (`gochara_v3`, `ka_vedha_gochara/freshness.py`) reads `kala_moorti_nirnaya` and its `upstream_fingerprint`, so a reviewer sees the real coupling next to the declared radius; no edge is added (the readers belong to the Gochara family and are not registry writers of their own here)
- **Files / declaration / migration:** the brief and the Track I notes only
- **Failing-first test and mutation:** n/a (documentation of an observed fact)
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** information
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

No Track I item touches this asset. The DB9 dict-row fix is already in the writer.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 72 (rolling)
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL with a tier column: the contract plus tier route to PASS
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* `moorti_classical_citation`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 3 / 3
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* FD-1
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, graha, window_start)` (DB UNIQUE). Volatile columns excluded: `id`, `computed_at`. The table already stores an `upstream_fingerprint`; use it as the cross-check, not as the comparison key. Horizon-edge rows (`start_truncated`, `moorti_computed = false`) change with the as-of: fingerprint at a fixed as-of window (pass `horizon_start`/`horizon_end`). `precision_regime` (`instant_grain` / `date_grain`) is part of the comparison: a fallback from instant to date grain changes the grade for that run. Rebuild expectation: same rows for the same as-of, L0 moorti table and ephemeris.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the verbatim L0 moorti table, the `moorti_computed` / `unsourced` discipline, the N7 provenance stamps, the upstream fingerprint.
- **Carriage check chosen (T4 §4.1; one only):** D3: re-derive the nakshatra offset and quality tier for a stratified sample of runs from the janma nakshatra, the ingress Moon position and the L0 table, by a hand-written fixture.
- **Opportunities (never blocking):** a verse-cited state needs the mūrti rule form in the corpus; the Moon's own ingress is out of scope by design.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **Q-L3-12 (R) — accepted.** N/A by cause `rolling_horizon` with the window declared; a rule only through `NA_RULE_DECISIONS` with SS approval (FD-1). Track I: TI-L3-13, TI-L3-35.
- **Q-L3-13 — accepted.** SS notifies Pravāha before any wave that rebuilds `ka_moorti_nirnaya` (Pravāha-owned python reads its rows and `upstream_fingerprint`). Track I: TI-L3-37.
- **Q-L3-15 — accepted.** `ka_moorti_nirnaya` is treated as non-family, with the coupling documented (FD-3).

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-12** — CF-28: how is a rolling floor declared?
- **Q-L3-13** — does SS notify Pravāha before any wave that rebuilds `ka_moorti_nirnaya`?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-13, TI-L3-20, TI-L3-35, TI-L3-37 (added by the SS rulings of 2026-10-01).
