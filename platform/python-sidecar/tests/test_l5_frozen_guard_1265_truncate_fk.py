"""1265 self-test: the TRUNCATE probes of brahma_prospective_ledger against PRODUCTION'S FOREIGN-KEY SHAPE (2026-10-04).

The dry run of 2026-10-04T15:00Z was refused: production has mimamsa_intervention_ledger.prediction_id -> brahma_prospective_ledger (ON DELETE NO ACTION) and
PostgreSQL refuses a plain TRUNCATE of a referenced table (SQLSTATE 0A000) before the guard's statement trigger fires. The test world
(l5_frozen_guard_world.py) now carries that table and FK by default. What is proved here, on a disposable PostgreSQL:

  * the old probe fails in this world with exactly the production message (the defect is reproduced);
  * the new probes: plain TRUNCATE accepted as "already impossible" when PostgreSQL's FK refusal (0A000) is seen, and RECORDED (NOTICE), TRUNCATE ... CASCADE must be
    refused by the GUARD's own message and is recorded too;
  * safety: with the guard removed / disabled / replaced by a decoy the self-test RAISES, the whole transaction ends rolled back and BOTH tables are intact; the
    probe undoes an unrefused statement at once (sub-block), holds no lock afterwards, does not touch the CASCADE target's rows, and fails fast on a lock
    held by another session (lock_timeout scoped to the probe and restored);
  * mutants of the new probe are each killed.
"""
from __future__ import annotations

import re
import time

import pytest

from tests.l5_frozen_guard_world import FORWARD, drop_world, make_world, pg_cluster  # noqa: F401  (pg_cluster is a fixture)

REAL = FORWARD.read_text(encoding="utf8")
LEDGER, TARGET = "brahma_prospective_ledger", "mimamsa_intervention_ledger"
P_PRO = "brahma_prospective_ledger_frozen_row_guard:"
FK_MSG = "cannot truncate a table referenced in a foreign key constraint"
A1, A2 = "00000000-0000-4000-8000-0000000000a1", "00000000-0000-4000-8000-0000000000a2"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
TRUNC_TRIGGER = "brahma_prospective_ledger_frozen_row_guard_truncate"

NEW_BLOCK = re.search(r"    IF has_table_privilege\(current_user, 'public\.brahma_prospective_ledger', 'TRUNCATE'\) THEN\n      -- production:.*?\n    END IF;\n", REAL, re.S).group(0)
OLD_BLOCK = """    IF has_table_privilege(current_user, 'public.brahma_prospective_ledger', 'TRUNCATE') THEN
      r := pg_temp.m1265_refused('TRUNCATE public.brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard:');
      IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_prospective_ledger: ' || r); END IF;
    END IF;
"""
BEFORE_D1 = "-- D1. SELF-TEST helpers"


def helper_text(script: str) -> str:
    m = re.search(r"CREATE FUNCTION pg_temp\.m1265_truncate_probe.*?\n\$h\$;\n", script, re.S)
    assert m, "the probe helper is not in the script"
    return m.group(0)


def seed_intervention_rows(w):
    """Rows in BOTH tables: two interventions pointing at two filed predictions of chart A (production has none today; the proof wants data to lose)."""
    w.exec("INSERT INTO public.mimamsa_intervention_ledger (intervention_id, chart_id, intent, prediction_id) VALUES "
           "('dddddddd-0000-4000-8000-000000000001', %s, 'i1', %s), ('dddddddd-0000-4000-8000-000000000002', %s, 'i2', %s), "
           "('dddddddd-0000-4000-8000-000000000003', %s, 'i3', NULL)", (CHART_A, A1, CHART_A, A2, CHART_A), role="amjis_app")


def fingerprint(w):
    """count + md5 of every row of both tables, read as the administrator (one comparable value)."""
    out = {}
    for t in (LEDGER, TARGET):
        out[t] = w.query("SELECT count(*), md5(COALESCE(string_agg(x::text, '|' ORDER BY x::text), '')) FROM public." + t + " x")[0]
    return out


