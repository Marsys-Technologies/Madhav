"""The no-real-cloud guard blocks every way of launching gcloud/gsutil/bq/kubectl from a test and nothing else (the 2026-10-05 incident)."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

import no_real_cloud_guard as g


@pytest.mark.parametrize("cmd", [
    ["gcloud", "run", "jobs", "execute", "x"], ["/opt/homebrew/bin/gcloud", "run"], ["gsutil", "ls"], ["bq", "query"], ["kubectl", "get", "pods"],
    ["env", "NIRMANA_FORCE_EXECUTE=1", "gcloud", "run", "jobs", "execute"], ["timeout", "5", "gcloud", "x"],
    ["bash", "-c", "gcloud run jobs execute x"], ["sh", "-c", "echo hi; gcloud auth list"],
])
def test_a_cloud_command_is_blocked_as_argv(cmd):
    assert g.is_blocked(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.run(cmd, capture_output=True)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.Popen(cmd)


@pytest.mark.parametrize("cmd", ["gcloud run jobs execute x", "echo a && gcloud x", "(gcloud x)", "x | gsutil cp", "FOO=1 gcloud x", "`gcloud x`"])
def test_a_cloud_command_is_blocked_as_a_shell_string(cmd):
    assert g.is_blocked(cmd, True) and g.is_blocked(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        subprocess.run(cmd, shell=True, capture_output=True)
    with pytest.raises(g.RealCloudCommandAttempt):
        os.system(cmd)
    with pytest.raises(g.RealCloudCommandAttempt):
        os.popen(cmd)


def test_the_binding_time_of_the_caller_does_not_matter():
    """The incident: code that bound subprocess.run at import time. The guard sits under Popen, so a stored reference is blocked too."""
    run_bound_early = subprocess.run
    check_output_bound_early = subprocess.check_output
    with pytest.raises(g.RealCloudCommandAttempt):
        run_bound_early(["gcloud", "run", "jobs", "execute", "j"])
    with pytest.raises(g.RealCloudCommandAttempt):
        check_output_bound_early(["gcloud", "x"])


def test_exec_and_spawn_families_are_blocked():
    with pytest.raises(g.RealCloudCommandAttempt):
        os.execv("/usr/bin/true", ["gcloud", "x"])
    if hasattr(os, "posix_spawn"):
        with pytest.raises(g.RealCloudCommandAttempt):
            os.posix_spawn("/usr/bin/true", ["gcloud", "x"], {})


@pytest.mark.parametrize("cmd", [["echo", "gcloud"], ["git", "--version"], [sys.executable, "-c", "print('gcloud')"], ["bash", "-c", "echo hello"], ["true"]])
def test_other_commands_and_the_word_inside_arguments_are_untouched(cmd):
    assert not g.is_blocked(cmd)
    assert subprocess.run(cmd, capture_output=True).returncode == 0


def test_a_blocked_attempt_is_recorded_for_audits(tmp_path):
    rec = tmp_path / "attempts.jsonl"
    uninstall = g.install(str(rec))
    try:
        with pytest.raises(g.RealCloudCommandAttempt):
            subprocess.run(["gcloud", "x"])
    finally:
        uninstall()
    assert rec.exists() and '"gcloud"' in rec.read_text()


def test_uninstall_restores_the_originals_and_install_is_idempotent_in_effect():
    before = (subprocess.Popen.__init__, os.system, os.popen)
    uninstall = g.install()
    assert subprocess.Popen.__init__ is not before[0]
    uninstall()
    assert (subprocess.Popen.__init__, os.system, os.popen) == before
