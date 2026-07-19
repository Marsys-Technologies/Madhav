---
artifact: GROUND_TRUTH_REGISTER.md
canonical_id: RETRIEVAL_AUDIT_GROUND_TRUTH_REGISTER
version: 1.0
status: COMPLETE — reconciliation adjudication (brief §F.1)
authored_by: Claude (conductor, reconciliation pass — opus, high effort), 2026-07-19
governing_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §F
audit_subject: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (v1.2)
lane_sources:
  - LANE_A_REPORT.md (catalog & registration — sonnet)
  - LANE_B_REPORT.md (envelope & budget — sonnet)
  - LANE_C_REPORT.md (planner & taxonomy — opus/high)
  - LANE_D_REPORT.md (MCP edge & adaptivity — sonnet)
  - LANE_E_REPORT.md (data-plane & service coverage — opus/high)
  - LANE_F_REPORT.md (Paripraśna rebuild interface — opus/high)
---

# Ground Truth Register — Retrieval Plane Elevation Plan v1.2

Every factual claim in plan §1.1–§1.5 is adjudicated below as one of:

- **CONFIRMED** — the plan states it correctly; lane evidence backs it.
- **CORRECTED** — the plan is stale/wrong/imprecise; the true fact is stated with lane+file:line evidence.
- **NEW-GAP** — a real defect a lane found that the plan does not claim (cited to lane).
- **PLAN-ITEM-ALREADY-DONE** — reality is ahead of the plan; the item need not be re-done (cited).

Then every §3/§7/§8 phase item carries a **feasibility note** row (verdict of whether the audit changed
its feasibility, scope, or sequencing). Zero plan claims are silently skipped. IDs (`GT-n`) are stable
handles the plan v1.3 amendment traces against.

Two conventions: (1) counts that no single grep reproduces today are marked **CORRECTED-APPROX** with the
band; (2) where two lanes read the same object differently, the divergence is its own flagged row
(`GT-AMBIG-n`), never silently collapsed.

---

## Part A — Plan §1 factual claims

### §1.1 — "The catalog is triplicated"

