# Kṣetra family reconciliation (for the Suvarṇa campaign)

- Date: 2026-09-28. Read-only: nothing was edited, committed, pushed, written to the DB or built.
- Sources: `origin/main` at `d968e889f` (2026-09-28), all remote `*kshetra*` / `l3/*` branches, the six named worktrees, the production DB (read-only), and the Nikaṣa worktree `/Users/Dev/madhav-nikasha` at `03b97a17c`.
- Path shorthand: `K/` = `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/`, `SVC/` = `platform/python-sidecar/services/ka_kshetra/`.
- Short names for the Kṣetra governance documents in `K/`:
  - BRIEF = `KSHETRA_ELEVATION_BRIEF_v1_0.md`, internal v4.10
  - PLAN = `KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md`, v1.17
  - SHEET = `KSHETRA_RULING_SHEET_v1_0.md`, v1.13
  - S3P = `KSHETRA_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`, v1.8
  - INB = `KSHETRA_INBOUND_RECONCILIATION_v1_0.md`
  - L0FIX = `KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md`
  - ABL = `KSHETRA_ABLATION_PREREGISTRATION_v1_0.md`
  - KIMIC = `KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md`
- Short names for the design documents:
  - W2D = `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_W2_FIELD_DESIGN_v1_0.md`
  - DES = `00_ARCHITECTURE/briefs/overnight_campaign_plans/DHARA_ENGINE_SPEC_v1_0.md`
  - PKP = `.../PURNA_KSHETRA_PLAN_v1_1.md`
  - DNC = `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md`
  - W0FS = `.../MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md`
  - HAND = `.../MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md`
- Citations are `file:line` in the `origin/main` blob unless another branch is named.

---

## 0. Bottom line

`ka_kshetra` is the largest asset in the estate: 10,982,957 `kala_field` rows and 5.36 GB for that table alone. It is also one of the least finished.

- **Canonical chart `482012f1`.** It holds a partial, mixed-generation field from a build that crashed on 2026-09-11.
  - 25 classes in `kala_field`, 15 in `kala_field_null`, 14 in `kala_field_windows`.
  - Zero salience, insight, timeline or snapshot rows, so nothing is published.
  - The field was built on a time axis that is measurably wrong (knots in days since J2000 are placed on a birth-relative axis).
  - 85.7% of its windows rest on a synthetic baseline.
