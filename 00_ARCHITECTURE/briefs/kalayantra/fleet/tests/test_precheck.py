"""KV3-B-PRECHECK: precheck.sh is fixture-aware through KY_RUN and refuses the paths of FROZEN_PATHS.txt.

Every case runs a copy of the script, beside a manifest the test writes, inside a throwaway git repository with an
origin/main ref and stub npm / npx / gitleaks / secret_scan.sh. No network, no database, no real /Users/Dev/kalayantra path.
A verdict is only trusted with its reason: a RED case names the one line that made it red, and GREEN needs all nine steps.
"""
import hashlib
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
PRECHECK = FLEET / "precheck.sh"
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
ITEM = "KV3-T-ITEM"
FROZEN_ENTRY = "docs/frozen_note.md"          # outside the inline pattern of step 9
DEFAULT_MANIFEST = "# frozen paths (test manifest)\n\n" + FROZEN_ENTRY + "\ndocs/other_frozen.md\n"
INLINE_RED = "diff touches a frozen or forbidden path"
ORCH = "platform/python-sidecar/pipeline/orchestrator"

STUB = """#!/bin/bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
echo "stub $(basename "$0") $*"
v="STUB_$(basename "$0" | tr a-z A-Z)_EXIT"; exit "${!v:-0}"
"""
GOV_STUB = "print('{name}: 0 {noun} (stub)')\n"


def git(repo, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                   env={"PATH": SYSTEM_PATH, "HOME": str(repo.parent), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})


def marker_test(path, marker):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"def test_marks():\n    open({str(marker)!r}, 'w').write('ran')\n")


class Bench:
    """A throwaway lane worktree with the script under test, its frozen manifest, and separate KY_ROOT and KY_RUN."""

    def __init__(self, tmp, manifest=DEFAULT_MANIFEST):
        self.tmp = tmp
        self.repo = tmp / "repo"
        self.marks = tmp / "marks"
        self.ky_root = tmp / "kyroot"
        self.ky_run = tmp / "kyrun"
        self.stub_log = tmp / "stub.log"
        for d in (self.repo, self.marks, self.ky_root / "run" / "tests", self.ky_run / "tests", tmp / "tmp", tmp / "home", tmp / "bin"):
            d.mkdir(parents=True)
        for name in ("npm", "npx", "gitleaks"):
            stub = tmp / "bin" / name
            stub.write_text(STUB)
            stub.chmod(0o755)
        (tmp / "bin" / "python3").symlink_to(sys.executable)   # step 4 of the full run calls a bare python3
        gov = self.repo / "platform" / "scripts" / "governance"
        gov.mkdir(parents=True)
        (gov / "secret_scan.sh").write_text("#!/bin/bash\nexit 0\n")
        (gov / "drift_detector.py").write_text(GOV_STUB.format(name="drift_detector", noun="findings"))
        (gov / "schema_validator.py").write_text(GOV_STUB.format(name="schema_validator", noun="violations"))
        (gov / "check_fact_category_pinning.py").write_text("")
        for keep in ("platform/python-sidecar/.gitkeep", "platform-mcp/.gitkeep", "docs/readme.md", FROZEN_ENTRY, "docs/काल.md"):
            (self.repo / keep).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / keep).write_text("baseline\n")
        for name in ("pass_a", "pass_b", "pass_c"):
            marker_test(self.repo / "t" / f"test_{name}.py", self.marks / name)
        (self.repo / "t" / "test_red.py").write_text("def test_red():\n    assert False\n")
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / ".git" / "info" / "exclude").write_text("fleet/\n__pycache__/\n")   # the copy under test is never in the diff
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "baseline")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.repo, "checkout", "-q", "-b", "lane")
        self.fleet = self.repo / "fleet"
        self.fleet.mkdir()
        shutil.copy(PRECHECK, self.fleet / "precheck.sh")
        self.manifest = self.fleet / "FROZEN_PATHS.txt"
        if manifest is not None:
            self.manifest.write_bytes(manifest if isinstance(manifest, bytes) else manifest.encode())

    def change(self, rel, text="changed\n", stage=True):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if stage:
            git(self.repo, "add", "--", rel)

    def run(self, mode="--item", tests="t/test_pass_a.py", ky_run="default", cwd=None, script=None, **extra):
        env = {"PATH": f"{self.tmp / 'bin'}:{SYSTEM_PATH}", "HOME": str(self.tmp / "home"), "TMPDIR": str(self.tmp / "tmp"),
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "PYTHONDONTWRITEBYTECODE": "1",
               "PYTEST_ADDOPTS": "-p no:cacheprovider", "STUB_LOG": str(self.stub_log),
               "KY_ROOT": str(self.ky_root), "KY_PY": sys.executable, "KY_ITEM": ITEM}
        if ky_run == "default":
            env["KY_RUN"] = str(self.ky_run)
        elif ky_run is not None:
            env["KY_RUN"] = ky_run
        if tests is not None:
            env["TESTS"] = tests
        env.update({k: v for k, v in extra.items() if v is not None})
        for k in [k for k, v in extra.items() if v is None]:
            env.pop(k, None)
        argv = ["/bin/bash", script or str(self.fleet / "precheck.sh")] + ([mode] if mode else [])
        p = subprocess.run(argv, cwd=cwd or self.repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        return p.returncode, p.stdout.decode("utf-8", "replace")

    def ran(self, name):
        return (self.marks / name).exists()


def reds(out):
    return [line.strip()[2:] for line in out.splitlines() if line.strip().startswith("✗ ")]


def assert_green(rc, out):
    assert rc == 0, out
    assert "PRECHECK GREEN (item mode; CI remains the full gate)" in out and "PRECHECK RED" not in out
    assert reds(out) == [], out
    for n in range(1, 10):
        assert f"── {n}/9 " in out, f"step {n} did not run:\n{out}"


def assert_red(rc, out, *reasons):
    """RED for exactly these reasons — a script that is always red, or red for another reason, does not pass."""
    assert rc == 1, out
    assert "PRECHECK RED — do not push" in out and "PRECHECK GREEN" not in out
    assert reds(out) == list(reasons), out


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.is_dir(), None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest(),
                   p.stat().st_mtime_ns) for p in root.rglob("*"))


