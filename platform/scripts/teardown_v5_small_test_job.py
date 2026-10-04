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

Then deletes, in ONE commit, in this order: provenance receipts and the freshness row of this asset on the chart; build_run_assets
and build_runs of the exclusively-owned test runs (by id); the asset_throughput row; the OUTPUT CHAIN of (chart, '5.0') in the
order RecordStore.delete_generation_chain uses; the SEARCH INVENTORY in the order InventoryStore.delete_generation_inventory uses,
then the input snapshot; the candidate manifest. KEPT: the asset_registry row (restored inert, is_active = false, and verified
field by field against the migration-1304 small-test shape), the global sky-event substrate, Moon on-demand coverage partitions,
every other chart, generation and asset.

DATABASE ROLE. The script runs as ONE role; it never assumes the admin role. The privileges it needs, table by table, are in the
steward runbook above (section "Which role").

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
# The legacy v4 ledger tables are NOT written by the v5 writer: GUARD-ONLY. A table that does not exist is skipped (named `absent`
# in the listing); rows of '5.0' in one are not this test's, and the teardown refuses and names them.
LEGACY_GUARD_TABLES = ("kala_gochara_windows", "kala_gochara_contacts")


class TeardownRefused(RuntimeError):
    """A named refusal: nothing was deleted. The message holds ids and counts only, never connection text."""


def _writer():
    """The sidecar writer module: its slice validator is the SINGLE implementation of what a valid stamp is."""
    sidecar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python-sidecar"))
    if sidecar not in sys.path:
        sys.path.insert(0, sidecar)
    try:
        import pipeline.orchestrator.writers.ka_gochara_v5 as writer
    except Exception as exc:  # an environment without the sidecar deps cannot validate: refuse, never skip
        raise TeardownRefused(
            f"cannot import the ka_gochara_v5 writer to validate the slice stamp ({type(exc).__name__}); run this from an "
            "environment with the sidecar dependencies — the stamp is never accepted unvalidated") from None
    return writer


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
            continue                                  # before the flip the row is as the test left it (active)
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
        conn.rollback()                       # nothing is open; the unlock below runs outside any transaction
        conn.autocommit = True
        conn.cursor().execute("SELECT pg_advisory_unlock(hashtext(%s))", (CHART_ID,))
    except Exception:
        pass


def _same_instant(a, b) -> bool:
    try:
        return a == b
    except TypeError:
        return False


def _stamp_problem(vector, horizon) -> str | None:
    """None when the manifest's input vector PROVES a test slice, by the WRITER'S OWN validation: the stamp's marker is rebuilt from
    the component and validated by `ka_gochara_v5._validate_test_slice` (schema, run, classes among the scored classes, tz-aware
    ISO horizon, the run's own shape rules), and the component must equal what the writer's `_slice_component` produces for that
    marker (which includes the marker DIGEST recomputed). The manifest's horizon must be the stamp's horizon."""
    writer = _writer()
    if not isinstance(vector, dict):
        return "the manifest carries no input vector"
    if vector.get("stored_scope") != writer.TEST_SLICE_SCOPE:
        return f"stored_scope is {vector.get('stored_scope')!r}, not {writer.TEST_SLICE_SCOPE!r}"
    comp = vector.get("test_slice")                   # the component key the writer stamps (ka_gochara_v5, the input-vector stamp check)
    if not isinstance(comp, dict):
        return "no 'test_slice' component"
    marker = {"schema": comp.get("schema"), "run": comp.get("run"), "horizon": comp.get("horizon"), "classes": comp.get("classes")}
    try:
        sliced = writer._validate_test_slice(marker)
    except writer.TestSliceRefusal as exc:
        return f"the stamp's marker fails the writer's own validation ({exc})"
    except Exception as exc:  # noqa: BLE001 — any other failure to validate is a refusal, never an acceptance
        return f"the stamp's marker could not be validated ({type(exc).__name__})"
    if comp != writer._slice_component(sliced):
        return ("the stamp is not the writer's component for its marker (the marker digest or a normalised field differs from "
                "what the writer's own _slice_component produces)")
    if horizon is None or not (_same_instant(getattr(horizon, "lower", None), sliced.horizon[0])
                               and _same_instant(getattr(horizon, "upper", None), sliced.horizon[1])):
        return "the manifest's horizon is not the stamp's horizon"
    return None


def _stamped_classes(vector) -> list[str]:
    return list((vector.get("test_slice") or {}).get("classes") or [])


