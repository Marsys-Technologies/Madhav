# F-135 DIAGNOSIS (TIER4-POLISH) — ranked_themes.weaknesses empty at depth=complete

Stream S4 VĀCA · PARIŚEṢA campaign · Stage-D DIAGNOSE

## Live Reproduction

Called `synth_chart_brief_get` live with `chart_id=482012f1-710e-4a25-994a-93821f5871aa`,
`depth=complete`. **Reproduces exactly as claimed.**

`content.ranked_themes`:
- `strengths`: **13 entries**, all `promised`, grades 6.2/10–8.8/10.
- `weaknesses`: **`[]`** — confirmed empty.
- `open_questions`: **14 entries**, all `conditional`, grades 3.8/10–5.9/10, including all five
  domains named in the finding:
  - `"Marriage: conditional (grade 4.5/10)."`
  - `"Romantic Relationship Start: conditional (grade 3.9/10)."`
  - `"Property Acquisition: conditional (grade 3.8/10)."`
  - `"Acute Illness: conditional (grade 4.7/10)."`
  - `"Surgery: conditional (grade 4.7/10)."`

13 (strengths) + 14 (open_questions) + 0 (weaknesses) = 27, matching
`coverage_receipt`'s "27 domain verdicts" — i.e. every scored event class for this chart
lands in exactly one of the two populated buckets; none land in `weaknesses`.

## Claim Decomposition

(a) **weaknesses empty** — TRUE, confirmed live.
(b) **open_questions contains domains graded 3.8–4.7/10** — TRUE, confirmed live (see above;
range actually 3.8–5.9/10 across all 14 open_questions rows).
(c) **strengths bucket populated status** — TRUE, populated (13 entries, grades 6.2–8.8/10).
The asymmetry is real: a caller sees a well-populated `strengths` list, a well-populated
`open_questions` list containing several sub-5.0 domains, and a `weaknesses` list that reads
as suspiciously empty by contrast — exactly the presentation the finding describes.

## Mechanism (file:line, quoted code)

Two-stage pipeline, both stages confirmed by direct source read:

**Stage 1 — status assignment, `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py`
lines 190–198** (the "central design decision" the module's own docstring documents at length,
lines 41–105):

```python
_OCCURRENCE_BAND_TO_STATUS: dict[str, str] = {
    "DENIED": _STATUS_DENIED,
    "WEAK": _STATUS_CONDITIONAL,
    "MODERATE": _STATUS_CONDITIONAL,
    "STRONG": _STATUS_PROMISED,
    "VERY_STRONG": _STATUS_PROMISED,
}
```

`V4_RUBRIC_SPEC_v1_0.md §6.1`'s five occurrence bands are `[0,0.2) DENIED`, `[0.2,0.4) WEAK`,
`[0.4,0.6) MODERATE`, `[0.6,0.8) STRONG`, `[0.8,1.0] VERY_STRONG`. `grade = round(occurrence * 10, 3)`
(bo_pratijna.py line 127, confirmed: "a straight unit rescale of the v4-native occurrence axis").
So on the 0–10 grade scale actually served: **`denied` requires grade < 2.0/10**; grades in
`[2.0, 6.0)` (WEAK + MODERATE) both collapse to `conditional`; only grade ≥ 6.0 is `promised`.

**Stage 2 — bucketing, `platform-mcp/src/tools/register_p1_synthesis.ts` lines 457–467**:

```ts
// MC-010: strengths/weaknesses verbs ('promised'/'denied') are only ever bucketed
// when n_support > 0 — a zero-evidence row's status was already overwritten above
// (status !== 'promised'/'denied' in that case), the `!zeroSupport` guard here is
// deliberate defense-in-depth against any future refactor that stops overwriting it.
if (status === 'promised' && !zeroSupport && (grade == null || grade >= 6)) {
  strengths.push(sentence)
} else if (status === 'denied' && !zeroSupport) {
  weaknesses.push(sentence)
} else {
  openQuestions.push(sentence)
}
```

**Confirmed: `weaknesses` requires `status === 'denied'`, and `status === 'denied'` requires
`grade < 2.0/10` per Stage 1.** Every row this chart carries with grade in the 3.8–5.9 range —
the exact range the finding names — has `status = 'conditional'` by construction (WEAK/MODERATE
band), not `'denied'`. `conditional` never routes anywhere except the `else` branch
(`open_questions`), regardless of how low its grade is short of the 2.0 floor. There is no
grade threshold within the `conditional` branch that could ever promote a row to `weaknesses` —
the bucket is selected purely by the upstream `status` string, and `'conditional'` is not one of
the two strings (`'promised'`, `'denied'`) the branch tests.

## Sibling Census — is the weaknesses bucket structurally unreachable?

**No — reachable in principle, but empirically unpopulated for every event class on this
specific chart.** This is a narrower and more precise finding than "dead code":

- `status === 'denied'` fires whenever `bo_pratijna_v4_engine`'s occurrence score for an event
  class falls below 0.20 (grade < 2.0/10) — i.e. "classical evidence for this event's occurrence
  is largely absent, OR has been actively negated" (bo_pratijna.py line 58, quoting
  `V4_RUBRIC_SPEC_v1_0.md §6.1`'s own a-priori definition).
