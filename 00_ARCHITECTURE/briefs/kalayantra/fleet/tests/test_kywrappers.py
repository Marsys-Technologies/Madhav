"""KV3-B-WRAPPERS (relaunch plan v2.7 §5, §14 B-1/B-3): the override-preserving `ky` and `kybrief` wrappers.

The wrappers are copied into a temporary ROOT whose `tracker_live/pravaha_tracker/cli.py` is a stub that records its
arguments and the seven PRAVAHA_* values; nothing here touches /Users/Dev/kalayantra or an installed wrapper."""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
SRC = FLEET / "bin"
INSTALLER = FLEET / "install_tracker.sh"
PY = "/opt/homebrew/bin/python3"
CAMPAIGN = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
SEVEN = ("PRAVAHA_HOME", "PRAVAHA_EVENTS", "PRAVAHA_PLAN_MODEL", "PRAVAHA_REPO", "PRAVAHA_HOLD",
         "PRAVAHA_TRACKER_PORT", "PRAVAHA_URL")
PATHS = SEVEN[:5]
WRAPPERS = ("ky", "kybrief")
KYVETO_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "KY_ROOT", "KY_RUN", "KY_FLEET")
REFUSAL = re.compile(r"(ky|kybrief): REFUSED override: ([A-Z_]+): ([^\n]+)\n")
SHARED = re.compile(r"^# --- mode decision: begin.*?^# --- mode decision: end[^\n]*\n", re.S | re.M)

STUB = '''import json, os, sys
import kyverdicts
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
names = %r + ("PRAVAHA_STREAM", "KY_WORKER", "PYTHONPATH")
with open(os.path.join(root, "stub_record.json"), "w") as f:
    json.dump({"argv": sys.argv[1:], "env": {n: os.environ.get(n) for n in names}, "kyverdicts": kyverdicts.MARK,
               "stdin": sys.stdin.read()}, f)
sys.stdout.write("stub-out\\n"); sys.stderr.write("stub-err\\n")
code = os.path.join(root, "stub_exit")
sys.exit(int(open(code).read()) if os.path.exists(code) else 0)
''' % (SEVEN,)


class Tree:
    """One temporary ROOT (bin/ky, bin/kybrief, the stub CLI) and one KY_SCRATCH with a fixture directory."""

    def __init__(self, tmp):
        self.tmp = Path(os.path.realpath(tmp))
        self.root = self.tmp / "root"
        self.scratch = self.tmp / "scratch"
        self.fixture = self.scratch / "fixture"
        self.outside = self.tmp / "outside"
        (self.root / "bin").mkdir(parents=True)
        for w in WRAPPERS:
            shutil.copyfile(SRC / w, self.root / "bin" / w)
            os.chmod(self.root / "bin" / w, 0o755)
        pkg = self.root / "tracker_live" / "pravaha_tracker"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "cli.py").write_text(STUB)
        (self.root / "fleet_live").mkdir()
        (self.root / "fleet_live" / "kyverdicts.py").write_text("MARK = 'fleet_live'\n")
        for d in (self.fixture / "home" / "run", self.fixture / "repo", self.outside):
            d.mkdir(parents=True)
        self.model = self.fixture / "repo" / "plan_model.json"
        self.model.write_text(json.dumps({"items": [{"id": "FX-1", "title": "फ़िक्स्चर item", "brief": {"spec": ["a b"]}},
                                                    {"id": "FX-2"}]}))
        self.record = self.root / "stub_record.json"

    def defaults(self):
        r = str(self.root)
        return {"PRAVAHA_HOME": r, "PRAVAHA_EVENTS": r + "/run/EVENTS.jsonl",
                "PRAVAHA_PLAN_MODEL": CAMPAIGN + "/00_ARCHITECTURE/control/kalayantra/plan_model.json",
                "PRAVAHA_REPO": CAMPAIGN, "PRAVAHA_HOLD": r + "/HOLD",
                "PRAVAHA_TRACKER_PORT": "8767", "PRAVAHA_URL": "http://127.0.0.1:8767"}

    def fixture_env(self):
        f = str(self.fixture)
        return {"KY_SCRATCH": str(self.scratch), "PRAVAHA_HOME": f + "/home", "PRAVAHA_EVENTS": f + "/home/run/EVENTS.jsonl",
                "PRAVAHA_PLAN_MODEL": str(self.model), "PRAVAHA_REPO": f + "/repo", "PRAVAHA_HOLD": f + "/home/HOLD",
                "PRAVAHA_TRACKER_PORT": "18767", "PRAVAHA_URL": "http://127.0.0.1:18767"}

    def run(self, wrapper, args, env, **kw):
        return subprocess.run([str(self.root / "bin" / wrapper), *args], env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, cwd=str(self.tmp), timeout=60, **kw)

    def recorded(self):
        return json.loads(self.record.read_text())

    def snapshot(self):
        out = {}
        for p in sorted(self.tmp.rglob("*")):
            st = p.lstat()
            out[str(p)] = (stat.S_IFMT(st.st_mode), st.st_mode, st.st_mtime_ns,
                           hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() and not p.is_symlink() else None)
        return out


