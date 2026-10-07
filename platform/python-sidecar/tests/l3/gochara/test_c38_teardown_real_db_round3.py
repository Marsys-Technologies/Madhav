"""C38 — the small-test TEARDOWN executed for real, part 3 (Codex rounds 3 and 4, Stream B v1.3: the real catalog foreign keys, the row-lock race, the
chain-class tie, the interrupted replacement, the relationship-level exemptions). Split from test_c38_teardown_real_db.py so each CI job stays well
inside its budget; the helpers and fixtures are imported from part 1 (and part 2 for the role), not copied. CI job: gochara-a55-teardown-round3.
"""
from __future__ import annotations

import json
import os

import psycopg
import pytest

from .test_c38_teardown_real_db import (  # noqa: F401
    GEN, MARKER, SHORT, _counts, _prune, _refused_and_untouched, _run, _slice_run, _slice_steps, _snapshot, _step, _teardown, psycopg, pytest, td, threading, time, template, tworld, writer_mod,
)

# ── Codex round 3 (v1.2): items 1 and 2 on a real database ───────────────────────────────────────────────────────────────────────

#: the six foreign keys INTO build_runs that migrations 1120, 1122 and 1123 add (ON DELETE SET NULL), with their real table and column names
RUN_FKS = (("conversations", "archived_by_run_id"),
           ("event_chart_state_index", "chart_context_superseded_by_run_id"),
           ("mimamsa_predictions", "chart_context_superseded_by_run_id"),
           ("mimamsa_calibration_snapshot", "chart_context_superseded_by_run_id"),
           ("brahma_prospective_ledger", "chart_context_superseded_by_run_id"),
           ("brahma_mimamsa_prediction_ledger", "chart_context_superseded_by_run_id"))


@pytest.mark.parametrize("table, column", RUN_FKS, ids=[t for t, _ in RUN_FKS])
def test_item1_each_real_build_runs_foreign_key_is_found_from_the_catalog_and_refused_by_name(tworld, table, column):
    """Codex round 3 P2: the six real ON DELETE SET NULL references. The list comes from pg_constraint at run time, so a future one is covered."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute(f"CREATE TABLE public.{table} (id serial PRIMARY KEY, {column} uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute(f"INSERT INTO public.{table} ({column}) VALUES (%s)", (rid,))
    _refused_and_untouched(w, rf"{table}\.{column} \(1 row\(s\), ON DELETE SET NULL\)")


def test_item1_an_unreferenced_new_foreign_key_does_not_block(tworld):
    """A table with such a key but no row pointing at an owned run is not an obstacle (a hardcoded 'any FK blocks' would be wrong too)."""
    w = tworld
    _slice_run(w)
    w.conn.execute("CREATE TABLE public.some_future_table (id serial PRIMARY KEY, built_by uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute("INSERT INTO public.some_future_table (built_by) VALUES (NULL)")
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


NON_CANONICAL = dict(MARKER, horizon=[SHORT[0].isoformat().replace("+00:00", "Z"), SHORT[1].isoformat().replace("+00:00", "Z")],
                     classes=list(reversed(MARKER["classes"])))


def test_item2_a_valid_writer_stamp_from_a_non_canonical_marker_is_proved_against_the_original_marker_of_the_run(tworld, capsys):
    """The writer hashes the marker AS GIVEN (Z timestamps, reversed class order) and stores the normalised component, so the stamp's
    digest is not the reconstruction's. With the run row alive the proof is the original preimage and the teardown accepts it."""
    w = tworld
    rid = _run(w, marker=NON_CANONICAL)
    _slice_steps(w, rid)
    _teardown(w, dry_run=True)
    assert f"stamp\tproved against the ORIGINAL marker of run {rid}" in capsys.readouterr().out
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_item2_the_same_stamp_with_no_run_row_left_is_refused_and_the_refusal_says_why(tworld):
    w = tworld
    rid = _run(w, marker=NON_CANONICAL, receipt=False)
    _slice_steps(w, rid)
    _prune(w, rid)                                                           # the watchdog's prune: nothing left to read the preimage from
    _refused_and_untouched(w, r"original marker preimage could not prove it \(no owned run row survives\).*reconstruction")


