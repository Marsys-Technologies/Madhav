---
artifact: ASTRA_REVIEW_A2_5_STREAMING
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 56395158d
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** Amendments **4 and 6 are CLOSED**; **2, 3 and 5 are PARTLY CLOSED**; **1 is NOT CLOSED** under the steward’s explicit conditions. All three memory-residual conditions fail. The new receipt producer also generates body-specific provenance that the driver rejects as inconsistent.

I read v1.1 first and reviewed `7cea0c111 → 56395158d718cd8b4a4bf5ce9717da6f395328fd`. Numbering below follows v1.1’s **six ranked amendments**, rather than its older closure-table numbering.

All reported commits and `GREEN` emissions were observed through production functions using SQL recorders and in-memory evidence sinks. **No database was connected.**

**Closure table**

| v1.1 ranked amendment | Status | File:line evidence and independent rerun |
|---|---|---|
| **1. Complete-chain memory bound** | **NOT CLOSED** | [Class-context streaming](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06a_class_context.py:122) fixes the prior instant-list growth: my 20k/40k/80k probes each peaked at **6,728 bytes**. Batched insertion at 20k/40k remained approximately **0.98 MB**. Missing external staging now refuses. However, projection still retains input-proportional contacts and [writer dictionaries](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:743), and the substitute guard fails conditions (a)–(c), detailed below. |
| **2. Verifiable completeness and provenance** | **PARTLY CLOSED** | Replayed missing/unreadable objects, clean truncation, unexplained empty objects, empty/shortened coverage, foreign-body rows, absent snapshot, orb `999` versus `5`, and missing dedupe provenance: these now refuse without commit. Missing ephemeris and mixed-source receipts also refuse. Nevertheless, [candidate verification checks receipt coverage counts without comparing its coverage hash](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:896). Altered coverage with an unchanged receipt reached **exit 0, commit and GREEN**. Real producer receipts also fail cross-body compatibility. |
| **3. Comprehensive diagnostic redaction** | **PARTLY CLOSED** | The original URI-query, ordinary libpq, child-output and early manifest-error counterexamples now redact. A real child with a pipe handshake confirmed ordinary redaction preserves streaming and exit propagation. But [credential extraction](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/common.py:82) mishandles valid libpq escapes, and line-by-line forwarding leaks multiline secrets. Custom early driver refusals also bypass the redactor. |
| **4. Fresh, immutable attempts** | **CLOSED** | [Attempt identity, exclusive local creation and conditional uploads](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:142) are implemented at lines 142–147, 315 and 187 respectively. Replayed the collision using separate simulated containers and the **same forced attempt ID**: the second attempt returned **3**, and earlier finalized artifacts remained byte-identical. Existing empty attempt directories also refuse; 200 generated IDs were distinct. |
| **5. Actual identity, dedupe, digest and end-to-end tests** | **PARTLY CLOSED** | [Explicit survivor/identity tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/tests/l3/gochara/test_step06_century_stream.py:1959) and the production digest test at line 2063 now detect the formerly surviving constant-digest, constant-ID and disabled-dedupe mutations. My eight-body fixture, including aliases, divergent citations and eight no-exact survivors, again reduced **24 inputs to 16 survivors**, with matching IDs and real ledger digests away from minute-boundary cases. However, the claimed end-to-end fixture fabricates receipts and misses the producer incompatibility, late guard failures and retained writer state. |
| **6. Integrity-subclass classification** | **CLOSED** | [Classification](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:727) uses `isinstance` or SQLSTATE class `23`; handling is at lines 993–1005. Injected installed psycopg `UniqueViolation`, `IntegrityError` and a duck-typed `23505`: each returned **5**, rolled back and did not commit. An unrelated `RuntimeError` remained an exception after rollback. Reverting to exact class-name matching was detected. |

**Residual acceptance conditions (a)–(c)**

**(a) Loud abort before the container’s 16 GiB: FAIL.**

The [driver accepts an optional, unrestricted guard](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:260). My controlled chain runs with `--memory-guard-gib 0`, `-1`, `16` and `32` all returned **0/COMPLETE**. Zero and negative values omitted the guard from all children.

