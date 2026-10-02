---
artifact: REVIEW_REQUEST_A2_5_V41_CANDIDATE_WRITER
version: "1.3"
author: "Stream A (Karma) — Kimi Code"
date: "2026-10-01"
subject_pr: "#2799"
reviewed_commit: f6cb3914e
authority: "Review request only; authorizes nothing. Reviews are the steward's to dispatch (PRAVAHA_EXECUTION_ARCHITECTURE §5.10)."
supersedes: "v1.2 (head 1dbb07ef6, ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER_v1_0: REJECT)"
---

# Re-review request — PR #2799 after the ASTRA v1.0 rework (PUSH 1–3)

**Head under review:** `f6cb3914e` (branch `pravaha/a25-v41-candidate-writer`). Three rework
commits answer all ten ASTRA v1.0 findings:

| Commit | Findings |
|---|---|
| `27de72476` PUSH 1 | A1 (runner types), A6 (CLI exit 6), A8 (dry_run) |
| `0664ead07` PUSH 2 | A2 (half-open horizon), A5 (ephemeris resolution) |
| `f6cb3914e` PUSH 3 | A3 (source closure), A4 (teardown), A7 (earned PG evidence), A9 (cockpit exclusion), A10 (timeout) |

This document is the amendment-by-amendment response to ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER_v1_0.

## A1 · P1 — runner's actual input types (rank 1)

- `_require_pinned_chart` compares the canonical string form: the runner's `UUID` and the CLI's
  string both accepted (`test_chart_guard_accepts_the_runners_uuid_and_the_clis_string`,
  `test_plan_and_refusal_behave_identically_for_uuid_chart`).
- The whole injected chain is row-shape agnostic: `ledger._scalar` / `_manifest_row` normalise
  dict-row and tuple-row; every positional access removed (`test_ledger_manifest_path_accepts_dict_rows`,
  `test_ledger_write_and_publish_paths_accept_dict_rows`, `test_step06b_fetchers_accept_dict_rows`).
- **Earned on real PG (A7):** the manifest substep runs end-to-end on a `dict_row` connection with
  `chart_id` as a `uuid.UUID` (`test_manifest_substep_real_pg_native_types_gate_green`).

## A2 · P1 — half-open horizon enforced (rank 2)

- Writer-side: `_validate_windows_within_horizon` refuses `window_start >= 2026-04-18`,
  `window_end > 2026-04-18`, and `peak_date` outside its own span or the half-open domain, BEFORE
  any DML (`test_validator_refuses_a_day_row_on_the_excluded_end_date`,
  `test_validator_refuses_a_peak_on_the_excluded_end_date`,
  `test_validator_admits_a_window_ending_exactly_at_the_limit`,
  `test_validator_refuses_a_peak_outside_its_own_span`).
- Contact-side: `_validate_episodes_within_horizon` runs after enumeration and BEFORE contact DML
  (`t_in`/`t_out` within `[start, end]`, `t_exact` strictly inside).
- Producer-side: `episodes.py` boundary membership is half-open and exact at the boundary
  (`test_episode_backstop_half_open`, `test_boundary_membership_is_half_open_and_exact` — a contact
  at `1997-12-31T23:59:59.999960Z` is rejected, a contact at `2026-04-18T00:00:00Z` exact rejected,
  the inclusive start retained); the projection never samples the excluded end
  (`test_projection_series_never_samples_the_excluded_end`).

## A3 · P1 — complete executable source closure (rank 3)

- The writer declares `source_paths`: its own module + the four importlib-by-path step06 modules +
  `gochara_kernel/ledger.py` + `gochara_kernel/legacy_semantics.py`; the hasher extends each root
  through static local imports.
- Proofs: the closure covers every dynamically loaded module
  (`test_writer_source_closure_covers_dynamically_loaded_modules`); it is strictly larger than the
  reviewer's 35-file run and a perturbation of a dynamically loaded module changes the digest
  (`test_writer_source_closure_digest_covers_the_closure`).
