"""
test_node_series_readers_ignore_mean_rows.py — NODE-SERIES step-2 PROOF (SS release condition), one parametrised file.

THE CLAIM. Today `ephemeris_daily` holds only TRUE Rahu/Ketu rows (node_mode = 'true'; the seven other bodies carry
node_mode NULL). Step 2 adds a MEAN Rahu/Ketu row set BESIDE them (same date, same ayanamsha_id, node_mode = 'mean').
Every reader in the T1 table (REVIEW_OURS_READERS_STEP0_v1_0.md) must then return the SAME result as on the TRUE-only
table, OR refuse loudly (NodeSeriesError / an explicit error). Nothing may silently read both, last-row-wins, or merge.

THE METHOD. A disposable local PostgreSQL (initdb in a temp dir, unix socket only, no TCP, no network, no production
credential) holds two databases built from the LIVE DDL shape of `public.ephemeris_daily` (read as suvarna_reader,
2026-10-02, snapshot below):

    db_true          TRUE rows only, the CURRENT key  UNIQUE (date, body, ayanamsha_id)  + the step-0 index (1227)
    db_mixed         the same TRUE rows + a synthetic MEAN Rahu/Ketu set, the post-1250 key (the 3-column constraint
                     dropped; UNIQUE (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT only)
    db_true_missing  db_mixed with the TRUE Rahu/Ketu rows REMOVED (MEAN present): the state a reader must not "repair"
                     by silently reading the MEAN series. A reader that REQUIRES the node rows must refuse loudly here.

Each registered reader is run against both and the results compared (volatile timestamps scrubbed). The synthetic
MEAN set is plausible: mean Rahu retrogrades at a constant 0.0529 deg/day, mean Ketu = mean Rahu + 180 with the
CORRECT shared speed and flag (F-L0-08), the stored TRUE Ketu rows keep today's inverted speed/flag, and mean and
true longitudes differ by up to ~1.5 degrees so a read of the wrong series (or of both) shows.

THE REGISTRY (`READERS`). One row per reader id of the T1 table: ('same_result' | 'loud_refusal' | 'known_unpinned_legacy'
| 'not_driven', callable, reason). `not_driven` carries an explicit reason; `test_every_t1_reader_is_driven_or_explained`
fails when a T1 id is missing or has no reason. The dead unpinned copies in `brahmagyan/l0_ephemeris.py` are registered
as `known_unpinned_legacy` and must FAIL the same-result check (xfail strict): that is the proof this harness can
detect the defect. Each later reader PR of the NODE-SERIES stack flips its `not_driven` rows to driven.

Requires PostgreSQL >= 15 binaries (NULLS NOT DISTINCT). Found via NODE_SERIES_PG_BIN, Homebrew, /usr/lib/postgresql,
or PATH. EARNED IN CI (SS ruling 3): when GITHUB_ACTIONS=true (or NODE_SERIES_REQUIRE_PG=1) this module NEVER skips: a
missing psycopg2, a root runner or the absence of PostgreSQL >= 15 binaries FAILS the run. On a developer machine
without PostgreSQL it still SKIPS. The sidecar CI job (ci.yml `Governance Gates`) has no `services:` Postgres, so the
proof runs on the runner image's preinstalled PostgreSQL binaries through a disposable initdb cluster (unix socket only).
A pytest terminal-summary line ("NODE-SERIES PROOF: N passed ...") is printed even under `-q` so the CI job log carries
the pass count.
"""
from __future__ import annotations

import contextlib
import glob
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable

import pytest

# EARNED IN CI: under GitHub Actions (or NODE_SERIES_REQUIRE_PG=1) every skip route of this module becomes a failure.
MUST_RUN = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("NODE_SERIES_REQUIRE_PG") == "1"

if MUST_RUN:
    import psycopg2          # an ImportError is a collection ERROR, never a skip
else:
    psycopg2 = pytest.importorskip("psycopg2")

from brahmagyan import ephemeris_routes as routes  # noqa: E402
from brahmagyan import l0_ephemeris as legacy  # noqa: E402
from brahmagyan import l0_ephemeris_queries as pinned  # noqa: E402
from services.w2g.node_series import NodeSeriesError  # noqa: E402

