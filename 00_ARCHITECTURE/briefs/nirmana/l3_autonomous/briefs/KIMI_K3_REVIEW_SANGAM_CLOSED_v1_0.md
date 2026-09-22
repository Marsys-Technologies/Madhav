---
title: "KIMI_K3_REVIEW_SANGAM_CLOSED_v1_0"
version: "1.0"
status: COMPLETED_EXTERNAL_REVIEWER_OUTPUT
role: reviewer_output
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
verdict: ACCEPT_WITH_CONDITIONS
findings: "K2-01…K2-12 (4 MAJOR, 5 MINOR, 3 NOTE)"
description: "Verbatim Kimi K3 (effort=max, Kimi CLI) adversarial review of the CLOSED Saṅgam packet — plan v1.0/v0.4 and the author's delegated decisions D-1…D-8. Not authored by this session; frontmatter prepended for gate parity, body unchanged."
generated: "2026-09-23T03:54:13+05:30 → 04:29:50+05:30 via: kimi -m kimi-code/k3 --output-format text -p <KIMI_REVIEW_PACKET_SANGAM_CLOSED_v1_0.md>; k3 default_effort=max, thinking.effort=max (config verified by TOML parse, restored after)"
author_verification: "K2-01 arithmetic reproduced exactly (P(X≥10|Bin(30,0.2))=0.0611, power=0.8237; α≤0.05 needs crit≥11→power 0.7085). K2-07 reproduced (177.3″ = true-node margin past the pāda 3/4 boundary; 3658.3″ = 1.016204° = the mean↔true convention gap). K2-06 confirmed — the sheet's [U] is false; this session's own earlier DB query returned the clause verbatim. K2-04 confirmed — MANIFEST holds 14 lines, zero D30/DOSHA entries. K2-05 confirmed — plan cites OUTPUT_2026-09-22T2342*; OUTPUT_2026-09-23T012041.txt exists. K2-03 confirmed — the sheet's M-6 record does carry 'ambiguous stays in the denominator, fraction disclosed'."
---

• I'll take this review. Per the repo's bootstrap, I first read `CLAUDE.md`, then the packet. Let me scope the files.

• I have the three core documents. Now the v0.3 plan and the evidence harness, in parallel.

• Now the verification layer: outputs, database, and the code lines the packet cites — in parallel.

