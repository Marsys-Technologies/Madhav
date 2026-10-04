"""
The karaka READERS, executed on a REAL Postgres (the first real execution must not be inside the rebuild window).

Three readers consume ga_sensitive's stored ``karaka_chara_position`` rows (the S-L1 lanes #2878 / #2886 / #2883):

  * ga_vargas   ``_read_jaimini_karakas``      -> {AK..DK: graha}      \\ ONE shared implementation,
  * ga_dashas   ``_read_karaka_roles``         -> {graha: AK..DK}      /  ga_writers/_karaka_roles.py
  * ga_structural ``_build_karaka_web_rows``   -> its own assigned_graha read (ORDER BY fact_subject, fact_id)

Every DB-free test of them uses a fake cursor, so the SQL itself (the pins, the total ORDER BY, the school filter,
the unique-index shape it runs against) had never been executed. This module runs it against a ``chart_facts`` with
the production column types, primary key (``fact_id``), the two partial unique indexes and the
verification_pass_status CHECK, on rows built by the REAL ga_sensitive writer (``_build_karaka_rows``, synthetic
longitudes, no birth data): five ayanamshas, both karaka schools (kn_rao_rahu_included 8-scheme and the
parashari_rahu_excluded 7-scheme variant) coexisting as they do in production.

What it proves: each reader returns exactly the stored kn_rao assignment per (chart, ayanamsha) and ignores every
decoy (other school / chart / ayanamsha / category / fact_key / NULL formula_id); it REFUSES (never defaults) on zero
rows, a duplicated row, a rank gap or duplicate rank, a duplicated graha, a missing/NULL half; a chart carrying TWO
build generations of the karaka rows is refused the same way under every insertion order, planner setting and
PYTHONHASHSEED (the total ORDER BY makes the refusal, and the row order the reader sees, reproducible; the readers
do NOT silently pick a generation).

Needs KARAKA_READER_TEST_DATABASE_URL pointing at a disposable database named EXACTLY ``karaka_reader_test`` on a
loopback host or unix socket (the fixture TRUNCATEs ``chart_facts``; see the guard below, SS N-46). All rows are
SYNTHETIC. The fixture only TRUNCATEs a ``chart_facts`` it created itself (stamped with a table-comment marker; a
production-shaped table without the marker, or holding any non-synthetic chart_id, is refused), and a unix-socket
target must be a real socket under the system temp dir. Marked ``integration``: the generic sidecar job (``-m "not integration"``) deselects the module; ci.yml's
dedicated step in the DB-service job runs it with no -m filter. Under GITHUB_ACTIONS=true a missing variable or an
unreachable database FAILS (never skips); locally an unset variable skips.

Run:  KARAKA_READER_TEST_DATABASE_URL='postgresql://postgres@/karaka_reader_test?host=/tmp/ikfx/sock&port=55471' \\
      python -m pytest tests/test_karaka_readers_pg.py -q
"""
from __future__ import annotations

import hashlib
import ipaddress
import itertools
import os
import pathlib
import random
import socket
import stat
import subprocess
import sys
import tempfile
from urllib.parse import parse_qs, urlparse

import pytest

SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SIDECAR))

URL = os.environ.get("KARAKA_READER_TEST_DATABASE_URL", "")
IN_CI = os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"
# `integration`: the generic sidecar job runs `pytest ... -m "not integration"` with no DSN and deselects this
# module; ci.yml's dedicated step runs the file with NO -m filter and the variable set.
pytestmark = pytest.mark.integration

EXPECTED_DB_NAME = "karaka_reader_test"
_LOOPBACK_NAMES = {"localhost"}
# The columns of the production chart_facts (read from the live catalog as the read-only reader role; counts and
# shape only). The fixture creates exactly this table; a pre-existing chart_facts that differs is refused.
PRODUCTION_COLUMNS = frozenset({
    "fact_id", "chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject", "fact_key",
    "fact_value_text", "fact_value_num", "fact_value_jsonb", "unit", "citation_ref", "citation_human",
    "source_calculation", "verification_pass_status", "engine_version", "salience_formula_ver", "computed_at",
    "tolerance_arcsec", "near_sign_boundary_flag", "near_nakshatra_boundary_flag", "vargottama_flag_at_point",
    "formula_provenance_text", "cross_ayanamsha_divergence_arcsec", "formula_id",
})


# ── disposable-database guard (SS N-46): the fixture TRUNCATEs chart_facts ──────────────────────────────────────
class RefusedError(RuntimeError):
    """The disposable-database guard refused the connection target."""


def _temp_roots() -> "set[str]":
    """The real paths of the system temp dir (and /tmp): the only place a unix-socket directory may live."""
    return {os.path.realpath(tempfile.gettempdir()), os.path.realpath("/tmp")}


def _is_test_socket_dir(directory: str, port: str) -> bool:
    """A unix-socket DIRECTORY this test may TRUNCATE through: absolute, EXISTS, resolves under the system temp dir (a
    Cloud SQL proxy directory such as /cloudsql/... or /var/run/postgresql never does), and holds a real unix socket
    named ``.s.PGSQL.<port>`` (os.stat S_ISSOCK), not merely any string that starts with '/'."""
    if not directory.startswith("/") or "," in port:
        return False
    real = os.path.realpath(directory)
    if not os.path.isdir(real):
        return False
    if not any(real == root or real.startswith(root.rstrip("/") + "/") for root in _temp_roots()):
        return False
    try:
        return stat.S_ISSOCK(os.stat(os.path.join(real, f".s.PGSQL.{port or '5432'}")).st_mode)
    except OSError:
        return False


def _is_local(entry: str, port: str = "5432", *, allow_socket: bool = True) -> bool:
    """A loopback NAME, a loopback IP LITERAL (127.0.0.0/8, ::1) or (``allow_socket``) a unix-socket directory that
    `_is_test_socket_dir` verifies. "" is NOT local here: libpq's default socket directory cannot be verified, so a
    DSN must name its host. A prefix test ("127.") would accept the hostname 127.0.0.1.evil.example, so IPs are parsed."""
    if entry in _LOOPBACK_NAMES:
        return allow_socket  # a loopback NAME is not an address literal: hostaddr must be an IP
    if entry.startswith("/"):
        return allow_socket and _is_test_socket_dir(entry, port)
    try:
        return ipaddress.ip_address(entry.strip("[]")).is_loopback
    except ValueError:
        return False


def require_disposable(dsn: str, environ: "dict[str, str] | None" = None) -> str:
    """Refuse unless EVERY libpq target of `dsn` (and of the environment) is local and the database is EXACTLY
    `karaka_reader_test`. Validation is on libpq's OWN parse (`conninfo_to_dict`), never on `urlparse().hostname`
    (which sees only the first host of a multi-host URI). Returns the database name."""
    from psycopg.conninfo import conninfo_to_dict

    env = os.environ if environ is None else environ
    try:
        parsed = urlparse(dsn)
        info = conninfo_to_dict(dsn)
    except Exception as exc:  # unparseable: refuse rather than guess
        raise RefusedError(f"REFUSED: DSN is not parseable ({type(exc).__name__})") from exc
    if "," in (parsed.netloc or ""):
        raise RefusedError("REFUSED: ',' in the DSN authority (multi-host failover list)")
    if "://" in dsn:
        extra = set(parse_qs(parsed.query)) - {"host", "port"}
        if extra:
            raise RefusedError(f"REFUSED: DSN query-string overrides {sorted(extra)} are not allowed")
    if info.get("service"):
        raise RefusedError("REFUSED: a service= entry can redirect the target")
    if not (info.get("host") or info.get("hostaddr")):
        raise RefusedError("REFUSED: the DSN names no host (libpq's default socket directory cannot be verified)")
    port = info.get("port", "") or "5432"
    for key in ("host", "hostaddr"):
        value = info.get(key, "")
        if "," in value:
            raise RefusedError(f"REFUSED: ',' in {key} (multi-host failover list)")
        if value and not _is_local(value, port, allow_socket=(key == "host")):
            raise RefusedError(
                f"REFUSED: {key} {value!r} is not loopback / a real unix socket under the temp dir")
    if info.get("dbname") != EXPECTED_DB_NAME:
        raise RefusedError(f"REFUSED: database {info.get('dbname')!r} is not the disposable {EXPECTED_DB_NAME!r}")
    # Environment overrides libpq would honour: PGHOSTADDR redirects the connection even when the DSN names a
    # host; PGHOST/PGDATABASE would redirect a DSN that omits them; PGSERVICE fills any unset parameter from a
    # service file we cannot see. Refused whatever the DSN says (stricter than needed, never looser).
    for var in ("PGHOST", "PGHOSTADDR"):
        env_port = (env.get("PGPORT", "") or port).strip()
        bad = [e for e in env.get(var, "").split(",")
               if e.strip() and not _is_local(e.strip(), env_port, allow_socket=(var == "PGHOST"))]
        if bad:
            raise RefusedError(f"REFUSED: environment {var} names a non-loopback target {bad}")
    if env.get("PGDATABASE") not in (None, "", EXPECTED_DB_NAME):
        raise RefusedError(f"REFUSED: environment PGDATABASE={env['PGDATABASE']!r} is not {EXPECTED_DB_NAME!r}")
    if env.get("PGSERVICE"):
        raise RefusedError("REFUSED: environment PGSERVICE is set (a service file could redirect the target)")
    return info["dbname"]


