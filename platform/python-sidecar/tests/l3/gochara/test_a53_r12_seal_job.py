"""A5.3 — Codex round 12, R12-2: the EXECUTABLE sealing caller (`pipeline/orchestrator/seal_job.py`).

`seal_flow.seal_with_approval` was a library function whose only callers were tests: nothing obtained or authenticated the approval, bound
the run to the reviewed revision, or owned the transaction. The job reads ONE credential (the sealer's), refuses unless it IS the sealer,
validates the approval record, takes the RUN and the sealing REVISION from the environment of the running workflow, requires one of the two NAMED policies
(`all_null_candidate/1`, or — OD-1 — `window_qualification/1` with its table bound; see the end of this file), and owns one explicit transaction (recompute → publish → seal → receipt) so a failure anywhere — the receipt
included — rolls publication back too. Every case runs on the faithful disposable DB as the real `gochara_sealer` LOGIN."""
from __future__ import annotations

import json

import psycopg
import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises the sealing job's identity, approval and receipt handling on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")
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


def test_the_job_pins_the_policy_when_one_is_named(built):
    assert sf.ACCEPTED_POLICIES == ("all_null_candidate/1", "window_qualification/1")
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


# ═══ OD-1 (SR-OD1-NUMERICAL): the sealing job accepts `window_qualification/1` with its frozen table bound, and nothing else unknown ═══════════════
# Claims (one oracle each; the planted reversion is named): 5. the verification job refuses a manifest whose bound table is not the frozen one and verifies the
# same generation with it — through the live-input drift check every verification starts with (`qualification_table.digest` differs; revert: leave the table out of
# `build_input_vector`, and the tampered manifest verifies); 6. the sealer ACCEPTS the policy with the table bound and writes the receipt,
# refuses another table (`qualification_table_mismatch`, nothing written) and still refuses a policy it does not know (`wrong_policy`) (revert: restore the single
# required policy / drop the table check). The all-NULL seal is unchanged: every test above this section is the all-NULL path.

from services.gochara_kernel import result_policy as rp  # noqa: E402
from services.gochara_kernel import verification_job as vj  # noqa: E402


@pytest.fixture()
def built_qual(rworld, request):
    rworld.result_policy = rp.POLICY_QUALIFICATION          # the manifest step binds it (and the frozen table beside it) when `built` boots the world
    return request.getfixturevalue("built")


def _set_table_digest(w, digest):
    _bypass(w, ("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector,"
                " '{qualification_table,digest}', to_jsonb(%s::text))", (digest,)))


def test_the_built_qualification_world_binds_the_frozen_table(built_qual):
    vector = built_qual.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
    assert vector["result_policy"] == rp.POLICY_QUALIFICATION and vector["qualification_table"] == rp.qualification_table_component(rp.POLICY_QUALIFICATION)


def test_the_verification_job_verifies_with_the_frozen_table_and_refuses_another(built_qual):
    w = built_qual
    assert _run(w)["status"] == "VERIFIED"
    _set_table_digest(w, "0" * 64)
    with pytest.raises(vj.VerificationRefused) as exc:
        _run(w)
    assert exc.value.code == "stale_inputs" and "qualification_table" in exc.value.detail, exc.value.detail


@pytest.fixture()
def sealable_qual(built_qual, monkeypatch, tmp_path):
    w = built_qual
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


def test_the_sealer_accepts_the_qualification_policy_with_its_table_bound(sealable_qual, capsys):
    w = sealable_qual
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_SEALED and out["status"] == "SEALED" and out["brief_digest"] == w.digest, out
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


def test_the_sealer_refuses_a_manifest_that_binds_another_table_and_writes_nothing(sealable_qual, capsys):
    w = sealable_qual
    _set_table_digest(w, "0" * 64)
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "qualification_table_mismatch", out
    _nothing_written(w)


@pytest.mark.parametrize("policy", ["numeric/1", "all_null"])
def test_the_sealer_still_refuses_a_policy_it_does_not_know(sealable_qual, capsys, policy):
    w = sealable_qual
    _bypass(w, ("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{result_policy}',"
                " to_jsonb(%s::text))", (policy,)))
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "wrong_policy", out
    _nothing_written(w)


