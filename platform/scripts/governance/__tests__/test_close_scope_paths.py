"""Exercise the real close-checklist scope guard with lexical Git paths."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import schema_validator as validator


def validate(path, may_touch):
    handshake = {"session_open": {"declared_scope": {
        "may_touch": may_touch,
        "must_not_touch": ["99_ARCHIVE/**"],
    }}}
    close = {"session_close": {"files_touched": [{"path": path}]}}
    return validator.validate_scope_boundary(handshake, close)


@pytest.mark.parametrize("path,may_touch", [
    ("platform/../99_ARCHIVE/CLAUDE.md", ["platform/**"]),
    ("platform/../../outside.md", ["platform/**"]),
    ("/outside.md", ["**"]),
    ("C:/outside.md", ["**"]),
    ("platform\\..\\99_ARCHIVE\\CLAUDE.md", ["**"]),
    ("platform//src/example.ts", ["platform/**"]),
    ("platform/./src/example.ts", ["platform/**"]),
    ("platform/src/", ["platform/**"]),
    ("platform/\x00bad", ["platform/**"]),
    ("", ["**"]),
    (None, ["**"]),
    (1, ["**"]),
])
def test_rejects_noncanonical_touched_path_before_globs(path, may_touch):
    [violation] = validate(path, may_touch)
    assert violation.rule == "scope_boundary_violation"
    assert violation.severity == "HIGH"
    assert "canonical repository-relative POSIX path" in violation.evidence


@pytest.mark.parametrize("path,may_touch", [
    ("platform/src/example.ts", ["platform/**"]),
    ("platform/docs/Source file.md", ["platform/**"]),
    ("00_ARCHITECTURE/AGENTS.md", ["00_ARCHITECTURE/**"]),
])
def test_preserves_valid_allowed_paths(path, may_touch):
    assert validate(path, may_touch) == []


@pytest.mark.parametrize("path,may_touch,evidence", [
    ("99_ARCHIVE/CLAUDE.md", ["**"], "matches declared must_not_touch"),
    ("other/example.ts", ["platform/**"], "is not in declared may_touch"),
])
def test_preserves_valid_denied_paths(path, may_touch, evidence):
    [violation] = validate(path, may_touch)
    assert violation.rule == "scope_boundary_violation"
    assert violation.path == path
    assert evidence in violation.evidence
