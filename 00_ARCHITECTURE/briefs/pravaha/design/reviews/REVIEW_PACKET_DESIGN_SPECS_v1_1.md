---
artifact: REVIEW_PACKET_DESIGN_SPECS
canonical_id: REVIEW_PACKET_DESIGN_SPECS
version: "1.1"
status: PARKED_PENDING_NATIVE_DISPATCH
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
purpose: "B3.7 — second review round of specs v1.1 + oracles v1.1 + protocol v2.0 + registry v2.0, before the freeze decision (B3.9, gated on D-SPECS and D-PROTO)"
dispatch: "native-only. Stream B does not dispatch reviewers. The native runs Kimi K3 and Codex per ruling (1) of 2026-09-29."
precedent: "design/reviews/REVIEW_PACKET_DESIGN_SPECS_v1_0.md — same ground rules, same evidence discipline"
---

# Review packet v1.1 — Gochara specs v1.1, oracles v1.1, protocol v2.0 (B3.7)

You are one of two independent reviewers in the **second** round. Round 1 (your predecessors'
reviews of specs v1.0) ended in REWORK on both sides; every finding was dispositioned in
`design/RECONCILIATION_DESIGN_SPECS_v1_0.md` and the rework landed as the v1.1/v2.0 artifacts
below. You are asked whether the rework **correctly resolves what round 1 found** — and whether
the new measurement stack (registry + protocol v2.0 + the '3.0' re-run) is sound.

## 1. Review surface (full sha256, branch `campaign/pravaha`, 2026-09-29)

| Artifact | SHA-256 |
|---|---|
| design/GOCHARA_DESIGN_SPECS_v1_1.md | d5d9e85b08358230cf7f47f5531a3bb0709b85f6d33c356f8ef2882a3f130161 (updated after G-10 resolution; see §5) |
| design/GOCHARA_TEST_ORACLES_v1_1.json | 96c27dfd858167e07980d22cf2d94010e776f092610c3ad77c9e93d571128926 (updated after G-10 resolution; see §5) |
| design/RECONCILIATION_DESIGN_SPECS_v1_0.md | f5f11c2f07068135dbe1e764dae34e381f6f38306f52e9a60458d79dd194c28c |
| measurement/EVALUATION_PROTOCOL_v2_0.md | 21fa3bc6fcad9cce140c2225fcff44ea84a8953229a533cacec9e391abc7e999 |
| measurement/EVENT_REGISTRY_v2_0.md | dcce07ff1247f68991f109e77b17e7739b007ac47ace22c838619ac2a2bd78de |
| measurement/BASELINE_3_0_v2_0.md | 9e1318e70e7ff5c09695baf6c537b6600dbe4d701eba32ba2b558ce473902964 |
| measurement/baseline_3_0_extract_v1_0.json | 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff |
| measurement/rerun_3_0_v2_0_scorer.py | 951f98034e155e45500f24eca794312aabed4746b227611bcbdab89f29bd6b5d |
| measurement/random_controls_v1_0.json | ef6ad8a2dc40e0d622ef8ca72100e1fede96f4ce9537d87dbb12d0a1f559a2e6 |
| measurement/rerun_per_event_v1_0.json | e685ecb6a6d241022392f04d4e9e8b3a22f0073de555ff166e33df3c286ef9ad |
| design/GOCHARA_DESIGN_SPECS_v1_0.md (history) | c87919dbe06fc6828ee719805143a319898b6ebd4c0ae502d67deb14a5debea0 |
| design/GOCHARA_TEST_ORACLES_v1_0.json (history) | 4bd029feddf1ebc19b1f951ec5dc341eca80222666a981ce81b471c31dd1c95b |
| measurement/EVALUATION_PROTOCOL_v1_0.md (history) | c7c5a8370443c8d24b73336b3693ed7f63f793b838478e185f620724b0efbb0f |
| measurement/EVALUATION_PROTOCOL_v1_1.md (history) | e093010dff71b15b67629d6796227843632a894d73d7ab58b3dba7cef821bd2f |
| measurement/EVALUATION_PROTOCOL_v1_2-DRAFT.md (history) | 8ab737edf0cdf931509171da79631bd3d22bce059fa1eb1e96fc98139ae50f16 |
| measurement/BASELINE_3_0_v1_0.md (history) | 8562c6c885d67a102723bc7949154e2ffb03973562e4a5f91ed7cee9f35d1a75 |

