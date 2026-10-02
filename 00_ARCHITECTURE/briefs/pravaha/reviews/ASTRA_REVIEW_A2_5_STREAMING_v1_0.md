---
artifact: ASTRA_REVIEW_A2_5_STREAMING
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 804c2e977
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** The implementation preserves the candidate/publication boundary, but does not deliver the specified memory bounds or an earned completeness signal. It also exposes DSN credentials and fails to enforce the authorized chart/generation scope.

Reviewed HEAD `804c2e97713f92eed3e21d4a900de23706fbb07b` against merge base `95e96d63cb8f5b58689d19f728266107f39df346`.

**Findings**

1. **F1 — P1: The century path still accumulates the complete dataset in RAM.**  
   [The runner](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:159>) retains every local body file after uploading it. On the specified Cloud Run filesystem, those files consume memory. [The reader](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:143>) then materializes and sorts **all** episode dictionaries; `ledger.write_contacts()` creates another complete normalized-row list and returns a complete ID list. The subsequent windows projection also fetches every contact and constructs additional per-class copies.

   GCS is an upload destination only: the candidate builder reads local files, and supplying a `gs://` URI produces `FileNotFoundError`. Thus uploading does not relieve the memory pressure. The implementation remains O(total episodes), and compliance with 16 GiB is unproven. The PR’s new “enumeration-only” memory disclosure does not satisfy §2’s original design.

2. **F2 — P1: A truncated or incomplete stream can earn candidate `GREEN` with full-century coverage.**  
   [The reader](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:137>) checks only whether *some* files match. It accepts empty files and any valid prefix ending at a JSON-object boundary. There is no finalized manifest binding all eight bodies, row counts, checksums, chart, generation, horizon, or input fingerprints to the coverage file.

   **Reproduced without a database:** using the real builder and ledger functions with an in-memory SQL recorder, both a one-row Sun stream and an empty stream returned `0`, committed, and emitted `GREEN` while accepting eight coverage partitions declaring the full century complete. This violates §N.8.

   These remain **candidates**, with the unpublished-digest sentinel; the probe did not demonstrate publication. Malformed JSON does fail. Clean truncation is the undetected case.

3. **F3 — P1: Every subprocess command exposes the database credential.**  
   [`_run()`](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:113>) prints the entire argument vector, including `--dsn`. A password-bearing connection string therefore enters job logs before the child’s production guard runs. An in-memory probe confirmed that a synthetic password appeared verbatim.

4. **F4 — P1: Chart `482012f1` and generation `'4.1'` are defaults/documentation, not enforced scope.**  
   [The driver’s guards](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:143>) validate the authorization marker and horizon only. Arbitrary chart IDs and generation labels pass through to every child.

   With subprocesses intercepted, another chart UUID and canonical-chart generation `'4.0'` both reached enumeration. Existing ledger guards should subsequently refuse an already-published `'4.0'`; **I found no new bypass of that protection**. However, another chart’s candidate can be written, and the driver does not enforce the requested authorization boundary.

5. **F5 — P2: Crash/retry safety depends on callers supplying a fresh directory.**  
   The default workdir is deterministic, existing directories are accepted, and [episode output always appends](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:1188>). Reusing an output after a successful or interrupted invocation retains prior rows.

   Writing the same two episodes twice produced four reader rows but only two distinct contact IDs. The existing database primary key should reject that rebuild rather than deduplicate it. A partial final JSON object instead makes the appended stream unparsable. Fresh Cloud Run filesystems avoid reuse, but the driver does not establish or verify freshness itself.

