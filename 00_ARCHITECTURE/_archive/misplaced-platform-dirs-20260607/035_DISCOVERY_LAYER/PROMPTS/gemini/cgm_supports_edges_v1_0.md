---
prompt_id: gemini.cgm_supports_edges
version: "1.0"
status: CURRENT
phase: B.4
pass_type: PROMISCUOUS_CONNECTOR_PASS_1
produced_by: Madhav_M2A_Exec_7
produced_on: 2026-04-26
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B4_supports_batch<N>_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
reconciler: "platform/python-sidecar/rag/reconcilers/cgm_supports_reconciler.py"
changelog:
  - v1.0 (2026-04-26): Initial version. SUPPORTS-edge two-pass prompt for B.4 Task 3.
      Pass-1 Gemini (promiscuous connector); Pass-2 Claude (reconciler with P1/P2/P5 + L3 chain check).
---

<!-- =====================================================================
BATCH STRATEGY — READ BEFORE RUNNING
======================================================================
This prompt is run 9 times, once per CURRENT L3 Domain Report.

Batch IDs and expected raw response files:
  Batch 1: B4_supports_batch1 → 2026-04-26_B4_supports_batch1_raw.md  (REPORT_CAREER_DHARMA_v1_1.md)
  Batch 2: B4_supports_batch2 → 2026-04-26_B4_supports_batch2_raw.md  (REPORT_CHILDREN_v1_1.md)
  Batch 3: B4_supports_batch3 → 2026-04-26_B4_supports_batch3_raw.md  (REPORT_FINANCIAL_v2_1.md)
  Batch 4: B4_supports_batch4 → 2026-04-26_B4_supports_batch4_raw.md  (REPORT_HEALTH_LONGEVITY_v1_1.md)
  Batch 5: B4_supports_batch5 → 2026-04-26_B4_supports_batch5_raw.md  (REPORT_PARENTS_v1_1.md)
  Batch 6: B4_supports_batch6 → 2026-04-26_B4_supports_batch6_raw.md  (REPORT_PSYCHOLOGY_MIND_v1_1.md)
  Batch 7: B4_supports_batch7 → 2026-04-26_B4_supports_batch7_raw.md  (REPORT_RELATIONSHIPS_v1_1.md)
  Batch 8: B4_supports_batch8 → 2026-04-26_B4_supports_batch8_raw.md  (REPORT_SPIRITUAL_v1_1.md)
  Batch 9: B4_supports_batch9 → 2026-04-26_B4_supports_batch9_raw.md  (REPORT_TRAVEL_v1_1.md)

HOW TO RUN EACH BATCH:
1. Copy the prompt body below into Gemini 2.5 Pro.
2. At the end of the prompt (Section D — Per-Batch Context), also paste the FULL TEXT of
   the target L3 report for this batch (from 03_DOMAIN_REPORTS/).
3. Replace [BATCH_REPORT_NAME] and [BATCH_NUMBER] in Section D with the actual values.
4. Run Gemini. Gemini outputs STRICT YAML (proposed_supports_edges list).
5. Save Gemini's YAML response as the raw response file named above.
6. Commit the raw file and notify the executor (Claude Code) to run the reconciler.

NOTE: The Citation Index in Section C shows which MSR signals and UCN sections are
already explicitly cited in each L3 report — use these as anchor points. But Gemini
SHOULD ALSO propose edges for signals that are implicitly supported by the L3 narrative
(domain overlap, Vimshottari window, Karaka functions, drishti chains) even if not
explicitly cited by ID.
====================================================================== -->

# Gemini SUPPORTS-Edge Proposals — CGM v9.0 (Pass 1: Promiscuous Connector)

## Role

You are operating as a **Promiscuous Connector** in a two-pass graph enrichment protocol for
the MARSYS-JIS Chart Graph Model (CGM). Your task in this Pass 1 run is to propose SUPPORTS
edges — relationships where an MSR signal provides evidentiary support for a claim made in a
UCN section, as demonstrated through a narrative chain in a specific L3 Domain Report.

**Mandate:** Propose ALL potentially valid SUPPORTS edges. The Claude reconciler (Pass 2)
will accept or reject your proposals using P1/P2/P5 invariant checks plus an L3 chain
verification. Do not self-censor — prefer recall over precision. High-recall Pass 1 is the
design intent; the reconciler is the gate.

**Subject:** Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India.
Aries Lagna. Data authoritative from FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1.

---

## Task

Propose SUPPORTS edges where each edge represents:
> "MSR signal X provides evidence for the claim made in UCN section Y, as demonstrated
> by the narrative chain in L3 report Z."

A SUPPORTS edge is valid when:
1. The MSR signal is grounded in L1 chart facts (FORENSIC_v8_0) or derives from them
   via an explicit L2 chain.
2. The UCN section makes a claim that the signal corroborates (directly or through the
   L3 report's narrative chain).
3. The L3 report's body demonstrates this connection in its narrative (the signal and
   UCN section are co-present in a coherent argument within the report).

### Focus Categories (Pass-1 mandate — search all five)

1. **Direct signal–evidence pairings**: Signal is cited in the same paragraph or
   section as a UCN claim in the L3 report. Highest confidence; always include.

2. **Vimshottari-window evidentiary alignment**: Signal is part of a Mahadasha/Antardasha
   architecture that UCN section VIII names, and the L3 report uses this timing context
   to ground its claim.

3. **Cross-house signal aggregation**: Signal's `domains_affected` overlaps with the
   UCN section's principal domain, AND the L3 report's narrative chain ties them together
   (even without explicit co-citation).

4. **Karaka-overlap evidence**: Signal is grounded in a Chara Karaka function (AK, AmK,
   BK, MK, PiK, PuK, GK, DK) that UCN section II or III elaborates, and the L3 report
   uses this Karaka chain as an argument.

5. **Drishti-driven evidence chains**: Signal is grounded in a planet whose graha-drishti
   (or special aspect: Saturn 3rd/10th, Jupiter 5th/9th, Mars 4th/8th) UCN's mechanism
   statement names, and the L3 narrative deploys this drishti chain.

---

## Section A — UCN Section Registry (stable IDs for target_node_id)

These are the 44 canonical UCN sections. Use the `stable_id` as `target_ucn_section_id`
in your output. The `raw_ref` is how the L3 reports cite them (e.g., `(UCN §IV.3)`).

```yaml
ucn_sections:
  UCN.SEC.I.1: "The Five Foundation Signatures"  # cite in L3 reports as (UCN §I.1)
  UCN.SEC.I.2: "How the Five Signatures Interact"  # cite in L3 reports as (UCN §I.2)
  UCN.SEC.I.3: "What This Chart Is NOT"  # cite in L3 reports as (UCN §I.3)
  UCN.SEC.II.1: "The Atmakaraka: What the Soul Elected"  # cite in L3 reports as (UCN §II.1)
  UCN.SEC.II.2: "The Karakamsa: The Soul's Purpose Sign"  # cite in L3 reports as (UCN §II.2)
  UCN.SEC.II.3: "Past-Karma Orientation: What the Soul Carries"  # cite in L3 reports as (UCN §II.3)
  UCN.SEC.II.4: "This-Life Mission: What the Soul Came to Do"  # cite in L3 reports as (UCN §II.4)
  UCN.SEC.II.5: "The Moksha Direction: Where the Soul Is Headed"  # cite in L3 reports as (UCN §II.5)
  UCN.SEC.III.1: "The Aries Lagna: The Self's Fundamental Disposition"  # cite in L3 reports as (UCN §III.1)
  UCN.SEC.III.2: "Moon in 11th House: The Psychological Matrix"  # cite in L3 reports as (UCN §III.2)
  UCN.SEC.III.3: "Mars in 7th House: The Psychological Drive Architecture"  # cite in L3 reports as (UCN §III.3)
  UCN.SEC.III.4: "The Chart's Health Karma"  # cite in L3 reports as (UCN §III.4)
  UCN.SEC.III.5: "The Psychological Integration Challenge"  # cite in L3 reports as (UCN §III.5)
  UCN.SEC.IV.1: "The Four-House Material Axis"  # cite in L3 reports as (UCN §IV.1)
  UCN.SEC.IV.2: "The Saraswati-Lakshmi-Raja Yoga Stack"  # cite in L3 reports as (UCN §IV.2)
  UCN.SEC.IV.3: "How the Engine Fires: The Mercury MD Mechanism"  # cite in L3 reports as (UCN §IV.3)
  UCN.SEC.IV.4: "Wealth as Dharmic Output: The Critical Principle"  # cite in L3 reports as (UCN §IV.4)
  UCN.SEC.IV.5: "The Singapore Context and the 11H-12H Interface"  # cite in L3 reports as (UCN §IV.5)
  UCN.SEC.V.1: "The 7th House: The Karmic Vortex"  # cite in L3 reports as (UCN §V.1)
  UCN.SEC.V.2: "The Upapada Lagna: The Marriage Architecture"  # cite in L3 reports as (UCN §V.2)
  UCN.SEC.V.3: "The 4th House: The Domestic-Maternal Foundation"  # cite in L3 reports as (UCN §V.3)
  UCN.SEC.V.4: "The 5th House: Progeny and Creative Legacy"  # cite in L3 reports as (UCN §V.4)
  UCN.SEC.V.5: "The 11th House: Networks and the AK's Social Infrastructure"  # cite in L3 reports as (UCN §V.5)
  UCN.SEC.V.6: "The 12th House: The Boundary-Zone of Relationship and Dissolution"  # cite in L3 reports as (UCN §V.6)
  UCN.SEC.V.7: "The Relational Web as One Ecosystem"  # cite in L3 reports as (UCN §V.7)
  UCN.SEC.VI.1: "The 12th House as Jupiter's Domain"  # cite in L3 reports as (UCN §VI.1)
  UCN.SEC.VI.2: "The Rahu-Ketu Axis: The Resource-Transformation Polarity"  # cite in L3 reports as (UCN §VI.2)
  UCN.SEC.VI.3: "The Foreign Professional Base as Chart-Congruent"  # cite in L3 reports as (UCN §VI.3)
  UCN.SEC.VI.4: "The Ketu MD as the Moksha Turn"  # cite in L3 reports as (UCN §VI.4)
  UCN.SEC.VII.1: "The Pattern Defined"  # cite in L3 reports as (UCN §VII.1)
  UCN.SEC.VII.2: "The Internal Architecture in Depth"  # cite in L3 reports as (UCN §VII.2)
  UCN.SEC.VII.3: "The External Display: AL = 10H"  # cite in L3 reports as (UCN §VII.3)
  UCN.SEC.VII.4: "The Temporal Validation: Sade Sati as Proof-of-Pattern"  # cite in L3 reports as (UCN §VII.4)
  UCN.SEC.VII.5: "The ATT Across Domains"  # cite in L3 reports as (UCN §VII.5)
  UCN.SEC.VIII.1: "Why Timing Deserves Its Own Part"  # cite in L3 reports as (UCN §VIII.1)
  UCN.SEC.VIII.2: "The Vimshottari Stack in Sequence"  # cite in L3 reports as (UCN §VIII.2)
  UCN.SEC.VIII.3: "The Bhrigu Bindu: The Temporal Trigger in Context"  # cite in L3 reports as (UCN §VIII.3)
  UCN.SEC.VIII.4: "The Mercury-Saturn-Ketu Sequence: Why It Matters Uniquely Here"  # cite in L3 reports as (UCN §VIII.4)
  UCN.SEC.IX.1: "The Meta-Principle: Tension as Growth Engine"  # cite in L3 reports as (UCN §IX.1)
  UCN.SEC.IX.2: "The Seven Contradictions"  # cite in L3 reports as (UCN §IX.2)
  UCN.SEC.IX.3: "The Collective Implication"  # cite in L3 reports as (UCN §IX.3)
  UCN.SEC.X.1: "What These Instructions Are"  # cite in L3 reports as (UCN §X.1)
  UCN.SEC.X.2: "The Five Operating Instructions"  # cite in L3 reports as (UCN §X.2)
  UCN.SEC.X.3: "The Chart's Central Request"  # cite in L3 reports as (UCN §X.3)
```

---

## Section B — MSR Signal Registry (source_signal_id candidates)

These are the 495 canonical MSR signals. Each entry: signal_id | signal_name | domains.
Use the exact `signal_id` as `source_signal_id` in your output.

