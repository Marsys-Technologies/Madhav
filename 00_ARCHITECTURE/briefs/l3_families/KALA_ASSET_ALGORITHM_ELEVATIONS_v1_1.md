---
artifact: KALA_ASSET_ALGORITHM_ELEVATIONS
canonical_id: KALA_ASSET_ALGORITHM_ELEVATIONS
version: "1.1"
status: DRAFT — reconciled against Astra's review (REWORK → this revision); for the native's rulings in reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md §7, then the stage briefs. Research and design only; authorises nothing.
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1); fourth pass: finding-by-finding reconciliation of reviews/ASTRA_REVIEW_KALA_LAYER_PLAN_v1_0.md (gpt-6-astra, xhigh) with independent re-verification of every cited line (reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md §1)'
supersedes: 'KALA_ASSET_ALGORITHM_ELEVATIONS_v1_0.md — retained byte-identical as the reviewed artifact (sha256 8128e5ff0583ae1d8ac2c55932817aa7ad72eea290302ad499a5bd3f509994e7)'
companions: 'KALA_LAYER_VALUE_REVIEW_v1_1.md (evidence) · KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md (the engine these algorithms run in) · reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md (why each change below was made)'
grounded_at: 'code read-only at cooperative-racer @ c751f3bd8; served classical corpus searched live 2026-10-06 (classical_text_chunks, 15–16 texts); local OCR source files under 00_ARCHITECTURE/SOURCE_DATA/classical_texts/ read by line this session'
evidence_labels: "[S] source code read at the named ref · [D] doctrine verified in the SERVED corpus this session, locator given · [D-local] doctrine verified in the project's LOCAL OCR files (BPHS Santhanam vols 1–2, Jaimini Abhyankar, KP Reader V/VI) by line number this session — not yet in the served corpus · [D-prior] verified earlier by the project (document named) · [A] taken from a digest or prior document, not re-read · [U] not found in any corpus available to this session · [L] production measurement by the author · [M] measurement-method literature · [I] design judgement"
depth_standard: 'the Gochara 5.0 elevation (sealed doctrine v3.0 → design specs v1.4 FROZEN + the delegated rulings of 2026-10-02): relationship records with frame and period anchor, rule paths with prerequisites and provenance, three-field valence, permission per instant, vedha as intervals with typed states, coverage, solver uncertainty, oracles with mutations. Every card below is written to reach that shape or to say why the asset should not be a scorer at all.'
changelog:
  - "1.1 (2026-10-06): reconciliation with Astra's review. §2 register: twelve rows upgraded or corrected from the local OCR ([D-local] introduced); KP non-claim corrected (local OCR exists; served corpus does not have it); Muhūrta Cintāmaṇi predicates quoted exactly; PG82 v.46 is Jupiter-only. Cards: 3.1 daśā methods separated (Cara / kāraka-kendrādi / Mūla), competence classes → descriptive tags, invalid Cara fixture replaced; 3.3 cancellation as typed defeat edges, candidate vs effective state, two mechanism routes; 3.4 effective-state algebra, measured rate moved downstream, F1 dependency, release may be unknown; 3.5 no universal lord-period gate, Today corrected; 3.7 condition-aware diff, Today corrected; 3.8 episode vs issue identity, issuance ≠ generation, L4 read → protection contract; 3.9 class integrals, declared mapping; 3.10 incomparability; 3.12 contract reconciled to the judge and NR-VIPAREETA-20261002; 3.13–3.15 legacy preserved and qualified, variants only with a source; 3.16 full BPHS 74 method; 3.17 exact predicates, marriage scope, cancellation_unassessed, Guru-bala only, combustion kept, intra-day boundaries; 3.19 SAV correction; 3.20 two generations (G1 repair / G2 specified replacement), knots kept (B8-6), null estimands separated; 3.21 pinned periods, manifest policy, verifier separation. §4 F-A3/F-A4/F-A7/F-A8/F-A12 reworded. §5 re-keyed to the new packet order. §6 questions answered. §7 corrected."
  - "1.0 (2026-10-06): first version; reviewed by Astra as REWORK."
---

# Kāla — asset-by-asset algorithm elevations

**Written for:** the native, then the sessions that will write each stage brief. Astra's review is incorporated; its remaining open items are the native's (reconciliation §7).

## §0 · What this document does

The layer review found the layer dark at its centre; the code plan designed one engine to replace three. This document says, asset by asset, *what the astrology inside each asset should compute*. For each active asset: the algorithm as it exists today (from the code, constants quoted); its defects; the elevated algorithm as typed inputs → computation → outputs → nulls; the classical basis with each citation labelled by where it was verified; what the asset gives to and takes from the rest of the layer; and the oracle that would fail if the elevation were wrong.

Two things this revision adds to every card where they apply: **the judge's authority includes the delegated rulings of 2026-10-02** (`NR-*`, in `pravaha/decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md`), which accompany spec v1.4 when current semantics are determined; and **"elevated" means a defensible design direction, not predictive validation**. Where a card's "Today" was wrong in v1.0, the correction is marked ⟨corrected⟩.

The judge (Gochara 5.0, frozen) and the jury (concept note §5) are not re-designed here; 3.19 and 3.21 carry only what the other cards depend on.

---

## §1 · The depth standard, in one table

| Dimension | Before (v3.0 and earlier) | After (v1.4 FROZEN + 2026-10-02 rulings) |
|---|---|---|
| Object | one flat per-target score row | physical contact (label-independent identity, occurrence ordinal), relationship record (frame, agent → relation → object, role, period anchor), evaluated window |
| Rule | an implicit weighting | rule paths P1–P6 implemented (P7–P9 specified, not implemented), each with frame, prerequisites in evaluation order, provenance (`verse_cited` / `uncited_extension`), operator role (`scored` / `testimony`); PD-level P1 records are testimony (AM-21 part 4) |
| Valence | one signed number | evidence for, evidence against, valence; occurrence evidence is never outcome valence |
| Clock | a static prior | permission as a function of the instant, read from the pinned L1 daśā build |
| Obstruction | a flag or multiplier | vedha as an interval relation with states `active · inactive · unqualified`, two exception pairs, Moon scope, coverage; no viparīta (ruled) |
| Geometry | daily step scan | boundary events computed once, roots bracketed and Swiss-refined, solver method and uncertainty stored |
| Absence | silence | a coverage object on every answer |
| Numbers | always | by manifest-selected result policy; the current candidate policy is all-NULL |
| Proof | a passing test suite | oracles with fixtures and mutations; a pre-declared evaluation protocol with a held-out registry |

---

## §2 · Corpus check register

