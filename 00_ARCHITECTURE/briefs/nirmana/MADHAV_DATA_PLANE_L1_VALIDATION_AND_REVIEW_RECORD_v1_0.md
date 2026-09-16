---
artifact: MADHAV_DATA_PLANE_L1_VALIDATION_AND_REVIEW_RECORD
version: "1.0"
status: PASS
implementation_commits:
  - 7cabc0cfd1eae83f0a1054132d3c850c6b760153
  - 3cb1a84ae
  - bcda11997
  - 0fc45813e
  - b2c4f1d7f
  - a9c44c298
accepted_base: f6fed12c794224329f6b3b436f8b1b814499d06d
review_verdict: PASS
---

# L1 validation and review record

## Executed local evidence

| Command/evidence | Result |
|---|---|
| `schema_validator.py --handshake /private/tmp/madhav-data-plane-l1-session-open.yaml` | exit 0; 0 violations after exact same-session scope amendments. |
| initial `pytest -q ga_writers/__tests__/test_l1_data_plane_contracts.py` | 29 passed; two dependency deprecation warnings. |
| corrected contract/runtime/orchestrator/dasha/transit focus | 90 passed; exit 0. |
| corrected sensitive/structural/transit focus | 348 passed; exit 0. |
| final focused contract/condition/COPY suite, including full condition writer regressions | 147 passed; two dependency warnings; exit 0. |
| bounded GA/L1 suite (51 files; inherited uncollectable Vāstu module excluded) | 927 passed; 33 warnings; exit 0. |
| `validate_data_plane_l1_contract.py` | exit 0; `PASS`; 19/19 runtime boundaries; zero findings; golden slice digest `25c46b55…8d3279`; 11 row-trigger tables plus set-based dasha capture. |
| initial broad L1 suite | 1,255 passed, 1 skipped, 7 subtests passed; 36 warnings; exit 0. |
| post-challenge broad GA suite | 1,022 passed, 1 skipped, 7 subtests passed; 5 warnings; exit 0. |
| full GA collection including `writers/__tests__` | exit 2 on inherited `test_ga_vastu.py` import error; reproduced identically at accepted base `f6fed12c7`. |
| disposable PostgreSQL 15 migration/application proof | current migration apply and exact reapply exit 0; same-input replay digest equal; two generations retained after active replacement; exact selector and head rollback pass. |
| dasha post-pass accounting proof | three source rows captured before and after concurrency update as six immutable typed revisions; two chart-fact sentinels captured; final partition receipt records the adapter-returned two and generation completes. |
| full dasha persistence-volume proof | Original 536,000-row typed capture/digest completed in 9.83 seconds. With canonical semantic hashes: fresh capture/digest 15.09 seconds; completed replay after changing all `computed_at` only 8.72 seconds; second build with identical stable rows/different build and timestamps 14.58 seconds and the same digest; selector 536,000 rows in 7.24 seconds with zero null digest or leaked build/time. Zero generic row/fact child amplification. Rejected row-trigger and JSON-envelope designs were cancelled after 72.46 and 51.30 minutes respectively. |
| condition/configuration DB proof | 25 explicitly specified condition fields from one composite row; astronomical speed, deterministic combustion and rule-derived score have distinct units/verification and actual constituent IDs. Yoga catalog content SHA, typed participant roles and observed clauses retained while admitted state stays `UNQUALIFIED_SOURCE`. |
| PostgreSQL negative controls | wrong dasha build/count exit 1; completed-generation dasha mutation exit 1 and transaction rollback; non-finite numeric exit 1; snapshot delete exit 1 with append-only rejection. |
| `compileall` on all changed Python | exit 0. |
| `provenance_inventory --check` | exit 0 after deterministic writer-digest regeneration. Protected layer-pin check remains expected exit 1; file unmodified. |
| `git diff --check` | exit 0. |
| live DB/service proof | `NOT_RUN`; `DBURL` and `DATABASE_URL` absent. |

The first broad run was 1,254 passed, 1 skipped, 7 subtests passed and one source-
lint failure. An exact detached accepted-base reproduction at `f6fed12c7` returned the
same guard failure (1 failed, 2 passed): its hard-coded allowed line numbers were already
stale. The current branch refreshed only the intended prose/lookup line pins; focused and
broad suites then passed. The detached worktree was removed.

