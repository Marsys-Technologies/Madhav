VERDICT: ACCEPT — PR 3185; ACCEPT — PR 3187.

**Both PRs are mergeable at `33cf58a9ef2f`.** The sole round-5 P2 blocker is resolved under the steward’s required unresolved-result policy. I found no new wrong-number, false-acceptance, or wrongful-refusal regression.

PR 3185’s `measuring_report.py` and both test files are byte-for-byte unchanged from `5c49c204b`. The delta changes only `near_miss_verifier.py`, its tests, and four mutation definitions.

**Round-5 blocker: RESOLVED**

The amendment requires both in-band geometry at the event and a certified continuous in-band path into the particular stretch. Failed connectedness produces `junction_membership_unresolved`. Evidence: [near_miss_verifier.py:320](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR6x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py:320), membership decision at line 380, refusal propagation at line 562.

I replayed the original smooth, Mars-speed-bounded input:

```python
TC = 2000-01-15T12:00:00Z
x = elapsed_days_from_TC
delta = 1e-7
d(x) = .5 + sqrt((sqrt(x*x + delta*delta) - .5)**2
                 + delta*delta) + 3e-6

position = 100 + d(x)
centres = [100]
orb = 1
horizon = [TC - 2 days, TC + 2 days)
```

Both analytically constructed stored rows pass `row_problems`.

| Event | Stretch 1 | Stretch 2 |
|---|---|---|
| `TC − 1 second` | Membership accepted; omission refused | `junction_membership_unresolved` |
| `TC + 1 second` | `junction_membership_unresolved` | Membership accepted; omission refused |

The false packet claiming the junction on **both** stretches returned `[]` at round 5; HEAD refuses it in both directions. The honest two-row packet also remains **unresolved for the neighboring stretch**, as the binding ruling permits—it is no longer falsely declared a junction mismatch.

The earlier probe, `d(x)=min(1.1, .75+.25*x*x)`, also passes: at both entry and exit, events 0.5 seconds inside accept membership and reject omission; events 0.5 seconds outside do the reverse. Exact-edge events remain named unresolved.

**Connectedness proof and cost**

For margin `m(t)=orb−|d(t)|`, the stated speed bound gives:

```text
m(t) ≥ max(m0 − v·s, m1 − v·(g−s))
     ≥ (m0 + m1 − v·g)/2
```

Thus the acceptance bound is sound under the stated speed assumption. Negative endpoint margins fail; unproved intervals at the 1 ms floor become unresolved. The caller’s path is at most six seconds, bounding a fully subdivided check to approximately 8,193 distance evaluations.

An additional **1,200 smooth-curve checks**, including reversed traversal and narrow excursions, produced **zero false acceptances**. Some true paths remained uncertified at the floor, consistent with the explicit unresolved policy.

The separate **60-second search-resolution limit remains named and exposed**, with `complete=False` and `verified_empty=False`: [near_miss_verifier.py:197](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR6x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py:197).

**Verification**

- **211 pure tests passed**, with repository conftests, bytecode writing, and pytest caching disabled. These cover P4 intersection—including abutting intervals and absent agents—K-B variants, class unions, contributions, scored-role filtering, horizon refusals, near-equal minima, identity/ordinal/orb checks, finite values, wrap, and clipped stretches.
- All **40 ND-H tier/kāraka cells**, additional frame/mother/version/open-point checks, and **216 bereavement K-B licence combinations** matched the authoritative text.
- The scorer uses **IST calendar dates with inclusive endpoints: 10,334 days**. The guard probe returns **4,134 / 10,334 = 40.0038707%**, triggering reversion. A window spanning `18:29Z–18:31Z` counts two scored dates and one UTC build date. Evidence: [measuring_report.py:450](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR6x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:450), `gochara_eval/registry.py:8`, `extract.py:65`, `metrics.py:80`. No `EVALUATION_PROTOCOL_v2_3` artifact was found under `00_ARCHITECTURE`.
- Missing `provenance.lel_id` still refuses by name. Valid provenance derives `1998-01-01 .. 2084-02-05`; zero rows use the rebuild date; nonempty undated logs refuse.
- Reader SQL remains parameterized SELECTs against the migration-defined names. Database tests were read, **not executed**.
- Runtime kernel imports remain: none in measuring-report or ND-H; only `contact_reconstruct` in near-miss, for the mandated ONE-band reuse. Shared-band equality tests establish consistency, not independent geometry.
- The unchanged minimum certificate remains sound conditional on the speed bound. A synthetic 31,446-day Moon sweep used **209,398 calls at 1°** and **222,555 at 3°**, approximately **0.66/0.72 seconds** with trivial callbacks.
- The mutation harness was **not run**. Static inspection found **84 mutants and two justified equivalents**; replacement targets occur once and compile in memory. Baseline success remains required. No kill-count claim was verified.

**P3 follow-up only — none blocks merge**

| Carried item | Concrete exposure and location |
|---|---|
| Finite helper arguments | Infinite clearance, NaN speed override or K-B separation: `near_miss_verifier.py:76,226`; `nd_h_tables.py:153`. |
| Marker shape validation | `test_slice=True` or `{"horizon":123}` can raise raw exceptions: `measuring_report.py:409,418`. |
| Candidate interval validation | Reversed `[tc+2s, tc−2s]` can pass through slack: `near_miss_verifier.py:548`. |
| Mutation classification | Assertion-prefixed exception messages can misclassify; nonzero exits without failures can become survived: `mutation_check_verifier_side.py:137–152`. |
| Stale claims | Obsolete fallback/convention wording and unused closest-time tolerance: `measuring_report.py:248`; `nd_h_tables.py:239`; `near_miss_verifier.py:49`. |

The checked-in new tests use stand-in stretches; my full analytical adjacent-stretch replay in both directions was additional in-memory evidence.

I did **not** verify database execution, production rows, real ephemeris accuracy/runtime, astronomical speed maxima, physical tolerance justification, builder-table equality, job wiring, stationless-body enforcement, source/precision binding, full-domain provenance, complete-build census, actual layer-on/off scored outputs, or remote PR/CI state.

No files were modified. No database or network access was used.

