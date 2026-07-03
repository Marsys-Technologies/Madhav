---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT
version: 2.0
status: READY-FOR-EXECUTION — elevated: the as-is audit + the to-be Retrieval Tool Blueprint, for Claude Code
created: 2026-07-02
supersedes: v1.0 (the 3-part coverage audit) — this expands it into the full blueprint per native direction 2026-07-02
author: Cowork (from the live MCP analysis + strategic direction) — for execution by Claude Code in Antigravity
parent: RETRIEVAL_TO_SYNTHESIS_ANALYSIS_AND_INTERVENTION_v1_0
naming_standard_ratified: <layer>_<topic>_<type> (native-approved 2026-07-02) — see §5
why_claude_code: large white-box trace (85 assets × 53 tools) + a spec build; must be produced incrementally
  (layer by layer, tool by tool), saving to committed artifacts so a mid-run drop never loses progress.
single_goal: >
  The LLM, over the MCP channel, EFFICIENTLY and ACCURATELY uses the data from the retrieval tools to generate
  SUPERLATIVE INSIGHT — interpretation, prediction, timing, guidance/remediation, rectification. Every part of
  this brief serves that one goal. A finding, a card, a schema that does not serve LLM synthesis quality is noise.
---

# CLAUDE CODE BRIEF — RETRIEVAL TOOL BLUEPRINT + COVERAGE AUDIT (v2.0)

> **Read this whole brief before starting.** It has two halves. **PART A (as-is audit)** rigorously establishes
> what the 53 retrieval tools currently do against the 85 data assets — coverage, fidelity, astrological
> completeness, output quality. **PART B (to-be Blueprint)** turns that into the reference design that makes the
> LLM produce superlative insight: an insight-type ontology, a per-tool Capability Card for every tool, a
> reasoning-workflow library, a unified output envelope, and a synthesis-quality eval. The blueprint = as-is +
> to-be + how-to-measure, unified. **Save incrementally; commit artifacts as you go.**

---

## §0 — CONTEXT (the accumulated understanding — so you audit with full context, not cold)

**The system.** MARSYS-JIS is an LLM-operated Jyotish instrument. Six layers, 85 Postgres assets, fronted by a
sealed retrieval registry (`platform/src/lib/retrieval`) exposed to LLMs through an MCP server (`platform-mcp`,
53 wired tools). The native chart is 482012f1 (Abhisek); non-native test chart 1c826d5a (Abhinandan).

**The governing frame (apply throughout — every rating is judged by these):**
1. **ASTROLOGICAL-MEANING FIRST.** Each asset is a *topic* (an astrological subject holding meaningful facts),
   not a table. Each tool is judged by the *astrological value* it delivers — does it answer an astrological
   question with astrological logic, and does every element carry its *signification* (what it means, why it
   matters)? The target output is *meaningful, structured, correctly-weighted astrological data*, not clean bytes.
2. **RANKING IS THE CRUX.** Ranking = astrological judgment encoded (what matters). It is the single
   highest-leverage property. Astrological ranking is a COMPOSITE of: topic-relevance (is it a significator of
   the question?) × intrinsic-strength (dignity/shadbala/avastha) × structural-role (yoga/argala/centrality) ×
   temporal-activation (live now via dasha/transit). A single flat salience is the core failure.
3. **1M-CLASS MODELS, ALL FOUR FAMILIES** (Gemini, Claude, GPT, DeepSeek V4 Pro — all ~1M context). No
   small-context floor. Optimum = maximal SIGNAL at volume (organized, ranked, deduped, grounded), served two
   ways: BULK (large pre-assembled organized briefing for one-shot models) and AGENTIC-LOOP (bounded + drill
   pointers for iterative models). DeepSeek reachable in both, but over the plain backend (no MCP connector).
4. **FOUR MEASURES per element end-to-end:** VOLUME (right amount, not noise) · RELEVANCE (pertinent to the
   question) · ACCURACY (astrologically correct + grounded) · RANKING (correctly weighted — the crux).

