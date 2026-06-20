---
artifact: CLAUDECODE_BRIEF_BO_SAMVADA_v1_0.md
canonical_id: BO_SAMVADA_BRIEF
version: 1.0
status: FOR_NATIVE_REVIEW (Batch 2/3 — UCD; the chart's GESTALT + the navigable spine of the layer)
authored_by: Cowork (grounded in judgment strategy + all upstream assets) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: bo_samvada ONLY — UCD. ELEVATED from "read-side view" to THIN WRITER (composes + stores the chart gestalt) + a read-side view (raw summaries). Depends on bo_laksana + bo_sangati + bo_karanajala + bo_drishti (it points at all of them).
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — the digest is where the judgment substrate CONVERGES into the LLM's first call)
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (§STORAGE) + L2_BODHA_SCHEMA_REDESIGN_v1_0.md + A14_UCN_RETIRED_TO_UCD_v1_0.md
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
form_decision_2026_06_19: >
  THIN WRITER + VIEW (native). bo_samvada becomes a thin @register('bo_samvada') WriterBase that COMPUTES + stores
  the deterministic GESTALT (bodha_chart_gestalt), AND keeps vw_chart_digest as the read-side join for raw
  summaries. (Supersedes the earlier "Option A: pure view, not a writer" — composing a gestalt is computation.)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py (NEW thin writer — the gestalt)
  - new migration: CREATE bodha_chart_gestalt + CREATE VIEW vw_chart_digest + bo_samvada asset_registry seed
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (query_ucd / the orientation + zoom tools)
must_not_touch: FROZEN orchestrator contract; ga_* writers; the other bo_* writers (it READS their outputs).
---

# bo_samvada — the chart's GESTALT + the navigable spine (the LLM's first call)

## §0 — What this is + why it's deceptively important
bo_samvada is the UCD — Unified Chart Digest — the LLM's FIRST retrieval: the call that gives it the whole chart's
skeleton so its follow-up queries are TARGETED, not scattershot. Base design treated it as a join of summaries.
ELEVATED: it is **the chart's GESTALT** (the master's first impression) AND **the navigable spine** of the whole
judgment substrate (the table-of-contents that lets the LLM zoom gestalt→domain→signal→L1/L0 and back). It is
where the entire layer's work CONVERGES into one orientation surface — and where the two pillars are PROVEN to
meet. Deterministic: the gestalt is composed by versioned formula from upstream pointers; NO LLM, NO narrative,
NO pre-answering — it POINTS to the master's first impression, it does not write the reading.

