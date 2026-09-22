---
artifact: SANGAM_ALGORITHM_ELEVATION_PLAN
canonical_id: SANGAM_ALGORITHM_ELEVATION_PLAN
version: "0.1"
status: PROPOSAL_FOR_INDEPENDENT_REVIEW   # → native ruling after Astra review
date: 2026-09-22
asset: ka_sangam (Saṅgam — the convergence engine, L3 Kāla)
companion: SANGAM_ELEVATION_BRIEF_v1_0.md v1.2 (the OUTPUT-CONTRACT elevation; this plan is the METHOD elevation)
base_branch: main (services/ka_sangam/engine.py, writers/ka_sangam.py verified byte-identical to origin/main 2026-09-22)
governed_by:
  - CLAUDE.md §B.10 (no fabricated computation), §N.5 (L1 authority), §N.7/§N.8 (earned signals)
  - MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §2 (L3-Q01–Q13), §3, §5 (P4), L3-U02/U07
  - CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md §4.5/§4.6 (native rulings 2026-06-22)
  - l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md (no confidence/salience scalar; F04/F06/F12 binding)
does_not_authorize: any code, migration, build, or doctrine. Method qualification is the native's.
evidence_tags: "[C] verified in code this session · [D] classical doctrine, source named · [P] established practice, textual anchor weaker · [J] author's judgment · [U] unverified"
---

# Saṅgam — algorithm elevation plan

**The question this plan answers.** From an astrological standpoint, where is the *credible*
opportunity to make Saṅgam's windows more accurate as predictions — not more numerous, not
better-served, but *righter*? The companion brief fixes what Saṅgam *says*; this plan proposes
changes to what it *computes*.

**The frame.** Accurate timing in Jyotiṣa is a funnel: daśā sets the season, slow gochara sets the
month, fast gochara and nakṣatra set the day, and a window becomes a *prediction* only when it is
checked against outcomes. Saṅgam today does the first two — partly in a non-Vedic way — and neither
of the last two. Six elevations follow, ranked by predictive leverage, each with its classical basis,
what the code does now, the proposal, its equivalence contract, its cost, its falsifying test, and
the decision it puts to the native.

**The native's priority order, applied throughout:** (1) quality of what the asset delivers,
(2) build efficiency, (3) the surrounding ecosystem matters as much as the asset.

---

## §1 — What Saṅgam computes today (the baseline, [C] throughout)

| Component | What it does | Where |
|---|---|---|
| **Mode A** | daśā-eligibility soft prior (`KaDashaKalaService.query(target_lords, max_level=3)`) → transit contact scan inside the horizon → I-16 score | `engine.py:1048-1300`; `:1113-1126`; `:1124` |
| **Mode B** | same contact scan, no daśā gate; flagged `is_off_dasha_discovery` | `:1332+` |
| **Mode C** | subsystem sign-residence periods (Sade-Sati-like) | `:1570-1671` |
| **Mode D** | SAV ≥ 28 sign-ingress windows for Jupiter/Saturn/Mars; predicate-agnostic | `:1668-1760`, `:1673`, `:1718` |
| **Contact model** | `find_aspect_events` from `pipeline/transit_search.py`: transiting planet vs `target_longitude_deg`, `aspect_degrees=[0, 60, 90, 120, 180]`, `orb_deg` default 5.0 | `:213`, `:467`, `:1087`, `:1148-1150` |
| **Transiting planet** | per signature (§4.6, landed): DOSHA→Saturn, YOGA→Jupiter, DIGNITY→own graha, DISPOSITOR_RELATIONAL→house lord, SUBSYSTEM→none | `:992-1015` |
| **Inline gate** | events below `HIGH_CONFIDENCE_ORB_THRESHOLD = 0.45` dropped as found | `:968`, `:1171`, `:1400` |
| **I-16 score** | `Π(necessary) × (1 − Π(1 − wᵢsᵢ))`; C11 vedha is a necessary term | `:696-729` |
| **Supporting currents** | C7 aṣṭakavarga potency · C8 eclipse · C9 transit-to-transit · C10 station · C12 tājika · C13 school consensus · pāñcāṅga · benefic dṛṣṭi · cross-daśā agreement · nakṣatra overlay · tāra bala | `:44-52`, `:1196-1240` |
| **C7 — dead** | has returned `None`/`0.0` on **4,729 of 4,729** rows: vocabulary mismatch + an unresolved HOUSE-vs-SIGN frame; both live charts are Aries lagna so the frames are indistinguishable | `:103-140` |
| **C13 — dead** | `school_consensus_by_domain` never populated pre-U4 | `ka_sangam.py:989` |
| **Daśā interval test** | closed-closed `start <= peak <= end` | `:1138` |
| **Daśā depth** | `max_level=3` (MD/AD/PD) | `:1124` |
| **Fast planets** | Moon/Sun appear only in the rarity period table and a luminary helper; never as a trigger | `:168`, `:949-950` |
| **Retrograde** | C10 marks a station in-window; three passes of one planet over one point are not linked | `:234` |
| **Independence** | hand-weighted coupling table → `independent_current_count` | `:850-889` |
| **Rarity** | `rarity_years ≈ period × aspect/360`, clamped — a formula, not a measured base rate | `:946-990` |
| **Not read from L1** [C, grep] | daśā *sandhi*; daśā-lord *capability*; any *divisional* chart | — |

