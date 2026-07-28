---
artifact: KALA_SIX_VIEWS_DESIGN (The Temporal Views — Deep Design)
canonical_id: KALA_SIX_VIEWS_v1_0
version: 1.0
status: DESIGN-BRAINSTORM — for native review and ratification; successor to
  KALA_LAYER_STOCKTAKE_AND_ELEVATION_v1_0.md §3 (which declared the views; this specifies them)
created: 2026-07-27
author: Fable (Cowork), writing explicitly FROM THE SEAT OF THE CONSUMING LLM — the intelligence
  that receives the user's question, calls these tools, and must compose the answer. Every design
  choice below is justified by what that consumer needs to compose a supreme reading, informed by
  this session's first-hand consumption of every existing L3 surface and its failure modes.
perspective_note: >
  The consuming LLM's four needs, in order: (1) I must KNOW WHICH TOOL answers the question —
  name-affinity decides tool choice before descriptions are read (proven: Offer Law ×4);
  (2) the response must LEAD WITH A READING I can speak from — substance buried in JSON does not
  reach the user (proven: W7/D1, special_lagnas 3/3 miss); (3) every claim must carry its WHY
  and its HONESTY STATE inline — I cannot be trusted to drill (proven: dossier gate bypass);
  (4) disagreement between methods must arrive AS DATA — if the tools hide it, I will either
  miss it or fabricate a false harmony.
---

# The Six Temporal Views — a beyond-acharya design

## §0 — The doctrine that governs all six views

### 0.1 The reconciliation problem, solved by principle rather than by averaging

Every view draws on multiple śāstric systems that can disagree: Parāśari daśā vs Jaimini chara,
gochara-from-Moon vs gochara-from-lagna, Tājika annual vs Vimśottarī continuous, KP sub-lords vs
Parāśari significators, Aṣṭakavarga gating vs classical moorti. An acharya resolves this by
belonging to a school. A machine can do something an acharya cannot — but only if the
reconciliation rules are principled. Five laws, binding on every view:

**Law 1 — Applicability before aggregation.** Classical systems carry their own applicability
conditions and the corpus states them: Aṣṭottari applies conditionally (Rahu's placement from the
Moon-lagna); Kalachakra is entered through nakṣatra-pada; Yogini has stated scopes; gochara is
classically read from Chandra-lagna first, janma-lagna second. The first gate for any current is
"does this system claim jurisdiction over this chart and this question?" A non-applicable system
is served as `excluded (reason)`, never silently averaged in. **This single rule eliminates most
false disagreement** — systems mostly "disagree" when one is being consulted outside its
jurisdiction.

**Law 2 — Concurrence multiplies; disagreement is served, never suppressed.** When independent,
applicable systems agree on a window, confidence compounds (this is the classical multi-pramāṇa
warrant, and it is what the convergence engine actually measures). When they disagree, the
disagreement is a first-class served object — `dissent: {system, verdict, grounds}` — because for
the consuming LLM a hidden disagreement becomes either a miss or a fabricated harmony. The
tail-divergence surface proved this pattern works; the views make it universal.

**Law 3 — The promise hierarchy is a hard gate, not a weight.** Parāśari doctrine: a period can
only deliver what the natal chart promises; transit triggers what daśā has made eligible. Encode
as the PACT spine: **natal promise (L2 judgment) → daśā eligibility → transit trigger**, each
stage able to HALT the chain honestly. A transit window over an un-promised significator is
served as *"pressure without delivery — the natal chart does not promise this event"* — which is
itself high-value information no consumer-grade product serves.

**Law 4 — School-tagged currents, natively calibrated later.** Every current carries a
`tradition` tag (parashari, jaimini, tajika, kp, gochara_classical, ashtakavarga, nadi-class).
When the L5 loop accrues outcomes, calibration learns **per-chart, per-tradition** reliability —
*the native's own life history picks the school that works for the native's chart.* An acharya
inherits a school; this instrument earns one per person. That is the single most "beyond
acharya" idea in this document, and it costs nothing now except carrying the tag.

