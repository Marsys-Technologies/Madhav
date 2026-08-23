# F-135 REVIEW (Stage R) — ranked_themes.weaknesses silent-empty disclosure

Stream S4 VĀCA · PARIŚEṢA campaign · Stage-R independent review of SPEC.md, per the plan's
"no code until an independently-reviewed-COMPLETE spec exists" discipline. Reviewer did not
author DIAGNOSIS.md or SPEC.md.

## 1. Does the spec address the mechanism or merely the symptom?

**The symptom — correctly, and by governance mandate, not by omission.** DIAGNOSIS.md's own
verdict classifies F-135 as a "design-boundary mismatch," not a code bug: Stage 1
(`bo_pratijna.py`'s occurrence-band → status mapping) and Stage 2 (`buildRankedThemes`'s
status → bucket routing) both execute exactly as documented and unit-tested. PRATINIDHI ruling
PAR-R-8 (referenced throughout SPEC.md) already adjudicated the mechanism question and refused
to reopen the L2 rubric (`bo_pratijna.py`'s WEAK/MODERATE→`conditional` collapse) — the SPEC
correctly treats that as settled and scopes itself to `buildRankedThemes()` only, adding a
computed `weaknesses_empty_reason` (an honest disclosure of *why* the bucket is empty) and a
grade-ascending sort of `open_questions`. Given the ruling, "fix the symptom (missing
disclosure) without touching the settled mechanism (rubric thresholds)" is the correct target,
not a shortcut. No deficiency here.

## 2. Does every D-2 sub-claim map to a spec element? (SPEC's coverage table vs. DIAGNOSIS's actual Claim Decomposition)

**Substantively yes, with one accuracy correction and one unlabeled addition — neither
blocking.**

- DIAGNOSIS.md's actual section is titled "Claim Decomposition" (not "D-2" verbatim — the
  "D-2" label appears to be the plan's internal Stage-D task numbering, which this reviewer
  cannot independently confirm without the campaign plan, but the *content* referenced is
  unambiguously DIAGNOSIS.md's three lettered claims).
- (a) weaknesses empty — DIAGNOSIS: TRUE. SPEC table: "Unchanged — correctly empty per
  rubric." Matches.
- (b) open_questions contains graded domains — DIAGNOSIS's header line says "3.8–4.7/10" but
  its own body immediately corrects this to "range actually 3.8–5.9/10 across all 14
  open_questions rows." SPEC's table uses "3.8–5.9" — i.e. it correctly used DIAGNOSIS's
  *corrected* figure, not its stale header figure. This is accurate, not a discrepancy.
- (c) strengths populated / asymmetry — DIAGNOSIS: TRUE, asymmetry real. SPEC table: matches,
  and correctly notes the asymmetry becomes *disclosed* rather than *fixed* once
  `weaknesses_empty_reason` exists.
- The three "PRATINIDHI (a)/(b)/(c)" rows in SPEC's table have no counterpart in DIAGNOSIS.md
  (DIAGNOSIS ends at an ESCALATE-TO-PRATINIDHI three-way fork, not a ruling). These rows
  restate PAR-R-8's directive, which this reviewer cannot read directly (not supplied), so
  their accuracy against the actual ruling text cannot be independently verified here — flagged
  as an unverifiable-by-this-reviewer gap, not a confirmed error, and not itself grounds for
  return since it's additive (spec requirements beyond D-2), not a dropped D-2 claim.

## 3. Would the exit test genuinely fail today?

**Yes, confirmed against the actual code.** Read `register_p1_synthesis.ts` lines 381-471
directly:
- `buildRankedThemes`'s return type (line 384) is exactly
  `{ strengths: string[]; weaknesses: string[]; open_questions: string[]; verdict_quality_flags: string[] }`
  — **no `weaknesses_empty_reason` field exists anywhere in the type or the return statement**
  (line 470).
- `openQuestions.push(sentence)` occurs at three sites (420, 422/openQuestions via no_evidence
  path, 466) in verdict-array iteration order; there is no `.sort()` call anywhere in the
  function or between the loop and the `return` — **`open_questions` is confirmed
  insertion-ordered, not grade-sorted.**

Both preconditions the SPEC's exit test relies on are true today, so a test asserting
`ranked_themes.weaknesses_empty_reason` exists and `open_questions` is ascending-sorted would
fail against current code exactly as claimed.

## 4. Are all sibling sites from D-4 covered, or excluded with a stated reason?

