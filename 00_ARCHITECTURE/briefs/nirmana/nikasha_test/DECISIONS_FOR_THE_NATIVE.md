---
artifact: NIKASHA_TEST_DECISIONS_FOR_THE_NATIVE
canonical_id: NIKASHA_TEST_DECISIONS_FOR_THE_NATIVE
version: "1.0"
status: RULED 2026-09-27 — native-delegated reconciliation; D5 revised 2.1 by the native the same day (see DECISIONS_RECOMMENDATIONS_v2_0.md v2.1)
produced_on: 2026-09-26
campaign_id: nikasha-test
ruled_on: 2026-09-27
ruled_by: Claude Fable session NIKASHA-DECISIONS-FREEZE-20260927, under explicit native delegation ("use Fable to reconcile it and freeze it")
rulings_source: DECISIONS_RECOMMENDATIONS_v2_0.md (FINAL; reconciles DECISIONS_RECOMMENDATIONS_v1_0.md with reviews/REVIEW_NIKASHA_DECISIONS_RECOMMENDATIONS_v1_0.md)
changelog:
  - "1.0 (2026-09-27, D5 revised): the native overturned D5 in kind — the planner LLM maps questions to catalog units per query, so no static P/V × layer table is used; D5's appended ruling replaced with the 2.1 text (catalog provenance + DAG closure, computed; P-needs as planner test; §0.1 re-scoped; no §3.6). D1–D4, D6 unchanged."
  - "1.0 (2026-09-27, RULED): status AWAITING_NATIVE → RULED; the adopted ruling appended verbatim under each of D1–D6 from DECISIONS_RECOMMENDATIONS_v2_0.md. The original decision text above each ruling is unchanged, so the recommendation-as-raised and the ruling-as-adopted can be read side by side."
  - "1.0 (2026-09-26): six decisions raised at Phase 6 close, AWAITING_NATIVE."
---

# Decisions for the native — Nikaṣa test campaign, Phase 6

