---
artifact: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN
canonical_id: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN
version: 2.1
status: CURRENT — the single execution-governing document for the Beyond-Acharya program
created: 2026-07-02
author: Cowork (strategic workstream) — for native Abhisek Mohanty
folds_in: >
  BEYOND_ACHARYA_SUPPLEMENT_RANKING_SALIENCE_CONSTANTS_v1_0.md (v1.0, 2026-07-02) — the Ranking Doctrine,
  the salience-fabric review (S-A…S-E statistical + A-A…A-D astrological elevations), and the constants
  audit (new L0 asset bg_formula_constants + classification + sensitivity harness). All supplement §3.1
  code-constant claims re-verified against writer source 2026-07-02 (see §1.5-C10…C13). The supplement's
  §4 merge-map is now integrated into §2/§3/§5/§6 below — the supplement is background/rationale; THIS
  document is the executable authority.
supersedes: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v1_0.md (v1.0, 2026-07-02) — this v2.0
  is the v1.0 plan RECONCILED against the live codebase (repo/registry/migrations/writers verified
  2026-07-02). Where v2.0 and v1.0 disagree on a fact, count, id, migration number, or dependency,
  THIS document wins. The strategic shape (no new layers; the E-wave arc; the four north-star tests)
  is preserved unchanged.
