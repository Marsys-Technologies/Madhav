"""pytest glue for no_real_cloud_guard: import this from a conftest.py (`from no_real_cloud_pytest import *  # noqa`).

Importing installs the guard for the whole process at CONFTEST-IMPORT time (not in a session fixture that runs after collection), and exposes two fixtures:
`_no_swallowed_cloud_attempts` (autouse, per test): fails a test whose run recorded a blocked attempt even if the code under test swallowed the exception;
`acknowledge_attempts`: a test that deliberately triggers the guard asks for it and says how many attempts it expects.
"""
from __future__ import annotations

import pytest

import no_real_cloud_guard as _guard

_guard.ensure_installed()


@pytest.fixture(autouse=True)
def _no_swallowed_cloud_attempts(request):
    before = _guard.attempt_count()
    expected = {"n": 0}
    request.node._cloud_guard_expected = expected
    yield
    grew = _guard.attempt_count() - before
    if grew > expected["n"]:
        recent = _guard.ATTEMPTS[-grew:]
        pytest.fail(f"{grew} real cloud command attempt(s) were blocked during this test (expected {expected['n']}): "
                    + "; ".join(str(a["args"]) for a in recent), pytrace=False)


@pytest.fixture
def acknowledge_attempts(request):
    def say(n: int):
        request.node._cloud_guard_expected["n"] += n
    return say


__all__ = ["_no_swallowed_cloud_attempts", "acknowledge_attempts"]
