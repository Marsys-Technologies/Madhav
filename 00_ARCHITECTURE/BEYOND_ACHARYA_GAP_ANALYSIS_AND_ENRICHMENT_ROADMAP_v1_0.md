---
canonical_id: BEYOND_ACHARYA_GAP_ANALYSIS
version: 1.3
status: DRAFT-FOR-NATIVE-REVIEW
created: 2026-07-02
author: Cowork (strategic workstream, Claude Fable 5) — for native Abhisek Mohanty
parent: MARSYS_STRATEGIC_HANDOFF_v1_0 (north star) + MCP_SYSTEM_AUDIT_FINDINGS_v1_0 (live reality)
method: >
  Ground-truth inventory of all six layers taken from WRITER SOURCE CODE (bg_*/ga_*/bo_*/ka_*/ph_*/mi_*.py),
  not from seal documents; cross-checked against live MCP probes of chart 482012f1 (2026-07-02) and the
  W1–W4 audit-fix state. Gaps are classified by KIND, then ordered by leverage toward the north star:
  understanding, interpreting, and predicting charts beyond what any human practitioner can hold.
changelog:
  - v1.3 (2026-07-02): §10 added from native's two probe-questions — (a) query-class readiness matrix
    (period-quality and undertaking-outcome queries CANNOT be served today; taxonomy of 7 predictive query
    classes with data-path/composition/readiness each; activity ontology + prashna chart-type + period-reading
    product named as new requirements); (b) learning-loop verdict = REDESIGN mechanics, retain infrastructure
    (blind protocol, control windows, ablation attribution, classical-priors-as-Bayesian-priors, bounded
    two-key updates). E-waves amended (E2.5 scope grows; E3 gains the period-reading + undertaking products).
  - v1.2 (2026-07-02): §9 added — L4/L5 deep audit (native dissatisfaction ratified as findings P-1…P-5,
    M-1…M-5) + the PROMISE→ACTIVATION→TRIGGER→DELIVERY redesign + the L5 Retrodiction Engine; §6 E3/E5
    revised accordingly (E3 restructured, retrodiction pulled forward into new E2.5).
  - v1.1 (2026-07-02): §8 added — layer folding map (native question: new layers vs existing). Verdict: no new
    layers; one new subject type (chart-pair), two new feedback arrows (L5→L0 graduation, L5→L2 re-weighting),
    two services (transit application, waveform fine-grain).
  - v1.0 (2026-07-02): first full gap analysis across L0–L5 + beyond-human frontier + leverage-ordered roadmap.
---

# BEYOND-ACHARYA GAP ANALYSIS & ENRICHMENT ROADMAP v1.0

> **The one-sentence verdict.** The corpus is dramatically more complete than the strategic handoff assumed —
> the binding constraint is no longer *collecting* astrology; it is that the collected astrology is not yet
> **organized as judgment** (salience, graph semantics, cross-tradition concordance, temporal convolution,
> outcome calibration). The fastest path to beyond-acharya insight is not "add more systems" — it is to make
> the systems already computed at L1 *reach* the synthesis surfaces, and to build the five organs no human
> tradition ever built because no human could operate them.

---

## §1 — WHAT ACTUALLY EXISTS (corrected ground truth; the handoff understates L1)

Verified from writer source code 2026-07-02. Per chart × 5 ayanamshas unless noted.

**L0 (reference, ~840k rows):** 15 classical works, verse-level, 8,193 embedded chunks (BPHS 2,094 vv,
Phaladeepika, Saravali, Jataka Parijata, Brihat Jataka, Uttara Kalamrita, Jaimini Sutras, Hora Sara,
Muhurta Chintamani, Tajaka Neelakanthi, Bhrigu Nandi Nadi, Nadi Navamsa, Yavana Jataka, Brihat Samhita,
Sarvartha Chintamani); ~1,900–2,500 regex-extracted rules; 81+ yoga catalog with cancellation rules;
50-dosha catalog; 264-remedy corpus; nakshatra subsystem (27+Abhijit, 108 padas, full attribute set);
prashna methods (5 lagna methods incl. KP 1–249); transit rules (thin: ~37 rows); medical mappings;
ephemeris 1900–2150 (825k rows).

**L1 (deterministic, ≥602k rows/chart) — the correction that matters most:**
- **Cross-tradition data EXISTS at L1**: Jaimini chara karakas (8), graha arudha padas, chara-karaka dasha,
  jaimini + tajika aspect matrices, tri-deva roles; KP sub-lord AND sub-sub-lord per graha AND per cusp;
  Tajika varshaphala (solar return, Muntha, Yogini varsha); Nadi vargas D108/D150/D2700 with rishi/karma
  attribution; Lal Kitab pakka-ghar flags. **The handoff's "other traditions are the enrichment horizon" is
  stale — they are an L2-projection horizon.**
- 7 dasha systems × 4 levels (Vimshottari/Yogini/Ashtottari/Chara-karaka/Naisargika/Mudda/Kalachakra),
  1950–2100, 536,471 rows. Prana (5th level) scope-capped.
- 30 vargas (16 Parashari + 11 supplementary + D108/D150/D2700) with dignity, vargottama family
  (vargottama/super/trikona/trans-count), pushkara navamsa+bhaga, per-varga aspect matrices, per-varga
  ashtakavarga, D60 deities, D30 lords.
