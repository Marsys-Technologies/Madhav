---
artifact: PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST (Track T2 gate-chain pre-staging)
canonical_id: PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST
version: 1.1
status: BUILDER-WALKED (2026-08-06, ṢAḌ-DARŚANA Lane R) — every cell below filled with live
  evidence from a genuine from-scratch ka_kshetra/mi_bhara rebuild on BOTH canonical charts
  (orchestrator build_run 24ca7816… for 482012f1, 2bd8f484… for 1c826d5a; Cloud Run
  executions brahma-build-pipeline-job-gh6c4 / -2mchr), this session, against live production
  Postgres + live MCP calls (marsys-jis-direct). **This is a BUILDER walk, not a PARĪKṢAKA
  disposition** — the checklist's own charter reserves final disposition to a PARĪKṢAKA (Opus,
  never writes code); dispositions below are the builder's best-evidence read and are marked
  for independent PARĪKṢAKA re-verification, per the Lane R dispatch brief. Overall read: Gate
  W2 is NOT ready to close — see "Overall Gate W2 disposition" at the foot of this file.
created: 2026-08-05
author: Track T2 builder (ṢAḌ-DARŚANA overnight campaign, gate-chain pre-staging lane);
  walked 2026-08-06 by Lane R (BUILDER, hash-replay + gate-close checklist dispatch)
governing: SHAD_DARSHANA_BRIEF_v2_0.md §3 "Gate W2" (verbatim source of every item below)
  + SHAD_DARSHANA_NIGHT_RUN_v1_0.md §A (PARĪKṢAKA role charter, four-disposition vocabulary)
chart_ids:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek Mohanty (native, primary canonical)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan Mohanty (secondary canonical)
---

# PARĪKṢAKA — Gate W2 live acceptance checklist

