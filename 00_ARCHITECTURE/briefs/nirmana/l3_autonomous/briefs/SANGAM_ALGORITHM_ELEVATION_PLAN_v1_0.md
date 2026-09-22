---
artifact: SANGAM_ALGORITHM_ELEVATION_PLAN
canonical_id: SANGAM_ALGORITHM_ELEVATION_PLAN
version: "1.0"
status: APPROVED_FOR_EXECUTION_STAGE_3   # native rulings M-1…M-7 confirmed + author decisions D-1…D-8 under delegation (2026-09-23T03:39:33+05:30); no open question remains; third Astra review is a stage-3 ENTRY GATE (D-8); E1/E3 wait on the Gochara N-7 ruling
date: 2026-09-22
supersedes: SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md (content unchanged from v0.4 except §0R and frontmatter — v0.4 is the reviewed text; v1.0 is v0.4 + the native's rulings)
approval_record: "SANGAM_RULING_SHEET_v1_0.md §RULINGS (native, 2026-09-23T02:42:50+05:30, confirmed 2026-09-23T03:39:33+05:30) + §CLOSE D-1…D-8 (author, under the native's written delegation)"
reviews_incorporated:
  - ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md  # F-01…F-19, A-01, A-02 — dispositioned in v0.2/v0.3
  - ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_3.md  # RR-01…RR-10 + A.1 re-dispositions — dispositioned in §0 below; 8 new factual claims re-verified at source
evidence: evidence_sangam/ (v2 harness) — 13 assertion-based falsifiers, each with a negative control that must fail; manifest-checked runner; OUTPUT_2026-09-22T234243.txt = SUITE-PASS (13/13 positive, 13/13 negative controls fail); OUTPUT_…T234203.txt retained = the run that caught two of the author's own script errors
asset: ka_sangam (Saṅgam — the convergence engine, L3 Kāla)
companion: SANGAM_ELEVATION_BRIEF_v1_0.md v1.2 — §7 lists the amendments now required of it (extended per RR-01, RR-04, RR-08)
base_branch: main (engine, writer, transit_search verified byte-identical to origin/main by both reviews)
governed_by:
  - CLAUDE.md §B.10, §N.5, §N.7, §N.8
  - MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §2, §3, §5 (P4 + benchmark), L3-U02/U07
  - CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md §4.5/§4.6/§6
  - l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md
does_not_authorize: any code, migration, build, L4 rebuild, L5 consumption, or doctrine. Method qualification is the native's.
evidence_tags: "[C] verified in code · [D] doctrine, verse-cited (reviewer-verified corpus) · [P] practice · [J] judgment · [U] unverified · [R] reviewer finding, author re-verified"
---

# Saṅgam — algorithm elevation plan v1.0

## §0R — The native's rulings, applied (recorded 2026-09-23T02:42:50+05:30)

Verbatim from `SANGAM_RULING_SHEET_v1_0.md §RULINGS` (transcribed from the native's written answer;
the M-6 placeholder was not filled and its minimum count is OPEN):

```
M-1: agree — mean node; Placidus-as-stored; retire legacy scan after one generation; no node dṛṣṭi
M-2: agree, but 4 leans adverse; 6/8/12 inversion does not ship
M-3: agree — §4.5 governs; owner = Gochara stream (kernel path if N-7 approved); E3 tier granted
M-7: agree
M-4: agree, but D30 for DOSHA held
M-5: agree
M-6: agree; minimum n = <your number>
```

| Ruling | Effect on this plan |
|---|---|
| M-1 | R-1/R-3/E1 as written, with **mean node** (disposition (b): true L0 knots retained, mean derived at read in the L0 service, ~1° disagreement declared per row), **Placidus-as-stored cusps** (frame on every row; Śrīpati only as a ratified variant), **legacy scan retired after one generation**, **no node dṛṣṭi** (nodes as gochara agents and targets only). R-3's convention vector: `ephemeris_backend`, `epoch_convention`, `ayanamsa_application` (= `apparent_flg_sidereal`). |
| M-2 | E2 as written; **4 = indeterminate-leaning-adverse** (Phaladīpikā 23.11 = `phaladeepika:PG299:C1`, verified at the table 2026-09-23; note 3 and 4 both read "fear" there — the 4/≤3 boundary is BPHS's); **6/8/12 inversion does not ship**; BPHS bands primary; producer completeness receipt now; kakṣyā deferred; Kshetra S1 shares the source. |
| M-3 | **§4.5 governs.** R-1's directed events are produced **upstream by the Gochara stream** — Path B (kernel, N-5/N-7) if the native approves N-7 on the Gochara brief, else Path A (bounded `transit_search` amendment). **E1 and E3 stay gated until N-7 is ruled**; E3's bounded tier is granted in principle. `_resolve_transit_planet` is replaced by event consumption at that point, not extended. TRANSIT_REDESIGN prompt → SUPERSEDED-and-reissued. |
| M-7 | R-6 as written. |
| M-4 | E4 as written; **D30-for-DOSHA HELD** — domain varga primary, D30 computed and carried as labelled `secondary_dosha`, excluded from every score path, falsifier: any D30 term in a DOSHA score path fails the suite (D-4); cancellation detector precondition binds. |
| M-5 | E5 as written. |
| M-6 | E6 as written; L5 consumption opens on the two preconditions. **`EMPIRICALLY_EVALUATED` gate set (D-1): n=30 per `(domain × route × method_version)`; n=100 instrument-level pooled within one frozen `method_version`; never pooled across versions; below either → `PROVISIONAL_INSUFFICIENT_N` with actual n. Thresholds recompute at equal power if the measured base rate ≠ 0.20.** `ambiguous` → native-adjudicated, censored not scored, 20% per-stratum censoring ceiling (D-2). Evaluation population: consenting charts with real outcomes only; synthetic `evaluation_eligible = false` (D-3). |

**Author decisions under delegation (2026-09-23).** The native confirmed M-1…M-7 and delegated the
residual items; `SANGAM_RULING_SHEET_v1_0.md §CLOSE` carries D-1…D-8 with reasoning. Binding on this
plan: **D-1** (E6 gate numbers), **D-2** (`ambiguous` censoring + ceiling), **D-3** (evaluation
population), **D-4** (D30 secondary, non-scoring, with falsifier), **D-5** (mean convention governs
the pāda reading — Rohiṇī pāda 3, true retained as declared variant, 177″ published), **D-6**
(instrument-level no-node-dṛṣṭi; Gochara owns execution, same-generation λ regeneration),
**D-7** (legacy scan withdrawn only on the R-5 successor manifest), **D-8** (third Astra review =
stage-3 entry gate, before any code).

**Execution order under the rulings (unchanged from §4):** step 1 (companion amendments — done in
brief v1.3/v1.4; June reconciliation — ruled) → step 2 (**R-5 in the disposable harness first**) →
step 3 (R-1…R-4, R-6) → step 4 (E1/E2 — **E1 waits on N-7**; E5) → step 5 (E4; annual-Tājika gate)
→ step 6 (E3 — waits on N-7 and the cost experiment; then E6). A **separate stage-3 execution
session with an independent reviewer** implements; the author certifies nothing. A third independent
review (Astra) runs on this v1.0 before stage 3 opens.

---

# (v0.4 text follows, unchanged — the reviewed content)


**What changed from v0.3, in one paragraph.** The second review returned REWORK, and again it was
right on the substance. Its sharpest finding was about the evidence, not the astrology: my thirteen
"falsifiers" printed CONFIRMED unconditionally — mutation-tested, a constant substituted for the
real function still passed (RR-01). That is the §N.8 defect this campaign exists to eliminate, in my
own work. The suite is rebuilt: every script asserts a named proposition, exits nonzero when
contradicted, and carries a negative control that *must* fail; the runner checks a manifest and
never truncates prior output. Running it caught two of my own new scripts before they could be
cited. The second-sharpest finding: S3 tested a producer that doesn't exist — `ga_strength_writer`
writes `HOUSE_N` and `SIGN_N` from the *same* value, so the "Aries lagna hides a rotation" story was
false (RR-02); E2 is now about vocabulary, provenance and a producer-side zero-validity amendment.
Also new: the I-16 kernel returns **0.0 at dignity 0 regardless of support** — intense adverse
activity is erased (RR-05), so a score-kernel separation becomes repair R-6 and decision M-7; the
lagna read **defaults to Aries** on failure; a post-engine TRIGGER composition was missing from the
input contract; the outcome record needs two axes, not one enum; the preservation test cited a
column that doesn't exist; and Swiss Ephemeris here is answering with Moshier. Every one of these
is dispositioned and located below.

---

## §0 — Disposition ledger

### §0.1 v0.3 review — RR findings and A.1 re-dispositions

| # | Finding | Disposition | Applied at |
|---|---|---|---|
| **RR-01** | Evidence suite is demonstration output; verdicts don't depend on evidence; runner truncates and can't fail | **ACCEPT — suite rebuilt** | `evidence_sangam/` v2: `prop()`/`done()` harness, nonzero exit, `NEG=1` negative control per script, `MANIFEST.txt`, runner exits nonzero on any positive failure or any negative control that passes; new timestamped OUTPUT each run. §6.1 |
| **RR-02** | S3's lagna-rotation fixture is false; `HOUSE_N`=`SIGN_N` same value; missing-planet zeros indistinguishable downstream | **ACCEPT — S3 replaced; E2 re-scoped** | S3 v2 asserts the real producer (same `float(bindus)`, legacy-category read, Lahiri hardcode, `[0]*12`); E2 now: vocabulary + fact-id + ayanāṃśa provenance, and a **producer** completeness receipt for missing planets. §3 E2, §3b |
| **RR-03** | Nine SPEC falsifiers accept the wrong thing or reject the right thing | **ACCEPT — all nine replaced** | §3b (R-1 provenance-not-value; R-2 intersection oracle; R-4 occupancy/tangency separate from S7; E1 same geometry two labels; E2 real GS output; E3 dated fixture; E4 hold-all-else-fixed; E5 orb intervals not crossings; E6 estimand-bound coverage) |
| **RR-04** | R-3's dedup tuple is a geometry cache key, not testimony identity; lagna/Moon defaults silent; zero-vs-failure states merged | **ACCEPT** | R-3 split into (a) geometry cache key and (b) testimony identity; §1b rows 5, 17; S12 |
| **RR-05** | I-16 kernel: dignity 0 → 0.0; signed labels around a nonnegative combiner cannot carry adverse testimony; legacy/new coexistence undefined | **ACCEPT — new repair R-6, decision M-7** | §3 R-6: activity · valence · applicability · availability as separate fields; dignity leaves the necessary product; legacy generation labelled, never pooled. S11 |
| **RR-06** | §1b omits post-engine TRIGGER composition (`W:49-114`, calls `:682`, `:708`); generic angular currents C9/benefic-dṛṣṭi untouched | **ACCEPT** | §1b row 17; R-4 names both generic currents (`E:210-224`, `E:442-482`) for method/role assignment or withdrawal; S13 |
| **RR-07** | Outcome enum conflates observation with model validity | **ACCEPT** | §3 E6: two axes — `observation ∈ {hit, miss, ambiguous, censored, unobserved}` × `derivation ∈ {valid, invalidated, superseded}` |
| **RR-08** | Preservation test too weak; `outcome_content` not a real column (real: `outcome_recorded`, `outcome_notes`); count/hash permit swaps | **ACCEPT** | §6.3 rewritten: manifest keyed by stable claim/outcome id, exact content, bindings, successor mappings; attack list incl. content-swap; real columns |
| **RR-09** | S8 is Moshier fallback (flags 65794→65860, no `.se1`); stations bracketed not solved; no expected count | **ACCEPT** | S8 v2 records engine provenance, bisects stations to 1 min, asserts loop count 3 and 3/1 crossings; §9 corrects "no ephemeris test" |
| **RR-10** | Serving proof is a future obligation; no consumer matrix; no material-field sentinel | **ACCEPT** | §6.2 adopts the reviewer's 7×6 matrix and served-surface table (incl. its own correction on `priority.ts`); sentinel per changed meaning |
| A.1 F-03 MISAPPLIED | — | ACCEPT (= RR-02) | §3 E2 |
| A.1 F-12 MISAPPLIED | R-5 lacks an implementation gate; enum conflation | ACCEPT (= RR-07) + §4 step 2 | §4 |
| A.1 F-14 MISAPPLIED | — | ACCEPT (= RR-04) | R-3 |
| A.1 F-16 LISTED_NOT_APPLIED | generic benefic-dṛṣṭi weights unaddressed | ACCEPT | R-4 |
| A.1 F-17 LISTED_NOT_APPLIED | no per-E applicable/selected/served accounting | ACCEPT | §6.2 table per E |
| A.1 A-01 MISAPPLIED | quota selector & self-scoped delete preserved "unconditionally" | ACCEPT | §1: preserved = transaction ownership, resumability, SAVEPOINT pattern; selection cap and delete policy are contract-dependent |
| A.1 A.3 MISAPPLIED | "90° never under Parāśari" contradicts fractional Parāśari 4th | ACCEPT | E1: same geometry may carry Parāśari (fractional) and Tājika evaluations, separately labelled, one root |
| A.1 D.1 / D.2 / D.3 / E.1 LISTED_NOT_APPLIED | sequence gate for R-5; P4 per-E accounting; lineage enumeration; consumer matrix | ACCEPT | §4, §6.2, §3 D.3 rows, §6.2 |
| A.4 row 5 | lagna defaults to `'Aries'` on failure (`W:1149`), fallback retained (`W:1162`) | ACCEPT — new | §1b row 5; R-3(b); S12 |
| A.4 row 8 | "birth-year derivation" from MIN level-1 start is unproven | ACCEPT | §1b row 8 marked `[U]` |
| A.4 row 11 | scanner signature can't take frame args — bounded amendment is a *prerequisite*, not an escape | ACCEPT | R-3 explicitly gates on that amendment |
| A.5 S5/S6/S7/S9/S10 mutation results | verdicts independent of evidence | ACCEPT (= RR-01) | all thirteen scripts now fail under `NEG=1` |
| E.2 reviewer self-correction | `priority.ts` route does **not** read `kala_convergence` (`WRAP:673-711`) | ACCEPT — recorded | §6.2 served table |
| D.1 companion amendments | §5.3 not §4.2; B:98,114,229 streaming; B:191-192/325 kernel/rarity; mapped semantic comparison | ACCEPT | §7 |
| F verdict — fit for rulings | M-1/M-1a, M-2, M-3 legitimate once fixture facts corrected; M-4…M-6 later | ACCEPT | §8 marks which are rulable now |

**Author's one point of emphasis (not a rejection):** the reviewer's "predictive improvement is
UNVERIFIABLE" stands throughout. The plan's claim is narrower and unchanged — that it makes windows
*falsifiable* — and the reviewer agrees that is the honest scope.

### §0.2 v0.1 review — carried from v0.2/v0.3 (unchanged dispositions)

F-01…F-19, A-01, A-02, doctrine anchors, C.2 techniques, D.1 sequence: all ACCEPT, as in
v0.3 §0 — retained by reference; where the v0.3 review re-graded a row, §0.1 above governs.

---

## §1 — Baseline, corrected [C] (v0.3 §1 plus what the second review added)

Unchanged rows: modes A–D; contact model; per-signature planet incl. fast resolution; gate after
accumulation; C11 dampener 0.3 / missing → 1.0; C7 dead on the usable path; C8 target unused; C12
start-only lord match; C13 dead; cross-daśā exact-endpoint key; `max_level=3` vs service default 4;
closed-closed at `:1140`; frame hardcodes; ±15-day shoulders; rarity angle fraction; L1 facts unread.

| Added | Verified behaviour | Where |
|---|---|---|
| **Kernel erases adverse activity** | `convergence_score([0,1,1], full support)` → **0.0**; `[0.2,…]` → 0.052. Dignity multiplies the whole result; an intensely active adverse configuration scores as nothing. | `engine.py:696-728, 1221`; **S11** |
| **Lagna defaults to Aries** | `lagna_sign = 'Aries'` ("this native's lagna") before the query; retained on any failure — the CR-87 class, on the lagna read | `ka_sangam.py:1147-1163`; **S12** |
| **Post-engine TRIGGER composition** | `apply_trigger_suppression` at admitted 0.2/0.2 applied to A/B results *after* `mode_a_search` (`:667`) / `mode_b_sweep` (`:695`), at `:682`/`:708`; missing service = no-op; exceptions logged and continued | `ka_sangam.py:49-114`; **S13** |
| **Generic angular currents still live** | C9 transit-to-transit `[0,60,90,120,180]`; benefic dṛṣṭi `_ASP_WEIGHT {0:1, 60:.7, 90:.2, 120:1, 180:.5}` | `engine.py:210-224, 442-482` |
| **Ephemeris provenance** | requested `SWIEPH`, returned `MOSEPH`; no `.se1` files under repo or venv | **S8** provenance line |
| **Mode B** | requires a magnitude threshold in addition to the orb gate | `engine.py:1400-1404`; `ka_sangam.py:702` |

**Preserved (engineering, not policy):** orchestrator transaction ownership; cross-attempt resume
ledger; SAVEPOINT-guarded soft reads; fail-loud *birth location* (CR-87 — but not the lagna read,
S12); house-from-Moon vedha *producer* contract; honest-empty `_current_stance`. **No longer
"unconditional":** the 200/60 per-class selection cap and the self-scoped delete policy — both
depend on the coverage and generation contracts (A-01).

### §1b — Inputs consumed: source contract (v0.3 rows 1–16 as re-graded; rows 17–18 new)

Rows 1, 3, 4, 7, 9, 10, 12, 14, 15, 16: CONFIRMED by the v0.3 review, unchanged. Re-graded rows:

| # | Change |
|---|---|
| 2 | Producer is binder **and** `ka_yojaka.py:244-310, 392-418` (eligibility enrichment with resolution reasons) — preserve that lineage; successful empty/zero eligibility ≠ service failure |
| 5 | Add: `lagna_sign` defaults to `'Aries'` (`W:1149`, retained `:1162`); Moon reads fix Lahiri; lagna query does not qualify ayanāṃśa. Plan requires: fail-loud, ayanāṃśa-qualified, total `ORDER BY` |
| 6 | Reader-level "measured zero vs missing planet" is **impossible** after `GS:1026` emits identical rows → bounded **producer** amendment: completeness/validity receipt per planet (RR-02) |
| 8 | Birth-year equivalence of `MIN(start_date) level 1` is `[U]` until compared with authoritative birth input |
| 11 | `KaGocharaService` and the scanner are separate contracts; the scanner's signature does not accept frame/node args — a bounded amendment is a **prerequisite** for R-3, not an escape |
| 13 | Add fixed Lahiri and missing/failed-read state; a full annual method needs more than the year-lord table |
| **17** | **Post-engine TRIGGER composition** — `ka_sangam.py:49-114`; inputs: gochara service, vedha rules, Moon frame; admitted version/weights 0.2/0.2; no-op on missing service. Plan requires: component source facts/context/availability recorded; relation to favourable vs adverse propositions declared; no-op ≠ "no obstruction"; lineage with C11 and Vighnakara declared (no duplicate-vedha bug is asserted — `TG:314-329` documents its removal) |
| **18** | **Generic angular currents** — C9 (`E:210-224`), benefic dṛṣṭi (`E:442-482`). Plan requires: assign each a named method/role under E1's contracts or withdraw it; test relevance and polarity |

---

## §2 — Constraints — unchanged from v0.3, with one addition

**Both E1's new geometry and E3's fast tier touch the June ruling**; the June artifact carries
competing directions (§4.5/§6 vs §4.6). M-3 is an *integrated* ruling. Existing fast-trigger
reachability (`_resolve_transit_planet` returns Moon/Sun/Mercury) is not retrospective authority.

---

## §3 — The plan: six repairs, then six elevations

### Stage R — Repairs (blocking; before any new method)

| # | Repair | Falsifier (see §3b) |
|---|---|---|
| **R-1 Target binding** | Every trigger carries `target_fact_id`, `target_type` (natal graha / bhāva-madhya / sign / point / **relational — separate detector**), `frame`, `ayanamsha_id`, `derivation`. Unresolvable → `unavailable`. A *sourced* target at exactly 0° is valid; a *defaulted* 0° is not — provenance, not value, is the test (RR-03). Bhāva-madhya vs whole-sign decided per rule class here (M-1a). | S1 (today) · SPEC R-1 |
| **R-2 Clock intersection** | Atomic simultaneous intersection with parent hierarchy (not transitive merging of any overlappers); failed service → `unavailable`; successful query with zero support → **evaluated, empty** (never merged with failure); `max_level` declared; boundary convention declared (S-H). | S6 (today) · SPEC R-2 |
| **R-3 Frame and identity** | **(a) geometry cache key** = (planet, directed angle, target, frame, ayanāṃśa, node convention, date) — for sharing geometry; **(b) testimony identity** = (a) + chart, signal/predicate, route, mode, method/version, source generations, precise interval/contact id — never coalesced (RR-04). Frame/ayanāṃśa/node flow from the predicate to *every* reader (scanner, AV read, Moon/lagna reads); the scanner signature amendment is a prerequisite. Lagna/Moon missing → fail-loud, never Aries (S12). | S12 (today) · SPEC R-3 |
| **R-4 Detector and current audit** | Real interval ends for C/D; measured orb entry/exit shoulders for A/B; tangencies/near-station/horizon-edge occupancy; C8 uses its target; C11 applies to the proposition it qualifies, `unavailable` ≠ 1.0; **C9 and benefic dṛṣṗi assigned a method/role or withdrawn** (RR-06); domain lord per domain; I-17's cos²/0.7 labelled `[P]` or requalified against BPHS 26.6-8 fixtures. Missing-planet AV zeros → producer receipt (row 6). | S7 = performance-path observation only · SPEC R-4 (occupancy, tangency, unavailable-vedha — separate) |
| **R-5 Identity and history** | Stable contact/episode identity independent of `peak_date`; split/merge/supersession relations; immutable issued-claim content + version + exposure; generation-aware dependent map across 403/245/247/249/363 incl. nullable and FK-free references. **Implemented and qualified in the disposable harness before any contact-changing implementation is admitted** (§4 step 2). | SPEC R-5 |
| **R-6 Score-kernel separation** *(new, RR-05)* | Replace the single I-16 output with separate fields: `activity` (geometric/clock intensity, ≥0), `valence` (signed, from dignity/nature/AV/route), `applicability` (F06 per method), `availability` (inputs present), and — only where separately qualified — a calibrated probability. **Dignity leaves the necessary product**; it becomes valence. I-16's multiplicative-veto form survives only for genuine necessity (orb presence, route satisfied). Legacy rows carry `kernel_version = legacy_i16` and are **never pooled or ranked** with new rows. Consumer projections choose fields explicitly. | S11 (today) · SPEC R-6 · **M-7** |

### Stage E — Elevations (re-scoped per both reviews)

**E1 — Method-specific contact contracts.** Four versioned contracts — Moon-gochara + vedha
(Phaladīpikā 26.1-8 [D]); Parāśari graha-dṛṣṭi with **full and fractional** aspects (BPHS 26.2-5,
BP1:16485-16505 [D]), *directed* (source at `target − angle`, S2), degree strength per BPHS 26.6-8 on
worked fixtures; Jaimini rāśi-dṛṣṭi on a qualified Jaimini route only (BPHS 8.1-3; no degree
requirement); Tājika with its own orbs/strengths/itthaśāla motion rule (Hāyanaratna 2.1, 3.3 [D]).
**The same geometry may carry a Parāśari (fractional 4th) and a Tājika (square) evaluation, separately
labelled, one root** — the v0.3 "never under Parāśari" fixture is withdrawn. Sign applicability +
degree annotation is a declared hybrid; the interval survives with no exact pass. Legacy scan kept
one generation as `legacy_unsigned_angles`, R-6-labelled, never pooled. Requires R-1, R-3, R-6.

**E2 — Aṣṭakavarga from the correctly named facts, signed.** Read `ashtakavarga_bindu_sign` with
fact ids, generation, predicate ayanāṃśa, and the edition's bindu/rekhā → stored-value mapping
(A-02). C7 := transiting planet's own BAV → structured verdict `{value, rule, source, availability,
verdict ∈ support|indeterminate|obstruct}` — **not** `BAV/8` into the positive combiner (R-6).
Thresholds ≥4/≤3 provisional; equality per M-2; SAV bands school-labelled (BPHS 72.3-5 vs
Phaladīpikā 23.20), never two votes. Every ingress evaluated, verdict recorded, no SAV prefilter.
Kakṣyā deferred to an L1 amendment exposing the contributor matrix (`strength.py:216`). **Producer
amendment now, not deferred:** completeness/validity receipt so missing-planet zeros are
distinguishable (RR-02). The frame is *not* an open question.

**E3 — Fast-tier refinement, conditional on M-3.** Inside selected parents; all authorised
families enumerated; resource limit → `refinement: incomplete`, resumable; coverage receipt states
how parents were selected ("complete inside selected parents" ≠ "complete chart refinement");
overlapping parents must not duplicate child evidence. Children are *conditional refinement
selected through the parent* — new geometry, evidence count unchanged. Tāra and Sarvatobhadra are
different conditioning methods; reuse the served vedha/laṭṭā producer. **Annual Tājika gets its own
scheduled contract and gate before E3** (§4 step 5), not a promise.

**E4 — Typed natal and clock conditioning** (gates withdrawn; reviewer AGREEs). (1)
`boundary_distance` **per clock, level, parent and lord** with signed time-to/from and source
precision — never a minimum over "any level"; annotation only, no salience meaning (BPHS 47.3-4
defeats a universal last-portion rule). (2) `lord_condition` — signed promise/denial from sourced
strength, functional role, dignity, lordship; **operative when weak/adverse** (BPHS 47.2-4). (3)
`varga_condition` — *natal* dignity in the domain varga (BPHS 7.1-8), with cancellation evidence;
the capability aggregate's varga average is cited, never re-voted. All three feed R-6's `valence`,
never `activity`; none vetoes (M-4).

**E5 — Episodes with child contacts.** Episode = contacts of one (graha, target, directed angle,
frame, method) linked by a station loop; **every child retains its own orb entry/peak/exit
interval, identity, precision, method/orb, truncation**; singletons valid; >3 or horizon-truncated
episodes not forced to a template; hull = search envelope; **occupied time = union of child
intervals**; no default peak phase (cheṣṭā-bala is strength, BPHS 27.21-25). Geometric identity
separate from claim attachment; split/merge/supersession relations published before any key
change. `ka_taranga`: define the aggregation unit (occupied duration / episode / route) — month-set
union is insufficient because its mean counts one contribution per intersecting row (RR-05 sibling).
S8 supplies oracle *points*; orb-interval occupancy (disjoint vs continuous across a loop) is a
separate SPEC.

**E6 — Modelled episode frequency, and a two-axis outcome record.** `modelled_episode_frequency`
= qualified episodes ÷ declared exposure, with strata: target/predicate/route/domain population,
context, method version, horizon, eligible exposure, censoring, duplicate policy, unit (e.g.
episodes per target-year). Contact counts and episode counts named as such. Zero numerator over
complete positive exposure = measured zero; zero/missing exposure = unavailable; a fully scanned
30-year horizon is *complete for that horizon* and incomplete only against a larger claimed
estimand (RR-03). `rarity_years` retired; not replaced by a constant period. **Outcome record
(RR-07):** immutable issued claim (content, version, exposure) × `observation ∈ {hit, miss,
ambiguous, censored, unobserved}` × `derivation ∈ {valid, invalidated, superseded}` — an
invalidated derivation never erases or converts an observation. M-6 opens *consumption*, not
`EMPIRICALLY_EVALUATED`.

### §3b — Falsifier per repair and elevation (RR-03 replacements)

| Item | Falsifier | Data source | Detector that returns false | Status |
|---|---|---|---|---|
| R-1 | (a) sourced target at exactly 0° Aries is **accepted** with provenance; (b) absent target → `unavailable`, no contact rows; (c) relational trigger routes to its own detector | synthetic predicates | a defaulted-0° row exists; a sourced-0° row rejected; relational trigger hits the natal-point detector | S1 (today) · SPEC |
| R-2 | expected intersection *segments with supporter/parent sets* for: unequal endpoints, disjoint, nested levels, zero score, valid empty, service failure, sub-day boundary | synthetic intervals | any segment missing; empty merged with failure | S6 (today) · SPEC |
| R-3 | Lahiri vs Raman rows distinguishable and never coalesced; missing lagna → fail-loud not Aries; same geometry shared across two predicates yields one cache entry and two testimonies | synthetic | cross-frame dedup; `lagna_sign == 'Aries'` with a failed query; two testimonies collapsed | S12 (today) · SPEC |
| R-4 | contact active at horizon start reported; tangency within orb reported; vedha data missing → `unavailable`; C9/benefic-dṛṣṭi either carry a method label or are absent | Swiss (Moshier-labelled) + synthetic | edge/tangent contact missing; `vedha_factor==1.0` with no data; an unlabelled generic current in output | S7 (perf path only) · SPEC |
| R-5 | move a peak one day; split one contact into two; merge two into one; interrupt and resume — every original claim/outcome id retains exact content and bindings, successors mapped | disposable harness | orphaned or re-pointed outcome; content differs; Bhaviṣya fail-closed trips | SPEC |
| R-6 | `activity` > 0 and `valence` < 0 for a dignity-0 intensely active configuration; legacy and new rows never in one ranking | real kernel + synthetic | score 0.0 with full support (S11 today); a ranking containing both kernel versions | S11 (today) · SPEC · M-7 |
| E1 | Mars 4th onto target: search at `target−90`; Saturn 3rd/10th likewise; same 90° geometry emits one Parāśari-fractional and one Tājika evaluation, one root; sign-valid interval with no exact pass survives; 359°→1° wraparound; non-Aries synthetic | arithmetic (S2) + synthetic + Swiss | naive search used; Tājika row labelled Parāśari or vice-versa; interval dropped; two roots | S2 (today) · SPEC |
| E2 | reader consumes **real** `ga_strength_writer` output: sign selection, vocabulary mapping, measured 0, null, missing-planet receipt; SAV30/BAV2 → `obstruct` as a *verdict field*; SAV26/BAV6 → `support`; BAV=4 per ledger | real GS output on synthetic chart | legacy category read; `BAV/8` in activity; null coerced to 0 without receipt | S3 (today) · SPEC |
| E3 | dated fixture: parent `[2027-03-01, 2027-04-29]`, target Moon-natal 200.0° Lahiri (Moshier stated); independently enumerated expected Moon contacts (conj+opp at least) — all emitted, none capped; resource-interrupt → `incomplete` and resume; no-contact parent → `[]`; overlapping parents → no duplicated child | Swiss + synthetic | fewer than enumerated with `complete`; default date; duplicate child; evidence count increments | S4 (bound only) · SPEC |
| E4 | hold **every other consumed fact fixed**; vary only D10 dignity of the running lord: the career-route `valence` changes, health-route fields unchanged; debilitated lord still present with signed condition; no `boundary_distance` multiplier | synthetic charts + synthetic `chart_divisionals` | health fields change; lord absent/`inapplicable`; any multiplier | SPEC |
| E5 | S8's inside points (2026 347.11°, 2027 0.20°, 2028 13.60°) with orb 5° → **child intervals** — assert whether occupancy is disjoint or continuous across the loop, per point; controls (352.52°, 5.63°, 19.05°) → one contact, not grouped; `ka_taranga` weights invariant to duplicate insertion; partial-month occupancy | Swiss (Moshier-labelled) + synthetic | 3 rows not 1 episode; control grouped; continuous occupancy reported as disjoint; taranga weight changes on duplicate insert | S8 (points) · SPEC |
| E6 | 30-year declared horizon fully scanned → `complete` for that estimand; lifetime estimand over 30-year scan → `incomplete`; zero exposure → `unavailable`; frequency never appears in `independence_groups`; hit + later `invalidated` keeps the hit | synthetic versioned sweep | wrong completeness label; frequency as witness; observation erased | S5 (today) · SPEC |

**Fixture policy.** Synthetic charts are non-persons. Both production charts are Aries lagna and
therefore cannot exercise lagna-dependent reads (S12 shows the default is Aries — indistinguishable
on those charts). Swiss Ephemeris here runs **Moshier** (S8 provenance line); it is an independent
referee for geometry at Moshier precision, not pinned Swiss-file provenance — every geometric
fixture states engine, flags, ayanāṃśa, node convention and tolerance. Saṅgam's own output is never
the oracle for a claim about Saṅgam. Read-only DB aggregates are for incidence only.

---

## §4 — Sequence (v0.3 review D.1, adopted)

| Step | Content | Rulable now? |
|---|---|---|
| 1 | Correct fixture/evidence defects (done: suite v2); prepare method/source decision packets; reconcile June scope, target kinds, school meanings | **M-1/M-1a, M-2, M-3** |
| 2 | Amend the companion (§7); **implement and qualify R-5 in the disposable harness before any contact-changing implementation** | — |
| 3 | R-1…R-4, R-6: truthful inputs, intersections, context, detectors, current polarity/availability, kernel separation; complete baseline manifests | **M-7** |
| 4 | E1/E2 method-specific signed contracts; complete route/predicate coverage before geometry reuse; then E5 on the defined events with child aggregation and consumer mappings | M-5 after this |
| 5 | E4 typed conditions; **scheduled annual-Tājika contract and gate**; lineage and consumer meaning | M-4 |
| 6 | E3 after the integrated ruling and a fixed-context full-scope cost experiment; then E6 on qualified versioned exposure. Claim preservation began at step 2. | M-6 |

Lineage (D.3, adopted per E): E1 target facts/derivation, geometry, context, route/method version,
binding predicate — two methods on one contact = one root; E2 raw BAV contributor roots, SAV as
aggregate, kakṣyā as contributor view — one origin; E3 parent-selection derivation + independently
computed child geometry — conditional, non-incrementing; E4 clock ids/parents, natal facts,
cancellation rule, capability's reused roots exposed; E5 every contact and loop with episode
membership — grouping neither corroborates nor repairs ICC; E6 exposure manifest and immutable
claim/observation provenance — frequency never a witness for its own contacts. Also C11 / TRIGGER /
Vighnakara roots and proposition-specific roles declared before composition. **No statistical
independence is claimed.**

---

## §5 — Techniques (v0.3 review C.2, adopted verbatim)

Chara/Jaimini daśā + rāśi-dṛṣṭi: IN, qualified route after R-2, with karakas/argalā, declared
variant (BPHS 46.155-157). Yoginī: IN via existing clock, Moon-derived lineage (BPHS 46.195-199).
Kālacakra: IN conditionally after savya/apasavya/deha/jīva qualification (BPHS 46.52+, ch.49).
Tājika varṣa-praveśa: IN **before E3** for annual questions — C12's lord match is not an annual
judgment. Sudarśana: IN as audited reuse (BPHS 74.4-6, 74.19-23). Praśna: OUT of unattended sweep.
Argalā: IN through its producer for relevant routes (BPHS 31.2-9). Bhāva-madhya vs whole sign:
**mandatory at binding** (BP1:16632-16633). Rāhu/Ketu: IN under named rules and node convention;
absence from `_AV_SCAN_PLANETS` is not itself a defect; node 5th/9th `[U]`.

---

## §6 — Executable evidence, ecosystem, preservation

### 6.1 Evidence suite v2 (RR-01, RR-09)

`evidence_sangam/RUN_ALL.sh`: reads `MANIFEST.txt` (13 scripts; expected positive exit 0; each must
exit nonzero under `NEG=1`); writes a **new** timestamped `OUTPUT_…txt` (refuses to overwrite);
exits nonzero on any positive failure or any negative control that passes. Each script: one named
proposition via `prop()`, `done()` states whether PASS means *pre-fix defect present* or *post-fix
behaviour*. Current: `OUTPUT_2026-09-22T234243.txt` **SUITE-PASS 13/13**; the retained
`OUTPUT_2026-09-22T234203.txt` shows the run that failed on two author errors (S3 over-broad regex;
S13 wrong call name) — the runner working as intended. Source-regex scripts (S1, S3, S9, S10, S12,
S13) establish **reachability**, not behaviour; S5/S6/S11 call real functions; S8 is Moshier-
labelled geometry. SPEC rows join the manifest as they become runnable; a SPEC that cannot be made
runnable at its step blocks that step.

### 6.2 Ecosystem — seven consumers × six elevations (adopted from the v0.3 review E.1) and served surfaces (E.2)

Adopted verbatim as obligations; each cell is a compatibility decision owed before that E lands.
Load-bearing cells: `ka_kala_darshana` **reads `confidence_label` and `rarity_years` — removal breaks
SQL**; no shim may equate frequency to rarity. `ka_bhavishya_lekha` — geometry/peak changes break
its signal/peak key unless R-5 is in place; it narrates rarity as a "year cycle" — prose must
change. `ka_tulana` — 40/25/20/15 composite consumes rarity/30 and confidence; **redesign, do not
relabel**. `ka_taranga` — per-row mean; define the unit. `ka_kalasutra` — one best scalar per
signal cannot choose across method classes. `ka_vighnakara` — peak-only obstruction check misses
child variation. `ka_jivana_parva` — counting units explicit; `LIMIT 1` deterministic.

Served: `query_convergence_windows.ts:90-129` selects old scalars + `constituent_factors`, default
30/max 200 rows, no method/ayanāṃśa selection — every changed meaning needs an L3-U04/U11 packet
and a **material-field sentinel** (a low-ranked adverse condition surviving to a real caller).
`kala_views/priority.ts` → `call_priority_ranking` → `WRAP:673-711` **does not read
`kala_convergence`** (reviewer's own correction of its v0.1 claim) — declare non-consumption or an
authorized new route, tested independently of `ka_tulana`. `explain.ts` has no automatic edge from
`method_states` — link or disclose. Applicable ≠ selected ≠ served: per-E accounting per the
v0.3 review D.2 table (E1 manifest predicate × method × target; E2 every ingress incl. adverse/zero/
equality/unavailable; E3 parent coverage + child enumeration; E4 domain × clock × condition with
explicit missing state; E5 every old contact has a child/supersession disposition; E6 frequency from
the exposure manifest, invariant to page size/top-K/duplicates). **No runtime saving is claimed.**

### 6.3 Downstream preservation (RR-08 — rewritten)

On the disposable harness only. Before and after a candidate Saṅgam generation is prepared (L4 not
rebuilt): a **manifest keyed by each original stable id** — issued claim (`kala_bhavishya` row:
full content, version, exposure), its observation (**`outcome_recorded`, `outcome_notes`** — the
actual columns), every dependent binding (`kala_obstruction`, `kala_darshana`, `phala_anchors`,
`phala_suddha_sodhana`, `phala_muhurta`/`phala_mitigation` linked ids, `phala_phaladesa.top_anchor_id`
resolved semantically since it is FK-free), and authorized successor mappings. Compare **exact
content per id**, not counts or unframed hashes. Required attacks: empty rebuild; moved date;
one-to-many split; many-to-one merge; ambiguous match; interrupted/resumed rebuild; **unchanged-
count content-swap**. Original history immutable; candidate additions carry an explicit expected
delta. This authorises no L4 rebuild; switching dependent generations needs its own admitted
contract.

---

## §7 — Amendments required of the companion brief (v1.2 → v1.3)

1. **§5.3 keys** (not §4.2): contact/episode identity + generation replaces `peak_date`-anchored
   keys; split/merge/supersession relations (F-12).
2. **§5.2** cascade map over all dependent entities incl. nullable and FK-free references (F-19).
3. **§4.4** per-class superset test = regression check, not completeness; replace peak-based
   equivalence with a **mapped semantic comparison** that permits explicitly invalid old rows to be
   withdrawn (D.1).
4. **§2.4 / D-3** broadened to the integrated June reconciliation (E1 + E3).
5. **Correct B:98, B:114, B:229** — the streaming/memory claims are false (S7).
6. **Replace B:191-192 / B:325** — I-16/I-17/I-18/rarity are not "preserved unchanged"; R-6 and E6
   supersede.
7. Publish generation/served compatibility for all seven consumers (§6.2).

## §8 — Decisions for the native

| # | Decision | Rulable |
|---|---|---|
| M-1 / M-1a | Contact contracts in scope; fate of legacy scan; bhāva-madhya vs whole-sign per rule class | **now** (fixture facts corrected) |
| M-2 | Aṣṭakavarga ledger: edition bindu/rekhā mapping; BAV thresholds incl. equality; SAV bands by school | **now** |
| M-3 | **Integrated June ruling**: §4.5 (slow-only, no scan) vs §4.6 (gated fast scans) — governing rule and allowed scope for both E1's geometry and E3's tier | **now**; blocks E1/E3 |
| **M-7** *(new)* | Score-kernel separation (R-6): dignity leaves the necessary product and becomes valence; legacy generation labelled, never pooled | after step 2 |
| M-4 | Varga–domain table; boundary-distance semantics per clock/level; no condition vetoes | after step 3 |
| M-5 | Episode boundary conventions; occupancy unit for aggregators | after step 4 |
| M-6 | Consumption boundary for issued claims/outcomes; separately, empirical-evaluation authority | after step 5 |

## §9 — Non-claims

1. No predictive improvement is claimed; falsifiability is.
2. No value is proposed as fact; `[NATIVE-RATIFY]` validates nothing arithmetically.
3. Doctrine: reviewer-verified corpus anchors (Santhanam BPHS; Phaladīpikā ch. 23/26; Hāyanaratna
   2.1/3.3); edition/OCR/school differences material. Node 5th/9th, Muhūrta Cintāmaṇi tāra verse,
   Narapati-jaya-caryā: `[U]`.
4. Live incidence of every defect: `[U]`; source reachability is what is established.
5. **Ephemeris:** S8 ran, on **Moshier** (no `.se1` files; requested SWIEPH, returned MOSEPH). v0.3's
   "no ephemeris test" was wrong; corrected.
6. No live DB query; no build; no L4 rebuild experiment; no production safety receipt.

## Changelog
- **0.4** (2026-09-22) — Second review (REWORK) incorporated: RR-01…RR-10 and all A.1
  re-dispositions (§0.1). Evidence suite rebuilt as 13 assertion-based falsifiers with negative
  controls and a manifest-checked, non-truncating runner (SUITE-PASS; the failing run retained). S3
  rebuilt on the real producer (rotation hypothesis withdrawn). New repair **R-6** and decision
  **M-7** (kernel erases adverse activity at dignity 0). §1b rows 17–18 (TRIGGER composition;
  generic angular currents); row 5 lagna-defaults-to-Aries; row 8 `[U]`; row 11 prerequisite.
  §3b: all nine invalid SPECs replaced. E6 outcome record split into two axes. §6.3 preservation
  rewritten on real columns with attack list. §6.2 adopts the 7×6 consumer matrix and the
  reviewer's `priority.ts` self-correction. §7 extended (§5.3; B:98/114/229; B:191-192/325). §9
  corrects the ephemeris non-claim.
- **0.3** — falsifiers, inputs contract, evidence spec; verdict REWORK.
- **0.2** — first REWORK incorporated. **0.1** — first issue.
