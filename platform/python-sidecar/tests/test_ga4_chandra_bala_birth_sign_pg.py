"""
TI-l1-panchanga-moon-sign-001 — the position-fact read, executed on a REAL Postgres.

`_read_birth_moon_signs` selects ONE `graha_position | MOON | sign` row per ayanamsha with
`DISTINCT ON (ayanamsha_id) ... ORDER BY ayanamsha_id, computed_at DESC, build_id DESC`.
The DB-free tests in test_ga4_chandra_bala_birth_sign.py use a fake connection and therefore
cannot prove that SQL; this module does, against a disposable Postgres.

Needs GA4_MOON_SIGN_TEST_DATABASE_URL to point at a disposable database (the tests
CREATE/TRUNCATE a minimal `chart_facts` table carrying the production column types of the
columns the query touches: chart_id uuid, build_id uuid, computed_at timestamptz). All rows are
SYNTHETIC (made-up chart ids and signs); no birth data.

Marked `integration`, so the generic sidecar job (`-m "not integration"`, no DSN) deselects it.
Locally an explicit run SKIPs when the variable is unset. Under GITHUB_ACTIONS=true an explicit run
never skips: a missing variable or an unreachable database FAILS (ci.yml provisions the database and
sets the variable in the "TI-l1-panchanga-moon-sign-001" step of the DB-service job, which runs this
file with no -m filter).

Run:  GA4_MOON_SIGN_TEST_DATABASE_URL='postgresql:///ga4_moon_sign_test?host=/private/tmp/claude-504/pms' \
      python -m pytest tests/test_ga4_chandra_bala_birth_sign_pg.py
"""
from __future__ import annotations

import itertools
import json
import os
import pathlib
import subprocess
import sys

import re
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

URL = os.environ.get("GA4_MOON_SIGN_TEST_DATABASE_URL", "")
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
# `integration`: the generic sidecar job runs `pytest tests/ -m "not integration"` with no DSN and
# deselects this module; ci.yml's dedicated step runs the file with NO -m filter and the variable set.
pytestmark = pytest.mark.integration

SIDECAR = pathlib.Path(__file__).parent.parent
CHART = "00000000-0000-4000-8000-0000000000aa"
OTHER_CHART = "00000000-0000-4000-8000-0000000000bb"
AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
# Realistic pattern (synthetic): Aquarius for four ayanamshas, Pisces for surya_siddhanta.
SIGNS = {a: "Aquarius" for a in AYANAMSHAS}
SIGNS["surya_siddhanta_classical"] = "Pisces"

B_OLD = "00000000-0000-4000-8000-00000000b001"
B_MID = "00000000-0000-4000-8000-00000000b002"
B_NEW = "00000000-0000-4000-8000-00000000b003"


# ── disposable-database guard (the fixture TRUNCATEs chart_facts): exact name + local host + table guard ────────────
EXPECTED_DB_NAME = "ga4_moon_sign_test"
_LOOPBACK = {"localhost", "127.0.0.1", "::1"}
_MINIMAL_COLUMNS = {
    "chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject", "fact_key",
    "fact_value_text", "fact_value_num", "computed_at",
}


class RefusedError(RuntimeError):
    """The disposable-database guard refused the connection target."""


def _is_local(entry: str) -> bool:
    return entry == "" or entry in _LOOPBACK or entry.startswith("127.") or entry.startswith("/")