The broader adapter-test collection also found `test_ga_vastu.py` importing
`CANONICAL_CHART_ID` from `ga_vastu_writer.py`, where the symbol does not exist. A detached
accepted-base run produced the identical collection error, so it is inherited rather than
an L1 change. The bounded post-challenge suite excludes only that uncollectable inherited
module and passes. Its temporary worktree was removed.

## Negative controls covered

- build/generation replay retains semantic fact and interval IDs;
- subject/chart/context/build/generation mismatch rejects a join;
- mean/true node and material formula/context changes remain distinct;
- zero is numeric zero, while unavailable/floored/inapplicable/unqualified/failed/
  unexplored cannot carry a normal value;
- unqualified doctrine cannot reach a formed/partial state;
- duplicate constituent roots are rejected;
- dangling/duplicate clock identity fails;
- relevant boundary perturbation changes output and irrelevant perturbation does not;
- personal/stored chart identity is rejected by the first slice;
- numerical error is a failed attempt, not empty/zero/Aries success;
- every one of the 19 runtime adapters opens/completes the same versioned producer boundary;
- failed writers do not complete a generation partition;
- active-row replacement preserves prior snapshots and same-input replay has an identical digest;
- wrong-build rows, non-finite numerics and history mutation fail closed;
- Prāṇa never attempts an invalid level-5 interval; its explicit inapplicable fact and the
  legal KP cap both write;
- incomplete structural geometry, sensitive Lagna/vara/day-night inputs and partial transit
  anchors fail before output;
- Bhāvat remains unapplied and `NOT_REACHABLE`.

## Independent read-only challenge

The first challenge on `7cabc0cfd` returned `FAIL` with no CRITICAL and owned HIGH findings:
the typed contract was slice-only rather than runtime-integrated; fact identity omitted
semantic context; active deletes could not preserve generations; non-finite JSON/numerics
were accepted; transit, structural and sensitive paths retained numerical fallbacks; the
slice had unresolved dependencies and non-recomputed sensitivity; the golden digest was
not asserted; and Prāṇa's level-5 interval could never satisfy its table constraint.

Commit `3cb1a84ae` corrects those findings with the 19-adapter runtime boundary, migration
1033, context-bound fact IDs, strict canonical numerics, complete-input gates, closed
fixture ancestry/recomputation/golden pin and the fact-based Prāṇa scope declaration.
The next challenge on `3cb1a84ae` found eight HIGH issues; `bcda11997` corrected invariant
multi-partition context, astronomical day/night, complete-generation freeze, latest-row
selection, recursive non-finite rejection, typed runtime projections, closed L0 dependency
identity and real D9 sensitivity. Its re-challenge found three HIGH issues: dasha receipt
coupling, asset-level field semantics/inexact yoga observation and catastrophic per-column
fan-out on ~536k dasha rows. Commit `0fc45813e` corrects all three with independent receipt
accounting, explicit per-field condition specifications and ancestry, typed/digested yoga
observation quarantine, and a bounded typed-composite dasha history path proven at full
cardinality. The next challenge found three HIGH issues in volatile dasha replay/digest,
cross-context condition dasha ancestry and cross-ayanāṃśa/date-truncated concurrency.
Commit `b2c4f1d7f` uses one canonical dasha payload and stored digest, constrains condition
ancestry to exact ayanāṃśa/build and evaluates concurrence with exact instants inside one
ayanāṃśa. The reviewer then identified nested source build identity as an observation-only value that
would rotate otherwise compatible condition semantics. Commit `a9c44c298` removes it from
the nested semantic period while retaining exact build selection and the enclosing observation
context; an explicit cross-build equality regression passes. The final independent
re-challenge of exact tip `a9c44c298a3b6460d676e84cd7b26468e3d2e053` returned
`PASS` with zero HIGH, MED or LOW findings. Its focused no-cache suite passed 147 tests;
its independent bounded run passed 857 tests and the supplementary scope/sentinel/
structural set passed 66. It also confirmed the 19/19 validator, provenance check, scope
boundary and later-state non-claims. The reviewer did not access a database, so the
PostgreSQL/full-volume rows above remain implementation-supplied local evidence rather
than independent deployment or integration proof.
