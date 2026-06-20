---
artifact: CLAUDECODE_BRIEF_BO_LAKSANA_v1_0.md
canonical_id: BO_LAKSANA_BRIEF
version: 1.2
status: FOR_NATIVE_REVIEW (Batch 1 — the root; everything depends on it)
authored_by: Cowork (grounded in live MSR schema + 14 L1 writers + ga_structural v2.0) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
v1_2_changes: >
  Folds in JUDGMENT-substrate moves 2 + 3 (L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY v1.1 FROZEN). MOVE 2:
  relational/contextual salience (conditioning relationships — "matters BECAUSE of X") + signature_tier
  (chart-defining 5-10 threads vs background). MOVE 3: structured epistemic honesty (agreement-state /
  ayanamsha-fragility / computation-vs-interpretation / calibration hook) replaces the binary tier. See §JUDGMENT.
v1_1_changes: >
  Native clarifications 2026-06-19 folded in (see §ELEVATION, now native-confirmed): (1) DASHA TWO-PLANE
  SEPARATION — project dasha STRUCTURE only; the temporal timeline stays L1 for L3 Kāla (planes never
  intersect; no 536k-row copy). (2) DEPTH = full relationship-CHAIN length to terminus, multi-entity, no
  hop cap (cycle-detection guard only). (3) WIDTH = entity-type breadth (grahas/houses/nakshatras/signs/
  aspects/conjunctions) — relationships not planet-only; data-domain coverage (medical/vastu/prashna/yoga)
  is a separate axis, also in. (4) ABSENCES = significant-only, curated classically-grounded list. (5) E-R2
  two text fields (lossless summary + short headline). General principle: project generously, no noise;
  borderline → lean toward projection.
scope: bo_laksana ONLY — the MSR projection of the WHOLE of L1 into bodha_msr_signals. The root asset.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_SCHEMA_REDESIGN_v1_0.md (THE schema contract — bo_laksana builds bodha_msr_signals to it)
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (S1–S5 + the embedding-consistency protocol — see §STORAGE)
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — moves 2+3 in §JUDGMENT)
  - L2_BODHA_OVERALL_APPROACH_v1_0.md (the governing approach + two pillars)
  - GA_STRUCTURAL_REBUILD_VERIFY_v2_1.md (the keystone it reads — 106,103 rows, refs in fact_value_jsonb)
  - A10_MSR_SPEC_v1_0.md (§4 salience_formula_v1, §11 MVs) + MSR_COMPUTED_VALUE_DRIFT_HANDOFF (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT (Trap 2)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract) + §5 (conformance checklist)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py (rewrite the projection)
  - platform/python-sidecar/bodha_writers/formulas.py (salience_formula_v1 — present; do not change the formula)
  - new migration(s): redefine bodha_msr_signals to the enriched schema (empty table — free to ALTER/recreate)
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (NEW — the MSR retrieval tools + coverage)
must_not_touch: FROZEN orchestrator contract; any ga_* writer; the fan-out writers (B2+).
---

# bo_laksana — MSR: the projection of the WHOLE of L1 (the root)

## §0 — What bo_laksana is
`bo_laksana` projects EVERY meaningful L1 fact — across ALL 14 ga_ assets AND ga_structural's relational +
graph-theoretic surface — into one `bodha_msr_signals` row each, for the native chart × 5 ayanamshas. It does
NOT re-fire predicates, does NOT re-derive values, does NOT curate. It INHERITS each L1 `fact_id` by reference
and ADDS the population-level layer: salience (salience_formula_v1), rank, domain/tradition tags, `fact_kind`
typing, `source_l1_asset`, the L0 classical bridge, a lossless `signal_summary_text`, and cross-ayanamsha
consistency. **The whole point is the anti-drift spine: every `constituent_facts_array` element resolves to a
real L1 fact_id. Prove it on bo_laksana ALONE before any fan-out.**

