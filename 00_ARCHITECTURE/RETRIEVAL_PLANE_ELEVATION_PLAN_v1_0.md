---
artifact: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md
canonical_id: RETRIEVAL_PLANE_ELEVATION_PLAN
version: 1.8
status: DRAFT — FOR NATIVE REVIEW
authored_by: Claude (Cowork, Fable 5) 2026-07-19; amended by the retrieval-audit reconciliation pass (Claude, opus/high) 2026-07-19
parent_documents:
  - 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
  - 00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md
  - 00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md (the WHY + acceptance criteria)
  - 00_ARCHITECTURE/briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md (v1.3 grounding — the six-lane code audit)
purpose: >
  The master plan to elevate the MARSYS-JIS retrieval plane into a single,
  best-in-class, multi-LLM-consumable system serving every door (Paripraśna,
  MCP raw tools, prashna_ask) from one compiled source of truth. Grounded in
  a three-agent code audit of registry, dispatch, envelope, budget, planner,
  and MCP edge conducted 2026-07-19.
changelog:
  - v1.8 (2026-07-19): scale/concurrency/QoS architecture added (§9.7 +
    W-28..W-31) per native question. Core doctrine: determinism makes
    responses perfectly cacheable (immutable per build_id — the invalidation
    signal already exists in pin drift detection); the Vidhi planner is
    deterministic and precompilable (≈zero marginal latency/cost); quality
    and UX are INVARIANTS under load — capacity absorbs pressure (cache,
    queue, parallelism, tiering), quality is never thinned to go faster;
    the battery runs at concurrency so the invariant is measured.
  - v1.7 (2026-07-19): Fable-5 architecture pass on the asset↔retrieval
    lifecycle. New §9.6 — the Concept Spine: a closed-loop design in which
    inventory truth is EXTRACTED (harvest pipeline) or GENERATED (single
    writable ledger, all other surfaces projections), never hand-authored;
    concepts carry lifecycle states with gated transitions; drift is caught
    at three horizons (merge / build / serve); new assets ship under a
    CI-enforced commissioning contract. W-24..W-27 added as the execution
    rows; W-20/W-22/W-23 re-anchored to §9.6 (design unchanged in intent,
    mechanism made derivation-first to solve the backfill-scale and
    perpetual-freshness problems the native flagged).
  - v1.6 (2026-07-19): W-20 grounded in code by a provider-side audit. Finding:
    the matrix's "declared" column has no source — no provider declares its
    concepts structurally (writer output inventory lives only in count_sql
    WHERE-strings + Python constants; bodha/kala/phala signal classes have NO
    enumeration anywhere; chart_facts has THREE inconsistent enumerations —
    CHART_FACTS_SCHEMA.json 147 vs coverage_matrix.ts 158 vs planner prose
    "37"; asset_registry row count itself disagrees 39/92/106 across surfaces;
    existing declared-vs-actual audits are soft/LOW). New rows W-22 (Provider
    Concept Manifest — the declared side) and W-23 (enumeration reconciliation
    + hard-gating of today's soft audits); W-20 amended to consume the
    existing surfaces rather than invent parallel ones.
  - v1.5 (2026-07-19): native requirement — total concept reachability made an
    explicit, checked deliverable. New §9.4 rows W-20 (Concept Reachability
    Matrix: every data-plane concept — table, fact_category, signal family,
    service endpoint — mapped to serving capability + umbrella path ≤2 hops +
    Vidhi primitive; compiled artifact, CI drill-crawl gate, consumed by the
    planner compiler) and W-21 (fact_category-level census: L1 concepts are
    categories inside chart_facts, so table-level coverage under-counts).
  - v1.4 (2026-07-19): native adjudication session (Cowork). All six §8.5
    Paripraśna contradictions RULED (C-1..C-6 dispositions in new §9);
    F-R1/F-R7 absorbed; AMBIG-1..4 dispositioned; the R-0.5 safety patch is
    NOT executed as a standalone hotfix per native decision — all safety
    items tracked in §9.1 and executed at implementation. §9 is the
    consolidated implementation-opening checklist; nothing is implemented
    before the campaign opens.
  - v1.3 (2026-07-19): six-lane retrieval-audit ground-truth register absorbed
    (`briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md`, adjudicating every
    §1.1–§1.5 claim against file:line lane evidence). Corrected **13 stale
    facts** in §1 (catalog #2 is a 6-entry served `ToolContract` catalog not a
    76-row `ToolReconciliationEntry` audit table; the D9/D10 bootstrap bug class
    is LIVE not historical — `getCatalog()`↔`route.ts` disagree 118 vs 122 for
    D6/MARO/synth; the 123 count needs a codegen-verified caveat; `result_clipper`
    is NOT orphaned; unclamped surface is ~36/115 tools; `still_over_budget` is
    dead on every path; only `pattern_register` is pushed live and `cluster_atlas`
    is a dead constant; `registry_data.ts` has two already-drifted copies with no
    parity gate; CR-55 is tri-state; description leakage is 11 instances / 8 files
    incl. native PII; the fail-open dev token is a 13-file pattern; `parity_check.ts`
    may be dead code). Absorbed **17 new-gap items** (GT-40..GT-56) into their host
    phases. Marked **1 item already-done** (GT-8: envelope codegen exists — though
    the parity test is not CI-wired). **Re-scoped R-3.1** from a flat superset-rename
    enum to a decomposed scope tuple `{answer_mode × domain × depth × horizon}` with
    `IntentClass` derived, per Lane C's orthogonal-axes finding (GT-24 — the single
    biggest plan correction). Added the **six Lane-F Paripraśna-alignment
    contradictions C-1..C-6** as new open ruling items (raised, not resolved — native
    rulings required). Wired `ka_graha_sancara` + `kala_timeline` into R-1.5;
    corrected the L0 table census (13 → ~39 physical) and the single-directory grep
    methodology; routed the envelope-honesty gaps into R-2.
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