Two corpora are distinct and labelled separately: the **served** corpus (`classical_text_chunks`, searched through the project's own tool; `[D]`) and the **local OCR files** under `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` (`[D-local]`; BPHS Santhanam vol. 1 = 33,506 lines, vol. 2 = 50,428; Jaimini Abhyankar; KP Reader V and VI). A `[D-local]` row is a bounded ingestion task for L0, not yet a served citation.

| Doctrine the cards need | Result | Locator / note |
|---|---|---|
| Daśā-sandhi as a stated rule | **not found** `[U]` | Sārāvalī ch. 42 (PG160, PG165) has within-period timing, no junction band; the band stays an engineering convention |
| Antardaśā lord's placement relative to the daśā lord conditions results | **found** `[D]` + `[D-local]` | served: BPHS PG638:C2, PG684:C2, PG694:C2; local: 52.11–14 (BPHS2 12013–12034) — the Sun-daśā / Moon-antardaśā **instance**: "benefics in the 1st, 9th, kendra from the lord of the Dasa"; "the Moon in the 6th, 8th or 12th from the lord of the Dasa". The principle is shown by instance, not stated generally |
| Commencement and fruition phase (47.3–6) | **found** `[D-local]` | BPHS2 8939–8977: first/second/third drekkāṇa → beginning/middle/end; retrograde reverses; Rāhu and Ketu always reverse; favourable if at commencement the daśā lord is in the lagna, exaltation, own or friend's sign. Equal-width thirds are a declared interpretation, not in the text |
| Aṣṭottarī applicability | **found** `[D-local]` ⟨was [U]⟩ | BPHS2 3256–3272 (46.17–20): Rāhu, not in the lagna, in a kendra or trikoṇa from the lagna lord; 3595–3598 (46.23): day birth in Kṛṣṇa pakṣa or night birth in Śukla pakṣa. The sealed Gochara doctrine already treats these conjunctively for this chart |
| Yoginī construction | **found** `[D-local]` ⟨was [U]⟩ | BPHS2 8600–8619 (46.195–199): eight Yoginīs with lords Moon, Sun, Jupiter, Mars, Mercury, Saturn, Venus, Rāhu; years 1…8; (janma nakṣatra + 3) mod 8 selects; balance from bhayāt/bhabhoga. Shares Moon-nakṣatra ancestry with Vimśottarī (jury dependence) |
| Kālacakra: basis and breadth of results | **found** `[D]` + `[D-local]` | served: BPHS PG594:C1; Patel PG1872/PG2020 (deha/jīva). Local: 46.131–134 (BPHS2 6850–6881) — wealth, royal favour, education, family, society. **Kālacakra is not a health clock** ⟨corrects v1.0's competence class⟩ |
| Cara daśā (Jaimini rāśi daśā) construction | **found** `[D]` + `[D-local]` | served: Jaimini Sūtras (Rao) PG46 Sū. 28, PG48; local: BPHS2 7078–7168 (years from the rāśi to its lord, forward for odd, reverse for even; dual lords for Scorpio and Aquarius; ±1 exalted/debilitated; direction from the 9th's pada); Abhyankar introduction 3537–3546. **Kendrādi and kāraka daśā are separate methods** (BPHS2 7717–7877); PG198 Sū. 12–13 belongs to them, not to Cara ⟨corrects v1.0⟩ |
| Alternate nakṣatra-ladder start (Lagna star; Satyācārya) | **found** `[D]` | Horā Sāra ch. 31 v. 2 (PG331:C1); Jātaka Pārijāta 18.33. **Sārāvalī PG155 ("strongest of Lagna, Sun, Moon") is the Mūla daśā rule — a separate system, not a Vimśottarī start variant** ⟨corrects v1.0⟩ |
| Sudarśana cakra daśā (BPHS 74) | **found** `[D-local]` ⟨was [D-prior], "not surfaced"⟩ | BPHS2 43255–43381, 43867–43946: three circles (Lagna, Moon, Sun); judgment by benefic/malefic occupancy and aspect; equal counts decided by strength; **if two or all three of Lagna, Moon, Sun share a rāśi, judge from the birth chart only** (43868–43873); one year per house, month antardaśā, then 2½ days and 12½ ghaṭikā; commencement conditions (benefics in 1/4/7/10/5/9/8) |
| Argalā and virodha (31.2–9) | **found** `[D-local]` | BPHS1 24310–24335: argalā from 4/2/11 (and 5), obstruction from 10/12/3 (and 9); stronger or more numerous prevails; three or more malefics in the 3rd give viparīta argalā; nodes counted in reverse; effects in the daśā of the rāśi or graha concerned |
| Bādhaka | **found** `[D-local]` ⟨was [U]⟩ | BPHS2 10412–10454 (ch. 50 vv. 20–21, pp. 605–606): the 11th from a movable sign is its bādhaka house; a malefic there gives sorrow, imprisonment, disease in its daśā. Movable signs only; no universal multiplier follows |
| Transit result excepted by the running daśā (70.12–14) | **found** `[D-local]` | BPHS2 40952–40970: the adverse Saturn transit "does not take place if a favourable Dasa be in force". A complete rule with its own exception, not a global veto |
| Aṣṭakavarga piṇḍa timing (70.24–27, 30–33) | **found** `[D-local]` | BPHS2 41248–41260, 41537–41558: yoga piṇḍa × rekhās, remainders mod 27 and mod 12 → nakṣatra and rāśi; result when Saturn transits them or their trikoṇas |
| Viparīta vedha | **commentary only** `[D-local]`; **ruled not used** | BPHS1 24418–24442 is Santhanam's note, not a verse; `NR-VIPAREETA-20261002` leaves it out; overturn path = a served locator with a cancellation rule |
| KP sub-lord rule | **found** `[D-local]`; **not in the served corpus** ⟨corrects v1.0 "no KP text in the corpus"⟩ | `KP/kp_reader_vol5_djvu.txt` 2215–2249 (printed pp. 9–11): the star lord signifies the matters, the sub lord decides favourable or adverse; vol. 6 (horary) also present. Ingestion is a bounded L0 task; KP admission stays corpus-gated (D-T2) until then |
| Kota-cakra | **not found** `[U]` | ring table stays `uncited_extension` (ADJUDICATION-9) |
| Tithi-praveśa | **not found** `[U]` | neither the Moon-longitude return nor a phase return surfaced |
| Tājaka muntha, varṣeśa, sahams, itthaśāla | **not surfaced** `[U]` | Tājaka Nīlakaṇṭhī is ingested (290 chunks); the custodian's count is still owed |
| Muhūrta doṣa cancellation (parihāra / apavāda) — **exact predicates** | **found** `[D]` | see §3.17 step 3; all in the **vivāha chapter**: PG110:C1 v. 68; PG115:C2 + PG116:C1 v. 88; PG116:C1 vv. 89, 90, 91 (+C2); PG26:C1–C2 v. 34 ṭīkā (first prakaraṇa, general) |
| Tārā cycle rule | **found** `[D]` | PG67:C1 v. 13: first cycle, vipat/pratyari/vadha wholly inauspicious; second cycle, their first, middle, last **thirds** (the ṭīkā glosses as 20 ghaṭīs of 60); third cycle, all auspicious; dāna per tārā as remedy |
| Guru-bala for upanayana and marriage | **found** `[D]` — **Jupiter only** ⟨corrects v1.0's Śukra-bala⟩ | PG82:C2 v. 46: Jupiter by transit from the janma rāśi best in 5, 9, 11, 2, 7; 10, 6, 3, 1 acceptable (1 after śānti); 4, 8, 12 condemned; stated for a boy's vratabandha and a girl's vivāha |
| Transit result ahead of ingress; by degree-third | **found** `[D]` | PG70:C1 vv. 17, 19 |
| Moon's twelve avasthās | **found** `[D]` | PG67:C1 vv. 14–15 |
| Ariṣṭa-bhaṅga / protection | **found (partial)** `[D]` | Patel PG2299; BPHS Ch. 9–10 `[D-prior]` |
| Bhāva destruction; dusthāna lord in own house | **found** `[D]` | Phaladīpikā XV 27–29 (PG199:C1); Uttara Kālāmṛta PG77:C1 |

---

## §3 · The asset cards

Order follows the plan's build order. Each card: **Today · Defects · Elevated algorithm · Classical basis · Synergy · Oracles · Disposition.**

### 3.1 · `ka_dasha_kala` — the clock (F2)

**Today** [S `services/ka_dasha_kala/{service,tree_walk,eligibility}.py`]. A lazy tree walk over seven systems (Vimśottarī, Yoginī, Aṣṭottarī, Cara, Naisargika, Mudda, Kālacakra; Nārāyaṇa absent, reason undocumented). Each period lord is scored against the caller's target lords (exact 0.85, related 0.50, neutral 0.20); branches below a band are pruned at levels 1–3; level-4 leaves never. "Cross-system agreement" = the number of systems whose surviving interval has the identical `(start_date, end_date)` (`service.py:76–78, 196–211`), divided by 7 by the consumer. A nine-slice "prāṇa grain" inherits the parent's lord. No applicability gate. KP sub-level passes through. Self-test on the canonical chart only.

**Defects.** *Astrological:* identity-of-boundaries is not agreement between different clocks; pruning by lord-match conflates eligibility with lordship; no applicability (Aṣṭottarī has entry conditions, Kālacakra follows the janma-nakṣatra pāda, Cara has its own year counts); nothing prevents a life-stage band from being "compared" to a fruition clock. *Computational:* no boundary uncertainty; no alternate start convention; the prāṇa approximation invents precision below the data.

**Elevated algorithm.** F2 is a service with two calls and no scores: `period_context(chart, t, system) → {MD, AD, PD, SD, lords, applicability, σ_boundary(t), scenario_id}` and `boundaries(chart, system, level) → [(instant, σ, scenario_id)]`, both reading the pinned L1 `chart_dashas` build (build id, ayanāṃśa, tier on every row). **F2 constructs no period itself**; L1 is the producer, F2 the reader and interpreter.

- **Named methods, never aliased.** Each system row carries `method_id` and its L1 producer: `vimshottari` (Moon nakṣatra ladder); `ashtottari` (conditional; entry conditions evaluated separately as satisfied / failed / unknown with the fact ids `[D-local 46.17–20, 23]`); `yogini` (Moon-nakṣatra derived; eight lords `[D-local 46.195–199]`; ancestry shared with Vimśottarī declared); `kalachakra` (janma-nakṣatra pāda, savya/apasavya, deha/jīva rāśis, gati transitions `[D PG594; Patel PG1872]`; results span wealth, education, family, society `[D-local 46.131–134]`); `chara` (Jaimini rāśi daśā: years from the rāśi to its lord, odd forward / even reverse, dual lords for Scorpio and Aquarius, ±1 for exaltation/debilitation, direction from the 9th's pada `[D PG46, PG48; D-local BPHS2 7078–7168]`); `karaka_kendradi` and `mula` are **recorded as distinct methods not built** (`[D-local BPHS2 7717–7877]`; Sārāvalī PG155) — never a flag on Cara or Vimśottarī; `naisargika` (life-stage band, never a predictor); `mudda` (annual; admitted with the annual stage `[U]`); `vimshottari_kp` (Vimśottarī proportions with the KP sub-lord reading `[D-local KP Reader V]`; shared ancestry declared).
- **Start-convention scenarios apply to the nakṣatra ladder only:** Moon-star default; Lagna-star and Satyācārya's "stronger of the two" as declared variants `[D Horā Sāra PG331; Jātaka Pārijāta 18.33]`, served as sensitivity. Mūla daśā is not a scenario of this ladder.
- **Descriptive tags, not a prohibition.** Each method carries tags (`fruition_ladder`, `rasi_period`, `conditional_entry`, `annual`, `life_stage`, `sub_lord_refinement`) plus applicability and dependency metadata (shared ancestry groups). Comparison of the *same outcome* across methods is permitted and is the jury's job; the only prohibition is counting shared-ancestry methods as independent, which the dependency metadata enforces ⟨replaces v1.0's competence classes⟩.
- **Uncertainty once, correctly:** boundaries carry σ from birth-time and ayanāṃśa through one linearisation (`dB = (1−kv)dT + k·dA`); adjacent boundaries move together; sūkṣma and prāṇa are expressible but license no forecast grain. The sandhi band (3 % of own span) stays a declared engineering convention `[U]`.
- **Descriptors exposed, not scored:** the lord's placement class from the lagna, own/exaltation, association with the lagna lord `[D PG638, PG684, PG694]`; the MD–AD relation as the text shows it (placement of the AD lord from the MD lord; 6/8/12 adverse `[D-local 52.11–14, by instance]`); the lord's transit condition at commencement and the fruition phase by natal drekkāṇa, reversed when retrograde and always for the nodes `[D-local 47.3–6]`.

**Classical basis.** As cited inline; the counting convention for Cara (inclusive or exclusive) is a declared parameter pinned in the stage brief against the local text's worked examples.

**Synergy.** Gives: permission-per-instant inputs to the judge; applicability to negative space; boundaries to the jury; clock terms to the forecaster; period rows to the dossier and chapters; sandhi bands to NOW. Takes: the pinned L1 build; birth-time uncertainty from the admitted L1/L4 artifact.

**Oracles.** Boundaries equal the L1 rows at σ = 0. **Perturbation tests:** a birth-time shift moves two adjacent boundaries together (covariance, not marginal σ); a shift that crosses a nakṣatra boundary changes the Vimśottarī and Yoginī ladders together and Cara not at all. Aṣṭottarī on this chart reads `method_inapplicable` with the failed condition named. **Cara fixtures with valid placements:** Aries with Mars in Capricorn (exalted) = base count + 1; Aries with Mars in Cancer (debilitated) = base count − 1; the base count's convention is the one pinned in the brief and the fixture asserts it. Kālacakra savya/apasavya fixture passes. Any field named "agreement" or "score" on an F2 row fails lint.

**Disposition.** Service, re-based (plan §8). Owner of the layer's clock reading.

---

### 3.2 · `ka_avadhi` — period dossiers (F2 materialised)

**Today** [S `writers/ka_avadhi.py`]. One row per MD and AD across seven systems (no level 3). Lord condition stored as fact *references* (keys only, no values). "Activated promises" are Pratijñā rows whose domain is in a fixed graha→domain table, first ten, no overlap check. Sub-lord modulation is a sentence. Quality is the same domain list for every period of a lord. One generic citation. Refuses to write unless all seven systems are present.

**Defects.** The graha→domain table is unsourced; promises attach by lord's domain, not by role in a mechanism; references without values cannot be narrated; nothing about the period's own condition is computed; no σ.

**Elevated algorithm.** A view over **both F2 and F1** (it cannot precede F1 as the full dossier). Per period row: (1) the lord's natal condition with fact ids *and values*; (2) the placement class and the relation to the lagna lord `[D]`; (3) for AD rows, the AD lord's placement from the MD lord `[D-local 52.11–14]`; (4) condition at commencement from the sky substrate `[D-local 47.5–6]`; (5) the fruition phase by natal drekkāṇa and motion `[D-local 47.3–4]` (equal thirds declared as interpretation); (6) attached F1 mechanisms in which the lord participates, with signed roles and effective cancellation status; (7) boundaries with σ and scenario id; (8) applicable rule conclusions and their qualifications where the judge has evaluated them. Every undeterminable field is a typed null. No score, no quality label.

**Synergy.** Gives STORY, NOW and EXPLAIN their period rows. Takes F2 and F1.

**Oracles.** Changing Mars' natal dignity changes only Mars-period rows. A mechanism that does not involve the lord never attaches. **Changing a lord's relevant condition while keeping the period interval changes the dossier.** Commencement condition equals the sky substrate at the boundary instant.

**Disposition.** Re-purposed in place as F2's data asset; writer rewritten as a read model after K1 and K2.

---

### 3.3 · `ka_yojaka` — the promise bridge (F1)

**Today** [S `writers/ka_yojaka.py`, `services/ka_yojaka/{classifier,binder}.py`]. Each L2 MSR signal is classified into one of eight signature classes, bound to a template naming a daśā rule and a transit trigger as *labels* no consumer reads. Constituent lords by a five-step chain ending in `always_on`. Strength hook = dignity × normalised ṣaḍbala; CGM centrality and CDLM linkage default to 0.5; "multi_system_confirmation_count" counts distinct *ayanāṃśas*. Predicates carry no target longitude.

**Defects.** *Astrological:* the universe of promise is the L2 reading's selection, not the chart (§N.5; concept K11); a cancelled yoga is absent rather than recorded; no frame; no exceptions; "confirmation" counts conventions. *Computational:* label-only triggers; three 0.5 defaults; string heuristics for lordship; rows that outlive the signals they point at.

**Elevated algorithm.** F1 builds the chart's **mechanism graph** from L1 facts and versioned L0 rules; L2 *attaches*.

- **Nodes:** grahas, bhāvas, rāśis, nakṣatras, yoga and doṣa formations from `ga_yoga_firings` with their formation state, kārakas (Parāśara and Jaimini), ārūḍhas, special lagnas, sensitive points, varga positions where a rule needs them. Every node carries its `fact_id`s.
- **Edges (typed, frame-bearing):** lordship, occupation, classical aspect (per-graha table, nodes cast none), dispositor chain, kāraka role, yoga constituency, argalā / virodha as intervention and its obstruction `[D-local 31.2–9]`. Each edge: `rule_id`, `rule_version`, `provenance`, `frame ∈ {lagna, moon, arudha, graha:X}`, `applicability`.
- **Cancellation is defeat of a conclusion, not negative evidence** ⟨replaces v1.0's "sign −"⟩. Two edge types target a *specific rule conclusion*: `defeats(conclusion_id, by: fact_ids, rule_id)` (bhaṅga; the formation remains, the conclusion does not) and `excepts(conclusion_id, …)` (a rule's own apavāda). The graph stores the **candidate** conclusion and its defeating evidence, and computes an **effective** state `∈ {in_force, defeated, partly_defeated, contested, unresolved}` per conclusion. A defeated adverse conclusion is not support for the opposite; a defeated favourable conclusion is not harm. Rule-local strength comparisons (which of two formations dominates under a cited rule) remain computable from the descriptors; there is no universal scalar.
- **Two mechanism routes:** an **admitted mechanism** is a reproducible typed rule over L1 facts (scored where the judge's paths allow); a **proposed interpretive mechanism** is L2-originated, fact-grounded, with explicit assumptions and source status, carried as `testimony` until reviewed. The second route never enlarges scored promise silently; the first route's incompleteness never discards the second.
- **Mechanism:** a named subgraph with a role per participant and a `supports / opposes / conditions` relation to an event class; mechanism → event-class mapping is a separate reviewable table with a source per row. `missing_fact` and `evaluated_empty` are distinct states.
- **Attachments:** MSR, CGM and Pratijñā rows attach to mechanisms by deterministic id; absence of an attachment is never denial.
- **Promise route** per event class = admitted mechanisms with roles, preconditions, and effective cancellation status; the judge's natal-fact rows (R-3), negative space and the forecaster's structural features read it. **The forecaster's feature mapping from this graph is specified in 3.20, not implied here.**

**Classical basis.** Formation and cancellation rules already in L0; argalā `[D-local]`; cancellation as rule-targeted defeat per BPHS Ch. 9–10 `[D-prior per the Kṣetra plan]`.

**Synergy.** Gives: natal-fact rows to the judge (R-3), effective cancellations and exceptions to negative space, attachments to the jury, typed features to the forecaster, participations to the dossier. Takes: L1 facts, L0 rule versions, L2 attachments.

**Oracles.** Removing an L2 signal leaves the admitted graph unchanged; removing an L1 fact flips its mechanisms to `missing_fact`. **Defeating a harmful conclusion removes or modifies that conclusion, leaves the formation present, and changes no unrelated conclusion.** Two MSR signals for one configuration attach to one mechanism. Every constant has declared meaning and provenance (lint on undeclared constants, not on constants). No predicate without a target identity.

**Disposition.** Stage writer under the same id; storage additive and versioned (plan R-5).

---

### 3.4 · `ka_vighnakara` — negative space

**Today** [S `writers/ka_vighnakara.py`]. Five detectors at every anchor (top 500 convergence peaks plus up to 200 daśā-midpoint anchors that depend on `date.today()`): Saturn/Rāhu in dusthānas from lagna or Moon (0.40–0.65), Rikta tithi (0.35), transit Moon in gaṇḍānta (0.55), pāpakartarī of the lagna *sign* (0.50), transit Mars/Saturn combust (0.30). Thresholds (≥ 0.70 severe) make "severe" unreachable (max 0.65). `override_score = score × 0.45`. No daśā veto; two detectors "reserved".

**Defects.** *Astrological:* a muhūrta tithi rule and a daily gaṇḍānta applied as natal obstructions; transit combustion of Mars or Saturn is not an obstruction doctrine for the native; pāpakartarī tested on the lagna sign rather than the bhāva and lord concerned; no release conditions; no exceptions (Saturn in 3/6/11 from the Moon is favourable in the same chapters); anchors inherit Saṅgam's defects. *Computational:* invented weights; unreachable severity; today-dependence.

**Elevated algorithm.** The asset becomes the **materialised interpretation of the judge's findings and coverage**, not a second astrology engine, and emits typed states with provenance, never a number.

- **Inputs (declared dependencies: judge, F1, F2):** the judge's vedha interval relation with its states `active · inactive · unqualified` (reasons `node_obstruction_undecided`, `obstructor_residence_unknown`), Moon scope and coverage ⟨no viparīta state exists; `NR-VIPAREETA-20261002`⟩; the judge's `evidence_against` records (adverse rule paths with their own exceptions, e.g. 70.12–14 `[D-local]`); F1 effective cancellation states and protections (benefic in kendra, Jupiter's aspect `[D Patel PG2299; D-prior BPHS 9–10]`); F2 applicability; structural bhāva-destruction conditions `[D Uttara Kālāmṛta PG77]` and the dusthāna-lord-in-own-house rule `[D Phaladīpikā XV 27–29]`; pāpakartarī of the concerned bhāva or lord from the judge's records; bādhaka for movable-sign lagnas `[D-local ch. 50 vv. 20–21]` as a scoped mechanism.
- **Internal model — five axes, stored separately** ⟨replaces one exclusive six-value enum⟩: *applicability/exposure* (in risk set, outside, method applicable / inapplicable); *knowledge* (searched, unsearched, inputs missing, computation failed, complete); *rule conclusion* (none, supportive, adverse, obstructed, conditionally deferred, denied under a named rule); *defeat/qualification* (active, excepted, cancelled, partly cancelled, contested, unresolved); *measurement* (not estimated here — see below). A period can be fully covered, applicable, carry an active adverse finding and a cancelled obstruction at once; the row says all four.
- **Effective state exposed.** An obstruction candidate with its defeating evidence is retained, and the row's `effective_state ∈ {obstruction_in_force, obstruction_cancelled, obstruction_partly_cancelled, obstruction_contested}` is what every consumer reads. `obstruction_active` with a `cancelled_by` sub-field is **not** emitted ⟨v1.0 defect: it invited every consumer to re-apply the obstruction⟩.
- **The six-value external vocabulary** (`outside_risk_set · method_inapplicable · information_unavailable · evaluated_silent · obstruction_active · measured_lower_rate`) survives only as a *derivation* from the axes for serving, with the detailed contest beside it. **`measured_lower_rate` is not produced here**; it is a post-forecaster read model (plan §4.1) ⟨removes the feedback cycle⟩.
- **Release** is computed where it can be (transit exit instant from the sky substrate; onset of a protecting aspect; the period boundary that ends a scoped mechanism) and is `release_unknown` or `release_conditional(predicate)` otherwise — never invented.
- Daily pañcāṅga doṣas (Rikta tithi, gaṇḍānta-of-the-day, kulika) leave this asset for the election view (3.17).

**Classical basis.** Vedha: Phaladīpikā XXVI (judge-owned). Protection and cancellation: Patel PG2299 `[D]`, BPHS 9–10 `[D-prior]`. Bhāva destruction `[D]`. Bādhaka `[D-local]`, movable signs only. No universal bādhaka or māraka multiplier.

**Synergy.** Gives: contest sources to the jury (reported, never netted), effective obstruction states to the forecaster's suppression inputs, "what obstructs" to NOW and EXPLAIN, release dates or `release_unknown` to AHEAD. Takes: judge records and vedha intervals, F1, F2.

**Oracles.** A planted vedha `active` yields `obstruction_in_force` whose release equals the vedha interval end. A planted Jupiter-kendra protection yields `obstruction_cancelled` with the protecting fact ids, not silence and not `obstruction_active`. Missing vedha coverage yields `information_unavailable`, never "clear". A Rikta tithi produces no natal row. **An obstruction whose release cannot be computed carries `release_unknown` and still passes** ⟨v1.0's "release date present whenever active" was too strong⟩. No numeric weight exists.

**Disposition.** Stage writer under the same id; storage additive and versioned.

---

### 3.5 · `ka_kalasutra` — activation intervals

**Today** [S `writers/ka_kalasutra.py`, `services/ka_temporal/date_resolver.py`]. For each predicate, the convergence row with the highest score supplies a peak; the window is peak ± a half-width by class (yoga 7, doṣa 14, else 5 days) or, without a peak, each matching Vimśottarī period's span with a midpoint "peak"; predicted dates at peak ± 3 days with strength `1 − 0.2·|δ|` or at period start/middle/end with 0.6 / 1.0 / 0.4; **at most eight periods are listed, and the temporally relevant primary (current, else soonest future, else most recent past) is guaranteed a slot ahead of the cap** ⟨corrected: v1.0 said the cut "drops later recurrences" without this; `date_resolver.py:474–499`⟩; proximity = dignity × ṣaḍbala, identical across periods; `as_of` defaults to `today`.

**Defects.** Half-widths and date strengths have no source; a period midpoint has no doctrine; proximity is natal strength, not timing; the eight-row cap still truncates the listing beyond the primary; implicit `today` makes output non-reproducible. The doctrinal kernel (a yoga fruits in the daśā of its constituents) is a *rule*, and rules belong to the judge.

**Elevated algorithm.** A read model over the judge, F1 and F2 that **adds no rule**. For each F1 mechanism attached to an L2 signal: intervals = the judge's evaluated windows whose relationship records name the mechanism's participants as agent or object, each carrying its `contact_id`s, **the judge's own period anchor** (system, level, lord as the path evaluated it), coverage, and operator role. **The constituent-lord daśā is an annotation, not a filter**: `lord_period_concurrent = true/false` with the period id, computed from F2 ⟨replaces v1.0's intersection, which narrowed judge windows under a rule the judge never applied and could convert PD testimony into scored timing (AM-21 part 4)⟩. If the native wants "daśā of the constituents" to *select* windows, that is a rule path for Pravāha to admit, with its locator. The recurrence ladder is the ordered set of the judge's contacts for the mechanism's participants across the searched horizon with occurrence ordinals, `unsearched` where coverage ends. No half-widths, no strengths, no proximity, no cap, explicit `as_of`.

**Classical basis.** None of its own; everything is the judge's.

**Synergy.** Gives NOW/AHEAD per-structure intervals and the ladder. Takes judge windows and contacts, F1, F2.

**Oracles.** Two mechanisms sharing one contact show the same `contact_id`. **A valid judge window whose path has no daśā prerequisite survives unchanged** (the gate mutant fails). An interval outside judge coverage reads `unsearched`. The ladder has no fixed length. A PD-anchored testimony record never appears as a scored interval.

**Disposition.** Read-model writer (SQL over judge/F1/F2 tables).

---

### 3.6 · `ka_kala_darshana` — the published view

**Today** [S `writers/ka_kala_darshana.py`]. Top 750 convergence rows; `effective = conv × (1 − max override)`; a NULL convergence becomes 0.5; labels at 0.70 / 0.45 / 0.20; rows 501–750 can never carry an obstruction; daśā-anchored obstructions never join; fixed-string narrative with a precedence bug.

**Elevated algorithm.** A read model over the candidate generation: per `(event_class, interval)` the judge's window with its three valence fields and occurrence evidence **kept separate**, the jury's `D(W)` with witness signature and segment support, the negative-space effective state, the forecaster's alignment surprise where present, and a `tier` column (`operator_role` + qualification) for density layering. **Separate contextual rows** carry what has no judge window: clock-only context, a coverage gap, an uncomputed method ⟨v1.0's "no row without a judge window" would have hidden the honest unknown⟩. No composite, no label, no default; narration at serve time.

**Oracles.** Every published interval has a negative-space row. **An interval with no judge window but a known coverage gap is visible as a contextual row.** No numeric composite column exists.

**Disposition.** Read-model writer.

---

### 3.7 · `ka_jivana_parva` — life chapters

**Today** [S `writers/ka_jivana_parva.py`]. MD and AD rows (plus the current PD) from Vimśottarī; `high_convergence_count` and `avg_effective_score` from convergence windows inside the span (a table now empty); quality labels from thresholds (0.55, 0.60, 0.45, 0.25); theme keywords from a hard-coded planet table; AD narratives pass "MD/AD" as the planet.

**Defects.** The labels grade a dead number; themes are invented; **the code explicitly refuses to lower the thresholds to make `peak` reachable, naming the upstream defect (F-SANGAM-1) as the cause** ⟨corrected: v1.0 said the thresholds "compensate" for the defect; they do the opposite, on principle⟩; the as-of date is implicit.

**Elevated algorithm.** A read model over F2 and the stages. A chapter is an F2 period carrying: the dossier descriptors (3.2); mechanisms active in it; judge windows, jury turning points and negative-space effective states inside its span; LEL events pinned, **role-gated** (F3 boundary; the circularity guard kept). "How this chapter differs from the last" is a **condition-aware diff**: mechanisms new / gone / present in both, **and for mechanisms present in both: the participants' conditions, the commencement condition, the effective cancellation status and the coverage that changed**, with σ on boundaries ⟨v1.0's mechanism-id diff would have reported identical mechanisms under changed lords as "no difference"⟩. Themes are the event classes of attached mechanisms. No quality label. Explicit `as_of`.

**Oracles.** Removing the convergence table changes nothing. **Identical mechanisms under changed lord conditions produce a non-empty, attributable diff.** An AD chapter names its own lord.

**Disposition.** Read-model writer; the serving fix for stale counts lands first (review F-L2).

---

### 3.8 · `ka_bhavishya_lekha` — issued forecasts

**Today** [S `writers/ka_bhavishya_lekha.py`]. Up to 100 darshana rows within five years become projections with tiers at 0.70 / 0.45; domain by keyword match with order shadowing; a generic ±21-day falsifier; **a robust outcome-preservation discipline that reads L4 `phala_anchors` to find bhavishya ids referenced by outcomes and keeps them** (`:262–276`); the seed says "3-year horizon, up to 50".

**Defects.** Tiers are a structural score read as probability (the code's F-BHAV-2 note says so); domains by keyword; the falsifier is not the event's observation predicate; one row per darshana row multiplies forecasts; identity is a rank.

**Elevated algorithm.** The **registrar of issued forecasts**, with three identities kept apart ⟨v1.0 used one⟩:

1. **Episode key** `(event_class, phase, affected_person, episode)` — stable across refinements; outcome credit clusters here.
2. **Issue key** — immutable per issued statement: `issue_id`, `version`, `issued_at`, `information_cutoff`, manifest reference, the delivered statement verbatim, the model qualification in force (result policy, calibration status), intervals (disconnected allowed) with the disclosed grain, a declared point functional, `probability_target` null unless the class is `calibrated`, the falsifier = the event class's observation predicate from the ontology.
3. **Delivery linkage** — an issue exists only when delivered to the native through a named channel; **a generated candidate is not an issued forecast** ⟨v1.0 would have issued every candidate⟩. Candidates live in the stage tables; the registrar writes an issue on delivery.

A refinement issues a new version; nothing is edited. **Already-issued uncalibrated probability statements remain archived faithfully**; a quality gate governs new issues only. **The L4 read is replaced, not deleted**: reference protection moves to a contract owned where the outcomes live (plan R-11: L5 beside Samīkṣā owns issuance/outcome lifecycle; L3 supplies the registrar interface and immutable manifest references), and until that contract exists the current protective read stays ⟨corrects review F-L22's "one-line correction"⟩.

**Oracles.** A re-run with unchanged inputs changes no existing issue. **Two issues for one episode remain distinct while outcome credit stays episode-clustered.** No issue carries a probability while its class is uncalibrated. Domain never comes from a keyword. A candidate that was never delivered has no issue row.

**Disposition.** Registrar writer (append-only by issue key, with an equality check on re-insert — a reviewed Idem treatment, plan §7). Table location routed (R-11).

---

### 3.9 · `ka_taranga` — the shape of the year

**Today** [S `writers/ka_taranga.py`, `services/taranga_kernel`, `services/taranga_service.py`]. Monthly 1950–2100: harmonic mean of a domain-match term, the mean convergence score and the mean Pratijñā grade / 10; the event-class scope is degenerate by construction. The live service uses a different additive formula. The W2 decision to drop the event-class half is unimplemented. The graha→domain table has eleven names outside the canonical thirteen. **Served today by one registered retrieval capability** (`query_activation_waveform.ts`, reads `kala_taranga`), by no MCP facade; the Vidhi `taranga_curve` primitive routes to a tool that does not read it ⟨corrected scope, review F-L21⟩.

**Elevated algorithm.** A read model: per **`(event_class, month)`** the integral of the forecaster's compact field over the month (`∫λ`), with its units and risk set, beside a separate count of judge windows active in the month. **A domain figure exists only through a declared class→domain table** (source per row; overlap rule stated — a class in two domains is counted once per domain and flagged; units preserved) ⟨v1.0 promised a domain integral with no transform⟩. No blending, no harmonic mean, no planet table. The live service retires once the read model is served.

**Oracles.** The monthly integral equals the sum of segment integrals clipped to the month. **Overlapping labels for one event class do not double its expected count.** Duplicate insertion changes nothing.

**Disposition.** Read-model writer (after K5).

---

### 3.10 · `ka_tulana` — priority

**Today** [S `services/ka_tulana/ranker.py`]. Linear composite (convergence 0.40, rarity 0.25, confidence 0.20, proximity 0.15), rarity capped at 30 years, `compare(A, B)` with ties to A; accepts only Saṅgam modes A and B (`:61–62`); **not called by the priority tool** (`call_service_wrappers.ts:708` ranks `bodha_msr_signals ⨝ kala_activation` directly; `producer_editorial_review.ts:386` credits Tulana).

**Defects.** One composite over incommensurables; fixed weights; inputs that no longer exist; attribution without use.

**Elevated algorithm.** A ranking *service* over typed inputs: jury `D(W)` with coverage, negative-space effective state, the forecaster's salience axes, and the caller's declared question frame. Output is a **Pareto front** with the caller's lexicographic order (`nearest`, `strongest`, `most_robust`, `best_suited`); **ties and incomparability are first-class results** (most alternatives will be incomparable; the tie-break is a declared decision policy, reported as such); `compare(A, B)` returns the dominance table; dissonance is the presence of contest rows. No weights.

**Oracles.** Swapping A and B swaps the result. **A window with `information_unavailable` is incomparable with one with `evaluated_silent` on that axis — neither outranks the other** ⟨v1.0 invented a safety ordering⟩. **Changing the caller's preference changes the ordering without changing any evidence field.** No fixed weight constant exists.

**Disposition.** Service, re-based; wiring into PRIORITY is the native's R-6.

---

### 3.11 · `ka_gochara_resonance` — transit targets

**Today** [S `services/ka_gochara_resonance/writer.py`]. Per event class, targets from the ontology's signature houses, lords, kārakas (weight 1.0), `mechanism_node` rows from `bg_transit_rules` with weights, sensitive degrees 0.5, ārūḍhas 0.6, yoga constituents 0.7, daśā-lord portfolio 0.8, derived points 0.5. First root wins per `(target_type, target_ref)`. **Frame defect:** signature houses (from the lagna) are joined directly to `bg_transit_rules.primary_house`, documented as counted from the Moon (`writer.py:823–828`; `l0_transit.py:166`); `mechanism_node` rows always `resolved` (`:1172–1178`).

**Defects.** Weights pre-judge the rule; one physical target with two roles deduplicated to one; the frame mismatch mis-selects the *rule*, not just the label; the daśā-lord portfolio duplicates the kāraka set.

**Elevated algorithm.** Resonance becomes the **typed relationship resolver** of F1 onto the judge's records: for each event class, every physical object a promise route's mechanism names, with `frame` typed and **resolved before any rule is matched** (a Moon-frame rule is matched against Moon-frame houses; a lagna-frame signature against lagna-frame houses), `role` typed, mechanism id, rule id and provenance. No weight column. One physical object with several roles is one object with several role edges. Derived points keep their Phaladīpikā locators.

**Oracles.** **For a non-Aries lagna whose Moon and lagna houses differ, a Moon-frame transit rule selects the Moon-frame target and a lagna-frame signature the lagna-frame target, independently** (the frame-mixing mutant fails). One physical target with two roles yields one object and two edges. No numeric weight exists.

**Disposition.** Folded into F1 (K2); writer retired after the judge reads F1 directly.

---

### 3.12 · `ka_vedha_gochara` — vedha as intervals

**Today** [S `services/ka_vedha_gochara/{logic,gate,writer}.py`; L0 `l0_transit.py`, `l0_phaladeepika_vedha.py`]. Three mechanisms over a rolling −60/+400-day horizon, one ayanāṃśa offset at `today` for every day. *House vedha:* 36 cited pairs from the Moon (Phaladīpikā XXVI 3–8) plus 6 unsourced Rāhu/Ketu pairs; occupants include the Moon and the nodes; Sun↔Saturn and Moon↔Mercury excepted; a *viparīta* cancellation carved from any companion sharing the primary's sign, stamped `translator_commentary`. *Sarvatobhadra:* an algorithmic approximation; the grid table is empty. *Lattā:* 8 rows (PG338–339; Ketu absent; ślokas 47–48 not implemented). Intervals inside a JSON column. **Divergences from the judge** (`gochara_rules/vedha_derive.py`): the judge produces no viparīta (ruled, `NR-VIPAREETA-20261002`); a node-only obstructor yields `unqualified` (`node_obstruction_undecided`), **but a cited obstructor present alongside a node establishes `active`**; the Moon is never a *stored* obstructor, so every `inactive` carries the scope `excluding_on_demand_moon_obstruction` (except a Mercury primary, whose exception removes the Moon); an obstructor's residence must be established over the primary span or the state is `unqualified` (`obstructor_residence_unknown`) ⟨corrected: v1.0's shorthand "the judge ignores nodes" and "omits viparīta" understated both⟩.

**Defects.** Two definitions of vedha in one layer; a constant ayanāṃśa offset across 461 days; a rolling horizon with no coverage disclosure; viparīta served at the same tier as cited vedha; the approximation stamped with a citation it was told not to carry.

**Elevated algorithm.** One definition — **the judge's contract, including its later rulings** — produced once as an adapter over the sky substrate for the century: for each cited pair, the half-open intersection of the primary's residence in house *h* from the Moon with the obstructor's residence in the vedha house; states `active | inactive | unqualified` with `unqualified_reason ∈ {node_obstruction_undecided, obstructor_residence_unknown}`; the two exception pairs; `inactive` carries `moon_scope = excluding_on_demand_moon_obstruction` except for a Mercury primary; `coverage` on every answer. **Viparīta is not produced** (ruled); the disclosure "not applied — no served source" is carried as data. Lattā rows `verse_cited` (PG338–339) with the Ketu gap declared and ślokas 47–48 as an enrichment row. **Sarvatobhadra is `information_unavailable` (grid unpopulated; construction attempted and blocked at L0), not `method_inapplicable`**; the approximation rows retire. Ayanāṃśa per instant. A dedicated interval table replaces the JSON column.

**Classical basis.** Phaladīpikā XXVI 3–8 (L0, 36 rows verified row by row); PG322–323 exceptions; PG338–339 lattā; PG353/PG349 scales unused (D-PG353); `NR-VIPAREETA-20261002`; `NR-NODE-RETRO-20261002` for the node motion basis.

**Synergy.** Gives the judge's P2 operand (today `VEDHA_SOURCE = None`), negative space's obstruction intervals and the forecaster's suppression primitive. Takes the sky substrate and L0 rules.

**Oracles.** Sun–Saturn never obstruct each other. **Three fixtures give three different outcomes: node-only → `unqualified`; node plus a cited obstructor → `active`; primary span with a residence gap and no known obstruction → `unqualified` (`obstructor_residence_unknown`).** Interval equality with the judge's independent derivation on a fixture. A request outside the century reads `unsearched`.

**Disposition.** Adapter, aligned to the judge; the layer's single vedha producer (Kṣetra ruling 8).

---

### 3.13 · `ka_moorti_nirnaya` — transit quality

**Today** [S `services/ka_moorti_nirnaya/{logic,writer}.py`]. For each sign run of eight grahas, the Moon's nakṣatra at the ingress instant counted from the janma nakṣatra gives an offset 1–27; `offset mod 4` gives svarṇa / rajata / tāmra / loha. Arcs built at UT midnight (`overlays.date_to_jd`) against the kernel's noon-UT convention. Rolling 461-day horizon. The module records that the rule form is not in the served corpus; the project's value architecture noted a 12-house Moon-relative table as the commonly cited form. Neither surfaced this session.

**Defects.** Method identity contested and uncited; epoch mismatch; `corpus_verifiable` false on every row while NOW serves it as computed.

**Elevated algorithm.** **Preserve the legacy output as a named legacy computation** (`moorti_nakshatra_27`, `source_status = uncited_legacy`) and **fix the epoch first** (ingress and Moon position evaluated at the same instant under the same convention from the sky substrate). **The twelve-sign table is not computed as a coequal convention**; it enters only as a separately sourced variant after the corpus custodian admits a locator ⟨v1.0's "two conventions, both computed" treated computability as establishment⟩. The judge may use mūrti only as `testimony` (D-PADMIT); negative space may report loha as a factor, never suppress with it.

**Oracles.** Ingress instants equal the sky substrate's roots; the Moon is evaluated at the same instant. A row without `uncited_legacy` fails until a locator exists. No consumer scores it.

**Disposition.** Adapter, gated (plan R-8).

---

### 3.14 · `ka_kota_chakra` — the fort

**Today** [S `services/ka_kota_chakra/{logic,writer}.py`]. Ring partition from the janma nakṣatra (stambha / durgāntara / prakāra / bāhya) — a transcription with `corpus_status = not_in_corpus`; posture × nature table "this writer's own synthesis"; static benefic/malefic; no direction; horizon not overridable.

**Defects.** Uncited ring table; no entry/exit geometry; a nature table disagreeing with the judge's `nature.py`.

**Elevated algorithm.** Adapter emitting **ring occupancy only** as `uncited_extension` testimony: nakṣatra-ingress events from the sky substrate (century; one epoch); nature from the shared `gochara_rules/nature.py`. **Direction of motion is null** until the selected convention's directed path and door geometry is sourced — longitude speed alone cannot say "toward the centre" ⟨corrects v1.0⟩. Ring × benefic/malefic readings remain authored interpretation and are not emitted.

**Oracles.** Nature equals `nature.py` for the same instant. A row without `uncited_extension` fails. Identical ring occupancy under different (hypothetical) paths does not claim equivalence of reading.

**Disposition.** Adapter, testimony-only.

---

### 3.15 · `ka_tithi_pravesha` — the annual return

**Today** [S `services/ka_tithi_pravesha/{logic,writer}.py`]. The praveśa instant is the Moon's return to its natal sidereal longitude nearest the civil birthday; a chart is cast; 120 rows; two-pass verification by Moon equality. Citation `not_in_corpus`. Not computed: Muntha, varṣeśa, the Tājaka yogas.

**Defects.** The name says tithi-praveśa but the computation is a Moon-longitude return; civil-date anchor; uncited and contested, served as `computed` by NOW and `not_in_corpus` by AHEAD.

**Elevated algorithm.** **Keep today's computation as the named legacy `moon_longitude_return`** with `uncited_legacy`. **The phase-return variant is specified, not computed**, until a cited school definition supplies: the elongation rule, the solar-month condition, leap-month and duplicate-root handling, and the year-number convention `[U]` ⟨v1.0 would have computed it from a phase-equality fixture alone⟩. Annual chart objects become judge `annual_object_identity` candidates only after admission (D-T2). NOW and AHEAD report one coverage state.

**Oracles.** Legacy rows carry `uncited_legacy`. NOW and AHEAD agree. (The phase-return oracle is written when the definition is admitted.)

**Disposition.** Adapter, gated (plan R-8).

---

### 3.16 · `ka_sudarshana_varsha` — the three-frame year

**Today** [S `services/ka_sudarshana_varsha/{logic,writer}.py`]. For year *N*, active sign = natal sign + (N−1) mod 12 from Lagna, Moon and Sun (`logic.py:69–80`); `tri_lagna_convergence = (JL == CL == SL)` (`:110–117`), constant per chart and true only when the natal signs coincide; day-grade windows; nested periods out of scope; no citation column.

**Defects.** The flag is meaningless by construction; the wheel is the method's first step only; no bhāva reading.

**Elevated algorithm.** The Sudarśana method as a judge method at enrichment step 2, per BPHS 74 `[D-local 43255–43381, 43867–43946]`:

- **Three frames** (Lagna, Moon, Sun), each with its active rāśi for the year and that rāśi's benefic/malefic occupants and aspects from F1; **judgment** by the balance of benefics and malefics, **equal counts decided by strength**.
- **Coincident-frame rule:** when two or all three of Lagna, Moon and Sun share a rāśi, the judgment is made from the birth chart only — the frames are not treated as three.
- **Nested periods as F2 rows:** one year per house, one month per house within the year, then 2½ days and 12½ ghaṭikā, with applicability tag `annual`.
- **Commencement conditions:** benefics in 1/4/7/10/5/9/8 at commencement, as the text lists them.
- **The year anchor** (birthday by civil date, solar return, or another convention) is **not supplied by the extracted verses**; it is a declared convention `[U]` on every row ⟨v1.0 asserted "from the solar return"⟩.
- **No agreement flag.** Where two frames reach a conclusion, the comparison is of *conclusions and their reasons* (which bhāva, which occupants), never of offsets — a shared offset from two frames is the tautology v1.0 removed and nearly re-introduced.

**Oracles.** The active sign has period 12. Month sub-periods partition the year. **A chart with Lagna and Moon in one rāśi is judged from the birth chart only** (the three-frame mutant fails). The constant flag no longer exists.

**Disposition.** Adapter now; judge method at step 2.

---

### 3.17 · `ka_muhurta_seva` and the election view

**Today** [S `services/ka_muhurta_seva`, `muhurat/finder.py`, `panchang_engine/*`]. A whole day scored at sunrise: `100 × min(1, Σ w_f·q_f)` over tithi, nakṣatra and vāra tables per event, special yogas, "Jupiter and Venus not combust" (`finder.py:120–123`: +0.5 each, no strength), and Tārā-bala when a native chart is given (cycle attenuation 1.0 / 0.8 / 0.6, unsourced). Knockout to zero on `Saturday ∧ tithi ∈ {4, 8, 9, 14, 30}`. Weights from YAML summing to 0.95; an `avoid_penalty` never read; Chandra-bala implemented but unused; a hard-coded "active daśā lord = Jupiter" read by nothing; no lagna; no intra-day interval. The election view reports residual doṣas "uncancelled" because `bg_parihara_rules` has no muhūrta-scope rows (60 rows, all natal `[L]`).

**Defects.** Day-grain only; a weighted sum of incommensurables; a hard zero instead of a doṣa; the tārā cycle rule invented; "uncancelled" asserted where cancellation was never assessed; the cancellation doctrine is in the served corpus and was never extracted.

**Elevated algorithm.** Election over qualified methods, per Product §3.11 (general calendar, personal suitability and outcome expectation kept apart).

1. **Candidate intervals, intra-day.** Boundaries = muhūrta lagnas (sign rises), horās, **and every change of tithi, nakṣatra, yoga, karaṇa and every start/end of an applicable doṣa interval** (Bhadrā mouth/tail, the shunned ghaṭīs of Parigha/Śūla/Gaṇḍa/Vyāghāta, kulika etc.) ⟨v1.0 used lagnas and horās only⟩. The whole-day score retires.
2. **A doṣa ledger per candidate**, typed rows with locators: tithi–nakṣatra combinations `[D PG19 vv. 11–13]`; dagdha, viṣa, hutāśana vāra × tithi `[D PG17 v. 8]`; śūnya nakṣatras and rāśis by month `[D PG19 vv. 14–16]`; Vyatīpāta, Vaidhṛti, Bhadrā, kṣaya/vṛddhi tithi, kulika, pāta, the first ghaṭīs of Viṣkambha and Vajra `[D PG26 v. 34]`; the eclipsed nakṣatra `[D PG26 v. 33]`; pakṣa-randhra ghaṭīs `[D PG27 v. 36]`; Parigha/Śūla/Gaṇḍa/Vyāghāta ghaṭīs `[D PG26 v. 35]`; dagdha-tithi by solar month `[D PG109 v. 66]`; yāmitra `[D PG109 v. 67]`.
3. **Parihāra applied as cited — exact predicates, exact scope.** Each rule is a predicate with the chapter it sits in; **all of the following are in the vivāha (marriage) chapter and apply to marriage (and upanayana where the verse says so) until a general-scope clause is found** — PG109 v. 65 ṭīkā itself says the chapter's doṣa reckoning is not doṣa-producing in other undertakings ⟨replaces v1.0's general application⟩:
   - **v. 68 (PG110:C1):** `lagna_has_strength(Moon) ∧ lagna_has_strength(Sun)` → ekārgala, upagraha, pāta, lattā, yāmitra, kartarī, udayāsta **perish** (marriage lagna). v. 69: vedha is to be shunned in every country — **vedha is never cancelled by this verse**.
   - **v. 88 (PG115:C2 mūla damaged; fixed by the PG116:C1 ṭīkā):** kartarī-doṣa absent when the two kartarī malefics are in an enemy's house, debilitated or combust; Venus debilitated or in an enemy's sign → no doṣa even in the 6th; Mars debilitated, combust or in the 8th → no doṣa; the Moon debilitated (sign or navāṃśa) in 6/8/12 → no doṣa from him.
   - **v. 89 (PG116:C1, "in marriage"):** `strong(Mercury) ∧ strong(Jupiter) ∧ strong(Venus)` each in a kendra (1,4,7,10) or koṇa (5,9) from the lagna → the doṣas of year, ayana, season, tithi, month, nakṣatra, pakṣa, dagdha-tithi and the blind/one-eyed/deaf/lame lagnas perish; likewise a Moon conjoined with malefics and a navāṃśa held by malefics. The ṭīkā reads the three planets conjunctively ("Budha, Bṛhaspati and Śukra stand strong"); the predicate is stored as the ṭīkā reads it, with `conjunction_reading = tika`.
   - **v. 90 (PG116:C1):** `Jupiter ∈ {kendra, koṇa, 11}` ∨ `Sun ∈ upacaya (3,6,10,11)` ∨ `Moon ∈ {lagna, vargottama navāṃśa}` → "all doṣas come to destruction"; `Moon in 7th` → the muhūrta doṣas perish. The ṭīkā extends "by implication" to Mercury and Venus; stored as `tika_extension`, never as the verse.
   - **v. 91 (PG116:C1–C2):** in the marriage lagna, Mercury in a koṇa or a kendra other than the 7th removes "a hundred" doṣas; Venus "two hundred"; Jupiter "a lakh"; lagna lord and navāṃśa lord in a kendra (ṭīkā: or the 11th) quiet "the whole heap". **The numbers are the text's priority language and are stored as `priority_rank`, never subtracted from a count.**
   - **v. 34 ṭīkā (PG26:C1–C2, first prakaraṇa, general scope):** Jupiter in a kendra → kṣaya/vṛddhi-tithi doṣa absent; Mercury in a kendra → vṛddhi-tithi and tri-spṛśā doṣa absent.
   This requires an **L0 extraction** into `bg_parihara_rules` with `scope ∈ {marriage, upanayana, general}` and the exact locators. **Until the applicable rules have been evaluated for a candidate, the view says `cancellation_unassessed`, never "uncancelled"** ⟨corrects v1.0⟩.
4. **Tārā-bala by cycle** `[D PG67 v. 13]`: first cycle, vipat (3), pratyari (5), vadha (7) wholly inauspicious; second cycle, their first, middle and last **thirds** respectively (ṭīkā: 20 of 60 ghaṭīs — a variable-duration star is divided in thirds, not in fixed ghaṭīs); third cycle, all auspicious; dāna per tārā recorded as remedy text. The 1.0/0.8/0.6 attenuation retires.
5. **Planetary factors, each sourced separately** ⟨v1.0 merged three⟩: **Guru-bala** from the janma rāśi `[D PG82 v. 46]` — Jupiter in 5/9/11/2/7 best; 10/6/3/1 acceptable, the 1st after śānti; 4/8/12 condemned; stated for a boy's vratabandha and a girl's vivāha and scoped so; **no Śukra-bala from this verse**. **Combustion of Jupiter and Venus is kept as its own factor** (the current check, now with the locator the stage brief finds or `[U]`). **Sign-phase and anticipation** `[D PG70 vv. 17, 19]` are added as further factors, not substitutes. **Moon's avasthā** at commencement reported `[D PG67 vv. 14–15]`.
6. **Personal layer, separate:** the native's judge windows and negative-space effective states for the undertaking's event class, F2 applicability, janma-nakṣatra / janma-tithi avoidance `[D PG26 v. 34]`; served beside, never summed with, the calendar layer.
7. **No composite.** A candidate carries: interval, factors present (cited), doṣas, parihāras applied (cited, scoped), residual doṣas or `cancellation_unassessed`, personal layer, uncited factors in their own list.

**Classical basis.** Muhūrta Cintāmaṇi locators as listed `[D]`; Bṛhat Saṁhitā and Muhūrta Mārtaṇḍa named in code without locators `[U]`.

**Synergy.** Takes the judge, negative space and F2 for the personal layer; gives ELECT and RITUAL their candidates; daily pañcāṅga primitives move here from NOW's TypeScript.

**Oracles.** A kartarī whose malefics are debilitated reads `cancelled` with v. 88 cited, for a marriage election only; the same candidate for a business undertaking reads `cancellation_unassessed`. **A doṣa or a cancellation beginning halfway through a candidate splits the candidate.** A Saturday caturthī produces a doṣa row, never a silent zero. The tārā fixture (second cycle, vipat, 25th ghaṭī of a 60-ghaṭī star) reads auspicious. No weighted scalar exists.

**Disposition.** Service kept; the finder's scoring retires; the view re-bases; one L0 demand (scoped muhūrta parihāra rows, plan L0-M).

---

### 3.18 · `ka_graha_sancara` — the sky service

**Today** [S `services/ka_graha_sancara/engine.py`, `scripts/temporal/compute_transits.py`]. Two day-grain paths twelve hours apart: path A reads the daily ephemeris at noon UT; path B computes at 00:00 UT with Moshier by default (`compute_transits.py:75, 217`); neither uses time of day; the supported-ayanāṃśa set excludes the id every writer uses; naive datetimes assumed IST. No L3 writer calls it.

**Elevated algorithm.** The facade of `kala_core.sky`: instant-grain positions by JD through the arc index with Swiss refinement. **The contract names, on every answer:** instant (JD, time scale), backend (Swiss or Moshier, never substituted silently), flags, node model (mean/true, series), ayanāṃśa id and the per-instant value, coverage; for local products (lagna, sunrise) also location and civil-time convention. One cache keyed by `(JD, convention_id)`.

**Oracles.** Both historical paths agree with the solver within tolerance at one JD under the same declared backend. The canonical ayanāṃśa id is accepted. **A request whose backend data is missing returns `information_unavailable`, never a different backend's number.** A twelve-hour epoch mutant fails.

**Disposition.** Service, re-based; the layer's only ephemeris door.

---

### 3.19 · `ka_sangam` — the jury

**Today** [S `services/ka_sangam/engine.py`, `writers/ka_sangam.py`, `kala_trigger/trigger.py`]. Four modes: A (daśā-eligible windows then aspect events to a target), B (long-horizon sweep), C (Saturn over the Moon's 12th/1st/2nd, or Mars over signs hard-coded for an Aries lagna, `engine.py:1557–1567`), D (Jupiter/Saturn/Mars ingress into signs with SAV ≥ 28). **Modes A, B and TRIGGER measure contacts against 0° Aries because `target_longitude_deg` defaults to 0.0 and nothing sets it** (`engine.py:1148, 1377`) ⟨scoped; v1.0 said "every contact"⟩. **Mode D's SAV read is correct: the legacy `-HOUSE_n` rows are sign-indexed under a legacy label, and Mode D reads them as signs** (`ga_strength_writer.py:1218–1226`; CR-99a added sign-keyed rows with the same values) ⟨corrected: v1.0 revived a refuted frame accusation⟩. Mode D re-runs for every lifetime predicate because each substep passes one predicate and the first-predicate guard compares within the substep (`ka_sangam.py:592–603`). The I-16 score is Π(necessary) × [1 − Π(1 − wᵢsᵢ)] over thirteen currents, several always dropped; a static 0.5 daśā prior; confidence labels; `independent_current_count` up to ten; the near horizon starts at `date.today()`.

**Defects.** Geometry against the wrong point (A/B/TRIGGER); dead currents; a static prior; counts of currents presented as independence; row multiplication; Aries-lagna constants; today-dependence; `plan_substeps` deletes.

**Elevated algorithm.** As the concept note §5 (reconciled), restated as the jury's contract: reads the judge's assertions, negative-space effective states, F1 and F2; writes jury assertions with the **evidence algebra** (roles `selects · conditions · qualifies · corroborates · explains`; a reused root yields no increment; testimony weighs nothing; **selection ancestry recorded** so a root used for selection never corroborates); **declared witness groups** with shared inputs (G-P the judge's paths; G-J Jaimini on Cara daśā and rāśi-dṛṣṭi `[D]`, arriving as a **complete, separately reviewed method output**, never an incomplete rule inside jury logic; G-T Tājaka behind corpus admission `[U]`; G-K KP behind ingestion `[D-local]`; G-A Yoginī/Kālacakra as testimony with their shared Moon-nakṣatra ancestry declared); **G-J is a declared group, not a claim of statistical independence**; elementary half-open segments with support vectors; `D(W)` with a conditional and a whole-pipeline shift null, reported as a surrogate where exchangeability fails; turning points, sequences, contests; canonical attachment of reading claims. Deleted from code: the ephemeris scan, the symmetric aspect table, Modes A–D as row producers, the static prior, `confidence_*`, `independent_current_count`, `rarity_years`, the Aries constants, the destructive `plan_substeps`. Mode fixtures kept as tests.

**Classical basis.** Jaimini Cara `[D][D-local]`; Kālacakra `[D][D-local]`; Yoginī `[D-local]`; Tājaka `[U]`; KP `[D-local]`, not served; the measurement design `[M]`.

**Oracles.** J1–J5 plus: `W=[0,30), A=[0,1), B=[29,30)` has no joint segment; a universally active witness contributes ≈ 0; **a P8-selected window is never G-J-corroborated, and a root used for selection adds no corroboration**; duplicate roots add nothing; no row multiplies with the predicate count.

**Disposition.** Stage writer, rewritten (K4).

---

### 3.20 · `ka_kshetra` — the forecaster

**Today** [S `services/ka_kshetra/*`]. `ln λ = ln λ⁰ + ln P̃ + Σ_s w_s·A_s·r_s(t) + Σ_j β_j·x_j(t) + Σ_m ln(1 − ρ_m·u_m)`. λ⁰ from six seeded class priors (else synthetic 1.0); P̃ = 0.05 + 0.95·P with P a noisy-OR over k-shortest routes through the L2 graph; twelve covariates with seeded β; suppression ρ per vighna class with a 0.25 default. The stored field is piecewise log-linear on breakpoints = kinematics roots ∪ envelope knots ∪ supported daśā boundaries ∪ {0, H}, **with adaptive midpoint refinement to τ = 0.02 nats, depth ≤ 6** (W2 §5.2; `stage4_field.py:880–896`) — the `ln(1 − ρu)` term is curved, so the representation is an approximation bounded by refinement, and "exact integration" is exact for the representation. DHARA null: the envelope term is circularly shifted against fixed clocks and promise; **1,023 non-identity shifts plus the observation, denominator 1,024** (`dhara_null.py:166–175`); sliding-window maxima over ten duration buckets; pooled 0.95 quantile. Salience = weighted mean of five factors; lazy-greedy selection of 15 atoms; seven insight detectors.

**Five defects the code does not flag** [S, verified twice]: (1) **the clock term is always zero in this implementation** — `hazard.py:277` builds `graha:{lord}` from full names while `stage2_promise.py:117–131` creates `graha:Ju`-style ids, so no lord matches a route; (2) seeded weights match Vimśottarī, Yoginī, Kālacakra and Mudda but **not Cara (`w_s:chara` vs `chara_karaka`), Aṣṭottarī or `vimshottari_kp`** (migration 491:137–143) ⟨scoped⟩; (3) `absence_of_expected` can never fire; (4) the reversal insight's obstruction branch can never be true; (5) **no obstructive primitive is built in the production assembly** (`stage1_symbolization.py:592–709` builds contacts, stations, syzygies, sandhi; the vedha, mūrti and pañcāṅga builders exist but are never called; AV is a logged coverage gap), so `S ≡ 1`. Plus the known: J2000 axis under birth-relative arithmetic; chart-wide suppression (G3); σ_T floor; rarity on the krishnamurti ayanāṃśa; Mudda applicability on `datetime.now()`; `scarcity` with `gap_days = None`; `contrast` never runs.

**Elevated algorithm — in two generations** ⟨v1.0 removed the formulas without specifying successors; that is not an elevation⟩.

**G1 — the designed model, repaired, nothing else changed.** So the ablation (ruling 10) tests the model that was actually designed: (a) one canonical graha/system vocabulary (`kala_core.vocab`) so the clock term can be non-zero, with typed handling for sign-period lords (Cara stores signs) and Yoginī names; (b) clock weights keyed by canonical system ids; (c) suppression inputs wired from the adapters (3.12, 3.13) and negative space's effective states where the model's `u_m` expects them — **transits cited as evidence consume the judge by `window_ref` (B8-6 (b)); the field's knots stay Kṣetra's own continuous kinematics (B8-6 verbatim)**; (d) `as_of` and the time axis pinned, with a detector that fails on today's data; (e) rarity on the canonical ayanāṃśa with disclosure; (f) the insight detectors given working thresholds or removed; (g) **the full breakpoint set kept** (envelope rise/plateau/fall knots, switching roots where the maximum envelope changes, `min(Moon, Lagna)` crossings, clock and scenario boundaries, mask edges, horizon seams, adaptive refinement) — no compact knot subset is admitted without the numerical contract in plan §6.2. G1 keeps the existing functional form and its seeded coefficients; every constant's provenance is declared.

**G2 — a replacement model, only when specified.** A replacement for P̃ (noisy-OR over conductances), the ρ-defaults and the suppression operator is admitted only when K5's brief specifies all of: the **event process** (first event vs recurrent; eligibility; censoring — a marriage, a career change and an ongoing psychological span are not one Poisson-type event `[M Andersen–Gill]`); the **risk set** per class; **baseline units** and sourcing; the **graph features** read from F1 (typed: counts of admitted mechanisms by role, effective cancellation indicators, rule-local dominance) and how each enters `ln λ`; **coefficients** (declared, with provenance; learned only under ruling-10-style pre-registration); the **suppression operator** (route-scoped per ruling 9, typed as less-favourable / delayed / reduced-intensity); and **unavailable-input behaviour** (a term whose input is `information_unavailable` is absent with a flag, never defaulted). Until then G2 does not exist and the plan does not pretend it does.

**Null and uncertainty (both generations).** Shared *preparation* and *shift schedule* with the jury (one pass over elementary segments); **separate estimands** — jury incremental agreement, whole-pipeline selection, class-specific field maxima — each with its own conditioning and statistics; denominator = shifts + observation, stated; circular shifts are not assumed exchangeable and the surrogate flag is carried `[M Phipson–Smyth]`. σ once from F2; parameter, numerical and predictive uncertainty kept apart. **Odds only** under a declared event model and after calibration status is `calibrated`.

**Numerical contract for any compact representation (plan §6.2 item 4):** structural equality of segment partitions and coefficients where the same representation is claimed; a per-segment analytic or bounded-error justification; one-sided evaluation at every discontinuity; adversarial interior switching and peak fixtures; random differential evaluations and interval integrals as supplementary; **reproduction of the null statistics**, not only the unshifted field. Bitwise equality where the operation is unchanged; a declared tolerance where evaluation order changes; neither preserves the known zero-clock bug.

**Classical basis.** The clock and lord-condition doctrine of 3.1; vedha and lattā as 3.12; life-stage conditioning candidates `[A]`; the statistics `[M]`.

**Synergy.** Takes judge, jury, negative space, F1, F2, base rates, F3 through roles; gives `∫λ` to Taranga, alignment to the views, salience to the ranker, the snapshot to the manifest.

**Oracles.** K1–K6 of the concept note, plus: **a relevant active lord changes the clock component; an irrelevant lord does not** (the vocabulary mutant fails); the Cara clock weight is non-zero under the corrected table; no obstructive primitive is missing when the adapters have rows; `absence_of_expected` fires on a planted class; **the corrected reference and any compact evaluator agree under the declared numerical contract, including the null statistics**.

**Disposition.** Stage writer: G1 repair in K5 after the value checkpoint; G2 only on a specified brief.

---

### 3.21 · The judge — observations for Pravāha, not a redesign

- Only rule paths **P1–P6** exist in code (P1–P4 in record and window grains; **P5 held**); P7–P9 are specified, not implemented. Any "P1–P9" wording elsewhere overstates the current catalogue.
- `VEDHA_SOURCE = None` in the writer, so every P2 record is `unqualified`; the adapter of 3.12 is what fills it.
- **The result policy is selected by the generation's manifest** (`result_policy.py`; `ka_gochara_v5.py:763`); the current candidate policy is `all_null_candidate/1`, under which every numeric field is NULL and valence `unqualified`, by design. ⟨corrected: not "the default stores no numbers" as a fixed property⟩
- **`permission_per_instant` in the registered writer reads pinned L1 Vimśottarī rows** (`load_pinned_vimshottari`, `make_period_rows_for`, `:472, 694–704`); the per-chart literals live in a reference module, not in the production path ⟨corrects v1.0's "pinned as literals for the canonical chart"⟩. F2 (3.1) remains the intended common reader.
- **Verification is separated from the builder** (R9-6.1, `:774–776`): the writer runs in-build self-checks and *reports*; the verification rows are written by a separate job under the verifier principal. Other stages copy this separation, not a builder-written verification row.
- P1's categorical factors are `value_mapping_undeclared`; graduated dṛṣṭi windows are `unqualified` unless `allow_dynamic`, which the writer never passes.
- **The delegated rulings of 2026-10-02 accompany v1.4**: `NR-VIPAREETA-20261002` (viparīta not used), `NR-NODE-RETRO-20261002` (node motion as a cited constant, qualifier NULL), `NR-P1-PD-LEVEL-20261002` (PD testimony). Current semantics are read from spec + rulings, never from the spec alone.
- The node favourable set in `favourable_houses.py` includes the 10th, which the L0 node rows omit; the six L0 node vedha pairs are unsourced.
- Candidate soft factors for P2/P3 from Muhūrta Cintāmaṇi gocara (PG70 vv. 17, 19) `[D]` belong in the enrichment register; **a complete rule with its own daśā exception (70.12–14 `[D-local]`) is the pattern for any period-conditioned transit rule**, not a global veto.

---

## §4 · Findings at the algorithm level (as corrected)

| ID | Finding | Evidence | Consequence |
|---|---|---|---|
| F-A1 | Kṣetra's clock term is identically zero **in this implementation** (`graha:Jupiter` lookup vs `graha:Ju` ids); concurrence can never fire | [S `hazard.py:277`; `stage2_promise.py:117–131`; `stage4_field.py:867`] | one vocabulary module plus typed sign/Yoginī lords fixes it; historical rows are not re-audited here |
| F-A2 | No obstructive primitive is built in the production assembly; builders exist uncalled; AV is a logged gap; `S ≡ 1` | [S `stage1_symbolization.py:592–709`, `:241`] | wire the adapters; G3 scoping is moot until fed |
| F-A3 | **Four of seven seeded clock weights match** (Vimśottarī, Yoginī, Kālacakra, Mudda); Cara mismatches (`w_s:chara` vs `chara_karaka`); Aṣṭottarī and `vimshottari_kp` unseeded ⟨reworded⟩ | [S migration 491:137–143; `stage3_clocks.py:285–303`; `hazard.py:531`] | canonical ids; a missing KP weight is not authority for an independent KP weight |
| F-A4 | Saṅgam Modes A, B and TRIGGER measure against 0° Aries (default 0.0, never set); Mode C uses Aries-lagna constants; Mode D multiplies per predicate because each lifetime substep passes one predicate ⟨scoped⟩ | [S `engine.py:1148, 1377, 1557–1567`; `ka_sangam.py:592–603, 728`] | retired with the jury rewrite |
| F-A5 | `ka_dasha_kala` agreement = identity of `(start, end)`; the all-one live distribution is the author's measurement [L] | [S `service.py:76–78, 196–211`] | removed; dependency metadata replaces it |
| F-A6 | Vighnakara's `severe` unreachable (max 0.65 < 0.70); override × 0.45; no daśā veto | [S `:58–60, 128, 687, 136–139`] | typed states |
| F-A7 | Two vedha definitions: the adapter carves viparīta and counts nodes and the Moon as obstructors; the judge yields `unqualified` for node-only, `active` when a cited obstructor is present, excludes the Moon as a stored obstructor, and **omits viparīta by ruling** ⟨reworded⟩ | [S `vedha_derive.py`; adapter `logic.py:291–445`; `NR-VIPAREETA-20261002`] | one contract (3.12) |
| F-A8 | Muhūrta Cintāmaṇi's cancellation verses are in the **served** corpus (PG26, PG67, PG82, PG110, PG115–116, retrieved with headings this session) but `bg_parihara_rules` has 60 rows, all natal-scope [L]; the election view says "uncancelled" where it never assessed | [D this session; L live count] | one scoped L0 extraction; `cancellation_unassessed` until then |
| F-A9 | Resonance joins lagna-frame houses to Moon-frame rules; `mechanism_node` always `resolved` | [S `writer.py:823–828, 1172–1178`; `l0_transit.py:166`] | frame before rule, in F1 |
| F-A10 | Mūrti builds arcs at UT midnight against noon-UT knots; the sky service's two paths differ by 12 h and in backend | [S `overlays.py:41–46`; `convention.py:19`; `l0_ephemeris.py:179–183`; `compute_transits.py:75, 217`] | one sky contract naming instant, backend, flags, nodes |
| F-A11 | Kalasutra, Jivana Parva, Vighnakara anchors and Saṅgam's near horizon default to `today()`; Mudda applicability to `now()`; some accept overrides | [S several] | a pinned `as_of` is required; no claim about which historical builds used wall-clock |
| F-A12 | Under the manifest-selected candidate policy every judge number is NULL; P5 held; P2 unqualified without a vedha source; P7–P9 absent; **the registered writer reads pinned L1 periods** ⟨reworded⟩ | [S `result_policy.py`; `ka_gochara_v5.py:119, 137–144, 472, 694–704, 763`] | observations to Pravāha (3.21) |
| F-A13 | Tulana validates only modes A/B; PRIORITY ranks without it; attribution credits it | [S `ranker.py:61–62`; `call_service_wrappers.ts:708`; `producer_editorial_review.ts:386`] | re-based ranker; wiring is R-6 |
| F-A14 | Sudarśana's `tri_lagna_convergence` is constant per chart | [S `logic.py:69–80, 110–117`] | removed; full method at step 2 |

---

## §5 · How the cards land in the plan's packets (re-keyed to plan v1.1 §9)

| Packet | Cards |
|---|---|
| **K0a vertical slice** | the vocabulary F-A1/F-A3 need; typed lord/frame identities; pinned `as_of`; the corrected G1 clock reference (3.20 (a)–(b)); candidate/publication contract; one assertion carried end-to-end to a registry-served result |
| K1 F2 | 3.1, 3.2 (full dossier after K2) |
| K2 F1 | 3.3, 3.11 |
| K7 (early, narrow) | routing and honest coverage propagation for 3.6/3.9/3.10 views; the two serving defects |
| K3 negative space | 3.4 (upstream doctrine/coverage only); adapters 3.12–3.14 as inputs |
| K4 jury | 3.19; G-J as a complete method output |
| Value checkpoint | ruling-10 ablation, amended, on the G1 field |
| K5 forecaster | 3.20 G1; 3.9 read model |
| K6 read models + registrar | 3.5, 3.6, 3.7, 3.8 (registrar after R-11) |
| K8 incremental | declarations per implemented asset; `uncited_legacy` / `uncited_extension` qualifications on 3.13–3.15 |
| L0 demands | scoped muhūrta parihāra rows (3.17); KP Reader V/VI ingestion (3.19 G-K); Sarvatobhadra grid remains blocked |
| Pravāha (not ours) | 3.21 observations; enrichment rows from §2 |

---

## §6 · The reviewer's questions, answered

1. **Competence partition (3.1):** descriptive tags plus applicability and dependency metadata; cross-tag comparison of the same outcome is permitted; shared ancestry forbids independence claims. Adopted.
2. **Scalar promise (3.3):** none; rule-local strength stays computable; the forecaster's feature mapping is specified in 3.20 G2's requirements. Adopted.
3. **Cancelled obstruction (3.4):** candidate retained, defeating evidence retained, effective state exposed; never left operationally active. Adopted.
4. **Two contested conventions (3.13, 3.15):** preserve the named legacy output with qualified status; a sourced variant is admitted separately; no automatic dual materialisation. Adopted; admission is the native's (R-8).
5. **Marriage parihāra (3.17):** marriage (and upanayana where stated) until a general-scope clause or an undertaking-specific passage is found. Adopted.
6. **Ablation (3.20):** amend and freeze the pre-registration against the minimally repaired G1 field before results are inspected; three arms; ordinary-period control. Adopted; the native approves the revised ablation (R-12).
7. **G-J before P8 (3.19):** G-J may proceed as a separately reviewed complete method output; no double credit when P8 later uses the same ancestry; no incomplete Jaimini rule inside jury logic. Adopted.

## §7 · What this document does not claim

No predictive validity for any elevated algorithm. No locator upgraded to `[D]` without a served-corpus hit this session; `[D-local]` rows are local OCR reads awaiting ingestion. Tājaka, kota, tithi-praveśa and the twelve-sign mūrti table remain `[U]`. KP text exists locally and is not served. The Muhūrta Cintāmaṇi predicates are quoted from the served translation and its ṭīkā; where the mūla is damaged (v. 88) the ṭīkā's reading is used and said so. Production universals (every stored generation, every live query) are the author's measurements, labelled [L], not static-code facts. The Gochara spec and its delegated rulings are cited, never reopened.
