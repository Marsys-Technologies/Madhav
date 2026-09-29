"""F1 (GPT-6 Astra independent review §2): the centralized fail-closed gate evaluator.

Every case here is one of the review's own counterexamples for the pre-fix code: an authoritative
decisions log supplied with no matching `decided` line must never let an item event (forged or
merely misrouted) mark a native gate done. These are negative tests — each one must fail (i.e. the
gate must NOT read 'done') against the review's own counterexample inputs.
"""
import datetime as dt

from suvarna_tracker.events import validate
from suvarna_tracker.gates import evaluate_decision_gate, evaluate_detector_gate, evaluate_gate
from suvarna_tracker.state import build_snapshot

NOW = dt.datetime(2026, 9, 30, 12, 0, tzinfo=dt.timezone.utc)

MODEL = {
    "campaign": "Suvarṇa",
    "tracks": [{"id": "T", "title": "T", "mode": "parallel"}],
    "items": [
        {"id": "GATE", "track": "T", "title": "native gate", "depends_on": [], "done_by": "decision", "decision": "N-1"},
        {"id": "DEP", "track": "T", "title": "depends on the gate", "depends_on": ["GATE"], "done_by": "event"},
        {"id": "REV", "track": "T", "title": "revision-bound gate", "depends_on": [], "done_by": "decision",
         "decision": "N-2", "revision": "abc123"},
        {"id": "DET", "track": "T", "title": "detector item", "depends_on": [], "detector": {"type": "pr_merged", "pr": 1}},
    ],
    "decisions": [{"id": "N-1", "title": "x", "recommendation": "yes"}, {"id": "N-2", "title": "y", "recommendation": "yes"}],
}


def ev(**kw):
    return validate({"actor": "a", "ts": "2026-09-30T11:00:00+00:00", **kw})


def snap(events=(), dets=None, decisions=None):
    return build_snapshot(MODEL, list(events), dets or {}, {}, {}, now=NOW, decisions=decisions)


def status_of(s, iid):
    return next(i for t in s["tracks"] for i in t["items"] if i["id"] == iid)


def log(latest: dict) -> dict:
    return {"latest": latest, "malformed": 0}


# ---- F1 negative case 1: absent decision -------------------------------------------------------

def test_absent_decision_is_never_done():
    s = snap(decisions=log({}))
    assert status_of(s, "GATE")["status"] != "done"


def test_absent_decision_with_forged_item_event_is_never_done():
    """The exact pre-fix defect: an ordinary item event for the gated item's own id, claiming done
    with evidence, while the authoritative log has no matching decided line at all."""
    forged = [ev(kind="item", item="GATE", state="done", evidence="trust me")]
    s = snap(forged, decisions=log({}))
    assert status_of(s, "GATE")["status"] != "done"


# ---- F1 negative case 2: refused / revoked -------------------------------------------------------

