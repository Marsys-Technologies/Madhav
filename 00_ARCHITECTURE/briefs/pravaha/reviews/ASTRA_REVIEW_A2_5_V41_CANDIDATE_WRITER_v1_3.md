---
artifact: ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER
version: "1.3"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 98864fc41
authority: "Review only; authorizes nothing."
---

**Verdict: ACCEPT_WITH_AMENDMENTS**

The original R1 interval-loss and R2 excluded-end abort counterexamples are fixed. R3’s unsound Moon success cache is removed. A1 and all seven earlier closures remain closed.

One bounded **P2 merge-blocking amendment** remains: disclose the horizon stand-in in persisted rows and the governed writer’s audit output. Currently, consumers receive an ordinary-looking peak, while the writer discards the class-report counters identifying its substitution.

Independent execution: **281 focused tests passed**. **Nine PostgreSQL cases were NOT_RUN** because the sandbox denied the disposable cluster connection. Eleven cases requiring filesystem mutation or other excluded fixtures were deselected; the CLI baseline comparison was reproduced separately in memory. These results do not establish the PR’s full-suite or PostgreSQL claims.

Source references below are relative to `platform/python-sidecar/` unless explicitly rooted elsewhere.

## Closure table

| Finding | Status | Evidence and independent rerun |
|---|---|---|
| **R1 — Final partial interval lost** | **CLOSED** | `scripts/kala_gochara_cutover/step06b_windows_projection.py:1517` preserves the component when its only above-threshold sample is the horizon limit. I reran the v1.2 geometry through actual `solve_episodes → fetch_contacts → project_class_windows → writer validator`: old projection produced zero rows; current projection produces one valid era window and `final_edge_components=1`. |
| **R2 — Refined peak at excluded end aborts writer** | **CLOSED** | Projection `:1566` substitutes an in-domain instant before constructing month/day rows. The Sun contact centred exactly on `h1` previously produced April 18 month/day peaks and `HorizonViolation`; current output preserves the era/month/day family, dates the peaks April 17, records one clamp, and passes the validator. Representation qualification remains amendment 1 below. |
| **R3 — Moon cache scope/invalidation** | **CLOSED** | `services/gochara_kernel/knots.py:119`, `:140`, `:170`: no success cache remains; every Moon call probes its own instant under the Swiss-state lock. My warmed-cache/backend-loss comparison accepted the modeled loss under old code and raised `EphemerisBackendError` under current code. Real-library coverage-boundary tests also passed. |
| **A7 — Acceptance evidence** | **PARTLY** | The earlier test-design gap is closed: `tests/l3/gochara/test_a25_final_edge_projection.py:121` reproduces R1 verbatim; `:169` covers R2; both reach the writer validator. The disposable-PG R1 path is at `:211`, alongside the existing writer/retry cases. However, nine database cases remain independently unexecuted, and no test establishes stand-in disclosure through persistence and governed-writer reporting. |
| **A1 — Runner input types** | **CLOSED** | `step06a_class_context.py:329` handles dictionary/tuple rows; projection `:1807` supplies the optional `formula_version` alias. Fresh nonempty-dictionary/UUID parser reruns passed, including `formula_version=None`. The full real-PG writer test remains unexecuted here. |
| **A3 — Executable source closure** | **CLOSED** | Writer `ka_gochara_v4_41_candidate.py:308` retains the dynamic roots. The actual hasher finds **62 files**, matches the committed `f27c2801c62c…` digest, and passes executable mutation-sensitivity testing. |
| **A4 — Teardown scope/refusals** | **CLOSED** | `platform/scripts/dispatch_a25_v41_candidate_job.py:185` scopes deletion; `:213`, `:227`, `:241` retain published/serving/active-run refusals. Recording-connection tests passed. Transaction concurrency remains separate. |
| **A5 — Ephemeris path** | **CLOSED** | Writer `:168` retains explicit configuration → `SWE_EPHE_PATH` → development fallback. Resolution-order and real-library tests passed; deployed-image contents were not verified. |
| **A6 — CLI refusal exit code** | **CLOSED** | `step06_candidate_build.py:89` preserves exception identity. An independent in-memory baseline/current comparison again returned **exit 6 with identical `REFUSED` stderr**. This establishes the exercised refusal path, not blanket CLI equivalence. |
| **A8 — Dry run** | **CLOSED** | Writer `:348` returns before execution/DML. Direct-substep and inherited-run recording tests passed. |
| **A9 — Inactive cockpit planning** | **CLOSED** | `platform/src/app/api/cockpit/plan/route.ts:51` requires active writers. I executed the actual transpiled route and planner with mocked authentication/database boundaries: the active asset was planned and the inactive candidate excluded. |
| **A10 — Timeout consistency** | **CLOSED** | `platform/scripts/seed/asset_registry_seed.ts:2291` specifies 7200 seconds; dispatch validation `:161` rejects an incompatible existing row. The refusal test passed. |

