"""
teardown_v5_small_test_job.py — Pravāha C38: teardown for the SMALL TEST build
of ka_gochara_v5 staged by dispatch_v5_small_test_job.py (C37).

Pinned chart only (482012f1-710e-4a25-994a-93821f5871aa; there is no chart argument), ONE transaction, fail-closed.

RUNNING IT
  DESTRUCTION NEEDS INTENT. The default is a dry run: every refusal check runs, the would-delete counts are listed, the
  transaction is rolled back and nothing is written. Deleting needs BOTH `--execute` and `--i-am-steward`.
  The database URL comes ONLY from the process environment (DATABASE_URL): never from an argument, never from a file in the
  checkout (this script no longer reads `.env.local`), never printed. A failure prints the exception CLASS (and the SQLSTATE
  when there is one), never the exception text: a connection error can carry the credentials.

SYNCHRONISATION (Codex P1-1)
  Before ANY ownership check the script takes, in the order the orchestrator uses, (1) the per-chart orchestrator exclusion lock
  (`pg_try_advisory_lock(hashtext(chart))`, non-blocking: if a build run holds it, the teardown refuses) and (2) the Gochara
  chart lock `ka_gochara_lock_chart` (transaction-scoped, behind a `lock_timeout` so a competing writer makes the teardown fail
  closed instead of waiting). Both are held to commit; every check below is evaluated INSIDE them, so nothing can commit between a
  check and the delete it authorises.

REFUSES (loudly, nothing deleted) when ANY of these holds:
  1. the orchestrator exclusion lock or the Gochara chart lock cannot be taken;
  2. a kala_gochara_publication row for the chart at '5.0' is `published`, or a ka_gochara_generation_seal row exists for it, or
     kala_gochara_authority names '5.0' (published / sealed / serving generations are never torn down);
  3. ANY build run on the chart is planned / running / paused (whatever its scope or assets);
  4. a build run whose MEMBERSHIP includes this asset (a `build_run_assets` row, or the asset named in a comma-separated
     `scope_target`; layer runs and multi-asset sets included) was not triggered by 'gochara-v5-small-test';
  5. a small-test run is not EXCLUSIVELY this asset's: any `build_run_assets` row for another asset, another asset in its
     `scope_target`, or another asset's provenance receipt linked to it (deleting the run would orphan or destroy that);
  6. a provenance receipt of this asset on the chart has NO run link (its origin is unprovable: preserved, named), or links to a
     run that is not one of the small-test runs counted above;
  7. generation '5.0' output (chain, inventory, snapshot) or a manifest exists and the CURRENT manifest is not PROVEN to be a test
     slice: status candidate, stored_scope = 'test_slice' and a `test_slice` component naming its run, classes and horizon. A
     historical test run never authorises deleting an unstamped candidate;
  8. the legacy ledger tables `kala_gochara_windows` / `kala_gochara_contacts` hold '5.0' rows for the chart (the v5 writer
     writes neither; such rows are not this test's and are named, never deleted).

Then deletes, in ONE commit, in this order:
    provenance receipts and the freshness projection of this asset on the chart (by asset and chart, so no receipt is left with a
      NULL run link — the link is ON DELETE SET NULL and the Nirmana monitor, rule N-137, reads a receipt whose run cannot be found
      as NON-test evidence);
    build_run_assets and build_runs of the exclusively-owned test runs only; the asset_throughput row;
    the OUTPUT CHAIN of (chart, '5.0'), in the order RecordStore.delete_generation_chain uses (windows → records → contacts →
      event-class coverage; membership and prerequisites cascade);
    the SEARCH INVENTORY, in the order InventoryStore.delete_generation_inventory uses, then the input snapshot;
    the candidate manifest (proven to be the test slice's).
KEPT: the asset_registry row (migration 1243 inserts it permanently; deleting it would fail the orchestrator's writer-gap
preflight on every build run) — restored inert (is_active = false) in the same transaction and verified field by field against the
migration-1304 small-test shape; the global sky-event substrate; Moon on-demand coverage partitions; every other chart, generation
and asset.

Usage:
  cd <repo-root>/platform
  DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py                          # dry run (the default)
  DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py --execute --i-am-steward  # delete
"""
from __future__ import annotations

