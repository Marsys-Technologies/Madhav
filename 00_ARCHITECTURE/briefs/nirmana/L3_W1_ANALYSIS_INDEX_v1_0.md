---
artifact: L3_W1_ANALYSIS_INDEX_v1_0.md
canonical_id: NIRMANA_L3_W1_ANALYSIS_INDEX
version: "1.0"
status: COMPLETE — 23/23 assets analysed; input to L3-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3 — Kāla
definition_revision: t0-2026-09-01-0e5b06fb
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
authorized_by: >
  NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §4 (W1 rubric) + §5 (L3 mandate), under
  SESSION_CHARTER_V21.md. Produced autonomously per C3; no human was consulted.
---

# L3 KĀLA — W1 ANALYZE — INDEX

**One clock, many instruments. W1's job was to find out how many instruments there actually are,
which ones anyone is listening to, and who arbitrates when they disagree.** The answers, measured:
**34** temporal engines, **10** live overlap cells where two engines can answer the same question,
and **exactly one** arbiter in existence.

## 0. Method, and what "measured" means here

Five independent read-only subagents, one per batch, each given the plan §4 eight-point rubric plus
batch-specific questions, each writing exactly one file and issuing only `SELECT`. Every number in
these documents comes from a command run during this session against live production; anything that
could not be measured is written "unmeasured" rather than estimated. Where a batch's conclusion
disagreed with its own evidence I re-derived it myself and recorded the correction (§4 below) — the
batch files are inputs to W2, not verdicts.

| batch | assets | file |
|---|---|---|
| A — the gochara lineage | `ka_gochara_resonance`, `ka_gochara`, `ka_gochara_sweep`, `ka_gochara_v3_century_materialize` | `L3_W1_ANALYSIS_BATCH_A.md` |
| B — the quality overlays | `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_sudarshana_varsha`, `ka_tithi_pravesha` | `L3_W1_ANALYSIS_BATCH_B.md` |
| C — the services | `ka_graha_sancara`, `ka_muhurta_seva`, `ka_dasha_kala`, `ka_tulana` | `L3_W1_ANALYSIS_BATCH_C.md` |
| D — the heavy core | `ka_kshetra`, `ka_avadhi`, `ka_taranga`, `ka_yojaka` | `L3_W1_ANALYSIS_BATCH_D.md` |
| E — the artifact spine | `ka_sangam`, `ka_vighnakara`, `ka_kalasutra`, `ka_kala_darshana`, `ka_jivana_parva`, `ka_bhavishya_lekha` | `L3_W1_ANALYSIS_BATCH_E.md` |

23/23. No asset was skipped, sampled, or inferred from a sibling.

## 1. The layer in one paragraph

**L3's writers are largely sound; L3's wiring is not.** Almost every defect found in this pass sits
in one of three places — the *consumer wiring* between a built table and the code meant to read it,
the *serving plane* that presents the result, or the *registry metadata* that is supposed to describe
and check it. Very few sit in a writer's arithmetic. That is a good problem to have, because wiring
and metadata are cheap to fix and do not require re-deriving any astrology. It is also a dangerous
problem to have, because every one of these defects is silent: nothing fails, nothing logs, and the
served answer looks exactly as confident as a correct one.

## 2. The five findings that shape W2

**2.1 — The E-gate is only as sound as `depends_on`, and L3's DAG is wrong in both directions.**
`ka_gochara_resonance` declares one dependency and its writer reads six tables, four of them into
unfrozen L1 (`writer.py` lines 369/375/382/389/396/412 — I read the SQL myself). Meanwhile
`ka_muhurta_seva` is held shut by an edge its own package docstring labels *"(planned)"*. Missing
edges open gates that should be shut; fictional edges shut gates that should be open. **Consequence:
L3 has zero genuinely E-gate-open assets, and both assets nominated as gate canaries are artefacts.**
Filed as **#1734**. This is the single most important thing W1 found, because it is not about any
asset — it is about whether the campaign's central gate measures anything.

**2.2 — Built, consumed, and still inert: the wiring gap is two layers deep.** The D-SERVICE
"built-but-unplugged" defect class turns out to have a worse variant at L3. For
`ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_tithi_pravesha` and `ka_sudarshana_varsha`, the table is
built *and* the consuming mechanism module is written — and the mechanisms read `ClassContext`
fields (`context.kota_*`, `context.moorti_rows`, …) **that do not exist on the dataclass**. Each
returns its honest `modifier = 1.0` on every call, on every chart, forever. Of the five overlays the
mandate asked me to verify as "consumed modulation, not shelf inventory", **exactly one
(`ka_vedha_gochara`) is consumed.** The same shape appears at the heavy core: `kala_field_windows`
holds 31,350 live rows while `kala_ritual_resonance.ts:491` unconditionally returns `not_computed`
with the reason *"field empty, ka_kshetra has written no rows"* — §N.8 inverted, a signal reporting
absence over data that is present.

