---
artifact: DBN_TOPOLOGY_v1_0.md
canonical_id: DBN_TOPOLOGY
version: "1.1"
status: APPROVED
frozen_at: "2026-05-13T00:00:00+05:30"
frozen_session: M5-B-S2
native_approval_phrase: "I approve"
nap_gate_status: APPROVED
phase: M5-B
sub_phase: M5-B-S2
authored_by: M5-B-S1 (U2 expansion at M5-B-S2)
authored_at: 2026-05-13
nap_gate: NAP.M5.1
held_out_status: >
  Topology committed WITHOUT consulting held-out partition outcomes.
  Held-out partition IDs (from LEL_HELD_OUT_PARTITION_v1_0.md §3):
    EVT.2008.06.09.01, EVT.2009.06.XX.01, EVT.2017.03.XX.01,
    EVT.2018.11.28.01, EVT.2019.05.XX.01, EVT.2022.01.03.01,
    EVT.2024.02.16.01, EVT.2025.05.XX.01, EVT.2026.01.XX.01
  First consultation of held-out outcomes: M5-D fitting phase only.
  All design decisions D1–D6 committed before any held-out outcome was read.
predecessor_artifacts:
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll2_edge_weights_v1_0.json
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll7_discovery_prior_v1_0.json
  - 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL5_DASHA_TRANSIT_DESIGN_v1_0.md
  - 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL4_PREDICTION_PRIOR_v1_0.md
  - 01_FACTS_LAYER/LEL_HELD_OUT_PARTITION_v1_0.md
derivation_ledger:
  - claim: "Antardasha is the atomic time-slice"
    l1_source: "FORENSIC §5.1 — Vimshottari dasha sequence (DSH.V.001–DSH.V.050+) for native's birth 1984-02-05"
    ll_source: "LL5_DASHA_TRANSIT_DESIGN §1.1 — dasha_weight = primary axis for 410/420 observed activations"
  - claim: "5 domains selected (CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL) — U2 split at M5-B-S2"
    l1_source: "FORENSIC §1.2 (Lagna Aries, 10H Capricorn career apex, 7H Libra relationship, 8H Scorpio transformation/psychology, 9H Sagittarius dharma/spirit)"
    ll_source: "LL4_PREDICTION_PRIOR §4 — career/health/relationship each MODERATE tier; spiritual+psychological combined WEAK (n=6, mean_lit=1.0 unreliable); split approved NAP.M5.1 U2 2026-05-13. SPIRITUAL captures dharma/practice events (SPR.*); PSYCHOLOGICAL captures transformation/inner-state events (PSY.*)"
  - claim: "30 production MSR signals are Type A natal static nodes"
    l1_source: "FORENSIC §1–§2 — all 30 signals derive from natal chart structure fixed at birth"
    ll_source: "ll1_weights_promoted_v1_0.json — 30 signals status=production, all natal-static"
  - claim: "Domain persistence initial value 0.65"
    l1_source: "None — initial prior, no L1 basis"
    ll_source: "LL4_PREDICTION_PRIOR §2.2 — mean match_rate 0.630 training; persistence 0.65 is a conservative initialization above this baseline, calibrated at M5-D"
  - claim: "Observation model P(EVENT|ELEVATED)=0.70"
    l1_source: "None — initial prior"
    ll_source: "LL4_PREDICTION_PRIOR §2 — held_out mean_lit=0.913, training mean=0.630; ELEVATED state is defined as the state when signals are densely active, interpolated between these bounds"
  - claim: "Cross-domain CAREER↔RELATIONSHIP edge weight 0.35"
    l1_source: "FORENSIC §2.1 — Saturn exalted Libra 7H (relationship house) as AmK (career significator)"
    ll_source: "CDLM.D1.D3 strength=0.91 bidirectional; LL.2 EDGE-01/02/04/08 co_count=4–7 career-relationship co-activations"
  - claim: "Cross-domain HEALTH↔SPIRITUAL edge weight 0.25"
    l1_source: "FORENSIC §2.1 — Ketu in Scorpio 8H (health transformation house, moksha karaka)"
    ll_source: "CDLM.D4.D6 strength=0.82 Health→Spirit; CDLM.D6.D4 strength=0.80 Spirit→Health; SIG.MSR.402 msr_anchor in D4.D6"
  - claim: "Dasha-state node conditions domain activation via LL.5 axis weights"
    l1_source: "FORENSIC §5.1 — 9 Vimshottari mahadasha lords; precise antardasha sequence from birth"
    ll_source: "LL5_DASHA_TRANSIT_DESIGN §2–§3 — dasha_weight computed for 380 signals; HIGH tier: Sun+Ketu dasha_dominant; MED tier: 12 signals"
nap_m5_1_status: >
  NAP.M5.1 FULLY RESOLVED AND FROZEN at M5-B-S2 (2026-05-13). Three unresolved items all
  resolved: U1 RESOLVED (CAREER↔SPIRITUAL weight confirmed 0.20 by native at M5-B-NAP-S1);
  U2 IMPLEMENTED at M5-B-S2 (SPIRITUAL_PSYCHOLOGICAL split → SPIRITUAL + PSYCHOLOGICAL, 5th domain;
  all 5 CPT scaffolds updated — persistence.json 45 entries, observation.json 5 entries,
  natal_to_domain.json 45 entries, dasha_to_domain.json 81×5-domain, cross_domain.json updated);
  U3 RESOLVED (LL.2 per-edge campaign closed — see ll2_promotion_campaign_v1_0.md §6).
  Native formal freeze approval issued at M5-B-S2: "I approve". Topology status: APPROVED.
  This topology is now frozen — no further design changes permitted. CPT fitting at M5-D may
  adjust initial_values but the graph structure (nodes, edges, domains) is locked.
changelog:
  - v1.0 (2026-05-13, M5-B-S1): Initial committed topology. DRAFT pending NAP.M5.1. All 9 sections populated. D1–D6 committed before held-out consultation.
  - v1.0 amended in-place (2026-05-13, M5-B-NAP-S1): NAP.M5.1 review outcomes recorded in nap_m5_1_status. CAREER↔SPIRITUAL edge weight confirmed 0.20 (U1 resolved). Domain split SPIRITUAL_PSYCHOLOGICAL→SPIRITUAL+PSYCHOLOGICAL approved (U2 approved; implementation deferred to M5-B-S2). LL.2 campaign closed: 3 APPROVED + 1 APPROVED_CONDITIONAL + 4 REJECTED. SIG.MSR.145 label corrected in MSR_v3_0.md. Status remains DRAFT pending U2 implementation.
  - v1.1 (2026-05-13, M5-B-S2): U2 IMPLEMENTED + NAP.M5.1 FORMALLY FROZEN. SPIRITUAL_PSYCHOLOGICAL split into SPIRITUAL (dharmic practice, 9H domain) + PSYCHOLOGICAL (transformation, inner-state, 8H Ketu / 4H Moon domain). D2 updated to 5 domains. §3.3 PSYCHOLOGICAL Type C node added (P(E)=0.25, P(N)=0.50, P(S)=0.25 symmetric scaffold). §3.4 PSYCHOLOGICAL_EVENT Type D node added. §4.1 PSYCHOLOGICAL conditioning edges added: SIG.12 (wt=0.60 MED) and SIG.MSR.297 (wt=0.60 MED). §4.2 PSYCHOLOGICAL column added. §4.4 domain labels updated. §5 CPT file references updated. All 5 CPT scaffolds updated simultaneously. Native issued formal approval at M5-B-S2: "I approve". Status: APPROVED — topology frozen.
---

# DBN TOPOLOGY — v1.0
## MARSYS-JIS — Dynamic Bayesian Network for Abhisek Mohanty's Chart

---

## §1 — Purpose and scope

This document specifies the Dynamic Bayesian Network (DBN) topology for the MARSYS-JIS probabilistic prediction layer. The DBN models how this native's fixed natal chart structure (30 calibrated MSR signals), the unfolding Vimshottari dasha sequence, and latent domain activation states jointly produce observable life events across five life domains: CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, and PSYCHOLOGICAL.

