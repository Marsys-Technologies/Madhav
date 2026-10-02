"""A5.3 — Codex round 13, R13-3 (Stream A's half): the approval is bound to the SPECIFIC brief, produced by THIS commit in THAT execution.

The persisted brief carries its producer (commit, immutable image digest, Cloud Run execution id) from the job's own environment; the receipt
names the brief id and execution the approval was given for; the receipt's COMMIT-time trigger and the sealer's early check require the brief to be
the current persisted one AND `producer_commit == the sealing commit` AND the ids to match. An older same-state brief of another execution can
never pass as this run's approval basis. Fresh attempt vs reuse (explicit): the seal accepts ONLY the brief id the approval names; that is the
brief the same workflow run's brief job reported (fresh) — or, for a seal-only rerun, the earlier run's brief iff it is STILL the current persisted
one (reuse), with a fresh approval that names it. Anything else is refused by name."""
from __future__ import annotations

import json

import psycopg
import pytest

from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow as sf

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import BRIEF_IDS, EXECUTION, IMAGE, _brief_as_verifier, _verified  # noqa: F401
from .test_a53_r12_persisted_brief import _publish_seal_receipt
from .test_a53_r12_seal_job import COMMIT, _approval, _nothing_written, _run_job, sealable  # noqa: F401
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401

GOOD = {"GOCHARA_RUNNER_COMMIT": COMMIT, "GOCHARA_RUNNER_IMAGE_DIGEST": IMAGE, "CLOUD_RUN_EXECUTION": "projects/p/locations/l/jobs/j/executions/e1"}


# ── the producer identity is read from the job's environment and refused when absent or malformed ─────────────────

def test_the_producer_identity_comes_from_the_environment():
    assert sb.producer_identity(GOOD) == {"commit": COMMIT, "image_digest": IMAGE, "execution_id": GOOD["CLOUD_RUN_EXECUTION"]}


@pytest.mark.parametrize("drop,over,named", [
    ("GOCHARA_RUNNER_IMAGE_DIGEST", None, "GOCHARA_RUNNER_IMAGE_DIGEST"),
    ("CLOUD_RUN_EXECUTION", None, "CLOUD_RUN_EXECUTION"),
    (None, {"GOCHARA_RUNNER_IMAGE_DIGEST": "latest"}, "sha256:<64 hex>"),
    (None, {"GOCHARA_RUNNER_IMAGE_DIGEST": "sha256:" + "A" * 64}, "sha256:<64 hex>"),
    (None, {"GOCHARA_RUNNER_IMAGE_DIGEST": "sha256:" + "1" * 64 + "\n"}, "sha256:<64 hex>"),
    (None, {"CLOUD_RUN_EXECUTION": "  "}, "CLOUD_RUN_EXECUTION"),
])
def test_an_absent_or_malformed_producer_identity_refuses_the_brief(drop, over, named):
    env = {k: v for k, v in GOOD.items() if k != drop}
    env.update(over or {})
    with pytest.raises(sb.BriefRefused, match="producer_identity_absent") as exc:
        sb.producer_identity(env)
    assert named in str(exc.value)


def test_the_producing_commit_must_be_the_sealing_commit_the_brief_names(built):
    w = built
    _verified(w)
    from .test_a53_verification_job import login
    with login(w, "gochara_verifier") as c:
        with c.transaction():
            out = sb.brief(c, CHART_ID, GEN, sealing_commit="aaaaaaa")
            with pytest.raises(sb.BriefRefused, match="producer_not_sealing_commit"):
                sb.persist_brief(c, out, producer={"commit": "bbbbbbb", "image_digest": IMAGE, "execution_id": "e"})
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_brief").fetchone()[0] == 0


def test_the_persisted_brief_carries_its_producer_and_the_table_refuses_a_malformed_one(built):
    w = built
    _verified(w)
    out = _brief_as_verifier(w, sealing_commit=COMMIT, execution="exec-A")
    row = w.conn.execute("SELECT producer_commit, image_digest, execution_id, produced_by FROM public.ka_gochara_seal_brief").fetchone()
    assert tuple(row) == (COMMIT, IMAGE, "exec-A", "gochara_verifier") and out["persisted"]["brief_id"]
    for image in ("latest", "sha256:" + "G" * 64, "sha256:abc"):
        with pytest.raises(psycopg.errors.CheckViolation):
            w.conn.execute("INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest,"
                           " runner_identity, producer_commit, image_digest, execution_id) VALUES (%s::uuid, %s, gen_random_uuid(),"
                           " repeat('a', 64), repeat('0', 64), '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 't', %s, 'e')",
                           (CHART_ID, GEN, image))


# ── the receipt: the specific brief, the producing commit, the execution ──────────────────────────────────────────

def _receipt_sql(w, *, digest, brief_id, execution, commit):
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        from services.gochara_kernel import ledger as gk_ledger
        gk_ledger.publish(w.conn, CHART_ID, GEN)
        mid = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        w.conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id,"
                       " producer_execution_id, approver_login, approved_by_note, run_id, run_attempt, workflow_commit)"
                       " VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, 'x', 'x', 1, 1, %s)",
                       (CHART_ID, GEN, mid, digest, brief_id, execution, commit))


