---
artifact: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
canonical_id: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
version: "2.0"
status: SUPERSEDED
superseded_by: "FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (SEALED 2026-09-29) after independent review by Codex gpt-6-astra (REWORK) and Kimi K3 (PROCEED_WITH_AMENDMENTS), reconciled in RECONCILIATION_GOCHARA_ASTRO_v1_0.md — this version is retained as the text both reviewers read (sha256 270184f7…)"
date: 2026-09-29
reviewer: "Claude Fable 5.1 (astrology-first review, requested by the native 2026-09-29)"
supersedes: "FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v1_0.md — retained in place; its verified findings (§2) and worked examples (§2.2) are carried forward unchanged"
subject: "The Gochara family transit engine — the astrological content of λ_v3 as designed and as built in the '4.0' candidate (2026-09-28) on the canonical chart; restructured as a coarse-to-fine timing hierarchy; missing/overkill audit; efficient-implementation strategy"
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty) only — per the native's directive of 2026-09-29"
basis: >
  Same evidence base as v1.0: source at l3/gochara-autonomous-wp0-7 @ ec4c35110; production read-only 2026-09-29;
  the '4.0' delta and run reports under .run/wp10_tranche2/; LIFE_EVENT_LOG_v1_2.md; L0 ephemeris via
  ref_planet_position_get for the worked dates. No new corpus claim is made (F-32).
evidence_labels: "[S] source at ec4c35110, file:line · [L] live production read, 2026-09-29 · [R] repository record · [D] doctrine, text named, already verified in the served corpus by this campaign · [P] practice (widely taught; no primary verse claimed) · [I] inference / estimate from stated inputs · [J] my astrological judgment · [U] unverified — settle by count(*) against classical_text_chunks, never by assertion"
changelog:
  - "2.0 (2026-09-29): (1) the review is re-organised around the timing hierarchy the native proposed — factors that OPEN a window (years), NARROW it (months), PINPOINT it (days), and QUALIFY at any grain — with the engine's current terms mapped onto it (§1); (2) an explicit audit of what is significantly MISSING and what is OVERKILL in the current equation (§3); (3) a new §6 on implementing the same astrology efficiently — the hierarchy is sparse, so evaluate coarse-to-fine, store physical events once, and derive class views by lookup; (4) elevation plan re-cut by hierarchy level (§5); (5) external-review questions updated (§7). Verified findings and the three worked events (§2) unchanged from v1.0."
  - "1.0 (2026-09-29): first astrology-first review."
what_this_is_not: "Not an engineering review, except §6 where implementation strategy changes cost without changing astrology. Not a re-litigation of ruled items (D-1..D-3, R1–R10, N-1..N-22, M-1..M-8); where the build contradicts a ruling, the ruling stands."
next_step: "Native incorporates what is accepted; an independent review (GPT/Astra, effort max) reads this version. §7 lists what that review should adjudicate."
---

# Gochara — astrological review v2.0: the timing hierarchy, what is missing, what is overkill, and how to build it cheaply

## 0. Read this first

**What changed since v1.0, in one paragraph.** v1.0 established that the engine's *design* is a sound
Parāśari triad (natal promise × daśā permission × transit trigger, qualified by vedha, tārā and aṣṭakavarga)
and that the *build* has collapsed it to "any of six bodies within 5° of a few natal graha degrees, times a
per-class constant". This version keeps those findings (§2) and re-frames the whole engine around the way a
practitioner actually narrows time: **some factors open a window, some narrow it, some pinpoint it, and some
only qualify**. That framing (§1) does three things at once: it says which factor is allowed to act at which
grain (the Moon cannot open a decade; Saturn cannot pinpoint a day), it exposes what is missing and what is
overkill (§3), and it makes the efficient implementation obvious (§6) — because the hierarchy is sparse, the
expensive computation only ever runs inside windows the level above has opened.

**The verdict in one line.** Keep the frame, fix the collapse, re-cut the factors by grain, drop the noise
terms, and the same astrology computes in minutes instead of days — with *more* discriminating output, not less.

**How to read the verdicts.** SOUND · SOUND-UNWIRED · INVERTED · MISSING · UNCITED · OVERKILL (present, and
either dilutes the result or costs more than it contributes).

---

## 1. The timing hierarchy — how time is actually narrowed, and where each engine term sits

### 1.1 The model

A window for an event class is produced by a **cascade of four levels plus a qualifier layer**. Within a level
the factors combine by OR (any one can act); *across* levels they combine by AND (each level can only act
inside what the level above has opened). This is the multiplicative λ the design already has — split by grain,
with each factor assigned to the grain at which the doctrine lets it act.