def require_connected_to_disposable(current_database: str) -> None:
    """Post-connect check on what the server actually is: `current_database()` must be EXACTLY
    `karaka_reader_test`. (Deliberately NOT a check of `inet_server_addr()`: behind the GitHub-Actions service
    container's port mapping the server's own address is the container's bridge IP, never loopback, so such a check
    would refuse the one legitimate CI target. The pre-connect libpq-target validation already pins the TCP
    destination to loopback.)"""
    if current_database != EXPECTED_DB_NAME:
        raise RefusedError(f"REFUSED: connected to database {current_database!r}, not {EXPECTED_DB_NAME!r}")


# The sentinel this module writes on ITS OWN table (COMMENT ON TABLE) the first time it creates it. A restored copy
# of production has the same columns but never this comment, so the column set alone is not trusted.
OWNER_MARKER = "karaka_readers_pg.py: disposable synthetic chart_facts created by tests/test_karaka_readers_pg.py"
SYNTHETIC_CHART_PREFIX = "00000000-0000-4000-8000-"


def require_disposable_chart_facts(
    existing_columns: "set[str]", table_comment: "str | None" = None, foreign_rows: int = 0,
) -> None:
    """Refuse to TRUNCATE a `chart_facts` that this module did not create. Absent (no columns) is fine (the fixture
    creates it and stamps OWNER_MARKER). A pre-existing table must (1) carry OWNER_MARKER as its table comment, (2)
    have EXACTLY the production-shaped column set, and (3) hold no row whose chart_id is outside this module's
    synthetic id range. Production-shaped columns WITHOUT the marker are refused (that is what a restored copy is)."""
    cols = set(existing_columns)
    if not cols:
        return
    if table_comment != OWNER_MARKER:
        raise RefusedError(
            "REFUSED: chart_facts already exists and does not carry this test's ownership marker (a restored copy "
            "of production has the same columns): not a table this module created, refusing to TRUNCATE. Drop it "
            "by hand if it really is disposable."
        )
    extra = sorted(cols - PRODUCTION_COLUMNS)
    if extra:
        raise RefusedError(
            "REFUSED: chart_facts already exists with columns this test did not create "
            f"({extra[:4]}...): not a disposable table, refusing to TRUNCATE"
        )
    if cols != PRODUCTION_COLUMNS:
        raise RefusedError(
            f"REFUSED: chart_facts already exists with a different shape (missing {sorted(PRODUCTION_COLUMNS - cols)[:4]}...)"
        )
    if foreign_rows:
        raise RefusedError(
            f"REFUSED: chart_facts holds {foreign_rows} row(s) whose chart_id is outside this module's synthetic range"
        )


# ── DB-free tests of the guard (they run in the explicit step; the module is `integration`) ─────────────────────
SOCK_PORT = "55461"


@pytest.fixture()
def unix_sock():
    """A REAL unix socket ``.s.PGSQL.<port>`` in a fresh SHORT directory under /tmp (AF_UNIX paths are <= ~104 bytes)."""
    import shutil
    d = tempfile.mkdtemp(prefix="krt", dir="/tmp")
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        srv.bind(os.path.join(d, f".s.PGSQL.{SOCK_PORT}"))
        yield d
    finally:
        srv.close()
        shutil.rmtree(d, ignore_errors=True)


_OK_URLS = [
    "postgresql://postgres:postgres@localhost:5432/karaka_reader_test",
    "postgresql://postgres:postgres@127.0.0.1:5432/karaka_reader_test",
    "postgresql://postgres:postgres@[::1]:5432/karaka_reader_test",
    "host=127.0.0.1 hostaddr=127.0.0.1 dbname=karaka_reader_test",
]
_BAD_URLS = [
    ("postgresql://u:p@localhost:5432,db.prod.example.com:5432/karaka_reader_test", "multi-host"),
    ("postgresql://u:p@db.prod.example.com:5432/karaka_reader_test", "not loopback"),
    ("postgresql://u:p@127.0.0.1.evil.example:5432/karaka_reader_test", "not loopback"),
    ("postgresql://u:p@localhost/karaka_reader_test?hostaddr=203.0.113.9", "query-string"),
    ("postgresql://u:p@localhost/karaka_reader_test?dbname=postgres", "query-string"),
    ("postgresql://u:p@localhost/karaka_reader_test?service=prod", "query-string"),
    ("postgresql://u:p@localhost:5432/postgres", "is not the disposable"),
    ("postgresql://u:p@localhost:5432/karaka_reader_test_2", "is not the disposable"),
    ("postgresql://u:p@localhost:5432/Karaka_Reader_Test", "is not the disposable"),
    ("postgresql://u:p@localhost:5432/", "is not the disposable"),
    ("postgresql://u:p@localhost:5432/staging_test", "is not the disposable"),
    ("host=db.prod.example.com dbname=karaka_reader_test", "not loopback"),
    ("host=localhost,db.prod.example.com dbname=karaka_reader_test", "multi-host"),
    ("host=localhost hostaddr=203.0.113.9 dbname=karaka_reader_test", "not loopback"),
    ("host=localhost hostaddr=127.0.0.1,203.0.113.9 dbname=karaka_reader_test", "multi-host"),
    ("host=localhost dbname=karaka_reader_test service=prod", "service"),
    ("postgresql://u:p@lo calhost:5432/karaka_reader_test", "not parseable"),
    # no host at all: libpq's default socket directory cannot be verified
    ("postgresql:///karaka_reader_test", "names no host"),
    ("dbname=karaka_reader_test", "names no host"),
    # a socket-looking host that is not a real socket under the temp dir
    ("host=/cloudsql/proj:region:inst dbname=karaka_reader_test port=5432", "not loopback"),
    ("host=/var/run/postgresql dbname=karaka_reader_test", "not loopback"),
    ("host=/tmp/definitely-not-there-krt dbname=karaka_reader_test port=55461", "not loopback"),
    ("host=/tmp dbname=karaka_reader_test port=55461", "not loopback"),  # exists, under /tmp, but holds no socket
]


@pytest.mark.parametrize("dsn", _OK_URLS)
def test_guard_accepts_loopback_targets(dsn):
    assert require_disposable(dsn, {}) == EXPECTED_DB_NAME


