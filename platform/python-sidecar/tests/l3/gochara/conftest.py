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
import os
from pathlib import Path

import pytest

# C22: no hard-coded personal path. The pinned .se1 corpus directory comes from
# SE_EPHE_PATH — the one variable the Swiss C library itself honours (see
# panchang_engine/swiss_backend.py), the one ci.yml exports when it downloads
# the corpus, and the one the root python-sidecar conftest populates locally
# (MARSYS_TEST_SE1_DIR / SWE_EPHE_PATH / /app/ephe / /tmp/se1). When the corpus
# is missing or fails the pinned checksums the Swiss tests skip NOT_RUN with an
# explicit reason — unless GOCHARA_SE1_REQUIRE=1, which makes an unusable corpus
# a hard failure instead of a silent skip (CLAUDE.md §N.8: green because skipped
# is not evidence).
EPHE_PATH = os.environ.get("SE_EPHE_PATH", "")

SE1_CHECKSUMS = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}


def _verify_se1() -> dict[str, str]:
    problems = []
    actual = {}
    if not EPHE_PATH:
        problems.append("SE_EPHE_PATH is unset — no pinned .se1 corpus directory provided")
        return problems, actual
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

if _PROBLEMS and os.environ.get("GOCHARA_SE1_REQUIRE") == "1":
    raise RuntimeError(
        "GOCHARA_SE1_REQUIRE=1 and the pinned .se1 corpus is unusable — refusing "
        "to skip these tests (CLAUDE.md §N.8): " + "; ".join(_PROBLEMS)
    )

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


# ── §12.5 earned-signal guard: the real ephemeris, or a NAMED failure ────────
# The mean-node convention test (test_wp3a_kernel::test_case_02_mean_node_convention)
# once failed in a full-suite run with "jd -0.001010 outside Moshier planet range"
# — an error that names neither the cause nor the culprit. It has not reproduced
# since (every pairwise ordering and the full suite pass with and without a
# reachable database), so the cause is UNKNOWN and is recorded as such. What can
# be made true is that a recurrence identifies itself: real-ephemeris tests call
# this first, and it fails LOUDLY if the module is a stub or the calendar
# conversion is wrong, rather than letting a stubbed global decide a ruled
# convention's test. F-31 records the Swiss ephemeris path as process-global.
J2000_JD = 2451545.0  # 2000-01-01 12:00 UT


def assert_real_ephemeris() -> None:
    import types

    import swisseph as swe

    if not isinstance(swe, types.ModuleType):
        raise AssertionError(
            f"the swisseph module is {type(swe).__name__}, not a real module — a "
            "test left the process-global ephemeris stubbed (finding F-31)"
        )
    jd = swe.julday(2000, 1, 1, 12.0)
    if jd != J2000_JD:
        raise AssertionError(
            f"swe.julday(2000,1,1,12.0) returned {jd!r}, expected {J2000_JD} — the "
            "ephemeris calendar function is stubbed or replaced (finding F-31); a "
            "real-ephemeris result computed now would be meaningless"
        )


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
    "WP6_LEDGER_DSN", "postgresql://wp6:local@localhost:55433/wp6"
)

WP6_MIGRATION_1072 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql"
)

# §12.3 (4.13a–d) additive follow-on to 1081: inclusivity, the six-state F06
# completeness CHECK, time_basis CHECK, tier_basis, and the fourth coverage
# partition kind. Applied after 1081 on the same disposable DB (E-011).
WP6_MIGRATION_1087 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql"
)

# Pravāha A2.1: t_exact nullable + exact_crossing/t_exact consistency CHECK +
# truncated_at_horizon 'both' (N3 truncated contacts persistable). Applied
# after 1081/1087 on the same disposable DB.
WP6_MIGRATION_1152 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1152_kala_gochara_contacts_t_exact_nullable_truncated.sql"
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
    """Apply migration 1081 (formerly 1076) + the §12.3 follow-on 1087 to a
    fresh schema on the disposable DB.

    Skips the requesting test NOT_RUN when the disposable DB is unreachable.
    """
    if not _wp6_check_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(WP6_DROP_SQL)
    conn.execute(WP6_MIGRATION_1072.read_text())
    conn.execute(WP6_MIGRATION_1087.read_text())
    conn.execute(WP6_MIGRATION_1152.read_text())
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


@pytest.fixture(autouse=True, scope="module")
def _fresh_contact_reconstruct_cache():
    """C52: `contact_reconstruct._CACHE` is a PROCESS-WIDE memo keyed by the position source's declared `cache_key`
    (e.g. ("swiss", EPHE_PATH)) plus body/cells/horizon. Two test modules that build DIFFERENT position functions under
    the SAME key (a stand-in sky in one, the real ephemeris in another) shared entries when the A5.3 suites run in ONE
    pytest process (the CI step), so a module's result depended on which module ran before it —
    test_a53_stored_scope_real_sky passed alone and failed in the combined run. Every module starts from an empty memo
    (within a module the memo still does its job: across the classes of one build); a key that is reused for a
    different source can no longer cross a module boundary."""
    from services.gochara_kernel import contact_reconstruct
    contact_reconstruct._CACHE.clear()
    yield
    contact_reconstruct._CACHE.clear()


# G8: the verification job refuses a candidate that does not claim every class its manifest pins (the class census,
# verification_job._enforce_class_census). A few older a53 job-mechanics suites deliberately build a ONE-class "subset world" (marriage)
# whose manifest, written by the real writer, pins all 26 -- exactly the 25-of-26 shape the census exists to refuse. Each such suite must
# OPT OUT BY NAME and say why: it declares a module-level `G8_CENSUS_OPT_OUT_REASON` string and `pytestmark =
# pytest.mark.usefixtures("g8_census_opt_out")`. The fixture refuses a module with no reason, and test_g8_class_census.py carries a guard that
# lists exactly which suites opt out and fails when a new one appears. Only the census step is set aside; everything else the job does runs.
@pytest.fixture()
def g8_census_opt_out(request, monkeypatch):
    reason = getattr(request.module, "G8_CENSUS_OPT_OUT_REASON", None)
    if not isinstance(reason, str) or len(reason.strip()) < 20:
        raise pytest.UsageError(f"{request.module.__name__} opts out of the G8 class census without a stated reason "
                                "(G8_CENSUS_OPT_OUT_REASON, at least 20 characters)")
    from services.gochara_kernel import verification_job as _vj
    monkeypatch.setattr(_vj, "_enforce_class_census", lambda *a, **k: None)
