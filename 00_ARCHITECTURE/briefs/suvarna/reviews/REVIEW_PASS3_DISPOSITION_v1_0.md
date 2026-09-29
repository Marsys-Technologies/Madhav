---
artifact: SUVARNA_REVIEW_PASS3_DISPOSITION
canonical_id: SUVARNA_REVIEW_PASS3_DISPOSITION
version: "1.0"
status: "DONE — the disposition of every review-pass-3 finding; documents and plan model folded in place (plan v1.4.1)"
produced_on: 2026-09-30
produced_in: session "Strategic Suvarṇa" (document and plan-model side; the tracker code is fixed in parallel by the code agent)
inputs:
  - "briefs/suvarna/reviews/REVIEW_PASS3_v1_0.md (A: 6 pass-2 fixes not done or partial, 3 cosmetic; B: B1–B10, B11 folded into B10; 5 near-blockers)"
  - "briefs/suvarna/reviews/REVIEW_PASS2_DISPOSITION_v1_0.md (CODE-1…CODE-21)"
  - "origin/main .claude/settings.json; origin/campaign/nikasha-test register; _migrations_applied and pg_constraint (read-only, as suvarna_reader)"
changelog:
  - "1.0 (2026-09-30): first disposition, with plan v1.4.1 (edited in place; no new plan file)."
---

# Review pass 3 — disposition

**Dispositions.** FIXED: the documents and `plan_model.json` now carry the fix, and the code already supports it (or
needs no code). CODE: the remaining risk sits in tracker code under `platform/scripts/governance/suvarna_tracker/`;
the spec is in §3 for the code agent (not edited here), and the documents were aligned to it in this pass. NATIVE: needs
a ruling, prepared in plan §8. Each finding is counted once, by where its substantive risk now sits. Section A rows that
restate a B blocker point to it and are not counted twice.

