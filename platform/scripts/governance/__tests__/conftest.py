"""conftest for the governance tool tests: no test may launch a real cloud command (see no_real_cloud_guard.py: the 2026-10-05 incident).

Installed at conftest import for the whole process, autouse, no opt-out marker. Tests that need to prove a tool REFUSES to dispatch use the guard's own
exception or their own stubs; a test that deliberately triggers the guard uses the `acknowledge_attempts` fixture.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from no_real_cloud_pytest import *  # noqa: E402,F401,F403
