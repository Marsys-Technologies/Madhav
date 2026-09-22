---
artifact: KALA_PRE_ELEVATION_CRITICAL_REVIEW
canonical_id: KALA_PRE_ELEVATION_CRITICAL_REVIEW
version: "1.1"
status: AWAITING_NATIVE_RULING
date: 2026-09-22
reviewed_against:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md (CCD-010)                  # "Product"
  - briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md (DP-SD-009)      # "VA"
  - briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md       # "F"
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (DP-SD-017)        # "Strategy"
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md             # "Brief"
reviewed_artifacts:
  - audit/KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md v1.1 + 9 deliverables
  - KALA_NATIVE_RULING_SHEET_v1_0.md
  - KALA_ELEVATION_READINESS_PACKAGE_v1_0.md (7 lanes)
  - "the four-phase pre-elevation plan the native approved ('rest all is good') — exists ONLY in conversation; no artifact carries it (verified by repo grep)"
does_not_authorize: any change. Every item is a proposal until the native rules.
changelog:
  - "1.1 (2026-09-22): addendum §9 — the W0 tier beneath the Strategy was never read by this review; three items corrected (C1 reframed, A2 narrowed, A6 reversed) and the accepted 2026-09-15/16 source work credited. Body unchanged as audit trail."
  - "1.0 (2026-09-22): first issue."
---

# Critical review of the Kāla pre-elevation setup

**The question asked:** is what we have assembled aligned with the product definition, the
data-plane strategy and the L3 strategy — from the user's perspective — and what should change,
be added, or be dropped before execution.

**The short answer:** the *findings* are sound and survived adversarial re-reading. The *plan*
built on them is not yet aligned. It is asset-shaped where the governing texts are
question-shaped; it invents vocabulary the foundation contract already ratifies; it omits the
one architectural substrate the strategy makes its spine; and in two places it contradicts a
standing ruling. None of this is fatal. All of it is cheaper to fix now than after execution.

---

## 1. What changes (eight corrections, most serious first)

### C1 — The plan omits the generation / compatible-dependency substrate. This is the spine.

The strategy's §4 lifecycle is explicit: *"Bind one compatible transitive dependency vector …
All input reads use those snapshots … no implicit fall-through to mutable `public` rows … Publish
/select the complete compatible generation; downstream eligibility opens only after this data
acceptance."* F09 makes it plane-wide. VA §11: *"Independently choosing each layer's latest rows
is insufficient."*

The four-phase plan says nothing about generations. Yet generations are the mechanism by which
**every one of the native's own stated objectives** becomes achievable:

- *"If it gets wiped, we rebuild"* is safe only if the previous generation is retained until the
  new one is published — that is what a head/partition model gives you.
- The cascade (five `kala_*` tables emptied by any L2 rebuild) is solved structurally by binding
  Kāla rows to an L2 **generation**, not to a live surrogate `signal_id`.
- The determinism gate the plan proposes ("build twice, diff") is *undefined* without a pinned
  input vector: today the inputs are mutable `public` rows that L2's active campaign changes
  underneath a running build.

Measured today: the L1/L2 generation tables exist; **zero generations have ever been opened for
either** (`l1_data_plane_generation_heads` = 0, `l2_…` = 0). No L3 head table exists. So the
strategy's W1 — "establish physical upstream truth" — has never been exercised, and L3 has
nothing to bind to. Also measured: **79 rows** in `kala_activation_predicates` for the canonical
chart point at `signal_id`s that no longer exist in same-chart MSR — exactly the number the
strategy reported. The layer therefore has *both* failure modes at once: tables emptied by
cascade, and tables that survive with dangling references. Neither is coherent, and generation
binding fixes both.

**Change:** Phase 1 gains, ahead of the temporal contract, *"adopt the 1035/1036 generation
pattern for L3 and bind to published L1/L2 generations."* This is Domain D's open decision; it
must be ruled, not deferred. It also makes the dependency on the L2 campaign visible: L3 cannot
bind until L2 **publishes** a generation, which it has not yet done.

### C2 — "Define a qualification vocabulary" would create a rival definition. Bind instead.

The plan's central item was to *define* what confidence/salience means so the LLM can reconcile.
But the foundation contract already ratifies the vocabulary, and creating another is the exact
failure F01/DP01 prohibit ("no rival definitions"):

