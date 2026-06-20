---
artifact: L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md
canonical_id: L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS
version: 1.0
status: RATIFIED 2026-06-21 (native sign-off — convergence FORM §3.1 + all weight values §3.2–§3.8 approved as v1.0 starting parameters; frozen + read-only for the swarm; L5 calibration may re-tune later)
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
ratifies: [I-7 (influence-weight model), I-15 (the class→template table), I-16 (the convergence-scoring function)]
consumed_by: [ka_yojaka (the templates), ka_sangam (I-16 + I-7), ka_vighnakara (I-7 danger), ka_tulana (I-11), ka_kala_darshana]
purpose: >
  The PRE-APPROVED domain-judgment inputs for the L3 Kāla autonomous build. Per the closeout D7 decision,
  Cowork pre-authors the activation templates (I-15) + the influence-weight sets (I-7/I-16) so the swarm's
  NATIVE-RATIFY gates are satisfied BEFORE launch and the run never halts mid-build. EVERY template encodes
  a CLASSICAL activation principle with a cited source; EVERY weight carries its rationale. Nothing here is
  invented — it is classical Jyotish made deterministic. NATIVE SIGN-OFF converts status → RATIFIED.
ratification_protocol: >
  The native reviews §2 (templates) + §3 (weights). Per the canonical-or-floor rule
  ([[feedback-canonical-or-floor-rule]]): weights are JUDGMENTS — the native may adjust any value; on
  adjustment Cowork NORMALIZES (never silently re-picks). On sign-off, status flips to RATIFIED and these
  become frozen, versioned formula parameters the swarm treats as read-only.
---

# L3 Kāla — Activation Templates & Influence Weights v1.0 (PRE-APPROVED INPUTS)

## §0 — What this is and why it exists
The L3 layer's machine is deterministic, BUT three things rest on *judgment* the corpus requires the native
to ratify: (1) **the activation templates** — how each kind of L2 signal "fires" in time (I-15); (2) **the
influence weights** — how much each factor (daśā/transit/dignity/panchāṅga) counts (I-7); (3) **the
convergence-scoring function** — how the factors combine into one score (I-16). Left as in-run HALT gates,
the autonomous swarm would stall waiting for the native. This document PRE-AUTHORS all three with full
classical grounding, so the native ratifies ONCE, here, and the swarm runs uninterrupted.

**Discipline:** every template carries a `CLASSICAL BASIS` (the principle + a source class) and a
`DERIVATION_LEDGER` pointer (the `bg_transit_rules` rule_id(s) the executor binds at build time). Every
weight carries a `RATIONALE`. Weights are normalized to sum to 1.0 within each group. The native may change
any number; Cowork re-normalizes.

---

## §1 — The signature_class taxonomy (recap; the classifier assigns ONE per signal)
Per plan §5.12.3, `ka_yojaka` classifies each L2 signal into ONE archetype from its existing L2 fields:
YOGA · DOSHA · DIGNITY · DISPOSITOR/RELATIONAL · SENSITIVE-POINT · CONJUNCTION/ASPECT · SUBSYSTEM.
Each archetype maps to ONE template (§2). The template is BOUND per signal from its `constituent_facts_array`.

---

## §2 — THE ACTIVATION TEMPLATES (I-15) — one per signature_class

> **Template structure (every entry):** `CLASSICAL BASIS` (the principle + source class) · `DAŚĀ-ELIGIBILITY
> RULE` (the Mode-A prior) · `TRANSIT-TRIGGER RULE` (the Stage-2/Mode-B condition, from the §5.9.2 vocabulary)
> · `STRENGTH/AFFLICTION HOOK` (what scales/vetoes it) · `BOUND-FROM` (which signal fields instantiate it).
> The executor (`ka_yojaka`) binds the parameters from the signal's constituents + cites the matching
> `bg_transit_rules` rule_id in the DERIVATION_LEDGER.

