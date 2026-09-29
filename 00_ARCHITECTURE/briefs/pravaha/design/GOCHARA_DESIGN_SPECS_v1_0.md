---
artifact: GOCHARA_DESIGN_SPECS
canonical_id: GOCHARA_DESIGN_SPECS
version: "1.0"
status: DRAFT_IN_REVIEW
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
doctrine: "sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (SEALED; D-BRIEF countersigned 2026-09-29)"
reconciliation: "design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md (B3.1)"
rulings: "D-RQ1…D-RQ8, D-P4, D-PADMIT (native, 2026-09-29); lane sheets M-1…M-8, N-1…N-22, ADK-0026/0027/0028 — all stand"
freeze_protocol: "B3.5 independent review (Kimi K3 max + Codex gpt-6-astra max) → B3.6 reconcile → status: FROZEN under D-SPECS. Until FROZEN, Stream A builds nothing against this file."
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa only (D-SCOPE)"
evidence_labels: "[D] served corpus text:page · [P] practice, uncited_extension with ruling · [R] native ruling · [L] production read-only · [S] source at lane branch · [U] unverified"
---

# Gochara design specs v1.0 — the J1 contract

Eleven sections. Each carries a **schema** (the object and its fields), **invariants** (what must
always be true), and **test oracles** (given/when/then, with the arithmetic written out — the
lesson of the miscounted house is campaign law: no rule number without the count behind it).
Stream A's migrations implement these schemas; Stream B's rule paths (B5.1) implement these
evaluators; the rehearsal (A5.5) runs these oracles. Section 11 is the master oracle index.

## 0. Shared definitions

