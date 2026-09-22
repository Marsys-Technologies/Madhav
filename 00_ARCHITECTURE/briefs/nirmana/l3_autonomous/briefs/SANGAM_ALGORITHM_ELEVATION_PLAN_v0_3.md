---
artifact: SANGAM_ALGORITHM_ELEVATION_PLAN
canonical_id: SANGAM_ALGORITHM_ELEVATION_PLAN
version: "0.3"
status: PROPOSAL_FOR_NATIVE_RULING      # post independent review
date: 2026-09-22
supersedes: SANGAM_ALGORITHM_ELEVATION_PLAN_v0_2.md (which incorporated the REWORK of v0.1 — ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md)
review_incorporated: ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md (Codex gpt-6-astra, xhigh, 2026-09-22) — every finding dispositioned in §0 and located in §0.1; 13 factual overturns re-verified at source and 10 reproduced as runnable scripts (evidence_sangam/)
evidence: evidence_sangam/S1…S10 + RUN_ALL.sh → OUTPUT_2026-09-22.txt (read-only; no DB; Swiss Ephemeris for S8)
asset: ka_sangam (Saṅgam — the convergence engine, L3 Kāla)
companion: SANGAM_ELEVATION_BRIEF_v1_0.md v1.2 (output contract; §0 records the amendments this plan now requires of it)
base_branch: main
governed_by:
  - CLAUDE.md §B.10, §N.5, §N.7, §N.8
  - MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §2, §3, §5 (P4 + benchmark contract), L3-U02/U07
  - CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md §4.5/§4.6/§6 (native rulings 2026-06-22)
  - l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md
does_not_authorize: any code, migration, build, L5 consumption, or doctrine. Method qualification is the native's.
evidence_tags: "[C] verified in code · [D] doctrine, verse-cited (reviewer-verified corpus: BPHS R. Santhanam ed., Phaladīpikā, Hāyanaratna) · [P] practice, weaker anchor · [J] author's judgment · [U] unverified · [R] reviewer finding, author re-verified"
---

# Saṅgam — algorithm elevation plan v0.3

**What changed from v0.1, in one paragraph.** The independent review returned REWORK, and it was
right. v0.1 proposed changing aspect theory before establishing *what natal point the scan actually
targets* — and the answer, verified at source, is that for every semantic trigger it targets **0°
Aries by default** (F-01). It built E2 around a "frame question" that `ga_strength_writer` had
already answered in its own docstring (F-03). It rested E4 on three L1 facts whose meanings it
had assumed rather than read (F-07). It stated a Moon-contact bound that simple arithmetic refutes
(F-06), a streaming-memory claim the code comment asserts but the code does not do (P:48), and a
rarity formula whose angle fraction is wrong (P:58). It called the daśā prior "necessary" when it is
a supporting current (F-08). v0.2 therefore inverts the order: **five repairs to what already exists
come before any new method**, the six elevations are re-scoped as the reviewer amended them, E4's
gate design is withdrawn, identity moves to the front, and every doctrine anchor is corrected to a
verse the reviewer located in the corpus. What survives from v0.1 is the direction — Vedic contact
contracts, revived aṣṭakavarga, a bounded fast tier, typed natal/clock conditioning, episode
grouping, measured exposure — none of it as first stated.

---

## §0 — Review disposition ledger

Every finding, with what this plan does about it. **ACCEPT** = incorporated as stated;
**ACCEPT-MOD** = incorporated with a change, reason given; **REJECT** = not incorporated, reason
given. No finding is silently dropped.

