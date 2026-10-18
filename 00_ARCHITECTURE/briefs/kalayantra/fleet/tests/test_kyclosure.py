"""Acceptance-closure tool (relaunch plan v2.2 §0 step 2): edge semantics, skip propagation, refusals and
reproducibility — on synthetic models, then on the committed model, roots and closure."""
import copy
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
CONTROL = REPO / "00_ARCHITECTURE" / "control" / "kalayantra"
sys.path.insert(0, str(FLEET))

import kyclosure  # noqa: E402


def item(iid, deps=(), **extra):
    base = {"id": iid, "depends_on": list(deps), "mandatory": True, "brief": {"spec": [f"spec of {iid}"]},
            "detector": {"type": "file_exists", "path": f"/x/{iid}"}}
    base.update(extra)
    return base


def roots_for(model, mapping, chain=()):
    items = {i["id"]: i for i in model["items"]}
    return {"plan_version": "2.2",
            "acceptances": [{"id": aid, "roots": [{"item": r, "step": None, "brief_spec": items[r]["brief"]["spec"],
                                                   "detector": items[r].get("detector")} for r in rs]}
                            for aid, rs in mapping.items()],
            "mechanical_close_chain": {"items": list(chain)}}


def base_model():
    return {"model_version": "t", "items": [
        item("A"), item("B", ["A"]), item("ROOT", ["B"], steps=["one", "two"]),
        item("D-X", ["A"], done_by="decision", detector=None),
        item("NEEDS", [], requires_outcome={"D-X": "approved"}),
        item("OPT", ["A"], mandatory=False),
        item("EXIT", ["NEEDS", "OPT", "B"], accepts_not_applicable_dependencies=True),
        item("TOP", ["EXIT"]),
        item("HARD", ["NEEDS"]),
        item("LONELY"), item("JOIN-ALL", ["ROOT", "TOP", "LONELY"], done_by="join", join=True),
    ]}


def test_depends_on_supplies_item_edges_and_outside_is_everything_else():
    m = base_model()
    c = kyclosure.compute(m, roots_for(m, {"i": ["ROOT"]}, chain=["JOIN-ALL"]))
    assert c["closure"] == ["A", "B", "ROOT"]
    assert "LONELY" in c["outside"] and "JOIN-ALL" in c["outside"]
    assert c["members"]["B"]["required_by"] == ["ROOT"]
    assert c["mechanical_close_chain_excluded_as_roots"] == ["JOIN-ALL"]


def test_requires_outcome_is_an_explicit_decision_edge_even_without_depends_on():
    m = base_model()
    c = kyclosure.compute(m, roots_for(m, {"i": ["HARD"]}))
    assert "D-X" in c["closure"]
    assert c["members"]["NEEDS"]["prerequisites"] == {"D-X": ["decision"]}


def test_steps_are_obligations_not_items():
    m = base_model()
    c = kyclosure.compute(m, roots_for(m, {"i": ["ROOT"]}))
    assert "one" not in c["closure"] and "two" not in c["closure"]
    m["items"][2]["steps"] = ["A"]
    with pytest.raises(ValueError, match="steps are intra-item obligations"):
        kyclosure.compute(m, roots_for(m, {"i": ["ROOT"]}))


def test_a_skipped_input_absorbed_by_an_accepting_item_is_reported_as_a_gap_on_the_acceptance():
    m = base_model()
    c = kyclosure.compute(m, roots_for(m, {"i": ["TOP"]}))
    gaps = c["acceptances"]["i"]["gap_candidates"]
    assert [(g["absorbed_by"], g["input"]) for g in gaps] == [("EXIT", "NEEDS"), ("EXIT", "OPT")]
    assert gaps[0]["reasons"] == ["decision:D-X=approved"] and gaps[1]["reasons"] == ["optional"]
    assert c["acceptances"]["i"]["skip_capable_roots"] == {}


def test_a_non_accepting_consumer_inherits_the_skip_so_the_root_itself_is_flagged():
    m = base_model()
    c = kyclosure.compute(m, roots_for(m, {"i": ["HARD"]}))
    assert c["acceptances"]["i"]["skip_capable_roots"] == {"HARD": ["input:NEEDS"]}


