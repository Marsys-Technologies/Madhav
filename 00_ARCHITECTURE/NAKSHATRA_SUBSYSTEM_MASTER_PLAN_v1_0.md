---
artifact: NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: NAKSHATRA_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — native-ratified maximal scope, full L0–L5 subsystem
authored_for: the Nakshatra Subsystem build (Cowork plans → Claude Code in Antigravity executes)
supersedes: NAKSHATRA_TWO_ASSET_PLAN_v1_0.md (absorbed — the two assets are this plan's L0+L1 tier)
purpose: >
  Define the COMPLETE Nakshatra subsystem as a first-class parallel framework spanning L0–L5, not a
  single asset. The nakshatra system is its own zodiac (its own dignities, deities/powers, dasha engine,
  compatibility science, timing logic) — equal to the rashi chart, not subordinate. This plan captures
  EVERY classical + deterministic nakshatra data point across the layers, maximal, then tiers the BUILD:
  Tier 1 (now: L0 reference + L1 parallel chart) · Tier 2 (designed-now, built with L2 Bodha) ·
  Tier 3 (substrate-captured-now, exploited at L3/L4/L5).
governing_principle: >
  Capture richly at L0/L1 NOW (storage is cheap; the chart cannot be re-observed later); phase the
  EXPLOITATION (graphs, signals, timing, remediation, research) to the layer where it belongs. Everything
  deterministic + classically-cited; no LLM-generated content; no narrative.
context: Audit 2026-06-10 found L1 had nakshatra POSITION but lacked attribution DEPTH. Native: build maximal, before/alongside L2.
---

# Nakshatra Subsystem — Master Plan (L0–L5) v1.0

## §0 — The reframe (why this is a subsystem, not an asset)

The rashi (sign) and nakshatra systems are **two complete, independent coordinate systems over the same
ecliptic**. Most software treats nakshatras as a footnote to the sign chart. Classically the nakshatra
system is its OWN full framework: its own deities + powers (shakti), its own dasha engine (Vimshottari
runs on nakshatras), its own compatibility science (kuta), its own muhurta + timing logic, its own
predictive grain (Nadiamsa). **The deepest value comes from treating the nakshatra layer as a first-class
PARALLEL CHART — a second independent witness that either corroborates or contradicts the rashi reading.**
Agreement across two independent systems is the strongest deterministic signal an instrument can produce;
contradiction between them is the acharya-grade "this chart is subtler than it looks." This reframe decides
what lives at each layer.

This subsystem is also the clearest expression of the project's end-goal — "a research tool for astrology
as a discipline": the nakshatra space is high-dimensional, under-studied, and richly deterministic.

## §1 — The full subsystem across L0–L5 (the vision)

| Layer | Nakshatra role | Asset(s) | Build tier |
|---|---|---|---|
| **L0** Brahmagyan | The enriched GLOBAL reference — every chart-agnostic nakshatra/pada datum + all static matrices | `bg_nakshatra` (+ pada + matrix tables) | **Tier 1 — now** |
| **L1** Gaṇita | The per-chart PARALLEL nakshatra chart — placement, attribute-join, sub-grains, the nakshatra dispositor graph, degree-flags, chart statistics | `ga_nakshatra` | **Tier 1 — now** |
| **L2** Bodha | Nakshatra SIGNALS + the nakshatra dispositor GRAPH as a parallel CGM + nakshatra as a third convergence witness | extends `bo_laksana`/`bo_karanajala`/`bo_sangati` | **Tier 2 — design now, build w/ L2** |
| **L3** Kāla | Nakshatra TIMING engine — transit-nakshatra activations, Panchapakshi windows, Tara-by-date, vedha timing | extends `ka_*` | **Tier 3 — substrate now, build at L3** |
| **L4** Phala | Nakshatra REMEDIATION — deity/sound/mantra → upaya bridge | extends `ph_*` / feeds `bo_upaya` | **Tier 3 — substrate now** |
| **L5** Mīmāṃsā | Nakshatra RESEARCH substrate — which nakshatra factors predicted lived events (held-out) | extends `mi_*` | **Tier 3 — substrate now, exploit at L5** |

**Build now = Tier 1 (L0 + L1).** Tiers 2/3 are *designed* here so the Tier-1 capture is complete enough
to feed them — you capture the substrate once, exploit it later at the right layer.

---

## §2 — L0 `bg_nakshatra` (GLOBAL reference — maximal static capture) [Tier 1]

Three grains, FK'd: **per-nakshatra (27 + Abhijit 28th)**, **per-pada (108)**, **relational matrices**.

### §2.1 — Per-nakshatra attributes (the 27/28)
Identity+span (number, name_sa IAST+Devanagari, name_en, alt_names, start/end longitude, span, rashi(s)
spanned, degree-in-rashi ranges). Rulership (vimshottari_lord, presiding deity/devata + secondary deities,
ruling vs deity distinction). **Compatibility/nature axes:** gana (Deva/Manuṣya/Rākṣasa), nadi
(Ādi/Madhya/Antya), yoni (14-animal + sex), varna, tatva/element, guna, pakshi/bird, nakshatra-gender.
**Muhurta classification:** type (Chara/Dhruva/Mishra/Ugra/Mridu/Tikshna/Kshipra/Laghu), disha, favorable/
prohibited activities. **Symbolism + theology:** symbol, **shakti + basis-above + basis-below + net-result**
(the Nakshatra Shakti verses), motivation (dharma/artha/kama/moksha), body_part (Kalapurusha). **Longevity/
maturity:** paramayus, **naisargika maturity age** (the age each nakshatra "ripens"). **Deity→domain map**
(§2.5). **Sound layer** (§2.4). All with classical_source citations.

### §2.2 — Per-pada (108)
pada_number, pada_lord, **pada_navamsa_sign** (static map), pada degree-range (3°20′), **pada_akshara**
(naming syllable), pada deity-nuance, pada element/dosha shading, the static vimshottari sub-lord seed,
**pada→navamsa cross-map** (the deterministic link between nakshatra-pada and the D9 layer).

### §2.3 — Relational matrices (static — the foundation compatibility/timing run on)
Hold COMPLETE matrices, not scalars: **yoni 14×14** (friend/enemy/neutral + the classical clash pairs),
**tara 27×27** (the 9-fold cycle from any reference nakshatra), **gana 3×3**, **nadi 3-way clash**, **rajju**
(positional clash groups: aroha/avaroha + the 5 body-part rajjus), **vedha pairs** (Sarvatobhadra
obstruction pairs), **mahendra / stree-deergha / varna-kuta / vashya-via-nakshatra** kuta tables. These are
the 36-guna Ashtakuta compatibility substrate + the timing-vedha substrate — all static.

### §2.4 — Sound / phonetics layer
The 108 syllables (akshara) per pada + **bija/sound correspondences + nakshatra→mantra mapping** (feeds L4
Upaya remediation). Static.

### §2.5 — Deity→domain structured map
Each presiding deity carries a life-DOMAIN (Yama→death/discipline, Ashwins→healing, Agni→fire/digestion,
Brahma→creation, …). Structuring deity→domain makes "planet in Yama's nakshatra" computationally
connectable to a life-domain — a deterministic nakshatra→domain bridge L2's CDLM uses.

### §2.6 — Additional nakshatra cycle definitions (static seeds)
The cycle-DEFINITIONS (chart-position is L1): Nakshatra-Nadi timing cycle, Yogini-from-nakshatra,
Sapta-Shalaka/Sarvatobhadra vedha cycles, the 27 sub-taras (9×3), Kalachakra-nakshatra seeds,
Gauri-Panchang/Chandra-Tara-Vela tables.

### §2.7 — Multi-tradition variants + cross-tradition maps (the research move)
Where texts disagree (BPHS vs Muhurta vs Nadi on gana/yoni/etc.), hold VARIANTS with `tradition_scope`
markers — never flatten to one. **Abhijit** as the 28th with tradition_scope (used in some muhurta/longevity;
excluded from 27-fold dasha math). **Cross-tradition mansion maps:** nakshatra ↔ Chinese 28 lunar mansions
↔ Arabic 28 manazil (the lunar-mansion systems across cultures) — pure static comparative reference.

### §2.8 — L0 registration
`bg_nakshatra` + `reference_nakshatra_padas` + `reference_nakshatra_matrices`. L0 `scope: global`,
`asset_type: data`, underscore id, ON-CONFLICT idempotency, deterministic cited constants (NOT LLM).
Additive L0 extension (a NEW global asset, like the panchanga service assets — not an L0 rebuild). Becomes
a dependency for ga_nakshatra. Flag the L0-reopen for native confirmation (it's additive, sealed-but-extensible).

---

## §3 — L1 `ga_nakshatra` (PER-CHART PARALLEL CHART — PyJHora-computed) [Tier 1]

Per ayanamsha (×5), per body (all 9 grahas + Lagna + nodes + key sensitive points). The depth L1 lacked.

### §3.1 — Placement + attribute join
Per body: nakshatra (name+number), pada, exact degree-within-nakshatra, % traversed; **JOIN bg_nakshatra
static attrs onto each body** (gana/nadi/yoni/varna/tatva/pakshi/deity/shakti/pada_navamsa/akshara —
REFERENCED from bg_nakshatra, never restated); nakshatra_lord + the lord's own placement (dignity/house —
the "nakshatra-lord condition").

### §3.2 — The PARALLEL NAKSHATRA CHART (the headline enrichment)
Treat "which nakshatra each body occupies" as a full chart:
- **Nakshatra dispositor graph** — each body's nakshatra-lord, chained to that lord's nakshatra-lord, to
  terminus/cycle. The graph IN NAKSHATRA SPACE, distinct from the rashi dispositor graph.
- **Nakshatra exchange (parivartana)** — two bodies in each other's nakshatra-lord's nakshatras.
- **Nakshatra conjunction** — bodies sharing a nakshatra (distinct from sign-conjunction).
- **Nakshatra center-of-gravity** — the body the most nakshatra-chains terminate on (the nakshatra-chart's
  functional king — a deterministic, novel "most consequential factor in nakshatra space").

### §3.3 — Sub-nakshatra precision (finest deterministic grain)
**KP 249 sub-lord → sub-sub-lord → (prana) chain** per body + per house cusp (the KP significator backbone —
currently absent). **Nadiamsa D150** nakshatra-level lord/deity per body (Nadi-prediction grain). Star-lord/
sub-lord/sub-sub for each.

### §3.4 — Degree-sensitive flags WITH SEVERITY (gradients, not booleans)
**Gaṇḍānta** flag + exact arc-minutes from junction (severity gradient). **Mṛtyu-bhāga** proximity per
planet (death-degrees). **Abhukta mūla**, **rashi-/nakshatra-/pada-sandhi** (three junction types) with
distance. **Pushkara navamsa/bhaga** (cross-link GA6, don't duplicate). **Deep-exaltation nakshatra-pada**
(each planet's exact exaltation point's nakshatra). **Vargottama-via-pada** (pada navamsa == D1 sign).

### §3.5 — Tara / cycle positions (chart-specific from the static cycle defs)
**Full per-chart Tara matrix** — each body's nakshatra's tara from every other body (not just transit-Moon
from natal-Moon; extend the GA4 27-row baseline). Position in each §2.6 cycle (Yogini-from-nak, Nadi-cycle,
sub-taras). **Sarvatobhadra-chakra occupancy** per body (vedha candidates — chakra static, occupancy per-chart).

### §3.6 — Chart-level nakshatra STATISTICS (within-chart deterministic — feeds L2)
Per the L2 design philosophy ([[feedback-l2-bodha-design-philosophy]]): gana distribution across all bodies,
nadi balance, yoni distribution, **tatva balance (the chart's elemental nakshatra signature)**, gana/nadi/
yoni concentration scores, **cross-ayanamsha nakshatra consistency** per body (5/5 vs flips at a boundary).
These are the nakshatra ingredients L2 turns into signals.

### §3.7 — L1 registration
`ga_nakshatra`, target `chart_facts` (or dedicated `ganita_nakshatra` — decide at build), L1 `scope:
per_chart`, underscore id, `@register('ga_nakshatra')` WriterBase conforming to the FROZEN orchestrator
contract (ctx.db_conn, never commit, per-ayanamsha sub-steps if heavy), L1 delete-then-insert idempotency,
count_sql + target_floor = achieved. `depends_on: ['bg_nakshatra', 'ga_positions']`. FORENSIC: native Moon
nakshatra = **Purva Bhadrapada** — assert; per-body nakshatras internally consistent with ga_positions.
Two-pass per row.

---

## §4 — L2 Bodha exploitation (DESIGN NOW, build with L2) [Tier 2]

Folds into the Bodha campaign; flag as EXTENSIONS to the locked A10–A14 specs for sign-off
([[feedback-l2-bodha-design-philosophy]] §13 rule):
- **Nakshatra MSR signal family** (`bo_laksana`): gana-balance, nadi-affliction, yoni-clash, gaṇḍānta-at-
  birth, KP-significator, Panchapakshi-state, deity-domain signals — ~doubles the signal vocabulary.
- **Nakshatra dispositor graph as a parallel CGM** (`bo_karanajala`/`bo_bimba`): compute the nakshatra-space
  graph alongside the rashi graph; **where the two graphs AGREE = high-weight corroboration; where they
  DIVERGE = first-class contradiction** (the parallel-witness payoff + the convergence/contradiction
  philosophy applied across two independent systems).
- **Nakshatra as a third convergence witness** (`bo_sangati`): when a rashi signal + a nakshatra signal +
  a KP-sub signal converge on one domain, the convergence-density is stronger than any one witness.

## §5 — L3/L4/L5 exploitation (SUBSTRATE captured now, built later) [Tier 3]
- **L3 Kāla — nakshatra timing engine:** transit-nakshatra activations, **Panchapakshi 5-bird daily
  windows** (the L0 bird-state tables + L1 chart-bird → L3 timing), Tara-bala-by-date, Sarvatobhadra-vedha
  timing, nakshatra-cycle dasha overlays.
- **L4 Phala — remediation:** deity/shakti/sound/**mantra → upaya** bridge (L0 §2.4/§2.5 → L4/`bo_upaya`):
  which mantras/deities for an afflicted nakshatra placement.
- **L5 Mīmāṃsā — research:** with the LEL, test which nakshatra factors (gana/nadi/yoni/KP-sub/Nadiamsa/
  parallel-graph-divergence) actually predicted lived events — held-out, deterministic-input/empirical-
  output. The under-studied predictor space the research-instrument goal points at.

## §6 — Build plan (tiered)
1. **Phase 1 — L0 `bg_nakshatra`** (Tier 1): author all §2 tables as deterministic cited constants (incl.
   matrices, sound, deity→domain, cycles, variants, cross-tradition maps); migration; register; build global.
2. **Phase 2 — L1 `ga_nakshatra`** (Tier 1): the §3 PyJHora writer incl. the parallel nakshatra chart +
   KP-249 + Nadiamsa + severity-gradient flags + per-chart statistics; orchestrator-native; build via the
   orchestrator for the native; FORENSIC-gate + cockpit-verify.
3. **Phase 3 — wire into L2** (Tier 2 design): add the nakshatra assets to the L2 data interface + fold the
   §4 signal/graph/witness extensions into the Bodha campaign (flagged for sign-off).
4. **Tier 3** stays substrate-captured (L0/L1) + designed (§5); built at L3/L4/L5.

## §7 — Standards + open decisions
Standards (inherited): deterministic-first (classical tables, no LLM); only-facts (gana IS a fact;
"rakshasa gana = aggressive" is NOT — that's serve-time); atomic grain (matrices as rows or sanctioned
JSONB, justified); two-pass; FORENSIC-gated; L0 ON-CONFLICT / L1 delete-then-insert idempotency; no
JH-parity (verify by internal-consistency + classical-table re-derivation); no tier; floors aspirational;
orchestrator-native; surgical migrations; **bg_nakshatra is the AUTHORITY for static attrs — ga_nakshatra
references, never restates.**

### §7.1 — Open decisions — ALL RESOLVED (native-ratified 2026-06-10; locked, do NOT re-ask at build)

1. **Abhijit** → 28th reference row with `tradition_scope` marker; included where the tradition uses it
   (muhurta/some longevity), EXCLUDED from the 27-fold dasha math. Exact span ~6°40′ around the
   Uttarashadha-end → Shravana-start junction (~Capricorn) — confirm the precise arc against the source.
2. **Yoni / kuta** → the FULL 36-guna Ashtakuta set (Varna, Vashya, Tara, Yoni, Graha-Maitri, Gana, Bhakoot,
   Nadi) — the complete kuta substrate, matching the deep-research depth of the product. Hold every kuta's
   table at L0 §2.3.
3. **ga_nakshatra storage → `chart_facts`** (NOT a dedicated table), AND it remains a SEPARATE asset
   (`ga_nakshatra`). Consistent with L2 retrieval. **BUILD-TIME WATCH:** the KP-249 chain (sub→sub-sub→prana)
   × all bodies × all cusps × 5 ayanamshas is potentially the largest single chart_facts contributor —
   MEASURE the row count + chart_facts query performance at build; if it's enormous, raise with native
   (revisit-conversation, not a silent problem). The decision stands; the measurement is a watch.
4. **KP depth → sub + sub-sub + prana, per-body AND per-cusp.** Full significator backbone.
5. **bg_nakshatra shape → 3-grain split** (per-nakshatra 27/28 + per-pada 108 + matrices), FK'd.
6. **Reopen L0 AND L1 → YES, both, ADDITIVE.** bg_nakshatra = a NEW L0 global asset (like the panchanga
   service assets); ga_nakshatra = a NEW L1 per-chart asset. Neither is a rebuild of sealed assets — both
   are additive extensions. (L0 ON-CONFLICT idempotency for bg_nakshatra; L1 delete-then-insert for ga_nakshatra.)
7. **Multi-tradition variants → SOURCED, and they BECOME PART OF `bg_texts`** (the classical-texts corpus),
   NOT a standalone variant store. So every variant attribute carries `tradition_scope` + a CITATION into
   bg_texts — grounded, auditable, and inheriting the existing retrieval/grounding machinery. **Sourcing:
   FIRST check what nakshatra-coverage texts are ALREADY indexed in bg_texts; source-gap only what's missing.
   Recommended comprehensive sources for full attribute coverage: a comprehensive Nakṣatra compendium
   (attribute tables: gana/nadi/yoni/varna/tatva/pakshi/shakti), Muhūrta Cintāmaṇi / Kālaprakāśikā (muhurta
   classifications + Abhijit), and the Nadi corpus already partly in bg_texts (Nadiamsa + variant assignments).
   Confirm exact editions at build; add to bg_texts via the existing l0_texts ingestion path.**
8. **Nadiamsa D150 → ALREADY COMPUTED as a varga; ga_nakshatra REFERENCES it, does NOT recompute.** A6
   includes D150 in the 30-varga set, so `ga_vargas`/`chart_divisionals` already holds each body's D150
   (Nadiamsa) SIGN. ga_nakshatra's job is to ADD the nakshatra-level Nadiamsa ATTRIBUTION (lord/deity/rishi
   per the 150-fold subdivision) ON TOP of the existing D150 position — cross-referencing ga_vargas, never
   re-deriving the position (the L1-is-authority discipline applied internally). **BUILD STEP:** verify what
   D150 detail ga_vargas already emits; build ONLY the nakshatra-attribution gap, citing the ga_vargas D150 row.

---

*End. The Nakshatra Subsystem: a first-class parallel framework across L0–L5 — a fully-enriched global
reference, a per-chart parallel nakshatra chart with its own dispositor graph, a nakshatra signal/graph
witness in L2, a timing engine in L3, remediation in L4, and a research substrate in L5. Build L0+L1 now
(maximal), design L2+, capture-everything-deterministic-now because the chart can't be re-observed later.*
