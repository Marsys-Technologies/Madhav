VERDICT: REJECT

**Not mergeable under the stated contract.** The seven original failures are substantially corrected, but ordinary builds still change, station records contain incorrect evidence, and the missing-LEL-ID report omits one valid case.

Reviewed local `origin/main` **`2c117ba1a` → HEAD `57c45f598`**, including the round delta from `4f9ccfafc`. No network, database access or file modifications.

**Merge blockers**

1. **Ordinary-build vectors are not byte-identical to main.**  
   [input_vector.py:54](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/input_vector.py:54) adds `stretch_sink` and `horizon` to the unconditional implementation identity. The edited writer, certifier and vector module are also hashed.

   **Replay:** identical ordinary-build inputs, using each revision’s actual module-source hashes, produced differences at exactly:

   ```text
   implementation.evaluation
   implementation.geometry
   ```

   Neither vector contained `horizon_basis`; they nevertheless differed. The geometry digest changed from `e041874e977d…` to `e1f71b63caba…`; evaluation changed from `b4a08e744205…` to `3b95a416073f…`.

   This fails the explicit byte-identity requirement. Preserving stale implementation hashes would conceal changed code, so that is not an acceptable repair.

2. **The state guard changes markerless builds.**  
   [ka_gochara_v5.py:1032](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1032) calls `_require_building` unconditionally.

   **Replay:** no marker; configuration containing only the pinned `chart_id` and real `birth_params`; throughput state `error`; `rules` substep. With ephemeris resolution and rule persistence stubbed identically, main reaches rule seeding; HEAD raises `asset_not_building`. The added state read also executes when the ordinary build is healthy.

   The guard is appropriate for the measuring build, but its current placement violates the requested isolation of non-measuring builds.

3. **Station-seam fields are present but can be wrong.**  
   There are two independently reproduced cases:

   - [ka_gochara_v5.py:472](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:472) reports spline extrema. Main’s [substrate.py:564](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/substrate.py:564) stores the refined station instant. Using checksum-verified local ephemeris files, Mercury’s February 2026 station was **`06:47:43.801163` in the sink versus `06:47:30.707813` in the stored-path computation**, on February 26 UTC: **13.093350 seconds apart**. MB-2.3 requires the station row’s `t_exact` to equal `station_at`. This was a local computation, not a database readback.
   - [stretch_sink.py:145](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/stretch_sink.py:145) substitutes the horizon interval for missing `full_interval`. For `120 − 0.5 + 0.02d²`, with a matching ledger contact and horizon starting February 28, the whole stretch starts **February 20**, but the seam reports **February 28** as its full start while also declaring `clipped_by_horizon=["start"]`.

4. **`rows_without_lel_id` does not report every such row.**  
   [horizon.py:322](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/horizon.py:322) builds this list from `others`, after removing the birth row.

   **Replay:** birth row `{event_id:"birth-no-id", event_date:1984-02-05, domain:"other/birth", date_confidence:"exact", provenance_lel_id:null}`, plus the valid 1998 event. Derivation succeeds, correctly identifies the birth row, but returns **`rows_without_lel_id=[]`**. The amendment requires every missing-ID row to be reported. Birth exclusion from start selection must not exclude it from this report.

**Disposition of each round-1 blocker**

| # | Result | Replay and evidence |
|---|---|---|
| 1. Horizon isolation | **Partly resolved** | [ka_gochara_v5.py:636](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:636) restores ordinary `DEFAULT_HORIZON` exactly: `[1998-01-01, 2026-04-17)`. Real runner configuration reads no LEL and receives no basis; an unusable log cannot affect that horizon. Both older shapes retain their bounds. Full vector identity still fails as described above. |
| 2. Sink invented contacts and anomalies | **Resolved for the reported failures** | [contact_certify.py:224](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/contact_certify.py:224): constant Venus longitude `180°`, target `point:120.0`, no reconstructed interval and ledger contact `[2026-02-28, 2026-03-02)` now produces `invented/ledger_contact_not_reconstructed`; the certifier returns successfully. A half-covered reconstructed interval produces boundary-anomaly and invented records, without treating it as a plain contact. The ordinary policy still rejects these inputs. Environment failures remain exceptions. |
| 3. Schema, ID recipe and vocabulary | **Original defects resolved** | [stretch_sink.py:100](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/stretch_sink.py:100) now uses `%.3f`, residence `0.000`, the specified UUID transformation, and the required fields. The closed reason vocabulary and extension-detail strings match. Independently recomputing the original Venus near-miss example gives **`407dbb76-bd2c-8990-82fd-08a51dcf1497`**, matching HEAD. Input-order hardening remains below. |
| 4. Station seam | **Partly resolved** | [stretch_sink.py:142](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/stretch_sink.py:142) requires at least one overlapping contact. The original rootless parabola with no contacts now emits only `near_miss`, never a seam. Positive seams carry both fields, but their values fail in the cases above. |
| 5. Birth identification | **Resolved** | [horizon.py:246](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/horizon.py:246) requires the birth date and the single named domain constant `other/birth`. The old `domain="other/other", provenance_subcategory="birth"` input no longer identifies a birth row. |
| 6. Mid-build comparison order | **Resolved for the reported input** | [ka_gochara_v5.py:610](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:610): on the actual pinned chart, removing the 1998 event after pinning now produces **`horizon_basis_horizon_changed`** when 2007 becomes first. Before a basis is pinned, the same changed log fails planning with `horizon_derivation_disagrees_with_ruling`. |
| 7. Historical teardown eligibility | **Resolved** | The requested two-file diff is empty. I additionally generated old-shape stamps with **main’s validator**, then passed them through HEAD’s shared proof: both original-run proof and reconstruction succeed, with identical marker digests and components. See [v5_small_test_shared.py:148](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/scripts/v5_small_test_shared.py:148). |