```yaml
msr_signals:
  SIG.MSR.001: "Sasha Mahapurusha Yoga — Saturn Exalted in 7H Kendra" | domains: [career, wealth, relationships, mind]
  SIG.MSR.002: "D9 Neecha Bhanga Raja Yoga — Venus Debilitated Virgo D9, Cancelled by Mercury Vargottama" | domains: [relationships, wealth, spirit]
  SIG.MSR.003: "D9 Neecha Bhanga Raja Yoga — Saturn Debilitated Aries D9, Cancelled by Sun in D9 Lagna" | domains: [career, wealth, parents]
  SIG.MSR.004: "Atmakaraka Moon in 11H Aquarius — D9 Karakamsa Gemini" | domains: [spirit, mind, travel, wealth]
  SIG.MSR.005: "Moon-AK Chalit-12 Foreign Income Architecture" | domains: [travel, wealth, spirit]
  SIG.MSR.006: "D9 12H Gemini Stellium — Moon + Jupiter + Rahu Disposited by Vargottama Mercury" | domains: [spirit, travel, wealth, mind]
  SIG.MSR.007: "Saraswati Yoga — Jupiter + Venus + Mercury in Kendra/Trikona — CYSS 91" | domains: [career, wealth, mind, spirit]
  SIG.MSR.008: "Lakshmi Yoga — 9L Jupiter Own-Sign + Venus Strong in 9H — CYSS 77" | domains: [wealth, career, spirit, parents]
  SIG.MSR.009: "Mercury Vargottama + MD Lord + Yogi Planet — Chart Operational Spine" | domains: [career, wealth, relationships, mind]
  SIG.MSR.010: "Rahu in 2H Taurus Rohini — Wealth Through Unconventional Channels" | domains: [wealth, relationships, family]
  SIG.MSR.011: "Anapha Yoga — Sun + Mercury in 12th from Moon (Capricorn)" | domains: [career, mind, wealth]
  SIG.MSR.012: "Venus Shadbala Rank 7 — Weakest Planet by Aggregate Strength" | domains: [relationships, wealth, spirit, health]
  SIG.MSR.013: "Sade Sati Cycle 2 Active — Saturn in Pisces Transiting 12th from Natal Moon" | domains: [health, mind, career, wealth, relationships]
  SIG.MSR.014: "Sun 10H Capricorn with AL + Mercury — Career-Density Stellium" | domains: [career, wealth, parents]
  SIG.MSR.015: "Hidden Raja Yoga — Mars + Saturn Exalted Conjunction in 7H Libra" | domains: [career, relationships, wealth]
  SIG.MSR.016: "Mercury Operational Dominance — Six-Factor CVG.01 Convergence" | domains: [career, wealth, relationships, mind]
  SIG.MSR.017: "Jupiter 9L-Own Dharma-Wealth Chain — CVG.02" | domains: [wealth, spirit, career, children]
  SIG.MSR.018: "Moon AK Foreign-Income Chain — CVG.03" | domains: [travel, wealth, spirit]
  SIG.MSR.019: "10H Career-Density Convergence — CVG.04" | domains: [career, wealth, parents]
  SIG.MSR.020: "Saturn 7H Exalted + Shadbala + MPY + AD Lord + Yogini — CVG.05" | domains: [career, relationships, wealth, mind]
  SIG.MSR.021: "Jupiter 9H Own-Sign + Lakshmi Member + 9L + MPY Near-Miss — CVG.06" | domains: [spirit, wealth, children, travel]
  SIG.MSR.022: "Gemini 3H Nexus — UL + A5 + A11 + Hora Lagna + Vivaha Saham (4H Cancer) — CVG.07" | domains: [relationships, children, wealth]
  SIG.MSR.023: "Aries-Libra Axis Triple-Aspect — Mars/Saturn 7th + Jupiter 5th + Bhrigu Bindu + Muntha — CVG.08" | domains: [career, relationships, health, mind]
  SIG.MSR.024: "Saturn Ishta/Kashta Phala Resolution — Saturn IS the Chart's Most Beneficial Phala Planet (v2.0 REVISED)" | domains: [career, relationships, wealth, health]
  SIG.MSR.025: "Dharma Devata Tension — Venkateswara (Classical) vs Jagannath (Operational) — CTR.02" | domains: [spirit, mind]
  SIG.MSR.026: "Jupiter Uccha Bala Rank 7 Last — Positional Weakness Amid Dignity Strength — CTR.03" | domains: [parents, children, spirit, wealth]
  SIG.MSR.027: "Moon Rashi-11H vs Chalit-12H House Drift — CTR.04" | domains: [travel, wealth, mind, spirit]
  SIG.MSR.028: "Mercury Rashi/Chalit Ambiguity — 10H vs Cusp Proximity — CTR.05" | domains: [career, wealth]
  SIG.MSR.029: "Sun Sthana Bala Arithmetic Resolved — CTR.06" | domains: [career]
  SIG.MSR.030: "Sade Sati Phase Labels vs Saturn Ephemeris Inconsistency — CTR.07" | domains: [health, mind, career]
  SIG.MSR.031: "Rahu Quadruple Jaimini Aspect — Rahu Aspects Sun + Mercury + Mars + Saturn" | domains: [career, wealth, relationships]
  SIG.MSR.032: "7H Bhavabala Rank 12 vs SAV Rank 1 — Paradox: Strong Sign in Weak House" | domains: [relationships, career]
  SIG.MSR.033: "12H Bhavabala Rank 1 vs SAV Rank 12 — Self-Powered Moksha Architecture" | domains: [spirit, travel, health]
  SIG.MSR.034: "Sun-Mercury-AL 10H Density Loop-Closure — Triple 10H Concentration" | domains: [career, wealth, parents]
  SIG.MSR.035: "Mercury Operational Yoga Stack — Elevates CVG.01 to Six-Layer Convergence" | domains: [career, wealth, relationships, mind]
  SIG.MSR.036: "Ketu-Mercury 0.50° Quincunx — Tightest Aspect in Chart, MD-Handover Bridge 2027" | domains: [career, spirit, mind]
  SIG.MSR.037: "Saturn Quadruple-Structural-Activation — Shadbala + Pinda + MPY + AD + AmK" | domains: [career, relationships, wealth]
  SIG.MSR.038: "Triple-Exalted-Nodal-Axis — Saturn (Libra) + Rahu (Taurus) + Ketu (Scorpio) All Exalted" | domains: [career, spirit, relationships, travel]
  SIG.MSR.039: "Mars-Capricorn-Transit as Career-Launch Trigger — Retrodictively Confirmed" | domains: [career, wealth]
  SIG.MSR.040: "Saturn-Pisces Triple-Activation 2025–2028 — Transit + Kakshya + Sade Sati Descending" | domains: [spirit, travel, health, mind, wealth]
  SIG.MSR.041: "D27 Lagna Pisces = D1 12H Pisces — Strength-Chart Lagna is Natal Moksha House" | domains: [spirit, travel, health]
  SIG.MSR.042: "D60 Saturn at Lagna — Past-Karma Primary Thread is Saturn-Discipline" | domains: [spirit, career, mind]
  SIG.MSR.043: "D20 + D40 Sun-Pisces Vishnu-Affinity — Structural Cross-Divisional Pattern" | domains: [spirit, mind]
  SIG.MSR.044: "Mercury MD Retrodictive Density 10× Other MDs — Empirical Validation of CVG.01" | domains: [career, wealth, relationships, children]
  SIG.MSR.045: "100% AD-Lord Domain-Match Pattern — Every Mercury MD Sub-Period Thematically Matches Lord" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.046: "Saturn Return Libra 2041–2044 — Lifetime Apex Transit at Age 57–60" | domains: [career, relationships, wealth, health, spirit]
  SIG.MSR.047: "Sun in Capricorn D1 — Enemy Sign (Shatru Kshetra)" | domains: [career, parents, mind]
  SIG.MSR.048: "Moon in Aquarius D1 — Neutral Sign (Sama)" | domains: [mind, wealth, travel, spirit]
  SIG.MSR.049: "Mars in Libra D1 — Enemy Sign, Lagnesh in 7H" | domains: [health, relationships, career]
  SIG.MSR.050: "Mercury in Capricorn D1 — Neutral/Friendly Sign" | domains: [career, wealth, mind]
  SIG.MSR.051: "Jupiter in Sagittarius D1 — Own Sign (Swa Kshetra)" | domains: [wealth, spirit, children, parents, career]
  SIG.MSR.052: "Venus in Sagittarius D1 — Friend's Sign (Mitra Kshetra)" | domains: [spirit, relationships, wealth, health]
  SIG.MSR.053: "Saturn in Libra D1 — Exalted (Uccha), Maximum Uccha Bala 59.18 Virupa" | domains: [career, relationships, wealth, mind]
  SIG.MSR.054: "Rahu in Taurus D1 — Exalted (Classical School)" | domains: [wealth, relationships, family]
  SIG.MSR.055: "Ketu in Scorpio D1 — Exalted (Classical School)" | domains: [spirit, health, mind, travel]
  SIG.MSR.056: "Mercury Vargottama in Capricorn D9 — Same Sign as D1 (Maximum Stability)" | domains: [career, wealth, mind, relationships]
  SIG.MSR.057: "Venus Debilitated in Virgo D9 — Neecha, Cancelled (NBRY)" | domains: [relationships, wealth, spirit]
  SIG.MSR.058: "Saturn Debilitated in Aries D9 — Neecha, Cancelled (NBRY)" | domains: [career, relationships, wealth]
  SIG.MSR.059: "Moon in Gemini D9 12H — AK in Moksha House of Navamsa" | domains: [spirit, travel, mind]
  SIG.MSR.060: "Jupiter in Gemini D9 12H — Enemy Sign, Yet Part of Moksha Stellium" | domains: [spirit, wealth, children]
  SIG.MSR.061: "Sun in Cancer D9 — Friend's Sign, D9 Lagna (1H D9) — Strong Navamsa Positioning" | domains: [career, parents, spirit]
  SIG.MSR.062: "Saturn in Taurus D10 — Friend's Sign at D10 Midheaven" | domains: [career, wealth]
  SIG.MSR.063: "Sun + Mars in Aries D10 9H — Both Exalted/Own-Sign in D10 Trikona" | domains: [career, wealth, parents]
  SIG.MSR.064: "Mercury Own-Sign in Virgo D10 2H — Budha in Own Sign in Dhana Bhava of Career Chart" | domains: [career, wealth]
  SIG.MSR.065: "Mars Exalted in Capricorn D3 Drekkana — Physical Vitality Reinforced" | domains: [health, career]
  SIG.MSR.066: "Jupiter Own-Sign in Sagittarius D7 Saptamsha — Children Prosperity" | domains: [children]
  SIG.MSR.067: "Saturn D9 Aries Debilitation — Cross-Reference to MSR.058" | domains: [career]
  SIG.MSR.068: "Rahu in Gemini D9 12H — Amplifies Stellium and Foreign Dimension" | domains: [travel, spirit, wealth]
  SIG.MSR.069: "Jupiter Exalted in Cancer D3 — Dharma Vitality Peak in Drekkana" | domains: [spirit, children, wealth]
  SIG.MSR.070: "Shadbala Rank 1 — Sun: Highest Overall Planetary Strength Despite Enemy Sign" | domains: [career, parents, mind]
  SIG.MSR.071: "Shadbala Rank 2 — Saturn: Second Strongest Despite Pinda Paradox" | domains: [career, relationships, wealth]
  SIG.MSR.072: "Shuddha Pinda Rank 1 — Mars: Maximum Dramatic-Activation Potential" | domains: [health, career, relationships]
  SIG.MSR.073: "Vimsopaka Rank 1 — Jupiter: Highest Cross-Divisional Aggregate Strength" | domains: [wealth, spirit, children, parents]
  SIG.MSR.074: "D27 Bhamsa Lagna Pisces — Native Strength Chart Opens With Jupiter's Own Sign" | domains: [spirit, health]
  SIG.MSR.075: "D60 Shashtyamsa — Past-Karma Chart Primary Configuration" | domains: [spirit, career, mind]
  SIG.MSR.076: "Lagna Lord Mars in Libra — Lagnesh in 7H Enemy Sign Creates Body-Partnership Tension" | domains: [health, relationships, career]
  SIG.MSR.077: "12H Lord Jupiter in Own-Sign 9H — 12L in 9H = Moksha-Dharma Integration" | domains: [spirit, wealth, travel]
  SIG.MSR.078: "9H Lord Jupiter in Own-Sign 9H — 9L in 9H Self-Powered Dharma Engine" | domains: [spirit, wealth, career, children]
  SIG.MSR.079: "10L Saturn Exalted in 7H — Career Lord Away from Career House, But Exalted" | domains: [career, relationships]
  SIG.MSR.080: "11L Saturn Exalted in 7H — Gains Lord Exalted in Partnership House" | domains: [wealth, career, relationships]
  SIG.MSR.081: "2L Venus in 9H — Wealth Lord in Dharma House" | domains: [wealth, spirit]
  SIG.MSR.082: "7L Venus in 9H — Partnership Lord in Dharma House" | domains: [relationships, spirit]
  SIG.MSR.083: "5L Sun in 10H — Children Lord in Career House" | domains: [children, career]
  SIG.MSR.084: "4L Moon in 11H/12H (Rashi/Chalit) — Comfort Lord Away from Comfort House" | domains: [mind, travel, family, health]
  SIG.MSR.085: "3L Mercury in 10H — Siblings/Communication Lord in Career House" | domains: [career, wealth]
  SIG.MSR.086: "8L Mars in 7H — 8H Lord in 7H, Maraka Axis Activation" | domains: [health, relationships]
  SIG.MSR.087: "6L Mercury in 10H — Disease Lord in Career House (Viparita Consideration)" | domains: [career, health]
  SIG.MSR.088: "Moolatrikona Sun in Shravana — Sun's Nakshatra Resonates with Career Themes" | domains: [career, mind]
  SIG.MSR.089: "Moolatrikona Jupiter at 09°48' Sagittarius — Within Mulatrikona Band" | domains: [wealth, spirit, career, children]
  SIG.MSR.090: "Saturn Exaltation at 22°27' Libra — Post-Peak Exaltation (Saturn's Moolatrikona is Aquarius, not Libra)" | domains: [career, relationships]
  SIG.MSR.091: "9L in 9H Self-Dispositorship — Jupiter Disposits Itself in Sagittarius" | domains: [spirit, wealth, career]
  SIG.MSR.092: "Ketu's Dispositor Mars in Enemy Sign — Weakened Karmic-Resolver" | domains: [spirit, health, mind]
  SIG.MSR.093: "Rahu's Dispositor Venus in Friend Sign 9H — Rahu Filtered Through Dharma" | domains: [wealth, spirit, relationships]
  SIG.MSR.094: "Saturn AmK in 7H — Career-Authority Karaka Exalted in Partnership House" | domains: [career, relationships]
  SIG.MSR.095: "Moon AK in 11H/12H — Soul-Significator in Gains/Moksha Zone" | domains: [spirit, wealth, travel, mind]
  SIG.MSR.096: "Mercury DK (Darakaraka) in 10H — Spouse/Partner Significator in Career House" | domains: [relationships, career]
  SIG.MSR.097: "Budh-Aditya Yoga — Sun + Mercury Conjunction in 10H Capricorn (Not Combust)" | domains: [career, mind, wealth]
  SIG.MSR.098: "Vasi Yoga — Moon in 2nd from Sun (Aquarius)" | domains: [wealth, mind, career]
  SIG.MSR.099: "Vesi Yoga — Jupiter + Venus in 12th from Sun (Sagittarius)" | domains: [wealth, spirit, career]
  SIG.MSR.100: "Ubhayachari Yoga — Planets Both Sides of Sun (Vasi + Vesi Simultaneous)" | domains: [career, wealth, spirit, mind]
  SIG.MSR.101: "Bhadra Yoga — Mercury in Kendra (10H) in Friend's Sign" | domains: [career, mind, wealth]
  SIG.MSR.102: "Dhana Yoga — 2L + 11L Relationship (Venus + Saturn)" | domains: [wealth]
  SIG.MSR.103: "Dhana Yoga — 5L + 9L (Sun + Jupiter) Relationship" | domains: [wealth, spirit, children]
  SIG.MSR.104: "Dhana Yoga — 9L in Own-Sign (Jupiter Self-Sustaining Fortune)" | domains: [wealth, spirit]
  SIG.MSR.105: "Dhana Yoga — 5L Sun in 10H Kendra (Intelligence-Career Wealth Link)" | domains: [wealth, career]
  SIG.MSR.106: "Raja Yoga — 1L + 10L Conjunction (Mars + Saturn in 7H)" | domains: [career, relationships, wealth]
  SIG.MSR.107: "Raja Yoga — 9L + 10L Relationship (Jupiter + Saturn)" | domains: [career, wealth, spirit]
  SIG.MSR.108: "Raja Yoga — 5L + 9L (Sun + Jupiter) Trikona-Trikona" | domains: [career, wealth, spirit]
  SIG.MSR.109: "Raja Yoga — 4L + 1L (Moon + Mars) Angular Relationship" | domains: [career, health]
  SIG.MSR.110: "Kahala Yoga — 4L + 9L Strong; Lagnesh Strong" | domains: [career, wealth]
  SIG.MSR.111: "Amala Yoga Near-Miss — 10th from Moon Has Ketu (Malefic), Not Pure" | domains: [career]
  SIG.MSR.112: "Kala Sarpa Yoga — ABSENT (Planets on Both Sides of Nodal Axis)" | domains: []
  SIG.MSR.113: "Gajakesari Yoga — ABSENT Natally (Jupiter 11th from Moon, Not Kendra)" | domains: [children, wealth, spirit]
  SIG.MSR.114: "Uchcha Graha Yoga — Three Exalted Planets (Saturn + Rahu + Ketu) Simultaneously" | domains: [career, spirit, relationships]
  SIG.MSR.115: "Parvatayoga Near-Miss — 6L + 12L Strong But Not Mutual Kendra" | domains: [spirit, health]
  SIG.MSR.116: "Vipreet Raja Yoga — 8L Mars in 7H (Near-Dusthana Configuration)" | domains: [career, health, relationships]
  SIG.MSR.117: "Hamsa Yoga Near-Miss — Jupiter in 9H (Trikona) Not Kendra" | domains: []
  SIG.MSR.118: "Ruchaka Yoga — ABSENT (Mars in Enemy Sign, Not Own/Exalted in Kendra)" | domains: []
  SIG.MSR.119: "Malavya Yoga — ABSENT (Venus Not in Own/Exalted in Kendra)" | domains: []
  SIG.MSR.120: "Surya-Chandra Yoga — Sun-Moon 30° Apart (Sukla Paksha Waning Context)" | domains: [mind, career, wealth]
  SIG.MSR.121: "Panchadhyayi Yoga — Five Planets in Two Signs (Cap+Aqu+Lib+Sag = Concentrated)" | domains: [career, spirit, relationships]
  SIG.MSR.122: "Akhanda Samrajya Yoga — Jupiter as Lord of 2/5/11 + Kendra Lord Strong" | domains: [career, wealth]
  SIG.MSR.123: "Dur Yoga — Lagna Lord in Enemy Sign + 6th from Lagna Lord (Mars)" | domains: [career, health]
  SIG.MSR.124: "Durudhura Yoga — ABSENT (No Planets on Both Sides of Moon)" | domains: []
  SIG.MSR.125: "Chandra Mangala Yoga — ABSENT Natally (Moon-Mars Not in Conjunction or Mutual Kendra)" | domains: []
  SIG.MSR.126: "Vipreet Lakshmi Yoga — Jupiter (12L) in 9H Own-Sign (12L Benefically Placed)" | domains: [spirit, travel, wealth]
  SIG.MSR.127: "Yoga Karaka for Aries Lagna — Saturn (Rules Both Kendra 10H and Trikona... wait — Saturn rules 10H and 11H)" | domains: [career, health, relationships]
  SIG.MSR.128: "Saraswati Yoga Extended — Third Angle Confirmation via All Three in Kendra/Trikona" | domains: [career, mind, spirit, wealth]
  SIG.MSR.129: "Dhana Yoga — Rahu in 2H Amplifies Accumulated Wealth (Unconventional)" | domains: [wealth]
  SIG.MSR.130: "Composite Yoga — Saraswati + Lakshmi + Budh-Aditya Stack (Intelligence-Wealth-Dharma)" | domains: [career, wealth, mind, spirit]
  SIG.MSR.131: "Composite Yoga — Sasha + Hidden Raja Stack (Authority Through Structural Tension)" | domains: [career, relationships]
  SIG.MSR.132: "Yoga Timing — All Major Yogas Become Active During Mercury MD (2010–2027)" | domains: [career, wealth, mind, spirit]
  SIG.MSR.133: "Yoga Timing — All Sasha + Hidden Raja Yogas Peak During Saturn AD (2024–2027)" | domains: [career, relationships, wealth]
  SIG.MSR.134: "Yoga Denial — Mars Avayogi (Inauspicious Sensitive Point) Reduces Lagnesh" | domains: [health, career, relationships]
  SIG.MSR.135: "Yoga Enhancement — Mercury Yogi (Auspicious Sensitive Point) Elevates MD" | domains: [career, wealth, mind]
  SIG.MSR.136: "Composite Yoga — Moon AK + AK in 12H (Chalit) + D9 12H Stellium = Moksha-Orientation Stack" | domains: [spirit, travel, mind]
  SIG.MSR.137: "Saturn-Venus Mutual Affinity Yoga — Saturn in Venus's Libra, Venus Disposits to Jupiter" | domains: [career, spirit, wealth]
  SIG.MSR.138: "Three-Planet Dispositorship Hub — Sun, Moon, Mercury All Route to Saturn" | domains: [career, mind, wealth]
  SIG.MSR.139: "Three-Planet Dispositorship Hub — Mars, Saturn, Rahu All Route to Venus" | domains: [relationships, spirit, wealth, health]
  SIG.MSR.140: "Mercury MD Yoga Activation — Every Mercury-Member Yoga Peaks 2010-2027" | domains: [career, wealth, mind, relationships]
  SIG.MSR.141: "Yoga Absence — No Mahapurusha for Sun (No Ravi Yoga from Classical Set)" | domains: []
  SIG.MSR.142: "Kendradhipati Dosha — Moon (4L) in Upachaya + Saturn Double-Kendra Lord" | domains: [mind, family, health]
  SIG.MSR.143: "Yoga Presence — Sarpa Yoga ABSENT (No Three Serpent Planets in Angles)" | domains: []
  SIG.MSR.144: "Vasumati Yoga — Natural Benefics in Upachaya (3/6/10/11) from Lagna or Moon" | domains: [wealth, career]
  SIG.MSR.145: "Yoga — Parivartana (Exchange) Between Saturn-10L and Venus-7L (Both in Each Other's Sign)" | domains: []
  SIG.MSR.146: "Yoga — Parivartana Between Jupiter (12L) and Mars (8L) — 8H-12H Exchange" | domains: []
  SIG.MSR.147: "Yoga — Nipuna Yoga (Mercury in Own Sign/Exaltation with Jupiter Aspect)" | domains: [career, mind]
  SIG.MSR.148: "Yoga — Pushkala Yoga (Moon conjunct or aspected by dispositor in Kendra)" | domains: [mind, wealth]
  SIG.MSR.149: "Yoga — Trigraha in 7H (Mars + Saturn + Bhrigu Bindu) = Triple 7H Concentration" | domains: [relationships, career, spirit]
  SIG.MSR.150: "Yoga — Ketu MD Incoming (2027): Moksha Stack Activation at Age 43-50" | domains: [spirit, mind, health, career]
  SIG.MSR.151: "Yoga — Venus MD Coming (2034-2054): 20-Year Grace Period for Relationships and Wealth" | domains: [wealth, relationships, spirit, health]
  SIG.MSR.152: "Conjunction — Mars+Saturn in Libra 7H: Hidden Raja Yoga — Iron-Forge in Partnerships House" | domains: [career, relationships, wealth, mind]
  SIG.MSR.153: "Conjunction — Jupiter+Venus in Sagittarius 9H: Dharma-Lakshmi Engine" | domains: [spirit, wealth, relationships, career]
  SIG.MSR.154: "Conjunction — Sun+Mercury in Capricorn 10H: Budhaditya Yoga in Career Peak" | domains: [career, mind, wealth]
  SIG.MSR.155: "Aspect — Saturn (7H Exalted) 7th Drishti to Aries Lagna: Exalted Authority Compresses Self-Identity" | domains: [career, health, mind, spirit]
  SIG.MSR.156: "Aspect — Mars (7H) 7th Drishti to Aries Lagna: Lagnesh Also Aspects Its Own Lagna" | domains: [career, relationships, health, mind]
  SIG.MSR.157: "Aspect — Saturn (3rd, 45v) + Mars (4th, 45v): Joint Pressure on Sagittarius 9H (Jupiter+Venus)" | domains: [spirit, career, parents, wealth]
  SIG.MSR.158: "Aspect — Mars (7H) 4th Drishti to Capricorn 10H (Sun+Mercury): Lagnesh Energizes Career Cluster" | domains: [career, mind, wealth]
  SIG.MSR.159: "Aspect — Mars (7H) 8th Drishti to Taurus 2H (Rahu): Penetrating Warrior-Pressure on Wealth-Amplifier" | domains: [wealth, family, health, mind]
  SIG.MSR.160: "Aspect — Jupiter (9H, Own Sign) 5th Drishti to Aries Lagna: Guru Grace on Self-Identity" | domains: [spirit, career, mind, health]
  SIG.MSR.161: "Aspect — Rahu (2H) 7th Drishti to Scorpio 8H (Ketu): Nodal Axis Self-Aspect" | domains: [wealth, spirit, health, mind]
  SIG.MSR.162: "Aspect — Ketu (8H) 7th Drishti to Taurus 2H (Rahu): Moksha-Severancer Checks Wealth-Amplifier" | domains: [wealth, spirit, health]
  SIG.MSR.163: "Aspect — Saturn (7H) 10th Drishti to Cancer 4H (Empty): Saturnine Oversight of Home Domain" | domains: [health, parents, wealth]
  SIG.MSR.164: "Aspect — Jupiter (9H) 7th Drishti to Gemini 3H (Empty) + 9th Drishti to Leo 5H (Empty): Guru Activates Communication and Progeny Houses" | domains: [mind, children, spirit, career]
  SIG.MSR.165: "Aspect — Sun+Mercury (10H) Both Cast 7th Drishti to Cancer 4H (Empty): Career Cluster Illuminates Home Domain" | domains: [career, parents, health, mind]
  SIG.MSR.166: "Aspect — Moon (11H) 7th Drishti to Leo 5H (Empty): AK Soul-Mind Blesses Progeny-Intelligence House" | domains: [children, mind, spirit, wealth]
  SIG.MSR.167: "Aspect — Venus (9H) 7th Drishti to Gemini 3H (Empty): Lakshmi Blesses Communication Domain" | domains: [wealth, relationships, career, mind]
  SIG.MSR.168: "Convergence — Dual Malefic 7th Drishti to Lagna (Saturn 60v + Mars 60v = 120v): Maximum Malefic Grip on Identity" | domains: [career, health, mind, spirit, relationships]
  SIG.MSR.169: "Convergence — Triple Aspect on Lagna (Saturn 60v malefic + Mars 60v malefic + Jupiter 45v benefic): The Chart's Central Identity Equation" | domains: [career, spirit, mind, health, relationships]
  SIG.MSR.170: "Convergence — Cancer 4H (Empty) Triple-Aspected (Saturn 30v + Sun 60v + Mercury 60v = 150v): Most-Aspected Empty House" | domains: [health, parents, career, mind]
  SIG.MSR.171: "Convergence — Moon-AK in 11H (Aquarius) Receives ZERO Parashari Graha Drishti: Isolated Atmakaraka" | domains: [mind, spirit, wealth, career]
  SIG.MSR.172: "Jaimini Rashi Drishti — Taurus 2H (Rahu, Fixed) to Libra 7H + Capricorn 10H: RAHU QUADRUPLE ASPECT (SIG.16)" | domains: [career, wealth, relationships, mind, spirit]
  SIG.MSR.173: "Jaimini Rashi Drishti — Libra 7H (Mars+Saturn, Movable) to Taurus 2H + Aquarius 11H: Dual-Malefic Reaches Rahu + Moon-AK" | domains: [wealth, mind, spirit, career]
  SIG.MSR.174: "Jaimini Rashi Drishti — Capricorn 10H (Sun+Mercury, Movable) to Taurus 2H + Scorpio 8H: Career Cluster Sees Rahu + Ketu" | domains: [career, wealth, spirit, mind]
  SIG.MSR.175: "Jaimini Rashi Drishti — Scorpio 8H (Ketu, Fixed) to Capricorn 10H (Sun+Mercury): Moksha-Wisdom Sees Career" | domains: [career, spirit, mind]
  SIG.MSR.176: "Jaimini Rashi Drishti — Aquarius 11H (Moon-AK, Fixed) to Libra 7H (Mars+Saturn): Soul Sees the Iron-Forge" | domains: [mind, spirit, career, health]
  SIG.MSR.177: "Jaimini Rashi Drishti — Sagittarius 9H (Jupiter+Venus, Dual) Zero Planetary Reach: Dharma Cluster is Jaimini-Isolated" | domains: [spirit, career, relationships]
  SIG.MSR.178: "Virupa Summary — Lagna (Aries 1H) Receives 165 Total Virupas (120 malefic + 45 benefic): Most-Aspected Point in Chart" | domains: [career, health, mind, spirit, relationships]
  SIG.MSR.179: "Virupa Summary — Saturn's Three-House Aspect Grid (60v+45v+30v): Saturnine Structural Coverage" | domains: [career, spirit, health, parents]
  SIG.MSR.180: "Virupa Summary — Mars's Three-House Aspect Grid (60v+45v+30v): Lagnesh Comprehensive Coverage" | domains: [career, wealth, health, mind, relationships]
  SIG.MSR.181: "Aspect Summary — 7H Libra Conjunction (Mars+Saturn) Projects 5-House Aspect Grid: Structural Hub of Chart" | domains: [career, wealth, health, mind, spirit, relationships]
  SIG.MSR.182: "Red-Team — Prior Session Summary Planetary Position Errors: Correction Audit Log" | domains: []
  SIG.MSR.183: "Nakshatra — Lagna in Ashwini Pada 4 (Aries 12°23'): Ketu-Lord Healing-Pioneer Ascendant" | domains: [health, spirit, career, mind]
  SIG.MSR.184: "Nakshatra — Moon-AK in Purva Bhadrapada Pada 3 (Aquarius 27°02'): Jupiter-Lord Soul in Fierce Pyre-Nakshatra" | domains: [mind, spirit, wealth, travel]
  SIG.MSR.185: "Nakshatra — Sun in Shravana Pada 4 (Capricorn 21°57'): Moon-Lord Listening-Sovereign in Authority Sign" | domains: [career, spirit, mind, parents]
  SIG.MSR.186: "Nakshatra — Mercury in Uttara Ashadha Pada 2 (Capricorn 00°50'): Sun-Lord Invincible-Vow Communicator" | domains: [career, mind, wealth, spirit]
  SIG.MSR.187: "Nakshatra — Mars in Swati Pada 4 (Libra 18°31'): Rahu-Lord Independent-Sword in Relationship Sign" | domains: [career, relationships, health, wealth]
  SIG.MSR.188: "Nakshatra — Jupiter in Moola Pada 3 (Sagittarius 09°48'): Ketu-Lord Root-Galactic-Center Guru in Own Sign" | domains: [spirit, career, mind, parents]
  SIG.MSR.189: "Nakshatra — Venus in Purva Ashadha Pada 2 (Sagittarius 19°10'): Venus-Lord Self-Referencing Nakshatra — Swakshetra at Nakshatra Level" | domains: [wealth, relationships, spirit, health]
  SIG.MSR.190: "Nakshatra — Saturn in Vishakha Pada 1 (Libra 22°27'): Jupiter-Lord Branching-Goal-Ambition in Exaltation" | domains: [career, wealth, relationships, mind, spirit]
  SIG.MSR.191: "Nakshatra — Rahu in Rohini Pada 3 (Taurus 19°01'): Moon-Lord Lush-Growth Amplifier in Exaltation Sign" | domains: [wealth, career, mind, relationships]
  SIG.MSR.192: "Nakshatra — Ketu in Jyeshtha Pada 1 (Scorpio 19°01'): Mercury-Lord Elder-Chief in Exaltation Sign" | domains: [spirit, career, health, mind]
  SIG.MSR.193: "Nakshatra Lord Chain — Sun-Mercury Exchange: Sun in Shravana (Moon lord) / Mercury in Uttara Ashadha (Sun lord)" | domains: [career, mind, spirit]
  SIG.MSR.194: "Nakshatra Lord Chain — Jupiter-Ketu-Mercury Loop: Moola(Ketu)→Jyeshtha(Mercury)→UA(Sun)→Shravana(Moon)→PBP(Jupiter) = Karma-Dharma Closed Chain" | domains: [career, spirit, mind, wealth]
  SIG.MSR.195: "Nakshatra — Mars-Saturn Nakshatra Pair in 7H: Swati(Rahu) + Vishakha(Jupiter) = Rahu-Jupiter Nakshatra Opposition in Iron-Forge" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.196: "Tara Bala — Rahu's Rohini is Naidhana (7th Tara = Danger Tara) from Moon's Purva Bhadrapada" | domains: [wealth, health, mind]
  SIG.MSR.197: "Tara Bala — Lagna Nakshatra (Ashwini = 4th Kshema Tara) from Moon: Favorable Lagna-Soul Relationship" | domains: [health, spirit, career]
  SIG.MSR.198: "Tara Bala — Summary of Key Planetary Taras from Moon (Purva Bhadrapada): Complete Tara Diagnostic" | domains: [health, career, spirit, mind, wealth]
  SIG.MSR.199: "Nakshatra Convergence — Three Ketu-Lord Nakshatras in Chart (Moola+Ashwini+Magha chain): Ketu as Hidden Nakshatra Hub" | domains: [spirit, career, mind, health]
  SIG.MSR.200: "Nakshatra Pada — Mercury in Uttara Ashadha Pada 2 (Capricorn Navamsa): Triple-Capricorn Vargottama Lock" | domains: [career, mind, wealth]
  SIG.MSR.201: "Nakshatra Pada — Saturn in Vishakha Pada 1 (Aries Navamsa): Exalted-Debilitated Navamsa-Nakshatra Pattern" | domains: [career, wealth, parents, spirit]
  SIG.MSR.202: "Nakshatra — Ketu in Jyeshtha + Mars (Lagnesh) in Swati (Rahu lord): Ketu-Mars Nakshatra-Lord Loop" | domains: [spirit, health, career, mind]
  SIG.MSR.203: "Nakshatra — Venus in Own Nakshatra (Purva Ashadha): Self-Referencing Lakshmi Principle" | domains: [wealth, relationships, spirit, health]
  SIG.MSR.204: "Nakshatra — Jupiter in Moola (Galactic Center, Nirriti deity): Root-Dissolution as Dharmic Method" | domains: [spirit, career, mind]
  SIG.MSR.205: "Nakshatra — Rahu in Rohini (Brahma deity, Taurus): Creative-Generative Ambition at Maximum Material Peak" | domains: [wealth, career, relationships, mind]
  SIG.MSR.206: "Nakshatra Summary — Chart's Deity Profile: Vishnu (Shravana) + Brahma (Rohini) + Vishvadevas (UA) + Nirriti (Moola): Creator-Preserver-Dissolver Trinity Present" | domains: [spirit, career, mind, health]
  SIG.MSR.208: "D9 — Mercury Vargottama (Capricorn D1 = Capricorn D9): Chart's Most Structurally Continuous Dignity" | domains: [career, mind, wealth]
  SIG.MSR.209: "D9 — 12H Stellium (Moon+Jupiter+Rahu in Gemini D9): Soul-Dispersion to Foreign-Dharmic Domain" | domains: [travel, wealth, spirit, career]
  SIG.MSR.210: "D9 — Venus NBRY (Virgo Debilitated, Mercury Vargottama Cancels): Partnership Weakness → Elevated" | domains: [relationships, wealth, spirit]
  SIG.MSR.211: "D9 — Saturn NBRY (Aries Debilitated, Sun in D9 Lagna Cancer Cancels): Authority Weakness → Raja Yoga" | domains: [career, wealth, parents, spirit]
  SIG.MSR.212: "D9 — Mars in Pisces 9H (Dharmic Trine from D9 Lagna Cancer): Lagnesh in Dharma-Angle at Navamsa Level" | domains: [spirit, career, health]
  SIG.MSR.213: "D10 — Saturn at D10 Midheaven (Taurus 10H): Career-Permanence Signature" | domains: [career, wealth]
  SIG.MSR.214: "D10 — Sun+Mars in D10 9H Aries (Dharmic Trine from D10 Lagna Leo): Dharmic-Martial-Career Fusion" | domains: [career, spirit]
  SIG.MSR.215: "D10 — Mercury Own-Sign D10 Virgo 2H + Jupiter Own-Sign D10 Pisces 8H: Dual Own-Sign Planets in 2H-8H Axis" | domains: [career, wealth, spirit]
  SIG.MSR.216: "D10 — Rahu in D10 Cancer 12H (Foreign-Career Engine): Structural US-Stint Predictor" | domains: [career, travel, wealth]
  SIG.MSR.217: "D27 — Lagna Pisces = D1 12H Parallel: Strength-Foundation Rooted in Moksha Domain (SIG.26)" | domains: [spirit, health, travel, career]
  SIG.MSR.218: "D60 — Saturn at D60 Lagna (Gemini): Karmic-Primacy of Discipline at Past-Karma Origin (SIG.27)" | domains: [spirit, career, mind]
  SIG.MSR.219: "D60 — Ketu in D60 8H Capricorn: Past-Life Moksha-Crisis in Authority Domain" | domains: [spirit, health, mind]
  SIG.MSR.220: "D20 — Sun in D20 Pisces 5H (Vishnu-Affinity Trine): Structural Spiritual Architecture (SIG.28)" | domains: [spirit, mind, career]
  SIG.MSR.221: "D20 — Jupiter at D20 Lagna Scorpio: Guru-at-Spiritual-Origin = Dharmic-Research Sadhana Architecture" | domains: [spirit, mind, career]
  SIG.MSR.222: "D30 — Saturn+Mars+Venus Triple-Conjunction D30 6H Gemini: Internal Conflict Structural Register" | domains: [relationships, health, career, mind]
  SIG.MSR.223: "D40 — Jupiter+Venus D40 9H Taurus: Lakshmi-Dharma Recurrence Across Three Divisionals (D1, D9, D40)" | domains: [wealth, spirit, relationships, parents]
  SIG.MSR.224: "Divisional — Triple-Exalted Nodal Axis: Saturn(Libra D1 exalted) + Rahu(Taurus D1 classically exalted) + Ketu(Scorpio D1 classically exalted): Chart-Level Structural Exaltation Pattern (SIG.23)" | domains: [career, wealth, spirit, health, relationships]
  SIG.MSR.225: "Divisional — Vimsopaka Bala Assessment: Key Planetary Dignities Across 16 Divisionals" | domains: [career, wealth, spirit, health]
  SIG.MSR.226: "Divisional — D7 Saptamsha: Progeny Register; Twin-Daughter Signature (EVT.2022.01.03.01)" | domains: [children]
  SIG.MSR.227: "Divisional — D12 Dvadashamsha: Parental Ancestry Register; Leo Lagna; Father-Signification Weak Pattern (CTR.03 Echo)" | domains: [parents, family]
  SIG.MSR.228: "Sensitive-Point — Gulika in Gemini 3H (13°57′ Ardra): Calamity-Significator in House of Courage and Communication" | domains: [health, mind, relationships]
  SIG.MSR.229: "Sensitive-Point — Mandi in Cancer 4H (14°13′ Pushya): Malefic Shadow in House of Home, Mother, and Mental Peace" | domains: [health, mind, parents]
  SIG.MSR.230: "Sensitive-Point — Dhuma in Gemini 3H (5°17′ Mrigasira): Smoke-Point Co-Present with Gulika in 3H" | domains: [career, mind]
  SIG.MSR.231: "Sensitive-Point — Vyatipata in Capricorn 10H (24°42′ Dhanishta): Opposition-Malefic in Career House" | domains: [career, wealth]
  SIG.MSR.232: "Sensitive-Point — Parivesha in Cancer 4H (24°42′ Ashlesha): Encirclement-Point Co-Present with Mandi in 4H" | domains: [mind, parents]
  SIG.MSR.233: "Sensitive-Point — Indrachapa in Sagittarius 9H (5°17′ Moola): Rainbow-Arc in House of Dharma" | domains: [spirit, career, wealth]
  SIG.MSR.234: "Sensitive-Point — Upaketu in Sagittarius 9H (21°57′ Purva Ashadha): Pseudo-Ketu at Venus's Own Nakshatra in Dharma House" | domains: [spirit, wealth, relationships]
  SIG.MSR.235: "Sensitive-Point — Yogi Point in Pisces 12H (22°20′ Revati): Mercury-Blessed 12H Fortune-Accumulator" | domains: [wealth, spirit, career, travel]
  SIG.MSR.236: "Sensitive-Point — Yogi Planet Mercury: Chart's Fortune-Activator = Also Vargottama Career-Operational Planet — Dual-Function Structure" | domains: [career, wealth, spirit, travel]
  SIG.MSR.237: "Sensitive-Point — Avayogi Planet Mars: Chart's Fortune-ADVERSARY = Also Lagna Lord — Crisis-Identity Paradox" | domains: [wealth, career, health]
  SIG.MSR.238: "Sensitive-Point — Natal Bhrigu Bindu in Libra 7H (8°04′ Swati Pada 1): Life-Accumulation-Point in House of Saturn-Mars Conjunction" | domains: [relationships, career, wealth, spirit]
  SIG.MSR.239: "Sensitive-Point — Bhrigu Bindu Progression Age 42 (2026): BB at Gemini 20°04′ (Punarvasu Pada 1) in 3H" | domains: [career, wealth, mind]
  SIG.MSR.240: "Sensitive-Point — Bhrigu Bindu Transit Activation: Saturn-on-Natal-BB (2012) and Future Rahu-Return-to-BB (~2040)" | domains: [career, relationships, wealth]
  SIG.MSR.241: "Sensitive-Point — Pranapada Lagna in Pisces 12H (28°46′ Revati Pada 4): Prana-Vehicle at the End of the Zodiac, Mercury-Ruled" | domains: [spirit, health, travel]
  SIG.MSR.242: "Sensitive-Point — CONVERGENCE: Yogi Point + Pranapada Both in Revati 12H = Mercury-12H as Chart's Fortune-Prana Axis" | domains: [spirit, wealth, career, travel]
  SIG.MSR.243: "Sensitive-Point — Hora Lagna in Libra 7H (10°11′ Swati): Material-Wealth-Lagna Co-Present with Saturn-Mars-Bhrigu Bindu in 7H" | domains: [wealth, relationships, career]
  SIG.MSR.244: "Sensitive-Point — Bhava Lagna in Aries 1H (14°23′ Ashwini): Life-Force-Lagna on the Actual Natal Lagna Axis" | domains: [health, spirit]
  SIG.MSR.245: "Sensitive-Point — Ghati Lagna + Varnada Lagna BOTH in Scorpio 8H: Power-Authority Double-Lagna in Transformation House" | domains: [career, spirit, wealth]
  SIG.MSR.246: "Saham — Pitri (Father) in Capricorn 10H (12°90′ Shravana Pada 1): Father-Karaka in Career House; EVT.2018.11.28.01 Retrodict" | domains: [parents, career]
  SIG.MSR.247: "Saham — Mrityu (Death) in Sagittarius 9H (27°81′ Uttara Ashadha Pada 1): Hazard-Point in Dharma House Near Moola Boundary" | domains: [health, spirit, parents]
  SIG.MSR.248: "Saham — Paradesa (Foreign) in Aries 1H (15°08′ Bharani Pada 1): Foreign-Destiny Point ON THE NATAL LAGNA" | domains: [career, wealth, travel, spirit]
  SIG.MSR.249: "Saham — Vyapara (Business) in Capricorn 10H (8°99′ Uttara Ashadha Pada 4): Business-Destiny in Career House; EVT.2023-2024 Retrodict" | domains: [wealth, career]
  SIG.MSR.250: "Saham — Yasas (Fame) in Scorpio 8H (4°68′ Anuradha Pada 1): Fame-Accumulator in Transformation-Occult House" | domains: [career, spirit]
  SIG.MSR.251: "Saham — Roga+Mahatmya BOTH in Libra 7H: Disease-Point AND Greatness-Point Conjunct Saturn-Mars — The 7H Crucible Paradox" | domains: [health, career, wealth, spirit]
  SIG.MSR.252: "Saham — Samartha (Capability) in Aries 1H (12°43′ Ashwini Pada 4): Self-Capability-Point at Natal Lagna" | domains: [career, wealth, travel]
  SIG.MSR.253: "Saham — Shoka+Sraddha+Bandhu: Grief, Faith, and Kin in Pisces/Sagittarius — Hidden Emotional Architecture" | domains: [mind, spirit, relationships]
  SIG.MSR.254: "Sensitive-Point — 7H Libra Supreme Convergence: Saturn+Mars+BhriguBindu+HoraLagna+RogaSaham+MahatmyaSaham = Six-Layer Convergence in One House" | domains: [career, wealth, health, relationships, spirit]
  SIG.MSR.255: "Dasha — Mercury MD (2010-08-21 to 2027-08-21): 17-Year Operational-Excellence Arc as Yogi-Planet MD" | domains: [career, wealth, travel, mind]
  SIG.MSR.256: "Dasha — Mercury MD 10x Event-Density Pattern (SIG.29): Statistical Confirmation of Yogi-Planet MD Premium" | domains: [career, wealth, travel, relationships]
  SIG.MSR.257: "Dasha — Mercury-Mercury AD (2010-08-21 to 2013-01-18): Pure MD-lord AD = Career + Life Relaunch" | domains: [career, wealth, mind]
  SIG.MSR.258: "Dasha — Mercury-Saturn AD (2024-12-12 to 2027-08-21): CURRENT — Planting-to-Compounding Window" | domains: [career, wealth, relationships]
  SIG.MSR.259: "Dasha — Mercury-Jupiter AD (2022-09-06 to 2024-12-12): Highest-Density AD in Lifetime (5 Events in 27 months)" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.260: "Dasha — Mercury-Moon AD (2017-09-21 to 2019-02-21): AK Soul-Planet AD + Father's Death + US Move Trigger" | domains: [parents, mind, travel]
  SIG.MSR.261: "Dasha — Mercury-Ketu AD (2013-01-18 to 2014-04-15): Ketu-Closes-Karmic-Cycle; Marriage Event" | domains: [relationships, spirit]
  SIG.MSR.262: "Dasha — AD-Lord Domain Match 100% Pattern (SIG.30): Every AD Lord's Domain = Primary LEL-Event Domain" | domains: [career, wealth, relationships, spirit, parents]
  SIG.MSR.263: "Dasha — Ketu MD (2027-08-21 to 2034-08-21): 7-Year Withdrawal Phase Post-Mercury Operational Era" | domains: [spirit, health, wealth]
  SIG.MSR.264: "Dasha — Venus MD (2034-08-21 to 2054-08-21): 20-Year Prosperity-Creative Expansion as Dharmic-9H Planet" | domains: [wealth, relationships, career, spirit]
  SIG.MSR.265: "Dasha — Saturn MD Historical (1992-2010-overlap): 19-Year Foundation Era with Sade Sati Cycle 1 Embedded" | domains: [career, health, relationships]
  SIG.MSR.266: "Dasha — Yogini Dasha Bhadrika/Mercury → Ulka/Saturn Transition (Dec 2026): Yogini Regime Change Within Mercury-Saturn AD" | domains: [career, wealth]
  SIG.MSR.267: "Dasha — Chara Dasha Scorpio MD (from ~Feb 2026): Saturn-Karaka + Ketu-Exaltation Chara Period" | domains: [career, spirit, wealth]
  SIG.MSR.268: "Dasha — Saturn Own-Exaltation Return Libra 2041-2044: Lifetime-Apex Transit Within Venus MD (SIG.31)" | domains: [career, wealth, spirit, health]
  SIG.MSR.269: "Dasha — Ketu MD Ketu-Rahu AD (2030-07-21 to 2031-08-09): Rahu Transit on Natal Ketu = Nodal-Reversal Crisis Window" | domains: [career, wealth, health, spirit]
  SIG.MSR.270: "Dasha — Mars MD Future (Post-Venus MD ~2054): Avayogi-Planet MD at Age 70+ — Karmic-Final-Arc" | domains: [health, spirit]
  SIG.MSR.271: "Transit — Saturn in Pisces 12H (2025-03-30 to 2028-02-23 approx): Triple-Activation Setting Phase (SIG.25)" | domains: [spirit, wealth, travel]
  SIG.MSR.272: "Transit — Rahu in Aquarius (11H) Transiting Natal Moon: Double-AK Activation 2025-2026" | domains: [wealth, mind, career]
  SIG.MSR.273: "Transit — Jupiter in Taurus 2H (2025-2026): 2H Wealth-Expansion Over Natal Rahu" | domains: [wealth, career, family]
  SIG.MSR.274: "Transit — Jupiter in Cancer (4H) Exalted 2026-2027: Gajakesari Yoga Renewed by Transit" | domains: [wealth, spirit, mind, parents]
  SIG.MSR.275: "Transit — Saturn Historical Capricorn 10H (2020-2023): Career-Structural Crystallization" | domains: [career, wealth]
  SIG.MSR.276: "Transit — Jupiter in Aquarius 11H Gajakesari with Natal Moon (2021-2022): Twin-Birth Window" | domains: [children, wealth]
  SIG.MSR.277: "Transit — Saturn in Sagittarius 9H (2017-2020): Father's Death Transit — Classical Pitru-Dosha Activation" | domains: [parents, spirit]
  SIG.MSR.278: "Transit — Saturn in Aries 1H (2028-2030): Debilitated Saturn on Lagna — Identity-Crisis Window" | domains: [health, career, spirit]
  SIG.MSR.279: "Transit — Rahu in Gemini (3H) 2031-2033: On UL Spouse-Karma Reset Window" | domains: [relationships, career]
  SIG.MSR.280: "Transit — Saturn-Venus-Rahu AD Convergence 2041-2044: Lifetime-Apex Transit Window (SIG.31)" | domains: [career, wealth, spirit]
  SIG.MSR.281: "Transit — Annual Sun Transit Aries (Lagna Activation): April-May Every Year = Peak Identity-Expression Window" | domains: [career, wealth]
  SIG.MSR.282: "Transit — Mars Transit Capricorn (10H) = Career-Launch Trigger (SIG.24): Annual Activation Pattern" | domains: [career, wealth]
  SIG.MSR.283: "Transit — Jupiter in Leo 5H (2028-2029): Post-Sade-Sati Children-Fortune Window" | domains: [children, spirit, mind]
  SIG.MSR.284: "Transit — Saturn Taurus Kantaka (2H, 2029-2032): Rahu-Over-Saturn Wealth-Friction Window" | domains: [wealth, health]
  SIG.MSR.285: "Transit — Jupiter-Aquarius 2033 Gajakesari Recurrence: End-of-Ketu-MD Fortune Surge" | domains: [wealth, children, spirit]
  SIG.MSR.286: "Transit — Jupiter in Pisces 12H (2034 future): Yogi-Point Activation in Venus MD Opening" | domains: [spirit, wealth, travel]
  SIG.MSR.287: "Transit — Ketu Transit Scorpio 8H (Natal Position Return ~2039-2040): Nodal Homecoming" | domains: [spirit, health, wealth]
  SIG.MSR.288: "Transit — Eclipse Impact: 5 Eclipses Within 6 Months of Father's Death (2018)" | domains: [parents]
  SIG.MSR.289: "Transit — Saturn Pisces Setting Sade Sati + Jupiter Cancer Exalted (2026): The Current Dual Fortune-Structure Window" | domains: [spirit, wealth, mind]
  SIG.MSR.290: "Transit — Mars-Transit-Libra (7H) Annual: Activating the Supreme Convergence Zone" | domains: [career, relationships, wealth]
  SIG.MSR.291: "Sade Sati — Chart Overview: Moon in Aquarius = 4 Lifetime Cycles (Ages 6-13, 36-44, 65-72, 95-102)" | domains: [health, career, mind, wealth]
  SIG.MSR.292: "Sade Sati — Cycle 2 Peak Phase: Saturn in Aquarius 11H (2022-04-29 to 2025-03-29)" | domains: [career, wealth, spirit, relationships]
  SIG.MSR.293: "Sade Sati — Cycle 2 Rising Phase: Saturn in Capricorn 10H (2020-01-24 to 2023-01-17)" | domains: [career, health]
  SIG.MSR.294: "Sade Sati — Cycle 2 Setting Phase (CURRENT): Saturn in Pisces 12H (2025-03-30 to 2028-02-23)" | domains: [wealth, spirit, family]
  SIG.MSR.295: "Sade Sati — Cycle 1 Peak (1993-1995, Ages 9-11): Headache Onset and R#1 Roots" | domains: [health, mind, relationships]
  SIG.MSR.296: "Sade Sati — Own-Sign Double Mitigation: Rising (Capricorn) + Peak (Aquarius) = Both Saturn's Own Signs" | domains: [career, wealth, spirit, health]
  SIG.MSR.297: "Sade Sati — Cycle 3 Projected (2049-2058, Ages 65-74): The Elder-Recalibration Cycle" | domains: [health, spirit]
  SIG.MSR.298: "Sade Sati — Cycle 2 Paradox: Highest LEL-Event Density Coincides with Sade Sati Peak — Chart's Most Counterintuitive Finding" | domains: [career, wealth, spirit]
  SIG.MSR.299: "Sade Sati — Cycle 1 Setting Phase (1996-1998): R#1 Launch at Sade Sati Exit" | domains: [relationships]
  SIG.MSR.300: "Sade Sati — Shani Kakshya During Peak: Saturn's Nakshatra Beam in Aquarius 11H" | domains: [health, mind, career]
  SIG.MSR.301: "Sade Sati — End-of-Cycle-2 Date (2028-02-23): 7.5-Year Complete Liberation" | domains: [health, mind, spirit]
  SIG.MSR.302: "Sade Sati — Cycle 2 Rising Phase (Capricorn 10H) Produces Own-Sign Saturn: Career-Not-Health as Primary Theme" | domains: [career, wealth]
  SIG.MSR.303: "KP — Cusp 10 (Career) Sub-Lord Saturn: Career Promise Delivered Through Saturn's Structural Discipline" | domains: [career]
  SIG.MSR.304: "KP — Cusp 11 (Gains) Sub-Lord Mercury: Yogi-Planet Governs the Gain-Cusp — Fortune × Gains = One Planet" | domains: [wealth, career]
  SIG.MSR.305: "KP — Cusp 7 (Spouse) Sub-Lord Saturn: Marriage Adjudicated by Exalted Saturn — Structured and Delayed" | domains: [relationships]
  SIG.MSR.306: "KP — Cusp 2 (Wealth) Sub-Lord Rahu: Wealth-Promise Delivered Through Unconventional Channels" | domains: [wealth]
  SIG.MSR.307: "KP — Cusp 1 (Lagna) Sub-Lord Mercury: Self-Identity Delivered Through Mercury's Intelligence" | domains: [career, spirit, mind]
  SIG.MSR.308: "KP — Cusp 9 (Fortune) Sub-Lord Jupiter: Fortune-Cusp Delivered by 9L in Own Sign — Maximum Cusp Promise" | domains: [wealth, spirit, career]
  SIG.MSR.309: "KP — Cusp 12 (Loss/Investment) Sub-Lord Saturn: Investments and Hidden Expenditures Through Saturn's Channel" | domains: [wealth, spirit, travel]
  SIG.MSR.310: "KP — Saturn KP Sub-Lord = Saturn: Saturn Self-References Its Own Delivery" | domains: [career, wealth, spirit]
  SIG.MSR.311: "KP — Venus KP Sub-Lord = Rahu: Venus-Delivered Fortune Channels Through Rahu's Ambition" | domains: [wealth, relationships, spirit]
  SIG.MSR.312: "KP — Mercury KP Sub-Lord = Rahu: Mercury's Operational Intelligence Flows Through Rahu's Innovation" | domains: [career, wealth, mind]
  SIG.MSR.313: "KP — H10 (Career) Significators: ALL 9 Planets Except Jupiter and Moon — Career Touches Everything" | domains: [career]
  SIG.MSR.314: "KP — H11 (Gains) Significators: Sun, Rahu, Moon, Saturn — Moon AK is a Primary Gain-Significator" | domains: [wealth]
  SIG.MSR.315: "KP — Saturn as Multi-Cusp Sub-Lord: Governs Cusps 6, 7, 10, 12 — The Chart's KP Anchor Planet" | domains: [career, wealth, relationships, health]
  SIG.MSR.316: "KP — H12 Significators: Saturn and Jupiter — Spiritual-Investment Duality" | domains: [spirit, wealth, travel]
  SIG.MSR.317: "Jaimini — Moon as Atmakaraka (AK): Soul-Significator in Own-Sign Saturn = Disciplined-Soul Architecture" | domains: [spirit, career, wealth]
  SIG.MSR.318: "Jaimini — Saturn as Amatya Karaka (AmK): Career-Minister-Significator = Exalted Planet" | domains: [career, wealth]
  SIG.MSR.319: "Jaimini — Mercury as Darakaraka (DK): Spouse-Significator = Vargottama Yogi Planet" | domains: [relationships, career]
  SIG.MSR.320: "Jaimini — Mars as Putrakaraka (PK): Children-Significator = Avayogi Lagnesh in 7H" | domains: [children, spirit]
  SIG.MSR.321: "Jaimini — Jupiter as Gnatri Karaka (GK): Relatives/Community Significator = Own-Sign 9H" | domains: [spirit, career, relationships]
  SIG.MSR.322: "Jaimini — Arudha Lagna (AL) in Capricorn 10H: Public-Image in Career House (Sun+Mercury)" | domains: [career, wealth]
  SIG.MSR.323: "Jaimini — Upapada Lagna (UL) in Gemini 3H: Spouse-Image in Communication House" | domains: [relationships]
  SIG.MSR.324: "Jaimini — A7 (Partner Arudha) in Aquarius 11H (Moon AK's House): Partners Connect at Soul Level" | domains: [relationships, wealth, career]
  SIG.MSR.325: "Jaimini — A6 (Enemy Arudha) in Taurus 2H (With Rahu): Enemies Enter Through Wealth-Gate" | domains: [wealth, health]
  SIG.MSR.326: "Jaimini — Karakamsa in Gemini (D9): Mercury-Ruled Karma; Sri Krishna / Vishnu as Palana Devata" | domains: [spirit, career]
  SIG.MSR.327: "Jaimini — Rahu Quadruple Jaimini Aspect (SIG.16): Taurus Fixed → Cancer+Libra+Capricorn = 4 Planets" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.328: "Jaimini — Fixed-Sign Yoga: 3 of 4 Fixed Signs Occupied (Taurus+Leo+Scorpio+Aquarius Configuration)" | domains: [spirit, career, wealth, relationships]
  SIG.MSR.329: "Jaimini — Argala from 2H: Rahu Argala on Lagna-System" | domains: [career, wealth, spirit]
  SIG.MSR.330: "Jaimini — AK-DK Connection (Moon-Mercury): Soul and Spouse Linked = Spouse as Soul-Mirror" | domains: [relationships, spirit]
  SIG.MSR.331: "Jaimini — Ketu in Scorpio (Fixed) Rashi Drishti: Aspects Aries+Cancer+Libra = Lagna+4H+7H Trikona of Fixed-Axis" | domains: [spirit, career, mind]
  SIG.MSR.332: "Jaimini — Moon in Aquarius (Fixed) Rashi Drishti: AK Aspects Aries+Cancer+Capricorn = Lagna+4H+10H Activation" | domains: [spirit, relationships, career, mind]
  SIG.MSR.333: "Jaimini — Jupiter+Venus in Sagittarius (Dual) Rashi Drishti: 9H Aspects Fixed Signs = Taurus+Leo+Scorpio+Aquarius" | domains: [spirit, wealth, children, career]
  SIG.MSR.334: "Jaimini — Mercury in Capricorn (Movable) Rashi Drishti: DK+Vargottama Aspects Dual Signs = Gemini+Virgo+Sagittarius+Pisces" | domains: [relationships, career, spirit, wealth]
  SIG.MSR.335: "Jaimini — Saturn in Libra (Movable) Rashi Drishti: AmK Aspects Dual Signs = Gemini+Virgo+Sagittarius+Pisces" | domains: [career, relationships, spirit, wealth]
  SIG.MSR.336: "Jaimini — A7 (Darapada) = Aquarius 11H = Exactly with Moon AK: Soul and Spouse-Image Fused" | domains: [relationships, spirit]
  SIG.MSR.337: "Jaimini — A6 (Shatrupada) = Taurus 2H = Exactly with Rahu: Enemies from Wealth/Foreign Domain" | domains: [wealth, career, relationships]
  SIG.MSR.338: "Jaimini — UL (Upapada Lagna) = Gemini 3H: Spouse from Communication/Sibling-Domain; Mercury-Ruled Marriage" | domains: [relationships]
  SIG.MSR.339: "Jaimini — AL (Arudha Lagna) = Capricorn 10H: Public Image IS Career — Identity and Reputation Fused" | domains: [career, wealth]
  SIG.MSR.340: "Jaimini — AK (Moon 11H) + AmK (Saturn 7H) Rajayoga: Soul-Force and Career-Force in Kendra = Classical Rajayoga" | domains: [career, wealth, spirit]
  SIG.MSR.341: "Jaimini — GK Jupiter in Own Sign (Sagittarius 9H): Gnati Karaka at Maximum Strength = Litigation/Competitor Challenges Overcome by Dharmic Force" | domains: [career, spirit, health]
  SIG.MSR.342: "Jaimini — MK Venus in Sagittarius 9H with Jupiter: Matri Karaka with GK = Mother-Archetype and Challenge-Domain Fused in Dharma House" | domains: [spirit, parents]
  SIG.MSR.343: "Jaimini — PK Mars in Libra 7H: Putra Karaka in Relationship House = Children-Domain Colored by Saturn's Conjunction" | domains: [children, relationships]
  SIG.MSR.344: "Jaimini — BK Sun in Capricorn 10H: Bhratri Karaka in Career House = Siblings-Domain Fused with Professional Life" | domains: [career, relationships]
  SIG.MSR.345: "Jaimini — Chara Dasha Current Period: Scorpio MD (2025-2026 approx.) = Ketu-8H Period = Moksha-Release-Transformation Window" | domains: [spirit, wealth, health]
  SIG.MSR.346: "Jaimini — Moon-AK Argala on 10H (from 11H): Soul-Force Intervenes in Career = Career Receives Soul-Blessing" | domains: [career, spirit]
  SIG.MSR.347: "Jaimini — Jupiter+Venus (9H) Argala on 6H (Virodha of 7H Argala): Dharmic Benefics Counter-Balance the 7H Malefic Concentration" | domains: [spirit, relationships, career]
  SIG.MSR.348: "Jaimini — Navamsha Karakamsa Integration: Mercury Vargottama in D9 Capricorn + Karakamsa Gemini = Mercury-Twin Confirmation of Soul-Path" | domains: [career, spirit, wealth]
  SIG.MSR.349: "Jaimini — Rashi Drishti Convergence on Capricorn 10H: Receives Jaimini Aspects from Aries+Cancer+Libra (All Movable Signs) = 10H is Chart's Most-Aspected House via Jaimini" | domains: [career, spirit, wealth]
  SIG.MSR.350: "Jaimini — Chart-Level Integration: The Chart's Jaimini Architecture = Three Interlocking Rajayoga Mechanisms" | domains: [career, wealth, spirit]
  SIG.MSR.351: "Panchang — Birth Tithi: Shukla Chaturdashi (14th bright fortnight) = Moon near Full = Maximum Lunar Power at Birth" | domains: [mind, spirit]
  SIG.MSR.352: "Panchang — Birth Vara: Sunday (Ravivar) = Sun-Day Birth = Authority, Sovereignty, Father-Karma, and Solar Destiny" | domains: [career, parents, spirit]
  SIG.MSR.353: "Panchang — Birth Nakshatra (Janma Nakshatra): Purva Bhadrapada (Moon's Nakshatra) = Jupiter-Ruled, Fiery, Spiritually Aggressive" | domains: [spirit, mind]
  SIG.MSR.354: "Panchang — Birth Yoga: Shiva Yoga or Parigha Yoga at Birth = [PANCHANG CALCULATION REQUIRED]" | domains: [spirit]
  SIG.MSR.355: "Panchang — Birth Karana: Vishti (Bhadra) Karana = The Most Inauspicious Karana = Fierce-Initiation Birth Environment" | domains: [mind, spirit, career]
  SIG.MSR.356: "Panchang — Nakshatra Pada at Birth: Purva Bhadrapada Pada 3 (Leo Navamsha) = Soul's Emotional-Royal-Mode" | domains: [mind, spirit]
  SIG.MSR.357: "Panchang — Lagna Nakshatra: Ashwini Pada 4 = Ketu-Ruled Birth Rising = Spiritual Acceleration of Identity" | domains: [spirit, career, health]
  SIG.MSR.358: "Panchang — Tithi Lord: Chaturdashi Tithi Lord = Shiva = Transformation Deity Governs Birth Moment" | domains: [spirit]
  SIG.MSR.359: "Panchang — Vara Lord: Sunday Lord = Sun = Sun-God's Day Governs Birth = Authority and Father-Karma from Birth-Moment" | domains: [career, parents]
  SIG.MSR.360: "Panchang — Nakshatra Lord (Janma): Purva Bhadrapada Lord = Jupiter = Dharmic Mind-Expansion as Emotional Foundation" | domains: [mind, spirit, career]
  SIG.MSR.361: "Panchang — Amrita Siddhi Yoga: Sunday + Ashwini Nakshatra = One of the Rare Amrita Siddhi Yoga Combinations" | domains: [spirit, health]
  SIG.MSR.362: "Panchang — Chandra Bala (Birth Nakshatra in Transit): Current Moon Transits and Natal Nakshatra Resonance" | domains: [mind, career]
  SIG.MSR.363: "Panchang — Tarabala: Birth Nakshatra as Reference for 27-Nakshatra Tarabala Cycle = Which Nakshatras Are Beneficial Periods" | domains: [career, wealth, health]
  SIG.MSR.364: "Panchang — Birth Month: Magha Month (Paush/Magha Masya) = Sun in Capricorn Makar = Solar Capricorn-Season Birth" | domains: [career, spirit, parents]
  SIG.MSR.365: "Panchang — Ganda Moola: Native NOT Born in Ganda Moola (No Junction-Nakshatra at Lagna or Moon) = Auspicious Clear Birth" | domains: [spirit, health]
  SIG.MSR.366: "Panchang — Birth Hour: 10:43 IST = Late Morning Birth = Sun Near Culmination = Solar Power Ascending to Meridian" | domains: [career, spirit]
  SIG.MSR.367: "Panchang — Panchang Tatva Score: All 5 Panchang Elements Assessed = Net Auspiciousness of Birth Moment" | domains: [spirit, career, mind]
  SIG.MSR.368: "Panchang — Naamakshara (Birth Syllable): Purva Bhadrapada Pada 3 = 'De' Syllable = Mercury-Beginning Name Energy" | domains: [spirit]
  SIG.MSR.369: "Panchang — Tri-Nadi Dasha (Prana-Agni-Soma): Purva Bhadrapada = Agni (Fire) Nadi = Fire-Force as Emotional Ground" | domains: [health, spirit]
  SIG.MSR.370: "Panchang — Varna: Purva Bhadrapada = Brahmin Varna = Knowledge-Dharma Archetype at Soul Level" | domains: [spirit, career]
  SIG.MSR.371: "Panchang — Gana: Purva Bhadrapada = Manushya (Human) Gana = Balanced, Practical-Spiritual Temperament" | domains: [spirit, relationships]
  SIG.MSR.372: "Panchang — Yoni: Purva Bhadrapada = Simha (Lion) Yoni = Regal, Fierce, Non-Submissive Instinct" | domains: [spirit, relationships]
  SIG.MSR.373: "Panchang — Tattva: Purva Bhadrapada = Agni (Fire) Tattva + Aquarius = Vayu (Air) Sign = Fire-Air Soul in Air-Structured Environment" | domains: [health, spirit]
  SIG.MSR.374: "Panchang — Devata of Nakshatra: Aja Ekapada (Purva Bhadrapada Devata) = The One-Footed Goat = Rudra-Form Deity as Emotional Guardian" | domains: [spirit, career]
  SIG.MSR.375: "Panchang — Section Synthesis: 5 Panchang Pillars Point to Intense-Transformational-Knowledge-Seeking Birth Environment" | domains: [spirit, career, mind]
  SIG.MSR.376: "Tajika — Varshaphal Framework: Annual Chart Methodology for Abhisek Mohanty (Solar Return = Sun Returns to Natal Position)" | domains: [career, wealth]
  SIG.MSR.377: "Tajika — Muntha Position at Age 42 (2026): Muntha in Gemini 3H = UL/Spouse-Domain Annual Activation" | domains: [health, career, wealth]
  SIG.MSR.378: "Tajika — Ithasala Yoga: When Two Planets Are Converging in Degree = Action-Producing Tajika Yoga" | domains: [career, wealth]
  SIG.MSR.379: "Tajika — Ishrafa (Separation) Yoga: Retrograde or Past-Separation Patterns in Annual Chart = Years of Completion Rather Than Initiation" | domains: [career, wealth]
  SIG.MSR.380: "Tajika — Varshesha (Year Lord) Identification: The Strongest Planet in Each Annual Chart Governs That Year's Theme" | domains: [career, wealth]
  SIG.MSR.381: "Tajika — Tajika Special Lagna: Varshaphal Lagna Changes Each Year at Different Location = Singapore vs Bhubaneswar Annual Lagna Divergence" | domains: [career, wealth]
  SIG.MSR.382: "Tajika — Sahama in Varshaphal: Annual Sahamas as Tajika Sensitive Points" | domains: [career, wealth]
  SIG.MSR.383: "Tajika — Tri-Pataki Chakra: The 3-Sign Trident from Annual Lagna = Strongest Tajika Directional Sectors" | domains: [career, wealth, spirit]
  SIG.MSR.384: "Tajika — Mudda Dasha in Varshaphal: 12 Monthly Sub-Periods Within Each Annual Chart = Monthly Resolution Layer" | domains: [career, wealth]
  SIG.MSR.385: "Tajika — Natal Saturn Exalted as Perennial Tajika Year-Lord Candidate: Saturn-Strong Annual Charts = Structural Achievement Years" | domains: [career, wealth]
  SIG.MSR.386: "Tajika — Dwisaptati Sama Dasha (72-Year Dasha): Sun in 7H of Annual Chart = Tajika Conditional Dasha Condition" | domains: [career, spirit]
  SIG.MSR.387: "Tajika — Section Synthesis: Varshaphal as Annual Resolution Layer = Mercury-Saturn Pair as Most Potent Tajika Annual Focus 2024-2027" | domains: [career, wealth, health]
  SIG.MSR.388: "Meta-Convergence — Mercury Quintuple Confirmation: MD Lord + Yogi Planet + Vargottama + DK + Karakamsa Sign Lord = Five Independent Mercury Confirmations" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.389: "Meta-Convergence — Saturn Triple Structural Axis: Exalted (D1) + AK's Sign (D1 Aquarius/Moon) + AmK (Jaimini) + Sub-Lord of 4 Cusps (KP) = Four Systems" | domains: [career, wealth, relationships, spirit, health]
  SIG.MSR.390: "Meta-Convergence — 10H Capricorn Quadruple Layer: Natal Planets (Sun+Mercury) + AL (Jaimini) + Jaimini Rashi Drishti from Rahu+Ketu+Leo + KP Sub=Saturn" | domains: [career, wealth, spirit]
  SIG.MSR.391: "Vivaha Saham in 4H Cancer Pushya — Marriage-Fortune Anchored in Domestic-Maternal Domain" | domains: [relationships, parents, mind]
  SIG.MSR.392: "Meta-Convergence — Pisces 12H Fortune Cluster: Yogi Point + Pranapada + KP Cusp 12 Sub=Saturn = Three Fortune-Isolation Layers" | domains: [spirit, career, wealth]
  SIG.MSR.393: "Meta-Convergence — Nodal Axis Four-System Lock: Rahu (Taurus 2H) + Ketu (Scorpio 8H) Confirmed Across Parashari + Jaimini + KP + Sensitive Points" | domains: [wealth, relationships, spirit]
  SIG.MSR.394: "Meta-Convergence — Jupiter-Venus 9H Dual Benefic: GK+MK Both Own/Exalted Domain + Tri-Pataki Trikona + Dual-Sign Jaimini Coverage" | domains: [spirit, career, wealth, parents]
  SIG.MSR.395: "Meta-Convergence — Sunday + Ashwini + Saturn Hora: Panchang's Three Time-Lords = Sun + Ketu + Saturn = The Chart's Primary Trio" | domains: [spirit, career, relationships]
  SIG.MSR.396: "Meta-Convergence — Sade Sati Paradox Confirmed Across Three Systems: Parashari (Moon Own-Sign Mitigation) + LEL Retrodiction (Best Events in Peak) + KP (Aquarius Sub=Mercury)" | domains: [career, wealth, spirit]
  SIG.MSR.397: "Meta-Convergence — Devata Retrodiction Loop: Palana=Mercury/Vishnu + Dharma=Saturn/Venkateswara + Ishta=Venus/Mahalakshmi = Jaimini + EVT.2025 + Panchang Triple-Lock" | domains: [spirit]
  SIG.MSR.398: "Meta-Convergence — Mars as Avayogi + PK + 7H Placement: The Chart's Deliberate Weakness = Relationship/Children Domain Has Structural Friction" | domains: [relationships, children, wealth]
  SIG.MSR.399: "Meta-Convergence — 1H Aries Empty but Convergent: Lagna + Bhava Lagna + Saham Samartha + Saham Paradesa within 3° Arc = Four-Layer 1H Convergence" | domains: [career, spirit, travel]
  SIG.MSR.400: "Meta-Convergence — Mercury-Saturn Mutual-Reinforcement: 10H-7H Parashari Mutual Reception + Jaimini Rashi Drishti + KP AD Pair + Current Vimshottari = Four Simultaneous Mercury-Saturn Systems" | domains: [career, wealth]
  SIG.MSR.401: "Meta-Convergence — Rahu Exalted in Nakshatra of Moon's Most Favored Domain: Rohini (Moon-Ruled) = Rahu Absorbs Moon's Nourishing Frequency in 2H" | domains: [wealth, career, relationships]
  SIG.MSR.402: "Domestic-Dharmic Authority Architecture — Varnada in 4H Cancer + Ghati in 9H Sagittarius (REPLACEMENT FOR MSR.402)" | domains: [relationships, spirit, career, parents]
  SIG.MSR.403: "Meta-Convergence — Venus as Triple-Role Planet: 2L+7L (Parashari) + MK (Jaimini) + Ishta Devata (Jaimini Karakamsa) = Wealth-Marriage-Fortune Triad" | domains: [wealth, relationships, spirit, parents]
  SIG.MSR.404: "BB-UL 2026 Five-Fold Crystallization — Quadruple-Loaded Gemini 3H Convergence (v2.0 UPGRADED)" | domains: [relationships, wealth, career, mind]
  SIG.MSR.405: "Meta-Convergence — Triple Exalted Nodal Axis + D27 Confirmation: Saturn+Rahu+Ketu All Exalted in D1 AND Nodal Axis Confirmed in D27" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.406: "Meta-Convergence — Moon-AK Purva Bhadrapada + Nakshatra Lord Jupiter Own-Sign + Janma Nakshatra Devata Aja Ekapada: Soul in a Fully-Resourced Nakshatra" | domains: [spirit, career]
  SIG.MSR.407: "9H Jupiter-Venus Laxmi-Narayana-Adjacent Architecture — Shree Lagna OUT of 9H (v2.0)" | domains: [spirit, wealth, career, relationships]
  SIG.MSR.408: "Meta-Convergence — Ghati Lagna + Varnada in Scorpio 8H: Transformation Domain is Power-Authority Apex + Soul-Ranking House" | domains: [career, spirit, mind]
  SIG.MSR.409: "Meta-Convergence — KP Cusp 11 Sub=Mercury (Yogi) + Moon in 11H (AK) + A7 in 11H: Gains House is Simultaneously KP-Mercury + Soul-Planet + Spouse-Image" | domains: [wealth, relationships, spirit]
  SIG.MSR.410: "Meta-Convergence — The Chart's Two Supreme Convergence Zones: 7H Libra (Six Layers) vs 11H Aquarius (Three Layers) = Relationship-karma and Soul-Fulfillment as Dual Epicenters" | domains: [relationships, wealth, spirit, career]
  SIG.MSR.411: "Meta-Convergence — Mars-Saturn 7H Exact Degree Proximity: 22°27' vs 18°31' = 3°56' Apart = Within Classical 5° Orb = Tight Conjunction" | domains: [relationships, career]
  SIG.MSR.412: "Meta-Convergence — Jupiter-Venus Exact Degree Proximity in 9H: Purva Ashadha Pada 2 vs Moola Pada 3 = Same Nakshatra Family = Sagittarius Dual-Benefic Bond" | domains: [spirit, wealth, relationships]
  SIG.MSR.413: "Mercury Eight-System Convergence — Chart's Primary Operational Planet (v2.0 UPGRADED from Seven)" | domains: [career, wealth, relationships, mind, spirit]
  SIG.MSR.414: "Meta-Convergence — Saturn Apex 2041-2044: Saturn Return (Libra) + SIG.31 + Current Sade Sati Setting (Pisces) Building Toward the Return" | domains: [career, wealth, spirit]
  SIG.MSR.415: "Meta-Convergence — The Whole Chart as Organism: Primary Axis (7H-1H), Secondary Axis (10H-4H), Soul Axis (11H-5H) = Three Kendra Axes All Activated" | domains: [career, wealth, relationships, spirit, health, children, parents, mind, travel]
  SIG.MSR.416: "Statistics — Signal Distribution by Type (415 signals enumerated)" | domains: []
  SIG.MSR.417: "Statistics — Confidence Distribution: High (≥0.85) vs Medium (0.70-0.84) vs Low (<0.70) Signal Breakdown" | domains: []
  SIG.MSR.418: "Statistics — Domain Coverage Matrix: All 9 Domains Covered Across All 16 Signal Types" | domains: [career, wealth, spirit, relationships, mind, health, children, parents, travel]
  SIG.MSR.419: "Statistics — Open Gaps Requiring Future Resolution (Red-Team Register)" | domains: []
  SIG.MSR.420: "Statistics — MSR_v1_0 Completeness Certificate: 420 Signals, 16 Signal Types, 9 Domains, Acharya-Grade Coverage" | domains: [career, wealth, spirit, relationships, mind, health, children, parents, travel]
  SIG.MSR.421: "Kalpadruma / Parijata Yoga (D-1) — Royal Yoga of Principled Warrior King" | domains: [career, wealth, relationships, spirit]
  SIG.MSR.422: "Chaamara Yoga (D-1) — Long-Lived, Scholarly, Eloquent Native" | domains: [career, mind, spirit]
  SIG.MSR.423: "Mridanga Yoga (D-1) — King or Equal, Happy, Well-Honored" | domains: [career, wealth, relationships]
  SIG.MSR.424: "Sankha Yoga (D-1) — Wealth, Good Spouse-and-Children, Kind, Pious, Long-Lived" | domains: [relationships, wealth, children, spirit]
  SIG.MSR.425: "Vosi Yoga (D-1) — Skillful, Charitable, Learned, Successful" | domains: [career, spirit, wealth]
  SIG.MSR.426: "Anaphaa Yoga (D-1) — Comforts, Good Character, Self-Reliant" | domains: [mind, career, wealth]
  SIG.MSR.427: "Kedaara Naabhasa Yoga (D-1, Lifetime) — Happy, Wealthy, Helpful" | domains: [career, wealth, spirit, mind]
  SIG.MSR.428: "Gaja-Kesari Yoga in D-9 Navamsa — Famous and Virtuous (MAJOR D-9 YOGA)" | domains: [spirit, career, mind, wealth]
  SIG.MSR.429: "Kaahala Yoga (D-9) — Strong, Bold, Leads Large Enterprise" | domains: [career, wealth, spirit]
  SIG.MSR.430: "Raja-Lakshmi Yoga (D-9) — Fortunate, High Achiever (Moon + Jupiter)" | domains: [career, wealth, spirit, mind]
  SIG.MSR.431: "Yogakaraka Mars (D-9, D-10) — Same Planet Owns Kendra + Kona = Success" | domains: [career, wealth, spirit]
  SIG.MSR.432: "Raja Yoga AK-PK (D-9) — Loyal Following and Power (Moon + Rahu)" | domains: [career, relationships, spirit]
  SIG.MSR.433: "Viparita Raja Yoga Jupiter (D-9) — Success After Pressures, Others' Losses Become Native's Opportunity" | domains: [career, wealth, spirit]
  SIG.MSR.434: "Sarala Viparita Raja Yoga (D-10) — Long-Lived, Fearless, Learned, Celebrated, Prosperous in Career Chart" | domains: [career, wealth, health]
  SIG.MSR.435: "Maha Yogada (D-2 Hora) — Power, Authority, and Wealth (Jupiter Associated with Lagna + GL + HL)" | domains: [wealth, career, spirit]
  SIG.MSR.436: "Sadhu Yoga (D-2 Hora) — Saintly Character, Spiritually Grounded Wealth" | domains: [wealth, spirit, mind]
  SIG.MSR.437: "Birth Yoga = Siva (Mercury-Ruled) — Auspicious Yoga Lord Convergence (GAP.01 RESOLVED)" | domains: [spirit, career, mind, wealth]
  SIG.MSR.438: "Saturn Ishta Phala 43.28 / Kashta 4.81 — ~9:1 Beneficial Delivery Ratio (Primary Phala Planet)" | domains: [career, wealth, relationships, health]
  SIG.MSR.439: "Jupiter Ishta 10.78 / Kashta 48.81 — ~1:5 Malefic Phala Despite Maximum Pancha-Vargeeya (CTR.03 Quantified)" | domains: [parents, children, spirit, wealth]
  SIG.MSR.440: "Bhava Bala 5H Rank 1 (Strongest) — Purva Punya-Children-Creativity House is Structurally Strongest" | domains: [children, mind, spirit, wealth]
  SIG.MSR.441: "Pancha-Vargeeya Operational Triad — Mercury + Jupiter + Saturn = Three POWERFUL Classifications" | domains: [career, wealth, spirit, mind]
  SIG.MSR.442: "Kalachakra Paramayush = 85 Years (Savya Scheme) — Longevity Structural Indicator (LONGEVITY.GAP.01 Partial Resolution)" | domains: [health]
  SIG.MSR.443: "Special Lagna Comprehensive Architecture v8.0 — Four-Lagna Distribution" | domains: [relationships, spirit, career, wealth, health, parents]
  SIG.MSR.444: "Lagna Nakshatra — Ashwini Pada 4 Fire-Initiative Gate" | domains: [career, mind]
  SIG.MSR.445: "Moon Nakshatra — Purva Bhadrapada III Collective-AK Thread" | domains: [relationships, spirit]
  SIG.MSR.446: "Sun Nakshatra — Shravana Pada 4 Career Listening Intelligence" | domains: [career]
  SIG.MSR.447: "Mars Nakshatra — Swati Pada 4 Relational Calibration" | domains: [relationships]
  SIG.MSR.448: "Mercury Nakshatra — Uttarashada Pada 2 Vargottama Spine" | domains: [career, mind]
  SIG.MSR.449: "Jupiter Nakshatra — Purva Ashadha Pada 3 Dharma Pouring" | domains: [spirit, wealth]
  SIG.MSR.450: "Venus Nakshatra — Purva Ashadha Pada 2 Lakshmi Adjacent" | domains: [wealth, relationships]
  SIG.MSR.451: "Saturn Nakshatra — Vishakha Pada 1 Exalted Structural Spine" | domains: [career, relationships]
  SIG.MSR.452: "Rahu Nakshatra — Rohini Pada 3 Wealth Magnetism" | domains: [wealth]
  SIG.MSR.453: "Ketu Nakshatra — Jyeshtha Pada 1 Occult Precision" | domains: [spirit, health]
  SIG.MSR.454: "Indu Lagna Nakshatra — Jyeshtha Pada 4 Hidden Fortune Vector" | domains: [wealth, spirit]
  SIG.MSR.455: "Bhava Lagna Nakshatra — Revati Pada 3 Moksha Float" | domains: [spirit, travel]
  SIG.MSR.456: "Saham Punya in Gemini 3H — Merit Routing Through Communication Nexus" | domains: [wealth, career]
  SIG.MSR.457: "Saham Yasas in Scorpio 8H — Fame Through Depth Not Noise" | domains: [career, spirit]
  SIG.MSR.458: "Saham Vidya in Pisces 12H — Knowledge Dissolving Into Moksha House" | domains: [spirit, travel]
  SIG.MSR.459: "Saham Mitra in Cancer 4H — Alliance Through Roots" | domains: [relationships, parents]
  SIG.MSR.460: "Saham Samartha + Kali Coincident Cancer 4H — Enterprise vs Misfortune Same Soil" | domains: [wealth, parents]
  SIG.MSR.461: "Saham Pitru + Rajya Conjunct Capricorn 10H — Father-Kingdom Same Seat" | domains: [career, parents]
  SIG.MSR.462: "Saham Karma in Aquarius 11H — Profession as Network Gain" | domains: [career]
  SIG.MSR.463: "Saham Artha in Virgo 6H — Wealth Through Disciplined Service" | domains: [wealth, health]
  SIG.MSR.464: "Saham Paradara + Sastra Pisces 12H — Boundary Dissolution vs Learning Stack" | domains: [relationships, spirit]
  SIG.MSR.465: "Saham Bandhu Aquarius 11H — Relative Gains Layer" | domains: [relationships]
  SIG.MSR.466: "Saham Jeeva in Aquarius 11H — Life Force in Gains House" | domains: [health, wealth]
  SIG.MSR.467: "Saham Gaurava Duplicate Yasas — Respect Equals Fame Point" | domains: [career]
  SIG.MSR.468: "Saham Bhratru Gemini 3H — Sibling Lane in Communication House" | domains: [relationships]
  SIG.MSR.469: "Vimshottari Bridge 2027 — Mercury MD Termination to Ketu MD Onset Window" | domains: [career, spirit]
  SIG.MSR.470: "Ketu MD 2031–2038 Primary Moksha-Authority Window (Reframed Post v8.0)" | domains: [spirit, health]
  SIG.MSR.471: "Venus MD 2038–2058 NBRY Reservoir Priming" | domains: [relationships, wealth]
  SIG.MSR.472: "Mercury MD Saturn AD 2024–2027 Triple-Engine Career Pressure Cooker" | domains: [career]
  SIG.MSR.473: "Ketu AD Preview Inside Late Mercury MD — Early 8H Dip" | domains: [spirit]
  SIG.MSR.474: "Chara Dasha Scorpio MD — Martial Container for Mercury Operations" | domains: [career, mind]
  SIG.MSR.475: "Yogini Dasha Bhramari / Dhanya Handoff 2021–2022 Anxiety-Economy Bridge" | domains: [mind, health]
  SIG.MSR.476: "Sade Sati Cycle 3 Peak 2049–2052 Early Warning Hook" | domains: [health, spirit]
  SIG.MSR.477: "Saturn Transit Pisces 2025–2028 Triple Wave on Natal Moon Sign" | domains: [mind, career]
  SIG.MSR.478: "Jupiter Return Sagittarius 2019 Cycle — Dharmic Reload Before Mercury Peak" | domains: [spirit, career]
  SIG.MSR.479: "Rahu Transit Aries 2025–2026 Ignition of Lagna Desires" | domains: [career, relationships]
  SIG.MSR.480: "2041 Saturn Return Exactitude to Natal Exalted Saturn Degree — Apex Transit" | domains: [career]
  SIG.MSR.481: "D9 AK Moon Gemini — Intellectualized Soul Lens" | domains: [mind, career]
  SIG.MSR.482: "D9 Jupiter Gemini — Dharma Teacher as Information System" | domains: [spirit, career]
  SIG.MSR.483: "D9 Venus Virgo Debilitation — Relational Effort Structural Mark" | domains: [relationships]
  SIG.MSR.484: "D9 Saturn Aries Debilitation — Authority Training Arc in Navamsa" | domains: [relationships, career]
  SIG.MSR.485: "D10 Mercury Capricorn — Executive Mercurial Career Archetype" | domains: [career]
  SIG.MSR.486: "D10 Saturn Taurus — Stable Authority Platform in Profession Chart" | domains: [career]
  SIG.MSR.487: "D12 Sun — Father-Line Dwadashamsa Pointer" | domains: [parents]
  SIG.MSR.488: "D7 Moon — Emotional Progeny Matrix for Children Domain" | domains: [children]
  SIG.MSR.489: "D20 Vimsamsa Spiritual Technique Lineage (Sun Placement)" | domains: [spirit]
  SIG.MSR.490: "D27 Nakshatra Strength Chart — PBha Moon Echo" | domains: [spirit, health]
  SIG.MSR.491: "D40 Khavedamsa Luxury Sub-Tone on Venus" | domains: [wealth]
  SIG.MSR.492: "D60 Shashtyamsa Soul Texture — Secondary to D9 for Specialist Reads" | domains: [spirit]
  SIG.MSR.493: "Maandi Upagraha in Gemini 3H — Shadow Commerce Adjunct to UL Cluster" | domains: [wealth, career]
  SIG.MSR.494: "Gulika Upagraha in Gemini 3H — Delay Kernel Inside Gemini Nexus" | domains: [career, mind]
  SIG.MSR.495: "Five-Layer 7H + Four-Layer 3H Cross-Weave — Relational Wealth Meets Communication Wealth" | domains: [wealth, relationships, career]
  SIG.MSR.496: "Retrodictive Eclipse ±6mo Density Near Career Pivots — Empirical Stack" | domains: [parents, career, children]
```

