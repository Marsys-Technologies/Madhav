---
artifact: RECONCILIATION_GOCHARA_ASTRO
canonical_id: RECONCILIATION_GOCHARA_ASTRO
version: "1.0"
status: COMPLETE
date: 2026-09-29
reconciles: "ASTRA_REVIEW_GOCHARA_ASTRO_v1_0.md (Codex gpt-6-astra, reasoning max, verdict REWORK) and KIMI_K3_REVIEW_GOCHARA_ASTRO_v1_0.md (Kimi K3, effort max, verdict PROCEED_WITH_AMENDMENTS) — both of FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md (sha256 270184f7…)"
method: "Every finding either reviewer raised was re-verified by the author at source (file:line), in production (read-only; predicates in FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md), or by count(*) against the served classical_text_chunks (F-32). Where the two reviewers disagree, the served corpus or the code decides, never the reviewer. Dispositions: ACCEPTED · ACCEPTED-AMENDED (accepted with a stated narrowing) · REFUTED (with the evidence) · DEFERRED [U] (needs a count or ruling the author cannot supply)"
outcome: "All accepted items are incorporated in FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (SEALED). Nothing accepted here was left out of v3.0; nothing in v3.0 rests on a refuted item."
---

# Reconciliation — two independent reviews of the Gochara astrological review v2.0

## 0. Verdict reconciliation

Codex: **REWORK** — "valuable as a defect inventory and architectural proposal; not to be sealed as doctrine
until the universal cascade, source attributions, worked-example errors, ruling conflicts and new defects are
corrected." Kimi: **PROCEED_WITH_AMENDMENTS** — "the hierarchy is the right doctrine; 19/27 confirmed, 0 refuted;
must not be sealed as-is (one doctrinal error, two numeric errors, one half-flagged attribution, three omissions)."

Both are right about the same document. The disagreement is about *what is being sealed*. v3.0 therefore seals a
**plan** — the verified defect inventory, the corrected doctrine model, the implementation contract and the
validation protocol — and explicitly does **not** seal any claim of predictive accuracy, which both reviewers
say must be earned by measurement (Codex G-10, Kimi T3). Every REWORK item Codex names is either corrected in
v3.0 or carried as an open ruling request; nothing is sealed "through ambiguous wording" (Codex G, last para).

## 1. Where the two reviewers disagreed — and what decided it