| # | Finding (short) | Disposition | Where / why |
|---|---|---|---|
| **F-01** | Semantic triggers carry no `target_longitude_deg`; scan defaults to **0° Aries** (`engine.py:1148`, `ka_sangam.py:662`; binder: 0 occurrences) | **ACCEPT — becomes R-1, blocking, first** | Nothing else in this plan is meaningful until the target is bound. Author re-verified: `grep -c target_longitude services/ka_yojaka/binder.py` → 0. |
| **F-02** | Graha-dṛṣṭi is *directed*; naïve angle substitution into `find_aspect_events` (which searches `target + angle`) reverses Mars/Saturn asymmetric aspects | **ACCEPT** | E1 now specifies directed source/target semantics and a per-aspect reverse-branch test; `transit_search.py` stays untouched — the direction logic lives in a Saṅgam-side adapter that computes the search angle. |
| **F-03** | Frame question already answered: `ga_strength_writer.py:970-979, 1028-1036` writes sign-keyed `ashtakavarga_bindu_sign` `-SIGN_N` from the same rāśi-indexed array, plus śodhana grids and kakṣyā boundaries; the proposed lagna experiment is invalid (lagna is itself a BAV contributor) | **ACCEPT — E2 simplified** | E2 no longer adjudicates a frame; it reads the correct category. Author re-verified at the cited lines. |
| **F-04** | E2's proposal (SAV≥28 ∧ BAV≥4) and its own falsifier (SAV26/BAV6 must pass) contradict; `BAV/8` in a nonnegative combiner makes BAV2 *positive* | **ACCEPT** | Conjunction dropped; BAV is a *signed* verdict (support / indeterminate / obstruct), evaluated on every ingress, recorded not filtered. |
| **F-05** | Kakṣyā needs the per-contributor matrix, which the adapter obtains and discards (`strength.py:216`); not "zero geometry" | **ACCEPT** | Kakṣyā deferred to a bounded L1 amendment (expose `_prastara` with lineage) and costed; not in this plan's first pass. |
| **F-06** | Moon bound ⌈d/27.3⌉+1 is false: conj+opp alone give 5 in 60 d, 7 in 90 d; multiple targets/families multiply | **ACCEPT** | E3 bounds *scope*, not count: enumerate all authorised families within declared parents; report incomplete rather than cap. |
| **F-07** | `sandhi_flag` = duration < 20 days (`ga_dashas_writer.py:1062`); capability is a serving-layer aggregation, not a stored floor; `chart_divisionals` exists but supplies no universal gate | **ACCEPT** | E4's three "facts" restated with their real meanings; sandhi becomes a boundary-distance *annotation* from `start_iso/end_iso`, no multiplier. |
| **F-08** | Adverse evidence ≠ inapplicability; a debilitated lord still operates (BPHS 47.2-4); Mode A's daśā term is *supporting* (`engine.py:1221-1223`), not necessary | **ACCEPT — E4 gate design withdrawn** | Replaced by typed, signed, domain-specific conditions per the reviewer's alternative. Author re-verified `necessary = [dignity_score, orb_s, vedha_factor]`. |
| **F-09** | Row grouping is not an ICC repair; ICC counts currents within a row, not episodes across rows | **ACCEPT** | E5 drops the "3→1 independence fix" claim; states the real defect (downstream row counts overstate activity) and tests the aggregator. |
| **F-10** | First-to-last hull fabricates activity in gaps and loses shoulders; `ka_taranga:161-169` spreads score over every month of the stored interval | **ACCEPT** | E5 emits an episode with **child contact intervals**; hull only as a labelled search envelope. Author re-verified taranga's month loop. |
| **F-11** | Counted geometric recurrence ≠ event base rate; current sweep is capped/selected, not an unbiased denominator | **ACCEPT** | E6 renamed: `modelled_contact_frequency` with exposure/coverage/censoring fields; never "rarity" as prediction evidence. |
| **F-12** | Model invalidation ≠ outcome miss; a `peak_date` key is unstable under algorithm change; identity must precede E1–E5 | **ACCEPT — moves to R-5, before all E's** | Companion brief §5.3 keys must be amended (see §7). |
| **F-13** | Multi-clock overlap groups on exact `(start,end)` (`service.py:76-78`); Strategy §U02 requires intersection; failed eligibility falls to static 0.5 prior | **ACCEPT — becomes R-2** | Author re-verified. This is a defect in a current the plan proposed to *extend*. |
| **F-14** | Scanner hardcodes Lahiri + true node (`transit_search.py:9-10, 64, 245`); predicates carry ayanāṃśa; dedup key omits planet/angle/target/ayanāṃśa | **ACCEPT — becomes R-3** | Frame/ayanāṃśa/node context is a prerequisite, not metadata polish. |
| **F-15** | A/B shoulders are fixed ±15 d; C/D ends are period averages; tangencies/edge occupancy not detected | **ACCEPT — becomes R-4** | "Ingress-bounded" claim withdrawn until both ends are actually known. |
| **F-16** | C8 ignores its target; benefic dṛṣṭi uses generic weights; C11 same attenuation regardless of proposition; first constituent lord stands in for domain lord | **ACCEPT — folded into R-4** | Polarity/relevance audit of existing currents precedes adding new ones. |
| **F-17** | Companion's superset test is a regression check, not proof of the full applicable set; downstream 500/750/100 must not define the rarity population | **ACCEPT** | §6 evidence spec separates "applicable universe" from "selected/served". |
| **F-18** | `query_convergence_windows.ts` selects scalars + `constituent_factors` only; nesting new fields in JSONB is not served reasoning | **ACCEPT** | Served-contract change is an explicit L3-U04/U11 packet with a sentinel; not assumed. |
| **F-19** | Stable identity must survive the real cascade; Bhaviṣya fails closed on ambiguous reattachment | **ACCEPT** | Part of R-5; generation-aware dependent map required before any rebuild. |
| **A-01** | "Already right" list is not an acceptance baseline: I-17's cos² / 0.7 penalty lack classical authority; C11 conflates unavailable with no-obstruction | **ACCEPT-MOD** | Kept as *preserved engineering* (transaction safety, fail-loud context); method correctness of I-17/C11 moved to R-4's requalification. Mod: the resume ledger and SAVEPOINT pattern are retained unconditionally — they are not method claims. |
| **A-02** | Bindu/rekha convention differs by edition (Santhanam: bindus adverse); repo adapter computes benefic counts | **ACCEPT** | Doctrine ledger records the edition convention → stored-value mapping; no inversion. |
| A.3 doctrine | Phaladīpikā aṣṭakavarga is **ch. 23** not 26; BPHS SAV bands 72.3-5 are >30/25-30/<25; Jupiter 90° has *fractional* standing (BPHS 26.2-5); Tājika 60°/90° legitimate (Hāyanaratna 2.1); node 5th/9th `[U]`; sandhi "last portion" defeated by BPHS 47.3-4 (drekkāṇa order, reversed for retrogression) | **ACCEPT** | All anchors corrected in §3; "no classical basis for 60°/90°" withdrawn. |
| C.2 techniques | Chara/Jaimini, Yoginī, Kālacakra: rule in via existing clocks after R-2; Tājika ahead of a generic fast tier; Sudarśana as reuse; Praśna out of unattended sweep; argalā from its producer; bhāva-madhya a mandatory context decision; Rāhu/Ketu under node convention | **ACCEPT** | §5. |
| D.1 sequence | Reviewer's seven-step order | **ACCEPT** | §4 adopts it verbatim in structure. |
| P:410 | "Only E3 touches a standing ruling" is false — E1's new geometry also touches §4.5's no-scan direction | **ACCEPT** | M-3 broadened to an *integrated* June-ruling reconciliation. |
| — | Reviewer's "predictive improvement UNVERIFIABLE" throughout | **ACCEPT, and it is the point** | This plan makes windows *testable*; it does not claim they will test well. |

### §0.1 Verification pass — every finding located, and what reproduces it

Added in v0.3 at the native's request ("ensure everything has been addressed"). Each row names
the v0.3 section where the disposition is *applied* (not merely listed) and the runnable evidence,
where one exists. `SPEC` = a falsifier that can only run after the repair/elevation is built; its
fixture is specified in §3b.

