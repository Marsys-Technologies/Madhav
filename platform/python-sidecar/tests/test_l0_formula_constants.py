"""Governance guards for the bg_formula_constants canonical writer seed."""

from brahmagyan.l0_formula_constants import CONSTANTS, seed_formula_constants


def test_writer_seeds_only_operational_formula_constants() -> None:
    ids = {row["constant_id"] for row in CONSTANTS}

    assert "_bug_ka_sangam_confidence_conflation" not in ids
    assert all(row["class"] != "conflation_bug" for row in CONSTANTS)


def test_dry_run_reports_the_ten_w1_operational_constants() -> None:
    assert seed_formula_constants(None, dry_run=True) == {
        "brahma_formula_constants": 10,
    }


# ── TI-L0-21 (SS Q8): calibratable constants are seed-once ───────────────────
#
# L0 holds seeds only; a calibrated value belongs to whoever calibrated it. A
# rebuild must therefore never write a `calibratable` constant's value (or its
# version) back to the seed, while a non-calibratable (classical / engineering)
# constant is still converged to the seed on every rebuild.

import json
import os
import re

import pytest

import brahmagyan.l0_formula_constants as ffc


class _Cur:
    """Recording cursor: remembers every (sql, params) it is asked to run."""

    def __init__(self, log: list) -> None:
        self._log = log

    def __enter__(self) -> "_Cur":
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def execute(self, sql: str, params=None) -> None:
        self._log.append((sql, params))

    def fetchone(self) -> dict:
        return {"count": 1}


class _Conn:
    def __init__(self) -> None:
        self.log: list = []

    def cursor(self) -> _Cur:
        return _Cur(self.log)

    def commit(self) -> None:  # autocommit=False in production; harmless here
        pass


def _set_clauses(sql: str) -> dict[str, str]:
    """column -> right-hand side, for the ON CONFLICT ... DO UPDATE SET list."""
    tail = sql.split("DO UPDATE SET", 1)[1].strip()
    out: dict[str, str] = {}
    for part in re.split(r",\s*\n\s*(?=\w+\s*=\s)", tail):
        col, rhs = part.split("=", 1)
        out[col.strip()] = " ".join(rhs.split())
    return out


def _upsert_sql_by_constant() -> dict[str, str]:
    conn = _Conn()
    seed_formula_constants(conn, autocommit=False)
    upserts = [(s, p) for s, p in conn.log if "INSERT INTO brahma_formula_constants" in s]
    return {p[0]: s for s, p in upserts}


def test_there_are_eight_calibratable_constants_and_two_fixed_ones() -> None:
    # The brief (FD-2) speaks of "the 8 calibratable constants"; pin the partition
    # so a change to it is a visible, reviewed edit of this test.
    assert sum(1 for r in CONSTANTS if r["calibratable"]) == 8
    assert sum(1 for r in CONSTANTS if not r["calibratable"]) == 2


def test_calibratable_value_and_version_are_only_written_when_the_value_equals_the_seed() -> None:
    by_id = _upsert_sql_by_constant()
    assert set(by_id) == {r["constant_id"] for r in CONSTANTS}
    for row in CONSTANTS:
        sets = _set_clauses(by_id[row["constant_id"]])
        if row["calibratable"]:
            for col, seed_rhs in (("value_jsonb", "EXCLUDED.value_jsonb"), ("version", "EXCLUDED.version")):
                rhs = sets[col]
                assert rhs.startswith("CASE WHEN"), (row["constant_id"], col, rhs)
                # equal to the seed -> seed; otherwise keep the table's own column
                assert "brahma_formula_constants.value_jsonb = EXCLUDED.value_jsonb" in rhs
                assert f"THEN {seed_rhs}" in rhs
                assert f"ELSE brahma_formula_constants.{col} END" in rhs
            # the descriptive columns still converge unconditionally
            for col in ("class", "consumer_assets", "citation_or_ratification", "calibratable", "bounds"):
                assert sets[col] == f"EXCLUDED.{col}", (row["constant_id"], col)
        else:
            assert sets["value_jsonb"] == "EXCLUDED.value_jsonb", row["constant_id"]
            assert sets["version"] == "EXCLUDED.version", row["constant_id"]


_PG = os.environ.get("FORMULA_CONSTANTS_TEST_DATABASE_URL")