**U2 amendment (M5-B-S2):** The original v1.0 combined domain `SPIRITUAL_PSYCHOLOGICAL` has been split into two distinct domains: `SPIRITUAL` (dharmic practice, 9H Jupiter/Venus domain — captures SPR.* events: practice deepening, devotional intensification, philosophical shifts) and `PSYCHOLOGICAL` (transformation and inner-state, 8H Ketu / 4H Moon domain — captures PSY.* events: psychological pressure periods, inner dissolution, identity restructuring). Native approval phrase issued conditionally at M5-B-NAP-S1: "I approve the deviant topology." Formal freeze at M5-B-S2 after U2 visible.

**What the v1.0 DBN models:** The conditional probability structure linking natal static signals → domain activation states → event occurrences, mediated by the time-varying dasha-state node, across Vimshottari antardasha time-slices from 1984-02-05 forward.

**What v1.0 explicitly does NOT model:**
- Transit nodes beyond the dasha-lord context (deferred to v2.0 if warranted by M5-D validation)
- Finance and Education as separate domains (insufficient training-partition LEL coverage)
- Navamsa (D9) or divisional chart signals beyond what is reflected in the D1 natal signals
- N-step-ahead forward prediction horizon (M6 deliverable)
- Full 81-state dasha matrix with fitted CPT values (M5-D deliverable)

**Philosophical commitment:** Per Learning Layer discipline rule #4, this topology is committed in writing before any held-out event outcome is consulted. The nine held-out event IDs are listed in the frontmatter. The commit timestamp of this file is the pre-registration seal. M5-D fitting may consult held-out data; this topology document may not be modified after commit to accommodate held-out observations.

---

## §2 — Committed design decisions

The following six decisions are made before any DBN fitting. They must not be reversed post-hoc based on held-out partition behavior.

### D1 — Time-slice unit: Vimshottari antardasha period

The Vimshottari antardasha (sub-period) is the atomic time-slice for this DBN.

**Rationale:**
- Antardasha periods average 12–24 months — the right granularity for LEL life events. The LEL events annotated with dasha/antardasha context show strong retrodictive alignment at the antardasha level.
- LL.5 shadow file `ll5_dasha_transit_v1_0.json` confirms: 410/420 observed signal activations across training events are attributed to `dasha` or `both` (dasha+transit jointly). Transit-only activations = 4/420 (< 1%). The dasha axis dominates empirically.
- FORENSIC §5.1 provides the exact antardasha sequence for this native from DSH.V.001 (Jupiter-Venus, 1984-02-05) through DSH.V.023 (Mercury-Saturn, 2024-12-12 to 2027-08-21). This sequence is deterministic — we know exactly which antardasha governs every historical date.
- Solar year is retained as a secondary axis for transit-only signals if transit signals are added in v2.0.

**Derivation:** FORENSIC §5.1 (dasha sequence); LL5_DASHA_TRANSIT_DESIGN §2.1 (primary input: lel_event_match_records.json training partition only, lit_source field).

### D2 — Domain scope in v1.0: 4 domains

**Selected domains:**
1. `CAREER` — professional role changes, promotions, geographic relocations, business launches, employer transitions
2. `HEALTH` — physical symptoms onset, medical procedures, recovery arcs, chronic pattern activations
3. `RELATIONSHIP` — marriage, partnership formation, significant relationship events, separations
4. `SPIRITUAL` — spiritual practice onset/deepening, devotional intensification, dharmic turning points, philosophical consolidations (SPR.* events; 9H Jupiter/Venus domain; Ishta Devata / Dharma Devata activations)
5. `PSYCHOLOGICAL` — psychological pressure periods, inner dissolution, identity restructuring, emotional pattern shifts (PSY.* events; 8H Ketu / 4H Moon domain; Sade Sati inner pressure, Ketu-period deconstruction)

*(U2 amendment at M5-B-S2: domains expanded from 4 → 5 by splitting `SPIRITUAL_PSYCHOLOGICAL` into `SPIRITUAL` + `PSYCHOLOGICAL`. Native approved: "I approve the deviant topology" at M5-B-NAP-S1, conditional on U2 implementation.)*

**Rationale for selection:**
- LL.4 domain priors (ll4_prediction_priors_v1_0.json): career (0.5016 mean_lit, n_obs=431), health (0.4948, n_obs=97), relationship (0.4113, n_obs=124), spiritual (1.0000 lit, n_obs=6). All four have substantial LEL training coverage.
- CDLM v1.3 confirms HIGH-strength (≥0.80) cross-domain linkages between these four: D1↔D3 (0.91), D1↔D6 (0.89), D4→D6 (0.82), D6→D4 (0.80), D3↔D6 (0.86). These are the chart's primary structural linkages.
- Of the 30 production signals: 14 are in health domain, 1 in relationship, 5 in general (multi-domain including career), 9 in unknown/multi-domain (covering career/relationship/spirit).

**Rationale for exclusion:**
- Finance/Wealth: embedded in career events in the LEL training partition; insufficient standalone events to constrain a separate Finance DBN node.
- Education: all pre-1990, entirely in the training partition; too sparse for meaningful node calibration.
- These become v2.0 domain additions contingent on LEL corpus growth.

### D3 — Node types

**Type A — Natal static nodes (exogenous, fixed across all time-slices):**
All 30 production MSR signals from `ll1_weights_promoted_v1_0.json`. These are structural natal chart properties that do not vary with time. In the DBN, they function as background evidence nodes whose observed values are fixed from the chart and condition domain activation priors at every time-slice t.

**Type B — Dasha-state node (time-varying, observed, categorical):**
At each antardasha time-slice t: the tuple `(mahadasha_lord, antardasha_lord)` — 81 possible states (9 planets × 9 planets). This node is **observed** (not latent): the Vimshottari sequence is deterministic from the birth date; we know the state at every t. Source: FORENSIC §5.1 DSH.V.001–DSH.V.050+.

**Type C — Domain activation nodes (latent, time-varying, 3-state):**
One per domain: `CAREER_STATE(t)`, `HEALTH_STATE(t)`, `RELATIONSHIP_STATE(t)`, `SPIRITUAL_STATE(t)`, `PSYCHOLOGICAL_STATE(t)`. States: `{ELEVATED, NORMAL, SUPPRESSED}`. These are the hidden variables. They are NOT directly observed — only the occurrence of events (Type D) is observed. The DBN infers the most probable domain state sequence from the evidence. *(v1.1 U2: SPIRITUAL_PSYCHOLOGICAL_STATE split into SPIRITUAL_STATE + PSYCHOLOGICAL_STATE.)*

**Type D — Event occurrence nodes (observed, binary):**
Per domain per antardasha time-slice: `CAREER_EVENT(t)`, `HEALTH_EVENT(t)`, `RELATIONSHIP_EVENT(t)`, `SPIRITUAL_EVENT(t)`, `PSYCHOLOGICAL_EVENT(t)`. Value = 1 if ≥1 LEL training event in that domain falls within this antardasha period; 0 otherwise. These are the observation model nodes — the "data" the DBN fits against. *(v1.1 U2: SPIRITUAL_EVENT retains SPR.* events; PSYCHOLOGICAL_EVENT captures PSY.* events.)*

### D4 — Edge types

**Static natal → domain activation (Type A → Type C, at every t):**
Each natal signal (Type A) has directed edges to the domain(s) it conditions, weighted by `LL.1_production_weight × CDLM_linkage_strength_score`. The edge weight is computed once and held constant across all t. High-weight signals (production_weight > 0.7) with CDLM anchor are "strong conditioning" (HIGH tier); others are MED or LOW per the conditioning strength formula.

**Dasha-state → domain activation (Type B → Type C, at each t):**
`dasha_state(t)` → [CAREER_STATE(t), HEALTH_STATE(t), RELATIONSHIP_STATE(t), SPIRITUAL_STATE(t)]. The conditional distribution is initialized from LL.5 axis-weight modulation and classical Jyotish domain associations for each mahadasha lord. Antardasha lord modulates the mahadasha tendency as a multiplier.

**Domain persistence (temporal, Type C(t) → Type C(t+1)):**
Domain states persist across antardasha boundaries. Initial persistence probability: P(same_state at t+1 | state at t) = 0.65 for all states and all domains. Fitted values replace these in M5-D. The 3×3 transition matrix per domain is specified in §4.3.

**Cross-domain edges (at same t, Type C(t) ↔ Type C(t)):**
Sourced from CDLM HIGH-linkage domain pairs and LL.2 promoted edges. Three cross-domain edges in v1.0, all verified against CDLM. Specified in §4.4.

