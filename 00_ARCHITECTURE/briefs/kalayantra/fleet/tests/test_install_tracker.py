"""install_tracker.sh v1.2 (incident 2026-10-21 07:05Z): the live plan model comes from ONE source, a stale checkout is refused,
and the restart never leaves the tracker down silently.

Everything runs against a temporary KY_ROOT, HOME and git fixture (a bare origin, a pusher clone and the "campaign" clone the
installer reads) with a fake `launchctl` and `curl` first on PATH; nothing here touches /Users/Dev/kalayantra, a LaunchAgent,
a real tracker or the network. The installer's own timeouts are shrunk through its documented KY_* variables."""
import json
import os
import plistlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
INSTALLER = FLEET / "install_tracker.sh"
MODEL_REL = "00_ARCHITECTURE/control/kalayantra/plan_model.json"
FLEET_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet"
LIVE_CAMPAIGN = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
LABEL = "com.madhav.kalayantra.tracker"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}

FAKE_LAUNCHCTL = r'''#!/bin/bash
# state: $FAKE_STATE/loaded (service present) · lag (number of `print` calls that still report it after a bootout)
S="$FAKE_STATE"; echo "$1" >> "$S/calls.log"
case "$1" in
  print)
    if [ -f "$S/lag" ]; then n=$(cat "$S/lag"); if [ "$n" -gt 0 ]; then echo $((n-1)) > "$S/lag"; exit 0; fi; rm -f "$S/lag" "$S/loaded"; fi
    [ -f "$S/loaded" ] && exit 0; exit 113 ;;
  bootout)
    [ -f "$S/loaded" ] || exit 3
    rm -f "$S/health"; echo "${FAKE_BOOTOUT_LAG:-0}" > "$S/lag"; exit 0 ;;
  bootstrap)
    echo "$3" > "$S/bootstrapped_plist"
    if [ -f "$S/lag" ] || [ -f "$S/loaded" ]; then echo "Bootstrap failed: 5: Input/output error" >&2; exit 5; fi
    f="$S/bootstrap_failures_left"
    if [ -f "$f" ] && [ "$(cat "$f")" -gt 0 ]; then echo $(( $(cat "$f") - 1 )) > "$f"; echo "Bootstrap failed: 5: Input/output error" >&2; exit 5; fi
    touch "$S/loaded"; [ "${FAKE_HEALTH:-1}" = 1 ] && touch "$S/health"; exit 0 ;;
  *) exit 0 ;;
esac
'''
FAKE_CURL = r'''#!/bin/bash
[ -f "$FAKE_STATE/health" ] || exit 22
echo '{"ok": true, "engine_tick_age_s": 1, "model_error": null}'
'''


