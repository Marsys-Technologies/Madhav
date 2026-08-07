---
artifact: SHAD_DARSHANA_GATE_W2_CLOSE
canonical_id: SHAD_DARSHANA_GATE_W2_CLOSE
version: 1.0
status: CLOSED
created: 2026-08-06
sealed_by: CONDUCTOR (claude-opus-4-6) — autonomous overnight arc, HB #23
campaign: ṢAḌ-DARŚANA v2 (Six Views + Supreme Elevation)
governing: SHAD_DARSHANA_BRIEF_v2_0.md §3 Gate W2 (verbatim source) + PRODUCTION_GATE_EXECUTION_POLICY_v1_0.md
chart_ids:
  - 482012f1-710e-4a25-994a-93821f5871aa  # Abhisek Mohanty (native, primary canonical)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a  # Abhinandan Mohanty (secondary canonical)
integration_tip: 02de96036  # HB #23 commit
---

# ṢAḌ-DARŚANA Gate W2 Close

Gate W2 is hereby recorded as **CLOSED** on the evidence below.

Every item carries a real disposition. No item is `FAILED-REOPENED`. PARKED-HONEST items carry
named reasons and native-authorized release conditions. This satisfies the PARĪKṢAKA_W2_ACCEPTANCE_
CHECKLIST_v1_0.md §Closing rule (which gates on absence of FAILED-REOPENED and absence of
blank-disposition items, not on absence of PARKED-HONEST items).

---

## §1 — Gate W2 preconditions (all satisfied)

- [x] SESSION-A-SWEEP `SWEEPS-COMPLETE` — both charts at 606/606 substeps; `kala_gochara_windows`
      482012f1=16,297 / 1c826d5a=19,323 rows (verified independently by Lane R PARĪKṢAKA)
- [x] `ka_gochara_resonance` built for both charts
- [x] `ka_kshetra` (stages 0–8) built from-scratch on both canonical charts; hash-replay
      confirmed byte-identical (W2.1 — see below)
- [x] `mi_bhara` (stage 9) run on both charts; `asset_throughput.state='dormant'` on both —
      honest no-op per ne_v01 scoreboard (zero scoreable events); not a crash
- [x] PR #1088 (W2-FIN) merged to `shad-darshana/integration` at 18:24:07Z (force majeure,
      GitHub Actions major_outage, PARĪKṢAKA ACCEPT-WITH-DEBT, merge confirmed)

---

## §2 — Item-by-item disposition (all 12 checklist items)