- Digests regenerated (`provenance_inventory`): exactly four writers move —
  `ka_gochara_v4_41_candidate` (approved_intentional_change) and
  `ka_gochara_v3_century_materialize` / `ka_moorti_nirnaya` / `ka_sangam` (derived_import_change
  via `episodes.py` only — verified per-writer from `asset_runner._writer_source_files` closures;
  no own-module edits). `ka_gochara`, `ka_vedha_gochara`, `ka_gochara_resonance`, all other layers:
  byte-unchanged.
- **Re-admission:** the D-PINS-A2.5 successor `l3:639eece63be3:df2b966b1d97` no longer matches
  source by construction of this fix. Stream A has **not** self-admitted: authority requested from
  the steward (`M20261001T101549-2180`), mechanics ready (generator `AUTHORIZED_SOURCE_COMMITS`
  entry, ONE append-only L3 successor archiving the D-PINS-A2.5 pin whole, census
  `--source-revision`, receipts test re-base) — the #2793 D-PINS-A2-continuation precedent.

## A4 · P1 — transactional, chart/run-scoped teardown (rank 4)

`dispatch_a25_v41_candidate_job.py --teardown`: ONE transaction, fail-closed. Refuses (nothing
deleted) when (a) a `published` '4.1' manifest exists for the pinned chart, (b)
`kala_gochara_authority` names '4.1' for the chart (serving), or (c) a `planned`/`running`/`paused`
build_run exists for the asset on the chart. Then deletes build bookkeeping (run-scoped) and the
candidate rows pinned chart × '4.1' only — never another chart's '4.1', never 'v1'/'3.0'.
Tests: `test_teardown_refuses_a_published_generation`, `test_teardown_refuses_a_serving_generation`,
`test_teardown_refuses_an_active_run`, `test_teardown_deletes_chart_scoped_in_one_transaction`
(every DELETE's SQL asserted chart- and generation-scoped; one commit), `test_teardown_flag_dispatches_to_teardown`.

## A5 · P1 — ephemeris from the image's supported configuration (rank 5)

`resolve_ephe_path`: `ctx.config["ephe_path"]` → `$SWE_EPHE_PATH` (the pipeline image's own
setting, `/app/ephe` per Dockerfile.pipeline) → dev-checkout default. Proofs:
`test_resolve_ephe_path_order` (all three branches) and `test_swieph_backend_through_the_resolved_path`
(a real knot-sampling probe through the resolved path returns backend `swieph`).

## A6 · P1 — exit code 6 restored (rank 6)

The CLI handler catches the exception class from the SAME ledger module instance the core raises
(single `_load_ledger()` per process). Earned comparison: `test_cli_published_refusal_exit6_baseline_vs_refactored`
executes the merge-base CLI and the refactored CLI as subprocesses against the same
published-manifest recording connection and asserts identical exit code 6 and REFUSED output —
not a source-string grep.

## A7 · P1 — earned integration evidence (rank 7)

New `tests/l3/gochara/test_a25_v41_candidate_writer_pg.py` (5 tests), run against the disposable
remainder Postgres (port 55434, `GOCHARA_REMAINDER_DSN`; NOT_RUN-skip when unreachable, never a
fallback):

1. **Native types, real gate:** manifest substep on `dict_row` + UUID chart with the §12.9
   freshness gate genuinely green — real `bg_transit_rules` / `bg_vedha_malefic_scale` /
   `bg_transit_moorti` seeds, overlay rows fingerprinted by the writers' own fetch path. Rerun
   replaces the manifest in place (one row, same `manifest_id`).
2. **dry_run** issues no DML on a real connection (A8, DB-verified).
3. **Interrupted substep / retry, sibling preservation:** committed siblings (another chart's
   '4.1', this chart's '3.0', this chart's other body) survive a mid-substep crash (transaction
   rollback) and a savepoint rollback; the retried body substep replaces exactly
   chart × '4.1' × body — SQL-counted, contact-id-set-compared, no duplicates, no sibling loss.
4. **Lifecycle refusal on real rows:** published manifest → `PublishedGenerationRefusal`; row set
   byte-identical afterwards.
5. **Real generation trigger:** migration 1071 applied from its file; 'v1' DELETE/UPDATE refused
   (BUILD-PROTECTED), '4.1' passes.

The WP10 suite was executed against the same instance: **15 passed**, including
`test_step03_guard_blocks_protected_generations` (the '3.0' trigger the review noted was never
run). Three WP10 failures remain — **pre-existing on origin/main** (verified by running the same
suite from a pristine `origin/main` worktree against the same instance; see "Pre-existing findings"
below), one of which this PR fixes.

Actual planner routes: `src/app/api/cockpit/plan/__tests__/route.inactive-assets.test.ts` invokes
the real `POST` handler with a mocked db layer honouring the SQL predicate (A9). Runner manifest
validation: `test_dispatch_frozen_manifest_shape_for_this_asset` (the helper's output through
`runner.validate_frozen_run_manifest`).

## A8 · P2 — dry_run honoured (rank 8)

`run_substep` gates on `ctx.dry_run` BEFORE any DML — one gate covering the inherited `run()` and
direct `run_substep()` (`test_dry_run_suppresses_every_dml_path` on fakes;
`test_manifest_substep_dry_run_issues_no_dml` on real PG).

## A9 · P2 — inactive assets excluded from cockpit planning (rank 9)

`/api/cockpit/plan`'s registry query now reads `WHERE (has_writer = true AND is_active = true) OR …`
— the same predicate `runPreparation.ts` applies (`WHERE is_active = true`), asserted against both
real sources so the surfaces cannot drift apart again. Route-level test: an inactive has_writer
asset never reaches `plan_waves`; an active one still does.

## A10 · P2 — timeout alignment (rank 10)

- Seed carries `writer_timeout_seconds: 7200` (matching the dispatch's budget).
- Dispatch validates the LANDED registry row field by field after the `ON CONFLICT DO NOTHING`
  insert and refuses a non-conforming pre-existing row BEFORE the `is_active` flip
  (`test_dispatch_refuses_a_preexisting_row_with_wrong_timeout`: no flip, no staging, no commit).
- TS inertness test asserts the seed's timeout is 7200.

## Pre-existing findings (recorded for the L0/WP10 owner; NOT introduced by this PR)

1. **step06b CLI `sys.path` defect (FIXED here).** The lazy `services.*` evaluator imports
   (`ka_vedha_gochara.gate` et al.) crash the standalone CLI with `ModuleNotFoundError` — the
   sidecar root was only on `sys.path` in-process. Reproduced on pristine `origin/main`; fixed in
   PUSH 3 by a guarded import-time insert.
2. **WP10 rehearsal drift (NOT fixed here).** `test_step07_flip_gates` / `test_step08_flip_and_reverse`
   / `test_clear_windows_on_reversal_refusals` fail on main and on this branch alike: the
   rehearsal-synthetic class context's static permission (0.26, `static_systems_active`) admits no
   era window post-T0-6, so `step06b --rehearse-synthetic` writes 0 '4.0' rows and the
   `windows_present` flip gate is red. Fixture/semantics drift from the Tier 0-S repairs (#2769),
   invisible in CI (the suite NOT_RUN-skips without the disposable DB). Repair belongs to the WP10
   rehearsal owner; recorded here so it is never silently absorbed.

## Verification totals on `f6cb3914e`

- `tests/l3/gochara`: **610 passed, 65 skipped, 9 xfailed** (incl. 5 new PG-integration tests;
  only the 3 pre-existing WP10 failures above, DB-present).
- `pipeline/orchestrator`: **1179 passed, 67 skipped**.
- `tests/l3/gochara/test_a25_v41_candidate_writer.py`: 56 passed (fake-conn unit suite).
- vitest: `a25_v41_candidate_inert` (4), `route.inactive-assets` (3), `asset_registry_seed_dag_parity` (12) — green.
- `tsc --noEmit` clean; ESLint clean on all touched TS files.

## What is NOT in this push

No dispatch, no production write, no flip, no pins self-admission (steward authority requested,
`M20261001T101549-2180`). Push of `f6cb3914e` to the PR branch was blocked at authoring time by a
locked macOS keychain on the build host (`M20261001T101836-1622`); the commit lands on the PR the
moment credentials are restored.