R1 and R2 are closed as computational defects. **A2 remains partly closed overall until the substituted peak is honestly qualified.**

The independently replayed projection results were:

| Case | `1c84d6b32` projection | `98864fc41` projection |
|---|---|---|
| R1: target 300°, speed 0.5°/day, orb 5°, centre `h1 + 9.5d` | Zero windows despite positive activity at April 17 18:00 UTC | Era April 17–18; peak date April 17; validator passes |
| R2: target 300°, speed 1°/day, orb 5°, centre `h1` | Month/day peak April 18; validator aborts | Month/day peak April 17; validator passes |
| Orb opens exactly at `h1` | — | No episode/window |
| Interior peak three days before `h1` | Valid family | Same dates and intensities |

## Kernel change

**1. Exact half-open membership is justified.**

`services/gochara_kernel/episodes.py:211`, `:405`, `:493`, and `:711` consistently distinguish interval overlap from exact-event membership:

- An instant at `h0` belongs to the horizon; one at `h1` does not.
- An overlapping span survives even when its exact event lies outside the horizon.
- Empty overlap at the excluded end is discarded.
- Solver tolerance does not enlarge the domain.

My baseline/current reproductions confirmed that an ingress approximately 40 μs before `h0` now retains the overlapping residence with `t_exact=None`, and an ingress exactly at `h1` no longer creates a zero-length residence.

This agrees with the half-open contract and the specification’s preservation of truncated spans. It **can change results near the former slack boundaries**; it is not output-neutral.

**Migration 1153 does not independently guarantee `[)`.** Its helper at `platform/migrations/1153_gochara_sky_event_substrate.sql:417` checks finite, nonempty, era-bounded ranges; its self-test at `:1244` explicitly accepts `[]`. The convention constraint at `:595` only orders endpoints. This writer also uses the legacy ledger. Application validation remains necessary, as the corrected PR body states.

**2. The multi-revolution fix is justified.**

`episodes.py:149` enumerates every intersecting unwrapped orb band while preserving direction-dependent entry/exit solving.

My 600-day synthetic Sun comparison, with longitude increasing 1°/day and target 200°, produced:

- Baseline: exact occurrence at **+460 days only**.
- Current: exact occurrences at **+100 and +460 days**.

The focused tests also cover falling sweeps and unchanged station-complex controls. The changed expectations repair missing occurrences; they are not merely updated snapshots concealing unexplained drift.

**3. The Moon probe’s application-cache defect is closed.**

`knots.py:140` performs a same-instant TRUE_NODE backend probe before each Moon calculation. `:130` and `:152` serialize both operations through the reentrant Swiss-state boundary. Rahu/Ketu remain mean-node calculations; the probe does not change their node model.

The new implementation makes no calendar-block cache decision and remembers no successful result. Real coverage-edge checks and the modeled backend-loss comparison support that narrower claim.

This is **backend detection, not cryptographic file-identity verification**. I did not establish atomicity against external filesystem replacement or independent invalidation of Swiss Ephemeris’s internal file state.

**Consumer effects**

| Consumer | Effect of these changes |
|---|---|
| **`ka_gochara_v3_century_materialize`** | Its calculation path uses `build_resolution_hierarchy` and threshold machinery (`pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2135`, `:2193`). I found no numerical effect from these three kernel changes on that path. Its source digest changes through the dependency closure. |
| **`ka_moorti_nirnaya`** | Calls kernel boundary-root refinement (`services/ka_moorti_nirnaya/writer.py:229`), not episode horizon membership or `in_orb_intervals`. The Moon probe can trigger the existing unrefined-spline fallback at `:234`; solver provenance is recorded at `:251`. A later build can therefore change refinement results and notes. The fallback disclosure came from merged main and is context, not this PR’s repair. |
| **`ka_sangam`** | Its exercised paths use legacy `find_aspects`/`find_ingresses` (`services/ka_sangam/engine.py:464`, `:1627`, `:1743`), which delegate to legacy calculations (`services/ka_gochara/service.py:177`, `:198`). No direct numerical effect from these three changes was identified; its closure digest still changes. |
| **step06 “4.x” chain** | Directly calls the changed episode, boundary and residence functions (`step06_enumerate_episodes.py:768`, `:782`, `:806`). Subsequent permitted builds can persist different contact counts, exact stamps and downstream windows. |
| **Live Moon episode serving** | Calls the sampler and changed episode solvers (`services/ka_gochara/service.py:615`, `:627`, `:631`). **All three changes can affect served results on deployment without a candidate flip.** My synthetic 90-day replay through the actual service changed one returned occurrence to three, with authentication/ledger boundaries mocked. |

Deployment alone rewrites no stored rows. Existing ledger-backed results remain stored as before; subsequent builds may differ. Live Moon computation is the important exception to any suggestion that “no flip” means “no serving change.”

## Follow-ups