Six decisions only the native can take. Each carries a recommendation and the cost of each option.
Register rows cited are in `NIKASHA_CHANGE_REGISTER_v2_0.md`; evidence paths are under
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/`.

## D1 · Authorize orchestrator behaviour edits for R35, R36, R37, R38

R34 (rate instrumentation) is already authorized (register §4: "native said yes"). R35 (error text
on every failure), R36 (run-killer: a registry change mid-run aborts every asset — 18 assets,
8 runs, including a 10-asset L0 run aborted in full on 2026-09-04), R37 (orphan/guardian noise),
R38 (cascade reporting) are the same class: engine behaviour, never the frozen `WriterBase`
contract.

- **Recommendation: authorize**, sequenced as packets P1 (R34/R35), P2 (R36), P8 (R37/R38, parallel
  with layer elevation, never gating).
- Cost of authorizing: ≈ 26 h of orchestrator work plus regression risk in the runner, mitigated by
  the sandbox harness (the P2 proof replays a mid-run registry change).
- Cost of declining: the from-scratch run has no rate baseline (rows_per_second NULL 268/268 — P6
  measurement), 69% of failed runs are undiagnosable (288/419 silent — P6), and the elevation
  campaign's own runs can be aborted in full by any registry edit landing mid-run (R36 evidence).
  R34's prior authorization is orphaned — a rate with no error text diagnoses nothing.

**Ruling (adopted 2026-09-27, native-delegated reconciliation — DECISIONS_RECOMMENDATIONS_v2_0.md):**

> D1 is not a re-authorization. Engine-behaviour work the native authorized to the Nirmāṇa engine
> campaign (2026-09-26) is neither re-authorized nor re-implemented here. R34–R38 are re-owned by a
> requirement-level crosswalk, and every requirement is tracked at five stages — implementation ·
> merge · migration applied · deployed · runtime proof — none of which is satisfied today (production
> read 2026-09-26T20:03Z: 268/268 NULL rates, 288/419 silent failed runs, migrations 1094 and 1095
> absent).
>
> - **R34** = engine A1 (`8edba0533`, CLOSED_ON_BRANCH: the engine times every registered writer
>   itself; migration 1094) **plus** two open residuals: (i) the legacy `ga_writers/_telemetry.py`
>   path — its 8 `ga_*` call sites still write NULL — owned by the asset campaign per engine ruling
>   D-1(b) (`73385d72f`), recorded on R34; (ii) the applicable-path proof below.
> - **R35** = engine A2 (`f4a6f9541`, CLOSED_ON_BRANCH: every asset-terminating path now writes
>   `build_run_assets.error`) **plus** an open run-level residual, new row **R217**:
>   `build_runs.last_error` is still never written by `mark_run_state` (`runner.py:408–425`) on the
>   failed-assets path (:1450), the exception path (:1456) or the writer-gap path (:1240); only
>   `_terminalize_preflight_failure` (:327) and the TypeScript `terminalizeFailedRun` / watchdog CTEs
>   write it. R217 is engine-owned (`runner.py` is engine surface) and is exactly what the 288/419
>   population measures. A2b (`mark_asset_error` empty-exception) stays carried on the engine side.
> - **R36** = engine A3 (`551d5ecad`, CLOSED_ON_BRANCH: a registry divergence fails only the
>   diverged asset; Family A = 2 of the 8 runs) **plus** P2's acceptance (the harness replay of a
>   mid-run registry change, then the same replay against the deployed engine). Family B (6 runs
>   dispatched with no manifest at all) is engine A3b — a different defect, carried separately; the
>   pre-dispatch fault window (engine G-1/G-2) stays carried.
> - **R37** = engine C1, OPEN, not started. `guardian_cleanup` (310 records) and `manual reap` (77)
>   have zero source hits in this repository or in madhav-l3; C1 does not start by assuming the code
>   is here.
> - **R38** = engine B1 (`17e5a1257`, CLOSED_ON_BRANCH: the failure-counting surfaces are certified;
>   migration 1095's disposition backfill was simulated, not applied) **plus** the labelling surfaces
>   B1 expressly did not certify — `PlanTimeline`, `/api/cockpit/runs/[id]/assets`,
>   `ArmillaryGraph.stateColor` and the three unmapped-default sites — which stay with engine B2 and
>   R21.
>
> P1 and P2 are not withdrawn: they become integration-and-acceptance packets (merge → migration →
> deploy → runtime proof), and P1 additionally carries R217. P8 becomes "consume B1 and C1, and hold
> B2/R21's labelling work". No 27 h saving is claimed: P1+P2's 11 h of implementation is replaced by
> R217 (2 h) plus acceptance (≈ 4 h); P8's 16 h is unchanged except that R38's 4 h is covered for the
> counting surfaces only. Engine D-1(b) and D-2(a) are consumed as already ruled in `73385d72f`, not
> re-decided.
>
> The freeze precondition "instrument the builder before the from-scratch run" is met only when, on
> the deployed engine, representative applicable paths (one timed writer build per layer, a zero-row
> completion, a skip after a prior timing, a legacy `ga_*` writer) and representative failure paths (a
> failed asset, a run failed by exception, a mid-run registry change) each pass their named proof —
> not when one non-NULL rate makes 268/268 fall.
>
> Two governance rows are added. **R215**: a campaign checks `CURRENT_STATE` and the sibling
> worktrees for concurrent campaigns on the same surface at session open. **R216**:
> `platform/scripts/governance/asset_census.py` is changed by B1 (`17e5a1257`, +75 lines) and again
> by P4/P6; P4 rebases on B1's diff before any detector change lands, and B1's census tests stay
> green.

## D2 · Reopen the sealed tiers for the clause-level batch

The documentation-drift cluster (C7) plus the derivability cluster (C8) require edits to sealed
documents: tier 1 (R01, R72, R76), tier 2 (R06, R73, R75, R85, R88–R91, R109, …), tier 3 (R08,
R09, R65, R67, R68, R71, R74, R117, …). Campaign constraint §2.2: the campaign proposes, the native
reopens by ruling.

- **Recommendation: one bundled reopen per document**, with the register's per-row proposed
  replacement text as the agenda, rather than per-row rulings.
- Cost of bundling: one seal-break event per document; a single re-review scope (~40 clauses across
  three tiers); tier versions bump once.
- Cost of per-row rulings: ~30 separate reopen rulings, each re-establishing context; the C7 rows
  are individually trivial (0.5–2 h) and would cost more to rule than to fix.
- Cost of not reopening: BLOCKS_FREEZE row R71 stands (the [TRANSFERS] contradiction — D3), C-9/R09
  keeps every per-asset carriage check unassignable (confirmed on all five non-reference layers),
  and tier-3 §0.1 stays unfillable (D5). Tier 4, the L0 instance, the pilots and the tracker
  comment are editable without any reopen and proceed regardless.

**Ruling (adopted 2026-09-27, native-delegated reconciliation — DECISIONS_RECOMMENDATIONS_v2_0.md):**

> Three bundled reopens are authorized, one per sealed document, each on a **reviewed row-to-clause
> agenda** that names, for every row, the exact clause and — where the register offers alternative
> remedies — the remedy chosen. Listing a row id does not ratify its register text. The agenda:
>
> - **T1** (product definition): R01 (§2 P23/P24 order), R72 (`review_record` pointer), R76 (field
>   rename to `document_reviews` **and** one glossary line — T1 has no glossary section, so the
>   agenda names where the line lands, recommended §16).
> - **T2** (data plane): R06 (multi-producer clause — §7.1 or §13.3, chosen on the agenda), R73 and
>   R75 (frontmatter counts), R85 (D5 rev. 2.1: **withdrawn from the T2 agenda** — necessity is computed from the catalog; no §3.6 is created), R88 (§9.2
>   per-layer switch behaviour), R89 (§3.4 carried-by-layer column), R90 (§5 per-layer obligation
>   enumeration), R91 (per-layer entity classes), R119's T2 half (the [TRANSFERS] tag at §13.3 items 1
>   and 6 and on the §12.2/DP rows where a layer plan reads them), and the §7.1 text halves of
>   R181/R186/R198 (per-layer produced/consumed index with edge type and declared-use column).
>   R109's registry columns are P9 data work, not a reopen.
> - **T3** (layer template): R08 (§5.2's "§7" defined; §2.5/§2.7 order), R09 (§2.7 per-asset carriage
>   table), R10 (§1.1 multi-producer inventory, with R06), R65's T3 half (§5.2/changelog check count —
>   "align on nine" or "record the six-plus-three split", chosen on the agenda), R67, R68's T3 half
>   (:359/:520 spelling), R71 (D3's text at §5.4 test 4 **and** §2.2 `measured_by`; R94/R140/R185 close
>   with it), R74 (§5.1 ruling-11 clause), R93 (§3.2 evidence→disposition rule and preserved kernels),
>   R120 (§4.4 role row; R192/R208 close with it), R201 (§2.3 names the source of declared use),
>   R221 (§0.1 re-scoped to catalog units produced and closure position — D5 rev. 2.1).
> - **Explicitly deferred to a second reopen round**, after P9's derivability re-run makes their remedy
>   text known: R131 (§0.2 external comparison), R210 (default per-obligation detectors), R214 (§0.3
>   migration-pin location). They stay OPEN; no sealed row is silently outside this ruling.
> - **No reopen needed — proceed now:** R63, R64, R69, R70, R77, R65's tracker-comment half, R68's T4
>   half, R119's T4 §1.2 half.
>
> Rules. (1) The agenda is closed once opened: anything discovered mid-edit becomes a new register row
> for the next round. (2) Before each re-seal, a cross-tier re-render pass greps every count, gate name
> and section number the changed clauses touch — across tiers, instances and the tracker — and fixes
> the echoes in the same commit; this is the cause of C7, not one of its rows. (3) Drafting may start
> anywhere (R71's text first), but re-sealing is parent-before-child — **T1, then T2, then T3** —
> because T3's §0.1 and ownership rows cannot be certified derivable while T2's necessity (§3.6) and
> ownership inputs are unsealed. (4) One version bump per document, after its re-render pass and an
> independent review.

## D3 · Resolve the [TRANSFERS] contradiction (R71)

Tier 2 §1/§12.2 mark Presentation parity [TRANSFERS] ("a layer plan does not inherit it as its own
work"); tier 3 §5.4 test 4 requires it of a layer instance ("Presentation parity holds for the
layer's served surface"). P4 hit this on three layers (R94, R119, R140, R185).

- **Recommendation: reword tier-3 §5.4 test 4** to the P4 proposal: "run where the surface exists;
  where the owning plane is not built, record [TRANSFERS]-pending — never a pass, never a block."
- Cost of rewording T3: 2 h (R71) + transcription rows; keeps the transfer discipline intact; layer
  instances stop being asked to accept work they cannot execute.
- Cost of un-marking T2 §12.2 instead: every data-plane layer plan inherits a presentation-parity
  obligation against planes (retrieval, conversation) that are not built — an acceptance test that
  can only fail or be faked, i.e. an invented number in verdict form.

**Ruling (adopted 2026-09-27, native-delegated reconciliation — DECISIONS_RECOMMENDATIONS_v2_0.md):**

> The contradiction is real (T2 §1 :83–85 and §12.2 :614/:621 versus T3 §5.4 test 4 :628 and §2.2
> `measured_by` :278) and it hit **four** layers (R94 L1, R119 L2, R140 L3, R185 L4). It is resolved by
> separating what the data layer owns from what it does not:
>
> - **The data layer must prove retention and hand-off of its assigned presentation fields.** T2 §3.4
>   makes this a data obligation, and it stays binding: every §3.4 field the layer owns is present in
>   its produced contracts, by contract test. "Never a block" never excuses a missing field.
> - **End-to-end Presentation parity and Delivery sentinel remain owned by the receiving plane**
>   ([TRANSFERS], T2 §12.2). Where that owner or its test is not built, the instance records
>   `[TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>` — no pass, and no block
>   on the instance for the transferred part alone. This does not discharge product acceptance. Where
>   the owner can run the test, its result is linked, never inherited as the layer's own acceptance:
>   the existence of a built plane is not an ownership assignment.
>
> Replacement texts, both on the T3 reopen agenda (D2):
>
> T3 §5.4 test 4 → "4. **Presentation fields carried.** Every §3.4 field this layer owns (§2.2) is
> present in its produced contracts — a contract test, run here. End-to-end Presentation parity and
> Delivery sentinel are [TRANSFERS] (Data plane §12.2): where their owner or its test is not built,
> record `[TRANSFERS]-pending` with the obligation, owner and dependency — never a pass, never a block
> on this instance for the transferred part alone, never an invented verdict; where the owner runs it,
> link the result."
>
> T3 §2.2 `measured_by:` → "producer-field carriage test — each §3.4 field this layer owns is present in
> its produced contracts; the presentation-parity test itself (Data plane §12.2) is [TRANSFERS] and is
> linked when its owner runs it, never run as this layer's own acceptance".
>
> The same tag is applied at every inheritance point R119 names (T2 §13.3 items 1 and 6; T4 §1.2), so
> the class is fixed, not one row. R94, R119, R140 and R185 close with R71.

## D4 · Choose the ledger namespace (R78–R81)

Eleven measured hand↔census duplicate pairs (`consistency/T5_LEDGER_DRIFT.md` §A) coexist because
the ledger carries two row idioms and `emit_gaps` dedupes by id only.

- **Recommendation: option (a) — hand-style ids as the single namespace**, census becomes a
  detector reference attaching measurements by substance key (asset, criterion-family with alias
  resolution); fold the 11 pairs with `superseded_by`, ledger stays append-only. This is the T5
  proposal verbatim.
- Cost of (a): the census loses its self-contained emission idiom; the alias table
  (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`, `Carr.D1|D2|D3`≡
  `Carr.detector`, `Completeness.*`≡`Complete.*`) must be maintained (R79, 4 h).