# ------------------------------------------------------------------------------------------- live DDL snapshot
# `public.ephemeris_daily`, read as suvarna_reader 2026-10-02 (information_schema.columns, pg_constraint, pg_indexes).
LIVE_DDL = """
CREATE TABLE public.ephemeris_daily (
    id                 uuid        NOT NULL DEFAULT gen_random_uuid(),
    date               date        NOT NULL,
    body               text        NOT NULL,
    ayanamsha_id       text        NOT NULL DEFAULT 'tropical',
    tropical_longitude numeric     NOT NULL,
    latitude           numeric     NOT NULL DEFAULT 0.0,
    speed_dps          numeric     NOT NULL DEFAULT 0.0,
    is_retrograde      boolean     NOT NULL DEFAULT false,
    sign_number        smallint,
    degree_in_sign     numeric,
    nakshatra_number   smallint,
    source_citation    text        NOT NULL DEFAULT 'pyswisseph DE441 + Swiss Ephemeris',
    computed_at        timestamptz NOT NULL DEFAULT now(),
    node_mode          text,
    epoch_convention   text,
    CONSTRAINT ephemeris_daily_pkey PRIMARY KEY (id),
    CONSTRAINT ephemeris_daily_node_mode_check CHECK (node_mode IS NULL OR node_mode = ANY (ARRAY['true'::text, 'mean'::text]))
);
CREATE INDEX idx_ephemeris_date ON public.ephemeris_daily USING btree (date);
CREATE INDEX idx_ephemeris_body ON public.ephemeris_daily USING btree (body);
CREATE INDEX idx_ephemeris_date_body ON public.ephemeris_daily USING btree (date, body);
CREATE INDEX idx_ephemeris_ayanamsha ON public.ephemeris_daily USING btree (ayanamsha_id);
"""
OLD_KEY = "ALTER TABLE public.ephemeris_daily ADD CONSTRAINT ephemeris_daily_date_body_ayanamsha_id_key UNIQUE (date, body, ayanamsha_id);"
NEW_KEY = ("CREATE UNIQUE INDEX ephemeris_daily_date_body_ayanamsha_id_node_mode_key ON public.ephemeris_daily "
           "(date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT;")

START = date(2026, 7, 1)
N_DAYS = 41                                                  # 2026-07-01 .. 2026-08-10
DAYS = [START + timedelta(days=i) for i in range(N_DAYS)]
BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
NODES = ("Rahu", "Ketu")
CITATION = "pyswisseph + Swiss Ephemeris .se1"
EXTRA_DAYS = [(date(1984, 2, 5), "Sun", 315.87, 1.0), (date(2050, 1, 1), "Saturn", 345.0, 0.05)]   # check_volume spot checks


# ------------------------------------------------------------------------------------------- synthetic series
def _ang(x: float) -> float:
    return round(x % 360.0, 6)