@pytest.fixture
def tree(tmp_path):
    return Tree(tmp_path)


def assert_refused(tree, wrapper, env, name, args=("FX-1",)):
    """Exit 78, exactly one stderr line naming `name`, no value, the stub not started and no file changed."""
    before = tree.snapshot()
    r = tree.run(wrapper, list(args), env)
    assert r.returncode == 78, (r.returncode, r.stdout, r.stderr)
    assert r.stdout == ""
    m = REFUSAL.fullmatch(r.stderr)
    assert m, r.stderr
    assert (m.group(1), m.group(2)) == (wrapper, name), r.stderr
    for n, v in env.items():
        if n in SEVEN + ("KY_SCRATCH",) and len(v) > 1:
            assert v not in r.stderr, n
    assert not tree.record.exists()
    assert tree.snapshot() == before
    return m.group(3)


# ---------------------------------------------------------------------------------------------- LIVE

def test_live_defaults_with_an_empty_environment(tree):
    r = tree.run("ky", ["status"], {})
    assert (r.returncode, r.stdout, r.stderr) == (0, "stub-out\n", "stub-err\n")
    rec = tree.recorded()
    assert rec["argv"] == ["status"]
    assert {n: rec["env"][n] for n in SEVEN} == tree.defaults()
    assert rec["env"]["PRAVAHA_STREAM"] == "" and rec["env"]["KY_WORKER"] == ""
    assert rec["env"]["PYTHONPATH"] == f"{tree.root}/tracker_live:{tree.root}/fleet_live"
    assert rec["kyverdicts"] == "fleet_live"


def test_live_defaults_with_kyvetos_nine_name_environment(tree):
    decoy = tree.tmp / "decoy"
    decoy.mkdir()
    env = dict(zip(KYVETO_NAMES, ("/Users/Dev", "Dev", "en_US.UTF-8", "dumb", "/usr/bin:/bin", str(tree.tmp),
                                  str(decoy), str(decoy / "run"), str(decoy / "fleet_live"))))
    args = ["decide", "D-7", "--outcome", "approved", "--as", "steward", "--delegated", "--detail", "two words; $HOME *"]
    r = tree.run("ky", args, env)
    assert r.returncode == 0, r.stderr
    rec = tree.recorded()
    assert rec["argv"] == args and rec["stdin"] == ""
    assert {n: rec["env"][n] for n in SEVEN} == tree.defaults()      # KY_ROOT in the environment is not consulted
    assert "decoy" not in json.dumps(rec["env"])


def test_all_seven_equal_to_the_defaults_is_live(tree):
    r = tree.run("ky", ["next", "--json"], dict(tree.defaults()))
    assert r.returncode == 0, r.stderr
    assert {n: tree.recorded()["env"][n] for n in SEVEN} == tree.defaults()


