---
artifact: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
canonical_id: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
version: "3.0"
status: SEALED
sealed_on: 2026-09-29
sealed_by: "Claude Fable 5.1, under the native's delegated instruction recorded verbatim in §9 ('…let them review it thoroughly and come back to you, which you finally incorporate and seal the plan')"
seal_scope: "SEALS the astrological doctrine model, the verified defect inventory, the elevation plan, the implementation contract and the validation protocol for the Gochara family. DOES NOT seal any claim of predictive accuracy (to be earned under §5 Tier 3), DOES NOT authorise a build, migration, publication or hold release, and DOES NOT change any native ruling — eight ruling requests are carried in §7 for the native."
supersedes: "FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md (the text both external reviewers read; retained) · v1_0.md (retained)"
reviews_incorporated: "ASTRA_REVIEW_GOCHARA_ASTRO_v1_0.md (Codex gpt-6-astra, reasoning max — REWORK) · KIMI_K3_REVIEW_GOCHARA_ASTRO_v1_0.md (Kimi K3, effort max — PROCEED_WITH_AMENDMENTS) · reconciled finding-by-finding in RECONCILIATION_GOCHARA_ASTRO_v1_0.md; every accepted amendment is in this text, every refuted one is recorded there with its evidence"
evidence: "FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md — every production figure cited below, with its SQL predicate (E1–E9); corpus counts against the served classical_text_chunks run 2026-09-29 (§8)"
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty) only, per the native's directive of 2026-09-29"
evidence_labels: "[S] source at l3/gochara-autonomous-wp0-7 (ec4c35110 / 507a759bf), file:line · [L] production read-only 2026-09-29 (appendix) · [D] doctrine verified in the served corpus (text:page) · [P] practice, no primary verse · [I] estimate · [J] judgment · [U] unverified — to be settled by a stated count or read"
changelog:
  - "3.0 SEALED (2026-09-29): incorporates both external reviews. Structural changes: the timing hierarchy is retained as ORDER OF INQUIRY and COMPUTATION STRATEGY, no longer as a necessary-condition law; admissibility is a UNION OF SOURCE-QUALIFIED RULE PATHS, each intersecting its own prerequisites (Codex B; Kimi B); the flat target list is replaced by an EVENT-SPECIFIC RELATIONSHIP RECORD (Codex C1; Kimi C); valence carries three fields (Codex B). Corrections: twins example (Jupiter is 1st from the Aquarius Moon — both reviewers); father example is not a double transit (Codex F3); Venus vedha pairs stay as coded — the served Phaladīpikā PG323 confirms 12→6/11→3 (Codex D3; Kimi's amendment refuted); plateau figure 27 of 41 (Kimi A24); Sun crossings 27/yr; precision_regime semantics preserved. Seven new Tier-0 defects verified at source (Codex C2–C6). New verse-cited mechanisms from the served corpus: daśā-lord transit rules (Phaladīpikā XX.34–38), kakṣyā-by-contributor (XXIII), piṇḍa-nakṣatra timing (XXIV), joint Jupiter/Saturn varga rule (XVII.12), adverse 12/8/1 residence (XXVI.11), transit-to-transit modification (XXVI.30), aṅga-gochara (XXVI.35–40), lagna-frame results (Yavana Jātaka 45–48), Tājaka sahams/muntha/varṣeśa (Devanagari). Sade-Sati/Kaṇṭaka withdrawn as licences; sahams moved to the annual path; cost section rewritten as a measurable contract."
  - "2.0 (2026-09-29): hierarchy; missing/overkill; efficiency. 1.0 (2026-09-29): first review."
---

# Gochara — astrological review v3.0 (SEALED): doctrine model, verified defects, elevation plan, implementation contract

## 0. Read this first

**What this seals.** A plan, not a result. Both reviewers confirmed the defect inventory (Codex 15 confirmed / 10 partly /
0 refuted; Kimi 19 / 5 / 0) and both refused to let the *doctrine* be sealed as written in v2.0 — Codex because the
four-level cascade was stated as a universal law and several repairs conflicted with rulings; Kimi because of one
doctrinal error, two numeric errors and three omissions. Every one of those objections is corrected below or carried as
a ruling request (§7). What remains unsealed is exactly what should be: whether the corrected engine predicts. That is
§5 Tier 3's job, and it now precedes mechanism-building rather than following it.

**The one-paragraph model.** A window for an event is admitted when **some admitted rule path's prerequisites all hold**
(a daśā-lord path, a Moon-frame gochara path, a lagna-frame bhāva path, a double-transit path, an aṣṭakavarga path, a
Moon-channel path …), each path stating its own frame, its agent→relation→object, its prerequisites and its source.
Inside admitted windows a **score ranks**, assembled from the factors the path names, weighted by the chart's own
aṣṭakavarga and the agent's nature, and reported with three valence fields (evidence for, evidence against, outcome for
the native). The practitioner's order of inquiry — promise, period, slow transit, day — is the **computation strategy**:
evaluate coarse first and prune an interval only when a *necessary* predicate of the path is demonstrably false. Grain
assignments (Saturn narrows months, the Moon pinpoints days) are **authoring defaults**, because the corpus itself has the
Sun selecting a month (BPHS ch.70) and Mars delivering gains (ibid.).

