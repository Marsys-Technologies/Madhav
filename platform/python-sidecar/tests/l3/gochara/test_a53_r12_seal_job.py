"""A5.3 — Codex round 12, R12-2: the EXECUTABLE sealing caller (`pipeline/orchestrator/seal_job.py`).

`seal_flow.seal_with_approval` was a library function whose only callers were tests: nothing obtained or authenticated the approval, bound
the run to the reviewed revision, or owned the transaction. The job reads ONE credential (the sealer's), refuses unless it IS the sealer,
validates the approval record, takes the RUN and the sealing REVISION from the environment of the running workflow, requires the milestone's
`all_null_candidate/1` policy, and owns one explicit transaction (recompute → publish → seal → receipt) so a failure anywhere — the receipt
included — rolls publication back too. Every case runs on the faithful disposable DB as the real `gochara_sealer` LOGIN."""
from __future__ import annotations

import json

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import seal_job
from services.gochara_kernel import seal_flow as sf

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, _bypass, _run, built, login, rworld)  # noqa: F401
from .test_a53_r11_seal_brief import BRIEF_IDS, EXECUTION, _brief_as_verifier, _sealer_stand_ins, _verified  # noqa: F401
from .test_a53_verification_job import PASSWORD
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _persist_test_brief, _seal  # noqa: F401

COMMIT = "0123456789abcdef0123456789abcdef01234567"
RUN, ATTEMPT = 424242, 2
ACTOR = "release-owner"
NOTE = f"ruling:owner-2#2; actor:{ACTOR}"          # the MECHANICAL note the workflow writes (F-R12 / steward: never free text)


def _approval(digest, **over):
    a = {"schema": "seal_approval/2", "brief_digest": digest, "brief_id": BRIEF_IDS.get(digest, 1), "producer_execution_id": EXECUTION,
         "run_id": RUN, "run_attempt": ATTEMPT,
         "approver_login": "owner-login", "approved_by_note": NOTE}
    a.update(over)
    return a


@pytest.fixture()
def sealable(built, monkeypatch, tmp_path):
    w = built
    _verified(w)
    digest = _brief_as_verifier(w, sealing_commit=COMMIT)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    monkeypatch.setenv(seal_job.ENV_URL, make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD))
    monkeypatch.setenv("GITHUB_RUN_ID", str(RUN))
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", str(ATTEMPT))
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", COMMIT)
    monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", ACTOR)
    w.digest, w.tmp = digest, tmp_path
    yield w
    w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")


def _run_job(w, capsys, approval=None, raw=None, extra=()):
    f = w.tmp / "approval.json"
    if raw is not None:
        f.write_text(raw)
    elif approval is not None:
        f.write_text(json.dumps(approval))
    code = seal_job.main(["--chart", CHART_ID, "--approval-file", str(f), *extra])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1])


def _nothing_written(w):
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0


def test_the_job_seals_as_the_real_sealer_and_writes_the_receipt_of_this_run(sealable, capsys):
    w = sealable
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_SEALED and out["status"] == "SEALED" and out["brief_digest"] == w.digest, out
    r = w.conn.execute("SELECT brief_digest, approver_login, approved_by_note, run_id, run_attempt, workflow_commit,"
                       " manifest_id::text, brief_id, producer_execution_id FROM public.ka_gochara_seal_approval").fetchone()
    assert r[:6] == (w.digest, "owner-login", NOTE, RUN, ATTEMPT, COMMIT) and r[6] == out["manifest_id"]
    assert (r[7], r[8]) == (BRIEF_IDS[w.digest], EXECUTION)                     # R13-3: the receipt names the specific brief and execution
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"


def test_no_credential_means_no_run(sealable, monkeypatch, capsys):
    monkeypatch.delenv(seal_job.ENV_URL)
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_IDENTITY and out["code"] == "no_sealer_credential"
    _nothing_written(sealable)