- **Last good build.** No build of the canonical chart has ever completed. The only complete, published field is a 6-class run on the second chart `1c826d5a`, dated 2026-08-12. It predates the DHARA 1.2, resume-v9/v10 and time-axis corrections.
- **Rebuild is blocked.** The writer on main cannot rebuild either chart today. By design it raises `KshetraReplacementHeld` on any populated chart until the "W7 immutable candidate/publication" infrastructure exists (`SVC/writer.py:520-570`, landed in `fa9857f00` / #2607 on 2026-09-16). W7 is not built.
- **Where the work stands.** A full elevation packet exists and stage 3 (source-only, fixture-bound elevation) was authorized by the native on 2026-09-24. The executor never started, and no `ka_kshetra` code has changed on main since #2607.
- **Unmerged Kṣetra code.** A Kṣetra-touching code change sits unmerged on the live Gochara branch. Its registry migration `1084` has been applied to production without the file being on main.

---

## 1. Inventory

### 1.1 Assets

| asset_id | Layer | Kind | Target table | Relationship to Kṣetra | Evidence |
|---|---|---|---|---|---|
| `ka_kshetra` | kala (L3) | data, heavy writer (`has_substeps=t`), timeout 86,400 s, rung R3 | `kala_field` plus 14 sibling tables | The family's only producer | `asset_registry` row (query Q1) |
| `mi_bhara` | mimamsa (L5) | data | `kala_field_skill` (also writes `kala_field_gof` and `kala_insights WHERE lel_derived=true`) | Downstream consumer and co-writer of family tables; `depends_on={ka_kshetra}` | Q1; `pipeline/orchestrator/writers/mi_bhara.py:7,193-203` |
| `mi_sankalpa` | L5 | data | — | Downstream; `depends_on` includes `ka_kshetra` | Q1b |

- **Q1:** `select … from asset_registry where asset_id ilike '%kshetra%' or target_table ilike 'kala_field%'` returns `ka_kshetra` and `mi_bhara`.
- **Q1b:** `select asset_id from asset_registry where depends_on::text ilike '%ka_kshetra%'` returns `mi_bhara` and `mi_sankalpa`.

### 1.2 Tables and what each holds

"Owner" means the build-time writer. The writer declares 13 tables in `natural_key_partition` (registry row). `kala_field_routes` and `kala_field_boundaries` are deliberately excluded from that declaration as non-deterministic.

| Stage | Table | What it holds, in plain words | Rows: canonical `482012f1` | Rows: `1c826d5a` |
|---|---|---|---|---|
| S0 kinematics | `kala_field_kinematics` | Transit events over 100 years: ingresses, stations, contacts, eclipses | 120,118 | 119,543 |
| S2 promise graph | `kala_field_promise_nodes` / `_edges` / `_routes` | The natal "promise" for each event class as a graph from bodha signals, and the routes from promise to event | 88 / 114 / 91 | 86 / 106 / 91 |
| S3 clocks | `kala_field_clocks` / `_boundaries` | Which daśā systems apply, plus every daśā boundary with its birth-time/ayanāṃśa uncertainty σ_t | 8 / 261,998 | 8 / 249,322 |
| S1 primitives | `kala_field_primitives` | Transit "primitives" (vedha, mūrti, AV gate, station and so on) as time intervals | 165,082 | 151,721 |
| S4 field | `kala_field` | The hazard field λ_e(t) per event class, as log-linear segments (`alpha`, `gamma`, promise / clock / modifier / suppression terms) | **8,570,075** (25 classes) | 2,412,882 (6 classes) |
| S5 null | `kala_field_null` | A circular-shift null distribution per class and duration bucket (the q_e threshold) | 150 (15 classes) | 60 (6 classes) |
| S5 windows | `kala_field_windows` | Windows where λ exceeds its null, with peak, expected count, null_p, robustness, confidence tier and `baseline_is_synthetic` | 17,528 (14 classes; 15,024 synthetic) | 7,650 (6 classes; 0 synthetic) |
| S5 provenance | `kala_field_provenance` | Per-window term contributions traced to source facts | ≈1.35M across both charts (estimate); 1,029 MB | (same) |
| S6 salience | `kala_field_salience` | Five-axis salience (I/Q/R/B/A) plus submodular top-K selection | **0** | 7,650 |
| S6.5 insights | `kala_insights WHERE lel_derived=false` | Eight insight types (concurrence, rarity, absence of the expected, and others) | **0** | 415 |
| S8 timeline | `kala_timeline_spec` | Six timeline views: now, ahead, elect, story, priority, explain | **0** | 6 |
| Snapshot | `kala_field_snapshots` | The publication record: pin hash, attempted and built classes | **0** | 1 |
| Reference | `kala_field_weights` / `kala_field_weight_versions` | Structural classical priors θ⁰, version `v0_classical`; explicitly "NOT a fit", `n_events_used=0` | 29 rows / 1 row, global | — |
| Reference | `ka_kshetra_tier_basis` | Per-class prior tier: 6 calibrated, 19 shape_only, 2 not_applicable | 27 rows, global | — |
| L5 | `kala_field_skill` / `kala_field_gof` (written by `mi_bhara`) | Calibration skill and goodness of fit | 7 / 6, but pinned to snapshot `kfs_87484404…` from 2026-08-09, which no longer exists in `kala_field` (orphaned) | 0 |

- Row-count query Q2: `select chart_id, count(*) from <t> group by 1`.
- Q2b: `kala_field` per chart, grouped by `field_snapshot_id`.
- Sizes: `kala_field` 5,362 MB, `kala_field_provenance` 1,029 MB, `kala_field_boundaries` 320 MB (`pg_total_relation_size`).

### 1.3 Computation, in plain words

For each life-event class, the writer computes a continuous hazard rate over a 100-year horizon (W2D:536-623). In multiplicative form:

`λ = λ⁰ (actuarial baseline) × P̃ (natal promise) × C (daśā clocks) × M (12 transit modifiers) × S (suppression)`

- **Windows.** It then finds windows where λ exceeds its own circular-shift null. That null holds natal structure and the daśā ladder fixed and shifts only the transit term, with R = 1024 (BRIEF:329-344).
- **Downstream stages.** Windows are scored for salience, turned into insights, and laid out as timelines.
- **Circularity boundary.** Stages 0–8 never read the life-event log. Only L5 `mi_bhara` may (W2D:93-126).
- **Classical versus actuarial.** Only the clock term is classical. The baseline λ⁰ is actuarial (BRIEF:149-150). Only 6 classes have a real prior (`ka_kshetra_tier_basis` has 6 `calibrated` rows, seeded from NFHS-5, NSSO and MOSPI); the other 19 are `shape_only` synthetic.

### 1.4 Upstream edges: declared versus actually read

**Declared `depends_on`** (live registry): `ka_dasha_kala, ka_gochara_resonance, ga_panchanga, bo_pratijna, bo_sangati, bo_upaya, bg_cohort, bg_class_lifetime_counts, ka_vedha_gochara`. The `ka_vedha_gochara` edge came from migration `1084`, applied 2026-09-24 11:46; see §2.3.

**Actually read.** I searched `SVC/*.py` on main for table identifiers.

| Group | Tables |
|---|---|
| L1 | `chart_dashas`, `chart_facts`, `chart_positions` |
| L2 (bodha) | `bodha_pratijna`, `bodha_cgm_nodes`, `bodha_cgm_edges`, `bodha_msr_signals` |
| L0 | `bg_synthetic_cohort(_md)`, `bg_class_priors` / `brahma_class_priors`, `brahma_event_ontology`, `bg_transit_rules`, `bg_transit_moorti`, `bg_transit_av_gates`, `bg_kp_sublord_division`, `bg_dasha_systems` / `brahma_dasha_systems` |
| L3 | `gochara_resonance_map`, `kala_gochara_windows` (the retired sweep corpus), `kala_gochara_authority` |
| L4 | `phala_rectification` |

- **Declared but never read:** `bo_upaya` (target `bodha_rm_resonances`) and `bo_sangati` (target `bodha_cdlm_cells`). No `bodha_rm_*` or `bodha_cdlm_*` identifier appears anywhere in `SVC/`. This matches BRIEF:156-173 ("rank 4: edge register wrong both ways").
- **Read but undeclared:** about 10 tables, including `bodha_cgm_*`, `bodha_msr_signals`, `kala_gochara_windows` and `phala_rectification`.
- **Forbidden upward read.** `phala_rectification` (L4) is read at `SVC/uncertainty.py:191`, called from `SVC/stage3_clocks.py:1012` (`U.fetch_sigma_t_days`).

### 1.5 Downstream consumers

**Build-time.**
- `mi_bhara` binds the field with `SELECT field_snapshot_id FROM kala_field WHERE chart_id=%s LIMIT 1`, which is unordered (`writers/mi_bhara.py:403`). It therefore binds to any snapshot present, not to a published one.
- `mi_sankalpa`.

**Serving** (grep of `platform-mcp/src` on main):

| Surface | Reads | Location |
|---|---|---|
| `kala_envelope.ts` | `kala_field_snapshots` and `kala_field_skill` | :133-257, :520-556 |
| `kala_views/priority.ts` | `kala_field_salience` | :53-139 |
| `kala_views/explain.ts` | `kala_field_windows` | :40 |
| `ahead_autofile.ts` | `kala_field_windows`, behind SM-γ C5 | :257-287 |
| `kala_upaya_diagnosis.ts` | `kala_field_routes`, optional, currently off | :896-994 |

- `kala_ritual_resonance.ts:491-507` states that "no serving capability exists over any `kala_field*` table".
- `kala_field` itself is dark: no reader anywhere. Nikaṣa R23 confirms this (NIKASHA_CHANGE_REGISTER_v2_0.md:151).
- On the canonical chart every one of these surfaces currently returns an honest null or not-computed, because there is no snapshot and no salience.

---

## 2. What was done, and where it stands

### 2.1 Dated timeline

All commits are on `origin/main` unless marked otherwise.

| Date | What | Evidence | Status |
|---|---|---|---|
| 2026-07-29/30 | KALA_W2_FIELD_DESIGN v1.0 (the science); ṢAḌ-DARŚANA W2 lanes A–E build stages 0–8 and the shim | `d0310c91f`, #944–#949 | merged |
| 2026-08-05/07 | ṢAḌ-DARŚANA, ŚABDA-ŚUDDHI and SIDDHĀNTA rebuilds; first "complete" builds, several of them only 0–5 s long (likely no-op) | `build_run_assets` query Q4 | historical |
| 2026-08-09/10 | SAMPŪRTI Wave 0/1: the "clockless field" fix, OOM fixes, batching | `c93540ca8`, `5339f251c`, `888459364`, … | merged |
| 2026-08-12 | `1c826d5a` 6-class build completes (20:27–22:26, about 2 h). This is the only published snapshot, `kfs_b3bcf77a…` | Q4, Q2b | data still live |
| 2026-08-13/14 | DHARA analytic engine: sweep, vectorized null, Layer 0/1, `shape_only` tier, `baseline_is_synthetic` on windows; ENGINE_VERSION flipped to analytic | `00345531e`, `2f4e7a872`, `e822700a2`, `2e435600d`, … | merged |
| 2026-08-14/16 | SAMPŪRTI A6–A8 canonical-chart attempts: every full attempt orphaned; only canary-class runs completed | Q4 | failed |
| 2026-08-20/21 | PARIŚEṢA fixes: F-78 attempted-vs-built disclosure, F-149/F-185/F-186 streaming | `47ea424b8`, `b5638f771`, `3164f37c9`, `889701d86` | merged |
| 2026-09-05 | L3 W3 M7+M8 §N.8 fixes | `97fd08e1c` | merged |
| 2026-09-09 | Migrations 1002/1003: output_digest_spec and natural_key_partition | `d5f134e68` (#2513); `_migrations_applied` 09-09 14:41 | merged and applied |
| 2026-09-10 → 09-11 | Superseded Nirmāṇa elevation: 29 canonical attempts in 7.6 h. The first ran 1 h 55 m and was orphaned; then stall kills and about 25 kill-redispatch cycles; the last ended `worker_crash: OperationalError: the connection is lost` at 03:31 | Q4 (`triggered_by = nirmana-elevation:…`, `l3-lane-kill-redispatch-ka_kshetra`) | failed; left the partial field |
| 2026-09-11 | Local-only branch `codex/nirmana-ka-kshetra-elevation-k0-k1` (`61cff2501`): KA_KSHETRA_ELEVATION_CONTRACT v1.0 plus a test | `git show --stat 61cff2501` | not on main; superseded (inference) |
| 2026-09-13 → 09-15 | Codex branches `codex/l3-kshetra-p0`, `-p0-correction`, `-w0-preservation`: P0 planning safety, DHARA oracle, clock left limits, W0 populated-slice preservation | branch logs | squashed into #2607 |
| 2026-09-16 | **#2607 `fa9857f00`**: governed L0–L3 source execution. Introduces `KshetraReplacementHeld`, `_RESUME_VERSION=10` and DHARA 1.2. This is the last main commit touching `SVC/` | `git log -S KshetraReplacementHeld` | merged; deployment likely (sidecar template tag `079e77ef9` descends from `fa9857f00`, per HAND:443; not independently verified) |
| 2026-09-18 | Migrations 1035/1036: producer history and generations for L1/L2 (a partial foundation for immutable generations) | `_migrations_applied` | applied |
| 2026-09-22 | Kāla readiness audit and blueprint; Kṣetra elevation packet (brief v4.3, plan v1.4, Kimi K3 review, ruling sheet) | `54766b5da` (#2722) | merged (docs) |
| 2026-09-23 | CLOSE (rulings 7/8/9 independently reviewed); judge and rubric sealed; stage-3 executor prompt prepared; ruling-8 tighten; stage 3 AUTHORIZED; rank-0 time-axis defect measured | #2724, #2725, #2726, #2728, #2729 | merged (docs) |
| 2026-09-24 | L0 vedha repair applied to production (migrations 1075–1079, #2727); binding 2.0 folded (#2730); inbound reconciliation (#2732, `130108538`), the last Kṣetra doc on main | as listed | merged (docs), L0 data applied |
| 2026-09-24 | **Gochara branch** `f256b24d3`: "WP7 K-1/V-1: N-10 authority seam in ka_kshetra". Edits `SVC/writer.py`, `SVC/stage4_field.py`, tests, and adds migration `1084_wp7_k1_v1_registry_edges.sql`. 1084 was applied to production 09-24 11:46 | `git show --stat f256b24d3`; `_migrations_applied` id 876 | **code NOT on main; migration applied in prod** |
| 2026-09-27/28 | Nikaṣa inspection: 9 open `ka_kshetra` gaps; R237 notes "ka_kshetra below its floor" | `asset_gaps.jsonl`, register :442 | open |

### 2.2 Branches

The branch/worktree sub-audit compared files by blob hash.

| Branch | Goal | Merged? |
|---|---|---|
| `l1-w405-ka-kshetra-output-digest-spec` | Migrations 1002/1003 | Yes: #2513 |
| `l3/kshetra-elevation` | Packet v4.3 / v1.4 | Yes: #2722 (tip identical to the squash) |
| `l3/kshetra-close` | Close plus review of rulings 7/8/9 | Yes: #2724 |
| `l3/kshetra-stage3-prep` | Judge, rubric, S3P, L0 fixes, ablation pre-registration | Yes: #2725 |
| `l3/kshetra-db-tighten` | Ruling 8 | Yes: #2726 |
| `l3/kshetra-stage3-authorized` | Stage 3 authorized | Yes: #2728 |
| `l3/kshetra-taxis-defect` | Time-axis defect | Yes: #2729 |
| `l3/kshetra-binding-2-0` | Binding 2.0 | Yes: #2730 |
| `l3/kshetra-inbound-reconciliation` | Inbound sweep | Yes: #2732 |
| `codex/l3-kshetra-p0`, `-p0-correction`, `-w0-preservation` | P0 and W0 safety code | Yes, superseded by #2607; every `SVC/` file on `-w0-preservation` is identical to main |
| `l3/kala-elevation-readiness` (136 ahead) / `l3/kala-layer-briefs` (191 ahead) | Kāla-wide readiness and briefs | **No.** Kṣetra-relevant docs exist only here: `KALA_SYNERGY_AUDIT/BINDING/AMENDMENTS_v1_0.md`, `KALA_ENVIRONMENT_READINESS_v1_0.md`, `KALA_PRE_ELEVATION_CHECKLIST_v1_0.md`. The verbatim native stage-3 authorization is in blueprint v4.8 at line 491 on this branch (commit `447ba7a51`) |
| `l3/gochara-autonomous-wp0-7` (live, tip `ae0743136` 09-28) | Gochara WP0–7/WP10 | **No.** Carries Kṣetra code `f256b24d3`, `K/KSHETRA_INSTRUCTIONS_FROM_GOCHARA_2026-09-24_v1_0.md` (status ISSUED) and `KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT_v1_0.md` (ruling-8 arithmetic corrected to 42/36/0/6) |

**Worktrees.** None has uncommitted work.

| Worktree | Branch | State |
|---|---|---|
| `/Users/Dev/madhav-l3/kshetra` | main | at `130108538`, 18 behind |
| `/Users/Dev/madhav-l3/kshetra-stage3` | local `l3/kshetra-stage3` | 0 own commits, so the executor never started |
| `/Users/Dev/madhav-l3/kshetra-kimi-review` | detached | at `d0b127455` |
| The three `.codex` worktrees | codex branches | at their pushed tips |

### 2.3 Half-done items

1. **Stage-3 executor authorized but not started.**
   - `S3P:5` reads `status: AUTHORIZED_STAGE_3_ONLY … stage 4 explicitly NOT opened; executor not yet started`.
   - `BRIEF:21` and `INB:163` say the same.
2. **Migration file drift.**
   - Production has `1084_wp7_k1_v1_registry_edges.sql` applied (`_migrations_applied` id 876). The live `ka_kshetra.depends_on` includes `ka_vedha_gochara`.
   - Neither the file nor the matching writer change (N-10 authority seam, removal of the `'v1'` COALESCE) is on main.
   - The Gochara branch's `wp7_packets/PACKET_K1_kshetra_dependency.md:5` still says `DESIGN_ONLY_NOT_IMPLEMENTED`.
3. **Canonical field is a crashed partial.** Its tables come from different attempts:

   | Tables | Timestamp or snapshot |
   |---|---|
   | S0–S3 (`primitives`, `clocks`, `boundaries`, `promise_nodes`, `routes`) | stamped 2026-09-11 01:49–01:50 |
   | `kala_field` | computed 2026-09-10 19:40–21:15 |
   | `null` / `windows` / `provenance` | span 09-10 21:15 → 09-11 03:22 |
   | `skill` / `gof` | point at dead snapshot `kfs_87484404…` (08-09) |

   - Q2c: per-table `min/max(computed_at)` and `field_snapshot_id`.
4. **Governance surfaces lag.**
   - `CURRENT_STATE_v1_0.md` on main has no entry for the Kṣetra packet or the stage-3 authorization.
   - `S3P:16` says the "next free migration is 1082", which is stale: 1082, 1084, 1087 and 1150 are all taken and applied.
   - `S3P:89-90, 283-284` still quote the superseded 32/3/6 vedha split.
   - `PLAN:32` still reads `independent_reviewer: UNASSIGNED`.

---

## 3. Current production state

These are measured today (read-only).

| Measure | Value | Query or source |
|---|---|---|
| `asset_throughput`, `ka_kshetra` @ `482012f1` | `state=error`, `last_error='worker_crash: OperationalError: the connection is lost'`, `last_built_at` 2026-09-11 03:31, rows_written 1,183,134 | Q3 |
| `asset_throughput`, `ka_kshetra` @ `1c826d5a` | `stale`, last built 2026-08-12 22:26, 837,992 rows | Q3 |
| `asset_throughput`, `mi_bhara` | canonical `error` (BLOCKED by timeout 08-21); `1c826d5a` `error` (BLOCKED by `ka_kshetra`) | Q3 |
| All-time `build_run_assets` for `ka_kshetra` | 158 rows: 98 error, 33 queued (never started), 15 complete, 12 aborted. 114 h of wall time in started attempts | Q4 |
| Canonical chart | 88 started, 11 "complete", 13 blocked. **No full-class build has ever completed.** The last completes (08-14 22:34–23:18) were SAMPŪRTI canary runs, and 3 of the 11 "complete" rows lasted under 10 s | Q4 |
| Most recent attempts | 29 attempts from 2026-09-10 19:33 to 09-11 03:31, all errors | Q4 |
| `kala_field` canonical | 8,570,075 rows, 25 classes, one snapshot `kfs_18052158…`, `weights_version=v0_classical`, `refinement_exhausted=0` | Q2b |
| Registry floor | `target_floor=8,599,775` against live 8,570,075 (−29,700). `size_sql` is NULL; `count_sql` and `integrity_check_sql` are set | Q5; Nikaṣa `Count.floor` |
| Time axis (live) | `kala_field` t spans 0…36,525 on both charts. `kala_field_kinematics.t_days` spans −5,808.75…30,717 on canonical, i.e. days since J2000 (birth 1984-02-05 is J2000 − 5,808.75 d) | Q6; confirms PCD-1 (PLAN:102-125) |
| Upstreams at canonical | `bo_pratijna` stale (09-09), `bo_upaya` stale (09-09); the others lit (`bo_sangati` 09-11, `ka_dasha_kala` 09-10, `ga_panchanga` 09-07, `ka_gochara_resonance` 09-07, `ka_vedha_gochara` 09-07, `bg_*` global) | Q3b; Nikaṣa `Build.dep_liveness` |

**Can the canonical chart be rebuilt today? No.** Three independent reasons:

1. **The writer refuses by design.** `prepare:replace` calls `_populated_owned_table`, which takes an advisory lock and runs an EXISTS probe over all owned tables. It raises `KshetraReplacementHeld` if any has rows for the chart (`SVC/writer.py:520-570`, `:2482` `_OWNED_TABLES`).
   - Both populated charts are therefore frozen as they are.
   - The documented release is "W7 immutable candidate/publication" (writer docstring lines 19-26; W0FS:125-138, 241-247; HAND:699).
   - W7 is unbuilt.
2. **A DAG build that includes `bo_upaya` would fail before reaching Kṣetra.** Nikaṣa R244 (register :459): #2607 removed a delete, so any `bo_upaya` rebuild hits a NO ACTION FK violation.
   - `ka_kshetra` would then be recorded `BLOCKED`, even though it never reads `bo_upaya` data (§1.4).
   - R244 was ruled 2026-09-28 as "fix by restoring the delete, L2 owner PR" (register :11); the fix has not landed.
3. **Build reliability is unproven for this scope.** The last full canonical attempt ran about 7.5 h and died on a lost connection.
   - The crash cause is a hypothesis only (the 600 s idle-in-transaction killer on `amjis_app`), not reproduced (`l3_autonomous/readiness/_work/LANE_A2_KSHETRA_CRASH_DIAGNOSIS.md:4,44-81`).
   - For scale, the 6-class run on `1c826d5a` took about 2 h.

---

## 4. Open problems

### 4.1 Correctness defects

All are routed to stage 3 and all are open.

| ID | Defect | Evidence | Severity |
|---|---|---|---|
| PCD-1 (rank 0) | Time axis: kinematic and primitive knots are in days since J2000, but they are clipped and partitioned on a birth-relative [0, H]. The native's first ~16 years are absent and the kinematic structure is misplaced by ~15.9 years. `mi_bhara/living_lel.py:113` reads t as days since birth | PLAN:102-125; SHEET:85-93; Gochara instructions §4 (`stage4_field.py:1361-1369` → `writer.py:2049`); live Q6 | Invalidates every existing field row on both charts |
| G3 (rank 0, after PCD-1 per B8-10) | Field and null are chart-wide. Route scoping exists only in `layer1.project_layer1`, which has no production caller. Needs a field≡null≡projection byte-equality test before any `null_p` is served | IR:130-136; PLAN:126-139; S3P:224-233; SHEET ruling 9 | null_p semantics wrong |
| Rank 1 | `baseline_is_synthetic` is computed and then discarded (`layer1.py:89`); it is not among the 21 `kala_field` insert columns | BRIEF:218-223; DES:211-213 | Honesty (§N.7/§N.8) |
| Rank 2 | S3 performs an upward read of L4 `phala_rectification` | `SVC/uncertainty.py:191` via `stage3_clocks.py:1012`; BRIEF:142-143,225 | Layer violation; S3 "cannot run" |
| Rank 3a | `kala_field_boundaries` reads `chart_dashas` without `ayanamsha_id`; copies disagree on the earliest MD lord; up to 1,434 ambiguous dedup groups | registry `natural_key_partition` text; BRIEF:320-327 | Non-determinism |
| Rank 3b | `kala_field_routes.path_edge_ids` embeds bigserial ids that are re-minted on every rebuild | same; BRIEF:355-357 | Non-determinism |
| Rank 4 | Edge register wrong both ways (see §1.4) | BRIEF:156-173 | DAG and staleness correctness |
| Rank 5 | `mi_bhara` binds the snapshot with an unordered `LIMIT 1` over `kala_field` | `writers/mi_bhara.py:403`; BRIEF:189-195 | L5 binds an unpublished or dead snapshot |
| DAG edge guard | `writer.py:2344` (read of `kala_gochara_windows`) would be a HARD violation; three options stated | S3P:262; INB | Open |
| `'v1'` fall-through | COALESCE to a retired generation | `writer.py:2330-2347`, `stage4_field.py:1386-1389`; fixed only on the Gochara branch `f256b24d3` | Provenance hole |
| Duplicate producers | `build_vedha_primitive` / `build_moorti_primitive` recompute verdicts that ruling 4/8 assigned to `ka_vedha_gochara` / `ka_moorti_nirnaya` | Gochara instructions §1; SHEET ruling 4 | Two answers for one instant |
| Contact episodes | `stage0_kinematics.py:329 find_contact_episodes` is a second contact producer | Gochara §2; ruled evaluation-only (B8-6, SHEET) | Needs declaration/stamping |
| Others | K-1 bare `source_pk`; F-KSHETRA-9 (S0–S3 register no substeps); resume fingerprint blind to upstream content; no SAVEPOINT on cohort read; `null_resolution` declared 1/(R+1) but bound 1/R; node frame mixes true transit with mean natal (C-2) | S3P:86,260-263; BRIEF:138-141,174-175; KIMIC | Mixed |
| W7-scope | F-KSHETRA-6: stage-8 per-view substep 1,210 s, over the writer timeout. The six-view grain is orphaned by the product definition | PLAN:474-475; T1:151-158 | Build and serving |

### 4.2 Nikaṣa gaps

Nine, all OPEN (`/Users/Dev/madhav-nikasha/00_ARCHITECTURE/control/asset_gaps.jsonl`, last row per gap_id, ts 2026-09-27T21:34):

| Gap | What was measured |
|---|---|
| `Build.completion` | Build record is `error` (1,183,134 written vs 8,570,075 live) |
| `Build.dep_liveness` | 7/9 dependencies lit; `bo_pratijna` and `bo_upaya` stale |
| `Build.history` | Latest run is an error (09-11); 98 errors, 12 aborts |
| `Carr.detector` | No D1/D2/D3 detector |
| `Complete.depth` | `refinement_residual` never populated (refinement is dormant by ruling B-4) |
| `Cost.baseline` | NO_DETECTOR (migration 1094 instrument absent) |
| `Count.floor` | −29,700 |
| `Earn.build_record` | NO_DETECTOR |
| `Idem.pattern` | **FAIL**: refused rebuild at `writer.py:545`; §N.3 "rebuild replaces" not met |

Related register rows:
- **R237** (:442, OPEN): Kāla data findings including "ka_kshetra below its floor".
- **R244** (bo_upaya FK): ruled, fix pending.
- **R205** (OPEN): the shared-table producer declaration for `kala_field_skill`.

### 4.3 Reviewer findings and design questions still open

- **Kimi K3 close review.**
  - C-2 (`config_pin` lacks node frame/epoch) is open.
  - C-4 (cross-class comparability) is open as B-4 obligation (c).
  - C-5 (governance concentration: every ruling was made by the author under the native's delegation) is observed, not resolved (KIMIC:164-209).
- **Unsettled** (BRIEF:530-537; PLAN:480-482):
  - The three-arm ablation (Q1) has never run. It is pre-registered as `SEALED_PENDING_HASH_RECORD` (ABL:5).
  - `weakest_link` / A1 has not been run.
  - Late-worker publication protection is unresolved.
  - 25 vs 27 event classes is unexplained.
  - The crash cause is unconfirmed.
- **Data and L0.**
  - Vedha rows are all `unqualified` in production until the stamp columns are populated. Migration 1082 is applied, but the stamping writers are on the Gochara branch.
  - 6 Rāhu/Ketu vedha rows are unsourced (L0 owner's decision).
  - 132 `house_vedha` rows still cite "BPHS Ch.29".
  - Sarvatobhadra population was "attempted and BLOCKED" (INB:84).
  - There is an L2 DEMAND for `event_class.valence`.
  - The `independence_group` migration is owned by Saṅgam.
  - There are 79 dangling MSR predicate ids (PLAN:218).
- **Ablation design gap** (my observation). ABL selects real production chapters (ABL:62-65) while requiring fixture-bound arms with the W7 hold standing (ABL:126-128). How it runs without a correct populated field is not specified.

---

## 5. The "fully enriched" target

### 5.1 Documented intent

**Terminal state.** `PRODUCER_READY`, then `t3 FROZEN` (BRIEF:39-40, 514-515; PLAN:259-267). In BRIEF's words, the elevation "is qualification, reach and a complete generation — not more columns" (BRIEF:76-77). Its stated goal is to qualify the interval/trajectory-segment object and give it a reach, an L3-U11 capability with a sentinel test (BRIEF:12-15).

**Product scope (ruling 1).** The calibrated 6-class run is the product; the 25-class rows are substrate.
- Ruling 2: build fresh at `L3-W7-KSHETRA-COHERENT-PUBLICATION-01`. The old rows cannot be resumed.
- This narrows the earlier PŪRṆA-KṢETRA mandate of 27 classes, 1024 nulls and a cold build of about 60 minutes or less (PKP:53-57, 251-255).

**Stage arc** (PLAN:259-267):

| Stage | Content | Status |
|---|---|---|
| 0 | Reconcile | ✓ |
| 1 | Frame | ✓, ablation not run |
| 2 | Brief | ✓ |
| 3 | Source elevation | authorized, not started |
| 4 | Physical data: calibrated 6-class run built fresh at W7 | HELD: W7 ← W1 ← RI-01 |
| 5 | Integrate U11/U10/U01, then P6→P2→P1 | held |
| 6 | Terminal | held |

**Stage-3 internal phases** (S3P:180-304):
- Phase 0: gate.
- Phase 1: time axis, then G3.
- Phase 2: seams (S4/S3/S2 fixes, pins including node frame and `t_axis_convention`, edge register, SAVEPOINT, synergy and inbound items a–h).
- Phase 3: ablation.
- Phase 4: S1, U10, U11, U01, gated on an ablation PASS.
- Phase 5: P6→P2→P1.

**End-state guarantees** (PLAN:294-310):
- `baseline_is_synthetic` on every row.
- Only manifest-published snapshots are selectable.
- A null contract on the row.
- `sigma_t_source` and `weakest_link` carried.
- A served-evidence sentinel.
- Field ≡ null ≡ projection.
- L5 binds through the manifest (`ORDER BY built_at DESC`) and refuses when there is no manifest (PLAN:241).

**Grounding.**
- Consume `ka_vedha_gochara` and `ka_moorti_nirnaya` and retire the internal derivations after one cross-check generation (rulings 4 and 8).
- σ_T from L1 birth-time precision, never `phala_rectification` (ruling 3).
- Node frame: true node, declared (ruling 7; the L0 side is done).
- The malefic covariate (PG349/PG353) is `unqualified`; the field is built without it (SHEET, 2026-09-24).

**Serving.** A `query_field_trajectory` capability with a field list, `density_contract` and an L3-owned sentinel test; Pūrṇa implements it (BRIEF:401-417).

**Performance.** P6 (interval indexes, bounded streaming, recoverable publication), then P2, then P1 (the exact blocked null programme, which avoids about 372M ops per class). P1 is gated on the ablation (ruling 5; BRIEF:395-399; HAND:629-634).

**Enrichment** (PLAN:271-288; ruling 6):
- E0 (counterfactual-self) and E1 (mechanism fingerprint) first. The plan calls each "a query".
- E2–E8 only on cited sources, after the ablation. For scale, the E2 three-arm null is about 2–3× S5.

### 5.2 My inference, not stated in the documents

- "Fully enriched" in the native's sense probably goes beyond `PRODUCER_READY`:
  - Real priors for more than 6 classes. Today 19 are `shape_only` synthetic and produce 85.7% of canonical windows.
  - A fitted weights version: `v0_classical` has `n_events_used=0`.
  - Populated refinement: `refinement_residual` has never been written.
- None of this is scheduled in PLAN. Ruling 1 explicitly makes 6 classes the product.
- Extending coverage would re-open ruling 1 and needs a native decision.

---

## 6. Gap and effort

These are my estimates. They rest on four things:
- (a) the number and locality of the named defects, most of which cite exact files and lines;
- (b) observed pace: SAMPŪRTI landed about 30 Kṣetra PRs in 08-09 → 08-16, and the packet documents took 09-22 → 09-24;
- (c) measured build cost: about 2 h for 6 classes on `1c826d5a`, about 7.5 h crashed for 25 classes;
- (d) the fact that the documents give no durations for stages 3–6.

One "day" means one focused engineering session plus review. The ranges are wide where infrastructure (W7) or research (priors, sources) dominates.

### 6.1 Must-fix correctness

| # | Item | Effort | Notes |
|---|---|---|---|
| C1 | PCD-1 time axis: one convention, `t_axis_convention` in `config_pin`, and a detector that fails on today's rows | 1–2 d | Makes all existing rows invalid, so a rebuild is mandatory |
| C2 | G3 route-scoped hoist plus the field≡null≡projection byte-equality test | 2–4 d | Ruled Option B; touches stage 4 and 5 |
| C3 | Thread `baseline_is_synthetic` onto `kala_field` (migration plus insert) | 0.5–1 d | |
| C4 | Remove the S3 upward read: σ_T from L1, interim `default_120s_assumption` | 0.5–1 d | |
| C5 | Boundaries `ayanamsha_id` pin; routes content-addressed id or `id_basis` | 1–2 d | Unblocks natural-key declaration for 2 tables |
| C6 | Edge register: drop the `bo_upaya`/`bo_sangati` phantom edges, declare the real reads, resolve the `writer.py:2344` guard | 1 d plus a migration | Also removes R244 exposure |
| C7 | Reconcile the Gochara branch's `f256b24d3` (authority seam, `'v1'` removal) with main; land a file for the already-applied 1084 | 0.5–1 d | Coordination with the live Gochara lane |
| C8 | Retire duplicate vedha/mūrti derivations after one cross-check generation; declare contact episodes evaluation-only | 2–3 d | Needs a cross-check generation, i.e. a build |
| C9 | `mi_bhara` manifest bind (U10); K-1 `source_pk`; resume fingerprint; cohort SAVEPOINT; `null_resolution`; node frame pin | 2–3 d | Mixed L3 and L5 |
| **Subtotal** | | **≈ 11–19 days** | Source-only, fixture-provable (stage 3 Phases 1–2) |

### 6.2 Rebuild capability and physical data

This is the gating item.

| # | Item | Effort | Notes |
|---|---|---|---|
| R1 | W7 immutable candidate/publication for the 15-table family, or a native-ruled interim path (for example, archive-then-clear under explicit authorization) | W7 proper: 1–3 weeks. Interim path: 1–3 days plus a native ruling | 1035/1036 give an L1/L2 generation foundation; the L3 equivalent is not built. A §N.3 / Idem FAIL until done |
| R2 | Build reliability: diagnose the lost-connection crash, P6 (streaming, interval indexes, recoverable publication), stage-8 per-view timeout (F-KSHETRA-6) | 1–2 weeks | Much cheaper at 6 classes |
| R3 | First fresh canonical build (6-class), then Nikaṣa re-certification and `target_floor` reset | 1–2 d wall | Canary first |

### 6.3 Algorithm and enrichment

| # | Item | Effort | Notes |
|---|---|---|---|
| A1 | Run the three-arm ablation (sealed judge, Kimi K3, native adjudication) | 2–4 d | Must precede S1 ingestion; its design gap (§4.3) needs closing first |
| A2 | S1 ingestion; E0 counterfactual-self; E1 mechanism fingerprint | 3–5 d | Gated on an ablation PASS |
| A3 | P2 then P1 exact null programme | 1–2 weeks | P1 is about 4× everything else (BRIEF:399) |
| A4 | E2–E8 on cited sources | 2–6 weeks, open-ended | Each needs source qualification |
| A5 | *(Inference, beyond PLAN)* Real priors for the 19 `shape_only` classes; a fitted weights version; refinement activation; 25 vs 27 classes | Weeks to months; research-bound | Re-opens ruling 1 |

### 6.4 Serving and retrieval

| # | Item | Effort |
|---|---|---|
| S1 | `query_field_trajectory` (U11) capability with `density_contract` and sentinel; registry entry | 3–5 d |
| S2 | Light up the existing surfaces (envelope, priority, explain, ahead C5, ritual λ) against the first published snapshot; verify honest-null paths still hold for unpublished charts; U01 | 2–4 d |
| S3 | Settle the stage-8 six-view grain against the product definition | 1–2 d plus a ruling |

### 6.5 Governance

| # | Item | Effort |
|---|---|---|
| G1 | Close the 9 Nikaṣa gaps: Idem via R1, Build via R3, Carr detector, Cost/Earn instruments (1094), Complete.depth disposition for `refinement_residual`, Count floor | 2–4 d, spread across the above |
| G2 | Refresh S3P (migration numbers, 36/0/6), CURRENT_STATE entry, assign an independent reviewer, merge or retire the Kāla-branch docs (synergy binding, rulings recount) | 1–2 d |
| G3 | Registry: `size_sql`, natural-key declaration for routes and boundaries after C5, R205 shared-table producer declaration | 1 d |

### 6.6 Totals

- **A correct, rebuilt, published 6-class field on the canonical chart, served and Nikaṣa-certified:** about **5–9 weeks**. That is §6.1 + R1–R3 + A1–A2 + S1–S2 + G1–G3, with W7 as the swing factor.
- **"Fully enriched"** (adding A3–A4, and A5 if the native wants beyond-PLAN coverage): about **10–20+ weeks**, dominated by source-qualified enrichment and prior research.

---

## 7. Risks and dependencies

1. **Refused rebuild (the biggest risk).**
   - Both populated charts are locked by `KshetraReplacementHeld`.
   - The canonical chart's rows are simultaneously wrong (PCD-1), partial (14 of 25 classes windowed) and unpublished.
   - Until W7 exists or the native rules an interim clear, no correction can reach production data. Every stage-3 fix stays fixture-only.
   - Failure mode to watch: pressure to disable the guard to "get a build through". HAND:291 explicitly forbids this.
   - Any clear of the canonical slice is a DELETE of about 11M rows (about 6.7 GB with provenance and boundaries) and needs explicit native authorization.
2. **Size and reliability.**
   - 5.36 GB for `kala_field` for two charts. Canonical is 25 × 342,803 segments (BRIEF).
   - 114 h of cumulative attempt time, 98 errors, and never a full canonical completion.
   - The crash cause is unconfirmed. The 6-class scope (ruling 1) cuts the load by about 4×, but per-chart storage still scales linearly with charts.
3. **`bo_upaya` / R244.**
   - `ka_kshetra` declares `bo_upaya` but never reads it (§1.4). Any orchestrated run that rebuilds the stale `bo_upaya` will hit the FK violation, and `ka_kshetra` will be marked BLOCKED.
   - Mitigation: either the R244 L2 fix lands (ruled 09-28, owner PR pending) or Kṣetra drops the phantom edge (C6). The second is in-scope and decouples the two.
   - `bo_pratijna` is also stale on canonical, and it IS read: it drives event-class discovery. Rebuilding it may change the class set.
4. **Overlap with the live L3 Gochara workstream.**
   - `l3/gochara-autonomous-wp0-7` (active 09-28) edits `SVC/writer.py` and `stage4_field.py`, and has already applied a Kṣetra registry migration (1084) to production without the file on main.
   - It issues binding instructions to Kṣetra: retire the duplicate vedha/mūrti producers, reconcile contact episodes, decline `unstable_key`, and flag the time axis.
   - Two lanes editing the same writer means merge-conflict and semantic-collision risk, and the migration numbering has already collided once (1075/1076 → 1080/1081; 1082 taken).
   - Suvarṇa should sequence after, or explicitly coordinate with, the Gochara merge.
5. **Downstream contamination.**
   - `mi_bhara`'s unordered bind means L5 can calibrate against an unpublished or dead snapshot.
   - `kala_field_skill` / `gof` on canonical already point at snapshot `kfs_87484404…`, which has no field rows.
6. **Governance concentration.** Every one of the 16 rulings was made by the author under the native's delegation (SHEET:25-27; KIMIC C-5), and the packet still has no independent reviewer assigned.
7. **Stale second chart.** `1c826d5a`'s published 6-class snapshot is the only served-capable field. It predates DHARA 1.2 and has the same time-axis defect, so it should not be treated as a reference output.

---

## Appendix: queries run (read-only, `timeout` ≤ 240 s)

- **Q1:** `asset_registry` rows for `%kshetra%` / `kala_field%` targets.
  - **Q1b:** `depends_on::text ilike '%ka_kshetra%'`.
  - **Q5:** `target_floor`, formula, `size_sql`, `integrity_check_sql`, `count_sql`.
- **Q2:** per-chart counts for all 18 family tables.
  - **Q2b:** `kala_field` grouped by chart, snapshot, weights and x-schema, with `min/max(computed_at)`.
  - **Q2c:** per-table timestamps and snapshot ids.
- **Q3:** `asset_throughput` for `ka_kshetra`, `mi_bhara`, `mi_sankalpa`, `bo_upaya`, `ka_vedha_gochara`, `ka_gochara_resonance`.
  - **Q3b:** upstream states at canonical.
- **Q4:** `build_run_assets ⋈ build_runs` for `ka_kshetra`: state histogram, the last 40 started, the complete list, and attempts since 09-10.
- **Q6:** `min/max(t_start, t_end)` on `kala_field`, `min/max(t_days)` on `kala_field_kinematics`, and the synthetic-window share.
- `_migrations_applied` for 569, 867, 1002, 1003, 1035, 1036, 1080–1084, 1087, 1091 and 1150.
- `pg_total_relation_size` for the three largest tables.