**What is already right and must survive:** the I-16 multiplicative-veto form; continuous orb strength
(I-17); peak/shoulder (I-18); the inline gate; per-signature planet source; C11 vedha in the
house-from-Moon frame (CR-102); honest-empty stance (`:731-760`); SAVEPOINT discipline; fail-loud
birth context (CR-87).

---

## §2 — Constraints this plan inherits (not relitigated)

1. **June rulings (native 2026-06-22).** §4.6 per-signature planet + inline gate + no fallback:
   **landed** [C]. §4.5 Q1 (no ephemeris scan; evaluate rules over pre-computed slow-transit events)
   and Q2 (`planet` as a list): **not landed** [C]; the landed §4.6 forecloses Q2. *"Slow transits
   only"* was ratified with a stated reason (memory explosion + daśā/transit conflation). This plan
   honours the reason and names, in E3, the one place it proposes a bounded exception — as a
   decision, not a design-past.
2. **P4** (Strategy §5): *"Reuse geometric search results across compatible predicates/modes …
   Mode identity and full applicable predicate coverage. Savings fund broader coverage; reduced caps
   cannot pass as equivalent."* Every proposal below carries its equivalence contract.
3. **L3-U02:** *"another representation of the same origin adds no independent support."* Every new
   witness this plan adds must declare its lineage group; several *reduce* the count.
4. **§N.5 / B.10:** no L1 value restated; no number invented. Where a rule needs a value L1 does not
   hold, this plan marks `[EXTERNAL_COMPUTATION_REQUIRED]` or routes it to L1 as a bounded amendment.
5. **`transit_search.py` is untouchable** (shared with Kshetra, the Gochara family, frozen L0).
   Any new geometry lives in `services/ka_sangam/` or a new service; never an edit there.
6. **No confidence/salience scalar** (Product §5.2). Nothing here adds one; E6 replaces one.
7. **The output contract comes first.** The companion brief's typed testimony (independence groups,
   `method_states`, `route`, `coverage`, `comparability_class`) is the precondition for E1–E6 being
   *testable*. This plan assumes it.
8. **Method qualification is the native's** (acharya standard). Each E ends in a decision, not a rule.

---

## §3 — The six elevations

### E1 — Vedic contact model: graha dṛṣṭi and sign-from-Moon gochara, not Ptolemaic aspects

**What the code does** [C]. Mode A/B find "contacts" by longitude: the transiting planet forms
0/60/90/120/180° to a natal longitude within a 5° orb (`:213`, `:1148-1150`). Those five angles
with symmetric orbs are Western aspect theory.

