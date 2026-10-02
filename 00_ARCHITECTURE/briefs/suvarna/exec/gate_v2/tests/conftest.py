"""Fixtures for the GATE_V2 tests (helpers live in the uniquely named gate_v2_helpers.py so other conftest.py files cannot shadow them)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate_v2_helpers as h  # noqa: E402


@pytest.fixture()
def world(tmp_path):
    return h.World(tmp_path)


@pytest.fixture()
def staged(tmp_path):
    return h.make_staged(tmp_path)
