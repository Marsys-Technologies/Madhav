"""C38 — the small-test TEARDOWN executed for real, part 2 (round 2 onwards; split from test_c38_teardown_real_db.py so each CI job stays well inside its budget).

Everything here uses the helpers and fixtures of the first module (imported, not copied): the real chain tables, the stub orchestrator tables and the
exact-privilege role. CI runs the two modules in two parallel jobs (gochara-a55-teardown and gochara-a55-teardown-round2).
"""
from __future__ import annotations

import json
import os

import psycopg
import pytest

from .test_c38_teardown_real_db import (  # noqa: F401  (fixtures and helpers of part 1)
    ASSET, GEN, MARKER, OTHER_CHART, SHORT, _built_stamped_with_test_run, _counts, _default_build, _present, _prune, _refused_and_untouched, _run, _slice_run, _slice_steps, _snapshot, _step, _teardown, json, os, psycopg, pytest, td, threading, time, template, tworld, writer_mod,
)

# ── round 2 (ASTRA v1.1): proven ownership of the existing output, the end state, effects outside the chart, the rehearsal ───────

def _restamp(w, **changes):
    """Rewrite the stamped manifest's component behind the guards (a corrupted or forged stamp)."""
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        for key, value in changes.items():
            w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector,"
                           " %s::text[], %s::jsonb) WHERE generation = %s", (["test_slice", key], json.dumps(value), GEN))


def test_an_interrupted_replacement_a_later_slice_stamped_over_an_older_nontest_chain_is_refused(tworld):
    """Codex round 2 P1, the scenario itself: a failed NON-test candidate leaves its output; a later small test commits its stamped
    manifest and dies before the snapshot substep replaces the old output. Test run + valid stamp: the old output must NOT be deleted."""
    w = tworld
    _default_build(w)                                                           # the older, non-test candidate (default vector, its own snapshot)
    rid = _run(w, marker=MARKER)                                             # the later small test ...
    _step(w, rid, writer_mod.MANIFEST_SUBSTEP)                               # ... committed its stamped manifest, then failed
    assert w.conn.execute("SELECT input_generation_vector->>'stored_scope' FROM public.kala_gochara_publication WHERE generation = %s",
                          (GEN,)).fetchone()[0] == "test_slice"
    assert _counts(w)["ka_gochara_contact"] >= 5                             # the older output is still there
    _refused_and_untouched(w, "interrupted replacement")


@pytest.mark.parametrize("changes", [
    {"classes": [""]},
    {"horizon": ["bogus", "backwards"]},
    {"marker_digest": "0" * 64},
    {"schema": "gochara_v5_test_slice/9"},
    {"run": "one_class_full"},
], ids=["empty_class", "bogus_horizon", "wrong_digest", "wrong_schema", "run_shape_contradicts_classes"])
def test_a_forged_or_corrupted_stamp_is_refused_by_the_writers_own_validation(tworld, changes):
    """Codex drove classes=[''] and horizon=['bogus','backwards'] through to all 15 DELETEs; the writer's validator and the digest now stand in the way."""
    w = tworld
    _slice_run(w)
    _restamp(w, **changes)
    # Codex round 4 T4: the test run row SURVIVES here, so its ORIGINAL marker must prove the stamp and a forged stamp cannot; that
    # rule fires first. (The writer-validation refusals for a stamp with NO surviving run are the unit tests in test_teardown_v5_small_test.)
    _refused_and_untouched(w, "an owned run row survives, so its ORIGINAL marker preimage must prove the stamp")


def test_a_valid_stamp_whose_inventory_header_has_another_identity_is_refused(tworld):
    w = tworld
    _slice_run(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.ka_gochara_search_inventory SET horizon = tstzrange('2025-01-01', '2025-01-05') WHERE generation = %s", (GEN,))
    _refused_and_untouched(w, "inventory header")


def test_a_non_test_receipt_of_the_asset_on_another_chart_breaks_the_n137_end_state(tworld):
    """The monitor's evidence query is asset-wide: any chart, any non-test (or unlinked) receipt keeps the asset out of the excluded set."""
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'x', NULL)",
                   (ASSET, OTHER_CHART))
    _refused_and_untouched(w, f"N-137 end state.*{OTHER_CHART}")


