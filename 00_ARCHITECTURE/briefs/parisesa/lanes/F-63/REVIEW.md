---
lane: F-63
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md v1.2, SPEC.md (F-63 post-reviser), DIAGNOSIS.md (F-63), existing REVIEW.md (prior pool-1 INCOMPLETE-RETURN). No REVIEW_LEADS.md present.
Context note: "re-review after reviser cycle" — verifying that reviser closed D1.

Source verified at `/Users/Dev/par-night/main-ro` (origin/main):
- `platform/python-sidecar/panchang_engine/special_yogas.py:68-77` — `_yoga_dict()` producer
- `platform/python-sidecar/ga_writers/ga_panchanga_writer.py:1050-1084` — `_emit_special_yoga_combinations()` consumer
- `platform/python-sidecar/tests/test_ga4_writer.py:165-190` — `_make_forensic_pi()` fixture factory
- Grep for `special_yoga_combination_name` and `test_special_yoga` in test file → no output (function does not yet exist in source, as expected)

## Q1 — Mechanism vs. symptom

PASS. Spec targets the mechanism: `ga_panchanga_writer.py:1060` reads keys `"name"`/`"yoga_name"` from `yoga_dict`, but `special_yogas.py:_yoga_dict()` (lines 68-77) exclusively emits the key `"yoga"`. The fallback to literal `"unknown"` fires unconditionally. The fix is the key-contract correction, not symptom patching. Source confirms: line 1060 reads `yoga_dict.get("name", yoga_dict.get("yoga_name", "unknown"))` and `_yoga_dict()` returns `{"yoga": name, ...}` — exact mismatch confirmed.

## Q2 — Sub-claim coverage

PASS. All 8 sub-claims from DIAGNOSIS.md's claim decomposition are explicitly mapped in the spec's coverage table:
- (a) detector correct/untouched — no spec action, root-cause statement records this ✓
- (b) key-mismatch mechanism (not a lookup-table gap) — Files-to-change item 1 ✓
- (c) `"unknown"` served unconditionally — Files-to-change item 1 ✓
- (d) emission-gate correct/untouched — no spec action, confirmed ✓
- §N.8 fixture-masks-bug contributing factor — Files-to-change item 2 + exit-test sequencing ✓
- Sibling census 0 additional instances — Sibling sites section ✓
- Blast-radius `bo_laksana.py` explicitly out-of-scope with stated reason ✓
- `ekv/b-01` disjointness confirmed, no action needed ✓

## Q3 — Exit test genuinely fails on today's code

PASS — prior D1 deficiency fully closed by reviser.

Prior REVIEW (pool-1) found: the SPEC referred to amending "an existing test" that exercises `_emit_special_yoga_combinations`, but no such function exists in `test_ga4_writer.py`. The `-k special_yoga` command collected 0 tests, so the "Fails today" claim was false.

Revised SPEC now explicitly states:
- "no test function in `test_ga4_writer.py` currently calls `_emit_special_yoga_combinations` or asserts `combination_name`. The `-k special_yoga` selector collects 0 tests on current code, so the exit test cannot be an amendment to an existing function — Stage B must add a new test function."
- Names the function: `test_special_yoga_combination_name_resolves_real_name`
- Provides full minimal implementation (lines 96-104 of SPEC)
- Updated command: `pytest ... -k special_yoga_combination_name -v` (collects exactly 1 test once added)
- Explicitly traces fixture-first/writer-second sequencing: with fixture corrected to `{"yoga": ...}` but writer NOT yet fixed, `yname` resolves to `"unknown"` (`.get("name", ...)` chain has no match on the corrected fixture) → assertion `value_text == "Sarvartha Siddhi Yoga"` fails. After writer fix, `yname == "Sarvartha Siddhi Yoga"` → passes.

Traced against current source: `test_ga4_writer.py:176-178` still has `{"name": "Sarvartha Siddhi Yoga", "yoga_name": "Sarvartha Siddhi Yoga"}` — unfixed fixture on current main-ro. Grep for `test_special_yoga_combination_name_resolves_real_name` → no output (new function not yet added, as expected). The SPEC correctly sequences Stage B's work and the exit test is sound.

## Q4 — Sibling sites covered

PASS. Three sites inspected and ruled out with per-site reasons:
- `bo_pratijna.py:307` — `dignity_state` key genuinely appears in producer, legitimate defensive default ✓
- `mi_darshana.py:158` — `domain` key appears in producer ✓
- `bo_cgm_paths.py:163` — `node_subject` key appears in producer ✓
Single-consumer confirmation accurate: `special_yogas.py`'s `_yoga_dict()` has exactly one consumer (`ga_panchanga_writer.py`). No second call site exists to check independently. Sibling count 0 additional instances is correct.

## Q5 — Recurrence guard

PASS. Once Stage B adds the new test function with the corrected fixture, the guard is genuine: the fixture shape matches production (`_yoga_dict()` output), the assertion checks for a real name (not `"unknown"`), and fixture-first/writer-second sequencing proves the corrected fixture actually exercises the real code path. TypedDict recommendation is correctly labeled optional (not a blocking requirement). Guard is structurally sound.

## Q7 — Verified citations

PASS. All file:line citations verified against current main-ro source:
- `ga_panchanga_writer.py:1060` → `yname = yoga_dict.get("name", yoga_dict.get("yoga_name", "unknown"))` ✓
- `ga_panchanga_writer.py:1063` → `subj = f"YOGA_{yname.upper().replace(' ', '_')}"` ✓
- `ga_panchanga_writer.py:1066-1069` → `_row(... value_text=yname ...)` ✓
- `ga_panchanga_writer.py:1055-1057` → `yogas = pi.special_yogas_instant or []` / `if not yogas: yogas = []` ✓
- `special_yogas.py:68-77` → `_yoga_dict()` returns `{"yoga": name, ...}` exclusively ✓
- `test_ga4_writer.py:176-178` → `pi.special_yogas_instant = [{"name": ..., "yoga_name": ...}]` ✓
- NEEDS-LEASE: S6_ADHARA owns `platform/python-sidecar/ga_writers/**` — lease conflict framing accurate per LEASES.json.

Minor note carried forward from pool-1 (not a blocking deficiency): `test_ga4_writer.py` lives under `platform/python-sidecar/tests/`, outside S6's `ga_writers/**` glob. Conductor should confirm test-file ownership when re-leasing to S6.

## Named deficiencies (if INCOMPLETE-RETURN)

None. Prior D1 (exit test references non-existent existing function) has been fully resolved by the reviser. No new deficiencies found.

## Verdict: COMPLETE
