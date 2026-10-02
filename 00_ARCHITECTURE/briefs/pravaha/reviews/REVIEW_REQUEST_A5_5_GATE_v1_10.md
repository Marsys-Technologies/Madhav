---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.10"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.9. ROUND-9 REQUEST, scoped to the steward's milestone: the ALL-NULL '5.0' candidate. FILL BEFORE DISPATCH: <<WRITER_HEAD>> and <<BRIEF_VERSION>> (Stream A's branch pravaha/a53-am5-inventory); everything else is final as of this packet."
---

# A5.5 gate — round-9 request: the ALL-NULL `'5.0'` candidate (2026-10-02)

## 0. The milestone (steward decision on scope)
Round 8 returned REJECT; accepted as contracts: the P4 score ruling, objective ≠ score, the smooth-piece tie ruling, `UNVERIFIED_DYNAMIC` never satisfying a gate, migration source 1204/1206/1232, the codec, amendment 11. **The next milestone is Codex's steps (a), (b), (c) with every numeric result NULL by design.** Numerical activation — dynamic solving, qualified vedha, P1 scoring (R8-6 solver guarantee, R8-7 integration, R8-9) — is **deferred as explicitly DISABLED capabilities with named reasons (§C), not half-built.** Blockers for the milestone: **R8-1, R8-2, R8-3, R8-4, R8-5, R8-10.** Specs/oracles v1.4 are frozen and untouched; text lives in the amendments draft **v0.20** (`campaign/pravaha`).