def test_guard_accepts_a_real_unix_socket_under_the_temp_dir(unix_sock):
    for dsn in (f"postgresql://postgres@/karaka_reader_test?host={unix_sock}&port={SOCK_PORT}",
                f"host={unix_sock} port={SOCK_PORT} dbname=karaka_reader_test"):
        assert require_disposable(dsn, {}) == EXPECTED_DB_NAME
    assert require_disposable("postgresql://postgres:postgres@localhost:5432/karaka_reader_test",
                              {"PGHOST": unix_sock, "PGPORT": SOCK_PORT}) == EXPECTED_DB_NAME


def test_guard_refuses_a_socket_dir_whose_file_is_not_a_unix_socket(unix_sock):
    # a regular file named like the socket (S_ISSOCK is false), in a directory that exists under /tmp
    other = tempfile.mkdtemp(prefix="krt", dir="/tmp")
    try:
        pathlib.Path(other, f".s.PGSQL.{SOCK_PORT}").write_text("not a socket")
        with pytest.raises(RefusedError, match="not loopback"):
            require_disposable(f"host={other} port={SOCK_PORT} dbname=karaka_reader_test", {})
    finally:
        import shutil
        shutil.rmtree(other, ignore_errors=True)
    # right dir, wrong port: the socket for THAT port does not exist
    with pytest.raises(RefusedError, match="not loopback"):
        require_disposable(f"host={unix_sock} port=5433 dbname=karaka_reader_test", {})


def test_guard_refuses_a_real_unix_socket_outside_the_temp_dir(unix_sock, monkeypatch):
    """A real socket in a directory that is NOT under the system temp dir (modelled by pointing the temp roots
    elsewhere) is refused: a socket file alone proves nothing (a Cloud SQL proxy directory holds real sockets)."""
    monkeypatch.setattr(sys.modules[__name__], "_temp_roots", lambda: {"/nonexistent-root"})
    with pytest.raises(RefusedError, match="not loopback"):
        require_disposable(f"host={unix_sock} port={SOCK_PORT} dbname=karaka_reader_test", {})


def test_guard_refuses_a_socket_path_as_hostaddr(unix_sock):
    with pytest.raises(RefusedError, match="not loopback"):
        require_disposable(f"host=localhost hostaddr={unix_sock} port={SOCK_PORT} dbname=karaka_reader_test", {})


@pytest.mark.parametrize("dsn,why", _BAD_URLS)
def test_guard_refuses_unsafe_dsn(dsn, why):
    with pytest.raises(RefusedError, match="REFUSED") as ei:
        require_disposable(dsn, {})
    assert why in str(ei.value) or why == "not parseable", (dsn, str(ei.value))


@pytest.mark.parametrize("env", [
    {"PGHOST": "db.prod.example.com"},
    {"PGHOST": "localhost,db.prod.example.com"},
    {"PGHOST": "/cloudsql/proj:region:inst"},
    {"PGHOST": "/tmp/definitely-not-there-krt"},
    {"PGHOSTADDR": "203.0.113.9"},
    {"PGHOSTADDR": "127.0.0.1,203.0.113.9"},
    {"PGSERVICE": "prod"},
    {"PGDATABASE": "postgres"},
    {"PGDATABASE": "karaka_reader_test_2"},
])
def test_guard_refuses_environment_overrides_even_with_a_good_dsn(env):
    with pytest.raises(RefusedError, match="REFUSED"):
        require_disposable("postgresql://postgres:postgres@localhost:5432/karaka_reader_test", env)


@pytest.mark.parametrize("env", [{"PGHOST": "localhost"}, {"PGHOST": ""},
                                 {"PGHOSTADDR": "127.0.0.1"}, {"PGDATABASE": "karaka_reader_test"}, {"PGSERVICE": ""}])
def test_guard_accepts_loopback_environment(env):
    assert require_disposable("postgresql://postgres:postgres@localhost:5432/karaka_reader_test", env) == EXPECTED_DB_NAME


def test_guard_reads_the_real_environment_by_default(monkeypatch):
    monkeypatch.setenv("PGHOSTADDR", "203.0.113.9")
    with pytest.raises(RefusedError, match="PGHOSTADDR"):
        require_disposable("postgresql://postgres:postgres@localhost:5432/karaka_reader_test")


@pytest.mark.parametrize("db", ["postgres", "karaka_reader_test_2", "Karaka_Reader_Test", ""])
def test_post_connect_check_refuses_the_wrong_database(db):
    with pytest.raises(RefusedError, match="REFUSED"):
        require_connected_to_disposable(db)


def test_post_connect_check_accepts_the_disposable_database():
    require_connected_to_disposable(EXPECTED_DB_NAME)


def test_chart_facts_shape_guard():
    # absent: fine (the fixture creates it and stamps the marker)
    require_disposable_chart_facts(set())
    require_disposable_chart_facts(set(), None)
    # this module's own table: marker + exact production column set + only synthetic rows
    require_disposable_chart_facts(set(PRODUCTION_COLUMNS), OWNER_MARKER)
    require_disposable_chart_facts(set(PRODUCTION_COLUMNS), OWNER_MARKER, 0)
    with pytest.raises(RefusedError, match="did not create"):
        require_disposable_chart_facts(set(PRODUCTION_COLUMNS) | {"some_real_extra_column"}, OWNER_MARKER)
    with pytest.raises(RefusedError, match="different shape"):
        require_disposable_chart_facts({"chart_id", "fact_id"}, OWNER_MARKER)
    with pytest.raises(RefusedError, match="outside this module's synthetic range"):
        require_disposable_chart_facts(set(PRODUCTION_COLUMNS), OWNER_MARKER, 3)


@pytest.mark.parametrize("comment", [None, "", "some production comment", OWNER_MARKER + " ", OWNER_MARKER.upper()])
def test_a_production_shaped_table_without_the_marker_is_refused(comment):
    """The reviewer's scenario: a restored production copy has EXACTLY the production columns. Without the marker
    this module stamps on its own table it is refused (the column set alone no longer passes)."""
    with pytest.raises(RefusedError, match="ownership marker"):
        require_disposable_chart_facts(set(PRODUCTION_COLUMNS), comment)


# ── production-shaped chart_facts + the real writer's rows ───────────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS chart_facts (
  fact_id                         text NOT NULL,
  chart_id                        uuid NOT NULL,
  ayanamsha_id                    text NOT NULL,
  build_id                        uuid NOT NULL,
  fact_category                   text NOT NULL,
  fact_subject                    text NOT NULL,
  fact_key                        text NOT NULL,
  fact_value_text                 text,
  fact_value_num                  numeric,
  fact_value_jsonb                jsonb,
  unit                            text,
  citation_ref                    text NOT NULL,
  citation_human                  text NOT NULL,
  source_calculation              text NOT NULL,
  verification_pass_status        text NOT NULL,
  engine_version                  text NOT NULL,
  salience_formula_ver            text,
  computed_at                     timestamptz NOT NULL,
  tolerance_arcsec                double precision,
  near_sign_boundary_flag         boolean DEFAULT false,
  near_nakshatra_boundary_flag    boolean DEFAULT false,
  vargottama_flag_at_point        boolean DEFAULT false,
  formula_provenance_text         text,
  cross_ayanamsha_divergence_arcsec double precision DEFAULT 0.0,
  formula_id                      text,
  CONSTRAINT chart_facts_pkey PRIMARY KEY (fact_id),
  CONSTRAINT chart_facts_verification_pass_status_check CHECK ((verification_pass_status = ANY (ARRAY[
    'two_pass_verified','classical_match','divergent_flagged','single','single_pass','documented_approximation',
    'computed_extension','floored','not_defined_for_nodes','scope_cap_sentinel','skipped_malformed_source',
    'external_computation_required','pending_w3_verification']))) NOT VALID
);
CREATE UNIQUE INDEX IF NOT EXISTS chart_facts_unique_null_formula
  ON chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id) WHERE (formula_id IS NULL);
CREATE UNIQUE INDEX IF NOT EXISTS chart_facts_unique_with_formula
  ON chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id, formula_id) WHERE (formula_id IS NOT NULL);