**What the doctrine says** [D]. Vedic transit judgment has two textual bases, neither of which is
degree-symmetric:
- **Gochara by sign from the Moon** — the planet's *rāśi* counted from Chandra-lagna, with *vedha*
  (obstruction) points that cancel a favourable position. Sources: BPHS gochara adhyāya;
  Phaladeepika ch. 26 (the code already cites it at `:1671`); Bṛhat Saṃhitā. The C11 current
  already implements the vedha half in the correct frame — so half the engine already speaks this
  language.
- **Graha dṛṣṭi** — planet-specific, house-counted: every graha aspects the 7th from itself; Mars
  additionally the 4th and 8th; Jupiter the 5th and 9th; Saturn the 3rd and 10th; Rāhu/Ketu by
  some authorities the 5th/9th (BPHS dṛṣṭi adhyāya; Parāśara's full/three-quarter/half/quarter
  dṛṣṭi values). A Jupiter "square" (90°) has no classical standing; a Jupiter 5th-house dṛṣṭi does.

**The gap** [J]. The engine's *interval* (when is the contact on) is defined by a model that is not
the one L0's `bg_transit_rules` and the vedha table encode. The *peak* (orb-strength, I-17) is a
sound intensity measure and should survive.

**Proposal.** Split *interval* from *peak*:
- Interval = the transiting graha's **sign-based dṛṣṭi/occupation** of the target's sign, counted
  from the Moon for gochara rules and from the natal target for dṛṣṭi rules — i.e. an
  ingress-bounded window, which the Gochara service already produces for Mode C/D.
- Peak = the existing degree pass (I-17/I-18) *inside* that interval, using the graha's own dṛṣṭi
  angles (7th = 180°; Mars 4th/8th ≈ 90°/210°; Jupiter 5th/9th ≈ 120°/240°; Saturn 3rd/10th ≈
  60°/270°) rather than the generic five — with Parāśara's fractional dṛṣṭi strengths as the
  intensity scale where the angle is not a full dṛṣṭi.
- Each row declares `contact_model ∈ {vedic_drishti, gochara_from_moon, ptolemaic_legacy}` in its
  comparability class so the two are never ranked together during transition.