*(§1 corrected against `GROUND_TRUTH_REGISTER.md` v1.0, 2026-07-19 — GT-IDs cited inline.)*

- **Three parallel tool catalogs, no parity check.** (1) The retrieval
  registry — **≈118 capability descriptors** in
  `platform/src/lib/retrieval/registry/layers/` (GT-1: no single grep
  reproduces one number — `getCatalog()` reaches 118, `route.ts` bootstrap 122,
  `server.tool(` sites 115; the old "123" is a stale snapshot ±5. **The census
  must be codegen-derived, not counted** — do not treat any single count as an
  invariant). (2) The contract catalog — **NOT** the 76-row table the plan
  previously named. GT-3: those 76 rows in `lib/contract/tool_metadata.ts` are
  typed `ToolReconciliationEntry` (an audit/coverage map, `tool_metadata.ts:300`)
  and are **not served**. The actually-served chat contract catalog is
  `TOOL_CONTRACTS` in `lib/contract/registry.ts` = **6 `ToolContract` entries**,
  feeding `CONTRACT_CATALOG` → `schema_utils.ts:24-36` (the live chat surface).
  **The chat LLM sees 6 rows, not ~76.** R-1's compiler must absorb the real 6
  and separately retire/re-scope the 76-row audit table. (3) The MCP surface —
  **25** hand-written `server.tool` registrations in `registry_bridge.ts`
  (GT-5: the `server.ts` census comment's "20" is itself stale; the aggregate
  live MCP tool count is **unverifiable to an exact integer by grep** —
  wrapper-indirection via `regAlias`/`globalAlias` defeats a naive count; lower
  bound ≈145; any R-1 number must come from an AST/runtime census) plus the
  hand-maintained alias/bridge maps. The carefully authored registry
  descriptions are served to **no one but MCP**, and the chat descriptions can
  drift from them silently.
- **Bootstrap duplication caused two production outages — and the bug class is
  LIVE, not just historical (GT-4).** `api/retrieval/capability/route.ts:103-135`
  maintains its own registration list separate from `catalog.ts`; D9
  `judgment_query` and D10 `pact_query` each 404'd in production because one list
  was updated and not the other. **Those two are fixed, but the same failure
  class is unfixed for 6 more capabilities today:** `getCatalog()` and
  `route.ts`'s bootstrap still disagree — D6-synergy (`synergy/pipeline`,
  `synergy/cross_layer`) and MARO/dprofiles (`maro/orchestrate`,
  `maro/mcp_surface`, `resource/maro/profiles`) are in `route.ts` but absent from
  `catalog.ts`; `synth_compose_large_n` is the reverse. R-1.3 must enumerate all
  6, not only D9/D10.
- **The Vidhi planning registry exists in three hand-synced copies** (two TS
  trees + a DB seed, migration 440); `capability_version.ts` hashes only one.
  **The drift has already begun (GT-56):** the two TS copies
  (`platform/src/lib/vidhi/registry_data.ts`,
  `platform-mcp/src/resources/vidhi/registry_data.ts`) have diverged on the
  type-import line (`'./types'` vs `'./types.js'`) **with no parity gate** — the
  triple-copy risk is materializing NOW, in the very floors R-3.3 will extend,
  not hypothetically. (The `cr_status.ts` copies are still byte-identical —
  uneven drift.)
- **The session-pin type is hand-mirrored** into `platform-mcp/src/lib/session.ts`
  (GT-7: not independently re-verified this pass; note the "session pin"
  construct itself is slated for D-16 restructuring — the mirror may be moot
  post-excision).
- Positive: the envelope mirror is **already codegen'd**
  (`platform-mcp/src/generated/envelope.ts`, sha-stamped, parity-tested) —
  the handoff's "hand-maintained mirror" claim is stale (GT-8,
  PLAN-ITEM-ALREADY-DONE). The codegen pattern works; it just covers only the
  envelope. **Caveat (GT-9):** the parity test (`r5_codegen_parity.test.ts`) is
  **not wired into CI** — platform-mcp's whole vitest suite is deliberately
  excluded, so drift is currently undetected despite the machinery existing.

### §1.2 The envelope is authored once, applied almost nowhere

