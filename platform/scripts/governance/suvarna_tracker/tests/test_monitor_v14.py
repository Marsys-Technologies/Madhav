"""v1.4 additions to the Monitor (review pass 2): `isolation` (CODE-12), `decision_writers`
(CODE-13), `builder_scope` (CODE-15). No network, no real `suvarna-build`, no real separate OS
user — every external fact is injected via `Config`."""
import json
import os

from suvarna_tracker import monitor as M
from suvarna_tracker.decisions import append_decision

CHART_ID = M.BUILDER_CHART_ID


def cfg(tmp_path, **kw):
    home = kw.pop("home", str(tmp_path / "home"))
    return M.Config(home=home, **kw)


# ---- isolation (CODE-12, B1: the three N-25 outcomes) ----------------------------------------

def _decide_n25(c, detail, writer="strategic-suvarna"):
    append_decision(c.decisions_path, {"id": "N-25", "state": "decided", "writer": writer,
                                       "source": "Native, session 'X', 2026-09-29: 'ruled'", "detail": detail})


# -- not yet decided: unchanged "always warn" behaviour --------------------------------------

def test_isolation_not_decided_warns(tmp_path):
    """CODE-12: until N-25 is decided there is nothing to verify, so this check must never
    fabricate `ok` and must never `block` (that would make today's single-user environment
    permanently undispatchable for a gate it cannot yet satisfy)."""
    r = M.check_isolation(cfg(tmp_path))
    assert r.status == "warn"
    assert "N-25 not implemented" in r.detail


def test_isolation_names_the_current_user(tmp_path, monkeypatch):
    c = cfg(tmp_path, getuser_fn=lambda: "abhisek")
    r = M.check_isolation(c)
    assert "abhisek" in r.detail


def test_isolation_expected_user_configurable_via_config_field(tmp_path):
    c = cfg(tmp_path, getuser_fn=lambda: "abhisek", isolation_expected_user="suvarna")
    r = M.check_isolation(c)
    assert "suvarna" in r.detail and r.status == "warn"


def test_isolation_expected_user_configurable_via_env(tmp_path, monkeypatch):
    monkeypatch.setenv(M.ISOLATION_EXPECTED_USER_ENV, "suvarna")
    c = cfg(tmp_path, getuser_fn=lambda: "abhisek")
    r = M.check_isolation(c)
    assert "suvarna" in r.detail and r.status == "warn"


def test_isolation_is_in_check_names_and_run_checks(tmp_path):
    assert "isolation" in M.CHECK_NAMES
    results = M.run_checks(cfg(tmp_path))
    assert any(r.name == "isolation" and r.status == "warn" for r in results)


# -- decided declined / accepted-risk: measured fallback hardening (CODE-22, review pass 3
# disposition) — ok is earned, never given on the decision's own say-so -----------------------

class _FakeStat:
    def __init__(self, mode):
        self.st_mode = mode


def _declined_cfg(tmp_path, detail="outcome=no — the native accepts the risk of running as the native "
                                    "account for now", **overrides):
    # F3 (independent review): the isolation check now also confirms the swarm's own reader
    # credential is readable (real os.access — a fake, unwritten pgenv path would otherwise fail
    # this new requirement) and mode 600 (via the same isolation_stat_fn mock every other path uses
    # here). A real, readable file is created below so the default "everything passes" fixture
    # keeps meaning "everything passes" under the new requirement too.
    pgenv_path = tmp_path / "pgenv.sh"
    pgenv_path.write_text("# reader credential\n")
    os.chmod(pgenv_path, 0o600)
    kwargs = dict(getuser_fn=lambda: "abhisek", pgenv=str(pgenv_path),
                 isolation_stat_fn=lambda path: _FakeStat(0o100600),  # every path: mode 600
                 isolation_hash_fn=lambda path: "deadbeef")
    kwargs.update(overrides)
    c = cfg(tmp_path, **kwargs)
    os.makedirs(os.path.dirname(c.isolation_settings_baseline_path), exist_ok=True)
    with open(c.isolation_settings_baseline_path, "w", encoding="utf-8") as f:
        json.dump({p: "deadbeef" for p in c.isolation_settings_paths}, f)
    _decide_n25(c, detail)
    return c


