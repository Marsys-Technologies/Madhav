---
artifact: ALPHA_FLAGSHIP_ACCEPTANCE_GRADING
version: 1.0
status: FINAL (Phase 4, Elevation Campaign v2.1)
authored_by: Stream α (SATYA) Conductor, acting as Verifier per charter §2 Ω-Verification
grading_method: mechanical, per SEALED_EVALUATOR_HARNESS_v1_0.md — the Verifier read the score,
  never played the consumer. All four consumer runs were fresh, uninstructed sub-agents given only
  the frozen sealed system prompt (no charter text, no EL vocabulary, no mention of dossier/Lane Ω).
pass_threshold: "score >= 0.90 per (domain, chart) pair, per-concept hit/miss, no partial credit"
---

# α Flagship Acceptance Grading — Phase 4

## Result summary

| Domain | Chart | Hits | Required | Score | Pass (>=0.90)? |
|---|---|---|---|---|---|
| wealth | 482012f1 | 3 | 13 | 23% | **NO** |
| wealth | 1c826d5a | 2 | 13 | 15% | **NO** |
| career | 482012f1 | 4 | 12 | 33% | **NO** |
| career | 1c826d5a | 3 | 12 | 25% | **NO** |

**Verdict: §2 Ω-Verification flagship acceptance is NOT MET, on all four (domain, chart) pairs.**
This is consistent with — and independently corroborates — Stream γ's own `flagship_self_verified:
false` self-assessment (γ measured 2/13 ≈ 15% on wealth×482012f1 in its own fresh test; this
independent re-run scored 3/13 ≈ 23% on the same pair — reasonable run-to-run variance for a
non-deterministic naive-agent tool-choice process, not a contradiction).

## Methodology note

Each of the 4 consumer runs was dispatched as a genuinely fresh Agent-tool sub-agent (no memory of
this conductor's session) with EXACTLY the frozen system prompt from `SEALED_EVALUATOR_HARNESS_v1_0.md`
§1, substituting only the chart_id and the one user question ("How is my wealth?" / "How is my
career?"). One adaptation from the harness's literal architecture, stated for transparency: the
harness envisions an out-of-band transcript-capture mechanism; this conductor's tooling does not
provide one, so each consumer was additionally asked, as a trailing note *after* the sealed prompt
and question, to list its tool calls/arguments/result-summaries and restate its final answer — a
reporting-format instruction only, not a hint about what is being measured or how to answer. Grading
below is performed against the reported transcript, per-concept, with the same "substance must
appear in the final answer, not just be technically retrievable" rule the harness specifies.

## Per-run grading detail

### Wealth × 482012f1 — 3/13
- HIT `divisional_D2` — tool log explicitly consulted D2 (Horā) dignity table (varga_analysis step).
- HIT `divisional_D11` — same step, D11 (Rudrāṃśa) dignity table explicitly consulted.
- HIT `timing_windows` — extensive: Mercury MD → Saturn AD → Moon PD chain, activation window with
  computed peak, full upcoming sub-period table.
- MISS `per_varga_ashtakavarga` — not called this run.
- MISS `indu_lagna` — not mentioned.
- MISS `argala_house_2` / `argala_house_11` — argala never discussed.
- MISS `full_dispositor_closure` — individual dispositor placements described (Jupiter own-sign,
  Venus-Jupiter conjunction, Saturn exalted) but no traced closure to a final node.
- MISS `all_chart_mechanisms_and_chains` — 13 yoga *firings* covered richly (`ganita_yoga_firings_get`),
  but this is the L1 yoga catalog, not the L2 `bodha_mechanisms_get` structures (dispositor
  chains/cycles/house-lordship cycles/mutual-aspect triangles etc.) Ω6 requires as first-class;
  that tool was never called.
- MISS `special_lagnas` — not mentioned.
- MISS `cross_ayanamsha_agreement` — not mentioned.
- MISS `remedies` — not mentioned.
- MISS `contradictions_with_adjudication` — the tool result showed "0 of 3 chart-wide contradictions
  tagged to wealth," but this was never surfaced in the composed final answer — graded as a miss per
  the harness's own rule that a retrieved-but-unreflected fact does not count as a hit.

### Wealth × 1c826d5a — 2/13
- HIT `timing_windows` — Saturn MD → Rahu AD → Moon PD chain, activation window, peak date.
- HIT `contradictions_with_adjudication` — explicitly reflected: "No wealth-specific contradictions
  were found... this domain reads as internally consistent."
- MISS on all other 11 concepts (ashtakavarga, D2, D11, indu lagna, both argala items, dispositor
  closure, chart mechanisms/chains, special lagnas, cross-ayanamsha, remedies) — none called or
  reflected. D2/D11 were referenced only as inputs cited by `verdict.clauses` in the raw tool log,
  never surfaced with their actual dignity/placement substance in the composed prose — graded miss,
  same standard applied consistently with the 482012f1 wealth run's stricter items.

### Career × 482012f1 — 4/12
- HIT `per_varga_ashtakavarga` — Jupiter pinda_sarva=55, Mars=39 explicitly stated.
- HIT `divisional_D10` — "Dasamsa (D10) confirmation: Consulted directly... Moon exalted in D10
  10th house, Jupiter in own sign."
- HIT `timing_windows` — Mercury MD activation window, computed start/end dates.
- HIT `contradictions_with_adjudication` — "one domain-tagged contradiction... automated resolution
  hint came back empty, so this needs acharya-level adjudication" — explicitly reflected.
- MISS `divisional_D9`, `karakamsha_or_swamsha`, `argala_house_10`, `full_dispositor_closure`,
  `all_chart_mechanisms_and_chains` (yoga firings again, not bodha_mechanisms), `special_lagnas`,
  `cross_ayanamsha_agreement`, `remedies` — none called or reflected.

### Career × 1c826d5a — 3/12
- HIT `karakamsha_or_swamsha` — "Jaimini Karakāmśa-Sun signature... confirmed."
- HIT `timing_windows` — Saturn MD, 3 window families with peaks, an upcoming Oct-2026 convergence.
- HIT `contradictions_with_adjudication` — "one chart-wide contradiction is tagged specifically to
  career — a promise vs. denial tension" — explicitly reflected, though no adjudication resolution
  stated (graded as hit on the contradiction-disclosure half per the same standard applied above).
- MISS `per_varga_ashtakavarga`, `divisional_D10` (mentioned as "available" not actually served),
  `divisional_D9`, `argala_house_10`, `full_dispositor_closure`, `all_chart_mechanisms_and_chains`,
  `special_lagnas`, `cross_ayanamsha_agreement`, `remedies`.

## What this confirms

1. **`contradictions_with_adjudication` and `timing_windows` are the two most reliably-served
   concepts across all four runs** — both are already load-bearing, well-integrated parts of
   `assess_wealth`/`assess_career`/`judgment_query`'s existing default response shape.
2. **Never served in ANY of the 4 runs:** `argala_house_2`, `argala_house_11`, `argala_house_10`,
   `indu_lagna`, `special_lagnas`, `cross_ayanamsha_agreement`, `remedies`, `all_chart_mechanisms_and_chains`
   (the true L2 bodha_mechanisms structures, as distinct from L1 yoga firings), `full_dispositor_closure`.
   This is precisely the "33-item wealth floor with verified omissions" charter §0.2.A already
   diagnosed pre-campaign — argala, dispositor chains, special lagnas/sahams, and cross-ayanamsha were
   named there explicitly as absent from the compiled floor, and this Phase-4 measurement confirms
   they remain absent from what a naive consumer actually receives, even after this campaign's fixes.
3. **The urgent merge #4 fix (wiring assess_wealth/career through dossier's completeness) demonstrably
   changed consumer behavior** — visible directly in three of the four transcripts, which explicitly
   surfaced the `domain_completeness`/`completeness_directive` signal (one transcript even quoted the
   exact "13,825-concept career slice" figure back to the user). **But in none of the four runs did the
   naive consumer actually follow the directive and call `dossier` itself** — it treated the directive
   as informational rather than as an instruction to act on, and continued composing its answer from
   `assess_wealth`/`assess_career`/`judgment_query`/`kala_windows_get`'s own (rich, but partial) content.
   This is the precise, honest limit of what a response-level nudge can do without either (a) making
   `dossier` itself irresistibly the first tool a naive agent reaches for, or (b) having the
   default entrypoints internally hydrate the full slice rather than pointing at it.

## Disposition (four-state, per charter §9.6)

**`section2_omega_verification_flagship_acceptance`: PARKED-HONEST.**
Not `VERIFIED-CLOSED` (the numeric bar is not met, on any of 4 runs). Not `NOT-REPRODUCED` (the gap is
real and reproduces every time — 4/4 runs, 0/4 pass). Not `PREPARED-FOR-NATIVE` in isolation (the
underlying mechanism is built and independently verified layer-by-layer — this is a live, working,
well-diagnosed residual, not a native-only decision point, though the coverage gap itself is also
named in the morning's PREPARED-FOR-NATIVE dark-corpus packet).

**Root cause, fully diagnosed (not vague):** the last-mile gap is not in any one layer's correctness —
every layer this campaign built (dossier's paging/accounting, the planner floor wiring, the
depth-routing fix, this stream's completeness-signal wiring into assess_wealth/career) is independently
confirmed working, live, in isolation. The gap is in `assess_wealth`/`assess_career`'s own *content*:
they do not themselves serve argala, indu lagna, special lagnas, cross-ayanamsha agreement, remedies,
or the L2 mechanism/chain structures — they serve a rich but genuinely partial slice, now WITH an
honest completeness receipt and a directive pointing at the fuller `dossier` corpus, which a naive
consumer reads but does not reliably act on.

**Recommended next action (for the next campaign or a native-attended session, not built here — time-
boxed out per this run's charter §11.5 wall-clock cap):** either (a) have `assess_wealth`/`assess_career`
internally hydrate (not merely point at) the missing concept classes directly in their own response —
the heavier version of merge #4's fix that was explicitly scoped out as too risky this late in the run,
or (b) make `dossier` itself the tool `tool_search`/the MCP catalog surfaces FIRST for a domain question,
ahead of `assess_wealth`, so the naive agent's own tool-choice — not a post-hoc directive inside another
tool's response — is what changes. Both were identified and explicitly scoped out of this run's urgent
fix for time/risk reasons, not overlooked.
