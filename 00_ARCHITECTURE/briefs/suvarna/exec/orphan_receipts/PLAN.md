---
artifact: D6_ORPHAN_RECEIPTS_PLAN
version: 1.0
status: DRAFT_FOR_REVIEW (plan hash NOT yet approved; no data change made)
date: 2026-10-02
lane: suvarna/land/TI-d6-orphan-receipts-001
decision: design review DESIGN_REVIEW_LEGACY_WHOLE_ASSET_RECEIPTS, option (a): D6 owner-path retirement, narrow, per stage
changelog:
  - "1.0 (2026-10-02): plan, executor, tests, standing orphan check and resolver port. Nothing was run against the real database (read-only catalog/data reads as suvarna_reader only)."
---

# D6 plan: retire the orphaned `__whole_asset__` receipt rows (ga_positions at S-L1; bo_* at S-L2)

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
| V | resolver verdicts (SQL port, `resolver_verdicts.sql`) computed inside the transaction for ALL assets before and after; the diff is EXACTLY `{<asset>: receipt_not_proven -> RESOLVED}` | any other asset changes (either direction), or this asset does not become RESOLVED |
| A | snapshot A (before everything) vs snapshot B (after the work, after the transient membership is revoked): `relacl` (aclexplode incl. grantable), owner, `relrowsecurity`/`relforcerowsecurity`, `pg_policy` rows, `pg_auth_members` rows, over every public relation: all diffs empty | any difference |
| E | (optional) `--expect-evidence <digest>` equals the evidence digest this run computes | differs |
| evidence | before-images + reversal SQL written (0700 dir, 0600 files) BEFORE any DELETE | cannot be written: ABORT + ROLLBACK, in both modes |

One transaction; `SET LOCAL lock_timeout = '5s'`, `statement_timeout = '5s'`, `search_path = pg_catalog, pg_temp`, `TimeZone = 'UTC'`. `--dry-run` ALWAYS ends in ROLLBACK. `--apply` COMMITs only if every check holds, otherwise ROLLBACK and exit 1.

Decision for SS (strike if unwanted): after `SET LOCAL ROLE amjis_app` the executor takes `LOCK TABLE asset_provenance_receipts, asset_freshness, build_runs IN SHARE ROW EXCLUSIVE MODE` (readers are not blocked; writers, i.e. a builder or a build start, wait). This makes P5 race-free (no build can start between the check and the DELETE) and bounds the window to a few seconds; if the lock is not obtained in 5 s the run fails and changes nothing.

## 4. Mechanism (owner path, copied from `ChartGrants/cg_exec.py`)

The only role able to DELETE from either table is the table owner `amjis_app` (login role; `data_plane_builder` holds only SELECT/INSERT/UPDATE, a DB test pins DELETE as refused). The executor, connected as the admin in-process (password fetched from Secret Manager inside the process, never printed, logged or saved; proxy 127.0.0.1:5433): snapshot A; `GRANT amjis_app TO <session user>` only if not already a member; `SET LOCAL ROLE amjis_app`; locks; before-images; checks; DELETEs; `RESET ROLE`; `REVOKE` only what it granted; snapshot B. Rendered statement-by-statement in `plan.txt` (current rendering below). Ownership read from the catalog as `suvarna_reader`: both receipt tables, `build_runs`, `build_run_assets`, `asset_registry`, `asset_output_digest_specs` are owned by `amjis_app`; no RLS, no policies, no triggers on the two receipt tables, no FK referencing either.

## 5. Apply order (a named step of S-L1: "S-L1.RETIRE-ORPHAN-RECEIPTS")

ONLY AFTER the ga_positions S-L1 rebuild is verified by direct DB read (new run `completed`, its `build_run_assets` row `complete`/`build`, the declared-partition receipt `proven`/`fresh`, the digest checks LC-1..LC-4), and BEFORE any served-surface acceptance read (those go through the fence and would otherwise see no ga_positions). Retiring earlier would serve the old 09-07 rows once and then flip again.

1. Record `T0` = the instant the S-L1 ga_positions rebuild was dispatched (UTC, with offset). That is `--min-build-after`.
2. After the rebuild is verified: `python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --dry-run --min-build-after <T0>`; read the printed JSON: expect `status DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`, exit 0, `verdict_diff == {"ga_positions": ["receipt_not_proven", "RESOLVED"]}`, rowcounts 1/1, all A diffs 0, `evidence_digest`.
3. SS approves the plan hash (section 6) and the dry-run evidence.
4. `python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --apply --expect-plan <hash> --min-build-after <T0> --expect-evidence <digest from step 2>`; expect `COMMITTED`.
5. Read-only after commit: `orphan_count.sql` no longer lists ga_positions; `resolver_verdicts.sql` shows ga_positions RESOLVED; then served-surface acceptance (inquiry lifecycle tokens and sessions pinned to the old generation see a changed generation identity: fail closed, in-flight inquiries restart).

