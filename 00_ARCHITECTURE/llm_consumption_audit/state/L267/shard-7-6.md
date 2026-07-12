# Shard 7-6 — SYNTHESIS-CEILING (Lane 7 / P-11)

- **Charter §4 class:** 8 — UN-SYNTHESIZABLE AT SCALE
- **Heavy question (E1):** "Cross-domain life-arc integration (all domains, temporally indexed)" for chart `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek).
- **Channel:** deployed MCP connector (read-only doctrinal public channel), `amjis-mcp-*.run.app`, 130 tools enumerated.
- **Verdict:** CEILING HIT. No serving path composes the factor pool E1 requires. Every synthesis-capable path either flattens to a top-K wall or is temporally indexed only at coarse dasha granularity without integrating the signal/verdict/graph substrate.

---

## 1. What E1 actually requires (factor census, from live receipts)

E1 = every life domain × the full lifespan timeline, integrated into one calibrated, temporally-ordered narrative with ledger. The factor families the system itself exposes for this chart:

| Family | Tool | Universe (receipted) | Served per call |
|---|---|---|---|
| MSR signals | `get_signals` | **13,364** (`signature_tier.metrics.total`) | 50 (flat) |
| Signal refs / domain | `get_domain_reading` (career) | **12,364** (`signal_id_refs_total`) | 3 lenses × 20 |
| Verdict objects | `synth_chart_brief_get` | 38 topic slots / 11 domains | 22 verdicts + 5 LB signals + 5 discoveries |
| Life-arc parvas | `kala_life_arc_get` | ≥50 (`parva_count`=returned, no total) | 50 (flat) |
| Convergence windows | referenced inside parvas | **9,133** (Σ `high_convergence_count` over 50 shown parvas) | 0 enumerated |
| CGM graph | `get_cgm_subgraph` | full `bodha_cgm_nodes/edges` | 10 hub nodes / 107 edges |
| Dasha timeline | `get_dashas` | `chart_dashas` (536k DB-wide; per-chart Vimśottarī L1–L3 = hundreds) | 50 (faceted window) |
| Projections | `get_projections` | 5-yr horizon set | 50 |
| Yogas / doshas | domain digest | 15 yogas / 22 doshas | inline |

**Factor estimate (needed for a genuine E1 answer):** the *composable load-bearing set* is on the order of **300–800 curated factors** (signals that survive salience + convergence + cross-domain linkage), drawn from a **raw retrieval universe of ~22,500+ rows** (13,364 signals + ~9,133 convergence windows + graph edges + dasha nodes + 22 verdicts). E1 is inherently an **N-hundred → N-thousand** reduction problem indexed along a ~90-year timeline.

---

## 2. Where the ceiling is (serving-path analysis)

- **No single path composes across families.** `synth_chart_brief_get` is the only *cross-domain synthesizer*, and it collapses the entire chart to **22 verdicts + 5 load-bearing signals + 5 discoveries** — and it is **NOT temporally indexed** (no dasha/parva axis in the output; `pagination.limit=0`, no depth/expand param).
- **`kala_life_arc_get` is the only temporally-indexed path**, but it integrates *only at coarse dasha-parva granularity*: it emits a per-parva narrative + a `high_convergence_count` **integer** (901, 165, …) and never enumerates, ranks, or interprets those windows. It does not consume MSR verdicts, CGM paths, or projections. It is a timeline skeleton with no flesh.
- **Flat top-K walls everywhere:** signals=50, parvas=50, projections=50, CGM hubs=10, domain reading=3×20. There is **no map-reduce over signal families, no staged/hierarchical retrieval, no narrative-with-ledger that spans domains × full timeline.**
- **Silent clamp:** `get_signals` with `top_k:2000` returns 50 and echoes `filters.top_k:50` with `truncated:false` — the request ceiling is invisible to the caller.

E1 cannot be assembled by the LLM by hand either: pagination to drain 13,364 signals at 50/call = **268 calls** for one family alone; convergence windows are not even enumerable (only counted). The connector's own throttle + byte budget makes brute-force fan-out non-viable, and even a full drain yields an un-reduced dump, not a synthesis.

---

## 3. Receipt-honesty evidence (captured per instruction)

1. **`get_signals` — false `truncated`.** `total_matching_filters=13364`, `returned_count=50`, **`truncated=false`**, `pagination.total=null`. A 267× reduction reported as non-truncated; total hidden in `provenance.signature_tier.metrics.total`, not in the pagination envelope.
2. **`get_signals` — silent top_k clamp.** Requested `top_k:2000` → served 50, `filters` echoes `top_k:50`, no warning/clamp field.
3. **`get_projections` — contradictory receipt.** `projections_total:0` and `projections_returned:0` while `content.projections` carries **50** populated rows.
4. **`kala_life_arc_get` — no total.** `parva_count:50` equals the returned count with `filters.top_k:50`; no total disclosed; 9,133 referenced convergence windows never surfaced.
5. **`synth_chart_brief_get` — no widen path.** `pagination:{limit:0,total:null}`; 38 topics → 5/5 top-K; no depth/expand parameter.
6. **HONEST COUNTER-EXAMPLE — `get_domain_reading`.** `signal_id_refs_total:12364`, **`signal_id_refs_capped:true`**, plus `token_safety_note:"Bounded to 3 lenses × 20 signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload."` This is the correct receipt pattern (true cap flag + total + documented widen params) — the spec below generalizes it.

*Also observed: the S3 "serialization-tax fix" suppresses the `text` duplicate for large payloads (payload lives only in `structuredContent.object`) — benign, but a consumer parsing `content[0].text` gets a stub.*

---

## 4. P-11 REQUIREMENTS SPEC — what synthesis capability E1 needs

To answer E1 the system needs a **compositional synthesis layer** the doctrinal channel does not have today:

**R1 — Staged / hierarchical retrieval (not flat top-K).**
Replace the 50-row wall with a two-tier fetch: (a) a *summary tier* returning family-level aggregates + counts for the whole universe (all 13,364 signals bucketed by domain × dasha-parva × valence × signature_tier), then (b) *drill tokens* to expand any bucket on demand. The domain-reading `max_lenses/max_signals_per_lens` widen-params + `*_capped` flags are the template; make them universal and honest across every tool.

**R2 — Map-reduce over factor families.**
A server-side reducer that, per (domain × parva) cell, maps the salient signals → convergence windows → verdicts → CGM paths and reduces to a bounded, ranked, *ledgered* cell summary. This is the missing join between `kala_life_arc_get` (timeline skeleton) and `synth_chart_brief_get` (domain verdicts). The 9,133 convergence windows must be *reducible*, not merely *countable*.

**R3 — Temporally-indexed synthesis object (life-arc × domains matrix).**
A single asset keyed on `parva_index × domain` whose cells carry: dominant signals (with `constituent_facts` ledger back to `chart_facts`), verdict + calibration band, convergence-window peaks, and a narrative span — i.e. `synth_chart_brief_get`'s verdict depth *stamped onto* `kala_life_arc_get`'s 50-parva timeline. Today these two live in separate tools that never join.

**R4 — Narrative-with-ledger, budget-aware.**
A composer that emits an acharya-grade prose arc where **every clause cites its factor IDs** (B.3 derivation-ledger), with an explicit byte/token budget and an honest `coverage_receipt` stating factors-considered vs. factors-rendered (e.g. "612 of 13,364 signals load-bearing; 50 of 50 parvas covered; 9,133 windows reduced to 41 peaks").

**R5 — Honest receipts as an invariant.**
Every list tool MUST report `{returned, total, truncated=(returned<total), widen_params}`. Kill silent clamps (finding 2), false `truncated` (finding 1), and zeroed totals over non-empty rows (finding 3). Without this, a synthesis client cannot even *know* it is under-reading, so it cannot compensate with fan-out.

**Even unreachability shapes the spec:** the fact that E1 is un-synthesizable today is *because* R2+R3 do not exist. The two halves E1 needs (all-domain verdicts, full timeline) each exist as a top-K flat surface; nothing composes them. The deliverable is the **compositional synthesis layer (R1–R5)**, most critically R2 (map-reduce over families) and R3 (the parva×domain matrix object).

---

## 5. Bottom line

- `synthesis_attempted`: yes — via `synth_chart_brief_get` + `kala_life_arc_get` + `get_signals` + `get_domain_reading` + `get_cgm_subgraph` + `get_projections`.
- `ceiling_hit`: **yes.** Flat top-K walls (50/50/50/10/3×20), no map-reduce, un-budgeted-but-truncated dumps, one synthesizer that is not temporally indexed, one timeline that does not synthesize.
- `factors_needed_est`: ~300–800 load-bearing, from a ~22,500+-row raw universe; N-hundred curated.
- Class 8 (UN-SYNTHESIZABLE AT SCALE) confirmed for E1 on the doctrinal public channel.
