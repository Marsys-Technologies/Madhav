---
artifact: PHASE_M5_PLAN_v1_0.md
canonical_id: PHASE_M5_PLAN
version: 1.1
status: CURRENT
authored_by: Cowork-M5-S1-PLAN-AUTHORING-2026-05-13
authored_at: 2026-05-13
amended_by: Cowork-M5-S2-PLAN-AMENDMENT-2026-05-13
amended_at: 2026-05-13
parent_macro_phase: M5 — Probabilistic Model
parent_plan: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M5
predecessor_artifact: 06_LEARNING_LAYER/M4_CLOSE_v1_0.md
predecessor_phase_plan: 00_ARCHITECTURE/PHASE_M4_PLAN_v1_0.md (SUPERSEDED-AS-COMPLETE at M4-D-S1 2026-05-02)
sub_phases: [M5-A, M5-B, M5-C, M5-D, M5-E]
hard_prerequisite_gate: >
  M4 CLOSED — CLEARED 2026-05-02 (M4-D-S1). LL.1–LL.7 active; 30 production-weight
  signals in 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/.
  Pre-M5 portal gates (I, II, III, IV) — CLEARED 2026-05-13 (commit adb61fb).
  No hard prerequisite blocks M5-A entry.
ppl_volume_tracking:
  required_for_m6_entry: "≥20 predictions verified against known outcomes (retroactive held-out LEL approach accepted at M5-S2 Cowork session 2026-05-13)"
  required_for_m6_entry_v1_0: "≥50 prospective predictions with ≥6-month horizon elapsed [SUPERSEDED by v1.1 gate redefinition]"
  current_count_at_m5_open: 16
  gap: "≥4 additional retroactive predictions minimum; ongoing prospective cadence for M7+ calibration depth"
  retroactive_protocol: >
    Generate predictions from chart+dasha state at the time of each held-out LEL event
    WITHOUT reading the recorded LEL outcome. Prediction is written first; then outcome
    is revealed and scored. Blinding is enforced within the session: Claude does not
    consult the LEL entry for the event being predicted until after the prediction is
    committed. This protocol decouples M6 entry from calendar time.
  held_out_partition_target: "9 most recent LEL events (approx 2019–2026); to be formally documented in M5-A-S1"
  note: >
    PPL volume gate redefined (Cowork session 2026-05-13) to use retroactive held-out
    LEL events. This allows M6 to open once ≥20 predictions are verified, rather than
    waiting 6 calendar months for prospective horizons to elapse. Ongoing prospective
    predictions continue to accumulate for M7+ calibration depth; M6 is no longer
    blocked on calendar time.
  prediction_gate_design: >
    NAP.M5.0 approved with caveat (2026-05-13): prediction emission to portal UI is
    gated behind two control layers. Layer 1 — global master switch:
    MARSYS_FLAG_PREDICTION_ENGINE_ENABLED (default OFF; stays off until portal is stable
    end-to-end). Layer 2 — per-chart toggle: prediction_engine_enabled boolean field on
    each chart/client record; only charts with this true emit predictions in chat responses
    when master switch is on. Separation: PPL internal calibration (retroactive held-out
    scoring, PPL log accumulation) continues regardless of flags. Portal UI emission is
    completely suppressed while master flag is OFF. Implementation: per-chart toggle in
    admin UI; deferred to dedicated portal session (new carry-forward item PE.1).
  nap_m5_0_status: "APPROVED with caveat — 2026-05-13, Cowork-M5-B-S1-NAP.M5.1-final"
native_approval_points:
  - M5-A close — PPL cadence plan: retroactive held-out protocol + ongoing prospective cadence (NAP.M5.0); ≥20 gate confirmed
  - M5-B close — DBN topology: node schema, edge types, time-slice structure (NAP.M5.1)
  - M5-C close — Prior specification: per-signal and per-domain priors (NAP.M5.2)
  - M5-D close — Confidence-interval reporting policy: band width, disclosure tier (NAP.M5.3)
  - M5-E close — M5 macro-phase close (held-out pass + IS.8(b) red-team PASS)
mirror_obligations:
  claude_side: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
  gemini_side: phase-plan pointer in .gemini/project_state.md (MP.4 adapted parity; propagated at M5-A open)
  mirror_mode: adapted_parity_pointer
  authoritative_side: claude
  asymmetries: >
    Gemini-side carries a one-line pointer to this plan plus the active sub-phase ID.
    Full sub-phase tables and ACs stay Claude-side. Gemini-side updates on each
    sub-phase transition (M5-A open, M5-B open, M5-C open, M5-D open, M5-E close).
carry_forward_from_m4:
  - CF.LL7.1: CDLM Pancha-MP anchor patch — confirm landed and re-emit ll7_discovery_prior (M5-A)
  - R.LL1TPA.1: Gemini mirror gap (FINAL_NOT_REACHABLE) — re-attempt at M5-A entry
  - KR.M3A.JH-EXPORT: JH-access window + Sthana/Drik ECR + Narayana Dasha — schedule M5-A; execute when JH available
  - R.LL3.1/.2/.3: LL.3 fix-before-prod recommendations — integrate during M5-B/C (retrieval-domain alignment)
  - LL.2 per-edge campaign: 8 MED-tier Pancha-MP anchors awaiting per-edge two-pass (M5-A/B)
  - MSR signal-completeness: 4 absent signal IDs (SIG.MSR.207 + 497/498/499) — reconcile M5-A
  - AC.IV.6 partial (recall=0.9355): pre-existing planner gap — target improvement in M5 retrieval work
  - AC.IV.7 unable (latency_ms null): re-test after M5-A has prod traffic with populated telemetry