def _row(day: date, body: str, lon: float, speed: float, retro: bool, node_mode: str | None) -> tuple:
    lon = _ang(lon)
    return (day, body, "tropical", lon, 0.0, round(speed, 6), retro, int(lon // 30) + 1, round(lon % 30.0, 6),
            int(lon / (360.0 / 27.0)) + 1, CITATION, node_mode, "noon_ut")


def _rows_true() -> list[tuple]:
    rows: list[tuple] = []
    sat_lon = 20.0
    for i, d in enumerate(DAYS):
        sat_speed = 0.02 * (10 - i) / 10.0                    # direct, stations at i = 10, then retrograde
        sat_lon += sat_speed
        for b in BODIES[:7]:
            if b == "Sun":
                lon, sp = 98.0 + 0.9856 * i, 0.9856
            elif b == "Moon":
                lon, sp = 50.0 + 13.176 * i, 13.176
            elif b == "Mars":
                lon, sp = 150.0 + 0.52 * i, 0.52
            elif b == "Mercury":
                lon, sp = 120.0 + 1.1 * i, 1.1
            elif b == "Jupiter":
                lon, sp = 90.0 + 0.08 * i, 0.08
            elif b == "Venus":
                lon, sp = 140.0 + 1.2 * i, 1.2
            else:
                lon, sp = sat_lon, sat_speed
            rows.append(_row(d, b, lon, sp, sp < 0, None))
        mean_lon = 330.0 - 0.0529 * i
        true_rahu = mean_lon + 1.5 * math.sin(i / 3.0)          # the TRUE node oscillates about the mean
        true_sp = -0.0529 + 0.03 * math.cos(i / 3.0) / 3.0
        rows.append(_row(d, "Rahu", true_rahu, true_sp, True, "true"))
        # the stored TRUE Ketu rows today: Rahu + 180 with the speed and flag INVERTED (F-L0-08)
        rows.append(_row(d, "Ketu", true_rahu + 180.0, -true_sp, False, "true"))
    for d, b, lon, sp in EXTRA_DAYS:
        rows.append(_row(d, b, lon, sp, False, None))
    return rows


def _rows_mean() -> list[tuple]:
    rows: list[tuple] = []
    for i, d in enumerate(DAYS):
        mean_lon = 330.0 - 0.0529 * i
        rows.append(_row(d, "Rahu", mean_lon, -0.0529, True, "mean"))
        rows.append(_row(d, "Ketu", mean_lon + 180.0, -0.0529, True, "mean"))   # Ketu = Rahu + 180, CORRECT shared speed/flag
    return rows


INSERT = ("INSERT INTO public.ephemeris_daily (date, body, ayanamsha_id, tropical_longitude, latitude, speed_dps, "
          "is_retrograde, sign_number, degree_in_sign, nakshatra_number, source_citation, node_mode, epoch_convention) "
          "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")


# ------------------------------------------------------------------------------------------- disposable PostgreSQL
def _pg_major(bindir: str) -> int:
    try:
        out = subprocess.run([os.path.join(bindir, "postgres"), "--version"], capture_output=True, text=True, timeout=20).stdout
        m = re.search(r"\(PostgreSQL\)\s+(\d+)", out)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def _find_pg_bin() -> str | None:
    cands: list[str] = []
    if os.environ.get("NODE_SERIES_PG_BIN"):
        cands.append(os.environ["NODE_SERIES_PG_BIN"])
    cands += sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)
    cands += sorted(glob.glob("/usr/local/opt/postgresql@*/bin"), reverse=True)
    cands += sorted(glob.glob("/usr/lib/postgresql/*/bin"), key=lambda p: int(re.search(r"/(\d+)/bin$", p).group(1)), reverse=True)
    w = shutil.which("initdb")
    if w:
        cands.append(os.path.dirname(w))
    for d in cands:
        if all(os.path.isfile(os.path.join(d, n)) for n in ("initdb", "pg_ctl", "postgres")) and _pg_major(d) >= 15:
            return d
    return None


class Cluster:
    def __init__(self, bindir: str):
        base = os.environ.get("NODE_SERIES_PG_TMP") or "/tmp"          # short path: unix sockets are limited to ~100 bytes
        self.root = tempfile.mkdtemp(prefix="nsp", dir=base)
        self.bindir = bindir
        data = os.path.join(self.root, "data")
        run = lambda *a: subprocess.run([os.path.join(bindir, a[0]), *a[1:]], capture_output=True, text=True, timeout=120)  # noqa: E731
        r = run("initdb", "-D", data, "-A", "trust", "-U", "postgres", "--no-sync", "-E", "UTF8", "--locale=C")
        assert r.returncode == 0, r.stderr
        r = run("pg_ctl", "-D", data, "-o",
                f"-c listen_addresses='' -c unix_socket_directories={self.root} -c fsync=off -c synchronous_commit=off "
                f"-c full_page_writes=off -c max_connections=30", "-w", "-t", "90", "-l", os.path.join(self.root, "log"), "start")
        assert r.returncode == 0, r.stdout + r.stderr
        self._data = data

    def connect(self, db: str):
        c = psycopg2.connect(host=self.root, dbname=db, user="postgres")
        c.autocommit = True
        return c

    def dsn(self, db: str) -> str:
        return f"postgresql://postgres@/{db}?host={self.root}"

    def stop(self):
        subprocess.run([os.path.join(self.bindir, "pg_ctl"), "-D", self._data, "-m", "immediate", "stop"], capture_output=True, timeout=60)
        shutil.rmtree(self.root, ignore_errors=True)


@dataclass
class Ctx:
    """What a reader driver gets: a live autocommit connection and the DSN a route would read from DATABASE_URL."""
    conn: Any            # psycopg2, autocommit (the L0 readers take a psycopg2 connection)
    dsn: str
    _pg3: Any = None

    @property
    def pg3(self):
        """A psycopg (v3) autocommit connection to the same database: the orchestrator writers use psycopg.rows."""
        if self._pg3 is None:
            import psycopg
            self._pg3 = psycopg.connect(self.dsn, autocommit=True)
        return self._pg3

    def close(self):
        if self._pg3 is not None:
            self._pg3.close()
        self.conn.close()

    @contextlib.contextmanager
    def database_url(self):
        old = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = self.dsn
        try:
            yield
        finally:
            if old is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old