def run(args, cwd, env, check=True):
    r = subprocess.run(args, cwd=str(cwd), env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
    if check:
        assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r


class World:
    def __init__(self, tmp):
        self.tmp = Path(os.path.realpath(tmp))
        self.origin, self.pusher, self.camp = (self.tmp / n for n in ("origin.git", "pusher", "campaign"))
        self.root, self.home, self.state = self.tmp / "root", self.tmp / "home", self.tmp / "state"
        self.gov, self.fakebin = self.tmp / "gov", self.tmp / "fakebin"
        self.genv = {"PATH": "/usr/bin:/bin", "HOME": str(self.tmp), **GIT_ENV}
        run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], self.tmp, self.genv)
        run(["git", "clone", "-q", str(self.origin), str(self.pusher)], self.tmp, self.genv)
        (self.pusher / MODEL_REL).parent.mkdir(parents=True)
        (self.pusher / MODEL_REL).write_text('{"model": "live"}\n')
        shutil.copytree(FLEET / "bin", self.pusher / FLEET_REL / "bin")
        self.n = 0
        self.commit("seed")
        run(["git", "clone", "-q", str(self.origin), str(self.camp)], self.tmp, self.genv)
        pkg = self.gov / "pravaha_tracker"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "cli.py").write_text("print('stub')\n")
        self.fakebin.mkdir()
        for name, body in (("launchctl", FAKE_LAUNCHCTL), ("curl", FAKE_CURL)):
            (self.fakebin / name).write_text(body)
            (self.fakebin / name).chmod(0o755)
        self.state.mkdir()
        (self.root / "wt" / "campaign" / MODEL_REL).parent.mkdir(parents=True)     # the stale decoy the old installer read
        (self.root / "wt" / "campaign" / MODEL_REL).write_text('{"model": "STALE-DECOY"}\n')

    def commit(self, msg, model=False):
        """One commit on origin/main (via the pusher clone); `model` makes it change plan_model.json."""
        self.n += 1
        target = self.pusher / (MODEL_REL if model else "note_%d.txt" % self.n)
        target.write_text(("%s %d\n" % (msg, self.n)) if not model else '{"model": "v%d"}\n' % self.n)
        run(["git", "add", "-A"], self.pusher, self.genv)
        run(["git", "commit", "-q", "-m", "%s %d" % (msg, self.n)], self.pusher, self.genv)
        run(["git", "push", "-q", "origin", "main"], self.pusher, self.genv)

    def env(self, **extra):
        e = {"PATH": "%s:/usr/bin:/bin:/opt/homebrew/bin" % self.fakebin, "HOME": str(self.home), "KY_ROOT": str(self.root),
             "KY_SOURCE_REPO": str(self.camp), "FAKE_STATE": str(self.state), "KY_POLL_S": "0", "KY_BOOTOUT_WAIT_S": "5",
             "KY_HEALTH_WAIT_S": "3", **GIT_ENV}
        e.update(extra)
        return e

    def install(self, script=INSTALLER, **extra):
        return run(["/bin/bash", str(script), "--gov", str(self.gov)], self.tmp, self.env(**extra), check=False)

    @property
    def plist(self):
        return self.home / "Library" / "LaunchAgents" / (LABEL + ".plist")

    def calls(self, verb):
        log = self.state / "calls.log"
        return [v for v in (log.read_text().split() if log.exists() else []) if v == verb]

    def untouched(self):
        """Nothing the installer writes exists: no plist, no snapshot, no recorded package, no launchctl call."""
        return (not self.plist.exists() and not (self.root / "tracker_live").exists()
                and not (self.root / "run" / "TRACKER_GOV").exists() and not (self.state / "calls.log").exists())


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


def test_installer_parses():
    assert subprocess.run(["/bin/bash", "-n", str(INSTALLER)], capture_output=True, text=True).returncode == 0


def test_default_source_is_the_live_campaign_checkout_like_the_other_scripts():
    """One default for the whole campaign: executor.sh, finalize.sh, bin/ky and this installer name the same checkout."""
    text = INSTALLER.read_text()
    assert 'KY_SOURCE_REPO="${KY_SOURCE_REPO:-%s}"' % LIVE_CAMPAIGN in text
    for other in ("executor.sh", "finalize.sh"):
        assert "KY_SOURCE_REPO:-%s}" % LIVE_CAMPAIGN in (FLEET / other).read_text(), other
    assert 'CAMPAIGN = "%s"' % LIVE_CAMPAIGN in (FLEET / "bin" / "ky").read_text()
    code = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    assert not [ln for ln in code if "wt/campaign" in ln], "no stale wt/campaign path in executable lines"


def test_model_and_repo_both_come_from_the_source_checkout_not_the_stale_one(w):
    r = w.install()
    assert r.returncode == 0 and "ACCEPTED" in r.stdout, (r.stdout, r.stderr)
    env = plistlib.loads(w.plist.read_bytes())["EnvironmentVariables"]
    assert env["PRAVAHA_PLAN_MODEL"] == str(w.camp / MODEL_REL) and env["PRAVAHA_REPO"] == str(w.camp)
    receipt = json.loads((w.root / "run" / "TRACKER_INSTALL_RECEIPT.json").read_text())
    import hashlib
    assert receipt["model_sha256"] == hashlib.sha256((w.camp / MODEL_REL).read_bytes()).hexdigest()
    assert receipt["model_sha256"] != hashlib.sha256((w.root / "wt" / "campaign" / MODEL_REL).read_bytes()).hexdigest()


