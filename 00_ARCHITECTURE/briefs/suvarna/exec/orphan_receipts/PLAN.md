---
artifact: D6_ORPHAN_RECEIPTS_PLAN
version: 3.1
status: DRAFT_FOR_REVIEW (v3 plan hash NOT yet approved; the 1.0 and 1.1 hashes are VOID for apply; no data change made)
date: 2026-10-02
lane: suvarna/land/TI-d6-orphan-receipts-001
decision: design review DESIGN_REVIEW_LEGACY_WHOLE_ASSET_RECEIPTS, option (a): D6 owner-path retirement, narrow, per stage
changelog:
  - "3.1 (2026-10-02): rev2 after the independent adversarial review of GATE_V2 (PR #2938 head 5aa2ccefd) and of this executor. (1) The three gate files are re-copied BYTE-IDENTICALLY from gate_v2 5aa2ccefd (new shas below; the marker is now v2 and carries an under_test flag, the gate counts deploy runs on ANY ref, pins the repo, checks current_database() = amjis, run_gated.sh exits 98 for a bad target). (2) SafeOutcome: a `committed` flag is set right after conn.commit(); an interruption (the applied write raising, KeyboardInterrupt, SIGTERM/SIGHUP) after it records `applied` with the warning `outcome_write_failed_after_commit:<ExceptionClassName>`, never `failed`; SIGTERM/SIGHUP/SIGINT are held (signal mask) around the COMMIT and SIGTERM/SIGHUP end the run with SystemExit(128+n) after the right outcome is written. A MISSING outcome.json means check the database (SIGKILL / power loss cannot be handled). (3) `D_twin_integrity_unchanged` now has its own test (and a mutation). (4) outcome.json records `under_test` (from the marker) and `warnings`. New executor sha and plan hashes; the previous v3 values (executor 61a2d613..., plan hash 67d1191b0e901cbdea20e2207e869fb55dcbbe52312facad076ebb6e02ac8f55, gate shas e74683cb... / a9951a29... / 7a1393be...) are VOID for apply."
  - "3.0 (2026-10-02): v3 = the APPLY executor for the S-L1 window, on top of 1.1 (the 1.1 files are not edited in place: v3 is a new commit; the 1.1 executor de4aad0c... and plan hash 29a9e1e5... stay recorded in section 6 as history). SS binding: (1) prerun_gate.py and run_gated.sh are BYTE-IDENTICAL copies of GATE_V2 (PR #2938) plus executor_standards.py (the v1 gate and its tests are removed); (2) main() calls require_gate_launch(...) FIRST and refuses (exit 93) unless started by run_gated.sh; the three gate files are pinned by sha256 in the executor; (3) the plan hash binds the gate shas (bind_gate_into_plan_hash) in addition to the executor and resolver shas; (4) outcome.json (dry_run | applied | failed) in the evidence directory in every mode; (5) ORPH_TEST_EVIDENCE_ROOT set outside pytest is REFUSED (exit 95), not ignored. Resolver SQL unchanged. New executor sha and plan hashes (sections 5, 6)."
  - "1.1 (2026-10-02): SS review of 1.0 (bbf9b90d3): --expect-evidence REQUIRED at --apply (MED); resolver port completed (receipt-build and spec-digest split checks, TS reason labels); --evidence-root ignored outside tests, all created evidence dirs 0700; execute() validates asset/chart itself; section 8 refreshed with the first real dry run; pre-run gate as code (prerun_gate.py + run_gated.sh). New executor sha and plan hash; the 1.0 approval (13dc3c2d..., eba9c7da...) is void."
  - "1.0 (2026-10-02): plan, executor, tests, standing orphan check and resolver port. Nothing was run against the real database (read-only catalog/data reads as suvarna_reader only)."
---

# D6 plan: retire the orphaned `__whole_asset__` receipt rows (ga_positions at S-L1; bo_* at S-L2)

## 0. v3: what changed since 1.1 (for a gate-and-wiring delta review)

v1.1 (head `050eace55`) was accepted after its real dry run; v3 changes ONLY the gate wiring, the outcome file and the test-environment refusal. Every condition (P1-P5, D, V, A, E), the DELETE statements, the transaction, the locks, the before-images, the reversal SQL, `--expect-evidence` REQUIRED at `--apply`, `--min-build-after`, the 0700/0600 evidence modes and `resolver_verdicts.sql` (sha256 `724ef0db39f61799a0bffc325e4babbeeac7918d3ce1896ab031661841b96f23`, unchanged, no defect found) are untouched.