**A lesson written into the seal.** v2.0 attached a Phaladīpikā rule number to a miscounted house (Jupiter in Aquarius
called "5th from the Moon" when the Moon *is* in Aquarius). Both reviewers caught it. It is the same error class this
review condemns in the engine — a citation without the count behind it — and it is why §8 lists every remaining `[U]`
with the predicate that will settle it, and why the sealed plan cites nothing its evidence appendix does not contain.

---

## 1. The verified state of the build

### 1.1 The twenty-seven findings (v2.0 §2), as adjudicated

| # | Finding (as sealed) | Status |
|---|---|---|
| 1 | PROMISE = 1.000 for all 27 classes — noisy-OR over type-constant weights measures target *presence*, not promise | CONFIRMED (both) |
| 2 | PERMISSION is a per-class constant over the decade (union over candidate instants) | CONFIRMED (both) |
| 3 | The Gochara loading path reads mahādaśā only (level 1); AD/PD never enter the score | CONFIRMED, scope narrowed (Codex) |
| 4 | Sade-Sati open-ended in the engine; 0.10 weight retained in '4.0' despite testimony mode | CONFIRMED (both) |
| 5 | Tārā-bala never fires (`"Moon"` vs `"MOON"`; '4.0' passes `None`); served '3.0' rows carry no tārā term (E4) | CONFIRMED (both) |
| 6 | All boundary contacts are zero-width and contribute 0; 98.6 % of the ledger (E1). Repair = retain residence/state, not broaden instants | CONFIRMED, repair re-scoped (Codex) |
| 7 | The kernel computes `ResidenceSpan`s; enumeration stores only their ingress instant — house-level targets never reach the score (E1) | CONFIRMED (both) |
| 8 | 647 of 1,140 targets "unavailable" (595 yoga, 52 lord); the lord resolver exists and fails on missing facts | CONFIRMED, diagnosis corrected (Codex) |
| 9 | Production resonance map is pre-WP3c: 154 of 176 sensitive-degree targets are negative-result checks (E3) | CONFIRMED by predicate (E3) |
| 10 | **Two** frame errors: Moon-relative rules matched to lagna house numbers *and* resolved from LAGNA | CONFIRMED (both) |
| 11 | Rule polarity copied class-blind; negatives clamped out of activity (they reach only the afflicting channel) | CONFIRMED (both) |
| 12 | All 1,435 era rows "favourable" (of 4,415 rows) incl. separation, deception, bereavement | CONFIRMED (both) |
| 13 | Mars 4/8 and Saturn 3/10 mirrored (`target + angle`); Jupiter's labels swap but its root set survives; the 7th survives | CONFIRMED with independent arithmetic (both) |
| 14 | No 0° boundary root (Aries / Aśvinī); **and** the residence helper can fabricate an Aries ingress at horizon start (§1.2) | CONFIRMED (both) |
| 15 | No graduated dṛṣṭi; BPHS ch.26 cited, not applied | CONFIRMED (both) |
| 16 | Vedha grade names mismatch → 2–4 malefics and laṭṭā fall to 0.35; scale is the PG353 *battle* scale (uncited generalisation) | CONFIRMED (both) |
| 17 | Inactive and cancelled vedhas still suppress; a clean favourable transit ×0.85; duplicates multiply twice (E2) | CONFIRMED (both) |
| 18 | AV gate compares Moon-relative to lagna houses and never resolves bindus; favourable mechanism weights exist but are not evaluated gochara-phala | CONFIRMED, scope narrowed (Codex) |
| 19 | Kakṣyā lords never used; L1 grid key mismatch; a 672-row prastāra emission already exists in the strength writer | CONFIRMED (both) |
| 20 | No ṣaḍbala / dignity / functional nature / maitrī **consumed by this scoring path** | CONFIRMED, scope narrowed |
| 21 | Ontology `transit_triggers`, `vargas`, `dasha_rules` never read; point targets Cartesian over bodies (interval targets, returns and nodes excepted) | CONFIRMED, scope narrowed |
| 22 | Yogas attached by overlap; strength ignored | CONFIRMED (both); prevalence per class in E3 |
| 23 | "afflicted" is a label, never a predicate | CONFIRMED (both) |
| 24 | Plateau: **27 of 41** childbirth era rows at 0.627200 (marriage 32/50, deception 39/66 — E5); day tier is an argmax of the same curve | CONFIRMED, figures corrected |
| 25 | Overlay covers 2026-07-29 → 2027-11-01 only; 99 of 127 house-vedha rows are Moon transits (E2); absent coverage reads as 1.0 not "unavailable" | CONFIRMED by predicate (E2) |
| 26 | Mūrti computed, never in λ; w21 uses the rule's `min_sav_score` as a proxy | CONFIRMED (both) |
| 27 | Boundary events enumerated per target (31,401 × 3 identical rows, E1) — physical identity must be label-independent | CONFIRMED by predicate (E1) |