@pytest.fixture(scope="module")
def cluster():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        msg = "initdb refuses to run as root"
        pytest.fail(msg) if MUST_RUN else pytest.skip(msg)
    bindir = _find_pg_bin()
    if bindir is None:
        msg = "no PostgreSQL >= 15 binaries (set NODE_SERIES_PG_BIN); the disposable-cluster proof cannot run here"
        pytest.fail(msg) if MUST_RUN else pytest.skip(msg)
    c = Cluster(bindir)
    try:
        admin = c.connect("postgres")
        for db in ("db_true", "db_mixed", "db_true_missing"):
            admin.cursor().execute(f"CREATE DATABASE {db}")
        admin.close()
        for db, mixed in (("db_true", False), ("db_mixed", True), ("db_true_missing", True)):
            conn = c.connect(db)
            cur = conn.cursor()
            cur.execute(LIVE_DDL)
            if not mixed:
                cur.execute(OLD_KEY)                                   # the CURRENT key (until migration 1250); db_mixed never has it
            cur.execute(NEW_KEY)                                       # the step-0 index (migration 1227)
            cur.executemany(INSERT, _rows_true())
            if mixed:                                                  # post-1250: only the four-column key exists
                cur.executemany(INSERT, _rows_mean())
            if db == "db_true_missing":
                cur.execute("DELETE FROM public.ephemeris_daily WHERE body IN ('Rahu', 'Ketu') AND node_mode = 'true'")
            conn.close()
        yield c
    finally:
        c.stop()


@pytest.fixture(scope="module")
def ctx_true(cluster):
    conn = cluster.connect("db_true")
    ctx = Ctx(conn, cluster.dsn("db_true"))
    yield ctx
    ctx.close()


@pytest.fixture(scope="module")
def ctx_mixed(cluster):
    conn = cluster.connect("db_mixed")
    ctx = Ctx(conn, cluster.dsn("db_mixed"))
    yield ctx
    ctx.close()


@pytest.fixture(scope="module")
def ctx_true_missing(cluster):
    conn = cluster.connect("db_true_missing")
    ctx = Ctx(conn, cluster.dsn("db_true_missing"))
    yield ctx
    ctx.close()


# ------------------------------------------------------------------------------------------- normalisation
def _jsonable(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return str(o)


def normalise(x: Any) -> Any:
    """JSON round-trip with volatile timestamps dropped, so two runs of a reader can be compared with =="""
    def scrub(v):
        if isinstance(v, dict):
            return {k: scrub(w) for k, w in v.items() if k != "computed_at"}
        if isinstance(v, (list, tuple)):
            return [scrub(w) for w in v]
        return v
    return scrub(json.loads(json.dumps(x, default=_jsonable, sort_keys=True)))


# ------------------------------------------------------------------------------------------- the registry
SAME, LOUD, LEGACY, NOT_DRIVEN = "same_result", "loud_refusal", "known_unpinned_legacy", "not_driven"
D0, D1, D2 = "2026-07-10", "2026-07-11", "2026-07-12"
W0, W1 = "2026-07-01", "2026-08-10"

# every reader id of the T1 table (REVIEW_OURS_READERS_STEP0_v1_0.md) and of Pravaha's pinned set
T1_IDS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S9", "S11", "P3", "P4", "P8", "P9", "L1-e", "T3", "S17", "L1-c",
          "S13/S14/S15/S20", "reg", "P1", "P2", "P5", "P6", "P7", "P14", "P15"]


@dataclass(frozen=True)
class Reader:
    rid: str                                   # a T1 id
    label: str
    kind: str                                  # SAME | LOUD | LEGACY | NOT_DRIVEN
    run: Callable[[Ctx], Any] | None = None
    reason: str = ""                           # required for NOT_DRIVEN and LEGACY
    # what the reader does when the TRUE node rows are absent and the MEAN ones are present: None = not asserted,
    # LOUD = it must raise (a reader that REQUIRES the node series and must never fall back to the MEAN one)
    when_true_missing: str | None = None


def _route(fn, *a, **kw):
    def run(ctx: Ctx):
        with ctx.database_url():
            return fn(*a, **kw)
    return run


def _mk(mod, call):
    return lambda ctx: call(mod, ctx.conn)