@pytest.fixture
def bench(tmp_path):
    return Bench(tmp_path)


# ── the script itself ────────────────────────────────────────────────────────────────────────────────────────────────

def test_script_names_the_live_run_directory_only_as_the_default():
    text = PRECHECK.read_text()
    assert text.count("KY_ROOT/run") == 1 and 'KY_RUN="${KY_RUN:-$KY_ROOT/run}"' in text
    assert "precheck v2.1 " in text.splitlines()[1] and "KV3-B-PRECHECK" in text


# ── GREEN is earned ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_clean_code_diff_with_passing_test_is_green(bench):
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run()
    assert_green(rc, out)
    assert bench.ran("pass_a") and "✓ pytest t/test_pass_a.py" in out
    assert "✓ no frozen/forbidden paths" in out and "✓ no path of FROZEN_PATHS.txt in the diff" in out


def test_failing_test_is_red(bench):
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests="t/test_red.py")
    assert_red(rc, out, "pytest t/test_red.py")


def test_no_code_change_and_no_manifest_is_green(bench):
    bench.change("docs/readme.md")
    rc, out = bench.run(tests=None)
    assert_green(rc, out)
    assert "no code change and no test manifest" in out


# ── KY_RUN: the run directory ────────────────────────────────────────────────────────────────────────────────────────