**The accumulated live findings you inherit (verify, don't re-derive from scratch):**
- Data layer is astrologically COMPLETE + correct at the foundation (natal matches 7 FORENSIC anchors); the
  deficiency is everything downstream of it.
- DEFECT-001: constituent_facts_array → L1 fact_ids resolve at ~8.5% (91.5% orphan) — machine grounding broken.
- Salience is degenerate: for a career query the top signals are 96% ashtakavarga bindu counts (sub-vargas to
  D2700), identical salience, ZERO yogas/10th-lord/raja-yoga; `signature_tier` is 100% "background" (unused).
- Domain filter inert: bodha_question_lenses has no domain column (a career query returns a progeny lens).
- Payloads unbounded: assess_career = 6.2 MB (~1.5M tokens, overflows even 1M); get_positions 63 KB;
  get_cgm_subgraph convergence 53 KB; get_domain_reading was 17 MB → 20 KB after the F-021R bounding fix.
- L3 activation empty: kala_activation / predicates return 0 (yoga_activation_by_dasha → 0 activated yogas) — no timing.
- The apex assess_* tools DO NOT SYNTHESIZE — they dump ingredients (no prose verdict, dasha window empty,
  citations deferred, contradictions as raw UUID pairs with null resolution_hint). "Ships the pantry, not the meal."
- Positives to preserve: tool descriptions are acharya-literate; entitlement/session/auth solid; ephemeris +
  natal compute correct; provenance envelopes + honest self-reporting are exemplary.

**The reframe (why this brief is a Blueprint, not just an audit):** the audit tells us what's broken; it does
NOT tell us what "superlative-enabling" looks like. The tool DESCRIPTIONS + OUTPUT CONTRACTS are the LLM's
*cognitive interface* — the LLM's entire ability to wield the data flows through what each tool tells it and
returns. So we must SPECIFY the tools as that interface (Part B), with the audit (Part A) as the as-is input.

---

## §1 — INPUTS (ground truth)
- **85 assets:** live via the MCP `list_assets` tool OR the asset_registry table. Each row: asset_id, layer,
  target_table, **count_sql** (this ENUMERATES the fact-categories/tables the asset owns — it is the yardstick
  for the asset's FULL content), scope, depends_on. Asset→table pairs are catalogued in the parent analysis doc
  Part 1; the live registry is authoritative.
- **53 tools:** platform-mcp/src/server.ts (registrations) → platform-mcp/src/tools/*.ts,
  platform-mcp/src/tools/retrieval/*.ts, platform-mcp/src/tools/registry_bridge.ts. Registry-bridge tools call
  `marsys://tool/L{n}/name` resolving in platform/src/lib/retrieval/registry/layers/. Others hit the Python
  sidecar (REST) or platform API routes. Trace each to the actual table(s)/capability/endpoint it reads (file:line).

---

## PART A — THE AS-IS AUDIT

### §2 — AUDIT 1: Asset→Tool coverage (completeness of coverage)
For each of the 53 tools: which asset(s)/table(s) does it read? (file:line + the SQL/URI/endpoint). Then INVERT:
for each of the 85 assets, which tool(s) cover it, classified:
- **COVERED** — a tool returns the asset's core content.
- **PARTIAL** — a tool touches the table but only some fact-categories (compare the tool's query to the asset's
  full count_sql category list — e.g. does any tool expose ga_strength's SHADBALA, or only its ashtakavarga?).
- **UNCOVERED** — no tool reads it.
Deliver: (a) tool→table map; (b) asset→coverage table (all 85 rows); (c) the **UNCOVERED list** (assets we built
but cannot retrieve — the headline gap); (d) the PARTIAL list with exactly which content is unreachable.

### §3 — AUDIT 2: Retrieval fidelity per mapping (is full potential realized?)
For each COVERED/PARTIAL asset-tool pair: does the tool retrieve the asset's **completeness + accuracy**?
- Completeness: all meaningful categories the asset holds, or a thin slice? (count_sql list = yardstick.)
- Accuracy/grounding: does it preserve fact_ids/citations? Does DEFECT-001 break provenance on retrieval?
- Check the known degeneracies: ga_strength/bo_laksana salience collapse; bo_upaya remedy scores; ga_dashas
  shadbala-null + pre-birth-sort + default-system; L3 kala_activation empty.
- Rate each: FULL / PARTIAL / DEGRADED, with the specific shortfall + file:line where the query limits it.

### §4 — AUDIT 3: Astrological coverage + output quality
- **Astrological completeness of the SURFACE:** across all tools, is every meaningful astrological aspect
  reachable? Build the checklist from the classical topics: positions, dignities, shadbala (all 6 components),
  ashtakavarga, all vargas D1–D60, aspects (graha + rasi drishti), argala, dispositor chains, yogas, doshas,
  nakshatra substructure (padas, lords, tara bala, gandanta), sahams, arudha padas, karakamsa/swamsa, upagrahas,
  special lagnas, multiple dasha systems (Vimshottari + others), transits, sade-sati, the causal graph,
  cross-domain linkage, remedies, calibration, medical, vastu, prashna, tajaka. Mark each: reachable via which
  tool / NOT reachable. Output the astrological gaps.
- **Output QUALITY per tool** (from code + a live call where possible): is the output COMPLETE (all promised
  fields populated — e.g. assess_* activating_dasha empty, citations deferred), ACCURATE (correct + grounded),
  and OPTIMIZED (bounded? ranked meaningfully? structured by the acharya reasoning chain karaka→bhava→lord→
  dispositor→yoga→dasha, or flat rows? UUIDs resolved to names?). Rate each tool complete/accurate/optimized,
  with the specific defect + file:line.

---

## PART B — THE RETRIEVAL TOOL BLUEPRINT (to-be; the reference design for superlative synthesis)

> Part B defines what the surface SHOULD be. Where a field requires astrological JUDGMENT that is the native's to
> set (ranking priors/weights, what a "correct" reading contains, golden answers), you DRAFT a proposal and mark
> it `[NATIVE-RATIFY]` — never present invented judgment as settled. See §6 for the judgment boundary.

### §B1 — The insight-type ontology (design backward from the outputs)
Define the five insight-types the surface must produce, and for EACH: the astrological question it answers, the
required tool-composition (which tools, in what order), the data it needs, and the ideal output shape.
- **Interpretation** — "what does this chart mean for domain X?" (natal condition → yogas → strength → verdict)
- **Prediction** — "what will happen and when?" (natal potential → dasha/transit activation → anchors + falsifier)
- **Timing** — "when is X ripe / auspicious?" (activation windows, convergence, muhurta)
- **Guidance/Remediation** — "what should be done?" (affliction → remedy resonance → prescription + economics)
- **Rectification** — "is the birth time right?" (LEL fit → candidate times)
Deliver: an ontology table (insight-type → required tools → required assets → output shape), with the
composition/weighting elements flagged `[NATIVE-RATIFY]` where they encode judgment.

### §B2 — Per-tool Capability Cards (the LLM's cognitive interface — the highest-value artifact)
For EVERY one of the 53 tools, a standardized card with these fields:
- **tool** (current name) → **proposed name** (per §5 convention).
- **astrological_purpose** — the question(s) it answers in an acharya's reasoning.
- **source_assets** — the asset(s)/table(s) it reads (from Audit 1).
- **when_to_use / when_not** — selection guidance for the LLM.
- **ranking_logic** — how it weights results today (as-is) and the target composite (to-be, `[NATIVE-RATIFY]` on weights).
- **composition_hints** — which tools it chains with (before/after); its place in the reasoning workflows (§B3).
- **insight_role** — which insight-type(s) it feeds (from §B1).
- **output_contract** — the exact synthesis-ready shape it should return (per the §B4 envelope).
- **as_is_vs_to_be** — current defect (from Part A) vs the target.
- **mode_notes** — how it serves BULK vs AGENTIC-LOOP consumption.
Produce all 53 cards. The card is the deliverable of "significant value" — it is what lets the LLM wield each tool masterfully.

### §B3 — The reasoning-workflow library (the acharya's method, encoded)
For each insight-type, define the canonical astrological TRAVERSAL as a first-class workflow — the ordered
tool-chain an acharya's reasoning follows, e.g. interpretation(career) = orient → 10th-lord condition → D10 →
kāraka strength (Saturn/Sun) → relevant yogas → dāśā activation → contradiction reconcile → verdict. For each
workflow render BOTH: a **bulk bundle** (the pre-assembled, organized, ranked briefing for one-shot models) and
an **agentic drill-graph** (the orient→drill path + pointers for loop models). These workflows double as the
acceptance tests for the eval (§B5). Deliver the workflow library; flag any traversal-logic choice `[NATIVE-RATIFY]`.

### §B4 — The unified output envelope (one synthesis-ready schema for all tools)
Design ONE evidence-envelope schema every tool conforms to, so the LLM gets consistent, composable, weighted
material. It must carry: the reconciled/structured content organized by the reasoning chain (not flat rows);
per-element ranking (the composite score + its components); grounding (resolving fact_id refs + human citation);
insight-type tag; provenance; and be BOUNDED by default with drill pointers + a response_format lever
(minimal/standard/full) for the bulk-vs-loop modes. Deliver the schema (as a spec) + how each current tool maps onto it.

### §B5 — The synthesis-quality eval (how we MEASURE "superlative")
Design a harness: golden questions × the five insight-types × ≥2 charts (native + non-native), each with an
expected acharya-grade answer, run through the LIVE tools + each LLM family, scored on the four measures
(volume/relevance/accuracy/ranking) + insight quality. Deliver: the harness design + the golden-question SET
(the questions are yours to draft; the golden ANSWERS are `[NATIVE-RATIFY]` — an acharya defines "correct"). This
closes the loop: it turns "superlative" from aspiration into a measured target every future intervention is judged by.

### §4B — THE SPEARHEAD (prove the blueprint end-to-end on ONE insight-type first)
Rather than a shallow spec across all five, produce a DEEP, end-to-end worked blueprint for ONE spearhead
insight-type — cards + workflow + envelope + eval — proven on chart 482012f1, as the replicable template.
**Default spearhead: INTERPRETATION** (the foundational insight-type). `[NATIVE-RATIFY: confirm or redirect the
spearhead]`. Do the shallow scaffolding for the other four; the deep proof for the spearhead.

---

## §5 — Tool-naming standardization (ratified convention)
Convention (native-approved): **`<layer>_<topic>_<type>`** — snake_case, NO hyphens (Gemini), ≤128 chars.
- layer: ganita | bodha | kala | phala | mimamsa | ref (L0) | nav (session) | synth (cross-layer reasoning units)
- type: get | compute | search | assess | list | select | record
Deliver a full 53-tool rename table (current → proposed). Examples: get_signals→bodha_signals_get;
get_dashas→ganita_dashas_get; query_chart_facts→ganita_facts_search; get_cgm_subgraph→bodha_graph_traverse;
assess_marriage→synth_marriage_assess; yoga_activation_by_dasha→kala_yoga_activation_get; resolve_entity→
ref_entity_resolve; list_my_charts→nav_charts_list. **PROPOSE only — do NOT execute the rename** (client-breaking;
gate the migration behind native sign-off + an alias/back-compat plan so existing connectors don't break).

---

## §6 — THE JUDGMENT BOUNDARY (what you produce vs what is native-gated — do not cross it)
- **You (Claude Code) produce, from code + classical logic + the tool descriptions:** the entire as-is audit
  (Part A), the tool→asset map, the current output shapes, the Capability Card scaffolding (all
  code-derivable + reasonably-inferred fields), the workflow DRAFTS, the output-envelope DESIGN, the eval HARNESS
  design + golden-question drafts, the rename table.
- **NATIVE-RATIFY (draft + flag, never present as settled):** the ranking priors/weights (what outweighs what),
  the to-be "ideal output" content where it encodes acharya judgment, any traversal-logic choice, and the golden
  ANSWERS (what a "correct" reading is). Mark every such item `[NATIVE-RATIFY]` inline.
- **Never fabricate astrological judgment as fact.** A wrong-guess ranking model presented as settled is the
  exact failure mode this whole effort exists to avoid. Draft, cite reasoning, flag for sign-off.

---

## §7 — VERIFICATION STEP (run this self-check BEFORE declaring the audit done; it gates completion)
Do not report complete until ALL of the following pass, each with evidence:
1. **Coverage completeness:** all **85 assets** appear in the Audit-1 table, each classified COVERED/PARTIAL/
   UNCOVERED; all **53 tools** appear in the tool→table map. No asset or tool omitted. (Count them: 85 and 53.)
2. **Evidence:** every tool→table mapping + every defect cites **file:line**. No unsupported claim.
3. **Fidelity:** every COVERED/PARTIAL asset has a FULL/PARTIAL/DEGRADED rating with a named shortfall.
4. **Astro-completeness:** the classical-topic checklist (§4) is complete; every topic marked reachable-via-X or
   NOT-reachable; the astrological-gap list is explicit.
5. **Output quality:** every one of the 53 tools has a complete/accurate/optimized rating with the specific defect.
6. **Blueprint present:** §B1 ontology (5 insight-types), §B2 Capability Cards (all **53**, no field blank —
   `[NATIVE-RATIFY]` where judgment-gated), §B3 workflow library (all 5 insight-types, bulk + drill renderings),
   §B4 output envelope schema, §B5 eval harness + golden-question set. Confirm each exists.
7. **Spearhead:** the ONE spearhead insight-type has the DEEP end-to-end proof (cards+workflow+envelope+eval) on
   chart 482012f1, with a real sample output; the other four have scaffolding.
8. **Naming:** all 53 tools have a proposed name; the migration is marked PROPOSAL/gated (not executed).
9. **Judgment boundary honored:** every judgment-gated element is flagged `[NATIVE-RATIFY]`; nothing invented is
   presented as settled. (Grep your own output for un-flagged ranking weights / golden answers.)
10. **Frame applied:** every rating is expressed against the four measures (volume/relevance/accuracy/ranking)
    and notes BULK vs AGENTIC-LOOP where relevant.
11. **Incremental-save:** artifacts were written layer-by-layer / tool-by-tool as you went (a mid-run drop would
    have preserved partial progress). Confirm the artifacts are committed.
Emit the verification result as a checklist at the top of the deliverable, each item PASS + evidence, so the
native can see the audit is complete and accurate before reading it.

---

## §8 — DELIVERABLES (commit under 00_ARCHITECTURE/)
- `RETRIEVAL_COVERAGE_MAP_v1_0.md` — Part A Audits 1+2 (tool→table map, 85-asset coverage, UNCOVERED + PARTIAL, fidelity).
- `RETRIEVAL_ASTRO_COVERAGE_AND_OUTPUT_QUALITY_v1_0.md` — Part A Audit 3 (astro checklist + gaps, per-tool output quality).
- `RETRIEVAL_TOOL_BLUEPRINT_v1_0.md` — Part B (ontology + all 53 Capability Cards + workflow library + output
  envelope + eval harness + the spearhead deep proof). This is the reference design.
- `MCP_TOOL_NAMING_STANDARD_v1_0.md` — the convention + full 53-tool rename table + alias/migration plan (proposal).
Each saved incrementally; each opens with its slice of the §7 verification checklist.

## §9 — CONSTRAINTS
Read-mostly: produce the audit + blueprint artifacts; make NO product code changes (the rename + the
blueprint's to-be schema are PROPOSALS, gated on native sign-off). Cite file:line throughout. Where a live call
clarifies output quality, mint an MCP key via POST /api/mcp/keys (code path, not hand-SQL). Honor §6 (never
fabricate judgment). Accuracy over speed. Save incrementally.

*End of CLAUDECODE_BRIEF_RETRIEVAL_TOOL_BLUEPRINT_AND_AUDIT v2.0 — the as-is audit + the to-be blueprint, unified,
with a gating verification step, sized for incremental Claude Code execution toward the single goal: superlative
LLM synthesis over the MCP channel.*