S_CALLS = {
    "S1 all bodies": lambda m, c: m.query_planet_position(D1, conn=c),
    "S1 Rahu": lambda m, c: m.query_planet_position(D1, planet="Rahu", conn=c),
    "S1 Ketu tropical": lambda m, c: m.query_planet_position(D1, planet="Ketu", ayanamsha_id="tropical", conn=c),
    "S2 Rahu window": lambda m, c: m.query_planet_transit("Rahu", W0, W1, conn=c),
    "S2 Ketu sign filter": lambda m, c: m.query_planet_transit("Ketu", W0, W1, sign_number=5, ayanamsha_id="tropical", conn=c),
    "S2 Venus window": lambda m, c: m.query_planet_transit("Venus", W0, W1, conn=c),
    "S3 aspects 1deg": lambda m, c: m.query_aspects_at_time(D1, orb_degrees=1.0, conn=c),
    "S3 aspects 10deg tropical": lambda m, c: m.query_aspects_at_time(D1, orb_degrees=10.0, ayanamsha_id="tropical", conn=c),
    "S4 retrograde Rahu": lambda m, c: m.query_retrograde_periods("Rahu", W0, W1, conn=c),
    "S4 retrograde Ketu": lambda m, c: m.query_retrograde_periods("Ketu", W0, W1, conn=c),
    "S4 retrograde Saturn": lambda m, c: m.query_retrograde_periods("Saturn", W0, W1, conn=c),
    "S5 native lifetime cache": lambda m, c: m.get_ephemeris_cache_native_lifetime(conn=c),
    "S6 all": lambda m, c: m.query_ephemeris(conn=c, limit=500),
    "S6 nodes": lambda m, c: m.query_ephemeris(conn=c, bodies=["Rahu", "Ketu"], limit=500),
    "S6 window limit": lambda m, c: m.query_ephemeris(conn=c, date_start=date(2026, 7, 1), date_end=date(2026, 7, 5), limit=45),
    "S7 check_volume": lambda m, c: m.check_volume(conn=c),
}


def _sancara(module: str):
    """P8 driver: PATH-A `get_ephemeris` of `module` (the pinned copy, or the dead unpinned `engine`) at one instant."""
    def run(ctx: Ctx):
        import dataclasses
        import importlib
        from datetime import timezone

        res = importlib.import_module(module).get_ephemeris(
            datetime(2026, 7, 12, 6, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))), ayanamsha="lahiri", db_conn=ctx.pg3)
        assert res.source == "bg_ephemeris"                                # PATH-A, not the live fallback
        return {"source": res.source, "grahas": {k: dataclasses.asdict(v) for k, v in res.grahas.items()}}
    return run


def _driven() -> list[Reader]:
    out: list[Reader] = []
    for label, call in S_CALLS.items():
        out.append(Reader(label.split()[0], label, SAME, _mk(pinned, call)))
    out.append(Reader("S9", "S9 /all_bodies_range rows (tropical)", SAME,
                      _route(routes.get_all_bodies_range, W0, "2026-07-20", count_only=False, ayanamsha_id="tropical")))
    out.append(Reader("S9", "S9 /all_bodies_range rows (sidereal)", SAME,
                      _route(routes.get_all_bodies_range, W0, "2026-07-20", count_only=False, ayanamsha_id="lahiri_chitrapaksha")))
    out.append(Reader("S9", "S9 /all_bodies_range count_only", SAME,
                      _route(routes.get_all_bodies_range, W0, W1, count_only=True, ayanamsha_id="tropical")))
    out.append(Reader("S11", "S11 /native_lifetime_meta", SAME,
                      _route(routes.get_native_lifetime_meta, start_date="2026-01-01", end_date="2026-12-31", count_only=False)))

    def kota(ctx: Ctx):
        from services.ka_kota_chakra import writer as kota_writer
        return kota_writer._fetch_daily_nak_idx_by_graha(ctx.pg3, DAYS[0], DAYS[-1], 23.9)

    out.append(Reader("P4", "P4 ka_kota_chakra._fetch_daily_nak_idx_by_graha", SAME, kota, when_true_missing=LOUD))

    out.append(Reader("P8", "P8 ka_graha_sancara.engine_pinned PATH-A get_ephemeris", SAME,
                      _sancara("services.ka_graha_sancara.engine_pinned"), when_true_missing=LOUD))

    def muhurta_signs(ctx: Ctx):
        from brahmagyan.phala import muhurta
        return muhurta._read_transiting_sign_ids(datetime(2026, 7, 12, 6, 0), ctx.dsn)

    out.append(Reader("P9", "P9 phala.muhurta._read_transiting_sign_ids (through P8)", SAME, muhurta_signs,
                      when_true_missing=LOUD))
    return out


