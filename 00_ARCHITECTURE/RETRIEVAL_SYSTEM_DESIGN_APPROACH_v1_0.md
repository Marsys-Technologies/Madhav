---
canonical_id: RETRIEVAL_SYSTEM_DESIGN_APPROACH
version: 1.4
status: DRAFT
created: 2026-06-27
updated: 2026-06-27
author: Cowork (planning) — for native Abhisek Mohanty
classification: governance / design-of-the-design (meta-plan)
scope: Approach + work-breakdown for producing the full RETRIEVAL_SYSTEM_DESIGN master artifact (L0–L5, all assets, MCP + chat channels, multi-LLM)
deliverable_of_this_artifact: NOT the design itself — the grounded plan to BUILD the design
governs_until: superseded by RETRIEVAL_SYSTEM_DESIGN_MASTER_v1_0 (the artifact this plan produces)
changelog:
  - v1.0 (2026-06-27): Initial approach/meta-plan. Grounded in (a) internal audit of current retrieval/LLM/MCP corpus and (b) heavy external research on best-in-class retrieval (mid-2026). Design-only per Cowork-vs-Antigravity split; implementation deferred to Claude Code.
  - v1.1 (2026-06-27): Model-heterogeneity made a first-class, both-channels requirement (native ruling). Added: the Model-Aware Retrieval Orchestrator (MARO) as a shared core behind both channels (§A); the channel-asymmetry principle — full loop control on chat, surface-shaping-within-protocol-limits on MCP (§A); declared→profiled / undeclared→universal-best MCP behavior (§A, §5); a new dedicated wave D-PROFILES (the four behavioral profiles as a living artifact) inserted into the wave sequence (§3, §4); principle 8 split into orchestration (8) + profiles (11); decision points updated (§5).
  - v1.2 (2026-06-27): The two-sided ground-truth mandate elevated (native ruling: "this is the most important piece; getting it wrong is most expensive"). Added: §B — the bridge mandate (LLM-side from authoritative provider docs read verbatim; asset-side from full asset + Vedic-astrology comprehension); a new FOUNDATIONAL wave **D-GROUNDTRUTH** that PRECEDES D1/D5 and feeds the contract, tool topology, and per-asset surfaces (§3, §4); the **tool-topology framework** (single / multi / umbrella-thread-with-drill-down tools) made an explicit deliverable derived from asset + domain understanding (§B, §1 item I); principle 12 (LLM-side from authoritative docs) + principle 13 (tool topology is an astrological question) added; decision points + session map updated.
  - v1.4 (2026-06-27): **Chart-agnostic / anti-native-contamination mandate** made first-class (native ruling — recurrence of the data-plane contamination bug must be impossible by design). Added §D (the mandate + contract gate + the existing-code leakage audit findings) and binding principle #14. Native-leakage audit found CRITICAL contamination in the OLD `platform-mcp/src/tools/` surface (≥5 tools default a missing chart_id to the native; `lel_query` serves the native LEL corpus with no chart selector) — but the NEW `lib/retrieval/registry/` layer is clean. This hardens the §C.1.1 decision: build on the new registry; treat the old MCP tools as a remediation target, not a base. Runtime brief extended with a leakage audit block.
  - v1.3 (2026-06-27): **Code-plane validation pass** (native ruling: "validate the entire plan in Claude Code before implementation"). Two sub-agents read actual source; results in `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md`. Six load-bearing corrections folded in (new §C): (1) there are TWO/THREE parallel retrieval systems (lib/retrieval new + lib/retrieve old-with-tier + mcp/primitives_registry bridge) — the plan must name which it builds on; (2) MCP wires ~13 tools not 27, ~14 written-yet-unwired; (3) MCP has NO SSE (Streamable-HTTP only); (4) the dedup/UCD-first→drill topology is DOC-ONLY in code (only query_ucd exists) → TO-BUILD; (5) **all six layers have writers — the "L0–L2 reality / L3–L5 intent" split is REFUTED** (memory was stale; transit_search + L3/L4/L5 writers + CLOSE seals exist); (6) Anthropic not code-banned, only defaulted-away. Plus integrity flags: both manifests stale (2026-06-05), tier residue in MCP resources, gemini-vs-nim default discrepancy. Design-impact notes added per wave.
---

# RETRIEVAL SYSTEM DESIGN — APPROACH / META-PLAN (v1.0)

> **What this document is.** This is the *design of the design*. It does not contain
> the retrieval-system design. It contains the grounded, sequenced plan — work-breakdown,
> session waves, decision gates, audit targets, acceptance criteria — for *producing* the
> full retrieval-system design as a versioned master artifact across L0–L5, every asset,
> both consumption channels (MCP + chat), and all four LLM families.
>
> **Why a meta-plan first.** The retrieval system is the load-bearing seam between
> ~70 assets of expensive deterministic data and the LLMs that turn that data into
> acharya-grade reading. Designing it wrong wastes the entire data corpus's value; designing
> it in one undisciplined pass produces a document no one can execute. Per native ruling
> (2026-06-27), this session produces the approach; later sessions execute it wave by wave.

---

## §0 — Grounding established this session

Two parallel research streams were run before writing this plan. Both are folded into the
work-breakdown below; their full outputs are the evidentiary base. Key facts that shape the plan:

### §0.1 — Current-state reality (internal audit)

The legacy retrieval system was **surgically torn out** (`feature/legacy-teardown`, 2026-06-02);
`RETRIEVAL_INTERFACE_REGISTER_v1_0.md` is marked **WIPED** ("all 55 retrieval tool contracts removed").
What stands today is **not a greenfield** — it is a clean-slate scaffold plus residue:

- **A retrieval registry architecture already exists** at `platform/src/lib/retrieval/` —
  three primitive types (`tool` / `resource` / `prompt`), four adapter families
  (`agentic_loop/`, `bulk_context/`, `openai_function_calling/`, `hybrid/`), a canonical
  registry (`registry/index.ts` + per-layer `index.ts`), URI scheme `marsys://{type}/{layer}/{name}`,
  **no audience tier**. Governing doc: `L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md` (currently L2-scoped).
- **A live MCP server** (`platform-mcp/`, Cloud Run `amjis-mcp`, Streamable HTTP + SSE,
  Bearer + OAuth 2.0) exposing ~27 tools across L0–L5 — but a documented health audit
  (`MCP_TOOL_AUDIT_2026-05-25`) shows **5 working / 9 sub-optimal / 4 broken / 6 not-built**.
  The headline failure pattern: **MCP tools are stubs that silently drop filters** that the
  portal SQL layer implements (e.g. `query_signals` returns the full 573-signal MSR corpus
  unfiltered). The MCP and chat channels have **drifted apart**.
- **Multi-provider LLM routing already exists** (`platform/src/lib/models/`): Anthropic,
  Google, DeepSeek, OpenAI, NVIDIA registered; `resolveModel()`, family-worker map, health
  checks, reasoning-mode handling (markers / native / none). Per native standing policy,
  **Anthropic is cost-banned by default → Gemini primary, DeepSeek fallback** ([[feedback_llm_model_selection]]).
