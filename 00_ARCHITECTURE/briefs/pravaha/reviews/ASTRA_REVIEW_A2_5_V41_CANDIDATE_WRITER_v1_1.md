---
artifact: ASTRA_REVIEW_A2_5_V41_CANDIDATE_WRITER
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-10-01"
verdict: REJECT
reviewed_commit: 31e56d9b6
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT**

Seven findings are closed; **A1, A2 and A7 remain PARTLY closed**. The remaining defects are substantive:

- The actual windows entry point still crashes with the runner’s dictionary rows.
- Actual enumeration can produce an empty contact at the excluded horizon end that passes validation.
- The projection change can silently discard legitimate activity inside the final day.

I read the v1.0 review, the latest author packet, and the supplied PR-body snapshot. Independent checks completed: **54 candidate-writer tests passed**, **73 focused kernel/service/projection tests passed**, plus the counterexamples and comparisons below. These passing suites do not detect the remaining failures.

**Closure table**

Paths below are relative to the reviewed checkout; line numbers refer to `31e56d9b6`.

| Finding | Status | Evidence and independent rerun |
|---|---|---|
| **A1 — Runner input types** | **PARTLY** | UUID normalization is fixed in `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py:212`; ledger dictionary-row handling passes. However, `platform/python-sidecar/scripts/kala_gochara_cutover/step06a_class_context.py:329` still unpacks dictionaries as tuples. My actual `run_substep(..., windows)` invocation with a UUID chart and dictionary rows raises **`AttributeError: 'str' object has no attribute 'timestamp'`**. |
| **A2 — Half-open horizon** | **PARTLY** | The original instantaneous-boundary and excluded-date window counterexamples are repaired. Remaining failures occur in span clipping, residence membership and projection sampling, detailed below. Relevant locations: `platform/python-sidecar/services/gochara_kernel/episodes.py:216`, `:697`; writer `:267`; `step06b_windows_projection.py:1460`. |
| **A3 — Executable source closure** | **CLOSED** | Writer `:308` declares the dynamic roots. The actual hasher now collects **62 files**, including all four cutover modules, `ledger.py` and `legacy_semantics.py`, versus 35 files previously. The derived digest matches the committed inventory; in-memory changes to declared implementation bytes change the digest. |
| **A4 — Teardown scope/refusals** | **CLOSED** | `platform/scripts/dispatch_a25_v41_candidate_job.py:185` scopes data deletion to the pinned chart and generation; bookkeeping is scoped to the dispatch/chart. Published, serving and active-run refusals precede deletion at `:213`, `:227`, `:241`. Reruns exercised each refusal and one-transaction cleanup. This closes the original sequential teardown defect; concurrency remains a separate follow-up. |
| **A5 — Ephemeris path** | **CLOSED** | Writer `:168` resolves explicit configuration, then `SWE_EPHE_PATH`, then the development fallback. I passed the resolved environment path into the real sampler using checksum-verified local ephemeris files: **32 knots, backend `swieph`**. Deployed-image contents were not inspected. |
| **A6 — CLI refusal exit code** | **CLOSED** | `step06_candidate_build.py:89` caches the ledger module, preserving exception identity. I executed the merge-base and current CLI implementations in memory against the same published-manifest recording connection: **both returned 6 with identical `REFUSED` stderr**. This verifies that refusal path, not blanket CLI equivalence. |
| **A7 — Acceptance evidence** | **PARTLY** | Coverage improves materially, including actual route and frozen-manifest checks. However, the PostgreSQL retry test at `test_a25_v41_candidate_writer_pg.py:343` calls ledger functions directly, not an interrupted writer substep; the windows dictionary-row failure remains untested. The projection-end test at `test_a25_v41_candidate_writer.py:1024` checks source strings. The new pins assertion at `platform/src/generated/__tests__/nirmana-analysis-receipts.test.ts:615` remains inside `describe.skip` at `:78`. |
| **A8 — Dry run** | **CLOSED** | Writer `:348` returns before execution/DML. Reruns covered inherited `run()` and direct `run_substep()` paths with no recorded DML. |
| **A9 — Inactive cockpit planning** | **CLOSED** | `platform/src/app/api/cockpit/plan/route.ts:51` now requires active writers. I executed the actual baseline/current route and planner code with mocked authentication/database boundaries: baseline selected the inactive candidate; current returned only the active asset. |
| **A10 — Timeout consistency** | **CLOSED** | `platform/scripts/seed/asset_registry_seed.ts:2284` specifies **7200 seconds**. Dispatch validates the landed registry row at `:161`. The pre-existing 600-second-row counterexample now refuses before staging or activation. |

**Kernel change**

The exact-membership changes at `episodes.py:391` and `:479` are directionally correct: numerical solver tolerance should not enlarge a declared `[start, end)` domain.