| Question | Kimi | Codex | Decided by | Resolution in v3.0 |
|---|---|---|---|---|
| Venus vedha pairs (seed 11→3, 12→6) | wrong; standard is 11→6, 12→3 (KP Reader vol5:1330-1337) | correct as coded | **Served Phaladīpikā PG323:C1 śl.8** (queried 2026-09-29): houses listed "…8th, 9th, **12th and 11th**", vedha "…5th, 11th, **6th and 3rd** respectively" → 12→6, 11→3 | **Seed stands.** KP transcription pairs them differently — recorded as a secondary-source discrepancy `[U]` for the corpus owner; primary text governs (F-32) |
| Double transit citation | "no such passage; 20th-century practice" | same, plus K.N. Rao primary evidence of modern codification; seed's same-house definition differs from the practice rule | Corpus count: 11 Phaladīpikā chunks co-mention Jupiter+Saturn+transit; the only *joint* rule is **Adh. XVII śl.12 (PG216)** — Jupiter at a Māndi-derived navāṃśa *and* Saturn at the dvādaśāṃśa → death | Double transit = **[P] modern practice**, `uncited_extension`; PG216 cited as the sole primary joint-transit precedent (death timing, varga-specific); method definition rewritten (house-or-lord, occupation-or-aspect) |
| Combination law | interval-set intersection for admissibility + multiplicative ranking inside; add an "unlicensed-but-strong" escape channel | union of complete source-qualified rule paths, each intersecting its own prerequisites; no fixed planet→grain | Both, unified | **Admissibility = ⋃ over admitted rule paths of ⋂ of that path's prerequisites** (Codex); ranking score only inside admitted windows (Kimi); Kimi's escape channel is simply a rule path whose prerequisites omit daśā. Hierarchy kept as order of inquiry and computation strategy, not as law |
| Sade-Sati / Kaṇṭaka / Aṣṭama as adverse-class L1 licences | agree, as testimony, phase-split, never on gain classes | reject as a blanket licence (reinstates the N-15 gate under another name) | N-15 + served corpus | **Withdrawn as licence.** Replaced by (i) the verse-cited rule path PG335:C1 śl.11 (Saturn/Sun/Mars/Jupiter in 12/8/1 from the Moon → danger to life, fall, loss) for adverse classes, and (ii) N-15 testimony rows, phase-split, never attached to gain classes (Kimi) |
| Mars placement | L2 for adverse + Mars-signified classes; L3 otherwise | rule-path dependent; BPHS ch.70 vv.24–27 Mars gains | BPHS2:41248-41259 (verified) | No planet→grain law; Mars's temporal role is declared per rule path; Kimi's default (adverse + Mars-signified at month grain) kept as the *authoring default* |
| Sun/Mercury/Venus "L3 only" | agree with demotion | reject: BPHS ch.70 vv.19–20 uses the Sun's sign to select a month | BPHS2:41041-41049 (Codex cite; consistent with the AV election rule) | Demotion withdrawn as law; fast bodies default to trigger role for *point* contacts, and any rule path may assign them otherwise |
| Worked event 3 (father) | reading right; add mārakas of the 9th | not a double transit (Jupiter in Scorpio does not aspect Sagittarius); Saturn is 11th from the Moon | Arithmetic (verified) | v2.0's "all three events were L1 residence + L2 double transit" **withdrawn**; father = Saturn over the 9L in the 9th + 8th-house cluster + MD/AD lords = 7th-from-9th and 8th-from-9th lords (both reviewers converge on the same relationship reading) |
| Mūrti wiring | wait for rule-form count; nakṣatra-at-ingress form "most likely right" | reject multiplicative Q pending adjudication; code's `verse_cited` flag is automatic | Corpus count: **0 mūrti-nirṇaya chunks by predicate** (2 hits are a Varāha-mūrti charity and an art-history note) | Mūrti stays `uncited_extension`; not wired; its `verse_cited`/`corpus_verifiable` auto-flag is a §N.8 defect (Tier 0); adjudication requested of the native |
| Cost model | plausible order of magnitude | several figures wrong (27 not 33 Sun crossings; Moon events ~4×10⁵/250y; products not piecewise-linear; OR pricing inconsistent) | Arithmetic | Corrected; cost section rewritten as a **measurable contract** (Codex G-9), estimates re-labelled `[I]` |

## 2. Dispositions — Kimi K3