- Full shadbala (6 components, D1) + ishta/kashta + vimsopaka ×4 sets + bhava bala (7 components);
  ashtakavarga bhinna/sarva + trikona/ekadhipathya shodhana + kakshya.
- Avasthas: baladi + deeptaadi per 16 vargas; jagradadi D1; sayanadi/lajjitadi FLOORED.
- Sensitive: ~24 Tajika sahams, 4 special lagnas, gulika/mandi/dhooma, yogi/avayogi, bhrigu bindu,
  pranapada, gandanta flags.
- Structural: 3 aspect systems, conjunctions, dispositor chains + composite dispositor strength,
  parivartana pairs, argala 144-matrix + virodha 144-matrix, 200+ yoga fires with constituent fact_ids and
  cancellation, functional benefic/malefic per lagna, neecha-bhanga/vipareeta rollups.
- Panchanga incl. tara bala (9-fold) + chandra bala; sade sati phases; medical indications; vastu map;
  prashna judgment engine; transit anchors (house-from-Moon per graha).

**L2 (synthesis, ~64.7k signals/chart):** full-enumeration MSR (11 signal_type_class families) with
50-column schema incl. salience decomposition + signature_tier + valence + tradition + constituent facts +
citations; CGM graph (bo_bimba nodes + bo_karanajala 7 edge types + motifs: mutual_reception, stellium,
parivartana_chain); contradictions (~1,034/chart); CDLM (70 cells); remedy resonances; per-signal
embeddings (bo_samskara); 12 question lenses; quality scorecard.

**L3 (timing):** activation predicates (ka_yojaka), convergence engine (ka_sangam, 4 modes, 7-yr +
lifetime horizons), obstructions, dasha/gochara/muhurta services. **L4 (prediction):** anchors from
convergence+discovery (spine-first gate), confidence = dasha_quality × signal_strength × convergence,
falsifiers, mitigations, muhurta, rectification (validates 10:43 birth time on held-out LEL). **L5
(learning):** attribution/negative-control/discovery substeps, journal, export — STRUCTURAL, awaiting
outcomes.

---

## §2 — GAP CLASS A: ASTROLOGY NOT YET CAPTURED (data-collection gaps)

Ordered by interpretive weight, not by count. Fewer than the handoff feared; each is precise.

- **A1. Bhava arudhas (A1–A12), including Arudha Lagna and Upapada (UL).** Graha padas exist; BHAVA padas
  do not. This is the single most consequential classical omission: AL is the Jaimini lens on manifest
  status/perception (career-as-seen), UL on marriage trajectory — both indispensable for prediction that
  matches lived reality (perceived life ≠ inner life is *itself* a beyond-acharya discriminator the chart
  encodes). Cheap to compute (sign arithmetic from existing lords/positions).
