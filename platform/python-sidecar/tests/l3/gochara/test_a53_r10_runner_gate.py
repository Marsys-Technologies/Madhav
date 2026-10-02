"""A5.3 — Codex round 10, R10-4: mandatory input identity, the runner's recorded identity, the combined candidate gate.

(i)   a run that cannot independently re-derive its inputs (no ephemeris path / no module map) REFUSES and persists nothing;
(ii)  every window-verification row carries the actual RUNNER identity (commit, implementation digest, runtime, logins), the
      implementation digest must be the one the manifest vector PINNED (database gate arm), and the verification-job modules
      are part of the governed implementation identity;
(iii) the job ends in `ka_gochara_candidate_gate_violations` — the SAME combined gate the seal uses — on the actual candidate
      manifest, and its status/exit code reflect that gate (the completeness half reads only a PUBLISHED manifest row, so the
      three arms that do are re-derived against the candidate; nothing else is filtered)."""
from __future__ import annotations

import hashlib
import json

import pytest

from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import verification_job as vj
from services.gochara_kernel import window_gate as wg

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, LIBRA, _job_position, _kwargs, _run, _verification_rows, built, login,  # noqa: F401
                                            rworld)
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401


def _refused(w, **override):
    kw = _kwargs(w, _job_position(w, [LIBRA]))
    kw.update(override)
    with login(w, "gochara_verifier") as conn:
        with pytest.raises(vj.VerificationRefused) as exc:
            vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
    return exc.value


@pytest.mark.parametrize("override,named", [({"ephe_path": None}, "no ephemeris path"),
                                            ({"modules": None}, "no implementation module map"),
                                            ({"ephe_path": ""}, "no ephemeris path")])
def test_a_run_that_cannot_rederive_its_input_identity_is_refused_and_persists_nothing(built, override, named):
    w = built
    exc = _refused(w, **override)
    assert exc.code == "no_input_identity" and named in exc.detail, (exc.code, exc.detail)
    assert exc.exit_code == vj.EXIT_REFUSED and _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_the_entry_point_refuses_without_an_ephemeris_path(built, monkeypatch, capsys):
    from pipeline.orchestrator import verification_job as entry
    from psycopg.conninfo import make_conninfo
    from .test_a53_verification_job import PASSWORD
    w = built
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    monkeypatch.setattr(entry, "_build_kwargs", lambda conn, ephe: {
        k: v for k, v in _kwargs(w, _job_position(w, [LIBRA])).items() if k not in ("classes", "ephe_path")} | {"ephe_path": ephe})
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        assert entry.main(["--chart", CHART_ID, "--class", CLS]) == vj.EXIT_REFUSED      # CLI: no --ephe-path, no SE_EPHE_PATH
        assert json.loads(capsys.readouterr().out)["code"] == "no_input_identity"
    finally:
        w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_every_window_verification_row_carries_the_actual_runner_identity(built, monkeypatch):
    monkeypatch.setenv(wg.ENV_RUNNER_COMMIT, "deadbeefcafe0123")
    w = built
    assert _run(w)["status"] == "VERIFIED"
    vector = w.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
    pinned = hashlib.sha256(wg._canon(vector["implementation"]).encode("utf-8")).hexdigest()
    rows = w.conn.execute("SELECT runner_identity FROM public.ka_gochara_eval_window_verification").fetchall()
    assert len(rows) == 4
    for (rid,) in rows:
        assert rid["commit"] == "deadbeefcafe0123" and rid["implementation_digest"] == pinned
        assert rid["login"] == "gochara_verifier" and rid["python"] and rid["implementation"]
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)"
                          " WHERE violation = 'window_verification_runner_not_pinned'", (CHART_ID, GEN)).fetchone()[0] == 0


