---
artifact: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md
canonical_id: RETRIEVAL_PLANE_ELEVATION_PLAN
version: 1.2
status: DRAFT — FOR NATIVE REVIEW
authored_by: Claude (Cowork, Fable 5) 2026-07-19
parent_documents:
  - 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
  - 00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md (the WHY + acceptance criteria)
purpose: >
  The master plan to elevate the MARSYS-JIS retrieval plane into a single,
  best-in-class, multi-LLM-consumable system serving every door (Paripraśna,
  MCP raw tools, prashna_ask) from one compiled source of truth. Grounded in
  a three-agent code audit of registry, dispatch, envelope, budget, planner,
  and MCP edge conducted 2026-07-19.
changelog:
  - v1.2 (2026-07-19): RETRIEVAL_STRATEGY_v1_0 absorbed (§8 of that doc) —
    new §8 here: phase R-1.5 (Tool Census & Coverage Closure, grounded in
    the 2026-07-19 data-plane census), demand-driven serving items into
    R-2/R-3, spine bundles into R-4, strategy metrics as gate criteria,
    ruling rows RS-1/RS-2/RS-3.
  - v1.1 (2026-07-19): four-vendor industry consult absorbed (see
    RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md §4) — new §7 amendments:
    per-family schema dialect compiler, mandatory outputSchema,
    cache-stable projections, errors-as-steering contract, verbosity knob,
    compact-profile size split, tool-search metadata, agent-task evals,
    weak-caller circuit breakers, reasoning-artifact preservation,
    corpus-leg reranking, three new ruling rows.
  - v1.0 (2026-07-19): initial draft from the grounding audit.
---

# Retrieval Plane Elevation Plan

## §0 — The reframing this plan makes

The question that opened this workstream was "how should the MCP channel be
shaped?" The audit shows that is the wrong first question. The MCP channel,
Paripraśna, and the future `prashna_ask` are **doors**. What is behind the
doors — the retrieval plane — is today **not one system but three partially
overlapping ones**, and every weakness in every door traces back to that
fragmentation. This plan therefore targets the plane first, and lets each
door become a thin, generated projection of it.

**The governing architecture (confirms and sharpens handoff §4.1 / §7.1):**

```
  Paripraśna (portal)      MCP raw tools        prashna_ask (planned)
        │  our planner+loop     │  client's LLM       │  our planner+loop
        ▼                       ▼                     ▼
  ╔═══════════════════ THE RETRIEVAL PLANE ═══════════════════╗
  ║  ONE registry (compiled catalog)                          ║
  ║  ONE dispatch path (auth → pin → capability → handler)    ║
  ║  ONE envelope (v3, self-describing, register-labeled)     ║
  ║  ONE budget/trim discipline (structure-aware, honest)     ║
  ║  ONE planner (Vidhi: scope tuple → floor → receipt)       ║
  ╚═══════════════════════════════════════════════════════════╝
```

Answer to the native's question directly: **yes, an external LLM has two
routes today** (raw tools now; `prashna_ask` designed but unbuilt), and that
two-route shape is correct and should be kept — per handoff §7.1 they are
architecturally different (raw tools = "our retrieval plane, their brain";
`prashna_ask` = "our brain, their transport"). What is *not* correct is that
the plane behind those routes is fragmented. Fix the plane, and both routes
plus Paripraśna inherit the elevation simultaneously.

---

## §1 — Audit findings the plan is built on (ground truth, 2026-07-19)

Three parallel Fable-5 audit agents read the code. The load-bearing findings,
each verified with file:line citations (full reports in the session record):

### §1.1 The catalog is triplicated

- **Three parallel tool catalogs, no parity check.** (1) The retrieval
  registry — **123 capability descriptors** in
  `platform/src/lib/retrieval/registry/layers/`. (2) The contract catalog —
  ~76 `ToolContract` entries in `lib/contract/tool_metadata.ts`, **which is
  what the live chat LLM actually sees** (`schema_utils.ts:24-36`). (3) The
  MCP surface — ~25 hand-written `server.tool` registrations in
  `registry_bridge.ts` plus the hand-maintained alias/bridge maps. The
  carefully authored registry descriptions are served to **no one but MCP**,
  and the chat descriptions can drift from them silently.
- **Bootstrap duplication already caused two production outages.**
  `api/retrieval/capability/route.ts:103-135` maintains its own registration
  list separate from `catalog.ts`; D9 `judgment_query` and D10 `pact_query`
  each 404'd in production because one list was updated and not the other.