def test_a_non_test_run_asset_row_of_the_asset_on_another_chart_breaks_the_n137_end_state(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    _run(w, triggered_by="cockpit-manual-build", receipt=False, chart=OTHER_CHART)
    _refused_and_untouched(w, f"N-137 end state.*{OTHER_CHART}")


@pytest.mark.parametrize("break_it, match", [
    ("UPDATE public.asset_registry SET catalog_status = 'RETIRED' WHERE asset_id = 'ka_gochara_v5'", "catalog_status is RETIRED"),
    ("UPDATE public.asset_registry SET depends_on = '{ka_gochara_v5}' WHERE asset_id = 'other_asset'", "depends_on"),
], ids=["retired", "a_dependent"])
def test_the_registry_side_of_the_n137_end_state_is_validated(tworld, break_it, match):
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute(break_it)
    _refused_and_untouched(w, match)


def test_an_owned_run_that_also_holds_a_receipt_of_the_asset_on_another_chart_is_refused(tworld):
    """Deleting the run would set that receipt's run link to NULL (migration 596)."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'y', %s)",
                   (ASSET, OTHER_CHART, rid))
    _refused_and_untouched(w, f"other chart.*{OTHER_CHART}")


def test_an_active_registry_row_with_freshness_on_another_chart_is_refused_but_alone_it_is_restored(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))
    w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key) VALUES (%s, %s, 'z')", (ASSET, OTHER_CHART))
    _refused_and_untouched(w, r"ACTIVE.*596.*EVERY chart")
    w.conn.execute("DELETE FROM public.asset_freshness WHERE chart_id = %s", (OTHER_CHART,))
    _teardown(w)
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


def test_the_dry_run_rehearses_the_deletes_and_so_fails_where_an_execution_would(tworld):
    """Codex round 2 P2: a dry run that returned before the DELETEs could not see a trigger or a constraint that refuses one. A trigger
    that blocks the throughput DELETE makes the DRY RUN fail, and nothing is left changed."""
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("CREATE FUNCTION public.block_throughput_delete() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'blocked'; END $$")
    w.conn.execute("CREATE TRIGGER block_it BEFORE DELETE ON public.asset_throughput FOR EACH ROW EXECUTE FUNCTION public.block_throughput_delete()")
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.Error):
        _teardown(w, dry_run=True)
    assert _snapshot(w) == before


def test_the_dry_run_prints_the_retention_remaining_for_the_owned_run(tworld, capsys):
    w = tworld
    _built_stamped_with_test_run(w)
    _teardown(w, dry_run=True)
    out = capsys.readouterr().out
    assert "day(s) of the 90-day cockpit retention remain" in out and "PAST RETENTION" not in out
    w.conn.execute("UPDATE public.build_runs SET created_at = now() - interval '91 days'")
    _teardown(w, dry_run=True)
    assert "PAST RETENTION" in capsys.readouterr().out


# ── Stream B additions (TEARDOWN-B-ADD): B3 a role holding EXACTLY the documented privileges, B4/B5 catalog references ────────────

ROLE = "td_exact_role"
# a SYNTHETIC password (built from parts, no literal): CI's postgres service authenticates host connections by password, a local trust server does not
ROLE_PASSWORD = "-".join(["exact", "role", "pw"])


def _grant_documented(w, *, registry_update=False, skip=()):
    """Grant EXACTLY td.REQUIRED_PRIVILEGES (and, with registry_update, the conditional ones) to ROLE. `skip` names a privilege to leave out
    as 'table:PRIV' or 'execute:fn' (the missing-grant tests)."""
    rp, c = td.REQUIRED_PRIVILEGES, w.conn
    for t in rp["select_delete"]:
        for priv in ("SELECT", "DELETE"):
            if f"{t}:{priv}" not in skip and _present(w, t):
                c.execute(f"GRANT {priv} ON public.{t} TO {ROLE}")
    for t in rp["select"]:
        if _present(w, t) and f"{t}:SELECT" not in skip:
            c.execute(f"GRANT SELECT ON public.{t} TO {ROLE}")
    for t in rp["update"]:
        if f"{t}:UPDATE" not in skip:
            c.execute(f"GRANT UPDATE ON public.{t} TO {ROLE}")
    for t in rp["select_referencing"]:
        if _present(w, t) and f"{t}:SELECT" not in skip:
            c.execute(f"GRANT SELECT ON public.{t} TO {ROLE}")
    for fn in rp["execute"]:
        if f"execute:{fn}" not in skip:
            c.execute(f"GRANT EXECUTE ON FUNCTION public.{fn} TO {ROLE}")
    if registry_update:
        c.execute(f"GRANT UPDATE (is_active) ON public.asset_registry TO {ROLE}")
        c.execute(f"GRANT SELECT, UPDATE ON public.asset_freshness TO {ROLE}")


@pytest.fixture()
def exact_role(tworld):
    w = tworld
    w.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")
    w.admin.execute(f"CREATE ROLE {ROLE} LOGIN PASSWORD '{ROLE_PASSWORD}'")
    # production revokes PUBLIC EXECUTE on the functions its owner creates (migration 1220 grants the builder the guard functions
    # explicitly for that reason); a freshly built test database leaves PUBLIC EXECUTE in place, which would MASK a missing EXECUTE
    w.conn.execute("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC")
    # the tables production has referencing build_runs (names and columns from the production catalog, Stream B, 2026-10-05): the script
    # counts them, so the role needs SELECT on each; empty here, so none refuses
    for table, column in (("conversations", "archived_by_run_id"), ("event_chart_state_index", "chart_context_superseded_by_run_id"),
                          ("mimamsa_predictions", "chart_context_superseded_by_run_id"),
                          ("mimamsa_calibration_snapshot", "chart_context_superseded_by_run_id"),
                          ("brahma_prospective_ledger", "chart_context_superseded_by_run_id"),
                          ("brahma_mimamsa_prediction_ledger", "chart_context_superseded_by_run_id")):
        w.conn.execute(f"CREATE TABLE public.{table} (id serial PRIMARY KEY, {column} uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    # migration 596's invoker-rights invalidation, VERBATIM function body; the trigger lists only the columns the stub registry has
    w.conn.execute("""CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$$""")
    w.conn.execute("ALTER TABLE public.asset_freshness ADD COLUMN IF NOT EXISTS reasons jsonb NOT NULL DEFAULT '[]'::jsonb")
    w.conn.execute("ALTER TABLE public.asset_freshness ADD COLUMN IF NOT EXISTS observed_at timestamptz NOT NULL DEFAULT now()")
    w.conn.execute("""CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, scope, has_writer, is_active, target_table,
       target_floor ON public.asset_registry FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION public.nirmana_invalidate_registry_receipts()""")
    w.conn.execute("REVOKE EXECUTE ON FUNCTION public.nirmana_invalidate_registry_receipts() FROM PUBLIC")
    try:
        yield w
    finally:
        w.conn.execute(f"DROP OWNED BY {ROLE}")
        w.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")


def _teardown_as(w, dry_run=False):
    from psycopg.conninfo import make_conninfo
    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = make_conninfo(w.dsn, user=ROLE, password=ROLE_PASSWORD)
    try:
        td.teardown(dry_run=dry_run)
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


def test_b3_the_script_runs_as_a_role_holding_exactly_the_documented_privileges(exact_role, capsys):
    """The other tests connect as a superuser and prove LOGIC, not privileges. Here the dry run and then the execution run as a role that
    holds EXACTLY `REQUIRED_PRIVILEGES` (the registry row is inert, so no registry UPDATE is granted)."""
    w = exact_role
    _built_stamped_with_test_run(w)
    _grant_documented(w)
    before = _snapshot(w)
    _teardown_as(w, dry_run=True)                                       # the rehearsal succeeds with those privileges alone
    assert _snapshot(w) == before
    _teardown_as(w)
    assert all(n == 0 for n in _counts(w).values())
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0


def test_b2_b3_an_active_registry_row_needs_the_conditional_privileges_and_without_them_the_dry_run_fails(exact_role):
    w = exact_role
    _built_stamped_with_test_run(w)
    w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))
    _grant_documented(w)                                                # NOT the conditional UPDATE(is_active)
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before
    _grant_documented(w, registry_update=True)
    _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before
    _teardown_as(w)
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


@pytest.mark.parametrize("skip", ["asset_freshness:DELETE", "asset_provenance_receipts:DELETE", "build_runs:DELETE",
                                  "kala_gochara_publication:DELETE", "ka_gochara_contact:DELETE", "execute:ka_gochara_lock_chart(uuid)"],
                         ids=lambda s: s.replace(":", "_").replace("(uuid)", ""))
def test_b3_a_missing_grant_fails_the_dry_run_and_changes_nothing(exact_role, skip):
    """The rehearsal runs the real statements, so a missing privilege shows up in the DRY RUN, not at the steward's execution."""
    w = exact_role
    _built_stamped_with_test_run(w)
    _grant_documented(w, skip=(skip,))
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before


def test_b4_another_table_referencing_an_owned_run_is_found_from_the_catalog_and_named(tworld):
    """build_runs deletion sets ON DELETE SET NULL references to NULL (conversations, the ledgers, ...): found from pg_constraint, not a list."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("CREATE TABLE public.conversations_like (id serial PRIMARY KEY, archived_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute("INSERT INTO public.conversations_like (archived_by_run_id) VALUES (%s)", (rid,))
    _refused_and_untouched(w, r"conversations_like\.archived_by_run_id \(1 row\(s\), ON DELETE SET NULL\)")


def test_b5_a_no_action_reference_to_the_manifest_is_named_not_a_bare_sqlstate(tworld):
    w = tworld
    _slice_run(w)
    w.conn.execute("CREATE TABLE public.contacts_like (id serial PRIMARY KEY, input_generation_vector_id uuid REFERENCES public.kala_gochara_publication(manifest_id))")
    w.conn.execute("INSERT INTO public.contacts_like (input_generation_vector_id) SELECT manifest_id FROM public.kala_gochara_publication WHERE generation = %s", (GEN,))
    _refused_and_untouched(w, r"contacts_like\.input_generation_vector_id \(1 row\(s\), ON DELETE NO ACTION\)")


def test_b6_the_pid_and_lock_checks_pass_on_a_direct_connection(tworld):
    """On a real direct connection the backend does not change across transactions and the session lock is held by it."""
    w = tworld
    _built_stamped_with_test_run(w)
    _teardown(w, dry_run=True)
