---
artifact: RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION
canonical_id: RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION
version: 1.1
status: CURRENT
created: 2026-06-27
author: Cowork (code-plane validation, two parallel sub-agents reading actual source) — for native Abhisek Mohanty
classification: D-GROUNDTRUTH validation — grounds the plan in running code before implementation
scope: code-plane only (per native ruling); NO prod DB / Cloud Run / build touched (governance: prod-only data plane + sync-freeze)
method: every load-bearing claim in the approach plan + D-GROUNDTRUTH deliverables checked against actual code/migrations/seed; code wins over docs
changelog:
  - v1.0 (2026-06-27): Initial findings register. 2 sub-agents validated Groups A–G against source. Major corrections: two parallel retrieval systems (not one); MCP wires 13 not 27 tools; MCP has no SSE; the dedup/drill doctrine is doc-only except query_ucd; BOTH manifests stale; L3/L4/L5 are BUILT (memory was stale); Anthropic not code-banned; tier still lives in MCP resources.
  - v1.1 (2026-06-27): Added §H — native-contamination audit (chart-agnostic mandate, approach §D). Found CRITICAL native defaults in the OLD platform-mcp/src/tools/ surface; the NEW lib/retrieval/registry/ layer is clean. Reinforces "build on the new registry."
---

# RETRIEVAL GROUND-TRUTH — CODE-PLANE VALIDATION REGISTER (v1.0)

