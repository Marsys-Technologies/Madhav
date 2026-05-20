---
canonical_id: DASHA_CORRECTNESS_RESEARCH
version: 1.1
status: APPROVED — execution plan at PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN_v1_0.md
author: Claude (analysis stream)
authored_on: 2026-05-19
amended_on: 2026-05-19
scope: research-dossier-only
problem_class: hallucination — pretrained-LLM-knowledge displaces ground-truth data
symptom_class: wrong next/upcoming Vimshottari MD (e.g., "Saturn MD next" when correct answer is "Ketu MD")
two_stream_branch: analysis/backend-data-pipeline-perf-audit
related: EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md (peer dossier — same pattern of "data correct, planner can't reach it"), PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN_v1_0.md (execution plan)
changelog:
  - v1.0 (2026-05-19): initial dossier with 5-layer diagnosis + outstanding decisions
  - v1.1 (2026-05-19): native approved all 5 default decisions; status → APPROVED; execution plan authored
---

# Dasha Correctness — Research Dossier

## §0 Purpose

The native reports systematic failures where synthesis claims "Saturn MD next" (or other wrong next-dasha lord) despite the actual Vimshottari sequence putting **Ketu MD next** (2027-08-21 → 2034-08-21). The error pattern is hallucination, not a numerical bug in the upstream compute. This dossier traces the failure end-to-end and proposes a five-layer structural fix that makes the mistake impossible.

## §1 What's correct (upstream)

### §1.1 The compute is right

`platform/scripts/temporal/compute_vimshottari.py` defines the canonical Vimshottari cycle:

```python
VIMSHOTTARI_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars",
                      "Rahu", "Jupiter", "Saturn", "Mercury")
VIMSHOTTARI_DURATIONS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
```

The cycle is correct (canonical Parashari order). `ad_sequence()` correctly returns the 9 AD lords starting with the MD lord then cycling forward. `md_sequence()` cyclically advances. The subdivision math (`MD_full × AD_lord / 120`) is canonical. The partial-first-MD scaling via `balance / md_full` is right.

### §1.2 The output JSON is right

`05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json` contains 7 MDs, 63 ADs, 567 PDs (1984-02-05 → 2070-08-18). MD entries explicitly:

```
Jupiter:  1984-02-05 → 1991-08-19
Saturn:   1991-08-19 → 2010-08-18   ← historical
Mercury:  2010-08-18 → 2027-08-19   ← current
Ketu:     2027-08-19 → 2034-08-18   ← NEXT
Venus:    2034-08-18 → 2054-08-18
Sun:      2054-08-18 → 2060-08-18
Moon:     2060-08-18 → 2070-08-18
```

### §1.3 The FORENSIC §5.1 table is right

`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1` lists 50 MD/AD rows `DSH.V.001` through `DSH.V.050+`, dates 1984-02-05 → 2060-08-21. Mercury MD: rows 015–023 (Mercury–Mercury → Mercury–Saturn). Ketu MD: rows 024–032. Venus MD: 033–041. Per FORENSIC governance, these dates are canonical (GAP.09 resolved 2026-04-19 — FORENSIC dates over JH dates).

### §1.4 The chart_facts data is right

`01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` contains all 50 rows as `category: dasha_vimshottari` facts with `value_json: {md_lord, ad_lord, start_date, end_date}`. `forensic_extractor.py` upserts these into the `chart_facts` Postgres table. Mercury MD + Ketu MD + Venus MD all present in DB.

### §1.5 The sidecar `dasha_chain.py` is right

`/dasha_chain` endpoint extends the DB-derived MD schedule both backward (to 1900-01-01) and forward (to 2100-12-31) algorithmically using `_sequence_from(lord)` which correctly cycles Ketu→Venus→…→Mercury and wraps. The 5-level chain (MD/AD/PD/SD/PD2) at any date is correctly computed via proportional subdivision.

**Conclusion of §1**: every upstream component is mathematically and semantically correct. The bug is not in the data.

## §2 Where the failure lives — five layered gaps

The synthesis layer produces wrong next-MD claims because of a **discoverability + delivery + grounding-discipline** failure stack, not a numerical bug.