- **Embeddings are scaffold-grade**: TF-IDF+SVD 256-dim placeholder; Vertex AI 768-dim
  designed-not-deployed; `pgvector` columns exist; `vector_search` MCP tool currently **broken**.
- **Asset queryable surface is registry-described**: `asset_registry` table (storage_type,
  target_table, **count_sql**, scope, depends_on…) + `CAPABILITY_MANIFEST.json` (117 entries).
  This is the spine the design must consume — every asset already self-describes part of its surface.
- **Retrieval-plan coverage is uneven** (as the native stated): L1 Ganita rich; L0 Brahmagyan
  rich; L2 Bodha fragmentary (holistic_bundle live, not all `bo_*` wired); L3–L5 thin or data-pending.
  **[v1.3 correction — see §C.1.5]** Code validation REFUTED the "L3–L5 unbuilt" reading: all six layers
  have writers and CLOSE seals; the real uneven axis is *retrieval-surface wiring* (only `query_ucd` exists
  in the L2 registry) and *runtime data-population*, not asset existence.

### §0.2 — Best-in-class direction (external research, mid-2026)

The research converged on ten principles (full list in §6). The ones that most change our
design — and several that **independently validate existing MARSYS rulings** — are:

1. **Route, don't choose.** A query router is the top-level architecture: numeric/exact →
   deterministic tool; relational / "contradictions across layers" → graph; narrative → vector;
   simple → cheap single-shot; hard multi-hop → agentic loop. Reported 66–75% cost reduction.
2. **Failure mode > raw accuracy.** A path that *errors* on out-of-scope is safer than one that
   confidently fabricates. This is why a **semantic/metric layer** belongs in front of every
   numeric claim (errors-when-uncovered; ~98–100% on covered queries vs ~84% text-to-SQL).
3. **Reference the fact, never restate the number** — confirmed best practice in the grounding
   literature. This is **exactly your `CLAUDE.md §N.5` / MSR-drift rule**, externally validated.
4. **Invest in graph edges + a cheap query-time traversal primitive, not LLM pre-summarization.**
   Your relationships are already *curated* (CGM graph, CDLM, cross-asset linkage) — so skip
   GraphRAG's expensive, error-prone LLM entity/relation extraction. Go straight to
   property-graph + Text2Cypher (precise) + vector (entry points) + a PPR/LazyGraphRAG-style
   budget primitive for multi-hop / "themes across everything." **This is where the CGM's value lives.**
5. **Hybrid retrieval is the non-negotiable baseline** for the prose/citation corpus (bg_texts,
   classical attributions): BM25 + dense + RRF + cross-encoder rerank + top-20, with Anthropic
   Contextual Retrieval preprocessing (−49% retrieval failures). Pure-dense silently misses
   Sanskrit transliterations and asset IDs.
6. **Define retrieval primitives once as MCP servers, consumed cross-model**; few consolidated
   *workflow-shaped* tools (~10–15), not a 70-asset API mirror; resources for read-only catalogs;
   structured output + text fallback; **resolve opaque UUIDs to human-meaningful names**
   (your canonical chart_id is an opaque UUID — measured to hurt LLM precision).
7. **A model-agnostic adapter** must absorb the four families' real divergences: tool-arg decoding
   (OpenAI/DeepSeek return a JSON *string*; Anthropic/Gemini a parsed *object*), non-portable
   prompt caching (structure every prompt as `[stable prefix] + [variable tail]`), structured-output
   reliability (DeepSeek `json_object` drifts 5–12% → **validate-and-repair, never trust raw JSON**),
   and **context budgeted to the DeepSeek ~128k floor** with cited facts at top/bottom.
8. **The eval harness gates the seal and scores trajectories, not just outputs** — matching the
   existing "eval-harness-gates-L2-seal" plan ([[feedback_bodha_l0_bridge_and_eval_harness]]).

The strategic upshot: **we are not inventing from zero, and we are not adopting RAG orthodoxy
wholesale.** We extend the existing registry/adapter scaffold into a *router-fronted, semantic-layer-
grounded, graph-aware, multi-model* retrieval system whose primitives are defined once and served to
both channels — and we let the existing MARSYS disciplines (deterministic-first, reference-don't-restate,
floors-aspirational, no-audience-tier) act as guardrails that the external best practice happens to confirm.

---

## §A — The model-heterogeneity spine (the central architectural requirement)

> Added v1.1 after native ruling: **every request, on BOTH channels, may come from a different
> LLM family, and is highly likely to.** Maximum asset leverage + most efficient synthesis must
> hold for whichever model shows up. This is not a feature of one channel — it is the spine the
> whole system hangs on. The waves in §3 are reordered around it.

### §A.1 — Why a naive single MCP surface cannot satisfy this

MCP is, by protocol, **client-driven**: the connecting LLM owns the reasoning loop and decides
when to call tools, how many, in what order, and how to use what returns. A single naive tool set
cannot be simultaneously optimal for all four families because the *optimization target itself
differs per family*:

- **Anthropic (Opus/Sonnet)** — agentic, adaptive tool loop. Wants **many small, composable,
  well-described tools** it can chain; a monolithic "give me everything" tool wastes its strength.
- **Gemini** — very large context; prefers to **pull a large relevant bundle once** and reason over
  all of it. Wants a fat bundle-loader; fifteen tiny tools under-use its context advantage.
- **GPT (incl. reasoning models)** — reasons-then-acts decisively; strict about **structured output**;
  its own tool-call rhythm. Wants well-typed, predictable returns.
- **DeepSeek** — ~128k real context floor; **5–12% JSON-schema drift**; reasoning-marker quirk.
  Needs the most defensive, smallest-footprint, validate-everything treatment.

Optimizing tool granularity, bundle size, context budget, and output strictness for one family
de-optimizes the others. So heterogeneity must be handled by an explicit, model-aware component —
not by a one-size tool set.

### §A.2 — The architecture: a Model-Aware Retrieval Orchestrator (MARO) shared by both channels

Because heterogeneity is present on **both** the chat channel and the MCP channel (different LLM per
user, both sides), the per-model intelligence must live in **one shared core**, not in either channel.
Anything else duplicates the hardest logic and guarantees the two channels drift — which is precisely
the failure the current MCP already exhibits (filters honored in chat, silently dropped in MCP).

```
                 ┌──────────────────────────────────────────┐
   assets (L0–L5) │  Shared retrieval PRIMITIVES (over assets) │
   ~70, Postgres  └──────────────────────────────────────────┘
                                    │
                 ┌──────────────────────────────────────────┐
                 │  MARO — Model-Aware Retrieval Orchestrator │
                 │  reads the BEHAVIORAL PROFILE for the      │
                 │  active model family → shapes: tool surface,│
                 │  bundle size, context budget, output        │
                 │  validation, grounding, routing             │
                 └──────────────────────────────────────────┘
                          │                         │
              ┌───────────────────┐     ┌───────────────────────┐
              │  CHAT channel      │     │  MCP channel           │
              │  (we own the loop) │     │  (client owns the loop)│
              └───────────────────┘     └───────────────────────┘
                  Opus│Gemini│GPT│DeepSeek   Opus│Gemini│GPT│DeepSeek (BYO)
```

