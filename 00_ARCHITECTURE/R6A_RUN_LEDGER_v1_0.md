---
canonical_id: R6A_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-11
role: Conductor log for R6 Wave A — Yoga & Cancellation Integrity, per
  CLAUDECODE_BRIEF_R6_YOGA_INTEGRITY_v1_0.md. Phases R6A.0–R6A.7. Native go-ahead received
  2026-07-11 ("My sending this is the go-ahead").
---

# R6A Run Ledger — Yoga & Cancellation Integrity (Wave A)

## PHASE R6A.0 — PREFLIGHT + AUTHORITY SETUP

**Register v2.0 status confirmed** (direct read, 2026-07-11):
- Y-1 (vacuous-pass fabricated yoga surface) — `FIXED [verify-against: prod, R6 2026-07-10]`
- Y-7 (vacuous fires stamped two_pass_verified) — `FIXED [verify-against: prod, R6 2026-07-10]`
- Y-9 (exclusion clauses never enforced) — `FIXED [verify-against: prod, R6 2026-07-10]`
- Y-2 (ga_yoga_firings unwired) — `OPEN` — **Wave B, out of scope for this brief**
- Y-3 (NBRY effectively absent) — `OPEN` — **Wave A, R6A.1**
- Y-4 (house-lord yoga family undetected) — `OPEN` — **Wave A, R6A.2**
- Y-5 (cancellation as a class unimplemented) — `OPEN` — **Wave A, R6A.1**
- Y-6 (D9 cross-check blind to cancellation) — `OPEN` — **Wave A, R6A.3**

**Y-1 non-regression on the Abhinandan clean-baseline build (2026-07-11, this session's prior
run)**: confirmed via the just-closed Abhinandan resume — `mimamsa_predictions`/`phala_anchors`
spot-checks showed no vacuous-pass fires reintroduced; the R6A_RUN_LEDGER predecessor
(R6_RUN_LEDGER) already recorded zero fabricated-surface regressions. Y-1 holds.

**Lead intelligence, per brief**:
- FABLE 5 authors the detection/cancellation logic (R6A.1–R6A.3) — dispatched via Agent tool with
  `model: fable`.
- Pratinidhi-R rules every classical choice (which rules, which aliases, which citations) —
  conductor re-reads `R5_AUTHORITY_DOSSIER_v1_0.md` fresh at each consultation, rules per §1
  precedence, logs to this ledger (not a separate judgment ledger — R6A is scoped narrower than R5,
  rulings logged inline per phase below).

**Governing discipline restated**: canonical-or-citation for every yoga relation and every bhanga
rule — cited classical source (BPHS / Phaladeepika / Saravali / Jaimini Sutras, chapter+verse or
catalog chunk_id) OR floored NULL+reason. No uncited rule fires. This is a HALT condition if
violated, not a style preference.

**Worktree**: `.claude/worktrees/r6a-cancellation-engine`, branch `r6a/cancellation-engine`, off
`origin/main` @ `3e265785` (post ph_nimitta fix, pre-Wave-A).

**may_touch** (per brief): `ga_yoga_writer.py` + `ga_structural_writer.py` (yoga + cancellation
evaluators), `bo_laksana.py` (D9 cross-check), `bodha_writers/formulas.py` (bhanga boost feed —
FEED the constant, never re-pick it), `l0_yogas.py` catalog seed (rule/citation corrections only,
versioned), surgical migrations (full-path cited), tests, `00_ARCHITECTURE` run/ledger docs +
register status updates.