I reran the original boundary geometry against both `1dbb07ef6` and the reviewed implementation:

| Computed crossing | Before | Current |
|---|---|---|
| `1998-01-01T00:00:00Z` | Retained | Retained |
| `1997-12-31T23:59:59.999960Z` | Incorrectly retained | Excluded |
| `2026-04-18T00:00:00Z` | Incorrectly retained | Excluded |

This agrees with half-open exact-contact membership and with the specification’s distinction between exact events and retained truncated spans. [GOCHARA_DESIGN_SPECS_v1_4.md:630](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md:630) and `:664` require off-horizon centres to remain represented by their legitimate overlapping spans.

**Migration 1153 does not establish that this writer enforces those semantics.** Its `ka_gochara_horizon_finite_ok` at `platform/migrations/1153_gochara_sky_event_substrate.sql:417` checks finite, bounded, nonempty horizons and the permitted era; it does not require `[)` bounds. Its self-test explicitly accepts a finite `[]` range. The convention constraint at `:595` checks only `domain_start < domain_end`. Its new contact table requires positive spans at `:1102`, but this writer uses the separate legacy `kala_gochara_*` tables.

The consumer effects are:

| Consumer | Effect of this kernel hunk |
|---|---|
| **step06 “4.x” chain** | Calls both changed solvers at `step06_enumerate_episodes.py:768`, `:782`. Re-enumeration can change boundary rows for **4.0 as well as 4.1**. For pre-4.1 generations, an orb contact whose exact instant becomes out-of-domain is withheld by the null-exact gate at `:743`. |
| **Live Moon serving** | **Served output can change immediately on deployment.** `services/ka_gochara/service.py:627` and `:631` call the changed solvers. I exercised the real `find_episodes(..., moon=True)` entry point under a **4.0 authority**, with synthetic knots and refinement disabled: the old kernel served the crossing at the excluded end; current code returned no episode. |
| **`ka_gochara_v3_century_materialize`** | Its calculation uses `find_threshold_crossings`/the resolution hierarchy, including writer `:2193`, rather than these episode solvers. Its digest changes through the shared import closure. No calculation change from this hunk was identified. |
| **`ka_moorti_nirnaya`** | `services/ka_moorti_nirnaya/writer.py:186` imports and calls `contacts.find_boundary_roots`, not the changed membership functions. The digest movement is an import-closure consequence. |
| **`ka_sangam`** | Current calls use the legacy service methods—e.g. `services/ka_sangam/engine.py:464`, `:1627`—rather than Moon `find_episodes`. Its digest movement is likewise an import-closure consequence. |

Importing or deploying this kernel change does not itself rewrite existing stored rows. Rebuilding through affected producers can produce different rows and digests. Ordinary reads of unchanged ledger rows remain unchanged; the live Moon counterexample demonstrates why a general **“existing served output is unchanged”** claim would be false.

Two kernel defects remain:

1. **Empty overlap at the excluded end is accepted.** `_clip_to_horizon` at `episodes.py:216` rejects `t_in > h1`, but permits `t_in == h1`. Using the real `enumerate_body`, a synthetic Sun moving 1°/day, target 0°, orb 5°, and exact centre five days beyond the horizon produced:

   ```
   relation = conjunction
   t_in     = 2026-04-18T00:00:00Z
   t_exact  = None
   t_out    = 2026-04-18T00:00:00Z
   ```

   The writer validator accepted it; `ledger.write_contacts` reached **one recorded INSERT**. This is not a legitimate overlapping truncated span.

2. **Residence membership still uses the old slack and closed end.** `episodes.py:697` retains `h0 - 1e-9 <= entry_exact <= h1 + 1e-9`. Actual residence enumeration retained the ingress approximately 40 μs before the start. An ingress exactly at the excluded end generated a zero-length residence with that excluded exact instant; the writer then raised `HorizonViolation`, aborting the body instead of excluding the nonoverlapping residence.

The re-pinned digests are justified mechanically. They do not establish correctness of these remaining branches.

**Follow-ups**

- **Whole-horizon memory/elapsed measurement — still open.** No representative measurement was supplied or obtained. Writer `:493` logs elapsed time, but logging and a 7200-second budget are not capacity evidence. `step06b_windows_projection.py:1693` fetches all contacts, and `:342` maintains an unbounded position cache. Measure the complete windows substep after the functional blockers are repaired, before the approximately 10M-row dispatch.

- **Candidate/publication serialization — still open.** `services/gochara_kernel/ledger.py:239` performs an ordinary status SELECT before mutation at `:417`; candidate-manifest UPDATE at `:548` has no status predicate. Teardown also uses ordinary checks. A candidate check can precede a concurrent publication commit, followed by candidate mutation/deletion. No common serialization mechanism or concurrency proof was established. Resolve this before allowing concurrent candidate mutation, publication or teardown.