---

## Section C — Per-L3-Report Citation Index (anchor points)

These are the MSR signals and UCN sections already explicitly cited in each L3 report.
Use these as the highest-confidence anchor edges. Also propose edges for signals that
appear in the L3 narrative without explicit ID citation.

```yaml
citation_anchors:
  REPORT_CAREER_DHARMA_v1_1.md:
    msr_cited: [SIG.MSR.131, SIG.MSR.228, SIG.MSR.354, SIG.MSR.391, SIG.MSR.396, SIG.MSR.397, SIG.MSR.404, SIG.MSR.413]
    ucn_cited: [UCN.SEC.I.1, UCN.SEC.II.2, UCN.SEC.IV.3, UCN.SEC.IV.4, UCN.SEC.IV.5, UCN.SEC.IX.2, UCN.SEC.VI.2, UCN.SEC.VII.3, UCN.SEC.VII.4, UCN.SEC.VIII.2, UCN.SEC.VIII.4, UCN.SEC.X.2]
  REPORT_CHILDREN_v1_1.md:
    msr_cited: [SIG.MSR.333, SIG.MSR.341, SIG.MSR.343, SIG.MSR.394, SIG.MSR.397, SIG.MSR.398, SIG.MSR.404, SIG.MSR.406, SIG.MSR.413]
    ucn_cited: []
  REPORT_FINANCIAL_v2_1.md:
    msr_cited: [SIG.MSR.024, SIG.MSR.391, SIG.MSR.404, SIG.MSR.407, SIG.MSR.435, SIG.MSR.436, SIG.MSR.438]
    ucn_cited: [UCN.SEC.IV.4]
  REPORT_HEALTH_LONGEVITY_v1_1.md:
    msr_cited: [SIG.MSR.391]
    ucn_cited: []
  REPORT_PARENTS_v1_1.md:
    msr_cited: [SIG.MSR.225, SIG.MSR.320, SIG.MSR.330, SIG.MSR.342, SIG.MSR.374, SIG.MSR.391, SIG.MSR.394, SIG.MSR.397, SIG.MSR.407]
    ucn_cited: [UCN.SEC.III.4, UCN.SEC.IV.1, UCN.SEC.IV.2, UCN.SEC.V.7, UCN.SEC.VI.3]
  REPORT_PSYCHOLOGY_MIND_v1_1.md:
    msr_cited: [SIG.MSR.190, SIG.MSR.253, SIG.MSR.348, SIG.MSR.354, SIG.MSR.369, SIG.MSR.374, SIG.MSR.388, SIG.MSR.396, SIG.MSR.406, SIG.MSR.413]
    ucn_cited: [UCN.SEC.V.5]
  REPORT_RELATIONSHIPS_v1_1.md:
    msr_cited: [SIG.MSR.343, SIG.MSR.391, SIG.MSR.396, SIG.MSR.404, SIG.MSR.443]
    ucn_cited: []
  REPORT_SPIRITUAL_v1_1.md:
    msr_cited: [SIG.MSR.374, SIG.MSR.397, SIG.MSR.402, SIG.MSR.406, SIG.MSR.407, SIG.MSR.408, SIG.MSR.433, SIG.MSR.437]
    ucn_cited: []
  REPORT_TRAVEL_v1_1.md:
    msr_cited: [SIG.MSR.335, SIG.MSR.381, SIG.MSR.392, SIG.MSR.397, SIG.MSR.399, SIG.MSR.407, SIG.MSR.413]
    ucn_cited: [UCN.SEC.IV.4, UCN.SEC.IV.5, UCN.SEC.VI.1, UCN.SEC.VI.3]
```

