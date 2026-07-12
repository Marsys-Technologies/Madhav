# Shard 7-3 — SYNTHESIS-CEILING (Lane 7 / Charter §4 class 8: UN-SYNTHESIZABLE AT SCALE)

- **Question (P-11):** "Marriage/relationship full dossier synthesis (Mercury-standard depth) — L4" for chart `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek).
- **Channel:** deployed MCP connector (read-only, doctrinal public channel), `amjis-mcp-qm256lasva-el.a.run.app`, 130 tools.
- **Verdict:** CEILING HIT. No serving path composes the factors this question needs. The relationship domain carries **7,014 signals** (2nd-densest domain after career); every path either flattens it to ~10–20 ranked items, dumps its 7,014 UUIDs raw (0.8 MB) with no synthesis, or returns EMPTY exactly where marriage depth lives (D9 varga, dasha timing, forward projections). Nothing joins structure to timing.

---

## 1. Factors the question actually needs (estimate)

A Mercury-standard marriage dossier is a multi-axis reconciliation, not a single lens:

| Axis | Population observed on the wire | What the acharya answer needs |
|---|---|---|
| Relationship signals (structural) | **7,014** in-template / **7,034** relevant (`apex_marriage_assess` marriage lens `template_count` / `total_count`; corroborated by `get_signals(domain=relationship).total_matching_filters=7014` and `get_domain_reading.signal_id_refs_total=7014`) | top ~100–300 ranked with content, not 10 |
| Classical marriage anatomy | 7th house + 7th lord dignity/aspects; Venus & Jupiter kārakas; **D9 navāṁśa** (lagna, 7th, Venus, UL); Upapada Lagna + lord + 2nd-from-UL; Darākāraka (Jaimini); 2nd/4th/8th/12th bhāvat-bhāva; Kuja/Maṅgala dosha from Lagna+Moon+Venus; Rāhu/Ketu axis; D30 | each computed and reconciled across traditions |
| Temporal (marriage timing) | Vimśottarī chain = **88 periods** available (`get_dashas.total=88`); antardaśā activation of 7th-lord/Venus/UL | per-window marriage activations, ~10–15 salient windows |
| Cross-domain (CDLM) | 5 relationship cells surfaced | which shared signals drive linkage |
| Graph (CGM) | 7th-lord neighborhood, convergence hubs | 7L/kāraka/D9 paths mapped onto the arc |

**Composition space** ≈ 7,014 relationship signals × the classical anatomy above × the dasha timeline. A well-formed answer is roughly **250–400 composed factors** (ranked signals bound to the 7th-house/kāraka/D9/UL frame and mapped onto the marriage-activating daśās, each carrying a ledger). "N-hundred" is the floor.

---

## 2. Does any serving path COMPOSE them? No. The walls, with receipts.

### Wall A — Flat top-K caps (structural side collapsed to a token)
- `apex_marriage_assess` (delegates to `assess_marriage`): marriage lens `all_relevant_ranked_jsonb` → `total_count=7034`, `template_count=7014`, `ranked_signals` len=**10**, `truncated=True`. Also `verdict_skeleton.top_10_composite` len=**10**; `house_analysis.signals_per_lens_cap=10`; `karaka_analysis.cdlm_cells` len=**5**. The full dossier is answered off the top 10 of ~7,000.
- `get_chart_orientation` (mandatory first call): `content.top_signals` len=**10** (filters say `top_k:20`, 10 returned); `entity_profiles` len=2. Whole-chart entry point is a 10-signal skim of a 13,364-signal chart (`digest.msr_signal_count=13364`).
- `get_cgm_subgraph(mode=convergence, query="marriage relationship spouse")`: `hub_nodes` len=**10** (`top_k=10`), `topology_summary=null`. Convergence hubs flat-capped at 10.
- `get_domain_reading(domain=relationship)`: 2 lenses × ~10 ranked signals + `cdlm_cells` len=5.

### Wall B — Un-budgeted raw-UUID dump (0.8 MB of receipts without content)
`apex_marriage_assess` payload = **813,072 bytes**; the text channel is a stub (`"[large payload — see structuredContent]"`, len 39) and the whole thing is shoved into `structuredContent`. The bulk is `house_analysis.question_lenses` = **814,414 bytes** for just **2 lenses**, of which `template_element_ids_jsonb.signal_ids` = a bare list of **7,014 UUIDs** per lens (280 KB + 528 KB, no summaries, no scores). The actually-synthesized `all_relevant_ranked_jsonb` is ~2 KB (10 signals). **0.8 MB shipped; ~20 signals usable.** Meanwhile `grounding.grounding_score=None`, `grounding.fact_ids=[]` — the dump carries no derivation ledger.

### Wall C — get_signals cannot walk the tail (RECEIPT DISHONESTY)
`get_signals(domain=relationship, limit=200)` (200 is the hard max — `limit:500` → `-32602 too_big, maximum:200`): returns `signals` len=200, `total_matching_filters=**7014**`, **`truncated: false`**, and `pagination={offset:0, limit:200, total:null, next_cursor:**null**}`. So the receipt claims "not truncated" while **6,814 of 7,014 signals are unreachable** and there is **no cursor to continue**. Salience of the returned 200 spans 2.3 → 0.489; the entire lower-salience tail is simply gone. The signals themselves ARE content-rich (summary, citation, valence, `constituent_facts_array`) — proving the data exists and only the serving budget/pagination is the wall.

### Wall D — Marriage TIMING and D9 depth return EMPTY where they matter most
- `apex_marriage_assess.activating_dasha`: `activations` len=**0**, `activation_count=0`, `predicates=[]`, `signal_id_refs=[]`. The single most important marriage question — *when* — is unanswered.
- `apex_marriage_assess.varga_analysis`: `{note, drill_uri}` only — **no D9 navāṁśa content**. Navāṁśa is the classical heart of marriage judgment; it is a drill pointer, not composed.
- `get_projections(domain=relationship, horizon_years=10)`: `projections` len=**0**, `signal_id_refs=[]`. Forward marriage windows: empty.

### Wall E — Trim hard-caps with a BROKEN recovery pointer (RECEIPT DISHONESTY)
`phala_outlook_get(horizon_months=24)` returns an explicit `trim_report`: `anchors` `original_count=195 → kept_count=5` (`reason:"floored to 5 (hard-cap)"`), `mitigations` `100 → 10`, `auspicious_windows` `30 → 10`. Each `recover_via.instrument=**"unknown_tool"**` with `hint:"call unknown_tool again…"` — **the recovery instrument literally names no tool**. The client is told the data was trimmed 195→5 and given an un-actionable way to recover it. `summary_confidence=0.322` (low).

### Wall F — Semantic graph entry is broken; only raw UUIDs traverse
`traverse_graph(about="lord_of(bhava 7)")` (the R5 W2 address-expression feature — the natural way to enter the marriage subgraph) → `error:"Could not parse address expression: 'l'"` (parser fails on the first character). Seeding by raw signal UUID works but returns `hub_nodes` len=**10** (`top_k=10`), `topology_summary=null` — a capped neighbor dump, not a composed 7L→kāraka→D9 path. `get_dashas` is the one honest/complete path (`rows=88, total=88`) but it is raw periods with **no marriage-signal binding** — and Wall D shows the binding layer returns 0.

---

## 3. P-11 REQUIREMENTS SPEC — what synthesis capability the system would need

To answer a Mercury-standard marriage dossier, the serving layer needs, in order:

1. **Staged / narrowing retrieval (not flat top-K + UUID dump).** Replace the 10-per-lens cap and the 7,014-UUID raw dump with a funnel: (a) domain filter → relationship signals; (b) composite rank → keep top ~250–300 **with summaries + scores + `constituent_facts` inline** (never bare UUIDs); (c) real cursor pagination for the tail. A "receipt" must be the ranked, summarized signal — and `truncated`/`next_cursor` must be honest (Wall C is a correctness bug: `truncated:false` on 200/7014 with `next_cursor:null`).

2. **The classical marriage anatomy must be COMPUTED, not pointed-to.** D9 navāṁśa (lagna/7th/Venus/UL), Upapada Lagna + lord + 2nd-from-UL, Darākāraka, and Kuja-dosha (Lagna+Moon+Venus) are non-negotiable for this domain and are today either a `drill_uri` (`varga_analysis`) or absent. The assess handler must return these as first-class composed blocks with values, not deferrals.

3. **Marriage-timing spine (structural × temporal JOIN).** Bind the 7th-lord / Venus / UL-lord signals onto the 88-period Vimśottarī chain and return the activating antardaśā windows with salience — the exact object that `activating_dasha.activations` and `get_projections` return **empty** today. Map-reduce shape: for each daśā/antardaśā window, compute the marriage-relevant activation set, summarize to a per-window verdict, fold into a timeline.

4. **Narrative-with-ledger composition.** `assess_marriage` must return a real `verdict` + `ranking_basis` + populated `grounding` (today `grounding_score=None`, `fact_ids=[]`). Each dossier claim carries a DERIVATION_LEDGER (B.3): the L1 `fact_id`s + `signal_id`s + D9/UL cell it rests on. This is the composed acharya-grade output that the top-K / dump / empty-timing layers structurally cannot produce.

5. **Honest trim + working recovery.** Every hard-cap (`phala_outlook` 195→5) must name a REAL recover-via tool + arguments, not `"unknown_tool"`. And large payloads must be budgeted: 0.8 MB of raw UUIDs (Wall B) is pure waste — it costs bytes and yields no synthesis.

---

## 4. Receipt-honesty evidence (captured, per lane mandate)

| Signature | Tool | Receipt on the wire |
|---|---|---|
| Dishonest `truncated` + dead cursor | `get_signals(domain=relationship)` | `returned 200 / total_matching_filters 7014`, `truncated:false`, `next_cursor:null` |
| Capped refs are bare UUIDs | `get_domain_reading(relationship)` | `signal_id_refs_total 7014`, `signal_id_refs len 200`, `signal_id_refs_capped true`, `token_safety_note` present |
| Un-budgeted dump, no ledger | `apex_marriage_assess` | 813 KB payload; `house_analysis` 814 KB = 2× 7,014 raw UUIDs; `grounding_score None`, `fact_ids []` |
| Trim with broken recovery | `phala_outlook_get` | `trim_report`: anchors 195→5 hard-cap; `recover_via.instrument="unknown_tool"` |
| Empty where depth lives | `apex_marriage_assess`, `get_projections` | `activating_dasha.activations=0`; `varga_analysis` = drill pointer only; relationship `projections=0` |
| Broken semantic entry | `traverse_graph(about="lord_of(bhava 7)")` | `error:"Could not parse address expression: 'l'"` |

**Bottom line:** the relationship signal corpus (7,014, content-rich) and the timing chain (88 periods) both EXIST in the store; the ceiling is entirely in the serving/composition layer — flat top-K walls, a megabyte UUID dump, empty timing/varga joins, dishonest receipts, and no map-reduce. Un-synthesizable at scale as served.

---

## 5. Independent second-run corroboration (Lane 7, re-run)

A second independent pass over the deployed connector reproduced the ceiling and confirms every wall above:
- **Wall A/B:** `assess_marriage` = 815,446 bytes; text channel budget-capped (`"[budget-capped response — text duplicate suppressed for this instrument per R5.1 C1]"`), all payload in `structuredContent`. `verdict_skeleton.top_10_composite` len=10, and the top-10 is dominated by **generic non-marriage yoga labels** (Sasa, Shoola, Vasi, Yuga, Gola, Anapha, Kedara) — the flat rank does not even surface marriage-typed items. `caps_applied = {max_signals_per_lens:10, max_contradictions:15, composite_signals_fetched:50}` → 4D ranking only ever sees top-50 of 13,364.
- **Domain-string trap (adds to Wall C):** `get_signals(domain="marriage", top_k=500)` returns `signals:[], returned_count:0, total_matching_filters:0`, and `top_k` silently clamped to `limit:50`. The corpus is stored under domain **`relationship`** (7,014), NOT `marriage` — so the obvious domain string yields a *silent empty*, not an error. Consumer must already know the internal facet vocabulary. `pagination.total:null, next_cursor:null` on this path too.
- **Wall D confirmed:** `assess_marriage.activating_dasha.activations=0` over window 2026-07-12→2029-07-11; `contradictions.status="no_data"`; `varga_analysis` = note + drill_uri only.
- **Wall E confirmed (independent horizon):** `phala_outlook_get(marriage, 12mo)` `trim_report` = anchors **100→5** hard-cap (theirs 195→5 at 24mo), mitigations 100→10, `recover_via.instrument="unknown_tool"`. The 5 kept anchors were `transition_discovery_event`/`career_discovery_event` — **zero marriage-typed** — so even the surviving 5% is off-domain. `get_domain_reading(marriage)` also returned `question_lenses:[], lenses_total:0` (route fragmentation vs. the apex path).
- **Factor estimate** independently landed at ~350–500 composed factors — same order as §1's 250–400. Convergence on "N-hundred, un-composed."

*Two independent runs, one verdict: the data is present; the composition tier is absent.*
