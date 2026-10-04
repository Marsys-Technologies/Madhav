"""A5.3 — steward ruling M20261002T175331: bounded waits in the sealing transaction and in `--brief`.

`statement_timeout = 15min` and `lock_timeout = 2min` are set transaction-locally inside the sealing transaction, `lock_timeout = 2min` inside
`--brief`; a timeout surfaces as a NAMED refusal with nothing published / persisted. Tested with a REAL held lock (another session holds the
chart lock) and a real statement timeout, as the real sealer / verifier logins."""
from __future__ import annotations

import json

import psycopg
import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises the job's statement and idle timeouts on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import seal_job
from pipeline.orchestrator import verification_job as entry
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow as sf
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r12_seal_job import _approval, _nothing_written, _run_job, sealable  # noqa: F401
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _verified  # noqa: F401
from .test_a53_verification_job import PASSWORD
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401


def test_the_agreed_bounds_are_the_ruled_values():
    assert (sb.SEAL_STATEMENT_TIMEOUT, sb.SEAL_LOCK_TIMEOUT, sb.BRIEF_LOCK_TIMEOUT) == ("15min", "2min", "2min")


def test_the_timeouts_are_transaction_local_and_in_force_inside_the_sealing_transaction(sealable, monkeypatch):
    w = sealable
    seen = {}
    real = sf.seal_with_approval

    def spy(conn, **kw):
        seen["in_txn"] = tuple(conn.execute(f"SHOW {n}").fetchone()[0] for n in ("statement_timeout", "lock_timeout"))
        return real(conn, **kw)
    monkeypatch.setattr(sf, "seal_with_approval", spy)
    with psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD), autocommit=True) as conn:
        before = tuple(conn.execute(f"SHOW {n}").fetchone()[0] for n in ("statement_timeout", "lock_timeout"))
        sf.execute_seal(conn, chart_id=CHART_ID, generation=GEN, approval=_approval(w.digest), run_id=424242, run_attempt=2,
                        sealing_commit="0123456789abcdef0123456789abcdef01234567", triggering_actor="release-owner")
        after = tuple(conn.execute(f"SHOW {n}").fetchone()[0] for n in ("statement_timeout", "lock_timeout"))
    assert seen["in_txn"] == ("15min", "2min") and before == after == ("0", "0")      # local to the transaction: the session is as it was


def test_a_held_chart_lock_is_a_named_refusal_and_nothing_is_published(sealable, monkeypatch, capsys):
    w = sealable
    monkeypatch.setattr(sb, "SEAL_LOCK_TIMEOUT", "300ms")
    with psycopg.connect(w.dsn, autocommit=True) as holder:
        with holder.transaction():
            holder.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))          # another build/verification holds the lock
            code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "seal_lock_timeout" and "300ms" in out["detail"], out
    _nothing_written(w)
    code, out = _run_job(w, capsys, _approval(w.digest))                                             # the lock is free: the same job seals
    assert code == sf.EXIT_SEALED, out


def test_a_statement_that_outlives_the_bound_is_a_named_refusal_and_publication_is_rolled_back(sealable, monkeypatch, capsys):
    w = sealable
    monkeypatch.setattr(sb, "SEAL_STATEMENT_TIMEOUT", "1ms")        # every real step of the seal takes longer than 1 ms somewhere
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "seal_statement_timeout", out
    _nothing_written(w)


def test_the_briefs_held_lock_is_a_named_refusal_and_nothing_is_persisted(built, monkeypatch, capsys):
    w = built
    _verified(w)
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        monkeypatch.setattr(sb, "BRIEF_LOCK_TIMEOUT", "300ms")
        monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", "sha256:" + "1" * 64)
        monkeypatch.setenv("CLOUD_RUN_EXECUTION", "executions/test-exec-1")
        monkeypatch.delenv("GOCHARA_SEALING_COMMIT", raising=False)
        with psycopg.connect(w.dsn, autocommit=True) as holder:
            with holder.transaction():
                holder.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                code = entry.main(["--chart", CHART_ID, "--brief"])
        out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert code == vj.EXIT_REFUSED and out["code"] == "brief_lock_timeout" and out["status"] == "REFUSED", out
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_brief").fetchone()[0] == 0
        assert entry.main(["--chart", CHART_ID, "--brief"]) == vj.EXIT_OK                          # lock free: it briefs
    finally:
        w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")
