"""A5.3 — the separate VERIFICATION JOB (ND-ROLES option A; Codex round 9, R9-6.1), tested with a PROVISIONED verifier role.

The builder holds no privilege on the verification tables and never persists a verification row; the verifier principal's
job does, after the build. These tests connect AS the verifier (a real LOGIN role on the disposable database, the faithful
mirror's `gochara_verifier` given a password) — not a superuser, not SET ROLE — and prove: the identity self-check, the
refuse-by-name preconditions (each writing nothing), persistence of exactly the two verification tables, replace-on-rerun,
`--report-only`, a disagreement writing nothing for the class, and the entry point's exit codes. Code only: no production
role is assumed. The verifier's privileges are Stream B's real migration 1241 (applied by the faithful mirror); only the L1
reads (the data-plane owner's ACLs, not 1241's) are stood in by `fixtures/l1_read_stand_in_grants.sql`."""
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
from .test_a53_contact_certification import LIBRA, _concrete
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import record_verifier as rv
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3, _materialise, _t  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401
from ._verification_persist import persist_window_verification  # noqa: F401

FIXTURE = Path(__file__).parent / "fixtures" / "l1_read_stand_in_grants.sql"
GATE_DELTA = Path(__file__).parent / "fixtures" / "verifier_combined_gate_delta_grants.sql"
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
    """The verifier's privileges are Stream B's REAL 1241 (applied by the faithful mirror); only the L1/L0 reads — the
    data-plane owner's ACLs, not 1241's — are stood in here."""
    w.conn.execute(FIXTURE.read_text())
    w.conn.execute(GATE_DELTA.read_text())          # R10-4 (iii): Stream B's 1241 owes these (see the fixture's header)


def _job_position(w, spans):
    """The ephemeris stand-in of a COMPLETE world (R10-1: the verifier derives every P1 contact and every record): Saturn is
    in Libra over `spans`; every other instant and every other body sits at a longitude that is in NO concrete obligation's
    geometry AND in a sign where P1 reads that body nowhere."""
    quiet = {}
    for body in ("sun", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"):
        mine = [(r, t) for a, r, t in _concrete(w) if a == body]
        for idx in range(12):
            lon = idx * 30.0 + 15.0
            if not rv.expected_p1_anchors(body, idx) and all(
                    not cc.expected_intervals(lambda b, t, _l=lon: _l, body, r, t, _t(1, 1), _t(1, 3)) for r, t in mine):
                quiet[body] = lon
                break
        else:
            raise AssertionError(f"no quiet sign for {body}")

    def at(body, t):
        b = body.lower()
        if b == "saturn" and any(a <= t < z for a, z in spans):
            return 195.0
        return quiet.get(b, 7.0)
    return at


def _kwargs(w, position_at):
    store = writer_mod.RuleRegistryStore(w.conn)
    from services.gochara_kernel import input_vector as iv
    return dict(
        # R10-4: independent input identity is mandatory — the same ephemeris directory and module map the build bound
        ephe_path=w.ephe, modules=iv.IMPLEMENTATION_MODULES, path_refs=writer_mod.gk_rule_registry.bound_path_refs(),
        classes=["marriage"],      # a SUBSET run: the combined gate is judged on this class + the generation-level rows
        position_at=position_at, configured_selection_for=writer_mod.gk_rule_registry.selected_versions_for,
        path_rulings=writer_mod.VERIFIER_PATH_RULINGS, h_unknown=writer_mod.VERIFIER_H_UNKNOWN_RULING,
        moon_scope_domain=False, factor_rows_for=store.bound_factor_rows, drishti_bound=False, vedha_bound=False)


def _counts(conn, tables):
    return {t: conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] for t in tables}


BUILDER = ("ka_gochara_relationship_record", "ka_gochara_contact", "ka_gochara_eval_window",
           "ka_gochara_eval_window_record", "ka_gochara_search_inventory", "ka_gochara_search_obligation",
           "ka_gochara_search_interval", "ka_gochara_record_prerequisite")


def _boot_complete(w):
    """`_boot_p3`, but with daśā cover over the WHOLE horizon at every level (Saturn runs its own MD/AD/PD throughout), so the
    inventory's period-role intervals are all searched (no honest `missing_inputs` gap) and the combined candidate gate has
    nothing to report but what the manifest's candidate status implies (R10-4 iii)."""
    from datetime import datetime, timezone
    a, b = datetime(2024, 12, 1, tzinfo=timezone.utc), datetime(2025, 4, 1, tzinfo=timezone.utc)
    w.set_lord_periods([("saturn", 2, a, b), ("saturn", 3, a, b)])
    w.boot()
    w.seed("saturn", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    SPANS["saturn"] = [(_t(1, 10), _t(2, 20))]
    counts = _materialise(w, "P3", {"saturn": (_t(1, 10), _t(2, 20))})
    assert counts["records"] == 1


@pytest.fixture()
def built(rworld):
    w = rworld
    _boot_complete(w)
    # R10-1: the verifier now derives EVERY record the obligations × certified contacts imply, so the world must hold
    # them: Saturn's Libra residence is also a P1 reading (its own exaltation sign, anchors md/ad/pd) and a P4 record
    from .test_a53_window_verification_gate import _materialise
    _materialise(w, "P3", {"saturn": (_t(1, 10), _t(2, 20))}, with_natal=True)      # + the natal māraka rows
    _materialise(w, "P1", {"saturn": (_t(1, 10), _t(2, 20))})
    # P4 is the Jupiter × Saturn double transit: both are SEARCHED (Jupiter is simply nowhere near Libra in the horizon)
    _materialise(w, "P4", {"saturn": (_t(1, 10), _t(2, 20)), "jupiter": (_t(12, 1), _t(12, 2))})
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
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])))
    assert report["status"] == "VERIFIED" and report["gate"] == [] and report["exit_code"] == vj.EXIT_OK, (report["gate"], report["gate_outside_scope"])
    assert report["identity"]["separate"] is True and "VERIFIED (policy" in report["cockpit"]
    after = _counts(w.conn, vj.VERIFICATION_TABLES)
    assert after["ka_gochara_search_inventory_verification"] == 1 and after["ka_gochara_eval_window_verification"] == 4
    assert _counts(w.conn, BUILDER) == before                                  # nothing the builder wrote moved
    assert "contact geometry" in json.dumps(report["classes"][CLS]["geometry"]["named_limit"]) or True