### 1.2 Seven further defects raised by the reviews and verified at source `[S]`

| id | Defect | Where |
|---|---|---|
| N1 | **M-1 is implemented as a time triangle, not angular separation** — `linear_no_box_decay` interpolates t_in→t_exact→t_out; the ruling is `1 − |Δ|/orb`. Coincides only under constant angular speed; wrong around stations | step06b_windows_projection.py:209-228 vs engine.py:1090-1120; SHEET M-1 |
| N2 | **Residence helper fabricates an exact ingress** at a clipped horizon start (`t_exact = ca`, `exact_crossing=True`, `completeness_state='applied'`) and searches only the lower boundary (retrograde entries come through the upper) | episodes.py:443-508 |
| N3 | **Episodes with `t_exact=None` are dropped** — a contact overlapping the horizon whose exact centre lies outside becomes absence instead of a truncated span | step06_enumerate_episodes.py:614-619 |
| N4 | **Vedha writer collapses temporal structure** — every obstructor overlapping any part of a residence is counted as simultaneous; first obstruction and first cancellation only; one outer row per primary residence | ka_vedha_gochara/writer.py:455-568 |
| N5 | **90-day producer separation filter retained** contrary to N-17 (moved to serve time) | step06b:417-424 (`MIN_PEAK_SEPARATION_DAYS`) |
| N6 | **`birth_anchor` kill-switch is prose only** — 43 era / 43 month / 43 day windows produced for the natal epoch class | resonance writer.py:288-296; run report |
| N7 | **Mūrti `verse_cited` / `corpus_verifiable=true` are set whenever a grade computed** — a §N.8 earned-signal defect; the rule form is not in the served corpus (§8) | ka_moorti_nirnaya/logic.py:81-86 |
| N8 | **Bindu/rekhā polarity undeclared** — L1's `ashtakavarga_bindu*` stores PyJHora's benefic "dots"; the Santhanam BPHS edition names the benefic mark *rekhā* and the malefic *bindu*, so a "BPHS ch.66" citation on a `bindu` column can carry the opposite polarity | ga_strength_writer.py:1148-1167; BPHS2:35666-35684 |
| N9 | **LEL chart-state annotations are unreliable** for the three worked events (Rahu "in Aries", Moon "in Pisces", natal Ketu "in Leo", "Jan 2020 ≈ 2 months after Nov 2018") — the native's dated observations stand; the computed annotations must be regenerated from L0/L1 before any retrodiction | LEL:998-1002, 1148-1162 vs E8 |

---

## 2. The doctrine model (sealed)

### 2.1 Order of inquiry — retained as workflow and computation strategy

| Level | Question | Default grain | Typical factors |
|---|---|---|---|
| L0 Promise | Does this chart signify this event, for whom, how strongly, with what condition? | lifetime | signature houses, lords, **occupants**, kārakas, dispositors, mārakas-of-the-house; their strength *and condition* (kept separate); yogas with a cited yoga→event relation; Jaimini kārakas/padas inside a declared Jaimini path |
| L1 Period | Is it licensed now, under which path? | years→months | nested Vimśottarī MD/AD/PD with event-relevant relationships (lordship, occupancy, dispositor, association); Chara daśā for Jaimini targets; applicability-gated Aṣṭottarī (fails on this chart); annual Tājaka context for the annual path |
| L2 Transit support | Which months? | months→weeks | slow-body residence in **both** frames (as *support*, not a substitute period); Jupiter/Saturn/node degree contacts with graduated dṛṣṭi; double transit on house-or-lord; daśā-lord transit rules (Phaladīpikā XX); piṇḍa-nakṣatra transits; Sun's month where a rule uses it; Mars where a rule uses it; retrograde pass structure |
| L3 Finer timing | Which days? | days | on demand: Moon over the path's objects and their trines *as the path specifies*; tārā; tithi–nakṣatra; the Moon's own vedha; eclipses on objects with source-defined sensitivity; day quality only for elections |
| Q Qualify | How strong, how obstructed? | any | vedha scoped to the specific primary transit with exceptions/vipareeta intervals; graha-specific BAV, SAV bands, contributor kakṣyā; transit dignity and combustion (Phaladīpikā XXVI.30–32); natural/functional nature and maitrī as *interpretive* modifiers |