changelog:
  - v1.1 (2026-05-13, Cowork-M5-S2-PLAN-AMENDMENT-2026-05-13): Gap-resolution amendment.
      (1) PPL/M6 gate redefined: ≥50/6-month → ≥20 retroactive held-out LEL approach;
      blinding protocol specified; calendar-time dependency eliminated. (2) M5-A scope
      expanded: added items 11–14 (held-out partition formalization, LEL domain enrichment,
      DIS.009 R1 closure, answer:eval framework). (3) DBN tooling confirmed: Hybrid-C
      (JSON CPT manually computed; LLM does inference; LLM-assisted signal selection).
      (4) LLM stack declared: Gemini → DeepSeek → NIM; no Anthropic/Claude API.
      (5) DIS.009 R1 confirmed (AL=Capricorn native-confirmed; PAT.008 split into
      PAT.008-AL + PAT.008-KMC; both L1-groundable from FORENSIC). (6) Execution strategy
      added: dedicated worktree marsys-m5-dbn on feature/m5-probabilistic-model; long-running
      Antigravity session with --dangerously-skip-permissions. (7) R.M5.7 added (retroactive
      PPL blinding risk). (8) LEL enrichment scope: 10 new events from Cowork session
      across spiritual, creative, psychological domains documented for M5-A-S1 addition.
  - v1.0 (2026-05-13, Cowork-M5-S1-PLAN-AUTHORING-2026-05-13): Initial M5 phase plan.
      Sub-phases M5-A through M5-E defined per M4_CLOSE_v1_0.md §5 and MACRO_PLAN §M5.
      Pre-M5 gate sequence declared CLEARED (Gates I, II, III, IV — 6/8 ACs; 2 deferred as
      non-regressions). Two-path M5 architecture: time-independent substrate + topology work
      in M5-A/B/C; time-gated DBN fit in M5-D (waits on LEL held-out partition quality);
      M5-E closes the phase. PPL volume cadence plan is M5-A close deliverable.
---

# PHASE M5 PLAN — v1.0

## §0 — Status block

| Field | Value |
|---|---|
| Macro-phase | **M5 — Probabilistic Model** |
| Active sub-phase | **M5-A — Substrate, Entry Cleanup, PPL Cadence** |
| Sub-phase status | OPEN — M5-A-S1 is next execution session |
| Phase opened | 2026-05-13 (pre-M5 gate sequence CLEARED at adb61fb) |
| Phase plan authored | 2026-05-13 (v1.0); amended 2026-05-13 (v1.1) |
| Hard prerequisite gate | M4 CLOSED — **CLEARED** 2026-05-02; Pre-M5 gates — **CLEARED** 2026-05-13 |
| PPL volume at open | 16 predictions (target ≥20 for M6 gate per v1.1; gap = ≥4 retroactive + ongoing prospective) |
| DBN tooling | Hybrid-C: JSON CPT manually computed; LLM does inference; LLM-assisted signal selection |
| LLM stack | Gemini → DeepSeek → NIM (no Anthropic/Claude API) |
| Execution strategy | Dedicated worktree: marsys-m5-dbn on feature/m5-probabilistic-model; long-running Antigravity session |
| Concurrent (non-blocking) | CW.PPL (active throughout); CW.LEL maintenance; JH-export when JH available |

---

## §1 — Reading order for M5 sessions

Per `CLAUDE.md §C`, every M5 session reads its mandatory list at open. Sub-phase-specific
add-ons:

- **All M5 sessions:** replace item 5 (PHASE_M4_PLAN) with this file. Add
  `06_LEARNING_LAYER/M4_CLOSE_v1_0.md §5` (M5 setup recommendations) at first M5 session
  only; thereafter reference by summary below.
- **M5-A sessions:** add `06_LEARNING_LAYER/` README (LL scaffold state), current PPL log,
  and `MACRO_PLAN_v2_0.md §LL-Appendix.B LL.8–LL.9` (the two new activations for M5).
- **M5-B sessions:** add `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` (once created at M5-A
  close or M5-B open), `MACRO_PLAN §M5` DBN topology section, and MSR production signals
  (the 30 promoted to production at M4 close).
- **M5-C sessions:** add the approved DBN topology artifact, `06_LEARNING_LAYER/dbn/` current
  state, and `MACRO_PLAN §LL-Appendix.B LL.8` prior-specification protocol.
- **M5-D sessions:** add the approved prior specification document, the signal embedding refit
  infrastructure (once scaffolded in M5-C), and `MACRO_PLAN §M5` exit state criteria.
- **M5-E sessions:** add IS.8(b) red-team template (precedent: `00_ARCHITECTURE/EVAL/`),
  held-out DBN validation results (path declared at M5-D close), and `MACRO_PLAN §M6`
  (successor phase orientation).

---