"""

INSERT_COLS = [
    "fact_id", "chart_id", "build_id", "ayanamsha_id", "engine_version", "fact_category", "fact_subject", "fact_key",
    "fact_value_num", "fact_value_text", "fact_value_jsonb", "formula_id", "source_calculation", "computed_at",
    "citation_ref", "citation_human", "verification_pass_status", "tolerance_arcsec", "near_sign_boundary_flag",
    "near_nakshatra_boundary_flag", "vargottama_flag_at_point", "formula_provenance_text",
    "cross_ayanamsha_divergence_arcsec",
]
INSERT_SQL = (
    "INSERT INTO chart_facts (" + ", ".join(INSERT_COLS) + ") VALUES ("
    + ", ".join("%s::jsonb" if c == "fact_value_jsonb" else "%s::timestamptz" if c == "computed_at" else "%s"
                for c in INSERT_COLS) + ")"
)

CHART = "00000000-0000-4000-8000-0000000000a1"
OTHER_CHART = "00000000-0000-4000-8000-0000000000b2"
BUILD_NEW = "00000000-0000-4000-8000-00000000c002"
BUILD_OLD = "00000000-0000-4000-8000-00000000c001"
AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
KN_RAO = "kn_rao_rahu_included"
PARASHARI = "parashari_rahu_excluded"
# SYNTHETIC sidereal longitudes (not any native's); each ayanamsha shifts them by its own offset, and the raman
# offset carries the Sun across a sign boundary so the assignments are NOT identical across the five.
BASE_LONGS = {"LAGNA": 12.5, "SUN": 301.2, "MOON": 331.7, "MAR": 47.9, "MER": 289.4, "JUP": 101.3,
              "VEN": 333.9, "SAT": 203.6, "RAH_MEAN": 17.4}
AYA_OFFSET = {"lahiri_chitrapaksha": 0.0, "true_chitra": 0.02, "krishnamurti": -0.09, "raman": 1.35,
              "surya_siddhanta_classical": 0.45}
ABBR = ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK")


def _writer():
    import ga_writers.ga_sensitive_writer as w
    return w


def writer_rows(chart: str, ayanamsha: str, build: str, *, shift: float = 0.0) -> "list[dict]":
    """The REAL ga_sensitive writer's karaka rows for synthetic longitudes (106 rows: 8x7 kn_rao + 1 strikaraka_alias
    + 7x7 parashari). `shift` perturbs every longitude so an older generation carries DIFFERENT assignments."""
    longs = {k: (v - AYA_OFFSET.get(ayanamsha, 0.0) + shift) % 360.0 for k, v in BASE_LONGS.items()}
    return _writer()._build_karaka_rows(longs, chart, ayanamsha, build, "karaka-reader-test/1", "/dev/null")


def reid(rows: "list[dict]", salt: str) -> "list[dict]":
    """Distinct fact_ids for a second generation. The writer's fact_id excludes build_id, so a same-id rebuild
    replaces (delete-then-insert) rather than coexists; two generations can only coexist in the production table
    (PK = fact_id) if their ids differ (e.g. an id-scheme change or an older writer version). That is what this
    models, with a 16-hex id like the real ones."""
    return [{**r, "fact_id": hashlib.sha256((r["fact_id"] + salt).encode()).hexdigest()[:16]} for r in rows]


def kn_rao_expected(rows: "list[dict]") -> "dict[int, str]":
    """Independent oracle read straight off the generated rows: {rank: graha} of the kn_rao school."""
    graha = {r["fact_subject"]: r["fact_value_text"] for r in rows
             if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha"}
    rank = {r["fact_subject"]: int(r["fact_value_num"]) for r in rows
            if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank"}
    assert len(graha) == len(rank) == 8
    return {rank[s]: graha[s] for s in graha}


def mk_row(template: dict, **over) -> dict:
    row = {**template, **over}
    if "fact_id" not in over:
        row["fact_id"] = hashlib.sha256(repr(sorted(
            (k, str(row[k])) for k in ("chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject",
                                       "fact_key", "formula_id", "fact_value_text", "fact_value_num"))).encode()
        ).hexdigest()[:16]
    return row


def order_rows(rows: "list[dict]", how: str) -> "list[dict]":
    if how == "asc":
        return sorted(rows, key=lambda r: (r["fact_subject"], r["fact_key"], r["fact_id"]))
    if how == "desc":
        return sorted(rows, key=lambda r: (r["fact_subject"], r["fact_key"], r["fact_id"]), reverse=True)
    out = list(rows)
    random.Random(int(how.removeprefix("shuffle"))).shuffle(out)
    return out


ORDERS = ["asc", "desc", "shuffle1", "shuffle2", "shuffle3"]
PLANS = {
    "default": [],
    "seqscan_only": ["SET enable_indexscan = off", "SET enable_bitmapscan = off", "SET enable_indexonlyscan = off"],
    "index_only": ["SET enable_seqscan = off"],
}


# ── fixtures ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _no_database():
    msg = ("KARAKA_READER_TEST_DATABASE_URL is not set: the real-Postgres proof of the karaka readers cannot run")
    if IN_CI:
        pytest.fail(msg + " (GITHUB_ACTIONS=true: this suite must run in CI, never skip)", pytrace=False)
    pytest.skip(msg)


def connect(**kw):
    """A guarded connection: DSN validated, then the live server verified. Fails (never skips) on a refusal."""
    import psycopg
    if not URL:
        _no_database()
    require_disposable(URL)
    try:
        c = psycopg.connect(URL, connect_timeout=5, **kw)
    except psycopg.OperationalError as exc:
        if IN_CI:
            pytest.fail(f"the disposable Postgres is unreachable under GITHUB_ACTIONS=true: {exc}", pytrace=False)
        pytest.skip(f"the disposable Postgres is unreachable: {exc}")
    try:
        row = c.execute("SELECT current_database()").fetchone()
        require_connected_to_disposable(list(row.values())[0] if isinstance(row, dict) else row[0])
    except BaseException:
        c.close()
        raise
    return c


@pytest.fixture()
def conn():
    c = connect()
    cols = {r[0] for r in c.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = 'chart_facts'").fetchall()}
    comment, foreign_rows = None, 0
    if cols:
        comment = c.execute(
            "SELECT obj_description(format('%I.chart_facts', current_schema())::regclass, 'pg_class')").fetchone()[0]
        if comment == OWNER_MARKER and cols == PRODUCTION_COLUMNS:
            foreign_rows = c.execute(
                "SELECT count(*) FROM chart_facts WHERE chart_id::text NOT LIKE %s",
                (SYNTHETIC_CHART_PREFIX + "%",)).fetchone()[0]
    require_disposable_chart_facts(cols, comment, foreign_rows)
    c.execute(DDL)
    if not cols:  # this module just created the table: stamp it so a later run recognises it as ITS OWN
        from psycopg import sql as _sql  # utility statements take no bind parameters: a quoted literal
        c.execute(_sql.SQL("COMMENT ON TABLE chart_facts IS {}").format(_sql.Literal(OWNER_MARKER)))
    c.execute("TRUNCATE chart_facts")
    c.commit()
    yield c
    c.rollback()
    c.close()


def seed(c, rows: "list[dict]", how: str = "asc") -> None:
    with c.cursor() as cur:
        cur.executemany(INSERT_SQL, [tuple(r[col] for col in INSERT_COLS) for r in order_rows(rows, how)])
    c.commit()


def set_plan(c, name: str) -> None:
    c.execute("RESET ALL")
    for stmt in PLANS[name]:
        c.execute(stmt)


def vargas():
    import ga_writers.ga_vargas_writer as m
    return m


def dashas():
    import ga_writers.ga_dashas_writer as m
    return m


def seed_five(c, chart: str = CHART, build: str = BUILD_NEW, how: str = "asc") -> "dict[str, list[dict]]":
    per_ay = {ay: writer_rows(chart, ay, build) for ay in AYANAMSHAS}
    seed(c, [r for rows in per_ay.values() for r in rows], how)
    return per_ay


# ── 1. happy path: five ayanamshas x both schools x both writers ─────────────────────────────────────────────────
def test_precondition_assignments_differ_across_ayanamshas():
    maps = {ay: tuple(sorted(kn_rao_expected(writer_rows(CHART, ay, BUILD_NEW)).items())) for ay in AYANAMSHAS}
    assert len(set(maps.values())) >= 2, "the synthetic longitudes must give the five ayanamshas different assignments"


@pytest.mark.parametrize("plan", list(PLANS))
@pytest.mark.parametrize("how", ["asc", "shuffle1"])
def test_five_ayanamshas_each_reader_returns_the_stored_kn_rao_assignment(conn, plan, how):
    per_ay = seed_five(conn, how=how)
    set_plan(conn, plan)
    for ay, rows in per_ay.items():
        exp = kn_rao_expected(rows)
        assert vargas()._read_jaimini_karakas(conn, CHART, ay) == {ABBR[r - 1]: g for r, g in exp.items()}
        assert dashas()._read_karaka_roles(conn, CHART, ay) == {g: ABBR[r - 1] for r, g in exp.items()}


def test_both_schools_coexist_and_the_seven_scheme_is_ignored(conn):
    per_ay = seed_five(conn)
    ay = AYANAMSHAS[0]
    n = conn.execute("SELECT count(*) FROM chart_facts WHERE chart_id=%s AND ayanamsha_id=%s AND formula_id=%s",
                     (CHART, ay, PARASHARI)).fetchone()[0]
    assert n == 49, "the 7-scheme variant (7 subjects x 7 keys) must be present as a decoy"
    # a 7-scheme assignment that DIFFERS from the 8-scheme at the same ranks must never leak into the read
    p7 = {r["fact_subject"]: r["fact_value_text"] for r in per_ay[ay]
          if r["formula_id"] == PARASHARI and r["fact_key"] == "assigned_graha"}
    got = vargas()._read_jaimini_karakas(conn, CHART, ay)
    assert set(got.values()) == set(kn_rao_expected(per_ay[ay]).values())
    assert "Rahu" in got.values() and len(got) == 8 and len(p7) == 7


def test_seven_scheme_only_is_refused_not_read(conn):
    seed(conn, [r for r in writer_rows(CHART, AYANAMSHAS[0], BUILD_NEW) if r["formula_id"] == PARASHARI])
    for fn in (vargas()._read_jaimini_karakas, dashas()._read_karaka_roles):
        with pytest.raises(vargas().KarakaDependencyMissing, match="no kn_rao karaka_chara_position rows"):
            fn(conn, CHART, AYANAMSHAS[0])


def test_strikaraka_alias_row_is_not_a_ninth_subject(conn):
    rows = writer_rows(CHART, AYANAMSHAS[0], BUILD_NEW)
    assert any(r["fact_key"] == "strikaraka_alias" for r in rows)
    seed(conn, rows)
    assert len(vargas()._read_jaimini_karakas(conn, CHART, AYANAMSHAS[0])) == 8


def test_the_two_writers_share_one_exception_class_and_one_reader():
    import ga_writers._karaka_roles as kr
    assert vargas().KarakaDependencyMissing is dashas().KarakaDependencyMissing is kr.KarakaDependencyMissing
    assert vargas().fetch_kn_rao_karaka_rows is dashas().fetch_kn_rao_karaka_rows is kr.fetch_kn_rao_karaka_rows


def test_dict_row_default_connection_reads_the_same(conn):
    """The orchestrator opens worker connections with row_factory=dict_row; the readers open their own tuple cursor."""
    from psycopg.rows import dict_row
    per_ay = seed_five(conn)
    d = connect(row_factory=dict_row)
    try:
        ay = AYANAMSHAS[3]
        exp = kn_rao_expected(per_ay[ay])
        assert vargas()._read_jaimini_karakas(d, CHART, ay) == {ABBR[r - 1]: g for r, g in exp.items()}
        assert dashas()._read_karaka_roles(d, CHART, ay) == {g: ABBR[r - 1] for r, g in exp.items()}
    finally:
        d.close()


# ── 2. decoys the pins must exclude ──────────────────────────────────────────────────────────────────────────────
def _decoys(template: dict, ay: str) -> "list[dict]":
    """Rows that match all but ONE pin; each carries a poisoned value that would corrupt or break a read that
    ignored the pin (a different graha, a rank that breaks the permutation, a NULL)."""
    # (an older build_id, so a decoy never collides with the real row on the production unique indexes)
    old = {"build_id": BUILD_OLD}
    return [
        # wrong category, right subject/key/formula
        mk_row(template, fact_category="karaka_web_per_varga", fact_subject="ATMAKARAKA", fact_key="assigned_graha",
               fact_value_text="Ketu", **old),
        mk_row(template, fact_category="karakamsa_position", fact_subject="ATMAKARAKA", fact_key="karaka_rank",
               fact_value_text=None, fact_value_num=99, **old),
        # wrong key (the real writer emits these for every subject; a read without the key pin would treat any
        # of them as a karaka_rank row)
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="sign", fact_value_text="Pisces", fact_value_num=None, **old),
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="karaka_school", fact_value_text="x", fact_value_num=None, **old),
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="degree_in_sign", fact_value_text=None, fact_value_num=1.5, **old),
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="house_d1", fact_value_text=None, fact_value_num=3, **old),
        # wrong school / NULL formula_id
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="assigned_graha", formula_id="some_third_school",
               fact_value_text="Ketu", **old),
        mk_row(template, fact_subject="ATMAKARAKA", fact_key="karaka_rank", formula_id=None,
               fact_value_text=None, fact_value_num=42, **old),
        # other chart / other ayanamsha, complete and conflicting
        *writer_rows(OTHER_CHART, ay, BUILD_NEW, shift=3.3),
        *writer_rows(CHART, "not_a_canonical_ayanamsha", BUILD_NEW, shift=5.5),
    ]


@pytest.mark.parametrize("plan", list(PLANS))
def test_decoys_with_wrong_pin_are_ignored_by_both_readers(conn, plan):
    per_ay = seed_five(conn)
    template = next(r for r in per_ay[AYANAMSHAS[0]] if r["fact_key"] == "assigned_graha" and r["formula_id"] == KN_RAO)
    seed(conn, _decoys(template, AYANAMSHAS[0]), how="shuffle2")
    set_plan(conn, plan)
    for ay, rows in per_ay.items():
        exp = kn_rao_expected(rows)
        assert vargas()._read_jaimini_karakas(conn, CHART, ay) == {ABBR[r - 1]: g for r, g in exp.items()}
        assert dashas()._read_karaka_roles(conn, CHART, ay) == {g: ABBR[r - 1] for r, g in exp.items()}
    # the other chart is read as ITS OWN assignment, never the first chart's
    other = {ay: kn_rao_expected(writer_rows(OTHER_CHART, ay, BUILD_NEW, shift=3.3)) for ay in AYANAMSHAS[:1]}
    for ay, exp in other.items():
        assert vargas()._read_jaimini_karakas(conn, OTHER_CHART, ay) == {ABBR[r - 1]: g for r, g in exp.items()}


# ── 3. refusals (never a default): both writers, real SQL ────────────────────────────────────────────────────────
def _both():
    return [("ga_vargas", vargas()._read_jaimini_karakas), ("ga_dashas", dashas()._read_karaka_roles)]


def _mutate_and_read(conn, mutate, match, expect_in=("ga_vargas", "ga_dashas")):
    ay = AYANAMSHAS[0]
    rows = mutate(writer_rows(CHART, ay, BUILD_NEW))
    seed(conn, rows, how="shuffle1")
    for who, fn in _both():
        if who not in expect_in:
            continue
        with pytest.raises(vargas().KarakaDependencyMissing, match=match) as ei:
            fn(conn, CHART, ay)
        assert f"[{who}]" in str(ei.value)
    # a refusal is a Python-side exception: the connection must still be healthy (not an aborted transaction)
    import psycopg.pq
    assert conn.info.transaction_status != psycopg.pq.TransactionStatus.INERROR
    conn.execute("SELECT 1")
    conn.execute("TRUNCATE chart_facts")
    conn.commit()


def test_zero_rows_raises(conn):
    seed(conn, writer_rows(OTHER_CHART, AYANAMSHAS[0], BUILD_NEW))  # rows exist, but not for this chart
    for who, fn in _both():
        with pytest.raises(vargas().KarakaDependencyMissing, match="ga_sensitive dependency missing") as ei:
            fn(conn, CHART, AYANAMSHAS[0])
        assert f"[{who}]" in str(ei.value) and "does not recompute karakas" in str(ei.value)


def test_zero_rows_for_this_ayanamsha_raises_even_when_others_are_built(conn):
    seed(conn, writer_rows(CHART, AYANAMSHAS[0], BUILD_NEW))
    for _who, fn in _both():
        with pytest.raises(vargas().KarakaDependencyMissing, match="dependency missing"):
            fn(conn, CHART, AYANAMSHAS[1])


def test_duplicate_assigned_graha_row_raises(conn):
    def mutate(rows):
        victim = next(r for r in rows if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha"
                      and r["fact_subject"] == "MATRIKARAKA")
        return rows + [mk_row(victim, fact_id="dup00000000000a1", build_id=BUILD_OLD)]
    _mutate_and_read(conn, mutate, "assigned_graha for subject 'MATRIKARAKA' is duplicated")


def test_duplicate_rank_row_raises(conn):
    def mutate(rows):
        victim = next(r for r in rows if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank"
                      and r["fact_subject"] == "DARAKARAKA")
        return rows + [mk_row(victim, fact_id="dup00000000000a2", build_id=BUILD_OLD)]
    _mutate_and_read(conn, mutate, "karaka_rank for subject 'DARAKARAKA' is duplicated")


def test_rank_gap_raises_non_permutation(conn):
    def mutate(rows):  # ranks 1..7 and 9: a gap, still eight distinct integers
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank" and int(r["fact_value_num"]) == 8:
                r["fact_value_num"] = 9.0
        return rows
    _mutate_and_read(conn, mutate, r"ranks \[1, 2, 3, 4, 5, 6, 7, 9\] are not a 1\.\.8 permutation")


def test_duplicate_rank_value_across_subjects_raises_non_permutation(conn):
    def mutate(rows):  # two subjects both rank 3
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank" and int(r["fact_value_num"]) == 4:
                r["fact_value_num"] = 3.0
        return rows
    _mutate_and_read(conn, mutate, "not a 1..8 permutation")


def test_rank_zero_based_raises_non_permutation(conn):
    def mutate(rows):  # 0..7 (an off-by-one writer)
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank":
                r["fact_value_num"] = float(int(r["fact_value_num"]) - 1)
        return rows
    _mutate_and_read(conn, mutate, "not a 1..8 permutation")


def test_one_graha_holding_two_roles_raises(conn):
    def mutate(rows):  # ATMAKARAKA's graha copied onto AMATYAKARAKA: ranks are still a clean permutation
        graha = next(r["fact_value_text"] for r in rows if r["formula_id"] == KN_RAO
                     and r["fact_key"] == "assigned_graha" and r["fact_subject"] == "ATMAKARAKA")
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha" and r["fact_subject"] == "AMATYAKARAKA":
                r["fact_value_text"] = graha
        return rows
    _mutate_and_read(conn, mutate, "are not 8 distinct grahas")


def test_assigned_graha_without_its_rank_raises(conn):
    def mutate(rows):
        return [r for r in rows if not (r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank"
                                        and r["fact_subject"] == "GNATIKARAKA")]
    _mutate_and_read(conn, mutate, "assigned_graha subjects .* != karaka_rank subjects")


def test_null_graha_text_raises(conn):
    def mutate(rows):
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha" and r["fact_subject"] == "PUTRAKARAKA":
                r["fact_value_text"] = None
        return rows
    _mutate_and_read(conn, mutate, "assigned_graha for subject 'PUTRAKARAKA' is NULL")


def test_null_rank_raises(conn):
    def mutate(rows):
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "karaka_rank" and r["fact_subject"] == "PITRIKARAKA":
                r["fact_value_num"] = None
        return rows
    _mutate_and_read(conn, mutate, "karaka_rank for subject 'PITRIKARAKA' is NULL")


def test_seven_rows_only_of_the_eight_scheme_raises(conn):
    def mutate(rows):  # a half-built kn_rao school (7 subjects)
        return [r for r in rows if not (r["formula_id"] == KN_RAO and r["fact_subject"] == "DARAKARAKA")]
    _mutate_and_read(conn, mutate, "not a 1..8 permutation")


def test_pre_2878_shaped_rows_are_refused_by_both_readers(conn):
    """A stale pre-#2878 ga_sensitive generation (STRIKARAKA stored as the 8th SUBJECT, no PITRIKARAKA; ranks still a
    clean 1..8 permutation of eight distinct grahas) is REFUSED, not read. The ga_sensitive -> ga_vargas/ga_dashas
    ordering exists only in the held migration 1226, so the reader guards the generation itself."""
    relabel = {"PITRIKARAKA": "PUTRAKARAKA", "PUTRAKARAKA": "GNATIKARAKA", "GNATIKARAKA": "DARAKARAKA",
               "DARAKARAKA": "STRIKARAKA"}

    def mutate(rows):
        out = []
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "strikaraka_alias":
                continue  # the old writer had no alias row
            if r["formula_id"] == KN_RAO and r["fact_subject"] in relabel:
                r = mk_row(r, fact_subject=relabel[r["fact_subject"]])
            out.append(r)
        return out
    _mutate_and_read(conn, mutate, r"STRIKARAKA.*PITRIKARAKA|PITRIKARAKA.*STRIKARAKA")


def test_dashas_refuses_a_graha_outside_its_universe(conn):
    """ga_dashas' lord universe is the eight karaka grahas (no Ketu): a stored Ketu role is refused there."""
    def mutate(rows):
        for r in rows:
            if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha" and r["fact_subject"] == "DARAKARAKA":
                r["fact_value_text"] = "Ketu"
        return rows
    _mutate_and_read(conn, mutate, "distinct grahas drawn from", expect_in=("ga_dashas",))


