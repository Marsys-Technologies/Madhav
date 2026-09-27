---
title: "KIMI_DECISION_PACKET_SANGAM_v1_0"
version: "1.0"
status: COMPLETED
role: review_request
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
description: "Author-written decision packet sent to Kimi K3 (max effort, Kimi CLI) for recommendations on the seven decisions."
frontmatter_added: "2026-09-23 — prepended for governance-gate parity (madhav-fc G18 finding: briefs tree is outside the frontmatter gate); body byte-identical to the prior commit"
---

# Decision packet — Saṅgam (ka_sangam) algorithm elevation: seven method rulings

You are Kimi K3, asked for **recommendations** on seven decisions that the native (Abhisek Mohanty,
the chart owner and ruling authority of this Jyotiṣa instrument) must make. You are not the
authority — you advise. Standard: **acharya-grade.** A senior Jyotiṣa ācārya reading your answer
should find it at or above their own level. Generic astrology is a failure.

## Ground rules
- Do NOT write any file. Print your answer only.
- For every recommendation: the option you recommend · why (classical basis with text/chapter where
  you can; engineering basis where relevant) · what it costs · what would falsify it · what you are
  NOT deciding. Mark each claim **[D]** doctrine (name the text), **[P]** practice, **[J]** your
  judgment, **[U]** you could not verify. Never present a number as fact — thresholds and weights
  are proposals for the native to ratify.
- The native's priority order: (1) quality of what the asset delivers, (2) build efficiency,
  (3) the surrounding ecosystem matters as much as the asset.
- Binding constraints you must respect: no invented computed values (B.10); L1 facts are the
  authority, never restated (§N.5); no scalar "confidence"/"salience" field may be invented; a
  reduced cap can never pass as equivalent coverage (Strategy P4); "another representation of the
  same origin adds no independent support" (L3-U02); a signal with no detector behind it is null,
  not green (§N.8).