- `status_from_occurrence_label("DENIED") == "denied"` is directly unit-tested
  (`platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bo_pratijna.py:64`), and the
  code path executes on every writer run — it is not gated out or unreachable at the type level.
- For chart `482012f1`, all 27 scored event classes land either `promised` (13, grade ≥ 6.0) or
  `conditional` (14, grade in `[3.8, 5.9]`, i.e. squarely inside the WEAK/MODERATE band
  `[2.0, 6.0)`). **None land below the 2.0 floor.** The lowest-graded class on this chart
  (Property Acquisition, 3.8/10) is still 1.8 points above the `denied` ceiling.
- `n_support` (via `len(ranked_evidence)`) is effectively always > 0 for v4-scored rows, because
  `ranked_evidence` falls back to the engine's own `factor_ledger` (mi_darshana.py lines 400–420)
  when `supporting_signal_ids` is NULL (which it always is under v4 — bo_pratijna.py line 133).
  So `!zeroSupport` is not the actual gate suppressing `weaknesses` here; `status !== 'denied'` is.

**Conclusion: the `weaknesses` branch is live, unit-tested code with a real (if narrow) firing
condition — it is not dead code for the system in general.** But on the one chart this
diagnosis was run against, and by the documented design of the WEAK/MODERATE→`conditional`
collapse (bo_pratijna.py §"the central design decision", explicitly reasoned and pre-registered
before any chart was scored, R13/R16/R20 blind-definition discipline), a domain graded
anywhere from 2.0 to 5.9 out of 10 — i.e. everything a casual reader would call a "weak" or
"below-average" showing — is *by design* labeled `conditional`/open-question, never `weakness`.
Whether that design choice is the right one for the `ranked_themes` serving contract (which
markets `weaknesses` as a distinct labeled bucket, implying it should populate when low-grade
domains exist) is a genuinely separate question from whether the code is buggy — the code
correctly implements the documented rubric; the rubric's `denied` threshold (occurrence < 0.20)
is simply far stricter than what a reader would intuitively call "a weakness."

## Blast Radius (file overlap with F-129)

**Same file, different code region — no line-level overlap.** F-135's mechanism lives in
`buildRankedThemes()`, `platform-mcp/src/tools/register_p1_synthesis.ts` lines 381–471
(bucketing decision at 457–467). F-129 (per the finding's own description, `top_discoveries`
statement field) is built from a separate SQL query block in the same file, lines 815–822:

```ts
const discResult = await platformQuery(`
  SELECT discovery_id, affected_domains_array AS domains, surface_reading AS statement,
         composite_discovery_rank AS salience_score
  FROM bodha_discoveries
  WHERE chart_id = $1
  ORDER BY composite_discovery_rank DESC NULLS LAST
  LIMIT $2
`, [chart_id, discLimit], principal)
```

`top_discoveries[].statement` is a raw passthrough of `bodha_discoveries.surface_reading` (an L2
Bodha column), never touched by `buildRankedThemes`. The two findings are ~350–450 lines apart
in the same file, share no variables, no shared helper function, and draw from different upstream
tables (`mimamsa_insight_units` verdict rows for F-135 vs. `bodha_discoveries` for F-129). A fix
to one cannot regress the other; they should be treated as independent lanes despite the
file-level proximity.

## Verdict

**CONFIRMED, live-reproduced, TIER4-POLISH is a reasonable severity call given the mechanism.**
Not a bug in the sense of "code fails to implement its own logic correctly" — Stage 1 (occurrence
band → status) and Stage 2 (status → bucket) both execute exactly as documented and unit-tested.
It is a **design-boundary mismatch**: the `weaknesses` bucket's firing condition (`status ===
'denied'`, requiring grade < 2.0/10 — "largely absent or actively negated" evidence) is far
stricter than what the `ranked_themes` envelope's implicit contract (strengths / weaknesses /
open_questions as three peer buckets) leads a caller to expect. On this chart, five domains a
reader would naturally call "weak" (3.8–4.7/10) are demoted to the same `open_questions` bucket
as genuinely uncertain 5.8–5.9/10 domains, with no field distinguishing "low-conditional
(near-denied)" from "high-conditional (near-promised)" within `open_questions` itself.

**ESCALATE-TO-PRATINIDHI:** whether to (a) leave as-is (the rubric's `denied` threshold is a
deliberately blind, pre-registered classical-evidence judgment per bo_pratijna.py's own R13/R16
reasoning, and loosening it to match colloquial "weakness" would be scope creep into a sealed L2
rubric); (b) add a *serving-layer-only* distinction inside `buildRankedThemes` — e.g. sub-sort or
sub-flag `open_questions` entries below some display threshold (not a new `status` value, just a
presentation split) so a reader isn't left inferring "no weaknesses" from an empty bucket that
actually means "nothing was strongly denied, but 14 domains are read as conditional, several of
them on the low side"; or (c) rename/re-scope the `weaknesses` bucket's implied contract (e.g. in
docs/schema comments) so callers don't expect it to catch anything short of near-total classical
denial. This is a genuine design-intent question, not a bucketing-logic bug, and PAR-R-7 says it
should not be silently resolved by picking the safer-looking option — the fix's shape depends on
whether `weaknesses` is *supposed* to mean "denied" or "low-graded," and only the native/PRATINIDHI
can rule on which the `ranked_themes` contract was meant to promise.