# ── 4. TWO build generations of the karaka rows ──────────────────────────────────────────────────────────────────
def two_generations(ay: str = AYANAMSHAS[0]) -> "list[dict]":
    old = reid(writer_rows(CHART, ay, BUILD_OLD, shift=7.0), "gen-old")
    new = writer_rows(CHART, ay, BUILD_NEW)
    assert kn_rao_expected(old) != kn_rao_expected(new), "the older generation must carry different assignments"
    return old + new


@pytest.mark.parametrize("plan", list(PLANS))
@pytest.mark.parametrize("how", ORDERS)
def test_two_generations_are_refused_identically_under_every_insertion_order_and_plan(conn, how, plan):
    seed(conn, two_generations(), how)
    set_plan(conn, plan)
    msgs = set()
    for who, fn in _both():
        with pytest.raises(vargas().KarakaDependencyMissing) as ei:
            fn(conn, CHART, AYANAMSHAS[0])
        msgs.add(str(ei.value).replace(f"[{who}]", "[X]"))
    # the total ORDER BY fixes WHICH duplicate is reported first: the smallest (subject, key) -- 'AMATYAKARAKA' <
    # 'ATMAKARAKA', 'assigned_graha' < 'karaka_rank' -- whatever the physical row order.
    assert len(msgs) == 1
    assert "assigned_graha for subject 'AMATYAKARAKA' is duplicated" in next(iter(msgs))


