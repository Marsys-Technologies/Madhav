---
artifact: SUVARNA_REVIEW_PASS1_DISPOSITION
canonical_id: SUVARNA_REVIEW_PASS1_DISPOSITION
version: "1.0"
status: "DONE — the disposition of every review-pass-1 finding in the v1.3 plan set"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
inputs:
  - briefs/suvarna/reviews/REVIEW_PASS1_SUBSTANCE_v1_0.md (30 findings, prefix S)
  - briefs/suvarna/reviews/REVIEW_PASS1_CONSISTENCY_v1_0.md (44 findings, prefix C)
  - briefs/suvarna/reviews/FABLE_REVIEW_D1_D5_v1_0.md and decisions D1–D6 ($SUVARNA_HOME/run/DECISIONS.jsonl)
changelog:
  - "1.0 (2026-09-29): first disposition, with plan set v1.3."
---

# Review pass 1 — disposition

**Dispositions.** FIXED: changed in the v1.3 set now. ALREADY FIXED: fixed by code that had already landed
(commit `db1b8d2c1` and the D6 commits: the decisions log outside git behind `python -m suvarna_tracker.decide`, native
gates reading it, `delegated` not done, the Monitor's `credential_readonly`, `census_lock`, detectors reading committed
refs, the `elevated (proxy)` label, cycles as errors, every execution item waiting for FI-7). SUPERSEDED: a decision
changed the premise. DEFERRED→item: to the named tracker item.

**Scope of this revision.** The documents revised are the plan (v1.3, new file), charter (v1.3), execution
architecture (v1.3), L3 focus families (v1.2), `plan_model.json`, and the document map (v1.1). Role files, start
prompts, the runbook and the review package were not edited here; every change they need is deferred to **L.12**, a
launch item that FI-7 (N-1) and L.9 (the independent review) wait for. Findings that touch the family prompts are also
relayed at once to the family sessions as a report (**FI-8**), because those sessions are already running.

**Counts.**

| | FIXED | ALREADY FIXED | SUPERSEDED | DEFERRED | Total |
|---|---|---|---|---|---|
| Substance (S) | 24 | 5 | 0 | 1 | 30 |
| Consistency (C) | 29 | 3 | 1 | 11 | 44 |
| **Total** | **53** | **8** | **1** | **12** | **74** |

Each finding is counted once, by the disposition of its substantive risk. 13 of them (S2, S3, S9, S17, S24, S26, S27,
C15, C18, C20, C22, C24, C37) also leave a role-file or prompt wording remainder, carried by L.12.

## Substance (REVIEW_PASS1_SUBSTANCE_v1_0.md)

