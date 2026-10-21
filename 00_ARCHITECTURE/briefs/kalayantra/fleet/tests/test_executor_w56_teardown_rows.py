"""W5W6-READINESS WP2 (brief 02), the executor side of the two K9 teardown kinds: `orchestrator_rebuild_teardown` and `orchestrator_rebuild_teardown_dryrun` are ENABLED in the committed
table (shard W56-WP2-teardown.json; surrogate ruling S-1 may hold them back, in which case this file and that shard are dropped together). The oracles read the committed table as shipped.

  C2  every teardown kind needs a V1 signer (SR-MINIMAL-PROTECTION 2; `executor.mechanical_exempt`: every `*_teardown` is a deletion, never mechanical) and the signer's attestations
      that a backup was taken and a dry run passed. (Open point, stated not hidden: the executor has no receipt detector for a K9 teardown dry run, unlike `orchestrator_rebuild`'s
      `dry_run_check`; the dry-run-first rule for this kind rests on the signer's attestation. Deletion also stays behind the pack's teardown gate and the database role.)
"""
import json

import pytest

from test_executor_cancel_lane import RUN
from test_executor_w56_cancel_kinds import ShippedWorld, TEARDOWN_KINDS

SIGNER_ONLY = "needs a V1 signer's acceptance, never a mechanical one"


@pytest.fixture
def world(tmp_path, monkeypatch):
    return ShippedWorld(tmp_path, monkeypatch)


def teardown_request(w, kind, *, oid, checks):
    req = w.request(kind, {"run-id": RUN}, oid=oid)
    if "acceptance_receipt" in req:
        path = w.mod.ACC / f"{oid}.json"
        body = json.loads(path.read_text())
        body["checks"] = checks
        path.write_text(json.dumps(body))
    return req


def c2(w):
    assert all(w.table[k]["enabled"] is True for k in TEARDOWN_KINDS)
    kind = "orchestrator_rebuild_teardown"
    assert w.mod.mechanical_exempt(kind) and w.mod.mechanical_exempt("orchestrator_rebuild_teardown_dryrun") is False   # the dry run deletes nothing: it is not a deletion
    both = {"backup_taken": True, "dry_run_passed": True}
    assert w.validate(teardown_request(w, kind, oid="op-td-ok", checks=both)) is None                                    # positive control: a signer's complete acceptance admits it
    req = teardown_request(w, kind, oid="op-td-mech", checks=both)
    req.pop("acceptance_receipt"); req["pack_fill"] = {"pack_manifest_sha256": "0" * 64, "template": {}, "fill_sha256": "0" * 64}
    assert SIGNER_ONLY in w.validate(req)                                                                               # the mechanical route is refused by name
    req.pop("pack_fill")
    assert "acceptance receipt missing" in w.validate(req)                                                              # and no route at all is refused
    for n, checks in enumerate(({"dry_run_passed": True}, {"backup_taken": True}, {})):
        why = w.validate(teardown_request(w, kind, oid=f"op-td-partial-{n}", checks=checks))
        assert why == "required backup/restore/dry-run attestation missing", (checks, why)


def test_c2_every_teardown_kind_needs_a_v1_signer_with_the_backup_and_dry_run_attestations(world):
    c2(world)


def test_c2_planted_reversion_the_teardown_suffix_rule_dropped_fails(world, monkeypatch):
    # reversion: mechanical_exempt no longer treats `*_teardown` as a deletion (only the closed SIGNED_ONLY_KINDS set)
    monkeypatch.setattr(world.mod, "mechanical_exempt", lambda kind: kind in world.mod.SIGNED_ONLY_KINDS)
    with pytest.raises(AssertionError):
        c2(world)
