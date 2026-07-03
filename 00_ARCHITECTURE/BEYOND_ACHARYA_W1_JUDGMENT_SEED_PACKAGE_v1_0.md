---
canonical_id: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE
version: 1.0
status: DRAFT-FOR-NATIVE-GLANCE — authored by Cowork under explicit native delegation (2026-07-02).
  These are the ratified W1 seeds the master plan gates W2+ on. The native delegated the judgment calls;
  this package makes them, cited and versioned. Every value is a FALSIFIABLE PRIOR under permanent L5 test
  (the Ranking Doctrine, plan §0.1) — not dogma. Native glance requested only on §0.2's flagged items.
created: 2026-07-02
author: Cowork (acting as delegated acharya) — for native Abhisek Mohanty
governs: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN §2 (the W1 sitting) → seeds bg_class_priors,
  bg_ghatana (event + activity ontology), bg_formula_constants, and the two query-time affinity tables.
grounded_in: live schema verified 2026-07-02 — CHART_FACTS_SCHEMA.json (~180 fact_categories),
  migration 325 (bodha_msr_signals column vocabularies), mi_kula._FAMILIES (11 families), ga_vargas_writer
  (30 vargas), migration 250 bg_combustion_orbs, LIFE_EVENT_LOG_v1_2 (15 LEL categories), migration 261
  bg_prashna_rules, ws2_l0_remedy_corpus (7 remedy types).
schema_findings_folded_to_plan:
  - C14: signal_type_registry/G52 is RETIRED (migration 223). Class-priors key on the free-TEXT columns
    signal_type_class × fact_kind × source_subsystem × signal_tradition on bodha_msr_signals — NOT a
    registry table. (Corrects the memory note "G52 signal_type_registry global prereq".)
  - C15: there is NO canonical domain enum (8 divergent code sites). §1 of this package DEFINES it; it
    becomes a W2 prerequisite (a migration normalizes the 8 sites to it).
changelog:
  - v1.0 (2026-07-02): first authored seed package (all five W1 tables + the canonical domain taxonomy).
---

# W1 JUDGMENT SEED PACKAGE v1.0

*The five seed tables the Beyond-Acharya build reads. Authored under native delegation. Cited to classical
sources where classical; flagged where a judgment call was made. All values are versioned priors, bounded,
and L5-calibratable — the ranking is a hypothesis under test, not a verdict.*

---

## §0 — READ FIRST: what I decided, and where your glance still helps

### §0.1 — The delegation, honestly framed

You delegated the W1 judgment calls to me. I have made them. Three things make this safe rather than
presumptuous: (1) the **classical content** (karakas, combustion orbs, varga importance, ontology
signatures) is scholarship with citations, not preference; (2) the **only irreducibly-personal input** —
your lived events — does not feed these seeds, it feeds L5 calibration later; (3) every number here is a
**bounded, versioned prior under permanent empirical test** — if I set one wrong, retrodiction catches it
and the L5→L0 arrow re-weights it, with your co-sign at the publication gate. I am setting priors, not
carving stone.

### §0.2 — The handful of calls where your glance genuinely adds value (everything else is classical)

1. **Domain taxonomy granularity (§1).** I unified 8 divergent code lists into 12 canonical life-domains.
   The only real judgment: whether `progeny` and `creativity` are one domain (I merged them under the 5th
   house) and whether `transition` is a domain or a magnitude-flag (I kept it as a cross-cutting domain
   because the code uses it). A 2-minute look confirms these read right to you.
2. **Bala-gating served state (§7, A-B).** I ruled that a weak-constituent yoga ranks as a distinct served
   state **"present-but-enfeebled"** rather than being hidden or fully-ranked. This is an astrological-honesty
   call you flagged interest in — confirm you want that third state.
3. **verification_certainty re-scale (§7, C5).** I ruled that verification stops being a *multiplicative
   salience term* (the 0.778 strangler) and becomes a *separately-served confidence dimension*. This is the
   cleanest fix but it changes what "salience" means slightly — worth your nod.