def test_root_is_the_real_directory_above_the_wrappers_bin(tree):
    link = tree.tmp / "linked_root"
    link.symlink_to(tree.root)
    r = subprocess.run([str(link / "bin" / "ky"), "status"], env={}, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=60)
    assert r.returncode == 0, r.stderr
    assert tree.recorded()["env"]["PRAVAHA_HOME"] == str(tree.root)


# ------------------------------------------------------------------------------------------- FIXTURE

def test_a_complete_valid_fixture_set_is_passed_through_unchanged(tree):
    env = tree.fixture_env()
    r = tree.run("ky", ["claim", "FX-1"], env)
    assert r.returncode == 0, r.stderr
    rec = tree.recorded()
    assert {n: rec["env"][n] for n in SEVEN} == {n: env[n] for n in SEVEN}
    assert rec["env"]["PYTHONPATH"] == f"{tree.root}/tracker_live:{tree.root}/fleet_live"
    assert "8767" not in {rec["env"]["PRAVAHA_TRACKER_PORT"], rec["env"]["PRAVAHA_URL"].rsplit(":", 1)[1]}


def test_fixture_values_are_not_normalised(tree):
    env = tree.fixture_env()
    env["PRAVAHA_HOME"] = f"{tree.fixture}/repo/../home/"
    env["PRAVAHA_HOLD"] = f"{tree.fixture}/not/yet/created/HOLD"
    link = tree.fixture / "inner"
    link.symlink_to(tree.fixture / "repo")                           # a symlink that stays inside is allowed
    env["PRAVAHA_REPO"] = str(link)
    r = tree.run("ky", ["status"], env)
    assert r.returncode == 0, r.stderr
    assert {n: tree.recorded()["env"][n] for n in SEVEN} == {n: env[n] for n in SEVEN}


def test_ky_scratch_reached_through_a_symlink_is_resolved(tree):
    alias = tree.tmp / "scratch_alias"
    alias.symlink_to(tree.scratch)
    env = tree.fixture_env()
    env["KY_SCRATCH"] = str(alias)
    r = tree.run("ky", ["status"], env)
    assert r.returncode == 0, r.stderr
    assert tree.recorded()["env"]["PRAVAHA_HOME"] == env["PRAVAHA_HOME"]


# --------------------------------------------------------------------------------------- pass-through

@pytest.mark.parametrize("code", [0, 1, 2, 3, 4])
def test_exit_status_and_output_are_the_clis_own(tree, code):
    (tree.root / "stub_exit").write_text(str(code))
    args = ["block", "KV3-X", "--detail", "a detail with  two spaces", "", "*", "$(id)", "नमस्ते", "-x", "--"]
    r = tree.run("ky", args, {})
    assert (r.returncode, r.stdout, r.stderr) == (code, "stub-out\n", "stub-err\n")
    assert tree.recorded()["argv"] == args


def test_stream_and_lane_are_mapped_as_before(tree):
    def env_seen(env):
        assert tree.run("ky", ["inbox", "--stream", "S", "--json"], env).returncode == 0
        return tree.recorded()["env"]
    assert env_seen({"KY_STREAM": "S", "PRAVAHA_STREAM": "Q", "KY_LANE": "L3"})["PRAVAHA_STREAM"] == "S"
    assert env_seen({"KY_STREAM": "S", "KY_LANE": "L3"})["KY_WORKER"] == "L3"
    assert env_seen({"PRAVAHA_STREAM": "Q"})["PRAVAHA_STREAM"] == "Q"
    assert env_seen({"KY_STREAM": "", "PRAVAHA_STREAM": "Q"})["PRAVAHA_STREAM"] == "Q"
    assert env_seen({"KY_WORKER": "stale"})["KY_WORKER"] == ""
    assert env_seen({"PYTHONPATH": "/nonexistent/elsewhere"})["PYTHONPATH"] == f"{tree.root}/tracker_live:{tree.root}/fleet_live"


