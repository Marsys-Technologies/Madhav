"""
teardown_v5_small_test_job.py — Pravāha C38: teardown for the SMALL TEST build
of ka_gochara_v5 staged by dispatch_v5_small_test_job.py (C37).

Pinned chart only (482012f1-710e-4a25-994a-93821f5871aa; there is no chart argument), ONE transaction, fail-closed.

RUNNING IT
  DESTRUCTION NEEDS INTENT. The default is a dry run. A dry run and an execution run the SAME statements and validations in the
  same transaction — every lock, every refusal check, every DELETE, the registry UPDATE and the end-state validation — and differ
  only in the last step: the dry run ROLLS BACK (zero commits), the execution commits. Deleting needs BOTH `--execute` and
  `--i-am-steward`. The database URL comes ONLY from the process environment (DATABASE_URL): never from an argument, never from a
  file in the checkout (this script no longer reads `.env.local`), never printed. A failure prints the exception CLASS (and the
  SQLSTATE), never the exception text, and says what is KNOWN about the transaction: rollback confirmed, rollback not confirmed,
  or commit outcome unknown (a COMMIT was sent and no answer came back). It never claims the database is unchanged unless a
  rollback was confirmed.

RETENTION — RUN THIS WITHIN 90 DAYS OF THE SMALL TEST
  The cockpit watchdog deletes terminal build runs 90 days after their creation (`app/api/cockpit/watchdog/route.ts`, "M-4"), and
  `asset_provenance_receipts.build_id` is ON DELETE SET NULL. A receipt whose run is gone has an origin nothing can prove, and this
  script refuses it for good (below). The dry run prints each owned run's creation time and the days of retention that remain. Past
  the window the only way out is the steward recovery runbook,
  00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md.

SYNCHRONISATION
  Before ANY ownership check the script takes, in the order the orchestrator uses, (1) the per-chart orchestrator exclusion lock
  (`pg_try_advisory_lock(hashtext(chart))`, non-blocking: if a build run holds it, the teardown refuses) and (2) the Gochara
  chart lock `ka_gochara_lock_chart` (transaction-scoped, behind a `lock_timeout` so a competing writer makes the teardown fail
  closed instead of waiting). Both are held to commit; every check below is evaluated INSIDE them.
  WHAT THE LOCKS DO NOT DO: the advisory lock excludes ORCHESTRATOR build runs (`runner.acquire_chart_lock`) and the chart lock
  excludes Gochara writers. Neither excludes the cockpit WATCHDOG, which takes no advisory lock and may prune terminal runs at any
  moment; the script's reads and DELETEs are by id inside one transaction, and a run pruned in between can only make a receipt it
  had already proven lose its run link, which the same transaction deletes as proven anyway.
  A DIRECT CONNECTION IS REQUIRED. The orchestrator lock is a SESSION advisory lock; through a transaction-mode pooler (PgBouncer
  and the like) it silently holds nothing. The script reads `pg_backend_pid()` across separate transactions and refuses if the backend
  changes, and checks that the lock is held by the backend running the transaction; use the database's own host and port, never a pooler.

REFUSES (loudly, nothing deleted) when ANY of these holds:
  1. the orchestrator exclusion lock or the Gochara chart lock cannot be taken;
  2. a kala_gochara_publication row for the chart at '5.0' is `published`, or a ka_gochara_generation_seal row exists for it, or
     kala_gochara_authority names '5.0' (published / sealed / serving generations are never torn down);
  3. ANY build run on the chart is planned / running / paused (whatever its scope or assets);
  4. a build run whose MEMBERSHIP includes this asset (a `build_run_assets` row, or the asset named in a comma-separated
     `scope_target`) was not triggered by 'gochara-v5-small-test';
  5. a small-test run is not EXCLUSIVELY this asset's (another asset in its child rows or `scope_target`, or another asset's
     provenance receipt linked to it), or an owned run has receipts of THIS asset on ANOTHER chart (deleting the run would set
     their run link to NULL);
  6. a provenance receipt of this asset on the chart has NO run link (origin unprovable: preserved, named, pointer to the
     runbook), or links to a run that is not one of the owned small-test runs;
  7. generation '5.0' output (chain, inventory, snapshot) or a manifest exists and the CURRENT manifest is not PROVEN to be this
     test's slice. Proof is the writer's OWN validation (`ka_gochara_v5._validate_test_slice`, imported, no second implementation)
     of the stamp's marker, the marker digest and the whole component recomputed with the writer's own `_slice_component`, the
     manifest's horizon equal to the stamp's, AND the stored input snapshot and every inventory header carrying the SAME vector
     identity as the stamped manifest (snapshot vector equal; inventory input digest, horizon and class inside the stamp). A
     manifest stamped by a later slice whose snapshot substep has not yet replaced an older chain (an interrupted replacement) is
     refused by name: re-dispatch the slice (which replaces the chain), then tear down;
  8. the legacy ledger tables `kala_gochara_windows` / `kala_gochara_contacts` hold '5.0' rows for the chart (never this
     writer's; named, never deleted);
  9. the Nirmana N-137 end state would not hold: the registry row's catalog_status is RETIRED, any asset lists this asset in
     `depends_on`, or ANY chart holds a receipt or a build_run_assets row of this asset from a run that is not a
     'gochara-v5-small-test' run — checked before deleting AND again before claiming success;
  10. the registry row is active and another chart holds a freshness row for this asset (restoring the row inert fires migration
     596's invalidation across ALL charts; the script refuses rather than stale other charts' projections).

  11. any table (found from the catalog, not a hardcoded list) references an owned `build_runs` row or the manifest and is not one
     of the tables this script deletes itself: deleting the run would set that reference to NULL (conversations, the prediction and
     calibration ledgers, ...) and deleting the manifest would fail on a NO ACTION reference (the legacy contacts'
     `input_generation_vector_id`). Named, with table, column and count, instead of a bare SQLSTATE.

Then deletes, in ONE commit, in this order: provenance receipts and the freshness row of this asset on the chart; build_run_assets
and build_runs of the exclusively-owned test runs (by id); the asset_throughput row; the OUTPUT CHAIN of (chart, '5.0') in the
order RecordStore.delete_generation_chain uses; the SEARCH INVENTORY in the order InventoryStore.delete_generation_inventory uses,
then the input snapshot; the candidate manifest. The asset_registry row is KEPT; it is touched ONLY when it is found ACTIVE (then
restored inert, is_active = false) — a row already inert is not updated, so the role needs no UPDATE on it — and it is verified
field by field against the migration-1304 small-test shape either way. KEPT as well: the global sky-event substrate, Moon on-demand
coverage partitions, every other chart, generation and asset.

SHARED PROOF. What proves a generation '5.0' candidate is a small-test slice's, and the N-137 end-state predicate, live in ONE module,
`v5_small_test_shared.py`, imported by this script and by the dispatch (PR 3097): neither carries a second copy.

DATABASE ROLE. The script runs as ONE role; it never assumes the admin role. The privileges it needs are REQUIRED_PRIVILEGES below
(one list; a real-database test runs the script as a role holding EXACTLY it, and shows a missing grant fails the dry run) and, with the
runbook's reading of the migrations, in the steward runbook (section "Which role"). The role also needs SELECT on every table the
catalog discovery (item 11) finds referencing the run or manifest; with the registry row ACTIVE, the registry restore additionally needs
UPDATE(is_active) on asset_registry and, because migration 596's invalidation trigger fires on a real change, SELECT and UPDATE on
asset_freshness.

Usage:
  cd <repo-root>/platform
  DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py                          # dry run (the default)
  DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py --execute --i-am-steward  # delete
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))     # the shared proof module sits next to this script
import v5_small_test_shared as shared  # noqa: E402
from v5_small_test_shared import (  # noqa: E402,F401  (re-exported: the tests and the runbook read these names here)
    ASSET_ID, CHAIN_TABLES, CHART_ID, GENERATION, INVENTORY_TABLES, OUTPUT_TABLES, TRIGGERED_BY, Refused)

TeardownRefused = Refused
_writer, _count, _table_exists = shared.writer, shared.count, shared.table_exists
_same_instant, _stamp_problem, _stamped_classes = shared.same_instant, shared.stamp_problem, shared.stamped_classes
_generation_rows, _end_state_problems = shared.generation_rows, shared.end_state_problems

ACTIVE_STATES = ("planned", "running", "paused")
LOCK_TIMEOUT = "10s"                                       # the chart lock is requested behind this: fail closed, never wait forever
RETENTION_DAYS = 90                                        # the cockpit watchdog's terminal-run retention (watchdog/route.ts, M-4)
RUNBOOK = "00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md"

# The shape the ka_gochara_v5 registry row must hold after teardown: the migration-1304 small-test row, the SAME values
# dispatch_v5_small_test_job.EXPECTED_REGISTRY_ROW validates before staging (a test pins the two equal).
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": True,
    "writer_timeout_seconds": 7200,
    "depends_on": ["ga_positions", "ga_dashas"],
    "target_table": "ka_gochara_eval_window",
    "count_sql": ("SELECT COUNT(*) FROM ka_gochara_eval_window "
                  "WHERE chart_id=$1 AND generation='5.0'"),
    "target_floor": 0,
    "estimated_seconds": None,
}

MANIFEST_TABLE = ("kala_gochara_publication", "")   # the candidate manifest: last, and only once proven to be the slice's
GENERATION_TABLES = CHAIN_TABLES + INVENTORY_TABLES + (MANIFEST_TABLE,)
# The legacy v4 ledger tables are NOT written by the v5 writer: GUARD-ONLY. A table that does not exist is skipped (named `absent`
# in the listing); rows of '5.0' in one are not this test's, and the teardown refuses and names them.
LEGACY_GUARD_TABLES = ("kala_gochara_windows", "kala_gochara_contacts")

#: THE list of what the script needs, by object (schema public). The runbook's table states the same; a real-database test creates a role
#: holding EXACTLY this and runs the script as it. The two verification tables are deliberately absent: they go by foreign-key cascade.
REQUIRED_PRIVILEGES = {
    "select_delete": ("asset_provenance_receipts", "asset_freshness", "build_run_assets", "build_runs", "asset_throughput",
                      *(t for t, _ in GENERATION_TABLES)),
    "select": ("ka_gochara_generation_seal", "kala_gochara_authority", "asset_registry", *LEGACY_GUARD_TABLES),
    "execute": ("ka_gochara_lock_chart(uuid)", "ka_gochara_generation_is_sealed(uuid, text)"),   # the second: the DELETE guards call it (invoker)
    # only when the registry row is found ACTIVE (a row already inert is not updated): the restore UPDATE and 596's invalidation trigger
    "when_registry_active": {"asset_registry": ("UPDATE(is_active)",), "asset_freshness": ("SELECT", "UPDATE")},
}
#: tables other than these (found from the catalog) that reference an owned run or the manifest are refused by name
RUN_REFERENCES_SKIP = ("build_run_assets", "asset_provenance_receipts")


def _validate_registry_row(cur, *, check_active: bool = True) -> None:
    cur.execute(
        """SELECT scope, is_active, has_writer, has_substeps, writer_timeout_seconds,
                  depends_on, target_table, count_sql, target_floor, estimated_seconds
           FROM asset_registry WHERE asset_id = %s""",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        raise TeardownRefused(
            f"asset_registry row for {ASSET_ID} is missing — migration 1243 "
            "inserts it permanently and the writer-gap preflight fails every "
            "build run without it; restore the row, do not re-run teardown")
    for field, expected in EXPECTED_REGISTRY_ROW.items():
        if field == "is_active" and not check_active:
            continue                                  # before the flip the row is as the test left it (active)
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if actual != expected:
            raise TeardownRefused(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — "
                "the registry row must be its migration-1304 small-test self after teardown "
                "(apply 1304; never edit the row by hand)")


def _require_direct_connection(conn) -> None:
    """The orchestrator lock below is a SESSION advisory lock; through a transaction-mode pooler it silently holds nothing. Read
    `pg_backend_pid()` in three SEPARATE transactions (each ended by a rollback — the point at which a pooler may hand the next one a
    different backend) and refuse if it ever changes. Not proof of a direct connection (a quiet pooler can reuse a backend), which is why
    the runbook also REQUIRES the database's own host and port; it is the check that fails loudly when pooling is in play."""
    pids = []
    for _ in range(3):
        cur = conn.cursor()
        cur.execute("SELECT pg_backend_pid() AS pid")
        pids.append(cur.fetchone()["pid"])
        conn.rollback()
    if len(set(pids)) != 1:
        raise TeardownRefused(
            f"the database backend changed between transactions (pids {pids}): this looks like a pooled connection, through which the "
            "orchestrator's SESSION advisory lock holds nothing. Nothing was checked or deleted; connect DIRECTLY to the database host "
            "and port (no PgBouncer or other transaction-mode pooler) — see the runbook")


