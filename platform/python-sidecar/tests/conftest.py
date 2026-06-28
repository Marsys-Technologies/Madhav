"""Root conftest for the python-sidecar test suite."""
from __future__ import annotations

# Pre-load the real writers package before any test module is imported.
#
# tests/l2/test_bo_a1_fixes.py installs a sys.modules stub for
# `pipeline.orchestrator.writers` at MODULE LEVEL via setdefault().  Pytest
# collects directories alphabetically, so `l2/` is traversed (and the stub
# installed) before `test_ga_orchestrator_conformance.py` and
# `test_orchestrator_substeps.py` are imported — causing a collect-time
# ImportError for `discover_all` from the stub that lacks it.
#
# Importing the real package here guarantees it is already in sys.modules
# when test_bo_a1_fixes.py runs its setdefault(), making that call a no-op.
import pipeline.orchestrator.writers  # noqa: F401
