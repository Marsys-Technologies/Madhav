"""test_f154_ekv_f91_surface_profiles.py — F-154 prove-it-can-fail gate.

F-154: ekv_controls.py::_check_f91() statted `platform/src/generated/projections/
mcp_surface_profiles.generated.ts` — a path that has never existed (the real
platform-side projection artifact at that directory is the `.json` sibling, not a
`.ts` file). Because the guard was `if not profiles_file.exists(): return SKIP`, the
control returned SKIP for its entire life — it could never FAIL, a CLAUDE.md §N.8
gate-that-cannot-fail defect. Compounding it: no CI workflow invokes ekv_controls.py
at all, so this was never even a live green signal on a dashboard — a dormant control
statting a path that never existed.

Fix: point the control at the real artifact that actually gates MCP tool-catalog
serving — `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` (confirmed to
exist, built by mcp_surface_profile_builder.ts from the live retrieval registry) — and
change the missing-artifact outcome from SKIP to FAIL. Also parameterize the path
(`profiles_file` kwarg) so it has an injection point for tests, mirroring the reason
the old inline module-level constant could never be tested.

These tests prove the fixed check CAN fail (mutation-checked: reverting the artifact
path change makes `test_default_path_points_at_real_existing_file` fail against the
real repo tree; reverting the SKIP->FAIL change makes
`test_missing_artifact_is_fail_not_skip` fail).

Run:
  python -m pytest platform/scripts/governance/__tests__/test_f154_ekv_f91_surface_profiles.py -v
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ekv_controls  # noqa: E402


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


# ── The wrong-path regression the finding names ──────────────────────────────

def test_default_path_no_longer_points_at_the_never_existed_location():
    """The old path (platform/src/generated/projections/*.ts) never existed and must
    not be reintroduced as the default."""
    dead_path = REPO_ROOT / "platform" / "src" / "generated" / "projections" / "mcp_surface_profiles.generated.ts"
    assert ekv_controls.DEFAULT_MCP_SURFACE_PROFILES_PATH != dead_path
    assert not dead_path.exists(), (
        "This path was never supposed to exist (that's F-154's whole finding) — if it "
        "now exists, re-evaluate whether the control should point here after all."
    )


def test_default_path_points_at_real_existing_file():
    """The new default must resolve to a real, existing artifact in this checkout."""
    assert ekv_controls.DEFAULT_MCP_SURFACE_PROFILES_PATH.exists(), (
        f"DEFAULT_MCP_SURFACE_PROFILES_PATH does not exist: "
        f"{ekv_controls.DEFAULT_MCP_SURFACE_PROFILES_PATH}"
    )
    assert ekv_controls.DEFAULT_MCP_SURFACE_PROFILES_PATH == (
        REPO_ROOT / "platform-mcp" / "src" / "generated" / "mcp_surface_profiles.generated.ts"
    )


# ── The can-fail proof ───────────────────────────────────────────────────────

def test_missing_artifact_is_fail_not_skip(tmp_path):
    """THE load-bearing test. Point the check at a path with no artifact and assert
    FAIL — not SKIP, which is what let this control go dead for its whole life.

    Mutation-check: reverting the SKIP->FAIL change makes this assertion fail (status
    would read 'SKIP' again).
    """
    missing_path = tmp_path / "does_not_exist.generated.ts"
    result = ekv_controls._check_f91(profiles_file=missing_path)
    assert result.status == "FAIL", (
        f"Expected FAIL for a missing artifact, got {result.status!r}: {result.detail}"
    )
    assert result.control_id == "F-91"


def test_artifact_missing_consult_profile_is_warn(tmp_path):
    """An artifact that exists but lacks one of the three profiles is WARN, not PASS —
    regression guard on the still-real content check."""
    bad_file = tmp_path / "mcp_surface_profiles.generated.ts"
    bad_file.write_text("export const profiles = { \"full\": {}, \"compact\": {} }\n", encoding="utf-8")
    result = ekv_controls._check_f91(profiles_file=bad_file)
    assert result.status == "WARN"
    assert "full=True" in result.detail
    assert "compact=True" in result.detail
    assert "consult=False" in result.detail


def test_artifact_with_all_three_profiles_is_pass(tmp_path):
    good_file = tmp_path / "mcp_surface_profiles.generated.ts"
    good_file.write_text(
        "export const profiles = { \"full\": {}, \"compact\": {}, \"consult\": {} }\n", encoding="utf-8"
    )
    result = ekv_controls._check_f91(profiles_file=good_file)
    assert result.status == "PASS"


# ── The real artifact actually satisfies the check (recorded pass) ──────────

def test_real_artifact_passes_the_repointed_check():
    """A one-time recorded pass of the (previously-dead) check against the real,
    live artifact this control is now pointed at."""
    result = ekv_controls._check_f91()
    assert result.status == "PASS", (
        f"Repointed F-91 check does not PASS against the real artifact: {result.detail}"
    )