def test_the_receipt_must_name_the_current_brief_id_the_producing_commit_and_the_execution(built):
    w = built
    _verified(w)
    out = _brief_as_verifier(w, sealing_commit=COMMIT, execution="exec-A")
    good = dict(digest=out["sha256"], brief_id=out["persisted"]["brief_id"], execution="exec-A", commit=COMMIT)
    for over, why in (({"brief_id": good["brief_id"] + 7}, "receipt_brief_id_mismatch"),
                      ({"execution": "exec-B"}, "receipt_brief_execution_mismatch"),
                      ({"commit": "1234567"}, "receipt_brief_producer_commit_mismatch")):
        with pytest.raises(psycopg.errors.CheckViolation, match=why):
            _receipt_sql(w, **{**good, **over})
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0
        assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"     # nothing stayed published
    _receipt_sql(w, **good)
    assert w.conn.execute("SELECT brief_id, producer_execution_id FROM public.ka_gochara_seal_approval").fetchone() == (good["brief_id"], "exec-A")


def test_an_older_same_state_brief_of_another_execution_cannot_pass_as_this_runs_approval(built):
    """Two briefs of the SAME candidate state and revision (so the same digest) from two executions: only the latest is current. An approval that
    names the older brief id or execution is refused even though the digest is the very one the database holds."""
    w = built
    _verified(w)
    old = _brief_as_verifier(w, sealing_commit=COMMIT, execution="exec-OLD")
    new = _brief_as_verifier(w, sealing_commit=COMMIT, execution="exec-NEW")
    assert old["sha256"] == new["sha256"] and old["persisted"]["brief_id"] < new["persisted"]["brief_id"]
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_id_mismatch"):
        _receipt_sql(w, digest=new["sha256"], brief_id=old["persisted"]["brief_id"], execution="exec-OLD", commit=COMMIT)
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_execution_mismatch"):
        _receipt_sql(w, digest=new["sha256"], brief_id=new["persisted"]["brief_id"], execution="exec-OLD", commit=COMMIT)
    _receipt_sql(w, digest=new["sha256"], brief_id=new["persisted"]["brief_id"], execution="exec-NEW", commit=COMMIT)


# ── the approval record and the sealing job ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("over", [{"brief_id": 0}, {"brief_id": "7"}, {"brief_id": True}, {"brief_id": None}, {"producer_execution_id": " "},
                                  {"producer_execution_id": 5}, {"schema": "seal_approval/1"}])
def test_an_approval_without_a_well_formed_brief_id_and_execution_is_refused_and_nothing_is_written(sealable, capsys, over):
    code, out = _run_job(sealable, capsys, _approval(sealable.digest, **over))
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_malformed", out
    _nothing_written(sealable)


@pytest.mark.parametrize("missing", ["brief_id", "producer_execution_id"])
def test_an_approval_missing_either_field_is_refused(sealable, capsys, missing):
    a = _approval(sealable.digest)
    del a[missing]
    code, out = _run_job(sealable, capsys, a)
    assert code == sf.EXIT_REFUSED and out["code"] == "approval_malformed", out
    _nothing_written(sealable)


def test_the_job_refuses_an_approval_naming_another_brief_id_or_execution_before_publishing(sealable, capsys):
    w = sealable
    wrong_id = _approval(w.digest, brief_id=BRIEF_IDS[w.digest] + 1)
    code, out = _run_job(w, capsys, wrong_id)
    assert code == sf.EXIT_MISMATCH and "receipt_brief_id_mismatch" in out["detail"], out
    code, out = _run_job(w, capsys, _approval(w.digest, producer_execution_id="some-other-execution"))
    assert code == sf.EXIT_MISMATCH and "receipt_brief_execution_mismatch" in out["detail"], out
    _nothing_written(w)


def test_fresh_attempt_and_explicit_reuse_both_seal_only_with_an_approval_naming_the_current_brief(sealable, capsys, monkeypatch):
    """FRESH: the run's own brief job persisted the brief the approval names — `sealable` (its brief is the latest). REUSE (a seal-only rerun of an
    earlier run's brief): allowed iff that brief is STILL the current persisted one; a newer brief makes it stale and the job refuses."""
    w = sealable
    monkeypatch.setenv("GITHUB_RUN_ID", "555")                                                     # a later workflow run…
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    code, out = _run_job(w, capsys, _approval(w.digest, run_id=555, run_attempt=1))               # …with a FRESH approval naming the same brief
    assert code == sf.EXIT_SEALED and out["run_id"] == 555, out
    r = w.conn.execute("SELECT brief_id, run_id FROM public.ka_gochara_seal_approval").fetchone()
    assert tuple(r) == (BRIEF_IDS[w.digest], 555)


def test_a_reuse_after_a_newer_brief_exists_is_refused(sealable, capsys):
    w = sealable
    newer = _brief_as_verifier(w, sealing_commit="1" * 40, execution="exec-newer")                 # a newer brief (another revision) supersedes
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_MISMATCH and "receipt_brief_superseded" in out["detail"], out
    _nothing_written(w)
    assert newer["persisted"]["brief_id"] > BRIEF_IDS[w.digest]