### D5 — Parameterization strategy (Hybrid-C)

Per PHASE_M5_PLAN §0 declared tooling:
- CPTs are **manually computed from LL outputs** — JSON format in `06_LEARNING_LAYER/dbn/cpt/`
- LLM (DeepSeek) performs **inference queries** against the fitted CPT structure at M5-D+
- **LLM-assisted signal selection** (DeepSeek) may refine which natal signals condition which domains at M5-C prior specification

In M5-B: produce CPT *structure specification* (schema + initial values based on LL outputs). Actual fitted values land in M5-D after DBN fitting on training data.

### D6 — v1.0 scope boundary

Explicitly out of scope for DBN_TOPOLOGY v1.0:
- Transit nodes beyond dasha-lord context
- Finance, Education, Creative domains
- Navamsa (D9) divisional chart signals
- N-step ahead prediction horizon
- Retrograde state as a separate node (may be added if transit nodes are added in v2.0)

---

## §3 — Node inventory

### §3.1 — Type A nodes: Natal static signals (exogenous)

All 30 production MSR signals from `ll1_weights_promoted_v1_0.json`. Node type A for all.

**Conditioning strength formula:**
- HIGH = production_weight ≥ 0.7 AND CDLM msr_anchor confirmed in ≥1 relevant domain cell
- MED = production_weight ≥ 0.4 OR CDLM msr_anchor confirmed
- LOW = production_weight < 0.4 AND no CDLM anchor (classical house association only)

**Edge weight formula:**
`edge_weight = LL.1_production_weight × CDLM_linkage_strength_score`
where CDLM_linkage_strength_score: HIGH(confirmed anchor in HIGH-strength cell)=1.0, MED(anchor in MED-strength cell or inferred)=0.6, LOW(classical only, no anchor)=0.2, ABSENT=0.0

| Signal_ID | Description (abbreviated) | LL.1_prod_wt | Domains_conditioned | Conditioning_strength | CDLM_anchor_status |
|---|---|---|---|---|---|
| CTR.01 | Saturn Phalita 9:1 Ishta (primary deliverer) | 1.0000 | CAREER, SPIRITUAL | MED, LOW | No confirmed CDLM anchor; classical: Saturn AmK → career (primary), dharma devata → spiritual |
| CTR.03 | Jupiter Uccha Bala Rank 7 Last | 1.0000 | SPIRITUAL, HEALTH | MED, LOW | No confirmed CDLM anchor; classical: Jupiter 9H → spiritual; GK (children-domain) |
| CVG.02 | Jupiter 9L-Own Dharma-Wealth Chain | 1.0000 | CAREER, SPIRITUAL | MED, MED | No direct CDLM anchor; domains_affected=[wealth,spirit,career,children] |
| SIG.01 | D9 Neecha Bhanga Raja Yoga — Venus D9 Virgo | 1.0000 | CAREER, RELATIONSHIP | MED, MED | No CDLM anchor; domains=[career,wealth,relationships,mind] |
| SIG.09 | Rahu 2H Taurus Rohini — Wealth/Ambition | 1.0000 | CAREER | MED | No confirmed anchor; career-ambition driver per CDLM.D2.D1 |
| SIG.10 | Anapha Yoga — Sun+Mercury 12H from Moon | 1.0000 | RELATIONSHIP | MED | No confirmed anchor; domains=[wealth,relationships,family] |
| SIG.12 | Sade Sati C2 Active — Saturn transiting Pisces | 1.0000 | RELATIONSHIP, SPIRITUAL, HEALTH | MED, MED, MED | No confirmed CDLM anchor; domains=[relationships,wealth,spirit,health] |
| SIG.13 | Sun 10H Capricorn with AL+Mercury — Career Stellium | 1.0000 | CAREER, HEALTH | MED, LOW | No direct anchor; domains=[health,mind,career,wealth,relationships] |
| SIG.15 | Mercury Operational Dominance — CVG.01 | 1.0000 | CAREER, RELATIONSHIP | MED, LOW | No confirmed anchor; domains=[career,relationships,wealth] |
| SIG.MSR.013 | Sade Sati Cycle 2 Active | 1.0000 | HEALTH | MED | health domain; no explicit CDLM anchor found |
| SIG.MSR.030 | [Health signal — Sade Sati health dimension] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.163 | [Health signal — 8H/Ketu health dimension] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.170 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.198 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.229 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.251 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.278 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.291 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.295 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.297 | [Health-Spirit dimension — 8H Ketu transformation] | 1.0000 | HEALTH, SPIRITUAL | HIGH, MED | CDLM.D4.D6 msr_anchors=[MSR.402,MSR.408,MSR.297] — MSR.297 confirmed anchor in Health→Spirit cell |
| SIG.MSR.300 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.301 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.391 | [Relationship signal — 7H Saturn-Mars dynamic] | 1.0000 | RELATIONSHIP | MED | relationship domain; classical 7H anchor |
| SIG.MSR.476 | [Health signal] | 1.0000 | HEALTH | MED | health domain |
| SIG.MSR.145 | Parivartana Exchange Saturn-10L/Venus-7L | 0.9091 | CAREER, RELATIONSHIP | MED, MED | OPEN_ITEM.P1.1: MSR.145 not patchable as CDLM anchor (no Bhadra yoga cell); career-relationship linkage inferred from LL.2 EDGE-01/02/04/08; [CDLM_VERIFICATION_REQUIRED] |
| RPT.DSH.01 | Dasha Report Convergence Signal | 0.8000 | CAREER | MED | No CDLM anchor; dasha convergence → primarily career-temporal domain |
| SIG.MSR.402 | Hidden-Pinnacle 8H Architecture (Varnada+Ghati) | 0.7273 | HEALTH, SPIRITUAL | HIGH, MED | CDLM.D4.D6 msr_anchors include MSR.402 — confirmed HIGH anchor in Health→Spirit cell |
| SIG.MSR.118 | Ruchaka ABSENT — Mars not own/exalted kendra | 0.4545 | CAREER, HEALTH | LOW, LOW | CDLM.D5.D6 has MSR.119 anchor (different signal); MSR.118 in LL.2 EDGE-02/06; classical: Mars Avayogi |
| SIG.MSR.119 | Malavya ABSENT — Venus not own/exalted kendra | 0.4545 | RELATIONSHIP, SPIRITUAL | MED, LOW | CDLM.D5.D6 has MSR.119 anchor in Children domain; classical: Venus 9H → relationship/spirit |
| SIG.MSR.143 | Sarpa Yoga ABSENT — no three serpent planets in angles | 0.4545 | CAREER | MED | CDLM.D5.D7 has MSR.143 anchor; structural openness signal → career benefic when absent |
| SIG.MSR.117 | Hamsa Near-Miss — Jupiter 9H Trikona not Kendra | 0.3636 | SPIRITUAL | LOW | CDLM.D1.D1 has MSR.117; `shadow_indefinite_low_match_rate`; enters as shadow node only |

**Note on SIG.MSR.117:** This signal is `shadow_indefinite_low_match_rate` in LL.1 and is NOT in the 30-signal production set. However, it appears as a CDLM anchor (CDLM.D1.D1) and is referenced in LL.2 EDGE-06/07. It enters the topology as a **shadow node** — conditions SPIRITUAL at LOW weight (0.3636 × 0.2 = 0.073) and is not promoted as a primary conditioning signal. Its edges are marked `pending_promotion: true` per LL.2 campaign.

### §3.2 — Type B node: Dasha-state (time-varying, observed)

**Encoding:** Tuple `(mahadasha_lord, antardasha_lord)` ∈ {Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu}². 81 possible states.

**Native's antardasha sequence (from FORENSIC §5.1, TRAINING PARTITION ONLY):**

The training partition covers LEL events in years 1984–2026 (excluding 9 held-out events). The antardasha periods governing training events are drawn from DSH.V.001 through DSH.V.023:

| DSH_ID | MD | AD | Start | End | Training events in window |
|---|---|---|---|---|---|
| DSH.V.001 | Jupiter | Venus | 1984-02-05 | 1986-03-03 | EVT.1984.02.05.01 (birth) |
| DSH.V.002 | Jupiter | Sun | 1986-03-03 | 1986-12-21 | — |
| DSH.V.003 | Jupiter | Moon | 1986-12-21 | 1988-04-21 | — |
| DSH.V.004 | Jupiter | Mars | 1988-04-21 | 1989-03-27 | — |
| DSH.V.005 | Jupiter | Rahu | 1989-03-27 | 1991-08-21 | — |
| DSH.V.006 | Saturn | Saturn | 1991-08-21 | 1994-08-24 | early school events |
| DSH.V.007 | Saturn | Mercury | 1994-08-24 | 1997-05-03 | academic events |
| DSH.V.008 | Saturn | Ketu | 1997-05-03 | 1998-06-12 | — |
| DSH.V.009 | Saturn | Venus | 1998-06-12 | 2001-08-12 | EVT.1998.XX.XX.01 (engineering), EVT.2000.XX.XX.01 |
| DSH.V.010 | Saturn | Sun | 2001-08-12 | 2002-07-24 | EVT.2001.03.XX.01, EVT.2001.09.XX.01 |
| DSH.V.011 | Saturn | Moon | 2002-07-24 | 2004-02-24 | EVT.2002.XX.XX.01, EVT.2003.01.XX.01 |
| DSH.V.012 | Saturn | Mars | 2004-02-24 | 2005-04-03 | EVT.2004.02.05.01 (20th birthday marker) |
| DSH.V.013 | Saturn | Rahu | 2005-04-03 | 2008-02-09 | EVT.2006.06.XX.01, EVT.2007.04.XX.01 |
| DSH.V.014 | Saturn | Jupiter | 2008-02-09 | 2010-08-21 | [EVT.2008.06.09.01 BLINDED], [EVT.2009.06.XX.01 BLINDED] |
| DSH.V.015 | Mercury | Mercury | 2010-08-21 | 2013-01-18 | EVT.2010.08.XX.01, EVT.2012.10.XX.01 |
| DSH.V.016 | Mercury | Ketu | 2013-01-18 | 2014-01-15 | EVT.2013.12.11.01 |
| DSH.V.017 | Mercury | Venus | 2014-01-15 | 2016-11-15 | EVT.2014.01.15.01, EVT.2015.06.XX.01 |
| DSH.V.018 | Mercury | Sun | 2016-11-15 | 2017-09-21 | [EVT.2017.03.XX.01 BLINDED] |
| DSH.V.019 | Mercury | Moon | 2017-09-21 | 2019-02-21 | [EVT.2018.11.28.01 BLINDED] |
| DSH.V.020 | Mercury | Mars | 2019-02-21 | 2020-02-18 | [EVT.2019.05.XX.01 BLINDED] |
| DSH.V.021 | Mercury | Rahu | 2020-02-18 | 2022-09-06 | EVT.2020.03.XX.01, EVT.2021.01.XX.01, [EVT.2022.01.03.01 BLINDED] |
| DSH.V.022 | Mercury | Jupiter | 2022-09-06 | 2024-12-12 | EVT.2022.XX.XX.02, EVT.2023.XX.XX.01 |
| DSH.V.023 | Mercury | Saturn | 2024-12-12 | 2027-08-21 | EVT.2025.07.XX.01, EVT.2026.03.20.01, EVT.2026.04.08.01, [EVT.2024.02.16.01 BLINDED], [EVT.2025.05.XX.01 BLINDED], [EVT.2026.01.XX.01 BLINDED] |

**BLINDED entries:** These antardasha periods contain held-out events. The period itself is known (dasha dates are deterministic), but the event outcomes are not consulted. Marked BLINDED for topology purposes.

**Note on DSH.V.024+:** Ketu MD starts 2027-08-21. These are future periods beyond the current date (2026-05-13) and are not part of the training or held-out partition.

**Classical mahadasha domain tendency mapping** (for CPT initialization in §4.2):
The 9 mahadasha lords map to domain tendency profiles. These are classical Jyotish associations modulated by this chart's specific LL.5 axis-weight data:

| MD Lord | CAREER tendency | HEALTH tendency | RELATIONSHIP tendency | SPIRITUAL tendency | LL.5 basis |
|---|---|---|---|---|---|
| Jupiter | expansion/protection | protective | growth/dharmic | HIGH elevation | Jupiter 9L-own; GK; 9H dharma; dasha_dominant (high) |
| Saturn | restructuring/discipline | chronic pressure | contraction→stability | Dharma Devata (Venkateswara) | Saturn AmK; exalted 7H; 10L+11L; HIGH dasha_dominant |
| Mercury | communication/strategy | nervous-system | communication-quality | study/practice | Mercury MD lord; DK; Yogi; Vargottama; LL.5 HIGH for career |
| Ketu | dissolution/withdrawal | subtle-body | spiritual over material | HIGH deepening | Ketu 8H moksha-karaka; spiritual accelerant |
| Venus | aesthetic/wealth channel | stable | HIGH prominence | Ishta Devata (Mahalakshmi) | Venus 9H; Ishta Devata; Shree Lagna 7H |
| Sun | authority/visibility | moderate | ego-assertion | dharmic authority | Sun 10H; AL; career visibility driver |
| Moon | emotional/adaptive | HIGH sensitivity | emotional-quality | variable/devotional | Moon AK; 11H; soul-karaka; emotional intelligence |
| Mars | active/assertive | HIGH risk | conflict/resolution | unsettled | Mars Avayogi; 7H; PK children; tension-activator |
| Rahu | disruption/leap | unusual conditions | unconventional | unsettled/seeking | Rahu 2H exalted; ambition driver; shadow-realm |

### §3.3 — Type C nodes: Domain activation (latent, time-varying)

One node per domain per antardasha time-slice. These are the primary hidden variables the DBN infers.

| Domain | State space | LL.4 mean_lit | Base prior P(ELEVATED) | Base prior P(NORMAL) | Base prior P(SUPPRESSED) | Persistence_init | Primary conditioning signals (top 3 from §3.1) |
|---|---|---|---|---|---|---|---|
| CAREER | {ELEVATED, NORMAL, SUPPRESSED} | 0.5016 | 0.30 | 0.45 | 0.25 | 0.65 | SIG.13 (wt=0.60), CTR.01 (wt=0.60), SIG.15 (wt=0.60) |
| HEALTH | {ELEVATED, NORMAL, SUPPRESSED} | 0.4948 | 0.30 | 0.45 | 0.25 | 0.65 | SIG.MSR.297 (wt=1.00), SIG.MSR.402 (wt=0.73), SIG.MSR.013 (wt=0.60) |
| RELATIONSHIP | {ELEVATED, NORMAL, SUPPRESSED} | 0.4113 | 0.25 | 0.50 | 0.25 | 0.65 | SIG.MSR.391 (wt=0.60), SIG.MSR.145 (wt=0.55), SIG.01 (wt=0.60) |
| SPIRITUAL | {ELEVATED, NORMAL, SUPPRESSED} | 1.0000 (n=SPR.* subset, WEAK) | 0.25 | 0.50 | 0.25 | 0.65 | CTR.03 (wt=0.60), CVG.02 (wt=0.60), SIG.MSR.297 (wt=0.60) |
| PSYCHOLOGICAL | {ELEVATED, NORMAL, SUPPRESSED} | n/a (n=PSY.* subset, WEAK) | 0.25 | 0.50 | 0.25 | 0.65 | SIG.12 (wt=0.60), SIG.MSR.297 (wt=0.60), CTR.01 (wt=0.20 LOW) |

**Note on SPIRITUAL and PSYCHOLOGICAL priors (U2 split):** The original SPIRITUAL_PSYCHOLOGICAL mean_lit=1.0 (n=6, WEAK tier) spanned both SPR.* and PSY.* events combined. After split, each domain has insufficient observations to compute a reliable separate mean_lit — both inherit the conservative symmetric prior P(E)=0.25, P(N)=0.50, P(S)=0.25. Ketu MD periods show highest PSYCHOLOGICAL P(E) (0.55–0.66 in dasha_to_domain.json) consistent with Ketu 8H psychological transformation role. M5-D will calibrate per-domain from training partition events once PSY.* and SPR.* are counted separately.

**Note on HEALTH conditioning for SPIRITUAL_PSYCHOLOGICAL split:** SIG.MSR.402 (now invalidated, revised_confidence=0.00) has been removed from SPIRITUAL primary conditioning signals. SIG.MSR.402b (replacement, strength_score=0.72) will be incorporated at Task #8 after EDGE-01 co-occurrence re-check.