- **The Vidhi planning registry exists in three hand-synced copies** (two TS
  trees + a DB seed, migration 440); `capability_version.ts` hashes only one.
- **The session-pin type is hand-mirrored** into `platform-mcp/src/lib/session.ts`.
- Positive: the envelope mirror is **already codegen'd**
  (`platform-mcp/src/generated/envelope.ts`, sha-stamped, parity-tested) —
  the handoff's "hand-maintained mirror" claim is stale. The codegen pattern
  works; it just covers only the envelope.

### §1.2 The envelope is authored once, applied almost nowhere

- Only **6 of ~123 handlers** import `envelope.ts`; the rest emit bespoke
  JSON. Only **3 tools default to v3** (`judgment_query`, `graha_portrait`,
  `pact_query`); everything else defaults legacy, and legacy has **no
  `chart_header`** — most of the estate serves a foreign LLM with no
  chart-frame anchor at all.
- `judgment_flags` is typed `string[]` but `register_d8_assess_domain.ts:595`
  emits **objects**; flags range from stable tokens to multi-sentence prose —
  a consumer cannot switch on them.
- `envelope_version` stays `'v1'` even under v3; consumers must sniff a
  second field.
- Cursors encode only `{offset}` — no filter/sort fingerprint; a cursor
  replayed under different facets silently paginates the wrong family.
- `density_contract`: **6 of ~123** capabilities (~5%); three of the six
  declare `empty_reason:false` with "not yet added" notes.
- **No `register` block exists** (A-18 unbuilt): raw envelopes leak
  `SIG.MSR.*`, `marsys://` URIs, and layer-coded tokens with zero
  plain-language mapping — and on the raw-tools path the envelope is the
  *entire* epistemic safety mechanism (handoff §7.2).
- Two incompatible clippers coexist: structure-aware `response_budget.ts`
  (40/25KB, honest trim receipts) vs byte-truncating `result_clipper.ts`
  (32KB, produces invalid JSON). `still_over_budget` is emitted but **unread**
  by four direct callers; reference tools are entirely unclamped.

### §1.3 The planner is duplicated and mis-wired

- **Paripraśna does not use the Vidhi engine at all.** `consult/route.ts`
  runs `pipeline_planner` (its own `query_class` taxonomy) + a **hardcoded**
  B.11 floor injection — which pushes tool names (`pattern_register`,
  `cluster_atlas`) that `tool_name_bridge.ts` documents as resolving to
  nothing. The acharya floor / machine band / completeness receipt exists
  only for external MCP callers.
- **The DR-8 intent classifier's vocabulary has zero overlap with the Vidhi
  compiler's intents.** `scope_resolver.coerce` silently collapses every
  DR-8 intent to `general_synthesis`/`deepdive` — the advertised
  `intent_classify → plan_retrieval` path **never selects a domain floor**.
  CR-28 is worse than "three unreconciled implementations": there are three
  live taxonomies plus a dormant prompt, and the flagship handoff between
  two of them is a silent no-op.
- Domain floors are thin beyond wealth (career 12 / health 10 / marriage 9
  items vs wealth 26); 12 of 37 primitives are dark-by-construction with
  open CRs; `cr_status.ts` is a frozen snapshot with a self-flagged CR-55
  contradiction.

### §1.4 Multi-LLM adaptation is scaffolded but inert

- `server.ts:287-304` **fetches the model-family surface spec and discards
  it** — `max_tools` is never enforced; all 120 tools go to every client
  including families whose spec says they can't handle them. It even reads a
  `response_format` field the spec never contains.
- **No MCP tool annotations anywhere** (`readOnlyHint`/`idempotentHint`/…) —
  foreign LLMs must infer read-vs-write from prose.
- `behavioral_overrides` (the per-family hook) is populated **once** in the
  entire codebase; `drill_children` 11×; `output_schema` 4×.
- Descriptions are excellent but 1–2KB each, and several embed **the native
  chart's exact row counts** (66,738 / 27,554 / 5,566) — native-derived data
  in supposedly chart-agnostic descriptions that the chart-agnostic gate
  doesn't catch.
- `listCapabilities` silently ignores the `archetype`/`tool_role`/
  `traversal_level` filters its own type advertises.

### §1.5 Trust seams