def _generation_rows(cur) -> int:
    total = 0
    for table, extra in OUTPUT_TABLES:
        total += _count(cur, f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s{extra}",
                        (CHART_ID, GENERATION))
    return total


def _end_state_problems(cur) -> list[str]:
    """The Nirmana N-137 end state for the v5 asset (definitions.ts, NIRMANA_STAGED_INERT_CANDIDATE_RULES and runtimeEvidenceSql):
    catalog_status not RETIRED, nothing depends on the asset, and NO receipt or build_run_assets row of the asset on ANY chart
    from a run that is not a 'gochara-v5-small-test' run (a receipt whose run is gone reads as non-test). Returned as named
    problems; empty means the monitor would still exclude the asset as an unsealed test candidate."""
    problems: list[str] = []
    cur.execute("SELECT catalog_status FROM asset_registry WHERE asset_id = %s", (ASSET_ID,))
    row = cur.fetchone()
    if row is None:
        problems.append(f"asset_registry row for {ASSET_ID} is missing")
    elif row["catalog_status"] == "RETIRED":
        problems.append(f"the registry row's catalog_status is RETIRED (rule N-137 requires it not to be)")
    cur.execute("SELECT asset_id FROM asset_registry WHERE %s = ANY(depends_on)", (ASSET_ID,))
    dependents = [r["asset_id"] for r in cur.fetchall()]
    if dependents:
        problems.append(f"asset(s) {dependents} list {ASSET_ID} in depends_on (rule N-137: nothing may depend on it)")
    cur.execute(
        """SELECT r.chart_id, count(*) AS n FROM asset_provenance_receipts r
           WHERE r.asset_id = %s
             AND NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = r.build_id AND b.triggered_by = %s)
           GROUP BY r.chart_id""", (ASSET_ID, TRIGGERED_BY))
    receipts = cur.fetchall()
    if receipts:
        problems.append("receipts of the asset from a non-test run (or with no run link) exist on chart(s) "
                        f"{[(str(r['chart_id']), int(r['n'])) for r in receipts]}")
    cur.execute(
        """SELECT b0.chart_id, count(*) AS n FROM build_run_assets a LEFT JOIN build_runs b0 ON b0.id = a.run_id
           WHERE a.asset_id = %s
             AND NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = a.run_id AND b.triggered_by = %s)
           GROUP BY b0.chart_id""", (ASSET_ID, TRIGGERED_BY))
    run_assets = cur.fetchall()
    if run_assets:
        problems.append("build_run_assets rows of the asset from a non-test run exist on chart(s) "
                        f"{[(str(r['chart_id']), int(r['n'])) for r in run_assets]}")
    return problems


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

    # OWNERSHIP of the generation's output: the CURRENT manifest must PROVE this test's slice, and the stored snapshot and inventory
    # headers must carry the SAME vector identity as that manifest
    rows = _generation_rows(cur)
    cur.execute("SELECT status, input_generation_vector, horizon FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                (CHART_ID, GENERATION))
    manifest = cur.fetchone()
    if rows or manifest:
        if manifest is None:
            raise TeardownRefused(
                f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} with NO manifest — nothing proves they are the "
                "small test's; this script never touches them")
        problem = _stamp_problem(manifest["input_generation_vector"], manifest["horizon"])
        if manifest["status"] != "candidate" or problem:
            raise TeardownRefused(
                f"the '5.0' manifest of chart {CHART_ID} is not PROVEN to be a test slice ("
                f"{'status ' + repr(manifest['status']) if manifest['status'] != 'candidate' else problem}) — a historical "
                f"'{TRIGGERED_BY}' run never authorises deleting an unproven candidate; {rows} output row(s) are untouched")
        classes = _stamped_classes(manifest["input_generation_vector"])
        cur.execute(
            """SELECT (s.input_generation_vector = p.input_generation_vector) AS same_vector, s.input_digest
               FROM ka_gochara_search_input_snapshot s
               JOIN kala_gochara_publication p ON p.chart_id = s.chart_id AND p.generation = s.generation
               WHERE s.chart_id = %s AND s.generation = %s""", (CHART_ID, GENERATION))
        snapshot = cur.fetchone()
        if snapshot is None:
            if rows:
                raise TeardownRefused(
                    f"{rows} generation '5.0' output row(s) exist for chart {CHART_ID} but no input snapshot binds them to the "
                    "stamped manifest — their origin is unproven; re-dispatch the slice (which replaces the chain), then tear down")
        else:
            if snapshot["same_vector"] is not True:
                raise TeardownRefused(
                    f"the stored input snapshot of chart {CHART_ID} '5.0' carries a DIFFERENT input vector from the stamped "
                    "manifest: a later slice stamped the manifest and its snapshot substep has not yet replaced the older output "
                    "(an interrupted replacement) — the output is not provably this test's. Re-dispatch the slice (which "
                    "replaces the chain), then tear down")
            cur.execute(
                """SELECT count(*) AS n FROM ka_gochara_search_inventory i
                   JOIN ka_gochara_search_input_snapshot s ON s.chart_id = i.chart_id AND s.generation = i.generation
                   JOIN kala_gochara_publication p ON p.chart_id = i.chart_id AND p.generation = i.generation
                   WHERE i.chart_id = %s AND i.generation = %s
                     AND (i.input_digest <> s.input_digest OR i.horizon <> p.horizon OR NOT (i.event_class = ANY(%s::text[])))""",
                (CHART_ID, GENERATION, classes))
            bad = int(cur.fetchone()["n"])
            if bad:
                raise TeardownRefused(
                    f"{bad} inventory header(s) of chart {CHART_ID} '5.0' do not carry the stamped manifest's identity (input "
                    "digest, horizon, or a class outside the stamp) — the output is not provably this test's; re-dispatch the "
                    "slice, then tear down")

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
    return owned


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
    "commit_unknown": ("COMMIT OUTCOME UNKNOWN: the COMMIT statement was sent and no confirmation came back. The transaction may or "
                       "may not have committed. Run the dry run (it rehearses every check and shows what remains) before any retry; "
                       "do not assume either way."),
}