import argparse
import os
import sys

ASSET_ID = "ka_gochara_v5"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"
GENERATION = "5.0"
SLICE_SCOPE = "test_slice"
SLICE_RUNS = ("all_classes_1y", "one_class_full")         # the run names the writer's marker validation accepts
ACTIVE_STATES = ("planned", "running", "paused")
LOCK_TIMEOUT = "10s"                                       # the chart lock is requested behind this: fail closed, never wait forever

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

# (table, extra WHERE) — the order is the deletion order and the dry-run listing order. The chain and inventory orders are
# the kernel's own (RecordStore.delete_generation_chain, InventoryStore.delete_generation_inventory); a test runs the REAL
# helpers against a recording connection and compares.
CHAIN_TABLES = (
    ("ka_gochara_eval_window", ""),                 # window membership cascades with it
    ("ka_gochara_relationship_record", ""),         # prerequisites cascade with it
    ("ka_gochara_contact", ""),                     # ALL of the generation's contacts (orphans and shared ones too)
    ("kala_gochara_coverage", " AND partition_kind = 'event_class'"),   # last: records / windows reference it
)
INVENTORY_TABLES = (
    ("ka_gochara_search_interval", ""),
    ("ka_gochara_search_obligation", ""),
    ("ka_gochara_search_path_pin", ""),
    ("ka_gochara_search_inventory", ""),            # its verification rows cascade
    ("ka_gochara_search_input_snapshot", ""),
)
MANIFEST_TABLE = ("kala_gochara_publication", "")   # the candidate manifest: last, and only once proven to be the slice's
GENERATION_TABLES = CHAIN_TABLES + INVENTORY_TABLES + (MANIFEST_TABLE,)
OUTPUT_TABLES = CHAIN_TABLES + INVENTORY_TABLES     # what "generation output exists" means (the manifest is judged on its own)
# The legacy v4 ledger tables are NOT written by the v5 writer and are not part of every database's migration chain: they are
# only GUARDED. A table that does not exist is skipped (named `absent` in the dry-run listing); rows of '5.0' in one are not
# this test's, and the teardown refuses and names them.
LEGACY_GUARD_TABLES = ("kala_gochara_windows", "kala_gochara_contacts")


class TeardownRefused(RuntimeError):
    """A named refusal: nothing was deleted. The message holds ids and counts only, never connection text."""


def _count(cur, sql: str, params: tuple = ()) -> int:
    cur.execute(sql, params)
    return int(cur.fetchone()["n"])


def _table_exists(cur, table: str) -> bool:
    cur.execute("SELECT to_regclass(%s) AS r", (f"public.{table}",))
    return cur.fetchone()["r"] is not None


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
            continue                                  # a dry run sees the row as the test left it (active)
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if actual != expected:
            raise TeardownRefused(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — "
                "the registry row must be its migration-1304 small-test self after teardown "
                "(apply 1304; never edit the row by hand)")


def _take_locks(cur) -> None:
    """(1) the orchestrator's per-chart exclusion lock — the one `acquire_chart_lock` takes for a build run, session-level and
    non-blocking; (2) the Gochara chart lock the writers and the replace take, transaction-scoped, behind a lock_timeout. Both
    BEFORE any ownership check; both held to commit/rollback (the first until the connection closes)."""
    cur.execute("SELECT pg_try_advisory_lock(hashtext(%s)) AS got", (CHART_ID,))
    if not cur.fetchone()["got"]:
        raise TeardownRefused(
            f"the orchestrator's exclusion lock for chart {CHART_ID} is held — a build run (or another operator) is active on "
            "this chart; nothing was checked or deleted")
    cur.execute("SELECT set_config('lock_timeout', %s, true)", (LOCK_TIMEOUT,))
    cur.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))