def test_stdin_reaches_the_cli(tree):
    r = subprocess.run([str(tree.root / "bin" / "ky"), "request"], env={}, input="piped text", capture_output=True,
                       text=True, timeout=60)
    assert r.returncode == 0 and tree.recorded()["stdin"] == "piped text"


def test_installed_copy_is_executable_as_kyloop_requires(tree):
    assert os.access(tree.root / "bin" / "ky", os.X_OK)
    for w in WRAPPERS:
        assert os.access(SRC / w, os.X_OK), w


# -------------------------------------------------------------------------------------------- REFUSED

@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", SEVEN)
def test_any_one_of_the_seven_missing_is_refused(tree, wrapper, name):
    env = tree.fixture_env()
    del env[name]
    assert assert_refused(tree, wrapper, env, name) == "not set"


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", ["PRAVAHA_HOME", "PRAVAHA_EVENTS", "PRAVAHA_HOLD"])
def test_a_missing_name_is_not_completed_even_where_the_default_would_validate(tree, wrapper, name):
    """A wrapper installed inside the fixture directory: its own HOME, EVENTS and HOLD defaults would pass the path rule."""
    inner = tree.fixture / "kalayantra"
    shutil.copytree(tree.root, inner)
    env = tree.fixture_env()
    del env[name]
    r = subprocess.run([str(inner / "bin" / wrapper), "FX-1"], env=env, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=60)
    assert (r.returncode, r.stdout, r.stderr) == (78, "", f"{wrapper}: REFUSED override: {name}: not set\n")
    assert not (inner / "stub_record.json").exists()


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", SEVEN)
def test_any_one_of_the_seven_empty_is_refused(tree, wrapper, name):
    env = tree.fixture_env()
    env[name] = ""
    assert_refused(tree, wrapper, env, name)


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", SEVEN)
def test_a_single_name_set_is_never_completed_from_defaults(tree, wrapper, name):
    for value in (tree.fixture_env()[name], tree.defaults()[name]):
        env = {"KY_SCRATCH": str(tree.scratch), name: value}
        r = tree.run(wrapper, ["FX-1"], env)
        assert r.returncode == 78 and REFUSAL.fullmatch(r.stderr) and not tree.record.exists(), (value, r.stderr)


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", SEVEN)
def test_a_mixed_set_is_refused(tree, wrapper, name):
    """Six fixture values and one live default, and six live defaults and one fixture value."""
    env = tree.fixture_env()
    env[name] = tree.defaults()[name]
    r = tree.run(wrapper, ["FX-1"], env)
    assert r.returncode == 78 and REFUSAL.fullmatch(r.stderr) and not tree.record.exists(), r.stderr
    env = {"KY_SCRATCH": str(tree.scratch), **tree.defaults(), name: tree.fixture_env()[name]}
    r = tree.run(wrapper, ["FX-1"], env)
    assert r.returncode == 78 and REFUSAL.fullmatch(r.stderr) and not tree.record.exists(), r.stderr


@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_the_live_port_is_refused(tree, wrapper):
    env = tree.fixture_env()
    env.update(PRAVAHA_TRACKER_PORT="8767", PRAVAHA_URL="http://127.0.0.1:8767")
    assert_refused(tree, wrapper, env, "PRAVAHA_TRACKER_PORT")


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("port", ["999", "1023", "65536", "70000", "018767", "+18767", "18767 ", " 18767", "0x4967",
                                  "18767.0", "1e4", "port", "-1", "१८७६७", "18767\n"])