**Equivalence contract.** Not equivalence — a **declared semantic change** (Strategy §5: "the old
output is not the parity oracle where the method has a defect"). Reference oracle: a hand-worked
set of ≤20 windows on the canonical chart, each with the classical dṛṣṭi stated, ruled by the
native. Coverage must not shrink: every predicate that had a legacy contact gets a Vedic
evaluation; where none fires, `method_states.transit = applied` with the empty result recorded.

**Cost.** Sign-based intervals are *cheaper* than degree scans (ingress events, not per-day
longitudes); the peak pass runs only inside intervals. P4-positive.

**Falsifying test.** Jupiter transiting the 10th from a natal Moon in the 6th (a 5th-house dṛṣṭi
onto the 2nd — no such 120° in Ptolemaic terms would have fired). If the Vedic model fires it and
the legacy one does not, the models differ where doctrine says they must.

**Unlocks.** Windows a Jyotiṣī would recognise; removal of false positives from 60°/90° contacts
with no classical basis.

**Non-claim.** This plan does not rule *which* dṛṣṭi table (Parāśara vs Jaimini rāśi dṛṣṭi) — that
is **M-1**.

**Decision M-1.** Adopt Parāśari graha dṛṣṭi + gochara-from-Moon as the contact interval model, with
the degree pass retained for peak only? Keep the Ptolemaic scan as a *labelled legacy* class for one
generation, or retire it outright?

---

### E2 — Revive aṣṭakavarga, and use the right one

**What the code does** [C]. The C7 "does the transit deliver?" current has **never fired** — 4,729
of 4,729 rows at 0.0, first from a vocabulary mismatch (`JUP` vs `Jupiter`), then held on an
unresolved frame question: the stored L1 facts are keyed `<GRAHA>-HOUSE_<N>` while the lookup is
by `transit_sign`. The engineer returned an honest `None` rather than guess (`:117-140`) — correct
under §N.7 item 6. Mode D uses **SAV ≥ 28** (`:1673`) — the sum over all seven contributors.

**What the doctrine says** [D]. The primary aṣṭakavarga *transit* rule is **bhinnāṣṭakavarga**: the
transiting planet's *own* bindus in the sign it transits — ≥4 (of 8) supports, ≤3 obstructs; and
within a sign, the **kakṣyā** (eighth-part) whose contributor gave a bindu is where the result
concentrates. SAV is the secondary, sign-level aggregate. Sources: BPHS aṣṭakavarga adhyāyas
(the code cites "BPHS Ch.66 Gochara-Ashtakavarga" at `:1671`); Phaladeepika ch. 26.

**The gap** [J]. The one rule that classically answers "will *this* transit deliver *here*?" is
the dead one, and the live sub-mode uses the blunt aggregate.

**Proposal.**
1. **Adjudicate the frame** — one query against L1: for a non-Aries-lagna chart (or a synthetic
   one), do `<GRAHA>-HOUSE_<N>` bindus vary with lagna? If they do not, the label is a misnomer for
   rāśi and the lookup is right; if they do, L1 is storing house-frame bindus and the fact needs a
   bounded L1 amendment. Either way it is *L1's* frame to declare (§N.5), not Saṅgam's to guess.
2. **C7 := BAV of the transiting planet in the transited sign**, `bindus/8` as now, from the
   adjudicated frame. Requires the per-planet BAV facts, which `chart_facts` already carries
   (`ashtakavarga_bindu` per planet, `ka_sangam.py:991-1024`) [C].
3. **Kakṣyā** as an optional refinement of the peak: when the degree pass lands in a kakṣyā whose
   contributor gave a bindu, `peak_qualification = kakshya_supported`. Needs the kakṣyā-contributor
   table — L0 reference data; if absent, `[EXTERNAL_COMPUTATION_REQUIRED]` and route to L0.
4. **Mode D rebased**: keep SAV ≥ 28 as the *sign* filter, add BAV ≥ 4 for the scanning planet as
   the *planet* filter; a window passing both is a stronger and rarer claim, declared as such.

**Equivalence contract.** C7 has been arithmetically absent; adding it is a declared change with the
frame adjudication as its oracle. Mode D's row count *falls* (BAV gate is stricter) — reduced
*rows*, not reduced *coverage*: every ingress is still evaluated and recorded in `coverage`.

**Cost.** Negligible — table lookups on facts already fetched.

**Falsifying test.** A Saturn ingress into a sign with SAV 30 but Saturn's own BAV 2 must *not*
produce a supported window; SAV 26 with BAV 6 must. Today both are decided by SAV alone.

**Decision M-2.** Frame adjudication owner (L1) and the BAV thresholds (≥4 support / ≤3 obstruct
per Parāśara — confirm or amend).

---

### E3 — Day-level timing: the fast tier, bounded inside qualified windows

**What the code does** [C]. No fast planet is ever a trigger. The June ruling excluded them with
a reason: scanning the Moon over a century holds every weak crossing in RAM (the 11 h / 1.2 GB
explosion) and the MD-lord fix conflated the period lord with the trigger.

**What the doctrine says** [D/P]. Slow grahas set the season; **the Moon times the day** — its
transit over the sensitive point, its nakṣatra relative to janma-nakṣatra (**tāra bala**: the
3rd/5th/7th tārās adverse; Muhūrta Cintāmaṇi and the muhūrta literature generally), and
Sarvatobhadra-cakra vedha (Narapati-jaya-caryā). The Sun's ingress and its contact with the
natal point time monthly turns. This is standard practice for pinpointing an event already
indicated by daśā and slow gochara — never for *finding* the event.

**The gap** [J]. Saṅgam can say "2027"; it cannot say "the third week of March 2027." For
prediction that is the difference between a claim that can be checked and one that cannot.

**Proposal.** Apply the engine's own spine one level deeper — *generator → narrow → ephemeris
last* — so the fast tier runs **only inside an already-qualified slow window**:
- Input: a Mode A window `[window_start, window_end]` (typically days to months).
- Inside it: Moon contact to the same target (own dṛṣṭi model per E1), Moon's tāra from janma
  nakṣatra, Sun's contact/ingress. Output: `sub_peaks[]` — dated to the day — attached to the
  parent window, **not** new rows.
- Bound: at most `⌈window_days / 27.3⌉ + 1` Moon contacts per window per target; a 90-day window
  yields ≤5. No accumulation; the inline gate applies. This is arithmetically incapable of the
  explosion the ruling prevented.
- Lineage: the fast sub-peak is **coupled** to its parent slow witness (same origin, refined) —
  `independence_groups` gains no new member. U02-compliant by construction.

**Equivalence contract.** Additive: parent windows unchanged; `sub_peaks` may be empty (`applied`,
silent). No row count change.

**Cost.** ≤ a few dozen Moon positions per window; Sun ingress is a table lookup. Bounded and
declared.

**Falsifying test.** A 60-day Mode A window must yield ≤4 Moon sub-peaks, each at a date where
the Moon's longitude is within orb of the target under the E1 model — verifiable against any
ephemeris. A window with no Moon contact in its span reports `sub_peaks: []`, not a parent-date
default.

**Unlocks.** Windows the L5 calibration loop can actually score at day resolution; the ordinary
"when in this quarter" question (Product §9).

**Non-claim.** This does not reopen "scan fast planets over the horizon." It is bounded by the
parent window and cannot run without one.

**Decision M-3 (the June-ruling question).** Is a *bounded, inside-window* fast tier consistent
with the 2026-06-22 "slow transits only" ruling's intent — or does the ruling need an explicit
amendment to admit it? This plan asserts the former and asks the native to confirm or supersede.

---

### E4 — Three L1 facts Saṅgam has and never reads: sandhi, capability, varga

**What the code does** [C, grep]. No read of daśā *sandhi*, of daśā-lord *capability*, or of any
*divisional* chart. "Running" is the entire daśā test; the domain tag comes from MSR and is never
checked against the chart.

**What the doctrine says.**
- **Daśā sandhi** [P] — the junction of two periods is where results cluster and mix; the
  practice is near-universal, the textual anchor diffuse (Phaladeepika and later commentators
  treat the last portion of a daśā as the fructification zone). L1 already computes `sandhi_flag`
  on clock intervals [C, context §6]; Saṅgam's closed-closed test (`:1138`) discards it.
- **Daśā-lord capability** [D] — a period lord gives results according to its functional nature
  for the lagna, its dignity, its house, and the houses it owns (BPHS daśā-phala adhyāyas;
  Phaladeepika). L1 already serves this (`ganita_dasha_lord_capability_get` exists as a
  capability, so the computation exists upstream) [C]. Saṅgam treats an exalted yogakāraka and a
  debilitated māraka as equally "eligible."
- **Varga standing** [D] — a result fructifies in the domain whose divisional chart holds the
  lord well: D9 for marriage, D10 for career, D7 for children, D4 for property (BPHS varga
  adhyāya; the varga–bhāva correspondence is standard). L1 holds `chart_divisionals` [C].
  Saṅgam's `domain` is inherited from MSR and never confronted with the varga.

**Proposal.** Three **applicability gates** (F12 *gates applicability*), not new witnesses:
1. `sandhi_amplifier`: a window whose peak falls inside a sandhi zone of any constituent lord's
   period carries `route.sandhi = {lord, level, boundary}` and a declared multiplier on the
   necessary daśā term — value **native-ratified**, not invented here.
2. `dasha_lord_capability`: read from L1; a lord below a declared capability floor makes the daśā
   term *inapplicable* for that lord (F06 `inapplicable`, recorded), not merely low.
3. `varga_gate`: for the window's domain(s), the daśā lord's and transiting graha's dignity in the
   corresponding varga, from `chart_divisionals`; below floor → `method_states.varga =
   contradictory_unresolved` and the window is served with that state, never silently dropped.

**Equivalence contract.** Gates change which windows are *applicable*, not which are *found*;
every gated-out window is retained with its F06 state (Strategy §5: absence within scope must be
distinguishable). Row count unchanged; served ranking changes.

**Cost.** Three joins on facts already in L1. Zero new geometry.

**Falsifying test.** Two windows identical in transit geometry, differing only in that one lord
is exalted in D10 and one debilitated, must differ in `method_states.varga` and in served order
for a career-domain question — and must be identical for a health-domain question.

**Decisions M-4a/b/c.** Sandhi zone definition and multiplier; capability floor and its L1 source
column; the varga–domain correspondence table (which varga for which domain).

---

### E5 — Retrograde triple-pass as one trajectory

**What the code does** [C]. C10 marks a station in-window; each degree pass is scored on its own.
Three passes of Saturn over one point produce either three windows or one (dedup on `peak_date`),
and in the first case three witnesses.

**What the doctrine says** [P]. A slow graha's direct–retrograde–direct crossing of a point is one
event with a seed, a development, and a fruition — the retrograde pass often the most intense
(retrograde as *cheṣṭā-bala*, BPHS bala adhyāya) [D on the bala; P on the three-phase reading].
Strategy §3 already asks for "onset/peak/decay/recurrence" and §5 for "stations, retrograde
re-entries … must survive."

**Proposal.** When `find_aspect_events` returns ≥2 events for the same (planet, target, angle)
separated by a station, emit **one** window with `trajectory = [{phase: seed|retro|fruition,
date, orb_strength}]`, `window_start` = first pass, `window_end` = last, `peak_date` = the
strongest phase. Lineage: one group.

**Equivalence contract.** Row count falls where triples existed; coverage identical; the served
distinction *increases* (a three-phase event is more information than three dates).

**Falsifying test.** Saturn's 2027–28 triple crossing of any natal point on the canonical chart
must appear as one row with three dated phases, not three rows; `independence_groups` must count
it once.

**Decision M-5.** Which phase is the classical peak by default (retro pass vs final direct pass) —
or leave it to orb-strength, declared?

---

### E6 — Rarity as a measured base rate, and the outcome loop

**What the code does** [C]. `rarity_years` is `period × aspect/360`, clamped (`:946-990`) — a
recurrence *formula*. It answers "how often does this geometry recur," not "how often does this
*configuration* occur in this chart's life."

**Why this outranks every classical addition** [J]. Prediction is calibration. The instrument was
built for it (L5 Mīmāṃsā, the LEL, `mimamsa_outcome_record`). No dṛṣṭi table improves accuracy as
much as knowing that "Saturn 7th-dṛṣṭi on the Moon during Saturn AD" has hit 3 of 4 times on
this chart — or 0 of 4.

**Proposal.**
1. `rarity_years` → **measured**: count, over the chart's lifetime horizon, the windows of the
   same `(contact_model, planet, angle_class, comparability_class)` — "1-in-N-years" from the
   sweep the engine already runs, not from the period table. Keep the formula as
   `rarity_years_formula` for one generation, labelled.
2. **Falsifier per window** — the companion brief's `route` gives it: the necessary clauses. A
   window whose necessary clauses are later found false is *falsified*, not "unconfirmed."
3. **L5 hook** — each window carries a stable identity (natural key, not `convergence_id`) so an
   outcome recorded against it survives a rebuild (U10). This is the brief's §5.2; it is repeated
   here because without it E1–E5 cannot be evaluated.

**Equivalence contract.** `rarity_years` changes meaning: declared, both retained one generation.

**Decision M-6.** Is L5 authorised to consume Saṅgam windows as prediction candidates once the
identity is stable — i.e. does `EMPIRICALLY_EVALUATED` open for this asset first?

---

## §4 — Interactions and sequencing

| Order | Elevation | Why here | Depends on |
|---|---|---|---|
| 0 | Companion brief (output contract) | nothing below is testable without typed testimony and stable identity | native ruling on brief |
| 1 | **E2** aṣṭakavarga | smallest, most classical, revives a dead current, needs one L1 adjudication | frame query |
| 2 | **E4** the three gates | pure joins on existing L1 facts; changes applicability, not geometry | M-4 values |
| 3 | **E5** triple-pass | contained change to event grouping; fixes an independence error | none |
| 4 | **E1** Vedic contact model | deepest change; changes what "transit" means for every downstream asset | M-1; E5 (grouping runs on the new events) |
| 5 | **E3** fast tier | needs E1's dṛṣṭi model for the Moon and the ruling in M-3 | E1, M-3 |
| 6 | **E6** measured rarity + L5 | needs the identity and the sweep from all of the above | brief §5.2; E1 |

**Independence bookkeeping each step owes** (U02): E3 adds *no* group (coupled to parent); E5
*reduces* three to one; E1 changes the "transit" member's meaning — the coupling table's
`transit + dasha → independent` row must be re-examined once the transit is sign-based from the
Moon, because a Moon-relative gochara rule and a Moon-nakṣatra daśā share a root [J].

**Efficiency (P4).** E1 and E2 reduce work; E3 is bounded by construction; E4/E5 are joins and
grouping. No elevation here trades time resolution or method coverage for speed.

---

## §5 — Proof and acceptance

Every E carries a falsifying test above. Plus, layer-wide:
- **Doctrine oracle**: a native-ruled set of ≤20 hand-worked windows on the canonical chart, one
  per rule class, is the reference — not the old output (Strategy §5).
- **Ablation set**: E1 vs legacy on the same predicates (do the models disagree where doctrine
  says?); E4 gates on/off for a domain question; E5 grouping on/off for independence counts.
- **Calibration**: E6 against the LEL, only for windows with stable identity; reported per
  `comparability_class`, never pooled across grains.
- **Non-regression**: the companion brief's proof matrix (positive, negative, duplication,
  delivery sentinel) must still pass after each E.