**2.3 — Incommensurable scores, and the weakest evidence wins.** `kala_convergence.convergence_score`
is written by four modes on four different scales, and every consumer orders by it descending. Mode C
is `dignity_score × severity` — two catalog constants, `orb_strength` hardcoded to 1.0, zero engine
testimony — and it averages 0.7913 while the twelve-current Mode A funnel tops out at 0.3086.
Measured: top-200 is **200/200 Mode C**; `kala_darshana` is **750/750 Mode C**, and all 750 narrate
"independent sweep". The mode carrying the least agreement evidence has captured every served
surface. This is the D-SYNTHESIS failure in its purest form, and it is upstream of the arbiter — no
concordance verdict is worth anything while the scores it compares are not on one scale.

**2.4 — The arbiter is 60% built already.** `ka_sangam` computes twelve weighted currents summing to
1.0, splits them necessary-vs-supporting (which is gate-vs-corroborating), carries an
`independent_current_count` coupling discount and `cross_dasha_agreement`, and persists per-window
testimony in `constituent_factors`. What D-TIME needs on top is narrow and nameable: a **stance
vocabulary** (today every current is supporting in `[0,1]`, so a dissent and an absent engine are
both `0.0` — the system cannot say "this engine disagrees"), testimony on Modes C/D (85.8% of rows),
commensurable scales, a verdict plus `adjudicated_by`, and any read at all of the two authority
tables. `kala_paddhati_profile` is *already* a per-(chart, factor_family) authority profile carrying
`school_tag`, `constraint_role`, `convention_status` (whose `declared_not_computed` value is exactly
the silent-vs-dissent distinction `ka_sangam` lacks) and `native_confirmed`. **The Temporal
Concordance Contract is an extension of things that exist, not a new build** — which is the single
most consequential fact for W2's cost estimate.

**2.5 — Registry metadata is empty across the whole layer, and that is now a gate.** All 23 assets:
`integrity_check_sql` NULL, `expected_volume_formula` NULL, `expected_volume_inputs` NULL,
`natural_key_partition` NULL, and no non-zero `target_floor`. Because `integrity_verified` is
mandatory on every route and its detector runs SQL with no bind parameters while every L3 `count_sql`
is `$1`-bound, **no L3 asset can reach a capsule until real contracts are authored** — 19 of them
(the 4 services take the health-probe path). Ruled campaign-wide as **D-CND-03**.

## 3. Cost: the registry's estimates are not merely stale, they are the wrong order of magnitude

Measured from `build_substep_progress` deltas and build-state spans, never estimated:

| asset | registry `estimated_seconds` | measured (native chart) | ratio |
|---|---:|---:|---:|
| `ka_kshetra` | 237 | **22,685 s** (6 h 18 m, 308 substeps, 10.50 M rows) | **96×** |
| `ka_gochara_v3_century_materialize` | 614 | **3,479.7 s** (270 substeps) | 5.7× |
| `ka_kalasutra` | 33 | **486.9 s** (p50) | 14.8× |
| `ka_sangam` + spine (single chart) | ~513 implied | **≈2,251 s** | 4.4× |
| the five quality overlays | 2–4 each | 2.09–3.12 s each | ~1× ✓ |

`rows_per_second` is NULL with `measurement_count = 0` on the heavy assets — nothing has ever
recorded a measurement, which is why the estimates were never corrected. The overlays, tellingly,
are accurate: small assets got honest estimates and large ones got guesses.

**WP-4 verdict on chunk-parallelism: NO, and it is STOP-and-raise territory.** `asset_runner.py`
drives substeps serially on the single orchestrator-owned connection (`SAVEPOINT writer_exec` →
`run_substep` → `RELEASE` → commit). Parallel substeps need a second connection, which forfeits both
frozen invariants (§N.2), and the §3.5 freeze exception grants nothing in `writers/`. `ka_kshetra`'s
chunk key is `stage4:{event_class}:{decade}` (25 × 10) plus `stage5dhara` (50) ≈ 309 substeps/chart;
the century materializer's is 27 classes × 10 decades = **270**, not the manifest's "60". What *is*
tunable, and rides §3.5 legitimately as scheduling constants: LPT ordering and width in `runner.py`.
The measured hot spot is not where anyone assumed — **`stage5dhara` is 68% of `ka_kshetra`'s runtime
(15,415 s), stage4 only 24%**, and `stage8` burns 1,224 s to produce 6 rows nothing reads, with one
substep (1,210 s) already exceeding `_WRITER_TIMEOUT_SECONDS = 600`.

