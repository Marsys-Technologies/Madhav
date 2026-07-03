---
artifact: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN
canonical_id: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN
version: 1.0
status: CURRENT — the single execution-governing document for the Beyond-Acharya program
created: 2026-07-02
author: Cowork (strategic workstream, Claude Fable 5) — for native Abhisek Mohanty
consolidates:
  - BEYOND_ACHARYA_GAP_ANALYSIS_AND_ENRICHMENT_ROADMAP_v1_0.md (v1.3) — the WHY and WHAT
  - MIMAMSA_V2_LEARNING_LAYER_DESIGN_v1_0.md (v1.0) — the L5 redesign in full
supersedes_in_part: >
  The E-wave sequencing of the gap analysis v1.3 (§6/§9.4/§10) is RESEQUENCED here (§6): the
  retrodiction learning engine moves AFTER the R-pipeline build (it consumes promise/activation/anchor-v2;
  v1.3's E2.5 placement was optimistic). Where this document and the two parents disagree on sequencing or
  asset naming, THIS document wins.
how_to_use: >
  Paste this document (or its path) as the opening context of a new implementation conversation. It is
  self-contained: current-state anchors, the full asset delta (IDs, tables, scopes, dependencies,
  count_sql patterns), migration plan, Nirmāṇa/orchestrator embedding mechanics, wave-by-wave execution
  program with named CLAUDECODE briefs, acceptance gates, and the traps register. Implementation follows
  the standing split: Cowork authors briefs; Claude Code in Antigravity implements; every wave verifies
  against prod.
changelog:
  - v1.0 (2026-07-02): first consolidated master plan.
---

# BEYOND-ACHARYA — MASTER IMPLEMENTATION PLAN v1.0

## §0 — MISSION ANCHOR (one paragraph)

Elevate MARSYS-JIS from "richly built, correctly computed, poorly judged" to an instrument whose served
output — insight, interpretation, prophecy, guidance — exceeds what any individual acharya can derive,
while staying grounded, cited, falsifiable, and calibrated. The program embeds entirely into the existing
six layers (L0 Brahmagyan → L5 Mīmāṃsā), the FROZEN orchestrator, and the Nirmāṇa build tracker. No new
layers. New architecture is limited to: one subject type (chart-pair), two feedback arrows (L5→L0
graduation, L5→L2/L4 re-weighting), two services (transit application, waveform fine-grain).

## §1 — CURRENT-STATE ANCHORS (verified 2026-07-02)

- Canonical native chart `482012f1-710e-4a25-994a-93821f5871aa`; test chart Abhinandan `1c826d5a-…`;
  entitled family charts Arunima `acdf0d66-…`, Kiran `cb73cd3d-…`. (`362f9f17-…` is a dead phantom.)
- All six layers sealed/closed; ~81 assets; orchestrator FROZEN (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`).
- MCP channel: 45 tools, prod-hardened (M1–M8 sealed); audit-fix W1–W4 done on paper, BUT live probes
  2026-07-02 show W3 bounding NOT live (17.3 MB domain reading despite `max_lenses=1`), L4 anchors still
  schema-erroring (`column "id" does not exist`), kala sidecar down, panchanga_daily empty → E0 below.
- Salience v1 root cause verbatim in `bo_laksana.py::_compute_salience` — no signal-type/varga terms;
  signature_tier thresholds unreachable (max ≈ 2.33 < 3.0). DEFECT-001: 91.5% constituent_facts orphaned.
- L5 v1: 12 mi_* assets; scoring engine has stub falsifier (=1.0 always), no null models, no control
  windows, catch-all attribution; skeleton + journal loop + firewall are sound (keep per MIMAMSA_V2 §1).
- asset_registry mechanics: rows carry `(asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, scope, has_writer, target_floor, count_sql)`; cockpit stats read
  `count_sql` (chart-scoped `$1`), NOT asset_throughput. Migrations: `platform/migrations/` currently at
  365 — **verify next free number across BOTH migration dirs at brief time** (two-dir lexical-collision
  trap; never infer from one dir).

## §2 — THE NATIVE JUDGMENT SITTING (gates everything; schedule FIRST)

One sitting, three ratification tables + two sign-offs. Cowork prepares structured DRAFTS for correction
(never blank pages):

1. **Salience class-prior table** (→ `bg_class_priors` seed): weight per signal class/family — raja-yoga
   family vs dosha-major vs dignity-extreme vs karaka-alignment vs house-lord placement vs … vs per-varga
   atomic tallies; plus the varga-grain weight vector (D1 … D2700) and the composite-aggregation ruling.
2. **Event ontology** (→ `brahma_event_ontology` seed): ~20–30 event classes; per class: signature model
   (houses/lords/karakas/vargas/dasha rules/transit triggers), magnitude floor, adjacency (for PARTIAL
   adjudication), base-rate prior by age band, citations.
3. **Activity ontology** (→ `brahma_activity_ontology` seed): elective/undertaking classes → significators
   + fructification rules (largely the event classes seen from the elective side).
4. Sign-off: MIMAMSA_V2 §1 keep/replace verdicts, Loop-D resonance quarantine, REFUTED-requires-attestation.
5. Sign-off: this plan's wave sequencing (§6) and the E4 classical-completions ranking.

## §3 — FULL ASSET DELTA (the embedding: every ID, table, dependency)

Legend: **NEW** = new writer + migration + registry row + DAG edge · **EXT** = reopen existing writer
(seal-amendment pattern, as L1-E) · **FRM** = formula bump + rebuild (delete-then-insert regenerates) ·
scope `per_chart` unless noted. All writers conform to the FROZEN contract (§N.2): `@register`,
`run(ctx)`/`plan_substeps`, never commit `ctx.db_conn`, orchestrator owns build-state.

### L0 Brahmagyan (global scope; ON CONFLICT upsert idempotency)

| Asset | Action | Tables | Notes |
|---|---|---|---|
| `bg_class_priors` | **NEW** | `brahma_class_priors` | Salience class-prior + varga-weight vectors; native-ratified, versioned rows (`prior_version`); **one substance with mi_kula's family registry** — mi_kula v2 READS this table (no second weight source). L5 snapshots overlay it, never overwrite (two-key). |
| `bg_ghatana` | **NEW** | `brahma_event_ontology`, `brahma_activity_ontology` | Event + activity ontologies (§2 seeds); machine-decidable matching/adjacency rules jsonb; base-rate priors by age band. |
| `bg_transit_rules` | EXT | `bg_transit_rules` (+`bg_transit_av_gates`) | Ashtakavarga kakshya/SAV transit gates; vedha; double-transit (Jupiter+Saturn) rules; cited. |
| `bg_rules` | EXT | `sutravali_rules` | Nadi extraction pass (Bhrigu Nandi Nadi + Nadi Navamsa already in corpus); muhurta/tajika Phase-2 chunks. |

### L1 Gaṇita (per-chart; delete-then-insert per §N.3; reopens seal per amendment pattern — L1-E precedent)

| Asset | Action | New fact content |
|---|---|---|
| `ga_sensitive` | EXT | Bhava arudhas A1–A12 incl. Arudha Lagna + Upapada (fact_category `bhava_arudha`); Karakamsha + Swamsha derived facts. |
| `ga_dashas` | EXT | Classical Jaimini Chara dasha (sign periods, Rao-standard); [optional, native-ranked: Narayana]. |
| `ga_strength` | EXT | Per-varga Shadbala/bhava-bala (native ruling 2026-06-17; label computed-extension; floor NULL+reason where classical is D1-only — canonical-or-floor rule). |
| `ga_condition` | EXT | Graha yuddha (by longitude, cited method); lajjitadi + sayanadi avasthas (unfloor). |

L1 exit gates after extension build: FORENSIC 7/7 on 482012f1; chart-agnostic contamination check on
1c826d5a; new fact_categories visible in `chart_facts` under all 5 ayanamshas (or INVARIANT).

### L2 Bodha (per-chart; ONE regeneration absorbs everything below + DEFECT-001 MSR rebuild)

| Asset | Action | Detail |
|---|---|---|
| `bo_laksana` | **FRM v2.0** | `salience_v2 = class_prior(bg_class_priors) × varga_weight × specificity × v1 condition terms × dasha_activation_boost (L3 hook)`; hierarchical aggregation (atomic families roll into composite profile signals — atoms queryable, never top-band); signature_tier thresholds recut against the v2 distribution so `chart_defining` FIRES; cross-ayanamsha robustness columns filled (5-slice agreement). DEFECT-001: rebuild resolves constituent_facts against current L1 SHA. |
| `bo_bimba` / `bo_karanajala` | EXT | Project the L1 relational riches as typed edges: dispositor, argala/virodha, parivartana, yoga-membership, karaka-role, nakshatra-dispositor, KP-sub-lord chains; fill `valence`, `relationship_basis`, `affected_domains` on every edge; node strength from salience v2 (not the degenerate constant). Contradiction rows gain `domains_affected` + reconciliation record (evidence-weighted, citing both sides + activation state). |
| `bo_pratijna` | **NEW** | `bodha_pratijna` — Promise Register: chart × event_class (from `brahma_event_ontology`): promised/denied/conditional, grade, supporting + contradicting signal refs (salience-v2-ranked), varga confirmation state. The WHAT of prophecy; also a served insight product. |
| `bo_sangati` | EXT | `bodha_triangulation` — per question-class × tradition stack (Parashari/Jaimini/KP/Tajika): independent verdict inputs + concordance score. |
| `bo_samskara` | EXT (wave E6) | Whole-chart + per-domain configuration embeddings (pinned local model). |

Regeneration discipline: L2 rebuilds ONCE for E1 (all of the above in one pass), on ≥2 charts, with the
degenerate-distribution gate (no scoring column may collapse to constants) + trap-1 authority check.

### L3 Kāla

| Asset | Action | Detail |
|---|---|---|
| `ka_yojaka` | EXT | Fill signals' dasha_activation columns across ALL 7 dasha systems (closes U1 with purpose); promise-linked activation predicates: for each `bodha_pratijna` row, periods whose lords connect to the promise (multi-system cross-confirmation count as first-class score). |
| `ka_avadhi` | **NEW** | `kala_avadhi` — Period Dossiers: per MD/AD × chart: lord natal-dossier refs (sign/nakshatra/dispositor/D9/karaka roles), activated promise refs, sub-lord modulation, quality components + citations. Powers query-class Q1 ("how will my Ketu dasha be"). |
| `ka_taranga` | **NEW** | `kala_taranga` — Activation Waveform: coarse (monthly) per-domain/per-event-class activation curves 1950–2100 from dasha×transit×promise convolution; fine resolution = **service** (never stored day-grain). L4 anchors become its gated local maxima. |
| transit service | EXT | AV kakshya/SAV gates + double-transit checks as on-demand computation (service-not-storage ruling). |

### L4 Phala

| Asset | Action | Detail |
|---|---|---|
| `ph_nimitta` | **REBUILD v2** | Anchor v2 = `(event_class, window, magnitude, posterior)`; `posterior = base_rate(event_class, age_band, window) × promise_lift × activation_lift × trigger_lift`; lift_vector frozen per anchor (analytic attribution substrate); structured falsifier `{event_class, magnitude_floor, window, attestation_required}`; G-LADDER retired (ayanamsha-robustness survives as a lift modifier); full probability range allowed (incl. "unlikely/denied"). |
| `ph_muhurta` | EXT | Activity-aware election: `brahma_activity_ontology` significators × panchanga × tarabala/chandrabala vs the native's own chart; fructification follow-up hooks (Loop B). |
| prashna path | **NEW (chart-type)** | `charts.chart_type='prashna'` build path: cast at question time, minimal asset set (ga_positions/ga_panchanga/prashna judgment); consumes existing L0 prashna rules. Precedent: chart-type, not layer. |

### L5 Mīmāṃsā (implements MIMAMSA_V2 in full; per-asset verdicts from its §1)

| Asset | Action | Detail |
|---|---|---|
| `mi_kula` | v2 | Reads `bg_class_priors` (unification — deletes its embedded weight catalog); neg-control battery retained. |
| `mi_jivanaghatana` | EXT | + period attestation flags (REFUTED requires attested-complete periods). |
| `mi_pramana` | **ENGINE v2** | Adjudication per MIMAMSA_V2 §4 (CONFIRMED/PARTIAL/REFUTED/EXPIRED + FALSE_ALARM on controls; ontology adjacency replaces binary domain; structured falsifiers replace stub); scoring per §5 (Brier vs climatology null; sharpness via null; rank-aware retrodiction credit; ECE retained). |
| `mi_pariksha` | **v2 substeps** | `retrodiction_generate` (blind, date-filtered connection views — the ph_pramana firewall generalized) · `control_windows` (≥3 per event, stratified) · `ablation` (per technique family masked reruns) · `attribution` (analytic from lift_vectors; catch-all fallback DELETED) · `neg_control` + `discovery` retained. |
| `mi_gunanaka` | v2 | Hierarchical shrinkage replaces n≥10 gates (cell→parent pooling; at n=0 posterior = classical prior); 3× divergence cap RETAINED; produces versioned calibration snapshots. |
| `mi_adhilepa` | WIRE | Snapshot publication two-key (system proposes, native co-signs); overlays to 3 sinks only: `bg_class_priors` overlay, R-4 lift calibrations, triangulation tradition-weights. Never L1. |
| `mi_seva`/`mi_abhilekha` | WIRE | Daily closed-window scan → ask-cards; journal resync; Loop-B prashna follow-ups; Loop-D resonance stored QUARANTINED (moves S4 presentation only). |
| `mi_sambandha` | KEEP+ | Manifestation grammar live from adjudicated outcomes (Dirichlet smoothing on v1 priors). |

### SY — chart-pair subject type (wave E6)

`charts.chart_type='synastry'` (two member chart_ids) + minimal `sy_koota` (ashtakoota + dosha-koota),
`sy_graph` (inter-chart aspects/overlays), `sy_timing` (dasha overlap) — onboarded through the frozen
contract exactly like a layer; family-lattice cross-chart event consistency checks feed L5 as labeled
consistency evidence.

## §4 — NIRMĀṆA / ORCHESTRATOR EMBEDDING MECHANICS (how the data gets built)

1. **Per NEW asset:** one surgical migration = `CREATE TABLE` + `asset_registry` INSERT (correct layer,
   sort_order within layer, sanskrit/english names, `scope='per_chart'` or `'global'`, `has_writer=true`,
   chart-scoped `count_sql` using `$1` — the cockpit-truth rule; `target_floor` set to achieved count
   post-build, never pre-fabricated) + DAG `depends_on` edges. Then the `@register('<asset_id>')` writer.
   The orchestrator is NEVER modified; if a writer seems to need a contract change → STOP, raise to native.
2. **Per EXT asset:** reopen via the seal-amendment pattern (as L1-E): amendment note in the layer's seal
   record, writer extension, migration only if new tables/columns, rebuild REPLACES per §N.3.
3. **Per FRM asset:** bump `*_formula_version`, document in the asset header, rebuild regenerates.
4. **DAG additions (dependency order the cockpit will drive):**
   `bg_class_priors, bg_ghatana` (roots) → L1 EXTs → `bo_laksana v2` → `bo_bimba/karanajala, bo_pratijna,
   bo_sangati` → `ka_yojaka EXT` → `ka_avadhi, ka_taranga` → `ph_nimitta v2, ph_muhurta` →
   `mi_jivanaghatana → mi_bhavisya → mi_pramana → mi_pariksha → mi_gunanaka → mi_adhilepa`.
5. **Build/regeneration sequence per chart (one cockpit "Rebuild" cascade):** L0 seeds (global, once) →
   L1 (with FORENSIC + contamination gates) → L2 single regeneration (degenerate-distribution gate) →
   L3 → L4 → L5. Two-chart rule: every wave verifies on 482012f1 AND 1c826d5a before claiming done.
6. **Services** (transit application, waveform fine-grain, prashna casting) live in the Python sidecar /
   retrieval layer — registered as service-handler assets (mi_seva precedent: writer verifies readiness,
   creates no build rows).

## §5 — NON-ASSET WORKSTREAMS

- **Retrieval fork:** the VERDICT OBJECT (top-k reconciled findings: claim, evidence, contradiction
  resolution, tradition concordance, activation state, ayanamsha robustness, confidence, falsifier,
  citations — LLM narrates ON TOP, never instead); period-reading composition (Q1) over `ka_avadhi`;
  undertaking composition (Q4); activation-aware + calibration-aware ranking; `query_calibration` v2
  (per-cell skill/n/CI/snapshot). Registry capabilities only — retrieval remains the single query brain.
- **MCP channel:** tool updates to serve the above; query-class taxonomy (gap analysis §10.2) becomes the
  living readiness matrix — a query class is GREEN only when every stage of its recipe serves on prod.
- **Portal:** ask-cards (closed-window adjudication), period-attestation card, structured LEL intake form
  (event_class + magnitude per ontology), prashna follow-up scheduler, calibration-snapshot co-sign UI.
- **Ops (E0):** deploy-truth pass — Cloud Run revision SHA vs W2–W4 merge SHAs (`gcloud run services
  describe`), W3 bounding live-verify, L4 schema errors, kala sidecar up, panchanga_daily populated.

## §6 — EXECUTION PROGRAM (implementation waves → named CLAUDECODE briefs)

> Standing mechanics per wave: Cowork authors the brief → `CLAUDECODE_BRIEF.md` at project root
> (governing scope: `may_touch`/`must_not_touch`, acceptance criteria each tagged
> `[verify-against: prod|db|ci]`) → Claude Code in Antigravity implements on the wave's own branch →
> prod gate re-checks headline numbers on live prod before the wave claims done (the V1.3 scar).

| Wave | Content | Briefs | Gate to next |
|---|---|---|---|
| **W0 = E0** | Serving truth (ops §5) | `BA_W0_SERVING_TRUTH` | All 45 tools structured-respond on prod; bounding demonstrably live; kala/L4/panchanga serving. |
| **W1 = judgment sitting** | §2 sitting → ratified seeds | (Cowork-led, no CC brief; produces 3 seed datasets) | Three tables ratified + sign-offs recorded. |
| **W2 = E1** | `bg_class_priors` + `bg_ghatana` + L1 EXTs + L2 single regeneration (salience v2, edges, contradictions, pratijna, triangulation, DEFECT-001) | `BA_W2A_L0_SEEDS_AND_L1_EXT`, `BA_W2B_L2_REGENERATION` | G10-style check: career top-10 on 482012f1 = 10th-lord/karaka/yoga structures, zero sub-varga atoms; constituent_facts 100% resolve; signature_tier fires; two-chart + degeneracy gates pass. |
| **W3 = E2** | Verdict object + serving (retrieval/MCP): triangulation, ayanamsha ensemble, activation-aware ranking | `BA_W3_VERDICT_AND_SERVING` | An external LLM over MCP produces a cited, reconciled career reading judged acharya-grade (rubric eval ≥ WS-3 bar). |
| **W4 = E3** | R-pipeline: `ka_yojaka` EXT + `ka_avadhi` + `ka_taranga` + `ph_nimitta v2` + `ph_muhurta` EXT + prashna path | `BA_W4A_KALA_ACTIVATION`, `BA_W4B_PHALA_V2` | Q1 + Q3 + Q4 recipes GREEN on prod; anchors span full probability range with LEL-decidable falsifiers; posteriors carry lift_vectors. |
| **W5 = learning live** | MIMAMSA_V2 Phases R1+R2 (retrodiction, controls, ablation, scoring v2, shrinkage, first snapshot) | `BA_W5_MIMAMSA_V2_ENGINE` | First honest skill table on 482012f1 (45 train/12 held-out); ≥1 family beats null OR the null finding published; snapshot changes served weights reversibly under two-key. |
| **W6 = E4** | Classical completions build-out already scaffolded in W2 L1 EXTs — remainder per native ranking (Nadi rules, AV-transit L0, avasthas) | `BA_W6_CLASSICAL_COMPLETIONS` | New fact_categories flow through bo_laksana v2 ranked (not as noise). |
| **W7 = portal loops** | MIMAMSA_V2 Phase R3 (ask-cards, attestation, prashna follow-ups, co-sign UI) | `BA_W7_PORTAL_LEARNING_LOOPS` | Closed windows convert to adjudicated outcomes ≥80% in 7 days. |
| **W8 = E5/E6** | Research organs: synastry `sy_*`, chart embeddings + case retrieval, motif mining, rule-induction w/ L5→L0 graduation | `BA_W8_RESEARCH_ORGANS` (split at brief time) | Gated on multi-chart corpus growth; each organ consumes W5's calibration corpus. |

Parallelizable: W4A/W4B after W2; W6 alongside W4; W7 alongside W6. Strictly serial: W0→W1→W2, W4→W5.

## §7 — TRAPS REGISTER (inherited scars this program must not repeat)

1. Verify against PROD, not worktree — every AC tagged; wave-complete prod gate mandatory.
2. Two-dir migration numbering — scan both dirs for the next free number at brief time.
3. Surgical migrations only; never deploy.yml-auto/bulk migrate.
4. count_sql is cockpit truth — every new asset ships a correct chart-scoped `count_sql`.
5. Degenerate-distribution gate on EVERY new scoring column (salience v2, posteriors, skill cells) —
   halt if a column collapses to constants (the 2.326672 / 0.28 scars).
6. L1-authority (trap-1): L2+ references fact_ids, never restates computed values as its own.
7. Chart-agnostic: no native leakage into non-native charts; contamination check post-rebuild.
8. Canonical-or-floor: cited values or NULL+reason; formula weights are native judgments (halt for
   sign-off, never re-pick).
9. Anthropic API banned in build/narration paths (Gemini/DeepSeek per model policy); scoring paths are
   LLM-free entirely (D-1).
10. Destructive ops need reverse-citation gates; brief schema promises audited against migration files.
11. Retrieval layer stays FROZEN except through its own fork's contract; MCP consumes the registry.

## §8 — PROGRAM-LEVEL ACCEPTANCE (the north-star test, restated operationally)

1. **Judgment:** a career question on 482012f1 surfaces the chart's defining structures, reconciled,
   cited, with contradictions weighed — zero mechanical atoms in the top band (W2/W3).
2. **Prophecy:** "Ketu dasha 2027" and "this activity in two months" return composed, falsifiable,
   base-rate-honest verdicts on prod (W4).
3. **Learning:** the instrument publishes which of its own technique families demonstrably work for this
   native, from a leakage-audited pipeline, and its served weights visibly follow (W5/W7).
4. **Integrity:** every claim machine-resolves to L1 facts and classical citations; every prediction
   carries a decidable falsifier; every weight change is versioned, bounded, and co-signed (all waves).

*End of BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN v1.0. Open a new implementation conversation with this
document; first actions there: (a) schedule the W1 judgment sitting; (b) author `BA_W0_SERVING_TRUTH`.*
