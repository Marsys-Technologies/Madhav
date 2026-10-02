"""node_series_digest v1 on a disposable local PostgreSQL (never the project database). Run:
    PG_BIN=/opt/homebrew/opt/postgresql@15/bin python3 -m pytest 00_ARCHITECTURE/briefs/suvarna/exec/node_series/digest/tests -q
Proves: the digest does NOT move when non-node rows change, when the other node_mode's rows are present or change, or with physical/insertion
order; it DOES move on a 6th-decimal longitude or speed change, a flag flip, a row added, removed or re-keyed; it ignores the excluded columns;
the TRUE bind works; the body-scoped and non-node variants agree with it; cost on a synthetic 183,352-row series.
"""
import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import uuid

import psycopg
import pytest

HERE = pathlib.Path(__file__).resolve().parent
DIR = HERE.parent
D1, D2, D3 = (DIR / n for n in ("node_series_digest_v1.sql", "node_series_digest_bodies_v1.sql", "non_node_digest_v1.sql"))


def _bin(name):
    pb = os.environ.get("PG_BIN")
    if pb and os.path.exists(os.path.join(pb, name)):
        return os.path.join(pb, name)
    import glob
    for c in [shutil.which(name), f"/opt/homebrew/bin/{name}", *sorted(glob.glob(f"/usr/lib/postgresql/*/bin/{name}"), reverse=True)]:
        if c and os.path.exists(c):
            return c
    return None


INITDB, PG_CTL, PSQL = _bin("initdb"), _bin("pg_ctl"), _bin("psql")
pytestmark = pytest.mark.skipif(not (INITDB and PG_CTL and PSQL) or (hasattr(os, "geteuid") and os.geteuid() == 0),
                                reason="no local PostgreSQL binaries (or root): digest tests NOT RUN")

DDL = """
CREATE TABLE public.ephemeris_daily (
  id uuid NOT NULL DEFAULT gen_random_uuid(), date date NOT NULL, body text NOT NULL, ayanamsha_id text NOT NULL DEFAULT 'tropical',
  tropical_longitude numeric NOT NULL, latitude numeric NOT NULL DEFAULT 0.0, speed_dps numeric NOT NULL DEFAULT 0.0,
  is_retrograde boolean NOT NULL DEFAULT false, sign_number smallint, degree_in_sign numeric, nakshatra_number smallint,
  source_citation text NOT NULL DEFAULT 'pyswisseph DE441 + Swiss Ephemeris', computed_at timestamptz NOT NULL DEFAULT now(),
  node_mode text, epoch_convention text,
  CONSTRAINT ephemeris_daily_pkey PRIMARY KEY (id),
  CONSTRAINT ephemeris_daily_node_mode_check CHECK (node_mode IS NULL OR node_mode = ANY (ARRAY['true','mean']))
);
-- the post-step-2 key (migration 1227 index; the old three-column key is dropped by 1250)
CREATE UNIQUE INDEX ephemeris_daily_date_body_ayanamsha_node_mode_uq ON public.ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT;
"""
# DAYS days x (7 non-node bodies + TRUE Rahu/Ketu + MEAN Rahu/Ketu); MEAN: Ketu = Rahu + 180, Ketu speed = Rahu speed, both retrograde
SEED = """
INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, speed_dps, is_retrograde, node_mode, epoch_convention, sign_number)
SELECT DATE '2000-01-01' + n, b.body, ((n * 1.37 + b.i * 11) % 360)::numeric(12,7), (0.5 + b.i * 0.01)::numeric(10,7), false, NULL, 'noon_ut', 3
FROM generate_series(0, {days} - 1) n, (VALUES ('Sun',1),('Moon',2),('Mars',3),('Mercury',4),('Jupiter',5),('Venus',6),('Saturn',7)) b(body, i);
INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, speed_dps, is_retrograde, node_mode, epoch_convention)
SELECT DATE '2000-01-01' + n, b.body,
       (CASE b.body WHEN 'Rahu' THEN (125.04064606 - 0.053 * n) ELSE (125.04064606 - 0.053 * n + 180) END % 360 + 360) % 360,
       -0.05295 - 0.0004 * sin(n / 3.7), true, 'mean', 'noon_ut'
FROM generate_series(0, {days} - 1) n, (VALUES ('Rahu'), ('Ketu')) b(body);
INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, speed_dps, is_retrograde, node_mode, epoch_convention)
SELECT DATE '2000-01-01' + n, b.body,
       (CASE b.body WHEN 'Rahu' THEN (123.95402284 - 0.0529 * n + 0.7 * sin(n / 11.0)::numeric) ELSE (123.95402284 - 0.0529 * n + 0.7 * sin(n / 11.0)::numeric + 180) END % 360 + 360) % 360,
       CASE b.body WHEN 'Rahu' THEN -0.05 * cos(n / 11.0) ELSE 0.05 * cos(n / 11.0) END,        -- the stored TRUE defect: Ketu speed = -Rahu speed
       (CASE b.body WHEN 'Rahu' THEN -0.05 * cos(n / 11.0) ELSE 0.05 * cos(n / 11.0) END) < 0, 'true', 'noon_ut'
FROM generate_series(0, {days} - 1) n, (VALUES ('Rahu'), ('Ketu')) b(body);
"""