- **3 authoring sites** feed the envelope (GT-10 corrects the "6 of 123
  handlers" framing, which conflated files with handlers):
  `synthesis/capability.ts`, `registry_bridge.ts`'s `envelope()` wrapper, and
  `register_p1_ganita.ts`'s wrapper feed a low-double-digit count of tools; 2
  more files import only `buildHonestPagination`. Adoption is a small minority
  either way. Only **3 tools default to v3** (`judgment_query`, `graha_portrait`,
  `pact_query`, GT-11 exact — `resolveEnvelopeFormat(... ?? 'v3')` at
  `registry_bridge.ts:1857/2422/2827`); everything else defaults legacy, and
  legacy has **no `chart_header`** — most of the estate serves a foreign LLM with
  no chart-frame anchor at all.
- `judgment_flags` is typed `string[]` but `register_d8_assess_domain.ts:595`
  emits **objects**; flags range from stable tokens to multi-sentence prose —
  a consumer cannot switch on them.
- `envelope_version` stays `'v1'` even under v3; consumers must sniff a
  second field.
- Cursors encode only `{offset}` — no filter/sort fingerprint; a cursor
  replayed under different facets silently paginates the wrong family.
- `density_contract`: **6 of ≈118** capabilities (~5%); the split is 3
  `empty_reason:false` / 3 `true` (GT-15), and only **2 of the 3** `false` carry
  a "not yet added" stub note (`get_yoga_dosha.ts:71`, `query_signals.ts:230`);
  the third (`register_d9_judgment.ts:418`) is a **deliberate design choice**
  (judgment_flags is its honest-gap channel), not an unfinished stub.
- **No `register` block exists** (A-18 unbuilt): raw envelopes leak
  `SIG.MSR.*`, `marsys://` URIs, and layer-coded tokens with zero
  plain-language mapping — and on the raw-tools path the envelope is the
  *entire* epistemic safety mechanism (handoff §7.2).
- Two incompatible clippers coexist: structure-aware `response_budget.ts`
  (40/25KB, honest trim receipts) vs byte-truncating `result_clipper.ts`
  (32KB, produces invalid JSON). **`result_clipper.ts` is NOT orphaned (GT-17):**
  it has a live caller — `adapters/bulk_context/bundler.ts:47`, on the
  bulk-context/hybrid path — and is a narrower-purpose LLM-context clipper
  (documented at `response_budget.ts:12`), not dead code. R-2's "evict
  result_clipper" must preserve this live consumer, not delete blind.
  `still_over_budget` is **dead output on every call path (GT-18/GT-45)** — even
  `finalizeMcpBudget` recomputes its own over-budget check independently rather
  than reading it; it is "read by nobody," not merely "unread by 4 callers."
  Unclamped surface is **~36 of ~115 tools across 15 of 21 registration files
  (GT-19/GT-48)**, materially bigger than "the reference tools" — the 7 `ref_*`
  tools are only the visible tip.

### §1.3 The planner is duplicated and mis-wired

- **Paripraśna does not use the Vidhi engine at all.** `consult/route.ts`
  runs `pipeline_planner` (its own `query_class` taxonomy) + a **hardcoded**
  B.11 floor injection at `route.ts:513-546`. GT-21: only **`pattern_register`
  is actually pushed live** (`route.ts:535`); `cluster_atlas` is a **dead
  constant** that lives only in the L2.5 detection membership list
  (`route.ts:520`) and `inferLayer`, never in a `.push()`. Both resolve to
  nothing in the registry. Read the injection as: "pushes the dead
  `pattern_register`; also carries dead `cluster_atlas`/`resonance_register` in
  its detection constants." The acharya floor / machine band / completeness
  receipt exists only for external MCP callers.
- **The DR-8 intent classifier's vocabulary has zero overlap with the Vidhi
  compiler's intents.** `scope_resolver.coerce` silently collapses every
  DR-8 intent to `general_synthesis`/`deepdive` (`scope_resolver.ts:70-72,
  100-109`) — the advertised `intent_classify → plan_retrieval` path **never
  selects a domain floor** (compiler selects floor by intent alone,
  `compiler.ts:105`, so the collapsed intent always hits the 6-item
  general_synthesis floor). CR-28 is worse than "three unreconciled
  implementations": there are three live taxonomies plus a dormant prompt, and
  the flagship handoff between two of them is a silent no-op.
- Domain floors are thin beyond wealth (career 12 / health 10 / marriage 9
  items vs wealth 26, GT-25 exact); 12 of 37 primitives are dark-by-construction
  with open CRs (GT-26 exact — CR-16/24/30/37/56/61/64/66/67/68/69/73);
  `cr_status.ts` is a frozen hand-authored snapshot with a self-flagged CR-55
  contradiction that is in fact **tri-state across three documents (GT-27)**:
  snapshot=CLOSED vs consumption-register-body=OPEN-ELEVATED vs the defect
  register's third reading ("appears fixed live"). A frozen snapshot cannot
  self-correct; the tri-state must be resolved during R-3.3's re-derivation.

### §1.4 Multi-LLM adaptation is scaffolded but inert

- `server.ts:287-304` **fetches the model-family surface spec and discards
  it** (`void effectiveFamily; void responseFormat` at 303-304). GT-29
  corrects the enforcement claim: `max_tools` **IS** enforced — but only for
  internal composite-bundle sub-tool fan-out (`bundle_adapters.ts`); it is
  never enforced on the **`tools/list` surface** a client sees (there is no
  `ListToolsRequestSchema` handler). Two distinct enforcement points — R-4.1
  must build the surface-list path and **not** rebuild the working fan-out
  path. It also reads a `response_format` field `McpSurfaceSpec` never contains.
- **No MCP tool annotations anywhere** (`readOnlyHint`/`idempotentHint`/…) —
  foreign LLMs must infer read-vs-write from prose (GT-30 exact: zero matches).
- `behavioral_overrides` (the per-family hook) is populated **once** in the
  entire codebase (`dprofiles_registration.ts:99`, GT-31); `drill_children` 11×;
  `output_schema` 4× (the latter two carried forward plan-stated, not
  re-verified this pass).
- **Description leakage is elevated-severity, not a hygiene footnote (GT-32):
  11 leak instances across 8 files, not 3.** Beyond the row-count leaks
  (66,738 / 27,554 / 5,566), `ephemeris_cache_native_lifetime.ts:24-29` embeds
  the **native's full name / DOB / birth-time / birthplace verbatim (full PII
  leak, GT-42)** in a served resource description, and `get_dashas.ts:123`
  embeds **601,443 rows — which both leaks AND disagrees with CLAUDE.md's
  canonical seal (chart_dashas=536,471, GT-43)**, i.e. leaked and apparently
  stale/wrong. The chart-agnostic gate scans only `description:` fields, so it
  misses the resource-description PII, empty_reason-string leaks (GT-54: d8's
  `TEMPORAL_EMPTY_REASON` leaks "native chart 0/13,364 dated on lahiri"), and
  these counts entirely. R-1.6's scan must widen well beyond `description:`.
- `listCapabilities` silently ignores the `archetype`/`tool_role`/
  `traversal_level` **and a fourth field, `scope` (GT-33)** — implementation
  (`registry/index.ts:52-61`) checks only `type`/`layer`/`name_prefix`.

### §1.5 Trust seams

- Dev-mode internal token check **fails open** (verified at
  `asset/route.ts:33-36`) — and this is a **13-file duplicated pattern (GT-34/
  GT-44), not a one-liner.** The fail-open fires when `MCP_INTERNAL_TOKEN` is
  unset AND `NODE_ENV==='development'`, replicated verbatim across 13+ route
  files. R-0.5's fix is therefore a multi-file patch (extract a shared
  `validateServiceToken`, or enumerate every site) — still simple, but **not
  the single-PR one-liner the plan previously framed.**
