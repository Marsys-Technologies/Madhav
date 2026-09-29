---
artifact: SUVARNA_TRACK_E_BRIEF
canonical_id: SUVARNA_TRACK_E_BRIEF
version: "1.2"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-29
produced_in: "Strategic Suvarṇa"
session: "Nikaṣa Engine"
decision_owner: "Strategic Suvarṇa (N-28); the native only for N-1, the veto, scope changes and NATIVE_SETUP_v1_0.md acts"
plan_item: "L.11"
governed_by:
  - "SUVARNA_CAMPAIGN_PLAN_v1_5.md §4.2 (J1), §5.1 (Track E), §5.3 (F-3), §6.3–§6.6"
  - "SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.5 (G1–G15; R1–R11; P1–P14; §6 serving-guard precondition)"
  - "SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md v1.5 §3, §6, §11.7, §12"
  - "NATIVE_SETUP_v1_0.md (NS.0–NS.10 before N-1; NP.1 = E7.2)"
  - "decisions N-2, N-3, N-6, N-26, N-27, N-28, N-29, N-31–N-38, D1–D4, F-3 ($SUVARNA_HOME/authority/DECISIONS.jsonl)"
changelog:
  - "1.2 (2026-09-30, plan set v1.5): approvals re-owned — merges by the swarm identity through merge_gate (N-25b, N-38); N-4/N-5/N-8/N-22/N-26/N-27, the CLAUDE.md note and closing #2736 by Strategic Suvarṇa (re-seals and the freeze after an independent review; N-28); E7.2 stays native. E0.1 is SS's control PR, new E0.2 the `Suvarṇa path guard` CI job (N-38; NATIVE_SETUP NS.6). New §4a F-3 lane: drop the eight FKs, guard never refuses, F3.GUARD/F3.PROOF (N-32). E5 heading 40–65 h (Astra F18). E5.3 through the build broker with hold, scope and expect_job_image_tag re-checks, LANDING.json, serving guard, no dump (N-29, N-31, N-33, N-35, N-36; Astra F13). E5.5 certification currency contract (Astra F14). E5.6 rehearsal environment specified (Astra F16). E5.7 becomes the L0 rebuild drill (N-29; Astra F15). New E5.8 serving-guard inventory (N-33), E5.9 transitive footprint (N-32; Astra F13). E6.3t detector elevated_interface_ok (Astra F7). E7.1 server enforcement and the global-L0 grant (N-31; Astra F13); E7.2 adds _suvarnabuild ownership of builder.env (N-36). Tools from /Users/Dev/suvarna/control, decisions log under authority/ (N-37); parks to SS, no /loop (N-28, N-34)."
  - "1.1.1 (2026-09-30, review pass 3 folded; REVIEW_PASS3_DISPOSITION_v1_0.md): migrations only in the Suvarṇa range after N-27's deny-list amendment (E0.1), which gates E7.1 and E3.2; N-26 renumbers into it. New packet E1.10: R34 and R36 closed after landing, migration, deploy and runtime proof; R34's residual split. E4.2r: DEFERRED counts only with the bo_upaya-Idem.pattern withholding in force and the fix PR (head suvarna/land/E4.2-build-001) merged. E5.3: dispatch is an --assets run over the level's non-family assets only and refuses a family intersection. E6.3: the interface elevated_assets(ref, repo) -> set[str] and the LEVEL_MAP.json schema pinned; E6.3t's detector. Census through census_run."
  - "1.1 (2026-09-29, review pass 2 folded): one branch rule (lanes from suvarna/trunk; fold lanes before the cut-over pushed to campaign/nikasha-test; landing branches from origin/main). E3: the 10 commits cherry-picked; migrations per N-26; R39 closes on the census's Build checks in the scorecard; deploy = ancestry. E4: E4.1 no longer waits for the ledgers; E4.3 lands them and checks the register too; E4.2 split into the merged fix (test file pinned) and R244's state (E4.2r). E1: scorecard schema and committed generator; E1.9 census --assets. E5: canary in E5.3; E5.6 wave rehearsal off production; E5.7 L0 dump rehearsal. E6: FAMILY_ASSETS.json and registry-coverage schemas pinned; E6.3t. E7: preflight returns the builder's scope; suvarna-build interface pinned; builder_scope measured through the preflight; E7.3 lands on strategy/suvarna-plan. §9 findings folded into plan v1.4."
  - "1.0 (2026-09-29): first issue. Packets, write sets and boundaries for lanes E1–E7; approvals named; plan_model detector fields pinned (E3.2, E3.7, E5.1–E5.5, E6.3). Measured today: the build engine's own work is 10 commits on top of l3/kala-layer-briefs, not ~200 (§3); migrations 1094–1096 are unapplied and sit inside L3's reserved range 1070–1119 (§3.3); the tier documents and the Nikaṣa tools are not on main (§4)."
---

# Track E brief — the Nikaṣa Engine session

This brief is the write boundary G4 refers to for every Track E packet. It never contradicts plan v1.5; where it found
the plan's facts out of date it says so (§9) and follows the plan until Strategic Suvarṇa revises it.

## §1 · Scope and done