**Whole-horizon windows capacity — OPEN.** The PR correctly marks this unevidenced. Moon sampling timings do not measure the windows substep. Projection fetches contacts with `fetchall()` at `step06b_windows_projection.py:1734` and retains potentially large structures, including the position cache at `:342`.

Before the intended large dispatch, record representative contact/window counts, peak process memory, total windows-substep elapsed time and transaction behavior against the configured timeout. Existing elapsed logging is instrumentation, not capacity evidence.

**Candidate/publication/teardown serialization — OPEN.** `services/gochara_kernel/ledger.py:239` checks status with an ordinary read; publication later updates at `:548`. Teardown has analogous prechecks. These do not establish mutual exclusion between candidate mutation, publication and teardown. A shared locking/serialization protocol remains necessary before concurrent operation is allowed. This is the previously separated operational follow-up, not a newly discovered merge blocker.

**PR-body claims — mostly corrected.** The supplied body now accurately limits CLI equivalence, distinguishes author PostgreSQL evidence, explains migration 1153, removes successor-admission claims, discloses live Moon effects, and leaves capacity/concurrency open.

Two qualifications remain:

- Line 8’s “counted in the class report — never implied” overstates disclosure through the governed writer.
- “Latest in-domain instant” is inaccurate terminology for an 8.64-second offset. It is a chosen sample. The source’s benchmark figures at `knots.py:126` and PR-body figures use different baselines and should be labeled accordingly.

The live-serving caveat should explicitly cover membership and multi-revolution changes as well as the probe.

## Regressions and pins consistency

**The remaining regression is loss of stand-in provenance.**

The choice at [step06b_windows_projection.py:1445](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799d/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:1445) is numerically defensible as a disclosed boundary-limited sample: `max(interval_start, h1 − 1e-4d)`. The intensity is correctly reevaluated there.

It is **not a located extremum**. For the increasing R2 example, the excluded endpoint is where the maximum would occur, while the retained domain has a supremum rather than an attained maximum.

Nevertheless:

- `_window_row` emits ordinary `peak_date`, intensity and `peak_basis` at `:1653`, `:1657`, `:1710`.
- Its persisted `suppression_state` at `:1683` has no stand-in qualification.
- The class report contains counters at `:1608`, but [the governed writer at :492](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2799d/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:492) drops them from both its returned notes and log.

I passed actual R2 rows through the real `write_windows` function with a recording connection. The month/day INSERT payloads carried the ordinary basis `gochara_lambda_v3:m1_linear_no_box:step06b` and no substitution metadata. A separate report-propagation replay showed `peaks_clamped_to_horizon_limit=1` disappearing from governed-writer output.

A consumer can therefore mistake the stand-in date and evaluated intensity for an identified peak. Candidate-only status limits exposure but does not make that representation honest.

No additional computational blocker was found in the exercised paths.

**Pins remain consistent with the owner’s zero-diff decision.** All five checked pins-family files are byte-identical to both merged main `15d8ca379` and local `origin/main@916842561`. The retained generation is `l3:4f4a1993c6ad:1ddd6f117934`. There is **no A2.5 pins successor**, and none is required. Both earlier admission documents are explicitly superseded.

All four changed writer digests match independently derived source closures:

| Writer | Files | Digest prefix |
|---|---:|---|
| Candidate | 62 | `f27c2801c62c` |
| Century materializer | 55 | `028f987c6744` |
| Moorti | 17 | `e6c303584c53` |
| Sangam | 39 | `9e899b7b261e` |

Census content hashing, all 343 member hashes and ten directly hashed sources match. Its source revision correctly identifies the pre-refresh parent. The runtime catalog projection was not independently regenerated.

## Ranked merge-blocking amendments

**1. P2 — Persist and propagate horizon stand-in qualification.**

Qualify every affected R1 era row and R2 month/day row as a horizon-limited sample, using persisted metadata and an explicit consumer-visible basis/qualification. Record the selected instant, excluded horizon end and substitution rule; do not describe it as an attained extremum.

Carry the aggregate counters into the governed writer’s durable audit result or log. Add a regression assertion covering the persisted INSERT payload and writer reporting, rather than stopping at the direct projection report. Correct the PR/source wording, then refresh affected digests and census while preserving the intentional zero pins diff.

Capacity measurement and concurrency serialization remain separate follow-ups, not additional merge-blocking amendments in this review.

## What I could not verify

- Nine disposable-PostgreSQL cases, including real rollback/retry, native-row windows execution and the new final-edge ledger case. Their reported passes remain author evidence.
- Filesystem-mutating Moon tests, external file-replacement atomicity, deployed ephemeris contents or Swiss internal cache invalidation.
- Full CI, the reported 650-test result, representative windows capacity or concurrent-transaction safety.
- Production data/schema/authority, the PR’s production row-count audit, or deployment behavior.
- Full runtime catalog projection regeneration.

**No file was written, no git write command was run, no production database was contacted, and neither prohibited tree was read or changed.**