---

## Section D — Per-Batch Context (REPLACE for each batch run)

**Batch number:** [BATCH_NUMBER]
**Report being processed:** [BATCH_REPORT_NAME]

The full text of [BATCH_REPORT_NAME] follows. Read it carefully. Propose SUPPORTS edges
for every MSR signal the report uses — both those cited by ID (from Section C anchors)
and those referenced by signal name, concept, or yoga name without an explicit SIG.MSR.NNN.

[PASTE THE FULL CONTENT OF THE TARGET L3 REPORT HERE]

---

## Output Schema (STRICT YAML — no prose, no markdown, no commentary outside this block)

Your entire response must be a single YAML block:

```yaml
proposed_supports_edges:
  - source_signal_id: "SIG.MSR.<NNN>"
    target_ucn_section_id: "UCN.SEC.<part>.<section>"
    target_ucn_heading: "<verbatim section heading from Section A above>"
    l3_evidence_report: "<filename from Section D — e.g. REPORT_CAREER_DHARMA_v1_1.md>"
    l3_evidence_section: "<section heading or §-reference within the L3 report>"
    l1_basis: "<FORENSIC_v8_0 §-citation if signal grounds in L1 directly; else 'derivative — l3_evidence_report carries the chain'>"
    confidence_prior: "LOW|MED|HIGH"
    notes: "<optional; use [EXTERNAL_COMPUTATION_REQUIRED] if signal needs verification>"
```