| Finding | Applied at | Runnable evidence (evidence_sangam/) |
|---|---|---|
| F-01 | §3 R-1; §1b row 1; §3b E1 | **S1** — binder emits 0 `target_longitude`; engine/writer default `0.0` at `:1148`, `:1377`, `:662` |
| F-02 | §3 E1 (directed contracts); §3b E1 | **S2** — Mars/Saturn naive vs directed search sets differ; Jupiter's mirror pair hides it |
| F-03 | §3 E2; §1b row 6 | **S3** — L1 writes `-SIGN_N`; writer reads legacy category at `:1004`; Capricorn-lagna synthetic returns wrong bindus, Aries hides it |
| F-04 | §3 E2 (signed verdict, no conjunction); §3b E2 | SPEC (post-E2): SAV30/BAV2 → obstruct; SAV26/BAV6 → support |
| F-05 | §3 E2 (kakṣyā deferred to L1 amendment) | — (source: `strength.py:216` discards `_prastara`) |
| F-06 | §3 E3 (scope not count); §3b E3 | **S4** — 5 contacts in 60 d, 7 in 90 d vs claimed ≤4/≤5 |
| F-07 | §3 E4 (boundary_distance from `start_iso/end_iso`); §1b row 9 | **S9** — `sandhi_flag = duration_days < 20` |
| F-08 | §3 E4 (gates withdrawn); §3b E4 | **S10** — `necessary = [dignity, orb, vedha]`; daśā is supporting |
| F-09 | §3 E5 (claim withdrawn; aggregator test) | SPEC (post-E5): `ka_taranga` months == union of child intervals |
| F-10 | §3 E5 (episode + children; hull = envelope) ; §3b E5 | **S8** — oracle points inside/outside three Saturn loops incl. the 0°-wrapping 2027 loop |
| F-11 | §3 E6 (`modelled_contact_frequency`, exposure fields); §3b E6 | **S5** — `_rarity_years('Saturn',180)` = 14.73 vs 29.46 |
| F-12 | §3 R-5; §7 item 1 | SPEC (post-R-5): peak shift of one day must not orphan an attached outcome |
| F-13 | §3 R-2; §1b row 10 | **S6** — 305-day overlap, keys differ |
| F-14 | §3 R-3; §1b rows 3, 11 | — (source: `transit_search.py:9-10, 64, 245`; dedup key `ka_sangam.py:883`) |
| F-15 | §3 R-4; §1 baseline rows Mode C/D, shoulders | — (source: `engine.py:1621-1635, 1756, 1186-1187`) |
| F-16 | §3 R-4 | — (source: `engine.py:141-186, 442-482, 1221, 1100-1103`) |
| F-17 | §6 (applicable ≠ selected ≠ served); §7 item 3 | — |
| F-18 | §6 served-contract packet | — (source: `query_convergence_windows.ts:90-129`) |
| F-19 | §3 R-5; §6 preservation spec; §7 item 2 | SPEC: cascade invariants on the disposable harness |
| A-01 | §1 "preserved unconditionally" narrowed to engineering; R-4 requalifies I-17/C11 | **S7** — gate filters after full accumulation (comment claim false) |
| A-02 | §3 E2 (edition ledger) | — |
| A.3 doctrine | §3 E1/E2/E4/E5 anchors; §9 item 3 | — (reviewer corpus refs carried verbatim) |
| C.1 F-13…F-16 | Stage R | S6, S7 |
| C.2 techniques | §5 | — |
| D.1 sequence | §4 | — |
| D.2 P4 | §6; §3 each E's "no runtime claim" | S7 (the one claimed saving refuted) |
| D.3 lineage | §4 last paragraph; §3 each E | — |
| E.1 consumers | §6 consumer obligations | — |
| E.2 served | §6 (L3-U04/U11 packet; `explain.ts` non-consumption disclosed) | — |
| E.3 rebuild truth | §3 R-5; §6 preservation spec | SPEC |
| F verdict — 3 changes | (1) R-1…R-4 + E4 replacement · (2) §6 evidence spec, no speed claims · (3) R-5 first, §7 companion amendments | — |

**Where the author holds a different emphasis (not a rejection):** the reviewer treats the six
E's as premature until R-1…R-5 land. Agreed for *implementation*. For *ruling*, the native can
usefully decide the method questions (M-1, M-2, M-3) now, in parallel with the repairs — because
R-1 (which point is the target) is itself a method question. §4 marks which decisions are
independent of the repairs.

---

## §1 — Baseline, corrected (what the engine does today) [C]

