---
artifact: NIKASHA_IMPLEMENTATION_PLAN
canonical_id: NIKASHA_IMPLEMENTATION_PLAN
version: "1.0"
status: IN_PROGRESS — wave 1 folded 2026-09-27 (P3 landed; P4 partly; P9-R85 landed); rulings D1–D6 applied 2026-09-27 (nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md); no native decision pending on any packet; what remains for the native is the review of the R218 planner-test output per P-need (D5 rev. 2.1 — §3.6 withdrawn) (D5) and the three re-seal signatures (D2)
produced_on: 2026-09-26
authored_by: nikasha-test campaign, Phase 6 (K3_256 LOW effort, per native instruction)
register: NIKASHA_CHANGE_REGISTER_v2_0.md (214 rows)
analysis: nikasha_test/PHASE6_ANALYSIS.md
changelog:
  - "1.0 (2026-09-27, NIKASHA-DECISIONS-FREEZE-20260927): rulings applied — P1/P2 → integration-and-acceptance packets (P1 +R217); P3 closure semantics fixed (D4); P4 +R216 first and the D6 spec on R55; P5 dependencies ruled (D2 agenda); P6 rewritten per D4 (25 h); P7 +R215; P8 → consume engine B1/C1, hold B2/R21; P9's D3/D5 pointers → ruled; coverage check and total re-summed (≈ 379 h). Version stays 1.0 (LIVING; in-place)."
  - "1.0 (2026-09-26): first plan, ten packets, awaiting D1–D6."
---

# Nikaṣa — implementation plan v1.0

Ordered packets. Each packet names: the register rows it closes · its **proof** (a detector that
fails until the packet lands) · dependencies · effort (sum of the register rows' `effort_h`;
transcription rows that carry `depends_on` are counted at their registered 0.5–2h where noted) ·
**who decides**. Effort figures are the register's honest hours, summed, not re-estimated.

Ordering rationale (register §2.7 one-liner, confirmed by P6 measurements): instrument the builder
before the from-scratch run, remove the run-killer, port the closure loop, fix the inspector's
detectors, align the documents, unify the ledger namespace, rotate the fingerprint, then the
layer-instance blockers, and the builder's own plan last — because the engine is tuned to a
contract that must first stop moving.

Total: **10 packets, ≈ 379 h** (≈ 157 h in P1–P8 after the 2026-09-27 rulings: 6 + 2 + 20 + 69 + 16 + 25 +
2.5 + 16; ≈ 222 h in P9–P10, dominated by the derivability mappings). Native decisions: 6, **all ruled
2026-09-27** (`nikasha_test/DECISIONS_FOR_THE_NATIVE.md`, reconciled in
`nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md`). No packet waits on a decision; the native's remaining
acts are the review of the R218 planner-test output per P-need (D5 rev. 2.1 — §3.6 withdrawn) (D5) and the three re-seal signatures (D2).

---

## P1 · Integrate and prove the builder instrumentation (engine A1/A2), plus the run-level error residual — per D1 ruling 2026-09-27

- **Closes:** R34 (acceptance of engine A1 `8edba0533` + migration 1094; the legacy `_telemetry` residual is the asset campaign's per engine D-1(b)), R35 (acceptance of engine A2 `f4a6f9541` at asset level) and **R217** (run-level `build_runs.last_error` on `mark_run_state`'s failed paths — the one implementation item left in this packet, engine-owned).
- **Proof (fails until landed):** the two P6 baseline queries (`rows_per_second IS NULL` 268/268; `build_runs` failed with empty `last_error` 288/419 — both re-read live 2026-09-26T20:03Z, unchanged) **plus** representative-path proofs on the deployed engine: one timed writer build per layer, a zero-row completion (rate 0.0, not NULL), a skip after a prior timing (duration untouched, attributed to the earlier attempt), a legacy `ga_*` writer (still NULL until D-1(b) lands — recorded, not hidden); and prospective failure paths: a failed asset, a run failed by exception, a run failed at preflight — each with non-empty `build_runs.last_error` and `build_run_assets.error`.
- **Stages, tracked separately:** implementation (A1/A2 CLOSED_ON_BRANCH; R217 OPEN) → merge of `campaign/nirmana-engine` (no PR exists) → migration 1094 applied (absent in production) → deploy → runtime proof.
- **Dependencies:** the engine branch merged and deployed. Nothing here is re-implemented.
- **Effort:** R217 2 + acceptance 4 = **6 h** (was 7 h of implementation; no net saving is claimed).
- **Who decides:** none pending — D1 ruled 2026-09-27.