S-L2: the same executor, `--asset bo_laksana | bo_sangati | bo_cgm_motifs | bo_upaya`, one apply each after that asset's S-L2 rebuild is verified. `bo_upaya` must additionally have been rebuilt under its CURRENT spec (`e73b69a6`; its declared receipt is under a retired spec today) or V refuses (the asset would not become RESOLVED). `bo_sangati`'s declared receipt was rebuilt 09-11 (before S-L2): only `--min-build-after` distinguishes it from the S-L2 rebuild, which is why the parameter is mandatory. Plan hashes for these (computed offline; valid only while the executor and `resolver_verdicts.sql` are byte-identical to this PR; re-run `make_plan.py --asset <a>`):

| asset | plan hash (chart 482012f1-710e-4a25-994a-93821f5871aa) |
|---|---|
| bo_laksana | `36afac7ca32fae738ced97a5bb1dd02806ff522fa9484b4d4ca98a7dba34055c` |
| bo_sangati | `f689f9f8c0798b20c571d16b2238ef3488c6cb2fcea8558b73a720845eccff82` |
| bo_cgm_motifs | `d1a37bbb0d9e232046a53e5cdc02214db9fe5e91fd54f7344bb93c82e70bcee3` |
| bo_upaya | `1218f7a7d86426044829bda6647989f329d7f7765e850106417a58b4e7bcd090` |

## 6. Plan hash (what is bound, what is not)

- `plan_text` = `plan.txt` (rendered by `render_plan()` for the asset and chart; embeds the executor sha256 and the `resolver_verdicts.sql` sha256).
- `DIFF` (static) = `['asset_freshness|ga_positions|482012f1-710e-4a25-994a-93821f5871aa|__whole_asset__|present->absent', 'asset_provenance_receipts|ga_positions|482012f1-710e-4a25-994a-93821f5871aa|__whole_asset__|present->absent', 'resolver_verdict|ga_positions|receipt_not_proven->RESOLVED']`.
- **plan hash = sha256(plan_text + "\n" + json.dumps(DIFF))**, computed WITHOUT the database (`python3 make_plan.py`; the executor prints the same value first and refuses `--apply` unless `--expect-plan` equals it). It binds: the exact statements, the asset and chart, the executor code, the resolver port, and the expected verdict transition.

| item | value |
|---|---|
| executor `orphan_receipts_exec.py` sha256 | `eba9c7da1f72907fedd8c9a8a6eefb1e5b735d3f3c697a0c7fb9076b867ab09f` |
| `resolver_verdicts.sql` sha256 | `cbd79344bb5c9d23f23a4b33fef1e410ee765d2dab9d3936292288b20b6b1126` |
| **plan hash, ga_positions on 482012f1-710e-4a25-994a-93821f5871aa** | `13dc3c2d8f6bc4f8fb9dab3888fb44a64e7f9ab7f3cd7c7d328901dcfc25af38` |

DB-dependent, computed at dry-run/apply time and NOT in the plan hash: the before-images (their sha256 are printed and in `SHA256SUMS`), the reversal SQL, the verdict diff, rowcounts, the ACL/owner/RLS/policy/membership snapshots, and `--min-build-after`. They are bound by `evidence_digest` = sha256 of canonical JSON of {asset, chart, min_build_after, plan hash, executor sha, before-images sha, reversal sha, verdict diff, chart-scoped counts before/after, per-check pass/fail}. Pass the dry run's digest as `--expect-evidence` to apply so the apply provably runs against the state the dry run showed (the digest contains no timestamp, so identical state gives an identical digest).