### §2.1 Gap A — `chart_facts_query` doesn't advertise dasha categories to the planner

**Source**: `platform/src/lib/router/retrieval_capability_spec.ts`, entry `chart_facts_query`.

The RCS description lists categories the planner can pass:

> "37 categories (shadbala, ashtakavarga, bhava bala, sahams, yogas, longevity indicators, upagrahas, mrityu bhaga, avastha, planet placements, house contents)"

The supported_params example list includes `"shadbala", "ashtakavarga_bav", "bhava_bala", "saham", "yoga", "planet", "house", ...` — but **NOT** `dasha_vimshottari` / `dasha_yogini` / `dasha_chara`. The optimal_patterns include yoga lookups, saham lookups, BAV by planet — no dasha pattern.

But the TS code itself (`platform/src/lib/retrieve/chart_facts_query.ts`) declares the full enum including `'dasha_vimshottari' | 'dasha_yogini' | 'dasha_chara'`. The tool's implementation accepts these; only the RCS description hides them.

**Effect**: the LLM-first planner reads RCS and concludes that `chart_facts_query` is for chart placements / strengths / yogas — not dashas. So for a query like "what's my next MD?", the planner doesn't schedule `chart_facts_query` despite the answer being one row away in the DB.

### §2.2 Gap B — `temporal` returns only the active chain at one date, not the next MD

**Source**: `platform/src/lib/retrieve/temporal.ts`, lines 106–120.

When `dasha_context_required=true`, the tool calls `/dasha_chain` with a single date (today, or `time_window.start`). The endpoint returns the 5-level MD/AD/PD/SD/PD2 active at that one date.

It does NOT return:
- The next MD after the current one
- The full upcoming MD schedule
- Any forward-looking dasha context

**Effect**: even when the planner correctly schedules `temporal` for a "what's my next dasha?" query, the tool gives synthesis the current chain (Mercury MD / Saturn AD / …), not the next chain. Synthesis is forced to extrapolate "next" with no data.

### §2.3 Gap C — `timeline_query` warning lives in the wrong layer

**Source**: `platform/src/lib/retrieve/timeline_query.ts`, lines 8–9.

A hardcoded warning sits in the file header:

> "IMPORTANT: The next MD after Mercury is KETU MD (2027-08-21 → 2034-08-21). Never suggest Saturn MD as upcoming — Saturn MD was historical (1992-2010)."

But:
- This is a **code-level docstring**, not a prompt the LLM ever sees
- The corresponding RCS entry surfaces it to the planner, but synthesis never reads RCS
- The tool itself does `ILIKE` over `rag_chunks WHERE doc_type='l5_timeline'` filtering by `dasha_name`. If the planner doesn't pass `dasha_name='Ketu MD'` (because that requires already knowing the answer), the tool returns nothing useful for "next dasha" queries.

**Effect**: the warning is in the wrong place to actually prevent the hallucination.

### §2.4 Gap D — FORENSIC §5.1 IS delivered, but buried in 1900 lines

**Source**: `platform/src/lib/bundle/bundle_hydrator.ts` + FORENSIC as floor asset.

The bundle hydrator enforces FORENSIC as a floor asset (always loaded). FORENSIC §5.1's full 50-row dasha table IS in the synthesis context window — embedded in a ~75 KB document that also contains §1–§26 with chart facts, sahams, yogas, KP cusps, BAV, varshphal, etc.

LLM behavior with large contexts: attention degrades on specific sections of long documents, especially numeric tables. The model knows §5.1 exists; reading 50 rows to find "the row after Mercury–Saturn" reliably is a needle-in-haystack task that pretrained "Vimshottari cycle from memory" displaces.

**Effect**: the LLM defaults to pretrained dasha-sequence knowledge (which is noisy across training data) instead of carefully reading §5.1.

### §2.5 Gap E — no synthesis discipline gate + no post-synthesis validator

**Source**: `platform/src/lib/prompts/templates/predictive.ts` + `platform/src/lib/checkpoints/`.

The predictive synthesis prompt has gates for: B11 explicit-layer citation, falsifier, calibration language, DBN posterior framing, prescriptive citation. None of them say:

> "Before claiming any 'next/upcoming/previous' dasha, you MUST consult the dasha_vimshottari rows in the bundle and cite the specific DSH.V.NNN row(s) for your claim."

And `checkpoint_4_5.ts` / `5_5.ts` / `8_5.ts` exist as post-synthesis validators (for forensic-citation density, B11 discipline, etc.) — none of them cross-check dasha claims against `chart_facts`.

**Effect**: even when the right data is in context, synthesis isn't required to use it, and a wrong claim isn't caught after the fact.

## §3 Root cause in one sentence

> The Vimshottari schedule is correct everywhere it's computed and stored, but synthesis is neither **mandated** to consult it nor **caught** when it doesn't, and the LLM's pretrained knowledge of the cycle is uneven and easily displaced by the historical Saturn MD that sits prominently in the FORENSIC document.

## §4 Proposed structural fix — five layers of defense

Each layer alone reduces the failure rate. All five together make the failure structurally impossible.

### §4.A — RCS discoverability fix (smallest; immediate win)

Update `chart_facts_query`'s RCS entry to advertise dasha categories with optimal_patterns. Add patterns:

- "Current MD/AD/PD: {category:'dasha_vimshottari', as_of_date: 'today'}"
- "Next N MDs from a date: {category:'dasha_vimshottari', from_date: 'today', limit: 12}"
- "Specific dasha lord history: {category:'dasha_vimshottari', md_lord:'Mercury'}"

Also extend `chart_facts_query.ts` to support `as_of_date` and `from_date` JSON-path filters against `value_json->>'start_date'` and `value_json->>'end_date'`. Currently neither is supported.

**Cost**: ~1 session. RCS text + ~30 LoC in TS query builder + 3-4 unit tests.

### §4.B — Dedicated `query_dasha_periods` retrieval tool (medium; clarity)

A surgical 30th retrieval tool. Wraps `chart_facts` dasha rows with the right semantic shape. Params:

```ts
{
  system?: 'vimshottari' | 'yogini' | 'chara'        // default vimshottari
  level?: 'M' | 'A' | 'P' | 'all'                     // default 'all'
  as_of_date?: string                                 // returns active period
  next_count?: number                                 // returns next N MDs after as_of_date
  prev_count?: number                                 // returns prev N MDs before as_of_date
  md_lord?: string                                    // filter by MD lord
  ad_lord?: string                                    // filter by AD lord
  from_date?: string                                  // range start
  to_date?: string                                    // range end
  limit?: number                                      // default 30
}
```

Default behavior with empty params: returns today's active chain + next 3 MDs. This is the "what's my dasha situation?" answer in one tool call.

Distinct from chart_facts_query: chart_facts_query is the chart-fact swiss army knife; `query_dasha_periods` is the dasha-specific surface. Like the M9 multi_school_signal_lookup vs msr_sql split — same data, semantic clarity.

**Cost**: ~1 session. New file `platform/src/lib/retrieve/query_dasha_periods.ts` mirroring the M8-G wrapper pattern + RCS entry + ALL_29 → ALL_30 in `trace/types.ts` + 5 unit tests + 4 golden-set entries + smoke test.

### §4.C — Planner R-DA (Dasha Anchor) rule (medium; ensures the tool fires)

New PLANNER_PROMPT rule alongside R-TC, R-PA, R-TE:

```
R-DA. DASHA ANCHOR: Attach `query_dasha_periods` (in addition to query_ephemeris
under R-TC) when the query references:
  (a) Mahadasha / MD / Vimshottari period / current dasha / next dasha / 
      upcoming dasha / previous dasha / which dasha
  (b) Antardasha / AD / Pratyantardasha / PD / Sookshma / SD / Prana / PD2
  (c) A specific dasha lord by name in a temporal-context way
      ("when is my Saturn dasha", "Mars antardasha")
  (d) The Yogini, Chara, Narayana, or Kalachakra dasha systems

Priority:
  - Pure dasha-lookup query → priority 1
  - Predictive query mentioning dasha as a timing layer → priority 1
  - General predictive query (R-TC fires) → priority 2

Date param selection:
  - "current/now/today" → as_of_date = today; level = 'all'
  - "next" / "upcoming" → as_of_date = today, next_count = 3
  - "previous/past" → as_of_date = today, prev_count = 2
  - Specific date → as_of_date = that date
  - Date range → from_date + to_date

Exclusions:
  - Pure natal MD-lord-significance query goes through chart_facts_query
    + msr_sql (MD-lord karaka context). R-DA still attaches as priority 3
    for cross-reference, but the natal interpretation is the answer.
```