def inject(script: str, sql: str) -> str:
    assert script.count(BEFORE_D1) == 1
    return script.replace(BEFORE_D1, sql.strip() + "\n\n" + BEFORE_D1)


DISABLE_GUARD = "ALTER TABLE public.brahma_prospective_ledger DISABLE TRIGGER " + TRUNC_TRIGGER + ";"
DECOY = """
CREATE FUNCTION public.m1265_decoy() RETURNS trigger LANGUAGE plpgsql AS $d$ BEGIN RAISE EXCEPTION 'decoy: refused' USING ERRCODE = 'insufficient_privilege'; END $d$;
ALTER TABLE public.brahma_prospective_ledger DISABLE TRIGGER %s;
CREATE TRIGGER m1265_decoy_truncate BEFORE TRUNCATE ON public.brahma_prospective_ledger FOR EACH STATEMENT EXECUTE FUNCTION public.m1265_decoy();
""" % TRUNC_TRIGGER


@pytest.fixture()
def world(pg_cluster):
    w = make_world(pg_cluster)
    yield w
    drop_world(pg_cluster, w)


@pytest.fixture()
def applied(pg_cluster):
    """The real script applied (guards live) in the FK world, rows in both tables."""
    w = make_world(pg_cluster)
    seed_intervention_rows(w)
    w.apply_sql(REAL)
    yield w
    drop_world(pg_cluster, w)


def locks_held_on_the_two_tables(c):
    return c.execute("SELECT c.relname, l.mode FROM pg_locks l JOIN pg_class c ON c.oid = l.relation WHERE l.pid = pg_backend_pid() AND l.locktype = 'relation' "
                     "AND c.relname IN (%s, %s) AND l.mode IN ('AccessExclusiveLock', 'ExclusiveLock', 'ShareRowExclusiveLock', 'ShareLock') ORDER BY 1, 2", (LEDGER, TARGET)).fetchall()


# ================================================================ A. the world carries production's FK shape; the defect is reproduced

def test_the_world_has_production_fk_shape_and_a_plain_truncate_is_refused_by_postgresql_before_any_trigger(world):
    assert world.query("SELECT conrelid::regclass::text, confrelid::regclass::text, confdeltype, convalidated FROM pg_constraint "
                       "WHERE conname = 'mimamsa_intervention_ledger_prediction_id_fkey'") == [(TARGET, LEDGER, "a", True)]
    psy = world.pg["psycopg"]
    with world.connect("amjis_app") as c:
        with pytest.raises(psy.errors.FeatureNotSupported, match=FK_MSG) as ei:
            c.execute("TRUNCATE public." + LEDGER)
        assert ei.value.sqlstate == "0A000"


def test_the_old_probe_fails_in_this_world_with_exactly_the_production_message(world):
    psy = world.pg["psycopg"]
    old = REAL.replace(NEW_BLOCK, OLD_BLOCK)
    assert old != REAL
    with pytest.raises(psy.errors.RaiseException, match=r"1265 self-test FAILED: brahma_prospective_ledger: unexpected error \(cannot truncate a table referenced in a foreign key constraint\): TRUNCATE public\.brahma_prospective_ledger"):
        world.apply_sql(old)


# ================================================================ B. the new probes: accepted, recorded, and the GUARD proves itself on CASCADE

