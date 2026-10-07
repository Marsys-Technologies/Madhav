---
artifact: KALA_ASSET_ALGORITHM_ELEVATIONS
canonical_id: KALA_ASSET_ALGORITHM_ELEVATIONS
version: "1.0"
status: DRAFT — for the native's reading, then Astra's independent review. Research and design only; authorises nothing.
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1); third pass over the Kāla layer at the native''s request: per-asset domain-logic elevation at the depth the Gochara family received'
companions: 'KALA_LAYER_VALUE_REVIEW_v1_0.md (evidence) · KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_0.md (the engine the elevated algorithms run in; this document is its §8 made concrete, asset by asset)'
grounded_at: 'code read-only at cooperative-racer @ c751f3bd8 (origin/main 2026-10-04) via three algorithm-extraction digests; classical corpus checked live through the project''s own text search on 2026-10-06 (16 texts; citations below carry the corpus locator the search returned)'
evidence_labels: "[S] source code read at the named ref · [D] doctrine verified in the ingested corpus this session, locator given · [D-prior] doctrine verified earlier by the project (document named) · [A] taken from a digest or prior document, not re-read · [U] not found in the corpus; stated from the tradition, needs a count before it enters a scored path · [I] design judgement"
depth_standard: 'the Gochara 5.0 elevation (sealed doctrine v3.0 → design specs v1.4 FROZEN): a flat score table became relationship records with frame and period anchor, rule paths with prerequisites and provenance, three-field valence, permission per instant, vedha as intervals, coverage, solver uncertainty, and 57 test oracles. Every card below is written to reach that shape or to say why the asset should not be a scorer at all.'
---

# Kāla — asset-by-asset algorithm elevations

**Written for:** the native, then Astra, then the sessions that will write each stage brief.

## §0 · What this document does

The layer review found the layer dark at its centre; the code plan designed one engine to replace three. Neither said, asset by asset, *what the astrology inside each asset should compute*. This document does. For each of the twenty-two active assets it gives: the algorithm as it exists today (from the code, with the constants quoted); its defects, astrological and computational; the elevated algorithm, written as the Gochara spec writes a rule path (inputs → computation → typed outputs → nulls); the classical basis, with each citation labelled by whether it was verified in the project's own corpus this session; what the asset gives to and takes from the rest of the layer; and the oracle that would fail if the elevation were wrong.

Two assets are already at the target depth and are not re-designed here: the judge (Gochara 5.0, frozen) and, in design, the jury (the pipeline concept note §5). They appear only where another asset's card depends on them.

Governance is not discussed here. The plan's §7 carries the minimum.

---

## §1 · The depth standard, in one table

What "elevated at Gochara's depth" means, so each card can be measured against it [S specs v1.4; A5.3 brief]:

| Dimension | Before (v3.0 and earlier) | After (v1.4 FROZEN) |
|---|---|---|
| Object | one flat per-target score row | three objects with separate lineages: physical contact (label-independent identity, occurrence ordinal), relationship record (frame, agent → relation → object, role, period anchor), evaluated window |
| Rule | an implicit weighting | a catalogue of rule paths P1–P9, each with frame, prerequisites in evaluation order, provenance (`verse_cited` / `uncited_extension` + ruling), and operator role (`scored` / `testimony`) |
| Valence | one signed number | three fields: evidence for, evidence against, valence; occurrence evidence is never outcome valence |
| Clock | a static prior | permission as a function of the instant, read from the pinned L1 daśā build |
| Obstruction | a flag or multiplier | vedha as an interval relation with states and exception pairs |
| Geometry | daily step scan | boundary events computed once, roots bracketed and Swiss-refined, solver method and uncertainty stored |
| Absence | silence | a coverage object on every answer; Moon and day tier on demand with their own coverage record |
| Proof | a passing test suite | 57 oracles, each with a fixture labelled by kind and a mutation that must fail; a pre-declared evaluation protocol with a held-out registry |

The cards below aim at that table. Where an asset's honest best shape is *not* a scorer (an adapter, a view, a service), the card says so and designs that instead.

---

## §2 · Corpus check register (this session)