Shared primitives at the bottom (the assets), shared model-intelligence in the middle (MARO),
two **thin channel adapters** on top. Per-model logic exists once.

### §A.3 — The channel-asymmetry principle (stated honestly)

The two channels differ in exactly one way, and the design must be honest about it rather than
pretend otherwise:

- **Chat channel — we own the reasoning loop.** MARO has full control: it decides what to fetch,
  how to bundle, when to stop, how to budget context, how to validate. **Full per-model optimization
  is achievable here.**
- **MCP channel (BYO) — the user's LLM owns the loop; we cannot take it back.** MARO can shape *what
  each tool returns, how the surface is presented per family, grounding, budgeting, and validation* —
  but it **cannot force** Gemini to make one fat call instead of fifteen, force Opus to loop more, or
  stop GPT/DeepSeek from reasoning first. The client's native temperament asserts itself.

The mature design move on MCP is therefore to **invite** each model toward its best behavior rather
than try to control it: present a surface so well-shaped per family that the client's *native* loop
lands on the optimal path anyway. The truthful capability statement is:

> *On the chat channel, the system maximizes per-model value fully. On the BYO-MCP channel, it
> maximizes everything within protocol control (per-model surface, returns, grounding, budgeting,
> validation) and shapes the surface so the client's native loop is nudged onto the optimal path.
> It does not claim control over a stranger's loop — that would be a false promise.*

### §A.4 — MCP per-model behavior: declared → profiled, undeclared → universal-best (native ruling)

MCP does not reliably expose the connecting *model* (the client may report an app name, and any model
can sit behind any client). So per-model MCP optimization is **opt-in via declaration**, never magic
auto-detection:

- **Declared** (user/config/key states the model family) → MARO serves that family's **profiled
  surface** (fine-grained for Opus, fat-bundle for Gemini, strict-schema for GPT/DeepSeek).
- **Undeclared** → MARO serves **one excellent universal surface** engineered to be strong across all
  four (consolidated workflow tools, structured+text output, a `response_format`/`verbosity` lever so
  the client self-selects concise vs exhaustive).

Both are designed; the universal-best surface is the safe floor, the profiled surface is the
opt-in ceiling. (Declaration *mechanics* — config vs OAuth scope vs per-key binding vs client hint —
are resolved in-wave, not here.)

### §A.5 — What MARO guarantees regardless of model or channel

Independent of which family shows up and which channel it's on, MARO enforces the invariants that make
completeness and retrievability non-negotiable: **grounding** (reference `fact_id`, never fabricate a
number — §N.5), **validation** (validate-and-repair all structured returns; DeepSeek-grade defense by
default), **context budgeting** (pack to the smallest-supported real ceiling, cited facts at top/bottom),
and **the routing + graph + semantic-layer retrieval** that deliver the asset value. The *shaping*
varies per model; the *guarantees* do not.

---

## §B — The bridge mandate: two faces, each designed from ground truth (foundational)

> Added v1.2 after native ruling. The retrieval system is **a bridge with two faces**: the LLM on one
> side, the assets on the other. Each face must be designed from *authoritative ground truth*, not from
> assumption or generic RAG orthodoxy. This is the most expensive thing to get wrong, so it is studied
> FIRST, in a dedicated foundational wave (D-GROUNDTRUTH, §3), before the contract or the per-asset
> surfaces are designed — because both are downstream of this knowledge.

### §B.1 — The LLM-facing face: from authoritative provider documentation, read directly

The design's LLM-facing decisions (what tools, resources, prompts, schemas, caching strategy, structured-
output handling we build) must be grounded in the **primary-source, authenticated documentation of each
provider**, read directly and captured with citations — not from memory or third-hand summaries:

- **Anthropic** — MCP server authoring, tool/resource/prompt design, "writing tools for agents," code-
  execution-with-MCP, prompt caching (`cache_control`), tool-use + structured output.
- **Google Gemini** — function calling, context handling, context caching, OpenAI-compat surface, schema constraints.
- **OpenAI** — function calling, Structured Outputs (strict schemas), reasoning-model behavior, the MCP/connector contract.
- **DeepSeek** — function calling, JSON/`json_object` mode, reasoning-model handling.

The output is a **per-provider cited best-practices spec the design MUST honor**, for BOTH the internal
chat application AND the external MCP — covering resource creation, schema shapes, tool descriptions,
pagination, structured vs text returns, caching prefixes, and anything else the docs prescribe. The
explicit goal is **miss nothing**: if a provider's docs prescribe a practice for resources/schema/etc.,
it is captured and honored. Conflicts between providers are flagged for native decision (resolved toward
the cross-family intersection per §0.2 principle 8, or per-profile per §A).

### §B.2 — The asset-facing face: from full asset comprehension AND Vedic-astrology domain knowledge

The design's asset-facing decisions (the tool architecture over the assets) must be grounded in **two
kinds of understanding, both required**:

1. **Thorough asset + layer comprehension** — for every asset across L0–L5: what it is, what it stores,
   its queryable surface, its standalone value, its cross-asset synergy, and the relational/graph structure
   (CGM, CDLM, linkage). With the requirements that the tool underneath each asset delivers **completeness,
   high retrievability, and enforced de-duplication (no duplicates)** by construction.
2. **Vedic-astrology domain knowledge** — *very importantly* — a model of how an acharya-grade Jyotish
   reading **actually traverses a chart**: what is asked first, what naturally clusters, what drills into
   what, the hierarchy of inquiry (whole-chart-read → life-domain → factor → derivation → classical source).

### §B.3 — Why tool topology is an astrological question, not only a data-engineering one

The central design output of the asset face is the **tool topology** — and the native's key instruction is
that it is *derived from the assets and the domain*, never imposed generically. The topology question set:

- **One tool per asset, or multiple tools per asset?** Driven by what the asset *is* — a single flat
  emitter may warrant one tool; a rich relational asset may warrant several differentiated tools.
- **Umbrella / "thread" tools that fan out into finer-grained drill-down tools?** A reading starts broad
  (an umbrella tool that returns the high-level surface) and then drills (child tools for granularity). The
  *shape of that hierarchy must mirror how an acharya reasons*, because a topology that is technically valid
  but astrologically unnatural will be correct and useless.

> The discriminating principle: **whether `bo_laksana` (or any asset) is one tool or an umbrella-with-
> children is decided by how a jyotish reading traverses lakshanas — what an acharya asks for first, what
> they drill into — not by the table's row shape alone.** The astrology traversal model (§B.2.2) is therefore
> a *required input* to tool topology, co-equal with the asset comprehension and the LLM-side best practices.

### §B.4 — The three studies converge into one framework

D-GROUNDTRUTH runs three studies — (1) LLM-side authoritative best-practices spec, (2) asset + layer
comprehension, (3) the Vedic-astrology traversal model — and converges them into the **tool-topology design
framework**: the decision rules for single / multi / umbrella-thread tools, the dedup + completeness +
retrievability guarantees, and the worked examples, honoring both faces simultaneously. That framework then
feeds the RetrievalSurface contract (D1), the graph design (D4), and the per-asset fan-out (D5).