## §1 — Non-negotiables (every step)
Deterministic-first (no generative LLM; embeddings are a deterministic transform and belong in bo_samskara,
not here); no audience tier; no silent drops (skips logged, must be zero in a clean run); per-chart isolation;
**real fact_ids, never mock**; FROZEN orchestrator contract (`@register('bo_laksana')` WriterBase on
`ctx.db_conn`, never commits/closes, no asset_throughput writes, chart_id+birth_params from ctx.config);
count_sql is data-truth; floors aspirational; **Trap 1** (reference L1 value, never restate) + **Trap 2**
(versioned deterministic formulas only, no narrative in the asset). G52 ELIMINATED — no predicate registry.

## §2 — Preconditions (verify on prod; fix-forward)
1. Proxy up; confirm main == prod; max migration number (handoff cites ~324).
2. ga_structural v2.0 built for the native (build `a712b250`, ~106,103 rows) + all 14 L1 assets built.
3. Apply the enriched `bodha_msr_signals` migration (per L2_BODHA_SCHEMA_REDESIGN §3 + §ELEVATION below);
   readback. The table is EMPTY — ALTER/recreate freely.
4. **Pin the projection count NOW:** `SELECT count(*) FROM chart_facts WHERE chart_id=native AND <projectable
   categories across all 14 assets>` (+ ga_structural's projectable categories). Record per-asset breakdown.
   This is B1's parity target — knowable today, before the build runs.

## §3 — B1.1 — Project the WHOLE of L1 (category-agnostic, no curation)
- DELETE any hardcoded category allow-list. Enumerate projectable categories FROM LIVE chart_facts (every
  `source_asset_id` in the 14-asset L1 set + ga_structural), minus a tiny documented helper-exclude — and even
  helpers are projected as magnitude-signals (§3.3). Data-derived, never hardcoded.
- **Read ga_structural references from `fact_value_jsonb.constituent_fact_ids`** (v2.0 reality — NOT a
  chart_facts column). Store them in the MSR `constituent_facts_array` column. Union base ∪ D1-per_varga
  categories (filtering only `%_per_varga` UNDER-counts D1).
- Salience per signal (salience_formula_v1); NEVER a filter. `top_k_salience_rank` over the full population.

## §4 — B1.2 — The category-agnostic signal model (how 14 assets fit one table)
Each L1 fact → one row where: `signal_type_id` = category:key; `signal_type_class` ∈ the widened enum;
`configuration_jsonb` = the fact's full structured content; `fact_kind` ∈ {relationship, magnitude, position,
time_window, birth_moment, configuration, medical, vastu, prashna, annual, dasha_period}; `source_l1_asset` =
the emitting asset. No per-category column proliferation. This is what makes "project all 14" tractable.

## §5 — B1.3 — Magnitude facts as signals (close the strength/varga gap)
Project every ga_strength / ga_vargas magnitude fact (shadbala per-varga, ashtakavarga, vimsopaka, bhava-bala,
pushkara/vargottama flags, deity/rishi attribution, Lal Kitab specials) as a retrievable signal AND keep the
salience lookup dicts. A fact being a salience input does not bar it from being a stored signal.