# ═══ OD-1 numerical-window gate (SR-OD1-DESIGN): see the claims list in the block below ══════════════════════════════════════════════════════════════
from services.gochara_kernel import numerical_window_gate as nwg  # noqa: E402
from services.gochara_kernel import window_sweep as _ws  # noqa: E402
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod  # noqa: E402

_ORIG_BOUND_ROWS = writer_mod.RuleRegistryStore.bound_factor_rows


def _declared_kernel_rows(self, path, version):
    """The 1.1.0 catalogue rows (they DECLARE applicability) where a 1.1.0 path exists, else the bound rows: the catalogue the final rules bind today (P3/P4 1.2.0 →
    activity_kernel@1.0.0) declares none, so no window of it could be numbered — that finding is reported; this stand-in is the same one `test_a53_window_sweep_pg` uses."""
    try:
        return [dict(r) for r in _ws.registry_factor_rows(path, "1.1.0")]
    except KeyError:
        return _ORIG_BOUND_ROWS(self, path, version)


@pytest.fixture()
def built_numbers(rworld, request, monkeypatch):
    """`built`, under `window_qualification/1`, with rows that declare applicability: the P3 and P4 windows come out NUMBERED, P1/P2 stay honest nulls."""
    from datetime import datetime, timedelta, timezone
    rworld.result_policy = rp.POLICY_QUALIFICATION
    monkeypatch.setattr(writer_mod.RuleRegistryStore, "bound_factor_rows", _declared_kernel_rows)
    fuzz = timedelta(milliseconds=500)         # a numeric window asks the geometry about the instant 1 µs before its end: finer than a float JD can state

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc)
        return (195.0 if any(a - fuzz <= t < b + fuzz for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)
    return request.getfixturevalue("built")


# Claims (SR-OD1-DESIGN; every one has ONE oracle and the planted reversion that must make it fail):
#   N1. the independent job re-derives every window and persists a PASSED attestation per grain; the verdict's numbered count is the stored peaks   — revert: persist no attestation
#   N2. a window blank where the frozen table yields a value is REFUSED by the re-derivation, and nothing is persisted                                 — revert: delete the "qualified but peak NULL" check
#   N3. a stub policy (the build drafts all-NULL under a manifest that selects window_qualification/1) is REFUSED                                       — revert: the verifier accepts a blank for a qualified objective (same check)
#   N4. a manifest that binds another table than the frozen one makes the verdict FAILED                                                            — revert: drop the table comparison in the verdict
#   N5. a window_qualification/1 generation is not briefed, and not sealed, unless its gate PASSED (two named refusals)                              — revert: drop the brief problem / drop `require_passed`
#   N6. a PASSED numbers generation SEALS, with the verdict and its counts in the sealed brief                                                         — revert: n/a (positive)
#   N7. the all-NULL path is unchanged: no attestation, no verdict key, NOT_APPLICABLE                                                              — revert: attest under every policy
#   N8. windows the policy cannot number are honest nulls: counted by reason code, grouped, never a refusal                                         — revert: the recount ignores blank reasons
#   N9. a report-only run reports the gate NOT_EVALUATED, never green                                                                              — revert: delete that branch
#  N10. the stdlib brief check agrees with the sidecar's verdict and refuses a FAILED / table-mismatched / miscounted one                           — revert: skip the check


@pytest.fixture(autouse=True)
def _job_identity(monkeypatch):
    """SR-OD1 R8: every attestation is bound to the immutable image and the execution that wrote it; the aggregate the brief and the seal read refuses one that names neither."""
    monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", "sha256:" + "1" * 64)
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", "executions/test-exec-1")


def _gate_rows(w):
    return [json.loads(r[0]) if isinstance(r[0], str) else r[0] for r in w.conn.execute(
        "SELECT runner_identity FROM public.ka_gochara_eval_window_verification ORDER BY path_id").fetchall()]


def test_n1_the_job_persists_a_passed_attestation_per_grain_and_the_verdict_counts_the_stored_peaks(built_numbers):
    w = built_numbers
    report = _run(w)
    assert report["status"] == "VERIFIED", report["classes"]
    verdict = report["numerical_window_gate"]
    peaks = w.conn.execute("SELECT count(peak_instant), count(*) FROM public.ka_gochara_eval_window").fetchone()
    assert verdict["status"] == "PASSED" and (verdict["numbered_windows"], verdict["windows"]) == tuple(peaks) and verdict["numbered_windows"] >= 1
    assert verdict["valence_of_numbered"] == {"favourable": verdict["numbered_windows"]} and verdict["grains"] == 4
    assert verdict["judgment_flags"] == []
    rows = _gate_rows(w)
    assert len(rows) == 4 and all(r["numerical_window_gate"]["status"] == "PASSED" and r["numerical_window_gate"]["table"] == nwg.table_binding() for r in rows)
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN)["status"] == "PASSED"