## 4. Corrections I made to the batch analyses

Recorded so a later reader does not re-inherit them:

1. **The v1-gochara "hard-floor alert" is downgraded.** Batch A's facts are all true (zero
   protection triggers; 38,287 v1 rows across 3 charts; the in-DB table snapshot covers only 2). Its
   conclusion is not: migration 588 removed those triggers **by native instruction (2026-08-23)**,
   because the guard was keyed on `asset_id` and permanently blocked the very writer it was meant to
   protect, and it replaced them with a full logical snapshot. That dump exists at
   `00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/` at **16,214,137 bytes —
   exactly the size the migration records** — and `pg_restore -l` reads a valid TOC containing the
   corpus table. The hard floor's condition is **satisfied**. Three residuals survive and are carried
   to W2: chart `cb73cd3d`'s 2,667 v1 rows sit outside the fast in-DB recovery path; the dump is
   git-ignored, so the only recovery path for an unregenerable corpus is one local file; and
   migration 588's own suggestion to re-key a guard on `(table, generation)` is an adjudication, not
   an L3 decision, because it would reverse something the native removed deliberately.
2. **Chart `cb73cd3d` is not deleted.** Batch A called it an orphan/deleted chart; it is present in
   `charts` (measured). It is a third real chart with un-snapshotted v1 rows, which makes residual 1
   more serious, not less.
3. **The mandate's "17,240 rows" for the v1 archive is wrong in both count and location.** Measured:
   the v1 corpus is 38,287 rows interleaved in the *live serving table* `kala_gochara_windows` under
   `generation='v1'`, not in a separate archive. 17,240 = the native chart's 16,297 v1 rows + 943
   gen-3.0 rows, i.e. a whole-table count mislabelled as an archive count.
4. **The mandate's "8.6M rows" for `ka_kshetra` is the native chart alone**, not the table: exact
   measurement 8,599,775 (native) + 2,412,882 (Abhinandan) = 11,012,657. Not growth, not accretion —
   multi-chart. Several other campaign figures are stale `reltuples` estimates (`kala_taranga`
   194,543 vs actual 277,236; `kala_activation_predicates` 100,859 vs 150,150).
5. **`ka_graha_sancara` is not stale state.** Batch C's diagnosis stands after review: two
   independent real defects, and the self-test check that would catch one of them **has never been
   green in the writer's real path** — its 19/19 passing tests feed a tuple-returning mock. C12
   applies exactly: a check that has never been green is a proposal, not a gate.

## 5. What W1 hands to W2

- **23 route recommendations**, one per asset, each with the evidence behind it.
- **A findings ledger** to triage MUST / NOW / NEVER-LATER with doctrine citations.
- **A dependency-reconciliation table**: every asset's declared `depends_on` against its writer's
  actual reads — the input to the supersession requested in #1734.
- **19 integrity-contract proposals** under D-CND-03, several already executed against live data.
- **The Temporal Concordance evidence base**: 34 engines, the 10-cell overlap matrix, both authority
  tables dumped and explained, and the precise serving attachment point (`explain.ts:571`, beside
  `weakest_link`, with `school_voices[]` becoming `engine_testimony[]`).
- **Measured costs** for every asset, replacing estimates that were wrong by up to 96×.

## 6. Standing constraints carried forward

- **SNAPSHOT RULE ABSOLUTE.** No dispatch that could write `kala_gochara_windows` without a fresh
  verified snapshot first. `ka_gochara_sweep` is never dispatched: its `@register` was removed at
  retirement, so the build system cannot regenerate those rows — the sweep would be a ~30 h per-chart
  re-run if the dump were lost.
- **`ka_kshetra` and the century materializer are solo slots, always** (C5), and at 6 h 18 m and
  58 min measured they are the campaign's real scheduling problem, not a formality.
- **No writer-contract change.** WP-4's answer on parallelism is no; the tuning lives in `runner.py`
  scheduling constants under §3.5, logged.

*End L3-W1. Next: `L3_W2_DECIDE_v1_0.md`.*