def _legacy() -> list[Reader]:
    why = ("dead unpinned copy in brahmagyan/l0_ephemeris.py (kept byte-identical: editing it moves 49 writer digests); "
           "it must differ once a MEAN set exists, which proves this harness detects the defect")
    # calls on a non-node body (Venus, Saturn) never see a node row: the legacy copy is correct for them, so they are not
    # xfail rows (their pinned twins above still assert the same result)
    rows = [Reader(label.split()[0], "LEGACY " + label, LEGACY, _mk(legacy, call), why)
            for label, call in S_CALLS.items() if not label.endswith(("Venus window", "retrograde Saturn"))]
    rows.append(Reader("P8", "LEGACY P8 ka_graha_sancara.engine_pinned PATH-A get_ephemeris", LEGACY,
                       _sancara("services.ka_graha_sancara.engine"),
                       "dead unpinned copy in services/ka_graha_sancara/engine.py (kept byte-identical: a one-line edit moves ~43 writer "
                       "digests); last-row-wins body_map, so it must differ once a MEAN set exists"))
    return rows


def _not_driven() -> list[Reader]:
    nd = lambda rid, reason: Reader(rid, rid, NOT_DRIVEN, None, reason)  # noqa: E731
    return [
        nd("P3", "ka_kshetra stage 0 (stage0_kinematics.fetch_ephemeris_series): travels with the I-10 digest move (PR E, prepared last)"),
        nd("L1-e", "get_av_transit_gating is a TypeScript tool over HTTP /planet_transit (= S2, driven above); its INPUT guard is PR D"),
        nd("T3", "pact_query TRIGGER (TypeScript) reaches the table only through HTTP /planet_transit = S2, driven above"),
        nd("S17", "migration 606 integrity probe: an applied migration, replaced by migration 1228 (not touched here)"),
        nd("L1-c", "get_graha_yuddha reads only Mars/Mercury/Jupiter/Venus/Saturn by construction (body = ANY with five non-node bodies)"),
        nd("S13/S14/S15/S20", "legacy statements on columns that do not exist in the current schema (planet/longitude/retrograde); they error and are swallowed"),
        nd("reg", "asset_registry count_sql floor statements (seed + applied migrations 174/525/606): migration 1228 re-sets the floor"),
        nd("P1", "Pravaha reader (w2g arcs, db_source): imported read-only and driven in the proof-extension commit of this stack"),
        nd("P2", "Pravaha reader (gochara kernel / db_source second path): proof-extension commit of this stack"),
        nd("P5", "Pravaha reader: proof-extension commit of this stack"),
        nd("P6", "Pravaha reader: proof-extension commit of this stack"),
        nd("P7", "Pravaha reader (ka_vedha_gochara retrograde-day set): proof-extension commit of this stack"),
        nd("P14", "Pravaha reader: proof-extension commit of this stack"),
        nd("P15", "Pravaha reader: proof-extension commit of this stack"),
    ]


def _harness_selfcheck() -> list[Reader]:
    """A synthetic reader that guards itself (counts the rows it sees for one node/date and refuses when it is not exactly
    one): it proves the LOUD path of this harness works. Not a T1 reader."""
    def guarded(ctx: Ctx):
        cur = ctx.conn.cursor()
        cur.execute("SELECT count(*) FROM ephemeris_daily WHERE body = 'Rahu' AND date = %s", (D1,))
        n = cur.fetchone()[0]
        if n != 1:
            raise NodeSeriesError(f"harness self-check: {n} rows for (Rahu, {D1})")
        return {"ok": True, "rows": n}
    return [Reader("harness", "harness: self-guarding reader refuses on two rows", LOUD, guarded)]


READERS: list[Reader] = _driven() + _legacy() + _harness_selfcheck() + _not_driven()
_RUNNABLE = [r for r in READERS if r.kind in (SAME, LOUD, LEGACY)]


def _param(r: Reader):
    marks = []
    if r.kind == LEGACY:
        marks.append(pytest.mark.xfail(strict=True, reason=r.reason, raises=AssertionError))
    return pytest.param(r, id=r.label, marks=marks)


