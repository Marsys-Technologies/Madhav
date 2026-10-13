"""KV3-B-KYVERSION: kyversion.sh says OK only for checks that ran in that call; each check refuses alone.

Every test builds its own KY_RUN, KY_FLEET and git repository under tmp_path. kymanifest.py is a recording
double (its argv, working directory and environment are asserted); the activation-chain verdicts are also
compared with kyloop.py's own `activation_chain`, whose rules kyversion.sh follows."""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "kyversion.sh"
sys.path.insert(0, str(FLEET))
import kyloop  # noqa: E402
import kymanifest as km  # noqa: E402

REFUSED = re.compile(r"^kyversion: REFUSED ([A-Z][0-9]): \S.*$")
PAIR_ROLES = [role for role, _canon, _compat in km.PAIRS]
C0, C1, C2, C3 = "a" * 40, "b" * 40, "c" * 40, "d" * 40
OTHER = "e" * 64
DEFAULT_ROOT = "/Users/Dev/kalayantra"
DEFAULT_SOURCE_REPO = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"

# The stand-in for the reviewed kymanifest.py. It records how it was started and then answers as
# <double>/behave.json says; by default as the real `check` does: {"ok": true, "manifest_sha256": the file's own}.
DOUBLE = '''import json, os, sys
call = {"argv": sys.argv[1:], "cwd": os.getcwd(), "isolated": sys.flags.isolated,
        "dont_write_bytecode": sys.flags.dont_write_bytecode,
        "leaked": sorted(k for k in os.environ if k.startswith(("GIT_", "PYTHON")))}
with open(%(log)r, "a") as f:
    f.write(json.dumps(call) + "\\n")
how = json.load(open(%(behave)r)) if os.path.exists(%(behave)r) else {}
if "stdout" in how:
    sys.stdout.write(how["stdout"])
else:
    try:
        own = json.load(open(sys.argv[2])).get("manifest_sha256")
    except (OSError, ValueError, IndexError, AttributeError):
        own = None
    print(json.dumps({"ok": True, "manifest_sha256": own, "components": 3}))
sys.exit(how.get("exit", 0))
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def with_digest(body):
    body = {k: v for k, v in body.items() if k != "manifest_sha256"}
    return dict(body, manifest_sha256=hashlib.sha256(km.canonical(body)).hexdigest())


def read(path):
    return json.loads(Path(path).read_text())


def write(path, doc):
    Path(path).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")


class Rig:
    def __init__(self, tmp):
        self.tmp, self.root, self.repo, self.double = tmp, tmp / "ky", tmp / "repo", tmp / "double"
        self.run, self.fleet = self.root / "run", self.root / "fleet_live"
        for d in (self.run, self.fleet, self.repo, self.double, self.root / "evidence"):
            d.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.fleet / "kyversion.sh")
        self.log, self.behave = self.double / "calls.jsonl", self.double / "behave.json"
        (self.fleet / "kymanifest.py").write_text(DOUBLE % {"log": str(self.log), "behave": str(self.behave)})
        subprocess.run(["git", "-C", str(self.repo), "init", "-q"], check=True, capture_output=True)
        self.components, self.installed = [], []
        for rel in (km.FLEET + "/kyctl.sh", km.FLEET + "/kyloop.py", km.FLEET + "/cards/BOOTSTRAP.md"):
            target = self.root / "installed" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("component " + rel + "\n")
            self.components.append({"path": rel, "sha256": sha(target)})
            self.installed.append({"path": rel, "installed_path": str(target), "sha256": sha(target)})
        self.pairs = []
        for role, canon, compat in km.PAIRS:
            for rel in (canon, compat):
                (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (self.repo / rel).write_text("generated " + role + "\n")
            self.pairs.append({"role": role, "canonical": canon, "compatibility": compat,
                               "canonical_abs": str(self.repo / canon), "compatibility_abs": str(self.repo / compat),
                               "sha256": sha(self.repo / canon), "content_version_declared": "2.2"})

    # ---- the installation under test
    def manifest_body(self, mode):
        return {"schema": "ky.versions_bootstrap/1" if mode == "bootstrap" else "ky.versions/1", "mode": mode,
                "plan_version": "2.7", "approved_source_commit": C0,
                "entrypoints": {role: {"path": rel, "sha256": "1" * 64, "git_blob": "2" * 40}
                                for role, rel in km.ENTRYPOINTS.items()},
                "components": copy.deepcopy(self.components), "generated_pairs": copy.deepcopy(self.pairs)}

    def evidence(self, name):
        path = self.root / "evidence" / name
        path.write_text("evidence " + name + "\n")
        return {"path": str(path), "sha256": sha(path)}

    def install(self, mode):
        """A complete, valid installation of that mode; → its manifest digest."""
        self.manifest_path = self.run / ("VERSIONS.bootstrap.json" if mode == "bootstrap" else "VERSIONS.json")
        manifest = with_digest(self.manifest_body(mode))
        write(self.manifest_path, manifest)
        receipt = {"schema": "ky.install_receipt/1", "mode": mode,
                   "manifest": {"path": str(self.manifest_path), "manifest_sha256": manifest["manifest_sha256"]},
                   "components": copy.deepcopy(self.installed)}
        receipt["qualifications"] = []
        for role in ("planner", "conductor"):
            path = self.run / (role + ".json")
            write(path, {"role": role, "model": "claude-opus-5-5", "result": "PASS"})
            receipt["qualifications"].append({"role": role, "model": "claude-opus-5-5", "receipt": str(path),
                                              "receipt_sha256": sha(path), "result": "PASS"})
        if mode == "final":
            receipt.update({
                "tracker_revision": "f" * 40,
                "rehearsal": {"tested_components": copy.deepcopy(self.components),
                              "results": self.evidence("REHEARSAL_RESULTS.json")},
                "coverage": dict(self.evidence("COVERAGE.json"), verdict="ACCEPTED"),
                "packets": [self.evidence("PACKET_A.md"), self.evidence("PACKET_B.md")],
                "backfill": dict(self.evidence("BACKFILL.json"), validated=True)})
        write(self.run / "INSTALL_RECEIPT.json", receipt)
        return manifest["manifest_sha256"]

    def edit_receipt(self, change):
        doc = read(self.run / "INSTALL_RECEIPT.json")
        change(doc)
        write(self.run / "INSTALL_RECEIPT.json", doc)

    def edit_manifest(self, change, rebind=True):
        """Change the manifest and give it a true digest again; the receipt follows unless rebind=False."""
        doc = read(self.manifest_path)
        change(doc)
        doc = with_digest(doc)
        write(self.manifest_path, doc)
        if rebind:
            self.edit_receipt(lambda r: r["manifest"].update(manifest_sha256=doc["manifest_sha256"]))
        return doc["manifest_sha256"]

    # ---- the script
    def env(self, **extra):
        env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": str(self.tmp), "KY_ROOT": str(self.root),
               "KY_RUN": str(self.run), "KY_FLEET": str(self.fleet), "KY_SOURCE_REPO": str(self.repo),
               "TMPDIR": str(self.tmp / "no-such-tmpdir")}      # nothing may need a temporary file
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def kyversion(self, *args, **extra):
        """kyloop.py `run_helper`'s call form."""
        return subprocess.run(["/bin/bash", str(self.fleet / "kyversion.sh"), *args], capture_output=True, text=True,
                              timeout=300, env=self.env(**extra), cwd=str(self.tmp))

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    # ---- activation records
    def root_link(self, digest, commit=C0, **more):
        doc = {"final_manifest_digest": digest}
        if commit is not None:
            doc["source_commit"] = commit
        doc.update(more)
        write(self.run / "ACTIVATION_RECORD.json", doc)

    def link(self, n, old, new, previous="auto", **more):
        """Link n: old/new are (commit, manifest digest); previous defaults to the true predecessor file."""
        if previous == "auto":
            before = self.run / ("ACTIVATION_RECORD.json" if n == 1 else "ACTIVATION_RECORD.%d.json" % (n - 1))
            previous = {"file": before.name, "sha256": sha(before)}
        doc = {"n": more.pop("number", n), "old_commit": old[0], "old_manifest_digest": old[1], "new_commit": new[0],
               "new_manifest_digest": new[1], "previous": previous}
        doc.update(more)
        write(self.run / ("ACTIVATION_RECORD.%d.json" % n), doc)


@pytest.fixture()
def rig(tmp_path):
    return Rig(tmp_path)


def codes(result):
    """The refusal codes on stderr, in order; every stderr line must be a refusal line."""
    lines = result.stderr.splitlines()
    assert lines and all(REFUSED.match(line) for line in lines), result.stderr
    return [REFUSED.match(line).group(1) for line in lines]


def assert_ok(result, mode, digest):
    tail = " tracker_revision=recorded" if mode == "final" else ""
    authorises = "bootstrap-only" if mode == "bootstrap" else "final-bundle"
    assert (result.returncode, result.stderr) == (0, ""), result.stderr
    assert result.stdout == "kyversion: OK mode=%s manifest_sha256=%s authorises=%s%s\n" % (mode, digest, authorises, tail)


def argv(args, digest):
    """["D"] in a parameter list stands for the expected-digest mode with the installed manifest's digest."""
    return ["--expected-manifest-digest", digest] if args == ["D"] else args


def assert_refused(result, *expected):
    """Exit 1, nothing on stdout, exactly one stderr line per failed check — and no other check failed."""
    assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
    assert result.stdout == ""
    assert codes(result) == list(expected), result.stderr


# ------------------------------------------------------------------ the file itself

def test_the_script_is_an_executable_bin_bash_script_that_parses_under_bash_3_2():
    assert SCRIPT.read_text().splitlines()[0] == "#!/bin/bash"
    rel = str(SCRIPT.relative_to(REPO))
    index = subprocess.run(["git", "-C", str(REPO), "ls-files", "-s", "--", rel], capture_output=True, text=True).stdout
    assert index.startswith("100755 "), "git mode of %s: %r" % (rel, index)
    assert subprocess.run(["/bin/bash", "-n", str(SCRIPT)], capture_output=True).returncode == 0
    version = subprocess.run(["/bin/bash", "-c", "echo $BASH_VERSION"], capture_output=True, text=True).stdout
    assert version.startswith("3.2"), "these tests are the bash 3.2 proof; /bin/bash is %s" % version


# ------------------------------------------------------------------ one passing run per mode

def test_bootstrap_mode_passes_on_a_valid_bootstrap_installation(rig):
    digest = rig.install("bootstrap")
    result = rig.kyversion("--bootstrap", GIT_DIR=str(rig.tmp / "elsewhere"), PYTHONPATH=str(rig.tmp / "planted"))
    assert_ok(result, "bootstrap", digest)
    assert rig.calls() == [{"argv": ["check", str(rig.run / "VERSIONS.bootstrap.json"), "--repo", str(rig.repo),
                                     "--run", str(rig.run)],
                            "cwd": "/", "isolated": 1, "dont_write_bytecode": 1, "leaked": []}]


def test_normal_mode_passes_on_a_valid_final_installation_and_never_asks_kymanifest(rig):
    digest = rig.install("final")
    assert_ok(rig.kyversion(), "final", digest)
    assert rig.calls() == []


def test_expected_digest_mode_passes_when_the_manifest_and_the_terminal_link_carry_it(rig):
    digest = rig.install("final")
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, digest))
    assert_ok(rig.kyversion("--expected-manifest-digest", digest), "final", digest)
    assert rig.calls() == []


def test_bootstrap_mode_reads_no_final_manifest(rig):
    digest = rig.install("bootstrap")
    (rig.run / "VERSIONS.json").write_text("{ not json")
    assert_ok(rig.kyversion("--bootstrap"), "bootstrap", digest)


def test_normal_mode_reads_no_bootstrap_manifest(rig):
    digest = rig.install("final")
    (rig.run / "VERSIONS.bootstrap.json").write_text("{ not json")
    assert_ok(rig.kyversion(), "final", digest)


@pytest.mark.parametrize("mode,args", [("bootstrap", ["--bootstrap"]), ("final", []), ("final", ["D"])])
def test_a_valid_chain_passes_the_structure_check_of_every_mode(rig, mode, args):
    digest = rig.install(mode)
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, "9" * 64))
    rig.link(2, (C1, "9" * 64), (C2, digest))
    assert_ok(rig.kyversion(*argv(args, digest)), mode, digest)


@pytest.mark.parametrize("mode,args", [("bootstrap", ["--bootstrap"]), ("final", []), ("final", ["D"])])
def test_it_writes_nothing_and_needs_no_temporary_file(rig, mode, args):
    digest = rig.install(mode)
    rig.root_link(digest, C0)

    def snapshot():
        seen = {}
        for base in (rig.root, rig.repo):
            for path in sorted(base.rglob("*")):
                st = path.lstat()
                seen[str(path)] = (st.st_mode, st.st_size, st.st_mtime_ns, sha(path) if path.is_file() else None)
        return seen

    before = snapshot()
    args = argv(args, digest)
    assert_ok(rig.kyversion(*args), mode, digest)
    rig.edit_receipt(lambda r: r.update(mode="other"))
    before_refusal = snapshot()
    assert rig.kyversion(*args).returncode == 1
    assert snapshot() == before_refusal
    assert {k: v for k, v in before.items() if not k.endswith("INSTALL_RECEIPT.json")} \
        == {k: v for k, v in before_refusal.items() if not k.endswith("INSTALL_RECEIPT.json")}
    assert not (rig.tmp / "no-such-tmpdir").exists() and not list(rig.tmp.rglob("__pycache__"))


# ------------------------------------------------------------------ usage: anything else is 64

@pytest.mark.parametrize("args", [
    ["--bootstrap", "--expected-manifest-digest", "D"],             # both options at once
    ["--expected-manifest-digest", "D", "--bootstrap"],
    ["--bootstrap", "--bootstrap"],
    ["--expected-manifest-digest"],
    ["--expected-manifest-digest", ""],
    ["--expected-manifest-digest", "UPPER"],
    ["--expected-manifest-digest", "SHORT"],
    ["--expected-manifest-digest", "NEWLINE"],
    ["--expected-manifest-digest=D"],
    ["--final"], ["bootstrap"], ["D"], [""], ["--help"]])
@pytest.mark.parametrize("mode", ["bootstrap", "final"])
def test_any_other_usage_exits_64_and_checks_nothing(rig, mode, args):
    digest = rig.install(mode)
    rig.root_link(digest, C0)
    forms = {"D": digest, "UPPER": digest.upper().replace("0", "A")[:63] + "A", "SHORT": digest[:63],
             "NEWLINE": digest + "\n", "--expected-manifest-digest=D": "--expected-manifest-digest=" + digest}
    result = rig.kyversion(*[forms.get(a, a) for a in args])
    assert result.returncode == 64, (result.stdout, result.stderr)
    assert result.stdout == "" and "usage: kyversion.sh" in result.stderr and "REFUSED" not in result.stderr
    assert rig.calls() == []


# ------------------------------------------------------------------ environment

def test_ky_fleet_defaults_to_the_scripts_directory_and_ky_run_to_ky_root_run(rig):
    digest = rig.install("bootstrap")
    assert_ok(rig.kyversion("--bootstrap", KY_FLEET=None, KY_RUN=None), "bootstrap", digest)
    assert rig.calls()[0]["argv"] == ["check", str(rig.run / "VERSIONS.bootstrap.json"), "--repo", str(rig.repo),
                                      "--run", str(rig.run)]


def test_ky_root_and_ky_source_repo_default_as_kyctl_sh(rig):
    # Only the paths handed to the double are asserted: what those real directories hold is not this test's.
    rig.kyversion("--bootstrap", KY_ROOT=None, KY_RUN=None, KY_SOURCE_REPO=None)
    run = DEFAULT_ROOT + "/run"
    assert rig.calls()[0]["argv"] == ["check", run + "/VERSIONS.bootstrap.json", "--repo", DEFAULT_SOURCE_REPO,
                                      "--run", run]
    kyctl = (FLEET / "kyctl.sh").read_text()
    assert 'KY_ROOT="${KY_ROOT:-%s}"' % DEFAULT_ROOT in kyctl
    assert 'KY_SOURCE_REPO="${KY_SOURCE_REPO:-%s}"' % DEFAULT_SOURCE_REPO in kyctl


@pytest.mark.parametrize("name", ["KY_RUN", "KY_FLEET", "KY_SOURCE_REPO"])
@pytest.mark.parametrize("mode,arg", [("bootstrap", ["--bootstrap"]), ("final", [])])
def test_a_path_that_is_not_absolute_refuses_before_any_check(rig, mode, arg, name):
    rig.install(mode)
    assert_refused(rig.kyversion(*arg, **{name: "ky/relative"}), "E1")
    assert rig.calls() == []


def not_a_repo(rig):
    plain = rig.tmp / "plain"
    plain.mkdir()
    return {"KY_SOURCE_REPO": str(plain)}


def missing_repo(rig):
    return {"KY_SOURCE_REPO": str(rig.tmp / "absent")}


def below_the_top(rig):
    return {"KY_SOURCE_REPO": str(rig.repo / "00_ARCHITECTURE")}


def bare_repo(rig):
    bare = rig.tmp / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True)
    return {"KY_SOURCE_REPO": str(bare)}


def redirected_by_the_environment(rig):
    plain = rig.tmp / "plain"
    plain.mkdir()
    return {"KY_SOURCE_REPO": str(plain), "GIT_DIR": str(rig.repo / ".git"), "GIT_WORK_TREE": str(plain)}


@pytest.mark.parametrize("how", [not_a_repo, missing_repo, below_the_top, bare_repo, redirected_by_the_environment])
@pytest.mark.parametrize("mode,args", [("bootstrap", ["--bootstrap"]), ("final", []), ("final", ["D"])])
def test_a_source_repository_that_is_no_work_tree_refuses(rig, mode, args, how):
    digest = rig.install(mode)
    rig.root_link(digest, C0)
    args = argv(args, digest)
    assert_refused(rig.kyversion(*args, **how(rig)), "E2")


# ------------------------------------------------------------------ B1 / F1: the receipt's mode

def test_b1_a_final_receipt_under_bootstrap_refuses(rig):
    rig.install("bootstrap")
    rig.edit_receipt(lambda r: r.update(mode="final"))
    assert_refused(rig.kyversion("--bootstrap"), "B1")


def test_b1_a_final_installation_under_bootstrap_refuses(rig):
    rig.install("final")                                    # no VERSIONS.bootstrap.json at all
    result = rig.kyversion("--bootstrap")
    assert result.returncode == 1 and result.stdout == ""
    assert set(codes(result)) >= {"B1", "B2", "B3"}


def test_f1_a_bootstrap_receipt_in_normal_mode_refuses(rig):
    rig.install("final")
    rig.edit_receipt(lambda r: r.update(mode="bootstrap"))
    assert_refused(rig.kyversion(), "F1")


@pytest.mark.parametrize("mode,args", [("bootstrap", ["--bootstrap"]), ("final", [])])
@pytest.mark.parametrize("value", ["absent", None, "", "FINAL", "Bootstrap", ["bootstrap"], True])
def test_b1_f1_an_unknown_receipt_mode_refuses(rig, mode, args, value):
    rig.install(mode)
    rig.edit_receipt(lambda r: r.pop("mode") if value == "absent" else r.update(mode=value))
    assert_refused(rig.kyversion(*args), "B1" if mode == "bootstrap" else "F1")


@pytest.mark.parametrize("mode,args,expected", [("bootstrap", ["--bootstrap"], ["B1", "B3", "B4"]),
                                                ("final", [], ["F1", "F3", "F4", "F7"])])
@pytest.mark.parametrize("damage", ["missing", "not json", "not an object"])
def test_a_receipt_that_cannot_be_read_refuses_every_check_that_needs_it(rig, mode, args, expected, damage):
    rig.install(mode)
    receipt = rig.run / "INSTALL_RECEIPT.json"
    if damage == "missing":
        receipt.unlink()
    else:
        receipt.write_text("{ not json" if damage == "not json" else "[]")
    assert_refused(rig.kyversion(*args), *expected)


# ------------------------------------------------------------------ a bootstrap-only installation never passes normal mode

def test_a_bootstrap_only_installation_never_passes_the_normal_mode(rig):
    digest = rig.install("bootstrap")
    rig.root_link(digest, C0)
    assert_ok(rig.kyversion("--bootstrap"), "bootstrap", digest)       # it is a valid bootstrap installation
    for args in ([], ["--expected-manifest-digest", digest]):
        result = rig.kyversion(*args)
        assert result.returncode == 1 and result.stdout == ""
        assert set(codes(result)) >= {"F1", "F2"}


def test_a_bootstrap_manifest_renamed_to_the_final_one_never_passes_the_normal_mode(rig):
    digest = rig.install("bootstrap")
    shutil.copy2(rig.run / "VERSIONS.bootstrap.json", rig.run / "VERSIONS.json")
    rig.root_link(digest, C0)
    for args in ([], ["--expected-manifest-digest", digest]):
        result = rig.kyversion(*args)
        assert result.returncode == 1 and result.stdout == ""
        assert set(codes(result)) >= {"F1", "F2", "F7"}
    rig.edit_receipt(lambda r: r.update(mode="final"))                  # … nor with a receipt that merely says final
    for args in ([], ["--expected-manifest-digest", digest]):
        result = rig.kyversion(*args)
        assert result.returncode == 1 and result.stdout == ""
        assert codes(result) == ["F2", "F7"]


# ------------------------------------------------------------------ B2: kymanifest.py check

@pytest.mark.parametrize("behave", [
    {"exit": 1},                                                              # the real refusal
    {"exit": 1, "stdout": '{"ok": true, "manifest_sha256": "OWN"}'},          # … whatever it printed
    {"exit": 2, "stdout": '{"ok": true, "manifest_sha256": "OWN"}'},
    {"exit": 0, "stdout": '{"manifest_sha256": "OWN"}'},                      # exit 0 without `ok`
    {"exit": 0, "stdout": '{"ok": false, "manifest_sha256": "OWN"}'},
    {"exit": 0, "stdout": '{"ok": "true", "manifest_sha256": "OWN"}'},
    {"exit": 0, "stdout": '{"ok": 1, "manifest_sha256": "OWN"}'},
    {"exit": 0, "stdout": '{"ok": true, "manifest_sha256": "%s"}' % OTHER},    # another digest
    {"exit": 0, "stdout": '{"ok": true}'},
    {"exit": 0, "stdout": '{"ok": true, "manifest_sha256": null}'},
    {"exit": 0, "stdout": ""},
    {"exit": 0, "stdout": "ok\n"},
    {"exit": 0, "stdout": '[{"ok": true, "manifest_sha256": "OWN"}]'},
    {"exit": 0, "stdout": '{"ok": true, "manifest_sha256": "OWN"}\n{"ok": true}\n'}])
def test_b2_refuses_unless_kymanifest_exits_0_with_ok_true_and_the_files_own_digest(rig, behave):
    digest = rig.install("bootstrap")
    if "stdout" in behave:
        behave = dict(behave, stdout=behave["stdout"].replace("OWN", digest))
    write(rig.behave, behave)
    assert_refused(rig.kyversion("--bootstrap"), "B2")
    assert len(rig.calls()) == 1


def test_b2_refuses_when_kymanifest_is_not_installed(rig):
    rig.install("bootstrap")
    (rig.fleet / "kymanifest.py").unlink()
    assert_refused(rig.kyversion("--bootstrap"), "B2")


@pytest.mark.parametrize("damage", ["missing", "not json", "not an object", "no digest"])
def test_a_bootstrap_manifest_that_cannot_be_read_refuses_every_check_that_needs_it(rig, damage):
    rig.install("bootstrap")
    if damage == "missing":
        rig.manifest_path.unlink()
    elif damage == "no digest":
        doc = read(rig.manifest_path)
        del doc["manifest_sha256"]
        write(rig.manifest_path, doc)
        assert_refused(rig.kyversion("--bootstrap"), "B2", "B3")       # its components and pairs are still readable
        return
    else:
        rig.manifest_path.write_text("{ not json" if damage == "not json" else "[]")
    assert_refused(rig.kyversion("--bootstrap"), "B2", "B3", "B4", "B5")


# ------------------------------------------------------------------ F2: the final manifest

def changed_content(doc):
    doc["plan_version"] = "2.8"


def changed_component(doc):
    doc["components"][0]["sha256"] = OTHER


def stated_digest_changed(doc):
    doc["manifest_sha256"] = OTHER


def test_f2_a_changed_final_manifest_refuses(rig):
    rig.install("final")
    doc = read(rig.manifest_path)
    changed_content(doc)
    write(rig.manifest_path, doc)                           # the stated digest is now stale
    assert_refused(rig.kyversion(), "F2")


def test_f2_a_final_manifest_whose_stated_digest_is_not_its_contents_refuses_everything_bound_to_it(rig):
    rig.install("final")
    doc = read(rig.manifest_path)
    stated_digest_changed(doc)
    write(rig.manifest_path, doc)
    assert_refused(rig.kyversion(), "F2", "F3")


@pytest.mark.parametrize("change", [
    lambda d: d.update(mode="bootstrap"),
    lambda d: d.pop("mode"),
    lambda d: d.update(mode="FINAL"),
    lambda d: d.pop("entrypoints"),
    lambda d: d.update(entrypoints=[]),
    lambda d: d["entrypoints"].pop("surrogate_agent"),
    lambda d: d["entrypoints"].pop("plan"),
    lambda d: d["entrypoints"].update(sixth={"path": "x"}),
    lambda d: d["entrypoints"].update(strategy="KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md"),
    lambda d: d["entrypoints"]["owner_decisions"].update(path=""),
    lambda d: d["entrypoints"]["cockpit_prompt"].pop("path")])
def test_f2_refuses_a_manifest_that_is_not_final_or_lacks_the_five_role_entrypoints(rig, change):
    rig.install("final")
    rig.edit_manifest(change)                               # its digest is true and the receipt binds it
    assert_refused(rig.kyversion(), "F2")


@pytest.mark.parametrize("damage", ["missing", "not json", "not an object"])
def test_a_final_manifest_that_cannot_be_read_refuses_every_check_that_needs_it(rig, damage):
    rig.install("final")
    if damage == "missing":
        rig.manifest_path.unlink()
    else:
        rig.manifest_path.write_text("{ not json" if damage == "not json" else "[]")
    assert_refused(rig.kyversion(), "F2", "F3", "F4", "F5", "F7")


# ------------------------------------------------------------------ B3 / F3: the receipt binds the digest

MODES = [("bootstrap", ["--bootstrap"], "B"), ("final", [], "F")]


@pytest.mark.parametrize("mode,args,prefix", MODES)
@pytest.mark.parametrize("change", [
    lambda r: r["manifest"].update(manifest_sha256=OTHER),
    lambda r: r["manifest"].pop("manifest_sha256"),
    lambda r: r["manifest"].update(manifest_sha256=None),
    lambda r: r.pop("manifest"),
    lambda r: r.update(manifest=r["manifest"]["manifest_sha256"]),
    lambda r: r.update(manifest_sha256=r["manifest"].pop("manifest_sha256"))])
def test_b3_f3_a_receipt_that_does_not_bind_the_manifest_digest_refuses(rig, mode, args, prefix, change):
    rig.install(mode)
    rig.edit_receipt(change)
    assert_refused(rig.kyversion(*args), prefix + "3")


@pytest.mark.parametrize("mode,args,prefix", MODES)
def test_b3_f3_a_manifest_rebuilt_after_the_receipt_refuses(rig, mode, args, prefix):
    rig.install(mode)
    rig.edit_manifest(lambda d: d.update(note="rebuilt"), rebind=False)
    assert_refused(rig.kyversion(*args), prefix + "3")


# ------------------------------------------------------------------ B4 / F4: installed bytes

def other_bytes(rig):
    Path(rig.installed[1]["installed_path"]).write_text("edited after installation\n")


def installed_file_missing(rig):
    Path(rig.installed[0]["installed_path"]).unlink()


def installed_path_is_a_directory(rig):
    Path(rig.installed[0]["installed_path"]).unlink()
    Path(rig.installed[0]["installed_path"]).mkdir()


def no_components(rig):
    rig.edit_receipt(lambda r: r.update(components=[]))


def components_absent(rig):
    rig.edit_receipt(lambda r: r.pop("components"))


def components_not_a_list(rig):
    rig.edit_receipt(lambda r: r.update(components={c["path"]: c for c in r["components"]}))


def hash_not_the_manifests(rig):
    # the file really holds the bytes the receipt names: only the manifest disagrees
    target = Path(rig.installed[2]["installed_path"])
    target.write_text("another reviewed-looking version\n")
    rig.edit_receipt(lambda r: r["components"][2].update(sha256=sha(target)))


def path_not_in_the_manifest(rig):
    rig.edit_receipt(lambda r: r["components"][0].update(path=km.FLEET + "/unlisted.sh"))


def relative_installed_path(rig):
    rig.edit_receipt(lambda r: r["components"][0].update(
        installed_path=os.path.relpath(r["components"][0]["installed_path"], str(rig.tmp))))


def installed_path_absent(rig):
    rig.edit_receipt(lambda r: r["components"][0].pop("installed_path"))


def entry_without_a_hash(rig):
    rig.edit_receipt(lambda r: r["components"][0].pop("sha256"))


def entry_not_an_object(rig):
    rig.edit_receipt(lambda r: r["components"].append(r["components"][0]["installed_path"]))


@pytest.mark.parametrize("mode,args,prefix", MODES)
@pytest.mark.parametrize("damage", [
    other_bytes, installed_file_missing, installed_path_is_a_directory, no_components, components_absent,
    components_not_a_list, hash_not_the_manifests, path_not_in_the_manifest, relative_installed_path,
    installed_path_absent, entry_without_a_hash, entry_not_an_object])
def test_b4_f4_installed_bytes_that_are_not_the_manifests_refuse(rig, mode, args, prefix, damage):
    rig.install(mode)
    damage(rig)
    assert_refused(rig.kyversion(*args), prefix + "4")


@pytest.mark.parametrize("change", [
    lambda d: d.update(components="none"),
    lambda d: d["components"].append(dict(d["components"][0])),               # a path listed twice
    lambda d: d["components"][1].update(sha256="short")])
def test_b4_a_manifest_without_a_usable_component_list_refuses(rig, change):
    rig.install("bootstrap")
    rig.edit_manifest(change)
    assert_refused(rig.kyversion("--bootstrap"), "B4")


# ------------------------------------------------------------------ B5 / F5: KU-03 canonical and compatibility copies

def pair_change(key, role, value=None):
    def change(doc):
        for pair in doc["generated_pairs"]:
            if pair["role"] == role:
                if value is None:
                    pair.pop(key)
                    if key.endswith("_abs"):
                        pair.pop(key[:-4], None)  # no relative identity either
                else:
                    pair.update({key: value})
    return change


@pytest.mark.parametrize("mode,args,prefix", MODES)
@pytest.mark.parametrize("role", PAIR_ROLES)
@pytest.mark.parametrize("copy_key", ["canonical_abs", "compatibility_abs"])
@pytest.mark.parametrize("damage", ["missing", "unequal", "directory", "symlink"])
def test_b5_f5_a_missing_or_unequal_copy_refuses(rig, mode, args, prefix, role, copy_key, damage):
    rig.install(mode)
    pair = next(p for p in rig.pairs if p["role"] == role)
    target, twin = Path(pair[copy_key]), Path(pair["canonical_abs" if copy_key == "compatibility_abs" else "compatibility_abs"])
    if damage == "unequal":
        target.write_text("edited independently\n")
    else:
        target.unlink()
        if damage == "directory":
            target.mkdir()
        elif damage == "symlink":                           # a link to the other copy is not a copy
            target.symlink_to(twin)
    assert_refused(rig.kyversion(*args), prefix + "5")


@pytest.mark.parametrize("mode,args,prefix", MODES)
def test_b5_f5_both_copies_edited_alike_refuse(rig, mode, args, prefix):
    rig.install(mode)
    for key in ("canonical_abs", "compatibility_abs"):
        Path(rig.pairs[0][key]).write_text("the same unreviewed bytes\n")
    assert_refused(rig.kyversion(*args), prefix + "5")


@pytest.mark.parametrize("mode,args,prefix", MODES)
@pytest.mark.parametrize("change", [
    lambda d: d.pop("generated_pairs"),
    lambda d: d.update(generated_pairs=[]),
    lambda d: d.update(generated_pairs={p["role"]: p for p in d["generated_pairs"]}),
    lambda d: d["generated_pairs"].append("CLOSURE"),
    lambda d: d["generated_pairs"].pop(0),                                    # WORKTREE_DISPOSITIONS absent
    lambda d: d["generated_pairs"].pop(1),                                    # ACCEPTANCE_ROOTS absent
    lambda d: d["generated_pairs"].pop(2),                                    # CLOSURE absent
    lambda d: d["generated_pairs"].append(dict(d["generated_pairs"][2])),     # a role named twice
    pair_change("compatibility_abs", "CLOSURE"),
    pair_change("canonical_abs", "ACCEPTANCE_ROOTS"),
    pair_change("sha256", "WORKTREE_DISPOSITIONS"),
    pair_change("sha256", "WORKTREE_DISPOSITIONS", OTHER),
    pair_change("compatibility_abs", "CLOSURE", "relative/CLOSURE_v2_2.json"),
    lambda d: d["generated_pairs"][2].update(compatibility_abs=d["generated_pairs"][2]["canonical_abs"])])
def test_b5_f5_a_manifest_that_does_not_record_both_copies_of_each_role_refuses(rig, mode, args, prefix, change):
    rig.install(mode)
    rig.edit_manifest(change)
    assert_refused(rig.kyversion(*args), prefix + "5")


# ------------------------------------------------------------------ B6 / F6 and the expected digest: the activation chain
# Each case writes records into KY_RUN given D, the installed manifest's digest, and states what the chain is:
# "none", "valid" (terminal link = D), "valid-other" (a sound chain ending elsewhere) or "refused".

def chain_none(rig, d):
    pass


def chain_root_only(rig, d):
    rig.root_link(d, C0)


def chain_root_without_a_commit(rig, d):
    rig.root_link(d, None)


def chain_root_two_agreeing_keys(rig, d):
    rig.root_link(d, C0, new_manifest_digest=d, new_commit=C0)


def chain_root_two_disagreeing_keys(rig, d):
    rig.root_link(d, C0, new_manifest_digest=OTHER)


def chain_root_two_disagreeing_commits(rig, d):
    rig.root_link(d, C0, new_commit=C1)
    rig.link(1, (C0, d), (C1, d))


def chain_root_and_two_links(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, "9" * 64))
    rig.link(2, (C1, "9" * 64), (C2, d))


def chain_numbered_only(rig, d):
    rig.link(1, (C0, OTHER), (C1, "9" * 64), previous=None)
    rig.link(2, (C1, "9" * 64), (C2, d))


def chain_ends_elsewhere(rig, d):
    rig.root_link(d, C0)
    rig.link(1, (C0, d), (C1, OTHER))


def chain_root_only_elsewhere(rig, d):
    rig.root_link(OTHER, C0)


def chain_gapped(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, "9" * 64))
    rig.link(2, (C1, "9" * 64), (C2, "8" * 64))
    rig.link(3, (C2, "8" * 64), (C3, d))
    (rig.run / "ACTIVATION_RECORD.2.json").unlink()


def chain_gapped_at_the_start(rig, d):
    rig.link(1, (C0, OTHER), (C1, "9" * 64), previous=None)
    rig.link(2, (C1, "9" * 64), (C2, d))
    (rig.run / "ACTIVATION_RECORD.1.json").unlink()


def chain_broken_predecessor_hash(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d), previous={"file": "ACTIVATION_RECORD.json", "sha256": "7" * 64})


def chain_broken_predecessor_rewritten(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d))
    rig.root_link(OTHER, C0, note="rewritten after link 1 was written")


def chain_broken_predecessor_name(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, "9" * 64))
    rig.link(2, (C1, "9" * 64), (C2, d), previous={"file": "ACTIVATION_RECORD.json", "sha256": sha(rig.run / "ACTIVATION_RECORD.json")})


def chain_broken_discontinuous_digest(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, "9" * 64), (C1, d))


def chain_broken_discontinuous_commit(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C3, OTHER), (C1, d))


def chain_broken_root_gave_no_commit(rig, d):
    rig.root_link(OTHER, None)
    rig.link(1, (C0, OTHER), (C1, d))


def chain_broken_first_numbered_names_a_predecessor(rig, d):
    rig.link(1, (C0, OTHER), (C1, d), previous={"file": "ACTIVATION_RECORD.json", "sha256": "7" * 64})


def chain_broken_misnumbered(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d), number=2)


def chain_broken_number_is_text(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d), number="1")


def chain_broken_number_is_true(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d), number=True)


def chain_broken_link_unreadable(rig, d):
    rig.root_link(d, C0)
    (rig.run / "ACTIVATION_RECORD.1.json").write_text("{ not json")


def chain_broken_link_without_digests(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d))
    doc = read(rig.run / "ACTIVATION_RECORD.1.json")
    del doc["new_manifest_digest"]
    write(rig.run / "ACTIVATION_RECORD.1.json", doc)


def chain_broken_link_with_a_short_commit(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), ("abc1234", d))


def chain_forked_second_start(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d), previous=None)


def chain_forked_stray_file(rig, d):
    rig.root_link(d, C0)
    write(rig.run / "ACTIVATION_RECORD.final.json", {"final_manifest_digest": d})


def chain_forked_zero_padded_link(rig, d):
    rig.root_link(OTHER, C0)
    rig.link(1, (C0, OTHER), (C1, d))
    (rig.run / "ACTIVATION_RECORD.1.json").rename(rig.run / "ACTIVATION_RECORD.01.json")


def chain_forked_copy_beside_it(rig, d):
    rig.root_link(d, C0)
    shutil.copy2(rig.run / "ACTIVATION_RECORD.json", rig.run / "ACTIVATION_RECORD copy.json")


def chain_root_unreadable(rig, d):
    (rig.run / "ACTIVATION_RECORD.json").write_text("{ not json")


def chain_root_not_an_object(rig, d):
    write(rig.run / "ACTIVATION_RECORD.json", [d])


def chain_root_is_a_directory(rig, d):
    (rig.run / "ACTIVATION_RECORD.json").mkdir()


def chain_root_without_a_digest(rig, d):
    write(rig.run / "ACTIVATION_RECORD.json", {"source_commit": C0})


def chain_root_digest_in_upper_case(rig, d):
    rig.root_link(d.upper(), C0)


def chain_root_digest_not_text(rig, d):
    write(rig.run / "ACTIVATION_RECORD.json", {"final_manifest_digest": 7})


CHAINS = [
    (chain_none, "none"),
    (chain_root_only, "valid"), (chain_root_without_a_commit, "valid"), (chain_root_two_agreeing_keys, "valid"),
    (chain_root_and_two_links, "valid"), (chain_numbered_only, "valid"),
    (chain_ends_elsewhere, "valid-other"), (chain_root_only_elsewhere, "valid-other"),
    (chain_root_two_disagreeing_keys, "refused"), (chain_root_two_disagreeing_commits, "refused"),
    (chain_gapped, "refused"), (chain_gapped_at_the_start, "refused"),
    (chain_broken_predecessor_hash, "refused"), (chain_broken_predecessor_rewritten, "refused"),
    (chain_broken_predecessor_name, "refused"), (chain_broken_discontinuous_digest, "refused"),
    (chain_broken_discontinuous_commit, "refused"), (chain_broken_root_gave_no_commit, "refused"),
    (chain_broken_first_numbered_names_a_predecessor, "refused"), (chain_broken_misnumbered, "refused"),
    (chain_broken_number_is_text, "refused"), (chain_broken_number_is_true, "refused"),
    (chain_broken_link_unreadable, "refused"), (chain_broken_link_without_digests, "refused"),
    (chain_broken_link_with_a_short_commit, "refused"),
    (chain_forked_second_start, "refused"), (chain_forked_stray_file, "refused"),
    (chain_forked_zero_padded_link, "refused"), (chain_forked_copy_beside_it, "refused"),
    (chain_root_unreadable, "refused"), (chain_root_not_an_object, "refused"), (chain_root_is_a_directory, "refused"),
    (chain_root_without_a_digest, "refused"), (chain_root_digest_in_upper_case, "refused"),
    (chain_root_digest_not_text, "refused")]


def kyloop_verdict(run, digest):
    """What kyloop.py's own activation_chain says of the same directory, in this table's words."""
    links, reason = kyloop.Controller.activation_chain(types.SimpleNamespace(run=run))
    if links is None:
        return "none" if reason.startswith("activation_record_missing") else "refused"
    return "valid" if links[-1]["manifest_digest"] == digest else "valid-other"


@pytest.mark.parametrize("build,chain", CHAINS, ids=[c[0].__name__ for c in CHAINS])
def test_b6_the_bootstrap_mode_checks_the_chains_structure_only(rig, build, chain):
    digest = rig.install("bootstrap")
    build(rig, digest)
    assert kyloop_verdict(rig.run, digest) == chain                 # the table states kyloop.py's rules
    result = rig.kyversion("--bootstrap")
    if chain == "refused":
        assert_refused(result, "B6")
    else:
        assert_ok(result, "bootstrap", digest)


@pytest.mark.parametrize("build,chain", CHAINS, ids=[c[0].__name__ for c in CHAINS])
def test_f6_the_normal_mode_checks_the_chains_structure_only(rig, build, chain):
    digest = rig.install("final")
    build(rig, digest)
    assert kyloop_verdict(rig.run, digest) == chain
    result = rig.kyversion()
    if chain == "refused":
        assert_refused(result, "F6")
    else:
        assert_ok(result, "final", digest)


@pytest.mark.parametrize("build,chain", CHAINS, ids=[c[0].__name__ for c in CHAINS])
def test_d2_the_expected_digest_must_be_the_terminal_link_of_a_valid_chain(rig, build, chain):
    digest = rig.install("final")
    build(rig, digest)
    assert kyloop_verdict(rig.run, digest) == chain
    result = rig.kyversion("--expected-manifest-digest", digest)
    if chain == "valid":
        assert_ok(result, "final", digest)
    elif chain == "refused":
        assert_refused(result, "F6", "D2")
    else:                                                           # no chain, or one that ends elsewhere
        assert_refused(result, "D2")


def test_d1_an_expected_digest_unequal_to_the_manifest_refuses(rig):
    digest = rig.install("final")
    rig.root_link(digest, C0)
    rig.link(1, (C0, digest), (C1, OTHER))                          # the chain does end in the digest asked for
    assert_refused(rig.kyversion("--expected-manifest-digest", OTHER), "D1")


def test_d2_an_expected_digest_unequal_to_the_terminal_link_refuses(rig):
    digest = rig.install("final")
    rig.root_link(digest, C0)                                       # an earlier link carries it; the terminal does not
    rig.link(1, (C0, digest), (C1, OTHER))
    assert_refused(rig.kyversion("--expected-manifest-digest", digest), "D2")


def test_d2_an_expected_digest_without_a_chain_refuses(rig):
    digest = rig.install("final")
    assert_refused(rig.kyversion("--expected-manifest-digest", digest), "D2")


def test_d1_d2_an_expected_digest_found_nowhere_refuses_twice(rig):
    digest = rig.install("final")
    rig.root_link(digest, C0)
    assert_refused(rig.kyversion("--expected-manifest-digest", OTHER), "D1", "D2")


def test_an_unlistable_run_directory_refuses_the_chain_check_too(rig):
    rig.install("bootstrap")
    shutil.rmtree(rig.run)
    assert_refused(rig.kyversion("--bootstrap"), "B1", "B2", "B3", "B4", "B5", "B6")


# ------------------------------------------------------------------ F7: the final receipt's evidence

def stale_tested_hashes(r):
    r["rehearsal"]["tested_components"][0]["sha256"] = OTHER


def one_component_untested(r):
    r["rehearsal"]["tested_components"].pop()


def one_extra_component_tested(r):
    r["rehearsal"]["tested_components"].append({"path": "fleet/extra.sh", "sha256": OTHER})


def one_component_tested_twice(r):
    r["rehearsal"]["tested_components"].append(dict(r["rehearsal"]["tested_components"][0]))


def no_tested_components(r):
    del r["rehearsal"]["tested_components"]


def mapping_of_tested_components(r):
    r["rehearsal"]["tested_components"] = {c["path"]: c["sha256"] for c in r["rehearsal"]["tested_components"]}


def remove(*keys):
    def change(r):
        target = r
        for key in keys[:-1]:
            target = target[key]
        del target[keys[-1]]
    return change


def put(value, *keys):
    def change(r):
        target = r
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
    return change


def file_gone(*keys):
    def change(r):
        target = r
        for key in keys:
            target = target[key]
        Path(target["path"]).unlink()
    return change


def file_changed(*keys):
    def change(r):
        target = r
        for key in keys:
            target = target[key]
        Path(target["path"]).write_text("rewritten after the receipt\n")
    return change


F7_CASES = {
    "stale tested hashes": stale_tested_hashes,
    "a tested component missing": one_component_untested,
    "an untested extra component": one_extra_component_tested,
    "a tested component twice": one_component_tested_twice,
    "tested components absent": no_tested_components,
    "tested components as a mapping": mapping_of_tested_components,
    "rehearsal missing": remove("rehearsal"),
    "rehearsal null": put(None, "rehearsal"),
    "rehearsal results missing": remove("rehearsal", "results"),
    "rehearsal results file gone": file_gone("rehearsal", "results"),
    "rehearsal results file changed": file_changed("rehearsal", "results"),
    "rehearsal results hash missing": remove("rehearsal", "results", "sha256"),
    "rehearsal results path relative": put("evidence/REHEARSAL_RESULTS.json", "rehearsal", "results", "path"),
    "coverage missing": remove("coverage"),
    "coverage file gone": file_gone("coverage"),
    "coverage file changed": file_changed("coverage"),
    "coverage verdict missing": remove("coverage", "verdict"),
    "coverage verdict rejected": put("REJECTED", "coverage", "verdict"),
    "coverage verdict lower case": put("accepted", "coverage", "verdict"),
    "packets missing": remove("packets"),
    "packets empty": put([], "packets"),
    "packets not a list": put({"path": "x"}, "packets"),
    "a packet file gone": file_gone("packets", 1),
    "a packet file changed": file_changed("packets", 0),
    "a packet without a hash": remove("packets", 0, "sha256"),
    "a packet entry that is a bare path": put("PACKET_A.md", "packets", 0),
    "backfill missing": remove("backfill"),
    "backfill file gone": file_gone("backfill"),
    "backfill file changed": file_changed("backfill"),
    "backfill not validated": put(False, "backfill", "validated"),
    "backfill validated as text": put("true", "backfill", "validated"),
    "backfill validated as 1": put(1, "backfill", "validated"),
    "backfill validated missing": remove("backfill", "validated"),
    "tracker revision missing": remove("tracker_revision"),
    "tracker revision null": put(None, "tracker_revision"),
    "tracker revision empty": put("", "tracker_revision"),
    "tracker revision blank": put("   ", "tracker_revision"),
    "tracker revision true": put(True, "tracker_revision"),
}


@pytest.mark.parametrize("case", sorted(F7_CASES))
def test_f7_final_evidence_that_is_missing_stale_or_changed_refuses(rig, case):
    rig.install("final")
    rig.edit_receipt(F7_CASES[case])
    assert_refused(rig.kyversion(), "F7")


def test_f7_tested_components_must_be_the_manifests_even_when_the_receipts_installed_list_is_shorter(rig):
    rig.install("final")
    rig.edit_receipt(lambda r: r["components"].pop())               # F4 allows a partial installed list …
    assert_ok(rig.kyversion(), "final", read(rig.manifest_path)["manifest_sha256"])
    rig.edit_receipt(lambda r: r["rehearsal"].update(tested_components=[   # … F7 does not allow a partial rehearsal
        {"path": c["path"], "sha256": c["sha256"]} for c in r["components"]]))
    assert_refused(rig.kyversion(), "F7")


def test_the_expected_digest_mode_runs_every_normal_check(rig):
    digest = rig.install("final")
    rig.root_link(digest, C0)
    rig.edit_receipt(stale_tested_hashes)
    other_bytes(rig)
    assert_refused(rig.kyversion("--expected-manifest-digest", digest), "F4", "F7")


@pytest.mark.parametrize("role", ["planner", "conductor"])
@pytest.mark.parametrize("damage", ["tamper", "missing", "not-pass", "unrecorded", "wrong-role", "wrong-model"])
def test_bootstrap_installer_loop_receipts_are_required_hash_bound_and_pass(rig, role, damage):
    digest = rig.install("bootstrap")
    rows = []
    for loop in ("planner", "conductor"):
        path = rig.run / (loop + ".json")
        write(path, {"role": loop, "model": "claude-opus-5-5", "result": "PASS"})
        rows.append({"role": loop, "model": "claude-opus-5-5", "receipt": str(path),
                     "receipt_sha256": sha(path), "result": "PASS"})
    rig.edit_receipt(lambda r: r.update(qualifications=rows))
    assert_ok(rig.kyversion("--bootstrap"), "bootstrap", digest)
    row = next(r for r in rows if r["role"] == role)
    path = Path(row["receipt"])
    if damage == "tamper":
        path.write_text(path.read_text() + " ")
    elif damage == "missing":
        path.unlink()
    elif damage == "unrecorded":
        rows.remove(row)
        rig.edit_receipt(lambda r: r.update(qualifications=rows))
    else:
        doc = read(path)
        doc.update({"result": "FAIL"} if damage == "not-pass" else
                   {"role": "surrogate"} if damage == "wrong-role" else {"model": "other"})
        write(path, doc)
        row["receipt_sha256"] = sha(path)
        rig.edit_receipt(lambda r: r.update(qualifications=rows))
    result = rig.kyversion("--bootstrap")
    assert result.returncode == 1 and "REFUSED B7:" in result.stderr, result.stderr


def test_bootstrap_pairs_are_resolved_relative_to_campaign_checkout(rig):
    digest = rig.install("bootstrap")
    rig.edit_manifest(lambda m: [p.pop(k) for p in m["generated_pairs"] for k in ("canonical_abs", "compatibility_abs")])
    digest = read(rig.manifest_path)["manifest_sha256"]
    assert_ok(rig.kyversion("--bootstrap"), "bootstrap", digest)
    (rig.repo / km.PAIRS[0][2]).write_text("changed byte")
    assert_refused(rig.kyversion("--bootstrap"), "B5")


@pytest.mark.parametrize("mode,args,code", [("bootstrap", ["--bootstrap"], "B7"), ("final", [], "F8")])
@pytest.mark.parametrize("damage", ["no-list", "duplicate", "row-not-pass", "relative", "no-hash"])
def test_installer_loop_receipt_record_must_be_complete(rig, mode, args, code, damage):
    rig.install(mode)
    def change(receipt):
        rows = receipt["qualifications"]
        if damage == "no-list":
            receipt.pop("qualifications")
        elif damage == "duplicate":
            rows.append(dict(rows[0]))
        elif damage == "row-not-pass":
            rows[0]["result"] = "FAIL"
        elif damage == "relative":
            rows[0]["receipt"] = "planner.json"
        else:
            rows[0].pop("receipt_sha256")
    rig.edit_receipt(change)
    assert_refused(rig.kyversion(*args), code)


def test_loop_roles_match_controller():
    text = SCRIPT.read_text().split("\n: <<'KYVERSION_PY'\n", 1)[1].rsplit("\nKYVERSION_PY\n", 1)[0]
    # Read the literal declaration without executing the check program's main.
    import ast
    roles = next(ast.literal_eval(n.value) for n in ast.parse(text).body
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "LOOP_ROLES" for t in n.targets))
    assert roles == kyloop.ROLES == km.LOOP_ROLES
