---
artifact: CONTRADICTION_REGISTER_v1_1.md
version: "1.1"
status: CURRENT
supersedes: CONTRADICTION_REGISTER_v1_0.md
expose_to_chat: true
native_id: "abhisek"
layer: "L3.5"
produced_by_session: KARN-W5-R3-RES-CON-EXPANSION
produced_at: 2026-04-30
canonical_source: 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json
schema: 06_LEARNING_LAYER/SCHEMAS/contradiction_schema_v0_1.json
changelog:
  - v1.0 (2026-04-27, Madhav_M2A_Exec_11): Initial scaffold — 8 contradictions (Gemini Pass-2).
  - v1.1 (2026-04-30, KARN-W5-R3-RES-CON-EXPANSION): Expanded to 27 contradictions. CON.009–CON.027 added via two-pass Claude protocol. Two Pass-2 revisions: CON.013 (medium→high), CON.025 (cross_ref CON.010 added). CON.016 verification note added.
---

# CONTRADICTION REGISTER v1.1 — MARSYS-JIS Discovery Layer

## §1 — About This Register

Confirmed internal corpus contradictions. CON.001–CON.008 carried forward from v1.0 (Gemini Pass-1+2).
CON.009–CON.027 added via two-pass Claude protocol (session KARN-W5-R3-RES-CON-EXPANSION, 2026-04-30).

**v1.1 class distribution:**

| Class | Count | IDs |
|---|---|---|
| signal_polarity_conflict | 5 | CON.001, CON.009–CON.012 |
| system_divergence | 5 | CON.013–CON.017 |
| temporal_paradox | 5 | CON.018–CON.022 |
| frame_conflict | 5 | CON.023–CON.027 |
| karaka_ambiguity (legacy) | 1 | CON.002 |
| domain_cross_claim (legacy) | 2 | CON.003, CON.007 |
| p6_uvc_conflict (legacy) | 1 | CON.004 |
| timing_conflict (legacy) | 1 | CON.005 |
| p1_layer_bleed (legacy) | 1 | CON.006 |
| classical_basis_conflict (legacy) | 1 | CON.008 |

Total: **27 contradictions**

---

## §2 — Contradiction Index

| contradiction_id | contradiction_class | domains_implicated | severity | verdict |
|---|---|---|---|---|
| CON.001 | signal_polarity_conflict | relationships, career | HIGH | CONFIRMED (Gemini) |
| CON.002 | karaka_ambiguity | career, spiritual, mind | HIGH | CONFIRMED (Gemini) |
| CON.003 | domain_cross_claim | children, health | HIGH | CONFIRMED (Gemini) |
| CON.004 | p6_uvc_conflict | wealth | MED | CONFIRMED (Gemini) |
| CON.005 | timing_conflict | career, mind | MED | CONFIRMED (Gemini) |
| CON.006 | p1_layer_bleed | career, parents | MED | CONFIRMED (Gemini) |
| CON.007 | domain_cross_claim | wealth, career, mind | MED | CONFIRMED (Gemini) |
| CON.008 | classical_basis_conflict | wealth, spiritual | MED | CONFIRMED (Gemini) |
| CON.009 | signal_polarity_conflict | career, mind, spiritual | high | ACCEPTED (Claude Pass-2) |
| CON.010 | signal_polarity_conflict | career, health | high | ACCEPTED (Claude Pass-2) |
| CON.011 | signal_polarity_conflict | spiritual, parents, wealth | medium | ACCEPTED (Claude Pass-2) |
| CON.012 | signal_polarity_conflict | travel, wealth, mind | medium | ACCEPTED (Claude Pass-2) |
| CON.013 | system_divergence | career, spiritual, relationships | high | ACCEPTED (Claude Pass-2, severity revised) |
| CON.014 | system_divergence | career, relationships, spiritual | high | ACCEPTED (Claude Pass-2) |
| CON.015 | system_divergence | relationships, parents, wealth | medium | ACCEPTED (Claude Pass-2) |
| CON.016 | system_divergence | career, parents, spiritual | low | ACCEPTED (Claude Pass-2, verification note) |
| CON.017 | system_divergence | wealth, travel, mind | medium | ACCEPTED (Claude Pass-2) |
| CON.018 | temporal_paradox | career, wealth, mind, spiritual | low | ACCEPTED (Claude Pass-2) |
| CON.019 | temporal_paradox | career, wealth, spiritual, parents | low | ACCEPTED (Claude Pass-2) |
| CON.020 | temporal_paradox | career, spiritual, mind | high | ACCEPTED (Claude Pass-2) |
| CON.021 | temporal_paradox | career, spiritual | medium | ACCEPTED (Claude Pass-2) |
| CON.022 | temporal_paradox | career, wealth, spiritual | medium | ACCEPTED (Claude Pass-2) |
| CON.023 | frame_conflict | relationships, career | high | ACCEPTED (Claude Pass-2) |
| CON.024 | frame_conflict | spiritual, health | high | ACCEPTED (Claude Pass-2) |
| CON.025 | frame_conflict | career, health | **critical** | ACCEPTED (Claude Pass-2; cross_ref CON.010) |
| CON.026 | frame_conflict | career, relationships, mind | high | ACCEPTED (Claude Pass-2) |
| CON.027 | frame_conflict | wealth, relationships, spiritual | medium | ACCEPTED (Claude Pass-2) |