- **F04** — six epistemic classes (`SOURCE_TESTIMONY` … `EVALUATION_EVIDENCE`).
- **F06** — six completeness states (`applied`, `inapplicable`, `unavailable`, `unqualified`,
  `contradictory_unresolved`, `unexplored`), with the rule *"no null/zero/empty fallback
  collapses these states."*
- **F12** — eight operator roles an input can play.
- **Strategy §3, "Temporal testimony"** — the exact L3 object: *target structure, exact evidence
  roots, method/family, units/polarity, applicability, support/opposition/silence,
  **independence group** and material uncertainty.*
- **Product §5.2** — *"Keep deterministic fact, structural prior, classical prior, empirically
  calibrated claim and unresolved interpretation distinct. A probability, a comparative structural
  grade, an astronomical timestamp and a reliability interval are not substitutes."*

That last line is the one the native's revised stance must respect. **A single "salience" or
"confidence" scalar per reading is precisely what §5.2 forbids.** What the LLM needs is *typed*
confidence: which epistemic class the claim is, which completeness state each method is in for
that window, which independence group it belongs to, and whether two quantities are even on a
comparable scale (L3-Q05: "non-comparable scales"). One number cannot carry that.

**Change:** replace "define a qualification vocabulary" with *"bind every Kāla output row to
F04 + F06 + F12 and the Strategy §3 Temporal-Testimony object; add no new field that these
already cover."* Lane E's `tier_basis = 'relative_uncalibrated'` finding shows the layer already
does part of this honestly — extend that discipline rather than replace it.

### C3 — The baseline must be the thirteen ratified questions, not sixteen invented ones.

Strategy §2 ratifies **L3-Q01–Q13**, each with its required added distinction and a named
primary proof. Lane E produced a fresh portfolio of sixteen (Q-K01–16). Those are useful as a
check on coverage, but adopting them as the acceptance baseline would create a second question
authority — the pattern this whole review keeps finding. Product §14 also fixes the *first
proving set*: "a deep structural question without a forced forecast; a structure–time question
with accountable permitted forward claims when earned; and a historical challenge that actively
seeks misfit."

**Change:** Phase 0's frozen baseline = L3-Q01–Q13 with their strategy-named proofs, plus the
three §14 proving-set cases. Map Lane E's sixteen onto them; any that maps to nothing is either a
real gap in the ratified set (raise as a strategy amendment) or is dropped.

### C4 — B1 is re-elevated, not downgraded. The Clear path deletes the protected snapshot.

Earlier in this session I told the native that "data is disposable" turned the Gochara-deletion
finding into a registry-truth problem rather than a data-loss risk. **That was wrong, and the
governing texts say why.** The rows the Clear route would delete are
`kala_gochara_windows WHERE generation='v1'` — **38,287 rows** — and that is the retired
`ka_gochara_sweep`'s data. Strategy §4: *"`ka_gochara_sweep` remains retired, **snapshot-protected
and never rebuildable**."* The execution brief lists *"ka_gochara_sweep implementation, retained
corpus/snapshot or its non-rebuild protection"* under must-not-touch. F19 preserves "historical
readings, failed forecasts, tests, receipts."

"Disposable" is correct for **rebuildable projections**. It is not correct for three classes the
strategy names: the protected sweep snapshot (a standing ruling), issued claims and observations
(F17, L3-U10: "candidate regeneration does not reset a delivered forecast"), and
`kala_bhavishya`'s retained outcomes (L3-A21). The Clear path hits the first of these.

And it is reachable by an ordinary user: `clear/route.ts:93` sets `allowedScopes = ['per_chart']`
for non-super-admins; the sweep row is `scope='per_chart'`, `layer='kala'`. Any authenticated
chart owner triggering a layer-scoped Clear deletes the one thing the strategy says can never be
rebuilt.

**Change:** B1 returns to BLOCKS-CAMPAIGN, and specifically to *W0 — "make the programme safe"*,
before any other Kāla work. Fix: `ka_gochara.target_table` → `_v2`; `is_active` filter on the
Clear route's registry query; a real guard (trigger or `build_protected_assets` populated) on
`generation='v1'`.

### C5 — Build-cost work must adopt the strategy's benchmark contract, not a thinner one.

The plan said "measure real build cost on the harness." Strategy §5 already specifies the
benchmark contract in detail — hardware, ephemeris/dependency versions, Swiss-lock time, SQL
round-trips, WAL, RSS, cold/warm/resume/horizon-extension/upstream-correction workloads, repeated
matched runs with spread — and names **five distinct cost profiles**: *new chart, unchanged
replay, dependency correction, extended horizon, precise on-demand inquiry.* The plan measured
one. The user experience the native cares about ("build the chart efficiently") spans at least
three: first build, returning user, birth-time refinement.

