"""Plan-model reconciliation (relaunch plan v2.2 §0 step 5).

The two reconciliation tests the plan names:
  1. path-only migration — identical item states from one hashed EVENTS prefix, one captured detector-result
     map and one fixed clock (tests `test_path_*`);
  2. triage — the model's delta equals the reviewed expected delta covering dependencies, dispositions,
     readiness and close membership, with earned guarded completions and their evidence preserved
     (tests `test_triage_*`).
Around them: the inputs are what they claim to be, the model is the reproducible build of those inputs, the
staged decisions are not published, and the build refuses inconsistent declarations.

The event log is read-only input. It lives on the campaign host; where it is absent the tests that need it SKIP
(a skip is not a pass). Nothing here writes a tracker event.
"""
import copy
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
CONTROL = REPO / "00_ARCHITECTURE" / "control" / "kalayantra"
BRIEFS = REPO / "00_ARCHITECTURE" / "briefs" / "kalayantra"
FIX = HERE / "fixtures" / "reconcile"
sys.path.insert(0, str(FLEET))
sys.path.insert(0, str(REPO / "platform" / "scripts" / "governance"))

import kyclosure  # noqa: E402
import kyreconcile as R  # noqa: E402

# the committed pre-reconciliation model (148 items; blob of commit 4a7f80a9c)
BASE_FILE_SHA256 = "bf522425455cc8054856d2b0252f538add7eaed672771016d9c873b25ff062a1"
# the expected delta the independent reviewer accepted; any change to the delta needs re-review (owner, 2026-10-11)
REVIEWED_DELTA_SHA256 = "ae527f0a6696d89524b074cc6036386c4dca3877af85b86bc6a699a690056000"
PLANNER_SESSIONS = {"local_ec1c912e-e039-4666-abc3-a815f9c4a2d1", "local_ef70d1f5-345a-4255-847f-212971af5951"}
EVENTS = Path(os.environ.get("KY_RECONCILE_EVENTS", "/Users/Dev/kalayantra/run/EVENTS.jsonl"))
KINDS = {"code", "artifact", "operation", "packet"}


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def base():
    return R.load(FIX / "plan_model.base.json.gz")


@pytest.fixture(scope="module")
def decl():
    return R.load(CONTROL / "TRIAGE_DECLARATIONS_v2_2.json")


@pytest.fixture(scope="module")
def roots():
    return R.load(CONTROL / "ACCEPTANCE_ROOTS_v2_1.json")


@pytest.fixture(scope="module")
def staged():
    return R.load(CONTROL / "STAGED_MODEL_ACTIONS_v2_2.json")


@pytest.fixture(scope="module")
def final():
    # The accepted v2.2 reconciliation is immutable. Live models may append later campaign items.
    return R.load(FIX / "plan_model.reviewed.json.gz")


@pytest.fixture(scope="module")
def capture():
    return R.load(FIX / "capture.json")


@pytest.fixture(scope="module")
def events(capture):
    if not EVENTS.exists():
        pytest.skip(f"event log {EVENTS} is not on this host (set KY_RECONCILE_EVENTS); this is a skip, not a pass")
    return R.read_events_prefix(EVENTS, capture)  # raises if the prefix does not hash to the captured value


@pytest.fixture(scope="module")
def migrated(base):
    return R.migrate_paths(base)


# ---------------------------------------------------------------- inputs are what they claim to be

