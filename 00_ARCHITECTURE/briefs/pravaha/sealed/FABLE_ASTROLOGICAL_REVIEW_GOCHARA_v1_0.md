---
artifact: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
canonical_id: FABLE_ASTROLOGICAL_REVIEW_GOCHARA
version: "1.0"
status: SUPERSEDED
superseded_by: "FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md (2026-09-29) — restructured around the coarse-to-fine hierarchy the native asked for, adds the missing/overkill audit and the efficient-implementation strategy; the verified findings and worked examples are carried forward unchanged"
date: 2026-09-29
reviewer: "Claude Fable 5.1 (astrology-first review, requested by the native 2026-09-29)"
subject: "The Gochara family transit engine — the astrological content of λ_v3 as designed, and as it actually computes in the '4.0' candidate built on the canonical chart 482012f1 on 2026-09-28"
chart_scope: "482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty) only — per the native's directive of 2026-09-29 no other chart is in scope for builds or for this review"
basis: >
  Source read at l3/gochara-autonomous-wp0-7 @ ec4c35110 (services/gochara_v3/**, services/gochara_kernel/**,
  services/gochara_grammar/**, services/gochara_intensity/**, services/ka_gochara_resonance/writer.py,
  services/ka_vedha_gochara/**, services/ka_moorti_nirnaya/**, scripts/kala_gochara_cutover/step06*.py);
  production read-only 2026-09-29 (gochara_resonance_map, kala_gochara_contacts '4.0', kala_vedha_gochara,
  kala_gochara_windows '3.0', bg_transit_rules, bg_transit_av_gates, chart_facts, chart_dashas, ga_yoga_firings);
  the '4.0' factor delta report .run/wp10_tranche2/prod_link3_delta_report_482012f1.md and run report;
  LIFE_EVENT_LOG_v1_2.md; L0 ephemeris via ref_planet_position_get for the three worked dates.
  Three parallel code readers extracted file:line facts; every load-bearing claim below was re-verified by me
  in source or in production data before being written.
evidence_labels: "[S] source at ec4c35110, file:line · [L] live production read, 2026-09-29 · [R] repository record · [D] doctrine, text named, already verified in the served corpus by this campaign · [P] practice (widely taught, no primary verse claimed) · [J] my astrological judgment · [U] unverified — to be settled by a count(*) against classical_text_chunks (F-32 rule), never by assertion"
what_this_is_not: "Not an engineering review. Not a re-litigation of ruled items (D-1..D-3, R1–R10, N-1..N-22, M-1..M-8). Where a ruling is astrologically sound but the code does not do what the ruling says, that is reported as a gap between ruling and build, not as a challenge to the ruling."
next_step: "Native incorporates what is accepted; an independent review (GPT/Astra, effort max) then re-reads the incorporated design. §5 lists the questions that review should be asked to adjudicate."
---

# Gochara — astrological review of the transit engine (what it factors in, why, and how to make it accurate)

## 0. Read this first

**The question asked.** What does the Gochara engine factor in to name a specific time window for a specific
event; in what relationships and contexts; why was it built that way; and what would make it astrologically
accurate. Technology is out of scope here except where it changes what the astrology computes.

**The one-paragraph answer.** The *design* is a sound Parāśari frame: a natal **promise** (which houses,
lords and kārakas signify the event), a daśā **permission** (does the running period license it), a transit
**trigger** (which graha touches which natal point, when, by what relation), qualified by **gochara-vedha**,
**tārā-bala** and **aṣṭakavarga**. That is the classical triad every competent jyotiṣī uses, made explicit and
computable. The *build*, however, has drifted a long way from the design. In the `'4.0'` candidate on your
chart the promise term is 1.0 for all 27 classes, the permission term is a per-class constant over the whole
decade, tārā never fires, the house-frame for the gochara-phala rules is mixed (Moon-relative rules applied
from the lagna), the special aspects of Mars and Saturn are computed in the mirrored direction, 98.6 % of the
stored contacts contribute nothing, every window reads "favourable" including separation and deception, and
every peak in a class has the same height so nothing can be ranked. What is left is: *any of six bodies within
5° of a handful of natal graha degrees*. That is not the design, and it is not Jyotiṣa. The good news is that
almost all of it is repairable inside the existing frame, and L1 already holds most of the facts the repairs
need (§4).

**How to read the verdicts.** Each component in §3 gets one of: **SOUND** (doctrine right, code right) ·
**SOUND-UNWIRED** (doctrine right, never reaches the score) · **INVERTED** (code does the opposite of the
doctrine) · **MISSING** (classical and absent) · **UNCITED** (present, no admitted source).

---

## 1. The design as intended — the "secret sauce", in astrological terms

### 1.1 The governing equation and its classical reading

```
λ_class(t) = PROMISE_class × PERMISSION_class(t) × ACTIVITY_class(t) × tārā(t) × w30(t) × quality_gates(t)
```
`[S]` services/gochara_v3/engine.py:877; reproduced in step06b_windows_projection.py:274-315.

| Term | Astrological meaning intended | Classical warrant the design leans on |
|---|---|---|
| PROMISE | *Does this chart signify this event at all?* — the natal bhāva/lord/kāraka structure of the class | Bhāva-kārakatva (BPHS bhāva chapters; ontology citations per class) `[D]` |
| PERMISSION | *Is the event licensed now?* — the running daśā lords (8 systems) plus four transit "licences" (Sade-Sati, Guru–Śani double transit, aṣṭakavarga threshold, planetary return) | The daśā–gochara concurrence principle: daśā shows, gochara delivers `[P]`; the design's own D-3 premise `[R]` |
| ACTIVITY | *Is a transiting graha touching a signifying point right now?* — noisy-OR over the contacts in orb | Transit judged against each natal graha's position (BPHS ch.66–72, `[D]` per plan §4.2); per-graha dṛṣṭi (BPHS ch.26 `[D]`) |
| tārā | Moon's nakṣatra counted from janma nakṣatra (9-fold cycle) as a day-quality modifier | Muhūrta tārā-bala `[P]`; text cited in code: Muhūrta Cintāmaṇi `[U]` |
| w30 | Nodal 5/7/9 dṛṣṭi | refuted for BPHS (F-29); **removed** by N-14 `[R]` |
| quality_gates | Gochara-vedha (obstruction from the Moon sign), laṭṭā, sarvatobhadra vedha — attenuators only | Phaladīpikā Adh. XXVI (PG322–353) `[D]` |

**Why multiplicative.** A product encodes the doctrine that *all three* must concur: a strong promise with no
daśā licence yields nothing; a licensed period with no trigger yields nothing; a trigger on an unsignified
point yields nothing. That is the right shape `[J]`, and it is the reason the collapse of any one term (§2) is
fatal to the whole score rather than merely weakening it.

### 1.2 What the natal chart contributes — the resonance map

`gochara_resonance_map` `[L]` says, per event class, which natal points a transit must touch. Seven target
types, each carrying a **type-constant** weight (writer.py:405-446, 304-309, 505, 540, 571, 684, 701 `[S]`):

| target_type | What it is astrologically | weight | cited? |
|---|---|---|---|
| bhava | the class's signature houses as whole-sign spans from the lagna | 1.0 | yes (ontology) |
| lord | the lords of those houses ("7L") | 1.0 | yes |
| karaka | naisargika kārakas of the class (Venus for marriage, Jupiter for children…) | 1.0 | yes |
| mechanism_node | a `bg_transit_rules` row (graha × house, favourable/unfavourable/double-transit) — the Phaladīpikā gochara-phala table | +1.0 / −1.0 / 0.75 | yes (Adh. XXVI, verse-cited for 36 rows) |
| dasha_lord_portfolio | Vimśottarī MD lords that are also class kārakas (in practice: the kāraka list again) | 0.8 | no |
| yoga_constituent | natal grahas that constitute any fired yoga overlapping the class's houses/kārakas | 0.7 | no |
| arudha | ārūḍha padas A_h of the signature houses (sign-level) | 0.6 | no |
| sensitive_degree | mṛtyu-bhāga / gaṇḍānta / kartari / puṣkara checks on the kāraka grahas | 0.5 | no |

The 27 class signatures (houses · lords · kārakas), from the ontology seed `[S]` migrations 388/456:

| class | houses | lords | kārakas | | class | houses | lords | kārakas |
|---|---|---|---|---|---|---|---|---|
| marriage | 7, 2 | 7L | Venus | | separation | 6, 8, 12 | 7L (afflicted) | Rahu, Saturn, Mars |
| romantic_start | 5, 7 | 5L, 7L | Venus | | childbirth | 5, 1 | 5L | Jupiter |
| career_entry | 10, 6, 1 | 10L, 6L | Sun, Saturn | | career_advancement | 10, 11 | 10L, 11L | Sun |
| career_change | 10, 3, 9 | 10L | Rahu | | career_setback | 10, 6, 8, 12 | 10L (afflicted) | Saturn, Rahu |
| business_launch | 7, 10, 11 | 7L, 10L, 11L | Mercury, Jupiter | | achievement_recognition | 10, 11, 5 | 10L, 11L, 5L | Sun, Mercury |
| education_milestone | 4, 5, 9 | 4L, 5L, 9L | Mercury, Jupiter | | exam_outcome | 5, 9 | 5L | Mercury |
| major_gain | 2, 11 | 2L, 11L | Jupiter, Mercury | | major_loss | 2, 11, 12 | 2L, 11L (affl.), 12L | Saturn, Rahu |
| financial_deception | 2, 11, 12 | 2L, 11L (affl.), 12L | Rahu, Saturn | | property_acquisition | 4 | 4L | Mars |
| relocation | 4, 3, 12 | 4L, 3L | Moon, Rahu | | foreign_settlement | 12, 9, 7 | 12L, 9L | Rahu |
| travel_event | 3, 9, 12 | 3L, 9L | Moon | | illness_acute | 6, 8 | 6L, 8L | Mars, Saturn |
| chronic_onset | 6, 8 | 6L, 8L | Saturn | | surgery | 6, 8 | 6L, 8L | Mars |
| bereavement | 8, 12, 2 | 8L, 2L, 7L | Saturn, Ketu | | parental_event | 4, 9 | 4L, 9L | Moon, Sun |
| spiritual_turn | 9, 12, 5 | 9L, 12L | Jupiter, Ketu | | psychological_arc | 1, 6, 12 | 1L, 6L | Moon, Mercury, Saturn |
| birth_anchor | 1 | 1L | Sun | | | | | |

This is a respectable Parāśari signature table `[J]`. Its intent is clear and mostly conventional: kalatra-bhāva
and Venus for marriage; putra-bhāva and Jupiter for children; the duṣthānas with Mars/Saturn/Rahu for
separation and illness; 8/12/2 with Saturn/Ketu for bereavement.

### 1.3 What time contributes — the contact relations

The kernel solves, for each transiting body × natal target, the exact instants of `[S]` convention.py:45-55,
contacts.py, episodes.py:

| relation | meaning | orb (as built) |
|---|---|---|
| conjunction | body on the target's degree | 5.0° (`--orb-deg`, overriding the 1.0° table value) |
| drishti_contact | body's special aspect degree on the target: Mars 4/8, Jupiter 5/9, Saturn 3/10, all 7th | 5.0° |
| return | body on its own natal degree | 0.5° |
| sign_ingress / nakshatra_ingress | body crosses a sign / nakṣatra boundary | 0 (instant) |
| kakshya_cell_crossing | body crosses a 3.75° kakṣyā boundary | 0 (instant) |

Agents: Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu (the Moon on demand — M-3). Every body is
tried against every point target; only mechanism nodes and the M-6 rows restrict the agent
(step06_enumerate_episodes.py:410-419, 621-658 `[S]`).

### 1.4 The permission layer

Twelve "systems", each a weighted vote (`SYSTEM_WEIGHTS`, permission.py:100-113 `[S]`): Vimśottarī 0.16 ·
Chara (Jaimini) 0.10 · Nārāyaṇa 0.08 · Mudda 0.09 · Yoginī 0.07 · Aṣṭottarī 0.07 · Naisargika 0.05 ·
Kālacakra 0.05 · Sade-Sati 0.10 · Guru–Śani double transit 0.10 · AV threshold 0.06 · planetary return 0.07.
A daśā system votes "yes" when the running lord is one of the class's relevant grahas/signs. PERMISSION is the
weighted fraction that says yes.

### 1.5 The qualifiers and gates

- **Gochara-vedha** (`ka_vedha_gochara`): houses counted **from the natal Moon** (logic.py:446-450 `[S]` —
  correct frame), favourable house → vedha house pairs from `bg_transit_rules` (36 rows verse-cited to
  Phaladīpikā PG322/323 `[L]`), Sun↔Saturn and Moon↔Mercury exceptions (M-8), vipareeta cancellation (M-8),
  a `retrograde_malefic` qualifier (M-2). Attenuates λ by a malefic-count schedule.
- **Laṭṭā** (Phaladīpikā PG338–339 `[D]`): forward/backward star counts per graha; fires on the janma nakṣatra.
- **Sarvatobhadra**: grid tables empty; a cyclic-opposite approximation stands in (`uncited_extension`).
- **Mūrti-nirṇaya** (`ka_moorti_nirnaya`): gold/silver/copper/iron grade at ingress — computed, **not** in λ.
- **Koṭa-cakra**: computed, consumed by nothing in λ.
- **Tārā-bala** (w23): Moon's nakṣatra from janma nakṣatra, 9-fold, modifiers 0.70–1.20.

### 1.6 The '4.0' rulings and why they were made

| ruling | change | astrological reason given | my verdict on the *ruling* |
|---|---|---|---|
| D-1 | Swiss sidereal Lahiri, nutation-consistent | the old arcs were built on tropical longitudes (F-07) | SOUND — necessary |
| N-4/N-4a | mean node | L1 natal is mean; one convention for natal and transit | SOUND (either convention is defensible; consistency is what matters) |
| M-1 | activity linear in separation, no ±5-day box; 5.0° for candidate 1, 1.0° carried | BPHS ch.26 śl.6–8 graduated dṛṣṭi-koṇa as the warrant for separation-scaling `[D]` | SOUND in shape; the 5.0° value is a practice figure (`uncited_extension`) — see §3.15 |
| M-3 | Moon out of the century score; on-demand Moon channel | no admitted text scores daily Moon transits at century scale; 43 % of served aspect records were Moon noise | SOUND for the *century* score; the Moon must come back as the **day-level trigger** (§3.8) |
| M-8 | vedha exceptions + vipareeta + retrograde qualifier | Phaladīpikā PG322/323/348/350 `[D]` | SOUND |
| N-14 | no nodal dṛṣṭi; nodes stay agents and targets | BPHS ch.26 names only Saturn/Jupiter/Mars (F-29 `[D]`) | SOUND on the corpus; note Rahu's 5/9 aspect is common *practice* (Jaimini/nāḍī lineages) — keep it out of the score, keep it as testimony `[J]` |
| N-15 | Sade-Sati out of the λ product, to testimony | only nāḍī rows in the corpus; no primary Parāśari text for the composite | SOUND as a *weight* decision; but Saturn 12/1/2 from the Moon *is* in Phaladīpikā's unfavourable table (rule id 39 `[L]`), so it must not vanish from the mechanism-node layer (§3.10) |
| N-17 | no cap on peaks | truncation was masquerading as absence (F-10) | SOUND |
| N-22 / N-13 | kakṣyā crossing with no bindu → no activity | BPHS aṣṭakavarga: a transit gives fruit in the kakṣyā of a bindu-donor `[D]` (nāḍī PG1615/1616 for contributor semantics) | SOUND — the interim (sign-level BAV, ≥1 bindu) is too permissive (§3.4) |

### 1.7 Why it was built this way — and what the philosophy costs

The build discipline behind all of this is: cite or flag (`uncited_extension`), never invent a number (B.10),
store an honest null rather than a plausible default (§N.7), persist what was computed (N-7). Those are the
right rules for a research instrument and they are why the defects below are *findable* at all — every one of
them is visible in a stored field. The cost is that the engine was assembled bottom-up from *cited fragments*
(a rule table here, a check there) without a top-down astrological audit of what the fragments add up to.
The result is a score whose parts are each defensible and whose product is not (§2). The elevation this
review recommends is exactly that audit, turned into design (§4).

---

## 2. What actually reaches the number today — verified

### 2.1 The collapse, term by term

| # | Finding | Evidence | Known to the campaign? |
|---|---|---|---|
| 1 | **PROMISE = 1.000 for all 27 classes.** It is a noisy-OR over type-constant weights; any weight-1.0 target saturates it. It encodes *nothing* about this chart's strength for the event. | promise.py:61-74 `[S]`; delta report per-class table `[L]` | No |
| 2 | **PERMISSION is a per-class constant over the whole decade** (0.42–0.88). The daśā vote was taken as "did the system fire at *any* candidate instant in 10 years" (union semantics). Daśā timing therefore does not move λ in time at all. | step06a_class_context.py:23-31 `[S]` (disclosed there as "static per-class collapse"); class-context JSON `[R]` | Disclosed as a collapse; not treated as a doctrinal defect |
| 3 | **Only mahādaśā is read** (level 1). No antardaśā, no pratyantar, in the map or in permission. | dasha_data.py:37; context.py:258-261 `[S]` | No |
| 4 | **Sade-Sati permission never switches off** in the engine: phase start is used with an open end 9999-12-31. | engine.py:2006 `[S]` | No |
| 5 | **Tārā-bala never fires.** The mechanism reads `graha_longitudes["Moon"]`; the context keys by subject code `"MOON"`. In '4.0' it is called with `None`. No served row carries a tārā value. | w23_tara_bala.py:213 vs context.py:362 `[S]`; '3.0' rows: no tārā key, stored formula = `PROMISE × PERMISSION × activity × quality_gates` `[L]` | No |
| 6 | **98.6 % of contacts contribute zero.** Every sign/nakṣatra/kakṣyā crossing is stored with `t_in = t_exact = t_out`; the M-1 decay returns 0 on a zero-width span. Chart-2 ledger (structurally identical to chart 1's): 136,887 of 138,836 rows zero-width; the score rests on 253 conjunctions + 369 dṛṣṭi + 29 returns (physical contacts). | episodes.py:399-401; step06b:209-228 `[S]`; ledger query `[L]`; link3 evidence 28 Sep `[R]` | Disclosed 28 Sep as "amplitude-inert"; not treated as doctrinal |
| 7 | **House-level targets never reach the score.** bhāva, ārūḍha and mechanism-node targets exist only as zero-width `sign_ingress` rows — the residence spans the contract promised (WP1 §7 "residence") were never materialised. | ledger query: sign_ingress × {bhava 361, arudha 356, mechanism_node 140}, all zero-span `[L]` | No |
| 8 | **House lords and yogas resolved as "unavailable"** — 647 of 1,140 targets (52 lord + 595 yoga). For Aries lagna that removes Saturn (10L/11L), Sun (5L), Moon (4L), Jupiter (9L/12L), Mars (1L/8L), Mercury (3L/6L) as *lord* targets. | step06 evidence `[R]` | Yes (recorded; disposition owed) |
| 9 | **Production resonance map is pre-WP3c.** Negative sensitive checks (`not_gandanta`, `not_pushkara`, `not_fired`) are still targets; the '4.0' candidate was built on them. | map query `[L]` (marriage carries VEN not_gandanta / not_pushkara / not_fired) | Yes (R-1..R-6 "inert until the step-6 rebuild") |
| 10 | **Two house frames are mixed.** `bg_transit_rules.primary_house` is counted from the natal **Moon** (migration 266:53-55); the resonance writer matches it against **lagna** signature houses (writer.py:950), and the '4.0' driver resolves the node's sign from **LAGNA** (step06:410-419). The Phaladīpikā gochara-phala table is being applied from the wrong reference point. | `[S]` | Only the vedha-pair case (MR-43) |
| 11 | **Rule sign is taken as-is, not relative to the class.** illness_acute carries Mars/Saturn *favourable*-6th ("good health") at +1; bereavement carries Ketu favourable-12th at +1; property_acquisition's only mechanism is Mars *unfavourable*-4th at −1 — and negative weights are clamped to 0, so for adverse classes the malefic rules count for nothing. | writer.py:304-309; configuration_activity.py:133 `[S]`; map rows `[L]` | No |
| 12 | **Every '4.0' window is "favourable"** — all 1,435 era rows, including separation, financial_deception, bereavement, illness. Valence comes from a supportive-vs-afflicting channel balance keyed on the *sign of the target weight*; almost all weights are positive. The '3.0' writer used the class label instead. | legacy_semantics compute_signed_channels_v3 / resolve_valence_v3 `[S]`; delta report `[L]` | No |
| 13 | **Mars's and Saturn's special aspects are mirrored.** The solver fires when the *body* is at `target + angle`, i.e. the target sits *behind* the body. Mars's 4th/8th land on the 10th/6th from Mars; Saturn's 3rd/10th on the 11th/4th. Jupiter (5/9 symmetric) and the 7th are unaffected. The legacy path has the same convention. | contacts.py:206-213; transit_search.py:320 `[S]` | No |
| 14 | **Ingress into Aries (and Aśvinī) is never a root** — the boundary list runs 30°…330°. Your lagna is Aries: the 1st-house residence/ingress (birth_anchor, childbirth h1, career_entry h1, psychological_arc h1) can never be detected. | contacts.py:259-262 `[S]` | No |
| 15 | **No graduated dṛṣṭi.** Only full-strength aspects at the special angles; BPHS ch.26's quarter/half/three-quarter graduation is cited in `convention.py:39-40` and not applied. | `[S]` | No |
| 16 | **Vedha grade names do not match the scale table** (`fear/failure/killing/death/ignominy` stored vs `fear/grade_2/…` looked up): any vedha by 2–4 malefics takes the harshest factor 0.35; every laṭṭā (graded as 3) takes 0.35. | legacy_semantics.py:690-693 `[S]` | No |
| 17 | **Inactive and cancelled vedhas still suppress.** The gate ignores `obstruction_active`, `cancelled` and `independence_group`. On your chart: rows with no active obstruction still apply 0.85; vipareeta-cancelled rows still attenuate. **A clean favourable Moon-sign transit — the thing the doctrine calls good — lowers λ by 15 %.** | legacy_semantics.py:696-783 `[S]`; kala_vedha_gochara rows `[L]` (obstruction_active=false / cancelled=true rows present) | No |
| 18 | **The gochara-phala table is never a positive factor.** Moon-relative houses appear only as vedha suppression and in the AV gate (where the Moon-relative column is compared with lagna house numbers, and the bindu count is never compared: `bindu_count_resolved: False`). | engine.py:2093-2116; primitives.py:808 `[S]` | No |
| 19 | **Kakṣyā lords are never used; the L1 kakṣyā grid is never read** (subject-key mismatch `KAKSHYA_k` vs `{planet}.{index}`); the uncited equal-eighths fallback always runs. A crossing is 8 boundaries × 9 grahas, each worth 0.5 × weight in the legacy engine and 0 in '4.0'. | context.py:669-672; primitives.py:628 `[S]` | Partly (F-09, F-27) |
| 20 | **No strength anywhere.** No ṣaḍbala, dignity, exaltation, combustion, functional benefic/malefic, natural friendship, vargottama — in promise, activity, or agent selection. | grep of the whole engine `[S]` | No |
| 21 | **The class signature's own trigger agents are dropped.** The ontology's `transit_triggers` ("Jupiter/Saturn transit to 7th; Jaimini DK activation" for marriage) is never read; `vargas` and `dasha_rules` are never read. Every body is tested against every target. | writer.py:939-944 `[S]` | No |
| 22 | **Yogas attach to classes by mere overlap**; strength ignored; Kedāra (all seven grahas) lands on nearly every class; rāja/dhana yogas land on childbirth, foreign_settlement, spiritual_turn. | writer.py:820-834 `[S]`; map `[L]` | No |
| 23 | **"afflicted" is a label, not a check.** No test that 7L/10L/11L is actually afflicted in this chart. Weight 1.0 either way; nothing downstream reads the qualifier. | writer.py:357-362, 427 `[S]` | No |
| 24 | **Every peak in a class has the same height** (childbirth: 13 peaks at 0.6272 in 2020–22; separation: 0.4998–0.5100). λ_peak ≈ permission × quality_gates because activity saturates at 1.0 on any exact contact. Nothing can be ranked. The "day" tier is the argmax of a nearly flat curve, not a day-level trigger. | delta report `[L]`; step06b peak logic `[S]` | No |
| 25 | **The overlay covers 1.26 % of the century** (2026-07-29 → 2027-11-01). Outside it `quality_gates = 1.0` because no rows exist, not because the sky is clear (F-11). Inside it, 99 of 127 house-vedha rows are **Moon** transits — day-scale noise attenuating decade-scale windows. | kala_vedha_gochara `[L]` | F-11 known; the Moon-dominance is new |
| 26 | Sade-Sati still carries its 0.10 permission weight in '4.0' despite `sade_sati_mode=testimony` (the testimony path exists only in the engine). | legacy_semantics.py:109-129; step06b:141 `[S]` | No |
| 27 | Mūrti is computed and never enters λ; the AV gate uses the *rule's* `min_sav_score` as a proxy and never the chart's bindus (w21). | engine.py; w21 `[S]` | Partly |

### 2.2 Three of your own events, read classically, against what the engine can see

All positions Lahiri sidereal from L0 (`ref_planet_position_get`) `[L]`; natal from `chart_facts` `[L]`:
Lagna Aries 12°26′ · Sun Cap 21°58′ (10) · Moon Aqu 27°03′ (11, Pūrva-Bhādrapadā) · Mercury Cap 0°50′ (10) ·
Venus Sag 19°10′ (9) · Jupiter Sag 9°47′ (9, Mūla) · Mars Lib 18°31′ (7) · Saturn Lib 22°26′ (7, exalted) ·
Rahu Tau 19°02′ (2) · Ketu Sco 19°02′ (8). Aries lagna lords: 1L Mars · 2L/7L Venus · 3L/6L Mercury · 4L Moon ·
5L Sun · 8L Mars · 9L/12L Jupiter · 10L/11L Saturn.

**(a) Marriage, 2013-12-11 — Mercury MD / Ketu AD.**
Saturn 24°15′ Libra: **Saturn return in the 7th house**, 1.8° from its natal exalted degree, over natal
Mars–Saturn. Jupiter 24°34′ Gemini (R): its **5th aspect falls at 24°34′ Libra — on natal Saturn (2.1°) and on
transiting Saturn (0.3°)**; its 9th aspect at 24°34′ Aquarius sits on the natal Moon (2.5°). Ketu 12°59′ Aries
**exactly on the lagna degree (0.6°)**, Rahu in the 7th. That is the textbook signature: Jupiter and Saturn both
on the 7th house (double transit), Saturn returning to its own exalted 7th-house degree, the AD lord on the
lagna. `[D][J]`
*What '4.0' could see for `marriage`:* natal Venus's degree and Jupiter's degree (via the negative sensitive
checks) as point targets; the 7th house as an inert span; 7L unresolved (coincidentally Venus); Saturn's
natal degree is not a marriage target at all. The double transit is invisible; the Saturn return is invisible;
Ketu on the lagna is invisible. Any window it produced here would have come from a fast body within 5° of
natal Venus.

**(b) Twin daughters, 2022-01-03 — Mercury MD / Rahu AD.**
Jupiter 6°52′ Aquarius (11th house): its **7th aspect falls on Leo — the 5th house (putra-bhāva)**. Saturn
18°01′ Capricorn: **conjunct natal Sun, the 5th lord, within 4°**. So Jupiter aspects the 5th house while
Saturn sits on the 5th lord — a double transit on the 5th, with the AD lord Rahu transiting the 2nd
(kuṭumba). `[D][J]`
*What '4.0' could see for `childbirth`:* natal Jupiter's degree; bhāva 1/5 inert; **5L (Sun) unresolved** —
the Saturn-on-5th-lord contact does not exist in the ledger; Jupiter's aspect on the 5th house is a zero-width
ingress. The engine's peaks at 2021-12-16 and 2022-01-29 (0.6272, identical to eleven others) come from
something touching natal Jupiter's degree, not from the mechanism above.

**(c) Father's passing, 2018-11-28 — Mercury MD / Moon AD.**
Saturn 13°26′ Sagittarius, **in the 9th house (father), conjunct the 9th lord Jupiter's natal degree (3.6°)**;
Sun (pitṛ-kāraka), Jupiter and retrograde Mercury clustered in the **8th house**; Ketu conjunct natal Mercury
(3°) in the 10th. Saturn over the 9th lord in the 9th, Sun in the 8th: classical. `[D][J]`
*What '4.0' could see:* `bereavement`'s lords are 8L/2L/7L and kārakas Saturn/Ketu — natal Jupiter is not a
bereavement target; `parental_event` has 9L as a lord target, which is unresolved. The trigger that a first-year
student would name is not in the target set of either class.

The pattern across all three: **the events were delivered by lords, houses and double transits — exactly the
three things the '4.0' score cannot see.** The things it *can* see (fast bodies on kāraka degrees) are the
weakest classical triggers.

### 2.3 The '3.0' engine's opposite failure (context)

The served `'3.0'` score is the mirror image: ingress and kakṣyā crossings *did* contribute (0.5 each, at every
instant a slow planet resided in an aspected sign), so activity sat at 0.9996–1.0 on every row with a value
(F-09 `[L]`), and the same three terms (promise 1.0, permission a step function, no tārā) applied. Two builds,
two ways of making the transit term uninformative. Neither is a calibration problem; both are design.

---

## 3. Doctrine assessment, component by component

### 3.1 Frame of reference — **INVERTED (partly)**
Classical gochara-phala and vedha are reckoned **from the janma-rāśi (natal Moon)** (Phaladīpikā Adh. XXVI
`[D]`); bhāva-based transit (Saturn over the 9th house, Jupiter aspecting the 5th) is reckoned **from the
lagna**; aṣṭakavarga transit is reckoned **against each natal graha's bindus by sign**. All three frames are
legitimate and *complementary* — a mature reading uses all three and notes where they concur. The build has
the vedha writer correct (from the Moon) but the mechanism-node layer wrong (Moon-table rows resolved from the
lagna, finding 10). **Fix:** carry an explicit `frame ∈ {moon, lagna, graha}` on every rule and every target;
resolve mechanism nodes from the Moon; add the lagna-frame bhāva transit as its own relation (§4 T0-2).

### 3.2 The gochara-phala table and vedha — **SOUND-UNWIRED / INVERTED**
The 36 verse-cited rows are the right table. Three faults: (i) it is never a *positive* factor — a favourable
transit only ever *lowers* λ (finding 17), which is the doctrine upside down; (ii) the malefic-count schedule
is broken (16) and ignores cancellation (17); (iii) the Venus pairs 11→3 / 12→6 look transposed against the
usual 11→6 / 12→3 — **verify against PG323 `[U]`**. Laṭṭā's severity multiplier (śl.47) is not implemented `[U]`.
The Rahu/Ketu house rows are honestly `UNSOURCED` — keep them out of the score.

### 3.3 Dṛṣṭi — **INVERTED (Mars, Saturn) / MISSING (graduation)**
Finding 13 is the most consequential single geometry error in the family: it silently relocates every Mars
4th/8th and Saturn 3rd/10th contact for both `'3.0'` and `'4.0'`. Fix the sign convention (body = target − angle)
and add a regression fixture with a hand-computed case (e.g. Saturn at 24° Libra → 3rd aspect at 24°
Sagittarius). Then implement BPHS ch.26 śl.6–8 graduation (¼ at 3/10, ½ at 5/9, ¾ at 4/8, full at 7, with the
special aspects full) as the *activity weight per aspect* — this is verse-cited and already the warrant M-1 cites.
Rāśi-dṛṣṭi (sign-to-sign) and sphuṭa-dṛṣṭi (degree) should both be stored, as residence and as point.

### 3.4 Aṣṭakavarga — **SOUND in design, MISSING in build**
This is the most classical *transit-timing* system in the corpus (BPHS ch.66–72 `[D]`) and it is the one the
build uses least. What L1 already holds `[L]`: BAV per graha per sign (`ashtakavarga_bindu_sign`, 96 rows), SAV
(`ashtakavarga_bindu`), trikoṇa and ekādhipatya śodhana, śodhya piṇḍa per graha (`ashtakavarga_pinda_sodhita`,
`_bhinna`, `_raasi`, `_sarva`), kakṣyā boundaries. What the engine does with them: nothing that reaches λ.

Four classical mechanisms to wire, in order of value `[J]`:
1. **BAV bindus of the transiting graha in the transited sign** as the activity weight for *every* contact
   by that graha in that sign (0–1 bindus: suppress; 4: neutral; ≥5–6: amplify; 8: full) — BPHS ch.66–72 `[D]`.
   This replaces the saturated activity with a chart-specific gradient and is the substantive cure for F-09.
2. **Kakṣyā qualification by contributor** (G-10): a crossing counts only into a kakṣyā whose lord donated a
   bindu to that sign in that graha's BAV — nāḍī PG1615/1616 semantics `[D]`. The interim "≥1 bindu at sign
   level" is far too permissive (a 1-bindu sign is a malefic transit, not a qualified one).
3. **SAV in the transited sign** (≥28 favourable, <25 weak) as a sign-level gate — the existing `bg_transit_av_gates`
   intent, corrected to compare like with like and to read the chart's own SAV.
4. **Śodhya-piṇḍa timing**: piṇḍa × bindus-in-sign ÷ 27 → the nakṣatra whose Saturn transit (and trikoṇas)
   times the graha's affairs — BPHS ch.70 per plan §4.2 `[D]`. Per-graha "timing nakṣatras" become first-class
   targets (Saturn/Jupiter over them). L1 has the piṇḍas; nothing consumes them.

### 3.5 Daśā integration — **SOUND design, COLLAPSED build**
A time-varying permission is the heart of the design and it is constant in '4.0' (finding 2) and mahādaśā-only
everywhere (3). Classical practice reads MD–AD–PD together and asks whether the transit *of or to the running
lords* concurs `[P]`. Concretely: (i) evaluate permission **at each instant** (the engine already does; the
projection must stop collapsing it); (ii) read levels 1–3 and treat the **AD and PD lords as targets** (transit
over the AD lord; AD lord transiting over the MD lord or the class's signifying house) — `chart_dashas` holds
levels 1–4 for eight systems `[L]`; (iii) replace the flat 12-way vote with **applicability-gated** selection:
Vimśottarī as the spine; Aṣṭottarī/Ṣoḍaśottarī/Dvādaśottarī only where BPHS's applicability conditions hold;
Jaimini Chara alongside for Jaimini targets; Kālacakra/Nārāyaṇa/Mudda as corroboration, not as equal voters.
A weighted average of eight systems that mostly disagree is astrologically meaningless `[J]`. (iv) Fix the
Sade-Sati open end (4) and the testimony/weight mismatch (26).

### 3.6 Promise — **MISSING (the term exists, the astrology does not)**
PROMISE must answer "how strongly does this chart signify this class", and it must vary across classes and
charts. L1 already computes the inputs `[L]`: `graha_shadbala_total`, `bhava_bala_total_extended`,
`house_strength_classification_rollup`, `graha_dignity_per_varga`, `graha_functional_class_per_ascendant`,
`vargottama_per_varga`, `karaka_bhava_concordance`, `graha_ishta_phala/kashta_phala`, yoga strengths.
A defensible first form `[J]`: promise_class = f(bhāva-bala of signature houses, ṣaḍbala/dignity of their lords
and kārakas, relevant varga placement — D9 for marriage, D7 for children, D10 for career, D4 for property,
D24 for education — yoga presence *weighted by strength and relevance*), normalised so that a chart with
afflicted 7L/Venus/D9 does not read 1.0 for marriage. Keep the noisy-OR only for *presence*, never for strength.

### 3.7 Agent–target relationship and valence — **MISSING**
The score has no notion of *who* is transiting *what*. Saturn over the 7th lord and Jupiter over the 7th lord
are the same contact in '4.0'. Classically they are opposite events. Three layers to add `[J]`:
1. **Agent nature**: natural benefic/malefic; **functional** benefic/malefic for Aries lagna (L1
   `graha_functional_class_per_ascendant`); dignity of the transiting graha in the transited sign
   (L1 `graha_dignity_per_varga` covers natal — transit dignity is a reference lookup).
2. **Relationship**: the transiting graha's relationship to the target graha (pañcadhā-maitrī — L1 has
   `panchadha_maitri`, 42 rows) and to the class (kāraka of the class, lord of a signature house, lord of a
   duṣthāna from the signature house).
3. **Class-relative sign**: a favourable rule *supports* a gain class and *opposes* a loss class; an
   unfavourable rule the reverse. Encode `supports_class ∈ {+1, −1}` on the (rule, class) pair instead of
   copying the rule's own sign (finding 11). Then valence becomes a real quantity — the sign of the net
   supportive-minus-afflicting channel — and "financial_deception: favourable" becomes impossible (12).

### 3.8 The Moon — answering the earlier question, and Astra's R4
M-3 is right that the Moon must not swamp a century-scale score. But the classical role of the Moon in
*timing* is precisely the finest grain: the day of an event is when the Moon transits the signifying house, its
lord, or a trine of the daśā lord, under a favourable tārā `[P]`. That is what the "day" tier should be — and
today the day tier is the argmax of a flat curve (finding 24) with no Moon in it. Design `[J]`: the century
projection produces month-grain windows from slow bodies; **the Moon channel runs inside each month window**
and emits the day rows (Moon on the signature house/lord/kāraka/AD lord, tārā-bala, tithi/nakṣatra quality),
with its own coverage record. Astra's R4 objection ("do not amputate the Moon") and the native's M-3 are both
satisfied by that split. Also fix the Moon's *negative* role: 99 of 127 vedha rows are Moon transits
attenuating slow-planet windows for a day or two — restrict vedha rows in the century gate to slow bodies,
and let the Moon's vedha act inside the day channel only.

### 3.9 Nodes — **SOUND (N-14)** with two notes
Keep nodes as agents (conjunction, ingress, return) and targets. Nodal *return* (18.6 y) and half-return are
classically weak but practically strong `[P]` — keep, `uncited_extension`. Rahu's 5/9 aspect is lineage
practice, not BPHS — testimony, never weight. Ketu on the lagna at your marriage (§2.2a) is the kind of
contact that should at least be *reported* as testimony even while it carries no weight.

### 3.10 Sade-Sati and Saturn's special cycles — **SOUND ruling, INCOMPLETE build**
N-15 is right that the *composite* has no primary Parāśari text. But Saturn in the 12th/1st/2nd from the Moon
is in Phaladīpikā's unfavourable table (rule 39 `[L]`), and Saturn in the 4th (kaṇṭaka) and 8th (aṣṭama) likewise
— L1 already computes all of these as periods `[L]` (`sade_sati_phase`, `kantaka_shani_period`,
`ashtama_shani_period`, `ardha_ashtama_shani_period`, `dhaiya_period`). Use them as **interval testimony on
adverse classes** (present on the window row with a citation), and let the *mechanism-node* layer carry
Saturn-12/1/2-from-Moon as an ordinary verse-cited unfavourable rule with class-relative sign (§3.7). That
respects N-15 (no invented weight for the composite) without losing the doctrine that is actually cited.

### 3.11 Tārā-bala, mūrti, laṭṭā, sarvatobhadra, koṭa — **SOUND-UNWIRED / UNCITED**
- Tārā: fix the key (finding 5); apply it in the **day channel** only (it is a Moon-day quality), not to slow windows.
- Mūrti-nirṇaya: the code grades by Moon-nakṣatra mod 4; the widely taught rule grades by the Moon's **rāśi**
  from the natal Moon (1/6/11 gold, 2/5/9 silver, 3/7/10 copper, 4/8/12 iron) `[P]` — **verify the code's form
  against the cited chapter by count `[U]`** before wiring it. Once verified, mūrti is a natural per-ingress
  multiplier on that graha's whole sign residence (gold 1.25 … iron 0.75 is the code's own scale).
- Laṭṭā: verse-cited; implement the severity rule; Ketu gap honest.
- Sarvatobhadra: the cyclic-opposite stand-in is not the cakra. Either populate the grid from a standard
  construction (the campaign has withdrawn "buildable from PG346 prose") and label the school, or keep SBC
  as `unqualified` and out of the gate — never as a 0.85 attenuation on an approximation.
- Koṭa-cakra: computed, uncited (0 corpus rows), unconsumed. Leave out of λ; keep as testimony.

### 3.12 Retrograde, stations, returns, eclipses — **partly SOUND**
Three passes (direct–retro–direct) are stored with `branch` — good; classical practice treats the *retrograde*
pass over a natal point as intensifying and the third pass as delivering `[P]`; M-2's "typed testimony, no
weight" is the honest position until an ablation on real events. Stations within orb of a target should be a
distinct relation with a real orb (today 0.5 flat in legacy, absent in '4.0'). Returns (Saturn, Jupiter, nodes)
are practice `[P]` — keep with `uncited_extension`. Eclipses (w26) on natal points are classical (grahaṇa
chapters `[D]` as cited in code) and dormant — wire with real eclipse instants (H-4 already asks for this).

### 3.13 Yogas — **UNCITED and mis-attached**
Attaching every fired yoga to every overlapping class makes the target sets of unrelated classes nearly
identical (finding 22). Classical use of yogas in timing is narrower: a yoga's *constituents* become targets for
the classes the yoga *signifies* (dhana yogas → gain classes; rāja yogas → career/achievement; Gaja-kesarī →
recognition/children; Kemadruma/Anapha etc. → psychological), and their contribution is scaled by the yoga's
strength (L1 stores it) and by daśā activation of a constituent `[P][J]`. Add a `yoga → classes` map to the
ontology with citations; drop the overlap heuristic.

### 3.14 Divisional charts, Jaimini, Tājaka, KP — **MISSING (all computed at L1, none used)**
- **Vargas**: promise should read the relevant varga (§3.6). Transit *to* varga positions (Jupiter over the
  D9 lagna or D9 7th lord for marriage) is practice `[P]`; admit as testimony with `uncited_extension`.
- **Jaimini**: the ontology itself cites "Jaimini DK / putra-kāraka" for marriage and children but the writer
  uses naisargika kārakas only; L1 has `karaka_chara_position` (DK, PK, AmK, AK), `upapada_lagna`,
  `karakamsa_position`, `argala_natal_matrix`. Add DK/PK/AK and UL/A7/AL as targets for the classes that
  cite them; Jupiter/Saturn transit over UL and its lord for marriage is verse-cited practice in the Jaimini
  corpus (`bphs_jaimini`, 264 chunks) — **cite by count `[U]`**.
- **Tājaka**: L1 holds 70 sahams (`saham_position`, 560 rows) and Tājaka aspects; the Vivāha, Putra, Karma,
  Mṛtyu and Roga sahams are *event-specific* points whose transit and annual-chart activation are the
  Tājaka timing method `[D]` (text present in the corpus; predicate to verify `[U]`). This is the single richest
  unused L1 resource for class-specific targets.
- **KP**: not in the corpus (0 chunks) — L1's `kp_house_significators` may be served as testimony only.

### 3.15 Orbs and time grain — **UNCITED (declared honestly)**
5.0° for conjunction/dṛṣṭi is a practice figure; the WP8 battery preferred 1.0° on synthetic data; the native
chose 5.0° for candidate 1 to isolate the shape change — a reasonable sequencing decision. Astrologically the
orb should be **per agent** (Saturn/Jupiter wider, Sun/Mercury/Venus narrower) and, once BAV weighting exists
(§3.4), the orb matters much less than the bindu gradient. Time grain: era/month from slow bodies; day from
the Moon channel (§3.8). A "day" row that is not Moon-derived should not exist.

---

## 4. Elevation opportunities — prioritised

**Tier 0 — restore the intended doctrine (before any calibration; each is a defect, not a design choice)**

| id | change | why it comes first |
|---|---|---|
| T0-1 | Fix the dṛṣṭi sign convention (body = target − angle) in kernel and legacy; regression fixture | every Mars/Saturn special-aspect contact is currently in the wrong place (2.1 #13) |
| T0-2 | Carry `frame ∈ {moon, lagna, graha}` on rules and targets; resolve mechanism nodes from the Moon; add lagna-frame bhāva residence as a relation | #10 |
| T0-3 | Materialise **residence spans** for bhāva/ārūḍha/mechanism targets (t_in = ingress, t_out = egress) so interval targets carry activity; give ingress/kakṣyā crossings a declared span or drop them from activity | #6, #7 — 98.6 % of the ledger is inert |
| T0-4 | Resolve lords and yoga constituents (the 647 "unavailable") | #8 — the lords are where the events live (§2.2) |
| T0-5 | Permission evaluated per instant; levels 1–3; Sade-Sati end date honoured; testimony mode actually removes the weight | #2, #3, #4, #26 |
| T0-6 | Valence: class-relative rule sign (`supports_class`) and a real net channel; class prior only when nothing fires | #11, #12 |
| T0-7 | Vedha gate: match grade names; honour `obstruction_active`/`cancelled`/`independence_group`; no attenuation for a clean favourable transit; slow bodies only in the century gate | #16, #17, #25 |
| T0-8 | Tārā key fix; Aries/Aśvinī boundary root; L1 kakṣyā grid key fix | #5, #14, #19 |
| T0-9 | Rebuild the resonance map (R-1..R-6 landed) before any candidate; drop negative checks | #9 |

**Tier 1 — complete the classical core (each verse-cited or already ruled)**

| id | change | source |
|---|---|---|
| T1-1 | BAV-bindu weighting of every contact by the transiting graha in the transited sign; SAV sign gate reading the chart's own SAV | BPHS ch.66–72 `[D]`; L1 has both |
| T1-2 | Kakṣyā by contributor (G-10) replacing the ≥1-bindu interim | nāḍī PG1615/1616 `[D]`; L1 writer change already specified (migration 1086) |
| T1-3 | Śodhya-piṇḍa timing nakṣatras as targets for Saturn/Jupiter | BPHS ch.70 `[D]`; L1 has piṇḍas |
| T1-4 | Graduated dṛṣṭi weights (¼/½/¾/1) | BPHS ch.26 śl.6–8 `[D]` |
| T1-5 | Gochara-phala table as a *positive* mechanism (favourable-from-Moon supports gain classes) with vedha as its obstruction, exceptions and vipareeta applied per M-8 | Phaladīpikā XXVI `[D]` |
| T1-6 | PROMISE from natal strength (§3.6) — bhāva-bala, ṣaḍbala/dignity of lords and kārakas, relevant varga, yoga strength | L1 categories listed in §3.6 |
| T1-7 | Agent nature and relationship layer (§3.7) — natural/functional benefic-malefic, transit dignity, maitrī | L1 `graha_functional_class_per_ascendant`, `panchadha_maitri` |
| T1-8 | AD/PD lords as targets; applicability-gated daśā selection | `chart_dashas` levels 1–4 `[L]` |
| T1-9 | Moon day-channel inside month windows: Moon on house/lord/kāraka/AD-lord, tārā, tithi/nakṣatra quality — the only producer of day rows | M-3 + §3.8 |
| T1-10 | Mūrti as a per-residence multiplier once its rule form is verified | code cites Phaladīpikā/BPHS `[U]` |

**Tier 2 — enrichment from facts L1 already computes**

| id | change |
|---|---|
| T2-1 | Jaimini targets: DK/PK/AK, UL, A7/AL, kārakāṃśa; Chara daśā as the licence for them (`karaka_chara_position`, `upapada_lagna`, `karakamsa_position`) |
| T2-2 | Tājaka sahams as class-specific targets (Vivāha, Putra, Karma, Mṛtyu, Roga, Dhana…) and Muntha/varṣeśa as an annual licence (`saham_position`, `aspect_tajik`, `tajik_hadda_lord`) |
| T2-3 | `yoga → classes` map with citations, strength-scaled, daśā-activated (drop the overlap heuristic) |
| T2-4 | Varga-position targets (D9 for marriage, D7 children, D10 career, D4 property, D24 education) as testimony |
| T2-5 | Kaṇṭaka/aṣṭama/ardhāṣṭama Śani, dhaiyā as interval testimony on adverse classes (`kantaka_shani_period` etc.) |
| T2-6 | Eclipses on natal points with real instants (w26, H-4); stations as a real relation with orb |
| T2-7 | Argala (`argala_natal_matrix`) to qualify which transit-to-house contacts are unobstructed — Jaimini, cite by count `[U]` |
| T2-8 | KP significators and Bhṛgu-nāḍī points as served testimony only (no weight; KP not in corpus) |

**Tier 3 — make it measurable (so the GPT/Astra round and the L5 loop have something to test)**

| id | change |
|---|---|
| T3-1 | Retrodiction protocol on the LEL's 36 dated events: for each event, (a) does its class have a window within ±k days, (b) what is the window's **rank** within the class that year, (c) what is the class base rate (windows per year). A hit at rank 1 of 5 means something; a hit at rank 13 of 13 equal peaks means nothing. Report per mechanism (which relation/agent produced the peak) so doctrine can be ablated. |
| T3-2 | Discrimination metrics: peak/median ratio per class per year; cross-class correlation of window sets (today near 1.0 because the target sets overlap); fraction of peaks produced by slow-body contacts vs fast-body contacts. |
| T3-3 | Per-mechanism ablations on the real chart (M-1 orb, BAV weighting, frame fix, valence fix) reported as factor-level deltas — the A-3 instrument, run on doctrine, not just on flags. |
| T3-4 | Calibration stays at L5 (ph_pramana NO-SCORING gate stands); Gochara ships *ranked, mechanism-attributed* windows, never probabilities. |

**Sequencing note `[J]`.** Tier 0 before anything else — a calibration run on the current score would calibrate
noise. T1-1 (BAV weighting) and T1-6 (promise) are the two changes that turn a flat plateau into a ranked
landscape; T0-3/T0-4 are what let the classical triggers of §2.2 exist as contacts at all. The horizon-parity
`'4.1'` rebuild now running will inherit every Tier-0 defect; it is worth completing only as an *engineering*
proof of the full-century pipeline, not as an astrological deliverable.

---

## 5. Questions for the independent review (GPT/Astra, effort max)

1. Confirm or refute the dṛṣṭi direction finding (contacts.py:206-213) with an independent hand computation.
2. Confirm the house-frame mixing on mechanism nodes (migration 266:53-55 vs writer.py:950 vs step06:410-419).
3. Adjudicate the mūrti-nirṇaya rule form (nakṣatra mod 4 vs rāśi 1/6/11 …) against the cited chapter, by count.
4. Adjudicate the Venus vedha pairs (11→3/12→6 vs 11→6/12→3) against PG323, by count.
5. Is a weighted 12-system permission vote defensible at all, or should permission be applicability-gated
   Vimśottarī (+ Jaimini Chara for Jaimini targets) with the rest as corroboration?
6. Which BAV-bindu → weight mapping should be admitted (0–1 suppress / 4 neutral / ≥5 amplify is one
   convention; the reviewer should name the text it follows).
7. Should the century score carry a Moon-derived day tier at all, or should day rows be produced only on
   demand (M-3 strict)? §3.8 argues for "inside each month window".
8. Which classes' signature tables in §1.2 need correction (e.g. career_change with Rahu as sole kāraka;
   property_acquisition with a single negative mechanism; bereavement without 9L/Sun for the father).
9. Is the `yoga → classes` attachment worth doing, or should yogas enter only through promise?
10. Rank the Tier-1 items by expected retrodictive gain on this chart.

---

## 6. Limits of this review

- Doctrine labels: `[D]` items are ones this campaign already verified in `classical_text_chunks`; I made **no
  new presence or absence claim** against the corpus (F-32). Every `[U]` is a count someone must run.
- Chart 2's ledger was used only as a structural proxy for chart 1's deleted `'4.0'` contacts (counts differed
  by one row); no claim about chart 2's astrology is made or intended.
- I did not re-derive ṣaḍbala, bhāva-bala or aṣṭakavarga values; I relied on L1's stored facts and the
  campaign's own FORENSIC anchors.
- "Widely taught" (`[P]`) marks practice I am confident is standard in Indian Jyotiṣa teaching but for which I
  do not claim a verse; the reviewer round should either cite or leave it as `uncited_extension`.
- Nothing here changes any ruling. Where the build contradicts a ruling, the ruling stands and the build is
  the thing to fix.