# ── Codex round 4 / Stream B (v1.3): T1, T4, TB1, D3 on a real database ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("parent", ["run", "manifest"])
def test_t1_a_reference_committed_while_the_teardown_waits_for_the_row_lock_is_seen_by_the_checks(tworld, parent):
    """THE RACE: a competing session inserts a row referencing an owned run (or the manifest) and has not yet committed. It holds a KEY SHARE
    lock on the parent row. The teardown's FOR UPDATE row lock waits for it; when the session commits, the teardown's VALIDATION (which runs
    after the lock) sees the reference and refuses by name. Without the row lock the checks would run first and pass, the DELETE would then
    wait out the same lock and, once the session committed, silently set the reference to NULL (or fail on a NO ACTION one): the dry run
    would 'succeed'. So this test fails if either FOR UPDATE is removed (mutation-checked)."""
    w = tworld
    _slice_run(w)
    if parent == "run":
        w.conn.execute("CREATE TABLE public.conversations_like (id serial PRIMARY KEY, archived_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
        sql, args = "INSERT INTO public.conversations_like (archived_by_run_id) SELECT id FROM public.build_runs LIMIT 1", ()
        named = r"conversations_like\.archived_by_run_id \(1 row\(s\)"
    else:
        w.conn.execute("CREATE TABLE public.contacts_like (id serial PRIMARY KEY, input_generation_vector_id uuid REFERENCES public.kala_gochara_publication(manifest_id))")
        sql, args = "INSERT INTO public.contacts_like (input_generation_vector_id) SELECT manifest_id FROM public.kala_gochara_publication WHERE generation = %s", (GEN,)
        named = r"contacts_like\.input_generation_vector_id \(1 row\(s\)"
    other = psycopg.connect(w.dsn, autocommit=False)
    outcome = {}

    def teardown_thread():
        try:
            _teardown(w, dry_run=True)
            outcome["result"] = "succeeded"
        except BaseException as exc:                          # noqa: BLE001
            outcome["result"] = exc

    try:
        other.execute(sql, args)                              # uncommitted: KEY SHARE on the parent row
        before = _snapshot(w)
        t = threading.Thread(target=teardown_thread)
        t.start()
        time.sleep(3)                                         # the teardown is waiting on the lock (lock_timeout is 10 s)
        assert t.is_alive(), f"the teardown did not wait for the row lock: {outcome}"
        other.commit()                                        # the reference becomes visible; the waiting lock is released
        t.join(60)
    finally:
        other.close()
    result = outcome.get("result")
    assert isinstance(result, td.TeardownRefused), result
    assert __import__("re").search(named, str(result)), str(result)
    assert _snapshot(w) == before


def test_t4_a_surviving_run_with_a_wrong_plan_digest_is_refused_even_though_the_stamp_is_canonical(tworld):
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("UPDATE public.build_runs SET plan_manifest_digest = %s WHERE id = %s", ("0" * 64, rid))
    _refused_and_untouched(w, r"an owned run row survives.*does not match its plan_manifest_digest")


def test_tb1_a_chain_row_of_a_class_outside_the_stamp_is_refused_and_nothing_is_deleted(tworld):
    w = tworld
    _slice_run(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_coverage SET partition_key = 'zz_not_a_stamped_class' WHERE generation = %s"
                       " AND partition_kind = 'event_class' AND partition_key = (SELECT min(partition_key) FROM public.kala_gochara_coverage"
                       " WHERE generation = %s AND partition_kind = 'event_class')", (GEN, GEN))
    _refused_and_untouched(w, r"belong to a class outside the stamp.*'coverage': 1")


def _interrupted_replacement(w):
    """The earlier slice's chain and snapshot (run r1), then a later slice (r2, a different horizon) that committed its stamped manifest
    and died before its snapshot substep replaced anything."""
    from datetime import timedelta
    r1 = _slice_run(w, receipt=False)
    later = dict(MARKER, horizon=[SHORT[0].isoformat(), (SHORT[1] + timedelta(days=1)).isoformat()])
    r2 = _run(w, marker=later, part="p2")
    _step(w, r2, writer_mod.MANIFEST_SUBSTEP)
    manifest_vector, snapshot_vector = (w.conn.execute(q, (GEN,)).fetchone()[0] for q in (
        "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE generation = %s",
        "SELECT input_generation_vector FROM public.ka_gochara_search_input_snapshot WHERE generation = %s"))
    assert manifest_vector != snapshot_vector                                  # the interrupted-replacement state, really
    assert manifest_vector["test_slice"]["marker_digest"] != snapshot_vector["test_slice"]["marker_digest"]
    return r1, r2


def test_d3_an_older_proven_test_chain_under_a_newer_proven_test_manifest_is_removed(tworld):
    """Each stamp is proved by an owned run's ORIGINAL marker (the shared proof, applied to the snapshot's own vector)."""
    w = tworld
    _interrupted_replacement(w)
    assert _counts(w)["ka_gochara_contact"] >= 5
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_d3_the_same_state_is_refused_once_the_older_run_is_pruned_and_the_runbook_not_the_other_script_is_named(tworld):
    w = tworld
    r1, _r2 = _interrupted_replacement(w)
    _prune(w, r1)                                                              # the older stamp can no longer be proved
    before = _snapshot(w)
    with pytest.raises(td.TeardownRefused, match="older stamp is not proved by an owned test run") as exc:
        _teardown(w)
    assert "V5_SMALLTEST_TEARDOWN_RUNBOOK" in str(exc.value) and "dispatch" not in str(exc.value).lower()
    assert _snapshot(w) == before


def test_r5_a_second_foreign_key_from_an_exempt_table_is_checked_on_the_real_catalog_not_exempted_by_table_name(tworld):
    """Codex round 5 (3): build_run_assets.run_id (CASCADE) is the understood relationship; ANOTHER key from the same table into build_runs
    is not exempt, so rows that reference an owned run through it are named instead of being silently nulled."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("ALTER TABLE public.build_run_assets ADD COLUMN superseded_by_run uuid REFERENCES public.build_runs(id) ON DELETE SET NULL")
    w.conn.execute("UPDATE public.build_run_assets SET superseded_by_run = %s WHERE run_id = %s", (rid, rid))
    _refused_and_untouched(w, r"build_run_assets\.superseded_by_run \(1 row\(s\), ON DELETE SET NULL\)")
