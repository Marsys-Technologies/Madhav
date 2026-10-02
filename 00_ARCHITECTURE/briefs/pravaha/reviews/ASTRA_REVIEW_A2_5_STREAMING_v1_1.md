---
artifact: ASTRA_REVIEW_A2_5_STREAMING
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 48cad9f36
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** Exact chart/generation enforcement is closed. The other five amendments are partly closed: the rework improves streaming insertion and detects post-finalization corruption, but still lacks bounded memory across the complete chain, verified input provenance/completeness, comprehensive credential redaction, collision-safe staging, and the required mutation-sensitive tests.

Reviewed `804c2e977 → 48cad9f3657727c68734131ec7d9401458061b63`, after reading the round-1 review. Findings below distinguish observed probe results from unverified production behavior.

**Closure table**

| Original amendment | Status | Evidence and independent rerun |
|---|---|---|
| **1. Bounded memory end-to-end, including projection** | **PARTLY CLOSED** | [Batched insertion](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/services/gochara_kernel/ledger.py:414) now streams without retaining all rows or IDs. With 1,000-row batches, my 20,000/40,000-episode probes peaked at **1,818,179/1,820,873 bytes**. However, [projection accumulates every contact for a class](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:1042): 20k/40k/80k contacts retained **11.4/22.7/45.4 MiB before solving**. [Class-context preparation still uses `fetchall()` and retains all class instants](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06a_class_context.py:77); its corresponding probe grew **3.07/6.15/12.31 MB**. The complete chain remains input-sized. |
| **2. Finalized manifest preventing incomplete or mixed input from succeeding** | **PARTLY CLOSED** | [Object-stat verification before commit](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:600) correctly rejected clean truncation and missing objects: exit **3**, no commit, no `GREEN`. But [static verification](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:338) does not validate the snapshot, coverage completeness, declared partition count, actual episode body, or object provenance. With consistent checksums, empty bodies, empty coverage, shortened coverage horizons, and a Sun object containing Mercury contacts all returned **0**, called commit, and emitted **`GREEN`** through an in-memory evidence sink. |
| **3. DSNs redacted in every log and diagnostic** | **PARTLY CLOSED** | [Command logging](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:155) redacts `--dsn`, but child stdout/stderr pass through unchanged. [The redactor](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/common.py:53) only handles URI user-info passwords. My synthetic secret survived valid URI `?password=…` and libpq `password=…` forms, injected child stderr, and the [pre-connection manifest-error diagnostic](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:552). |
| **4. Canonical chart and `'4.1'` enforced before work** | **CLOSED** | [The century driver’s guards](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:205) enforce the complete canonical UUID and exact generation. Another UUID, canonical-chart `'4.0'`, and canonical-chart `'5.0'` each returned **3**, with zero subprocess calls and without reaching the instrumented filesystem check. |
| **5. Fresh retry prefixes or validated resume** | **PARTLY CLOSED** | Existing nonempty local directories are rejected, and ordinary retries at different timestamps receive different prefixes. But [run identity has only second resolution](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:218), while [uploads have no create-only precondition](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:144). Two simulated containers starting in the same second reused one remote prefix. The second attempt overwrote Sun, then failed at Mars, leaving the first finalized manifest present with a now-invalid Sun checksum. |
| **6. Precise equivalence and mutation-sensitive tests** | **PARTLY CLOSED** | [The revised definition](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:42) correctly qualifies digest equality on controlled metadata and supplies a total ordering. My eight-body fixture, including aliases, divergent citations, and no-exact contacts, reduced **24 inputs to 16 survivors** with equal IDs and equal results from the real `_canonical_row_set()` function over simulated database JSON rows. However, [the committed “real ledger digest” test](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/tests/l3/gochara/test_step06_century_stream.py:924) still uses its own digest helper. Constant real digests, constant contact IDs, and disabled deduplication survived my functional-test replay. |

The manifest gap is substantive. [Its `input_snapshot`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:346) contains configuration/path labels, not bound source snapshots or ephemeris checksums. Removing it entirely—or setting its orb to `999` while building with `5.0`—still earned `GREEN`. Each [enumerator independently reads current source data](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py:1274); the parent does not establish that those reads belong to one snapshot.