## §2 — Sub-phase summary

| Sub-phase | Name | Sessions (est.) | Primary deliverable | Blocks |
|---|---|---|---|---|
| M5-A | Substrate, Entry Cleanup, PPL Cadence | 3–5 | LL.8+LL.9 scaffold; PPL cadence plan; mirror sync; carry-forward cleared | M5-B |
| M5-B | DBN Topology Design | 3–5 | DBN_TOPOLOGY_v1_0.md; NAP.M5.1 approved | M5-C |
| M5-C | Prior Specification | 3–5 | PRIOR_SPEC_v1_0.md; NAP.M5.2 approved; signal embedding refit scaffold | M5-D |
| M5-D | DBN Fit + Validation | 8–15 | DBN fitted; 3-run refit-stable; held-out PASS; NAP.M5.3 approved | M5-E |
| M5-E | M5 Close | 2–3 | IS.8(b) red-team PASS; M5_CLOSE sealing artifact; CURRENT_STATE flip M5→M6 INCOMING | M6 entry |

**Total envelope:** 20–35 sessions (consistent with MACRO_PLAN §M5 estimate of 20–40).

---

## §3 — Sub-phase rows

---

### M5-A — Substrate, Entry Cleanup, PPL Cadence

**Scope**

1. **LL.8 scaffold** — Bayesian model updating infrastructure. Per `§LL-Appendix.A`, LL.8
   is `scaffold` at M5 (activates once DBN parameters exist from M5-D). Scaffold = directory
   structure, spec document, parameter register stub, kill-switch definition.
   Path: `06_LEARNING_LAYER/dbn/ll8_bayesian_update/` (or as declared in LL.8 spec).

2. **LL.9 scaffold** — Counterfactual learning from misses. Per `§LL-Appendix.A`, LL.9
   is `scaffold` at M5 (activates at M6). Scaffold = miss_registry stub, spec document.
   Path: `06_LEARNING_LAYER/miss_registry/` (per LL.9 spec).

3. **CDLM patch confirmation (CF.LL7.1)** — Confirm M4-D-P1 parallel patch landed.
   Re-emit `ll7_discovery_prior_v1_0.json` with expected flip: 8 MED-tier sanity anchors
   `novel` → `confirmed`. If patch did NOT land: this becomes M5-A blocker S1.

4. **Gemini mirror sync attempt (R.LL1TPA.1)** — Re-attempt mirror-pair propagation
   for accumulated M4 surrogate decisions per `LL1_TWO_PASS_APPROVAL §5.5`. If REACHABLE:
   ratify or contest per `GOVERNANCE_INTEGRITY_PROTOCOL §K.3`. If NOT_REACHABLE: extend
   surrogate-disclosure ledger entry and declare FINAL_NOT_REACHABLE_M5.

5. **MP.1 + MP.2 mirror catch-up** — CURRENT_STATE v3.9 noted mirror NOT propagated
   at Pre-M5-Final-Autonomous session (may_touch constraint). Propagate at M5-A open.

6. **MSR signal-completeness reconciliation** — 4 absent signal IDs (SIG.MSR.207 + 497/498/499)
   reported by `msr_domain_buckets.json` vs MSR §I declared count of 500. Reconcile:
   either populate the missing signals or update the declared count with rationale.

7. **LL.2 per-edge promotion campaign (Phase 1)** — 8 MED-tier Pancha-Mahapurusha
   anchor edges are promotion-eligible (gate-level block lifted at M4-B-S5). Initiate
   two-pass approval campaign for these 8 edges. Native review is the bottleneck; schedule
   at M5-A open. Target completion: M5-A close or M5-B open.

8. **PPL volume audit + cadence plan (v1.1 — gate redefined)** — M6 gate is now ≥20
   predictions verified against known outcomes (retroactive held-out LEL approach; calendar-
   time dependency eliminated per Cowork session 2026-05-13). Scope: (a) audit the 16
   existing entries for completeness; (b) execute retroactive prediction protocol on held-out
   LEL partition (≥4 events minimum to reach M6 gate; each prediction written BEFORE the
   LEL outcome is read in-session); (c) document the feedback loop: prediction emission →
   LEL outcome recording → comparison → LL.8 Bayesian update; (d) propose ongoing prospective
   cadence for M7+ calibration depth. Cadence plan is the M5-A close native-approval item
   (NAP.M5.0). Falsifier definitions must accompany every prediction.

9. **JH-export workstream scheduling (KR.M3A.JH-EXPORT)** — Three items: JH export of
   Sthana (positional strength) + Drik (aspectual strength) values; ECR for Sthana/Drik
   discrepancies; Narayana Dasha verification. These require JH software access (external
   dependency). M5-A schedules the window with native; execution is parallel-safe whenever
   JH is available.

10. **Gate IV deferred ACs (non-blocking)**
    - AC.IV.6 (recall=0.9355): Re-run golden-set eval after LL.3 retrieval fixes land
      (target: M5-B). Not a blocker for M5-A close.
    - AC.IV.7 (latency_ms null): Re-check audit_events telemetry after 7 days prod traffic.