_DDL = """
DROP TABLE IF EXISTS brahma_formula_constants;
CREATE TABLE brahma_formula_constants (
    constant_id TEXT PRIMARY KEY,
    value_jsonb JSONB NOT NULL,
    class TEXT NOT NULL CHECK (class IN ('classical','native_judgment','engineering','conflation_bug')),
    consumer_assets TEXT[] NOT NULL DEFAULT '{}',
    citation_or_ratification TEXT NOT NULL,
    calibratable BOOLEAN NOT NULL DEFAULT false,
    bounds JSONB,
    version TEXT NOT NULL DEFAULT '1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


@pytest.mark.skipif(not _PG, reason="FORMULA_CONSTANTS_TEST_DATABASE_URL not configured")
def test_rebuild_keeps_a_calibrated_value_and_still_repairs_a_classical_one() -> None:
    import psycopg
    from psycopg.rows import dict_row

    # The DDL drops brahma_formula_constants: never point this at anything but a scratch database.
    assert _PG.rsplit("/", 1)[-1].endswith("_test"), "refusing to run: database name must end with _test"

    calibratable_id = "house_weights"            # native_judgment, calibratable
    classical_id = "combustion_orbs"             # classical, fixed
    with psycopg.connect(_PG, row_factory=dict_row) as conn:
        try:
            conn.execute(_DDL)
            seed_formula_constants(conn, autocommit=False)
            first = {r["constant_id"]: r for r in conn.execute(
                "SELECT *, value_jsonb::text AS value_text FROM brahma_formula_constants").fetchall()}
            assert len(first) == len(CONSTANTS)          # first install seeds all ten
            seed_value = first[calibratable_id]["value_jsonb"]

            # An L5-style calibration of the calibratable row + a descriptive-column drift,
            # and a hand edit of the classical row.
            conn.execute(
                "UPDATE brahma_formula_constants SET value_jsonb='{\"calibrated\": 1.23}'::jsonb, "
                "version='2.0', citation_or_ratification='stale citation' WHERE constant_id=%s",
                (calibratable_id,))
            conn.execute(
                "UPDATE brahma_formula_constants SET value_jsonb='{\"tampered\": true}'::jsonb, "
                "version='9.9' WHERE constant_id=%s", (classical_id,))
            # A calibratable row whose live value EQUALS the seed but is written the way
            # migration 389 wrote it (trailing zeros): the rebuild must still normalise it
            # to the writer's text form, because the reviewed migration-615 digest hashes
            # that text.
            equal_id = "dignity_scores"
            seed_text = json.dumps(
                next(r for r in CONSTANTS if r["constant_id"] == equal_id)["value_jsonb"])
            padded = seed_text.replace(": 0.8,", ": 0.80,").replace(": 1.0,", ": 1.00,")
            assert padded != seed_text
            conn.execute(
                "UPDATE brahma_formula_constants SET value_jsonb=%s::jsonb, version='3.0' "
                "WHERE constant_id=%s", (padded, equal_id))
            padded_stored = conn.execute(
                "SELECT value_jsonb::text AS t FROM brahma_formula_constants WHERE constant_id=%s",
                (equal_id,)).fetchone()["t"]
            assert "0.80" in padded_stored and "1.00" in padded_stored     # jsonb keeps the typed scale

            seed_formula_constants(conn, autocommit=False)   # the rebuild
            after = {r["constant_id"]: r for r in conn.execute(
                "SELECT *, value_jsonb::text AS value_text FROM brahma_formula_constants").fetchall()}

            # calibrated value and its version survive; descriptive column converges
            assert after[calibratable_id]["value_jsonb"] == {"calibrated": 1.23}
            assert after[calibratable_id]["value_jsonb"] != seed_value
            assert after[calibratable_id]["version"] == "2.0"
            assert after[calibratable_id]["citation_or_ratification"] == \
                first[calibratable_id]["citation_or_ratification"]
            # the classical constant is converged back to the seed
            assert after[classical_id]["value_jsonb"] == first[classical_id]["value_jsonb"]
            assert after[classical_id]["version"] == first[classical_id]["version"]
            # equal-to-seed value: text normalised back, version converged
            assert after[equal_id]["value_text"] == first[equal_id]["value_text"]
            assert after[equal_id]["value_text"] != padded_stored
            assert after[equal_id]["version"] == first[equal_id]["version"]
            # no other row moved
            for cid in first:
                if cid not in (calibratable_id, classical_id, equal_id):
                    assert after[cid]["value_jsonb"] == first[cid]["value_jsonb"], cid
            assert len(after) == len(CONSTANTS)
        finally:
            conn.rollback()
