---
artifact: SANGAM_RULING_SHEET
canonical_id: SANGAM_RULING_SHEET
version: "1.0"
status: CLOSED   # M-1…M-7 confirmed by the native; residual items decided by the author under written delegation (see CLOSE D-1…D-8)
date: 2026-09-23
for: the native — seven method rulings on the Saṅgam algorithm elevation (plan v0.4 §8)
inputs:
  - SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4.md (the decisions, as framed after two Astra reviews)
  - KIMI_K3_RECOMMENDATIONS_SANGAM_DECISIONS_v1_0.md (Kimi K3, effort=max; read plan, both reviews, June ruling, corpus)
  - ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md / _v0_3.md (constraints each ruling must respect)
verification_by_author: "every BPHS line Kimi cited re-read at the corpus (BP1:16605-16652, 7569-7593, 22725-22742; BP2:8955-8962, 35666-35676, 42332-42369) — all verbatim; Phaladīpikā 23.10/23.11/23.20 re-read online (wisdomlib doc1621595) — verbatim; Hāyanaratna 2.1/3.3 NOT re-verified by the author (Kimi and Astra both cite the same online edition) — tagged [D-online]; Kimi's '0 dots = loss of life' — RECORDED AS NOT FOUND, **RETRACTED 2026-09-23 (K2-06): that was a FALSE NEGATIVE.** The clause is verbatim at the cited page (`phaladeepika:PG299:C1`, Adh. XXIII śl. 11): 'if it be found that a Rasi is void of any benefic dot in a planet's Ashtakavarga, it indicates that the native will lose his life when the particular planet in his orbit transits that Rasi.' This session's own earlier query returned that text; the verification record contradicted the author's own tool output. Kimi was verse-correct. Changes no ruling (M-2 rests on the 3/4 'fear' reading, independently confirmed) — but a verification artifact that itself errs is the exact failure this packet exists to catch — [U]"
rulings_recorded: "2026-09-23T02:42:50+05:30 — by the native, in writing, in the Saṅgam session (madhav-d9), transcribed verbatim below; attribution: Abhisek Mohanty"
does_not_authorize: "implementation. This sheet records the native's rulings plus the author's delegated decisions; plan v1.0 is APPROVED_FOR_EXECUTION_STAGE_3 with the third Astra review as a stage-3 ENTRY GATE (D-8). No code, migration or build is authorized by this document."
answer_format: "M-n: agree / agree, but … / no — …"
delegation_recorded: "2026-09-23T03:39:33+05:30 — the native confirmed M-1…M-7 as delivered and delegated the residual open items (M-6 n, D30 hold shape, pāda, node-dṛṣṭi scope) to the author; delegation quoted verbatim in CLOSE. Author decisions D-1…D-8 are the author's, not the native's."
---

# CLOSE — native confirmation and delegated decisions (2026-09-23T03:39:33+05:30)

**Native confirmation.** The native confirmed the seven lines as delivered and delegated the
residual open items to the author, in writing, in this session:

> "I want you to consider what Kimi has proposed, but the decision is yours final. With this can you
> close All the rulings as native delivered."

