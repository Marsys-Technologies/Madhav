"""
TI-l1-panchanga-moon-sign-001 — chandra_bala_natal_baseline birth Moon sign.

Defect: `_emit_chandra_bala_baseline` derived the birth Moon SIGN from the
nakshatra id (`((nak_id - 1) * 4) // 9 + 1`) — the sign of the nakshatra's
START — instead of reading the Moon's sign. Purva Bhadrapada (id 25) straddles
Aquarius (pada 1-3) and Pisces (pada 4), so the formula said Aquarius for every
ayanamsha even where the Moon sits in the Pisces portion.

Fix under test: the writer READS the upstream ga_positions fact
(`graha_position | MOON | sign`, English sign name) for each ayanamsha and
raises when it is absent or unrecognised (CLAUDE.md §N.5 / §N.7).

All data here is SYNTHETIC (a made-up chart id and made-up per-ayanamsha Moon
signs); no real chart value is read or embedded.
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from tests.test_ga4_writer import _make_forensic_pi  # noqa: E402  (reuse the pi fixture)

SYNTH_CHART_ID = "00000000-0000-4000-8000-00000000c0de"
BUILD_ID = "test-chandra-sign-build"
COMPUTED_AT = "2026-06-10T00:00:00+00:00"
AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

# Independent hand-derived expectations (position 1 = the birth Moon's own sign;
# classical Chandra Bala: 1,3,6,7,10,11 favourable; 9 neutral here; others not).
# Birth Moon in Aquarius (Kumbha): position of transit sign = (sign - 11) % 12 + 1.
EXPECTED_AQUARIUS = {
    "KUMBHA": "favorable", "MEENA": "unfavorable", "MESHA": "favorable",
    "VRISHABHA": "unfavorable", "MITHUNA": "unfavorable", "KARKA": "favorable",
    "SIMHA": "favorable", "KANYA": "unfavorable", "TULA": "neutral",
    "VRISHCHIKA": "favorable", "DHANU": "favorable", "MAKARA": "unfavorable",
}
# Birth Moon in Pisces (Meena): position = (sign - 12) % 12 + 1.
EXPECTED_PISCES = {
    "MEENA": "favorable", "MESHA": "unfavorable", "VRISHABHA": "favorable",
    "MITHUNA": "unfavorable", "KARKA": "unfavorable", "SIMHA": "favorable",
    "KANYA": "favorable", "TULA": "unfavorable", "VRISHCHIKA": "neutral",
    "DHANU": "favorable", "MAKARA": "favorable", "KUMBHA": "unfavorable",
}


def _w():
    from ga_writers import ga_panchanga_writer
    return ga_panchanga_writer


def _by_subject(rows: list[dict]) -> dict[str, str]:
    return {r["fact_subject"].replace("TRANSIT_SIGN_", ""): r["fact_value_text"] for r in rows}


def _emit(sign: Any, ay: str = "lahiri_chitrapaksha") -> list[dict]:
    return _w()._emit_chandra_bala_baseline(SYNTH_CHART_ID, BUILD_ID, COMPUTED_AT, ay, sign)


# ── (1) the two portions of Purva Bhadrapada ─────────────────────────────────

def test_moon_in_aquarius_portion_of_purva_bhadrapada():
    rows = _emit("Aquarius")
    assert _by_subject(rows) == EXPECTED_AQUARIUS
    assert all("birth Moon sign=Kumbha" in r["citation_human"] for r in rows)


def test_moon_in_pisces_portion_of_purva_bhadrapada():
    """The case the nakshatra-id formula got wrong (it always yielded Aquarius)."""
    rows = _emit("Pisces")
    assert _by_subject(rows) == EXPECTED_PISCES
    assert all("birth Moon sign=Meena" in r["citation_human"] for r in rows)


def test_pisces_and_aquarius_differ_in_exactly_nine_classifications():
    a, p = _by_subject(_emit("Aquarius")), _by_subject(_emit("Pisces"))
    assert sorted(k for k in a if a[k] != p[k]) == sorted(
        ["MEENA", "MESHA", "VRISHABHA", "KARKA", "KANYA", "TULA", "VRISHCHIKA", "MAKARA", "KUMBHA"]
    )


@pytest.mark.parametrize("sign_en, sign_id", [
    ("Aries", 1), ("Taurus", 2), ("Gemini", 3), ("Cancer", 4), ("Leo", 5), ("Virgo", 6),
    ("Libra", 7), ("Scorpio", 8), ("Sagittarius", 9), ("Capricorn", 10),
    ("Aquarius", 11), ("Pisces", 12),
])
def test_every_sign_is_read_as_given_not_derived(sign_en, sign_id):
    """The birth sign's own transit row is position 1 (favourable) for ALL 12 signs,
    independent of any nakshatra."""
    rows = _emit(sign_en)
    own = _w().SIGN_NAMES[sign_id - 1].upper()
    assert _by_subject(rows)[own] == "favorable"
    assert len(rows) == 12


# ── (2) absent / unrecognised position fact raises (no default) ──────────────

@pytest.mark.parametrize("bad", [None, "", "Kumbha", "aquarius", 11, "unknown"])
def test_absent_or_unrecognised_moon_sign_raises(bad):
    with pytest.raises(RuntimeError, match="graha_position\\|MOON\\|sign"):
        _emit(bad)


def test_tara_bala_has_no_owner_chart_fallback():
    w = _w()
    for bad_pi in (None, MagicMock(nakshatra=None), MagicMock(nakshatra=MagicMock(id=None)),
                   MagicMock(nakshatra=MagicMock(id=0)), MagicMock(nakshatra=MagicMock(id=28))):
        with pytest.raises(ValueError, match="nakshatra"):
            w._emit_tara_bala_baseline(bad_pi, SYNTH_CHART_ID, BUILD_ID, COMPUTED_AT, "lahiri_chitrapaksha")


def test_tara_bala_uses_nakshatra_id_only():
    """Sibling check: tara_bala_natal_baseline is a pure function of the nakshatra id."""
    w = _w()
    pi = _make_forensic_pi()
    rows = w._emit_tara_bala_baseline(pi, SYNTH_CHART_ID, BUILD_ID, COMPUTED_AT, "lahiri_chitrapaksha")
    by = {r["fact_subject"]: r["fact_value_text"] for r in rows}
    assert by["TRANSIT_NAK_PPB"] == "Janma"  # birth nakshatra = id 25
    pi2 = _make_forensic_pi()
    pi2.nakshatra.id = 1
    rows2 = w._emit_tara_bala_baseline(pi2, SYNTH_CHART_ID, BUILD_ID, COMPUTED_AT, "lahiri_chitrapaksha")
    assert {r["fact_subject"]: r["fact_value_text"] for r in rows2}["TRANSIT_NAK_ASH"] == "Janma"


# ── (3) end-to-end: emitted birth sign == the position fact, all 5 ayanamshas ─

class _Cur:
    def __init__(self, rows):
        self._rows = rows
        self.rowcount = 0

    def fetchall(self):
        return list(self._rows)


class _FakeConn:
    """Minimal psycopg-like connection: answers the Moon-sign SELECT from a
    synthetic position-fact table, swallows delete/authorize, records INSERTs."""

    def __init__(self, moon_sign_by_ay: dict[str, str], dict_rows: bool = True):
        self.moon_sign_by_ay = moon_sign_by_ay
        self.dict_rows = dict_rows
        self.inserted: list[dict] = []
        self.selects: list[tuple] = []

    def execute(self, sql, params=None):
        text = " ".join(sql.split())
        if text.startswith("SELECT DISTINCT ON (ayanamsha_id)"):
            assert "fact_category = 'graha_position'" in text
            assert "fact_subject = 'MOON'" in text and "fact_key = 'sign'" in text
            assert "ORDER BY ayanamsha_id, computed_at DESC, build_id DESC" in text
            self.selects.append(tuple(params))
            rows = [
                {"ayanamsha_id": a, "fact_value_text": s} if self.dict_rows else (a, s)
                for a, s in self.moon_sign_by_ay.items()
            ]
            return _Cur(rows)
        if text.startswith("INSERT INTO chart_facts"):
            self.inserted.append(dict(params))
        return _Cur([])


def _run_build(monkeypatch, conn: _FakeConn) -> dict:
    w = _w()
    import panchang_engine

    monkeypatch.setattr(panchang_engine, "panchanga_instant", lambda *a, **k: _make_forensic_pi())
    monkeypatch.setattr(w, "resolve_birth_params", lambda cid, bp: {
        "datetime_local": datetime(2001, 1, 1, 6, 0), "latitude_deg": 10.0,
        "longitude_deg": 20.0, "tz_offset_minutes": 0,
    })
    return w.build_ga_panchanga(chart_id=SYNTH_CHART_ID, build_id=BUILD_ID, conn=conn)


# Synthetic: a chart whose Moon is in Pisces for two ayanamshas and Aquarius for
# three — covers both portions of Purva Bhadrapada inside one build.
SYNTH_MOON_SIGNS = {
    "lahiri_chitrapaksha": "Aquarius",
    "true_chitra": "Aquarius",
    "krishnamurti": "Aquarius",
    "raman": "Pisces",
    "surya_siddhanta_classical": "Pisces",
}


@pytest.mark.parametrize("dict_rows", [True, False])
def test_build_emits_birth_sign_equal_to_position_fact_for_all_five(monkeypatch, dict_rows):
    conn = _FakeConn(SYNTH_MOON_SIGNS, dict_rows=dict_rows)
    _run_build(monkeypatch, conn)
    assert conn.selects == [(SYNTH_CHART_ID, AYANAMSHAS)]

    sanskrit = {"Aquarius": "Kumbha", "Pisces": "Meena"}
    expected = {"Aquarius": EXPECTED_AQUARIUS, "Pisces": EXPECTED_PISCES}
    seen_ays = set()
    for ay in AYANAMSHAS:
        rows = [r for r in conn.inserted
                if r["fact_category"] == "chandra_bala_natal_baseline" and r["ayanamsha_id"] == ay]
        assert len(rows) == 12, ay
        fact_sign = SYNTH_MOON_SIGNS[ay]
        emitted = {re.search(r"birth Moon sign=(\w+)", r["citation_human"]).group(1) for r in rows}
        assert emitted == {sanskrit[fact_sign]}, f"{ay}: emitted {emitted} vs position fact {fact_sign}"
        assert _by_subject([{"fact_subject": r["fact_subject"], "fact_value_text": r["fact_value_text"]}
                            for r in rows]) == expected[fact_sign]
        seen_ays.add(ay)
    assert seen_ays == set(AYANAMSHAS)


def test_build_raises_before_any_insert_when_an_ayanamsha_lacks_the_position_fact(monkeypatch):
    partial = {k: v for k, v in SYNTH_MOON_SIGNS.items() if k != "surya_siddhanta_classical"}
    conn = _FakeConn(partial)
    with pytest.raises(RuntimeError, match="surya_siddhanta_classical"):
        _run_build(monkeypatch, conn)
    assert conn.inserted == []


# ── (4) structural: no nakshatra-id -> sign derivation left in the L1 writers ─

def test_no_nakshatra_id_to_sign_formula_in_ga_writers():
    root = pathlib.Path(__file__).parent.parent / "ga_writers"
    pat = re.compile(r"\*\s*4\s*\)\s*//\s*9")
    offenders = [
        f"{p.name}:{i}"
        for p in sorted(root.glob("*.py"))
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if pat.search(line) and not line.lstrip().startswith("#")
    ]
    assert offenders == []
    src = (root / "ga_panchanga_writer.py").read_text(encoding="utf-8")
    assert "NATIVE_MOON_NAK_ID" not in src and "NATIVE_MOON_SIGN_ID" not in src


# ── (5) the real-Postgres module's disposable-database guard (DB-free unit tests) ─

OK_DB = "ga4_moon_sign_test"


@pytest.mark.parametrize("dsn", [
    f"postgresql://postgres:postgres@localhost:5432/{OK_DB}",
    f"postgresql://u@/{OK_DB}?host=/private/tmp/claude-504/pms",
    f"postgresql://u@127.0.0.1/{OK_DB}",
    f"postgresql://u@[::1]:5432/{OK_DB}",
    f"host=localhost dbname={OK_DB} user=u",
    f"host=/var/run/postgresql dbname={OK_DB}",
    f"dbname={OK_DB}",  # no host at all: libpq default unix socket
])
def test_guard_accepts_only_the_exact_local_database(dsn):
    from tests.test_ga4_chandra_bala_birth_sign_pg import require_disposable
    assert require_disposable(dsn, {}) == OK_DB


REFUSED_DSNS = [
    # other names
    "postgresql://u:p@localhost:5432/pms_test",
    "postgresql://u:p@localhost:5432/some_other_test",
    f"postgresql://u:p@localhost:5432/{OK_DB}_backup",
    f"postgresql://u:p@localhost:5432/staging_{OK_DB}",
    "postgresql://u:p@localhost:5432/GA4_MOON_SIGN_TEST",
    "postgresql://u:p@localhost:5432/madhav_prod_test",
    "postgresql://u:p@localhost:5432/postgres",
    "postgresql://u:p@localhost:5432/amjis",
    "postgresql://u:p@localhost:5432/chart_facts",
    "postgresql://u:p@localhost:5432/",
    # remote single hosts
    f"postgresql://u:p@db.internal.example.com:5432/{OK_DB}",
    f"postgresql://u:p@10.0.0.5/{OK_DB}",
    "postgresql://u@/amjis?host=/cloudsql/proj:region:inst",
    f"postgresql://u@/{OK_DB}?host=db.example.com",
    # multi-host: libpq fails over to the later host (urlparse().hostname sees only the first)
    f"postgresql://u:p@localhost:5432,db.prod.example.com:5432/{OK_DB}",
    f"postgresql://u:p@localhost,db.prod.example.com/{OK_DB}",
    f"postgresql://u:p@localhost,10.0.0.5/{OK_DB}",
    f"postgresql://u:p@localhost:5432,10.0.0.5:5432/{OK_DB}",
    f"postgresql://u:p@10.0.0.5,localhost/{OK_DB}",
    f"postgresql://u:p@localhost,127.0.0.1/{OK_DB}",  # even all-loopback multi-host is refused
    f"postgresql://u@/{OK_DB}?host=/a,db.example.com",
    f"host=localhost,db.prod.example.com dbname={OK_DB}",
    f"host=localhost,10.0.0.5 port=5432,5432 dbname={OK_DB}",
    # query-string / keyword overrides
    f"postgresql://u@localhost/{OK_DB}?hostaddr=10.0.0.5",
    f"postgresql://u@localhost/{OK_DB}?dbname=amjis",
    f"postgresql://u@localhost/{OK_DB}?service=prod",
    f"postgresql://u@localhost/{OK_DB}?sslmode=require",
    f"host=localhost hostaddr=10.0.0.5 dbname={OK_DB}",
    f"host=localhost service=prod dbname={OK_DB}",
    f"host=db.prod.example.com dbname={OK_DB}",
    "host=localhost dbname=amjis",
    # unparseable
    "postgresql://u@[localhost/ga4_moon_sign_test",
]


@pytest.mark.parametrize("dsn", REFUSED_DSNS)
def test_guard_refuses_every_other_target(dsn):
    from tests.test_ga4_chandra_bala_birth_sign_pg import RefusedError, require_disposable
    with pytest.raises(RefusedError, match="REFUSED"):
        require_disposable(dsn, {})


@pytest.mark.parametrize("dsn, env", [
    # the DSN leaves the host unset, so libpq takes PGHOST / PGHOSTADDR from the environment
    (f"dbname={OK_DB}", {"PGHOST": "db.prod.example.com"}),
    (f"dbname={OK_DB}", {"PGHOST": "localhost,db.prod.example.com"}),
    (f"dbname={OK_DB}", {"PGHOST": "10.0.0.5"}),
    (f"postgresql:///{OK_DB}", {"PGHOST": "db.prod.example.com"}),
    # PGHOSTADDR wins over host even when the DSN names a local host
    (f"dbname={OK_DB}", {"PGHOSTADDR": "10.0.0.5"}),
    (f"host=localhost dbname={OK_DB}", {"PGHOSTADDR": "10.0.0.5"}),
    (f"postgresql://u@localhost/{OK_DB}", {"PGHOSTADDR": "10.0.0.5"}),
    (f"host=localhost dbname={OK_DB}", {"PGHOSTADDR": "10.0.0.5,127.0.0.1"}),
    # service files can redirect everything; a database override changes the target
    (f"dbname={OK_DB}", {"PGSERVICE": "prod"}),
    (f"host=localhost dbname={OK_DB}", {"PGSERVICE": "prod"}),
    (f"host=localhost dbname={OK_DB}", {"PGDATABASE": "amjis"}),
])
def test_guard_refuses_environment_overrides(dsn, env):
    from tests.test_ga4_chandra_bala_birth_sign_pg import RefusedError, require_disposable
    with pytest.raises(RefusedError, match="REFUSED"):
        require_disposable(dsn, env)


def test_guard_ignores_a_remote_PGHOST_that_libpq_itself_ignores():
    """libpq ignores PGHOST when the DSN names a host, so the target is still local."""
    from tests.test_ga4_chandra_bala_birth_sign_pg import require_disposable
    assert require_disposable(f"host=localhost dbname={OK_DB}", {"PGHOST": "db.prod.example.com"}) == OK_DB


def test_guard_allows_loopback_environment_values():
    from tests.test_ga4_chandra_bala_birth_sign_pg import require_disposable
    assert require_disposable(f"dbname={OK_DB}", {"PGHOST": "localhost", "PGDATABASE": OK_DB}) == OK_DB
    assert require_disposable(f"dbname={OK_DB}", {"PGHOSTADDR": "127.0.0.1"}) == OK_DB


def test_guard_reads_the_process_environment_by_default(monkeypatch):
    from tests.test_ga4_chandra_bala_birth_sign_pg import RefusedError, require_disposable
    monkeypatch.setenv("PGHOSTADDR", "10.0.0.5")
    with pytest.raises(RefusedError, match="hostaddr"):
        require_disposable(f"host=localhost dbname={OK_DB}")


@pytest.mark.parametrize("db, addr, ok", [
    (OK_DB, None, True), (OK_DB, "127.0.0.1", True), (OK_DB, "::1", True),
    (OK_DB, "127.0.0.1/32", True),
    (OK_DB, "10.0.0.5", False), (OK_DB, "10.0.0.5/32", False),
    ("postgres", None, False), ("amjis", "127.0.0.1", False), ("ga4_moon_sign_test_backup", None, False),
])
def test_post_connect_check_pure(db, addr, ok):
    from tests.test_ga4_chandra_bala_birth_sign_pg import RefusedError, require_connected_to_disposable
    if ok:
        require_connected_to_disposable(db, addr)
    else:
        with pytest.raises(RefusedError, match="REFUSED"):
            require_connected_to_disposable(db, addr)


def test_guard_refuses_to_truncate_a_chart_facts_that_looks_real():
    from tests.test_ga4_chandra_bala_birth_sign_pg import RefusedError, require_minimal_table
    require_minimal_table(set())  # absent table: fine
    require_minimal_table({"chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject",
                           "fact_key", "fact_value_text", "fact_value_num", "computed_at"})
    with pytest.raises(RefusedError, match="not a disposable table"):
        require_minimal_table({"chart_id", "fact_id", "citation_human", "verification_pass_status"})