- Cost of (b) census namespace only: the hand rows' richer `change`/detector text is lost or
  re-transcribed; first-registration of judgement rows (opportunities) has no home (R26 already
  rules the census never emits them).
- Cost of (c) keep both with cross-references: cheapest today, but the duplicate pairs recur on
  every layer — the 11 pairs become ~60 at six layers — and "which row do I close" stays ambiguous.

**Ruling (adopted 2026-09-27, native-delegated reconciliation — DECISIONS_RECOMMENDATIONS_v2_0.md):**

> **Obligation identity comes first; the id is derived from it.** A gap row is identified by
> `(asset, scope, criterion)`, where `criterion` is an entry in a **declarative criterion registry**
> the census reads (new — today criteria are strings built inline in `asset_census.py:484–560`). Each
> entry carries: gate, check, applicability rule, detector binding or `NONE`, and a revision. The gap
> id is derived — `<asset>-<Gate>.<check>`, the census's existing form, with a scope suffix where
> chart-scoped. Hand-written gap rows use a registered criterion; if the gap has none, the author
> registers one line first. A registered criterion with `detector: NONE` yields `NO_DETECTOR` rows on
> every run — the census's existing `Carr.detector` practice and tier 4's "a gap, never a pass" — which
> is the visible "detector wanted" state. A specific proof is a distinct criterion from its generic
> placeholder (`Carr.D1` ≠ `Carr.detector`; `Completeness.depth.dasha_link` ≠ `Complete.depth`;
> `Earn.service_state` ≠ `Earn.build_record`) and is never merged by family alias.
>
> **History is preserved by an append-only crosswalk, not a blind fold.** `superseded_by` is added to
> the `_schema` (R80). The 30 hand gap rows across the five pilots (ontology 10, rules 8, ephemeris 6,
> panchanga 4, sarvatobhadra 2) are migrated by a reviewed table (R81, re-scoped): each row is
> re-keyed to a registered criterion (its `change`/`owner`/`gate` text carried onto the new row; the
> old id gets `superseded_by`), split, or preserved with a newly registered criterion. T5's group 8 is
> a partial overlap: `bg_panchanga-G01` becomes its own criterion `Earn.service_state` and is never
> folded onto a timing id. The four family aliases (`Vocab.rule1.alias`→`Vocab.alias`,
> `Dens.density_contract`→`Dens.served`, `Carr.D1|D2|D3`→`Carr.detector`, `Completeness.*`→
> `Complete.*`) are crosswalk entries used once in the migration, not a runtime alias table — R79 is
> re-scoped, not withdrawn. Opportunity rows (`-O<n>`) and layer-scope rows (`_layer_all-BT<nn>`) keep
> their hand idioms.
>
> **The census appends measured transitions by deterministic lookup, under closure semantics proven
> before the port lands** (R57 amended): CLOSED only on `PASS` or an explicitly justified `N/A`, never
> on `NOT_GENERIC`, `UNKNOWN`, an errored check or an unmeasured criterion; an `IN_PROGRESS` row
> transitions on `PASS`; a closed row re-opens on regression; a superseded id is never resurrected;
> hand `change`/`owner`/`gate` are carried onto every transition row, never replaced by census
> defaults. The sandbox port (`harness/asset_census_closing.py:649–679`) is not adopted unchanged — it
> fails four of these today. The tracker resolves latest state per identity.
>
> **Scope.** The migration runs on the current ledger as a proof of the mechanism over preserved test
> history; the five pilot briefs are regenerated after freeze (register frontmatter) and are not
> re-keyed by hand — their `G` ids resolve through the crosswalk. Cost: P6's 17 h stands as the floor,
> plus the reviewed migration table (≈ 4 h) and R57's acceptance cases (≈ 4 h).