def test_env_override_moves_both_model_and_repo_together(w, tmp_path):
    other = tmp_path / "other_clone"
    run(["git", "clone", "-q", str(w.origin), str(other)], w.tmp, w.genv)
    assert w.install(KY_SOURCE_REPO=str(other)).returncode == 0
    env = plistlib.loads(w.plist.read_bytes())["EnvironmentVariables"]
    assert (env["PRAVAHA_PLAN_MODEL"], env["PRAVAHA_REPO"]) == (str(other / MODEL_REL), str(other))


def test_repo_behind_origin_by_the_limit_is_accepted_and_one_more_is_refused(w):
    for _ in range(20):
        w.commit("n")
    assert w.install().returncode == 0, "exactly KY_STALE_MAX_COMMITS behind is still current"
    w.commit("n")
    r = w.install()
    assert r.returncode == 1 and "E_TRACKER_SOURCE_STALE" in r.stderr and "21 commits behind" in r.stderr, r.stderr


def test_a_stale_checkout_is_refused_before_anything_is_written(w):
    for _ in range(30):
        w.commit("n")
    r = w.install()
    assert r.returncode == 1 and "E_TRACKER_SOURCE_STALE" in r.stderr, (r.stdout, r.stderr)
    assert w.untouched()


def test_the_limits_are_overridable_by_env(w):
    for _ in range(5):
        w.commit("n")
    assert w.install(KY_STALE_MAX_COMMITS="4").returncode == 1
    assert w.install(KY_STALE_MAX_COMMITS="5").returncode == 0


def test_model_changed_upstream_more_than_the_limit_is_refused_even_when_the_repo_is_nearly_current(w):
    for _ in range(3):
        w.commit("m", model=True)
    assert w.install().returncode == 0, "3 missing model commits is within KY_MODEL_MAX_COMMITS"
    w.commit("m", model=True)
    r = w.install()
    assert r.returncode == 1 and "E_TRACKER_MODEL_STALE" in r.stderr and "4 model commits" in r.stderr, r.stderr


def test_a_head_that_is_not_an_ancestor_of_origin_main_is_refused(w):
    (w.camp / "local.txt").write_text("not on main\n")
    run(["git", "add", "local.txt"], w.camp, w.genv)
    run(["git", "commit", "-q", "-m", "local only"], w.camp, w.genv)
    r = w.install()
    assert r.returncode == 1 and "E_TRACKER_SOURCE_DIVERGED" in r.stderr, r.stderr
    assert w.untouched()


def test_a_missing_model_or_a_non_git_source_is_refused_by_name(w, tmp_path):
    (w.camp / MODEL_REL).unlink()
    assert "E_TRACKER_SOURCE_MISSING" in w.install().stderr
    plain = tmp_path / "plain"
    (plain / MODEL_REL).parent.mkdir(parents=True)
    (plain / MODEL_REL).write_text("{}")
    r = w.install(KY_SOURCE_REPO=str(plain))
    assert r.returncode == 1 and "E_TRACKER_SOURCE_MISSING" in r.stderr
    assert w.untouched()


def test_origin_unreachable_is_refused_not_trusted(w):
    shutil.rmtree(w.origin)
    r = w.install()
    assert r.returncode == 1 and "E_TRACKER_SOURCE_FETCH" in r.stderr
    assert w.untouched()


def test_run_from_a_fleet_live_copy_without_bin_takes_the_wrappers_from_the_source(w, tmp_path):
    live = tmp_path / "fleet_live"
    live.mkdir()
    shutil.copyfile(INSTALLER, live / "install_tracker.sh")
    r = w.install(script=live / "install_tracker.sh")
    assert r.returncode == 0, (r.stdout, r.stderr)
    for name in ("ky", "kybrief"):
        assert (w.root / "bin" / name).read_bytes() == (FLEET / "bin" / name).read_bytes()


def test_no_wrappers_anywhere_is_a_named_refusal_before_any_write(w, tmp_path):
    live = tmp_path / "fleet_live"
    live.mkdir()
    shutil.copyfile(INSTALLER, live / "install_tracker.sh")
    shutil.rmtree(w.camp / FLEET_REL / "bin")
    r = w.install(script=live / "install_tracker.sh")
    assert r.returncode == 1 and "E_TRACKER_NO_WRAPPERS" in r.stderr
    assert w.untouched()