4. **Event base-rate priors (§5).** These are seeded from general population/demographic reasoning, not your
   life. They are the weakest-grounded numbers here BY DESIGN (they're what L5 will most improve). Treat them
   as placeholders with the right shape, not measurements.

Everything below not in this list is classical and I hold it to acharya grade.

---

## §1 — CANONICAL DOMAIN TAXONOMY (foundational; new — resolves the 8-site fragmentation, C15)

The system carries 8 inconsistent domain lists. This is the single canonical set every consumer normalizes
to (a W2 migration maps the old sites → these ids). 12 life-domains + `general`. Each maps to a primary
house cluster and absorbs the legacy synonyms.

| canonical_id | houses (primary) | absorbs (legacy synonyms across code) | scope |
|---|---|---|---|
| `career` | 10, 6, 1 | career, profession, authority, karma, status | profession, vocation, standing |
| `wealth` | 2, 11 | wealth, financial, finance, gain, income | assets, earning, gains |
| `relationship` | 7 | relationship(s), relational, marriage, partnership | spouse, unions, contracts-of-partnership |
| `progeny` | 5 | progeny, children, creative, creativity, intellect(5th) | children, creative output, purva-punya |
| `health` | 1, 6, 8 | health, psychological(somatic) | body, vitality, disease, longevity(with 8) |
| `education` | 4, 5, 9 | education | learning, degrees, higher knowledge |
| `family` | 4, 2(kutumba), 9(father),4(mother) | family, parents | home relations, mother/father, kin |
| `residence` | 4 | residential, property, land | dwelling, real estate, relocation-of-home |
| `travel` | 3, 9, 12 | travel | journeys, foreign lands, pilgrimage |
| `spirituality` | 9, 12, 5(mantra) | spiritual, spirit, character(dharmic) | dharma, moksha, sadhana |
| `character` | 1 (+ Moon) | mind, character, psychological(temperament) | temperament, disposition, mental state |
| `transition` | dusthana/sandhi cross-cut | transition | major life-phase turning points (cross-cutting) |
| `general` | — | general | catch-all; never a ranking target, only a fallback |

Note: technique-tags that appeared in one code list (`dasha`, `nadi_bnn`, `yogini_tajaka`, `house_domain`)
are NOT life-domains — they are subsystem/source tags and belong on `source_subsystem` / `signal_tradition`,
not here. This is the fragmentation's root cause: mixing "what life-area" with "by-what-technique."

---

## §2 — SALIENCE CLASS-PRIORS (→ `bg_class_priors`; keyed on the REAL columns, C14)

`signal_type_registry` is dead — priors key on `bodha_msr_signals`' actual columns. The class-prior is a
**positive multiplier centered on 1.0** that decides BETWEEN families; the within-class percentile (S-A)
decides WITHIN a family. Composition (the ruling): `class_prior = w(signal_type_class) × w(source_subsystem)
× w(signal_tradition)`, each factor a bounded multiplier, stored as three rows so each is independently
versionable and L5-adjustable.

### §2.1 — `w(signal_type_class)` — the primary axis (11 values from migration 325)

| signal_type_class | weight | rationale (classical) |
|---|---|---|
| `configuration` (yogas, raja/dhana/arishta) | **1.40** | Yogas are the acharya's headline structures; BPHS devotes its phala chapters to them. Highest. |
| `relationship` (dispositor, argala, parivartana, aspects) | **1.20** | The chart's wiring; a parivartana or argala reshapes a whole reading. |
| `position` (graha in sign/house, dignity) | **1.10** | The atomic backbone; individually humble, collectively decisive. |
| `magnitude` (bala, strength scores) | **1.00** | Modulates delivery (see A-B bala-gating); baseline. |
| `dasha_period` | **1.15** | Timing is half of Jyotish; a period's lord-condition is first-class. |
| `time_window` | **0.95** | Derived timing; slightly below the period itself. |
| `birth_moment` (panchanga, lagna specifics) | **1.05** | Foundational but often background once the chart is read. |
| `annual` (varshaphala/tajika) | **0.85** | Powerful but tradition-scoped (see tradition weight). |
| `medical` | **0.90** | Domain-specific; high within `health`, humble elsewhere (domain-conditioned at query time). |
| `vastu` | **0.70** | Environmental/remedial layer; genuinely peripheral to natal judgment. |
| `prashna` | **1.00** | Only fires on prashna charts; neutral base, gated by chart_type. |
| `absence` (fact_kind only; a signal that a factor is absent) | **0.80** | Real evidence (a missing yoga matters) but weaker than a present one. |

### §2.2 — `w(source_subsystem)` — provenance multiplier (12 values)

`structural 1.00` · `dasha 1.10` · `yoga 1.15` · `strength_ashtakavarga 0.95` · `nakshatra 1.05` ·
`sensitive 1.00` · `varga 1.00` (the varga-grain weight in §3 does the real varga work; this stays neutral) ·
`tajaka 0.85` · `sade_sati 1.05` · `panchanga 0.90` · `medical 0.90` · `vastu 0.70`.

### §2.3 — `w(signal_tradition)` — school weight (ratifiable; classical-parity default)

`parashari 1.00` (the spine) · `jaimini 0.95` · `kp 0.90` · `tajika 0.85` · `nadi 0.80` (Bhrigu-Nandi /
Nadi-Navamsa — powerful but method-sensitive) · `lal_kitab 0.70`. These are the *prior* tradition weights;
L5 triangulation (bo_sangati) will produce empirical concordance weights that overlay these under two-key.

### §2.4 — Family mapping (supersedes `mi_kula._FAMILIES`; C6 unification)

mi_kula's 11 families map onto the axes above so there is ONE weight source. Retire the embedded
`prior_weight` literals; mi_kula v2 reads these. Mapping (family → dominant class/subsystem, seed weight):
`fam_graha_natal→position/structural 1.10` · `fam_dasha_period→dasha_period/dasha 1.15` ·
`fam_yoga→configuration/yoga 1.40` · `fam_divisional→position/varga 0.90` (varga vector §3 refines) ·
`fam_transit→time_window/(transit service) 0.95` · `fam_convergence→configuration/structural 1.25` (multi-
system convergence is the strongest single evidence, per the Doctrine's structural-elevation organ) ·
`fam_ashtakavarga→magnitude/strength_ashtakavarga 0.95` · `fam_msr_signal→position 1.00` ·
`fam_anchor→(L4, not salience) 1.00` · `fam_null_control / fam_shuffled_birth → 0.0` (controls, unchanged).

### §2.5 — Aggregation ruling (the hierarchy, plan S-A + hierarchical-aggregation)

Atomic per-varga tallies (e.g. `varga_position` in D27) roll UP into composite profile signals; the atoms
stay queryable but NEVER occupy the top band on their own. Composition: a composite's salience = its own
class_prior × f(within-class percentile) × the effective-evidence-corrected count of its atoms (S-B:
contribution ∝ log(1+n_family), not raw n). The career top-10 must therefore be 10th-lord / karaka / yoga
composites — never a pile of sub-varga atoms (the G10 acceptance witness).

---

## §3 — VARGA WEIGHT VECTOR (→ `bg_class_priors` varga axis; 30 vargas)

Base weight = classical **Ṣoḍaśavarga Vimśopaka** scheme (BPHS ch. on Vimśopaka-bala; total 20 across the 16
Parāśari vargas), normalized to a multiplier centered ~1.0 for D1. Supplementary (11) and Nāḍī (3) vargas
are floored low (present, never top-band) — the Doctrine keeps them queryable; specificity (S-A) can still
raise a genuinely extreme one.

### §3.1 — Domain-neutral base weight (stored)

| Varga | Vimśopaka | base_wt | · | Varga | Vimśopaka | base_wt |
|---|---|---|---|---|---|---|
| D1 | 3.5 | **1.00** | | D24 | 0.5 | 0.30 |
| D2 | 1.0 | 0.45 | | D27 | 0.5 | 0.30 |
| D3 | 1.0 | 0.45 | | D30 | 1.0 | 0.45 |
| D4 | 0.5 | 0.30 | | D40 | 0.5 | 0.28 |
| D7 | 0.5 | 0.30 | | D45 | 0.5 | 0.28 |
| D9 | 3.0 | **0.90** | | D60 | 4.0 | **0.95** |
| D10 | 0.5 | 0.55* | | D5,D6,D8,D11,D14,D15,D21,D32,D33,D50,D54 (supp.) | — | 0.18 |
| D12 | 0.5 | 0.32 | | D108, D150, D2700 (Nāḍī) | — | 0.12 |
| D16 | 2.0 | 0.60 | | | | |
| D20 | 0.5 | 0.35 | | | | |

\*D10 is lifted above its raw Vimśopaka (0.5→0.55) because modern practice weights the daśāṃśa heavily for
career; this is a documented deviation-from-strict-Vimśopaka, flagged. D60 stays high (Parāśara: "D60
foremost") but note its extreme time-sensitivity — pair with a robustness flag (S-D).

### §3.2 — Domain-conditioned overlay (applied at QUERY time, A-D; stored stays neutral)

Multiply the base by the overlay when the question's domain is known (never bake into storage — S-E):

| domain | boosted vargas (×1.5) | rationale |
|---|---|---|
| career | D10, D1 | daśāṃśa = karma/profession |
| relationship | D9, D1 | navāṃśa = spouse/dharma |
| progeny | D7, D9 | saptāṃśa = children |
| wealth | D2, D11-effects via D1 | horā = wealth |
| residence | D4 | caturthāṃśa = fortune/property |
| education | D24, D9 | siddhāṃśa/caturviṃśāṃśa = learning |
| family | D12, D4 | dvādaśāṃśa = parents/lineage |
| health | D30, D1 | triṃśāṃśa = evils/affliction |
| spirituality | D20, D60 | viṃśāṃśa = worship/upāsanā |
| character | D1, D9, D16 | ṣoḍaśāṃśa = comforts/temperament |

---

## §4 — GRAHA × DOMAIN AFFINITY (A-A karaka congruence; → query-time table)

Multiplier applied at query time to a signal whose graha bears on the question's domain. Base 1.0; strong
natural-karaka congruence up to 1.5; weak/contrary down to 0.7. Sources: BPHS kāraka chapter (naisargika
kārakas) + Jaimini chara-kāraka significations + standard bhāva-kāraka assignments.

| graha \ domain | career | wealth | relat. | progeny | health | educ. | family | resid. | travel | spirit. | char. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sun | **1.4** | 1.0 | 0.8 | 0.9 | 1.1 | 1.0 | 1.1(father) | 0.9 | 0.9 | 1.0 | 1.1 |
| Moon | 1.0 | 1.0 | 1.1 | 1.0 | 1.1 | 1.0 | **1.3**(mother) | 1.0 | 1.0 | 1.0 | **1.4** |
| Mars | 1.2 | 1.0 | 1.0 | 0.9 | 1.2(surgery/accident) | 0.9 | 1.0(siblings) | **1.4**(land) | 1.0 | 0.9 | 1.1 |
| Mercury | 1.2 | 1.2(commerce) | 1.0 | 1.0 | 1.0 | **1.4** | 1.0 | 0.9 | 1.1 | 1.0 | 1.2(intellect) |
| Jupiter | 1.1 | 1.3(dhana) | 1.1 | **1.5**(putra) | 1.0 | 1.3 | 1.1 | 1.0 | 1.0 | **1.4** | 1.1 |
| Venus | 1.0 | 1.2(luxury) | **1.5**(kalatra) | 1.2(arts) | 1.0 | 1.0 | 1.0 | 1.2(vehicles) | 1.0 | 0.9 | 1.1 |
| Saturn | **1.4**(karma) | 1.0 | 0.9 | 0.8 | 1.2(chronic/āyuṣ) | 0.9 | 0.9 | 1.2(labor/land) | 1.0 | 1.1(vairāgya) | 1.0 |
| Rahu | 1.1(unconv.) | 1.1(speculation) | 0.9 | 0.8 | 1.0(mystery) | 1.0 | 0.8 | 1.0 | **1.4**(foreign) | 1.1 | 1.0 |
| Ketu | 0.9 | 0.9 | 0.8 | 0.8 | 1.1(occult ailments) | 1.0 | 0.9 | 0.9 | 1.1 | **1.5**(mokṣa) | 1.1(detach) |

---

## §5 — EVENT ONTOLOGY (→ `bg_ghatana`.`brahma_event_ontology`; 22 classes)

Keyed to the 15 LEL `category` values. Each class carries: **signature** (houses / lords / kārakas / vargas
/ daśā rules / transit triggers), **magnitude_floor** (min LEL magnitude to count), **adjacency** (classes
that count as PARTIAL for adjudication), and a **base-rate prior by age band** (0-12 / 13-25 / 26-40 / 41-60
/ 60+ — per-band probability the event occurs at all; PLACEHOLDER shape per §0.2.4). Citations: BPHS bhāva
+ phala chapters; Phaladeepika; standard significator practice.

| event_class | LEL cat | signature (houses · kārakas · vargas · timing) | mag_floor | adjacency | base-rate by band |
|---|---|---|---|---|---|
| `career_entry` | career | 10L/6L, Sun/Sat, D10; MD/AD of 10th-related | moderate | career_change | .00/.55/.20/.05/.01 |
| `career_advancement` | career | 10/11 lords, Sun, D10; benefic transit to 10th | moderate | career_entry | .00/.15/.45/.35/.05 |
| `career_change` | career | 10L in dusthāna/parivartana, Rahu; daśā-sandhi | moderate | career_entry, transition | .00/.20/.45/.30/.05 |
| `career_setback` | career/loss | 10L afflicted, 6/8/12 to 10th, Sat/Rahu; adverse transit | significant | career_change | .00/.10/.35/.35/.15 |
| `business_launch` | career/finance | 7/10/11, Merc/Jup, D10; strong daśā | significant | career_entry | .00/.15/.50/.30/.05 |
| `education_milestone` | education | 4/5/9 lords, Merc/Jup, D24; benefic daśā | moderate | — | .10/.70/.25/.05/.01 |
| `exam_outcome` | education | 5/9, Merc, D24; transit to 5th | trivial | education_milestone | .15/.75/.20/.03/.01 |
| `marriage` | relationship | 7L, Venus (kalatra), D9; 7th-daśā, Jup/Sat transit to 7th | significant | partnership_formed | .00/.45/.45/.10/.02 |
| `romantic_start` | relationship | 5/7, Venus, D9; benefic transit | moderate | marriage | .05/.55/.35/.10/.02 |
| `separation` | relationship/loss | 7L afflicted, 6/8/12 to 7th, Rahu/Sat/Mars; adverse daśā | significant | marriage(as negation) | .00/.15/.40/.30/.10 |
| `childbirth` | family/progeny | 5L, Jupiter (putra), D7; 5th-daśā, Jup transit to 5th | significant | — | .00/.30/.60/.08/.00 |
| `parental_event` | family | 4th(mother)/9th(father), Moon/Sun, D12; relevant daśā | moderate | bereavement | .05/.20/.35/.35/.20 |
| `bereavement` | loss | 8/12, 2nd(maraka), Sat/Ketu; māraka daśā, adverse transit | significant | parental_event | .05/.15/.30/.30/.30 |
| `major_gain` | finance/gain | 2/11 lords, Jup/Merc, D2; dhana-daśā | moderate | property_acquisition | .00/.20/.40/.30/.10 |
| `major_loss` | finance/loss | 2/11 afflicted, 12L, Sat/Rahu; adverse daśā | significant | career_setback | .00/.15/.40/.30/.15 |
| `property_acquisition` | finance/resid. | 4L, Mars (bhūmi), D4; 4th-daśā, benefic transit | moderate | major_gain, relocation | .00/.15/.50/.30/.05 |
| `relocation` | residential/travel | 4/3/12, Moon/Rahu, D4; daśā-change | moderate | property_acquisition, foreign_settlement | .05/.30/.40/.20/.05 |
| `foreign_settlement` | travel | 12/9/7, Rahu, D9/D12; Rahu daśā/transit | significant | relocation | .00/.35/.45/.15/.02 |
| `illness_acute` | health | 6/8L, Mars/Sat, D30; adverse transit to lagna/6th | moderate | surgery, chronic_onset | .15/.20/.25/.30/.40(annualized-ish) |
| `chronic_onset` | health | 6/8, Sat (chronic), lagna-lord weak, D30; Sāde-Sati | significant | illness_acute | .02/.08/.20/.35/.45 |
| `surgery` | health | 6/8, Mars (śastra), D30; Mars/Ketu daśā-transit | significant | illness_acute | .05/.10/.20/.30/.35 |
| `spiritual_turn` | spiritual | 9/12/5(mantra), Jup/Ketu (mokṣa), D20; Ketu/Jup daśā | moderate | transition | .00/.15/.25/.35/.45 |

`transition` and `legal`/`creative`/`psychological` LEL categories are handled as **magnitude/valence
overlays or adjacency members** rather than separate signature classes (they lack a distinct classical
signature); a `major_transition` catch-all class inherits the signature of whichever domain it touches, at
magnitude_floor = `major`. Each row also stores `citations[]` (BPHS bhāva chapter refs) — populated in the
seed migration.

---

## §6 — ACTIVITY ONTOLOGY (→ `bg_ghatana`.`brahma_activity_ontology`; electional)

Each electional class: **significators** (grahas/houses/vargas to strengthen), **avoidances** (panchanga /
dūrmuhūrta / tārā-bala / candra-bala rules), **fructification** (BPHS/Muhūrta-Chintāmaṇi timing). The muhūrta
engine already derives 7 activities from domains; this formalizes and extends them.

| activity_class | strengthen (grahas · houses · varga) | avoid | fructification anchor |
|---|---|---|---|
| `marriage` | Venus, Jup; 7th; D9 strong | 6/8/12 afflicting 7th; Bhadra; Venus/Jup combust | tārā+candra-bala; Jup/Venus dignified |
| `business_start` | Merc, Jup, Sun; 10/11; D10 | 8th lord hora; Rahu-kāla; weak 10L | strong lagna+10th at election |
| `contract_signing` | Merc; 3/11; D1 | Merc combust/retro; void Moon | Merc dignified, waxing Moon |
| `travel_journey` | Moon, Merc; 3/9/12 | dūrmuhūrta; Moon in 8th from janma-rāśi | favorable candra-bala, disha-śūl clear |
| `property_purchase` | Mars, Sat; 4th; D4 | 4L weak; adverse Sat transit | 4th-lord strong, Mars dignified |
| `medical_procedure` | (elective surgery) Mars controlled; 6/8 timing | Kṛṣṇa-caturdaśī; afflicted lagna; Moon in surgery-site rāśi | benefic lagna, Moon away from affected part |
| `education_start` | Merc, Jup; 4/5; D24 | Merc combust; weak 5L | Vasanta-pañcamī-type windows; dignified Merc/Jup |
| `spiritual_initiation` | Jup, Ketu; 9/12; D20 | — (broadly permissive) | Jup/Moon strong; auspicious tithi/nakṣatra |
| `vehicle_purchase` | Venus; 4th (comforts); D4 | Venus combust; 4L weak | Venus dignified, benefic Moon |
| `financial_investment` | Jup, Merc; 2/11; D2 | 8th-lord periods; void Moon | dhana-yoga active, waxing Moon |
| `griha_pravesh` | Moon, Jup; 4th; D4 | Cāturmāsya prohibitions; weak Moon | classical griha-praveśa nakṣatras |
| `ceremony_naming` | Jup, Moon; 5th | dūrmuhūrta; Rikta tithi | benefic Moon-nakṣatra |

Activity ↔ event symmetry: each activity's success signature mirrors the corresponding event_class seen from
the electional side (e.g. `marriage` activity ↔ `marriage` event), enabling Loop-B fructification follow-up.

---

## §7 — CONSTANTS-RATIFICATION SHEET (→ `bg_formula_constants`; class + value + bounds + citation)

Class column: **CLASSICAL** (cite, encode exactly, never tune) · **NATIVE-JUDGMENT** (ratify, versioned,
L5-calibratable within bounds) · **ENGINEERING** (document) · **CONFLATION-BUG** (fix at source, do not
seed).

| constant | current | ruling (this package) | class | bounds | citation |
|---|---|---|---|---|---|
| Combustion orbs (per-graha) | Moon12/10 Mars17/15 Merc14/12 Jup11/9 Ven10/8 Sat15/12 Ra/Ke 9/7 | **KEEP** (already correct in `bg_combustion_orbs`); delete ka_vighnakara flat 6° and repoint to this (C12) | CLASSICAL | fixed | Sārāvalī 6 / BPHS 3 |
| Obstruction severity thresholds | 0.70 / 0.40 | RATIFY as 0.70/0.40 (severe/moderate/mild); move to registry | NATIVE-JUDGMENT | [0.6–0.8]/[0.3–0.5] | uncited → house-strength convention |
| Magnitude tiers | rarity/10yr; 0.60/0.40/0.20 | RATIFY; align to LEL magnitudes (life-altering/major/significant/moderate/trivial) | NATIVE-JUDGMENT | ±0.10 each | anchor-v2 (§plan W4B) |
| Corroboration levels | 5 (two-pass) / 2 | **RE-SCALE per C5 below** — remove from salience product | NATIVE-JUDGMENT | n/a | — |
| Dignity scores | (v1 _DIGNITY_SCORE) | RATIFY: exalted 1.00 · mūlatrikoṇa 0.90 · own 0.80 · gt-friend 0.65 · friend 0.55 · neutral 0.45 · enemy 0.30 · gt-enemy 0.20 · debilitated 0.10 | NATIVE-JUDGMENT | ±0.05 | Ṣaḍbala/dignity convention |
| House weights | (v1 _HOUSE_WEIGHT) | RATIFY: Kendra(1,4,7,10) 1.15 · Trikoṇa(1,5,9) 1.20 (1 counts as trikoṇa) · Upachaya(3,6,11) 1.00 · 2,8,12 0.85 · dusthāna(6,8,12) contextual | NATIVE-JUDGMENT | ±0.10 | BPHS bhāva-bala |
| Attention-budget split | (new) | RATIFY 70/20/10 (head/dissent/tail); per-query-class tunable | NATIVE-JUDGMENT | head[0.5–0.8] tail[0.05–0.2] | Doctrine §1.4 |
| ka_sangam confidence=convergence | mirror | **CONFLATION-BUG** — fix at source (W4A), do not seed | CONFLATION-BUG | — | C10 |
| ka_sangam dasha_score>0.3 flag | 0.3 | RATIFY 0.3; to registry | NATIVE-JUDGMENT | [0.2–0.4] | uncited |
| mi_sambandha channel priors | career .40/.35/.25 etc. | RATIFY as Dirichlet base (per MIMAMSA_V2) | NATIVE-JUDGMENT | Dirichlet α | uncited |
| mi_gunanaka 3× divergence cap | 3.0 | KEEP | NATIVE-JUDGMENT | [2–4] | MIMAMSA_V2 |
| Holdout partition (MD5 mod10) | 20% | KEEP | ENGINEERING | — | — |

### §7.1 — The verification_certainty re-scale ruling (C5 + S-A, resolved)

**Ruling:** verification stops being a multiplicative salience term. In v1, salience carried
`verification_certainty = log(1+corroboration)/log(10)` (max ≈0.778), which capped the top band and killed
`chart_defining`. Two facts make the fix clean: (1) S-A within-class percentiles mean absolute scale no
longer matters for ranking; (2) verification is *epistemic confidence*, not *astrological weight* — they are
different quantities that should never have been multiplied. **So:** `epistemic_tier` (`two_pass_verified` /
`documented_approximation`, already a column) is served as a SEPARATE confidence dimension on the verdict
object (weighting the *presentation* and the calibration, per S-D), and is REMOVED from the salience
product. Salience v2 = `class_prior × f(pctl_in_class) × specificity × condition_terms` (stored) `×
activation × karaka_congruence × varga_affinity` (query-time). `chart_defining` now fires on genuine
top-percentile structures. This is the §0.2.3 call for your nod.

---

## §8 — SEED → ASSET → WAVE MAP (how this package becomes data)

| §here | seeds | asset / table | wave |
|---|---|---|---|
| §1 domain taxonomy | canonical domain enum + a normalization migration for the 8 sites | (schema) `domain` normalization | **W2A prerequisite** |
| §2 class-priors | `w(signal_type_class)`, `w(source_subsystem)`, `w(signal_tradition)`, family map | `bg_class_priors` / `brahma_class_priors` | W2A |
| §3 varga vector | base + domain overlay | `bg_class_priors` (varga axis) | W2A (stored) / W3 (overlay) |
| §4 graha×domain | affinity matrix | query-time table (bg_class_priors or bg_formula_constants) | W2A seed / W3 apply |
| §5 event ontology | 22 event classes | `bg_ghatana` / `brahma_event_ontology` | W2A |
| §6 activity ontology | 12 activity classes | `bg_ghatana` / `brahma_activity_ontology` | W2A |
| §7 constants sheet | all judgment constants + re-scale | `bg_formula_constants` / `brahma_formula_constants` | W2A |

*End of BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE v1.0. This discharges the W1 judgment sitting under native
delegation. The four §0.2 items await a native glance; everything else is classical and ready to seed in
W2A. Next: fold C14/C15 into the master plan, then author `BA_W2A_L0_SEEDS_AND_L1_EXT` which encodes these
tables as the migration + writer seeds.*