Every classical claim the cards lean on was checked against the ingested corpus (16 texts: BPHS, Jaimini Sūtras, Bṛhat Jātaka, Bṛhat Saṁhitā, Horā Sāra, Jātaka Pārijāta, Muhūrta Cintāmaṇi, Phaladīpikā, Sārāvalī, Sarvārtha Cintāmaṇi, Tājaka Nīlakaṇṭhī, Uttara Kālāmṛta, Yavana Jātaka, Bhṛgu Nandi Nāḍī, Patel's Nāḍī Navāṁśa). Results, so that no card quietly upgrades a `[U]` to a `[D]`:

| Doctrine the cards need | Result | Locator / note |
|---|---|---|
| Daśā-sandhi (junction of two periods) as a stated rule | **not found** | Sārāvalī ch. 42 ("effects of sub-periods", PG160, PG165) has timing-within-period doctrine but no junction band; the sandhi band stays an engineering convention `[U]`, as the Kṣetra plan already concluded |
| Period lord's placement and relation to the lagna lord governing antardaśā results | **found** `[D]` | BPHS antardaśā chapters: PG638:C2 (Ketu in Moon's daśā "in a kendra, trikoṇa or the 3rd … endowed with strength"), PG684:C2 (Mercury in Saturn's daśā "in a kendra or trikoṇa"), PG694:C2 ("associated with the lord of the Ascendant, or in his own sign or sign of exaltation") |
| Lord's condition at commencement; beginning/middle/end fruition (BPHS 47.3–6) | **found earlier** `[D-prior]` | verified by the pipeline concept note (vol. 2 p. 577, OCR 8939–8958) |
| Alternate daśā start (stronger of Lagna and Moon; Satyācārya) | **found** `[D]` | Horā Sāra ch. 31 v. 2 (PG331:C1): daśā order counts "from one's birth star or the star in which the Lagna rises"; Satyācārya "stronger of the two"; Jātaka Pārijāta 18.33 adds two more; Sārāvalī Mūla daśā (PG155:C2) "first daśā of the strongest of the Ascendant, the Sun and the Moon" |
| Argalā as intervention with 10/12/3 obstruction (BPHS 31.2–9) | **found earlier** `[D-prior]` | concept note (vol. 1 pp. 311–312) |
| Muhūrta doṣa cancellation (parihāra / apavāda) | **found, rich** `[D]` | Muhūrta Cintāmaṇi: PG110:C1 vv. 68–71 (ekārgala, upagraha, pāta, lattā, yāmitra, kartarī, udayāsta perish when the lagna has Moon and Sun strength; vedha is to be shunned in every country); PG115:C2 v. 88 and PG116:C1 vv. 88–91 (kartarī apavāda; year/ayana/season/tithi/month/nakṣatra/pakṣa/dagdha-tithi/lagna doṣas perish with Mercury, Jupiter, Venus in kendra or trikoṇa; Jupiter in kendra/trine/11th, Sun in upacaya, Moon in lagna or vargottama destroys all doṣas; Mercury removes a hundred doṣas, Venus two hundred, Jupiter a lakh; lagna lord and navāṃśa lord in kendra); PG26:C1 v. 34 ṭīkā (Jupiter in kendra cancels kṣaya/vṛddhi tithi doṣa; Mercury in kendra cancels tri-spṛśā). **The election tool's statement that no muhūrta-scope cancellation rule exists in the corpus is false of the corpus and true only of the L0 rule table**, whose 60 rows are all natal-scope `[L]` |
| Tārā-bala cycle rule and tārā parihāra | **found** `[D]` | Muhūrta Cintāmaṇi PG67:C1 v. 13: first cycle, tārās 3/5/7 wholly inauspicious; second cycle, the first/middle/last twenty ghaṭīs respectively; third cycle, all auspicious; dāna parihāra per tārā |
| Transit result given ahead of ingress; result by degree-third within a sign | **found** `[D]` | Muhūrta Cintāmaṇi gocara ch. 4 (PG70:C1) v. 17: Sun 5 days, Mars 8, Mercury 7, Venus 7, Moon 3 ghaṭī, Rāhu 3 months, Saturn 6 months, Jupiter 2 months before ingress ("once past 27°"); v. 19 with ṭīkā: Sun and Mars give full result in the first 10°, Venus and Jupiter in the middle 10°, Mercury throughout, Moon and Saturn in the last 10° |
| Guru-bala from the janma-rāśi for initiation and marriage | **found** `[D]` | Muhūrta Cintāmaṇi PG82 v. 46: Jupiter best in 5, 9, 11, 2, 7 from natal Moon; acceptable with śānti in 10, 6, 3, 1; condemned in 4, 8, 12 |
| Moon's twelve avasthās at commencement | **found** `[D]` | Muhūrta Cintāmaṇi PG67:C1 vv. 14–15 (pravāsa, nāśa, maraṇa, jaya, hāsya, arati, krīḍita, supta, bhukta, jvara, kampa, sthiratā; computation given) |
| Ariṣṭa-bhaṅga / cancellation of evils | **found (partial)** `[D]` | Patel PG2299 ("malefics between benefics, benefics in angles and trines … eliminate"); Muhūrta Cintāmaṇi PG115 v. 88 (kartarī cancelled when its malefics are in enemy sign, debilitated or combust); BPHS Ch. 9–10 `[D-prior]` per the Kṣetra plan |
| Bhāva destruction / dusthāna lord results in his daśā | **found** `[D]` | Phaladīpikā XV ślokas 27–29 (PG199:C1): lagna lord gives the effects of the bhāva whose lord he joins; a dusthāna lord in his own other house gives in his daśā only that house's effects; Uttara Kālāmṛta PG77:C1: a bhāva is destroyed when bhāva, lord and kāraka are hemmed by malefics, weak, unaspected by benefics, with malefics in 4/5/8/9/12 from them |
| Bādhaka-sthāna as such | **not found** | `[U]`; the concept note's "no universal bādhaka multiplier" stands |
| Kota-cakra | **not found** | confirms ADJUDICATION-9; ring table stays `uncited_extension` |
| Tithi-praveśa (lunar-return annual chart) | **not found** | confirms `not_in_corpus`; method stays contested |
| Sudarśana cakra daśā nested periods (BPHS 74) | **not surfaced by search** | `[D-prior]` per the Kṣetra plan and concept note; smallest subdivisions OCR-damaged |
| Tājaka muntha, varṣeśa, sahams, itthaśāla | **not surfaced by search** although Tājaka Nīlakaṇṭhī (290 chunks) is ingested | `[U]` until the custodian counts; the Kṣetra plan's warning that directory reads are not counts applies |
| KP sub-lords | **no KP text in the corpus** | `[U]`; KP admission is corpus-gated (D-T2 class) |
| Kālacakra daśā basis and deha/jīva rāśis | **found** `[D]` | BPHS PG594:C1 ("on the Kāla-chakra, prepared on the basis of the pada of the Janma Nakṣatra, the Daśās of the Navāṃśa rāśis and their duration"; effects applied "in a judicious manner" from vol. I); Patel PG1872/PG2020 (first daśā rāśi is Deha and the 9th Jīva for savya nakṣatras, reversed for apasavya) |
| Jaimini Cara daśā construction | **found** `[D]` | Jaimini Sūtras (Rao) PG46 Sū. 28: a rāśi's daśā years = count from the rāśi to its lord's position; PG48: exaltation adds a year, debilitation removes one; Scorpio and Aquarius have two lords (both in sign → 12 years; else the stronger decides); PG198 Sū. 12–13: kendras from Lagna furnish the first daśā; the kāraka daśā counted from Lagna or the 7th, whichever is stronger, forward or backward by odd/even sign |
| Yoginī daśā (Moon-nakṣatra derived) | **not surfaced by search** | `[U]` this session; the concept note cites BPHS 46.195–199 `[A]` |

---

## §3 · The asset cards

Order follows the pipeline's build order (plan §4.1): foundations, judge inputs, stages, projections, services. Each card has the same seven parts: **Today · Defects · Elevated algorithm · Classical basis · Synergy (gives / takes) · Oracles · Disposition in the plan.**

### 3.1 · `ka_dasha_kala` — the clock (F2)

**Today** [S `services/ka_dasha_kala/{service,tree_walk,eligibility}.py`]. A lazy tree walk over seven systems (Vimśottarī, Yoginī, Aṣṭottarī, Cara, Naisargika, Mudda, Kālacakra; Nārāyaṇa absent, reason undocumented). Each period lord is scored against the caller's target lords: exact 0.85, related 0.50, neutral 0.20; branches below a band are pruned at levels 1–3 (the docstring says level 1 only); level-4 leaves are never pruned. "Cross-system agreement" is the number of systems whose surviving interval has the *identical* `(start_date, end_date)`; the consumer divides by 7. A nine-slice "prāṇa grain" inherits the parent's lord. No applicability gate: all seven systems are queried for every chart. KP sub-level passes through. The self-test runs only on the canonical chart with hard-coded targets.

**Defects.** *Astrological:* "agreement by identical boundaries" is meaningless across systems that are different clocks (the consumer's own docstring measured count = 1 on every live query); pruning by lord-match conflates eligibility with lordship; there is no applicability (Aṣṭottarī has entry conditions, Kālacakra follows the janma-nakṣatra pāda, Cara has its own year counts); no competence classes, so a life-stage band (Naisargika) can be compared to a fruition clock. *Computational:* no boundary uncertainty; no alternate start convention; the prāṇa approximation invents precision below the data.

**Elevated algorithm.** F2 is a service with two calls and no scores.
- `period_context(chart, t, system) → {MD, AD, PD, SD, lords, applicability, σ_boundary(t), scenario_id}` and `boundaries(chart, system, level) → [(instant, σ, scenario_id)]`, read from the pinned L1 `chart_dashas` build (build id, ayanāṃśa, tier recorded on every row).
- **Applicability per system, stored once per chart:** Vimśottarī universal; Kālacakra applicable with its savya/apasavya direction and deha/jīva rāśis from the janma-nakṣatra pāda `[D BPHS PG594; Patel PG1872]`; Cara (Jaimini) constructed per the sūtras: a sign's years = count from the sign to its lord, +1 exalted, −1 debilitated, dual lordship for Scorpio and Aquarius, first daśā from the kendras of the stronger of Lagna and 7th `[D Jaimini Sūtras PG46, PG48, PG198]`; Aṣṭottarī conditional, recorded `method_inapplicable` where its entry condition fails (this chart) `[U] for the condition text`; Yoginī `[U]` pending count; Mudda tied to the Tājaka year (admitted with the annual stage) `[U]`; Naisargika a life-stage band, never a predictor; KP = Vimśottarī proportions, shared ancestry declared.
- **Competence class** on every system: `fruition_clock` (Vimśottarī, Yoginī, Aṣṭottarī), `arena_clock` (Cara), `jurisdiction_clock` (Kālacakra: health, life-force), `annual_clock` (Mudda), `life_stage_band` (Naisargika), `sub_lord_refinement` (KP). Comparison is permitted only within a class; across classes the systems compose (actor × stage), never agree or disagree.
- **Start-convention scenarios:** the Moon-star start is the default; the Lagna-star start and Satyācārya's "stronger of Lagna, Sun, Moon" are declared variants in the scenario set `[D Horā Sāra PG331; Sārāvalī PG155]`, served as sensitivity, never as a second truth.
- **Uncertainty once, correctly:** boundaries carry σ from birth-time and ayanāṃśa through the one linearisation (`dB = (1−kv)dT + k·dA`); adjacent boundaries move together; sūkṣma and prāṇa are *expressible* from the proportional ladder but license no forecast grain. The sandhi band (3 % of own span) is kept as a declared engineering convention labelled `[U]`; no classical sandhi rule was found.
- **Descriptors F2 exposes for the stages** (computed, not scored): the lord's natal placement class from the lagna (kendra, trikoṇa, 3rd, dusthāna), own/exaltation sign, association with the lagna lord `[D BPHS PG638, PG684, PG694]`; the MD–AD relation (natural and temporal friendship; mutual 6/8 vs kendra/trikoṇa); the lord's transit condition at the period's commencement `[D-prior BPHS 47.5–6]`; the fruition phase (beginning, middle, end by natal drekkāṇa, reversed when retrograde) `[D-prior BPHS 47.3–4]`.

**Classical basis.** BPHS antardaśā chapters `[D]`; BPHS 47.3–6 `[D-prior]`; Jaimini Sūtras 28 and 12–13 `[D]`; BPHS Kālacakra `[D]`; Horā Sāra 31.2 and Sārāvalī Mūla daśā on start conventions `[D]`; Six Views A.2 competence classes `[I]`.

**Synergy.** Gives: permission-per-instant inputs to the judge; applicability states to negative space; segment boundaries to the jury; clock terms to the forecaster; period rows to the dossier and chapter views; sandhi bands to NOW. Takes: the pinned L1 build; birth-time uncertainty from the admitted L1/L4 artifact.

**Oracles.** Boundaries equal the L1 rows byte-for-byte at σ = 0. A birth-time shift moves two adjacent boundaries together (covariance test). Aṣṭottarī on this chart reads `method_inapplicable`, never a row of zeros. The Cara fixture (Aries lord in the 7th → 7 years; exalted → 8) and the Kālacakra savya/apasavya fixture pass. Any field named "agreement" or "score" on an F2 row fails lint.

**Disposition.** Service, re-based (plan §8). Owner of the layer's clock.

---

### 3.2 · `ka_avadhi` — period dossiers (F2 materialised)

**Today** [S `writers/ka_avadhi.py`]. One row per MD and AD across seven systems (no level 3). Lord condition stored as fact *references* (keys only, no values). "Activated promises" are Pratijñā rows whose domain is in a fixed graha→domain table (Mars → career, property, health, disputes), first ten, with no check that the promise overlaps the period in time. Sub-lord modulation is the sentence "AD lord X modulates MD lord Y" with no factor. Quality is the same domain list for every period of a lord. One generic citation. The writer refuses to write unless all seven systems are present.

**Defects.** The graha→domain table is unsourced and makes every Mars period say the same thing; promises attach by lord's domain, not by the lord's role in a mechanism; fact references without values cannot be narrated; nothing about the period's own condition (commencement, phase, relation to the MD lord) is computed; no σ.

**Elevated algorithm.** The dossier is a *view over F2 and F1*, re-shaped under the same id. Per period row: (1) the lord's natal condition with fact ids *and values* (dignity, house from lagna, combustion, retrograde, strength tier); (2) the placement class and the relation to the lagna lord `[D]`; (3) the MD–AD relation (for AD rows); (4) condition at commencement: the lord's transit sign, house and dignity at the period's start instant, read from the sky substrate `[D-prior 47.5–6]`; (5) the three fruition sub-intervals (beginning, middle, end) with the lord's natal drekkāṇa and motion `[D-prior 47.3–4]`; (6) attached mechanisms: F1 mechanisms in which the lord participates as lord, dispositor or kāraka, with each mechanism's own event classes and signed role; no domain table; (7) boundaries with σ and scenario id. Every undeterminable field is a typed null. No score, no quality label.

**Classical basis.** As 3.1, items 2–5.

**Synergy.** Gives the STORY, NOW and EXPLAIN views their period rows; shares its descriptors with the judge's P1 period anchor. Takes F2 and F1 only.

**Oracles.** Changing Mars' natal dignity changes only Mars-period rows. A mechanism that does not involve the lord never attaches. The commencement transit condition equals the sky substrate at the boundary instant. Two periods of the same lord with different commencement conditions differ.

**Disposition.** Re-purposed in place as F2's data asset; writer rewritten as a projection; the failed-build diagnosis becomes moot.

---

### 3.3 · `ka_yojaka` — the promise bridge (F1)

**Today** [S `writers/ka_yojaka.py`, `services/ka_yojaka/{classifier,binder}.py`]. Each L2 MSR signal is classified into one of eight signature classes by `signal_type_class`, bound to a template (`template_version v1.0`) that names a daśā rule and a transit trigger as *labels* (kendra/trikoṇa lists, orb 1.0°, aspect set 0/60/90/120/180, veto strings) which no consumer reads. Constituent lords are resolved by a five-step chain (yoga firings; config keys; a `on_<Sign>` regex; the first alphabetic token of a constituent fact; else `always_on`). Strength hook = dignity × normalised ṣaḍbala; CGM centrality and CDLM linkage default to 0.5; "multi_system_confirmation_count" is the number of distinct *ayanāṃśas* in Pratijñā rows for the first listed domain. The distribution-yoga threshold of six grahas is justified by "the observed data". Predicates carry no target longitude.

**Defects.** *Astrological:* the universe of promise is the L2 reading's selection, not the chart (§N.5; concept K11); a cancelled yoga is absent rather than signed; no frame; no exceptions; "confirmation" counts conventions, not methods. *Computational:* label-only triggers; three 0.5 defaults; string heuristics for lordship; a bridge whose rows outlive the signals they point at.

**Elevated algorithm.** F1 builds the chart's **signed mechanism graph** from L1 facts and versioned L0 rules, and lets L2 *attach*.
- **Nodes:** grahas, bhāvas, rāśis, nakṣatras, yoga and doṣa formations from `ga_yoga_firings` with `fired / partial / cancelled` state, kārakas (Parāśara and Jaimini), ārūḍhas, special lagnas, sensitive points, varga positions where the rule needs them. Every node carries its `fact_id`s.
- **Edges (signed, typed, frame-bearing):** lordship, occupation, classical aspect (per-graha table, nodes cast none), dispositor chain, kāraka role, yoga constituency, **cancellation** (bhaṅga: sign −, keeps polarity), **exception** (a rule's own apavāda), argalā/obstruction (as intervention, BPHS 31.2–9 `[D-prior]`). Each edge: `rule_id`, `rule_version`, `provenance`, `frame ∈ {lagna, moon, arudha, graha:X}`, `applicability`.
- **Mechanism:** a named subgraph with a role per participant and a signed support/oppose/condition relation to an **event class**; the mechanism → event-class mapping is a separate reviewable table with a source per row (no keyword inference). `missing_fact` and `evaluated_empty` are distinct states.
- **Attachments:** MSR, CGM and Pratijñā rows attach to mechanisms (many to one) by deterministic id; a reading may omit a mechanism; absence of an attachment is never denial.
- **No scalar strength.** Dignity, ṣaḍbala, avasthā are descriptors read by fact id; the judge and jury decide what they mean under a cited rule.
- **Promise route** per event class = the mechanisms with their signed roles, the preconditions, and the cancellations in force; this is what the judge's P1–P9 natal-fact rows, the negative-space producer and the forecaster's structural term all read.

**Classical basis.** Formation and cancellation rules already in L0 (`bg_yogas`, `bg_rules`, `ga_yoga_firings`); BPHS 31.2–9 for argalā `[D-prior]`; cancellation as a signed first-class operation per BPHS Ch. 9–10 `[D-prior per the Kṣetra plan]`.

**Synergy.** Gives: natal-fact rows to the judge (R-3), cancellations and exceptions to negative space, claim attachments to the jury, promise nodes and routes to the forecaster, lord participations to the dossier. Takes: L1 facts, L0 rule versions, L2 attachments.

**Oracles.** Removing an L2 signal leaves the graph unchanged; removing an L1 fact flips its mechanisms to `missing_fact`. A cancelled yoga is present with sign −. Two MSR signals for one configuration attach to one mechanism. No default value exists anywhere (lint). No predicate without a target identity.

**Disposition.** Stage writer under the same id; table re-shaped by strangler columns.

---

### 3.4 · `ka_vighnakara` — negative space

**Today** [S `writers/ka_vighnakara.py`]. Five detectors run at every anchor (the top 500 convergence peaks plus up to 200 daśā-midpoint anchors that depend on `date.today()`): transit Saturn/Rāhu in dusthānas from lagna or Moon (weights 0.40–0.65), Rikta tithi (0.35), transit Moon in gaṇḍānta (0.55), pāpakartarī of the lagna *sign* by transit Saturn/Mars/Rāhu (0.50), transit Mars/Saturn combust (0.30). Severity thresholds (≥ 0.70 severe) make "severe" unreachable. `override_score = score × 0.45`. No daśā veto exists; two detectors are "reserved".

**Defects.** *Astrological:* a muhūrta tithi rule and a daily Moon gaṇḍānta are applied as natal obstructions; transit combustion of Mars or Saturn is not an obstruction doctrine for the native; pāpakartarī is tested on the lagna sign rather than the bhāva and lord concerned; no release conditions; no exceptions (Saturn in 3/6/11 from Moon is favourable in the same gochara chapters that make 12/1/2 adverse); the anchors are Saṅgam's peaks, so the detector inherits Saṅgam's defects. *Computational:* invented weights; unreachable severity; today-dependence.

**Elevated algorithm.** The asset becomes the layer's **negative-space producer**: per `(event_class, interval)` it emits one of six typed states with provenance, never a number.
- Inputs: the judge's vedha interval relation (active, vipareeta-cancelled, inactive; exception pairs) and its `evidence_against` records (adverse rule paths and their exceptions, e.g. BPHS 70.12–14 `[A]`); F1 cancellations, exceptions and ariṣṭa-bhaṅga protections (benefic in kendra, Jupiter's aspect) `[D Patel PG2299; D-prior BPHS 9–10]`; F2 applicability; structural bhāva-destruction conditions (bhāva, lord and kāraka hemmed by malefics, weak, unaspected by benefics; malefics in 4/5/8/9/12 from them; navāṃśa lords inimical, combust or defeated) `[D Uttara Kālāmṛta PG77]` and the dusthāna-lord-in-own-house rule `[D Phaladīpikā XV 27–29]`; pāpakartarī of the concerned bhāva or lord, from the judge's records.
- States: `outside_risk_set · method_inapplicable · information_unavailable · evaluated_silent · obstruction_active {what, by_what, scope ∈ {structural, transit, period}, interval, release_condition} · measured_lower_rate` (the last only from the forecaster's evaluation). A cancelled obstruction is `obstruction_active` with a `cancelled_by` and the cancellation's own interval, so the contest is visible.
- Release conditions are computed, not narrated: transit exit instant (from the sky substrate), onset of the protecting aspect, the period boundary that ends a daśā veto.
- Daily pañcāṅga doṣas (Rikta tithi, gaṇḍānta-of-the-day, kulika) leave this asset and live in the election view, where Muhūrta Cintāmaṇi's cancellation verses apply (3.14).

**Classical basis.** Vedha: Phaladīpikā XXVI (judge-owned, verified in L0). Protection and cancellation: Patel PG2299 `[D]`, BPHS 9–10 `[D-prior]`. Bhāva destruction: Uttara Kālāmṛta PG77 `[D]`; Phaladīpikā XV `[D]`. No universal bādhaka multiplier (`[U]`).

**Synergy.** Gives: contest sources to the jury (reported, never netted), scoped suppression distinctions to the forecaster, the "what obstructs" layer to NOW and EXPLAIN, release dates to AHEAD. Takes: judge records and vedha intervals, F1, F2.

**Oracles.** A planted vedha yields `obstruction_active` whose release equals the vedha interval end. A planted Jupiter-kendra protection yields a cancelled row, not silence. Missing vedha data yields `information_unavailable`, never "clear". A Rikta tithi produces no natal row (the mutation that adds one fails). No numeric weight exists (lint).

**Disposition.** Stage writer under the same id; table re-shaped.

---

### 3.5 · `ka_kalasutra` — activation intervals

**Today** [S `writers/ka_kalasutra.py`, `services/ka_temporal/date_resolver.py`]. For each predicate, the convergence row with the highest score (strict `>`, so ties go to read order) supplies a peak; the window is the peak ± a half-width by class (yoga 7, doṣa 14, else 5 days) or, without a peak, each matching Vimśottarī period's full span with a midpoint "peak"; predicted dates at peak ± 3 days with strength `1 − 0.2·|δ|` or at period start/middle/end with 0.6 / 1.0 / 0.4; at most eight periods (the earliest ADs); proximity = dignity × ṣaḍbala, identical across periods; `today` is implicit.

**Defects.** The half-widths and date strengths have no source; a period midpoint has no doctrine; proximity is natal strength, not timing; the eight-match cut drops later recurrences; the implicit `today` makes the output non-reproducible. The only doctrinal content (a yoga fruits in the daśā of its constituents) survives.

**Elevated algorithm.** A SQL projection. For each F1 mechanism attached to an L2 signal: intervals = the judge's evaluated windows whose relationship records name the mechanism's participants as agent or object, intersected with F2 periods whose lord is a participant (the surviving doctrine), each interval carrying its `contact_id`s, the period anchor and the judge's coverage. The recurrence ladder is the ordered set of those intervals across the searched horizon, with `unsearched` where coverage ends. No half-widths, no strengths, no proximity, no cap, explicit `as_of`.

**Classical basis.** Daśā of a yoga's constituents gives its fruit `[A]` (standard; to be pinned to its BPHS locator in the stage brief); everything else is the judge's.

**Synergy.** Gives NOW/AHEAD their per-structure intervals and the recurrence ladder. Takes judge windows, F1, F2.

**Oracles.** Two mechanisms sharing one contact show the same `contact_id`. An interval outside judge coverage reads `unsearched`. The ladder has no fixed length.

**Disposition.** Projection writer.

---

### 3.6 · `ka_kala_darshana` — the published view

**Today** [S `writers/ka_kala_darshana.py`]. Top 750 convergence rows; `effective = conv × (1 − max override)`; a NULL convergence becomes 0.5; labels at 0.70 / 0.45 / 0.20; rows 501–750 can never carry an obstruction because the detector scanned 500; daśā-anchored obstructions never join; the narrative is fixed strings with a precedence bug that drops rarity and mode when orb strength is falsy.

**Elevated algorithm.** A projection over the publication manifest: per `(event_class, interval)` the judge's window with its three valence fields, the jury's `D(W)` with witness signature and segment support, the negative-space state, the forecaster's alignment surprise where present, and a `tier` column carrying `operator_role` and qualification for density layering. No composite, no label, no default; narration happens at serve time from these fields.

**Oracles.** Every published interval has a negative-space row. No row exists without a judge window. No numeric composite column exists.

**Disposition.** Projection writer.

---

### 3.7 · `ka_jivana_parva` — life chapters

**Today** [S `writers/ka_jivana_parva.py`]. MD and AD rows (plus the current PD) from Vimśottarī; `high_convergence_count` and `avg_effective_score` from convergence windows inside the span (a table now empty); quality labels `peak / building / consolidating / receding / transitional` from average thresholds (0.55, 0.60, 0.45, 0.25), with "ongoing" including the future; theme keywords from a hard-coded planet table; AD narratives pass "MD/AD" as the planet and fall back to "transformation".

**Defects.** The labels grade a dead number; the themes are invented; the thresholds are acknowledged in code as compensating for an upstream defect; the as-of date is implicit.

**Elevated algorithm.** A projection over F2 and the stages. A chapter is an F2 period (MD, AD) carrying: the dossier descriptors (3.2); the mechanisms active in it (F1 participants of the lord) and the judge windows, jury turning points and negative-space states inside its span; the LEL events pinned (kept, with the existing circularity guard). "How this chapter differs from the last" is a **diff**: mechanisms present in both, mechanisms new, participants and conditions that changed, with σ on the boundaries. Themes are the event classes of the attached mechanisms from the ontology, not planet keywords. No quality label. Explicit `as_of`.

**Oracles.** Removing the convergence table changes nothing. Two chapters with the same attached mechanisms diff to empty. An AD chapter names its own lord.

**Disposition.** Projection writer; serving fix for the stale counts lands first (review F-L2).

---

### 3.8 · `ka_bhavishya_lekha` — issued forecasts

**Today** [S `writers/ka_bhavishya_lekha.py`]. Up to 100 darshana rows within five years become projections with tiers at 0.70 / 0.45; domain by keyword match with order shadowing (`fifth` → education before progeny); a generic ±21-day falsifier text; a robust outcome-preservation discipline under an advisory lock (kept rows keep their ids; protected rows fail closed). The seed still says "3-year horizon, up to 50".

**Defects.** Tiers are thresholds on a structural score read as probability (the code's own F-BHAV-2 note says so); domains by keyword; the falsifier is not the event's observation predicate; one row per darshana row multiplies forecasts for one event.

**Elevated algorithm.** The **registrar of `issued_forecast`**: one forecast per event identity `(event_class, phase, affected_person, episode)` from jury-attached claims; `issued_at`, `information_cutoff`, pipeline manifest reference; intervals (disconnected allowed) with the disclosed grain = weakest of computation, source-licensed and empirically supported resolution; a declared point functional; `probability_target` null unless the forecaster's calibration status for the class is `calibrated`; the falsifier is the event class's observation predicate from the ontology; registration in Samīkṣā only for prospective forecasts. Never edited: a refinement issues a new forecast with a new cutoff. The outcome-preservation discipline is kept as is.

**Oracles.** A re-run with unchanged inputs changes no existing forecast. A refined window creates a new id and leaves the old one. No forecast carries a probability while its class is uncalibrated. Domain never comes from a keyword.

**Disposition.** Registrar writer (append-only by identity).

---

### 3.9 · `ka_taranga` — the shape of the year

**Today** [S `writers/ka_taranga.py`, `services/taranga_kernel`, `services/taranga_service.py`]. Monthly 1950–2100: harmonic mean of a domain-match term (1.0 if the MD lord's domain table lists the domain, else 0.15), the mean convergence score that month and the mean Pratijñā grade / 10; the event-class scope is degenerate by construction (the domain gate is a tautology). The Sade-sati claim in the docstring has no Saturn term. The live service uses a different, additive formula (cos² currents + daśā cap + SAV). The W2 decision to drop the event-class half is unimplemented. The graha→domain table has eleven names outside the canonical thirteen.

**Elevated algorithm.** A projection: per `(domain, month)` the integral of the forecaster's compact field over the month (`∫λ`, domain scope only), beside a separate count of judge windows active in the month. No blending, no harmonic mean, no domain table. The live service retires.

**Oracles.** The monthly integral equals the sum of segment integrals clipped to the month. Duplicate insertion changes nothing.

**Disposition.** Projection writer.

---

### 3.10 · `ka_tulana` — priority

**Today** [S `services/ka_tulana/ranker.py`]. A linear composite with ratified weights (convergence 0.40, rarity 0.25, confidence 0.20, proximity 0.15), rarity capped at 30 years, a piecewise proximity curve, `compare(A, B)` with ties to A and three recommendations; no dignity down-ranking despite the tool text; accepts only Saṅgam modes A and B; **not called by the priority tool**.

**Defects.** One composite over incommensurable quantities (the product definition's "salience monoculture"); fixed weights; inputs that no longer exist.

**Elevated algorithm.** A ranking *service* over typed inputs: the jury's `D(W)` with coverage, the negative-space state, the forecaster's salience axes (informativeness, consequence, relevance, reliability, actionability) and the caller's question frame. Output is a **Pareto front** with the lexicographic order the caller declares (`nearest`, `strongest`, `most_robust`, `best_suited`), ties and incomparability preserved; `compare(A, B)` returns the dominance table; dissonance is the presence of contest rows. No weights.

**Oracles.** Swapping A and B swaps the result. A window with `information_unavailable` never outranks one with `evaluated_silent` on the safety axis. No fixed weight constant exists (lint).

**Disposition.** Service, re-based and wired to PRIORITY (plan R-6).

---

### 3.11 · `ka_gochara_resonance` — transit targets

**Today** [S `services/ka_gochara_resonance/writer.py`, `gochara_grammar/derived_points.py`]. Per event class (26; birth_anchor excluded): targets from the ontology's signature houses, lords and kārakas (weight 1.0), `mechanism_node` rows from `bg_transit_rules` with weights (favourable 1.0, unfavourable −1.0, vedha 0.3, double-transit 0.75, else 0.5), sensitive degrees 0.5 (positive checks only, after R-1), ārūḍhas 0.6, yoga constituents 0.7, daśā-lord portfolio 0.8 (always a subset of the kārakas), gulika/māndi and yamakaṇṭaka derived points 0.5 (Phaladīpikā XVII.26 cited). First root wins per `(target_type, target_ref)`. **Frame defect:** the ontology's signature houses (counted from the lagna) are joined directly to `bg_transit_rules.primary_house`, which L0 documents as counted from the Moon; `mechanism_node` rows are always stamped `resolved`.

**Defects.** Weights on targets pre-judge the rule; one physical target with two roles is deduplicated to one role (the family-coordination note's "role edges, not independent observations" is violated at the source); the frame mismatch silently mis-targets every mechanism-node row; the daśā-lord portfolio duplicates the kāraka set.

**Elevated algorithm.** Resonance becomes the **projection of F1 onto the judge's relationship records**: for each event class, every physical object (point, span, star, derived point) that a promise route's mechanism names, with `frame` typed (`lagna | moon | arudha | graha:X | bhavat_bhavam:h`), `role` typed (house, lord, kāraka, ārūḍha, yoga constituent, daśā lord, sensitive point, derived point), the mechanism id, the rule id and provenance. **No weight column**: the judge's rule paths decide what a contact to a target is worth. One physical object with several roles is one object with several role edges (the judge's `contact_id` then carries them all). The derived points keep their Phaladīpikā locators.

**Classical basis.** Signature houses and lords per class from the ontology (its own citations); Phaladīpikā XVII.26 and yamakaṇṭaka ślokas for the derived points (already verbatim in code) `[S]`; frames per the judge's spec §0.

**Synergy.** Gives the judge its target set (R-3); takes F1 and the ontology.

**Oracles.** The marriage class's 7th house resolves to a lagna-frame span, and a Moon-frame transit rule to a Moon-frame target (a frame-mixing mutant fails). One physical target with two roles yields one object and two edges. No numeric weight exists.

**Disposition.** Folded into F1 (K2); writer retired after the judge reads F1 directly.

---

### 3.12 · `ka_vedha_gochara` — vedha as intervals

**Today** [S `services/ka_vedha_gochara/{logic,gate,writer}.py`; L0 `l0_transit.py`, `l0_phaladeepika_vedha.py`]. Three mechanisms over a rolling −60/+400-day horizon, one ayanāṃśa offset computed at `today` for every day. *House vedha:* 36 cited pairs from the Moon (Phaladīpikā XXVI ślokas 3–8, PG322–323) plus 6 unsourced Rāhu/Ketu pairs; occupants are every other graha including the Moon and the nodes; Sun↔Saturn and Moon↔Mercury excepted first; a *vipareeta* cancellation carved from any companion sharing the primary's sign, stamped `translator_commentary`; the malefic-count grade removed by ruling (PG353 is a battle scale; PG349's general scale not seeded). *Sarvatobhadra:* an algorithmic approximation with a stale disclosure string; the grid table is empty by ruling. *Lattā:* 8 rows (PG338–339; Ketu absent; multi-lattā ślokas 47–48 not implemented). The intervals live inside a JSON column; a dedicated interval table is deferred. **Divergences from the judge's own vedha derivation:** the judge produces no vipareeta (no served citation), treats node obstructors as `unqualified`, and excludes the Moon as a stored obstructor; this writer does the opposite on all three.

**Defects.** Two definitions of vedha in one layer; a constant ayanāṃśa offset across 461 days; a rolling horizon with no coverage disclosure; vipareeta served at the same tier as cited vedha; the approximation stamped with a classical citation it was told not to carry.

**Elevated algorithm.** One definition, the judge's `vedha_interval_relation`, produced once as an adapter over the sky substrate for the century: for each cited pair, the half-open intersection of the primary's residence in house *h* from the Moon with the obstructor's residence in the vedha house, with states `active | inactive`, the two exception pairs applied, node obstructors `unqualified`, the Moon excluded as a stored obstructor (Mercury–Moon exception retained), and `coverage` on every answer. Vipareeta is emitted as **testimony** with `source_qualification = translator_commentary` until a served verse exists; it never attenuates. Lattā rows are `verse_cited` (PG338–339) with the Ketu gap declared and ślokas 47–48 (multi-lattā severity) as an enrichment row. Sarvatobhadra is `method_inapplicable` while the grid cannot be populated; the approximation rows retire. Ayanāṃśa per instant through `kala_core.ayanamsha`. A dedicated interval table replaces the JSON column. The freshness digest over the L0 inputs is kept.

**Classical basis.** Phaladīpikā XXVI 3–8 (L0, 36 rows verified by the Kṣetra review row by row); PG322–323 exceptions `[S]`; PG338–339 lattā `[S]`; PG353/PG349 scales deliberately unused (D-PG353).

**Synergy.** Gives the judge's P2 attenuation operand (today `VEDHA_SOURCE = None`, so every P2 record is `unqualified`), the negative-space producer's obstruction intervals, and the forecaster's suppression primitive. Takes the sky substrate and L0 rules.

**Oracles.** Sun–Saturn never obstructs each other. A node obstructor yields `unqualified`, never `active`. Interval equality with the judge's independent vedha oracle on a fixture. A century coverage manifest; a request outside it reads `unsearched`.

**Disposition.** Adapter, aligned to the judge (plan §8); the single vedha producer for the layer (Kṣetra ruling 8).

---

### 3.13 · `ka_moorti_nirnaya` — transit quality

**Today** [S `services/ka_moorti_nirnaya/{logic,writer}.py`; L0 `bg_transit_moorti`]. For each sign run of eight grahas (never the Moon), the Moon's nakṣatra at the ingress instant, counted from the janma nakṣatra, gives an offset 1–27; `offset mod 4` gives svarṇa (1), rajata (2), tāmra (3), loha (0), with 27 set to tāmra "per Phaladīpikā". Instant-grain roots via the kernel's arc index, but the arcs are built at UT midnight while the kernel convention and the daily ephemeris are noon UT (a 12-hour epoch mismatch). Rolling 461-day horizon. The module itself records that the mūrti rule form "is NOT present in the served corpus", and the project's value architecture flagged that the tradition's commonly cited rule is a **12-house Moon-relative** table (1/6/11 svarṇa, 2/5/9 rajata, 3/7/10 tāmra, 4/8/12 loha), not a 27-nakṣatra cycle. The corpus check this session did not surface either form.

**Defects.** Method identity contested and uncited; epoch mismatch in instant grading; `corpus_verifiable` false on every row while the NOW view serves it as computed.

**Elevated algorithm.** Two **declared conventions**, both computed, neither scored: `moorti_nakshatra_27` (today's) and `moorti_rasi_12` (the Moon's sign at ingress counted from the janma rāśi) `[U]`, each with a `convention_id`; the row carries `method_qualification = method_contested` until the corpus custodian adjudicates. Ingress instants come from the sky substrate's `sign_ingress` events (one solver, one epoch). The judge may use mūrti only as `testimony` (already D-PADMIT); the negative-space producer may use loha only as a *reported* factor, never a suppression. Horizon = the century domain.

**Classical basis.** `[U]` on both conventions; BPHS Ch. 28 and Phaladīpikā 26 are cited in code without locators.

**Synergy.** Gives testimony to the judge and a reported factor to negative space; takes sky events and the Moon's position at the instant.

**Oracles.** Ingress instants equal the sky substrate's roots. Both conventions present on every row; a frame mutant (Moon longitude vs Moon sign) changes the tier. No consumer scores a `method_contested` row (lint).

**Disposition.** Adapter, gated (plan R-8).

---

### 3.14 · `ka_kota_chakra` — the fort

**Today** [S `services/ka_kota_chakra/{logic,writer}.py`; L0 `bg_kota_chakra_rings`]. Ring partition from the janma nakṣatra (stambha {4, 11, 18, 25}; durgāntara {3, 5, 10, 12, 17, 19, 24, 26}; prakāra {2, 6, 9, 13, 16, 20, 23, 27}; bāhya the rest, so the janma nakṣatra itself is bāhya) — a tier-(iii) transcription with `corpus_status = not_in_corpus`; posture × nature table "this writer's own synthesis"; static benefic/malefic (no waxing Moon, no Mercury association); no direction of motion; no node-series predicate on the ephemeris read; horizon not overridable. Every row `uncited_extension`.

**Defects.** Uncited ring table; no entry/exit (dvāra) direction, which is the point of the fort reading; static nature table that disagrees with the judge's own `nature.py`.

**Elevated algorithm.** Keep as an adapter emitting **testimony only**, with: nakṣatra-ingress events from the sky substrate (century; one epoch); nature from the shared `gochara_rules/nature.py` (waxing Moon benefic, Mercury by association); **motion direction** (entering toward stambha vs exiting toward bāhya) as a typed field; the kota-svāmī and kota-pāla reserved (null) until a source is admitted; `uncited_extension` retained on every row until ADJUDICATION-9 closes. No posture × severity synthesis; the four rings and the direction are the facts; the reading is the judge's, if ever admitted.

**Classical basis.** `[U]`; no corpus hit this session.

**Synergy.** Testimony to the judge; a reported factor to negative space.

**Oracles.** Nature equals `nature.py` for the same instant. A row without `uncited_extension` fails until a locator exists.

**Disposition.** Adapter, testimony-only.

---

### 3.15 · `ka_tithi_pravesha` — the lunar-return year

**Today** [S `services/ka_tithi_pravesha/{logic,writer}.py`]. The praveśa instant is the Moon's return to its **natal sidereal longitude** nearest the civil-calendar birthday (`birth + N years`), found by bisection; a chart is cast at that instant; 120 rows; two-pass verification by Moon equality within 0.01°. Citation: `not_in_corpus`. Not computed: Muntha, varṣeśa, the Tājaka yogas.

**Defects.** The name says *tithi* praveśa but the computation is a Moon-longitude return; the anchor is a civil date, not the solar return; the method is uncited and contested, yet NOW serves it as `computed` while AHEAD says `not_in_corpus`.

**Elevated algorithm.** Two declared conventions, both stored, neither scored: `moon_longitude_return` (today's) and `tithi_return` — the instant, nearest the **solar return** (Sun at natal sidereal longitude), when the Sun–Moon elongation equals the natal elongation with the Sun in the natal month `[U]`. Both carry `convention_id` and `method_contested`. The annual chart objects they produce (praveśa lagna, positions) are candidates for the judge's `annual_object_identity` (§9 of the spec) only after corpus admission (D-T2 class). Anchor instants from the sky substrate.

**Classical basis.** `[U]`; neither form surfaced in the corpus.

**Synergy.** Annual objects to the judge once admitted; nothing else reads it.

**Oracles.** For `tithi_return`, elongation at return equals natal elongation within tolerance and the Sun's sign equals the natal Sun's sign. Both conventions on every row. NOW and AHEAD report the same coverage state.

**Disposition.** Adapter, gated (plan R-8).

---

### 3.16 · `ka_sudarshana_varsha` — the three-frame year wheel

**Today** [S `services/ka_sudarshana_varsha/{logic,writer}.py`]. For year *N*, active sign = natal sign + (N−1) mod 12, separately from Lagna, Moon and Sun; `tri_lagna_convergence = (JL == CL == SL)`, which is constant for a chart and true only when the three natal signs coincide; day-grade calendar windows; nested periods explicitly out of scope; no classical citation column.

**Defects.** The convergence flag is meaningless by construction; the wheel is only the first step of the method; no bhāva reading.

**Elevated algorithm.** The Sudarśana cakra daśā as a judge method (enrichment step 2, the native's order): per year and per frame, the active sign, its natal bhāva from each frame, its lord, occupants and aspects (from F1), and the year's reading per BPHS 74 `[D-prior]`; nested **month** (one sign per month) and **day** (two and a half days) sub-periods as F2 rows of competence class `annual_clock` `[D-prior; smallest subdivisions OCR-damaged, read the scan first]`; windows from the solar return, not the civil birthday. The flag is removed. The frame-agreement quantity, if any, is "the same natal bhāva is active from two frames", computed and reported, never scored.

**Classical basis.** BPHS 74 `[D-prior per the concept note and Kṣetra plan]`.

**Synergy.** A judge method and an F2 annual clock; STORY reads the year.

**Oracles.** The active sign has period 12. Month sub-periods partition the year. The constant flag no longer exists.

**Disposition.** Adapter now; judge method at step 2.

---

### 3.17 · `ka_muhurta_seva` and the election view

**Today** [S `services/ka_muhurta_seva`, `muhurat/finder.py`, `panchang_engine/*`]. A whole day scored at sunrise: `100 × min(1, Σ w_f·q_f)` over tithi, nakṣatra and vāra suitability tables per event (eight events), auspicious special yogas (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-puṣya, Tri/Dvi-puṣkara, Siddha), "Jupiter and Venus not combust", and Tārā-bala when a native chart is given (cycle attenuation 1.0 / 0.8 / 0.6, unsourced). Knockout to zero when `rāhu-kālam ∧ yamagaṇḍa ∧ tithi ∈ {4, 8, 9, 14, 30} ∧ Saturday`; since the first two exist every day, this is "Saturday and śukla 4/8/9/14 or amāvāsyā". Weights from a YAML whose defaults sum to 0.95; a declared `avoid_penalty` never read; Chandra-bala and the 60/40 combination implemented but unused; a hard-coded "active daśā lord = Jupiter" that contradicts the pinned Mercury period and is read by nothing; no lagna; no intra-day interval. The election view reports residual doṣas "uncancelled" because the L0 rule table has no muhūrta-scope cancellation rows (60 rows, all natal).

**Defects.** Day-grain only; a weighted sum of incommensurables; a hard zero instead of a doṣa; the tārā cycle rule invented; **the cancellation doctrine exists in the ingested corpus and was never extracted**.

**Elevated algorithm.** Election over qualified methods, per Product §3.11 (general calendar, personal suitability and outcome expectation kept apart).
1. **Candidate intervals, intra-day:** muhūrta lagnas (sign rises) and horās within the searched days; the whole-day score retires.
2. **A doṣa ledger per candidate**, typed rows with locators: tithi–nakṣatra combinations `[D MC PG19 vv. 11–13]`; dagdha, viṣa and hutāśana vāra × tithi yogas `[D MC PG17 v. 8]`; śūnya nakṣatras and rāśis by month `[D MC PG19 vv. 14–16]`; Vyatīpāta, Vaidhṛti, Bhadrā, kṣaya and vṛddhi tithi, kulika, pāta, the first ghaṭīs of Viṣkambha and Vajra `[D MC PG26 v. 34]`; the eclipsed nakṣatra by obscuration `[D MC PG26 v. 33]`; Rikta tithis; the Parigha/Śūla/Gaṇḍa/Vyāghāta ghaṭīs `[D MC PG26 v. 35]`.
3. **Parihāra applied as cited**, row by row, producing the residual: lagna with Moon and Sun strength cancels ekārgala, upagraha, pāta, lattā, yāmitra, kartarī and udayāsta `[D MC PG110 v. 68]`; kartarī exceptions `[D MC PG115–116 v. 88]`; Mercury, Jupiter, Venus strong in kendra or trikoṇa cancel the year, ayana, season, tithi, month, nakṣatra, pakṣa, dagdha-tithi and lagna doṣas `[D v. 89]`; Jupiter in kendra, trine or 11th, the Sun in upacaya, the Moon in the lagna, vargottama or the 7th destroy all doṣas `[D v. 90]`; the graded "hundred / two hundred / a lakh" and the lagna-lord-and-navāṃśa-lord-in-kendra rule `[D v. 91]`; Jupiter in kendra cancels kṣaya/vṛddhi-tithi, Mercury in kendra the tri-spṛśā `[D PG26 v. 34 ṭīkā]`. This requires an **L0 extraction** into `bg_parihara_rules` with `scope = muhurta` and the exact locators; until then the view keeps saying "uncancelled" honestly.
4. **Tārā-bala by cycle** `[D MC PG67 v. 13]`: first cycle, tārās 3/5/7 wholly inauspicious; second cycle, their first, middle and last twenty ghaṭīs respectively; third cycle, all auspicious; the dāna parihāra as remedy text. The 1.0/0.8/0.6 attenuation retires.
5. **Guru-bala and Śukra-bala** for marriage and initiation from the janma rāśi `[D MC PG82 v. 46]`; **Moon's avasthā** at commencement reported `[D MC PG67 vv. 14–15]`; the planetary factor re-based on the sign-phase rules (first/middle/last ten degrees; anticipation before ingress) `[D MC PG70 vv. 17, 19]` instead of "Jupiter and Venus not combust".
6. **Personal layer, separate:** the native's judge windows and negative-space states for the undertaking's event class, the F2 period applicability, and the pañcāṅga's janma-nakṣatra / janma-tithi avoidance `[D MC PG26 v. 34]`; served beside, never summed with, the calendar layer.
7. **No composite.** A candidate carries: interval, factors present (cited), doṣas, parihāras applied (cited), residual doṣas, personal layer, uncited factors in their own list.

**Classical basis.** Muhūrta Cintāmaṇi locators as listed (`[D]`, this session); Tārā and avasthā `[D]`; Bṛhat Saṁhitā and Muhūrta Mārtaṇḍa named in code without locators `[U]`.

**Synergy.** Takes the judge, negative space and F2 for the personal layer; gives ELECT and RITUAL their candidates; the daily pañcāṅga primitives (horā, gulika, diśā-śūla) move here from NOW's TypeScript.

**Oracles.** A kartarī whose malefics are debilitated reads `cancelled` with v. 88 cited. A Saturday caturthī produces a doṣa row, never a silent zero. The tārā cycle fixture (second cycle, vipat, 25th ghaṭī) reads auspicious. No weighted scalar exists.

**Disposition.** Service kept; the finder's scoring retires; the view re-bases; one L0 demand (muhūrta-scope parihāra rows).

---

### 3.18 · `ka_graha_sancara` — the sky service

**Today** [S `services/ka_graha_sancara/engine.py`, `scripts/temporal/compute_transits.py`]. Two day-grain paths twelve hours apart in epoch: path A reads the daily ephemeris at noon UT with no node-series predicate (later rows overwrite earlier); path B computes at 00:00 UT with Moshier by default; neither uses the time of day; the supported-ayanāṃśa set excludes `lahiri_chitrapaksha`, the id every other writer uses; naive datetimes are assumed IST; the memo cache lives for one call. No L3 writer calls it.

**Elevated algorithm.** The facade of `kala_core.sky`: instant-grain positions by JD through the arc index with Swiss refinement; one ayanāṃśa policy that accepts the canonical id; the node series pinned and declared; the epoch convention explicit; `applying_or_separating` kept; a cache keyed by `(JD, convention_id)` that outlives a call. Every stage reads the sky through it.

**Oracles.** Both historical paths agree with the solver within tolerance at one JD. The canonical ayanāṃśa id is accepted. A twelve-hour epoch mutant fails.

**Disposition.** Service, re-based; the layer's only ephemeris door.

---

### 3.19 · `ka_sangam` — the jury

**Today** [S `services/ka_sangam/engine.py`, `writers/ka_sangam.py`, `kala_trigger/trigger.py`]. Four modes: A (daśā-eligible windows then aspect events of a class-resolved planet to a target), B (long-horizon sweep without the daśā gate), C (Saturn over the Moon's 12th/1st/2nd, or Mars over signs hard-coded for an Aries lagna), D (Jupiter/Saturn/Mars ingress into signs with SAV ≥ 28, where the SAV map is keyed by *house* and read as *sign*). **No template sets a target longitude, so Modes A, B and TRIGGER measure every contact against 0° Aries.** The I-16 score is Π(necessary) × [1 − Π(1 − wᵢsᵢ)] over thirteen currents, of which ashtakavarga (C7), pañcāṅga, school consensus (C13) and usually Tājaka (C12) are always dropped; the daśā prior is a static 0.5 unless a yoga names constituents; orb strength is cos² with 0.7 when separating; rarity is the planet's period scaled by aspect; confidence labels at 0.75 / 0.45; `independent_current_count` can reach ten. Mode D re-runs for every non-subsystem lifetime predicate and is not de-duplicated (80 % of rows). The trigger composition adds only the suppressive side. The near horizon starts at `date.today()`.

**Defects.** Geometry against the wrong point; dead currents; a static prior; counts of currents presented as independence; row multiplication; Aries-lagna constants; today-dependence.

**Elevated algorithm.** As the pipeline concept note §5 (reconciled with Astra), restated as the jury's contract: reads the judge's assertions, the negative-space states, F1 and F2; writes jury assertions with the **evidence algebra** (roles `selects · conditions · qualifies · corroborates · explains`; a reused root yields no increment; testimony weighs nothing); **declared witness groups** with their shared inputs (G-P the judge's paths; G-J Jaimini on Cara daśā and rāśi-dṛṣṭi `[D Jaimini Sūtras]`; G-T Tājaka behind corpus admission `[U]`; G-K KP behind a corpus `[U]`; G-A Yoginī/Kālacakra/Nārāyaṇa as testimony `[D Kālacakra; U Yoginī]`), admitted sequentially; **elementary half-open segments** with support vectors; the centred agreement measure `D(W)` with a conditional and a whole-pipeline shift null, reported as a surrogate diagnostic where exchangeability fails; turning points, sequences and contests; **canonical forecast attachment** of reading claims. Deleted from code: the ephemeris scan, the symmetric aspect table, Modes A–D as row producers, the static prior, `confidence_*`, `independent_current_count`, `rarity_years`, the Aries constants, the suppressive-only composition. Tests J1–J5 with four-way verdicts.

**Classical basis.** Jaimini Cara construction `[D]`; Kālacakra `[D]`; Tājaka and KP `[U]`; the measurement design `[M]` per the concept note.

**Synergy.** Takes the judge, negative space, F1, F2; gives attachments to the registrar, `D(W)` to the views and ranker, segments to the forecaster.

**Oracles.** The concept note's J1–J5 plus: `W=[0,30), A=[0,1), B=[29,30)` has no joint segment; a universally active witness contributes ≈ 0; a P8-selected window is never G-J-corroborated; no row multiplies with the predicate count.

**Disposition.** Stage writer, rewritten (K4).

---

### 3.20 · `ka_kshetra` — the forecaster

**Today** [S `services/ka_kshetra/*`]. `ln λ = ln λ⁰ + ln P̃ + Σ_s w_s·A_s·r_s(t) + Σ_j β_j·x_j(t) + Σ_m ln(1 − ρ_m·u_m)`. λ⁰ = N_e / 36,525 from six seeded class priors (else a synthetic 1.0 with `baseline_is_synthetic`, a flag persisted only on windows); P̃ = 0.05 + 0.95·P with P a noisy-OR over k-shortest routes through the L2 graph (conductance = L2 `computed_strength`; cancelled edges dropped; `suppressed_by` never populated); twelve covariates (Moon and Lagna contacts, their minimum, AV gate, three mūrti dummies, station, sandhi ±3 days across all systems and levels, syzygy, eclipse, pañcāṅga) with seeded β; suppression ρ per vighna class with a 0.25 default and a raise above 0.95. DHARA null: the envelope term alone is circularly shifted (R = 1024) against fixed clocks and promise, maxima over ten duration buckets, p = (1 + #≥)/1024, q = the pooled 0.95 quantile. Salience = weighted mean of five factors (0.30/0.25/0.20/0.15/0.10) with relevance fixed at 1 and actionability null at build; a lazy-greedy submodular selection of 15 atoms; seven insight detectors.

**Five defects the code does not flag** [S, this session's trace]: (1) **the clock term is always zero** — lord-stack node ids are `graha:Jupiter` while promise-graph nodes are `graha:Ju`, so no lord ever matches a route, `r ≡ 0`, `C ≡ 1`, and `system_concurrent` can never be true; (2) under the seeded weights the Cara clock has weight 0 (key `w_s:chara`, system id `chara_karaka`), as do Aṣṭottarī and KP; (3) `absence_of_expected` can never fire (threshold 6.0 on the grade scale, input a noisy-OR below 1); (4) the reversal insight's obstruction branch can never be true (`signed_obstruction` never changes sign); (5) **no obstructive primitive is ever built in production** (vedha, mūrti and pañcāṅga builders have no caller), so `S ≡ 1`, and the AV gate is a declared coverage gap. Plus the known ones: the J2000 axis under birth-relative arithmetic; chart-wide instead of route-scoped suppression (G3); σ_T floored at 120 s with the quadrature defect; rarity resolved on the krishnamurti ayanāṃśa; Mudda applicability depends on `datetime.now()`; `scarcity` fires for the last window of every class with `gap_days = None`; `contrast` never runs.

**Elevated algorithm.** Per the concept note §6 and the Kṣetra rulings, with the trace folded in:
- **Terms re-sourced, not re-derived:** contacts and stations from the judge's contact ledger (B8-6 keeps Kṣetra's own knots for evaluation only); vedha and mūrti from the adapters (3.12, 3.13); the AV operand from the judge's P5 declaration; sandhi from F2 (per system applicability, not all systems); syzygy and eclipse from the sky substrate; the promise term from F1 routes with **signed** cancellation (no noisy-OR of unsigned conductances; no default conductance); clocks from F2 with weights keyed by the **canonical system ids** and the node vocabulary unified in `kala_core.vocab` so the clock term can be non-zero for the first time.
- **Suppression route-scoped** (ruling 9, Option B), as three typed distinctions (less favourable, delayed, reduced intensity), never inherited multipliers or floors; no `ρ` default.
- **Compact field:** piecewise log-linear segments on the union of knots of the terms actually in the model, with coefficients, risk masks and `∫λ`; dense rows deleted only after byte-equality on sampled instants and integrals.
- **One null, shared:** the shift null runs once per generation over elementary segments shared with the jury, with the exact blocked order-statistic reducer; replicates declared with a power argument.
- **Six classes first** (ruling 1); base rates on two axes (`population_sourced` with citation vs `none`; calibration status `uncalibrated` until prospective data); **odds only** under a declared first-event model and after K2.
- **σ once, correctly:** from F2 (`dB = (1−kv)dT + k·dA`); scenario recomputation near boundaries; parameter, numerical and predictive uncertainty kept apart.
- **Insights with working detectors:** absence on one scale; reversal defined on λ crossing q only; contrast given a declared baseline; scarcity requires a measured gap; concurrence requires `r > 0`, which now can occur.
- **Axis pinned** birth-relative with a detector that fails on today's data; rarity on the canonical ayanāṃśa with the change of meaning disclosed.
- Salience axes kept (I, Q, R, B, A); the composite deferred (concept §6.6).

**Classical basis.** The clock and lord-condition doctrine of 3.1; vedha and lattā as 3.12; life-stage conditioning candidates (naisargika, Ch. 72 thirds) `[A]`; the statistics `[M]`.

**Synergy.** Takes judge, jury, negative space, F1, F2, base rates, F3 through roles; gives `∫λ` to Taranga, alignment to the views, salience to the ranker, the snapshot to the manifest.

**Oracles.** K1–K6 of the concept note, plus: a fixture with a route through `graha:Jupiter` makes the clock term non-zero (the vocabulary mutant fails); the Cara clock weight is non-zero under the seeded table; no obstructive primitive missing when the adapters have rows; `absence_of_expected` fires on a planted high-grade class with zero windows; byte-equality field ≡ compact evaluator.

**Disposition.** Stage writer, re-shaped (K5).

---

### 3.21 · The judge — observations for Pravāha, not a redesign

The frozen spec is the standard the other cards aim at. The trace found facts the stage briefs must carry, which only the steward can act on:
- Only rule paths **P1–P6** exist in code; P7–P9 (the argalā path the jury's G-J relies on, the Tājaka path, and one more) are not implemented. The concept note's "P1–P9" overstates the current catalogue.
- **P5 (aṣṭakavarga) is held** out of the record and window grains; P5a treats a known zero as adverse and any non-zero as `unresolved`; P5c (kakṣyā donor) is disabled pending the L1 contributor matrix.
- `VEDHA_SOURCE = None` in the writer, so every P2 record is `unqualified`; the adapter of 3.12 is what fills it.
- The **default result policy is all-NULL**: under it every numeric field of a `'5.0'` window is NULL and valence is `unqualified`. The candidate is honest by construction, and currently stores no numbers.
- `permission_per_instant` uses MD/AD/PD rows **pinned as literals for the canonical chart**; acceptable under D-SCOPE, a blocker for any second chart; F2 (3.1) is the replacement source.
- P1's categorical factors are `value_mapping_undeclared`; graduated dṛṣṭi windows are `unqualified` under the dynamic-switch rule unless `allow_dynamic`, which the writer never passes.
- The node favourable set in `favourable_houses.py` includes the 10th, which the L0 node rows omit; the L0 node vedha pairs are unsourced.
- The Muhūrta Cintāmaṇi gocara rules found this session (result given ahead of ingress by planet; result by degree-third within the sign) `[D PG70 vv. 17, 19]` are candidate soft factors for P2/P3 and belong in the enrichment register.

---

## §4 · Findings new to this pass (algorithm level)

| ID | Finding | Evidence | Consequence |
|---|---|---|---|
| F-A1 | Kṣetra's clock term is identically zero in production (node-id vocabulary mismatch `graha:Jupiter` vs `graha:Ju`); `system_concurrent` and the concurrence insight can never fire | [S `hazard.py:277`; `stage2_promise.py:117–135`] | the "daśā × gochara" field was never a daśā × gochara field; one vocabulary module fixes it |
| F-A2 | No obstructive primitive is ever built in production; `S ≡ 1`; the AV gate is a coverage gap; mūrti and pañcāṅga builders have no caller | [S `stage1_symbolization.py`] | the stored field has no suppression; G3's route-scoping question is moot until the adapters feed it |
| F-A3 | Seeded clock weights never match the system ids in use (`w_s:chara` vs `chara_karaka`; none for Aṣṭottarī, KP) | [S migration 491; `stage3_clocks.py:285–303`] | canonical ids in `kala_core.vocab` |
| F-A4 | Saṅgam measures every contact against 0° Aries because no template sets a target; Mode D rows multiply per predicate; Mode C uses Aries-lagna constants | [S `binder.py`; `engine.py:1148, 1377, 1557–1567`; `ka_sangam.py:643–660`] | retired with the jury rewrite |
| F-A5 | `ka_dasha_kala`'s "cross-system agreement" is identity of `(start, end)` across systems and reads 1 on every live query | [S `service.py:76–78, 196–213`] | removed; competence classes replace it |
| F-A6 | Vighnakara's severity thresholds make `severe` unreachable (max score 0.65 < 0.70); the daśā veto does not exist | [S `writer:58–60, 128, 144–148`] | replaced by typed states |
| F-A7 | Two vedha definitions coexist: the adapter carves vipareeta, counts nodes and the Moon as obstructors; the judge does none of these | [S `vedha_derive.py:25–55`; adapter `logic.py:291–445`] | one definition (3.12) |
| F-A8 | Muhūrta Cintāmaṇi's doṣa-cancellation verses are in the corpus (PG26, PG110, PG115–116, PG67) but `bg_parihara_rules` has 60 rows, all natal-scope; the election view therefore reports "uncancelled" | [D this session; L live count] | one L0 extraction unlocks election's main gap |
| F-A9 | Resonance joins lagna-frame signature houses to Moon-frame transit rules without conversion; `mechanism_node` rows are always `resolved` | [S `writer.py:823–828, 1172–1178`; `l0_transit.py:166`] | frames typed in F1 |
| F-A10 | Mūrti's instant grading builds arcs at UT midnight against noon-UT knots (12-hour epoch mismatch); the sky service's two paths are 12 hours apart too | [S `moorti/writer.py:228`; `convention.py:19`; `engine.py:173–339`] | one epoch in `kala_core.sky` |
| F-A11 | Kalasutra, Jivana Parva, Vighnakara's daśā anchors and Saṅgam's near horizon depend on `date.today()` / `datetime.now()`; Mudda applicability too | [S several] | explicit `as_of` everywhere |
| F-A12 | The judge stores no numbers under its default all-NULL result policy; P5 held; P2 unqualified without a vedha source; P7–P9 absent | [S `result_policy.py`; `ka_gochara_v5.py:119, 137–144`; `gochara_rules`] | observations to Pravāha (3.21) |
| F-A13 | Tulana validates only modes A and B while Darshana's top-750 is reported as 100 % Mode C; Tulana is not called by PRIORITY | [S `ranker.py:61–62`; review F-L20] | re-based ranker |
| F-A14 | Sudarśana's `tri_lagna_convergence` is constant per chart (true only when the three natal signs coincide) | [S `logic.py:117`] | removed |

---

## §5 · How the cards land in the plan's packets

| Packet (plan §9) | Cards it implements |
|---|---|
| K0 core | the vocabularies that F-A1/F-A3 need; the null-reason and role types every card uses; the sky facade's epoch (3.18) |
| K1 F2 | 3.1, 3.2 |
| K2 F1 | 3.3, 3.11 |
| K3 negative space | 3.4; the adapters' obstruction inputs (3.12–3.14) |
| K4 jury | 3.19; the witness groups' doctrine notes (G-J first) |
| K5 forecaster | 3.20; 3.9 (Taranga) |
| K6 projections and registrar | 3.5, 3.6, 3.7, 3.8 |
| K7 serving plane | 3.10 (ranker wired), 3.17 (election view re-based), NOW/AHEAD consume 3.12–3.16 through the adapters |
| K8 registry and declarations | the `method_contested` and `uncited_extension` qualifications on 3.13–3.15 as declared columns |
| New: **L0 demand** | muhūrta-scope `bg_parihara_rules` rows with the PG locators of 3.17 (an L0 packet, not a Kāla one) |
| Pravāha (not ours) | 3.21 observations; the enrichment-register rows from the corpus register (§2) |

---

## §6 · Questions for the reviewer (algorithm level)

1. 3.1: is a competence-class partition (fruition, arena, jurisdiction, annual, life-stage, sub-lord) the right way to forbid cross-system "agreement", or should the jury's declared dependency groups carry that alone?
2. 3.3: F1 proposes no scalar promise strength at all. Does any stage need one, and if so, under which cited rule would it be computed?
3. 3.4: the six negative-space states are taken from the concept note. Is `obstruction_active` with a `cancelled_by` sub-state sufficient to represent a contest, or should cancellation be its own state?
4. 3.13 / 3.15: computing two conventions and serving both as `method_contested` vs. computing none until adjudication — which is the honest tier for a served surface?
5. 3.17: the Muhūrta Cintāmaṇi parihāra verses are in the vivāha and śubhāśubha chapters. May they be applied to the other undertakings (travel, business, initiation) as the text's general rules, or only to marriage until a per-undertaking source is found?
6. 3.20: with the clock term having been zero in every stored field, is the Kṣetra ablation pre-registration (ruling 10) still the right admission test, or must it be re-registered against a field whose clock term works?
7. 3.21: should the jury's G-J group wait for the judge's P8 (argalā) to exist, or may Cara daśā and rāśi-dṛṣṭi enter as a jury-side method with their own review?

## §7 · What this document does not claim

No predictive validity for any elevated algorithm; no classical locator upgraded from `[U]` to `[D]` without a corpus hit this session; the Tājaka Nīlakaṇṭhī, Yoginī, kota, tithi-praveśa and bādhaka doctrines remain `[U]`; KP has no text in the corpus; the three digests were read as reported and spot-checked where the cards depend on them; the Gochara spec is cited, never reopened.