11. **Held-out partition formalization** — The LEL held-out partition was never formally
    documented at M4-B close. At M5-A-S1 open: declare the held-out partition explicitly
    before any retroactive prediction work begins. Target: 9 most recent LEL events
    (approximate range 2019–2026). Document the partition in a dedicated file or LEL
    section. From this point forward, held-out events are treated as sacrosanct: no
    topology, prior, or DBN-design session may read held-out outcomes until M5-D fitting
    begins.

12. **LEL domain enrichment (10 new events)** — Cowork session 2026-05-13 produced
    structured life-event data across four previously sparse domains. Events to be written
    into the LEL as new YAML entries with full chart_state_at_event, retrodictive_match,
    and notes fields. Dasha and transit tags will require Swiss-Ephemeris lookup for events
    prior to 2026-05-01 (proxy-date computation acceptable for year-approx events).
    New event list (approved by native in Cowork session):
    - SPR.A: Father's spiritual dialogue transmission (late teens ~1997–2001) — seed event
    - SPR.B: Shani Puja initiation by father (~2002–2003, sustained ~10 years) — Shani Shtotram nightly
    - SPR.C: Ugratara Shakti pitha devotion onset (~2009–2011, ongoing ~15 years)
    - SPR.D: Mahadev/Shiva devotion onset (early thirties ~2014–2016)
    - SPR.E: Daily abhisheka + yajna practice + panchang study convergence (~2024)
    - SPR.F: Yantra mandala established (mid-2025)
    - SPR.G: Ma Kamlatmika (tantric Mahalakshmi) devotion onset (late 2025)
    - CRE.A: Painting competition awards, childhood (~1990–1996) — multiple prizes
    - PSY.A: Vertigo/head reeling onset and peak debilitation during engineering exam prep (~2001–2004)
    - PSY.B: Stammering onset-overcome-resurgence arc (childhood → overcome by MBA years → resurgence 2025)
    NOTE: Cockroach phobia (childhood) to be added as a §5 chronic_pattern entry, not a
    point event. Father's passing, knee surgery, and panic attacks are already in the LEL.