**must_not_touch**: orchestrator/planner core (FROZEN), retrieval/serving surfaces (Wave B), chart
data `482012f1` before the native-rebuild phase, LEL rows, salience/priors CONSTANTS (feed the
bhanga BOOST value, don't re-pick it), battery/grading criteria.

**halt_conditions** (verbatim from brief): any writer completing with 0 rows · any
fabricated/vacuous fire reintroduced · a bhanga/yoga rule shipped WITHOUT a classical citation or
an explicit floor · chart-data write to `482012f1` before the native-rebuild phase · canary
regression with failed rollback.

Proceeding to R6A.1.

## PHASE R6A.1 — THE CANCELLATION ENGINE (Y-5 generic + Y-3 NBRY) — IN PROGRESS

**Grounding read** (conductor, before dispatch):
- `ga_writers/ga_yoga_writer.py` ~1172-1191: `bhanga_active`/`bhanga_na_reason` set — today only
  `KEMADRUMA_CANONICAL_ID` gets a real value; every other yoga floors NULL with an honest
  "no per-yoga bhanga formula implemented (avoid fabrication — B.10)" reason. Correct floor
  discipline today, just incomplete scope — this is exactly Y-5's gap.
- `ga_writers/ga_structural_writer.py` `_evaluate_catalog_rule` (~4666-4930): the Y-1/Y-7/Y-9
  hard-fail-on-unimplemented-shape logic, reusable dignity/kendra/house helpers
  (`dignity_of`, `is_kendra`, `is_trikona`, `graha_house`, `graha_sign`).
- `brahmagyan/l0_yogas.py`: `cancellation_conditions` catalog field is narrative-only
  (`{"weakened_if": ["mars combust", ...]}`) — not a structured evaluable shape; R6A.1 designs
  its own structured NBRY rule representation rather than force-fitting this narrative field.
- `pipeline/orchestrator/writers/bo_laksana.py` `_build_d9_cross_check_signals` (~1290-1462):
  the Y-6 bug, confirmed exactly as registered — `d1_tier>=2 and d9_tier<=-1` → hardcoded
  `"broken_promise"`, with `neechabhanga_modifier`/`cancellation_modifier` hardcoded `1.0` at
  lines 1417-1418 regardless of any real cancellation state (this is R6A.3's fix target, not
  R6A.1's — noted here for continuity).
- `bodha_writers/formulas.py` lines ~110-111/154-155/510-511/554-555: the salience-boost formula
  ALREADY multiplies by `neechabhanga_modifier`/`cancellation_modifier` — confirmed a pure
  feed-through (defaults 1.0), not a constant to re-pick. R6A.3 will feed it; R6A.1 does not
  touch this file.

**Dispatched** (2026-07-11): Fable-5 (model=fable), isolated worktree, background — tasked to
author: (a) a generic cancellation evaluator (Y-5) extending `bhanga_active` determination beyond
Kemadruma, with a reusable interface for R6A.2 to plug into later; (b) all 5 classical Neecha
Bhanga Raja Yoga rules, per-varga (D1 + D9), each with a real classical citation (BPHS/
Phaladeepika/Saravali/Jaimini Sutras) or an explicit floor+reason if no rule can be confidently
cited; (c) the golden-gate test reproducing the native's own Saturn/D9/Sun-in-kendra case; (d) a
negative-control test (no false positives); (e) regression confirmation against existing
ga_yoga_writer/ga_structural_writer test suites. Instructed: no LLM in the runtime path, no writes
to chart 482012f1, no touching formulas.py's constants, report ambiguities resolved via
less-scope rather than guessed.

**Fable-5 completed** (worktree `.claude/worktrees/agent-a5d1e382a148e756d`, branch
`worktree-agent-a5d1e382a148e756d`, changes uncommitted for review). Self-report: 4/5 NBRY rules
cited (BPHS Ch.39 / Phaladeepika Ch.7 chapter-grain, reusing the catalog's existing `BPHS_CH39`
citation anchor rather than inventing one), rule 5 (mutual-kendra) honestly floored (no confident
citation found); golden-gate test claimed passing; 22/22 new tests, 215/1-skip regression suite,
94-pass yoga/structural sweep claimed; changes confined to `ga_yoga_writer.py` (~628 lines) + new
`tests/test_r6a1_neecha_bhanga.py` (285 lines); no DB writes, chart `482012f1` untouched.

**RING-2 VERDICT: NOT SAFE TO MERGE AS-IS — 2 required fixes, 1 minor note.**
Independently re-ran all tests (confirmed 22/22 new, 215/1-skip regression exact match) but found:
- **Sweep count wrong**: implementer claimed 94 passed for `-k "yoga or structural"`; Ring-2
  independently got **221 passed, 0 failed** + 3 pre-existing unrelated collection errors
  (`test_forensic_writer.py`/`test_a3_writer.py`/`test_panchanga_writer.py`, confirmed via
  `git stash` to predate this diff — stale refs to the retired GA2 `forensic_render.ts`). Not a
  regression, but the implementer's own count was off by >2x and the errors went unreported —
  logged as a process note, not a blocker.
- **SERIOUS — L1-internal contradiction risk**: `ga_structural_writer.py` (lines ~2788-2849,
  `_build_structural_relationship_rows`, called unconditionally every build) ALREADY contains a
  separate, partial neecha-bhanga check — rule-2-only, D1-only, lagna-kendra-only (no Moon-kendra,
  no rules 1/3/4/5, no D9) — that writes `chart_facts.graha_composite_state_classification`
  (`"debilitation_cancelled"` vs `"debilitated"`). This is completely unreconciled with the new
  full 5-rule/D9-aware `ga_yoga_firings` NBRY evaluator. For any graha redeemed via rule 1, 3, 4,
  the D9 extension, or a Moon-kendra — real, reachable case shapes per the implementer's own test
  suite — the two L1 facts would DISAGREE on the same question for the same graha in the same
  chart. Two L1 facts contradicting each other is treated as halt-worthy in this project (§N.5's
  underlying principle, even though that section is nominally scoped to L2+ vs L1). **Fix
  dispatched back to Fable-5**: make the structural-writer's inline check defer to the new
  `evaluate_nbry`/`evaluate_bhanga` as single source of truth (preferred), or at minimum stop it
  from claiming flat "debilitated" when the fuller evaluator would disagree.
- **Misleading golden-gate narrative**: the shipped "golden gate" test forces the D9 path via a
  synthetic fixture (D1 Sun in Pisces house 12) to prove rule 2 fires through D9 — but per the
  project's own FORENSIC canon (Sun=Capricorn, Lagna=Aries for the real native chart), Capricorn is
  ALREADY the 10th-from-Aries kendra, so rule 2 fires in D1 ALONE for the real chart; D9 isn't
  actually what redeems the real native's Saturn. The implementer's own second test half-admits
  this but the "golden gate" framing overstated it. No test in the original submission loads real
  `chart_facts`/`chart_divisionals` rows for `482012f1` to validate the production path
  end-to-end — everything was synthetic. **Fix dispatched**: correct the test-file narrative to
  accurately describe synthetic-vs-real, and add a genuine read-only integration test against real
  chart `482012f1` data if practical.

Fix-iteration dispatched to the same Fable-5 agent (full context retained) via SendMessage.
Awaiting fix-iteration completion before re-verification + R6A.2 dispatch.

**Fix-iteration complete** (same worktree, changes still uncommitted). Fable-5 reports:
1. **Contradiction closed**: both `ga_structural_writer.py` neecha-bhanga checks now defer to
   `ga_yoga_writer.evaluate_nbry`/`detect_neecha_bhanga` via lazy imports (mirrors the existing
   reverse lazy-import direction already used elsewhere in this file, avoiding a circular import).
   `_build_structural_relationship_rows` gained an optional `conn` param (threaded from both real
   call sites, `build_ga_structural` ~L5052 and `build_ga_structural_substep` ~L6210) so it can
   load D9 positions via the existing `_load_varga_positions` helper; `graha_composite_state_
   classification` is now computed from the SAME full 4-cited/1-floored rule set as
   `ga_yoga_firings.bhanga_active`, not the old narrow rule-2/D1/lagna-only inline check. `conn=None`
   degrades honestly to D1-only with a logged warning (never fabricates). The legacy no-DB-catalog
   fallback path (`_evaluate_yoga_fires`'s `NEECHA_BHANGA_RAJA_YOGA` branch, no `conn` in its
   signature) stays D1-only, documented in-code as an honest narrowing, not a silent gap.
2. **Golden-gate narrative corrected**: split into 3 tests — `TestGoldenGateSyntheticD9Extension`
   (explicitly labeled synthetic, isolates the D9 mechanism in isolation), `TestGoldenGateReal
   NativeShape` (uses the real FORENSIC-anchored chart shape, correctly shows rule 2 already
   redeems Saturn from D1 alone — Capricorn is the 10th-from-Aries kendra), and new
   `TestGoldenGateRealChartIntegration` (reads REAL `chart_facts`/`chart_divisionals` for
   `482012f1` read-only, `pytest.skip()`s honestly when no DB is reachable in this environment
   rather than fabricating a pass — confirmed no DB reachable, skip fires).
3. **Test-count discrepancy resolved**: re-ran from the `python-sidecar` root (not scoped to
   `tests/`, which is what undercounted originally) — 221 passed/0 failed/3 pre-existing unrelated
   collection errors, matching Ring-2's independent figure exactly. New suite: 22 passed, 1 skipped
   (the DB integration test).

Diff now: `ga_structural_writer.py` (+107/-9, defer logic + call-site threading),
`ga_yoga_writer.py` (unchanged from original submission, +628/-14), new
`tests/test_r6a1_neecha_bhanga.py` (golden-gate section rewritten/expanded). Nothing committed.

**Re-verification dispatched** to the same Ring-2 agent (full context retained) — confirm the
contradiction is genuinely closed (not just "the word evaluate_nbry appears somewhere"), the
corrected tests test what they claim, no circular-import breakage, no scope drift. Awaiting
verdict before merge.

**RING-2 RE-VERDICT: SAFE TO MERGE.** Both required fixes independently confirmed genuine, not
cosmetic:
- **Contradiction closure**: verifier read the actual diff hunk (old rule-2/D1/lagna-only block
  fully deleted, replaced by a real call to `evaluate_nbry`), then went further than reading —
  **constructed an independent synthetic case not in the implementer's own test suite** (Saturn
  debilitated in Aries, redeemed ONLY via rule 3 — Mars aspecting from the 8th, a case the OLD
  code structurally could not have seen since it only checked rule 2/lagna-kendra) and ran it
  directly against `_build_structural_relationship_rows`: returned `debilitation_cancelled`,
  proving the fix generalizes to all 4 cited rules, not narrowly patched for the one case
  originally flagged. Confirmed clean circular-import resolution (both modules compile + import
  in both orders) and an honest, logged D1-only degrade when `conn=None` (never silent
  misclassification).
- **Golden-gate narrative**: confirmed all 3 split tests test exactly what their names claim;
  confirmed `TestGoldenGateRealChartIntegration` genuinely skips (`DATABASE_URL not set`, verified
  no such env var/`.env.local` exists) rather than vacuously passing.
- **Test counts**: independently reproduced exactly — 22 passed/1 skipped new suite; 221
  passed/0 failed/3 pre-existing unrelated collection errors on the broader sweep.
- **Scope**: confirmed unchanged — only `ga_structural_writer.py` + `ga_yoga_writer.py` +
  new test file; no touch to `bo_laksana.py`/`formulas.py`/`l0_yogas.py`; `482012f1` appears only
  in the new read-only integration test's `SELECT`, never in a production write path.

**MERGED**: PR #542 (`r6a/cancellation-engine`) — committed excluding the two ambient
`CONDUCTOR_HALT_LOG.md` noise files (unrelated concurrent-process auto-appends, confirmed not
part of this work), auto-merge enabled, CI running. Worktree `agent-a5d1e382a148e756d` (renamed
to branch `r6a/cancellation-engine`) is the source; the earlier empty manually-created
`.claude/worktrees/r6a-cancellation-engine` scaffold was removed as redundant.

**PHASE R6A.1: CLOSED — CONFIRMED MERGED.** PR #542 needed one resync (main advanced past it via
the docs-only PR #541 first) — re-merged origin/main into the branch, re-pushed, CI re-ran clean
(Governance Gates' pytest step ~12m38s, matching this campaign's known "larger suite = longer
step" pattern, not a stall). Merge commit `09b29eaa0887dadf1acc85cde136b210823ffc31` confirmed on
`origin/main`. Worktree `agent-a5d1e382a148e756d`/branch `r6a/cancellation-engine` cleaned up.

## PHASE R6A.2 — HOUSE-LORD YOGA FAMILY (Y-4) — IN PROGRESS

**Grounding read** (conductor, current code post-R6A.1 merge): `ga_yoga_writer.py`'s main
relation-evaluation loop has a ~27-relation skip-list tuple (grep
`"4th_and_9th_lords_in_mutual_kendra"` to locate — includes Viparita family markers, Dhana
combinations, Kendra-Trikona Raja, Dharma-Karmadhipati, Daridra-adjacent, a Kala-Sarpa relation
form, Shakata, and others) carrying the exact false comment the register's Y-10 already flags:
"The ga_structural writer (GA8) does yoga_fires rows that handle these. Here we conservatively
skip rather than fabricate." `_check_house_lord_association(state, h1, h2)` and
`_check_kendra_trikona_raja(state)` are confirmed hardcoded `return False` stubs (currently only
reachable via the Dharma-Karmadhipati and Kendra-Trikona-Raja branches respectively).

**Dispatched** (2026-07-11): Fable-5 (model=fable), fresh isolated worktree, background — tasked
to: (a) implement real relation-evaluators for the house-lord families (Viparita Raja Yoga —
Harsha/Sarala/Vimala via dusthana-lord-in-dusthana; Dhana Yoga — 2nd/5th/9th/11th lord
associations; Kendra-Trikona Raja Yoga — any kendra-lord+trikona-lord association, the classical
Raja Yoga definition; Dharma-Karmadhipati — 9th+10th lord association, implementing
`_check_house_lord_association` generically; Daridra Yoga — 11th lord dusthana placement; Shakata
Yoga — Moon/Jupiter mutual 6th/8th, cross-checked against the existing
`jupiter_in_kendra_from_lagna` exclusion already implemented in `ga_structural_writer.py`'s
`_evaluate_catalog_rule`); (b) investigate whether the skip-list's "Kala-Sarpa relation form" is a
duplicate of an existing dosha-form implementation elsewhere (remove if redundant, cite existing
catalog entries rather than re-deriving from memory where possible); (c) plug into R6A.1's
`_BHANGA_EVALUATORS` registry for any yoga with a genuine classical cancellation rule, leave
floored otherwise; (d) replace the false Y-10 comment; (e) tests including a regression check
against R6A.1's own NBRY test suite. Same hard constraints as R6A.1 (no LLM in runtime path, no
writes to chart 482012f1, no touching formulas.py, no orchestrator/serving/LEL). Instructed:
per-relation floor-vs-cite disclosure, less-scope on genuine ambiguity, no commit/push.

Awaiting agent completion before Ring-2 verification.

**Fable-5 completed.** 15 relations implemented, all citations reused from existing catalog rows
(verified against `l0_yogas.py`: `dharma_karmadhipati`/`kendra_trikona_raja_yoga`/
`parivartana_raja_yoga`→BPHS Ch.39, Viparita family→Phaladeepika Ch.7, `raja_yoga_lagna_9th`→BPHS
Ch.40, Dhana family→BPHS Ch.41, `pravrajya_yoga`→BPHS Ch.36, Daridra/Shakata→Saravali+BPHS). 14
relations floored with specific per-relation reasons (`R6A2_FLOOR_REASONS` dict) — including
identifying the skip-list's Kala-Sarpa relation-form entry as a legacy duplicate of the existing,
real `ga_structural_writer._detect_kala_sarpa` (writes `kala_sarpa_per_varga` rows) — pointed at,
not reimplemented. Zero new `_BHANGA_EVALUATORS` entries (deliberate, documented per-case: no
citable classical cancellation rule for any of these). `_check_house_lord_association`/
`_check_kendra_trikona_raja` are now real, generic, mutual-aspect-only, fail-closed on missing
lagna/lord data. 41 new tests + R6A.1's NBRY suite confirmed passing unmodified.

**RING-2 VERDICT: SAFE TO MERGE.** Independently: confirmed the false Y-10 comment is genuinely
gone from source (not moved/renamed); confirmed 4+ citation claims trace to real pre-existing
catalog rows, not invented; confirmed `_BHANGA_EVALUATORS` dict is byte-identical to what R6A.1
shipped (untouched); confirmed `ga_structural_writer._detect_kala_sarpa` is a real, non-stub
implementation, correctly pointed at with no double-fire path. **Built independent synthetic test
cases not in the implementer's own suite** (same discipline as R6A.1's re-verification): a
same-lord-pair scenario (Taurus lagna, Saturn lords both 9th+10th) correctly returns no
association; a one-way-drishti-only scenario (Mars aspects Mercury's house via its special 4th
aspect, but Mercury's default 7th-only aspect doesn't reach back) correctly returns no association
— confirming "mutual aspect only" holds exactly as documented and fails closed on missing data
rather than crashing or vacuously firing. Test counts reproduced exactly (41 new; 265/1-skip
combined regression); one minor process note — the implementer's full-suite failure count (41)
undercounted by 6 relative to Ring-2's own run (47), all 6 extra failures independently confirmed
via `git stash` to be pre-existing and unrelated (panchang/muhurat serialization drift, an
unrelated dict-shape issue, a writer-completeness registry gap) — not a blocker, logged as a
process note same as R6A.1's test-count discrepancy. No comparable cross-check conflict to R6A.1's
found (Shakata's exclusion logic is self-contained; the debilitation-cancellation floor correctly
defers to R6A.1's NBRY rather than re-implementing).

**MERGED**: PR #543 (`r6a/house-lord-family`), committed excluding the ambient `CONDUCTOR_HALT_LOG.md`
noise files, auto-merge enabled, CI running (branch confirmed NOT behind main this time — no
resync needed).

**PHASE R6A.2: CLOSED — CONFIRMED MERGED.** No resync needed this time (branch was not behind).
Merge commit `c7bf4c69cf4df581934669e92b86c4bbf80ec602` confirmed on `origin/main`. Worktree
`agent-a1517fbdc291ba11f`/branch `r6a/house-lord-family` cleaned up.

## PHASE R6A.3 — D9 CROSS-CHECK CONSULTS CANCELLATION (Y-6) — IN PROGRESS

**This is the second and most important native golden-gate catch** — the exact inversion the
native caught on his own chart (Saturn misread as `broken_promise` when neecha-bhanga-redeemed).

**Grounding read**: `bo_laksana.py`'s `_build_d9_cross_check_signals` (~lines 1290-1462,
untouched by R6A.1/R6A.2 as expected) unconditionally classifies `d1_tier>=2 and d9_tier<=-1` as
`"broken_promise"` with `neechabhanga_modifier`/`cancellation_modifier` hardcoded `1.0` at
~lines 1417-1418, zero awareness of R6A.1's now-live NBRY evaluation. Confirmed the function
already receives `conn`/`chart_id`/`ayanamsha_id` — meaning it can query the L1 `ga_yoga_firings`
table (populated by R6A.1, live on main) directly rather than recomputing cancellation logic
itself.

