"""Tests for RC-1 (§H.3.5/§H.3.8 registry repoint) + F-163 (status filter), landed
together per the PARISESA-V4 ruling ("RC-1 + F-163 — the registry-mutation
decision"): F-163 has no independent existence and closes only inside RC-1's PR.

Run from repo root:
  python -m pytest platform/scripts/governance/__tests__/test_drift_detector_h35_h38.py -v
"""
import pathlib
import sys

import pytest

# Allow import of drift_detector / _ca_loader from their directory.
_GOV_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_GOV_DIR))

from _ca_loader import CanonicalArtifacts  # noqa: E402
import drift_detector  # noqa: E402


def _fake_ca(artifacts: dict) -> CanonicalArtifacts:
    return CanonicalArtifacts(
        path=pathlib.Path("nonexistent.md"),
        raw_text="",
        fingerprint_observed="",
        artifacts=artifacts,
        mirror_pairs={},
    )


# --------------------------------------------------------------------------------------
# F-163 — the load-bearing can-fail test.
#
# One CURRENT row absent from the comparison surface, one PREDECESSOR row also
# absent. Only the CURRENT row should produce a finding: PREDECESSOR rows are
# SUPPOSED to be absent from a CURRENT-rows registry (that is F-163's whole
# defect: the old loop had no status filter at all, so a PREDECESSOR row being
# "missing" was wrongly flagged as agreement drift).
#
# Mutation-check performed manually while writing this test: commenting out the
# `if not _is_current(row): continue` line in check_file_registry_agreement makes
# this test fail (2 findings instead of 1, PREDECESSOR_ROW wrongly flagged) --
# confirming the test actually exercises the filter rather than passing vacuously.
# --------------------------------------------------------------------------------------

def test_f163_current_row_flagged_predecessor_row_is_not(tmp_path):
    ca_path = tmp_path / "00_ARCHITECTURE" / "CANONICAL_ARTIFACTS_v1_0.md"
    ca_path.parent.mkdir(parents=True)
    # Comparison surface exists, but names neither basename.
    ca_path.write_text("# CANONICAL_ARTIFACTS_v1_0.md\n\nNo relevant rows here.\n")

    ca = _fake_ca({
        "CURRENT_ROW": {"path": "00_ARCHITECTURE/CURRENT_ROW_v1_0.md", "status": "CURRENT"},
        "PREDECESSOR_ROW": {"path": "00_ARCHITECTURE/PREDECESSOR_ROW_v1_0.md", "status": "PREDECESSOR"},
    })

    findings = drift_detector.check_file_registry_agreement(tmp_path, ca)

    assert len(findings) == 1, (
        f"expected exactly 1 finding (CURRENT_ROW only), got {len(findings)}: {findings}"
    )
    assert findings[0].canonical_id == "CURRENT_ROW"
    assert findings[0].severity == "MEDIUM"