| Level | Question it answers | Grain | Classical factors | Combines as |
|---|---|---|---|---|
| **L0 · Promise** | Does this chart signify this event at all, and how strongly? | lifetime (time-invariant) | signature houses, their lords, kārakas; strength of each (bhāva-bala, ṣaḍbala, dignity, relevant varga); yogas that signify the class; Jaimini kārakas/padas; sahams | produces the **target set** and a **promise strength** ∈ (0,1] |
| **L1 · Open** | Is the event licensed now? | years → months | Vimśottarī MD/AD (PD for month-grain) whose lords connect to the target set; Chara daśā for Jaimini targets; slow-body **residence** (Saturn, Jupiter, nodes in a signature house from the lagna, or in a favourable/unfavourable house from the Moon); Sade-Sati / Kaṇṭaka / Aṣṭama Śani as adverse-class licences | OR within → an **open interval set** |
| **L2 · Narrow** | Which months inside the open interval? | months → weeks | Jupiter/Saturn/node **degree contacts** to targets (conjunction, graduated dṛṣṭi); **double transit** on a house or its lord; Saturn/Jupiter over the śodhya-piṇḍa nakṣatras; retrograde passes; Mars contacts for adverse classes; Tājaka varṣa (year-lord, muntha, saham activation); AD/PD lord transiting a target or being transited | OR within, weighted by aṣṭakavarga bindus and agent nature |
| **L3 · Pinpoint** | Which days? | days | Moon over the signature house / lord / kāraka / running AD-PD lord (and trines); tārā-bala; tithi–nakṣatra quality; Sun/Mercury/Venus contacts to targets *as triggers*; eclipses on targets; Moon's own vedha | OR within; only produced inside L2 windows |
| **Q · Qualify** | How strong / obstructed is what fired? | any | gochara-vedha (from the Moon) with exceptions and vipareeta; BAV bindus of the transiting graha in the transited sign; SAV of the sign; kakṣyā contributor; natural and functional nature of the agent; transit dignity; mūrti; laṭṭā | multiplicative on the level it qualifies |

The **valence** of a window is the sign of the net supportive-minus-afflicting evidence *relative to the class*
(a favourable-from-Moon Jupiter supports a gain class and opposes a loss class), decided at the level that
produced the window.

### 1.2 The engine's current terms mapped onto the hierarchy

| Engine term today | Where it belongs | State (§2 for evidence) |
|---|---|---|
| PROMISE (noisy-OR of type-constant weights) | L0 | present in name only — 1.0 for every class |
| PERMISSION (12-system weighted vote, MD only) | L1 | collapsed to a per-class constant; MD only; 8 of 12 voters are OVERKILL (§3.2) |
| ACTIVITY — Saturn/Jupiter/node conjunction & dṛṣṭi | L2 | the only thing that reaches the score; aspects mirrored for Mars/Saturn; no BAV weighting; no graduation |
| ACTIVITY — Sun/Mercury/Venus/Mars conjunction & dṛṣṭi | L3 (trigger) | acting at L2 with a 5° orb — they *open* windows they should only *pinpoint* |
| ACTIVITY — sign/nakṣatra/kakṣyā ingress | L1 residence (slow) / Q (kakṣyā) | stored as zero-width instants; contribute nothing |
| bhāva / ārūḍha / mechanism-node spans | L1 residence | never materialised as spans; mechanism nodes resolved from the wrong frame |
| Moon (M-3 separate channel) | L3 | not produced; its vedha rows are attenuating L1/L2 windows |
| tārā (w23) | L3 | never fires |
| guru_shani_double_transit (permission voter) | L2 | demoted to a 0.10 vote; should be a first-class L2 mechanism |
| av_threshold, w21 | Q | frame mismatch; never reads the chart's bindus |
| Sade-Sati (permission voter → testimony) | L1 (adverse) | open-ended in engine; still weighted in '4.0' |
| quality_gates (vedha, laṭṭā, SBC) | Q | grade table mismatched; cancelled rows still count; favourable transits attenuate |
| mūrti, koṭa | Q | computed, unwired |
| era / month / day tiers | L1 / L2 / L3 | day tier is the argmax of a flat curve, not an L3 product |

### 1.3 The hierarchy on your own events (positions from L0 `[L]`, reading `[D][J]`)

Natal (Lahiri): Lagna Aries 12°26′ · Sun Cap 21°58′ (10) · Moon Aqu 27°03′ (11) · Mercury Cap 0°50′ (10) ·
Venus Sag 19°10′ (9) · Jupiter Sag 9°47′ (9) · Mars Lib 18°31′ (7) · Saturn Lib 22°26′ (7, exalted) ·
Rahu Tau 19°02′ (2) · Ketu Sco 19°02′ (8). Lords for Aries: 1L Mars · 2L/7L Venus · 3L/6L Mercury · 4L Moon ·
5L Sun · 8L Mars · 9L/12L Jupiter · 10L/11L Saturn.