def _release_orchestrator_lock(conn) -> None:
    """Best effort: closing the connection releases a session-level advisory lock anyway."""
    try:
        conn.rollback()                       # nothing is open; the unlock below runs outside any transaction (no second commit)
        conn.autocommit = True
        conn.cursor().execute("SELECT pg_advisory_unlock(hashtext(%s))", (CHART_ID,))
    except Exception:
        pass


def _stamp_problem(vector) -> str | None:
    """None when the manifest's input vector PROVES a test slice: the scope word and a component naming run, classes, horizon."""
    if not isinstance(vector, dict):
        return "the manifest carries no input vector"
    if vector.get("stored_scope") != SLICE_SCOPE:
        return f"stored_scope is {vector.get('stored_scope')!r}, not '{SLICE_SCOPE}'"
    comp = vector.get("test_slice")
    if not isinstance(comp, dict):
        return f"no '{SLICE_SCOPE}' component"
    if comp.get("run") not in SLICE_RUNS:
        return f"the component's run is {comp.get('run')!r}, not one of {list(SLICE_RUNS)}"
    classes = comp.get("classes")
    if not (isinstance(classes, list) and classes and all(isinstance(c, str) for c in classes)):
        return "the component names no classes"
    horizon = comp.get("horizon")
    if not (isinstance(horizon, list) and len(horizon) == 2 and all(isinstance(h, str) for h in horizon)):
        return "the component names no horizon"
    return None


def _generation_rows(cur) -> int:
    total = 0
    for table, extra in OUTPUT_TABLES:
        total += _count(cur, f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s{extra}",
                        (CHART_ID, GENERATION))
    return total


def _refusal_checks(cur) -> list[str]:
    """Every guard, fail-closed, evaluated INSIDE the locks. Raises TeardownRefused; nothing is deleted. Returns the ids of the
    small-test runs this teardown may delete (every one proven to be exclusively this asset's)."""
    cur.execute(
        """SELECT manifest_id FROM kala_gochara_publication
           WHERE chart_id = %s AND generation = %s AND status = 'published'""",
        (CHART_ID, GENERATION),
    )
    published = cur.fetchone()
    if published:
        raise TeardownRefused(
            f"kala_gochara_publication has a PUBLISHED '5.0' manifest {published['manifest_id']} for chart {CHART_ID} "
            "— a published generation is immutable")

    cur.execute(
        """SELECT manifest_id FROM ka_gochara_generation_seal
           WHERE chart_id = %s AND generation = %s""",
        (CHART_ID, GENERATION),
    )
    seal = cur.fetchone()
    if seal:
        raise TeardownRefused(
            f"ka_gochara_generation_seal records '5.0' (manifest {seal['manifest_id']}) for chart {CHART_ID} — a sealed "
            "generation is permanent publication history")

    cur.execute("SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = %s", (CHART_ID,))
    authority = cur.fetchone()
    if authority and authority["authoritative_generation"] == GENERATION:
        raise TeardownRefused(
            f"kala_gochara_authority names '5.0' as the authoritative_generation for chart {CHART_ID} — a serving "
            "generation is never torn down")

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

    # RECEIPTS: deleted by asset and chart, so each must be PROVEN the test's: a run link to an owned test run
    cur.execute(
        "SELECT partition_key, build_id FROM asset_provenance_receipts WHERE asset_id = %s AND chart_id = %s",
        (ASSET_ID, CHART_ID))
    receipts = cur.fetchall()
    unlinked = [r["partition_key"] for r in receipts if r["build_id"] is None]
    if unlinked:
        raise TeardownRefused(
            f"{len(unlinked)} provenance receipt(s) of {ASSET_ID} on chart {CHART_ID} carry NO run link (partitions {unlinked}): "
            "their origin cannot be proven (a pruned test run and a pruned real run look the same) and a current manifest stamp "
            "cannot establish it retroactively — they are preserved; resolve them by hand")
    foreign_links = sorted({str(r["build_id"]) for r in receipts if str(r["build_id"]) not in owned})
    if foreign_links:
        raise TeardownRefused(
            f"provenance receipt(s) of {ASSET_ID} on chart {CHART_ID} belong to run(s) {foreign_links} that are not "
            f"'{TRIGGERED_BY}' runs of this asset — those are not small-test evidence")

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

    # OWNERSHIP of the generation's output: the CURRENT manifest must PROVE a test slice
    rows = _generation_rows(cur)
    cur.execute("SELECT status, input_generation_vector FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                (CHART_ID, GENERATION))
    manifest = cur.fetchone()
    if rows or manifest:
        if manifest is None:
            raise TeardownRefused(
                f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} with NO manifest — nothing proves they are the "
                "small test's; this script never touches them")
        problem = _stamp_problem(manifest["input_generation_vector"])
        if manifest["status"] != "candidate" or problem:
            raise TeardownRefused(
                f"the '5.0' manifest of chart {CHART_ID} is not PROVEN to be a test slice ("
                f"{'status ' + repr(manifest['status']) if manifest['status'] != 'candidate' else problem}) — a historical "
                f"'{TRIGGERED_BY}' run never authorises deleting an unstamped candidate; {rows} output row(s) are untouched")
    return owned