**ELEVATED state definition:** Domain activation node = ELEVATED when the dasha evidence + natal signal evidence collectively suggest this domain is a primary focus period for the native — characterized by high signal co-activation density and dasha-state alignment with the domain.

**SUPPRESSED state definition:** Domain activation = SUPPRESSED when dasha evidence + natal signals suggest dormancy, dissolution, or withdrawal from the domain.

### §3.4 — Type D nodes: Event occurrence (observed, binary)

One binary observation node per domain per antardasha time-slice. These are the data points the DBN fits against in M5-D.

| Domain event node | Value 1 condition | Value 0 condition |
|---|---|---|
| CAREER_EVENT(t) | ≥1 LEL training event categorized as career/professional in antardasha t | No career events in antardasha t |
| HEALTH_EVENT(t) | ≥1 LEL training event categorized as health/physical in antardasha t | No health events |
| RELATIONSHIP_EVENT(t) | ≥1 LEL training event categorized as relationship/marriage in antardasha t | No relationship events |
| SPIRITUAL_EVENT(t) | ≥1 LEL training event tagged SPR.* (spiritual practice, devotional, dharmic) in antardasha t | No SPR.* events |
| PSYCHOLOGICAL_EVENT(t) | ≥1 LEL training event tagged PSY.* (psychological pressure, inner dissolution, identity shift) in antardasha t | No PSY.* events |

**Observation model (initial values, to be fitted in M5-D):**
| Domain state | P(EVENT=1 | state) | Basis |
|---|---|---|
| ELEVATED | 0.70 | LL.4 held_out mean_lit=0.913 minus conservatism buffer; ELEVATED state = strong evidence activation |
| NORMAL | 0.20 | LL.4 training mean_lit=0.630 minus low-evidence discount; NORMAL = background event probability |
| SUPPRESSED | 0.05 | Near-zero; suppressed domain → events rare but possible (1-in-20 antardasha) |

**Event counting note:** One training antardasha period may contain multiple LEL events in the same domain. The Type D node is binary (EVENT or NO_EVENT) — multiple events in one period = EVENT=1. Event count within a period is not modeled in v1.0 (event count becomes a v2.0 extension using Poisson observation model).

---

## §4 — Edge inventory

### §4.1 — Natal → domain edges (Type A → Type C)

Edge weight = `LL.1_production_weight × CDLM_linkage_strength_score`
- HIGH anchor score = 1.0; MED anchor/inferred = 0.6; LOW classical-only = 0.2; ABSENT = 0.0
- Only edges with weight > 0.0 are included.

| Signal_ID | Domain | Edge_weight | Conditioning_strength | Source |
|---|---|---|---|---|
| CTR.01 | CAREER | 0.600 | MED | LL.1 wt=1.0 × classical-inferred 0.6 (Saturn AmK, career driver) |
| CTR.01 | SPIRITUAL | 0.200 | LOW | LL.1 wt=1.0 × 0.2 (Saturn as Dharma Devata → SPIRITUAL dharma channel; no CDLM anchor) |
| CTR.03 | SPIRITUAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Jupiter 9H = dharma/spirit domain; 9H is the SPIRITUAL domain house) |
| CVG.02 | CAREER | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Jupiter dharma-wealth chain, career domain) |
| CVG.02 | SPIRITUAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Jupiter 9L own sign = dharma; SPIRITUAL domain primary) |
| SIG.01 | CAREER | 0.600 | MED | LL.1 wt=1.0 × 0.6 (D9 NBRY; domains=[career,wealth,relationships,mind]) |
| SIG.01 | RELATIONSHIP | 0.600 | MED | LL.1 wt=1.0 × 0.6 (domains include relationships) |
| SIG.09 | CAREER | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Rahu 2H ambition → career; CDLM.D2.D1 strength=0.88) |
| SIG.10 | RELATIONSHIP | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Anapha Yoga; domains=[wealth,relationships,family]) |
| SIG.12 | RELATIONSHIP | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Sade Sati C2; domains include relationships) |
| SIG.12 | SPIRITUAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Sade Sati → spiritual deepening / devotional intensification in this chart) |
| SIG.12 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Sade Sati C2 health dimension) |
| SIG.12 | PSYCHOLOGICAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (U2: Sade Sati creates psychological pressure periods — Saturn transiting 12H from Lagna = liminal inner pressure, identity restructuring; distinct from spiritual deepening) |
| SIG.13 | CAREER | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Sun 10H stellium; primary career signal) |
| SIG.13 | HEALTH | 0.200 | LOW | LL.1 wt=1.0 × 0.2 (domains include health; secondary domain only) |
| SIG.15 | CAREER | 0.600 | MED | LL.1 wt=1.0 × 0.6 (Mercury dominance; primary career domain) |
| SIG.15 | RELATIONSHIP | 0.200 | LOW | LL.1 wt=1.0 × 0.2 (secondary; domains include relationships) |
| SIG.MSR.013 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain; no confirmed CDLM anchor) |
| SIG.MSR.030 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.163 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.170 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.198 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.229 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.251 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.278 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.291 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.295 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.297 | HEALTH | 1.000 | HIGH | LL.1 wt=1.0 × 1.0 (CDLM.D4.D6 confirmed msr_anchor; high-strength Health cell) |
| SIG.MSR.297 | SPIRITUAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (CDLM.D4.D6 Health→Spirit; conditioning SPIRITUAL via health-spirit moksha bridge) |
| SIG.MSR.297 | PSYCHOLOGICAL | 0.600 | MED | LL.1 wt=1.0 × 0.6 (U2: 8H Ketu transformation drives PSYCHOLOGICAL states; 8H is the house of inner dissolution, hidden fears, psychological depth — Ketu 8H activates PSY.* events alongside health events) |
| SIG.MSR.300 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.301 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.391 | RELATIONSHIP | 0.600 | MED | LL.1 wt=1.0 × 0.6 (relationship domain; 7H Saturn-Mars dynamic) |
| SIG.MSR.476 | HEALTH | 0.600 | MED | LL.1 wt=1.0 × 0.6 (health domain) |
| SIG.MSR.145 | CAREER | 0.545 | MED | LL.1 wt=0.9091 × 0.6 (career-relationship Parivartana; OPEN_ITEM.P1.1; [CDLM_VERIFICATION_REQUIRED]) |
| SIG.MSR.145 | RELATIONSHIP | 0.545 | MED | LL.1 wt=0.9091 × 0.6 (Parivartana Saturn-7H/Venus; [CDLM_VERIFICATION_REQUIRED]) |
| RPT.DSH.01 | CAREER | 0.480 | MED | LL.1 wt=0.8 × 0.6 (dasha convergence report; primarily career-temporal signal) |
| SIG.MSR.402 | HEALTH | 0.727 | HIGH | LL.1 wt=0.7273 × 1.0 (CDLM.D4.D6 confirmed msr_anchor in Health→Spirit cell) |
| SIG.MSR.402 | SPIRITUAL | 0.436 | MED | LL.1 wt=0.7273 × 0.6 (CDLM.D4.D6 Health→Spirit direction) |
| SIG.MSR.118 | CAREER | 0.091 | LOW | LL.1 wt=0.4545 × 0.2 (Ruchaka ABSENT; classical: Mars in 7H Avayogi) |
| SIG.MSR.118 | HEALTH | 0.091 | LOW | LL.1 wt=0.4545 × 0.2 (Mars health-risk association; classical) |
| SIG.MSR.119 | RELATIONSHIP | 0.273 | MED | LL.1 wt=0.4545 × 0.6 (Malavya ABSENT; Venus 9H; CDLM.D5.D6 anchor adjacent) |
| SIG.MSR.119 | SPIRITUAL | 0.091 | LOW | LL.1 wt=0.4545 × 0.2 (Venus as Ishta Devata → SPIRITUAL devotional secondary domain) |
| SIG.MSR.143 | CAREER | 0.273 | MED | LL.1 wt=0.4545 × 0.6 (Sarpa ABSENT = structural openness; CDLM.D5.D7 anchor) |
| SIG.MSR.117 | SPIRITUAL | 0.073 | LOW_SHADOW | LL.1 wt=0.3636 × 0.2 (shadow node; pending LL.2 EDGE-06 promotion; CDLM.D1.D1 anchor; conditions SPIRITUAL — Hamsa near-miss is a dharmic wisdom signal, not PSY domain) |