**Architecture rule emphasized to the agent** (explicitly, twice, in the dispatch prompt): L1
(`ga_yoga_writer.py`) is the authority over L2+ (`bo_laksana.py`) for this fact — `bo_laksana.py`
must NOT reimplement/duplicate NBRY, only consult `ga_yoga_firings` as the single source of
truth. This is the exact class of bug R6A.1's own Ring-2 review caught and fixed in
`ga_structural_writer.py`; explicitly flagged so it isn't repeated here.

**Dispatched** (2026-07-11): Fable-5 (model=fable), fresh isolated worktree, background — tasked
to: (a) before classifying `broken_promise`, query `ga_yoga_firings` for an active
`neecha_bhanga_raja_yoga` redemption for the graha in question, classify as a new distinct
`"redeemed"`/`"neecha_bhanga"` value instead if found (following the existing
build-lookup-dict-once-then-use-per-graha pattern already in this file, mirroring
`_build_d1_dignity_map`/`_build_d9_dignity_map`); (b) feed real (not hardcoded 1.0)
`neechabhanga_modifier`/`cancellation_modifier` values per `formulas.py`'s own documented
semantics (read-only — formulas.py itself is not to be edited, only fed); (c) the golden-gate
test: synthetic unit test + a real read-only integration test against chart_facts/ga_yoga_firings
for `482012f1` (skip gracefully if no DB reachable, same pattern as R6A.1); (d) negative-control
test (genuinely uncancelled debilitations still classify `broken_promise`); (e) regression
confirmation against bo_laksana's own suite + R6A.1/R6A.2's suites (files not touched, must still
pass). Constraints: no LLM in runtime path, read-only queries against 482012f1 permitted for the
integration test but no writes, no edits to formulas.py, no orchestrator/serving/LEL. Scope for
this phase narrowed to `bo_laksana.py` + new tests only.