def test_f163_also_applies_to_unreferenced_canonical_scan(tmp_path):
    """§H.3.8 must apply the same _is_current() filter (the coupling ruling
    requires the two repointed checks to agree on what counts as a live row)."""
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE.md\n\nNo relevant rows here.\n")
    (tmp_path / "00_ARCHITECTURE").mkdir()
    (tmp_path / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json").write_text('{"entries": []}')

    ca = _fake_ca({
        "CURRENT_ROW": {"path": "00_ARCHITECTURE/CURRENT_ROW_v1_0.md", "status": "CURRENT"},
        "SUPERSEDED_ROW": {"path": "00_ARCHITECTURE/SUPERSEDED_ROW_v1_0.md", "status": "SUPERSEDED"},
        "PROPOSAL_ROW": {"path": "00_ARCHITECTURE/PROPOSAL_ROW_v1_0.md", "status": "PROPOSAL"},
    })

    findings = drift_detector.check_unreferenced_canonical(tmp_path, ca)

    assert len(findings) == 1
    assert findings[0].canonical_id == "CURRENT_ROW"


@pytest.mark.parametrize("status,expected", [
    ("CURRENT", True),
    ("CURRENT-FOR-EXECUTION", True),
    ("LIVING", True),
    ("READY", True),
    ("PREDECESSOR", False),
    ("SUPERSEDED", False),
    ("PROPOSAL", False),
    ("", False),
    (None, False),
])
def test_is_current_vocabulary(status, expected):
    """Pinned to the real CAPABILITY_MANIFEST.json status vocabulary, enumerated via
    `jq -r '..|.status?|select(type=="string")' 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
    | sort -u` on 2026-08-22: CURRENT, CURRENT-FOR-EXECUTION, LIVING, PREDECESSOR,
    PROPOSAL, READY, SUPERSEDED. See drift_detector._CURRENT_STATUSES for the
    exclusion rationale (PREDECESSOR/SUPERSEDED are historical; PROPOSAL is
    pre-ratification)."""
    assert drift_detector._is_current({"status": status}) is expected


# --------------------------------------------------------------------------------------
# Repoint regression — against the REAL tree.
# --------------------------------------------------------------------------------------

def test_repoint_no_longer_uses_file_registry_as_h35_surface():
    """§H.3.5 no longer compares against FILE_REGISTRY_v1_14.md (SUPERSEDED). The
    pre-repoint code produced 84 findings against that surface (F94 plan §4.1);
    post-repoint, against CANONICAL_ARTIFACTS_v1_0.md, real measured count on
    2026-08-22 is 77 -- still non-trivial (CANONICAL_ARTIFACTS_v1_0.md's frozen
    ~33-row §1 table predates most of CAPABILITY_MANIFEST.json's growth to 128
    entries) but a real drop from false-positive-by-construction 84/128 to a
    genuine, triaged 77/114 -- see this PR's body for the triage. Assert strictly
    less than the old 84, not a fixed number, so this doesn't need updating every
    time a real row is registered."""
    repo_root = _GOV_DIR.parent.parent.parent
    from manifest_reader import load_manifest_as_ca
    ca = load_manifest_as_ca(repo_root)
    findings = drift_detector.check_file_registry_agreement(repo_root, ca)
    assert len(findings) < 84, (
        f"§H.3.5 regressed toward the pre-repoint false-positive count: {len(findings)} findings"
    )


def test_repoint_h38_corpus_is_manifest_not_file_registry():
    """§H.3.8's corpus is now CLAUDE.md + CAPABILITY_MANIFEST.json. Real measured
    count on 2026-08-22 is 0 -- flagged explicitly in this PR's body and in the
    function's own docstring as a known, not-fixed-here consequence: under
    default manifest mode `ca` is itself manifest-derived, so folding the
    manifest's own raw text into the corpus makes basename presence close to
    tautological. This test pins that measured behavior so a future change to
    the corpus construction is a deliberate, reviewed decision, not a silent
    regression back toward FILE_REGISTRY."""
    repo_root = _GOV_DIR.parent.parent.parent
    from manifest_reader import load_manifest_as_ca
    ca = load_manifest_as_ca(repo_root)
    findings = drift_detector.check_unreferenced_canonical(repo_root, ca)
    assert len(findings) == 0


def test_rc4_governance_stack_msr_row_present():
    """RC-4: GOVERNANCE_STACK_v1_0.md §1 now carries the MSR_v5_0.md row this
    check flagged as missing pre-fix. Real (non-repointed) surface, so this is a
    genuine drift fix, not a repoint."""
    repo_root = _GOV_DIR.parent.parent.parent
    from manifest_reader import load_manifest_as_ca
    ca = load_manifest_as_ca(repo_root)
    findings = drift_detector.check_governance_stack_agreement(repo_root, ca)
    assert not any(f.canonical_id == "MSR" for f in findings), (
        "GOVERNANCE_STACK_v1_0.md still missing its MSR row after RC-4"
    )


# --------------------------------------------------------------------------------------
# Remediation-string guard — the "actively harmful remediation" defect class
# (drift_detector.py used to emit "Add a row for {basename} in FILE_REGISTRY",
# instructing a session to edit an archival-retain-in-place document).
# --------------------------------------------------------------------------------------

def test_no_remediation_instructs_editing_file_registry():
    repo_root = _GOV_DIR.parent.parent.parent
    from manifest_reader import load_manifest_as_ca
    ca = load_manifest_as_ca(repo_root)
    all_findings = (
        drift_detector.check_file_registry_agreement(repo_root, ca)
        + drift_detector.check_unreferenced_canonical(repo_root, ca)
    )
    for f in all_findings:
        assert "FILE_REGISTRY" not in f.suggested_remediation, (
            f"remediation still points at the archival FILE_REGISTRY: {f}"
        )


# --------------------------------------------------------------------------------------
# Surface-missing CRITICAL — a missing comparison surface must still be CRITICAL.
# --------------------------------------------------------------------------------------

def test_h35_critical_when_canonical_artifacts_missing(tmp_path):
    # tmp_path has no 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md at all.
    ca = _fake_ca({"X": {"path": "00_ARCHITECTURE/X.md", "status": "CURRENT"}})
    findings = drift_detector.check_file_registry_agreement(tmp_path, ca)
    assert len(findings) == 1
    assert findings[0].severity == "CRITICAL"
    assert findings[0].canonical_id == "CANONICAL_ARTIFACTS"
