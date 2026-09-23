"""Shared harness for the WP3a kernel gate tests (F-14 discipline).

Every Swiss comparison in this directory runs under the WP1_CONTRACTS.md §10
gate:
  * the three .se1 files' sha256 checksums are verified against the pinned
    values BEFORE any gate-grade computation; a mismatch skips the Swiss
    tests as NOT_RUN (never a pass on the wrong ephemeris);
  * `swe.set_ephe_path` points at the pinned directory; the kernel re-asserts
    the path on every calc through knots.calc_sidereal_lon;
  * every calc_ut retflag is asserted (`retflag & 2`); a Moshier fallback
    (retflag & 4) raises EphemerisBackendError which the tests convert into
    pytest.skip(reason) — NOT_RUN, never a silent pass.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

EPHE_PATH = "/Users/Dev/madhav-l3/gochara-wp0-7/.run/se1"

SE1_CHECKSUMS = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}


def _verify_se1() -> dict[str, str]:
    problems = []
    actual = {}
    for name, expected in SE1_CHECKSUMS.items():
        p = Path(EPHE_PATH) / name
        if not p.exists():
            problems.append(f"{name} missing at {p}")
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        actual[name] = digest
        if digest != expected:
            problems.append(f"{name} checksum {digest} != pinned {expected}")
    return problems, actual


_PROBLEMS, ACTUAL_CHECKSUMS = _verify_se1()

requires_swieph = pytest.mark.skipif(
    bool(_PROBLEMS),
    reason="NOT_RUN: .se1 ephemeris files missing or checksum mismatch: "
    + "; ".join(_PROBLEMS),
)

# Set the pinned ephemeris path for direct Swiss calls in this test directory
# (the kernel re-asserts it per-call; tests comparing raw swe.calc_ut need it
# set once at import time).
if not _PROBLEMS:
    import swisseph as swe

    swe.set_ephe_path(EPHE_PATH)


# ── WP6 disposable-database fixtures ─────────────────────────────────────────
# (WP6, ledger/coverage/publication — see test_wp6_ledger.py. Merged into this
# shared conftest; the WP3a section above is untouched.)
#
# The ONLY database these fixtures touch is the disposable WP6 Postgres
# (docker container gochara-wp6-disposable). If it is unreachable the WP6
# tests skip NOT_RUN — never fall back to any other DSN.

import os  # noqa: E402

import psycopg  # noqa: E402

WP6_DSN = os.environ.get(
    "WP6_LEDGER_DSN", "postgresql://wp6:disposable@localhost:55433/wp6"
)

WP6_MIGRATION_1072 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1072_nirmana_l3_gochara_ledger_coverage_publication.sql"
)

WP6_DROP_SQL = """
DROP TABLE IF EXISTS kala_gochara_contacts;
DROP TABLE IF EXISTS kala_gochara_coverage;
DROP TRIGGER IF EXISTS kala_gochara_convention_immutable ON kala_gochara_convention;
DROP FUNCTION IF EXISTS kala_gochara_convention_no_mutation();
DROP TABLE IF EXISTS kala_gochara_publication;
DROP TABLE IF EXISTS kala_gochara_convention;
"""


def _wp6_check_reachable() -> bool:
    try:
        with psycopg.connect(WP6_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def wp6_schema():
    """Apply migration 1072 to a fresh schema on the disposable DB.

    Skips the requesting test NOT_RUN when the disposable DB is unreachable.
    """
    if not _wp6_check_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(WP6_DROP_SQL)
    conn.execute(WP6_MIGRATION_1072.read_text())
    conn.close()
    return True


@pytest.fixture()
def conn(wp6_schema):
    """One autocommit connection per test; tests open explicit transactions."""
    c = psycopg.connect(WP6_DSN, autocommit=True)
    try:
        yield c
    finally:
        c.close()