- `plan_retrieval` and the `vidhi_plan` prompt compile plans for **any
  chart_id with no entitlement check** (low disclosure, but a gap;
  `register_vidhi_plan.ts`/`plan_builder.ts` have zero `authorize`/`entitle`
  hits — the prompt path shares `plan_builder.ts` so the gap almost certainly
  applies, GT-35).
- `parity_check.ts` — **mechanism imprecise + may be DEAD CODE (GT-36):** a
  failed bridge import returns an empty `mcpUris` set, but in the normal
  populated context that makes every consume-URI land in `missing_in_mcp` → a
  **hard FAIL**, not an auto-pass (true auto-pass only in the degenerate
  both-empty case). More important: **no CI/test/script invokes
  `checkParity()`/`runParityCheck()`, no `parity_check.test.ts` exists, and a
  newer `scripts/manifest/parity_validator.ts` may be the live successor.**
  R-0.5 must first confirm the file is even in the enforcement path before
  "fixing" it.
- Per-chart entitlement on the dispatcher is solid (fail-closed, 30s cache),
  as is the chart-agnostic gate (7 rules + raw-file scan) — but note its scan
  surface (`description:` only) is narrower than the leak surface above
  (GT-42/GT-43/GT-54).

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
5. Safety patch (RE-SCOPED v1.3 — **multi-file, not a single one-liner PR**;
   still simple, no design): dev token fail-open → fail-closed — but this is a
   **13-file duplicated pattern (GT-44)**, so extract a shared
   `validateServiceToken` or enumerate all sites; entitlement check on
   `plan_retrieval`/`vidhi_plan` (GT-35); `parity_check` — **first confirm it
   is even in the enforcement path (GT-36: may be dead code with a live
   successor `parity_validator.ts`; it already hard-fails in the populated
   case)** before "fixing" its degenerate both-empty auto-pass. Should not wait
   for their phases.

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
   (a) chat tool defs — absorbing the **real served chat contract catalog
   (`TOOL_CONTRACTS` in `lib/contract/registry.ts` = 6 entries, GT-3)** and
   separately retiring/re-scoping the 76-row `ToolReconciliationEntry` audit
   table in `lib/contract/tool_metadata.ts` (which is NOT served — do not treat
   it as the chat surface); (b) MCP tool registrations —
   replacing the ~25 hand-written `server.tool` blocks in `registry_bridge.ts`
   and the alias files with a loop over compiled defs (handlers stay
   hand-written; *surfaces* are generated); (c) the vidhi primitive rows'
   tool bindings; (d) a machine-generated census (kills the hand-recounted
   `server.ts` comment); (e) a docs resource (`marsys://resource/catalog`)
   so any client can self-orient.
3. **One bootstrap.** `catalog.ts` becomes the only registration list;
   `api/retrieval/capability/route.ts` imports it. The class of D9/D10
   outages becomes impossible. **Must enumerate the 6 currently live-divergent
   capabilities (GT-40), not only D9/D10:** D6-synergy (`synergy/pipeline`,
   `synergy/cross_layer`), MARO/dprofiles (`maro/orchestrate`,
   `maro/mcp_surface`, `resource/maro/profiles`) present in `route.ts` but
   absent from `catalog.ts`, and `synth_compose_large_n` the reverse.
4. **Alias cutover** (A-02): delete the 41 live aliases + resolve the 6
   DEFERRED renames in one breaking release with
   `notifications/tools/list_changed`; `tool_name_bridge.ts` survives only
   for replaying persisted conversations.
5. **De-mirror by codegen** (extend the proven envelope pattern): vidhi
   registry (one TS source → generated MCP copy + DB seed), session-pin
   types, and — per A-01 — begin the `@marsys/contract` package as the
   long-term home. `capability_version` hashes the full compiled catalog,
   making the staleness kill actually cover all tools.