- Dev-mode internal token check **fails open** (`route.ts:34-35`).
- `plan_retrieval` and the `vidhi_plan` prompt compile plans for **any
  chart_id with no entitlement check** (low disclosure, but a gap).
- `parity_check.ts` **auto-passes** (returns empty set) when its bridge
  import fails.
- Per-chart entitlement on the dispatcher is solid (fail-closed, 30s cache),
  as is the chart-agnostic gate (7 rules + raw-file scan).

---

## §2 — Design principles for the elevated plane

1. **One compiled catalog, many generated projections** (D-08, reconciled
   reading — requires OT-7 assent). Nothing that describes a tool to any LLM
   is hand-written twice. The `CapabilityDescriptor` is the single author
   surface; chat tool defs, MCP tool registrations, vidhi primitive rows,
   docs resources, and the census are all **compiled** from it, with CI
   parity gates in the style of the (working) envelope codegen.
2. **The envelope is the product on the raw-tools path.** A foreign LLM that
   reads carefully must get it right; one that reads carelessly must fail
   loudly (handoff §7.2). Everything in §4 serves this.
3. **Honesty is machine-readable.** Flags, coverage, trim receipts, and
   empty-reasons are closed vocabularies with structured detail — never
   prose-only, never silently absent (extends §N.6).
4. **One planner, every door.** B.11 is enforced by construction (a compiled
   floor), not by hardcoded injection — for Paripraśna exactly as for MCP.
5. **Adaptation is data-driven.** Per-model-family shaping flows from
   descriptor metadata + surface spec, both enforced at the edge; no
   prompt-engineering hopes.
6. **Fail closed everywhere**; every bypass found in §1.5 is removed.
7. **Measure, don't assume.** A standing multi-model eval battery is part of
   the plane, not an afterthought — retrieval quality per model family is a
   tracked number, and regressions gate merges.

---

## §3 — The plan

Six phases, R-0 … R-5. Each is a closable campaign wave with its own gate,
sized to the doctrine-wave cadence the project already runs. Dependencies are
strictly forward; R-1 and R-2 can overlap after R-0.

### R-0 — Ratify and de-risk (native session, no code)

1. Rule **OT-7** ("one registry, many generated projections") — every phase
   below assumes the *best-surface-per-channel* reading.
2. Rule **OT-10** (recommend (b)+(c): connect-time profiles — MCP-consult /
   MCP-expert — enforced by OAuth scope).
3. Adopt this plan's reframing into `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
   (§8.1 feedback rule: new decisions into its §1, new tensions §18, defects
   §16). **Commit the two currently-untracked governing docs.**
4. Sequence against the doctrine campaign: D-4 is INCOMING; this plan is the
   infrastructure track. Recommendation: R-1/R-2 may run pre- or inter-wave
   (they are serving-layer, not kernel); nothing here touches the FROZEN
   orchestrator or the L0–L5 writers.
5. Quick safety patch (single PR, no design): dev token fail-open →
   fail-closed; entitlement check on `plan_retrieval`/`vidhi_plan`;
   `parity_check` hard-fails when its import fails. These are one-liners and
   should not wait for their phases.

**Gate:** rulings recorded; safety PR merged.

### R-1 — One Catalog (kill the triplication)

The single highest-leverage phase.

1. **Promote the registry to sole author surface.** Extend
   `CapabilityDescriptor` (via the D1 amendment protocol — first real entry
   in `D1_AMENDMENTS`) with the fields the projections need:
   `display` (short_label, one_line, full_description — length-disciplined),
   `annotations` (read_only/idempotent/destructive/open_world),
   `register` block (A-18: reader-facing plain-language labels per §4.3),
   mandatory `density_contract` (A-05), `mutation` class (A-04),
   `projection_tags` (which surfaces serve it: chat / mcp_full / mcp_compact
   / mcp_consult), and `family_overrides` (subsumes `behavioral_overrides`).
2. **Build the projection compiler.** One build-time generator emits:
   (a) chat tool defs — replacing `lib/contract/tool_metadata.ts` as an
   authored artifact (it becomes generated); (b) MCP tool registrations —
   replacing the ~25 hand-written `server.tool` blocks in `registry_bridge.ts`
   and the alias files with a loop over compiled defs (handlers stay
   hand-written; *surfaces* are generated); (c) the vidhi primitive rows'
   tool bindings; (d) a machine-generated census (kills the hand-recounted
   `server.ts` comment); (e) a docs resource (`marsys://resource/catalog`)
   so any client can self-orient.