**Marriage, 2013-12-11.**
- L1 open: Saturn resident in Libra = the 7th house, Aug 2012 → Nov 2014 `[I]`; Jupiter in Gemini aspecting Libra
  (5th aspect), mid-2013 → mid-2014 `[I]`. Intersection ≈ 12 months.
- L2 narrow: Saturn's **return** to its exalted natal degree (24°15′ transit vs 22°26′ natal on the day, 1.8°) and
  Jupiter's 5th aspect **exact on natal Saturn (2.1°) and on transiting Saturn (0.3°)** — a double transit on the
  7th *and* on the 7th-house Saturn, tightest Nov 2013 → Feb 2014. Ketu on the lagna degree (0.6°), Rahu in the 7th.
- L3 pinpoint: the day itself was a chosen muhūrta (Moon in Pisces, 12th) — a case where L3 is the family's
  choice, not the chart's trigger; the engine should report L2 and stop.
- What the '4.0' build sees: none of the above (Saturn's degree is not a marriage target; the 7th house is an
  inert span; the return relation is not attached to marriage).

**Twin daughters, 2022-01-03.**
- L1 open: Mercury MD / Rahu AD; Jupiter resident in Aquarius (11th; 5th from the natal Moon — a favourable
  Jupiter house from the Moon, Phaladīpikā rule 27 `[L]`), Nov 2021 → Apr 2022 `[I]`.
- L2 narrow: Jupiter's 7th aspect on **Leo, the 5th house**; Saturn **conjunct the 5th lord Sun** (18°01′ vs 21°58′,
  4°) — double transit on the 5th; tightest Dec 2021 → Feb 2022.
- L3 pinpoint: Moon at 29° Sagittarius — the 9th house, trine to the 5th, in the putra-kāraka's own sign `[J]`;
  Rahu (AD lord) in the 2nd (kuṭumba).
- What the '4.0' build sees: natal Jupiter's degree only; 5L unresolved, house aspects zero-width.

**Father's passing, 2018-11-28.**
- L1 open: Saturn resident in Sagittarius = the 9th house (father), Jan 2017 → Jan 2020 `[I]`; Mercury MD / Moon AD.
- L2 narrow: Saturn **over the 9th lord Jupiter's natal degree (3.6°)**; Sun (pitṛ-kāraka), Jupiter (9L) and
  retrograde Mercury clustered in the **8th house**; Ketu on natal Mercury (3°).
- What the '4.0' build sees: nothing relevant — natal Jupiter is not a bereavement target; 9L unresolved for
  parental_event.

The pattern: the events were produced by **L1 residence + L2 double transit on lords and houses**, the two
things the current score cannot represent. The things it *can* represent (fast bodies on kāraka degrees) are
L3 triggers wrongly promoted to L2.

---

## 2. Verified state of the build (carried from v1.0, unchanged)

