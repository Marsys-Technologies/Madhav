"""B-0c: the bootstrap manifest only records what it can re-observe; KU clauses stay verbatim."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
REPO = FLEET.parents[3]
sys.path.insert(0, str(FLEET))
import kymanifest as km  # noqa: E402

# A stand-in for the reviewed harness: `check <receipt> --config <cfg> --require-context launchd`
# exits 0 unless a file `<receipt>.reject` exists beside the receipt.
HARNESS_STUB = '''import os, sys
a = sys.argv[1:]
ok = a[:1] == ["check"] and "--config" in a and a[a.index("--require-context") + 1] == "launchd"
sys.exit(0 if ok and not os.path.exists(a[1] + ".reject") else 1)
'''


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c",
                           "commit.gpgsign=false"] + list(args), capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture()
def rig(tmp_path):
    repo, run = tmp_path / "repo", tmp_path / "run"
    repo.mkdir()
    run.mkdir()
    git(repo, "init", "-q")
    for rel in km.BUNDLE:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("bundle " + rel + "\n")
    for _role, canon, compat in km.PAIRS:
        for rel in (canon, compat):
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text("generated " + _role + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "approved bundle")
    approved = git(repo, "rev-parse", "HEAD")
    comps = [km.COMPONENT_LIST, km.FLEET + "/cards/BOOTSTRAP.md", km.FLEET + "/schemas/packet.json", km.FLEET + "/kyctl.sh",
             km.HARNESS, km.LAUNCH_CONFIG % "bootstrap-builder"]
    for rel in comps[1:]:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(HARNESS_STUB if rel == km.HARNESS else "component " + rel + "\n")
    (repo / km.COMPONENT_LIST).write_text("# B-0c components\n" + "\n".join(comps) + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "b0c")
    ok = {m: {"sign_in": "works"} for m in km.ROSTER}
    (run / "PROBES.json").write_text(json.dumps({"contexts": {"shell": ok, "launchd": ok}, "extra_lean_flags": {"chosen": []}}))
    (run / "QUALIFICATIONS").mkdir()
    receipt = run / "QUALIFICATIONS" / "bootstrap-builder-claude-opus-5-5.json"
    receipt.write_text(json.dumps({"result": "PASS", "role": "bootstrap-builder", "model": "claude-opus-5-5", "context": "launchd"}))
    (run / "reviews").mkdir()
    review = repo / "review.json"

    def write_review(verdict="ACCEPTED", session="acceptor-1", drop=None, wrong=None, commit=None, areas="default",
                     area_verdict="ACCEPTED", area_sessions=("rev-a", "rev-b"), area_drop=None, top_inputs=True):
        inputs = {rel: sha(repo / rel) for rel in comps if rel != drop}
        if wrong:
            inputs[wrong] = "0" * 64
        entries = []
        if areas == "default":
            halves = [comps[:3], comps[3:]]
            for i, (name, files) in enumerate(zip(("one", "two"), halves)):
                rec = run / "reviews" / (name + ".review.json")
                rec.write_text(json.dumps({"area": name, "reviewer_session_id": area_sessions[i],
                                           "inputs": {rel: sha(repo / rel) for rel in files if rel != area_drop},
                                           "review": {"verdict": area_verdict if i == 1 else "ACCEPTED"}}))
                entries.append({"area": name, "record": str(rec), "record_sha256": sha(rec)})
        doc = {"verdict": verdict, "reviewer_session_id": session, "source_commit": commit or approved,
               "inputs": inputs if top_inputs else {}}
        if areas is not None:
            doc["area_reviews"] = entries
        review.write_text(json.dumps(doc))

    def run_cli(*args):
        return subprocess.run([sys.executable, str(FLEET / "kymanifest.py")] + [str(a) for a in args],
                              capture_output=True, text=True)

    def build(out="VERSIONS.bootstrap.json", commit=None):
        return run_cli("build", "--repo", repo, "--run", run, "--approved-commit", commit or approved,
                       "--review", review, "--out", run / out)

    def check(name="VERSIONS.bootstrap.json"):
        return run_cli("check", "--repo", repo, "--run", run, run / name)

    write_review()
    return type("Rig", (), dict(repo=repo, run=run, approved=approved, comps=comps, review=review, receipt=receipt,
                                write_review=staticmethod(write_review), build=staticmethod(build),
                                check=staticmethod(check), cli=staticmethod(run_cli),
                                commit=staticmethod(lambda m: (git(repo, "add", "-A"), git(repo, "commit", "-qm", m)))))


def test_build_is_deterministic_and_check_passes(rig):
    assert rig.build().returncode == 0, rig.build().stderr
    assert rig.build("second.json").returncode == 0
    a, b = (rig.run / "VERSIONS.bootstrap.json").read_bytes(), (rig.run / "second.json").read_bytes()
    assert a == b
    m = json.loads(a)
    assert m["mode"] == "bootstrap" and m["approved_source_commit"] == rig.approved
    assert set(m["entrypoints"]) == {"plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent"}
    assert [c["path"] for c in m["components"]] == sorted(rig.comps)
    assert {p["role"] for p in m["generated_pairs"]} == {"WORKTREE_DISPOSITIONS", "ACCEPTANCE_ROOTS", "CLOSURE"}
    assert [q["result"] for q in m["qualifications"]] == ["PASS"] and m["qualifications"][0]["context"] == "launchd"
    assert [r["area"] for r in m["review"]["area_reviews"]] == ["one", "two"]
    assert rig.check().returncode == 0


def test_deferred_files_are_listed_and_pinned_but_neither_bound_nor_reviewed(rig):
    later = km.FLEET + "/prompts/LOOP.md"
    (rig.repo / later).parent.mkdir(parents=True, exist_ok=True)
    (rig.repo / later).write_text("a loop prompt whose review is still running\n")
    assert "unlisted file" in rig.build().stderr                              # in a covered directory, not listed
    (rig.repo / km.COMPONENT_LIST).write_text("\n".join(rig.comps) + "\n# tranche: deferred\n" + later + "\n")
    assert "differs from the components commit" in rig.build().stderr or "not committed" in rig.build().stderr
    rig.commit("list the deferred file")
    rig.write_review()                                                        # the review does NOT cover the deferred file
    assert rig.build().returncode == 0, rig.build().stderr
    m = json.loads((rig.run / "VERSIONS.bootstrap.json").read_text())
    assert later not in [c["path"] for c in m["components"]]
    assert [c["path"] for c in m["deferred_components"]] == [later] and "NOT reviewed" in m["deferred_note"]
    (rig.repo / later).write_text("edited after the manifest\n")
    r = rig.check()
    assert r.returncode == 1 and "differs from the components commit" in r.stderr   # deferred, yet pinned
    # a receipt whose launch configuration is only a deferred component cannot be recorded
    cfg = km.LAUNCH_CONFIG % "bootstrap-builder"
    (rig.repo / later).write_text("a loop prompt whose review is still running\n")
    (rig.repo / km.COMPONENT_LIST).write_text("\n".join(c for c in rig.comps if c != cfg) + "\n# tranche: deferred\n" + later + "\n" + cfg + "\n")
    rig.commit("defer the launch configuration")
    assert "not a bound component" in rig.build().stderr
    (rig.repo / km.COMPONENT_LIST).write_text("# tranche: later\n" + "\n".join(rig.comps) + "\n")
    assert "unknown tranche marker" in rig.build().stderr
    (rig.repo / km.COMPONENT_LIST).write_text("# tranche: deferred\n" + "\n".join(rig.comps) + "\n")
    assert "must list itself among the bound" in rig.build().stderr


def test_a_later_commit_that_leaves_the_components_alone_keeps_the_manifest_valid(rig):
    assert rig.build().returncode == 0
    (rig.repo / "unrelated.txt").write_text("the review receipt, a note, anything outside the components\n")
    rig.commit("later commit")
    assert rig.check().returncode == 0


def test_entrypoints_binding_is_stable_and_changes_with_any_bound_blob(rig):
    r = rig.cli("entrypoints", "--repo", rig.repo, "--commit", rig.approved)
    assert r.returncode == 0, r.stderr
    b = json.loads(r.stdout)
    assert set(b["entrypoints"]) == set(km.ENTRYPOINTS) and len(b["entrypoints_digest"]) == 64
    assert rig.build().returncode == 0
    assert json.loads((rig.run / "VERSIONS.bootstrap.json").read_text())["entrypoints_digest"] == b["entrypoints_digest"]
    assert rig.cli("entrypoints", "--repo", rig.repo, "--commit", rig.approved[:10]).returncode == 1
    (rig.repo / km.ENTRYPOINTS["plan"]).write_text("a later plan\n")
    assert "differs from the approved commit" in rig.cli("entrypoints", "--repo", rig.repo, "--commit", rig.approved).stderr
    rig.commit("successor bundle")
    head = subprocess.run(["git", "-C", str(rig.repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    later = json.loads(rig.cli("entrypoints", "--repo", rig.repo, "--commit", head).stdout)
    assert later["entrypoints_digest"] != b["entrypoints_digest"]


def test_byte_identity_is_not_fooled_by_index_flags(rig):
    rel = rig.comps[1]
    git(rig.repo, "update-index", "--assume-unchanged", rel)
    (rig.repo / rel).write_text("edited behind an assume-unchanged flag\n")
    assert subprocess.run(["git", "-C", str(rig.repo), "diff", "--quiet", "HEAD", "--", rel]).returncode == 0  # git diff is blind
    r = rig.build()
    assert r.returncode == 1 and "differs from the components commit" in r.stderr


def test_check_fails_after_any_drift(rig):
    assert rig.build().returncode == 0
    (rig.repo / rig.comps[1]).write_text("edited after review\n")
    r = rig.check()
    assert r.returncode == 1 and "differs from the components commit" in r.stderr
    rig.commit("sneak the edit in")
    r = rig.check()
    assert r.returncode == 1 and "differs from the components commit" in r.stderr  # still bound to the reviewed commit


def test_check_fails_on_tampered_manifest_changed_probes_or_a_changed_area_record(rig):
    assert rig.build().returncode == 0
    path = rig.run / "VERSIONS.bootstrap.json"
    m = json.loads(path.read_text())
    m["qualifications_all_pass"] = False
    path.write_text(json.dumps(m))
    assert rig.check().returncode == 1
    assert rig.build().returncode == 0
    rec = rig.run / "reviews" / "two.review.json"
    doc = json.loads(rec.read_text())
    doc["review"]["verdict"] = "REJECTED"
    rec.write_text(json.dumps(doc))
    r = rig.check()
    assert r.returncode == 1 and "per-area review record missing or changed" in r.stderr
    rig.write_review()
    assert rig.build().returncode == 0
    (rig.run / "PROBES.json").write_text(json.dumps({"contexts": {"shell": "unknown", "launchd": "unknown"}}))
    r = rig.check()
    assert r.returncode == 1 and "sign-in" in r.stderr


def test_a_receipt_the_harness_rejects_or_that_is_not_pass_blocks_the_manifest(rig):
    Path(str(rig.receipt) + ".reject").write_text("x")
    r = rig.build()
    assert r.returncode == 1 and "harness does not accept" in r.stderr
    Path(str(rig.receipt) + ".reject").unlink()
    assert rig.build().returncode == 0
    (rig.run / "QUALIFICATIONS" / "planner-claude-opus-5-5.json").write_text(json.dumps({"result": "unknown", "role": "planner"}))
    r = rig.check()
    assert r.returncode == 1 and "not PASS" in r.stderr
    (rig.run / "QUALIFICATIONS" / "planner-claude-opus-5-5.json").write_text(json.dumps({"result": "PASS", "role": "planner"}))
    assert "no launch configuration" in rig.build().stderr


@pytest.mark.parametrize("breaker, reason", [
    (lambda r: (r.repo / km.PAIRS[1][2]).write_text("edited independently\n"), "copies differ"),
    (lambda r: (r.repo / km.PAIRS[2][2]).unlink(), "copy missing"),
    (lambda r: (r.repo / km.BUNDLE[0]).write_text("plan edited\n"), "differs from the approved commit"),
    (lambda r: (r.repo / km.ENTRYPOINTS["surrogate_agent"]).write_text("agent edited\n"), "differs from the approved commit"),
    (lambda r: (r.repo / km.FLEET / "cards" / "EXTRA.md").write_text("unlisted\n"), "unlisted file"),
    (lambda r: (r.repo / r.comps[2]).write_text("uncommitted edit\n"), "differs from the components commit"),
    (lambda r: (r.run / "PROBES.json").unlink(), "probes not recorded"),
    (lambda r: (r.run / "PROBES.json").write_text(json.dumps({"contexts": {
        "shell": {m: {"sign_in": "works"} for m in km.ROSTER}, "launchd": {m: {"sign_in": "fails"} for m in km.ROSTER}}})),
     "sign-in working for every roster model in the launchd context"),
    (lambda r: r.receipt.unlink(), "no launch-qualification receipt"),
    (lambda r: r.receipt.write_text(json.dumps({"result": "FAIL", "role": "bootstrap-builder"})), "not PASS"),
    (lambda r: r.write_review(verdict="REJECTED"), "not ACCEPTED"),
    (lambda r: r.write_review(session=""), "no reviewer session"),
    (lambda r: r.write_review(drop=r.comps[3]), "review does not cover"),
    (lambda r: r.write_review(wrong=r.comps[1]), "review does not cover"),
    (lambda r: r.write_review(commit="0" * 40), "not bound to the authorised source commit"),
    (lambda r: r.review.unlink(), "review record missing"),
    (lambda r: r.write_review(areas=None), "no per-area review records"),
    (lambda r: r.write_review(area_verdict="REJECTED"), "per-area review is not ACCEPTED"),
    (lambda r: r.write_review(area_sessions=("rev-a", "rev-a")), "signs twice"),
    (lambda r: r.write_review(area_sessions=("rev-a", "acceptor-1")), "signs twice"),
    (lambda r: r.write_review(area_sessions=("rev-a", "")), "names no reviewer session"),
    (lambda r: r.write_review(area_drop=r.comps[4]), "no ACCEPTED per-area review covers"),
    (lambda r: (r.write_review(), (r.run / "reviews" / "one.review.json").unlink()), "per-area review record missing or changed"),
])
def test_build_refuses(rig, breaker, reason):
    breaker(rig)
    r = rig.build()
    assert r.returncode == 1 and reason in r.stderr, r.stderr
    assert not (rig.run / "VERSIONS.bootstrap.json").exists()


def test_build_refuses_short_or_unknown_commit_and_untracked_component(rig):
    assert "full 40-hex" in rig.build(commit=rig.approved[:12]).stderr
    assert "not found" in rig.build(commit="f" * 40).stderr
    new = km.FLEET + "/kynew.sh"
    (rig.repo / new).write_text("x\n")
    (rig.repo / km.COMPONENT_LIST).write_text("\n".join(rig.comps + [new]) + "\n")
    assert "not committed" in rig.build().stderr or "differs from the components commit" in rig.build().stderr


# --- the real tree -------------------------------------------------------------------

def test_ku_clauses_are_verbatim_from_the_review():
    bind = json.loads((FLEET / "templates" / "ku_bindings.json").read_text())
    review = (REPO / bind["source"]["path"]).read_text(encoding="utf-8")
    assert hashlib.sha256(review.encode()).hexdigest() == bind["source"]["sha256"]
    md = (FLEET / "templates" / "KU_REPLACEMENTS_v2_7.md").read_text(encoding="utf-8")
    flat = lambda s: " ".join(s.replace(">", " ").split())  # noqa: E731
    assert set(bind["clauses"]) == {"KU-01", "KU-02", "KU-03"}
    for ku, c in bind["clauses"].items():
        assert hashlib.sha256(c["text"].encode()).hexdigest() == c["text_sha256"]
        assert flat(c["text"]) in flat(review), ku + " is not verbatim in the review"
        assert flat(c["text"]) in flat(md), ku + " is missing from the template"
        assert c["required_in"], ku + " binds no packet"


def test_every_file_in_a_covered_directory_is_listed():
    listed = set(km.read_components(str(REPO)))
    for d in km.COVERED_DIRS:
        for p in (REPO / d).rglob("*"):
            if p.is_file() and not p.name.startswith(".") and "__pycache__" not in p.parts:
                assert str(p.relative_to(REPO)) in listed, "unlisted: %s" % p.relative_to(REPO)
    for rel in listed:
        assert (REPO / rel).is_file(), "listed but missing: " + rel