- **Done = J1-ready:** every Track E row of the J1 checklist (plan §4.2 #1–#6a, #9–#13, #16) reads done by its detector, and
  the Conductor hands Strategic Suvarṇa one J1 packet with evidence. The freeze itself is N-8 (SS, after an independent
  review of the packet); the reopens are N-4/N-5 (SS; re-seals after an independent review).
- **Seven lanes:** E1 tooling · E2 clause fixes · E3 build engine · E4 landing and `bo_upaya` · E5 execution tooling ·
  E6 gate detectors (D3) · E7 build identity (D1; the D1 auth PR is E7.1) — plus the F-3 migration (§4a, N-32). E0.1
  and E0.2 are Strategic Suvarṇa's control PRs (§2a), not lanes.
- **Queue:** `hq/00_ARCHITECTURE/control/suvarna/state/QUEUE_ENGINE.jsonl`; queue ids `<plan_item>-<kind>-<nnn>`;
  lane branches `suvarna/lane/<queue id>`; worktrees `$SUVARNA_HOME/lanes/<queue id>` (arch §12.2).

## §2 · Rules for every lane

- **Branch base (arch §12.2, one rule).** Every lane branches from `suvarna/trunk` (= `main` plus accepted packets),
  never from `campaign/nikasha-test` or `campaign/nirmana-engine`: both sit on `l3/kala-layer-briefs` and carry ~190
  foreign commits. Source branches are read with `git show`/`cherry-pick -x` only. Inspector work starts once
  E4.1-build-001 is accepted and merged into trunk. **Exception:** a fold lane before the E4.3 cut-over is cut from
  `origin/campaign/nikasha-test` and pushed back to it as a fast-forward (arch §12.7); it never opens a PR. **Landing:**
  PRs to `main` come from `suvarna/land/<group>` branches cut from `origin/main` (charter G11). Never edit
  `/Users/Dev/madhav-nikasha` or `/Users/Dev/madhav-engine`; the engine checkout's uncommitted files are not touched.
- **Proof.** Failing-first test plus a recorded mutation run (plan §6.3). Commits `git commit -- <paths>`, one row per
  commit. Fingerprints rotate last (E5.4 once landed).
- **No production writes.** Track E dispatches **no build** (a live build before J1 fails charter §6 precondition 6).
  Schema changes go only by migration, applied by the deploy after the swarm identity's merge through the merge gate
  (N-25b, N-38), verified read-only. Ledgers change only by `--emit-gaps` with the withholding list or by a reviewed
  migration script proven idempotent on a copy.
- **Tools and authority (N-37):** every `python3 -m suvarna_tracker.*` runs from the control checkout
  (`PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance`); decisions are read from
  `$SUVARNA_HOME/authority/DECISIONS.jsonl`, holds from `authority/HOLDS.jsonl` (N-35). Questions park to Strategic
  Suvarṇa (Steward → SS, N-28), never to the native.
- **Out of bounds, all lanes:** family assets and their code, data and migrations (charter R8: `ka_gochara`,
  `ka_gochara_resonance`, `ka_vedha_gochara`, `ka_sangam`, `ka_kshetra` and tables, plus claimed prerequisites), except
  the F-3 migration's DROP CONSTRAINT on `kala_convergence` under lease and notification (§4a);
  the `WriterBase` contract (R2); any chart but `482012f1…` (R4); credentials (P1, R10); `CLAUDE.md`, `.github/**` and
  `.claude/**` (path-guarded, E0.2: SS's control PRs only); the plan, plan model and tracker code (Strategic's; E7.3 is a
  PR to `strategy/suvarna-plan`); tiers 1–3 before their agenda is approved.
- **Migrations:** only in the Suvarṇa range 1200–1299 (N-27, decided), and only once its deny-list amendment is on
  `main` (E0.1): until then main's `.claude/settings.json` refuses every Suvarṇa migration edit (arch §12.5). One number
  at a time inside the range, placeholder on the lane branch, row on the coordination branch; never in
  `platform/supabase/migrations/` to step around the deny (P13); every migration file goes through the
  `migration-guard` agent before its PR opens.
- **Reviews:** a fresh gate reviewer per packet (Opus 5.5 medium; **high** for writer, ledger, auth, reopen and
  algorithm packets); two rejects → Steward. CI green before a PR is marked ready. A PR merges only through
  `python3 -m suvarna_tracker.merge_gate --pr <n>` (CI green on the head SHA, a gate-reviewer ACCEPT for that SHA, the
  path guard, no active hold) into main's merge queue (N-38).

## §2a · E0 — Strategic Suvarṇa's control PRs (outside the swarm)

- **E0.1** (N-27): amends main's `.claude/settings.json` deny line `1[2-9][0-9][0-9]` → `1[3-9][0-9][0-9]` so Suvarṇa
  lanes may edit `platform/migrations/12[0-9][0-9]_*`. Authored by SS as a control PR outside the swarm (the swarm's
  path guard refuses `.claude/**`), coordinated with the L3 Kāla owner by a coordination note on the coordination
  branch. Gates E7.1, E3.2 and the F-3 migration.
- **E0.2** (N-38): SS's control PR adding the CI job **`Suvarṇa path guard`**: it fails a PR whose head is `suvarna/*`
  or whose author is the swarm bot if the PR touches family paths (`FAMILY_ASSETS.json` assets and the family code
  globs), other workstreams' reserved paths, migrations outside 1200–1299, `.claude/**`, `.github/**` or `CLAUDE.md`.
  The native adds it to ruleset 20141220's required checks (NATIVE_SETUP NS.6). Needed before the first swarm merge
  (launch gate LG.5).

## §3 · Lane E3 — the build engine (40–70 h)

### 3.1 · What is actually there (measured 2026-09-29)
`campaign/nirmana-engine` is 200 commits ahead of `main`, but only **10 are the engine's**: `origin/l3/kala-layer-briefs
..campaign/nirmana-engine` = `d9dab8ad2 e9daf4eea f4a6f9541 8edba0533 551d5ecad 7fc5c8e8b 17e5a1257 73385d72f
8fdcdfe40 e5dd65b8f` (A1, A2, A3, B1, B2, decisions, hand-off; ~60 code files, each packet with recorded reviews). The
other ~190 are L3 readiness docs and Saṅgam stage 3 (`ka_sangam` engine and writer, migrations 1092/1093), which travel
to `main` via PR #2735 under the Saṅgam session. **E3 lands only the 10.**

### 3.2 · Packets

| Queue id | Plan item | Content | Done (detector) |
|---|---|---|---|
| E3.2-build-001 | E3.2 | **engine-core PR**: A1 (`8edba0533`), A2 (`f4a6f9541`), A3 (`551d5ecad`), D-1(b) code hunks of `73385d72f`; `runner.py`, `asset_runner.py`, `ga_writers/_telemetry.py`, `terminalizeFailedRun.ts`, `recalibrationEnqueue.ts`, `cockpit/watchdog`, their tests; migration 1094; the `ci.yml` hunk | PR from `suvarna/lane/E3.2-build-001` merged |
| E3.2-build-002 | E3.2 | **engine-cascade PR**: B1 (`17e5a1257`) and B2 (`8fdcdfe40`) — cockpit stats and runs routes, cockpit v2 components, `columnPresence.ts`, `viewPresence.ts`, integration tests; migrations 1095, 1096. **Excludes** B1's `asset_census.py` hunk and `test_b1_asset_census_blocked_dependency.py` (R216: carried identically by E4.1) | PR from `…/E3.2-build-002` merged |
| E3.2-build-003 | E3.2 | **engine-record PR** (docs only): `00_ARCHITECTURE/briefs/nirmana/engine/**` (STATE, DECISIONS, EVENTS, measurements, reviews, hand-off) | PR from `…/E3.2-build-003` merged |
| E3.2-build-004 | — | `CLAUDE.md` §N.2 "KNOWN BREACH" note (engine D-1), rebased on current `CLAUDE.md`, own PR | **Strategic Suvarṇa** decides (N-28); lands as SS's control PR (`CLAUDE.md` is path-guarded, E0.2); not a J1 input |
| E3.3-migrate-001 | E3.3 | after the deploy: read-only check of `_migrations_applied` and the new column, enum and view | `migrations_applied` on the three numbers N-26 fixes (1094–1096 unless renumbered; the plan model is pinned in the same commit as the N-26 line) |
| E3.4-build-001 | E3.4 | R217 (`mark_run_state` writes `build_runs.last_error` on :1240/:1450/:1456), A2b (`mark_asset_error` empty text; site-2 global assets; mock-leak), A3b (runs dispatched with no manifest). Proof on the CI Postgres integration suite; no build is dispatched to manufacture a failure | R217 closed |
| E3.5-build-001… | E3.5 | C1 (crash/orphan/reap; begins with a search, `guardian_cleanup`/`manual reap` have no source hits) and C2 (stuck states). After landing; runs alongside Track B; not a freeze input | event with evidence |
| E3.6-analysis-001 | E3.6 | R39: after E3.7, the census's `Build.*` checks run on `main` against the engine's own claims (run-level states, `last_error` written, cascade and downstream reporting); every check PASS, none NO_DETECTOR; results recorded in the scorecard under `engine_build_checks`. An elevation-plan document is optional and closes nothing | R39 closed |
| E3.7 | E3.7 | the landing PRs' merge (squash) commits through main's merge queue are ancestors of the job image's commit (`suvarna-build --preflight` → `job_sha`), and the landed writer files' hashes match at that commit | `deployed_contains` (job, ancestry) on 001 and 002 |

- **Content:** the 10 engine commits are cherry-picked with `-x` onto lanes from `suvarna/trunk`; nothing else from
  `campaign/nirmana-engine` is carried.
- **Sequencing:** 001 → 002 (002's migration follows 001's) ‖ 003; after merge: E3.3 → E3.4 → E3.6 (needs E1.7, E3.7);
  E3.7 needs E7.2 (the preflight script). Generated files (`nirmana-writer-digests.json`,
  `capability_estate_census.json`) are regenerated on the landing branch by their generator, never cherry-picked.
- **Detector pins:** plan_model E3.2 and E3.7 name the PRs by **head ref** (the landing branches
  `suvarna/land/E3.2-build-001/-002/-003`, base `main`) with `prs: []`. The detectors resolve a head ref to its PR
  (`gh pr list --head <ref> --base main --state all`; a CODE item in REVIEW_PASS2_DISPOSITION); until that lands the
  items read unknown, and Strategic Suvarṇa adds the PR numbers the day each PR opens (its duty, named in the plan
  model's `pinned_by`).
- **Write set:** the files above, the build engine's three migrations (today `platform/supabase/migrations/1094_*`–`1096_*`;
  after N-26 renumbered into the N-27 range, in `platform/migrations/`, the folder the amended deny list opens), their tests. **Boundary:** no other
  writer, no family code, no `WriterBase`/`WriterResult` shape change (A1 stops *reading* `duration_seconds`; the
  field stays).

### 3.3 · Migration numbers — decided (N-26, N-27)
1094–1096 are unapplied (`_migrations_applied`, read 2026-09-29 and 2026-09-30), claimed by no open PR, and **inside L3 Kāla's
reserved range 1070–1119** (coordination branch). **N-26:** they are renumbered at landing to the next free numbers of
the Suvarṇa range 1200–1299 (N-27) once E0.1 is merged — the lane re-verifies read-only that each is still unapplied at
that moment (legal: never applied, P4 untouched); if one has been applied meanwhile, the lane stops and parks to SS.
Strategic Suvarṇa pins E3.3's `numbers` and plan §4.2 #9 in the same commit. Only E3.2-build-001/002's PR opening
waits on E0.1.

## §4 · Lane E4 — landing and `bo_upaya` (10–20 h)

`asset_census.py`, `catalog_provenance.py`, `asset_elevation_tracker.py`, `manifest_fingerprint.py`,
`check_migration_ledger_vs_production.py`, the ledgers, the register **and tiers 1–4, the L0 instance v3.0 and the five
pilot briefs** are all absent from `main` today; they live on the `l3/kala-layer-briefs` base. N-3's "split and
retarget" is done by building fresh branches from `suvarna/trunk`, not by retargeting #2736.

| Queue id | Plan item | Content | Done (detector) |
|---|---|---|---|
| E4.1-build-001 | E4.1, E4.1c | **code PR**: every governance tool at `campaign/nikasha-test` HEAD with its tests (`platform/scripts/governance/{asset_census,catalog_provenance,hand_row_provenance,ledger_r81_migration,apply_r80_r81_ledger_migration,manifest_fingerprint,check_migration_ledger_vs_production}.py`, `drift_detector.py`/`schema_validator.py` hunks, `__tests__/*`, `r218_*`), `00_ARCHITECTURE/control/asset_elevation_tracker.py`; a base-dependency sweep (every import and path resolves on `main`); a CI job running `platform/scripts/governance/__tests__/` | files on main; `ci.yml` contains `asset_census` |
| E4.1-build-002 | E4.1 | **evidence PR**: the four tiers, L0 instance v3.0, pilot briefs, register v2.8, implementation plan, `nikasha_test/**`, reviews, the `bo_upaya` hand-off. `SESSION_LOG`, `CURRENT_STATE`, `CAPABILITY_MANIFEST` hunks only as Nikaṣa-own rows added on `main` (never a rebase); manifest re-fingerprinted last | register on main (E4.1's `main_has_files` has no ledgers) |
| E4.3-fold-001 | E4.3 | **ledger PR at the named cut**: folds stop on `campaign/nikasha-test` at a recorded commit; `asset_gaps.jsonl`, `asset_certs.jsonl` land; line count and md5 of both ledgers **and the register** equal old vs new (evidence in the event); Strategic Suvarṇa re-points `NIKASHA_REF` to `origin/suvarna/trunk` in one step | `main_has_files` on both ledgers; a J1 input |
| E4.2-build-001 | E4.2, E4.2r | `bo_upaya` per the hand-off: restore `replace_prior_rm_dasha_windowed()` before `replace_prior_rm_prescriptions()` (`bo_upaya.py:1942–1945`), rewrite the comment, source-order test at `platform/python-sidecar/tests/l2/test_bo_upaya_source_order.py`, correct the three write-ups and L2 strategy §6 wording. Lease `SUVARNA-E4.2-build-001` on `bo_upaya`. Not migration 1013, not `cr_status.ts`, no live rebuild (that is B.U). Landing branch `suvarna/land/E4.2-build-001` | E4.2: the test on `main`; E4.2r: R244 `DEFERRED`, folded on the merged fix, and counted by `register_rows_state` only while `NIKASHA_WITHHOLDING.json` at the Nikaṣa ref holds `bo_upaya-Idem.pattern` (`deferred_withholding_entry`) and the fix PR is merged (`deferred_pr`: the head ref above, replaced by the PR number the day it opens) |

- **Sequencing:** 001 first (it unlocks `suvarna/trunk` as the base for E1, E5, E6), then 002, then the cut-over last.
  E4.2 in parallel from day one. PR #2736 stays open until 001–003 merge; closing it is Strategic Suvarṇa's act (N-28).
- **Folds before the cut-over** (arch §12.7): fold lanes cut from `origin/campaign/nikasha-test`, pushed back as a
  fast-forward; register rows only, no ledger emits until E5.2 lands.

## §4a · F-3 — the MSR key migration (N-32; plan §5.3)

F-3 is decided (N-28/N-29, concrete form N-32): derived rows are regenerable, so the L2→L3 cascade is handled by
rebuilding in wave order, never by refusing rebuilds. Track E owns the migration; the lane takes a lease on the
coordination branch and notifies whoever owns Saṅgam (a family session that has claimed it; otherwise Track F's
Saṅgam lane until J1.FO rules) by lease note before its PR opens and again when it is deployed; the owners of
`kala_convergence`'s downstream are notified the same way.

| Queue id | Content | Done (detector) |
|---|---|---|
| F3.FK-migrate-001 | one migration in 1200–1299 (after E0.1): `ALTER TABLE … DROP CONSTRAINT` for all eight FKs into `bodha_msr_signals` (seven tables); `CREATE OR REPLACE FUNCTION assert_l2_msr_delete_safe` **without the refusal branch** (keeps the admitted-asset-context check; records the referencing-row counts per table into build evidence; also removes the re-arm if a key is ever re-added). `migration-guard` before the PR; gate review high. Rejected alternative: ON DELETE SET NULL (4 of the 8 columns are NOT NULL, measured 2026-09-30; nulled references serve as meaningless rows) | F3.FK: `fk_no_cascade`, target `no_fk` — zero FKs of any kind into the table (the detector checks the target, no `allow` escape; Astra F9) |
| F3.GUARD | after the deploy: the function's live definition has no refusal path; a read-only check of `pg_proc` plus the recorded counts from the first MSR writer run | event with evidence, validated by `evidence_verified` |
| F3.PROOF | on the E5.6 rehearsal database: an MSR writer's delete/reinsert with referencing rows present in all seven tables; no refusal; the dangling-reference count recorded (`msr_referential_integrity.py`); the downstream rebuild in wave order restores referential integrity | E5.6 acceptance case, `evidence_verified`; gates J1/W0 |

- **Why it is safe:** signal ids are deterministic (`test_bo_*_signal_identity.py`,
  `test_bo_shared_msr_signal_identity.py`), so an unchanged signal keeps its id and references stay valid; a changed or
  removed signal leaves a dangling reference until the downstream asset rebuilds in its own wave (staleness
  propagation marks it; the serving guard, N-33, covers the gap); `msr_referential_integrity.py` measures dangling
  references after each wave.
- **Not changed:** the other cascades found by the pg_constraint closure (`kala_convergence` → `kala_darshana`,
  `kala_obstruction`, `phala_anchors`, SET NULL `kala_bhavishya`; `phala_anchors` → `phala_pramana`, `phala_sankrama`,
  `phala_sodhana`, `phala_suddha_sodhana`, SET NULL `phala_mitigation`, `phala_muhurta`) stay; each wave's impact
  statement lists them (E5.9) and the downstream rebuilds in wave order.

## §5 · Lane E1 — tooling (30–50 h)

| Queue id | Plan item | Content | Done |
|---|---|---|---|
| E1.1-analysis-001 | E1.1 | re-run T1–T5 on today's tooling with the generator `platform/scripts/governance/nikasha_scorecard.py` (written here); publish the scorecard (schema below) | event with the scorecard |
| E1.2-build-001… | E1.2 | R245 Idem blind spots · R248 full-shape detector match · R249 empty-by-design vs broken · R250 verify the `bg_sarvatobhadra_grid` label · the `asset_census.py` docstring's exit-code drift (a new register row) | rows closed |
| E1.3-build-001… | E1.3 | R226 `catalog_provenance.py --live` · R228 twelve out-of-range `source_ref`s (annotation only, no serving change) · R229 the 27 unowned tables measured and classified; any registry change it implies is handed to the owning layer's Track A brief | rows closed |
| E1.4-migrate-001 | E1.4 | R251: 19 pilot hand rows and 42 unregistered hand criteria through a reviewed crosswalk migration (R81 pattern) | R251 closed |
| E1.5-analysis-001 | E1.5 | R55 once 1094 is applied: timing verdicts read live | R55 closed |
| E1.6-build-001 | E1.6 | R246 DELETE-FK-child detector, narrow, after E4.2 merges | R246 closed |
| E1.8-analysis-001 | E1.8 | R24: production L3 census (R134) and clean re-runs of all six layers after E1.2–E1.4 | R24 closed |
| E1.7-analysis-001 | E1.7 | T1–T5 re-proved with the tools on `main`; scorecard committed on `main` by the committed generator | `scorecard_pass` |
| E1.10-analysis-001 | E1.10 | R34 and R36 (BLOCKS_FREEZE, `CLOSED_ON_BRANCH`): after E3.2 (A1 `8edba0533`, A3 `551d5ecad` landed), E3.3 (A1's timing migration applied) and E3.7 (deployed), prove each at runtime: R34 non-NULL `rows_per_second`/duration on representative applicable paths, R36 a registry divergence failing only the diverged asset (harness replay, then the deployed evidence), both read-only from build history or on the E5.6 rehearsal database, never by a Suvarṇa production build before J1; split R34's residual (the legacy `ga_writers/_telemetry.py` path, 8 `ga_*` call sites) into its own non-freeze row; fold both rows closed | `register_rows_state` R34, R36 in CLOSED/DONE; J1.R expects both |
| E1.9-build-001 | E1.9 | `asset_census.py --assets <id,…>` for the census and `--emit-gaps`, so a level wave measures and emits only its assets (other assets' gap state untouched); tests | `main_file_contains` `--assets` |

- **Scorecard schema** (`00_ARCHITECTURE/control/NIKASHA_T1_T5_SCORECARD.json`): `{"generator":
  "platform/scripts/governance/nikasha_scorecard.py", "generator_sha256": "<sha256 of that file at the ref>",
  "inspector_commit": "<sha>", "ref": "<ref>", "tests": {"T1": {"verdict": "PASS|FAIL|PARTIAL", "cells": {…},
  "population": "…", "evidence": "<path>"}, …, "T5": {…}}, "engine_build_checks": {"<criterion>": "PASS|…"}}`.
- **Write set:** `platform/scripts/governance/**` (inspector, provenance, their tests), the scorecard, the
  retrieval-registry `source_ref` annotations (R228 only), the ledgers through E5.2/migration scripts only.
- **Census lock:** every census here goes through `python3 -m suvarna_tracker.census_run --layer <Lx> --out <absolute
  path> --wait 900 --emit --actor <role>` (it holds the census lock) and competes with Track A's six censuses; the Conductor asks Exec Suvarṇa's
  Conductor for a slot by tracker note, never runs outside the lock.

## §6 · Lane E2 — founding-document fixes, held for the reopen (20–30 h)

- **E2.1-design-001/002/003:** one agenda per tier, `00_ARCHITECTURE/briefs/suvarna/reopen/REOPEN_AGENDA_T{1,2,3}_v1_0.md`,
  each row with its clause, the chosen remedy and the drafted replacement text, from the D2 ruling
  (`nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md` D2): T1 R01, R72, R76 · T2 R06, R73, R75, R88, R89, R90, R91, R119
  (T2 half), R181/R186/R198 (§7.1 halves) · T3 R08, R09, R10, R65 and R68 (T3 halves), R67, R71 (D3's text), R74, R93,
  R120, R201, R221; closing with them R94, R140, R185, R192, R208. R131, R210, R214 stay deferred. That is **31** rows
  against the plan's figure of 32 (Astra F18): the packet reconciles the two and reports the count it finds, and SS
  corrects whichever document is wrong.
- **Combine:** after A.H, each agenda gains the harvested tier gaps assigned to it (v1.1). Strategic Suvarṇa decides
  N-4.Tx (N-28). Once approved the agenda is closed; later finds become rows for a second round.
- **Apply (plan items J1.1/J1.2/J1.3):** after N-4.Tx, a lane redlines that tier, runs the cross-tier re-render pass
  (counts, gate names, section numbers across tiers, instances, tracker), gets an independent review (GPT-6 Astra or
  Kimi K3), and Strategic Suvarṇa decides N-5.Tx on it, strictly T1 → T2 → T3. E2.2 (R71) closes with the T3 re-seal.
- **Write set:** the agenda files; the tier documents only after their agenda's N-4 and only on their lane branch.

## §7 · Lane E5 — execution tooling (40–65 h)

All on `main` via `suvarna/trunk`, each with its test (the paths are the plan-model pins):

| Item | Files | What it must prove |
|---|---|---|
| E5.1 | `platform/scripts/governance/nikasha_certify.py`, `__tests__/test_e5_1_certify.py` | writes arch §12.16 records; refuses a PASS whose criterion has `detector: NONE` or no census run id; refuses N/A not computed by the registry; idempotent on a ledger copy |
| E5.2 | `nikasha_fold.py`, `__tests__/test_e5_2_fold.py` | register state transitions; `--emit-gaps` with the withholding list (`00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json`, today `bo_upaya-Idem.pattern`); computed tallies; fingerprints; drift |
| E5.3 | `suvarna_level_wave.py`, `__tests__/test_e5_3_level_wave.py` | dispatch only through the **build broker** (`suvarna-build` = `sudo -n -u _suvarnabuild … broker.py`, N-36), **always `--assets <the level's non-family assets>`**: every asset at the level in the frozen `LEVEL_MAP.json` minus `FAMILY_ASSETS.json`'s `family_set`, never `--level`; **refuse** (exit non-zero, nothing dispatched) if the dispatch set intersects `family_set` or either file is missing on `origin/main`; the test asserts both, with a fixture level holding a family asset (levels 1, 5, 12, 13 do today). The broker re-checks at dispatch, independently of the script: no active hold in the hold ledger (N-35); asset scope ⊆ the frozen level minus `family_set`; the running job commit, passing `expect_job_image_tag` so the server refuses on a check-to-dispatch race. **wave_deployed evidence:** `$SUVARNA_HOME/evidence/<wave>/LANDING.json` with the exact head ref, PR number, merge (squash) commit through main's merge queue and the writer-file hashes; that commit an **ancestor** of `job_sha` / `deployed_sha` after a fetch, never equality; writer hashes re-checked at the running commit. Read-only per-chart lock check. **Destructive-op record (R3, N-29), no dump:** pre-wave semantic fingerprints (E5.5) and counts of every table in the write footprint, the impact statement with its transitive footprint (E5.9) and the rebuild plan, a post-wave diff; for an L0 wave (N-31, dispatched by the builder under the global-L0 grant) the statement also names the L0 assets changed and, per other chart, the downstream closure served stale (disclosed, N-33), and the fingerprints and diffs are retained to campaign close. **Serving guard (N-33)** per the E5.8 mode of each written table: build the candidate, verify, switch authority, reverse on failure; or a disclosed maintenance window (the notice in the served envelope, a canary of golden reads of the served MCP tools for `482012f1` before and after, the window closed only on a passing canary; an unexplained difference triggers the stated reversal). Fail closed. Tested against the builder with `--preflight` and expected-refused dispatches (§8 E7.1's list), and end to end in E5.6. How staleness propagates on a global run is established from `staleness.py` and build history, read-only |
| E5.4 | `manifest_fingerprint.py`, `__tests__/test_e5_4_manifest_per_entry_rotation.py` | rotates each changed entry, not only the root |
| E5.5 | `nikasha_stale_certs.py`, `__tests__/test_e5_5_stale_certs.py` | invalidates a record whose writer hash, upstream certificate generation ids or semantic row fingerprint no longer match, under the **certification currency contract** below (Astra F14) |

(all under `platform/scripts/governance/`). Sequencing: E5.1 → E5.5; E5.3 after E7.3; E5.6 after E5.1–E5.5, E7.1 and
the F-3 migration; E5.7 on the E5.6 environment; E5.8 before the first wave. E5.6, E5.7 and F3.PROOF gate J1/W0.
Ledger-writing code: Builder at high effort, gate review high.

- **E5.5 certification currency contract (Astra F14).** (1) **Semantic row fingerprint** per asset: rows ordered by
  natural key, serialized as canonical JSON, with volatile columns (surrogate ids, timestamps, build ids) excluded — the
  excluded list is declared in the asset's brief (Track A §5); embeddings are compared under a declared equivalence
  policy, not byte equality. An idempotent rebuild leaves the fingerprint unchanged and invalidates nothing downstream;
  a material change does. (2) **Certificate generation ids:** each certificate records the generation ids of the
  upstream certificates it rests on. (3) **Invalidation watermark:** E5.5 records the ledger ref up to which it has
  evaluated invalidations; `elevated_assets` raises unless the watermark is at least the ledger ref it is asked about.
  (4) **Bounded re-walks:** at most two invalidation re-walks per layer; a third goes to Strategic Suvarṇa for review
  before any further rebuild.
- **E5.6 rehearsal environment (Astra F16).** A local PostgreSQL cluster run by the `suvarna` user (`/opt/homebrew`
  binaries; data dir `/Users/Dev/suvarna/rehearsal/pg`); schema by `migrate.ts` at the landing commit; seeded from
  reader dumps (as `suvarna_reader`); the orchestrator run from source at the same commit as the job image (residual:
  not the image itself). It isolates global L0 writes. **Executable acceptance cases**, at least: one level find → fix →
  rebuild → certify with E5.1–E5.5; F3.PROOF (§4a); a family-intersecting dispatch refused; a hold refuses dispatch;
  the canary triggers the reversal; an idempotent rebuild leaves the semantic fingerprint unchanged. Each case's
  evidence is validated by `evidence_verified` (CODE→). No production write.
- **E5.7 L0 rebuild drill (N-29 replaces the dump; Astra F15).** Rebuild L0 on the rehearsal database from its sources
  and compare its semantic fingerprints with production's (read as `suvarna_reader`); a difference is explained or
  fixed before B.W0. This proves every L0 wave's rebuild plan. Pre/post fingerprints and diffs are retained to
  campaign close.
- **E5.8 serving-guard inventory (N-33).** `00_ARCHITECTURE/control/SERVING_GUARD_INVENTORY.json`: every served table
  and MCP tool with its mode — an authority mechanism (candidate → verify → switch → reverse; the Gochara/Pravāha
  pattern, L2 producer generations, migration 1036) or maintenance-window mode — and the disclosure notice the served
  envelope carries during a window. E5.3 refuses a write to a table the inventory does not list.
- **E5.9 transitive footprint (N-32; Astra F13).** Every wave's impact statement lists the write set's transitive
  write/delete footprint by pg_constraint closure (CASCADE and SET NULL edges, read-only), not only the writers' own
  tables; E5.3 computes it and its test uses the measured 2026-09-30 closure (§4a) as a fixture.

## §8 · Lanes E6 and E7

**E6 — gate detectors (50–90 h).** E6.0 is N-22 (Strategic Suvarṇa, before E6.5). E6.1: `layers:` and column-pattern
applicability on every entry of `CRITERION_REGISTRY` (`asset_census.py`); generic Null (schema defaults, writer
literal fallbacks, constant columns; never PASS alone), Dens (contract **and** a tier column in the served select;
labelled structural), Ldgr (L0 source presence, L1 build receipt, L2+ constituent resolution generalised from
`msr_referential_integrity.py`), Carr per layer, `Earn.literal_lint` (`check_earned_signal.py`), a real
`Earn.service_state`; the narration lints wired as Narr. E6.2: the rollup (worst of FAIL > ERRORED > NO_DETECTOR >
PARTIAL > PASS; N/A only by rule; no checks = NO_DETECTOR), cells versioned with the registry revision. E6.3:
ELEVATED exact in `asset_elevation_tracker.py` (terminal dispositions honoured) with
`__tests__/test_e6_3_elevated_exact.py`; `00_ARCHITECTURE/control/LEVEL_MAP.json` and
`00_ARCHITECTURE/control/FAMILY_ASSETS.json` generated from the live registry, frozen at J1; a cycle is an error.
**The E6.3 interface** (pinned; the tracker and E5.3 call it): `asset_elevation_tracker.elevated_assets(ref: str, repo:
str) -> set[str]`, a module-level function; input = a git ref (the Nikaṣa ref the tracker reads the ledgers at) and a
repository path; it reads every input with `git -C <repo> show <ref>:<path>` (`asset_gaps.jsonl`, `asset_certs.jsonl`,
with E5.5's invalidations already in the ledger, and the recorded dispositions), never the working tree, never the
database, no side effects; output = the asset ids ELEVATED per plan §1.1 or terminally dispositioned; it **raises** on
any unreadable or malformed input, and when E5.5's invalidation watermark is older than the ledger ref (§7), never
returns an empty set for a failure. `__tests__/test_e6_3_tracker_interface.py` proves the signature, the committed-ref
reads (a dirty working tree changes nothing), and both raises.
**LEVEL_MAP.json keys**: `{"version", "frozen_at", "registry_revision", "levels": {"<asset_id>": <level>}}`; wave
membership is read only from it (plan-model `level_map`).
**FAMILY_ASSETS.json keys** (the plan model reads these names): `{"version", "frozen_at", "registry_revision",
"family_gochara": [...], "family_sangam": [...], "family_kshetra": [...], "family_readers_L3": [...],
"family_readers_L4": [...], "family_readers_L5": [...], "family_set": [<union of all six>]}`. E6.3t (Strategic's):
the Suvarṇa tracker calls the E6.3 function at the committed ref through that interface; its detector is
`elevated_interface_ok` (CODE→; reads unknown until built): the running tracker's own caller invokes
`elevated_assets(ref, repo)` at the approved commit and gets a set back, not file presence (Astra F7). E6.4: `ledger_e6_4_info_rekey.py` (R81 pattern, on
a copy first). E6.5: `asset_census.py --registry-check --out 00_ARCHITECTURE/control/registry_coverage_report.json`,
committed on `main`, schema `{"registry_revision", "inspector_commit", "covered_cells": <n>,
"uncovered_required_criteria": [], "per_asset_pending": [<criteria declared "required, per-asset detector
pending">], "na_rules": [...]}`. Per-asset semantic detectors are Track A/I, not here.

**E7 — build identity (8–15 h; re-estimated after E7.1, whose scope grew in v1.2).** E7.1-build-001:
`authorizeChartAccess.ts`, `requireChartPermission.ts`, `api/cockpit/runs/route.ts` (dispatch needs `'build'`;
`clear_before` needs `'all'`), new `api/cockpit/runs/preflight/route.ts` (authenticated; returns `{job_image_tag,
job_sha, deployed_sha, builder: {principal_id, role, status, grants: [{chart_id, permission}]}}`, the caller's own
scope), one migration widening `chart_grants.permission` to `('view','build')` (numbered in 1200–1299; the PR waits for
E0.1). **Server enforcement (Astra F13):** the dispatch route itself rejects any asset outside the builder's scope, any
family asset (the server reads `FAMILY_ASSETS.json` at the deployed commit), `clear_before`, any other chart, a
dispatch whose `expect_job_image_tag` differs from the running image, and a dispatch while a run is active on the
chart. **A second grant form, global L0 (N-31):** an asset list ⊆ the active L0 assets; never an L1+ asset, never
`clear_before`, never a family input; not `super_admin`. **Tests:** refused on clear, clear routes, scope aliases
(`layer=brahmagyan` or any layer/level alias that would expand past the grant), other charts, family assets through
every scope, L1+ assets under the L0 grant, a revoked or disabled identity, concurrent and duplicate dispatch, and a
stale `expect_job_image_tag`. `security-reviewer` agent plus gate review at high. **E7.2 is the native's** (admin DB;
NATIVE_SETUP NP.1, after E7.1): the account, the grant rows (canonical build and global L0), `builder.env` owned by the broker
account `_suvarnabuild` (mode 600; the swarm cannot read it, N-36), the broker's sudoers entry and the `suvarna-build`
wrapper; the non-secret builder uid, role, status and grant rows recorded in `$SUVARNA_HOME/run/builder_identity.json`.
**The `suvarna-build` interface** (pinned here; E5.3 and the detectors use it): absolute path
`~/.config/suvarna/bin/suvarna-build`, which calls exactly `sudo -n -u _suvarnabuild /opt/homebrew/bin/python3
/Users/Dev/suvarna/control/platform/scripts/governance/suvarna_tracker/broker.py <args>`; `--preflight` prints one JSON
object, the preflight route's answer; `--assets <id,…>` (canonical build grant) or `--l0-assets <id,…>` (global-L0
grant) dispatches after the broker's checks (hold ledger, scope, family exclusion, running commit; it passes
`expect_job_image_tag`) and prints `{run_id, plan, asset_count, job_image_tag}`; no other flags; output is always JSON;
a refusal is JSON with a non-zero exit. E7.3: the Monitor's `builder_scope` check reads `builder` from the preflight and
compares it with `builder_identity.json` (the reader cannot read `chart_grants.permission` or `profiles`, D6); the code
is a lane PR to `strategy/suvarna-plan`, which Strategic Suvarṇa merges and releases as a new control tag
(`suvarna-control-v<x>`) checked out at `/Users/Dev/suvarna/control` (N-37); the Monitor daemon restarts on it.

## §9 · Approvals, sequencing, estimates

| Act | Who |
|---|---|
| Packet specs, dispatch, retries, model/effort | Architect writes; Conductor (G1, G2, G8) |
| Gate verdict and fold | Gate reviewer; Scribe (G7); two rejects → Steward |
| Open a PR to `main` | Conductor (G11) |
| Merge to `main`; the deploy follows | the **swarm's GitHub identity** through `python3 -m suvarna_tracker.merge_gate --pr <n>` into main's merge queue (N-25b, N-38; §2) |
| Migration numbering of 1094–1096 (§3.3) | decided (N-26): renumbered into 1200–1299 at landing, unapplied state re-verified then |
| The Suvarṇa range and the deny-list amendment (E0.1) | decided (N-27); the PR is **Strategic Suvarṇa's** control PR outside the swarm, coordinated with the L3 Kāla owner by a coordination note |
| The `Suvarṇa path guard` CI job (E0.2) | **Strategic Suvarṇa's** control PR; the **native** adds it to ruleset 20141220's required checks (NATIVE_SETUP NS.6) |
| F-3 (§4a) | decided (N-32); Track E's lane, lease and notification to Saṅgam's owner |
| `CLAUDE.md` note (E3.2-build-004); closing #2736 | **Strategic Suvarṇa** (N-28) |
| Per-gate applicability rules (E6.0) | **Strategic Suvarṇa** (N-22) |
| Reopen agendas (N-4.Tx) | **Strategic Suvarṇa** |
| Re-seals (N-5.Tx) | **Strategic Suvarṇa**, after an independent review (GPT-6 Astra or Kimi K3) |
| Destructive operations beyond a writer's own delete-then-insert | **Strategic Suvarṇa** records a decision on a rebuild plan, a serving guard and the recorded pre-op fingerprint/counts (R3, N-29) |
| Holds | any role sets one (`python3 -m suvarna_tracker.hold --set --reason …`); SS clears a swarm hold; only the native clears a native hold (N-35) |
| Builder provisioning (E7.2) | **native** (admin DB; NATIVE_SETUP NP.1, after E7.1) |
| Freeze | **Strategic Suvarṇa** (N-8), after an independent review of the Conductor's J1 packet |

The Steward decides only within G1–G15; G16 (asset briefs) does not apply to Track E. Everything else the Steward
parks to Strategic Suvarṇa (`emit decision --state requested` + the park file; N-28), never to the native.

**Critical path:** N-27 → E0.1 → E7.1, E3.2 and the F-3 migration; E0.2 before the first swarm merge; E4.1-001 →
E1.2/E1.3/E1.4 → E1.8 → E1.7 → E3.6; E3.2 → merge → E3.3 → E1.5; E3.3 + E3.7 → E1.10; E7.1 → E7.2 → E7.3 → E5.3/E3.7;
E6.1 → E6.2 → E6.5 (+N-22); E5.1 → E5.5 → E6.3; E5.1–E5.5 + E7.1 + F-3 migration → E5.6 (F3.PROOF) → E5.7 → J1; A.H →
E2 combine → N-4/N-5 ×3.

**Estimates (plan §5.1 = §6.6):** E1 30–50 · E2 20–30 · E3 40–70 · E4 10–20 · E5 40–65 · E6 50–90 · E7 8–15 =
**200–340 h**. E3 may land lower (10 reviewed commits, not 200); re-estimate after E3.2. E5 (E5.6–E5.9), E7.1 and the
F-3 lane grew in v1.2: re-estimate after E7.1 and the first E5.6 run, reported against plan §10's trigger. **Swarm
merges before J1: about 12–14 PRs** (E3 ×3–4, E4 ×4, E7 ×1, E3.4 ×1, E1/E5/E6 grouped ×2–3, F-3 ×1; Astra Q3 recount),
plus SS's control PRs E0.1, E0.2 and the `CLAUDE.md` note; the Conductor batches where review allows.

**Findings for Strategic Suvarṇa:** all folded into plan v1.4, carried in v1.5 (10 engine commits; 1094–1096 and N-26; the tier
documents not on `main`; the branch rule). None open.