If the executor or `resolver_verdicts.sql` changes by one byte, the plan hash changes and SS must re-approve (`tests` pin `plan.txt` and this file's quoted hashes to the committed code).

## 7. Reversal

`reversal.sql` (in the evidence directory, sha256 recorded) re-inserts both rows from the before-images (every non-generated column as a typed literal; `scope_key` is GENERATED and recomputes) inside one `BEGIN; SET LOCAL TimeZone='UTC'; SET LOCAL ROLE amjis_app; INSERT...; INSERT...; COMMIT;`. Run through the same owner path (transient membership). Tested on a disposable Postgres: after `--apply` then `reversal.sql`, a md5-of-every-row image of every table plus the ACL/RLS/policy/membership catalogs is byte-identical to the pre-apply image. After reversal the resolver returns ga_positions to `receipt_not_proven`.

## 8. What the dry run shows, and what it CANNOT show today

Printed JSON (never row content, never the 108-char partition text, never a credential): `status`, `failed_checks` / `skipped_checks`, every check with its detail, `rowcounts` (orphan rows found, DELETE rowcounts, chart-scoped counts before/after, table totals), `verdict_diff`, `verdict_counts` before/after, `acl_diff` and the rls/policy/membership/owner diff counts, `before_images` (dir + path + sha256 of each file), `evidence_digest`, `plan_hash`, `executor_sha256`. Exit codes: 0 all hold / committed; 1 apply refused or aborted; 2 dry-run refused; 3 dry-run counterfactual (no `--min-build-after`).

Today (2026-10-02, before the S-L1 rebuild) the later declared-partition receipt that P3 requires does not exist: the only declared receipt is the pre-S-L1 one from 2026-09-07. Therefore:

- A real dry run NOW with `--min-build-after <any instant after 2026-09-07 08:37 UTC>` is expected to REFUSE at P3 (`after_min_build_after: false`, `newer_than_orphan_build: true`), issue no DELETE, and write the before-images + reversal SQL. P1, P2, P4, P5 are expected to hold (registry declares the partition; W rows `unknown`/`stale`; 1 and 1; zero planned/running/paused runs as of the last read: 14 stopped, 300 completed, 422 failed). That run shows the refusal and the exact before-images.
- A real dry run NOW without `--min-build-after` is a counterfactual (exit 3): P3 is evaluated without the rebuild gate, so every check is expected to hold and the verdict diff is expected to be `{ga_positions: receipt_not_proven -> RESOLVED}` (the design review's counterfactual: 37/15 -> 38/14). It proves the mechanism and the blast radius on the live data but is not a rehearsal of `--apply`, which would refuse.
- The rehearsal that matters (step 2 of section 5, `--min-build-after <T0>`) can only run AFTER the S-L1 ga_positions rebuild. It is expected to be run, once SS approves the hash, both now (the refusal and the before-images) and after the rebuild.

Not verifiable without the real run: that `postgres` can still `GRANT amjis_app` and `SET LOCAL ROLE` on the current Cloud SQL major version (taken from the `cg_exec.py` precedent; on PostgreSQL 16+ a CREATEROLE-only admin cannot grant an arbitrary role, the executor then fails before any change); whether the 5 s statement timeout is enough for the verdict query on production (it took 0.9 s as `suvarna_reader`); any event trigger / audit extension on admin DML (not visible to `suvarna_reader`).

## 9. Not in scope / not done

No data change. No migration, no registry edit, no code change to `served_generation.ts`, `provenance.py`, or the orchestrator (the frozen orchestrator contract is untouched). The resolver fix (option b: ignore orphan partitions at serve time) and the writer-side retirement (option c) are separate native decisions. Global-scope orphans (`chart_id IS NULL`; one pair, `bg_formula_constants`) are out of scope: the chart resolver does not read them.

## 10. Verification performed

- 55 tests on a disposable local PostgreSQL 15 (initdb in a temp dir, own port; non-superuser CREATEROLE admin so the transient GRANT/REVOKE is exercised) and the same suite on PostgreSQL 17 with a superuser admin: happy path, rowcounts, before-image content/modes/hashes, reversal byte-for-byte, dry-run byte-identity (rows and catalogs), generalisation to a second asset, chart scoping, and every refusal in section 3 (several each, apply mode and dry-run).
- Mutation proof (`tests/mutation_proof.py`): neutering each of P5, P3(min-build-after), V, A(acl), P1 in a copy of the executor turns its test red.
- Fixture tables are the production definitions as read from the catalog (`\d`), see `tests/fixture_schema.py` for the two deliberately minimal tables.
- Read-only as `suvarna_reader`: `orphan_count.sql` and `resolver_verdicts.sql` run against production (README.md); the executor itself was never run against any real database.

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
-- --dry-run: the same statements, then ROLLBACK, always. --apply: COMMIT only if every check above holds and --expect-plan equals this plan hash.
-- resolver port: resolver_verdicts.sql sha256 cbd79344bb5c9d23f23a4b33fef1e410ee765d2dab9d3936292288b20b6b1126
-- executor: orphan_receipts_exec.py sha256 eba9c7da1f72907fedd8c9a8a6eefb1e5b735d3f3c697a0c7fb9076b867ab09f
```