It also already names the redesign candidates and their equivalence contracts (P0–P6). The plan
framed `ka_kshetra` as "7.5 hours — make it faster." The strategy's framing is stricter and
correct: **P1/P2/P6 with exact equivalence** ("same finite-value policy, float64/rank/ties, full
shift set"), and *"reduced caps cannot pass as equivalent."* Product §1.2: *"Processing speed is
subordinate to depth."*

**Change:** adopt §5's benchmark contract verbatim; measure all five profiles; kshetra work is
P0→P1/P2/P6 with equivalence proofs, never a speed target. Retire the registry's
`estimated_seconds` from every calculation (F28: no detector behind it → null).

### C6 — Serving fidelity is a Pūrṇa-owned interface packet, not L3 work.

Phase 3 proposed that L3 protect its qualification fields in the response-budget contract and fix
the seven hardcoded `dissent: []` sites. Those files are `platform-mcp/src/tools/kala_views/*` —
the managed-MCP door that the Pūrṇa Anveṣaṇa campaign is actively changing. F11 puts serving in
the data-to-answer chain; DP12 owns delivery; Strategy L3-U04/U11 already define the L3→served
packets. Doing this from the L3 side is a collision waiting to happen, exactly as with the
mortality-exclusion gap.

**Change:** Phase 3 becomes an *interface obligation* in L3-U04/U11 form — L3 owns the
served-evidence **sentinel test** (Brief §7: "a sentinel only in a low-ranked, non-default field
reaches the allowed consumer"), Pūrṇa owns the code. L3 never edits `kala_views/`.

### C7 — Reconciling the twelve June briefs is a defined transformation, not a vague task.

Strategy §6.4 states what every asset packet must contain: *"input generations, field-level
transformations, preserve/change/reuse decisions, method qualification, output keys/partitions,
source and data checks, consumer effects, benchmark target, history/rollback contract and an
independent reviewer."* VA §13.3 states what each asset brief supplies. The June briefs (K1–K5
waves against `L3_KALA_CAMPAIGN_PLAN_v0_10`) carry real per-asset thinking — the Sangam brief's
rigor stratum and independence discount are exactly what the strategy asks for — but in a
superseded shape.

**Change:** "reconcile" = extract each June brief's kernel (what the asset is, what it should
become) and re-express it in the §6.4 packet shape against the current W0–W8 waves. Twelve
transformations, one template, one reviewer.

### C8 — `ka_tithi_pravesha` as "first slice, ready now" was over-claimed.

It is the right *path* proof — it builds in 0.61 s, is idempotent, contract-compliant, and its
verification flag is mutation-proven. But the strategy's own row (L3-A09) says: *"Qualify the
implemented Moon-return method against the admitted method before promotion … Current v3 does not
read it."* The writer's own `CLASSICAL_SOURCE_CITATION` reads `not_in_corpus`. Under §7 it
cannot reach `DATA_ACCEPTED` without source qualification, and F23 requires "qualification/source"
proof. Product §3.10 names tithi-praveśa as an admitted instrument, so the qualification is
obtainable — but it is a real step, not a formality.

**Change:** keep it as the path proof (build → receipt → evidence → freeze) and the vehicle for the
5.5-hour timezone fix; do not present it as W2 progress until its method is source-qualified.

---

## 2. What must be added (seven items)

**A1 — W1, physical upstream truth.** Zero generations opened; 79 dangling predicates; the
strategy's §3 closing paragraph names these exact conditions and says *"resolve … before using
that connection for an elevated L3 rebuild."* Not optional, not L3's alone: it needs L2 to
publish.

**A2 — The internal input/output/use matrix** (VA §13.3 item 3; Strategy §4 "two related maps").
Lane E traced five seams; the strategy wants every edge with its F12 operator role. This is the
concrete artifact behind "elevate synergistically as a layer" — without it, seam repair is
anecdotal.

**A3 — Comparability and applicability per method per window.** The native's "LLM reconciles in
context" is compatible with the texts only if the LLM receives F06 state per method and a
comparable-scale flag (L3-Q05, F08 "never average incompatible schools"). Otherwise it will
compare a Tājika score to a daśā score as commensurable. This is the missing half of
"co-reference."