6. **Description hygiene (RE-SCOPED v1.3):** strip native row counts (extend
   `chart_agnostic_gate` with a native-cardinality rule); enforce length
   budgets per display field. **The scan must widen well beyond `description:`
   fields** — to resource descriptions (GT-42: full native PII —
   name/DOB/birth-time/birthplace — in `ephemeris_cache_native_lifetime.ts:24-29`)
   and `empty_reason` strings (GT-54: d8's `TEMPORAL_EMPTY_REASON`). Also
   **reconcile the `get_dashas.ts:123` 601,443 vs CLAUDE.md-seal 536,471
   discrepancy (GT-43)** — leaked AND apparently stale; flag for L1-seal
   cross-check.

**Gate:** one authored source; chat and MCP surfaces byte-derived from it;
CI parity (registry ↔ chat defs ↔ MCP tools/list ↔ census) green; aliases
gone; a grep for hand-authored tool descriptions outside the registry
returns zero.

### R-2 — One Envelope (the raw-tools path's entire defense)

1. **v3 becomes the only shape.** Every handler routes through
   `buildRetrievalEnvelope`; `envelope_version: 'v3'`; legacy served only
   behind an explicit `response_format:'legacy'` compat flag with a sunset.
   `chart_header` mandatory on every per-chart response (fail-loud
   `judgment_flag` if unresolvable, never silently null). **GT-47 makes this
   concrete: `chart_header` currently fails silently with no flag in two
   layers** — inner (`chart_header.ts:90-93` swallows DB errors, fields stay
   null) and outer (3 `registry_bridge.ts` call sites catch→null) —
   contradicting the §N.6 honesty discipline the same files apply elsewhere.
   Both silent paths must be made fail-loud.
2. **Close the flag vocabulary.** `judgment_flags` becomes
   `{code, detail?, severity?}[]` with a closed, registry-checked code enum
   (a CI census of emitters already exists in audit form); the d8 object
   emission and prose-sentence flags migrate into `code+detail`. Ship a
   compat shim during transition. **Must also fold in (v1.3): the two handler
   files emitting static `judgment_flags: []`** (`register_p1_synthesis.ts:82`,
   `register_p1_reference.ts:87`, GT-46 — field present, no honest-gap
   machinery at all, worse than the `empty_reason:false` "not yet" gap) **and
   the cross-cutting `finalizeMcpBudget` emitter** that injects
   `response_still_over_<N>kb_budget_after_full_trim` into whatever
   `judgment_flags` field the caller names (GT-53) — both must land inside the
   closed enum, not outside it.
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
   (which alone reads the true ceiling); bare `applyResponseBudget` callers and
   the **~36-of-~115 unclamped tools across 15 registration files (GT-48 — far
   more than "the reference tools")** migrated; `still_over_budget` is **dead
   output on every path (GT-45)** — either wire it into the closed enum or
   delete it, do not merely "surface" it. **`result_clipper.ts` is NOT orphaned
   (GT-17): preserve its live bulk-context caller**
   (`adapters/bulk_context/bundler.ts:47`) — it is a narrower-purpose
   LLM-context clipper, not dead code, so scope this as "keep it off the
   retrieval envelope path" rather than "evict/delete." `density_contract`
   populated for all ≈118 (mandatory per R-1), with `empty_reason` actually
   implemented where declared.
6. Fix the stale provenance semantics (`build_id` doc → `build_runs`;
   `salience_formula_ver` either wired or removed).

**Gate:** every capability in the codegen-derived census (≈118, not a
hand-counted 123 — GT-1) emits v3 with header, grades, coverage,
register labels, and budget discipline; a schema validator over live
`tools/call` output for the full surface passes; W4-style rubric battery
re-run confirms no answer-quality regression.

### R-3 — One Planner (Vidhi everywhere, taxonomies unified)

1. **One decomposed scope tuple (RE-SCOPED v1.3, GT-24 — the single biggest
   plan correction).** The v1.2 design assumed the three intent taxonomies
   (DR-8 vocab, Vidhi compiler `IntentClass`, `pipeline_planner` `query_class`)
   were three dialects of one vocabulary that a **flat superset-rename enum**
   could unify. Lane C's structural finding refutes this: they are **three
   orthogonal axes, not three dialects** — DR-8 is technique+domain (domain
   lives *outside* its intent field), Vidhi `IntentClass` fuses domain×depth
   into one token, and `query_class` is an epistemic answer-mode. A flat
   superset enum **cannot** faithfully unify them. The correct construct is a
   **decomposed scope tuple**:

   ```
   { answer_mode × domain × depth × horizon  (× intervention × entitlement) }
   ```

   with `IntentClass` **derived** from `(domain × depth)` at compile time, not
   stored as a peer enum. `classifyScope`, `scope_resolver`, and
   `pipeline_planner` all emit/consume the decomposed tuple; the compiler
   derives its `IntentClass` (and thus the domain floor) from the tuple's
   `domain`+`depth` axes rather than from a collapsed single token; `coerce`
   fails loud (`scope_unresolved` flag) instead of silently collapsing to
   `general_synthesis`/`deepdive`. This is a real re-scoping of R-3's build
   surface — the deliverable is a tuple algebra + a derivation function, not a
   rename map. This closes CR-28 fully.
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
   re-generated at every subsequent phase gate. **Methodology correction
   (v1.3, GT-51): the census-generation rubric run MUST grep all three serving
   paths — `lib/retrieval/`, `register_p1_*`, and `brahma/*` — not a single
   directory.** The prior census grepped only `platform/src/lib/retrieval/` and
   thereby **false-dark-misclassified** `bg_dignity_reference`, `bg_sign_medical`,
   and `chart_panchanga` (they are in fact SERVED via the other two paths). A
   single-directory grep repeats this error.
2. **Coverage doctrine enforcement** (strategy §5.2): every table becomes
   SERVED / INTERNAL-BY-DESIGN (declared) / RETIRED. **Baseline correction
   (v1.3, GT-51): the L0 stratum is ~39 physical tables, NOT 13** — the "13
   tables" figure was an undercount from the single-directory census error
   above; the census baseline is re-set to the ~39 physical L0 tables. **Split
   "dark-unbuilt" from "dark-unwired" (GT-49) and from "retire" (GT-52):**
   - **Dark-unwired (quick wins, wiring only, no build):** `kala_timeline` is
     **built-but-unwired (GT-49)** — a complete handler
     (`platform-mcp/src/tools/kala_timeline.ts`, `registerKalaTimeline`) that is
     simply **never imported into `server.ts`** (one-line wiring fix; do not
     mis-group it with build items).
   - **Dark SERVICE, high priority (GT-50):** `ka_graha_sancara`
     (arbitrary-datetime ephemeris) is a **live in-code dark service** —
     `call_service_wrappers.ts:200-208` returns "not yet wired to a compute
     sidecar endpoint," which **blocks ALL date-parameterized "positions at
     time T" retrieval.** Named nowhere in the prior plan or strategy; take its
     disposition (wire the sidecar endpoint) as a **high-priority** R-1.5 item.
   - **RETIRE, not wire-up (GT-52):** the 5 `reference_*` tables
     (aspects/signs/planets/nakshatras/vargas) are **dead-superseded by served
     `bg_*` equivalents** — RETIRE candidates, not wire-up candidates.
     Conflating them would wire up dead tables. (Note: `chart_panchanga`,
     `bg_dignity_reference`, `bg_sign_medical` were false-dark and are already
     SERVED — do not re-wire.)
   - **Substantive dark set to wire, priority order:**
     `bodha_rm_dasha_windowed_prescriptions` (time-targeted remedies), CDLM
     rollup tiers (`domain_rollups`/`evolution_gradients`/`pattern_clusters`),
     `bodha_triangulation` + `bodha_cgm_sub_graphs`, the served portion of the
     L0 `bg_*` catalog stratum, `chart_ayanamsha_reports`, and the four
     substantive mimamsa read candidates (`signal_adjustment`,
     `manifestation_sets`, `discoveries`, `insight_embeddings`).
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

### §8.5 — Paripraśna-alignment contradictions (v1.3 — RAISED, not resolved)

The six-lane audit's Lane F cross-checked this plan against the settled
Paripraśna target architecture (`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`) and
surfaced six architectural conflicts. Per the reconciliation brief's
"raised, not resolved" discipline (§D.4 / handoff §8 rule 8) these are **open
ruling items for the native — this plan does not adjudicate them.** Full
statements: `GROUND_TRUTH_REGISTER.md` Part C and `LANE_F_REPORT.md` §3.

- **C-1 (CONTRADICTED) — `prashna_ask`'s plan contract carries a `depth` param
  D-15 forbids.** R-5.1's contract `{chart_id, question, scope_tuple?, depth,
  response_format}` includes `depth`, but D-15/§13.4 removed `depth` and `tier`
  from the engine signature and `scope_tuple?` already derives depth — making
  `depth` both forbidden and redundant. Cheap to fix now (tool unbuilt, paper
  only). → `PARIPRASHNA §1/D-15, §13.4`; `LANE_F_REPORT.md §3`.
- **C-2 (CONTRADICTED by omission) — R-3.2's `consult/route.ts` edit leaves a
  live D-15 `audience_tier` violation un-excised.** R-3.2 rewrites the exact
  `consult/route.ts` block that carries a live `audience_tier` stamp
  (`route.ts:459`, `:616`) without excising it; excision is assigned to a
  different workstream (PARIPRASHNA P2'). The floor mechanism itself is
  D-15/D-16-safe — the hazard is omission: the floor could land D-15-dirty. →
  `PARIPRASHNA §13.7, §16.1/F-25g`; `LANE_F_REPORT.md §3`.
- **C-3 (UNDER-SPECIFIED) — cited signal *content* is still internal-register
  text.** The plan supplies token labels (R-2.3a) but not reader-facing signal
  *prose*; `bodha_msr_signals` has no reader-facing column (only
  `signal_summary_text`/`signal_headline_text`, machine-internal), so the
  `signal_reader_text` editorial pass (PARIPRASHNA P5') sits in no plan phase.
  → `PARIPRASHNA §13.6, §16.6`; `LANE_F_REPORT.md §3`.
- **C-4 (CONTRADICTED, potential) — the `verbosity: concise|detailed` knob
  (§7.6) vs D-15 "never a parameter of the ask."** The plan/industry-consult
  frames it as orthogonal token-length control; D-15 warns a per-call knob that
  thins the reading is "a depth axis wearing a token-budget costume." →
  `PARIPRASHNA §13.4 final para`; `LANE_F_REPORT.md §3`.
- **C-5 (UNDER-SPECIFIED) — R-3's unified planner preserves two outcomes; the
  rebuild needs three.** R-3 emits `PlanReceipt | fault`; A-29/§6.6 requires a
  third outcome `ClarificationRequest` + a pre-plan ledger check (§14.7's
  "strongest compliance-decay mitigation"). The outcome set is a plan-algebra
  decision (R-3's scope), even if the clarification UX is not. → `PARIPRASHNA
  §6.6, A-29, §9.5`; `LANE_F_REPORT.md §3`.
- **C-6 (SEQUENCING TENSION) — the load-bearing consumer contract
  (`prashna_ask`) is sequenced last (R-5).** PARIPRASHNA T-2 makes it a *core
  bet*; §19.1 fault 1 is "the core bet was validated last." A thin `prashna_ask`
  spike earlier would de-risk the headless-engine boundary (F-R1) the plan
  depends on but does not own. → `PARIPRASHNA §18/T-2, §6.4.1, §19.1`;
  `LANE_F_REPORT.md §3`.

*(Two further Lane F under-specified plane items also deserve native
attention: **F-R1** — headless-engine callability, consumed by R-5 but
built/owned by neither workstream with a cross-cite; **F-R7** —
`calibration_context_only` NO-LEAKAGE exclusion from projections/`prashna_ask`
tool set + a CI canary. See `GROUND_TRUTH_REGISTER.md` Part C tail.)*

---

## §9 — Consolidated tracking register (v1.4 — the implementation-opening checklist)

Native directive 2026-07-19: **no implementation now.** Every open item —
including safety findings — is tracked here and executed inside the
Retrieval Plane Elevation implementation campaign. This section is the
campaign's opening checklist; R-0 begins by walking it.

### §9.1 Safety items (deferred by explicit native decision — first work in R-0.5)

| # | Item | Source | Lands in |
|---|---|---|---|
| S-1 | **Native PII in a served tool/resource description** — remove; extend the chart-agnostic gate to resource descriptions | GT-42 (Lane D) | R-0.5 → R-1.6 hygiene scan (elevated to first commit of implementation) |
| S-2 | Fail-open dev-token pattern duplicated across **13 files** — fail-closed everywhere, single shared guard | GT-44 | R-0.5 (re-scoped from "one-liner") |
| S-3 | Entitlement check on `plan_retrieval` / `vidhi_plan` | plan §1.5 (confirmed) | R-0.5 |
| S-4 | `parity_check` — confirm live/dead status first, then hard-fail-on-import-failure or delete | GT-36 | R-0.5 |
| S-5 | Native row counts + native-derived cardinalities in descriptions (11 instances / 8 files) + `empty_reason` strings + the 601,443 vs 536,471 discrepancy | GT-43, GT-F11 | R-1.6 |

### §9.2 Paripraśna alignment rulings — RULED by native 2026-07-19

| ID | Ruling | Disposition → plan change |
|---|---|---|
| C-1 | **ACCEPTED.** Drop `depth` from the `prashna_ask` contract (D-15); `scope_tuple` derives it | R-5.1 signature = `{chart_id, question, scope_tuple?, response_format}` |
| C-2 | **ACCEPTED.** Excision of the live `audience_tier` stamp (`consult/route.ts:459,:616`) is an explicit PRECONDITION of R-3.2, coordinated with PARIPRASHNA P2′ under a single named owner | R-3.2 precondition row |
| C-3 | **ACCEPTED.** Reader-facing signal prose (`signal_reader_text` editorial pass) added as a dependency-flagged R-2 row, bridged to PARIPRASHNA P5′; R-2.3 envelope honesty is incomplete without it | new R-2.7 |
| C-4 | **KEEP-WITH-GUARD.** The `verbosity` knob survives with a hard D-15 guard: it may shorten evidence arrays ONLY — never remove floor items, verdict content, or dissent-quota rows. Guard text ships in the descriptor + CI check | §7.6 amended |
| C-5 | **ACCEPTED.** Planner outcome set becomes `PlanReceipt | ClarificationRequest | fault` + pre-plan ledger check (A-29/§14.7) | R-3.1 |
| C-6 | **ACCEPTED.** Thin `prashna_ask` spike (question → headless engine → synthesized answer; no transport polish) added as an R-3 EXIT-GATE item; full contract stays in R-5 | R-3 gate |
| F-R1 | **ACCEPTED.** Headless-engine callability gets joint ownership: cross-cited deliverable in this plan (R-3 gate spike) and PARIPRASHNA §6.4.1; neither ships without the other signing | R-3/R-5 cross-cite |
| F-R7 | **ACCEPTED.** NO-LEAKAGE arms 2 & 4: `calibration_context_only` flag on the descriptor (R-1.1), excluded from ALL projections and the `prashna_ask` tool set (R-4), + CI canary | R-1.1 / R-4 / battery |

### §9.3 Ambiguity dispositions — RULED by native 2026-07-19

| ID | Disposition |
|---|---|
| AMBIG-1/2 | No grep count is an invariant. The census is codegen/AST-derived (R-1.2d); until it lands, the live MCP tool count is treated as UNKNOWN ±30 and never cited as a fact. |
| AMBIG-3 | The "4 retired aliases" claim is DELETED from R-1.4 (unverifiable; no retire ledger). R-1.4 scope = 55 live aliases + 6 DEFERRED, recounted by the census at execution. |
| AMBIG-4 | **AUTHORIZED:** correct `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §6.1 (stale `depth` param + "session pin" naming) at source — a docs task at implementation open, so C-1/F-R4 are not re-inherited. |