- You may read the repository at the working directory for depth (plan:
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md`;
  reviews: `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md`, `…_v0_3.md`; code:
  `platform/python-sidecar/services/ka_sangam/engine.py`, `pipeline/orchestrator/writers/ka_sangam.py`;
  classical corpus: `00_ARCHITECTURE/SOURCE_DATA/classical_texts/`). Everything essential is below.

## What Saṅgam is
The L3 (Kāla) convergence engine. For each structural predicate about the chart it asks "when could
this fire?" and writes dated windows (`kala_convergence`) where a daśā period and a transit line up.
Seven downstream assets consume it. It has four modes: A (daśā soft prior → transit contact), B
(off-daśā sweep), C (sign-residence periods), D (Sarvāṣṭakavarga ≥28 sign-ingress).

## Verified facts about the current code (all checked at source; do not re-litigate)
1. **Target:** predicates carry no natal target longitude; the scan defaults to **0° Aries**.
2. **Contact model:** Western-style unsigned aspects `[0,60,90,120,180]` at 5° orb, searched at
   `target + angle` (so directed graha-dṛṣṭi — Mars 4th/8th, Saturn 3rd/10th — is mis-searched;
   Jupiter's mirror pair 5th/9th hides the error).
3. **Per-signature planet (June 2026-06-22 ruling §4.6, implemented):** DOSHA→Saturn, YOGA→Jupiter,
   DIGNITY→the signal's own graha, DISPOSITOR→house lord (may be Moon/Sun/Mercury), SUBSYSTEM→none;
   inline orb gate 0.45; no hardcoded fallback.
4. **June ruling §4.5 (native-ratified, NOT implemented):** "slow transits only (Saturn, Jupiter,
   Rāhu/Ketu); no ephemeris scan inside Saṅgam — evaluate rules against pre-computed slow-transit
   events; `planet` becomes a LIST of grahas that fired." The two halves of the June artifact point
   different ways; the code followed §4.6.
5. **Score kernel (I-16):** `score = Π(necessary) × (1 − Π(1 − wᵢsᵢ))`, necessary = dignity × orb ×
   vedha-factor (vedha is a 0.3 dampener, missing data → 1.0). **With dignity 0 the score is 0.0
   regardless of support** — an intensely active adverse configuration scores as nothing. The daśā
   prior is a *supporting* term, not necessary.
6. **Aṣṭakavarga:** the C7 "does the transit deliver?" current has never fired (vocabulary mismatch);
   L1 already stores per-planet BAV per sign (`ashtakavarga_bindu_sign`) plus kakṣyā boundaries; Mode D
   uses SAV≥28 only. Repo stores **benefic** counts; Santhanam's BPHS ch.66 calls adverse marks
   "bindus" and favourable "rekhās" — an edition-vocabulary hazard. Missing planet → twelve zeros,
   indistinguishable from measured zeros.
7. **Not read from L1:** daśā period boundaries at ISO precision (`start_iso/end_iso`); daśā-lord
   capability (a serving-layer aggregation exists); divisional charts (`chart_divisionals`).
   `sandhi_flag` in L1 means "period shorter than 20 days", not junction.
8. **Cross-clock agreement** groups intervals on the exact (start,end) pair — overlap with different
   endpoints never registers agreement.
9. **Retrograde:** three passes of one planet over one point are three windows or a dedup on date;
   never one episode.
10. **Rarity:** `period × angle/360` — reports a fixed target's opposition as recurring twice per
    period; not a base rate.
11. **Outputs today:** one score, one degenerate confidence label (2–6 witnesses → "speculative",
    1 witness → the only "high"), one domain, no route, no per-method silence, no coverage.
12. Both production charts are Aries lagna; Swiss Ephemeris here runs the Moshier fallback.

## Doctrine anchors already verified by an independent reviewer against the corpus
BPHS (Santhanam ed.): ch.26.2-5 graha-dṛṣṭi full/special/fractional; 26.6-8 degree-dependent
strength; ch.8.1-3 Jaimini rāśi-dṛṣṭi; ch.7.1-8 varga–domain (D7 progeny, D9 spouse, D10 position,
D4 fortunes); ch.47.2-4 daśā results by lord's nature/strength/placement, beginning/middle/end by
drekkāṇa and reversed under retrogression (defeats any universal "last-part strongest"); ch.27.21-25
motion states and ceṣṭā-bala; ch.66.13-15 aṣṭakavarga marks vocabulary; ch.72.3-5 SAV >30 / 25-30 / <25;
ch.46 Chara/Yoginī/Kālacakra; ch.74 Sudarśana; ch.31 argalā. Phaladīpikā ch.26 (gochara from Moon,
vedha; 26.2/26.12 Moon/Sun), ch.23 (aṣṭakavarga: 23.10-11 own-BAV, 23.16-19 kakṣyā, 23.20 SAV >28).
Hāyanaratna 2.1 (Tājika aspects incl. 60°/90° with own strengths/orbs), 3.3 (itthaśāla, motion/orbs).

## The seven decisions

### M-1 / M-1a — Contact-interval contracts; fate of the legacy scan; bhāva-madhya vs whole-sign
Proposal on the table: replace the single unsigned angle list with **four versioned method
contracts**, each with its own interval and intensity rule: (a) Moon-relative gochara + vedha;
(b) Parāśari graha-dṛṣṭi — full 7th, Mars 4/8, Jupiter 5/9, Saturn 3/10 full, plus the fractional
¼/½/¾ aspects — **directed** (aspecting graha at target − angle); (c) Jaimini rāśi-dṛṣṭi only on a
qualified Jaimini route; (d) Tājika aspects with their own orbs and itthaśāla motion rule. The same
geometry may carry a Parāśari (fractional) and a Tājika evaluation, separately labelled, one
evidential root. Sign applicability with degree annotation is a declared hybrid: the sign interval
survives when no exact degree pass occurs. The legacy scan is kept one generation as
`legacy_unsigned_angles`, never ranked with new rows.
**Questions:** Which contracts are in scope for this chart's instrument, and in what order? Should
the legacy scan be retired outright? For each rule class, is the target the whole sign, the natal
longitude, or bhāva-madhya (house cusp — which house system)? Are Rāhu/Ketu given dṛṣṭi (5th/9th per
some schools — unverified) and under which node convention (true vs mean)?

### M-2 — Aṣṭakavarga ledger
**Questions:** (i) Record the edition convention → stored-value mapping (repo stores benefic counts;
Santhanam names adverse marks "bindus"): which convention governs prose and code? (ii) Own-BAV
thresholds: is ≥4 support / ≤3 obstruct the rule you ratify, and what is BAV = 4 exactly? (iii) SAV
bands: BPHS 72.3-5 (>30 / 25–30 / <25) or Phaladīpikā 23.20 (>28)? — keep both school-labelled, or
choose? (iv) Should Mode D become "BAV-supported ingress" (planet-specific) rather than SAV-only?
(v) Kakṣyā: worth an L1 amendment to expose the contributor matrix now, or later?

### M-3 — The integrated June ruling (blocking)
§4.5 says slow-only, no scan inside Saṅgam, `planet` as a list. §4.6 says per-signature planet
(which admits fast planets for DIGNITY/DISPOSITOR), inline gate, no caps — and the code did §4.6.
Two proposals need this ruled: **E1** (new directed geometry) and **E3** (a fast tier — Moon/Sun/tāra
contacts computed *only inside an already-qualified slow window*, all families enumerated, no count
cap, evidence count unchanged).
**Questions:** Which governs — §4.5 or §4.6? If §4.5 is re-affirmed, the per-signature resolver is
replaced and `planet` becomes a list. If §4.6 supersedes, say so explicitly so the repo stops carrying
a READY prompt nobody intends to run. Is a scope-bounded inside-window fast tier within the ruling's
intent, or does it need an amendment? Classically: is "slow sets the season, Moon times the day" a
legitimate two-tier method for *natal event timing* (not just muhūrta), and which fast witnesses
(Moon contact; tāra from janma-nakṣatra; Sun ingress) are defensible?

### M-7 — Score-kernel separation (new, from the second review)
Because dignity 0 → score 0.0, the kernel erases adverse activity. Proposal: separate fields —
`activity` (geometric/clock intensity), `valence` (signed: dignity, nature, AV, route), `applicability`
(per method), `availability` (inputs present); dignity leaves the necessary product and becomes
valence; legacy rows labelled `kernel_version = legacy_i16`, never pooled.
**Questions:** Is there a *classical* reason dignity should gate rather than colour? (E.g., does a
debilitated lord's period produce *no* event, or an *adverse* event?) Is the four-field separation
the right shape, or is there a classical taxonomy of result (phala) vs intensity vs auspiciousness
that should be used instead? What is the legacy/new coexistence rule for consumers?

### M-4 — Typed natal/clock conditions (replaces rejected "gates")
Three signed conditions, none a veto, none a multiplier: `boundary_distance` per clock/level/parent/
lord from ISO period boundaries (annotation only — BPHS 47.3-4 defeats a universal last-portion rule);
`lord_condition` from strength/functional role/dignity/lordship (operative even when weak — BPHS
47.2-4); `varga_condition` — *natal* dignity of the relevant lords in the domain's varga.
**Questions:** The varga–domain table: D7 progeny, D9 spouse, D10 position, D4 property/fortunes —
confirm, extend (D2 wealth? D12 parents? D24 learning?), and which lords are "relevant" per domain?
Should *any* typed condition ever veto (default: none)? Is boundary-distance annotation worth
carrying at all absent a ratified sandhi doctrine, or drop it?

### M-5 — Episode conventions
Proposal: contacts of one (graha, target, directed angle, frame, method) linked by a station loop
form one episode with child contact intervals (each with orb entry/peak/exit), hull only as an
envelope, occupied time = union of children, no default peak phase.
**Questions:** Is the station loop the right linkage, or should nearness in time/longitude also
link? How are >3-contact and horizon-truncated episodes named? For the monthly-wave consumer
(`ka_taranga`, which averages one contribution per row per month), what is the right aggregation
unit — occupied duration, episode, or route?

### M-6 — Consumption and evaluation boundary
Once identity is stable and outcomes are recorded on two axes (observation: hit/miss/ambiguous/
censored/unobserved × derivation: valid/invalidated/superseded), may L5 (Mīmāṃsā) consume Saṅgam
windows as prediction candidates? Under what gate does `EMPIRICALLY_EVALUATED` open — held-out /
predeclared evaluation, minimum count, censoring rules?

## Deliverable
A markdown answer with one section per decision (M-1/M-1a, M-2, M-3, M-7, M-4, M-5, M-6) in that
order, each containing: **Recommendation** · **Classical basis** (cite) · **Engineering basis** ·
**Cost** · **Falsifier** · **Not decided here** · **Confidence** (with [D]/[P]/[J]/[U] tags). Close
with a short **cross-decision consistency check** (do your seven recommendations cohere?) and the
**three things you would ask the native before ruling**.
