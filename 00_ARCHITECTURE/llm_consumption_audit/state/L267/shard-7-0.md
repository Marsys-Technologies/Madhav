# Shard 7-0 — SYNTHESIS-CEILING (Lane 7, Charter §4 class 8: UN-SYNTHESIZABLE AT SCALE)

- **Question (heavy):** "Magnitude of wealth — whole-chart, multi-varga convergence — L1"
- **Chart:** `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty)
- **Access path:** deployed MCP connector (read-only public channel), `apex_wealth_assess` + supporting L2/L3 tools
- **Verdict:** CEILING HIT. No serving path composes the answer. Synthesis attempted, could not compose.

---

## 1. Factor census — how many factors this question needs

The question is a whole-chart, multi-varga *convergence* magnitude read. The system's own counters expose the denominator:

| Factor family | Population (system-reported) | Source counter |
|---|---|---|
| Wealth-domain MSR signals | **2,003** | `total_matching_filters` (bodha_signals_get), `signal_id_refs_total` (domain_reading) |
| Constituent fact refs backing signals (this chart) | **67,590** (845 orphaned, 1.3%) | DEFECT-001 note in domain_reading provenance |
| CGM convergence subgraph (wealth) | 10 hub nodes / **107 edges** | bodha_graph_subgraph_get (mode=convergence) |
| Varga facts, per single varga (D9) | **160 facts** | ganita_chart_facts_get returned_count |
| Multi-varga substrate (shodasavarga ≈16 × ~160) | **~2,000–2,560 divisional facts** | extrapolated from D9=160 |
| CDLM wealth cells | 5 | domain_reading cdlm_cells |
| Question lenses (wealth) | 2 | domain_reading question_lenses |
| Activating dasha windows (2026-07→2029) | **0 returned** (kala_activation empty for chart) | apex_wealth_assess.activating_dasha |

**Estimate:** the system must *survey* on the order of **2,000+ wealth-tagged signals + ~2,000 divisional facts + ~100 dhana-yoga graph edges + N dasha windows** (~4,000+ raw factors) to *curate down* to the ~150–400-factor convergence an acharya actually reasons over. The convergence is the whole point of the question and is precisely what no tool computes.

## 2. Ceiling mechanisms observed (receipt-honest evidence)

**(a) Flat top-K walls.**
- `bodha_signals_get` domain=wealth: 2,003 matching → fetch 50 → **hard-cap floor to 10** (`trim_report: signals floored to 10`). Recovery = "paginate via offset" → **~200 pages of 10** to see the population, with no reducer.
- `bodha_graph_subgraph_get`: `top_k:10` hub nodes; 107 edges → **trimmed to 53**; recover_via instrument = `"unknown_tool"` (the connector cannot even name the pagination tool — a receipt-honesty gap in the recovery hint itself).

**(b) Un-budgeted dumps that floor to ZERO (byte ceiling 40,960 B).**
- `bodha_domain_reading_get` domain=wealth: whole response **955,590 B** (~23× ceiling). After flooring *every* section to 0 it is *still* 947,791 B — "base content exceeds budget." `signal_id_refs` floored **200 → 0**. The domain reading returns **zero usable signal references**. Only recovery is `response_format:legacy` (full untrimmed) — i.e., dump the whole 955 KB on the client.
- `ganita_chart_facts_get` D9 alone: whole response **148,997 B** (~3.6× ceiling), facts floored **160 → 0**. **A single varga's facts cannot fit in one response.** Multi-varga convergence (D1+D2+D9+D10+D6+…) in one budgeted call is categorically impossible.

**(c) No map-reduce; the one "composer" punts the core.**
`apex_wealth_assess` is the closest thing to a wealth composer. It:
- bounds to **top-50** composite-ranked signals, displays **top-10** + by_stage (caps_applied: `max_signals_per_lens:10`, `composite_signals_fetched:50`);
- **does NOT compute varga convergence** — `varga_analysis` is a *note + drill_uri* pointer (`marsys://tool/L1/chart_facts_query`), i.e., it hands the multi-varga core back to the client (which then hits the D9=0 wall above);
- returns **0 dasha activations** (temporal axis empty);
- `contradictions: no_data`;
- `citations`: 200 signal_id_refs unresolved, drill pointer only;
- emits a `verdict_skeleton` (literally "skeleton"), `requires_acharya_validation: true`, with the note "No LLM inference." It ranks; it does not *judge magnitude*.

**Net:** every path either walls at top-10, floors to 0, or points elsewhere. Nothing joins signals × vargas × graph × dashas into a magnitude verdict with a ledger. The convergence never happens on any server-side path; the client is structurally forced to hand-assemble ~200 signal pages + N varga dumps (each already over budget) — which the 41 KB ceiling makes impossible in-band.

