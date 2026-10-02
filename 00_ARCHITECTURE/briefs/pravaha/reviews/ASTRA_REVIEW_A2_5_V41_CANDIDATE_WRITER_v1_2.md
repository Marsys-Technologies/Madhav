---
artifact: ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: 1c84d6b32
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

**A1 is CLOSED. A2 and A7 remain PARTLY closed.** The seven previously closed findings remain closed.

Two substantive projection failures remain:

- The exact v1.1 final-day counterexample still produces **zero windows despite positive in-domain activity**.
- Restoring the horizon limit to the sampling series reintroduces **excluded-end month/day peaks**, causing the writer to abort.

The multi-revolution correction is justified. The Moon probe correctly rejects an unavailable backend on a cold cache, but its cache does not establish the claimed file-block scope or complete invalidation.

Independent execution: **173 focused tests passed**, **20 Swiss-state/non-mutating Moon tests passed**, and **3 database-independent tests from the PostgreSQL module passed**. Eight PostgreSQL cases skipped because the sandbox denied the local connection. Additional counterexamples, baseline comparisons, route execution and hash checks ran in memory.

Source references below are relative to `platform/python-sidecar/` unless explicitly rooted elsewhere.

**Closure table**

| Finding | Status | Evidence and independent rerun |
|---|---|---|
| **A1 — Runner input types** | **CLOSED** | `scripts/kala_gochara_cutover/step06a_class_context.py:329` now handles dictionary and tuple rows; `step06b_windows_projection.py:1773` aliases the optional column. My actual `run_substep(windows)` execution with a UUID chart, nonempty dictionary results and a recording database completed: `classes=1`, `class_context_omitted=0`. The identical input against the old context code reproduced `AttributeError: 'str' object has no attribute 'timestamp'`. The old optional-column path reproduced `KeyError: 'formula_version'`; current code returned `formula_version=None`. Freshness was mocked in this comparison; it was not PostgreSQL evidence. |
| **A2 — Half-open horizon** | **PARTLY** | `services/gochara_kernel/episodes.py:223` fixes empty span overlap; `:713` fixes residence ingress membership. My producer-level reruns confirmed both. Projection still loses the original final-day interval at `step06b_windows_projection.py:1496`, and peak refinement can again escape onto the excluded end at `:1537`. Detailed reproductions follow. |
| **A3 — Executable source closure** | **CLOSED** | `pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:308` declares the dynamic roots. The actual hasher collects **62 files**. Its digest, `3980d25ccae15…`, matches the inventory; the executable mutation-sensitivity test passes. |
| **A4 — Teardown scope/refusals** | **CLOSED** | `platform/scripts/dispatch_a25_v41_candidate_job.py:185` scopes candidate deletion to the pinned chart/generation. Published, serving and active-run checks remain at `:213`, `:227`, `:241`. Recording-connection tests passed for all refusals and transactional cleanup. Concurrency remains separate. |
| **A5 — Ephemeris path** | **CLOSED** | Writer `ka_gochara_v4_41_candidate.py:168` retains explicit configuration → `SWE_EPHE_PATH` → development fallback. Resolution-order and checksum-pinned real-Swiss sampler tests passed. This does not verify deployed-image contents or the new Moon cache. |
| **A6 — CLI refusal exit code** | **CLOSED** | `step06_candidate_build.py:89` preserves ledger exception identity. I loaded the baseline CLI into memory and reran both implementations: **exit 6 and identical `REFUSED` stderr**. The PR body now correctly limits this equivalence claim to the exercised refusal path. |
| **A7 — Acceptance evidence** | **PARTLY** | The new tests materially improve coverage: actual windows execution at `test_a25_v41_candidate_writer_pg.py:601`, interrupted writer-substep execution and retry at `:503`, and disposable-database creation at `:235`. However, the replacement projection test at `:940` uses a constant longitude and activity beginning three days before the limit, rather than the v1.1 failing geometry. It misses both remaining failures. Eight PostgreSQL cases were **NOT_RUN** independently. No pins-admission test is required under the owner’s revised scope. |
| **A8 — Dry run** | **CLOSED** | Writer `:348` returns before execution/DML. The inherited `run()` and direct-substep recording tests passed. |
| **A9 — Inactive cockpit planning** | **CLOSED** | `platform/src/app/api/cockpit/plan/route.ts:51` requires active writers. I executed the actual route and planner in memory with mocked authentication/database boundaries: the active asset was planned; the inactive candidate was excluded. |
| **A10 — Timeout consistency** | **CLOSED** | `platform/scripts/seed/asset_registry_seed.ts:2291` specifies **7200 seconds**. Dispatch validation at `dispatch_a25_v41_candidate_job.py:161` still rejects a pre-existing incompatible row. Its refusal test passed. |

**Kernel change**

**1. Exact half-open membership: the episode-side repairs are correct.**

My old/current comparisons through actual enumeration produced:

| Geometry | `31e56d9b6` | `1c84d6b32` |
|---|---|---|
| Orb interval begins exactly at excluded `h1` | Empty contact at `h1` emitted | Excluded |
| Residence ingress 40 μs before `h0` | Out-of-domain exact stamp; validator raises | Overlapping span retained with `t_exact=None`; validator passes |
| Residence ingress exactly at `h1` | Zero-length residence; validator raises | Excluded |

The current instantaneous-boundary tests also retain `h0` and exclude `h1`. Removing solver slack from domain membership is appropriate; retaining legitimate overlapping spans separately satisfies the N3 truncation requirement.

**Migration 1153 still does not enforce `[)` universally.** Its `ka_gochara_horizon_finite_ok` at `platform/migrations/1153_gochara_sky_event_substrate.sql:417` checks finite, nonempty, era-bounded ranges. Its self-test at `:1244` explicitly accepts `[]`. The convention check at `:595` requires ordered endpoints. Moreover, this writer uses the legacy `kala_gochara_*` ledger, not the new substrate’s contact constraints. Application-level enforcement remains necessary.

**2. Multi-revolution enumeration: accepted.**

`episodes.py:149`–`:183` searches every intersecting unwrapped band and preserves direction-aware entry/exit solving.

I independently reran the ruling’s Sun geometry:

```text
Sun: λ = 100° + 1°/day; target = 200°; horizon = 600 days

Before: exact occurrences [460]
After:  exact occurrences [100, 460]
```

The focused suite’s Moon, Mercury, falling-sweep and retrograde controls passed. I found no defect in this correction.

**3. Moon file probe: correct cold-cache gate, incomplete cache guarantees.**

The TRUE_NODE probe at `knots.py:169` is serialized, does not replace mean-node contact geometry, and correctly rejects the modeled missing-`semo` condition through the sampler and bisection entry points. The real complete-file comparison passed.

Two cache assumptions are unsound:

- **The calculated block is not the file’s actual coverage.** `knots.py:132` approximates calendar years. The installed, checksum-pinned library reports `semo_18.se1` coverage as JD **2378487.555370702–2597656.4574524714**, extending into **January 2400**. A successful real probe on **2400-01-02** caches block `1`; **2400-02-01** shares that key and skips the required probe. With the cache cleared, the February call raises `EphemerisBackendError`. In this real reproduction February’s Moon flag was also Moshier, so downstream flag checks still reject it; this demonstrates incorrect cache scope, not a demonstrated silently served Moshier result.
- **Directory metadata is not file identity.** `knots.py:147` records directory inode/mtime only. Changes to file contents, or to an externally located symlink target, need not change that stamp. With backend loss modeled while preserving the directory stamp, the warmed gate returned the Moon’s misleading SWIEPH flag without another TRUE_NODE call; clearing the cache correctly refused the same call.

The fake library’s block selector at `test_a25_moon_file_backend_probe.py:123` repeats the implementation’s approximation, so its widely separated 2000/2500 test cannot detect the real coverage-boundary problem. Also, `ephe_path=None` is not invariably uncached: a statable `SE_EPHE_PATH` can produce a cache key.

**Consumer effects**

| Consumer | Effect of these changes |
|---|---|
| **step06 “4.x” chain** | Calls the changed episode solvers at `step06_enumerate_episodes.py:768` and `:782`. Re-enumeration can change boundary membership and occurrence counts for **4.0 and 4.1**. The pre-4.1 null-exact filter still applies. The candidate persists no Moon, so its body enumeration does not exercise the new Moon probe. |
| **Live Moon serving** | `services/ka_gochara/service.py:615`, `:627`, `:631` exercise all three changes. **Served output can change upon deployment without a candidate flip.** Through actual `find_episodes(..., moon=True)` under mocked **4.0 authority**, a synthetic 90-day Moon sweep returned **one occurrence before, four after** the revolution fix. |
| **`ka_gochara_v3_century_materialize`** | Uses the threshold-crossing/resolution-hierarchy path, including writer `:2135` and `:2193`. I found no calculation change from these hunks; its digest changes through import closure. |
| **`ka_moorti_nirnaya`** | Calls `contacts.find_boundary_roots`, not the changed episode membership functions. Its Moon refinement now encounters the new probe; `services/ka_moorti_nirnaya/writer.py:235` can fall back to spline roots and change solver notes. Grading uses the daily Moon arc at `:454`; I found no necessary numeric grading change from this probe alone. |
| **`ka_sangam`** | Its current service calls use legacy methods such as `find_aspects` and `find_ingresses` (`engine.py:464`, `:1627`), not live Moon episode solving. No calculation change from these hunks was identified; its digest changes through import closure. |

Deployment does not rewrite stored rows. Affected producers can generate different rows on a subsequent permitted build. Existing ledger reads remain unchanged until data changes; live Moon computation is immediately affected.

The four regenerated writer digests are **mechanically justified and match their source closures**. They do not establish semantic correctness.

**Follow-ups**