---

## §C — Code-plane validation corrections (the plan, grounded in running code)

> Added v1.3 after native ruling to validate the entire plan in code before implementation. Two sub-agents
> read the actual source (not summaries); full register in `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md`.
> **Code-plane only** — no prod DB/Cloud Run/build touched (governance). These corrections OVERRIDE earlier
> claims in this plan and the D-GROUNDTRUTH deliverables where they conflict.

### §C.1 — The six corrections that change the design

1. **Two (arguably three) parallel retrieval systems exist — earlier text conflated them.**
   `platform/src/lib/retrieval/` (NEW registry: 3 primitives, 4 adapters, tier-free — the modern target) ·
   `platform/src/lib/retrieve/` (OLD chat toolset `msr_sql`/`chart_facts_query`, used by `/api/chat/consult`,
   **still has `audience_tier`**) · `platform/src/lib/mcp/primitives_registry.ts` (a bridge aliasing
   `query_signals→msr_sql`). **D0 must rule on which system the design builds on and how the other two are
   migrated/retired.** This is the most important correction.

2. **MCP wires ~13 tools, not 27** ("27" was a file count; `/health` reports `tools:13`). ~14 tool files are
   **written-yet-unwired** (incl. `get_cgm_subgraph`, `vector_search`/bo_2-7, all `kala_*`, several phala) —
   real code, not broken stubs. D4/D7 can *adopt* the unwired graph/vector tools rather than build from zero.

3. **MCP has NO SSE** — POST-only Streamable HTTP, stateless. (Compatible with Gemini Remote-MCP, which needs
   Streamable HTTP anyway.) Any "SSE on MCP" text is corrected.

4. **The dedup / UCD-first→drill topology is DOC-ONLY in code.** The L2 registry has only `query_ucd` +
   `index.ts`; the drill tools (`query_zoom`/`lens`/`domain-evidence`) and the `lel_enabled` toggle do NOT
   exist in code. → The umbrella-then-drill topology is **TO-BUILD** (a clean slate aligned to doctrine), not
   "extend an existing implementation." The design alignment holds; the implementation does not yet exist.

5. **All six layers have writers — the "L0–L2 reality / L3–L5 intent" split is REFUTED.** Writers exist for
   every ka_*/ph_*/mi_* asset; `transit_search.py` is substantive; L3/L4/L5 CLOSE seals exist. The loaded
   MEMORY.md saying L3–L5 are unbuilt / transit_search never built is **STALE**. The true split is
   "L0–L2 mature vs L3–L5 recently-sealed," and the real unknowns are **runtime/data-plane** (has the writer
   *run* and populated the table), not existence. (Service-type assets have NULL floors by design.)

6. **Anthropic is not code-banned — only defaulted away** (`DEFAULT_STACK_ID='gemini'`; "credits exhausted").
   The ban is policy/memory, not code. Plus a real bug to note: `DEFAULT_STACK_ID='gemini'` vs
   `CALL_TYPE_ROUTING=STACK_ROUTING['nim']` disagree on the effective default by call site.

### §C.2 — Integrity flags the design must resolve (governance, D0/D8)

- **Both `CAPABILITY_MANIFEST.json` copies are stale** (stamped 2026-06-05, predate migration 325 + L3–L5
  writers). Even the "137 live" root copy is not ground truth; the **seed (81 assets) + the writers dir are
  closer**. Regenerate the manifest post-mig-325 and resolve the two-copy drift (root 137 vs platform 117).
- **`audience_tier` residue persists in MCP resources** (`house_rules_variants/{client,acharya,super_admin}.md`
  + an active `server_tier_visibility.test.ts`) despite the no-tier doctrine and the GISMCP-stripped memory.
  Strip on sight (per `feedback_no_audience_tier`).
- **The `gemini` vs `nim` default-stack discrepancy** in model routing — reconcile.

### §C.3 — What stayed CONFIRMED (the plan's foundations are sound)

The MSR/CGM spine is real and matches the schema (bodha_msr_signals with signal_id/constituent_facts_array/
classical_sources_jsonb/contradicts_signals_array/lel_origin; bodha_cgm_nodes+edges with the 768-dim vector;
bodha_contradictions FKs). The 3-primitive registry + 4 adapters are real. The 5-provider model layer with
reasoning-modes + family-worker map is real. The seed's 81-asset catalog is exact and its per_chart count_sql
correctly scopes by chart_id (the cockpit-lies trap is NOT present in the current seed). The embeddings path is
real Vertex 768-dim (`bo_samskara.py`), not the dead TF-IDF scaffold. So the *architecture* the plan rests on
is validated; the corrections are about scope, wiring state, and which-of-several-systems — not about the spine
being wrong.

### §C.4 — Deferred to a runtime session (NOT done here — prod-only governance)

Writers existing ≠ data built. The following need a controlled Claude Code/Antigravity session against prod
(not Cowork): whether L3/L4/L5 writers have actually run + populated tables on the native chart; whether
`bo_samskara` embeddings are populated; whether the deployed MCP revision matches main HEAD; live count_sql
correctness; whether `query_ucd` returns correctly against the live view. A runtime-validation brief for these
is an implementation-session deliverable.

---

## §D — The chart-agnostic mandate (no native contamination, by construction)

> Added v1.4 after native ruling. The retrieval tools must work on **whatever chart the portal/MCP/chat user
> is operating on** — never the native's data by default. Native contamination was an expensive data-plane bug
> the project already had to fix (positions stored under the wrong chart_id; the NATIVE_BIRTH sweep across ~40
> files; the LEL-strip). It must be **impossible to reintroduce in the retrieval layer by design.** A
> code-plane leakage audit (this session) found it is, in fact, **already present** in the old MCP tool
> surface — making this rule urgent, not theoretical.

### §D.1 — The two rules

1. **`chart_id` is always a runtime parameter, never a constant.** Every retrieval tool / query / MCP tool /
   chat path takes `chart_id` from request context and operates *only* on that chart. **Forbidden:** any
   literal chart_id in tool logic; any default-to-native fallback (`chart_id ?? NATIVE`, `.default(NATIVE)`);
   any `process.env.NATIVE_CHART_ID` default (a single global default is still not agnostic); any optional
   `chart_id` on a per-chart tool. **Required:** if `chart_id` is missing, the tool **errors loudly** — it
   does not fall back to anyone.