def _take_locks(cur) -> None:
    """(1) the orchestrator's per-chart exclusion lock — the one `acquire_chart_lock` takes for a build run, session-level and
    non-blocking; (2) the Gochara chart lock the writers and the replace take, transaction-scoped, behind a lock_timeout. Both
    BEFORE any ownership check; both held to commit/rollback (the first until the connection closes)."""
    cur.execute("SELECT pg_try_advisory_lock(hashtext(%s)) AS got", (CHART_ID,))
    if not cur.fetchone()["got"]:
        raise TeardownRefused(
            f"the orchestrator's exclusion lock for chart {CHART_ID} is held — a build run (or another operator) is active on "
            "this chart; nothing was checked or deleted")
    cur.execute(
        """SELECT count(*) AS n FROM pg_locks WHERE locktype = 'advisory' AND granted AND pid = pg_backend_pid()
             AND ((classid::bigint << 32) + objid::bigint) = hashtext(%s)::bigint""", (CHART_ID,))
    if int(cur.fetchone()["n"]) < 1:
        raise TeardownRefused(
            "the orchestrator exclusion lock was granted but is not held by the backend running this transaction (a pooled connection?); "
            "nothing was checked or deleted — connect DIRECTLY to the database host and port, see the runbook")
    cur.execute("SELECT set_config('lock_timeout', %s, true)", (LOCK_TIMEOUT,))
    cur.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))


