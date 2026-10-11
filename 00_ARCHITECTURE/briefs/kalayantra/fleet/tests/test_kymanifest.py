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
    comps = [km.COMPONENT_LIST, km.FLEET + "/cards/BOOTSTRAP.md", km.FLEET + "/schemas/packet.json", km.FLEET + "/kyctl.sh"]
    for rel in comps[1:]:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("component " + rel + "\n")
    (repo / km.COMPONENT_LIST).write_text("# B-0c components\n" + "\n".join(comps) + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "b0c")
    ok = {m: {"sign_in": "works"} for m in km.ROSTER}
    (run / "PROBES.json").write_text(json.dumps({"contexts": {"shell": ok, "launchd": ok}, "extra_lean_flags": {"chosen": []}}))
    review = repo / "review.json"

    def write_review(verdict="ACCEPTED", session="rev-1", drop=None, wrong=None, commit=None):
        inputs = {rel: sha(repo / rel) for rel in comps if rel != drop}
        if wrong:
            inputs[wrong] = "0" * 64
        review.write_text(json.dumps({"verdict": verdict, "reviewer_session_id": session, "inputs": inputs,
                                      "source_commit": commit or approved}))

    def run_cli(*args):
        return subprocess.run([sys.executable, str(FLEET / "kymanifest.py")] + [str(a) for a in args],
                              capture_output=True, text=True)

    def build(out="VERSIONS.bootstrap.json", commit=None):
        return run_cli("build", "--repo", repo, "--run", run, "--approved-commit", commit or approved,
                       "--review", review, "--out", run / out)

    def check(name="VERSIONS.bootstrap.json"):
        return run_cli("check", "--repo", repo, "--run", run, run / name)

    write_review()
    return type("Rig", (), dict(repo=repo, run=run, approved=approved, comps=comps, review=review,
                                write_review=staticmethod(write_review), build=staticmethod(build),
                                check=staticmethod(check), cli=staticmethod(run_cli), commit=staticmethod(lambda m: (git(repo, "add", "-A"), git(repo, "commit", "-qm", m)))))


def test_build_is_deterministic_and_check_passes(rig):
    assert rig.build().returncode == 0
    assert rig.build("second.json").returncode == 0
    a, b = (rig.run / "VERSIONS.bootstrap.json").read_bytes(), (rig.run / "second.json").read_bytes()
    assert a == b
    m = json.loads(a)
    assert m["mode"] == "bootstrap" and m["approved_source_commit"] == rig.approved
    assert set(m["entrypoints"]) == {"plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent"}
    assert m["qualifications"] == [] and m["qualifications_all_pass"] is False  # none recorded → never "all pass"
    assert [c["path"] for c in m["components"]] == sorted(rig.comps)
    assert {p["role"] for p in m["generated_pairs"]} == {"WORKTREE_DISPOSITIONS", "ACCEPTANCE_ROOTS", "CLOSURE"}
    assert m["probes"]["sign_in_works_launchd"] is True
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


def test_check_fails_after_any_drift(rig):
    assert rig.build().returncode == 0
    (rig.repo / rig.comps[1]).write_text("edited after review\n")
    r = rig.check()
    assert r.returncode == 1 and "differs from HEAD" in r.stderr
    rig.commit("sneak the edit in")
    r = rig.check()
    assert r.returncode == 1 and "review does not cover" in r.stderr


def test_check_fails_on_tampered_manifest_or_changed_probes(rig):
    assert rig.build().returncode == 0
    path = rig.run / "VERSIONS.bootstrap.json"
    m = json.loads(path.read_text())
    m["probes"]["sign_in_works_launchd"] = False
    path.write_text(json.dumps(m))
    assert rig.check().returncode == 1
    assert rig.build().returncode == 0
    (rig.run / "PROBES.json").write_text(json.dumps({"contexts": {"shell": "unknown", "launchd": "unknown"}}))
    r = rig.check()
    assert r.returncode == 1 and "probes" in r.stderr


def test_qualification_results_are_recorded_and_never_upgraded(rig):
    q = rig.run / "QUALIFICATIONS"
    q.mkdir()
    (q / "bootstrap-claude-opus-5-5.json").write_text(json.dumps({"result": "PASS"}))
    assert rig.build().returncode == 0
    assert json.loads((rig.run / "VERSIONS.bootstrap.json").read_text())["qualifications_all_pass"] is True
    (q / "planner-claude-opus-5-5.json").write_text(json.dumps({"result": "maybe"}))
    r = rig.check()
    assert r.returncode == 1 and "qualifications" in r.stderr
    assert rig.build().returncode == 0
    m = json.loads((rig.run / "VERSIONS.bootstrap.json").read_text())
    assert m["qualifications_all_pass"] is False and [x["result"] for x in m["qualifications"]] == ["PASS", "unknown"]


def test_probe_failure_is_recorded_not_hidden(rig):
    (rig.run / "PROBES.json").write_text(json.dumps({"contexts": {
        "shell": {m: {"sign_in": "works"} for m in km.ROSTER}, "launchd": {m: {"sign_in": "fails"} for m in km.ROSTER}}}))
    assert rig.build().returncode == 0
    m = json.loads((rig.run / "VERSIONS.bootstrap.json").read_text())
    assert m["probes"]["sign_in_works_shell"] is True and m["probes"]["sign_in_works_launchd"] is False


@pytest.mark.parametrize("breaker, reason", [
    (lambda r: (r.repo / km.PAIRS[1][2]).write_text("edited independently\n"), "copies differ"),
    (lambda r: (r.repo / km.PAIRS[2][2]).unlink(), "copy missing"),
    (lambda r: (r.repo / km.BUNDLE[0]).write_text("plan edited\n"), "differs from the approved commit"),
    (lambda r: (r.repo / km.FLEET / "cards" / "EXTRA.md").write_text("unlisted\n"), "unlisted file"),
    (lambda r: (r.repo / r.comps[2]).write_text("uncommitted edit\n"), "differs from HEAD"),
    (lambda r: (r.run / "PROBES.json").unlink(), "probes not recorded"),
    (lambda r: r.write_review(verdict="REJECTED"), "not ACCEPTED"),
    (lambda r: r.write_review(session=""), "no reviewer session"),
    (lambda r: r.write_review(drop=r.comps[3]), "review does not cover"),
    (lambda r: r.write_review(wrong=r.comps[1]), "review does not cover"),
    (lambda r: r.review.unlink(), "review record missing"),
    (lambda r: r.write_review(commit="0" * 40), "not bound to the authorised source commit"),
    (lambda r: (r.repo / km.ENTRYPOINTS["surrogate_agent"]).write_text("agent edited\n"), "differs from the approved commit"),
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
    assert "not committed" in rig.build().stderr or "differs from HEAD" in rig.build().stderr


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
