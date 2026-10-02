---
artifact: ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-01"
verdict: REJECT
reviewed_commit: 1dbb07ef6
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT.** The submitted writer cannot execute successfully with the runner’s actual context. Its horizon enforcement admits out-of-range data, its frozen digest omits the implementation it executes, and the refactor breaks an existing CLI refusal exit code.

Transaction ownership and the L3 successor’s mechanical consistency are substantially sound. Those positives do not resolve the execution and data-boundary defects below.

Review baseline: merge-base `2b3e096739b3501395a74c079846433c1bee3992`. Main-comparison results below are pinned to cached `origin/main` at `7418db50f27198ad5d74eb4a54cec06f5de799f9`.

## Findings by question

### 1. Frozen orchestrator contract and substep idempotency

**A1 — P1: The writer does not accept the runner’s actual input types.**

Two independent failures exist:

- `runner.load_run()` receives `chart_id` as a psycopg UUID and passes it unchanged into `ContextSpec`. The [chart guard](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:183) compares that UUID directly with a string. Supplying the correct chart as `UUID("482012f1-710e-4a25-994a-93821f5871aa")` raises `ChartRefusal`.
- The orchestrator connection uses `psycopg.rows.dict_row`. The injected step06 code and ledger still use tuple indexing. For example, [manifest creation](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/services/gochara_kernel/ledger.py:499) reads `fetchone()[0]` and existing manifests through `row[1]`. Dictionary-shaped probes produce `KeyError(0)` for creation and `KeyError(1)` for existing candidate/published manifests. Enumeration and projection contain further positional accesses.

Fixing only the chart comparison therefore exposes the next failure.

**A5 — P1: The default ephemeris path disagrees with the pipeline image.**

The [writer default](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:160) resolves to `/app/.run/se1` in the image. [Dockerfile.pipeline](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/Dockerfile.pipeline:15) installs the files under `/app/ephe` and sets `SWE_EPHE_PATH` accordingly. The runner supplies no `ephe_path`, and the writer ignores that environment setting. A real knot-sampling probe with the writer’s image path raised `EphemerisBackendError` after Swiss Ephemeris returned a non-SWIEPH backend.

**A8 — P2: `dry_run=True` still performs DML.**

[run_substep()](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:247) never checks `ctx.dry_run`. A recording-connection invocation of the real manifest substep with that flag set issued convention and publication INSERTs. The inherited `run()` supplies no protection.

**Transaction ownership:** I found no connection commit, full rollback, close, new connection, or `asset_throughput` write on the writer’s invoked core/ledger path. CLI lifecycle calls remain outside those cores. Nested SQL savepoint recovery does not surrender the orchestrator’s transaction ownership. `WriterResult` has the expected shape.

**Idempotency:** The replacement scopes are appropriate in source: contacts by chart/generation/body, coverage by chart/generation/body-prefixed partition, windows by chart/generation. Under the orchestrator’s savepoint handling, a failed substep should restore its deleted rows; preceding successful substeps remain committed. I found no concrete duplicate-row defect in these predicates. Actual interrupted-run/retry safety, including preservation of other bodies/charts/generations, is not established by the submitted tests.

### 2. Inertness and chart refusal

**A9 — P2: An existing cockpit planner can select the inactive asset.**

The [cockpit plan route](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/src/app/api/cockpit/plan/route.ts:48) selects `has_writer = true` without an `is_active` condition, then passes those rows to `resolveBuildPlan`. This candidate has `has_writer=true`, so it can enter preview plans.

This is a **selection/preview defect**. The inspected execution preparation and recalibration queries do filter inactive rows; I did not establish an automatic execution bypass through those routes.

The dispatch script’s TRUE→FALSE activation inside one transaction does not expose the intermediate TRUE value to another PostgreSQL session. Its success path commits only after restoring FALSE, and its exception path rolls back.

Both public writer entry paths check the chart before writer DML. Wrong charts are refused; A1 means the correct UUID-valued chart is also refused.

### 3. Candidate-only behavior and generation guards

The inspected writer call path does not call `ledger.publish()`, invoke the flip script, update serving authority, or change its generation away from `4.1`. Despite its name, `publish_candidate()` creates or refreshes a candidate manifest.

Existing published/noncandidate manifest checks provide a serial refusal path once the connection-shape defect is corrected. However:

- The new tests exercise Python refusals through a fake tuple-row connection.
- They do **not** execute the PostgreSQL generation trigger.
- The existing [WP10 trigger test](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py:334) does attempt protected-generation mutations, but I did not run it. The author’s aggregate skipped-test count does not establish that this test executed.

The documented teardown bypasses candidate-status checks entirely; see A4. Also, ordinary status SELECTs are not proof of immunity to a concurrent publication transaction.

### 4. Half-open horizon

**A2 — P1: The advertised `[1998-01-01, 2026-04-18)` boundary is not enforced.**

The [window validator](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:192) permits `window_end == 2026-04-18`, permits a point window starting on that excluded date, and does not validate `peak_date`.

Using synthetic trajectories through the **real projection**, I obtained:

| Resolution | Start | End | Peak |
|---|---|---|---|
| era | 2026-04-08 | 2026-04-18 | 2026-04-18 |
| month | 2026-04-08 | 2026-04-18 | 2026-04-18 |
| day | 2026-04-18 | 2026-04-18 | 2026-04-18 |

The writer’s validator accepted all three.

Contacts have no corresponding writer-side horizon check. The shared [boundary enumerator](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/services/gochara_kernel/episodes.py:440) uses a closed interval with floating-point slack. Actual enumeration probes produced:

- A contact exactly at the inclusive start: correctly retained.
- A contact at `1997-12-31T23:59:59.999960Z`: incorrectly retained.
- A contact at `2026-04-18T00:00:00Z`: incorrectly retained.

These were computed outputs, not hand-constructed output rows. An exclusive interval endpoint can legitimately equal the horizon limit, but an exact contact or day window on the excluded date cannot.

### 5. Standalone CLI compatibility

**A6 — P1: Published-generation refusal no longer returns exit code 6.**

[The exception handler](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:263) catches `_load_ledger().PublishedGenerationRefusal`. Each call to `_load_ledger()` creates a fresh module and a distinct exception class. The core raises the class from its earlier module instance, which the handler cannot catch.

Comparing the merge-base and submitted CLI mains against the same published-manifest recording connection:

- Merge-base: returned **6** and printed `REFUSED`.
- Submitted commit: let `PublishedGenerationRefusal` escape; standalone execution consequently exits **1** with a traceback.

The test checking that the source contains `"return 6"` passes despite this regression. The byte-identical CLI claim is false.

### 6. `bodies=None` ledger compatibility

**No regression found in the default deletion behavior.**

For both contacts and coverage, `bodies=None` retains the previous chart-and-generation DELETE predicate and the existing normalization/insertion path. The added scope validation and narrower DELETEs apply only when `bodies` is supplied.

Contacts use exact body names; coverage uses the lowercased partition prefix, consistent with the enumerator’s partition convention. The new default-scope test covers only contacts and is weaker than its “byte unchanged” title, but the diff supports behavioral equivalence for both default paths.

### 7. Dispatch manifest, active-run refusal, and teardown

The real manifest helper’s output was accepted by `runner.validate_frozen_run_manifest` in an in-memory check. The manifest version, scope, action, waves, asset entry, and canonical digest agree with the runner.

The script relies on migration 595’s partial unique index for active-run refusal. That index excludes a second `planned`/`running`/`paused` run for the same chart; an insertion conflict reaches the script’s rollback. A separate preliminary SELECT is not required for correctness. Production installation of that index was not verified.

**A4 — P1: The teardown is globally scoped and publication-blind.**

The [documented DELETEs](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/scripts/dispatch_a25_v41_candidate_job.py:48) remove every generation-`4.1` row across all charts. They do not require candidate status, check serving authority, restrict cleanup to the staged run, or provide one transactional cleanup boundary.

If another chart has `4.1`, or this generation is later published, the recipe can delete those rows. A trigger protecting `v1`/`3.0` does not prevent that.

**A10 — P2: Timeout depends on whether seed or dispatch creates the row first.**

The [seed row](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/scripts/seed/asset_registry_seed.ts:2250) omits `writer_timeout_seconds`, so the seed supplies **600**. Dispatch specifies **7200**, but `ON CONFLICT DO NOTHING` preserves the seeded value. The runner reads that registry timeout. Thus seeding first silently gives this heavy job a ten-minute budget.

### 8. Do the tests earn the claims?

**A7 — P1: The acceptance claims exceed what the tests measure.**

The isolated candidate-writer suite passed: **32 tests**, with bytecode, pytest caching, external plugins, and conftest loading disabled.