Awaiting agent completion before Ring-2 verification.

**Fable-5 completed** with one useful correction to the brief: the real function name is
`_build_navamsha_cross_check_signals`, and a debilitated D1 graha (tier=-2) can never literally
reach the `broken_promise` branch (requires `d1_tier>=2`) — the native's redeemed Saturn was
actually landing in `concordant_weak`/`vargottama_resilience`/`mixed`, all equally bhanga-blind
with hardcoded modifier 1.0. Fix: a new `neecha_bhanga_redeemed` classification checked FIRST in
the branch chain (before every tier branch, not just `broken_promise`), consulting
`ga_yoga_firings` once per chart/ayanamsha (mirroring the existing dignity-map-lookup pattern).
`neechabhanga_modifier` fed as 1.3 per `formulas.py`'s own documented "cancelled debility"
semantics (file untouched); `cancellation_modifier` deliberately left at 1.0 (that field means
"cancelled yoga," a distinct concept from a redeemed debility). Golden-gate: synthetic test
passes; real-data integration test correctly `pytest.skip()`s — honestly reported that no
`neecha_bhanga_raja_yoga` rows exist in ANY reachable environment yet, since no chart has been
rebuilt against R6A.1's writer (expected — R6A.5 is exactly where this closes for real). 13 new
tests (12 pass/1 skip), 0 regressions (123 passed/1 skip across bo_laksana + R6A.1/R6A.2 suites,
confirmed unmodified).

**RING-2 VERDICT: SAFE TO MERGE — extra scrutiny applied given this phase's safety-criticality.**
Independently traced the tier arithmetic itself (not trusting the implementer's claim) and
confirmed: debilitated (tier=-2) genuinely cannot hit the old `broken_promise` branch — this is a
real fix, not a rationalization. Confirmed `formulas.py` untouched and semantics match exactly.
**Independently queried the actual reachable dev DB directly** (not trusting implementer's
DB-unavailability claim) — corroborated: native chart has only 4,876 `chart_facts` rows (vs
canonical 27,554), zero `neecha_bhanga_raja_yoga` rows anywhere, and (bonus finding) 3 FORENSIC-gate
halts in the log showing this dev DB's chart `482012f1` data mismatches ALL 7 forensic anchors —
strong confirmation this is materially different/wrong data, not just an incomplete build.
Constructed 4 independent adversarial test cases beyond the implementer's own suite (mixed
malformed+valid `bhanga_rule_fired` strings, unknown/typo planet name, a **reversed
`D9->D1` context string** — the one case that could plausibly have broken a naive `startswith`
parser, and didn't — and duplicate firing rows) — all held correctly. One minor process note (same
recurring pattern as R6A.1/R6A.2): implementer's "41 pre-existing failures" figure undercounted
the real baseline of 47 — verified via `git stash` that the SAME 47 fail identically with and
without this diff, so zero regressions either way, just an imprecise self-reported count. Judged
the "golden gate not yet validated against real production data" gap as an acceptable interim
state at this point in the campaign (R6A.5 is explicitly the venue designed to close it) rather
than a merge-blocker, since the code logic itself is sound and the test is correctly written to
validate for real once data exists.

**MERGED**: PR #544 (`r6a/d9-cross-check-redemption`), committed excluding ambient
`CONDUCTOR_HALT_LOG.md` noise, auto-merge enabled, CI running.

**PHASE R6A.3: CLOSED — CONFIRMED MERGED.** Merge commit `58b27b6f5ebb80c22f15422981608e06fa137f96`
confirmed on `origin/main`. Worktree `agent-a93ac61beb5f741bc`/branch
`r6a/d9-cross-check-redemption` cleaned up. Both native golden-gate catches now have code-level
fixes on main: (a) NBRY fires for Saturn (R6A.1), (b) D9 cross-check reads redeemed not
broken_promise (R6A.3).

## PHASE R6A.4 — VERIFY Y-1 HOLDS + HONESTY — CLOSED

Lighter confirmatory phase, done directly (no Fable-5 dispatch needed — pure verification, not
new authorship).

1. **Y-1 hard-fail logic confirmed intact** post-R6A.1/R6A.2: read `_evaluate_catalog_rule`
   (`ga_structural_writer.py:4729`) — every unrecognized shape (empty `requires`, unstructured
   string, non-dict element, unimplemented relation/planet-subkey/house-class/exclude value)
   still hard-fails to `(False, "rule_shape_unimplemented:*"/"relation_unimplemented:*")`;
   `(True, "requires_pass")` only reached after every named check passes. R6A.1's reconciliation
   of the neecha-bhanga contradiction touched a different function
   (`_build_structural_relationship_rows`) — confirmed no overlap with this evaluator.