2. **No native facts baked into shared/global logic.** Not just IDs — also: native placements/dates as
   defaults (e.g. date ranges defaulting to the native's lifespan); the native chart used as a generic test
   fixture; native identifiers in LLM-visible tool descriptions (which bias the model to fill in the native
   when the user didn't specify); native-tuned thresholds/prompts; cache keys that collapse charts into a
   shared bucket. **The LEL/L5 layer is the danger zone:** the native's lived-experience calibration
   (`lel_origin`) must never bleed into another chart's retrieval — the LEL firewall (default
   `lel_enabled=false`, transitive `lel_origin` exclusion) is enforced through every tool.

**Construction-vs-shipped distinction (native ruling):** the native chart is FINE to use for audit, planning,
and read-only validation of queries. It must appear NOWHERE in shipped implementation as a default, a
fixture-masquerading-as-generic, or a baked value.

### §D.2 — The contract gate (D1 conformance, enforced)

The RetrievalSurface contract (D1) MUST require, and a gate MUST enforce, for every tool:
- declares `chart_id` as a **required** input drawn from context (per-chart tools);
- contains **no literal chart_id** and **no native-default fallback** (static check rejects `?? <uuid>`,
  `.default(<uuid>)`, `?? NATIVE*`, `env.NATIVE_CHART_ID ??`);
- **errors-if-missing** rather than defaulting;
- tool descriptions use a **neutral placeholder** (`<chart_uuid>`), never a real chart_id;
- per-chart caches **key on the real chart_id** (no `'default'` bucket — cross-chart collision risk);
- LEL is excluded by default and only included via explicit `lel_enabled=true`, transitively.
This sits alongside the F1 dedup gate (B6) and the completeness gate as a hard, CI-enforced conformance check.

### §D.3 — Existing-code audit findings (what we must NOT build on)

The leakage audit (full register to be filed) found two layers with opposite hygiene:
- **CLEAN — the NEW `platform/src/lib/retrieval/registry/` layer.** Every per-chart tool sets
  `required_inputs:['chart_id']`, scopes SQL `WHERE chart_id=$1`, and has **no native fallback** in any
  handler. Only LOW description-string cleanup (one `get_positions.ts` describe string names the native).
  **This is the correct base to build on** — reinforcing §C.1.1.
- **CONTAMINATED — the OLD `platform-mcp/src/tools/` surface.** CRITICAL: ≥5 tools resolve a missing
  `chart_id` to the native (`kala_temporal` ×2, `holistic_bundle`, `ganita_forensic_render`,
  `l0_brahmagyan`); `kala_convergence` defaults date ranges to the native's lifespan; **`lel_query` serves the
  native's LEL corpus with NO chart selector** (HIGH calibration-leak); several embed the native's computed
  dāśā tables as literal fallback data. Plus MEDIUM native-as-fixture tests (one even asserts a description
  must contain "Abhisek Mohanty", pinning the contamination green) and LOW native identifiers in ~21
  LLM-visible descriptions. (The dead phantom `362f9f17` is clean — zero hits.)

**Design consequence:** build on the new registry; treat the old MCP tools as a **remediation target** when
they are carried into the consolidated MCP surface (D7) — every native default removed, `chart_id` made
required, `lel_query` given a required chart_id, descriptions scrubbed to placeholders, cache keys fixed.

---

## §1 — What "the design" must ultimately answer (definition of done for the master artifact)

The meta-plan exists to produce a master artifact. That artifact, `RETRIEVAL_SYSTEM_DESIGN_MASTER`,
is **done** when it answers all of the following with acharya-grade rigor and zero hand-waving:

**A. The whole-system shape.**
- The end-to-end architecture from asset → retrieval primitive → router → adapter → channel → LLM,
  drawn as a single canonical diagram with every seam named.
- Where the two channels (MCP, chat) converge on shared primitives and where they legitimately differ.
- The contract by which any layer/asset onboards a retrieval surface (the analogue of the FROZEN
  `WriterBase` orchestrator contract, but for *retrieval* — call it the **RetrievalSurface contract**).

**B. Per-layer, per-asset retrieval surface (all ~70 assets, L0–L5).**
- For every asset: its storage_type, its queryable surface, which retrieval *modality* it serves
  (deterministic-fact / semantic-vector / graph-traversal / pre-rendered-summary), what value it
  provides standalone, and which primitive(s) expose it.
- The **synergy map**: which cross-asset combinations produce value no single asset holds
  (the CGM graph, CDLM asymmetry, convergence/contradiction surfacing) — and the primitives that
  realize that synergy.

**C. The router.**
- The query taxonomy and the routing policy (numeric → semantic-layer tool; relational → graph;
  narrative → hybrid vector; simple → single-shot; hard → agentic loop). Cost/latency/quality
  tradeoff per route. Termination policy for agentic routes.

**D. The grounding spine.**
- The semantic/metric layer that fronts every numeric/computed claim so the LLM *selects* governed
  metrics rather than fabricating numbers — and the enforcement of reference-don't-restate (`fact_id`
  inheritance) end-to-end.

**E. The Model-Aware Retrieval Orchestrator (MARO) + the four behavioral profiles.**
- The shared model-aware core (§A.2) that both channels consume: how it reads a family's behavioral
  profile and shapes tool surface, bundle size, context budget, output validation, grounding, routing.
- The normalization layer for the four families (tool-arg decoding string-vs-object, caching strategy,
  structured-output validate-and-repair, context budgeting, prompt prefix/tail). The per-family
  capability matrix.
- The **four behavioral profiles** themselves (Anthropic / Gemini / GPT / DeepSeek) as concrete
  orchestrator parameters — preferred tool granularity, bundle-size sweet spot, context-degradation
  curve, structured-output reliability, caching mechanics, reasoning-mode handling, arg-decoding —
  each a hypothesis from research, each hardened to measured fact by the eval harness, maintained as a
  **living artifact** re-measured as models evolve.

**F. The MCP + chat integration (with channel asymmetry).**
- How the wiped MCP surface is rebuilt as consolidated workflow-shaped tools over the shared primitives;
  how the chat engine consumes the same primitives; how filter-drift between the two is made impossible
  by construction (single source of query logic = the shared MARO core).
- The **channel-asymmetry design** (§A.3): full loop control on chat; surface-shaping-within-protocol
  on MCP; declared→profiled / undeclared→universal-best MCP behavior (§A.4); the honest capability
  statement of what is and is not controllable per channel.

**G. The eval + governance harness.**
- The retrieval eval harness (retrieval vs generation decomposition, recall@k ceiling, faithfulness
  headline, trajectory scoring, calibrated LLM-judge, golden set) that **gates any retrieval seal**.
- How retrieval primitives carry version/status/changelog under existing governance (drift_detector,
  CAPABILITY_MANIFEST registration).

**H. The migration from current state.**
- The honest path from "5 working / 9 sub-optimal / 4 broken / 6 not-built MCP tools + scaffold
  embeddings" to the target — what is salvaged, what is rebuilt, what is net-new. (Per
  [[feedback_rebuild_skepticism_of_existing_code]]: existing code is reference-for-intent, not authority.)

**I. The tool topology (the architecture of the tools over the assets).**
- The decision framework + the actual topology: per asset, whether it is one tool, multiple tools, or an
  **umbrella/thread tool with finer-grained drill-down children** — derived from asset comprehension AND
  the Vedic-astrology traversal model (§B), and conformant to the LLM-side provider best practices (§B.1).
- The by-construction guarantees that every tool delivers **completeness, high retrievability, and
  enforced de-duplication** over its asset(s).
- The cited per-provider best-practices spec (§B.1) the whole tool/resource/schema design honors.

If any of A–I is absent or hand-waved, the master artifact is not done.

