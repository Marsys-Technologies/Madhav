"""Bind archived WP6 oracles to a database owned by the current DB fixture."""
import os
import sys
import pytest


@pytest.fixture(scope="module", autouse=True)
def _bind_archived_wp6(isolated_kala_db_dsn):
    # All modules are collected before fixtures run, so copied FROM imports of
    # WP6_DSN must be rebound too. Each wrapper gets a fresh database.
    changed = []
    for module in list(sys.modules.values()):
        if module is not None and hasattr(module, "WP6_DSN") and "python-sidecar" in str(getattr(module, "__file__", "")):
            changed.append((module, module.WP6_DSN))
            module.WP6_DSN = isolated_kala_db_dsn
    old_path = os.environ.get("PYTHONPATH")
    old_dsn = os.environ.get("WP6_LEDGER_DSN")
    from pathlib import Path
    sidecar = str(Path(__file__).resolve().parents[4])
    os.environ["PYTHONPATH"] = sidecar + (os.pathsep + old_path if old_path else "")
    os.environ["WP6_LEDGER_DSN"] = isolated_kala_db_dsn
    try:
        yield
    finally:
        for module, value in changed:
            module.WP6_DSN = value
        for key, old in (("PYTHONPATH", old_path), ("WP6_LEDGER_DSN", old_dsn)):
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