def _release_orchestrator_lock(conn) -> None:
    """Best effort: closing the connection releases a session-level advisory lock anyway."""
    try:
        conn.rollback()                       # nothing is open; the unlock below runs outside any transaction
        conn.autocommit = True
        conn.cursor().execute("SELECT pg_advisory_unlock(hashtext(%s))", (CHART_ID,))
    except Exception:
        pass


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _referencing_rows(cur, parent: str, ids: list[str], skip_tables: set[str]) -> list[str]:
    """Every foreign key INTO `public.<parent>` from the catalog (single-column keys), minus the tables this script deletes itself:
    the rows that reference `ids`, as named problems (table, column, delete action, count). The catalog is the list, so a reference added
    by a later migration is found without anyone remembering to add it here."""
    if not ids:
        return []
    cur.execute(
        """SELECT c.conrelid::regclass::text AS tbl, a.attname AS col, c.confdeltype AS action
           FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
           WHERE c.contype = 'f' AND c.confrelid = %s::regclass AND cardinality(c.conkey) = 1
           ORDER BY 1, 2""", (f"public.{parent}",))
    found = []
    for ref in cur.fetchall():
        table = ref["tbl"][len("public."):] if ref["tbl"].startswith("public.") else ref["tbl"]
        if table.strip('"') in skip_tables:
            continue
        n = _count(cur, f"SELECT count(*) AS n FROM {ref['tbl']} WHERE {_quote(ref['col'])} = ANY(%s::uuid[])", (ids,))
        if n:
            action = {"n": "SET NULL", "c": "CASCADE", "a": "NO ACTION", "r": "RESTRICT", "d": "SET DEFAULT"}.get(ref["action"], ref["action"])
            found.append(f"{table}.{ref['col']} ({n} row(s), ON DELETE {action})")
    return found


