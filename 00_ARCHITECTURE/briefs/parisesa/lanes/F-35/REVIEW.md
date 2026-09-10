---
lane: F-35
stream: S3
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read PROTOCOL.md, SPEC.md, DIAGNOSIS.md in full. Read source at `/Users/Dev/par-night/main-ro`:
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` (full)
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` (full)
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` (full)
- `platform/python-sidecar/tests/test_mi_darshana.py` (full)
- `platform/migrations/348_mimamsa_pramana.sql` lines 1-25
- `platform/migrations/` directory listing (confirmed HEAD = 572)
- Confirmed no existing `test_mi_sambandha.py`

All spec file:line citations traced against live source. No REVIEW_LEADS.md present.

## Q1 — Does the spec address the mechanism or merely the symptom?

Mechanism. SPEC §0 explicitly retires the corpus's wrong causal claim ("population-level cross-chart mining") and replaces it with the actual code path: `mi_sambandha.py:95-96` uses `n = opp` (raw assignment count) as the gate for `"empirical"`, with no check on whether any of those assignments carries a scored `composite_verdict` (`confirmed`/`partial`/`denied`). Verified: `mi_sambandha.py` lines 77-84 confirm `counts[key] = {"fire": 0, "opp": 0}` (no `scored` key) and lines 95-96 confirm `n = opp; grade = "empirical" if n >= 5 else "prior_only"`. The diagnosis correctly notes that `fire_count` (the outcome-derived number) plays no role in the grade decision. The fix targets the predicate directly (§2a) and the downstream hardcoded pass-through (§2b). This is a §N.8 earned-signal defect addressed at the earning site.

## Q2 — Does every D sub-claim map to a spec element?

Yes. Full mapping:

| Sub-claim | Spec element |
|---|---|
| C1 (mixed undifferentiated insight_units[]) | §2a (grade split into honest tiers) + §2b (tier passed through, not collapsed) + §2d (aggregate summary) |
| C2 (no inline marker for the tier mixing) | §2a + §2b — `evidence_grade` itself becomes the honest marker |
| C3 (corpus's population-mining causal claim) | Retired in §0 with mechanism correction — not a deficiency, correct disposition |

Sibling census (DIAGNOSIS §4) fully accounted for in SPEC §4:
- `mi_sambandha.py:96` → Fixed §2a ✓
- `mi_darshana.py:151,184` → Fixed §2b ✓
- `mi_darshana.py:215` emergent-law block → Excluded: `mi_pariksha.py`'s `n_support` semantics untraced in Stage-D budget; correct call (Q7 would fail if assumed) ✓
- `mi_pramana.py:474` → Excluded: confirmed clean sibling (outcome-derived, not a defect) ✓
- `query_insights.ts` → Fixed §2d ✓
- `query_calibration.ts` → Excluded: separate capability, no known defect ✓
- `query_manifestation_grammar.ts` → Excluded: single-source, no mixing ✓

All sub-claims mapped. No unmapped diagnosis claim.

## Q3 — Would the exit tests genuinely fail on today's code?

**Test 3a (`test_nine_unscored_assignments_do_not_earn_empirical_grade`):** Traced against current source. Nine rows with `composite_verdict=None` → `counts[key]["opp"]=9`, `fire=0`. Line 96: `n = opp = 9; grade = "empirical"` (9 ≥ 5). Test constant `EVIDENCE_GRADE = 13` indexes into the current 15-element INSERT tuple at position 13 = `citation_ref` = `json.dumps({"method": "fire_over_opportunity"})`, not `"assignment_only"` → assertion fails. **Fails today. ✓**

Note: SPEC §3a says index 13 "points past the tuple boundary" but the current tuple has 15 elements (indices 0–14); index 13 is within bounds, it reads `citation_ref`. The test still fails for the right overall reason (wrong value at the expected index), but the inline explanation is factually imprecise (not out-of-bounds, wrong column). **Non-blocking — test behavior is correct.**

**Test 3b (`test_assignment_only_grade_passed_through_not_hardcoded_empirical`):** Current `_grammar_row` helper (test_mi_darshana.py:112) has no `evidence_grade` parameter → calling it with `evidence_grade="assignment_only"` raises `TypeError` on setup. Even with the helper extended, `mi_darshana.py:184` hardcodes `"empirical"` regardless of the source row → `row[EVIDENCE_GRADE]` = `"empirical"` ≠ `"assignment_only"` and statement contains `"empirical learning"` → both assertions fail. **Fails today. ✓**

**Column indexes verified:**
- `EVIDENCE_GRADE = 13` in 3a: correct for post-fix 16-element tuple (scored_count inserted at index 7 shifts grade from 12 to 13) ✓
- `EVIDENCE_GRADE = 11` in 3b: verified against `mi_darshana.py` INSERT SQL column list — `evidence_grade` is at position 11 ✓
- `STATEMENT = 6` (inherited from existing test file line 147): verified ✓

## Q4 — Are all sibling sites covered or excluded with a stated reason?

Yes — six sibling sites from DIAGNOSIS §4, all accounted for in SPEC §4 with either a fix or a stated exclusion reason. See Q2 table. No uncovered site.

## Q5 — Is there a recurrence guard, and does it detect the actual defect class?

Yes, and genuinely. Three orthogonal guards:
1. `test_nine_unscored_assignments_do_not_earn_empirical_grade` — fails closed the moment the predicate reverts to gating on `opp`/assignment count (guards the false-positive direction).
2. `test_five_scored_assignments_do_earn_empirical_grade` — fails closed if "empirical" is over-narrowed and stops granting for genuinely-scored data (guards the false-negative / over-correction direction).
3. `test_assignment_only_grade_passed_through_not_hardcoded_empirical` — independently guards against re-introduction of a hardcoded `"empirical"` literal in `mi_darshana.py`'s manifestation-grammar block, regardless of what `mi_sambandha.py` computes.

All three detect the actual defect class (opportunity-vs-outcome gate / hardcoded grade pass-through), not proxies.

## Q7 — Any unverified assumptions? Every file:line citation checked?

**Verified correct:**
- `mi_sambandha.py:95-96` (`n = opp; grade = "empirical" if n >= 5`) — confirmed ✓
- `mi_sambandha.py:68-84` (counts dict loop) — confirmed (lines 70-84) ✓
- `mi_sambandha.py:90-96` (grade block, as quoted) — confirmed ✓
- `mi_darshana.py:151` (`AND evidence_grade = 'empirical'`) — confirmed ✓
- `mi_darshana.py:184` (hardcoded `"empirical"`) — confirmed ✓
- `platform/migrations/348_mimamsa_pramana.sql:17` (`composite_verdict` value set `'confirmed'|'partial'|'denied'|'pending'`) — confirmed ✓
- `query_insights.ts:105` (`evidence_grade` in SELECT list) — confirmed ✓
- Migration HEAD = 572 — confirmed ✓
- No existing `test_mi_sambandha.py` — confirmed (new file is correct) ✓

**Minor citation drift (non-blocking):**
- SPEC says `query_insights.ts` return block is "currently lines 133-141"; actual is lines 135-144 (diff: return starts at 135, const at 133). Off by 2.
- SPEC cites `insight_units: insightResult.rows` at `:137`; actual line is 138. Off by 1.
- SPEC says EVIDENCE_GRADE=13 "points past the current 15-element tuple's boundary"; the tuple has indices 0-14 so index 13 is in-bounds at `citation_ref`. Factually imprecise (wrong column, not out-of-bounds), but test fails correctly.

None of these affect the correctness of the fixes or tests.

**writer_asset / rs_class / rebuild_group accuracy:**
- `writer_asset: mi_sambandha` ✓ (the primary defect writer)
- `rs_class: RS-A` (writer-level fix) ✓
- `rebuild_group: G4` (`mi_sambandha` ← F-35) — consistent with PROTOCOL.md rebuild_groups description ✓
- SPEC §6 correctly acknowledges rebuild requires native permission per ND-PARISESA-2; Stage V must not trigger a rebuild autonomously ✓

## Verdict: COMPLETE

The spec correctly identifies the mechanism (opportunity-count gate, not outcome-count gate, on the `"empirical"` grade), maps all diagnosis sub-claims to fix elements, specifies genuine exit tests that fail on today's code, covers all sibling sites with stated dispositions, and provides real recurrence guards that detect the actual defect class. Minor citation line-number drift is non-blocking. No unverified assumption affects the correctness of any proposed fix.