Two things follow and are kept apart on purpose. **(1) M-1…M-7 are the NATIVE'S rulings** —
transcribed verbatim below and now explicitly confirmed. The transparency note (they matched the
author's example lines, adopted by paste) stands as the historical record of how they were
delivered; the native has since affirmed them as their own. **(2) D-1…D-8 below are the AUTHOR'S
decisions, made under the delegation quoted above.** They are not native words and are not recorded
as such. Each carries its reasoning so any one can be overturned with a single line.

### D-1 — M-6 minimum n: **35 per stratum (crit ≥12, α=0.0344, power 0.805) · 100 instrument-level (crit ≥28, α=0.0342, power 0.833) · `method_version` never pooled**

**[HEADING CORRECTED 2026-09-24.** The body of this decision was amended to n=35 on 2026-09-23 (K2-01) and the executor's `exposure.py` computes 35/12 and 100/28 from exact binomial tails — but this heading still read "30", so the first line a reader saw contradicted the paragraph beneath it. Caught by the strategic session while checking the arithmetic under the native's direct instruction (`KALA_DELEGATED_DECISIONS_v1_0.md` **D-F** at `59cd0390e`: n=35 adopted, pooled 100 unchanged). The drift class this campaign has been finding, in the decision meant to govern how the instrument proves itself; corrected in place.]**

- **Hard partition: `method_version`.** Windows scored under different kernel/contract versions are
  different estimands and are never pooled. This is the calibration-leak discipline the project
  already enforces, not a new rule.
- **Per-stratum claim** — a claim about one `(domain × route × method_version)`, Kimi's stratum shape,
  adopted: **n = 35** fully observed, non-censored evaluated windows, **critical ≥ 12 hits,
  α = 0.0344, power = 0.805** against a 0.20 null at a 0.40 alternative (exact binomial).
  **[AMENDED 2026-09-23 — K2-01, MAJOR, Kimi K3 max-effort review; the author's arithmetic was wrong.** The
  original read "n = 30 … α=0.05 one-sided, critical ≥10, ≈80% power". Reproduced exactly:
  P(X≥10 | Bin(30,0.20)) = **0.0611**, power 0.8237 — the power figure was right, **the α was not**:
  the stated gate ran at 6.1%, not 5%. Holding α≤0.05 at n=30 forces critical ≥11 → power drops to
  0.709. Rather than restate 30 with a corrected description, the gate is **set by the arithmetic**:
  35 is the smallest n that actually satisfies the design as written (α≤0.05 **and** power≥0.80).
  A number chosen for its roundness and then described wrongly is the §N.8 defect in miniature.]**
- **Instrument-level claim** — Saṅgam's windows beat measured exposure within ONE frozen
  `method_version`, pooled across domain and route with both carried as reported covariates and the
  per-stratum counts published alongside (never suppressed): **n = 100, critical ≥ 28, α = 0.0342, power = 0.833** at 0.20 → 0.32 (exact binomial).
  **[AMENDED 2026-09-23 — K2-01:** the original claimed "≈85%"; at n=100 holding α≤0.05 the true power is
  **0.833**. n=98/crit≥27 would reach 0.854 at α=0.0446; 100 is retained as the already-communicated
  figure with its **honest** power published rather than the aspirational one.]**

- **Independence is NOT assumed — amended 2026-09-23, K2-02 (MAJOR).** The binomial figures above are
  **first-order approximations**. The admissible population is **two charts** (D-3), so windows are
  clustered within two subjects: intracluster correlation makes the effective n materially lower than
  the nominal n, and plan §4 already says "No statistical independence is claimed" — the author's
  original power computation silently re-introduced it. Therefore: (i) the triples are published **as
  approximations**, never as exact operating characteristics; (ii) a **chart-level concordance
  requirement** binds — the lift direction must appear **independently in both charts** before any
  claim opens; and (iii) a **beta-binomial overdispersion check is computed and published** with every
  claim. Neither (ii) nor (iii) costs data; both are the difference between "35 windows" and "35
  windows that mean what the formula thinks they mean".

- **Pooling rule — amended 2026-09-23, K2-10 (MAJOR).** The instrument-level claim pools strata with
  different base rates and exposures and is therefore **Simpson-vulnerable**: a pooled lift no stratum
  has, or a real per-stratum lift masked. Publishing per-stratum counts displays the problem without
  deciding it. **Predeclared primary estimand: a stratified (CMH-type / standardized) pooled lift, and
  the claim opens only if no stratum shows a significant opposite-sign deviation.** The raw pooled
  number is secondary display only.

- **Base-rate provenance — amended 2026-09-23, K2-12.** The 0.20 null comes from the **exposure/coverage
  model, a priori** — never estimated from the same outcome data the gate scores, which would test and
  fit on one dataset.

- **Reachability has a detector — amended 2026-09-23 (Kimi Q3).** The first generation's exposure manifest
  **publishes the measured window-issuance rate** (windows per chart-year, by stratum). Without it,
  "the instrument-level gate opens first" is an article of faith rather than a quantity. Note for the
  record: `PROVISIONAL_INSUFFICIENT_N` carrying actual n **is** a real detector with a real false
  state, so the design is §N.8-compliant; the residual risk is *status fossilization* — a per-stratum
  `EMPIRICALLY_EVALUATED` that can never open on a two-chart population. The instrument-level gate is
  what prevents that, and this text now says so.
- **Below either threshold:** `EMPIRICALLY_EVALUATED` stays closed and the result reports as
  `PROVISIONAL_INSUFFICIENT_N` carrying the actual n and the lift that n can see — never as a
  calibration, never silently (§N.8: the gate needs a detector, and "not enough data yet" is a real
  answer).
- **Both numbers are functions of the measured base rate, not constants.** E6's exposure computation
  supplies it; if the measured base rate differs materially from 0.20, the thresholds are
  **recomputed at the same power**, not kept.
- **Reasoning.** Kimi deliberately named no number ("the number is yours **[NATIVE-RATIFY]**") and was
  right to; the native has now delegated it. A smaller gate (n≈12) can only see a 3× lift and would
  let a weak result wear a calibrated label. **Consequence stated honestly:** at ~16 strata, full
  per-stratum coverage is years out on a two-chart corpus. That is consistent with L5 being sealed in
  STRUCTURAL mode by design — the instrument-level gate at n=100 is the reachable one and opens first.

### D-2 — `ambiguous`: adjudicated by the native, **out of n but binding at the rate's adverse end**, with a censoring gradient

- Adjudicated by **the native** — not the author, not the instrument: the only party holding the
  lived facts. Every adjudication records its reason.
- `ambiguous` is **excluded from n** (hence "fully observed, non-censored" above) — n measures how
  much real evidence exists. **But it is NOT excluded from the reported rate.**
  **[AMENDED 2026-09-23 — K2-03 (MAJOR): the original D-2 contradicted this sheet's own M-6 record.** That
  record carries, among the five conditions the native's "agree" covered, Kimi's condition 4:
  *"`ambiguous` stays in the denominator, fraction disclosed"*. The original D-2 ("censored, excluded
  from n") stated the opposite, leaving two contradictory censoring rules in one packet, one of them
  native-adjacent — a GA.1-class registry disagreement authored by the very session that has spent
  the day correcting them in others. **Resolved without superseding the native-adjacent rule**, and
  the resolution is strictly better than either original: see the interval below, whose adverse end
  *is* condition 4.]**
- **Every stratum reports a hit-rate INTERVAL, and the claim is stated against its adverse end**
  (K2-11): `[ hits / all windows (ambiguous included) , (hits + ambiguous) / all windows ]`. The lower
  bound is Kimi's condition 4 exactly — ambiguity can never help the instrument. The upper bound is
  the censored estimate, published alongside with the censoring rate. This closes the
  **informative-censoring** exposure the original D-2 carried: the hardest cases to adjudicate are
  plausibly the near-misses, so excluding them preferentially removes misses and inflates the rate;
  a ceiling caps that inflation's *magnitude* but not its *direction*, and only the adverse end does.
- **The censoring rate is published per stratum**, with a **gradient rather than a cliff** (K2-11):
  above **10%** the stratum's claim carries a `censoring_elevated` label; above **20%** the claim is
  **blocked regardless of n**. A bare 20% binary would make 19.9% and 20.1% mean wholly different
  things for no reason available in the data. Without that ceiling, n counts only the clean cases
  and a high-ambiguity predicate looks well-evidenced precisely because it is ill-defined.

### D-3 — Evaluation population: consenting persons with real outcomes only

Only charts with a consenting person behind them and a real outcome record are evaluation-eligible —
today the two production charts. Synthetic and test charts may exercise the machinery; their rows
carry `evaluation_eligible = false` and can never enter n (Kimi: "synthetic charts are non-persons
and cannot supply outcomes"). Extending beyond the two charts is a consent-and-outcome question
under the MACRO_PLAN Ethical Framework, not a technical one.

### D-4 — M-4: the **shape** of the D30 hold — domain varga primary, D30 secondary and non-scoring

- The native held D30 as the DOSHA varga. **Held means "not the authority", not "erased".** DOSHA
  predicates take the **domain varga as primary**; D30 is computed, stored and carried as
  `varga_role: 'secondary_dosha'`, labelled, and **excluded from every score, grade and verdict
  path** until ruled.
- **Falsifier** (mirroring Kimi's own for `boundary_distance`): *any D30 term appearing in a DOSHA
  score path fails the suite.*
  **[AMENDED 2026-09-23 — K2-04 (MAJOR), and the author's own §N.8 violation.** As written that sentence was
  **a claim with no detector**: the evidence MANIFEST holds 14 script lines and **zero** D30/DOSHA
  entries (verified), so no code path exists that could ever make it read false — precisely the defect
  §N.8 forbids, authored inside the decision whose purpose was honest exclusion. Its scope was also
  too narrow: "score path" does not reach a D30 value surfacing in a **served response** or in a
  **consumer's scoring SQL**. Corrected, and stated as a gate rather than an accomplishment:
  **(i)** the D30 storage contract (table, column, label location) is **pinned in stage 3 before any
  D30 row is written** — the test cannot be authored until it is; **(ii)** the falsifier **exists in
  `evidence_sangam/MANIFEST.txt` with a negative control, and passes, BEFORE the first D30 row
  ships** — not after; **(iii)** its scope covers score paths, **served surfaces and consumer SQL**.
  Until (i)–(iii) hold, D-4's exclusion is an **intention, not a verified property**, and must be
  described that way wherever it is cited.]**
- **Reasoning.** Kimi recommended adopting D30 with verse support ("evil effects from Triṃśāṃśa",
  BP1:7569-7593) and named its own falsifier — that triṃśāṃśa may read as *the native's* evils
  rather than evil events in the domain — with the fallback "domain varga + D30 as secondary,
  labelled". The hold selects exactly that branch, so this is not a reversal of Kimi's advice but its
  declared alternate. Dropping D30 outright would discard a computed, verse-attested signal (B.10,
  §N.6) and force recomputation when the native rules; carrying it non-scoring costs nothing and
  keeps the option open.

### D-5 — M-1: the mean convention governs the **reading** — Rohiṇī **pāda 3** for this chart

- **Yes.** If the served node is L1's `RAH_MEAN`, every derivation of it — sign, nakṣatra, pāda —
  follows from it. Serving the mean longitude and reading the true node's pāda is precisely the
  authority inversion §N.5 forbids.
- So for this chart Rāhu's nakṣatra-pāda is **Rohiṇī pāda 3** (L1 fact `060bb63b81a073bb`), with the
  true-node value (pāda 4; Swiss 50.049248° at 05:13 UT) retained as the **declared variant** and the
  **both quantities published on every row that carries it, each named** — the **mean↔true convention gap of 3658.3″ (1.016204°)**, which is what M-1's disposition (b) requires declared, and the **true node's margin of 177.3″ past the pāda 3/4 boundary at 50°00′**, which is the fragility measure **[CORRECTED 2026-09-23 — K2-07: the author's original text called 177″ "the disagreement", conflating the boundary margin with the convention gap; both reproduced by arithmetic]**. Anything citing the pāda cites the
  convention with it.
- **Two limits, stated so this is not read wider than it is.** It settles which *convention* governs
  a reading, **not** which node is astronomically more correct. And it does **not** close the
  `ephemeris_daily` undeclared-contract finding (§11.1) — that stays open under its own owner.

### D-6 — M-1: "no node dṛṣṭi" is **instrument-level**; execution belongs to the Gochara stream

- **Scope, corrected 2026-09-23 at the Gochara session's boundary-setting, and they are right.** The native's delegation covered **Saṅgam's** residual items. So D-6 **binds Saṅgam** and states a **cross-stream position with its grounds** for every other family — it is **not** authority over an asset the delegation did not cover. Whether the Gochara family applies it is **N-14's to rule, by that stream's native**, doctrine included, not merely its schedule. The author's first wording ("instrument-level doctrine") overstated the reach and is corrected here rather than defended: this campaign has already shown what a shared premise does when nobody re-scopes it.
- **Position (Saṅgam-binding; recommended instrument-wide): graha-dṛṣṭi is not applied to Rāhu or Ketu.** One instrument should not
  grant node aspects in one asset and deny them in another. The citation behind the live
  implementation is refuted at the text (Santhanam Ch.26 names Saturn, Jupiter and Mars; zero
  rāhu/ketu/node occurrences in the chapter span, against 254 *lines* matching rāhu|ketu in the file — 270 lines / 309 occurrences with `node` included; the parenthetical previously conflated lines with occurrences and omitted `node` (K2-09, 2026-09-23)); the practice is not found
  at table level across all 15 corpus texts; Kimi independently graded it `[U] — do not implement by
  default`; and `w30_nodal_drishti.py`'s own docstring already says it is not in BPHS. Continuing
  would keep a **false citation in served data**.
- **Execution and the ruling itself are the Gochara stream's, under its N-14 — neither is this sheet's to impose.** The Gochara session has adopted the three conditions below on their own merits, independent of who rules N-14. The shape this
  decision requires of it: a **same-generation** change (drop `w30_modifier` from the λ product and
  regenerate every stored λ within that generation, never a patch over live rows); the absence
  declared as `completeness_state`, never silently dropped; and the removed term preserved for one
  generation as a **labelled, non-scoring** annotation so every dependent claim has an authorized
  successor.
- Saṅgam's own cost is **zero** — its engine applies no node dṛṣṭi today (only C8 eclipse proximity
  at `engine.py:180`). The whole live cost falls in Gochara, and that asymmetry is why the doctrine
  is decided here and the schedule is not.

### D-7 — Legacy scan withdrawal: Kimi's condition adopted

`legacy_unsigned_angles` is kept exactly one generation, labelled, never pooled or ranked with new
rows, and **withdrawn only after the R-5 preservation manifest shows every dependent claim has an
authorized successor** — on that condition, not on a date.

### D-8 — The third Astra review: a **stage-3 entry gate**, not a close condition

Recorded plainly because it is the one discipline this packet is short of: **plan v0.4 — the text
v1.0 is built from — has never been reviewed by anyone.** v0.1 returned REWORK (19 findings), v0.3
returned REWORK (10), and v0.4 is the text that answered the second REWORK. The packet closes now;
the review runs **before any code is written in stage 3**, by the independent reviewer, with
`ASTRA_REVIEW_REQUEST_SANGAM_ALGO_v0_4.md` re-pointed at v1.0. It is not discharged by the author and
is not skippable.

---

## Residual rulings closed — second delegation (2026-09-23T22:57:26+05:30)

**The native's instruction, verbatim, in the Saṅgam session:**

> "First on my rulings, point number one, on my behalf, can you Respond to the four decisions and
> close out my rulings."

The four were listed to the native as: **B-1** (N-7, the producer path), **B-2** (a Path-A owner if
N-7 were declined), **B-3** (aborted approaches in E6's frequency numerator), and **N-14** (node
dṛṣṭi in the Gochara family). Same discipline as §CLOSE: what follows is the **author's** record
under the native's delegation, kept apart from the native's words; any line is reversible by the
native in one sentence.

**Two of the four were already ruled — by the native, on the Gochara sheet — and are ADOPTED, not
re-ruled.** `GOCHARA_RULING_SHEET_v1_0.md` (branch `l3/gochara-elevation`, commit `50b5e1822`,
`status: RULED`, `ruled_by: Native … by explicit delegated instruction to session madhav-e6, recorded
verbatim in §0`, 2026-09-23 03:55 IST) carries:

- **N-7 — RULED: persist the Contact object** as `kala_gochara_contacts`, owned by `ka_gochara`,
  exact-instant grain, with the coverage manifest `kala_gochara_coverage` — i.e. **the kernel, Path
  B**. Its own consequence line: *"the producer path is the kernel (Path B); packet S-2 binds;
  **Saṅgam E1/E3 are released from their N-7 gate**."* → **B-1 CLOSED.** E1 and E3 are no longer
  gated by authority; they are built when the kernel's contact ledger and `find_episodes` exist
  (S-2), and until then they are unbuilt **for lack of a producer, not for lack of a ruling**. The
  scanner-dependent R-3(b)/R-4 SPECs (RRV-02) release on the same terms.
- **B-2 — MOOT.** Path B was chosen; no Path-A owner is needed. If the kernel were ever abandoned,
  the Gochara sheet already names the same owner for the bounded `transit_search` amendment.
- **N-14 — RULED: extend "no graha-dṛṣṭi for Rāhu/Ketu" to this family.** `drishti_contact` casts
  no dṛṣṭi from the nodes; `w30_nodal_drishti` leaves the λ product; the nodes remain full gochara
  agents and targets; the three implementation conditions from D-6 adopted (same-generation
  regeneration in a new candidate, absence declared as `completeness_state`, one-generation labelled
  non-scoring successor); cost "accepted knowingly". → **DIS.031 can close as RESOLVED (instrument
  consistent)** — referred to the register's owner with this pointer. D-6's cross-stream position is
  now the instrument's doctrine by the native's own ruling, not by this sheet's reach.

**Correction to this campaign's record.** `SANGAM_STAGE3_STATE.md` B-1 and plan §0R M-3 stated
*"N-7 status at 2026-09-23: UNRULED (verified by full-text search of the campaign tree)"*. The
search covered the executor's branch; the ruling lived on `l3/gochara-elevation`, ruled earlier the
same morning. **B-1 was stale when written** — one more instance of a claim of absence made against
the wrong place. Corrected in both files.

**The one decision that was genuinely open, decided now — B-3.**

### B-3 — Aborted approaches **count** in E6's numerator, as `perfected: false`, stratified

- **Decision.** An aborted-approach child (`approached_never_perfected = true`, `perfected = false`,
  E5/RRV-06) **is an issued window** and enters E6's frequency numerator. `perfected` is carried as a
  **mandatory reported covariate**: every E6 output publishes the perfected / unperfected split per
  stratum alongside the pooled figure, and the convention is stated on the output. RRV-06's interim
  ("excluded until ruled, convention stated") is superseded; RRV-13's "*all issued windows*" is
  read consistently — *all* includes unperfected.
- **Why include.** (i) **Numerator–denominator consistency.** E5's occupied-day union — which feeds
  `ka_taranga` *and* E6's exposure denominator — already includes approach children whose interval
  overlaps a loop. Counting their days in exposure while excluding them as candidates biases the
  measured frequency **down** and makes the base-rate comparison incoherent. (ii) **Erasure is the
  defect this plan repaired.** R-6 exists because the old kernel erased adverse activity; an
  applying-then-separating approach is real geometry (the classical applying/separating distinction
  is a *strength* grading, not a nullity), and silently dropping it from the record repeats the
  erasure one layer up. (iii) **It is an empirical question, and E6 is the instrument for answering
  it.** Whether unperfected approaches carry lower skill is exactly what the stratified split will
  show; baking the answer in as an exclusion would hide the data E6 is built to produce. (iv) The
  independent reviewer leaned the same way (*"Kimi leans yes as `perfected: false`"*).
- **Limit stated.** This decides *counting*, not *weight*: an unperfected child's `activity` remains
  whatever R-6 computes for its geometry; nothing here inflates it.

**With this, all residual rulings are closed.** Remaining open items are engineering or belong to
other owners (state file B-4…B-6; plan §10 RRV-13/RRV-14 carried into E6 and E1/E3).

## Post-close independent review — Kimi K3 (effort=max), 2026-09-23T04:33:31+05:30

The closed packet was sent for adversarial review to Kimi K3 at max effort via the Kimi CLI
(`KIMI_REVIEW_PACKET_SANGAM_CLOSED_v1_0.md` → `KIMI_K3_REVIEW_SANGAM_CLOSED_v1_0.md`), specifically
targeting the two bodies of text no reviewer had ever seen: **plan v0.4** and **D-1…D-8**.

**Verdict: ACCEPT_WITH_CONDITIONS** — 12 findings (4 MAJOR, 5 MINOR, 3 NOTE), no BLOCKER, no
re-ruling required. **Q1, answered for the first time by an independent reader: v0.4 genuinely closes
the v0.3 REWORK (RR-01…RR-10)**, with RR-09's harness now stricter than the review demanded.

Every MAJOR was a defect in the **author's** delegated decisions, not in the native's rulings, and
each was **reproduced at source by the author before acceptance** (a reviewer's confirmation is not
evidence this session has not itself queried — the rule this campaign ended up writing):

| # | Finding | Status |
|---|---|---|
| K2-01 | D-1's α was arithmetically wrong (0.0611, not 0.05) for its stated critical value | **fixed** — gate re-derived: n=35/crit≥12/α=0.0344/power 0.805; n=100/crit≥28/α=0.0342/power 0.833 |
| K2-02 | D-1's power math assumed i.i.d. windows on a two-chart population, contradicting plan §4 | **fixed** — approximations declared; chart-level concordance + published overdispersion check |
| K2-03 | D-2 contradicted this sheet's own M-6 record (`ambiguous` in the denominator) | **fixed** — interval whose adverse end *is* condition 4; nothing native-adjacent superseded |
| K2-04 | D-4's falsifier had no detector and missed served surfaces (§N.8 class, author-authored) | **fixed** — restated as a gate: contract pinned, falsifier in MANIFEST and passing before any D30 row |
| K2-10 | The pooled instrument claim was Simpson-vulnerable with no pooling-safety rule | **fixed** — stratified CMH-type primary estimand predeclared |
| K2-11 | Informative censoring; 20% cliff | **fixed** — adverse-end interval; 10%/20% gradient |
| K2-05 | Stale evidence pointer (Moshier run cited as current) + harness/audit skew | **fixed** in plan §6.1/frontmatter |
| K2-06 | The sheet's own `[U]` was a false negative | **retracted** in `verification_by_author` |
| K2-07 | D-5 mislabelled 177″ as the convention gap | **fixed** — both quantities published, named |
| K2-08 | §0R rows mix author-layer content without per-element markers | **fixed** in plan §0R |
| K2-09 | Line-vs-occurrence count imprecision; D-6 should be registered, not only stated | count fixed; **registration referred to the governance owner** (see below) |
| K2-12 | Base-rate circularity risk | **fixed** — null comes from the exposure model a priori |

**One condition NOT discharged here, and deliberately so.** K2-09's second half asks that D-6's
cross-stream position be entered in `DISAGREEMENT_REGISTER_v1_0.md` so it cannot close silently while
Gochara's N-14 is unruled. That register is a shared governance artifact owned outside this packet;
this session referred the entry to the strategic session rather than editing a shared register
unilaterally at the end of its own close. **It is open until that entry exists.**

**What this review does NOT discharge:** D-8. The third Astra review remains the stage-3 entry gate,
and it is the correct place to verify that these amendments actually landed — this review is a second
independent read, not a substitute for the one the author owes before code is written.

**With D-1…D-8 the seven rulings are CLOSED. No open question remains on this sheet.** What remains
are *dependencies owned elsewhere*, not Saṅgam decisions: E1/E3 wait on the Gochara N-7 ruling
(producer path); the `ephemeris_daily` undeclared-contract finding (§11.1) is open under its owner;
and house-vedha's 39 mis-cited rules await L0 re-citation under Gochara F-23/G-8.

# RULINGS — recorded 2026-09-23T02:42:50+05:30

The native answered the seven questions **in writing, in the Saṅgam session**, in the sheet's own
format. Transcribed **verbatim**; attribution Abhisek Mohanty. **Transparency note, stated so it can
be corrected:** the seven lines are character-for-character the author's *example* lines offered
in the same exchange (the M-6 placeholder `<your number>` was not filled). The native adopted them
as their rulings by pasting them as the answer; the author records them as such and flags M-6's
minimum count as **OPEN** — a placeholder cannot be a ruling, and only the native can supply that
number. Any line the native meant differently is corrected on request; nothing below is inferred.

```
M-1: agree — mean node; Placidus-as-stored; retire legacy scan after one generation; no node dṛṣṭi
M-2: agree, but 4 leans adverse; 6/8/12 inversion does not ship
M-3: agree — §4.5 governs; owner = Gochara stream (kernel path if N-7 approved); E3 tier granted
M-7: agree
M-4: agree, but D30 for DOSHA held
M-5: agree
M-6: agree; minimum n = <your number>
```

**Two clarifications put to the native after recording (2026-09-23T02:52:53+05:30) — **ANSWERED 2026-09-23 by the author under the native's delegation: see CLOSE D-5 (pāda) and D-6 (node-dṛṣṭi scope). Retained as the record of what was asked and on what evidence:**

- **M-1 / pāda.** "Mean node" has a chart-level consequence the line does not state: at this native's birth instant the mean node is Rohiṇī **pāda 3** (L1 fact `060bb63b81a073bb`) and the true node is **pāda 4** (Swiss 50.049248°, 177″ apart = 2.7× the Moshier bound). Does the ruling mean only *"the citable (mean) value governs"*, or also *"pāda 3 is the reading for this chart"*? The `ephemeris_daily` undeclared-contract finding (§11.1) stays open either way. (Raised by the strategic session on verifying the sheet; author agrees it needs one line.)
- **M-3 / E3's vedha standing — transparency, not a question.** E3's bounded tier was granted "under the uniform admission rule" while this sheet said the rule's outcome was `unqualified` for *every* vedha row. The rule is unchanged, but its outcome is now per `vedha_kind` (§Corrections item 2): laṭṭā and the malefic scale qualify today; house-vedha qualifies on L0 re-citation; SBC on population. So the vedha evidence E3 admits will carry **higher standing** than the native was shown at ruling time — more `applied` rows, not fewer. M-3 stands as ruled unless the native says otherwise; recorded so the grant is not read as having been made on the lower figure. (Raised by the Kshetra session, 2026-09-23.)
- **M-1 / "no node dṛṣṭi".** Cost and corpus status, so the line is ruled with both in view: (i) Saṅgam's engine applies no node dṛṣṭi today (`engine.py` — only C8 eclipse proximity at :180; aspect lists are symmetric 0/60/90/120/180), so the ruling removes nothing in Saṅgam; (ii) the Gochara family DOES apply it live — `gochara_grammar/primitives.py:189-196` gives Rāhu/Ketu Jupiter's 120/180/240 citing "BPHS Ch.26", and on the canonical chart that is Rāhu 85 records across 76 of 914 served rows, Ketu 87 across 79 (Gochara session measurement, raised as their decision N-14); (iii) **corpus check, 2026-09-23, author-run:** three hybrid searches over the admitted corpus (35 unique hits) found every classical aspect rule — Horā Sāra śl. 13-14, Jātaka Pārijāta śl. 30, Uttara Kālāmṛta, Patel's transit gloss — naming Mars 4/8, Jupiter 5/9, Saturn 3/10, 7th for all, and **none naming Rāhu or Ketu**; the BPHS aspect chapter itself did not surface (page-based chapter index), so the grade is *unverified so far*, not *absent*. Does "no node dṛṣṭi" extend to the Gochara family (one instrument, one rule — the Gochara session's recommendation and the author's), or is it Saṅgam-only?

**Corrections recorded 2026-09-23T02:59:36+05:30 — author-verified against the `classical_text_chunks` TABLE (`count(*)` / regex on `amjis`, via the direct connector) and the raw Santhanam OCR, not the search tool. These supersede the sheet's earlier statements where they conflict; the rulings themselves are unchanged.**

1. **"Admitted corpus = BPHS, Jaimini Sūtram, KP, KP Reader only" was FALSE.** That list is `SOURCE_DATA/classical_texts/`'s four *directory names*, copied into `ka_vedha_gochara/logic.py:56` and migration 526:42 as if it were the ingested corpus (a filename-for-corpus error, same family as `bg_phaladeepika_vedha`; retracted by the strategic session, blueprint §11.21, and re-measured here). The table holds **15 texts**: bphs 1459 chunks, phaladeepika 564, saravali 471, hora_sara 460, jataka_parijata 704, brihat_jataka 607, uttara_kalamrita 289, muhurta_chintamani 274, bphs_jaimini 264, … — and **no `kp` / `kp_reader` text_id at all.** Rows matching `vedha`: phaladeepika **17**, sarvartha_chintamani 5, uttara_kalamrita 5, bphs 2, muhurta_chintamani 1, yavana_jataka 1.
2. **Consequence for the uniform vedha admission rule — the RULE stands, the OUTCOME changes.** `applied` iff `corpus_verifiable` ∧ geometry is unchanged. But "today every gochara-vedha row is `unqualified`" was built on item 1. Corrected, per `vedha_kind`: **laṭṭā** — cited to Phaladīpikā PG338-339, and `phaladeepika:PG338:C1` (śl. 39-40, Saturn/Rāhu/Ketu limb table) and `PG339:C1` (Adh. XXVI laṭṭā stars) exist with that content → **corpus-verifiable today** → `applied` where geometry passes. **Malefic scale** — PG353:C1 exists: "vedha by one, two, three, four or five malefics → fear, failure, killing, death, ignominy" → verifiable. **House-vedha** — of the 41 `bg_transit_rules` rows (`rule_type='favourable' AND vedha_house IS NOT NULL`), **39 carry `classical_citation = "BPHS Ch.29 (Gochara Phala)"`** (refuted: Ch.29 is Bhāva Padas) and 2 (Rāhu/Ketu) carry "Phaladeepika Ch.26"; yet the 39 rows' *content* (Sun favourable in 11/3/10/6 with vedha 5/9/4/12, …) is verbatim Phaladīpikā Adh. XXVI śl. 3-8 at `PG322:C1`–`PG323:C1`. So they are **mis-cited, not unsourced**: `unqualified` *as cited today*, becoming `applied` on an L0 **re-citation** to Phaladīpikā XXVI (page-anchored), which is the L0 owner's action under Gochara F-23/G-8 — not a corpus-admission action, since the text is already admitted. **Sarvatobhadra** — corrected again 2026-09-23T03:01 after the Gochara session's 8-row hint, verified chunk by chunk: 7 of the 8 `sarvato` hits are noise (Bṛhat Saṃhitā index fragments, a Patel aside, Phaladīpikā's contents/preface), but **`phaladeepika:PG345:C1`–`PG352:C1` is Adh. XXVI śl. 48, a full PRIMARY description of the Sarvatobhadra-chakra** — 81 squares from ten lines each way, the 16 vowels in the corner squares from the north-east, the 28 asterisms from Kṛttikā in the outer ring, tithis/rāśis/weekdays, three vedhas (left/front/right) per planet with retrograde → right and Sun/Moon → left, benefic/malefic effects, and the sensitive-star set (Janma; Karma = 10th; Ādhāna = 19th; Vaināśika = 23rd; Sāmudāyika = 18th; Sāṅghātika = 16th; Jāti/Deśa/Abhiṣeka = 26/27/28) at PG352:C1. **Migration 526:36-48's claim that the corpus holds no primary source for the SBC grid is false** — it looked for Muhūrta Cintāmaṇi (present, 274 chunks, but 0 `sarvato` rows) and never at Phaladīpikā. So `l1_sarvatobhadra_positions` / `l1_sarvatobhadra_vedha` are empty but **populatable from a cited primary**; SBC rows stay `unqualified` *today* because the grid is unpopulated, not because it is unsourced. Precision note (strategic session's PG332 hint, verified): `phaladeepika:PG332:C1` is also a grid page, but it is the 28-asterism ring chakra for the **Sun-vedha rule at śl. 26-27** (Kṛttikā start; "counted from Kṛttikā as shown in the previous page"), not the SBC proper at śl. 48 (PG345-346) — same ring, different chakra; transcribe the right one. ~~Honest limit (strategic session, agreed): both pages are severely OCR-degraded — the grid renders as scattered tokens — so present in the corpus is not extractable today; the bounded task is a re-OCR of two known pages against the source images.~~ **[CORRECTED 2026-09-23, strategic session's own retraction, confirmed by the author's earlier read of the same pages: only PG345 — the diagram page — OCRs as tokens; PG346:C1–PG352:C1 is clean prose (~1,400 chars/page) that BUILDS the grid without the diagram: ten lines each way → 81 squares, the 16 vowels in the corner squares from the north-east, the 28 asterisms from Kṛttikā in the outer ring (PG346); weekday/tithi groups and the malefic set (PG347); the motion-dependent vedha direction (PG348); the five-fold scale (PG349); effects by motion and quarter (PG350-351); the sensitive-star set (PG352). So SBC is *buildable from prose today*; the bounded task is transcription from PG346-352 under the partition invariant migration 526's own docstring proposed, with a re-OCR of PG345 only as an optional cross-check of the diagram. "Page one is not a chapter" — the sparse-sample rule, applied to a text.]** One honesty item for the L0 owner: Adh. XXVI carries **two** 1-5 vedha-count effect scales — PG349:C1 (agitation, fear, loss, disease, death) and PG353:C1 (fear, failure, killing, death, ignominy; the battle context) — `bg_vedha_malefic_scale` cites PG353 and its row should say which scale and why. **C11** (Saṅgam's vedha edge) inherits qualification per row from these — it is no longer "unqualified on every row", it is *unqualified on the 39 mis-cited house-vedha parents until re-cited, verifiable on laṭṭā/scale parents.* G-9 ("admit Phaladīpikā") is therefore moot; what remains is re-citation + a page-anchored citation convention.
3. **M-2's "Phaladīpikā 23.11" resolves, at page grain, to `phaladeepika:PG299:C1`** (Adh. XXIII; OCR renders "Sloka 11" as "Sloka 77"): *"one, two, three, four, five, six, seven or eight benefic dots → (1) destruction or loss (2) expenditure (3) fear (4) fear (5) accomplishment of the desired object (6) acquisition of a damsel (7) gain of wealth (8) a kingdom."* So **"4 leans adverse" is verse-backed** — with the honest detail that Phaladīpikā gives **3 and 4 the same word (fear)**; the 4-vs-≤3 boundary of the three-state verdict comes from the BPHS bands (primary), not from this śloka. `verse_ref` in this corpus is page-based, so every chapter.śloka citation on this sheet needs its page anchor before stage 3 can verify it; this one now has it.
4. **"No node dṛṣṭi" — the "BPHS Ch.26" citation is REFUTED, the practice is UNCITED in the corpus, and the cost in Gochara is a whole λ factor, not 172 rows.** (i) Santhanam Ch.26 in the raw OCR (`SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt`, chapter head at line 16490): *"All planets aspect the 7th fully. Saturn, Jupiter and Mars have special aspects respectively on 3rd and 10th, 5th and 9th, and 4th and 8th"* — and the whole chapter span (16457–18361) has **zero** occurrences of rāhu/ketu/node (254 in the file overall). (ii) Table-level regex over all 15 texts for (rāhu|ketu|node) ∧ (aspect|dṛṣṭi) ∧ (5th…9th) returns only noise (Ketu *in* the 5th, malefics in 5th/9th, Sarvārtha Cintāmaṇi st.103 on planets' "sight" as physiognomy)

  **[RE-CHECK ATTEMPTED AND BLOCKED, 2026-09-23 — strategic session / DIS.031.** That session entered D-6 in
  `DISAGREEMENT_REGISTER_v1_0.md` as **DIS.031** (entered `20c21568e`, **corrected in place `68b0fd09d`** — cite the corrected revision) and graded this ground **ATTRIBUTED, not verified by
  the recording session** — correctly, and for the reason this campaign exists: it had not run the
  query itself. It also raised a sharper objection: `w30_nodal_drishti.py`'s docstring names
  **Phaladīpikā and Sārāvalī** as the rule's actual sources, and the BPHS Ch.26 refutation therefore
  disposes of a citation the module *already disclaims* while the two texts it points at go unread.

  **Two things, stated precisely.** (1) *Partly answered already:* the table-level query above was run
  against the table over all 15 texts, **Phaladīpikā (564 chunks) and Sārāvalī (471) included** — they
  were in scope and returned only non-granting rows (Phaladīpikā `PG429:C1`, an INDEX entry on
  Jupiter in transit; Sārāvalī `PG129:C2`, 7th-house relations). So they are not unexamined. (2) *But
  the objection still bites:* that query required an aspect term **and** a 5th/9th term **in the same
  chunk**, so a differently-phrased grant ("Rāhu, like Jupiter, sees the trines"), one split across
  chunk boundaries, or one degraded by OCR would be missed. A predicate-level read of **every**
  rāhu/ketu chunk in those two texts is the stronger check and **has not been done**. *(DIS.031 `68b0fd09d` adopted this downgraded grading and corrected its own 'not read by anyone' claim to the author's attribution; that session independently hit the same `ECONNREFUSED` twice, minutes apart, so neither session can discharge the item — the register says so, and the item stays OPEN pending N-14, 2026-09-23.)*

  **It could not be done when this was written.** The direct database path returned
  `ECONNREFUSED 127.0.0.1:5433` (the same outage that stopped the strategic session), and the remote
  search path — which does respond — **cannot establish absence**: this session measured it returning
  **zero** rows for a predicate with **17** matching rows in the table. A search run was made and
  returned nothing from either text; **that is recorded as a non-result, not as evidence.** Reporting
  it as absence would be precisely the failure this packet spent the day correcting.

  **Exact re-check to run when the database returns, before N-14 is ruled:**
  ```sql
  SELECT text_id, verse_ref,
         left(regexp_replace(coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,''),'\s+',' ','g'), 400)
  FROM classical_text_chunks
  WHERE text_id IN ('phaladeepika','saravali')
    AND (coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,'')) ~* '(rahu|ketu|node)'
  ORDER BY text_id, verse_ref;   -- read ALL of them for the predicate; do not conjoin an aspect term
  ```
  Until that read exists, **D-6's corpus ground is weaker than this sheet's original wording implied**:
  it is "not found by a conjunctive table-level regex including both texts", not "not found in the
  corpus". D-6's other grounds — the refuted BPHS Ch.26 citation, w30's own docstring concession, and
  Kimi's independent `[U]` grade — are unaffected, and Saṅgam's zero cost is unaffected.]**; Uttara Kālāmṛta PG41 restates the three-graha rule with no nodes. Grade: **not found at the table level** (stated regex; OCR-degraded text), not proven absent from the tradition. (iii) Gochara's own `gochara_v3/mechanisms/w30_nodal_drishti.py:8-21` docstring already says the rule "is NOT found in the original BPHS" and attributes it to later tradition — while `gochara_grammar/primitives.py:193-194` cites "BPHS Ch.26" for the same rule (Gochara F-29, a false citation). (iv) `_W30_NODAL_DRISHTI_ENABLED = True` (`gochara_v3/engine.py:107`) and `raw_lambda = promise × permission × activity × tara_modifier × **w30_modifier** × quality_gates` (`:632`): extending the ruling to Gochara removes a multiplicative factor and **invalidates every stored λ** — a same-generation change. Saṅgam's cost remains zero. The scope question above stands, now with the true cost in view.

**Resolution per decision (what the ruling binds; consequences drawn from the sheet's own text):**

| # | Ruling | Binds |
|---|---|---|
| M-1 / M-1a | agree — mean node; Placidus-as-stored; retire legacy scan after one generation; no node dṛṣṭi | Four contact contracts adopted (Parāśari directed + fractional; Moon-gochara + vedha; Tājika qualifier on all contacts, full Tājika annual only; Jaimini on a Jaimini route). **Node = mean** (L1's `RAH_MEAN`; the only citable node) with disposition **(b)** as the sheet's default unless the native says otherwise: true-node L0 knots retained, mean derived at read, ~1° disagreement declared per row, derivation in the L0 service. **Cusps = Placidus-as-stored**, house system on every row, Śrīpati only as a ratified variant with an L1 amendment. **Legacy scan** kept exactly one generation as `legacy_unsigned_angles`, then retired. **No graha-dṛṣṭi for Rāhu/Ketu** — nodes ship as gochara agents and targets only. |
| M-2 | agree, but 4 leans adverse; 6/8/12 inversion does not ship | Three-state own-BAV verdict (≥5 support / 4 indeterminate / ≤3 obstruct), conditioned by dignity in sign; **4 is recorded as indeterminate-leaning-adverse** (Phaladīpikā 23.11 "fear"). Vocabulary ledger (Santhanam bindu = adverse mark). BPHS bands primary, Phaladīpikā alternate, 28 → middle band. **Santhanam's 6/8/12 inversion gloss does not ship.** Mode D = BAV-supported ingress; producer completeness receipt now; kakṣyā deferred. **Cross-stream lock:** Kshetra S1 consumes the same admitted AV source. |
| M-3 | agree — §4.5 governs; owner = Gochara stream (kernel path if N-7 approved); E3 tier granted | **§4.5 re-affirmed as mechanism** — no ephemeris scan inside Saṅgam; consume pre-computed directed contact events; `planet` as a list, absent when nothing fires; §4.6's per-signature attribution kept as a refinement; inline-threshold principle applied upstream. **Owner = the Gochara stream**; **Path B (the pure kernel, N-5/N-7) if the native approves N-7 on the Gochara brief, else Path A (bounded `transit_search` amendment) under the same owner.** E1 and E3 remain gated on that N-7 ruling landing — **not unblocked today**. **E3 bounded fast tier granted**: Moon/Sun, tārā-vedha, laṭṭā inside qualified parents, all families enumerated, no cap, evidence count unchanged; vedha rows under the uniform admission rule (all `unqualified` today). `CLAUDE_CODE_PROMPT_KA_SANGAM_TRANSIT_REDESIGN.md` → SUPERSEDED-and-reissued against this integrated reading. |
| M-7 | agree | R-6 kernel separation: `activity` · `valence` · `applicability` · `availability`; dignity leaves the necessary product → valence; genuine gates survive only where classical; `kernel_version = legacy_i16` never pooled; `activity` scale (virupa vs [0,1]) left to implementation with the choice recorded. |
| M-4 | agree, but D30 for DOSHA held | Full ṣoḍaśavarga domain table adopted; no typed condition ever vetoes; relevant lords ratified line by line; boundary annotation carries the drekkāṇa rule; cancellation (nīca-bhaṅga) detector is a precondition; `chart_divisionals` becomes a declared L1 read with explicit missing states. **D30 as the DOSHA-predicate varga is HELD** — not adopted; DOSHA predicates take the domain varga as primary; D30 is computed and carried as a labelled `secondary_dosha` condition excluded from every score path, with a falsifier test (author decision under delegation, CLOSE D-4). |
| M-5 | agree | Station-loop episodes with child contact intervals; no default peak (vakra = 60 is strength, not date); aborted approaches kept as labelled children; `ka_taranga` unit = occupied-day union per month per (contract × valence-sign); split/merge/supersession published before any key change (R-5 first). |
| M-6 | agree; minimum n — **DECIDED under delegation, CLOSE D-1** | L5 may consume Saṅgam windows as prediction candidates once R-5 identity is qualified in the harness and outcomes are on two axes; `EMPIRICALLY_EVALUATED` stays closed behind the five conditions. **Minimum counts set by the author under delegation (D-1, amended 2026-09-23 per the Kimi K3 post-close review): n=35 per `(domain × route × method_version)` stratum (critical ≥12, α=0.0344, power 0.805 at 0.20→0.40); n=100 instrument-level pooled (critical ≥28, α=0.0342, power 0.833 at 0.20→0.32) via a stratified CMH-type estimand; `method_version` never pooled; figures are first-order approximations, so chart-level concordance and a published overdispersion check bind; below either → `PROVISIONAL_INSUFFICIENT_N`.** `ambiguous` adjudicated by the native, **excluded from n but retained in the reported rate's adverse end** (the interval's lower bound is Kimi's condition 4 verbatim), with a 10%/20% censoring gradient (D-2). Evaluation restricted to consenting charts with real outcomes (D-3). |

---

# Saṅgam — the seven rulings

How to read each row: **Kimi recommends** (condensed) · **Verified** (what I checked) · **My
position** (agree / agree with change / push back — with the reason) · **Astra's constraint** (what
any ruling must not violate) · **Your question**, with options.

---

## M-1 / M-1a — Contact contracts · legacy scan · targets per rule class · nodes

**Kimi recommends.** Adopt four versioned contracts in this order: Parāśari directed graha-dṛṣṭi
(full + fractional ¼/½/¾) → Moon-gochara + vedha → a Tājika *motion qualifier* (apply/separate/
station) folded into all contracts → Jaimini rāśi-dṛṣṭi only on a qualified Jaimini route → full
Tājika aspects only on the annual route. Keep the legacy scan one generation, never pooled; retire
it only after R-5's preservation manifest shows every dependent claim has a successor. Targets:
**sign** for gochara/vedha, rāśi-dṛṣṭi, aṣṭakavarga; **natal longitude** for graha targets under
dṛṣṭi; **bhāva-madhya** for house targets under dṛṣṭi (Śrīpati as default); relational predicates
get their own detector. Nodes: no dṛṣṭi (unverified); **mean node** as default convention.

**Verified.** BPHS 26.2-5 (sign-level aspects + fractional slabs), 26.6-8 (the six virupa rules;
Mars +15 at 90-120/210-240, Jupiter +30 at 120-150/240-270, Saturn +45 at 60-90/270-300; "for
house in aspect, consider the cusp") — **verbatim at BP1:16605-16652**. BPHS 8.1-3 Jaimini
degree-irrelevance — verbatim (per Astra, BP1:8686-8723). "Rāhu and Ketu who are always
retrograde" — **verbatim BP2:8959-8960**. Hāyanaratna valences [D-online].
**Code:** L1's natal positions are **mean-node** (`pyjhora_adapter/strength.py:195-197`: "mean-node-
patched … consistent with every other position fact this project stores"); the transit scanner is
**true-node** (`transit_search.py:10, 64`) — a live inconsistency that R-3 must close either way.
L1 already computes **Placidus** cusps (`ga_positions_writer.py`, `ga_kp_significators.py`) and
whole-sign; no Śrīpati anywhere.

**My position.** *Agree* on the four contracts, the order, directed search, fractional aspects
shipping in v1, the hybrid (sign interval survives without an exact pass), and the legacy-scan
retention rule. *Agree* on mean node — it is what L1 stores, so it is the §N.5-consistent default;
the scanner's true-node is the outlier. **Push back on Śrīpati:** L1 stores Placidus cusps today;
defaulting to Śrīpati adds a third house frame with no L1 fact behind it (B.10). Recommend:
bhāva-madhya = the cusp L1 *already stores* (Placidus, via the KP cusp facts), house system recorded
on every row; Śrīpati only as a ratified variant with its own L1 amendment.

**Astra's constraint.** Direction must be tested per special aspect and reverse branch (F-02); the
same geometry under two contracts is one root (A.3); relational/house triggers may need a different
detector, never coerced onto a natal point (F-01/RR-03).

**Your question.** (a) Confirm the four contracts and order? (b) Retire the legacy scan after one
generation, or sooner? (c) **House frame for cusp targets: Placidus-as-stored (my recommendation) /
Śrīpati (Kimi) / whole-sign only?** (d) **Node convention: mean (L1, Kimi, me) / true (scanner)?** — **Re-corrected 2026-09-23 (Gochara session's finding, author-verified at source): the split is FIVE-way, and `ephemeris_daily` is TRUE despite its contract.**
  (1) served L1 natal facts (`ga_positions` → pyjhora, `_jhora.py:23-55`) = **MEAN**;
  (2) `ephemeris_daily` knots = **TRUE** — `l0_ephemeris.py:290` calls `swe.calc_ut(jd, 11, …)` (11 = `TRUE_NODE`; 10 = `MEAN_NODE`) under a comment that says *"mean North Node"*; migration 624:30's probe contract says `node_mode="mean"`; the Gochara session's live read (Rāhu 1984-02-05 tropical 73.629°, TRUE 73.634°, MEAN 72.649°) confirms the store is TRUE — a **receipt-vs-data discrepancy** (DAR_CLOSE:20 records a MEAN rebuild), routed to L0's owner;
  (3) `transit_search.py:10, 64` = **TRUE**;
  (4) the legacy `brahmagyan/ganita/l1_positions.py:128` chain (`l1_dashas`, `l1_strength`, `l1_divisionals`, …) = **TRUE** (imports verified; persisted divergence not yet checked — a bounded L1/L0 check). (5) the *registered* `bg_cohort` writer — a fifth **independent** TRUE_NODE declaration (it reproduces `l1_positions`' formulas rather than importing them); the Gochara session's claim **reproduces at source** and the strategic session has confirmed it (its negative came from a `head -5`-truncated grep) (`pipeline/orchestrator/writers/bg_cohort.py:159` docstring "TRUE_NODE Rahu"; `:333` `("Rahu", swe.TRUE_NODE)` in the body list `calc_ut` iterates at `:340`; `@register("bg_cohort")` at `:470`) — the strategic session's negative did not; **verified, not `[U]`**. Its persisted-output divergence is the part still unchecked.
  **So Kshetra is not "mean/mean": its contract says mean, its store (via `ephemeris_daily`) is true.** The earlier scope note is withdrawn.
  **The ruling is not free — pair it with a disposition:** (a) rebuild `ephemeris_daily` mean-node (matches DAR's receipt; touches a frozen L0 layer and every consumer); (b) keep the knots true and derive mean Rāhu/Ketu analytically at read time — cheap, no L0 rebuild, but store and derivation then disagree by ~1° and that must be **declared** per consumer, never silent (Gochara session recommends this; recorded as its N-4a); (c) a declared mixed-frame contract per consumer. Author leans (b) with the disagreement declared on every row `[J]`.
  **Reading-visible consequence — stated in class, not as a specific pāda (withdrawn to class 2026-09-23 on the strategic session's reconciliation, which the author accepts):** a mean-vs-true Rāhu shift of ~1° against 3°20′ pādas **can move a natal pāda**, so this ruling is visible in a reading, not only in code. For your own chart the two sides are of unequal standing:
  - **Mean (authoritative, cited per §N.5 — the pāda is L1's own fact, nobody's arithmetic):** `chart_facts` **`060bb63b81a073bb`** `RAH_MEAN.pada = 3`; `67f32a2ca86253de` `nakshatra = Rohini`; `c520713087b97470` `longitude_sidereal = 49.0330441°` — all `lahiri_chitrapaksha`, engine pyjhora/1.0.0 (the mean-node adapter chain). Per the Gochara session's live check (not this page): `near_nakshatra_boundary_flag = false` — L1 itself asserts it is not near a boundary — and `source_calculation = pyjhora_adapter.positions`. Ketu: `KET_MEAN` 229.033°, Jyeṣṭhā pāda 1. **Structural, verified this session:** the served `graha_position` subjects for this chart are exactly `JUP, KET_MEAN, LAGNA, MAR, MER, MOON, RAH_MEAN, SAT, SUN, VEN` — **there is no `RAH_TRUE` subject**. L1 serves only the mean node and says so in the subject name; that settles the "mean = L1" leg of this ruling structurally, not by inference from an adapter flag, and it is *why* the true side has no fact to cite. **Honest tier:** every one of these facts is `verification_pass_status = single` — a permitted tier under §N.4's S7 ruling meaning nothing double-checked it. Cite them as L1's facts; do not read them as two-pass verified.
  - **True side — measured on Swiss (corrected 2026-09-23; the Kshetra session was right that it is determinable here):** the Swiss files ARE on this host (`/private/tmp/se1/{seas,sepl,semo}_18.se1`, placed 2026-09-22 17:20; `brahmagyan.l0_ephemeris._resolve_ephe_path()` → `/tmp/se1` — the production resolver's own candidate). Every "Moshier" figure earlier today, the author's included, came from scripts that never set the path. With the path set (`retflag 258 = SWIEPH|SPEED`, no Moshier bit): **true Rāhu at the birth instant — 1984-02-05 05:13 UT = 10:43 IST, jd 2445735.717361 — = 50.049248° sidereal Lahiri → Rohiṇī pāda 4**, 177″ from the boundary against arcsecond precision. **The instant is pinned by L1 itself:** Swiss MEAN at that instant = 49.033044°, **0.0″** from L1's `RAH_MEAN` fact — so this is L1's birth instant. The Kshetra and strategic sessions' 50.0451° is the **same instant** — the 14.82″ gap is **nutation**: `FLG_SIDEREAL` applies the *apparent* ayanāṃśa (with nutation) and reproduces L1's fact to 0.00″, so it is the project convention; `tropical − get_ayanamsa_ut` applies the *mean* ayanāṃśa and is the outlier (author-verified: difference +14.82″, nutation in longitude at jd −14.82″). The author's earlier "thirty-minute slip on their side" diagnosis was **wrong** and is withdrawn; the instant-pinning by L1's fact was right. Both methods land in pāda 4 (177″ / 162″), so the conclusion is convention-independent — but **three conventions now govern one longitude** (node frame, epoch, ayanāṃśa application) and **none is recoverable from the data**; a cited number carries its instant *and* its ayanāṃśa method. **Consumer consequence (strategic session's point, adopted):** because L1 stores no `RAH_TRUE`, the true natal value is *computed at read time and stored nowhere* — any consumer wanting it recomputes it and silently inherits whatever epoch and backend its caller happens to use. That is the M-1d cost in one sentence — now *three* ways to be wrong (epoch, backend, ayanāṃśa method), none visible in the data. **Two further measured figures (strategic session; not re-verified by the author):** Moshier's true-node error against Swiss, **measured over the full domain — every noon knot 1950-01-01 → 2100-12-31, 55,152 knots, Swiss `retflag` asserted on each call — is bounded at |65.3″|** (worst 1972-11-20; min −58.1″), measured by the Gochara session, reproduced by the strategic session, and **reproduced independently by the author** (1.6 s on this host). Both earlier sparse figures — 18.1″ from five dates, 32.5″ from sixteen decade-spaced dates — under-reported in the same direction, because the node's error oscillates on sub-decade timescales. **Rule earned (the third beside "a date is not an epoch" and "a flag is not a backend"): a sparse sample is not a bound.** Consequences, stated as ratios not adjectives: the natal margin 177.3″ is **2.7×** the bound — reportable on either backend, a real margin but not a comfortable one; the stored-knot margin 6.3″ is **10.4× under** it — not reportable on any backend, and never was. And a caveat for R-3 and the Gochara stream: 65.3″ is ~200× the inherited W2G spline-accuracy figure (0.314″); if that validation ran without `set_ephe_path`, it compared its spline against a reference two orders of magnitude coarser than its own claim — whether the V3 runner sets the path is answerable from source and must be answered before 0.314″ anchors any gate. And the sharpest single statement of why a knot is an interpolation input and never an answer: **same body, same day — noon knot TRUE 49.998° = pāda 3; birth instant 50.049° = pāda 4** — opposite sides of a classical boundary. **This is an author computation with full provenance (engine SWIEPH, files + sha256, ayanāṃśa, instant), not an L1 fact — L1 serves no `RAH_TRUE` subject.** If the true-node pāda ever bears on a reading, L1 should serve it; §N.5 forbids this sheet from standing in for that. The earlier "true may land in pāda 3" came from carrying a Moshier *knot* offset across epochs — a mis-carry, withdrawn by its author.
  - **The stored knot, exactly:** `ephemeris_daily` Rāhu 1984-02-05 tropical 73.629058 = Swiss TRUE at **12:00 UT** to six decimals (author-verified). So the store is true-node at Swiss precision, at a **noon-UT epoch** — and the row declares **neither its node frame nor its epoch**. Two sessions were misled by the undeclared epoch in one day; that is the second half of the same §N.8 finding against `bg_ephemeris`. The knot's own proximity to the pāda boundary (49.998°) is a transit sample on the birth *date*, irrelevant to the natal pāda, and is dropped from this sheet.
  - The strategic session's five-date residuals (stored vs Swiss TRUE ≤ 0.104°, vs MEAN 0.95–1.47°) carry the same Moshier caveat; the **convention** conclusion is untouched — tenfold discrimination survives any 0.1° error. **Live incidence (strategic session, DB-verified 2026-09-23; not an author measurement):** for the canonical chart 40 `gochara_resonance_map` targets are Rāhu/Ketu; node contacts on **232 of 914 rows at generation `g3_utkarsha` (served, via `term_breakdown`) and 50 of 87 at generation 2.0 (via `active_sentences`)** — the strategic session's corrected figures (its earlier "242" summed both generations without a filter) — the mean/true split is reached and served, not latent. Three readers: `ka_gochara/service.py`, `ka_kshetra/stage0_kinematics.py` (mean, via `ephemeris_daily`), `ka_sangam/engine.py` (true, via the scanner). Strategic session concurs: mean node; hub repair before any of the three rebuild. M-3 owner routed to you with the recommendation that the **Gochara stream owns the bounded `transit_search` amendment** (blueprint v1.1 §11.2), Kshetra and Saṅgam as named consumers.
(e) Any graha-dṛṣṭi for Rāhu/Ketu — which houses, on the authority of which text?

**Evidence rule adopted from the Gochara session (2026-09-23), binding on plan R-3 and every §3b SPEC:** `ephemeris_backend` (`swieph` + the three `.se1` checksums, or `moshier`) is an explicit member of the frame/convention vector, because comparability and any `tolerance_arcsec` depend on it. **And two more beside it — `epoch_convention` (Gochara session) and `ayanamsa_application` ∈ {`apparent_flg_sidereal` (project convention, reproduces L1), `mean_get_ayanamsa_ut`} (strategic session, after the 14.82″ nutation episode): a date is not an epoch — `ephemeris_daily` knots are at 12:00 UT (`l0_ephemeris` builds every knot at `swe.julday(y,m,d,12.0)`; W2G: "KNOT ABSCISSA: NOON UT"), and a midnight-vs-noon mismatch is exactly the 332″ that briefly looked like a cross-host ephemeris disagreement. Every cross-source geometric comparison states its instant. Detector for the backend: the returned `retflag` (bit 4 = MOSEPH) — a silent fallback cannot fool it; S8 v2.1 asserts it. A geometric assertion of **accuracy or tolerance against Swiss** run without `.se1` present is **NOT_RUN**, never PASS — Moshier compared with Moshier cannot fail (§N.8). Assertions of **logic** (counts, grouping, interval membership) may run on Moshier with the backend recorded. Audit of the current suite: only S8 touches Swiss; it asserts loop count and crossing counts (topology), states its backend, and makes no accuracy claim; no Saṅgam artifact cites the W2G 0.314″ spline figure — which the Gochara session has marked `[U]` pending the V3 run's environment. **Directed aspects — where the defect actually lives (strategic session, author-verified at source):** the Gochara grammar does it right — `gochara_grammar/primitives.py:342-343` passes `SPECIAL_DRISHTI_DEG.get(planet, …)` per graha (`:189-195`: Mars 90/180/210, Jupiter 120/180/240, Saturn 60/180/270, nodes as Jupiter), and `drishti_contact` fires on 379 of 914 served rows. The defect is at **Saṅgam's call sites**: `engine.py:464-467` passes the symmetric `[0,60,90,120,180]` for Jupiter and Venus (benefic dṛṣṭi), and `:213`/`:1148-1150` likewise for the main scan — into `transit_search`'s unsigned `target + angle` search. So F-02 stands **as a Saṅgam defect**; the fix routes to Saṅgam, not to the producer, and "zero served rows carry an asymmetric degree" is **withdrawn** (that field cannot hold a degree).

---

## M-2 — Aṣṭakavarga ledger

**Kimi recommends.** (i) Record the mapping: *stored integer = count of auspicious marks*;
Santhanam calls these **rekhās** (his *bindus* are the adverse dots); say "benefic marks" in prose.
(ii) Do **not** ratify "≥4 support / ≤3 obstruct": Phaladīpikā 23.11's own enumeration puts 4 with 3
("fear"); ratify a **three-state verdict {support ≥5, indeterminate = 4, obstruct ≤3}**, every verdict
conditioned by the transiting planet's dignity in the sign (23.10). (iii) Keep both SAV bands
school-labelled, BPHS three-band primary (>30 / 25-30 / <25, in rekhās), Phaladīpikā >28 as
alternate, 28 → middle band by declaration; never two votes. (iv) Mode D → BAV-supported ingress
with SAV as context. (v) Kakṣyā deferred; **missing-planet producer receipt now**.

**Verified.** BPHS 66.13-15 vocabulary — **verbatim BP2:35666-35676** ("inauspicious … dots (bindus)
… auspicious … small vertical lines (rekhas)"). BPHS 72.3-5 bands in rekhās, plus Santhanam's
*note* on 6/8/12 inversion being a gloss — **verbatim BP2:42332-42369**. **Phaladīpikā 23.11 —
verified online, verbatim:** one…eight benefic dots → "destruction or loss, expenditure, fear,
**fear**, accomplishment of the desired object, acquisition of a damsel, gain of wealth, kingdom."
23.10 conditioning ("in their own, exaltation, friendly or upacaya places … advance") and 23.20
(>28) on the same page. Kimi's "0 = loss of life" — **not on the page, [U]**.

**My position.** *Agree in full.* The three-state verdict is the honest encoding of a text that puts
4 in the adverse half while practice calls it average; it neither inflates nor contradicts. The
vocabulary mapping is a dictionary amendment, not a data change (A-02). Producer receipt now is
right — RR-02 proved reader-level recovery impossible.

**Astra's constraint.** Not `BAV/8` into a nonnegative combiner (F-04/RR-05); SAV contains BAV —
one lineage (D.3); the frame is *settled*, not open (RR-02).

**Cross-stream (added 2026-09-23, from the Kshetra session, author-verified):** Kshetra's `av_kaksha_gate` covariate is a declared `not_in_corpus` gap (`stage1_symbolization.py:346`). Whichever AV source you admit here — E2's signed testimony or `ganita_av_transit_gating` directly — **Kshetra S1 must consume the same one**, so the layer carries **one AV verdict per instant** (U02). Kshetra's decision list §7 item 4 mirrors this.

**Your question.** (a) **BAV = 4: indeterminate (text; Kimi; me) or support (modern practice)?**
(b) Within "indeterminate", does 4 lean adverse (23.11 says "fear") or neutral? (c) BPHS bands
primary with Phaladīpikā as alternate — confirm? (d) Does the 6/8/12 SAV inversion (Santhanam's
gloss, not verse) ship at all?

---

## M-3 — The integrated June ruling (blocking E1 and E3)

**Kimi recommends.** **Re-affirm §4.5 as the governing mechanism** — no ephemeris scan inside the
Saṅgam writer/engine; Saṅgam consumes pre-computed transit events from an upstream producer;
`planet` becomes a LIST, absent when nothing fires — and **declare §4.6 superseded as authority for
in-writer scans**, keeping three of its rulings as refinements (per-signature *attribution* within
the slow channel; no count caps; inline threshold applied *upstream*). Retire the READY prompt as
written. E1's directed geometry is within the ruling **if produced upstream**. E3's fast tier is
within intent only as conditional refinement inside a qualified parent, evidence count unchanged —
grant it as a one-paragraph bounded amendment. Ranked fast witnesses: Moon's house-from-Moon
(Ph. 26.2/26.12), tārā-vedha stars (26.26-29), laṭṭā (26.42-44, producer already served), Sun's
house/saṅkrānti (26.9-11, 26.29), decanate phase (26.25). The muhūrta tārā-bala form stays [U]. **Condition mirrored from the Kshetra session (2026-09-23), adopted:** reuse of the served vedha producer is **per `vedha_kind`, not per table** — `house_vedha` rows enter as F06 `applied` — **verified source chain (re-corrected 2026-09-23; an earlier version of this line named a relation `bg_phaladeepika_vedha` that does not exist — it is a writer *filename*, migration 528 creates `bg_phaladeepika_latta` and `bg_vedha_malefic_scale`; the error propagated from a peer message and the author copied it):** `ka_vedha_gochara` (`services/ka_vedha_gochara/writer.py`) reads house-vedha rules from **L0 `bg_transit_rules`** (`rule_type='favourable' AND vedha_house IS NOT NULL`, `:99-101`; Phaladīpikā Ch.26 co-cited — the "BPHS Ch.29" half of that co-citation is a mis-citation *in the L0 data and the L3 writer's own docstring* (`logic.py:13-14, :105`; Ch.29 is Bhāva Padas), struck by the L0 owner under Gochara F-23/G-8); **sarvatobhadra** from `bg_sarvatobhadra_grid` (`:115`); **laṭṭā** from `bg_phaladeepika_latta` (`:123`; migration 528, Phaladīpikā PG338-339 ślokas 42-44); the **malefic scale** from `bg_vedha_malefic_scale` (`:128`; PG353, ADJUDICATION-11 — which belongs to the scale, not to a vedha-rules table); positions from `ephemeris_daily` (`:106`). **Shared vocabulary across the three packets (Gochara plan v2.0 §5.4):** every `ka_vedha_gochara` row carries `source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}` derived from its own `classical_citation` / `grid_basis` / `uncited_extension` — house_vedha and laṭṭā read `verse_cited` by construction (Ketu is laṭṭā's disclosed classical gap), sarvatobhadra reads `algorithmic_approximation` where `grid_basis` says so — and `precision_regime = 'date_grain'` until kernel ingress instants land. **Consumer admission — corrected a second time 2026-09-23 (Kshetra v1.4, caught by the Gochara session; author-verified):** the policy this line carried an hour ago — house_vedha `applied`, laṭṭā `unqualified`, on the ground that Phaladīpikā is outside the admitted corpus — was **inconsistent**: after the BPHS Ch.29 strike, *every* house-vedha rule also rests on Phaladīpikā Ch.26. Same text, opposite verdicts, one reason. **Uniform rule (Saṅgam, Kṣetra, century alike):** a `ka_vedha_gochara` row is F06 `applied` **iff** the producer's `corpus_verifiable = true` (Gochara §5.4 (iii): the cited text is present in the admitted corpus — today BPHS, Jaimini Sūtram, KP, KP Reader only) **and** geometry passes the vedha integrity conjuncts; **otherwise `unqualified`**. ~~Today `corpus_verifiable` is false for every gochara-vedha row, so house_vedha, sarvatobhadra and laṭṭā all enter `unqualified`, verse-cited or not.~~ **[SUPERSEDED 2026-09-23 — premise false (directory mistaken for corpus); see §Corrections item 2 above: outcome is per `vedha_kind` — laṭṭā and the malefic scale verifiable now → `applied` where geometry passes (Ketu excepted for laṭṭā); house-vedha `applied` on L0 re-citation to Phaladīpikā XXVI PG322-323; SBC `unqualified` until the grid is populated from PG345-346.]** Geometry checkability is computational correctness, not source qualification — F24 keeps the tiers apart. ~~Lifts row by row when the corpus/L0 owner admits the text~~ **[SUPERSEDED 2026-09-23: the text is already admitted — lifts on L0 re-citation at page grain, Gochara F-23/G-8; G-9 is moot]** (Gochara G-9: admit Phaladīpikā and, for rows to stay verse-cited, Sārāvalī / Jātaka Pārijāta — or re-grade every gochara-vedha row as cited-outside-admitted-corpus for all three consumers). **Consequence for Saṅgam's own C11 vedha edge (`ka_sangam.py:1037-1045`, `engine.py:282-297`):** ~~it is *source-unqualified today on the same ground*.~~ **[SUPERSEDED 2026-09-23: C11 inherits qualification per parent row — see §Corrections item 2.]** The 0.3 dampener is computationally defined but acts as if qualified; the sheet's position is that C11 carries F06 `unqualified` and `corpus_verifiable = false` on every row it touches until G-9 lifts it, its 0.3 *value* is `[NATIVE-RATIFY]` not doctrine, and under R-6 it becomes a signed condition rather than a necessary multiplier. W0 consequence (routed to the strategic session by Kshetra): FOUNDATION_SAFETY §5:207-209's "existing source-qualified ordinary reference" *is* the struck citation — ~~the layer currently has no corpus-verifiable vedha reference at all; `sarvatobhadra` and `latta` enter as `unqualified` until source-qualified~~ **[SUPERSEDED 2026-09-23 — see §Corrections item 2: laṭṭā is corpus-verifiable at PG338-339 and enters `applied`; SBC unqualified for being unpopulated, not unsourced]** (FOUNDATION_SAFETY §5: sarvatobhadra "remains unqualified"; laṭṭā separately scoped) — never `applied` by virtue of sharing the table. And `kala_vedha_gochara` windows are **DATE-grain**: any child sub-peak that cites them stamps `precision_regime` accordingly. This also binds C11 today.

**Verified.** June §6 prohibition ("Do NOT re-introduce any ephemeris scan inside ka_sangam") — read
this session; the landed code scans (`find_aspect_events` inside `mode_a_search`, S1/S7). BPHS 47
per-strength delivery — verbatim. Phaladīpikā 26.x fast-body gochara [D-online]; tārā-vedha stars
and laṭṭā verses [D-online, not re-verified by me].

**My position.** *Agree with the reading* — it is the only one consistent with §6, and it turns E1's
geometry into an upstream event contract, which is where R-3's scanner amendment already had to
land. **Add one thing Kimi did not say:** the upstream producer is `transit_search.py` /
`ka_gochara`'s service — **the Gochara stream's territory**, frozen against Saṅgam edits (S-I). So
this ruling creates a cross-stream obligation: name the owner of the directed-event producer and its
bounded amendment before E1 can proceed. Without that, "§4.5 re-affirmed" is a ruling nobody can
execute. On the E3 amendment: *agree* to grant it in exactly the bounded form (inside qualified
parents, all families enumerated, no cap, evidence count unchanged).

**Astra's constraint.** Existing fast-trigger reachability is not retrospective authority; the
integrated ruling must cover both E1 and E3 (B.3, D.1); "complete inside selected parents" ≠
"complete chart refinement" (D.2).

**Producer paths (added 2026-09-23 after both L3 sessions replied):** the strategic session recommends the **Gochara stream owns a bounded `transit_search` amendment** (blueprint v1.1 §11.2). The Gochara session's own brief instead proposes a **new pure kernel** (`services/gochara_kernel/**`, N-5/N-7: unimported until adopted; emits directed contact episodes with `t_in / t_exact / t_out`, bracket, tolerance, branch, orb + source, and a Search-coverage row per partition; **edits neither `transit_search.py` nor `ka_dasha_kala`**). Saṅgam's E1/E3 can bind to that kernel and avoid the shared-hub edit entirely — the better shape, and Kshetra S0 could adopt the same module later. **Caveat stated plainly:** the kernel is an unruled proposal (Gochara brief stages 0–2, `PROPOSED_FOR_NATIVE_RULING`); if you rule against N-7, Saṅgam is back to needing the `transit_search` amendment with a **single** named owner. Neither peer session will name that owner — correctly; it is yours.

**Your question.** (a) **§4.5 re-affirmed as mechanism, §4.6 kept as attribution — yes/no?**
(b) If yes: **which producer — the Gochara kernel (N-5/N-7, if you approve it) or a `transit_search` amendment — and who owns it?** `transit_search.py` may not be edited from Saṅgam. (c) **Grant the bounded E3 fast
tier?** (d) Is the Sun in the slow set as a calendar witness (§4.5 lists Saturn/Jupiter/Rāhu/Ketu)?
(e) Mark `CLAUDE_CODE_PROMPT_KA_SANGAM_TRANSIT_REDESIGN.md` SUPERSEDED-and-reissued?

---

## M-7 — Score-kernel separation (new)

**Kimi recommends.** Adopt the four fields — `activity` (nonnegative), `valence` (signed),
`applicability`, `availability` — with **dignity removed from the necessary product** and re-seated
in valence. *No classical warrant for dignity as a gate*: BPHS 47.3-4 scales delivery by strength
(a nīca lord delivers *trouble*, not silence — nīca-bhaṅga presupposes delivery); Phaladīpikā
23.23-24 composes valence from nature × dignity × lordship (a benefic owning a duḥsthāna injures
even exalted); 23.10 "generally fails to sustain" is graded. The shape maps the classical
**bala** (nonnegative) / **phala** (signed) distinction. `activity` on the 26.6-8 virupa scale
(leans). Genuine gates survive only where classical: orb of light, itthaśāla motion, route
eligibility. Legacy `kernel_version = legacy_i16`, never pooled.

**Verified.** BPHS 47.3-4 — verbatim BP2:8939-8960. BPHS 27.21-23 cheṣṭā values (vakra **60**,
maximum) — **verbatim BP1:22725-22742**. Phaladīpikā 23.10 — verified online; 23.23-24 [D-online].
Code: `convergence_score([0,1,1], full support)` → **0.0** (S11).

**My position.** *Agree in full.* This is the strongest recommendation in the set — three
independent anchors, and it dissolves the reviewer's RR-05 without inventing a scalar. The virupa
scale for `activity` is attractive because it is self-documenting; I would still leave normalised
vs virupa to you (`[J]`).

**Astra's constraint.** Signed labels around a nonnegative combiner cannot carry adverse testimony
(RR-05); legacy/new must have explicit compatibility selection; consumers select fields explicitly.

**Your question.** (a) **Dignity leaves the necessary product — yes?** (b) Four fields, or a fifth
`route` dimension outside applicability? (c) `activity` in virupas (textual) or [0,1]? (d) Is there
any configuration in your practice that produces *nothing* (as opposed to evil) — if so it becomes
an applicability rule, never a multiplier.

---

## M-4 — Typed natal / clock conditions

**Kimi recommends.** Confirm D7/D9/D10/D4 and extend from the same verse: D2 wealth, D3 co-born,
D12 parents, D16 conveyances, D20 worship, D24 learning, D27 strength, **D30 evil effects** (natural
varga for DOSHA-class predicates), D60 deferred. Relevant lords per domain = D1 domain-bhāva lord +
natural kāraka + (per school) the domain varga's lagna lord — each one's *natal* dignity in the
domain varga, with cancellation evidence. **No typed condition ever vetoes.** Carry
`boundary_distance` as annotation *with the drekkāṇa-phase rule alongside it* (BPHS 47.3-4: lord in
first/second/third drekkāṇa → effect at start/middle/end; reversed when retrograde; nodes always
reversed), so the annotation carries doctrine, not a bare number.

**Verified.** BPHS 7.1-8 full sixteen-varga table — **verbatim BP1:7569-7593** (D2 wealth, D12
parents, D24 learning, D27 "strength and weakness from Bhamsa", D30 "evil effects", D40, D45, D60).
BPHS 47.3-4 drekkāṇa phasing + reversal — verbatim. L1 stores a `retrograde_flag`
(`ga_prashna_writer.py:142`; `ga_positions_writer.py` handles retrograde) — natal retrograde state
is available [C-partial]. Kāraka verse pins [U]. D30-for-DOSHA is Kimi's [J].

**My position.** *Agree* on the table, no-veto, natal-only, and carrying the drekkāṇa rule with the
annotation — that last point improves on my plan (a bare `boundary_distance` was a number without
doctrine). *Agree with change:* the "relevant lords" registry must be ratified **line by line**, as
Kimi says; do not automate it. The D30-for-DOSHA mapping is a proposal to rule, not doctrine.

**Astra's constraint.** Adverse ≠ inapplicable (F-08); capability aggregate cited, never re-voted;
"hold every other fact fixed" fixtures (RR-03).

**Your question.** (a) Confirm the extended varga–domain table? (b) Per-domain relevant-lords list —
rule it line by line (I will draft from BPHS kāraka verses for your ratification). (c) D30 as the
DOSHA varga — yes/no? (d) Confirm: no typed condition vetoes.

---

## M-5 — Episode conventions

**Kimi recommends.** Station loop is the **sole** linkage (it is the only generator of multiple
contacts for one graha/target/angle); nearness must not link across loops. Children = each pass
with orb entry/peak/exit, identity, precision, truncation flag; hull = envelope; occupied time =
union; no default peak. Aborted approaches (station before exactness) are children labelled
`approached, never perfected` — classically "no itthaśāla" but sign-level applicability survives.
>3-contact and truncated episodes carry `truncated: start|end` with measured partial occupancy.
**`ka_taranga` unit: occupied-day union per month per (method-contract × valence-sign)** —
additive, duplicate-invariant, respects partial months.

**Verified.** BPHS 27.21-23 vakra = 60 (max), vikala = 15 — verbatim: the retrograde pass is the
*strongest* phase, so it is neither noise nor an automatic event date. Hāyanaratna 3.3 motion rules
[D-online]. Code: `ka_taranga.py:161-169` averages one contribution per intersecting row per month
(RR-05 sibling) — confirmed.

**My position.** *Agree in full.* The taranga unit is the concrete answer Astra asked for
("month-set union is insufficient"); it is mechanically checkable by duplicate-insertion
invariance. Aborted-approach children are a real gap in my plan — adopt.

**Astra's constraint.** Crossings ≠ orb-interval occupancy (RR-03 E5); every child and its interval
survive (D.2); grouping is not an ICC repair (F-09).

**Your question.** (a) Loop-as-sole-linkage — confirm? (b) Do aborted approaches count in E6's
episode numerator (Kimi leans yes as `perfected: false`)? (c) Taranga unit as proposed?

---

## M-6 — Consumption and evaluation boundary

**Kimi recommends.** Yes — once R-5 identity is qualified in the harness and outcomes are on two
axes, L5 may consume Saṅgam windows as **prediction candidates**. `EMPIRICALLY_EVALUATED` stays
closed until five conditions hold: predeclared protocol (estimand, horizon, population, version
frozen); held-out issuance chronology (reuse `01_FACTS_LAYER/LEL_HELD_OUT_PARTITION_v1_0.md`,
`06_LEARNING_LAYER/PREDICTION_LEDGER/`); native-ratified minimum n per (domain × route × version)
stratum; censoring rules (open windows `censored`, never misses; `unobserved` ≠ `miss`; `ambiguous`
stays in the denominator, fraction disclosed); base-rate discipline (hit rate vs coverage fraction).
No classical basis — and saying so is part of the discipline.

**Verified.** Both cited artifacts exist. Two-axis record matches RR-07. Existing Bhaviṣya writer
fails closed on ambiguous reattachment (per Astra).

**My position.** *Agree in full.* The one sentence worth underlining: *the machinery must be willing
to say "no demonstrated skill," or it is RR-01 rebuilt at L5.*

**Astra's constraint.** Model invalidation ≠ outcome miss (F-12/RR-07); an L5 hook permits
observation, it does not earn `EMPIRICALLY_EVALUATED` (B.6).

**Your question.** (a) Open consumption on those preconditions — yes? (b) Minimum n per stratum —
your number. (c) Who adjudicates `ambiguous`?

---

## Cross-decision coherence (Kimi's check, endorsed)

M-1 supplies geometry; M-7 rules geometric intensity can never be erased by natal condition; M-2 and
M-4 supply signed valence — so an adverse-but-intense window is representable end to end. M-3's
mechanism (upstream events) is what licenses M-1's directed contracts under the June ruling; E3's
children never increment witnesses, the same one-root discipline as M-1's two-labels-one-root,
M-2's SAV-contains-BAV, M-4's cite-don't-revote. M-5's occupancy union feeds both `ka_taranga` and
M-6's exposure denominator. No new scalar anywhere. **One tension, named:** M-3's slow-channel
discipline vs contract (a)'s Moon-centrism — resolved only if the E3 amendment is granted; if it is
refused, contract (a) narrows to slow carriers and Phaladīpikā 26.12's Moon material waits.

## The three questions Kimi would ask before you rule (endorsed, with my additions)

1. **June integration + E3 amendment** (M-3 a/c) — the only "no" that *deletes* textual capability
   rather than deferring it. **My addition:** name the upstream producer's owner in the same breath.
2. **BAV = 4** (M-2 a/b) — the text says "fear"; practice says "average"; the highest-blast-radius
   threshold in the ledger.
3. **Nodes** (M-1 d/e) — mean vs true, and any dṛṣṭi. **My addition:** the codebase is already split
   (L1 mean, scanner true), so this is a live repair either way, not a preference.

**And one Kimi did not ask, which I would:** **House frame for cusp targets** (M-1 c) — L1 stores
Placidus; Śrīpati would be a third system with no fact behind it.
