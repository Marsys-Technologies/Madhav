---
artifact: SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md
canonical_id: SUBSYSTEM_PROGRAM_ROADMAP
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — native-ratified 7-subsystem program
authored_for: the multi-subsystem build program (Cowork plans → Claude Code in Antigravity executes)
purpose: >
  Tie SEVEN cross-cutting subsystems into one dependency-ordered program, each embedded via the
  subsystem-embedding pattern (audit → reframe → static-vs-computed split → full L0–L5 map → tiered build →
  converge into existing layers → inherit standards → resolve decisions). Nakshatra (already in build) is #1;
  six new ones join it. Defines waves, dependencies, the on-demand transit architecture, and the build
  discipline (design now, build wave-by-wave, AFTER the current L2/nakshatra/L1-close queue is validated).
read_in_combination_with:
  - feedback-subsystem-embedding-pattern (memory — the 8-step method every subsystem follows)
  - NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md (the worked template — subsystem #1)
  - L2_BODHA_CAMPAIGN_HANDOFF + feedback-l2-bodha-design-philosophy (the L2 convergence engine all subsystems feed)
  - ORCHESTRATOR_CONVERGENCE_CLOSE (the frozen contract every new writer conforms to)
governing_discipline: >
  DESIGN all 7 now (cheap; captures the vision). BUILD strictly wave-by-wave, each fully validated before
  the next. Do NOT begin any subsystem build until the current designed-but-unbuilt queue (L2 Bodha,
  nakshatra bg_/ga_, L1 Phase-5 close) is built + prod-validated. The session-long risk is design outrunning
  validated build — this program multiplies it; the wave-gate is the control.
---

# Subsystem Program Roadmap — 7 Subsystems (L0–L5) v1.0

## §0 — The program + the unifying architectural key

Seven cross-cutting subsystems, each a first-class framework threaded through L0–L5, each embedded via the
[[feedback-subsystem-embedding-pattern]]. The unifying key that governs all seven (and resolves transit):

**Three data categories, not two:**
- **STATIC rules/attributes → L0 reference** (chart-agnostic; ON-CONFLICT idempotent; computed once).
- **CHART-SPECIFIC natal anchors → L1 per-chart** (PyJHora; delete-then-insert; the chart's facts).
- **TIME-VARYING / combinatorially-infinite → an L0 SERVICE (compute on demand), NOT a stored asset** —
  exactly how `bg_panchanga` already works (a deterministic engine with APIs, nothing stored across time).
  Transit positions, prashna-moment charts, "when does rule R fire for chart C" all live here.

**The rule, the principle for the whole program:** store the deterministic RULES + the natal ANCHORS;
compute the time-varying POSITIONS on demand via a service; let L2/L3 ask the service at query time. The
instrument stays small; the infinite spaces (all-time transits, any-moment prashna) stay computable. This is
the architectural insight that makes a "transit subsystem" feasible without hard-coding billions of rows.

## §0.5 — THE ENRICHMENT STANDARD (governs ALL seven — native-ratified 2026-06-10)

**No subsystem ships thin. Each is built to the FULL classical depth of its tradition — every concept,
every variant, every computable relationship — so the deterministic data is maximally dense and the LLM has
a complete substrate to synthesize from holistically.** The bar: an acharya of that specialty reviewing the
subsystem would say "you've captured everything computable in this system." Depth WITHIN each subsystem
(maximal), not just breadth across them.

**The HARD GATE that keeps "maximal" from becoming fabrication (non-negotiable):**
> **A data point is STORED only if it is (a) deterministically COMPUTED and (b) CITABLE to a classical
> source. Everything else is serve-time interpretation, never stored as fact.**

So "maximal enrichment" = **exhaust the computable-AND-citable space** of each tradition — NOT generate
plausible-sounding content. If a yoga has a strength formula in Phaladeepika → compute + store it. If a
"yoga interpretation" is acharya intuition with no formula → it's serve-time, NOT a stored row. This is the
floors-aspirational + no-fabrication discipline ([[feedback-floors-are-aspirational-not-gates]],
[[feedback-deterministic-first-for-data-build]]) applied as the enrichment ceiling: chase the maximum
GENUINE deterministic+cited data; never fabricate; an uncited value is worse than a missing one (floor it
null+marked). The citation requirement is precisely what lets the project go maximal without losing the
research-grade integrity / contamination guardrail ([[MSR contamination audit]]).

**How it's encoded (decision: maximal scope in the plan, NO separate manifest artifact):** each subsystem's
master plan is WRITTEN to maximal depth — it enumerates the tradition's full concept-set inline (like the
Nakshatra plan's §2/§3 exhaustive lists), each concept marked computed/captured or justified as
non-deterministic-→-serve-time. The thoroughness lives in the plan itself; no separate checklist file. The
Nakshatra subsystem is the depth TEMPLATE: every other subsystem matches that level of inline completeness.

**Per-subsystem "fully enriched" means (the depth bar, not exhaustive):**
- **Yoga:** every yoga from every source (BPHS + Saravali + Phaladeepika + Jataka Parijata + Brihat Jataka +
  300-combinations + Nabhasa/Sankhya/Aakriti geometric yogas), each with strength-gradient, ALL
  formation+cancellation+bhanga rules, partial-formation flags, activating-dasha windows, constituent
  decomposition, yoga-on-yoga interactions — all where a formula+citation exists.
- **Dignity/Avastha:** all avastha schemes + sub-states, dignity across ALL 16+ vargas, sambandha (4 types),
  graha-yuddha, all combustion gradients, all 8 motion-states, full shadbala-as-condition, vimsopaka all
  varga-groups, condition trajectory through every dasha level.
- **Transit:** every transit-significance rule — Vedha, **Ashtakavarga-Kakshya bindu-gated transit** (deepest
  lens), Moorti nirnaya, from-Moon AND from-Lagna, special transits (Kantaka/Ashtama/Janma) for EVERY planet,
  Sade-Sati-equivalents for Jupiter/Rahu, station sensitivity, transit-to-every-sensitive-point — all via the
  on-demand service.
- **Medical:** every graha→dosha/dhatu(7)/body-system, sign/nakshatra/drekkana/D6→body-part, house→health,
  all Arishta/disease yogas, dosha-imbalance computation (tiered: indications-not-diagnosis + disclaimer).
- **Astrovastu:** all 16 directions + 45-devata Vastu-Purusha mandala + marma points + weak-planet→direction→
  remedy join (maximal for its genuinely-thinner deterministic scope; real content tiered in bo_upaya).
- **Prashna:** all Prashna-Lagna methods (Tajik/KP-249/Brihat/Aarudha/Swara), the full horary rule-set
  (Ithasala/Eesarpha/Nakta/Kambula etc. on the prashna chart), querent/quesited significators across methods,
  fructification timing, Nashta-jataka, + full reuse of every other subsystem on the prashna chart.
- **Nakshatra:** already the maximal template (parallel chart + 36-guna + KP-249 + Nadiamsa + Panchapakshi +
  shakti + deity-domain + cross-tradition maps).

## §1 — The seven subsystems + dependency waves

| # | Subsystem | What it is | Build wave | Depends on |
|---|---|---|---|---|
| 1 | **Nakshatra** | parallel nakshatra chart | **W0 (in build)** | — |
| 2 | **Yoga** | yoga catalog → yoga SYSTEM (families, interactions, activation) | **W1** | existing yoga data |
| 3 | **Dignity / Avastha** | unified planetary-CONDITION + how it changes through dasha/transit | **W1** | existing strength/avastha |
| 4 | **Transit / Gochara** | the on-demand transit SERVICE + rules (the missing half of prediction) | **W2** | Yoga, Dignity, panchanga-service pattern |
| 5 | **Medical / Ayurvedic** | graha→dosha→body deterministic mapping + condition | **W3** | Dignity, Nakshatra |
| 6 | **Astrovastu** | directional reference + remedial tradition | **W3** | Dignity, RM (bo_upaya) |
| 7 | **Prashna (Horary)** | a chart-TYPE (question-moment) + horary rule layer, reusing all above | **W4** | ALL above + chart-creation plumbing |

**Why this order:** Yoga + Dignity are pure leverage over existing data, lowest risk, and FEED the others
(transit-activated yogas; transit-planet condition; medical planetary condition). Transit needs them + the
service pattern. Medical + Astrovastu reuse Dignity (+ Nakshatra body-parts). Prashna reuses EVERYTHING and
is mostly plumbing — last by construction.

---

## §2 — Subsystem 2: YOGA (Wave 1) — leverage, not new computation

**Reframe:** today yogas are a flat CATALOG (250+ in bg_yogas) + flat FIRINGS (A8 yoga_fires). The subsystem
turns it into a STRUCTURED system.
- **L0** (extend bg_yogas): yoga FAMILY taxonomy (Mahapurusha/Raja/Dhana/Nabhasa/Arishta/Sannyasa/…),
  yoga-interaction rules (which strengthens/cancels which beyond simple cancellation), classical citations.
- **L1** (extend ga_structural OR a thin ga_yoga): per-chart yoga firing already exists — ADD: yoga STRENGTH
  as a deterministic gradient (constituents' shadbala/dignity/varga across all D-charts), yoga ACTIVATION
  windows (when each fired yoga's lords run their dasha — joins ga_dashas), yoga-family membership per firing.
- **L2** (extend bo_laksana/bo_karanajala): yoga signals + yoga-CONVERGENCE (multiple yogas on one domain =
  weight of evidence) + yoga-interaction edges in the graph. Flag as A10–A14 extension for sign-off.
- Value: highest value-per-effort; pure leverage; feeds every other subsystem's "is there a yoga here" question.

## §3 — Subsystem 3: DIGNITY / AVASTHA / PLANETARY CONDITION (Wave 1) — the condition substrate

**Reframe:** dignity data is scattered (varga dignity A6, avasthas A8, combustion/retro A1). Unify into ONE
deterministic "how is this planet doing, and when."
- **L0**: the dignity/avastha reference tables (exaltation/debilitation/moolatrikona/own degrees, the 5 avastha
  scheme definitions, combustion orbs) — mostly exists; consolidate + cite.
- **L1** (ga_condition): per graha, a UNIFIED condition composite (dignity × avastha × combustion × retro ×
  shadbala × varga-dignity-spread) as a single versioned-formula score; PLUS the condition TRAJECTORY — how
  it changes across the dasha timeline (a planet weak natally but strong in its own dasha) and under transit
  (references the W2 transit service). Versioned formula (condition_formula_v1).
- **L2**: condition signals + condition as a node-weight in the graph (a strong-condition planet's signals
  carry more salience).
- Value: answers the holistic "planetary condition" question no single asset does; substrate for Transit
  (transit value depends on transiting planet's condition) and Medical (planet condition → body condition).

## §4 — Subsystem 4: TRANSIT / GOCHARA (Wave 2) — the on-demand service (native's architecture)

**THE architecture (native-specified, non-negotiable): DO NOT hard-code transit positions across time.** It's
infinite + trivially recomputable. Instead:
- **L0 transit SERVICE (`bg_transit_engine`, like bg_panchanga):** deterministic APIs, compute on demand from
  ephemeris/PyJHora — `transit_positions_at(instant)`, `transit_aspects_to(chart_id, instant)`,
  `next_transit_event(chart_id, rule, from_date)`. NOTHING stored across time.
- **L0 transit RULES reference (`bg_transit_rules`):** which transits matter (Sade-Sati rule, Kantaka/Ashtama,
  Jupiter-return, the Vedha/obstruction transit rules, the **Ashtakavarga transit-strength / Kakshya** gates —
  a classical transit lens currently absent), all as STATIC deterministic rules.
- **L1 natal ANCHORS (`ga_transit_anchors`):** the chart's natal points/sensitive-points/sign-lords the
  transit rules fire against — stored once per chart (small). NOT positions over time.
- **L2** (extend bo_laksana): transit SIGNALS computed at query time via the service ("Saturn currently
  transiting your natal Moon = Sade Sati active") — the rule + anchor are stored, the DATE is computed live.
- **L3 Kāla — the timing engine:** this is where it pays off. `next_transit_event` + the rules + anchors =
  a deterministic timing fabric answering "when does X activate for this chart," computed on demand, infinite
  range. The missing half of prediction; makes the instrument TESTABLE against lived events (the research thesis).
- Value: the highest-ceiling subsystem; the genuinely-novel architecture (service-not-storage); the timing
  half the instrument currently lacks.

## §5 — Subsystem 5: MEDICAL / AYURVEDIC JYOTISH (Wave 3)

**Reframe:** today minimal (graha-constitution pairings in RM). Build the deterministic medical mapping.
- **L0 (`bg_medical_mappings`):** graha → dosha (Vata/Pitta/Kapha), graha → body-system/organ, sign → body-part
  (Kalapurusha — partly exists), nakshatra → body-part (REUSES nakshatra subsystem), house → health-domain,
  tatva → bodily element. All deterministic classical mappings, cited.
- **L1 (`ga_medical`):** per chart — the chart's dosha-balance (Vata/Pitta/Kapha from graha placements +
  REUSES ga_condition for planetary strength → bodily-system strength), afflicted body-parts (malefic on
  6th/8th + the body-part mappings), medical-yoga firings (REUSES the Yoga subsystem — Arishta/disease yogas).
- **L2**: health-domain signals feeding bo_sangati's health domain. **EPISTEMIC TIER: clearly flagged as
  classical-Jyotish health INDICATIONS, NOT medical diagnosis** — the documented-approximation tier + a strong
  not-medical-advice disclaimer (the project's user-wellbeing + ethical-framework discipline).
- Value: a real under-served domain; mostly deterministic mappings; heavy reuse of Dignity + Nakshatra + Yoga.

## §6 — Subsystem 6: ASTROVASTU (Wave 3) — a remedial tradition, NOT a deep subsystem

**Honest placement (per the prior analysis): Astrovastu's deterministic content is THIN; its value is
remedial + space-dependent. Build it small, in the right home.**
- **L0 (`bg_vastu_directions`):** the 16-direction → planet → element → life-domain → deity mapping + the
  Vastu-Purusha mandala grid — deterministic, cited, and useful beyond Astrovastu (Dik Bala / Disha Shul /
  directional strength touch the same data).
- **L1 (thin — a derived view, not a heavy writer):** "your weak planets (REUSE ga_condition) → their
  associated directions" — a JOIN, almost no new computation.
- **L4 / `bo_upaya` (where the real content lives):** Astrovastu directional remedies become a TRADITION
  within the existing 6-tradition × 18-category remedy matrix. **EPISTEMIC TIER: a remedial recommendation
  cited to its source, clearly flagged as the Astrovastu tradition's suggestion — NOT a deterministic fact**
  (the contamination guardrail; Vastu remedies don't fit the falsifiable-prediction frame, so they're tiered
  out of the deterministic base).
- Value: real product/remedial value; small build; correct architectural home (a remedial tradition, you
  already have a remedial subsystem). Do NOT build it as a standalone L0–L5 subsystem — it has no deterministic
  substance in the middle layers to justify that shape.

## §7 — Subsystem 7: PRASHNA / HORARY (Wave 4) — a chart-TYPE that reuses everything

**Reframe (native chose full subsystem design): Prashna is a NEW CHART-TYPE (the moment-of-question chart)
that runs through ALL existing subsystems + a thin Prashna-specific rule layer. The value is in REUSE; the
build is mostly an entry-point + horary rules.**
- **Chart-creation plumbing (the real architectural work):** a second chart-creation path — cast a chart for
  the question-INSTANT (lat/lon = querent's location). This reuses the ENTIRE existing pipeline (positions,
  vargas, dashas, nakshatra, yoga, dignity, transit) — a prashna chart IS a chart. The plumbing: a
  `prashna_charts` entry alongside `charts`, with question-metadata (the question, the moment, the querent).
- **L0 (`bg_prashna_rules`):** the horary-specific rule layer — Prashna Lagna derivation methods (Tajik/KP/
  Krishnamurti number, Brihat Prashna), the special horary judgment rules (Ithasala/Eesarpha = "will it
  happen"; the querent vs quesited significator derivation; the "fructification" timing rules), Ārūḍha/Lagna-
  based prashna methods. Static, cited.
- **L1 (`ga_prashna`):** per prashna-chart — the querent/quesited significators (which houses/planets
  represent the question's subject), the Ithasala/Eesarpha between them (will it happen?), the fructification
  window (when?), the prashna-specific yogas. REUSES every other subsystem's computation on the prashna chart.
- **L2**: prashna signals → a focused "answer the question" synthesis (the one place where pre-answering IS
  appropriate, because a prashna chart exists to answer ONE question).
- **EPISTEMIC NOTE:** prashna is a distinct *method*; its outputs are time-bound to the question-moment, not
  natal facts. Keep prashna outputs in their own namespace, never mixed with the natal chart's facts.
- Value: a complete second mode of the instrument (event/question astrology), high reuse, but real plumbing
  (the question-chart entry point) — hence last.

## §8 — Build discipline + STRATEGY (native-ratified 2026-06-10 — the governing decisions)

**THE BUILD STRATEGY IS SUBSYSTEM-BY-SUBSYSTEM ACROSS ALL LAYERS, then CLOSE EACH LAYER ONCE AT THE END.**
NOT layer-by-layer-close-as-you-go. Rationale (native): a layer cannot VALIDLY close until everything that
belongs in it exists — L0 is missing subsystem reference data, L1 is missing per-chart subsystem computation,
L2 Bodha CANNOT close because its assets depend on subsystem data not yet built. So closing "L1 Phase 5" now
is MEANINGLESS — it would seal a layer about to be reopened 7×. The earlier L1 "seals" were the premature
ones; this strategy REFUSES to false-seal. Build all 7 subsystems embedded into every layer they touch, THEN
close L0 once → L1 once → and only then L2 Bodha can close (its inputs finally exist). This is mechanically
clean BECAUSE the orchestrator is FROZEN + metadata-driven — adding dozens of subsystem assets across the
plane needs ZERO orchestrator change (each is @register + registry metadata; layers stay DRAFT/open until
the final seal).

**DECISION 1 — VALIDATE-AS-YOU-GO (the guardrail inside the strategy):** each SUBSYSTEM is individually
validated when its assets land (writers build clean, FORENSIC-gated where applicable, cockpit-lit, idempotent)
— even though the LAYER stays open/DRAFT. Validate the subsystem CONTINUOUSLY; seal the layer ONCE at the
end. This keeps the "close once" elegance WITHOUT piling all validation onto the final close (which would be
the seal-vs-reality chasm at maximum scale). Subsystem-level proof as you go; layer-level seal at the end.

**DECISION 2 — DESIGN ALL 7 MAXIMAL MASTER PLANS FIRST, then build the whole program.** Author the complete
design picture (7 maximal master plans, Nakshatra-depth, decisions-resolved-upfront) BEFORE executing any
build. Nakshatra's master plan exists; author the other 6 (Yoga, Dignity, Transit, Medical, Astrovastu,
Prashna). Then execute the build program in dependency-wave order.

**DECISION 3 — NAKSHATRA FOLDS IN as subsystem #1 of 7** (no longer a separate two-asset build; its bg_/ga_
briefs build as W0 within the program). The L1 "Phase 5 E2E close" is SUPERSEDED — L1 closes once, at the end,
after all subsystems embed. The Abhinandan teardown is a disposable TEST runtime (deleted later; the real
end-to-end build runs on the FINISHED enhanced system) — not a closure dependency.

**Wave order (build phase, after all 7 plans authored):** W0 Nakshatra → W1 Yoga + Dignity (leverage-first,
feed others) → W2 Transit (on-demand service) → W3 Medical + Astrovastu → W4 Prashna. Each subsystem fully
built + subsystem-validated before the next; LAYERS sealed once at the very end (L0 → L1 → L2 Bodha).
4. **Every subsystem follows the 8-step pattern** + inherits ALL standards (orchestrator-native @register,
   underscore ids, deterministic-first, floors-aspirational, no-JH-parity, no-tier, two-pass, FORENSIC-gated,
   surgical migrations, L0 ON-CONFLICT / L1 delete-then-insert idempotency) + the epistemic tiering
   (deterministic-fact vs documented-approximation vs remedial-tradition).
5. **The three SERVICES** (panchanga exists; transit + prashna-chart-cast are new) follow the L0-service
   pattern (compute on demand, APIs, nothing stored across time) — NOT stored assets.

## §9 — Per-subsystem decision sets (resolve at each wave's master-plan time, like nakshatra's §7.1)
Each subsystem gets its own master plan with an upfront "decisions RESOLVED" section before briefs. Known
open questions per subsystem are listed in each §2–§7 above (e.g. Transit: which Ashtakavarga-transit method;
Medical: how strong the not-diagnosis disclaimer; Prashna: which Prashna-Lagna method is primary).

---

*End. Seven subsystems, one dependency-ordered program: Nakshatra (in build) → Yoga + Dignity → Transit
(on-demand service) → Medical + Astrovastu → Prashna (chart-type). Each embedded via the proven pattern; the
static-rules-vs-on-demand-service split makes infinite spaces (all-time transits, any-moment prashna)
computable without hard-coding. Design now; build wave-by-wave; gate behind the current queue's validation.*
