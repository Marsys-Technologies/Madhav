"""Fixtures for the 1272/1273 owner-path executor tests.

Pure tests need nothing. The mirror tests (marker `mirror`) need a disposable PostgreSQL 15 built like production (production schema, owners and ACLs; see
platform/python-sidecar/tests/l2/realpg/README.md and /Users/Dev/suvarna-evidence/S_L2/realpg/) and three URLs:
  DPBP_MIRROR_SUPER_URL    container superuser: used ONLY to put the database back to the production pre-state between tests and to read facts
  DPBP_MIRROR_ADMIN_URL    the executor's administrator: NOT a superuser, CREATEROLE (mirrors production's `postgres`)
  DPBP_MIRROR_BUILDER_URL  data_plane_builder, the pipeline login (end-to-end proof)
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
FOLDER = HERE.parent
EXEC_PATH = pathlib.Path(os.environ.get("DPBP_EXEC_PATH", FOLDER / "dp_builder_privileges_exec.py"))


def load_executor():
    name = "dpbp_exec_under_test"
    spec = importlib.util.spec_from_file_location(name, EXEC_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def ex():
    return load_executor()


SUPER = os.environ.get("DPBP_MIRROR_SUPER_URL")
ADMIN = os.environ.get("DPBP_MIRROR_ADMIN_URL")
BUILDER = os.environ.get("DPBP_MIRROR_BUILDER_URL")
mirror = pytest.mark.skipif(not (SUPER and ADMIN and BUILDER), reason="DPBP_MIRROR_{SUPER,ADMIN,BUILDER}_URL not provided (disposable production-mirrored PostgreSQL)")


def pytest_configure(config):
    config.addinivalue_line("markers", "mirror: needs the disposable production-mirrored PostgreSQL")


def reset_database(ex):
    """Back to the production pre-state for B3/B4: the shipped live bind definition + its live attestation digest, no builder EXECUTE on the identity functions."""
    import psycopg
    p = ex.BIND_PATCH
    with psycopg.connect(SUPER, autocommit=True) as c:
        cur = c.cursor()
        cur.execute("SET ROLE data_plane_l2_owner")
        cur.execute(p.live_def())
        cur.execute("RESET ROLE")
        cur.execute(f"ALTER TABLE {ex.FN_ATT} DISABLE TRIGGER {ex.FN_ATT_IMMUTABLE}")
        cur.execute(f"UPDATE {ex.FN_ATT} SET definition_digest=%s WHERE function_signature=%s", (p.live_sha256, p.signature))
        cur.execute(f"ALTER TABLE {ex.FN_ATT} ENABLE TRIGGER {ex.FN_ATT_IMMUTABLE}")
        for sig, _ in ex.IDENTITY_FUNCTIONS:
            cur.execute(f"REVOKE EXECUTE ON FUNCTION public.{sig} FROM {ex.BUILDER}")
        cur.execute("UPDATE build_runs SET state='completed' WHERE state IN ('planned','running','paused')")


@pytest.fixture
def db(ex):
    reset_database(ex)
    yield
    reset_database(ex)


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    root = tmp_path / "evidence"
    monkeypatch.setenv("DPBP_TEST_EVIDENCE_ROOT", str(root))
    return root


class Args:
    def __init__(self, mode, expect_plan, expect_evidence=None, evidence_root=None):
        self.mode, self.expect_plan, self.expect_evidence, self.evidence_root = mode, expect_plan, expect_evidence, evidence_root


def run_mode(ex, mode, expect_evidence=None, plan=None, connect=None):
    import psycopg

    def default_connect():
        return psycopg.connect(ADMIN)
    return ex.execute(Args(mode, plan or ex.plan_hash(), expect_evidence), connect or default_connect)
