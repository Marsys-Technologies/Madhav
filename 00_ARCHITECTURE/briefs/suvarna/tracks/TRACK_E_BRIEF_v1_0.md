---
artifact: SUVARNA_TRACK_E_BRIEF
canonical_id: SUVARNA_TRACK_E_BRIEF
version: "1.0"
status: "DRAFT — for native approval with N-1"
produced_on: 2026-09-29
produced_in: "Strategic Suvarṇa"
session: "Nikaṣa Engine"
decision_owner: "Native (Abhisek Mohanty)"
plan_item: "L.11"
governed_by:
  - "SUVARNA_CAMPAIGN_PLAN_v1_3.md §4.2 (J1), §5.1 (Track E), §6.3–§6.6"
  - "SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.3 (G1–G15; R1–R11; P1–P13)"
  - "SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md v1.3 §3, §6, §11.7, §12"
  - "decisions N-2, N-3, N-6, D1, D2, D3, D4 ($SUVARNA_HOME/run/DECISIONS.jsonl)"
changelog:
  - "1.0 (2026-09-29): first issue. Packets, write sets and boundaries for lanes E1–E7; approvals named; plan_model detector fields pinned (E3.2, E3.7, E5.1–E5.5, E6.3). Measured today: the build engine's own work is 10 commits on top of l3/kala-layer-briefs, not ~200 (§3); migrations 1094–1096 are unapplied and sit inside L3's reserved range 1070–1119 (§3.3); the tier documents and the Nikaṣa tools are not on main (§4)."
---

# Track E brief — the Nikaṣa Engine session

This brief is the write boundary G4 refers to for every Track E packet. It never contradicts plan v1.3; where it found
the plan's facts out of date it says so (§9) and follows the plan until Strategic Suvarṇa revises it.

## §1 · Scope and done