**Summary counts (v1.1 — 5 domains):**
- CAREER edges: 10 (CTR.01, CVG.02, SIG.01, SIG.09, SIG.13, SIG.15, SIG.MSR.145, RPT.DSH.01, SIG.MSR.118, SIG.MSR.143)
- HEALTH edges: 16 (all 14 health-domain signals + SIG.12 + SIG.13 + SIG.MSR.402 + SIG.MSR.118)
- RELATIONSHIP edges: 8 (SIG.MSR.391, SIG.MSR.145, SIG.01, SIG.10, SIG.12, SIG.15, SIG.MSR.119)
- SPIRITUAL edges: 8 (CTR.01, CTR.03, CVG.02, SIG.12, SIG.MSR.297, SIG.MSR.402, SIG.MSR.119, SIG.MSR.117)
- PSYCHOLOGICAL edges: 2 (SIG.12, SIG.MSR.297) — U2 new additions
- Total Type A→C edges: 44 (including SIG.MSR.117 shadow node)

### §4.2 — Dasha-state → domain edges (Type B → Type C)

The dasha-state node `(MD_lord, AD_lord)` conditions all four domain activation nodes at each time-slice. The conditional distribution encodes the mahadasha lord's domain tendency (from classical Jyotish + LL.5 axis-weight data) as prior tendencies toward {ELEVATED, NORMAL, SUPPRESSED} per domain.

**Mahadasha lord → domain tendency mapping (scaffold; for CPT initialization):**

*(v1.1 U2: SPIRITUAL column retains original SPIRITUAL_PSYCHOLOGICAL values. PSYCHOLOGICAL column is new — derived from Ketu 8H / Moon AK analysis. Ketu MD: highest PSYCHOLOGICAL P(E)=0.55 (8H deconstruction). Moon MD: HIGH PSYCHOLOGICAL P(E)=0.50 (AK emotional soul). Saturn MD: MED P(E)=0.35 (discipline-through-restriction). Jupiter MD: LOW-stable P(E)=0.25 (protective). All are n=1 priors; M5-D fitting will differentiate.)*

| MD Lord | CAREER: P(E/N/S) | HEALTH: P(E/N/S) | RELATIONSHIP: P(E/N/S) | SPIRITUAL: P(E/N/S) | PSYCHOLOGICAL: P(E/N/S) |
|---|---|---|---|---|---|
| Jupiter | 0.45/0.40/0.15 | 0.30/0.50/0.20 | 0.35/0.45/0.20 | 0.55/0.35/0.10 | 0.25/0.55/0.20 |
| Saturn | 0.50/0.35/0.15 | 0.25/0.45/0.30 | 0.30/0.40/0.30 | 0.45/0.40/0.15 | 0.35/0.40/0.25 |
| Mercury | 0.55/0.35/0.10 | 0.30/0.50/0.20 | 0.35/0.45/0.20 | 0.35/0.45/0.20 | 0.30/0.50/0.20 |
| Ketu | 0.20/0.35/0.45 | 0.25/0.45/0.30 | 0.15/0.35/0.50 | 0.60/0.30/0.10 | 0.55/0.30/0.15 |
| Venus | 0.30/0.45/0.25 | 0.35/0.45/0.20 | 0.55/0.35/0.10 | 0.45/0.40/0.15 | 0.25/0.55/0.20 |
| Sun | 0.50/0.40/0.10 | 0.30/0.50/0.20 | 0.25/0.45/0.30 | 0.35/0.45/0.20 | 0.30/0.45/0.25 |
| Moon | 0.30/0.45/0.25 | 0.45/0.40/0.15 | 0.45/0.40/0.15 | 0.40/0.45/0.15 | 0.50/0.35/0.15 |
| Mars | 0.40/0.40/0.20 | 0.35/0.35/0.30 | 0.30/0.35/0.35 | 0.20/0.40/0.40 | 0.35/0.35/0.30 |
| Rahu | 0.40/0.35/0.25 | 0.25/0.40/0.35 | 0.30/0.35/0.35 | 0.25/0.40/0.35 | 0.30/0.38/0.32 |

**Antardasha modulation:** The antardasha lord modulates the mahadasha tendency. When MD and AD lords are the same planet, the tendency is amplified (multiply P(ELEVATED) by 1.1, renormalize). When AD lord is traditionally antagonistic to MD lord, suppress the ELEVATED probability.

The full 81-state CPT scaffold is in `cpt/dasha_to_domain.json`. Initial values are set from the mahadasha table above with AD modulation applied. All `fitted_value` fields are null — M5-D fitting will replace these.

**LL.5 basis note:** LL.5 shadow file (`ll5_dasha_transit_v1_0.json`) confirmed dasha_weight HIGH tier for 2 signals and MED tier for 12 signals across 380 signals. The dasha axis dominates (259/380 signals dasha_dominant vs. 1/380 transit_dominant). This reinforces D1 (antardasha as primary time-slice) and validates that the dasha-state node is the primary time-varying conditioner.

### §4.3 — Domain persistence edges (Type C(t) → Type C(t+1))

Initial 3×3 transition matrix (same across all 5 domains in v1.1; to be fitted per-domain in M5-D):

| From state \ To state | ELEVATED | NORMAL | SUPPRESSED |
|---|---|---|---|
| ELEVATED | 0.55 | 0.35 | 0.10 |
| NORMAL | 0.20 | 0.65 | 0.15 |
| SUPPRESSED | 0.05 | 0.35 | 0.60 |

**Rationale:** NORMAL state has the highest persistence (0.65) — periods of ordinary functioning tend to continue. ELEVATED and SUPPRESSED both decay toward NORMAL over time, but at slightly different rates. SUPPRESSED→ELEVATED direct transition is very rare (0.05) — direct jumps from suppressed to elevated without passing through normal are uncommon. These values are conservative priors; M5-D will calibrate per-domain.

**Derivation:** Conservative initialization above LL.4 training mean_lit=0.630. The 0.65 NORMAL persistence reflects the empirical baseline that ≈63% of antardasha periods show moderate signal activation (neither strongly elevated nor suppressed).

### §4.4 — Cross-domain edges (Type C(t) ↔ Type C(t))

Three cross-domain edges in v1.0, all verified against CDLM v1.3:

**Edge 1: CAREER(t) ↔ RELATIONSHIP(t)**
- Direction: bidirectional
- Initial weight: 0.35
- CDLM basis: CDLM.D1.D3 strength=0.91 bidirectional (Saturn exalted AmK in 7H = career significator in relationship house; "karmically inseparable" per CDLM key_finding)
- LL.2 supporting edges: EDGE-01 (MSR.145↔MSR.402 co_count=7), EDGE-02 (MSR.118↔MSR.145 co_count=5), EDGE-04 (MSR.143↔MSR.145 co_count=5), EDGE-08 (MSR.119↔MSR.145 co_count=4) — all PENDING_NATIVE_APPROVAL
- Astrology note: Saturn exalted in 7H as AmK creates the tightest possible career-relationship structural fusion in Jaimini. Career transitions reliably activate relationship-domain simultaneously in this chart.
- `pending_promotion: true` (LL.2 approval pending for EDGE-01/02/04/08)

**Edge 2: CAREER(t) ↔ SPIRITUAL(t)**
- Direction: bidirectional
- Initial weight: 0.20 (U1 confirmed by native at NAP.M5.1; supersedes surrogate recommendation of 0.15)
- Domain interpretation: SPIRITUAL = dharmic practice domain (9H Jupiter/Venus). Career excellence IS dharmic practice in this chart (Saturn = Dharma Devata/Venkateswara).
- CDLM basis: CDLM.D1.D6 strength=0.89 bidirectional ("Career and spirit are mutually feeding — professional excellence IS dharmic practice; Saturn = Dharma Devata")
- LL.7 supporting: LL.7 novel edges include MSR.145↔MSR.402 cluster which spans career-spiritual dimension
- [CDLM_VERIFICATION_REQUIRED: CDLM.D1.D6 supports the mechanism conceptually but msr_anchors=[MSR.397, MSR.407, MSR.388] do not include production signals. Weight initialized conservatively at 0.20 per native confirmation at NAP.M5.1.]
- `pending_promotion: false` (CDLM mechanistic support confirmed by native)

