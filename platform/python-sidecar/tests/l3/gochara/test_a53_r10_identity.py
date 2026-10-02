"""A5.3 — Codex round 10, R10-5: the identity self-check proves its stated separation.

The old check used `has_table_privilege`, which does not see COLUMN grants — and 1242 deliberately grants the builder columns —
and it reported `session_user` without judging it, so a superuser login operating under a restricted role passed. Now: the
effective role must hold no write privilege, table OR column level, anywhere on the builder write surface; BOTH `session_user`
and `current_user` are judged (superuser, the builder, a member of the builder or of the role that OWNS the Gochara tables);
and they must be the same role (the job never uses SET ROLE). Every negative case uses a REAL restricted login on the faithful
disposable database (the mirror's `gochara_verifier` given a password), never a stub."""
from __future__ import annotations

from contextlib import contextmanager

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from services.gochara_kernel import verification_job as vj

from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_verification_job import PASSWORD, _provision, login
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401


@contextmanager
def _grant(w, statement, revoke):
    w.conn.execute(statement)
    try:
        yield
    finally:
        w.conn.execute(revoke)


def _refused_as_verifier(w, match):
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused, match=match) as exc:
            vj.check_identity(conn)
    assert exc.value.exit_code == vj.EXIT_PRIVILEGE and exc.value.code == "identity_not_separate"
    return exc.value


def test_the_provisioned_verifier_still_passes_the_stronger_check(built):
    with login(built, "gochara_verifier") as conn:
        out = vj.check_identity(conn)
    assert out == {"login": "gochara_verifier", "session": "gochara_verifier", "separate": True}


@pytest.mark.parametrize("grant,revoke,named", [
    ("GRANT INSERT (record_id) ON public.ka_gochara_relationship_record TO gochara_verifier",
     "REVOKE INSERT (record_id) ON public.ka_gochara_relationship_record FROM gochara_verifier",
     r"INSERT\(record_id\) on ka_gochara_relationship_record"),
    ("GRANT UPDATE (admission_state) ON public.ka_gochara_relationship_record TO gochara_verifier",
     "REVOKE UPDATE (admission_state) ON public.ka_gochara_relationship_record FROM gochara_verifier",
     r"UPDATE\(admission_state\) on ka_gochara_relationship_record"),
    ("GRANT UPDATE (interval) ON public.ka_gochara_eval_window TO gochara_verifier",
     "REVOKE UPDATE (interval) ON public.ka_gochara_eval_window FROM gochara_verifier",
     r"UPDATE\(interval\) on ka_gochara_eval_window"),
    ("GRANT TRUNCATE ON public.ka_gochara_contact TO gochara_verifier",
     "REVOKE TRUNCATE ON public.ka_gochara_contact FROM gochara_verifier", "TRUNCATE on ka_gochara_contact"),
    ("GRANT INSERT ON public.ka_gochara_sky_event TO gochara_verifier",
     "REVOKE INSERT ON public.ka_gochara_sky_event FROM gochara_verifier", "INSERT on ka_gochara_sky_event"),
])
def test_a_column_or_table_write_grant_anywhere_on_the_builder_surface_is_refused(built, grant, revoke, named):
    w = built
    with _grant(w, grant, revoke):
        if grant.startswith(("GRANT INSERT (", "GRANT UPDATE (")):
            # the detector's old blind spot: the table-level function sees nothing of a column grant
            table = grant.split(" ON ")[1].split(" TO ")[0]
            assert w.conn.execute("SELECT has_table_privilege('gochara_verifier', %s, 'INSERT')", (table,)).fetchone()[0] is False
        _refused_as_verifier(w, named)
    with login(w, "gochara_verifier") as conn:                              # revoked: the verifier is clean again
        assert vj.check_identity(conn)["separate"] is True


def test_a_superuser_login_operating_under_the_restricted_role_is_refused(built):
    """Judged on session_user, not only current_user: the admin login `SET ROLE gochara_verifier` has the verifier's
    privileges as its CURRENT role — the old check passed it."""
    w = built
    with psycopg.connect(w.dsn, autocommit=True, connect_timeout=3) as admin:
        admin.execute("SET ROLE gochara_verifier")
        who = admin.execute("SELECT current_user, session_user").fetchone()
        assert who[0] == "gochara_verifier" and who[1] != "gochara_verifier"
        with pytest.raises(vj.VerificationRefused, match="session_user .* is a superuser") as exc:
            vj.check_identity(admin)
        assert exc.value.exit_code == vj.EXIT_PRIVILEGE


def test_a_non_superuser_login_that_switches_to_the_verifier_role_is_refused(built):
    w = built
    w.conn.execute(f"CREATE ROLE r10_hopper LOGIN PASSWORD '{PASSWORD}'")
    w.conn.execute("GRANT gochara_verifier TO r10_hopper")
    try:
        with psycopg.connect(make_conninfo(w.dsn, user="r10_hopper", password=PASSWORD), autocommit=True, connect_timeout=3) as c:
            c.execute("SET ROLE gochara_verifier")
            with pytest.raises(vj.VerificationRefused, match="session_user r10_hopper differs from current_user gochara_verifier"):
                vj.check_identity(c)
    finally:
        w.conn.execute("DROP ROLE r10_hopper")


def test_a_login_that_is_a_member_of_the_role_owning_the_gochara_tables_is_refused(built):
    w = built
    owner = w.conn.execute("SELECT pg_get_userbyid(c.relowner) FROM pg_class c WHERE c.oid ="
                           " 'public.ka_gochara_relationship_record'::regclass").fetchone()[0]
    w.conn.execute(f"CREATE ROLE r10_member LOGIN PASSWORD '{PASSWORD}'")
    w.conn.execute(f"GRANT {owner} TO r10_member")
    try:
        with psycopg.connect(make_conninfo(w.dsn, user="r10_member", password=PASSWORD), autocommit=True, connect_timeout=3) as c:
            with pytest.raises(vj.VerificationRefused, match=f"a member of, {owner}, which OWNS the Gochara tables"):
                vj.check_identity(c)
    finally:
        w.conn.execute("DROP ROLE r10_member")


def test_1240s_postcheck_refuses_a_verifier_with_a_column_write_grant(built):
    """The migration's own post-apply check (extracted verbatim and run on the applied schema): the grant postcheck covers the
    COLUMN predicate too, consistently with the job's identity check."""
    import re
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[4] / "migrations" / "1240_gochara_window_verification_gate.sql").read_text()
    m = re.search(r"(  IF to_regrole\('gochara_verifier'\) IS NOT NULL THEN.*?\n  END IF;\n)", sql, re.S)
    assert m, "the R10-5 post-check block is missing from 1240"
    block = "DO $chk$ DECLARE missing text; BEGIN\n" + m.group(1) + "END $chk$;"
    w = built
    w.conn.execute(block)                                                     # clean verifier: passes
    with _grant(w, "GRANT UPDATE (house_from_frame) ON public.ka_gochara_relationship_record TO gochara_verifier",
                "REVOKE UPDATE (house_from_frame) ON public.ka_gochara_relationship_record FROM gochara_verifier"):
        with pytest.raises(psycopg.errors.RaiseException, match=r"UPDATE\(house_from_frame\) on ka_gochara_relationship_record"):
            w.conn.execute(block)
