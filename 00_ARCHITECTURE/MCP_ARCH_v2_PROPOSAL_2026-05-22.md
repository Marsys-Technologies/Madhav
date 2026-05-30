---
artifact: MCP_ARCH_v2_PROPOSAL_2026-05-22.md
status: SUPERSEDED
superseded_by: 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md
superseded_on: 2026-05-22
superseded_reason: |
  v2 still retained the Gemini Flash planner as a server-side LLM. Native correctly
  observed this is the same antipattern as v1's synthesis LLM, just at a different
  layer. v3 removes BOTH server-side LLMs (synthesis AND planner) and has Claude
  orchestrate tools directly per the canonical MCP pattern. v2 is retained as
  audit trail only; consult v3 for the current architectural direction.
authored_by: Claude (Cowork session, Sonnet 4.7)
authored_on: 2026-05-22
parent_brief: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
sibling_artifact: 00_ARCHITECTURE/MCP_DIAGNOSIS_2026-05-22.md
audience: native
disposition: SUPERSEDED — see v3
version: "2.0"
---

# MCP v2 — Context-Provider Architecture (Proposal)

**Subject:** Re-shape the MCP so the synthesis LLM runs on the *client side* (Claude in Claude Chat / Cowork), not on the *server side* (Gemini on the platform). The MCP returns a *retrieval bundle*, not a *finished answer*.

**Why now:** The native flagged that the current architecture is wrong in principle. The §1 diagnosis below explains why he is right. The §2 onward builds the v2 design.

---

## §1 — Why the current architecture is wrong (validating the thesis)

The shipped `ask_madhav` flow is:

```
Claude (host LLM) ──tool call──► MCP server ──HTTPS──► platform
                                                       │
                                                       ▼
                                          ┌────────────────────────┐
                                          │ planner (Flash, 2-3 s) │
                                          │ tools (parallel, ~1 s) │
                                          │ synthesis (Pro, 30-90 s) │ ← server-side LLM
                                          └────────────────────────┘
                                                       │
                                                       ▼
                                          answer_markdown ────────────►
Claude wraps Gemini's answer ◄────────── returned to MCP server
```

This double-LLMs the work. Two synthesis passes on the same query: Gemini synthesizes, returns a finished paragraph, then Claude (the host) takes that finished paragraph and re-wraps it into its own conversational reply. The user pays for both. The result is the worst of both worlds:

1. **Latency.** Server synthesis adds 30–90 s. Claude can't stream until Gemini finishes. The 60-s Claude Chat ceiling is breached on anything non-trivial (see sibling diagnosis §2).
2. **Quality compression.** Claude wraps Gemini's already-finished output. The host model can only paraphrase or quote — it can't think *with* the retrieval data. The signal-by-signal nuance, the contradictions, the cross-domain linkages that Claude *would* see if given the raw bundle — all get pre-collapsed by Gemini into prose Claude then has to summarize again.
3. **Wasted compute.** Two complete synthesis passes per query. The platform pays for Gemini Pro tokens. The user pays for Claude tokens to re-render those same tokens. Net spend, net latency, both doubled.
4. **Antipattern for MCP.** The MCP specification is built around exposing *tools* (verbs) and *resources* (nouns) — both of which deliver context. The model uses that context to reason and answer. An MCP that pre-bakes the answer with its own LLM is no longer an MCP; it's a remote-procedure-call wrapping a chatbot.
5. **It contradicts the brief's own intent.** `MCP_BRIEF_v1_0.md §1` says: *"the most underrated value isn't 'Claude can answer chart questions' — it is that Claude becomes a second seat at the instrument."* A second seat *at the instrument* — not a downstream consumer of Gemini's already-formed verdict. The v1 implementation drifted from that framing.

The right framing — the one you stated — is:

> *The planner builds the context and passes it over to Claude. Claude uses the payload along with its own context to respond to the user.*

Everything below is the development of that.

---

## §2 — v2 architecture: MCP as context provider

