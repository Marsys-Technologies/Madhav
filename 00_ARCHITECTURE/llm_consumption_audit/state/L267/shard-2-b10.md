# Lane 2 Evidence-Sufficiency — Shard 2-b10 (Group F: Kutumba & Vivaha, F7–F10)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1 §7.3 (4-point scale). Mode: P-12 plan-then-acquire.
Channel: deployed MCP connector (read-only). Charts: A=`482012f1…` (Abhisek), B=`1c826d5a…` (Abhinandan).
Status: COMPLETE — 16/16 rows graded. trim_seen: TRUE (digest envelope budget-caps observed on every orientation-bearing tool).

## Evidence plans (per theme — the plan IS a deliverable)

- **F7 romance vs arranged:** an acharya needs the 7th bhava (love-partnership), the 5th (romance/purva-punya),
  Venus–Mars linkage, 5L↔7L exchange, Rahu-on-7/Rahu-Venus (love-marriage yogas), Upapada, D9. Order: judgment_query(relationship)
  → get_domain_reading lenses (is there a "romance/love" question_type?) → get_signals(relationship) for named love yogas → D9 varga.
- **F8 extramarital risk:** 7th affliction, 7th-from-7th, dara-karaka, Venus–Mars–Rahu, 12th (bed-pleasures), unchaste-yoga classifiers,
  D9 Venus. Order: judgment_query(relationship) occupants/karaka → get_signals for any infidelity dosha → D9.
- **F9 engagement vs consummation muhurta:** two distinct electional rule-sets (vagdana/nischitartha vs garbhadhana/shobhana).
  Order: enumerate muhurta_finder action_type enum → run marriage windows → check for engagement/consummation-specific types.
- **F10 dampatya remedial priority:** ranked remedy set scoped to relationship affliction, with priority ordering.
  Order: get_remedies(relationship) → bodha_remedies_get(fields=all) → CDLM cell_remedy_priority_rank.

## Shared evidence acquisition (relationship domain, both charts)

Tools called (read-only): `assess_marriage`/`apex_marriage_assess`, `get_domain_reading`(domain=relationship),
`get_signals`(domain=relationship), `judgment_query`(domain=relationship), `get_temporal_windows`(domain=relationship),
`get_remedies`+`bodha_remedies_get`(domain=relationship, fields=all), `muhurta_finder`(action_type=marriage).

Key received facts:
- **judgment_query is the acharya path.** Returns deterministic 7th-bhava classical checklist: bhava (from lagna + chandra),
  bhavesha, karaka (Venus), occupants, aspecting grahas, bearing_yogas, D9 varga_confirmation, timing_hooks, grounding.fact_ids.
  - Chart A: 7th=Libra; 7L Venus in 9th Sagittarius (neutral, shadbala 4.64); **occupants Mars+Saturn in 7th**; verdict "mixed", composite −1; bearing_yogas [] (empty); D9 rows [] (empty).
  - Chart B: 7th=Libra; 7L Venus **exalted** in 12th Pisces (shadbala 7.75); **Ketu in 7th**; verdict "convergent_moderate", composite 1.9; bearing_yogas [Gola Yoga — a generic non-marital yoga]; D9 rows [] (empty).
- **get_domain_reading / get_signals** for relationship surface only generic pan-chart Pancha-Mahapurusha yogas (Sasa/Shoola/Vasi/Yuga/Gola/Anapha/Kedara) at an **identical composite wall (1.0465 ×7 rows)** — not marriage-specific (DROWNED). domain_reading question_lenses = 2 rows, both question_type "marriage"; **no romance/love lens**. Signals arrive as ID+salience lists (signal_id_refs capped 200/7014); text only via get_signals drill.
- **get_temporal_windows(relationship): activation_count=0, predicate_count=0 on BOTH charts** (EMPTY SHELL; kala R-45 pattern). Only marriage timing is judgment_query.timing_hooks (Venus MD 2034–2054 for A).
- **get_remedies / bodha_remedies_get(relationship): resonance_count=0, prescription_count=0 on BOTH charts** (EMPTY SHELL). data_gap_note: bo_upaya `associated_doshas_array` + `estimated_cost_inr_range_jsonb` 100% NULL for every chart built. CDLM `cell_remedy_priority_rank`=null.
- **muhurta_finder** works (dated windows w/ panchanga+dasha+transit+signal scores), but `action_type` enum = {marriage, travel, business, medical, education, property, general} — **no "engagement", no "consummation"**. Source_citation cites deleted `FORENSIC v8.0` (stale). dasha `ad_lord`/`md_lord`="unknown" on rows (A ad_lord unknown; B md_lord unknown).

## Cross-cutting defects observed (findings)
- **DISHONEST RECEIPT (class 5):** judgment_query receipt claims `varga_confirmed:"D9✓"` while `varga_confirmation.rows=[]` on BOTH charts — receipt asserts D9 confirmation the payload does not contain.
- **TRIM (class 6/5):** assess_marriage text suppressed ("[budget-capped response]"); top_10 signal summaries "[truncated for budget]" mid-value; signal_id_refs capped 200/7014 (`signal_id_refs_capped:true`); token_safety_note bounds to 3 lenses×20 signals. trim_seen=TRUE.
- **DROWNED (class 7):** relationship top-signals = chart-wide mahapurusha yogas tied at one score; UNATTRIBUTED entity holds 299/300 signals (R-44 anchor rediscovered).
- **STALE PROVENANCE (class 5):** muhurta_finder cites `FORENSIC v8.0 §5.1` — deleted in PR #187.

## Class-9 UNGOVERNED-JUDGMENT improvisation log
- **F7:** taxonomy→life-language + method choice — no love-vs-arranged classifier exists; LLM must invent the determinant set (5L–7L link, Rahu-Venus) from raw 7th placements.
- **F8:** method choice + silent decomposition — no infidelity model; LLM must choose which houses/karakas signal extramarital risk and translate "Mars+Saturn in 7th" into a risk verdict.
- **F9:** silent decomposition — LLM must decide which of engagement/consummation the single "marriage" action_type covers, and improvise the other.
- **F10:** conflict/gap adjudication — with 0 served remedies, any priority ordering is LLM-fabricated.

## Per-row verdicts (theme × chart; narrow/broad share the evidence pool)

**F7 romance vs arranged** — Narrow binary → INSUFFICIENT (no manner-of-union method; whole classifier improvised; class 9). Broad → SUFFICIENT-WITH-GAPS (7th dossier composable into a general relationship narrative, gap-honest about the love/arranged determinant). Same on A and B.

**F8 extramarital risk** — Narrow → INSUFFICIENT (no infidelity model; UNREACHABLE-BY-NONEXISTENCE for a dedicated computation + class 9 method improvisation; only raw 7th affliction retrievable). Broad → SUFFICIENT-WITH-GAPS (cautionary read on 7th affliction/Venus composable, gap-honest). Same on A and B.

**F9 engagement vs consummation muhurta** — Narrow distinction → INSUFFICIENT (only action_type="marriage"; engagement/consummation not modeled — partly UNANSWERABLE-BY-DESIGN; class 9 decomposition; + class-5 stale FORENSIC cite + ad/md_lord "unknown"). Broad "auspicious marriage dates" → SUFFICIENT-WITH-GAPS (real scored windows; dasha-detail gaps + stale cite). Same on A and B.

**F10 dampatya remedial priority** — Narrow AND broad → INSUFFICIENT on BOTH charts (class 4 EMPTY SHELL; 0 resonances/0 prescriptions; nothing to prioritize; any ranking fabricated).