**A4 — User-experience obligations**, which nothing we assembled addresses despite the native's
explicit ask. From Product §9/§10.2 and current measured state:
  - *Availability truth.* Experience 1 is "ask a real question and see what this chart can answer
    now." Today four assets sit in `error`, five tables are empty, and `asset_throughput` disagrees
    with reality. §10.2: *"Availability badges … need detectors for the exact claims they make."*
    The user's first experience of Kāla — knowing what it can answer — is broken at the detector.
  - *Build progress, cancellation, resumption* (§1.2). A first build takes an unknown time (the
    registry says 24 min; reality ≥ 7.5 h) with no honest progress semantics, and a crash leaves a
    partial layer with no indicator.
  - *Identity continuity, chapter → interval* (Experience 4, §3.10 last sentence). Lane E shows
    identity dies at nearly every internal hop. This must be an acceptance test, not a hope.
  - *Ordinary periods.* §9: *"must work for ordinary charts and ordinary periods, not only dramatic
    named yogas."* Every fixture we have is dramatic. Add an ordinary-period case to the baseline.

**A5 — The five cost profiles** (C5).

**A6 — P0 safety confirmation.** Both strategy-named hazards (Kshetra planner mutation; Bhavishya
empty-input deletion) *appear repaired in code* — the outcome-preservation read at
`ka_bhavishya_lekha.py:114-141` now precedes the early return at `:206`, and the Kshetra planning
range shows no mutation. But the strategy requires the *tests* ("zero planning/dry-run mutations;
crash/resume and empty-generation tests"), and no receipt shows they ran. Confirm, don't assume.

**A7 — Write the plan down.** The plan the native approved has no artifact. Everything else here
is versioned; the thing execution would follow is not. §7 of this review is that artifact.

---

## 3. What to drop (six items)

- **D1** Lane E's sixteen questions as an authority (→ mapped into L3-Q01–Q13).
- **D2** The concord/harmonization surface — already dropped by the native; recorded here with the
  textual reason: L3-Q05 requires *"actual changed and unchanged evidence without a forced
  consensus."* It was contrary to the strategy, not merely unwanted.
- **D3** Any single salience/confidence scalar (Product §5.2).
- **D4** The registry's `estimated_seconds` as an input to anything (F28).
- **D5** Any L3 edit to `platform-mcp/src/tools/kala_views/` (Pūrṇa territory).
- **D6** "Data is disposable" as a blanket — retain it for projections; exclude the three protected
  classes (C4).

## 4. What survives unchanged

The temporal contract via `ka_temporal` (DP07; §3.10 "compute boundaries, calendars,
location/time-zone conventions … correctly"). The determinism gate — now defined *relative to a
pinned dependency vector*. The anti-force-fit sweep — rebound to VA §10.2's eight "cast away"
categories as the checklist, with our six findings as instances. Freeze-before-change. Measure
before optimize. The environment fixes (grants, builder timeout, supervisor, registry truth).
`ka_tithi_pravesha` as the path proof. All seven lane deliverables as evidence.

---

## 5. The user's perspective — what a person gets from Kāla today

Walking Product §9 against measured state, for the primary consumer who "may know no Jyotish
terminology":

| Experience | What the definition promises | What the layer delivers today |
|---|---|---|
| 1 · First encounter | "See what this chart can answer now" | Cannot be known: availability signals have no detector behind them (`asset_throughput` ≠ reality; 4 assets in `error`). |
| 4 · Temporal landscape | Chapter → interval "without changing evidential identity" | Identity lost at internal seams; `kalasutra` keeps 2 of 21 columns; provenance survives only inside a citation string. |
| 5 · Choice comparison | Nearest vs stronger under a *named* criterion | `call_priority_ranking` ignores `ka_tulana` entirely; ranking = L2 salience × an orb that is NULL 99.6% of the time. |
| 7 · Truthful forecast review | Frozen claim, fit/misfit, no retrospective repair | Plumbing exists (`_reattach_outcome`); but `kala_bhavishya` has 0 rows for the canonical chart, so nothing to review. |
| §10.2 · Graceful incompleteness | Expose unavailable dependencies without jargon | A "no window" today may be a capped search (`LIMIT 750` = mode filter) presented as an honest empty. |

The point is not that the assets are bad — several are genuinely good. It is that **the person
cannot currently tell the difference between "Kāla has nothing to say" and "Kāla is broken,"**
and that is the first thing the setup must fix, before any asset is elevated. Product §10.2
makes it a binding requirement, not a nicety.

---

## 6. Decisions this review adds for the native

1. **Generations for L3** — adopt the 1035/1036 pattern (head + partitions + publish)? This gates
   W1, the cascade fix, and determinism. Recommend yes; it is the strategy's own design.
2. **Typed confidence, not a scalar** — confirm that "confidence or salience attached" means the
   F04/F06/F12 + Temporal-Testimony binding, and that no single number will stand in for it.
3. **The protected classes** — confirm that "disposable" excludes the sweep snapshot, issued
   claims/observations and retained outcomes.
4. **`ka_tithi_pravesha` source qualification** — who qualifies the Moon-return method against
   the admitted tithi-praveśa method, and from which admitted source?
5. **Baseline authority** — L3-Q01–Q13 + the §14 proving set as the frozen baseline; Lane E's
   sixteen mapped in, not adopted.

---

## 7. The corrected pre-elevation plan (the artifact that was missing)

**Phase 0 — Freeze and measure; change nothing.**
0.1 Freeze L3-Q01–Q13 + the three §14 proving-set cases + one ordinary-period case, with today's
    answers recorded. 0.2 Confirm P0 safety tests actually ran. 0.3 Measure all five cost profiles
    under the §5 benchmark contract on the disposable harness (carrying the seven trigger
    functions). 0.4 Build the internal input/output/use matrix with F12 operator per edge.

**Phase 1 — Make the programme safe (Strategy W0).**
1.1 Close B1: registry `target_table` truth, `is_active` on Clear, real guard on `generation='v1'`.
1.2 Grants on the three `bg_*` tables; explicit timeout on `data_plane_builder`.
1.3 Supervisor fix; disposable-harness spec; session posture.
1.4 Coordinate the cascade with the Nirmāṇa campaign's existing `cascade_check.sql`.

**Phase 2 — Foundations.**
2.1 Adopt L3 generations; bind to published L1/L2 generations (needs W1 from L2).
2.2 Temporal contract via `ka_temporal`: one interval type, explicit boundary convention,
    timezone-explicit instants, no `date.today()`, no naive-into-`timestamptz`.
2.3 Determinism gate relative to the pinned vector.
2.4 Bind every output to F04/F06/F12 + Temporal Testimony; comparability flag per method.

**Phase 3 — Remove force-fitting (VA §10.2's eight categories as checklist).**
Our instances: `LIMIT 750` mode filter; harmonic mean dropping zeros; the stored-not-served
Sangam tier; `max_windows=8`; NULL→default; the two-vocabulary ayanāṃśa seam; first-domain-only
at `ph_nimitta:159`; `confidence_score = ICC/13` sold as confidence.

**Phase 4 — Interface packets, not L3 code.** L3-U04/U11 packets to Pūrṇa for the seven
`dissent: []` sites and budget protection; L3 owns the sentinel test.

**Phase 5 — Reconcile the twelve June briefs** into §6.4 packet shape; author the Kshetra brief.

**Phase 6 — Individual assets**, each inheriting all of the above. Path proof:
`ka_tithi_pravesha` (fix the 5.5 h, source-qualify, freeze). First substantive: per W2.

---

## 8. What this review does not establish

It did not re-run any lane's measurements beyond the eight checks listed in the integrator log
and the seven made for this review (P0 status, v1 snapshot identity, generation heads, dangling
predicates, Clear reachability, plan-artifact absence, tithi source citation). It does not judge
the Jyotish correctness of any asset — that is the elevation's own work. It does not resolve the
five decisions in §6; it names them.

---

# Addendum §9 (v1.1) — what this review did not read, and what that changes

This review was built against the five top-level authorities. It did **not** read the W0 tier
beneath the Strategy — `MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` (status `ACCEPTED`),
`..._W0_FIELD_CONTRACT_REGISTER_v1_0.md`, `..._W0_BENCHMARK_BASELINE_v1_0.md`,
`..._L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md`, `..._L3_EXECUTION_FOCUS_AMENDMENT_v1_0.md`
(DP-SD-019) — nor the execution ledger's L3 rows. The native asked whether the data-plane
elevation strategy had been consulted; the honest answer is "the master plan yes, the tier beneath
it no." Three conclusions change. The body above is left as written.

## 9.1 C1 is reframed: the generation design is not open — it is frozen; the *physical* work is held

C1 said the plan "omits the generation / compatible-dependency substrate" and made adopting it
native decision 1. **The design was frozen and independently accepted at W0** — FOUNDATION_SAFETY §6
(eight numbered design points: content-addressed generations, candidate vs selected heads, atomic
layer manifest, rollback by head re-pointing, Kshetra's fifteen-table stage plan, Bhavishya's
fail-closed rule) and CURRENT_STATE §4.4: *"This is reviewed design, not physical infrastructure."*
What is held is **physical implementation**, on `L3-W1-UPSTREAM-GENERATIONS-01`
(FOUNDATION_SAFETY §8 item 2), which itself waits on the RI-01 precursor release.

The measurements stand (zero generation heads ever opened; 79 dangling predicates). **Decision 1
reframes** from *"adopt the 1035/1036 pattern?"* to *"authorize the physical L3 generation
infrastructure now, per the frozen W0 design, and state what releases the W1 hold."* Asking the
native to re-decide an accepted design is the error; asking them to release a hold is the question.

## 9.2 A2 is narrowed: the DAG/producer-use map and the field register already exist

A2 asked for "the internal input/output/use matrix … every edge with its F12 operator role."
CURRENT_STATE §4.1 already holds the source-derived DAG (81 declared entries, 32 active-L3 edges)
with a producer/use row and W0 disposition per identity, and the field register holds 699 explicit
fields across 39 partitions, each with producer path, grain, key role, null semantics,
qualification code, receiver and falsifying test. **What is genuinely missing is one overlay:** the
F12 operator role on each §4.1 edge. A2 becomes that overlay, not a matrix from scratch — and
DP-SD-019 §6 forbids the latter in terms: *"do not build another tracker, scheduler or blanket
per-field paperwork system."*

## 9.3 A6 is reversed in framing and kept in substance: P0 is accepted; the real-DB rehearsal is not

A6 said both P0 hazards "appear repaired in code; no receipt shows the required tests ran."
**Receipts exist.** FOUNDATION_SAFETY §4.1 (Kshetra `3f109869d`: 27 focused / 133 expanded,
independent ACCEPT) and §4.2 (Bhavishya `a3e518864`: 25 passed plus a disposable two-connection
lock proof, independent ACCEPT); execution ledger 2026-09-15 04:04 / 04:47 / 05:01. The framing
was wrong.

What FOUNDATION_SAFETY itself still lists as not run: *"A populated real Bhavishya/Phala rehearsal
remains not run"* (§4.2) and *"No production rehearsal is inferred"* (§4.1). The accepted proofs ran
against a strict fake connection. A functions-first disposable-PostgreSQL rehearsal of the real
writers is therefore **additive**, not duplicative — and the Phase 0/1 session has already built
exactly that (`tests/l3/_p0_harness.py`, `test_ka_kshetra_p0_planning_readonly.py` with three
independent detectors, `test_bhavishya_p0_empty_generation_db.py`). Its close-out must say
"real-DB rehearsal added to accepted fake-based proof," never "P0 was unproven before us."

## 9.4 Credit the accepted source work this review under-stated

At the **t3 evidence** level, "0/22, no L3 event under the frozen definition" is true and stays
true. At the **source-acceptance** level it was misleading to leave unstated that, on 2026-09-15/16
under DP-SD-017/018/019: W0 passed terminal independent review at `00a161195`; W2 first-frontier
source for eight replacements (Avadhi, Yojaka, Gochara 27-event-class completeness, Tulana typed
fields, Dasha contracts) was accepted at `47131772b`; RI-02 provenance and security were accepted
(`da498ebd9`); Kshetra's DHARA left-limit correction was admitted as generation
`l3:87cc8c9baf89:002a118b218e`; and the DP-SD-019 source release gate went GREEN at `475f5ab5a`.
None of this is deployed, physically built, or campaign-accepted — the ledger is explicit — but it
is accepted, reviewed source, and every asset brief starts from it, not from zero.

## 9.5 Two things that survive unchanged

The W0 benchmark baseline is real but explicitly bounded — *"source-local, no-DB, small fixture,
Moshier fallback; PostgreSQL rows/storage/WAL, full-chart duration … remain future packet
measurements."* Phase 0.3's five-profile measurement is precisely that future packet. Keep it.
And the asset-brief template the native asked for **already exists** as the reusable
`ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT` (bound by DP-SD-017 as blob `71ff974ec…`) plus the
skill's A–J `asset-elevation-contract.md`; `KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md` binds
them for one Kāla asset rather than adding a fifth authority.

