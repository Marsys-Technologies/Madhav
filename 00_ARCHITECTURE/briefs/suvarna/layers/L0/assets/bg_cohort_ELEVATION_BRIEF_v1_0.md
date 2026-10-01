---
asset_id: bg_cohort
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [bg_cohort-Earn.build_record, bg_cohort-Cost.baseline, bg_cohort-Carr.detector, bg_cohort-Build.history, bg_cohort-Build.completion]
---
# bg_cohort — Synthetic reference cohort (10,000 charts + 100,000 Mahādaśā rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Writes `bg_synthetic_cohort` (10,000 synthetic birth charts: positions by sign/nakshatra plus Lagna) and `bg_synthetic_cohort_md` (10 Vimśottarī Mahādaśā rows per chart = 100,000), a chart-independent base-rate population for the Rarity axis and matched sub-cohorts (`platform/python-sidecar/pipeline/orchestrator/writers/bg_cohort.py:1-30`). Birth instants are drawn uniformly over 1900-01-01 → 2099-12-31 with a fixed RNG seed `COHORT_RNG_SEED = 20260729` (`:150`), so the cohort is reproducible; every position is a real pyswisseph computation, only the birth inputs are synthetic (`:60-75`). `data_disposition = RETAINED_AS_CAPITAL`. Depends on the service `bg_ephemeris_engine`. Readers: `ka_kshetra.py` and `mi_bhara.py` reference it; `kala_ritual_resonance.ts:568-575` calls it 'a dormant L0 asset with no retrieval capability wired into this surface', which is why the declarations leave `served_surface` null.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:553` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_cohort.py:470`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_synthetic_cohort`; count_sql tables: `bg_synthetic_cohort`, `bg_synthetic_cohort_md` | census CEN-R |
| live rows / floor | 110000 / 110,000 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ephemeris_engine` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 3 (every layer) (named 0 of 1 direct; the rest not identified offline) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_synthetic_cohort`: 3 non-test py/ts/tsx files reference it (2 outside brahmagyan/ and bg_*.py writers): `writer.py`, `cohort_client.py`; `bg_synthetic_cohort_md`: 4 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `writer.py`, `cohort_client.py`, `priority.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run d35590e5 complete/skip_no_delta (2026-09-07) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=10000 disagrees with live=110000 (count_sql total over 2 table(s): bg_synthetic_cohort, bg_synthetic_cohort_md; global); target_table bg_synthetic_cohort alone: 10000 row(s), whole table — context, not the compared figure |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-04): DEP-ASSERT: declared dependency(ies) not lit before run: bg_ephemeris_engine(receipt:unknown) — refused to build on incomplete/missing upstream data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run d35590e5 complete/skip_no_delta (2026-09-07) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 10000/10000 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_synthetic_cohort (bg_cohort.py:641), bg_synth…); Vocab.identity (declared key (synthetic_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (3 executed run(s) of 5 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-07); Build.registered (@register in bg_cohort.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_cohort-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_cohort-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_cohort-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_cohort-Build.history | Build | history | CF-10: a record of past errors/aborts; the latest run completed \| ledger: measured: latest run complete, but 1 error(s) and 1 abort(s) on record. DEP-ASSERT: declared dependency(ies) not lit before run: bg_ephemeris_engine(receipt:unknown) — r… |
| bg_cohort-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record rows_written=10000 disagrees with live=110000 (count_sql total over 2 table(s): bg_synthetic_cohort, bg_synthetic_cohort_md; global); target_table… |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — retained capital with named readers; the open items are build-record attribution (CF-02) and detectors. Not historical: its consumers are live code (`ka_kshetra.py`, `mi_bhara.py`).

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: build record counts one of two tables

- **Answers:** census `Build.completion` FAIL (rows_written 10,000 vs live 110,000); ledger `bg_cohort-Build.completion`; CF-02
- **Change:** the writer tracks `rows_written` (cohort) and `md_rows_written` apart (`bg_cohort.py:525-575`) and reports the first. Either report both tables in the returned counts (rows_inserted = cohort + md) or scope the registry count_sql to the target table; the writer already asserts `md = 10 × COHORT_SIZE`, so the sum is exact.
- **Files / declaration / migration:** `pipeline/orchestrator/writers/bg_cohort.py` (WriterResult return) OR the registry `count_sql` literal (migration + `asset_registry_seed.ts` row `bg_cohort`, seed L553)
- **Failing-first test and mutation:** rerun test: `rows_written` of a first build equals live count_sql (110,000) and a converged rerun equals 0 changed rows with the same live count; mutation: drop one md row → integrity/count test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** registry option: none. Writer option: needs production rebuild (110,000 rows, idempotent upsert) to write the new record
- **Gate it moves:** Build (completion)
- **Fix class:** writer code or registry/declaration; **buildable before J1:** tier-independent
- **Question for SS:** Which side (writer reports both tables, or count_sql scoped to the primary table) does SS prefer? Both close the gate.

### FD-2 · Carr detector — D3 independent re-derivation

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** two deterministic checks: (a) `sample_birth_params(n, seed)` (pure, `bg_cohort.py:259-267`) regenerates the birth parameters from the fixed seed; compare to the stored rows; (b) recompute a stratified sample of stored positions through `ephemeris_daily` for the birth date (same pinned Swiss Ephemeris, independent path) within a declared tolerance in degrees. Report mismatches; seeded corruption of one position must be caught.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_cohort.py` (`_flush_batch`, `_flush_md_batch`) for any composed text column; declare `[]` if no text column is composed (the writer stores sign/nakshatra labels and numeric fields; confirm in `_flush_batch`)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · DEP-ASSERT history on a service dependency

- **Answers:** ledger `bg_cohort-Build.history` (2026-09-04: declared dependency `bg_ephemeris_engine` receipt unknown); CF-10
- **Change:** the service `bg_ephemeris_engine` has no writer, so a build cannot light it; the saved `dep_liveness` reads PASS (1/1 lit) at present. Record in the asset’s declarations that a service dependency is satisfied by its throughput state and receipt; no code change.
- **Files / declaration / migration:** `asset_declarations.json` note (Track E)
- **Failing-first test and mutation:** dep_liveness stays PASS on a fresh census; mutation: remove the service throughput row → the cell must FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (dep_liveness)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T4-02 (assets with no table)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* build record counts 10,000 of 110,000
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 error (DEP-ASSERT, 2026-09-04) and 1 abort on record; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `synthetic_id` for `bg_synthetic_cohort`, `(synthetic_id, md_index)` for `bg_synthetic_cohort_md` (census declared key `synthetic_id`; md key to be confirmed against the DDL). Reproducibility contract: same seed → same rows. Volatile: `created_at`/build-id columns if present (not read in this pass).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the fixed seed and sampling methodology (`bg_cohort.py:60-120`), the 10,000 / 100,000 shape, the `source_citation` on every row (10,000/10,000 populated).
- **Carriage check chosen (T4 §4.1; one only):** D3 (a re-derivation of stored positions through the ephemeris, plus seed reproducibility).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Which side of the cohort count mismatch does SS want fixed (writer report or count_sql scope)?