## D5 · Who authors the P-need/V-journey → layer necessity mapping (R85)

The campaign's largest finding: no tier maps P01–P24 / V01–V13 to layers by *necessity*, so tier-3
§0.1 is unfillable on every layer and 130 P4 invention rows trace here. The mapping is product
judgement — which needs genuinely cannot be answered without a layer — not measurement.

- **Recommendation: the native authors the necessity column** (a per-layer "necessary for P/V"
  table in tier 2 §3.1 or §13.3), with the campaign supplying the mechanical join evidence
  (DP-contract ↔ P/V mapping already present in tier 2); layer instances then narrow, never invent.
  Estimated native effort: a focused review pass over 24 + 13 rows; the register prices the
  documentation mechanics at 12 h (R85) plus transcription.
- Cost of native-authored: native time; the mapping becomes a sealed decision, so changing it later
  is a reopen.
- Cost of machine-derived (data-driven from the DP-contract graph): reproducible, but "necessary"
  is stronger than "reachable through the DAG" — the campaign's own derivation attempts produced
  involvement lists, not necessity sets (that is exactly what the 130 rows record). A derived table
  would still need a native sign-off to be honest.
- Also bound here: whether tier-3 §0.1's "necessary — not involved in, not contributes to" semantics
  stand (recommended: they stand; they are what makes §0.1 falsifiable) or relax to involvement.