| # | change | where |
|---|---|---|
| 1 | v1 `prerun_gate.py` / `run_gated.sh` replaced by the GATE_V2 files, byte-identical (`cmp` against PR #2938's `gate_v2/`, sha256 below); `executor_standards.py` added byte-identical; `tests/test_prerun_gate.py` (v1 gate tests) deleted (gate_v2 carries its own tests) | `prerun_gate.py`, `run_gated.sh`, `executor_standards.py` |
| 2 | `main()` calls `launch_gate()` FIRST (before argument parsing): refuses with exit 93 unless `executor_standards.py` equals its pin and `GATE_V2_LAUNCH` verifies via `require_gate_launch(expected_gate_sha, expected_launcher_sha)` against the live files AND the pins in `GATE_PINS` | `orphan_receipts_exec.py` (`GATE_PINS`, `launch_gate`, `main`) |
| 3 | plan hash = `bind_gate_into_plan_hash(sha256(plan text + "\n" + DIFF), fingerprint())`; the plan text now also names the three gate shas (so a changed `executor_standards.py` changes the hash too) | `render_plan`, `plan_hash`, `plan_hash_unbound`, `gate_shas`, `make_plan.py`, `plan.txt` |
| 4 | `outcome.json` (`executor_outcome_v1`: status `dry_run` / `applied` / `failed`, UTC, executor sha, plan hash, gate shas, evidence digest, failed check names) written by `outcome_guard` (subclass `SafeOutcome`, see below) in every mode and on every failure / `SystemExit` / silent return. The run directory is now created BEFORE any argument gate and any connection (`make_run_dir`, `mkdir` without `exist_ok`: a collision aborts and can never overwrite another run's evidence or outcome); `write_evidence` writes into it | `execute`, `SafeOutcome`, `conclude`, `refuse`, `make_run_dir`, `write_evidence` |
| 5 | `ORPH_TEST_EVIDENCE_ROOT` set (even empty) and `PYTEST_CURRENT_TEST` absent: REFUSED, exit 95, clear message (no silent ignore, no redirect); set but empty inside pytest: also refused (never falls back to the real root). Unset: the real root, `--evidence-root` ignored, as before | `resolve_evidence_root`, first statement of `execute` |
| 6 | tests: gate wiring (`tests/test_gate_wiring.py`), outcome tests and evidence-root refusals (`tests/test_orphan_receipts_exec.py`), mutation proof extended to the new rules (`tests/mutation_proof.py`) | `tests/` |

Behaviour notes for the reviewer.
- rev2 outcome rules. `SafeOutcome.mark_committed()` runs IMMEDIATELY after `conn.commit()`. From then on an exception (also `KeyboardInterrupt`), a SIGTERM/SIGHUP, or a block that returns without declaring an outcome records `applied` with the warning `outcome_write_failed_after_commit:<ExceptionClassName>` (and a stderr line `THE COMMIT HAPPENED`), never `failed`; before the commit it records `failed` as before. SIGTERM, SIGHUP and SIGINT are blocked (`pthread_sigmask`) around `commit()` + `mark_committed()` so none can land between the COMMIT and its bookkeeping; `main()` installs handlers that turn SIGTERM/SIGHUP into `SystemExit(128+n)` after the outcome is written. A MISSING `outcome.json` therefore means "check the database" (SIGKILL, power loss and a crash inside the final instructions leave none; they are not handled and cannot be). `outcome.json` also carries `under_test` (the launch marker's flag: true only when `run_gated.sh` was started with `GATE_V2_UNDER_TEST=1`) and `warnings`.
- `SafeOutcome` otherwise only adds that an `OSError` while writing `outcome.json` is recorded as a warning (`write_error`) and never replaces the real result or the real exception; in particular a failed outcome write AFTER `COMMIT` cannot turn a committed apply into an error (the printed result carries `THE COMMIT HAPPENED`). The vendored `executor_standards.py` is imported unmodified.
- A dry run without `--min-build-after` (exit 3, the counterfactual) is recorded as `failed` with check `counterfactual_no_min_build_after`: it is not a rehearsal of `--apply`. `dry_run` is recorded only for a dry run in which every check holds AND `--min-build-after` was given.
- No `outcome.json` exists for a run that stops before its evidence directory exists: an invalid `--asset`/`--chart`, an argparse error, the launch refusal (93), the test-variable refusal (95), or an evidence root that cannot be created (exit 1, `ABORTED_ROLLED_BACK`, nothing was connected). Those carry the exit code and a stderr message only.
- Convention-grade, as in GATE_V2: the launch marker guards against accidents (direct start, stale or edited gate), not against someone who can run python; `PYTEST_CURRENT_TEST` is likewise an accident guard.

| item | value |
|---|---|
| v3 executor `orphan_receipts_exec.py` sha256 | `d94588d6d4f7cc277ae5dbfda6a87a0b9964b8239fa36d8620845e0eecb71c61` |
| `resolver_verdicts.sql` sha256 | `724ef0db39f61799a0bffc325e4babbeeac7918d3ce1896ab031661841b96f23` (unchanged) |
| `prerun_gate.py` sha256 (GATE_V2) | `ba65d82a338257bd7b3b1ae37df312fb382ef548291a211eadbc2538a987ef73` |
| `run_gated.sh` sha256 (GATE_V2) | `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` |
| `executor_standards.py` sha256 (GATE_V2) | `7ca8ea9cc3422f41d38ced27f6501d666dcce78918e38e1d255b8dabcdd3c38d` |
| **v3 plan hash, ga_positions on 482012f1-710e-4a25-994a-93821f5871aa** | `50d5710a17b210d37e21afdd6115f131f52560b412f77e36c74cf4d70422cd36` |

## 1. Purpose

`asset_provenance_receipts` and `asset_freshness` are keyed `(asset_id, scope_key, partition_key)`. While an asset's registry row declared no `natural_key_partition`, the provenance writer stored its receipt under the key `__whole_asset__` (W). Declaring a partition afterwards made the next build write a different key, so the old W row (`receipt_state = unknown`, freshness `stale`) was orphaned by construction; nothing ever deletes it. The served-generation resolver (`served_generation.ts`, `classifyAssetGeneration`) requires EVERY receipt row of an asset to be proven, so on the canonical chart the orphan alone makes ga_positions `receipt_not_proven` and withholds its facts from every fenced read. Rebuilding does not help (the rebuild upserts the declared key again; the W row stays). This plan removes exactly the orphan pair (one receipt row plus its freshness twin) with one reviewed, hash-pinned, reversible owner-path transaction.

It removes an `unknown`/non-fresh row. It never creates, edits or promotes a receipt, so no `proven`/`fresh` state is fabricated (596 header doctrine and CLAUDE.md N.7/N.8 preserved).

## 2. Exact rows (canonical chart `482012f1-710e-4a25-994a-93821f5871aa`; read-only as `suvarna_reader`, 2026-10-02; no digest values, no birth data)

ga_positions (S-L1), both keyed asset_id `ga_positions`, chart (= scope) as in the heading, partition_key `__whole_asset__`:

| table | key | state | observed_at (UTC) | other non-secret facts |
|---|---|---|---|---|
| asset_provenance_receipts | W (15 chars) | `unknown` | 2026-09-07 01:07:39.668056 | build `e1c5109f-f60d-4548-b0d6-bb8ce00945ab` (completed, `build`, created 01:07:21); receipt_version `nirmana-provenance-receipt-v2`; output_digest_spec_sha256 NULL; unknown_reasons `output_digest_spec_unavailable, output_digest_unavailable, partition_digest_unavailable, partition_undeclared` |
| asset_freshness | W | `stale` | 2026-09-07 03:30:26.252461 | reasons the four above plus `registry_changed` |

Untouched, same asset and chart, partition key = the registry declaration (108 chars): receipt `proven`, observed 2026-09-07 08:37:20.895985, build `0ac321ee-192d-4c86-bd67-495613a76780` (a `skip_no_delta` re-attribution), spec active; freshness `fresh`, observed 2026-09-07 03:42:46.579549. (These are the pre-S-L1 rows: the S-L1 rebuild rewrites them, see section 5.)

Resolver verdict for ga_positions today: `receipt_not_proven` (2 partitions). Whole chart today: 37 RESOLVED / 15 unresolved. S-L1 asset set (19 assets): 17 RESOLVED, 2 not (ga_positions: this orphan; ga_strength: `receipt_spec_retired`, a different defect that S-L1's ga_strength rebuild fixes).

Before-image shape (written by the executor before any DELETE; `before_images.json`):
`{"asset_id", "chart_id", "partition_key": "__whole_asset__", "tables": {"asset_provenance_receipts": {"columns": [{"name","type","generated"}...], "rows": [ <to_jsonb of the full row, ALL columns incl. generated scope_key> ]}, "asset_freshness": {...same...}}}` plus `reversal.sql`, `SHA256SUMS`, `result.json`.

## 3. Conditions (each is a CHECK that REFUSES; there is a test per refusal in `tests/test_orphan_receipts_exec.py`)

| id | condition | refuses when |
|---|---|---|
| args | `--asset` and `--chart` explicit (no default); `--apply` needs `--expect-plan` == plan hash, `--min-build-after` (tz-aware) | any missing / hash differs (refused before any connection) |
| P1 | registry `natural_key_partition` for the asset is non-empty and is not `__whole_asset__` | the registry declares no partition: the W row is the live key, not an orphan (also: asset not in registry) |
| P2 | the W receipt is `unknown` and its twin freshness is `stale`/`unknown` | the W row is proven/fresh: it is not blocking anything and is never deleted |
| P3 | a declared-partition receipt exists, `proven`, freshness `fresh`, from a `completed` build with a `build_run_assets` row, whose build is newer than the W row's build AND whose receipt `observed_at` and build `created_at` are `> --min-build-after` | none exists / not proven / not fresh / build not completed / not newer than the orphan / not newer than `--min-build-after` (so the old 09-07 receipts can never satisfy "from the S-L1 rebuild") |
| P4 | exactly 1 receipt row and exactly 1 freshness twin for (asset, chart, `__whole_asset__`) | 0 or 2 of either |
| P5 | zero `build_runs` with `state IN ('planned','running','paused')` on ANY chart (real column `build_runs.state`; the table has a unique partial index of exactly these states per chart) | any |
| D | both DELETE rowcounts are exactly 1; the row-key + md5-of-whole-row map of BOTH tables after equals the map before minus exactly the two removed keys (no other row of any table changed, any column); chart-scoped receipt<->freshness twin integrity unchanged | any other row differs, any rowcount other than 1/1 |
| V | resolver verdicts (SQL port v1.1 of `classifyAssetGeneration`: per-partition defects in `partition_key` order with the TS reason names, then the split checks on rows build, receipt build and spec digest; `resolver_verdicts.sql`) computed inside the transaction for ALL assets before and after; the diff is EXACTLY `{<asset>: receipt_not_proven -> RESOLVED}` | any other asset changes (either direction), or this asset does not become RESOLVED |
| A | snapshot A (before everything) vs snapshot B (after the work, after the transient membership is revoked): `relacl` (aclexplode incl. grantable), owner, `relrowsecurity`/`relforcerowsecurity`, `pg_policy` rows, `pg_auth_members` rows, over every public relation: all diffs empty | any difference |
| E | `--expect-evidence <digest>` is REQUIRED at `--apply` (refused before any connection if absent) and must equal the evidence digest this run computes | absent (refused at parse and again in `execute()`) or differs |
| gate (v3) | the run was started by `run_gated.sh` after a passing GATE_V2; `executor_standards.py`, `prerun_gate.py`, `run_gated.sh` are the pinned files | no verifying `GATE_V2_LAUNCH` (missing, malformed, check mismatch, stale > 6 h, from the future, shas differ from the live files or from `GATE_PINS`): exit 93, before the arguments are parsed |
| test env (v3) | `ORPH_TEST_EVIDENCE_ROOT` is unset (or set inside a pytest run with a value) | set outside pytest, or set empty: exit 95 |
| outcome (v3) | `outcome.json` is written into the evidence directory in every mode | never silently skipped: failure, exception, `SystemExit`, silent return all record `failed` (a write error is a warning, never a masked result) |
| evidence | before-images + reversal SQL written (0700 dir, 0600 files) BEFORE any DELETE | cannot be written: ABORT + ROLLBACK, in both modes |

One transaction; `SET LOCAL lock_timeout = '5s'`, `statement_timeout = '5s'`, `search_path = pg_catalog, pg_temp`, `TimeZone = 'UTC'`. `--dry-run` ALWAYS ends in ROLLBACK. `--apply` COMMITs only if every check holds, otherwise ROLLBACK and exit 1.

Decision for SS (strike if unwanted): after `SET LOCAL ROLE amjis_app` the executor takes `LOCK TABLE asset_provenance_receipts, asset_freshness, build_runs IN SHARE ROW EXCLUSIVE MODE` (readers are not blocked; writers, i.e. a builder or a build start, wait). This makes P5 race-free (no build can start between the check and the DELETE) and bounds the window to a few seconds; if the lock is not obtained in 5 s the run fails and changes nothing.

## 4. Mechanism (owner path, copied from `ChartGrants/cg_exec.py`)

The only role able to DELETE from either table is the table owner `amjis_app` (login role; `data_plane_builder` holds only SELECT/INSERT/UPDATE, a DB test pins DELETE as refused). The executor, connected as the admin in-process (password fetched from Secret Manager inside the process, never printed, logged or saved; proxy 127.0.0.1:5433): snapshot A; `GRANT amjis_app TO <session user>` only if not already a member; `SET LOCAL ROLE amjis_app`; locks; before-images; checks; DELETEs; `RESET ROLE`; `REVOKE` only what it granted; snapshot B. Rendered statement-by-statement in `plan.txt` (current rendering below). Ownership read from the catalog as `suvarna_reader`: both receipt tables, `build_runs`, `build_run_assets`, `asset_registry`, `asset_output_digest_specs` are owned by `amjis_app`; no RLS, no policies, no triggers on the two receipt tables, no FK referencing either.

## 4a. Pre-run gate (code, not a look): GATE_V2

The real dry run and the real apply MUST be started as `./run_gated.sh python3 orphan_receipts_exec.py <executor args>` (from this folder). The three files are byte-identical copies of `gate_v2/` (PR #2938, `GATE_VERSION = "GATE_V2"`; its README is the specification, its `tests/mutation_proof.py` proves the gate rules):

| file | sha256 |
|---|---|
| `prerun_gate.py` | `ba65d82a338257bd7b3b1ae37df312fb382ef548291a211eadbc2538a987ef73` |
| `run_gated.sh` | `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` |
| `executor_standards.py` | `7ca8ea9cc3422f41d38ced27f6501d666dcce78918e38e1d255b8dabcdd3c38d` |

What it does in one invocation, read-only and fail-closed: `run_gated.sh` (`set -euo pipefail`, refuses the test environment with exit 95, resolves python3 / gh / psql / bash once as absolute paths and prints them) runs `prerun_gate.py`, which reads (a) the `deploy.yml` runs on `main` whose status is not `completed` (union by `databaseId` of the newest 100 and one `--status` query per non-completed status) and (b) `build_runs` in state `planned/running/paused` on ANY chart through `psql` as `suvarna_reader` (`pgenv.sh` sourced in a subshell with every ambient `PG*` removed; the session role must be exactly `suvarna_reader`), prints both counts to stderr and exits 0 only if both are 0. Only then does `run_gated.sh` set `GATE_V2_LAUNCH` and `exec` the target; otherwise the target is NOT started and the gate's exit code (1 non-zero count, 2 read failure, 94 missing binary, 95 test env, 96 wrong role, 97 pgenv) is returned.

The executor's side (v3): `main()` calls `launch_gate()` first. It refuses with exit 93 unless `executor_standards.py` equals its pin and `require_gate_launch(expected_gate_sha, expected_launcher_sha)` accepts `GATE_V2_LAUNCH` (check recomputes, shas equal the live gate files AND the sha256 pinned in `GATE_PINS`, not from the future, not older than 6 hours). The gate and launcher shas are folded into the plan hash with `bind_gate_into_plan_hash`, and the plan text names all three gate shas, so editing any gate file after review changes the plan the operator approved. The executor's own P5 (builds in flight, inside the transaction, with the table locks) remains the second, race-free line. The gate is a point-in-time read (a deploy or build can start one second later); the launch marker is an accident guard, not authentication. The same gate is meant for the other production executors (cg_exec-style, F-A2, G-IDX, the dispatch wrapper); SS binds that for them.

## 5. Apply order (a named step of S-L1: "S-L1.RETIRE-ORPHAN-RECEIPTS")

ONLY AFTER the ga_positions S-L1 rebuild is verified by direct DB read (new run `completed`, its `build_run_assets` row `complete`/`build`, the declared-partition receipt `proven`/`fresh`, the digest checks LC-1..LC-4), and BEFORE any served-surface acceptance read (those go through the fence and would otherwise see no ga_positions). Retiring earlier would serve the old 09-07 rows once and then flip again.

1. Record `T0` = the instant the S-L1 ga_positions rebuild was dispatched (UTC, with offset). That is `--min-build-after`.
2. After the rebuild is verified: `./run_gated.sh python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --dry-run --min-build-after <T0>` (`<T0>` = the S-L1 `ga_positions` dispatch time, UTC with offset); read the printed JSON: expect `status DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`, exit 0, `verdict_diff == {"ga_positions": ["receipt_not_proven", "RESOLVED"]}`, rowcounts 1/1, all A diffs 0, `evidence_digest`.
3. SS approves the plan hash (section 6) and the dry-run evidence.
4. `./run_gated.sh python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --apply --expect-plan 50d5710a17b210d37e21afdd6115f131f52560b412f77e36c74cf4d70422cd36 --min-build-after <T0> --expect-evidence <digest from step 2>` (`--expect-evidence` is mandatory); expect `COMMITTED`.
5. Read-only after commit: `orphan_count.sql` no longer lists ga_positions; `resolver_verdicts.sql` shows ga_positions RESOLVED; then served-surface acceptance (inquiry lifecycle tokens and sessions pinned to the old generation see a changed generation identity: fail closed, in-flight inquiries restart).

S-L2: the same executor, `--asset bo_laksana | bo_sangati | bo_cgm_motifs | bo_upaya`, one apply each after that asset's S-L2 rebuild is verified. `bo_upaya` must additionally have been rebuilt under its CURRENT spec (`e73b69a6`; its declared receipt is under a retired spec today) or V refuses (the asset would not become RESOLVED). `bo_sangati`'s declared receipt was rebuilt 09-11 (before S-L2): only `--min-build-after` distinguishes it from the S-L2 rebuild, which is why the parameter is mandatory. Plan hashes for these (computed offline; valid only while the executor, `resolver_verdicts.sql` and the three gate files are byte-identical to this PR; re-run `make_plan.py --asset <a>`; the v1.1 hashes of these four are void):

| asset | plan hash (chart 482012f1-710e-4a25-994a-93821f5871aa) |
|---|---|
| bo_laksana | `2c03f0238788dbc22a3154a3e431b6a9f74a1bfbebc5fa43ca72b0d094adda20` |
| bo_sangati | `0b640586a7cd1ff224d296671becf2bc82d7ed1a260819986ce10d983111ec35` |
| bo_cgm_motifs | `fa2a0ac5de45430ba33fb88850837a3f1e2c569c97e55db482f6c61aa472a9a4` |
| bo_upaya | `c60cd45a625545372f0b18abc7e3cc478a6f93390f58011be949c00a655883d1` |

## 6. Plan hash (what is bound, what is not)

- `plan_text` = `plan.txt` (rendered by `render_plan()` for the asset and chart; embeds the executor sha256, the `resolver_verdicts.sql` sha256 and the three gate-file sha256).
- `DIFF` (static) = `['asset_freshness|ga_positions|482012f1-710e-4a25-994a-93821f5871aa|__whole_asset__|present->absent', 'asset_provenance_receipts|ga_positions|482012f1-710e-4a25-994a-93821f5871aa|__whole_asset__|present->absent', 'resolver_verdict|ga_positions|receipt_not_proven->RESOLVED']`.
- **plan hash = `bind_gate_into_plan_hash(sha256(plan_text + "\n" + json.dumps(DIFF)), {prerun_gate.py sha256, run_gated.sh sha256})`** = `sha256("|".join([sha256(plan_text + "\n" + DIFF), prerun_gate_sha256, run_gated_sha256]))`, computed WITHOUT the database (`python3 make_plan.py`; the executor computes the same value and refuses `--apply` unless `--expect-plan` equals it). It binds: the exact statements, the asset and chart, the executor code, the resolver port, all three gate files (the two launch files twice: in the text and by the fold-in), and the expected verdict transition. `make_plan.py` also prints the value before the fold-in (the v1.1 formula) for reference only.

| item | value |
|---|---|
| executor `orphan_receipts_exec.py` sha256 (v3) | `d94588d6d4f7cc277ae5dbfda6a87a0b9964b8239fa36d8620845e0eecb71c61` |
| `resolver_verdicts.sql` sha256 | `724ef0db39f61799a0bffc325e4babbeeac7918d3ce1896ab031661841b96f23` |
| `prerun_gate.py` / `run_gated.sh` / `executor_standards.py` sha256 | `ba65d82a338257bd7b3b1ae37df312fb382ef548291a211eadbc2538a987ef73` / `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` / `7ca8ea9cc3422f41d38ced27f6501d666dcce78918e38e1d255b8dabcdd3c38d` |
| **plan hash v3, ga_positions on 482012f1-710e-4a25-994a-93821f5871aa** | `50d5710a17b210d37e21afdd6115f131f52560b412f77e36c74cf4d70422cd36` |

History (all VOID for apply; kept as the record): v1.0 executor `eba9c7da...`, plan hash `13dc3c2d...`; v1.1 (head `050eace55`) executor `de4aad0cdec65ed91c2f1569a658008c0fa1b8eae24b1fd0849c19f656aef9d2`, plan hash `29a9e1e5d08a006c1f58255a61cf8c7f6c1e0d0138279268500b33250d3e9967` (its real dry run ran and was accepted by SS).

DB-dependent, computed at dry-run/apply time and NOT in the plan hash: the before-images (their sha256 are printed and in `SHA256SUMS`), the reversal SQL, the verdict diff, rowcounts, the ACL/owner/RLS/policy/membership snapshots, and `--min-build-after`. They are bound by `evidence_digest` = sha256 of canonical JSON of {asset, chart, min_build_after, plan hash, executor sha, before-images sha, reversal sha, verdict diff, chart-scoped counts before/after, per-check pass/fail}. Pass the dry run's digest as `--expect-evidence` to apply so the apply provably runs against the state the dry run showed (the digest contains no timestamp, so identical state gives an identical digest).

If the executor, `resolver_verdicts.sql` or any of the three gate files changes by one byte, the plan hash changes and SS must re-approve (`tests` pin `plan.txt` and this file's quoted hashes to the committed code).

## 7. Reversal

`reversal.sql` (in the evidence directory, sha256 recorded) re-inserts both rows from the before-images (every non-generated column as a typed literal; `scope_key` is GENERATED and recomputes) inside one `BEGIN; SET LOCAL TimeZone='UTC'; SET LOCAL ROLE amjis_app; INSERT...; INSERT...; COMMIT;`. Run through the same owner path (transient membership). Tested on a disposable Postgres: after `--apply` then `reversal.sql`, a md5-of-every-row image of every table plus the ACL/RLS/policy/membership catalogs is byte-identical to the pre-apply image. After reversal the resolver returns ga_positions to `receipt_not_proven`.

## 8. What the dry run shows, and what it CANNOT show today

Printed JSON (never row content, never the 108-char partition text, never a credential): `status`, `failed_checks` / `skipped_checks`, every check with its detail, `rowcounts` (orphan rows found, DELETE rowcounts, chart-scoped counts before/after, table totals), `verdict_diff`, `verdict_counts` before/after, `acl_diff` and the rls/policy/membership/owner diff counts, `before_images` (dir + path + sha256 of each file), `evidence_digest`, `plan_hash`, `executor_sha256`. Exit codes: 0 all hold / committed; 1 apply refused or aborted; 2 dry-run refused; 3 dry-run counterfactual (no `--min-build-after`).

Today (2026-10-02, before the S-L1 rebuild) the later declared-partition receipt that P3 requires does not exist: the only declared receipt is the pre-S-L1 one from 2026-09-07. Therefore:

- A real dry run NOW with `--min-build-after <any instant after 2026-09-07 08:37 UTC>` is expected to REFUSE at P3 (`after_min_build_after: false`, `newer_than_orphan_build: true`), issue no DELETE, and write the before-images + reversal SQL. P1, P2, P4, P5 are expected to hold (registry declares the partition; W rows `unknown`/`stale`; 1 and 1; zero planned/running/paused runs; `build_runs` by state, re-read as `suvarna_reader` 2026-10-02 after the first review: 292 completed, 422 failed, 14 stopped, 0 planned, 0 running, 0 paused). That run shows the refusal and the exact before-images.
- A real dry run NOW without `--min-build-after` is a counterfactual (exit 3): P3 is evaluated without the rebuild gate, so every check is expected to hold and the verdict diff is expected to be `{ga_positions: receipt_not_proven -> RESOLVED}` (the design review's counterfactual: 37/15 -> 38/14). It proves the mechanism and the blast radius on the live data but is not a rehearsal of `--apply`, which would refuse.
- The rehearsal that matters (step 2 of section 5, `--min-build-after <T0>`) can only run AFTER the S-L1 ga_positions rebuild. It is expected to be run, once SS approves the hash, both now (the refusal and the before-images) and after the rebuild.

Not verifiable without the real run: that `postgres` can still `GRANT amjis_app` and `SET LOCAL ROLE` on the current Cloud SQL major version (taken from the `cg_exec.py` precedent; on PostgreSQL 16+ a CREATEROLE-only admin cannot grant an arbitrary role, the executor then fails before any change); whether the 5 s statement timeout is enough for the verdict query on production (it took 0.9 s as `suvarna_reader`); any event trigger / audit extension on admin DML (not visible to `suvarna_reader`).

### Dry run 2026-10-02T01:35:31Z (recorded as reported by Exec Suvarna; not run by the author of this change)

The first real dry run, with the 1.0 executor `eba9c7da...`: REFUSED at P3 as designed; orphan rows 1 / 1; ACL, membership, owner, policy and RLS diffs empty; the admin path (transient `amjis_app` membership, `SET LOCAL ROLE`) worked on PostgreSQL 15.18; evidence digest `66641f6f...`; evidence directory `ga_positions_482012f1_20261002T013531943634Z`. That run used the 1.0 executor, so it does not bind this version: a new dry run with the new sha (section 6) is required before any approval. At the time of this change `prerun_gate.py`, run live (read-only), printed `deploy_runs_not_completed=2`, `build_runs_in_flight=0` and exited 1: it blocks a run while a deploy is in flight.

### What the v3 dry run will look like after the S-L1 rebuild

`./run_gated.sh python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --dry-run --min-build-after <T0>`:

- stderr (the gate, then the launcher): `run_gated: python3=... gh=... psql=... bash=...`, `deploy_runs_not_completed=0`, `build_runs_in_flight=0`, `GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK`, `run_gated: gate OK; GATE_V2_LAUNCH set; starting target`. If any count is non-zero or any read fails: `GATE_V2 FAIL ...`, `run_gated: gate exit=<n>; target NOT started`, and nothing else runs.
- stdout: the diff JSON, exit 0, `status DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`, `failed_checks []`, `skipped_checks []`, every check `ok: true`; `verdict_diff == {"ga_positions": ["receipt_not_proven", "RESOLVED"]}`; `rowcounts`: orphan rows 1 / 1, DELETE rowcounts 1 / 1, chart-scoped receipts and freshness each one fewer after than before; `acl_diff []` and the rls / policy / membership / owner diffs 0 (the transient `amjis_app` membership is granted and revoked inside the transaction, `transient_membership_granted` true if the admin is not already a member); `evidence_digest` (64 hex); `plan_hash` = the v3 hash; `outcome_file`.
- the evidence directory (`/Users/Dev/suvarna-evidence/OrphanReceipts/ga_positions_482012f1_<UTC ts>/`, 0700): `before_images.json`, `reversal.sql`, `SHA256SUMS`, `result.json`, and `outcome.json` (0600) with `status: dry_run`, the executor and gate shas, the plan hash, the same `evidence_digest`, `failed_checks: []`.
- Before the rebuild (the declared receipt is still the 2026-09-07 one) the same command refuses at P3: exit 2, `outcome.json` `status: failed`, `failed_checks: ["P3_later_proven_declared_receipt"]`, before-images still written; without `--min-build-after` it is the counterfactual (exit 3, outcome `failed` with `counterfactual_no_min_build_after`).

### Apply requirements (v3)

`./run_gated.sh python3 orphan_receipts_exec.py ... --apply --expect-plan <v3 hash> --min-build-after <T0> --expect-evidence <digest of the accepted v3 dry run>`: all three flags mandatory (each refusal is recorded in `outcome.json`: `args_expect_plan_mismatch`, `args_min_build_after_missing`, `args_min_build_after_not_tz_aware`, `args_expect_evidence_missing`); the gate must pass; `<T0>` is the S-L1 `ga_positions` dispatch time; a v3 dry run (not the v1.1 one: the digest binds the plan hash) must precede it. A committed apply writes `outcome.json` `status: applied`.

## 9. Not in scope / not done

No data change. No migration, no registry edit, no code change to `served_generation.ts`, `provenance.py`, or the orchestrator (the frozen orchestrator contract is untouched). The resolver fix (option b: ignore orphan partitions at serve time) and the writer-side retirement (option c) are separate native decisions. Global-scope orphans (`chart_id IS NULL`; one pair, `bg_formula_constants`) are out of scope: the chart resolver does not read them.

## 10. Verification performed

- 142 tests (119 executor on a disposable local PostgreSQL, 23 gate-wiring / launch / plan-binding tests that need no database) pass on PostgreSQL 15 (initdb in a temp dir, own port; non-superuser CREATEROLE admin so the transient GRANT/REVOKE of `amjis_app` is exercised) and the same suite on PostgreSQL 17 (superuser admin). All v1.1 coverage is retained: happy path, rowcounts, before-image content/modes/hashes, reversal byte-for-byte, dry-run byte-identity, generalisation to a second asset, chart scoping, every refusal of section 3, `--expect-evidence` required, `execute()` parameter validation, evidence modes under a permissive umask, resolver split cases. The v1 gate tests (23) are replaced by the wiring tests; the GATE_V2 gate itself is tested in `gate_v2/tests` (PR #2938).
- Mutation proof (`tests/mutation_proof.py`): 42 mutations (the 34 above plus 8 for rev2: twin-integrity check, commit marker, applied-after-commit recording, signal mask, signal handlers, launch fingerprint to execute, under_test recording and refusal), each turns its test red (every one first proven green un-mutated): the 11 v1.1 executor/resolver rules kept (P5, P3, V, A, P1, `--expect-evidence` optional x2, E compare, `execute()` validation, resolver receipt-build and spec-digest splits) plus 23 new: launch check removed / moved after argument parsing, marker verification bypassed, gate / launcher / `executor_standards.py` pin not enforced, a pinned sha changed, a gate file edited (no longer byte-identical), plan hash not folding the gate fingerprint, plan text not naming the standards sha, outcome not declared for dry run / apply, failed outcome losing its check names, counterfactual recorded as dry_run, argument refusals and the naive-timezone refusal not recorded, an outcome write error masking the result, run-directory reuse on collision, `outcome_guard` not recording an exception or a silent return, the evidence-root variable honoured outside pytest, an empty value falling back to the real root, the flag honoured without the variable. The two v1.1 gate mutations moved to `gate_v2/tests/mutation_proof.py` (19 mutations there).
- v3 specific tests: the three gate files equal the gate_v2 shas and the executor pins; the plan hash changes with each gate sha and equals `bind_gate_into_plan_hash`; `launch_gate` refuses no / empty / malformed / forged / stale / future markers, a marker made over an edited gate file, and live files that differ from the pins; the real CLI as a subprocess is refused (93) when started directly (also for `--help`), with an edited `executor_standards.py` or gate file even with a marker made for it, and with the stray test variable (95); a valid marker passes the launch check and the refusal is recorded; `run_gated.sh` with PATH shims for gh / psql / python3 starts the executor only when the gate passes (deploy in flight, build in flight, wrong role: not started); `outcome.json` in dry run, apply, refused apply and dry run, counterfactual, every argument refusal, a failed connection (exception class only, never its message), an exception and a `SystemExit` inside the transaction, a lock timeout; an unwritable `outcome.json` never masks a committed apply; two runs in the same instant never overwrite each other's outcome.
- Fixture tables are the production definitions as read from the catalog (`\d`), see `tests/fixture_schema.py` for the two deliberately minimal tables.
- Read-only as `suvarna_reader`: `orphan_count.sql` and `resolver_verdicts.sql` run against production (README.md); the executor itself was never run against any real database by this work, and the admin secret was never read.

## 11. Rendered plan (`plan.txt`, hash input)

```
-- plan: retire the ORPHANED legacy __whole_asset__ receipt row and its asset_freshness twin for asset ga_positions on chart 482012f1-710e-4a25-994a-93821f5871aa (data rows only: no grant, no schema, no code, no other row of any table)
SET LOCAL search_path = pg_catalog, pg_temp
SET LOCAL lock_timeout = '5s'
SET LOCAL statement_timeout = '5s'
SET LOCAL TimeZone = 'UTC'
-- snapshot A (session user): relacl + owner of every public relation, relrowsecurity/relforcerowsecurity, pg_policy, pg_auth_members
-- membership: GRANT amjis_app TO <session user> only if missing; REVOKE before snapshot B only if granted here
SET LOCAL ROLE amjis_app
LOCK TABLE public.asset_provenance_receipts, public.asset_freshness, public.build_runs IN SHARE ROW EXCLUSIVE MODE
-- before-images (all columns, JSON) of both rows + reversal INSERT SQL written to the evidence directory BEFORE any DELETE; if unwritable: abort + ROLLBACK
-- resolver port (resolver_verdicts.sql, chart-parameterised) run for ALL assets: verdicts A; row-key+md5 map of both tables A
-- pre-checks (any failure: no DELETE is issued, ROLLBACK):
--   P1 registry declares a non-empty natural_key_partition for the asset, != '__whole_asset__'
--   P2 the __whole_asset__ receipt is receipt_state='unknown' and its twin freshness_state in ('stale','unknown') (never a proven/fresh row)
--   P3 a PROVEN declared-partition receipt exists with freshness 'fresh', from a COMPLETED build that is newer than the __whole_asset__ row's build
--      AND its receipt observed_at and its build created_at are > --min-build-after (required at --apply; a runtime parameter, tz-aware, bound by the evidence digest; a --dry-run without it is a counterfactual only, exit 3)
--   P4 exactly 1 receipt row and exactly 1 freshness twin for (asset, chart, '__whole_asset__')
--   P5 zero build_runs in state planned/running/paused on ANY chart
DELETE FROM public.asset_freshness WHERE asset_id = 'ga_positions' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid AND partition_key = '__whole_asset__' AND freshness_state IN ('stale','unknown')   -- rowcount must be 1
DELETE FROM public.asset_provenance_receipts WHERE asset_id = 'ga_positions' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid AND partition_key = '__whole_asset__' AND receipt_state = 'unknown'   -- rowcount must be 1
-- resolver port again: verdicts B; row-key+md5 map B
RESET ROLE
-- REVOKE amjis_app FROM <session user> only if granted here; snapshot B
-- commit only if: both DELETE rowcounts == 1; the row-key+md5 diff of BOTH tables is exactly the two removed keys (no other row of any table changed); the per-asset verdict diff over ALL assets is exactly {ga_positions: receipt_not_proven -> RESOLVED}; relacl, owner, relrowsecurity, relforcerowsecurity, pg_policy and pg_auth_members diffs between snapshot A and B are all empty; chart-scoped receipt<->freshness twin integrity unchanged
-- --dry-run: the same statements, then ROLLBACK, always. --apply: COMMIT only if every check above holds, --expect-plan equals this plan hash AND --expect-evidence (REQUIRED) equals the evidence digest computed in this transaction (check E).
-- the real run is started ONLY through run_gated.sh <executor> <args> (GATE_V2): prerun_gate.py must read zero non-completed main deploy.yml runs and zero planned/running/paused build_runs as suvarna_reader, else the executor is not started; run_gated.sh then sets GATE_V2_LAUNCH and the executor REFUSES (exit 93) unless that marker verifies against the gate files pinned below.
-- in every mode the executor writes outcome.json (status dry_run | applied | failed, UTC time, executor sha, plan hash, gate shas, evidence digest, failed check names, under_test from the launch marker, warnings) into its evidence directory (after COMMIT an interruption records applied with a warning, never failed; a MISSING outcome.json means check the database); it refuses (exit 95) when ORPH_TEST_EVIDENCE_ROOT is set outside a pytest run.
-- gate files (byte-identical to gate_v2, PR #2938): prerun_gate.py sha256 ba65d82a338257bd7b3b1ae37df312fb382ef548291a211eadbc2538a987ef73; run_gated.sh sha256 305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076; executor_standards.py sha256 7ca8ea9cc3422f41d38ced27f6501d666dcce78918e38e1d255b8dabcdd3c38d
-- plan hash = bind_gate_into_plan_hash(sha256(plan text + "\n" + DIFF), prerun_gate.py sha256, run_gated.sh sha256)
-- resolver port: resolver_verdicts.sql sha256 724ef0db39f61799a0bffc325e4babbeeac7918d3ce1896ab031661841b96f23
-- executor: orphan_receipts_exec.py sha256 d94588d6d4f7cc277ae5dbfda6a87a0b9964b8239fa36d8620845e0eecb71c61
```