# ------------------------------------------------------------------------------------------- the fixtures themselves
def test_the_fixture_is_the_live_shape(ctx_true, ctx_mixed):
    """The synthetic world is what the claim says: the CURRENT 3-column key on db_true, only the 4-column key on db_mixed,
    nine rows per date vs eleven, and the MEAN Ketu carries Rahu's speed and flag."""
    def one(ctx, sql):
        cur = ctx.conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

    keys_true = {r[0] for r in one(ctx_true, "SELECT conname FROM pg_constraint WHERE conrelid = 'public.ephemeris_daily'::regclass AND contype = 'u'")}
    keys_mixed = {r[0] for r in one(ctx_mixed, "SELECT conname FROM pg_constraint WHERE conrelid = 'public.ephemeris_daily'::regclass AND contype = 'u'")}
    assert keys_true == {"ephemeris_daily_date_body_ayanamsha_id_key"} and keys_mixed == set()
    idx = one(ctx_mixed, "SELECT indexdef FROM pg_indexes WHERE indexname = 'ephemeris_daily_date_body_ayanamsha_id_node_mode_key'")
    assert "NULLS NOT DISTINCT" in idx[0][0] and "(date, body, ayanamsha_id, node_mode)" in idx[0][0]
    per_date_true = one(ctx_true, f"SELECT count(*) FROM ephemeris_daily WHERE date = '{D1}'")[0][0]
    per_date_mixed = one(ctx_mixed, f"SELECT count(*) FROM ephemeris_daily WHERE date = '{D1}'")[0][0]
    assert (per_date_true, per_date_mixed) == (9, 11)
    assert one(ctx_true, "SELECT count(*) FROM ephemeris_daily WHERE node_mode = 'mean'")[0][0] == 0
    mean = one(ctx_mixed, "SELECT body, speed_dps, is_retrograde FROM ephemeris_daily WHERE node_mode = 'mean' ORDER BY date, body LIMIT 2")
    assert mean[0][0] == "Ketu" and mean[1][0] == "Rahu" and mean[0][1] == mean[1][1] and mean[0][2] is True and mean[1][2] is True
    # the TRUE Ketu rows keep today's inverted speed/flag (the existing defect the step-2 rebuild corrects)
    tk = one(ctx_true, f"SELECT t.speed_dps, r.speed_dps, t.is_retrograde FROM ephemeris_daily t JOIN ephemeris_daily r ON r.date = t.date "
                       f"AND r.body = 'Rahu' WHERE t.body = 'Ketu' AND t.date = '{D1}'")[0]
    assert tk[0] == -tk[1] and tk[2] is False
    # a DUPLICATE under the new key is impossible: the proof does not rest on the database accepting two TRUE rows
    cur = ctx_mixed.conn.cursor()
    with pytest.raises(psycopg2.errors.UniqueViolation):
        cur.execute(INSERT, _row(DAYS[1], "Rahu", 1.0, -0.05, True, "true"))


def test_every_t1_reader_is_driven_or_explained():
    """Lint-style completeness: every T1 id has at least one driver or an explicit not_driven reason; none is both."""
    by_id: dict[str, list[Reader]] = {}
    for r in READERS:
        by_id.setdefault(r.rid, []).append(r)
    by_id.pop("harness", None)                                            # the harness self-check is not a T1 reader
    missing = [i for i in T1_IDS if i not in by_id]
    assert not missing, f"T1 reader ids with neither a driver nor a not_driven reason: {missing}"
    unknown = [i for i in by_id if i not in T1_IDS]
    assert not unknown, f"registry ids that are not T1 ids: {unknown}"
    for rid, rs in by_id.items():
        nd = [r for r in rs if r.kind == NOT_DRIVEN]
        driven = [r for r in rs if r.kind in (SAME, LOUD)]
        assert not (nd and driven), f"{rid} is both driven and not_driven"
        for r in nd:
            assert len(r.reason.strip()) >= 20 and r.run is None, f"{rid}: a not_driven row needs a written reason and no callable"
        if not nd:
            assert driven, f"{rid} has only legacy rows: the live reader must be driven"
        for r in rs:
            if r.kind == LEGACY:
                assert r.reason.strip(), f"{r.label}: a legacy row needs a reason"


def test_every_legacy_copy_has_a_pinned_twin():
    live = {r.label for r in READERS if r.kind == SAME}
    for r in READERS:
        if r.kind == LEGACY:
            assert r.label.removeprefix("LEGACY ") in live, f"{r.label} has no driven pinned twin"


