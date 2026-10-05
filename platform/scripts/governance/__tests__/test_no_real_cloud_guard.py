"""The no-real-cloud guard blocks every way of launching gcloud/gsutil/bq/kubectl (and write-capable gh) from a test and nothing else (the 2026-10-05 incident).

Every blocked attempt raises RealCloudCommandAttempt (a BaseException) and is COUNTED: the conftest's autouse fixture fails any test whose run recorded an attempt, even when
the code under test swallowed the exception. This file triggers the guard on purpose, so its own autouse fixture acknowledges what it provoked.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

import no_real_cloud_guard as g

HERE = pathlib.Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def _this_file_provokes_the_guard_on_purpose():
    yield
    g.acknowledge()                    # runs before the conftest fixture's check (torn down first)


@pytest.mark.parametrize("cmd", [
    ["gcloud", "run", "jobs", "execute", "x"], ["/opt/homebrew/bin/gcloud", "run"], ["gsutil", "ls"], ["bq", "query"], ["kubectl", "get", "pods"],
    ["env", "NIRMANA_FORCE_EXECUTE=1", "gcloud", "run", "jobs", "execute"], ["timeout", "5", "gcloud", "x"], ["sudo", "-n", "gcloud", "x"],
    ["nohup", "gcloud", "x"], ["nice", "-n", "5", "gcloud", "x"], ["xargs", "gcloud", "x"], ["env", "-i", "A=1", "timeout", "5s", "gsutil", "ls"],
    ["bash", "-c", "gcloud run jobs execute x"], ["sh", "-c", "echo hi; gcloud auth list"], ["bash", "-lc", "cd x && /opt/google/bin/gcloud run"],
    ["sh", "-c", "'gcloud' run"], ["bash", "/x/bin/gcloud", "run"], ["bash", "-c", "env A=1 timeout 3 gcloud x"], ["sh", "-c", "sh -c 'gcloud x'"],
    ["A=1", "gcloud", "x"],
])
def test_a_cloud_command_is_blocked_as_argv(cmd):
    assert g.is_blocked(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.run(cmd, capture_output=True)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.Popen(cmd)


@pytest.mark.parametrize("cmd", ["gcloud run jobs execute x", "echo a && gcloud x", "(gcloud x)", "x | gsutil cp", "FOO=1 gcloud x", "`gcloud x`", "echo $(gcloud x)",
                                 "cd x && /opt/google/bin/gcloud run", "'gcloud' run", "true; gcloud x", "false || gsutil ls", "echo a\ngcloud x",
                                 "if true; then gcloud x; fi", "timeout 5 gcloud x", "xargs gcloud x", "ls | xargs -n1 gsutil", "nohup bq query &"])
def test_a_cloud_command_is_blocked_as_a_shell_string(cmd):
    assert g.is_blocked(cmd, True) and g.is_blocked(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.run(cmd, shell=True, capture_output=True)
    with pytest.raises(g.RealCloudCommandAttempt):
        os.system(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        os.popen(cmd)


@pytest.mark.parametrize("cmd", [
    ["echo", "gcloud"], ["grep", "-r", "gcloud", "."], ["git", "log", "--grep", "gcloud"], ["timeout", "5", "git", "log", "--grep", "gcloud"], ["command", "-v", "gcloud"],
    ["bash", "-c", "echo gcloud"], ["bash", "-c", "grep -r gcloud . | wc -l"], ["sh", "-c", "command -v gcloud || true"], ["env", "FOO=gcloud", "echo", "x"],
    ["python3", "-c", "print('gcloud')"], ["cat", "gcloud.txt"], ["ls", "/opt/homebrew/bin/gcloud-completion"], ["gh", "pr", "view", "1"], ["gh", "api", "repos/x/y"],
    ["gh", "run", "list"], ["gh", "workflow", "list"], ["git", "status"], ["psql", "--version"],
])
def test_a_command_that_only_mentions_the_name_is_not_blocked(cmd):
    assert not g.is_blocked(cmd)


@pytest.mark.parametrize("cmd", [
    ["gh", "workflow", "run", "ci.yml"], ["gh", "pr", "merge", "1", "--auto"], ["gh", "pr", "create", "--title", "x"], ["gh", "run", "rerun", "1"],
    ["gh", "api", "-X", "POST", "repos/x/y/dispatches"], ["gh", "api", "--method", "DELETE", "repos/x/y"], ["gh", "api", "repos/x/y/issues", "-f", "title=x"],
    ["gh", "api", "--method=PUT", "x"], ["gh", "api", "-XPATCH", "x"], ["gh", "release", "create", "v1"], ["gh", "secret", "set", "X"],
    ["env", "GH_TOKEN=x", "gh", "pr", "merge", "1"],
])
def test_a_write_capable_gh_call_is_blocked(cmd):
    assert g.is_blocked(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.Popen(cmd)


def test_the_executable_argument_is_checked_too():
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.Popen(["harmless", "x"], executable="/opt/google-cloud-sdk/bin/gcloud")


def test_the_binding_time_of_the_caller_does_not_matter():
    """The incident: code that bound subprocess.run at import time. The guard sits under Popen, so a stored reference is blocked too."""
    run_bound_early = subprocess.run
    check_output_bound_early = subprocess.check_output
    for f in (run_bound_early, check_output_bound_early):
        with pytest.raises(g.RealCloudCommandAttempt):
            f(["gcloud", "run", "jobs", "execute", "x"])


def test_the_guard_error_cannot_be_swallowed_by_a_broad_except():
    assert not issubclass(g.RealCloudCommandAttempt, Exception) and issubclass(g.RealCloudCommandAttempt, BaseException)
    swallowed = []
    try:
        try:
            subprocess.run(["gcloud", "x"])
        except Exception:                                                 # noqa: BLE001 (the exact pattern that would hide it)
            swallowed.append(1)
    except g.RealCloudCommandAttempt:
        pass
    assert swallowed == []


@pytest.mark.parametrize("name,call", [
    ("execv", lambda: os.execv("/usr/bin/env", ["gcloud", "x"])), ("execve", lambda: os.execve("/usr/bin/env", ["gcloud"], {})),
    ("execvp", lambda: os.execvp("gcloud", ["gcloud", "x"])), ("execvpe", lambda: os.execvpe("gcloud", ["gcloud"], {})),
    ("execl", lambda: os.execl("/opt/homebrew/bin/gcloud", "gcloud", "x")), ("execlp", lambda: os.execlp("gcloud", "gcloud", "x")),
    ("execle", lambda: os.execle("/opt/homebrew/bin/gcloud", "gcloud", {})), ("execlpe", lambda: os.execlpe("gsutil", "gsutil", {})),
    ("spawnv", lambda: os.spawnv(os.P_NOWAIT, "/opt/homebrew/bin/gcloud", ["gcloud", "x"])), ("spawnve", lambda: os.spawnve(os.P_NOWAIT, "/opt/x/gcloud", ["gcloud"], {})),
    ("spawnvp", lambda: os.spawnvp(os.P_NOWAIT, "gcloud", ["gcloud", "x"])), ("spawnvpe", lambda: os.spawnvpe(os.P_NOWAIT, "bq", ["bq"], {})),
    ("spawnl", lambda: os.spawnl(os.P_NOWAIT, "/opt/homebrew/bin/gcloud", "gcloud", "x")), ("spawnlp", lambda: os.spawnlp(os.P_NOWAIT, "kubectl", "kubectl", "get")),
    ("spawnle", lambda: os.spawnle(os.P_NOWAIT, "/opt/x/gcloud", "gcloud", {})), ("spawnlpe", lambda: os.spawnlpe(os.P_NOWAIT, "gsutil", "gsutil", {})),
    ("posix_spawn", lambda: os.posix_spawn("/opt/homebrew/bin/gcloud", ["gcloud", "x"], {})), ("posix_spawnp", lambda: os.posix_spawnp("gcloud", ["gcloud"], {})),
])
def test_every_os_exec_spawn_and_posix_spawn_form_is_blocked_with_its_own_signature(name, call):
    if not hasattr(os, name):
        pytest.skip(f"os.{name} does not exist here")
    with pytest.raises(g.RealCloudCommandAttempt):
        call()


def test_a_harmless_spawn_still_runs():
    pid = os.spawnv(os.P_NOWAIT, sys.executable, [sys.executable, "-c", "pass"])
    assert os.waitpid(pid, 0)[1] == 0
    assert subprocess.run([sys.executable, "-c", "print('ok')"], capture_output=True, text=True).stdout.strip() == "ok"
    assert subprocess.run("echo gcloud", shell=True, capture_output=True, text=True).stdout.strip() == "gcloud"


def test_attempts_are_counted_and_recorded(tmp_path):
    before = g.attempt_count()
    rec = tmp_path / "rec.jsonl"
    un = g.install(record_path=str(rec), stubs=False)
    try:
        with pytest.raises(g.RealCloudCommandAttempt):
            subprocess.run(["gcloud", "run", "x"])
    finally:
        un()
    assert g.attempt_count() == before + 1 and "gcloud" in rec.read_text()


def test_a_child_process_that_the_patch_cannot_see_still_cannot_reach_a_real_cloud(tmp_path):
    """The stubs: a python child (no in-process patch) running `gcloud` through the shell finds the exit-97 stub FIRST on PATH, with an empty CLOUDSDK_CONFIG."""
    out = subprocess.run([sys.executable, "-c", "import subprocess;print(subprocess.run('gcloud auth list', shell=True).returncode)"],
                         capture_output=True, text=True)
    assert out.stdout.strip() == "97" and "blocked while tests run" in out.stderr
    cfg = subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('CLOUDSDK_CONFIG',''))"], capture_output=True, text=True).stdout.strip()
    assert cfg and os.path.isdir(cfg) and os.listdir(cfg) == []
    first = os.environ["PATH"].split(os.pathsep)[0]
    assert sorted(os.listdir(first)) == ["bq", "gcloud", "gsutil", "kubectl"]


def test_nested_installs_restore_in_order_including_path_and_config():
    path0, cfg0 = os.environ["PATH"], os.environ.get("CLOUDSDK_CONFIG")
    orig = subprocess.Popen.__init__
    un = g.install()
    assert subprocess.Popen.__init__ is not orig and os.environ["PATH"] != path0
    un()
    assert subprocess.Popen.__init__ is orig and os.environ["PATH"] == path0 and os.environ.get("CLOUDSDK_CONFIG") == cfg0


def _nested_pytest(tmp_path, test_body: str) -> subprocess.CompletedProcess:
    (tmp_path / "conftest.py").write_text(textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(HERE.parent)!r})
        from no_real_cloud_pytest import *   # noqa
    """))
    (tmp_path / "test_x.py").write_text(textwrap.dedent(test_body))
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path / "test_x.py")], capture_output=True, text=True, env=env, cwd=tmp_path)


def test_a_swallowed_attempt_still_fails_the_test(tmp_path):
    r = _nested_pytest(tmp_path, """
        import subprocess
        def test_swallows():
            try:
                subprocess.run(["gcloud", "run", "jobs", "execute", "x"])
            except BaseException:
                pass
    """)
    assert r.returncode != 0 and "real cloud command attempt" in (r.stdout + r.stderr)


def test_an_acknowledged_attempt_passes_and_a_clean_test_passes(tmp_path):
    r = _nested_pytest(tmp_path, """
        import subprocess, pytest
        import no_real_cloud_guard as g
        def test_expected(acknowledge_attempts):
            acknowledge_attempts(1)
            with pytest.raises(g.RealCloudCommandAttempt):
                subprocess.run(["gsutil", "ls"])
        def test_clean():
            assert subprocess.run(["echo", "hi"], capture_output=True).returncode == 0
    """)
    assert r.returncode == 0, r.stdout + r.stderr
