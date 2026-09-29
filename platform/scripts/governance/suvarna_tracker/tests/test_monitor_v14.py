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


# ---- isolation ------------------------------------------------------------------------------

def test_isolation_always_warns_never_ok_never_block(tmp_path):
    """CODE-12: until N-25 lands there is nothing to verify, so this check must never fabricate
    `ok` and must never `block` (that would make today's single-user environment permanently
    undispatchable for a gate it cannot yet satisfy)."""
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


def test_builder_scope_ok_before_provisioning(tmp_path):
    c = cfg(tmp_path)
    r = M.check_builder_scope(c)
    assert r.status == "ok" and "no builder identity" in r.detail


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
    assert any(r.name == "builder_scope" and r.status == "ok" for r in results)


# ---- run_tracker.sh (CODE-17) -------------------------------------------------------------------

def test_run_tracker_sh_defaults_nikasha_ref_to_campaign_nikasha_test():
    script_path = os.path.join(M.HERE, "run_tracker.sh")
    with open(script_path, encoding="utf-8") as f:
        content = f.read()
    assert 'export NIKASHA_REF="${NIKASHA_REF:-origin/campaign/nikasha-test}"' in content
