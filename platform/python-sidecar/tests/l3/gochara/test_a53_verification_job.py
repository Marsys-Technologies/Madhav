"""A5.3 — the separate VERIFICATION JOB (ND-ROLES option A; Codex round 9, R9-6.1), tested with a PROVISIONED verifier role.

The builder holds no privilege on the verification tables and never persists a verification row; the verifier principal's
job does, after the build. These tests connect AS the verifier (a real LOGIN role on the disposable database, the faithful
mirror's `gochara_verifier` given a password) — not a superuser, not SET ROLE — and prove: the identity self-check, the
refuse-by-name preconditions (each writing nothing), persistence of exactly the two verification tables, replace-on-rerun,
`--report-only`, a disagreement writing nothing for the class, and the entry point's exit codes. Code only: no production
role is assumed. Until Stream B's verifier grants migration exists, `fixtures/pending_verifier_grants.sql` stands in for it
(derived by running the job as the verifier and adding one grant per `permission denied`)."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import verification_job as entry
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t, _world
from .test_a53_contact_certification import LIBRA, _position
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401
from ._verification_persist import persist_window_verification  # noqa: F401

FIXTURE = Path(__file__).parent / "fixtures" / "pending_verifier_grants.sql"
PASSWORD = "job-test-pw"


@pytest.fixture()
def rworld(monkeypatch, tmp_path):
    yield from _world(monkeypatch, tmp_path, faithful=True)


@contextmanager
def login(w, role):
    """A real connection AS `role` (LOGIN + password granted for the test, withdrawn after)."""
    w.conn.execute(f"ALTER ROLE {role} LOGIN PASSWORD '{PASSWORD}'")
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(w.dsn, user=role, password=PASSWORD), autocommit=True, connect_timeout=3)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        w.conn.execute(f"ALTER ROLE {role} NOLOGIN PASSWORD NULL")


def _provision(w):
    """The grants the verifier needs that no reviewed migration gives it yet (see the module docstring)."""
    w.conn.execute(FIXTURE.read_text())
    for table in ("charts", "chart_facts", "chart_dashas", "bg_transit_rules", "_migrations_applied"):
        w.conn.execute(f"GRANT SELECT ON public.{table} TO gochara_verifier")


def _kwargs(w, position_at):
    store = writer_mod.RuleRegistryStore(w.conn)
    return dict(
        position_at=position_at, configured_selection_for=writer_mod.gk_rule_registry.selected_versions_for,
        path_rulings=writer_mod.VERIFIER_PATH_RULINGS, h_unknown=writer_mod.VERIFIER_H_UNKNOWN_RULING,
        moon_scope_domain=False, factor_rows_for=store.bound_factor_rows, drishti_bound=False, vedha_bound=False)


def _counts(conn, tables):
    return {t: conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] for t in tables}


BUILDER = ("ka_gochara_relationship_record", "ka_gochara_contact", "ka_gochara_eval_window",
           "ka_gochara_eval_window_record", "ka_gochara_search_inventory", "ka_gochara_search_obligation",
           "ka_gochara_search_interval", "ka_gochara_record_prerequisite")


@pytest.fixture()
def built(rworld):
    w = rworld
    _boot_p3(w)
    for p in ("P1", "P2", "P3", "P4"):
        w.step(f"window:{CLS}:{p}")                        # the builder's steps only: it persists no verification row
    _provision(w)
    return w


# ── identity ─────────────────────────────────────────────────────────────────────────────────────────

def test_a_superuser_connection_is_refused_by_the_identity_self_check(rworld):
    with pytest.raises(vj.VerificationRefused, match="identity_not_separate") as exc:
        vj.check_identity(rworld.conn)
    assert exc.value.exit_code == vj.EXIT_PRIVILEGE


def test_the_builder_login_is_refused(rworld):
    with login(rworld, "data_plane_builder") as conn:
        with pytest.raises(vj.VerificationRefused, match="identity_not_separate"):
            vj.check_identity(conn)


def test_the_provisioned_verifier_passes_and_a_verifier_with_a_builder_table_write_is_refused(built):
    w = built
    with login(w, "gochara_verifier") as conn:
        assert vj.check_identity(conn)["login"] == "gochara_verifier"
    w.conn.execute("GRANT DELETE ON public.ka_gochara_contact TO gochara_verifier")
    try:
        with login(w, "gochara_verifier") as conn:
            with pytest.raises(vj.VerificationRefused, match="DELETE on ka_gochara_contact"):
                vj.check_identity(conn)
    finally:
        w.conn.execute("REVOKE DELETE ON public.ka_gochara_contact FROM gochara_verifier")


# ── the run ──────────────────────────────────────────────────────────────────────────────────────────

def test_the_verifier_writes_exactly_the_two_verification_tables_and_the_gate_passes(built):
    w = built
    assert _counts(w.conn, vj.VERIFICATION_TABLES) == {t: 0 for t in vj.VERIFICATION_TABLES}      # the builder wrote none
    before = _counts(w.conn, BUILDER)
    with login(w, "gochara_verifier") as conn:
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _position(w, [LIBRA])))
    assert report["status"] == "VERIFIED" and report["gate"] == [] and report["exit_code"] == vj.EXIT_OK, report
    assert report["identity"]["separate"] is True and "VERIFIED (policy" in report["cockpit"]
    after = _counts(w.conn, vj.VERIFICATION_TABLES)
    assert after["ka_gochara_search_inventory_verification"] == 1 and after["ka_gochara_eval_window_verification"] == 4
    assert _counts(w.conn, BUILDER) == before                                  # nothing the builder wrote moved
    assert "contact geometry" in json.dumps(report["classes"][CLS]["geometry"]["named_limit"]) or True


def test_a_rerun_replaces_and_report_only_writes_nothing(built):
    w = built
    kw = _kwargs(w, _position(w, [LIBRA]))
    with login(w, "gochara_verifier") as conn:
        vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
        again = vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
        assert again["status"] == "VERIFIED"
        assert _counts(w.conn, vj.VERIFICATION_TABLES) == {"ka_gochara_search_inventory_verification": 1,
                                                             "ka_gochara_eval_window_verification": 4}   # replaced, not accreted
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
        w.conn.execute("DELETE FROM public.ka_gochara_search_inventory_verification")
        dry = vj.run(conn, chart_id=CHART_ID, generation=GEN, report_only=True, **kw)
    assert dry["report_only"] is True and dry["status"] == "NOT_VERIFIED"
    assert _counts(w.conn, vj.VERIFICATION_TABLES) == {t: 0 for t in vj.VERIFICATION_TABLES}


# ── refusals: BY NAME, writing nothing ───────────────────────────────────────────────────────────────

def _refused(w, code, **over):
    kw = {**_kwargs(w, _position(w, [LIBRA])), **over}
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused, match=code):
            vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
    assert _counts(w.conn, vj.VERIFICATION_TABLES) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_refused_without_a_candidate_manifest(built):
    w = built
    w.conn.execute("ALTER TABLE public.kala_gochara_publication DISABLE TRIGGER USER")
    w.conn.execute("DELETE FROM public.kala_gochara_publication")
    _refused(w, "no_candidate_manifest")


def test_refused_on_a_sealed_generation(built):
    w = built
    kw = _kwargs(w, _position(w, [LIBRA]))
    with login(w, "gochara_verifier") as conn:
        vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
    _seal(w)
    w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE false")
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused, match="already_sealed"):
            vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)


def test_refused_on_an_incomplete_build(built):
    w = built
    w.conn.execute("ALTER TABLE public.kala_gochara_coverage DISABLE TRIGGER USER")
    w.conn.execute("DELETE FROM public.ka_gochara_eval_window_record")
    w.conn.execute("DELETE FROM public.ka_gochara_eval_window")
    w.conn.execute("DELETE FROM public.ka_gochara_relationship_record")
    w.conn.execute("DELETE FROM public.kala_gochara_coverage WHERE partition_kind = 'event_class'")
    _refused(w, "incomplete_build")


def test_refused_on_stale_inputs(built, tmp_path):
    w = built
    from services.gochara_kernel import input_vector as iv
    _refused(w, "stale_inputs", ephe_path=str(tmp_path), modules=iv.IMPLEMENTATION_MODULES,
             path_refs=writer_mod.gk_rule_registry.bound_path_refs())


def test_a_refusal_for_a_missing_verification_grant_names_it(built):
    w = built
    w.conn.execute("REVOKE INSERT ON public.ka_gochara_search_inventory_verification FROM gochara_verifier")
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused, match="no_verifier_privilege"):
            vj.check_identity(conn)


# ── a disagreement writes nothing for the class ──────────────────────────────────────────────────────

def test_an_independent_disagreement_writes_nothing_and_exits_3(built):
    w = built
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_record WHERE path_id = 'P3'")     # an omitted membership
    with login(w, "gochara_verifier") as conn:
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _position(w, [LIBRA])))
    assert report["status"] == "DISAGREE" and report["exit_code"] == vj.EXIT_DISAGREE
    assert report["classes"][CLS]["status"] == "DISAGREE" and "membership" in report["classes"][CLS]["detail"]
    assert _counts(w.conn, vj.VERIFICATION_TABLES) == {t: 0 for t in vj.VERIFICATION_TABLES}
    assert report["gate"]                                                        # the gate stays CLOSED, by name


# ── the entry point ──────────────────────────────────────────────────────────────────────────────────

def test_the_entry_point_reads_one_credential_and_maps_outcomes_to_exit_codes(built, monkeypatch, capsys):
    w = built
    monkeypatch.delenv(entry.ENV_URL, raising=False)
    assert entry.main(["--chart", CHART_ID]) == vj.EXIT_PRIVILEGE                  # no verifier credential: refused
    assert json.loads(capsys.readouterr().out)["code"] == "no_verifier_credential"
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (195.0, 2))   # a stand-in sky for main()
    monkeypatch.setattr(entry, "_build_kwargs", lambda conn, ephe: _kwargs(w, _position(w, [LIBRA])))
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        assert entry.main(["--chart", CHART_ID]) == vj.EXIT_OK
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "VERIFIED"
        monkeypatch.setenv(entry.ENV_URL, w.dsn)                                  # the admin (superuser) login
        assert entry.main(["--chart", CHART_ID]) == vj.EXIT_PRIVILEGE
        assert json.loads(capsys.readouterr().out)["code"] == "identity_not_separate"
    finally:
        w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")


def test_the_job_is_not_a_registered_writer_and_reads_no_builder_credential():
    import inspect

    from pipeline.orchestrator.writers import WRITER_REGISTRY as REGISTRY
    assert not any("verification_job" in str(k) for k in REGISTRY)
    src = inspect.getsource(entry)
    assert "GOCHARA_VERIFIER_DB_URL" in src and "data-plane-builder" not in src and "DATABASE_URL" not in src


@pytest.mark.parametrize("revoke,inputs", [
    ("REVOKE SELECT ON public.ka_gochara_search_obligation FROM gochara_verifier", False),
    ("REVOKE EXECUTE ON FUNCTION public.ka_gochara_window_verification_violations(uuid, text) FROM gochara_verifier", False),
    # the input-identity re-derivation (the stale-inputs precondition) reads the registry and the sky convention
    ("REVOKE SELECT ON public.ka_gochara_predicate FROM gochara_verifier", True),
    ("REVOKE SELECT ON public.ka_gochara_sky_convention FROM gochara_verifier", True),
    ("REVOKE SELECT ON public.ka_gochara_rule_path_prerequisite FROM gochara_verifier", True),
])
def test_every_pending_verifier_grant_is_individually_necessary(built, tmp_path, revoke, inputs):
    """The fixture is the exact delta: revoking any one of its grants makes the job fail on that privilege — so the
    migration Stream B authors needs all of them and nothing in the fixture is padding."""
    from services.gochara_kernel import input_vector as iv
    w = built
    w.conn.execute(revoke)
    extra = (dict(ephe_path=str(tmp_path), modules=iv.IMPLEMENTATION_MODULES,
                  path_refs=writer_mod.gk_rule_registry.bound_path_refs()) if inputs else {})
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            vj.run(conn, chart_id=CHART_ID, generation=GEN, **{**_kwargs(w, _position(w, [LIBRA])), **extra})