- **Contact**: one solved physical relation between a transiting body and a physical object
  (point, span, star, derived point, varga position, saham). Physical identity is
  label-independent (v3.0 #27): one crossing exists once, however many interpretive roles attach.
- **Three objects, three lineages** (v3.0 §2.3, Codex E6): physical geometry (contacts),
  interpretive records (relationship records), evaluated windows. A doctrine change re-evaluates
  windows; a frame/aspect/target-generation change re-solves geometry; neither is the other.
- **Admission**: a rule path is admitted iff its source status is `[D]`, or `[P]` with
  `uncited_extension=true` and a native ruling recorded (v3.0 §2.2). `[U]` never enters a score.
- **Frame** enum: `moon | lagna | graha:<X> | dasha_lord | bhavat_bhavam:<house>`. Counting is
  inclusive of the reference sign (1st = the sign itself). Every count in an oracle shows it.
- **Generation labels**: `'4.1'` = geometric baseline, candidate-only, never flipped (D-41);
  `'5.0'` = first sound candidate. Manifest-driven provenance (N-10): no string-matched branches.

---

## 1. `relationship_record` — the object that replaces the flat target list

### 1.1 Schema

One row per (event_class, affected_person, frame, agent, relation, object, role):

| field | type | notes |
|---|---|---|
| `record_id` | uuid | deterministic hash of the natural key below |
| `chart_id` | uuid | 482012f1 only |
| `event_class` | text | the 27 classes; adverse classes first-class |
| `affected_person` | enum | `native | father | mother | spouse | child | sibling | …` |
| `frame` | enum + arg | §0; `bhavat_bhavam:9` for the father |
| `agent` | graha | the transiting (or period) body |
| `relation` | enum | `residence | aspect | conjunction | dispositorship | association | ownership | occupancy | period_running` |
| `object_kind` | enum | `degree_point | sign_span | star | derived_point | varga_position | saham` |
| `object_ref` | jsonb | physical identity: `{body|house|point, longitude|sign, varga?, year?}` — never a label-only ref |
| `object_role` | enum | `lord | occupant | karaka | dispositor | maraka_of_house | period_lord | yoga_constituent | pada` |
| `prerequisites` | jsonb | ordered list: `natal_condition · period · residence · applicability` — cheapest necessary predicate first (§6 pruning) |
| `temporal_support` | jsonb | grain + support intervals |
| `coverage_ref` | → coverage manifest | uncomputed ≠ empty, always resolvable |
| `precision` | jsonb | `solver_method`, δλ, δt (§7) |
| `source_text`, `source_page` | text | e.g. `Phaladīpikā`, `PG249-250 (XX.34-38)` |
| `source_status` | enum | `D | P` |
| `qualification` | enum | `verse_cited | uncited_extension | testimony` |
| `ruling_ref` | text | required iff `qualification = uncited_extension` (e.g. `D-P4`) |
| `evidence_for_occurrence` | real | §3 |
| `evidence_against_occurrence` | real | §3 |
| `outcome_valence_for_native` | enum | `favourable | adverse | mixed | unqualified` — §3 |
| `severity` | real | interpretive, never a gate |

### 1.2 Invariants

1. `frame` is present on **every** row; a row without a frame cannot exist (v3.0 #10 — two frame
   errors: Moon-relative rules matched to lagna house numbers *and* resolved from LAGNA).
2. `qualification = uncited_extension ⇒ ruling_ref IS NOT NULL` (admission rule; D-P4, D-PADMIT).
3. Role aliases of one physical contact (Jupiter as kāraka, as 9L, as yoga constituent) are
   **role edges on one `contact_id`** — never independent observations; no noisy-OR across them.
4. `object_ref` resolves to a physical longitude/sign/varga position; sensitive-degree checks with
   negative results (`not_gandanta`, `not_pushkara`, `not_fired`, `none`) are **not objects**
   (E3: 154 of 176) — they fold into the graha's interpretation.
5. House counts are computed from the row's own `frame`, with the arithmetic stored at evaluation
   time (the count behind every citation).
6. A relative's event never reads the native's Moon frame as its licence; `bhavat_bhavam` frames
   carry relatives (v3.0 §4 father example).
7. No soft factor field may zero an admitted window; exclusion only via L0 absence or a failed
   prerequisite of the record's own path.

### 1.3 Test oracles

- **O-RR-1 (twins frame count).** Natal Moon 327.06° = Aquarius. Transit Jupiter 306.87° =
  Aquarius. Count: Aquarius is the **1st** from Aquarius ⇒ a Moon-frame record "Jupiter in 5th
  from Moon" must NOT exist for 2022-01-03; v2.0's claim is the regression case. The lagna-frame
  record (Jupiter in 11th from lagna, aspecting Leo = 5th house) must exist.
- **O-RR-2 (father frame).** `bhavat_bhavam:9` (Sagittarius): 7th from 9th = Gemini (Mercury),
  8th from 9th = Cancer (Moon), 2nd from 9th = Capricorn (Saturn). On 2018-11-28 the period
  lords Mercury (MD) and Moon (AD) must resolve as father-frame relationship records.
- **O-RR-3 (occupant recovery).** Marriage class: the 7th-house **occupant** (natal Saturn,
  202.43° in Libra) must appear as an object with `object_role = occupant`; resolving 7L Venus
  alone is a recorded miss (the v3.0 §4 target lesson).
- **O-RR-4 (no negative-result object).** Building records for any class must not create an
  object from a `chart_facts` row whose value ∈ {not_gandanta, not_pushkara, not_fired, none}.

---

## 2. `rule_paths_P1_P6` — admissibility as a union of source-qualified paths

`W_event = ⋃ over admitted paths r ( ⋂ over prerequisites p of r  I_p )`; inside `W_event` a
score **ranks** (product of the path's named soft factors); ranking never admits or excludes.

### 2.1 Path catalogue (each path: frame · agent→relation→object · prerequisites in evaluation
order · soft factors · source · status)

**P1 — daśā-lord path** `[D]` Phaladīpikā XX.34–38 (PG249–250); node-dispositor `[P]` (D-PADMIT,
testimony). Frame: `dasha_lord` / natal sign positions. Content: running MD/AD/PD lord's own
transit through svakṣetra/exaltation/friendly sign promotes its bhāva; debility/inimical/combustion
→ misery; Sun or Jupiter transiting the bhukti lord's exaltation sign delivers the auspicious
bhukti's fruit. AD/PD lords appear as objects **and** agents; dispositor and association edges.
Prerequisites: (1) period running at t (§4); (2) natal bhāva relationship of the period lord to
the event class; (3) the transit relation itself.

**P2 — Moon-frame gochara-phala** `[D]` Phaladīpikā XXVI.1–8 (PG321–323), XXVI.11 (PG335); M-8
`[R]`. Frame: `moon`. Per-planet favourable houses from janma-rāśi with vedha, Sun↔Saturn and
Moon↔Mercury exceptions, vipareeta cancellation; **adverse residence**: Saturn/Sun/Mars/Jupiter in
12/8/1 → danger/fall/loss — attaches to **adverse** classes only. Licences the native's fortune,
never a relative's event (v3.0 §4: Saturn 11th from the natal Moon on 2018-11-28 is favourable
for the native and irrelevant to the father's frame).

**P3 — lagna-frame bhāva transit** `[D]` Yavana Jātaka ch.45–48 + Parāśari bhāva doctrine;
māraka-of-house `[P]` (D-PADMIT, testimony). Frame: `lagna`; relatives via `bhavat_bhavam`.
Slow-body residence in / aspect on a signature house **and its lord**; father = 9th, its
2nd/7th/8th as the maraka/māraka set.

**P4 — double transit** `[P]` `uncited_extension` under **D-P4**; sole primary joint precedent
Phaladīpikā XVII.12 (PG216) `[D]`. Jupiter **and** Saturn both influencing (occupation or aspect)
a signature house **or its lord**; tightest overlap = peak. The seed's "same Moon-house"
definition is withdrawn; v2.0's father-example double-transit claim is withdrawn (Jupiter in
Scorpio aspects Pisces/Taurus/Cancer — not Sagittarius).