### T1 — YOGA template (benefic yoga: Lakshmi / Raja / Dhana / Gajakesari / …)
- **CLASSICAL BASIS:** A yoga is a *promise* that fructifies in the daśā/antardaśā of its constituent lords,
  when transit corroborates and the lords are unafflicted. (Phaladīpikā / Bṛhat Parāśara Horā Śāstra — daśā
  fructification of yogas; gochara corroboration.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD or AD (or PD, for finer windows) lord ∈ {the yoga's constituent
  lords ∪ their dispositors ∪ the lord of the bhāva the yoga occupies}. Eligibility STRENGTH = exact
  constituent-lord match > dispositor > house-lord.
- **TRANSIT-TRIGGER:** fires when (a) a constituent lord, OR (b) a natural benefic (Jupiter/Venus/Mercury),
  transits a kendra (1/4/7/10) or trikoṇa (1/5/9) FROM the yoga's bhāva, OR aspects the yoga's lord; orb per
  the orb-strength curve (§3.4). Higher magnitude: Jupiter transit, or a constituent-lord RETURN.
- **STRENGTH/AFFLICTION HOOK:** scaled by the constituent lords' dignity/Shadbala (§3.2); VETOED/dampened if
  a constituent lord is combust, in a maraka/dusthāna transit, or afflicted by a malefic transit at the same
  time (the affliction feeds `ka_vighnakara`).
- **BOUND-FROM:** `yoga_label`, the constituent grahas + bhāvas in `constituent_facts_array`,
  `graha_yoga_karaka_flag`.

### T2 — DOSHA template (Kāla Sarpa / Kemadruma / Śakaṭa / Grahaṇa / Viṣa-yoga / …)
- **CLASSICAL BASIS:** An affliction "fires" as a DANGER window in the daśā of the afflicting graha, when
  transit re-triggers the affliction. (BPHS doṣa periods; Sade-Sati / aṣṭama-Śani gochara doctrine.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD/AD lord ∈ {the afflicting grahas (Rahu/Ketu/Saturn/Mars per the
  doṣa) ∪ the lord of the afflicted bhāva}.
- **TRANSIT-TRIGGER:** fires as DANGER when an afflicting malefic (Saturn/Mars/Rahu/Ketu) transits OVER the
  afflicted point/lord, or a station/eclipse lands on it. → emitted by `ka_vighnakara`, NOT the opportune pipeline.
- **STRENGTH/AFFLICTION HOOK:** severity scaled by the malefic's strength + the count of simultaneous
  afflictions (double-affliction → higher severity). Mitigated if a strong benefic simultaneously aspects.
- **BOUND-FROM:** `dosha_label`/`dosha_fires`, `kala_sarpa_per_varga`, the afflicting grahas + afflicted bhāva.

### T3 — DIGNITY template (exaltation / debilitation / own-sign / Nīcabhaṅga state of a graha)
- **CLASSICAL BASIS:** A graha delivers per its dignity in its own daśā and when transit activates it;
  an exalted graha gives strongly, a debilitated one weakly (unless Nīcabhaṅga). (BPHS dignity doctrine;
  Saptavargaja-bala.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD/AD lord = the graha itself (or its dispositor).
- **TRANSIT-TRIGGER:** fires when the graha is strongly transited — a benefic aspect to it, its return, or
  its ingress into a dignity-favorable sign.
- **STRENGTH/AFFLICTION HOOK:** force scaled DIRECTLY by the graha's natal dignity/Shadbala (this is the
  archetype where strength-coupling is most central, §3.2); Nīcabhaṅga raises a debilitated graha's force.
- **BOUND-FROM:** the graha's dignity state from `ga_strength` / `graha_effective_dignity_modified_by_aspects`.

### T4 — DISPOSITOR / RELATIONAL template (Parivartana / dispositor-chain / mutual aspect)
- **CLASSICAL BASIS:** A relational yoga (e.g. Parivartana — mutual sign exchange) fires when EITHER
  exchanging lord is daśā-active and transit links them. (BPHS parivartana; sambandha doctrine.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD/AD lord ∈ {either of the two related lords}.
- **TRANSIT-TRIGGER:** fires when one related lord transits to aspect/conjoin the other, or transits the
  bhāva the other rules (the exchange "completes" in time).
- **STRENGTH/AFFLICTION HOOK:** scaled by `composite_dispositor_strength`; dampened if either lord is afflicted.
- **BOUND-FROM:** `parivartana_per_varga`, `graha_dispositor_chain`, the two related grahas + bhāvas.

### T5 — SENSITIVE-POINT template (Arūḍha / Karakāmśa / Swāmśa / KP cuspal / upagraha)
- **CLASSICAL BASIS:** A sensitive point activates when a graha transits OVER it (gochara to a special
  point). (Jaimini ārūḍha/kāraka doctrine; KP cuspal-significator transit doctrine.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD/AD lord ∈ {the lord/significator of the sensitive point}.
- **TRANSIT-TRIGGER:** fires when a relevant graha transits OVER the point (conjunction within orb), or
  stations on it (high magnitude).
- **STRENGTH/AFFLICTION HOOK:** scaled by the transiting graha's nature (benefic → opportune; malefic →
  caution); the point's own strength modulates.
- **BOUND-FROM:** `arudha_pada` / `karakamsa_position` / `swamsa_position` / `kp_cuspal_significators`.

### T6 — CONJUNCTION / ASPECT template (a natal conjunction or Parāśarī/Tājika aspect re-triggered)
- **CLASSICAL BASIS:** A natal yoga formed by conjunction/aspect re-activates when transit re-forms the same
  angular relationship (gochara re-trigger of a natal sambandha). (BPHS dṛṣṭi; Tājika ithasala for time-bound aspects.)
- **DAŚĀ-ELIGIBILITY:** eligible when MD/AD lord ∈ {the conjoining/aspecting grahas}.
- **TRANSIT-TRIGGER:** fires when transit re-forms the natal aspect angle (the same degrees: 0/60/90/120/180)
  to the natal point, OR a transiting graha re-conjoins the natal pair.
- **STRENGTH/AFFLICTION HOOK:** scaled by the orb-strength of the re-formed aspect + applying/separating
  (§3.4); applying > separating.
- **BOUND-FROM:** `conjunction_within_orb`, `aspect_parashari_given`, `aspect_jaimini_per_varga`.

### T7 — SUBSYSTEM template (Sade-Sati / Medical / Vāstu / Nakshatra-subsystem-specific)
- **CLASSICAL BASIS:** Each embedded subsystem has its OWN classical activation rule; the template DELEGATES
  to the subsystem's rule rather than a generic one. (Subsystem-specific śāstra: Sade-Sati dhaiyā doctrine;
  medical Jyotiṣa timing; Astro-Vāstu directional timing.)
- **DAŚĀ-ELIGIBILITY:** per the subsystem (e.g. Sade-Sati is daśā-independent — it is a Saturn-gochara
  phenomenon; medical is the afflicted-bhāva-lord daśā).
- **TRANSIT-TRIGGER:** per the subsystem (Sade-Sati = Saturn transiting 12th/1st/2nd from natal Moon;
  medical = malefic transit to the 6th/8th/āyur points; Vāstu = the directionally-relevant graha's transit).
- **STRENGTH/AFFLICTION HOOK:** per the subsystem's own severity/benefit scale.
- **BOUND-FROM:** `ga_sade_sati` / `sade_sati_phase` / `ga_medical` / `ga_vastu` references.

> **Coverage note:** these 7 templates cover the full signature_class taxonomy. If `ka_yojaka` finds a signal
> that matches none, it is a CLASSIFY-RESIDUAL → logged (not fabricated), per the brief's 100%-coverage AC.

---

## §3 — THE INFLUENCE WEIGHTS (I-7) + THE CONVERGENCE FUNCTION (I-16)

> **All weight groups normalize to 1.0.** Each weight carries a RATIONALE grounded in classical relative
> importance. The native may adjust any value; Cowork re-normalizes the group. These are STARTING judgments,
> explicitly calibratable later by L5 (the prediction-records feed reliability curves that can re-tune them).

### §3.1 — The convergence-scoring FUNCTION (I-16) — the FORM (native-ratify the form first)
Per plan §5.13.A1, the score is NOT a flat weighted sum. It is:
```
convergence_score = ( Π over NECESSARY conditions: necessity_factor_i )   ×   ( saturating_sum over SUPPORTING conditions )
```
- **NECESSARY conditions (multiplicative — a veto):** daśā-eligibility present (≠0), AND the constituent
  lord not fatally afflicted. If a necessary condition is ~0, the whole score is ~0 (you cannot have an
  opportune Lakshmi-yoga window when its lord is combust in a dusthāna, however many minor positives align).
- **SUPPORTING conditions (additive with saturation):** each corroborating current (transit aspect,
  panchāṅga, Tāra Bala, cross-daśā agreement, benefic dṛṣṭi) adds, but with DIMINISHING RETURNS
  (saturating, e.g. `1 - Π(1 - w_i·s_i)`), so ten weak positives never fake one strong necessary one.
- **Result ∈ [0,1]**, matching the existing `kala_convergence.convergence_score` CHECK.
- **RATIONALE:** this mirrors how an acharya reasons — a fatal flaw vetoes; corroboration accumulates but
  saturates. Pure-additive would let weak factors fake strength (false confluence); pure-multiplicative
  would be too brittle. **NATIVE: ratify this FORM.**

### §3.2 — Strength-coupling weights (I-7) — how dignity/Shadbala scales trigger FORCE
A trigger's force is multiplied by a dignity factor of the involved graha:
| Graha dignity state | force multiplier | RATIONALE (classical) |
|---|---|---|
| Exalted / own-sign / Mūlatrikoṇa | 1.0 | full promise; the graha delivers strongly |
| Friendly sign / dignified by aspect | 0.75 | supported, near-full |
| Neutral | 0.5 | baseline |
| Enemy sign | 0.3 | weakened delivery |
| Debilitated (no Nīcabhaṅga) | 0.15 | minimal force — needs Mode-B magnitude to register |
| Debilitated WITH Nīcabhaṅga | 0.6 | the cancellation restores much of the promise |
| Combust | ×0.4 further | the graha's significations are "burnt" — a strong dampener |
**RATIONALE:** these track the classical Ṣaḍbala/dignity ladder; the native may sharpen any rung.

### §3.3 — The supporting-current weights (I-7) — relative importance in the saturating sum
Within the SUPPORTING group (normalized to 1.0):
| Supporting current | weight | RATIONALE |
|---|---|---|
| Constituent-lord transit (the direct trigger) | 0.30 | the most direct activation — the lord itself moving |
| Benefic dṛṣṭi/transit corroboration (Jupiter/Venus) | 0.20 | classical "Jupiter's glance" corroboration |
| Cross-daśā agreement (multiple systems concur) | 0.18 | independent confirmation (discounted for coupling, §3.6) |
| Panchāṅga quality (tithi/nakshatra/vara/yoga) | 0.12 | the day's intrinsic auspiciousness |
| Tāra Bala (native-specific nakshatra overlay) | 0.12 | makes it auspicious FOR THIS NATIVE |
| Nakshatra/subsystem corroboration | 0.08 | secondary embedded-subsystem support |
**RATIONALE:** the direct lord-trigger dominates; native-specific (Tāra Bala) and independent (cross-daśā)
signals are weighted above generic day-quality. Native may re-rank.

### §3.4 — Orb-strength curve (I-17) — the continuous trigger strength
`orb_strength(orb, applying/separating) ∈ [0,1]`:
- **Form:** a smooth falloff — full (1.0) at exact (0° orb), decaying to 0 at the orb boundary. Proposed:
  `cos²( (orb / max_orb) · π/2 )` (smooth, 1→0, classical-feeling tight-at-exact).
- **max_orb:** 3° default (matches the router's clamp [0,3]); luminaries/Jupiter may take wider (per
  `bg_transit_rules`).
- **Applying vs separating:** an APPLYING aspect (tightening) ×1.0; a SEPARATING aspect ×0.7. **RATIONALE:**
  classical doctrine holds an applying aspect stronger (the event is "building"); Tājika ithasala formalizes this.
- Native may change the curve or the applying/separating ratio.

### §3.5 — The confidence function (I-21) — words → numbers
`confidence = f( independent_current_count, mean_strength, rarity, birthtime_robustness )`. Proposed mapping:
| confidence_score | label | typical condition |
|---|---|---|
| ≥ 0.75 | **high** | ≥3 INDEPENDENT currents agree, strong, robust to birth-time |
| 0.45–0.75 | **moderate** | a strong single trigger, or 2 independent currents |
| < 0.45 | **speculative** | a weak/lone trigger, or birth-time-sensitive |
**RATIONALE:** "independent" is the operative word — see §3.6. Native ratifies the thresholds.

### §3.6 — The independence-discount weights (I-22) — the anti-echo-chamber
Because daśā is DERIVED from the natal Moon's nakshatra (plan I-1), a daśā signal and a nakshatra-overlay
signal are CORRELATED, not independent. The `independent_current_count` discounts coupled evidence:
| Current pair | correlation | counts as |
|---|---|---|
| Daśā ↔ nakshatra-overlay | HIGH (daśā is nakshatra-derived) | ~1 combined, not 2 |
| Transit ↔ daśā | LOW (sky-from-without vs. promise-from-within) | 2 independent |
| Panchāṅga ↔ transit | MODERATE (both sky-based) | ~1.5 |
| Cross-daśā systems (Vimśottarī ↔ Yoginī) | MODERATE (different mathematics, shared natal root) | ~1.5 |
**RATIONALE:** this is the single most important rigor weight — it prevents the apex insight
(cross-subsystem convergence) from being an echo chamber. Native ratifies the correlation tiers.

### §3.7 — Mode-B magnitude threshold (I-8) — what counts as a rare-high-magnitude off-daśā event
A configuration crosses into Mode-B "discovery" when its magnitude (orb-strength × dignity-force × benefic-
weight) ≥ **0.6** AND it fires DESPITE a daśā-eligibility < 0.3 (i.e. genuinely off-daśā). **RATIONALE:** high
enough to be rare (the value), low enough to not miss the strong off-daśā activations the native prioritized.
The always-return-ranked guarantee LOWERS this when the daśā is far. Native may tune the 0.6.

### §3.8 — Cross-pattern prioritization weights (I-11, for ka_tulana)
Ranking across patterns (normalized to 1.0): convergence_score 0.35 · rarity 0.25 · confidence 0.20 ·
consequence (L2 pattern importance) 0.15 · proximity (sooner) 0.05. **RATIONALE:** strength + rarity
dominate ("how good × how rare"); proximity is a light tiebreaker. Native may re-weight.

---

## §4 — RATIFICATION — ✅ COMPLETE (native sign-off 2026-06-21)
- [x] **§3.1 convergence FORM** (multiplicative-necessary × saturating-supporting) — **RATIFIED.**
- [x] **§2 the 7 templates** — **RATIFIED** (classical basis accepted as sound).
- [x] **§3.2–§3.8 the weight sets** — **RATIFIED** as the v1.0 starting set (accepted as proposed).
- **Status flipped to RATIFIED.** These are now FROZEN, versioned, read-only parameters. The autonomous
  swarm's NATIVE-RATIFY gates (I-7/I-15/I-16) are PRE-SATISFIED — the run will NOT halt for them. L5's
  calibration loop may re-tune the weights later via the prediction-records (reliability curves); any such
  change is a versioned re-ratification, never a silent re-pick (canonical-or-floor rule).

> **Note for the swarm:** these are STARTING judgments, deliberately conservative + classically grounded.
> They are NOT claimed to be optimal — L5's calibration loop exists precisely to refine them against lived
> reality. The build's job is to APPLY them deterministically, never to silently re-pick (canonical-or-floor rule).

---
*End of L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS v1.0 (AWAITING RATIFICATION). 7 classical activation
templates (I-15) + the convergence function form (I-16) + 7 weight groups (I-7/I-8/I-11/I-17/I-21/I-22). Once
the native signs off, the autonomous swarm's NATIVE-RATIFY gates are PRE-SATISFIED and the run never halts.*