@pytest.mark.parametrize("raw,code_name", [
    (None, "approval_absent"), ("", "approval_absent"), ("not json", "approval_malformed"), ("[]", "approval_malformed"),
    (json.dumps({"schema": "other/1"}), "approval_malformed"),
])
def test_an_absent_or_malformed_approval_is_refused_and_nothing_is_written(sealable, capsys, raw, code_name):
    w = sealable
    f = w.tmp / "approval.json"
    if raw is None:
        code = seal_job.main(["--chart", CHART_ID])                      # no --approval-file at all
        out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    else:
        code, out = _run_job(w, capsys, raw=raw)
    assert code == sf.EXIT_REFUSED and out["code"] == code_name, out
    _nothing_written(w)


@pytest.mark.parametrize("over", [
    {"brief_digest": "abc"}, {"brief_digest": "A" * 64}, {"brief_digest": "a" * 64 + "\n"}, {"run_id": "424242"}, {"run_id": 0}, {"run_attempt": True},
    {"approver_login": " "}, {"approved_by_note": ""}])
def test_a_malformed_field_is_refused(sealable, capsys, over):
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, **over))
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_malformed", out
    _nothing_written(sealable)


@pytest.mark.parametrize("note", [
    "steward under owner ruling #2", "approved", "ruling:owner-2", f"ruling:; actor:{ACTOR}", f"ruling:owner-2; actor:{ACTOR} extra",
    f"ruling:owner 2; actor:{ACTOR}", f"actor:{ACTOR}; ruling:owner-2", f"ruling:owner-2;actor:{ACTOR}", f" ruling:owner-2; actor:{ACTOR}",
    f"ruling:owner-2; actor:{ACTOR}\n"])
def test_a_free_typed_approval_note_is_refused_and_nothing_is_written(sealable, capsys, note):
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, approved_by_note=note))
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_note_not_mechanical", out
    _nothing_written(sealable)


def test_a_note_naming_someone_other_than_the_runs_triggering_actor_is_refused(sealable, capsys):
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, approved_by_note="ruling:owner-2; actor:someone-else"))
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_note_actor_mismatch", out
    _nothing_written(sealable)


@pytest.mark.parametrize("actor", [None, "", "  "])
def test_a_run_that_names_no_triggering_actor_cannot_seal(sealable, monkeypatch, capsys, actor):
    if actor is None:
        monkeypatch.delenv("GITHUB_TRIGGERING_ACTOR")
    else:
        monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", actor)
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "triggering_actor_absent", out
    _nothing_written(sealable)


def test_the_actor_comparison_ignores_case_and_accepts_a_bot_login(sealable, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", "Release-Bot[bot]")
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, approved_by_note="ruling:owner-2; actor:release-bot[bot]"))
    assert code == sf.EXIT_SEALED, out


@pytest.mark.parametrize("over", [{"run_id": RUN + 1}, {"run_attempt": ATTEMPT + 1}])
def test_an_approval_given_for_another_run_or_attempt_is_refused(sealable, capsys, over):
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, **over))
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_not_for_this_run", out
    _nothing_written(sealable)


