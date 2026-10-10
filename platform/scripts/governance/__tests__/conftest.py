"""conftest for the governance tool tests: no test may launch a real cloud command (see no_real_cloud_guard.py: the 2026-10-05 incident).

Installed at conftest import for the whole process, autouse, no opt-out marker. Tests that need to prove a tool REFUSES to dispatch use the guard's own
exception or their own stubs; a test that deliberately triggers the guard uses the `acknowledge_attempts` fixture.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from no_real_cloud_pytest import *  # noqa: E402,F401,F403


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _vocab_registered_alias_set_starts_empty():
    """N-233 R2: asset_census reads bg_ontology's registered alias set from brahma_ontology at measure time (`vocab_registered_load`) and caches it process-wide. A test that never
    sets it up must not depend on a database it does not have, nor on a set left by an earlier test: each test starts with the set LOADED AS EMPTY (the pre-N-233 reading: no alias
    is registered). A test of the registered-alias rule sets `ac._VOCAB_REGISTERED` itself, or sets it to None to exercise the load."""
    ac = sys.modules.get("asset_census")
    if ac is not None:
        ac._VOCAB_REGISTERED = {}
    yield
    ac = sys.modules.get("asset_census")
    if ac is not None:
        ac._VOCAB_REGISTERED = None


@pytest.fixture(autouse=True)
def _census_runs_in_tests_are_disposable(monkeypatch):
    """SS N-332: every census must DECLARE its target and a run that states none refuses. Every governance test runs against a fake or throw-away database, and calling that "production" would be a
    false declaration (§N.8), so the shared default is the honest one: `disposable` (census_postprocess never certifies one). The tests of the target logic itself (test_n317_evaluation_copy.py)
    clear or set the variable explicitly."""
    monkeypatch.setenv("SUVARNA_CENSUS_TARGET", "disposable")
