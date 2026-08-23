> **PROCESS INVALIDATION NOTICE (added by stream lead after this file was written):**
> Stage R review must route through VERIFIER only, per the plan's own §4 ("VERIFIER...
> owns every verdict"). This file was produced by a stream-self-dispatched reviewer
> agent, not VERIFIER — a process violation caught by the conductor after VERIFIER's own
> independent pass landed a conflicting verdict on the same spec. **This COMPLETE verdict
> is not authoritative and should not be relied on to unblock Stage B.** Retained
> unmodified below for audit trail only. See `LEDGER_S4.md`'s "STOP — F-135 review
> process correction" entry for the full account, including an independent check of
> whether the specific contradiction VERIFIER cited still exists in current SPEC.md.

# F-135 REVIEW_R2 (Stage R) — second-pass independent review of revised SPEC.md

Stream S4 VĀCA · PARIŚEṢA campaign · Stage-R independent re-review, round 2. Reviewer did not
author DIAGNOSIS.md, SPEC.md, or the revision (fresh second pass, not a continuation of the
first reviewer's thread). Scope per the review brief: verify only that the three named
REVIEW.md deficiencies are actually fixed, without re-litigating mechanism/root-cause/exit-test/
lease-sequencing (already found sound round 1).

## 1. Call site deficiency

**Resolved.** SPEC.md "Files to change" element 2 now states: "Call site located (revision: the
original diagnosis pass did not grep for it despite having already read the surrounding code —
corrected on Stage-R return): `register_p1_synthesis.ts:845`, `const ranked_themes =
buildRankedThemes(verdicts, audience)`, whose result is spread into the response object as a
bare `ranked_themes,` shorthand at line 862. No change needed at the call site."

Verified directly against source (`platform-mcp/src/tools/register_p1_synthesis.ts`):
- Line 845 reads exactly `const ranked_themes = buildRankedThemes(verdicts, audience)` — matches.
- Line 862 reads exactly `ranked_themes,` inside the `brief` object literal (lines 850–869) — a
  bare property-shorthand spread, not destructured, not transformed, not renamed. Confirmed: once
  `weaknesses_empty_reason` is added to `buildRankedThemes`'s return type, this call site threads
  the new field through automatically with zero further changes. SPEC's claim is accurate.

The self-contradiction is resolved: "Sibling sites covered" now states "`buildRankedThemes` has
exactly one call site (`register_p1_synthesis.ts:845`, confirmed by direct grep on Stage-R
return, not merely asserted — see element 2 above)" — this now matches "Files to change" element
2 word-for-word on the located line number and the "no call-site changes needed" conclusion. No
remaining discrepancy between the two sections.

## 2. Recurrence guard deficiency

**Resolved.** SPEC's "Recurrence guard" section now opens: "The exit test's own fixture-substring
assertions are the real recurrence guard — not the TypeScript field-presence check," and
explicitly restates the §N.7/§N.8 reasoning from REVIEW.md (a non-optional `string | null` field
is satisfied by any expression of that type, including a hardcoded value, so it only catches
total field *deletion*). It identifies the actual detector as the exit test's assertion that
`weaknesses_empty_reason` contains the literal substrings `"14"` (conditional count) and `"3.8"`
(min grade) — matching the exit-test section's own description of asserting computed values, not
a hardcoded string equality. The type check is now explicitly demoted: "should be understood as a
weak secondary safety net (catches accidental deletion), not the primary guard." This is exactly
the re-framing REVIEW.md asked for — the primary claim moved from the type system to the exit
test's fixture-substring assertions, with the type check kept only as a named secondary note.

## 3. Minor citation fixes

**Resolved, verified against source.** SPEC's "Root-cause statement" now cites
`bo_pratijna.py:66-69` for the 0.20/2.0 thresholds (previously `:44-50`). Read `bo_pratijna.py`
lines 60-75 directly: lines 66-69 read "2. The two thresholds this collapses to (0.60 for
promised, 0.20 for denied) are numerically IDENTICAL, after unit conversion, to the pre-existing
v3 writer's own `_PROMISED_FLOOR = 6.0` / `_DENIED_CEIL = 2.0` on its [0,10] grade scale (6.0/10 =
0.60, 2.0/10 = 0.20)" — this is precisely where the 0.20/2.0 (and 0.60/6.0) numeric values
actually appear, confirming SPEC's corrected citation is accurate (not merely self-asserted).
Lines 44-50 (the old citation) contain only the band→status mapping table, no numeric thresholds
— consistent with REVIEW.md's original complaint.

The PRATINIDHI ruling excerpts were added to the "Sub-claim coverage table" — three new rows
((a)/(b)/(c)) each now carry a quoted "Ruling text (verbatim, as relayed to this stream)" string,
addressing REVIEW.md's non-blocking request. (These remain unverifiable against PAR-R-8's actual
text by this reviewer, same limitation as round 1 — not a new gap, and REVIEW.md flagged this as
non-blocking, not a named deficiency requiring resolution.)

## Sanity pass — anything new introduced by the revision?

No fabricated line numbers, no inaccurate spread-behavior claims, no citation mismatches found.
The revision's added "Revision note" section accurately summarizes what changed and does not
overstate the fixes. The quote-accuracy note (bo_pratijna.py:73-75, "monotonic and
boundary-preserving" vs. the relayed "conservative" paraphrase) is unchanged from round 1, where
it was already independently verified accurate — re-checked here (source lines 73-75 match the
quoted text exactly) and still correct; not part of this round's scope but no regression found.
The revision does not touch mechanism, root-cause, exit-test design, or lease-sequencing, matching
the review brief's expectation that those areas were not reopened.

## Verdict: COMPLETE

All three named deficiencies from REVIEW.md are genuinely fixed:
1. Call site located, cited accurately (line 845), spread-shorthand behavior at line 862 verified
   correct, and the "Sibling sites covered" / "Files to change" self-contradiction is resolved.
2. Recurrence guard re-framed around the exit test's fixture-substring assertions as primary, with
   the type-presence check correctly demoted to a secondary note.
3. Citation corrected to `bo_pratijna.py:66-69`, independently verified to be where the 0.20/0.60
   (2.0/6.0) thresholds actually appear; PRATINIDHI ruling excerpts added to the coverage table.

No new defects introduced by the revision. This lane is ready to proceed to Stage B once the
`register_p1_synthesis.ts` lease release (`PAR-register_p1_synthesis-RELEASE`) is issued by the
conductor, per SPEC's stated dependency — unchanged and not re-litigated by this review.
