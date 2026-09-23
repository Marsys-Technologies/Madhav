---
artifact: FINAL_REPORT
version: "1.0"
status: CAMPAIGN_WP0_WP7_COMPLETE
date: 2026-09-23
executes: KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md (the autonomy contract);
          GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4 (WP0–WP7);
          KIMI_RESUME_PROMPT_GOCHARA_v1_0.md (resume-from-commit instructions)
branch: l3/gochara-autonomous-wp0-7 @ /Users/Dev/madhav-l3/gochara-wp0-7
evidence_class: producer prototype evidence throughout — synthetic fixtures and synthetic
  chart ids only (PB-7); no production service was modified by WP4–WP7
---

# FINAL REPORT — Gochara family elevation, WP0–WP7 autonomous campaign

## 1. State reached

All eight work packages of the WP0–WP7 campaign are delivered on branch
`l3/gochara-autonomous-wp0-7`. Test suite: **96/96 passing**
(`platform/python-sidecar/tests/l3/gochara/`, includes the 10 WP4 decomposed-comparison
tests). Every divergence observed between legacy and kernel was classified against
`WP3b_CLASSIFICATION.md` before being reported; the unclassified-divergence stop
condition never fired.

## 2. Artifact ledger

| WP | artifact / deliverable | location | commit |
|---|---|---|---|
| WP0 | Findings re-validation, nutation sign pin, consumer re-enumeration | `gochara_wp0_7/WP0_FINDINGS.md` | b262cbf6a |
| WP1 | Contracts design + golden-case fixtures | `gochara_wp0_7/WP1_CONTRACTS.md` | 35a419f5d |
| WP2 | Synthetic fixture suite (12 independently-derived cases + factorized scorer oracle) | `gochara_wp0_7/WP2_FIXTURES.md` | 46b9529cc |
| WP3a | `gochara_kernel` geometry package + acceptance tests (13/13, FLG_SIDEREAL) | `platform/python-sidecar/services/gochara_kernel/` | f775c2d6e |
| WP3b | Span-aware legacy baseline + delta classification | `gochara_wp0_7/WP3b_CLASSIFICATION.md` | 25aeab607 |
| WP3c | Resonance corrections R-1..R-6 (N-12 pre-approved honesty fixes) | `services/gochara_v3/` + docs | bd65433f8 |
| WP4 | **Decomposed comparison on workload WP4-SYNTH-1 (this session)** | `gochara_wp0_7/WP4_DECOMPOSED_COMPARISON_v1_0.md` + `tests/l3/gochara/test_wp4_decomposed.py` | this commit |
| WP5 | Honesty fixes H-1a/H-2/H-3/H-4/H-6 implemented; H-5 + N-14 escalated (may_touch/frozen contracts) | `services/gochara_v3/interval_solver.py`; `ESCALATIONS.md` | 719cf980b, 59bebe7dc, 28fd59245 |
| WP6 | Ledger/coverage/publication schema + writer layer on disposable DB; measured 200k-row pricing | `gochara_wp0_7/WP6_LEDGER.md`; migration 1072 | 25aeab607 |
| WP7 | 8 receiving-contract design packets + sentinel exit-gate test | `gochara_wp0_7/wp7_packets/` (00_INDEX, P-1..P-4, S-1/S-2, T-1, C-1, V-1, K-1) | 46b9529cc, 3d884a0c2, this commit (T-1/P-1/P-2 folds) |

## 3. WP4 measured results (headline)

Workload WP4-SYNTH-1: synthetic cubic Saturn/Jupiter curves, 731-day horizon,
1097 knots/body, synthetic chart id (PB-7). Full numbers in
`WP4_DECOMPOSED_COMPARISON_v1_0.md`.

- **Anchor equivalence verified**: legacy and kernel agree at every exact crossing
  (λ = 0.8 at t_exact, both conjunction legs) — deltas are off-anchor behavior only.