Grain is a default for rule authors; a rule path may place any agent at any grain its source supports. Era/month/day are
**output resolutions**, produced by the rule paths that actually operate at those grains — never by clipping a curve.

### 2.2 Admissibility and ranking

```
W_event = ⋃ over admitted rule paths r  ( ⋂ over prerequisites p of r  I_p )
score(t) inside W_event = Π of the soft factors the path names (ranking only)
```
- A path is admitted when its source status is `[D]`, or `[P]` with `uncited_extension=true` and a native ruling.
- Pruning: an interval is discarded for path r only when a **necessary** predicate of r is demonstrably false there.
  Unknown applicability is not false applicability (Codex D8). "Uncomputed" is never reported as "empty".
- No soft factor may zero an admitted window; only L0 absence (no relationship at all) and a path's own failed
  prerequisites exclude.
- Aliases (Jupiter as kāraka, as 9L, as yoga constituent) are **role edges on one physical contact**, never independent
  observations; noisy-OR across them is withdrawn.

### 2.3 The relationship record — the object that replaces the flat target list

```
event_class · affected_person (native | father | mother | spouse | child | …)
frame (moon | lagna | graha:<X> | dasha_lord | bhavat_bhavam:<house>)
agent → relation → object   (object = degree point | sign span | star | derived point | varga position | saham)
role of object (lord | occupant | karaka | dispositor | maraka_of_house | period_lord | yoga_constituent | pada)
prerequisites (natal condition · period · residence · applicability)
temporal support · coverage · precision
source (text:page | practice) · qualification (verse_cited | uncited_extension | testimony)
evidence_for_occurrence · evidence_against_occurrence · outcome_valence_for_native · severity
```
Physical geometry (one row per solved contact), interpretive rules (records above) and evaluated windows are **three
objects** (Codex E6); a doctrine change re-evaluates windows; a frame/aspect/target-generation change re-solves geometry.

### 2.4 Admitted rule paths — initial catalogue with source status