def test_isolation_decided_no_with_hardened_fallback_is_ok(tmp_path):
    c = _declined_cfg(tmp_path)
    r = M.check_isolation(c)
    assert r.status == "ok" and "N-25 declined: fallback hardening verified" in r.detail


def test_isolation_decided_accepted_risk_phrasing_with_hardened_fallback_is_ok(tmp_path):
    """'accepted-risk' alone (no literal 'no') is still an unambiguous decline."""
    c = _declined_cfg(tmp_path, detail="outcome=no (accepted-risk): keep single-user for now, revisit after J1")
    r = M.check_isolation(c)
    assert r.status == "ok" and "fallback hardening verified" in r.detail


def test_isolation_decided_no_blocks_on_readable_dbenv_file(tmp_path):
    c = _declined_cfg(tmp_path, isolation_stat_fn=lambda path: _FakeStat(0o100644 if "dbenv" in path else 0o100600))
    r = M.check_isolation(c)
    assert r.status == "block" and "group- or world-readable" in r.detail and "dbenv" in r.detail


def test_isolation_decided_no_blocks_on_missing_dbenv_file(tmp_path):
    def stat_fn(path):
        if "dbenv" in path:
            raise OSError("no such file")
        return _FakeStat(0o100600)

    c = _declined_cfg(tmp_path, isolation_stat_fn=stat_fn)
    r = M.check_isolation(c)
    assert r.status == "block" and "could not be stat-ed" in r.detail


def test_isolation_decided_no_blocks_on_group_writable_decisions_log(tmp_path):
    c = _declined_cfg(tmp_path)
    c.isolation_stat_fn = lambda path: _FakeStat(0o100660 if path == c.decisions_path else 0o100600)
    r = M.check_isolation(c)
    assert r.status == "block" and "group- or world-writable" in r.detail


def test_isolation_decided_no_blocks_on_settings_hash_mismatch(tmp_path):
    c = _declined_cfg(tmp_path)
    c.isolation_hash_fn = lambda path: ("deadbeef" if path == c.isolation_settings_baseline_path
                                        else "mismatched-hash")
    r = M.check_isolation(c)
    assert r.status == "block" and "does not match its baseline hash" in r.detail


def test_isolation_decided_no_blocks_on_missing_baseline(tmp_path):
    c = _declined_cfg(tmp_path)
    c.isolation_hash_fn = lambda path: None
    r = M.check_isolation(c)
    assert r.status == "block" and "no settings baseline readable" in r.detail


def test_isolation_decided_unclear_detail_warns(tmp_path):
    """A decided line whose detail names neither an accept nor a decline must never be guessed at —
    same `warn` as not-yet-decided, but naming the record so a human can correct it."""
    c = cfg(tmp_path, getuser_fn=lambda: "abhisek")
    _decide_n25(c, "Discussed at length, revisit next session")
    r = M.check_isolation(c)
    assert r.status == "warn" and "outcome could not be read" in r.detail


# -- decided yes: measured (CODE-12's stat/access/hash checks, all injectable) ----------------

def _accepted_cfg(tmp_path, **overrides):
    # F3 (independent review): the isolation check now also confirms the swarm's own reader
    # credential is readable and mode 600 — the default fixture below reads it as such (readable
    # via isolation_access_fn, mode 600 via isolation_stat_fn) so "everything passes" still means
    # everything passes under the new requirement.
    pgenv_path = str(tmp_path / "pgenv.sh")
    kwargs = dict(getuser_fn=lambda: "suvarna",
                 isolation_native_user_fn=lambda: "abhisek",
                 pgenv=pgenv_path,
                 # nothing readable/writable by default, except the swarm's own reader credential
                 isolation_access_fn=lambda path, mode: mode == os.R_OK and path == pgenv_path,
                 isolation_stat_fn=lambda path: _FakeStat(0o100600),
                 isolation_hash_fn=lambda path: "deadbeef")
    kwargs.update(overrides)
    c = cfg(tmp_path, **kwargs)
    _decide_n25(c, "outcome=yes — yes to all three")
    return c