Checksums now prove that consumed bytes match the finalized declaration. They do not establish that the declaration represents complete, consistent enumeration. Missing dedupe sidecars also went unchecked.

**Regressions and additional defects**

- **P2 — A later attempt can invalidate finalized remote artifacts.** The same-second collision above is specific to the new staging design. Local-directory checks cannot protect a shared bucket across separate containers. Checksum verification subsequently rejects the damaged artifact, but the promised fresh-prefix and finalized-artifact guarantees do not hold.
- **P2 — The new duplicate-error handler misses actual PostgreSQL duplicate exceptions.** [The handler compares the exact class name to `"IntegrityError"`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py:626). Injecting the installed psycopg’s `IntegrityError` returned **5**; injecting its `UniqueViolation` subclass escaped unhandled, producing the ordinary CLI exception exit instead of **5**. Both paths rolled back. This is an incomplete new error-handling branch, not evidence of a publication bypass.
- **The unbounded staging route remains available.** [Omitting `--gcs-prefix`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2768b/platform/python-sidecar/scripts/kala_gochara_cutover/century_run.py:305) retains every body locally while this driver still requires the full-century horizon. Its “local rehearsal” label does not impose a smaller workload.

**Published `'4.0'`: code-level protection is preserved.** The chain contains no publication or flip invocation. The existing published-generation guards remain intact, and my real-function probes refused contact, coverage, candidate, and window mutations against a simulated published `'4.0'` before any row-changing SQL. This review itself touched no database. **Live `'4.0'` contents were not independently verified.**

Verification results:

- Direct read-only pytest run: **6 passed, 28 deselected**, using `python3 -B -m pytest -q -p no:cacheprovider`, disabled plugin autoload, `--noconftest`, and `--capture=sys`.
- All **34 test functions passed** when filesystem fixtures were replaced with in-memory I/O. This was a controlled replay, not an ordinary full pytest execution.
- Mutation replay covered **33 functional tests**, excluding the memory measurement:

| In-memory mutation | Result |
|---|---|
| Disable object-stat verification | Detected: 2 failures |
| Omit Ketu from driver body set | Detected: 1 failure |
| Skip GCS uploads | Detected: 1 failure |
| Disable command redaction | Detected: 1 failure |
| Constant real manifest digest | **Survived: 33 passed** |
| Constant contact ID | **Survived: 33 passed** |
| Disable deduplication | **Survived: 33 passed** |

**Ranked merge-blocking amendments**

1. **P1 — Finish the complete-chain memory bound.** Stream class-context preparation; bound projection’s retained contacts, intermediate series, and report data. Require external staging for the century path. Demonstrate the resulting bound with growing synthetic inputs, including one disproportionately large class.
2. **P1 — Make manifest completeness and provenance verifiable.** Bind enumeration completion receipts, actual body identity, source snapshot/fingerprints, ephemeris checksums, configuration, coverage partitions/horizons, and required dedupe provenance. Reject absent or inconsistent bindings before success; an empty or partial object needs a verified enumeration explanation.
3. **P1 — Complete diagnostic redaction.** Cover valid libpq and URI credential forms, child output, early validation errors, connection failures, and uncaught-exception reporting. Preserve streaming when handling child logs.
4. **P2 — Guarantee fresh, immutable attempt artifacts.** Use collision-resistant execution/attempt identities, exclusive local staging creation, and conditional remote creation. A failed attempt must not overwrite objects referenced by an earlier finalized manifest.
5. **P2 — Test actual identity, dedupe, digest, and end-to-end behavior.** Invoke the production digest function with controlled metadata and explicit expected identities/survivors. Add behavioral tests for the counterexamples above; ensure the surviving mutations fail.
6. **P2 — Correct exception classification.** Recognize psycopg integrity subclasses or appropriate SQLSTATEs, and verify actual `UniqueViolation` routing to the documented exit code.

**What I could not verify**

No database, GCS service, Cloud Run execution, century enumeration, or live published-generation state was accessed. Actual PostgreSQL constraints/rollback, database JSON encoding, GCS concurrency behavior, container peak RSS, image dependencies, bucket permissions, and pinned ephemeris availability remain unverified. SQL recorders establish application calls, not database acceptance.

No files were created, edited, moved, or deleted. No git write command was run. Neither prohibited tree was accessed.

