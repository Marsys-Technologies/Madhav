# orphan_receipts: D6 retirement of orphaned `__whole_asset__` receipts

One-shot operator tooling (not product code). The plan is `PLAN.md`; the hash-input text is `plan.txt`.

| file | what |
|---|---|
| `PLAN.md` | the plan for SS hash review: rows, conditions, apply order, hash, reversal, what the dry run can/cannot show |
| `plan.txt` | rendered plan text for ga_positions on the canonical chart (hash input) |
| `orphan_receipts_exec.py` | the executor (`--dry-run` always rolls back; `--apply --expect-plan <hash> --min-build-after <ts> --expect-evidence <digest>`, all three mandatory at apply). NEVER run it without SS approval of the plan hash |
| `run_gated.sh`, `prerun_gate.py` | the pre-run gate as code; the real dry run / apply MUST go through `run_gated.sh <executor args>` (see below) |
| `make_plan.py` | offline (no DB, no credential): re-render `plan.txt` and print executor sha + plan hash for any `--asset` |
| `orphan_count.sql` | READ-ONLY standing S-L1 / S-L2 exit check: the orphan receipt rows (expected: none) |
| `resolver_verdicts.sql` | READ-ONLY per-asset served-generation verdict for one chart (SQL port of `served_generation.ts`; shared with the executor) |
| `tests/` | 108 tests (85 executor on a disposable local Postgres, 23 gate with PATH shims) + `mutation_proof.py` (14 mutations) |

## Pre-run gate (binding): always start the real executor through `run_gated.sh`

```bash
./run_gated.sh --asset ga_positions --chart 482012f1-710e-4a25-994a-93821f5871aa --dry-run --min-build-after <ISO ts with offset>
```
`prerun_gate.py` (stdlib only, read-only, fail closed) reads in the same invocation (a) the number of `deploy.yml` runs on `main` with status != completed (`gh run list --workflow deploy.yml --branch main --limit 20 --json status`) and (b) the number of `build_runs` in state `planned/running/paused` on any chart (`psql` as `suvarna_reader` in a subshell sourcing `~/.config/suvarna/pgenv.sh`), prints both counts, and exits 0 only if both are 0 (1: a count is non-zero; 2: a read failed or its output was malformed). `run_gated.sh` execs the executor only on exit 0. The gate is generic: the cg_exec-style executors, the F-A2 executor, the G-IDX executor and the dispatch wrapper must call the same gate (SS binds that for them). Evidence always goes to `/Users/Dev/suvarna-evidence/OrphanReceipts/` (`--evidence-root` is ignored unless the test-only env var `ORPH_TEST_EVIDENCE_ROOT` is set).

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
python3 -m pytest 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests -q          # needs psycopg 3 + local initdb/pg_ctl/psql (gate tests need neither)
python3 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests/mutation_proof.py      # neuter one refusal at a time: each test goes red
# PostgreSQL >= 16: a CREATEROLE-only admin cannot GRANT an arbitrary role, so run as a superuser admin:
PG_BIN=/opt/homebrew/opt/postgresql@17/bin ORPH_TEST_ADMIN=postgres python3 -m pytest 00_ARCHITECTURE/briefs/suvarna/exec/orphan_receipts/tests -q
```
Tests never touch a real database: the CLI's only door is `connect_admin()`; tests inject a connection to a throw-away cluster.

## After ANY edit to the executor or `resolver_verdicts.sql`

`python3 make_plan.py --write`, then update the hashes quoted in `PLAN.md` (a test pins them) and get the new plan hash re-approved.