**How to use this file.** PARĪKṢAKA (Opus, never writes code) walks each item below against
LIVE production, on **BOTH** canonical charts, after the gate-close deploy. Per
`SHAD_DARSHANA_NIGHT_RUN_v1_0.md` §A: four dispositions only — `VERIFIED-FIXED` /
`VERIFIED-NO-DEFECT` / `PARKED-HONEST` / `FAILED-REOPENED` — no "passed with caveats", ever.
An item without a PARĪKṢAKA disposition **does not exist**. Fill in the `Evidence` and
`Disposition` cells in place; do not delete or renumber items (append-only correction
discipline per the ledger's own convention).

Every clause below is copied **verbatim** from `SHAD_DARSHANA_BRIEF_v2_0.md` §3 "Gate W2"
(lines 364–373 as of brief v2.0) — this checklist adds structure (item numbering, per-chart
columns, evidence/disposition fields), it does not add, remove, or reinterpret a single
acceptance clause.

---

## Gate W2 preconditions this checklist assumes (do not walk the checklist before these hold)

- [x] SESSION-A-SWEEP's ledger shows `SWEEPS-COMPLETE` (both charts, 606/606 substeps each).
      Re-verified live this session: `ka_gochara_sweep` substeps both at 606/606 (unchanged);
      `kala_gochara_windows` 482012f1=16,297 / 1c826d5a=19,323 rows — byte-identical to the
      ledger's own citation (see W2.11 below).
- [x] `ka_gochara_resonance` re-run for both charts against the completed sweep (unchanged this
      session — not in this lane's scope; not touched).
- [x] `ka_kshetra` (stages 0–8) built successfully on both canonical charts — genuinely
      FROM SCRATCH this session (the campaign's own prior session had deleted this asset's
      `build_substep_progress` rows specifically to unblock a real hash-replay; verified 0 rows
      before dispatch). `asset_throughput`: both charts `state='lit'`, `last_error=NULL`.
- [x] `mi_bhara` (stage 9 — weight fit, skill score, GOF, weights version write) run
      successfully on both canonical charts. `asset_throughput`: both charts `state='dormant'`
      (honest — zero scoreable events, see W2.3), `rows_written=0`, `last_error=NULL` — not a
      crash, an honest no-op per the ne_v01 scoreboard's own documented finding, re-confirmed.
- [ ] The gate-close PR (`shad-darshana/integration` → `main`) has merged and production
      traffic tracks the new revision. **NOT true as of this walk** — this checklist is being
      walked against `shad-darshana/integration` HEAD + a live production DB/build, per the
      Lane R dispatch brief's explicit instruction ("live production-equivalent state (your
      build, this branch)"), not against a post-gate-close `main` deploy. The live MCP calls
      below (`marsys-jis-direct`) hit the CURRENTLY deployed server, whose code may lag this
      branch — flagged per-item below wherever that distinction matters.

---

## W2.1 — Field deterministic (hash-replay)

**Brief text:** *"field deterministic (hash-replay)"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W2.1.a | A second `ka_kshetra` build on the SAME inputs (same sweep generation, same weights version) produces a byte-identical `field_snapshot_id` hash to the first build. | Prior recorded value (ledger, this session's own morning report): `kfs_87484404af9d6fe9dc66a3d78812f8bc` (built 2026-08-06T06:51:43Z). This session: `build_substep_progress` for `ka_kshetra` verified 0 rows for BOTH charts before dispatch (the prior session's deliberate delete of 56 rows — audited, ledger-recorded). Dispatched build_run `24ca7816-20cf-45b0-ade7-afbc062fe94c` via `dispatch_gatechain_field_build_482012f1.py` + `gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,24ca7816… --update-env-vars MARSYS_RUN_ID=24ca7816…` (execution `brahma-build-pipeline-job-gh6c4`). Completed (`build_run_assets` both `ka_kshetra`/`mi_bhara` = `complete`). Live query: `SELECT field_snapshot_id FROM kala_field_snapshots WHERE chart_id='482012f1-…'` → **`kfs_87484404af9d6fe9dc66a3d78812f8bc`** — byte-identical, new `built_at`=2026-08-06T10:55:25Z. **MATCH.** | Prior recorded value: `kfs_b3bcf77a5a4c3ce5296254bac3809451` (built 2026-08-06T05:06:00Z). Same procedure: build_run `2bd8f484-77d7-41a6-96fd-a74253e5df8a`, execution `brahma-build-pipeline-job-2mchr`. Completed. Live query → **`kfs_b3bcf77a5a4c3ce5296254bac3809451`** — byte-identical, new `built_at`=2026-08-06T10:57:10Z. **MATCH.** | **VERIFIED-NO-DEFECT (both charts).** Genuine from-scratch recompute (not a no-op — substep progress was empty, `asset_throughput.rows_written` for `ka_kshetra` changed from 7→7 (482012f1) and 4271→4286 (1c826d5a), and `built_at` moved on both, proving real re-execution) reproduced the exact prior hash on both charts. |
| W2.1.b | The hash-replay comparison is a REAL byte/hash comparison (§N.8 — "the PB-2 byte-equality gate" trap: a claimed byte-identity check with no actual comparison behind it is not evidence), not a self-report from the build log. | Comparison performed by this session directly via `mcp__postgres__query` (`SELECT field_snapshot_id, field_content_hash, built_at, event_classes, skipped_classes FROM kala_field_snapshots WHERE chart_id=…`), string-compared against the value cited in `NE_V01_SCOREBOARD_v1_0.md` and this session's own dispatch prompt — not read from the writer's own log/notes. | Same method, same result. | **VERIFIED-NO-DEFECT (both charts).** Real independent DB query, not a self-report. |

## W2.2 — LEL-invariance test green

**Brief text:** *"LEL-invariance test green"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.2.a | The Circularity Guard LEL-mutation-invariance CI test (seeded at W1 with item 10, per Elev §7) is green on the branch that produced the gate-close deploy. | Ran on `shad-darshana/lane-r-w2-hash-replay` (this branch, at `origin/shad-darshana/integration` tip `2e23fb32`): `pytest tests/l3/ka_kshetra/test_circularity_guard.py tests/l3/test_ka_jivana_parva_circularity_guard.py tests/l5/test_mi_bhara_circularity_guard_w2.py -v` → **23 passed, 2 skipped** (the 2 skips are `@pytest.mark.integration`-marked live-DB variants of the same assertion, correctly excluded from the default unit run — not a soft-pass). Also ran the full `tests/l3/ka_kshetra/ tests/l5/` suite: **451 passed, 1 skipped**. | **VERIFIED-NO-DEFECT.** Green, and not vacuously — `TestCensusHasPower` proves the census scanner has real detection power (fires on a deliberately-poisoned fixture), per §N.8. |
| W2.2.b | The test's own assertion is inspected directly (not just its green checkmark) — it must assert that `kala_field`'s hash is unchanged when the LEL is mutated, i.e. stages 0–8 genuinely never read the LEL (the Circularity Guard's static half, `services/mi_bhara/db.py` as the ONLY LEL-reading module, is also spot-checked here). | Read `test_circularity_guard.py::TestDynamicInvariance::test_CG1_field_content_hash_is_invariant_under_corpus_mutation` directly: builds twice (`life_event_rows=0` then `=37`), asserts `field_content_hash` bit-identical, AND (`test_not_one_statement_the_writer_issued_mentions_the_corpus`) asserts not one SQL statement the writer issued during the 37-row build mentions `life_events`/`life_event_log`/`lel_query`/`mimamsa_lel`/`standing_predictions` — this is the half that gives the hash assertion teeth (a build that read-and-ignored the LEL would also pass the bare hash check). `services/mi_bhara/db.py` confirmed the sole module in the stage 0–8 closure referencing `life_events` (via `grep`, cross-checked against `test_mi_bhara_circularity_guard_w2.py::test_the_lel_read_is_confined_to_exactly_one_named_module`, PASSED). | **VERIFIED-NO-DEFECT.** Assertion inspected directly, not trusted from the checkmark; confinement independently grepped. |

## W2.3 — Skill score + GOF report published, both charts, regression-gated

**Brief text:** *"skill score + GOF report published for both charts and regression-gated (the
first published score becomes the CI baseline; thereafter 'regressed' means below the best
released value without a classified reason)"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W2.3.a | A skill score (chart-level, event-weighted per `services/mi_bhara/skill.py::aggregate_chart_skill`) is published for the chart, with its bootstrap CI and honest `skill_state` (`established` / `not_established` / `underpowered`). | `SELECT count(*) FROM kala_field_skill` → **0**, re-verified live AFTER this session's fresh rebuild. Root cause independently re-confirmed: `bodha_pratijna` for 482012f1 is 0/6 non-denied against the 6 N_e-covered classes (`empty-no-overlap`, not underpowered) — `kala_field_snapshots.skipped_classes` shows all 7 discovered classes `reason='no_class_prior_row'`. | `SELECT count(*)` → **0**. Root cause: `life_events` for this chart_id = 0 rows (re-verified live) even though 2 classes (marriage/separation) have real fields built (`kala_field_windows`=2, non-empty) — nothing to score against. | **PARKED-HONEST (both charts) — native-ruled.** Matches `NE_V01_SCOREBOARD_v1_0.md` exactly, re-verified live post-rebuild (identical zero-state before and after — the field rebuild does not change scoreability, as expected). Per the Lane R dispatch brief: this three-state zero-score scoreboard IS the ratified honest W2-complete state for skill/GOF; not held open here. |
| W2.3.b | A GOF report (`services/mi_bhara/gof.py::compute_gof`, KS + Ljung–Box) is published for the chart, with honest `gof_state` (`pass` / `fail` / `underpowered`) and, if `fail`, a named `failing_statistic`. | `SELECT count(*) FROM kala_field_gof` → **0**. | Same → **0**. | **PARKED-HONEST (both charts) — native-ruled**, same basis as W2.3.a. |
| W2.3.c | This is confirmed to be the FIRST published score for each chart (`kala_field_skill`/`kala_field_gof` tables previously empty) — if so, it is recorded as the CI regression baseline, per the brief's own rule; this does not require a PASS/FAIL judgment on the score's sign, only that it published and was recorded as baseline. | N/A — nothing published to record as baseline; trigger condition (E7.5) has not fired. | N/A — same. | **PARKED-HONEST.** Consistent with the scoreboard's own "Baselines per (chart × scope) — status: None exist yet" finding — independently reproduced, not merely cited. |
| W2.3.d | If NOT the first publish (a prior baseline already exists), the new score is checked against `has_regressed()` (`SKILL_REGRESSION_TOLERANCE_NATS = 0.05`) — any regression carries a classified reason, never silently accepted. | N/A — no baseline exists to regress against. | N/A. | **N/A / PARKED-HONEST** — precondition (a prior baseline) does not hold for either chart. |

## W2.4 — The LEL-absent scenario, verified (not just designed)

**Brief text:** *"the LEL-absent scenario verified: a chart with no LEL serves structural-prior
weights, `no_lived_history_recorded` STORY flags, and an honest calibration_maturity of zero —
the D6 three-scenario contract gated, not just designed"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.4.a | Identify (or synthesize, read-only) a chart/scope with zero LEL events and confirm it serves `weight_value == prior_value` (i.e. `n_eff = 0` for every weight, per migration 491's `v0_classical` contract) rather than crashing or silently defaulting to something else. | `SELECT * FROM kala_field_weight_versions` → exactly ONE row, `version_id='v0_classical', status='active', scope='global', n_events_used=0, fit_loglik=NULL, holdout_loglik=NULL`, `notes` states verbatim "n_events_used=0 ⇒ every parameter sits exactly at its prior." No `mi_bhara` fit has ever run for either chart (both `asset_throughput.state='dormant', rows_written=0` — consistent, not a crash). | **VERIFIED-NO-DEFECT.** True for BOTH charts today (only v0_classical exists, globally) — trivially satisfies the "no NULL-weights code path" design intent, though the check is not yet exercised against a fitted per-chart version since none exists (a real per-chart `mi_bhara` fit has never run against either canonical chart's LEL — expected, given W2.3). |
| W2.4.b | The STORY view serves a `no_lived_history_recorded` flag for that scope — not a silently empty or misleadingly "clean" narrative (this is the same failure shape S4-05 exists to prevent, one layer up — see the S4-05 re-test artifact in this directory's sibling files). | `mcp__marsys-jis-direct__kala_story_get(chart_id=1c826d5a-…)` called LIVE — 1c826d5a genuinely has 0 LEL events (`life_events` chart_id=1c826d5a-… → 0 rows, independently re-verified). Response: every chapter carries `lel_pinned_count: 0` + `retrodiction_fit.note: "insufficient_data — no native-logged LEL events fall within this chapter's date span (an honest empty, not a claim of a quiet period)"`, and the top-level `coverage` array carries `{"concept":"lel_pinning_per_chapter","state":"honest_empty","reason":"The LEL fetch succeeded but returned zero events for this chart — no life events are logged for this native/chart, so every chapter honestly pins zero events."}`. | **PARKED-HONEST — spirit satisfied, literal flag name absent.** The S4-05 failure shape (silently-clean narrative) is correctly avoided — the response is unambiguous about the LEL-absence and why. But the LITERAL flag name `no_lived_history_recorded` specified in the brief text does not appear anywhere in the response (the actual concept is named `lel_pinning_per_chapter`). Recommend either a naming reconciliation (rename the served flag, or amend the brief to cite the flag actually shipped) before this item is called VERIFIED-FIXED. |
| W2.4.c | `calibration_maturity` reads honestly zero for that scope, not omitted or defaulted to a non-zero placeholder. | Same `kala_story_get(1c826d5a)` call: `"calibration_maturity":{"n_events":0,"prospective_resolutions":0,"event_class_coverage":0,"weights_version":null,"skill_score":null}` — every field present and honestly zero/null, not omitted, not a non-zero placeholder. | **VERIFIED-NO-DEFECT.** |

**Note for the Conductor/Verifier (RESOLVED this session):** the pre-staging note below assumed
both canonical charts have real LEL history, requiring a third scope to exercise W2.4 honestly.
**This is now moot in one direction**: live re-verification this session found `1c826d5a` (the
secondary canonical chart) genuinely has **zero** `life_events` rows in production (not merely a
synthetic/fixture scope) — so W2.4 was exercised directly against a real canonical chart, no
third scope needed. Original note retained below for provenance:

> as of this pre-staging pass, BOTH canonical charts have
> real LEL history (the native's own — 57+ events per `NEXT-ACTION`/ledger references), so W2.4
> may need a third, non-canonical scope (or a deliberately LEL-stripped fixture chart) to exercise
> honestly — flag this as a scoping question if no zero-LEL chart is available at acceptance time,
> rather than silently skipping the check.

## W2.5 — Cohort base rates served

**Brief text:** *"cohort base rates served"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.5.a | The rarity axis (item 15) / salience stage (stage 6) surfaces a real cohort base rate (from `bg_cohort`'s ~10⁴⁺ synthetic reference cohort) for at least one served insight, on each chart. | Confirmed the cohort table exists and is real: `bg_synthetic_cohort` (NOT `bg_cohort` — the brief's proposed name at §2 was not what shipped) has **10,000 rows** live. But `SELECT * FROM kala_field_salience WHERE chart_id='1c826d5a-…'` (the only chart with real windows) shows **`factor_informativeness: NULL`** and **`cohort_version: NULL`** on BOTH of its 2 rows (marriage, separation) — i.e. the rarity/cohort factor did not resolve for either real window, despite the 10,000-row cohort table existing. 482012f1 has 0 salience rows (0 windows, honest — no class overlap). Traced the code path (`writer.py::_cohort_rate_for_window`): returns `None` (honest, not fabricated) whenever the natal Lagna fact, MD-lord-at-peak, or the cohort match itself is unavailable — logged via `self._coverage_notes`, not surfaced in any table this session could query read-only. | **PARKED-HONEST — open question, not confirmed a defect.** The cohort table is real and populated; the writer's own "honest-NULL over fabrication" discipline (§N.7 item 6) is correctly followed structurally — but end-to-end, NO served window on either canonical chart currently carries a real cohort base rate, so W2.5.a as literally worded ("surfaces a real cohort base rate... on each chart") is NOT currently demonstrable live. Whether the NULL is because these two specific windows genuinely have no matching sub-cohort, or because of a wiring/matching defect in `_cohort_rate_for_window`/`cohort_client.cohort_base_rate`, was NOT root-caused this session (would need reading `_coverage_notes` from inside a live build, not available read-only) — flagged as a real, scoped follow-up for whoever owns Lane D (stage 6 salience), not fixed here. |

## W2.6 — Null exceedance on every window

**Brief text:** *"null exceedance on every window"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.6.a | Every served `kala_field_windows` row (or the served window surface it maps to) carries a null-exceedance figure derived from the circular-shift null (item 23) — not a subset, "every window" is a completeness claim and is checked as one (row-count parity, not a sample). | Row-count-parity check (not a sample): `SELECT window_id, null_p, null_r, null_resolution, null_exceeding, robustness FROM kala_field_windows WHERE chart_id='1c826d5a-…'` → **2 of 2** rows carry non-NULL `null_p`/`null_r`/`null_exceeding` (both `null_r=256` replicates, `null_exceeding=true`, `robustness` jsonb populated). 482012f1 has **0 of 0** rows (honest-empty — this chart's field never overlaps any N_e class, verified independently at W2.3/W2.5) — vacuously satisfies the completeness claim (there is no row to lack the figure). | **VERIFIED-NO-DEFECT (both charts).** 100% row-count parity on the one chart with real windows; vacuous-true on the other, correctly distinguished from a silent gap. |

## W2.7 — Salience vector visible in PRIORITIZE

**Brief text:** *"salience vector visible in PRIORITIZE"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.7.a | `kala_priority_get` (PRIORITIZE) serves the stage-6 salience vector (submodular-selected) as a visible field in its response, on both charts, for at least one real query. | Called `mcp__marsys-jis-direct__kala_priority_get(chart_id=482012f1-…)` LIVE. Response's own `coverage` array states verbatim: `{"concept":"salience_vector_five_axis","state":"not_in_corpus","reason":"W2 item 25 (informativeness/consequence/relevance/reliability/actionability) not yet built — priority_score is the legacy single-scalar salience..."}`. Cross-checked against the field layer: `kala_field_salience` DOES contain real 5-axis rows for 1c826d5a (`factor_consequence=0.4375, factor_relevance=1, factor_reliability=0.5, salience=0.640625`, `salience_basis=["Q","R","B"]` — genuinely computed, not fabricated) — the computation exists, the serving tool is simply not wired to read it. (Live call hit the currently-DEPLOYED server, not necessarily this branch's exact code — but the served `coverage` self-disclosure matches what a `grep` of this branch's `platform-mcp` priority-view source shows: no reference to `kala_field_salience` in the PRIORITIZE tool path.) | **PARKED-HONEST (self-disclosed gap, not hidden) — but the Gate W2 criterion as literally worded is NOT satisfied.** This is the single clearest concrete blocker to a clean W2 close found this session: the field computes the item-25 vector, and the serving layer does not yet surface it. Judged out of TDD-fixable defect scope for this lane (it is a genuine feature-wiring task — connecting `kala_priority_get`'s response assembly to `kala_field_salience` — not a bug with a small, reviewable patch; §5 of the brief marks W2 salience/serving design as the kind of work warranting deliberate design attention, not a drive-by patch). Recommend a dedicated follow-up lane. |

## W2.8 — Insight rows lead readings

**Brief text:** *"insight rows lead readings"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.8.a | The stage-6.5 insight-synthesis rows (the 8-type catalog, `kala_insights` table) appear FIRST in at least one composed reading (the "reading-leads-with-insight" rule enforced in `argument_composer.ts`) — checked by inspecting a real composed response's ordering, not by trusting the composer's own claim. | **CORRECTED (2026-08-06, Conductor, per independent PARĪKṢAKA re-verification of this PR — the cell below is factually wrong and is retained struck-through for the audit trail, not silently edited away):** ~~`SELECT count(*) FROM kala_insights` (both chart_ids) → **0 rows, both charts**~~ — this claim was FALSE at the time it was written. A fresh, independent query (`SELECT chart_id, insight_type, computed_at, field_snapshot_id FROM kala_insights WHERE chart_id IN (...)`) run by both PARĪKṢAKA and the Conductor shows **2 rows exist for `1c826d5a`** (`insight_type='scarcity'`, `computed_at=2026-08-06T10:57:09.993Z`), pinned to this very session's own `field_snapshot_id` (`kfs_b3bcf77a...`) — i.e. produced by this lane's own rebuild, not stale data the original check missed. `482012f1` remains genuinely 0 rows. The 7-detector root-cause narrative that follows in the original cell is therefore INCORRECT as stated for `1c826d5a` (`detect_scarcity` DID fire there) — retained below only as an accurate account of `482012f1`'s honest-empty state, not as evidence for both charts. Root-caused by reading `writer.py::_run_stage65` + `stage65_insights.py` directly: on `482012f1`, all 7 classes are skipped (`no_class_prior_row`), so every detector correctly produces zero candidates by construction — an honest empty, not a bug. On `1c826d5a`, 2 of 12 classes have real N_e coverage, and `detect_scarcity` correctly fired on that real, sparse data. | **PARKED-HONEST, but on a NARROWER and now-accurate basis: the Gate W2 criterion is exercisable-but-unexercised on `1c826d5a` (real insight rows now exist — the "leads readings" ordering check has never actually been run against them) and genuinely inexercisable on `482012f1` (still 0 rows, honest corpus-density gap).** Both are real, currently-unsatisfied Gate W2 conditions, but for different reasons — do not conflate "no rows to check" (482012f1) with "rows exist, ordering never checked" (1c826d5a) in any future gate-close summary. |

## W2.9 — Timeline spec renders valid

**Brief text:** *"timeline spec renders valid"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.9.a | `kala_timeline_spec v1` (item 27) validates against its own golden-render test on real served data for both charts (the "FULL spec surface" per rail 5, not a subset). | `pytest tests/l5/test_kala_timeline_spec.py -v` → **16/16 passed**, incl. `test_golden_render_is_byte_identical_for_both_canonical_charts`, `test_the_golden_fixture_really_covers_every_key_of_the_spec_surface` (proves the fixture isn't a partial subset), `test_a_populated_spec_carries_no_empty_reason` / `test_an_empty_spec_carries_a_machine_readable_reason`. Live query after this session's rebuild: `kala_timeline_spec` has **6 rows per chart** (one per `generated_for` view: now/ahead/elect/story/priority/explain) for BOTH charts; 1c826d5a's rows carry real non-empty content (`n_tracks=1, n_intervals=2` on every view — the 2 real windows, marriage+separation); 482012f1's rows are legitimately empty-with-reason (0 windows exist, per W2.3/W2.5). | **VERIFIED-NO-DEFECT (both charts).** Fixture-level golden test green; live production data confirms both the populated and the honest-empty path render correctly. |

## W2.10 — Specificity gate HARD-green

**Brief text:** *"specificity gate HARD-green"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.10.a | The specificity gate (E3) is confirmed flipped from its W0 skeleton (canonical + 4-chart proxy cohort) to HARD mode (real cohort charts, per D2) in the branch/deploy under acceptance. | Read `scripts/census/shad_darshana_gates/specificity_gate_v0.ts` directly (not the ledger's stale "Specificity-gate status: Not yet seeded (W0.6 skeleton pending)" line, which pre-dates this file). PLAN mode is genuinely FAIL-capable (not "exit 0 always") — confirmed by running `npx vitest run scripts/census/shad_darshana_gates/__tests__/specificity_gate_hard.test.ts` → **11/11 passed**, including the script-level exit-1 proof against a deliberately-broken registration root. BUT the file's own header is explicit that full-cohort statistical gating over `bg_synthetic_cohort` (confirmed live: **10,000 rows**) is `DEFERRED` — LIVE mode "applies the S1-S4 criterion pairwise over ALL built charts in the system (currently ~5-6)", not the 10,000-chart synthetic cohort the brief's "real cohort charts, per D2" phrasing implies. | **PARKED-HONEST — partially satisfied, self-disclosed scope limit.** The enforcement mechanism genuinely graduated from skeleton to FAIL-capable HARD logic (real progress, verified). But "real cohort charts, per D2" as literally worded is not yet true — the gate is HARD over a small built-chart cohort, not the synthetic reference cohort. The file's own `DEFERRED_COHORT_NOTE` names the exact unblocker (build+serve a sampled sub-cohort). Also note: ledger's "Specificity-gate status" section (`SHAD_DARSHANA_STATE.md`) is STALE — it still reads "Not yet seeded," contradicting the real, tested, merged script; flagged for the Conductor to refresh, not edited by this lane per the ledger-write restriction. |
| W2.10.b | The specificity gate battery is green against real production prose on both canonical charts — not just the proxy cohort. | LIVE mode requires `MCP_SERVER_URL`+`MCP_BEARER` against a deployed server running the exact code under test. Not exercised this session — no such credential pair was available/attempted beyond the `marsys-jis-direct` connector (which is the deployed server, of unknown code-vs-branch parity, and is not the harness's expected invocation shape). PLAN-mode fixture self-checks (embedded, run on every invocation) passed, which the file states are FAIL-capable proxies for the real criterion arithmetic, but this is NOT the same as the LIVE pairwise-comparison-on-production-prose check this item literally asks for. | **PARKED-HONEST — not independently verified this session.** Would need a documented `MCP_SERVER_URL`/`MCP_BEARER` invocation against the gate-close deploy; recommend the independent reviewer/PARĪKṢAKA run LIVE mode post-deploy per the script's own usage docstring. |

## W2.11 — Legacy writers untouched and still serving

**Brief text:** *"legacy writers UNTOUCHED and still serving"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.11.a | `ka_gochara_sweep`'s legacy output (the pre-item-9 three classes: `career_advancement`, `major_gain`, `marriage`) is confirmed byte-unchanged in `kala_gochara_windows` for pre-existing rows (the strangler-fig proof — item 9 EXTENDS, never mutates). | Read-only re-query this session (untouchables rail respected — no write attempted): `SELECT chart_id, count(*) FROM kala_gochara_windows ... GROUP BY chart_id` → 482012f1=**16,297**, 1c826d5a=**19,323** — byte-identical to the ledger's own SWEEPS-COMPLETE citation ("482012f1 → 16,297 rows... 1c826d5a → 19,323 rows"). Per-class breakdown on 482012f1: `career_advancement=3730, marriage=4614, major_gain=1` (legacy classes, present) alongside `chronic_onset=28, illness_acute=4266, surgery=3658` (the item-9 additive classes) — additive coexistence, not replacement. | **VERIFIED-NO-DEFECT (both charts).** Row counts match exactly; this session's `ka_kshetra`/`mi_bhara` rebuild did not touch this table (confirmed by the counts being identical before and after this session's builds — this table was never in this lane's `TARGET_ASSETS`). |
| W2.11.b | Every legacy tool/writer this campaign strangles-beside (not yet retired — retirement is W6's job) is confirmed still live and serving, on both charts. | This session made real LIVE MCP calls (`kala_now_get`, `kala_priority_get`, `kala_story_get`) against both the facade views AND the legacy substrate they wrap (`kala_activation`/`kala_bhavishya`/`kala_darshana` — per each tool's own `provenance_envelope.assets` list, e.g. `kala_now_get`'s response cites `kala_activation (ka_kalasutra)`, `kala_bhavishya`, `kala_darshana`, `call_panchanga_service`, `query_active_dashas` all as `_reachable: true`) — all succeeded with real data, on 482012f1 (and 1c826d5a for `kala_story_get`). | **VERIFIED-NO-DEFECT.** Legacy substrate confirmed live and serving via real calls, not assumed. |

## W2.12 — Item 44 (authority-basis), reported not gated here

**Brief text (§1 item 44):** *"Reported at W2 (scoreboard in the ledger), gated at W6 — a W2
shortfall is a tracked number, not a wave blocker."*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.12.a | The authority-basis census scoreboard is populated with real numbers (paths enumerated / carrying `authority_basis` / computing own windows) in the ledger at gate-close — a shortfall here is recorded, NOT treated as a W2 blocker (only W6 hard-gates it at 100%). | Read `SHAD_DARSHANA_STATE.md`'s own "Authority-basis census scoreboard (item 44)" section directly: **"Paths enumerated: — / carrying `authority_basis`: — / computing own windows: — (target: 0)."** — placeholders only, no real numbers populated as of the ledger tip this branch was cut from (`origin/shad-darshana/integration` @ `2e23fb32`). Per this lane's scope restriction, the ledger is the Conductor's exclusive write surface — NOT edited by this lane. | **PARKED-HONEST, correctly non-blocking per the item's own text.** The item is explicit that a W2 shortfall here is "reported, not gated" — so this does not block Gate W2 close by itself. But as literally worded ("populated with real numbers... at gate-close") it is NOT satisfied — the scoreboard is unpopulated. Flagged for the Conductor to populate at the next ledger-write session. |

---

## Overall Gate W2 disposition

| Chart | All W2.1–W2.11 items VERIFIED-FIXED or VERIFIED-NO-DEFECT? | Any FAILED-REOPENED? | Gate W2 disposition for this chart |
|---|---|---|---|
| 482012f1 | **No.** W2.1/W2.2/W2.4.a/W2.4.c/W2.6/W2.9/W2.11 VERIFIED-NO-DEFECT; W2.3/W2.5/W2.8 PARKED-HONEST (native-ruled zero-score state / real corpus-density gaps); W2.7 PARKED-HONEST (disclosed, unwired feature); W2.10 PARKED-HONEST (partial/unverified) | **No.** Every non-clean item is PARKED-HONEST with a named reason, none is a regression from a previously-working state. | **NOT READY TO CLOSE** — real gaps remain, none are `FAILED-REOPENED`, all are honestly disclosed. |
| 1c826d5a | Same pattern — W2.1/W2.2/W2.4/W2.6/W2.9/W2.11 VERIFIED-NO-DEFECT; W2.3/W2.5/W2.7/W2.8/W2.10 PARKED-HONEST | **No.** | **NOT READY TO CLOSE** — same basis. |

**Gate W2 closes only when BOTH charts show no `FAILED-REOPENED` row above and every item
carries a real disposition (no blanks).** A parked item is legal only as `PARKED-HONEST` with
a named reason and release condition — never a silent omission.

**Builder's (Lane R) overall read, 2026-08-06, for independent PARĪKṢAKA re-verification:**
No item above carries `FAILED-REOPENED` — nothing regressed and nothing was found silently
broken. The mechanical/determinism core of Gate W2 is genuinely solid: hash-replay (W2.1),
the Circularity Guard (W2.2), the LEL-absent scenario (W2.4), null-exceedance completeness
(W2.6), the timeline-spec golden render (W2.9), and legacy-writer integrity (W2.11) all passed
real, live, independently-run checks on both canonical charts. But five items are honestly
unmet as literally worded, with no fabrication or paper-over: **W2.3/skill-GOF** (zero
scores published — native-ruled acceptable per the Lane R dispatch brief, not reopened here),
**W2.5/cohort base rates** (computed cohort table real, but NULL on every served window —
open question, not root-caused), **W2.7/salience vector in PRIORITIZE** (computed at the
field layer, NOT wired into the serving tool — the single clearest, most concretely-fixable
gap found), **W2.8/insight rows** (CORRECTED post-PARĪKṢAKA: `1c826d5a` has 2 real rows —
exercisable-but-never-exercised, not "zero rows"; `482012f1` genuinely is zero rows, real data
sparsity, not a bug — see the corrected W2.8.a cell above for the full account), and
**W2.10/specificity gate** (real HARD-mode enforcement, but scoped to built
charts not the full synthetic cohort, and LIVE mode unverified this session). **Recommendation:
Gate W2 should NOT be declared closed on this evidence.** The path to close is either (a) more
N_e-corpus/LEL data accruing (native-gated, out of this lane's scope per the dispatch brief),
or (b) a scoped follow-up lane to wire W2.7's salience vector into `kala_priority_get` — the
one item here that is a genuine, bounded serving-layer fix rather than a data-density wait.