def test_only_the_ky_run_manifest_runs_and_the_live_run_directory_is_untouched(bench):
    (bench.ky_root / "run" / "tests" / f"{ITEM}.txt").write_text("t/test_pass_a.py\n")
    (bench.ky_run / "tests" / f"{ITEM}.txt").write_text("t/test_pass_b.py\n")
    bench.change("t/new_module.py", "X = 1\n")
    before = snapshot(bench.ky_root)
    rc, out = bench.run(tests=None)
    assert_green(rc, out)
    assert bench.ran("pass_b") and not bench.ran("pass_a")
    assert snapshot(bench.ky_root) == before


def test_tests_env_wins_over_both_manifests(bench):
    (bench.ky_root / "run" / "tests" / f"{ITEM}.txt").write_text("t/test_pass_a.py\n")
    (bench.ky_run / "tests" / f"{ITEM}.txt").write_text("t/test_pass_b.py\n")
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests="t/test_pass_c.py")
    assert_green(rc, out)
    assert bench.ran("pass_c") and not bench.ran("pass_a") and not bench.ran("pass_b")


def test_ky_run_unset_uses_the_ky_root_run_manifest_as_before(bench):
    (bench.ky_root / "run" / "tests" / f"{ITEM}.txt").write_text("t/test_pass_a.py\n")
    (bench.ky_run / "tests" / f"{ITEM}.txt").write_text("t/test_pass_b.py\n")
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests=None, ky_run=None)
    assert_green(rc, out)
    assert bench.ran("pass_a") and not bench.ran("pass_b")


def test_code_diff_with_neither_tests_nor_a_manifest_under_ky_run_is_red(bench):
    (bench.ky_root / "run" / "tests" / f"{ITEM}.txt").write_text("t/test_pass_a.py\n")   # the live manifest is no fallback
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests=None)
    assert_red(rc, out, "this diff changes code but there is no explicit test manifest — export KY_ITEM=<item id> "
                        "(with run/tests/<ITEM>.txt) or TESTS")
    assert not bench.ran("pass_a")


def test_empty_tests_env_falls_through_to_the_ky_run_manifest(bench):
    (bench.ky_run / "tests" / f"{ITEM}.txt").write_text("t/test_pass_b.py\n")
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests="")
    assert_green(rc, out)
    assert bench.ran("pass_b")


def test_with_ky_run_set_a_missing_ky_root_is_neither_needed_nor_created(bench):
    shutil.rmtree(bench.ky_root)
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run()
    assert_green(rc, out)
    assert not bench.ky_root.exists()


@pytest.mark.parametrize("kind", ["relative", "missing", "file", "empty", "dot-relative"])
def test_ky_run_set_but_not_an_absolute_existing_directory_is_red_before_step_1(bench, kind):
    (bench.ky_root / "run" / "tests" / f"{ITEM}.txt").write_text("t/test_pass_a.py\n")
    (bench.repo / "relrun").mkdir()
    (bench.tmp / "afile").write_text("x")
    value = {"relative": "relrun", "missing": str(bench.tmp / "nowhere"), "file": str(bench.tmp / "afile"), "empty": "",
             "dot-relative": "./relrun"}[kind]
    bench.change("t/new_module.py", "X = 1\n")
    before = snapshot(bench.ky_root)
    rc, out = bench.run(tests=None, ky_run=value)
    assert rc == 1, out
    assert reds(out) == [f"KY_RUN is set but is not an absolute path of an existing directory: '{value}'"], out
    assert "PRECHECK RED — do not push" in out and "PRECHECK GREEN" not in out
    assert "── " not in out, "no step may run"
    assert not bench.ran("pass_a") and snapshot(bench.ky_root) == before
    assert not (bench.tmp / "nowhere").exists()


def test_migration_log_goes_under_ky_run(bench):
    bench.change("platform/migrations/901_x.sql", "select 1;\n")
    before = snapshot(bench.ky_root)
    rc, out = bench.run(KY_LANE="k9")
    assert_green(rc, out)
    assert "✓ migrate.ts applied pending migrations to ky_k9" in out
    assert "stub npx tsx scripts/migrate.ts" in (bench.ky_run / "precheck_migrate_k9.log").read_text()
    assert snapshot(bench.ky_root) == before