• All verification I can reach is done. The postgres connector died after my first two queries (ECONNREFUSED on every retry), so the remaining table-level claims are tagged as not-re-verified in the closing section. Here is the review.

  ---

  # K2 review — Saṅgam CLOSED packet (plan v1.0 = v0.4 + §0R, D-1…D-8)

  Verdict up front: **ACCEPT_WITH_CONDITIONS** — five conditions, all in the delegated decisions, none requiring re-ruling. Detail below, questions in order, findings K2-01…K2-12, closing separation of verified vs asserted.

  ---

  ## Q1 — Did v0.4 actually close the v0.3 REWORK?

  I walked all ten RR findings against the v0.4 text (confirmed byte-identical to v1.0 below §0R by diff), the ASTRA review's "Replace with" demands, the evidence harness, and the code. **Nine closed, one partially closed — and the closure is real, not cosmetic.**

  - **RR-01 — CLOSED, verified by running the mechanism's logic myself.** RUN_ALL.sh v2 reads MANIFEST.txt, requires exit 0 positive AND nonzero under `NEG=1`, refuses to overwrite prior output, exits nonzero on any failure. `_common.py`'s `prop()`/`done()` makes every verdict a function of recorded assertions. Both OUTPUT files show 13/13 positive pass + 13/13 negative controls failing. S11 calls the real `convergence_score`; its NEG substitutes a constant — the mutation test RR-01 demanded. Residual honesty note: the NEG control is a per-script *convention*; a script could hardcode `if NEG: exit(1)` and the runner would not know. The harness enforces structure, not sincerity — that last mile is review, not code. Acceptable.
  - **RR-02 — CLOSED, output verified.** S3 v2 asserts the real producer: HOUSE_N/SIGN_N from the same `float(bindus)` (GS lines [1032]/[1035]), missing planet → twelve zeros ([1026]), reader on the legacy category ([1004]), Lahiri hardcode. The rotation story is explicitly withdrawn. E2 re-scoped to vocabulary/provenance/producer-receipt.
  - **RR-03 — CLOSED as text.** All nine SPECs replaced, and each replacement matches the reviewer's "Replace with" cell: sourced-0°-valid vs defaulted-0° (R-1); intersection segments not key-equality (R-2); occupancy/tangency/unavailable-vedha separated (R-4); one geometry two labels one root (E1); real GS output (E2); dated fixture with declared inputs (E3); hold-all-else-fixed (E4); orb intervals not crossings (E5); estimand-bound coverage (E6). These are SPEC-status (not yet runnable) — the plan's own rule ("a SPEC that cannot be made runnable at its step blocks that step") is the right backstop.
  - **RR-04 — CLOSED.** R-3 split into (a) geometry cache key / (b) testimony identity with the full field list the reviewer enumerated.
  - **RR-05 — CLOSED.** New R-6 (activity/valence/applicability/availability; dignity out of the necessary product), new M-7, S11 runnable. I verified the defect at source: `engine.py:1221` `necessary = [dignity_score, orb_s, vedha_factor]`; kernel at :696-728 is a strict product — dignity 0 → 0.0 with full support.
  - **RR-06 — CLOSED.** §1b rows 17–18 added; R-4 names C9 (`engine.py:210-224`) and benefic dṛṣṭi (`:442-482`, `_ASP_WEIGHT` at :460 — both read by me) for method/role assignment or withdrawal; S13 shipped (`ka_sangam.py:50`, calls :682/:708 after :667/:695, weights 0.2/0.2 at :46-47 — all verified).
  - **RR-07 — CLOSED.** E6 carries `observation × derivation` as two axes; invalidated derivation never erases an observation.
  - **RR-08 — CLOSED as text, execution owed by design.** §6.3 rewritten on the real columns — I verified `outcome_recorded`/`outcome_notes` are the actual columns at `ka_bhavishya_lekha.py:17,98,122` — manifest keyed by stable id, exact content, attack list including unchanged-count content-swap. The harness run itself is a stage-3 deliverable (the review demanded execution receipts a plan cannot contain).
  - **RR-09 — CLOSED, harness is now stricter than the review demanded.** S8 v2.1 on disk records backend + .se1 checksums, bisects stations to ~1 min, asserts exactly 3 loops and 3/1 crossings, and **exits NOT_RUN(3) on Moshier** — the review only asked for provenance + solved stations + expected counts. See K2-05 for the skew this creates with the cited run.
  - **RR-10 — PARTIALLY CLOSED (by design, but say it plainly).** §6.2 adopts the 7×6 matrix and the served table with the reviewer's own `priority.ts` correction (verified: `call_service_wrappers.ts:673-711` has zero `kala_convergence` references, joins `kala_activation`). The **material-field sentinel is an obligation, not a built detector** — it must be a stage-3 entry artifact, not a mid-stage discovery.
  - A.1 re-dispositions: all land. Spot-verified in v0.4 text: F-12 (§4 step 2 now gates R-5 in the disposable harness *before any contact-changing implementation*), F-14 (=RR-04), F-16 (both generic currents named in R-4), F-17 (§6.2 per-E applicable/selected/served table), A-01 (§1 "No longer 'unconditional': the 200/60 cap and self-scoped delete"), A.3 (E1 "same geometry may carry a Parāśari (fractional 4th) and a Tājika (square) evaluation, separately labelled, one root — the v0.3 'never under Parāśari' fixture is withdrawn"), D.1 (six-step order with R-5 gate; annual-Tājika scheduled contract at step 5), D.2/D.3/E.1/E.2 (§6.2, §4 lineage paragraph).

  **Q1 answer: yes — v0.4 closes the second REWORK as a plan.** RR-08/RR-10's execution receipts are correctly deferred to stage 3 and must be on its entry checklist. This is the first independent confirmation of that claim.

  ## Q2 — D-1's arithmetic and design

  **The power claims are right; the α claim is wrong; the instrument gate has no declared critical value; and the whole computation assumes independence the plan elsewhere disclaims.**

  Exact binomial computation (my run, `math.comb`):

  - **n=30 claim:** "α=0.05 one-sided, critical ≥10, ≈80% power for 0.20→0.40." Exact: **P(X≥10 | Bin(30,0.20)) = 0.0611**, power at p=0.40 = **0.8237**. So "≈80%" ✓, "α=0.05" ✗ — the stated critical value yields α = 6.1%. To actually hold α ≤ 0.05 requires crit ≥ 11 (α = 0.0256), which drops power to **0.709**. An implementer building from this text will ship a gate that differs from the text one way or the other (K2-01).
  - **n=100 claim:** "≈85% power for 0.20→0.32." No critical value is stated — itself a defect under M-6's own "predeclared protocol" condition. Exact: crit ≥ 27 → α = 0.0558, power = 0.882; crit ≥ 28 → α = 0.0342, power = 0.833. So "≈85%" is achievable, but only with a named critical value; as written the gate is underdetermined.
  - **"A smaller gate (n≈12) can only see a 3× lift"** — fair (n=12, crit ≥ 5: α ≈ 0.073, power at 3× = 0.94, at 2× = 0.67). Not a finding.
  - **Simpson's hazard — real, unfixed.** Pooling across `(domain × route)` strata with different base rates and exposures can produce a pooled lift no stratum has (composition shift) or mask a per-stratum lift. D-1 publishes per-stratum counts, which displays the problem but does not decide it. Minimal fix that keeps the gate reachable: predeclare a **stratified primary estimand** (standardized/CMH-type pooled lift, or equivalently "pooled lift AND no stratum with a significant opposite-sign deviation"), with the raw pooled number as the secondary display. Cheap, orthodox, and the per-stratum counts D-1 already mandates make it computable (K2-10).
  - **Was naming a number worse than declining?** No. Declining was right *for me* — the number sets the evidentiary bar of the instrument and belongs to the native's delegation chain, which is what happened. The defect is not that a number was named but that the named number's α is misstated, its critical values are half-declared, and its power math assumes i.i.d. Bernoulli windows on a **two-chart** population. Plan §4 says "No statistical independence is claimed"; D-1's power computation silently re-introduces it. With two subjects the effective n is far below the nominal n (intracluster correlation; two clusters). Minimal fix: declare the binomial calculation a first-order approximation and add a **chart-level concordance requirement** (the lift direction must appear in both charts independently, or a beta-binomial overdispersion check with the result published) — this costs nothing and is the difference between "30 windows" and "30 windows that mean what the formula thinks they mean" (K2-02).

  ## Q3 — D-1 vs D-3: is the gate self-defeating?

  **Per-stratum: unreachable on two charts in any realistic horizon — and the author already concedes it in D-1's own reasoning ("at ~16 strata, full per-stratum coverage is years out on a two-chart corpus… the instrument-level gate at n=100 is the reachable one and opens first").** Full per-stratum coverage needs ~16 × 30 = 480 fully-observed, non-censored, adjudicated windows from two lives; even at an aggressive ~50 issuable windows/chart-year that is ~5 years before censoring and adjudication lag. So Q3's premise is correct and, to the author's credit, pre-answered.

  Two things the concession does not cover: (a) the **instrument-level n=100 carries the same clustering defect** — 100 windows from two people is not 100 independent observations, so "opens first" still rests on the i.i.d. fiction of K2-02; (b) nothing in D-1 states the **measured window-production rate**, so "opens first" has no detector for *when* — a one-line measured issuance-rate figure (windows/chart-year by stratum, from the first generation's exposure manifest) converts this from an article of faith into a quantity. On §N.8: strictly, the design is compliant — `PROVISIONAL_INSUFFICIENT_N` carrying actual n *is* a real detector with a real false state. The §N.8-adjacent failure would be status fossilization: a per-stratum `EMPIRICALLY_EVALUATED` that can never open on the admissible population. The packet survives this only because the instrument-level gate exists; say so in the text, with the rate number.

  ## Q4 — D-2's 20% ceiling

  - **Principled or arbitrary?** Arbitrary but *published* — which puts it above most such constants. Nothing dignifies 20% over 15% or 25%; at 19.9% the stratum passes, at 20.1% it is blocked regardless of n — a cliff edge with no gradient. Minimal fix: replace the cliff with a **mandatory downgrade label** (`PROVISIONAL_HIGH_CENSORING`) above the threshold, or report the censoring rate as a continuous penalty on confidence tier rather than a binary.
  - **Censor-not-score: directionally right, and the informative-censoring risk is real and unaddressed.** The cases hardest to adjudicate are plausibly the near-misses — vague windows, weak claims — so censoring them preferentially removes misses and inflates the measured hit rate. The 20% ceiling caps the *magnitude* of that inflation, not its *direction*. What the packet needs and does not have: a **sensitivity requirement** — every stratum reports the hit-rate interval [hits / all-windows, (hits + censored) / all-windows] alongside the censored estimate, and the claim is stated against the interval's adverse end. D-2's "every adjudication records its reason" is the right seed; the interval is the missing instrument (K2-11).
  - **Contradiction with the sheet's own M-6 record — see K2-03 (MAJOR).** Kimi's condition, recorded in the same sheet under M-6 and covered by the native's "agree," was "**`ambiguous` stays in the denominator, fraction disclosed**." D-2 excludes `ambiguous` from n. Defensible as design; **indefensible as record-keeping** — the sheet never says "this supersedes Kimi condition 4, with reason." One line fixes it; without that line the packet contains two contradictory censoring rules, one of them native-adjacent.

  ## Q5 — D-4: the shape of a hold

  **The shape is faithful to the hold and internally consistent with D-6's own treatment of w30** (a removed term preserved one generation as labelled, non-scoring annotation). "Held means 'not the authority', not 'erased'" is the right reading; recomputing later would cost more than carrying a labelled non-scoring column.

  The backdoor is not the storage, it is the **detector gap** (K2-04, MAJOR, §N.8 class):
  1. The falsifier "any D30 term in a DOSHA score path fails the suite" **has no script in the MANIFEST today** — the MANIFEST holds 13 scripts and none mentions D30. Until one joins, "excluded from every score path" is an assertion with no detector that could return false — precisely the §N.8 defect. Minimal fix: the falsifier joins the MANIFEST *before any D30 row ships*, and the storage contract (table, column, the `varga_role: 'secondary_dosha'` label's physical location — currently unpinned) is named so the test has something to grep.
  2. The falsifier covers **score paths** only. A D30 value reaching a **served surface** (an API row, a UI annotation) is not a score path — and a consumer aggregating it into a rank is a score-path violation at the SQL layer, not the writer layer. Extend the falsifier: any D30 value in a DOSHA-bearing served response, or in any consumer's scoring SQL, fails the suite.

  With those two, the hold is honest; without them it is adoption-wearing-a-label.

  ## Q6 — D-5: the pāda entailment

  **The entailment is clean.** If the served position is L1's `RAH_MEAN`, every derivation of that position — sign, nakṣatra, pāda — follows from it; serving the mean longitude while reading the pāda off the true node would be the authority inversion §N.5 exists to forbid. On the classical-practice question: the mean/true distinction is **computational-era**; the classical corpus knows one node, canonically "always retrograde" — a property only the *mean* node has (the true node stations and goes direct), which is itself an argument that mean is the classically coherent convention. Modern software (Jagannatha Hora et al.) offers a *global* mean/true switch; I know of no practice, classical or modern, that cites the longitude from one convention and the nakṣatra-pāda from the other within one reading [J]. The author's inference does not overreach, and D-5's two stated limits (convention ≠ astronomical correctness; the `ephemeris_daily` contract stays open under its owner) are the right ones.

  One label is wrong (K2-07, MINOR): "**the 177″ disagreement published**." 177″ is the **true node's margin past the Rohiṇī pāda-3/4 boundary** (50.049248° − 50°00′00″ = 177.3″ — boundary math verified: Rohiṇī pāda 3 = 46°40′–50°00′, pāda 4 from 50°00′; mean 49.033044° → pāda 3 ✓). The **disagreement between conventions** is ~3658″ (50.049248 − 49.033044 = 1.0162°), which is the number M-1's disposition (b) actually requires declared ("~1° disagreement declared per row"). D-5 conflates the fragility margin with the convention gap; publish both, named correctly.

  ## Q7 — D-6's corrected scope

  **The corrected scope is right.** The delegation covered Saṅgam's residuals; an author decision cannot bind another stream's asset, and pretending otherwise would be the same shared-premise failure this campaign already corrected once. "Too weak to prevent contradiction" is the wrong frame: Saṅgam's cost is genuinely zero (verified — its engine has only C8 eclipse proximity at `engine.py:~180`; the [0,60,90,120,180] lists at :213/:467 are symmetric), so a Saṅgam-only binding is nearly vacuous *as engineering* but correct *as governance*. The real exposure lives in Gochara (verified: `_W30_NODAL_DRISHTI_ENABLED = True` at `gochara_v3/engine.py:107`, `w30_modifier` a live multiplicative term in `raw_lambda` at :632, the refuted "BPHS Ch.26" comment at `gochara_grammar/primitives.py:193-194`, and w30's own docstring admitting "NOT found in the original BPHS" at `w30_nodal_drishti.py:11`). If N-14 rules to keep node dṛṣṭi, the instrument then holds a **native-ruled divergence**, not an accidental one — which is what DISAGREEMENT_REGISTER exists to record. Condition (minor): the cross-stream contradiction should be *registered* now, not merely stated in this sheet, so it cannot close silently (K2-09 folded into conditions).

  ## Q8 — §0R overreach audit

  Row by row against the native's verbatim words:

  - **M-1:** adds disposition (b) mechanics (true knots retained, mean derived at read, ~1° declared) and the R-3 convention vector (`ephemeris_backend`, `epoch_convention`, `ayanamsa_application`). None of that is in the native's line; it is the sheet's author layer ("disposition (b) as the sheet's default unless the native says otherwise") plus the adopted peer-session evidence rule. Disclosed upstream, but in §0R's "Effect on this plan" table it rides without a marker (K2-08).
  - **M-2:** "4 = indeterminate-leaning-adverse … 6/8/12 inversion does not ship" — faithful. "Producer completeness receipt now; kakṣyā deferred; Kshetra S1 shares the source" — author layer, unmarked.
  - **M-3:** the native's words grant "E3 tier granted" outright and condition only the kernel path on N-7. §0R reads it as "granted **in principle**; E1 and E3 stay gated until N-7 is ruled" — the *conservative* reading (E3 needs the producer), matching the sheet's own resolution table. Under-claiming rather than smuggling; acceptable, but it is an interpretation of an ambiguous line, and the native should know that is the reading being executed (NOTE).
  - **M-4:** "cancellation detector precondition binds" — author layer; "D30 … (D-4)" — correctly attributed. Mostly faithful.
  - **M-5, M-7:** "as written" — faithful.
  - **M-6:** substitutes D-1's numbers for the never-filled placeholder — explicitly attributed to D-1, and §0R's header keeps the "OPEN" record. Faithful.

  No row puts doctrine in the native's mouth that the sheet's author layer had not already disclosed; the defect is purely typographic — three rows mix layers without per-element markers (K2-08, MINOR).

  ## Q9 — What fails at stage 3 (ordered, with the tripwire for each)

  1. **E1/E3 stall on N-7 with no fallback owner.** Path A's owner is explicitly unowned ("Neither peer session will name that owner — correctly; it is yours"). Tripwire: stage-3 entry checks N-7 ruled AND a single named owner for the `transit_search` amendment before scheduling E1/E3; if N-7 is refused, the plan currently has a hole where E1's geometry comes from.
  2. **R-5 harness passes, then a real rebuild orphans claims through an FK-free or nullable reference** (`phala_phaladesa.top_anchor_id` is FK-free by the plan's own account). Tripwire: §6.3's attack list — empty rebuild, moved date, split, merge, ambiguous, interrupted/resumed, **unchanged-count content-swap** — run in the disposable harness before any contact change, with the FK-free reference resolved semantically.
  3. **Legacy contamination reaches a consumer at serve time, not build time.** `ka_kala_darshana` reads `confidence_label`/`rarity_years` in SQL (breaks on E6's rename); `ka_tulana`'s 40/25/20/15 composite consumes rarity/30. Tripwire: the §6.2 material-field sentinel delivered *before* E6 lands, plus per-consumer sign-off from the 7×6 matrix — this is RR-10's owed receipt.
  4. **Suite drift.** The grep-based scripts pin line numbers (S1: [1148, 1377]; S12: [1149]; S3: [1004]). A refactor either breaks the suite spuriously or — worse — shifts semantics while the regex still matches. Tripwire: mandatory suite re-run after every repair lands, and the SPEC rows join the MANIFEST at their step as *behavioral* tests (the plan's own block-the-step rule, enforced).
  5. **D30 leaks before its falsifier exists.** Tripwire: K2-04 — falsifier in MANIFEST before any D30 row ships.
  6. **Threshold drift under the recompute rule.** D-1's "recomputed at the same power if measured base rate ≠ 0.20" never says *which lift at which power* — an open door to garden-of-forking-paths. Tripwire: the predeclared protocol artifact (M-6 condition 1) names the estimand, critical values, exact α, and the recompute formula before E6 opens.
  7. **Node-convention transition.** Rebuilding before the `ephemeris_daily` hub repair (owned elsewhere) propagates the five-way mean/true split into new rows with the disagreement undeclared. Tripwire: R-3's convention vector populated on every row + the cross-frame dedup SPEC.

  ## Q10 — Anything else

  - **K2-06 (MINOR): the sheet's "[U]" on Kimi's "0 dots = loss of life" is itself false at the page it cites.** `verification_by_author` and §M-2 both say "not found on the page." The cited page (wisdomlib doc1621595, Adh. XXIII) contains śloka 11's first clause verbatim: *"if it be found that a Rasi is void of any benefic dot in a planet's Ashtakavarga, it indicates that the native will lose his life when the particular planet in his orbit transits that Rasi."* Kimi was verse-correct; the sheet's verification record carries a false negative. It changes no ruling (M-2 rests on the 3/4 "fear" reading, which I verified — both read "fear" ✓), but a verification artifact that itself errs is exactly the failure mode this packet exists to catch. Record the correction.
  - **K2-05 (MINOR): stale evidence pointer.** v1.0's frontmatter and §6.1 cite `OUTPUT_2026-09-22T234243.txt` as "Current … SUITE-PASS 13/13" — that run's S8 **passed as an oracle on Moshier**, which the on-disk S8 v2.1 now refuses to do (exits NOT_RUN). A newer run exists (`OUTPUT_2026-09-23T012041.txt`) with S8 on **SWIEPH with checksums**, also SUITE-PASS. Point the frontmatter at the SWIEPH run; also reconcile the sheet's audit ("topology may run on Moshier with backend recorded") with the script's stricter all-or-nothing NOT_RUN — they currently disagree on what S8 may assert on the fallback.
  - **K2-12 (NOTE): base-rate circularity risk.** D-1: "E6's exposure computation supplies [the base rate]." If the measured 0.20 ever comes from the *same outcome data the gate scores*, p0 is being estimated and tested on one dataset. The null rate must come from the exposure/coverage model (a priori), and the text should say so.
  - **K2-09 (NOTE): the "254 in the file" count.** Verified: the chapter span (16457–18361, head at ~16490, the Saturn/Jupiter/Mars rule at :16500-16501) has **zero** rāhu/ketu/node matches — the refutation stands. The file total is 254 *lines* matching `rahu|ketu`; with `node` included it is 270 lines (292 + 17 occurrences). Immaterial, but the sheet's parenthetical conflates line count with occurrence count and drops `node`.
  - **D-8 is not discharged by this review.** The packet made the third Astra review a stage-3 entry gate by the independent reviewer. I am Kimi, not Astra; Q1 above covers v0.4's content, but the gate stands as designed.

  ---

  ## Findings

  **K2-01 · MAJOR · D-1's α is arithmetically wrong for its stated critical value, and the n=100 gate has no declared critical value.** Claim: "n=30, α=0.05 one-sided, critical ≥10, ≈80% power for 0.20→0.40"; "n=100, ≈85% for 0.20→0.32." Evidence (exact binomial, my computation): P(X≥10|Bin(30,0.2)) = **0.0611**, power = 0.8237; α ≤ 0.05 needs crit ≥ 11 → power **0.709**. n=100: crit ≥ 27 → α 0.0558/power 0.882; crit ≥ 28 → α 0.0342/power 0.833. Fix: publish exact (critical, α, power) triples for both gates in the predeclared protocol; correct "α=0.05" to the exact α.

  **K2-02 · MAJOR · D-1's power math assumes i.i.d. windows on a two-chart population, contradicting the plan's own "No statistical independence is claimed" (§4).** Two subjects → severe intracluster correlation → effective n far below nominal; both gates' claimed power is overstated. Fix: declare the binomial figures first-order approximations and add a chart-level concordance requirement (lift direction present in both charts) or a beta-binomial overdispersion check, published.

  **K2-03 · MAJOR · D-2 contradicts the sheet's own M-6 record on the denominator.** Kimi's condition 4, recorded under M-6 under the native's "agree": "`ambiguous` stays in the denominator, fraction disclosed." D-2: "`ambiguous` is censored, excluded from n." The design change is defensible; the absence of a recorded supersession is not — the packet now carries two censoring rules. Fix: one line in §CLOSE stating D-2 supersedes condition 4, with the reason (scoring biases both ways; ceiling + published rate covers the disclosure intent).

  **K2-04 · MAJOR · D-4's falsifier has no detector, and its scope misses the served surface.** "Any D30 term in a DOSHA score path fails the suite" — no such script exists in the MANIFEST (13 scripts, verified); the D30 storage contract (table/column/label location) is unpinned, so the test cannot yet be written; and "score path" does not cover a D30 value reaching a served response or a consumer's scoring SQL. §N.8 class: an exclusion claim with no code path that could fail. Fix: pin the storage contract; land the falsifier in the MANIFEST before any D30 row ships; extend it to served surfaces and consumer SQL.

  **K2-10 · MAJOR · the pooled instrument claim is Simpson-vulnerable with no pooling-safety rule.** Per-stratum counts are published (display), but nothing decides what happens when pooled and per-stratum disagree. Fix: predeclare a stratified primary estimand (standardized/CMH pooled lift, or pooled-lift ∧ no-opposite-sign-stratum), pooled raw as secondary.

  **K2-05 · MINOR · stale evidence pointer + harness/audit skew.** Frontmatter/§6.1 cite the Moshier S8 run as current; the on-disk S8 exits NOT_RUN on Moshier; a SWIEPH-checksummed SUITE-PASS run (`OUTPUT_2026-09-23T012041.txt`) exists. Fix: re-point; align the sheet's topology-on-Moshier allowance with the script's all-or-nothing rule.

  **K2-06 · MINOR · false "[U]" in the sheet's verification record.** "Kimi's '0 dots = loss of life' not found on the page" — refuted at the cited page (śloka 23.11, first clause: void of benefic dots → "the native will lose his life"). Fix: record the correction; Kimi's claim was verse-correct.

  **K2-07 · MINOR · D-5's "177″ disagreement" mislabels the quantity.** 177″ is the true node's boundary margin; the mean↔true disagreement is ~3658″ (1.0162°). Fix: publish both, named.

  **K2-08 · MINOR · §0R rows M-1/M-2/M-4 mix author-layer content into "Effect on this plan" without markers** (disposition (b) mechanics, convention vector, producer receipt, cancellation precondition). Fix: per-element (D-n / sheet-layer) tags as done for D-1/D-4.

  **K2-11 · MINOR · informative-censoring exposure; 20% cliff.** Fix: per-stratum hit-rate interval [hits/all, (hits+censored)/all] reported against the adverse end; downgrade-label gradient instead of a binary 20% block.

  **K2-09 · NOTE · file-count imprecision** (254 = rahu|ketu lines; 270 lines/309 occurrences with node) and **cross-stream contradiction registration** (D-6's position should live in the disagreement register until N-14 closes, not only in this sheet).

  **K2-12 · NOTE · base-rate provenance:** state that the 0.20 null comes from the exposure model a priori, never from the outcome data under test.

  ## Verdict

  **ACCEPT_WITH_CONDITIONS.**

  1. D-1 amended: exact (critical, α, power) triples predeclared for both gates; the α=0.05 claim corrected (K2-01); independence assumption declared + chart-level concordance or overdispersion check added (K2-02).
  2. D-2 carries its supersession line over Kimi condition 4 (K2-03) and the sensitivity interval (K2-11).
  3. D-4's falsifier exists in the MANIFEST and covers served surfaces before any D30 row ships (K2-04).
  4. Stratified pooling rule predeclared for the instrument claim (K2-10).
  5. Record-keeping corrections: evidence pointer (K2-05), the "0 dots" correction (K2-06), 177″ label (K2-07), §0R layer markers (K2-08).

  Not REWORK: v0.4 genuinely closes the second REWORK (Q1, first independent check); the rulings are applied without material overreach; and every MAJOR is a text amendment to a delegated decision, not a redesign — the stage-3 entry gate (D-8, which this review does not discharge) is the correct place to verify the amendments landed.

  ## What I verified at source vs what I assert

  **Verified at source (my own reads/queries/computations this session):** corpus table = 15 texts with phaladeepika 564 / bphs 1459 / muhurta_chintamani 274 chunks, no `kp`/`kp_reader` text_id (SQL); `bg_transit_rules` 41 favourable-vedha rows = 39 "BPHS Ch.29" + 2 Phaladīpikā (SQL); Santhanam Ch.26 head ~:16490, the three-graha rule at :16500-16501, zero rāhu/ketu/node in span 16457–18361 (grep); Phaladīpikā 23.10/23.11/23.20/23.23-24 including "fear"/"fear" and the 0-dot "lose his life" clause ([wisdomlib doc1621595](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621595.html)); `_W30_NODAL_DRISHTI_ENABLED=True` (`gochara_v3/engine.py:107`), `w30_modifier` in `raw_lambda` (:632), w30's "NOT found in the original BPHS" docstring (:11), `primitives.py:193-194`'s refuted citation; `convergence_score` product form (:696-728) and `necessary=[dignity_score, orb_s, vedha_factor]` (:1221); lagna default `'Aries'` (`ka_sangam.py:1149`, fallback :1162); target default 0.0 (`engine.py:1148,1377`; writer :662); C9 (:210-224), benefic dṛṣṭi weights (:460), C8 (:180 area); TRIGGER composition (:50, :46-47, calls :682/:708); scanner TRUE_NODE + unsigned `target + angle` (`transit_search.py:10,:64,:320`); real outcome columns (`ka_bhavishya_lekha.py:17,98,122`); `call_service_wrappers.ts:673-711` no `kala_convergence`; `logic.py:53-58`'s directory-for-corpus sentence; migration 526:36-48's disclosure; 535:194 "KP Reader NOT ingested"; RUN_ALL/MANIFEST/_common v2 mechanics and both OUTPUT files' 13/13 SUITE-PASS; S11's real kernel call; S8's bisection + NOT_RUN-on-Moshier; v1.0 ≡ v0.4 below §0R (diff); all binomial figures (exact, `math.comb`); Rohiṇī pāda boundaries and the 177″/3658″ arithmetic.

  **Not verified at the table (connector died after my first two queries; tagged [U-at-table]):** the `RAH_MEAN` chart-fact values behind pāda 3; PG338/339/345-352/353 chunk contents and the SBC prose-buildability claim; the vedha-regex per-text counts (17/5/5/2/1/1); `bg_vedha_malefic_scale`'s PG353 citation; `l1_sarvatobhadra_*` emptiness. The two queries I did land confirm the premises I rely on most heavily.

  **Asserted from knowledge/judgment:** [D-verified] node dṛṣṭi refutation, Phaladīpikā 23.x readings, BPHS Ch.26 content; [D-knowledge] classical corpus knows no mean/true node distinction and canonically "always-retrograde" nodes — only the mean node qualifies; [J] no classical or modern practice mixes mean longitude with true-node pāda in one citation; [J] the stratified/CMH fix, clustering correction, and censoring-interval design are orthodox and sufficient; [J] D-6's corrected scope is governance-correct; [U] nothing above rests on an unverified factual claim I can identify — where the DB was unreachable I said so rather than inferring.

  *Packet instruction honored: no files written; this review is advisory only and authorizes nothing. (Root CLAUDE.md's SESSION_OPEN/CLOSE artifact discipline is superseded for this session by the packet's explicit "Write no files.")*

