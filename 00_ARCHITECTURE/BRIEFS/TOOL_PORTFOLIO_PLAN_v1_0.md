---
canonical_id: TOOL_PORTFOLIO_PLAN
version: 1.0
status: DRAFT — FOR NATIVE REVIEW
date: 2026-05-27
author: Cowork planning session (no implementation; plan only)
scope: MCP/LLM tooling portfolio — structure, reconciliation, dynamic loading
related:
  - platform-mcp/src/server.ts
  - platform-mcp/src/tools/catalog.ts
  - platform-mcp/src/tools/tier_catalog.ts
  - platform/src/lib/mcp/primitives_registry.ts
  - platform/src/lib/retrieve/index.ts
  - 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
note: >
  This is a STRATEGIC PLAN, not an implementation brief. It records the target
  structure and the per-tool reconciliation verdicts for native review. Executor
  briefs (paste-ready, per-phase) are cut only after this plan is approved.
---

# Tool Portfolio Reconciliation — Strategic Plan v1.0

## §0 — Purpose

Turn the current accreted tool surface into a coherent **tooling portfolio** that
an LLM (optimized for Anthropic/Claude clients) can navigate without trial-and-error,
and that stays coherent over time. This plan covers: the vocabulary, the portfolio
structure, what gets built into every tool, the dynamic-loading mechanism, the
elimination of tiers, the per-tool reconciliation verdicts, and the phased sequence.

Decisions already locked with the native:
- **Full reconcile** — merge / split / delete / promote / fold as needed.
- **Tiers ripped out entirely** — filtering AND all tier metadata/annotation logic.
- **Dynamic loading: both** — gateway baseline now, protocol-native `listChanged` later.
- **Sequencing: industry best practice, Anthropic-optimized** — manifest spine first.

---

## §1 — The problem: four inventories that disagree

The root cause of "tools randomly popping up with no strategy" is that four separate
inventories exist and none agrees with the others:

| Inventory | Where | Count |
|---|---|---|
| Retrieval **engines** (real data-access logic) | `platform/src/lib/retrieve/` | ~55 |
| MCP **primitive whitelist** (dispatchable) | `primitives_registry.ts` | ~33 names (+ alias dupes) |
| MCP **registered tools** (what the LLM sees) | `platform-mcp/src/server.ts` | 40 |
| Tool **catalog** (lint/description list) | `catalog.ts` | "57" |

Four confirmed pathologies follow from this:

1. **True redundancy.** `query_signals` and `msr_sql` are two MCP tools pointing at
   the *same* engine (`msr_sql`). The LLM must choose between two doors to one room.
2. **Alias cruft.** The whitelist carries both MCP-names and engine-names for the same
   capability (`query_varshphal` + `query_varshaphala`, etc.); `msr_sql` appears twice
   in the `SURGICAL_TOOLS` array. Pure drift residue from the UDA/TR waves.
3. **Stubs/empty tools registered as functional.** `query_jaimini_drishti` is a sidecar
   stub (`not_implemented`); `get_cgm_subgraph`, `timeline_query`, `query_signal_state`
   are healthy code over **empty data tables**. The LLM can't tell these from working tools.
4. **Parity gap.** ~15 retrieval engines exist but have **no MCP tool** — real capability
   built for the portal channel but invisible to the LLM (see §6 disposition).

---

## §2 — Vocabulary: one source of truth (reconcile registry / manifest / catalog / tier)

Today four words name overlapping things and they have drifted. The fix is to make
three of them **derive from one**, and delete the fourth.

- **Manifest** — the single declarative source of truth. One entry per tool: identity,
  input schema, output shape, description, family, role, annotations, data-dependency.
  The *only* hand-edited artifact. Nothing is "true" about a tool unless it is here.
- **Registry** — runtime/operational state only (enabled, healthy, version, data-coverage).
  Keyed to the manifest. Answers "is it live right now?", never "does it exist?".
- **Catalog** — the presentation surface shown to the LLM (descriptions + grouping +
  ordering). **Generated from the manifest**, never hand-maintained. This is what
  permanently kills the 40/57/33 drift.
- **Tier** — **eliminated** (see §3).

Rule: **manifest declares → registry tracks liveness → catalog is rendered → tiers gone.**
One thing to edit, two derived, one deleted.

---

## §3 — Tier elimination (clean cut)

Per native decision, tiers come out entirely in this pass — both jobs they were doing:

- **Access filtering** — remove `getCatalogForTier` filtering, `OPS_TOOLS` / `SYNTHESIS_TOOLS`
  gating in `tier_catalog.ts`. Every authenticated caller sees the identical portfolio.