def test_base_fixture_is_the_committed_pre_reconciliation_model(base):
    raw = gzip.decompress((FIX / "plan_model.base.json.gz").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == BASE_FILE_SHA256
    assert len(base["items"]) == 148


def test_events_prefix_refuses_a_wrong_hash(capture, events):
    wrong = copy.deepcopy(capture)
    wrong["events"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        R.read_events_prefix(EVENTS, wrong)


def test_capture_replays_the_live_snapshot(base, capture, events):
    """the reduced detector map, the hashed prefix and the fixed clock reproduce all 148 captured item states"""
    assert len(capture["item_states"]) == 148
    assert R.replay_mismatches(base, events, capture) == {}


# ---------------------------------------------------------------- reconciliation test 1: path-only migration

def test_path_migration_changes_paths_only(base, migrated):
    assert migrated != base
    assert R.unmigrate_paths(migrated, base) == base
    assert R.OLD_CAMPAIGN not in json.dumps(migrated, ensure_ascii=False)
    for stream in migrated["streams"]:
        assert stream["worktrees"][0] == R.CAMPAIGN
        assert all(w.startswith(R.POLICY_ROOT + "/kalayantra-") for w in stream["worktrees"])
    for a, b in zip(base["items"], migrated["items"]):
        assert a.keys() == b.keys() and a["id"] == b["id"]
        assert a["depends_on"] == b["depends_on"] and a.get("steps") == b.get("steps")


def test_path_migration_item_states_identical(base, migrated, capture, events):
    before = R.states(base, events, capture)
    after = R.states(migrated, events, capture)
    assert len(before) == 148
    assert before == after


def test_path_only_comparison_has_teeth(base, migrated, capture, events):
    """a migration that also touched a dependency, a step list or a detector would not compare equal"""
    before = R.states(base, events, capture)
    mutants = []
    m = copy.deepcopy(migrated)
    next(i for i in m["items"] if i["id"] == "K7-4")["depends_on"].remove("K4-2b")
    mutants.append(m)
    m = copy.deepcopy(migrated)
    next(i for i in m["items"] if i["id"] == "B-K-INBOX")["steps"].pop()
    mutants.append(m)
    m = copy.deepcopy(migrated)
    del next(i for i in m["items"] if i["id"] == "J-0c")["detector"]
    mutants.append(m)
    for mutant in mutants:
        assert R.states(mutant, events, capture) != before


# ---------------------------------------------------------------- reconciliation test 2: triage

def test_triage_model_is_the_reproducible_build(base, decl, roots):
    built = R.render(R.build(base, decl, roots))
    assert built == gzip.decompress((FIX / "plan_model.reviewed.json.gz").read_bytes())
    assert built == R.render(R.build(base, decl, roots))


def test_live_model_preserves_the_reviewed_reconciliation(final):
    live = R.load(CONTROL / "plan_model.json")
    by_id = {item["id"]: item for item in live["items"]}
    assert all(by_id.get(item["id"]) == item for item in final["items"])
    assert {k: v for k, v in live.items() if k != "items"} == {k: v for k, v in final.items() if k != "items"}


def test_triage_delta_equals_the_reviewed_expected_delta(base, final, decl, staged, capture, events):
    expected_path = CONTROL / "TRIAGE_EXPECTED_DELTA_v2_2.json"
    assert sha(expected_path) == REVIEWED_DELTA_SHA256
    assert R.compute_delta(base, final, decl, staged, capture, events) == R.load(expected_path)


def test_triage_expected_delta_was_independently_accepted():
    """DRAFT comes off only on ACCEPTED: one independent session, not the planner, bound to these exact inputs"""
    record_path = CONTROL / "TRIAGE_DELTA_REVIEW_v2_2.json"
    assert record_path.exists(), "the expected delta has not been independently reviewed"
    record = R.load(record_path)
    assert record["verdict"] == "ACCEPTED"
    assert record["reviewer_session_id"] and record["reviewer_session_id"] not in PLANNER_SESSIONS
    assert record["inputs"]["expected_delta"] == REVIEWED_DELTA_SHA256
    for name, rel in (("model", CONTROL / "plan_model.json"), ("roots", CONTROL / "ACCEPTANCE_ROOTS_v2_1.json"),
                      ("closure", CONTROL / "CLOSURE_v2_1.json"), ("kyclosure", FLEET / "kyclosure.py"),
                      ("declarations", CONTROL / "TRIAGE_DECLARATIONS_v2_2.json"),
                      ("staged_actions", CONTROL / "STAGED_MODEL_ACTIONS_v2_2.json")):
        actual = hashlib.sha256(gzip.decompress((FIX / "plan_model.reviewed.json.gz").read_bytes())).hexdigest() \
            if name == "model" else sha(rel)
        assert record["inputs"][name] == actual, f"{name} changed after the review"


def test_triage_preserves_earned_completions(base, final, decl, staged, capture, events):
    delta = R.compute_delta(base, final, decl, staged, capture, events)
    earned = delta["earned_completions"]
    assert earned["count"] == 46 and earned["all_unchanged"] is True  # 39 guarded + 1 join + 6 decisions
    recorded = {e["item"]: (e.get("completion") or {}).get("type") for e in events
                if e.get("kind") == "item" and e.get("state") == "done" and e.get("guarded") and not e.get("step")}
    assert decl["earned_completion_kinds"]["kinds"] == recorded and len(recorded) == 39
    by_id = {i["id"]: i for i in final["items"]}
    assert all(by_id[i]["completion_kind"] == k for i, k in recorded.items())
    assert all(capture["item_states"][i]["status"] == "done" for i in decl["done_outside"])
    before, after = R.states(R.migrate_paths(base), events, capture), R.states(final, events, capture)
    for iid, st in before.items():
        if st["status"] == "done":
            assert after[iid] == st, f"{iid}: an earned completion changed"


def test_triage_classes_follow_the_committed_closure(final, roots):
    from pravaha_tracker import server  # noqa: PLC0415
    assert server.check_model(final) == []
    closure = R.load(CONTROL / "CLOSURE_v2_1.json")
    assert kyclosure.compute(final, roots) == closure
    cls = {i["id"]: i["triage"]["class"] for i in final["items"]}
    assert {i for i, c in cls.items() if c == "a"} == set(closure["closure"])
    assert sorted(i for i, c in cls.items() if c == "a_close") == sorted(roots["mechanical_close_chain"]["items"])
    for i in final["items"]:
        if cls[i["id"]] == "b":
            assert i["triage"]["reason"] and i["triage"]["re_entry"]
        elif i["id"] != "JOIN-ALL":
            assert not [d for d in i["depends_on"] if cls[d] == "b"], f"{i['id']} is retained but waits on a deferred item"
    join = next(i for i in final["items"] if i["id"] == "JOIN-ALL")
    assert join["depends_on"] == sorted(i for i, c in cls.items() if c not in ("b", "a_close"))
    ids = set(cls)
    assert all(x in ids for sec in final["coverage"].values() for lst in sec.values() for x in lst)


def test_triage_generated_copies_are_identical():
    """Astra v2.2 KU-03: the plan-named file is canonical; the prompt-named copy holds the same bytes"""
    for a, b in (("ACCEPTANCE_ROOTS_v2_1.json", "ACCEPTANCE_ROOTS_v2_2.json"), ("CLOSURE_v2_1.json", "CLOSURE_v2_2.json")):
        assert (CONTROL / a).read_bytes() == (CONTROL / b).read_bytes()
    assert (BRIEFS / "WORKTREE_DISPOSITIONS_v2_1.md").read_bytes() == (BRIEFS / "WORKTREE_DISPOSITIONS_v2_2.md").read_bytes()


def test_triage_declaration_fields(final):
    legend = final["control_plane"]["declarations"]
    for i in final["items"]:
        if R.executable(i):
            assert i["completion_kind"] in KINDS and i["producer"] == i["owner"]
            assert i["reviewer_rule"] in legend["reviewer_rule"]
            assert list(i.get("step_evidence", {})) == i.get("steps", [])
            # no step detector is claimed before a packet names one (CLAUDE.md §N.8)
            assert all(v["detector"] is None and v["evidence"] == R.STEP_EVIDENCE[i["completion_kind"]]
                       for v in i.get("step_evidence", {}).values())
            if i["completion_kind"] == "code":
                assert i["reviewer_rule"].endswith("post_deploy_at_merge_commit") == R.writes_data(i)
        else:
            assert not [k for k in ("completion_kind", "producer", "reviewer_rule", "step_evidence") if k in i]
            assert i.get("done_by") in ("decision", "join")


# ---------------------------------------------------------------- staged, not published

def installation_events(staged, capture):
    events = R.staged_events(staged, capture["clock"])
    declarations = {row.get("decision") or row["item"]: row
                    for key in ("decisions", "parks", "blocks") for row in staged.get(key, [])}
    for event in events:
        event["detail"] = declarations[event.get("decision") or event["item"]]["detail"]
    return events


def staged_publication_state(log, staged, capture):
    """Count and verify each staged action; duplicates and partial publication fail."""
    counts = []
    for expected in installation_events(staged, capture):
        identity = "decision" if expected["kind"] == "decision" else "item"
        found = [e for e in log if e.get("kind") == expected["kind"]
                 and e.get(identity) == expected[identity]
                 and e.get("actor") == expected["actor"] and e.get("detail") == expected["detail"]
                 and (identity == "decision" or e.get("state") == expected["state"])]
        assert len(found) <= 1, "staged action published more than once: " + expected[identity]
        if found:
            keys = ("state", "actor", "outcome") if identity == "decision" else ("state", "actor")
            assert all(found[0].get(k) == expected[k] for k in keys), "incorrect staged effect: " + expected[identity]
        counts.append(len(found))
    assert set(counts) in ({0}, {1}), "partial staged publication"
    return "published" if all(counts) else "unpublished"


def test_staged_actions_are_not_published(final, staged, capture):
    events = [json.loads(line) for line in (FIX / "staged_preinstall.jsonl").read_text().splitlines() if line.strip()]
    assert staged["status"].startswith("STAGED — NOT PUBLISHED")
    staged_decisions = {d["decision"] for d in staged["decisions"]}
    assert staged_decisions == {"D-RETIRE-B-K-INBOX", "D-RETIRE-B-CLAIM-RECOVERY"}
    assert all(d["outcome"] == "refused" for d in staged["decisions"])
    assert not [e for e in events if e.get("decision") in staged_decisions]
    assert not [e for e in events if e.get("item") in staged_decisions | {"KV3-SCHEMA-1"}]
    now = R.states(final, events, capture)
    assert now["B-K-INBOX"]["status"] != "not_applicable" and now["B-CLAIM-RECOVERY"]["status"] != "not_applicable"
    sim = R.states(final, events + R.staged_events(staged, capture["clock"]), capture)
    for d in staged["decisions"]:
        assert sim[d["retires"]]["status"] == "not_applicable" and sim[d["retires"]]["skip_origin"] == [d["decision"]]
    assert sim["KV3-SCHEMA-1"]["status"] == "blocked"
    assert {p["item"] for p in staged["parks"]} == {i["id"] for i in final["items"] if i["triage"]["class"] == "b"}


@pytest.mark.parametrize("installed", [False, True])
def test_staged_publication_census_accepts_pre_and_post_install(staged, capture, installed):
    before = [json.loads(line) for line in (FIX / "staged_preinstall.jsonl").read_text().splitlines() if line.strip()]
    published = installation_events(staged, capture)
    assert staged_publication_state(before + (published if installed else []), staged, capture) == (
        "published" if installed else "unpublished")


@pytest.mark.parametrize("bad", ["duplicate", "wrong_outcome", "partial"])
def test_staged_publication_census_refuses_invalid_publication(staged, capture, bad):
    published = installation_events(staged, capture)
    if bad == "duplicate":
        published.append(copy.deepcopy(published[0]))
    elif bad == "wrong_outcome":
        published[0]["outcome"] = "approved"
    else:
        published.pop()
    with pytest.raises(AssertionError):
        staged_publication_state(published, staged, capture)


def test_live_staged_actions_are_unpublished_or_published_exactly_once(staged, capture):
    if not EVENTS.exists():
        pytest.skip(f"event log {EVENTS} is not on this host; live publication state unobserved")
    with EVENTS.open(encoding="utf-8") as log:
        live = [json.loads(line) for line in log if line.strip()]
    assert staged_publication_state(live, staged, capture) in ("unpublished", "published")


# ---------------------------------------------------------------- the build refuses inconsistent declarations

def test_build_refuses_deferring_a_critical_path_item(base, decl, roots):
    bad = copy.deepcopy(decl)
    bad["deferred"]["K9-1"] = {"reason": "x", "re_entry": "y"}
    with pytest.raises(ValueError, match="in the closure"):
        R.build(base, bad, roots)


def test_build_refuses_an_item_without_a_disposition(base, decl, roots):
    bad = copy.deepcopy(decl)
    bad["done_outside"].remove("B-8")
    with pytest.raises(ValueError, match="no declared disposition"):
        R.build(base, bad, roots)


def test_build_refuses_a_retained_item_waiting_on_a_deferred_one(base, decl, roots):
    bad = copy.deepcopy(decl)
    bad["recuts"] = []
    with pytest.raises(ValueError, match="depends on deferred"):
        R.build(base, bad, roots)


def test_build_refuses_a_stale_recut(base, decl, roots):
    bad = copy.deepcopy(decl)
    bad["recuts"][0]["replaces"] = ["J-7"]
    with pytest.raises(ValueError, match="re-cut expects"):
        R.build(base, bad, roots)
