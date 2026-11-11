"""Desktop qualification fixtures exercise the production handshake parser."""

import copy
import hashlib
import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import schema_validator as validator


@pytest.fixture
def desktop():
    checked = datetime.now(timezone.utc) - timedelta(seconds=1)
    observation = validator.CodexDesktopQualification(
        observed_client="codex_work_desktop",
        observed_host="local",
        desktop_session_id="desktop-fixture",
        session_id="GOVERNANCE_FIXTURE",
        worktree_path="/fixture/madhav",
        validator_sha256=hashlib.sha256(Path(validator.__file__).read_bytes()).hexdigest(),
        coordination_commit="1" * 40,
        lease_id="L-FIXTURE",
        lease_status="live",
        lease_checked_at=checked,
        lease_expires_at=checked + timedelta(minutes=30),
        work_order_surface="00_ARCHITECTURE/briefs/fixture/WORK_ORDER.md",
        may_touch=("00_ARCHITECTURE/briefs/fixture/**",),
        must_not_touch=("platform/migrations/**", "99_ARCHIVE/**"),
        instruction_fingerprints=(("CLAUDE.md", "2" * 64), ("AGENTS.md", "3" * 64)),
        access_posture="verified",
        access_evidence_sha256="4" * 64,
    )
    handshake = {
        "session_id": observation.session_id,
        "cowork_thread_name": "Desktop synthetic qualification",
        "agent_name": "synthetic-model",
        "agent_version": "fixture",
        "tool": "Codex",
        "tool_profile": "codex-desktop",
        "desktop_session_id": observation.desktop_session_id,
        "worktree_path": observation.worktree_path,
        "step_number_or_layer": "fixture",
        "coordination": {
            "coordination_ref": "origin/campaign-coordination",
            "lease_id": observation.lease_id,
            "lease_status_verified": True,
            "lease_verified_at": checked.isoformat(),
            "remote_commit": observation.coordination_commit,
            "work_order_surface": observation.work_order_surface,
        },
        "cross_tool_state_read": {"cross_cutting_decision_register": True},
        "predecessor_session": "fixture-predecessor",
        "mandatory_reading_confirmation": [
            {"file": name, "fingerprint_sha256": digest} for name, digest in observation.instruction_fingerprints
        ],
        "canonical_artifact_fingerprint_check": [],
        "declared_scope": {
            "may_touch": list(observation.may_touch),
            "must_not_touch": list(observation.must_not_touch),
        },
        "mirror_pair_freshness_check": [],
        "native_directive_obligations": [],
        "red_team_due": False,
    }
    return handshake, observation


def validate(handshake, observation=None):
    return validator.validate_handshake_yaml(
        json.dumps({"session_open": handshake}), trusted_desktop_qualification=observation
    )


def assert_desktop_denied(handshake, observation=None):
    violations = validate(handshake, observation)
    assert validator.compute_exit_code(violations) == 1
    assert "handshake_codex_desktop_qualification_invalid" in {row.rule for row in violations}


def test_matching_independent_desktop_observations_qualify(desktop):
    assert validate(*desktop) == []


def test_yaml_claims_cannot_qualify_desktop(desktop):
    handshake, _ = desktop
    handshake["trusted_desktop_qualification"] = {"startup_verified": True, "access_posture": "verified"}
    assert_desktop_denied(handshake)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observed_client", "codex-cli"),
        ("observed_host", "remote"),
        ("desktop_session_id", "different-desktop-session"),
        ("session_id", "DIFFERENT_GOVERNANCE_SESSION"),
        ("worktree_path", "/fixture/other-worktree"),
        ("validator_sha256", "0" * 64),
        ("coordination_commit", "0" * 40),
        ("lease_id", "L-OTHER"),
        ("lease_status", "superseded"),
        ("lease_status", "unverified"),
        ("work_order_surface", "foreign-work-order.md"),
        ("may_touch", ("platform/**",)),
        ("must_not_touch", ("99_ARCHIVE/**",)),
        ("instruction_fingerprints", (("CLAUDE.md", "0" * 64),)),
        ("access_posture", "unverified"),
        ("access_evidence_sha256", ""),
    ],
)
def test_independent_desktop_mismatch_denied(desktop, field, value):
    handshake, observation = desktop
    assert_desktop_denied(handshake, replace(observation, **{field: value}))