| Component | Verified behaviour | Where |
|---|---|---|
| Mode A | daśā *soft prior* as a **supporting** current `constituent_lord_transit`; necessary = dignity × orb × vedha; failed/empty eligibility falls back to static 0.5 | `engine.py:1117-1142, 1221-1223` |
| Mode B | same scan + magnitude threshold, no daśā gate | `:1332-1544, :1400-1404` |
| Mode C | starts at real ingress, **ends at ingress + mean period/12** (estimated, not actual egress) | `:1621-1635` |
| Mode D | SAV ≥ 28 for Jupiter/Saturn/Mars; end estimated; inherits the *first predicate's* signal id and domain | `:1673-1683, :1723-1725, :1756`; `ka_sangam.py:721-737` |
| **Target** | `transit_trigger_jsonb.target_longitude_deg` **absent from every semantic trigger the binder builds** → defaults to **0.0° (Aries)** | `engine.py:1148`; `ka_sangam.py:662`; `binder.py` (0 hits) |
| Contact model | `find_aspect_events(target + angle)`, angles `[0,60,90,120,180]`, orb 5°; zero-crossing detection; unsigned angles, one branch | `transit_search.py:320, 331` |
| Planet | per-signature (§4.6 landed); **DIGNITY/DISPOSITOR can resolve Moon, Sun, Mercury** — no slow allowlist | `engine.py:992-1015` |
| Gate | threshold 0.45 applied **after** `find_aspect_events` returns the full accumulated list | `transit_search.py:351-371`; `engine.py:1154, 1171` |
| C11 vedha | **dampener 0.3**, not a veto; missing data → 1.0 (optimistic) | `:282-297` |
| C7 aṣṭakavarga | returns `None` on the usable path; reads only legacy `-HOUSE_N` category, Lahiri hardcoded, no fact ids | `:103-140`; `ka_sangam.py:1001-1024` |
| C8 eclipse | its target longitude is unused | `:141-186` |
| C12 tājika | domain lord vs year/Munthā lord → 1/0.5/0; checks window *start* only, inclusive | `:648-691`; `ka_sangam.py:1111-1115` |
| C13 | never populated | `ka_sangam.py:989` |
| Cross-daśā agreement | groups intervals on **exact `(start_date, end_date)`** — overlap without equal endpoints never agrees | `ka_dasha_kala/service.py:76-78, 194-212` |
| Daśā depth / interval | `max_level=3` (service defaults 4); closed-closed at `:1140` | `:1124, :1140` |
| Frame | scanner: Lahiri + true node hardcoded; predicates carry `ayanamsha_id`; no ayanāṃśa on output; dedup key omits planet/angle/target/ayanāṃśa | `transit_search.py:9-10, 64, 245`; `ka_sangam.py:276, 883` |
| Shoulders | A/B: peak ± 15 days fixed | `:1186-1187, :1412-1413` |
| Rarity | `period × angle/360`, clamped — and the angle fraction is wrong (a fixed target's opposition recurs once per revolution, not twice) | `:971-989` |
| L1 facts unread | `ashtakavarga_bindu_sign` (correct frame), śodhana grids, kakṣyā boundaries (`ga_strength_writer.py:1028-1036, 1071-1083`); `start_iso/end_iso` on clocks (`ga_dashas_writer.py:1042-1050`); `chart_divisionals` (`ga_vargas_writer.py`) | grep, this session |

**Preserved unconditionally (engineering, not method):** per-substep self-scoped delete; resume
ledger; SAVEPOINT-guarded soft reads; fail-loud birth context (CR-87); house-from-Moon vedha frame
(CR-102); D-3 per-class quota selector; honest-empty `_current_stance`.

---

### §1b — Inputs consumed: source contract (what the plan requires of each)

Astra's closing requirement: *"complete source contracts for the inputs it consumes."* Each row:
producer, exact column/category, frame, grain, null semantics **as they are today**, and what this
plan requires. [C] unless marked.

| # | Input | Producer / read site | Frame & grain today | Null / default today | Plan requires |
|---|---|---|---|---|---|
| 1 | `transit_trigger_jsonb` (type, trigger_events, rules, veto) | `ka_yojaka/binder.py:39-131,231-238` → `ka_sangam.py:277,298` | rule spec; **no target** | `target_longitude_deg` absent → `0.0` | R-1: `target_fact_id`, `target_type`, `frame`, `ayanamsha_id`, `derivation`; unresolvable → `unavailable` |
| 2 | `dasha_eligibility_rule_jsonb` (constituent_lords, eligibility_score) | binder → `ka_sangam.py:277` | full lord set used for the daśā query (`engine.py:1113`) | `eligibility_score` default 0.5 on failed/empty service result (`:1131-1142`) | R-2: failure → `unavailable`, never 0.5 |
| 3 | `ayanamsha_id` on predicate | `ka_sangam.py:276` | carried in; **not** passed to scanner; not stored | `or 'lahiri'` at `engine.py:1097` | R-3: flows to scan and row; part of dedup key |
| 4 | `bodha_msr_signals.domains_affected_array`, `dignity_score`, graha, house | `ka_sangam.py:337-353` | per signal | `[0]` only (`:353`); dignity NULL → 0.5 in rank key (`:348,:360`) | companion §3.4 (`domains[]`); dignity NULL → excluded from rank, reported |
| 5 | `chart_facts` Moon nakṣatra/sign, Lagna sign | `ka_sangam.py:758-762, 1150-1156` | `fact_key='sign' LIMIT 1` no `ORDER BY` (`:1154`) | — | total `ORDER BY` (§N.7 item 2) |
| 6 | `chart_facts` aṣṭakavarga | `ka_sangam.py:991-1024` reads `fact_category='ashtakavarga_bindu'` (legacy `-HOUSE_N`, actually rāśi-indexed); L1 also writes `ashtakavarga_bindu_sign` `-SIGN_N`, śodhana grids, `ashtakavarga_kakshya_boundary` (`ga_strength_writer.py:1028-1036, 1071-1083`) | rāśi; Lahiri hardcoded (`:1005`); no fact ids | null → 0 (`:1021`); missing planet → twelve zeros (`ga_strength:1026`) | E2: read `_sign` category with fact ids and predicate ayanāṃśa; distinguish measured zero / null / missing planet; edition convention per A-02 |
| 7 | `public.charts` lat/lng/tz | `ka_sangam.py:832-838` | tz offset at **run time** (`:854`) | fail-loud if missing (CR-87) | companion §4.8: offset at birth instant |
| 8 | `chart_dashas` MIN(start_date) level 1 | `ka_sangam.py:869-874` | birth-year derivation | — | unchanged |
| 9 | L1 clock intervals (`start_iso/end_iso`, `sandhi_flag`) | `ga_dashas_writer.py:1042-1062` — **not read** by Saṅgam; consumed via `KaDashaKalaService` at date grain | `sandhi_flag` = duration < 20 d | — | E4(1): `boundary_distance` from `start_iso/end_iso`; `sandhi_flag` not used as junction |
| 10 | `KaDashaKalaService.query(target_lords, max_level=3)` | `engine.py:1113-1126`; service `:76-78` groups by exact `(start,end)` | multi-clock; date grain; closed-closed test `:1140` | failed → static prior | R-2: interval intersection; declared boundary convention; `max_level` declared |
| 11 | `KaGocharaService(swe)` / `find_aspect_events` | `ka_sangam.py:317-320`; `engine.py:1087`; `transit_search.py:242-272, 312-371` | Lahiri + true node **hardcoded**; unsigned `target + angle`; full list then filter | — | R-3 frame from predicate (adapter-side; scanner untouched); E1 directed semantics; R-4 real interval ends |
| 12 | `kala_vedha_gochara` | `ka_sangam.py:1055-1073` (SAVEPOINT) — **undeclared edge** | precomputed windows; house-from-Moon | missing → 1.0 (`engine.py:282-297`) | companion §5.4 declare; R-4: missing → `unavailable` |
| 13 | `l1_tajik_varsha_year_lords` | `ka_sangam.py:1098-1120` (SAVEPOINT) | year/Munthā lord; window start only, inclusive (`engine.py:675-690`) | — | §5 Tājika: real annual judgment, coverage split at annual boundary |
| 14 | `convergence_scores` (C13) | never queried (`ka_sangam.py:989`) | — | always absent | remove from any denominator (companion §4) |
| 15 | `chart_divisionals` | `ga_vargas_writer.py` — **not read** | natal varga positions | — | E4(3): natal dignity in domain varga, declared natal |
| 16 | daśā-lord capability | `get_dasha_lord_capability.ts:6-33, 174-204` — serving-layer aggregation, **not an L1 column** | Vimśottarī MD lords; averaged varga ratification | — | E4(2): *cite* as evidence; do not reuse as a floor; avoid double-counting its varga average |

## §2 — Constraints (inherited; one corrected)

Unchanged from v0.1 items 2–8 (P4; U02; §N.5/B.10; `transit_search.py` untouchable; no confidence
scalar; companion contract first; method is the native's). **Corrected item 1:** the June artifact
contains *competing* directions — §4.5/§6 (slow only, no Saṅgam scan) and §4.6 (Moon/Mercury
scans qualified by the inline gate; no hard caps). The landed code follows §4.6 and already
resolves fast planets. **Both E1 and E3 touch this**; neither proceeds without the integrated
ruling in M-3.

---

## §3 — The plan: five repairs, then six elevations

### Stage R — Repairs to what exists (blocking; before any new method)

| # | Repair | What it fixes | Falsifier |
|---|---|---|---|
| **R-1 Target binding** | Every predicate's transit trigger carries `target_fact_id`, `target_type` (natal graha / bhāva-madhya / sign / point), `frame`, `ayanamsha_id`, `derivation`. Unresolvable → `method_states.transit = unavailable`; **never 0°**. Relational/house triggers may need a different detector, declared. Bhāva-madhya vs whole-sign is decided *here* (mandatory context, per C.2). | F-01 | A DIGNITY predicate for natal Saturn at 200° must scan 200°, not 0°; a predicate with no resolvable target must yield no contact rows and an `unavailable` state. |
| **R-2 Clock intersection** | `_build_overlap_key` → interval *intersection* with parent hierarchy (Strategy U02); failed/empty eligibility → `unavailable`/`inapplicable`, never the 0.5 static prior; `max_level` declared (3 vs service default 4) with reason. | F-13, P:42 | Two clocks overlapping by 30 days with different endpoints must register agreement; a service failure must not produce a 0.5-scored row. |
| **R-3 Frame provenance** | Ayanāṃśa and node convention flow from the predicate into the scan (adapter-side; `transit_search.py` unchanged — if it cannot accept them, that is a bounded amendment to raise, not an edit); `ayanamsha_id` on the row; dedup key = (planet, angle, target, frame, ayanāṃśa, date). | F-14 | Two builds under different ayanāṃśas produce distinguishable rows; a Lahiri predicate and a Raman predicate never dedup together. |
| **R-4 Detector + current audit** | Real interval ends for C/D (actual egress, not period average); measured shoulders for A/B (orb entry/exit), not ±15 d; tangency/near-station and horizon-edge occupancy detected; C8 uses its target; C11 applies to the proposition it qualifies, with `unavailable` ≠ 1.0; I-17's cos²/0.7 requalified or labelled `[P]`; domain lord resolved per domain, not `constituent_lords[0]`. | F-15, F-16, A-01 | A contact active at horizon start is reported; a window with no vedha *data* reads `unavailable`, not "no vedha". |
| **R-5 Identity + outcome attachment** | Stable contact/episode identity independent of `peak_date`; split/merge/supersession relations; immutable prediction+outcome records; generation-aware dependent map across the real cascade (403/245/247/249/363). **Amends the companion's §5.3 keys.** | F-12, F-19 | An algorithm change that moves a peak by one day must not orphan an attached outcome; Bhaviṣya's fail-closed check must find its record. |

### Stage E — Elevations (re-scoped)

**E1 — Method-specific contact contracts** (AMEND). Not one enum; four versioned contracts, each
with its own interval rule, intensity rule, and school: (a) **Moon-relative gochara + vedha**
(Phaladīpikā 26.1-8 [D]); (b) **Parāśari graha-dṛṣṭi** — full 7th; Mars 4/8, Jupiter 5/9, Saturn
3/10 full; **fractional** ¼/½/¾ for the others incl. Jupiter's 4th (BPHS 26.2-5, Santhanam
BP1:16485-16505 [D]) — *directed*: the search angle is derived from the aspecting graha's own
position, with every special aspect and reverse branch tested (F-02); degree strength per BPHS
26.6-8, not a universal cos² (A-01); (c) **Jaimini rāśi-dṛṣṭi** where a Jaimini route needs it
(BPHS 8.1-5 [D]); (d) **Tājika** aspects incl. 60°/90° with their own orbs and itthaśāla motion
rule (Hāyanaratna 2.1, 3.3 [D]) — *withdrawn claim:* "60°/90° have no classical basis." The
present Ptolemaic scan is labelled `legacy_unsigned_angles` and retained one generation. Sign
applicability with degree annotation is a **declared hybrid**: the interval survives when no
exact pass occurs; occupation is its own condition. **Oracle:** directed Mars/Saturn cases,
non-Aries frames, Jupiter fractional 4th, a separate Tājika square, wraparound, sign-eligible
without exact perfection — replaces v0.1's invalid single example. **M-1** rules school and scope.

**E2 — Aṣṭakavarga from the correct facts, signed** (AMEND). Read `ashtakavarga_bindu_sign` (the
sign-keyed category L1 already writes), with fact ids and the predicate's ayanāṃśa; C7 := the
transiting planet's own BAV → a **signed verdict** `support / indeterminate / obstruct` with the
threshold *attributed* (edition convention recorded per A-02; ≥4/≤3 is a practice convention
`[P]` until the native adjudicates equality and the Phaladīpikā 23.11 reading). SAV bands per
BPHS 72.3-5 (>30 / 25-30 / <25) or Phaladīpikā 23.20 (>28) — **both retained, school-labelled**,
never averaged; SAV and BAV are not two votes (SAV contains BAV). Mode D evaluates **every**
ingress and records a verdict; no SAV prefilter (F-04, D.2). Kakṣyā: deferred to an L1
amendment exposing the contributor matrix (F-05). Missing-planet zeros (`ga_strength:1026`) and
null→0 (`ka_sangam.py:1021`) distinguished from measured zero. **M-2** rules thresholds/edition.

**E3 — Fast-tier refinement inside selected parents, complete within declared scope** (AMEND,
gated on M-3). Moon/Sun contacts and tāra bala as *conditioning* witnesses (Phaladīpikā 26.2, 12
[D]; tāra 3/5/7 `[P]`), computed only inside parent windows, **all authorised families enumerated,
no count cap** (F-06); resource limit → `refinement: incomplete`, resumable, never "complete".
Sub-peaks are structurally subordinate but carry their own geometry source and precision;
lineage = *conditional refinement selected through the parent* (not "same origin"); evidence count
does not increment. Sarvatobhadra/laṭṭā: **reuse** the existing vedha producer already served by
`kala_views/now.ts:556-607`, not a new engine. Tājika annual (C12 made a real annual judgment) is
ruled **ahead** of this tier for annual questions (C.2). **Non-claim:** a dated Moon contact is
not a dated life event.

**E4 — Typed natal and clock conditioning** (v0.1 gates REJECTED; replacement). Three *signed,
domain-specific conditions* attached to `route`, none a gate, none a multiplier:
(1) `boundary_distance` — days from the peak to the nearest constituent-lord period boundary at
any level, from `start_iso/end_iso` (not `sandhi_flag`); **annotation only** until a rule is
adjudicated — BPHS 47.3-4 orders beginning/middle/end by drekkāṇa and reverses for retrogression,
defeating any universal "last-portion" amplifier [D]; (2) `lord_condition` — sourced strength,
functional role, dignity, house/lordship of each running lord (BPHS 47.2-4 [D]) as *signed
promise/denial*, never inapplicability: a debilitated lord delivers adverse or weak results, it
does not stop operating (F-08); the serving-layer capability aggregation is cited, not reused as
a floor; (3) `varga_condition` — natal dignity of the relevant lords in the domain's varga (BPHS
7.1-8: D7 progeny, D9 spouse, D10 position, D4 fortunes [D]), *natal* explicitly (not a transit
D10), with cancellation evidence, and with the capability aggregation's own varga average not
double-counted. **M-4** rules the varga–domain table and whether any condition may ever veto.

