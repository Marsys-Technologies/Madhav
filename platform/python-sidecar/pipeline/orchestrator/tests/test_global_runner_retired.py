"""The historical direct global runner must fail closed."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.global_runner import execute_global_build


def test_direct_global_build_is_retired():
    with pytest.raises(RuntimeError, match="canonical cockpit build_run"):
        execute_global_build()
