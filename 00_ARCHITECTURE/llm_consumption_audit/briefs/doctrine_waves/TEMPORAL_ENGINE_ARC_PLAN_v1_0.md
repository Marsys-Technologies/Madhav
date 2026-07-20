---
artifact: TEMPORAL_ENGINE_ARC_PLAN
type: ARC PLAN (governs the D-4a → D-5 → D-4b sequence; briefs are cut from this document)
version: 1.0
status: RATIFIED — native-confirmed 2026-07-19 (D-4a conductor session; frontmatter was stale —
  the plan was approved in the 2026-07-19 Cowork session but the status stamp was never bumped
  after ratification, per CLAUDE.md B.8 versioning discipline). Briefs BRIEF_D4A.md/BRIEF_D4B.md/
  BRIEF_D5.md are authored and operative.
authored_by: Fable 5 (Cowork) with the native, 2026-07-19
supersedes_in_part: BRIEF_D4.md v2.0's monolithic lane map — its lanes are REDISTRIBUTED across
  this arc per the native-ratified ordering decision (2026-07-19: "engine before one-shot
  calibration; harness before engine; prospective clock starts immediately"). BRIEF_D4 v2.0
  remains the content source for the redistributed lanes.
governing: CONDUCTOR_PROTOCOL.md · DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md · MACRO_PLAN_v2_0.md
  (Ethical Framework + Learning Layer) · DR-10/11/12/13 (ratified) · DR-14/15/16 (drafted herein)
---

# Temporal Engine Arc — D-4a (Measurement Foundry) → D-5 (Gochara-Chitra) → D-4b (Calibration Ignition)

## §0 — The vision this arc serves (native's statement, formalized)

The cosmos continuously generates configurations — grahas moving through signs, houses,
nakshatras, kakṣyās, read differently by different systems. The instrument must, RELATIVE TO A
NATAL CHART, identify the subset of configurations that crosses a confidence threshold for a
given event-class — auspicious AND inauspicious — and answer four questions as views over ONE
object, the per-chart per-event-class intensity function λ_e(t | chart):

1. RETRODICTION — score past events against λ (the LEL harness).
2. ACTIVATION — "when will X likely happen?" → windows where λ_X peaks.
3. FORECAST — "what is likely in window T?" → all e with λ_e(T) above threshold, signed.
4. ELECTION/AVOIDANCE — "when should I act / not act?" → argmax(λ_favorable − λ_adverse),
   and suppression windows served as first-class answers ("likely to NOT happen/succeed").

Deep natal understanding is the filter that makes this tractable: the chart defines a sparse
RESONANCE MAP; the sky's millions of permutations are projected onto it, not enumerated.

**Classical anchor (§J framing):** the Sarvatobhadra Chakra is the tradition's manual build of
exactly this engine — transits streamed through a nakshatra grid against natal points, vedhas
read off. Currently a stub in L1 (CR-21). D-5 is its computational completion, alongside the
dvi-pramāṇa dictum (daśā promise × gochara delivery) generalized to the DR-14 plurality.

## §1 — Why this ordering (decision record, native-ratified 2026-07-19)

1. **The C-2 backfill is one-shot.** Scoring 57 LEL events into permanent `mimamsa_outcome_record`
   rows against curves we intend to replace would stamp L5's first outcomes on an obsolete
   kernel. Calibration must follow the engine. (Native's argument — decisive.)
2. **Engines built without a measurement harness score red.** D-3's kernel was verified 5× for
   mechanical correctness and scored below a shuffled control on first contact with reality.
   The D-5 engine is 10× that surface area. It must be developed TEST-FIRST against a working
   harness, every lane carrying a mini-retrodiction acceptance check. Harness precedes engine.
   (Fable's argument — decisive.)
3. **The prospective ledger accrues value in wall-clock time.** Every month it doesn't run is
   outcome data lost forever. It starts in D-4a, attribution improves later. (Joint.)

Hence: measurement infrastructure → engine → calibration. Wave naming: the engine wave is
**D-5** (not "D-3.5" — chronology stays monotonic); BRIEF_D4 v2.0 splits into **D-4a/D-4b**.
`wave_sequence` becomes [... D-3, D-4a, D-5, D-4b]; DR-12's bakeoff adjudication is explicitly
DEFERRED to D-4b (recorded so no one reads D-4a's dry-run as the ruling).

## §2 — Arc overview

| Wave | Name | Builds | Gate proves | Size |
|---|---|---|---|---|
| D-4a | Measurement Foundry | substrate repair, shape-aware matcher, event ontology, controls, CRPS harness, prospective ledger LIVE | "we can measure any timing model honestly" | small–medium |
| D-5 | Gochara-Chitra | resonance map, configuration grammar, multi-system superposition, forward sweep, adverse symmetry, Sarvatobhadra | "the engine generates signed, grounded, dated windows — and was measured throughout construction" | large |
| D-4b | Calibration Ignition + Grand Bakeoff | DR-12 adjudication over full contender set, one-shot backfill, hierarchical calibration, remedy-leverage, retrodiction surface, campaign close | "the data picked the model; L5 is fed; confidence is earned" | medium |

---

## §3 — D-4a: Measurement Foundry (lanes cut from BRIEF_D4 v2.0)

**A-0 — Serving-substrate repair** (= v2.0 Lane C-0 verbatim, horizon amended per §10 Q3):
CR-109 cardinality (full-span **birth → birth+100y** — serve every period the dasha table
holds; FIX-COV worktree as starting point), CR-110 double-spine (verify-first), CR-111
convergence join (verify-first), D-3 per-event artifact rescue, canonical_faces bookkeeping.

**A-1 — Shape-aware matcher + LEL v2** (= v2.0 Lane C-1): CR-47 root fix; DR-13 event shapes
(point/interval/chain, overlap scoring, confidence-scaled tolerance); LEL schema v2 additive
migration; windfall interval reclassification applied; native questionnaire answers ingested
when returned (firewall per BRIEF_D4 §7/§8 notes); leverage_index false-empty (carried #1).

**A-2 — Canonical event ontology** (= v2.0 Lane C-3, elevated): event-class taxonomy with STABLE
IDs shared by LEL classes, evidence sets, and future λ_e curves — this is the vision's "e".
Event-class-specific evidence (gain ≠ loss); non-discriminating self-reporting; kill-switch
release criteria as data. Ontology doc is a first-class artifact other waves import.
**Each event-class carries a canonical TEMPORAL SHAPE** (native doctrine, 2026-07-18 discussion
→ DR-13): `point` (birth, death, marriage ceremony), `interval` with a typical-duration prior
(windfall payment-flow, illness arc, business launch ramp), or `chain` with a named milestone
template (e.g. education: exam-written → result → enrollment → completion; venture: decision →
registration → first-revenue) — including, where classically meaningful, the designated
IRREVERSIBILITY MILESTONE (first payment credited, deed registered, letter in hand) as the
strongest match target. The shape is ontology DATA, consumed identically by the matcher (A-1),
the ledger (A-4), and the engine's own outputs (§4.4) — events unfold, they do not merely occur,
and every layer of the arc must speak in that grammar.

**A-3 — Negative controls + proper-scoring harness** (= v2.0 Lane C-4 + the DR-15 upgrade):
shuffled-birth + antiphase controls real (stubs die); **CRPS/log-score scoring alongside legacy
hit-rate**; skill = 1 − CRPS_model/CRPS_control; control-mirroring enforced in the harness
itself (a scoring rule that isn't applied to the control refuses to run). The harness is
MODEL-AGNOSTIC: anything exposing `curve(chart, event_class, [t1,t2])` can be scored.

**A-4 — Prospective ledger, LIVE from this wave** (= v2.0 Lane C-7 + generator attribution):
prediction store (claim, event_class per A-2 ontology, **claim_shape matching the ontology's
canonical shape — a point-claim for an interval-class event is a schema violation**, window or
milestone-set accordingly, model + formula_version, confidence, falsifier, as_of,
**generator_class** [anchor_engine | reading_synthesis | engine],
**configuration_signature** [nullable until D-5 populates it]); LEL-append → outcome-matching
hook via A-1's matcher; native-readable ledger surface; first entries = the wealth-baseline
arc predictions (Sat–Jup pratyantar 2027-04-09→08-18; Ketu-MD consolidation shape; Venus-MD
2034 activation) each with falsifier.

**A-5 — Harness dry-run (gate lane):** score the three existing models (midpoint-triangle,
pratyantar-lord, transit-kernel-on-repaired-substrate) through the A-3 harness on the full
DR-13-scored LEL. Results recorded as **diagnostics only — explicitly NOT the DR-12
adjudication** (deferred to D-4b; the dry-run's purpose is to prove the harness, find its bugs,
and give D-5 a baseline to beat during construction).

**D-4a gate (sketch — brief will formalize):** A-0 live assertions (v2.0 §G.1 verbatim);
matcher matches both named specimens with the windfall scored as interval + synthetic chain
event scores per-milestone; ontology published and consumed by matcher + ledger; controls real
with mirroring enforced; CRPS harness scores all three models end-to-end with per-event tables
committed; ledger live with ≥5 falsifier-bearing entries + demonstrated append-hook; carried
findings #2/#4 dispositioned; anti-gaming pass; all prior batteries green.

**Explicitly OUT of D-4a:** any DR-12 retirement ruling; the C-2 backfill; C-5; C-6;
any engine construction.

## §4 — D-5: Gochara-Chitra (the engine)

### §4.1 — Resonance map (chart-side, build-time)
Formalize the Taraṅga chart-static substrate into a persisted, served, event-class-aware map:
for each event-class e (A-2 ontology), the target set T_e = natal points classically relevant
(shastra map bhavas + lords + karakas), mechanism nodes (D-2 objects incl. tenancy/affliction
mechanisms), sensitive degrees, arudhas, yoga-constituent degrees, dasha-lord portfolios —
each target carrying contact-type sensitivities with **classical-prior weights** sourced from
bg_transit_rules + BPHS transit chapters (citations mandatory, B.3). Persisted as
`gochara_resonance_map` (per chart × event-class), served with provenance. The map is sparse:
this is what makes scanning millions of sky-states a cheap projection.

### §4.2 — Configuration grammar (sky-side)
**Contact primitives** (each grounded in an EXISTING L1 category where noted — the grammar
formalizes what the DB already holds, it does not invent new astronomy):
degree-contact (conj/opp/aspect within orb; ephemeris_daily) · drishti-contact (Parashari
special aspects onto natal points/cusps) · sign-ingress relative to lagna/chandra ·
nakshatra-ingress + tara-state from natal Moon (tara_bala) · kakṣyā-cell crossing (shipped
D-3 T-1) · AV-threshold state (SAV/BAV gating, shipped) · gochara-vedha pair states
(bg_transit_rules) · Sarvatobhadra vedha on natal nakshatra points (CR-21 completion — the
lane's classical centerpiece) · station/retro-loop points near natal degrees (retrograde
periods) · eclipse-degree contacts · return events (Saturn/Jupiter/nodal — K-7 closes here) ·
Sāde-Satī phase states (ga_sade_sati).
**Composition operators:** simultaneity (∧ within tolerance) · double-transit (two grahas'
drishti on one target — Guru-Śani first-class) · kartari (bracketing of a natal point) ·
cancellation (vedha ∧ primitive) · amplification (AV state × primitive) · dasha-coincidence
(primitive ∧ window from ANY DR-14 system, at any level incl. pratyantar).
Every servable "configuration" is a sentence; every sentence carries constituent fact_ids +
classical citation or an honest `uncited_extension` flag (B.10 — no invented rules).

### §4.3 — Intensity engine
λ_e(t | chart) = PROMISE_e(chart) × PERMISSION(t) × exp(β_e · X(t)) − suppression terms, where
X(t) = sparse active-sentence vector from the sweep, β_e initialized from CLASSICAL PRIORS
(the resonance map weights — the texts are the prior, the data will be the likelihood; until
D-4b fits them, all β served as `calibration_state: structural_prior`), PERMISSION = the
multi-system window superposition per DR-14 (Vimśottarī levels, Chara, Nārāyaṇa, Tājaka
year-lord, and the other stored systems as independent generators — NOT as a Vimśottarī-gated
multiplier). Adverse event-classes get the identical machinery with signed valence (D-2's
valence doctrine) — auspicious and inauspicious are symmetric outputs, per the vision.

### §4.4 — Forward-sweep service + serving
Daily-grid sweep over the chart-relative horizon **birth → birth+100 years** (§10 Q3 —
retro-scored past + full forward span in one standing table; curve() unbounded beyond),
materializing
threshold-crossing windows per event-class into `kala_gochara_windows` (window, event_class,
signed intensity, active sentences with fact_ids, systems contributing, suppression state,
peak_basis provenance per DR-10). **Shape-aware output semantics (binding):** the engine
emits in the event-class's canonical shape — for point-class events a dated window with peak;
for interval-class events an elevated-hazard SPAN with duration drawn from the ontology's
duration prior (never a single asserted day); for chain-class events per-milestone sub-windows
(the sweep scores each milestone's own configuration — an enrollment fires on different
primitives than a result-declaration), with the irreversibility milestone flagged as the
primary claim. Event-time ambiguity is honored at generation, not just at scoring — the engine
must never speak with more temporal precision than the event-class's shape supports. Serving views: activation query, forecast scan, election/
avoidance (muhurta becomes argmax over the signed field — the existing muhurta_finder becomes
a view), plus curve access for the harness. §N.6 density discipline + budgets from day one.

### §4.5 — Test-first construction discipline (binding on every lane)
Every D-5 lane's acceptance includes a mini-retrodiction check through the D-4a harness (does
this lane's contribution improve CRPS skill on the relevant event-classes vs the A-5 baseline,
or at minimum not degrade it? — recorded per-lane, diagnostics not gates), plus specimen
requirements from the LEL (e.g. the Sarvatobhadra lane must show its vedha states around
2025-05 and 2010-07; the double-transit lane must produce the marriage-2013 configuration).
The engine may not arrive at its gate unmeasured. D-5's own gate: engine-integrity +
specimen + no-degradation assertions — NOT a calibration claim (that's D-4b's).

### §4.6 — Explicitly OUT of D-5
KP sub-lord engine (CR-75 — no substrate; enters only if independently built first) · any
fitted β (structural priors only) · any DR-12 ruling · new ayanamsha/astronomy code beyond the
sidecar's existing capabilities.

## §5 — D-4b: Calibration Ignition + Grand Bakeoff (lanes from v2.0, now meaningful)

**B-1 Grand bakeoff (= v2.0 C-B + DR-14/15):** full contender set — midpoint-triangle
(incumbent, expected retirement), pratyantar-lord, transit-kernel, each D-5 system-generator
standalone, and the hierarchical ENSEMBLE — one identical harness (D-4a's), pre-registered
thresholds/event-set/win-criterion, CRPS primary + hit-rate legacy, mirrored controls,
per-model per-event tables committed, **no-winner branch pre-committed verbatim from v2.0**.
DR-12 adjudication happens HERE. DR-14's learned system-weights come out of this lane.
**B-2 One-shot backfill (= v2.0 C-2):** against the bakeoff-selected model (or best-available
+ `model_confidence: none_validated` on the no-winner branch); shrinkage honesty + structural-
mode exit criterion verbatim from v2.0.
**B-3 Hierarchical calibration:** event-class-level weights, chart-level shrunk toward them;
every multiplier serves n_observations + control delta + calibration_state.
**B-4 Remedy-leverage join (= v2.0 C-5)** and **B-5 mechanism_retrodiction surface (= v2.0
C-6)** — unchanged content.
**B-6 Campaign close:** v2.0's close condition verbatim — parked-items review, DR ratification
sweep, register seal, master regression suite, and the THREE-POINT BASELINE DIFF (pre-D-2 →
post-D-2 → post-arc) as the native-facing deliverable of the whole campaign.

## §6 — Doctrine pipeline (drafted for native ratification at D-4a bind)

- **DR-14 — Daśā non-exclusivity / timing-system plurality:** windows are generated by a
  plurality of systems computable from stored data (Vimśottarī spine as default generator, not
  absolute container; Chara/Nārāyaṇa; Tājaka; double-transit; AV-threshold; returns; Sāde
  Satī); cross-system confluence raises confidence per the classical multi-pramāṇa principle;
  per-system weights are LEARNED (D-4b), never assumed; no system's window may be served as
  exclusive.
- **DR-15 — Ensemble + proper scoring:** the confluence ensemble is a first-class contender;
  model comparison uses proper scoring rules (CRPS/log-score) with mirrored reference
  forecasts; hit-rate retained as legacy secondary; densities may be multi-modal (several
  peak-logics coexisting within one window is a legitimate served shape).
- **DR-16 — Adverse-window disclosure:** inauspicious windows are served under the Ethical
  Framework's disclosure tiers — probabilistic, falsifier-bearing, never fatalistic, always
  paired with the suppression/mitigation surface; "likely difficult for X" framing; no
  death/catastrophe point-claims. (Ethics before capability: this DR gates D-5's adverse
  serving, and the native ratifies its exact language before that lane ships.)

## §7 — Statistical spine (arc-wide commitments)

**Event-shape symmetry (arc-wide invariant):** the DR-13 shape semantics apply identically to
MEASUREMENT (matcher, harness, controls) and GENERATION (ontology, ledger claims, engine
output) — a system that scores intervals but predicts points has not implemented the doctrine ·
Point-process intensity with sparse sentence features · classical texts as informative priors,
data as likelihood · hierarchical partial pooling (chart ← event-class ← global; honest at
N≈40, strengthens as charts join per §A research ambition) · sparsity priors on β (horseshoe/
lasso-class) so most sentences stay at ~0 · proper scoring rules with mirrored controls ·
pre-registration of thresholds/event-sets before every scoring run · sealed test-split
discipline unchanged (ESCALATION §4) · every loosening mirrored to controls (DR-13).

## §8 — Risk register (arc-level)

R1 overfitting one chart (mitigation: hierarchy + sparsity + priors + sealed split) · R2 engine
scope explosion in D-5 (mitigation: grammar over EXISTING L1 categories only; §4.6 exclusions;
per-lane mini-checks catch dead weight early) · R3 gate-gaming pressure after a second red
(mitigation: pre-committed branches, anti-gaming verifier, native-only adjudication of
integrity gates) · R4 compute (mitigation: sparse projection + daily grid + materialized
windows; sweep is batch, not per-query) · R5 wall-clock (mitigation: A-4 ledger live from
D-4a; D-5 lanes parallelizable after resonance-map lane) · R6 adverse-serving ethics
(mitigation: DR-16 gates the lane; native ratifies language first) · R7 the one-shot backfill
run prematurely (mitigation: B-2 hard-gated on B-1's adjudication receipt — encoded in the
brief's merge order, verified by scope-warden).

## §9 — Production checklist (what gets authored next, in order)

1. Native ratifies THIS PLAN (v1.0 → RATIFIED) — including the D-4a/D-5/D-4b naming and the
   DR-14/15/16 drafts as bind-time ratification candidates.
2. `BRIEF_D4A.md` v1.0 (cut from §3 + BRIEF_D4 v2.0's corresponding lanes; full §F3-class
   execution discipline; promise ledger; §B bind slots incl. bakeoff-dry-run pre-registration).
3. `SANKALPA_GOCHARA_CHITRA_v1_0.md` (vision document — §0/§4 expanded with the classical
   sourcing for each primitive; feeds MACRO_PLAN review trigger per hygiene §I).
4. `BRIEF_D5.md` v1.0 skeleton (lanes from §4; FROZEN after D-4a's close ratifies its §B).
5. `BRIEF_D4B.md` v1.0 skeleton (from §5; binds after D-5's gate).
6. Governance: BRIEF_D4 v2.0 marked SUPERSEDED-BY-ARC (content preserved as lane source);
   CLAUDECODE_BRIEF wave_sequence + current_wave → D-4a (INCOMING); CURRENT_STATE banner;
   register rows for the redistribution; DR-12 deferral note in DISAGREEMENT_REGISTER.
7. D-4a kickoff prompt (the "Prompt 2" the native asked for — now targeting D-4a).

## §10 — Open questions — RESOLVED (native, 2026-07-19)

Q1. **RESOLVED:** Fable drafts DR-16; native review waived. Binding refinement — the
    **honest-clarity principle**: the consumer is an educated, consenting adult; adverse
    windows are stated CLEARLY and SPECIFICALLY (vagueness is itself a disclosure failure),
    honestly probabilistic, falsifier-bearing, mitigation-paired, within the Ethical
    Framework's tier system. Clarity and honesty are requirements co-equal with restraint.
Q2. **RESOLVED:** native returns the date-tightening questionnaire ASAP, target before A-1
    closes; partial submissions accepted and ingested incrementally.
Q3. **RESOLVED:** sweep horizon is **chart-relative — birth → birth+100 years** (not a fixed
    calendar year; a 2022-born chart sweeps to 2122). Uniform for every chart. Explicitly
    NOT tied to computed longevity (ayurdaya exists in L1 but using it to bound the sweep
    would encode a lifespan claim — Ethical Framework violation; uniform 100y avoids it).
    The curve() API remains unbounded for on-demand ranges beyond.
Q4. **RESOLVED with clarification + a new data-governance principle (§11):** the
    `native_intuition` generator class = EXPLICITLY REGISTERED predictions only — a user
    deliberately files a dated, falsifier-bearing claim into the ledger as an intentional
    act. Chat/consultation conversations are NEVER mined for implicit predictions.

## §11 — Calibration data-governance principle (native-ratified 2026-07-19; binding arc-wide)

Calibration, learning, and scoring draw from exactly TWO user-data sources, for every user:
(1) the user's LEL — ground-truth life events they deliberately provide and maintain;
(2) explicitly registered ledger predictions (any generator_class, including the user's own
    `native_intuition` entries — always an intentional, opt-in filing act).
Chat/consultation content is NEVER mined for training, calibration, or implicit prediction
extraction. A prediction exists in the ledger because someone chose to file it, never because
a conversation was parsed. This applies to the native and to every future user identically.

## §12 — Likely-time acceptance + knowledge census (native-originated 2026-07-20; binds D-4b)

Ratified additions after D-5's specimen findings (full texts: DR-17/DR-18 in
DR_14_15_16_TEMPORAL_DOCTRINE_v1_0.md):
- **DR-17 Graded Manifestation Acceptance:** peak/sub_peak/elevated all right-in-kind; neutral
  = miss; contra = anti-hit (double-weighted against the model); tie-bands for within-
  uncertainty peaks; percentile-of-manifestation vs mirrored control as the calibration curve;
  residual mining of (manifested, skipped-peak) pairs → re-weighting + a served
  `unmodeled_variance` humility term per event-class. The chara_karaka-vs-double-transit
  marriage pair (2013-01-07 vs 2013-12-11) is the type-specimen residual pair.
- **DR-18 Knowledge-Utilization Census:** standing audit of consumed vs computed-unconsumed vs
  known-uncomputed factors; first run at D-4b bind; bakeoff admits factor families by measured
  skill; TESTED-NO-SIGNAL recorded as negative knowledge.
- **D-4b consequences:** B-1's bakeoff scores under DR-17 grades (controls mirrored); B-3's
  calibration outputs include the percentile-of-manifestation distribution + unmodeled_variance
  per class; the KUC backlog feeds candidate factor-families into the bakeoff's contender set.