def test_n2_a_window_blank_where_the_table_yields_a_value_is_refused_and_nothing_is_persisted(built_numbers):
    w = built_numbers
    _bypass(w, ("UPDATE public.ka_gochara_eval_window SET peak_instant = NULL, score = NULL, evidence_for = NULL, evidence_against = NULL,"
                " outcome_valence_for_native = 'unqualified' WHERE path_id = 'P3'", ()))
    report = _run(w)
    c = report["classes"][CLS]
    assert (c["status"], c["stage"]) == ("DISAGREE", "window_semantics P3") and "peak/evidence_for is NULL" in c["detail"], c
    assert report["status"] == "DISAGREE" and w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0


def test_n3_a_stub_policy_is_refused(built_numbers):
    """What a stub `window_qualification/1` would store — every number NULL, the unqualified valence, and the ALL-NULL policy's own reason under the qualification policy's
    name — written over the windows the real policy numbered. (Built that way the in-build verify refuses it too; the century defers that step, so the independent job
    is the only detector there.)"""
    w = built_numbers
    _bypass(w, ("UPDATE public.ka_gochara_eval_window SET peak_instant = NULL, score = NULL, evidence_for = NULL, evidence_against = NULL, objective_value = NULL,"
                " outcome_valence_for_native = 'unqualified', qualification = jsonb_set(qualification, '{unqualified_reason}', '\"all_null_candidate_policy\"')"
                " WHERE path_id = 'P3'", ()))
    report = _run(w)
    c = report["classes"][CLS]
    assert (c["status"], c["stage"]) == ("DISAGREE", "window_semantics P3"), c
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    c = nwg.census(w.conn, CHART_ID, GEN, CLS, "P3", "1.0.0")                       # …and the gate's own recount names it independently of the re-derivation
    assert any("stub policy" in p for p in c["problems"]), c["problems"]


def test_n4_a_manifest_that_binds_another_table_makes_the_verdict_fail(built_numbers):
    w = built_numbers
    assert _run(w)["status"] == "VERIFIED"
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN)["status"] == "PASSED"
    _set_table_digest(w, "0" * 64)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("qualification_table" in p for p in verdict["problems"]), verdict["problems"]


@pytest.fixture()
def sealable_numbers(built_numbers, monkeypatch, tmp_path):
    w = built_numbers
    _verified(w)
    w.digest = _brief_as_verifier(w, sealing_commit=COMMIT)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    monkeypatch.setenv(seal_job.ENV_URL, make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD))
    monkeypatch.setenv("GITHUB_RUN_ID", str(RUN))
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", str(ATTEMPT))
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", COMMIT)
    monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", ACTOR)
    w.tmp = tmp_path
    yield w
    w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")


def _drop_attestation(w):
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = runner_identity - 'numerical_window_gate' WHERE path_id = 'P3'", ()))


def test_n5a_a_generation_whose_gate_did_not_pass_is_not_briefed(built_numbers):
    from services.gochara_kernel import seal_brief as sb
    w = built_numbers
    _verified(w)
    _drop_attestation(w)
    with pytest.raises(sb.BriefRefused) as exc:
        _brief_as_verifier(w, sealing_commit=COMMIT)
    assert exc.value.code == "candidate_not_approvable" and any(v.startswith("numerical_window_gate:") for v in exc.value.violations), exc.value.violations


def test_n5b_a_brief_approved_before_the_gate_was_lost_is_not_sealed_and_nothing_is_written(sealable_numbers, capsys):
    w = sealable_numbers
    _drop_attestation(w)                                   # the approved brief existed; the attestation is gone at seal time
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_REFUSED and out["code"] == "numerical_gate_not_passed", out
    _nothing_written(w)


def test_n6_a_passed_numbers_generation_seals(sealable_numbers, capsys):
    w = sealable_numbers
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_SEALED and out["status"] == "SEALED" and out["brief_digest"] == w.digest, out
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)             # the sealed generation's verdict still reads PASSED, with numbers in it
    assert verdict["status"] == "PASSED" and verdict["numbered_windows"] >= 1