def test_migration_failure_names_the_log_under_ky_run(bench):
    bench.change("platform/migrations/901_x.sql", "select 1;\n")
    rc, out = bench.run(KY_LANE="k9", STUB_NPX_EXIT="1")
    assert_red(rc, out, f"migrate.ts failed on ky_k9 (see {bench.ky_run}/precheck_migrate_k9.log)")
    assert (bench.ky_run / "precheck_migrate_k9.log").is_file()


def test_migration_with_ky_lane_unset_is_red(bench):
    bench.change("platform/supabase/migrations/901_x.sql", "select 1;\n")
    rc, out = bench.run()
    assert_red(rc, out, "migration in diff but KY_LANE unset — cannot apply to a lane database")
    assert "migrate.ts" not in (bench.stub_log.read_text() if bench.stub_log.exists() else "")


def test_full_mode_heavy_lock_is_taken_under_ky_run(bench):
    bench.change("t/new_module.py", "X = 1\n")
    before = snapshot(bench.ky_root)
    rc, out = bench.run(mode=None)
    assert rc == 0 and reds(out) == [] and "PRECHECK GREEN (full mode; CI remains the full gate)" in out, out
    assert "✓ tsc platform-mcp" in out and "✓ vitest" in out and "skipped in --item mode" not in out
    assert (bench.ky_run / "precheck_heavy.lock").is_file()
    assert snapshot(bench.ky_root) == before


# ── step 9: the inline prohibitions are unchanged ────────────────────────────────────────────────────────────────────

INLINE_ALTERNATIVES = [
    "CLAUDECODE_BRIEF.md",
    "CLAUDE.md",
    ".codex/config.toml",
    ".github/workflows/ci.yml",
    "platform/src/lib/retrieval/registry/knowledge/entry.md",
    "platform/src/lib/purna/note.md",
    "00_ARCHITECTURE/briefs/nirmana/BRIEF.md",
    "00_ARCHITECTURE/briefs/suvarna/BRIEF.md",
    "00_ARCHITECTURE/briefs/sampurti/BRIEF.md",
    "00_ARCHITECTURE/briefs/purna_anvesana/BRIEF.md",
    f"{ORCH}/asset_runner.py",
    f"{ORCH}/runner.py",
    f"{ORCH}/staleness.py",
    f"{ORCH}/writers/__init__.py",
]


@pytest.mark.parametrize("path", INLINE_ALTERNATIVES)
def test_every_alternative_of_the_inline_pattern_is_still_refused(bench, path):
    """The test manifest names none of these paths: the inline pattern alone refuses them, so a short manifest relaxes nothing."""
    bench.change(path)
    rc, out = bench.run()
    assert_red(rc, out, INLINE_RED)
    assert "✓ no path of FROZEN_PATHS.txt in the diff" in out


@pytest.mark.parametrize("path", INLINE_ALTERNATIVES[:1] + INLINE_ALTERNATIVES[10:11])
def test_inline_pattern_refuses_a_committed_change_too(bench, path):
    bench.change(path)
    git(bench.repo, "commit", "-q", "-m", "lane change")
    rc, out = bench.run()
    assert_red(rc, out, INLINE_RED)


def test_workflow_file_is_allowed_for_k0a_0_only(bench):
    bench.change(".github/workflows/ci.yml")
    rc, out = bench.run(KY_ITEM="K0a-0")
    assert_green(rc, out)
    assert "✓ no frozen/forbidden paths" in out


def test_k0a_0_exception_covers_nothing_but_workflows(bench):
    bench.change(f"{ORCH}/runner.py")
    rc, out = bench.run(KY_ITEM="K0a-0")
    assert_red(rc, out, INLINE_RED)


@pytest.mark.parametrize("path", ["lane.env", "certs/server.pem", "certs/server.key", "ops/pgenv"])
def test_staged_credential_like_file_is_red(bench, path):
    bench.change(path)
    rc, out = bench.run()
    assert_red(rc, out, "credential-like file staged")