class Cluster:
    def __init__(self, port, sock):
        self.port, self.sock = port, sock

    def conn(self, db):
        return psycopg.connect(host="127.0.0.1", port=self.port, dbname=db, user="postgres", autocommit=True, connect_timeout=10)

    def run_sql(self, db, file, **binds):
        cmd = [PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(self.port), "-U", "postgres", "-d", db, "-v", "ON_ERROR_STOP=1"]
        for k, v in binds.items():
            cmd += ["-v", f"{k}={v}"]
        r = subprocess.run(cmd + ["-f", str(file)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return tuple(r.stdout.strip().split("|"))

    def ex(self, db, sql):
        with self.conn(db) as c:
            c.execute(sql)

    def new_db(self, days):
        name = "t" + uuid.uuid4().hex[:10]
        with self.conn("postgres") as c:
            c.execute(f"CREATE DATABASE {name}")
        self.ex(name, DDL)
        self.ex(name, SEED.format(days=days))
        return name


@pytest.fixture(scope="module")
def cl():
    d = tempfile.mkdtemp(prefix="pgdigest_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o", f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d} -c fsync=off",
                    "-l", d + "/log", "-w", "start"], check=True, capture_output=True)
    try:
        yield Cluster(port, d)
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
def db(cl):
    return cl.new_db(400)


def mean(cl, db):
    return cl.run_sql(db, D1, node_mode="mean")


def true(cl, db):
    return cl.run_sql(db, D1, node_mode="true")


def non_node(cl, db):
    return cl.run_sql(db, D3)


def test_shape_and_format(cl, db):
    n, h = mean(cl, db)
    assert n == "800" and len(h) == 64 and h == h.lower()
    # the preimage is what the header says: rebuild it in python from the rows and hash it
    import hashlib
    with cl.conn(db) as c:
        rows = c.execute("SELECT ayanamsha_id, body, to_char(date,'YYYY-MM-DD'), node_mode, round(tropical_longitude,9)::text, round(speed_dps,9)::text, "
                         "CASE WHEN is_retrograde THEN '1' ELSE '0' END FROM public.ephemeris_daily WHERE node_mode='mean' AND body IN ('Rahu','Ketu')").fetchall()
    rows.sort(key=lambda r: (r[0].encode(), r[1].encode(), r[2]))
    pre = "node_series_digest_v1\n" + "\n".join("|".join(r) for r in rows)
    assert hashlib.sha256(pre.encode()).hexdigest() == h
    first = pre.split("\n")[1]
    assert first.count("|") == 6 and first.startswith("tropical|Ketu|2000-01-01|mean|")      # 'Ketu' sorts before 'Rahu' (COLLATE "C")
    assert first.split("|")[4].count(".") == 1 and len(first.split("|")[4].split(".")[1]) == 9


