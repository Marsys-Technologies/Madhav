---
canonical_id: BA_BRIEF_PACK_P2_P7
version: 1.2
status: SUPERSEDED (2026-07-03, native directive) — split into EIGHT standalone root briefs, one per
  phase/lane, each self-contained with its share of the v1.1 annex embedded:
  CLAUDECODE_BRIEF_BA_P2_QUERYTIME_RANKING_v1_0.md · BA_P3A_L0_SEEDS_AND_L1_EXT · BA_P3B_L2_REGENERATION ·
  BA_P4_VERDICT_MAHABRIEF_EVAL · BA_P5A_KALA_ACTIVATION · BA_P5B_PHALA_V2 · BA_P6_MIMAMSA_ENGINE ·
  BA_P7A_CLASSICAL_COMPLETIONS · BA_P7B_PORTAL_LEARNING_LOOPS (all at repo root). THE ROOT BRIEFS ARE THE
  EXECUTION AUTHORITY; this pack is retained as the consolidated design record + annex reference only.
  Conductor fills ⟦SLOT⟧s in the root briefs directly (no materialization step).
created: 2026-07-03
author: Cowork (strategic workstream, Claude Fable 5) — FULL substance authorship; conductor fills slots only
contract: >
  At each phase start the CONDUCTOR materializes that phase's section into a root
  CLAUDECODE_BRIEF_BA_<PHASE>_v1_0.md, fills every ⟦SLOT⟧ from the prior phase's close report / run
  ledger, and submits the slot-fill (ONLY the slot-fill) to the Spec-Auditor's Brief-Audit gate. The
  substance below is FROZEN Cowork authorship — the conductor may not alter scope, steps, gates, or
  must_not_touch lists; discovering that substance must change = a HALT-condition-1-adjacent event
  (checkpoint + report, unless the change is strictly narrowing).
common_to_all_briefs: >
  FROZEN contract (§N.2) · surgical migrations, number = max(both dirs)+1 at materialization ·
  delete-then-insert per §N.3 (per-chart) / upsert (global) · count_sql chart-scoped $1 + Clear nulls
  rows_written · degeneracy gate on every new scoring column · two-chart rule (1c826d5a BEFORE 482012f1)
  · PD-5: any asset_registry change updates ASSET_NAMES.ts + ASSET_MAP same PR · ACs tagged
  [verify-against: prod|db|ci] · Ring-1 before merge, Ring-2 at promotion · SESSION_LOG/CURRENT_STATE
  close per governance · Anthropic banned in product paths; scoring LLM-free.
---

# BRIEF PACK — P2 → P7 (materialize per phase; slots in ⟦…⟧)

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P2 — QUERY-TIME RANKING + THE ZEROING BENCH
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P1 final tool census + new-tool list⟧ · ⟦P0 baseline latency table ref⟧ · ⟦HEAD SHA⟧
**may_touch:** retrieval registry ranking/composition module (NEW code paths), envelope retrofit sites,
seed-extraction script, synth_* assembly. **must_not_touch:** pipeline writers, migrations, stored
salience columns, orchestrator/cockpit.

1. **Seed extraction:** from the committed `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md`, extract
   class-prior table + varga-grain vector + graha×domain + domain×varga affinities into a runtime config
   (`prior_version=0.9-prov`) loaded by the retrieval layer. NO DB migration in P2 (the L0 asset lands in
   P3A); config file is the interim home, schema-identical to the future `brahma_class_priors` row shape.
2. **The 4-dim composite** (RM §4) computed at query time: topic_relevance (affinities + lordship/occupancy
   from ga_positions/ga_structural) × intrinsic_strength (ga_strength shadbala + ga_condition dignity —
   REAL values, never the degenerate stored salience) × structural_role
   (`COALESCE(pagerank, f(yoga_membership, signature_class))` — pagerank is 100% NULL, fallback REQUIRED)
   × temporal_activation (current MD/AD lords direct from chart_dashas; kala bypass). Percentile-within-
   class on the fly. `ranking_basis` (4 sub-scores + composite + priors_version) on every payload.
   **Cache:** keyed (chart × domain × priors_version), invalidation scheduled at dasha-boundary dates.