- **Representative windows memory/elapsed measurement — OPEN.** The PR body correctly acknowledges this at line 22. My sparse recording-database execution is not capacity evidence for the intended build. The contact fetch remains whole-set (`step06b_windows_projection.py:1698`), and the position cache remains unbounded (`:342`). Obtain representative peak memory and complete-substep elapsed evidence before dispatch.
- **Candidate/publication/teardown serialization — OPEN.** `ledger.py:239` remains an ordinary status read; candidate-manifest update at `:548` lacks a status predicate or shared serialization mechanism. Teardown likewise checks before deleting without preventing a concurrent publication. The PR now discloses this limitation. Resolve it before allowing those operations concurrently.
- **PR-body corrections — PARTLY CLOSED.** The blanket CLI-equivalence and obsolete teardown-help claims are corrected. However, [the supplied body](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/pr2799_body_c.md:18>) still claims successor admissions at lines 18 and 38, contrary to the final reset. Its half-open/projection claim at line 8 remains false. The new Moon change and cache limitations are absent. Production row-count/blast-radius statements remain author evidence, not independently verified facts.

These operational follow-ups remain separate from the reproduced projection rejection grounds.

**Regressions and successor consistency**

**R1 — The exact v1.1 final-day omission remains.**

Through actual `enumerate_body` → `fetch_contacts` → projection, with target 300°, speed 0.5°/day, orb 5° and exact centre 9.5 days after the horizon end:

```text
t_in     = 2026-04-17T12:00:00Z
t_exact  = None
t_out    = 2026-04-18T00:00:00Z

λ(2026-04-17T18:00:00Z) = 0.02025 > 1e-9
Projected components   = 0
Projected windows      = 0
```

Appending `h1` allows `find_components` to locate the positive interval. But its only sampled above-threshold point is `h1`. Filtering that point at `step06b_windows_projection.py:1496` leaves an empty list, and `:1499` discards the **nonempty in-domain interval**. “No in-domain sample” does not establish “no in-domain activity.”

**R2 — Peak refinement reintroduces the excluded end and aborts the substep.**

Using actual enumeration for a Sun contact whose exact centre is precisely `h1`, target 300°, speed 1°/day and orb 5° produced:

| Resolution | Window start | Window end | Peak |
|---|---|---|---|
| era | 2026-04-13 | 2026-04-18 | 2026-04-17 |
| month | 2026-04-13 | 2026-04-18 | **2026-04-18** |
| day | **2026-04-18** | **2026-04-18** | **2026-04-18** |

`refine_peak_to_day` at `:1528` can return `h1`; the inclusive `<= exit_jd` check at `:1537` admits it. The writer then raises **`HorizonViolation`** before DML. This is a fail-closed build abort, not persisted invalid output.

**R3 — Moon cache scope/invalidation gaps are new**, as detailed above.

**Pins: consistent with the owner’s zero-diff decision.**

All five checked pins-family files are byte-identical to local `origin/main@2992093bc`. The active L3 generation is **`l3:4f4a1993c6ad:1ddd6f117934`**, with eight historical entries. There is **no A2.5 successor admission in this final tree**, and its absence is not a defect.

Exactly four inventory entries differ from main: candidate, century materializer, Moorti and Sangam. All four match independently derived hashes. Census content hashing, all **343 member hashes**, and **10 directly hashed sources** match. Denominator movement accounts for the added inactive candidate; active membership is unchanged. The runtime catalog projection was not regenerated.

**Ranked merge-blocking amendments**

| Rank | Priority | Required amendment |
|---:|---|---|
| **1** | **P1 — A2/R1** | Preserve positive final partial intervals even when only the horizon-limit sample is above threshold. Add the exact producer-to-projection counterexample above. |
| **2** | **P1 — A2/R2** | Keep refined peaks strictly inside the horizon. Preserve a valid in-domain representation when refinement reaches `h1`; do not abort or discard the legitimate interval. Test through the writer validator. |
| **3** | **P2 — R3** | Remove the Moon success cache or bind it to verified file identity and actual coverage. Test real coverage-boundary transitions and invalidation independent of directory mtime. |
| **4** | **P2 — A7/evidence** | Add tests that fail on R1–R3, rerun the disposable PostgreSQL integration cases, and reconcile PR/authority prose with the final implementation and zero-pins-diff scope. Refresh digests/census after fixes; **do not re-admit pins**. |

**What I could not verify**

The disposable PostgreSQL fixture now creates and drops its own database and checks the cluster identity before setup. The sandbox nevertheless denied its local connection: **eight database cases were NOT_RUN**, including real retry/rollback and windows integration. Their reported passes remain author evidence.

I did not run Moon tests requiring temporary filesystem mutation, verify production schemas/data/authority, inspect the deployed image, establish representative capacity or concurrent-transaction safety, run full CI, or regenerate the runtime catalog projection. Synthetic and recording-boundary reproductions are identified above.

**No file was written, no git write command was run, no production database was contacted, and neither prohibited tree was read or changed.**