| path | content | source | status |
|---|---|---|---|
| P1 daśā-lord | the running MD/AD/PD lord's own transit through its svakṣetra/exaltation/friendly sign promotes its bhāva; through debility/inimical/combustion → misery; **Sun or Jupiter transiting the bhukti lord's exaltation sign delivers the auspicious bhukti's fruit**; AD/PD lords as objects and agents; dispositor and association relationships | Phaladīpikā XX śl.34–38 (PG249–250) `[D]`; node-dispositor `[P]` | admit |
| P2 Moon-frame gochara-phala | per-planet favourable houses from the janma-rāśi with vedha, Sun↔Saturn / Moon↔Mercury exceptions, vipareeta; **adverse residence** Saturn/Sun/Mars/Jupiter in 12/8/1 → danger to life, fall, loss (adverse classes) | Phaladīpikā XXVI śl.1–8 (PG321–323), śl.11 (PG335) `[D]`; M-8 `[R]` | admit — Moon-lagna is "most important" for gochara-phala (śl.1); it licenses the **native's** fortune, not a relative's event |
| P3 lagna-frame bhāva transit | slow-body residence in / aspect on a signature house and its lord, per house from the ascendant; relatives via bhāvāt-bhāvam frames (father = 9th; its 2nd/7th/8th) | Yavana Jātaka ch.45–48 `[D]`; Parāśari bhāva doctrine `[D]`; māraka-of-house `[P]` | admit |
| P4 double transit | Jupiter **and** Saturn both influencing (occupation or aspect) a signature house **or its lord**; tightest overlap = peak | modern practice (K.N. Rao) `[P]`, `uncited_extension`; sole primary joint precedent Phaladīpikā XVII śl.12 (PG216: Jupiter at a Māndi-derived navāṃśa *and* Saturn at the dvādaśāṃśa → death) `[D]` | admit as [P]; the seed's "same Moon-house" definition is replaced |
| P5 aṣṭakavarga | (a) transit favourable through signs with more benefic marks in the **transiting graha's own** AV, adverse with fewer — known zero is adverse, not unqualified (Mars: BPHS ch.70 vv.24–27); (b) SAV >30 favourable / 25–30 medium / <25 adverse; (c) fruit delivered in the **kakṣyā owned by the mark-donor**; (d) śodhya-piṇḍa × marks ÷ 27 → nakṣatra; Saturn/Jupiter over it (or trine) times the graha's affairs (self, father); (e) Sun-month selection where the rule says so | BPHS ch.66 vv.13–15 (`BPHS2:35666-35684`), ch.70 (`:40799-41558`), `:42332-42335` `[D]`; Phaladīpikā XXIII (PG301), XXIV (PG304, PG307) `[D]` | admit after N8 polarity normalisation; no universal numeric multiplier (§7 RQ-1) |
| P6 Moon channel | Moon over the path's objects/trines as the path specifies; tārā (nine-fold); tithi–nakṣatra; the Moon's own vedha; chandrāṣṭama; day quality for elections | muhūrta practice `[P]`; Muhūrta Cintāmaṇi present (274 chunks, pages to read) | admit on demand (M-3) — day rows come only from here |
| P7 eclipses & stations | eclipse on an object with source-defined sensitivity; stations within orb as a relation | Phaladīpikā XXVI.26–29 `[D]` (pages to read) | admit after read |
| P8 Jaimini | AK/DK/PK, UL/AL/A7, kārakāṃśa as objects; Chara daśā as licence; argala as obstruction; rāśi-dṛṣṭi convention declared | `bphs_jaimini` present (UL 30 chunks); UL/DK *transit* rule 0 by predicate | admit natal+Chara; transit `[P]` |
| P9 Tājaka annual | varṣa chart, varṣeśa, muntha, sahams as **annual** objects (Vivāha, Putra, Karma, Mṛtyu, Roga …), Mudda daśā inside the year | Tājaka Nīlakaṇṭhī: सहम 28 chunks, मुन्था 5, वर्षेश 4 `[D]` present; activation rule `[U]` | Tier 2, own identity per year |
| P10 retrograde passes | pass identity (1st/2nd/3rd), station, repeated opportunity — geometry and testimony | M-2 `[R]` | admit as testimony; no weight |
| P11 transit-to-transit | a transit's result modified by aspects from benefics/malefics, dignity and combustion of the transiting body | Phaladīpikā XXVI.30–32 (PG334) `[D]` | Tier 2 |
| P12 star-limb & sign-third | aṅga-gochara (planet's star counted from janma nakṣatra → body limb → result), saptaśalākā/sensitive stars, sign-third fruition | Phaladīpikā XXVI.25, 26–29, 35–40 (PG336–337 verified) `[D]` | Tier 2 |
| testimony only | Sade-Sati phase rows (12th/1st/2nd from the Moon; never on gain classes), Kaṇṭaka/Aṣṭama periods, mūrti (rule form unverified), koṭa, sarvatobhadra (until a school-tagged grid), navatārā on slow-planet star transits, nodal 5/9 `[P]`, node-dispositor delivery `[P]` | N-15, N-21, N-14 | never weights |

### 2.5 Factors inside an admitted window

Activity (angular M-1 kernel, per-agent orb evidence-gated) · graduated dṛṣṭi (¼/½/¾/full for ordinary aspects; **specials at full** — BPHS1:16496-16502) · graha-specific BAV marks in the transited sign and contributor kakṣyā · SAV band · vedha scoped to the primary transit with cancellation intervals · transit dignity/combustion · agent nature and maitrī as interpretive modifiers · promise strength **and** condition (an afflicted 7L promises marriage *with difficulty*, it does not deny it — Codex B) · three valence fields.

---

## 3. Missing and overkill — final

**Missing, now admitted (with source status):** relationship record (§2.3) · lords, occupants, dispositors, mārakas-of-house, running AD/PD lords as objects and agents · P1 daśā-lord rules `[D]` · P5 aṣṭakavarga in all four forms `[D]` · P4 double transit `[P]` · promise as strength+condition · three-field valence · Moon channel on demand · both residence frames · graduated dṛṣṭi with specials full · P8/P9/P11/P12 · eclipses/stations · day-quality layer for elections · varga positions as objects (primary precedent: Phaladīpikā XVII śl.12–16; JP navāṃśa-of-7L rule `[P]`) · daśā-lord reference frame.

**Overkill, removed or demoted:** twelve-system weighted vote (Vimśottarī spine; Chara for Jaimini; Aṣṭottarī only where both BPHS ch.46 conditions hold — both fail on this chart; Mudda inside the annual path; Yoginī/Kālacakra/Nārāyaṇa/Naisargika as testimony until adjudicated as independent paths) · fixed planet→grain laws · fast-body kakṣyā *enumeration* (contributor qualification stays available on demand) · generic ingress attached per target · sensitive checks as targets (fold into the graha's interpretation; keep mṛtyu-bhāga/puṣkara as malefic-transit sensitivities `[P]`; keep M-6 derived points) · static daśā-portfolio type · yoga-by-overlap · fast-body returns as weights (solar return = annual anchor only) · SBC stand-in in the gate · Moon vedha on decade windows · century-wide materialised day tier.

**Kept exactly as ruled:** D-1, N-4, M-1 (implemented *angularly*), N-7, M-8, N-14, N-15 (with phase-split testimony), N-17 (producer filter removed), N-22 (with RQ-1), M-2.

---

## 4. The worked events — corrected

Positions L0 Lahiri (E8); natal from L1. Lords for Aries: 1L Mars · 2L/7L Venus · 3L/6L Mercury · 4L Moon · 5L Sun · 8L Mars · 9L/12L Jupiter · 10L/11L Saturn.

**Marriage 2013-12-11 — Mercury MD / Ketu AD.** P3+P4: Saturn returning to its exalted natal degree **as the 7th-house
occupant** (1°49′); Jupiter's 5th aspect from Gemini on Libra, 2°08′ from natal Saturn and 0°19′ from transit Saturn;
Ketu 0°33′ from the lagna degree, Rahu in the 7th. P1: MD lord Mercury's dispositor is Saturn in the 7th; AD lord Ketu's
sign-lord is Mars, the lagna lord in the 7th — relationship licences `[P]`. The target lesson: the marriage signature
lacks **occupants**; resolving 7L alone would not recover this. The wedding-day Moon (Pisces, 12th from the lagna, 2nd
from the Moon) is not analysed here — the LEL does not establish an election, and an election is itself analysable.

**Twin daughters 2022-01-03 — Mercury MD / Rahu AD.** P3+P4 (lagna frame): Jupiter in Aquarius (11th) casting its 7th
aspect on Leo, the 5th; Saturn 3°57′ from natal Sun, the 5th lord — house-plus-lord double transit `[P]`. Moon frame:
Jupiter is in the **1st** from the Aquarius Moon (v2.0 wrongly said 5th) — a house Phaladīpikā's table does not favour —
so the Moon-frame phala did not license this gain; the lagna frame did. The 5th from the Moon is Gemini, ruled by
**Mercury, the MD lord** (Codex). P1: AD lord Rahu's dispositor Venus (2L) sits in the 9th — the 5th-from-5th — with the
putra-kāraka `[P]`. Moon at the quoted instant: Sādhana tārā (6th) `[P]`; not a whole-day claim. Twins are not inferred
from "Rahu multiplies" (LEL annotation, not doctrine).

**Father's passing 2018-11-28 — Mercury MD / Moon AD.** P3 with the father frame (9th house Sagittarius): Saturn
3°39′ from natal Jupiter, the 9th lord, in the 9th; Sun, Jupiter and retrograde Mercury in the native's 8th. Father-frame
relationships: 7th from the 9th = Gemini (**Mercury, MD lord**), 8th from the 9th = Cancer (**Moon, AD lord**), 2nd from
the 9th = Capricorn (Saturn, the transiting agent) `[P]` — both reviewers converge on this reading. **Not** a double
transit (Jupiter in Scorpio aspects Pisces, Taurus, Cancer — not Sagittarius); v2.0's claim withdrawn. Saturn is the
**11th from the natal Moon** — favourable in the Moon frame — a clean demonstration that the native's Moon-frame phala
does not carry a relative's event; the bhāvāt-bhāvam frame does. The BPHS Sun-AV father procedure (9th from the natal
Sun = Virgo; piṇḍa; Saturn star) is the textually precise investigation to run `[D][U operands]`.

**What the three show, stated honestly:** the events ran on **lords, occupants, relationships and period-lord
connectivity** — none of which the '4.0' score represents — and on **frame choice** (lagna/relative frames for events,
Moon frame for the native's fortune). They are development cases, not held-out evidence (Codex G-10).

---

## 5. Elevation plan (sealed)

**Tier 0 — repair physical geometry, coverage and conformance before interpreting another score.**
T0-1 aspect direction (`body = target − angle`) with Saturn and Mars regression cases · T0-2 0° seam root; remove the
fabricated-ingress fallback (N2); search both boundaries for retrograde entry · T0-3 retain residence spans and
truncated contacts (N3) as intervals with coverage · T0-4 frame on **rule selection and resolution** (two errors, #10);
`frame` on every record · T0-5 resolve lords, occupants, yoga constituents (#8) · T0-6 per-instant nested MD/AD/PD
permission with applicability; N-15 enforced on the projection path (#2–#4) · T0-7 three-field valence; class-relative
rule polarity (#11, #12) · T0-8 vedha as scoped interval relations with cancellation sub-intervals, exceptions,
independence; grade keys fixed; battle-scale suppression stamped `uncited_extension`; no attenuation without an
obstruction (#16, #17, N4) · T0-9 angular M-1 (N1); 90-day filter to serve time (N5); `birth_anchor` excluded (N6);
mūrti auto-flag removed (N7); `precision_regime` semantics preserved, `solver_method` + uncertainty added · T0-10 tārā
key, L1 kakṣyā key (#5, #19) · T0-11 bindu/rekhā polarity declared on the L1 categories (N8) · T0-12 rebuild the
resonance map on R-1..R-6 (#9) · **T0-13 measurement first**: regenerate LEL chart-state annotations from L0/L1 (N9);
pre-declare evaluation rules, negative/control intervals and held-out events *before* Tier 1.

**Tier 1 — the rule paths.** P1 (daśā-lord rules; AD/PD lords as objects/agents; dispositor and association edges) ·
P3 (both residence frames; relative frames) · P4 (double transit, redefined) · P5a–d (AV forms after N8) · graduated
dṛṣṭi with specials full · promise as strength+condition from L1 (bhāva-bala, ṣaḍbala, dignity, relevant varga, cited
yoga→event map) · agent nature/maitrī as interpretive modifiers · P6 Moon channel on demand inside admitted windows.

**Tier 2.** P9 Tājaka annual path · P8 Jaimini path · P11 transit-to-transit · P12 star-limb/sign-third/saptaśalākā ·
P7 eclipses/stations · varga positions as objects · SBC with a school-tagged grid (testimony) · navatārā and day-quality
extensions.

**Tier 3 — validation (protocol pre-declared in Tier 0).** Retrodiction on the reconciled LEL by **rank within class and
year**, base rate, timing error, false-positive burden, per-mechanism attribution; the three §4 events excluded as
development cases; cross-class window-set correlation as a diagnostic; per-path ablations on the real chart; cold/warm
benchmarks with root counts, Swiss calls, unresolved spans, coverage, peak preservation. Calibration stays at L5.

**Ranking of expected gain** — two judgments recorded, not measured: Codex — frames/aspects/coverage → relationships and
period relevance → vedha timing → valence → AV → double transit/graduation → day timing → Jaimini/Tājaka. Kimi — M2
(lords, AD/PD) > M1 (double transit) > M7 (residences) > M5 (nature/valence) > M3 (BAV) > M6 (Moon) > M4 (promise) > M8.
Both put Tier 0 first and relationships second.

---

## 6. Implementation contract — same astrology, lower cost, measured not promised

1. **Sky-event substrate**, computed once per (ephemeris/convention generation, ayanāṃśa, node convention, body, grid):
   sign, nakṣatra and kakṣyā crossings, stations, eclipse instants. Sun: 12 / 27 / 96 crossings per year; Saturn ≈ 0.4 /
   1.1 / 3.2 plus retrograde re-crossings. **Moon boundary events are generated on demand** (≈ 4×10⁵ per 250 y if
   materialised — Codex E5). Relative-body geometry (aspects between transiting bodies, combustion, tithi) is a separate
   substrate; location-dependent election predicates are not part of the natal-contact table.
2. **Solve physical geometry once per (body, physical point or span, relation, aspect)**; attach relationship-record edges
   (class, affected person, role, frame, weight) in a join table. Role edges are not independent observations.
   Interval objects stay intervals; cusps are never converted to points. Annual objects (sahams) carry per-year identity.
3. **Per-path coarse-to-fine pruning**: evaluate each admitted path's cheapest necessary predicate first and discard an
   interval only where it is demonstrably false. Fast-body solves therefore run only where some path still admits.
4. **Lazy refinement with certified bounds**: bracket from the arc index; refine to Swiss whenever the approximation's
   uncertainty could change membership, ordering, boundary identity or a reported peak; store `solver_method` and
   angular/time uncertainty (δt ≈ δλ/|λ̇|, unstable near stations — refine there). `precision_regime` keeps its ruled
   meaning.
5. **Interval sweep** for categorical prerequisites (O(B log B + output)); factor segments with explicit functional forms;
   **interior-extremum and threshold-root solving** for retained scores (products of linear factors are quadratic; no
   endpoint-only evaluation); adaptive refinement where no closed form exists.
6. **Day tier on demand** with its own coverage record; prefetch for ranked windows is a policy, never an exclusion;
   uncomputed ≠ empty.
7. **What is re-solve vs re-score**: weight, frame-*interpretation*, valence and path changes re-score; aspect direction,
   new aspect levels, frame-dependent *resolution*, target-generation and support-domain changes re-solve. Lineage
   propagates to Kṣetra, Saṅgam and downstream (Codex E6).
8. **Cost is a contract to measure, not a figure to quote**: the '4.0' build enumerated 1.35 M episodes per decade and
   refined all of them; the contract above removes duplicated solves and inert rows by construction. Benchmarks report
   cold/warm wall time, physical root count, Swiss calls, unresolved spans, coverage and peak preservation, and correctness
   against independently evaluated rule cases — never against the old pipeline's output. v2.0's minute-scale estimates are
   withdrawn as claims and retained as `[I]` hypotheses for the first benchmark.

---

## 7. Ruling requests carried to the native (nothing here changes a ruling)

| id | request | basis |
|---|---|---|
| RQ-1 | **M-7 / N-22:** distinguish *observed zero* favourable marks (doctrinally adverse — BPHS ch.70 vv.24–27) from *unresolved* operand (→ `unqualified`); normalise bindu/rekhā polarity first; keep the M-7 bands as a WP8 hypothesis | Codex D5, G; Kimi D5 |
| RQ-2 | **M-1:** implement the ruled angular kernel now (step06b is non-conformant); authorise a separately versioned calibration study of BPHS ch.26's graduated profile | Codex C2, G; Kimi §3.3 |
| RQ-3 | **M-3 / G-9:** the served Phaladīpikā carries Moon-relative node results (XXVI.2, XXVI.24) — recount PG321/PG331; no nodal aspect is thereby authorised (N-14 stands) | Codex G |
| RQ-4 | **Mūrti:** rule form and source — 0 chunks by predicate; A-1's true-ingress requirement stands; the nakṣatra-mod-4 table and its auto `verse_cited` stamp are not covered by A-1 | Codex D3, G; Kimi D3 |
| RQ-5 | **N-15:** testimony rows phase-split (12th/1st/2nd from the Moon), never attached to gain classes — the twins were born in phase 1 | Kimi G |
| RQ-6 | **N-17:** revisit only after Tier 0; meanwhile move the producer's 90-day filter to serve time as ruled | Kimi G; Codex C5 |
| RQ-7 | **Aṣṭottarī:** both BPHS ch.46 conditions fail on the canonical chart (Rahu 8th from the lagna lord; day birth in Śukla pakṣa) — its vote must be *absent*; confirm the pakṣa operand | Kimi C; Codex D3 |
| RQ-8 | **Corpus notes:** record the KP Reader vs Phaladīpikā Venus-vedha ordering discrepancy in `bg_transit_rules.rule_notes`; strike the "§double-gochara" citation string in favour of `[P]` + PG216 precedent | Codex D3; §8 |

---

## 8. Corpus register — what was counted, what remains `[U]`

**Counted 2026-09-29 against `classical_text_chunks` (15 texts, 10,651 chunks):**
Venus vedha pairs — PG323:C1 śl.8 (12→6, 11→3) · Moon-lagna primacy and per-planet table — PG321–323 · adverse
12/8/1 residence — PG335 śl.11 · daśā/bhukti lord transit rules — PG249–250 (Adh. XX śl.34–38) · kakṣyā by donor —
PG301 (Adh. XXIII) · piṇḍa nakṣatra, self and father — PG304, PG307 (Adh. XXIV) · joint Jupiter/Saturn varga rule —
PG216 (Adh. XVII śl.12) · transit-to-transit modification — PG334 (śl.30) · aṅga-gochara tables — PG336–337 · lagna-frame
transit results — Yavana Jātaka ch.45–48 · BPHS ch.26 graduation and specials — BPHS1:16496-16502 · Aṣṭottarī conditions
— BPHS2:3256-3262, 3593-3596 · SAV bands and BAV direction — BPHS2:42332-42335, 41956-41959 · Tājaka सहम 28 / मुन्था 5 /
वर्षेश 4 chunks · upapada 30 chunks, none with transit · kakṣyā 14 chunks (Sārāvalī, UK, Jaimini, nāḍī) · **zero** by
predicate: mūrti-nirṇaya rule; node-dispositor result-delivery; chandrāṣṭama-as-avoidance; UL/DK transit rule; JP
navāṃśa-of-7L marriage rule; a generic "double gochara" passage (11 co-mention chunks read; only PG216 is a joint rule).

**Still `[U]` — predicate or read named:** Phaladīpikā XXVI.25–29 (sign-third, saptaśalākā, Abhijit scheme) — read
PG331–334 · Muhūrta Cintāmaṇi tārā/chandrāṣṭama pages · Tājaka saham *activation* rule — read PG86–107, PG144–167 ·
BPHS ch.70 Sun-AV father operands for this chart · Kimi's KP-transcription discrepancy (secondary) · Saṅgam/Kṣetra
consumers of the relationship record (lineage).

---

## 9. Seal record and limits

**The native's instruction (2026-09-29), verbatim:** *"Overall plan reviewed by GPT6 Astra Max Effort and kimi k3 max
effort both of them give them full context all meaningful information all proposals concerns and your questions, let
them review it thoroughly and come back to you, which you finally incorporate and seal the plan."*

Both reviews were run with the full packet (REVIEW_PACKET_GOCHARA_ASTRO_v1_0.md), read-only, against the worktree at
HEAD 507a759bf; their outputs are retained unedited; every finding is dispositioned in RECONCILIATION_GOCHARA_ASTRO_v1_0.md.
This document incorporates every accepted amendment and carries every unresolved item to §7 or §8. Sealed by the
author under that delegation.

**Limits.** No new build, migration or publication is authorised by this seal; the standing order and every native
ruling stand. Cost figures are hypotheses (§6.8). The three worked events are development cases. Chart 2's ledger was
used only as a structural proxy for the deleted chart-1 candidate. Doctrine labelled `[P]` enters only as
`uncited_extension` with a ruling; nothing labelled `[U]` enters the score.