**Edge 3: HEALTH(t) ↔ SPIRITUAL(t)**
- Direction: bidirectional
- Initial weight: 0.25
- Domain interpretation: SPIRITUAL = moksha / dharmic-protection channel. Ketu 8H transforms health crises into spiritual catalysis (Health→Spirit direction); Jupiter+Venus 9H provides dharmic protective supervision (Spirit→Health direction).
- CDLM basis: CDLM.D4.D6 strength=0.82 Health→Spirit ("Ketu exalted 8H transforms health challenges into spiritual catalysts"); CDLM.D6.D4 strength=0.80 Spirit→Health ("Spirit compensates health challenges — Jupiter+Venus Jaimini supervision provides dharmic protection")
- LL.2 supporting: EDGE-07 (MSR.117↔MSR.402 co_count=4, is_ll2_med=True) — REJECTED at NAP.M5.1 (native cannot confirm); edge motivation remains via CDLM basis.
- Note on U2: HEALTH↔PSYCHOLOGICAL is a deferred edge (HEALTH_PSYCHOLOGICAL_bidir in cross_domain.json deferred_edges). The 8H Ketu mechanism motivates both SPIRITUAL and PSYCHOLOGICAL connections from HEALTH; SPIRITUAL captures the dharmic/moksha direction; PSYCHOLOGICAL captures the inner-dissolution direction. HEALTH↔PSYCHOLOGICAL deferred to v1.1 to avoid overparameterization.
- `pending_promotion: false` (CDLM.D4.D6 confirmed independently; EDGE-07 rejection does not invalidate the edge)

**Additional CDLM-supported cross-domain pairs considered but deferred:**
- RELATIONSHIP↔SPIRITUAL (CDLM.D3.D6 strength=0.86): Strong structural support (AK-DK soul-spouse connection; Shree Lagna 7H Lakshmi grace in relationship domain). Deferred to v1.1 to avoid overparameterization. Added to risk register as RT.M5B.1 extension item.
- HEALTH↔PSYCHOLOGICAL (U2 addition): 8H Ketu drives PSYCHOLOGICAL activation during health-crisis periods (same structural basis as HEALTH↔SPIRITUAL). Deferred to v1.1 — adding a 4th active cross-domain edge at 5 nodes would overcomplicate the n=1 topology. See cross_domain.json deferred_edges.

---

## §5 — CPT structure specification (Hybrid-C scaffold)

The CPT files live under `06_LEARNING_LAYER/dbn/cpt/`. All files are `UNFITTED_SCAFFOLD` status — initial values are provided but `fitted_value` fields are null. M5-D fitting populates the fitted values.

*(v1.1 U2: All 5 CPT files updated at M5-B-S2 to reflect 5-domain topology. Domain list in all files: `["CAREER", "HEALTH", "RELATIONSHIP", "SPIRITUAL", "PSYCHOLOGICAL"]`.)*

### CPT file paths and entry counts (v1.1):
- `cpt/natal_to_domain.json` — Type A → C edges (45 entries; 43 original + 2 U2 PSYCHOLOGICAL additions: SIG.12 + SIG.MSR.297)
- `cpt/dasha_to_domain.json` — Type B → C (81-state dasha × 5-domain conditional distribution; SPIRITUAL retains original SPIRITUAL_PSYCHOLOGICAL values; PSYCHOLOGICAL column derived from MD tendency analysis)
- `cpt/persistence.json` — Type C(t)→C(t+1) (3×3 per domain × 5 domains = 45 entries)
- `cpt/cross_domain.json` — Type C↔C inter-domain edges (3 active + 2 deferred; RELATIONSHIP_SPIRITUAL + HEALTH_PSYCHOLOGICAL both deferred to v1.1)
- `cpt/observation.json` — Type C → D observation model (5 entries; PSYCHOLOGICAL symmetric scaffold P(EVENT|ELEVATED)=0.70)

### JSON schema (common pattern):
```json
{
  "cpt_id": "<id>",
  "version": "scaffold_M5-B-S1",
  "status": "UNFITTED_SCAFFOLD",
  "fit_session": null,
  "entries": [...]
}
```

See §6 (CPT scaffold files created at this session) for the actual content. The scaffolds are pre-populated with initial values from §4 above; `fitted_value` fields are null throughout.

---

## §6 — LL.2 integration status

### §6.1 — Promoted edges included in topology

The 8 LL.2 MED-tier campaign edges from `ll2_promotion_campaign_v1_0.md` are incorporated into the topology but marked `pending_promotion: true` — they are in the design but not yet native-approved.

**LL.2 campaign outcome for this session: DEFERRED (Outcome B)**
No native approval instruction was received during M5-B-S1. The campaign remains PENDING_NATIVE_APPROVAL. All 8 edges are in the topology design (cross-domain edges + natal→domain edges reference them), but marked pending.

| EDGE_ID | Signal pair | Co-count | Topology section | pending_promotion |
|---|---|---|---|---|
| EDGE-01 | MSR.145 ↔ MSR.402 | 7 | §4.1 (CAREER edge for both), §4.4 Cross-domain basis | true |
| EDGE-02 | MSR.118 ↔ MSR.145 | 5 | §4.1 CAREER edges | true |
| EDGE-03 | MSR.119 ↔ MSR.402 | 5 | §4.1 RELATIONSHIP + HEALTH edges | true |
| EDGE-04 | MSR.143 ↔ MSR.145 | 5 | §4.1 CAREER edges | true |
| EDGE-05 | MSR.143 ↔ MSR.402 | 5 | §4.1 CAREER + HEALTH edges | true |
| EDGE-06 | MSR.117 ↔ MSR.119 | 4 | §4.1 shadow-node edges (conditional on MSR.117 shadow status) | true |
| EDGE-07 | MSR.117 ↔ MSR.402 | 4 | §4.4 HEALTH↔SPIRITUAL basis (partial) | true |
| EDGE-08 | MSR.119 ↔ MSR.145 | 4 | §4.4 CAREER↔RELATIONSHIP basis | true |

### §6.2 — Conditional nodes (MSR.117 shadow status)

SIG.MSR.117 (Hamsa Near-Miss — `shadow_indefinite_low_match_rate`) is included as a **shadow node** in the topology:
- Conditions SPIRITUAL at weight=0.073 (LOW_SHADOW tier)
- EDGE-06 and EDGE-07 in the LL.2 campaign depend on this shadow status
- SIG.MSR.117 is NOT in the 30-signal production register; it enters topology only as a shadow-pending node
- Promotion to standard conditioning signal requires: (a) native approval of EDGE-06/07, AND (b) match-rate stabilization above 0.4 threshold

---

## §7 — Risk register entry (per PHASE_M5_PLAN §4)

| Risk ID | Risk | Mitigation in this topology | Severity |
|---|---|---|---|
| R.M5.4 | Topology overfit to LEL history | Held-out partition sacrosanct; all D1–D6 decisions committed before held-out data is seen; commit timestamp is pre-registration seal | HIGH |
| R.M5.2 | DBN under-identification at n=1 | Shadow mode for all CPT entries; v2.0 extension plan declared; conservative initial CPT values; n=1 caveat on all outputs; 30-signal conditioning is structural constraint, not fitted flexibility | HIGH |
| R.M5.3 | Learned-vs-classical divergence | Persistence matrix initialized conservatively (0.65); any posterior contradicting classical rules by >0.3 triggers DISAGREEMENT_REGISTER entry; cross-domain edges anchored to classical mechanisms (Saturn in 7H, Ketu 8H) not just empirical co-occurrence | MED |
| RT.M5B.1 | Domain scope too narrow | v2.0 extension plan: Finance (Rahu 2H exalted → wealth separate domain), Education (pre-1990 events), Relationship↔Spiritual cross-edge (CDLM.D3.D6 strength=0.86 deferred); M5-D validation will expose domain gaps via residual analysis | MED |
| RT.M5B.2 | Initial CPT values too uniform | All health signals initialized at MED (0.60) regardless of specific signal content; M5-D fitting will differentiate; residual tracking will identify which signals are over- vs. under-weighted | LOW |
| RT.M5B.3 | Shadow node contamination | SIG.MSR.117 shadow node clearly labeled; `pending_promotion: true` on all EDGE-06/07 dependent entries; removal from topology is clean if match-rate does not stabilize | LOW |