@pytest.mark.parametrize("path", ["fixture/madhav", "/fixture/a/../madhav", "/fixture//madhav", "//fixture/madhav"])
def test_invalid_worktree_denied_even_when_claim_matches(desktop, path):
    handshake, observation = desktop
    handshake["worktree_path"] = path
    assert_desktop_denied(handshake, replace(observation, worktree_path=path))


@pytest.mark.parametrize("delta", [timedelta(minutes=-11), timedelta(minutes=1)])
def test_stale_or_future_readback_denied_even_when_claim_matches(desktop, delta):
    handshake, observation = desktop
    checked_at = observation.lease_checked_at + delta
    handshake["coordination"]["lease_verified_at"] = checked_at.isoformat()
    assert_desktop_denied(handshake, replace(observation, lease_checked_at=checked_at))


def test_expired_lease_denied(desktop):
    handshake, observation = desktop
    assert_desktop_denied(handshake, replace(observation, lease_expires_at=observation.lease_checked_at))


@pytest.mark.parametrize("tool", ["Claude Code", "Kimi Code"])
def test_desktop_identifier_rejects_other_tools(desktop, tool):
    handshake, observation = desktop
    handshake["tool"] = tool
    assert_desktop_denied(handshake, observation)


@pytest.mark.parametrize("profile", ["madhav-safe", "madhav-parity"])
def test_legacy_cli_profiles_remain_compatible_but_not_for_observed_desktop(desktop, profile):
    handshake, observation = desktop
    handshake["tool_profile"] = profile
    del handshake["desktop_session_id"]
    assert validate(handshake) == []
    assert_desktop_denied(handshake, observation)


@pytest.mark.parametrize("profile", ["Codex desktop (actual client; no legacy profile inferred)", "managed", "arbitrary", None])
def test_original_profile_failures_are_retained(desktop, profile):
    handshake, _ = desktop
    handshake["tool_profile"] = profile
    violations = validate(handshake)
    assert validator.compute_exit_code(violations) == 1
    assert [row.rule for row in violations] == ["handshake_codex_profile_invalid"]


@pytest.mark.parametrize(
    ("key", "value", "rule", "exit_code"),
    [
        ("coordination", {"lease_status_verified": False}, "handshake_coordination_lease_unverified", 1),
        ("cross_tool_state_read", {"cross_cutting_decision_register": False}, "handshake_ccd_register_not_confirmed", 1),
        ("declared_scope", {"must_not_touch": []}, "handshake_must_not_touch_empty", 2),
        ("canonical_artifact_fingerprint_check", [{"match": False}], "handshake_fingerprint_mismatch", 1),
    ],
)
def test_desktop_cannot_relax_existing_guards(desktop, key, value, rule, exit_code):
    handshake, observation = desktop
    if isinstance(handshake[key], dict):
        handshake[key].update(value)
    else:
        handshake[key] = value
    assert rule in {row.rule for row in validate(handshake, observation)}
    cli = copy.deepcopy(handshake)
    cli["tool_profile"] = "madhav-safe"
    assert validator.compute_exit_code(validate(cli)) == exit_code
    assert [row.rule for row in validate(cli)] == [rule]


def test_retired_mirror_rows_remain_compatibility_fields(desktop):
    handshake, observation = desktop
    handshake["mirror_pair_freshness_check"] = [{"stale": True}]
    assert validate(handshake, observation) == []
    del handshake["mirror_pair_freshness_check"]
    assert [row.rule for row in validate(handshake, observation)] == [
        "handshake_field_missing[mirror_pair_freshness_check]"
    ]
