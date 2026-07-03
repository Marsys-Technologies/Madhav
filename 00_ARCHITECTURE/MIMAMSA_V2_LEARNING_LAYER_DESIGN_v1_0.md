---
artifact: MIMAMSA_V2_LEARNING_LAYER_DESIGN
canonical_id: MIMAMSA_V2_LEARNING_LAYER_DESIGN
version: 1.0
status: DRAFT-FOR-NATIVE-REVIEW
created: 2026-07-02
author: Cowork (strategic workstream, Claude Fable 5) — for native Abhisek Mohanty
parent: BEYOND_ACHARYA_GAP_ANALYSIS_AND_ENRICHMENT_ROADMAP v1.3 (§9.2, §10.3)
supersedes: the L5 scoring/learning MECHANICS of the mi_* v1 build (the 12-asset skeleton, journal loop,
  leakage firewall, and manifestation-grammar concept are RETAINED — see §1 verdict table)
method: full from-scratch design, grounded in a source-code review of all 12 mi_* writers (headers +
  scoring functions verbatim), the LEL v1.7 corpus, portal/MCP usage reality, and the §9 R-pipeline.
design_criteria: practical to implement · aligned with real portal usage · deterministic (no LLM in the
  scoring path, D-1) · logically sound (proper scoring, honest nulls) · astrologically sound (classical
  priors as the starting point; learning adjusts weights, never rewrites shastra)
changelog:
  - v1.0 (2026-07-02): first full design.
---

# MĪMĀṂSĀ v2 — THE LEARNING LAYER, DESIGNED FROM SCRATCH

> **Design thesis.** A learning layer for a Jyotish instrument has exactly one legitimate job: **move
> probability mass between techniques, calibrations, and expression-channels in proportion to demonstrated
> predictive skill on this native's (and later this corpus's) lived outcomes — starting from classical
> priors and never leaving their gravitational field without overwhelming evidence.** Everything below
> serves that sentence. The existing v1 build got the SKELETON right and the EVIDENCE ENGINE wrong: it
> waits for prospective outcomes that arrive at n≈2/year, scores them against stub falsifiers and binary
> domain matches, and attributes credit through fabricated 0.5 defaults. v2 keeps the skeleton, replaces
> the engine, and wires the loop into how the portal is actually used.

---

## §1 — VERDICT ON THE EXISTING IMPLEMENTATION (reviewed, not dismissed)

| v1 asset | Purpose | Verdict | Why |
|---|---|---|---|
| mi_jivanaghatana | LEL vault + MD5 holdout + leakage firewall | **KEEP** | Correct and disciplined. The 20% held-out partition + admissibility flags are exactly right. |
| mi_bhavisya | Freeze L4 predictions immutably | **KEEP** (input upgraded) | Freezing claims before scoring is correct; its INPUT becomes R-4 anchors v2. |
| mi_pramana | Match + score + reliability | **REPLACE ENGINE** | Multi-dim scoring idea sound; execution broken: falsifier stub =1.0 always, manifestation stub =0.5, domain binary, timing has NO window-width penalty (a 10-yr window scores like a 3-month one — sharpness never rewarded), no null baseline, no control windows. |
| mi_pariksha | Attribution + neg-control + discovery | **REPLACE attribution / KEEP harness+discovery** | Catch-all `fam_graha_natal` fallback with fabricated 0.5 strengths poisons credit assignment; neg-control substep + discovery miner retained. |
| mi_gunanaka | Learned multipliers, n≥10 gates, 3× divergence cap | **KEEP cap, REPLACE gates** | The 3× classical-divergence cap is excellent astrological governance. Hard n-gates → hierarchical shrinkage (usable estimates from n=3, honest CIs). |
| mi_adhilepa | Overlay rows (signal/fact/convergence/anchor) + load-bearing map | **KEEP** | Right mechanism (non-destructive overlays; L1 never touched). Wire it — currently inert. |
| mi_sambandha | Manifestation grammar (per-native channel propensity) | **KEEP + ELEVATE** | Genuinely novel and astrologically deep: the same activation manifests differently per nativity; learning the native's expression channels IS classical judgment (acharyas do this intuitively across a client relationship). |
| mi_kula | Signal-family registry w/ prior weights + neg-control battery | **KEEP, UNIFY** | Correct home for classical priors — MUST become one substance with the B1 class-prior L0 table (today they would drift apart). |
| mi_darshana | Insight units + embeddings | KEEP | Serving surface, unaffected. |
| mi_seva / mi_abhilekha | Serve-time apply + journal write / journal re-sync | **KEEP + WIRE** | The portal loop already designed — surface→journal→native answers→lifecycle update. It lacks UI wiring and auto-triggers, not design. |
| mi_vistara | Export-integrity ledger | KEEP | Disclosure governance, unaffected. |

