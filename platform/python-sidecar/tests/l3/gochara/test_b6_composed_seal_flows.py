"""Composed builder → verifier → sealer flows on the REAL production-ordered stack with ALL guards enabled (Codex R9-6 iv, R9-4).

Unlike the 1240 role suite (1206's seal trigger DISABLED, the build made as a superuser) and the 39-assert rehearsal (object presence
and privileges only), these flows run each act AS ITS PRINCIPAL — the restricted builder builds, the verifier verifies, the sealer
seals — on a database where every object is owned by the migration principal and PUBLIC EXECUTE is revoked (composed_world.py).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv

from . import composed_world as cw
from . import test_a53_p1_support as p1s
from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t
from .conftest import EPHE_PATH as EPHE  # noqa: E402
from .test_a53_window_verification_gate import CLS, SPANS, _materialise  # noqa: F401
from .test_a53_window_verification_roles import _input_digest, _report, _seal  # noqa: F401

UTC = timezone.utc
REAL_CALC = writer_mod.calc_sidereal_lon          # captured before any fixture replaces it: these flows run on the REAL ephemeris


@pytest.fixture()
def cworld(monkeypatch, tmp_path):
    monkeypatch.setattr(p1s, "create_am5_database", lambda tag="p1s", faithful=True: cw.composed_create("comp"))
    yield from p1s._world(monkeypatch, tmp_path, faithful=True)


@pytest.fixture()
def store_without_verification_delete(monkeypatch):
    """STAND-IN for Stream A's pending R9-6.1 change: the builder holds no DELETE on the verification table (PC-4), so the store must not
    DELETE it (the 1206 FK now cascades from the header). Used by every flow except the one that proves the shipped store still does."""
    from services.gochara_kernel import inventory_store
    monkeypatch.setattr(inventory_store, "_CLASS_TABLES_DELETE_ORDER",
                        tuple(t for t in inventory_store._CLASS_TABLES_DELETE_ORDER if "verification" not in t))


@pytest.fixture(autouse=True)
def geometry_probe_margin_stand_in(request, monkeypatch):
    """STAND-IN for Stream A's pending fix of a finding made by this rehearsal (R9-9): `verify_member_geometry` probes 1 SECOND inside and
    outside each stored contact edge, but the contact solver's declared accuracy is 1 ARCSECOND (arcs.DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC)
    — about 24 s of Sun time, ~12 min of Saturn time — so on the REAL sky the writer's own window phase rejects its own correct contacts.
    The stand-in widens the default margin to one hour (the verifier still caps it at a quarter of the span). Tests marked
    `shipped_geometry` run WITHOUT it."""
    if request.node.get_closest_marker("shipped_geometry"):
        return
    orig = wv.verify_member_geometry

    def widened(conn, **kw):
        kw.setdefault("probe_seconds", 3600.0)
        return orig(conn, **kw)
    monkeypatch.setattr(wv, "verify_member_geometry", widened)


@pytest.fixture(autouse=True)
def _real_sky(cworld, monkeypatch):
    """The real Swiss ephemeris (the pinned files), not a stand-in: the builder's contact solves, the inventory verifier's sampling and the
    window verifier's geometry probes all read the SAME sky, so the flows exercise the real derivations end to end."""
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", REAL_CALC)


_LAST_SQL = [""]


@pytest.fixture(autouse=True)
def _capture_sql(monkeypatch):
    """Remember the last statement so a privilege denial can be attributed to its verb (SELECT/INSERT/UPDATE/DELETE)."""
    import psycopg
    orig = psycopg.Cursor.execute

    def wrapped(self, query, *a, **k):
        if isinstance(query, str):
            _LAST_SQL[0] = query
        return orig(self, query, *a, **k)
    monkeypatch.setattr(psycopg.Cursor, "execute", wrapped)


@contextmanager
def as_role(conn, role):
    import psycopg
    conn.execute(f"SET ROLE {role}")
    try:
        yield
    except psycopg.errors.InsufficientPrivilege as exc:
        verb = (_LAST_SQL[0].lstrip().split() or ["?"])[0].upper()
        raise RuntimeError(f"ROLE={role}: VERB={verb}: {exc}") from exc     # the derivation loop reads the principal and verb from here
    finally:
        conn.execute("RESET ROLE")


import json  # noqa: E402
import os  # noqa: E402

#: {role: {"tables": [[privilege, table], ...], "funcs": [name, ...]}} — the privileges DERIVED by running each act as its principal
#: (the derivation loop in the rehearsal record); empty = what the migrations grant today
EXTRA = json.loads(os.environ.get("B6_EXTRA", "{}"))


