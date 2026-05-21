---
artifact: PANEL_SYNTHESIS_ADDENDUM_v0_1.md
version: 0.1
status: SUPERSEDED (2026-04-27 — content absorbed into MARSYS_JIS_ARCHITECTURE_v1_0.md §10 Synthesis Strategies; retained in place for historical audit and provenance)
revision: v0.1 (2026-04-27 initial) → v0.2 (2026-04-27 same-session amendment incorporating six architectural fixes from external critique pass — see §17 changelog)
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
authoring_session: Cowork conversation — "Multi-LLM panel synthesis brainstorm with native"
purpose: Architectural design for an opt-in multi-LLM panel synthesis variant of the Consume layer's Stage-7 SYNTHESIZE step. Panel mode fans out a query to multiple frontier LLMs, captures their independent responses, and synthesizes them via an adjudicator model.
governance_status: NOT YET ADOPTED. Awaits native review. Depends on parent design `CONSUME_DESIGN_v0_1.md` adoption (via ND.2 or PHASE_B_PLAN amendment v1.0.4). Path to adoption for this addendum: a follow-on ND.3 directive bound to B.7 (Synthesis Router phase), or a subsequent PHASE_B_PLAN amendment (v1.0.5) folding panel mode into B.7 deliverables.
depends_on:
  - CONSUME_DESIGN_v0_1.md (parent design — must be adopted first; this addendum has no architectural ground without it)
