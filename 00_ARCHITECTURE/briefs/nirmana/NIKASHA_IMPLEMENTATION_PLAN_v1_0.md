---
artifact: NIKASHA_IMPLEMENTATION_PLAN
canonical_id: NIKASHA_IMPLEMENTATION_PLAN
version: "1.0"
status: PROPOSED — awaits native rulings listed in nikasha_test/DECISIONS_FOR_THE_NATIVE.md; the plan continues around them
produced_on: 2026-09-26
authored_by: nikasha-test campaign, Phase 6 (K3_256 LOW effort, per native instruction)
register: NIKASHA_CHANGE_REGISTER_v2_0.md (214 rows)
analysis: nikasha_test/PHASE6_ANALYSIS.md
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

Total: **10 packets, ≈ 365 h** (≈ 150 h measured-precision work in P1–P8; ≈ 215 h dominated by the
P9 derivability mappings). Native decisions: 6, collected in
`nikasha_test/DECISIONS_FOR_THE_NATIVE.md` (D1–D6). No packet is blocked by a pending decision;
each names the ruling it needs and proceeds around it.

---

## P1 · Instrument the builder — rate and error text

- **Closes:** R34 (rows_per_second + duration in `asset_throughput`), R35 (error text on every failure).
- **Proof (fails until landed):** `SELECT count(*) FROM asset_throughput WHERE rows_per_second IS NULL` → must fall below 268/268 after one instrumented build; `SELECT count(*) FROM build_runs WHERE state='failed' AND (error text null or empty)` → 0 for every run after the instrumented build. Both queries are the P6 baselines (268/268 NULL; 288/419 silent).
- **Dependencies:** none. Native authorization for R34 already recorded (register §4: "native said yes"); R35 is the same class and is covered by decision D1.
- **Effort:** 4 + 3 = **7 h**.
- **Who decides:** native (orchestrator behaviour edit) — authorized for R34; D1 covers R35.

## P2 · Remove the run-killer