def _dry_run_counts(cur, owned: list[str]) -> dict:
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


def teardown(*, dry_run: bool = True) -> None:
    import psycopg
    import psycopg.rows

    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        _take_locks(cur)                                   # BEFORE any ownership check; held to commit / rollback
        owned = _refusal_checks(cur)
        _validate_registry_row(cur, check_active=False)    # a dry run validates the shape too (a missing row must not pass it)
        if dry_run:
            counts = _dry_run_counts(cur, owned)
            conn.rollback()
            print(f"[dry-run] teardown of the v5 small-test run on chart {CHART_ID} "
                  f"would delete (ROLLED BACK, nothing written; pass --execute --i-am-steward to delete):", file=sys.stderr)
            for name, n in counts.items():
                print(f"{name}\t{n}")
            return
        _delete_everything(cur, owned)
        # The registry row stays (migration 1243) — restore inertness and verify the landed row field by field
        # against the migration-1304 shape, in the same transaction.
        cur.execute("UPDATE asset_registry SET is_active = false WHERE asset_id = %s", (ASSET_ID,))
        _validate_registry_row(cur)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        _release_orchestrator_lock(conn)
        conn.close()
    print(f"[teardown] removed the small-test run bookkeeping, its provenance receipts and freshness row, the output chain, the "
          f"search inventory and the candidate manifest for chart {CHART_ID} generation '5.0'; asset_registry row kept and "
          f"restored to inert (is_active=false) in its migration-1304 shape — one transaction", file=sys.stderr)


def _safe_failure(exc: BaseException) -> str:
    """The class (and SQLSTATE) only: a connection or parse error can carry the credentials in its text."""
    kind = f"{type(exc).__module__}.{type(exc).__name__}"
    state = getattr(exc, "sqlstate", None)
    return (f"teardown failed: {kind}{f' (SQLSTATE {state})' if state else ''}. The exception text is withheld because a "
            "connection error can carry credentials. Nothing was committed.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="teardown_v5_small_test_job.py",
        description="Fail-closed teardown of the ka_gochara_v5 SMALL TEST run (pinned chart only). Dry run by default; "
                    "deleting needs --execute AND --i-am-steward. DATABASE_URL comes from the environment only.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="the default: run every check, list would-delete counts, roll back")
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
        print(f"teardown refused: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:                       # noqa: BLE001 — the boundary: print the class, never the text
        print(_safe_failure(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