def teardown(*, dry_run: bool = True) -> None:
    import psycopg
    import psycopg.rows

    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    phase = "open"                                # open -> committing (COMMIT sent) -> committed
    report: tuple | None = None
    try:
        _take_locks(cur)                                   # BEFORE any ownership check; held to commit / rollback
        owned = _refusal_checks(cur)
        _validate_registry_row(cur, check_active=False)
        retention = _retention_lines(cur, owned)
        counts = _plan_counts(cur, owned)
        # THE SAME STATEMENTS in both modes: the deletes, the registry restore and the end-state validation run in this transaction
        _delete_everything(cur, owned)
        cur.execute("UPDATE asset_registry SET is_active = false WHERE asset_id = %s", (ASSET_ID,))
        _validate_registry_row(cur)
        post = _end_state_problems(cur)
        if post:
            raise TeardownRefused("the N-137 end state does not hold after the deletes, so success is not claimed: " + "; ".join(post))
        if dry_run:
            conn.rollback()
            report = ("dry_run", counts, retention)
        else:
            phase = "committing"
            conn.commit()
            phase = "committed"
            report = ("executed", counts, retention)
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
    if kind == "dry_run":
        print(f"[dry-run] the SAME statements an execution runs (locks, checks, every DELETE, the registry restore, the end-state "
              f"validation) ran for chart {CHART_ID} and were ROLLED BACK — zero commits; pass --execute --i-am-steward to delete:",
              file=sys.stderr)
        for name, n in counts.items():
            print(f"{name}\t{n}")
        for line in retention:
            print(f"retention\t{line}")
        return
    print(f"[teardown] COMMITTED: removed the small-test run bookkeeping, its provenance receipts and freshness row, the output "
          f"chain, the search inventory and the candidate manifest for chart {CHART_ID} generation '5.0'; asset_registry row kept "
          f"and restored to inert (is_active=false) in its migration-1304 shape — one transaction", file=sys.stderr)


def _safe_failure(exc: BaseException) -> str:
    """The class (and SQLSTATE) only — a connection or parse error can carry the credentials in its text — and what is KNOWN about the
    transaction. 'Unchanged' is claimed only when a rollback was confirmed."""
    kind = f"{type(exc).__module__}.{type(exc).__name__}"
    state = getattr(exc, "sqlstate", None)
    known = OUTCOME_TEXT.get(getattr(exc, "teardown_outcome", None) or "no_transaction", OUTCOME_TEXT["commit_unknown"])
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
        outcome = OUTCOME_TEXT.get(getattr(exc, "teardown_outcome", None) or "no_transaction", OUTCOME_TEXT["commit_unknown"])
        print(f"teardown refused: {exc}\n{outcome}", file=sys.stderr)
        return 1
    except Exception as exc:                       # noqa: BLE001 — the boundary: print the class, never the text
        print(_safe_failure(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
