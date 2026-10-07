# KĀLA-YANTRA test collection

Database-free Kāla tests belong under `platform/python-sidecar/tests/l3/kala/`.
The required Governance Gates job discovers them through its existing `pytest tests/`
command. `test_ci_canary.py` writes a named pass line into that job's log.

Database-backed Kāla tests belong under `platform/python-sidecar/tests/l3/kala_db/`.
The additive `kala-db-tests` job runs that whole directory against a disposable
PostgreSQL service. `KALA_REQUIRE_DB=1` makes an unreachable server, a missing DSN,
or any skipped test fail the job. Each test gets a uniquely named database created
and dropped by `conftest.py`; the shared disposable-database guard validates the
connection before any database-changing command. For the fleet's local Docker
server, the fixture also checks the exact campaign container image, label,
loopback port binding, and reported server address before allowing its bridge
address. All other targets remain refused.

For local checks, list these exact paths in `run/tests/<ID>.txt` and run
`KY_ITEM=<ID> fleet/precheck.sh` from the lane worktree:

```text
platform/python-sidecar/tests/l3/kala/test_ci_canary.py
platform/python-sidecar/tests/l3/kala/test_kala_db_guard.py
platform/python-sidecar/tests/l3/kala_db
```

The guard test fails when a Kāla database-free test directly opens a database.
CI discovery of the complete DB directory means new database tests need no
workflow edit. The local precheck is evidence for the checkpoint; the required
CI job and independent verdict remain later acceptance gates.