**E5 — Episodes with child contacts** (AMEND). When ≥2 contacts of one (graha, target, directed
angle, frame, method) are linked by a station loop, emit one **episode** with **child contact
intervals** (each with its own orb entry/peak/exit and identity), a hull only as a labelled
envelope, membership from geometry and chronology, **no default peak phase** — cheṣṭā-bala (BPHS
27.21-25 [D]) is a strength condition, not an event date; ties retained. Horizon-truncated
episodes and >3 contacts supported. Old-contact→episode mappings published before any cascade.
*Withdrawn:* "three→one independence fix" (F-09) — the real defect is downstream row-count
overstatement, tested at the aggregators (`ka_taranga` months, `ka_jivana_parva` counts). **M-5**
rules episode boundary conventions.

**E6 — Modelled contact frequency, and a real outcome loop** (AMEND). `rarity_years` retired as a
name. New: `modelled_contact_frequency` = qualified episodes ÷ **complete, versioned exposure**
(horizon, coverage complete/incomplete, censoring, counting unit, method version), computed over
the *full applicable universe* — never over the capped/selected sweep (F-11, F-17). Zero exposure
→ unavailable. Separately: **prediction outcomes** — frozen claim (domain, event definition,
polarity, tolerance, eligibility, version) → outcome ∈ {hit, miss, model-invalidated, ambiguous,
censored, unobserved}; derivation invalidation ≠ miss (F-12). Retrospective vs prospective
evaluation separated; no accuracy claim without held-out/predeclared evaluation. **M-6** rules
when L5 may consume.