**Eight-row readback replay**

This is the supplied eight-row sample; the readback does not provide their complete stored `event_id` strings.

| Row | Treatment |
|---|---|
| 1 — birth-date psychological interval, exact, no LEL ID | Excluded; reported in `rows_without_lel_id` with its event ID and `1984-02-05`. It is not the birth row. |
| 2 — `EVT.1984.02.05.01`, `other/birth` | Set aside as the birth row. |
| 3 — `EVT.1993.XX.XX.01`, exact | Excluded; reported in `flag_exact_but_id_undated`. |
| 4 — `EVT.1995.XX.XX.02`, exact | Excluded; reported in `flag_exact_but_id_undated`. |
| 5 — `EVT.1995.XX.XX.01`, year-only interval | Excluded; not in the exact-flag discrepancy list. |
| 6 — `EVT.1998.02.16.01`, exact, matching stored date | First qualifying event. |
| 7 — `EVT.1998.XX.XX.02`, exact | Excluded; reported in `flag_exact_but_id_undated`. |
| 8 — `EVT.2000.XX.XX.01`, exact | Excluded; reported in `flag_exact_but_id_undated`. |

Result: **`[1998-01-01T00:00:00+00:00, 2084-02-05T00:00:00+00:00)`**, basis `first_dated_event`, **six non-birth exclusions**, eight consumed rows.

The exact-flag-only reading starts `1984-01-01`; the ID and conjunction readings start `1998-01-01`. All three shape readings start `1998-01-01`.

The implementation correctly requires exact confidence **and** a fully dated provenance ID **and** equality with the stored date; it never falls back to `event_id`. I also replayed missing-ID non-birth rows under all three supported confidences: all were excluded and reported. Zero rows use the rebuild date; a birth-containing log without a qualifying non-birth event raises `horizon_underivable_log_has_no_dated_event`. The birth-row reporting exception is blocker 4 above.

**Every changed execution path with no slice marker**

| File / edit | Behavior against main |
|---|---|
| Writer imports and measuring constants, lines 50–183 | New modules load. No horizon derivation occurs, but their inclusion affects implementation identity. |
| `_test_slice`, line 411 | Same early return when no marker exists; new marker validation is unreachable. |
| `_effective_horizon`, line 636 | Same behavior, including explicit `horizon=None`; its change is explanatory text. |
| `_require_building`, line 1032 | **Different:** additional database read and refusal; blocker 2. |
| Manifest basis keyword, line 1123 | `_horizon_basis(ctx, None)` returns `None` without reading LEL or pinned basis. Same serialized fields, apart from implementation identity. |
| Live-check basis keyword, line 831 | Returns `None` for the ordinary path. No added LEL derivation. |
| Certification plumbing, lines 1288–1324 | Passes `stretch_sink=None`, policy `raise`; emits no structured sink and adds an empty note. Same ordinary certification result/refusals. |
| Certifier defaults/forwarding, lines 279–391 | Policy validation executes; default `raise` follows the original comparison. No collection branch executes without a sink. |
| Graze refactor, lines 88–193 | The public wrapper returns the same graze result; added reason/detail bookkeeping does not change decisions. Ordinary writer certification does not enter graze classification. |
| Vector module lists, lines 54–69 | **Different:** unconditional geometry/evaluation identity; blocker 1. |
| Vector assembly/build/replay/live optional basis handling, lines 223, 449, 518, 537 | Absent basis remains absent for ordinary vectors. Equivalent field behavior given identical implementation inputs. |

**Stamp, verification, seal, publication and serving**

I found **no new bypass** in the inspected paths:

- The manifest receives `stored_scope="test_slice"` and the validated marker component at writer lines 1121–1123. Scope normalization changes a separate dictionary, not the stored stamp.
- [verification_job.py:180](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/verification_job.py:180) refuses either stamp.
- [ledger.py:623](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/ledger.py:623) explicitly refuses publication; its conditional update also excludes both stamps.
- [seal_flow.py:58](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/services/gochara_kernel/seal_flow.py:58) publishes before invoking the SQL seal. The SQL completeness check also requires `stored_non_moon`.
- [register_gochara_contact_ledger.ts:338](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:338) refuses the slice before contact/coverage queries.

The writer’s internal checks do not persist final verification rows.

**Dispatch and teardown**

The requested command returned no differences:

```text
git diff origin/main HEAD -- platform/scripts/teardown_v5_small_test_job.py platform/scripts/v5_small_test_shared.py
```

Every dispatch edit is accounted for below; references are to [dispatch_v5_small_test_job.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/scripts/dispatch_v5_small_test_job.py).

| Lines | Change and judgment |
|---|---|
| 67–79, 116, 263–264 | Marker documentation, usage and function documentation describe the new shape. Appropriate. |
| 228–230 | Adds `SLICE_MARKER_KEY` and `all_classes_full` to the run list. Appropriate; writer/list agreement remains enforced. |
| 278–280 | Defaults the new shape to `MEASURING_HORIZON`; preserves `one_class_full`’s original default. Correct. |
| 281–283 | Updates the missing-bound explanation; both-or-neither validation remains intact. |
| 352–358 | Updates CLI help and choices. Appropriate. |
| 621–631 | Adds the required dry-run explanation. It currently also prints for the older shapes, whose horizons are **not** checked against a database derivation. Scope that sentence to `all_classes_full`; this is a reporting correction, not a weakened refusal. |

No admission, ownership, locking, transaction, registry-cap or refusal predicate changed directly in dispatch. The 28,800-second expectation is already on main.

**State guard and evidence limitations**

The guard itself is read-only: a plain `SELECT` on the caller’s connection, no throughput row lock, no writer commit/close, skip on dry run or absent row. Its savepoint handling preserves the runner’s `writer_exec` rollback boundary. I found no new row-lock cycle with timeout marking; database concurrency was not exercised. The final in-flight-substep/finish race remains the contract’s acknowledged residual.

The fired-cap test at [test_mb_real_db.py:241](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-mbA3x/platform/python-sidecar/tests/l3/gochara/test_mb_real_db.py:241) now uses the measuring shape and asserts failed/error states plus an incomplete prefix. It also requires a scheduler-message substring. Its post-process observations cannot establish “never transiently lit” or prove that the surviving worker reached and was stopped by the guard. Removing the guard could still pass if process exit kills the worker first.

The lit-over-error tests use state, not stored error text, but construct those states manually. They establish teardown handling, not the occurrence or prevention of the runner race.

**Hardening and test claims that remain unearned**

- The “byte-identical” test at `test_mb_horizon_shape_guard.py:232` compares two **HEAD** assemblies with supplied fixture implementation inputs. It would pass despite blocker 1. The database test at `test_mb_real_db.py:82` checks absence of `horizon_basis`, not equality with main.
- `test_mb_stretch_sink.py:453` checks source strings rather than executing a class through the writer’s collection/logging path.
- Reversing reconstructed intervals before `compare_contact_sets` still reverses their assigned ordinals and IDs: line 244 enumerates input order. Production reconstruction currently supplies sorted intervals; the reversal tests operate after ordinal assignment. Harden the helper/test to prove the contract’s order-independence claim.
- `test_a53_gochara_v5_writer.py:136` still injects `horizon`, which the runner does not supply, and retains the stale comment that absence means derivation. The newer ordinary-build test uses the correct runner shape.
- `test_mb_horizon_shape_guard.py:338` tests measuring-plan equality without birth parameters and with an explicit horizon. That bypasses the real derivation path.
- The mutation harness now distinguishes several crash classes, an improvement. I did not run it because it rewrites source files.

The steward’s L2-prelude question: this writer does **not** invoke `bind_l2_exact_inputs`. Its snapshot stores consumed L1 fact IDs, selected daśā-row IDs and digests through `InventoryStore.insert_snapshot`; it does not copy the whole L2 input closure. Pinned-chart row counts were not measured.

**Verification performed:** **127 pure tests passed**, plus **35 selected dispatch/teardown tests using recording fakes**; independent main-versus-HEAD vector and historical-marker comparisons; original-input replays; local station calculations with verified ephemeris bytes.

**Not verified:** the remaining 55 production LEL rows, actual stored station rows, database integration/concurrency, deployed migrations or privileges, CI, production timeout behavior, complete build execution, independent verifier recount/agreement, golden capture, deployment or operational teardown.