def test_the_new_script_applies_in_the_fk_world_and_records_which_refusal_each_probe_saw(world):
    notices = []
    world.apply_sql(REAL, notices=notices)
    plain = [n for n in notices if n.startswith("1265 self-test: TRUNCATE public.brahma_prospective_ledger refused by POSTGRESQL")]
    casc = [n for n in notices if n.startswith("1265 self-test: TRUNCATE public.brahma_prospective_ledger CASCADE refused by the GUARD")]
    assert len(plain) == 1 and "SQLSTATE 0A000" in plain[0] and "referenced by mimamsa_intervention_ledger.mimamsa_intervention_ledger_prediction_id_fkey" in plain[0], notices
    assert len(casc) == 1 and P_PRO in casc[0], notices
    assert [n for n in notices if "TRUNCATE public.brahma_prospective_ledger" in n and "GUARD" in n and "CASCADE" not in n] == []
    assert world.query("SELECT count(*) FROM pg_trigger WHERE tgname = %s AND tgenabled = 'A'", (TRUNC_TRIGGER,)) == [(1,)]


def test_without_the_fk_the_plain_probe_requires_and_records_the_guard(world):
    world.exec("ALTER TABLE public.mimamsa_intervention_ledger DROP CONSTRAINT mimamsa_intervention_ledger_prediction_id_fkey", role="amjis_app")
    notices = []
    world.apply_sql(REAL, notices=notices)
    assert any(n.startswith("1265 self-test: TRUNCATE public.brahma_prospective_ledger refused by the GUARD") for n in notices), notices
    assert any(n.startswith("1265 self-test: TRUNCATE public.brahma_prospective_ledger CASCADE refused by the GUARD") for n in notices), notices
    assert not any("POSTGRESQL" in n for n in notices)


def test_the_existing_mimamsa_predictions_truncate_skip_is_unchanged(world):
    notices = []
    world.apply_sql(REAL, notices=notices)
    assert any("TRUNCATE branch skipped for mimamsa_predictions" in n for n in notices)


# ================================================================ C. the probe helper, directly

def call(w, sql_args="true, false", role="amjis_app", pre=None, helper=None):
    """Install the helper (pg_temp) in a transaction as amjis_app, call it, return (result, locks held, lock_timeout after, fingerprint inside the txn)."""
    with w.connect(role) as c:
        c.execute("SET LOCAL lock_timeout = '5s'")
        c.execute(helper or helper_text(REAL))
        r = c.execute("SELECT pg_temp.m1265_truncate_probe(%s, %s, " % ("'" + LEDGER + "'", "'" + P_PRO + "'") + sql_args + ")").fetchone()[0]
        inside = {t: c.execute("SELECT count(*) FROM public." + t).fetchone()[0] for t in (LEDGER, TARGET)}
        out = (r, locks_held_on_the_two_tables(c), c.execute("SHOW lock_timeout").fetchone()[0], inside)
        c.rollback()
        return out


def test_helper_plain_is_accepted_as_fk_only_when_asked_and_cascade_needs_the_guard(applied):
    n_ledger, n_target = applied.query("SELECT count(*) FROM public." + LEDGER)[0][0], applied.query("SELECT count(*) FROM public." + TARGET)[0][0]
    assert n_ledger > 0 and n_target == 3
    assert call(applied, "false, true")[0] == "fk"
    r = call(applied, "false, false")[0]
    assert r.startswith("unexpected error (" + FK_MSG)
    assert call(applied, "true, false")[0] == "guard"
    assert call(applied, "true, true")[0] == "guard"


def test_helper_the_cascade_probe_leaves_both_tables_untouched_holds_no_lock_and_restores_lock_timeout(applied):
    before = fingerprint(applied)
    r, locks, lt, inside = call(applied, "true, false")
    assert r == "guard" and locks == [] and lt == "5s"
    assert inside[LEDGER] == before[LEDGER][0] and inside[TARGET] == before[TARGET][0] == 3
    assert fingerprint(applied) == before


def test_helper_scopes_a_short_lock_timeout_to_the_probe_only(applied):
    with applied.connect("amjis_app") as c:
        c.execute(helper_text(REAL))
        assert c.execute("SELECT proconfig FROM pg_proc WHERE proname = 'm1265_truncate_probe' AND pronamespace = pg_my_temp_schema()").fetchone()[0] == ["lock_timeout=2s"]
        c.rollback()