def test_isolation_decided_yes_all_measurements_pass_is_ok(tmp_path):
    c = _accepted_cfg(tmp_path, isolation_hash_fn=lambda path: "deadbeef")
    # the baseline file itself must be readable JSON for the "no baseline" branch not to fire
    os.makedirs(os.path.dirname(c.isolation_settings_baseline_path), exist_ok=True)
    with open(c.isolation_settings_baseline_path, "w", encoding="utf-8") as f:
        json.dump({p: "deadbeef" for p in c.isolation_settings_paths}, f)
    r = M.check_isolation(c)
    assert r.status == "ok" and "N-25 in force" in r.detail


def test_isolation_decided_yes_blocks_on_wrong_current_user(tmp_path):
    c = _accepted_cfg(tmp_path)
    c.getuser_fn = lambda: "someone-else"
    r = M.check_isolation(c)
    assert r.status == "block" and "not the configured swarm user" in r.detail


def test_isolation_decided_yes_blocks_when_current_user_is_the_native(tmp_path):
    c = cfg(tmp_path, getuser_fn=lambda: "abhisek", isolation_expected_user="abhisek",
           isolation_native_user_fn=lambda: "abhisek",
           isolation_access_fn=lambda path, mode: False)
    _decide_n25(c, "outcome=yes — yes to all three")
    r = M.check_isolation(c)
    assert r.status == "block" and "native's own account" in r.detail


def test_isolation_decided_yes_blocks_on_readable_credential_path(tmp_path):
    c = _accepted_cfg(tmp_path, isolation_access_fn=lambda path, mode: mode == os.R_OK and "dbenv" in path)
    r = M.check_isolation(c)
    assert r.status == "block" and "readable by" in r.detail and "dbenv" in r.detail


def test_isolation_decided_yes_blocks_on_writable_decisions_log(tmp_path):
    c = _accepted_cfg(tmp_path)
    c.isolation_access_fn = lambda path, mode: mode == os.W_OK and path == c.decisions_path
    r = M.check_isolation(c)
    assert r.status == "block" and "is writable by" in r.detail


def test_isolation_decided_yes_blocks_on_missing_baseline(tmp_path):
    c = _accepted_cfg(tmp_path)  # isolation_hash_fn returns "deadbeef" for everything, including
    c.isolation_hash_fn = lambda path: None  # ...but here the baseline itself is unreadable
    r = M.check_isolation(c)
    assert r.status == "block" and "no settings baseline readable" in r.detail


def test_isolation_decided_yes_blocks_on_settings_hash_mismatch(tmp_path):
    c = _accepted_cfg(tmp_path)
    calls = {"n": 0}

    def hash_fn(path):
        calls["n"] += 1
        if path == c.isolation_settings_baseline_path:
            return "baseline-file-hash"  # the baseline file itself is readable
        return "actual-hash-does-not-match"

    c.isolation_hash_fn = hash_fn
    os.makedirs(os.path.dirname(c.isolation_settings_baseline_path), exist_ok=True)
    with open(c.isolation_settings_baseline_path, "w", encoding="utf-8") as f:
        json.dump({p: "expected-hash" for p in c.isolation_settings_paths}, f)
    r = M.check_isolation(c)
    assert r.status == "block" and "does not match its baseline hash" in r.detail


# ---- decision_writers -------------------------------------------------------------------------