Material gaps remain:

- The connection fake returns tuples and the context uses a string chart ID, hiding A1.
- The supposed retry proof [counts one insertion from one call](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/tests/l3/gochara/test_a25_v41_candidate_writer.py:376). It neither maintains database state nor interrupts and reruns the writer.
- CLI exit tests inspect source strings instead of executing refusal paths.
- Horizon tests call the validator with constructed rows and omit the exclusive endpoint and actual producer output.
- The [inertness tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/scripts/__tests__/a25_v41_candidate_inert.test.ts:31) reproduce selected predicates instead of invoking the actual planner surfaces.
- The new TypeScript pins assertion sits inside an existing `describe.skip`.
- Some Python preservation assertions compare against a predecessor reconstructed from the submitted document itself. That does not independently establish preservation of main.

These tests have useful unit coverage, but the broader completion signals do not satisfy §N.8.

### 9. Pins admission and residual equality

**Mechanical admission checks pass for L3.**

I independently verified:

- Active successor: `l3:639eece63be3:df2b966b1d97`.
- Archived predecessor: `l3:4f4a1993c6ad:1ddd6f117934`, with its actual protected-baseline pin and writer snapshot preserved.
- Exact inventory delta: only `ka_gochara_v4_41_candidate`.
- Other layers and immutable definition bindings remain unchanged.
- Source-head and delivery-mode checking introduce no L3 failure.
- The three ordered L1/L2 residuals are **byte-identical** to the fixed main comparison. A read-only ancestry simulation restricted to main produced the same residuals.

The complete checker still reports those three inherited failures; this is not a globally green pins check.

**A3 — P1: The admitted digest does not cover the executed implementation.**

The writer [loads all four step06 modules and the ledger dynamically](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799a/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:149), without declaring `source_paths`. The frozen hasher follows static imports.

Running the actual source-closure implementation produced **35 files, zero cutover modules, and no `gochara_kernel/ledger.py`**. Its digest matches the committed digest, which demonstrates the omission rather than curing it. Those excluded implementation files can change without invalidating this writer’s expected code digest.

## Ranked merge-blocking amendments

| Rank | Finding | Required amendment |
|---:|---|---|
| 1 | **A1 · P1** | Accept the runner’s UUID and dictionary-row connection throughout the injected chain, while preserving standalone CLI compatibility. Do not alter the frozen orchestrator contract. |
| 2 | **A2 · P1** | Enforce the half-open horizon in actual contact/window production and validation. Cover start, just-before-start, exclusive end, peaks, and interval inclusivity. |
| 3 | **A3 · P1** | Declare the complete executable source closure, including dynamically loaded modules; regenerate digests/census and re-admit the resulting L3 inventory. |
| 4 | **A4 · P1** | Replace the teardown with transactional, chart/run-scoped cleanup that refuses published or serving generations and active execution. |
| 5 | **A5 · P1** | Resolve ephemeris files from the pipeline image’s supported configuration and verify the SWIEPH backend through that path. |
| 6 | **A6 · P1** | Catch the same exception class the core raises; execute baseline-versus-refactored CLI refusal and output comparisons. |
| 7 | **A7 · P1** | Add earned integration evidence: native connection types, interrupted substep/retry with sibling-row preservation, real generation triggers, actual planner routes, and actual runner manifest validation. |
| 8 | **A8 · P2** | Honor `dry_run` before every writer DML path, including inherited `run()` and direct `run_substep()`. |
| 9 | **A9 · P2** | Exclude inactive assets from cockpit planning consistently with execution preparation. |
| 10 | **A10 · P2** | Align seed and dispatch timeout configuration; validate pre-existing registry rows before staging. |

## Separate follow-ups

- Measure memory use and elapsed time for the single whole-horizon windows substep before the approximately 10M-row dispatch.
- Review serialization between candidate mutation and independent publication; status-check SELECTs alone do not establish concurrency safety.
- Correct the PR’s stale test count and “all conditions implemented”/“byte-identical” claims after the amendments.

## What I could not verify

No production or local database connection was made. I did not verify deployed image contents, installed production guards/indexes, production authority state, full-scale execution, database concurrency, or the author’s complete suite/CI totals.

No actual squash commit was created; delivery checking and ancestry simulation were performed in memory. The separate native ruling for adding this supporting-writer exception—still marked “flagged for native ruling” in source—was not established by the supplied evidence.

No file was written and no git write command was run.