def test_does_not_move_when_non_node_rows_change(cl, db):
    before, nn = mean(cl, db), non_node(cl, db)
    cl.ex(db, "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude + 1, speed_dps = 9, is_retrograde = true WHERE node_mode IS NULL")
    cl.ex(db, "DELETE FROM public.ephemeris_daily WHERE body = 'Sun' AND date < '2000-02-01'")
    cl.ex(db, "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude) VALUES ('2100-01-01', 'Moon', 5)")
    assert mean(cl, db) == before and true(cl, db) is not None
    assert non_node(cl, db) != nn                                                                       # ... and the non-node digest DID move


def test_does_not_move_when_true_rows_are_present_beside_it_or_change(cl, db):
    before_mean, before_true = mean(cl, db), true(cl, db)
    cl.ex(db, "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude + 0.5, speed_dps = -speed_dps, is_retrograde = NOT is_retrograde WHERE node_mode = 'true'")
    cl.ex(db, "DELETE FROM public.ephemeris_daily WHERE node_mode = 'true' AND body = 'Ketu' AND date < '2000-03-01'")
    cl.ex(db, "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2101-01-01', 'Rahu', 5, 'true')")
    assert mean(cl, db) == before_mean
    assert true(cl, db) != before_true
    # and the reverse: mean changes leave the TRUE digest alone
    t = true(cl, db)
    cl.ex(db, "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude + 0.5 WHERE node_mode = 'mean'")
    assert true(cl, db) == t and mean(cl, db) != before_mean


def test_does_not_depend_on_physical_or_insertion_order(cl, db):
    before = mean(cl, db)
    with cl.conn(db) as c:
        c.execute("CREATE TEMP TABLE keep AS SELECT * FROM public.ephemeris_daily WHERE node_mode = 'mean'")
        c.execute("DELETE FROM public.ephemeris_daily WHERE node_mode = 'mean'")
        c.execute("INSERT INTO public.ephemeris_daily SELECT * FROM keep ORDER BY random()")
        c.execute("VACUUM FULL public.ephemeris_daily")
    assert mean(cl, db) == before
    # a freshly generated id and computed_at (what a rebuild changes) do not matter either
    cl.ex(db, "UPDATE public.ephemeris_daily SET id = gen_random_uuid(), computed_at = now() + interval '1 day' WHERE node_mode = 'mean'")
    assert mean(cl, db) == before


@pytest.mark.parametrize("sql", [
    "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude + 0.000001 WHERE node_mode='mean' AND body='Rahu' AND date='2000-01-10'",
    "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude - 0.000001 WHERE node_mode='mean' AND body='Ketu' AND date='2000-01-10'",
    "UPDATE public.ephemeris_daily SET speed_dps = speed_dps + 0.000001 WHERE node_mode='mean' AND body='Ketu' AND date='2000-01-10'",
    "UPDATE public.ephemeris_daily SET is_retrograde = false WHERE node_mode='mean' AND body='Ketu' AND date='2000-01-10'",
    "DELETE FROM public.ephemeris_daily WHERE node_mode='mean' AND body='Rahu' AND date='2000-01-10'",
    "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2050-01-01','Rahu',1,'mean')",
    "UPDATE public.ephemeris_daily SET ayanamsha_id = 'lahiri_chitrapaksha' WHERE node_mode='mean' AND body='Rahu' AND date='2000-01-10'",
    "UPDATE public.ephemeris_daily SET date = date + 5000 WHERE node_mode='mean' AND body='Rahu' AND date='2000-01-10'",
], ids=["lon-6th-decimal-rahu", "lon-6th-decimal-ketu", "speed-6th-decimal", "flag-flip", "row-removed", "row-added", "re-keyed-ayanamsha", "re-keyed-date"])
def test_moves_on_any_change_to_a_row_of_the_series(cl, db, sql):
    before = mean(cl, db)
    cl.ex(db, sql)
    assert mean(cl, db)[1] != before[1]


