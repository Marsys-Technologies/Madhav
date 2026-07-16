---
artifact: BIND_D-2
type: BINDER PASS RECORD (CONDUCTOR_PROTOCOL §1 Binder / §2 step 1 OPEN)
wave: D-2 — Vidhi Engine + Mechanism
bound_date: 2026-07-16 (~21:00 IST; probes executed 15:41–15:45 UTC)
binder: Claude Fable 5
brief_version_bound: 2.2 (BRIEF_D2.md)
brief_status_recommendation: BOUND (all 10 §B slots resolved; 1 pre-V-3 conductor action; 0 blocking regressions)
probe_channel: >
  marsys-jis-direct MCP tools (the ?api_key face of the deployed amjis-mcp Cloud Run service —
  §8.1 ruling: same service, valid gate channel) + postgres MCP (read-only SELECTs) + gcloud
  describe + git/ls. All batches ≤13 calls; no 429s encountered.
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek), ayanamsha lahiri_chitrapaksha
---

# BIND_D-2 — Binder findings

## §B0 spot-verify (PRE-BOUND slots)

- **B0.1 known_gap reconciliation:** accepted as pre-bound per brief instruction; spot-checks run:
  CR-28 row confirmed at `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` line 84, status OPEN
  ("returns a classifier PROMPT… needs RATIFY-or-redesign"). CR-16 confirmed OPEN by live schema
  (`query_special_lagnas` takes `datetime_iso/latitude_deg/longitude_deg` only — no `chart_id`).
  **CR-9 ANOMALY:** `asset_registry_all` returned a full 200 payload (97 assets, 59.4KB) on the
  marsys-jis-direct face this session — the "still 401" claim did NOT reproduce on this face.
  Either the MCP server reaches the registry without the proxy allowlist path, or the 401 is
  Bearer-face/route-specific. V-3 must re-verify the CR-9 root cause live before "fixing" it;
  the fix may be moot or face-specific. Not a blocker.
- **B0.2 Track-3:** confirmed still ABSENT (`ls track3/` → No such file or directory). V-1/V-3 absorb.
- **B0.5 harness 429-retry:** not re-verified in code (pre-bound); no 429s hit during this pass's
  paced batches, consistent with the ≤17-call discipline working.
- **B0.6 rebuild transport:** standing fact accepted, no probe.

## §B.1 — Rollback pin + prior-battery regression check