---

## §3 — v1.1 New Entries Detail (CON.009–CON.027)

### CON.009 — signal_polarity_conflict (severity: high)
- **hypothesis_text:** SIG.MSR.001 (Sasha Mahapurusha Yoga — Saturn authority/greatness) and SIG.MSR.168 (Dual Malefic 7th Drishti to Lagna — identity-level constraint) both proceed from Saturn 7H. Same planet, same position, same aspect mechanism — authority vs. constraint.
- **domains:** career, mind, spiritual
- **signals_in_conflict:** SIG.MSR.001, SIG.MSR.168
- **resolution_options:** (A) Context-gating by temporal layers (Sasha in Saturn MD vs. malefic grip as natal baseline). (B) Domain-partitioning (Mahapurusha in career/public; malefic grip in personal identity/health).

### CON.010 — signal_polarity_conflict (severity: high)
- **hypothesis_text:** SIG.MSR.016 (Mercury eight-system career dominance) and SIG.MSR.087 (Mercury 6L disease activation) both arise from Mercury's 10H. Deploying Mercury maximally = activating health risk maximally.
- **domains:** career, health
- **signals_in_conflict:** SIG.MSR.016, SIG.MSR.087
- **resolution_options:** (A) Viparita dominance: 6L in 10H neutralizes disease pathway into career advantage. (B) Dual activation: both simultaneously true — manage cognitive output as a health variable.

### CON.011 — signal_polarity_conflict (severity: medium)
- **hypothesis_text:** SIG.MSR.017 (Jupiter 9L own-sign dharmic abundance) and SIG.MSR.157 (joint malefic pressure from Saturn+Mars partial drishti on 9H) present contradictory 9H condition assessments.
- **domains:** spiritual, parents, wealth
- **signals_in_conflict:** SIG.MSR.017, SIG.MSR.157
- **resolution_options:** (A) Dignity priority: Jupiter own-sign overrides partial 45v aspects. (B) Mixed: yoga strength high but Lakshmi Yoga delivery periodically pressured during Saturn/Mars activations.

### CON.012 — signal_polarity_conflict (severity: medium)
- **hypothesis_text:** SIG.MSR.005 (Moon AK Chalit-12H foreign income CVG.03) and SIG.MSR.229 (Mandi 4H malefic shadow on home/mother) create a gaining-the-world/losing-the-home structural contradiction.
- **domains:** travel, wealth, mind
- **signals_in_conflict:** SIG.MSR.005, SIG.MSR.229
- **resolution_options:** (A) Domain separation: foreign success coexists with domestic challenges simultaneously. (B) Temporal alternation: foreign periods deliver income; domestic focus activates Mandi shadow.

### CON.013 — system_divergence (severity: high — revised from medium)
- **hypothesis_text:** Parashari (Saturn AmK AD = career peak) and Jaimini Chara Dasha (Scorpio MD = karmic dissolution, Ketu 8H activation) produce divergent primary narratives for the current 2026–2030 window.
- **domains:** career, spiritual, relationships
- **signals_in_conflict:** SIG.MSR.020, SIG.MSR.267
- **resolution_options:** (A) Layer separation: Vimshottari for events; Chara Dasha for soul direction. (B) Dominant system per query type (event prediction vs. soul guidance).

### CON.014 — system_divergence (severity: high)
- **hypothesis_text:** D9 Saturn in Aries = debilitation (NBRY cancelled — SIG.MSR.003) vs. D1 Saturn in Libra = exaltation (Sasha MPY — SIG.MSR.001). Saturn's dignity is simultaneously highest (D1) and lowest (D9) with cancellation.
- **domains:** career, relationships, spiritual
- **signals_in_conflict:** SIG.MSR.003, SIG.MSR.001
- **resolution_options:** (A) D1 primacy for conditional predictions. (B) Temporal layering: D1 for events; D9 for marriage/dharmic-soul quality.