**A (27 findings).** 19 CONFIRMED / 5 PARTLY / 3 UNVERIFIABLE_HERE / 0 REFUTED — accepted. The `[L]` figures Kimi could not
see are now published with predicates (FABLE_REVIEW_EVIDENCE_APPENDIX E1–E9). #24 corrected to **27 of 41** childbirth
era rows at 0.627200 (v2.0's "13" was a 2020–22 subset). #13 strengthened as Kimi says: the corruption is exactly the
malefic special aspects.

**B.** Cascade AGREED; frame split → superseded by the rule-path model (both frames are cited: Phaladīpikā XXVI.1 makes
the Moon primary for gochara-phala; Yavana Jātaka ch.45–48 gives lagna-frame results); Mars amended as above; node
dispositor rule ACCEPTED as [P] (0 by predicate in BPHS); algebra amended as above; L3 extensions (navatārā nine-fold,
chandrāṣṭama, vāra/karaṇa/nitya-yoga, pakṣa-bala, avoidance blocks, navatārā on slow-planet star transits) ACCEPTED as
rule-path candidates on demand [P] (chandrāṣṭama-as-avoidance: 0 by predicate → [P]).

**C.** M1–M13 all ACCEPTED with the amendments recorded; M8 specials-at-full ACCEPTED (BPHS1:16496-16502 verified). O1
ACCEPTED-AMENDED (Codex: a conditional daśā is a path, not "testimony forever"); Aṣṭottarī inadmissible on this chart
ACCEPTED (BPHS2:3256-3266 verified; Rahu in Taurus is the 8th from Mars in Libra). O5 AMENDED (keep mṛtyu-bhāga /
puṣkara as sensitive degrees for malefic transits [P]); O9 AMENDED (SBC held as Tier-2 testimony with a school-tagged
grid). Four higher-leverage omissions ACCEPTED: node-dispositor delivery [P]; mārakas of the signature house [P]; varga
gochara triggers (primary precedent: Phaladīpikā XVII śl.12–16 Jupiter-at-navāṃśa death timing [D]; JP navāṃśa-of-7L
marriage rule 0 by predicate → [P]); daśā-lord reference frame — **upgraded to [D]**: Phaladīpikā XX śl.34–38 (PG249–250)
gives the daśā/bhukti lord's own transit dignity and Sun/Jupiter over the bhukti lord's exaltation sign as the delivery
trigger. §3.3 re-openings (M-1 decay shape checkpoint; N-17 after Tier 0) carried to the ruling requests.

**D.** Q3 Venus REFUTED (above). Mūrti: Kimi's "most likely right" not adopted — 0 by predicate. Aṣṭottarī ACCEPTED.
Jaimini UL transit: 0 by predicate (30 upapada chunks, none with transit) → Chara-daśā licensing only, as scoped.
Tājaka: Kimi's predicate returned 0 because the served Nīlakaṇṭhī is in Devanagari; **सहम 28 chunks, मुन्था 5, वर्षेश 4**
→ definitions present [D]; activation rule still [U]. D5 BAV convention ACCEPTED-AMENDED per Codex D5 (polarity first;
no universal multiplier). D9 ranking ACCEPTED as one of two judgment rankings (Codex's differs — both recorded).

**G.** Twelve amendments: 1 ACCEPTED; 2 REFUTED; 3–12 ACCEPTED (10: battle-scope stamp verified at migration 528:101;
12: mūrti held). Three ruling requests carried.

## 3. Dispositions — Codex gpt-6-astra

**A (27 findings).** 15 CONFIRMED / 10 PARTLY / 2 UNVERIFIABLE_HERE / 0 REFUTED — accepted. Scope narrowings adopted
verbatim in v3.0: #3 "anywhere" → "in the Gochara loading path"; #6 ingress is legitimately an instant — the repair is
retained residence/state, not broadening; #7 the kernel computes `ResidenceSpan`s and enumeration discards them (a
lost-data repair); #8 the lord resolver exists and fails on missing facts; #11 negatives reach the afflicting channel
but never activity; #12 1,435 era rows of 4,415 total; #14 the residence helper can fabricate an Aries row; #18/#20/#21
narrowed; #19 a 672-row prastāra emission exists in the strength writer (so contributor data is partly built).

**Decisive checks** (aspect arithmetic; five read-only probes) ACCEPTED and re-run in spirit at source.

**B.** Decomposition AMENDED, universal combination law REJECTED — ACCEPTED (§1 above). Factor table: every AMEND
adopted; the three REJECTs (sahams at L0 — annual objects; Sade-Sati blanket licence; Mars/fast-body grain laws) ACCEPTED;
Mūrti-Q reject ACCEPTED; "era/month/day are output resolutions, not mechanisms" ACCEPTED. Three-field valence
(evidence for / evidence against / outcome valence) ACCEPTED. Precision caveats (birth-time and event-time uncertainty
bound the advertised precision) ACCEPTED into Tier 3.

**C.** M1–M13 and O1–O12 amendments ACCEPTED as written, with one narrowing: O3 — fast-body kakṣyā crossings are
removed from *enumeration* (duplicated, zero-span) but the contributor qualification is kept available on demand per
Codex. Six higher-leverage omissions ACCEPTED: (1) the event-specific **relationship record** replaces the flat target
list — adopted as v3.0's central object; (2) step06b's M-1 is linear in **time**, not angular separation — **verified**
(`linear_no_box_decay` interpolates t_in→t_exact→t_out) — Tier 0; (3) residence fallback fabricates `exact_crossing=True`
ingress at horizon start — **verified** (episodes.py:486-508: `t_exact=ingress.exact_jd if ingress else ca`,
`exact_crossing=True` unconditionally) — Tier 0; episodes with `t_exact=None` are dropped — **verified**
(step06:614-619 `continue`) — Tier 0; (4) vedha writer discards obstruction temporal structure — ACCEPTED, Tier 0
(interval relation); battle-scope suppression — ACCEPTED; (5) 90-day producer filter contradicts N-17 — **verified**
(step06b:417-424 `MIN_PEAK_SEPARATION_DAYS` retained) — Tier 0; `birth_anchor` kill-switch is prose only — **verified**
(writer.py:288-296 comment; 43/43/43 windows in the report) — Tier 0; (6) mūrti `verse_cited` auto-flag — **verified**
(logic.py:81-86 `return "verse_cited" if moorti_computed`) — Tier 0 (§N.8). Four additional Phaladīpikā XXVI
mechanisms ACCEPTED as Tier-2 candidates, **now verified in the served corpus**: śl.30 transit-to-transit modification
(PG334:C1), aṅga-gochara star-limb tables (PG336–337:C1), sign-third fruition and saptaśalākā (in Adh. XXVI, pages to
be read) [D].

**D.** D1 ACCEPTED. D2 ACCEPTED (three corrections + the fallback repair). D3: mūrti — ACCEPTED, corpus count now run
(0); Venus — ACCEPTED (served text); double transit — ACCEPTED (+ PG216 precedent); Aṣṭottarī — ACCEPTED, day/night and
pakṣa operands remain [U] for this birth (10:43 IST daytime; pakṣa Śukla per the FORENSIC tithi Śukla Tṛtīyā → day birth in
Śukla pakṣa **fails** v.23's recommendation too — both conditions fail on this chart); Jaimini — ACCEPTED (0 by
predicate); Tājaka — ACCEPTED-AMENDED (definitions present in Devanagari; activation [U]). Codex's required predicates:
all run except the Abhijit/saptaśalākā read (Tier 2). D4 ACCEPTED. D5 ACCEPTED in full — including the **bindu/rekhā
polarity** point: L1's `ashtakavarga_bindu*` categories store PyJHora's benefic "dots" while the Santhanam edition names
the benefic mark *rekhā* and the malefic *bindu*; polarity must be declared on the category before any citation-bearing
weight (Tier 0 data-contract item). Known-zero ≠ unqualified: ACCEPTED as a ruling clarification request (M-7/N-22).
D6 ACCEPTED (on demand; prefetch as policy; uncomputed ≠ empty). D7 ACCEPTED (all signature corrections; "5L-of-5L"
disambiguated to the 9th house and its lord). D8 ACCEPTED — pruning per rule path only where a necessary predicate is
demonstrably false. D9 ACCEPTED as the second judgment ranking; "measurement preparation ahead of implementation"
ACCEPTED — Tier 3's protocol becomes a Tier-0 prerequisite (LEL reconciliation, pre-declared rules, held-out events).

**E.** E1–E6 ACCEPTED: sky-event substrate versioned by convention; geometry/rules/windows as three objects; role edges
not independent observations; lazy refinement with certified bounds and a **separate solver-method field** (the
ratified `precision_regime` keeps its `instant_grain|date_grain` meaning — v2.0's `spline|swiss` overload withdrawn);
interval sweep with interior-extremum solving (products of linear factors are not linear); cost table corrected (Sun 27
nakṣatra crossings/yr; Moon boundary events ≈ 4×10⁵ per 250 y if materialised — on demand instead; OR-model pricing
withdrawn; "projection-only" claim narrowed to weight/frame/valence changes; geometry changes require re-solve).

**F.** F1 ACCEPTED (Saturn as 7th-house *occupant* is the target lesson; "muhūrta" claim not established by the LEL —
withdrawn; Moon in Pisces is 2nd from the natal Moon; the 2013 "what '4.0' sees" is a grammar deduction — relabelled).
F2 ACCEPTED (1st from Moon; 5th from Moon = Gemini/Mercury = MD lord; tārā Sādhana at the quoted instant; LEL
annotations inconsistent — **verified**: LEL says Rahu "in Aries", Moon "in Pisces", natal Ketu "in Leo" against L0/L1
Taurus, Sagittarius, Scorpio). F3 ACCEPTED (no double transit; father-reference relationships; Saturn 11th from Moon;
LEL "Jan 2020 ~2 months after" is 14 months — **verified**).

**G.** Ten amendments ACCEPTED (5 includes Venus staying as coded). Four ruling requests carried; "no reopening" list
respected — v3.0 complies with N-14, N-15, M-2, N-17, M-8, D-1, N-4, N-7.

## 4. Author's own errors, recorded

1. Twins: "5th from the natal Moon" — wrong (1st). A rule number attached to a miscounted house — the very defect
   class the review condemns. Fixed; the lesson is written into v3.0 §0.
2. "All three events were produced by L1 residence + L2 double transit" — wrong for the father. Fixed.
3. "13 peaks at 0.6272" — a subset presented as a whole. Fixed (27/41).
4. Sun "≈33 nakṣatra crossings/yr" — wrong (27). Fixed.
5. Hierarchy stated as a necessary-condition law — overstated. Re-stated as order of inquiry + computation strategy.
6. "Every doctrine change is a projection" — overstated. Narrowed.
7. `precision_regime = spline|swiss` — collided with the ratified field. Withdrawn; separate field.
8. Sade-Sati/Kaṇṭaka as licences — contradicted N-15's intent. Withdrawn.
9. Sahams at L0 — annual objects mis-placed. Moved to the annual path.

## 5. Open — needs the native or a read, not another review

| id | item | owner |
|---|---|---|
| RQ-1 | M-7/N-22: a **known-zero** favourable AV count is doctrinally meaningful (BPHS ch.70 Mars without rekhās → adverse), not "unqualified"; clarify the boundary between unresolved operand and observed zero; normalise bindu/rekhā polarity first | native |
| RQ-2 | M-1: implement the ruled *angular* kernel now (step06b's time triangle is non-conformant); authorise a separately versioned study of BPHS ch.26's graduated dṛṣṭi profile as a calibration checkpoint | native |
| RQ-3 | M-3/G-9: the served Phaladīpikā carries Moon-relative node results (XXVI.2, XXVI.24) — the earlier absence premise was too strong; recount PG321/PG331; no nodal aspect is thereby authorised | corpus owner |
| RQ-4 | Mūrti-nirṇaya: rule form and source — 0 chunks by predicate; A-1's true-ingress requirement stands; the nakṣatra-mod-4 table and its auto `verse_cited` stamp are not approved by A-1 | native |
| RQ-5 | N-15: testimony rows phase-split (12th/1st/2nd from the Moon), never attached to gain classes (twins born in phase 1) | native |
| RQ-6 | N-17: revisit only after Tier 0 (promise saturation and the 1e-9 floor caused the plateaus jointly); meanwhile the producer's 90-day filter must move to serve time as ruled | native |
| RQ-7 | KP Reader vs Phaladīpikā Venus vedha ordering — secondary-source discrepancy to be noted in `bg_transit_rules.rule_notes` | corpus owner |
| RQ-8 | Aṣṭottarī: both applicability conditions fail on the canonical chart — its vote must be absent, not down-weighted; confirm the pakṣa reading (Śukla Tṛtīyā, day birth) | native |