**Ruling (revised 2.1 by the native, 2026-09-27 — DECISIONS_RECOMMENDATIONS_v2_0.md v2.1; supersedes the 2.0 ruling):**

> **Necessity is a property of the catalog, not of questions — and it propagates upstream through the
> build DAG.** (Native revision 2.1, 2026-09-27, superseding the 2.0 text below-the-line.) Pariprāśna
> answers a question by a planner LLM searching the semantic capability catalog
> (`platform/src/generated/capability_knowledge.snapshot.json`, 182 SCUs; `planner_projection.ts`) and
> choosing retrieval tools per query; a synthesis LLM then answers. No static question→layer or
> question→asset mapping exists or can: which information a question needs is decided per question, by
> the planner. A signed P/V × layer matrix therefore measures nothing the system uses, and is withdrawn.
>
> What replaces it, in four parts:
>
> 1. **Catalog completeness.** Everything an asset produces that the planner could need must appear in
>    the catalog — the asset template's completeness (§1.1) and reachability (§1.2) measurements,
>    unchanged.
> 2. **Catalog provenance.** Every catalog unit names the asset(s) that produce or part-produce it
>    (`producer_output_claims`). Today **12 of 182** units do, naming 15 assets. R85 becomes this job.
> 3. **Necessity, computed.** An asset is necessary if it produces or part-produces any catalog unit,
>    **or** lies upstream in the build DAG (`asset_registry.depends_on` — the DAG the orchestrator walks;
>    `build_dependencies` is a dead pre-rename table, R219) of any asset that does: the transitive
>    closure from the catalog's producer claims. Under completeness there is no "sole producer" test —
>    two full producers of one unit is a §9 consolidation opportunity, never a necessity failure.
>    Measured 2026-09-27 on today's catalog: **63 of 127 active assets necessary, 64 not reachable** —
>    all 23 Phala/Mīmāṃsā, 21 L0, 9 L3, 6 L1, 4 L2. An asset outside the closure is first a
>    catalog-provenance finding (part 2); only once every unit names its producers is it a merge/retire
>    candidate.
> 4. **The P-needs are the test, not the map.** Each of P01–P24 is run through `plan_retrieval`; the
>    test passes when the plan resolves to capabilities whose catalog units carry named producers
>    (R218). The native's judgement is exercised where it genuinely lives — the P-needs themselves
>    (T1 §2, already the native's) and acceptance of each planner plan — not on 220 cells.
>
> Tier-3 §0.1 is re-scoped on the T3 reopen agenda (R221): from "P-needs and V-journeys this layer is
> necessary for" to "the catalog units this layer's assets produce or part-produce, and the layer's
> place in the necessity closure" — a derived section, filled from parts 2–3, never judged. The clause
> whose unanswerability produced the 130 invention rows is retired with its cause. **No T2 §3.6 is
> created.** Layer instances inherit the computed closure and narrow, never invent.

## D6 · Align the Earn/Cost verdict scale with tier 4 (surfaces at R55)

Tier 4 §1 records "not instrumented" as a legal value; the census scores `rows_per_second` NULL as
FAIL on every asset (all 19 L1 assets FAIL — `derivations/L1_INVENTIONS.md` observations). Until
R34 lands there is no rate anywhere, so both Earn.build_record and Cost.baseline are constant-FAIL
and carry no signal (R55: they are one detector reading one column).

- **Recommendation: amend the census** — NULL rate reads PARTIAL ("not instrumented — R34 pending")
  rather than FAIL until R34 lands, then FAIL means what it says; and collapse Earn.build_record /
  Cost.baseline into one emitted row citing both gate names, since they cannot disagree (T1-FN4).
- Cost of census-side fix: ~2 h inside packet P4; verdicts become honest during the
  pre-instrumentation window.
- Cost of tier-4-side fix instead (declare NULL a failure by design): every asset of every layer
  carries two FAIL rows until the builder is instrumented — ledger noise that trains operators to
  ignore the gate.
- Cost of neither: after R34 lands the ambiguity resolves itself, but every ledger row emitted
  before then carries a FAIL that means "not yet instrumented", permanently ambiguous in the
  append-only record.

**Ruling (adopted 2026-09-27, native-delegated reconciliation — DECISIONS_RECOMMENDATIONS_v2_0.md):**

> **R55 stays OPEN as a detector-design row; the two measurements are separated, not collapsed, and
> neither certifies the whole Earn gate.** `Cost` is not one of the nine gates — `Cost.baseline`
> measures tier 4 §1's build-cost baseline; `Earn.build_record` is one Earn measurement among the
> asset's status/grade claims and never discharges `Earn.service_state` or any other earned-signal
> obligation.
>
> The census (in P4, after R216's rebase on B1's census diff, together with R44/R45/R49):
>
> 1. **Feature-detects the instrument.** `asset_throughput.duration_seconds` absent (migration 1094
>    not applied — true in production today) → both measurements read `NO_DETECTOR — instrument
>    absent (migration 1094)`, scoped to the run; a failed query → `NO_DETECTOR — instrument
>    unreachable`. Neither is `PARTIAL`: nothing was partly measured.
> 2. **Attributes timing to an attempt.** Measurement identity is `(asset, chart scope, latest
>    build_run_assets attempt)`. A duration counts for a build only if its completion write is that
>    attempt's; `last_built_at` alone proves nothing, because skip (`asset_runner.py:985`), probe-green
>    (:1053), error (:587) and start (:1555) all refresh it without touching duration. The census stops
>    taking an unordered last row per asset (:318–323).
> 3. **Grades `Earn.build_record` by cause**, for the latest attempt: a completion write (`lit`,
>    `dormant` or `incomplete`, per migration 1094) with a finite duration → `PASS` — a zero-row
>    completion has a duration and a rate of 0.0, a measured value, never suppressed; healthy
>    non-execution (`skip_no_delta`, probe-green) or a legacy health-probe service with no registered
>    writer → `N/A` with the reason; a completion write reached with no duration → `FAIL` (the legacy
>    `_telemetry` path — R34's residual); an attempt that failed, was orphan-reaped or watchdog-aborted
>    before any completion write → `N/A — failed before completion; see Build.history` (the build
>    failure is Build.history's finding, not a timing defect); a NULL of unknown cause →
>    `NO_DETECTOR — unclassified NULL`, never `PASS`.
> 4. **Grades `Cost.baseline` against a sanctioned baseline.** The baseline is the most recent
>    *measured* completion for the asset at that scope, with provenance (attempt id, age); a healthy
>    skip neither erases a prior baseline nor creates one. With the instrument present and no
>    measured completion on record → `FAIL — no sanctioned baseline build`; the from-scratch run
>    establishes one for every asset.
> 5. **Is tested before adoption** against the engine implementation (`asset_runner.py` at
>    `8edba0533`+, migration 1094): failure, zero rows, skip after a prior timing, probe-green, the
>    legacy `ga_*` path, the absent column, an unknown NULL. It lands when those tests pass — not
>    "before merge" by decree — so the first instrumented build is graded by a tested classifier
>    whenever that build happens.

---

*Decisions D1–D3 gate BLOCKS_FREEZE rows (R71 directly; D1/D2 transitively). D4–D6 gate DEGRADES
and BLOCKS_LAYER work. Per the campaign brief §5 Phase 6.4, no packet waits on these: the plan
continues around each, and the packet that needs a ruling names it.*

*All six ruled 2026-09-27. What remains for the native personally: the review of the R218 planner-test output per P-need (D5 rev. 2.1 — §3.6 withdrawn)
(D5) and the three re-seal signatures (D2). The register and plan carry the mechanical consequences,
each changed row marked "per D<n> ruling 2026-09-27".*
