---
artifact: STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
status: DRAFT
version: 1.0
authored_by: Claude (Cowork session) — synthesis of native-led design discussion 2026-05-27
authored_on: 2026-05-27
audience: native (Abhisek Mohanty); implementation executor (Claude Code in Antigravity IDE)
disposition: >
  Data-engineering build specification for the T1 (model-neutral) structural fact layer.
  Defines the deterministic derivations of L1 to pre-compute and persist as chart_facts
  rows so that panelist models reason FROM structural facts rather than deriving them
  (error-prone) under query pressure. PENDING NATIVE APPROVAL of the parent decision.
parent_brief: 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md
sibling_artifact: 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md
relates_to:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md (L1 source)
  - platform/scripts/data/ (chart_facts seed scripts — implementation home)
  - chart_facts DB table (target)
implementation_note: >
  All compute belongs in deterministic Python (Swiss Ephemeris + classical rule tables),
  NOT in an LLM. The LLM must never compute shadbala/aspects/etc. at query time — it
  reads the pre-computed row. This is a B.10 (no fabricated computation) safeguard.
approval_gate: inherits parent_brief approval gate
---

# Structural Fact Layer — T1 Build Specification

## §0 — Principle

> **Any deterministic function of L1 data is itself L1 data.**

Human acharyas hold a large body of *derived* structural facts in implicit working memory:
which planet aspects which, what the dispositor chain is, how strong each planet is across
vargas. These are not interpretations — they are computable from positions via classical
rules. The LLM currently re-derives them mid-query, which is (a) wasteful and (b) the
single largest source of arithmetic error and hallucinated configurations. This layer
**pre-computes the acharya's augmented working memory** and serves it as fact. It adds
**columns, not conclusions** — no meaning-making, no narrative, no model fingerprint.

The line, restated: **"is this configuration present / what is this number?" = T1.
"what does it mean for this native?" = the model's interpretive job.**

---

## §1 — The seven structural categories

Each category below is: deterministic, classically grounded, numerically precise where
possible, interpretation-free, and falsifiable against a classical threshold or
computation. Each produces `chart_facts` rows (schema in §3).

### §1.1 — Aspect matrix `[highest value]`
Complete graha drishti (planetary aspects) **and** rashi drishti (sign aspects) — kept
separate, as they are routinely conflated.
- Graha drishti: every planet's 7th (all), plus special aspects — Mars 4/7/8, Jupiter
  5/7/9, Saturn 3/7/10, (Rahu/Ketu per chosen convention — declare it).
- For each aspect: source planet, target house, target planet(s) if any, **exact arc orb**,
  aspect type, and (optional) drishti strength fraction (virupa/60 per classical aspect
  strength tables).
- Rashi drishti: the Jaimini sign-aspect set (movable↔fixed-except-adjacent, etc.).
- **Why it matters:** the model cannot reliably compute "Mars in 7H casts its 4th on 10H,
  7th on 1H, 8th on 2H" mid-query. Pre-computed, it reads three facts instead of risking
  three arithmetic errors.

### §1.2 — Dispositor chain table
For each of the 9 grahas, the full dispositor chain to termination (self-disposited at own
sign / exaltation, or a detected cycle).
- Row per planet: ordered chain, termination type (`self_dispositor` | `cycle`), chain
  length, and the terminal planet.
- Example (native): Mars→Venus→Saturn→(Saturn own/exalted, terminates).
- **Why it matters:** reveals which planetary sub-network a planet feeds into; the model
  currently rebuilds this from scratch every time.

### §1.3 — Cross-varga strength table
Per planet, dignity across the relevant vargas (at minimum D1, D9, D10, D24, D60; ideally
the full shodasavarga where computed). Plus the boolean flags **vargottama** (same sign
D1↔D9) and **pushkara navamsha/bhaga** membership.
- Consolidated as a **strength vector per planet**, so a single row answers "how robust is
  this planet across levels of reality?"
- **Why it matters:** compact per-planet robustness without the model computing divisional
  positions at query time.

### §1.4 — Yoga register (presence as boolean fact)
All classical yogas whose **presence** is rule-decidable from positions.
- Row per yoga: `yoga_name`, `classical_source` (text + verse), `constituent_planets`,
  `constituent_houses`, `is_present` (bool), `formation` (`full` | `partial` | `cancelled`),
  optional `strength_modifier`, and any `cancellation_reason` (e.g. bhanga conditions).
- **Hard boundary:** this table records *that the configuration exists* and *what the
  classical text calls it*. It records **nothing** about what it portends for the native —
  that is interpretation and stays out.
- **Why it matters:** yoga detection under query pressure is where LLMs hallucinate most
  (inventing yogas, misidentifying constituents). Pre-computed boolean flags eliminate the
  failure mode entirely.

### §1.5 — Nakshatra-lord / KP sub-lord chain
For all 9 grahas **and** all 12 house cusps: nakshatra, nakshatra lord, sub-lord, and
(optionally) sub-sub-lord, plus the nakshatra-lord chain to termination.
- **Why it matters:** the KP predictive coordinate. Partially present today in lagna data
  only; this generalises it to all planets and cusps deterministically.

### §1.6 — Proximity / criticality metrics (continuous)
Pure degree-distance facts that give the model *gradation* rather than binary strong/weak:
- distance to exact exaltation point; distance to exact debilitation point;
- distance to nakshatra sandhi (junction); distance to gandanta (Pisces/Aries,
  Cancer/Leo, Scorpio/Sagittarius water-fire junctions);
- distance into/out of moolatrikona arc; combustion distance from Sun (with classical
  per-planet combustion orbs).