---

## §2 — Method (how each design wave will be run)

Every design wave follows the same disciplined loop, mirroring the proven MARSYS pattern
(audit → holistic → per-unit → holistic → seal):

1. **Audit** the relevant slice of current state (code + docs + asset_registry rows) so the design
   is grounded in what exists, not assumed. Flag doc↔code contradictions.
2. **Holistic-first.** Design the cross-cutting shape for the wave's scope *before* drilling into
   individual assets/tools — so per-asset work inherits a coherent frame (the §0.2 Whole-Chart-Read
   discipline applied to retrieval design itself).
3. **Per-unit design.** Specify each asset's retrieval surface / each primitive / each route, against
   the holistic frame.
4. **Synergy pass.** Explicitly design the cross-asset / cross-layer value, not just the per-unit surfaces.
5. **External-validation check.** Cross-reference each wave's decisions against the §0.2 principles +
   the research sources; record where we deliberately diverge and why.
6. **Decision-gate to native.** Surface the wave's open decisions as explicit, numbered choices for
   native sign-off before they harden (per disagreement protocol + native-decides-formula-weights pattern).
7. **Versioned artifact.** Emit the wave's output as a frontmatter-bearing `.md` section/sub-artifact,
   registered for the manifest. One closed artifact per wave (cadence discipline).

**Operating constraints baked into every wave** (non-negotiable, inherited):
- **Design-only.** Output is committed `.md` design + pasteable Claude Code briefs — never chat bullets
  the native must translate ([[feedback_cowork_vs_antigravity_split]]). Implementation is Antigravity.
- **No fabricated numbers / no parity oracle.** Design verification is internal-consistency + classical
  re-derivation + FORENSIC grounding ([[feedback_no_jh_parity_anywhere]]).
- **Layer separation preserved.** Retrieval must not collapse facts into interpretation; L2+ primitives
  reference L1 `fact_id` and inherit values (§N.5).
- **No audience tier** anywhere in the design ([[feedback_no_audience_tier]]).
- **Verify state from CURRENT_STATE + git**, not stale doc snapshots, at each wave's audit step
  ([[feedback_verify_state_not_claude_md]]).

---

## §3 — Work-breakdown: the design waves (D0–D8)

Eight waves produce the master artifact. They are ordered by dependency: the contract and router
must exist before per-layer surfaces; the grounding spine and multi-model adapter are cross-cutting
and designed early; per-layer asset design fans out; integration and eval close it.

### D-GROUNDTRUTH — The two-faced ground-truth study (FOUNDATIONAL; precedes D1 and D5)
- **Produces:** the three convergent studies of §B and the tool-topology framework they yield —
  1. **LLM-side authoritative best-practices spec** (§B.1): Anthropic / Gemini / OpenAI / DeepSeek docs read
     directly, captured verbatim-cited, distilled into a per-provider spec the design must honor for tools,
     resources, prompts, schema, caching, structured output — for both internal chat and external MCP.
     Conflicts + gaps flagged for native.
  2. **Asset + layer comprehension matrix** (§B.2.1): every asset L0–L5 — what it is, stores, queryable
     surface, standalone value, synergy, relational/graph structure — with dedup/completeness/retrievability
     requirements per asset.
  3. **Vedic-astrology traversal model** (§B.2.2): how an acharya-grade reading traverses a chart —
     hierarchy of inquiry, what clusters, what drills into what. *Built WITH the native* (it encodes
     acharya-grade judgment; a sub-agent cannot guess it).
  4. **Tool-topology design framework** (§B.3–§B.4): the decision rules for single / multi / umbrella-thread
     tools with drill-down children; the by-construction dedup + completeness + retrievability guarantees;
     worked examples; honoring both faces.
- **Decision gate:** the topology decision rules; any provider-best-practice conflicts; the traversal-model
  hierarchy (native-authored).
- **Why foundational:** native ruling — this is the most important, most expensive-to-change piece; the
  contract (D1), graph (D4), and per-asset surfaces (D5) are all *downstream* of it. Designing them before
  this study would force a redesign after.
- **Depends on:** D0. **Feeds:** D1, D4, D5, D7.
- **Effort:** highest of any wave; runs as parallel sub-studies (LLM-docs + asset-comprehension can run as
  sub-agents; the traversal model is a native working session) converging into the framework.

### D0 — Foundations: glossary, current-state map, design principles (this plan → first execution wave)
- **Produces:** the consolidated current-state map (from §0.1, expanded with a code-level audit of the
  registry/adapter scaffold and the MCP server), the locked retrieval glossary, and the ratified
  design-principle set (from §0.2, accepted/diverged-from with rationale).
- **Decision gate:** confirm the ten principles as binding; confirm what is salvaged vs rebuilt at the
  scaffold level.
- **Why first:** everything downstream cites this.

### D1 — The RetrievalSurface contract (the "WriterBase for retrieval")
- **Produces:** the frozen-once contract by which any asset/layer declares its retrieval surface —
  modality(ies), primitive type(s), input schema, grounding obligations (fact_id references),
  governance fields. The analogue of the FROZEN orchestrator contract.