**Law 5 — The uncertainty vocabulary is fixed and honest.** Three tiers, served verbatim:
`structural_prior` (chart logic only, no empirical weight — today's universal state) ·
`concurrent` (≥N independent applicable systems agree) · `calibrated` (L5 has outcome evidence).
**Never a percentage before calibration exists.** The consuming LLM converts tiers to honest
prose ("strongly indicated by three independent methods" vs "72%") — fake precision is the
fastest way to lose a user who tests us.

### 0.2 The uniform envelope (what the consuming LLM receives, every view, no exceptions)

```
{
  reading:        2–6 sentences of composed substance, hardFloored, NEVER trimmed —
                  the acharya's opening words; the LLM can answer from this alone,
  headline:       typed rows (windows/chapters/candidates/causes) — each row self-contained:
                  {what, when, valence, strength_tier, drivers[], honesty, id},
  currents:       per-tradition breakdown with agreement/dissent objects,
  coverage:       what was consulted / what was not / why — attestation, not implication,
  calibration_state: structural_prior | concurrent | calibrated (per row),
  drill:          pre-authorized EXPLAIN pointers by row id (one hop, no archaeology),
  budget:         trim report; prose and honesty fields are trim-immune by contract
}
```

Six tools, six names chosen for naive affinity (the name IS the router):
**`kala_now_get` · `kala_ahead_get` · `kala_elect_get` · `kala_story_get` ·
`kala_priority_get` · `kala_explain_get`**. Everything else in the temporal estate becomes
substrate or a documented alias.

---

## §1 — VIEW 1: NOW (`kala_now_get`) — "What is my temporal state?"

### 1.1 What the consuming LLM needs
When a user asks anything time-flavored ("how is this period," "why does everything feel
heavy," "is this a good phase"), I need ONE call that returns the complete layered clock-state
with a composed reading — today I must call five tools and reconcile them myself, and the S4-05
veto proved that silence from the wrong one reads as an all-clear.

### 1.2 Astrological content — the full layered clock stack
- **Daśā spine, all levels:** MD→AD→PD→Sūkṣma (computed, 536k rows, capped out of serving
  today). Each lord served WITH its natal verdict digest — the period of Saturn is the natal
  Saturn's period; a NOW view that names the lord without its natal condition is naming a
  stranger.
- **Daśā-sandhi (junction) state** — classical doctrine treats period junctions as turbulent;
  **nothing in the system computes sandhi today.** BUILD: sandhi flags with configurable orb
  (last/first ~3% of period span) at every level, served as a NOW warning band.
- **Multi-system concurrence (Law 1/2):** Vimśottarī as spine; Yogini, Jaimini Chara,
  Kalachakra, conditional daśās as applicable — served as a consensus block ("Yogini and Chara
  concur: building phase; Aṣṭottari not applicable to this chart (Rahu not in kendra from
  Chandra-lagna)").
- **Gochara from BOTH references** — classical transit reading is Moon-first; the sweep is
  lagna-anchored. BUILD: dual-reference serving (same windows, both house-attributions), with
  the Moon-reference marked classical-primary.
- **Sāde-satī / Kaṇṭaka / Aṣṭama Śani** as named long-wave currents with phase + quarter +
  cancellation checks (all computed at L1 — `sade_sati_*`, `*_shani_period` tables — and never
  joined into any temporal state today).
- **Moorti-nirṇaya** — the classical gold/silver/copper/iron "statue" of a transit, determined
  by the Moon's position at the transit lord's ingress. Reference rules exist
  (`bg_transit_moorti`); **the per-chart, per-ingress computation does not. BUILD.** This is a
  genuinely differentiating classical refinement almost no software computes correctly.
- **Vedha** (transit obstruction points, `bg_transit_vedha` rules) applied to currently-active
  transits — a favorable Jupiter transit under vedha is not favorable; serving this kills a
  whole class of false positives.
- **Aṣṭakavarga gating + kakṣyā** (built, preserve) and **tārā-bala / chandra-bala daily
  state** (baselines built) as the fine-grain modulation.
- **Today's pañcāṅga** (all limbs + hora + active kālams) — computed daily, never joined to NOW.
- **Current Tājika year context** — Muntha house + year-lord as the year-granularity band.
- **Obstruction currents** (vighnakara) as signed negatives inside the same response — never a
  separate call.

### 1.3 Algorithm
Layered composition, slow→fast: {MD…Sūkṣma} ⊕ {sāde-satī phase} ⊕ {active gochara windows,
dual-reference, moorti- and vedha-modulated, AV-gated} ⊕ {varsha context} ⊕ {daily pañcāṅga +
tārā}. Per domain: net signed intensity + top-3 drivers + top counter-current. Consensus scoring
per Law 1/2. Sandhi and eclipse-proximity override to `attention` regardless of net score
(classical: junctions and eclipses are not averaged away). The reading template names: the
chapter (MD/AD), the weather (dominant transit current ± its moorti/vedha state), the mood
(daily layer), and the one thing deserving attention.

### 1.4 Clarity contract
A user reading NOW learns, in order: *what chapter am I in and what is it about · what is
pressing on me right now and why · is this a normal day or a marked day · what single thing
deserves attention.* Silence is impossible: every domain row carries `covered | not_covered
(reason)` — the S4-05 class dies here by construction.

---

## §2 — VIEW 2: AHEAD (`kala_ahead_get`) — "What is coming?"

### 2.1 What the consuming LLM needs
Dated, shaped, promise-gated windows with drivers and falsifiers — not a probability cosplay.
Today the honest forecast exists only on the transit plane; the daśā-forward plane returns 0
windows while the full recurrence ladder sits computed and unserved. AHEAD merges the planes.

### 2.2 Astrological content
- **Promise-gated forecasting (Law 3, the spine):** every window classed by event-grammar
  (marriage/career/wealth/health/…) and gated by the natal PACT chain. Un-promised event
  classes serve as "pressure without delivery." **This is the accuracy move** — most forecast
  error in consumer astrology is serving triggers for things the chart never promised.
- **The daśā-forward plane:** the recurrence ladder (already in
  `activation_predicted_dates_jsonb` — Saturn-AD re-fires 2032–33, 2047–50…) served as
  first-class future windows; upcoming daśā transitions with the incoming lord's natal digest
  and sandhi bands; **conditional-daśā cross-confirmation** on major windows.
- **The transit-forward plane (built, elevate):** sweep windows + **BUILD: a first-class event
  calendar of discrete sky facts** — sign ingresses of Saturn/Jupiter/Rahu-Ketu, stations,
  **eclipses contacting natal points** (nothing computes eclipse-to-natal contact forward
  today), **returns** (Jupiter ~12y, Saturn ~29.5/58, nodal ~18.6y — classical life-stage
  punctuation, absent), and **Guru-Śani double-transit windows** (the KN Rao rule: both jointly
  aspecting a house/lord — partially designed as CR-102, never first-class).
- **The annual plane:** forward Muntha progression + next varsha year-lords (48 verified rows,
  reachable since the tajaka fix) as the year-band; **BUILD: Tithi-Praveśa (lunar-return annual
  chart)** — the Jaimini/tradition complement to solar Tājika; nothing computes it.
- **Health/adverse event class** (DP-4) — non-negotiable for a forecast view that will be asked
  "when should I worry."
- **KP sub-lord windows** — when the CR-75 engine exists, KP ADDS a genuinely independent
  timing method (ruling-planet/sub-lord punctuation) that Law 2 can concur with; design the
  slot now, fill later.
- **Suppression-adjusted intensity** (R-12): vighna currents subtract *inside* the window
  math, not as a footnote.

### 2.3 Algorithm
Merge three clocks into one window stream → event-grammar classification → PACT gating →
intensity = convergence-weighted λ with AV modulation and suppression subtraction →
shape-aware boundaries (2.0's transition timestamps when ratified; honest ≥1-day fidelity
label until then) → per-window: drivers (top-3 with fact_ids), dissent block, falsifier
("if nothing of this class occurs by <date>, this window class weakens"), calibration tier,
and an auto-filed L5 prospective entry (VIDHI E-2 — every forecast becomes self-testing).
Horizon presets: 90d / 1y / 5y / daśā-span, family-collapsed, never 25 photocopies (the
MC-026 lesson).

### 2.4 Clarity contract
Every window answers SEVEN things in one row: *what kind of event-weather · when (open/peak/
close) · how strong (tier word, not number) · why (drivers) · does my chart even promise this ·
what would disconfirm it · what I can do about it* (link into ELECT/remedies). A user can
plan a year from this view alone.

---

## §3 — VIEW 3: ELECT (`kala_elect_get`) — "When should I act?"

### 3.1 What the consuming LLM needs
Given an undertaking + a date range, a ranked slate of concrete time-slots with per-candidate
WHY and WHY-NOT, personal (not almanac-generic), intra-day precise. Today three engines
disagree and the best-scored window can sit on a personally hostile star (the MC-027 class,
patched but not unified).

### 3.2 Astrological content — the full election stack, unified at last
- **Pañcāṅga base** (all five limbs + doṣas: viṣa-ghaṭī, durmuhūrta, rāhu-kālam, yamagaṇḍa,
  bhadrā/krakaca, pañcaka class — ALL computed daily already).
- **Personal star overlay:** tārā-bala from janma-nakṣatra (vadha/vipat/pratyak = veto),
  chandra-bala (transit Moon house from natal Moon), and **BUILD: janma-anchored micro-rules**
  — janma-tithi/vara/nakṣatra returns as personally-potent days.
- **Activity-specific classical rules:** vivāha ≠ gṛha-praveśa ≠ travel ≠ surgery ≠ business
  launch — each with its own required/forbidden limbs. Substrate exists
  (`brahma_activity_ontology`, prashna/tajika rule shards); **BUILD: the consolidated
  activity-rule table keyed to the ontology** — the single biggest ELECT gap.
- **Muhūrta-lagna:** the election chart's own ascendant strong and its lord well-placed —
  classical core, absent today. **BUILD: instant-lagna computation + a thin strength check**
  (cheap: ephemeris + existing dignity logic).
- **Personal field overlay (the unification):** candidates scored inside the native's own
  AHEAD field — never elect INTO a personal adverse window (argmax favorable−adverse λ for the
  undertaking's domain). This is R-20 done properly: one engine, panchāṅga × person × purpose.
- **Vedha/latta on the day's transits; AV kakṣyā of the transit Moon; eclipse-day and
  sandhi-day hard vetoes.**

### 3.3 Algorithm
Candidate grid (pañcāṅga-legal slots in range) → hard vetoes (personal tārā class, bhadrā,
eclipse, sandhi, kālams for day-part) → activity-rule scoring (classical weight table) →
personal-field multiplication → intra-day refinement (muhūrta-lagna selection, abhijit/brahma
windows) → ranked slate with per-candidate ledger: `{score_tier, satisfied_rules[],
violated_rules[], personal_notes[], lagna_note}` + honest "best available is mediocre — here
is why, and here is the next genuinely good date" when the range is poor (the almanac-app
failure is serving the least-bad slot as if it were good).

### 3.4 Clarity contract
The user gets: *the 3 best slots, why each is good FOR THEM and THIS purpose, what's imperfect
about each, and the single best date if they can wait.* Every rejection is inspectable
("Jul 30 rejected: Vadha-tārā for your star" — the exact miss MC-027 caught, now structural).

---

## §4 — VIEW 4: STORY (`kala_story_get`) — "What is the story of my life in time?"

### 4.1 What the consuming LLM needs
A clean chapter hierarchy I can narrate from directly — no duplicate spans, no contradictory
labels (the current parva output has both), each chapter carrying its meaning, its evidence,
and its verdict against lived history.

### 4.2 Astrological content
- **Chapters = daśā periods with the lord's natal identity:** a Saturn chapter IS natal
  Saturn's story (exalted 10th/11th-lord in the 7th → "the earning of standing through
  others"). Chapter theme derives from: lord's natal verdict digest × functional nature for
  the lagna × domain promise map — not keyword boilerplate ("receding phase marked by
  transformation" ×40 is the current state; it must die).
- **Chara-daśā as the second narrative voice** — Jaimini's sign-periods narrate *arenas*
  ("the Libra years: the 7th house comes into focus") vs Vimśottarī's *agents*. Both computed;
  Chara never narrated. Two-voice chapters are a genuinely richer biography than any
  single-school telling.
- **Punctuation marks:** Saturn return (~29.5/58), Jupiter returns, nodal return/half-return
  (18.6/9.3), sāde-satī cycles as recurring trials with their phase quality, eclipses on
  natal points, daśā-sandhi as chapter transitions. (Same BUILD items as AHEAD's event
  calendar — one build, two views.)
- **Lived-history verdicts:** LEL events pinned to chapters with the retrodiction fit served
  per chapter — *"in your Saturn/Mercury years the log shows the first job and the exit; the
  clocks explain 2 of 2."* The 57-event LEL + `mechanism_retrodiction` exist; the per-chapter
  join does not. **BUILD.** This is where the instrument proves itself to the user inside
  their own biography — the single most trust-building surface possible.
- **The road ahead as story:** future chapters previewed in the same voice (Ketu 2027–34 "the
  turn inward"), continuous with the past — one biography, not two products.

### 4.3 Algorithm
Strict hierarchy MD→AD→PD (dedup by construction — one row per span per level, parent ids;
the current duplication becomes schema-impossible). Chapter quality = f(lord natal strength,
functional nature, convergence density, obstruction density) with the formula served. Theme
composition from the lord's actual natal digest. Punctuation events interleaved. LEL pinning +
retrodiction fit per chapter. Chara overlay as parallel track with concurrence notes.

### 4.4 Clarity contract
Reads as a table of contents of a life: each chapter one paragraph — *its name, its nature,
what it asked of you / will ask, what actually happened (verified), what the next one wants.*
Citations behind every sentence via EXPLAIN ids.

---

## §5 — VIEW 5: PRIORITIZE (`kala_priority_get`) — "Of everything, what matters most right now?"

### 5.1 What the consuming LLM needs
Triage I can trust when composing a bounded answer: which temporal facts MUST make it into my
reply. Today's ranking is salience-monoculture — "dignity: neutral" descriptor rows outrank a
fired pushkara (MC-030's class) and the wealth query returns character rows (MC-022).

### 5.2 Design — rank on a served VECTOR, not an opaque scalar
Five axes, each visible per row: **imminence** (time-to-peak) · **intensity** (net λ, suppression-
adjusted) · **rarity** (population-relative: how unusual is this configuration — the
`nakshatra_statistics`/chart-cluster substrate exists and is never used for this) ·
**actionability** (is there an ELECT lever or a remedy join — a window you can act on outranks
one you can only await) · **confidence** (Law-5 tier + concurrence count). Domain-filtered
(shipped in ŚODHANA), question-scoped. Hard rules: fired rare events (pushkara, gandanta,
eclipse-contact, sandhi) floor above descriptor rows categorically; `attention_budget` framing —
top-N plus an honest "M items below the cut, largest omitted: X."

### 5.3 Clarity contract
The user (and the consuming LLM) gets a defensible answer to "why are you telling me THIS?" —
because every row shows its five axes. Triage becomes auditable instead of vibes.

---

## §6 — VIEW 6: EXPLAIN (`kala_explain_get`) — "Why do you say that?"

### 6.1 What the consuming LLM needs
When the user pushes back — and the sophisticated user always pushes back — I need the full
causal chain for any window/chapter/candidate id in ONE call. Today this is manual archaeology
across five tools; under challenge, an LLM without EXPLAIN either caves or confabulates. This
view is the product's trust backbone AND its teaching surface.

### 6.2 Design — the provenance graph, materialized at build time
Every field row persists its edges when written (not reconstructed at query time): window →
predicates → signals → natal facts, each edge typed (`clock | promise | modulation |
suppression | concurrence`) with fact_ids AND classical citations (the corpus is ingested —
BPHS/Phaladeepika/Jaimini chunks with attributions; rules already carry citation stubs; the
join is buildable). Response per id:
- **the chain** — walkable, each link grounded and cited;
- **the school ledger** — which traditions endorse this window, which dissent, on what grounds
  (Law 2's dissent objects, drilled);
- **the weakest link** — the least-attested edge, named honestly ("this link rests on a
  computed extension, not a classical rule" — `uncited_extension` flags exist and serve
  nowhere);
- **the counterfactual** — what would strengthen/weaken it ("without the vedha on Jupiter this
  window would grade one tier higher"), computable from the modulation stack already applied;
- **the calibration record** — once L5 lives: "windows of this class for this chart: 7 of 9
  confirmed."

### 6.3 Clarity contract
Any claim in any view is two hops from its śāstric ground: claim → chain → verse. That is a
stronger provenance discipline than any human acharya can perform live — and it converts every
skeptical user into a student.

---

## §7 — The missing data points (the build-registry for supremacy)

Consolidated from §§1–6; **[N]** = new computation, **[J]** = join/serving of existing data,
**[E]** = engine-scale build. Priority order within tier:

**Tier A — required for the views to meet their contracts:**
1. [N] Daśā-sandhi calendar, all levels, both directions (NOW, AHEAD, ELECT, STORY).
2. [J] Recurrence-ladder serving from `activation_predicted_dates_jsonb` (AHEAD).
3. [N] Sky-event calendar: ingresses, stations, **eclipse-to-natal contacts**, **returns**
   (Jupiter/Saturn/nodal), **Guru-Śani double-transit windows** (AHEAD, STORY; aligns with
   GOCHARA-2.0's chart-independent diary — build once, share).
4. [N] Moorti-nirṇaya per transit ingress per chart (NOW; rules exist, computation doesn't).
5. [J] Vedha application to active/forecast transits (NOW/AHEAD; rules exist) — **and the real
   Sarvatobhadra grid data (R-19), which this finally forces**.
6. [N] Activity-specific muhūrta rule table keyed to `brahma_activity_ontology` (ELECT).
7. [N] Muhūrta-lagna instant computation + strength check (ELECT).
8. [J] Gochara dual-reference (Moon + lagna) serving (NOW/AHEAD).
9. [N] Health/adverse event class in the sweep grammar (AHEAD — DP-4, already mandated).
10. [J] Per-chapter LEL pinning + retrodiction fit (STORY).
11. [N] Provenance edges persisted at field-write; citation join rules→classical chunks (EXPLAIN).
12. [J] Daśā-system applicability evaluation per chart (Law 1; conditions are in the daśā
    reference corpus, never evaluated).

**Tier B — differentiators:**
13. [N] Tithi-Praveśa (lunar-return annual charts) — the missing third annual technique.
14. [N] Janma-anchored election micro-rules (tithi/vara/nakṣatra returns).
15. [J] Rarity axis from population statistics (PRIORITIZE).
16. [N] Kota-Chakra transit fortress (classical protective/danger frame; strong for the
    health/adversity register nothing else covers).
17. [N] Sudarśana-Chakra year-wheel (tri-lagna annual rotation) as a STORY/NOW cross-check.
18. [E] KP sub-lord clock (CR-75) — a fully independent concurrence voice; slot designed now.
19. [E] GOCHARA-2.0 sub-day substrate — ELECT's hour-precision and AHEAD's honest edges.

**Tier C — the learning loop:** 20. [J] Auto-filed prospective ledger entries per AHEAD window
(VIDHI E-2) · 21. [E] per-tradition per-chart calibration weights (Law 4) once outcomes accrue.

## §8 — Planner integration (the views must be UNMISSABLE)

Six Vidhi primitives (`now_read`, `ahead_read`, `elect_read`, `story_read`, `priority_read`,
`explain_read`) with machine-band defaults: **every domain deepdive compiles NOW + AHEAD +
PRIORITIZE for its domain** (timing is never optional in a deepdive — depth doctrine);
undertaking/timing intents compile ELECT; biography/life intents compile STORY; **every served
row id pre-authorizes one EXPLAIN hop** (VIDHI E-3's bounded-expansion pattern). `intent_classify`
gains the six view-verbs as routable intents so "when should I…" → ELECT and "why do you say…" →
EXPLAIN deterministically. Tool descriptions written name-first for naive affinity; the six
retire/alias the fourteen (each legacy tool's description points to its successor view for one
deprecation cycle — the consuming LLM must never face two answers to one question again).

## §9 — What must not be lost (preservation register)

The sweep's shape-aware windows + DR-16 honesty payloads → AHEAD's core. AV gating + kakṣyā →
NOW/ELECT modulation. `window_families` dedup → all views. Obstruction detection → signed
suppression everywhere. Convergence math → Law-2's concurrence engine. Parva quality labels →
STORY's chapter grades (with the formula finally served). Tārā/chandra baselines → ELECT vetoes.
The DR-13 shapes, `peak_basis`, coverage attestation, `structural_prior` honesty — carried
verbatim. Nothing of value in the current fourteen surfaces lacks a named home above.

## §10 — Sequencing

1. Ratify this design (one decision).
2. **Envelope + facade first:** the six tools as facades over EXISTING substrate (even
   imperfect), so the consuming LLM's world becomes six names immediately; substrate
   consolidates beneath a stable contract.
3. Tier-A builds in dependency order (1–2–8–5 are days; 3–4–6–7–9–11 are the real wave —
   pairs with the stocktake's consolidation campaign).
4. Planner wiring (§8) rides VIDHI-PŪRṆATĀ E-1 (same lane, same files).
5. Tier B/C as commissioned waves; KP and 2.0 keep their standing designs.

---
*The one-line version: six names an LLM cannot miss, five laws that turn school-disagreement
from a liability into served intelligence, one promise-gated field beneath them, and a build
list — sandhi, sky-calendar, moorti, vedha, election rules, provenance edges — that takes the
layer from "computes almost everything, serves a fraction" to an instrument that can say WHEN,
WHY, and HOW SURE, and prove all three.*