**Scope of this revision.** Edited in place, patch versions: plan v1.4 → **v1.4.1** (no new plan file), charter
v1.4.1, architecture v1.4.1, runbook v1.2.1, Track E and Track A briefs v1.1.1, `runtime/INTERIM_RUNTIME_v1_0.md`
v1.1.1, both start prompts v1.2.1, five role files v1.2.1 (analyst, builder, build operator, common, monitor), the three
family prompts **v1.3** and the correction notice **v1.2** (a new relay round, so FI-8's acknowledgement names them),
the document map v1.2.1, REVIEW_PASS2_DISPOSITION v1.1 (pass-3 follow-up), and `plan_model.json`. Nothing committed; no
code edited; no database write; no event or decision emitted.

**Measured for this pass (2026-09-30, read-only).**
- **The migration deny (B4), verified.** `git show origin/main:.claude/settings.json` (last changed by `ee9b6c7e8`, L3
  Kāla Phase 1.4, #2718) denies `Edit(platform/migrations/…)` for `[0-9][0-9][0-9]_*`, `10[0-6][0-9]_*`, `1070_*`,
  `11[2-9][0-9]_*`, `1[2-9][0-9][0-9]_*`, `ws2_*`, and `Edit(.claude/settings.json)` itself. Only 1071–1119 is
  editable. The deny does **not** cover `platform/supabase/migrations/`, which `platform/scripts/migrate.ts` also applies
  (its header: "Reads platform/migrations/*.sql and platform/supabase/migrations/*.sql"); the build engine's 1094–1096
  sit in that folder today on `campaign/nirmana-engine`.
- **1200–1299 is free.** No migration numbered 1200 or above in either folder on `origin/main` or on any of the 2,220
  local and remote refs; none in the 22 open PRs (`gh pr list --state open --json files`); `_migrations_applied`: 0 of
  883 rows match `^1[2-9][0-9]{2}_`, the highest applied is `1150_wp10_ka_gochara_conjunct_e_utc_date_compare.sql` (L3
  Gochara, PR #2731, still open), and 1094–1096 are not applied. Open PRs use 1033–1119 and 1150 only.
- **R34, R36** at `origin/campaign/nikasha-test`: both BLOCKS_FREEZE, `CLOSED_ON_BRANCH` (R34: engine A1 `8edba0533`,
  migration 1094, pending merge/migration/deploy/runtime proof, with an OPEN residual on the legacy `_telemetry.py`
  path; R36: engine A3 `551d5ecad`, pending harness and deployed replay).
- **Keys into `bodha_msr_signals`:** exactly eight, all `confdeltype = 'c'`, from the seven known tables; no RESTRICT
  or NO ACTION key exists today.
- **FI-8** has no acknowledgement yet in `run/EVENTS.jsonl`, so re-versioning the relay costs no re-acknowledgement.

## 1 · Counts

| | FIXED | CODE | NATIVE | Total |
|---|---|---|---|---|
| Blockers B1–B10 (B11 in B10) | 3 (B3, B8, B9) | 6 (B1, B2, B5, B6, B7, B10) | 1 (B4) | 10 |
| Section A not counted elsewhere | — | 4 (S14 hold guard; CODE-8, CODE-17, CODE-18 cosmetic) | — | 4 |
| Near-blockers | 1 (E6.3t) | 4 (F3.FK target, `levels_elevated` membership, `wave_deployed` head ref, `main_protected` bypass) | — | 5 |
| **Total** | **4** | **14** | **1** | **19** (CODE-35 is a follow-on spec, not a finding) |

## 2 · Every finding

| # | Class | Disposition | Where (documents, plan model) | Note |
|---|---|---|---|---|
| A.1 | S1, CODE-12, CODE-20, CODE-11 | → B1; CODE-11's bypass part → near-blocker `main_protected` | — | — |
| A.2 | S2, CODE-14 | → B6 | — | — |
| A.3 | C3, CODE-15 | → B2 | — | — |
| A.4 | S10(b), CODE-6 | → B7 | — | — |
| A.5 | S14 hold-guard path | **CODE** (CODE-25) | arch §2.4, §5.5; runbook §2 step 9; `INTERIM_RUNTIME` §6; charter §13 | The hook runs from `/Users/Dev/suvarna/hq/platform/scripts/governance` and **fails closed for dispatches**: a hook that cannot run or cannot read its payload refuses `Agent` and dispatch-like Bash. Documents now say so; the template command is code. |
| A.6 | C22/S1, CODE-21 | → B5 (push) and B10 (allow forms) | — | — |
| A.c1 | CODE-8 docstring | **CODE** (CODE-34) | — | Cosmetic. |
| A.c2 | CODE-17 `NIKASHA_ROOT` default; supervisor started before CODE-17 | **CODE** (CODE-34) | — | The running supervisor is restarted from hq by L.17 (unchanged launch item). |
| A.c3 | CODE-18 `lane_launch` emits `item: <qid>` | **CODE** (CODE-34) | — | Emit `--item <plan_item> --step <qid>` (arch §12.1). |
| **B1** | (1)(4) isolation never `ok` | **CODE** (CODE-22) | plan-model L.16a title; arch §2.4, §8; charter §13; runbook §2 steps 2a, 6, 13 and a WARN row in §6; ROLE_MONITOR; ROLE_COMMON §12; both start prompts step 4; `INTERIM_RUNTIME` §5 | Documents now: `isolation` reads **warn until N-25 is decided, ok after**; before N-25 the Monitor exits 0 or 1, and 1 only from `isolation`; no launch step requires every check ok before N-25; step 2a is done when `isolation` reads ok after N-25. L.16a already waits for L.16d. |
| **B2** | (3) `builder_scope` ok before provisioning | **CODE** (CODE-23) | arch §8; runbook §2 step 6; ROLE_MONITOR; ROLE_COMMON §4; Engine start prompt | Documents now: `builder_scope` reads **warn until E7.2 writes `run/builder_identity.json`**, so E7.3 (and J1 row 13) cannot read done early. E7.2 stays done-by-event: `evidence_recent` reads under `evidence/` with a maximum age, so a one-time provisioning record would age back into pending; the check that could read false is E7.3's, now honest. |
| **B3** | (1) R34, R36 unowned | **FIXED** | plan-model **E1.10** (`register_rows_state` R34, R36 ∈ CLOSED/DONE; after E3.2, E3.3, E3.7); J1.R `expect_rows` + R34, R36 and depends on E1.10; J1.6 depends on E1.10; plan §3.4, §4.2 rows 6 and **6a**, §5.1 E1, §7, Appendix A; Track E §1, §5 (packet E1.10-analysis-001), §9 critical path; Engine start prompt lane table | Runtime proof is read-only (build history) or on the E5.6 scratch database, never a Suvarṇa production build before J1. R34's residual (the legacy `ga_writers/_telemetry.py` path, 8 `ga_*` sites) is split into its own non-freeze row by the E1.10 fold (a register change on `campaign/nikasha-test`, the Engine's). |
| **B4** | (1)(4) every Suvarṇa migration denied | **NATIVE** (N-27) | plan-model decision **N-27**, items **E0.1d** (decision) and **E0.1** (the amendment PR merged, `prs_merged`, `prs: []` pinned by Strategic Suvarṇa); E3.2n (N-26) depends on E0.1d; E3.2, E3.3 and E7.1 depend on E0.1; N-26's recommendation renumbers into the range; plan §5.1 E3/E7, §7, §8, §11, Appendix A, §4.2 row 9; arch §12.5 (rewritten with the evidence); ROLE_BUILDER step 4 and stop conditions; runbook §7; Track E §2, §3.2, §3.3, §8, §9; Engine start prompt | Recommendation below (§4). The amendment's author is the native or the L3 Kāla owner: `.claude/settings.json` is itself denied to every agent. |
| **B5** | (2) force-push via `+`, push to `…:main` | **CODE** (CODE-26) | arch §2.4, §5.5; runbook §2 step 9; ROLE_COMMON §12 | Documents now: the swarm pushes only to `suvarna/*`; no `+` refspec, no `…:main`, no force. |
| **B6** | (2)(3) `suvarna_tracker.*` wildcard; `census_lock` wraps anything | **CODE** (CODE-27) | arch §2.4, §5.5, §12.13, §12.15; runbook §2 step 9, §3; plan §6.5; ROLE_COMMON §4, §12; ROLE_ANALYST step 1; Track A §3; Track E §5; both start prompts; the three family prompts v1.3 and their Corrections; correction notice v1.2; plan-model FI-8 title; plan §5.0 | Documents now show the census only as `python3 -m suvarna_tracker.census_run --layer <Lx> --out <absolute path>` (every `census_lock … -- bash -c '…'` form removed), and name `decide`, `decisions`, `runtime_settings` as not allowed to the swarm. |
| **B7** | (3) scorecard generator pin ignored | **CODE** (CODE-24) | arch §11.7 (`scorecard_pass` row) | The spec's `generator` is the pin; the scorecard's own `generator` must equal it. |
| **B8** | (3) R244 DEFERRED on its own say-so | **FIXED** | plan-model E4.2r: `deferred_withholding_entry: "bo_upaya-Idem.pattern"`, `deferred_withholding_path`, `deferred_pr: "suvarna/land/E4.2-build-001"`, `pinned_by`; plan §4.2 row 5; arch §11.7; Track E §4 (E4.2-build-001 row); Engine start prompt | The code already reads both keys (`d_register_rows_state`); `deferred_pr` is passed to `gh pr view`, which resolves a head branch as well as a number, so the head ref works today and fails closed (not checkable → not counted) until the PR exists. Before E4.3 the withholding file is read at `campaign/nikasha-test`; if absent there, DEFERRED does not count, which is the safe direction. |
| **B9** | (2) whole-level runs rebuild family assets | **FIXED** | arch §6.2 item 2; plan §5.4 step 6, §5.1 E5.3; Track E §7 E5.3 spec (dispatch set = level in `LEVEL_MAP.json` minus `family_set`, `--assets`, never `--level`, refuse on intersection or a missing file; tested with a family-holding fixture level); ROLE_BUILD_OPERATOR steps 1 and 3; charter G13; runbook §7; Engine start prompt | E5.3 is a Track E packet not yet written, so its spec is the fix; no code exists to change. |
| **B10** (+B11) | (4) allow-list vs documents | **CODE** (CODE-28) | arch §2.4, §5.5; runbook §2 step 9; ROLE_COMMON §12 | Documents keep the single-quoted reader form they already used everywhere and now state the exact allowed forms; the template must allow them (and `pg_dump`, governance scripts, `suvarna-build`). |
| NB.1 | F3.FK passes on a restricting key | **CODE** (CODE-29) | plan-model F3.FK: `target: "no_fk"` + `pinned_by` (`set_null` if F-3 so rules, same commit as the F-3 line); plan §5.3; arch §11.7 | Today's code checks `confdeltype = 'c'` only; with the target read, RESTRICT/NO ACTION read pending. |
| NB.2 | E6.3t done by event; E6.3 interface unpinned | **FIXED** | plan-model E6.3t: `main_has_files` on `asset_elevation_tracker.py` and `__tests__/test_e6_3_tracker_interface.py`; Track E §8 pins `elevated_assets(ref: str, repo: str) -> set[str]` (pure over `git show <ref>:<path>`, raises on bad input); plan §4.2 row 16, §5.1 E6.3/E6.3t | The tracker's call must match the pin: CODE-31. |
| NB.3 | `levels_elevated` membership from the live DAG | **CODE** (CODE-30) | plan-model B.W0–B.W5 specs gain `level_map: "00_ARCHITECTURE/control/LEVEL_MAP.json"`; arch §6.1, §11.7; plan §5.1 E6.3; Track E §8 pins the file's keys | Until the code reads `level_map` the key is ignored; the wave items still read unknown until E6.3t, so nothing reads done early. |
| NB.4 | `wave_deployed` trusts the PR number in LANDING.json | **CODE** (CODE-32) | — | Not in this pass's document scope. |
| NB.5 | `main_protected` ignores bypass actors | **CODE** (CODE-33) | — | L.16b's detector spec already names `bypass_only: native`. |

## 3 · CODE specs (for the code agent; not edited here)

Numbering continues REVIEW_PASS2_DISPOSITION §3.

| Code | Finding | Spec |
|---|---|---|
| CODE-22 | B1, A.1 | `monitor.check_isolation` per CODE-12, stat/hash only: before N-25 has a `decided` line → `warn` ("N-25 not decided"); after → the decided outcome's checks (expected user; dbenv files mode 600, and unreadable under the separate user; `.config/madhav-admin`, `.codex` unreadable and the decisions log not writable under the separate user; settings hashes equal `settings_baseline.json`; `runtime_settings --check` clean); all pass → `ok`, any miss → `block`. **A declined N-25 is not `ok` by itself:** the fallback hardening the plan requires either way (dbenv mode 600, settings hashes, `--check`) is measured (as observed in the working tree on 2026-09-30, the in-progress code returns `ok` on a decline without measuring; that part is still open). Replace `test_isolation_always_warns_never_ok_never_block`. |
| CODE-23 | B2, A.3 | `check_builder_scope`: `builder_identity.json` absent → `warn` ("E7.2 not provisioned"), never `ok`. |
| CODE-24 | B7, A.4 | `d_scorecard_pass`: require `data["generator"] == spec["generator"]`, else pending; hash the spec's path; test. |
| CODE-25 | S14, A.5 | Template hook: `PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance`; a wrapper that exits 2 for `Agent` and dispatch-like Bash when the module cannot import or the payload cannot be parsed (fail closed for dispatches); tests. |
| CODE-26 | B5, A.6 | Template: drop `Bash(git push *)` (and rely on no project-level broad allow); allow only `git push origin suvarna/*` forms; deny `Bash(*git push*+*)` and `Bash(*git push*:main*)`; the hold guard refuses any push whose destination is not `suvarna/*` (the Engine's fast-forward to `campaign/nikasha-test` is the one named exception, arch §12.7). |
| CODE-27 | B6, A.2 | Template: deny `Bash(python3 -m suvarna_tracker.decide*)`, `…decisions*`, `…runtime_settings*`; `census_lock` refuses any wrapped command that is not the `asset_census.py` form; new `suvarna_tracker.census_run --layer <Lx> --out <absolute path> [--wait S] [--emit] [--actor A]` (validates both, takes the lock, exit 75 when held, exit 2 on a refused argument, sources `pgenv.sh`, runs only the inspector); allow it in the template. (Present in the working tree on 2026-09-30; the documents use `--wait 900 --emit --actor <role>`.) With `decide` denied to the swarm, CODE-14's TTY confirmation is no longer the only line. |
| CODE-28 | B10, B11 | Template allows: `Bash(bash -c 'source ~/.config/suvarna/pgenv.sh && psql *)`, `…&& pg_dump *)`, `Bash(python3 platform/scripts/governance/*)`, `Bash(~/.config/suvarna/bin/suvarna-build *)`. |
| CODE-29 | NB.1 | `d_fk_no_cascade` reads `target`: `no_fk` → done iff no foreign key into the table; `set_null` → done iff every key has `confdeltype = 'n'`; any `c`, `r`, `a` → pending (listed); `target` missing → unknown. |
| CODE-30 | NB.3 | `d_levels_elevated` reads membership from `spec["level_map"]` on `origin/main` (key `levels`, Track E §8), pending while absent; never the live `dag_levels`. |
| CODE-31 | NB.2 | E6.3t: the tracker calls `elevated_assets(ref, repo)` (the pinned interface) with the resolved Nikaṣa ref and `cfg.nikasha_root`. |
| CODE-32 | NB.4 | `d_wave_deployed`: the LANDING.json PR's `headRefName` must start with `suvarna/land/<wave>`, else error. |
| CODE-33 | NB.5 | `d_main_protected`: read the ruleset's `bypass_actors`; done only if they are limited to the named actor. |
| CODE-34 | A.c1–c3 | CODE-8 docstring (E6.3, not E4.1); CODE-17 `NIKASHA_ROOT` default = the hq worktree; CODE-18 `lane_launch` emits `--item <plan_item> --step <qid>`. |
| CODE-35 | B6 (follow-on) | `census_run` hard-codes the checkout `/Users/Dev/madhav-nikasha`; arch §12.13 moves the census to the `suvarna/trunk` worktree once E4.1 lands the inspector on `main`. Make the checkout switch (a validated option or a rule keyed on E4.1), never a caller-supplied path outside the two. |

## 4 · NATIVE decision needed

**N-27 — a Suvarṇa migration range and the edit permission for it.**

- **Why.** Main's committed `.claude/settings.json` (L3 Kāla #2718) denies `Edit` on every `platform/migrations/` number
  except L3's reserved 1071–1119, for every session in the repository; a deny beats the `--settings` allow. Main is at
  1125 (and production at 1150), so E7.1's grant migration (day 1), N-26's renumbering, every Track I migration and F-3
  (if Suvarṇa lands it) are refused in every lane.
- **Recommendation.** Reserve **1200–1299** for Suvarṇa, recorded as a reservation row on `campaign-coordination`.
  Merge one small PR to `main`, agreed with the L3 Kāla owner and authored by the native or that owner (no agent may
  edit the file), replacing `Edit(platform/migrations/1[2-9][0-9][0-9]_*)` with
  `Edit(platform/migrations/1[3-9][0-9][0-9]_*)`: one line, which opens only 12xx. Then N-26 renumbers 1094–1096 into
  the range (next free numbers, one at a time), placed in `platform/migrations/`.
- **Evidence the range is free** (2026-09-30): "Measured for this pass" above.
- **Rule that goes with it.** Suvarṇa never writes a migration into `platform/supabase/migrations/` (uncovered by the
  deny) or by any other route around it (charter P13). The L3 Kāla owner may want the deny extended to that folder;
  that is theirs to decide.
- **Tracker.** E0.1d (N-27) → E0.1 (`prs_merged`, the PR number pinned by Strategic Suvarṇa the day it opens) → E3.2,
  E3.3, E7.1; E3.2n (N-26) waits for E0.1d.

Unchanged and still open: N-25, N-26 (now after N-27), F-3, N-14.R236, N-1 with G16.

## 5 · Left for Strategic Suvarṇa

- Commit this set on `strategy/suvarna-plan`, merge into hq and restart the tracker and Monitor from hq (L.17).
- Pin E0.1's PR number, and replace E4.2r's `deferred_pr` head ref with the PR number, the day each PR opens.
- Set F3.FK's `target` to `set_null` in the same commit as the F-3 `decided` line, if F-3 rules SET NULL.
- Relay FI-8 anew: the native pastes correction notice v1.2 (prompts v1.3) into each family session.
- Present N-27 with N-25 and N-26 as one batch.