## P2 · Accept the run-killer fix (engine A3) — per D1 ruling 2026-09-27

- **Closes:** R36 (acceptance of engine A3 `551d5ecad` — Family A, 2 of the 8 runs). Family B (6 runs dispatched with no manifest) is engine A3b, a separate defect carried on the engine side; the pre-dispatch fault window (engine G-1/G-2) is carried there too.
- **Proof:** harness replay — start a multi-asset run in the sandbox harness, apply a registry change mid-run, assert the run completes, only the diverged asset fails and its dependents block by cascade; then the same replay against the deployed engine. Until deployed: the 09-04 abort signature reproduces in production.
- **Dependencies:** the engine branch merged and deployed (sequenced after P1 so failures during the replay are diagnosable).
- **Effort:** acceptance **2 h** (was 4 h of implementation).
- **Who decides:** none pending — D1 ruled 2026-09-27. The `WriterBase` contract is untouched.

## P3 · Port the closure loop into the production tools (~70 lines, proof exists in sandbox)

- **Wave 1 (2026-09-27): LANDED.** R57/R58/R47/R62/R30 CLOSED (Lane A, A_REVIEW2 ACCEPT_WITH_CORRECTIONS, final `7352ba484`). T3 passes under the production tools (OPEN→CLOSED→RE-OPENED→CLOSED, live, ledger copy). Carry **R222** (G2) must close before the first `--emit-gaps` on the production ledger.