## §6 — Decisions for the native (method rulings)

| # | Decision | Owner |
|---|---|---|
| M-1 | Contact interval model: Parāśari dṛṣṭi + gochara-from-Moon; fate of the Ptolemaic scan | native |
| M-2 | Aṣṭakavarga frame adjudication (L1) and BAV thresholds | L1 owner + native |
| M-3 | Bounded fast tier inside windows — consistent with the June "slow only" ruling, or an amendment? | native |
| M-4a/b/c | Sandhi zone + multiplier; capability floor + source; varga–domain table | native |
| M-5 | Triple-pass default peak phase | native |
| M-6 | L5 consumption of Saṅgam windows; opening `EMPIRICALLY_EVALUATED` | native |

## §7 — Non-claims and what this plan does not establish

1. No numerical value in this plan is proposed as a fact; every multiplier, floor and threshold
   is `[NATIVE-RATIFY]` (B.10).
2. Chapter numbers for BPHS dṛṣṭi/varga adhyāyas are cited by topic, not verified verse `[U]`;
   the reviewer should confirm against the classical-texts corpus before any is quoted in code.
3. The sandhi doctrine is marked `[P]` — practice stronger than text. If the native holds it
   textually weak, E4(1) becomes optional.
4. Whether `chart_facts`' `<GRAHA>-HOUSE_<N>` is rāśi- or bhāva-framed is **unknown** and is the
   single fact E2 turns on.
5. No live database query was run for this plan; all counts are from the readiness lane's
   read-only session or the code's own comments.
6. E3 is the one item that touches a standing native ruling; it is presented as a question.

## Changelog
- **0.1** (2026-09-22) — first issue for independent (Astra) review.