## §A. The three steps, their blockers and the evidence for each
### (a) Protected window 1204 → 1206 → 1232 → 1233 — R8-10
| exhibit | ref | state |
|---|---|---|
| **Operational rehearsal plan** (executable checklist; M1–M4 mechanical for Stream C, O1–O7 operator) | `runbooks/PROTECTED_WINDOW_REHEARSAL_PLAN_v1_0.md`, `runbooks/rehearsal/run_window_rehearsal.sh`, `prod_ledger_2026-10-02.txt`, `EXPECTED_WINDOW_SHA256.txt` | written; **run once by its author on PostgreSQL 15.17** (production is 15.18) |
| the real `migrate.ts --only <deploy list>` against a production-shaped ledger | M1 S3a | **REFUSED** by unapplied predecessor `1230_ka_gochara_registry_revert_1091_pin.sql` — the **only** unselected, unapplied file with a number ≤ 1233 in the 2026-10-02 production ledger. The window works only after the routine deploy applies 1230 (the live fixture's intervening 1216 is not the proof; production already holds 1216/1220/1225/1231) |
| per-file failure recovery | M1 S3c | 1204/1206/1232 stay committed; 1233 not recorded, no partial columns; the same invocation then applies only 1233 — **reproduced** |
| ownership / default privileges | M1 S4 | schema `public` owned by `data_plane_schema_owner`, objects owned by `amjis_app`, CREATE only inside the window, **0** `ka_gochara_*` functions with PUBLIC EXECUTE — **reproduced** |
| role matrix | M1 S4 + live suites | builder refused the seal function/table/seal-side helpers/1232's two helpers; sealer refused content writes; proposed verifier set tested — 29 asserts pass |
| live suites 1206 + 1232 + 1233, serially, PG15 | `tests/integration/…` | **55 tests pass** |
| volume / contention / seal timing | `tests/integration/gochara_b6_rehearsal_volume.db.test.ts` (opt-in) | 26 classes: seal 64 ms at 2 340 obligations / 7 020 intervals, 453 ms at 7 488 / 59 904; a builder write to another generation waits for the in-flight seal. Synthetic, laptop — **replace with Kimi's run on real counts** |
| **FINDINGS (open)** | plan §M4 | (1) the builder can write independent-verification rows (1206 §7) — PC-4 requires removal; (2) **the eval-window write path had no grants** (1216 defers it; 1220 covers only contact/record flow) — **now derived: migration 1234, PR #2920 (HOLD, grants only, routine)**: 2 tables + 3 functions, each individually necessary, 7/7 mutations caught; **ledger consequence: 1230 and 1234 must be applied by the routine deploy before the window lists 1240**; (3) sealer and verifier principals are not provisioned; (4) 1230 must be applied first |
| outstanding | plan O1–O7 + **ND-ROLES** | operator receipts: deployment ref, provisioning, dispatch, post-window checks, actual-role seal/replay evidence; **ND-ROLES (`decisions/ND_ROLES_DECISION_PACKET_v1_0.md`) is a blocker of (c)**: the verifier and sealer principals do not exist in usable form and the builder can write verification rows |

### (b) Bind the `1.1.0` registry versions — R8-2 (+ binding/read-back evidence)
| exhibit | ref | state |
|---|---|---|
| **AM-22 — per-class version selection and supersession** (Codex's operative sentence; two sets, composite keys, independent derivation, original selection for replay, required tests) | draft v0.20 §AM-22 | text ruled; **implementation is Stream A's** |
| the ONE flat codec (closed `activity_kernel` key schema; numeric orb only with `ratified` + `orb_decision_ref`) | #2897 `55fec69a1` | accepted by round 8 (writer's separate codec to be deleted — Stream A) |
| exact nakṣatra/sign membership; `aggregate_paths` qualification | #2897 / #2913 (merged) | done |
| vedha registry row + pairs + oracle + **callback contract** | #2901 `ab1afc50a` (contains #2897, #2907, main) | R8-7 code done: unique keys over **all** 42 rows (a duplicate Rāhu key is refused); `vedha_callback_result` / `check_callback_result` — factor reference in, validated reference out, structured results, segment boundaries, scopes |
| outstanding | Stream A | per-class selection in `inventory.py` / verifier; actual-schema SQL read-back evidence; historical-version evidence |

### (c) First `'5.0'` candidate build, all-NULL — R8-1 … R8-5 + R8-10
| blocker | owner | Stream B's part | state |
|---|---|---|---|
| **R8-1** consumed-input identity (the `l0` selection `rule_type='vedha'` selects nothing against the 42 `favourable` rows; the fixture hides it; replay/independent input check incomplete) | A | the 42-row authority fixture and `VedhaPairs.content_digest` (#2901) are the exhibit; AM-16 text/model v3 frozen literals | open (A) |
| **R8-2** per-class supersession | A | AM-22 text | open (A) |
| **R8-3** P1 support and anchoring | A + 1233 | **migration 1233 — PR #2919 `3994a57dc` (HOLD)**: `period_anchor_lord` / `period_anchor_level` on the relationship record; three named CHECKs (pair / vocabulary / set exactly for `P1`); gate refuses over existing P1 rows or on replay; no trigger/function/grant; live suite 8 + static 4, 9/9 mutations caught. **AM-21 carries Codex's exact sentence**; **AM-20 = LAGNA** (clean RULED text; every "candidate / unruled / keep unminted" leftover removed) | migration + text done; writer anchor-aware implementation open (A) |
| **R8-4** comprehensive, durable, gate-enforced verification | A | the vedha oracle (#2901) as an independent source; SI v1.3 unknown-competitor model | open (A) |
| **R8-5** scope disclosure ≠ completeness | A | — | open (A); the serving call site is wired at no server path |
| **R8-10** operational receipts | steward / Stream C | plan + script + harness (above) | open (operator O1–O7) |
| the **eval-window grants** (M4.1) | B derived, A confirmed the set | **migration 1234 — PR #2920 `pravaha/b6-1234-eval-window-builder-grants` (HOLD)**: `SELECT/INSERT/DELETE` window, `SELECT/INSERT` membership (cascade removal), `EXECUTE` text_array_ok / facts_horizon / membership_violation; live 7 + static 4 | derived; routine application before the window (ledger precondition) |

## §B. What changed since v1.9 on Stream B's side
**AM-20** rewritten as clean RULED text (lagna). **AM-21** (operative sentence, anchor part 2, Moon-tier exclusion follows the transiting body). **AM-22** per-class supersession. **AM-23** #2914 is a prerequisite of qualified P1 scoring only; the retrograde clause is a named limitation. **AM-18** items 8–9 (unique keys over all rows; the version-bound structured callback). **SI addendum v1.3** (bounds over **all** admissible assignments incl. the zero boundary `[60,80]`, average ranks, tolerance ties and tie-group **bridges** `0,0,1.5e-9,1.5e-9,1,2,3`+unknown → 3/8, 2/8, **5/8 void**; two-stage freeze; reference model `measurement/unknown_competitor_bounds_model.py` reproducing Codex's cases) — v1.2 marked superseded. `P1_FRAME_ANSWER` v1.2, `AM19` decision packet v1.1 (the served ladder), `NATIVE_OPEN_DECISIONS` v1.6.

## §C. Capabilities explicitly DISABLED in this milestone, each with a named reason
| capability | reason it is disabled | what would enable it |
|---|---|---|
| **dynamic numerical solving of windows** (peak/score/evidence as functions of t) | R8-6: no solver with a stated global-maximum guarantee; unknown portions must propagate; non-P4 score restricted to the for-channel; tolerance blurs smooth maxima | AM-17 implementation per the ruling, exact breakpoints, a solver with a guarantee per function class, dynamic verification |
| **qualified vedha** | R8-7: writer `VEDHA_SOURCE=None`; callback contract specified (AM-18 item 9) but not integrated | writer integration + persistence/serving of the Moon-obstruction scope + oracle over bound residence data |
| **P1 scoring** | R8-9 + AM-19: value mappings undecided; #2914 wrappers not consumed by the governed path; anchored records not minted | the native's AM-19 rulings; writer consumption; AM-21/1233 in the writer |
| **orb values** | ND-ORB-ADMISSION / ND-ORB-SCALE open | native rulings; new factor/path versions |
| **P5** | held (donor rows pending; forms P5c/P5d gated) | unchanged |
| **retrograde clause (Phaladīpikā XX.37)** | no factor; adopting it changes admitted readings | an explicit admission amendment |
| **P1 PD level** | no verse in XX.34–39 (spec extension) | a named source, or testimony |
| **ranking / timing endpoints** | no candidate adapter/scorer; no Stage-1/Stage-2 freeze | SI v1.3 §5 two-stage freeze + adapter |
| **completeness claims in serving** | R8-5: constructor unwired; scope ≠ completeness | derive completeness from valid coverage/inventory/verification state; wire every positive and no-window path |
An all-NULL candidate is evidence about materialization, admission accounting, bounded search scope and qualification handling — **not** about predictive success; it claims no peak, strength, rank, timing, P1 scoring, orb doctrine or production readiness.

## §D. Standing limits (unchanged)
Database cannot judge the *right* inventory; sealer/verifier unprovisioned in production; the DB-Integration CI job is advisory (`postgres:16`; production is 15.18 — rehearse on 15); seal timings measured only on synthetic volume; ND-ORB-ADMISSION and ND-ORB-SCALE open; ND-P1-FRAME (label only), AM-19, ND-COMBUSTION, ND-VIPAREETA, ND-NODE-VEDHA open; the AM-16 model must be reproduced by the writer's `assemble_vector`; `'5.0'`/`'4.1'` scorer not run; SI mapping pre-registered after seeing '3.0'. Open list: BPHS human re-read; L1 Sun-rūpa; Mercury/Moon mūlatrikoṇa one-degree, three combustion copies, L1 silent defaults (with Suvarṇa); AM-12 / AM-19 candidates; `varga_position` unclassified; three further float-floor nakṣatra copies outside Stream B (`legacy_semantics.py:561`, `gochara_intensity/enrichment.py:136`, `step06b_windows_projection.py:910`).

## §E. Stream A — writer head (to be filled at dispatch)
Writer: `pravaha/a53-am5-inventory` @ **<<WRITER_HEAD>>**, brief **<<BRIEF_VERSION>>**. The round-8 writer head was `f4767b0e6` (brief v1.19).

## §F. Judge-list
1. For each of (a), (b), (c): is the blocker list complete, and does the evidence in §A close, or correctly leave open, each?
2. §C: is each disabled capability explicitly disabled (never partly active), and does the all-NULL candidate stay honest without it?
3. #2919 (1233) and the rehearsal plan/script/harness as new exhibits; #2901's R8-7 change; AM-20…AM-23 and SI v1.3 as text.
Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per step (a)/(b)/(c) and per item, with numbered findings.