**Net verdict: ~60% retained, and the retained parts are the hard-to-invent parts. What v1 lacks is
(a) an evidence GENERATOR (it can only score predictions that were prospectively made — none exist),
(b) honest SCORING (stubs, no nulls, no sharpness), (c) honest ATTRIBUTION, (d) the portal LOOP wiring,
(e) statistical treatment fit for small n.**

---

## §2 — WHAT IS LEARNED (the five learnable surfaces — and what is NEVER learned)

1. **S1 Technique/family weights** — the multipliers on signal families (unified mi_kula ≡ B1 L0
   class-prior table). *Question answered: which evidence families actually predict for this corpus?*
2. **S2 Lift calibrations** — mapping functions from R-4's promise/activation/trigger lift scores to
   empirical probability lifts (reliability-curve fitting per lift). *Question: when the system says 2×
   base rate, is it 2×?*
3. **S3 Dasha-system fitness per chart** — relative timing skill of the 7 dasha systems for THIS
   nativity. Classically grounded: the shastra itself holds that different dashas apply per applicability
   conditions; v2 measures which system this life actually obeys. *A first-class astrological discovery
   surface, unique to machine practice.*
4. **S4 Manifestation grammar per chart** (elevated from v1 mi_sambandha) — the native's expression
   channels: given a confirmed activation, through which channel did it manifest (career/somatic/
   relational/psychological/material)? Learned as channel propensities per activation class.
5. **S5 Tradition weights for triangulation** (B4) — Parashari/Jaimini/KP/Tajika concordance weighting.

**Never learned (constitutionally fixed):** L1 facts; classical rule CONTENT (a rule's text/conditions
never change — only its WEIGHT); the salience formula STRUCTURE (weights move, terms don't, without a
versioned native-ratified formula bump); anything via LLM (D-1: the scoring path is 100% deterministic).

---

## §3 — THE EVIDENCE ENGINE (four loops, ordered by arrival speed)

**Loop A — Retrodiction (arrives NOW; n≈57 + controls).** The blind backtest over the LEL:
- For each admissible LEL event E at date T: freeze a data-cutoff at T−δ (δ = event lead time, default 90d);
  run the R-pipeline (promise→activation→trigger) on strictly pre-cutoff data; emit the top-k ranked
  (event_class, window, posterior) predictions for the horizon containing T.
- **Control windows:** for each event, sample ≥3 same-length windows from the same chart where NO
  admissible event of any class occurred (stratified by age band); run the identical generation. Hits in
  control windows = false alarms. Without this, recall is rewarded and precision is fiction.
- Adjudicate (§4), score (§5), attribute (§6). Leakage firewall: generation code receives a connection
  whose `chart_facts`/`chart_dashas` views are date-filtered (the ph_pramana rectification pattern,
  generalized). Held-out 20% partition (mi_jivanaghatana) is never used for weight updates — it is the
  final exam only.
- **Ablation harness:** rerun Loop A with each technique family masked (Jaimini off / ashtakavarga off /
  nakshatra off / each dasha system solo). Marginal skill per family = the ablation delta. This is the
  instrument's deepest beyond-human learning organ and feeds S1/S3 directly.

**Loop B — Prashna/undertaking outcomes (arrives in WEEKS; the fastest prospective loop).** Every Q4
(undertaking/election) verdict served by the portal auto-schedules a follow-up at its fructification
date; the portal asks the native the outcome (one-tap: happened-as-judged / partial / contrary / n-a).
Highest-velocity honest feedback the product can generate; also the least leakage-prone (future events).

**Loop C — Prospective anchors (arrives in MONTHS–YEARS; the headline).** R-4 anchors freeze at
publication (mi_bhavisya). When a window closes: auto-adjudicate against new LEL entries; where the LEL
is silent, the journal loop (mi_seva → portal ask-card → mi_abhilekha resync) asks the native directly.
Prospective results are the only ones reported as the instrument's headline skill (retrodiction is
labeled retrodictive, always).