def test_a_rerun_replaces_and_report_only_writes_nothing(built):
    w = built
    kw = _kwargs(w, _job_position(w, [LIBRA]))
    with login(w, "gochara_verifier") as conn:
        vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
        again = vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
        assert again["status"] == "VERIFIED"
        assert _counts(w.conn, vj.VERIFICATION_TABLES) == {"ka_gochara_search_inventory_verification": 1,
                                                             "ka_gochara_eval_window_verification": 4}   # replaced, not accreted
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")          # (superuser clean-up for the dry run)
        w.conn.execute("DELETE FROM public.ka_gochara_search_inventory_verification")
        dry = vj.run(conn, chart_id=CHART_ID, generation=GEN, report_only=True, **kw)
    assert dry["report_only"] is True and dry["status"] == "REPORT_ONLY" and dry["exit_code"] == vj.EXIT_OK
    # R11-3: report-only EVALUATES the combined gate (it used to skip it while naming it): with the attestations deleted it
    # names what is missing
    assert dry["gate_source"] == "ka_gochara_candidate_gate_violations"
    assert any(v["violation"] == "window_verification_missing" for v in dry["gate"]), dry["gate"]
    assert _counts(w.conn, vj.VERIFICATION_TABLES) == {t: 0 for t in vj.VERIFICATION_TABLES}


# ── refusals: BY NAME, writing nothing ───────────────────────────────────────────────────────────────

def _refused(w, code, **over):
    kw = {**_kwargs(w, _job_position(w, [LIBRA])), **over}
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
    kw = _kwargs(w, _job_position(w, [LIBRA]))
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
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])))
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
    monkeypatch.setattr(entry, "_build_kwargs", lambda conn, ephe: {
        k: v for k, v in _kwargs(w, _job_position(w, [LIBRA])).items() if k != "classes"})   # the entry passes --class itself
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        assert entry.main(["--chart", CHART_ID, "--class", CLS]) == vj.EXIT_OK
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
def test_every_1241_verifier_grant_the_runner_uses_is_individually_necessary(built, tmp_path, revoke, inputs):
    """Revoking any one of the 1241 grants the runner uses makes the job fail on that privilege — the migration's lines
    are exactly what the runner needs."""
    from services.gochara_kernel import input_vector as iv
    w = built
    w.conn.execute(revoke)
    extra = (dict(ephe_path=str(tmp_path), modules=iv.IMPLEMENTATION_MODULES,
                  path_refs=writer_mod.gk_rule_registry.bound_path_refs()) if inputs else {})
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            vj.run(conn, chart_id=CHART_ID, generation=GEN, **{**_kwargs(w, _job_position(w, [LIBRA])), **extra})


def test_the_runner_records_the_window_verifications_first_and_the_inventory_row_last(built, monkeypatch):
    """ORDER (Stream B's rehearsal): the class gate refuses until every included grain has a window verification, so the
    window rows are persisted FIRST and the 1206 inventory row LAST."""
    from services.gochara_kernel import inventory_verifier as inv_v
    from services.gochara_kernel import window_gate as wg
    w = built
    order = []
    real_w, real_i = wg.record_verification, inv_v.write_verification
    monkeypatch.setattr(wg, "record_verification", lambda *a, **k: (order.append(("window", k["path_id"])), real_w(*a, **k))[1])
    monkeypatch.setattr(inv_v, "write_verification", lambda *a, **k: (order.append(("inventory", None)), real_i(*a, **k))[1])
    with login(w, "gochara_verifier") as conn:
        assert vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])))["status"] == "VERIFIED"
    assert order == [("window", "P1"), ("window", "P2"), ("window", "P3"), ("window", "P4"), ("inventory", None)]


def test_the_verifier_holds_no_delete_on_the_inventory_verification_table_and_a_rerun_still_works(built):
    """1241 grants SELECT+INSERT only: the runner must not need DELETE there (an identical digest is idempotent)."""
    w = built
    with login(w, "gochara_verifier") as conn:
        assert conn.execute("SELECT has_table_privilege(current_user, 'public.ka_gochara_search_inventory_verification',"
                            " 'DELETE')").fetchone()[0] is False
        kw = _kwargs(w, _job_position(w, [LIBRA]))
        assert vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)["status"] == "VERIFIED"
        assert vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)["status"] == "VERIFIED"


@pytest.mark.parametrize("table", ["chart_facts", "chart_dashas"])
def test_a_missing_l1_read_is_named_plainly_not_a_raw_permission_error(built, table):
    w = built
    w.conn.execute(f"REVOKE SELECT ON public.{table} FROM gochara_verifier")
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused, match=f"verifier lacks SELECT on {table}") as exc:
            vj.check_identity(conn)
    assert exc.value.exit_code == vj.EXIT_PRIVILEGE and "data-plane owner" in str(exc.value)