def test_ka_writer_changed_without_its_digest_file_is_red(bench):
    bench.change(f"{ORCH}/writers/ka_sample.py", "X = 1\n")
    rc, out = bench.run()
    assert_red(rc, out, "writer changed but nirmana-writer-digests.json not regenerated (CI provenance check)")


def test_ka_writer_changed_with_its_digest_file_is_green(bench):
    bench.change(f"{ORCH}/writers/ka_sample.py", "X = 1\n")
    bench.change("platform/python-sidecar/nirmana-writer-digests.json", "{}\n")
    rc, out = bench.run()
    assert_green(rc, out)
    assert "✓ writer digest regenerated with the writer change" in out


def test_unknown_test_path_type_is_red(bench):
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run(tests="docs/readme.md")
    assert_red(rc, out, "unknown test path type: docs/readme.md")


# ── step 9: the frozen manifest ──────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("how", ["staged", "unstaged", "committed", "deleted"])
def test_path_listed_in_the_manifest_is_refused_with_freeze(bench, how):
    if how == "deleted":
        git(bench.repo, "rm", "-q", "--", FROZEN_ENTRY)
    else:
        bench.change(FROZEN_ENTRY, stage=how != "unstaged")
    if how == "committed":
        git(bench.repo, "commit", "-q", "-m", "lane change")
    rc, out = bench.run()
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")
    assert "✓ no frozen/forbidden paths" in out, "outside the inline pattern: the manifest alone refuses it"


def test_manifest_and_inline_pattern_are_a_union(tmp_path):
    bench = Bench(tmp_path, manifest=f"{ORCH}/runner.py\n{FROZEN_ENTRY}\n")
    bench.change(f"{ORCH}/runner.py")
    bench.change(FROZEN_ENTRY)
    rc, out = bench.run()
    assert_red(rc, out, INLINE_RED, f"freeze: {FROZEN_ENTRY}", f"freeze: {ORCH}/runner.py")


def test_entry_is_an_exact_path_not_a_prefix_or_pattern(tmp_path):
    bench = Bench(tmp_path, manifest="docs/frozen_note.md\ndocs/a.b\n")
    for near in ("docs/frozen_note.md.bak", "docs/frozen_note", "more/docs/frozen_note.md", "docs/aXb"):
        bench.change(near)
    rc, out = bench.run()
    assert_green(rc, out)


