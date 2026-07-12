# Shard 7-2 — SYNTHESIS-CEILING (Lane 7 / Charter §4 class 8: UN-SYNTHESIZABLE AT SCALE)

- **Question (P-11):** "Career trajectory with structural×temporal convergence over lifetime — L3" for chart `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek).
- **Channel:** deployed MCP connector (read-only, doctrinal public channel), `amjis-mcp-qm256lasva-el.a.run.app`, 130 tools.
- **Verdict:** CEILING HIT. No serving path composes the factors this question needs. The structural side over-serves (megabyte UUID dumps), the temporal side under-serves (silent 3-year clamp, zero activations), and nothing joins them.

---

## 1. Factors the question actually needs (estimate)

The question is a JOIN over two large axes plus a graph and a dasha timeline:

| Axis | Population observed on the wire | What the acharya answer needs |
|---|---|---|
| Structural (career-relevant signals) | **12,384** relevant / **12,364** in-template (from `apex_career_assess` question-lens `total_count`; `signal_count`) | top ~100–300 ranked, not 10 |
| Temporal (life parvas) | **50 parvas** spanning 1984→~2064; each carries a `high_convergence_count` (parva 1 = **901**, parva 26 = 189) | per-parva career-filtered convergence windows, ~10–15 career-salient parvas composed |
| Convergence windows | thousands (901 in a single parva alone) — only the COUNT is surfaced | the windows themselves, crossed against career signals |
| Cross-domain (CDLM) | 5 career cells; `shared_signal_count` up to **6,294** (career×character) | which shared signals drive linkage, not the aggregate |
| Graph / dasha | CGM subgraph + full Vimśottarī lifetime sequence | 10th-lord / kāraka / D10 paths mapped onto the dasha arc |

**Composition space** ≈ 12k structural × thousands of temporal windows ≈ **~10^7 candidate pairs**, which MUST be reduced. A well-formed answer is roughly **200–400 composed factors** (ranked career signals mapped onto ~10–15 life parvas with their convergence windows, each carrying a ledger). "N-hundred" is the floor; the raw candidate space is ~10^7.

---

## 2. Does any serving path COMPOSE them? No. The walls, with receipts.

### Wall A — Flat top-K caps (structural side truncated to a token)
`apex_career_assess`: `verdict_skeleton.top_10_composite` len=**10**; `signals_per_lens_cap=10`; `caps_applied={max_signals_per_lens:10, max_contradictions:15, composite_signals_fetched:50}`. `all_relevant_ranked_jsonb`: `total_count=12384`, `ranked_signals` len=**10**, `truncated=True`. The lifetime convergence question is answered off the top 10 of 12,384.

### Wall B — Un-budgeted raw-UUID dumps (receipts without content)
- `apex_career_assess` payload = **1,046,166 bytes**. The bulk is `question_lenses[0].template_element_ids_jsonb.signal_ids` = a bare list of **12,364 UUIDs** (no summaries, no scores) plus `citations.signal_id_refs` len=200 (UUIDs only, real citations behind a `drill_uri`).
- `bodha_domain_reading_get(domain=career)` payload = **6,312,158 bytes** (6.3 MB) — two lenses each re-dumping the 12,364-UUID list. Simultaneously its `trim_report` says `content.signal_id_refs: floored to 0 (hard-cap)` (`original_count=200 → kept_count=0`) with `signal_id_refs_total=12364, signal_id_refs_capped=True`. **It ships 6.3 MB of raw UUIDs while hard-capping the actual ref list to zero** — the payload is large and useless at the same time. `recover_via.hint`: "call again with a narrower filter/date_range" — i.e., the client is told to shard the query by hand.

### Wall C — Silent temporal-window override (RECEIPT DISHONESTY)
`kala_yoga_activation_get` called with `{date_from:"1984-02-05", date_to:"2064-01-01", top_k:500}` → response `query_window` and `filters` came back **`2026-07-11 → 2029-07-10, top_k:30`**. The lifetime parameters were **silently discarded and replaced with the 3-year forward default, with no warning field**. The whole "over lifetime" clause is unserviceable and the tool does not admit it.

### Wall D — Temporal join returns EMPTY for career at every window
Across `apex_career_assess.activating_dasha.activations` (len 0), `kala_yoga_activation_get` (0), `get_temporal_windows(career)` (`activations` 0, `top_signals` 0, window clamped to 2026→2027). The structural×temporal convergence — the literal subject of the question — is **not computed by any tool**; every temporal handler returns zero activations bound to a ≤3-year forward window.

### Wall E — Lifetime arc is a chart-wide templated stub, not a composed career narrative
`kala_life_arc_get`: 50 parvas, but `verdict=None`, `ranking_basis=None`, `grounding.citations` len=0. Each parva `narrative` is a fill-in-the-blank stub ("Jupiter daśā (1984–1991): consolidating phase… 901 high-convergence windows in this span"). `dominant_signal_class=DISPOSITOR_RELATIONAL` — **not career-filtered** (no domain parameter). The 901 windows are counted, never enumerated, never crossed with career signals.

### Wall F — Trim/aggregation primitives exist but are capped far below need
- `kala_projections_get`: honest `trim_report` (`original_count=50 → kept_count=25`) but `filters.horizon_years=3` — 3-year horizon, not lifetime.
- `get_temporal_windows` provenance reveals a real family-aggregation map-reduce ("300 atomic candidate signals → 67 families → 2 entities", E-6/R5.1). But it caps at **300** atomic candidates (vs 12,384 needed) and still returns 0 career activations.

---

## 3. P-11 REQUIREMENTS SPEC — what synthesis capability the system would need

To answer this class of question the serving layer needs, in order:

1. **Staged / narrowing retrieval (not flat top-K).** Replace the 10-per-lens cap + 12k-UUID dump with a funnel: (a) domain filter → career-relevant signals; (b) salience/composite rank → keep top ~200–300 with their scores+summaries inline (never bare UUIDs); (c) cursor pagination for the tail. A "receipt" must be the *ranked, summarized* signal, not its UUID.

2. **Lifetime temporal spine with an honored window.** `date_from/date_to/top_k` must be respected (or explicitly rejected with a stated max), never silently clamped. The temporal engine must serve the full Vimśottarī arc (birth→~+80y), returning per-parva/per-window activations, not a 3-year forward stub. The silent-clamp behavior (Wall C) is a correctness bug that must be fixed before any lifetime question is answerable.

3. **Map-reduce over parva families (structural × temporal JOIN).** The 50 parvas × ~thousands of convergence windows × 12k signals must be reduced server-side: for each parva, compute the career-filtered convergence set (the `high_convergence_count` should be *drillable to its members*, filtered by domain), summarize to a per-parva career verdict + top drivers, then fold the 50 parva-summaries into one lifetime arc. The existing E-6 family aggregation (300→67→2) is the right shape but must scale past its 300-candidate cap and accept a domain filter.

4. **Narrative-with-ledger composition.** `kala_life_arc_get` must return a `verdict` + `ranking_basis` + `grounding.citations` (today all null/empty). Each phase claim carries a DERIVATION_LEDGER (B.3): the L1 fact_ids + signal_ids + parva_ids it rests on. This is the composed acharya-grade output the top-K/dump layers cannot produce.

5. **Budget-honest envelopes.** A payload must not be 6.3 MB of UUIDs while its own `trim_report` floors the useful list to 0. Byte budget should be spent on ranked, summarized content; overflow is signalled via `pagination.total` + `next_cursor`, and every discard is disclosed in `trim_report` (the projections tool already models this correctly; the domain-reading/career-assess tools do not).

**Synthesis attempted:** yes — I gathered from `apex_career_assess`, `bodha_domain_reading_get`, `kala_life_arc_get`, `kala_projections_get`, `kala_yoga_activation_get`, `get_temporal_windows`. The structural axis is retrievable only as top-10 + a UUID dump; the temporal axis returns empty under a silently-clamped 3-year window; nothing joins them into the lifetime convergence arc. An acharya-grade answer could **not** be composed from any single path or any feasible stitch of these paths — the JOIN is not served and the lifetime window is not honored. Even the unreachability is diagnostic: it defines requirements 1–5.

---

## 4. Receipt-honesty evidence captured (byte-budget / trim)
- `apex_career_assess`: 1.05 MB; 12,364-UUID dump; `truncated:True`; `caps_applied` present (honest about caps, dishonest about the 12k dump).
- `bodha_domain_reading_get(career)`: **6.3 MB**; `signal_id_refs_capped:True`, `signal_id_refs_total:12364`; `trim_report` floors refs to 0 while payload ships megabytes of UUIDs.
- `kala_projections_get`: honest `trim_report` 50→25, but `horizon_years:3`.
- `kala_yoga_activation_get`: **silent param override** — lifetime request answered with default 3-year window, no warning (worst receipt-honesty failure found).
- `get_temporal_windows`: window silently 1-year; 0 activations; family-aggregation note (300→67→2) reveals a capped map-reduce primitive.

---

## 5. Run-2 confirmation + new receipts (independent re-probe)

A second independent gather reproduced Walls A–F and adds these receipts:

- **Lifetime coverage of the arc quantified.** `kala_life_arc_get` parvas span **1984→2054** across **50 parvas**; summing `high_convergence_count` = **9,133** convergence windows across the lifetime (parva 1 Jupiter=901 … parva 50 Ketu=0). Confirms Wall E: 9,133 windows *counted*, none enumerable/career-filterable; `grounding.fact_ids=[]`, `verdict=null`, `pagination.total=null`.
- **Full-lifetime window still returns ZERO (with correct param names).** `kala_yoga_activation_get{start_date:1984-02-05,end_date:2064-02-05,limit:500}` → `total_count=0`, echoed window correct BUT `filters.top_k` silently clamped to **200**. `get_temporal_windows{...include_convergence:true, 1984→2064}` → `activations=0, predicates=0`. Strengthens Wall D: the structural×temporal join is empty even over the honored full-life window — not just a clamp artifact, the career convergence data is simply not served.
- **False step-OK receipt (new receipt-honesty defect).** `apex_career_assess.step_results.temporal.ok=True` while `activating_dasha.activations=[]` (count 0). A consumer trusting `ok` flags would report convergence it never received.
- **Graph traversal for career errors out.** `traverse_graph{about:"career",depth:3}` → `error:"Could not parse address expression: 'c'"`; falls back to an `orientation_context` digest (which does confirm `convergence_domains[career].convergence_count=12364`, `msr_signal_count=13364`). The walk that would compose graph paths fails; only the aggregate survives.
- **Broken temporal join, disclosed.** `kala_yoga_activation_get` provenance `DEFECT-001`: `total_refs=67,590`, `orphan_refs=845`, `orphan_pct=1.3` — the kala_activation join carries 1.3% dangling refs (status MOSTLY_RESOLVED, expires 2026-07-13).
- **Dasha spine capped at 50.** `get_dashas` → `rows=50, total=50` (parva grain), consistent with the 50-parva arc.

**Reconciled factor estimate:** raw candidate space ~10^7 pairs (≈12.4k career signals × ~9.1k lifetime convergence windows); a well-formed acharya answer reduces to ~**200–400 composed factors** (top-ranked career signals mapped onto ~10–15 career-salient parvas, each ledgered). Floor is "N-hundred"; the raw space is ~10^7. No served path performs this reduction; class 8 (UN-SYNTHESIZABLE AT SCALE) confirmed by two independent runs.