**Consistent with DIAGNOSIS's Blast Radius section, with one internal-consistency problem
covered in Q7/verdict below.** DIAGNOSIS's "Blast Radius (file overlap with F-129)" section
states: same file, different code region, no line-level overlap — F-135's mechanism is
`buildRankedThemes()` (lines 381-471, bucketing at 457-467); F-129's `top_discoveries` is a
separate SQL block at lines 815-822 reading `bodha_discoveries`, sharing no variables or helper
function. Direct read of lines 790-869 confirms this: `discResult` (F-129's query, lines
815-822) and `ranked_themes = buildRankedThemes(verdicts, audience)` (line 845, F-135) are
independent — `discResult.rows` flows only into `top_discoveries: discResult.rows` (line 868),
never into `buildRankedThemes`. SPEC's "explicitly out of scope" claim for F-129 is consistent
with what DIAGNOSIS actually found. No other sibling sites are named in DIAGNOSIS's census, and
none were found by this reviewer's independent grep (see Q7) beyond the one call site SPEC
itself should have located.

## 5. Is there a recurrence guard, and does it actually detect the defect class?

**Real but overstated — a weaker guard than the SPEC's framing implies.** Applying §N.8 (what
specifically does this signal claim, and what code path would have to run — and fail — for the
signal to correctly read false?):

The claimed guard is "TypeScript return-type non-optional field is itself the guard... removing
the computation without removing the field from the type is a build break, not a silent
regression." This is only accurate for one specific defect: an engineer entirely deletes the
`weaknesses_empty_reason: ...` line from the returned object literal while leaving it in the
type — that genuinely fails to compile. But it does **not** detect the more likely regression in
this campaign's own defect taxonomy (§N.7 item 6, §N.8): someone leaves the field present but
replaces its computation with a hardcoded, always-wrong value (e.g. `weaknesses_empty_reason:
null` unconditionally, or a static string). TypeScript's structural type check is satisfied by
any `string | null`-typed expression — it cannot and does not verify that the value is actually
*computed from* `conditionalCount`/`minConditionalGrade` rather than hardcoded. That exact defect
class (a flag/field present but not actually backed by the check it claims) is the direct subject
of §N.7 item 4 and the whole point of §N.8 — the SPEC's own governing doctrine. The type-presence
"guard" is real but narrow, and it substantially overlaps with — while being strictly weaker
than — the exit test's own fixture assertions (which do check the actual substrings "14" and
"3.8", i.e. real values, not just field presence). The SPEC should have named the exit test
itself as the actual recurrence guard (it *is* a genuine detector for the hardcoded-value case)
rather than presenting the type check as an independent, suflicient guard in its own right. This
is a real but non-fatal documentation/framing gap, not a missing guard — the exit test already
does the real work, it's just mis-labeled.

## 6. Could this regress any of the 27 CL-00 controls, or another stream's lane?

**No visible collision found, but this is a partial check given this reviewer has no access to
S5's lane docs.** Direct read of `register_p1_synthesis.ts` around `buildRankedThemes` (lines
381-471) and its sole call site (773-845) shows no `CL-03`, `param_parity`, or `S5`-authored
comments anywhere in the file (`grep -n "CL-03\|S5\b\|param.parity" register_p1_synthesis.ts`
returns nothing). The function only takes `verdicts` and `audience` and touches no
authorization/param-validation logic. The SPEC correctly identifies and respects the
`LEASES.json` first-hold on this file and explicitly blocks Stage B until
`PAR-register_p1_synthesis-RELEASE` — this is the right posture given the file-level lease,
independent of whether a deeper conflict exists in code this reviewer cannot see. No deficiency
found within the scope available to this review.

## 7. Is anything in the spec an unverified assumption rather than read code?

**Two findings: one self-correction confirmed accurate; one omission that should have been
resolved by Stage S and was not.**