| # | Finding | Evidence |
|---|---|---|
| 1 | PROMISE = 1.000 for all 27 classes (noisy-OR over type-constant weights) | promise.py:61-74 `[S]`; delta report `[L]` |
| 2 | PERMISSION is a per-class constant for the decade (union semantics over all candidate instants) | step06a_class_context.py:23-31 `[S]` |
| 3 | Only mahādaśā (level 1) is read anywhere | dasha_data.py:37; context.py:258-261 `[S]` |
| 4 | Sade-Sati permission open-ended (end 9999-12-31) in the engine; still weighted 0.10 in '4.0' despite testimony mode | engine.py:2006; legacy_semantics.py:109-129; step06b:141 `[S]` |
| 5 | Tārā-bala never fires (`"Moon"` vs `"MOON"` key; called with `None` in '4.0'); no served row carries a tārā value | w23:213 vs context.py:362 `[S]`; '3.0' rows `[L]` |
| 6 | 98.6 % of contacts are zero-width and contribute nothing; the score rests on 253 conjunctions + 369 dṛṣṭi + 29 returns per decade (chart-2 ledger as structural proxy) | episodes.py:399-401; step06b:209-228 `[S]`; ledger `[L]` |
| 7 | bhāva / ārūḍha / mechanism-node targets exist only as zero-width sign_ingress rows — house-level astrology never reaches the score | ledger `[L]` |
| 8 | Lords and yoga constituents "unavailable": 647 of 1,140 targets | step06 evidence `[R]` |
| 9 | Production resonance map is pre-WP3c: negative sensitive checks are still targets | map `[L]` |
| 10 | House frames mixed: Moon-relative `bg_transit_rules` matched to lagna houses and resolved from LAGNA | migration 266:53-55; writer.py:950; step06:410-419 `[S]` |
| 11 | Rule sign copied as-is: illness classes carry "favourable 6th" at +1; negatives clamped to 0 | writer.py:304-309; configuration_activity.py:133 `[S]` |
| 12 | Every '4.0' window "favourable" (1,435 of 1,435), incl. separation, deception, bereavement | legacy_semantics valence; delta report `[L]` |
| 13 | Mars 4/8 and Saturn 3/10 aspects mirrored (body at target + angle) in kernel and legacy | contacts.py:206-213; transit_search.py:320 `[S]` |
| 14 | Ingress into Aries / Aśvinī never a root (boundaries 30°…330°) — your lagna sign | contacts.py:259-262 `[S]` |
| 15 | No graduated dṛṣṭi (BPHS ch.26 śl.6–8 cited, not applied) | convention.py:39-40 `[S]` |
| 16 | Vedha grade names mismatched: 2–4 malefics and every laṭṭā take 0.35 | legacy_semantics.py:690-693 `[S]` |
| 17 | Inactive and vipareeta-cancelled vedhas still suppress; a clean favourable Moon-sign transit lowers λ by 15 % | legacy_semantics.py:696-783 `[S]`; rows `[L]` |
| 18 | Gochara-phala never a positive factor; AV gate compares Moon-relative to lagna houses and never compares bindus | engine.py:2093-2116; primitives.py:808 `[S]` |
| 19 | Kakṣyā lords never used; L1 kakṣyā grid never read (key mismatch) | context.py:669-672 `[S]` |
| 20 | No ṣaḍbala, dignity, functional nature, friendship, vargottama anywhere | `[S]` |
| 21 | Ontology `transit_triggers`, `vargas`, `dasha_rules` never read; every body vs every target | writer.py:939-944 `[S]` |
| 22 | Yogas attached by overlap; strength ignored; Kedāra on nearly every class | writer.py:820-834 `[S]`; map `[L]` |
| 23 | "afflicted" is a label, never checked, never consumed | writer.py:357-362 `[S]` |
| 24 | Equal peak heights within a class (childbirth: 13 × 0.6272); day tier = argmax of a flat curve | delta report `[L]`; step06b `[S]` |
| 25 | Overlay covers 1.26 % of the century; inside it 99 of 127 house-vedha rows are Moon transits | kala_vedha_gochara `[L]` |
| 26 | Mūrti computed, never in λ; w21 uses the rule's `min_sav_score` as a proxy, never the chart's bindus | `[S]` |
| 27 | Every ingress of a body attached to every point target regardless of sign (31,401 × 3 identical rows per relation) | step06 `[S]`; ledger `[L]` |

---

## 3. The audit you asked for: what is significantly missing, and what is overkill

### 3.1 Missing — significant (ordered by how much retrodictive power each would add on this chart `[J]`)