def test_a_port_that_is_not_an_integer_in_range_is_refused(tree, wrapper, port):
    env = tree.fixture_env()
    env.update(PRAVAHA_TRACKER_PORT=port, PRAVAHA_URL="http://127.0.0.1:" + port)
    assert_refused(tree, wrapper, env, "PRAVAHA_TRACKER_PORT")


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("url", ["http://127.0.0.1:8767", "http://127.0.0.1:18768", "http://localhost:18767",
                                 "http://127.0.0.2:18767", "http://example.invalid:18767", "https://127.0.0.1:18767",
                                 "http://127.0.0.1:18767/", "http://127.0.0.1:18767@example.invalid",
                                 "http://example.invalid@127.0.0.1:18767", "http://127.0.0.1", "127.0.0.1:18767",
                                 "http://127.0.0.1:18767\n", "HTTP://127.0.0.1:18767", "http://[::1]:18767"])
def test_a_url_on_another_host_or_port_is_refused(tree, wrapper, url):
    env = tree.fixture_env()
    env["PRAVAHA_URL"] = url
    assert_refused(tree, wrapper, env, "PRAVAHA_URL")


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", PATHS)
def test_a_fixture_path_outside_the_fixture_directory_is_refused(tree, wrapper, name):
    (tree.scratch / "fixture2").mkdir()
    for value in (str(tree.outside / "x"), str(tree.scratch / "x"), str(tree.scratch / "fixture2" / "x"),
                  f"{tree.fixture}/../x", f"{tree.fixture}/home/../../x", str(tree.root), tree.defaults()[name], "/"):
        env = tree.fixture_env()
        env[name] = value
        assert_refused(tree, wrapper, env, name)


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", PATHS)
def test_a_fixture_path_that_leaves_through_a_symlink_is_refused(tree, wrapper, name):
    (tree.fixture / "escape").symlink_to(tree.outside)
    (tree.fixture / "dangling").symlink_to(tree.tmp / "nowhere")
    (tree.outside / "file").write_text("{}")
    (tree.fixture / "filelink").symlink_to(tree.outside / "file")
    for value in (f"{tree.fixture}/escape", f"{tree.fixture}/escape/not/yet/there", f"{tree.fixture}/dangling/x",
                  f"{tree.fixture}/filelink"):
        env = tree.fixture_env()
        env[name] = value
        assert_refused(tree, wrapper, env, name)


@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_a_fixture_directory_that_is_itself_a_symlink_out_is_refused(tree, wrapper):
    shutil.rmtree(tree.fixture)
    (tree.outside / "home").mkdir()
    tree.fixture.symlink_to(tree.outside)
    assert_refused(tree, wrapper, tree.fixture_env(), "PRAVAHA_HOME")


@pytest.mark.parametrize("wrapper", WRAPPERS)
@pytest.mark.parametrize("name", PATHS)
def test_a_relative_fixture_path_is_refused(tree, wrapper, name):
    env = tree.fixture_env()
    env[name] = "scratch/fixture/home"                               # the working directory is the parent of scratch/
    assert_refused(tree, wrapper, env, name)


@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_ky_scratch_unset_empty_or_relative_is_refused(tree, wrapper):
    env = tree.fixture_env()
    del env["KY_SCRATCH"]
    assert_refused(tree, wrapper, env, "KY_SCRATCH")
    assert_refused(tree, wrapper, {**env, "KY_SCRATCH": ""}, "KY_SCRATCH")
    assert_refused(tree, wrapper, {**env, "KY_SCRATCH": "scratch"}, "KY_SCRATCH")


@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_ky_scratch_that_does_not_hold_the_paths_is_refused(tree, wrapper):
    env = tree.fixture_env()
    env["KY_SCRATCH"] = str(tree.outside)
    assert_refused(tree, wrapper, env, "PRAVAHA_HOME")


def test_the_refusal_detector_itself_fails_when_the_stub_runs(tree):
    """Negative control: a run that reaches the stub is seen by both checks `assert_refused` relies on."""
    before = tree.snapshot()
    assert tree.run("ky", ["status"], tree.fixture_env()).returncode == 0
    assert tree.record.exists() and tree.snapshot() != before


# -------------------------------------------------------------------------------------------- kybrief