def test_n7_the_all_null_path_is_unchanged(built):
    w = built
    report = _run(w)
    assert report["status"] == "VERIFIED" and report["numerical_window_gate"] == {"schema": nwg.SCHEMA, "status": "NOT_APPLICABLE", "policy": rp.POLICY_ALL_NULL}
    assert all("numerical_window_gate" not in r for r in _gate_rows(w))
    payload = _brief_as_verifier(w, sealing_commit=COMMIT)
    assert "numerical_window_gate" not in payload["payload"] and "qualification_table" not in payload["payload"]


def test_n8_windows_the_policy_cannot_number_are_honest_nulls_counted_by_reason_never_a_refusal(built_qual):
    w = built_qual                                       # the catalogue the final rules bind today declares no kernel applicability: the P3 window cannot be numbered
    report = _run(w)
    v = report["numerical_window_gate"]
    assert report["status"] == "VERIFIED" and v["status"] == "PASSED" and v["numbered_windows"] == 0 and v["blank_windows"] == 1, v
    blanks = w.conn.execute("SELECT qualification ->> 'unqualified_reason', count(*) FROM public.ka_gochara_eval_window WHERE peak_instant IS NULL GROUP BY 1").fetchall()
    assert [tuple(b) for b in blanks] == [("applicability_undeclared", 1)]
    assert v["honest_nulls"] == [{"path_id": "P3", "group": nwg.APPLICABILITY, "reason": "applicability_undeclared", "windows": 1}]
    assert sum(h["windows"] for h in v["honest_nulls"]) == v["blank_windows"]
    assert v["judgment_flags"] == ["no_window_numbered_under_numerical_policy"]            # a numbers-on generation with no number in it says so, in the verdict and the brief


def test_n9_a_report_only_run_never_reads_green(built_numbers):
    w = built_numbers
    with login(w, "gochara_verifier") as conn:
        from .test_a53_r10_complete_records import _job_position, _kwargs, LIBRA
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, report_only=True, **_kwargs(w, _job_position(w, [LIBRA])))
    assert report["numerical_window_gate"]["status"] == "NOT_EVALUATED" and report["status"] == "REPORT_ONLY"


def _load_check_script():
    from importlib import util
    from pathlib import Path
    script = Path(__file__).resolve().parents[5] / "platform/scripts/gochara_seal_brief_check.py"
    spec = util.spec_from_file_location("gochara_seal_brief_check_nwg", script)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_n10_the_stdlib_brief_check_agrees_with_the_sidecar_and_refuses_what_the_gate_would(built_numbers):
    import copy
    w = built_numbers
    _verified(w)
    payload = _brief_as_verifier(w, sealing_commit=COMMIT)["payload"]
    check = _load_check_script()
    assert nwg.table_binding() == check.QUALIFICATION_TABLE_BINDING and payload["numerical_window_gate"]["status"] == "PASSED"
    check.check_numerical_gate(json.loads(json.dumps(payload)))                          # the real payload is accepted
    def refuses(mutate):
        p = json.loads(json.dumps(payload))
        mutate(p)
        with pytest.raises(check.Refused):
            check.check_numerical_gate(p)
    refuses(lambda p: p["numerical_window_gate"].update(status="FAILED", problems=["x"]))
    refuses(lambda p: p["numerical_window_gate"].update(table={"schema": "window_qualification_table/1", "digest": "0" * 64}))
    refuses(lambda p: p["numerical_window_gate"].update(blank_windows=p["numerical_window_gate"]["blank_windows"] + 1))
    refuses(lambda p: p["numerical_window_gate"].update(honest_nulls=[{"path_id": "P3", "group": "g", "reason": "", "windows": 0}]))
    refuses(lambda p: p.pop("numerical_window_gate"))
    refuses(lambda p: p["attestations"].update(ka_gochara_eval_window_verification=[l.replace("numerical_window_gate", "gone") for l in p["attestations"]["ka_gochara_eval_window_verification"]]))
    nullp = json.loads(json.dumps(payload))
    nullp["result_policy"] = rp.POLICY_ALL_NULL
    with pytest.raises(check.Refused):
        check.check_numerical_gate(nullp)                                               # an all-NULL brief carries no numerical verdict