- **Five classified deltas measured**: A-2 step-vs-graduated (legacy 0.8 vs kernel
  0.7441 at t_exact+4 d); A-1 exception→0.0→certified-active; A-6 overlay-absent
  unknown-as-clear (1.0 vs honest `unavailable`); A-4 era-window edge clamp vs
  `truncated_at_horizon='both'`; A-5+B-4 peak-cap truncation (3/5 retained) +
  plateau-first-point vs cap-free admission with all-tied rank 1.
- **Contact-id stability**: byte-identical ids under re-partition (full span vs split
  vs shifted horizon).
- **Timing**: kernel end-to-end cold 0.00212 s; search 0.00062 s cold/warm; one batched
  solve per (chart, horizon) — 4 search-matrix cells, 1 era window. The historical 58.2-min
  century-run figure is a scale reading only, never a like-for-like claim (E-001).
- **Ledger**: write_contacts 0.00224 s / write_coverage 0.00141 s / warm serve read
  0.00051 s at this workload's 3 rows; 200k-row index-scale pricing stays WP6's
  (9.9 s load, ~0.07 ms warm reads, 293.9 MiB).

## 4. WP7 packets — final state

All eight packets remain `DESIGN_ONLY_NOT_IMPLEMENTED` (every target file is in another
owner's may_touch). Changes folded in this session:

- **T-1 (v1.1)**: WP4 kernel-side numbers filled the explicit placeholder; the
  trigger-side instrumentation is honestly declared open (trigger.py is outside
  may_touch); the `find_episodes` adoption decision stays evidence-gated and both
  kala_trigger and S-1 callers keep running per plan §10.
- **P-1 (v1.1)**: new §3.6 (P-1e) — H-5 serving rule: admission cap-free, trim at serve
  time with disclosed counts, never re-rank.
- **P-2 (v1.1)**: the same H-5 boundary folded into the capped-page rationale.

## 5. Boundaries honored

- **may_touch/must_not_touch**: no file outside the campaign's may_touch was modified.
  WP7 packets are design documents owed to their owners; WP5's blocked fixes
  (H-5 kernel-adjacent, N-14) were escalated, not forced (ESCALATIONS.md).
- **PB-7**: synthetic curves, synthetic chart ids, disposable WP6 database only; no
  person data anywhere in the campaign.
- **PB-3**: campaign commits use the PB-3 Bot identity.
- **Measured-only**: every number in WP4/WP6 artifacts is printed by a passing test;
  no estimates. Where workloads differ (58.2-min figure), the mismatch is declared.
- **Stop conditions**: zero unclassified divergences; zero frozen-contract violations.

## 6. Unreached states / open items (owned by later work packages or other owners)

- **WP8** — doctrine corpus: not started (out of this campaign's scope).
- **WP9** — shadow run: not started.
- **WP10** — epochal elevation (E-005) incl. the six-move comparison and the authority
  flip: not started; P-1/P-2/C-1 make serving ready for it.
- **T-1 trigger-side instrumentation** — owned by the kala_trigger owner; the adoption
  decision is evidence-gated on it (packet T-1 v1.1).
- **WP5 H-5 + N-14** — escalated (ESCALATIONS.md); blocked on may_touch/frozen
  contracts, resolved only by their owners.
- **E-001** — `KALA_COST_PROFILE_v1_0.md` / `KALA_BASELINE_v1_0.md` unreachable from
  this branch; WP4 proceeded with fresh numbers (recorded in ESCALATIONS.md by WP1).
- **WP7 packet implementations** — all eight packets are design-only; each owner
  implements against their packet without further discovery.

## 7. Disclosure

This campaign ran autonomously per `KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md`
with a resume per `KIMI_RESUME_PROMPT_GOCHARA_v1_0.md`. All evidence is producer
prototype evidence; nothing here is a production reading, a production number, or a
claim about any person. Live-read receipts for WP6 were produced against the disposable
dockerized Postgres (`gochara-wp6-disposable`) and are reproduced by the test suite.
