"""SR-AUDIT-NA-TIMEOUT and SR-AUDIT-BOOKKEEPING (owner surrogate madhav-44, 2026-10-22): one oracle per distinct claim.

Source: the tracker open-item audit (job X-20261022T200203Z-tracker-audit, TRACKER_OPEN_AUDIT.md sections 3-5) and the rulings
that adopted it. Claims, each with the single planted reversion that makes its test fail:

  1. a `review` event on a PR that has since MERGED no longer reads as work in progress          (state.drop_merged_reviews)
  2. an unobserved merge changes nothing: honest null, never an assumed merge                      (merged_prs=None)
  3. the tracker asks GitHub about exactly the PRs the latest `review` events name                 (stale_review_prs, CodeDone)
  4. ready_at_accepted is a start condition only for a dependency that completes at its PR merge   (state.completes_at_merge)
  5. a decision whose own item reads not_applicable is not a question for the native (D-G2)        (native_queue filter)
  6. a branch nobody has pushed yet reads pending, any other fetch failure stays an error          (detectors.d_branch_merged)
  7. J-GOCHARA-TIMEOUT is not_applicable once the existing decision D-GOCHARA-TIMEOUT is refused (plan model; the decision reads decided)
  8. J-5q-b54 no longer names 4.1 as a comparator (SR-F5-41-DEFER)                                 (plan model)
  9. D-J4B-1303-NA is declared and J-4c-a55m drops the 1303 clause                                 (plan model)
 10. KR-1, KR-2, L0-K, C-2 read the deferral / "not yet" without a detector error                  (detector + snapshot)
 11. this file is matched by a CI suite glob
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D  # noqa: E402
from pravaha_tracker.merged_deployed import CodeDone  # noqa: E402
from pravaha_tracker.state import build_snapshot, completes_at_merge, drop_merged_reviews, review_pr, stale_review_prs  # noqa: E402

REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
NOW = dt.datetime(2026, 10, 22, 21, 0, tzinfo=dt.timezone.utc)
TS = NOW.isoformat()


def _rows(snap):
    return {t["id"]: t for tr in snap["tracks"] for t in tr["items"]}


def _model(items, **control):
    return {"campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V", **control},
            "tracks": [{"id": "K", "title": "K"}], "streams": [], "decisions": [], "items": [
                {"track": "K", "owner": "K", "title": i["id"], "depends_on": [], **i} for i in items]}


def _pending(model):
    return {i["id"]: {"status": "pending", "detail": "not yet", "checked_at": TS} for i in model["items"] if i.get("detector")}


def _review(item, pr, ts=TS):
    return {"kind": "item", "actor": "stream-K", "item": item, "state": "review", "ts": ts,
            "detail": f"PR #{pr} @ {'a' * 40} (pre-build; independent review ACCEPTED; PR OPEN; waiting on gate)"}


# ---------------------------------------------------------------------------------------- claims 1-3: stale review

def _review_model():
    return _model([{"id": "GATE", "detector": {"type": "file_exists", "path": "/nonexistent/gate.json"}},
                   {"id": "PREBUILT", "depends_on": ["GATE"],
                    "detector": {"type": "file_exists", "path": "/nonexistent/prebuilt.json"}}])


def test_a_review_on_a_merged_pr_no_longer_reads_in_progress():  # claim 1 (SR-AUDIT-BOOKKEEPING)
    # Audit section 4 item 3: J-5q / K9-6 carried 'review' on PRs #3600 / #3622 that merged days earlier and were counted
    # as 'in progress 8'. Reversion: drop_merged_reviews returns evs unchanged -> status review, running 1.
    model = _review_model()
    snap = build_snapshot(model, [_review("PREBUILT", 3600)], _pending(model), {}, {}, now=NOW, merged_prs=frozenset({3600}))
    row = _rows(snap)["PREBUILT"]
    assert (row["status"], row["deps_open"]) == ("waiting", ["GATE"])
    assert snap["overall"]["running"] == 0 and snap["now"] == []


def test_a_review_on_a_pr_still_open_or_not_observed_stays_review():  # claim 2 (honest null)
    # Reversion: treat "not observed" as merged (e.g. `merged_prs is None or ...`) -> these read waiting.
    events, model = [_review("PREBUILT", 3600)], _review_model()
    for merged in (None, frozenset(), frozenset({9999})):
        snap = build_snapshot(model, events, _pending(model), {}, {}, now=NOW, merged_prs=merged)
        assert _rows(snap)["PREBUILT"]["status"] == "review", merged
        assert snap["overall"]["running"] == 1


def test_only_a_trailing_merged_review_is_dropped():  # claim 1, boundary: later work on the item is real
    running = {"kind": "item", "actor": "stream-K", "item": "PREBUILT", "state": "running", "ts": TS, "detail": "rework"}
    evs = [_review("PREBUILT", 3600), running]
    assert drop_merged_reviews(evs, {3600}) == evs
    assert drop_merged_reviews([running, _review("PREBUILT", 3600)], {3600}) == [running]


def test_the_pr_a_review_event_names():  # claim 3
    assert review_pr({"detail": "PR #3622 @ fb639f5 (A6 D-40; PR OPEN)"}) == 3622
    assert review_pr({"detail": "PR OPEN; waiting on gate"}) is None
    assert review_pr({"pr": 3594, "detail": "PR #1"}) == 3594
    events = [_review("A", 3600, "2026-10-16T00:00:00+00:00"), _review("A", 3612, "2026-10-17T00:00:00+00:00"),
              _review("B", 3594), {"kind": "item", "item": "C", "state": "running", "detail": "PR #1", "ts": TS},
              {"kind": "item", "item": "D", "state": "review", "step": "s", "detail": "PR #2", "ts": TS}]
    assert stale_review_prs(events) == {3612, 3594}      # the latest event per item; a step event is not the item's review


class _Source:
    def __init__(self, states, unreadable=()):
        self.states, self.unreadable = states, set(unreadable)

    def pr(self, number):
        if number in self.unreadable:
            raise OSError("gh unreachable")
        return {"number": number, "state": self.states.get(number, "OPEN")}


def test_the_code_done_pass_observes_the_merge_of_the_prs_it_is_asked_about():  # claim 3
    # Reversion: run_once ignores watch_prs -> merged_prs() stays empty and the stale review is never dropped.
    cd = CodeDone("/nonexistent", source=_Source({3600: "MERGED", 3612: "OPEN"}, unreadable={3622}))
    assert cd.merged_prs() is None                         # nothing observed yet
    cd.run_once({"items": []}, watch_prs=frozenset({3600, 3612, 3622}))
    assert cd.merged_prs() == frozenset({3600})            # open stays unmerged; an unreadable PR is never assumed merged
    cd.run_once({"items": []}, watch_prs=frozenset())
    assert cd.merged_prs() == frozenset({3600})            # a merge cannot un-happen


# ---------------------------------------------------------------------------------------- claim 4: ready_at_accepted

def _accepted(item):
    return {"kind": "verdict", "actor": "stream-V:v", "item": item, "head": "a" * 40, "phase": "pre_merge",
            "result": "ACCEPTED", "detail": "ok", "ts": TS}


@pytest.mark.parametrize("dep, expected", [
    ({"completion_kind": "code", "detector": {"type": "branch_merged", "ref": "origin/dep"}}, "ready"),
    ({"detector": {"type": "branch_merged", "ref": "origin/dep"}}, "ready"),                       # an undeclared kind (legacy model)
    # K9-4a: an operation whose output is a dispatch receipt, not a merge
    ({"completion_kind": "operation", "detector": {"type": "file_exists", "path": "/nonexistent/dep.json"}}, "waiting"),
    # K9-6: a code item whose output is a live acceptance file, not the PR merge
    ({"completion_kind": "code", "detector": {"type": "file_exists", "path": "/nonexistent/dep.json"}}, "waiting"),
])
def test_ready_at_accepted_needs_a_dependency_that_completes_at_its_merge(dep, expected):  # claim 4 (SR-AUDIT-BOOKKEEPING)
    # Audit section 4 item 1: K9-4b and V-K9 read READY because the pre-merge verdict of the pre-build PR #3622 made K9-4a / K9-6
    # "start-satisfied". Reversion: ready_at_accepted adds every ACCEPTED item again -> the two waiting rows read ready.
    model = _model([{"id": "DEP", **dep}, {"id": "NEXT", "depends_on": ["DEP"],
                                          "detector": {"type": "file_exists", "path": "/nonexistent/next.json"}}],
                   ready_at_merge=True, ready_at_accepted=True)
    row = _rows(build_snapshot(model, [_accepted("DEP")], _pending(model), {}, {}, now=NOW))["NEXT"]
    assert row["status"] == expected and row["deps_open"] == ["DEP"]


def test_completes_at_merge_is_a_property_of_the_detector_and_the_kind():  # claim 4
    assert completes_at_merge({"detector": {"type": "pr_merged", "pr": 1}, "completion_kind": "code"})
    assert not completes_at_merge({"detector": {"type": "pr_ready", "pr": 1}})
    assert not completes_at_merge({"detector": {"type": "branch_merged", "ref": "x"}, "completion_kind": "artifact"})
    assert not completes_at_merge({})


# ---------------------------------------------------------------------------------------- claim 5: native queue

def test_a_decision_whose_item_is_not_applicable_is_not_a_question_for_the_native():  # claim 5 (D-G2)
    # D-G2 requires D-VC approved; D-VC was refused, so the D-G2 item reads not_applicable yet its own decision stayed 'pending' in
    # the native queue. Reversion: drop the `!= "not_applicable"` filter -> D-G2 is listed.
    def item(iid, **extra):
        return {"id": iid, "track": "K", "owner": "N", "title": iid, "depends_on": [], **extra}

    model = {"campaign": "fixture", "tracks": [{"id": "K", "title": "K"}], "streams": [],
             "control_plane": {"guarded_completion": True, "decision_outcomes": {"final": ["approved", "refused"],
                                                                                 "open": ["deferred", "insufficient_evidence"]}},
             "decisions": [{"id": "D-VC", "title": "vc"}, {"id": "D-G2", "title": "g2"}, {"id": "D-OTHER", "title": "other"}],
             "items": [item("D-VC", done_by="decision", decision="D-VC"),
                       item("D-G2", done_by="decision", decision="D-G2", depends_on=["D-VC"], requires_outcome={"D-VC": "approved"}),
                       item("D-OTHER", done_by="decision", decision="D-OTHER")]}
    refused = {"kind": "decision", "actor": "steward", "decision": "D-VC", "state": "delegated", "outcome": "refused",
               "detail": "no population", "ts": TS}
    snap = build_snapshot(model, [refused], {}, {}, {}, now=NOW)
    assert _rows(snap)["D-G2"]["status"] == "not_applicable"
    assert [d["id"] for d in snap["native_queue"]] == ["D-OTHER"]


# ---------------------------------------------------------------------------------------- claim 6: branch not pushed yet

@pytest.fixture
def det(tmp_path):
    detector = D.Detectors(D.Config(str(tmp_path), None, str(tmp_path)))
    yield detector
    detector._pool.shutdown(wait=True)


def _measure(det, spec):
    key = det.key(spec)
    det._run_one(key, spec)          # the production path: an exception becomes an `error` result here
    return det.results[key]


def _git(monkeypatch, fetch):
    def run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return fetch(cmd[-1])
        return 1, ""
    monkeypatch.setattr(D, "_run", run)


def test_a_branch_that_is_not_on_origin_yet_reads_pending_not_error(det, monkeypatch):  # claim 6 (KR-1, KR-2, L0-K, C-2)
    # Reversion: remove the `except RuntimeError` in d_branch_merged -> status error "git fetch ...: couldn't find remote ref".
    _git(monkeypatch, lambda branch: (0, "") if branch == "main" else (128, f"fatal: couldn't find remote ref {branch}"))
    result = _measure(det, {"type": "branch_merged", "ref": "origin/kalayantra/kr-1"})
    assert result.status == "pending" and "does not exist on origin yet" in result.detail


def test_any_other_fetch_failure_stays_a_detector_error(det, monkeypatch):  # claim 6, boundary (the K5-2-* PermissionError class)
    _git(monkeypatch, lambda branch: (0, "") if branch == "main" else (1, "fatal: unable to access: Permission denied"))
    assert _measure(det, {"type": "branch_merged", "ref": "origin/kalayantra/kr-1"}).status == "error"
    det._fetched.clear()
    _git(monkeypatch, lambda branch: (128, "fatal: couldn't find remote ref main") if branch == "main" else (0, ""))
    assert _measure(det, {"type": "branch_merged", "ref": "origin/kalayantra/kr-1"}).status == "error"   # main itself is never "not yet"


# ---------------------------------------------------------------------------------------- the real plan model

@pytest.fixture(scope="module")
def model():
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def items(model):
    return {i["id"]: i for i in model["items"]}


def _decision(decision, outcome, ts=TS):
    return {"kind": "decision", "actor": "steward", "decision": decision, "state": "delegated", "outcome": outcome,
            "detail": "recorded", "ts": ts}


def _snapshot(model, events, det_results=None):
    from pravaha_tracker.state import load_closure
    return build_snapshot(model, events, det_results or {}, {}, {}, now=NOW, closure=load_closure(model))


def test_the_timeout_pair_is_retired_by_the_existing_decision_item(model, items):  # claim 7 (SR-AUDIT-NA-TIMEOUT, fold-out)
    # J-GOCHARA-TIMEOUT reads not_applicable through the plan's own requires_outcome on the EXISTING decision item D-GOCHARA-TIMEOUT
    # (the fold-out added no item; kyclosure demands a decision item, which D-GOCHARA-TIMEOUT already is). The decision item itself
    # reads decided once recorded (the no-cycle invariant forbids requiring itself), class retired, so it is never work or deferred.
    # Reversion: restore requires_outcome on the folded-out D-GOCHARA-TIMEOUT-NA (kyclosure refuses it) or change the required outcome
    # to refused -> the item reads waiting after the refusal.
    targets = ["D-GOCHARA-TIMEOUT", "J-GOCHARA-TIMEOUT"]
    assert "D-GOCHARA-TIMEOUT-NA" not in items and "D-GOCHARA-TIMEOUT-NA" not in {d["id"] for d in model["decisions"]}
    assert items["J-GOCHARA-TIMEOUT"]["requires_outcome"] == {"D-GOCHARA-TIMEOUT": "approved"}
    assert "requires_outcome" not in items["D-GOCHARA-TIMEOUT"] and items["D-GOCHARA-TIMEOUT"]["done_by"] == "decision"
    for iid in targets:
        assert items[iid]["triage"]["class"] == "retired" and items[iid]["triage"]["decision"] == "D-GOCHARA-TIMEOUT"
        assert "SR-AUDIT-NA-TIMEOUT" in items[iid]["triage"]["reason"]
    deferred = _snapshot(model, [{"kind": "decision", "actor": "steward", "decision": "D-GOCHARA-TIMEOUT", "state": "delegated",
                                  "outcome": "deferred", "detail": "KYD-108", "ts": TS}])
    assert _rows(deferred)["J-GOCHARA-TIMEOUT"]["status"] != "not_applicable"            # an open outcome retires nothing
    after = _snapshot(model, [_decision("D-GOCHARA-TIMEOUT", "refused")])
    assert _rows(after)["J-GOCHARA-TIMEOUT"]["status"] == "not_applicable"
    decision = _rows(after)["D-GOCHARA-TIMEOUT"]                                          # decided, like D-VC after its refusal: it is
    assert decision["outcome"] == "refused" and decision["status"] != "not_applicable"    # not n/a, and waits on nothing but B-7 (done live)
    assert set(decision["deps_open"]) <= {"B-7"}
    assert not {d["id"] for d in after["overall"]["deferred"]} & set(targets)           # no longer deferred: ended, not parked
    cancelled = after["overall"]["reconciliation"]["cancelled"]["total"]
    assert cancelled > _snapshot(model, [])["overall"]["reconciliation"]["cancelled"]["total"] - 1       # class retired: cancelled, not work
    done = {"kind": "item", "actor": "stream-K:d46-sweep", "item": "JGT-NB-01", "state": "done", "guarded": True,
            "evidence": "PR #3569 merged", "ts": TS}
    kept = _snapshot(model, [_decision("D-GOCHARA-TIMEOUT", "refused"), done])
    assert _rows(kept)["JGT-NB-01"]["status"] == "done"                                 # the already-done consumer is untouched
    assert _rows(after)["C-1"]["status"] != "not_applicable"


def test_the_plan_item_total_is_274_and_no_ruling_became_an_item(model, items):  # claim 12 (fold-out: "do not add anything to the tracker")
    # Reversion: re-add D-GOCHARA-TIMEOUT-NA / D-J4B-1303-NA as decision items (what #3896 did) -> 276.
    assert len(model["items"]) == 274
    assert "D-GOCHARA-TIMEOUT-NA" not in items and "D-J4B-1303-NA" not in items
    assert {"retire_decision"} >= {(i.get("triage") or {}).get("class") for i in model["items"]
                                   if i["id"] in ("D-GOCHARA-TIMEOUT-NA", "D-J4B-1303-NA")}


def test_the_timeout_items_are_outside_the_closure_and_gate_nothing_in_it(model, items):  # claim 7
    from importlib import util
    spec = util.spec_from_file_location("kyclosure", REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/kyclosure.py")
    kyclosure = util.module_from_spec(spec)
    sys.modules[spec.name] = kyclosure
    spec.loader.exec_module(kyclosure)
    roots = json.loads((REPO / "00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v3.json").read_text(encoding="utf-8"))
    closure = set(kyclosure.compute(model, roots)["closure"])
    assert not closure & {"D-GOCHARA-TIMEOUT", "J-GOCHARA-TIMEOUT"}


def test_d_g2_is_not_in_the_native_queue_of_the_real_plan(model):  # claim 5, real model (SR-AUDIT-BOOKKEEPING)
    snap = _snapshot(model, [_decision("D-VC", "refused")])
    assert _rows(snap)["D-G2"]["status"] == "not_applicable"
    assert "D-G2" not in {d["id"] for d in snap["native_queue"]}


def test_j_5q_b54_no_longer_names_4_1_as_a_comparator(items):  # claim 8 (SR-F5-41-DEFER)
    # Reversion: restore the title "'5.0' vs '3.0' vs '4.1'" or the "prove inherited prerequisite: B4.4" test line.
    item = items["J-5q-b54"]
    assert "vs '4.1'" not in item["title"] and "'5.0' vs '3.0'" in item["title"] and "SR-F5-41-DEFER" in item["title"]
    tests = item["brief"]["tests"]
    assert "Before landing, independently prove inherited prerequisite: B4.4" not in tests
    note = next(t for t in tests if "SR-F5-41-DEFER" in t)
    assert "not a comparator" in note and "never substitutes another baseline" in note and "EVAL-41-ON-SEALED" in note
    assert item["depends_on"] == ["J-0m", "J-4f"] and item["triage"]["class"] == "a"      # in scope, narrowed, not deferred


def test_d_j4b_1303_na_is_declared_and_the_1303_clause_leaves_j_4c_a55m(model, items):  # claim 9 (audit R3, fold-out)
    # Reversion: drop the decision declaration, or put "1303 ... OPEN" back into the step's tests.
    decisions = {d["id"]: d for d in model["decisions"]}
    assert "D-J4B-1303-NA" in decisions and "F-DORMANT-ROLES" in decisions["D-J4B-1303-NA"]["default"]
    assert "J-4c-a55m.window2-20261021T0315Z" in decisions["D-J4B-1303-NA"]["default"]
    assert decisions["D-J4B-1303-NA"]["retires"] == ["J-4c-a55m (the 1303 clause only)"]
    assert "D-J4B-1303-NA" not in items                                                    # a declared decision, not a plan item
    a55m = items["J-4c-a55m"]
    assert "1303" not in a55m["title"] and "dormant-role revokes" not in a55m["title"]
    clause = next(t for t in a55m["brief"]["tests"] if t.startswith("1303 and the dormant-role revokes"))
    assert "NOT APPLICABLE by D-J4B-1303-NA" in clause and "OPEN" not in clause and "This step no longer requires the revokes" in clause
    assert "stay OPEN" not in a55m["brief"]["notes"] and "D-J4B-1303-NA" in a55m["brief"]["notes"]
    assert "requires_outcome" not in a55m and "D-J4B-1303-NA" not in a55m["depends_on"]    # retiring a clause never retires the item
    assert _rows(_snapshot(model, [_decision("D-J4B-1303-NA", "refused")]))["J-4c-a55m"]["status"] != "not_applicable"
    # a retirement decision with no item of its own is still STAGED (not a question for the native), recorded or not
    # (reversion: drop the `retires` clause in state.build_snapshot -> it is listed as pending)
    assert "D-J4B-1303-NA" not in {d["id"] for d in _snapshot(model, [])["native_queue"]}
    assert "D-J4B-1303-NA" not in {d["id"] for d in _snapshot(model, [_decision("D-J4B-1303-NA", "refused")])["native_queue"]}


@pytest.mark.parametrize("iid", ["KR-1", "KR-2", "L0-K", "C-2"])
def test_parked_and_future_branch_items_read_their_deferral_without_a_detector_error(model, items, det, monkeypatch, iid):  # claim 10
    # The four items whose branch does not exist: with the detector fix they read pending (not a fault), and the deferred three keep
    # reading parked and are listed apart with the SR-PARKED-OUT-OF-CAMPAIGN reason and re-entry. Reversion: the detector fix.
    _git(monkeypatch, lambda branch: (0, "") if branch == "main" else (128, f"fatal: couldn't find remote ref {branch}"))
    result = _measure(det, items[iid]["detector"])
    assert result.status == "pending"
    events = []
    if iid != "C-2":
        events = [{"kind": "item", "actor": "steward", "item": iid, "state": "parked", "ts": TS,
                   "detail": "deferred; re-entry: after V-J6 is accepted"}]
    snap = _snapshot(model, events, {iid: result.to_dict()})
    row = _rows(snap)[iid]
    assert "RuntimeError" not in row["detail"] and "couldn't find remote ref" not in row["detail"]
    if iid == "C-2":
        assert row["status"] == "waiting"
    else:
        assert row["status"] == "parked"
        listed = {d["id"]: d for d in snap["overall"]["deferred"]}
        assert listed[iid]["re_entry"] and "SR-PARKED-OUT-OF-CAMPAIGN" in items[iid]["triage"]["reason"]


def test_this_file_is_matched_by_a_ci_suite_glob():  # claim 11
    suites = json.loads((REPO / "platform/scripts/governance/ci_test_suites.json").read_text(encoding="utf-8"))
    me = Path(__file__).resolve().relative_to(REPO).as_posix()
    globs = [g for prof in suites["suites"].values() for g in prof.get("include", [])]
    assert any(fnmatch.fnmatch(me, g) for g in globs), me
