"""Pins the 1241 v7 test fixture to the reviewed migration bytes (PR #2949).

The fixture is the byte-exact copy of Stream B's real migration 1241 v7 that the faithful
mirror applies when the landing migration 1378 is absent. The landing differs only
in migration-number metadata and diagnostics; any other drift fails here.
"""
from __future__ import annotations

import hashlib

from ._migration_1241 import M1241_FIXTURE, M1241_NAME, M1241_SHA256, M1378_SHA256, migration_1241_sql


def test_1241_fixture_sha256_is_the_pinned_v7_digest():
    raw = M1241_FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M1241_SHA256


def test_1241_loader_falls_back_to_the_fixture_when_the_real_migration_is_absent(tmp_path):
    # an empty platform/migrations stand-in: the loader must serve the fixture bytes
    sql = migration_1241_sql(tmp_path)
    assert sql == M1241_FIXTURE.read_text()


def test_1241_loader_prefers_a_present_real_migration_and_verifies_its_digest(tmp_path):
    real = tmp_path / M1241_NAME
    landed = M1241_FIXTURE.read_bytes().replace(b"1241", b"1378")
    real.write_bytes(landed)
    assert migration_1241_sql(tmp_path) == landed.decode()
    real.write_text("-- tampered\n")
    try:
        migration_1241_sql(tmp_path)
    except AssertionError as exc:
        assert M1378_SHA256 in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a tampered 1241 must be refused")


def test_landed_grants_preserve_the_archived_sql_except_the_migration_number():
    from pathlib import Path
    migrations = Path(__file__).resolve().parents[4] / "migrations"
    assert (migrations / M1241_NAME).is_file(), "P05 must ship the renumbered grant migration"
    landed = migration_1241_sql(migrations)
    assert landed == M1241_FIXTURE.read_text().replace("1241", "1378")
