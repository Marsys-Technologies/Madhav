---
artifact: BEYOND_ACHARYA_SUPPLEMENT_RSC
canonical_id: BEYOND_ACHARYA_SUPPLEMENT_RSC
version: 1.0
status: CURRENT — supplement to BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v1_0 (the master plan is NOT
  edited; this document ENHANCES it; §4 tells the implementer exactly what to merge into which wave)
created: 2026-07-02
author: Cowork (strategic workstream, Claude Fable 5) — for native Abhisek Mohanty
scope: >
  Three subjects from the strategic conversation of 2026-07-02: (1) the Ranking Doctrine — the ratified
  philosophy resolving "completeness without prescription," elaborated with its discovery organs and the
  complement pass; (2) a full review of the SALIENCE FABRIC across the engine (statistical + data-
  engineering + astrological lenses) with elevation proposals; (3) the CONSTANTS AUDIT for L3/L4/L5 —
  inventory, classification, and the elevation mechanism. Source-verified against writer code 2026-07-02.
relationship_to_master: >
  Targets MASTER PLAN v2.0 (the code-reconciled revision; wave codes unchanged). Master wins on
  sequencing; this document adds deliverables into W1/W2/W3/W4A/W5 and one new L0 asset
  (bg_formula_constants). Compatibility notes vs v2.0's reconciliation ledger: (a) §2.1's "one formula's
  pathology" — v2.0 C-corrections found TWO divergent salience formula sites (bo_laksana._compute_salience
  vs bodha_writers/formulas.py); the S-A…S-E/A-A…A-D elevations apply to the UNIFIED site v2.0 mandates;
  (b) v2.0's finding that the verification_certainty 0.778 cap is the true top-band strangler is
  COMPLEMENTARY to S-A (within-class percentiles make any such cap harmless to ranking); (c) the
  bg_formula_constants registry (C-1) is the same governance move as v2.0's 3-site embedded-weight
  unification — one constants surface, all consumers read it.
changelog:
  - v1.0 (2026-07-02): first version (written against master v2.0).
---

# SUPPLEMENT — RANKING DOCTRINE · SALIENCE FABRIC REVIEW · CONSTANTS ELEVATION

---

## §1 — THE RANKING DOCTRINE (ratifiable principle + its organs)

### §1.1 — Context: the native's design philosophy, affirmed

Two pillars of the instrument are correct and permanent: **(P1) deterministic completeness** — every
astrological quantity is pre-computed by code, never by the LLM, because LLM arithmetic errs silently and
compounding errors poison synthesis; and **(P2) no exclusion** — no parameter is withheld from the
synthesis surface, because a prescribed lens institutionalizes blind spots.

### §1.2 — The resolution of the prescription dilemma

The physical fact: attention is finite (context windows for machines, working memory for humans). A flat,
unranked corpus does not give the LLM "everything" — it gives it an arbitrary truncation plus its own
pretraining biases: an *uncontrolled, invisible, unauditable* ranking. The 17 MB domain-reading failure is
the empirical proof. Therefore the choice is never "prescription vs. open eyes"; it is "a ranking you
designed, versioned, and can correct — vs. a ranking the model improvises per call."

**THE DOCTRINE (for native ratification):**