**Rollback pin (record in STATE_D-2.md at OPEN):**
- amjis-web image: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:b623033e1f00e6ace96e4be2722506f30b057031`
- amjis-mcp image: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:0824566951a3189bc750e24d20eab650f5542fb4`
- brahma-build-pipeline-job image: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:dfa4e8705aaa2243c3a24ba7eca26f55350cda8c`
- Abhisek build state: latest completed `build_runs` row = `8a353d5d-032f-4c49-b0e1-66e3eed8d381`
  (asset_set, completed 2026-07-16T13:01Z — D-1.6 rebuild 2); ga_vichara rows carry build_id
  `83949839-fff3-472f-bbb1-cbf6c3b1bb8a` (D-1.6 rebuild 1). One failed run `71b260c7` (12:50Z)
  sits between them — the documented state-race incident, recovered; no action.
- Note: amjis-web (b623033e) and amjis-mcp (08245669) are at DIFFERENT SHAs — expected
  (deploy.yml path-scoping; REPORT_D-1.5b flag). Record as-is.

**Regression sample (representative subset of Gate-A/B/Ś, 12 checks, run live on the deployed connector):**

| # | Check (gate) | Result |
|---|---|---|
| 1 | FORENSIC 7/7 via `ganita_natal_positions_compute` (Sun Cp 21.96° · Moon P.Bhadrapada Aq · Lagna Aries 12.42° · Shukla Tritiya · Ravivara · Shiva · Garaja) | **PASS 7/7** (also proves sidecar live — PyJHora engine responded) |
| 2 | Dosha verdict honesty (Ś#4): `ganita_structural_get(dosha_fires, v3)` — Kāla-Sarpa natal `not_formed`, agreement receipt `agrees:true`, B9 gate excluding 22 catalog-stub rows, per-varga map served | **PASS** |
| 3 | Yoga firings (Ś#5): 12 fired, Sasa 1.566 / Budha-Aditya / Sarasvati / 2× Dhana / Raja-KT grounded, constituent_fact_ids present, fired=true default | **PASS** |
| 4 | v3 verdict honesty (Ś#7): Sasa served as fired/formed with honest `bhanga_na_reason` (B.10 no-fabrication) | **PASS** |
| 5 | Window families (Ś#9): `kala_windows_get` → real dated windows (2024-12-08→2027-08-18, peak 2026-04-13), dasha_activation_proximity 0.8778 (not flat 0.5), predicates with eligibility rules | **PASS** |
| 6 | Muhurta citations (T-8): `kala_muhurta_get(business)` → 3 windows, real chart_dashas/panchanga_daily/BPHS ch.46 citations, `b3_citation_compliant:true` | **PASS** |
| 7 | Aspects facet routing (A7/R-17): `ganita_structural_get(aspects)` → categories = aspect_parashari_given/received/per_varga/matrix_summary (Parashari-only; jaimini split out) | **PASS** |
| 8 | ga_vichara serving (Gate B): 1,477 rows / 5 families (valence_pass 1421, ratification 9, divergence 3, consistency 9, leverage_index 35), layered verdict envelope | **PASS** |
| 9 | Digest (CR-55/D-5): weakest_graha=Venus w/ BPHS Ch.27 source, attribution 0/300 unattributed, composite_4d ranking basis | **PASS** |
| 10 | Signals surface (Gate B): `bodha_signals_get(sudarshana_agreement)` → 9 rows, DEFECT-001 0% orphans, tier distribution non-degenerate (84.8/12.3/2.3/0.6) | **PASS** |
| 11 | judgment_query wealth (v3): verdict `convergent_moderate` 2.38, receipt {bhava✓ bhavesha✓ karaka✓ from_moon✓ D2✓ yogas_checked:12 bhanga✓ timing_anchored:true}, honest judgment_flags | **PASS** (size observation below) |
| 12 | Infra (Ś#13): list_assets (97 assets), phala_anchors (4 anchors, falsifiers present), mimamsa_calibration (multipliers + 141 QA checks, 0 fail), positions (CR-50 grahas-only default) | **PASS** |

**Expected residuals — both confirmed present, both expected, non-blocking:**
- Gate Ś #8: `yoga_activation_by_dasha` → 5/5 rows `undated_activation_count=5`, activation dates
  null, dasha_alignment flat 0.5, sources panchanga/catalog `yoga_label` (incl. `fire_reason=requires_pass`).
  Exactly the documented residual. Disposition at §B.8.
- PARK-#4: keyword-heuristic valence rows still present (see §B.2/§B.4 scoping finding).

**Unexpected reds: NONE.** No regression incident; lanes may spawn.

**Two non-red observations (route to V-0 baseline + V-3's budget lens, non-blocking):**
- `judgment_query(wealth, v3, max_signals=5)` response = ~69KB (>64KB Gate-Ś ceiling); the tool
  itself flags `response_still_over_12kb_budget_after_full_trim`. No recorded per-tool baseline
  exists for it, so this is a baseline fact, not a proven regression.
- `ref_dasha_systems_get(keyword=narayana)` = ~76KB. Same treatment.

## §B.2 — V-5 salience constants + class priors

**Live class distribution on 482012f1 (bodha_msr_signals, post-D-1.6 estate):** 14 classes;
none of V-5's four target classes exist yet (correct — they're the deliverable). Calibration context:

| class | n | min/avg/max salience | tiers |
|---|---|---|---|
| composite_state | 37,144 | 0.215/0.686/2.716 | (bulk fabric) |
| karaka_alignment | 5,960 | 0.294/0.620/1.891 | mostly supporting |
| bhavat_bhavam_amplifier (DR-3 0.85) | 60 | 1.323/1.525/2.042 | 43 chart_defining / 17 major |
| sudarshana_agreement (DR-3 1.15) | 45 | 0.311/0.398/0.476 | all supporting |
| varga_ratification_divergence | 12 | 1.200 flat | all major |
| yoga | 74 | 0.483/0.674/2.521 | 70 supporting / 3 major / 1 chart_defining |
| dosha | 89 | 0.550/0.656/0.661 | all supporting |

**PROPOSED DR-n (Fable as Binder; conductor to allocate the DR number and record in
DISAGREEMENT_REGISTER per §8.8(ii) — NOT silently bound):** class priors for V-5's four new classes,
DR-3-precedent style (multiplier on the class's computed salience, tier assignment per emitter logic):
- `nakshatra_semantic` = **1.00** — high-volume corroborative fabric (own-star, dispositor chains,
  tara bala); neutral prior so it enriches without flooding; end-degree/gandanta-adjacent flags may
  earn per-signal boosts, not a class-wide one.
- `arudha` = **1.10** — Jaimini perception layer; AL-conjunction and AL–bhāva relations are
  reading-bearing (CR-61's whole point is they never surface today); modest boost above fabric.
- `special_lagna` = **0.90** — Indu/Sree/Ghati/Hora are domain-scoped corroborators (wealth via
  Indu, etc.); below-neutral chart-wide, with the emitter carrying domain_salience so they rank
  INSIDE their domain (mirrors how DR-3 kept sudarshana at supporting tier).
- `vargottama_amplification` = **1.15** — cross-frame confirmation class, structurally analogous
  to sudarshana_agreement's 1.15 (same "two independent frames agree" epistemics).
- `dhana_axis` (if emitted as its own class rather than folded into vargottama's lane) = **1.05** —
  domain-load-bearing but overlapping existing dhana yoga rows; slight boost, dedup discipline
  against `yoga` class required.
Rationale: keeps the DR-3 band (0.85–1.15); nothing new outranks the amplifier/divergence classes
that already carry the chart-defining layer; per-domain relevance is carried by domain fields, not
by inflating class priors.

## §B.3 — Orchestrator state-commit race (spot-verify only)

Commit `b13640d1` **confirmed on main**: "fix(orchestrator): pre-D-2 — D-1.6 asset_throughput
state-write defect (no-op completion misclassified as dormant)". D-2 verifies only, never patches
(§F2). The four non-blocking verifier findings carried forward verbatim as Binder agenda:
- **F1** monitor `asset.noop_completion` events from non-resumable writers (a §N.3 delete-then-
  insert violation could be probed 'lit' over stale rows — loud, but worth alerting);
- **F2** `bo_laksana.count_sql` is over-broad (counts bo_sudarshana's rows in shared
  bodha_msr_signals — same class as PR #574's delete-scope bug, count-side; currently unreachable
  but tighten via a surgical migration when V-4 touches bo_laksana anyway) — **assigned to V-4**
  (ledger row 40);
- **F3** the probe abstains (fail-safe) on ~11 multi-`$1` and 4 literal-`%` count_sqls — fine
  today, but if resumption spreads to those assets the protection won't follow;
- **F4** the 0-row-recovery upsert drops `built_against_*`/`rows_written` (rare path, could
  confuse staleness detection).
Forced same-day ka_sangam recompute semantics remain resume-by-design (writer-level, deferred).

## §B.4 — V-4 edge-strength formula terms

**Shipped valence-pass shape (live probe, `ganita_vichara_get`):** 5 families on chart —
`valence_pass` (1,421 rows; functional-lordship valence classes e.g. strong_malefic),
`varga_ratification` (9; ratification_factor ∈ [0.6,1.4] per domain×subject),
`varga_ratification_divergence` (3 subjects / 12 signals; flat salience 1.2, major),
`varga_consistency` (9; continuous 0..1), `leverage_index` (35; value_jsonb terms observed live:
`capability`, `dignity_score`, `shadbala_percentile`, `dasha_runway_weight`,
`domain_load_bearing_weight[_normalized]`, `ratification_factor_rescaled`, `years_to_start`,
`md_duration_years`). Every row carries `constituent_fact_ids` + `formula_version` (§N.5 conformant).

**PROPOSED DR-n (Fable as Binder; conductor records — NOT silently bound):** mechanism edge strength:
`edge_strength = base_relation_weight × valence_factor × ratification_factor × consistency_weight`, where
- `base_relation_weight` = the CGM edge-type weight already on bodha_cgm edges (dispositor/aspect/
  exchange/lordship), retiring the CR-86 hardcoded literals;
- `valence_factor` from the subject's `valence_pass` row: strong_benefic/strong_malefic 1.25,
  benefic/malefic 1.10, neutral 1.00 (magnitude; sign/direction carried as edge valence, never
  folded into magnitude — a strong malefic mechanism is STRONG);
- `ratification_factor` = the domain-scoped ga_vichara value [0.6,1.4] when the edge is
  domain-tagged, else 1.0;
- `consistency_weight` = 0.75 + 0.25 × varga_consistency (so a fully vargottama-consistent subject
  amplifies 1.0×, a fully inconsistent one dampens to 0.75×);
- clamp [0.1, 2.0]; `formula_version='edge_strength_v1'`; every edge carries constituent
  ga_vichara row ids (§N.5).
Rationale: uses only terms the valence pass ACTUALLY emits (probe-verified), keeps L1 authority
(V-4 references ga_vichara values, never restates), and the [0.6,1.4]×[0.75,1.0]×[1.0,1.25]
ranges compose to a bounded, non-degenerate distribution.

## §B.5 — Fresh census baseline

- **Tool count: 135** tools visible on the deployed connector's client tool list this session
  (the ?api_key face). This supersedes the "~126" planning figure; V-0's full sweep sizes to 135
  and V-3's canonical-face list is authored against these 135 names.
- No direct `tools/list` meta-tool exists on the connector; count taken from the client-visible
  registration list (the same list a consuming LLM sees), which is the right census universe.
- **Sampled sweep (18 tools across ganita/bodha/kala/phala/mimamsa/ref/util namespaces):**
  - **PASS (15):** ganita_natal_positions_compute, ganita_structural_get (dosha_fires v3 + aspects),
    ganita_yoga_firings_get, ganita_vichara_get, ganita_positions_get, bodha_signals_get,
    bodha_chart_digest_get, kala_windows_get, kala_muhurta_get, yoga_activation_by_dasha,
    phala_anchors_get, mimamsa_calibration_get, list_assets, asset_registry_all, intent_classify
    (works-as-built prompt contract, pending CR-28 ruling).
  - **PASS-EMPTY-HONEST (1):** ref_yogas_get(domain=wealth) → 0 rows WITH explicit `empty_reason`
    disclosing the stored domain vocabulary (raja/dhana/aristha/pancha_mahapurusha/sannyasa/other) —
    honest, but a vocabulary-mismatch trap V-3's errors-that-teach class should cover.
  - **DEGRADED-OVERSIZE (2):** judgment_query(wealth,v3) ~69KB; ref_dasha_systems_get ~76KB
    (both >64KB; both structurally correct payloads).
  - **FAIL (0).**
- Extrapolated baseline note for the gate's "census ≥ baseline" clause: estate is healthy; the
  full-135 V-0 sweep at cycle-1 close is expected to record ≥131 PASS with a small
  DEGRADED-OVERSIZE set — V-0 must record per-tool byte sizes so the oversize set becomes a real
  baseline instead of anecdote.
- **V-3 canonical-face input:** the alias pairs visible in the 135 (legacy get_*/query_* vs
  namespaced *_get twins, e.g. get_signals/bodha_signals_get, query_calibration/
  mimamsa_calibration_get, muhurta_finder/kala_muhurta_get, compute_natal_positions/
  ganita_natal_positions_compute, intent_classify/util_intent_classify) are the dedup universe;
  ~30 canonical faces is consistent with what the 135 collapse to.

## §B.6 — Migration number allocation

`platform/migrations/` HEAD = **439** (`439_ga_vargas_target_floor_rebaseline.sql`). Disjoint blocks:
- **V-1: 440–444** (`44N_vidhi_*.sql`)
- **V-4: 445–449** (mechanism table, bo_anveshana disposition, bo_laksana count_sql F2 fix)
- **V-5: 450–454** (signal-class registry appends, class priors)
- **V-6: 455–459** (upapada/maitrī rules, dasha wiring, dosha cancellation)
Single directory `platform/migrations/` only; each migration needs a guard receipt pre-apply.

## §B.7 — CR-28 engineering ruling (REQUIRED PRE-V-3 CONDUCTOR ACTION)

Register row (line 84, §A): "intent_classify / util_intent_classify return a classifier PROMPT for
the consuming LLM rather than a classification — works-as-built; needs RATIFY-or-redesign decision
(is prompt-delegation the intended P-10 contract?)". Live probe confirms the shape: the tool returns
`{prompt: "...You are a Jyotish query classifier...", usage: "Pass prompt to an LLM..."}` — no
classification. **The exact question for the Opus engineering adjudicator:**

> For the scope-tuple classifier V-3 must wire (question → intent/domains/width/depth/horizon/
> intervention/entitlement), is prompt-delegation RATIFIED as the P-10 contract (the tool returns a
> rendered prompt; the CONSUMING LLM classifies — zero server-side model dependence, but every
> caller must run its own inference and the server can never echo the tuple for correction
> server-side), or must intent_classify be REDESIGNED to return a classification (server-side or
> deterministic-rule classification — self-contained contract, enables the V-2 tuple-echo receipt,
> but adds latency/model-coupling or a rules-maintenance burden)? Note the V-2 dependency: "scope
> tuple echoed for correction before execution" is materially easier if the server produces the
> tuple. Binder recommendation to the adjudicator: hybrid — deterministic rule-based tuple
> classification server-side with the rendered prompt retained as a disclosed fallback field —
> but the ruling is Opus's to make, not this Binder's (wrong role class per §4.1).

The conductor dispatches this adjudication BEFORE V-3 wires intent_classify. V-3's other items
(scan/fetch, capability map, dedup, CR-44) are NOT gated on it.

## §B.8 — Gate Ś #8 pickup disposition

**Recommendation: V-5 ABSORBS it in cycle 1 (bounded), with an explicit fallback.** Reasoning:
(a) live probe confirms the residual is exactly as documented — every yoga-class activation row is
undated with flat 0.5 alignment, sourced from birth-moment/catalog rows lacking a natal
constituent_lord; (b) the fix lives in the yoga-signal-class's `dasha_eligibility_rule`
construction, which is precisely the signal-class-registry surface V-5 is already rebuilding for
four new classes — the marginal cost of also defining eligibility for the existing yoga class while
in that file/table is low, and doing it in the same wave avoids a THIRD wave touching the class
registry; (c) the firings-authoritative surface is unaffected either way, so the risk is bounded.
Fallback: if V-5 hits its lane ceiling, the item PARKs back to MARSYS_DEFECT_GAP_REGISTER_v2_0.md
as tracked non-blocking — the gate must list it as explicitly-excluded in that case (ledger row 45
carries both branches).

## §B.9 — Build-health row-count baseline (supersedes L1_GANITA_CLOSURE for ±1% checks)

Live counts for 482012f1 (postgres, 2026-07-16 ~15:42 UTC):
- **chart_facts = 138,279** — confirms the D-1.6 baseline exactly.
- **chart_dashas = 483,060** — NOTE: differs from the L1-closure canonical 536,471 (−10%).
  REPORT_D-1.6 investigated only the chart_facts delta; no wave report records a dasha re-count.
  Recorded as the new baseline per this slot's instruction; conductor should sanity-confirm at
  first rebuild that the count is stable (idempotent delete-then-insert means a stable 483,060 is
  simply the current writer's true output; a MOVING count would be the defect signal).
- **chart_divisionals = 22,092** (was 21,635; +2.1%, consistent with D-1.5b/D-1.6 varga additions).
- **bodha_msr_signals = 49,360** (14 signal classes; distribution in §B.2).
Expected deltas from this wave: +4–5 new signal_type_classes (V-5) with four-digit row growth in
bodha_msr_signals; new mechanism/vidhi tables (not in this baseline); possible chart_facts growth
from V-6 upapada/maitrī/functional-class facts — the wave's own health check compares against THESE
numbers plus lane-declared deltas.

## §B.10 — Rebuild scope ruling (cycle 1; EXPECTED scope — exact closure computed at rebuild time)

`{scope: asset_set, layers: [L0-vidhi-rules, L1-subset, L2, minimal L3-ingest], full: false}`

**Rationale:** none of the three §8.2 full-rebuild triggers requires full L1→L5 — but note V-4's
edge-strength change touches the CGM substrate that ka_yojaka reads (CR-85), so the L3 ingest edge
(`ka_yojaka` and, per the D-1.6 precedent, its sibling closure) must be IN the set; that is still
an asset_set, not a layer sweep.

**Expected changed writers (from §F1):** V-1 `bg_vidhi*` (new); V-4 `bo_karanajala`, `bo_cgm_*`
(motifs/paths/metrics), `bo_yantra*` (new mechanism writer), `bo_laksana` (re-rank pass, EXCLUSIVE),
`bo_anveshana` (retirement), `ka_yojaka` (CR-85 stub-removal only); V-5 four new `bo_*` emitter
modules; V-6 `ga_structural` (EXCLUSIVE), `ga_sensitive`, Nārāyaṇa/Chara dasha modules, L0 corpus
rule files.

**Live depends_on edges confirming the cascade shape (asset_registry, probed):**
`bo_laksana ← {bg_rules, ga_positions, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati,
ga_structural, ga_nakshatra, ga_condition, ga_vargas, ga_vichara}`; `bo_bimba ← bo_laksana`;
`bo_karanajala ← {bo_laksana, bo_bimba, ga_positions}`; `bo_cgm_motifs/paths ← {bo_bimba,
bo_karanajala}`; `bo_anveshana ← {bo_sangati, bo_karanajala, bo_samskara, bo_drishti, bo_bimba,
bo_laksana}`; `ka_yojaka ← {bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati,
bo_pratijna, bg_ghatana}`. V-6's ga_structural/ga_sensitive edits pull the L1-subset cascade
through bo_laksana (as the brief expects). **The EXACT asset_set is computed post-cycle-1-merge
from `asset_registry.depends_on` over the actually-changed writer set** (the D-1.6 precedent: a
too-narrow set DEP-ASSERTs; expand to asserted dependents only, never to a layer). D-1.6's
comparable closure was 47 assets; expect the same order of magnitude. Abhisek only; Abhinandan
never rebuilt.

## §F1.7 — Promise ledger (promise → assertion; the wave closes against THIS table)

Legend: [H] = executable harness assertion V-0 implements; [S] = structurally-verified-by-construction
with the stated evidence recipe. Every row must be GREEN-on-deployed-connector or native-visible-PARKed at close.

| # | Lane | Promise | Verification |
|---|---|---|---|
| 1 | V-0 | 6 §G.0 wealth conclusions as executable presence checks | [H] harness emits 6 named assertions; each conclusion traceable to a served top-15 signal/verdict on its domain surface |
| 2 | V-0 | Full census sweep (135 tools, §B.5 count) with PASS/DEGRADED/EMPTY/FAIL vs this bind's baseline | [H] census run output diffs against §B.5 table; 0 regressions; per-tool byte sizes recorded (creates the oversize baseline §B.1 lacks) |
| 3 | V-0 | Completeness-receipt validator | [H] validator passes on V-2's live wealth AND career readings; every `dark` item cites an OPEN/LOGGED CR row |
| 4 | V-0 | Alias-count check vs V-3's canonical-face list | [H] deployed tools/list count reconciles with canonical list + declared deprecations; no orphan twins |
| 5 | V-0 | Proactive pacing: ≤17-call batches, inter-batch throttle, per-batch checkpoint/resume, TRANSPORT-vs-TOOL separation | [H] interrupted-sweep resume test; a full sweep completes with zero 429-caused false reds |
| 6 | V-0 | Extends doctrine_harness/density_harness, never duplicates | [S] scope-warden diff confined to its globs; density assertions imported, not re-implemented |
| 7 | V-1 | ~30 primitives as versioned registry rows (definition, live-tool mapping+args, fallback face, known_gap) | [H] registry count ≥30; every mapped tool name ∈ the 135 live tools; every known_gap CR is OPEN/LOGGED — a known_gap citing a CLOSED CR fails |
| 8 | V-1 | Per-intent-class floors + machine bands as data; EVERY intent class has a floor | [H] floors cover the compiler's full intent-class enum; floor(wealth_deepdive) matches the design-§3 template shape |
| 9 | V-1 | Deterministic compiler: identical scope_tuple → identical contract | [H] hash-equality test: same tuple twice → byte-identical contract; unit tests in CI |
| 10 | V-1 | track3/ source drafts committed (absorbed Track-3) | [S] directory exists with floors+primitives drafts; DONE-CHECK items satisfied |
| 11 | V-1 | CR-27 corpus mapped: 4 Class-9 improvisations + CR-36 buried-evidence specimen + §G.0 table each prevented by a floor item or noted out-of-contract | [H] mapping table is total (6+ rows); harness spot-checks the 4 improvisations resolve to floor-item ids |
| 12 | V-1 | §B0.4 mandatory floor content: chalit/bhava-cusps, Sudarśana, Bhavat Bhavam, bhāva-bala, ashtakavarga_bindu_sign, D2 varga_hora_class, karakamsa_position, KP cusps+sub-lords, dasha_lord_capability, varga_ratification_divergence, sensitive degrees | [H] all 11 items appear in ≥1 floor's contractually-consumed list (V-1 verifier asserts) |
| 13 | V-1 | bg_vidhi* writer(s) + asset_registry row(s) with correct count_sql | [S] migration guard receipt + registry row exists + asset lit post-rebuild with count_sql-backed count >0 |
| 14 | V-2 | Vidhi registry as MCP resource | [H] deployed resources/list contains it; resource readable, rows match V-1's registry |
| 15 | V-2 | Compiled plans as MCP prompt + plan_retrieval fallback tool | [H] prompts/list contains it; fallback tool returns a compiled plan for a wealth question |
| 16 | V-2 | Scope tuple echoed for correction before execution | [H] plan/prompt output contains the echoed tuple field (contract shape depends on §B.7 ruling) |
| 17 | V-2 | Completeness receipt on EVERY synthesis (served/empty/dark per floor item; dark cites CR) | [H] = row 3 run against live readings post-deploy |
| 18 | V-2 | capability_version + tools/list_changed staleness kill | [H] capability_version served; bump-triggers-notification test |
| 19 | V-2 | amjis-mcp image SHA advances after each cycle-2 deploy | [S] gcloud describe before/after (evidence recipe; the REPORT_D-1.5b deploy-path trap) |
| 20 | V-3 | Pass-1 SCAN face (~60B/row) + Pass-2 FETCH-by-id | [H] scan tool live; avg row bytes ≈ target; fetched ids resolve to full rows |
| 21 | V-3 | Capability map live source / CR-9 | [H] asset_registry_all/_l0 return 200 on BOTH faces post-fix. **Bind note: 401 did not reproduce on the ?api_key face — V-3 re-verifies root cause first (see §B0.1)** |
| 22 | V-3 | Canonical-face list (~30 faces) authored; deprecated twins removed from LLM-visible list | [H] row-4 alias check green; CR-30 progress recorded in register |
| 23 | V-3 | CR-44 description-vs-payload CI audit (extends R-18 harness) | [H] CI job green with 0 unexplained divergences (explicit flags allowed) |
| 24 | V-3 | Errors-that-teach: corrected call returned on malformed input | [H] harness sends a malformed call → response carries the corrected-call suggestion (also cover the ref_yogas_get domain-vocabulary trap from §B.5) |
| 25 | V-3 | Per-chart reading-notes as MCP resources (CR-38/71/80 content) | [H] resources exist for 482012f1; content matches register rows |
| 26 | V-3 | Chart-keyed special-lagna access (CR-16) | [H] special-lagna query accepts chart_id and serves 482012f1's stored rows (schema-verified OPEN at bind) |
| 27 | V-3 | Pact MD-lord naming (CR-15) | [H] pact_query names the true MD lord (Mercury until 2027-08-19, then Ketu) on a live specimen |
| 28 | V-3 | Holistic bundle sub-tool repair; non-ok on sub-errors (CR-14/39) | [H] induced sub-error → bundle returns non-ok/explicit error section, never silent partial-ok |
| 29 | V-3 | intent_classify wired as scope-tuple classifier per CR-28 ruling | [H] post-ruling contract test. **GATED on §B.7 — do not wire before the Opus adjudication** |
| 30 | V-4 | Mechanism = named valenced CGM subgraph, first-class table + serving face | [S] migration guard receipt + [H] serving face returns ≥1 named mechanism for 482012f1 with valence + member nodes/edges |
| 31 | V-4 | Real edge-strength formula from ga_vichara; hardcoded literals retired (CR-86) | [H] edges carry formula_version + constituent ga_vichara refs; strengths non-degenerate (distribution test, anti-vacuous); [S] grep proves literals removed |
| 32 | V-4 | 10→8→12→10 chain/circuit motif exists as a SERVED mechanism (CR-24) | [H] motif query returns that circuit on the LIVE chart — verified by firing per §F1.7(5); if the live chart lacks it, the specimen is re-derived and the brief-vs-reality mismatch reported, not papered over |
| 33 | V-4 | Completed centralities: eigenvector, betweenness, harmonic | [H] cgm metrics rows carry all three non-null, non-constant across nodes |
| 34 | V-4 | CGM salience joins composite ranking (CR-25) | [H] ranking_basis.structural_role sourced from real CGM metrics; rank order measurably differs from the stub baseline |
| 35 | V-4 | CR-84: post-CGM re-rank pass → MSR structural_role dead link closed | [H] MSR ranking input references live CGM metric values; bo_laksana re-rank runs post-CGM in the DAG |
| 36 | V-4 | CR-85: ka_yojaka centrality-consumption stub removed | [H] `cgm_centrality_weight` in kala predicates ≠ constant 0.5 (live probe today shows flat 0.5 — the before-state is on record in §B.1 check 5's predicate rows) |
| 37 | V-4 | bo_anveshana retired (CR-78): registry removal + data disposition via migration WITH guard receipt | [S] guard receipt + registry row inactive/removed + [H] discoveries surface serves mechanism-derived rows; anything beyond idempotent delete-then-insert = PARK class 2 |
| 38 | V-4 | CR-62 multi-varga map: D10 lord-placement/karaka joins in career lens (wealth {D1,D2,D9,D11}, career {D1,D9,D10}) | [H] judgment_query(career) varga_subscores include D10 lord/karaka terms with non-zero weights |
| 39 | V-4 | PARK-#4 pickup: the 5 residual keyword rows re-emitted from the fixed builder or proven dead | [H] the 5 target rows' valence_source ≠ keyword_heuristic_v1 OR documented-unreachable proof. **BIND SCOPING FINDING: live keyword_heuristic_v1 population = 43,408/49,360 rows chart-wide — the "5 rows" is the PARK's narrow assertion scope only. V-4's re-rank pass works this substrate anyway; its close report must state explicitly what population the valence re-emit covered, so the register row can be dispositioned honestly** |
| 40 | V-4 | (F2 pickup) bo_laksana count_sql tightened to exclude sibling writers' rows | [S] surgical migration + guard receipt; count matches bo_laksana-owned classes only |
| 41 | V-5 | Four new emitter modules: nakshatra-semantic (CR-26/64), arudha (CR-61), special-lagna (CR-76), vargottama+dhana-axis (CR-36) — new files only | [H] post-rebuild, `bodha_signals_get(signal_type_class=<each>)` returns ≥1 row per class on 482012f1 with 0-orphan constituents; [S] scope-warden confirms new-files-only |
| 42 | V-5 | Append-only class registry; `owned_signal_type_classes` delete allowlist respected — rebuild never wipes a sibling class | [H] cross-writer scope check: per-class row counts for all 14 pre-existing classes (§B.2 table) unchanged after V-5's writers rebuild (the bo_laksana/bo_sudarshana class of defect, altitude b) |
| 43 | V-5 | Class priors per the recorded DR-n (§B.2 proposal) | [H] l0_class_priors values match the DR; served salience reflects them (spot ratio test) |
| 44 | V-5 | Gate Ś #8 disposition per §B.8 | [H] if absorbed: yoga-class activation rows with real dates >0 (from 74/0) and non-flat alignment; if parked: register row present + gate lists it excluded-non-blocking |
| 45 | V-6 | Upapada wiring (CR-101): BPHS ch.30 rules × computed A12 | [H] upapada facts/signals live for 482012f1, derivation ledger cites L0 rule ids (B.3) |
| 46 | V-6 | Nārāyaṇa Daśā (CR-104) | [H] narayana periods served for the chart (catalog presence confirmed live at bind: narayana + chara definitions exist in the 30-system ref catalog) |
| 47 | V-6 | Pañcadhā-maitrī compound matrix (CR-105) | [H] compound-relation facts served; one classical specimen spot-checked (e.g. Sun–Saturn compound status) |
| 48 | V-6 | Chara Daśā wired as timing witness (CR-77 — wiring, not build) | [H] chara periods appear as a witness on a timing surface for 482012f1 |
| 49 | V-6 | Kendrādhipati-doṣa + per-lagna functional-benefic completion | [S] Adjudicator-doctrine DR-n recorded BEFORE emission (extends valence matrix; must be consistent with DR-4's NBRY-grounds taxonomy) + [H] Aries-lagna rows match the DR; all 12 lagnas covered |
| 50 | V-6 | CR-73: every served dosha per-chart computed WITH cancellation/bhaṅga checks, or catalog-gated | [H] dosha_fires default page = computed rows only, each carrying a bhaṅga-check field; B9 gate still excludes catalog-only (regression on §B.1 check 2) |
| 51 | all | Three verification altitudes per cycle: Phase-1 per-lane / integration cross-lane / post-deploy LIVE before next cycle spawns | [S] receipts + integration sweep log + per-cycle live re-run recorded in STATE_D-2.md |
| 52 | all | Scale realism + data-over-flags: verifiers probe live rows, never fixtures-only or asset_throughput flags | [S] each verifier receipt names the live-data probe it ran (cockpit-truth rule §N.4) |
| 53 | all | Truncation honesty: no absence claim from a trimmed page | [S] harness absence-assertions page to exhaustion or use total fields (judgment_query and ref_dasha_systems_get are >64KB — see §B.5 — exactly the surfaces where a truncated-read absence claim would lie) |
| 54 | gate | §G.1 master acceptance: FRESH Sonnet floor-model reading agent, isolation recipe, 6/6 conclusions | [H] harness judges conclusion coverage; verbatim prompt in Appendix A below |
| 55 | gate | §G.2 census ≥ baseline + alias count + receipt present + Gate-A/B/Ś regression green (residuals absorbed/dispositioned) | [H] composite gate run, paced per V-0 rules |
| 56 | gate | §G.3 second synthesis probe, career domain: floor items served or honestly dark-cited, receipt validates | [H] career reading + receipt validation |

Ledger is total over §F1's seven lanes' deliverables, type specimens, servability claims and
closes-CR claims as enumerated in the brief. No §F1 promise is unledgered → the §F1.7(1) bind
condition is met.

## Appendix A — §G.1 verbatim gate prompt (stored at bind per the isolation spawn recipe)

> You are a Jyotish reading agent. You have access to exactly one instrument: the MARSYS-JIS MCP
> connector. You have no other files, notes, or prior context about this chart or this project.
> Task: produce a full financial (wealth) assessment for chart
> `482012f1-710e-4a25-994a-93821f5871aa` (ayanamsha lahiri_chitrapaksha). First retrieve the
> server-provided vidhi plan for a wealth deep-dive and follow it. Produce the reading with an
> explicit citation (served signal id / fact id / verdict field) for every conclusion you state,
> and include the completeness receipt the server returns. State honestly anything the plan calls
> for that the server could not serve. Do not invent chart values.

(Spawn: empty cwd outside the repo, tool allowlist = the deployed connector only, model=Sonnet.
The harness — not the agent — judges the 6-conclusion coverage afterward.)

## Verdict

**Brief BOUND: YES.** All 10 §B slots resolved against live state; §B0 spot-verified (one
documented anomaly: CR-9 did not reproduce on the direct face — V-3 re-verifies before fixing).
Prior-battery regression sample: 12/12 PASS, both expected residuals confirmed, zero unexpected
reds → lanes may spawn.

**Required conductor actions before/at SPAWN:**
1. Dispatch the CR-28 Opus engineering adjudication (§B.7) — gates only V-3's intent_classify wiring.
2. Formally record the two PROPOSED doctrine rulings (§B.2 class priors, §B.4 edge-strength
   formula) as DR-n entries with Fable-by-native-delegation provenance (§8.8(ii): register edits
   are conductor-only).
3. Record the §B.1 rollback pin + this ledger in STATE_D-2.md and commit.

**Non-blocking observations for the wave:** judgment_query(v3) ~69KB and ref_dasha_systems_get
~76KB exceed the 64KB ceiling (no prior baseline; V-0 baselines byte sizes, budget work is
S-5-class debt); chart_dashas = 483,060 vs the superseded 536,471 canonical (stability check at
first rebuild); keyword_heuristic_v1 valence population is 43,408 rows chart-wide (PARK-#4's
"5 rows" is the narrow assertion scope only — row 39).

*Binder remit note (§1.1): this pass wrote nothing to the repo — its entire output is this record
plus the brief's status stamp, both to be written by the conductor.*