3. **One bootstrap.** `catalog.ts` becomes the only registration list;
   `api/retrieval/capability/route.ts` imports it. The class of D9/D10
   outages becomes impossible.
4. **Alias cutover** (A-02): delete the 41 live aliases + resolve the 6
   DEFERRED renames in one breaking release with
   `notifications/tools/list_changed`; `tool_name_bridge.ts` survives only
   for replaying persisted conversations.
5. **De-mirror by codegen** (extend the proven envelope pattern): vidhi
   registry (one TS source → generated MCP copy + DB seed), session-pin
   types, and — per A-01 — begin the `@marsys/contract` package as the
   long-term home. `capability_version` hashes the full compiled catalog,
   making the staleness kill actually cover all tools.
6. **Description hygiene:** strip native row counts (extend
   `chart_agnostic_gate` with a native-cardinality rule); enforce length
   budgets per display field.

**Gate:** one authored source; chat and MCP surfaces byte-derived from it;
CI parity (registry ↔ chat defs ↔ MCP tools/list ↔ census) green; aliases
gone; a grep for hand-authored tool descriptions outside the registry
returns zero.

### R-2 — One Envelope (the raw-tools path's entire defense)

1. **v3 becomes the only shape.** Every handler routes through
   `buildRetrievalEnvelope`; `envelope_version: 'v3'`; legacy served only
   behind an explicit `response_format:'legacy'` compat flag with a sunset.
   `chart_header` mandatory on every per-chart response (fail-loud
   `judgment_flag` if unresolvable, never silently null).
2. **Close the flag vocabulary.** `judgment_flags` becomes
   `{code, detail?, severity?}[]` with a closed, registry-checked code enum
   (a CI census of emitters already exists in audit form); the d8 object
   emission and prose-sentence flags migrate into `code+detail`. Ship a
   compat shim during transition.
3. **Self-describing envelopes for foreign LLMs** (the §7.2 answer):
   (a) the `register` block from R-1 rides in the envelope — every internal
   token that appears (`fact_ids`, drill URIs, flag codes, epistemic grades)
   has a plain-language label adjacent to it;
   (b) a compact `reading_contract` header block: one paragraph, generated,
   telling the consuming model how to read grades/coverage/flags — the
   loud-failure mechanism for careless readers;
   (c) `epistemic` + `coverage` + honest pagination mandatory (B.10:
   `total: null` stays honest).
4. **Cursor integrity:** cursors embed a filter/sort fingerprint hash;
   mismatched replay → explicit `cursor_filter_mismatch` flag, not wrong
   pages.
5. **One trim discipline.** All tools route through `finalizeMcpBudget`
   (which alone reads the true ceiling); bare `applyResponseBudget` callers
   and unclamped reference tools migrated; `still_over_budget` surfacing
   enforced by type (the finalize path is the only exported entry);
   `result_clipper.ts` evicted from the retrieval tree (adapters-only, or
   deleted with the orphaned `adapters/` families after confirmation).
   `density_contract` populated for all 123 (mandatory per R-1), with
   `empty_reason` actually implemented where declared.
6. Fix the stale provenance semantics (`build_id` doc → `build_runs`;
   `salience_formula_ver` either wired or removed).

**Gate:** 123/123 capabilities emit v3 with header, grades, coverage,
register labels, and budget discipline; a schema validator over live
`tools/call` output for the full surface passes; W4-style rubric battery
re-run confirms no answer-quality regression.

### R-3 — One Planner (Vidhi everywhere, taxonomies unified)

1. **One scope-tuple vocabulary.** Define the canonical taxonomy (superset
   mapping of DR-8 vocab, compiler `IntentClass`, and `query_class`);
   `classifyScope`, `scope_resolver`, and `pipeline_planner` all emit/consume
   it; `coerce` fails loud (`scope_unresolved` flag) instead of silently
   collapsing. This closes CR-28 fully.
2. **Paripraśna consumes the Vidhi floor.** `consult/route.ts` replaces its
   hardcoded B.11 injection with the compiled floor + machine band from
   `compileContract`; the completeness receipt rides into chat synthesis
   (and eventually renders in the portal). Dead injected tool names
   (`pattern_register`, `cluster_atlas`) die with the injection. B.11
   becomes enforced by construction on every door.