**P5 — aṣṭakavarga path** `[D]` BPHS ch.66 vv.13–15 (`BPHS2:35666-35684`), ch.70
(`:40799-41558`, `:42332-42335`), Phaladīpikā XXIII (PG301), XXIV (PG304, PG307). After §8
polarity normalisation. Forms: (a) transit through signs with more benefic marks in the
**transiting graha's own** BAV favourable, fewer adverse — **known-zero is adverse** (D-RQ1;
BPHS ch.70 vv.24–27), unresolved operand is `unqualified`; (b) SAV >30 favourable / 25–30
medium / <25 adverse; (c) fruit delivered in the **kakṣyā owned by the mark-donor**; (d)
śodhya-piṇḍa × marks ÷ 27 → nakṣatra: Saturn/Jupiter over it (or its trine) times the graha's
affairs (self from own AV, father from Sun's AV); (e) Sun-month selection only where the rule
says so (BPHS ch.70). **No universal numeric multiplier** — M-7 bands remain a WP8 hypothesis
(D-RQ1).

**P6 — Moon channel (on demand)** `[P]` muhūrta practice; Muhūrta Cintāmaṇi present (274 chunks;
B3.3 reads). Frame: per the admitting path's objects. Moon over the path's objects/trines *as the
path specifies*; tārā (nine-fold); tithi–nakṣatra; the Moon's own vedha; chandrāṣṭama. **Day rows
come only from this path** (M-3); it runs on demand inside admitted windows with its own coverage
record — never materialised century-wide (§6).

### 2.2 Invariants

1. Admission per §0; every path row carries `source_status` and, for `[P]`, the ruling ref.
2. Pruning discards an interval for path r **only** where a necessary predicate of r is
   demonstrably false there; unknown applicability ≠ false applicability; "uncomputed" is never
   reported as "empty".
3. No soft factor zeroes an admitted window (v3.0 §2.2); vedha and AV **qualify**, L0 absence and
   failed prerequisites **exclude**.
4. Era/month/day are **output resolutions** produced by the paths operating at those grains —
   never a clipped curve (the 27-of-41 plateau, E5, is the defect this kills).
5. Grain assignments are authoring defaults, overridable by any rule whose source places an agent
   at another grain (Sun's month, Mars's gains — BPHS ch.70).
6. P6 is the only source of day-resolution rows; a day row from any other path is a defect.
7. Node-dispositor delivery and māraka-of-house edges are **testimony** (D-PADMIT): they annotate,
   never weight, until B5.4 ablation evidence supports promotion.

### 2.3 Test oracles

- **O-RP-1 (union, not cascade).** Given a window admitted by P3 with P2's Moon-frame phala
  adverse, the window remains admitted (union), and the P2 record attaches as
  `evidence_against_occurrence` on the native's own-fortune class only.
- **O-RP-2 (father, not a double transit).** 2018-11-28: Jupiter 220.31° (Scorpio) aspects
  Pisces (5th), Taurus (7th), Cancer (9th) — Sagittarius is not among them ⇒ no P4 record for the
  father frame on that date; the admission runs on P3 + P1.
- **O-RP-3 (twins, P4 house-plus-lord).** 2022-01-03: Jupiter in Aquarius (11th) aspects Leo
  (5th house); Saturn 288.01° is 3°57′ from natal Sun 291.96° (5L) ⇒ P4 admits (house via
  Jupiter's aspect + lord via Saturn's conjunction), tightest overlap = peak.
- **O-RP-4 (Aṣṭottarī absent).** Period evaluation for any t must not include an Aṣṭottarī vote
  (D-RQ7 — both BPHS ch.46 conditions fail: Rāhu 8th from lagna lord; day birth Śukla pakṣa).
- **O-RP-5 (adverse residence scoping).** A Saturn-in-8th-from-Moon interval attaches
  `evidence_against` to adverse classes and does **not** attach to gain classes (D-RQ5's shape
  generalised; twins' phase-1 Sade-Sati must not touch the childbirth class).

---

## 3. `three_field_valence` — evidence for, evidence against, outcome for the native

### 3.1 Schema (on every evaluated window and every relationship record)

`evidence_for_occurrence real` · `evidence_against_occurrence real` ·
`outcome_valence_for_native enum(favourable|adverse|mixed|unqualified)` · `severity real`.

Class-relative polarity (v3.0 #11, #12): each event class declares its polarity; rule polarity is
interpreted **relative to the class** (a strong 7th-house affliction is evidence **for** the
separation class and **against** the marriage class). Negatives are never clamped out of activity
— they flow to both evidence fields per class.

### 3.2 Invariants

1. The three fields are independent: high `evidence_for` and high `evidence_against` ⇒ `mixed`,
   not cancellation to neutral.
2. `outcome_valence_for_native` reports the *native's* interest (favourable marriage window vs
   favourable bereavement window are both "admitted" — their outcome valences differ).
3. `unqualified` is the honest state when operands are unresolved (ADK-0026; §N.7 honest null) —
   never a favourable-sounding default. Finding #12's defect (1,435 era rows all "favourable",
   incl. separation/deception/bereavement — E5) is the regression this field exists to prevent.
4. Valence is computed at evaluation time from class polarity + record content; it is never
   copied class-blind from the rule row.

### 3.3 Test oracles

- **O-TV-1.** A bereavement-class window admitted by P3 (Saturn to the 9th lord) evaluates
  `evidence_for_occurrence > 0` and `outcome_valence_for_native = adverse`.
- **O-TV-2.** The marriage window of 2013-12 carries `evidence_for` (P3+P4 on the 7th occupant)
  and `evidence_against` (natal 7th affliction as condition — promise = strength *and* condition)
  simultaneously; outcome `favourable`, severity moderated.
- **O-TV-3.** Any unresolved AV operand ⇒ the valence contribution is `unqualified`, and the
  window's breakdown names the unresolved operand — no silent 1.0.

---

## 4. `permission_per_instant` — period licence as a function of t

### 4.1 Schema

`permission(chart_id, t, event_class) → {admitted_paths[], period_context {md, ad, pd, system,
applicability}, prerequisites_state[]}`. Computed **per instant** from nested Vimśottarī MD/AD/PD
(level ≥ 3 from L1 `chart_dashas`), each lord's event-relevant relationships (lordship, occupancy,
dispositor, association — the §1 record edges). Chara daśā serves Jaimini targets only. Mudda
daśā lives inside P9 (Tier 2). Aṣṭottarī: applicability-evaluated, **absent on this chart**
(D-RQ7). N-15 enforced here: no Sade-Sati term in any permission or λ.