def test_revoked_decision_undoes_a_prior_decided():
    """A later 'revoked' line for the same decision id must undo an earlier 'decided' one — modeled
    here as decisions.load_decisions' own 'latest wins per id' resolution already having picked the
    revoked record as the latest for N-1."""
    s = snap(decisions=log({"N-1": {"id": "N-1", "state": "revoked", "detail": "revoked: superseded by a later ruling",
                                    "source": "Native, 2026-09-30: revoke", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "GATE")["status"] != "done"


def test_superseded_decision_is_never_done():
    s = snap(decisions=log({"N-1": {"id": "N-1", "state": "superseded", "detail": "superseded by N-9",
                                    "source": "Native, 2026-09-30: supersede", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "GATE")["status"] != "done"


def test_revoked_decision_with_forged_item_event_is_never_done():
    forged = [ev(kind="item", item="GATE", state="done", evidence="trust me")]
    s = snap(forged, decisions=log({"N-1": {"id": "N-1", "state": "revoked", "detail": "revoked",
                                            "source": "Native, 2026-09-30: revoke", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "GATE")["status"] != "done"


# ---- F1 negative case 3: wrong artifact revision -------------------------------------------------

def test_decided_for_wrong_revision_is_never_done():
    s = snap(decisions=log({"N-2": {"id": "N-2", "state": "decided", "detail": "approved; revision=zzz999",
                                    "source": "Native, 2026-09-30: yes", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "REV")["status"] != "done"


def test_decided_for_matching_revision_is_done():
    s = snap(decisions=log({"N-2": {"id": "N-2", "state": "decided", "detail": "approved; revision=abc123",
                                    "source": "Native, 2026-09-30: yes", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "REV")["status"] == "done"


def test_decided_with_no_revision_marker_at_all_is_never_done_for_a_pinned_item():
    s = snap(decisions=log({"N-2": {"id": "N-2", "state": "decided", "detail": "approved",
                                    "source": "Native, 2026-09-30: yes", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "REV")["status"] != "done"


# ---- F1 negative case 4: forged item event on a plain (unpinned) gate ---------------------------

def test_forged_item_event_never_flips_a_decision_gate_done_even_when_delegated():
    forged = [ev(kind="item", item="GATE", state="done", evidence="trust me")]
    s = snap(forged, decisions=log({"N-1": {"id": "N-1", "state": "delegated", "detail": "handed off",
                                            "source": "Native, 2026-09-30: delegate", "delegated_to": "x",
                                            "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "GATE")["status"] != "done"


# ---- F1 negative case 5: unmet prerequisites — a wrongly-not-done gate never releases dependents --

def test_dependent_item_stays_waiting_while_the_gate_is_not_legitimately_done():
    forged = [ev(kind="item", item="GATE", state="done", evidence="trust me")]
    s = snap(forged, decisions=log({}))
    assert status_of(s, "GATE")["status"] != "done"
    assert status_of(s, "DEP")["status"] == "waiting"
    assert status_of(s, "DEP")["deps_open"] == ["GATE"]


def test_dependent_item_becomes_ready_once_the_gate_is_legitimately_decided():
    s = snap(decisions=log({"N-1": {"id": "N-1", "state": "decided", "detail": "approved",
                                    "source": "Native, 2026-09-30: yes", "ts": "2026-09-30T10:00:00+00:00"}}))
    assert status_of(s, "GATE")["status"] == "done"
    assert status_of(s, "DEP")["status"] == "ready"


# ---- detector-gated items: an item event can never itself earn 'done' ---------------------------

def det(status, detail="x", progress=None):
    return {"status": status, "detail": detail, "checked_at": "2026-09-30T11:59:00+00:00", "source": "detector:t", "progress": progress}


def test_forged_item_event_never_flips_a_detector_gate_done():
    forged = [ev(kind="item", item="DET", state="done", evidence="trust me")]
    s = snap(forged, dets={"DET": det("pending", "not yet")}, decisions=log({}))
    assert status_of(s, "DET")["status"] == "conflict"


def test_unmeasured_detector_gate_is_never_done():
    s = snap(decisions=log({}))
    assert status_of(s, "DET")["status"] == "unknown"


# ---- direct unit tests on evaluate_gate / evaluate_decision_gate / evaluate_detector_gate --------

def test_evaluate_gate_returns_none_for_plain_event_items():
    item = {"id": "X", "done_by": "event"}
    assert evaluate_gate(item, None, None, {"items": {}, "decisions": {}}) is None


def test_evaluate_decision_gate_no_record_is_not_started_not_waiting():
    """The absence of any decision record must read 'not_started' (so the ordinary
    dependency-readiness rule applies), never a hardcoded 'waiting' that would override a
    dependency-free item's readiness."""
    item = {"id": "GATE", "done_by": "decision", "decision": "N-1"}
    out = evaluate_decision_gate(item, log({}), [])
    assert out["status"] == "not_started"


def test_evaluate_decision_gate_requested_event_is_running():
    item = {"id": "GATE", "done_by": "decision", "decision": "N-1"}
    requested = ev(kind="decision", decision="N-1", state="requested")
    out = evaluate_decision_gate(item, log({}), [requested])
    assert out["status"] == "running"


def test_evaluate_detector_gate_done_only_from_detector():
    out = evaluate_detector_gate("pr_merged", det("done", "PR merged"), None)
    assert out["status"] == "done"
    out2 = evaluate_detector_gate("pr_merged", None, None)
    assert out2["status"] == "unknown"