3. **Floor completeness campaign:** bring career/health/marriage floors to
   the §B0.4 mandatory-surface tag set; re-derive `cr_status` from the live
   register (resolving CR-55) and make dark-item receipts trustworthy;
   burn down the 12 dark primitives by CR priority (CR-56 first — flagged
   "#1 acharya-grade blocker").
4. **`plan_retrieval`/`vidhi_plan` become the same compiled artifact** the
   internal engine uses (they already call the same compiler — after (1)
   the DR-8 path actually reaches domain floors).

**Gate:** one taxonomy end-to-end (classifier → plan → floor → receipt);
Paripraśna emits completeness receipts; a scope-tuple round-trip test
(DR-8 output → compiled domain floor) passes for all intents; hardcoded
injection deleted.

### R-4 — Adaptive Multi-LLM Serving (the projections go live)

1. **Enforce the surface spec at the edge.** `server.ts` applies
   `max_tools`, name patterns, dual-output, and family quirks per authenticated
   principal; the discard bug dies. Projections from R-1 become real served
   surfaces: **MCP-full** (expert), **MCP-compact** (~25–35 umbrellas +
   `marsys_drill` dispatcher, leaves reachable via `drill_pointers`),
   **MCP-consult** (per OT-10: `prashna_ask` + ~5 orienting tools), **Chat**
   (planner-filtered per turn).
2. **Profile selection = entitlement** (OT-10 b+c): OAuth scope / connect
   URL selects the projection; a plain guest cannot reach raw tools.
3. **Annotations + family overrides live:** every generated tool carries MCP
   annotations; `family_overrides` drives description length and schema
   strictness per family (Anthropic long-form; OpenAI 64-char names +
   strict schemas; Gemini/DeepSeek per spec).
4. `listCapabilities` honors its full advertised filter set (routers can
   query by archetype/role/level).
5. **Foreign-LLM readback battery** (the measurement leg of principle 7):
   a standing eval where GPT/Gemini/DeepSeek-class models are given live v3
   envelopes and graded on (a) correctly distinguishing confirmed vs
   catalog-only, (b) honoring coverage/pagination honesty, (c) not
   inventing beyond `grounding`, (d) correct use of drill_pointers. Scores
   tracked per family per release; regression gates the merge. This is the
   empirical check on §7.2's "self-sufficient envelope" claim.

**Gate:** per-family `tools/list` conforms to spec in CI; readback battery
baselined with published scores; compact + consult profiles live behind
scopes.

### R-5 — `prashna_ask` + resilience hardening

1. **`prashna_ask`** (A-07: one agentic loop, two doors): contract =
   `{chart_id, question, scope_tuple?, depth, response_format}` →
   runs the *same* planner + loop + gates as Paripraśna, headlessly;
   returns synthesized reading + the v3 evidence envelopes + completeness
   receipt. Transport per OT-2 ruling (lean: progress notifications with
   job-handle fallback → decides the job table). Cost caps + entitlement
   enforced at the edge.
2. **Session semantics under D-05:** no transcripts; session pin + optional
   OT-6 journaling (questions + retrieval receipts only) if ruled in.
   Prediction ledger stays channel-agnostic (handoff §7.3) — outcomes from
   MCP land in the same Samīkṣā queue.
3. **Resilience:** rate limits per principal per projection; graceful
   degradation flags when the platform seam is slow; chaos test on the
   platform↔platform-mcp seam; load test the capability route (it is the
   single funnel for every MCP call).
4. **OT-5** (OAuth issuer) ruled and implemented in whichever direction the
   native picks; identity spine documented.

**Gate:** `prashna_ask` E2E on a non-native chart (Abhinandan `1c826d5a`)
with gates green; a consultation-profile client demonstrably cannot obtain
an ungrounded reading; full-surface load test passes.

---

## §4 — What this plan explicitly does NOT do

- Touch the FROZEN orchestrator, `WriterBase`, or any L0–L5 writer (§N.2).
- Redesign Paripraśna's UI/streaming/render (parallel workstream; R-3 item 2
  is a consumption change inside `consult/route.ts` only, coordinated per
  handoff §4.4).
- Reopen DR-5 (handoff §7.4) — `prashna_ask` is a door on the existing loop.
- Alter chart computation or any `chart_facts` semantics.

## §5 — Sequencing with the doctrine campaign

