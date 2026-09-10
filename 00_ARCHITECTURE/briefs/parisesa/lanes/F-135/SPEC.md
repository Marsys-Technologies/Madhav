# F-135 SPEC (TIER4-POLISH) — ranked_themes.weaknesses silent-empty disclosure

Stream S4 VĀCA · Stage S SPEC, per PRATINIDHI ruling PAR-R-8 on the D-stage escalation.

## Quote-accuracy note (flagged, not silently corrected)

The relayed PAR-R-8 text quotes `bo_pratijna.py:73-74` as saying "keeping the mapping
**conservative**." Direct read of the file (this session, lines 73–75) shows the actual
text is:

> "3. WEAK and MODERATE both collapse to 'conditional' rather than splitting WEAK into
> 'denied' or MODERATE into 'promised' -- keeping the mapping **monotonic and
> boundary-preserving** (every band maps to exactly one status, no band straddles two
> statuses) was preferred over any alternative split..."

"Monotonic and boundary-preserving" and "conservative" are not interchangeable — the
former is about the *shape* of the status→band mapping (no band splits across two
statuses), not the L2 rubric's threshold *strictness*. This does not change the ruling's
substance (the split-the-rubric option is still correctly refused, for the reasons the
docstring actually gives: R13/R16/R20 blind-definition discipline, thresholds reused
verbatim from the v3 writer's `_PROMISED_FLOOR`/`_DENIED_CEIL`) — but this spec cites the
verified text, not the relayed paraphrase, per Stage R review question 7 ("is anything in
the spec an unverified assumption rather than read code?"). Flagging back to conductor/
PRATINIDHI for the record; not blocking on it since the ruling's directive is unaffected.

## Root-cause statement

`buildRankedThemes()` (`platform-mcp/src/tools/register_p1_synthesis.ts:381-471`) buckets
a verdict into `weaknesses` only when the L2-assigned `status === 'denied'`
(occurrence < 0.20, grade < 2.0/10 per `bo_pratijna.py:66-69` — verified, not to be
re-litigated per PAR-R-8), so any chart whose lowest-graded verdicts all land in the
WEAK/MODERATE band (grade 2.0–5.9) serves an empty `weaknesses` array with no field
explaining why, while `open_questions` silently absorbs everything below the `promised`
floor — a §N.6 item 3 violation (silent-empty summary layer) compounded by having no
`empty_reason`.

## Files to change

**`platform-mcp/src/tools/register_p1_synthesis.ts`** — `buildRankedThemes()` only.
No change to `bo_pratijna.py` or any L2 writer (PAR-R-8: refused).

1. Compute `weaknesses_empty_reason` from the verdict set actually passed into
   `buildRankedThemes` (restatement of already-computed values, no new judgment):
   count of `status === 'conditional'` rows (`conditionalCount`), and the minimum grade
   among them (`minConditionalGrade`, using the same `grade` already extracted at
   line 395). When `weaknesses.length === 0 && conditionalCount > 0`, set:
   `` `no event class for this chart scored below the denied ceiling (grade < 2.0/10); ${conditionalCount} class(es) sit in the conditional band (lowest: ${minConditionalGrade.toFixed(1)}/10).` ``
   When `weaknesses.length === 0 && conditionalCount === 0` (all promised, a genuinely
   different case the ruling didn't have in view — this chart doesn't hit it, but the
   code must not assume it can't happen), fall back to:
   `` `no event class for this chart scored below the denied ceiling (grade < 2.0/10).` ``
   Never a hardcoded "weaknesses is always empty" string — both branches are computed
   from the actual `verdicts` array, not asserted.
2. Add `weaknesses_empty_reason: string | null` to `buildRankedThemes`'s return type
   (null when `weaknesses.length > 0`). **Call site located** (revision: the original
   diagnosis pass did not grep for it despite having already read the surrounding code —
   corrected on Stage-R return): `register_p1_synthesis.ts:845`,
   `const ranked_themes = buildRankedThemes(verdicts, audience)`, whose result is spread
   into the response object as a bare `ranked_themes,` shorthand at line 862. **No change
   needed at the call site** — the shorthand spread means any new field on
   `buildRankedThemes`'s return type is threaded through automatically. Stage B's only
   work is inside `buildRankedThemes` itself.
3. Sort `openQuestions` ascending by grade before return, so the lowest-graded (most
   "weakness-like") entries surface first. Requires holding `(sentence, grade)` pairs
   during the loop (currently only `sentence` strings are pushed at line 466) and sorting
   by grade with `null`/`ungraded` entries stable-sorted to the end (never dropped).

## Exit test

New test file: `platform-mcp/src/tools/__tests__/register_p1_synthesis_ranked_themes.test.ts`
(does not exist yet — Stage B creates it). Fails today (no `weaknesses_empty_reason` field
exists; `open_questions` is insertion-ordered, not grade-sorted). Asserts, against a fixture
verdict set shaped like chart `482012f1`'s real 27-verdict response (13 promised / 14
conditional / 0 denied):
- `ranked_themes.weaknesses === []`
- `ranked_themes.weaknesses_empty_reason` is a non-null string containing the literal
  substring `"14"` (the conditional count) and the literal substring `"3.8"` (the min
  grade, formatted `.toFixed(1)`) — i.e. asserts the computed values, not a hardcoded
  string equality, so the test itself stays honest if the fixture changes.
- `ranked_themes.open_questions[0]` contains the lowest-graded domain's name
  ("Property Acquisition", grade 3.8) and the last element contains the highest-graded
  open_questions domain — asserts ascending order end-to-end, not just the first pair.
- A second fixture with `weaknesses.length > 0` asserts `weaknesses_empty_reason === null`.

## Sibling sites covered

`buildRankedThemes` has exactly one call site (`register_p1_synthesis.ts:845`, confirmed
by direct grep on Stage-R return, not merely asserted — see element 2 above). F-129's
`top_discoveries` section is a separate code region (a SQL block at lines 815-822 reading
`bodha_discoveries`, flowing directly into `top_discoveries: discResult.rows` at line 868)
with no shared variables, helper function, or upstream table — independently confirmed by
Stage R's own read of lines 790-869. Explicitly out of scope for this lane, not a missed
sibling.

## Recurrence guard

**The exit test's own fixture-substring assertions are the real recurrence guard** — not
the TypeScript field-presence check (Stage R correctly identified the original framing as
too weak: a non-optional `string | null` field is satisfied by any expression of that
type, including a hardcoded value, so it only catches total field *deletion*, not a
silently-hardcoded replacement — exactly the §N.7 item 4 / §N.8 defect class this
campaign's own doctrine warns about). The guard that actually detects "the field exists
but isn't really computed" is the exit test's assertion that `weaknesses_empty_reason`
contains the literal substrings `"14"` (the live conditional count) and `"3.8"` (the live
min grade) — a hardcoded string or a `null`-always implementation fails these substring
checks the moment the fixture's numbers don't match a static guess. No separate CI
lint is needed beyond that test; TypeScript's field-presence check remains true but
should be understood as a weak secondary safety net (catches accidental deletion), not
the primary guard.

## Dependencies and rollback

- **Dependency (blocking, per PRATINIDHI sequencing note):** `register_p1_synthesis.ts`
  is under S5's ordered first-hold (`LEASES.json` §S4_VACA.ordered_handoff_pending`,
  plan §2.1). **This lane may not enter Stage B until the conductor issues
  `PAR-register_p1_synthesis-RELEASE`** (S5's CL-03 predicate fixes in this file
  VERIFIED first). Stage S and Stage R may proceed now (documents only); this SPEC.md
  is written in full so Stage B can start immediately on release, without re-deriving
  anything.
- **Rollback:** single-file, additive-field change (new optional-at-runtime-populated
  field, existing `weaknesses`/`open_questions`/`strengths` arrays unchanged in shape);
  a `git revert` of the one commit fully restores prior behavior with no data migration.

## Sub-claim coverage table (from D-2)

| D-2 sub-claim | Spec element that closes it |
|---|---|
| (a) weaknesses empty | Unchanged — correctly empty per rubric; PAR-R-8 refuses re-legislating this |
| (b) open_questions contains graded 3.8–5.9 domains | Unchanged (correct data); now sorted ascending (element 3) so the weakest surface first |
| (c) strengths populated (asymmetry) | Unchanged — asymmetry is real and *correctly* disclosed once `weaknesses_empty_reason` explains why weaknesses is empty (element 1) rather than looking like an oversight |
| PRATINIDHI (a) computed empty_reason | Spec elements 1–2. Ruling text (verbatim, as relayed to this stream): "A **computed** `empty_reason` on `weaknesses` derived from the actual verdict set (conditional count, observed minimum grade) — never a hardcoded string." |
| PRATINIDHI (b) chart-specific true wording | Spec element 1. Ruling text: "not 'weaknesses is always empty' (false in general), but 'no event class for this chart scored below the denied ceiling; N classes sit in the conditional band' — those N listed in open_questions with their grades." |
| PRATINIDHI (c) sort open_questions ascending | Spec element 3. Ruling text: "Sort open_questions ascending by grade so the weakest surface first — the grade is already rendered in every sentence, only ordering + the empty-array explanation are missing." |

## Revision note (Stage-R resubmission)

Returned INCOMPLETE-RETURN on first pass (`REVIEW.md`). Three named deficiencies fixed in
this revision: (1) call site located and cited (`register_p1_synthesis.ts:845`, no
call-site changes needed — spread shorthand), removing the internal contradiction between
this section and "Sibling sites covered"; (2) recurrence guard re-framed around the exit
test's actual substring assertions rather than the weaker type-presence check; (3) the
loose `bo_pratijna.py:44-50` citation corrected to the precise `:66-69` where the
0.20/2.0 thresholds actually appear. The PRATINIDHI ruling excerpts above were added per
the review's non-blocking tightening request.

## Verdict

Stage S complete, resubmitted post Stage-R INCOMPLETE-RETURN. Awaiting Stage R re-review
(same independent reviewer or a fresh one — author of this revision is the stream lead,
still ≠ reviewer) and the `register_p1_synthesis.ts` lease release from S5 before Stage B.
