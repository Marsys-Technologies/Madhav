# Maintained Gochara window rehearsal

This is a bounded **synthetic offline fixture**. It never observes or certifies
production readiness. Run with an authorized loopback test cluster; it creates
and drops one unique database, preserves pre-existing roles and drops only roles
whose CREATE succeeded in this invocation. It never starts or stops a server.

From the repository root:

```sh
REPO="$PWD" PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres STRICT=1 \
  REHEARSAL_OUT="$JOB_SCRATCH/original-ledger" \
  bash platform/scripts/gochara/rehearsal/run_window_rehearsal.sh
TODAY=1 REPO="$PWD" PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres STRICT=1 \
  REHEARSAL_OUT="$JOB_SCRATCH/no-pending-predecessors" \
  bash platform/scripts/gochara/rehearsal/run_window_rehearsal.sh
```

`TODAY` is retained as a legacy interface name. Mode 0 rehearses actual runner
refusal followed by represented prerequisite completion; mode 1 builds an
explicitly synthetic prerequisite ledger from current source file hashes. The
relevant Gochara routine SQL is executed; unrelated layer SQL is only represented.
Both modes run the eleven-file protected invocation, intentional 1233 failure/retry,
full sitting pre-window gates and the unchanged 1378 ACL closure. 1378 is applied
in a fixture transaction after the window, never added to its protected list.

`sitting_fixture.sql` supplies historical 131-row/124-writer expectations using
129 labeled Kala placeholders plus the real two-row 1243 INSERT. Runtime-evidence
tables are empty and the two monitor observations are explicitly synthetic. The
real sitting still owes its own ledger, census, continuity review and receipts.
The Node tsx loader avoids the CLI's Unix-socket path limit; migration diagnostics
are preserved. The pytest suite includes a recording psql safety probe: an unsafe
historical role-drop reversion fails without sending destructive SQL to PostgreSQL.

Main P07 includes protected migration 1235 in this window, after 1233 and before
1240 (`.github/workflows/deploy.yml:1112`; `platform/scripts/migrate.ts:152`). The real runner applies it with the bounded schema-CREATE capability; the
fixture checks its absence on failure and its callable result after recovery.
The pre/post-window readbacks track all six pending migrations. The read-only
`fn-1235-readbacks.sh --if-applied` returns **3 / NOT_APPLICABLE**, without an applied
receipt, only if both function and migration row are absent. The strict default
still fails on absence; partial and applied states run all original strict checks.

## Historical input provenance

Read-only source:
`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal/`.
Copied on 2026-10-16. Historical snapshots and pinned SQL/TSV/hash inputs retain
their original bytes, except `EXPECTED_WINDOW_SHA256.txt`, extended with the
unchanged 1235 migration digest during the main merge. `run_window_rehearsal.sh` is the maintained port with the
lifecycle, current-source prerequisites, sitting fixture and 1378 grant repairs.
No applied migration is copied over or edited.

| Original file | SHA-256 before porting |
|---|---|
| `prod_ledger_2026-10-02b.txt` | `cdaf8a66ea1f21e7cf17ba4d99dae6201b02bb7881d0c5c8138203590276e5f5` |
| `prod_ledger_2026-10-02c.txt` | `b165d888933ed2711f2fe0733ee88bacc05be0c4299a2b29c97052688d2fb939` |
| `window_preread_refusals.sql` | `73db79463a93f5794fdfe01a3a66accce9b230949b8bea6a926cab7aedc554a0` |
| `EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv` | `2a00af09f3db783f4975c03ea925baff7cf60be5630d235bffdfd77eac4bd73e` |
| `EXPECTED_WINDOW_SHA256.txt` | `1bc16795d3430cfacb31c30e1452d06bec580e29f5da6800bf8550fd90d7bcd1` |
| `run_window_rehearsal.sh` | `3f111f1d427297f26916f90bf2fbe035938ec443885a73dacf50defe5f673e52` |
| `window_trigger_manifest.sql` | `3d4df48e5881d580492d2185088eafba523789412bd6a16e574ed4445355a1a5` |
| `registry_1243_readback.sql` | `75e5901895f8d68c7ce23034b7ea4a5c601c35124a24a6b4041f707f614c8b07` |
