---
artifact: MEDICAL_AYURVEDIC_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: MEDICAL_AYURVEDIC_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — maximal scope, computed-and-cited + strong epistemic disclaimer
authored_for: the Medical/Ayurvedic Jyotish subsystem build (subsystem #5 of 7, Wave 3)
purpose: >
  Build the Medical/Ayurvedic subsystem to full classical depth: the complete deterministic mapping web from
  chart to body (graha→dosha/dhatu/body-system, sign/nakshatra/drekkana/D6→body-part, house→health, the
  Arishta/disease yogas, the dosha-balance computation). Maximal, computed-and-cited, and CLEARLY TIERED as
  classical-Jyotish health INDICATIONS — never medical diagnosis. Reuses Dignity + Nakshatra + Yoga.
read_in_combination_with:
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§0.5; §2 medical depth bar) + the depth template (Yoga plan)
  - DIGNITY (planetary condition → body-system strength), NAKSHATRA (body-part map), YOGA (disease yogas)
  - existing: A13 RM (graha-constitution remedies), D6 Shashtiamsa varga (the health varga in ga_vargas)
hard_gate: a medical-mapping datum stored only if deterministically COMPUTED + CITABLE; all output is INDICATION not diagnosis; never store a prose medical claim.
epistemic_tier: health INDICATIONS (documented-classical tier) + a strong NOT-MEDICAL-ADVICE disclaimer surfaced at serve-time (project user-wellbeing + ethical framework).
---

# Medical / Ayurvedic Jyotish Subsystem — Master Plan (maximal) v1.0

## §0 — Reframe + the epistemic firewall

Today: minimal (graha-constitution pairings in RM). Maximal: the COMPLETE deterministic chart→body mapping
web. BUT — this subsystem touches health, so the firewall is non-negotiable: **every output is a classical-
Jyotish INDICATION, never a medical diagnosis or advice.** It is tiered as documented-classical (not the
hard-fact tier), carries a strong not-medical-advice disclaimer at serve-time, and stores only the
deterministic classical mappings — never a medical claim. With that firewall, build it maximally.

## §1 — Three-data-category split
- **STATIC → L0 (`bg_medical_mappings`):** the complete classical mapping tables (graha→dosha/dhatu/organ,
  sign→body-part, nakshatra→body-part [reuse nakshatra subsystem], drekkana→body-part, house→health-domain,
  tatva→bodily-element). Chart-agnostic, cited.
- **CHART-SPECIFIC → L1 (`ga_medical`):** this chart's dosha-balance, afflicted-body-parts, disease-yoga
  firings, body-system strengths (reuses ga_condition). PyJHora.
- No service category (natal-structural; timing of health windows joins dasha/transit).

## §2 — L0 `bg_medical_mappings` (maximal static mapping web, cited)
- **graha → dosha** (Vata/Pitta/Kapha per planet — Sun/Mars=Pitta, Moon/Venus=Kapha-Vata, etc.).
- **graha → dhatu** (the 7 tissues: rasa/rakta/mamsa/meda/asthi/majja/shukra).
- **graha → body-system / organ** (each planet's organs — Sun=heart/eyes/bones, Moon=mind/fluids/chest, …).
- **sign → body-part** (Kalapurusha: Aries=head … Pisces=feet) + **the degree-within-sign body refinement**.
- **nakshatra → body-part** (the 27-fold body map — REUSES the nakshatra subsystem's body_part attribute).
- **drekkana → body-part** (the classical Drekkana medical reading — the 36 drekkanas to body regions —
  a deep classical method most systems omit).
- **D6 Shashtiamsa → disease/health** (D6 is the health varga — its amsa meanings) + **D8/D22 where the
  tradition uses them for longevity/chronic**.
- **house → health-domain** (6th=disease/acute, 8th=chronic/surgery/longevity, 12th=hospitalization/loss,
  Lagna=vitality/constitution) + the maraka/badhaka health rules.
- **tatva-balance → constitutional element**.
All cited (classical medical-Jyotish texts + BPHS health chapters + the relevant Ayurvedic-Jyotish corpus →
into bg_texts).

## §3 — L1 `ga_medical` (per-chart, computed)
Per chart per ayanamsha:
- **Dosha balance (Vata/Pitta/Kapha)** — computed from graha placements/strengths × the graha→dosha map
  (reuses ga_condition for planetary strength → which dosha dominates), a deterministic constitutional
  signature.
- **Afflicted body-parts** — malefics on/aspecting the 6th/8th + their sign/nakshatra/drekkana body-parts
  (the deterministic "which body regions carry affliction signals").
- **Disease/Arishta YOGA firings** — REUSES the Yoga subsystem (the Arishta family, Balarishta, the chronic-
  disease yogas) computed for this chart.
- **Body-system strengths** — each organ/system's strength from its karaka-graha's condition (reuses
  ga_condition).
- **Longevity/health-window markers** — the maraka/badhaka periods (joins ga_dashas), 6th/8th-lord dasha
  windows (deterministic "vulnerable periods" — INDICATION, not prediction).
- Two-pass; cited; all flagged INDICATION-tier.

## §4 — L2 exploitation (extend bo_sangati health domain — flag for sign-off)
The health-domain cell in CDLM (bo_sangati) gets the medical signals; convergence of disease-yoga +
afflicted-body-part + vulnerable-dasha-window on a body-system = a weighted health-INDICATION signal. Clearly
tiered + disclaimered.

## §5 — L3/L4/L5
L3: health-vulnerability timing (the dasha/transit windows). L4: Ayurvedic/health remedies (already partly in
bo_upaya — the graha-constitution + the gem/herb/mantra remedies, tiered). L5: did the health indications
correlate with logged health events (the one place this could become genuinely研究-valuable — held-out).

## §6 — Standards + the firewall
Computed-and-cited; **INDICATION-tier + strong not-medical-advice disclaimer (non-negotiable — the project's
user-wellbeing discipline)**; never store a medical claim or prose; L0 ON-CONFLICT / L1 delete-then-insert;
orchestrator-native; two-pass; FORENSIC where applicable; floors-aspirational; reuse (don't recompute)
Dignity/Nakshatra/Yoga; surgical migrations. bg_medical_mappings = authority; ga_medical references.

## §7 — Decisions upfront
1. Disclaimer wording + where surfaced (every health output; lock it). 2. Which medical-Jyotish texts to
source into bg_texts (the classical health corpus — confirm editions). 3. Dosha-balance formula
(dosha_balance_formula_v1 — exact weighting). 4. Which vargas count as health (D6 + D8/D22?). 5. How strongly
to tier (documented-classical, clearly NOT hard-fact, clearly NOT diagnosis).

---

*End. Medical/Ayurvedic maximal: the complete deterministic chart→body mapping web (graha→dosha/dhatu/organ,
sign/nakshatra/drekkana/D6→body-part, house→health, disease-yogas, dosha-balance) — computed-and-cited,
heavy reuse of Dignity/Nakshatra/Yoga, firewalled as health INDICATIONS with a strong disclaimer.*