- **PR-body corrections — not closed.** The supplied [PR-body snapshot](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/pr2799_body_b.md:3) still says “all conditions implemented,” claims byte-identical CLI behaviour at `:6`, describes teardown DELETEs in `--help` at `:9`, and reports **24 new tests** at `:13`. The author packet’s claim that the whole injected chain is row-shape agnostic is also contradicted by A1. Update claims to distinguish executed evidence, reported totals and remaining limitations.

These follow-ups are separate from the concrete rejection grounds.

**Regressions and successor consistency**

**New projection regression: legitimate final-day activity disappears.** At `step06b_windows_projection.py:1460–1467`, excluding the end from both breakpoints and the grid can leave no sample inside the last partial interval. `find_components` at `:1430` also treats the final sample as the component boundary.

I generated a legitimate contact through the actual enumerator, converted it through `fetch_contacts`, then ran actual projection:

```
t_in    = 2026-04-17T12:00:00Z
t_exact = None
t_out   = 2026-04-18T00:00:00Z
```

The synthetic trajectory has target 300°, speed 0.5°/day and its exact centre 9.5 days after the horizon end. At `2026-04-17T18:00:00Z`, the actual evaluator returns **0.00324**, above the **1e-9** threshold.

- Previous projection: one component, albeit with the previously invalid excluded-end peak.
- Current projection: **zero components, zero windows**.

The fix must preserve the positive in-domain interval while excluding out-of-domain peaks.

**New dictionary-row compatibility regression:** `step06b_windows_projection.py:1756` selects bare `NULL` when `formula_version` is absent, while `:1766` reads dictionary key `"formula_version"`. The returned column is `"?column?"`; my fallback-schema probe raises **`KeyError: 'formula_version'`**. Alias the expression. I did not establish whether that fallback schema exists in production.

**Pins successor: mechanically consistent.**

- Active successor: **`l3:f6cb3914e7f1:bf1dba54ee01`**.
- Archived predecessor: **`l3:639eece63be3:df2b966b1d97`**, preserved with its writer snapshot.
- Exactly four writer digests changed: candidate, century materializer, Moorti and Sangam.
- All four derived hashes match the committed inventory. For the latter three, the changed file in their closure is only `episodes.py`.
- L3 history grows from nine to ten entries; earlier entries, other layers and immutable definition bindings remain unchanged.
- Source and delivery checks, using protected baseline `2b3e096739b3501395a74c079846433c1bee3992`, introduce **no L3 failure**.
- The same three ordered inherited failures remain: L1 inventory staleness, the L1 successor’s changed-assets mismatch, and L2 inventory staleness. They match the fixed-main comparison and locally available `origin/main` comparison. **The complete pins checker is not globally green.**
- Census content hashing matches; **351 file fingerprints match**. Census changes are confined to timestamp, source revision, provenance and content hash; denominators remain unchanged. I did not regenerate its runtime catalog projection.

These checks support the successor recorded at `platform/src/generated/nirmana-analysis-layer-pins.json:1736`. Further implementation fixes will require updated digests and the corresponding governed successor treatment.

**Ranked merge-blocking amendments**

| Rank | Priority | Required amendment |
|---:|---|---|
| **1** | **P1 — A1** | Normalize dictionary/tuple access throughout the actual class-context/windows chain, including the optional-column alias. Exercise the real windows entry point with a UUID chart and nonempty dictionary-row results. |
| **2** | **P1 — A2** | Complete half-open handling across orb spans, residence ingress and projection. Exclude empty overlaps at the boundary, preserve valid instantaneous events inside the horizon, and retain legitimate final-day truncated activity. Add executable producer-to-validator/projection tests for the reproduced geometries. |
| **3** | **P1 — A7** | Establish the claimed writer integration evidence: actual windows execution and interrupted writer-substep retry with before/after sibling snapshots. Move the relevant pins assertion into an active test. Replace source-string evidence where it currently misses behaviour. Refresh digests/pins/census after those fixes. |

**What I could not verify**

No database connection was made. The added PostgreSQL fixture connects to an existing DSN and executes destructive setup; it does not create its own disposable database, so I did not run it under this review’s constraints. Its reported five passes remain author evidence.

I did not verify production schemas, deployed image contents, production authority state, full-scale performance, concurrent transactions, complete suite/CI totals, or an actual squash-delivery commit. The CLI comparison and route probe ran in memory with recording/mocked database boundaries; astronomical counterexamples used synthetic trajectories through real computation code.

**No file was written, no git write command was run, and neither prohibited directory was accessed.**