**(a) Quote-correction check — VERIFIED ACCURATE.** Read `bo_pratijna.py` lines 70-80 directly.
Lines 73-75 read: *"3. WEAK and MODERATE both collapse to 'conditional' rather than splitting /
WEAK into 'denied' or MODERATE into 'promised' -- keeping the mapping / monotonic and
boundary-preserving (every band maps to exactly one status..."* — this exactly matches the text
SPEC.md quotes as "verified," and does **not** say "conservative." SPEC's self-correction of the
relayed PAR-R-8 misquote is itself accurate; it did not introduce a new error while correcting
the old one. (Separately, minor: SPEC's root-cause statement cites "occurrence < 0.20, grade <
2.0/10 per bo_pratijna.py:44-50" — lines 44-50 actually state the band→status mapping table, not
the 0.20/2.0 numeric values themselves, which appear more precisely at lines 66-69. This is a
loose citation, not a wrong claim, and does not affect the spec's substance.)

**(b) Call-site location — NOT AN ACCEPTABLE GAP, and internally inconsistent within SPEC.md
itself.** SPEC.md's "Files to change" item 2 states the call site "was not located in this
diagnosis pass, Stage B's first task." A single grep resolves this immediately:

```
grep -n "buildRankedThemes(" platform-mcp/src/tools/register_p1_synthesis.ts
381:function buildRankedThemes(
845:        const ranked_themes = buildRankedThemes(verdicts, audience)
```

One call site, same file, 464 lines below the function definition — trivially locatable, and in
fact already implicitly within the exact line range (line 845) that both DIAGNOSIS.md and
SPEC.md already read and cited elsewhere (SPEC's Dependencies section discusses this same file's
lease; DIAGNOSIS's Blast Radius section quotes lines 815-822 of the very same `try` block that
contains line 845). Having already read the surrounding code, failing to notice or grep for the
one call to the function under active modification is a real gap in the diagnosis/spec work, not
a defensible "next stage's job."

Worse, this directly **contradicts** SPEC's own "Sibling sites covered" section, which asserts:
*"F-135's D-stage census... confirmed `buildRankedThemes` is a single function with one call
site."* That claim — "confirmed... one call site" — cannot be true if the call site itself "was
not located in this diagnosis pass" per the very same document three sections later. Either the
census located the call site (in which case Stage S should have cited it directly instead of
punting to Stage B), or it didn't (in which case the "confirmed... one call site" claim in the
Sibling sites section is itself an unverified assertion dressed as a confirmed finding). Both
readings are spec defects.

Having independently checked: the call site at line 845 is `const ranked_themes =
buildRankedThemes(verdicts, audience)`, and the returned object is spread into `brief` as a bare
`ranked_themes,` shorthand (line 862) with no destructuring or field-by-field handling — meaning
once `weaknesses_empty_reason` is added to `buildRankedThemes`'s return type, **the call site
requires zero additional changes** to thread the new field through. This is good news for
Stage B's actual workload, but it sharpens the review finding: the "unlocatable, Stage B's first
task" framing was not just avoidable but, once done, trivial and inconsequential — there was no
real reason to defer it.

## Verdict: INCOMPLETE-RETURN

**Named deficiencies:**

- **(Primary, per the review brief's own stated bar) Call site left unlocated despite trivial
  discoverability.** A single `grep -n "buildRankedThemes(" register_p1_synthesis.ts` finds the
  sole call site in ~0 effort. SPEC.md should state the located call site (line 845), confirm the
  spread-shorthand assignment (`ranked_themes,` at line 862) needs no further changes, and drop
  the "not located in this diagnosis pass, Stage B's first task" language entirely.
- **Internal self-contradiction in SPEC.md.** The "Sibling sites covered" section claims the
  D-stage census "confirmed... one call site," while the "Files to change" section says the call
  site "was not located." These cannot both be true as written; resolve by citing the actual
  located call site everywhere the claim is made.
- **Recurrence guard is mis-framed, though not absent.** The described guard (non-optional
  TypeScript field) only catches total field deletion, not a hardcoded/always-wrong value for
  that field — precisely the defect class §N.7/§N.8 (this campaign's own governing doctrine) warn
  about. The SPEC should identify the exit test's fixture-substring assertions (not the bare type
  check) as the actual recurrence guard, since that is the mechanism that would really fail if the
  computation were silently replaced by a constant.

**Not blocking, but should be tightened on resubmission:** the `bo_pratijna.py:44-50` citation
for the 0.20/2.0 thresholds is loose (the precise numbers live at lines 66-69); the three
"PRATINIDHI (a)/(b)/(c)" rows in the sub-claim coverage table could not be independently verified
against PAR-R-8's actual text (not supplied to this review) and should carry an explicit citation
or excerpt when resubmitted.

Return to Stage S author for a targeted fix: locate and cite the call site, resolve the
self-contradiction, and re-frame the recurrence guard around the exit test's real assertions. The
root-cause mechanism analysis, files-to-change scope, exit-test design, and lease-sequencing
posture are otherwise sound and do not need rework.