relates_to:
  - PHASE_B_PLAN_v1_0.md §B.7 (Synthesis Router — panel synthesis is a router-level variant)
  - PROJECT_ARCHITECTURE_v2_2.md §B Architectural Principles (B.1, B.3, B.10, B.11 inform the adjudicator's evaluation rubric)
  - GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K (multi-agent disagreement classes — extended in §6 below with new DIS.class.extension)
  - MACRO_PLAN_v2_0.md §Cross-cutting workstreams (Prospective Prediction Logging — panel mode multiplies log entries per predictive query)
  - 06_LEARNING_LAYER (per-model calibration data accumulates from panel mode usage; M3+ consumer)
  - MACRO_PLAN_v2_0.md §Ethical Framework (audience-tier filtering applies to panel responses identically to single-model responses)
seeds:
  - Native observation: "models sometimes miss a completely different aspect, which I think will be caught on by multiple models running."
  - Native intent: "use multiple LLMs to come back with their response and Claude Code can be the final adjudicator."
  - Architectural fit: panel synthesis is a Stage-7 variant within the parent design's eight-stage pipeline; it inherits Stages 1–6 and 8 unchanged.
  - v0.2 critique pass (2026-04-27): external agent identified six architectural concerns; v0.2 incorporates fixes for #1 super-bundle handoff, #2 consolidation orthogonality+grounding, #3 concurrent retry + opt-in 2-of-3 fallback, #4 history-mode toggle, #5 tool-call caching, #6 adjudicator/classifier split. See §17 changelog for details.
---

# PANEL SYNTHESIS ADDENDUM v0.1 — Multi-LLM Adjudicated Synthesis

## §1 — Purpose

Single-model synthesis at Stage 7 of the Consume pipeline (per `CONSUME_DESIGN_v0_1.md §4`) commits the answer to one model's interpretive frame. Different frontier LLMs trained on different corpora with different RLHF traditions reliably surface different aspects of the same query — sometimes one model catches a cross-domain signal the others miss, sometimes one frames the question in a way that exposes a weak interpretation in the others. Single-model mode discards this diversity by construction.

Panel synthesis is an opt-in variant of Stage 7 that fans the query out to multiple independent frontier LLMs in parallel, then synthesizes their responses via an adjudicator model. The native's intent is twofold: (a) widen the interpretive pool so that the final answer is informed by multiple framings rather than one, and (b) generate disagreement data that — over time — calibrates which model is reliable on which question type, feeding the M5 Learning Layer.

Panel synthesis is **not** a quality-or-fallback mechanism. It is a research-grade ensemble whose value compounds with use, because the disagreement-and-outcome record it accumulates is itself a discovery surface for the project's broader mission.

## §2 — Core Principle

Panel synthesis is a Stage-7 **synthesis strategy variant**, not a parallel architecture.

The eight-stage pipeline of the parent design (`CONSUME_DESIGN_v0_1.md §4`) is unchanged. Stages 1 (RECEIVE) through 6 (VALIDATE) execute identically regardless of synthesis mode. Stage 8 (DISCIPLINE) executes identically. Only Stage 7 (SYNTHESIZE) branches: in single-model mode, one model composes the answer over the validated bundle; in panel mode, three panel members compose independent answers over the same validated bundle, an adjudicator synthesizes from the three, and the adjudicator's synthesis enters Stage 8 as the unitary "synthesis output" the discipline gates evaluate.

Three corollaries follow.

The first is **infrastructure inheritance**: panel mode does not invent its own logging, validation, retrieval, or audience-tier filtering. It plugs into the parent design's existing facilities. Adding panel mode without the parent design adopted is incoherent — the addendum has no foundations to build on.

The second is **synthesis-output equivalence**: from the perspective of Stages 1–6 and Stage 8, the output of panel synthesis is indistinguishable from single-model synthesis. The discipline gates do not need to know whether panel mode was used. They evaluate the synthesized output and write the audit trail. The richer panel-specific data (per-member responses, retrieval transcripts, divergence classifications) is captured in extended audit-trail metadata (§7 below), but the gates themselves are mode-agnostic.

The third is **diversity-by-construction**: panel members must produce genuinely independent responses, or the panel collapses to expensive redundancy. Independence requires (a) diverse model lineages (different labs, different training distributions, different RLHF traditions), (b) blinded adjudication (the adjudicator does not know which response came from which model), and (c) retrieval transparency (each panel member's tool-call extensions are captured so the diversity of *attention* — not just interpretation — is preserved as audit data).

## §3 — Panel Composition

The panel is drawn from a configurable slate of four frontier-lab model families: **Claude (Anthropic), GPT (OpenAI), Gemini (Google), DeepSeek**. Each lab has multiple model versions in the registry; the manifest declares which version is the current "panel-best" per lab. The slate is configurable so version choices can evolve as new models ship.

Today's registry (per `platform/src/lib/models/`) contains Claude (Haiku 4.5, Sonnet 4.6, Opus 4.7), Gemini (2.5 Flash, 2.5 Pro, 3 Pro preview), and DeepSeek (V3, R1). **GPT (OpenAI) is not yet in the registry**; adding it (`@ai-sdk/openai`, registry entry, resolver case, `OPENAI_API_KEY`) is a strict prerequisite for panel mode and constitutes Migration step v0.5 in §14.

**Family-level adjudicator exclusion.** When the user selects a model as the adjudicator, that model's *entire family* is excluded from the panel. Selecting Claude Sonnet 4.6 as adjudicator excludes all Claude variants from the panel; the panel becomes {GPT-best, Gemini-best, DeepSeek-best}. Selecting Gemini 3 Pro excludes all Gemini variants; the panel becomes {Claude-best, GPT-best, DeepSeek-best}. This rule is non-negotiable: the LLM-as-judge literature (Zheng et al. 2023 and successors) measures large, robust self-preference bias when a judge sees its own family's stylistic fingerprint among the candidates, and family-level exclusion is the only reliable defense.

Panel size is therefore always **3 panel members + 1 adjudicator = 4 LLM calls per panel query** (regardless of which model the user selected as adjudicator). Cost is predictable.

**Tool-capability alignment.** The panel-best version per lab is selected with tool-use capability as a hard filter. DeepSeek R1 lacks tool-use and is therefore excluded from the panel-best slot for DeepSeek; the default DeepSeek panel member is V3. R1 remains available as an adjudicator selection (where tool-use is not required) and as a single-model selection. This rule prevents tool-use asymmetry within the panel — every panel member can extend the baseline bundle via tool calls.

**Configurability.** The capability manifest's `PANEL_SYNTHESIS.panel_slate` field declares the current best-per-lab assignments. The native can override per-lab versions via manifest edit without code change. The four labs themselves are fixed in v0.1 of this addendum; expanding the panel beyond four labs (e.g., adding Mistral, Grok) is a future-version decision tracked in §15.

## §4 — Activation

**Per-query checkbox in the Composer.** The Consume tab's `Composer` component gains a single checkbox labeled (working name) **"Run as super query"**. When checked, the request body sent to `POST /api/chat/consume` carries `panel_mode: true`. The checkbox auto-resets to unchecked after each send to enforce cost discipline; the user re-enables per query.

**Tier availability: universal.** The checkbox is rendered for all audience tiers (`super_admin`, `acharya_reviewer`, `client` post-M6, `public_redacted` post-M10). Panel mode is not gated to administrators. The disclosure-tier filter at Stage 8 (parent §4 step 8 gate 4) governs the *content* of what reaches each audience — in panel mode as in single-model mode — but the *availability* of panel mode itself is universal. See §11 for the audit-view consequences of this.

**No persistence across queries.** The panel toggle is request-scoped. It is not stored in `useChatPreferences` (the localStorage layer that persists model and style selection). This is intentional — panel mode is an explicit per-query choice, not a default mode. Future versions may revisit if the native wants a "panel by default" preference, but v0.1 enforces explicit re-selection.

**Style suffix propagation.** The selected style (`acharya` / `brief` / `client`, plus any future styles per §15) is propagated identically to all three panel members and the adjudicator's synthesis prompt. The panel does not mix styles; the entire panel turn is conducted in one register.

## §5 — Stage-7 Variant: Panel Synthesis Algorithm

This section specifies the algorithm that replaces the Stage-7 SYNTHESIZE step when `panel_mode: true`. Stages 1–6 of the parent pipeline have produced the validated retrieval bundle; Stage 8 will run the discipline gates on the synthesis output. Panel synthesis sits between them.

**Step 5.1 — Panel Resolution.** Read the user's selected adjudicator model from the request. Look up its provider family (`anthropic` | `openai` | `google` | `deepseek`). Read the manifest's `PANEL_SYNTHESIS.panel_slate` and exclude the adjudicator's family. The panel composition is the three remaining lab-best models. Record the resolved panel composition in the audit trail.

**Step 5.2 — Bundle Handoff.** Each of the three panel members receives the identical Stage-5 retrieval bundle: the validated, layer-balanced, L2.5-inclusive bundle assembled by the layered retriever per parent §4 step 5 and §14 obligation #1. The bundle is the *uniform baseline* — every panel member starts from the same data so that interpretive divergence is measurable against a common substrate.

**Step 5.3 — Parallel Panel Generation.** Fan out three asynchronous `streamText` calls to the panel members, in parallel. Each call carries:
- the same system prompt (with style suffix applied identically);
- the conversation history (per the conversation-history handling rule in §15 question 4);
- the validated retrieval bundle inlined as context;
- the user's current query;
- the same tool surface that single-model mode would offer (per §13 below — panel members may call tools to *extend* the baseline bundle with additional retrieval).

Critically: **panel members are not informed they are part of an ensemble**. The system prompt does not mention adjudication, panels, or other LLMs. Telling a model it is one of several reliably changes its behavior toward hedging or complementary-output positioning. The panel must be naive.

**Step 5.4 — Panel Response Collection.** Each panel member's complete response is collected, including:
- the response text;
- the full tool-call transcript (which tools were called with what parameters, and what each tool returned — capturing the panel member's *retrieval extensions* beyond the baseline bundle);
- token counts (input, output, cached);
- end-to-end latency;
- finish reason.

Panel responses where any individual call errors out trigger the failure path defined in §10. A successful panel turn requires all three responses received and validated.

**Step 5.5 — Panel-Member Validation.** Before adjudication, each panel response runs through the active P-validator stack (per parent §7 — P1, P2, P5 today; P3, P4, P6, P7, P8, P9 as they come online). A panel response that fails a validator is marked failed in the audit trail and the failure path triggers (§10). The rationale: an adjudicator should not synthesize from a contaminated input — for example, a panel response that smuggles L1 facts into L2+ claims (P1 violation) would propagate the violation into the synthesis.

**Step 5.6 — Anonymization & Adjudicator Synthesis (v0.2 super-bundle revision).** The three validated panel responses are anonymized — labeled A / B / C with model identity stripped — and shuffled into a randomized order. Before adjudication, the validated retrieval bundle is augmented into a **merged super-bundle**: the baseline bundle from Stage 5 plus the deduplicated content of every unique extension that any panel member retrieved during Stage-7 generation. The super-bundle ensures the adjudicator has access to source content for every claim any panel member made, enabling full B.10 (no-fabrication) validation across the synthesis. Without the super-bundle, claims grounded in extended-only content would be unverifiable — the adjudicator would be asked to validate ungroundable claims, which is the v0.1 critical flaw §17 Fix 1 corrects.

The adjudicator model is invoked with a synthesis prompt that includes:
- the user's original query;
- the **merged super-bundle** (baseline ∪ deduplicated extensions);
- the three anonymized, randomly-ordered panel responses;
- the per-panel-member retrieval transcripts (so the adjudicator can see *which* member retrieved *which* extension — feeding framing-divergence detection without re-fetching content);
- the explicit synthesis rubric (B.1 layer separation, B.3 derivation ledger, B.10 no-fabrication, B.11 whole-chart-read);
- the style suffix (so the synthesis is in the same register as the panel responses).

The adjudicator produces a single synthesized response that draws on whatever is correct, complete, or grounded in the panel responses, integrates its own perspective on the super-bundle, and produces synthesis reasoning. The adjudicator does **not** classify divergences in this step — classification is offloaded to a separate cheaper model in Step 5.6b to avoid attention-degradation on combined synthesis-plus-strict-JSON-extraction tasks (v0.2 §17 Fix 6).

**Step 5.6b — Divergence Classification (v0.2 addition).** A separate, smaller classifier model is invoked with:
- the three (still anonymized) panel responses;
- the adjudicator's synthesis output from Step 5.6;
- the merged super-bundle (so the classifier can ground divergence claims in source where needed);
- the disagreement-classification taxonomy from §6 with instruction to extract every detected divergence and label it with the appropriate `DIS.class.*` class.

The classifier model defaults to **the adjudicator's family's smallest/fastest model** — adjudicator Claude Sonnet 4.6 → classifier Claude Haiku 4.5; adjudicator Gemini 3 Pro → classifier Gemini 2.5 Flash; adjudicator GPT-5 → classifier GPT-5-mini-equivalent; adjudicator DeepSeek V3 → classifier DeepSeek V3 (no smaller variant available; same model called in classification-only mode). Same-family choice keeps any classification bias consistent with the synthesis bias, rather than introducing a third bias vector. The classifier model is configurable per the manifest (§12 below) — native can override the default per family.

The classifier produces a structured `divergences` list (per the §7 `panel_metadata` schema) which is appended to the audit-trail event at Stage 8.

Cost note: this adds one small-model LLM call per panel turn (typically <5% of total panel cost). The trade-off — sharper classification + unloaded synthesis cognition — is judged worth it.

**Step 5.7 — Synthesis-Output Handoff.** The adjudicator's synthesis from Step 5.6 is the unitary "synthesis output" that flows into Stage 8 (DISCIPLINE) of the parent pipeline. The classifier output from Step 5.6b is a parallel artifact appended to the audit-trail event but does not flow through the discipline gates. Stage 8 evaluates the synthesis identically to a single-model synthesis output — three-interpretation gate (P7), falsifier gate (P8), audit-trail write (P9), disclosure-tier filter. The Stage-8 audit-trail write is extended with the `panel_metadata` schema defined in §7, including the merged super-bundle hash and the divergence classifications from Step 5.6b.

## §6 — Disagreement Taxonomy Extensions

The parent project's `DISAGREEMENT_REGISTER_v1_0.md` (per `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K`) defines four disagreement classes for multi-agent collaboration:
- `DIS.class.fact` — disagreement on a factual claim;
- `DIS.class.interpretation` — same data, different reads;
- `DIS.class.computation` — disagreement on a derivation result;
- `DIS.class.scope` — disagreement on the scope of the question being answered;
- `DIS.class.mirror_desync` — Claude/Gemini cross-mirror divergence (governance-layer only, not relevant to panel synthesis).

This addendum proposes a fifth class for panel-mode use:

**`DIS.class.extension`** — divergence in *which additional retrievals* the panel members chose to perform beyond the baseline bundle. Example: Panel member A extended with `get_remedial_codex`, panel member B extended with `graph_walk_l35`, panel member C did not extend at all. This is not interpretation divergence (they read the same baseline differently); it is *attention* divergence (they thought different additional data was relevant). Surfacing extension divergences is research-grade audit data, because it identifies which retrieval strategies correlate with which interpretive moves — and over time, with which outcome accuracies (M5 Learning Layer feedback).

The classifier model at Step 5.6b (separate from the adjudicator per v0.2 §17 Fix 6) is instructed to extract and classify each detected divergence using the five-class taxonomy. The audit-trail entry (§7) carries the per-divergence classification list along with the classifier model identifier and its token/latency footprint.

## §7 — Persistence: `panel_metadata` Schema

Stage 8 of the parent pipeline writes an audit-trail event per query. For panel-mode queries, the event is extended with a `panel_metadata` field carrying the panel-specific data. The proposed schema (subject to migration concerns when the canonical Learning Layer prediction-ledger schema lands per parent §9 question 4):

```json
{
  "panel_mode": true,
  "panel_composition": {
    "adjudicator_model": "claude-sonnet-4-6",
    "adjudicator_family": "anthropic",
    "panel_members": ["gpt-5", "gemini-3-pro-preview", "deepseek-v3"],
    "panel_slate_manifest_version": "0.5",
    "panel_resolver_rule_applied": "exclude_adjudicator_family",
    "degrade_mode_allowed": false,
    "degrade_mode_triggered": false,
    "history_mode": "synthesized"
  },
  "merged_super_bundle": {
    "baseline_bundle_hash": "sha256:abc...",
    "extensions_by_member": {
      "A": ["sha256:def..."],
      "B": [],
      "C": ["sha256:ghi...", "sha256:jkl..."]
    },
    "super_bundle_hash": "sha256:zzz...",
    "deduplicated_extension_count": 3
  },
  "panel_responses": [
    {
      "label": "A",
      "model_id": "gpt-5",
      "response_text": "...",
      "tool_calls": [
        {"tool": "get_layer_document", "params": {...}, "result_hash": "sha256:...", "served_from_cache": false},
        {"tool": "get_remedial_codex", "params": {...}, "result_hash": "sha256:...", "served_from_cache": false}
      ],
      "tokens": {"input": 12453, "output": 1842, "cached": 8200},
      "latency_ms": 8421,
      "finish_reason": "stop",
      "validator_votes": {"P1": "pass", "P2": "pass", "P5": "pass"},
      "extracted_predictions": [
        {"claim": "...", "horizon": "...", "falsifier": "...", "confidence": 0.72}
      ],
      "retry_attempts": 0
    },
    {"label": "B", "model_id": "gemini-3-pro-preview", "...": "...", "retry_attempts": 1},
    {"label": "C", "model_id": "deepseek-v3", "...": "...", "retry_attempts": 0}
  ],
  "anonymization": {
    "label_to_model": {"A": "gpt-5", "B": "gemini-3-pro-preview", "C": "deepseek-v3"},
    "presentation_order_to_adjudicator": ["B", "A", "C"]
  },
  "adjudicator_synthesis": {
    "synthesis_text": "(this is the user-visible response)",
    "synthesis_reasoning": "(adjudicator's rationale for synthesis decisions)",
    "interpretations_consolidated": {
      "from_panel_member_count": 9,
      "user_visible_count": 3,
      "consolidation_rule": "orthogonal_explanatory_power_grounded",
      "ungrounded_excluded": [
        {"interpretation_summary": "...", "member_origin": "B", "reason": "no L1 fact_id citation"}
      ]
    },
    "tokens": {"input": 18920, "output": 2103, "cached": 0},
    "latency_ms": 6210,
    "finish_reason": "stop"
  },
  "divergence_classification": {
    "classifier_model_id": "claude-haiku-4-5",
    "classifier_tokens": {"input": 21043, "output": 850, "cached": 0},
    "classifier_latency_ms": 1820,
    "divergences": [
      {
        "class": "DIS.class.interpretation",
        "summary": "Panel A and C identified the Saturn-Mars opposition as the primary stress signal; Panel B identified the 6th-house lord weakness as primary.",
        "members_involved": ["A", "C", "B"],
        "adjudicator_treatment": "Treated as complementary rather than conflicting; both stressors named in synthesis with relative weight."
      },
      {
        "class": "DIS.class.extension",
        "summary": "Panel A extended bundle with get_remedial_codex; B and C did not.",
        "members_involved": ["A", "B", "C"]
      }
    ]
  },
  "panel_total_cost_estimate_usd": 0.44,
  "panel_total_latency_ms": 14631
}
```

**Storage.** This metadata is stored alongside the message in the conversation persistence layer (Supabase `messages` table per `platform/src/app/api/chat/consume/route.ts` `replaceConversationMessages`). The schema migration adds a single `panel_metadata` JSONB column on the messages table, populated only when panel mode was used. Single-model messages have `panel_metadata: null`.

**Visibility.** The synthesized response (`adjudicator_synthesis.synthesis_text`) is the conversation-rendered content. The remaining metadata is hidden by default and surfaced via the audit-view UX (§11). The audit view's content respects the audience-tier disclosure filter — see §11 for the tier interaction.

## §8 — Discipline Gate Interactions

Stage 8 of the parent pipeline runs four gates: three-interpretation (P7), falsifier (P8), audit-trail write (P9), disclosure-tier filter. Panel mode interacts with each as follows.

**Three-interpretation gate (P7).** Each panel member's response is required to carry three interpretations for interpretive-class queries (per parent §4 step 8 gate 1 and parent §7 P7 — coming online at B.5 Task 0). The adjudicator's synthesis at Step 5.6 consolidates the panel's nine total interpretations (three per panel member) into a single three-interpretation structure that becomes the synthesis output. The audit trail retains all nine; the user sees three.

**Consolidation rule (revised in v0.2 to prevent the consensus trap).** The v0.1 rule preferred interpretations supported by multiple panel members and demoted unique-to-one-member interpretations to "edge-case." This inverted the value proposition of panel mode — the unique insight one model surfaces that others miss is precisely what the panel is run to catch. The v0.2 rule replaces it:

*Select three interpretations that maximize coverage of the explanatory possibility space, subject to the constraint that every selected interpretation must cite L1 fact_ids per B.3 derivation-ledger discipline.*

Ungrounded interpretations are excluded from the user-visible three but logged in the audit trail as `interpretation_candidate_ungrounded` with the originating panel member identified, for later review (potential insight or potential hallucination — to be resolved by outcome data over time per the M5 Learning Layer feedback loop). Where multiple panel members converge on the same interpretation, the convergence is preserved as audit metadata for calibration use but does not bias selection. The principle: orthogonality + grounding > consensus.

**Falsifier gate (P8).** Each panel member's response is required to name falsifiers for any time-indexed claims (per parent §7 P8). The adjudicator consolidates these into the synthesis output's falsifier field, preferring the most precise falsifier offered by any panel member; if panel members offered conflicting falsifiers, the adjudicator surfaces the conflict in `divergences` (`DIS.class.scope` typically applies) and selects the most conservative.

**Audit-trail gate (P9).** The audit-trail write at Stage 8 is extended with `panel_metadata` per §7. P9's "audit-trail completeness" check (per parent §7) verifies that for panel-mode queries the panel_metadata block is present and well-formed; a panel turn whose audit-trail write fails P9 fails Stage 8 in the same way a single-model turn would.

**Disclosure-tier filter.** The filter applies to the synthesis output identically to a single-model synthesis output. For panel-mode queries the filter additionally applies to the audit-view content per audience tier (§11): super_admin sees raw panel responses; client (post-M6) sees panel responses passed through the same redaction/calibration-banding rules that apply to single-model output. The principle: the audit view's existence is universal, but its content is tier-conditional, mirroring how the conversation panel works.

## §9 — Prediction Ledger Interactions

Per native decision (this brainstorm, 2026-04-27) and parent §14 obligation #3:

**Audit-trail logging is universal.** Every panel-mode query writes the full `panel_metadata` block to the audit trail at Stage 8 P9, regardless of query class. A "what are my Raj Yogas?" panel query (interpretive, non-predictive) writes the same audit-trail richness as a "will my Saturn return next year impact my career?" panel query (predictive). The audit trail is the universal record.

**Prediction ledger writes are class-conditional.** The prediction-ledger pre-stream write (per parent §14 obligation #3) is architecturally meaningful only for time-indexed claims that have a falsifiable outcome to verify against later. The trigger criterion follows option (c) from the prior brainstorm round: the *predictive claims extracted from the responses*, not the queries themselves, drive ledger writes.

For predictive-class queries in panel mode, this means **all four** synthesis sources (three panel members + adjudicator synthesis) emit their own predictive claims with their own confidences and falsifiers, and **all four are written to the prediction ledger as separate entries** before streaming begins. Each entry is logged with: (a) which model produced it, (b) its panel-member or adjudicator role, (c) its panel turn ID (linking back to the audit-trail event), (d) the claim, horizon, falsifier, confidence, and (e) the validated bundle hash that grounded it. This produces 4× the prediction-ledger entries per panel query versus single-model — by design — because per-model calibration data is the M5 Learning Layer's substrate, and panel mode is the highest-fidelity source for accumulating it.

For non-predictive panel queries (interpretive, factual, remedial), no prediction-ledger entries are written. The audit trail captures everything; the prediction ledger remains class-conditional. This keeps the prediction-ledger corpus clean of interpretive noise and preserves the integrity of calibration metrics computed from it.

The pre-stream-write discipline (sacrosanct per Learning Layer rule #4) means: for predictive panel queries, all four ledger writes complete before any streaming to the user. This adds latency (4 atomic writes) but preserves outcome-blind logging.

## §10 — Failure Handling (v0.2 revision: concurrent retry + opt-in 2-of-3 degrade)

Per native decisions: Exec_10 hard-halt principle preserved as default; v0.2 critique-pass resolutions add aggressive concurrent retry and an opt-in 2-of-3 degrade mode.

**Default behavior: hard-halt at 3-of-3 with aggressive concurrent retry.** If any of the three panel-member API calls errors (network, rate limit, content policy, timeout, or any other failure mode), the failed call is retried *concurrently* — the moment a failure is detected, a retry of that member fires immediately while the other panel members continue running. Up to **N=3 retries per panel member** within a bounded total time budget (configurable; default 60 seconds end-to-end).

The math is the reason: v0.1's "single sequential retry then hard-halt" produced brittle uptime (4 × 99% ≈ 96% panel success; one degraded provider at 90% drops the panel to 87%). With four total attempts per member, a 99% provider reaches ~99.9999% per-member success; a degraded 90% provider reaches ~99.99%. The 3-of-3 requirement is preserved without the brittleness of single-attempt failure modes.

If retries exhaust without a successful response from a panel member, the panel turn enters one of two terminal paths depending on the user's `degrade_mode_allowed` setting (see below).

**Opt-in 2-of-3 degrade mode (v0.2 addition).** Each user has a setting in their preferences — **"Allow 2-of-3 degrade if a panel member fails"** — defaulting to **off**. When off (default), exhausted retries trigger hard halt per the original Exec_10 principle. When on, exhausted retries proceed to synthesis from the surviving panel members (minimum 2-of-3); the audit trail is marked `degrade_mode_triggered: true`; the M5 Learning Layer's calibration consumer is instructed to exclude degraded panel turns from training data by default. Users opting into degrade mode accept that their panel queries may occasionally produce 2-of-3 syntheses with reduced statistical fidelity, in exchange for higher panel-mode uptime. The choice is per-user and persistent (stored in user settings, not per-query).

**Hard-halt user-facing error.** When hard halt triggers (default mode, retries exhausted), the user receives an explicit error message identifying which panel member failed and the failure mode (e.g., *"Panel mode failed: GPT-5 unavailable after 3 retries. Retry now, enable 2-of-3 degrade mode in settings, or unselect panel mode and run as single-model query."*). The error is rendered in the conversation as an assistant message with distinct error styling, not silently dropped. The composer state (text, attachments, panel checkbox) is preserved for retry.

**Audit-trail capture of failure (and degrade).** Every panel turn — successful 3-of-3, hard-halted, or degrade-completed 2-of-3 — writes an audit-trail event capturing: which panel members succeeded, which failed, retry counts per member (`retry_attempts` field in `panel_metadata.panel_responses[]`), failure modes, the validated baseline bundle hash that was used (or would have been used), and the `degrade_mode_triggered` flag. Failed and degraded panel turns are themselves data — they identify provider reliability issues over time and feed the M5 calibration consumer's exclusion logic.

**No silent degradation.** Under no circumstances does panel mode silently substitute a 2-of-3 synthesis for a 3-of-3 result without the user having explicitly opted in. The integrity of the calibration corpus depends on degrade events being explicitly flagged and excluded by default from M5 training data. Default behavior remains hard-halt.

## §11 — UX Design

**Composer.** A single checkbox is added to the composer, label working name **"Run as super query"** with a tooltip explaining the panel mechanism in one sentence. Position: adjacent to the model selector. Default state: unchecked. Auto-resets to unchecked after each send. No styling escalation (no special highlighting, badge, or warning) — panel mode is a normal feature, not an alarming one.

**Conversation panel.** The synthesized response is rendered identically to a single-model assistant message — same bubble style, same typography, same copy/regenerate affordances. The user-visible content is the adjudicator's synthesis (`adjudicator_synthesis.synthesis_text`); panel-specific data is not surfaced in the conversation panel.

**Audit view (universal, tier-conditional).** Every assistant message — single-model and panel — exposes an "Inspect" affordance (small icon button). Clicking opens an expandable panel showing the audit-trail data associated with that message. Content varies:

- **Single-model message audit view**: capability snapshot (which assets were consulted), Stage-5 retrieval bundle summary, validator votes, synthesis prompt version, tool-call transcript, token/latency/cost.
- **Panel-mode message audit view**: all of the above for the adjudicator, plus per-panel-member sub-panels showing each panel response with its own bundle summary, tool-call transcript, validator votes, extracted predictions, and the divergence list with `DIS.class.*` classifications. The anonymization-key (which model was A, B, C) is shown.

Audit view availability is universal across audience tiers. Audit view *content* is tier-conditional via the disclosure filter: super_admin and acharya_reviewer see raw content with no redaction; client (post-M6) sees panel responses run through the same redaction/calibration-banding rules that apply to the synthesized response shown in the conversation; public_redacted (post-M10) follows the same rule, with additional cohort-level aggregation if applicable.

**Latency UX.** Panel mode total latency is `max(panel_member_latencies) + adjudicator_latency`, typically 10–30 seconds. The composer shows a progress indicator with state transitions: "Running panel..." → "Adjudicator synthesizing..." → streaming. No per-panel-member progress disclosure (would leak panel composition before the audit view is opened).

**No conversation-history visual difference.** Panel-mode messages are not visually distinguished from single-model messages in the conversation list. The audit view is the only surface that exposes which mode was used. This keeps the conversation panel clean and prevents the user from over-attending to mode selection.

**User settings (v0.2 additions).** Two new toggles live in the user preferences panel (separate from per-query composer state, because they encode epistemic stances about how panel mode should behave rather than per-question choices):

- **"Allow 2-of-3 degrade if a panel member fails"** (default: off). When enabled, panel turns where one member ultimately fails after retries proceed with 2-of-3 synthesis rather than hard-halting. Audit-trail-marked via `degrade_mode_triggered: true`; M5 calibration consumer excludes degraded turns from training data by default. Trades statistical fidelity for uptime. See §10.
- **"Research mode (no history in panel turns)"** (default: off). When enabled, panel members for every panel query receive only the system prompt and the current user query — no prior conversation history. Preserves pure naive-panel independence (no anchoring to prior synthesized adjudicator voice across multi-turn conversations) at the cost of multi-turn coherence: the panel cannot reference prior assistant turns the user might allude to. Recommended for research/calibration sessions where statistical purity matters more than conversational continuity. The `panel_metadata.history_mode` field records `"synthesized"` or `"research"` per turn so M5 calibration can stratify by mode if relevant. See §15 Question 2 for the trade-off rationale.

Both settings default to off, matching v0.1 behavior. Users opt into the alternative behaviors deliberately.

## §12 — Capability Manifest Entry

Panel synthesis registers as a new asset family in the capability manifest (per parent §5). Proposed entry:

```json
"PANEL_SYNTHESIS": {
  "available": true,
  "version": "v0.1",
  "tool_binding": "panel_synthesize_stage7",
  "preferred_for": [],
  "interface_version": "1.0",
  "panel_slate": {
    "anthropic": "claude-opus-4-7",
    "openai": "gpt-5",
    "google": "gemini-3-pro-preview",
    "deepseek": "deepseek-v3"
  },
  "panel_resolver_rule": "exclude_adjudicator_family",
  "panel_size": 3,
  "synthesis_strategy": "anonymized_synthesizer",
  "tier_availability": "universal",
  "depends_on_assets": ["L2_5_HOLISTIC", "RAG_CORPUS", "RAG_GRAPH"],
  "depends_on_validators": ["P1", "P2", "P5"]
}
```

Note `preferred_for: []` — panel synthesis is *never* the preferred default for any query class. It is opt-in only. The Synthesis Router (B.7) does not auto-select panel mode; the user explicitly opts in via the composer checkbox.

The `panel_slate` field is the single point of configuration for which model version represents each lab on the panel. Native edits the manifest to change versions; no code change required.

## §13 — Tool Access for Panel Members

Each panel member receives the same tool surface that single-model mode would offer at the same point in pipeline evolution (per parent §14 obligation #1 — layer-aware tool decomposition). Panel members may call:
- the layer-specific retrieval tools (`retrieve_from_l1`, `retrieve_from_l25`, `retrieve_from_l3`, `graph_walk_l35`, `temporal_project_l5` — coming online with B.6);
- the existing `get_layer_document`, `search_signals`, `get_planetary_positions`, `get_dasha_periods`, `get_transits`, `get_pyramid_status`, `get_birth_data`, `get_domain_report` (per `platform/src/lib/claude/consume-tools.ts`);
- any future tools added to the consume tool registry.

**Each panel member's tool calls extend the baseline bundle.** The Stage-5 baseline bundle (assembled by the layered retriever per the QueryPlan from Stage 2) is the uniform starting context for all three panel members. Each member's additional tool calls during Stage-7 synthesis are extensions — they retrieve *additional* data, they do not replace the baseline. The baseline guarantees a uniform substrate for interpretive-divergence measurement; the extensions allow attention-divergence to manifest and be captured.

**Per-member tool transcripts captured.** Every panel member's complete tool-call transcript (which tools called, with what parameters, returning what content hash) is captured in `panel_metadata.panel_responses[].tool_calls` (§7 schema). The adjudicator at Step 5.6 receives these transcripts as part of the synthesis input and can flag extension divergences (`DIS.class.extension` per §6).

**Tool-use policy uniform across panel members.** No panel member has tools disabled. The DeepSeek-V3 selection (rather than R1) for the DeepSeek panel slot is precisely what enforces tool-availability uniformity, since R1 lacks tool-use natively.

**Request-scoped tool cache (v0.2 addition).** When two or three panel members independently call the same tool with identical normalized parameters within the same panel turn, only the first call executes against the underlying tool/sidecar/DB; subsequent identical calls within the same panel turn return the cached result. The cache is keyed on `(tool_name, hash(normalized_params))`, scoped to the panel turn (cleared at panel-turn boundary). Normalization is parameter-object hashing — `get_planetary_positions(date='2026-04-27')` and `get_planetary_positions(date='2026-04-27', divisional='D9')` are different cache keys.

The audit trail records every call (the `tool_calls` arrays in `panel_metadata.panel_responses[]` show every panel member's intended calls, with a `served_from_cache: true | false` flag per call) — so the extension-diversity signal is preserved even when actual execution happened once. This prevents the 3× thundering-herd problem on tool infrastructure (Python sidecar, Cloud SQL, GCS) without sacrificing audit fidelity. Per v0.2 §17 Fix 5.

**Merged super-bundle composition for adjudicator (v0.2 addition; see §5.6).** After Step 5.5 panel-member validation completes, before Step 5.6 adjudicator synthesis fires, the per-member tool-call results are deduplicated and merged with the baseline bundle into a single **super-bundle** that is handed to the adjudicator. This ensures the adjudicator can perform B.10 (no-fabrication) validation on every claim any panel member made, regardless of whether the supporting content was in the baseline or in some panel member's extension. Without the super-bundle, claims grounded in extended-only content would be unverifiable by the adjudicator — the v0.1 critical flaw §17 Fix 1 corrects.

## §14 — Migration Path

**v0.5 — OpenAI registry integration.** Smallest possible PR: add `@ai-sdk/openai`, registry entry for `gpt-5` (or current OpenAI flagship), resolver case in `platform/src/lib/models/resolver.ts`, `OPENAI_API_KEY` env var, capability flags. Validates that the model abstraction generalizes. No user-visible changes. Strict prerequisite for any subsequent panel work.

**v1.0 — Server-side panel orchestration.** Extends the request schema for `POST /api/chat/consume` to accept `panel_mode: boolean` and uses the user's selected model as the adjudicator. Implements Steps 5.1–5.7 as a server-side orchestrator. Pre-resolves the validated bundle (already done by Stage 5 of the parent design's v1.0 retriever-backed Consume), fans out panel calls in parallel, runs per-member validators (§5.5), invokes the adjudicator with the synthesis prompt template (§5.6), persists `panel_metadata` (§7), writes prediction-ledger entries for predictive-class queries (§9), handles failures per §10. No UI changes yet — testable via direct API calls.

**v1.1 — UI wiring.** Adds the panel checkbox to `Composer` (with auto-reset behavior per §4). Adds the audit-view affordance to assistant messages with tier-conditional content rendering (§11). Updates `useChatSession` to thread the `panel_mode` flag through to the API. Adds the divergence-classification rendering in audit view.

**v1.2 — Disagreement-classification consumer.** Surfaces `DIS.class.*` divergences from `panel_metadata` into the project's `DISAGREEMENT_REGISTER_v1_0.md` for cross-session analysis. Enables the M3 Learning Layer to begin consuming per-model calibration data accumulated by panel-mode usage.

**Critical commitment between v0.5 → v1.2**: panel mode does not modify the parent pipeline's Stages 1–6 or Stage 8. The only Stage-7 surface area that changes is the addition of a `panel_synthesize_stage7` branch, gated by the `panel_mode` flag. The parent design's v1.0 → v4.0 evolution proceeds independently; panel mode rides it as a synthesis-strategy variant at every version.

**Dependencies summary.**
- v0.5 depends on: nothing (independent registry expansion).
- v1.0 depends on: v0.5 complete + parent design `CONSUME_DESIGN_v0_1.md` adopted + parent v1.0 (post-B.6) live.
- v1.1 depends on: v1.0 complete.
- v1.2 depends on: v1.1 complete + `DISAGREEMENT_REGISTER_v1_0.md` ready for panel-mode entries.

## §15 — Open Questions Awaiting Native Decision

**Question 1 — Cost monitoring / kill switch.** Panel mode is ~4–5× the cost of a single-model query (4 LLM calls vs 1, plus extension retrievals). Does the platform need a per-day or per-week panel-query budget cap with a soft warning to the user when approaching the cap, or is the per-query checkbox + auto-reset sufficient cost discipline? Recommendation: soft warning at session level (e.g., "you've run 10 panel queries this session"), no hard cap in v0.1.

**Question 2 — Conversation history handling in multi-turn panel sessions. RESOLVED (v0.2, 2026-04-27).** Critique pass surfaced the trade-off explicitly: option (i) synthesized history loses pure naive-panel independence over multi-turn conversations because panel members are conditioned on prior adjudicator-voiced syntheses; option (ii) per-model history is incompletely specifiable (when a panel member wasn't on a prior panel and wasn't the adjudicator, what does it see? — either degenerates into option (i) for that turn or breaks user-reference coherence); option (iii) reset preserves independence but breaks "as you mentioned earlier"-style references entirely.

**Resolution:** default option (i) synthesized history (preserves user-conversation coherence; matches v0.1 behavior); opt-in option (iii) "research mode" as a per-user setting toggle (per §11) for sessions where statistical purity matters more than conversational continuity. Native chose this 2026-04-27. Option (ii) is rejected as incompletely specifiable. The audit trail records `history_mode: "synthesized" | "research"` per turn so M5 calibration can stratify by mode if relevant.

**Question 3 — Style suffix expansion.** Today's three styles (`acharya` / `brief` / `client`) are parent-design inheritance. Two additional styles plausibly serve panel mode well: `juror` (forces structured pro/con framing, useful for predictive-shaped queries with named falsifiers) and `red-team` (forces adversarial probing of stated claims, useful for high-stakes interpretive queries). Should v0.1 expand to five styles, or hold at three for parent-design parity? Recommendation: hold at three for v0.1, propose expansion in a separate follow-on artifact if usage demonstrates value.

**Question 4 — Latency UX granularity.** §11 proposes a coarse three-state progress indicator ("Running panel..." / "Adjudicator synthesizing..." / streaming). A finer indicator could show per-panel-member arrival ("Panel response 1 of 3 received...") but would leak the panel composition before the audit view is opened, which slightly violates the anonymization principle. Recommendation: coarse indicator in v0.1; revisit if users find it opaque.

**Question 5 — Adjudicator's own pre-draft.** Step 5.6 specifies the adjudicator as pure synthesizer (Workflow A from the prior brainstorm — receives panel responses + bundle, produces synthesis without first generating its own independent draft). Workflow B (adjudicator first generates its own draft, then synthesizes from its draft + 3 panel responses) is more rigorous but doubles the adjudicator's cost and risks self-anchoring. Locked at Workflow A for v0.1; flagged here for transparency in case future calibration data suggests Workflow B is worth the cost.

**Question 6 — Panel slate expansion beyond four labs.** v0.1 fixes the slate at Claude / GPT / Gemini / DeepSeek. Future slate expansion (Mistral, Grok, others) is not currently planned but is not architecturally blocked — the manifest's `panel_slate` field is extensible, and the panel-resolver rule (`exclude_adjudicator_family`) generalizes. Out of v0.1 scope; deferred.

## §16 — Adoption Path (proposed)

The proposed sequence for getting panel synthesis from DRAFT_PROPOSAL to executed feature:

**Step 1 — Parent design adoption.** This addendum has no architectural ground without `CONSUME_DESIGN_v0_1.md` adopted. The parent's §10 path applies: native review, then ND.2 (binding native directive on B.6) or PHASE_B_PLAN amendment v1.0.4. Until the parent adopts, this addendum stays in DRAFT.

**Step 2 — Native review of this addendum.** Once the parent adopts, native reviews this addendum with annotations and corrections. Particular attention requested on: §3 (panel composition rules — especially family-level exclusion), §6 (the new `DIS.class.extension` proposal), §9 (prediction-ledger interaction with non-predictive panel queries — confirm interpretation), §11 (audit-view tier-conditional content rendering — confirm the disclosure filter applies to audit view as it does to conversation panel), §15 questions 1, 2, and 3 (policy decisions awaiting native).

**Step 3 — ND.3 authoring (or PHASE_B amendment v1.0.5).** Once this addendum is reviewed and accepted, native directs adoption via either ND.3 (binding directive on B.7 — Synthesis Router phase, the natural home for panel synthesis as a router-level variant) or PHASE_B_PLAN amendment v1.0.5 promoting this addendum's content into B.7 deliverables. ND.3 is faster and lighter; the amendment is more durable. Recommendation: ND.3 first, with a requirement that B.7's brief authoring session promotes the directive's content into the plan.

**Step 4 — B.7 brief authoring.** A Cowork session authors the B.7 executor brief (under whatever brief mechanism is appropriate — explicitly NOT `CLAUDECODE_BRIEF.md` as that path is occupied by a parallel stream per native instruction 2026-04-27) with this addendum's content fully expanded into per-task acceptance criteria. The executor session implements v0.5 (OpenAI registry), v1.0 (server orchestration), v1.1 (UI wiring), and v1.2 (disagreement-classification consumer) in sequence.

**Step 5 — Post-implementation ratification.** Once panel synthesis is live in production, Cowork ratifies this addendum as adopted (status `CURRENT`) and converts any deltas-from-design back into either further ND directives or a follow-on PHASE_B_PLAN amendment.

This sequence respects the project discipline: design-before-build, governance-binds-execution, executor-honors-brief, ratification-after-fact. It also explicitly inherits the parent design's adoption sequencing — the addendum cannot leapfrog the parent.

---

## §17 — v0.1 → v0.2 Changelog

v0.2 was authored same-session as v0.1 (2026-04-27) in response to a six-point external critique pass conducted by another agent. The fixes below address each critique point. v0.1 is preserved historically only via this changelog — the file content above reflects v0.2 as the current authoritative draft.

**Fix 1 (CRITICAL) — Adjudicator super-bundle (§5.6, §13).** v0.1 handed the adjudicator only the baseline bundle plus per-member retrieval *transcripts* (tool name, params, hash), not the *content* of extended retrievals. This made claims grounded in extensions unverifiable by B.10 (no-fabrication) — the adjudicator was being asked to validate ungroundable claims. v0.2 introduces the **merged super-bundle** = baseline ∪ deduplicated extension content from all panel members, handed to the adjudicator at Step 5.6 so every claim can be validated against source. Schema (§7) gains a `merged_super_bundle` block.

**Fix 2 — Consolidation rule rewrite for orthogonality + grounding (§8 P7).** v0.1's consolidation rule preferred panel-cross-supported interpretations and demoted unique-to-one-member interpretations to "edge-case." This inverted the value proposition of panel mode: the unique insight from one model is precisely what panel mode is run to catch. v0.2 replaces with: select three interpretations that maximize coverage of the explanatory possibility space, subject to grounding (every interpretation cites L1 fact_ids per B.3); ungrounded interpretations excluded from user-visible three but logged as `interpretation_candidate_ungrounded` for outcome-driven resolution. Convergence preserved as audit metadata, does not bias selection.

**Fix 3 — Concurrent retry + opt-in 2-of-3 degrade (§10, §11).** v0.1's "single sequential retry then hard-halt" produced brittle uptime math (4 × 99% ≈ 96% panel success; degraded 90% provider drops to 87%). v0.2 introduces: **aggressive concurrent retry** (up to N=3 per panel member, retry fires concurrently with other members continuing) raising effective per-member success to ~99.99% even on degraded providers; plus an **opt-in 2-of-3 degrade mode** as a user-settings toggle (default off) preserving the Exec_10 hard-halt principle as default while allowing users to trade statistical fidelity for uptime. Audit trail flags degraded turns via `degrade_mode_triggered: true`; M5 calibration excludes them from training data by default.

**Fix 4 — History anchoring resolution (§15 Q2 → resolved, §11).** v0.1 recommended option (i) synthesized history without engaging the anchoring trade-off. Critique correctly identified that option (i) conditions panel members on prior adjudicator voice across turns, eroding independence over multi-turn conversations. v0.2 resolves: **default option (i) synthesized history** for UX coherence; **opt-in option (iii) "research mode"** as a per-user toggle (no history in panel turns at all) for sessions prioritizing statistical purity over multi-turn coherence. Option (ii) per-model history rejected as incompletely specifiable. Audit trail records `history_mode` per turn for M5 stratification.

**Fix 5 — Request-scoped tool cache (§13).** v0.1 did not address concurrent tool execution. Three panel members running in parallel could all call `get_planetary_positions()` simultaneously, causing 3× duplicate execution against tool infrastructure (Python sidecar, Cloud SQL, GCS). v0.2 introduces a **request-scoped cache** keyed on `(tool_name, hash(normalized_params))` with panel-turn scope. First call executes; subsequent identical calls return cached result. Audit trail records all calls with `served_from_cache: true | false` flag preserving extension-diversity signal.

**Fix 6 — Adjudicator/classifier split (§5.6, §5.6b, §6).** v0.1 asked the adjudicator to perform synthesis AND classify divergences in a single output. LLMs measurably degrade on combined synthesis-plus-strict-JSON-extraction tasks. v0.2 splits Step 5.6 into: 5.6 (adjudicator synthesizes, no classification); 5.6b (a smaller classifier model — defaulting to the adjudicator's family's smallest/fastest variant — extracts and classifies divergences from the panel responses + synthesis into the `DIS.class.*` schema). One additional small-model call per panel turn (~5% cost addition); sharper classification + unloaded synthesis cognition.

**Non-breaking with respect to parent design.** All six fixes affect only the Stage-7 internal implementation. The Stage-7 variant interface as seen by Stages 1–6 and Stage 8 is unchanged (still: receive validated bundle, return synthesis output, write extended audit-trail metadata). The parent design's v1.0 → v4.0 evolution proceeds independently; v0.2 of this addendum is fully forward-compatible.

**Critique-pass attribution.** The six-point critique that drove v0.2 was produced by an external agent (model identity not recorded in this artifact; the critique itself is preserved in the authoring-session conversation log). Whichever model produced it demonstrated panel-mode-grade rigor; the empirical observation that this critique surfaced six legitimate architectural concerns in one pass is itself a small data point in favor of panel synthesis as a research instrument.

---

*End of PANEL_SYNTHESIS_ADDENDUM_v0_1.md (DRAFT_PROPOSAL, v0.2 amendment 2026-04-27). Awaits parent design adoption then native review of this addendum. Next concrete artifact: ND.3 draft text (post parent adoption + native review).*