def test_decision_writers_ok_when_no_decisions_yet(tmp_path):
    c = cfg(tmp_path)
    r = M.check_decision_writers(c)
    assert r.status == "ok" and "no decisions" in r.detail


def test_decision_writers_ok_when_every_decided_line_is_strategic_suvarna(tmp_path):
    c = cfg(tmp_path)
    append_decision(c.decisions_path, {"id": "N-1", "state": "decided", "writer": "strategic-suvarna",
                                       "source": "Native, session 'X', 2026-09-29: 'yes'", "detail": "approved"})
    r = M.check_decision_writers(c)
    assert r.status == "ok"


def test_decision_writers_blocks_on_a_steward_written_decided_line(tmp_path):
    c = cfg(tmp_path)
    append_decision(c.decisions_path, {"id": "N-1", "state": "decided", "writer": "steward",
                                       "source": "Native, session 'X', 2026-09-29: 'yes'", "detail": "approved"})
    r = M.check_decision_writers(c)
    assert r.status == "block"
    assert "N-1" in r.detail and "steward" not in r.detail.split(":")[0]


def test_decision_writers_ignores_non_decided_states(tmp_path):
    c = cfg(tmp_path)
    append_decision(c.decisions_path, {"id": "N-1", "state": "delegated", "writer": "steward",
                                       "source": "Native, session 'X', 2026-09-29: 'defer'",
                                       "detail": "delegated", "delegated_to": "Y"})
    r = M.check_decision_writers(c)
    assert r.status == "ok"


def test_decision_writers_only_the_latest_line_per_id_counts(tmp_path):
    """A correction (a new line) supersedes an earlier one — an old steward-written line for an id
    later corrected by strategic-suvarna must not keep blocking."""
    c = cfg(tmp_path)
    append_decision(c.decisions_path, {"id": "N-1", "state": "decided", "writer": "steward",
                                       "source": "Native, session 'X', 2026-09-29: 'first'", "detail": "first"})
    append_decision(c.decisions_path, {"id": "N-1", "state": "decided", "writer": "strategic-suvarna",
                                       "source": "Native, session 'X', 2026-09-29: 'corrected'", "detail": "corrected"})
    r = M.check_decision_writers(c)
    assert r.status == "ok"


def test_decision_writers_uses_suvarna_decisions_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "custom_decisions.jsonl")
    monkeypatch.setenv("SUVARNA_DECISIONS", override)
    c = cfg(tmp_path)
    assert c.decisions_path == override


def test_decision_writers_is_in_check_names_and_run_checks(tmp_path):
    assert "decision_writers" in M.CHECK_NAMES
    results = M.run_checks(cfg(tmp_path))
    assert any(r.name == "decision_writers" for r in results)


# ---- builder_scope ----------------------------------------------------------------------------

def _write_identity(path, **overrides):
    identity = {"builder": {"principal_id": "builder-guest-1", "role": "guest", "status": "active",
                            "grants": [{"chart_id": CHART_ID, "permission": "build"}]}}
    identity.update(overrides)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(identity, f)


def test_builder_scope_warns_before_provisioning(tmp_path):
    """B2 (review pass 3): absent `builder_identity.json` must never read `ok` — that made E7.3 read
    done while E7.2 (provisioning) was still open. It is an honest, open gap: `warn`."""
    c = cfg(tmp_path)
    r = M.check_builder_scope(c)
    assert r.status == "warn"
    assert "not provisioned" in r.detail and "E7.2" in r.detail


