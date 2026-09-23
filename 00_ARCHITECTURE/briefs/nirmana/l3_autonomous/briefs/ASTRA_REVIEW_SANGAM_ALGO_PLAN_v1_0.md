---
artifact: ASTRA_REVIEW_SANGAM_ALGO_PLAN
version: "1.0"
reviews: v1.0
prior_verdicts: [REWORK, REWORK]
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review"
date: 2026-09-23
verdict: PROCEED_WITH_AMENDMENTS
reviewed_plan_sha256: 8f97963fee71a2c74d877cc29f8f378f06e3048a42f3e34c112cb83e10f51119
authority: "Review only; authorizes nothing."
---

# Astra review — Saṅgam algorithm elevation plan v1.0 (third review, stage-3 entry gate D-8)

**Verdict: PROCEED_WITH_AMENDMENTS.** This is not the third REWORK, and saying so is itself a
finding: the two REWORKs' core demands are now genuinely met, which I verified by re-running and
mutation-testing the evidence suite rather than reading the author's claims about it. But four HIGH
findings — two scope/sequencing holes that would stall stage 3 inside its first week, one missing
serving-order contract, and two unnamed L4/L5 consumers — plus five ruling/plan-level
contradictions must land in the plan/brief **text** before stage-3 code execution. None requires
re-ruling; none touches the native's seven rulings; all are text/scope amendments in exactly the
class the Kimi K3 review handled.

Findings are numbered RRV-01…RRV-16 (re-review v1.0). Severity: **4 HIGH, 5 MODERATE, 5 MINOR,
2 NOTE**.

Verification posture: every [C] below was checked at file:line by my own reads; every [D] against
the corpus (table `classical_text_chunks` via read-only SQL, and the Santhanam OCR files where the
sheet cites them); [J]/[P]/[U] treated as unproven. The 5433 DB endpoint is down and the 5434 proxy
flapped during this session; the corpus queries below were executed through a working read-only
connector and are reproduced with exact SQL. The evidence suite was run by me (new OUTPUT
`OUTPUT_2026-09-23T051310.txt`: 13/13 positive exit 0, 13/13 negative controls exit nonzero, S8 on
SWIEPH with `.se1` sha256 checksums recorded) and independently mutation-tested in isolated
subprocesses. The only file written by this review is this one.

---

## A. Claims

### A.1 Every §0.1 disposition row

`APPLIED` = the disposition is incorporated as a plan requirement and I verified the incorporation
at the named section. Residual gaps are named as findings, not silently regraded. **P** = plan
`SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md`; **RS** = ruling sheet; **B** = companion brief
(v1.5); **EV** = `evidence_sangam/`.