def test_the_run_identity_must_come_from_the_environment(sealable, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_RUN_ID")
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "run_identity_absent"
    _nothing_written(sealable)


@pytest.mark.parametrize("commit", ["", "not-a-commit", "ZZZ", COMMIT + "\n"])
def test_an_absent_or_malformed_sealing_commit_is_refused(sealable, monkeypatch, capsys, commit):
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", commit)
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "sealing_commit_malformed"
    _nothing_written(sealable)


def test_a_different_sealing_revision_than_the_briefed_one_is_refused_as_a_mismatch(sealable, monkeypatch, capsys):
    """The sealing commit is INSIDE the briefed payload: sealing from another revision is a different digest."""
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", "f" * 40)
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_MISMATCH and out["code"] == "approval_mismatch", out
    _nothing_written(sealable)


def test_a_stale_approval_after_the_candidate_changed_is_refused_before_publication(sealable, capsys):
    w = sealable
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET source_text = 'changed after the brief' WHERE path_id = 'P3'", ()))
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_MISMATCH and "changed candidate invalidates the approval" in out["detail"], out
    _nothing_written(w)


def test_a_wrong_digest_is_refused_as_a_mismatch(sealable, capsys):
    code, out = _run_job(sealable, capsys, _approval("0" * 64))
    assert code == sf.EXIT_MISMATCH, out
    _nothing_written(sealable)


def test_the_job_requires_the_all_null_policy_explicitly(built):
    assert sf.REQUIRED_POLICY == "all_null_candidate/1"
    w = built
    _verified(w)
    d = _brief_as_verifier(w, sealing_commit=COMMIT)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    try:
        with psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD), autocommit=True) as conn:
            with pytest.raises(sf.SealRefused) as exc:
                sf.execute_seal(conn, chart_id=CHART_ID, generation=GEN, approval=_approval(d), run_id=RUN, run_attempt=ATTEMPT,
                                sealing_commit=COMMIT, triggering_actor=ACTOR, required_policy="window_qualification/1")
        assert exc.value.code == "wrong_policy"
    finally:
        w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")
    _nothing_written(w)


def test_only_the_sealer_login_may_run_the_job(sealable, monkeypatch, capsys):
    w = sealable
    # (a) the superuser admin login, (b) the verifier login, (c) an admin session SET ROLE'd to the sealer, (d) a non-autocommit connection
    for who in ("admin", "verifier", "setrole"):
        if who == "admin":
            monkeypatch.setenv(seal_job.ENV_URL, w.dsn)
        elif who == "verifier":
            w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
            monkeypatch.setenv(seal_job.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        else:
            monkeypatch.setenv(seal_job.ENV_URL, w.dsn + " options='-c role=gochara_sealer'")
        try:
            code, out = _run_job(w, capsys, _approval(w.digest))
        finally:
            if who == "verifier":
                w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")
        assert code == sf.EXIT_IDENTITY and out["code"] == "identity_not_sealer", (who, out)
        _nothing_written(w)
    conn = psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD))          # autocommit OFF
    try:
        with pytest.raises(sf.SealRefused, match="connection_not_autocommit"):
            sf.execute_seal(conn, chart_id=CHART_ID, generation=GEN, approval=_approval(w.digest), run_id=RUN,
                            run_attempt=ATTEMPT, sealing_commit=COMMIT, triggering_actor=ACTOR)
    finally:
        conn.close()


def test_a_sealer_holding_a_write_beyond_the_seal_set_is_refused(sealable, capsys):
    w = sealable
    w.conn.execute("GRANT UPDATE (house_from_frame) ON public.ka_gochara_relationship_record TO gochara_sealer")
    try:
        code, out = _run_job(w, capsys, _approval(w.digest))
    finally:
        w.conn.execute("REVOKE UPDATE (house_from_frame) ON public.ka_gochara_relationship_record FROM gochara_sealer")
    assert code == sf.EXIT_IDENTITY and "beyond the seal set" in out["detail"], out
    _nothing_written(w)


def test_a_failure_after_publication_rolls_publication_back_too(sealable, capsys):
    """The receipt INSERT is refused to the sealer AFTER the publication and the authoritative seal ran: the job owns the transaction,
    so the publication, the seal row and the receipt all roll back (exit 5)."""
    w = sealable
    w.conn.execute("REVOKE INSERT ON public.ka_gochara_seal_approval FROM gochara_sealer")
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_ERROR and out["status"] == "ERROR" and "InsufficientPrivilege" in out["detail"], out
    _nothing_written(w)


def test_a_second_run_over_a_sealed_generation_is_refused_and_writes_no_second_receipt(sealable, capsys):
    w = sealable
    assert _run_job(w, capsys, _approval(w.digest))[0] == sf.EXIT_SEALED
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code in (sf.EXIT_MISMATCH, sf.EXIT_REFUSED), out
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


