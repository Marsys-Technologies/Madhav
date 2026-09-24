# REMAINDER FINAL REPORT — v1.0

**Brief:** `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`
**Branch:** `l3/gochara-autonomous-wp0-7` (worktree `/Users/Dev/madhav-l3/gochara-wp0-7`)
**PR:** https://github.com/Marsys-Technologies/Madhav/pull/2731 (`feat(l3-gochara): …`, base `main`; body updated to name migrations 1085/1086 explicitly)
**Date:** 2026-09-24

Merge lands code only — no builds were run under the 2026-08-21 standing order. All migrations are disposable-DB-only. No shared database was written to.

---

## 1. State reached per task

### §4 — Point-1 residuals (A-class): COMPLETE (code landed; flags default-preserving)

| Item | State | Commit |
|---|---|---|
| N-17 cap-free peak admission | done | `6a1c23195` |
| N-22/N-13 interim sign-level bindu (flag `kakshya_bindu_interim`, default off) | done | `94abfba70` |
| M-6 derived target-contract rows | done | `ddf985751` |
| M-1 `activity_shape` flag (legacy_box default) | done | `f2cbe0705` |
| M-3 `moon_channel` split flag (blended default) | done | `c303ff473` |
| N-14 `nodal_drishti` removal flag (enabled default) | done | `93b6f2818` |
| N-15 `sade_sati_mode` testimony demotion | done | `98df8bc40` |
| N-21 standing rule recorded (testimony, never weight) | done | `dd84fa311` |
| N-16 citation-drift sweep | done | `4b0e0553d` |
| WP8 M-1 orb battery / M-2 retrograde ablation / factor-delta report | done | `597b29434`, `73a7cd1a3`+`0481d4565`, `627deb504` |

Review note: `wp7_packets/REVIEW_REQUEST_S4.md`.

### §5 — WP9 overlays on the kernel (A-1 authorized): COMPLETE

5.1 overlay stamp columns + migration 1082 (`a5ac0caad`); 5.2 M-8 vedha exceptions (`41e4843cd`); 5.3 vedha+moorti on the kernel with requested-horizon coverage / F-11 (`0c876fbe4`); 5.3 report + 5.4 Kota PRESERVE record (`7cca66fa2`). Review note: `wp7_packets/REVIEW_REQUEST_S5.md`.

### §6 — eight receiving-contract packets (WP7): COMPLETE

C-1 `7bd66b450` (+note `d153aa7c0`), P-1 `d668e3e87`, P-2 `6d7c40df3`, P-3 `273730192`, P-4 `1019b1f12`, K-1/V-1 `f256b24d3`, S-1/S-2 `e6a7a50fd`, T-1 note-only `40441b7a4`. Review notes `REVIEW_REQUEST_C1/P1/P2/P3/P4/K1/V1/S1_S2/T1.md` in `wp7_packets/`.

### §7 — WP10

