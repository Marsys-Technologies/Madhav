"""A5.3 — Codex round 10, R10-3: the verification job locks BEFORE it reads, holds the locks through persistence, and
binds each report to the exact data it checked.

The pre-fix job derived first and took the chart/global locks only at persistence (verification_job.py:215 vs :281–282), so
a builder could replace a checked record between the derivation and the lock; persistence then hashed the REPLACEMENT while
keeping the report produced from the original. These are barrier-controlled schedules (events, not sleeps-as-proof): the
verifier is held mid-derivation by the position callback, and a builder-side writer acts while it is held.

  * serialisation: a builder that follows the lock protocol (chart lock first) BLOCKS until the verifier's transaction ends —
    the attestation covers exactly what was checked, and the later replacement makes the seal gate report it stale;
  * refusal: a writer that does NOT take the lock (a trigger-bypassing superuser) changes the checked data mid-run — the
    persisted report would no longer identify it, so the job REFUSES and persists nothing."""
from __future__ import annotations

import threading

import psycopg
import pytest

from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, LIBRA, _job_position, _kwargs, _verification_rows, built, login,  # noqa: F401
                                            rworld)
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401

BARRIER_TIMEOUT = 20


def _gated_position(w, gate):
    """The job's ephemeris callback, paused ONCE the first time the verifier reaches it (after its locks and its first
    reads) until the test releases it."""
    inner = _job_position(w, [LIBRA])

    def at(body, t):
        if not gate["reading"].is_set():
            gate["reading"].set()
            assert gate["release"].wait(BARRIER_TIMEOUT), "the barrier was never released"
        return inner(body, t)
    return at


def _race(w, mutator, *, expect_blocked: bool, where: str = "early", monkeypatch=None):
    """`where`: 'early' pauses the verifier in its derivation (the position callback); 'late' pauses it AFTER every check and
    BEFORE persistence — exactly the schedule of the finding (a checked record replaced between derivation and persist)."""
    gate = {"reading": threading.Event(), "release": threading.Event()}
    if where == "late":
        real_fp = vj.class_fingerprint
        calls = {"n": 0}

        def late(conn, *a, **k):
            calls["n"] += 1
            if calls["n"] == 2 and not gate["reading"].is_set():          # the SECOND read = the pre-persist re-read
                gate["reading"].set()
                assert gate["release"].wait(BARRIER_TIMEOUT), "the barrier was never released"
            return real_fp(conn, *a, **k)
        monkeypatch.setattr(vj, "class_fingerprint", late)
    result: dict = {}
    mutated = threading.Event()

    def verifier():
        try:
            with login(w, "gochara_verifier") as conn:
                result["report"] = vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(
                    w, _gated_position(w, gate) if where == "early" else _job_position(w, [LIBRA])))
        except BaseException as exc:                              # noqa: BLE001 — surfaced to the test thread
            result["error"] = exc

    def builder():
        with psycopg.connect(w.dsn, autocommit=True, connect_timeout=3) as m:
            mutator(m)
        mutated.set()

    tv = threading.Thread(target=verifier, daemon=True)
    tv.start()
    assert gate["reading"].wait(BARRIER_TIMEOUT), "the verifier never reached its derivation"
    tb = threading.Thread(target=builder, daemon=True)
    tb.start()
    blocked = not mutated.wait(1.5)
    assert blocked is expect_blocked, f"builder-side writer blocked={blocked}, expected {expect_blocked}"
    gate["release"].set()
    tv.join(BARRIER_TIMEOUT * 3)
    tb.join(BARRIER_TIMEOUT)
    assert not tv.is_alive() and not tb.is_alive() and "error" not in result, result.get("error")
    assert mutated.is_set()
    return result["report"]


def _protocol_replace(m):
    """A builder that follows the lock protocol: chart lock first, then the replacement of a checked P1 record's house
    descriptor (record id, support and window structure preserved)."""
    with m.transaction():
        m.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        m.execute("UPDATE public.ka_gochara_relationship_record SET house_from_frame = house_from_frame % 12 + 1"
                  " WHERE path_id = 'P1'")


def _unlocked_replace(m):
    with m.transaction():
        m.execute("SET LOCAL session_replication_role = replica")
        m.execute("UPDATE public.ka_gochara_relationship_record SET house_from_frame = house_from_frame % 12 + 1"
                  " WHERE path_id = 'P1'")


def _gate(w):
    return {(r[1], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()}


@pytest.mark.parametrize("where", ["early", "late"])
def test_a_lock_following_builder_is_serialised_behind_the_verifier_and_the_attestation_covers_what_was_checked(
        built, monkeypatch, where):
    w = built
    report = _race(w, _protocol_replace, expect_blocked=True, where=where, monkeypatch=monkeypatch)
    assert report["status"] == "VERIFIED", report["classes"]
    assert report["classes"][CLS]["fingerprint"]                       # the report names the data it checked
    assert _verification_rows(w)["ka_gochara_eval_window_verification"] == 4
    # the replacement came AFTER the attestation: the seal gate sees the checked state is no longer the stored one
    assert ("P1", "window_verification_inputs_changed") in _gate(w)


def test_a_writer_that_ignores_the_lock_makes_the_job_refuse_and_persist_nothing(built, monkeypatch):
    """The finding's own schedule: every check passed on the original; the record is replaced before persistence."""
    w = built
    report = _race(w, _unlocked_replace, expect_blocked=False, where="late", monkeypatch=monkeypatch)
    c = report["classes"][CLS]
    assert c["status"] == "DISAGREE" and c["stage"] == "consistency", c
    assert report["status"] == "DISAGREE" and _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_the_locks_are_taken_before_the_first_attestation_read(built, monkeypatch):
    """Order, not timing: the first statement the class verification issues is the chart lock, the second the global shared
    key — before the inventory header, the pins or any derivation."""
    w = built
    seen: list[str] = []
    real = vj._inventory_header

    def spy(conn, *a, **k):
        seen.append("read")
        return real(conn, *a, **k)
    monkeypatch.setattr(vj, "_inventory_header", spy)
    real_take = vj.take_locks

    def take(conn, chart_id):
        seen.append("lock")
        return real_take(conn, chart_id)
    monkeypatch.setattr(vj, "take_locks", take)
    with login(w, "gochara_verifier") as conn:
        vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])))
    # the run's own preconditions lock first, and every class transaction locks before its first header read
    assert seen[0] == "lock"
    first_header = seen.index("read")
    assert "lock" in seen[:first_header]
