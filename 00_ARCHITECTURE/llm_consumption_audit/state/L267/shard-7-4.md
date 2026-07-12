# Shard 7-4 — SYNTHESIS-CEILING (Lane 7 / Charter §4 class 8, UN-SYNTHESIZABLE AT SCALE)

**Heavy question:** Health/longevity multi-factor synthesis (ayus, mrityu, dashas) — L5
**Chart:** 482012f1-710e-4a25-994a-93821f5871aa (Abhisek)
**Channel:** deployed MCP connector (read-only, doctrinal public channel), 130 tools
**Method:** live attempt via connector; no anchors.jsonl read. Verdict: **CEILING HIT.**
**Date:** 2026-07-12

---

## 1. What an acharya-grade ayus/mrityu answer requires (factors needed)

Longevity/health is one of the highest-fan-in questions in Jyotish. A defensible synthesis must
reconcile, at minimum:

- **Ayurdaya** — 3 span methods (Pinda / Amsa / Nisarga): ~8 sub-factors each → ~24
- **Maraka** — 2nd & 7th lords, dispositors, occupants, natural marakas → ~12
- **Badhaka** — badhakesh, badhaka house, aspects → ~5
- **8th house (mrityu/āyus)** — house, lord, karaka Saturn, occupants, aspects, D8 → ~12
- **6th house (roga)** — house, lord, karaka Mars/Saturn, D6 Shashtamsa → ~12
- **Lagna / lagnesh vitality** — shadbala, D1, D9, avastha → ~10
- **Ashtakavarga** — Lagna BAV/SAV bindus over 8th + maraka houses → ~12
- **Dashas across the whole lifespan** — Vimshottari MD/AD/PD activation of maraka/badhaka/8th
  (inherently a birth→death sweep, hundreds of periods)
- **Gochara** — Saturn / maraka-lord transits over sensitive points
- **MSR corpus for this chart** — health lens = **748** matching signals; longevity lens shares the
  same **768** ranked pool; plus cross-linked signals out of the chart's **13,364** total signals.

**Factors-needed estimate: ~1,200–1,800 load-bearing factors**, of which several hundred must be
*actually reconciled against each other*. Squarely class-8 territory.

---

## 2. Did any serving path COMPOSE them? — NO. Ceiling hit.

### 2a. `assess_health` / `apex_health_assess` — map-reduce shape, hollow substance
Advertises the right shape: `handlers_called` = 4 sub-handlers (L2 domain reading, L3 temporal
activation, L2 contradictions, L2 composite ranking). But the composed payload is empty exactly
where the ayus/mrityu factors must live:

- `verdict_skeleton.by_stage`: **yoga=5, karaka=0, lord=0, strength=0, varga=0, temporal=0,
  contradiction_pairs=0.** The lord/karaka/strength/varga/temporal stages — the entire multi-factor
  spine of a longevity read — returned **zero rows**.
- `activating_dasha`: `activations_total_count=0`, `predicates_total_count=0`, `truncated=false` —
  the L3 temporal join produced **nothing** for health. Longevity is a timing question and the
  timing dimension came back genuinely empty (not merely trimmed).
- `varga_analysis`: no D9/D6/D8/Ashtakavarga content — just a `drill_uri` pointer. Divisional
  longevity evidence is punted to a manual drill.
- `house_analysis.question_lenses`: health lens + longevity lens each report
  `all_relevant_ranked_jsonb.total_count = 768` but `signals_per_lens_cap = 10` → **~77:1 collapse**.
- `citations.signal_id_refs`: capped at **200** (of 748 health-matching).
- `entity_profiles`: only 2 of top_k_entities=10 present, **299 signals bucketed "UNATTRIBUTED"** —
  graha-level attribution (which planet drives the affliction, essential for ayus) collapsed into
  one lump; only Ketu (1 signal) individually attributed.
- **Narrative fully suppressed:** `content[0].text` = "[budget-capped response — see
  structuredContent; text duplicate suppressed for this instrument per R5.1 C1]". No prose delivered.
- `judgment_flags[0].requires_acharya_validation = true` — the tool declines to assert the synthesis.
- Digest confirms scale: `msr_signal_count=13364`, health convergence `conv_count=748`.

### 2b. `get_signals` (domain=health) — flat top-K wall, broken pagination
- `limit` **hard-capped at 200** (limit=2000 → `too_big` validation error).
- At limit=200: `returned_count=200`, `total_matching_filters=748`, but
  `pagination = {offset:0, limit:200, total:null, next_cursor:null}` and `truncated:false`.
  **No cursor, no advertised total, 548 signals withheld** — consumer must guess-paginate by manual
  `offset` with no page count. Receipt-honesty smell: `truncated:false` while returning 200/748.
- Each 200-signal page ≈ **218 KB**. Full health lens ≈ 4 pages ≈ ~870 KB — one lens of one domain,
  before longevity, dashas, divisionals, ashtakavarga.