- **Done = J1-ready:** every Track E row of the J1 checklist (plan §4.2 #1–#6, #9–#13) reads done by its detector, and
  the Conductor hands the native one J1 packet with evidence. The freeze itself is N-8; the reopens are N-4/N-5.
- **Seven lanes:** E1 tooling · E2 clause fixes · E3 build engine · E4 landing and `bo_upaya` · E5 execution tooling ·
  E6 gate detectors (D3) · E7 build identity (D1; the D1 auth PR is E7.1).
- **Queue:** `hq/00_ARCHITECTURE/control/suvarna/state/QUEUE_ENGINE.jsonl`; queue ids `<plan_item>-<kind>-<nnn>`;
  lane branches `suvarna/lane/<queue id>`; worktrees `$SUVARNA_HOME/lanes/<queue id>` (arch §12.2).

## §2 · Rules for every lane

- **Branch base.** A packet that ends in a PR to `main` branches from `suvarna/trunk` (= `main`), never from
  `campaign/nikasha-test` or `campaign/nirmana-engine`: both sit on `l3/kala-layer-briefs` and a PR from them carries
  ~190 foreign commits. Source branches are read with `git show`/`cherry-pick -x` only. Inspector work before E4.1
  lands may branch from `campaign/nikasha-test` (arch §12.2); it re-lands through E4.1. Never edit
  `/Users/Dev/madhav-nikasha` or `/Users/Dev/madhav-engine`; the engine checkout's uncommitted files are not touched.
- **Proof.** Failing-first test plus a recorded mutation run (plan §6.3). Commits `git commit -- <paths>`, one row per
  commit. Fingerprints rotate last (E5.4 once landed).
- **No production writes.** Track E dispatches **no build** (a live build before J1 fails charter §6 precondition 6).
  Schema changes go only by migration, applied by the deploy after the native's merge, verified read-only. Ledgers
  change only by `--emit-gaps` with the withholding list or by a reviewed migration script proven idempotent on a copy.
- **Out of bounds, all lanes:** family assets and their code, data and migrations (charter R8: `ka_gochara`,
  `ka_gochara_resonance`, `ka_vedha_gochara`, `ka_sangam`, `ka_kshetra` and tables, plus claimed prerequisites);
  the `WriterBase` contract (R2); any chart but `482012f1…` (R4); credentials (P1, R10); `CLAUDE.md` except by the
  native-decided PR in §3.2 (E3.2-build-004); the plan and plan model (Strategic's); tiers 1–3 before their agenda is approved.
- **Migrations:** one number at a time per arch §12.5, placeholder on the lane branch, row on the coordination branch;
  every migration file goes through the `migration-guard` agent before its PR opens.
- **Reviews:** a fresh gate reviewer per packet (Opus 5.5 medium; **high** for writer, ledger, auth, reopen and
  algorithm packets); two rejects → Steward. CI green before a PR is marked ready.

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
| E3.2-build-004 | — | `CLAUDE.md` §N.2 "KNOWN BREACH" note (engine D-1), rebased on current `CLAUDE.md`, own PR | **native** decides; not a J1 input |
| E3.3-migrate-001 | E3.3 | after the deploy: read-only check of `_migrations_applied` and the new column, enum and view | `migrations_applied` 1094, 1095 (1096 verified in the same evidence) |
| E3.4-build-001 | E3.4 | R217 (`mark_run_state` writes `build_runs.last_error` on :1240/:1450/:1456), A2b (`mark_asset_error` empty text; site-2 global assets; mock-leak), A3b (runs dispatched with no manifest). Proof on the CI Postgres integration suite; no build is dispatched to manufacture a failure | R217 closed |
| E3.5-build-001… | E3.5 | C1 (crash/orphan/reap; begins with a search, `guardian_cleanup`/`manual reap` have no source hits) and C2 (stuck states). After landing; runs alongside Track B; not a freeze input | event with evidence |
| E3.6-design-001 | E3.6 | R39: the builder's own elevation plan driven by the Build gate's nine checks, `00_ARCHITECTURE/briefs/suvarna/engine/BUILD_ENGINE_ELEVATION_PLAN_v1_0.md`, with its checks run against the engine | R39 closed |
| E3.7 | E3.7 | `suvarna-build --preflight` shows the landing merges in the job image | `deployed_contains` (job) on 001 and 002 |

- **Sequencing:** 001 → 002 (002's migration 1095 follows 1094) ‖ 003; after merge: E3.3 → E3.4 → E3.6 (needs E1.7);
  E3.7 needs E7.2 (the preflight script). Generated files (`nirmana-writer-digests.json`,
  `capability_estate_census.json`) are regenerated on the landing branch by their generator, never cherry-picked.
- **Detector pins:** no landing PR exists yet, so plan_model E3.2 and E3.7 pin the PRs by **head ref**
  (`suvarna/lane/E3.2-build-001/-002/-003`, base `main`) with `prs: []`; L.13's `prs_merged` and `deployed_contains`
  resolve a head ref to its merged PR. Until they do, the items read unknown, never done. Strategic Suvarṇa may add the
  numbers once the PRs open.
- **Write set:** the files above, `platform/supabase/migrations/1094_*`–`1096_*`, their tests. **Boundary:** no other
  writer, no family code, no `WriterBase`/`WriterResult` shape change (A1 stops *reading* `duration_seconds`; the
  field stays).

### 3.3 · Migration numbers — parked for the native
1094–1096 are unapplied (`_migrations_applied`, read 2026-09-29), claimed by no open PR, and **inside L3 Kāla's
reserved range 1070–1119** (coordination branch). Recommendation: renumber them at landing to freshly reserved
cross-cutting numbers (legal: never applied, P4 untouched), and Strategic Suvarṇa updates E3.3 and plan §4.2 #9 in the
same commit. Alternative: the L3 range owner confirms 1094–1096 on the coordination branch. The Steward parks this at
session open; only E3.2-build-001/002's PR opening waits on it.

## §4 · Lane E4 — landing and `bo_upaya` (10–20 h)

`asset_census.py`, `catalog_provenance.py`, `asset_elevation_tracker.py`, `manifest_fingerprint.py`,
`check_migration_ledger_vs_production.py`, the ledgers, the register **and tiers 1–4, the L0 instance v3.0 and the five
pilot briefs** are all absent from `main` today; they live on the `l3/kala-layer-briefs` base. N-3's "split and
retarget" is done by building fresh branches from `main`, not by retargeting #2736.

| Queue id | Plan item | Content | Done (detector) |
|---|---|---|---|
| E4.1-build-001 | E4.1, E4.1c | **code PR**: every governance tool at `campaign/nikasha-test` HEAD with its tests (`platform/scripts/governance/{asset_census,catalog_provenance,hand_row_provenance,ledger_r81_migration,apply_r80_r81_ledger_migration,manifest_fingerprint,check_migration_ledger_vs_production}.py`, `drift_detector.py`/`schema_validator.py` hunks, `__tests__/*`, `r218_*`), `00_ARCHITECTURE/control/asset_elevation_tracker.py`; a base-dependency sweep (every import and path resolves on `main`); a CI job running `platform/scripts/governance/__tests__/` | files on main; `ci.yml` contains `asset_census` |
| E4.1-build-002 | E4.1 | **evidence PR**: the four tiers, L0 instance v3.0, pilot briefs, register v2.8, implementation plan, `nikasha_test/**`, reviews, the `bo_upaya` hand-off. `SESSION_LOG`, `CURRENT_STATE`, `CAPABILITY_MANIFEST` hunks only as Nikaṣa-own rows rebased on `main`; manifest re-fingerprinted last | register on main |
| E4.3-fold-001 | E4.3 | **ledger PR at the named cut**: folds stop on `campaign/nikasha-test` at a recorded commit; `asset_gaps.jsonl`, `asset_certs.jsonl` land; line count and md5 equal old vs new; `NIKASHA_ROOT`/`NIKASHA_REF` re-pointed to `suvarna/trunk` in one step | event with the md5 evidence |
| E4.2-build-001 | E4.2 | `bo_upaya` per the hand-off: restore `replace_prior_rm_dasha_windowed()` before `replace_prior_rm_prescriptions()` (`bo_upaya.py:1942–1945`), rewrite the comment, source-order test, correct the three write-ups and L2 strategy §6 wording. Lease `SUVARNA-E4.2-build-001` on `bo_upaya`. Not migration 1013, not `cr_status.ts`, no live rebuild (that is B.U) | R244 `DEFERRED` with withholding, folded on the merged fix |

- **Sequencing:** 001 first (it unlocks `suvarna/trunk` as the base for E1, E5, E6), then 002, then the cut-over last.
  E4.2 in parallel from day one. PR #2736 stays open until 001–003 merge; closing it is the native's act.

## §5 · Lane E1 — tooling (30–50 h)

| Queue id | Plan item | Content | Done |
|---|---|---|---|
| E1.1-analysis-001 | E1.1 | re-run T1–T5 on today's tooling; publish `00_ARCHITECTURE/control/NIKASHA_T1_T5_SCORECARD.json` (per test: verdict, per-layer cells, inspector commit, ref, population, evidence path) | event with the scorecard |
| E1.2-build-001… | E1.2 | R245 Idem blind spots · R248 full-shape detector match · R249 empty-by-design vs broken · R250 verify the `bg_sarvatobhadra_grid` label | rows closed |
| E1.3-build-001… | E1.3 | R226 `catalog_provenance.py --live` · R228 twelve out-of-range `source_ref`s (annotation only, no serving change) · R229 the 27 unowned tables measured and classified; any registry change it implies is handed to the owning layer's Track A brief | rows closed |
| E1.4-migrate-001 | E1.4 | R251: 19 pilot hand rows and 42 unregistered hand criteria through a reviewed crosswalk migration (R81 pattern) | R251 closed |
| E1.5-analysis-001 | E1.5 | R55 once 1094 is applied: timing verdicts read live | R55 closed |
| E1.6-build-001 | E1.6 | R246 DELETE-FK-child detector, narrow, after E4.2 merges | R246 closed |
| E1.8-analysis-001 | E1.8 | R24: production L3 census (R134) and clean re-runs of all six layers after E1.2–E1.4 | R24 closed |
| E1.7-analysis-001 | E1.7 | T1–T5 re-proved with the tools on `main`; scorecard committed on `main` | `scorecard_pass` |

- **Write set:** `platform/scripts/governance/**` (inspector, provenance, their tests), the scorecard, the
  retrieval-registry `source_ref` annotations (R228 only), the ledgers through E5.2/migration scripts only.
- **Census lock:** every census here goes through `census_lock` and competes with Track A's six censuses; the Conductor
  asks Exec Suvarṇa's Conductor for a slot by tracker note, never runs outside the lock.

## §6 · Lane E2 — founding-document fixes, held for the reopen (20–30 h)

- **E2.1-design-001/002/003:** one agenda per tier, `00_ARCHITECTURE/briefs/suvarna/reopen/REOPEN_AGENDA_T{1,2,3}_v1_0.md`,
  each row with its clause, the chosen remedy and the drafted replacement text, from the D2 ruling
  (`nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md` D2): T1 R01, R72, R76 · T2 R06, R73, R75, R88, R89, R90, R91, R119
  (T2 half), R181/R186/R198 (§7.1 halves) · T3 R08, R09, R10, R65 and R68 (T3 halves), R67, R71 (D3's text), R74, R93,
  R120, R201, R221; closing with them R94, R140, R185, R192, R208. R131, R210, R214 stay deferred. The packet reconciles
  this list against the plan's figure of 32 and reports the count it finds.
- **Combine:** after A.H, each agenda gains the harvested tier gaps assigned to it (v1.1). Strategic Suvarṇa presents it
  for N-4.Tx. Once approved the agenda is closed; later finds become rows for a second round.
- **Apply (plan items J1.1/J1.2/J1.3):** after N-4.Tx, a lane redlines that tier, runs the cross-tier re-render pass
  (counts, gate names, section numbers across tiers, instances, tracker), gets an independent review, and hands it to
  the native for N-5.Tx, strictly T1 → T2 → T3. E2.2 (R71) closes with the T3 re-seal.
- **Write set:** the agenda files; the tier documents only after their agenda's N-4 and only on their lane branch.

## §7 · Lane E5 — execution tooling (30–50 h)

All on `main` via `suvarna/trunk`, each with its test (the paths are the plan-model pins):

| Item | Files | What it must prove |
|---|---|---|
| E5.1 | `platform/scripts/governance/nikasha_certify.py`, `__tests__/test_e5_1_certify.py` | writes arch §12.16 records; refuses a PASS whose criterion has `detector: NONE` or no census run id; refuses N/A not computed by the registry; idempotent on a ledger copy |
| E5.2 | `nikasha_fold.py`, `__tests__/test_e5_2_fold.py` | register state transitions; `--emit-gaps` with the withholding list (`00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json`, today `bo_upaya-Idem.pattern`); computed tallies; fingerprints; drift |
| E5.3 | `suvarna_level_wave.py`, `__tests__/test_e5_3_level_wave.py` | dispatch only via `suvarna-build`; preflight tag/SHA; writer-hash re-check; read-only per-chart lock check; L0 dump, `pg_restore --list` and row-count verification, post-wave diff, impact statement; fail closed. Tested against the builder with `--preflight` and expected-403 dispatches only (clear, `brahmagyan`, other chart). How staleness propagates on a global run is established from `staleness.py` and build history, read-only |
| E5.4 | `manifest_fingerprint.py`, `__tests__/test_e5_4_manifest_per_entry_rotation.py` | rotates each changed entry, not only the root |
| E5.5 | `nikasha_stale_certs.py`, `__tests__/test_e5_5_stale_certs.py` | invalidates a record whose writer hash, upstream cert ids or row-set fingerprint no longer match |

(all under `platform/scripts/governance/`). Sequencing: E5.1 → E5.5; E5.3 after E7.3. Ledger-writing code: Builder at
high effort, gate review high.

## §8 · Lanes E6 and E7

**E6 — gate detectors (50–90 h).** E6.0 is N-22 (native, before E6.5). E6.1: `layers:` and column-pattern
applicability on every entry of `CRITERION_REGISTRY` (`asset_census.py`); generic Null (schema defaults, writer
literal fallbacks, constant columns; never PASS alone), Dens (contract **and** a tier column in the served select;
labelled structural), Ldgr (L0 source presence, L1 build receipt, L2+ constituent resolution generalised from
`msr_referential_integrity.py`), Carr per layer, `Earn.literal_lint` (`check_earned_signal.py`), a real
`Earn.service_state`; the narration lints wired as Narr. E6.2: the rollup (worst of FAIL > ERRORED > NO_DETECTOR >
PARTIAL > PASS; N/A only by rule; no checks = NO_DETECTOR), cells versioned with the registry revision. E6.3:
ELEVATED exact in `asset_elevation_tracker.py` with `__tests__/test_e6_3_elevated_exact.py`; `00_ARCHITECTURE/control/
LEVEL_MAP.json` and `00_ARCHITECTURE/control/FAMILY_ASSETS.json` (family set plus the 16 readers) generated from the
live registry, frozen at J1; a cycle is an error. E6.4: `ledger_e6_4_info_rekey.py` (R81 pattern, on a copy first).
E6.5: an `asset_census.py --registry-check` self-check the `registry_coverage` detector runs. Per-asset semantic
detectors are Track A/I, not here.

**E7 — build identity (8–15 h).** E7.1-build-001: `authorizeChartAccess.ts`, `requireChartPermission.ts`,
`api/cockpit/runs/route.ts` (dispatch needs `'build'`; `clear_before` needs `'all'`), new
`api/cockpit/runs/preflight/route.ts` (`{job_image_tag, deployed_sha}`, authenticated), one migration widening
`chart_grants.permission` to `('view','build')`, tests proving 403 on clear, clear routes, `layer=brahmagyan`, other
charts. `security-reviewer` agent plus gate review at high. E7.2 is the native's (account, grant row, `builder.env`,
`suvarna-build`; the non-secret builder uid recorded in `$SUVARNA_HOME/run/builder_identity.json`). E7.3: the
Monitor's `builder_scope` check in `suvarna_tracker/monitor.py`, on a lane from `suvarna/hq`, merged to hq by merge
commit.

## §9 · Approvals, sequencing, estimates

| Act | Who |
|---|---|
| Packet specs, dispatch, retries, model/effort | Architect writes; Conductor (G1, G2, G8) |
| Gate verdict and fold | Gate reviewer; Scribe (G7); two rejects → Steward |
| Open a PR to `main` | Conductor (G11) |
| Merge to `main`; the deploy follows | **native** (R7) |
| Migration numbering of 1094–1096 (§3.3); `CLAUDE.md` note; closing #2736 | **native** (parked by the Steward) |
| Per-gate applicability rules (E6.0) | **native** (N-22) |
| Reopen agendas and re-seals | **native** (N-4.Tx, N-5.Tx) |
| Builder provisioning (E7.2) | **native** |
| Freeze | **native** (N-8), on the Conductor's J1 packet, presented by Strategic Suvarṇa |

The Steward decides only within G1–G15; G16 (asset briefs) does not apply to Track E.

**Critical path:** E4.1-001 → E1.2/E1.3/E1.4 → E1.8 → E1.7 → E3.6; E3.2 → merge → E3.3 → E1.5; E7.1 → E7.2 → E7.3 →
E5.3/E3.7; E6.1 → E6.2 → E6.5 (+N-22); E5.1 → E5.5 → E6.3; A.H → E2 combine → N-4/N-5 ×3.

**Estimates (plan §5.1 = §6.6):** E1 30–50 · E2 20–30 · E3 40–70 · E4 10–20 · E5 30–50 · E6 50–90 · E7 8–15 =
**190–325 h**. E3 may land lower (10 reviewed commits, not 200); re-estimate after E3.2. **Native merges before J1:
about 11–14 PRs** (E3 ×3–4, E4 ×4, E7 ×1, E3.4 ×1, E1/E5/E6 grouped ×2–3), above plan §6.6's 6–10, which counted only
E3/E4/E7 landings; the Conductor batches where review allows.

**Findings for Strategic Suvarṇa (plan untouched here):** the engine's own delta is 10 commits (plan §3.7 says ~200);
1094–1096 sit in L3's range (§3.3); migration 1096 is not in plan §4.2 #9; the tier documents are not on `main`;
arch §12.2's base rule needs the §2 clarification above; the Engine start prompt still names plan v1.2 and E1–E5 (L.12).