## §1 — Non-negotiables
Deterministic-first (the gestalt is a deterministic composition of pointers; no LLM); no audience tier; no silent
drops; per-chart isolation; **Trap 1** (the gestalt REFERENCES signature_tier ids / central-dynamic ids / pivot
ids / ledger ids / node ids — never restates values or conclusions); **Trap 2** (no narrative, no judgment — it
points to the ledgers/dynamics, the LLM narrates at serve-time); **POINTS NEVER PRE-ANSWERS** (it assembles "the
chart's defining features + watch-points + central tension as POINTERS" — never "the native is X"); FROZEN
orchestrator contract (`@register('bo_samvada')` WriterBase on ctx.db_conn, never commits, no asset_throughput).

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **bo_laksana + bo_sangati + bo_karanajala + bo_drishti built** (the gestalt points at signature_tier, the
   evidence ledgers, central dynamics, pivots, top-centrality nodes, and the bo_drishti outliers — all must exist).
3. Apply the NEW bodha_chart_gestalt migration + vw_chart_digest view + the bo_samvada asset_registry seed (depends_on the four above).

## §3 — THE GESTALT (the thin writer — composes + stores bodha_chart_gestalt)
Per (chart, ayanamsha), compose the deterministic gestalt as a STRUCTURE OF POINTERS (the master's first impression):

### §3.1 — Chart gestalt / executive summary
- `defining_threads_jsonb` — the chart-defining signature_tier signals (from bo_laksana, tier=chart_defining), ranked.
- `central_dynamics_ids` — the chart's defining cross-domain synergies + tensions (CDLM §C2).
- `pivot_ids` — the chart's pivot factors (CDLM §C3 — the roots explaining the most).
- `center_of_gravity_node_ids` — the top-centrality nodes + final-dispositor (CGM).
- `domain_verdict_map_jsonb` — every domain → its ledger verdict_class + confidence (the strongest + weakest domains visible at a glance).
All POINTERS (Trap 1). Composed by `gestalt_formula_v1` (versioned ranking; deterministic).

### §3.2 — Headline + watch-list + central question (what a master opens with)
- `headline_jsonb` — the chart's DEFINING STRENGTH (top signature thread + strongest domain verdict), as pointers.
- `watch_list_jsonb` — the DEFINING VULNERABILITIES (strongest afflictions + weakest-domain "strongly_against" verdicts + the pivot's risk), as pointers.
- `central_question_jsonb` — the defining ANTAGONISTIC axis (CDLM's strongest tension): "fundamentally a chart where X and Y are at war" — pointers to the two poles + the linking mechanism.

### §3.3 — Judgment inheritance at the digest level (calibrated opening)
- `headline_confidence` + `headline_epistemic_jsonb` — is the dominant signature robust 5/5 ayanamshas or method-dependent? (inherits Move 3). So the LLM opens calibrated, not overconfident.
- `outliers_jsonb` — the "WHAT AM I MISSING" surface: the `non_template_significant` outliers (from bo_drishti) that a master's most valuable observation is often about. The digest LEADS the LLM toward the unexpected.
- `contested_areas_jsonb` — domains/links where evidence is genuinely balanced (CDLM evidence-tension) — so the LLM opens with appropriate humility.

### §3.4 — The navigable ZOOM SPINE (the table-of-contents)
- `zoom_spine_jsonb` — the layered navigation: each gestalt element is a POINTER that drills: gestalt → domain
  ledger → constituent signals → L1 fact_ids + L0 citations. Every level resolvable; every hop carries provenance.
  This is the structure the LLM traverses to move between altitudes (whole-chart ↔ domain ↔ single fact) through
  ONE coherent surface instead of juggling eight tools.

## §4 — vw_chart_digest (the read-side view — raw summaries)
A VIEW joining the chart_summary rows across assets (CDLM chart_summary, CGM topology_summary, RM chart_summary,
the MSR MVs) — the raw digest for when the LLM wants the underlying summaries, not the composed gestalt. No
per-chart table (the view is live). (This is the original "Option A" surface, retained alongside the gestalt writer.)

## §5 — THE PILLARS-MEET PROOF (where completeness + retrievability are PROVEN to meet)
The digest is the ROOT of a navigable graph. Verify (and expose as a standing check bo_pramana_mapa audits):
- **Reachability:** EVERY stored thing (every MSR signal, every ledger, every CGM node, every pivot) is reachable
  from the gestalt in a BOUNDED number of hops via the zoom_spine. Anything NOT reachable from the digest is
  effectively invisible to the LLM — flag it.
- **Provenance at every hop:** each hop carries the fact_id / signal_id / citation so nothing is reached "bare."
This is the concrete point where the two pillars (completeness of storage + retrievability of access) are shown
to MEET. (Dovetails with the B6 eval harness — the eval traverses the digest.)

## §6 — Anti-drift + verification
1. Every pointer in the gestalt (defining_threads, central_dynamics, pivots, ledger refs, node refs, outliers) resolves to a real upstream row (Trap 1; zero unresolved).
2. **No pre-answer:** the gestalt stores NO verdict/conclusion text — only pointers + the (referenced) verdict_class/confidence from the ledgers. Audited.
3. **Reachability proof (§5):** a known signal deep in the weak tail is reachable from the gestalt via the zoom_spine.
4. **Outliers surfaced:** the bo_drishti non_template_significant items appear in outliers_jsonb (the digest leads toward them).
5. Idempotent; no silent drops; FORENSIC unaffected.

## §STORAGE COMPLIANCE (storage §4B)
- **S1** the zoom_spine / reachability may reuse the recursive-CTE traversal (do not build a second traversal engine).
- **S5** headline_confidence, question_type-like facets, chart_id = real columns; the gestalt structures are jsonb (variable, pointer-bearing).
- **S2** chart_id leads indexes. No vector column here (semantic lives in bo_samskara).

## §7 — Retrieval (the orientation payoff)
- `query_ucd(chart, ayanamsha)` → the GESTALT: headline + watch-list + central question + domain-verdict map +
  outliers + contested areas, each a resolvable pointer with confidence + provenance. THE LLM'S FIRST CALL.
- `query_zoom(element_id)` → drills one level (gestalt→domain→signal→L1/L0) via the zoom_spine.
- vw_chart_digest tool → the raw summaries. Coverage gate: the gestalt + view reachable; the reachability proof exercised.

## §8 — Acceptance
- [ ] bo_samvada is a THIN WRITER composing bodha_chart_gestalt (per chart×ayanamsha) + vw_chart_digest VIEW retained.
- [ ] **Gestalt:** defining_threads + central_dynamics + pivots + center_of_gravity + domain_verdict_map — all POINTERS, gestalt_formula_v1 versioned.
- [ ] **Headline + watch-list + central question** composed (the master's opening), as pointers.
- [ ] **Judgment inheritance:** headline_confidence + epistemic + outliers ("what am I missing") + contested_areas.
- [ ] **Zoom spine:** gestalt→domain→signal→L1/L0 navigation, every level resolvable, provenance per hop.
- [ ] **PILLARS-MEET PROOF:** every stored thing reachable from the gestalt in bounded hops; provenance at each hop; reachability check passes.
- [ ] POINTS never PRE-ANSWERS (no verdict text stored; audited). Anti-drift: all pointers resolve.
- [ ] query_ucd + query_zoom + view tools; storage compliance; FROZEN contract; migration + seed fresh.

---

# §ELEVATION (toward supreme)
- **V-1 [retrievability] Question-aware gestalt** — query_ucd(chart, question_type?) optionally biases the gestalt
  toward a question (reusing bo_drishti's lens) while STILL returning the whole-chart skeleton — orient generally OR toward a question.
- **V-2 [judgment] The "one-line chart" pointer** — a single deterministic pointer-tuple capturing the chart's
  essence (lagna + dominant graha + central dynamic) for the LLM's very first orienting glance. Points, never concludes.
- **V-3 [completeness] Per-ayanamsha gestalt diff** — surface where the gestalt itself is ayanamsha-stable vs
  fragile (does the chart's "defining thread" hold across methods?) — Move 3 at the whole-chart level.
- **V-4 [retrievability] Coverage/reachability manifest** — the digest emits the §5 reachability result as data
  (how many stored items reachable / any orphaned), so the pillars-meet proof is a standing, queryable metric.

---
*End of BO_SAMVADA v1.0. Elevated from a read-side join to the chart's GESTALT (the master's first impression:
defining threads + headline + watch-list + central question + domain-verdict map, all as pointers) AND the
NAVIGABLE SPINE (the zoom table-of-contents: gestalt→domain→signal→L1/L0 with provenance at every hop). A thin
writer composes the deterministic gestalt; vw_chart_digest stays the raw-summary view. It carries the judgment
substrate at the digest level (confidence, the "what am I missing" outliers, contested areas) so the LLM's FIRST
call is calibrated and leads toward the unexpected — and it is where the two pillars are PROVEN to meet (everything
stored is reachable from the digest, with provenance). Points, never pre-answers.*