### §9.4 Audit-derived work items folded into phases (from GT-40..GT-56 + Part D)

| # | Item | GT | Lands in |
|---|---|---|---|
| W-1 | Bootstrap divergence is LIVE for 6 capabilities (D6/MARO/synth: `getCatalog()` 118 vs `route.ts` 122) — single bootstrap closes it | GT-40 | R-1.3 |
| W-2 | Alias cutover recount: **55 live** (not 41/45) + 6 DEFERRED | GT-F09 | R-1.4 |
| W-3 | Projection compiler consumes the **6-row** served chat catalog (not the 76-row audit table) | GT-3 | R-1.2 |
| W-4 | `registry_data.ts` twin copies ALREADY DRIFTED, no parity gate — codegen de-mirror is urgent, not preventive | GT-56 | R-1.5 |
| W-5 | `still_over_budget` dead on EVERY path — enforce via the single finalize entry point | GT-45 | R-2.5 |
| W-6 | Two handlers emit static hollow `judgment_flags: []` — fold into the closed-enum migration | GT-46 | R-2.2 |
| W-7 | `finalizeMcpBudget` cross-cutting flag joins the flag enum | GT-53 | R-2.2 |
| W-8 | ~36 unclamped tools migrate to the budget path; `result_clipper` has a LIVE bulk-context caller — preserve that consumer, evict from the MCP path only | GT-48, GT-17 | R-2.5 |
| W-9 | Two silent chart_header-null paths made fail-loud | GT-47 | R-2.1 |
| W-10 | R-3.1 re-scope stands: DECOMPOSED scope tuple (three orthogonal axes, `IntentClass` derived) — not a flat superset enum | GT-24 | R-3.1 |
| W-11 | CR-55 tri-state resolved during cr_status re-derivation | GT-F20 | R-3.3 |
| W-12 | `max_tools`: build the `tools/list` enforcement path; reuse the working bundle-fan-out enforcement; add `response_format` to `McpSurfaceSpec` or delete the dead read | GT-29, Lane D | R-4.1 |
| W-13 | `listCapabilities` ignores FOUR filter fields (incl. `scope`) | GT-33 | R-4.4 |
| W-14 | Census harness greps ALL THREE serving paths (avoids false-dark) | GT-51 | R-1.5 census |
| W-15 | L0 inventory is ~39 tables; disposition split: `chart_panchanga`/`bg_dignity_reference`/`bg_sign_medical` are SERVED (correct the strategy §5.2 list); 5 `reference_*` = RETIRE; `kala_timeline` = one-line UNWIRE fix (dark-unwired, not dark-unbuilt) | GT-49..52 | R-1.5 |
| W-16 | **`ka_graha_sancara` dark service blocks ALL date-parameterized queries** — highest-impact single coverage item | GT-50 | R-1.5 (top of dark-set priority) |
| W-17 | Session-pin naming: rename to provenance stamp per D-16; drop mutable-session framing | GT-F28 | R-5.2 |
| W-18 | DB row counts UNVERIFIABLE without DSN — implementation environment provisions a read-only DSN so the census can verify | Lane E | R-1.5 precondition |
| W-19 | PARIPRASHNA §6.1 diagram fix (per AMBIG-4 authorization) | AMBIG-4 | R-0 docs task |
| W-20 | **Concept Reachability Matrix** — build-time compiled artifact: every data-plane CONCEPT (table, `chart_facts` fact_category, signal family, service endpoint) × its serving capability × its umbrella drill-path (≤2 hops) × the Vidhi primitive that names it. Three-way guarantee: SERVED (coverage) + NAVIGABLE (drill crawl reaches it, zero dead ends) + PLANNER-KNOWN (a floor/primitive references it — kills the LCA-19 "served but planner-blind" failure mode). CI gate: automated drill-pointer crawl + matrix completeness check on every merge; planner compiler consumes the matrix as input | native directive 2026-07-19 | R-1.5 (build) · R-3 (planner consumption) · R-4 battery (crawl gate) |
| W-21 | Census granularity = CONCEPT not table: enumerate `chart_facts` fact_categories (and signal-family / service-endpoint equivalents) as first-class census rows — table-level coverage under-counts L1 by design | native directive 2026-07-19 | R-1.5 census |
| W-22 | **Provider Concept Manifest — the "declared" side W-20 needs and today lacks.** Every asset and service declares its concept inventory machine-readably: a structured `emits` declaration (jsonb on `asset_registry`, NOT a WriterBase change — the orchestrator contract stays FROZEN) listing the fact_categories / signal_type_classes / windows an asset owns (replacing count_sql-WHERE-string archaeology); a signal-class registry for the bodha/kala/phala plane (none exists — dead classes like `functional_lordship_link` persist unnoticed); service manifests completing `provides_apis`/`health_probe` for ALL sidecar routers (~12 routers, only 2 probed today) with the FastAPI route surface committed, not runtime-only. Existing surfaces are consumed, not duplicated: asset_registry, CHART_FACTS_SCHEMA.json, coverage_matrix.ts, vidhi registry, CAPABILITY_MANIFEST | provider audit 2026-07-19 | R-1 (registry columns) · R-1.5 (population + probes) |
| W-24 | **Concept-ledger infrastructure** (§9.6-1): the single writable `concept_ledger` + projection generators for every downstream surface + the hardcoded-list lint | §9.6 | R-1 |
| W-25 | **Harvest pipeline + adjudication queue** (§9.6-2): extractors E1–E4, cross-diff, exception queue as R-1.5's core deliverable — replaces hand-authored backfill of ~106 assets | §9.6 | R-1.5 |
| W-26 | **Lifecycle states + three-horizon drift detection** (§9.6-3/4): transition predicates, post-build verifier (outside the FROZEN orchestrator), ledger_version in pin + envelope, dead-concept auto-queue | §9.6 | R-1.5 · R-2 (envelope field) · R-4 (probes) |
| W-27 | **Asset commissioning contract** (§9.6-5): the CI-enforced Definition-of-Done bundle for every new/elevated asset | §9.6 | R-1 CI, binds all future layers |
| W-28 | **Deterministic response cache + plan precompilation** (§9.7): envelope cache keyed on (uri, chart_id, build_id, ledger_version, args, projection, format), invalidated by build events; Vidhi floors precompiled per intent×depth, keyed by capability_version | §9.7 | R-2 (cache-safe envelopes) · R-3 (precompile) · R-4 (edge cache) |
| W-29 | **Concurrency capacity**: funnel horizontal scale + chart_header N+1 batching; DB pooling/read replicas + per-tool query budgets; sidecar memoization + per-engine concurrency caps | §9.7 | R-4 · R-5.3 (load test widened to these four points) |
| W-30 | **QoS + backpressure**: priority classes (interactive > background), per-principal fairness, prashna_ask job queue with backpressure (feeds the OT-2 ruling), and the honest-degradation rule — queue/refuse, never thin quality | §9.7 | R-4 · R-5 |
| W-31 | **Quality-under-load proof**: SLOs per query class, per-query cost ledger, battery executed at concurrency in CI as a regression gate | §9.7 | R-4 battery · R-5.3 |
| W-23 | **Enumeration reconciliation + hard gates.** Reconcile the three chart_facts category enumerations (SCHEMA.json 147 · coverage_matrix.ts 158 · planner spec "37" prose) into ONE generated source consumed by all three consumers; reconcile asset_registry row-count truth (39/92/106); upgrade today's soft audits to matrix gates — `check_a3_categories` declared-vs-populated from LOW/informational to hard, coverage_matrix R3 gate extended beyond chart_facts to the signal plane, handler facet lists (e.g. `AV_CATEGORIES`) generated from the manifest not hardcoded | provider audit 2026-07-19 | R-1.5 · R-4 CI |