- **Closes:** R36 (a registry change mid-run must not abort every asset in the run — 18 assets, 8 runs; a 10-asset L0 run aborted in full on 2026-09-04; BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md).
- **Proof:** harness replay — start a multi-asset run in the sandbox harness, apply a registry change mid-run, assert the run completes and only the affected asset's rows reflect the change. Until landed: the 09-04 abort signature reproduces.
- **Dependencies:** none (sequenced after P1 only so failures during P2's own testing are diagnosable).
- **Effort:** **4 h**.
- **Who decides:** native (D1 — orchestrator behaviour edit). The `WriterBase` contract is untouched.

## P3 · Port the closure loop into the production tools (~70 lines, proof exists in sandbox)

- **Closes:** R57 (closure impossible in stock tooling), R58 (hand-written rows carry no detector binding), R47 (census output path overwrites the production artifact), R62 (sandbox census emits prod-scale floor rows), R30 (tracker reads the census JSON, not only ledgers).
- **What it is:** port the three proven scratch changes — (a) `emit_gaps` closure semantics (append CLOSED when a previously-OPEN deterministic-id row's check now passes; RE-OPENED when a closed check fails again; ~40 lines), (b) last-wins-per-gap_id gap resolution in the tracker (~6 lines), (c) `NIKASHA_CONTROL_DIR` redirection + census `--out` flag — from `nikasha_test/harness/asset_census_closing.py` and `harness/tracker_sandbox.py`; plus detector bindings for hand-written rows (`<control>/detectors/<asset>_<check>.py` convention, proven by `harness/sandbox_control/detectors/bg_nakshatra_medical_D1.py`, which failed before its fix).
- **Proof:** re-run the T3 script (`harness/T3_CLOSURE_LOOP.md` §1–5) against the sandbox using the **ported production tools**, not the scratch copies: a row must flip OPEN→CLOSED→RE-OPENED→CLOSED and the tracker must move 0→1→0→1 on the same asset. Until landed: stock `emit_gaps` skips existing ids (`asset_census.py:576`) and the stock tracker reads state per row (`asset_elevation_tracker.py:200`) — closure is structurally absent.
- **Dependencies:** none. (Enables P6 ledger cleanup and every later certification.)
- **Effort:** R57 4 + R58 8 + R47 2 + R62 2 + R30 4 = **20 h**.
- **Who decides:** native — this is the campaign's headline finding; the change is small and proven, but it changes governance tooling behaviour (D4 covers the ledger-namespace choice it interacts with).

## P4 · Inspector detector fixes (the C1–C4 clusters)

- **Closes:** R41 (per-check fault isolation — first, everything else ships behind it), R40 (scalable duplicate count + configurable timeout), R42 + R52 + R99 (completion logic: N/A-despite-count_sql, inverted consistency test, empty-by-design third case), R43 (registration: constant indirection, package writers), R44 + R45 + R49 (latest-row selection), R46 (view count_sql), R48 + R56 (silent coverage: every gate emits a row for every asset, N/A-with-reason included; R128 folds in), R50, R51, R53, R54, R55, R60, R20 (follow writer delegation into the seeder — proof exists: sandbox F3 closed 23 Idem rows), R21 (blocking radius), R22 (declared width universes — needs the R06-class registry declaration from P9-D5), R23 (field-level reachability census).
- **Proof:** (a) re-run the T2 hand-verification protocol (`harness/T2_PROTOCOL.md`) on all six layers against production — verdict disagreements must go 60 → 0 (`handverify/T2_SUMMARY.md` baseline); (b) re-run the T1 planted suite against the fixed inspector — the TRUNCATE plant (`build_completion_truncate`) must now FAIL, and all 17 plants still detected with `collateral=[]`; (c) the L3 census completes on production (currently NOT_RUNNABLE, R40/R41); (d) the differential (`harness/differential.py`) finds zero unclassified disagreements and the three known hidden floor breaches (ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510) appear as emitted inspector rows.
- **Dependencies:** P3 (so the newly-correct verdicts can close rows); R22 additionally depends on P9's R06/R90 declarations (until then width stays NOT_GENERIC — honest, recorded).
- **Effort:** R20 6 + R21 4 + R22 6 + R23 8 + R40 4 + R41 6 + R42 4 + R43 4 + R44 2 + R45 2 + R46 2 + R48 3 + R49 1 + R50 1 + R51 2 + R52 3 + R53 2 + R54 2 + R55 2 + R60 1 = **65 h**.
- **Who decides:** executor (inspector is editable per campaign constraint §2.3-class defects; none of these touch the orchestrator). The Earn/Cost verdict-scale question (census FAIL vs tier-4 "not instrumented is legal") is native decision D6.

## P5 · Documentation alignment (C7 cluster — post-ruling-17 drift)

- **Closes:** R63, R64, R66, R68 (gate-count and verdict-spelling drift across T3/T4/tracker), R69, R70 (L0 self-contradicting figures — restate to 0/360 and current ledger counts, or date-stamp), R65, R67 (Build check-count alignment), R72 (missing T1 review file — locate/restore or correct pointer), R73, R75 (miscounted review/changelog entries), R74 (the ruling-11 clause in T3 §5.1), R76 (review-record naming + glossary line), R77 (five pilot briefs gain the Build row on refresh), R01 (cosmetic P24/P23 order).
- **Proof:** the T5 vocabulary check re-run (`consistency/T5_VOCABULARY.md` findings V1–V17) returns zero disagreements on these surfaces; `grep -c "the eight gates"` over T4 = 0; `grep -n "0/320"` over the L0 instance = 0.
- **Dependencies:** sealed-tier rows (R65/R67/R68-T3/R72/R74/R76/R01) require native reopen ruling **D2**; tier-4, tracker-comment and L0-instance rows are editable without it and proceed first.
- **Effort:** 16 × (0.5–3) = **16 h**.
- **Who decides:** native for the sealed-tier batch (D2); executor for the rest.

## P6 · Ledger namespace unification (C6 cluster)

- **Closes:** R78 (one criterion-string authority), R79 (substance-key dedupe with alias resolution in `emit_gaps`), R80 (`superseded_by` in the `_schema` line), R81 (fold the 11 measured hand↔census duplicate pairs — `consistency/T5_LEDGER_DRIFT.md` §A lists them verbatim), R15 (hand-written rows carry the census run id they were judged against), R29 (R15's mechanism).
- **Proof:** a ledger scan finds zero (asset, criterion-family) pairs with more than one live row; folding the 11 pairs leaves the ledger append-only (every fold is a `superseded_by` append, never a delete); `emit_gaps` run twice against an unchanged target appends nothing.
- **Dependencies:** P3 (R80 depends_on R57 — the closure port lands the append-only state machinery the fold rides on); D4 (namespace choice).
- **Effort:** 2 + 4 + 2 + 4 + 3 + 2 = **17 h**.
- **Who decides:** native (D4 — the namespace is a governance-ledger shape decision); execution is mechanical once ruled.

## P7 · Fingerprint rotation

- **Closes:** R82 (CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: rotate `fingerprint_sha256` to `244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f`, update `last_verified_*`; fix the L0 manifest note's stale "REVISED_PENDING_REVIEW" prose), R83 (drift_detector schema checks: reachable DB or explicit NOT_MEASURED — an unreachable instrument must not masquerade as a finding).
- **Proof:** `drift_detector.py` exits with 0 HIGH findings (baseline: 1 HIGH, `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.md`); `manifest_fingerprint.py --check` stays MATCH (136 entries).
- **Dependencies:** P5 (rotate after the tier-4 text edits land, so the rotation is not immediately stale).
- **Effort:** 0.5 + 1 = **1.5 h**.
- **Who decides:** executor (manifest hygiene; no seal involved).

## P8 · Stability and cascade reporting, alongside layer elevation

- **Closes:** R37 (crash/orphan/guardian-reap noise — 49 orphan-watchdog rows visible in the P6 failure population; 12 h), R38 (cascade reporting: a blocked asset is not a failed asset; 4 h).
- **Proof:** `Build.history` verdicts re-run over the 762-run history attribute every failure to a root cause class with zero unattributed orphan/guardian rows; a planted mid-run kill in the sandbox is reported as one root with N blocked, not N failures.
- **Dependencies:** P1 (instrumentation makes the noise classable); R21 (P4) for R38's radius. Timed per register §2.7: runs **in parallel with layer elevation, never gating it**.
- **Effort:** **16 h**.
- **Who decides:** native (D1 — orchestrator behaviour edit).

## P9 · Layer-instance blockers (C8 cluster — the derivability mappings)

- **Closes (primary rows; the ~100 remaining P4 rows are `depends_on` transcription rows that close with their primary):**
  - **R85** — the P-need/V-journey → layer necessity mapping (the universal blocker behind tier-3 §0.1 on all five layers; 12 h). Needs native decision **D5**.
  - **R06 + R10 + R95/R96/R103/R136/R205-class** — multi-producer shared-table expression: a shared table declares its producers; each producer's `count_sql` scopes to its own rows; the layer plan names the counting owner (8 + 4 h + transcription).
  - **R09 + R16** — per-asset carriage-check assignment (C-9, confirmed on all five non-reference layers; 6 + 2 h). Needs **D2** (sealed tier-3 reopen).
  - **R08** — tier-3 §5.2's undefined "§7" and the §2.5/§2.7 order (2 h; D2).
  - **R71** — the [TRANSFERS] contradiction (2 h; native decision **D3**).
  - **R14 + R97/R125/R165–R177/R196/R211/R212-class** — service/view/registry-orphan asset shapes in tier 4 (1 h + transcription).
  - **R86** (seed/migration-pin/live three-source DAG reconciliation; 6 h), **R87** (deployed-vs-current-code read; 6 h), **R88** (per-layer switch behaviour in T2 §9.2; 3 h), **R89** (§3.4 presentation rows → carrying layer; 8 h), **R90** (per-layer coverage-obligation ownership; 6 h), **R91** (entity-class emit/accept matrix; 6 h), **R93** (evidence→disposition rule + preserved kernels; 6 h), **R101** (per-layer §0.2 narrative content; 4 h), **R105** (minimum synergy/ablation harness; 16 h), **R106** (consumer-side evidence probes; 8 h), **R109** (registry `produces_contracts`/`consumes_contracts` + declared use; 8 h), **R113** (census emits the reconciled DAG + frozen revision id; 3 h), **R117** (per-rule detector registry; 8 h), **R120** (per-asset role row; 2 h), **R121** (per-asset purpose line; 2 h), **R122** (actual-consumer code census; 6 h), **R124** (per-obligation test templates; 4 h), **R129** (view completeness = parity check; 4 h), **R133** (edge types; 3 h), **R142** (five-state coverage census; 3 h), **R161** (Null gate check; 4 h), **R194** (Narr "emits prose" emission; 2 h), **R213/R214** (1.5 h), **R59** (admit Ashtanga Hridayam to the text class — 1 h; the D1 detector exists and failed before the fix), **R61** (recorded fact, 0.5 h).
- **Proof:** the Phase-4 derivability test re-run — a fresh reader derives each layer-instance skeleton (Parts 0, 1.1, 2.1–2.7, 4.4 inheritance) from tiers 1–4 + census only, and the invention count per layer goes to **0** (baseline: L1 15 · L2 30 · L3 49 · L4 18 · L5 18 = 130, `derivations/L*_INVENTIONS.md`).
- **Dependencies:** P4 (the census must emit the fields these mappings are read through), P5/D2 (sealed-tier reopens), D3, D5.
- **Effort:** primaries ≈ **157 h** + transcription rows (~97 rows × 0.5–2 h ≈ **55 h**) ≈ **212 h**.
- **Who decides:** native for content rulings (D2, D3, D5 — the mappings are product judgement); executor for the census/registry machinery.

## P10 · The builder's own elevation plan — last

- **Closes:** R39 (the builder's own elevation plan, driven by the `Build` gate's nine checks, frozen after the asset contract is frozen; 8 h) — and with it the remaining register sweep: R24 (T4 exercise closed by the post-fix clean re-runs), R26 (already DONE by rule), R31 (tracker SHAPE markers generated from one source with T4 §2; 2 h).
- **Proof:** the builder itself passes the nine `Build` checks it enforces; the freeze criterion (PHASE6_ANALYSIS.md §6.5) evaluates PASS on all five tests in production tooling.
- **Dependencies:** everything above — "seamless" is defined by the asset contract, which must stop moving first (register §2.7).
- **Effort:** **10 h**.
- **Who decides:** native (freeze is a ruling).

---

## Packet/row coverage check

Every OPEN register row appears in exactly one packet: P1 {R34, R35} · P2 {R36} · P3 {R57, R58,
R47, R62, R30} · P4 {R20–R23, R40–R46, R48–R56, R60, R128} · P5 {R01, R63–R70, R72–R77} ·
P6 {R78–R81, R15, R29} · P7 {R82, R83} · P8 {R37, R38} · P9 {R06, R08–R10, R14, R16, R59, R61,
R71, R85–R127, R129–R214} · P10 {R31, R39, R24}. DONE/CLOSED rows (R02–R05, R07, R11–R13, R17–R19,
R25–R27, R32, R33, R84-measured) need no packet.