reconciliation_basis: >
  Direct code verification of platform/python-sidecar/pipeline/orchestrator/writers/*, both migration
  dirs (platform/migrations + platform/supabase/migrations), the cockpit stats route, bo_laksana
  salience code, the L5 mi_* engine writers, the WriterBase FROZEN contract, and the live
  MCP_SYSTEM_AUDIT_FINDINGS / CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4 briefs. §1.5 is the full ledger.
how_to_use: >
  Paste this document (or its path) as the opening context of a new implementation conversation. It is
  self-contained. Implementation follows the standing split: Cowork authors CLAUDECODE briefs; Claude
  Code in Antigravity implements on the wave's own branch; every wave verifies against PROD, not worktree.
  First brief already authored: CLAUDECODE_BRIEF_BA_W0_SERVING_TRUTH_v1_0.md (repo root).
changelog:
  - v2.1 (2026-07-02): folded in the Ranking Salience Constants supplement. Added §0.1 Ranking Doctrine
    (ratifiable principle: "rank everything, drop nothing, hunt the tail"); the attention-budget protocol
    + complement pass (§5); five statistical + four astrological salience elevations into the bo_laksana v2
    delta (§3); the new L0 asset bg_formula_constants + constants classification + sensitivity harness
    (§3, §6-W5); two structural-conflation bug fixes (ka_sangam confidence=convergence; ka_vighnakara flat
    combustion orb vs L1 per-graha truth) into W4A; two new W1 affinity tables + a constants-ratification
    sheet (§2); four new traps (§7); corrections C10–C13 (§1.5). Wave sequencing unchanged.
  - v2.0 (2026-07-02): reconciled against live code. Nine corrections folded (see §1.5): next migration
    is 385 not 366; charts.chart_type does not exist (new column required); asset count is 82; salience
    v2 must also lift the verification_certainty 0.778 cap (the true strangler) and unify the two
    divergent salience formula sites; embedded-weight unification spans THREE sites not one; E0/W0
    absorbs (does not duplicate) the in-flight audit-fix swarm; DEFECT-001 fix site pinpointed;
    cross-ayanamsha columns confirmed stubbed; stats poll fast-path caveat noted.
  - v1.0 (2026-07-02): first consolidated master plan.
---

# BEYOND-ACHARYA — MASTER IMPLEMENTATION PLAN v2.0 (RECONCILED)

## §0 — MISSION ANCHOR (unchanged from v1.0)

Elevate MARSYS-JIS from "richly built, correctly computed, poorly judged" to an instrument whose served
output — insight, interpretation, prophecy, guidance — exceeds what any individual acharya can derive,
while staying grounded, cited, falsifiable, and calibrated. The program embeds entirely into the existing
six layers (L0 Brahmagyan → L5 Mīmāṃsā), the FROZEN orchestrator, and the Nirmāṇa build tracker. **No new
layers.** New architecture is limited to: one subject type (chart-pair / prashna via a new
`charts.chart_type` discriminator — see §1.5-C2), two feedback arrows (L5→L0 graduation, L5→L2/L4
re-weighting), two services (transit application, waveform fine-grain).

## §0.1 — THE RANKING DOCTRINE (ratifiable principle; governs every serving surface)

The two permanent pillars are **(P1) deterministic completeness** — every astrological quantity pre-computed
by code, never the LLM (LLM arithmetic errs silently and compounds into poisoned synthesis) — and **(P2) no
exclusion** — no parameter is withheld from synthesis. The supplement resolves the apparent tension between
P2 and finite attention:

> **RANK EVERYTHING. DROP NOTHING. HUNT THE TAIL.**
> Attention is finite (context windows for machines, working memory for acharyas). A flat, unranked corpus
> does not give the LLM everything — it gives an arbitrary truncation plus pretraining bias: an
> *uncontrolled, invisible, unauditable* ranking (the 17 MB domain-reading failure is the proof). So the
> real choice is never "prescription vs. open eyes"; it is "a ranking you designed, versioned, and can
> correct vs. one the model improvises invisibly per call." Salience v2 ORDERS the corpus; it never FILTERS
> ("salience is a column, never a filter" — standing native rule). The tail stays served and queryable.
> Discovery of factors OUTSIDE the ranking is guaranteed not by flatness but by five organs (§0.2) and by
> the ranking being a falsifiable, evidence-corrected object (the L5→L2 / L5→L0 arrows), not a dogma.

**This principle is a W1 ratification item.** Once ratified it binds §5's serving contract and §6's ACs.

### §0.2 — The five discovery organs (how the outside factor gets found)

1. **Specificity** (salience v2 term, §3) — statistically extreme configs rise on rarity even at humble
   class prior.
2. **Structural elevation** (CGM, bo_bimba/karanajala) — a low-class signal on a load-bearing dispositor
   path / convergence junction surfaces by WHERE it sits, not its family.
3. **Contradiction surface** (verdict object, §5) — evidence disagreeing with the top verdict ships WITH it,
   by construction; the reading carries its own dissent.
4. **Empirical promotion** (L5, §6-W5) — retrodiction + ablation detect skill in low-prior families; L5→L2
   re-weights; L5→L0 graduation admits genuinely new factors to the canon with falsifier receipts.
5. **The complement pass (NEW)** — a retrieval-layer product that synthesizes over ONLY the tail (head
   withheld) asking "what does the tail say that the head does not?", emitting a cited `tail_divergence` memo
   on the verdict object. Runs on demand, on a per-domain sampling cadence, and ALWAYS during retrodiction
   (a tail-only retrodiction run measures whether the tail carries INDEPENDENT predictive skill — the
   doctrine's own falsifier). Cost: one extra synthesis call. See §5. No practitioner could ever enumerate
   their own tail; this instrument can.

## §1 — CURRENT-STATE ANCHORS (re-verified 2026-07-02)

- Canonical native chart `482012f1-710e-4a25-994a-93821f5871aa`; test chart Abhinandan `1c826d5a-…`;
  entitled family charts Arunima `acdf0d66-…`, Kiran `cb73cd3d-…`. (`362f9f17-…` is a dead phantom.)
- All six layers sealed/closed. **82 registered writers** (`@register` decorators in
  `platform/python-sidecar/pipeline/orchestrator/writers/`; v1.0 said "~81" — trivially off, note
  double-registrations `bg_medical_mappings` and `bg_transit_rules`→`bg_transit_engine`). Orchestrator
  FROZEN (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`) — contract verified verbatim against
  `writers/__init__.py` (WriterBase L65, `register()` L167).
- MCP channel: 45 tools, prod-hardened (M1–M8 sealed, main HEAD `db813823`, CURRENT_STATE v6.08).
- **E0 ops findings are REAL and already have an in-flight brief** (`CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4_v1_0.md`,
  READY-FOR-EXECUTION). W1 (default-ayanamsha / `max_lenses` unblock, F-006/011/031) is DONE +
  prod-verified; W2 (serving wiring) DONE. **W3 (output bounding — F-026 inert `response_format`; F-021
  17 MB `get_domain_reading`) and W4 (L4 schema drift `column "id"` F-005; missing `panchanga_daily`
  F-014; corrupted ephemeris `sepl_18.se1` / kala sidecar F-012/F-030) are OPEN.** → BA-W0 ABSORBS this
  brief rather than duplicating it (§1.5-C7, §6).
- Salience v1 root cause confirmed in `bo_laksana.py::_compute_salience` (L740–808): no
  signal-type/varga terms; practical max salience ≈2.33 < the 3.0 `chart_defining` threshold (L421–428),
  so the top tier is effectively dead. **DEFECT-001 confirmed:** 61,161 / 66,832 (91.5%)
  `constituent_facts_array` refs orphaned (documented `CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT_v1_1.md`
  L112–115); origin = `bo_laksana._build_signal_row` L847–851 copies L1 arrays without re-resolving
  against the rebuilt L1 SHA scheme.
- L5 v1: 12 `mi_*` assets. Scoring engine `mi_pramana` has a stub falsifier (`_IS_STUB_FALSIFIER=True`,
  returns 1.0), no null models / control windows in the live scorer, catch-all attribution
  (`base_rate_adjusted_skill=None`, `n_for_stratum=1` placeholder). Control *definitions* exist as inert
  catalog rows in `mi_kula` (`_CONTROLS`, `fam_null_control`). Skeleton + journal loop + firewall sound
  (keep per MIMAMSA_V2 §1).
- asset_registry rows carry `(asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql)`. Cockpit stats
  (`platform/src/app/api/cockpit/stats/route.ts`) treat `count_sql` (chart-scoped `$1`) as authority
  **but the hot poll path uses `asset_throughput.rows_written` as a cache unless `?mode=live`** — the
  known stale-display trap (§1.5-C4).
- **Migrations: `platform/migrations/` max = 365; `platform/supabase/migrations/` max = 384. The true
  next-free number is 385** (v1.0 said "365"). Always scan BOTH dirs at brief time (§1.5-C1).

## §1.5 — RECONCILIATION LEDGER (v1.0 claims vs. verified reality)

Every material claim in v1.0 §1/§3, tagged **CONFIRMED** / **CORRECTED** / **NEW-CONSTRAINT**. Corrections
(Cn) are folded into §3–§6 below.

| # | v1.0 claim | Verdict | Detail / correction |
|---|---|---|---|
| — | Orchestrator FROZEN WriterBase contract (`@register`, `run`/`plan_substeps`, never commit `ctx.db_conn`, orchestrator sole `asset_throughput` writer) | **CONFIRMED** | `writers/__init__.py` L65/L94–99/L167. Contract quoted verbatim. All new/EXT writers conform. |
| — | 8 NEW ids don't collide | **CONFIRMED** | `bg_class_priors, bg_ghatana, bo_pratijna, ka_avadhi, ka_taranga, sy_koota, sy_graph, sy_timing` — none exist in registry/migrations/python. No `sy_*` prefix exists yet. |
| — | EXT/existing ids exist (incl. `ph_nimitta` for REBUILD v2) | **CONFIRMED** | All present under `writers/`. `ph_nimitta.py` exists → REBUILD-v2 premise valid. 12 `mi_*` confirmed. |
| — | Salience: no type/varga terms; ≈2.33 < 3.0; `chart_defining` dead; DEFECT-001 91.5% | **CONFIRMED** | Terms = orb×shadbala×dignity×verification_certainty×house_wt×av_mult×(1+vargottama)×neechabhanga×cancellation. |
| — | Cross-ayanamsha robustness columns to "fill" | **CONFIRMED** (they are stubbed NULL) | `cross_ayanamsha_consistency_score`, `strength_normalized_to_chart_max`, `cross_system_consensus_count`, `varga_provenance_jsonb`, `salience_confidence_interval_jsonb` all written `None`. 5 per-ayanamsha rows ARE emitted (raw material present). |
| — | mi_pramana stub falsifier / mi_kula embedded weights / transit service-not-storage | **CONFIRMED** | `mi_pramana._IS_STUB_FALSIFIER=True`; `mi_kula._FAMILIES` prior_weight literals; transits REAL (not stub) in `pipeline/transit_search.py` + `services/ka_gochara`. |
| C1 | "Migrations currently at 365" | **CORRECTED** | Next-free = **385** (supabase dir reaches 384: `382_mcp_sessions`, `383_mcp_oauth`, `384_mcp_api_keys_model_family`). v1.0's own §7 trap #2 is correct; its §1 number was one-dir. |
| C2 | Prashna/synastry via `charts.chart_type='prashna'|'synastry'` | **NEW-CONSTRAINT** | **`charts.chart_type` does NOT exist.** `charts` (001_baseline L134) has only `role CHECK (native/tertiary/fixture)`. The only `chart_type` in schema is on `school_analysis_runs` (natal/varsha_kundali). → Wave that introduces prashna/synastry MUST ship a migration adding `charts.chart_type` (default `'natal'`, backfill all existing) BEFORE any chart-type build path. This is net-new schema v1.0 glossed. |
| C3 | "~81 assets" | **CORRECTED (trivial)** | 82 registered writers. Set each new asset's `target_floor` post-build (never pre-fabricate). |
| C4 | count_sql is cockpit truth | **CONFIRMED + CAVEAT** | Poll fast-path reads `asset_throughput.rows_written`; `?mode=live` forces count_sql. New scoring assets must (a) ship correct chart-scoped count_sql AND (b) ensure `Clear` nulls `rows_written` (the documented stale-display bug) so the tracker cannot lie post-clear. |
| C5 | bo_laksana FRM v2.0 = class_prior × varga_weight × specificity × v1 terms × dasha boost | **CORRECTED (insufficient)** | The dominant strangler is the **hard `verification_certainty` cap = log(1+5)/log(10) ≈ 0.778** (corroboration fixed at 5/2). v2 MUST lift/replace this cap or `chart_defining` stays dead even with class/varga terms. ALSO: `bo_laksana._compute_salience` DIVERGES from the canonical `bodha_writers/formulas.py::salience_formula_v1` (writer omits the dasha-activation, aspect, argala terms). v2 must UNIFY to a single formula site (one `salience_formula_v2`) — no second inline copy. |
| C6 | mi_kula "deletes its embedded weight catalog" (single site) | **CORRECTED (three sites)** | Embedded weights live in THREE places: `mi_kula._FAMILIES.prior_weight`, `mi_pariksha._DIM_WEIGHTS`, and mi_pramana's dimension weights. The `bg_class_priors` unification must retire ALL THREE, or a stale copy silently overrides. |
| C7 | W0/E0 = fresh "serving truth" build | **CORRECTED (absorb, don't duplicate)** | E0's items map 1:1 to OPEN findings in the in-flight `CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4` (W3=F-026/F-021; W4=F-005/F-014/F-012/F-030). BA-W0 = verify that swarm's W1–W4 landed on PROD + run the residual E0 checks; it does not re-author those fixes. |
| C8 | (implicit) governance state current | **NEW-CONSTRAINT** | CURRENT_STATE v6.08 does not yet reference the audit-fix campaign. A governance-sync line is a W0 exit item. |
| C9 | DEFECT-001 "rebuild resolves" | **CONFIRMED + PINNED** | Fix site = `bo_laksana._build_signal_row` L847–851 + write path L975: must re-resolve `constituent_facts_array` against CURRENT `chart_facts` fact_ids (or floor to self with a logged reason), not copy the stale L1 array verbatim. Degeneracy/resolution gate must assert ≥ threshold% resolve before seal. |
| C10 | Supplement §3.1 constants inventory | **CONFIRMED (8/10 exact)** | `ka_vighnakara._COMBUSTION_ORB_DEG=6.0` flat (L56, cited "Parāśara Āstangata" but no śāstra uses a flat 6°); `_SEVERITY_THRESHOLDS=[(0.70,severe),(0.40,moderate),…]`; `ka_sangam._insert_windows` binds `confidence_score` = `convergence_score` (L474 comment "mirrors") + `dasha_score>0.3` flag; `mi_sambandha._PRIOR_PROPENSITIES` career 0.40/0.35/0.25; `mi_gunanaka._MIN_N_PROMOTE=10`, `_MAX_DIVERGENCE_RATIO=3.0`; `mi_jivanaghatana` MD5 mod10≥8≈20%; `bo_laksana` corroboration 5/2 (L778). |
| C11 | CGM 2.326672 / edge 0.581668 / RM 0.28 are "constants" | **CORRECTED (framing)** | These are **runtime data-degeneracies** (upstream salience/resonance collapse), NOT hardcoded literals. bo_bimba computes node strength (`graha_strength.get(g,0.5)`), bo_upaya computes `resonance_score_v1` (formulas.py). → They are FIXED as a side-effect of salience v2 + the degeneracy gate (§7-5), not by editing a literal. |
| C12 | "Two combustion truths" | **CONFIRMED + PINNED** | L1 combustion is in `ga_writers/ga_condition_writer.py` (NOT orchestrator `ga_condition.py`), reads per-graha orbs from the EXISTING L0 table `bg_combustion_orbs` (fallback dict L627–636: Moon 12/10, Mars 17/15, …). → W4A single-truth fix: `ka_vighnakara` reads `bg_combustion_orbs` / the L1 fact, deletes its flat 6°. No new table needed. |
| C13 | `bg_formula_constants` / `brahma_formula_constants` NEW L0 asset | **CONFIRMED CLEAR** | No collision — appears only in planning `.md`. Same governance move as the 3-site embedded-weight unification (C6): one constants surface, all consumers read it. |
| C14 | (memory) "G52 signal_type_registry global prereq" for class-priors | **CORRECTED** | `signal_type_registry` is **RETIRED** (migration 223 `DROP TABLE`). `bg_class_priors` must key on the free-TEXT columns on `bodha_msr_signals`: `signal_type_class` (11 values), `fact_kind` (12), `source_subsystem` (12), `signal_tradition` — NOT a registry table. Seeded accordingly in the W1 package §2. |
| C15 | (implicit) a canonical `domain` enum exists | **NEW-CONSTRAINT** | There is NO canonical domain enum — 8 divergent code sites (career/marriage vs relationship/relational, finance/financial/wealth, …); only `kala_bhavishya_domain_check` is DB-enforced (7 values). The W1 package §1 DEFINES the canonical 12-domain taxonomy; a **W2A-prerequisite migration** normalizes the 8 sites to it. All A-A/A-D affinity tables + query-time domain routing key on it. |

## §2 — THE NATIVE JUDGMENT SITTING (gates everything; schedule FIRST) — unchanged

One sitting, three ratification tables + two sign-offs. Cowork prepares structured DRAFTS for correction
(never blank pages):

1. **Salience class-prior table** (→ `bg_class_priors` seed): weight per signal class/family (raja-yoga
   family vs dosha-major vs dignity-extreme vs karaka-alignment vs house-lord placement vs per-varga
   atomic tallies); the varga-grain weight vector (D1 … D2700); the composite-aggregation ruling; **and
   the `verification_certainty` re-scaling decision** (C5 — how corroboration should scale, since the
   0.778 cap must change and that is a native judgment, not a re-pick).
2. **Event ontology** (→ `brahma_event_ontology` seed): ~20–30 event classes; per class: signature model
   (houses/lords/karakas/vargas/dasha rules/transit triggers), magnitude floor, adjacency (for PARTIAL
   adjudication), base-rate prior by age band, citations.
3. **Activity ontology** (→ `brahma_activity_ontology` seed): elective/undertaking classes → significators
   + fructification rules.
4. **Constants-ratification sheet** (→ `bg_formula_constants` seed; supplement C-2): one sheet of every
   NATIVE-JUDGMENT constant with current value, proposed classical correction where one applies, and bounds.
   Headliners: **per-graha combustion orbs** (replace the flat 6° — Moon 12°, Mars 17°, Mercury 14°/12°R,
   Jupiter 11°, Venus 10°/8°R, Saturn 15° — reconcile to the same values L1's `bg_combustion_orbs` already
   uses), obstruction severity thresholds, magnitude tiers, `mi_sambandha` channel propensity priors, the
   L2 house-weight / dignity-score vectors, corroboration levels (5/2). (Structural-conflation BUGS —
   confidence=convergence, flat-orb duplication — are NOT ratification items; they go to W4A as fixes.)
5. **Two small affinity tables** (query-time salience, §3): **graha × domain affinity** (A-A karaka
   congruence — e.g. Saturn↑career, Jupiter↑progeny) and **domain × varga affinity** (A-D — D10↑career,
   D9↑marriage, D7↑progeny). Classically cited, native-ratified.
6. Sign-off: **the Ranking Doctrine (§0.1)**; MIMAMSA_V2 §1 keep/replace verdicts; Loop-D resonance
   quarantine; REFUTED-requires-attestation; the `verification_certainty` re-scale (C5); the
   attention-budget split default (§5, 70/20/10).
7. Sign-off: this plan's wave sequencing (§6), the E4 classical-completions ranking, **and the
   prashna/synastry `chart_type` discriminator design (C2)**.

## §3 — FULL ASSET DELTA (reconciled)

Legend: **NEW** = new writer + migration + registry row + DAG edge · **EXT** = reopen existing writer
(seal-amendment) · **FRM** = formula bump + rebuild · scope `per_chart` unless noted. All writers conform
to the FROZEN contract. **Migration numbering starts at 385 and scans both dirs at each brief (C1).**

### L0 Brahmagyan (global scope; ON CONFLICT upsert)

| Asset | Action | Tables | Notes |
|---|---|---|---|
| `bg_class_priors` | **NEW** | `brahma_class_priors` | Salience class-prior + varga-weight vectors + verification_certainty re-scale params (C5); native-ratified, versioned (`prior_version`). **Single substance with mi_kula's family registry** — mi_kula v2 READS this table (retire embedded weights per C6). L5 snapshots overlay it, never overwrite (two-key). |
| `bg_ghatana` | **NEW** | `brahma_event_ontology`, `brahma_activity_ontology` | Event + activity ontologies (§2 seeds); machine-decidable matching/adjacency jsonb; base-rate priors by age band. |
| `bg_formula_constants` | **NEW** | `brahma_formula_constants` | The CONSTANTS REGISTRY (supplement C-1). `(constant_id, consumer_assets[], value_jsonb, class[classical|native_judgment|engineering], citation_or_ratification, calibratable, bounds, version)`. ALL classical + judgment constants extracted from code (incl. per-graha combustion orbs, severity thresholds, magnitude tiers, channel priors, L2 house-weight/dignity vectors, corroboration levels) so every judgment number becomes visible, versioned, citable, and (where flagged) L5-adjustable within bounds. Writers READ it — same pattern as `bg_class_priors`; also the natural home for the `bg_class_priors` weights and the §5 attention-budget split. Global scope, upsert, trivial count_sql. Structural-conflation values are NOT migrated in — they're deleted at source (W4A). |
| `bg_transit_rules` | EXT | `bg_transit_rules` (+`bg_transit_av_gates`) | AV kakshya/SAV transit gates; vedha; double-transit (Jupiter+Saturn); cited. (Writer `bg_transit_rules.py` also registers `bg_transit_engine` — amend both consciously.) |
| `bg_rules` | EXT | `sutravali_rules` | Nadi extraction pass (Bhrigu Nandi Nadi + Nadi Navamsa); muhurta/tajika Phase-2 chunks. |

### L1 Gaṇita (per-chart; delete-then-insert per §N.3; seal-amendment — L1-E precedent)

| Asset | Action | New fact content |
|---|---|---|
| `ga_sensitive` | EXT | Bhava arudhas A1–A12 incl. Arudha Lagna + Upapada (`fact_category=bhava_arudha`); Karakamsha + Swamsha derived facts. |
| `ga_dashas` | EXT | Classical Jaimini Chara dasha (Rao-standard sign periods); [optional, native-ranked: Narayana]. |
| `ga_strength` | EXT | Per-varga Shadbala/bhava-bala (native ruling 2026-06-17; label computed-extension; floor NULL+reason where classical is D1-only — canonical-or-floor). |
| `ga_condition` | EXT | Graha yuddha (by longitude, cited method); lajjitadi + sayanadi avasthas (unfloor). |

L1 exit gates: FORENSIC 7/7 on 482012f1; chart-agnostic contamination check on 1c826d5a; new
fact_categories visible in `chart_facts` under all 5 ayanamshas (or INVARIANT).

### L2 Bodha (per-chart; ONE regeneration absorbs everything below + DEFECT-001 MSR rebuild)

| Asset | Action | Detail |
|---|---|---|
| `bo_laksana` | **FRM v2.0** | `salience_v2 = class_prior(bg_class_priors) × varga_weight × specificity × rescaled_verification × condition_terms × dasha_activation_boost (L3 hook)`. **MUST lift the 0.778 verification cap (C5)** and **unify to a single formula site — retire the divergent inline copy vs formulas.py (C5).** Hierarchical aggregation (atomic families roll into composite signals — atoms queryable, never top-band). Recut `signature_tier` thresholds against the v2 distribution so `chart_defining` FIRES. Fill the 5 stubbed cross-ayanamsha/robustness columns. **DEFECT-001:** re-resolve `constituent_facts_array` against current L1 SHA at `_build_signal_row` (C9); resolution gate before seal. **PLUS supplement elevations (stored terms):** **S-A** within-class normalization — store BOTH `computed_salience` (absolute) AND `salience_pctl_in_class` (percentile within family for this chart); cross-class order = `class_prior × f(pctl)` (priors decide between families, percentiles within — kills ties, trivializes the degeneracy gate, and makes any residual verification cap harmless). **S-C** NULL-propagation — a missing input yields a NULL component + `salience_inputs_complete` flag, never a silent 0.5/1.0 neutral (canonical-or-floor in spirit). **S-D** `salience_robustness` (from the 5-ayanamsha slices) + `inputs_complete` served with the score. **A-B** `bala_gate` — weak-constituent yogas rank as a distinct served state "present-but-enfeebled" (constituent bala from L1). **A-C** `functional_context` — functional benefic/malefic per lagna from `ga_structural`. |
| `bo_bimba` / `bo_karanajala` | EXT | Project L1 relational riches as typed edges (dispositor, argala/virodha, parivartana, yoga-membership, karaka-role, nakshatra-dispositor, KP sub-lord chains); fill `valence`, `relationship_basis`, `affected_domains`; node strength from salience v2 (heals the degenerate 2.326672 node / 0.581668 edge constants — C11). Contradiction rows gain `domains_affected` + reconciliation record (evidence-weighted, citing both sides + activation state). NOTE: `bodha_contradictions` currently 0 rows for 1c826d5a — this rebuild must populate it. **S-B effective-evidence:** CDLM convergence sums (and bo_sangati concordance, ka_sangam windows) must de-duplicate by family cluster before summing (contribution ∝ log(1+n_family) or capped by W2 aggregation composites) and report `effective_evidence_count` alongside raw — volume must stop masquerading as independent evidence (the career `convergence_count: 11,970` artifact). |
| `bo_pratijna` | **NEW** | `bodha_pratijna` — Promise Register: chart × event_class (from `brahma_event_ontology`): promised/denied/conditional, grade, supporting + contradicting signal refs (salience-v2-ranked), varga confirmation state. The WHAT of prophecy; also a served product. |
| `bo_sangati` | EXT | `bodha_triangulation` — per question-class × tradition stack (Parashari/Jaimini/KP/Tajika): independent verdict inputs + concordance score. |
| `bo_samskara` | EXT (wave W8) | Whole-chart + per-domain configuration embeddings (pinned local model). |

Regeneration discipline: L2 rebuilds ONCE for W2 (all the above in one pass), on ≥2 charts, with the
degenerate-distribution gate (no scoring column may collapse to constants — C4/§7-5) + trap-1 authority
check + DEFECT-001 resolution gate.

### L3 Kāla

| Asset | Action | Detail |
|---|---|---|
| `ka_yojaka` | EXT | Fill signals' dasha_activation columns across ALL 7 dasha systems; promise-linked activation predicates: for each `bodha_pratijna` row, periods whose lords connect to the promise (multi-system cross-confirmation = first-class score). |
| `ka_avadhi` | **NEW** | `kala_avadhi` — Period Dossiers: per MD/AD × chart: lord natal-dossier refs, activated promise refs, sub-lord modulation, quality components + citations. Powers Q1 ("how will my Ketu dasha be"). |
| `ka_taranga` | **NEW** | `kala_taranga` — Activation Waveform: coarse (monthly) per-domain/per-event-class activation curves 1950–2100 from dasha×transit×promise convolution; fine resolution = **service** (never stored day-grain). L4 anchors become its gated local maxima. |
| transit service | EXT | AV kakshya/SAV gates + double-transit checks as on-demand computation. Engine REAL today (`pipeline/transit_search.py` + `services/ka_gochara`); EXT = add AV-gate logic, not build from scratch. |
| `ka_sangam` | FIX (W4A) | **Structural-conflation bug (C10):** `_insert_windows` binds `confidence_score` = `convergence_score` (one number, two names). Anchor v2 (posterior ≠ convergence) supersedes it at L4, but the L3 window table must stop mirroring — give `confidence_score` a real derivation or drop the column. Also apply S-B effective-evidence to window scores. |
| `ka_vighnakara` | FIX (W4A) | **Structural-conflation bug (C12):** flat `_COMBUSTION_ORB_DEG=6.0` matches no śāstra AND duplicates L1's per-graha combustion (`ga_condition_writer` reading `bg_combustion_orbs`). Repoint `ka_vighnakara` to the L1 combustion fact / `bg_combustion_orbs` (single truth); delete the flat constant. Severity thresholds move to `bg_formula_constants`. |

### L4 Phala

| Asset | Action | Detail |
|---|---|---|
| `ph_nimitta` | **REBUILD v2** | Anchor v2 = `(event_class, window, magnitude, posterior)`; `posterior = base_rate(event_class, age_band, window) × promise_lift × activation_lift × trigger_lift`; lift_vector frozen per anchor; structured falsifier `{event_class, magnitude_floor, window, attestation_required}`; G-LADDER retired (ayanamsha robustness → lift modifier); full probability range (incl. "unlikely/denied"). **Note: the L4 schema-drift fix (missing `id`/`anchor_id`, F-005) is a W0 prerequisite (migration 365 already targets it) — confirm landed before rebuild.** |
| `ph_muhurta` | EXT | Activity-aware election: `brahma_activity_ontology` significators × panchanga × tarabala/chandrabala vs the native's chart; fructification hooks (Loop B). |
| prashna path | **NEW (chart-type)** | Requires the `charts.chart_type` migration FIRST (C2). `chart_type='prashna'` build path: cast at question time, minimal asset set (ga_positions / ga_panchanga / prashna judgment); consumes existing L0 `bg_prashna_rules`. Precedent: chart-type, not layer. |

### L5 Mīmāṃsā (implements MIMAMSA_V2 in full)

| Asset | Action | Detail |
|---|---|---|
| `mi_kula` | v2 | Reads `bg_class_priors` (deletes embedded `_FAMILIES` weights); neg-control battery retained. |
| `mi_jivanaghatana` | EXT | + period attestation flags (REFUTED requires attested-complete periods). |
| `mi_pramana` | **ENGINE v2** | Adjudication per MIMAMSA_V2 §4 (CONFIRMED/PARTIAL/REFUTED/EXPIRED + FALSE_ALARM on controls; ontology adjacency replaces binary domain; structured falsifiers replace the `_IS_STUB_FALSIFIER` stub); scoring per §5 (Brier vs climatology null; sharpness via null; rank-aware retrodiction credit; ECE). **Retire mi_pramana's embedded dimension weights → bg_class_priors (C6).** |
| `mi_pariksha` | **v2 substeps** | `retrodiction_generate` (blind, date-filtered — the ph_pramana firewall generalized) · `control_windows` (≥3/event, stratified) · `ablation` (per technique-family masked reruns) · `attribution` (analytic from lift_vectors; catch-all fallback DELETED) · `neg_control` + `discovery` retained. **Retire `_DIM_WEIGHTS` → bg_class_priors (C6).** |
| `mi_gunanaka` | v2 | Hierarchical shrinkage replaces n≥10 gates (cell→parent pooling; at n=0 posterior = classical prior); 3× divergence cap RETAINED; versioned calibration snapshots. |
| `mi_adhilepa` | WIRE | Snapshot publication two-key (system proposes, native co-signs); overlays to 3 sinks only: `bg_class_priors` overlay, R-4 lift calibrations, triangulation tradition-weights. Never L1. |
| `mi_seva`/`mi_abhilekha` | WIRE | Daily closed-window scan → ask-cards; journal resync; Loop-B prashna follow-ups; Loop-D resonance stored QUARANTINED (S4 presentation only). |
| `mi_sambandha` | KEEP+ | Manifestation grammar live from adjudicated outcomes (Dirichlet smoothing on v1 priors). |

### SY — chart-pair subject type (wave W8)

Requires `charts.chart_type` (C2). `chart_type='synastry'` (two member chart_ids) + minimal `sy_koota`
(ashtakoota + dosha-koota), `sy_graph` (inter-chart aspects/overlays), `sy_timing` (dasha overlap) —
onboarded through the frozen contract like a layer; family-lattice cross-chart consistency checks feed L5
as labeled consistency evidence.

## §4 — NIRMĀṆA / ORCHESTRATOR EMBEDDING MECHANICS (reconciled)

1. **Per NEW asset:** one surgical migration (number = max(both dirs)+1, currently **385**) =
   `CREATE TABLE` + `asset_registry` INSERT (correct layer, sort_order, sanskrit/english names,
   `scope`, `has_writer=true`, chart-scoped `count_sql` with `$1`, `target_floor`=achieved post-build)
   + DAG `depends_on` edges. Then the `@register('<asset_id>')` writer. Orchestrator NEVER modified; if a
   writer seems to need a contract change → STOP, raise to native.
2. **Per EXT asset:** seal-amendment (L1-E pattern): amendment note in the layer seal, writer extension,
   migration only if new tables/columns, rebuild REPLACES per §N.3.
3. **Per FRM asset:** bump `*_formula_version`, document in the asset header, rebuild regenerates. For
   `bo_laksana` specifically: unify to ONE formula function (C5) — do not leave the inline/shared split.
4. **Schema-prerequisite migrations (do these before the dependent build path):** (a) `charts.chart_type`
   column for prashna/synastry (C2); (b) confirm L4 `id`/`anchor_id` drift fix (migration 365) is live
   before `ph_nimitta` rebuild.
5. **DAG additions (dependency order the cockpit will drive):**
   `bg_class_priors, bg_ghatana, bg_formula_constants` (roots) → L1 EXTs → `bo_laksana v2` →
   `bo_bimba/karanajala, bo_pratijna, bo_sangati` → `ka_yojaka EXT` → `ka_avadhi, ka_taranga` →
   `ph_nimitta v2, ph_muhurta` →
   `mi_kula → mi_jivanaghatana → mi_bhavisya → mi_pramana → mi_pariksha → mi_gunanaka → mi_adhilepa`.
   (`bg_formula_constants` is a root every judgment-bearing writer reads — seed it in W2A with `bg_class_priors`.)
   **Stored vs query-time split (S-E, hard rule):** salience is computed at BUILD and stored STATIC. The
   temporal/contextual terms — `dasha_activation_boost` (S-E), `karaka_congruence` (A-A), domain-conditioned
   `varga_affinity` (A-D) — are applied AT QUERY TIME (served = static × activation(t) × domain terms).
   Never bake activation or a domain term into the stored column — it would go stale the day the dasha (or
   the question's domain) changes.
6. **Build/regeneration per chart (one cockpit "Rebuild" cascade):** L0 seeds (global, once) → L1 (FORENSIC
   + contamination gates) → L2 single regeneration (degenerate-distribution + DEFECT-001 resolution gates)
   → L3 → L4 → L5. Two-chart rule: every wave verifies on 482012f1 AND 1c826d5a. **After each rebuild,
   confirm the cockpit `Clear` path nulls `asset_throughput.rows_written` so count_sql is authoritative
   (C4).**
7. **Services** (transit application, waveform fine-grain, prashna casting): Python sidecar / retrieval
   layer, registered as service-handler assets (mi_seva precedent: writer verifies readiness, creates no
   build rows). Transit engine already REAL — extend, don't rebuild.

## §5 — NON-ASSET WORKSTREAMS (unchanged in substance)

- **Retrieval fork:** the VERDICT OBJECT (top-k reconciled findings: claim, evidence, contradiction
  resolution, tradition concordance, activation state, ayanamsha robustness, confidence, falsifier,
  citations — LLM narrates ON TOP, never instead); period-reading composition (Q1) over `ka_avadhi`;
  undertaking composition (Q4); activation-aware + calibration-aware ranking; `query_calibration` v2
  (per-cell skill/n/CI/snapshot). Registry capabilities only — retrieval remains the single query brain.
  **Query-time salience terms (§0.2 organs, S-E/A-A/A-D):** the served ranking applies
  `dasha_activation_boost`, `karaka_congruence` (graha×domain table), and domain-conditioned `varga_affinity`
  on top of stored static salience — computed per query because domain and time are known only then.
- **Attention-budget protocol (§5, W3, doctrine serving contract):** every synthesis call allocates its
  context budget EXPLICITLY. Default **70/20/10**: 70% ranked head (salience v2 order) · 20% dissent
  (contradictions + anomalies + ayanamsha-fragile flags) · 10% tail sample (stratified random below the
  cutoff — a standing ε-greedy exploration term). The split is a versioned constant in
  `bg_formula_constants`, tunable per query class, and L5-evaluable (does a larger tail share ever change
  verdicts?). This converts "how much should the model see beyond the obvious" from vibes into a governed,
  tested parameter.
- **The complement pass (§0.2 organ 5, W3):** a retrieval-layer product that synthesizes over ONLY the tail
  (head withheld) and emits a cited `tail_divergence` memo on the verdict object — "what does the tail say
  that the head does not?". On demand + per-domain sampling cadence + ALWAYS during retrodiction (the
  tail-only retrodiction run is the doctrine's empirical falsifier: does the tail carry INDEPENDENT skill?).
  One extra synthesis call; nearly free.
- **MCP channel:** tool updates to serve the above; query-class taxonomy becomes the living readiness
  matrix — a class is GREEN only when every stage of its recipe serves on prod.
- **Portal:** ask-cards (closed-window adjudication), period-attestation card, structured LEL intake form
  (event_class + magnitude per ontology), prashna follow-up scheduler, calibration-snapshot co-sign UI.
- **Ops (W0 = E0):** ABSORB `CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4` (C7). Deploy-truth pass — Cloud Run
  revision SHA vs the swarm's merge SHAs; W3 bounding live-verify (F-026/F-021); L4 schema (F-005); kala
  sidecar / ephemeris (F-012/F-030); `panchanga_daily` (F-014). Governance-sync CURRENT_STATE (C8).

## §6 — EXECUTION PROGRAM (waves → named CLAUDECODE briefs, reconciled)

> Standing mechanics per wave: Cowork authors `CLAUDECODE_BRIEF_*.md` (governing scope:
> `may_touch`/`must_not_touch`, acceptance criteria each tagged `[verify-against: prod|db|ci]`) → Claude
> Code in Antigravity implements on the wave's own branch → prod gate re-checks headline numbers on live
> prod before the wave claims done (the V1.3 scar). Model policy: Gemini/DeepSeek in build/narration;
> scoring paths LLM-free; Anthropic banned unless native asks.

| Wave | Content | Briefs | Gate to next |
|---|---|---|---|
| **W0 = E0** | Serving truth — **absorb the in-flight audit swarm (C7)**: verify W1(done)/W2(done) on prod; drive W3 (F-026 bounding, F-021 17 MB) + W4 (F-005 L4 schema, F-014 panchanga_daily, F-012/030 kala sidecar/ephemeris) to done; governance-sync CURRENT_STATE (C8) | **`CLAUDECODE_BRIEF_BA_W0_SERVING_TRUTH_v1_0.md` (authored — repo root)** | All 45 tools structured-respond on prod; bounding demonstrably live (`get_domain_reading` bounded, `response_format` honored); kala/L4/panchanga serving; CURRENT_STATE references the campaign. |
| **W1 = judgment sitting** | §2 sitting → ratified seeds: 3 core tables (class-priors, event ontology, activity ontology) + **constants-ratification sheet (Table 4)** + **two affinity tables (graha×domain, domain×varga)** + **canonical domain taxonomy (C15)** + Doctrine + cap-rescale + attention-split + chart_type design. **AUTHORED: `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` (all five tables drafted under native delegation).** | `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` (Cowork-authored; native glance on its §0.2 items) | Package ratified (native glance on 4 flagged items) + sign-offs recorded (incl. Doctrine §0.1). |
| **W2 = E1** | `bg_class_priors` + `bg_ghatana` + **`bg_formula_constants`** + L1 EXTs + L2 single regeneration (salience v2 w/ cap-lift + formula unification + **S-A percentiles, S-C null-propagation, S-D robustness, A-B bala_gate, A-C functional_context, S-B effective-evidence**, edges, contradictions, pratijna, triangulation, DEFECT-001 resolution) | `BA_W2A_L0_SEEDS_AND_L1_EXT` (incl. bg_formula_constants + per-graha combustion orbs), `BA_W2B_L2_REGENERATION` | G10-style: career top-10 on 482012f1 = 10th-lord/karaka/yoga structures, zero sub-varga atoms; constituent_facts ≥ target% resolve; `signature_tier` fires `chart_defining`; `salience_pctl_in_class` populated + no scoring column degenerate; two-chart + degeneracy gates pass. |
| **W3 = E2** | Verdict object + serving (retrieval/MCP): triangulation, ayanamsha ensemble, activation-aware ranking + **query-time terms (S-E activation, A-A karaka congruence, A-D varga affinity)** + **attention-budget protocol (70/20/10)** + **complement pass (`tail_divergence`)** | `BA_W3_VERDICT_AND_SERVING` | External LLM over MCP produces a cited, reconciled career reading judged acharya-grade (rubric ≥ WS-3 bar); verdict object carries dissent + `tail_divergence`; budget split served + versioned. |
| **W4 = E3** | R-pipeline: `ka_yojaka` EXT + `ka_avadhi` + `ka_taranga` + `ph_nimitta v2` + `ph_muhurta` EXT + prashna path (**`charts.chart_type` migration first — C2**) + **W4A structural-conflation fixes (ka_sangam confidence=convergence; ka_vighnakara single-truth combustion — C10/C12)** | `BA_W4A_KALA_ACTIVATION`, `BA_W4B_PHALA_V2` | Q1 + Q3 + Q4 recipes GREEN on prod; anchors span full probability range with LEL-decidable falsifiers; posteriors carry lift_vectors; confidence≠convergence and one combustion truth. |
| **W5 = learning live** | MIMAMSA_V2 R1+R2 (retrodiction, controls, ablation, scoring v2, shrinkage, first snapshot); **retire all 3 embedded-weight sites (C6)**; **constants sensitivity harness (C-3)**; **tail-only retrodiction (doctrine falsifier)** | `BA_W5_MIMAMSA_V2_ENGINE` | First honest skill table on 482012f1 (45 train/12 held-out); ≥1 family beats null OR null finding published; snapshot changes served weights reversibly under two-key; each `bg_formula_constants` entry ranked by output sensitivity; tail's independent skill measured. |
| **W6 = E4** | Classical completions (Nadi rules, AV-transit L0, avasthas) per native ranking | `BA_W6_CLASSICAL_COMPLETIONS` | New fact_categories flow through bo_laksana v2 ranked (not noise). |
| **W7 = portal loops** | MIMAMSA_V2 R3 (ask-cards, attestation, prashna follow-ups, co-sign UI) | `BA_W7_PORTAL_LEARNING_LOOPS` | Closed windows convert to adjudicated outcomes ≥80% in 7 days. |
| **W8 = E5/E6** | Research organs: synastry `sy_*` (needs C2), chart embeddings + case retrieval, motif mining, rule-induction w/ L5→L0 graduation | `BA_W8_RESEARCH_ORGANS` (split at brief time) | Gated on multi-chart corpus growth; each organ consumes W5's calibration corpus. |

Parallelizable: W4A/W4B after W2; W6 alongside W4; W7 alongside W6. Strictly serial: W0→W1→W2, W4→W5.

## §7 — TRAPS REGISTER (reconciled)

1. Verify against PROD, not worktree — every AC tagged; wave-complete prod gate mandatory.
2. **Two-dir migration numbering — next-free is 385, scan BOTH dirs at brief time (C1).**
3. Surgical migrations only; never deploy.yml-auto / bulk migrate.
4. **count_sql is cockpit truth — ship correct chart-scoped `count_sql` AND ensure `Clear` nulls
   `asset_throughput.rows_written` (stale-display bug, C4).**
5. Degenerate-distribution gate on EVERY new scoring column (salience v2, posteriors, skill cells) — halt
   if a column collapses to constants (the 2.326672 / 0.28 scars).
6. L1-authority (trap-1): L2+ references fact_ids, never restates computed values. **DEFECT-001 is the
   live instance — re-resolve, don't copy (C9).**
7. Chart-agnostic: no native leakage into non-native charts; contamination check post-rebuild.
8. Canonical-or-floor: cited values or NULL+reason; formula weights are native judgments (halt for
   sign-off, never re-pick) — includes the verification-cap re-scale (C5).
9. Anthropic API banned in build/narration (Gemini/DeepSeek); scoring paths LLM-free (D-1).
10. Destructive ops need reverse-citation gates; brief schema promises audited against migration files.
11. Retrieval layer stays FROZEN except through its own fork's contract; MCP consumes the registry.
12. **NEW — `charts.chart_type` does not exist: any chart-type path ships the column migration first (C2).**
13. **NEW — embedded weights live in 3 sites (mi_kula, mi_pariksha, mi_pramana): unify ALL to
    bg_class_priors or a stale copy wins (C6).**
14. **NEW — bo_laksana has two divergent salience formula sites: unify to one in v2 (C5).**
15. **NEW — judgment/classical constants must live in `bg_formula_constants`, never as Python literals.**
    Four fates: CLASSICAL (cite śāstra, encode exactly, never tune), NATIVE-JUDGMENT (ratify, version,
    L5-calibrate within bounds), ENGINEERING (document, keep in code), STRUCTURAL-CONFLATION (a BUG — fix
    outright, do not migrate). Any new judgment number ships to the registry, not inline.
16. **NEW — single source of truth for combustion (C12):** one combustion definition (L1 `bg_combustion_orbs`
    / `ga_condition`), per-graha. No writer may carry a second combustion orb.
17. **NEW — silent neutral defaults (S-C):** never let `.get(k, 0.5)` / `orb=1.0` / `bindus=4` flow into a
    product as if measured. Missing input → NULL component + `salience_inputs_complete=false`; imputation
    must be visible. Same class as the mi_pariksha catch-all deletion.
18. **NEW — stored vs query-time (S-E):** activation and domain-conditioned terms are applied at query time
    only; baking them into a stored column makes it stale on the next dasha/domain change.
19. **NEW — volume ≠ evidence (S-B):** aggregate scores (CDLM convergence, sangati concordance, sangam
    windows) must de-duplicate by family cluster and report `effective_evidence_count`; a raw population
    sum (the 11,970 artifact) is not independent evidence.

## §8 — PROGRAM-LEVEL ACCEPTANCE (unchanged north-star)

1. **Judgment:** a career question on 482012f1 surfaces the chart's defining structures, reconciled,
   cited, with contradictions weighed — zero mechanical atoms in the top band (W2/W3).
2. **Prophecy:** "Ketu dasha 2027" and "this activity in two months" return composed, falsifiable,
   base-rate-honest verdicts on prod (W4).
3. **Learning:** the instrument publishes which of its own technique families demonstrably work for this
   native, from a leakage-audited pipeline, and its served weights visibly follow (W5/W7).
4. **Integrity:** every claim machine-resolves to L1 facts + classical citations; every prediction carries
   a decidable falsifier; every weight change is versioned, bounded, and co-signed (all waves); every
   judgment constant lives in `bg_formula_constants`, not a code literal.
5. **Discovery (the doctrine, §0.1):** nothing is filtered — the tail stays served and queryable; the
   verdict object carries its own dissent + a `tail_divergence` memo; and the ranking is under permanent
   empirical test (tail-only retrodiction measures whether the instrument is missing something outside its
   own ranking — a test no acharya could run).

*End of BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN v2.1 (RECONCILED + supplement folded). First actions in
the implementation conversation: (a) schedule the W1 judgment sitting — Cowork prepares the DRAFT seeds:
3 core tables (class-priors, event ontology, activity ontology) + the constants-ratification sheet +
graha×domain and domain×varga affinity tables + the Doctrine (§0.1) for sign-off; (b) execute
`CLAUDECODE_BRIEF_BA_W0_SERVING_TRUTH_v1_0.md`.*