# ------------------------------------------------------------------------------------------- the proof
@pytest.mark.parametrize("reader", [_param(r) for r in _RUNNABLE if r.kind in (SAME, LEGACY)])
def test_reader_returns_the_same_result_with_a_mean_series_beside_the_true_one(reader, ctx_true, ctx_mixed):
    base = normalise(reader.run(ctx_true))
    mixed = normalise(reader.run(ctx_mixed))
    if isinstance(base, dict) and "ok" in base:
        assert base["ok"] is True, f"{reader.label}: the baseline read failed: {base.get('error')}"
    assert mixed == base, f"{reader.label}: the result changed once a MEAN Rahu/Ketu set exists beside the TRUE one"


@pytest.mark.parametrize("reader", [_param(r) for r in _RUNNABLE if r.kind == LOUD])
def test_reader_refuses_loudly_instead_of_reading_both_series(reader, ctx_true, ctx_mixed):
    reader.run(ctx_true)                                                  # the TRUE-only table is served normally
    with pytest.raises((NodeSeriesError, RuntimeError, ValueError)):
        reader.run(ctx_mixed)


@pytest.mark.parametrize("reader", [pytest.param(r, id=r.label) for r in _RUNNABLE if r.when_true_missing == LOUD])
def test_a_required_path_reader_refuses_loudly_when_the_true_series_is_absent_and_the_mean_one_present(reader, ctx_true, ctx_true_missing):
    """The reader must not 'repair' a hole in the TRUE series by reading MEAN: it raises NodeSeriesError (or an explicit error)."""
    reader.run(ctx_true)                                                  # served normally on the TRUE-only table
    with pytest.raises((NodeSeriesError, RuntimeError, ValueError)):
        reader.run(ctx_true_missing)


def test_the_proof_is_not_vacuous_the_mean_series_changes_the_node_longitudes(ctx_true, ctx_mixed):
    """Reading the MEAN series instead (what a wrong pin would do) is visible in this fixture."""
    def lon(ctx, mode):
        cur = ctx.conn.cursor()
        cur.execute("SELECT tropical_longitude FROM ephemeris_daily WHERE body = 'Rahu' AND node_mode = %s AND date = %s", (mode, D2))
        r = cur.fetchone()
        return None if r is None else float(r[0])

    t, m = lon(ctx_mixed, "true"), lon(ctx_mixed, "mean")
    assert t is not None and m is not None and abs(t - m) > 0.2
    assert lon(ctx_true, "true") == t and lon(ctx_true, "mean") is None


def test_the_proof_has_not_silently_shrunk():
    """A collected-count floor: the registry may only grow (later PRs flip not_driven rows to driven), so a refactor that
    quietly drops reader cases cannot keep this file green with a smaller proof."""
    kinds = [r.kind for r in _RUNNABLE]
    assert kinds.count(SAME) >= 20, kinds.count(SAME)
    assert kinds.count(LOUD) >= 1
    assert kinds.count(LEGACY) >= 14, kinds.count(LEGACY)


# ------------------------------------------------------------------------------------------- CI-visible pass count
_THIS_FILE = os.path.basename(__file__)


class _ProofSummary:
    """Registered by the autouse fixture below. Prints the pass count of THIS module in the terminal summary (shown under
    `-q`, which the sidecar CI step uses without `-rs`), plus a GitHub Actions ::notice:: annotation."""

    def pytest_terminal_summary(self, terminalreporter):
        def n(outcome: str, phases: tuple[str, ...]) -> int:
            return sum(1 for rep in terminalreporter.stats.get(outcome, [])
                       if f"{_THIS_FILE}::" in getattr(rep, "nodeid", "") and getattr(rep, "when", "call") in phases)

        counts = {"passed": n("passed", ("call",)), "xfailed": n("xfailed", ("call",)), "xpassed": n("xpassed", ("call",)),
                  "failed": n("failed", ("call",)), "error": n("error", ("setup", "teardown", "call")),
                  "skipped": n("skipped", ("setup", "call"))}
        line = ("NODE-SERIES PROOF ({f}): {passed} passed, {xfailed} xfailed (known-unpinned legacy copies, strict), "
                "{xpassed} xpassed, {failed} failed, {error} errors, {skipped} skipped").format(f=_THIS_FILE, **counts)
        terminalreporter.write_line(line, bold=True)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            terminalreporter.write_line(f"::notice title=node-series reader proof::{line}")


@pytest.fixture(scope="module", autouse=True)
def _register_proof_summary(request):
    pm = request.config.pluginmanager
    if not pm.has_plugin("node_series_proof_summary"):
        pm.register(_ProofSummary(), "node_series_proof_summary")
    yield