- **§7.A:** done (follow-up delegation, 2026-09-24) — WP10 runbook prepared as runnable artifacts under `platform/python-sidecar/scripts/kala_gochara_cutover/` (steps 0–10 + evidence templates + production guard per tranche flag) and rehearsed on a disposable DB (55434); gate `tests/l3/gochara/test_wp10_cutover.py` 16/16 green (re-verified 2026-09-24). Outcomes + carried NOT_RUNs in `WP10_REHEARSAL_v1_0.md`; review note `wp7_packets/REVIEW_REQUEST_S7A.md`. Step 0 (clear-guard cherry-pick of `eb00da67d`), step 2 (restore drill — no dump locally), and step 7 gate 3 (TS-only) remain NOT_RUN by design.
- **§7.B (tranche 1, steps 0–5): ATTEMPTED 2026-09-24, HALTED at step 3.** The frontmatter flags were read fresh from disk and are now **TRUE** (both tranches authorized by `GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md` §3; this section previously reported them false — that was the pre-authorization state). Run executed per brief §12.15 order — **step 3 first** — with the Cloud SQL proxy on 127.0.0.1:5433 and the production guard flags acknowledged. **Step 3 STOPPED on a privilege precondition:** `amjis_app` lacks CREATE on schema `public` (owned by `data_plane_schema_owner`; no other credential exists locally), so `step03_guard_n6a.sql` aborted on its first statement and rolled back cleanly — production verified byte-identical to pre-state (no function, 0 triggers, generations `v1=38287`/`3.0=1830` unchanged, century `is_active=false` from the strategic session's earlier half intact). Steps **0, 1, 2, 4, 5 NOT RUN** — the failed-gate rule halts the tranche; never proceed past a red gate. Evidence: `platform/python-sidecar/scripts/kala_gochara_cutover/evidence/step03_evidence.md`. Escalation: **E-015** with the native's operator path (run step 3 as `data_plane_schema_owner`/`postgres`, or GRANT CREATE ON SCHEMA public TO `amjis_app`).
- **§7.C (tranche 2, steps 6–10): NOT STARTED** — tranche-1 evidence green is a precondition and does not exist. Per E-012, tranche 2 would anyway stop at step 7's `windows_present` gate (the `'4.0'` windows projection has no writer; the gates are deliberately not weakened).
- R-1..R-6 take effect only at a resonance rebuild sequenced at WP10 step 6.

### §12 — DELTA items (2026-09-24, after this report's first version)

| Item | State | Evidence / commits |
|---|---|---|
| §12.3 (4.13a–i conformance fixes, migration 1087) | done — disposable DB only | `8b5d7f4ed`, `c2eb8a780`, `660e12129`, `a54ee98c1`, `3d606523b`, `82e320cb8`, `5ca1e17e7`; review note `wp7_packets/REVIEW_REQUEST_12_3_conformance.md` |
| §12.4 KALA_SYNERGY_BINDING §B1–B7 adopted by reference | done — live binding **v2.3 @ `7374d8f71`** (never the version quoted in the brief) | proof matrix `wp7_packets/BINDING_PROOF_MATRIX_v1_0.md`; detectors `tests/l3/gochara/test_b_binding_conformance.py` (7 tests, each with a negative fixture); commits `dc2d05b46`, `b45da9ec7`, `b07f42e44`; review note `wp7_packets/REVIEW_REQUEST_12_4_binding.md` |
| §12.5 test-isolation defect | done | earned-signal guard in `tests/l3/gochara/conftest.py` (`assert_real_ephemeris`); full battery green |
| §12.9 upstream-fingerprint gap (vedha + mūrti) | done — by the parallel L3 session | `bb7644ee4`, `b70115631`; step 6 exits 7 if either overlay is stale |
| §12.13/'4.0' projection writer | **open — E-012, native decision needed** | step 7 `windows_present` gate + step 8 refusal installed (deliberately not weakened); the writer itself is unbuilt and unassigned |
| §7.B tranche 1 | **HALTED at step 3 — E-015, native action needed** | see §7 above |

### §8 — loose ends: COMPLETE

| # | Task | State |
|---|---|---|
| 8.1 | N-18 push + PR | done — PR #2731 |
| 8.2 | N-19 KALA_COST_PROFILE + KALA_BASELINE landed with attribution; §10 Value-row CI gate made real (asserts presence, NOT_RUN when absent) | done — `2b367cfc9`, test green |
| 8.3 | N-20 plan v2.2 — ten WP0 consumers into §6.1, w44 ↔ N-16 cross-ref, no guard for W41–W45 `_v2` | done — `5db94811d` |
| 8.4 | G-9 vedha repair, migration **1085** + disposable-DB test 4/4 | done, then **RETIRED (E-010)**: repair already applied by L0 (PR #2727); 1085 files removed; step 4 refuses it — `8a6b94a86` (superseded) |
| 8.5 | G-10 `ashtakavarga_bindu_contributor` writer change + schema entry + migration **1086** + tests 8/8 | done; 1086 **renamed to the L1 layer (E-010)** — an L1 lane applies it, never this tranche — `1fab2364e` |
| 8.6 | Reviewer for Kṣetra rulings 7/8/9 | **named 2026-09-24** (native ruling §4, O-3): a fresh independent session, dispatched same day; outcome is that session's, not this run's |

Review notes: `REVIEW_REQUEST_8_4_G9.md`, `REVIEW_REQUEST_8_5_G10.md`. Nothing is marked `REVIEWED`; the native runs the K3 review + reconciliation loop.

## 2. Unreached states (explicit)

- **WP10 tranche 1:** ATTEMPTED and HALTED at step 3 (E-015 — privilege precondition; steps 0/1/2/4/5 NOT RUN). Both authorization flags are now `true` (native ruling 2026-09-24 §3); the halt is a database-privilege fact, not an authorization gap.
- **WP10 tranche 2:** not started (tranche-1 precondition unmet; would also stop at step 7 per E-012).
- **'4.0' windows projection writer:** unbuilt, unassigned (E-012) — native decision needed.
- **Kṣetra rulings 7/8/9 reviewer:** named 2026-09-24 (O-3 — a fresh independent session; `KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT_v1_0.md`); outcome not this run's.
- **NOT_RUN items:**
  - WP9 5.3 real moorti day-grade error rate [U] — synthetic fixtures only (0/4 and 2/2); no production-data run authorized.
  - G-9 migration 1085: **RETIRED (E-010)** — files removed; the repair was already applied by the L0 session (PR #2727). G-10 migration 1086: renamed to the L1 layer; not this tranche's. Neither applied to any shared DB.
  - N-19 value-artifact gate was green here (files present on this branch); on branches without them the test skips NOT_RUN by design.
- **Pre-existing failures (baseline, unrelated, verified failing on the clean tree):** `platform-mcp` vitest 78 failed / 2167 passed; `tests/l3/test_ka_gochara.py::test_router_import` (ModuleNotFoundError); `tests/test_swiss_state_boundary.py::test_generated_inventory_is_exact_and_has_no_unresolved_live_owner`.

## 3. Escalations (ESCALATIONS.md) — summary

- **E-001:** KALA value artifacts unreachable from this branch → resolved by §8.2 (files landed with attribution).
- **E-002:** Branch ahead of plan's pinned source_revision — drift record, no blocker.
- **E-003:** H-1b out of scope for this run (explicit in the brief).
- **E-004:** WP0 consumer re-enumeration (ten consumers plan §6.1 did not name) → resolved by §8.3 (plan v2.2 table).
- **E-005:** N-14 designed-but-not-implemented → superseded this campaign: `nodal_drishti` removal flag implemented (`93b6f2818`).
- **E-006:** RESOLVED 2026-09-23 (`59bebe7dc`) — WP5 honesty fixes H-1a/H-2/H-3/H-4/H-6 implemented; original entry kept for the record.
- **E-007 + addendum:** migration reservation; initial next-free 1077 superseded after `origin/l0/vedha-and-frame-repair` pushed 1075–1079 (all five APPLIED to production 2026-09-23); this branch's 1075/1076 renumbered to **1080/1081** (never applied outside a disposable DB, so the never-renumber-after-apply rule was not engaged); next free 1082.
- **E-008:** Yamakaṇṭaka honesty in M-6 derived target rows; provisional weights flagged.
- **E-009:** 2026-09-24 all-head re-scan (corrected regex — an earlier draft missed names with digits after the prefix); max prefix **1084**; **1085 (G-9) and 1086 (G-10) reserved** and used.
- **E-010:** 1085 **retired** (would abort in production; repair already applied by L0, PR #2727); 1086 renamed to its layer (L1); step 4 `REFUSED` set + `assert_no_refused_migrations()`; A-2 literal-scope question (1082–1084/1087) recorded as the native's.
- **E-011:** §12.3 additive migration numbered **1087**; disposable DB only; production application WP10-gated.
- **E-012:** the `'4.0'` windows projection has **no writer** — step 7 `windows_present` gate + step 8 refusal installed; tranche 2 stops rather than flip onto an empty generation; writer owner is the native's call.
- **E-013:** two hard DAG-guard violations in `ka_gochara_resonance` (reads `ga_dashas`, `ga_yoga`, neither in `depends_on`); both producers verified `lit` on the canonical chart; edges to be added as their own reviewed change.
- **E-014 (+4 addenda):** century writer was armed (`is_active=true`, state `error`) with no `'3.0'` guard; strategic session applied the `is_active=false` half; seed fix on PR #2734 (pending merge); the durable trigger half became tranche-1 step 3.
- **E-015:** tranche 1 HALTED at step 3 — `amjis_app` lacks CREATE on schema `public`; native operator path recorded (run as `data_plane_schema_owner`/`postgres`, or grant CREATE to `amjis_app`); production verified unchanged.

## 4. Migrations landed (all disposable-DB-only)

1080/1081 (renumbered resonance target state + ledger coverage publication), 1082 (WP9 overlay stamps + `upstream_fingerprint` on mūrti, §12.9/§12.12), 1083 (L5 `contact_id`), 1084 (K-1/V-1 registry edges — the `ka_kshetra → ka_gochara` edge HELD OUT per `64bdc10da`), 1087 (§12.3: inclusivity, six-state F06 completeness CHECK, time_basis CHECK, tier_basis). **1085 was RETIRED and its files removed (E-010); 1086 was renamed to the L1 layer and is not this tranche's.** None applied to any shared or production database — the tranche-1 attempt (§7.B) halted at step 3 before any migration step ran.

## 5. Protected data / §3 hard list

Untouched. No OCR/source-data files were modified (read-only consultation of already-cited passages only); no production or shared DB was written; no applied migration was renumbered; WriterBase conformance preserved (orchestrator conformance tests green).

## 6. Verification battery (final state, 2026-09-24 close)

- Gochara suite: **334 passed, 0 failed** (`/opt/homebrew/bin/python3 -m pytest tests/l3/gochara -q` from `platform/python-sidecar`) — includes the §12.3 conformance tests, the §12.4 binding detectors (7), the §12.5 guard, and the §7.A WP10 cutover gate (`test_wp10_cutover.py` **16 passed**, re-verified 2026-09-24).
- Migration-number guard: `cd platform && npm run guard:migration-numbers` PASS.

## 7. Disposable DB

`gochara-remainder-disposable` (localhost:55434) used for 1085/1086 verification; torn down at closure (§11). §7.A's rehearsal used a fresh `gochara-wp10-disposable` on the same port, torn down after the battery. At final close (2026-09-24, §12.12) both remaining disposable containers — `gochara-wp6-disposable` (55433, started by the parallel L3 session) and `gochara-wp10-disposable` — were torn down (`docker rm -fv`); `docker ps -a` confirms no disposable containers or volumes remain.

## 8. Artifact list (this branch vs `origin/main`: 172 files, +33277/−3204)

Key artifacts: `gochara_wp0_7/` reports (WP0–WP9 incl. WP8 batteries, WP6 ledger, WP4 comparison), `wp7_packets/` packet + REVIEW_REQUEST notes, `platform/migrations/1080–1086`, writer/service changes under `platform/python-sidecar` (gochara_v3, gochara_kernel, ka_vedha/moorti overlays, ga_strength_writer, GocharaTransitService), serving-layer changes (cockpit clear-ops, retrieval registry, reading checklist), `CHART_FACTS_SCHEMA.json` (new category), `GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` v2.2, `ESCALATIONS.md` E-007 addendum/E-009, KALA value artifacts, this report.