**Loop D — Reading resonance (continuous; QUARANTINED).** Thumbs/notes on interpretive readings are
captured but **constitutionally barred from moving S1–S3/S5**. Resonance may only tune S4 presentation
emphasis. Rationale: resonance measures agreeableness, not truth — the sycophancy trap for any
learning-from-feedback system; predictions are scored against events, never against approval.

---

## §4 — ADJUDICATION (deterministic matching of claims to reality)

A frozen claim is `{chart, event_class, window, magnitude_floor, posterior, falsifier, lift_vector,
data_cutoff_sha}`. Adjudication against the LEL (and journal answers):

- **CONFIRMED** — an admissible LEL event of the claim's event_class (per the R-1 ontology's matching
  rules, which define class equivalence + adjacency) with magnitude ≥ floor falls inside the window.
- **PARTIAL** — adjacent event_class (ontology-defined adjacency, e.g. `career_elevation` ↔
  `career_change`) OR magnitude one tier below floor OR event within window ±20% of width.
- **REFUTED** — falsifier condition met: window expired with no qualifying or adjacent event, AND the
  LEL for that period is attested-complete (the native has marked the period as curated — else →
  UNRESOLVED, never silently REFUTED; an un-curated log must not count as a miss).
- **EXPIRED/UNRESOLVED** — window closed, LEL not attested; queued to the journal ask-card.
- Control windows adjudicate symmetrically: a claim fired in a control window = FALSE_ALARM.

All matching rules live in the R-1 event ontology (machine-decidable, versioned). The v1 falsifier stub
is deleted; falsifiers become structured `{event_class, magnitude_floor, window, attestation_required}`
objects — P-4 closed by construction.

## §5 — SCORING (proper, null-anchored, sharpness-aware)

- **Primary: Brier vs the climatology null.** Every scored cell reports `skill = 1 − Brier_model /
  Brier_null` where the null predicts the base rate (from R-1 age-band priors) for every window. A
  technique earns weight only by BEATING base rates — the weather-forecasting standard.
- **Sharpness enters through the null:** a wide window has a high base rate, so beating it is worth
  little; a narrow window has a tiny base rate, so a hit is worth much. This replaces v1's
  center-distance timing score (which rewarded width) with no extra machinery.
- **Rank-aware retrodiction credit:** for Loop A, the actual event's class must appear in the top-k;
  credit decays with rank (1/log2(rank+1)); posterior calibration scored by reliability curve (ECE — v1's
  reliability substep retained).
- **Magnitude adjacency** retained from v1 (it was sound). Domain binary match replaced by
  ontology-adjacency (§4).
- **Cell structure:** technique_family × event_class × dasha_system × ayanamsha (× chart, once
  multi-chart). Sparse by construction → §6 shrinkage. Bootstrap CIs (v1) retained on every cell.

## §6 — ATTRIBUTION & THE UPDATE RULE

- **Analytic attribution first:** R-4's posterior is a product of named lifts, each lift a sum of named
  technique contributions (the lift_vector frozen with the claim). Credit/blame flows down the vector
  arithmetically — no fabricated defaults; the v1 catch-all fallback is deleted. Claims with empty
  vectors are excluded from attribution (never defaulted).
- **Ablation attribution second:** Loop A ablation deltas cross-check the analytic shares; divergence
  between the two flags interaction effects → discovery queue (mi_pariksha discovery, retained).
- **Hierarchical shrinkage replaces n-gates:** cell posterior = weighted blend of cell evidence and
  parent-cell evidence (family→class→global), weights ∝ n. At n=0 the posterior IS the classical prior
  (mi_kula/B1) — the system degrades to tradition, never to silence or noise.
- **Update rule (S1/S3/S5):** multiplicative, bounded per run (±10%), bounded cumulatively (v1's 3×
  divergence cap retained), two-key (adhilepa: system proposes, native co-signs), published as a
  **versioned calibration snapshot**; serving reads the latest PUBLISHED snapshot only; rollback = point
  at prior snapshot. Reliability diagrams per cell ship with every snapshot as audit artifacts.