## §6 — B1.4 — fact_kind + source_l1_asset + source_subsystem typing on every signal (carry it to retrieval)
Three tags per signal: `fact_kind` (relationship/magnitude/position/...), `source_l1_asset` (the producing writer,
e.g. ga_medical), and **`source_subsystem`** (the DISCIPLINE: structural / nakshatra / strength_ashtakavarga /
medical / vastu / yoga / tajaka / sade_sati / panchanga / varga). `source_subsystem` is mostly derivable from
`source_l1_asset` but is its OWN first-class column because it is THE AXIS that downstream assets depend on:
- **bo_karanajala (CGM)** builds cross-subsystem edges keyed on `source_subsystem` (it cannot connect disciplines
  if signals aren't discipline-tagged);
- **bo_anveshana (discovery)** mines per-subsystem (intra) and across-subsystem (cross) on this axis.
**SCOPE NOTE (honest boundary):** MSR does NOT build cross-subsystem RELATIONSHIPS — those are first-class edges
built by CGM at L2 (bo_karanajala §XS), and discovered by bo_anveshana. MSR's job here is to GUARANTEE the
subsystem TAGGING that makes them possible. Project the facts (all subsystems present, §3) + tag the subsystem;
the cross-discipline JOIN happens at CGM. (This keeps MSR a pure projection — it points down, it does not absorb.)
**Acceptance:** every signal carries a non-null `source_subsystem`; the full subsystem set is represented (no
subsystem silently un-tagged — a coverage check confirms every L1 subsystem produced ≥1 tagged signal).

## §7 — B1.5 — Dedup by ownership
Two signals are duplicates iff same `fact_kind` + same `constituent_facts_array` + same `configuration`.
Magnitude-signal (ga_strength) and relationship-signal (ga_structural using that magnitude) are NOT duplicates.
Weak-but-real never dropped. (The table UNIQUE constraint on (chart,aya,signal_type_id,build,config) helps.)

## §8 — B1.6 — THE ANTI-DRIFT SPINE (the gate — prove on bo_laksana ALONE, HALT on failure)
Run only bo_laksana; verify on PROD in order:
1. **Spine resolves:** every `constituent_facts_array` element resolves to a real L1 fact_id (ga_structural
   via jsonb, value-assets direct) → ZERO unresolved.
2. **Count parity:** MSR count == the §2.4 pinned count (whole L1 population, all 14 assets + ga_structural).
3. **No re-derivation (Trap 1):** ≥10 spot-checks incl. FORENSIC anchors (Sun=Capricorn, Moon=Purva Bhadrapada,
   Lagna=Aries, Muntha=Libra/7H/Venus) inherit L1 values, not recomputed.
4. **Per-asset coverage:** all 14 L1 assets contributed ≥1 signal (no asset silently skipped).
5. **Weak tail present;** idempotent (delete-then-insert per chart×ayanamsha).
**If 1, 2, or 4 fail → fix the projection; do NOT fan out.**

## §9 — B1.7 — THE L0 CLASSICAL BRIDGE (structured)
Populate `classical_sources_jsonb` = {catalog_ids[], rule_ids[], text_chunk_ids[], citations[]} by
deterministic join: named yogas/doshas → brahma_yoga_catalog/brahma_dosha_catalog; rule-traceable configs →
bg_rules (verse ref); classical chunks → bg_texts via L0 id-linkage. Unmatched → empty (not faked); report
coverage ratio. Retrieval returns the FACT + its connected citation(s) together.

## §10 — B1.8 — Lossless signal_summary_text
Deterministic template, EXHAUSTIVE BY CONSTRUCTION: render all typed columns THEN iterate EVERY
`configuration_jsonb` key (no hardcoded subset). No LLM. Fuzz test proves no key omitted. Feeds bo_samskara's
embedding input.

## §11 — B1.9 — Materialized views (A10 §11): top_signals / recurring_patterns / domain_summary; refresh after insert.

## §11B — STORAGE COMPLIANCE (L2_BODHA_STORAGE_ARCHITECTURE — the rules that apply to bo_laksana)
- **S5 jsonb-vs-column discipline (load-bearing here):** anything the LLM filters/ranks by frequently MUST be a
  real INDEXED column, never jsonb-only — specifically `fact_kind`, `source_l1_asset`, `valence`,
  `signature_tier`, `computed_salience`, domain, varga, ayanamsha. Only genuinely per-category variable content
  stays in `configuration_jsonb`. Add the btree/GIN indexes for these in the migration.
- **Embedding protocol awareness (#1–#2):** bo_laksana produces the `signal_summary_text` that bo_samskara
  embeds — it does NOT embed here (deterministic-first: embeddings live in bo_samskara). But the summary text is
  the embedding INPUT, so keep it lossless + stable. Do NOT hardcode an embedding model anywhere in bo_laksana.
- **S2 partitioning readiness:** keep `chart_id` the LEADING column of every index (already in the schema) so
  multi-chart partitioning is a later non-breaking change.

## §12 — B1.10 — Retrieval tools (the retrievability half — built WITH the asset)
Create `platform/src/lib/retrieval/registry/layers/L2_bodha/`: ≥1 tool returning MSR signals filtered by
chart/ayanamsha/domain/fact_kind/source_l1_asset/salience-band, paginated (NEVER LIMIT-drop the weak tail),
each return carrying epistemic_tier + salience + classical_sources_jsonb + constituent_facts_array + fact_kind
+ source_l1_asset + signal_summary_text. Extend the coverage gate: bodha_msr_signals reachable + every
source_l1_asset reachable through it.

## §13 — Acceptance
- [ ] No curation; whole-L1 projection (all 14 assets + ga_structural); category-agnostic model.
- [ ] **Anti-drift spine (§8): zero unresolved; count parity; FORENSIC inherits; all 14 assets covered; weak tail; idempotent.**
- [ ] fact_kind + source_l1_asset + **source_subsystem** on every signal (non-null; every L1 subsystem produces ≥1 tagged signal); dedup clean. (MSR tags the subsystem axis; it does NOT build cross-subsystem relationships — CGM does.)
- [ ] L0 bridge: classical_sources_jsonb populated for matchable signals; raw empty (not faked); ratio reported.
- [ ] signal_summary_text lossless (fuzz test).
- [ ] **MOVE 2:** conditional salience (salience_conditioned_by_jsonb, referencing signal_ids) + signature_tier (chart_defining threads identified; two-pass w/ CGM documented).
- [ ] **MOVE 3:** structured epistemic_jsonb (agreement_state / ayanamsha_fragility / computation_vs_interpretation / calibration_hook) on every signal.
- [ ] 3 MVs; retrieval tools + coverage gate green; every return carries the full provenance set (incl. epistemic + signature_tier).
- [ ] FROZEN contract; migration fresh; surgical apply + readback. Proven on bo_laksana ALONE.

---

# §JUDGMENT — moves 2 + 3 (the data→judgment elevation; FROZEN strategy v1.1)

## §J.1 — MOVE 2: relational/contextual salience + chart-defining tiering
Salience must be RELATIONAL, not just an absolute formula score — a master thinks "this matters BECAUSE that
is also true; this DEFINES the chart; that is a footnote."
- **Conditional salience (new):** store the CONDITIONING relationships — `salience_conditioned_by_jsonb` =
  [{signal_id, effect: amplifies|damps, basis}]. Deterministic from structure (e.g. a debilitated graha's
  significance is AMPLIFIED when its dispositor is also weak; a malefic is DAMPED by neechabhanga). The LLM
  inherits the "it depends on" reasoning. References other signal_ids — never restates their values (Trap 1).
- **signature_tier (new column):** a deterministic classifier ∈ {chart_defining, major, supporting,
  background} separating the 5–10 chart-DEFINING structural threads (for the native: the Rahu–Moon–Jupiter
  axis) from the hundreds of merely-true facts. Computed from (graph centrality from CGM ∪ ga_structural
  centrality) × (cross-ayanamsha stability) × (convergence participation). So the LLM LEADS with what defines
  the chart. (May be finalized after CGM exists — bo_laksana writes a first-pass from ga_structural centrality;
  a refresh pass folds in CGM centrality. Document the two-pass.)

## §J.2 — MOVE 3: structured epistemic honesty (the research-instrument spine — mandatory)
Replace the binary `verification_pass_status` tiering with STRUCTURED, retrievable uncertainty on every signal
(`epistemic_jsonb`), so the LLM natively distinguishes near-certain / contested / method-dependent /
interpretively-ambiguous:
- **tradition_agreement_state** — sources AGREE (high conf) vs DISAGREE (genuinely contested) on this signal's meaning.
- **ayanamsha_fragility** — holds 5/5 (robust) vs 2/5 (method-dependent — flag). (cross_ayanamsha_consistency_score feeds this.)
- **computation_vs_interpretation** — the deterministic computation is solid BUT the classical interpretation is
  ambiguous (distinct from "the number is uncertain"). 
- **calibration_hook** — an empty field L4/L5 later populate with observed accuracy (the correctable loop; bo_laksana writes it null).
This is FIDELITY to the north star (calibrated/testable/correctable), not optional polish. An instrument that
cannot represent its own uncertainty cannot be those things.

---

# §ELEVATION — maximal completeness + depth + width + retrievability (NATIVE-CONFIRMED 2026-06-19)
*Native definitions clarified the axes. Governing principle: project GENEROUSLY for completeness, but NO noise
from irrelevant projections; on genuinely borderline cases, lean TOWARD projection. Everything deterministic;
strictly astrological value per signal/hop.*

## §E.1 — THE TWO PLANES (the load-bearing boundary — confirmed)
Dashas are a TEMPORAL plane; grahas/houses/relationships are a STRUCTURAL plane. **They must NOT intersect in
L2.** bo_laksana projects only **dasha STRUCTURE** — lords, karaka-roles, the significator architecture of each
dasha scheme (timeless facts about the chart's dasha *design*). It does **NOT** project the dated period
TIMELINE (the 536k-row ga_dashas windows). The timeline stays at L1; **L3 Kāla activates** structural signals
against it. The schema's `active_dasha_periods_jsonb` + `dasha_activation_proximity_score` are **L3-fill hooks
(pointers): bo_laksana writes them NULL/empty and NEVER populates them.** L2 stays timeless. This is the one
place "project everything" yields to a layer boundary — by native decision.

**CROSS-PLANE RESONANCE IS EXPLICITLY DEFERRED TO L3 KĀLA (native decision 2026-06-19).** The feature of
detecting that a *dated* moment (e.g. transit Sun/Moon during Mercury mahadasha) *resembles* a natal structural
signature is a TEMPORAL-meets-STRUCTURAL operation that belongs in Kāla, needs a transit capability that does
not yet exist, and will be designed only after ALL data layers are established. **bo_laksana does NOT build any
resonance scaffolding** — no `signature_class`-for-matching, no `resonance_eligible` flag, no transit hooks.
It stays pure timeless projection. The empty L3-fill hooks above are the ONLY forward-reference, and they
require no action now. Do NOT add resonance enabling to this asset. (`signature_class` if populated here is used
ONLY as a static structural fingerprint for within-chart dedup/grouping — never as a transit-matching key.)

## §E.2 — DEPTH = full relationship-CHAIN length (no hop cap)
"Depth" means: follow EVERY relationship chain to its natural astrological TERMINUS — a self-disposited graha,
a closed cycle, or a defined endpoint — with NO artificial 2–3-hop or depth-number cap. Chains are
**HETEROGENEOUS**: a hop may be graha→sign-lord→nakshatra-lord→house→aspecting-graha→config… any astrologically-
valid link. **Every hop must be a GENUINE classical tie** (defined relationship: aspect / conjunction /
lordship / dispositor / nakshatra-lordship / argala / occupancy / significator) — never an arbitrary pair.
- **The ONLY guard is cycle-detection** (a chain that loops back closes at the loop — the cycle IS the
  terminus; this prevents an infinite walk, it does NOT cap astrological depth).
- Store the FULL ordered hop-path; **each hop cites its own source fact_id** (Trap-1 per hop).
- ga_structural v2.0 already computes dispositor_tree + significator_path per-varga — bo_laksana PROJECTS these
  full chains as signals (reference, don't recompute); where a chain extends through entity types ga_structural
  didn't chain, the deeper traversal is a deterministic walk over the defined edges.
This is the deep multi-entity reasoning spine the synthesis LLM traverses. Depth is bounded by the astrology,
not a number.

## §E.3 — WIDTH = entity-type breadth (relationships are NOT planet-only)
Relationships must span ALL astrological entity types: grahas, houses/bhavas, signs/rashis, nakshatras (27) +
lords/padas, aspects, conjunctions, special points (sahams/arudhas/upagrahas/karakas/special-lagnas), and
configurations (yogas/doshas as nodes). A chain or edge may connect any of these. (This is distinct from §E.4
data-domain coverage — width = entity types IN relationships; §E.4 = which data DOMAINS get projected at all.)

## §E.4 — DATA-DOMAIN COVERAGE (a separate completeness axis, also in)
Project the newer L1 data domains the original design lacked, each `fact_kind`-typed:
- **medical** (ga_medical: body_part, body_part_watch, disease_tendency, nakshatra_body_part) → health questions.
- **vastu** (ga_vastu: directional facts) → directional questions.
- **prashna** (ga_prashna: horary) → horary questions.
- **annual** (ga_tajaka: varshaphal) → year-specific reasoning.
- **yoga** (ga_yoga firings).

## §E.5 — ABSENCES = SIGNIFICANT ONLY (curated, classically-grounded — native decision)
Do NOT project every absence (noise). Derive absence-signals ONLY from a curated, classically-grounded list of
significant absences, each citing the classical principle that makes the absence meaningful, e.g.: empty
kendra / trikona; bhava with no occupant AND a weak lord; Kemadruma (Moon with no adjacent support); a
"near-miss" yoga (ingredients almost present); a karaka absent from its expected house; a graha in no
relationship at all (isolated node). Bounded set, deterministic, `fact_kind = absence`. NOT an enumeration of
everything that didn't fire.

## §E.6 — DEPTH-OF-VALUE per signal (fold in; no trade-off)
- **E.6a** Populate ALL salience-decomposition columns per signal (orb_tightness, shadbala_norm, dignity_score,
  the modifiers), not just computed_salience — so the LLM sees WHY, and retrieval can filter on any component.
- **E.6b** Add `valence` (benefic / malefic / mixed / neutral) — does the signal HELP or HARM its domains
  (deterministic from natural + FUNCTIONAL nature per lagna; ga_structural emits functional_class_per_ascendant).
  *(This is a property, not "depth" — kept as its own item per native's correction.)*
- **E.6c** Carry FULL breakdowns in configuration_jsonb (condition_score_breakdown, shadbala 6-component) — not
  just the headline number.
- **E.6d** Populate `cross_ayanamsha_consistency_score` here (5/5 vs 2/5 = a confidence signal; intrinsic, deterministic).

## §E.7 — RETRIEVABILITY (fold in)
- **E.7a** Retrieval facets/indexes on domain, fact_kind, source_l1_asset, valence, salience-band, varga,
  ayanamsha — so "all malefic career signals in D10" is one call.
- **E.7b** TWO text fields: `signal_summary_text` (LOSSLESS — every config key; the EMBEDDING input) +
  `signal_headline_text` (SHORT deterministic human sentence; the LLM's first-read + retrieval display). Both
  pure templates, no LLM. Clarity without losing completeness.
- **E.7c** Cross-reference resolution — constituent_signals_array + contradicts_signals_array exposed as
  resolvable retrieval links (traverse signal→related-signals in one hop).
- **E.7d** Provenance-complete returns as a CONTRACT TEST — a return missing epistemic_tier / citation /
  fact_ids FAILS CI.
- **E.7e** Per-DOMAIN salience normalization (not just per-chart-max) — so "strongest CAREER signal" is directly retrievable.

## §E.8 — Coverage manifest (fold in)
bo_laksana EMITS a per-asset / per-category coverage row (how many of each L1 category became signals) so any
silent miss is visible at build time, not discovered at the eval harness.

---
*End of BO_LAKSANA v1.1. Base: project the WHOLE of L1 (14 assets + ga_structural) category-agnostically, read
refs from fact_value_jsonb.constituent_fact_ids, prove the anti-drift spine alone, bridge to L0, retrieval +
coverage gate. ELEVATION (native-confirmed): dasha STRUCTURE only (timeline → L3, planes don't intersect);
full-length multi-entity relationship chains to terminus (no hop cap, cycle-guard only); entity-type width +
data-domain coverage (medical/vastu/prashna/annual/yoga); significant absences only; full per-signal value
(decomposition + valence + breakdowns + cross-ayanamsha); two-field text; retrieval facets + provenance contract
+ per-domain normalization; coverage manifest. Project generously, no noise; borderline → project.*
