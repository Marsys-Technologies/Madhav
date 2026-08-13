"""FM-23 CI guard: every dhara_*.py in services/ka_kshetra/ must be imported
by at least one production file (not only by test files).

Background
----------
dhara_null.py, dhara_term_matrix.py, and dhara_pin_matrix.py were all merged
to main (PRs #1263, #1266, #1264) but none were imported by any production
code.  The build ran for 9 h using the old 256-replicate engine because the
optimised 1024-replicate engine was never called.  A merged-but-uncalled
module is a null signal wearing a green PR (§N.8 of CLAUDE.md).

Current expected state
----------------------
- dhara_sweep       -> PASS  (imported by engine_config.py and writer.py)
- dhara_null        -> FAIL  (will be fixed by OPT-N1)
- dhara_term_matrix -> FAIL  (will be fixed by OPT-N3)
- dhara_pin_matrix  -> FAIL  (will be fixed by OPT-N3)

The failing tests are INTENTIONAL — they exist precisely to catch the unwired
state and will turn green once the wiring PRs land.
"""

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Path roots
# ---------------------------------------------------------------------------

# Resolve from __file__: tests/governance/ -> tests/ -> python-sidecar/
SIDECAR_ROOT = pathlib.Path(__file__).parent.parent.parent

KA_KSHETRA_DIR = SIDECAR_ROOT / "services" / "ka_kshetra"

# Production search roots — test sub-directories are excluded by the filter
# inside find_production_imports().
PROD_DIRS = [
    SIDECAR_ROOT / "services",
    SIDECAR_ROOT / "pipeline",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_dhara_modules() -> list[str]:
    """Return sorted list of stem names for every dhara_*.py in ka_kshetra/."""
    return sorted(
        p.stem
        for p in KA_KSHETRA_DIR.glob("dhara_*.py")
        if "__pycache__" not in str(p)
    )


def find_production_imports(module_stem: str) -> list[pathlib.Path]:
    """Return all production .py files that reference *module_stem*.

    A file is excluded when:
    - any component of its path is named 'tests' or '__tests__', OR
    - its basename starts with 'test_', OR
    - it IS the module being checked (self-reference is not an import).
    """
    # Canonical path of the module itself — exclude self-matches.
    self_path = (KA_KSHETRA_DIR / f"{module_stem}.py").resolve()

    hits: list[pathlib.Path] = []
    for prod_dir in PROD_DIRS:
        if not prod_dir.exists():
            continue
        for pyfile in prod_dir.rglob("*.py"):
            # Exclude test files / test directories
            if any(part in ("tests", "__tests__") for part in pyfile.parts):
                continue
            if pyfile.name.startswith("test_"):
                continue
            # Exclude the module itself (a file always contains its own name)
            try:
                if pyfile.resolve() == self_path:
                    continue
            except OSError:
                continue
            try:
                text = pyfile.read_text(errors="replace")
            except OSError:
                continue
            if module_stem in text:
                hits.append(pyfile)
    return hits


# ---------------------------------------------------------------------------
# Parametrised guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_stem", find_dhara_modules())
def test_dhara_module_is_imported_by_production_code(module_stem: str) -> None:
    """FM-23: every dhara_*.py must be imported by at least one production file.

    A merged-but-uncalled module is a null signal wearing a green PR (§N.8).
    This guard prevents the FM-23 defect class from recurring.
    """
    hits = find_production_imports(module_stem)
    assert hits, (
        f"FM-23 VIOLATION: {module_stem}.py is not imported by any production "
        f"file. It exists in services/ka_kshetra/ but is only imported by "
        f"tests (if at all). Wire it into production code or this test will "
        f"continue to fail."
    )
