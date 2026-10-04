"""Pins the 1241 v7 test fixture to the reviewed migration bytes (PR #2949).

The fixture is the byte-exact copy of Stream B's real migration 1241 v7 that the faithful
mirror applies while 1241 itself must not live in platform/migrations on this branch
(protected-window rule). Any drift between the fixture and the reviewed migration fails here.
"""
from __future__ import annotations

import hashlib

from ._migration_1241 import M1241_FIXTURE, M1241_NAME, M1241_SHA256, migration_1241_sql


def test_1241_fixture_sha256_is_the_pinned_v7_digest():
    raw = M1241_FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == M1241_SHA256


def test_1241_loader_falls_back_to_the_fixture_when_the_real_migration_is_absent(tmp_path):
    # an empty platform/migrations stand-in: the loader must serve the fixture bytes
    sql = migration_1241_sql(tmp_path)
    assert sql == M1241_FIXTURE.read_text()


def test_1241_loader_prefers_a_present_real_migration_and_verifies_its_digest(tmp_path):
    real = tmp_path / M1241_NAME
    real.write_bytes(M1241_FIXTURE.read_bytes())
    assert migration_1241_sql(tmp_path) == M1241_FIXTURE.read_text()
    real.write_text("-- tampered\n")
    try:
        migration_1241_sql(tmp_path)
    except AssertionError as exc:
        assert M1241_SHA256 in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a tampered 1241 must be refused")