- **A2. Classical Jaimini Chara dasha (sign-based, Rao-standard) + Karakamsha/Swamsha chart.** The
  chara-karaka dasha built is a karaka-lord sequence; the canonical sign-period Chara dasha and the
  Karakamsha (AK's navamsha sign as lagna) reading surface are absent. Together with A1 they complete a
  fully independent second prediction stack for triangulation (see B4).
- **A3. Per-varga shadbala/bhava-bala** (native ruling L1-E 2026-06-17, not yet built): strength currently
  D1-only while positions/dignity/avasthas are per-varga — the D10 tenth-lord's *strength in D10* is
  exactly what career judgment needs. (Extension, labeled non-canonical where classical texts are D1-only.)
- **A4. Graha yuddha** (explicitly not computed in ga_condition), **lajjitadi/sayanadi avasthas**
  (floored — lajjitadi is judgment-relevant: BPHS gives it strong phala weight), **BLS/speed strength.**
- **A5. Ashtakavarga-in-transit machinery**: kakshya-level transit triggers and sarvashtakavarga gates for
  gochara. The natal ashtakavarga is complete; the transit application (its classical purpose!) has only
  ~37 generic transit rules at L0. This is the highest-value TIMING data gap.
- **A6. Nadi rule extraction**: Bhrigu Nandi Nadi + Nadi Navamsa are IN the text corpus and D108/D150/D2700
  positions are computed — but no Nadi jataka rules are extracted into the rule base; the finest-grain
  varga data currently has no interpretive consumers (it saturates salience instead — see B1).
- **A7. Multi-chart relational astrology (synastry/ashtakoota/family-lattice).** Nothing in any layer
  relates two charts. Four charts are already entitled (family). Koota references exist in the dosha
  catalog but no engine. Beyond-acharya prediction for relationship/progeny domains is structurally capped
  without it.
- **A8. Minor completions:** Upapada-dependent doshas; Narayana dasha (optional 8th system); Prana dasha
  level (only if day-grade prophecy is a goal — pairs with A5); sarvatobhadra/vedha chakras for transit
  sensitivity; muhurta election depth (choghadiya/hora already in L4 muhurta — verify coverage).

**What is NOT a gap:** more texts, more yogas, more vargas, more sahams, more dasha systems for their own
sake. §1 shows collection is largely done. Every new collection item must name its consumer.

---

## §3 — GAP CLASS B: CAPTURED BUT NOT ORGANIZED AS JUDGMENT (structural gaps — the highest leverage)

This is where beyond-acharya is won or lost. Six structural inversions, all fixable without new source data.

- **B1. Salience carries no astrology.** (F-020/F-025, root cause now precisely known from bo_laksana.py.)
  `salience = orb × shadbala(D1) × dignity(D1) × verification × house_wt × av_mult × modifiers` — the
  formula sees WHO (graha) and WHERE (house) but never WHAT (signal type) or AT-WHAT-GRAIN (varga). Hence
  thousands of exact ties at 2.326672 and a top band saturated by D2700 bindu tallies while 90 detected
  yogas rank nowhere; signature_tier thresholds (≥3.0) sit above the formula's achievable max (~2.33) —
  the tier can never fire. **Fix shape (salience v2): a multiplicative class-prior vector.**
  `salience_v2 = class_prior(signal_type) × varga_weight(varga_grain) × specificity(configuration rarity)
  × condition_modifiers (v1 terms) × dasha_activation_boost (L3 hook)`, where class_prior is the
  acharya-judgment table (yoga_raja > yoga_major > dosha_major > dignity_extreme > karaka_alignment >
  house-lord placement > … > per-varga bindu atom) — a native-ratified, versioned formula per the
  canonical-or-floor rule. **Plus hierarchical aggregation:** atomic family members (e.g., 360 per-varga
  bindu rows per graha) roll up into ONE composite profile signal (distribution attached); atoms remain
  queryable but never compete with composites for the top band. Re-ranking alone moves the served product
  from "bindu tallies" to "the chart's defining structures" — most of the distance to insight, exactly as
  the handoff predicted, now with a concrete formula target.
- **B2. The CGM projects a fraction of the relational riches L1 already computed.** Live traversal shows
  edges of one type (`aspect`), valence NULL, relationship_basis NULL, affected_domains NULL — while L1
  holds dispositor chains, argala+virodha matrices (288 rows), parivartana pairs, yoga-constituent
  memberships, karaka roles, nakshatra-dispositor chains, KP sub-lord chains. **Every one of those is an
  edge type waiting for projection.** Target: a graph where career = traverse(10th house ← lords ←
  dispositors ← argala ± virodha ← yoga-memberships ← dasha-activation), with valence + strength +
  domain tags on every edge. This is a bo_bimba/bo_karanajala enrichment, zero new L1 computation. The
  graph is the one organ a human cannot hold — today it holds less than an acharya does.
- **B3. Contradictions are counted, never weighed.** 1,034/chart exist but carry no domain attribution
  (live: every domain shows contradiction_count 0) and no reconciliation. Beyond-acharya's defining act is
  "the chart says X and ¬X; here is the resolution and why." Needs: domain tags on contradiction rows +
  a reconciliation record (evidence-weighted verdict citing both sides' salience_v2 + activation state).
- **B4. Cross-tradition triangulation has data but no structure.** Parashari, Jaimini, KP, Tajika answers
  to the same question are all computable from existing L1 — but signals are ~mono-tradition
  (`present_in_traditions_array` ≈ ["parashari"]) and nothing represents concordance. Build the
  **Triangulation Object**: per question, per tradition-stack, the independent verdict + a concordance
  score. Agreement across independent methods is the strongest confidence signal astrology can produce
  internally (before outcome calibration exists) — and no human runs four stacks in parallel.
- **B5. The ayanamsha ensemble is stored but unused.** Everything is computed ×5 ayanamshas; nothing
  consumes the VARIANCE. Cross-ayanamsha stability fields exist (nakshatra 5/5 checks; graph
  cross_ayanamsha_* columns) but are NULL/unaggregated. Treat the 5 as ensemble members: claims stable
  across all 5 get a robustness multiplier; ayanamsha-fragile claims get flagged. Free confidence
  dimension, zero new computation.
- **B6. Dasha-activation columns on signals are the designed L1↔L3 bridge — verify they FILL.**
  bo_laksana writes them NULL for ka_yojaka to fill; the classical gate "a yoga delivers only in its
  lords' periods" lives or dies on this join reaching the serving surface (get_signals returns salience
  ranked without activation state today). Activation-aware ranking = prophecy-aware insight.

Plus the known integrity prerequisite: **DEFECT-001 MSR rebuild** (91.5% constituent_facts orphaned) —
fold B1/B2/B3 fixes into that same L2 regeneration so the corpus is rebuilt once, not thrice.

---

## §4 — GAP CLASS C: BEYOND WHAT HUMAN ASTROLOGY EVER BUILT (the frontier organs)

These are the constructs the tradition never had because no human could operate them. Each is buildable on
existing substrate; each is falsifiable-by-design per the Ethical Framework.

- **C1. The Temporal Activation Waveform (continuous prophecy field).** Convolve, per domain: 7 dasha
  systems (536k periods) × transit stream (ephemeris daily + transit anchors + A5 ashtakavarga gates) ×
  natal salience_v2 × convergence logic → a continuous day-resolution activation curve per domain,
  1950–2100. Humans sample a handful of dates; the machine integrates the whole field, finds every peak,
  ranks all windows in a life at once. L3 convergence already detects discrete windows — this generalizes
  it to a field, and L4 anchors become its local maxima with principled confidence.
- **C2. Computational Nadi: chart-embedding + case-based reasoning.** bo_samskara already embeds signals.
  Extend to whole-chart and per-domain configuration embeddings → similarity retrieval across a growing
  chart corpus → "charts most like this one in the career-relevant subspace, and what happened to them."
  This is precisely what Nadi palm-leaf libraries were — a case base — rebuilt at machine scale. It is
  also the n=1 escape hatch: outcome transfer from similar charts, honestly labeled as empirical prior.
- **C3. Empirical yoga discovery (rule induction).** Mine LEL + multi-chart outcomes for
  configuration→outcome associations NOT in the classical catalog (the discovery layer + mi_pariksha
  discovery substep are already scaffolded for this). Candidate patterns are held to pre-registered
  falsifiers before earning rule status. This goes "beyond the astrology humans know" in the exact,
  disciplined sense you intend: the corpus proposes; outcomes dispose.
- **C4. Counterfactual robustness scoring.** Perturb birth time ±N minutes (rectification already sweeps
  185 candidates), recompute the signal set, and mark every claim ROBUST/FRAGILE to birth-time error.
  Fragile claims are served with degraded confidence. No human astrologer quantifies this; it converts the
  oldest weakness of the field (birth-time uncertainty) into a stated confidence dimension.
- **C5. Graph motif mining.** Beyond the 3 seeded motifs: frequent-subgraph mining over CGMs across charts;
  motif→outcome correlation via L5. New relational "yogas" (multi-hop structures classical texts could not
  enumerate) discovered from the graph organ itself.
- **C6. The calibration→salience feedback loop (already designed, barely started).** Brier scores per
  technique × ayanamsha re-weight class_priors and tradition weights over time (two-key adhilepa overlay
  per L5 design). This is the mechanism by which the instrument *becomes* beyond-acharya rather than
  merely being built beyond-acharya — a practice that systematically learns which of its techniques work,
  which no tradition institutionalized.

---

## §5 — WHAT THE FOUR OUTCOME PRODUCTS NEED (mapping products → gaps)

| Product | Definition | Blocking gaps (ordered) |
|---|---|---|
| **Insight** | non-obvious true structure, cited | B1 salience → B2 graph → B3 contradictions → B5 ensemble |
| **Interpretation** | classical meaning, verse-grounded | B1 + L0 bridge (classical_sources_array fill) + A6 Nadi rules |
| **Prophecy** | time-bound, falsifiable, calibrated | B6 activation join → A5 AV-transit → C1 waveform → C4 robustness → DEFECT-001 |
| **Guidance** | remedial economics, prioritized | F-007 remedy scoring de-degeneracy → B1 (weakness ranking) → RM cost/effect model |

And one **synthesis contract** shared by all four (Wave-5 F-024): the serving layer must emit a *verdict
object* — top-k reconciled findings, each carrying {claim, evidence signals, contradiction resolution,
tradition concordance, activation state, ayanamsha robustness, confidence, falsifier, citations} — with
the LLM narrating ON TOP of the verdict object, never substituting for it. Ingredients stay B.1-clean;
judgment becomes data.

---

## §6 — LEVERAGE-ORDERED ROADMAP (each wave names its consumer; no orphan enrichment)

**E0 — Serving truth (days; prerequisite).** Verify Cloud Run revision vs W2–W4 SHAs; get bounding
(F-021 params ignored live), L4 anchors (F-005 still erroring live), kala sidecar UP. Nothing downstream
is testable until the pipes tell the truth. `[verify-against: prod]` on every AC.

**E1 — Judgment rebuild (the Wave-5 core; one L2 regeneration).** Salience v2 (B1: class-prior vector —
NATIVE RATIFIES THE WEIGHT TABLE — + varga weights + hierarchical aggregation + live signature_tier) +
CGM edge projection (B2) + contradiction domain-attribution (B3) + DEFECT-001 MSR rebuild, regenerated
together, two-chart verified. Acceptance = the audit's G10 test: career top-10 shows 10th-lord/karaka/
raja-yoga structures, ranked, with zero sub-varga atoms in the top band.

**E2 — Verdict + triangulation surfaces (retrieval/MCP fork).** The verdict object (§5) behind
get_domain_reading / assess_*; the Triangulation Object (B4) with per-tradition stacks; ayanamsha-ensemble
robustness (B5); activation-aware ranking (B6). This is the MCP-channel face of beyond-acharya.

**E3 — Prophecy substrate.** A5 ashtakavarga-transit gates + C1 temporal waveform (L3 extension) +
C4 robustness scoring; L4 anchors regenerated from the waveform. Prophecy becomes continuous, gated,
and birth-time-honest.

**E4 — Classical completions (parallelizable with E2/E3).** A1 bhava arudhas + Upapada; A2 Chara dasha +
Karakamsha; A3 per-varga shadbala (already ruled); A4 graha yuddha + lajjitadi; A6 Nadi rule extraction.
Each lands as new fact_categories → automatically projected by full-enumeration bo_laksana → ranked by
salience_v2 (which is why E1 precedes it).

**E5 — The research organs (multi-chart horizon).** A7 synastry lattice; C2 chart embeddings + case
retrieval; C3 rule induction; C5 motif mining — gated on chart-corpus growth (the M9/M10 research-tool
arc) and on E1's honest ranking. C6 calibration loop matures continuously from first predictions onward.

**Process substrate (spans all waves):** acharya-gate evals on served readings (AI-assessed rubric, as in
WS-3); a prediction ledger with pre-registered falsifiers feeding LEL→L5; degenerate-distribution guards
on every new scoring column (the 0.28-remedy and 2.326672-salience scars generalized into a build gate).

---

## §7 — THE HONEST FRAME

Everything above serves understanding, interpreting, and predicting — and stays inside the project's
Ethical Framework: probabilistic, calibrated, falsifiable, disclosed. "Beyond human astrology" here means
beyond human *working memory, parallelism, and self-correction* — completeness, integration,
contradiction-holding, calibration — not beyond evidence. The instrument's superiority claim is earned at
L5, one scored prediction at a time. Data first; judgment structures second; the tradition honored, and
exceeded.

## §8 — LAYER FOLDING MAP (no new layers; ruled 2026-07-02)

The six layers are a semantic pipeline — reference (L0) → deterministic facts (L1) → within-chart
relational synthesis (L2) → timing (L3) → prediction (L4) → cross-chart learning/calibration (L5). Every
recommendation in §2–§4 is one of those six kinds. **No new layer is created.** New architecture is
limited to: one subject type, two feedback arrows, two services.

| Item | Layer | Fold |
|---|---|---|
| B1 salience v2 — class-prior weight table | **L0** | NEW reference asset (native-ratified, versioned, chart-agnostic; must be L5-re-weightable) |
| B1 salience v2 — formula + tier + aggregation | **L2** | bo_laksana v2 (existing asset) |
| B2 graph edge projection | **L2** | bo_bimba / bo_karanajala enrichment (existing) |
| B3 contradiction domain-attribution + reconciliation | **L2** | bo_karanajala / bo_samvada (existing) |
| B4 triangulation object | **L2** | bo_sangati extension OR one new bo_* asset (within-chart deterministic stat per L2 philosophy) |
| B5 ayanamsha-ensemble robustness | **L2** | fill existing NULL cross_ayanamsha_* fields |
| B6 dasha-activation join | **L3** | ka_yojaka owns it (existing); verify-fill + serve |
| A1 bhava arudhas + UL/AL | **L1** | ga_sensitive extension (seal-amendment pattern, cf. L1-E) |
| A2 Chara dasha + Karakamsha | **L1** | ga_dashas + ga_sensitive extensions |
| A3 per-varga shadbala | **L1** | ga_strength (already ruled, L1-E 2026-06-17) |
| A4 graha yuddha, lajjitadi, BLS | **L1** | ga_condition extension |
| A5 AV-transit — static gate rules | **L0** | bg_transit_rules extension |
| A5 AV-transit — application | **L3 service** | transit = service-not-storage (existing ruling) |
| A6 Nadi rule extraction | **L0** | bg_rules extension from in-corpus texts |
| A7 synastry / family lattice | **NEW SUBJECT TYPE, not layer** | composite chart entity (type `synastry`, two member chart_ids); `sy_*` writers onboard against the FROZEN contract exactly like a layer (§N.2); pair-facts are L1-kind, pair-synthesis L2-kind, pair-timing L3-kind. Precedent: Prashna = chart-type, not layer. |
| A8 minor completions | **L1/L4** | respective ga_/ph_ extensions |
| C1 temporal activation waveform | **L3** | new ka_* asset (coarse curves stored) + fine-grain **service** (do not store day×domain×150yr) |
| C2 chart/domain embeddings | **L2** | bo_samskara extension (per-chart embedding is within-chart) |
| C2 cross-chart case base + retrieval index | **L5** | new mi_* asset (cross-chart → L5 per ratified rule) |
| C3 empirical rule induction | **L5** | mi_pariksha discovery (scaffolded) |
| C3 graduated rules | **L5→L0 ARROW** | NEW flow: survived-falsifier rules written to bg_rules with `provenance: empirical` + validation record |
| C4 robustness scores | **L2 column + L4 anchor field** | sweep = build-time process; scores stored as annotations |
| C5 motif mining | **L5** | discovery; motifs graduate via the L5→L0 arrow |
| C6 calibration→salience | **L5→L2 ARROW** | existing adhilepa two-key design; re-weights the B1 L0 prior table |

**Summary of genuinely new architecture:** (1) chart-pair subject type (A7); (2) L5→L0 graduation arrow
(C3/C5) — the formal, falsifier-gated mechanism by which astrology-beyond-the-known enters the canon;
(3) L5→L2 re-weighting arrow (C6, already designed); (4) two services (A5 transit application, C1
waveform fine-grain). Everything else converges into existing layers and mostly existing assets — per the
subsystem-embedding playbook: converge, inherit standards, never pre-build structure.

---

## §9 — L4/L5 DEEP AUDIT & REDESIGN (native review request 2026-07-02; source-verified)

The native's dissatisfaction with L4 Phala and L5 Mīmāṃsā is ratified by the code. The engineering is
honest and disciplined (leakage firewalls, no-scoring gates, holdouts, stated stubs) — but the PREDICTION
LOGIC is astrologically inverted and the LEARNING LOOP is idle by construction. Findings, verbatim-grounded:

### §9.1 — L4 Phala findings (ph_nimitta engine + 8 siblings)

- **P-1 [ASTROLOGICAL INVERSION — the core defect].** Anchor generation is TIMING-FIRST: anchors derive
  from convergence windows / discovery rows / bhavishya projections, and the WHAT is reverse-derived from
  whatever signal metadata rides the window. Classical phalita runs the opposite way: **(1) PROMISE — is
  the event promised in the natal chart (yoga/karaka/house-lord/varga structure), at what grade; (2)
  ACTIVATION — dasha periods whose lords connect to THAT promise; (3) TRIGGER — transit confirmation
  (gochara gates, double-transit); (4) DELIVERY — magnitude from strength of promise × activation
  quality.** Without stage 1, the system predicts "something in domain D around date T" — temporally
  shaped noise around a real convergence engine, not phala.
- **P-2 [NO EVENT ONTOLOGY].** `derive_event_type()` is keyword string-matching on `signature_class`
  (7 coarse types + fallback `{source}_event`); `derive_domain()` likewise with fallback `'transition'`.
  There is no classical event-signature model anywhere: nothing encodes "marriage = 7th lord + Venus +
  UL/D9 activation," "childbirth = 5th/9th + Jupiter + D7," etc. The WHAT layer of prophecy has no
  reference substrate (and it is an L0-kind asset — see §9.3).
- **P-3 [CONFIDENCE WITHOUT PROBABILITY SEMANTICS].** G-LADDER (verbatim): `f = max(0.5, convergence);
  ceiling = min(0.80, 0.50 + 0.05×min(n,6)); rob = 0.80+0.04×robustness; mid = min(f, ceiling)×rob;
  range = mid±0.10, high≤0.80`. Consequences: (a) the floor construction means every anchor lands in a
  ~[0.30–0.80] band — the instrument can never say "unlikely"; (b) no base rate anywhere — "a health
  episode within a 90-day window" is frequent for ANY human, so a 0.6 tells nothing; (c) downstream L5
  Brier scores will measure base-rate miscalibration, not technique skill. Confidence must become
  `posterior = base_rate(event_class, age_band, window) × chart_lift(promise × activation × trigger)`,
  with the lift factors the calibratable quantities.
- **P-4 [WEAK FALSIFIERS].** Template: "REFUTED if no positive {domain} {event_type} is independently
  documented by {date}." "Positive career development" in a year is near-unfalsifiable. Falsifiers must
  bind to **LEL admissibility magnitude** (e.g., "an LEL-admissible magnitude ≥ major career event") so
  CONFIRMED/REFUTED is machine-decidable against the log's own rules.
- **P-5 [MONO-DASHA + LIVE BREAKAGE].** Anchors ride Vimshottari-era convergence only (U1 multi-dāśā
  population deferred) while L1 holds 7 systems for cross-confirmation. Live prod: anchors/mitigations
  schema-broken (F-005 recurrence), anchors empty at 12-month horizon, panchanga_daily unpopulated.
  Sound positives to keep: karmic-frame vocabulary, magnitude tiering, D5 NO-SCORING discipline,
  rectification engine (validates 10:43), narration separation.

### §9.2 — L5 Mīmāṃsā findings (12 mi_* assets)

- **M-1 [THE LOOP IS IDLE BY DESIGN — the core defect].** L5 waits for FUTURE outcomes (STRUCTURAL mode,
  n=0; gates n≥5 empirical / n≥10 promotion) while **57 adjudicated past events sit in the LEL**. The
  `retrodictive_match` field exists but is a MANUAL astrologer annotation, not a machine backtest. At
  n=1-chart prospective rates, the gates unlock in years. The layer is architecturally sealed and
  operationally dormant.
- **M-2 [SCORING DESIGN GAPS].** Brier over G-LADDER pseudo-probabilities inherits P-3's meaninglessness;
  no proper scoring for interval/censored predictions (event-in-window needs interval-aware scoring);
  hard n-gates produce dead zeros where **hierarchical shrinkage** (partial pooling across technique ×
  dasha-system × event-class cells) would give usable, honest estimates from n=3.
- **M-3 [NULL MODEL MISSING].** Negative controls exist (good) but the benchmark every technique must
  beat is absent: the **base-rate-only null** (climatology, as in weather-forecast skill scores). Add
  placebo controls: time-shifted birth charts, scrambled-dasha sequences.
- **M-4 [FEEDBACK UNWIRED].** The adhilepa L5→L2 re-weighting is designed (two-key) but not wired;
  `_score_falsifier` / `_score_manifestation` are stubs. The mechanism that makes the instrument LEARN —
  its deepest beyond-acharya idea — has no moving parts yet.
- **M-5 [n=1 UNDER-EXPLOITED].** Multi-chart deferred wholesale — yet 4 entitled family charts exist, and
  family LELs cross-reference (one native's marriage IS an event in relatives' charts: 7th-house activation
  in one should co-occur with 5th/2nd-house activation in parents' — a cross-chart consistency check no
  tradition could run systematically). Sound positives to keep: leakage firewall (MD5 holdout), honest-n
  reporting, bootstrap CIs, bounded modulation, negative-control substep, journal/export.

### §9.3 — The redesign: PROMISE → ACTIVATION → TRIGGER → DELIVERY (folds per §8; no new layers)

- **R-1. Event Ontology (L0, new reference asset; native ratifies).** ~20–30 predictable event classes;
  per class: signifying houses/lords, karakas, key vargas, classical dasha rules, transit triggers,
  LEL-admissibility magnitude threshold, **base-rate prior by age band**, classical citations. This is
  the WHAT-substrate of prophecy and the second native-judgment table after the B1 class-priors.
- **R-2. Promise Register (L2, new bo_* asset or bo_sangati extension).** Per chart × event class:
  promised / denied / conditional + grade + supporting and contradicting signal refs (salience_v2-ranked)
  + varga confirmation state. Pure natal judgment — the answer to "what does this chart promise?"
  BEFORE any timing. (Doubles as an insight product in its own right.)
- **R-3. Activation Calendar (L3, ka_yojaka/ka_sangam extension).** Per promised event class: dasha
  periods whose lords connect to the promise across ALL 7 systems (cross-confirmation count as a
  first-class score — closes U1 with purpose), transit triggers from R-1 (+A5 AV gates, double-transit),
  producing promise-specific convergence rather than generic peaks. C1's waveform becomes per-event-class.
- **R-4. Anchor v2 (L4, ph_nimitta rebuild).** `anchor = (event_class, window, magnitude, posterior)`
  where `posterior = base_rate × promise_grade_lift × activation_lift × trigger_lift`, each lift
  L5-calibratable; falsifier bound to LEL admissibility (P-4); direction retired in favor of event_class
  + magnitude; full G-LADDER retired (its ayanamsha-robustness term survives as a lift modifier).
- **R-5. Retrodiction Engine (L5, mi_pariksha elevation — THE unlock).** Machine backtest: for each of
  the 57 LEL events (and each family chart's LEL as they accrue), generate R-4 anchors from strictly
  pre-event data (leakage firewall pattern already proven in ph_pramana rectification), auto-adjudicate
  against the event, score per technique × dasha-system × event-class with hierarchical shrinkage, always
  against the M-3 null. **Turns n=0 into n≈57 immediately**; headline metrics stay prospective-labeled;
  retrodictive results feed the lifts and the adhilepa re-weighting NOW, not in three years.
- **R-6. Wire the feedback (M-4).** Implement `_score_falsifier`/`_score_manifestation`; activate adhilepa
  two-key (L5→L2 class-prior re-weighting + L5→R-4 lift calibration); extend record_outcome with an
  auto-resolution scan of open anchors against new LEL entries.

### §9.4 — Roadmap integration (revises §6)

**E2.5 — Retrodiction + prediction-integrity wave (NEW; pulled ahead of E3 — needs only existing data):**
R-5 retrodiction engine + M-3 null models + M-2 shrinkage + R-6 wiring + P-4 falsifier hardening.
Prerequisite: E0 (L4 schema repair) + DEFECT-001 rebuild (machine-resolvable constituent facts).

**E3 (REVISED) — Prophecy substrate = the R-pipeline:** R-1 event ontology (native ratification session
alongside the B1 class-prior table — schedule as ONE judgment sitting) → R-2 promise register → R-3
activation calendar (subsumes A5 gates + C1 waveform + U1 multi-dāśā) → R-4 anchor v2. Acceptance: for
chart 482012f1, anchors name event classes with posteriors spanning the FULL probability range (including
"denied/unlikely" verdicts), each with an LEL-decidable falsifier; retrodiction skill > null on ≥3 event
classes before any prospective claim is served.

**E5 (amended):** M-5 family-lattice cross-chart consistency checks join the synastry work; C2/C3/C5
research organs consume the retrodiction corpus as their first training signal.

---

## §10 — QUERY-CLASS READINESS + LEARNING-LOOP REDESIGN (native probe-questions, 2026-07-02)

### §10.1 — The two probe questions, answered honestly

**"How will my Ketu dasha in 2027 be?"** — NOT servable today. Correct method = a composition: Ketu natal
dossier (sign/nakshatra/dispositor — Ketu delivers through its dispositor and conjunctions — house, D9,
karaka roles) × promises Ketu activates as period lord × AD-lord modulation × transit overlay × classical
Ketu-dasha phala citations. L1 holds every input; NOTHING composes them. No period-reading product exists
in L2–L4; L3 timeline is Vimshottari-only (U1); kala sidecar serving empty; `yoga_activation_by_dasha` is
an ingredient, not a verdict. **Readiness: data ~80% / composition ~15% / serving broken.**

**"What is the outcome of this activity two months from now?"** — NOT servable today. Muhurta+prashna
hybrid: needs an ACTIVITY ONTOLOGY (activity → houses/karakas/significators — sibling of R-1), the prashna
chart-type build path (subsystem program: planned, unbuilt), election scoring against the native's own
chart (tarabala/chandrabala exist at L1), fructification timing (L0 rules exist), verdict composition
(absent), and live panchanga (0 rows). **Readiness: data ~50% / composition ~0%.**

### §10.2 — Query-class taxonomy (supersedes §5's four-products frame as the operational contract)

Every predictive query the portal must serve, with its recipe and current readiness:

| # | Query class | Example | Composition recipe | Readiness |
|---|---|---|---|---|
| Q1 | Period quality | "Ketu MD/AD in 2027" | lord dossier × activated promises × sub-lord × transit × citations | data ✅ / composition ✗ |
| Q2 | Event timing | "when will I marry" | R-2 promise → R-3 activation calendar → ranked windows | R-pipeline (E3) |
| Q3 | Event outcome-in-window | "job change this year?" | R-4 anchor posterior for (event_class, window) | R-pipeline (E3) |
| Q4 | Undertaking election/outcome | "activity 2 months out" | activity ontology × muhurta scoring vs own chart × prashna (if cast) × fructification | weakest today |
| Q5 | Domain arc | "career next 5 years" | C1 waveform per domain + Q1 per major period | E3 |
| Q6 | Remedial | "what to do about X" | RM de-degenerated (F-007) + anchor mitigations + cost/effect | partial |
| Q7 | Interpretation | "what does my D9 Sun mean" | salience_v2-ranked signals + L0 bridge citations + verdict object | E1+E2 |
| Q8 | Compatibility | "this partnership?" | A7 chart-pair subject type | E5 |

**New requirements surfaced:** (i) **Period-Reading product** (Q1) — stored dasha-period dossiers (L3
ka_* extension: per MD/AD period × chart: lord dossier ref, activated promise refs, quality score) +
retrieval-time verdict composition; (ii) **Activity Ontology** (Q4) — L0 reference asset alongside R-1
(often the same event classes seen from the elective side; author them together in the R-1 sitting);
(iii) **Prashna chart-type build path** (Q4) — already planned as chart-type in the subsystem program;
promoted from deferred to E3-adjacent. Each MCP reasoning-unit tool declares which query classes it
serves; the readiness matrix becomes a living gate (a query class is GREEN only when its recipe's every
stage serves on prod).

### §10.3 — Learning-loop verdict: REDESIGN mechanics, RETAIN infrastructure

The native's stated mechanism — blind-predict at each LEL timestamp, compare vs actual, score, feed
upward — is correct and is NOT what is implemented. Current implementation: manual `retrodictive_match`
annotation (human, sighted, subjective) aggregated to a concordance fraction; no blind protocol, no
per-technique attribution, no false-alarm measurement. Keep: journal, MD5 holdout, honest-n, bootstrap
CIs, two-key gates, bounded modulation. Replace the scoring engine with five elements:

- **LL-1 Blind protocol.** Pre-event data cutoff (leakage firewall, proven in ph_pramana); generate
  ranked event-class predictions for each LEL event window; rank-aware hit scoring (was the actual event
  class in top-k, at what rank, at what posterior).
- **LL-2 Control windows.** Sample non-event windows per chart and score false alarms → precision AND
  recall; all skill measured against the base-rate null (M-3). Without this the loop rewards prophecy-spam.
- **LL-3 Ablation attribution.** Re-run retrodiction with each technique family disabled (Jaimini off /
  ashtakavarga off / nakshatra off / per dasha-system off) → marginal skill per family. The purest
  beyond-human learning organ: no practitioner can ablate their own intuition.
- **LL-4 Classical priors as Bayesian priors.** Technique weights initialize at native-ratified classical
  values; evidence moves them via hierarchical shrinkage (partial pooling across technique × event-class ×
  dasha-system cells). Tradition = prior, LEL = likelihood, posterior = served weights. Guards the n=1
  overfit (one life must not rewrite the shastra); family-chart LELs widen the corpus (M-5).
- **LL-5 Bounded versioned updates** flowing to exactly three sinks: L0 class-prior table (B1), R-4 lift
  calibrations, triangulation tradition-weights. Never to L1. Every update two-key (adhilepa), with
  reliability diagrams per cell retained as audit artifacts.

**E-wave impact:** E2.5 scope = LL-1…LL-5 (was R-5/R-6 alone); E3 gains the Period-Reading product (Q1)
and the Activity Ontology + prashna path (Q4); the R-1 native sitting now ratifies THREE tables: salience
class-priors + event ontology + activity ontology.

**§10.3 SUPERSEDED IN DETAIL by `MIMAMSA_V2_LEARNING_LAYER_DESIGN_v1_0.md` (2026-07-02)** — the full
from-scratch learning-layer design: source-reviewed keep/replace verdict on all 12 mi_* assets (~60%
retained incl. manifestation grammar, 3× divergence cap, journal loop, leakage firewall), five learnable
surfaces (S1 family weights, S2 lift calibrations, S3 per-chart dasha-system fitness, S4 manifestation
grammar, S5 tradition weights), four evidence loops by arrival speed (A retrodiction-now, B prashna-weeks,
C prospective-months, D resonance-QUARANTINED), null-anchored sharpness-aware scoring, analytic+ablation
attribution, shrinkage-not-gates, snapshot publication, portal ask-card loops, R1–R4 rollout. E2.5 ≡ its
Phase R1+R2.

*End of BEYOND_ACHARYA_GAP_ANALYSIS_AND_ENRICHMENT_ROADMAP v1.3 — native review requested on: (1) ONE
combined judgment sitting ratifying three tables — salience class-priors (§3.B1) + event ontology (§9.3
R-1) + activity ontology (§10.2); (2) §9+§10 redesign sign-off (R-pipeline, LL-1…LL-5 learning loop,
query-class taxonomy as the operational contract); (3) E-wave sequencing incl. E2.5; (4) E4 ranking.*