> **What this is.** The result of grounding the retrieval-system design plan in *actual running code* before
> implementation — per native ruling ("validate the entire plan in Claude Code… pick up important learnings
> and design with those learnings"). Two parallel sub-agents read the real source (not prior summaries) and
> returned verdicts with file:line evidence. **Code-plane only** — no prod DB, Cloud Run, or build was
> touched, per the project's prod-only-data-plane + sync-freeze governance. Verdicts: CONFIRMED / REFUTED /
> CORRECTED / CANNOT-VERIFY-FROM-CODE.
>
> This register is authoritative over the four D-GROUNDTRUTH deliverables and the approach plan where they
> disagree. Corrections are folded into those artifacts (version bumps noted).

---

## §1 — The headline corrections (read these first)

Six findings materially change the design. Each is evidence-backed below.

1. **There are TWO (arguably three) parallel retrieval systems — the plan conflated them.**
   - `platform/src/lib/retrieval/` — the NEW capability registry (3 primitives, 4 adapters, URI scheme,
     per-layer registrations). Tier-free. *This is the modern target.*
   - `platform/src/lib/retrieve/` (no "l") — the OLDER chat/consume toolset (`msr_sql`, `chart_facts_query`)
     actually used by `/api/chat/consult`. **Still contains `audience_tier`.**
   - `platform/src/lib/mcp/primitives_registry.ts` — a third bridge mapping `query_signals → msr_sql`.
   → **The plan MUST name which system it builds on and account for migrating/retiring the other two.** This
     is the single most important correction.

2. **MCP wires ~13 tools, not 27** — "27" was a *file count*. `server.ts` registers ~13 tool groups;
   `/health` self-reports `tools: 13`. ~14 tool files exist but are **written-yet-unregistered** (incl.
   `get_cgm_subgraph`, `vector_search`/bo_2-7, all `kala_*`, several phala). "Broken stubs" was wrong — they
   are real code, just not wired.

3. **MCP has NO SSE.** It is POST-only Streamable HTTP, stateless (`sessionIdGenerator: undefined`); `GET /mcp`
   → 405. Any plan text citing "SSE streaming on MCP" is wrong. (External Gemini Remote-MCP requires Streamable
   HTTP anyway, so this is compatible — but the claim must be corrected.)

4. **The dedup / UCD-first→drill doctrine is almost entirely DOC-ONLY in code.** The L2 retrieval registry
   contains ONLY `query_ucd.ts` + `index.ts`. The drill tools the strategy doc names — `query_zoom`, `lens`,
   `domain-evidence` — and the `lel_enabled` toggle **do not exist in code.** → The topology framework's
   umbrella-then-drill pattern is **almost all TO-BUILD**, not "extend existing implementation." (The *design*
   alignment with the doctrine still holds; the *implementation* does not yet exist.)

5. **L3 / L4 / L5 are BUILT — the memory/handoffs were STALE.** Writers exist for every ka_*/ph_*/mi_* asset
   in `python-sidecar/pipeline/orchestrator/writers/`; `transit_search.py` exists and is substantive; CLOSE
   seal docs exist for L3/L4/L5. The loaded MEMORY.md ("L3 = BUILD+wire, transit_search never built", L4/L5
   writers absent) is OBSOLETE. → The plan's "L0–L2 reality / L3–L5 intent" split is **wrong**; all six layers
   have writers. (Service-type assets legitimately have NULL floors — that's by design, not unbuilt.)

6. **Anthropic is NOT code-banned** — only defaulted away (`DEFAULT_STACK_ID='gemini'`, comment "Anthropic
   credits exhausted"). The "Anthropic BANNED" rule is memory/policy, not code-enforced. Also a real
   discrepancy: `DEFAULT_STACK_ID='gemini'` vs `CALL_TYPE_ROUTING=STACK_ROUTING['nim']` disagree on the
   effective default depending on call site.

Plus two integrity flags: **BOTH CAPABILITY_MANIFEST copies are stale** (stamped 2026-06-05, predate migration
325 + L3–L5 writers — so even the "137 live" copy is not ground truth; the seed + writers dir are closer);
and **audience_tier still lives in MCP resources** (`house_rules_variants/{client,acharya,super_admin}.md` +
an active visibility test) despite the no-tier doctrine and the GISMCP-stripped memory.

---

## §2 — Full verdict tables

### Group A — Retrieval scaffold (`lib/retrieval`)
| Claim | Verdict | Evidence |
|---|---|---|
| A1 registry + 3 primitive types in registry/types.ts | CONFIRMED | `types.ts:11` `CapabilityType = 'tool'\|'resource'\|'prompt'` |
| A2 four adapter families, real impls | CONFIRMED (2 stubs) | agentic_loop(7)/bulk_context(4)/openai_function_calling/hybrid all real; stubs: `bulk_context/synthesizer.ts:63` `[SYNTHESIS_STUB]` (Vertex not wired), `openai_function_calling/oauth.ts:29` dev-only |
| A3 central + per-layer L0/L1/L5 index | CORRECTED | L0=15, L1=19, **L2=1 (query_ucd)**, L5=2 (not 3), L3=0, L4=0. Plan's "L0/L1/L5" omitted L2 |
| A4 URI scheme marsys://{type}/{layer}/{name} | CONFIRMED | `types.ts:13` + live URIs |
| A5 no audience_tier in retrieval | CONFIRMED (new) / REFUTED (global) | `lib/retrieval` clean; **`lib/retrieve/types.ts` + MCP `house_rules_variants/*` + `server_tier_visibility.test.ts` still carry tier** |

### Group B — MCP server
| Claim | Verdict | Evidence |
|---|---|---|
| B1 server, Streamable HTTP + SSE, Bearer+OAuth | CORRECTED | Streamable HTTP + Bearer + OAuth confirmed; **SSE REFUTED** (`GET /mcp`→405, stateless) |
| B2 ~27 tools L0–L5 | CORRECTED | **~13 wired** (`/health: tools:13`); 27 = file count; ~14 files unregistered |
| B3 filter-drift (MCP drops portal filters) | CORRECTED | **Worse: MCP exposes NO signal-filter tool at all.** `msr_sql` is chat-side (`lib/retrieve`); MCP `server.ts` registers no `query_signals`/`msr_sql`. Not drift — absence |
| B4 broken stubs vector_search/read_asset/get_cgm_subgraph | CORRECTED | Written-yet-unwired, not broken: `get_cgm_subgraph.ts` real but unwired; `vector_search` in `bo_2-7.ts` real (Vertex) but unwired; `read_asset` only in resource catalogs |

### Group C — Model routing
| Claim | Verdict | Evidence |
|---|---|---|
| C1 lib/models registry/resolver/health | CONFIRMED | files present (+nvidia/openai/runtime_config) |
| C2 5 providers + models | CONFIRMED | `registry.ts:47`; Anthropic claude-haiku-4-5/sonnet-4-6/opus-4-7, Google gemini-2.5-*, DeepSeek v4-pro/flash(+legacy), OpenAI gpt-4.1-*(+legacy), NVIDIA nemotron/kimi |
| C3 reasoning-mode + family-worker | CONFIRMED | `ReasoningMode='markers'\|'native'\|'none'`; FAMILY_WORKER:882 |
| C4 Anthropic cost-banned in code | CORRECTED | Not banned — defaulted away (`DEFAULT_STACK_ID='gemini'`); + `gemini` vs `nim` default discrepancy |

### Group D — Asset catalogs & drift
| Claim | Verdict | Evidence |
|---|---|---|
| D1 seed = 81 (22/16/10/12/9/12) | CONFIRMED | exact per-layer counts in seed |
| D2 two manifests 137 vs 117 | CONFIRMED (+worse) | root `entry_count:137`, platform `117`; **BOTH stamped 2026-06-05, predate mig 325 + L3–L5 → both stale** |
| D3 asset_registry columns | CORRECTED | 19 cols incl sort_order/size_sql/expected_volume_*/created_at; `asset_type` added later (mig 202+), not in 167 |
| D4 per_chart count_sql scopes chart_id | CORRECTED (good) | trap NOT present in current seed — all per_chart use `WHERE chart_id=$1`; global correctly omit |

### Group E — Build reality
| Claim | Verdict | Evidence |
|---|---|---|
| E1 L0–L2 built / L3–L5 unbuilt | **REFUTED** | writers for ALL ka_*/ph_*/mi_* in `writers/`; L3/L4/L5 CLOSE seals exist; service-type NULL floors are by-design |
| E2 transit_search never built / compute_transits stub | **REFUTED** | `pipeline/transit_search.py` substantive (swisseph); ka_gochara service/writer present — memory obsolete |

### Group F — MSR/CGM spine (mig 325)
| Claim | Verdict | Evidence |
|---|---|---|
| F1 bodha_msr_signals columns | CONFIRMED | signal_id PK:56, chart_id:57, constituent_facts_array:84, classical_sources_jsonb:72, computed_salience:107, contradicts_signals_array:133, lel_origin:80, signature_tier:78, signal_summary_text:70 |
| F2 CGM nodes+edges | CONFIRMED | nodes: msr_signal_id:474, node_embedding_vec VECTOR(768):485; edges: underlying_msr_signal_ids_array:538, relationship_basis:526 |
| F3 bodha_contradictions FKs | CONFIRMED | signal_a_id:195, signal_b_id:196 → bodha_msr_signals |
| F4 bo_samvada is a view | CONFIRMED | seed storage_type postgres_view, vw_chart_digest (writer also exists but type is view) |

### Group G — Dedup/retrieval doctrine
| Claim | Verdict | Evidence |
|---|---|---|
| G1 reference-don't-repeat + UCD-first→drill implemented? | CORRECTED (doc-only) | only `query_ucd.ts`+`index.ts` in L2 registry; `query_zoom`/`lens`/`domain-evidence` absent in code → TO-BUILD |
| G2 lel_origin column + lel_enabled handled | CONFIRMED col / lel_enabled DOC-ONLY | `lel_origin` real+indexed (mig 325:80,183); `lel_enabled` zero code matches |
| G3 embeddings pgvector + writer | CONFIRMED (+stale dup) | `bodha_signal_embeddings.embedding_vec VECTOR(768)` (mig 325:874); **live writer = `bo_samskara.py` (Vertex 768)**; `l2_embeddings.py` (TF-IDF 256) is the DEAD scaffold |

---

## §3 — Design impact (what changes, by wave)

- **Approach plan §0.1 / §B / D5:** correct the "L0–L2 reality / L3–L5 intent" framing — *all six layers have
  writers*; the real split is "L0–L2 sealed-and-mature vs L3–L5 built-and-recently-sealed," and the true
  unknowns are runtime/data-plane, not existence. Correct "27 MCP tools"→"~13 wired, ~14 written-unwired."
  Correct "SSE"→Streamable-HTTP-only. Correct "Anthropic banned in code"→"defaulted away."
- **D0 (scaffold disposition):** the decision is now sharper — there are **two/three retrieval systems**, and
  D0 must rule on: build on `lib/retrieval` (modern, tier-free) and migrate/retire `lib/retrieve` + the
  `primitives_registry` bridge; strip residual tier from MCP resources.
- **D1 (contract) / topology:** the umbrella-then-drill topology is **TO-BUILD** (only `query_ucd` exists) —
  good news is a clean slate aligned to doctrine; bad news is the plan must not assume drill tools exist.
- **D4 (graph):** `get_cgm_subgraph`/`vector_search` already exist as real-but-unwired code — D4 can *adopt*
  them rather than build from zero (verify they match mig 325 schema).
- **D7 (channels):** the MCP↔chat problem is not "drift" but **the MCP surface lacks the filtered signal
  query entirely** — D7's by-construction-no-drift goal becomes "expose the shared query logic on MCP for the
  first time," which is cleaner.
- **D8 (governance):** add resolving the two-manifest staleness + the lib/retrieve tier residue + the
  gemini-vs-nim default discrepancy as governance fixes; regenerate the manifest post-mig-325.

---

## §4 — Items that genuinely need runtime (deferred, NOT done here — governance)

These can only be confirmed against prod in a controlled Claude Code/Antigravity session (prod-only data
plane). Listed so they are not forgotten; NOT executed from Cowork:
- Whether the L3/L4/L5 writers have actually *run* and populated tables on the native chart (writers existing ≠ data built).
- Whether `bo_samskara` Vertex embeddings are actually populated vs empty.
- Whether the deployed MCP Cloud Run revision matches main HEAD (per the verify-revision-before-probe rule).
- Live count_sql correctness on the canonical chart (the cockpit-truth check).
- Whether `query_ucd` returns correctly against the live `vw_chart_digest`.

A runtime-validation brief for these belongs in the implementation session, not this design phase.

---

## §H — Native-contamination audit (chart-agnostic mandate)

Per native ruling, retrieval tools must be chart-agnostic — operate on the user's chart, never default to the
native. A dedicated leakage audit grepped all retrieval trees for the native id `482012f1-…`, phantom
`362f9f17`, NATIVE_BIRTH/NATIVE_CHART constants, native-default fallbacks, and native-as-fixture. Phantom =
zero hits (clean). Two layers, opposite hygiene:

### §H.1 — CLEAN: the new registry (build on this)
`platform/src/lib/retrieval/registry/layers/*` — every per-chart tool sets `required_inputs:['chart_id']`,
scopes SQL `WHERE chart_id=$1`, **no `?? native` fallback in any handler**. Only LOW: one describe string
(`L1_ganita/get_positions.ts:22`) names the native — scrub to placeholder.

### §H.2 — CONTAMINATED: the old MCP tools (remediation target, do NOT build on)
| Severity | Finding | Evidence |
|---|---|---|
| CRITICAL | missing chart_id → native fallback | `platform-mcp/src/tools/kala_temporal.ts:39,571` `.default(NATIVE_CHART_ID)`; `retrieval/kala_temporal.ts:45,466`; `retrieval/holistic_bundle.ts:56,280` `chart_id ?? NATIVE_CHART_ID`; `retrieval/ganita_forensic_render.ts:106`; `l0_brahmagyan.ts:23,218` stamps native id on every classify |
| CRITICAL | native lifespan as default date range | `kala_convergence.ts:154` `date_range.start ?? '1984-02-05'` |
| HIGH | native LEL corpus served with NO chart selector | `mimamsa_lel_intake.ts` (`lel_query`) — no chart_id param; description "for native Abhisek… 57 events" |
| HIGH | native computed dāśā tables embedded as literal fallback | `kala_period_snapshot.ts:50`, `kala_timeline.ts:54,314`, `retrieval/kala_temporal.ts:159` |
| MEDIUM | native-as-fixture tests (one asserts description must contain "Abhisek Mohanty") | `__tests__/kala_temporal*.test.ts`, `phala_muhurta.test.ts:243` |
| LOW | native ids in ~21 LLM-visible `.describe()`/JSDoc strings | bo_2-5/6, bodha_bo22, get_cgm_subgraph, phala_*, etc. |
| LOW | `?? 'default'` cache-key bucket (cross-chart collision, not native leak) | `bundle_adapters.ts:229+`, `bundles/holistic_bundle.ts:295` |

### §H.3 — Verdict + design consequence
The existing retrieval code is NOT uniformly chart-agnostic. **Build on the new `lib/retrieval/registry/`
layer** (clean); treat the old `platform-mcp/src/tools/` surface as a **remediation target** when carried into
the consolidated MCP surface (D7): remove every native default, make `chart_id` required + error-if-missing,
give `lel_query` a required chart_id, scrub descriptions to placeholders, fix cache keys. The chart-agnostic
contract gate (approach §D.2) must reject any of these patterns in CI going forward. Runtime confirmation of
the blast radius is in the runtime brief (V12b–V12d).

*End of RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION v1.1 — code-plane only; runtime items deferred per governance.*