2. **Regression confirmed**: R6A.1/R6A.2/R6A.3 suites — 75 passed/2 skipped combined;
   `test_bo_a1_fixes.py` — 49 passed (run separately per-file; running all four together hit a
   pytest double-import collision on `bo_laksana.py`'s `@register` decorator, a test-collection
   artifact from combining directories, not a real regression — confirmed by running files
   individually).
3. **Gap found and closed**: the ORIGINAL Y-1 fix (commit `caa0b727`, PR #517, 2026-07-10) was
   never given a permanent committed regression test — verified only via an ad-hoc "158/158"
   pytest run at merge time (confirmed via `git show --stat caa0b727`: only
   `ga_structural_writer.py` + a `.ts` file changed, zero test files). Wrote
   `tests/test_r6a4_y1_antifabrication.py` (11 tests) to close this permanently: the exact
   OCR-corpus `raw_verse_clause` shape that caused the original fabricated-yoga-surface bug,
   empty/unstructured/non-dict `requires`, unrecognized relation/planet-subkey/house-class/exclude
   values — all hard-fail; plus 2 positive-control tests confirming genuine evaluable rules still
   fire correctly (fail-closed discipline hasn't become over-aggressive). All 11 pass.
4. **`ga_yoga_firings` spot-check** (read-only, dev DB): all yoga_canonical_ids present
   (`amala`, `anapha`, `budha_aditya`, `pasha`, `ubhayachari`, `vasi`, `vesi`) are real classical
   yoga names — zero OCR-garbage entries (no `cnja_kesari`/`dariclra`/etc. of the kind the
   original Y-1 bug produced). Data is sparse (pre-rebuild, consistent with R6A.3's finding that
   no chart has been rebuilt against R6A.1's NBRY writer yet) but clean.

**PHASE R6A.4: CLOSED.** Committed as a small standalone PR (test-only, no production code
change) rather than a full worktree+Fable-5+Ring-2 cycle, since this phase is pure verification
with one small permanent-test-gap closure — reviewed by the conductor directly.

---

**WAVE A BUILD-SIDE CODE: COMPLETE (R6A.0–R6A.4).** All build-side fixes for Y-1/Y-3/Y-4/Y-5/Y-6
are now on `main`. Both native golden-gate catches have code-level fixes, each independently
Ring-2 verified (R6A.1 with 2 rounds after a real contradiction was caught and fixed; R6A.2 clean
on first pass; R6A.3 with extra scrutiny given its safety-criticality, also clean). Neither golden
gate has yet been validated against REAL rebuilt chart data — that is exactly what R6A.5 (the
guarded Abhinandan re-zero) is for. **Proceeding to R6A.5 next — a live guarded production rebuild,
the proving ground where both golden gates get their first real-data validation. Native briefed
before proceeding, per the significance of this phase.**

**PR #545 (R6A.4) confirmed merged** — commit `00faf881f48a1d947d5357af81d89851642780ef`.
Worktree/branch `r6a/y1-antifabrication-test` cleaned up.

## PHASE R6A.5 — RE-ZERO ON ABHINANDAN (guarded rebuild, the proving ground)

**Gate 1 (deploy-truth)**: `gcloud run jobs describe brahma-build-pipeline-job` shows the deployed
image tag = `58b27b6f5ebb80c22f15422981608e06fa137f96` (R6A.3's merge commit — contains all of
Wave A's runtime logic: R6A.1 NBRY evaluator, R6A.2 house-lord family, R6A.3 D9 cross-check fix).
R6A.4 added zero production code (test file only, confirmed via its PR diff) — no further deploy
needed before this rebuild exercises the corrected behavior. Deploy-truth confirmed, not assumed.

**Pre-rebuild snapshot** (exact `COUNT(*)`-based, not `wc -l` — no `\copy`/psql file-dump access
in this environment, so this is a SQL-count baseline rather than a full file dump; relying on the
already-verified idempotent per-writer discipline — delete-then-insert scoped to `chart_id`,
IRREPLACEABLE-outcome rows protected by PR #539's `mi_bhavisya` fix — as the safety net for a full
rebuild):
- All 61 chart-scoped assets for `1c826d5a`: `state='lit'`, 0 errors. Full per-asset `rows_written`
  baseline recorded (largest: `ga_dashas`=471,122; `ka_taranga`=79,728; `bo_laksana`/
  `bo_samskara`/`ka_kalasutra`/`ka_yojaka`=66,747 each; `mi_adhilepa`=127,041; `ga_structural`=
  103,491; `ga_vargas`=37,020).
- **`mimamsa_predictions`: 200/200 rows `lifecycle_status='pending'`** — zero confirmed/denied
  outcomes recorded yet for this chart. Zero IRREPLACEABLE-data risk from a full rebuild right now.
- **`life_events` (LEL): 0 rows** for this chart. Zero LEL risk.

Proceeding to fire the guarded global rebuild.

**Fired via Nirmāṇa UI (Playwright)**: clicked global "Rebuild" — dialog confirmed exact scope
(L1-L5, 54 assets, 1,111,415 rows to be deleted, L0 Brahma Jñāna correctly excluded), typed the
subject-name confirmation ("Abhinandan Mohanty"), confirmed. UI showed "Clearing 67 assets across
60 tables…" in progress, then correctly chained into a rebuild automatically (per
`handleAfterClear()`'s real POST to `/api/cockpit/runs`, verified via source-reading earlier this
session). **Confirmed via direct DB read**: new `build_runs` row `3e128fd5-11a3-430e-bfc0-fbf9dcb3b9f6`,
`scope='global'`, `action='rebuild'`, `state='running'`. Beginning guardian monitoring — early
progress confirmed real (not a false success): `ga_positions`=lit/530 rows,
`ga_sensitive`/`ga_vargas`=building with real in-progress row counts, `mi_jivanaghatana`=lit
(global-scope carryover, unaffected by chart-scoped clear as expected).

**Progress checkpoint (~20min in)**: 27/61 lit, 2 building, 1 stale, 0 errors, currently on
`bo_drishti` (Bodha layer). `ga_structural` completed: 103,491 rows — exact match to the
pre-rebuild baseline (consistency check passes). `ga_yoga` completed: **56 rows, up from the
pre-rebuild baseline of 30** — the increase is exactly what R6A.1+R6A.2 predict (previously
skip-listed house-lord relations + NBRY now actually firing instead of being silently dropped).

**First live confirmation of Wave A's new logic on REAL production data** (spot-check of
`ga_yoga_firings`, mid-rebuild): `neecha_bhanga_raja_yoga` fired=true, **`bhanga_active=true`**,
real citation present, 5 rows (one per ayanamsha) — R6A.1's NBRY evaluator genuinely detecting a
redeemed debilitation in Abhinandan's real chart, not just in synthetic tests. **This is golden
catch (a) — NBRY fires where classically applicable — already confirmed true**, ahead of full
gate-stack verification. Also firing with real citations, zero OCR-garbage names:
`kendra_trikona_raja_yoga`, `dhana_yoga_lagna_2`, `daridra_yoga`, `vipareeta_harsha`,
`vipareeta_sarala` (all R6A.2 house-lord relations) alongside the pre-existing real yogas (`amala`,
`anapha`, `budha_aditya`, `pasha`, `ubhayachari`, `vasi`, `vesi`). Continuing to monitor through
the L2-L5 cascade — golden catch (b) (D9 cross-check reading `neecha_bhanga_redeemed`) can only be
checked once `bo_laksana` (L2 Bodha) completes.

## R6A.5 — REBUILD COMPLETE, FULL GATE-STACK RESULTS

**Terminal state**: `build_runs.3e128fd5` → `state='completed'`, `last_error=null`.
**Gate 1 — all assets lit, 0 errors**: 61/61 chart-scoped assets `state='lit'` (confirmed via
direct `GROUP BY state` — only one state value present across the whole set: `lit`). 5 global-scope
assets (`mi_kula`, `mi_vistara`, `ka_graha_sancara`, `ka_gochara`, `ka_muhurta_seva`) confirmed
`lit`. **61 + 5 = 66/66, full reconciliation, zero errors, zero strays.**

**Gate 2 — yoga surface REAL**: full `ga_yoga_firings` sweep for this chart (not just the
mid-rebuild spot-check) — **zero fired rows with a missing citation**, across every
`yoga_canonical_id` present (`amala`, `anapha`, `budha_aditya`, `daridra_yoga`,
`dhana_yoga_lagna_2`, `kendra_trikona_raja_yoga`, `neecha_bhanga_raja_yoga`, `pasha`,
`ubhayachari`, `vasi`, `vesi`, `vipareeta_harsha`, `vipareeta_sarala`) — all real classical yoga
names, zero OCR-garbage entries, zero uncited fires.

**Gate 3 — house-lord yogas detected where present**: 5 distinct R6A.2 house-lord relations fired
for Abhinandan's real chart configuration (`kendra_trikona_raja_yoga`, `dhana_yoga_lagna_2`,
`daridra_yoga`, `vipareeta_harsha`, `vipareeta_sarala`) — plausible given his real placements
support some but not all 15 possible relations (the other 10 correctly did not fire, since his
chart doesn't satisfy their formation conditions).

**Gate 4 — cancellation evaluator ran**: `neecha_bhanga_raja_yoga` — 5/5 ayanamshas fired=true,
`bhanga_active=true`, real `bhanga_rule_fired` + `citation_ref` populated on every row. Not a
floor-only result — the evaluator genuinely detected and confirmed a real redemption.

### THE THREE GOLDEN CATCHES — ALL CONFIRMED ON REAL PRODUCTION DATA

**(a) NBRY fires where classically applicable** — CONFIRMED. `neecha_bhanga_raja_yoga`
`bhanga_active=true` across all 5 ayanamshas for Abhinandan's real chart, with real citations —
not a synthetic test, genuine live detection.

**(b) D9 cross-check reads `neecha_bhanga_redeemed`, not `broken_promise`, for the redeemed
graha** — CONFIRMED. Queried `bodha_msr_signals` (`navamsha_d9_cross_check:*` signals, R6A.3's
consult-first classification): **Jupiter → `neecha_bhanga_redeemed` across all 5 ayanamshas**
(salience 1.6, matching the fed `neechabhanga_modifier=1.3` boost path); Mercury → redeemed in 1
of 5 ayanamshas, `mixed` in the other 4 (ayanamsha-dependent placement variance — plausible, not
a bug). **The one `broken_promise` row in the entire dataset is for Ketu** — a lunar node, and
R6A.1 explicitly documented (LESS-scope decision) that NBRY is evaluated for the 7 classical
grahas only, nodes excluded, since classical neecha-bhanga doctrine doesn't extend to Rahu/Ketu.
Ketu was never eligible for redemption in the first place — this is the evaluator working exactly
as designed, not a gap. All 7 other grahas (Sun, Moon, Mars, Venus, Saturn, Rahu, and the
non-redeemed portion of Mercury) correctly show `mixed`/`concordant_strong`/`concordant_weak` —
none show a spurious `broken_promise` for a graha that should have been redeemed.

**(c) Yoga surface real, no fabrication, no contradictory pairs** — CONFIRMED (restates gate 2).
Zero uncited fires, zero garbage names, across the complete dataset.

**R6A.5: PASSED. All gates including all three golden catches confirmed on real, live-rebuilt
production data for Abhinandan (1c826d5a) — not synthetic tests, not partial spot-checks.**

**Awaiting explicit native go-ahead before R6A.6 (the native chart rebuild) — reporting now per
the standing instruction to check in at this exact checkpoint.**

## ⚖ NATIVE GO RECEIVED — PHASE R6A.6 (THE NATIVE REBUILD)

Native gave explicit GO for R6A.6 with the full protocol specified: exact-count snapshot before
any build, guarded global Rebuild via Nirmāṇa + Chrome MCP (owner/super_admin, WORKER_LIMIT=2,
guardian discipline), post-rebuild gates keyed on Saturn (the three golden catches) plus standing
gates (FORENSIC 7/7 ×5, LEL 57 rows + calibrated + 10:43 held, bhava_arudha 12×5, JL-009 traced,
degeneracy sweep, Abhinandan contamination-clean), HALT + restore-from-snapshot on any failure
with NO iteration on the native chart.

**Pre-rebuild snapshot** (exact-count-verified, PF-1 discipline — real `\copy` file export this
time, direct `psql` access via `platform/.env.local`'s `DATABASE_URL` through the already-running
`cloud-sql-proxy` on port 5433, confirmed working): 127 chart-scoped tables enumerated. Exported
every non-empty table for `482012f1` via `\copy ... CSV header`, `statement_timeout=300000` (the
truncation lesson — never trust a default/short timeout on a large table). Verified via Python's
`csv` module (not `wc -l`) against a **freshly re-queried** live `COUNT(*)` per table (not the
count captured at export time — catches any drift during the export window):

**VERIFIED: 9 non-empty tables, 5,211 total rows, ZERO mismatches.** Snapshot files at
`{scratchpad}/r6a6_snapshot/csv/*.csv`; restore path: `\copy <table> FROM '<file>.csv' CSV header`
per table (rehearsed restore mechanics already established earlier in this campaign's PF-2 work).

**Important finding, verified not assumed**: 9 tables/5,211 rows is far below the
`L1_GANITA_CLOSURE`-era historical baseline (chart_facts alone was 27,554 at that closure). Cross-
checked this is NOT a wrong-database artifact — confirmed via the independent `postgres` MCP tool
(the same tool used throughout this entire session for live production verification) that
`chart_facts` for `482012f1` shows the same **4,876** row count, and `asset_throughput` shows
**all 61 chart-scoped assets `state='dormant'`** for the native chart right now. This traces
directly to this campaign's own earlier work: PR #537 (the `ga_structural` clear-mechanism JOIN
bug fix, applied to BOTH charts) removed 196,987 rows including from `482012f1`, and the native
has not been rebuilt since — this is the genuinely current, correct, live state of the chart, and
exactly why R6A.6 (a full one-shot rebuild) is the pending action. The snapshot is valid and
verified against real current data, not stale/wrong data.

**Consequence for the rebuild trigger**: since native is fully dormant (0/61 lit), the Nirmāṇa
UI's top-level button will show **"Build" (not "Rebuild")** per `deriveAction()`'s
`dormant===total` logic — meaning the non-destructive `action='build'` path fires directly,
without the "Clear all chart data?" confirmation dialog (nothing lit to lose). This is the safest
possible trigger shape for this rebuild.

Proceeding to fire the guarded rebuild via Nirmāṇa + Playwright.

**Fired**: navigated to native's Nirmāṇa page — top-level button showed "Rebuild" (not "Build")
because the 5 global-scope carryover assets show as lit under `deriveAction()`'s counting, even
though all 61 real chart-scoped assets were confirmed genuinely `dormant`. Clicked Rebuild — dialog
confirmed a SMALL, low-stakes clear (only 105 rows via asset metadata: Gaṇita 90 + Mīmāṃsā 15, L0
correctly excluded, "2 assets cleared · 65 reset to dormant · 60 tables touched") — consistent
with the already-verified mostly-dormant state. Typed subject-name confirmation ("Abhisek
Mohanty"), confirmed. **Confirmed via direct DB read**: new `build_runs` row
`b06e28f8-3a44-4ddc-a444-a3dfb910aabe`, `scope='global'`, `action='rebuild'`, `state='planned'`.

Beginning guardian monitoring — WORKER_LIMIT=2 discipline, SSE + Cloud Run logs, no
completed-with-0, fix-and-redeploy + deploy-truth-reverify on any mid-build failure. **HALT +
restore-from-snapshot on any golden-catch failure or standing-gate miss. No iteration on the
native chart** per explicit native instruction.

**Progress checkpoint (~15min in)**: 9/61 lit, 1 building (`ga_strength`, historically ~11min),
0 errors. Real non-zero row counts across all lit assets (`ga_vargas`=37,020, `ga_strength`=11,620,
`ga_sensitive`=8,775, `ga_nakshatra`=1,802, `ga_panchanga`=437, `ga_positions`=530,
`ga_transit_anchors`=45, `mi_jivanaghatana`=57 — no false completed-with-0). Continuing to
monitor.

**Progress checkpoint (~30min in)**: 38/61 lit, 1 building (`ka_tulana`, Kāla L3), 0 errors.
`ga_structural` completed: 103,313 rows. `ga_yoga` completed: 50 rows.

**GOLDEN CATCH (a) CONFIRMED LIVE, EARLY** — direct spot-check of `ga_yoga_firings` mid-rebuild:
`neecha_bhanga_raja_yoga` fired=true, `bhanga_active=true`, `bhanga_rule_fired` contains
**`saturn@D9:nbry_rule_2_exaltation_lord_kendra`** — exactly the D9 rule-2 case the native
described (Saturn debilitated in D1 Aries, Sun exalts in Aries, sits in a kendra from the D9
lagna). Also confirmed: `venus@D9:nbry_rule_1_dispositor_kendra`/`nbry_rule_2_exaltation_lord_kendra`
— Venus independently redeemed too. `constituent_planets` includes `saturn`, `venus`, `mercury`,
`mars`, `sun`. 4 ayanamsha rows visible so far (rebuild still mid-cascade, 5th pending). Full
citation sweep + golden catch (b)/(c) + all standing gates to be run once the rebuild reaches a
terminal state and `bo_laksana` (L2) has completed.

## ⛔ R6A.6 HALT — GOLDEN CATCH (b) FAILED, RESTORED FROM SNAPSHOT, NO ITERATION ON NATIVE CHART

**Build itself completed mechanically clean**: `build_runs.b06e28f8` → `state='completed'`,
`last_error=null`, all 61/61 chart-scoped assets `lit`. This was NOT a build failure — every
writer ran, every asset landed real non-zero row counts, `ga_yoga`/`ga_structural` both completed
cleanly. **The failure is a golden-catch failure, caught post-build, exactly the class of failure
the native's protocol anticipated.**

**Golden catch (b) — FAILED.** Queried `bodha_msr_signals` for
`signal_type_id='navamsha_d9_cross_check:saturn'`, chart `482012f1`: **4 of 5 ayanamshas still
read `broken_promise`** (krishnamurti, lahiri_chitrapaksha, surya_siddhanta_classical,
true_chitra); the 5th (raman) reads `concordant_strong` — a different classification, still not
`neecha_bhanga_redeemed`. **Saturn does not read its own redemption on the native chart.**

**Root cause, investigated (not fixed — per explicit native instruction, no live fix on this
chart)**:
- Saturn's real D1 sign for chart `482012f1` is **Libra** (confirmed via direct `chart_facts`
  query, all 5 ayanamshas) — Libra is Saturn's classical **exaltation** sign, not debilitation.
  Saturn is D1-strong (tier ≥2), not debilitated at all in D1.
- `ga_yoga_firings.bhanga_rule_fired` for `neecha_bhanga_raja_yoga` shows, uniformly across all 4
  firing ayanamshas: `saturn@D9:nbry_rule_2_exaltation_lord_kendra` — the `D9` context tag (not
  `D1` or `D1->D9`) confirms Saturn is genuinely debilitated **within the D9/Navamsha chart
  itself** (in Aries), independently of D1, and that D9 debilitation is correctly detected as
  redeemed by rule 2 (R6A.1's evaluator worked correctly — this is golden catch (a), still true).
- **The gap is in R6A.3's `_build_nbry_redemption_map` filter**: per its own documented
  LESS-scope decision, only `D1`/`D1->D9`-context firings are consulted when deciding whether to
  flip a `broken_promise` classification to `neecha_bhanga_redeemed`. A pure-`D9`-context firing
  is filtered out. But the native's real chart is EXACTLY the case that filter excludes: D1-strong
  (Saturn exalted, tier≥2) + D9-weak (Saturn debilitated, tier≤-1) is precisely the formation
  condition for `broken_promise` in the first place — the D9 weakness IS the thing being judged,
  and its redemption (a pure-`D9`-context NBRY firing) is exactly what should be consulted to
  determine whether that D9 weakness is real or cancelled. R6A.3's filter, as shipped, structurally
  cannot ever redeem a `broken_promise` classification, because `broken_promise` is BY DEFINITION
  a D9-weakness case, and the filter only trusts D1-context redemptions.
- This was not caught by R6A.3's own tests or either Ring-2 review because all of R6A.1/R6A.2/R6A.3's
  synthetic and Abhinandan-real-data testing happened to exercise D1-context or D1→D9-extension
  redemption cases (Abhinandan's Jupiter redemption in R6A.5 was almost certainly a D1-context
  firing — not re-verified against this specific gap before now). The native's real chart is the
  first real data that exercises the pure-D9-context `broken_promise` redemption path, and it
  fails. **This is the "cross-chart-data-path exposure" pattern this campaign has already named
  once this session (M-23, ph_nimitta)** — a fix that looked clean on every prior data path hides
  a gap that only a new chart's real shape exposes.

**Standing gates and remaining golden catches**: NOT run to completion — per protocol, the moment
golden catch (b) failed, the correct action was HALT + restore, not continued gate-checking on
data about to be discarded.

**RESTORE EXECUTED AND VERIFIED**: chart `482012f1` restored from the pre-rebuild snapshot
(`\copy <table> FROM '<file>.csv'` per table, after a `DELETE ... WHERE chart_id=...` on each,
matching this project's idempotent delete-then-insert convention). Two dependency-order
complications handled: `phala_rectification`'s FK-dependent `phala_rectification_best` rows
cleared first, then `phala_rectification` itself; `charts` (master row, protected by FK, correctly
never touched) and `vw_chart_digest` (a view, not deletable, harmless) excluded from the
delete/restore loop as expected. **Final verification: 125 tables checked, ZERO mismatches against
the original snapshot counts. `asset_throughput`: 61/61 back to `state='dormant'`, exactly matching
pre-rebuild state.** Abhinandan (`1c826d5a`) independently confirmed unaffected: 61/61 still `lit`,
unchanged.

**R6A.6: HALTED. The fix did not land on the native chart. No iteration attempted, per explicit
native instruction. Native chart `482012f1` is back to its pre-rebuild (dormant) state, verified
exact. Awaiting native direction: this needs a genuine R6A.3 fix-iteration (extend the redemption-map
consult to include pure-`D9`-context firings specifically for the `broken_promise` formation case,
Ring-2 re-verified, re-validated on Abhinandan before any second attempt at the native) before
R6A.6 can be re-attempted.**

## ⚖ R6A.3 FIX-ITERATION APPROVED (native, 2026-07-11) — THE ONE AUTHORIZED ITERATION FOR Y-13

Native approved the fix-iteration with 5 precise directives (R5 one-iteration discipline — this
is it, no second round expected):
1. Fix the **principle** (varga-of-weakness: redemption consulted in the varga where the weakness
   lives), not just the one case — but **behavior-gate to the `broken_promise` path only**, with
   regression tests proving every other classification's output is unchanged.
2. Mandatory test set before Ring-2: (a) the exact live case as a permanent unit test + a new
   `GOLDEN_SIGNALS_482012f1_v1_0.yaml` row (standing rule: every real catch becomes a battery
   row); (b) Abhinandan's Jupiter still correct, explicit no-double-application proof; (c) negative
   control (unredeemed D9 debilitation stays `broken_promise`); (d) classification-value
   legality check before any write.
3. The 5th-ayanamsha divergence (4/5 `broken_promise`, 1/5 `concordant_strong`) gets its own
   verdict at Ring-2 time against FRESH rebuilt data — genuinely positional (navamsha-boundary
   sign flip near an ayanamsha offset) vs. a second defect — not to be shrugged past.
4. Register hygiene: **Y-13 added now** (OPEN, fix-iteration in progress), to close same-day with
   Ring-3 (prod) evidence once verified — found-fixed-same-day rows still get rows.
5. Re-attempt sequencing, unchanged canary discipline: fix → Ring-1 → Ring-2 (**fresh verifier**,
   explicitly attempting the double-application falsification) → rebuild the affected assets on
   **Abhinandan first** → gates → **then** the native chart re-attempt → report all 5 ayanamshas'
   final Saturn classifications.

**Y-13 logged** in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` §New rows (v2), full root-cause + evidence
citation, status `OPEN — fix-iteration approved by native 2026-07-11, in progress`.

**Fix-iteration dispatched** to Fable-5 (fresh isolated worktree, background) with all 5
directives given verbatim. Grounding: `bo_laksana.py`'s `_build_nbry_redemption_map` (~1296) and
`_build_navamsha_cross_check_signals` (~1351) read in full from current `main` (post-R6A.3-merge).
Instructed: keep the existing D1-context-only consult exactly as-is (it already correctly handles
D1-weak cases, e.g. Abhinandan's Jupiter — do not touch it); add a SEPARATE D9-context consult
reachable ONLY inside the `broken_promise` formation branch (`d1_tier>=2 and d9_tier<=-1`, and only
after the existing D1-context check already came back empty for that graha) — this makes
double-application structurally impossible by construction (the two branches are tier-disjoint),
not just asserted. Same target classification string (`neecha_bhanga_redeemed`, reused not
reinvented) with D9-varga provenance in `configuration_jsonb`. Explicitly told: the 5th-ayanamsha
divergence is NOT this task's job (no live data available post-restore to investigate it; deferred
to Ring-2 against fresh rebuilt data per directive 3). Do not commit/push.

Awaiting Fable-5 completion before Ring-2 (fresh verifier) dispatch.

**Fable-5 completed** (worktree `agent-a8dcecf4e46b9fbea`). All 4 mandatory tests (a/b/c/d) written
and passing, including a tier-disjointness sweep that imports the real `_DIGNITY_STRENGTH_TIER`
vocabulary (not a hardcoded copy). Zero regressions: 92 passed/2 skipped combined across
R6A.1/R6A.2/R6A.3 suites, none of the 13 pre-existing R6A.3 tests modified. GS-23 added to
`GOLDEN_SIGNALS_482012f1_v1_0.yaml`. Flagged one judgment call for Ring-2: `neechabhanga_modifier
=1.3` for the new D9-redeemed path (inferred from formulas.py's binary "cancelled debility"
semantics, not explicitly specified in the directives).

**RING-2 VERDICT (fresh verifier, per native's directive 5): SAFE TO MERGE.** All 10 claim groups
independently confirmed — if/elif mutual exclusivity traced directly in the code, shared
classification constant confirmed, provenance differentiation confirmed (D1 path never gains the
`redeemed_weakness_varga` key), test counts reproduced exactly, `ga_yoga_writer.py`/`formulas.py`
confirmed untouched, GS-23 parsed and validated. Constructed 2 independent adversarial cases beyond
the implementer's suite: the `concordant_strong` nearest-miss (D1-strong+D9-also-strong with a
D9-context firing present — confirmed the D9 consult is never even reached, since it sits inside
the `d9_tier<=-1` half of the `broken_promise` guard) and the mixed-zone tier boundary (confirmed
structurally unreachable by the same guard) — both held. Endorsed the `1.3` modifier judgment call
as the only semantically-consistent value per `formulas.py`'s own documented contract. One LOW
finding (mixed-zone boundary lacks an explicit test, though structurally moot) — non-blocking.

**MERGED**: PR #548 (`r6a-3/y13-d9-context-redemption`) — needed one resync (a docs-only ledger PR
#547 merged first), re-pushed, CI passed clean on the merge commit. **Deploy-truth confirmed**:
`gcloud run jobs describe brahma-build-pipeline-job` → deployed image tag
`e28762dfc7526d568da9bbaf731168292979f649`, exact match to the merge commit.

**Re-attempt sequencing, step 1 — Abhinandan-first rebuild (native directive 5)**: fired a scoped
per-asset rebuild on Abhinandan (`1c826d5a`) targeting ONLY `bo_laksana` (not global) — confirmed
via the "Confirm build" dialog listing exactly 1 asset before confirming, and via direct
`build_runs` read: `scope='asset'`, `scope_target='bo_laksana'`. Completed cleanly, `last_error=null`.

**Gate check — Jupiter (the known D1-context redemption) CONFIRMED UNCHANGED on real data**:
`navamsha_d9_cross_check:jupiter` → `neecha_bhanga_redeemed` across all 5 ayanamshas, `varga=null`
on every row (confirming it's still classified via the untouched D1-context path, not accidentally
routed through the new D9 path). **Full graha sweep is byte-identical to R6A.5's known prior
result**: Jupiter redeemed 5/5; Mercury redeemed 1/5 + mixed 4/5; Ketu `broken_promise` ×1 + mixed
×4 (the sole remaining `broken_promise` instance in Abhinandan's chart — Ketu is a lunar node,
correctly outside NBRY's scope by R6A.1's own design, not a miss); Mars/Moon/Rahu/Saturn/Sun all
`mixed` ×5; Venus `concordant_strong` ×5. **Zero regression, zero unintended side effects** — no
graha's classification changed, and Abhinandan's real chart configuration doesn't happen to contain
a D1-strong/D9-weak-with-D9-redemption case, so the new D9 path exists correctly but wasn't
exercised on this chart (harmless — it wasn't asked to be, only proven not to break anything).

**Step 1 of the re-attempt sequence: CONFIRMED CLEAN. Awaiting native go-ahead for step 2 — the
native chart re-attempt (R6A.6, take 2).**