@pytest.mark.parametrize("sql", [
    "UPDATE public.ephemeris_daily SET tropical_longitude = tropical_longitude + 0.0000000001 WHERE node_mode='mean' AND body='Rahu' AND date='2000-01-10'",   # below the 9-decimal grid
    "UPDATE public.ephemeris_daily SET latitude = 0.5 WHERE node_mode='mean'",
    "UPDATE public.ephemeris_daily SET source_citation = 'other engine' WHERE node_mode='mean'",
    "UPDATE public.ephemeris_daily SET epoch_convention = 'midnight_ut' WHERE node_mode='mean'",
    "UPDATE public.ephemeris_daily SET sign_number = 7, degree_in_sign = 1.5, nakshatra_number = 9 WHERE node_mode='mean'",
    "UPDATE public.ephemeris_daily SET computed_at = now() + interval '9 days', id = gen_random_uuid() WHERE node_mode='mean'",
], ids=["below-9-decimals", "latitude", "source_citation", "epoch_convention", "derived-columns", "computed_at-id"])
def test_ignores_the_excluded_columns_and_sub_grid_noise(cl, db, sql):
    before = mean(cl, db)
    cl.ex(db, sql)
    assert mean(cl, db) == before


def test_the_nulls_are_never_silently_dropped(cl, db):
    """concat_ws skips NULLs: every field of the series is NOT NULL, and the non-node variant writes the NULL node_mode as '~'."""
    with cl.conn(db) as c:
        assert c.execute("SELECT count(*) FROM public.ephemeris_daily WHERE node_mode='mean' AND (tropical_longitude IS NULL OR speed_dps IS NULL OR is_retrograde IS NULL)").fetchone()[0] == 0
    n, h = non_node(cl, db)
    assert n == "2800" and len(h) == 64


def test_absent_series_is_null_not_the_hash_of_nothing(cl, db):
    cl.ex(db, "DELETE FROM public.ephemeris_daily WHERE node_mode = 'mean'")
    assert mean(cl, db) == ("0", "")                                                                     # psql -t -A prints NULL as empty
    assert true(cl, db)[0] == "800"


def test_body_scoped_variant_agrees_with_the_canonical_one_and_splits_it(cl, db):
    both = cl.run_sql(db, D2, node_mode="mean", bodies="{Rahu,Ketu}")
    assert both == mean(cl, db)
    r, k = cl.run_sql(db, D2, node_mode="true", bodies="{Rahu}"), cl.run_sql(db, D2, node_mode="true", bodies="{Ketu}")
    assert r[0] == k[0] == "400" and r[1] != k[1] and r[1] != true(cl, db)[1]
    cl.ex(db, "UPDATE public.ephemeris_daily SET speed_dps = -speed_dps, is_retrograde = NOT is_retrograde WHERE node_mode='true' AND body='Ketu'")   # the TRUE Ketu correction
    assert cl.run_sql(db, D2, node_mode="true", bodies="{Rahu}") == r                                    # TRUE Rahu untouched
    assert cl.run_sql(db, D2, node_mode="true", bodies="{Ketu}") != k                                    # TRUE Ketu accounted for separately
    assert non_node(cl, db) is not None and mean(cl, db) == both


def test_the_true_bind_and_the_two_series_are_distinct(cl, db):
    assert true(cl, db)[1] != mean(cl, db)[1]
    assert true(cl, db) == true(cl, db)


def test_cost_on_a_series_of_183352_rows(cl):
    """91,676 days x (Rahu, Ketu) per node_mode, plus the 7 non-node bodies: the real table shape (1,008,436 rows)."""
    name = "t" + uuid.uuid4().hex[:10]
    with cl.conn("postgres") as c:
        c.execute(f"CREATE DATABASE {name}")
    cl.ex(name, DDL)
    cl.ex(name, SEED.format(days=91676))
    cl.ex(name, "ANALYZE public.ephemeris_daily")
    assert cl.run_sql(name, D1, node_mode="mean")[0] == "183352"
    t0 = time.time()
    n, h = cl.run_sql(name, D1, node_mode="mean")
    t_mean = time.time() - t0
    t0 = time.time()
    cl.run_sql(name, D1, node_mode="true")
    t_true = time.time() - t0
    t0 = time.time()
    nn = cl.run_sql(name, D3)
    t_non = time.time() - t0
    print(f"\nCOST rows={n} mean={t_mean:.2f}s true={t_true:.2f}s non_node={t_non:.2f}s (psql start-up included) table_rows=1008436")
    assert n == "183352" and nn[0] == str(7 * 91676) and t_mean < 30 and t_true < 30
