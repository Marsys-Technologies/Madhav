"""Root conftest for the python-sidecar test suite.

Scope: session-wide test isolation for the CONDUCTOR_HALT_LOG.md writer
path only. (tests/conftest.py carries a separate, tests/-scoped fixture for
import-order stubbing; this file does not duplicate or depend on it.)

Root cause (SAMĀPTI campaign, 2026-07-30): several `_write_halt_log()`
implementations across ga_writers/*.py (ga_positions_writer.py,
ga_panchanga_writer.py, ga_sade_sati_writer.py, ga_structural_writer.py — the
latter three duplicate the pattern independently) hard-code their target file
as a directory walk-up from `__file__` to the real, git-tracked
`00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_HALT_LOG.md` (and its
`l1-ganita-build/` sibling). Several unit tests exercise the production
`forensic_gate()` / `panchanga_forensic_gate()` functions directly with
deliberately-invalid fixture data to assert they raise (e.g.
tests/test_ga3_writers.py::TestForensicGate,
tests/test_ga4_writer.py::TestForensicGate) — and those gate functions call
`_write_halt_log()` unconditionally before raising, so every such test run
appended real "FORENSIC FAIL" fixture noise to the two tracked halt-log
files. This was observed and manually reverted (`git checkout --`) by
multiple independent SAMĀPTI lanes before landing in a commit.

Fix: each `_write_halt_log()` now honors a `CONDUCTOR_HALT_LOG_DIR_OVERRIDE`
env var and, when set, writes there instead of walking up to the real repo
file. This fixture sets that env var to a session-scoped tmp directory for
the entire pytest run, so no test — present or future — can dirty the real
CONDUCTOR_HALT_LOG.md files, without any test needing to know about the
mechanism.
"""
from __future__ import annotations

import os

import pytest


def _configure_swiss_corpus_for_tests() -> None:
    """Point SE_EPHE_PATH at a local Swiss .se1 corpus when one exists.

    The sidecar's ephemeris helper (panchang_engine/swiss_backend.py) fails
    closed without SE_EPHE_PATH -- there is no silent Moshier fallback.  CI
    exports it explicitly; for a local run this mirrors the production
    resolution order of brahmagyan.l0_ephemeris._resolve_ephe_path
    (SWE_EPHE_PATH, /app/ephe, /tmp/se1) and the explicit override
    MARSYS_TEST_SE1_DIR.  With no corpus the variable stays unset and the tests
    that need an ephemeris fail with the helper's explicit error.  Runs at
    conftest import, i.e. before any test module (and PyJHora) is imported.
    """
    if os.environ.get("SE_EPHE_PATH", "").strip():
        return
    for candidate in (
        os.environ.get("MARSYS_TEST_SE1_DIR"),
        os.environ.get("SWE_EPHE_PATH"),
        "/app/ephe",
        "/tmp/se1",
    ):
        if candidate and all(
            os.path.isfile(os.path.join(candidate, name))
            for name in ("sepl_18.se1", "semo_18.se1")
        ):
            os.environ["SE_EPHE_PATH"] = candidate
            return


_configure_swiss_corpus_for_tests()


@pytest.fixture(scope="session", autouse=True)
def _isolate_conductor_halt_log(tmp_path_factory: pytest.TempPathFactory):
    """Redirect every ga_writers `_write_halt_log()` call to a tmp dir.

    Autouse + session-scoped: applies to the whole suite with no per-test
    opt-in, so a forensic-gate test added later (in any ga_writers module)
    is covered automatically instead of relying on each new test author to
    remember to mock the halt-log writer.
    """
    halt_dir = tmp_path_factory.mktemp("conductor_halt_log")
    prior = os.environ.get("CONDUCTOR_HALT_LOG_DIR_OVERRIDE")
    os.environ["CONDUCTOR_HALT_LOG_DIR_OVERRIDE"] = str(halt_dir)
    try:
        yield halt_dir
    finally:
        if prior is None:
            os.environ.pop("CONDUCTOR_HALT_LOG_DIR_OVERRIDE", None)
        else:
            os.environ["CONDUCTOR_HALT_LOG_DIR_OVERRIDE"] = prior
