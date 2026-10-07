VERDICT: REJECT

**PR 3194 is not yet mergeable.** The two round-3 mutations now fail the comparison assertions, but the replacement tests still miss required regressions, and the golden contains environment-dependent values.

Reviewed HEAD `08698ddda` against round-3 `01c181cc0` and local `origin/main` `09fd39b4d`. No files modified; no database or network access.

**Blockers**

1. **The vector test excludes more than `implementation.*`.**  
   [test_mb_ordinary_golden.py:171](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/platform/python-sidecar/tests/l3/gochara/test_mb_ordinary_golden.py:171) drops `ephemeris.platform`, `library_sha256` and `probe_digest` whenever the platform differs from the golden’s `Darwin-arm64`. This exemption applies on Linux CI and contradicts the steward’s every-component requirement.

   **Replay:** replacing all three fields with bogus values still **passed** the actual vector comparison. Use fixed inputs or an appropriate main-generated baseline while retaining comparison of every non-implementation field.

2. **The capture does not establish the real runner’s sequence or complete observable results.**  
   [test_mb_ordinary_golden.py:82](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/platform/python-sidecar/tests/l3/gochara/test_mb_ordinary_golden.py:82) constructs its own sequence; `capture()` never calls `plan_substeps()`.

   **Replays:** swapping production’s `rules`/`convention` order left capture keys unchanged. Removing every production `verify` step reduced the plan from **298 to 272**, while the capture still supplied `verify:marriage` itself.

   Additionally, line 108 captures only `rows_inserted` and `notes`. Changing a real rules result to `rows_updated=7` left that captured outcome unchanged, although the runner includes those seven rows in telemetry. Lines 159–162 remove the guard SELECT wherever it occurs, so they also accept moving it to the end.

   Freeze and compare the actual plan, capture runner-consumed result fields, and assert the guard’s position explicitly.

3. **Cursor-issued writes bypass the SQL recorder.**  
   [test_mb_ordinary_golden.py:54](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/platform/python-sidecar/tests/l3/gochara/test_mb_ordinary_golden.py:54) forwards `cursor()` directly to the underlying connection.

   **Replay:** this snapshot write reached the underlying recording double but produced **zero recorded statements**:

   ```sql
   UPDATE public.ka_gochara_search_input_snapshot
   SET generation = generation WHERE false
   ```

   Through `connection.execute()`, it was detected; through `cursor().execute()`, it was invisible. Its zero affected rows also evade the table-count comparison. Wrap cursor execution as well.

4. **The golden is not portable to a UTC database session.**  
   The fixture’s [convention digest:66](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/platform/python-sidecar/tests/l3/gochara/fixtures/mb_ordinary_golden_main.json:66) incorporates timestamp strings rendered at `+05:30`. Its [verification error:938](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/platform/python-sidecar/tests/l3/gochara/fixtures/mb_ordinary_golden_main.json:938) also compares timezone-rendered, microsecond-exact timestamps.

   **Main-code reproduction:** the convention content hashes to the recorded `71108c78…` at `+05:30`, but to `a9e053d6…` in UTC. Main’s contact-certification code reproduced the recorded error exactly at `+05:30`; the same instants in UTC produced different text.

   Neither capture nor the CI job pins the database session timezone. The platform exemption does not remove either mismatch. Pin the capture environment and regenerate on unmodified main. Separately, local Python 3.14 produced a different Swiss-library artifact hash on the same `Darwin-arm64` platform, exposing another dependency on the original environment.

**Delta and CI**

Exactly four files changed:

- `.github/workflows/ci.yml`
- `test_mb_horizon_shape_guard.py`
- `test_mb_ordinary_golden.py`
- `fixtures/mb_ordinary_golden_main.json`

The latter three are under `platform/python-sidecar/tests/l3/gochara/`. **Non-test, non-fixture, non-CI files: none. No production code changed.**

The [CI delta:1443](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA5x/.github/workflows/ci.yml:1443) only appends the new test to the existing measuring-build job. The test loads its checked-in fixture; no service, dependency, permission or timeout changed this round.

**Golden provenance**

The documented source is main commit **`75eeda4c99af8c7d9370e4bb04e29c84ad75c925`**, with the capture command recorded at test lines 3–6.

I loaded repository modules from local `origin/main` Git objects into memory and independently reproduced:

- All three golden implementation hashes from main’s source bytes and module lists. The declared commit and current local main agree.
- The convention ID, admission-orb digest, rulings digest and node component.
- The real main rules result and its complete **45-statement ordered summary**, using an in-memory connection double.
- The recorded verification error for its two missing-contact obligations.

This strongly corroborates main-derived content. **I did not reproduce the complete database-backed golden.**

The capture command itself does not enforce provenance: `GOLDEN_COMMIT` is hard-coded, so running capture on HEAD would still label its output as main. However, an unmodified HEAD capture would not reproduce the delivered main implementation hashes or guard-free statement trace.

**Mutation results**

These are offline assertion, planner and recorder probes—not a full PostgreSQL fixture run.

| Mutation | Result |
|---|---|
| Assembler returns wrong `stored_scope` | **Comparison fails** |
| Append `[ORDINARY REGRESSION]` to real writer result | **Comparison fails**, identifying `rules` |
| Swap production substep order | **Missed:** capture sequence unchanged |
| Remove production `verify` kind | **Missed:** capture still supplies it |
| Extra snapshot write through connection | **Recorder detects it** |
| Same write through cursor | **Recorder misses it** |
| Corrupt platform/library/probe fields together | **Vector comparison passes** |
| Move guard SELECT to end | **Filtered statement comparison unchanged** |

**Coverage and comparison strength**

The golden includes **all ten named kinds**, including the six the steward specified. It covers one body, one class and P2/P3 record/window paths. Its verification case ends in a geometry refusal; successful verification beyond that point is untested.

For intercepted `execute()` calls, full normalized SQL text, parameter count, statement multiplicity and ordered-sequence hash will detect changed tables, added writes and statement reordering. Excluding parameter values avoids dependence on generated IDs. The cursor and guard-position gaps remain decisive.

**Follow-ups**

- `test_mb_ordinary_golden.py:63`: UUID normalization runs after hex normalization, leaving UUID prefixes intact. The current snapshot build ID is fixed, so this is not a demonstrated current failure.
- `:127`: the “repeatable” capture test performs only one capture and checks presence, not repeatability.
- Record the full source SHA and environment provenance, and refuse generation from mismatched or modified production sources.

**Verification limits**

**51 guard/horizon tests passed** using database/network denial, disabled filesystem caches, and `--noconftest` to avoid file-writing session fixtures. `git diff --check` passed; working-tree status remained unchanged.

Not verified: full PostgreSQL capture/comparison, actual Linux x86_64/Python 3.11 CI execution, complete cross-platform floating-point reproducibility, original capture logs, successful ordinary builds, or deployment. These findings concern the tests and fixture; they do not reopen the production defects resolved in round 3.