Also append a §4.28 few-shot example demonstrating R-DA on a "what's my next dasha?" query.

**Cost**: bundled into §4.B brief. PLANNER_PROMPT text + 1 few-shot example + the GT.083-086 golden set already exercised in §4.B.

### §4.D — Synthesis-prompt DASHA DISCIPLINE GATE (medium; makes consultation mandatory)

Add to `platform/src/lib/prompts/templates/predictive.ts` (and `factual.ts` for "current dasha" lookups) a new gate analogous to `B11_EXPLICIT_LAYER_GATE`:

```
DASHA DISCIPLINE GATE (mandatory):
Whenever the response claims a current, previous, next, or upcoming dasha
lord (MD/AD/PD/SD/PD2), the claim MUST cite the specific DSH.V.NNN fact_id
from the bundle's chart_facts dasha_vimshottari rows OR the
query_dasha_periods tool result.

Format: "current MD lord is Mercury (→ DSH.V.015–023, 2010-08-21 to 
2027-08-21)" or "next MD is Ketu (→ DSH.V.024, 2027-08-21 to 2034-08-21)".

Forbidden:
  - Asserting a dasha lord without DSH.V.NNN citation
  - Asserting period dates without FORENSIC §5.1 row citation
  - Extrapolating "next" / "previous" from generic Vimshottari knowledge
    when the bundle's chart_facts dasha rows are present

If the bundle does not contain the required dasha row(s), mark the claim
[EXTERNAL_COMPUTATION_REQUIRED: dasha_vimshottari row for <range> not
present in bundle; refetch via query_dasha_periods].
```

This is analogous to the existing FALSIFIER_GATE and CALIBRATION_LANGUAGE_GATE. Reuses the same enforcement pattern.

**Cost**: ~1 session. Text addition to predictive.ts + factual.ts + holistic.ts + remedial.ts (any template that may touch dasha context) + 2-3 golden-set tests for citation discipline.

### §4.E — Post-synthesis dasha validator (highest defense; catches anything that slips through)

New `platform/src/lib/checkpoints/checkpoint_dasha.ts`. Runs after synthesis output is drafted (same hook as checkpoint_5_5).

Algorithm:

1. Extract dasha claims from the response via regex over patterns like `(\w+) (MD|AD|PD|mahadasha|antardasha|sookshma)` + adjacent date phrases.
2. For each claim, check against `chart_facts` `category='dasha_vimshottari'`:
   - If claim says `Mercury MD 2010-2027` — match against DSH.V.015 start_date + ad_lord chain
   - If claim says `Ketu MD next` — match against the next row after the current MD-cluster end
   - If claim says `Saturn MD next after Mercury` — should match nothing valid in chart_facts (Saturn MD is in past), flag VIOLATION
3. On violation: emit `dasha_factual_violation` event + halt synthesis or trigger a retry with a remediation prompt.

This is the "validator-as-last-line-of-defense" pattern that exists for citation density (checkpoint_5_5) extended to dasha facts.

**Cost**: ~2 sessions. New checkpoint module + integration into single_model_strategy.ts orchestrator + 8-10 unit tests covering false-positive avoidance + correct-claim acceptance + wrong-MD rejection.

## §5 Phasing recommendation

| Phase | Layers | Sessions | Headline benefit |
|---|---|---|---|
| **5A** | §4.A + §4.B + §4.C (bundled — tool + RCS + planner rule) | 1-2 | Planner now reliably retrieves the right dasha data |
| **5B** | §4.D synthesis prompt gate | 1 | Synthesis is mandated to cite DSH.V.NNN; can't paraphrase from memory |
| **5C** | §4.E validator | 2 | Wrong claims caught + halted before reaching the user |