---

### §3b — Falsifier per elevation (data source · detector · status)

Astra: *"valid falsifiers for every E."* v0.2 kept only E1's. Each falsifier below names the input
that would make the claim fail, **where the data comes from** (arithmetic · synthetic chart · Swiss
Ephemeris · read-only DB aggregate), the detector, and whether it runs today (**RUN**, script in
`evidence_sangam/`) or after the change (**SPEC**, fixture stated).

| E | Falsifier | Data source | Detector that returns false | Status |
|---|---|---|---|---|
| **R-1** | A DIGNITY predicate for natal Saturn at 200° must scan 200°; a predicate with no resolvable target yields no contact and `unavailable` | synthetic predicate; source | scanned longitude ≠ target, or a row with a 0° target exists | **RUN** S1 (today's default) · SPEC (post-R-1) |
| **R-2** | Two clocks overlapping 305 d with different endpoints must agree; a service failure must not yield a 0.5 row | synthetic intervals | `_build_overlap_key` equality; any row with static-prior provenance | **RUN** S6 · SPEC |
| **R-3** | Lahiri vs Raman builds produce distinguishable rows and never dedup together | synthetic predicates, two ayanāṃśas | dedup collision across ayanāṃśa | SPEC |
| **R-4** | A contact active at horizon start is reported; a window with no vedha *data* reads `unavailable` not 1.0 | Swiss Ephemeris (edge occupancy); synthetic missing-vedha | edge contact missing; `vedha_factor == 1.0` with no data | **RUN** S7 (gate) · SPEC |
| **R-5** | Move a peak by one day via algorithm change; attached outcome must remain bound | disposable DB harness | orphaned outcome; Bhaviṣya fail-closed trips | SPEC |
| **E1** | (a) Mars 4th onto target 90°: search must be at 0° not 180°; Saturn 3rd/10th likewise; Jupiter 5th/9th shows *no* difference (so it is the wrong test case) · (b) non-Aries synthetic: sign-based dṛṣṭi interval survives with no exact pass · (c) a Tājika 90° contact is emitted under the Tājika contract and never under Parāśari · (d) 359°→1° wraparound | arithmetic (a); synthetic charts + Swiss Ephemeris (b–d) | search longitude equals naive `target+angle` for an asymmetric aspect; interval dropped for lack of exact pass; Tājika row labelled Parāśari | **RUN** S2 (a) · SPEC (b–d) |
| **E2** | (a) writer reads `ashtakavarga_bindu_sign`, not legacy · (b) Capricorn-lagna synthetic: Aries transit must read Aries bindus (4), not Capricorn's (2) · (c) SAV30/BAV2 → `obstruct`; SAV26/BAV6 → `support`; BAV4 → the ledger's equality ruling · (d) null bindu ≠ measured 0 ≠ missing planet | source (a); synthetic chart_facts rows (b–d) | category read is legacy; house-keyed value returned; BAV2 contributes positively; null coerced to 0 | **RUN** S3 (a, b) · SPEC (c, d) |
| **E3** | (a) 60-day parent: enumerated Moon conj/opp contacts must equal the ephemeris count (5), never a capped count · (b) resource limit → `refinement: incomplete`, resumable · (c) a parent with no Moon contact → `sub_peaks: []`, not a parent-date default · (d) evidence count unchanged by sub-peaks | arithmetic (a-bound); Swiss Ephemeris (a-count); synthetic (b–d) | count < ephemeris count with `complete`; default date; group count increments | **RUN** S4 (bound) · SPEC |
| **E4** | Two windows identical in geometry, one lord exalted in D10, one debilitated: **must differ** for a career question and **must be identical** for a health question; the debilitated case still produces a row with a *signed* condition, never `inapplicable` | synthetic charts with synthetic `chart_divisionals` | health ranking changes; debilitated row missing or `inapplicable`; any multiplier applied from `boundary_distance` | SPEC |
| **E5** | Saturn 2026 loop: natal point 347.11° → **one episode, three child contacts**; control 352.52° → one contact, **not grouped**; same for 2027 (0.20°/5.63°, wraps 0°) and 2028 (13.60°/19.05°); `ka_taranga` months == union of children, not hull | Swiss Ephemeris (points constructed by S8); synthetic natal point | 3 rows instead of 1 episode; control grouped; a month inside the hull gap counted active | **RUN** S8 (oracle) · SPEC (engine) |
| **E6** | (a) `_rarity_years('Saturn',180)` must not be half the period · (b) a 30-year-scanned chart reports `coverage: incomplete`, never a lifetime rate · (c) zero exposure → `unavailable` · (d) the frequency never appears as a witness for the windows that produced it | real function (a); synthetic versioned sweep (b–d) | 14.73 returned; a rate emitted over partial exposure; frequency inside `independence_groups` | **RUN** S5 (a) · SPEC |

**Fixture policy:** synthetic charts are non-persons; the two production charts are both Aries
lagna and therefore *cannot* falsify any house/sign-frame claim (S3) — every frame falsifier
uses a non-Aries synthetic. Swiss Ephemeris is the independent referee for every geometric claim;
Saṅgam's own output is never the oracle for a claim about Saṅgam. Read-only DB aggregates are used
only for incidence ("how many predicates carry no target"), never for correctness.

## §4 — Sequence (reviewer's D.1, adopted) and what can be ruled now

| Step | Content | Native decisions independent of prior steps |
|---|---|---|
| 1 | Companion amendments: keys (episode/contact identity), split/merge lineage, cascade map; integrated June-ruling reconciliation | **M-3** (fast tier + new geometry vs §4.5/§4.6), **M-1a** (bhāva-madhya vs whole-sign per rule) |
| 2 | R-1…R-4: target binding, clock intersection, frame provenance, detector/current audit; baseline established | **M-2** (edition/threshold ledger) |
| 3 | E1 contracts + E2 signed aṣṭakavarga; semantic acceptance separate from reuse; all applicable predicates qualified | **M-1** (schools in scope) |
| 4 | E5 episodes on the now-defined events; consumer mappings retained | **M-5** |
| 5 | E4 typed conditions, domain-specific, after existing promise/denial and annual evidence understood | **M-4** |
| 6 | E3 only after M-3 and a full-coverage cost experiment | — |
| 7 | E6 frequency on versioned exposure; outcome evaluation under its own authority | **M-6** |

Independence bookkeeping per E (D.3, adopted): each declares roots; two views of one contact are
method views, not two witnesses; BAV/SAV/kakṣyā are one lineage; the fast tier increments nothing;
E6's frequency never returns as a vote for the windows that produced it. **No statistical
independence is claimed anywhere in this plan.**

---

## §5 — Techniques ruled in / out (C.2, adopted)

| Technique | Ruling |
|---|---|
| Chara/Jaimini daśā + rāśi-dṛṣṭi | In, as a separately qualified route after R-2; not a global substitute |
| Yoginī, Kālacakra | In, via the existing clock service after R-2; school/birth-input qualification for Kālacakra (savya/apasavya, deha/jīva) |
| Tājika varṣa-praveśa | In, **ahead of E3** for annual questions; C12 becomes a real annual judgment |
| Sudarśana cakra | In as reuse/audit of the served producer; three chart perspectives ≠ three origins |
| Praśna | **Out** of the unattended lifetime sweep; in only for a separately authorised inquiry |
| Argalā/virodhārgalā | In, consumed from its producer for a Jaimini route; not a positive current |
| Rāhu/Ketu transits | In under an explicit node convention and named rules; no fabricated node BAV |

---

## §6 — Executable evidence specification (D.2, adopted)

**What runs today** — `evidence_sangam/RUN_ALL.sh` (read-only; no DB; venv python with Swiss
Ephemeris) executes S1–S10 and writes `OUTPUT_<date>.txt`. Current output
(`OUTPUT_2026-09-22.txt`): ten VERDICT lines, all CONFIRMED, reproducing F-01, F-02, F-03, F-06,
F-07, F-08, F-13, P:48, P:58 and constructing E5's oracle. A reviewer re-runs it in under a
minute; if any script's verdict flips after a change, the corresponding row in §0.1 is reopened.

**What runs after each change** — the SPEC rows of §3b, each with a stated fixture. They are
added to `RUN_ALL.sh` as they become runnable; a SPEC that cannot be made runnable at its step is
a blocker for that step, not a note.

**Downstream preservation (F-19, E.3)** — on the disposable harness only, before and after a
Saṅgam rebuild with L4 *not* rebuilt: (i) `count(*)` per dependent table (`kala_obstruction`,
`kala_darshana`, `kala_bhavishya`, `phala_anchors`, `phala_suddha_sodhana`, `phala_muhurta`,
`phala_mitigation`, `phala_phaladesa`) unchanged; (ii) `md5(string_agg(outcome_content))` over
outcome-bearing Bhaviṣya rows unchanged; (iii) zero rows where `phala_phaladesa.top_anchor_id`
no longer resolves; (iv) every pre-rebuild contact/episode id maps to exactly one post-rebuild id
or to an explicit supersession record. Any failure = the rebuild is not authorised on a chart with
L4 rows (companion §5.2).

Applicable universe ≠ selected ≠ served: each E states all three. Oracle: the ≤20 native-ruled
canonical windows are a *seed*; add synthetic non-Aries and multi-ayanāṃśa contexts, every
directed aspect branch and node convention, BAV equality/null/vocabulary/contributor cases,
simultaneous clock boundaries, invalid/empty/zero eligibility, exact/tangent/near-station
contacts, wraparound, no-event and dense-event horizons, overlapping parents, horizon clipping,
episode splits/merges, adverse domain evidence, rebuild/outcome immutability, consumer-level
falsifiers. Benchmarks per Strategy §5 fixed context (pinned inputs; cold/warm/resume; wall/CPU;
peak RSS; Swiss calls; DB/WAL; coverage receipts). **No runtime saving is claimed** — the one
v0.1 claimed (streaming gate) was false.

**Consumer compatibility (E.1, adopted as obligations):** each of the seven consumers gets a
deliberate decision per E — notably `ka_taranga` must aggregate over child intervals (E5);
`ka_bhavishya_lekha`'s signal/peak key must be remapped before E1/E5 (identity break); `ka_tulana`'s
40/25/20/15 weights are incompatible with retired confidence and renamed frequency and must be
redesigned, not fed. Served: `query_convergence_windows.ts` and `kala_views/*` change only via an
L3-U04/U11 packet with a sentinel; `explain.ts` has no automatic edge from `method_states` to its
voices — link it or disclose non-consumption.

---

## §7 — Amendments this plan requires of the companion brief (v1.2 → v1.3)

1. §4.2 keys: replace `peak_date`-anchored natural keys with contact/episode identity + generation;
   add split/merge/supersession relations (F-12).
2. §5.2: the cascade map must cover *dependent entities* (obstruction, Darśana, Bhaviṣya,
   `phala_anchors` and its children), not only the final table's surrogate (F-19).
3. §4.4: the "per-class superset" test is retained as a regression check and explicitly labelled
   *not* proof of the full applicable set (F-17).
4. §2.4 / D-3: broaden to an integrated June reconciliation covering E1's geometry as well as E3.

---

## §8 — Decisions for the native

| # | Decision | Independent of repairs? |
|---|---|---|
| M-1 | Contact contracts in scope (Parāśari dṛṣṭi; Moon-gochara; Jaimini; Tājika); fate of `legacy_unsigned_angles`; **M-1a** bhāva-madhya vs whole-sign per rule class | yes |
| M-2 | Aṣṭakavarga doctrine ledger: edition (Santhanam bindu/rekha) → stored-value mapping; BAV thresholds incl. equality; SAV bands by school | yes |
| M-3 | **Integrated June ruling:** does §4.5 (slow only, no scan) or §4.6 (gated fast scans) govern — and does a scope-bounded fast tier inside parents, plus E1's new geometry, fall inside or require amendment? | yes — and blocking for E1/E3 |
| M-4 | Varga–domain correspondence; whether any typed condition may ever veto (default: none) | after step 2 |
| M-5 | Episode boundary conventions (station loop linkage; horizon truncation) | after step 3 |
| M-6 | L5 consumption of Saṅgam predictions; opening `EMPIRICALLY_EVALUATED` | after step 5 |

## §9 — Non-claims

1. No predictive improvement is claimed for any E; the plan makes windows falsifiable.
2. No value (threshold, multiplier, floor) is proposed as fact; `[NATIVE-RATIFY]` does not
   validate arithmetic — v0.1's own arithmetic errors are the proof.
3. Doctrine anchors are the reviewer's corpus verifications (Santhanam BPHS line refs;
   Phaladīpikā ch. 23/26; Hāyanaratna 2.1/3.3); OCR/edition/school differences remain material and
   are not resolved into universal doctrine. Node 5th/9th dṛṣṭi, Muhūrta Cintāmaṇi tāra verses,
   Narapati-jaya-caryā: `[U]`.