def test_a_stale_partial_older_generation_alongside_a_complete_one_is_refused(conn):
    rows = writer_rows(CHART, AYANAMSHAS[0], BUILD_NEW)
    stale = reid([r for r in writer_rows(CHART, AYANAMSHAS[0], BUILD_OLD, shift=7.0)
                  if r["formula_id"] == KN_RAO and r["fact_key"] == "assigned_graha"
                  and r["fact_subject"] in ("ATMAKARAKA", "DARAKARAKA", "GNATIKARAKA")], "stale")
    seed(conn, rows + stale, "shuffle3")
    for _who, fn in _both():
        with pytest.raises(vargas().KarakaDependencyMissing, match="duplicated"):
            fn(conn, CHART, AYANAMSHAS[0])


def test_the_other_ayanamsha_is_unaffected_by_a_two_generation_neighbour(conn):
    per_ay = seed_five(conn)
    seed(conn, reid(writer_rows(CHART, AYANAMSHAS[0], BUILD_OLD, shift=7.0), "gen-old"))
    with pytest.raises(vargas().KarakaDependencyMissing):
        vargas()._read_jaimini_karakas(conn, CHART, AYANAMSHAS[0])
    exp = kn_rao_expected(per_ay[AYANAMSHAS[1]])
    assert vargas()._read_jaimini_karakas(conn, CHART, AYANAMSHAS[1]) == {ABBR[r - 1]: g for r, g in exp.items()}