| source# | severity | disposition | where | note |
|---|---|---|---|---|
| S1 | BLOCKER | FIXED | plan §3.7, §4.2 #13, §5.1 E7, §6.4; charter G13, R10, P1, P2, §6.4; arch §2.2, §8; plan_model E7.1–E7.3, E5.3, E3.7 | D1: dispatch through `POST /api/cockpit/runs` with a dispatch-only 'build' grant; deployed SHA from the job image tag via an authenticated preflight, not `/api/health`; L0 native-dispatched |
| S2 | BLOCKER | ALREADY FIXED | code `decisions.py`/`decide.py`; docs aligned: charter §2, §7.5, §11; arch §2.1, §11.1, §12.10, §12.12; plan §8 | authoritative log in `$SUVARNA_HOME/run/`, committed copies mirrors; hq takes plan revisions by merge, not ff-only; runbook §2.6 and ROLE_STEWARD wording → L.12 |
| S3 | BLOCKER | FIXED | plan §4.2 (#5 and the R244 note); plan_model E4.2 (`register_rows_state`), E1.6, B.U | path (a): J1 takes the merged fix with R244 closed or deferred with withholding; the live proof in its wave; R246 waits for the merged fix; Engine prompt wording → L.12 |
| S4 | BLOCKER | FIXED | plan §1.2, §5.3; arch §6.4; families §7; charter R8; plan_model B.FG, B.FS, B.FK, B.FR.L3–L5, `levels_elevated` `exclude` | D2: family rebuild (orchestrator-run only) is the Build exercise, Suvarṇa's re-measure certifies; families excluded from wave completion |
| S5 | BLOCKER | FIXED | plan §2.1, §5.1 E6; charter P5, G9; plan_model E6.0–E6.5, J1.6 | D3: generic detectors, registry applicability, rollup; per-asset semantic detectors in Tracks A/I; "a reviewer's opinion is not a detector" |
| S6 | BLOCKER | FIXED | plan §5.0b (L.11), §5.4 step 1; charter G16 (proposed); plan_model L.11, J1.0 (N-24) | track briefs listed as N-1 prerequisites (not written here); asset-brief approver named; I/B brief before J1 |
| S7 | MAJOR | FIXED | plan §1.1, §5.1 E6.3; arch §6.1, §11.6; plan_model E6.3 | exact ELEVATED, level map snapshot at J1, family exclusion; proxy label and cycle error already landed |
| S8 | MAJOR | ALREADY FIXED | code `state.py` (`decision_log_status`, `ALLOWED_DECISION_WRITERS`, conflicts) | `emit` still accepts any actor for events, but events no longer decide a gate |
| S9 | MAJOR | FIXED | charter §2, R1, §6.6, §7.5; plan §5.3, §8; families §6; plan_model F3.LOCK | F-3 needs a `decided` line recorded by Strategic Suvarṇa; family prompt wording → L.12, relayed now (FI-8) |
| S10 | MAJOR | FIXED | plan §5.3; arch §6.4, §12.9; charter R8 (hand-back); plan_model F3.LOCK → B.W2, B.FS ← B.W2; decisions HB-G/S/K | F-3 steered to a foreign-key change (D2); §12.9 now means the L2 writers only |
| S11 | MAJOR | FIXED | plan §5.2; plan_model A.L0i–A.L5i, A.L0–A.L5, A.L0r–A.L5r, A.H | the harvest waits only for census + instance; briefs provisional, revalidated after J1; L3 family evaluation off the J1 path |
| S12 | MAJOR | FIXED | plan §5.4 step 4, §6.6; arch §6.2; charter §6.4; plan_model B.W0M–B.W5M (`wave_deployed`) | one native-merged PR per wave group; latency modelled; writer-file hashes re-checked at dispatch |
| S13 | MAJOR | FIXED | plan §1.1, §5.1 E5.1/E5.5, §5.4 step 8, §7; arch §6.2.6, §12.16; plan_model E5.5 | records carry job image tag, writer hashes, upstream cert ids, fingerprint; families are unbound, so the fingerprint and E5.5 are the tripwires instead of a notification duty |
| S14 | MAJOR | FIXED | plan §1.2; arch §6.5 | D4: full-layer rebuild = `scope=layer, clear_before=false`; L0 proof by fingerprint; L2 cascade caveat |
| S15 | MAJOR | FIXED | charter §6.7; plan §6.4b; arch §6.5; plan_model B.N12 | D4: verified dump, measured impact, post-wave diff, surgical revert; N-12 before the first L0 wave |
| S16 | MAJOR | ALREADY FIXED | code `monitor.py` `check_credential_readonly`; plan §3.8; plan_model L.10 | D6 apply still pending; the check blocks until then, correctly |
| S17 | MAJOR | ALREADY FIXED | code detectors (`NIKASHA_REF`, `git show`); arch §12.2 (Track E lane bases), §12.12 (hq lock, L.13) | Engine prompt "Where" column → L.12 |
| S18 | MAJOR | FIXED | plan §5.1 E4; arch §12.7; plan_model E4.3 | named cut, ledgers last, md5 and line count equal, one-step re-point; recorded as evidence at the cut (a standing equality detector would go false as folds resume) |
| S19 | MAJOR | FIXED | plan §6.7; arch §5.1, §5.5, §10; charter G15, P13, §10; plan_model L.14, L.14d, L.15 | D5: `/loop` interim to G2; durable supervised headless pass loop; billing N-23 |
| S20 | MAJOR | FIXED | plan §3.5, §4.2 (one checklist); plan_model J1.6, E1.7 (`scorecard_pass`), E1.8, E2.2, J1.R, J1.1a–J1.5 | R24 → E1.8 (R40, R41 already closed); R71 → E2.2 via the reopen; "all rows closed or deferred" replaced: layer rows block layer close, not J1 |
| S21 | MAJOR | FIXED | plan §1.1(3), §1.4; charter P6; plan_model E6.2, E6.4 | D3: non-gate rows re-keyed `kind: info`, never block ELEVATED; coded rollup |
| S22 | MAJOR | FIXED | plan §5.2; families §5, §7; plan_model A.L3r, FI-8 | families record their template revision; post-J1 mapping in A.L3r |
| S23 | MAJOR | FIXED | families §5 (rewritten), §6; plan_model N-17, F0.2 | regime in force under N-17 described; families may change production while waves run |
| S24 | MAJOR | ALREADY FIXED | code `census_lock.py`; plan §6.5; arch §3.3, §12.13, §12.15 | family sessions told via FI-8; family prompt wording → L.12 |
| S25 | MINOR | FIXED | plan §5.1, §6.6 | Track E 190–325 h (E5, E6, E7 included); E3 raised; native/deploy latency separate; order-of-magnitude for briefs and I/B |
| S26 | MINOR | FIXED | plan §5.0b; arch §7, §11.6; plan_model N-20 | Secret-Manager wording removed; role-file references → L.12 |
| S27 | MINOR | FIXED | charter §10; arch §3.1, §5.4, §11.3, §12.5 | Conductor owns agent stalls; Monitor owns the Conductor watchdog; placeholder on the lane branch, never `main`; role files → L.12 |
| S28 | MINOR | DEFERRED→L.12 | start prompts §0 | explicit `may_touch` / `must_not_touch` globs in each start prompt |
| S29 | MINOR | FIXED | arch §12.14 | provisional censuses checked by script; Opus review only for certifying censuses |
| S30 | MINOR | FIXED | plan_model E3.2 (`prs_merged`, pinned by L.11), E3.3 (`migrations_applied`), E4.1 (`main_has_files`), E4.1c (CI); arch §11.7 | new detector types built by L.13 |

## Consistency (REVIEW_PASS1_CONSISTENCY_v1_0.md)

| source# | severity | disposition | where | note |
|---|---|---|---|---|
| C1 | BLOCKER | DEFERRED→L.12 | family prompts §2.2/§3.2 | the correct command is in arch §12.15 and relayed now (FI-8) |
| C2 | BLOCKER | ALREADY FIXED | plan_model (`db1b8d2c1`) | E3.2, E4.1, E4.2, E5.1–E5.4 depend on FI-7; kept in v1.3 |
| C3 | BLOCKER | FIXED | plan_model J1.6 (+E3.6, E1.8, E2.2, J1.R); plan §4.2 | R71 assigned to E2.2 (it closes through the reopen), not E1 |
| C4 | MAJOR | FIXED | plan §6.6 | §5.1 and §6.6 now agree (190–325 h) |
| C5 | MAJOR | FIXED | plan §5.0b, §8 N-19, changelog 1.3 | the 1.2 changelog line is corrected by a note, not edited |
| C6 | MAJOR | FIXED | plan §5.0b | L.3, L.4 done |
| C7 | MAJOR | FIXED | plan §5.0; map §5 | PR #2751 merged (FI-2); CURRENT_STATE recorded (FI-5) |
| C8 | MAJOR | FIXED | plan §0.1, §7 | N-2 decided |
| C9 | MAJOR | FIXED | map v1.1 §1, §3, §8, changelog | tracker now 198 tests |
| C10 | MAJOR | DEFERRED→L.12 | `SUVARNA_REVIEW_PACKAGE_v1_0.md`, review bundle | L.9 waits for L.12 |
| C11 | MAJOR | FIXED | families §5, §6 | status column from the log |
| C12 | MAJOR | FIXED | arch §11.6 | |
| C13 | MAJOR | FIXED | arch §7 intro, §7.2 | |
| C14 | MAJOR | FIXED | arch §2.3 | |
| C15 | MAJOR | FIXED | charter §10; arch §3.1, §5.4 | ROLE_CONDUCTOR, ROLE_MONITOR → L.12 |
| C16 | MAJOR | DEFERRED→L.12 | ROLE_SCRIBE, ROLE_BUILD_OPERATOR, ROLE_ARCHITECT, ROLE_MONITOR, ROLE_STEWARD | cite arch §12.x and E5.x |
| C17 | MAJOR | DEFERRED→L.12 | ROLE_STEWARD Outputs | arch §12.11 (digest on hq) unchanged |
| C18 | MAJOR | FIXED | arch §12.6 | one path: `briefs/suvarna/reviews/<qid>_REVIEW_<n>.md`, committed on the lane branch; roles → L.12 |
| C19 | MAJOR | DEFERRED→L.12 | ROLE_SCRIBE | arch §12.7 now names `FOLD_REQUEST.md` |
| C20 | MAJOR | FIXED | arch §12.2 | Track E lane bases; ROLE_COMMON §2 and the Engine prompt → L.12 |
| C21 | MAJOR | DEFERRED→L.12 | Engine prompt §1 E4 row | handoff path |
| C22 | MAJOR | FIXED | arch §2.3, §12.5; charter G4 | ROLE_BUILDER step 4 → L.12 |
| C23 | MAJOR | FIXED | plan §6.2; arch §3.3 | plan extended to the Steward's rulings and writer/ledger changes |
| C24 | MAJOR | ALREADY FIXED | code (log outside git); arch §12.10, §12.12 | the review's hq-writer proposal is superseded by the landed design; runbook §2.6 → L.12 |
| C25 | MAJOR | FIXED | plan_model N-20, N-17, F-0 | |
| C26 | MAJOR | FIXED | plan_model J1.1a–J1.5 (N-4.T1–T3, N-5.T1–T3, N-7.T4, N-7.L0) | |
| C27 | MAJOR | FIXED | plan_model B.W0M (+I.L3t), F3.LOCK → B.W2, `exclude: family_set` | D2 grain replaces "add I.L3 to B.W0" |
| C28 | MAJOR | FIXED | plan §1.1; plan_model E6.3 → J1.6 | exact ELEVATED before any certification; proxy label landed |
| C29 | MINOR | DEFERRED→L.12 | ROLE_COMMON header, changelog | |
| C30 | MINOR | FIXED | arch §1 principle 7 | |
| C31 | MINOR | FIXED | arch changelog 1.3 | |
| C32 | MINOR | FIXED | arch §1.1 row 5 | |
| C33 | MINOR | FIXED | arch §4.1 | |
| C34 | MINOR | FIXED | arch §8; charter §6.7 | a power warn fails a build's precondition |
| C35 | MINOR | FIXED | arch §7.1 | |
| C36 | MINOR | FIXED | charter §11 | |
| C37 | MINOR | ALREADY FIXED | `DECISIONS.jsonl` schema (`writer` field; every line names it) | ROLE_STEWARD field list → L.12 |
| C38 | MINOR | FIXED | plan §8 (second table); plan_model decisions | matching events no longer needed: the tracker reads the log |
| C39 | MINOR | SUPERSEDED | plan §4.2 #5 | by S3 path (a): J1 takes R244 closed or deferred with withholding; N-6 (fix now) still holds for the fix; prompt → L.12 |
| C40 | MINOR | DEFERRED→L.12 | Saṅgam prompt §1 | relayed now (FI-8) |
| C41 | MINOR | DEFERRED→L.12 | ROLE_ANALYST step 1 | exit codes and the evidence-folder rule are in arch §12.14, §12.15 |
| C42 | MINOR | DEFERRED→L.12 | ROLE_COMMON §2 | |
| C43 | MINOR | DEFERRED→L.12 | runbook §6 | arch §8 states the Monitor's actual behaviour (missing = block, too open = warn; read-only by privilege) |
| C44 | MINOR | FIXED | plan_model E4.1 (`main_has_files` incl. ledgers and register), E4.1c | |

## What L.12 must do (the deferred remainder, in one list)

1. **Family prompts** (Gochara, Saṅgam, Kṣetra): census command (C1; arch §12.15), Saṅgam migrations (C40), F-3 recorded
   by Strategic Suvarṇa (S9), census lock (S24), D2's orchestrator-run condition and the template revision (S22). The
   sessions are live: FI-8 relays the same as a report first.
2. **Engine and Exec start prompts:** `may_touch` / `must_not_touch` (S28); lane bases and "Where" column (S17, C20);
   handoff path (C21); R244 wording (S3, C39); v1.3 references; E5–E7 and the J1 checklist.
3. **Role files:** ROLE_COMMON header, §2 lane path and bases (C29, C42, C20); ROLE_SCRIBE (C16, C19); ROLE_BUILD_OPERATOR
   (C16; D1 dispatch, §6 commands, L0 parking); ROLE_ARCHITECT (C16); ROLE_MONITOR (C15, C16; watchdog); ROLE_CONDUCTOR
   (C15; stateless passes, D5); ROLE_STEWARD (C16, C17, C37; `decide` CLI; S2); ROLE_GATE_REVIEWER (C18); ROLE_BUILDER
   (C22); ROLE_ANALYST (C41; census lock).
4. **Runbook:** §2.6 merge instead of ff-only (S2, C24); §6 Monitor rows (C43); D5 runtime steps; decisions via `decide`.
5. **Review package and bundle** for the v1.3 set (C10), before L.9.