- **Decision gate:** the contract shape; the extension mechanism for L3–L5 (which don't exist yet) to
  onboard later without contract change.
- **Depends on:** D0, **D-GROUNDTRUTH** (the contract must express the tool-topology framework + the
  provider best-practices spec).

### D2 — The router architecture
- **Produces:** query taxonomy; routing policy across the five route classes; per-route cost/latency/
  quality budget; agentic-route termination policy (value-based stop, not hard loop count); how routing
  decisions are logged and evaluated.
- **Decision gate:** the taxonomy granularity; whether routing is model-driven, rule-driven, or hybrid.
- **Depends on:** D0, D1.

### D3 — The grounding spine (semantic/metric layer + reference-don't-restate enforcement)
- **Produces:** the governed metric/semantic layer over the deterministic assets so numeric answers are
  *selected from governed metrics*, not fabricated; the end-to-end enforcement design for fact_id
  inheritance; the "empty-on-missing, never-fabricate" behavior for graph/structured grounding.
- **Decision gate:** scope of the initial metric ontology (which numeric claims are covered v1);
  build-time pre-render vs query-time compute boundary.
- **Depends on:** D0, D1. **Cross-cuts all per-layer waves.**

### D4 — The graph retrieval design (CGM / CDLM / cross-asset synergy)
- **Produces:** the property-graph retrieval design — Text2Cypher precise traversal + vector entry
  points + a cheap multi-hop primitive (PPR / LazyGraphRAG-budget) for "themes/contradictions across
  everything"; explicit skip of LLM graph-extraction (relationships are curated); how the CGM graph and
  CDLM asymmetry become first-class retrievable surfaces.
- **Decision gate:** graph store choice / representation; the multi-hop primitive; passage-level retention
  to avoid the factual-regression trap.
- **Depends on:** D0, D1. **This is the single highest-leverage net-new wave** — it is where the corpus's
  unique relational value is unlocked.

### D-PROFILES — The four behavioral profiles + the MARO core (the model-heterogeneity wave)
- **Produces:** (a) the **MARO** design — the shared model-aware orchestration core (§A.2) that both
  channels consume, including the channel-asymmetry handling (§A.3) and the declared→profiled /
  undeclared→universal-best MCP behavior (§A.4); (b) the **four behavioral profiles** as concrete
  orchestrator-parameter dossiers (tool granularity, bundle-size sweet spot, context-degradation curve,
  structured-output reliability, caching mechanics, reasoning-mode handling, arg-decoding string-vs-object)
  — drafted as research-backed v1 hypotheses, with each parameter tagged for eval-harness hardening in D8.
- **Decision gate:** the profile parameter set (what we commit to measuring per model); the MARO core's
  boundary (what lives in the core vs the thin channel adapters); the declaration mechanics for MCP
  (config / OAuth scope / per-key binding / client hint).
- **Living-artifact commitment (native ruling):** the profiles are emitted as a standalone versioned
  artifact (`RETRIEVAL_MODEL_PROFILES`) that is re-measured and bumped as models evolve — never frozen.
- **Depends on:** D0, D1, D2, D3, D4 (it shapes how all of those are *served per model*).
- **Why its own wave:** native made model-heterogeneity the central requirement on both channels; the
  profiles are too load-bearing to bury as a subsection, and they must keep evolving. Slogan-level
  treatment ("Gemini has big context") would make the system mediocre for everyone.

### D5 — Per-layer / per-asset retrieval surfaces (the fan-out: L0 → L1 → L2 → L3 → L4 → L5)
- **Produces:** for every asset across all six layers, its retrieval surface against the D1 contract,
  its modality assignment, its standalone value, and its primitive bindings. Built layer-by-layer
  (L0/L1/L2 deeply against live data; L3/L4/L5 against placeholder/pending data with clean extension hooks).
  Includes the hybrid-retrieval design for the prose/citation corpus (bg_texts, classical attributions:
  BM25+dense+RRF+rerank+Contextual Retrieval).
- **Decision gate:** per-layer modality assignments; how data-pending layers (L3–L5) are designed without
  over-building (Macro-Plan scope-boundary discipline).
- **Depends on:** D1, D3, D4. **Largest wave — internally sub-waved per layer (D5.0–D5.5).**

### D6 — The synergy / whole-corpus value design
- **Produces:** the explicit cross-asset, cross-layer synergy map — the value combinations no single
  asset holds (convergence, contradiction, layered hydration L2→L1→L0). How the router + graph + grounding
  spine compose to deliver Whole-Chart-Read answers. This is the wave that makes the system *more than the
  sum of its assets*.
- **Depends on:** D2, D3, D4, D5.

### D7 — Channel integration (MCP + chat) over MARO
- **Produces:** the consolidated workflow-shaped MCP tool set rebuilt over the shared primitives + MARO;
  the chat-engine consumption of the same core; the by-construction elimination of MCP↔chat filter drift
  (single source of query logic = MARO); the concrete wiring of the channel-asymmetry + declared/undeclared
  surfaces from D-PROFILES into the live MCP server and chat engine.
- **Decision gate:** the abstraction substrate (e.g. LiteLLM-style proxy vs native-per-family — memory
  leans proxy for cost-tracking under the Anthropic ban); the MCP tool consolidation map (which of the
  current ~27 collapse into ~10–15 workflow tools); code-execution mode for large pulls.
- **Depends on:** D1–D6 + D-PROFILES. (Normalization mechanics + profiles come from D-PROFILES; this wave
  wires them into the two channels.)

### D8 — Eval harness + governance + migration plan (the seal)
- **Produces:** the retrieval eval harness design (retrieval/generation split, recall@k, faithfulness,
  trajectory scoring, calibrated judge, golden set, CI gate) that gates any retrieval seal; the governance
  wiring (versioning, manifest registration, drift detection for primitives); and the honest migration
  plan from current state (salvage/rebuild/net-new) with sequenced Claude Code briefs.
- **Decision gate:** the seal criteria; golden-set sourcing; migration sequencing.
- **Dual role:** the eval harness is also the instrument that **hardens the D-PROFILES dossiers** from
  research-backed hypotheses into measured-on-our-corpus facts (per-model, e.g. where each model's quality
  actually degrades on *our* assets), and provides the re-measurement mechanism for the living profiles artifact.
- **Depends on:** D1–D7 + D-PROFILES. **Closes the master artifact.**

---

## §4 — Sequencing, parallelism, and session map

Waves are not strictly serial. The realistic execution shape:

- **Session 1 (next):** D0 in full + **open D-GROUNDTRUTH** (kick off the LLM-docs study + asset-comprehension
  study; schedule the native traversal-model working session). Lands the current-state map, glossary, ratified
  principles.
- **Sessions 2–3:** **D-GROUNDTRUTH in depth** — the highest-effort wave. LLM-side cited spec + full asset
  comprehension matrix + native-authored traversal model → converge into the tool-topology framework. This is
  the foundation everything downstream is built on; it gets the time it needs.
- **Session 4:** D1 (RetrievalSurface contract, now expressing the topology framework) + D2 (router) +
  open D3 (grounding spine).
- **Session 5:** Close D3 + D4 (graph) — the two cross-cutting value waves. Highest-leverage non-foundational session.
- **Session 6:** **D-PROFILES** — the MARO core + the four behavioral profiles (model-heterogeneity wave).
  Sits here because it shapes how D2/D3/D4 are *served per model*, and must precede channel wiring (D7).
- **Sessions 7–9:** D5 fan-out, sub-waved per layer (D5.0 L0 + D5.1 L1 in one; D5.2 L2; D5.3–D5.5
  L3–L5 lighter), applying the D-GROUNDTRUTH topology framework per asset. Per-layer audit → holistic →
  per-asset → synergy. (Can overlap D-PROFILES — per-asset surfaces and profiles are largely independent.)
- **Session 10:** D6 synergy + D7 channel integration (wires MARO + profiles into MCP + chat).
- **Session 11:** D8 eval + governance + migration → harden the profiles to measured fact → seal the
  master artifact; red-team pass (cadence: macro-phase close requires red-team before seal).

**Parallelizable within a session** (via sub-agents): audit streams, external-validation cross-checks,
and per-asset surface drafting in D5 fan out cleanly. The holistic and decision-gate steps do not parallelize.

This is a **multi-session campaign**, consistent with daily-session / one-closed-artifact-per-session cadence.
A campaign tracker (`RETRIEVAL_SYSTEM_DESIGN_CAMPAIGN`) should be opened at D0 to hold live state, mirroring
the existing campaign-tracker pattern.

---

## §5 — Decision points requiring native input (surfaced now, resolved in-wave)

These are the choices that most shape the design. They are flagged here so the native can pre-steer; each
hardens at its wave's decision gate, not before.

1. **Scaffold disposition + system convergence (D0) [updated v1.3 — §C.1.1]:** there are TWO/THREE parallel
   retrieval systems (`lib/retrieval` new/tier-free, `lib/retrieve` old/with-tier, `mcp/primitives_registry`
   bridge). D0 must rule: build on `lib/retrieval` and migrate/retire the others, or unify differently. The
   *architecture* of `lib/retrieval` is validated as sound; the work is convergence + wiring (the MCP surface
   currently exposes no filtered signal query at all), not fixing a single drifted implementation.
2. **RetrievalSurface contract freeze (D1):** how frozen, how early? The orchestrator-contract precedent
   says freeze hard and onboard by conformance — but retrieval may need more evolution than the writer
   contract did.
3. **Router intelligence (D2):** rule-driven (cheap, deterministic, auditable — fits deterministic-first)
   vs model-driven classification (flexible, but a non-deterministic component) vs hybrid.
4. **Semantic-layer scope v1 (D3):** which numeric/computed claims get governed-metric coverage first.
   (Failure-mode principle says cover the high-traffic numeric claims; long tail can error-and-fallback.)
5. **Graph store + multi-hop primitive (D4):** representation and the cheap traversal primitive. Highest
   net-new technical decision.
6. **Multi-model substrate (D7):** a LiteLLM-style self-hosted proxy (unified normalization + cost
   tracking under the Anthropic ban) vs native-per-family adapters. Memory leans toward the proxy.
7. **MCP tool consolidation map (D7):** which of the ~27 current tools collapse into the ~10–15
   workflow-shaped target set.
8. **MARO core boundary (D-PROFILES):** what lives in the shared model-aware core vs the thin channel
   adapters. (Resolved: per-model intelligence is shared, not per-channel — but the exact seam is gated.)
9. **Behavioral-profile parameter set (D-PROFILES):** which parameters we commit to measuring per model
   (granularity, bundle sweet-spot, context-degradation curve, output reliability, caching, reasoning,
   arg-decoding). *Resolved by native:* profiles are a dedicated wave + **living artifact**, not a subsection.
10. **MCP declaration mechanics (D-PROFILES):** how a user declares their model family for the profiled
    surface — config vs OAuth scope vs per-key binding vs client hint. *Resolved by native:* behavior is
    declared→profiled / undeclared→universal-best; only the *mechanism* is gated.

---

## §6 — The fourteen ratified design principles (binding, pending D0 confirmation)

1. **Route, don't choose** — a query router is the top-level architecture.
2. **Failure mode beats raw accuracy** — prefer paths that error on out-of-scope over paths that fabricate.
3. **Numbers come from a deterministic source and are cited, not regenerated** — force tool calls; inherit
   `fact_id` values (confirms §N.5).
4. **Invest in graph edges + a cheap query-time traversal primitive** — skip LLM graph-extraction; the
   relationships are already curated.
5. **Hybrid retrieval is the non-negotiable baseline** for the prose/citation corpus — BM25+dense+RRF+rerank+top-20+Contextual Retrieval.
6. **Pre-render relational bundles as NL summaries for retrievability; pre-compute high-traffic answers** —
   the embodiment of "rich pre-computed ingredients, LLM synthesizes at query."
7. **Define retrieval primitives once as MCP servers, consumed cross-model** — few consolidated
   workflow-shaped tools; resources for catalogs; resolve UUIDs to names.
8. **A shared model-aware orchestrator (MARO), not per-channel logic** — per-model intelligence lives once,
   behind both channels; thin channel adapters on top. Absorbs the four families' divergences (arg-decoding
   string-vs-object, caching, structured-output, context budgeting to DeepSeek's ~128k floor, prompt
   prefix/tail). Honors channel asymmetry: full loop control on chat, surface-shaping within protocol on MCP.