def test_helper_a_lock_held_by_another_session_fails_the_probe_fast_and_does_not_hang(applied):
    holder = applied.connect("postgres")
    try:
        holder.execute("SELECT count(*) FROM public." + TARGET)           # ACCESS SHARE on the CASCADE target, held until the transaction ends
        t0 = time.monotonic()
        r = call(applied, "true, false")
        took = time.monotonic() - t0
        assert r[0].startswith("unexpected error (canceling statement due to lock timeout)"), r
        assert 1.5 < took < 4.5, took                                    # the probe's 2s, not the plan's 5s
        assert r[1] == [] and r[2] == "5s"
    finally:
        holder.rollback()
        holder.close()


def test_helper_an_unrefused_cascade_is_undone_at_once_inside_the_transaction(applied):
    applied.exec("ALTER TABLE public." + LEDGER + " DISABLE TRIGGER " + TRUNC_TRIGGER)          # as the administrator (a superuser here)
    before = fingerprint(applied)
    r, locks, lt, inside = call(applied, "true, false")
    assert r == "not refused (undone at once): TRUNCATE public.brahma_prospective_ledger CASCADE"
    assert inside[LEDGER] == before[LEDGER][0] > 0 and inside[TARGET] == before[TARGET][0] == 3, "the sub-block did not undo the truncate"
    assert locks == [] and lt == "5s"
    assert fingerprint(applied) == before


def test_helper_a_decoy_refusal_with_another_message_is_not_taken_for_the_guard(applied):
    applied.exec("ALTER TABLE public." + LEDGER + " DISABLE TRIGGER " + TRUNC_TRIGGER)
    applied.exec("CREATE FUNCTION public.m1265_decoy() RETURNS trigger LANGUAGE plpgsql AS $d$ BEGIN RAISE EXCEPTION 'decoy: refused' USING ERRCODE = 'insufficient_privilege'; END $d$", role="postgres")
    applied.exec("CREATE TRIGGER m1265_decoy_truncate BEFORE TRUNCATE ON public." + LEDGER + " FOR EACH STATEMENT EXECUTE FUNCTION public.m1265_decoy()", role="postgres")
    r = call(applied, "true, false")[0]
    assert r.startswith("refused by something else (decoy: refused)")


# ================================================================ D. the whole script: guard removed -> raises, whole transaction rolled back, both tables intact

def run_mutated_script(w, script, exc="RaiseException"):
    psy = w.pg["psycopg"]
    pre_state, pre_rows = w.catalog_state(), fingerprint(w)
    with pytest.raises(getattr(psy.errors, exc)) as ei:
        w.apply_sql(script)
    assert w.catalog_state() == pre_state, "the failed script left catalog or row changes behind"
    assert fingerprint(w) == pre_rows and pre_rows[TARGET][0] == 3 and pre_rows[LEDGER][0] > 0
    assert w.query("SELECT count(*) FROM pg_proc WHERE proname LIKE '%frozen%'") == [(0,)]       # not even the functions of the file survived
    assert w.query("SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%frozen_row_guard%'") == [(0,)]
    return str(ei.value)


def test_guard_trigger_disabled_before_the_self_test_makes_the_script_raise_and_the_transaction_roll_back_with_both_tables_intact(world):
    seed_intervention_rows(world)
    msg = run_mutated_script(world, inject(REAL, DISABLE_GUARD))
    assert "1265 self-test FAILED: brahma_prospective_ledger: not refused (undone at once): TRUNCATE public.brahma_prospective_ledger CASCADE" in msg
    assert "plain" not in msg and "GUARD" not in msg


def test_guard_replaced_by_a_decoy_raising_another_message_is_refused_as_something_else(world):
    seed_intervention_rows(world)
    msg = run_mutated_script(world, inject(REAL, DECOY))
    assert "refused by something else (decoy: refused): TRUNCATE public.brahma_prospective_ledger CASCADE" in msg