### CON.015 — system_divergence (severity: medium)
- **hypothesis_text:** Venus as Parashari 2L+7L (partnership/wealth roles) vs. Venus as Jaimini MK (mother-signifier). Venus MD (2034–2054) predictions diverge: Parashari → partnership/wealth; Jaimini → maternal-domain activation.
- **domains:** relationships, parents, wealth
- **signals_in_conflict:** SIG.MSR.082, SIG.MSR.189
- **resolution_options:** (A) System-layer specialization: Parashari for Phala events; Jaimini for soul-quality character. (B) Synthesis: maternal quality expressed through partnerships simultaneously.

### CON.016 — system_divergence (severity: low; verification note)
- **hypothesis_text:** Vimshottari Jupiter MD (1984–1991) = childhood dharma-prosperity vs. Jaimini Chara Dasha Cancer MD = home-protection for same childhood era. Two divergent narratives for formative years.
- **domains:** career, parents, spiritual
- **signals_in_conflict:** SIG.MSR.017, SIG.MSR.163
- **verification_note:** Chara Dasha dates for 1984–1991 require FORENSIC §14 verification. If Cancer MD does not overlap this window, contradiction dissolves.
- **resolution_options:** (A) Developmental framing: Vimshottari = karmic seeding; Jaimini = lived experience. (B) Retrodict and validate via LEL 1984–1991.

### CON.017 — system_divergence (severity: medium)
- **hypothesis_text:** Moon classified as Rashi 11H (gains/networks) vs. Chalit 12H (foreign/liberation) vs. KP cusp ambiguity. Three systems give Moon three different house positions with materially different predictions.
- **domains:** wealth, travel, mind
- **signals_in_conflict:** SIG.MSR.004, SIG.MSR.005
- **resolution_options:** (A) Rashi for natal quality; Chalit for bhava results; KP for precise timing. (B) KP primary: Chalit-12H as Moon's correct bhava (Moon AK = foreign income primary reading).

### CON.018 — temporal_paradox (severity: low)
- **hypothesis_text:** Major yoga formation at birth (1984) vs. yoga activation in Mercury MD (2010) — 26-year gap. The native carried full yoga potential from birth but yogas were structurally unavailable for delivery until Mercury MD.
- **domains:** career, wealth, mind, spiritual
- **signals_in_conflict:** SIG.MSR.132, SIG.MSR.255
- **resolution_options:** (A) MD-activation doctrine: Saturn MD was preparatory; Mercury MD was delivery. (B) Distinguish yoga types: check if Sasha Mahapurusha activated in Saturn MD via LEL.

