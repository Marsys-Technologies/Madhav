"""A5.3 — ST-WIRE-2 item 3: the sealing job's OWN-CHECKOUT self-check, before any database contact.

The digest of the implementation modules the job is running must equal the digest REGISTERED for the sealing commit
(`services/gochara_kernel/implementation_digest.lock.json`, committed with the code). A CI drift guard fails when the lock is stale; the job
refuses (exit 4, named) when the running code differs, or the lock is absent/unreadable — without ever connecting to a database."""
from __future__ import annotations

import json

import pytest

from pipeline.orchestrator import seal_job
from services.gochara_kernel import implementation_registry as reg
from services.gochara_kernel import seal_flow as sf
from services.gochara_kernel import window_gate as wg

from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r12_seal_job import _approval, _nothing_written, _run_job, sealable  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401


def test_the_committed_lock_is_current_for_the_code_in_this_checkout():
    """DRIFT GUARD: a commit that changes any governed module must carry the regenerated lock
    (`python -m services.gochara_kernel.implementation_registry --write`)."""
    assert reg.problem() is None, f"implementation_digest.lock.json is stale — regenerate it: {reg.problem()}"
    doc = reg.registered()
    assert doc["implementation_digest"] == wg.implementation_digest() and set(doc["stages"]) == {"geometry", "evaluation", "window"}


def test_the_sealing_job_module_and_the_registry_inputs_are_inside_the_digested_code():
    from services.gochara_kernel import input_vector as iv
    window = iv.IMPLEMENTATION_MODULES["window"]
    assert "pipeline.orchestrator.seal_job" in window and "services.gochara_kernel.seal_flow" in window


def test_a_changed_module_or_a_stale_lock_is_a_named_mismatch(tmp_path):
    good = reg.compute()
    p = tmp_path / "lock.json"
    p.write_text(json.dumps({**good, "implementation_digest": "0" * 64, "stages": {**good["stages"], "window": "0" * 64}}))
    why = reg.problem(p)
    assert why.startswith("digest_mismatch") and "['window']" in why
    p.write_text(json.dumps(good))
    assert reg.problem(p) is None
    for bad in ("", "not json", "[]", json.dumps({**good, "schema": "other/1"}), json.dumps({"schema": reg.SCHEMA})):
        p.write_text(bad)
        assert reg.problem(p) == "no_registered_digest", bad
    assert reg.problem(tmp_path / "absent.json") == "no_registered_digest"


def _forbid_database(monkeypatch):
    import psycopg

    def boom(*a, **k):                                               # pragma: no cover — reached only if the check is NOT first
        raise AssertionError("the sealing job contacted a database before its own-checkout self-check")
    monkeypatch.setattr(psycopg, "connect", boom)


@pytest.mark.parametrize("lock,code", [("stale", "own_checkout_digest_mismatch"), ("absent", "own_checkout_digest_unregistered")])
def test_the_job_refuses_before_any_database_contact(monkeypatch, tmp_path, capsys, lock, code):
    p = tmp_path / "lock.json"
    if lock == "stale":
        p.write_text(json.dumps({**reg.compute(), "implementation_digest": "f" * 64}))
    monkeypatch.setattr(reg, "LOCK_PATH", p)
    monkeypatch.setenv(seal_job.ENV_URL, "postgresql://never-contacted/db")
    _forbid_database(monkeypatch)
    approval = tmp_path / "approval.json"
    approval.write_text("{}")
    rc = seal_job.main(["--chart", "482012f1-710e-4a25-994a-93821f5871aa", "--approval-file", str(approval)])
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == sf.EXIT_IDENTITY and out["code"] == code and out["status"] == "REFUSED", out


def test_with_the_registered_code_the_job_proceeds_to_the_next_check(monkeypatch, tmp_path, capsys):
    """(The same job, current lock: it gets past the self-check — here it stops at the absent credential, which is the NEXT act.)"""
    monkeypatch.delenv(seal_job.ENV_URL, raising=False)
    approval = tmp_path / "approval.json"
    approval.write_text("{}")
    rc = seal_job.main(["--chart", "482012f1-710e-4a25-994a-93821f5871aa", "--approval-file", str(approval)])
    assert rc == sf.EXIT_IDENTITY and json.loads(capsys.readouterr().out.strip().splitlines()[-1])["code"] == "no_sealer_credential"


def test_a_sealer_of_different_code_than_the_manifest_pins_is_refused_before_publishing(sealable, monkeypatch, capsys):
    monkeypatch.setattr(reg, "problem", lambda path=None: None)                               # (the lock check is separate: pretend it passed)
    monkeypatch.setattr(wg, "implementation_digest", lambda modules=None: "e" * 64)
    code, out = _run_job(sealable, capsys, _approval(sealable.digest))
    assert code == sf.EXIT_MISMATCH and "sealer_code_not_pinned" in out["detail"], out
    _nothing_written(sealable)
