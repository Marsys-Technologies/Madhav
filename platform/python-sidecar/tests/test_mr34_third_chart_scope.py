"""
MR-34 — Third-chart (cb73cd3d) scope statement integrity tests.

TDD: written before THIRD_CHART_SCOPE_STATEMENT_v1_0.md was created;
run failing first, then pass after the document lands.
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).parents[3]
SCOPE_DOC = (
    REPO_ROOT
    / "00_ARCHITECTURE"
    / "llm_consumption_audit"
    / "briefs"
    / "gochara_elevation"
    / "THIRD_CHART_SCOPE_STATEMENT_v1_0.md"
)

THIRD_CHART_UUID = "cb73cd3d-9eba-4220-9902-0de91566e980"


def test_scope_statement_file_exists():
    """The scope statement document must exist at the canonical path."""
    assert SCOPE_DOC.exists(), (
        f"THIRD_CHART_SCOPE_STATEMENT_v1_0.md not found at {SCOPE_DOC}. "
        "MR-34 gate requires this file to be committed."
    )


def test_scope_statement_contains_chart_id():
    """Document must contain the third chart's UUID."""
    assert SCOPE_DOC.exists(), "Scope statement file missing — see test_scope_statement_file_exists"
    content = SCOPE_DOC.read_text()
    assert THIRD_CHART_UUID in content, (
        f"Chart UUID {THIRD_CHART_UUID} not found in scope statement. "
        "MR-34 requires the chart_id to be recorded explicitly."
    )
    # Also check the short prefix used in text references
    assert "cb73cd3d" in content, "Short chart_id prefix 'cb73cd3d' not found in document"


def test_scope_statement_declares_v1_authority():
    """Document must record the v1-authority stance explicitly."""
    assert SCOPE_DOC.exists(), "Scope statement file missing — see test_scope_statement_file_exists"
    content = SCOPE_DOC.read_text()
    assert "v1-authority" in content, (
        "Document must contain the string 'v1-authority' to record the intentional "
        "engine stance for this chart. MR-34 gate: 'statement recorded; battery includes it'."
    )


def test_scope_statement_references_mr24():
    """Document must reference MR-24 to confirm the battery constraint is recorded."""
    assert SCOPE_DOC.exists(), "Scope statement file missing — see test_scope_statement_file_exists"
    content = SCOPE_DOC.read_text()
    assert "MR-24" in content, (
        "Document must reference MR-24 (E2E battery must include this chart as a v1-authority "
        "test case). MR-34 gate requires this constraint to be documented."
    )


def test_scope_statement_has_correct_artifact_frontmatter():
    """Document frontmatter must carry artifact: THIRD_CHART_SCOPE_STATEMENT."""
    assert SCOPE_DOC.exists(), "Scope statement file missing — see test_scope_statement_file_exists"
    content = SCOPE_DOC.read_text()
    assert "artifact: THIRD_CHART_SCOPE_STATEMENT" in content, (
        "Frontmatter must contain 'artifact: THIRD_CHART_SCOPE_STATEMENT' "
        "(not the old 'artifact: THIRD_CHART_SCOPE.md' value)."
    )