- **S2 update:** isotonic-regression reliability fit per lift (deterministic), refit per snapshot.
- **S4 update:** channel-propensity counts with Dirichlet smoothing from v1's seeded priors (v1's prior
  table retained as the smoothing base).

## §7 — PORTAL INTEGRATION (how learning meets actual usage)

- **Ask-cards:** when any claim's window closes unresolved, the portal surfaces a one-tap adjudication
  card (happened / partially / didn't / can't say) — mi_seva journal write + mi_abhilekha resync already
  implement the plumbing; v2 adds the trigger scan (daily cron over closed windows) + the UI card.
- **LEL curation prompts:** monthly "attest this period" card (enables honest REFUTED per §4); event
  entry through a structured form that captures event_class + magnitude per the R-1 ontology (adjudication
  quality begins at intake).
- **Prashna follow-ups:** Q4 verdicts auto-create a scheduled ask at fructification date (Loop B).
- **Chart onboarding:** each new chart with an LEL (family first — M-5) multiplies the retrodiction
  corpus and starts populating cross-chart cells; cross-chart event consistency checks (one native's
  marriage appears in relatives' charts) enter as consistency evidence, labeled as such.
- **Transparency surface:** the MCP/portal exposes `query_calibration` v2 — per-cell skill, n, CI, last
  snapshot — so any consuming LLM can weight its own synthesis by demonstrated technique skill. The
  learning layer is not backstage machinery; it is a served product ("this instrument knows what it is
  good at").

## §8 — ASTROLOGICAL SOUNDNESS GUARANTEES

1. **Tradition is the prior** — at zero evidence the instrument IS classical astrology (native-ratified
   weights); evidence bends it slowly and boundedly (3× cap); the shastra's content is never edited by data.
2. **Per-nativity learning is classical** — S3 (which dasha this life obeys) and S4 (how activations
   express) formalize what an acharya learns across a long client relationship; v2 does it with receipts.
3. **No self-grading** — the LLM never scores itself; adjudication is deterministic against a
   native-curated event log; resonance is quarantined (Loop D).
4. **Falsifiability is structural** — every claim carries a machine-decidable falsifier at freeze time;
   the ethical frame (calibrated, falsifiable, disclosed) is enforced by schema, not policy.

## §9 — ROLLOUT

- **Phase R1 (needs only existing data):** §4 adjudication rules + §5 null-anchored scoring + Loop A
  retrodiction generator + control windows, on the 57-event LEL (45 train / 12 held-out). Depends on:
  E0 serving-truth, DEFECT-001 MSR rebuild, R-1 event ontology (native sitting). Deliverable: the first
  honest skill table — which technique families beat base rates for the native.
- **Phase R2:** shrinkage engine + analytic attribution (requires R-4 lift vectors → E3) + ablation
  harness + first calibration snapshot published through adhilepa two-key.
- **Phase R3:** portal loops (ask-cards, attestation, prashna follow-ups) + S4 grammar learning live.
- **Phase R4:** multi-chart corpus (family LELs), cross-chart cells, S3 per-chart dasha fitness served.

## §10 — ACCEPTANCE (the layer is REAL when)

1. A retrodiction run on 482012f1 produces a per-family skill table vs null with CIs, from a leakage-
   audited pipeline, reproducible bit-for-bit from `(LEL version, snapshot version, code SHA)`.
2. At least one technique family demonstrably beats the null on the held-out partition — or the honest
   finding that none do is published with the same prominence (the instrument's integrity claim).
3. A closed prediction window converts to an adjudicated outcome within 7 days ≥80% of the time (portal
   loop health).
4. A published calibration snapshot changes served weights, visibly and reversibly, with the native's
   co-signature on record.
5. `query_calibration` serves real cells to the MCP — and a consuming LLM's reading demonstrably differs
   when calibration says a family is weak for this chart.

*End of MIMAMSA_V2_LEARNING_LAYER_DESIGN v1.0 — native review requested on: (1) §1 keep/replace verdicts;
(2) §2 the five learnable surfaces (esp. S3 dasha-fitness as a first-class product); (3) §3 Loop D
quarantine (resonance never moves predictive weights); (4) §4 REFUTED-requires-attestation rule; (5) §9
phasing. On approval, R1 becomes a CLAUDECODE brief.*