### §9.5 Standing rulings queue (unchanged, for R-0)

OT-7 · OT-10 · OT-2 · OT-5 · OT-6 · RC-1 · RC-2 · RC-3 · RS-1 · RS-2 · RS-3
(RS-4 already RULED + executed 2026-07-19; C-1..C-6 + F-R1/F-R7 + AMBIG-1..4
now RULED per §9.2/§9.3.)

---

*End of RETRIEVAL_PLANE_ELEVATION_PLAN v1.8 (2026-07-19 — §9.7 scale/QoS
doctrine + W-28..W-31. Prior v1.7: §9.6 Concept Spine
architecture: derivation-first reconciliation + lifecycle states + three-
horizon freshness + commissioning contract; W-24..W-27 added. Prior v1.6:
W-20 grounded by the provider-side audit; W-22 Provider Concept Manifest +
W-23 enumeration reconciliation added. Prior v1.5: reachability
doctrine W-20/W-21 added per native directive. Prior v1.4: native
adjudication: C-1..C-6, F-R1/F-R7, AMBIG-1..4 all RULED into §9; safety
items tracked in §9.1 for execution at implementation open, per native
decision no standalone hotfix. Remaining rulings for R-0: OT-7, OT-10,
OT-2, OT-5, OT-6, RC-1, RC-2, RC-3, RS-1, RS-2, RS-3, plus assent to the
§0 reframing and R-0 §5 sequencing.)*