### 2c. `get_domain_reading` (health) — pointer-bag, not a reading
- Returns `question_lenses` (health + longevity) + `cdlm_cells` + `signal_id_refs`.
- `signal_id_refs_total=748`, `signal_id_refs_capped=true`, only **200 refs returned**.
- `token_safety_note`: "Bounded to 3 lenses × 20 signals. Pass max_lenses=12 +
  max_signals_per_lens=100 for full payload." → even the "reading" is a bounded ref list;
  **no narrative-with-ledger** anywhere.

### 2d. `get_dashas` — 10-year slice, not a lifespan
- `total=50` rows, `level: "cap<=3"`, `window: 2021-07-12 → 2031-07-12` (rolling 10-yr default).
  Longevity needs the **whole-life** MD/AD/(PD) sweep to place maraka/badhaka periods; the tool
  returns a 10-year, level-≤3 slice. The lifespan timing spine is unreachable in one call.

### 2e. Receipt-honesty degradation under budget
- **The trim_report is itself trimmed:** `[{path:"(trim_report)", original_count:1, kept_count:1,
  reason:"full trim_report omitted to fit budget", recover_via:{response_format:legacy}}]`. The
  audit ledger is the first thing dropped.
- Narrative text replaced by placeholder; real content only in `structuredContent` — a consumer
  reading the MCP-standard `content[0].text` gets nothing usable.

**Conclusion:** there is a *shape* of composition (`assess_health` calls 4 sub-handlers) but no
*substance*: flat top-K walls (10/lens, 50 composite, 200 citations, 200 refs), empty
lord/karaka/strength/varga/temporal stages, zero dasha activations, a 10-year dasha window, no
divisional/ashtakavarga content, and a suppressed narrative. **No serving path composes the
~1,500 factors into an acharya-grade ayus/mrityu answer.**

---

## 3. P-11 REQUIREMENTS SPEC — what the system would need

Serving layer needs a **staged map-reduce synthesis with a narrative-with-ledger reducer**:

1. **Staged retrieval over factor families, server-side.** Decompose into classical families
   (ayurdaya ×3, maraka, badhaka, 8th, 6th, lagna-vitality, ashtakavarga, dasha-timing, gochara).
   Retrieve *within each family to completeness* — so no family is silently zeroed the way
   `by_stage.{lord,karaka,strength,varga,temporal}` are today.

2. **Map-reduce over families, not a flat top-K.** Map = summarize each family into a bounded,
   faithful family-verdict (score + top constituents + fact_id ledger). Reduce = reconcile the
   family-verdicts into convergences/tensions. The 768→10-per-lens collapse must become
   768→(family summaries) where the reduction is *aggregative*, not *truncative*.

3. **Real pagination / streaming.** `get_signals` must return a working `next_cursor` and a truthful
   `total`, with a completeness contract ("all 748 delivered across N pages"). Manual-offset-without-
   total is not a synthesis substrate.

4. **Lifespan dasha access.** A longevity mode for `get_dashas` returning the full-life MD/AD
   sequence (or maraka/badhaka-filtered periods birth→+100y), not a rolling 10-year, level-≤3 slice.

5. **First-class divisional + ashtakavarga in the reducer.** D6/D8/D9 + Lagna BAV/SAV bindus must be
   pulled and reconciled by the orchestrator, not deferred to a `drill_uri`.

6. **Narrative-with-ledger output.** A composed prose verdict where every clause carries its
   `constituent_facts_array` / `signal_id` ledger (B.3 derivation-ledger mandate), delivered in the
   MCP-standard `content[0].text` — not suppressed to a placeholder with substance hidden in
   `structuredContent`.

7. **Honest, un-budget-dropped receipts.** `trim_report` must survive the budget (it is the audit
   surface); `truncated` must be true whenever rows are withheld; graha attribution must not collapse
   ~300 signals into "UNATTRIBUTED."

8. **Question-sized synthesis budget.** The fixed byte envelope forces the instrument to drop exactly
   the multi-factor content the question needs. Map-reduce over families keeps token cost bounded
   *while* preserving factor coverage — the escalation path a longevity query requires.

**Even unreachable, the shape is clear:** staged retrieval → map-reduce over classical families →
narrative-with-ledger reducer, with honest receipts and lifespan-scoped timing. The present system
has the orchestration *scaffold* (4 sub-handlers) but a *truncative* reducer under a fixed budget, so
it returns a skeleton with the load-bearing stages empty.

---

## 4. Live receipts (captured this run)

| Probe | Key numbers |
|---|---|
| `assess_health` | by_stage lord/karaka/strength/varga/temporal = **0**; dasha activations=**0**; text **suppressed**; lens 768→cap 10; citations cap 200; 299 UNATTRIBUTED; trim_report self-trimmed |
| digest | msr_signal_count=**13364**, health conv_count=**748**, yoga=15, dosha=22 |
| `get_signals` health | limit cap **200**; total_matching=**748**; pagination.total=**null**, next_cursor=**null**; truncated=false; ~218 KB/page |
| `get_domain_reading` health | signal_id_refs_total=**748**, capped=true, returned=**200**; token_safety_note bounds 3 lenses×20 |
| `get_dashas` | total=**50**, level cap≤3, window **2021→2031** only |