3. **Envelope retrofit** on all ⟦P1 census⟧ tools (verdict slot null; grounding block live; judgment_flags
   honest). **Apex repair:** assess_* assemble the structured verdict skeleton (top-k per reasoning-chain
   stage + contradiction pairs w/ both sides' rank + activation state + inline citations) — deterministic
   assembly, no prose.
4. **P2T — the tuning loop (Ācārya-Pratinidhi drives; config-only iterations):** run the 10 golden
   questions → score ranking quality per the Astro-Examiner rubric → adjust priors/affinities → repeat.
   Convergence = G10-QT passes AND no golden question's ranking-quality score regresses two iterations
   running. Freeze as `prior_version=1.0`; write values + full iteration trace into the seed package
   (version bump) + Judgment Ledger.
**Exit gates [verify-against: prod]:** G10-QT (career top-10 on 482012f1 = 10th-lord/kāraka/yoga
structures, ZERO sub-varga atoms); ranking_basis on every envelope; latency: ≤+500ms p95 cache-miss /
≤+50ms cache-hit vs ⟦P0 baseline⟧; golden-eval score recorded as the standing regression baseline.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P3A — L0 SEEDS + L1 EXTENSIONS
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦prior_version=1.0 values from P2T⟧ · ⟦next migration number, both dirs⟧ · ⟦HEAD SHA⟧
**may_touch:** new bg_* writers + migrations, ga_sensitive/ga_dashas/ga_strength/ga_condition writers,
seal-amendment notes, ASSET_NAMES/ASSET_MAP. **must_not_touch:** orchestrator/planner, bo_*/ka_*/ph_*/mi_*,
retrieval logic.

1. **Migrations (surgical, in order):** `charts.chart_type` column (default 'natal') · canonical
   12-domain normalization across the 8 divergent sites (BA_MASTER C15, per the seed package's domain
   taxonomy) · `brahma_class_priors` + registry row (GLOBAL) seeded with ⟦prior v1.0⟧ ·
   `brahma_event_ontology` + `brahma_activity_ontology` + registry row `bg_ghatana` (GLOBAL; seed package
   §2/§3) · `brahma_formula_constants` + registry row `bg_formula_constants` (GLOBAL; constants sheet incl.
   per-graha combustion orbs from bg_combustion_orbs as canonical citations).
2. **Writers:** `bg_class_priors`, `bg_ghatana`, `bg_formula_constants` (upsert; global; trivial count_sql).
3. **L1 EXTs (seal-amendment, per BA_MASTER §3-L1):** ga_sensitive += bhava arudhas A1–A12 + AL + UL +
   Karakamsha/Swamsha; ga_dashas += classical Chara dasha (Rao); ga_strength += per-varga shadbala
   (computed-extension label; canonical-or-floor); ga_condition += graha yuddha (cited method) + lajjitadi
   + sayanadi. Rebuild L1 for BOTH charts via the cockpit path.
**Exit gates:** FORENSIC 7/7 on 482012f1 [verify-against: db]; contamination check 1c826d5a; new
fact_categories present ×5 ayanamshas (or INVARIANT); global assets carry NO chart_id (§2.2-1); cockpit
shows the 3 new assets (ASSET_NAMES/ASSET_MAP updated); golden-eval non-regression.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P3B — THE L2 SINGLE REGENERATION (the one shot)
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P3A close SHA + migration numbers⟧ · ⟦pre-P3 snapshot id/location⟧
**may_touch:** bo_laksana/bo_bimba/bo_karanajala/bo_samvada/bo_upaya writers, NEW bo_pratijna writer +
migration, bo_sangati writer + bodha_triangulation migration, formulas.py unification.
**must_not_touch:** orchestrator/planner, L1 writers, retrieval interfaces (shape-stable swap only).

0. **Snapshot before rebuild** (charter §4): dump affected bodha_* tables for both charts; record id.
1. **bo_laksana v2.0 (ONE formula site — delete the divergent second):** salience_v2 = class_prior ×
   varga_weight × specificity × RESCALED verification (lift the 0.778 cap per C5) × v1 condition terms;
   store `salience_pctl_in_class` (S-A), NULL-propagation + `salience_inputs_complete` (S-C),
   `salience_robustness` + cross-ayanamsha fill (S-D/B5), `bala_gate` (A-B: weak-bala yogas =
   present-but-enfeebled state), `functional_context` (A-C); hierarchical aggregation (atomic families →
   composite profile signals; atoms never top-band); signature_tier recut so chart_defining FIRES;
   constituent_facts re-resolution VERIFIED ≥99% (PD-4 says clean — regeneration must keep it clean).
   Read priors from `brahma_class_priors` (single weight source).
2. **Graph + contradictions:** bo_bimba/bo_karanajala typed edges (dispositor, argala/virodha,
   parivartana, yoga-membership, karaka-role, nakshatra-dispositor, KP-sub-lord) with valence +
   relationship_basis + affected_domains filled; node strengths from salience v2; pagerank backfill;
   bodha_contradictions POPULATED both charts + domain attribution + reconciliation records; S-B
   effective-evidence correction in CDLM/sangati aggregates (log de-dup + effective_evidence_count).
3. **NEW bo_pratijna** (Promise Register: chart × event_class from brahma_event_ontology → promised/
   denied/conditional + grade + signal refs + varga confirmation) + **bo_sangati EXT**
   (bodha_triangulation: per question-class × tradition stack + concordance). **bo_upaya:** de-degenerate
   resonance scoring (F-007) using salience v2 inputs.
4. **Regenerate L2 ONCE**, Abhinandan FIRST, then native; then swap the retrieval layer's intrinsic
   inputs from query-time computation to the stored columns (query-time terms stay query-time, §2.2/S-E).
**Exit gates:** G10-STORED (same test, stored path) [verify-against: prod]; degeneracy gate on
salience_v2/pctl/robustness/resonance (no constant-collapse); trap-1 authority check; zero
consumer-visible interface change (envelope diff empty on 5 spot tools); golden-eval ≥ P2 baseline;
bodha_contradictions > 0 both charts; rollback tested = ⟦snapshot⟧ restore rehearsed on Abhinandan.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P4 — VERDICT OBJECT + MAHĀ-BRIEF + FULL EVAL
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P3B close SHA⟧ · ⟦golden-eval score after P3B⟧
**may_touch:** retrieval composition modules, mi_darshana writer (insight_units as verdict home),
synth_chart_brief_get + synth_tail_divergence_get (NEW tools), eval harness, LiveDependencyGraph/
AssetTable refactor. **must_not_touch:** L1/L2 writers (data is frozen post-P3), orchestrator.

1. **Verdict object live:** content.verdict = {claim, ranked_evidence, contradictions w/ resolution,
   tradition_concordance (bodha_triangulation), activation_state, ayanamsha_robustness, confidence?,
   falsifier?, citations} — deterministic assembly; mi_darshana insight_units = persistence home; served
   through assess_* + get_domain_reading + mimamsa_insight_get.
2. **Query-time judgment terms:** dasha_activation boost (S-E) + karaka_congruence (A-A) + domain×varga
   affinity (A-D) applied at query time from brahma_class_priors/bg_formula_constants; attention budget
   70/20/10 (constant in bg_formula_constants) shaping every synthesis payload.
3. **Complement pass:** `synth_tail_divergence_get` + `tail_divergence` on verdicts (head withheld,
   tail-only synthesis, cited memo).
4. **The MAHĀ-BRIEF:** `synth_chart_brief_get(depth=standard|deep|complete)` — all 38 topics (RM §7) in
   reasoning-chain order, per-topic head/dissent/tail-digest, front matter from vw_chart_digest, back
   matter provenance manifest; ≤1M tokens at complete.
5. **Eval harness full:** Pratinidhi authors golden answers for ALL query classes Q1–Q9 (lel_overlap
   flags; eval/learning corpora disjoint); Astro-Examiner blind rubric (3 scorings, median); harness
   becomes the standing per-promotion regression gate.
6. **PD-5 refactor:** make LiveDependencyGraph + AssetTable registry-driven (retire hardcoded maps);
   visual check vs the PG baseline.
**Exit gates [verify-against: prod]:** rubric ≥13/15 median on the golden set (both charts on the
INTERPRETATION classes; others as data allows pre-P5); Mahā-Brief complete-depth renders all 38 topics
GREEN; tail_divergence non-trivial ≥1 domain; UI visually consistent; latency budgets hold.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P5A — KĀLA ACTIVATION (prophecy substrate, timing half)
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P4 close SHA⟧ · ⟦migration numbers⟧
**may_touch:** ka_yojaka/ka_sangam/ka_vighnakara writers, NEW ka_avadhi + ka_taranga writers + migrations,
transit service (AV gates), bg_transit_rules EXT. **must_not_touch:** L2 stored data, ph_* (P5B), orchestrator.

1. ka_yojaka EXT: fill signals' dasha_activation across ALL 7 systems; promise-linked predicates per
   bo_pratijna (multi-system cross-confirmation count as first-class score).
2. NEW `ka_avadhi` (kala_avadhi: per MD/AD × chart — lord dossier refs, activated promises, sub-lord
   modulation, quality components + citations; powers Q1 period readings).
3. NEW `ka_taranga` (kala_taranga: monthly per-domain/event-class activation curves 1950–2100; fine
   grain = service, never stored).
4. FIX conflations: ka_sangam confidence_score gets a real derivation or the column drops; ka_vighnakara
   reads per-graha combustion from the L1/bg_combustion_orbs single truth (delete flat 6.0°); severity
   thresholds move to bg_formula_constants.
5. bg_transit_rules EXT: AV kakshya/SAV gates + vedha + double-transit (cited); transit service applies them.
**Exit gates:** kala_activation populated both charts [verify-against: db]; Q1 period-reading recipe GREEN
(a "Ketu dasha 2027" query returns a composed dossier) [verify-against: prod]; one combustion truth
(grep proves no second orb constant); golden-eval non-regression.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P5B — PHALA v2 (prophecy substrate, prediction half)
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P5A close state (activation live?)⟧ · ⟦migration numbers⟧
**may_touch:** ph_nimitta REBUILD, ph_muhurta EXT, prashna chart-type build path, mi_bhavisya freeze
format. **must_not_touch:** ka_* (P5A owns), L2 stored data, orchestrator.

1. **ph_nimitta v2:** anchor = (event_class, window, magnitude, posterior); `posterior = base_rate(event_
   class, age_band, window) × promise_lift(bo_pratijna grade) × activation_lift(ka_avadhi/yojaka) ×
   trigger_lift(transit gates)`; lift_vector frozen per anchor; structured falsifier {event_class,
   magnitude_floor, window, attestation_required}; G-LADDER deleted; full probability range served incl.
   denied/unlikely.
2. **ph_muhurta EXT:** activity-aware election (brahma_activity_ontology significators × panchanga ×
   tarabala/chandrabala vs the native chart) + fructification follow-up hooks.
3. **Prashna path:** chart_type='prashna' cast-at-question-time build (minimal asset set; consumes
   bg_prashna_rules). Q4 undertaking recipe assembled.
**Exit gates [verify-against: prod]:** anchors span full probability range with LEL-decidable falsifiers +
lift_vectors both charts; Q2/Q3/Q4 recipes GREEN; confidence ≠ convergence anywhere; golden-eval:
PREDICTION/TIMING classes now scoreable and ≥ rubric floor.

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P6 — MĪMĀṂSĀ v2 ENGINE (the learning loop goes live)
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦P5 close SHAs⟧ · ⟦LEL source decision executed (see step 0)⟧
**may_touch:** mi_* writers per MIMAMSA_V2 §1 verdicts, retrodiction generator, date-filtered view
mechanism, bg_class_priors overlay tables. **must_not_touch:** L1/L2/L3/L4 data (reads only),
classical rule content, orchestrator.

0. **LEL intake (PD-10):** mi_jivanaghatana EXT parses `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` into
   mimamsa_event_provenance (event_class + magnitude mapped per brahma_event_ontology; MD5 mod-10 holdout
   preserved; version-pinned to the LEL file SHA). The markdown remains the source of truth.
1. **mi_pramana ENGINE v2:** adjudication (CONFIRMED/PARTIAL/REFUTED-requires-attestation/EXPIRED/
   FALSE_ALARM; ontology adjacency; structured falsifiers — stub deleted); scoring = Brier vs
   base-rate null + rank-aware retrodiction credit + ECE; sharpness via the null.
2. **mi_pariksha v2 substeps:** retrodiction_generate (blind pre-event cutoffs via date-filtered views —
   generalize the ph_pramana firewall) · control_windows (≥3/event, stratified) · ablation (per family
   masked) · analytic attribution from lift_vectors (catch-all DELETED) · neg_control · discovery ·
   tail-only retrodiction (the doctrine's falsifier).
3. **mi_gunanaka v2:** hierarchical shrinkage (n-gates deleted; 3× cap kept); versioned calibration
   snapshot builder. **Weight unification:** mi_kula._FAMILIES + mi_pariksha._DIM_WEIGHTS + mi_pramana
   dims all read brahma_class_priors (3 embedded sites deleted).
4. **mi_adhilepa WIRE:** two-key snapshot publication (key-2 = Ācārya-Pratinidhi, logged); overlays to the
   3 sinks only. **Sensitivity harness:** vary bg_formula_constants within bounds → output-stability
   ranking recorded.
**Exit gates:** the first honest skill table (train/held-out per the intake partition) [verify-against:
db]; ≥1 family beats null OR the null finding published with equal prominence; snapshot visibly +
reversibly changes served weights under two-key; scoring path 100% LLM-free (audit); golden-eval
non-regression; eval corpus ∩ learning corpus = ∅ (lel_overlap flags enforced).

═══════════════════════════════════════════════════════════════════════════════
## BRIEF BA-P7A — CLASSICAL COMPLETIONS ∥ BA-P7B — PORTAL LEARNING LOOPS
═══════════════════════════════════════════════════════════════════════════════
**Slots:** ⟦Pratinidhi's E4 ranking (Judgment Ledger ref)⟧ · ⟦P5/P6 close SHAs⟧
**P7A may_touch:** bg_rules EXT (Nadi extraction from in-corpus texts), remaining avastha unfloors,
AV-transit rule completion. Gates: new fact_categories flow through bo_laksana v2 RANKED (spot-check:
no new family saturates any top band); citations resolve to real verses.
**P7B may_touch:** portal UI (ask-cards on closed windows, period-attestation card, structured LEL intake
form per ontology, prashna follow-up scheduler, snapshot co-sign surface) — existing design system only
(canonical tokens; no new visual language). Gates: closed-window → adjudicated ≥80% within 7 days
(measured over the run's own open windows where possible, else staged test windows); portal chat latency
within budget; visual consistency vs PG baseline [verify-against: prod].

═══════════════════════════════════════════════════════════════════════════════
## IMPLEMENTATION CONTEXT ANNEX (v1.1 — part of the frozen substance; applies to all briefs above)
═══════════════════════════════════════════════════════════════════════════════

### A — CODE ANCHORS (verified entry points; start here, don't excavate)
- MCP tool bridge/registration: `platform-mcp/.../tool_name_bridge.ts` (TOOL_NAME_TO_URI, SURGICAL_TOOLS,
  MCP_TO_RETRIEVAL_TOOL) — the P1/P2 wiring surface. Apex: `register_d8_assess_domain.ts`. Registry
  dispatch: `registry_bridge.ts` + `/api/retrieval/capability/route.ts` (ensureBootstrapped).
- Salience v1 + tier + row builder: `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`
  — `_compute_salience` L740–808, `_signature_tier` L419–428, `_build_signal_row` L847–851 (constituent
  refs). SECOND (divergent) formula site: `bodha_writers/formulas.py` — DELETE in P3B (C5).
- Orchestrator contract: `writers/__init__.py` (WriterBase L65, register L167) — read-only law.
- L4 anchor engine: `services/ph_nimitta/engine.py` (G-LADDER L44–60 to delete; derive_* functions;
  `_KARMIC_FRAME` to keep). L5: `mi_pramana.py` (stub falsifier L96–110), `mi_pariksha.py` (attribution
  substep + `_DIM_WEIGHTS`), `mi_kula.py` (`_FAMILIES`), `mi_gunanaka.py` (n≥10, 3× cap),
  `mi_jivanaghatana.py` (MD5 partition), `mi_sambandha.py` (`_PRIOR_PROPENSITIES` — keep as smoothing base).
- Kala fixes: `ka_sangam.py` (`_insert_windows` confidence mirror), `ka_vighnakara.py`
  (`_COMBUSTION_ORB_DEG=6.0` to delete; severity thresholds to registry). L1 combustion truth:
  `ga_condition_writer.py` reading `bg_combustion_orbs`.
- UI hardcoded maps (PD-5): `LiveDependencyGraph.tsx`, `AssetTable.tsx`, `asset_names.ts`.
- Leakage-firewall precedent (P6 retrodiction): `services/ph_pramana` rectification train/test split.
- Golden questions: `RETRIEVAL_TOOL_BLUEPRINT_v1_0.md` §B5 (Q-table + tool chains). Seed package:
  `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` (priors §1, ontologies §2–3, constants §4, affinities §5).

### B — DDL SKETCHES (column-level shape; executor may extend, never rename)
- `brahma_class_priors(prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition,
  class_prior numeric, varga_weights jsonb, contested bool, citation, ratified_by, PRIMARY KEY(prior_version,
  signal_type_class, fact_kind, source_subsystem, signal_tradition))` — key shape per C14.
- `brahma_event_ontology(event_class_id PK, name, domain, signature_model jsonb{houses,lords,karakas,
  vargas,dasha_rules,transit_triggers}, magnitude_floor, adjacency jsonb, base_rate_by_age jsonb,
  matching_rules jsonb, citations, version)`; `brahma_activity_ontology(activity_class_id PK, name,
  significators jsonb, fructification_rules jsonb, related_event_class FK, citations)`.
- `brahma_formula_constants(constant_id PK, value_jsonb, class, consumer_assets text[],
  citation_or_ratification, calibratable bool, bounds jsonb, version)`.
- `bodha_pratijna(chart_id, ayanamsha_id, event_class_id, status ∈{promised,denied,conditional}, grade
  numeric, supporting_signal_ids uuid[], contradicting_signal_ids uuid[], varga_confirmation jsonb,
  derivation jsonb, formula_version, UNIQUE(chart_id, ayanamsha_id, event_class_id))`.
- `bodha_triangulation(chart_id, ayanamsha_id, question_class, tradition, verdict_inputs jsonb,
  concordance_score numeric, formula_version, UNIQUE(chart_id, ayanamsha_id, question_class, tradition))`.
- `kala_avadhi(chart_id, system_id, level_n, lord_graha, period_start, period_end, dossier jsonb
  {lord_condition_fact_refs, activated_pratijna_ids, sublord_modulation}, quality jsonb, citations,
  UNIQUE(chart_id, system_id, level_n, period_start))`.
- `kala_taranga(chart_id, month date, scope_kind ∈{domain,event_class}, scope_id, activation numeric,
  components jsonb, formula_version, UNIQUE(chart_id, month, scope_kind, scope_id))`.

### C — FORMULA SPECS (defaults; Ācārya-Pratinidhi may tune within bounds, all reads from the registry)
- **specificity** (P3B): `1 + 0.5 × extremity_pctl`, extremity = percentile of |value − family median|
  within (family × chart × ayanamsha). Deterministic, no corpus dependence at n=2 charts.
- **verification rescale** (C5 replacement): multiplier map {two_pass_verified: 1.00, single_pass: 0.85,
  documented_approximation: 0.60} — replaces `log(1+corroboration)/log(10)` and its 0.778 ceiling.
- **bala_gate** (A-B, yoga-class only): `g = clamp(norm_constituent_shadbala, 0.30, 1.00)`; serve state
  `present_but_enfeebled` when g < 0.60 (state, not exclusion).
- **effective evidence** (S-B): family contribution = `max_salience_in_family × (1 + log10(1 + n_family))`;
  cell total = Σ over families; report raw count AND effective_evidence_count.
- **G10-QT tuning rubric** (P2T, /15, pass ≥13): top-10 contains ≥3 yoga-class signals (3) · contains a
  10th-lord signal (2) · contains a kāraka-congruent signal (2) · ZERO per-varga atomic tallies (2) · no
  tie-block >3 identical scores (1) · score distribution non-degenerate per the Warden (2) · every top-10
  row cites resolvable facts + a classical source (3).
- **P2 cache invalidation:** key (chart_id × domain × priors_version); TTL = `MIN(next dasha-boundary
  across active levels from chart_dashas, 30d)`; explicit bust on priors_version bump.

### D — KNOWN-VALUES SANITY TABLE (every phase spot-checks outputs against these; mismatch = halt-and-look)
482012f1: Lagna Aries (all 5 ayanamshas) · Sun Capricorn H10 (Shravana) · Moon Aquarius H11 (Purva
Bhadrapada) · 10th lord = Saturn · FORENSIC 7/7 anchors per CLAUDE.md §B · per-ayanamsha signal count
≈12,954 (×5 ≈64.7k) · yogas 90 · doshas 22 · contradictions ≈1,034 · current MD/AD derivable from
chart_dashas for run date. 1c826d5a: ≈12,963 signals · 88 yogas · distinct convergence profile (charts
must DIFFER — identical outputs across charts = contamination alarm).

### E — ANTI-GOALS (the specific wrong turns, per phase)
- P2: NO writes to bodha_* tables; NO migration; ranking lives in retrieval code + config only. Do not
  "fix" stored salience early. Do not bake activation into cached composites beyond the TTL rule.
- P3A: global seeds carry NO chart_id; do NOT regenerate L2 here (that is P3B, once).
- P3B: ONE regeneration; do not iterate priors here (frozen at P2T); do not change the envelope shape;
  do not touch retrieval interfaces except the documented input swap; Abhinandan before native, always.
- P4: the LLM never WRITES verdict content — assembly is deterministic; narration sits above the envelope.
  Mahā-Brief is generated-on-demand + cached artifact, never a stored table.
- P5A/P5B: no second combustion/orb/threshold constants anywhere — registry only. Anchors must be able to
  say "denied/unlikely" — a floor on posterior is a bug.
- P6: scoring path LLM-free (D-1) — any LLM call in adjudication/scoring is a Ring-1 failure; goldens with
  lel_overlap NEVER enter training cells; the LEL markdown is source-of-truth (DB projection is derived).
- P7B: existing design tokens only; no new visual language.

### F — SMOKE ONE-LINERS (exit-gate spot checks; adapt args)
- G10-QT/stored: `get_signals(482012f1, domain=career, limit=10)` → assert zero
  `ashtakavarga_bindu_per_varga:*` in top-10, ≥3 yoga-class, ranking_basis present.
- Scope law: `SELECT asset_id, scope FROM asset_registry WHERE layer='brahmagyan' AND scope!='global';` → 0 rows.
- Promise register: `SELECT status, count(*) FROM bodha_pratijna WHERE chart_id=$NATIVE GROUP BY 1;` →
  all three statuses present, grades non-degenerate.
- Period reading (Q1): `kala_avadhi` row for the current MD includes ≥1 activated_pratijna_id + citations.
- Anchor honesty: `SELECT min(posterior), max(posterior) FROM phala_anchors WHERE chart_id=$NATIVE;` →
  min < 0.2 (the instrument can say "unlikely").
- Learning: `mimamsa_calibration` skill table has ≥1 cell with n>0 vs null-model column populated;
  `grep -r "openai\|gemini\|anthropic" <scoring paths>` → clean.

*End of BA_BRIEF_PACK_P2_P7 v1.1 — v1.1 (2026-07-03): Implementation Context Annex added after Cowork
self-review (code anchors, DDL sketches, formula specs incl. G10-QT rubric, sanity table, anti-goals,
smoke one-liners). Substance frozen; slots to the conductor; Ring 3 closes the run.*