def big_manifest(hit_at, entries=2400):
    """A valid manifest of several pipe buffers (64 KiB each), with FROZEN_ENTRY at the given place: more than one buffer follows a middle hit."""
    lines = [f"docs/filler/{n:04d}_{'x' * 60}.md" for n in range(entries)]
    lines.insert({"first": 0, "middle": entries // 2, "last": entries}[hit_at], FROZEN_ENTRY)
    text = "# frozen paths (large test manifest)\n" + "\n".join(lines) + "\n"
    assert len(text.encode()) > 2 * (65536 + 4096)
    return text


@pytest.mark.parametrize("hit_at", ["first", "middle", "last"])
def test_manifest_above_one_pipe_buffer_still_refuses_its_entry(tmp_path, hit_at):
    """Review round 1, B-01: the membership test must not depend on how much of the entry list a reader consumed."""
    bench = Bench(tmp_path, manifest=big_manifest(hit_at))
    bench.change(FROZEN_ENTRY)
    bench.change("t/new_module.py", "X = 1\n")
    rc, out = bench.run()
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")


def test_renaming_a_frozen_file_away_is_refused_with_a_manifest_above_one_pipe_buffer(tmp_path):
    bench = Bench(tmp_path, manifest=big_manifest("first"))
    git(bench.repo, "mv", FROZEN_ENTRY, "docs/moved_note.md")
    rc, out = bench.run()
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")


def test_manifest_above_one_pipe_buffer_refuses_nothing_else(tmp_path):
    bench = Bench(tmp_path, manifest=big_manifest("first"))
    for near in ("t/new_module.py", "docs/frozen_note.md.bak", "docs/filler/0000_x.md", "docs/filler/*", "docs/fro*", "docs/[f]rozen_note.md",
                 "docs/frozen_note?md", "docs\\frozen_note.md"):
        bench.change(near, "X = 1\n")
    rc, out = bench.run()
    assert_green(rc, out)
    assert "✓ no path of FROZEN_PATHS.txt in the diff" in out


@pytest.mark.parametrize("dup_of", ["first", "middle"])
def test_duplicate_entry_in_a_manifest_above_one_pipe_buffer_is_malformed(tmp_path, dup_of):
    text = big_manifest(dup_of) + FROZEN_ENTRY + "\n"
    bench = Bench(tmp_path, manifest=text)
    bench.change("docs/readme.md")
    rc, out = bench.run()
    assert_red(rc, out, f"frozen manifest {bench.manifest} holds another line — line {text.count(chr(10))}: a duplicate entry")
    assert "✓ no path of FROZEN_PATHS.txt in the diff" not in out


AWK_STUB = """#!/bin/bash
n=$(( $(cat "$AWK_COUNT" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$AWK_COUNT"
[ "$n" = "$AWK_FAIL_AT" ] && exit 2
exec /usr/bin/awk "$@"
"""


@pytest.mark.parametrize("fail_at,reason", [("1", "frozen manifest {m} could not be checked for duplicate entries"),
                                            ("2", "frozen manifest check could not compare the diff with {m}")])
def test_membership_tool_failure_is_red_not_no_match(bench, fail_at, reason):
    """A comparison that did not run is not a comparison that found nothing."""
    stub = bench.tmp / "bin" / "awk"
    stub.write_text(AWK_STUB)
    stub.chmod(0o755)
    bench.change(FROZEN_ENTRY)
    rc, out = bench.run(AWK_COUNT=str(bench.tmp / "awk.count"), AWK_FAIL_AT=fail_at)
    assert_red(rc, out, reason.format(m=bench.manifest))
    assert "✓ no path of FROZEN_PATHS.txt in the diff" not in out


def test_renaming_a_frozen_file_away_is_refused(bench):
    git(bench.repo, "mv", FROZEN_ENTRY, "docs/moved_note.md")
    rc, out = bench.run()
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")


def test_non_ascii_frozen_path_is_refused(tmp_path):
    bench = Bench(tmp_path, manifest="docs/काल.md\n")
    bench.change("docs/काल.md")
    rc, out = bench.run()
    assert_red(rc, out, "freeze: docs/काल.md")


def test_manifest_is_found_beside_the_script_when_called_by_a_relative_path(bench):
    bench.change(FROZEN_ENTRY)
    rc, out = bench.run(cwd=bench.repo / "docs", script="../fleet/precheck.sh")
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")


def test_no_environment_variable_relocates_or_disables_the_manifest(bench):
    decoy = bench.tmp / "decoy"
    decoy.mkdir()
    (decoy / "FROZEN_PATHS.txt").write_text("docs/unrelated.md\n")
    bench.change(FROZEN_ENTRY)
    rc, out = bench.run(KY_FLEET=str(decoy), KY_FROZEN_PATHS=str(decoy / "FROZEN_PATHS.txt"), FROZEN_PATHS=str(decoy / "FROZEN_PATHS.txt"),
                        KY_FROZEN="0", KY_SKIP_FROZEN="1", OLDPWD=str(decoy), BASH_SOURCE=str(decoy / "precheck.sh"))
    assert_red(rc, out, f"freeze: {FROZEN_ENTRY}")


def test_missing_manifest_is_red(tmp_path):
    bench = Bench(tmp_path, manifest=None)
    bench.change("docs/readme.md")
    rc, out = bench.run()
    assert_red(rc, out, f"frozen manifest {bench.manifest} is missing")


def test_manifest_that_is_a_directory_is_red(tmp_path):
    bench = Bench(tmp_path, manifest=None)
    bench.manifest.mkdir()
    bench.change("docs/readme.md")
    rc, out = bench.run()
    assert_red(rc, out, f"frozen manifest {bench.manifest} is not a regular file")


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads any file")
def test_unreadable_manifest_is_red(bench):
    bench.manifest.chmod(0)
    bench.change("docs/readme.md")
    try:
        rc, out = bench.run()
    finally:
        bench.manifest.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert_red(rc, out, f"frozen manifest {bench.manifest} is unreadable")


@pytest.mark.parametrize("content", [b"", b"\n\n", b"# only a comment\n\n#another\n"], ids=["empty", "blank", "comments"])
def test_manifest_without_entries_is_red(tmp_path, content):
    bench = Bench(tmp_path, manifest=content)
    bench.change("docs/readme.md")
    rc, out = bench.run()
    assert_red(rc, out, f"frozen manifest {bench.manifest} has no entries")


MALFORMED = {
    "glob-star": (b"docs/*.md\n", "line 1: a glob character"),
    "glob-question": (b"docs/a?.md\n", "line 1: a glob character"),
    "glob-bracket": (b"docs/[ab].md\n", "line 1: a glob character"),
    "leading-slash": (b"/docs/a.md\n", "line 1: a leading /"),
    "dot-segment": (b"./docs/a.md\n", "line 1: a . or .. segment"),
    "dot-segment-inside": (b"docs/./a.md\n", "line 1: a . or .. segment"),
    "dotdot-segment": (b"docs/../a.md\n", "line 1: a . or .. segment"),
    "dotdot-leading": (b"../a.md\n", "line 1: a . or .. segment"),
    "dotdot-trailing": (b"docs/..\n", "line 1: a . or .. segment"),
    "space": (b"docs/a b.md\n", "line 1: white space"),
    "trailing-space": (b"docs/a.md \n", "line 1: white space"),
    "tab": (b"docs/a.md\tx\n", "line 1: white space"),
    "blank-with-spaces": (b"docs/a.md\n  \n", "line 2: white space"),
    "indented-comment": (b"docs/a.md\n # note\n", "line 2: white space"),
    "crlf": (b"docs/a.md\r\n", "line 1: white space"),
    "duplicate": (b"docs/a.md\n# c\ndocs/b.md\ndocs/a.md\n", "line 4: a duplicate entry"),
    "directory": (b"docs/\n", "line 1: an empty path segment"),
    "empty-segment": (b"docs//a.md\n", "line 1: an empty path segment"),
    "byte-order-mark": (b"\xef\xbb\xbfdocs/a.md\n", "line 1: a byte-order mark"),
    "after-a-good-line": (b"docs/frozen_note.md\ndocs/*\n", "line 2: a glob character"),
    "not-utf8": (b"docs/\xff.md\n", "is not valid UTF-8"),
    "nul-byte": (b"docs/a\x00.md\n", "holds a NUL byte"),
    "no-final-line-feed": (b"docs/frozen_note.md\ndocs/a.md", "does not end with a line feed"),
}


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_malformed_manifest_is_red(tmp_path, case):
    content, reason = MALFORMED[case]
    bench = Bench(tmp_path, manifest=content)
    bench.change("docs/readme.md")
    rc, out = bench.run()
    sep = " " if not reason.startswith("line") else " holds another line — "
    assert_red(rc, out, f"frozen manifest {bench.manifest}{sep}{reason}")
    assert "✓ no path of FROZEN_PATHS.txt in the diff" not in out


def test_without_origin_main_the_frozen_check_is_red_not_skipped(bench):
    bench.change(FROZEN_ENTRY)
    git(bench.repo, "commit", "-q", "-m", "lane change")
    git(bench.repo, "update-ref", "-d", "refs/remotes/origin/main")
    rc, out = bench.run()
    assert_red(rc, out, "frozen manifest check could not list the diff against origin/main")
