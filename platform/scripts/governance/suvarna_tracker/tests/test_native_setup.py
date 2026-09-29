"""Tests for suvarna_tracker/runtime/native_setup.sh (NS.1-NS.4, NS.8-NS.9 automation).

The script is bash, not Python, so these tests drive it as a subprocess under
NATIVE_SETUP_SIMULATE=1: every command that would touch real macOS state (sysadminctl, dscl,
dseditgroup, chown, chmod, chflags, launchctl, pmset, defaults, visudo, security, install, tee to
/etc) is replaced inside the script by a logger that appends a redacted description to a log file
and flips a key in a flat state file, instead of running for real. Nothing in this test module ever
runs with sudo, creates a user, or modifies real system state — see the module docstring in
native_setup.sh for the harness contract.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1] / "runtime" / "native_setup.sh"
)


def _base_env(sim_log: Path, sim_state: Path, suvarna_home: Path, **extra: str) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "NATIVE_SETUP_SIMULATE": "1",
            "NATIVE_SETUP_SIM_LOG": str(sim_log),
            "NATIVE_SETUP_SIM_STATE": str(sim_state),
            "SUVARNA_HOME": str(suvarna_home),
            "NATIVE_SETUP_CONTROL_ROOT": str(suvarna_home / "control"),
            "NATIVE_SETUP_HOME_ROOT": str(suvarna_home / "fake_native_home"),
        }
    )
    env.update(extra)
    return env


def seed_state(sim_state: Path, **kv: str) -> None:
    lines = [f"{k}={v}" for k, v in kv.items()]
    existing = sim_state.read_text() if sim_state.exists() else ""
    sim_state.write_text(existing + "\n".join(lines) + ("\n" if lines else ""))


def read_state(sim_state: Path) -> dict:
    out = {}
    if not sim_state.exists():
        return out
    for line in sim_state.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def run_script(
    tmp_path: Path,
    args: list[str],
    *,
    as_root: bool = False,
    admin_ok: bool = True,
    home_exists: bool = True,
    fail_at: str | None = None,
    extra_seed: dict | None = None,
    stdin: str | None = None,
) -> tuple[subprocess.CompletedProcess, Path, Path, Path]:
    """Run native_setup.sh in simulate mode. Returns (result, sim_log, sim_state, suvarna_home)."""
    suvarna_home = tmp_path / "suvarna_home"
    suvarna_home.mkdir(parents=True, exist_ok=True)
    sim_log = tmp_path / "sim.log"
    sim_state = tmp_path / "sim.state"
    sim_log.touch()
    sim_state.touch()

    seed = {
        "admin_check_pass": "1" if admin_ok else "0",
        "suvarna_home_exists": "1" if home_exists else "0",
    }
    if extra_seed:
        seed.update(extra_seed)
    seed_state(sim_state, **seed)

    extra_env = {}
    if as_root:
        extra_env["NATIVE_SETUP_SIM_ROOT"] = "1"
    if fail_at:
        extra_env["NATIVE_SETUP_SIM_FAIL_AT"] = fail_at

    env = _base_env(sim_log, sim_state, suvarna_home, **extra_env)
    result = subprocess.run(
        ["bash", str(SCRIPT), *args],
        env=env,
        capture_output=True,
        text=True,
        input=stdin,
        timeout=30,
    )
    return result, sim_log, sim_state, suvarna_home


def log_lines(sim_log: Path) -> list[str]:
    return [l for l in sim_log.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------------------------
# Static checks
# ---------------------------------------------------------------------------------------------

def test_bash_syntax_is_valid():
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
def test_shellcheck_reports_no_errors():
    result = subprocess.run(
        ["shellcheck", "-S", "error", str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------------------------

def test_check_mode_is_default_when_not_root_and_changes_nothing(tmp_path):
    result, sim_log, sim_state, _ = run_script(tmp_path, [], as_root=False)
    assert result.returncode == 0, result.stderr
    assert log_lines(sim_log) == []  # no mutating command was ever issued


def test_check_mode_explicit_flag_changes_nothing(tmp_path):
    result, sim_log, sim_state, _ = run_script(tmp_path, ["--check"], as_root=False)
    assert result.returncode == 0, result.stderr
    assert log_lines(sim_log) == []


def test_check_reports_pending_before_apply_and_done_after(tmp_path):
    before, _, sim_state, home = run_script(tmp_path, ["--check"])
    assert "[pending] NS.1" in before.stdout

    apply_result, sim_log, sim_state, home = run_script(
        tmp_path, ["--apply"], as_root=True, extra_seed=read_state(sim_state)
    )
    assert apply_result.returncode == 0, apply_result.stderr

    after = subprocess.run(
        ["bash", str(SCRIPT), "--check"],
        env=_base_env(sim_log, sim_state, home),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "[done]    NS.1" in after.stdout


def test_root_with_no_flag_requires_explicit_mode(tmp_path):
    result, _, _, _ = run_script(tmp_path, [], as_root=True)
    assert result.returncode == 2
    assert "explicitly" in result.stderr


# ---------------------------------------------------------------------------------------------
# --apply: ordering, idempotency, safety guards
# ---------------------------------------------------------------------------------------------

def test_apply_refuses_if_not_admin(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--apply"], as_root=True, admin_ok=False)
    assert result.returncode != 0
    assert "not an administrator" in result.stdout
    assert log_lines(sim_log) == []


def test_apply_refuses_if_suvarna_home_missing(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--apply"], as_root=True, home_exists=False)
    assert result.returncode != 0
    assert "does not exist yet" in result.stdout
    assert log_lines(sim_log) == []


def test_apply_issues_expected_commands_in_order(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--apply"], as_root=True)
    assert result.returncode == 0, result.stderr
    lines = log_lines(sim_log)
    joined = "\n".join(lines)

    def idx(needle: str) -> int:
        for i, l in enumerate(lines):
            if needle in l:
                return i
        raise AssertionError(f"expected log line containing {needle!r}; got:\n{joined}")

    # NS.1: user before group before memberships.
    assert idx("sysadminctl -addUser suvarna") < idx("dseditgroup -o create")
    assert idx("dseditgroup -o create") < idx("dseditgroup -o edit -a Dev")
    assert idx("dseditgroup -o edit -a Dev") < idx("dseditgroup -o edit -a suvarna")

    # NS.2: broker user before its folder before the sudoers rule; sudoers validated before install.
    assert idx("sysadminctl -addUser _suvarnabuild") < idx("mkdir -p")
    assert idx("visudo -cf") < idx("install the checked sudoers rule")

    # NS.1/NS.2 happen before NS.4's folder ownership pass, which happens before NS.9's power pass.
    assert idx("dseditgroup -o edit -a suvarna") < idx("create + chown/chmod/ACL campaign folders")
    assert idx("create + chown/chmod/ACL campaign folders") < idx("pmset -c sleep 0 disksleep 0")


def test_apply_is_idempotent_second_run_issues_no_commands(tmp_path):
    first, sim_log, sim_state, home = run_script(tmp_path, ["--apply"], as_root=True)
    assert first.returncode == 0, first.stderr
    assert log_lines(sim_log) != []

    state_after_first = read_state(sim_state)
    sim_log.write_text("")  # clear the log only; keep the accumulated state

    second = subprocess.run(
        ["bash", str(SCRIPT), "--apply"],
        env=_base_env(sim_log, sim_state, home, NATIVE_SETUP_SIM_ROOT="1"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert second.returncode == 0, second.stderr
    assert log_lines(sim_log) == [], (
        "a second --apply on the same state must issue no commands; got:\n"
        + "\n".join(log_lines(sim_log))
    )
    assert "already" in second.stdout.lower()
    # State must not have regressed.
    assert read_state(sim_state).get("user_suvarna_exists") == state_after_first.get(
        "user_suvarna_exists"
    )


def test_simulated_failure_stops_and_prints_undo_hint(tmp_path):
    result, sim_log, sim_state, _ = run_script(
        tmp_path, ["--apply"], as_root=True, fail_at="NS.2"
    )
    assert result.returncode != 0
    assert "STOPPED at NS.2" in result.stderr
    assert "--undo" in result.stderr

    lines = log_lines(sim_log)
    joined = "\n".join(lines)
    assert "[SIMULATED FAILURE at NS.2]" in joined
    # Nothing from later steps (NS.4 folders, NS.9 power) should have run.
    assert "create + chown/chmod/ACL campaign folders" not in joined
    assert "pmset -c sleep 0 disksleep 0" not in joined
    # NS.1 (before the failing step) did complete.
    assert "sysadminctl -addUser suvarna" in joined


def test_simulated_failure_at_sudoers_validation_stops_before_install(tmp_path):
    result, sim_log, _, _ = run_script(
        tmp_path, ["--apply"], as_root=True, fail_at="NS.2-validate"
    )
    assert result.returncode != 0
    assert "STOPPED at NS.2" in result.stderr
    joined = "\n".join(log_lines(sim_log))
    assert "install the checked sudoers rule" not in joined


# ---------------------------------------------------------------------------------------------
# --undo
# ---------------------------------------------------------------------------------------------

def _fully_applied_state() -> dict:
    return {
        "user_suvarna_exists": "1",
        "group_suvarna-campaign_exists": "1",
        "member_suvarna-campaign_Dev": "1",
        "member_suvarna-campaign_suvarna": "1",
        "ns1_keychain_stored": "1",
        "user__suvarnabuild_exists": "1",
        "ns2_broker_dir_ready": "1",
        "ns2_sudoers_installed": "1",
        "ns2_used_uids": "300,301",
        "ns3_own_dirs_locked": "1",
        "ns3_pending_files": "",
        "ns4_folders_ready": "1",
        "ns4_decisions_moved": "1",
        "ns4_holds_ready": "1",
        "ns4_pgenv_ready": "1",
        "ns8_source_present_tracker": "1",
        "ns8_installed_tracker": "1",
        "ns8_running_tracker": "1",
        "ns9_power_ready": "1",
        "ns9_softwareupdate_ready": "1",
    }


def test_undo_reverses_apply(tmp_path):
    result, sim_log, sim_state, _ = run_script(
        tmp_path, ["--undo"], as_root=True, extra_seed=_fully_applied_state()
    )
    assert result.returncode == 0, result.stderr
    joined = "\n".join(log_lines(sim_log))

    assert "launchctl bootout" in joined
    assert "rm -f /etc/sudoers.d/suvarna-build" in joined
    assert "sysadminctl -deleteUser _suvarnabuild" in joined
    assert "sysadminctl -deleteUser suvarna" in joined
    assert "dseditgroup -o delete suvarna-campaign" in joined
    assert "ownership only" in joined or "ownership/ACL only" in joined

    state = read_state(sim_state)
    assert state["user_suvarna_exists"] == "0"
    assert state["user__suvarnabuild_exists"] == "0"
    assert state["group_suvarna-campaign_exists"] == "0"
    assert state["ns2_sudoers_installed"] == "0"
    assert state["ns8_installed_tracker"] == "0"

    # NS.3 (credential locking) is a one-way tightening — undo must not claim to reverse it.
    assert "chmod" not in joined.replace("chown", "")  # no chmod-based re-loosening logged
    assert "go-rwx" not in joined


def test_undo_on_already_clean_state_is_a_safe_noop(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--undo"], as_root=True)
    assert result.returncode == 0, result.stderr
    assert log_lines(sim_log) == []


# ---------------------------------------------------------------------------------------------
# --verify
# ---------------------------------------------------------------------------------------------

def test_verify_writes_pass_fail_json(tmp_path):
    result, sim_log, sim_state, home = run_script(
        tmp_path, ["--verify"], as_root=True, extra_seed=_fully_applied_state()
    )
    assert result.returncode == 0, result.stderr
    out = home / "evidence" / "launch" / "NS_VERIFY.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert data, "verify JSON must not be empty"
    assert all(v in ("PASS", "FAIL") for v in data.values())
    assert data["ns1_user_created"] == "PASS"
    assert data["ns2_sudo_rule_installed"] == "PASS"


def test_verify_flags_missing_setup_as_fail(tmp_path):
    result, sim_log, sim_state, home = run_script(tmp_path, ["--verify"], as_root=True)
    assert result.returncode == 0, result.stderr
    out = home / "evidence" / "launch" / "NS_VERIFY.json"
    data = json.loads(out.read_text())
    assert data["ns1_user_created"] == "FAIL"
    assert "FAILED" in result.stdout or "FAIL" in result.stdout


# ---------------------------------------------------------------------------------------------
# Secrets never appear on a logged command line
# ---------------------------------------------------------------------------------------------

def test_apply_never_logs_a_password(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--apply"], as_root=True)
    assert result.returncode == 0, result.stderr
    joined = sim_log.read_text()
    assert "-password " not in joined or "<redacted" in joined
    assert "add-generic-password" in joined
    assert "<redacted, generated password>" in joined
    # The literal flag used for the real command must never carry a value in the log.
    for line in log_lines(sim_log):
        if "add-generic-password" in line:
            assert "-w " not in line or "<redacted" in line


def test_github_token_helper_never_logs_the_token(tmp_path):
    secret = "FAKE-" + "-".join(["github", "fixture", "not", "real"])  # built at run time: no token-shaped literal in the source
    result, sim_log, _, _ = run_script(
        tmp_path, ["--github-token"], as_root=True, stdin=secret + "\n"
    )
    assert result.returncode == 0, result.stderr
    assert secret not in sim_log.read_text()
    assert secret not in result.stdout
    assert secret not in result.stderr
    assert "piped via stdin, not logged" in sim_log.read_text()


def test_claude_token_helper_never_logs_the_token(tmp_path):
    secret = "FAKE-" + "-".join(["claude", "fixture", "not", "real"])  # built at run time: no token-shaped literal in the source
    result, sim_log, _, _ = run_script(
        tmp_path, ["--claude-token"], as_root=True, stdin=secret + "\n"
    )
    assert result.returncode == 0, result.stderr
    assert secret not in sim_log.read_text()
    assert secret not in result.stdout
    assert secret not in result.stderr
    assert "not logged" in sim_log.read_text()


def test_token_helpers_refuse_without_root(tmp_path):
    result, sim_log, _, _ = run_script(tmp_path, ["--github-token"], as_root=False)
    assert result.returncode != 0
    assert log_lines(sim_log) == []