| ID | Plan claim (§1.1) | Verdict | True fact / evidence |
|---|---|---|---|
| GT-1 | "**123 capability descriptors** in the retrieval registry." | **CORRECTED-APPROX** | Not a single reproducible invariant. Lane A: `getCatalog()` reaches **118**; `route.ts` bootstrap reaches **122**; the two disagree *by construction* (see GT-4). Lane B: **115** `server.tool(` sites / **116** `CapabilityDescriptor`-typed consts. "123" is a stale snapshot within ±5; use "≈118 registry descriptors, census must be codegen-derived" going forward. [Lane A §1, Lane B §1] |
| GT-2 | "**Three parallel tool catalogs, no parity check.**" | **CONFIRMED** (with catalog #2 corrected — see GT-3) | Three distinct catalogs exist and no live parity gate binds them. [Lane A §2] |
| GT-3 | Catalog #2 = "**~76 `ToolContract` entries in `lib/contract/tool_metadata.ts`, which is what the live chat LLM actually sees**." | **CORRECTED** | The claim **conflates two differently-typed tables.** `tool_metadata.ts`'s 76 rows are typed `ToolReconciliationEntry` (an audit/coverage map, `tool_metadata.ts:300`), **not served**. The actually-served contract catalog is `TOOL_CONTRACTS` in `lib/contract/registry.ts` = **6 entries**, feeding `CONTRACT_CATALOG` → `schema_utils.ts:24-36` (the live chat surface). The chat contract surface is **6 rows, not ~76**. R-1's compiler must absorb the real 6 and separately retire/re-scope the 76-row audit table. [Lane A §2] |
| GT-4 | "**Bootstrap duplication already caused two production outages** … D9/D10 each 404'd" (framed as historical, now fixed). | **CORRECTED — the bug class is LIVE, not just historical** | D9/D10 are indeed fixed (present in both `route.ts` and `catalog.ts`). But `getCatalog()` and `route.ts`'s bootstrap **still disagree today**: D6-synergy (2 caps: `synergy/pipeline`, `synergy/cross_layer`) and MARO/dprofiles (3 caps: `maro/orchestrate`, `maro/mcp_surface`, `resource/maro/profiles`) are in `route.ts` but absent from `catalog.ts`; `synth_compose_large_n` (1) is the reverse. Same failure class the plan calls fixed — unfixed for 5+1 capabilities. [Lane A §1, §3] |
| GT-5 | "MCP surface — **~25 hand-written `server.tool` registrations in `registry_bridge.ts`** plus hand-maintained alias/bridge maps." | **CORRECTED-APPROX** | `registry_bridge.ts` registers **25** tools (not ~25 — the `server.ts` census comment's "20" is itself stale; live count 25). Aggregate MCP tool count is **UNVERIFIABLE to an exact integer by grep** — wrapper-indirection (`regAlias`/`globalAlias` in `register_p1_aliases.ts`) makes a naive `grep server.tool(` undercount; lower bound ≈145. Any R-1 number must come from an AST/runtime census, not grep. [Lane A §2, §8] |
| GT-6 | "The Vidhi planning registry exists in **three hand-synced copies** (two TS trees + a DB seed, migration 440); `capability_version.ts` hashes only one." | **CONFIRMED** (and the drift has begun — see GT-30) | Two near-identical TS trees (`platform/src/lib/vidhi/registry_data.ts`, `platform-mcp/src/resources/vidhi/registry_data.ts`) + DB seed (migration 440, whose own comment documents the mirror). `capability_version.ts:29-35` hashes only the MCP-side TS copy's primitives+floors. [Lane A §5, §7; Lane C C-G1] |
| GT-7 | "The **session-pin type is hand-mirrored** into `platform-mcp/src/lib/session.ts`." | **CONFIRMED** (not independently re-derived; consistent with handoff) | Not directly re-counted by a lane this pass; no lane contradicted it. Carries forward as CONFIRMED-per-handoff. Note Lane F: the "session pin" construct itself is slated for D-16 restructuring (see GT-56/F-R4) — the mirror may be moot post-excision. |
| GT-8 | "Positive: the envelope mirror is **already codegen'd** … the handoff's 'hand-maintained mirror' claim is stale." | **CONFIRMED — PLAN-ITEM-ALREADY-DONE (partial)** | `platform-mcp/src/generated/envelope.ts` is sha-stamped generated; the hand mirror `platform-mcp/src/lib/envelope.ts` is deleted; a parity test (`r5_codegen_parity.test.ts`) exists. **Caveat (NEW, GT-9):** the parity test is **not wired into CI** — platform-mcp's whole vitest suite is deliberately excluded, so drift is currently undetected despite the machinery existing. [Lane A §6] |

### §1.2 — "The envelope is authored once, applied almost nowhere"

| ID | Plan claim (§1.2) | Verdict | True fact / evidence |
|---|---|---|---|
| GT-10 | "Only **6 of ~123 handlers** import `envelope.ts`." | **CORRECTED** | The "6 files" figure conflates files with handlers. Real picture: **3 authoring sites** (`synthesis/capability.ts`, `registry_bridge.ts`'s `envelope()` wrapper, `register_p1_ganita.ts`'s wrapper) feed a low-double-digit count of tools; 2 more files import only `buildHonestPagination`. Adoption is a small minority either way, but "6 of 123" is not the right shape — replace with the 3-authoring-sites framing. [Lane B §1] |
| GT-11 | "Only **3 tools default to v3** (`judgment_query`, `graha_portrait`, `pact_query`); everything else legacy; legacy has no `chart_header`." | **CONFIRMED (exactly)** | `resolveEnvelopeFormat(... ?? 'v3')` at exactly 3 sites (`registry_bridge.ts:1857/2422/2827`); all others default `'legacy'`. [Lane B §2] |
| GT-12 | "`judgment_flags` typed `string[]` but `register_d8_assess_domain.ts:595` emits **objects**; flags range from stable tokens to multi-sentence prose." | **CONFIRMED (exactly, file:line matches)** | d8 builder (feeds assess_marriage/career/health/wealth) emits `{claim, requires_acharya_validation}` objects vs the `string[]` type at `envelope.ts:302,346`. [Lane B §3] |
| GT-13 | "`envelope_version` stays `'v1'` even under v3." | **CONFIRMED (exactly)** | Hardcoded `'v1'` at `envelope.ts:391,421` and in the generated mirror; never conditioned on format. v3 distinguished only by `response_format:'v3'`. [Lane B §4] |
| GT-14 | "Cursors encode only `{offset}` — no filter/sort fingerprint." | **CONFIRMED (exactly)** | `encodeCursor`/`decodeCursor` (`envelope.ts:201-214`) carry only `.offset`. [Lane B §5] |
| GT-15 | "`density_contract`: **6 of ~123** (~5%); **three of the six** declare `empty_reason:false` with 'not yet added' notes." | **CONFIRMED count (6), CORRECTED sub-claim** | 6 confirmed; split is 3 `false` / 3 `true`. But only **2 of the 3** `false` carry a "not yet added" note (`get_yoga_dosha.ts:71`, `query_signals.ts:230`); the third (`register_d9_judgment.ts:418`) is a **deliberate design choice** (judgment_flags is its honest-gap channel), not an unfinished stub. [Lane B §6] |
| GT-16 | "**No `register` block exists** (A-18 unbuilt)." | **CONFIRMED** | No lane found any `register` block; corroborated by Lane F F-R6 (plan builds it at R-1.1/R-2.3a). |
| GT-17 | "Two incompatible clippers coexist: `response_budget.ts` vs byte-truncating `result_clipper.ts` (32KB, invalid JSON)." | **CONFIRMED that both exist; CORRECTED re: orphan implication** | Both exist and differ. But `result_clipper.ts` is **NOT orphaned** — live caller `adapters/bulk_context/bundler.ts:47`, itself on the bulk-context/hybrid path. It is a narrower-purpose LLM-context clipper (documented at `response_budget.ts:12`), not dead code. R-2's "evict result_clipper" must account for this live consumer. [Lane B §9] |
| GT-18 | "`still_over_budget` is emitted but **unread by four direct callers**." | **CONFIRMED, and understated** | The 4 callers are confirmed exactly. But the field is **dead output on every call path** — even `finalizeMcpBudget` recomputes its own over-budget check independently rather than reading it. Not "unread by 4," but "read by nobody." [Lane B §7] |
| GT-19 | "**Reference tools are entirely unclamped.**" | **CONFIRMED, and understated** | True for `register_p1_reference.ts` (7 ref_* tools). But **15 of 21 tool-registration files (~36 of ~115 tools)** never touch the budget trimmer — materially bigger than "the reference tools." [Lane B §8] |

### §1.3 — "The planner is duplicated and mis-wired"

| ID | Plan claim (§1.3) | Verdict | True fact / evidence |
|---|---|---|---|
| GT-20 | "**Paripraśna does not use the Vidhi engine at all.** `consult/route.ts` runs `pipeline_planner` + a hardcoded B.11 floor injection." | **CONFIRMED (exactly)** | Zero `vidhi`/`compileContract` hits in the consult tree; planner is `pipeline_planner`; B.11 injection at `route.ts:513-546`. [Lane C C-1, C-2] |
| GT-21 | "…injection pushes tool names (`pattern_register`, `cluster_atlas`) that resolve to nothing." | **CORRECTED (naming) — substantively true** | Only **`pattern_register` is actually pushed** (`route.ts:535`). `cluster_atlas` is a **dead constant** — it lives only in the L2.5 detection membership list (`route.ts:520`) and `inferLayer`, never in a `.push()`. Both are dead in the registry. Plan should read: "pushes the dead `pattern_register`; also carries dead `cluster_atlas`/`resonance_register` in its detection constants." [Lane C C-2] |
| GT-22 | "The **DR-8 classifier's vocabulary has zero overlap with the Vidhi compiler's intents**; `coerce` silently collapses every DR-8 intent to `general_synthesis`/`deepdive`; the advertised path **never selects a domain floor**." | **CONFIRMED (exactly)** | DR-8 INTENTS (12) ∩ Vidhi IntentClass (8) = ∅; `scope_resolver.ts:70-72,100-109` coerces intent→`general_synthesis`, depth→`deepdive`, horizon→`current`; compiler selects floor by intent alone (`compiler.ts:105`), so collapsed intent always hits the 6-item general_synthesis floor. [Lane C C-3] |
| GT-23 | "CR-28: **three live taxonomies plus a dormant prompt**, and the flagship handoff between two of them is a silent no-op." | **CONFIRMED (enumerated) — plus a STRUCTURAL re-scoping finding (GT-24)** | DR-8 (12) / Vidhi IntentClass (8) / pipeline `query_class` (10), pairwise ∩ = ∅, plus a dormant prompt that is a lossy subset of DR-8. [Lane C C-4] |
| GT-24 | (R-3.1 implicit design: "superset mapping … flat" enum unifies the taxonomies.) | **NEW-GAP / RE-SCOPING** | Lane C's structural finding: the three vocabularies are **not dialects of one taxonomy but three orthogonal axes** (technique+domain / domain×depth-fused / epistemic answer-mode). A flat superset-rename enum **cannot** unify them — DR-8's domain lives *outside* its intent field; Vidhi fuses domain×depth into one token. The only faithful unification is a **decomposed scope tuple** `{answer_mode × domain × depth × horizon (× intervention × entitlement)}` with `IntentClass` **derived**, not a peer enum. This changes what R-3.1 must build (see plan v1.3 R-3.1). [Lane C, Unified-taxonomy section] |
| GT-25 | "Domain floors thin beyond wealth (**career 12 / health 10 / marriage 9** vs wealth 26)." | **CONFIRMED (exactly)** | Counted from `registry_data.ts`: 26/12/10/9 exact. [Lane C C-5] |
| GT-26 | "**12 of 37 primitives** are dark-by-construction with open CRs." | **CONFIRMED (exactly)** | 37 `VidhiPrimitive` rows; exactly 12 carry a non-null OPEN-CR `known_gap` (CR-16/24/30/37/56/61/64/66/67/68/69/73, all in `cr_status.ts` OPEN_CRS). [Lane C C-6] |
| GT-27 | "`cr_status.ts` is a **frozen snapshot with a self-flagged CR-55 contradiction**." | **CONFIRMED (and CR-55 is tri-state)** | Frozen hand-authored arrays; self-documented CR-55 conflict (snapshot=CLOSED vs consumption-register-body=OPEN-ELEVATED). Defect register adds a **third** reading ("appears fixed live"). Tri-state; snapshot cannot self-correct. [Lane C C-7] |

### §1.4 — "Multi-LLM adaptation is scaffolded but inert"

| ID | Plan claim (§1.4) | Verdict | True fact / evidence |
|---|---|---|---|
| GT-28 | "`server.ts:287-304` **fetches the model-family surface spec and discards it** … reads a `response_format` field the spec never contains." | **CONFIRMED (exactly, verbatim line range)** | `void effectiveFamily; void responseFormat` at 303-304; `McpSurfaceSpec` has no `response_format` field. [Lane D §1] |
| GT-29 | "`max_tools` is **never enforced**; all 120 tools go to every client." | **CORRECTED (load-bearing nuance)** | `max_tools` **IS** enforced — for internal composite-bundle sub-tool fan-out (`bundle_adapters.ts`). It is never enforced on the **`tools/list` surface** a client sees (no `ListToolsRequestSchema` handler). Two distinct enforcement points; R-4.1 must build the surface-list path and **not** rebuild the working fan-out path. [Lane D §2] |
| GT-30 | "**No MCP tool annotations anywhere.**" | **CONFIRMED (exactly)** | Zero `readOnlyHint`/`idempotentHint`/`destructiveHint`/`openWorldHint` matches. [Lane D §3] |
| GT-31 | "`behavioral_overrides` populated **once**; `drill_children` 11×; `output_schema` 4×." | **CONFIRMED (the once); drill_children/output_schema NOT re-verified** | `behavioral_overrides` set exactly once (`dprofiles_registration.ts:99`). `drill_children`/`output_schema` counts flagged UNVERIFIABLE-NOT-CHECKED by Lane D (out of its core list) — carry forward as plan-stated, unconfirmed. [Lane D §4] |
| GT-32 | "Descriptions … several embed **the native chart's exact row counts** (66,738 / 27,554 / 5,566)." | **CONFIRMED, and materially understated (→ GT-42, GT-43)** | Leakage is **11 instances across 8 files**, not 3. [Lane D §5] |
| GT-33 | "`listCapabilities` silently ignores the `archetype`/`tool_role`/`traversal_level` filters." | **CONFIRMED, and broader** | Correct — plus a **fourth** ignored field, `scope`. Implementation (`registry/index.ts:52-61`) checks only `type`/`layer`/`name_prefix`. [Lane D §6] |

### §1.5 — "Trust seams"

| ID | Plan claim (§1.5) | Verdict | True fact / evidence |
|---|---|---|---|
| GT-34 | "Dev-mode internal token check **fails open** (`route.ts:34-35`)." | **CONFIRMED, and it is a 13-file pattern (→ GT-44)** | Fail-open fires when `MCP_INTERNAL_TOKEN` is unset AND `NODE_ENV==='development'`; verified at `asset/route.ts:33-36`. Duplicated verbatim across 13+ route files, not one site. [Lane D §7] |
| GT-35 | "`plan_retrieval` and the `vidhi_plan` prompt compile plans for **any chart_id with no entitlement check**." | **CONFIRMED for the tool; prompt path inferred** | `register_vidhi_plan.ts` / `plan_builder.ts` have zero `authorize`/`entitle` hits. The `vidhi_plan` *prompt* path shares `plan_builder.ts` so the gap almost certainly applies but was not independently re-verified (Lane F territory). [Lane D §8] |
| GT-36 | "`parity_check.ts` **auto-passes** (returns empty set) when its bridge import fails." | **CORRECTED (mechanism imprecise) + NEW-GAP (may be dead code)** | A failed bridge import does return an empty `mcpUris` set — but in the normal populated context that makes **every** consume-URI land in `missing_in_mcp` → `passed=false`, a **hard FAIL**, not auto-pass. True auto-pass only in the degenerate both-empty case. **More important:** no CI/test/script invokes `checkParity()`/`runParityCheck()`; no `parity_check.test.ts` exists; a newer `scripts/manifest/parity_validator.ts` may be the live successor. R-0.5's fix must first confirm the file is even in the enforcement path. [Lane D §9] |
| GT-37 | "Per-chart entitlement on the dispatcher is solid (fail-closed, 30s cache); chart-agnostic gate solid (7 rules + raw-file scan)." | **CONFIRMED (not challenged)** | No lane contradicted the positive framing. Note the chart-agnostic gate's scan surface is narrower than the leak surface (GT-42/GT-43): it scans `description:` fields, missing empty_reason strings and PII. |

---

## Part B — NEW-GAP rows (real defects the lanes found, not in plan §1)

| ID | New gap | Lane / evidence | Absorbed into (plan v1.3) |
|---|---|---|---|
| GT-40 | **`getCatalog()`↔`route.ts` bootstrap disagree live** (D6-synergy 2, MARO 3 missing from catalog.ts; synth 1 the reverse). | Lane A §1/§3 | R-1.3 (one bootstrap) — enumerate these 6 |
| GT-41 | **`register_d4_graph.ts` is dead code** — never imported; its top-level `registerCapability()` never fires (capability registered via other path). | Lane A §1 | R-1.6 (hygiene) |
| GT-42 | **Native PII leak** — `ephemeris_cache_native_lifetime.ts:24-29` embeds the native's full name/DOB/birth-time/birthplace verbatim in a served resource description. Stronger than a row-count leak. | Lane D §5 | R-1.6 (chart-agnostic gate must scan beyond `description:`) |
| GT-43 | **`get_dashas.ts:123` embeds 601,443 rows, which disagrees with CLAUDE.md's canonical seal (chart_dashas=536,471)** — leaked AND apparently stale/wrong. | Lane D §5 | R-1.6 + flag for L1 seal cross-check |
| GT-44 | **Dev-token fail-open is a 13-file duplicated pattern**, not a one-liner. R-0.5 must extract a shared `validateServiceToken` or enumerate all sites. | Lane D §7 | R-0.5 (re-scoped) |
| GT-45 | **`still_over_budget` is dead on every path** (not just unread by 4). | Lane B §7 | R-2.5 |
| GT-46 | **Two handler files emit static `judgment_flags: []`** (`register_p1_synthesis.ts:82`, `register_p1_reference.ts:87`) — field present, no honest-gap machinery at all (worse than the `empty_reason:false` "not yet" gap). | Lane B §3 | R-2.2 |
| GT-47 | **`chart_header` fails silently with no flag in two layers** — inner (`chart_header.ts:90-93` swallows DB errors, fields stay null) and outer (3 `registry_bridge.ts` call sites catch→null), contradicting the §N.6 honesty discipline the same files apply elsewhere. | Lane B §10 | R-2.1 (chart_header fail-loud) |
| GT-48 | **Unclamped surface is ~15 files / ~36 tools**, not "reference tools." | Lane B §8 | R-2.5 |
| GT-49 | **`kala_timeline` is built-but-unwired** — complete handler (`platform-mcp/src/tools/kala_timeline.ts`, `registerKalaTimeline`) never imported into `server.ts`. One-line wiring fix, mis-grouped with build items. | Lane E New-Finding 1 | R-1.5.2 (split "dark-unbuilt" from "dark-unwired") |
| GT-50 | **`ka_graha_sancara` (arbitrary-datetime ephemeris) is a live in-code dark SERVICE** — `call_service_wrappers.ts:200-208` returns "not yet wired to a compute sidecar endpoint"; blocks ALL date-parameterized "positions at time T" retrieval. Named nowhere in plan or strategy. | Lane E New-Finding 2 | R-1.5 (service-asset disposition) |
| GT-51 | **Census single-directory grep causes false-dark misclassification** — grepping only `platform/src/lib/retrieval/` missed `register_p1_*.ts` and `brahma/*` serving paths; `bg_dignity_reference`, `bg_sign_medical`, `chart_panchanga` were mis-flagged dark but are SERVED. R-1.5's harness must grep all three serving paths. | Lane E New-Finding 3 | R-1.5.1 |
| GT-52 | **`reference_*` vs `bg_*` supersession unrecognized** — 5 `reference_*` tables (aspects/signs/planets/nakshatras/vargas) are dead-superseded by served `bg_*` equivalents; they are RETIRE candidates, not wire-up candidates. Conflating them would wire up dead tables. | Lane E New-Finding 4, §2(a) | R-1.5.2 (disposition), corrects §8.2 |
| GT-53 | **`response_budget.finalizeMcpBudget` injects a flag** (`response_still_over_<N>kb_budget_after_full_trim`) into whatever `judgment_flags` field the caller names — a cross-cutting emitter the plan's flag census omitted; relevant to the closed-enum design. | Lane B §3 | R-2.2 |
| GT-54 | **d8 `TEMPORAL_EMPTY_REASON` leaks a native-derived count** ("native chart 0/13,364 dated on lahiri") in a served `empty_reason` string — same leak class as descriptions, different code path. | Lane D §5 | R-1.6 (widen scan) |
| GT-55 | **The one CI test named for completeness (`m8_e2e_proof.test.ts` "G12 — REGISTERED_TOOL_COUNT is truthful") checks a locally-redefined 57 against a partial subset**, blind to ~63 of ~120 tools — not a completeness gate despite its name. Plus stale hand-counts in `registry_bridge.ts` (census says 20 vs 25) and `register_p1_synthesis.ts` (header says 3 vs 6). | Lane A §8 | R-1.2d (codegen census kills all hand-counts) |
| GT-56 | **`registry_data.ts`'s two TS copies have already drifted** (type-import line `'./types'` vs `'./types.js'`) with no parity gate — the triple-copy risk materializing now, in the floors R-3.3 will extend. (`cr_status.ts` copies still byte-identical — uneven drift.) | Lane C C-G1 | R-1.5 de-mirror / R-3.3 |

---

## Part C — Lane F Paripraśna contradictions (RAISED, not resolved — native rulings required)

These are architectural conflicts between the plan and the settled Paripraśna target architecture. Per
brief §D.4 / handoff §8 rule 8 they are **raised, not adjudicated**. Each carries a pointer into
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`. Full statements: Lane F §3.

| ID | Contradiction | Verdict | Pointer |
|---|---|---|---|
| GT-C1 | **`prashna_ask` contract carries a `depth` param that D-15 abolished.** Plan R-5.1 = `{chart_id, question, scope_tuple?, depth, response_format}`; D-15/§13.4 removed `depth` and `tier` from the engine signature; `scope_tuple?` already derives depth, making `depth` both forbidden and redundant. Cheap to fix now (tool unbuilt, paper only). | **CONTRADICTED — raised** | PARIPRASHNA §1/D-15, §13.4, stale §6.1 Door-2 diagram |
| GT-C2 | **R-3.2 rewrites the exact `consult/route.ts` block carrying a live D-15 `audience_tier` violation** (`:459`, `:616`) without excising it; excision is assigned to a different workstream (PARIPRASHNA P2'). The floor mechanism itself is D-15/D-16-safe; the hazard is omission — the floor could land D-15-dirty. | **CONTRADICTED (by omission) — raised** | PARIPRASHNA §13.7, §16.1/F-25g |
| GT-C3 | **"The envelope is the product on the raw-tools path" vs missing reader-facing signal text.** Plan supplies token labels (R-2.3a) but not signal *prose*; `bodha_msr_signals` has no reader-facing column (only machine-internal `signal_summary_text`/`signal_headline_text`), so cited signal *content* is still internal-register text. The `signal_reader_text` editorial pass (PARIPRASHNA P5') is in no plan phase. | **UNDER-SPECIFIED — raised** | PARIPRASHNA §13.6, §16.6 |
| GT-C4 | **`verbosity: concise\|detailed` request knob (§7.6) vs D-15 "never a parameter of the ask."** Plan/industry-consult frames it as orthogonal token-length control; D-15 warns a per-call knob that thins the reading is "a depth axis wearing a token-budget costume." | **CONTRADICTED (potential) — raised** | PARIPRASHNA §13.4 final para |
| GT-C5 | **R-3's unified planner preserves two outcomes; the rebuild needs three.** R-3 emits `PlanReceipt \| fault`; A-29/§6.6 requires a third outcome `ClarificationRequest` + a pre-plan ledger check (§14.7's "strongest compliance-decay mitigation"). The outcome set is a plan-algebra decision (R-3's scope), even if the clarification UX is not. | **UNDER-SPECIFIED — raised** | PARIPRASHNA §6.6, A-29, §9.5 |
| GT-C6 | **The load-bearing consumer contract (`prashna_ask`) is sequenced last (R-5).** PARIPRASHNA T-2 makes it a *core bet*; §19.1 fault 1 is "the core bet was validated last." A thin `prashna_ask` spike earlier would de-risk the headless-engine boundary (F-R1) the plan depends on but does not own. | **SEQUENCING TENSION — raised** | PARIPRASHNA §18/T-2, §6.4.1, §19.1 |

Additional Lane F coverage counts (F-R1..F-R15): **8 COVERED / 4 UNDER-SPECIFIED / 3 CONTRADICTED.** Two
UNDER-SPECIFIED items beyond the contradictions above deserve plan rows: **F-R1** (headless engine
callability — consumed by R-5 but built/owned by neither workstream with a cross-cite) and **F-R7**
(NO-LEAKAGE arms 2 & 4 — `calibration_context_only` exclusion from projections/`prashna_ask` tool set, and
a CI canary — are retrieval-plane concerns the plan does not spell out).

---

## Part D — §3 / §7 / §8 phase-item feasibility notes

Verdict legend: **FEASIBLE** (audit did not change it) · **RE-SCOPED** (audit widened/narrowed the work) ·
**FEASIBLE-BUT-BLOCKED** (a precondition the plan omits) · **ALREADY-DONE** · **NEEDS-RULING** (a raised
contradiction gates it).

### §3 phases

| ID | Phase item | Feasibility verdict | Note (audit impact) |
|---|---|---|---|
| GT-F01 | R-0.1 Rule OT-7 | FEASIBLE | No code; unaffected. |
| GT-F02 | R-0.2 Rule OT-10 (connect-time profiles) | FEASIBLE | Family-resolution plumbing already exists end-to-end (Lane D feasibility notes); profiles buildable as extension. |
| GT-F03 | R-0.3 Adopt reframing into PARIPRASHNA; commit untracked docs | ALREADY-DONE (partial) | Phase-0 of this audit already committed the doc set (`9c358819`). |
| GT-F04 | R-0.4 Sequence against doctrine campaign | FEASIBLE | Unchanged. |
| GT-F05 | R-0.5 Safety patch (fail-open→closed; entitlement on plan_retrieval; parity_check hard-fail) | **RE-SCOPED** | Fail-open is 13 files not one (GT-44); parity_check may be dead/unwired and hard-fails already in the populated case (GT-36) — confirm live status before "fixing" it. Not the clean one-liner PR the plan implies. |
| GT-F06 | R-1.1 Extend CapabilityDescriptor (display/annotations/register/density/mutation/projection_tags/family_overrides) | FEASIBLE | Aligned with Lane F F-R2/F-R6/F-R13. Add `calibration_context_only` flag here for NO-LEAKAGE arm 2 (F-R7). |
| GT-F07 | R-1.2 Build projection compiler | FEASIBLE — input CORRECTED | Compiler must absorb the **6-row** served contract catalog, not the 76-row audit table (GT-3); derive the census from AST/runtime not grep (GT-5, GT-55). |
| GT-F08 | R-1.3 One bootstrap (catalog.ts sole list; route.ts imports it) | FEASIBLE — widen | Must enumerate the 6 live-divergent capabilities (GT-40), not only D9/D10. |
| GT-F09 | R-1.4 Alias cutover ("delete the 41 live aliases + 6 DEFERRED") | **RE-SCOPED (count corrected)** | Live aliases are **55** not 41/45 (GT-5 basis, Lane A §4); 6 DEFERRED reconfirmed; "retired = 4" is **UNVERIFIABLE** (no retire ledger found). |
| GT-F10 | R-1.5 De-mirror by codegen (vidhi, session-pin) | FEASIBLE | Drift already begun (GT-56); session-pin may be moot post-D-16 (GT-7). |
| GT-F11 | R-1.6 Description hygiene (strip native counts; length budgets) | **RE-SCOPED** | Scan must extend beyond `description:` to resource descriptions (PII, GT-42), empty_reason strings (GT-54); reconcile the 601,443 vs 536,471 discrepancy (GT-43). |
| GT-F12 | R-2.1 v3 the only shape; chart_header mandatory, fail-loud | FEASIBLE — reinforced | GT-47 makes the "fail-loud, never silently null" requirement concrete (two current silent paths). |
| GT-F13 | R-2.2 Close flag vocabulary `{code, detail?, severity?}` | FEASIBLE — reinforced | Raw material ready (Lane B closed-enum candidate list). Must also fold in the two static-`[]` emitters (GT-46) and the cross-cutting `finalizeMcpBudget` flag (GT-53). |
| GT-F14 | R-2.3 Self-describing envelopes (register block + reading_contract + epistemic/coverage) | FEASIBLE-BUT-BLOCKED | Token labels feasible; but honesty claim is incomplete without reader-facing signal *text* (GT-C3/F-R8) — flag the dependency. |
| GT-F15 | R-2.4 Cursor integrity (filter/sort fingerprint) | FEASIBLE | Direct fix for GT-14. |
| GT-F16 | R-2.5 One trim discipline; density for all 123 | FEASIBLE — widen | Migrate ~36 unclamped tools (GT-48); `still_over_budget` dead on every path (GT-45); `result_clipper` has a live bulk-context caller to preserve, not just evict (GT-17). |
| GT-F17 | R-2.6 Fix stale provenance semantics | FEASIBLE | Unchanged; Lane E confirms `computed_at` present 39× (provenance partially there). |
| GT-F18 | R-3.1 One scope-tuple vocabulary ("superset mapping … flat") | **RE-SCOPED (structural)** | The flat superset enum **cannot** unify three orthogonal axes (GT-24). Re-scope to a decomposed scope tuple with `IntentClass` derived. This is the single biggest plan correction. |
| GT-F19 | R-3.2 Paripraśna consumes the Vidhi floor | FEASIBLE-BUT-BLOCKED | Floor mechanism is D-15/D-16-safe (Lane F §2), but must co-excise the live `audience_tier` stamp or it lands D-15-dirty (GT-C2). NEEDS-RULING coordination with PARIPRASHNA P2'. |
| GT-F20 | R-3.3 Floor completeness campaign (career/health/marriage; re-derive cr_status; burn 12 dark primitives, CR-56 first) | FEASIBLE | Counts confirmed exactly (GT-25/26/27). CR-55 tri-state must be resolved as part of the re-derivation. |
| GT-F21 | R-3.4 plan_retrieval/vidhi_plan become the same compiled artifact | FEASIBLE | Depends on R-3.1 landing so the DR-8 path reaches domain floors. |
| GT-F22 | R-4.1 Enforce surface spec at edge; MCP-full/compact/consult/chat projections | **RE-SCOPED** | Build the `tools/list`-surface `max_tools` path (missing) but reuse the working bundle-fan-out enforcement (GT-29); `response_format` field must be added to `McpSurfaceSpec` or the `server.ts` read deleted as dead (Lane D §1). |
| GT-F23 | R-4.2 Profile selection = entitlement (OT-10 b+c) | FEASIBLE | Consistent with Lane F F-R15 (projections are not audience tiers — recommend the plan quote §6.5.1 disclaimer). |
| GT-F24 | R-4.3 Annotations + family_overrides live | FEASIBLE | Zero annotations today (GT-30); `family_overrides` subsumes the single `behavioral_overrides` use (GT-31). Dialect/reasoner-capability fields are net-new to `McpSurfaceSpec`/`FamilyNormalization` (Lane D feasibility). |
| GT-F25 | R-4.4 listCapabilities honors full filter set | FEASIBLE — widen | Four ignored fields not three (add `scope`, GT-33). |
| GT-F26 | R-4.5 Foreign-LLM readback battery | FEASIBLE | Unchanged; the measurement leg. |
| GT-F27 | R-5.1 prashna_ask contract | **NEEDS-RULING** | Contract carries forbidden `depth` (GT-C1); depends on headless engine boundary neither workstream owns (F-R1); exposes the loop tool set so NO-LEAKAGE arm-2 exclusion is a hard precondition (F-R7). |
| GT-F28 | R-5.2 Session semantics ("session pin + optional OT-6 journaling") | **NEEDS-RULING** | "Session pin" names and session-state-frames a construct D-16 abolished/restructured (GT-C-adjacent, F-R4). Re-name to provenance stamp; drop the mutable-session framing. |
| GT-F29 | R-5.3 Resilience (rate limits, chaos/load tests) | FEASIBLE | Unchanged. |
| GT-F30 | R-5.4 OT-5 OAuth issuer | FEASIBLE | Unchanged (ruling item). |

### §7 industry-consult amendments

| ID | Item | Feasibility verdict | Note |
|---|---|---|---|
| GT-F31 | §7.1 Per-family schema dialect compiler | FEASIBLE | Net-new fields on `McpSurfaceSpec`/`FamilyNormalization` (input-schema dialect enum, name charset) — buildable as extension, not rebuild (Lane D feasibility notes). |
| GT-F32 | §7.2 Mandatory outputSchema | FEASIBLE | Unchanged. |
| GT-F33 | §7.3 Cache-stable projections | FEASIBLE | Reinforced by GT-8 codegen pattern. |
| GT-F34 | §7.4 family_overrides gains (input_examples, search_result) | FEASIBLE | Unchanged. |
| GT-F35 | §7.5 Errors-as-steering contract | FEASIBLE | Unchanged. |
| GT-F36 | §7.6 verbosity knob | **NEEDS-RULING** | Sits on the D-15 line (GT-C4); reconcile before wiring. |
| GT-F37 | §7.7 Compact-profile size split | FEASIBLE | Ruling RC-1. |
| GT-F38 | §7.8 Tool-search-friendly expert profile | FEASIBLE | Unchanged. |
| GT-F39 | §7.9 Battery extension (tool-selection/agent-task evals) | FEASIBLE | Unchanged. |
| GT-F40 | §7.10 Trust posture (annotations verified) | FEASIBLE | Depends on GT-30 annotations landing (R-4.3). |
| GT-F41 | §7.11 Weak-caller circuit breakers | FEASIBLE | Unchanged. |
| GT-F42 | §7.12 Reasoning-artifact preservation | FEASIBLE | Reasoner-capability flags net-new (Lane D). |
| GT-F43 | §7.13 Corpus-leg retrieval upgrade | FEASIBLE | Unchanged. |
| GT-F44 | §7 ruling rows RC-1/RC-2/RC-3 | FEASIBLE | Unchanged. |

### §8 strategy amendments

| ID | Item | Feasibility verdict | Note |
|---|---|---|---|
| GT-F45 | §8 R-1.5.1 eight-axis rubric census | **RE-SCOPED** | Census harness must grep all three serving paths, not one (GT-51), or it repeats the false-dark error. |
| GT-F46 | §8 R-1.5.2 Coverage doctrine; wire dark set; "L0 reference_*/bg_* catalog stratum (13 tables)" | **RE-SCOPED (count + disposition corrected)** | L0 is **~39 physical tables not 13** (GT-51 basis, Lane E §1); several named "dark" tables (`chart_panchanga`, `bg_dignity_reference`, `bg_sign_medical`) are actually SERVED; 5 `reference_*` are RETIRE not wire-up (GT-52); split "dark-unbuilt" from "dark-unwired" (`kala_timeline`, GT-49); add `ka_graha_sancara` service (GT-50). |
| GT-F47 | §8 R-1.5.3 Close structural register rows (G-1, S-3, SC-2, SC-3..5) | FEASIBLE | All confirmed live-OPEN (Lane E §2(e)). |
| GT-F48 | §8 R-1.5.4 Supersede stale coverage map | FEASIBLE | Unchanged. |
| GT-F49 | §8 R-2 demand-driven serving (demand_ranking, timing hooks, prediction shape) | FEASIBLE | Aligned with Lane F F-R9. |
| GT-F50 | §8 R-3 demand contract (unified tuple everywhere; completeness receipts; get_chart_orientation front door) | FEASIBLE | Depends on the re-scoped R-3.1 (GT-24). |
| GT-F51 | §8 R-4 spine bundles + strategy §7 targets | FEASIBLE | Single cross-layer join confirmed (Lane E §4) — the "hand-stitch everything else" diagnosis holds. |
| GT-F52 | §8 ruling rows RS-1/RS-2/RS-3 | FEASIBLE | RS-2 (dark-table disposition authority) is where GT-49..GT-52 land. |

---

## Part E — Ambiguities / cross-lane divergences (flagged, not silently resolved)

| ID | Item | Nature | Disposition |
|---|---|---|---|
| GT-AMBIG-1 | The catalog count. Lane A: 118 (getCatalog) / 122 (route.ts). Lane B: 115 `server.tool(` sites / 116 `CapabilityDescriptor` consts. Plan: 123. | **Not a contradiction** — the lanes count different objects (registry descriptors reachable via getCatalog vs MCP server.tool sites vs typed consts). | Resolved as GT-1 CORRECTED-APPROX: no single grep reproduces one number; census must be codegen-derived. Flagged for the conductor: do not treat any single count as an invariant. |
| GT-AMBIG-2 | MCP aggregate tool count. Lane A floor ≈145 (from confirmed wrapper expansion); `server.ts` `REGISTERED_TOOL_COUNT`=120; Lane B counts 115 `server.tool(` sites. | Genuine unresolved integer — wrapper-indirection defeats grep; no lane had budget for a full AST pass. | UNVERIFIABLE by design; GT-5. R-1 must derive it from AST/runtime. Native/conductor note: the true live MCP tool count is unknown to ±30 today. |
| GT-AMBIG-3 | "Retired aliases = 4" (plan R-1.4). | No lane could find a retire ledger distinct from the 6 DEFERRED. | UNVERIFIABLE (Lane A §4). A native/implementer ruling or a `git log` archaeology pass could resolve; flagged in GT-F09. |
| GT-AMBIG-4 | PARIPRASHNA target doc internal staleness — its own §6.1 topology diagram still shows `prashna_ask(…, depth)` and "session pin," superseded by D-15/D-16 in the same doc. | Source-doc defect, not a plan defect — but the plan inherited C1/F-R4 from the stale diagram. | Out of this reconciliation's write scope (brief forbids touching PARIPRASHNA). Flagged for the native: correcting the diagram at source would prevent re-inheritance. (Lane F §4.) |

---

## Summary counts

- **Plan §1 factual claims adjudicated:** 37 rows (GT-1..GT-37) — 100% coverage of §1.1–§1.5.
  - CONFIRMED (incl. exactly / with-nuance): 19
  - CORRECTED (incl. CORRECTED-APPROX): 13
  - CONFIRMED + PLAN-ITEM-ALREADY-DONE: 1 (GT-8, partial — codegen exists, CI wiring does not)
  - CONFIRMED-not-reverified (carried forward): 4 (GT-7, GT-31, GT-35, GT-37)
- **NEW-GAP rows:** 17 (GT-40..GT-56)
- **Paripraśna contradictions raised (native rulings):** 6 (GT-C1..GT-C6) + 2 under-specified plane items (F-R1, F-R7)
- **Phase-item feasibility notes:** 52 (GT-F01..GT-F52) — every §3/§7/§8 item covered. FEASIBLE 38 · RE-SCOPED 8 · FEASIBLE-BUT-BLOCKED 2 · NEEDS-RULING 3 · ALREADY-DONE 1.
- **Ambiguities flagged:** 4 (GT-AMBIG-1..4).

*End GROUND_TRUTH_REGISTER v1.0.*
