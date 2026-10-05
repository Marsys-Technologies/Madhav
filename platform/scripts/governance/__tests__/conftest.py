"""conftest for the governance tool tests: no test may launch a real cloud command (see no_real_cloud_guard.py: the 2026-10-05 incident).

Session-wide and autouse, with no opt-out marker. Tests that need to prove a tool REFUSES to dispatch use the guard's own exception or their own stubs.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import no_real_cloud_guard  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _no_real_cloud_commands():
    uninstall = no_real_cloud_guard.install()
    yield
    uninstall()