```
Claude (host LLM) ──tool call──► MCP server ──HTTPS──► platform
                                                       │
                                                       ▼
                                          ┌────────────────────────┐
                                          │ planner (Flash, 2-3 s) │
                                          │ tools (parallel, ~1 s) │
                                          │   compose context bundle │
                                          │  ✗ NO server-side LLM   │
                                          │    synthesis            │
                                          └────────────────────────┘
                                                       │
                                                       ▼
                                              { plan, context_bundle, ←
                                                synthesis_directives,
                                                epistemics,
                                                synthesis_audit }
Claude synthesizes ◄────────── returned to MCP server
   directly from
   the bundle
```

**One LLM pass. Server-side latency drops from 60+ s to 5–10 s. Claude streams natively to the user. The MARSYS platform becomes what an MCP server should be: a context-providing service.**

---

## §3 — The new response envelope

The platform stops returning `answer_markdown`. It returns a *research packet*. Concretely:

```jsonc
{
  "ok": true,
  "trace_id": "qry_2026-05-22_abc123",
  "audience_tier": "super_admin",
  "epistemics": {
    "surgical": false,
    "confidence_band": null,    // ← Claude assigns this AFTER synthesis (or via separate call)
    "horizon_days": null,
    "falsifier": null
  },

  "plan": { /* PipelinePlan as today */ },

  "context_bundle": {
    "query_text": "Which is my strongest planet?",
    "query_class": "factual",
    "expected_output_shape": "single_answer",

    "retrievals": [
      {
        "tool": "msr_sql",
        "tool_version": "1.0.0",
        "params_used": { "karakas": ["AK"], "limit": 10 },
        "results": [
          {
            "signal_id": "SIG.MSR.317",
            "content": "Jaimini — Moon as Atmakaraka (AK)…",
            "layer": "L2.5",
            "confidence": 0.92,
            "significance": 0.92,
            "source_canonical_id": "MSR",
            "source_version": "5.0"
          },
          /* … 9 more … */
        ]
      },
      {
        "tool": "chart_facts_query",
        "params_used": { "category": "shadbala", "rank_by": "total_rupas" },
        "results": [ /* numerical shadbala values once data is backfilled */ ]
      }
      /* one entry per tool that fired */
    ]
  },

  "synthesis_directives": {
    // The platform tells Claude HOW it should synthesize, without doing it itself.
    "cite_signal_ids_as_footnotes": true,
    "footnote_format": "[^SIG.MSR.NNN]",
    "use_multi_school_triangulation": false,
    "epistemic_disclosure_required": true,
    "horizon_required_if_forward_looking": true,
    "falsifier_required_if_predictive": true,
    "log_prediction_after_response": false,
    "style": "acharya",                      // or "client"
    "guidance_note": "Factual single-answer query — produce one tight paragraph."
  },

  "synthesis_audit": {
    "l25_tools_fired": ["msr_sql"],
    "l25_contribution_summary": "1 L2.5 tool fired",
    "holistic_read_passed": true,
    "b11_floor_enforced": true,
    "domains_touched": [],
    "available_signal_ids": ["SIG.MSR.317", "SIG.MSR.001", /* … */ ]
  },

  "suggested_followups": [ /* same as today */ ],
  "warnings": []
}
```

Two shapes change:

- **`result.answer_markdown` is removed.** No prose comes back from the platform on the default path.
- **`context_bundle` is added.** Structured per-tool retrievals with full signal/event records, params actually used, and provenance.

The other envelope blocks (`epistemics`, `synthesis_audit`, `plan`, `suggested_followups`, `trace_id`) remain — they describe *what was retrieved and under what governance rules*. Claude reads them and respects them.

---

## §4 — Tool-by-tool: what changes