@pytest.mark.parametrize("mutate, message", [
    (lambda m, r: r["acceptances"][0]["roots"][0].update(item="NOPE"), "no such item"),
    (lambda m, r: r["acceptances"][0]["roots"][0].update(detector={"type": "other"}), "detector citation differs"),
    (lambda m, r: r["acceptances"][0]["roots"][0].update(brief_spec=["elsewhere"]), "brief citation differs"),
    (lambda m, r: r["acceptances"][0]["roots"][0].update(step="three"), "not one of the item's steps"),
    (lambda m, r: m["items"][1]["depends_on"].append("GHOST"), "depends_on names no item"),
    (lambda m, r: m["items"][4].update(requires_outcome={"A": "approved"}), "names no decision item"),
    (lambda m, r: m["items"][0].update(join=True), "disagrees with done_by"),
    (lambda m, r: m["items"].append(copy.deepcopy(m["items"][0])), "duplicate item id"),
    (lambda m, r: r["acceptances"][0].update(roots=[]), "no root item"),
])
def test_refusals(mutate, message):
    m = base_model()
    r = roots_for(m, {"i": ["ROOT"]})
    mutate(m, r)
    with pytest.raises(ValueError, match=message):
        kyclosure.compute(m, r)


def test_formatting_does_not_change_the_hash_and_content_does():
    m = base_model()
    r = roots_for(m, {"i": ["TOP"]})
    first = kyclosure.render(kyclosure.compute(m, r))
    again = kyclosure.render(kyclosure.compute(json.loads(json.dumps(m, indent=7)), json.loads(json.dumps(r))))
    assert first == again
    m["items"][7]["depends_on"].append("LONELY")
    assert kyclosure.render(kyclosure.compute(m, r)) != first


def run(*args):
    return subprocess.run([sys.executable, str(FLEET / "kyclosure.py"), *args], capture_output=True, text=True,
                          timeout=60)


def test_cli_refusal_exits_2_and_check_mismatch_exits_1(tmp_path):
    m = base_model()
    (tmp_path / "m.json").write_text(json.dumps(m))
    (tmp_path / "r.json").write_text(json.dumps(roots_for(m, {"i": ["ROOT"]})))
    assert run("--model", str(tmp_path / "m.json"), "--roots", str(tmp_path / "r.json"),
               "--out", str(tmp_path / "c.json")).returncode == 0
    assert run("--model", str(tmp_path / "m.json"), "--roots", str(tmp_path / "r.json"),
               "--check", str(tmp_path / "c.json")).returncode == 0
    (tmp_path / "c.json").write_text((tmp_path / "c.json").read_text().replace('"ROOT"', '"ROOT2"', 1))
    assert run("--model", str(tmp_path / "m.json"), "--roots", str(tmp_path / "r.json"),
               "--check", str(tmp_path / "c.json")).returncode == 1
    bad = roots_for(m, {"i": ["ROOT"]})
    bad["acceptances"][0]["roots"][0]["item"] = "NOPE"
    (tmp_path / "r.json").write_text(json.dumps(bad))
    refused = run("--model", str(tmp_path / "m.json"), "--roots", str(tmp_path / "r.json"),
                  "--out", str(tmp_path / "c2.json"))
    assert refused.returncode == 2 and "no such item" in refused.stderr and not (tmp_path / "c2.json").exists()


def test_committed_closure_is_reproducible_twice_from_the_committed_model_and_roots(tmp_path):
    # Reproduce the reviewed v2.2 closure, whose live model has since gained bootstrap items.
    raw = gzip.decompress((HERE / "fixtures/reconcile/plan_model.reviewed.json.gz").read_bytes())
    review = json.loads((CONTROL / "TRIAGE_DELTA_REVIEW_v2_2.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == review["inputs"]["model"]
    model, roots = tmp_path / "reviewed-model.json", CONTROL / "ACCEPTANCE_ROOTS_v2_1.json"
    model.write_bytes(raw)
    one, two = tmp_path / "one.json", tmp_path / "two.json"
    assert run("--model", str(model), "--roots", str(roots), "--out", str(one)).returncode == 0
    assert run("--model", str(model), "--roots", str(roots), "--out", str(two)).returncode == 0
    assert one.read_bytes() == two.read_bytes() == (CONTROL / "CLOSURE_v2_1.json").read_bytes()


@pytest.mark.parametrize("name", ["ACCEPTANCE_ROOTS", "CLOSURE"])
def test_compatibility_copies_are_byte_identical_to_the_canonical_files(name):
    # Astra review v2.2 KU-03: the plan's _v2_1 path is canonical; the prompt's _v2_2 path is a copy
    assert (CONTROL / f"{name}_v2_1.json").read_bytes() == (CONTROL / f"{name}_v2_2.json").read_bytes()


def test_the_old_join_and_the_close_chain_are_not_scope_roots():
    roots = json.loads((CONTROL / "ACCEPTANCE_ROOTS_v2_1.json").read_text(encoding="utf-8"))
    closure = json.loads((CONTROL / "CLOSURE_v2_1.json").read_text(encoding="utf-8"))
    rooted = {r["item"] for a in roots["acceptances"] for r in a["roots"]}
    chain = set(roots["mechanical_close_chain"]["items"])
    assert {"JOIN-ALL", "C-1", "C-2", "C-3", "C-4"} <= chain and not (rooted & chain)
    assert not (set(closure["closure"]) & chain)