class Checked:
    """What the refusal checks established: the runs this teardown may delete, whether the registry row was found active, and notes for
    the listing (how the stamp was proved)."""

    def __init__(self, owned: list[str], registry_active: bool, notes: list[str]):
        self.owned, self.registry_active, self.notes = owned, registry_active, notes


def _refusal_checks(cur) -> "Checked":
    """Every guard, fail-closed, evaluated INSIDE the locks. Raises TeardownRefused; nothing is deleted. Returns the ids of the
    small-test runs this teardown may delete (every one proven to be exclusively this asset's) and whether the registry row was found
    ACTIVE (only then is it updated)."""
    shared.refuse_if_frozen(cur)                      # published / sealed / serving: the SAME check the dispatch makes

    notes: list[str] = []
    # ACTIVE: any run on the chart, whatever its scope or assets
    cur.execute("SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running', 'paused')", (CHART_ID,))
    active = cur.fetchall()
    if active:
        raise TeardownRefused(
            f"active build_runs {[(str(r['id']), r['state']) for r in active]} on chart {CHART_ID} — stop active execution first")

    # MEMBERSHIP: the runs that actually include this asset (build_run_assets, or the asset named in a comma-separated scope_target)
    cur.execute(
        """SELECT r.id, r.triggered_by, r.scope, r.scope_target,
                  COALESCE(array_agg(DISTINCT a.asset_id) FILTER (WHERE a.asset_id IS NOT NULL), '{}') AS assets
           FROM build_runs r LEFT JOIN build_run_assets a ON a.run_id = r.id
           WHERE r.chart_id = %s
           GROUP BY r.id, r.triggered_by, r.scope, r.scope_target
           HAVING bool_or(a.asset_id = %s)
               OR (r.scope_target IS NOT NULL AND %s = ANY(string_to_array(r.scope_target, ',')))""",
        (CHART_ID, ASSET_ID, ASSET_ID))
    members = cur.fetchall()
    non_test = [str(r["id"]) for r in members if r["triggered_by"] != TRIGGERED_BY]
    if non_test:
        raise TeardownRefused(
            f"{len(non_test)} NON-test build run(s) include {ASSET_ID} on chart {CHART_ID} (run ids {non_test}; "
            f"triggered_by other than '{TRIGGERED_BY}'; layer runs and multi-asset sets count) — a real build was dispatched; "
            "this script only removes the small test")
    owned: list[str] = []
    for r in members:
        targets = {t.strip() for t in (r["scope_target"] or "").split(",") if t.strip()}
        others = sorted(({a for a in (r["assets"] or [])} | targets) - {ASSET_ID})
        if others:
            raise TeardownRefused(
                f"small-test run {r['id']} is not exclusively {ASSET_ID}'s: it also names {others} — deleting it would remove "
                "their bookkeeping and orphan their receipts; resolve it by hand")
        owned.append(str(r["id"]))

    if owned:
        cur.execute(
            "SELECT asset_id, count(*) AS n FROM asset_provenance_receipts WHERE build_id = ANY(%s::uuid[]) AND asset_id <> %s"
            " GROUP BY asset_id", (owned, ASSET_ID))
        foreign = cur.fetchall()
        if foreign:
            raise TeardownRefused(
                f"provenance receipts of other assets {[r['asset_id'] for r in foreign]} are linked to the small-test run(s) "
                f"{owned} — deleting those runs would orphan them")
        cur.execute(
            "SELECT chart_id, count(*) AS n FROM asset_provenance_receipts WHERE build_id = ANY(%s::uuid[]) AND asset_id = %s"
            " AND chart_id IS DISTINCT FROM %s::uuid GROUP BY chart_id", (owned, ASSET_ID, CHART_ID))
        elsewhere = cur.fetchall()
        if elsewhere:
            raise TeardownRefused(
                f"the small-test run(s) {owned} also hold receipts of {ASSET_ID} on other chart(s) "
                f"{[(str(r['chart_id']), int(r['n'])) for r in elsewhere]} — deleting the runs would set those receipts' run link to "
                "NULL; this script only removes the pinned chart's small test")

    # RECEIPTS: deleted by asset and chart, so each must be PROVEN the test's: a run link to an owned test run
    cur.execute(
        "SELECT partition_key, build_id FROM asset_provenance_receipts WHERE asset_id = %s AND chart_id = %s",
        (ASSET_ID, CHART_ID))
    receipts = cur.fetchall()
    unlinked = [r["partition_key"] for r in receipts if r["build_id"] is None]
    if unlinked:
        raise TeardownRefused(
            f"{len(unlinked)} provenance receipt(s) of {ASSET_ID} on chart {CHART_ID} carry NO run link (partitions {unlinked}): "
            "their origin cannot be proven (a pruned test run and a pruned real run look the same; the cockpit watchdog deletes "
            f"terminal runs after {RETENTION_DAYS} days) and a current manifest stamp cannot establish it retroactively — they are "
            f"preserved; follow the steward recovery runbook {RUNBOOK}")
    foreign_links = sorted({str(r["build_id"]) for r in receipts if str(r["build_id"]) not in owned})
    if foreign_links:
        raise TeardownRefused(
            f"provenance receipt(s) of {ASSET_ID} on chart {CHART_ID} belong to run(s) {foreign_links} that are not "
            f"'{TRIGGERED_BY}' runs of this asset — those are not small-test evidence")

    # OTHER REFERENCES to the owned runs, found from the catalog: deleting a run sets every ON DELETE SET NULL reference to NULL
    # (conversations, the prediction and calibration ledgers, ...) and a NO ACTION one makes the DELETE fail; name them instead
    run_refs = _referencing_rows(cur, "build_runs", owned, set(RUN_REFERENCES_SKIP))
    if run_refs:
        raise TeardownRefused(
            f"other tables reference the small-test run(s) {owned}: {run_refs} — deleting the runs would change or fail on them; "
            "this script only removes the small test's own rows; resolve them by hand")

    # LEGACY ledger tables: not the v5 writer's; rows of '5.0' are refused and named, never deleted
    found_legacy = {}
    for table in LEGACY_GUARD_TABLES:
        if not _table_exists(cur, table):
            continue
        n = _count(cur, f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s", (CHART_ID, GENERATION))
        if n:
            found_legacy[table] = n
    if found_legacy:
        raise TeardownRefused(
            f"the legacy ledger table(s) {found_legacy} hold '5.0' rows for chart {CHART_ID}: the v5 writer writes none, so they "
            "are not this test's — this script never touches them; resolve them by hand")

    # OWNERSHIP of the generation's output: the SHARED proof (v5_small_test_shared, the one copy the dispatch uses too): the CURRENT
    # manifest must PROVE this test's slice, and the stored snapshot and inventory headers must carry the SAME vector identity
    manifest, _rows = shared.generation_ownership(cur, owned, notes=notes,
                                                  remedy="re-dispatch the slice (which replaces the chain), then tear down")
    if manifest is not None:
        # the manifest is deleted last: any table that references it (found from the catalog) other than the ones this script deletes
        # first — notably kala_gochara_contacts.input_generation_vector_id, NO ACTION — would make that DELETE fail with a bare SQLSTATE
        manifest_refs = _referencing_rows(cur, "kala_gochara_publication", [str(manifest["manifest_id"])],
                                          {t for t, _ in GENERATION_TABLES})
        if manifest_refs:
            raise TeardownRefused(
                f"other tables reference the '5.0' manifest of chart {CHART_ID}: {manifest_refs} — deleting the manifest would fail "
                "(or change them); the legacy ledger rows are not this writer's, resolve them by hand")

    # THE N-137 END STATE, before anything is deleted (and again, below, before success is claimed)
    # a freshness row elsewhere + an active registry row: the inertness restore fires migration 596's invalidation on ALL charts
    cur.execute("SELECT is_active FROM asset_registry WHERE asset_id = %s", (ASSET_ID,))
    reg = cur.fetchone()
    if reg is not None and reg["is_active"] is True:
        other = _count(cur, "SELECT count(*) AS n FROM asset_freshness WHERE asset_id = %s AND chart_id IS DISTINCT FROM %s::uuid",
                       (ASSET_ID, CHART_ID))
        if other:
            raise TeardownRefused(
                f"the registry row of {ASSET_ID} is ACTIVE and {other} freshness row(s) of it exist on other chart(s): restoring it "
                "inert fires migration 596's registry invalidation, which marks the asset's freshness stale on EVERY chart. "
                "Refusing rather than changing other charts' projections; investigate why another chart holds freshness for the "
                "small-test asset first")
    problems = _end_state_problems(cur)
    if problems:
        raise TeardownRefused("the N-137 end state does not hold: " + "; ".join(problems))
    return Checked(owned, bool(reg is not None and reg["is_active"] is True), notes)


def _retention_lines(cur, owned: list[str]) -> list[str]:
    """For each owned run: when it was created and how many days of the cockpit watchdog's retention remain."""
    if not owned:
        return []
    cur.execute(
        f"""SELECT id, created_at, EXTRACT(EPOCH FROM (created_at + INTERVAL '{RETENTION_DAYS} days' - now())) AS secs
            FROM build_runs WHERE id = ANY(%s::uuid[]) ORDER BY created_at""", (owned,))
    lines = []
    for r in cur.fetchall():
        days = float(r["secs"]) / 86400.0
        lines.append(f"run {r['id']} created {r['created_at']}: {days:.1f} day(s) of the {RETENTION_DAYS}-day cockpit retention remain"
                     + ("" if days > 0 else " — PAST RETENTION: a pruned run's receipts would already refuse"))
    return lines


def _plan_counts(cur, owned: list[str]) -> dict:
    counts: dict = {}
    counts["asset_provenance_receipts"] = _count(
        cur, "SELECT count(*) AS n FROM asset_provenance_receipts WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    counts["asset_freshness"] = _count(
        cur, "SELECT count(*) AS n FROM asset_freshness WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    counts["build_run_assets"] = _count(
        cur, "SELECT count(*) AS n FROM build_run_assets WHERE run_id = ANY(%s::uuid[])", (owned,))
    counts["build_runs"] = len(owned)
    counts["asset_throughput"] = _count(
        cur, "SELECT count(*) AS n FROM asset_throughput WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    for table, extra in GENERATION_TABLES:
        counts[table] = _count(
            cur, f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s{extra}", (CHART_ID, GENERATION))
    for table in LEGACY_GUARD_TABLES:
        counts[table] = "guard-only (never deleted)" if _table_exists(cur, table) else "absent"
    return counts


def _delete_everything(cur, owned: list[str]) -> None:
    cur.execute("DELETE FROM asset_provenance_receipts WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    cur.execute("DELETE FROM asset_freshness WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    cur.execute("DELETE FROM build_run_assets WHERE run_id = ANY(%s::uuid[])", (owned,))
    cur.execute("DELETE FROM build_runs WHERE id = ANY(%s::uuid[])", (owned,))
    cur.execute("DELETE FROM asset_throughput WHERE asset_id = %s AND chart_id = %s", (ASSET_ID, CHART_ID))
    for table, extra in GENERATION_TABLES:
        cur.execute(f"DELETE FROM {table} WHERE chart_id = %s AND generation = %s{extra}", (CHART_ID, GENERATION))


def _note_outcome(exc: BaseException, outcome: str) -> None:
    """Attach what is KNOWN about the transaction to the exception, for the process boundary to report."""
    try:
        exc.teardown_outcome = outcome            # type: ignore[attr-defined]
    except Exception:                             # an exception type that refuses attributes: the boundary then reports 'unknown'
        pass


OUTCOME_TEXT = {
    "no_transaction": "No transaction was opened.",
    "rolled_back": "ROLLBACK CONFIRMED: this run changed nothing in the database.",
    "rollback_unconfirmed": ("ROLLBACK NOT CONFIRMED: the rollback itself failed. No COMMIT was sent, so the server rolls the "
                             "transaction back when the session ends, but this run did not observe that."),
    "committed": ("COMMIT CONFIRMED: the transaction COMMITTED; only reporting the result failed afterwards. The deletes are done. Run "
                  "the dry run to see the state; do not run the execution again."),
    "unlabelled": ("What happened to the transaction was not recorded for this failure. Run the dry run (it rehearses every check and shows "
                   "what remains) before any retry."),
    "commit_unknown": ("COMMIT OUTCOME UNKNOWN: the COMMIT statement was sent and no confirmation came back. The transaction may or "
                       "may not have committed. Run the dry run (it rehearses every check and shows what remains) before any retry; "
                       "do not assume either way."),
}


def teardown(*, dry_run: bool = True) -> None:
    import psycopg
    import psycopg.rows

    try:
        conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    except BaseException as exc:
        _note_outcome(exc, "no_transaction")
        raise
    conn.autocommit = False
    cur = conn.cursor()
    phase = "open"                                # open -> committing (COMMIT sent) -> committed
    report: tuple | None = None
    try:
        _require_direct_connection(conn)                   # refuses a pooled connection (the session lock would hold nothing)
        _take_locks(cur)                                   # BEFORE any ownership check; held to commit / rollback
        checked = _refusal_checks(cur)
        owned, registry_active = checked.owned, checked.registry_active
        _validate_registry_row(cur, check_active=False)
        retention = _retention_lines(cur, owned)
        counts = _plan_counts(cur, owned)
        # THE SAME STATEMENTS in both modes: the deletes, the registry restore and the end-state validation run in this transaction
        _delete_everything(cur, owned)
        if registry_active:                                # ONLY a row found active is touched: no UPDATE privilege otherwise needed
            cur.execute("UPDATE asset_registry SET is_active = false WHERE asset_id = %s", (ASSET_ID,))
        _validate_registry_row(cur)
        post = _end_state_problems(cur)
        if post:
            raise TeardownRefused("the N-137 end state does not hold after the deletes, so success is not claimed: " + "; ".join(post))
        if dry_run:
            conn.rollback()
            report = ("dry_run", counts, retention + [f"stamp: {n}" for n in checked.notes])
        else:
            phase = "committing"
            conn.commit()
            phase = "committed"
            report = ("executed", counts, retention + [f"stamp: {n}" for n in checked.notes])
    except BaseException as exc:
        if phase == "committing":
            _note_outcome(exc, "commit_unknown")
        else:
            try:
                conn.rollback()
                _note_outcome(exc, "rolled_back")
            except BaseException:
                _note_outcome(exc, "rollback_unconfirmed")
        raise
    finally:
        if phase != "committing":
            _release_orchestrator_lock(conn)
        try:
            conn.close()
        except Exception:
            pass
    kind, counts, retention = report
    try:                                          # a failure while REPORTING keeps the outcome that is already known (item 3)
        if kind == "dry_run":
            print(f"[dry-run] the SAME statements an execution runs (locks, checks, every DELETE, the registry restore when the row is "
                  f"active, the end-state validation) ran for chart {CHART_ID} and were ROLLED BACK — zero commits; pass --execute "
                  f"--i-am-steward to delete:", file=sys.stderr)
            for name, n in counts.items():
                print(f"{name}\t{n}")
            for line in retention:
                print(f"stamp\t{line[len('stamp: '):]}" if line.startswith("stamp: ") else f"retention\t{line}")
            return
        print(f"[teardown] COMMITTED: removed the small-test run bookkeeping, its provenance receipts and freshness row, the output "
              f"chain, the search inventory and the candidate manifest for chart {CHART_ID} generation '5.0'; asset_registry row kept "
              f"(restored to inert only if it was found active) in its migration-1304 shape — one transaction", file=sys.stderr)
    except BaseException as exc:
        _note_outcome(exc, "committed" if kind == "executed" else "rolled_back")
        raise


def _safe_failure(exc: BaseException) -> str:
    """The class (and SQLSTATE) only — a connection or parse error can carry the credentials in its text — and what is KNOWN about the
    transaction. 'Unchanged' is claimed only when a rollback was confirmed."""
    kind = f"{type(exc).__module__}.{type(exc).__name__}"
    state = getattr(exc, "sqlstate", None)
    known = OUTCOME_TEXT.get(getattr(exc, "teardown_outcome", None) or "unlabelled", OUTCOME_TEXT["unlabelled"])
    return (f"teardown failed: {kind}{f' (SQLSTATE {state})' if state else ''}. The exception text is withheld because a "
            f"connection error can carry credentials. {known}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="teardown_v5_small_test_job.py",
        description="Fail-closed teardown of the ka_gochara_v5 SMALL TEST run (pinned chart only). Dry run by default (the SAME "
                    "statements as an execution, rolled back); deleting needs --execute AND --i-am-steward. DATABASE_URL comes "
                    "from the environment only. Run it within 90 days of the small test (cockpit retention).")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="the default: the same statements as an execution, then ROLL BACK")
    mode.add_argument("--execute", action="store_true", help="delete (needs --i-am-steward)")
    p.add_argument("--i-am-steward", action="store_true", help="confirms a steward authorised this deletion")
    args = p.parse_args(argv)
    if args.execute and not args.i_am_steward:
        p.error("--execute needs --i-am-steward (destruction requires explicit steward intent)")
    if not os.environ.get("DATABASE_URL"):
        print("teardown refused: DATABASE_URL is not set in the process environment (this script reads no file and takes no "
              "URL argument).", file=sys.stderr)
        return 2
    try:
        teardown(dry_run=not args.execute)
    except TeardownRefused as exc:
        outcome = OUTCOME_TEXT.get(getattr(exc, "teardown_outcome", None) or "unlabelled", OUTCOME_TEXT["unlabelled"])
        print(f"teardown refused: {exc}\n{outcome}", file=sys.stderr)
        return 1
    except Exception as exc:                       # noqa: BLE001 — the boundary: print the class, never the text
        print(_safe_failure(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
