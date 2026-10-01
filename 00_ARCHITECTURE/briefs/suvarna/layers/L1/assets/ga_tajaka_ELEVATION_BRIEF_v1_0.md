---
asset_id: ga_tajaka
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 at the base commit (7 on origin/main 066c58587: the revision note names a NA_CAUSES addition for Carr; the criterion bodies were not diffed beyond that) and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS"
track_i_items: []
ledger_gap_ids: [ga_tajaka-Idem.pattern, ga_tajaka-Earn.build_record, ga_tajaka-Cost.baseline, ga_tajaka-Build.history, ga_tajaka-Carr.detector]
---
# ga_tajaka — Vārṣaphal annual charts: Muntha, Vārṣeśa by two methods, Tājika yogas (hybrid window)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Builds the Vārṣaphal annual chart per varṣa (birthday-to-birthday solar year) into `l1_tajik_varsha_year_lords`: Muntha, Vārṣeśa by two methods with candidate scoring, and the Tājika yogas in each annual chart (`ga_writers/ga_tajaka_writer.py:1-30`). Positions: PyJHora (`compute_positions` for the solar-return root-find, `compute_chart` for the annual chart). A hard FORENSIC gate (varṣa 43, Lahiri, 2026–27: Muntha Libra / 7th / Venus) halts the build on a miss. The hybrid window is past + current + next five years relative to the **build clock**: `reference_year` defaults to `datetime.now(timezone.utc).year` (`:74-78`, `_effective_reference_year` `:726-737`; the F-E16 fix for a frozen 2026 literal).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1356` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_tajaka.py:8` (`run`, light); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `l1_tajik_varsha_year_lords` (own table; natural-key detail not read) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 240 / 240 (Δ +0); `asset_throughput` lit / 240; seed floor literal 240 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `ga_dashas`, `ga_sensitive` (live and seed) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 1; census (2026-09-30, pre-1210): direct 1 / transitive 26; seed + 1210 reconstruction names 1 direct dependent(s): `ka_sangam` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_tajik.ts:215` (declarations `read_evidence`) and `reading_checklist.ts:902`; 2 census modules, 1 declaring `density_contract`; 1 direct (L3) / 26 transitive dependents | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | annual-clock foundation (layer instance §2.4 row 3.10: Tājaka, tithi-praveśa); the only L1 asset whose latest recorded error is a Moshier-range error (`jd -0.001010 outside Moshier planet range`, 2026-07-16) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 7 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): Error: swisseph.calc_ut: jd -0.001010 outside Moshier planet range 625000.50 .. 2818000.50  Traceback (most recent call last):   File "/app/platform/python-sidecar/pipeline/o… |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 346d56e9 complete/skip_no_delta (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 346d56e9 complete/skip_no_delta (2026-09-08) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 18/18 built column(s) (100.0%) selected by 2 capability module(s); dark: []; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PASS** — STRUCTURAL: 5 module(s) reach it by code: L1_ganita/coverage_matrix.ts, L1_ganita/get_tajik.ts, reading_checklist.ts, register_d9_judgment.ts, platform-mcp/src/tools/kala_views/ahead.ts; 1 capability(ies) declare density_contract AND select a tier column from it (verification_pass_status) in: L1_ga… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PARTIAL; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PASS; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: the row set depends on the wall clock at build time | Idem/Earn | SS question | a build in 2026 writes varṣa 1..48 (48 × 5 = 240 = the floor and the live count); a build in 2027 writes 1..49 (245 rows). The orchestrator never passes `reference_year` (`:726-731`), so two builds in different years of the same chart differ by design; F-E15 recorded the floor as a "wall-clock-derived equality". This is a documented, honest choice (the earlier frozen literal was the defect) but it makes the rebuild non-reproducible across years; the fingerprint must fix the reference year |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared; composed at `ga_tajaka_writer.py:621`; offline: agree PARTIAL (reverse leg unavailable), fidelity PARTIAL (4 test files call the builder, none names `citation_human`), lint PASS; CF-15 |
| ga_tajaka-Build.history | Build | history | PARTIAL: 7 errors / 7 aborts; latest error 2026-07-16 `swisseph.calc_ut: jd -0.001010 outside Moshier planet range` (a historical range bug; the latest run completed); CF-10 |
| brief: tier literals | Earn | real | 7 quoted tier strings (indicative); CF-17 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_tajaka_writer.py:835` (direct, under `owns_conn` `:833`; import comment line 48 "legacy CLI path only; orchestrator never calls this"); CF-14 |
| ga_tajaka-Carr / Earn / Cost / Idem | Carr, Earn, Cost, Idem | detector / stale | CF-07 (D3: solar-return root-find re-derived by a second method; Muntha by the classical rule); CF-05; the Idem ledger row is stale (census PASS) |
| census: Ldgr / Complete.depth / Vocab / Dens | all | PASS | every depth cell reads PASS; Dens rev 4 reads PASS offline (one of three L1 assets that do) |

## 3 · Disposition

**keep (P)** — every applicable cell is PASS but the history record; the hard FORENSIC gate and the two-method year-lord design are in place, and the W2 MUST fix (F-E16) is on main. The remaining items are a documented clock-dependence (an SS question) and detectors.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Record or fix the reference year the window used

- **Answers:** brief gap "wall-clock window"; CLAUDE.md B.8, reproducible calculations (T1 §14)
- **Change:** either (a) keep the clock default and record the `reference_year` used on each build (a column or the build record) so a rebuild can be compared like for like and the fingerprint contract fixes it, or (b) derive the reference year from the build run's recorded creation time rather than `now()` so a rerun of a recorded build reproduces. Not a `WriterBase` change: `ctx.config` carries `chart_id`/`birth_params` only (§N.2); (b) needs a source for the year that the frozen contract already supplies, which was not found here
- **Files / declaration / migration:** `ga_writers/ga_tajaka_writer.py:726-737`; for (a) possibly one additive column (migration)
- **Failing-first test and mutation:** failing-first: two builds with the same explicit `reference_year` produce identical fingerprints; mutation: change the year and the window differs
- **Output change:** none for (b); an additive column for (a)
- **Blast radius:** L3 consumer (`ka_*`, 1 direct) reads the table
- **Rebuild:** none unless the column is added (then a small production rebuild: 240 rows, REVIEW)
- **Gate it moves:** Idem/Earn (reproducibility claim)
- **Fix class:** writer code (+ migration for (a)); **buildable before J1:** tier-independent
- **Question for SS:** Clock-dependent hybrid window as designed (record the year), or reproducible from a recorded build time?

### FD-2 · Narr golden test naming `citation_human`

- **Answers:** Narr.fidelity_test PARTIAL; CF-15
- **Change:** assert the exact sentence for the 2026–27 varṣa (Muntha Libra, 7th house, lord Venus, the FORENSIC values already in the gate) so the sentence is graded
- **Files / declaration / migration:** a test beside `test_ga_tajaka_*`
- **Failing-first test and mutation:** mutation: change the Muntha sign in the citation and the test fails
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent

### FD-3 · Carr D3 for the solar-return instant

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** re-derive the solar-return instant of a sample of varṣas by a second root-find (different bracket/flags) and compare to `varsha_start_iso` within a declared tolerance; Muntha by the classical rule from Lagna and the varṣa number
- **Files / declaration / migration:** Track E inspector tooling
- **Failing-first test and mutation:** a seeded wrong start must be reported
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-2: declared
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-3: D3
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 7/7: history
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* literals: 7 (indicative)
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:835`
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `replace_prior_tajik_varsha`: exact `(chart, ayanamsha, varsha_year)` triples being written — a shrinking window leaves old years (the 2026 → 2027 case is additive, the reverse is not)
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PASS: one of three
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* Complete/Ldgr/Vocab: own table: whole-table figures are 780 rows (all charts) vs 240 for the chart

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, varsha_year)` (`_idempotency.replace_prior_tajik_varsha`; the unique key also includes `build_id`); volatile: `build_id`, `computed_at`; **the fingerprint must fix `reference_year`** (default = the build clock year) and compare over the same `varsha_year` window, otherwise a rebuild in a later year differs by construction.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the per-varṣa annual chart with Muntha and two-method Vārṣeśa and candidate scoring, the FORENSIC Muntha gate, the sanctioned JSONB composites.
- **Carriage check chosen (T4 §4.1; one only):** D3 — the solar-return instant and Muntha re-derived a second way.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Is a clock-dependent hybrid window acceptable for an L1 correctness asset (record the reference year), or must a rebuild of a recorded build reproduce its window?