def require_disposable(dsn: str, environ: "dict[str, str] | None" = None) -> str:
    """Refuse unless EVERY connection target of `dsn` is local (loopback host or unix socket) and
    the database is EXACTLY `ga4_moon_sign_test`. This module TRUNCATEs `chart_facts`; a mis-set
    variable, a staging copy that merely ends in `_test`, a multi-host DSN that libpq would fail
    over to a remote second host, a `?hostaddr=`/`?dbname=` override, or a PGHOST/PGHOSTADDR/
    PGSERVICE/PGDATABASE environment override must never be reachable.

    Validation is on libpq's OWN parse (`conninfo_to_dict`), never on `urlparse().hostname`
    (which sees only the first host). Returns the database name."""
    from psycopg.conninfo import conninfo_to_dict

    env = os.environ if environ is None else environ
    try:
        parsed = urlparse(dsn)
        d = conninfo_to_dict(dsn)
    except Exception as exc:  # unparseable: refuse rather than guess
        raise RefusedError(f"REFUSED: DSN is not parseable ({type(exc).__name__})") from exc
    if "," in parsed.netloc:
        raise RefusedError("REFUSED: multi-host DSN (',' in the host list): libpq would fail over")
    if "://" in dsn:
        extra = set(parse_qs(parsed.query)) - {"host"}
        if extra:
            raise RefusedError(f"REFUSED: DSN query-string overrides {sorted(extra)} are not allowed")
    if d.get("service") or env.get("PGSERVICE"):
        raise RefusedError("REFUSED: a PGSERVICE / service= entry can redirect the target")
    # libpq falls back to the environment for whatever the DSN leaves unset; hostaddr from either
    # source wins over host.
    host = d.get("host") if d.get("host") is not None else env.get("PGHOST", "")
    hostaddr = d.get("hostaddr") if d.get("hostaddr") is not None else env.get("PGHOSTADDR", "")
    for label, value in (("host", host), ("hostaddr", hostaddr)):
        if "," in value:
            raise RefusedError(f"REFUSED: multi-valued {label} {value!r}: libpq would fail over")
        if not _is_local(value):
            raise RefusedError(f"REFUSED: {label} {value!r} is not loopback / a unix socket")
    name = d.get("dbname", "")
    if name != EXPECTED_DB_NAME:
        raise RefusedError(
            f"REFUSED: database {name!r} is not the disposable {EXPECTED_DB_NAME!r}; "
            "this module TRUNCATEs chart_facts"
        )
    if env.get("PGDATABASE") not in (None, "", EXPECTED_DB_NAME):
        raise RefusedError(f"REFUSED: PGDATABASE={env['PGDATABASE']!r} environment override")
    return name


def require_connected_to_disposable(current_database: str, server_addr: "str | None") -> None:
    """Post-connect check on what the server actually is: `current_database()` must be exactly
    `ga4_moon_sign_test` and, for a TCP connection, `inet_server_addr()` must be loopback
    (NULL for a unix socket)."""
    if current_database != EXPECTED_DB_NAME:
        raise RefusedError(
            f"REFUSED: connected to database {current_database!r}, not {EXPECTED_DB_NAME!r}"
        )
    if server_addr is not None and not _is_local(str(server_addr).split("/")[0]):
        raise RefusedError(f"REFUSED: connected to non-loopback server address {server_addr!r}")


def assert_connected_to_disposable(conn) -> None:
    row = conn.execute("SELECT current_database(), inet_server_addr()::text").fetchone()
    vals = list(row.values()) if isinstance(row, dict) else list(row)
    require_connected_to_disposable(vals[0], vals[1])


def require_minimal_table(existing_columns: set[str]) -> None:
    """Refuse to TRUNCATE a `chart_facts` that carries columns beyond this module's own minimal
    table (i.e. one that looks like the real table). An absent table (empty set) is fine."""
    extra = set(existing_columns) - _MINIMAL_COLUMNS
    if extra:
        raise RefusedError(
            "REFUSED: chart_facts already exists with columns this test did not create "
            f"({sorted(extra)[:4]}...): not a disposable table, refusing to TRUNCATE"
        )


def _no_database():
    msg = ("GA4_MOON_SIGN_TEST_DATABASE_URL is not set: the real-Postgres proof of the "
           "ga_panchanga position-fact read cannot run")
    if IN_CI:
        pytest.fail(msg + " (GITHUB_ACTIONS=true: this suite must run in CI, never skip)", pytrace=False)
    pytest.skip(msg)