### 4.2 Invariants

1. Permission is a function of t, never a per-class constant over a decade (E6: one boolean per
   (class, system), union over candidate instants → 0.53 for the decade — the defect).
2. A period lord with **no relationship** to the event class does not licence it (relationship
   requirement, both reviewers' C-class findings).
3. Applicability is evaluated from chart operands (pakṣa, Rāhu position) and stored; a system
   whose conditions fail is `absent`, not `false`-weighted.
4. Permission prunes only through a path's necessary period prerequisite; it never multiplies as
   a decidable zero/one constant across all paths.

### 4.3 Test oracles

- **O-PP-1.** 2013-12-11 → MD Mercury / AD Ketu (L1 `chart_dashas`); 2018-11-28 → Mercury/Moon;
  2022-01-03 → Mercury/Rāhu. The function returns exactly these lords at these instants.
- **O-PP-2.** Permission for the marriage class differs between an instant inside Mercury/Ketu
  and an instant inside a period whose lords carry no 7th-house relationship — it is not constant
  across 2020–2030.
- **O-PP-3.** The Aṣṭottarī system reports `absent` with its failed conditions named
  (Rāhu 8th from lagna lord; day birth in Śukla pakṣa).

---

## 5. `vedha_interval_relation` — obstruction as intervals, not flags

### 5.1 Schema

`vedha_interval(primary_contact_id, obstructor_body, vedha_kind, t_in, t_out, state
∈ {active, cancelled_vipareeta, inactive}, exception ∈ {none, sun_saturn, moon_mercury},
independence_group, source_ref, qualification)`.

Semantics: a primary transit's vedha exists only where an obstructor's residence interval
**overlaps** the primary's residence interval in the vedha-paired house (temporal structure
preserved — N4: today's writer counts any overlap of any part as simultaneous and keeps first
obstruction/cancellation only). Vipareeta cancellation **carves a sub-interval** out of the
obstruction instead of flipping a row flag. The two exception pairs never obstruct each other
(M-8: Sun↔Saturn, Moon↔Mercury). Grade keys match the served table (#16); the PG353 battle scale
used as a general grade is stamped `uncited_extension` (D-RQ8 hygiene; G-9's note). **No
attenuation without an active obstruction** (#17: E2's 55 inactive + 46 cancelled rows currently
attenuate; a clean favourable transit ×0.85 is the defect). `independence_group`: one obstruction
root attenuates once, duplicates never multiply (E2).

### 5.2 Invariants

1. Vedha **qualifies** a specific primary transit (Q-level); it never excludes a window.
2. Attenuation requires `state = active` at t; `cancelled_vipareeta` and `inactive` intervals are
   reported, not applied.
3. Moon-vedha rows exist only inside P6 day windows with a P6 coverage record (Moon vedha on
   decade windows is on the overkill list).
4. Absent overlay coverage reads as `unavailable` with a coverage object, never as 1.0 (E2's
   1.26 %-of-century overlay reading as clean is the defect).

### 5.3 Test oracles

- **O-VI-1.** Primary Venus transit with an inactive obstruction row overlapping ⇒ attenuation
  factor exactly 1.0 and the row reported as inactive.
- **O-VI-2.** Obstruction overlapping only the first half of the primary residence ⇒ attenuation
  applies only inside the intersection interval; the second half is clean.
- **O-VI-3.** Saturn obstructing a Sun primary (and Moon obstructing Mercury) ⇒ no vedha
  interval is created (exception pairs).
- **O-VI-4.** A vipareeta row covering part of an obstruction ⇒ the covered sub-interval is
  carved out; attenuation resumes outside it; the row carries `cancelled_vipareeta` with its own
  interval.

---

## 6. `sky_event_substrate` — compute once, solve once

### 6.1 Schema

One substrate per (ephemeris/convention generation, ayanāṃśa, node convention, body, grid):
`sky_event(body, event_kind ∈ {sign_ingress, nakshatra_ingress, kakshya_crossing, station,
eclipse_instant}, t_exact, longitude, solver_method, δλ, δt)`. Relative-body geometry
(inter-transit aspects, combustion, tithi) is a **separate** substrate; location-dependent
election predicates are not in the natal-contact table.

**Contract counts** (v3.0 §6.1): Sun 12 sign / 27 nakṣatra / 96 kakṣyā crossings per year;
Saturn ≈ 0.4 / 1.1 / 3.2 plus retrograde re-crossings. **Moon events are generated on demand**
(≈ 4×10⁵ boundary events per 250 y if materialised — Codex E5); a Moon search writes a
`moon_on_demand` coverage record for the requested interval.

### 6.2 Invariants

1. **Physical identity is label-independent**: one crossing = one row, whatever targets consume
   it (E1's 31,401 × 3 identical kakṣyā rows are the defect).
2. **0° seam root exists** (Aries/Aśvinī; #14); boundary search covers **both** boundaries so
   retrograde entries are found (N2); **no fabricated ingress** at a clipped horizon start
   (`t_exact = ca`, `exact_crossing = true` is forbidden — N2); contacts whose exact centre lies
   outside the horizon are retained as **truncated spans** with coverage, never dropped (N3).
3. Residence spans are intervals with coverage (#6 repair: retain residence/state; #7: house-level
   targets reach the score as spans, not ingress instants).
4. Interval objects stay intervals; cusps are never converted to points (M-5).
5. Boundary events are enumerated **per body**, joined to targets afterwards — never per target.

### 6.3 Test oracles

- **O-SS-1 (counts).** For 2025-01-01→2026-01-01: Sun sign crossings = 12, nakṣatra = 27,
  kakṣyā = 96 (±0); Saturn within [0, 2] sign crossings including any retrograde re-crossing.
- **O-SS-2 (seam).** A body at 359.9° moving direct produces an Aries ingress root; at 0.1°
  retrograde, an ingress found through the **upper** boundary (Pisces re-entry), both with
  `exact_crossing = true` honestly.
- **O-SS-3 (truncation).** Horizon clipped mid-residence ⇒ the contact is stored as a truncated
  span with `coverage.truncated = true`, not dropped and not given a fabricated `t_exact`.
- **O-SS-4 (Moon on demand).** A P6 day query for a 30-day window returns Moon boundary events
  for exactly that window plus a `moon_on_demand` coverage row; the global substrate holds no
  materialised Moon rows.

---

## 7. `solver_method_uncertainty` — certified bounds, honest method

### 7.1 Schema (fields on every contact and sky event)

`solver_method ∈ {arc_index_bracket, swiss_refined, clipped_truncated}` · `delta_lambda` ·
`delta_t` · `precision_regime` (keeps its ruled meaning — date_grain / instant_grain).

Refinement rule: bracket from the arc index; refine to Swiss whenever the approximation's
uncertainty could change **membership, ordering, boundary identity, or a reported peak**; store
both uncertainties (δt ≈ δλ/|λ̇|, unstable near stations — stations are always Swiss-refined).

### 7.2 Invariants

1. Every reported `t_exact` carries its method and uncertainties; a row without them is a defect.
2. Scores retaining a functional form are solved for **interior extrema and threshold roots**
   (products of linear factors are quadratic; endpoint-only evaluation is forbidden) — v3.0 §6.5.
3. The M-1 activity kernel is **angular**: `activity = 1 − |Δλ|/orb` on angular separation, per
   the ruling — a time-interpolated triangle (N1) is a conformance defect (D-RQ2); around
   stations the two disagree and the angular form wins.
4. A tolerance or method change implies a new `convention_id` (plan v2.1 §4); contact ids hash
   `method_version`.

### 7.3 Test oracles

- **O-SM-1 (N1 regression).** Around a Saturn station, the activity curve from the angular kernel
  is symmetric in |Δλ| and non-monotone in t; the time-triangle implementation is rejected by
  comparing both against Swiss longitudes at 6-hour samples.
- **O-SM-2.** A conjunction bracketed by the arc index with δλ larger than the orb boundary
  distance is Swiss-refined before membership is reported.
- **O-SM-3.** Every station event in the substrate has `solver_method = swiss_refined`.

---

## 8. `bindu_polarity` — declared before any citation-bearing weight

### 8.1 Schema

`av_polarity_declaration(convention, benefic_mark_name, malefic_mark_name, source_ref,
applies_to_fact_categories[])`. For L1's `ashtakavarga_bindu*`: the columns store PyJHora's
benefic "dots"; the Santhanam BPHS names the benefic mark **rekhā** and the malefic **bindu**
(`BPHS2:35666-35684`) — so a "BPHS ch.66" citation on a `bindu` column can carry the opposite
polarity (N8). The declaration row pins: convention `pyjhora_dots = benefic_marks`, mapped to
BPHS `rekhā` for citation purposes, applied to all `ashtakavarga_bindu*` categories.

Evaluation semantics (D-RQ1): in a graha's own BAV, a transited sign's benefic-mark count is
compared against the sign mean — **more favourable, fewer adverse, a known zero is adverse**
(BPHS ch.70 vv.24–27); an **unresolved operand** (missing AV build, missing contributor matrix —
G-10) yields `unqualified`, never zero-weighted silence. SAV bands: >30 favourable / 25–30
medium / <25 adverse (`BPHS2:42332-42335`).

### 8.2 Invariants

1. No AV-derived weight or qualifier exists before the polarity declaration row exists (T0-11
   gates P5).
2. The declaration is data, not prose: evaluations join it and record it in their lineage.
3. Known-zero and unresolved are distinct states end-to-end; conflating them is a defect class
   (D-RQ1).
4. The per-contributor kakṣyā qualification (P5c) declares its operand level: sign-level BAV is
   the coarser qualification and says so until L1 closes G-10.

### 8.3 Test oracles

- **O-BP-1.** A sign with 0 benefic marks in Mars's BAV ⇒ Mars's transit there carries an
  **adverse** AV qualifier with the count shown (known-zero), not `unqualified`.
- **O-BP-2.** A chart scope lacking the AV build ⇒ the qualifier is `unqualified` and the window
  breakdown names the missing operand.
- **O-BP-3.** Any citation string "BPHS ch.66/70" emitted by an evaluation resolves through the
  polarity declaration (rekhā = benefic), verified by reading the declaration row back.

---

## 9. `annual_object_identity` — sahams, muntha, varṣeśa per year

### 9.1 Schema

`annual_object(chart_id, varsha_year, kind ∈ {saham:<name> | muntha | varshesha}, longitude,
sign, house_lagna_frame, source_ref)` — identity keyed by (chart, year, kind); computed from the
varṣa-praveśa chart of that year; **never joined across years** (a Vivāha saham of year n is not
the object of year n+1). Consumed only by P9 (Tier 2) and Mudda daśā inside the year.

### 9.2 Invariants

1. Annual objects carry their year in their identity; any cross-year equality test is a defect.
2. Saham formulas carry their source (`[D]` Tājaka Nīlakaṇṭhī, Devanagari chunks, B3.3 §4) and
   day/night variant where the text gives one.
3. The **activation rule** (what delivers the saham's fruit — varṣeśa/muntha/Mudda contact) is
   `[U]` until B3.3's read lands; until then P9 admits objects but no activation weight.
4. Annual objects are interval-free points; their transit contacts follow §6/§7 like any other
   physical point, within the year's horizon.

### 9.3 Test oracles

- **O-AO-1.** The Vivāha saham for two consecutive varṣa years differs in identity and (almost
  surely) longitude; a join on `kind` alone returns no cross-year match.
- **O-AO-2.** Every saham row's `source_ref` resolves to a Tājaka chunk locator from the B3.3
  register; a saham without one is rejected at write time.
- **O-AO-3.** Until the activation read is `[D]`, P9 windows carry `qualification` ≤ testimony
  and no activation factor.

---

## 10. `registered_writer_architecture` — how '5.0' gets written

### 10.1 Architecture contract

- **Three objects, one writer family** (`ka_gochara` registered writer, FROZEN orchestrator
  contract: `WriterBase` subclass, `run(ctx)` on `ctx.db_conn`, never commits/closes, idempotency
  = per-chart delete-then-insert scoped to (chart_id × generation), no `asset_throughput`
  self-writes). Emits: (1) contacts (§6 geometry, one row per physical contact); (2) relationship
  records (§1, join table of role edges); (3) evaluated windows (per admitted path, per output
  resolution actually operated).
- **Re-solve vs re-score** (v3.0 §6.7): weight, frame-interpretation, valence and path changes
  **re-score** (windows re-evaluated from stored contacts); aspect direction, new aspect levels,
  frame-dependent resolution, target-generation and support-domain changes **re-solve** (contacts
  rebuilt). Lineage propagates to Kṣetra, Saṅgam and downstream consumers.
- **Per-path coarse-to-fine pruning** (v3.0 §6.3): cheapest necessary predicate first; fast-body
  solves run only where some admitted path still admits; interval sweep for categorical
  prerequisites O(B log B + output).
- **Day tier on demand** with its own coverage record; prefetch for ranked windows is a policy,
  never an exclusion; uncomputed ≠ empty.
- **Publication**: manifest-driven (N-10 as amended by D-41): per-(chart, generation) manifest,
  `ka_gochara` publishes candidates, only the release authority flips, and only under D-FLIP at
  J2. `'4.1'` rows are candidate-only forever.
- **Serving contract** (P-1..P-4 survive, B3.1 §4): provenance and coverage read from the
  manifest (passes unchanged across `'4.1'`→`'5.0'`); absent authority ⇒ `unpublished`, never a
  `'v1'` fall-through; §N.6 density: confirmed vs context rows counted separately.
- **Benchmarks as contract** (v3.0 §6.8): cold/warm wall time, physical root count, Swiss calls,
  unresolved spans, coverage, peak preservation — reported per build; correctness measured against
  independently evaluated rule cases, never against the old pipeline's output.

### 10.2 Invariants

1. One registered writer produces `'5.0'`; no cutover script writes served rows (Disclosure 3
   closes at A6.2).
2. A doctrine (record/path/valence) change must not trigger a geometry rebuild; a geometry change
   must not silently keep old window rows (lineage invalidation is explicit).
3. Every no-window answer carries its coverage object (searched horizon, relations searched,
   targets unresolved, unavailable inputs).
4. S-2's directed events for Saṅgam are emitted **only** by the post-T0-1 kernel (aspect
   direction fixed, graduated dṛṣṭi with specials full — `BPHS1:16496-16502`); nodes excluded
   from dṛṣṭī families (N-14) while remaining agents and targets.

### 10.3 Test oracles

- **O-RW-1.** Change a valence rule ⇒ contacts table unchanged (digests identical), windows
  re-evaluated with new lineage; change aspect direction ⇒ contacts rebuilt.
- **O-RW-2.** A served no-window answer includes the coverage object; a served window set counts
  confirmed vs context rows separately (§N.6).
- **O-RW-3.** Provenance for the authority generation names `ka_gochara` and survives a
  republish under a new label without code change (manifest-driven).

---

## 11. `test_oracles` — the master index and the oracle harness contract

### 11.1 Harness contract

Oracles live as data (given/when/then + the arithmetic), executed by the B5.3 retrodiction
harness and A5.5 rehearsal. Every oracle names: the spec section it guards, the defect id it
regresses (v3.0 #1–#27, N1–N9), its operands' source (L0 `ref_planet_position_get` / L1
`chart_facts` / E8 table), and its tolerance. An oracle that cannot fail is a §N.8 violation and
is rejected at review.

### 11.2 Index (spec § → oracle ids → defect coverage)

| § | oracles | defects guarded |
|---|---|---|
| 1 relationship_record | O-RR-1…4 | #8, #9, #10, #22, E3 |
| 2 rule paths | O-RP-1…5 | #1, #2, #3, #4, RQ-7, father-example withdrawal |
| 3 valence | O-TV-1…3 | #11, #12 |
| 4 permission | O-PP-1…3 | #2, #3, E6 |
| 5 vedha | O-VI-1…4 | #16, #17, #25, N4, E2 |
| 6 substrate | O-SS-1…4 | #6, #7, #14, #27, N2, N3, E1 |
| 7 solver | O-SM-1…3 | N1, #15 (graduated dṛṣṭi conformance via BPHS1:16496-16502 oracle set) |
| 8 bindu polarity | O-BP-1…3 | N8, RQ-1, G-10 honesty |
| 9 annual identity | O-AO-1…3 | saham year-mixing (Tier 2 gate) |
| 10 writer | O-RW-1…3 | lineage (E6 Codex), §N.6, N-10/D-41 |

Plus the conformance set (N5: no producer-side 90-day filter — producer output contains peaks
closer than 90 days; serve-time filter applies at read; N6: zero rows for the natal-epoch
`birth_anchor` class; N7: mūrti rows carry no auto `verse_cited`; graduated dṛṣṭi: ordinary
aspects ¼/½/¾/full at 3-10/5-9/4-8/7, specials full).

### 11.3 Worked-event oracle set (development cases — never held-out evidence)

Positions per E8 (L0, Lahiri); natal per L1 (build 1c092ffb). These three events calibrate the
oracles; B4.2's protocol excludes them from scoring.

- **Marriage 2013-12-11**: Saturn 204.25° vs natal Saturn 202.43° (Δ = 1°49′, return to the
  exalted 7th occupant); Jupiter 84.57° R in Gemini, 5th aspect on Libra (2°08′ from natal Saturn,
  0°19′ from transit Saturn); Ketu 12.99° is 0°33′ from lagna 12.43°; Rāhu 192.99° in the 7th.
- **Twins 2022-01-03**: Jupiter 306.87° Aquarius (11th from lagna; 1st from the 327.06° Aquarius
  Moon — the count is written, not asserted); Saturn 288.01° is 3°57′ from natal Sun 291.96° (5L).
- **Father 2018-11-28**: Saturn 253.43° is 3°39′ from natal Jupiter 249.79° (9L) in the 9th;
  Saturn is 11th from the natal Moon (Moon-frame favourable — the frame-discrimination oracle);
  Sun/Jupiter/retrograde Mercury in the native's 8th.

---

*Draft for B3.5 review. Nothing herein overrides a native ruling; every `[P]` element names its
ruling; every figure traces to the sealed evidence appendix or v3.0 §8. Status flips to FROZEN
only at B3.6 under D-SPECS.*