| §0.1 row | Disposition | Section checked | Result |
|---|---|---|---|
| RR-01 | ACCEPT — suite rebuilt | P §6.1; `RUN_ALL.sh`, `MANIFEST.txt`, `_common.py`; my run `OUTPUT_2026-09-23T051310.txt` | **APPLIED.** Runner reads manifest, requires positive exit 0 AND nonzero under `NEG=1`, refuses overwrite, propagates failure. I re-ran it: 13/13 + 13/13. Residual: sincerity escape (RRV-15). |
| RR-02 | ACCEPT — S3 replaced; E2 re-scoped | `S3_ashtakavarga_producer_vs_reader.py`; `ga_strength_writer.py:968-1036` | **APPLIED.** S3 v2 asserts the real producer (same `float(bindus)` at both HOUSE/SIGN `_mk` calls — I read the source at :1026-1036; absolute-rāśi comment at :968-980). Rotation hypothesis withdrawn in text. |
| RR-03 | ACCEPT — nine SPECs replaced | P §3b rows R-1…E6 | **APPLIED (as text).** Each replacement matches my v0.3 "Replace with" cell. SPECs are not runnable yet — by design; the block-the-step rule backstops. Residuals: RRV-02 (runnability of R-3/R-4 gated on N-7), RRV-05/06 (E5 SPEC misses two ruled elements), RRV-14 (E1 angle-family), RRV-08 (R-6 fixture gap). |
| RR-04 | ACCEPT | P §3 R-3 | **APPLIED.** (a)/(b) split with the full testimony-identity field list I enumerated. |
| RR-05 | ACCEPT — R-6, M-7 | P §3 R-6; `S11`; `engine.py:696-728,1221`; RS M-7 | **APPLIED.** I reproduced the defect independently: `convergence_score([0,1,1], full support)` → 0.0 (S11 in my run). R-6 as specified is AMENDed in B below (RRV-03/08), not rejected. |
| RR-06 | ACCEPT | P §1b rows 17-18; R-4; `S13` | **APPLIED.** I read `ka_sangam.py:49-114` (:50 definition, 0.2/0.2 admitted weights, no-op on `None` service, per-window exception-swallow) and the calls after `mode_a_search` (:667→:682) / `mode_b_sweep` (:695→:708). C9 (`engine.py:210-224`) and benefic dṛṣṭi (`:442-482`, `_ASP_WEIGHT` at :460) both named in R-4 and §1b 18. |
| RR-07 | ACCEPT — two axes | P §3 E6; RS D-2 | **APPLIED**, with one pinning gap (RRV-13: censored windows' treatment in the interval denominator unstated). |
| RR-08 | ACCEPT — §6.3 rewritten | P §6.3; `ka_bhavishya_lekha.py:119-120` | **APPLIED as text.** Real columns verified — the SELECT at `pipeline/orchestrator/writers/ka_bhavishya_lekha.py:119-120` selects `outcome_recorded, outcome_notes`. Id-keyed manifest, attack list incl. unchanged-count content-swap, FK-free `top_anchor_id` resolved semantically. Residual: canonical-framing field-exclusion list unpinned (RRV-09). |
| RR-09 | ACCEPT — S8 v2.1 | `S8_saturn_loop_oracle.py`; my OUTPUT provenance line | **APPLIED.** My run: `requested flags 65794, returned 65858 → SWIEPH; .se1 sha256[:16]={'seas_18.se1':'a2cd8fc33807c78c','sepl_18.se1':'ca1393ceab3a44fb','semo_18.se1':'1ca07bd67c24374d'}`. Exactly 3 SR→SD loops, 3/1 crossings, inside points 347.107°/0.201°/13.601° matching §3b E5's 347.11/0.20/13.60. `NOT_RUN(3)` on Moshier verified by code read. |
| RR-10 | ACCEPT — 7×6 matrix + sentinel | P §6.2 | **APPLIED as obligation** (matrix adopted verbatim; sentinel "per changed meaning" stated as owed). Residual: two consumers missing (RRV-04). |
| F-03 / F-12 / F-14 / F-16 / F-17 / A-01 / A.3 / D.1-D.3 / E.1 | ACCEPT (= RR-02 / RR-07 / RR-04 / R-4 / §6.2 / §1 / E1 / §4 / §6.2 / §3b) | as cross-referenced | **APPLIED** — spot-verified each anchor in P: F-12 (§4 step 2 R-5-in-harness first), F-16 (both generic currents in R-4), F-17 (per-E accounting §6.2), A-01 ("No longer 'unconditional'" at P:151-155), A.3 (two-labels-one-root; "never under Parāśari" withdrawn at P:202-204). |
| A.4 row 5 | ACCEPT — lagna defaults to Aries | P §1b row 5; `S12`; `ka_sangam.py:1143-1166` | **APPLIED.** I read the source: `lagna_sign = 'Aries'` at :1149 with docstring "Falls back to Aries (this native's lagna) on any query failure" at :1147; exception path retains the default. |
| A.4 row 8 | ACCEPT — `[U]` | P §1b row 8 | **APPLIED.** |
| A.4 row 11 | ACCEPT — prerequisite | P §1b row 11; R-3 | **APPLIED** — and this is the seed of RRV-02. |
| A.5 mutation results | ACCEPT — all 13 fail under NEG=1 | per-script, see A.3 | **APPLIED and independently re-verified by me** — including adversarial mutations beyond the built-in controls (real-function patches to S5/S6/S11; source-text mutations to S1/S3/S12/S13). Details in A.3. |
| E.2 reviewer self-correction | ACCEPT — priority.ts | P §6.2:348-350 | **APPLIED**, including my own v0.1 overstatement correction. |
| D.1 companion amendments | ACCEPT — §7 | B changelog v1.3 | **APPLIED** — all seven items recorded in B v1.3 (:503-509). Residual: B v1.5 changelog carries a stale number (RRV-07). |
| F verdict — fit for rulings | ACCEPT | RS §RULINGS + §CLOSE | **APPLIED** — the rulings happened; §0R applies them. |

### A.2 Every [C] in plan §1 and every §1b row

All checked at file:line in `platform/python-sidecar/` (this worktree's copy; `readiness/platform/python-sidecar`).

| Claim | Verdict | My verification |
|---|---|---|
| §1 kernel erases adverse activity (`engine.py:696-728, 1221`) | CONFIRMED | Read :696-728 (strict product × saturating support) and :1221 (`necessary = [dignity_score, orb_s, vedha_factor]`). S11 reproduces 0.0 / 0.0524. |
| §1 lagna defaults to Aries (`ka_sangam.py:1147-1163`) | CONFIRMED | :1149 assignment, :1147 docstring, exception path retains. |
| §1 post-engine TRIGGER (`ka_sangam.py:49-114`; calls `:667`/`:695`→`:682`/`:708`) | CONFIRMED | Read :50-109 and the two call sites; weights 0.2/0.2 at :46-47 area; `gochara_service is None → return windows` no-op. |
| §1 generic angular currents (`engine.py:210-224`, `442-482`) | CONFIRMED | C9 transit-to-transit `[0,60,90,120,180]` at :213; `_ASP_WEIGHT = {0:1.0, 60:0.7, 90:0.2, 120:1.0, 180:0.5}` at :460. |
| §1 ephemeris provenance (S8) | CONFIRMED — **and stale in text** | My run is SWIEPH (RRV-10): §3b fixture policy and §9.5 still assert Moshier. |
| §1 Mode B magnitude threshold (`engine.py:1400-1404`) | CONFIRMED | Orb gate at :1400, `magnitude = dignity_score * orb_s` threshold at :1403-1404; writer passes 0.3 at the `mode_b_sweep` call. |
| §1b 17 (TRIGGER composition) | CONFIRMED | As above; `TG:314-329` removal note not re-verified (not load-bearing). |
| §1b 18 (generic currents) | CONFIRMED | As above. |
| §1b 2/5/6/8/11/13 | CONFIRMED by this and both prior reviews; row 6's producer claim re-verified at `ga_strength_writer.py:1026` (`bav.get(planet_name, [0] * 12)`) and :1032-1036 (both keys from same `float(bindus)`). | — |

### A.3 The suite: per-script mutation result and false-SUITE-PASS analysis

My run: `OUTPUT_2026-09-23T051310.txt` — **13/13 positive exit 0; 13/13 negative controls exit 1;
SUITE-PASS**. S8 on SWIEPH with checksums.

| Script | Built-in NEG mechanism (code-read) | My independent mutation | Verdict survives mutation? |
|---|---|---|---|
| S1 | `if NEG: b = [(1,'x')]` (pretend binder emits target) | Removed the engine default from in-memory source text → FAIL | No — flips correctly. |
| S2 | `expect_equal = (g == "Jupiter") ^ NEG` | Arithmetic identity; mutation flips Jupiter expectation | No. |
| S3 | `if NEG: same_val = False` | Replaced `float(bindus)` with `0.0` in producer source text → proposition (a) FAIL | No. |
| S4 | `if NEG: expect = bound` | Arithmetic counterexample | No. |
| S5 | `f = lambda p,a: 29.46` | **Patched the real `E._rarity_years` to a constant** in an isolated subprocess → `VERDICT: FAIL` exit 1 | No. |
| S6 | `key = lambda iv: ('same',)` | **Patched the real `DS._build_overlap_key` to an intersection-aware key** → FAIL | No. |
| S7 | `if NEG: appends, rets = [], [1]` | AST-structure evidence; NEG flips both propositions | No. |
| S8 | `if NEG: co = 3` | Ran on SWIEPH; Moshier path exits NOT_RUN(3) — verified by code read | No (and refuses to be an oracle on fallback). |
| S9 | `if NEG: m = []` | Exact-line grep; NEG empties | No. |
| S10 | `if NEG: n = []` | Exact-line grep; NEG empties | No. |
| S11 | `f = lambda nec, sup: 0.5` | **Patched the real `E.convergence_score` to a constant** → FAIL | No. |
| S12 | `if NEG: d = []` | Removed `lagna_sign = 'Aries'` from in-memory source text → FAIL | No. |
| S13 | `if NEG: calls = [(1,'x')]` | Renamed the composition call in source text → FAIL | No. |

**Can the runner be made to report SUITE-PASS falsely?** Two answers, tested/derived:

1. **Sincerity escape — YES, structurally possible (RRV-15).** I wrote a synthetic script that hardcodes `if NEG: exit(1)` and tests nothing: positive exit 0, NEG exit 1 — the runner would report SUITE-PASS. The manifest/runner checks *structure*, not that the negative control is evidence-bearing. Every on-disk script's NEG path genuinely mutates evidence (I read all thirteen), so today this is latent, not live. K3 flagged the same; it is acceptable **only** because per-step independent review is a standing stage-3 discipline. It must stay on that checklist, because the moment a future script authors its own NEG path lazily, the §N.8 defect returns wearing the harness's clothes.
2. **Truncation/verdict forgery — NO.** The verdict is computed from exit codes, not script output (a script printing "SUITE-PASS" changes nothing); the OUTPUT filename is timestamped to the second and `[ -e "$OUT" ]` refuses overwrite (exit 2); script failures propagate via `fail=1`; the manifest is read line-by-line with missing files failing the suite.

## B. R-1…R-6 and E1–E6

### R-1 Target binding — AGREE

Provenance-not-value is the right test; the relational-detector carve-out answers my F-01; the
sourced-0° valid / defaulted-0° invalid SPEC is correct. Nothing further.

### R-2 Clock intersection — AGREE

Intersection-segments-with-supporter-sets is the right oracle; evaluated-empty vs unavailable is
the right distinction. Nothing further.

### R-3 Frame and identity — AMEND (one line, not a redesign)

The (a)/(b) split is right. The gap: **R-3's own prerequisite — "the scanner signature amendment" —
is the same upstream artifact that M-3 gates on N-7, but §4 step 3 schedules R-3 as unblocked.**
Under the plan's rule ("a SPEC that cannot be made runnable at its step blocks that step"), SPEC R-3
blocks step 3, not just E1/E3. Same for R-4 (below). Amend §4 step 3 and §0R M-3 to state: R-3/R-4
detector SPECs gate on the same N-7/owner decision as E1; if N-7 is refused, the named Path-A owner
must exist before step 3's detector work is scheduled. Related: the mean-node convention (M-1) also
cannot reach the scanner (hardcoded `TRUE_NODE`, `transit_search.py:10,64`) until that amendment
lands — worth one explicit line so M-1 is not read as executable in Saṅgam today (RRV-16).

### R-4 Detector and current audit — AMEND

The audit list is right (C8 target, C11 proposition-specificity, C9/benefic-dṛṣṭi assignment,
I-17 requalification, producer receipt). Two amendments: (i) same N-7/owner gating as R-3 for the
occupancy/tangency/edge SPECs; (ii) the missing-planet AV receipt is a **producer** amendment in
`ga_writers/ga_strength_writer.py` — see RRV-01: the stage-3 brief's `may_touch`
(B frontmatter :16-20) does not include that file, and the GA writer surface sits under the frozen
orchestrator contract (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2). Name the owner and the bounded
change (a completeness/validity receipt column set — no numeric change) or this "now, not deferred"
item has nowhere to land.

### R-5 Identity and history — AGREE, with RRV-09

Harness-first before any contact-changing implementation is the correct order, and D-7's
"withdrawn only on the R-5 successor manifest" is the right retirement condition for the legacy
scan. The §6.3 test design is the right shape (see §6.3 assessment in C). It needs the
canonical-framing amendment (RRV-09) to be *executable* rather than merely well-written.

### R-6 Score-kernel separation — AMEND (right correction, three gaps)

**Is activity·valence·applicability·availability the right correction? Yes.** It maps the
classical bala/phala distinction; dignity-as-valence is verse-backed (BPHS 47.3-4: effects
"in accordance with their strength" — a weak lord delivers trouble, not silence; Phaladīpikā
23.23-24 composes valence from nature × dignity × lordship; I verified 47.3-4 verbatim at
BP2:8939-8950 and the drekkāṇa phasing it carries). S11 proves the defect is real and kernel-level.
Three gaps:

1. **Serving-order contract missing (RRV-03, HIGH).** R-6 removes the only rankable scalar and
   says "consumer projections choose fields explicitly." But every consumer cut is an ORDER BY
   (`ka_kala_darshana` LIMIT 750, `ka_vighnakara` 500, serving default 30/max 200, `ka_tulana`'s
   composite). Projections define columns, not order. Stage 3 will either reintroduce a hidden
   composite (the RR-05 defect reborn) or ship nondeterministic cuts. Fix: one declared
   within-class ordering key per `comparability_class` (e.g., `activity DESC` within class,
   valence/availability carried as data, never pooled into the key); SPEC R-6 asserts two
   identical-activity rows of opposite valence both survive to a served page.
2. **The static daśā prior bypasses availability (RRV-08, MODERATE).** `engine.py:1108`
   (`eligibility_score` default 0.5) and `:1142` (`return best if best > 0.0 else
   static_dasha_score`) manufacture a neutral **supporting** contribution when eligibility
   fails/empties — and S10 verified the daśā enters as `constituent_lord_transit` support. Under
   R-6 that is an availability state, not support. SPEC R-6 must add a fixture: eligibility service
   fails → zero manufactured support, `availability.dasha = unavailable`.
3. **Legacy/new coexistence must be enforced in SQL, not policy.** "Never pooled or ranked" must
   materialize as `comparability_class`/`kernel_version` partitioning in every consumer query —
   the companion's §4.4 partition rule is the enforcement vehicle; make it an R-6 acceptance item,
   not a companion-side obligation.

### E1 — AMEND: the two-labels-one-root resolution is sound; guard the angle family

On the pushed question: **"same geometry, two labelled evaluations, one root" resolves the A.3
problem only if the contracts own their angle families, strengths, and orbs.** As written it does
not smuggle the Western list back in — the plan requires directed search (`target − angle`, S2
verified), sign applicability surviving without exact perfection, degree strength per BPHS 26.6-8
(I verified 26.2-5 verbatim at BP1:16500-16501: "All planets aspect the 7th fully. Saturn, Jupiter
and Mars have special aspects respectively on 3rd and 10th, 5th and 9th, and 4th and 8th."), and
one-root lineage. The residual smuggle-path is the angle list itself: nothing asserts that a
Parāśari-labelled evaluation may not carry 60°/90° (Tājika families) or that Tājika may not reuse
Parāśari strength values. Add to the E1 falsifier: the emitted angle set per contract is asserted
(Parāśari: 7th for all + 3/10 Saturn, 5/9 Jupiter, 4/8 Mars, fractional slabs; 60/90 only under a
Tājika label with Tājika strengths/orbs). Otherwise a future edit can silently widen the common
list and the labels become wallpaper (RRV-14).

### E2 — AMEND: frame settled (verified); producer receipt needs an owner

The frame is **settled** — I verified `ga_strength_writer.py:968-980` ("absolute-**rāśi**-indexed
(index 0 = Aries)… ADDS, from the SAME bindu values (NO recompute)") and :1026-1036. It is not an
open question and the plan correctly says so. The producer completeness receipt is the right
repair for RR-02's zero-provenance loss — but it lives in a file stage 3 may not touch (RRV-01).
Amend before code: bounded scope item or L1-owner packet, with the receipt's physical shape pinned
(table/columns) so the E2 SPEC can target it. Doctrine ledger (bindu/rekhā mapping, three-state
verdict, 4 = indeterminate-leaning-adverse, bands school-labelled) is verse-backed — I verified
BPHS 66.13-15 (bindus = inauspicious dots, rekhas = auspicious lines) at BP2:35666-35676, BPHS
72.3-5 (>30/25-30/<25 rekhas) at BP2:42332-42354, and Phaladīpikā 23.11 at `phaladeepika:PG299:C1`
— OCR "Sloka 77" — with 3 and 4 both reading "fear", the 0-dot "lose his life" clause present, and
the 1-8 enumeration exactly as the sheet quotes. K2-06's retraction is correct.

### E3 — AMEND: same N-7 gate; carry the corrected vedha standing

Scope/families/no-cap/resumable-incomplete are right. Two amendments: (i) like R-3/R-4, E3's
children come from the same gated producer — the "E3 waits on N-7" note covers scheduling but the
plan should say the SPEC is unrunnable until then (it does say this generically; make it explicit
at §4 step 6); (ii) the ruling sheet's §Corrections item 2 upgraded laṭṭā and the malefic scale to
corpus-verifiable today (`PG338:C1` Saturn/Rāhu/Ketu laṭṭā table, `PG339:C1`, `PG353:C1` — I
verified all three at the table), so plan §3 E3's "reuse the served vedha/laṭṭā producer" should
carry the per-`vedha_kind` qualification outcomes rather than the pre-correction blanket. I
verified the table-level vedha counts the sheet cites: phaladeepika 17, sarvartha_chintamani 5,
uttara_kalamrita 5, bphs 2, muhurta_chintamani 1, yavana_jataka 1 (exact SQL in my session log).

### E4 — AGREE

Gates withdrawn, typed conditions, no veto, per-clock/level/parent/lord boundary annotation with
the drekkāṇa rule (verified BP2:8939-8950), capability cited-never-re-voted. This is my v0.1 F-07/F-08
replacement and it is correctly specified. D-4's three-part gate (contract pinned; falsifier in
MANIFEST before any D30 row; scope covers served surfaces and consumer SQL) is the honest shape —
note it remains an intention until executed (the MANIFEST today has 14 lines, zero D30 entries; I
verified).

### E5 — AMEND: occupancy union is necessary; absorb the ruled aggregation unit and aborted approaches

Occupancy = union of child intervals is the right occupancy semantics, and with the aggregation
unit pinned it **is** sufficient for `ka_taranga` — because the unit the sheet's M-5 resolution
rules ("occupied-day union per month per (contract × valence-sign)", RS :334) is mechanically
checkable (duplicate-insertion invariant by construction, partial months respected). But plan §3
E5 still presents the unit as an open choice among "occupied duration / episode / route" — a direct
contradiction of the sheet's own resolution row (RRV-05) — and omits the ruled aborted-approach
children (approached, never perfected; sign-level applicability survives) entirely (RRV-06). Also
unpinned: the timezone that bounds the "month" (an occupied-day union computed in IST vs UTC
splits different months). Fix: pin the ruled unit and aborted-approach children in §3 E5 and the
§3b E5 falsifier; declare the month-boundary tz. S8's oracle points I re-ran on SWIEPH (3 loops,
3/1 crossings) — as the plan itself says, crossings are points, not orb-interval occupancy; the
disjoint-vs-continuous SPEC remains the real E5 test.

### E6 — AMEND: two axes AGREE with RR-07; pin two loose ends

The two-axis record (immutable claim × `observation` × `derivation`) is exactly my RR-07 and is
correctly specified — an invalidated derivation neither erases nor converts an observation. The
exposure manifest with strata, and "complete for the declared estimand" (vs my v0.3 "E6 estimand-bound
coverage" replacement), are right. Two loose ends: (i) D-2's interval `[hits/all,
(hits+ambiguous)/all]` never defines "all" — censored and unobserved windows' treatment in the
denominator is unpinned, and different strata could compute the interval over different universes
(RRV-13); (ii) D-1's measured-issuance-rate detector is a genuine §N.8 improvement — keep it, and
have the stage-3 exposure manifest define "fully observed" against outcome-collection lag, or n=100
will be reachable on paper before it is reachable in fact.

### §6.3 — can the id-keyed manifest with the seven attacks prove historical integrity?

**It can prove preservation across a candidate generation in a faithful harness; it cannot, by
itself, prove historical integrity in production.** Three limits, two fixable in text: (i)
"compare exact content per id" needs a canonical serialization with an explicit field-exclusion
list (row id, `computed_at` legitimately change; JSONB framing) — otherwise the comparison either
fails benign rebuilds or is loosened until a swap passes, which is the unframed-hash attack one
level up (RRV-09); (ii) harness success ≠ production cascade behaviour — schema drift, concurrent
serving reads mid-generation-switch; run against a schema-faithful disposable DB; (iii) the
dependent map omits `mimamsa_convergence_adjustment` — see RRV-04. With those three amendments the
design satisfies RR-08; without (i) it does not.

## C. What the author missed

Ordered by leverage. Items 1-4 are the HIGH findings.

1. **RRV-01 (HIGH) — E2's producer receipt has no authorized hand.** Plan §3 E2 mandates a
   producer amendment "now, not deferred"; the only file that can provide it
   (`ga_writers/ga_strength_writer.py`) is outside the stage-3 brief's `may_touch` (B frontmatter
   :16-20) and sits under the frozen orchestrator contract. Stage 3 would hit this wall in week
   one. Fix: bounded `may_touch` addition (receipt columns only, no numeric change) or an L1-owner
   packet, with the receipt's physical shape pinned.
2. **RRV-02 (HIGH) — Step 3 is silently gated on N-7.** R-3's scanner amendment and R-4's
   occupancy/tangency/edge detectors are the same upstream artifact as E1's geometry. §4 shows
   step 3 unblocked; the plan's own block-the-step rule says otherwise. Fix in text: step 3's
   detector SPECs gate on N-7/owner; name the Path-A fallback owner (K3 Q9#1 asked; nobody has
   answered).
3. **RRV-03 (HIGH) — No within-class ordering contract post-R-6.** Every consumer cut is an
   ORDER BY; R-6 supplies fields but no order. Without a declared per-class ordering key, stage 3
   reintroduces a hidden composite or ships nondeterministic top-N. Fix: ordering key per
   `comparability_class` in R-6 + SPEC assertion.
4. **RRV-04 (HIGH) — Two consumers of `kala_convergence` the plan never names.** The companion
   itself measures them (B §2.5): **`mi_adhilepa` (L5)** — `SELECT convergence_id … LIMIT 500`
   with no ORDER BY feeding a calibration multiplier (`pipeline/orchestrator/writers/mi_adhilepa.py:297`),
   binding to the volatile surrogate id the companion's §5.2 calls the root cause; and
   **`ph_nimitta` (L4)** — per-domain `ROW_NUMBER` at :340 and a nearest-peak `LIMIT 1` attach at
   :710. E5's regrain changes row counts and surrogate ids under mi_adhilepa's overlays; E1/E5
   peak moves silently reattach ph_nimitta. Neither appears in §6.2's seven. Fix: add both (and
   the `UNRESOLVED_USE` list: `mi_kula`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`,
   `taranga_kernel`, `ka_temporal/date_resolver`, `kala_temporal.ts`) with per-E dispositions;
   mi_adhilepa's surrogate binding is an R-5 dependency, not an afterthought.
5. **RRV-05 (MODERATE) — Ruled taranga unit missing from plan E5** (see B/E5).
6. **RRV-06 (MODERATE) — Ruled aborted-approach children missing from plan E5.**
7. **RRV-07 (MODERATE) — Stale gate numbers in the companion changelog.** B v1.5 (:499) records
   "E6 gate numbers set (30 per stratum / 100 pooled)" — the pre-K2-01 figures. Amended D-1 is
   35/crit≥12/α=0.0344/power 0.805; I reproduced all four gate triples exactly (`math.comb`):
   n=30 crit≥10 → α=0.0611 (the K2-01 defect); n=35 crit≥12 → α=0.0344, power 0.8048 — and 35
   is indeed the smallest n meeting α≤0.05 ∧ power≥0.80; n=100 crit≥28 → α=0.0342, power 0.8325.
   One-line changelog correction; the exact failure class K2-01 caught, reappearing in the
   changelog of the document that recorded the fix.
8. **RRV-08 (MODERATE) — static daśā prior bypasses availability** (see B/R-6).
9. **RRV-09 (MODERATE) — §6.3 canonical framing** (see B/§6.3).
10. **RRV-10 (MINOR) — Stale ephemeris text.** P §3b fixture policy (:276-278) and §9.5 (:407-408)
    assert "Swiss Ephemeris here runs Moshier"; my run is SWIEPH with checksums (the `.se1` files
    landed 2026-09-22 17:20 at `/tmp/se1`). Fixtures labelled "Moshier stated" under-claim current
    provenance; restate as environment-dependent with the backend detector authoritative.
11. **RRV-11 (MINOR) — K2-08 markers partial.** §0R markers landed for M-1 (:44) and M-4 (:48) but
    not M-2 (:45 — "producer completeness receipt now; kakṣyā deferred; Kshetra S1 shares the
    source" are author-layer, unmarked).
12. **RRV-12 (MINOR) — K2-05 reconciliation half-done.** The evidence pointer moved to the SWIEPH
    run, but the policy question — which assertions may run on Moshier (sheet: logic may, with
    backend recorded; S8 v2.1: nothing) — is nowhere written. Not a contradiction (permissive vs
    stricter); one line settles it.
13. **RRV-13 (MINOR) — D-2 interval denominator unpinned** (see B/E6).
14. **RRV-14 (MINOR) — E1 angle-family assertion missing** (see B/E1).
15. **RRV-15 (NOTE) — NEG sincerity escape**, confirmed by me with a synthetic no-evidence script
    (A.3). Structural; managed by review discipline, not code.
16. **RRV-16 (NOTE) — mean-node ruling not executable in Saṅgam today**; scanner is hardcoded
    TRUE_NODE (`transit_search.py:10,64` — verified). One explicit line in §0R M-1/M-3 prevents
    the ruling being read as already-landed.

## D. Sequencing, P4, lineage

**§4's order is correct** — companion amendments → R-5 in the disposable harness before any
contact-changing implementation → R-1…R-4/R-6 → E1/E2 then E5 → E4 with the annual-Tājika gate →
E3 after the integrated ruling and cost experiment → E6 last, with claim preservation beginning at
step 2. R-5-in-harness-first is the load-bearing fix and it is where my v0.3 said it must be. The
one correction: step 3's detector work is gated on the same N-7/owner decision as E1 (RRV-02) —
the sequence is right, its gating annotations are incomplete.

**Does §6.2's per-E accounting satisfy "reduced caps cannot pass as equivalent"?** At the
accounting level, yes: the per-E applicable/selected/served rows (E1 manifest predicate × method ×
target; E2 every ingress; E3 parent coverage + child enumeration; E4 domain × clock × condition;
E5 every old contact's child/supersession disposition; E6 exposure-manifest invariance to page
size/top-K/duplicates) plus the companion §4.4 equivalence contract (Σ partition floors ≥ current
budget; any reduction declared as semantic change) are exactly P4's demand. The hole is downstream
of accounting: with R-6 removing the composite scalar, "equivalent serving" is undefined until the
within-class ordering contract exists (RRV-03). P4 is not satisfied at the serving layer until
that lands.

## E. Ecosystem

§6.2 **does** adopt the 7×6 matrix and **does** carry my `priority.ts` correction (P :348-350 —
`call_priority_ranking` → `WRAP:673-711` joins `kala_activation`, not `kala_convergence`; declare
non-consumption or an authorized new route). The load-bearing cells (darśana's
`confidence_label`/`rarity_years` SQL break; tulana's 40/25/20/15 composite — redesign not
relabel; bhaviṣya's signal/peak key and rarity narrative) are correctly identified as obligations.

**Consumers whose SQL breaks/changes that the plan still doesn't name (RRV-04):** `mi_adhilepa`
(L5 calibration overlays on the volatile `convergence_id`, unordered LIMIT 500) and `ph_nimitta`
(L4 nearest-peak attach) — detailed in C. The plan names seven consumers and served surfaces; its
own companion measures nine direct readers. The matrix must be reconciled with B §2.5's census
before E5/E6 land, and `mimamsa_convergence_adjustment` must join the §6.3 dependent map.

## F. Verdict

**PROCEED_WITH_AMENDMENTS** — stage-3 code execution opens when RRV-01…RRV-09 are dispositioned in
the plan/brief text (all are text/scope amendments; none requires re-ruling; none touches the
native's M-1…M-7). RRV-10…RRV-16 may land in the same pass or be carried as stage-3 checklist
items, with RRV-15 standing as a permanent discipline.

**Why not REWORK:** the two prior REWORKs' central demands are met and I verified them
independently — the suite now fails when mutated (13/13, re-run and re-mutated by me), the
falsifiers test what they claim, the corpus grounds are re-queried, the rulings are coherent with
the plan, and the K3 amendments are real. A third REWORK would punish the one thing this campaign
set out to reward.

**Why not unconditional PROCEED:** RRV-01 and RRV-02 would stall stage 3 within its first week
(scope wall; unnamed gating); RRV-03 and RRV-04 are semantic holes at the serving layer that the
accounting cannot paper over. These are exactly the class of defect this gate exists to catch
before code, not after.

### K2-01…K2-12 verification (this review is the designated place)

| # | Landed? | Evidence |
|---|---|---|
| K2-01 (α arithmetic) | **YES** | Plan §0R M-6 (:50) and RS D-1 carry n=35/crit≥12/α=0.0344/power 0.805 and n=100/crit≥28/α=0.0342/power 0.833; I reproduced all triples exactly. Residual: RRV-07 stale changelog. |
| K2-02 (independence) | **YES** | "First-order approximations", chart-level concordance, published overdispersion check — RS D-1 and plan §0R. |
| K2-03 (D-2 vs M-6 record) | **YES** | D-2 amended with the interval whose adverse end is condition 4 verbatim; supersession explained without touching the native-adjacent rule. |
| K2-04 (D-4 detector) | **YES as gate** | D-4 restated (i)-(iii): contract pinned before any D30 row; falsifier in MANIFEST before first D30 row; scope covers served surfaces and consumer SQL. MANIFEST verified: 14 lines, zero D30 entries — an intention, correctly described as one. |
| K2-05 (stale pointer) | **PARTIAL** | Pointer fixed (frontmatter cites the SWIEPH run). The sheet-vs-script policy reconciliation unwritten (RRV-12). |
| K2-06 (false [U]) | **YES** | Retracted in RS `verification_by_author`; I independently confirmed PG299:C1 carries the 0-dot clause and the "fear"/"fear" enumeration. |
| K2-07 (177″ label) | **YES** | Both quantities published named (3658.3″ convention gap; 177.3″ boundary margin). I reproduced both: 50.049248−49.033044 = 1.016204°; 50.049248−50° = 177.3″. |
| K2-08 (§0R markers) | **PARTIAL** | M-1 and M-4 rows carry [N]/[A]; M-2 row does not (RRV-11). |
| K2-09 (count + registration) | **YES** | Count fixed (254 rāhu/ketu lines; 270 with `node` — I re-grepped the OCR: 0 occurrences in span 16457-18361, 254/270 file totals). DIS.031 entered and corrected (`68b0fd09d`); my own query confirmed the register's predicate-level amendment (below). |
| K2-10 (Simpson) | **YES** | Stratified CMH-type primary estimand predeclared; raw pooled demoted to secondary. |
| K2-11 (censoring) | **YES** | Adverse-end interval + 10%/20% gradient replace the cliff. Residual: RRV-13 denominator pinning. |
| K2-12 (base rate) | **YES** | Null comes from the exposure model a priori. |

**New-evidence verification (DIS.031 amendment, `amendment_2026_09_23_predicate_level_recheck`):**
the claim is **CONFIRMED by my own query**. Exact SQL from the ruling sheet §Corrections item 4
against `classical_text_chunks`: 100 chunks (phaladeepika 89, saravali 11 — I reproduced both
counts). I read every returned row: Rāhu/Ketu appear as occupants, dāsa lords, transit agents
(Adh. XXVI 12th-house table `PG331:C1`, laṭṭā `PG338-339:C1`, SBC vedha-direction `PG348:C1`),
and as *targets* of generic malefic aspect language (e.g., Sārāvalī PG30:C2, PG35:C1) — **never as
aspect-grantors**; no 5th/9th grant, no special-aspect grant of any kind. Closest analog:
`phaladeepika:PG133:C1` "Rahu is similar to Saturn and Ketu to Mars" — a results-analogy in Adh.
IX, not a dṛṣṭi rule (this is the classical seed of the later-tradition practice w30's docstring
admits it draws on, and why "not found in these two texts" must not be over-read as "not in the
tradition" — the register's stated limit). The upgrade of the absence ground from ATTRIBUTED to
CONFIRMED (subject to the amendment's own OCR/400-char limits) is warranted. D-6 stands on four
grounds; N-14 remains the Gochara stream's to rule.

### Ruling/plan contradictions found

Four, precisely named:

1. **RRV-05** — RS M-5 resolution (ruling sheet :334) rules the `ka_taranga` aggregation unit
   ("occupied-day union per month per (contract × valence-sign)"); plan §3 E5 (:240-241) still lists
   the unit as an open choice. §0R's "M-5 → E5 as written" cannot be true of both texts.
2. **RRV-06** — RS M-5 resolution binds "aborted approaches kept as labelled children"; plan §3 E5
   contains no aborted-approach provision.
3. **RRV-07** — companion v1.5 changelog records "30 per stratum / 100 pooled"; amended D-1 and
   plan §0R carry 35/crit≥12. Stale record contradicting its own packet.
4. **RRV-10** — plan §3b fixture policy and §9.5 assert the local Swiss engine "runs Moshier"; the
   plan's own cited OUTPUT (and my run) is SWIEPH with checksums. The environment changed under the
   text; the fixture policy must be re-anchored to the backend detector.

None is a contradiction among the native's rulings; all four are author-layer text that disagrees
with the packet's own corrected record. Each is a one-line-to-one-paragraph fix.

---

**Scope and authority.** Read-only review. Executed: corpus SQL (read-only), the evidence suite
(new timestamped OUTPUT only), in-memory/subprocess mutation tests, source reads at the cited
lines, arithmetic reproductions (binomial gates, D-5 quantities, S4 counts). Not executed: no
build, no migration, no production DB write, no L4/L5 touch, no fetch of the remote tip. Live
incidence of every defect remains `[U]`; what this review establishes is source reachability,
harness behaviour, corpus text, and arithmetic. This review authorizes no implementation, ruling,
rebuild, deployment, or acceptance; the stage-3 gate condition is stated in F and belongs to the
native/author to discharge.
