"""W1 — the database grants the serving reader needs, measured (input to the grants migration, W7).

On a deployment-faithful throwaway database (PUBLIC EXECUTE revoked, as production's bootstrap does) a role holding
NOTHING but the grants listed here gets exactly the answer a superuser gets; with none of them it cannot answer; and
revoking any single one breaks it — so the list is sufficient and has no spare entry for the paths exercised (a
complete class with a window, and a class that was never searched).
"""
from __future__ import annotations

import uuid

import pytest

from services.gochara_kernel import scope_response as sr
from services.gochara_kernel import serving_reader as rd

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _world
from .test_a53_window_verification_gate import CLS, _consistent_sky  # noqa: F401
from .test_w1_serving_reader import _read, _sealed, _unguarded

# ── the grants a serving login needs (for the grants migration, W7) ──────────────────────────────────────

#: Seal-bound reads consume persisted results. They need neither EXECUTE on the
#: generation-wide replay/digest functions nor its prerequisite/legacy tables.
SERVING_SELECT_TABLES = (
    "kala_gochara_publication", "kala_gochara_coverage", "ka_gochara_generation_seal", "ka_gochara_seal_approval",
    "ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_relationship_record", "ka_gochara_contact",
    "ka_gochara_physical_object", "ka_gochara_search_input_snapshot", "ka_gochara_search_inventory",
    "ka_gochara_search_interval", "ka_gochara_search_inventory_verification",
    "ka_gochara_eval_window_verification", "ka_gochara_search_path_pin")
SERVING_EXECUTE_FUNCTIONS = ()


@pytest.fixture()
def world(monkeypatch, tmp_path):
    """The same world on a deployment-faithful database: PUBLIC holds no EXECUTE on the migrations' functions (so a
    missing EXECUTE grant shows, which it would not on the default throwaway database)."""
    yield from _world(monkeypatch, tmp_path, faithful=True)


def test_a_role_with_exactly_the_listed_grants_gets_the_same_answer_and_each_grant_is_needed(world):
    import psycopg
    w = _sealed(world)
    role = f"gochara_w1_reader_{uuid.uuid4().hex[:8]}"
    ask = {"event_classes": [CLS, "career_entry"]}
    expected = _read(w, **ask)
    assert [c["completeness"] for c in expected["classes"]] == ["class_not_searched", sr.COMPLETE]

    def as_role():
        with psycopg.connect(w.dsn, autocommit=True, connect_timeout=3) as c:
            c.execute(f"SET ROLE {role}")
            return rd.read_v5(c, CHART_ID, GEN, **ask)

    grants = ([("SELECT", f"public.{t}") for t in SERVING_SELECT_TABLES]
              + [("EXECUTE", f"FUNCTION {f}") for f in SERVING_EXECUTE_FUNCTIONS])
    w.conn.execute(f"CREATE ROLE {role} NOLOGIN")
    try:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):  # with nothing granted the reader cannot answer
            as_role()
        for privilege, target in grants:
            w.conn.execute(f"GRANT {privilege} ON {target} TO {role}")
        assert as_role() == expected
        for privilege, target in grants:                            # and none of them is spare
            w.conn.execute(f"REVOKE {privilege} ON {target} FROM {role}")
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                as_role()
            w.conn.execute(f"GRANT {privilege} ON {target} TO {role}")
        assert as_role() == expected
        # A missing approval must remain readable as unknown with these same
        # SELECT-only ACLs; no hidden fallback may require verifier privileges.
        _unguarded(w, 'ka_gochara_seal_approval',
                   'DELETE FROM public.ka_gochara_seal_approval WHERE chart_id = %s AND generation = %s',
                   (CHART_ID, GEN))
        unknown = as_role()
        assert unknown == _read(w, **ask)
        assert {c['event_class']: c['completeness'] for c in unknown['classes']} == {
            CLS: 'evidence_unavailable', 'career_entry': 'class_not_searched'}
        with psycopg.connect(w.dsn, autocommit=True, connect_timeout=3) as c:      # SELECT only: the role cannot write
            c.execute(f"SET ROLE {role}")
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute("DELETE FROM public.ka_gochara_eval_window")
    finally:
        w.conn.execute(f"DROP OWNED BY {role}")
        w.conn.execute(f"DROP ROLE {role}")