### CON.019 — temporal_paradox (severity: low)
- **hypothesis_text:** Jupiter MD (most auspicious planet's period) was spent in childhood (ages 0–7) when adult deliverables were inaccessible. Saturn MD (delay/discipline) then governed actual adult formation (ages 7–26). Richest MD first, harshest MD during adult formation.
- **domains:** career, wealth, spiritual, parents
- **signals_in_conflict:** SIG.MSR.017, SIG.MSR.132
- **resolution_options:** (A) Karma-seeding doctrine: Jupiter MD plants dharmic orientation in formative period. (B) Retrodict via LEL 1984–1991 for formative event quality.

### CON.020 — temporal_paradox (severity: high)
- **hypothesis_text:** Mercury MD career peak (ages 26–43) followed immediately by Ketu MD moksha/detachment (ages 43–50) with only a 0.50° quincunx bridge (SIG.MSR.036). No gradual transition — abrupt inversion at professional peak.
- **domains:** career, spiritual, mind
- **signals_in_conflict:** SIG.MSR.150, SIG.MSR.036
- **resolution_options:** (A) Transition framing: Ketu transforms career (detachment from outcome, not from activity). (B) Sharp pivot: genuine life-direction change; restructure career toward legacy/knowledge transmission from 2027.

### CON.021 — temporal_paradox (severity: medium)
- **hypothesis_text:** Saturn AD within Ketu MD (~2030–2031) delivers career-building energy (Saturn AmK) inside Ketu's primary detachment MD. Sub-period and main-period produce opposing instructions: "achieve" vs. "release."
- **domains:** career, spiritual
- **signals_in_conflict:** SIG.MSR.150, SIG.MSR.020
- **resolution_options:** (A) Nested integration: execute Saturn AD career tasks with Ketu MD detachment framing. (B) Conflict acknowledged: flag 2030–2031 as temporary career re-engagement window within detachment MD.

### CON.022 — temporal_paradox (severity: medium)
- **hypothesis_text:** Jupiter-Saturn 9L-10L Raja Yoga (BPHS strongest) should activate in Jupiter's or Saturn's MD per classical doctrine. But it activated in Mercury MD — a third planet's period not constituting the yoga.
- **domains:** career, wealth, spiritual
- **signals_in_conflict:** SIG.MSR.107, SIG.MSR.132
- **resolution_options:** (A) Mercury as synergistic activator: Mercury MD provided the operating platform for yoga delivery. (B) Saturn MD retrodiction: examine LEL 1991–2010 for hidden Raja Yoga activation.

### CON.023 — frame_conflict (severity: high)
- **hypothesis_text:** Saturn's delay/restriction in relationships domain = obstruction. Saturn's delay/discipline in career domain = virtue (AmK, Sasha Mahapurusha). Identical mechanism produces opposite valences by domain frame.
- **domains:** relationships, career
- **signals_in_conflict:** SIG.MSR.001, SIG.MSR.020
- **resolution_options:** (A) Domain-partitioned valence: both simultaneously true; Saturn structures relationships AND builds career. (B) Saturn's primary function is career (AmK, 10L); its 7H residence = career energy in relationship house.

### CON.024 — frame_conflict (severity: high)
- **hypothesis_text:** Ketu 8H exaltation (SIG.MSR.055 = maximum liberation potential) vs. Ketu's dispositor Mars in enemy sign (SIG.MSR.092 = weakened karmic delivery). Liberation vehicle present; fuel delivery system compromised.
- **domains:** spiritual, health
- **signals_in_conflict:** SIG.MSR.055, SIG.MSR.092
- **resolution_options:** (A) Exaltation overrides dispositor weakness (NBRY-style argument). (B) Dispositor-gated delivery: cultivation required (deliberate Mars energy channeling) to overcome enemy-sign dampening during Ketu MD.

### CON.025 — frame_conflict (severity: **critical**; cross_ref: CON.010)
- **hypothesis_text:** Mercury career-engine (career domain: deploy maximally) and Mercury 6L health-risk activator (health domain: monitor during deployment) produce directly contradictory practical advice. No intervening variable separates career-intensification from health-risk activation.
- **domains:** career, health
- **signals_in_conflict:** SIG.MSR.016, SIG.MSR.087
- **cross_ref:** CON.010 (signal_polarity_conflict) involves same signals; see for polarity reading
- **resolution_options:** (A) Viparita integration: disease events ARE the career-building mechanism (overcoming adversity builds authority). (B) Threshold management: Viparita protects below threshold; monitor health when sustained peak performance exceeds Saturn-defined limits.

### CON.026 — frame_conflict (severity: high)
- **hypothesis_text:** Mars Lagnesh (identity-engine, personal drive, self-assertion) vs. Mars Avayogi (career-obstruction, disrupts yoga delivery). The native's assertiveness (1L) is simultaneously his professional liability (Avayogi).
- **domains:** career, relationships, mind
- **signals_in_conflict:** SIG.MSR.134, SIG.MSR.076
- **resolution_options:** (A) Domain segregation: use Mars for identity/relationships; suppress Mars-energy in career-yoga contexts. (B) Manage the Avayogi: minimize Mars/Aries-style career assertiveness during career-yoga activation windows.

### CON.027 — frame_conflict (severity: medium)
- **hypothesis_text:** Rahu 2H wealth amplification (unconventional income via Rohini — SIG.MSR.010) vs. Rahu 2H family/speech destabilization (nodal axis severance — SIG.MSR.161). Acquiring wealth through Rahu's 2H channel structurally undermines the family-foundation required to sustain it.
- **domains:** wealth, relationships, spiritual
- **signals_in_conflict:** SIG.MSR.010, SIG.MSR.161, SIG.MSR.393
- **resolution_options:** (A) Dual-layer awareness: predict wealth AND family challenges together during Rahu activations. (B) Rahu Rohini moderation: Venus dispositor (9H dharmic) filters Rahu chaos, moderating disruption.

---

*End of CONTRADICTION_REGISTER_v1_1.md. Canonical source: CONTRADICTION_REGISTER_v1_1.json.*
*v1.0 (CONTRADICTION_REGISTER_v1_0.md) is SUPERSEDED as of 2026-04-30.*