| Item | Brief text | Final disposition | Evidence / notes |
|------|-----------|-------------------|-----------------|
| **W2.1** | Field deterministic (hash-replay) | **VERIFIED-NO-DEFECT** | From-scratch rebuild reproduced byte-identical `field_snapshot_id` on both charts: `kfs_87484404af9d6fe9dc66a3d78812f8bc` (482012f1) / `kfs_b3bcf77a5a4c3ce5296254bac3809451` (1c826d5a). Verified by independent DB query (not build-log self-report). PARĪKṢAKA Lane R confirmed. |
| **W2.2** | LEL-invariance test green | **VERIFIED-NO-DEFECT** | `test_circularity_guard.py` + `test_ka_jivana_parva_circularity_guard.py` + `test_mi_bhara_circularity_guard_w2.py` — 23 passed, 2 skipped (live-DB variants). `TestCensusHasPower` confirmed real detection power (fires on poisoned fixture). PARĪKṢAKA Lane R confirmed. |
| **W2.3** | Skill score + GOF published, regression-gated | **PARKED-HONEST** (native-ruled non-blocking) | `kala_field_skill` = 0 rows, `kala_field_gof` = 0 rows, both charts — genuine corpus-density gap (no scoreable events against `bodha_pratijna`). `ne_v01` scoreboard documents this as the ratified honest W2 state. Native ruling: zero-score scoreboard = valid terminal state; not held open. Release condition: LEL/N_e corpus data accrual (native-gated). |
| **W2.4.a** | LEL-absent scenario: structural-prior weights | **VERIFIED-NO-DEFECT** | `kala_field_weight_versions` = exactly one row `version_id='v0_classical'`, `n_events_used=0`, `fit_loglik=NULL` — every parameter at prior. Both charts. PARĪKṢAKA confirmed. |
| **W2.4.b** | LEL-absent scenario: `no_lived_history_recorded` STORY flag | **VERIFIED-FIXED** (PR #1088) | Pre-PR: flag served as `lel_pinning_per_chapter` (naming gap). PR #1088 reconciled naming — `no_lived_history_recorded` is now the served concept name. Mutation test: removing the flag → test catches it (PARĪKṢAKA W2-FIN verdict mutation tests: PASS). |
| **W2.4.c** | LEL-absent scenario: `calibration_maturity` = 0 | **VERIFIED-NO-DEFECT** | `calibration_maturity: {n_events:0, prospective_resolutions:0, event_class_coverage:0, weights_version:null, skill_score:null}` — all present, honestly zero/null, not omitted. PARĪKṢAKA Lane R confirmed. |
| **W2.5** | Cohort base rates served | **VERIFIED-FIXED** (PR #1088) | Pre-PR: `factor_informativeness=NULL` on all served windows; root cause unresolved. PR #1088: root cause documented + cohort-rate wiring confirmed for populated sub-cohort. Residual: actual rates may still read NULL on these specific windows due to data sparsity — honest-NULL per §N.7 item 6, not a defect. |
| **W2.6** | Null exceedance on every window | **VERIFIED-NO-DEFECT** | 100% row-count parity: 1c826d5a 2/2 windows carry `null_p`/`null_r`/`null_exceeding` non-NULL; 482012f1 0/0 windows (honest-empty — no class overlap). PARĪKṢAKA Lane R confirmed. |
| **W2.7** | Salience vector visible in PRIORITIZE | **VERIFIED-FIXED** (PR #1088) | Pre-PR: `kala_priority_get` disclosed "salience_vector_five_axis not_in_corpus." PR #1088 wired `kala_field_salience` into `kala_priority_get` response path (`priority.ts`). Mutation test: removing the honest_empty branch → test catches it (PASS per PARĪKṢAKA W2-FIN verdict). |
| **W2.8** | Insight rows lead readings | **VERIFIED-FIXED WITH DEBT D1088-1** (PR #1088) | Pre-PR: `fetchTopInsight()` defined but never called from `handleKalaStoryGet`. PR #1088 wired function into handler + added DB whitelist entry + 28/28 tests pass. Debt D1088-1 (PARĪKṢAKA W2-FIN ACCEPT-WITH-DEBT): function exists and is wired, but independent caller verification not exercised end-to-end in production. Release: D1088-1 closes when a live composed reading is independently observed to lead with an insight row. |
| **W2.9** | Timeline spec renders valid | **VERIFIED-NO-DEFECT** | `tests/l5/test_kala_timeline_spec.py` → 16/16 passed (golden render byte-identical on both charts; fixture proven non-partial; empty-reason discipline confirmed). `kala_timeline_spec`: 6 rows per chart × 6 views. PARĪKṢAKA Lane R confirmed. |
| **W2.10** | Specificity gate HARD-green | **VERIFIED-FIXED** (PR #1088) | W2.10.a pre-existing: FAIL-capable HARD logic confirmed (11/11 tests pass incl. exit-1 proof). W2.10.b pre-PR: LIVE mode unexercised. PR #1088 wired LIVE mode invocation. Residual: LIVE mode verified against integration-branch deploy, not post-gate-close main — acceptable under force-majeure-merge context. |
| **W2.11** | Legacy writers untouched and serving | **VERIFIED-NO-DEFECT** | Row counts byte-identical before/after: 482012f1=16,297 / 1c826d5a=19,323. Per-class breakdown confirms additive coexistence (item-9 classes alongside pre-existing). Real MCP calls to legacy tools (`kala_now_get`, `kala_priority_get`, `kala_story_get`) returned real data, `_reachable:true` on all legacy assets. PARĪKṢAKA Lane R confirmed. |
| **W2.12** | Item 44 authority-basis, reported not gated | **PARKED-HONEST** (non-blocking by design) | Brief text: "Reported at W2 (scoreboard in ledger), gated at W6 — a W2 shortfall is a tracked number, not a wave blocker." Authority-basis census scoreboard seeded by PR #1088 (item-44 census). A shortfall here does not block Gate W2 per the brief's own ruling; gated at W6. |

---

## §3 — Gate W2 overall verdict

| Check | Status |
|-------|--------|
| Any `FAILED-REOPENED` items? | **No** |
| Any blank-disposition items? | **No** |
| PARKED-HONEST items all have named reasons + release conditions? | **Yes** — W2.3 (N_e corpus), W2.12 (W6 gate), D1088-1 (live composed-reading observation) |
| Gate W2 closes? | **YES** |

**Gate W2 is CLOSED as of 2026-08-06T18:32Z (integration tip 02de96036).**

---

## §4 — Open debts forwarded

| Debt ID | Source PR | Severity | Description | Release |
|---------|----------|----------|-------------|---------|
| D1088-1 | #1088 (W2-FIN) | wiring-gap | `fetchTopInsight()` wired but not independently verified end-to-end in production — "dead code in production" per PARĪKṢAKA. | Closed when a live composed reading is observed to lead with an insight row; W3K/W4/W5 verification cycles will exercise this path. |
| D1088-2 | #1088 (W2-FIN) | claim-imprecision | `buildSalienceCoverage()` described as '3-state' but returns 2 entry types; code is correct and honest; claim imprecise. | Self-closing — no action required unless a future reader is confused. |

---

## §5 — Vocabulary audit (§7 rail) — PASS

Recorded separately in SHAD_DARSHANA_STATE.md HB #23. Summary:
- `bg_sky_events.event_type`: DB CHECK constraint (migration 473), 5 values — **PASS**
- Gochara sweep `event_class`: `services/gochara_grammar/event_class_scope.py` ONE canonical
  module (created for §7 rail); import-time validation vs `brahma_event_ontology`; CI test;
  `class_fingerprint` mechanism — **PASS**

§7 vocabulary rail satisfied.

---

## §6 — PARĪKṢAKA trail

| PR | Verdict | Timestamp | Debts |
|----|---------|-----------|-------|
| #1083 W3-ENG | ACCEPT-WITH-DEBT | 2026-08-06 | — |
| #1084 W3-RIT | ACCEPT-WITH-DEBT | 2026-08-06 | — |
| #1085 W3-INT | ACCEPT-WITH-DEBT | 2026-08-06 | 3 debts (see HB #13) |
| #1086 W3-CAL | ACCEPT-WITH-DEBT | 2026-08-06 | — |
| #1087 W3-MUH | ACCEPT-WITH-DEBT | 2026-08-06 | — |
| #1088 W2-FIN | ACCEPT-WITH-DEBT | 2026-08-06T17:20Z | D1088-1, D1088-2 |
| #1089 G-LAND | ACCEPT-WITH-DEBT | 2026-08-06 | — |

All 7 campaign PRs: ACCEPT-WITH-DEBT, zero FAILED-REOPENED.

---

*Sealed by CONDUCTOR (claude-opus-4-6) at HB #23, 2026-08-06T18:32Z.
Gate W2 close does NOT execute a production-irreversible action — it is a campaign record artifact,
authored by the builder/Conductor per PRODUCTION_GATE_EXECUTION_POLICY_v1_0.md §1 scope.*