def _connect(row_factory=None):
    if not URL:
        _no_database()
    import psycopg
    require_disposable(URL)
    kw = {"row_factory": row_factory} if row_factory else {}
    c = psycopg.connect(URL, **kw)
    try:
        assert_connected_to_disposable(c)
    except BaseException:
        c.close()
        raise
    return c


@pytest.fixture()
def conn():
    from psycopg.rows import dict_row
    if not URL:
        _no_database()
    c = _connect(dict_row)
    require_minimal_table({r["column_name"] for r in c.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = 'chart_facts'").fetchall()})
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS chart_facts (
          chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL,
          fact_category text NOT NULL, fact_subject text NOT NULL, fact_key text NOT NULL,
          fact_value_text text, fact_value_num double precision,
          computed_at timestamptz NOT NULL
        )
        """
    )
    c.execute("TRUNCATE chart_facts")
    c.commit()
    yield c
    c.rollback()
    c.close()


def _put(conn, ay, sign, build_id, computed_at, *, chart=CHART, cat="graha_position",
         subj="MOON", key="sign"):
    conn.execute(
        "INSERT INTO chart_facts (chart_id, ayanamsha_id, build_id, fact_category, fact_subject,"
        " fact_key, fact_value_text, computed_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::timestamptz)",
        [chart, ay, build_id, cat, subj, key, sign, computed_at],
    )


def _read(conn, chart=CHART):
    from ga_writers.ga_panchanga_writer import _read_birth_moon_signs
    return _read_birth_moon_signs(conn, chart)


def _seed_five_with_decoys(conn):
    for ay, sign in SIGNS.items():
        _put(conn, ay, sign, B_NEW, "2026-10-01T10:00:00Z")
        # decoys the pins must exclude
        _put(conn, ay, "Capricorn", B_NEW, "2026-10-02T10:00:00Z", subj="SUN")           # other graha
        _put(conn, ay, "3", B_NEW, "2026-10-02T10:00:00Z", key="pada")                   # other key
        _put(conn, ay, "Leo", B_NEW, "2026-10-02T10:00:00Z", cat="graha_sign_attributes")  # other category
        _put(conn, ay, "Gemini", B_NEW, "2026-10-02T10:00:00Z", chart=OTHER_CHART)       # other chart
    _put(conn, "not_canonical", "Taurus", B_NEW, "2026-10-02T10:00:00Z")                  # other ayanamsha
    conn.commit()


def test_five_ayanamshas_read_exactly_the_position_fact(conn):
    _seed_five_with_decoys(conn)
    assert _read(conn) == SIGNS
    # the other chart's own rows are read for that chart only (chart pin)
    assert _read(conn, OTHER_CHART) == {a: "Gemini" for a in AYANAMSHAS}
    assert _read(conn, "00000000-0000-4000-8000-0000000000cc") == {}


def test_tuple_row_connection_reads_the_same(conn):
    _seed_five_with_decoys(conn)
    t = _connect()  # default tuple rows (the standalone `_conn()` shape)
    try:
        assert _read(t) == SIGNS
    finally:
        t.close()


# Two build generations of the same key: the LATEST computed_at wins (the newer build's fact
# supersedes the older one), whatever order the rows were inserted in.
GENERATIONS = [
    (B_OLD, "2026-09-01T10:00:00Z", "Aquarius"),
    (B_NEW, "2026-10-01T10:00:00Z", "Pisces"),
]


@pytest.mark.parametrize("order", list(itertools.permutations(range(2))))
def test_two_generations_latest_build_wins_regardless_of_insert_order(conn, order):
    for i in order:
        b, ts, sign = GENERATIONS[i]
        _put(conn, "surya_siddhanta_classical", sign, b, ts)
    conn.commit()
    for _ in range(25):  # repeat: the plan must not flip between runs
        assert _read(conn) == {"surya_siddhanta_classical": "Pisces"}


@pytest.mark.parametrize("order", list(itertools.permutations(range(3))))
def test_three_generations_latest_wins_all_insert_orders(conn, order):
    gens = [
        (B_OLD, "2026-08-01T10:00:00Z", "Aries"),
        (B_MID, "2026-09-01T10:00:00Z", "Taurus"),
        (B_NEW, "2026-10-01T10:00:00Z", "Gemini"),
    ]
    for i in order:
        b, ts, sign = gens[i]
        _put(conn, "raman", sign, b, ts)
    conn.commit()
    for _ in range(10):
        assert _read(conn) == {"raman": "Gemini"}


@pytest.mark.parametrize("order", list(itertools.permutations(range(2))))
def test_equal_computed_at_is_broken_by_higher_build_id(conn, order):
    rows = [(B_OLD, "Aries"), (B_NEW, "Pisces")]  # same instant; B_NEW sorts higher
    for i in order:
        b, sign = rows[i]
        _put(conn, "raman", sign, b, "2026-10-01T10:00:00Z")
    conn.commit()
    for _ in range(25):
        assert _read(conn) == {"raman": "Pisces"}


def test_result_is_stable_across_python_hash_seeds(conn):
    for ay, sign in SIGNS.items():
        _put(conn, ay, "Aries", B_OLD, "2026-09-01T10:00:00Z")
        _put(conn, ay, sign, B_NEW, "2026-10-01T10:00:00Z")
    conn.commit()
    code = (
        "import json,os,psycopg;from psycopg.rows import dict_row;"
        "from ga_writers.ga_panchanga_writer import _read_birth_moon_signs as r;"
        "c=psycopg.connect(os.environ['GA4_MOON_SIGN_TEST_DATABASE_URL'],row_factory=dict_row);"
        f"print(json.dumps(r(c,'{CHART}'),sort_keys=True))"
    )
    outs = set()
    for seed in ("0", "1", "2", "3", "random"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-c", code], cwd=SIDECAR, env=env,
                           capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr[-500:]
        outs.add(p.stdout.strip().splitlines()[-1])
    assert outs == {json.dumps(SIGNS, sort_keys=True)}


def test_missing_position_fact_raises_with_a_clear_error(conn):
    from ga_writers.ga_panchanga_writer import _emit_chandra_bala_baseline
    for ay in AYANAMSHAS:
        if ay != "surya_siddhanta_classical":
            _put(conn, ay, SIGNS[ay], B_NEW, "2026-10-01T10:00:00Z")
    conn.commit()
    got = _read(conn)
    assert "surya_siddhanta_classical" not in got
    with pytest.raises(RuntimeError, match=r"graha_position\|MOON\|sign.*surya_siddhanta_classical.*None"):
        _emit_chandra_bala_baseline(CHART, "b", "t", "surya_siddhanta_classical",
                                    got.get("surya_siddhanta_classical"))


@pytest.mark.parametrize("bad", ["Kumbha", "aquarius", "", "Ophiuchus"])
def test_unrecognised_stored_sign_raises(conn, bad):
    from ga_writers.ga_panchanga_writer import _emit_chandra_bala_baseline
    _put(conn, "lahiri_chitrapaksha", bad, B_NEW, "2026-10-01T10:00:00Z")
    conn.commit()
    got = _read(conn)
    assert got == {"lahiri_chitrapaksha": bad}
    with pytest.raises(RuntimeError, match="lahiri_chitrapaksha"):
        _emit_chandra_bala_baseline(CHART, "b", "t", "lahiri_chitrapaksha", got["lahiri_chitrapaksha"])



def test_post_connect_check_accepts_the_disposable_and_refuses_another_database(conn):
    assert_connected_to_disposable(conn)  # the fixture's own connection
    import psycopg
    other = URL.replace("/" + EXPECTED_DB_NAME, "/postgres")  # a real, different database
    assert other != URL
    c = psycopg.connect(other)
    try:
        assert c.execute("SELECT current_database()").fetchone()[0] == "postgres"
        with pytest.raises(RefusedError, match="connected to database 'postgres'"):
            assert_connected_to_disposable(c)
    finally:
        c.close()