4. Live incidence of every defect (0° targets, fast triggers, cross-frame contamination) is
   `[U]`; source reachability is what is established.
5. No live DB query, no ephemeris test, no build.

## Changelog
- **0.3** (2026-09-22) — Second pass before re-review. Added §0.1 (every finding located; evidence
  named), §1b (inputs-consumed source contract, 16 rows), §3b (falsifier per R and per E with data
  source, detector, RUN/SPEC), §6 rewritten as an executable specification; `evidence_sangam/`
  S1–S10 + runner shipped and run. Three script defects found and fixed by the author before
  citation (S2 pair angles; S3 synthetic collision; S8 0°-wrapping loop).
- **0.2** (2026-09-22) — REWORK incorporated. Added Stage R (R-1…R-5) ahead of all elevations;
  E4 gates withdrawn and replaced by typed conditions; E1 split into four method contracts with
  directed-aspect semantics; E2 rebased on `ashtakavarga_bindu_sign`, signed, no prefilter; E3
  scope-bounded, count cap withdrawn, gated on M-3; E5 episodes with children, hull withdrawn, no
  default peak; E6 renamed to modelled frequency, outcome states separated, identity moved first;
  doctrine anchors corrected; §0 ledger; companion amendments listed.
- **0.1** — first issue; verdict REWORK.