The round-1 reviews you are checking against: `design/reviews/KIMI_K3_REVIEW_DESIGN_SPECS_v1_0.md`
(sha256 7872f239…c8c7) and `design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_0.md`
(sha256 536d2b1a…a8ee).

## 2. Ground rules (unchanged from round 1)

- **Read-only.** Do not edit any file. Your output is your review text, nothing else.
- **Verify what you can.** File:line citations against the repo (branch `campaign/pravaha`);
  recompute arithmetic yourself; no rule number without the count behind it.
- **Label every claim**: `[D]` served-corpus doctrine · `[S]` source you read · `[L]` evidence
  appendix figure · `[P]` practice · `[J]` judgment · `UNVERIFIABLE_HERE` where the packet does
  not let you settle it — never guess.
- The doctrine (`sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md`) stays SEALED; you are not
  asked to re-review it.

## 3. What changed (the reconciliation is the map)

**Specs v1.0 → v1.1** and **oracles v1.0 → v1.1**: every change traces to a dispositioned
finding in `RECONCILIATION_DESIGN_SPECS_v1_0.md` §A–§B (Kimi F1–F7/Q-M1…5; Codex
S-01…S-08/M-01…M-06/Q-M1…5; defect-coverage rows #1, #5, #19–#24, #26, N9). Headline changes:
O-RP-5 is one test in prose and JSON (Saturn 8th-from-Moon = evidence FOR adverse classes);
provenance vs operator role separated (all D-PADMIT + P6 Moon-channel = testimony-only); P3 as
explicit Boolean + per-class truth table; P5a–e independent with missing-data states; sign-mean
AV comparator removed; chart-specific AV operands `unresolved` pending G-10; saham activation =
three separate [D] modes; aspect-direction invariant + O-AD-1…4 first in the JSON; typed
contracts with keys/FKs/null states; oracle inventory = 55, index = JSON count, each with a
literal fixture plus a mutation that must fail.

**Protocol v1.2-DRAFT → v2.0** (v2.0 supersedes v1.0/v1.1/v1.2-DRAFT, all kept as history):
registry-sourced events (EVENT_REGISTRY_v2_0.md: 46 held-out = 27 timing-usable + 19 year-grain;
CURRENT.01 status-only; 2026-04-08 excluded; MBA enrolment restored; grandfather as interval);
masked horizon H = 10,334 d (1998-01-01 → 2026-04-17); single T-time rule (all errors capped
182 d, misses reported separately); T-FP per-class budgets `min(1, 3·n_c·90/H)` with printed
arithmetic; T-rank floor `floor(27/2)+1 = 14` of the audited cohort, rank-unproven blocks the
flip; dedup before counting N; ties = average rank; eligible misses at worst-rank 100; seed
482012 controls materialised; annotation guard.

**'3.0' re-run under v2.0** (`BASELINE_3_0_v2_0.md`, from the pinned extract — 914 rows,
read-only): T-cover 31/46 (the new floor); T-time 182 d capped median (FAIL); T-rank
rank-unproven 1/27 (FAIL); T-FP 8/9 adverse classes FAIL at 99.87 % burden; random controls
67.6 % ≈ coverage 67.4 %; era-boundary fingerprint 59.8 % → class-indiscriminate.

## 4. Explicit questions to the reviewers

1. **Overridden findings.** The reconciliation records exactly one override: Kimi Q-M1
   ("do not re-run '3.0'") overridden by the native's instruction #7, with Codex Q-M1 accepted.
   Is this override correctly recorded as a directive-supersession rather than an adjudication?
   If you find any *other* disposition in the reconciliation that is in substance an override
   wearing an "accepted" label, name it.
2. **Oracle fixtures.** For each of the 55 oracles in `GOCHARA_TEST_ORACLES_v1_1.json`: is the
   prose `given` field literal enough to build a fixture from **without asking a question**? If
   not, say which oracle ids and what is missing.
3. **Registry judgment calls.** (a) EVT.2026.03.20.01 remapped business_launch → major_gain
   (LEL:1500–1508: project closure with "enormous profits" — the dated point is a realised
   gain). (b) EVT.2011.06.XX.01 MBA enrolment restored, making the timing-usable cohort
   **27, not 26** (both round-1 reviewers computed 26 without this row). Are both correct
   against the LEL as written?
4. **Instant-class misses: '3.0' behaviour or scorer artefact?** — **settled by Stream B before
   dispatch; please verify the settlement.** Evidence: in the pinned extract, the five classes
   education_milestone (40 rows), career_change (30), business_launch (30),
   foreign_settlement (30), separation (30) serve **only zero-width rows** (`window_start =
   window_end = peak_date`, `temporal_shape = 'chain'`). The scorer's instant handling is:
   dedup merges only abutting/overlapping rows (chain instants are scattered, so they survive
   as separate 1-day candidates); containment requires `ws ≤ event_date ≤ we`, i.e. an exact
   day match; month-grain events use the 15th as proxy date (protocol v2.0 §5). Even under the
   most lenient month-overlap reading, only 2 of the 16 instant-class event-months contain any
   served day at all (2004-07: one day; 2024-02: one day, 2024-02-05 vs the exact event
   2024-02-16). Conclusion stated in the baseline: the misses are '3.0''s served behaviour
   (chain instant classes admit 0.09–0.12 % of the horizon), not a scorer artefact. Do you
   confirm, or can you construct a reading of protocol §5 under which the scorer is wrong?
5. **Horizon and budgets.** Masked horizon H = 10,334 d (1998-01-01 → 2026-04-17; full LEL
   horizon 10,592 d; 258 post-mask days excluded) and the per-class T-FP budgets
   `min(1, 3·n_c·90/H)`: n_c = 1 → 2.61 %, n_c = 2 → 5.23 %, n_c = 0 → single-event allowance
   2.61 %. Recompute; is the n_c = 0 allowance rule sound, and is the factor-3 slack over the
   ±45-day T-time tolerance defensible as stated?

## 5. Gap G-10 — RESOLVED by native routing before dispatch (updated 2026-09-29)

The native routed G-10 to Stream B directly (read-only pin from `chart_facts`). Result:

- **Pinned extract:** `design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json` (sha256
  `312de09e791e34e58377b7c0956e39f6691490bd2cfd0a27b415a7055c88fe83`) — 96 rows
  (`ashtakavarga_bindu_sign`, 7 BAV × 12 signs + SARVA, total 337) with fact_ids, build
  `aa9602ce-79df-4675-91c0-d08ade003d67`, engine `pyjhora/1.0.0`, ayanamsha
  `lahiri_chitrapaksha` (krishnamurti / raman / surya_siddhanta_classical / true_chitra
  recorded as available, unused).
- **Native check (1) — build consistency, answered:** the AV rows carry build aa9602ce while
  the natal positions in use carry build 1c092ffb. Settled empirically, not by assumption:
  pyjhora 1.0.0 fed the graha_position (build 1c092ffb) sidereal longitudes reproduces **all
  96 pinned values exactly** (extract §consistency_check prints the method). The pinned rows
  ARE consistent with the positions in use.
- **Native check (2) — tier honesty:** the rows are `verification_pass_status = single_pass`;
  the specs carry that tier as-is and do not describe them as verified.
- **P5c correction:** donor-level contributions are not out of reach in principle — the
  PyJHora prastāra writer (`ashtakavarga_bindu_contributor`, 7×8×12) is merged in PR #2731
  (migration 1086) — but rows exist only after a native-authorised ga_strength rebuild of
  482012f1, which the native has deferred. P5c stays disabled with **that** reason ("donor
  rows pending a native-authorised ga_strength rebuild"), not "no L1 source". P5d's
  piṇḍa-dependent operands are pending the same rebuild.
- Specs v1.1 §2-P5/§8 and oracle O-BP-5 updated accordingly (specs sha256 changed — see the
  updated hash table below).

Updated hashes after the G-10 resolution (others unchanged from §1):

| Artifact | SHA-256 |
|---|---|
| design/GOCHARA_DESIGN_SPECS_v1_1.md | d5d9e85b08358230cf7f47f5531a3bb0709b85f6d33c356f8ef2882a3f130161 |
| design/GOCHARA_TEST_ORACLES_v1_1.json | 96c27dfd858167e07980d22cf2d94010e776f092610c3ad77c9e93d571128926 |
| design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json | 312de09e791e34e58377b7c0956e39f6691490bd2cfd0a27b415a7055c88fe83 |

## 6. Out of scope for this round

'4.1'/'5.0' scoring (awaits D-PROTO); the freeze itself (B3.9, after D-SPECS and D-PROTO);
the generalised PG353 battle-scale attenuation (removed in v1.1; ruling D-PG353 pending with
the native).