Furthermore, [failure to apply `RLIMIT_AS` is nonfatal](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/common.py:246). Injecting `setrlimit` rejection into the real candidate entry point produced **exit 0 and commit**, with `memory_guard.applied: false`.

The driver checks terminated-child RSS only after the child exits. That is not a demonstrated container-wide bound: the [spec explicitly identifies RAM-backed staging](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/00_ARCHITECTURE/briefs/pravaha/CENTURY_CLOUD_RUN_JOB_SPEC_v1_0.md:17), while enumeration writes its body payload before releasing the retained episodes. Parent memory and staging consumption are not accounted for by the child’s address-space limit.

**(b) No aborted or partial run reaches COMPLETE/GREEN or a candidate: FAIL.**

The [candidate transaction commits at line 980 and emits GREEN at line 1033](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:980). The [driver subsequently checks that child’s peak and runs class context and projection](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:545).

Using the actual candidate orchestration and ledger functions inside the controlled chain:

| Injected failure | Driver result | Candidate/evidence already produced |
|---|---|---|
| Candidate’s post-exit measured peak exceeds 14 GiB | Exit **3** | **Committed; GREEN** |
| Class-context child reports allocation failure | Exit **3** | **Committed; GREEN** |
| Projection child reports allocation failure | Exit **3** | **Committed; GREEN** |

The driver correctly withholds its final chain `COMPLETE` in these cases. That does **not** undo the earlier candidate and `GREEN`.

Allocation failure can also disappear entirely. The new [projection refinement call](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:1054) reaches [`eval_single_legacy`, which catches every `Exception`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/services/gochara_kernel/legacy_semantics.py:948). My refinement probe injected **16 `MemoryError`s**: they became zero evaluations; projection emitted **three rows**, and `run_main_guarded` returned **0**, without a memory diagnostic.

As a positive control, an injected allocation failure during candidate insertion did roll back and return **3**. The defect concerns uncovered and later failure paths.

**(c) Residual documented with its measured slope: FAIL.**

The [spec’s residual disclosure](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/00_ARCHITECTURE/briefs/pravaha/CENTURY_CLOUD_RUN_JOB_SPEC_v1_0.md:102) gives estimates of **2–4 GiB per body**, **16 bytes per series point**, and approximately **50 MB per million contacts**. It does not document a measured enumeration slope or the full retained projection state.

My synthetic `tracemalloc` measurements were:

| Allocation measured | Input sizes | Observed bytes |
|---|---|---|
| Episode construction, real dedupe and canonical sort — peak | 10k / 20k / 40k episodes | 23,337,177 / 46,383,177 / 92,615,940 |
| Sweep contact retention before evaluation; distinct targets with coincident spans | 20k / 40k / 80k contacts | 13,378,098 / 26,787,106 / 53,631,218 |
| Real window-writer retained state; distinct logical keys collapsing to one natural key | 20k / 40k / 80k projected keys | 1,405,538 / 2,950,762 / 5,911,954 |

These show approximately **2,309 bytes/episode** marginal peak for the synthetic enumeration fixture, **671 bytes/contact** retained for overlapping contacts, and **75 bytes/projected key** retained by the writer—even when those rows are collapsed.

The submitted dense-component fixture also passed, with approximately **157 bytes/contact** measured growth, but it keeps overlap depth near six and does not exercise the actual persistent writer dictionaries.

Additional input-sized allocation exists in the [pass-two `fetchall()`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:652). A bounded time interval does not bound the number of intersecting contacts.

These measurements are Python allocations, **not container RSS or production capacity forecasts**. They establish that the disclosure’s two-residual model is incomplete.

**Regressions and additional findings**

**P1 — Producer receipts make the real multi-body chain reject itself.** The enumerator [records backends under the enumerated body’s name and embeds that dictionary in `ephemeris`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:1474). The [driver compares the entire provenance block for equality](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:226); the consumer repeats that comparison.

I ran the actual enumerator `main()` for Sun and Mercury with synthetic data/ephemeris seams and in-memory output. Both returned **0**, with identical shared provenance, but their receipts contained respectively `backends: {"Sun": …}` and `backends: {"Mercury": …}`. The real driver check rejected Mercury as differing in `['ephemeris']`.