# ── receipt attribution (R12): database-attested columns; first-seal-of-this-transaction only ──────────────────────

def test_the_receipt_columns_sealed_by_and_approved_at_are_database_attested(sealable, capsys):
    w = sealable
    assert _run_job(w, capsys, _approval(w.digest))[0] == sf.EXIT_SEALED
    sealed_by, approved_at, sealed_at = w.conn.execute(
        "SELECT a.sealed_by, a.approved_at, s.sealed_at FROM public.ka_gochara_seal_approval a"
        " JOIN public.ka_gochara_generation_seal s USING (chart_id, generation)").fetchone()
    assert sealed_by == "gochara_sealer" and approved_at == sealed_at          # the SESSION login, the transaction's timestamp


def test_forged_attribution_values_in_the_insert_are_overwritten(built):
    w = built
    _verified(w)
    _sealer_stand_ins(w)
    _persist_test_brief(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        from services.gochara_kernel import ledger as gk_ledger
        gk_ledger.publish(w.conn, CHART_ID, GEN)
        mid = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        w.conn.execute(
            "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login,"
            " approved_by_note, run_id, run_attempt, workflow_commit, sealed_by, approved_at) VALUES (%s::uuid, %s, %s::uuid,"
            f" repeat('a', 64), (SELECT coalesce(max(brief_id), 1) FROM public.ka_gochara_seal_brief), 'executions/test-exec-1', 'x', 'x', 1, 1, 'abc1234', 'forged-sealer', '2001-01-01T00:00:00Z')", (CHART_ID, GEN, mid))
    sealed_by, approved_at, sealed_at = w.conn.execute(
        "SELECT a.sealed_by, a.approved_at, s.sealed_at FROM public.ka_gochara_seal_approval a"
        " JOIN public.ka_gochara_generation_seal s USING (chart_id, generation)").fetchone()
    assert sealed_by != "forged-sealer" and approved_at == sealed_at


def test_a_receipt_cannot_be_attached_to_a_seal_written_before_this_transaction(built):
    """A generation sealed before 1240 (no receipt trigger then) or in an earlier transaction: a later receipt is refused at commit."""
    import psycopg
    w = built
    _verified(w)
    _persist_test_brief(w)                                                    # (a brief exists: only the first-seal rule can refuse)
    w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER ka_gochara_generation_seal_zz_receipt_required")
    _seal(w, receipt=False)                                                   # sealed, no receipt (the pre-1240 shape)
    w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER ka_gochara_generation_seal_zz_receipt_required")
    mid = w.conn.execute("SELECT manifest_id FROM public.ka_gochara_generation_seal").fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_without_first_seal"):
        with w.conn.transaction():
            w.conn.execute(
                "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login,"
                " approved_by_note, run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, %s::uuid, repeat('a', 64),"
                f" (SELECT coalesce(max(brief_id), 1) FROM public.ka_gochara_seal_brief), 'executions/test-exec-1', 'x', 'x', 1, 1, 'abc1234')", (CHART_ID, GEN, mid))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0


def test_a_receipt_naming_another_manifest_is_refused_even_with_the_first_seal(built):
    import psycopg
    w = built
    _verified(w)
    _persist_test_brief(w)
    with pytest.raises(psycopg.errors.CheckViolation):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            from services.gochara_kernel import ledger as gk_ledger
            gk_ledger.publish(w.conn, CHART_ID, GEN)
            w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
            w.conn.execute(
                "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login,"
                " approved_by_note, run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, gen_random_uuid(),"
                f" repeat('a', 64), (SELECT coalesce(max(brief_id), 1) FROM public.ka_gochara_seal_brief), 'executions/test-exec-1', 'x', 'x', 1, 1, 'abc1234')", (CHART_ID, GEN))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
