---
artifact: YOGA_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: YOGA_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — maximal scope, computed-and-cited hard gate
authored_for: the Yoga subsystem build (subsystem #2 of 7, Wave 1)
purpose: >
  Build the Yoga subsystem to FULL classical depth across L0–L5: turn the flat yoga catalog + flat firings
  into a complete yoga SYSTEM (families, formation/cancellation/bhanga, strength-gradient, activation-timing,
  yoga-on-yoga interactions, constituent decomposition) so the deterministic yoga data is maximally dense for
  holistic LLM synthesis. Embedded via [[feedback-subsystem-embedding-pattern]]; governed by the roadmap §0.5
  maximal-enrichment standard + the COMPUTED-AND-CITED hard gate.
read_in_combination_with:
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§0.5 enrichment standard; §2 yoga depth bar; §8 build strategy)
  - feedback-subsystem-embedding-pattern (the 8-step method)
  - NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md (the depth template this matches)
  - A8_T1_STRUCTURAL_SPEC (existing yoga_fires) + bg_yogas (existing brahma_yoga_catalog, 250+)
hard_gate: A yoga datum is STORED only if deterministically COMPUTED + CITABLE to a classical source; interpretive "results/meaning" with no formula = serve-time, never stored.
---

# Yoga Subsystem — Master Plan (maximal, L0–L5) v1.0

## §0 — Reframe: catalog → system

Today: a flat CATALOG (`bg_yogas` / `brahma_yoga_catalog`, 250+) + flat FIRINGS (`A8 yoga_fires` — which fired).
Maximal: a complete yoga SYSTEM — every yoga from every source, each with its full deterministic structure
(formation conditions, cancellation/bhanga, strength as a gradient, activation timing, interactions,
constituent decomposition). The bar: an acharya of yoga-shastra says "every computable aspect of every yoga
is captured." Interpretive *meaning* of a yoga = serve-time; its *structure* = stored deterministic fact.

## §1 — The three-data-category split (per roadmap §0)
- **STATIC → L0 (`bg_yogas` enriched):** the yoga DEFINITIONS — every yoga's formation rule, cancellation/
  bhanga rules, family membership, classical citation, the strength-formula template. Chart-agnostic.
- **CHART-SPECIFIC → L1 (extend `ga_structural` / a focused `ga_yoga` view):** which yogas FIRE for this
  chart, their computed strength, constituent decomposition, activation windows. PyJHora-derived.
- **No service category** — yogas are natal-structural (no time-varying compute needed; activation timing
  joins the existing dasha asset + the W2 transit service when built).

## §2 — L0 `bg_yogas` (maximal definition reference)

### §2.1 — Exhaustive yoga catalogue (every source, computed+cited)
Enumerate EVERY yoga with a deterministic formation rule + citation, from across the corpus:
- **Pancha Mahapurusha** (Ruchaka/Bhadra/Hamsa/Malavya/Sasa — 5).
- **Raja yogas** (all variants: kendra-trikona lord conjunctions/aspects/exchanges; Dharma-Karmadhipati;
  Vipareeta Raja — Harsha/Sarala/Vimala; Neecha-Bhanga Raja; Kahala; Chamara; Sankha; Bheri; Mridanga;
  Parvata; Lakshmi; Gauri; Chandra-Mangala; the full BPHS + Saravali + Phaladeepika Raja set).
- **Dhana yogas** (2nd/11th lord combinations, all classical wealth yogas + Jataka Parijata variants).
- **Nabhasa yogas — ALL 32** (the geometric/structural family most systems omit): the 3 Aakriti groups
  (20 Aakriti — Gada/Sakata/Vihaga/Sringataka/Hala/Vajra/Yava/Kamala/Vapi/Yupa/Sara/Sakti/Danda/Nauka/
  Kuta/Chatra/Chapa/Ardha-Chandra/Chakra/Samudra), the 7 Sankhya yogas (Vallaki/Damini/Pasa/Kedara/Sula/
  Yuga/Gola — by count of occupied signs), the 2 Dala (Mala/Sarpa), the 3 Asraya (Rajju/Musala/Nala).
- **Chandra yogas** (Sunapha/Anapha/Durudhara/Kemadruma + Gajakesari + Adhi + the Moon-based set).
- **Surya yogas** (Vesi/Vasi/Ubhayachari).
- **Arishta yogas** (Balarishta + the misfortune/affliction yogas — Daridra, Shakata, etc.).
- **Sannyasa / Pravrajya yogas** (renunciation — 4+ grahas in one sign etc.).
- **Specialized** (Kala Sarpa variants, Guru-Chandala, Grahan, Amala, Saraswati, Budha-Aditya, Veeprita,
  Maha Bhagya, Pushkala, etc.) + the "300 combinations" (BV Raman) set where each has a deterministic rule.