D-4 (model bakeoff) is INCOMING. R-0's safety patch and R-1 are
serving-layer-only and can proceed without kernel contention; R-2/R-3 touch
files D-4 lanes may also touch (`consult/route.ts`, envelope) — the conductor
should schedule them as either a pre-D-4 infrastructure wave or an
interleaved track with explicit `may_touch` separation. Notably, R-4's
readback battery directly *feeds* DR-12's bakeoff question with per-family
retrieval-consumption data — there is synergy in running R-1/R-2 before D-4
closes.

## §6 — Success criteria (the "best-in-class" bar, measurable)

1. **Zero duplication:** one authored catalog; every served surface
   generated; CI parity gates; hand-maintained census extinct.
2. **Zero hollow responses:** 100% v3, 100% density_contract, closed flag
   enum, honest coverage — §N.6 enforced by construction, not convention.
3. **One planner:** B.11 by construction on all doors; CR-28 closed; floors
   complete for all four domains.
4. **Measured multi-LLM quality:** readback battery scores per family,
   trending, regression-gated.
5. **Safe by default:** consultation profile default; raw tools
   scope-gated; all fail-open seams closed.
6. **Two doors, one brain:** `prashna_ask` live; identical question through
   either our door yields the same floor, receipts, and gates.

---

## §7 — Industry-consult amendments (v1.1)

Absorbed from `RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` (four-vendor
research: Anthropic, Google, OpenAI, DeepSeek — coverage 5/24 COVERED,
12 PARTIAL, 7 GAP against v1.0). Each item names its host phase.

**Into R-1 (One Catalog):**
1. **Per-family schema dialect compiler** — the projection compiler emits,
   from one canonical schema per tool: MCP-canonical, OpenAI-strict
   (`additionalProperties:false`, all-required, null-union optionality),
   Gemini OpenAPI-subset (flattened `$ref`/`anyOf`, shallow nesting),
   DeepSeek-strict-beta. Plus a portable-authoring lint: flat structure,
   enum-first, ≤2 nesting levels, minimal required params, name grammar
   `[a-z0-9_]{1,64}`, vendor size-ceiling checks.
2. **Mandatory `outputSchema`** on every generated tool (MCP 2025-06-18
   structuredContent discipline; also makes the surface programmatic-
   tool-calling-ready).
3. **Cache-stable projections** — byte-deterministic ordering and content
   per projection version, so client-side prompt caches (Claude
   `cache_control`, Gemini implicit prefix caching) hit reliably.
4. **`family_overrides` gains:** `input_examples` (emit for Claude-family;
   omit for OpenAI reasoning models where few-shot hurts) and
   `search_result` content-block emission for corpus tools (native span
   citations in Claude clients).

**Into R-2 (One Envelope):**
5. **Errors-as-steering contract, plane-wide** — every error names the
   specific fix and shows a correct example input; `errors_that_teach.ts`
   promoted from a local helper to the shared, CI-checked error shape.
6. **`verbosity: concise|detailed` request knob** wired through
   `density_contract` (Anthropic-pattern token control per call).

**Into R-4 (Adaptive Serving):**
7. **Compact-profile size split** — ≤20 umbrellas for non-Claude families
   (Google's official 10–20; OpenAI's <20); Claude-family compact may carry
   25–35 plus tool-search metadata.
8. **Tool-search-friendly expert profile** — namespaced names, a category
   inventory line, deferrable-tool flags (Claude `defer_loading` / OpenAI
   namespace deferral).
9. **Battery extension** — beyond envelope readback: tool-selection and
   agent-task evals (right tool, right chain, transcripts reviewed;
   frozen datasets; smooth-scored LLM graders), regression-gated.
10. **Trust posture** — read-only MCP annotations verified so client
    approval flows can relax; documented injection-safety stance for
    envelope content (tool results treated as untrusted by clients).

**Into R-5 (prashna_ask + resilience):**
11. **Weak-caller circuit breakers** — per-session identical-call
    detection returning a steering error, advertised step-cap advisory,
    validate-and-repair loop for malformed args.
12. **Reasoning-artifact preservation in the ModelPlane** — Gemini thought
    signatures and DeepSeek `reasoning_content` round-trip correctly
    inside the prashna_ask loop.
13. **Corpus-leg retrieval upgrade (scoped)** — reranking + contextual
    chunk enrichment for `ref_vector_search`/`ref_rules_search` (the only
    embedding-based leg; Anthropic contextual-retrieval pattern).