def test_even_without_the_immediate_undo_the_failed_script_rolls_everything_back(world):
    """Defence in depth: remove the probe's own sub-block undo; the file still raises at the end and the executor-owned transaction rolls back."""
    seed_intervention_rows(world)
    no_undo = inject(REAL, DISABLE_GUARD).replace("    RAISE EXCEPTION 'm1265_truncate_probe_unrefused' USING ERRCODE = 'P0001';", "    RETURN format('not refused (NOT undone): %s', stmt);")
    assert no_undo != inject(REAL, DISABLE_GUARD)
    msg = run_mutated_script(world, no_undo)
    assert "not refused (NOT undone): TRUNCATE public.brahma_prospective_ledger CASCADE" in msg


def test_the_guard_removed_entirely_from_the_file_fails_before_the_self_test_and_still_leaves_both_tables_intact(world):
    seed_intervention_rows(world)
    gone = REAL.replace("        EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.%I()', rec.trg, rec.tbl, rec.fn);", "        NULL;")
    assert gone != REAL
    run_mutated_script(world, gone, exc="UndefinedObject")      # ENABLE ALWAYS TRIGGER <missing truncate trigger> stops the file before the self-test


def test_a_cascade_truncate_attempted_directly_is_refused_by_the_guard_and_leaves_the_target_rows_and_locks_alone(applied):
    before = fingerprint(applied)
    psy = applied.pg["psycopg"]
    holder = applied.connect("postgres")
    try:
        with applied.connect("amjis_app") as c:
            c.execute("SAVEPOINT s")
            with pytest.raises(psy.errors.InsufficientPrivilege) as ei:
                c.execute("TRUNCATE public." + LEDGER + " CASCADE")
            assert str(ei.value).startswith(P_PRO)
            c.execute("ROLLBACK TO SAVEPOINT s")
            assert locks_held_on_the_two_tables(c) == []
            # the transaction is still open: a reader must not be blocked by anything the failed statement took
            holder.execute("SET lock_timeout = '1s'")
            assert holder.execute("SELECT count(*) FROM public." + TARGET).fetchone()[0] == 3
            assert holder.execute("SELECT count(*) FROM public." + LEDGER).fetchone()[0] == before[LEDGER][0]
            holder.rollback()
            c.rollback()
    finally:
        holder.close()
    assert fingerprint(applied) == before


# ================================================================ E. mutants of the new probe are each killed