| Tool | v1 behavior | v2 behavior |
|---|---|---|
| **`ask_madhav(query, mode?, context_hint?)`** | runs planner + tools + synthesis; returns `answer_markdown` | runs planner + tools; returns `context_bundle`. **No platform-side synthesis on the default path.** |
| `ask_madhav(query, synthesize: true)` | n/a | opt-in: also include Gemini's synthesis in the response, for *panel-of-acharyas* / inter-rater workflows. Costs extra; rarely needed. |
| `plan_query(query)` | returns `PipelinePlan` | **unchanged** |
| `execute_plan(plan)` | runs the plan + synthesis; returns answer | runs the plan; returns `context_bundle`. Same `synthesize: true` opt-in available. |
| Tier 3 surgical primitives | return raw data | **unchanged** (they were always context-provider tools — they didn't synthesize) |
| Tier 4 `read_asset` | returns raw markdown | **unchanged** |
| Tier 5 `get_trace` / `list_recent_queries` | returns audit data | **unchanged** |
| Tier 6 `log_prediction` / `record_outcome` / `flag_disagreement` | write tools | **unchanged** in shape, but the **discipline shifts** (see §5). |

Net code-surface change: `ask_madhav` and `execute_plan` are the only handlers that change behavior. The other 17 of 19 tools are unaffected.

The MCP-tool description for `ask_madhav` rewrites from *"Runs the full MARSYS-JIS astrological pipeline end-to-end…"* to:

> Returns a research packet for an astrological query. The MARSYS planner selects the right retrieval tools (MSR signals, LEL events, panchang, ephemeris, CGM topology, multi-school grounding…), executes them against the singleton chart, and returns the structured context bundle plus synthesis directives. You, the calling model, synthesize the answer from the bundle. Cite signal IDs from `context_bundle.retrievals[].results[].signal_id` using `[^SIG.MSR.NNN]` footnote syntax. Respect `synthesis_directives` (epistemic disclosure, falsifier on predictive queries, audience tier styling). Read the `marsys://chart-overview` and `marsys://house-rules` resources at session start to ground your synthesis voice.

That description is what makes Claude *behave correctly with* the bundle. It's load-bearing prompt engineering at the MCP-tool-description layer, exactly as `MCP_BRIEF §4.6` specified.

---

## §5 — Governance: what's preserved, what shifts

The brief codified twelve governance rules (G1–G12) for the MCP. Let me re-derive how each holds under v2.

| Rule | v1 enforcement | v2 enforcement |
|---|---|---|
| **G1** — B.11 Whole-Chart-Read floor (≥1 L2.5 tool on `ask_madhav`) | enforced server-side at `enforceB11Floor()` in `execute/route.ts:164` | **same** — floor is at retrieval-plan time, before tools fire. The `synthesis_audit.holistic_read_passed` flag is still computed server-side and returned in the envelope. Claude sees it and respects it. |
| **G2** — Audience tier stamping | tier resolved at MCP, stamped on plan, passed to citation/validator gates | **same** — gates that depended on synthesis context (citation gates, validator gates) now move to optional client-side validation OR run on the bundle (which contains all the signals that would have been cited). |
| **G3** — Trace logging | every step in `query_trace_steps` | **same** — the trace just gets shorter. No `synthesis` step (because it didn't happen). The retrieval steps and plan are still logged. `get_trace` still returns the full picture. |
| **G4** — PPL discipline (prospective predictions logged before outcome observed) | auto-logged server-side after synthesis | **shifts to Claude-driven**: if Claude emits a prediction, Claude calls `log_prediction(…)` as a follow-up tool. The `synthesis_directives.log_prediction_after_response: true` flag tells Claude to do this. Cleaner: the platform logs only what was actually predicted, not auto-generated placeholders with `[AUTO_LOGGED — native to specify falsifier]`. |
| **G5** — Disclosure tier (`epistemics` block mandatory) | block built server-side | block still built server-side, but `confidence_band` is null on the default path — Claude assigns it (because Claude is the one synthesizing). Or, optionally, Claude can call a `score_my_response({trace_id, response_text, confidence, falsifier})` tool to record its self-assigned epistemics back to the trace. |
| **G6** — Citation discipline (footnotes resolve to MSR signal IDs) | citations extracted from synthesis text via regex (`extractMcpCitations` in `execute/route.ts:208`) | **shifts**: bundle exposes `synthesis_audit.available_signal_ids[]` — Claude cites only from that set. Optional server-side validation tool `validate_citations({trace_id, cited_ids})` returns which cites are grounded vs fabricated. |
| **G7** — No fabrication (B.10) — numerical chart values come only from L1 / sidecar | enforced because synthesis prompt sees only retrieved bundles | **stronger** — Claude only ever sees the retrieved bundle. No prompt scaffolding to drift through. If a number isn't in the bundle, Claude can't cite it without fabricating, and fabrication is detectable post-hoc against the bundle. |
| **G8** — Layer purity (L1 reads, L1.5 reads, L2.5 synthesis) | mixed in synthesis prompt | **same**: bundle has per-tool layer tagging. Claude composes the L2.5 read from L2.5 signals; chart facts are tagged L1; panchang/ephemeris L1.5. Layer info is in every result. |
| **G9** — Versioning discipline (server semver) | platform-mcp package.json | **same** |
| **G10** — Scope boundary | enforced by brief | **same** |
| **G11** — Mirror discipline (no Gemini-side surface) | confirmed none | **same** |
| **G12** — Red-team obligation | discharged MCP-4-S2 | **needs a fresh red-team for v2 specifically** — the threat model changes (citation fabrication risk moves from "Gemini hallucinates" to "Claude cites IDs not in bundle"). |

**Net:** the v1 governance discipline carries over almost verbatim. The two non-trivial shifts are PPL logging (server-auto → Claude-explicit) and citation validation (regex post-extraction on Gemini output → bundle-set membership check on Claude output). Both shifts make the discipline *cleaner*, not weaker.

---

## §6 — Token economics & latency

For the trace I captured (`In one sentence: what is my Atmakaraka?`):

|   | v1 | v2 (default) | v2 (`synthesize:true` opt-in) |
|---|---|---|---|
| Platform LLM calls | 2 (planner + synthesis) | 1 (planner only) | 2 (same as v1) |
| Platform input tokens | ~8,600 | ~0 (planner has its own ~1,500) | ~8,600 |
| Platform output tokens | ~2,400 | ~0 | ~2,400 |
| Platform $ per query (est) | $0.03 | $0.001 (Flash planner only) | $0.03 |
| End-to-end latency to first byte | 60–90 s | **5–10 s** | 60–90 s |
| End-to-end latency to last byte | 60–90 s | **10–25 s** (Claude finishes) | 60–90 s |
| Tokens flowing into the host (Claude) | ~3,000 (the wrapped Gemini answer) | ~8,600 (the full bundle) | ~11,000 (bundle + Gemini's synthesis) |
| Net spend per query | platform pays $0.03 + user's Claude usage | platform pays $0.001 + user's Claude usage | platform pays $0.03 + user's Claude usage |

The bundle is bigger going into Claude than the v1 final answer was, but Claude's context window is 200k. ~8,600 tokens is 4% of capacity per query. For super-admin use (long acharya conversations), this is fine. For client-tier multi-turn flows, the bundle can be trimmed (significance-threshold filter, top-K cap).

**Latency-to-first-byte drops from 60 s to ~5 s.** That alone solves the Claude Chat timeout problem. Streaming-to-user is then Claude's responsibility, which it does natively.

---

## §7 — The quality argument (this is BETTER, not worse)

Counterintuitively, removing the Gemini synthesis step *raises* answer quality. Three reasons:

1. **Claude can think with the data, not around someone else's already-formed paragraph.** Currently the synthesis prompt to Gemini stitches 100 MSR signals into a single answer, and then Claude (in Claude Chat) sees that one answer as a tool result and has to figure out how to add value. Often it can't — it just repeats. In v2, Claude sees all 100 signals and decides for itself which 3 matter for the user's question. The reasoning chain becomes single-pass, coherent, and grounded.

2. **Model strength.** Sonnet 4.7 and Opus 4.6 are at least as strong as gemini-2.5-pro on long-context structured-data synthesis — and Claude is the LLM the user is *already* talking to. Routing synthesis through a second, weaker pass (Gemini Pro is good but not best-in-class) and then forcing Claude to re-render it costs quality at both layers.

3. **Conversational coherence.** The host LLM owns the conversation thread (D10 — single-shot MCP calls, host owns thread). When the host model does the synthesis, the answer is *in the host model's voice* and matches its prior turns. When Gemini does the synthesis, the user sees a stylistic seam in every reply. v2 removes the seam.

The brief's "panel of acharyas" goal (`MCP_BRIEF §1`) is *better* served too: instead of every Claude instance reading the same Gemini answer, every Claude instance reads the same *bundle* and produces its own independent synthesis. That actually generates inter-rater reliability data — Gemini's homogenizing pass was hiding the divergence.

---

## §8 — Backward compatibility & opt-in synthesis

Don't kill the synthesis path entirely. There are three legitimate cases for keeping it:

1. **The web `/consume` chat** (`/api/chat/consume/route.ts`). This is the platform's own UI. The platform IS the host LLM there. Keep this path completely unchanged.
2. **`ask_madhav(synthesize: true)`** — opt-in flag. Returns bundle *and* Gemini's synthesis. For inter-rater calibration workflows: native runs the same query with `synthesize:true` and asks Claude to compare its own synthesis against Gemini's. This is the "second seat at the instrument" use case made literal.
3. **Headless / programmatic clients** that have no LLM of their own and need a finished answer (e.g., a future webhook integration, or a CLI tool). They pass `synthesize:true` and get the v1 behavior.

So the platform keeps the synthesis machinery — it just stops invoking it by default through the MCP. The `/api/mcp/execute` route gets a `synthesize: boolean = false` parameter; when false, it returns at the `compose_bundle` stage; when true, it continues through synthesis (current behavior).

---

## §9 — Migration plan

This is a small change at the code surface but a meaningful product reshape. Sequence:

### §9.1 — Phase v2.0: ship the bundle response, keep synthesis as opt-in (1 session)

**`may_touch`:**
- `platform/src/app/api/mcp/execute/route.ts` — branch on `synthesize` param; default-false path returns the bundle; default-true path is the current behavior.
- `platform/src/lib/mcp/epistemics.ts` — add `buildContextBundle()` builder alongside the existing `buildEnvelope()`.
- `platform/src/lib/mcp/types.ts` — add `ContextBundle`, `SynthesisDirectives` types.
- `platform-mcp/src/tools/ask_madhav.ts` — add `synthesize` param to input schema; rewrite the §4.6 description to position the tool as a context provider.
- `platform-mcp/src/tools/execute_plan.ts` — same `synthesize` param.
- `platform-mcp/resources/house-rules.md` — add a new section *"Working with `ask_madhav` bundles"* that explains the citation convention, the directive fields, and the predict-then-log workflow.
- Tests: integration test that `ask_madhav` (no `synthesize`) returns bundle and no `answer_markdown`; integration test that `ask_madhav(synthesize:true)` returns both.

**`must_not_touch`:**
- `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `platform/src/lib/retrieve/` (except for the planner-params → tool-filter audit which is its own item).
- The `/api/chat/consume/route.ts` web chat path. Untouched.

**Acceptance criteria:**
- AC.v2.1 — `ask_madhav("What is my Atmakaraka?")` returns a bundle with `context_bundle.retrievals[]` populated, no `answer_markdown` field, and `synthesis_directives`.
- AC.v2.2 — `ask_madhav("…", synthesize:true)` returns both `answer_markdown` and the bundle. Latency ≥ 30 s (synthesis still runs).
- AC.v2.3 — Default `ask_madhav` latency drops to ≤ 10 s on factual queries.
- AC.v2.4 — Test from Claude Chat: ask "Which is my strongest planet?" — Claude reads the bundle, synthesizes correctly, cites the right signals, doesn't time out.
- AC.v2.5 — `synthesis_audit.holistic_read_passed` still computed and `true` on holistic queries.

**Estimated:** 1 session (~6 hours).

### §9.2 — Phase v2.1: explicit prediction logging and citation validation (1 session)

- `log_prediction` becomes the canonical PPL entry path from MCP. Remove the auto-log block in `execute/route.ts:548–594` (or guard it behind `synthesize:true`).
- New helper tool `validate_citations({trace_id, cited_ids[]})` — returns which cited IDs were in the bundle. Cheap. Optional Claude-self-check.
- New helper tool `score_my_response({trace_id, confidence, falsifier?})` — Claude writes back its self-assigned epistemics to the trace. Optional but improves audit data.

**Estimated:** 1 session.

### §9.3 — Phase v2.2: kill the `marsys_methodology_block` in MCP-served synthesis (parallel-safe with v2.0)

Even with the opt-in synthesis path, the `marsys_methodology_block` postlude shouldn't be emitted for MCP callers — the bundle already carries provenance. Gate the block by call source: present when the caller is the web `/consume` route, suppressed when the caller is `/api/mcp/execute`.

**Estimated:** ~1 hour. Can ship inside v2.0.

### §9.4 — Phase v2.3: red-team pass on v2 (per `MCP_BRIEF §6 G12`)

Threat model changes (citation fabrication, falsifier omission on predictive queries). Run a fresh §IS.8(b) red-team on the v2 surface. 0 class-1 findings required before v2 is sealed.

**Estimated:** 1 session.

---

## §10 — Open questions

1. **Should `context_bundle` include a pre-stitched markdown "research packet"?** I sketched §3 with structured per-tool arrays. Alternative: include both — the structured form (for programmatic clients) AND a pre-rendered markdown summary (for direct LLM consumption). Pre-rendering helps token-budget-constrained hosts. The structured form is the source of truth.

2. **How do we handle multi-school triangulation directives?** A `multi_school_triangulation` query class today fans out across Parashara/Jaimini/KP/Tajaka. In v2, the bundle includes per-school retrievals as separate `retrievals[]` entries; the directive `synthesis_directives.use_multi_school_triangulation: true` instructs Claude to produce a convergence-style synthesis. Claude probably handles this fine if the directive is clear. Worth validating.

3. **Does the host LLM need to know which retrievals were L2.5 vs L1?** Yes — `synthesis_audit.l25_tools_fired[]` + per-result `layer` field. Claude can produce a layer-respecting answer (L1 facts cited as facts; L2.5 syntheses cited as syntheses; no mixing).

4. **What about `chart_overview` for the bundle?** The MCP resource `marsys://chart-overview` already contains the canonical singleton-chart summary. Claude reads it at session attach. We do NOT need to include it in every bundle — that would be ~1,000 tokens of overhead per call.

5. **Should `synthesize:true` use Claude (via the host) or stay on Gemini?** It should stay on Gemini for the use cases it serves — that's its whole point (inter-rater workflow needs a *different* model from the host). If we routed it back to Claude we'd lose the second voice.

6. **What about Cowork (vs Claude Chat)?** Cowork's host LLM is also Claude. Identical architecture. No special handling.

7. **Conversation context.** D10 says single-shot. With v2, Claude is doing synthesis turn-by-turn, naturally accumulating context in its conversation thread. The MCP doesn't need a `context_hint` parameter anymore — Claude already has the prior turns. Consider deprecating `context_hint`.

8. **Caching the bundle.** Same-query, same-time bundles could be content-addressed and cached for 5 min. Cheap optimization, parallel-safe with v2.0.

---

## §11 — One-paragraph TL;DR for the operator

The shipped MCP runs Gemini synthesis server-side and returns a finished answer, which Claude (host) then has to re-wrap — two LLM passes, 60+ s latency, and worse answer quality than if Claude had just seen the raw retrieval data. The v2 architecture removes the server-side synthesis on the default path: the MCP returns a structured *context bundle* (planner output, all tool retrievals, synthesis directives, governance metadata) and Claude synthesizes from it directly. End-to-end latency drops from 60–90 s to 5–25 s, Claude Chat timeouts disappear, answer quality goes up (Claude thinks *with* the data instead of around Gemini's pre-baked paragraph), platform LLM spend drops to the planner-only cost, and governance discipline (B.11, audience tier, PPL, citations, traces) is preserved or strengthened. The synthesis path stays available as an opt-in `ask_madhav(synthesize:true)` for inter-rater workflows. Migration is ~3 sessions including a fresh red-team. This is the architecture the brief actually wanted — `MCP_BRIEF §1` framed Claude as *"a second seat at the instrument"*, not as a downstream consumer of Gemini's verdict — and the v1 implementation drifted.

---

*End of MCP_ARCH_v2_PROPOSAL_2026-05-22.md (DRAFT). Awaits native review. If accepted, supersedes the §7.1 fix list in `MCP_DIAGNOSIS_2026-05-22.md` (the postlude/timeout fixes become unnecessary once synthesis moves to the host).*
