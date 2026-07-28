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

---

## 5. Append-only annotation — PARIŚODHANA Phase C3 regime reconciliation + real grader certification (2026-07-28)

**This section is an append-only annotation. §1–§4 above are unmodified — FROZEN, per rail — and
this annotation records evidence, not a change to the harness, its prompts, or its grading list.**

### 5.1 — Why this annotation exists

`PARISHODHANA_BRIEF_v1_0.md` §3 item 3 named an unresolved ambiguity: two historical numbers for
the wealth flagship — **2/13** (`STREAM_GAMMA_CLOSE_v1_0.md`, `ALPHA_FLAGSHIP_ACCEPTANCE_GRADING_
v1_0.md` §"Wealth × 1c826d5a") and **≥12/13** (`PURNA_VIRAMA_BRIEF_v1_0.md`'s cited pass bar) — were
being compared as if they graded the same thing. They do not. This annotation (a) states which
consumer regime each number describes, per §1's own protocol, and (b) records the result of
**actually executing** `evals/k2/consumption_grader.ts` and `evals/r5-w4-full-battery/llm_grader.ts`
against live production (chart `482012f1-710e-4a25-994a-93821f5871aa`, both flagship domains,
2026-07-28, all 12 PARIŚODHANA PRs merged and deployed), rather than the "good-faith manual
grading" `SHODHANA_REPORT_v1_0.md` §7 explicitly flagged as a non-certified substitute.

### 5.2 — The two regimes, named

- **Naive-routing regime** (this harness's own §1 protocol): a consumer with no charter/tool-catalog
  knowledge, one user turn, calling whatever it judges useful. Historically this regime reached
  only `assess_wealth`'s pre-B2 *headline* content and never discovered `dossier` — hence **2/13**.
  `T1-1` in `PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md` names the root cause: `dossier` was
  absent from the served `tool_search` index, so even a tool-searching agent could not find it.
- **Dossier-paging regime**: a consumer that knows to call `dossier(domain, chart_id)` explicitly
  and page through its Ω5 gather-then-compose engine to 100% accounting before composing. This is
  a **different consumer**, not a better-performing run of the same one — it requires knowledge the
  naive protocol's system prompt (§1) deliberately withholds. This is the regime `PURNA_VIRAMA_
  BRIEF_v1_0.md`'s **≥12/13** figure describes.

`"11/13 against the 12/13 bar"` (as reported in `SAMAPANA_REPORT_v1_0.md`) is therefore a
comparison across two regimes unless the consumer's routing path is stated alongside the score.
Going forward: **always name the regime** — "naive-routing: N/13" or "dossier-paging: N/13" — never
a bare score.

### 5.3 — Live finding this session: the regime gap has substantially closed in production

Two real, live, unmodified-production tool calls this session (`assess_wealth` and `assess_career`,
chart `482012f1`, no other args) — the SAME single call a naive-routing consumer reaches first
(confirmed by a live `tool_search(query="how is my wealth")` / `tool_search(query="how is my
career")` call this session: `assess_wealth`/`assess_career` rank #1 by score, `dossier` ranks #2)
— returned, inline in ONE call, a server-computed `completeness_directive` and `reading` array
scoring against this harness's own frozen §3 concept-family lists:

- **Wealth: 12/13 families served** (`contradictions_with_adjudication` honestly
  `empty_for_this_chart` — a correct negative, not a gap) — `reading[].status` verified directly
  from the live response.
- **Career: 11/12 families served** (`divisional_D9` returned `domain_block_not_served`) — same
  direct verification.

This means the **naive-routing regime, as actually deployed today, now reaches parity with the
historical dossier-paging ceiling for the frozen concept-family grade** — `assess_wealth`/
`assess_career` now inline `dossier`'s completeness accounting and per-family substance directly,
which is the "inline coverage bridge" `PARISHODHANA_BRIEF_v1_0.md` §2 B2.1 named as unowned. The
naive consumer no longer needs to discover or page `dossier` separately to reach the ≥12/13 ceiling
for this specific grade. **Caveat:** this was verified by this agent acting as the consumer (a
Claude Code session with full campaign context), not by re-running a genuinely blind fresh
sub-agent under §1's exact isolation — the tool-call results themselves are real, live, and
unmodified, but a from-scratch blind harness re-run (per §1's isolation guarantee) is the more
rigorous confirmation a future session should still perform before this is treated as a formally
re-sealed number.

### 5.4 — Real execution of `evals/k2/consumption_grader.ts` (this session, live)

Invocation (per `evals/k2/README.md`'s documented convention, no flags guessed):
`npx tsx evals/k2/consumption_grader.ts <transcript.json> wealth 482012f1-710e-4a25-994a-93821f5871aa`.
Two real transcripts were assembled from genuine tool-call results captured this session (not
fabricated): (a) naive — one `assess_wealth` call; (b) broad — `assess_wealth` plus real
`ganita_dashas_get`/`ganita_positions_get`/`bodha_signals_get` calls. **Both scored
`consumption_ratio: 0 / 12450`.**

This is a real, non-fabricated result, and it is NOT a claim that current production regressed —
it is a **diagnosed grader-scope finding, reported per rail (not fixed, since fixing would be a
grader change)**: this K2 broader Ω3-scale metric (§`consumption_grader.ts` header: "the BROADER
Ω3-scale accounting", distinct from this harness's own §2 mechanism) only credits a concept when
the SPECIFIC underlying primitive tool it cites in `COMPLETENESS_ACCOUNTING_*.json` (e.g.
`ganita_chart_facts_get`, `ganita_positions_get`, `bodha_signals_get` — 26 distinct primitives for
wealth) was itself called in the transcript AND the exact cited `fact_id`/`signal_id` string
appears verbatim in that tool's raw result. An orchestrating tool (`assess_wealth`, `dossier`)
aggregates hundreds of these primitive calls server-side; that aggregation is invisible to a
client-side transcript capture, so no realistic consumer transcript — naive OR expert — can score
above ~0% on this metric today without the transcript itself logging the orchestrator's internal
primitive calls. A secondary, separately-diagnosed observation: at least one concept family's
recorded evidence `fact_id`s (`ganita_positions_get`/`ganita_dashas_get` rows) are UUID-formatted in
`COMPLETENESS_ACCOUNTING_wealth_482012f1_v1_0.json`, while the live tool's own `fact_id` field for
the same subjects returns a 16-hex-character id with no dashes — a possible accounting-file/live-
schema drift, flagged for native review, not corrected here (the accounting file is data the grader
reads, not the grader itself, but no rail authorizes this campaign to alter it either).

### 5.5 — Real execution of `evals/r5-w4-full-battery/llm_grader.ts` (this session, live)

Its exported `llmRubric()` was called for real (not mocked) against a genuine `assess_wealth` raw
response, with `GOOGLE_GENERATIVE_AI_API_KEY` and `DEEPSEEK_API_KEY` read from `process.env` exactly
as the module does internally. Both are **absent from this sandboxed execution environment**. The
real, unmodified function returned:

```json
{"applicable": true, "floor": 11, "structuralProxyScore": null, "status": "NOT_LLM_GRADED",
 "note": "Both graders failed for this item. Gemini: GOOGLE_GENERATIVE_AI_API_KEY not set. DeepSeek: DEEPSEEK_API_KEY not set.",
 "grader": "none", "grading_latency_ms": 0}
```

This is the honest result, not a fabricated score — it confirms, by actually running the code
rather than assuming it, `battery_runner.ts`'s own header comment: *"this harness has NO access to
a live Gemini/DeepSeek grader in this sandboxed environment."* Certifying a real numeric rubric
score requires running this from an environment with one of those two keys provisioned; that is a
credentials/infrastructure gap, not a code defect, and is reported here rather than papered over
with a plausible-looking number.

### 5.6 — Standing recommendation

1. Every future report citing a sealed-harness score states the regime (`naive-routing` vs
   `dossier-paging`) alongside the fraction — a bare "N/13" is no longer a well-posed statement as
   of this annotation.
2. §5.3's finding should be re-verified by a genuinely blind fresh-subagent run (true §1 isolation)
   before being treated as a formal re-seal of the flagship number — this annotation's verification
   was real-production but not blind-consumer.
3. `evals/k2/consumption_grader.ts`'s orchestrator-tool blind spot (§5.4) and the `fact_id` format
   drift it surfaced are native-review items, not fixed here per the untouchable-harness rail.
4. `evals/r5-w4-full-battery/llm_grader.ts` needs a `GOOGLE_GENERATIVE_AI_API_KEY` or
   `DEEPSEEK_API_KEY` provisioned in whatever environment is meant to certify R5 W4 rubric scores —
   it cannot produce a real number without one, by design (it refuses to fabricate one).