### §2.2 — Per-yoga DEFINITION fields (each, where computable+citable)
yoga_id, name_sa/en, family (§2.3), **formation_rule** (the exact deterministic predicate: which lords/
houses/planets/aspects), **cancellation_rules** (Bhanga — what nullifies it), **partial-formation
threshold** (what counts as 80%-formed), **required vs strengthening conditions**, classical_source (verse
citation into bg_texts), the **strength-formula reference** (§3 — the template, not the value), result-class
(the deterministic category — benefic/malefic/mixed — NOT the prose result), school/tradition variant marker.

### §2.3 — Yoga FAMILY taxonomy (static)
Hierarchical family tree: Mahapurusha / Raja / Dhana / Nabhasa(Aakriti/Sankhya/Dala/Asraya) / Chandra /
Surya / Arishta / Sannyasa / Specialized — each yoga's membership + parent-family. Enables family-level
convergence at L2.

### §2.4 — Yoga-INTERACTION rules (static — the deep part)
The classical rules for how yogas modify each other beyond simple cancellation: which yogas STRENGTHEN
another, which CONFLICT, which SUPERSEDE (a stronger yoga overriding a weaker). Stored as static
interaction-pair rules with citations. (The per-chart firing of these = L1/L2.)

## §3 — Strength formula (versioned, deterministic)
`yoga_strength_formula_v1`: a yoga's strength = f(constituents' shadbala + dignity + avastha + varga-spread
[reuses Dignity subsystem] + house-strength + aspect-modifiers), per the Phaladeepika/classical weighting
where a formula exists. Versioned + reproducible. If a yoga has NO classical strength formula → store the
firing + constituents but mark strength `null` (computed-and-cited gate; never invent a strength).

## §4 — L1 (per-chart yoga firing + structure)

Per chart per ayanamsha, extend `ga_structural` (or a focused asset):
- **yoga_fires** (exists) — EXTEND with: full **constituent decomposition** (the exact fact_ids of the
  planets/houses/aspects that formed it — references chart_facts, the L1-authority discipline), **strength**
  (yoga_strength_formula_v1), **partial-formation flag + %**, **bhanga/cancellation status** (did a
  cancellation rule fire? which?), **family membership**.
- **yoga activation windows** — when each fired yoga's constituent-lords run their dasha/antardasha (joins
  `ga_dashas`); the deterministic "when does this yoga deliver." (Transit-activation added when W2 lands.)
- **yoga-interaction firings** — which static §2.4 interaction-pairs are active in THIS chart (yoga A
  strengthens yoga B here).
- Two-pass; FORENSIC: the native's known yogas reproduce; constituent fact_ids resolve.

## §5 — L2 exploitation (extend bo_laksana / bo_karanajala / bo_sangati — flag for sign-off)
- **Yoga signals** (bo_laksana): each firing → a signal with its strength + constituents + activation.
- **Yoga convergence** (bo_sangati): multiple yogas on one life-domain = weight-of-evidence (the
  convergence-density philosophy).
- **Yoga-interaction edges** (bo_karanajala): the §2.4 interactions as graph edges (yoga A → strengthens →
  yoga B). Yoga-family clusters as graph communities.
- Flag as A10–A14 extensions for native sign-off (roadmap rule).

## §6 — L3/L4/L5 (substrate now, exploit later)
L3: yoga-activation TIMING (which yoga fires in which dasha/transit window — joins the transit service).
L4: yoga-specific remedies (afflicted/cancelled yogas → bo_upaya). L5: which yogas actually predicted events.

## §7 — Standards + the hard gate
Deterministic-first; **computed-and-cited HARD GATE** (a yoga's formation/strength stored only with a
classical formula+citation; its interpretive "result" is serve-time); atomic grain; L0 ON-CONFLICT / L1
delete-then-insert idempotency; orchestrator-native (@register, frozen contract); two-pass; FORENSIC-gated;
floors-aspirational (chase every computable yoga; an uncited yoga-strength is worse than a null one); no-JH-
parity; no tier; surgical migrations; bg_yogas = authority for definitions, ga = references.

## §8 — Decisions to resolve upfront (sign-off before briefs)
1. The exact source-set for the yoga catalogue (BPHS + Saravali + Phaladeepika + Jataka Parijata + Brihat
   Jataka + 300-combinations — confirm which editions, all into bg_texts).
2. Partial-formation threshold definition (how "formed" counts).
3. ga_yoga as a focused new asset vs extending ga_structural (recommend extend, less duplication).
4. Strength-formula weighting (yoga_strength_formula_v1 exact weights) — lock as v1.
5. How interaction rules are sourced (which texts give explicit yoga-interaction rules vs which are inferred
   — only store the explicitly-cited ones per the hard gate).

---

*End. Yoga subsystem maximal: every yoga from every source, full formation/cancellation/bhanga/strength/
activation/interaction structure, computed-and-cited only, embedded L0→L5 via the pattern. The catalog
becomes a system.*