BASELINE = {
    cw.SEALER: {"tables": [["SELECT", "ka_gochara_generation_seal"], ["INSERT", "ka_gochara_generation_seal"],
                           ["SELECT", "kala_gochara_publication"], ["UPDATE", "kala_gochara_publication"]]
                + [["SELECT", t] for t in ("kala_gochara_coverage", "ka_gochara_rule_path_seal", "ka_gochara_convention_bridge",
                                            "ka_gochara_av_polarity_declaration", "ka_gochara_relationship_record", "ka_gochara_eval_window",
                                            "ka_gochara_eval_window_record", "ka_gochara_search_input_snapshot", "ka_gochara_search_inventory",
                                            "ka_gochara_search_path_pin", "ka_gochara_search_obligation", "ka_gochara_search_interval",
                                            "ka_gochara_search_inventory_verification")],
                "funcs": ["ka_gochara_lock_chart", "ka_gochara_seal_generation", "ka_gochara_generation_governed", "ka_gochara_coverage_drift",
                          "ka_gochara_horizon_finite_ok", "ka_gochara_coverage_facts", "ka_gochara_facts_horizon", "ka_gochara_membership_violations",
                          "ka_gochara_membership_violation", "ka_gochara_lock_global_shared", "ka_gochara_search_completeness_violations",
                          "ka_gochara_search_l1_facts_digest", "ka_gochara_sha256_hex", "ka_gochara_canonical_json", "ka_gochara_search_dasha_digest",
                          "ka_gochara_search_av_entry", "ka_gochara_search_inventory_digest", "ka_gochara_search_ledger_digest",
                          "ka_gochara_search_inventory_preimage", "ka_gochara_utc_ts", "ka_gochara_search_replay_violations",
                          "ka_gochara_search_inventories_digest", "ka_gochara_search_moon_scope_violations",
                          "ka_gochara_search_moon_resolved_domain"]},
    cw.VERIFIER: {"tables": [["SELECT", "ka_gochara_search_inventory_verification"], ["INSERT", "ka_gochara_search_inventory_verification"],
                             ["DELETE", "ka_gochara_search_inventory_verification"]],
                  "funcs": ["ka_gochara_lock_chart", "ka_gochara_generation_is_sealed"]},
}


def apply_extra_grants(conn):
    for role, spec in BASELINE.items():
        for priv, table in spec["tables"]:
            conn.execute(f"GRANT {priv} ON public.{table} TO {role}")
        for fn in spec["funcs"]:
            for (sig,) in conn.execute("SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
                                       " WHERE n.nspname = 'public' AND p.proname = %s", (fn,)).fetchall():
                conn.execute(f"GRANT EXECUTE ON FUNCTION {sig} TO {role}")
    _apply_derived(conn)


def _apply_derived(conn):
    for role, spec in EXTRA.items():
        for priv, table in spec.get("tables", []):
            conn.execute(f"GRANT {priv} ON public.{table} TO {role}")
        for fn in spec.get("funcs", []):
            for (sig,) in conn.execute("SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
                                       " WHERE n.nspname = 'public' AND p.proname = %s", (fn,)).fetchall():
                conn.execute(f"GRANT EXECUTE ON FUNCTION {sig} TO {role}")


def build_as_builder(w):
    """The build, made by the RESTRICTED builder with the writer's OWN substeps for one class (marriage): convention, manifest, snapshot,
    the eight phase-1 body substrates, the class inventory + coverage, every record grain and every window grain. The L1 stub edit
    is the fixture's (superuser); everything after is the builder's."""
    apply_extra_grants(w.conn)
    with as_role(w.conn, cw.BUILDER):
        w.boot()
        for body in writer_mod.SUBSTRATE_BODIES:
            w.step(f"{writer_mod.BODY_SUBSTEP_PREFIX}{body}")
        for p in ("P1", "P2", "P3", "P4"):
            w.step(f"record:{CLS}:{p}")
        out = {p: w.step(f"window:{CLS}:{p}") for p in ("P1", "P2", "P3", "P4")}
    return out


@pytest.mark.shipped_geometry
@pytest.mark.xfail(strict=True, reason="R9-9: the shipped geometry self-check (1 s probes) is tighter than the solver's 1-arcsecond accuracy, "
                                       "so a real-sky build rejects its own contacts; remove when Stream A scales the probe margin to the "
                                       "solver tolerance and the body's speed", raises=RuntimeError)
def test_the_shipped_geometry_self_check_accepts_a_real_sky_build(cworld, store_without_verification_delete):
    build_as_builder(cworld)


