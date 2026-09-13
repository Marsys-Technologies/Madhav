---
artifact: MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD
version: "1.0"
status: VALIDATION_COMPLETE_PRODUCER_READY_BLOCKED
produced_on: 2026-09-13
implementation_commits:
  - c047d01a4
  - 30711044b
  - 7c5eb1dce
review_owner: independent read-only reviewer
---

# L0 validation and review record

## Executed checks

| Check | Result / raw exit | Meaning and negative detector |
|---|---|---|
| focused Python semantic/resource/service/arc suite | final `111 passed`, exit 0 | digest tamper, collision, unknown/ambiguous identity, released-reference integrity, physical variants, forbidden personal fields, state/scope/map mutation, invalid instant/location/context, backend state, cross-L0-service Swiss-state contention and cross-version deletion detectors |
| focused TS + Vidhi negative suite | `30 passed`, exit 0 | release alias/variant, invalid house, generated 36+4 cardinality, MCP bridge failure and induced Vidhi drift detectors |
| `npx tsc --noEmit` | exit 0 | producer adapters compile against repository types |
| targeted ESLint | exit 0 | five changed TS/test files satisfy lint |
| targeted Prettier check after formatting | exit 0 | changed TS/test files conform |
| Python `compileall` on changed modules | exit 0 | changed Python modules compile |
| Vidhi registry parity gate | PASS, 14/14 floors, exit 0 | existing TS/Python/Ω8 parity and known reservation remain detector-backed |
| registry parity DB-free self-test | 4 clean fixtures + 3/3 injected mutations caught, exit 0 | alias, SSoT drift and unresolved producer-value failures turn the status false |
| broad L0 service/writer suite | final `383 passed, 34 skipped, 2 failed`, pytest exit 1 | both failures reproduce standalone in untouched Muhūrta writer/tests; `git diff --quiet HEAD --` those two files returned 0 |
| live registry parity | unavailable, exit 1 | `DBURL`/`DATABASE_URL` absent; no live population/health claim made |
| repository governance drift preflight | 79 existing MEDIUM/LOW findings, exit 3 | no finding path intersects this packet; report retained at `/private/tmp/madhav-data-plane-l0-drift.*` |
| repository schema preflight | 42 existing MEDIUM/LOW violations, exit 3 | historical global hygiene backlog; no acceptance pass claimed |
| `git diff --check` | exit 0 before implementation commit | no whitespace-error finding |

The two Muhūrta failures are not relabelled as passes. Both tests replace
`swisseph` with a bare object but the unchanged writer imports
`brahmagyan.l0_ephemeris`, whose unchanged module requires real Swiss constants
before the monkeypatched failure point. They therefore fail before exercising
the assertion. This is a pre-existing test-isolation defect in a protected,
unchanged component and not evidence that a changed producer failed.

## F01-F28 disposition

| IDs | Stage result | Detector/evidence |
|---|---|---|
| F01-F02 | PASS at L0 producer boundary | six-layer ownership retained; slice lineage stops at explicit source gap and declares later owners |
| F03-F05 | PASS | legacy comparison names prevented errors; epistemic classes, identity, provenance and ancestry separation recorded |
| F06-F08 | PASS | five slice states map to the required completeness distinctions; odd/even/recursive/qualification fixtures and method boundaries are executable tests |
| F09-F10 | PASS for changed components/interface | release/slice generations, affected adapters, retained arc versions and rollback recorded; no downstream identity mutation |
| F11 | PRODUCER DESCRIPTION ONLY | 40-identity discovery description corrected; retrieval/query/channel chain remains read-only and `NOT_REACHED` |
| F12-F14 | PASS | operator, maturity and delivery states explicit; only `PRODUCER_READY` is eligible at close |
| F15-F18 | BOUNDARY PASS / NOT APPLICABLE TO MUTATION | no observation, event-derived feature, claim, evaluation or protected data entered L0; forbidden personal-field tests |
| F19-F21 | PASS | 40/40 preservation/disposition, restricted-capital/source-rights limits and zero retirement/migration |
| F22 | BLOCKED for process-wide numerical repeatability | changed adapters/inputs/digests/rollback pass, but an out-of-scope live transit route can mutate Swiss global state during a non-Lahiri request |
| F23 | APPLICABLE PROOFS PASS EXCEPT PROCESS-WIDE CONTENTION | qualification, computation, relevant/irrelevant input, duplication, missingness, boundary, omission, revision and simpler-baseline fixtures executed; managed channel and empirical evaluation not authorized/not reached |
| F24-F25 | PASS | computation, explanatory distinction and empirical value separated; implementation followed semantic→qualification→service→slice→acceptance order |
| F26-F27 | PASS by conformance/boundary | no orchestrator contract or L1 fact authority changed; existing writer class/upsert contracts preserved |
| F28 | PASS for claimed states; terminal is BLOCKED | tests can falsify release/slice/service/inventory states; the unowned race prevents a producer-ready label |