9. **Never trust raw model JSON — validate-and-repair** — DeepSeek (the fallback) drifts 5–12% on schema.
10. **The eval harness gates the seal and evaluates trajectories, not just outputs** — retrieval/generation
    split; recall@k ceiling; faithfulness headline; calibrated judge; CI gate.
11. **Per-model value comes from evidence-based behavioral profiles, hardened by measurement, kept living** —
    each family is a concrete parameter dossier (granularity, bundle sweet-spot, context-degradation curve,
    output reliability, caching, reasoning, arg-decoding), drafted from research, hardened to measured fact
    by the eval harness on *our* corpus, and re-measured as models evolve. Slogans ("Gemini has big context")
    are not actionable; parameters are.
12. **The LLM-facing design is built from authoritative provider documentation, read directly** — Anthropic /
    Gemini / OpenAI / DeepSeek docs captured verbatim-cited into a per-provider best-practices spec for tools,
    resources, prompts, schema, caching, and structured output, for both channels. Miss nothing the docs prescribe.
13. **Tool topology is an astrological question, not only a data-engineering one** — whether an asset is one
    tool, multiple tools, or an umbrella/thread tool with drill-down children is derived from how an acharya-grade
    Jyotish reading traverses the chart AND from asset comprehension, with by-construction dedup, completeness,
    and high retrievability. A technically valid but astrologically unnatural topology is a failure.
14. **Chart-agnostic, zero native contamination — by construction** — every tool takes `chart_id` from request
    context as a required input, operates only on that chart, and errors (never defaults to native) if it is
    missing. No literal chart_ids, no native-default fallbacks, no native facts in shared logic, no
    native-as-generic-fixture, no native in LLM-visible descriptions, LEL excluded by default and transitively.
    The native chart may be used to BUILD and audit; it appears nowhere in the shipped implementation. Enforced
    by a CI contract gate (§D.2). A native default anywhere in a per-chart tool is a halt-worthy bug.

---

## §7 — What this session did NOT do (explicit scope boundary)

- Did **not** write the master design (that is D0–D8 across later sessions).
- Did **not** modify any code (design-only; Antigravity executes).
- Did **not** freeze the RetrievalSurface contract or pick the graph store / router intelligence /
  multi-model substrate / MARO core boundary — those are decision-gated in their waves.
- Did **not** author the four behavioral profiles or pick the MCP declaration mechanism — those are
  D-PROFILES work; v1.1 only established that they exist, where they live, and that profiles are a
  living artifact.
- Did **not** re-audit every one of the ~70 assets at row level — D5 does per-asset audit in its fan-out.

---

## §8 — Immediate next action

Open **D0** (current-state map, glossary, ratify the thirteen principles, open the
`RETRIEVAL_SYSTEM_DESIGN_CAMPAIGN` tracker) and **immediately kick off D-GROUNDTRUTH** — the foundational
two-faced study — since the contract (D1) and everything downstream depend on it. Concretely: start the
LLM-side provider-doc study and the asset-comprehension study (parallel sub-studies), and schedule the
native working session for the Vedic-astrology traversal model. The tool-topology framework that these three
converge into is the gating deliverable before D1.

---

*End of RETRIEVAL_SYSTEM_DESIGN_APPROACH v1.2 — meta-plan only. The artifact it produces is
`RETRIEVAL_SYSTEM_DESIGN_MASTER`, built across waves D-GROUNDTRUTH → D0–D8 + D-PROFILES; the behavioral
profiles are emitted as the living `RETRIEVAL_MODEL_PROFILES` artifact, and the LLM-side spec + tool-topology
framework as `RETRIEVAL_GROUNDTRUTH` deliverables.*