- **Why it matters:** "Mars is 2°11′ from gandanta" is a precise fact; "Mars is weak" is a
  lossy categorisation the model would otherwise infer.

### §1.7 — Bhava strength aggregates (Ashtakavarga)
Per-house **sarvashtakavarga** bindus (0–48) and per-planet **bhinnashtakavarga** bindus
(0–8) per house. Cardinal house-strength measures, more precise than the ordinal
kendra/trikona/dusthana classification.
- **Why it matters:** gives a number per house, and (with §2) a transit-quality surface
  over time.

---

## §2 — The classical mathematical spine (the depth layer)

These are quantitative systems **already in the tradition**, designed to give
interpretation a computed foundation. They are the highest-leverage additions because they
convert the model's qualitative impressions into calibrated inputs.

### §2.1 — Shadbala (six-fold strength) `[single highest-value addition]`
Per planet, all six components **with their sub-scores**, plus total rupas and the
classical sufficiency verdict against the per-planet minimum threshold:
- Sthana bala (positional — degree-sensitive, continuous), Dig bala (directional),
  Kala bala (temporal — incl. nathonnata, paksha, tribhaga, varsha/masa/dina/hora,
  ayana, yuddha), Chesta bala (motional — speed vs. mean motion), Naisargika bala
  (fixed natural hierarchy), Drik bala (net aspectual).
- **Why it matters (model's own words):** asking the model "can Mars deliver its 7H
  significations in its dasha?" from dignity alone is like estimating blood pressure by
  looking at the patient. The number exists and is computable. Anchored to a shadbala
  score, every downstream dasha/transit/timing judgment sharpens. **This is the single
  addition that improves output quality most.**

### §2.2 — Ashtakavarga (eight-source voting)
The 8×12 contribution matrix per planet, the bhinnashtakavarga totals, and
sarvashtakavarga per sign/house (feeds §1.7). Plus, optionally, the **transit-quality
surface**: a transiting planet over a high-natal-bindu sign is classically stronger — a
testable, falsifiable claim and a natural input to the prediction-calibration loop.

### §2.3 — Vimshopaka bala (cross-varga weighted strength)
Weighted-average dignity across the 16 vargas (per-varga classical weights, max 20
vimshopakas). One robustness scalar per planet across the varga spectrum.

### §2.4 — KP precision coordinates
Sub-lord (and sub-sub-lord) of each house cusp — the ~1–2° resolution coordinate KP was
designed to provide, versus the ~13° nakshatra resolution. Feeds §1.5.

### §2.5 — Tajaka aspect predicates (for varshphal queries)
Boolean geometric predicates — Itthasala (applying, perfecting before sign-exit),
Ishrafa (separating), with orb and deeptamsha conditions. Pure orbital-mechanics
predicates, no interpretation.

---

## §3 — Storage model

All of the above land as rows in **`chart_facts`** (the existing key-value natal store),
NOT in any synthesis document. Reuse the established schema:

```
fact_id        e.g.  ASPECT.MARS.10H.GRAHA_4TH
                     SHADBALA.MARS.TOTAL_RUPAS
                     ASHTAKAVARGA.SAV.7H
                     YOGA.SASHA.PRESENT
                     DISPOSITOR.MARS.CHAIN
                     PROXIMITY.MARS.GANDANTA_DEG
category       aspect | shadbala | ashtakavarga | yoga | dispositor |
               nakshatra_chain | proximity | vimshopaka | kp_sublord | tajaka
divisional_chart  D1 | D9 | ... (where applicable; null for cross-varga aggregates)
value_text     short label / verdict
value_number   the continuous score where one exists
value_json     compound payloads (component breakdowns, chains, matrices)
provenance     JSONB: { engine, classical_rule_source, build_id, computed_on,
                        tier: "T1", deterministic: true }
```

**Critical provenance rule:** every row carries `tier: "T1"` and `deterministic: true`.
This is what lets the panelist context-builder (sibling tool spec) include them with
confidence and exclude T2.

---

## §4 — Implementation guidance (for the executor brief)

1. **Compute in Python, never in the LLM** (B.10). Swiss Ephemeris for positions; classical
   rule tables (encoded as data, not prose) for aspects/yogas/strength. Unit-test every
   formula against a known worked example from the source text.
2. **FORENSIC-ground every build.** Spot-check computed values against the native's chart
   at 1984-02-05 — e.g. confirm Saturn's exaltation registers in Sthana bala, confirm the
   Sasha yoga flags present, confirm Mars's enemy-sign dignity (the recently-corrected
   `chart_facts` value — do not re-introduce the drift).
3. **build_id + manifest registration.** Register each build in `build_manifests`
   (note the known auto-registration gap flagged across Phase 4C / DAR — do it explicitly).
4. **Generalise beyond the native.** Every formula must take a chart as input, not hardcode
   Abhisek's positions — this layer is the substrate for the §A research-tool extension.
5. **Idempotency guard checks the write target** (per the durable lesson) — verify
   `chart_facts`, not a sibling table, before re-seed.

---

## §5 — What this layer explicitly is NOT
- Not MSR. MSR *selects and scores* signals (model judgment). This layer computes *all*
  deterministic structural facts without selection or scoring-as-opinion. Where a number
  exists classically (shadbala rupas, SAV bindus), it is a computed value, not a
  calibrated belief.
- Not interpretation. No "this means", no domain-significance, no narrative.
- Not a replacement for FORENSIC — an extension of it. FORENSIC remains the human-readable
  L1 source of truth; this is its structured, derived expansion.

---

## §6 — Provenance of this brief
Model-authored (Claude, Cowork). DRAFT. Inherits the parent brief's approval gate —
no implementation executor brief is dispatched until the native approves the parent
decision.