def scenarios(pg, script):
    """Every behaviour the new probe has, evaluated against `script`; returns the names of the scenarios that did NOT behave as the real script does."""
    bad = []
    psy = pg["psycopg"]

    def fresh():
        w = make_world(pg)
        seed_intervention_rows(w)
        return w

    # 1. the production-shaped world: the script applies, and records both refusals
    w = make_world(pg)
    try:
        notices = []
        try:
            w.apply_sql(script, notices=notices)
            ok = (any("TRUNCATE public.brahma_prospective_ledger refused by POSTGRESQL" in n for n in notices)
                  and any("TRUNCATE public.brahma_prospective_ledger CASCADE refused by the GUARD" in n for n in notices))
            if not ok:
                bad.append("applies but does not record both refusals")
        except psy.Error as e:
            bad.append("production-shaped world: " + type(e).__name__)
    finally:
        drop_world(pg, w)
    # 2. guard disabled: must raise, nothing survives
    for name, sql in (("guard disabled", DISABLE_GUARD), ("decoy", DECOY)):
        w = fresh()
        try:
            try:
                w.apply_sql(inject(script, sql))
                bad.append(name + ": the self-test did not raise")
            except psy.errors.RaiseException as e:
                if "1265 self-test FAILED" not in str(e):         # the post-check also refuses a disabled / extra trigger: only the SELF-TEST counts here
                    bad.append(name + ": raised, but not by the self-test: " + str(e)[:80])
            except psy.Error as e:
                bad.append(name + ": " + type(e).__name__)
            if fingerprint(w)[TARGET][0] != 3 or w.query("SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%frozen_row_guard%'") != [(0,)]:
                bad.append(name + ": state not rolled back")
        finally:
            drop_world(pg, w)
    # 3. the helper's own immediate undo and lock_timeout scope (needs the guards live and then disabled)
    w = fresh()
    try:
        w.apply_sql(REAL)
        w.exec("ALTER TABLE public." + LEDGER + " DISABLE TRIGGER " + TRUNC_TRIGGER)
        h = helper_text(script)
        r, locks, lt, inside = call(w, "true, false", helper=h)
        if inside[TARGET] != 3 or inside[LEDGER] == 0:
            bad.append("the probe did not undo an unrefused CASCADE at once")
        if locks != [] or lt != "5s":
            bad.append("lock or lock_timeout left behind")
        w.exec("ALTER TABLE public." + LEDGER + " ENABLE ALWAYS TRIGGER " + TRUNC_TRIGGER)
        holder = w.connect("postgres")
        try:
            holder.execute("SELECT count(*) FROM public." + TARGET)
            t0 = time.monotonic()
            r2 = call(w, "true, false", helper=h)
            if not (time.monotonic() - t0 < 4.0 and r2[0].startswith("unexpected error (canceling statement due to lock timeout)")):
                bad.append("the probe did not fail fast on a held lock")
        finally:
            holder.rollback()
            holder.close()
    finally:
        drop_world(pg, w)
    return bad


PLAIN_CALL = "pg_temp.m1265_truncate_probe('brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard:', false, true)"
CASC_CALL = "pg_temp.m1265_truncate_probe('brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard:', true, false)"


def _replace(old, new):
    assert REAL.count(old) == 1, old
    return REAL.replace(old, new)


MUTANTS = [
    ("the CASCADE probe is gone", lambda: _replace("      r := " + CASC_CALL + ";\n      IF r <> 'guard' THEN failures := array_append(failures, 'brahma_prospective_ledger: ' || r); END IF;\n", "")),
    ("the CASCADE probe is a plain TRUNCATE (accepts the FK refusal as proof)", lambda: _replace(CASC_CALL, "pg_temp.m1265_truncate_probe('brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard:', false, true)")),
    ("the CASCADE result is not checked", lambda: _replace("      IF r <> 'guard' THEN failures := array_append(failures, 'brahma_prospective_ledger: ' || r); END IF;\n", "")),
    ("the plain probe no longer accepts the FK refusal (the defect again)", lambda: _replace(PLAIN_CALL, PLAIN_CALL.replace("false, true)", "false, false)"))),
    ("the helper takes any refusal for the guard (prefix not compared)", lambda: _replace("      IF msg LIKE prefix || '%' THEN", "      IF true THEN")),
    ("the helper does not undo an unrefused statement at once", lambda: _replace("    RAISE EXCEPTION 'm1265_truncate_probe_unrefused' USING ERRCODE = 'P0001';", "    RETURN format('not refused (undone at once): %s', stmt);")),
    ("the helper has no probe-scoped lock_timeout", lambda: _replace("LANGUAGE plpgsql SET lock_timeout = '2s' AS $h$", "LANGUAGE plpgsql AS $h$")),
    ("the helper reports any other refusal as the guard", lambda: _replace("      RETURN format('refused by something else (%s): %s', left(msg, 100), stmt);", "      RETURN 'guard';")),
]


def test_the_real_script_behaves_in_every_scenario(pg_cluster):
    assert scenarios(pg_cluster, REAL) == []


@pytest.mark.parametrize("name,make", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_of_the_new_probe_is_killed(pg_cluster, name, make):
    assert scenarios(pg_cluster, make()), "mutant survived: " + name