AUDIT = '''import json, runpy, sys
opened = []
sys.addaudithook(lambda event, args: opened.append(args[0]) if event == "open" and isinstance(args[0], str) else None)
out, script = sys.argv[1], sys.argv[2]
sys.argv = sys.argv[2:]
try:
    runpy.run_path(script, run_name="__main__")
    code = 0
except SystemExit as e:
    code = e.code
seen = [p for p in opened if p.endswith(".json")]
with open(out, "w") as f:
    json.dump(seen, f)
sys.exit(code)
'''


def opened_json(tree, env, item):
    """Run the copied kybrief under an `open` audit hook; return (result, the .json paths it opened)."""
    out = tree.tmp / "opened.json"
    r = subprocess.run([PY, "-I", "-B", "-c", AUDIT, str(out), str(tree.root / "bin" / "kybrief"), item], env=env,
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    return r, json.loads(out.read_text())


def test_kybrief_reads_the_fixture_model_in_fixture_mode(tree):
    r = tree.run("kybrief", ["FX-1"], tree.fixture_env())
    item = json.loads(tree.model.read_text())["items"][0]
    assert (r.returncode, r.stderr) == (0, "")
    assert r.stdout == json.dumps(item, ensure_ascii=False, indent=1) + "\n"
    assert opened_json(tree, tree.fixture_env(), "FX-1")[1] == [str(tree.model)]


def test_kybrief_unknown_item_and_usage(tree):
    r = tree.run("kybrief", ["NOPE 1"], tree.fixture_env())
    assert (r.returncode, r.stdout) == (1, "no such item: NOPE 1\n")
    for args in ([], [""], ["FX-1", "FX-2"]):
        r = tree.run("kybrief", args, tree.fixture_env())
        assert (r.returncode, r.stdout, r.stderr) == (64, "", "usage: kybrief <ITEM-ID>\n"), args
    assert tree.run("kybrief", [], {}).returncode == 64


def test_kybrief_fixture_model_unreadable_names_no_value(tree):
    env = tree.fixture_env()
    env["PRAVAHA_PLAN_MODEL"] = str(tree.fixture / "repo" / "absent.json")
    r = tree.run("kybrief", ["FX-1"], env)
    assert (r.returncode, r.stdout) == (66, "")
    assert r.stderr == "kybrief: cannot read plan model: PRAVAHA_PLAN_MODEL\n"
    tree.model.write_text("{not json")
    r = tree.run("kybrief", ["FX-1"], tree.fixture_env())
    assert (r.returncode, r.stdout) == (65, "") and str(tree.model) not in r.stderr and r.stderr.count("\n") == 1
    tree.model.write_text('{"items": 3}')
    assert tree.run("kybrief", ["FX-1"], tree.fixture_env()).returncode == 65


@pytest.mark.parametrize("env_kind", ["empty", "explicit defaults"])
def test_kybrief_live_mode_opens_exactly_the_default_path(tree, env_kind):
    """Holds whether or not the campaign checkout exists: the path is shown by the refusal line when the model is
    absent, by the printed item when it is present, and in both cases by the `open` audit record."""
    default = tree.defaults()["PRAVAHA_PLAN_MODEL"]
    env = {} if env_kind == "empty" else dict(tree.defaults())
    if os.path.isfile(default):
        items = json.loads(Path(default).read_text())["items"]
        r = tree.run("kybrief", [items[0]["id"]], env)
        assert (r.returncode, r.stderr) == (0, "")
        assert r.stdout == json.dumps(items[0], ensure_ascii=False, indent=1) + "\n"
    else:
        r = tree.run("kybrief", ["FX-1"], env)
        assert (r.returncode, r.stdout) == (66, "")
        assert r.stderr == f"kybrief: cannot read plan model: {default}\n"
    assert opened_json(tree, env, "FX-1")[1] == [default]


# --------------------------------------------------------------------------------------------- source

def test_the_mode_decision_is_the_same_text_in_both_wrappers():
    blocks = [SHARED.findall((SRC / w).read_text()) for w in WRAPPERS]
    assert all(len(b) == 1 for b in blocks)
    assert blocks[0] == blocks[1]
    assert "def decide(" in blocks[0][0] and "78" in blocks[0][0]


def test_the_wrappers_are_static_and_name_no_installed_root():
    for w in WRAPPERS:
        text = (SRC / w).read_text()
        assert text.startswith("#!/opt/homebrew/bin/python3 -IB\n"), w
        assert "/Users/Dev/kalayantra" not in text and "KY_ROOT" not in text.replace("`KY_ROOT`", ""), w
        assert not re.search(r"@@|\{\{|__[A-Z]+__(?<!__file__)", text.replace("__file__", "")), w
        assert CAMPAIGN in text and "wt/campaign" not in text, w
    ky = (SRC / "ky").read_text()
    assert '"-m", "pravaha_tracker.cli"' in ky and '"/tracker_live:"' in ky and '"/fleet_live"' in ky


def plist_split():
    """(lines outside the launchd plist heredoc, lines inside it)."""
    outside, inside, in_plist = [], [], False
    for line in INSTALLER.read_text().splitlines():
        if not in_plist and re.match(r'cat > "\$PLIST" <<EOF$', line):
            in_plist = True
        elif in_plist and line == "EOF":
            in_plist = False
        elif in_plist:
            inside.append(line)
        else:
            outside.append(line)
    return outside, inside


def assigns_pravaha(lines):
    return [line for line in lines if re.search(r"PRAVAHA_[A-Z0-9_]*\s*=", line)]


def test_install_tracker_assigns_no_pravaha_value_outside_its_plist_block():
    outside, inside = plist_split()
    assert len(inside) > 10 and any("PRAVAHA_HOME" in line for line in inside)
    assert assigns_pravaha(outside) == []
    assert not any("PRAVAHA_" in line for line in outside)
    text = "\n".join(outside)
    assert not re.search(r'cat\s*>\s*"?\$KY_ROOT/bin/', text)
    assert "pravaha_tracker.cli" not in text


def test_the_pravaha_assignment_detector_sees_the_old_generator():
    old = ['export PRAVAHA_HOME="$KY_ROOT"', "export PRAVAHA_TRACKER_PORT=8767", 'PRAVAHA_URL="http://127.0.0.1:8767" x',
           "  PRAVAHA_REPO = y"]
    assert assigns_pravaha(old) == old
    assert assigns_pravaha(['echo "$PRAVAHA_HOME"', "# PRAVAHA_HOME is set by the wrapper"]) == []


def test_install_tracker_installs_the_two_static_files_by_byte_copy(tmp_path):
    """The installer's wrapper block alone, run against a temporary fleet copy and a temporary root."""
    m = re.search(r"^# wrappers: begin[^\n]*\n(.*?)^# wrappers: end", INSTALLER.read_text(), re.S | re.M)
    assert m
    block = m.group(1)
    assert "<<" not in block and block.count("install -m 0755") == 1
    fleet, root = tmp_path / "fleet", tmp_path / "root"
    (fleet / "bin").mkdir(parents=True)
    (root / "bin").mkdir(parents=True)
    for w in WRAPPERS:
        shutil.copyfile(SRC / w, fleet / "bin" / w)
        os.chmod(fleet / "bin" / w, 0o600)
    (fleet / "block.sh").write_text('set -euo pipefail\numask 077\nKY_ROOT="$1"\n' + block)
    r = subprocess.run(["/bin/bash", str(fleet / "block.sh"), str(root)], env={"PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")
    assert sorted(p.name for p in (root / "bin").iterdir()) == ["ky", "kybrief"]
    for w in WRAPPERS:
        assert (root / "bin" / w).read_bytes() == (SRC / w).read_bytes()
        assert stat.S_IMODE((root / "bin" / w).stat().st_mode) == 0o755
    (fleet / "bin" / "kybrief").unlink()
    r = subprocess.run(["/bin/bash", str(fleet / "block.sh"), str(root)], env={"PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert r.returncode != 0
