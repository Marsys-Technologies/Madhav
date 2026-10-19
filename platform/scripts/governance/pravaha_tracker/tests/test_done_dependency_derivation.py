"""SR-BOLD-07 follow-up: `ky done` reads a dependency as done by the SAME derivation the display uses.

Source of the rule: the owner ruling SR-BOLD-07 (/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl) — a code item is
done when its PR is merged AND contained in a successful main deploy — and plan v3.0 SR-A4-01 (an operation item keeps
strict ordered completion: every dependency must be done). Measured defect 2026-10-19: the tracker showed J-3a… done
by merge+deploy while `ky done J-3c` refused "dependencies remain open: J-3a, …".
One oracle per distinct claim (D-OWNER-TESTS-20261016).
"""
from __future__ import annotations

import pytest

from pravaha_tracker import merged_deployed as M
from pravaha_tracker.completion import CompletionError, guarded_done_event

MERGE, DEPLOYED, DIGEST = "b" * 40, "c" * 40, "d" * 64


class Source:
    """What GitHub and git say: PR 10 is merged and deployed; PR 11 is merged but not deployed; PR 12 is open."""

    def pr(self, number):
        return {10: {"number": 10, "state": "MERGED", "headRefOid": "a" * 40, "mergeCommit": {"oid": MERGE}},
                11: {"number": 11, "state": "MERGED", "headRefOid": "a" * 40, "mergeCommit": {"oid": "e" * 40}},
                12: {"number": 12, "state": "OPEN", "headRefOid": "a" * 40, "mergeCommit": None}}.get(number)

    def merged_prs_for_branch(self, branch):
        return []

    def pr_of_commit(self, sha):
        return None

    def diff_paths(self, merge):
        return frozenset({"x.py"})

    def has_path(self, merge, path):
        return True

    def deployed(self, merge):
        ok = merge == MERGE
        return {"deployed_sha": DEPLOYED if ok else None, "run_id": 777 if ok else None, "contains_merge": ok}


def _code(iid, pr):
    return {"id": iid, "track": "K", "owner": "K", "title": iid, "depends_on": [], "completion_kind": "code",
            "detector": {"type": "pr_merged", "pr": pr}, "brief": {"owns": ["x.py"]}}


def _model(dep_pr):
    op = {"id": "K-OP", "track": "K", "owner": "N", "title": "op", "depends_on": ["K-DEP"],
          "detector": {"type": "file_exists", "path": "/receipt"}}
    return {"campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V"},
            "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
            "items": [_code("K-DEP", dep_pr), op]}


def _close_op(model, derived):
    receipt = {"operation_id": "op-1", "item_id": "K-OP", "status": "COMPLETED"}
    verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "K-OP", "phase": "artifact", "head": None,
               "artifact_digest": DIGEST, "result": "ACCEPTED", "ts": "2026-10-19T00:00:00+00:00"}
    proof = {"type": "operation", "operation_id": "op-1", "receipt": receipt, "artifact_digest": DIGEST}
    return guarded_done_event(model, [verdict], "K-OP", "stream-S:s1", {"status": "done"}, proof,
                              derived_done=derived)


def test_dependency_done_only_by_merge_and_deploy_lets_the_dependent_close():
    model = _model(10)
    derived = M.derive_for_events(model, [], Source())
    assert "K-DEP" in derived                               # the display's derivation says done
    assert _close_op(model, derived)["state"] == "done"     # so the completion check agrees


def test_dependency_that_is_not_merged_and_deployed_still_blocks():
    for pr in (11, 12):                                     # merged-not-deployed, and still open
        model = _model(pr)
        derived = M.derive_for_events(model, [], Source())
        assert "K-DEP" not in derived
        with pytest.raises(CompletionError, match="dependencies remain open: K-DEP"):
            _close_op(model, derived)


def test_without_the_shared_derivation_the_check_would_refuse_a_displayed_done_dependency():
    # the pre-fix behaviour (event log only) is reproduced by passing nothing: this is what the display contradicted
    with pytest.raises(CompletionError, match="dependencies remain open: K-DEP"):
        _close_op(_model(10), None)


def test_the_item_being_completed_is_not_refused_as_already_done_by_its_own_derivation():
    model = _model(10)
    model["items"][1]["depends_on"] = []
    derived = M.derive_for_events(model, [], Source())
    derived["K-OP"] = {"pr": 10, "evidence": "x", "detail": "x", "deploy_run_id": 1, "deploy": {}}
    assert _close_op(model, derived)["state"] == "done"


def test_derive_for_events_limits_work_to_the_upstream_and_skips_guarded_closures():
    model = _model(10)
    assert M.upstream_ids(model, "K-OP") == {"K-OP", "K-DEP"}
    assert M.derive_for_events(model, [], Source(), only={"K-OP"}) == {}
    closed = [{"kind": "item", "item": "K-DEP", "state": "done", "guarded": True}]
    assert M.derive_for_events(model, closed, Source()) == {}