## 3. P-11 REQUIREMENTS SPEC — what synthesis capability the system would need

To answer a whole-chart multi-varga magnitude question, the serving layer needs, in order:

1. **Map-reduce over signal families (staged retrieval).** Partition the 2,003 wealth signals into dhana families (2nd/dhana, 11th/labha, 9th/bhagya, karaka Jupiter+Venus, named dhana-yogas, dusthana drains 6/8/12). Reduce each family *server-side* to a fixed-size digest (band + top exemplars + count + strength aggregate). Compose the ~6 family digests, not 200 pages of 10. Removes the flat top-K wall.

2. **Cross-varga convergence operator (server-side).** A tool that reads dhana-relevant placements across D1/D2(hora)/D9(bhagya)/D10(karma)/D16/D60, computes vimsopaka-bala / varga-strength convergence, and returns a **bounded** convergence verdict — because raw varga facts (149 KB/varga) can never ship. This is the missing core of the question; today it is a drill_uri only.

3. **Byte-budget-aware progressive summarization.** The 41 KB ceiling *requires* map-reduce: every family and every varga must reduce to a stable fixed-schema digest server-side, never "floor to 0." A digest schema (not raw rows) is the contract.

4. **Narrative-with-ledger composer.** Emit a magnitude verdict as a *band + confidence* (not a raw ranked list), each claim bound to a `DERIVATION_LEDGER` of signal_id/fact_id refs per B.3. Convert `verdict_skeleton` → judged verdict with acharya-reviewable provenance.

5. **Temporal overlay that is actually populated.** Join wealth-yoga signals → `kala_activation` predicates → dasha/bhukti windows so magnitude is time-indexed. Today the join returns 0 for this chart/window — the wealth-signal→activation predicate table is empty and must be filled.

6. **Composing recovery, not pagination hints.** `recover_via` currently says "paginate via offset" or names `unknown_tool`. The system needs a server-side reduce so recovery *composes* the pages, rather than exporting the assembly burden (and a 955 KB legacy dump) to the client.

**Even unreachability shapes the spec:** the fact that a single varga and a single domain-reading each exceed the byte ceiling by 3.6×–23× is the hardest constraint. It proves the answer can only be produced by *server-side reduction to fixed-size digests* — never by shipping factors to the LLM for it to synthesize. The synthesis must move into the serving layer as a map-reduce/convergence operator; the LLM composes digests, not rows.

---

## 4. Independent re-run corroboration (fresh connector pass, 2026-07-12)

A second Lane-7 pass reconfirmed the ceiling and adds three receipts:

- **Signal census (whole chart):** `signature_tier.total = 13,364` MSR signals total; wealth-relevant subset = **2,003** (matches §1). Tier mix of the wealth pool: chart_defining 1.6% (~32), major 14.3% (~286), supporting 83.3%, background 0.8%. The acharya-relevant core (chart_defining + major ≈ **~300 signals**) alone exceeds every top-K wall by an order of magnitude.
- **Empty composition buckets (verbatim from `apex_wealth_assess.verdict_skeleton.by_stage`):** `karaka=[]`, `lord=[]`, `strength=[]`, `varga=[]`, `temporal=[]`, `contradiction_pairs=[]` — only `yoga` populated (5). The stages a wealth-magnitude judgment lives in are structurally empty; the tool ships a skeleton with the load-bearing joists missing. `verdict_skeleton.note` verbatim: "Deterministic classification by signal_type_class + source_subsystem. **No LLM inference.**"
- **Topic-relevance mis-rank:** the 4D composite top-10 is dominated by generic Nabhasa/Chandra yogas (Yuga, Anapha, Kedara, Sasa, Shoola, Vasi, Gola) and `kala_sarpa_per_varga` configuration rows — **not** wealth-specific Dhana yogas (2nd/11th-lord combinations). `class_prior × topic_relevance × intrinsic_strength × structural_role × temporal_activation` surfaces chart-defining yogas by prior, not wealth magnitude by relevance. This is a fourth ceiling mechanism: even the ranked top-K is off-topic for magnitude, so the flat wall does not even show the right 10.

These do not change the verdict — CEILING HIT, synthesis attempted and could not compose — they harden the P-11 spec items #1 (family map-reduce), #2 (varga convergence operator), and #4 (narrative-with-ledger composer to lift the "No LLM inference" gate under governance).

---
*Lane 7 / P-11. Connector calls throttled; no write tools invoked. Byte-trim receipts captured verbatim from `trim_report` / `caps_applied` / `signature_tier` fields. Read-only tools only.*