The [test fixture uses `backends: {}` for every body](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/tests/l3/gochara/test_step06_century_stream.py:177), concealing this producer/consumer incompatibility.

**P1 — Coverage can contradict its retained enumeration receipt and still earn GREEN.** I retained the Sun receipt, changed its merged coverage partition to `sun:unsearched_target`, cleared searched relations and target counts, and updated only the merged manifest’s coverage binding. Receipt and actual per-body coverage hashes differed. The real candidate entry point nevertheless returned **0**, committed and emitted **GREEN**. Its check establishes matching partition counts, not that the consumed partitions are those attested by enumeration.

**P1 — Valid escaped and multiline credentials still leak.** Using the installed psycopg’s connection-string parser without connecting, I confirmed valid libpq forms containing an escaped space or escaped backslash. Their decoded password literals survived `redact_text`. A quoted password containing a newline leaked through an actual child: `_run` redacted each line separately, so neither line matched the registered whole secret. Separately, passing a synthetic registered DSN as an invalid chart argument exposed it through the [raw early refusal](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:288).

**Inherited identity issue, not introduced by this diff.** An exact input instant `2020-03-11T01:00:00Z` becomes epoch `1583888399.9999866` after the enumerator’s Julian-date round trip; [ID serialization floors it to `00:59:00Z`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768c/platform/python-sidecar/services/gochara_kernel/ids.py:80). The independent UTC-floor oracle expects `01:00:00Z`. The new identity fixture uses seconds 17/59 and misses this boundary. I do not count this unchanged implementation as a newly introduced regression.

**Previously closed scope protection remains closed.** Another UUID and canonical-chart generations `4.0` and `5.0` each refused with **3 before filesystem/subprocess work**. Contact, coverage, candidate and window writers rejected a simulated published generation before row-changing SQL. Live published-generation contents remain unverified.

**Ranked merge-blocking amendments**

1. **P1 — Prevent partial-run success.** Keep intermediate work ineligible for candidate acceptance; defer candidate success and `GREEN` until every required stage and guard check succeeds. Make allocation failures fatal throughout the projection call tree.
2. **P1 — Repair receipt compatibility.** Separate shared ephemeris identity from body-specific backend attestations. Prove that receipts from the actual producer pass the driver and consumer for all eight bodies while genuinely mixed provenance refuses.
3. **P1 — Make the memory guard mandatory and effective.** Reject disabled, invalid and unsafe limits; refuse when the limit cannot be applied. Establish headroom for the whole container, including staging and parent/native allocations. Measure and disclose all retained-state slopes.
4. **P1 — Rebind consumed coverage to each receipt.** Compare each body’s actual coverage digest with its receipt, and validate the searched partition identities and completeness—not merely counts and horizons.
5. **P1 — Finish redaction.** Parse libpq escaping correctly, handle secrets spanning output boundaries with bounded streaming state, and route every diagnostic through the redactor.
6. **P2 — Replace the remaining test blind spots with behavioral checks.** Cover actual receipt production, altered per-body coverage, unapplied/disabled guards, failures after candidate insertion, swallowed allocation failures, overlapping-contact growth and actual writer-state retention. Preserve the successful identity/dedupe/digest mutation checks and add minute-boundary cases.

**Verification and what I could not verify**

- Direct read-only pytest: **17 passed, 52 deselected** in the streaming module; neighbouring modules: **35 passed, 16 deselected**. Runs used `python3 -B -m pytest -q -p no:cacheprovider`, disabled plugin autoload, `--noconftest` and `--capture=sys`.
- File-dependent counterexamples were replayed with in-memory filesystem fixtures. The real child’s file handshake was replaced with a pipe handshake. These are controlled replays, not an ordinary full-suite run.
- **Ten mutations were detected**, including all seven round-2 mutation cases, both production ID entry points, removal of conditional upload protection and reversion of integrity-subclass handling.
- No database, GCS service, Cloud Run job or century enumeration was accessed. Actual PostgreSQL transaction behavior, GCS concurrency, container RSS/OOM behavior, image dependencies, pinned ephemeris availability and live `4.0` state remain unverified.

No files were created, edited, moved or deleted. No git write command was run. Neither prohibited tree was accessed.