_FETCH_SQL_ORACLE = (
    "SELECT fact_subject, fact_key, fact_value_text, fact_value_num, fact_id FROM chart_facts "
    "WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='karaka_chara_position' "
    "AND fact_key IN ('assigned_graha','karaka_rank') AND formula_id=%s "
    "ORDER BY fact_subject, fact_key, fact_id"
)


@pytest.mark.parametrize("plan", list(PLANS))
@pytest.mark.parametrize("higher_fact_id_inserted_first", [True, False])
def test_fetch_order_is_the_total_order_including_the_fact_id_tie_break(conn, plan, higher_fact_id_inserted_first):
    """Rows tied on (fact_subject, fact_key) -- two generations -- must come back in ascending fact_id, NOT in
    physical insertion order and NOT in build_id/index order. Arranged so the two wrong orders agree with each other
    and disagree with the right one: the row with the higher fact_id carries the LOWER build_id and (in the first
    case) is inserted first; the second case is the mirror image."""
    ay = AYANAMSHAS[0]
    a = writer_rows(CHART, ay, BUILD_NEW)                       # lower fact_ids come from the writer's own hash
    b = reid(writer_rows(CHART, ay, BUILD_OLD, shift=7.0), "gen-old")
    # make every b fact_id sort strictly above its a twin, and every a fact_id above... decided per pair below
    by_key_a = {(r["fact_subject"], r["fact_key"], r["formula_id"]): r for r in a}
    pairs = []
    for r in b:
        twin = by_key_a[(r["fact_subject"], r["fact_key"], r["formula_id"])]
        lo, hi = sorted([twin["fact_id"], r["fact_id"]])
        pairs.append((twin, r, lo, hi))
    hi_first, lo_first = [], []
    for twin, r, lo, hi in pairs:
        # hi-id row gets the lower build_id; lo-id row the higher build_id
        t = {**twin, "fact_id": lo, "build_id": BUILD_NEW}
        o = {**r, "fact_id": hi, "build_id": BUILD_OLD}
        hi_first += [o, t]
        lo_first += [t, o]
    rows = hi_first if higher_fact_id_inserted_first else lo_first
    with conn.cursor() as cur:  # insert in EXACTLY this physical order
        cur.executemany(INSERT_SQL, [tuple(r[c] for c in INSERT_COLS) for r in rows])
    conn.commit()
    set_plan(conn, plan)
    from ga_writers._karaka_roles import fetch_kn_rao_karaka_rows
    got = fetch_kn_rao_karaka_rows(conn, CHART, ay)
    oracle = conn.execute(_FETCH_SQL_ORACLE, (CHART, ay, KN_RAO)).fetchall()
    assert [tuple(r[:4]) for r in oracle] == [tuple(r) for r in got]
    # and the oracle itself really is sorted by (subject, key, fact_id) in Python
    keyed = [(r[0], r[1], r[4]) for r in oracle]
    assert keyed == sorted(keyed)
    assert len(got) == 8 * 2 * 2  # 8 subjects x 2 keys x 2 generations


_CHILD = r"""
import os, sys
sys.path.insert(0, {sidecar!r})
import psycopg
from ga_writers import ga_vargas_writer as v, ga_dashas_writer as d
with psycopg.connect(os.environ["KARAKA_READER_TEST_DATABASE_URL"], connect_timeout=5) as c:
    assert c.execute("SELECT current_database()").fetchone()[0] == {db!r}
    out = []
    for fn in (v._read_jaimini_karakas, d._read_karaka_roles):
        try:
            out.append(("ok", repr(sorted(fn(c, {chart!r}, {ay!r}).items()))))
        except Exception as exc:
            out.append((type(exc).__name__, str(exc)))
print(repr(out))
"""


@pytest.mark.parametrize("scenario", ["two_generations", "clean"])
def test_result_is_identical_across_pythonhashseeds(conn, scenario):
    ay = AYANAMSHAS[0]
    seed(conn, two_generations(ay) if scenario == "two_generations" else writer_rows(CHART, ay, BUILD_NEW), "shuffle2")
    code = _CHILD.format(sidecar=str(SIDECAR), db=EXPECTED_DB_NAME, chart=CHART, ay=ay)
    outs = {}
    for hs in ("0", "1", "42", "31337", "random"):
        env = {**os.environ, "PYTHONHASHSEED": hs}
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=str(SIDECAR),
                           timeout=120)
        assert r.returncode == 0, r.stderr[-1500:]
        outs[hs] = r.stdout.strip().splitlines()[-1]
    assert len(set(outs.values())) == 1, outs
    only = next(iter(outs.values()))
    assert ("KarakaDependencyMissing" in only) == (scenario == "two_generations"), only


# ── 5. ga_dashas pipeline entry (cache + lazy raise) on a real connection ───────────────────────────────────────
def test_dashas_activate_then_lookup_on_a_real_connection(conn):
    per_ay = seed_five(conn)
    m = dashas()
    ay = AYANAMSHAS[3]
    m._activate_karaka_roles(CHART, ay, conn)
    exp = {g: ABBR[r - 1] for r, g in kn_rao_expected(per_ay[ay]).items()}
    for graha, role in exp.items():
        assert m._get_karaka_role(CHART, ay, graha) == role
    assert m._get_karaka_role(CHART, ay, "Ketu") is None            # no 8-scheme role for Ketu
    assert m._get_karaka_role(CHART, ay, "Mangala") is None         # a yogini lord: needs no read at all
    lord, parent = "Moon", "Sun"
    assert m._get_karakas_active(CHART, ay, lord, parent) == [
        f"{g}:{exp[g]}" for g in m._KARAKAS_ACTIVE_GRAHA_ORDER if g in (lord, parent)]


def test_dashas_activate_records_the_refusal_and_raises_only_when_a_role_is_needed(conn):
    m = dashas()
    ay = AYANAMSHAS[0]
    m._activate_karaka_roles(OTHER_CHART, ay, conn)               # nothing built for this chart
    assert m._get_karaka_role(OTHER_CHART, ay, "Mangala") is None  # sign/yogini lord: still builds
    with pytest.raises(m.KarakaDependencyMissing, match="ga_sensitive dependency missing"):
        m._get_karaka_role(OTHER_CHART, ay, "Sun")
    # a real rebuild between two builds in one process is picked up (always reloads)
    seed(conn, writer_rows(OTHER_CHART, ay, BUILD_NEW))
    m._activate_karaka_roles(OTHER_CHART, ay, conn)
    assert m._get_karaka_role(OTHER_CHART, ay, "Sun") in ABBR