**New ruling rows for R-0 (added to the OT queue):**
- **RC-1:** compact-profile size split per family (accept ≤20 non-Claude?).
- **RC-2:** ChatGPT-connector projection — a fifth generated projection
  implementing OpenAI's fixed `search`+`fetch` contract. In scope
  now / later / never.
- **RC-3:** DeepSeek posture — consult-profile-only (recommended) vs raw
  surface with circuit breakers.

---

## §8 — Strategy amendments (v1.2)

Absorbed from `RETRIEVAL_STRATEGY_v1_0.md` (the end-goal doctrine: the
consuming LLM's capability/efficiency/productivity; see that document for
rationale). The strategy's §7 metrics become gate criteria alongside §6.

**New phase R-1.5 — Tool Census & Coverage Closure** (after R-1 descriptor
metadata lands, before/alongside R-2):

1. Run the strategy §6 eight-axis rubric over every capability →
   `RETRIEVAL_TOOL_CENSUS_v1_0.md`, machine-generated scorecard,
   re-generated at every subsequent phase gate.
2. **Coverage doctrine enforcement** (strategy §5.2): every table becomes
   SERVED / INTERNAL-BY-DESIGN (declared) / RETIRED. Wire the substantive
   dark set, priority order: `bodha_rm_dasha_windowed_prescriptions`
   (time-targeted remedies), CDLM rollup tiers
   (`domain_rollups`/`evolution_gradients`/`pattern_clusters`),
   `bodha_triangulation` + `bodha_cgm_sub_graphs`, the L0
   `reference_*`/`bg_*` catalog stratum (13 tables), `chart_panchanga` /
   `kala_timeline` / `chart_ayanamsha_reports`, and the four substantive
   mimamsa read candidates (`signal_adjustment`, `manifestation_sets`,
   `discoveries`, `insight_embeddings`).
3. Close the open structural register rows in scope: G-1 (CGM bhava
   edge-orphans — breaks graph chains through houses), S-3 (bhava_arudha),
   SC-2 (graha speed/retro/combustion), SC-3..5 (ashtakavarga refinements).
4. Supersede the stale `RETRIEVAL_COVERAGE_MAP_v1_0.md` (53-tool era) with
   the census.

**Into R-2 (One Envelope) — demand-driven serving:**
5. `demand_ranking` descriptor field + question-conditioned ranking on
   every umbrella (bearing-first ordering generalized from
   `judgment_query`; static salience demoted to tiebreaker).
6. Timing hooks or an honest `timing_anchored:false` on every
   signal-bearing response (strategy S-6).
7. Standardized prediction shape: claim + window + mechanism + confidence
   + calibration lineage — ledger-ready on both channels.

**Into R-3 (One Planner) — demand contract everywhere:**
8. The unified scope tuple accepted by every umbrella, not only plan
   surfaces; absent tuple → orientation slice + flag, never a default dump.
9. Completeness receipts served on both channels (the LLM can prove
   "thorough/complete" or see exactly what remains dark, CR-cited).
10. `get_chart_orientation` redesigned as the S-1 front door: frame +
    notables + active dasha + category map + drill pointers, ≤2,000 tokens.

**Into R-4 (Adaptive Serving) — width machinery:**
11. **Spine bundles** as first-class capabilities on all profiles:
    pre-joined `signal → activation windows → phala anchors → calibration`
    chains per domain/scope (census finding: only one real cross-layer
    join exists today; the LLM hand-stitches everything else).
12. Strategy §7 targets wired into the battery as tracked, regression-
    gated numbers: deepdive ≤10 umbrella calls; time-to-first-verdict ≤3
    calls; orientation ≤2,000 tokens; zero dead ends in a drill-pointer
    crawl.

**New ruling rows:** **RS-1** layering ruling (layered data / flat access
/ guided navigation, strategy §5.1) · **RS-2** coverage doctrine +
dark-table disposition authority (§5.2) · **RS-3** efficiency targets as
gate criteria (§7).

---

*End of RETRIEVAL_PLANE_ELEVATION_PLAN v1.2 (2026-07-19). Rulings it
requires: OT-7, OT-10, OT-2, OT-5, OT-6, RC-1, RC-2, RC-3, RS-1, RS-2,
RS-3, plus native assent to the §0 reframing and the R-0 §5 sequencing
recommendation.*
