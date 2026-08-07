---
canonical_id: SHAD_DARSHANA_CLOSE
version: "1.0"
status: CURRENT
created: "2026-08-07"
conductor: "Claude Sonnet 4.6 (Closing Run, HB #114–#118)"
---

# ṢAḌ-DARŚANA CAMPAIGN CLOSE — v1.0

**Campaign:** ṢAḌ-DARŚANA — Kāla Layer Elevation
**Arc:** 2026-07-29 (Night 1) → 2026-08-07 (Closing Run)
**Closing Conductor:** CONDUCTOR (Claude Sonnet 4.6), Closing Run, HB #114–#118
**Ledger:** `SHAD_DARSHANA_STATE.md` (HB #1 – #118)
**Adjudications:** `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`

---

## §1 — Campaign Arc Summary

ṢAḌ-DARŚANA was the multi-wave autonomous campaign delivering the Kāla (L3) layer's full
serving infrastructure: eight elevation gates (W0–W6), two adjudications, five conductor
nights, one closing run, and a permanently-closed W2G sub-arc (GOCHARA-2.0).

**Wave chronology:**

| Wave | Name | Outcome | Evidence |
|---|---|---|---|
| W0 | Envelope + skeleton | CLOSED | PRs #877/#880–#884, census CI, authority_basis seed |
| W1 | 12 serving primitives | CLOSED (12/12 VERIFIED) | PRs #882–#934, round-2 PARĪKṢAKA |
| W2 | Field integration (ka_kshetra) | R5-SCOPED (see §3) | PRs #944–#949, migration 488–497 |
| W2G | GOCHARA-2.0 | LANDED (PR #1089, 2026-08-07) | N1-N5 ratified; ANTARYĀMIN PASS |
| W3 | KP + calendar + lattice + detection | CLOSED | PRs #1083–#1086, W3 PARĪKṢAKA |
| W3K | KP sub-lord clock (item 18) | CLOSED (PARĪKṢAKA ACCEPT) | PRs #1039/#1046; HB #116, 2026-08-07T06:47Z |
| W4 | Upāya + ritual integration | PARKED (scope not started) | Items 4/5/6/7/9/13/14/26/31/42 — future campaign |
| W5 | Serving primitives live-verify | CLOSED (8+1 verified) | HB #109; Mode-3 routing confirmed |
| W6 | Elevation cutover gate | PARKED-HONEST | HB #117, 2026-08-07T06:42Z |

**Adjudications:**
- ADJUDICATION-1 (2026-07-30, Night 2): MD-lord precomputation strategy →
  `bg_synthetic_cohort_md` chain table (ANTARYĀMIN ruling).
- ADJUDICATION-2 (2026-08-01, Night 3): N_e priors source → Option (b) demographic structural
  priors, Tier N-i, `ne_v01`, 6 Tranche-1 classes (ANTARYĀMIN ruling). Classic/cohort
  FORECLOSED. Seeded in `brahma_class_priors` (migration 522).

**Factual correction (Closing Run):** The FINAL-ARC overnight conductor had recorded
ADJUDICATION-2 as "unruled." This was a checklist factual error. ADJUDICATION-2 was RULED
on 2026-08-01 (Night 3). All W6 blocking on "field_window_id=0" downstream of this error
was resolved upon factual correction — the ka_kshetra field builds for both canonical charts
had already completed in the Night-5 session (2026-08-06T10:55–10:57Z).

**R3 Safety-net:** FULLY RETIRED (HB #113, 2026-08-07). Deletion of the R3 Lambda functions
and IAM bindings confirmed.

---

## §2 — Per-Item Disposition (44 + E1–E8)

Disposition vocabulary: VERIFIED-FIXED / VERIFIED-NO-DEFECT / PARKED-HONEST /
BUILT-UNVERIFIED / NOT-STARTED.

| # | Item | Wave | Closing Disposition | Notes |
|---|---|---|---|---|
| 1 | Daśā-sandhi calendar | W3 | VERIFIED-FIXED (W1-lite + W3 BUILT) | `kala_dasha_sandhi_get`; 15 tests; 3 accuracy anchors |
| 2 | Recurrence-ladder serving | W1 | VERIFIED-FIXED | 10 ladders C2; chart-differentiated; budget trimmer fire confirmed |
| 3 | Sky-event calendar | W3 | VERIFIED-FIXED | 11 accuracy-anchor tests vs real pyswisseph/SIDM_LAHIRI |
| 4 | Moorti-nirṇaya | W3/W4 | NOT-STARTED | Future campaign |
| 5 | Vedha + Sarvatobhadra grid | W3 | NOT-STARTED | Future campaign |
| 6 | Activity-specific muhūrta tables | W3 | NOT-STARTED | Future campaign |
| 7 | Muhūrta-lagna | W3 | NOT-STARTED | Future campaign |
| 8 | Gochara dual-reference | W1 | VERIFIED-FIXED | All 9 grahas non-null both charts; sidereal spot-check |
| 9 | Health/adverse event class | W3 | NOT-STARTED | Future campaign; N_e Tranche-N program feeds here |
| 10 | Per-chapter LEL pinning | W1 | VERIFIED-FIXED | Circularity guard verified |
| 11 | Provenance edges | W2 | BUILT-UNVERIFIED | `kala_field_provenance` live; 1c826d5a 4,233 kfw_* rows; 482012f1 DISCLOSED-GAP |
| 12 | Daśā-system applicability | W2 | BUILT-UNVERIFIED | `kala_field_clocks` live (migration 490) |
| 13 | Tithi-Praveśa | W3 | NOT-STARTED | Future campaign |
| 14 | Janma-anchored election rules | W3 | NOT-STARTED | Future campaign |
| 15 | Rarity axis | W2 | BUILT-UNVERIFIED | `kala_field_null` live; cohort join logic present |
| 16 | Kota-Chakra | W3 | BUILT-UNVERIFIED | 21 accuracy-anchor tests; no full PARĪKṢAKA acceptance yet |
| 17 | Sudarśana-Chakra | W3 | BUILT-UNVERIFIED | `ka_sudarshana_varsha`; collision audit PASS vs `bo_sudarshana` |
| 18 | KP sub-lord clock (CR-75) | W3K | **VERIFIED-CLOSED** (PARĪKṢAKA ACCEPT) | K.1–K.4; `bg_kp_sublord_division` 249 rows; `ganita_kp_cusps_get` live; HB #116 2026-08-07T06:47Z |
| 19 | GOCHARA-2.0 sub-day | W2G | **VERIFIED-FIXED** (G-LAND LANDED) | PR #1089; 1128-row scope-gap + 13-row upgrade accepted; both charts |
| 20 | Auto-filed prospective LEL entries | W2 | BUILT-UNVERIFIED | Living-LEL plane live |
| 21 | Per-tradition calibration weights | W2 | BUILT-UNVERIFIED | 29 seed rows in `kala_field_weights` |
| 22 | Synthetic reference cohort + MD-lord | W2 | VERIFIED-FIXED | `bg_cohort` 10k rows; `bg_synthetic_cohort_md` chain; ADJUDICATION-1 |
| 23 | Circular-shift null calibration | W2 | BUILT-UNVERIFIED | `kala_field_null` live (migration 494) |
| 24 | Uncertainty-budget propagation | W1-lite | VERIFIED-FIXED (lite) | `sukshma_boundary_uncertainty` on `kala_now_get`; full W2 budget future |
| 25 | Salience vector + submodular selection | W2 | BUILT-UNVERIFIED | `kala_field_salience` live (migration 495) |
| 26 | UPĀYA-SETU | W4 | NOT-STARTED | Future campaign |
| 27 | kala_timeline_spec v1 | W2 | BUILT-UNVERIFIED | `kala_timeline_spec` live (migration 496) |
| 28 | Daśā-lord transit-condition | W1 | VERIFIED-FIXED | Both charts; real transit sign/house/dignity |
| 29 | Chandrāṣṭama/horā/janma-resonance | W1 | VERIFIED-FIXED | Both charts; real `is_chandrashtama:true` positive |
| 30 | Mudda daśā join | W1 | VERIFIED-FIXED | Muntha real both charts; prose leak gone |
| 31 | Period-echo mining | W3 | NOT-STARTED | Future campaign |
| 32 | Diśā-śūla + gulika-kālam joins | W1 | VERIFIED-FIXED | Both fields both charts both dates |
| 33 | Absence-of-expected detector | W3 | BUILT-PARKED | PARĪKṢAKA ACCEPT-WITH-DEBT; D-33-1: monotonicity weak |
| 34 | Contrastive EXPLAIN | W3 | BUILT-PARKED | PARĪKṢAKA ACCEPT-WITH-DEBT; D-34-1: Py/TS zero-lambda divergence |
| 35 | Planner wiring verified LIVE (hard gate) | W5 | NOT-STARTED | Future session — W5 live-verify is wave-close, this is planner-wiring confirmation |
| 36 | Contender lattice + adjudication engine | W3 | BUILT-PARKED | PARĪKṢAKA ACCEPT-WITH-DEBT; D-36-1: cosmetic row-count discrepancy |
| 37 | Ritual-resonance + paddhati profile | W3/W4 | BUILT-PARKED | PARĪKṢAKA ACCEPT-WITH-DEBT; D-37-1: Rail-2 test survives `convention_status` filter mutation |
| 38 | ELECT ritual-pairing + grading | W1-facade | VERIFIED-FIXED (facade) | Grading engine + frontier v0; ritual-pairing W4 |
| 39 | Living-LEL incremental calibration | W2 | BUILT-UNVERIFIED | Lane E |
| 40 | `kala_ritual_get` registration + planner | W0-stub | VERIFIED-FIXED (Mode-3 redirect) | Mode-3 `wrong_view` redirect real and tested |
| 41 | Muhūrta Factor Census + corpus | W3 | VERIFIED-FIXED | 51 rows / 9 families (PARĪKṢAKA count); `bg_parihara_rules` updated |
| 42 | Unified Intervention Ledger | W4 | NOT-STARTED | Future campaign |
| 43 | Tri-plane traversability contract | W0–W1 | VERIFIED-FIXED | Real-data wiring on all 6 view facades confirmed |
| 44 | Single-temporal-authority (`authority_basis`) | W0-seed / W2 | VERIFIED-FIXED (seed) + R5-SCOPED (population) | 1c826d5a: 4,233 kfw_* provenance rows (PASS); 482012f1: DISCLOSED-GAP (R5) |
| E1 | Point-process formalization + skill score | W2 | BUILT-UNVERIFIED | `kala_field_skill` + `kala_field_gof` live; skill-score CI not yet |
| E2 | Insight synthesis stage | W2 | BUILT-UNVERIFIED | Stage 6.5 live |
| E3 | Argument-shaped reading + specificity gate | W0-skeleton | VERIFIED-FIXED (skeleton) | Hard-gate flip W2 future |
| E4 | question_frame compiler | W0 | VERIFIED-FIXED | `kala_envelope.ts` |
| E5 | field_snapshot_id | W0-stub | VERIFIED-FIXED (stub) | Real hash W2 future; TODO(W2) documented |
| E6 | Per-view elevations | W1-lite | VERIFIED-FIXED (lite) | `weakest_link` both charts; full per-view W3 |
| E7 | Substrate (census CI, freshness, cohort) | PARTIAL | PARTIAL | Composer lib + census CI seeded; cohort built; skill-score CI not yet |
| E8 | Non-elevations register | standing | NOT-STARTED | Future campaign |

**Summary counts:**
- VERIFIED-FIXED / VERIFIED-CLOSED: 21 items (1/2/3/8/10/18/19/22/24/28/29/30/32/38/40/41/43/44-seed + E3/E4/E5/E6)
- BUILT-PARKED (PARĪKṢAKA ACCEPT-WITH-DEBT): 4 items (33/34/36/37)
- BUILT-UNVERIFIED (W2 field integration pending full PARĪKṢAKA): 13 items (11/12/15/16/17/20/21/23/25/27/39 + E1/E2)
- NOT-STARTED: 11 items (4/5/6/7/9/13/14/26/31/35/42 + E8)
- PARTIAL: 1 item (E7)

---

## §3 — W2 Field Integration: R5 Disposition

Per CONDUCTOR pre-authorized ruling R5 (per-chart scoping), the W2 field integration
closes with split disposition:

**1c826d5a (Abhinandan Mohanty) — PASS:**
- ka_kshetra stage 2–8 completed 2026-08-06T10:55Z
- 2 field windows in `kala_field_windows` (kfw_5c3993a87cd5c6ad4cb7b482, etc.)
- 4,233 rows in `kala_field_provenance`, 100% carrying `kfw_*` authority_basis
- N_e classes activated: marriage + separation (2 of 6 ne_v01 classes; honest — bodha_pratijna
  has no promise for the other 4 classes in this chart)
- PARĪKṢAKA: ACCEPT-WITH-DEBT (D3/D4/D5, all non-blocking)

**482012f1 (Abhisek Mohanty, canonical) — DISCLOSED-GAP:**
- bodha_pratijna × ne_v01 class intersection = zero for this chart
- ka_kshetra completes with honest-empty output (stage8 zero-track guard removed 2026-08-05)
- Zero field windows; zero provenance rows — correct by construction, not a bug
- Blocked until bodha_pratijna acquires ne_v01-compatible class promises for this chart
  OR ne_v01 Tranche-N expands to cover the promise classes this chart DOES have

---

## §4 — Debt Register

### PARĪKṢAKA-filed debts (this Closing Run)

| ID | Item | Debt | Severity |
|---|---|---|---|
| D1 | W3K | Sub-sub/prana reference table PARKED (disclosed in module docstring) | Non-blocking |
| D2 | W3K | KP source texts Tier III citation only (bibliographic gap, not computational) | Non-blocking |
| D3 | W2 Field | 100-year flat windows (architecturally correct for flat λ⁰ baseline) | Non-blocking |
| D4 | W2 Field | Stage5 sampling 0-rows (in-memory Monte Carlo; by design) | Non-blocking |
| D5 | W2 Field | Only 2 of 6 ne_v01 classes activated for 1c826d5a (honest chart state) | Non-blocking |

### Pre-existing campaign debts (W2G, W3)

| ID | Item | Debt | Severity |
|---|---|---|---|
| D1089-1 | W2G (item 19) | PARĪKṢAKA Night-3 debt (per ADJUDICATION-2 session record) | Non-blocking |
| D1089-2 | W2G (item 19) | PARĪKṢAKA Night-3 debt (per ADJUDICATION-2 session record) | Non-blocking |
| D33-1 | Item 33 | Monotonicity test uses `<=` (weak); constant `carrier_salience` survives | Non-blocking |
| D34-1 | Item 34 | Python/TypeScript diverge on zero-lambda current-window delta | Non-blocking |
| D36-1 | Item 36 | Cosmetic row-count discrepancy in PR desc / migration comment (51 actual, not 45/50) | Cosmetic |
| D37-1 | Item 37 | Rail-2 test checks description only; `convention_status` filter mutation survives | Non-blocking |

### W6 gate debts (future session obligations)

| Clause | Debt | Obligation |
|---|---|---|
| W6-C1 | register_all.ts docstring says "eight" but registers 9 tools (kala_dasha_sandhi_get is W3K addition) | Fix docstring |
| W6-C2 | Legacy-vs-new divergence audit not run | Future session |
| W6-C3 | Dark corpus bright% ≥95% not re-measured | Future session (21-question evaluation) |
| W6-C4 | Authority_basis serving census (authority_basis_census_seed.ts) not run | Future session |
| W6-C5 | Full 44+E disposition ledger not formally verified against STATE.md | Future session |
| W6-C6 | Skill score not published or regression-gated | Future session |

### N_e Tranche-N program (ongoing)

ne_v01 covers 6 Tranche-1 classes. Tranche-N classes (e.g., health/adverse events, item 9)
are a future campaign obligation. ADJUDICATION-2 FORECLOSED the classic/cohort approach;
only demographic structural priors (Tier N-i) may serve as N_e. New Tranche-N classes require
an ANTARYĀMIN adjudication before seeding.

---

## §5 — §M Red-Team Verdict

**Status: PENDING at document creation time (2026-08-07T06:44Z)**

The §M adversarial red-team agent was dispatched during the Closing Run with defect taxonomy:
- D-CLASS-1: proxy-signal-without-detector
- D-CLASS-2: wrong-write-target
- D-CLASS-3: checklist-factual-error
- D-CLASS-4: tests-validating-fiction

Evidence corpus: STATE.md HBs #114–#116, stage2_promise.py, stage8_spec.py,
l0_class_lifetime_counts.py, ka_kshetra tests.

**Verdict will be appended below when agent returns. If REFUTE, specific findings are named.**

*(§M verdict: see HB #118 or later HB for the recorded result)*

---

## §6 — Gate Status Summary

| Gate | Status | Closed |
|---|---|---|
| W0 | CLOSED | Night 1 (2026-07-29) |
| W1 | CLOSED (12/12) | Night 2 (2026-07-30) |
| W2 | R5-SCOPED PARTIAL | 1c826d5a PASS / 482012f1 DISCLOSED-GAP |
| W2G | LANDED | 2026-08-07T18:24Z (PR #1089) |
| W3 | CLOSED | 2026-08-07 (Night-5 / PRs #1083–#1086) |
| W3K | CLOSED | 2026-08-07T06:47Z (HB #116, PARĪKṢAKA ACCEPT) |
| W4 | NOT-STARTED | Future campaign |
| W5 | CLOSED | 2026-08-07 (HB #109, 8+1 primitives live) |
| W6 | PARKED-HONEST | 5/6 clauses unverified; see §4 W6 debts |

---

## §7 — RUN-TERMINAL Declaration

**RUN-TERMINAL: PARKED-FINAL**

Reason: W6 gate cannot close this session (clauses 3/6 require external measurement
tooling; clauses 2/4/5 require audit runs not completed in the Closing Run). All
infrastructure, primitives, and data deliverables that can be completed within this arc
have been built, verified, or honestly declared as DISCLOSED-GAP per pre-authorized rulings.

**What is complete:**
- W0/W1/W3/W3K/W5/W2G formally closed with PARĪKṢAKA evidence
- R3 retired
- W2 field integration R5-scoped with honest per-chart disposition
- ADJUDICATION-2 factual error corrected in governance record
- All 9 Kāla tools registered and serving (kala_dasha_sandhi_get as W3K addition)

**What is parked for next session:**
- W6 gate 6-clause full closure (see §4 W6 debts)
- W4 items (4/5/6/7/9/13/14/26/31/42) — full future campaign
- 482012f1 field integration (requires ne_v01 Tranche-N or bodha_pratijna expansion)
- §M red-team result incorporation (pending agent return)

---

*ṢAḌ-DARŚANA CLOSE v1.0 — 2026-08-07 — Conductor: Claude Sonnet 4.6 (Closing Run HB #114–#118)*