def test_a_row_without_a_commit_or_for_other_code_is_refused_by_the_database(built):
    import psycopg
    w = built
    assert _run(w)["status"] == "VERIFIED"
    row = w.conn.execute("SELECT runner_identity FROM public.ka_gochara_eval_window_verification LIMIT 1").fetchone()[0]
    # (a) no commit: the table's CHECK refuses the row outright
    bad = dict(row, commit="")
    with pytest.raises(psycopg.errors.CheckViolation):
        with w.conn.transaction():
            w.conn.execute("SET LOCAL session_replication_role = replica")      # past the insert-only guard: the CHECK stands
            w.conn.execute("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = %s::jsonb"
                           " WHERE path_id = 'P3'", (json.dumps(bad),))
    # (b) a well-formed identity for OTHER code: the seal gate names it
    other = dict(row, implementation_digest="0" * 64)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = %s::jsonb"
                       " WHERE path_id = 'P3'", (json.dumps(other),))
    got = {(r[1], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()}
    assert ("P3", "window_verification_runner_not_pinned") in got


def test_a_runner_that_is_not_the_pinned_code_is_refused_before_it_persists(built, monkeypatch):
    real = wg.runner_identity
    monkeypatch.setattr(wg, "runner_identity", lambda *a, **k: dict(real(*a, **k), implementation_digest="f" * 64))
    w = built
    exc = _refused(w)
    assert exc.code == "runner_not_pinned" and _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_an_unnameable_runner_commit_is_refused(built, monkeypatch):
    monkeypatch.delenv(wg.ENV_RUNNER_COMMIT, raising=False)
    monkeypatch.setattr(wg, "_git_head", lambda: None)
    exc = _refused(built)
    assert exc.code == "no_runner_identity" and "commit" in exc.detail


def test_both_verification_job_modules_and_the_record_derivation_are_in_the_governed_implementation_identity():
    names = {m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}
    assert {"services.gochara_kernel.verification_job", "pipeline.orchestrator.verification_job",
            "services.gochara_kernel.record_derivation"} <= names
    digests = iv.implementation_digests()
    assert "window" in digests and "evaluation" in digests


def test_the_job_ends_in_the_combined_candidate_gate_and_its_status_reflects_it(built, monkeypatch):
    """The job consumes `ka_gochara_candidate_gate_violations` — NOT the window-only function — so a completeness violation
    (which the window gate cannot see) closes it: status NOT_VERIFIED, exit 3, the violation named in the report."""
    w = built
    seen = {"combined": 0, "window_only": 0}
    real = wg.combined_candidate_gate

    def combined(conn, chart, gen):
        seen["combined"] += 1
        return real(conn, chart, gen) + [{"event_class": CLS, "path_id": None, "rule_version": None,
                                          "violation": "obligation_uncovered", "detail": "injected completeness violation"}]
    monkeypatch.setattr(wg, "combined_candidate_gate", combined)
    monkeypatch.setattr(wg, "candidate_gate", lambda *a, **k: seen.__setitem__("window_only", seen["window_only"] + 1) or [])
    report = _run(w)
    assert seen == {"combined": 1, "window_only": 0}
    assert report["status"] == "NOT_VERIFIED" and report["exit_code"] == vj.EXIT_DISAGREE
    assert report["gate_source"] == "ka_gochara_candidate_gate_violations"
    assert [v["violation"] for v in report["gate"]] == ["obligation_uncovered"]
    assert "gate CLOSED" in report["cockpit"]


def test_the_published_only_arms_are_rederived_against_the_candidate_manifest_and_nothing_else_is_hidden(built):
    w = built
    assert _run(w)["status"] == "VERIFIED"
    raw = {v["violation"] for v in wg.combined_candidate_gate(w.conn, CHART_ID, GEN)}
    assert {"input_vector_mismatch", "convention_bridge_missing", "horizon_manifest_mismatch"} <= raw   # the artefacts of 'candidate'
    assert vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN) == []                          # re-derived: all agree
    # a REAL mismatch against the candidate manifest is still reported
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.ka_gochara_search_input_snapshot SET input_generation_vector ="
                       " input_generation_vector || '{\"x\": 1}'::jsonb")
    got = {v["violation"] for v in vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN)}
    assert "input_vector_mismatch" in got