13. **DIS.009 formal closure** — R1 verdict confirmed by native in Cowork session 2026-05-13.
    PAT.008 is to be split into two patterns:
    - PAT.008-AL: Arudha Lagna = Capricorn (10th house); lord = Saturn; confirmed by native.
    - PAT.008-KMC: Karakamsa = Gemini (Moon AK in Gemini D9); lord = Mercury; confirmed
      from FORENSIC_ASTROLOGICAL_DATA §20.1 (Moon D9 = Gemini; Atmakaraka = Moon 27°02').
    Both patterns are L1-groundable without JHora. DISAGREEMENT_REGISTER_v1_0.md DIS.009
    entry to be updated: status = RESOLVED_R1; verdict = split accepted; both patterns
    confirmed from FORENSIC L1 data; native adjudication 2026-05-13.

14. **answer:eval framework scaffold (DeepSeek)** — Per Cowork session 2026-05-13 decision:
    answer:eval uses DeepSeek (not Claude API — costs too high). Scaffold the evaluation
    framework: prompt template for DeepSeek-based quality scoring; rubric aligned to
    B.11 (Whole-Chart-Read discipline), citation completeness, calibration, and B.10
    (no fabricated computation). Output: eval harness runnable against production responses.
    This scaffold is parallel-safe with DBN topology work.

**Acceptance criteria (M5-A close)**

- [ ] AC.M5A.1 — LL.8 scaffold: directory created; spec document at `06_LEARNING_LAYER/dbn/ll8_bayesian_update/LL8_SPEC_v1_0.md`; parameter register stub present; kill-switch condition defined
- [ ] AC.M5A.2 — LL.9 scaffold: directory created; spec document at `06_LEARNING_LAYER/miss_registry/LL9_SPEC_v1_0.md`; miss_registry stub present
- [ ] AC.M5A.3 — CF.LL7.1 resolved: `ll7_discovery_prior_v1_0.json` re-emitted; 8 MED-tier anchor status confirmed (novel → confirmed or finding documented if not flipped)
- [ ] AC.M5A.4 — R.LL1TPA.1 disposition recorded (REACHABLE+ratified or FINAL_NOT_REACHABLE_M5 declared in surrogate ledger)
- [ ] AC.M5A.5 — MP.1+MP.2 mirror propagated for CURRENT_STATE v3.9 delta
- [ ] AC.M5A.6 — MSR signal-completeness reconciled: 4 absent IDs resolved or count updated with rationale
- [ ] AC.M5A.7 — LL.2 per-edge campaign initiated: 8 MED-tier edges submitted for two-pass native review
- [ ] AC.M5A.8 — PPL cadence plan authored and native-approved: retroactive held-out protocol documented; ≥4 retroactive predictions executed against held-out partition (blinding enforced); feedback loop (prediction → outcome → LL.8 update) documented; ongoing prospective cadence proposed; NAP.M5.0 approved
- [ ] AC.M5A.9 — JH-export workstream scheduled with native (window agreed; items scoped)
- [ ] AC.M5A.10 — CURRENT_STATE updated to M5-A CLOSED / M5-B INCOMING
- [ ] AC.M5A.11 — Held-out partition formally declared: ≥9 LEL events identified by ID; partition document or LEL section created; sacrosanct status confirmed before any topology/prior work begins
- [ ] AC.M5A.12 — LEL enrichment complete: all 10 new events from Cowork session 2026-05-13 added to LEL as YAML entries with chart_state_at_event, retrodictive_match, and notes fields; cockroach phobia added as §5 chronic_pattern entry
- [ ] AC.M5A.13 — DIS.009 closed: DISAGREEMENT_REGISTER updated with R1 verdict; PAT.008 split recorded (PAT.008-AL + PAT.008-KMC); L1 grounding citations confirmed; status = RESOLVED_R1
- [ ] AC.M5A.14 — answer:eval scaffold complete: DeepSeek-based eval harness exists; rubric covers B.11, citation completeness, calibration, B.10; runnable against production responses

**may_touch (M5-A)**
`06_LEARNING_LAYER/dbn/`, `06_LEARNING_LAYER/miss_registry/`, `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/shadow/` (LL.2), `025_HOLISTIC_SYNTHESIS/` (CDLM re-emit for CF.LL7.1), `01_FACTS_LAYER/LIFE_EVENT_LOG_*.md` (new entries + PPL section + held-out partition declaration), `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md`, `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` (DIS.009 closure), `.geminirules`, `.gemini/project_state.md`, `platform/scripts/eval/` (answer:eval scaffold — new directory)

**must_not_touch (M5-A)**
`platform/` (no app code in M5-A), `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md`, `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/` (production weights are frozen until M5-D validated)

---

### M5-B — DBN Topology Design

**Scope**

The DBN (Dynamic Bayesian Network) models how the chart's signals interact over time to
produce outcomes in life-domains. This sub-phase produces the topology — the shape of the
model — before any fitting happens. A topology that is approved but later disproved by the
data is still a valid scientific output; the discipline is to commit the topology before
seeing the held-out data.

1. **DBN topology proposal** — Define:
   - Node schema: which MSR signals become DBN nodes; which are latent variables; which are
     observed (tied to LEL events)
   - Edge types: causal, correlational, temporal (t → t+1 slices)
   - Time-slice structure: dasha periods as the time unit? Solar year? Transit windows?
   - Domain scope: which life-domains are modeled in v1.0 (career, health, relationships,
     finance, spiritual — or a subset?)
   - Parameterization space: conditional probability tables vs continuous parameterization

2. **Gemini two-pass topology review** — Per agent-role assignment in MACRO_PLAN §M5:
   "Gemini on topology proposals + prior elicitation." Gemini proposes alternatives and
   critiques. Claude synthesizes. Native adjudicates divergence.

3. **LL.3 retrieval-domain alignment** — Integrate R.LL3.1/.2/.3 fixes so that the
   retrieval layer surfaces signals aligned with the DBN's domain structure before the
   topology is locked. Fix before topology is locked per M4 close recommendation §5 item 6.

4. **LL.2 per-edge campaign completion (Phase 2)** — Complete the two-pass approval for
   the 8 MED-tier edges started in M5-A if not completed there.

5. **Native topology approval (NAP.M5.1)** — Full topology document with rationale, risk
   register entry per MACRO_PLAN §M5 risk (d) (topology overfit to LEL history), and
   native sign-off. After NAP.M5.1, topology is frozen for fitting.

**Acceptance criteria (M5-B close)**

- [ ] AC.M5B.1 — DBN_TOPOLOGY_v1_0.md authored at `06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` with node schema, edge types, time-slice definition, domain scope, parameterization choice
- [ ] AC.M5B.2 — Gemini two-pass topology review completed and documented
- [ ] AC.M5B.3 — LL.3 retrieval-domain alignment implemented (R.LL3.1/.2/.3 addressed)
- [ ] AC.M5B.4 — LL.2 per-edge campaign complete: 8 MED-tier edges two-pass approved or deferred with rationale
- [ ] AC.M5B.5 — NAP.M5.1 APPROVED by native (topology frozen)
- [ ] AC.M5B.6 — Topology risk register entry authored (overfit mitigation documented)
- [ ] AC.M5B.7 — AC.IV.6 re-evaluated after LL.3 fixes (golden-set eval re-run)

**may_touch (M5-B)**
`06_LEARNING_LAYER/dbn/`, `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/shadow/` (LL.2 completion), `platform/lib/` (LL.3 retrieval fixes — surgical), `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md`, `.geminirules`, `.gemini/project_state.md`

**must_not_touch (M5-B)**
`01_FACTS_LAYER/` (facts layer frozen; no new fact derivations during topology design), `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/` (production weights frozen), held-out LEL partition (sacrosanct until M5-D fitting)

---

### M5-C — Prior Specification

**Scope**

Priors lock the Bayesian model's initial beliefs before any data is seen. Per Learning Layer
discipline rule #1: "Classical priors are locked; learning modulates, never overwrites." The
prior specification is the formal expression of classical Jyotish knowledge as probability
distributions over the DBN parameters.

1. **Prior elicitation (classical → probabilistic)** — For each node and edge in the
   approved topology, specify a prior distribution:
   - Point priors for well-established classical claims (e.g., Venus in Libra in 7th
     strongly indicates partnership quality — prior probability high)
   - Weakly informative priors for empirically uncertain claims
   - Conjugate family choices (Dirichlet for categorical; Beta for binary; Gaussian for
     continuous strength scores)
   Per MACRO_PLAN §M5 agent roles: "Gemini on topology proposals + prior elicitation."

2. **Two-pass prior review** — Gemini proposes priors; Claude critiques for Bayesian
   discipline (are they truly "locked" priors or retrofitted on LEL history?); native
   adjudicates. Risk (a) from MACRO_PLAN §M5: "prior specification bias → mitigation:
   Bayesian discipline + two-pass Gemini/Claude prior review."

3. **Prior specification document (PRIOR_SPEC_v1_0.md)** — Complete specification with
   per-parameter prior family, hyperparameters, classical-citation basis, and confidence
   tier (HIGH = directly attested in classical texts; MED = inferred from classical rules;
   LOW = working assumption pending M8 cross-reference).

4. **Signal embedding refit scaffold** — Per MACRO_PLAN §M5 exit state (b): "signal
   embeddings stable across 3 refit runs." Scaffold the embedding refit infrastructure
   before M5-D so that the 3-run stability test can be executed without setup delays.
   Embeddings: GCS L1/L2_5/L3 vector representations via pgvector (Cloud SQL).

5. **Native prior approval (NAP.M5.2)** — Full prior specification review with native.
   After NAP.M5.2, priors are frozen. Any post-fit prior modification requires a formal
   disagreement register entry and native re-approval.

**Acceptance criteria (M5-C close)**

- [ ] AC.M5C.1 — PRIOR_SPEC_v1_0.md authored at `06_LEARNING_LAYER/dbn/PRIOR_SPEC_v1_0.md`; every DBN parameter has a prior entry (family + hyperparameters + classical citation + confidence tier)
- [ ] AC.M5C.2 — Two-pass prior review completed: Gemini pass documented; Claude critique pass documented; divergences resolved or logged in DISAGREEMENT_REGISTER
- [ ] AC.M5C.3 — Bayesian discipline audit: no prior is demonstrably retrofitted on LEL training data (auditor traces each prior to its classical-text basis, not to LEL outcomes)
- [ ] AC.M5C.4 — Signal embedding refit scaffold ready: infrastructure documented; 3-run stability test procedure written; `06_LEARNING_LAYER/dbn/embedding_refit/` directory exists
- [ ] AC.M5C.5 — NAP.M5.2 APPROVED by native (priors frozen)
- [ ] AC.M5C.6 — CURRENT_STATE updated to M5-C CLOSED / M5-D INCOMING

**may_touch (M5-C)**
`06_LEARNING_LAYER/dbn/`, `06_LEARNING_LAYER/dbn/embedding_refit/`, `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md`, `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md`, `.geminirules`, `.gemini/project_state.md`

**must_not_touch (M5-C)**
`01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/`, held-out LEL partition, `platform/` (no app code in prior spec phase)

---

### M5-D — DBN Fit + Validation

**Scope**

With topology and priors locked, this sub-phase fits the DBN on the training data and
validates it on the held-out partition. This is the core statistical work of M5.

**Pre-condition:** Held-out LEL partition must NOT have been consulted during topology or
prior phases (sacrosanct rule, Learning Layer discipline #4). The held-out partition was
declared at M4-B close; its contents are blinded until this sub-phase begins.

1. **Signal embedding refit (3-run stability test)** — Per MACRO_PLAN §M5 exit state (b).
   Run the embedding refit 3 independent times on the training partition. Embeddings are
   stable if the cosine similarity between run i and run j > threshold (threshold declared
   in the PRIOR_SPEC or LL.2 specification; default: 0.95). If unstable: investigate and
   resolve before proceeding to DBN fitting.

2. **DBN fit on training partition** — Fit DBN parameters (conditional probability tables
   or equivalent) using the training LEL partition (37 events), the 30 production-weight
   signals from LL.1, and the edge weights from LL.2.

3. **Held-out validation** — Apply the fitted DBN to the held-out LEL partition (~9 events).
   Per MACRO_PLAN §M5 exit state (a): "DBN identifies on held-out data (LEL 20% partition)."
   "Identifies" = the DBN assigns materially higher probability to the held-out events
   than a null model (random baseline). Tolerance declared in PRIOR_SPEC.

4. **Bayesian posterior framing** — Per MACRO_PLAN §M5 exit state (c): "Bayesian posterior
   framing applied to all outputs." Every query response that involves a signal or prediction
   must now carry: posterior probability estimate, credible interval, prior-vs-posterior
   delta, and sample-size caveat. This requires application-layer changes in the synthesis
   prompt and answer format.

5. **Confidence-interval reporting policy** — How wide? What credible level (80%? 95%)?
   How are asymmetric intervals displayed? What does the disclosure tier say about n=1
   uncertainty? This is a native-approval item (NAP.M5.3) because it determines what
   users see.

6. **LL.8 activation** — With DBN parameters in hand, LL.8 (Bayesian model updating)
   transitions from scaffold to active. The update mechanism fires on new PPL outcomes
   as they arrive.

7. **AC.IV.7 re-evaluation** — Latency telemetry should have ≥7 days of prod data by
   now. Re-run the latency regression check against the pre-gate baseline.

**Acceptance criteria (M5-D close)**

- [ ] AC.M5D.1 — Signal embedding refit: 3 independent runs complete; pairwise cosine similarity all ≥ threshold; result documented
- [ ] AC.M5D.2 — DBN fitted: parameter file at `06_LEARNING_LAYER/dbn/dbn_params_v1_0.json` (or equivalent format); fit procedure documented; training log present
- [ ] AC.M5D.3 — Held-out validation PASS: DBN posterior probability on held-out events materially exceeds null model within declared tolerance
- [ ] AC.M5D.4 — Bayesian posterior framing implemented in synthesis outputs: every signal-bearing response carries posterior probability, credible interval, prior-vs-posterior delta, n=1 caveat
- [ ] AC.M5D.5 — NAP.M5.3 APPROVED: confidence-interval reporting policy locked (band width, credible level, asymmetric display, n=1 disclosure text)
- [ ] AC.M5D.6 — LL.8 transitioned: scaffold → active; first Bayesian update cycle documented
- [ ] AC.M5D.7 — AC.IV.7 re-evaluated and result recorded (PASS or tracked finding)
- [ ] AC.M5D.8 — CURRENT_STATE updated to M5-D CLOSED / M5-E INCOMING

**may_touch (M5-D)**
`06_LEARNING_LAYER/dbn/`, `06_LEARNING_LAYER/dbn/embedding_refit/`, `06_LEARNING_LAYER/dbn/ll8_bayesian_update/`, `platform/lib/` (synthesis prompt — Bayesian framing), `platform/src/` (answer display — confidence interval rendering), `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md`, `.geminirules`, `.gemini/project_state.md`

**must_not_touch (M5-D)**
`06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md` (topology frozen), `06_LEARNING_LAYER/dbn/PRIOR_SPEC_v1_0.md` (priors frozen), `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/` (production weights frozen), `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md`

---

### M5-E — M5 Close

**Scope**

1. **IS.8(b) macro-phase-close red-team** — Per MACRO_PLAN §IS.8(b): mandatory at every
   macro-phase close. Five axes: factual accuracy, layer separation, derivation ledger,
   mirror discipline, scope discipline. Gemini runs the red-team; Claude runs it
   independently; native adjudicates any divergence. M5 does not close until red-team PASS.

2. **PPL volume checkpoint** — Report: how many predictions are in CW.PPL at M5 close?
   How many have ≥6-month elapsed horizon? Project: at current cadence, when will M6's
   ≥50 gate be clearable? If gap is large, emit a remediation plan.

3. **M5_CLOSE sealing artifact** — Per M4 precedent: `06_LEARNING_LAYER/M5_CLOSE_v1_0.md`.
   Sections: LL.8 outcome; DBN fit results; held-out validation summary; NAP registry;
   carry-forward roster; red-team results; M6 setup recommendations.

4. **CURRENT_STATE flip M5 → M6 INCOMING** — Update `active_macro_phase` to M6,
   `last_session_id`, `next_session_objective`, `file_updated_at`, `file_updated_by_session`.

5. **Mirror propagation** — Full MP.1+MP.2+MP.4 propagation at M5-E close.

**Acceptance criteria (M5-E close)**

- [ ] AC.M5E.1 — IS.8(b) red-team PASS (5/5 axes, 0 findings; or all findings resolved before close)
- [ ] AC.M5E.2 — PPL volume checkpoint reported: count at M5 close; eligible-horizon count; projection to M6 gate
- [ ] AC.M5E.3 — M5_CLOSE_v1_0.md authored and committed to `06_LEARNING_LAYER/M5_CLOSE_v1_0.md`
- [ ] AC.M5E.4 — CURRENT_STATE flipped M5 → M6 INCOMING
- [ ] AC.M5E.5 — SESSION_LOG.md M5-E entry appended (full atomic open+body+close block)
- [ ] AC.M5E.6 — All three mirror pairs (MP.1, MP.2, MP.4) propagated

---

## §4 — Risk register (M5-specific)

| Risk ID | MACRO_PLAN ref | Risk | Mitigation |
|---|---|---|---|
| R.M5.1 | §M5 risk (a) | Prior specification bias — priors unconsciously fitted to LEL history | Two-pass review; auditor traces each prior to classical-text basis before fitting begins; bias flag in PRIOR_SPEC per parameter |
| R.M5.2 | §M5 risk (b) | DBN under-identification at n=1 — too few events for reliable parameter estimation | Shadow mode; M7 re-fit plan; conservative credible intervals; n=1 caveat attached to all outputs per §3.5.A |
| R.M5.3 | §M5 risk (c) | Learned-vs-classical divergence — DBN posterior contradicts well-established classical rules | Divergence-alert threshold declared in PRIOR_SPEC; any divergence > threshold triggers DISAGREEMENT_REGISTER entry; learning discipline rule #1 (priors locked) enforced |
| R.M5.4 | §M5 risk (d) | Topology overfit to LEL history — topology designed with LEL in mind, not locked before seeing data | Held-out partition sacrosanct; topology locked at NAP.M5.1 before any data consultation; audit trail |
| R.M5.5 | New | PPL volume gap (16 → ≥50) — M6 gate unreachable if cadence is too slow | M5-A cadence plan; daily/weekly prediction emission discipline; PPL volume tracked at every M5 sub-phase close |
| R.M5.6 | New | Gemini unavailability (R.LL1TPA.1 persists) — two-pass topology and prior review degraded to surrogate | Surrogate-disclosure ledger; accept FINAL_NOT_REACHABLE_M5 if re-attempt fails; proceed with single-agent pass + native adjudication |
| R.M5.7 | New (v1.1) | Retroactive PPL blinding failure — predictions generated after implicitly reading LEL outcome in same session, invalidating the held-out verification | Strict in-session protocol: prediction YAML committed before LEL entry for that event is opened; separate tool-call sequence; audit trail in PPL log recording which session generated the prediction and which session revealed the outcome |

---

## §5 — Learning Layer activation at M5

Per `MACRO_PLAN §LL-Appendix.A`:

| Mechanism | Status at M4 close | Status at M5 open | Target at M5 close |
|---|---|---|---|
| LL.1 — Per-signal weight calibration | active (30 production signals) | active | active |
| LL.2 — Edge weights | scaffold (8 MED-tier pending) | scaffold → active (M5-A campaign) | active |
| LL.3 — Domain coherence | active | active (+ retrieval fix M5-B) | active |
| LL.4 — Temporal weighting | active | active | active |
| LL.5 — Dasha-transit axis-weight modulator | active | active | active |
| LL.6 — Plan selection learning | active | active | active |
| LL.7 — Discovery prior shaping | active (post CF.LL7.1 patch) | active | active |
| **LL.8 — Bayesian model updating** | **scaffold** | **scaffold** | **active** |
| **LL.9 — Counterfactual learning** | **n/a** | **scaffold (M5-A)** | **scaffold** |
| LL.10 — LLM fine-tuning | n/a | n/a | n/a |

---

## §6 — Native-approval points (NAP registry)

| NAP ID | Sub-phase | Item | Status |
|---|---|---|---|
| NAP.M5.0 | M5-A | PPL cadence plan: retroactive held-out protocol + ≥20 gate confirmed + feedback loop + ongoing prospective cadence | **APPROVED with caveat** — 2026-05-13, Cowork-M5-B-S1-NAP.M5.1. Caveat: prediction emission to portal UI gated behind two-layer flag (global `MARSYS_FLAG_PREDICTION_ENGINE_ENABLED` + per-chart `prediction_engine_enabled` toggle). PPL internal calibration continues regardless; UI emission off until portal stable + native enables per chart. Portal implementation item: per-chart prediction toggle in admin UI (deferred to dedicated portal session). |
| NAP.M5.1 | M5-B | DBN topology: node schema, edge types, time-slice, domain scope, parameterization | **PENDING** — U1 resolved (0.20), U3 resolved (LL.2 campaign CLOSED). U2 (SPIRITUAL_PSYCHOLOGICAL → SPIRITUAL + PSYCHOLOGICAL split, 5th domain) approved by native but not yet implemented in DBN_TOPOLOGY_v1_0.md or CPT scaffolds. Topology freeze conditional on M5-B-S2 implementing U2 amendment. |
| NAP.M5.2 | M5-C | Prior specification: per-parameter prior family, hyperparameters, classical citation | PENDING |
| NAP.M5.3 | M5-D | Confidence-interval reporting policy: band width, credible level, n=1 disclosure | PENDING |
| NAP.M5.4 | M5-E | M5 macro-phase close (IS.8(b) PASS + M5_CLOSE artifact review) | PENDING |

---

## §7 — Carry-forward disposition register

Items inherited from M4 close §5. Status at M5-A open:

| Item | Source | Target sub-phase | Status |
|---|---|---|---|
| CF.LL7.1 — CDLM Pancha-MP patch + LL.7 re-emit | M4-D-S1 | M5-A | OPEN |
| R.LL1TPA.1 — Gemini mirror sync re-attempt | M4-D-S1 | M5-A | OPEN |
| KR.M3A.JH-EXPORT — JH window + Sthana/Drik/Narayana | M4 carry | M5-A (schedule); exec when JH available | OPEN |
| R.LL3.1/.2/.3 — Retrieval domain alignment | M4 carry | M5-B | OPEN |
| LL.2 per-edge campaign (8 MED-tier) | M4-B-S5 | M5-A (init) / M5-B (complete) | OPEN |
| MSR 4 absent signal IDs | M4 carry | M5-A | OPEN |
| AC.IV.6 recall gap (0.9355 vs 0.97) | Pre-M5 gates | M5-B (post LL.3 fix) | OPEN (non-blocking) |
| AC.IV.7 latency telemetry | Pre-M5 gates | M5-D (7-day window) | OPEN (non-blocking) |
| MP.1+MP.2 mirror delta (CURRENT_STATE v3.9) | Pre-M5-Final-Autonomous | M5-A | OPEN |

---

*End of PHASE_M5_PLAN_v1_0.md — v1.1 (amended 2026-05-13 at Cowork-M5-S2-PLAN-AMENDMENT session).*
*M5-A is the active sub-phase. Next session: M5-A-S1 — execute §3 M5-A scope items 1–14.*
*Execution vehicle: worktree marsys-m5-dbn on feature/m5-probabilistic-model; long-running Antigravity session.*