| # | Missing factor | Level | Why it matters | Source status |
|---|---|---|---|---|
| M1 | **Double transit as a first-class L2 mechanism** — Jupiter and Saturn both influencing a signature house *or its lord* (occupation or aspect), with the tightest overlap as the peak | L2 | produced all three worked events; today a 0.10 permission vote, target-framed, never a contact | practice `[P]` (20th-c. codification; the `bg_transit_rules` "Phaladīpikā §double-gochara" citation should be verified by count `[U]`) |
| M2 | **Lords as live targets** (7L, 5L, 9L, 10L …), and **running AD/PD lords** as dynamic targets and as agents | L0/L1/L2 | the lords carried every worked event; AD/PD lords are what a practitioner reads first | BPHS bhāva-lord doctrine `[D]`; daśā-lord transit `[P]` |
| M3 | **Aṣṭakavarga as the weight of every contact** — BAV bindus of the transiting graha in the transited sign; SAV of the sign; kakṣyā by contributor; śodhya-piṇḍa nakṣatras as targets for Saturn/Jupiter | Q / L2 | the classical transit-strength system; L1 computes all of it; nothing consumes it | BPHS ch.66–72 `[D]`; nāḍī PG1615/1616 `[D]` |
| M4 | **Promise from natal strength** (bhāva-bala, ṣaḍbala/dignity of lords and kārakas, relevant varga, yoga strength) | L0 | without it every class is equally promised and every chart is the same chart | L1 categories exist `[L]` |
| M5 | **Agent nature and class-relative valence** — natural/functional benefic-malefic, transit dignity, maitrī; `supports_class` on each (rule, class) | Q | Saturn on the 7th lord and Jupiter on the 7th lord are opposite events; today identical | L1 `graha_functional_class_per_ascendant`, `panchadha_maitri` `[L]` |
| M6 | **The Moon as the L3 pinpoint** (over house/lord/kāraka/AD-PD lord and trines; tārā; tithi–nakṣatra) inside L2 windows | L3 | the only classical source of day precision; M-3 removed the Moon from the century score without giving it its day role | muhūrta practice `[P]`; M-3 ruling `[R]` |
| M7 | **Slow-body residence as an L1 licence** — Saturn/Jupiter/nodes in a signature house (lagna frame) or favourable/unfavourable house (Moon frame) | L1 | the gochara-phala table is the oldest transit doctrine in the corpus and is never positive | Phaladīpikā XXVI `[D]` |
| M8 | **Graduated dṛṣṭi** (¼ 3/10, ½ 5/9, ¾ 4/8, full 7 and specials) | L2 | verse-cited; the warrant M-1 already leans on | BPHS ch.26 śl.6–8 `[D]` |
| M9 | **Tājaka**: sahams as class-specific targets (Vivāha, Putra, Karma, Mṛtyu, Roga…), varṣa-praveśa year-lord and muntha as an annual L1/L2 licence | L1/L2 | event-specific points already computed (70 sahams `[L]`), an entire timing school unused | Tājaka Nīlakaṇṭhī present; predicate to verify `[U]` |
| M10 | **Jaimini**: DK/PK/AK, UL, A7/AL, kārakāṃśa as targets; Chara daśā as their licence; argala as obstruction | L0/L1/Q | the ontology *cites* DK and putra-kāraka and then ignores them | `bphs_jaimini` present; cite by count `[U]` |
| M11 | **Retrograde passes** as L2 structure (1st/2nd/3rd pass over a target; the retrograde pass intensifies, the third delivers) | L2 | stored as `branch`, unused | practice `[P]`; M-2 testimony ruling `[R]` |
| M12 | **Eclipses on targets** with real instants | L3 | w26 dormant | grahaṇa chapters as cited `[D]` |
| M13 | **A day-level quality layer** (tithi, nakṣatra, vāra, Moon's vedha) — only inside L3 | L3 | today the Moon's vedha attenuates decade windows instead | Phaladīpikā XXVI; muhūrta `[P]` |

### 3.2 Overkill — present, and either diluting the result or costing more than it gives

| # | Present factor | Verdict | What to do instead |
|---|---|---|---|
| O1 | **The 12-system weighted permission vote** (8 daśā systems + 4 transit licences, fixed weights, one denominator) | OVERKILL — a weighted average of systems that mostly disagree is astrologically meaningless; it can never say *no* strongly | Vimśottarī MD/AD/PD as the spine; Chara daśā for Jaimini targets; Aṣṭottarī only where BPHS's applicability condition holds (verify the condition by count `[U]`); Yoginī/Kālacakra/Nārāyaṇa/Mudda/Naisargika as **corroborating testimony** on the window, never as voters |
| O2 | **Sun/Mercury/Venus (and Mars for gain classes) at L2 with a 5° orb** | OVERKILL — they open windows they should only pinpoint; at 1°/day a 5° orb is a 10-day box on a body that returns every year | move to L3 as triggers inside L2 windows; per-agent orbs (Saturn/Jupiter wide, Sun/Mercury/Venus narrow) |
| O3 | **Kakṣyā crossings for Sun/Mercury/Venus** (826,893 dropped rows per decade) | OVERKILL — kakṣyā qualifies the slow transits; fast-body kakṣyā crossings are noise | keep kakṣyā for Saturn/Jupiter/Mars only, contributor-qualified (M3) |
| O4 | **Generic nakṣatra and sign ingress attached to every point target** | OVERKILL — an ingress is a *global* event of the body, not a contact with a target | one global boundary table per body (§6.2); the target-specific version is "transit over the significator's *own* nakṣatra / sign" (janma-nakṣatra, piṇḍa nakṣatras) |
| O5 | **sensitive_degree targets** (mṛtyu-bhāga, gaṇḍānta, kartari, puṣkara on kārakas) | OVERKILL as *targets* — they duplicate the graha's degree | fold into L0 as qualifiers of the graha's promise (a puṣkara-degree Venus is a stronger marriage promise; a mṛtyu-bhāga Saturn is a sensitivity for adverse classes) |
| O6 | **dasha_lord_portfolio** as a target type | OVERKILL — it is the kāraka list again at 0.8 | replace with running AD/PD lords as dynamic targets (M2) |
| O7 | **Yoga constituents by overlap** (Kedāra everywhere; rāja yogas on childbirth) | OVERKILL — makes all classes' target sets alike | yogas enter L0 promise via a cited yoga→class map, strength-scaled; constituents become targets only for the classes the yoga signifies |
| O8 | **Returns for Sun/Mercury/Venus/Mars** | OVERKILL — annual/biannual returns are muhūrta-level | keep returns for Saturn, Jupiter, nodes; the Sun's return only as the Tājaka varṣa-praveśa anchor |
| O9 | **Sarvatobhadra approximation in the gate** | UNCITED + OVERKILL — a cyclic-opposite stand-in attenuating at 0.85 | out of the gate until a grid with a named school exists; testimony only |
| O10 | **Moon vedha rows in the century gate** (99 of 127) | OVERKILL at that grain | Moon's vedha belongs to L3 only |
| O11 | **Three materialised tiers for the whole century** (era/month/day, 4,415 rows per decade) | OVERKILL — day rows are pseudo-precise and never read except for the top windows | materialise L1+L2 (era/month); produce L3 on demand for ranked windows and cache (§6.4) |
| O12 | **Nodal dṛṣṭi (w30)**, mudda/kālacakra votes, koṭa in λ | already removed / never wired — keep them out | testimony surfaces only |

### 3.3 What is *not* overkill and should stay exactly as ruled

Sidereal Lahiri on Swiss (D-1); mean node (N-4); linear orb decay (M-1); persisted contacts with identity and
coverage (N-7); vedha exceptions and vipareeta (M-8); no nodal dṛṣṭi (N-14); Sade-Sati as testimony rather than
weight (N-15) — *provided* Saturn 12/1/2 from the Moon still appears through the cited unfavourable rule at L1;
uncapped peaks (N-17); kakṣyā bindu qualification (N-22) once it is contributor-level; honest nulls and
`uncited_extension` everywhere.

---

## 4. Component assessment (condensed from v1.0 §3; mapped to levels)

| Component | Level | Verdict | One-line repair |
|---|---|---|---|
| Frame of reference | all | INVERTED (partly) | explicit `frame ∈ {moon, lagna, graha}` on every rule/target; mechanism nodes from the Moon; bhāva residence from the lagna |
| Gochara-phala table + vedha | L1 / Q | SOUND-UNWIRED / INVERTED | positive at L1 for gain classes (class-relative sign); vedha as its obstruction with M-8; fix grade table, honour cancellation; Venus 11→3/12→6 to verify against PG323 `[U]` |
| Dṛṣṭi | L2 | INVERTED (Mars, Saturn) / MISSING (graduation) | body = target − angle; hand-computed regression; ch.26 graduation weights |
| Aṣṭakavarga | Q / L2 | MISSING in build | BAV weight per contact; SAV gate on the chart's own SAV; kakṣyā by contributor (G-10); piṇḍa nakṣatras as targets |
| Daśā | L1 | COLLAPSED | per-instant; MD/AD/PD; applicability-gated; AD/PD lords as targets/agents |
| Promise | L0 | MISSING | strength-based; varga-aware; yoga strength; normalised |
| Agent–target relationship / valence | Q | MISSING | natural + functional nature, transit dignity, maitrī; `supports_class` |
| The Moon | L3 | SOUND ruling, UNBUILT role | day channel inside L2 windows; Moon vedha only there (reconciles M-3 with Astra R4) |
| Nodes | L1/L2 | SOUND (N-14) | agents and targets; returns kept; Rahu 5/9 as testimony only |
| Sade-Sati & Saturn cycles | L1 | SOUND ruling, INCOMPLETE | interval testimony on adverse classes (L1 already has all the periods); rule 39 at L1 as an ordinary cited unfavourable rule |
| Tārā, mūrti, laṭṭā, SBC, koṭa | L3 / Q | SOUND-UNWIRED / UNCITED | tārā at L3; mūrti after verifying its rule form (nakṣatra mod-4 vs rāśi 1/6/11 …) `[U]`; laṭṭā severity; SBC and koṭa as testimony |
| Retrograde / stations / returns / eclipses | L2 / L3 | partly SOUND | passes as L2 structure; stations a real relation; returns slow bodies only; eclipses wired |
| Yogas | L0 | UNCITED, mis-attached | yoga→class map, strength-scaled, into promise |
| Vargas / Jaimini / Tājaka / KP | L0–L2 | MISSING (all computed at L1) | varga promise; DK/PK/AK/UL/kārakāṃśa; sahams + varṣa; KP testimony only (not in corpus) |
| Orbs and grain | L2 / L3 | UNCITED (declared) | per-agent orbs; no day row that is not L3-derived |

---

## 5. Elevation plan, re-cut by level

**Tier 0 — restore the design (defects; before any calibration).** Aspect direction (§2 #13) · frame on rules
and targets (#10) · residence spans for bhāva/ārūḍha/mechanism targets (#7) · lords and yoga constituents
resolved (#8) · permission per instant, MD/AD/PD, Sade-Sati end honoured, testimony removes the weight
(#2, #3, #4) · class-relative valence (#11, #12) · vedha gate: grade names, cancellation, no attenuation on
a clean favourable transit, slow bodies only at L1/L2 (#16, #17, #25) · tārā key, Aries/Aśvinī root, L1
kakṣyā key (#5, #14, #19) · rebuild the map on R-1..R-6 (#9).

**Tier 1 — the hierarchy itself.**
- L0: promise from strength (M4); yoga→class map (O7); sensitive checks folded into promise (O5).
- L1: daśā spine with applicability (O1); slow-body residence as licence in both frames (M7); Sade-Sati /
  Kaṇṭaka / Aṣṭama as adverse-class licences.
- L2: double transit as a mechanism (M1); Jupiter/Saturn/node degree contacts with graduated dṛṣṭi (M8) and BAV
  weighting (M3); AD/PD lords as targets and agents (M2); retrograde passes (M11); piṇḍa nakṣatras (M3).
- L3: the Moon channel inside L2 windows (M6); Sun/Mercury/Venus demoted to triggers (O2); tārā, tithi–nakṣatra,
  eclipses (M12, M13).
- Q: agent nature and valence (M5); kakṣyā by contributor (M3); SAV gate; mūrti once verified.

**Tier 2 — enrichment.** Tājaka sahams and varṣa (M9) · Jaimini targets and Chara licence (M10) · varga
targets as testimony · argala as obstruction `[U]`.

**Tier 3 — measurability.** Retrodiction on the 36 LEL events by **rank within class and year**, with
per-mechanism attribution (which level and which factor produced the window) so doctrine can be ablated ·
cross-class window-set correlation as a diagnostic (today near 1.0) · factor-level deltas on the real chart
per Tier-1 item · calibration stays at L5 (ph_pramana NO-SCORING).

---

## 6. Implementing the same astrology efficiently — same value, a fraction of the cost

### 6.1 The principle: the hierarchy is sparse, so compute it top-down

An ācārya never scans every day of a life. They find the daśā, then the slow transits inside it, then the
Moon inside those. The current build does the opposite: it enumerates every body × every target × every
relation over the whole horizon (1.35 M episodes per decade), refines each to Swiss precision, discards 90 %
as duplicates, stores the remaining 138 k of which 98.6 % contribute nothing, then samples λ daily for 27
classes over the century. **Every one of those costs is a consequence of evaluating all grains at once.**
Evaluate coarse-to-fine and each level runs only inside the intervals the level above opened.

Estimated fraction of the century that survives each level for a typical class `[I]`: L1 (daśā lords
connected to the target set, MD/AD) ≈ 25–40 %; × slow-body residence on a signature house ≈ 25–35 % → L2 runs
on ≈ 8–15 % of the century; L2 contacts of Jupiter/Saturn/nodes inside that → a few dozen candidate months per
class per century; L3 runs only inside those months (or only for the top-N ranked ones on demand). Fast-body
enumeration — the bulk of today's cost — is confined to ≈ 5–10 % of the horizon and is trivial there.

### 6.2 Store physical events once; derive class views by lookup

1. **Global boundary table, per body, computed once for all charts.** Sign, nakṣatra and kakṣyā crossings,
   stations, retrograde loops and eclipses are properties of the sky, not of a chart. For 1900–2150 that is on
   the order of 10⁴–10⁵ rows in total `[I]` (Sun ≈ 12 sign / 33 nakṣatra / 96 kakṣyā crossings per year; Saturn
   ≈ 0.4 / 1.1 / 3.2 per year plus retrograde re-crossings). Today the same crossings are re-solved per chart and
   per target: 31,401 × 3 identical rows for one body-relation on one chart-decade (§2 #27). Slow-body residence
   intervals (L1) are then a lookup, not a solve.
2. **Deduplicate targets by physical point before solving.** The 1,140 resonance rows on your chart resolve to
   roughly **ten point longitudes** (the nine grahas and the lagna — kārakas, lords, dasha-portfolio and
   sensitive checks all name the same degrees) plus twelve house spans, twelve ārūḍha signs and, once added,
   a few dozen sahams and Jaimini points. Solve each (body, point, relation) **once**; attach the list of
   (class, role, weight) as labels. The H-6 independence principle then holds by construction instead of by a
   post-hoc 1.2 M-row dedupe.
3. **Contacts per chart-century become small.** Roots per point per century `[I]`: Saturn ≈ 3.4 per level,
   Jupiter ≈ 8, nodes ≈ 5, Mars ≈ 55, Sun/Venus ≈ 100, Mercury ≈ 130; with 2–4 aspect levels per body that is
   ≈ 900 roots per point, ≈ 40 k for 40 points — before L1 pruning of the fast bodies, which removes most of
   them. Compare 13.5 M enumerated per century today.
4. **Refine lazily and label honestly.** Bracket every root from the spline (microseconds). Refine to Swiss
   only what survives L1 and is slow-body or top-ranked; store `precision_regime = spline | swiss` on the row
   (the spike showed spline t_exact within ~1″ for slow bodies `[R]`, more than enough for month grain). This
   respects ADK-0019 — nothing is *labelled* Swiss that is not — while removing the refinement cost from the
   99 % that never needed it.

### 6.3 Interval algebra instead of daily sampling

Every factor in the hierarchy is an **interval** (daśā periods, residences, contact spans with linear decay)
or a **point** (exact instants). λ is therefore piecewise-linear with breakpoints at the union of interval
endpoints. Evaluate it at the breakpoints and at the analytic maxima of the decay segments — no 1-day grid,
no 986 k evaluations per century, no ±7-day argmax scan. The plan's own §4.5 already priced closed-form
evaluation at 0.013 ms per instant `[R]`; with breakpoints instead of a grid the projection for 27 classes over
a century is seconds. Peaks, eras and months fall out of the same breakpoint set exactly, not approximately.

### 6.4 Produce the day tier on demand

L3 (Moon channel, tārā, tithi–nakṣatra, fast-body triggers) is computed **only inside L2 windows** — for the
ranked top-N windows at build time and for any other window when a query asks for it — and cached with its
own coverage record. This is M-3's "on demand" principle applied consistently: a century of day rows nobody
reads is not an asset, and the Moon channel over a month is a sub-second computation.

### 6.5 Re-scoring is free; rebuilding is rare

Because physical contacts are stored once with identity, **every doctrine change in §5 is a projection change**
— new weights, new frames, new valence rules re-score the same ledger in seconds. A ledger rebuild is needed
only when an *input* changes (L1 facts, ephemeris substrate, the target set), and the input-generation vector
per target lets it be incremental: recompute the points whose facts changed, not the chart.

### 6.6 What this looks like as a build (per chart, full century) `[I]`

| Step | Work | Expected cost |
|---|---|---|
| 0 | Global tables (arcs, boundary events, stations, eclipses) | once per substrate version; reused by every chart |
| 1 | L0: target set + promise from L1 facts | milliseconds (SQL over `chart_facts`) |
| 2 | L1: daśā intervals × residence intervals per class | milliseconds (lookup + interval intersection) |
| 3 | L2: slow-body roots on ≈ 40 points, bracketed from arcs, refined inside L1 intervals | seconds |
| 4 | L2 projection by interval algebra; BAV/vedha/nature weights; ranking | seconds |
| 5 | L3 for top-N windows (Moon channel, triggers, tārā) | seconds; the rest on demand |
| 6 | Manifest, coverage, publication | as today |

Order of magnitude: **under a minute for the ledger, low single-digit minutes end-to-end**, against ≈ 11–12 h
projected for the current full-century pipeline — and the output is *more* discriminating because the fast-body
and boundary noise that flattened every peak is no longer in the score.

### 6.7 What to keep from the current build

The kernel's arc index and Swiss refinement; sidereal convention vector; contact identity (`contact_id`),
coverage manifest and publication generations; the vedha writer's Moon-frame geometry and M-8 rows; the L1
fact inventory. What changes is *what* is enumerated, *where* (inside opened intervals), and *how the score is
assembled* (breakpoints, not samples; levels, not one flat product).

---

## 7. Questions for the external review (GPT/Astra, effort max)

1. Is the four-level hierarchy (§1.1) the right decomposition of classical timing, and is each factor assigned
   to the correct grain? In particular: should Mars sit at L2 for adverse classes only, or at L3 always?
2. Confirm or refute, independently: the dṛṣṭi direction (contacts.py:206-213); the house-frame mixing on
   mechanism nodes; the Aries boundary gap.
3. Adjudicate, by corpus count: the mūrti-nirṇaya rule form; the Venus vedha pairs (11→3/12→6 vs 11→6/12→3);
   the "Phaladīpikā §double-gochara" citation on `bg_transit_rules`; the Aṣṭottarī applicability condition;
   the Jaimini UL/DK transit rules; the Tājaka saham predicate.
4. Which daśā systems belong in L1 as *licence* and which only as testimony (§3.2 O1)?
5. Which BAV-bindu → weight mapping to admit, and from which text.
6. Should the day tier be produced at all at build time, or strictly on demand (§6.4)?
7. Which class signatures in §1 of v1.0 need correction (career_change with Rahu as sole kāraka;
   property_acquisition with a single negative mechanism; bereavement without 9L/Sun for the father;
   marriage without UL/DK; childbirth without PK/5L-of-5L).
8. Does §6's sparse coarse-to-fine evaluation lose any admissible classical mechanism? (Name it if so.)
9. Rank the Tier-1 items by expected retrodictive gain on this chart.

---

## 8. Limits

- No new presence/absence claim was made against `classical_text_chunks`; every `[U]` is a count someone must run.
- Fractions and costs in §6 are estimates from stated motion rates and the measured '4.0' figures (`[I]`), not
  measurements; they are meant to be falsified by a first implementation, not quoted.
- Chart 2's ledger was used only as a structural proxy for chart 1's deleted '4.0' contacts.
- Nothing here changes any ruling; where the build contradicts a ruling, the ruling stands.
