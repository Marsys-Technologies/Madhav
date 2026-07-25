---
artifact: SEALED_EVALUATOR_HARNESS (Elevation Campaign v2.1, §2 Ω-Verification)
version: 1.0
status: FROZEN — committed read-only before any Ω builder is spawned (charter M2.4)
authored_by: RUNWAY session (non-participant)
flagship_domains: [wealth, career]
note_on_domain_choice: >
  Charter §2 Ω-V item 4 and §7.1 leave the second flagship domain as "career or marriage" —
  an explicit choice, not fixed by the charter. The RUNWAY session selects CAREER as the second
  flagship domain (structurally analogous to wealth: a single anchor house/lord chain — 10th vs
  2nd/11th — with comparable dispositor-closure and varga depth), so that both graded domains
  exercise Lane Ω symmetrically. This is a RUNWAY judgment call, logged here for the streams and
  the morning report; γ may not silently substitute marriage without filing an AMENDMENT row in
  CONTRACT_STATUS.md (M2.10).
---

# Sealed evaluator harness

## 1. The consumer (fixed, sealed)

A FRESH sub-agent, given the project's MCP tools and nothing else. Its system prompt is exactly:

```
You are an assistant with access to a set of astrology chart tools. A user will ask you one
question about their chart. Use whatever tools you judge useful, as many times as you judge
useful, and then answer the question directly and completely. The user's chart_id is
{{CHART_ID}}.
```

No charter text, no EL vocabulary, no concept names, no mention of "dossier" or "Lane Ω" — the
consumer must never be told what is being measured. It receives exactly ONE user turn per run:

- **Wealth, naive:** "How is my wealth?"
- **Career, naive:** "How is my career?"

The full transcript (every tool call, every tool result, the final answer) is captured verbatim to
`ledgers/harness_runs/<domain>_<chart_id>_<timestamp>.transcript.json`.

## 2. The grader (mechanical, not judgemental)

The grader is a deterministic script, never an LLM asked to judge quality. For a given
`(domain, chart_id)` transcript:

1. Load the frozen `required_concepts` list for that `(domain, chart_id)` pair (§3 below).
2. For each `concept_id`, scan the transcript's tool-call arguments and tool results (not the final
   prose answer alone — the answer may compress) for evidence the concept's *substance* was
   retrieved and used. A concept_id is a HIT only if a matching fact/signal/mechanism actually
   appears in a served tool result AND is reflected (in substance, not necessarily verbatim) in the
   final answer. A tool call that fires but returns nothing relevant, or a final answer that
   mentions a concept's name without its computed value, is a MISS.
3. Score = hits / len(required_concepts). **Pass threshold: score ≥ 0.90** (charter's "at 100%
   accounting" target for the underlying dossier is distinct from — and stricter than — this
   evaluator's pass bar; 0.90 is the harness's own acceptance floor, not the Ω3 accounting
   invariant, which is graded separately by the receipt gate).
4. Per-concept hit/miss is recorded in the grading output — partial credit does not exist at the
   per-concept level.

The Verifier reads the grader's score. It never plays the consumer, and it never re-grades a
transcript by eye — a Verifier that answers the question itself, or overrides a mechanical miss on
its own judgement, has invalidated the run.

## 3. Frozen required-concept lists

### Wealth (frozen from charter §2 Ω-V item 1, verbatim)
```
per_varga_ashtakavarga, divisional_D2, divisional_D11, indu_lagna, argala_house_2, argala_house_11,
full_dispositor_closure, all_chart_mechanisms_and_chains, special_lagnas, cross_ayanamsha_agreement,
timing_windows, remedies, contradictions_with_adjudication
```
`sahams` is explicitly EXCLUDED pre-β per the charter ("sahams (post-β)") — the harness does not
penalize its absence until a stream's `<C-sahams>.live` record exists (M2.5); the grader script
must read `~/elev-v2-shared/implementations/` before scoring and drop `sahams` from
`required_concepts` if no live record exists yet for the run being graded.

### Career (RUNWAY-authored, analogous structure — 10th-house anchor in place of 2nd/11th)
```
per_varga_ashtakavarga, divisional_D10, divisional_D9, karakamsha_or_swamsha,
argala_house_10, full_dispositor_closure, all_chart_mechanisms_and_chains, special_lagnas,
cross_ayanamsha_agreement, timing_windows, remedies, contradictions_with_adjudication
```

Both lists apply identically to both canonical charts (482012f1-710e-4a25-994a-93821f5871aa and
1c826d5a-41cb-4450-b4dc-59d440e5f75a) — per charter Ω-V item 4, the mechanism must prove general,
not chart-tuned.

## 4. Reuse for Ω4 (routing suite) and Ω7 (dark-corpus replay)

This harness's consumer configuration (fresh sub-agent, sealed system prompt, transcript capture) is
reused verbatim to execute `ROUTING_SUITE_60_v1_0.json` and `DARK_CORPUS_REPLAY_SET_v1_0.json` — the
only variable across all three uses is the user turn and the grading rule applied to the transcript.
