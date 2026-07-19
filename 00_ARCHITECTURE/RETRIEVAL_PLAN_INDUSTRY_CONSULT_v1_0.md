---
artifact: RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md
canonical_id: RETRIEVAL_PLAN_INDUSTRY_CONSULT
version: 1.0
status: CURRENT
authored_by: Claude (Cowork, Fable 5) 2026-07-19
purpose: >
  Independent four-vendor research (Anthropic/Claude, Google/Gemini, OpenAI,
  DeepSeek) on retrieval-system and tool-serving best practices, consolidated
  into a checklist, then audited against RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.
  Verdict per practice: COVERED / PARTIAL / GAP. Gaps feed the plan's v1.1
  amendment (§4 of this document).
method: >
  Four parallel research agents, one per vendor, official docs prioritized
  over community sources; ~75 citable practices collected; deduplicated into
  the 24-row matrix below. Source URLs retained in the per-vendor appendices
  of the session record.
---

# Industry Consult — Four-Vendor Best Practices vs the Elevation Plan

## §1 — The consolidated checklist and coverage matrix

Legend: source vendor(s) in brackets. Coverage judged against
`RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (R-0…R-5).

| # | Practice (vendor) | Plan coverage | Where / gap |
|---|---|---|---|
| 1 | Small active tool set: ≤10–20 tools per turn — Google states 10–20 officially, OpenAI states <20 officially [G, O] | **COVERED** | R-4.1 enforces `max_tools` per family; MCP-compact (~25–35) + consult (~5) projections. Note: compact's 25–35 still exceeds both vendors' stated numbers — see §3.1. |
| 2 | Rich tool descriptions are the #1 performance factor; 3–4+ sentences for Claude; terse for OpenAI/Gemini with policy in system prompt [A, O, G] | **PARTIAL** | R-1.1 `display` fields + length budgets; R-4.3 family-driven length. Gap: no per-field guidance codified (what goes in description vs llm_hints vs system-prompt policy). |
| 3 | Consolidate related ops into fewer, workflow-shaped tools; namespace names by service/layer [A, O] | **COVERED** | Umbrella/drill topology + `layer_noun_verb` naming + `marsys_drill` dispatcher (R-4.1). |
| 4 | Per-family JSON-Schema dialects: OpenAI strict (`additionalProperties:false`, all-required, null-union optionality); Gemini OpenAPI subset (`$ref`/`anyOf` traps, silent keyword dropping, shallow nesting); DeepSeek strict beta subset (no min/maxLength) [O, G, D] | **GAP** | The projection compiler (R-1.2) emits one schema per tool. It must emit **per-family schema dialects** from one canonical schema, plus a portable-authoring rule (flat, enums, ≤2 nesting, few required params). Biggest single gap found. |
| 5 | Name constraints: 64-char `[a-zA-Z0-9_-]` (OpenAI), 64-char + charset (Gemini), no `-` in Gemini remote-MCP server names [O, G] | **PARTIAL** | `layer_noun_verb` names comply de facto; no CI check asserts the portable name grammar. Cheap add to R-1 parity gates. |
| 6 | Enums and strong typing over prose constraints; make invalid states unrepresentable [O, G, D] | **PARTIAL** | Facets exist in `density_contract`; but audit found handlers accepting free strings where enums belong. Add an enum-first schema lint to R-1. |
| 7 | Tool defs cost tokens on every request: cache-stable definitions, deterministic ordering, prompt-cache alignment (byte-stable prefixes for Gemini implicit caching; `cache_control` for Claude) [A, G, O] | **GAP** | Plan never mentions definition stability/ordering. Generated projections must be byte-deterministic across requests and versions-stamped so client caches hit. |
| 8 | Deferred loading / tool-search for large catalogs: Claude `defer_loading` + Tool Search Tool (~85% token cut, accuracy up); OpenAI `namespace` blocks + defer_loading [A, O] | **GAP** | Plan's answer to catalog size is projections + drill. Right, but incomplete: for Claude/OpenAI clients the full/expert profile should *also* ship tool-search-friendly metadata (namespaced names, category inventory line, deferrable flags). |
| 9 | Paginate/filter/truncate every large response with sensible defaults; steer in the truncation message; ~25K-token result norm [A] | **COVERED** | §N.6 + response_budget + honest pagination + R-2.5 universal budget discipline. Trim receipts already carry `recover_via` steering. |
| 10 | `response_format: concise\|detailed` knob per tool; return semantic identifiers, not bare UUIDs [A] | **PARTIAL** | density_contract byte caps exist; no concise/detailed request knob is planned. Envelope `register` block (R-2.3) covers the semantic-labels half. |
| 11 | Errors are a steering surface: actionable, prompt-engineered error text with example-correct input, not codes/tracebacks [A] | **GAP** (as a standard) | `errors_that_teach.ts` exists in platform-mcp but is not a plane-wide contract. Elevate to a mandatory error-shape on every capability (R-2 amendment). |
| 12 | Tool Use Examples (`input_examples`) for complex tools — Claude-specific field, 72%→90% param accuracy; but few-shot examples can HURT OpenAI reasoning models [A, O] | **GAP** | Not in the descriptor. Belongs in `family_overrides` (emit for Claude, omit for OpenAI reasoning family). |
| 13 | MCP spec compliance: annotations (readOnly/destructive/idempotent/openWorld), `structuredContent` + `outputSchema` + text duplication, cursor-paginated `tools/list`, `list_changed`, progress notifications, Streamable HTTP, OAuth resource-server pattern [A/spec] | **PARTIAL** | Annotations planned (R-1.1). structuredContent/dual-output already live. Gap: `outputSchema` mandatory-per-tool not planned (only 4 of 123 have `output_schema` today); progress notifications only appear in OT-2 for prashna_ask, not for slow raw tools. |
| 14 | ChatGPT connector / Deep Research contract: exactly `search` + `fetch` tools with fixed result shapes (`{results:[{id,title,url}]}` / `{id,title,text,url,metadata}`) [O] | **GAP** | No projection in the plan can serve ChatGPT connectors or Deep Research. If that reach is wanted, a fourth generated projection — **MCP-connector (search/fetch)** — must map the corpus + capabilities onto the two-tool contract. Decision for the native (§3.2). |
| 15 | Approval/trust posture: OpenAI approval flows default-on for MCP; treat tool-returned content as untrusted (prompt-injection); read-only annotations reduce friction [O, A/spec] | **PARTIAL** | OT-10 scope gating covers access. Gap: nothing in the plan asserts our read-only tools are annotated so clients can relax approvals; nothing documents our injection-safety stance for envelope content. |
| 16 | Loop-prone / weaker callers (DeepSeek et al.): identical-call dedupe, step caps, circuit breakers, tool-call-as-text recovery, validate-and-repair loop with structured error re-prompt [D, community] | **GAP** | R-5.3 has rate limits; it lacks per-session identical-call detection with steering errors, and a repair-loop stance for malformed args. |
| 17 | Model split-brain routing (DeepSeek reasoner can't call tools; R1 quirks: no system prompt, temp 0.6) [D] | **PARTIAL** | Only relevant where *we* drive the model (prashna_ask ModelPlane / D-4 bakeoff). Surface spec already models families; add reasoner-capability flags to it. Raw-tools path: client's problem, but our docs resource should state minimum-capability expectations. |
| 18 | Reasoning-continuity artifacts must round-trip: Gemini thought signatures; DeepSeek `reasoning_content` (400 if echoed wrongly) [G, D] | **PARTIAL** | Client-side on raw tools. For prashna_ask's internal loop (R-5.1) the ModelPlane must preserve per-vendor reasoning artifacts — not stated in the plan. |
| 19 | Retrieval quality mechanics: hybrid dense+sparse with reranking (Anthropic contextual retrieval −67% failures; Google rerank-after-vector; OpenAI RRF hybrid + score thresholds) [A, G, O] | **PARTIAL** | Our retrieval is mostly deterministic DB serving (different problem class — B.10 favors this). But `ref_vector_search` / `ref_rules_search` (the corpus leg) has no reranking or contextual-chunk stage in the plan. Worth a scoped item, not a rebuild. |
| 20 | Citations as API-grade output: Claude `search_result` blocks enable span-level citations; Google check-grounding per-claim scores; DeepSeek `[citation:X]` numbered-docs convention [A, G, D] | **PARTIAL** | Envelope `grounding` block is strong (fact_ids). Gap: emitting Claude `search_result` content blocks for corpus tools (family override) would give external Claude clients native citation UX for free. |
| 21 | Long-context ≠ RAG replacement: multi-needle accuracy drops; query-last ordering; don't send tokens you don't need [G, A] | **COVERED** | The whole density/budget doctrine + drill topology is this principle; nothing to add. |
| 22 | Eval-driven tool optimization: realistic multi-call eval tasks, transcript reading, LLM-graded rubrics with smooth scores, frozen datasets, regression gating per release; let the model refactor its own tools [A, O, G] | **PARTIAL** | R-4.5 readback battery covers envelope consumption. Gap: no *tool-selection/агent-task* eval (does the model pick the right tool and chain correctly on our surface?) and no transcript-driven tool-refinement loop. Extend the battery. |
| 23 | Structured outputs limits awareness (OpenAI 5K props/1K enums/~10 nesting; Gemini schema-size rejection in forced mode) [O, G] | **PARTIAL** | Our schemas are small; the dialect compiler (row 4) should enforce ceilings so a growing schema never trips a vendor limit silently. |
| 24 | Code-execution / programmatic tool calling consumption: document return formats so models can write parsing code; Anthropic PTC (−37% tokens), MCP-as-code-API (−98.7%) [A] | **GAP** (deliberate, low priority) | Requires stable `outputSchema` everywhere (row 13). Once R-2 lands, our surface is PTC-ready by construction; note it, don't build for it. |

**Score: 5 COVERED · 12 PARTIAL · 7 GAP** (of 24 consolidated practices).

## §2 — What the research validates in the plan (no change needed)

The plan's spine is strongly confirmed by all four vendors independently:

1. **Generated, per-family projections of one catalog** — Google prescribes
   dynamic tool subsetting; OpenAI ships `allowed_tools`/namespaces/deferral;
   Anthropic ships tool search. Nobody serves one flat 120-tool surface to
   every model. The plan's central bet (R-1 + R-4) is the industry position.
2. **Self-describing, honest envelopes** — Anthropic's "errors as steering,"
   truncation-with-guidance, citations, and coverage honesty map directly
   onto §N.6 / R-2. Our epistemic-grade + coverage-stamp discipline is ahead
   of anything the vendors publish.
3. **Eval-gated serving** — all three majors now ship first-party eval/grader
   frameworks and preach regression gating; R-4.5 is directionally right.
4. **Umbrella-and-drill** — matches Anthropic's consolidation guidance and
   OpenAI's namespace pattern almost exactly.

## §3 — Decisions the research forces

### §3.1 Compact-profile size
MCP-compact at ~25–35 umbrellas exceeds Google's official 10–20 and OpenAI's
<20. Recommendation: target **≤20 umbrellas** for the cross-vendor compact
profile, with the delta absorbed by `marsys_drill` — or keep 25–35 for the
Claude-family compact only (Claude handles larger catalogs, especially with
tool search) and serve ≤20 to Gemini/OpenAI/DeepSeek families. The
per-family `max_tools` machinery (R-4.1) already supports the split.

### §3.2 ChatGPT-connector projection (native ruling needed)
Reaching ChatGPT connectors / Deep Research requires the fixed
`search`+`fetch` two-tool contract (row 14). This is a *fifth* projection
with real design work (mapping chart-scoped capabilities onto a
document-shaped search/fetch model). Rule: in scope now, later, or never.

### §3.3 DeepSeek posture
Given DeepSeek's loop-proneness, no-native-MCP, and schema restrictions, the
realistic tiers are: (a) serve DeepSeek only the consult profile
(`prashna_ask` + orienting tools — our loop, their transport), or (b) also
serve a minimal raw surface with the row-16 circuit breakers. Recommendation:
(a) — it converts our weakest-client problem into our strongest guarantee.

## §4 — Amendment list for RETRIEVAL_PLANE_ELEVATION_PLAN v1.1

- **R-1 additions:** (i) canonical-schema → per-family dialect compiler
  (OpenAI-strict, Gemini-subset, DeepSeek-strict-beta, MCP-canonical) with
  portable-authoring lint (flat, enum-first, ≤2 nesting, minimal required,
  name grammar `[a-z0-9_]{1,64}`); (ii) mandatory `outputSchema` per tool;
  (iii) byte-deterministic, version-stamped projection output for prompt-
  cache stability; (iv) `input_examples` + `search_result`-block emission as
  `family_overrides` (Claude-family on, OpenAI-reasoning off).
- **R-2 additions:** (v) plane-wide errors-as-steering contract (every error
  names the fix + a correct example; `errors_that_teach.ts` promoted to the
  shared discipline); (vi) optional `verbosity: concise|detailed` request
  knob wired to `density_contract`.
- **R-4 additions:** (vii) compact profile ≤20 umbrellas for non-Claude
  families (per §3.1); (viii) tool-search-friendly metadata on the expert
  profile (namespaces, category inventory, deferrable flags); (ix) extend
  the battery beyond envelope readback to tool-selection/agent-task evals
  with transcript review; (x) read-only annotations verified so client
  approval flows can relax; injection-safety stance documented.
- **R-5 additions:** (xi) per-session identical-call detection + steering
  error + step-cap advisory (weak-caller circuit breakers); (xii) ModelPlane
  preserves vendor reasoning artifacts (thought signatures /
  reasoning_content) inside the prashna_ask loop; (xiii) corpus-leg
  (`ref_vector_search`/`ref_rules_search`) reranking + contextual-chunk
  upgrade as a scoped subtask.
- **New ruling rows:** §3.1 compact size split; §3.2 connector projection;
  §3.3 DeepSeek consult-only posture.

---

*End of RETRIEVAL_PLAN_INDUSTRY_CONSULT v1.0 (2026-07-19). Companion to
RETRIEVAL_PLANE_ELEVATION_PLAN (v1.1 absorbs §4).*
