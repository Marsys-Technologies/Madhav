---
lane: F-68
stream: S3_SATYA
stage: R (REVIEW) — Stage R, banked under urgency (Q6 deferred, see note)
reviewer: VERIFIER (author != reviewer — DIAGNOSIS.md/SPEC.md authored by S3; sub-reviewer draft Q1-Q5/Q7 analysis reviewed and ratified by VERIFIER)
verdict: INCOMPLETE-RETURN
---

# F-68 — REVIEW (Stage R)

## Process note

TIER1-CORRECTNESS lane. A VERIFIER-dispatched sub-reviewer ran the exit test live (TIER1
requirement) and produced draft Q1-Q5/Q7 analysis; VERIFIER read that draft and is banking the
verdict now under explicit time pressure, with full Q6 cross-lane check deferred as a noted
follow-up rather than blocking this write.

## Named deficiency: sibling census incomplete despite a claimed-exhaustive grep

SPEC.md's coverage table claims an exhaustive sweep for the unconditional-numeric-attach
pattern (the P3-b tier-suppression defect this lane's real fix targets, per the adopted
`ekv/b-07-nimitta-tag` branch's own reclassification history — hygiene-only rename, not the
real fix). The sub-reviewer independently ran a live check against the actual database/service
layer (not just a static grep) and found **two more live instances of the exact same defect
class that the coverage table missed entirely:**

1. **`ph_sankrama`'s `query_spillover_cascades`** — confirmed live: 2985/2985 rows serving
   unsuppressed numeric confidence (posterior/lift) under a permanently non-calibrated tag,
   the same P3-b shape as F-68's primary target.
2. **`register_p1_synthesis.ts`'s `prashna_undertaking_get`** — a second live site with the
   same pattern.

This is directly relevant given `LEDGER_PRATINIDHI.md`'s own HN-4 handoff note already flagged
`ph_sankrama/engine.py` and `ph_sodhana/engine.py` as likely sibling sites requiring a
covered/excluded disposition in F-68's coverage table, not a handoff note (per PAR-R-4's binding
rule: "a sibling site is never a handoff note"). The sub-reviewer's live-DB check confirms at
least one of those two named sites is a genuine, currently-unaddressed live instance, plus a
third site SPEC.md's own claimed-exhaustive census did not surface.

## Other Q1-Q5/Q7 dimensions

Exit test run live by the sub-reviewer, TIER1 requirement satisfied (red confirmed on today's
code). Root-cause mechanism (numeric posterior/confidence/lift served unconditionally under a
non-calibrated tag, `engine.py:418` dataclass default) confirmed targeted correctly by the spec
for its named site — the gap is coverage breadth, not mechanism accuracy.

## Q6 — DEFERRED (follow-up, not blocking this verdict)

Not yet independently run. Given this lane already touches multiple files across S3's domain
(`ph_sankrama`, `ph_sodhana`, `register_p1_synthesis.ts`), this is a higher-than-F-34 priority
follow-up once the coverage gap below is closed — a wider fix surface means more cross-lane
lease/regression surface to check.

## Verdict: INCOMPLETE-RETURN

**Deficiency (return for):** extend the coverage table to give the `ph_sankrama`/
`query_spillover_cascades` and `prashna_undertaking_get` sites an explicit covered/excluded
disposition, per PAR-R-4's binding rule — a live-confirmed sibling site is never left to a
handoff note. Given HN-4 already named `ph_sankrama`/`ph_sodhana` as likely sites, this should
be a fast resubmission, not a re-diagnosis.
