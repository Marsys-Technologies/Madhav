# orphan_receipts: D6 retirement of orphaned `__whole_asset__` receipts

One-shot operator tooling (not product code). The plan is `PLAN.md`; the hash-input text is `plan.txt`.

| file | what |
|---|---|
| `PLAN.md` | the plan for SS hash review: rows, conditions, apply order, hash, reversal, what the dry run can/cannot show |
| `plan.txt` | rendered plan text for ga_positions on the canonical chart (hash input) |
| `orphan_receipts_exec.py` | the executor, v3 (`--dry-run` always rolls back; `--apply --expect-plan <hash> --min-build-after <ts> --expect-evidence <digest>`, all three mandatory at apply; writes `outcome.json` in every mode). NEVER run it without SS approval of the plan hash, and never directly: only through `run_gated.sh` (it refuses with exit 93 otherwise) |
| `run_gated.sh`, `prerun_gate.py`, `executor_standards.py` | the GATE_V2 files, BYTE-IDENTICAL copies of `gate_v2/` (PR #2938; sha256 in the table below); the real dry run / apply MUST go through `./run_gated.sh python3 orphan_receipts_exec.py <args>` (see below) |
| `make_plan.py` | offline (no DB, no credential): re-render `plan.txt` and print executor sha, gate shas and the (gate-bound) plan hash for any `--asset` |
| `orphan_count.sql` | READ-ONLY standing S-L1 / S-L2 exit check: the orphan receipt rows (expected: none) |
| `resolver_verdicts.sql` | READ-ONLY per-asset served-generation verdict for one chart (SQL port of `served_generation.ts`; shared with the executor) |
| `tests/` | 142 tests (119 executor on a disposable local Postgres, 23 gate-wiring / plan-binding / launch tests with PATH shims) + `mutation_proof.py` (42 mutations) |

## Pre-run gate (binding, GATE_V2): always start the real executor through `run_gated.sh`

| file | sha256 (byte-identical to `gate_v2/`, PR #2938) |
|---|---|
| `prerun_gate.py` | `ba65d82a338257bd7b3b1ae37df312fb382ef548291a211eadbc2538a987ef73` |
| `run_gated.sh` | `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` |
| `executor_standards.py` | `7ca8ea9cc3422f41d38ced27f6501d666dcce78918e38e1d255b8dabcdd3c38d` |

```bash
cd 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts
./run_gated.sh python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --dry-run --min-build-after <ISO ts with offset>
./run_gated.sh python3 orphan_receipts_exec.py --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --apply --expect-plan <v3 plan hash> --min-build-after <ISO ts with offset> --expect-evidence <digest of the v3 dry run>
```
`run_gated.sh` runs `prerun_gate.py` (read-only, fail closed): non-completed `deploy.yml` runs on `main` (all non-completed statuses) must be 0 and `build_runs` in state `planned/running/paused` on any chart (read as `suvarna_reader` through `~/.config/suvarna/pgenv.sh`) must be 0; it prints both counts to stderr, and only on exit 0 sets `GATE_V2_LAUNCH` and execs the executor. The executor calls `require_gate_launch(...)` FIRST and refuses (exit 93) without a verifying marker or when `prerun_gate.py` / `run_gated.sh` / `executor_standards.py` differ from the sha256 pinned in `GATE_PINS`; those shas are also folded into the plan hash. Exit codes of the executor: 0 ok / committed; 1 apply refused or aborted (or unexpected failure); 2 dry run refused; 3 dry-run counterfactual (no `--min-build-after`); 93 not launched by `run_gated.sh` / gate files differ from the pins; 95 `ORPH_TEST_EVIDENCE_ROOT` set outside a pytest run. The gate's own codes (1, 2, 94-97) come from `run_gated.sh` with `run_gated: gate exit=<n>; target NOT started`.

Evidence always goes to `/Users/Dev/suvarna-evidence/OrphanReceipts/<asset>_<chart8>_<UTC ts>/` (0700; `--evidence-root` is ignored; `ORPH_TEST_EVIDENCE_ROOT` is REFUSED outside pytest, exit 95, even when empty). In EVERY mode the run directory holds `outcome.json` (0600): `schema`, `status` (`dry_run` | `applied` | `failed`), `utc`, `executor_sha256`, `plan_hash`, `gate_sha256`, `run_gated_sha256`, `evidence_digest`, `failed_checks`. A dry run without `--min-build-after` (the counterfactual) is recorded as `failed` (`counterfactual_no_min_build_after`). No outcome file exists for a run that stops before its directory exists (invalid arguments, launch refusal 93, test-variable refusal 95).

## Run the read-only checks as `suvarna_reader`

```bash
D=00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts
# orphan rows (asset | chart | orphan key | registry declares a partition | total). Zero lines = clean.
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -f $D/orphan_count.sql )
# the count only (use as a gate: must print 0 at S-L1 / S-L2 exit)
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -f $D/orphan_count.sql | wc -l )
# per-asset served-generation verdicts for a chart (asset | verdict | partitions)
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -v chart=482012f1-710e-4a25-994a-93821f5871aa -f $D/resolver_verdicts.sql )
```

`orphan_count.sql` is the design review's section 4.6 query: an orphan is a chart-scoped receipt whose `partition_key` differs from
`coalesce(nullif(btrim(asset_registry.natural_key_partition),''),'__whole_asset__')`. Fire it before any registry edit that adds a
`natural_key_partition` and after each S-L1 / S-L2 stage. `resolver_verdicts.sql` (v1.1) is a port of `partitionDefect` + `classifyAssetGeneration` (TS reason names, partition_key order, split checks on rows build, receipt build and spec digest) validated against a reading of the
TypeScript, not the deployed code; the executor uses it only as a before/after diff.

## Current values (read 2026-10-02 as `suvarna_reader`, canonical chart)

- `orphan_count.sql`: **5** rows, all `partition_key = __whole_asset__`, registry declares a partition for each, chart `482012f1-710e-4a25-994a-93821f5871aa`: `bo_cgm_motifs`, `bo_laksana`, `bo_sangati`, `bo_upaya`, `ga_positions`.
- `resolver_verdicts.sql` on the canonical chart: **37 RESOLVED / 15 unresolved** (52 assets with chart receipts; unchanged by the v1.1 port). Unresolved: 4 of the 5 orphan cases above (`receipt_not_proven`; `bo_upaya` below), `ga_strength` (`receipt_spec_retired`), `bo_karanajala`, `bo_laksana_rerank`, `bo_pratijna`, `bo_samvada`, `bo_yantra_mechanism`, `ka_gochara`, `ka_yojaka` (`receipt_not_fresh`), `ka_dasha_kala` (`receipt_not_proven`, single partition: no digest spec), `ka_moorti_nirnaya` (`intervening_attempt_unreceipted`). `bo_upaya` now reads `receipt_spec_retired` (its declared partition is the first defective one; its W row is `receipt_not_proven` behind it).
- S-L1 asset set (19 assets: ga_positions, ga_sensitive, ga_vargas, ga_dashas, ga_nakshatra, ga_panchanga, ga_strength, ga_structural, ga_yoga, ga_vichara, ga_condition, ga_medical, ga_vastu, ga_sade_sati, ga_tajaka, ga_ayurdaya, ga_transit_anchors, ga_sensitive_degree, ga_prashna): **17 RESOLVED / 2 not** (`ga_positions` `receipt_not_proven` = the orphan this plan retires; `ga_strength` `receipt_spec_retired`).

## Run the tests

```bash
python3 -m pytest 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests -q          # needs psycopg 3 + local initdb/pg_ctl/psql (the wiring tests need neither)
python3 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests/mutation_proof.py      # neuter one rule at a time: each test goes red (optional name filters)
# macOS: keep the unix-socket path short, e.g.  TMPDIR=/private/tmp/claude-504/o  PG_BIN=/opt/homebrew/opt/postgresql@15/bin
# PostgreSQL >= 16: a CREATEROLE-only admin cannot GRANT an arbitrary role, so run as a superuser admin:
PG_BIN=/opt/homebrew/opt/postgresql@17/bin ORPH_TEST_ADMIN=postgres python3 -m pytest 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests -q
```
Tests never touch a real database: the CLI's only door is `connect_admin()`; tests inject a connection to a throw-away cluster.

## After ANY edit to the executor or `resolver_verdicts.sql`

`python3 make_plan.py --write`, then update the hashes quoted in `PLAN.md` and here (tests pin them) and get the new plan hash re-approved. The same applies to any change of the three gate files (re-copy them byte-identically from `gate_v2/`, update `GATE_PINS` in the executor).