@pytest.mark.xfail(strict=True, reason="R9-6.1: the shipped inventory store still DELETEs the verification table as the builder; "
                                       "remove this xfail when Stream A drops it from _CLASS_TABLES_DELETE_ORDER")
def test_the_shipped_inventory_store_rebuilds_as_the_restricted_builder(cworld):
    build_as_builder(cworld)


def test_the_restricted_builder_can_build_the_whole_candidate(cworld, store_without_verification_delete):
    """R9-4: the builder's REAL window INSERT after 1240 — with PUBLIC EXECUTE revoked, the new CHECK helper needs a builder EXECUTE
    grant. This test FAILS on 1240 as shipped without it."""
    out = build_as_builder(cworld)
    assert all(r.rows_inserted >= 0 for r in out.values())


def test_a_rebuild_by_the_restricted_builder_is_idempotent(cworld, store_without_verification_delete):
    """The writer's replace-prelude (delete-then-insert per grain/class) must work with the builder's REAL grants: the orphan-contact
    delete, the record-chain delete and the window replace — none of which the first build exercises."""
    w = cworld
    build_as_builder(w)
    with as_role(w.conn, cw.BUILDER):
        for key in ("inventory:marriage", "coverage:marriage"):
            w.step(key)
        w.seed("saturn", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
        _materialise(w, "P3", {"saturn": (_t(1, 10), _t(2, 20))})
        for p in ("P1", "P2", "P3", "P4"):
            w.step(f"window:{CLS}:{p}")


#: migration 1242's four grants: (revoke statement, grant statement, the table the denial must name)
_M1242 = [("DELETE ON public.ka_gochara_relationship_record", "ka_gochara_relationship_record"),
          ("DELETE ON public.ka_gochara_contact", "ka_gochara_contact"),
          ("UPDATE (admission_state) ON public.ka_gochara_relationship_record", "ka_gochara_relationship_record"),
          ("UPDATE (result) ON public.ka_gochara_record_prerequisite", "ka_gochara_record_prerequisite")]


@pytest.mark.parametrize("grant,table", _M1242, ids=["del_record", "del_contact", "upd_admission_state", "upd_prereq_result"])
def test_each_1242_grant_is_individually_necessary_for_the_rebuild_of_a_record_grain(cworld, store_without_verification_delete, grant, table):
    """1242's four grants, on the REAL migration stack (1242 applied as the real file): the builder rebuilds a record grain (the AM-3
    replace-prelude + the F5 finalisation) — revoking any ONE of them makes that rebuild fail, naming the table."""
    w = cworld
    build_as_builder(w)
    w.conn.execute(f"REVOKE {grant} FROM {cw.BUILDER}")
    try:
        with pytest.raises(RuntimeError, match=f"ROLE={cw.BUILDER}.*permission denied.*{table}"):
            with as_role(w.conn, cw.BUILDER):
                w.step(f"record:{CLS}:P3")
    finally:
        w.conn.execute(f"GRANT {grant} TO {cw.BUILDER}")


def _real_position_at(body, t):
    jd = t.timestamp() / 86400.0 + 2440587.5
    return REAL_CALC(body.title(), jd, EPHE)[0]


def verify_as_verifier(w):
    """The separate verification RUNNER (R9-6): the verifier principal runs the independent derivations on its OWN grants and persists
    the inventory verification (the writer's verify step) and one window verification per included grain."""
    from pipeline.orchestrator.writers.ka_gochara_v5 import RuleRegistryStore
    with as_role(w.conn, cw.VERIFIER):
        note = w.step(f"verify:{CLS}").notes
        for path in ("P1", "P2", "P3", "P4"):
            grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0")
            rows = RuleRegistryStore(w.conn).bound_factor_rows(path, "1.0.0")
            report = wv.verify_window_semantics(w.conn, factor_rows=rows, **grain)
            wv.verify_member_support(w.conn, **grain)
            wv.verify_member_geometry(
                w.conn, position_at=_real_position_at, **grain)
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                wg.record_verification(w.conn, report=report, input_digest=_input_digest(w), **grain)
    return note


def seal_as_sealer(w):
    with as_role(w.conn, cw.SEALER):
        return _seal(w)


def test_first_seal_builder_then_verifier_then_sealer_with_every_guard_enabled(cworld, store_without_verification_delete):
    w = cworld
    build_as_builder(w)
    # before any verification the candidate gate is CLOSED and the seal is refused (the honest "built, not verified" state)
    import psycopg
    with pytest.raises(psycopg.errors.Error):
        seal_as_sealer(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    note = verify_as_verifier(w)
    assert "verification row written" in note
    assert seal_as_sealer(w) is not None
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