6. **F6 — P2: The asserted byte/digest/order equivalence exceeds the demonstrated guarantee.**  
   For a fresh, fixed-input, one-file-per-body run, the core episode transformation looks sound: an adversarial eight-body fixture containing duplicate aliases, divergent citations, and no-exact contacts reduced 24 inputs to 16 survivors with identical ordered episodes and contact IDs.

   The broader claim fails in three respects:

   - Monolithic coverage is globally sorted by `partition_key`; the runner concatenates coverage in `PERSISTED_BODIES` order. Coverage insertion order differs.
   - `(t_in, body, relation)` is not a total ordering for arbitrary shards. Two distinct same-key contacts appeared as `Z,A` monolithically and `A,Z` after glob ingestion.
   - [The real manifest digest](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/services/gochara_kernel/ledger.py:502>) includes complete database rows, including `computed_at`, `build_id`, and manifest linkage. Calling the real normalization/digest functions twice with the same episode and build ID produced the same contact ID but different digests solely because `computed_at` changed.

   The volatile digest behavior predates this PR; the newly added unconditional equivalence claim is nevertheless incorrect. [The new tests’ digest helper](</private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768/platform/python-sidecar/tests/l3/gochara/test_step06_century_stream.py:107>) hashes episode dictionaries, not the actual ledger representation.

**Failure containment that does hold:** the inspected chain never calls `publish()` or the flip step. Existing generation-scoped guards protect published rows. Injected child exits `5`, `6`, and `7` propagated unchanged without `COMPLETE`. Malformed streams fail before database connection. Candidate writes use one transaction with rollback handling; actual database crash behavior was not exercised.

**Test and mutation evidence**

The unmodified touched test file was run with:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -B -m pytest -q -p no:cacheprovider --noconftest --capture=sys platform/python-sidecar/tests/l3/gochara/test_step06_century_stream.py -k 'test_century_run_refuses_without_env_marker or test_century_run_refuses_non_pinned_horizon or test_century_run_imports_persisted_bodies'
```

Result: **3 passed, 9 deselected**. `--noconftest` avoids the root autouse fixture that creates a directory; the deselected tests use filesystem fixtures.

Separately, all 12 test functions passed with filesystem operations replaced by memory-backed I/O. In that replay:

| In-memory mutation | Result |
|---|---|
| Remove reader sorting | Detected: 3 failures |
| Truncate instead of append | Detected: 1 failure |
| Skip Ketu in the driver | Survived: 12 passed |
| Remove GCS upload | Survived: 12 passed |
| Disable deduplication | Survived: 12 passed |
| Replace contact-ID computation with a constant | Survived: 12 passed |
| Replace manifest-digest computation with a constant | Survived: 12 passed |

The tests detect basic serialization mechanics but do not establish the advertised end-to-end guarantees.

**Ranked merge-blocking amendments**

1. **Bound the complete execution’s memory:** implement actual GCS-backed consumption and bounded insertion within one candidate transaction; remove full-dataset materialization and account for projection memory. Demonstrate the memory bound with permitted synthetic workloads.
2. **Require a finalized input manifest:** verify every expected body, count, checksum, identity, horizon, input snapshot, and coverage binding before candidate success. Missing, truncated, mixed-run, or unreadable objects must prevent `GREEN`/`COMPLETE`.
3. **Redact DSNs before logging**, including failure diagnostics.
4. **Enforce the exact canonical UUID and `'4.1'`** before filesystem work or subprocess execution.
5. **Make retry staging explicit and safe:** enforce fresh run directories/object prefixes or implement validated resume semantics; distinguish incomplete output from finalized output and preserve required dedupe provenance.
6. **Define and test equivalence precisely:** cover coverage ordering, tied keys, dedupe/identity, and the real ledger digest with explicitly controlled metadata. Add mutation-sensitive tests for omitted bodies, partial streams, upload/read failures, scope violations, and retries.

**What I could not verify**

No database, GCS, Cloud Run execution, century enumeration, or live published-generation state was accessed. Actual peak memory, PostgreSQL rollback/constraint behavior, bucket permissions, image packaging, and pinned ephemeris availability remain unverified.

The requested architecture-path spec was absent in both locations. I used the original [fallback spec](</Users/Dev/madhav-l3/pravaha-a/platform/python-sidecar/scripts/kala_gochara_cutover/CENTURY_CLOUD_RUN_JOB_SPEC_v1_0.md>) and compared it with the PR’s amended copy.

No files were written, no git write commands were run, and neither prohibited tree was accessed.