## DP01-DP18 disposition

| Contract | Result |
|---|---|
| DP01 | FULL producer pass: versioned identity release, Python/TS adapters, ambiguity/unknown and physical-variant tests. |
| DP02 | FULL honest-state pass: witness/rule fields and five states; exact witness absent, so `UNQUALIFIED_SOURCE` and positive `NOT_REACHABLE`. |
| DP03 | SUBSTRATE contract implemented, but process-wide repeatability blocked by an out-of-scope Swiss-state mutator; no chart fact. |
| DP04-DP05 | Vocabulary/qualification contract only; no condition/configuration instance. |
| DP06 | Interface/ancestry fields only; no L2 graph. |
| DP07 | Context/boundary fixtures pass; terminal repeatability remains blocked across the full live sidecar process. |
| DP08-DP09 | `NOT_IMPLEMENTED`; no temporal mechanism or manifestation. |
| DP10 | Producer description pass; discovery/ranking/caller integration withheld. |
| DP11-DP12 | Demand/schema fields only; no managed-channel or delivery claim. |
| DP13-DP15b | `NOT_APPLICABLE_TO_MUTATION`; no observation/history/claim/evaluation data. |
| DP16 | FULL for changed release: typed corrections, invalidation, compatible predecessors and rollback. |
| DP17 | Fixture-level baseline comparison only. |
| DP18 | `NOT_APPLICABLE`; no artifact/model/research admission. |

## Scope and privacy proof

The three implementation commits change only 26 declared L0/direct-adapter/test/record
files. They change no L1-L5 writer, retrieval query, Paripraśna, synthesis, MCP,
workflow, migration, Product Definition, CCD, canonical manifest, campaign,
credential or secret surface. `DATABASE_URL` was absent and no private row was
read. No push, PR, merge, deployment, rebuild or database mutation occurred.

## Independent challenge

One independent read-only reviewer challenged the whole packet three times. The
first pass found five MEDIUM blockers and one documentation mismatch: contradictory
top-level qualification, naked slice IDs, proxy backend qualification, incomplete
Swiss-state isolation, a false-positive rights negative and omitted Ketu correction
language. Commit `30711044b` corrected all except cross-service state isolation.
Commit `7c5eb1dce` introduced one shared lock for the permitted ephemeris and
Pañcāṅga entry points plus a real contention negative.

Final re-review found no owned HIGH or CRITICAL and confirmed those corrections,
but retained one MEDIUM terminal blocker: live
`platform/python-sidecar/pipeline/transit_search.py` and other sidecar callers can
still mutate the same process-global Swiss state without the shared boundary.
That path is outside the immutable `may_touch` list. A non-Lahiri ephemeris request
can therefore remain non-repeatable under concurrency. `PRODUCER_READY` is not
claimed.

The smallest next authority decision is either (a) expand a new execution packet
to inventory and serialize every live Swiss setter plus its dependent calculation,
including transit search, or (b) approve process-isolated L0 numerical execution
with an explicit latency/capacity contract. The current packet cannot choose that
architecture or edit the protected path.