- **Closes:** R57 (closure impossible in stock tooling), R58 (hand-written rows carry no detector binding), R47 (census output path overwrites the production artifact), R62 (sandbox census emits prod-scale floor rows), R30 (tracker reads the census JSON, not only ledgers).
- **What it is:** port the three proven scratch changes — (a) `emit_gaps` closure semantics (append CLOSED when a previously-OPEN deterministic-id row's check now passes; RE-OPENED when a closed check fails again; ~40 lines), (b) last-wins-per-gap_id gap resolution in the tracker (~6 lines), (c) `NIKASHA_CONTROL_DIR` redirection + census `--out` flag — from `nikasha_test/harness/asset_census_closing.py` and `harness/tracker_sandbox.py`; plus detector bindings for hand-written rows (`<control>/detectors/<asset>_<check>.py` convention, proven by `harness/sandbox_control/detectors/bg_nakshatra_medical_D1.py`, which failed before its fix).
- **Closure semantics (per D4 ruling 2026-09-27):** the port is not adopted unchanged — CLOSED only on `PASS` or an explicitly justified `N/A` (never `NOT_GENERIC`, `UNKNOWN`, an errored or unmeasured check); `IN_PROGRESS` transitions on PASS; regression re-opens; a superseded id is never resurrected; hand `change`/`owner`/`gate` carried onto every transition row. Each is an acceptance case with a test before the port lands (the sandbox copy fails four of them today).
- **Proof:** re-run the T3 script (`harness/T3_CLOSURE_LOOP.md` §1–5) against the sandbox using the **ported production tools**, not the scratch copies: a row must flip OPEN→CLOSED→RE-OPENED→CLOSED and the tracker must move 0→1→0→1 on the same asset. Until landed: stock `emit_gaps` skips existing ids (`asset_census.py:576`) and the stock tracker reads state per row (`asset_elevation_tracker.py:200`) — closure is structurally absent.
- **Dependencies:** none. (Enables P6 ledger cleanup and every later certification.)
- **Effort:** R57 4 + R58 8 + R47 2 + R62 2 + R30 4 = **20 h**.
- **Who decides:** native — this is the campaign's headline finding; the change is small and proven, but it changes governance tooling behaviour (D4 ruled 2026-09-27 — the identity, namespace and closure semantics it interacts with are fixed; see P6).

## P4 · Inspector detector fixes (the C1–C4 clusters)

- **Wave 2 W2-2 (2026-09-27): LANDED.** R233, R44, R49, R45, R43, R46, R50, R51, R53, R54, R232 CLOSED; D6 item 2 landed (R55 stays OPEN on migration 1094); the C-KSHETRA correction re-graded ka_kshetra's Idem.pattern to FAIL (found by the fix itself, not planned). W2-3 carries R20, R21, R23, R240, R241, R242.
- **Wave 2 W2-1 (2026-09-27): LANDED.** R222 (precondition MET), R224, R231, R223, R225, R42, R52, R56, R48 CLOSED; W2-2 carries R43–R46, R49–R51, R53, R54, D6 item 2, plus R232/R233; W2-3 carries R20, R21, R23.
- **Wave 1 (2026-09-27): PARTLY LANDED.** R216, R40, R41, R220 CLOSED; D6 classifier landed but R55 stays OPEN until **R225** (G1). Remaining: R20–R23, R42–R56 (the second P4 lane, incl. the attempt adapter D6 item 2 needs), plus carries **R223**, **R224**, **R231**.

- **Closes:** **R216** (rebase the census on engine B1's `17e5a1257` diff — before anything else in this packet; per D1 ruling 2026-09-27), R41 (per-check fault isolation — then everything else ships behind it), R40 (scalable duplicate count + configurable timeout), R42 + R52 + R99 (completion logic: N/A-despite-count_sql, inverted consistency test, empty-by-design third case), R43 (registration: constant indirection, package writers), R44 + R45 + R49 (latest-row selection), R46 (view count_sql), R48 + R56 (silent coverage: every gate emits a row for every asset, N/A-with-reason included; R128 folds in), R50, R51, R53, R54, R55 (per D6 ruling 2026-09-27: `Earn.build_record` / `Cost.baseline` separately specified, instrument feature-detected, timing attributed to the latest attempt at chart scope, graded by cause, a zero-row rate kept as 0.0, the cost baseline a sanctioned measured completion — tested against the engine implementation before adoption; register R55 carries the spec), R60, R20 (follow writer delegation into the seeder — proof exists: sandbox F3 closed 23 Idem rows), R21 (blocking radius), R22 (declared width universes — needs the R06-class registry declaration from P9-D5), R23 (field-level reachability census).
- **Proof:** (a) re-run the T2 hand-verification protocol (`harness/T2_PROTOCOL.md`) on all six layers against production — verdict disagreements must go 60 → 0 (`handverify/T2_SUMMARY.md` baseline); (b) re-run the T1 planted suite against the fixed inspector — the TRUNCATE plant (`build_completion_truncate`) must now FAIL, and all 17 plants still detected with `collateral=[]`; (c) the L3 census completes on production (currently NOT_RUNNABLE, R40/R41); (d) the differential (`harness/differential.py`) finds zero unclassified disagreements and the three known hidden floor breaches (ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510) appear as emitted inspector rows.
- **Dependencies:** R216 first (B1's census diff — the same file, changed on the engine branch); P3 (so the newly-correct verdicts can close rows); R22 additionally depends on P9's R06/R90 declarations (until then width stays NOT_GENERIC — honest, recorded).
- **Effort:** R20 6 + R21 4 + R22 6 + R23 8 + R40 4 + R41 6 + R42 4 + R43 4 + R44 2 + R45 2 + R46 2 + R48 3 + R49 1 + R50 1 + R51 2 + R52 3 + R53 2 + R54 2 + R55 4 + R60 1 + R216 2 = **69 h** (R55 re-priced and R216 added per the 2026-09-27 rulings).
- **Who decides:** executor (inspector is editable per campaign constraint §2.3-class defects; none of these touch the orchestrator). The Earn/Cost verdict-scale question is ruled (D6, 2026-09-27).

## P5 · Documentation alignment (C7 cluster — post-ruling-17 drift)

- **Closes:** R63, R64, R66, R68 (gate-count and verdict-spelling drift across T3/T4/tracker), R69, R70 (L0 self-contradicting figures — restate to 0/360 and current ledger counts, or date-stamp), R65, R67 (Build check-count alignment), R72 (missing T1 review file — locate/restore or correct pointer), R73, R75 (miscounted review/changelog entries), R74 (the ruling-11 clause in T3 §5.1), R76 (review-record naming + glossary line), R77 (five pilot briefs gain the Build row on refresh), R01 (cosmetic P24/P23 order).
- **Proof:** the T5 vocabulary check re-run (`consistency/T5_VOCABULARY.md` findings V1–V17) returns zero disagreements on these surfaces; `grep -c "the eight gates"` over T4 = 0; `grep -n "0/320"` over the L0 instance = 0.
- **Dependencies:** sealed-tier rows land on the D2 reopen agendas — **D2 ruled 2026-09-27** (T1: R01, R72, R76 · T2: R73, R75 · T3: R65-T3, R67, R68-T3, R74; seal order T1 → T2 → T3; a cross-tier re-render pass before each re-seal; the reopens are separate work); tier-4, tracker-comment and L0-instance rows (R63, R64, R66, R69, R70, R77, R65-tracker, R68-T4) need no reopen and proceed first.
- **Effort:** 16 × (0.5–3) = **16 h**.
- **Who decides:** ruled (D2) for the sealed-tier batch; executor for the rest.

## P6 · Ledger identity and crosswalk (C6 cluster) — per D4 ruling 2026-09-27

- **Closes:** R78 (the criterion authority is a declarative criterion registry the census reads — gate, check, applicability, detector binding or `NONE`, revision; ids derived `<asset>-<Gate>.<check>`, scope suffix where chart-scoped), R79 (re-scoped: deterministic lookup on `(asset, scope, registered criterion)`; the four family aliases are one-time crosswalk entries for R81, never a runtime alias table; specific ≠ generic criteria are never merged), R80 (`superseded_by` in the `_schema` line), R81 (re-scoped: a reviewed migration table over all 30 hand gap rows across the five pilots — re-key / split / preserve, hand `change`/`owner`/`gate` carried, old id `superseded_by`; `bg_panchanga-G01` becomes its own criterion `Earn.service_state`, never folded onto a timing id), R15 (hand-written rows carry the census run id they were judged against), R29 (R15's mechanism).
- **Proof:** a ledger scan finds zero `(asset, scope, criterion)` identities with more than one live row; every historical hand id resolves through `superseded_by` to exactly one live row, or is itself live; `Earn.service_state` exists in the registry and its row is not closed by any timing measurement; `emit_gaps` run twice against an unchanged target appends nothing; the ledger stays append-only (no line deleted).
- **Scope:** the migration runs on the current ledger as a proof of the mechanism over preserved test history; the five pilot briefs are regenerated after freeze and are not hand re-keyed — their `G` ids resolve through the crosswalk.
- **Dependencies:** P3 (R80 depends_on R57 — the closure port, with the D4 acceptance cases); D4 ruled.
- **Effort:** registry 4 + lookup 4 + `superseded_by` 2 + reviewed migration 8 + R15 3 + R29 2 + acceptance cases 2 = **25 h** (was 17 h; the review's identity and migration work is priced, not assumed).
- **Who decides:** none pending — D4 ruled 2026-09-27; the criterion registry's location is P6's call.

## P7 · Fingerprint rotation

- **Closes:** R82 (CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: rotate `fingerprint_sha256` to `244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f`, update `last_verified_*`; fix the L0 manifest note's stale "REVISED_PENDING_REVIEW" prose), R83 (drift_detector schema checks: reachable DB or explicit NOT_MEASURED — an unreachable instrument must not masquerade as a finding), **R215** (a campaign checks `CURRENT_STATE` and the sibling worktrees for concurrent campaigns on the same surface at session open; per D1 ruling 2026-09-27).
- **Proof:** `drift_detector.py` exits with 0 HIGH findings (baseline: 1 HIGH, `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.md`); `manifest_fingerprint.py --check` stays MATCH (136 entries).
- **Dependencies:** P5 (rotate after the tier-4 text edits land, so the rotation is not immediately stale).
- **Effort:** 0.5 + 1 + 1 = **2.5 h**.
- **Who decides:** executor (manifest hygiene; no seal involved).

## P8 · Consume engine B1/C1; hold B2/R21's labelling work — per D1 ruling 2026-09-27

- **Closes:** R37 (via engine C1 — consumed, not re-implemented; C1 is not started, and `guardian_cleanup` / `manual reap` have zero source hits here or in madhav-l3, so C1 begins with a search, not an assumption; its 12 h stays on the engine side), R38 (counting surfaces via engine B1 `17e5a1257` — consumed; the labelling surfaces `PlanTimeline`, `/api/cockpit/runs/[id]/assets`, `ArmillaryGraph.stateColor` and three unmapped-default sites stay with engine B2 and R21; migration 1095's backfill must be applied, not simulated, before R38 closes).
- **Proof:** `Build.history` verdicts re-run over the run history attribute every failure to a root cause class with zero unattributed orphan/guardian rows; a planted mid-run kill in the sandbox is reported as one root with N blocked, not N failures; and every labelling surface renders `blocked` — not `error`, not `lit` — for the eight production cascade victims B1 enumerated.
- **Dependencies:** P1 (deployed instrumentation makes the noise classable); R21 (P4) for R38's radius; the engine branch merged and migration 1095 applied. Timed per register §2.7: runs **in parallel with layer elevation, never gating it**.
- **Effort:** **16 h** unchanged (R37's 12 h is C1's, on the engine side; R38's 4 h now covers the labelling surfaces only).
- **Who decides:** none pending — D1 ruled 2026-09-27.

## P9 · Layer-instance blockers (C8 cluster — the derivability mappings)

- **Wave 1 (2026-09-27): R85 LANDED** (Lane B, B_REVIEW5 ACCEPT_WITH_CORRECTIONS, final `ef9c0bf50`): 107/182 SCUs name a producer; closure 63 → 111 of 127. Carries **R226** (`--live`, before compiler.ts wiring), **R227** (B1, awaiting native), **R228**, **R229**. R218 (planner test) and R221 (§0.1 re-scope) remain.

- **Closes (primary rows; the ~100 remaining P4 rows are `depends_on` transcription rows that close with their primary):**
  - **R85** — **re-scoped by D5 rev. 2.1 (native, 2026-09-27):** catalog provenance — name the producing asset(s) for the 170 of 182 catalog units that carry none (`capability_knowledge.snapshot.json` `producer_output_claims`; editorial.ts / compiler.ts), then compute the necessity closure over `asset_registry.depends_on` (today 63 of 127 active assets; all 23 ph/mi outside). The signed P/V × layer matrix is withdrawn: Pariprāśna's planner LLM chooses catalog units per question, so no static table is used. Plus **R218** — the planner P-need test (each of P01–P24 through `plan_retrieval`, PASS when every route's catalog unit has a named producer; 6 h) and **R221** — T3 §0.1 re-scoped to catalog units produced + closure position (2 h; T3 reopen agenda). No T2 §3.6. 12 + 6 + 2 h.
  - **R06 + R10 + R95/R96/R103/R136/R205-class** — multi-producer shared-table expression: a shared table declares its producers; each producer's `count_sql` scopes to its own rows; the layer plan names the counting owner (8 + 4 h + transcription).
  - **R09 + R16** — per-asset carriage-check assignment (C-9, confirmed on all five non-reference layers; 6 + 2 h). Needs **D2** (sealed tier-3 reopen).
  - **R08** — tier-3 §5.2's undefined "§7" and the §2.5/§2.7 order (2 h; D2).
  - **R71** — the [TRANSFERS] contradiction (2 h; **D3 ruled 2026-09-27** — replacement texts for T3 §5.4 test 4 and §2.2 `measured_by` fixed; the same tag at T2 §13.3 items 1/6 and T4 §1.2; lands on the T3 reopen agenda; R94/R119/R140/R185 close with it — four layers, not three).
  - **R14 + R97/R125/R165–R177/R196/R211/R212-class** — service/view/registry-orphan asset shapes in tier 4 (1 h + transcription).
  - **R86** (seed/migration-pin/live three-source DAG reconciliation; 6 h), **R87** (deployed-vs-current-code read; 6 h), **R88** (per-layer switch behaviour in T2 §9.2; 3 h), **R89** (§3.4 presentation rows → carrying layer; 8 h), **R90** (per-layer coverage-obligation ownership; 6 h), **R91** (entity-class emit/accept matrix; 6 h), **R93** (evidence→disposition rule + preserved kernels; 6 h), **R101** (per-layer §0.2 narrative content; 4 h), **R105** (minimum synergy/ablation harness; 16 h), **R106** (consumer-side evidence probes; 8 h), **R109** (registry `produces_contracts`/`consumes_contracts` + declared use; 8 h), **R113** (census emits the reconciled DAG + frozen revision id; 3 h), **R117** (per-rule detector registry; 8 h), **R120** (per-asset role row; 2 h), **R121** (per-asset purpose line; 2 h), **R122** (actual-consumer code census; 6 h), **R124** (per-obligation test templates; 4 h), **R129** (view completeness = parity check; 4 h), **R133** (edge types; 3 h), **R142** (five-state coverage census; 3 h), **R161** (Null gate check; 4 h), **R194** (Narr "emits prose" emission; 2 h), **R213/R214** (1.5 h), **R59** (admit Ashtanga Hridayam to the text class — 1 h; the D1 detector exists and failed before the fix), **R61** (recorded fact, 0.5 h).
- **Proof:** the Phase-4 derivability test re-run — a fresh reader derives each layer-instance skeleton (Parts 0, 1.1, 2.1–2.7, 4.4 inheritance) from tiers 1–4 + census only, and the invention count per layer goes to **0** (baseline: L1 15 · L2 30 · L3 49 · L4 18 · L5 18 = 130, `derivations/L*_INVENTIONS.md`).
- **Dependencies:** P4 (the census must emit the fields these mappings are read through); the D2 reopens (ruled 2026-09-27; agenda in `nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md` D2, seal order T1 → T2 → T3; R131/R210/R214 explicitly deferred to a second round after this packet's derivability re-run); D3 and D5 (ruled).
- **Effort:** primaries ≈ **157 h** + transcription rows (~97 rows × 0.5–2 h ≈ **55 h**) ≈ **212 h**.
- **Who decides:** D2, D3 and D5 ruled 2026-09-27; the native's remaining acts are review of the R218 planner-test output per P-need and the three re-seal signatures (§3.6 withdrawn by D5 rev. 2.1); executor for the census/registry machinery.

## P10 · The builder's own elevation plan — last

- **Closes:** R39 (the builder's own elevation plan, driven by the `Build` gate's nine checks, frozen after the asset contract is frozen; 8 h) — and with it the remaining register sweep: R24 (T4 exercise closed by the post-fix clean re-runs), R26 (already DONE by rule), R31 (tracker SHAPE markers generated from one source with T4 §2; 2 h).
- **Proof:** the builder itself passes the nine `Build` checks it enforces; the freeze criterion (PHASE6_ANALYSIS.md §6.5) evaluates PASS on all five tests in production tooling.
- **Dependencies:** everything above — "seamless" is defined by the asset contract, which must stop moving first (register §2.7).
- **Effort:** **10 h**.
- **Who decides:** native (freeze is a ruling).

---

## Packet/row coverage check

Every OPEN register row appears in exactly one packet: P1 {R34, R35, R217} · P2 {R36} · P3 {R57, R58,
R47, R62, R30} · P4 {R216, R20–R23, R40–R46, R48–R56, R60, R128} · P5 {R01, R63–R70, R72–R77} ·
P6 {R78–R81, R15, R29} · P7 {R82, R83, R215} · P8 {R37, R38} · P9 {R06, R08–R10, R14, R16, R59, R61,
R71, R85–R127, R129–R214} · P10 {R31, R39, R24}. DONE/CLOSED rows (R02–R05, R07, R11–R13, R17–R19,
R25–R27, R32, R33, R84-measured) need no packet. CLOSED_ON_BRANCH rows (R34, R36) stay in their acceptance packets until runtime proof (per D1 ruling 2026-09-27).