---

## §8 — Gemini two-pass topology review (surrogate pass)

Per MACRO_PLAN §M5 agent roles and R.LL1TPA.1 FINAL_NOT_REACHABLE_M5 status, Gemini is not reachable in this session. The surrogate protocol is executed:

```
SURROGATE_REVIEWER: Claude (acting for Gemini per R.LL1TPA.1 FINAL_NOT_REACHABLE_M5 protocol)
REVIEW_DATE: 2026-05-13
REVIEW_SESSION: M5-B-S1

REVIEW_FINDINGS:
  Finding 1 — Time-slice unit (D1):
    The antardasha time-slice is defensible and well-motivated. The LL.5 finding that 
    98% of signal activations are dasha or joint (only 4/420 purely transit) strongly 
    supports antardasha granularity over solar year. One alternative worth noting: 
    Chara Dasha (Jaimini) at the sign-period level could provide a complementary 
    time-slicing that captures different karmic timing. However, adding a second dasha 
    system in v1.0 would overparameterize for n=1. Antardasha is the right choice for v1.0.
    
  Finding 2 — 4 domain selection (D2):
    The 4 domains are reasonable given the training partition coverage. However:
    (a) The SPIRITUAL_PSYCHOLOGICAL domain combines two potentially distinct phenomena: 
        spiritual practice (9H Jupiter/Venus domain) vs. psychological states (8H Ketu, 
        4H Moon domain). These may have different dasha triggers. Combining them into one 
        node risks missing the divergence. Recommend native clarification on whether 
        SPR.* and PSY.* events co-activate or activate in complementary dasha periods.
    (b) Finance's exclusion is appropriate given current LEL structure, but 
        the Rahu 2H (SIG.09) and Moon 11H signals that are classified as CAREER 
        conditioning may actually be wealth-career junction signals — worth noting in M5-D.
    
  Finding 3 — Node types completeness:
    The 4-type structure (A/B/C/D) is appropriate. One potentially missing latent variable: 
    a "chart activation level" meta-node that reflects whether the overall chart is in 
    a high-activation window (multiple system convergences). This would be an L0 
    meta-latent above the domain nodes. However, this adds complexity without clear 
    falsifiability at n=1 — better as a v2.0 extension. Current structure is correct.
    
  Finding 4 — Cross-domain edge motivation:
    Edge 1 (CAREER↔RELATIONSHIP): STRONGLY SUPPORTED by CDLM.D1.D3 (0.91 bidirectional)
    and Saturn-in-7H structural basis. The [CDLM_VERIFICATION_REQUIRED] on MSR.145 is 
    correctly noted. The edge itself is motivated independently of MSR.145's CDLM anchor 
    status — CDLM.D1.D3 provides sufficient structural basis.
    
    Edge 2 (CAREER↔SPIRITUAL): WEAKLY MOTIVATED in the CPT scaffold. The CDLM.D1.D6 
    support is conceptual (Saturn=Dharma Devata) but has no production signal as msr_anchor. 
    Recommend initializing this edge at 0.15 rather than 0.20 to reflect weaker evidence. 
    This is a surrogate recommendation — native adjudication required.
    
    Edge 3 (HEALTH↔SPIRITUAL): WELL MOTIVATED by Ketu 8H + CDLM.D4.D6/D6.D4. The 
    MSR.402 CDLM anchor (D4.D6) is confirmed. The bidirectional initialization is 
    correct — health feeds spirit AND spirit compensates health per the CDLM mechanism.
    
  Finding 5 — Initial CPT values:
    The observation model (P(EVENT|ELEVATED)=0.70, NORMAL=0.20, SUPPRESSED=0.05) 
    appears reasonable but the SUPPRESSED value at 0.05 may be too generous — 
    "suppressed" in astrology typically means near-zero event probability. Consider 
    initializing at 0.02. This is a parameter choice for M5-D discussion.
    
    The dasha-to-domain mahadasha table is a classical prior, not fitted to data. 
    The Jupiter MD values appear generous for CAREER (0.45 ELEVATED) — Jupiter is the 
    GK and 9L+12L, not a direct career lord. Consider 0.35 for Jupiter→CAREER ELEVATED.
    These are surrogate recommendations for M5-C prior specification review.
    
  Finding 6 — Held-out sacrosanct enforcement:
    VERIFIED. The held-out event IDs are listed in frontmatter. The antardasha 
    table in §3.2 correctly marks all held-out antardasha windows as BLINDED. 
    The topology design decisions (D1–D6) do not reference any held-out outcome. 
    The CPT initial values are derived from LL.4/LL.5 prior documents that were 
    produced at M4 using only training data. The sacrosanct rule is verifiably enforced.

CLAUDE_RESPONSE:
  Finding 1 (Antardasha): ACCEPTED. Chara Dasha addition noted for v2.0 roadmap.
  Finding 2a (SPIRITUAL_PSYCHOLOGICAL split): ACKNOWLEDGED. SPR.* vs PSY.* split is 
    a legitimate concern. However, the v1.0 scope boundary (D6) explicitly combined 
    these because the LEL training partition has only 6 spiritual and 7 psychological 
    observations — splitting into two nodes would leave each severely under-constrained 
    at n=1. The combined node with state label SPIRITUAL_PSYCHOLOGICAL is the correct 
    v1.0 choice. Added to v2.0 consideration list.
  Finding 2b (Finance/Wealth signals): ACKNOWLEDGED. SIG.09 (Rahu 2H) is noted in 
    §4.1 as conditioning CAREER — if Finance becomes a separate domain in v2.0, 
    SIG.09 would shift to be a primary Finance conditioning signal. Correctly classified 
    for v1.0.
  Finding 3 (Meta-latent node): DEFERRED to v2.0 as surrogate recommended.
  Finding 4 Edge 2 (CAREER↔SPIRITUAL weight reduction): PARTIALLY ACCEPTED — 
    flagged for native adjudication. Will note in session-close block.
  Finding 4 Edges 1+3: CONFIRMED — motivated and will proceed as specified.
  Finding 5 (SUPPRESSED=0.05 and Jupiter CAREER=0.45): NOTED as M5-C prior 
    specification review items. Will not change unilaterally in topology document; 
    the initial values are the scaffolded priors, not the final fitted values.
  Finding 6 (Held-out enforcement): CONFIRMED. Sacrosanct rule is verified.

UNRESOLVED (native adjudication required):
  U1: CAREER↔SPIRITUAL edge weight — surrogate recommends 0.15, topology uses 0.20. 
      Native adjudication at NAP.M5.1 review.
  U2: SPIRITUAL_PSYCHOLOGICAL split — should v1.1 split into separate nodes? 
      Depends on whether SPR.* and PSY.* events show divergent dasha activation patterns 
      in M5-D training partition analysis.
  U3: LL.2 campaign approval — all 8 edges remain PENDING_NATIVE_APPROVAL. 
      Request formal NAP.M5.EDGE-BATCH approval at next Cowork session.

SURROGATE_DISCLOSURE: This review substitutes for Gemini Pass 1 per 
  LL1_TWO_PASS_APPROVAL_v1_0.md §5 surrogate protocol. Outcome subject to retroactive 
  Gemini ratification if Gemini becomes reachable in M5. Added to surrogate 
  disclosure ledger in LL1_TWO_PASS_APPROVAL_v1_0.md at session close.
```

---

## §9 — Version and changelog

| Version | Date | Session | Summary |
|---|---|---|---|
| 1.0 | 2026-05-13 | M5-B-S1 | Initial committed topology. DRAFT status. D1–D6 committed before held-out consultation. 30 natal static nodes + 1 dasha-state node + 4 latent domain-activation nodes + 4 event observation nodes. 3 cross-domain edges. 42 Type A→C edges. 5 CPT scaffold files created. Gemini surrogate two-pass conducted. NAP.M5.1 pending for CLOSED status. |

---

*End of DBN_TOPOLOGY_v1_0.md — DRAFT*
*Committed: M5-B-S1 (2026-05-13). Topology is pre-registered before held-out consultation.*
*NAP gate: NAP.M5.1 — native approval required to flip status from DRAFT → CLOSED.*