# ── 6. #2883: ga_structural's karaka-web read (its own SQL, ORDER BY fact_subject, fact_id) ─────────────────────
WEB_ROWS = [("ATMAKARAKA", "Sun"), ("AMATYAKARAKA", "Moon"), ("BHRATRIKARAKA", "Mars"),
            ("MATRIKARAKA", "Jupiter"), ("PITRIKARAKA", "Saturn")]
WEB_STATE = {  # the golden fixture of tests/test_ga8_writer.py::TestKarakaWebOrderIndependence
    "Sun": {"sign": "Aries", "house": 1}, "Jupiter": {"sign": "Aries", "house": 1},
    "Moon": {"sign": "Leo", "house": 5}, "Mars": {"sign": "Pisces", "house": 12},
    "Saturn": {"sign": "Gemini", "house": 3},
}
WEB_GOLDEN = [  # (fact_subject, fact_key), in the writer's canonical emission order
    ("D9_SUN", "conjunction_JUP"), ("D9_MAR", "aspect_SAT"), ("D9_JUP", "conjunction_SUN"),
    ("D9_JUP", "aspect_MOON"), ("D9_SAT", "aspect_MOON"), ("D9_SAT", "aspect_MAR"),
]


def structural():
    import ga_writers.ga_structural_writer as m
    return m


def run_web(c, chart=CHART, ay=AYANAMSHAS[0]):
    return structural()._build_karaka_web_rows(c, WEB_STATE, {}, "D9", chart, BUILD_NEW, ay,
                                               "2026-10-02T00:00:00+00:00", "karaka-reader-test/1")


def web_assignment_rows(template: dict, pairs, *, ay=AYANAMSHAS[0], build=BUILD_NEW, salt="") -> "list[dict]":
    return [mk_row(template, ayanamsha_id=ay, build_id=build, fact_subject=role, fact_key="assigned_graha",
                   fact_value_text=planet, fact_value_num=None, formula_id=KN_RAO,
                   fact_id=hashlib.sha256(f"{role}|{ay}|{build}|{salt}".encode()).hexdigest()[:16])
            for role, planet in pairs]


def _template():
    return next(r for r in writer_rows(CHART, AYANAMSHAS[0], BUILD_NEW)
                if r["fact_key"] == "assigned_graha" and r["formula_id"] == KN_RAO)


def _web_keys(rows):
    return [(r["fact_subject"], r["fact_key"]) for r in rows]


@pytest.mark.parametrize("plan", list(PLANS))
@pytest.mark.parametrize("how", ORDERS)
def test_karaka_web_real_sql_golden_rows_independent_of_insertion_order(conn, how, plan):
    seed(conn, web_assignment_rows(_template(), WEB_ROWS), how)
    set_plan(conn, plan)
    assert _web_keys(run_web(conn)) == WEB_GOLDEN


def test_karaka_web_ignores_decoys_on_real_sql(conn):
    t = _template()
    decoys = (
        web_assignment_rows(t, [("ATMAKARAKA", "Venus"), ("DARAKARAKA", "Mercury")], build=BUILD_OLD, ay=AYANAMSHAS[1])
        + [mk_row(t, fact_subject="ATMAKARAKA", fact_key="assigned_graha", formula_id=PARASHARI, fact_value_text="Venus")]
        + [mk_row(t, fact_subject="ATMAKARAKA", fact_key="karaka_rank", fact_value_text=None, fact_value_num=1)]
        + [mk_row(t, fact_category="karaka_per_varga", fact_subject="ATMAKARAKA", fact_key="assigned_graha",
                  fact_value_text="Venus")]
        + [mk_row(t, fact_subject="ATMAKARAKA", fact_key="assigned_graha", formula_id=None, fact_value_text="Venus")]
        + [mk_row(t, chart_id=OTHER_CHART, fact_subject="ATMAKARAKA", fact_key="assigned_graha", fact_value_text="Venus")]
    )
    seed(conn, web_assignment_rows(t, WEB_ROWS) + decoys, "shuffle2")
    assert _web_keys(run_web(conn)) == WEB_GOLDEN


class _RecordingConn:
    """Wraps a psycopg connection and records what each cursor's fetchall() returned, in the order returned."""

    def __init__(self, inner):
        self._inner = inner
        self.fetched: list[list] = []

    def cursor(self, **kw):
        outer, inner = self, self._inner.cursor(**kw)

        class _Cur:
            def __enter__(self_inner):
                inner.__enter__()
                return self_inner

            def __exit__(self_inner, *a):
                return inner.__exit__(*a)

            def execute(self_inner, *a, **k):
                return inner.execute(*a, **k)

            def fetchall(self_inner):
                rows = inner.fetchall()
                outer.fetched.append(list(rows))
                return rows

        return _Cur()


@pytest.mark.parametrize("plan", list(PLANS))
@pytest.mark.parametrize("higher_fact_id_inserted_first", [True, False])
def test_karaka_web_read_order_is_subject_then_fact_id(conn, plan, higher_fact_id_inserted_first):
    """#2883's ORDER BY was only string-asserted. Real SQL: the rows reach Python ordered by (fact_subject, fact_id),
    tie-broken on fact_id, not on insertion or build_id order (same arrangement as the shared-reader test)."""
    t = _template()
    gen_a = web_assignment_rows(t, WEB_ROWS, build=BUILD_NEW, salt="a")
    gen_b = web_assignment_rows(t, [(r, "Mercury") for r, _ in WEB_ROWS], build=BUILD_OLD, salt="b")
    rows = []
    for a, b in zip(gen_a, gen_b):
        lo, hi = sorted([a["fact_id"], b["fact_id"]])
        lo_row = {**a, "fact_id": lo, "build_id": BUILD_NEW}
        hi_row = {**b, "fact_id": hi, "build_id": BUILD_OLD}
        rows += [hi_row, lo_row] if higher_fact_id_inserted_first else [lo_row, hi_row]
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, [tuple(r[c] for c in INSERT_COLS) for r in rows])
    conn.commit()
    set_plan(conn, plan)
    rec = _RecordingConn(conn)
    out = structural()._build_karaka_web_rows(rec, WEB_STATE, {}, "D9", CHART, BUILD_NEW, AYANAMSHAS[0],
                                              "2026-10-02T00:00:00+00:00", "karaka-reader-test/1")
    assert len(rec.fetched) == 1 and len(rec.fetched[0]) == 10
    oracle = conn.execute(
        "SELECT fact_subject, fact_value_text FROM chart_facts WHERE chart_id=%s AND ayanamsha_id=%s "
        "AND fact_category='karaka_chara_position' AND fact_key='assigned_graha' AND formula_id=%s "
        "ORDER BY fact_subject, fact_id", (CHART, AYANAMSHAS[0], KN_RAO)).fetchall()
    assert [(r[0], r[1]) for r in rec.fetched[0]] == [tuple(r) for r in oracle]
    # the build's output stays a pure function of the SET of stored rows
    assert out == structural()._build_karaka_web_rows(
        _RecordingConn(conn), WEB_STATE, {}, "D9", CHART, BUILD_NEW, AYANAMSHAS[0],
        "2026-10-02T00:00:00+00:00", "karaka-reader-test/1")


def test_karaka_web_two_generations_is_deterministic_across_insertion_orders(conn):
    t = _template()
    gen_new = web_assignment_rows(t, WEB_ROWS, build=BUILD_NEW, salt="n")
    gen_old = web_assignment_rows(t, [("ATMAKARAKA", "Mercury"), ("AMATYAKARAKA", "Venus")], build=BUILD_OLD, salt="o")
    results = set()
    for how in ORDERS:
        conn.execute("TRUNCATE chart_facts")
        seed(conn, gen_new + gen_old, how)
        results.add(tuple(_web_keys(run_web(conn))))
    assert len(results) == 1