def started(w):
    return (w.state / "loaded").exists()


def test_bootstrap_waits_until_the_old_service_is_gone(w):
    (w.state / "loaded").touch()
    r = w.install(FAKE_BOOTOUT_LAG="3")
    assert r.returncode == 0 and "ACCEPTED" in r.stdout, (r.stdout, r.stderr)
    assert w.calls("bootstrap") == ["bootstrap"], "no retry needed: bootstrap was not attempted while the service was still loaded"
    assert w.calls("print"), "the installer asked launchd whether the service had disappeared"


def test_a_failed_bootstrap_is_retried_once_and_the_tracker_comes_up(w):
    (w.state / "bootstrap_failures_left").write_text("1")
    r = w.install()
    assert r.returncode == 0 and "ACCEPTED" in r.stdout and "retrying once" in r.stderr, (r.stdout, r.stderr)
    assert len(w.calls("bootstrap")) == 2 and started(w)


def test_two_failed_bootstraps_fail_loudly_and_do_not_try_a_third_time(w):
    (w.state / "bootstrap_failures_left").write_text("5")
    r = w.install()
    assert r.returncode != 0 and "E_TRACKER_BOOTSTRAP" in r.stderr and "DOWN" in r.stderr, (r.stdout, r.stderr)
    assert len(w.calls("bootstrap")) == 2


def test_no_health_200_within_the_timeout_is_a_nonzero_exit_with_a_named_error(w):
    r = w.install(FAKE_HEALTH="0")
    assert r.returncode != 0 and "E_TRACKER_DOWN" in r.stderr and "3s" in r.stderr, (r.stdout, r.stderr)
    assert not (w.root / "run" / "TRACKER_INSTALL_RECEIPT.json").exists(), "no receipt for a tracker that is down"


def test_a_service_that_never_disappears_fails_before_bootstrap(w):
    (w.state / "loaded").touch()
    r = w.install(FAKE_BOOTOUT_LAG="1000", KY_BOOTOUT_WAIT_S="3")
    assert r.returncode != 0 and "E_TRACKER_BOOTOUT" in r.stderr, (r.stdout, r.stderr)
    assert w.calls("bootstrap") == []


def plist_env(w):
    return plistlib.loads(w.plist.read_bytes())["EnvironmentVariables"]


def test_the_plist_carries_a_20_second_call_timeout_by_default(w):
    """Incident 2026-10-21 11:14Z: gh calls took ~6 s, above the tracker's built-in 5 s, so 115 branch_merged detectors timed out."""
    assert w.install(**{}).returncode == 0
    assert plist_env(w)["PRAVAHA_CALL_TIMEOUT_S"] == "20"


def test_the_call_timeout_is_overridable_by_the_installers_environment(w):
    assert w.install(PRAVAHA_CALL_TIMEOUT_S="45.5").returncode == 0
    assert plist_env(w)["PRAVAHA_CALL_TIMEOUT_S"] == "45.5"
    assert w.install(PRAVAHA_CALL_TIMEOUT_S="120").returncode == 0, "the tracker's MAX_CONFIGURED_S itself is allowed"
    assert plist_env(w)["PRAVAHA_CALL_TIMEOUT_S"] == "120"


@pytest.mark.parametrize("bad", ["121", "0", "-5", "abc", "20; x", "1e1", "<x/>"])
def test_a_call_timeout_the_tracker_would_reject_is_refused_before_anything_is_written(w, bad):
    r = w.install(PRAVAHA_CALL_TIMEOUT_S=bad)
    assert r.returncode == 1 and "E_TRACKER_CALL_TIMEOUT" in r.stderr, (r.stdout, r.stderr)
    assert w.untouched()


def test_the_installers_limit_matches_the_trackers_own_maximum():
    detectors = FLEET.parents[3] / "platform" / "scripts" / "governance" / "pravaha_tracker" / "detectors.py"
    assert re.search(r"^MAX_CONFIGURED_S = 120\.0$", detectors.read_text(), re.M)
    assert "<= 120" in INSTALLER.read_text()