def test_builder_scope_ok_when_preflight_matches_identity(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    preflight = json.dumps({"job_image_tag": "gcr.io/x:1", "deployed_sha": "abc",
                            "builder": {"principal_id": "builder-guest-1", "role": "guest", "status": "active",
                                       "grants": [{"chart_id": CHART_ID, "permission": "build"}]}})
    c.run_fn = lambda cmd, timeout=5: (0, preflight)
    r = M.check_builder_scope(c)
    assert r.status == "ok"


def test_builder_scope_blocks_on_missing_preflight_script(tmp_path):
    """CODE-15: a missing suvarna-build script blocks once builder_identity.json exists (unlike the
    detector-side reading of "not provisioned yet" as pending — a Monitor check runs continuously
    once dispatch could plausibly happen, so a script that vanished after identity was recorded is
    a real problem, not an expected pre-J1 state)."""
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)

    def boom(cmd, timeout=5):
        raise FileNotFoundError(f"[Errno 2] No such file or directory: {cmd[0]!r}")

    c.run_fn = boom
    r = M.check_builder_scope(c)
    assert r.status == "block" and "not found" in r.detail


def test_builder_scope_blocks_on_preflight_failure(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    c.run_fn = lambda cmd, timeout=5: (1, "connection refused")
    r = M.check_builder_scope(c)
    assert r.status == "block" and "preflight" in r.detail


def test_builder_scope_blocks_on_wrong_role(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    preflight = json.dumps({"builder": {"principal_id": "builder-guest-1", "role": "admin", "status": "active",
                                        "grants": [{"chart_id": CHART_ID, "permission": "build"}]}})
    c.run_fn = lambda cmd, timeout=5: (0, preflight)
    r = M.check_builder_scope(c)
    assert r.status == "block" and "role=" in r.detail


def test_builder_scope_blocks_on_extra_grant(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    preflight = json.dumps({"builder": {"principal_id": "builder-guest-1", "role": "guest", "status": "active",
                                        "grants": [{"chart_id": CHART_ID, "permission": "build"},
                                                   {"chart_id": "other-chart", "permission": "view"}]}})
    c.run_fn = lambda cmd, timeout=5: (0, preflight)
    r = M.check_builder_scope(c)
    assert r.status == "block" and "grants=" in r.detail


def test_builder_scope_blocks_on_mismatch_with_identity_file(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    preflight = json.dumps({"builder": {"principal_id": "a-different-builder", "role": "guest", "status": "active",
                                        "grants": [{"chart_id": CHART_ID, "permission": "build"}]}})
    c.run_fn = lambda cmd, timeout=5: (0, preflight)
    r = M.check_builder_scope(c)
    assert r.status == "block" and "does not match" in r.detail


def test_builder_scope_blocks_on_non_json_preflight(tmp_path):
    c = cfg(tmp_path)
    _write_identity(c.builder_identity_path)
    c.run_fn = lambda cmd, timeout=5: (0, "not json")
    r = M.check_builder_scope(c)
    assert r.status == "block" and "non-JSON" in r.detail


def test_builder_scope_is_in_check_names_and_run_checks(tmp_path):
    assert "builder_scope" in M.CHECK_NAMES
    results = M.run_checks(cfg(tmp_path))
    # No builder_identity.json in this fresh tmp_path home: warn (B2), never ok.
    assert any(r.name == "builder_scope" and r.status == "warn" for r in results)


# ---- run_tracker.sh (CODE-17) -------------------------------------------------------------------

def test_run_tracker_sh_defaults_nikasha_ref_to_campaign_nikasha_test():
    script_path = os.path.join(M.HERE, "run_tracker.sh")
    with open(script_path, encoding="utf-8") as f:
        content = f.read()
    assert 'export NIKASHA_REF="${NIKASHA_REF:-origin/campaign/nikasha-test}"' in content


def test_n25_outcome_needs_an_explicit_marker():
    """Free words never decide the outcome: 'yes; no bypass' is not a decline, and no marker is unclear."""
    assert M._classify_n25_outcome("yes; no bypass") == "unclear"
    assert M._classify_n25_outcome("outcome=yes; no bypass") == "accepted"
    assert M._classify_n25_outcome("OUTCOME = no, accepted risk") == "declined"
    assert M._classify_n25_outcome("outcome=yes then outcome=no") == "unclear"
    assert M._classify_n25_outcome("") == "unclear"