> **Rank everything. Drop nothing. Hunt the tail.**
> Salience orders; it never filters (the native's standing rule, reaffirmed). The full corpus remains
> served and queryable. Discovery of significant factors OUTSIDE the ranking is guaranteed not by
> flatness but by dedicated organs that systematically search the tail — and by the fact that the ranking
> itself is a falsifiable, evidence-corrected object (L5 arrows), not a dogma.

### §1.3 — The five discovery organs (how the outside factor gets found)

1. **Specificity** (master plan, salience v2 term): statistically extreme configurations rise on rarity
   even when their class prior is humble.
2. **Structural elevation** (master plan, CGM): a low-class signal on a load-bearing dispositor path or
   convergence junction surfaces because of WHERE it sits, not what family it is.
3. **Contradiction surface** (master plan, verdict object): evidence disagreeing with the top-ranked
   verdict ships WITH the verdict, by construction — the reading carries its own dissent.
4. **Empirical promotion** (master plan, L5): retrodiction + ablation detect predictive skill in
   low-prior families; the L5→L2 arrow re-weights them; the L5→L0 graduation arrow admits genuinely new
   factors to the canon with falsifier receipts. The ranking is a hypothesis under permanent test.
5. **The COMPLEMENT PASS (NEW — this document's addition).** A retrieval-layer product: synthesize over
   ONLY the tail (all signals below the head cutoff, head deliberately withheld), one question: *"what
   does the tail say that the head does not?"* Output: a divergence memo (claims found only in the tail,
   each cited), attached to the verdict object as `tail_divergence`. Runs (a) on demand, (b) on a sampling
   cadence per domain, (c) always during retrodiction (a tail-only retrodiction run measures whether the
   tail carries INDEPENDENT predictive skill — the empirical answer to "are we missing something outside
   the ranking?"). Cost: one extra synthesis call. No practitioner in history could enumerate their own
   tail; this instrument can — this is a beyond-acharya organ in the fullest sense.

### §1.4 — The attention-budget protocol (serving contract)

Every synthesis call allocates its context budget explicitly, e.g. default 70/20/10: **70% ranked head**
(salience v2 order) · **20% dissent** (contradictions + anomalies + ayanamsha-fragile flags) · **10% tail
sample** (stratified random from below the cutoff — a standing exploration term, ε-greedy attention).
The split is itself a versioned constant (→ §3 registry), tunable per query class, L5-evaluable (does a
larger tail share ever change verdicts? measurable!). This converts "how much should the model see beyond
the obvious" from vibes into a governed, tested parameter.

---

## §2 — SALIENCE FABRIC REVIEW (end-to-end; three lenses)

### §2.1 — Where salience lives and flows (the fabric, traced in code)

`bo_laksana._compute_salience` (v1 formula) → `computed_salience` + `signature_tier` on every MSR signal
→ consumed by: CGM node `strength_score` (bo_bimba; live nodes carry the degenerate 2.326672 constant),
CGM edge `computed_strength` (0.581668 constants observed), CDLM convergence sums (`convergence_score`,
`salience_weighted_sum` — raw sums over signal populations), question-lens rankings, RM remedy
`resonance_score` (0.28 degenerate, F-007), ka_yojaka activation weights (pagerank×cdlm with 0.5
fallbacks), ka_sangam `convergence_score` (and `confidence_score` MIRRORS it — one number wearing two
names), L4 G-LADDER (floor/cap heuristic over convergence), L5 scoring (inherits everything upstream).
**One formula's pathology propagates through six layers of consumers — which is also the good news: fixing
the fabric at its source (salience v2) heals most of the tree.**

### §2.2 — Statistical critique (beyond what the master plan already fixes)

The master plan (W2) already adds: class priors, varga weights, specificity, hierarchical aggregation,
activation boost, live signature_tier, degeneracy gates. This review finds five FURTHER statistical
defects the master plan does not yet name:

- **S-A. No within-class normalization.** Cross-class comparability is asserted, not constructed. Raw
  multiplicative scores from different families have different natural scales. Elevation: compute
  salience per family, then store BOTH `computed_salience` (absolute) and `salience_pctl_in_class`
  (percentile within its family for this chart); cross-class ranking uses
  `class_prior × f(percentile)` — priors decide BETWEEN families, percentiles decide WITHIN. Ties become
  impossible by construction; distribution gates become trivial.
- **S-B. Volume masquerading as convergence.** CDLM `convergence_count: 11,970` for career sums a
  population dominated by one family's multiplicity — the sum measures VOLUME, not independent evidence.
  Elevation: **effective-evidence correction** — de-duplicate by family clusters before summing
  (diminishing returns: family contribution ∝ log(1+n_family) or capped by aggregation composites from
  W2); report `effective_evidence_count` alongside raw counts. Applies to CDLM cells, bo_sangati
  concordance, ka_sangam window scores.
- **S-C. Silent 0.5/1.0 defaults contaminate.** `cgm_weight.get(…, 0.5)`, `cdlm_strength.get(…, 0.5)`,
  `orb=1.0`, `bindus=4` — fabricated neutrals flow into products indistinguishable from measured values
  (the canonical-or-floor rule violated in spirit). Elevation: NULL-propagation discipline — a missing
  input yields a NULL component + a `salience_inputs_complete` flag; consumers may impute, but imputation
  is VISIBLE. (Same class as the mi_pariksha catch-all deletion in MIMAMSA_V2.)
- **S-D. No uncertainty dimension.** A salience score from complete inputs with 5/5 ayanamsha agreement
  and one from imputed inputs with 2/5 agreement serve identically. Elevation: `salience_robustness`
  (already partially planned via B5 ensemble) + `inputs_complete` served WITH the score; the verdict
  object weights by it.
- **S-E. Build-time staleness by design.** Salience is computed at build; dasha-activation is temporal.
  The master plan's `dasha_activation_boost` must be applied AT QUERY TIME (stored: static salience;
  served: static × activation(t)) — make this explicit in W2/W3 so nobody bakes activation into the
  stored column (it would go stale the day the dasha changes).

### §2.3 — Astrological critique (the most important lens; four missing judgment terms)

Salience v2 (master plan) makes the ranking know WHAT a signal is. Classical judgment additionally asks
four questions the formula still would not ask:

- **A-A. Kāraka congruence.** A Saturn signal bearing on CAREER (Saturn = karma-kāraka, 10th-lord
  contexts) is not the same weight as a Saturn signal bearing on PROGENY (Jupiter's domain). Elevation:
  `karaka_congruence` multiplier — signal's graha × domain of the question, from a small native-ratified
  table (graha × domain affinity, classically cited). Applied at query time (domain known only then).
- **A-B. Bala gating.** Classical rule: a yoga delivers in proportion to its constituents' strength
  (śadbala floors; BPHS phala chapters qualify results by bala throughout). A magnificent raja-yoga of
  two debilitated, combust planets is a PROMISE ON PAPER. Elevation: `bala_gate` modifier — composite
  constituent strength (already in L1) modulates yoga-class signals; weak-bala yogas rank as
  "present-but-enfeebled" (a distinct, served state — astrologically honest and more interesting than
  either hiding or full-ranking them).
- **A-C. Functional nature context.** A Saturn signal in a Libra-lagna chart (yogakāraka) ≠ the same
  signal for Aries lagna. L1 computes functional benefic/malefic per lagna; salience v1/v2 never consults
  it. Elevation: `functional_context` term from the existing `ga_structural` functional-nature facts.
- **A-D. Query-time varga affinity.** A D10 signal weighs more for a career question, D9 for marriage,
  D7 for progeny — the varga weight vector should have a DOMAIN-CONDITIONED variant applied at query
  time (stored varga weight stays domain-neutral). Small table, classical, native-ratified in the W1
  sitting alongside the class priors.

**Fold:** S-A…S-D + A-A…A-D are all salience-v2-adjacent → merge into the W2B L2 regeneration brief
(stored terms) and the W3 serving brief (query-time terms: activation, karaka congruence, varga
affinity). The W1 sitting gains two SMALL extra tables: graha×domain affinity + domain×varga affinity.

---

## §3 — THE CONSTANTS AUDIT (L3/L4/L5; inventory → classification → elevation)

### §3.1 — Inventory (source-verified; representative, not exhaustive — the harness in §3.3 completes it)

| Constant | Location | Value | Class |
|---|---|---|---|
| Combustion orb | `ka_vighnakara._COMBUSTION_ORB_DEG` | **6.0° flat** | **JUDGMENT-MISCODED** — classical orbs are per-graha (Moon 12°, Mars 17°, Mercury 14°/12°R, Jupiter 11°, Venus 10°/8°R, Saturn 15°); a flat 6° matches no śāstra; ALSO duplicates/diverges from L1 ga_condition combustion — two combustion truths in one system. |
| Obstruction severity | `ka_vighnakara._SEVERITY_THRESHOLDS` | 0.70/0.40 | JUDGMENT (uncited) |
| Convergence horizon / budgets | `ka_sangam` | 7yr, 200 predicates, 40k rows, 100yr lifetime | ENGINEERING (fine; document) |
| Dasha predicate flag | `ka_sangam` | `dasha_score > 0.3` | JUDGMENT (uncited) |
| Confidence = convergence | `ka_sangam._insert_windows` | `confidence_score` mirrors `convergence_score` | **STRUCTURAL CONFLATION** — two semantically different quantities, one number; retired by Anchor v2 (posterior ≠ convergence), but the L3 window table keeps the mirror → fix in W4A. |
| G-LADDER family | `ph_nimitta` | 0.5 floor, 0.50+0.05n, 0.80 cap, 0.80+0.04r, ±0.10 | JUDGMENT — retired by master plan W4B (Anchor v2). |
| Magnitude tiers | `ph_nimitta.compute_magnitude` | rarity/10yr; 0.60/0.40/0.20 | JUDGMENT (uncited) |
| Ayanamsha robustness default | `ph_nimitta` | 3 (of 5) | SILENT DEFAULT (S-C class) |
| Timing/magnitude scoring | `mi_pramana` | center-decay; adjacency 0.5 steps | JUDGMENT — replaced by MIMAMSA_V2 §5 (null-anchored). |
| Retrodictive mapping | `l5_calibration_substrate` | yes=1.0 / partial=0.5 / no=0.0 | JUDGMENT — superseded by MIMAMSA_V2 adjudication. |
| Channel propensity priors | `mi_sambandha._PRIOR_PROPENSITIES` | e.g. career 0.40/0.35/0.25 | JUDGMENT (uncited, plausible) — retained as Dirichlet smoothing base per MIMAMSA_V2; needs ratification. |
| Promotion gate / divergence cap | `mi_gunanaka` | n≥10; 3× | gate→shrinkage (MIMAMSA_V2); 3× cap KEPT (ratify). |
| Holdout partition | `mi_jivanaghatana` | MD5 mod 10 = 20% | ENGINEERING (fine; document) |
| Corroboration levels | `bo_laksana` (L2, for completeness) | 5 vs 2 | JUDGMENT (uncited) |
| L2 fabric constants | `bo_laksana` | _DIGNITY_SCORE, _HOUSE_WEIGHT, _av_mult steps | JUDGMENT — house weights & dignity scores are ratifiable astrology; subsumed into salience v2 but the VALUES still need native sign-off. |

### §3.2 — Classification rule (the governance insight)

Constants divide into four classes with different fates: **CLASSICAL** (per-graha combustion orbs, dasha
years — cite the śāstra, encode exactly, never tune); **NATIVE-JUDGMENT** (house weights, severity
thresholds, channel priors, magnitude tiers — must be RATIFIED, versioned, and L5-calibratable within
bounds); **ENGINEERING** (budgets, horizons, holdout fractions — document, keep in code);
**STRUCTURAL-CONFLATIONS** (confidence=convergence; flat combustion orb duplicating L1 — these are BUGS,
not constants; fix outright). The current codebase's core defect: all four classes live undifferentiated
as Python literals — invisible to governance, invisible to L5, and (per the combustion example) able to
contradict both the śāstra and the system's own L1.

### §3.3 — Elevation mechanism (what the master plan lacks; three additions)

- **C-1. `bg_formula_constants` — NEW L0 asset (the constants registry).** Table
  `brahma_formula_constants`: `(constant_id, consumer_assets[], value_jsonb, class
  [classical|native_judgment|engineering], citation_or_ratification, calibratable bool, bounds,
  version)`. ALL classical + judgment constants extracted from code to this table; writers read it (as
  they will read `bg_class_priors` — same pattern, one governance surface). Effect: every judgment number
  in the engine becomes visible, versioned, citable, and (where flagged) L5-adjustable within bounds.
  Global scope, upsert idempotency, trivial count_sql.
- **C-2. Ratification batch → the W1 sitting gains table #4:** the NATIVE-JUDGMENT constants (one sheet:
  current value, proposed classical correction where applicable — e.g. per-graha combustion orbs — and
  bounds). Structural conflations (confidence-mirror, flat-orb duplication) go to W4A as bug fixes, not
  ratification items.
- **C-3. Sensitivity harness — W5 deliverable.** Vary each registry constant across its bounds; measure
  output stability (top-k composition, verdicts, anchor posteriors) on two charts. Constants ranked by
  output sensitivity: HIGH-sensitivity constants get ratification priority and tight bounds;
  LOW-sensitivity ones stop mattering (and the doctrine gains empirical humility: we KNOW which knobs the
  instrument actually turns on). No human practice has ever sensitivity-tested its own weights — a
  beyond-acharya governance organ, nearly free once retrodiction exists.

### §3.4 — Already addressed by the master plan (no action here)

G-LADDER retirement (W4B) · n-gates→shrinkage + scoring replacement (W5) · RM 0.28 degeneracy (F-007,
W2/W5) · class priors externalized (`bg_class_priors`, W2) · degenerate-distribution gates (traps
register) · catch-all attribution deletion (W5).

---

## §4 — MASTER-PLAN MERGE MAP (for the implementation conversation)

| Master wave | ADD from this supplement |
|---|---|
| **W1 sitting** | +Table 4: judgment-constants ratification sheet (§3.2/C-2); +two small affinity tables: graha×domain (A-A), domain×varga (A-D); +Doctrine ratification (§1.2). |
| **W2A (L0 seeds)** | +`bg_formula_constants` asset (C-1) with migration + registry row; classical combustion orbs seeded per śāstra. |
| **W2B (L2 regen)** | +S-A within-class percentiles (`salience_pctl_in_class`); +S-C NULL-propagation / `salience_inputs_complete`; +S-D robustness column; +A-B bala_gate; +A-C functional_context; +S-B effective-evidence correction in CDLM/sangati aggregates. |
| **W3 (serving)** | +§1.4 attention-budget protocol (70/20/10, registry-governed); +§1.3.5 complement pass (`tail_divergence` in the verdict object); +query-time terms: activation boost (S-E), karaka congruence (A-A), varga affinity (A-D). |
| **W4A (kala)** | +fix confidence=convergence conflation; +ka_vighnakara reads combustion from L1/ga_condition (single truth) with per-graha orbs from the registry. |
| **W5 (learning)** | +C-3 sensitivity harness; +tail-only retrodiction runs (does the tail carry independent skill — the doctrine's own falsifier). |

*End of BEYOND_ACHARYA_SUPPLEMENT_RANKING_SALIENCE_CONSTANTS v1.0 — native review requested on: (1) the
Doctrine (§1.2) for ratification; (2) the four astrological terms (§2.3) — especially bala-gating's
"present-but-enfeebled" served state; (3) the constants classification + per-graha combustion correction
(§3); (4) the merge map (§4) as instructions to the implementation conversation.*