Total: 4-5 sessions. Similar shape to the Phase 4 ephemeris campaign (4 sub-phases over 2 days). The native picks scope: 5A alone moves the needle materially (data becomes reachable); 5A+5B is the recommended minimum (data reachable + synthesis mandated to use it); all three is the bullet-proof shape.

## §6 Approved decisions (locked 2026-05-19 by native)

1. **Validator-on-violation behavior** — APPROVED: silent retry up to 2 attempts, then hard `VALIDATOR_FAILURE` if still wrong. Mirrors `checkpoint_5_5`. Implemented in §5C.

2. **Synthesis prompt gate scope** — APPROVED: all 4 templates (`predictive` / `factual` / `holistic` / `remedial`). One paragraph per template; cost is uniform. Implemented in §5B.

3. **`query_dasha_periods` as a separate retrieval tool** — APPROVED. Not folded into `chart_facts_query`. The discoverability + RCS-clarity benefit outweighs registry compactness, consistent with the M9 multi-school split vs msr_sql precedent. Becomes the 30th tool. Implemented in §5A.

4. **Multi-system coverage** — APPROVED: `query_dasha_periods` accepts a `system` param covering `vimshottari` / `yogini` / `chara` from day one (data exists in chart_facts for all three). The validator (§5C) stays Vimshottari-only initially; Yogini/Chara extension is mechanical and queued as a follow-up if needed.

5. **Baseline audit** — APPROVED as a Stage-0 task in the §5A brief (not a separate campaign sub-phase). Reads `audit_events` table; grep for dasha-mentions in past synthesis outputs; spot-checks 20 samples; emits a baseline rate of "wrong-next-MD" claims for post-campaign delta measurement.

All five decisions feed directly into the §5A / §5B / §5C briefs. No further native input required before brief authoring begins.

## §7 Sources

- `platform/scripts/temporal/compute_vimshottari.py` — canonical compute (correct).
- `05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json` — output (correct).
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1` — canonical table (50 rows, correct).
- `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` — 50 `dasha_vimshottari` facts (correct).
- `platform/python-sidecar/pipeline/extractors/forensic_extractor.py` — chart_facts loader.
- `platform/python-sidecar/routers/dasha_chain.py` — sidecar endpoint (correct, returns active chain at one date only).
- `platform/src/lib/retrieve/chart_facts_query.ts` — implementation supports `dasha_vimshottari` category; RCS description does not advertise it.
- `platform/src/lib/router/retrieval_capability_spec.ts` — `chart_facts_query` RCS entry (Gap A) + `timeline_query` RCS entry with hardcoded "Ketu next" warning that synthesis doesn't see (Gap C).
- `platform/src/lib/retrieve/temporal.ts` — `dasha_context_required` branch returns active chain only (Gap B).
- `platform/src/lib/retrieve/timeline_query.ts` — file-header warning in the wrong layer (Gap C).
- `platform/src/lib/bundle/bundle_hydrator.ts` — FORENSIC loaded as floor asset (Gap D — context-window dilution).
- `platform/src/lib/prompts/templates/predictive.ts` — no dasha discipline gate (Gap E).
- `platform/src/lib/checkpoints/` — three existing checkpoints, none catch dasha claims (Gap E).
- CLAUDE.md §I B.10 — no fabricated computation. Already applies; not enforced for dasha.

## §8 Out of scope for this dossier

- The DBN posterior + CI handling for dasha-domain probabilities (separate Learning Layer concern).
- Multi-native dasha computation (M7 scope).
- Tradition-fork resolution for Jaimini Chara / Narayana dasha (deferred per PHASE_M3_PLAN §3.3).
- Dasha computation under non-Lahiri ayanamshas (locked: Lahiri only per Phase 4 §6.5).
- Eclipse / transit / panchanga correctness — already addressed by Phase 4.

---

*End of DASHA_CORRECTNESS_RESEARCH_v1_0. Awaiting native decision on (1)–(5) in §6; brief authoring follows approval.*
