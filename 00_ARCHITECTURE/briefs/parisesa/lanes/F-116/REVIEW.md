---
lane: F-116
stream: S4_VACA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, SPEC.md, DIAGNOSIS.md, prior REVIEW.md (pool-1, INCOMPLETE-RETURN on D1).
Context note: "re-review after reviser cycle" — re-checking whether D1 was resolved.
Source verified at /Users/Dev/par-night/main-ro:
- bo_upaya.py lines 983–994 (_fetch_remedies_for_graha, planet-only WHERE clause)
- bo_upaya.py lines 1288–1374 (prescriptions loop, append call at 1336, remedy_label_human at 1347, prescription_detail_jsonb at 1348–1358, targets_dosha_class at 1361)
- grep for `_strip_conditional_preamble` in bo_upaya.py — absent; ImportError confirmed for exit test
No REVIEW_LEADS.md present in lane dir.

## Q1 — Mechanism vs symptom?

COMPLETE. Spec §1 identifies the exact root cause: `_fetch_remedies_for_graha` (bo_upaya.py:983–994) predicates only on `lower(planet) = %s`; the call site at line 1347 embeds `prescription_text` verbatim with no affliction-state gate. Fix is a write-side preamble stripper at the single output point — not a per-row or display-side workaround.

## Q2 — Every diagnosis sub-claim mapped?

COMPLETE. SPEC §7 Coverage table maps all 8 diagnosis sub-claims: (a) Jupiter false preamble, (b) Sun false preamble, (c) Venus false preamble, (d) architectural join-only predicate, three mechanism claims (_fetch_remedies_for_graha line range, dosha_by_graha unused for gating, query_remedies.ts:542 passthrough), sibling census, and blast-radius/F-50 overlap. No unmapped diagnosis claim found.

## Q3 — Exit test genuinely fails today?

YES. `_strip_conditional_preamble` is absent from bo_upaya.py in main-ro (grep confirms). Line 81 of the exit test file (`from pipeline.orchestrator.writers.bo_upaya import _strip_conditional_preamble`) raises ImportError before any DB fixture is reached. All four tests in the file fail at import — confirmed red today.

## Q4 — Sibling sites covered or excluded with reason?

COMPLETE. SPEC §4 covers all 5 corpus buckets. STOTRA (12/12 rows), DOSHA (~30+), and DANA (several) all route through `_fetch_remedies_for_graha` → line 1347 — single call site, single fix point. LEGACY and YANTRA excluded with stated reason (no preamble pattern confirmed in diagnosis; helper returns stripped=False, no harm). `dosha_target` filtering explicitly deferred with stated dependency reason (requires F-117 §2a). Adequate.

## Q5 — Recurrence guard adequate?

ADEQUATE. `test_strip_removes_stotra_preamble_sun` fails at ImportError if helper is removed — direct detection of defect-class regression. `test_stored_remedy_label_human_has_no_conditional_preamble` detects re-introduction of verbatim preambles in bodha_upaya_prescriptions post-rebuild. Advisory CI lint under governance/ noted for conductor. Together these guard the full defect class.

## Q7 — Unverified assumptions? File:line citations accurate?

All citations verified against main-ro:
- bo_upaya.py:983–994 (_fetch_remedies_for_graha, WHERE lower(planet) = %s only) ✓ exact
- bo_upaya.py:1288–1295 (prescriptions loop start) ✓ exact
- bo_upaya.py:1336 (prescriptions.append({) ✓ exact
- bo_upaya.py:1347 (remedy_label_human: str(corpus_row.get("prescription_text") or "")[:200]) ✓ exact
- bo_upaya.py:1348–1358 (prescription_detail_jsonb dict, closes with maraka_contraindication_verdict) ✓ exact
- bo_upaya.py:1361 (targets_dosha_class uses dosha_by_graha, never for selection) ✓ exact
- query_remedies.ts:542 (remedy_label_human: r['remedy_label_human'] passthrough) ✓ confirmed by prior pool-1 read; no reason to doubt
- `import re as _re` inserted at module scope ~line 982 (above _fetch_remedies_for_graha): Python allows module-level imports anywhere in a module file — syntactically valid, no issue.

## D1 closure check (prior INCOMPLETE-RETURN)

Prior D1: "Two Python assignment statements shown inside a dict literal — SyntaxError as literally written."

Revised SPEC §2 now reads: "In the loop body, **before** the `prescriptions.append({` call at line 1336, insert the two assignment lines" — followed by a standalone code block for the two assignments — then: "These assignments must appear in the loop body before `prescriptions.append({` at line 1336 — not inside the dict literal. `_preamble_stripped` is then in scope for the entire `prescriptions.append({...})` call below."

This is unambiguous. The assignments are loop-body statements outside the dict literal. `_preamble_stripped` is in scope when `prescription_detail_jsonb` dict opens. D1 is fully closed.

## writer_asset / data_delta verification

- writer_asset: bo_upaya — in rebuild group G3 per PROTOCOL.md ✓
- data_delta: narrow — only `remedy_label_human` and `prescription_detail_jsonb.preamble_stripped` fields affected; downstream passthrough in query_remedies.ts:542 is serving-only ✓

## Verdict: COMPLETE