Produce one entry per SUPPORTS edge proposal. Aim for HIGH recall. The typical range per
L3 report is 15–60 edges. Do not artificially cap; propose every edge you can support.

---

## Constraints

1. `source_signal_id` MUST be an exact SIG.MSR.NNN from Section B — no fabrication.
2. `target_ucn_section_id` MUST be an exact UCN.SEC.X.Y from Section A — no fabrication.
3. `l3_evidence_report` MUST be the filename of the L3 report in Section D.
4. `confidence_prior` must be LOW, MED, or HIGH — no other values.
5. Do not propose CONTRADICTS edges. This prompt is for SUPPORTS only.
6. Do not propose edges between two MSR signals or between two UCN sections.
   Source is always an MSR signal; target is always a UCN section.
7. If a signal is implicitly present in the L3 narrative (referenced by yoga name, planet
   function, or domain concept without explicit SIG.MSR.NNN), include it as LOW or MED
   confidence with the implicit reference in the `l3_evidence_section` field.
8. YAML block is your complete response. No introductory text, no trailing commentary.

---

## Footer

- Prompt: `gemini.cgm_supports_edges` v1.0
- Registered in: `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`
- Reconciler: `platform/python-sidecar/rag/reconcilers/cgm_supports_reconciler.py`
- Session: Madhav_M2A_Exec_7 (B.4 Task 3 SUPPORTS sub-task)
- Next step after all 9 batches: run `cgm_supports_reconciler.py` against raw response files