- **Presentation flavoring** — remove the acharya/super_admin description-suffix annotation
  logic and the `audience_tier`-conditioned house-rules coupling at the tool layer.
- **URL-key tier restriction** — decouple from tier (re-evaluate as a pure security control,
  not a tier control).

The `client / acharya / super_admin` axis is deleted from the tool-access path. (Deeper
audience-tier coupling elsewhere in the platform is the native's separate later cleanup.)

---

## §4 — The portfolio structure (framework)

### 4.1 Two classification axes (carried in the manifest)

**Axis 1 — Family (domain-meaningful grouping; the LLM navigates by this).** Tools are
grouped by the *kind of question they answer*, in the order a practitioner works:

1. **Foundation** — whole-chart L1 facts (rasi + vargas, dignity, shadbala, avastha).
2. **Holistic Synthesis** — L2.5 interpretive heart (MSR / UCN / CDLM / CGM / RM).
3. **Discovery** — L3.5 emergent structures (patterns, resonances, clusters, contradictions).
4. **Time & Prediction** — dasha / ephemeris / transit / timeline / signal-state.
5. **Electional (Muhurta)** — panchanga, muhurta, tara/chandra bala.
6. **System Lenses** — KP, Jaimini, Tajaka darshanas over the same chart.
7. **Tradition & Adjudication** — classical texts, multi-school convergence, remedies.
8. **Ground-truth & Substrate** — LEL, vector search, raw asset reads, domain reports.
9. **Governance / Meta** (non-astrological) — observability, health, writes.

**Axis 2 — Role (what the tool mechanically is; a fixed 5-value vocabulary):**
*entry-point/composite*, *primitive*, *raw-read*, *write*, *meta*.

Plus three lightweight per-tool attributes used by both the LLM and the system:
**access** (read-only vs write; idempotent vs not), **breadth/cost** (cheap-narrow vs
expensive-broad), **data-dependency** (which table/asset/engine — enables "functional vs stub").

### 4.2 The governing law

**No two tools may occupy the same intent slot.** Redundancy is resolved by merging (one
tool + a discriminating parameter) or by a razor-sharp non-overlapping disambiguator —
never left as two near-identical options.

### 4.3 What gets built into every tool (the contract, lint-enforced)

1. **Disambiguator-first description** in a fixed template: one-line "right tool when…" →
   what it does/returns → explicit *when to prefer / when NOT* pointers to sibling tools →
   input contract with ≥1 example → output-shape preview → cost/latency expectation.
2. **MCP annotations** — `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
3. **Token-efficient, shape-controlled responses** — `response_format` (concise|detailed) +
   sane pagination/truncation defaults.
4. **Structured, actionable errors** — class + remediation + retry hint.
5. **Uniform response envelope** across all tools (ok / trace_id / result / epistemics /
   citations / error).
6. **Self-reported data-dependency** so the registry distinguishes functional from stub/empty.

### 4.4 Annotation matrix (applied)

| Group | readOnly | destructive | idempotent | openWorld |
|---|---|---|---|---|
| All retrieval / raw-read / observability / health tools | true | false | true | false |
| `log_prediction`, `flag_disagreement` | false | false | false | false |
| `record_outcome` | false | false | true | false |

(Single closed corpus, single chart → `openWorldHint: false` everywhere.)

---

## §5 — Dynamic tool loading (both mechanisms)

**Finding (investigated 2026-05-27):** dynamic loading is **not available today** but is a
*build*, not a blocker. SDK `@modelcontextprotocol/sdk` **1.29.0** fully supports it
(`tools.listChanged: true`; `registerTool` handles expose `.enable/.disable/.update/.remove`,
each calling `sendToolListChanged()`). The blocker is the **deliberately stateless server**
(`sessionIdGenerator: undefined`; a fresh `McpServer` with all 40 tools per POST; `GET /mcp`
returns 405). Cloud Run (min-instances 1, concurrency 80, horizontal scale) makes stateful
sessions need sticky routing or externalized session state.

### 5.1 Gateway baseline (now) — Anthropic-optimal, stateless-safe

Aligned with Anthropic's "tool search / code execution with MCP" direction. Keep the server
stateless. Advertise a **small resident core**: the family entry-points + the universally-needed
reads + writes + meta + two gateway tools:
- `search_tools(query | family)` → returns matching tool **manifests** (name, description,
  schema, family) from the manifest substrate.
- `invoke_tool(name, params)` → generic dispatcher to the full reconciled set.

The full set lives behind the gateway; the LLM discovers on demand and invokes. No Cloud Run
rework, no client `listChanged` dependency, works on every host. This is why the manifest
(the data `search_tools` reads) must exist first.

### 5.2 Protocol-native listChanged (later) — enhancement layer

For hosts that honor it: make sessions stateful (`sessionIdGenerator: randomUUID()` + SSE
notification channel on `GET /mcp` + externalized session store, e.g. Memorystore, for
Cloud Run). Register the core at attach; `.enable()` a family's tools on a discovery trigger;
push `notifications/tools/list_changed`; client re-fetches `tools/list`. Layered on top of the
gateway baseline, not a replacement.

---

## §6 — Per-tool reconciliation disposition (PROPOSED — confirm)

Verdicts: **KEEP** (sharp + functional) · **MERGE** (redundant → one parameterized tool) ·
**SPLIT** · **PROMOTE** (engine exists, no MCP tool → expose) · **DE-REGISTER** (stub/dead) ·
**FOLD** (absorb into a broader tool as a param/recipe) · **DEDUP** (alias cruft) ·
**BACKFILL** (registered but empty data).

### Foundation
| Tool / engine | Verdict | Note |
|---|---|---|
| `chart_summary` | KEEP (entry-point) | canonical wide fact bundle |
| `query_chart_facts` | KEEP (primitive) | the workhorse |
| `query_divisional_chart` | KEEP | general varga reader; absorbs the D-specific tools below |
| `query_dasamsha_career` (D10) | FOLD → divisional (recipe/param) | |
| `query_shashtiamsha` (D60) | FOLD → divisional | |
| `query_drekkana_drishti` (D3) | FOLD → divisional / Jaimini | |
| `cross_varga_dignity_query` | FOLD → Foundation | |
| `get_shadbala_full` | PROMOTE | engine exists, no MCP tool |
| `get_planet_avastha` | PROMOTE | engine exists, no MCP tool |

### Holistic Synthesis
| Tool / engine | Verdict | Note |
|---|---|---|
| `holistic_bundle` | KEEP (entry-point) | |
| `query_signals` + `msr_sql` | **MERGE → one MSR-signal tool** | confirmed same engine |
| `query_ucn_walk` + `query_cdlm_lookup` + `query_rm_walk` | **MERGE → `synthesis_walk(layer:)`** | 3 → 1 |
| `get_cgm_subgraph` | KEEP + **BACKFILL** | CGM graph table empty |
| `query_msr_aggregate` | PROMOTE or FOLD | MSR stats |

### Discovery
| Tool / engine | Verdict | Note |
|---|---|---|
| `pattern_register` + `resonance_register` + `cluster_atlas` + `contradiction_register` | **MERGE → `discovery_register(kind:)`** | 4 → 1; identical shape — cleanest merge |

### Time & Prediction
| Tool / engine | Verdict | Note |
|---|---|---|
| `query_dasha_periods` | KEEP | SQL schedule |
| `query_ephemeris` + `temporal` | RECONCILE (merge under `mode`, or keep + razor disambiguator) | positional-SQL vs live-sidecar |
| `query_transit_event` | KEEP | event search |
| `query_transits_over_natal` | PROMOTE | high-value; "transits hitting MY chart" — currently invisible |
| `query_yogas_active_now` | PROMOTE | |
| `query_planetary_period_predictions` | PROMOTE | |
| `query_eclipse_transits` | PROMOTE | |
| `query_planet_war` | PROMOTE | |
| `timeline_query` | KEEP + **BACKFILL** | L5 timeline empty |
| `query_signal_state` | KEEP + **BACKFILL** | signal_states empty |
| `interpret_current_dasha` | → **prompt template**, not a tool | composition recipe |

### Electional (Muhurta)
| Tool / engine | Verdict | Note |
|---|---|---|
| `query_panchanga` | KEEP | |
| `muhurta_finder` (`query_muhurat`) | KEEP | |
| `tara_balam_for_native` | PROMOTE | core Muhurta strength factor |
| `chandra_balam_for_native` | PROMOTE | core Muhurta strength factor |

### System Lenses
| Tool / engine | Verdict | Note |
|---|---|---|
| `kp_query` + `query_kp_ruling_planets` | KEEP both, **sharpen disambiguator** | real FORENSIC-vs-computed distinction; do NOT merge |
| `query_jaimini_drishti` | **DE-REGISTER** until engine built | sidecar stub |
| `query_jaimini_chara_dasha` | PROMOTE (canonical) | |
| `jaimini_chara_dasha` / `jaimini_chara_dasha_full` | DEDUP | alias residue |
| `query_varshphal` (`query_varshaphala`) | KEEP | Tajaka annual |
| `saham_query` | PROMOTE | Tajaka sahams |

### Tradition & Adjudication
| Tool / engine | Verdict | Note |
|---|---|---|
| `multi_school_bundle` | KEEP (entry-point) | |
| `cross_school_lookup` (`multi_school_signal_lookup`) | KEEP | |
| `read_classical_text` (`classical_text_search`) | KEEP | |
| `query_remedial_mantras` + `query_remedies_prescribed` | **MERGE → one remedies tool** | mantras + prescribed |
| `classical_attribution_lookup` | FOLD → multi-school/classical | |
| `convergence_score_lookup` | FOLD → multi-school | |
| `classical_disclosure_filter` | INVESTIGATE/REMOVE | likely tier-coupled → remove with §3 |

### Ground-truth & Substrate
| Tool / engine | Verdict | Note |
|---|---|---|
| `lel_query` | KEEP | calibration spine |
| `vector_search` | KEEP (resident core) | |
| `read_asset` | KEEP | |
| `domain_report_query` | PROMOTE or FOLD | |
| `query_v7_additions` | INVESTIGATE | sidecar wrapper — disposition TBD |

### Governance / Meta
| Tool / engine | Verdict | Note |
|---|---|---|
| `get_trace`, `list_recent_queries` | KEEP | observability |
| `tool_health`, `data_coverage` | KEEP | become the functional-vs-stub gate engine |
| `log_prediction`, `record_outcome`, `flag_disagreement` | KEEP | writes |
| `manifest_query` | FOLD → meta | instrument self-description |
| `tool_catalogue` | reconcile → becomes the generated catalog (§2) | |

### Plumbing dead-code (remove)
- Orphaned planner path: `/api/mcp/execute`, `/api/mcp/plan`, `callPlatform()`, `callPlatformPlan()` — unreachable from any registered tool (the only server-side LLM/planner; remove or fence to the `/consume` web surface explicitly).
- Alias/dup entries in `primitives_registry.ts` (engine-name pass-throughs; duplicate `msr_sql`).

**Headline net effect:** ~6 merges (collapsing ~11 tools → ~4), ~10 promotions (exposing built-but-invisible engines), ~3 backfills, 1 de-registration, several folds + dedups, and one dead-code removal — yielding a tighter, fully-distinct, fully-exposed set where every family has one entry-point + non-overlapping primitives.

---

## §7 — Phased sequence (decided; Anthropic-optimized)

**Phase 0 — Manifest spine** *(implement first; low astrological risk)*
Define the manifest schema; make catalog generated from it; collapse registry to runtime-state;
**rip out tiers** (§3); remove the dead planner path + alias cruft. Outcome: one source of truth.

**Phase 1 — Per-tool contract enrichment**
Annotations (§4.4), the disambiguator description template + lint gate, `response_format` +
pagination defaults, structured errors, data-dependency declarations.

**Phase 2 — Reconciliation**
Execute the §6 merges / de-registrations / folds / dedups against the manifest.

**Phase 3 — Gateway baseline (dynamic loading, now)**
`search_tools` + `invoke_tool` over the manifest; define the resident core set; full reconciled
set behind the gateway.

**Phase 4 — Parity promotions**
Promote the engine-only capabilities (§6 PROMOTE rows), highest-value families first
(Time & Prediction, Electional).

**Phase 5 — Data backfills**
CGM graph, L5 timeline, signal_states — so health/coverage reads true.

**Phase 6 — Protocol-native listChanged (dynamic loading, later)**
Stateful sessions + SSE + externalized session store; layered on the gateway.

**Phase 7 — Prompts + eval gates**
`prompts` primitive for the canned reading workflows (incl. `interpret_current_dasha`);
per-tool contract tests (blocking) + functional/coverage gate.

---

## §8 — Open items for native confirmation

1. **Merge granularity** — confirm the §6 merges as proposed (signals+msr_sql → 1;
   register-quartet → 1; synthesis-walk-trio → 1; remedies → 1), KP pair kept separate,
   ephemeris+temporal reconciled. Or review each merge individually before any commit.
2. **`query_ephemeris` + `temporal`** — merge under a `mode` param, or keep separate with a
   sharpened disambiguator? (Live-sidecar vs positional-SQL is a real distinction.)
3. **`query_jaimini_drishti`** — de-register the stub now, or keep the slot reserved (visible
   but non-functional)? Recommendation: de-register.
4. **`query_v7_additions`, `classical_disclosure_filter`, `domain_report_query`** — need a
   quick engine read to finalize disposition (marked INVESTIGATE above).

---

*End of TOOL_PORTFOLIO_PLAN v1.0 (DRAFT — for native review). No implementation performed.
Executor briefs are cut per-phase only after this plan is approved.*
