---
artifact: MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_VALIDATION
version: "1.0"
status: VALIDATED_INDEPENDENT_CHALLENGE_PASS
produced_on: 2026-09-13
decisions:
  - DP-SD-010
  - DP-SD-011
accepted_sources:
  - 552fa76d21406fcbb7f534afbd9600330f3a6276
  - b8e342049f0ac90e794bc3f547468a785a98d108
strategy_content_revisions:
  - d61469b6d96b956782548d36fb23f9e813e1ae98
  - a112b64a61c60ff44369ba64eee73a3445a48461
approval_pin_revisions:
  - b1a0f17eb65494f21a00fd2b22d6264da76c3c38
  - add798f6ce37893f8c7ef3e771f30e15b0fb24f2
implementation_commits:
  - e0cfad5c14a6f1c8ee30cdfec37d326c4631ffa9
  - b8e342049f0ac90e794bc3f547468a785a98d108
  - f648d5add412d8e7c99ab3afd5166210b7dda9c7
---

# L0 Swiss-state boundary validation

## Computational result

The non-test Python sidecar resolves every detector-visible direct, aliased,
wrapper and transitive Swiss/PyJHora state-dependent operation to the one
canonical re-entrant boundary. The exact source inventory contains 70 operation
owners, 76 decorated entry points, four explicit-scope owners and 80 owners in
their union. `UNRESOLVED = 0`; the shipped tree contains one `RLock()`
construction.

DP-SD-011 closes the final GA-strength split spans. Both
`_derive_ashtakavarga_shodhana_grids` and `_derive_bhava_bala` now hold the
canonical boundary from ayanamsha selection through final result copying. They
perform computation only; no database, network or sleep is inside the boundary.
No numerical algorithm, schema, unit, rounding, node, ayanamsha or event-order
semantic changed.

## Executed evidence

| Check | Raw result | Disposition |
|---|---|---|
| DP-SD-010/011 boundary suite | `18 passed, 2 warnings`, exit 0 | exact inventory; direct/alias/wrapper negatives; single lock identity; forward/reverse barriers; cache context; GA Ashtakavarga/Bhava Bala critical-span, re-entrancy and value invariance |
| DP-SD-011 GA-strength regression suite | `132 passed, 14 warnings`, exit 0 | orchestrator enrichment, GA3, D-1.5b Bhava/Ashtakavarga and L1-strength behavior unchanged |
| exact governed focused L0 suite | `136 passed, 5 warnings`, exit 0 | original semantic/resource/service/arc proof plus the hardened boundary suite |
| exact broad L0 service/writer suite | `383 passed, 34 skipped, 2 failed, 5 warnings`, exit 1 | only the two unchanged Muhūrta isolation tests fail before their intended assertions |
| standalone current versus `552fa76d2` baseline | same two test identities and same pre-assertion `AttributeError` from bare-object `swisseph` substitution | inherited test-isolation defect reproduced on both revisions; neither GA-strength function or its test was changed by that baseline |
| changed-module `compileall` | exit 0 | syntax/import compilation passed |
| amendment/addendum scope matcher | zero outside `may_touch`; zero `must_not_touch` hits | implementation stayed inside the authorized union |
| `git diff --check` | exit 0 | no whitespace-error finding |
| live database parity | `NOT_RUN` | `DBURL` and `DATABASE_URL` absent; no live population, deployment or health claim |
| independent read-only challenge | PASS; `150 passed`; supplemental `56 passed, 4 skipped` | 156 direct/wrapper state-sensitive call sites reviewed; zero unsafe owners; no HIGH/MED/CRITICAL finding |

The broad failures remain failures, not passes. Each Muhūrta test substitutes a
bare object for `swisseph`; importing the ephemeris module then needs real Swiss
constants before reaching the test's intended injected failure. Test
order can instead reach the unchanged missing-file precondition first when that
module was already imported. The standalone comparison reproduces the same
bare-object failure on the current and accepted baseline revisions. The
authorized serialization changes do not alter that import/test arrangement.

## F22/F23 and DP03/DP07 disposition

- F22: PASS at the L0 computational producer boundary. Process-wide state
  selection and dependent calculation spans are serialized and detector-owned.
- F23: all applicable producer-computation proofs PASS. Managed-channel and
  empirical-evaluation proofs remain not authorized and not reached.
- DP03: PASS for the implemented substrate/service computation contract; no
  chart-fact or later-layer claim is made.
- DP07: PASS for terminal numerical repeatability under adversarial forward and
  reverse mode/path interleaving, nested entry and cache-context alternation.

The independent read-only challenge passed against `f648d5add`. It confirmed
one canonical lock, complete critical spans, correct cache context, authorized
scope, unchanged output contracts and zero live unresolved caller. The
substantive L0 `PRODUCER_READY` rule is satisfied. This validation does not claim
integration, deployment, production population/health, consumer value or
empirical evaluation.
