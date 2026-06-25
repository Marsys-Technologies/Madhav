---
artifact: DIGNITY_AVASTHA_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: DIGNITY_AVASTHA_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — maximal scope, computed-and-cited hard gate
authored_for: the Dignity/Avastha/Planetary-Condition subsystem build (subsystem #3 of 7, Wave 1)
purpose: >
  Build the planetary-CONDITION subsystem to full classical depth: unify the scattered dignity/avastha/
  motion/combustion data into ONE deterministic "how is each planet doing, and how does it change through
  time," maximally dense for holistic LLM synthesis. The condition SUBSTRATE that Transit + Medical + Yoga-
  strength all consume. Embedded via the pattern; roadmap §0.5 + computed-and-cited hard gate.
read_in_combination_with:
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§0.5; §2 dignity depth bar; §8 strategy)
  - YOGA_SUBSYSTEM_MASTER_PLAN_v1_0.md (the depth template + the consumer of condition-as-yoga-strength-input)
  - existing: A6 (varga dignity), A8 (avasthas, shadbala), A1 (combustion/retro/speed)
hard_gate: A condition datum is stored only if deterministically COMPUTED + CITABLE; interpretive "this weak planet means X" = serve-time.
---

# Dignity / Avastha / Planetary-Condition Subsystem — Master Plan (maximal) v1.0

## §0 — Reframe: scattered → unified condition

Dignity data is scattered today (varga dignity A6, 5 avasthas A8, combustion/retro/speed A1). Maximal: ONE
unified, deterministic PLANETARY CONDITION per graha — every classical state, across every varga, with the
TRAJECTORY of how that condition changes through the dasha timeline (and transit, when W2 lands). The bar: an
acharya says "every computable factor of a planet's condition is captured." This is the substrate the rest
of the program leans on (yoga strength, transit-planet condition, medical body-system strength).

## §1 — Three-data-category split
- **STATIC → L0:** the dignity/avastha reference tables (exaltation/debilitation/moolatrikona/own degrees +
  the deep-exaltation points, the avastha-scheme definitions, combustion orbs per planet, the motion-state
  thresholds, the friendship tables — naisargika/tatkalika/panchadha). Chart-agnostic.
- **CHART-SPECIFIC → L1 (`ga_condition`):** each graha's unified condition composite + per-varga dignity +
  all avasthas + motion/combustion state + the condition TRAJECTORY through dashas. PyJHora.
- **Service consumption:** the condition-at-transit-time uses the W2 transit service (no storage across time).

## §2 — L0 reference (maximal static condition tables)
- **Dignity reference:** exaltation/debilitation sign+exact-degree (deep exaltation/debilitation points),
  moolatrikona ranges, own-sign, the 5-fold relational dignity (great-friend → great-enemy).
- **Friendship tables (ALL three):** Naisargika (natural — static), the COMPUTATION rule for Tatkalika
  (temporal — per chart, L1) and Panchadha (5-fold composite — per chart, L1). Store the static naisargika +
  the rules.
- **Avastha scheme definitions (ALL):** Baladi (5 — infant/youth/adult/old/dead by degree), Jagradadi
  (3 — awake/dreaming/sleeping), Deeptaadi (9 — deepta/swastha/...), Lajjitaadi (6 — ashamed/delighted/...),
  Sayanadi (12 — the 12 postural states). Each scheme's exact degree/condition rule.
- **Motion-state thresholds:** the 8 classical motions (Vakra/Anuvakra/Vikala/Manda/Mandatara/Sama/Chara/
  Atichara) by speed. Combustion orbs per planet. Graha-yuddha (planetary war) proximity rule + win/lose
  criteria.
- All cited to BPHS Ch.45 (avasthas), Ch.27 (relationships), Saravali, etc.

## §3 — L1 `ga_condition` (per-chart unified condition)
Per graha, per ayanamsha:
- **Dignity in EVERY varga** (D1–D60 — not just D1/D9): the planet's dignity in all 16+ divisionals
  (references ga_vargas — L1-internal authority). The dignity SPREAD across vargas (strong-everywhere vs
  patchy) as a deterministic composite.
- **ALL avasthas** computed (Baladi/Jagradadi/Deeptaadi/Lajjitaadi/Sayanadi) per graha.
- **Tatkalika + Panchadha friendship** computed for this chart; **graha-yuddha** results (winner/loser);
  **combustion** state + exact arc-from-Sun; **motion state** (which of the 8).
- **The unified CONDITION COMPOSITE** — `condition_formula_v1`: a single deterministic score per graha =
  f(dignity × avastha × combustion × motion × shadbala × varga-dignity-spread × graha-yuddha). Versioned,
  reproducible. With the component breakdown stored (so "why is this planet's condition X" is auditable).
- **The condition TRAJECTORY** — how each graha's condition changes across the dasha timeline (a planet weak
  natally but in its own dasha-period; joins ga_dashas). The deterministic "when is this planet strong/weak."
- Two-pass; FORENSIC: the native's known dignities reproduce (e.g. Sun in Capricorn — neutral/enemy sign).

## §4 — L2 exploitation (extend bo_laksana / bo_karanajala — flag for sign-off)
- Condition signals (a planet's condition state → a signal).
- **Condition as graph NODE-WEIGHT** (bo_karanajala/bo_bimba): a strong-condition planet's signals carry more
  salience; centrality weighted by condition. (Directly serves the graph-depth philosophy.)
- Condition contradiction: a planet strong in some vargas, weak in others = a first-class contradiction-pair.

## §5 — L3/L4/L5 (substrate now)
L3: the condition trajectory IS a timing layer (when each planet peaks). L4: weakest-condition planets →
remedy candidates (feeds bo_upaya + the Astrovastu direction-join). L5: does condition predict?

## §6 — Standards + hard gate
Computed-and-cited (a condition score stored only with its formula+citation; "weak planet means hardship" =
serve-time); L0 ON-CONFLICT / L1 delete-then-insert; orchestrator-native; two-pass; FORENSIC; floors-
aspirational; atomic grain (each avastha/dignity its own row); no-JH-parity; no tier; surgical migrations;
L0 = dignity-table authority, ga_vargas = varga-dignity authority (reference, don't recompute).

## §7 — Decisions upfront
1. condition_formula_v1 exact weights (lock as v1). 2. ga_condition new asset vs extend ga_strength
(recommend new — it's a distinct composite). 3. Which avastha sub-schemes (all 5 confirmed). 4. Graha-yuddha
win/lose criterion (degree-based vs the classical northern-planet rule). 5. Motion-state thresholds (exact
speed cutoffs per planet).

---

*End. The planetary-condition subsystem: unified deterministic condition per graha across all vargas + all
avasthas + motion/combustion/yuddha + the dasha-trajectory, versioned-formula, computed-and-cited. The
substrate Transit/Medical/Yoga consume.*
