"""Pair of migration 1268 (SS N-111): the bg_doshas / bg_yogas writers must carry `attribution_state` across their
delete-then-insert rebuild, otherwise the column silently resets to NULL on the next rebuild (a signal with no
durability, CLAUDE.md N.8).

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per
available major version (15 and 17). Nothing here touches a real database. The REAL writer functions
`brahmagyan.l0_doshas.seed_doshas` and `brahmagyan.l0_yogas.seed_yogas` run against the production DDL of their six
tables (pg_dump of production, schema only; the FK to classical_text_chunks is dropped because the fixture has no corpus)
plus the `attribution_state` column and CHECK exactly as migration 1268 adds them, as `data_plane_builder` (NOSUPERUSER
NOINHERIT, SELECT/INSERT/UPDATE/DELETE only, no CREATE on schema public), with dict rows like the orchestrator.

What it proves:
  * rebuild_keeps_values   53 unsourced doshas + kala_sarpa_yoga unsourced (the 1268 backfill) and extra refuted/sourced
                           classifications survive TWO rebuilds of both writers unchanged; projection counts stay 79/79/148/148.
  * new/removed/re-cited   a NEW entry with the placeholder citation defaults to unsourced, a new entry with a real
                           citation stays NULL, a REMOVED entry's value goes with its row and is NOT resurrected when the
                           entry returns, a RE-CITED entry's old state is dropped (it described the old citation).
  * column_absent          a writer deployed before migration 1268 still works and never creates the column.
  * atomic                 a failed rebuild leaves the stored states untouched (the restore is inside the transaction).
  * falsifier              with capture/restore neutered (main today) the same scenarios FAIL.
  * mutants                9 mutants of the helper and both writer-side call sites are each detected.

HONEST LIMITS: stock PostgreSQL, reduced fixture DB without the corpus (yoga extraction patched to empty); it does not run
the orchestrator, does not read production, and `REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import collections
import copy
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brahmagyan import l0_attribution_state as attr_module, l0_doshas, l0_yogas  # noqa: E402

WRITERS_DDL = r"""
CREATE TABLE public.brahma_dosha_catalog (
    canonical_id text NOT NULL,
    name_sa text NOT NULL,
    name_en text NOT NULL,
    category text NOT NULL,
    formation_rule_jsonb jsonb NOT NULL,
    formation_text text NOT NULL,
    effects_text text NOT NULL,
    severity_grades jsonb,
    cancellation_conditions jsonb,
    classical_citations jsonb,
    source_chunk_ids bigint[] DEFAULT ARRAY[]::bigint[],
    associated_remedies uuid[] DEFAULT ARRAY[]::uuid[],
    school text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT brahma_dosha_catalog_category_check CHECK ((category = ANY (ARRAY['graha_placement'::text, 'rashi_combination'::text, 'nakshatra_compatibility'::text, 'tithi'::text, 'other'::text])))
);

CREATE TABLE public.brahma_ontology (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_class text NOT NULL,
    canonical_id text NOT NULL,
    canonical_name_en text NOT NULL,
    canonical_name_sa text,
    synonyms text[] DEFAULT '{}'::text[] NOT NULL,
    description text,
    source_citation text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.brahma_yoga_catalog (
    canonical_id text NOT NULL,
    name_sa text NOT NULL,
    name_en text NOT NULL,
    category text NOT NULL,
    formation_rule_jsonb jsonb NOT NULL,
    formation_text text NOT NULL,
    significations_jsonb jsonb DEFAULT '{}'::jsonb NOT NULL,
    significations_text text NOT NULL,
    cancellation_conditions jsonb,
    classical_citations jsonb,
    source_chunk_ids bigint[] DEFAULT ARRAY[]::bigint[],
    school text NOT NULL,
    rare boolean DEFAULT false NOT NULL,
    computed_strength_formula text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    bhanga_rules_jsonb jsonb,
    partial_formation_threshold numeric,
    strength_formula_ref text,
    result_class text,
    CONSTRAINT brahma_yoga_catalog_category_check CHECK ((category = ANY (ARRAY['raja'::text, 'dhana'::text, 'pancha_mahapurusha'::text, 'aristha'::text, 'sannyasa'::text, 'other'::text]))),
    CONSTRAINT brahma_yoga_catalog_result_class_check CHECK ((result_class = ANY (ARRAY['benefic'::text, 'malefic'::text, 'mixed'::text, 'neutral'::text])))
);

CREATE TABLE public.brahma_yoga_source_chunks (
    canonical_id text NOT NULL,
    source_chunk_id uuid NOT NULL
);

CREATE TABLE public.reference_doshas (
    canonical_id text NOT NULL,
    name_en text NOT NULL,
    category text NOT NULL
);

CREATE TABLE public.reference_yogas (
    canonical_id text NOT NULL,
    name_en text NOT NULL,
    category text NOT NULL
);

ALTER TABLE ONLY public.brahma_dosha_catalog
    ADD CONSTRAINT brahma_dosha_catalog_pkey PRIMARY KEY (canonical_id);

ALTER TABLE ONLY public.brahma_ontology
    ADD CONSTRAINT brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id);

ALTER TABLE ONLY public.brahma_ontology
    ADD CONSTRAINT brahma_ontology_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.brahma_yoga_catalog
    ADD CONSTRAINT brahma_yoga_catalog_pkey PRIMARY KEY (canonical_id);

ALTER TABLE ONLY public.brahma_yoga_source_chunks
    ADD CONSTRAINT brahma_yoga_source_chunks_pkey PRIMARY KEY (canonical_id, source_chunk_id);

ALTER TABLE ONLY public.reference_doshas
    ADD CONSTRAINT reference_doshas_pkey PRIMARY KEY (canonical_id);

ALTER TABLE ONLY public.reference_yogas
    ADD CONSTRAINT reference_yogas_pkey PRIMARY KEY (canonical_id);

CREATE INDEX idx_brahma_ontology_canonical ON public.brahma_ontology USING btree (canonical_id);

CREATE INDEX idx_brahma_ontology_class ON public.brahma_ontology USING btree (entity_class);

CREATE INDEX idx_brahma_ontology_synonyms ON public.brahma_ontology USING gin (synonyms);

CREATE INDEX idx_brahma_yoga_source_chunks_chunk ON public.brahma_yoga_source_chunks USING btree (source_chunk_id);

CREATE INDEX idx_dosha_category ON public.brahma_dosha_catalog USING btree (category);

CREATE INDEX idx_dosha_school ON public.brahma_dosha_catalog USING btree (school);

CREATE INDEX idx_yoga_category ON public.brahma_yoga_catalog USING btree (category);

CREATE INDEX idx_yoga_formation ON public.brahma_yoga_catalog USING gin (formation_rule_jsonb);

CREATE INDEX idx_yoga_school ON public.brahma_yoga_catalog USING btree (school);

ALTER TABLE ONLY public.brahma_yoga_source_chunks
    ADD CONSTRAINT brahma_yoga_source_chunks_canonical_id_fkey FOREIGN KEY (canonical_id) REFERENCES public.brahma_yoga_catalog(canonical_id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reference_doshas
    ADD CONSTRAINT fk_ref_dosha FOREIGN KEY (canonical_id) REFERENCES public.brahma_dosha_catalog(canonical_id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reference_yogas
    ADD CONSTRAINT fk_ref_yoga FOREIGN KEY (canonical_id) REFERENCES public.brahma_yoga_catalog(canonical_id) ON DELETE CASCADE;
"""

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")  # must be SHORT (unix socket path limit)
VERSIONS = ["15", "17"]
TABLES = ["brahma_dosha_catalog", "brahma_yoga_catalog", "brahma_ontology", "reference_doshas", "reference_yogas",
          "brahma_yoga_source_chunks"]
ATTR_DDL = """
ALTER TABLE public.brahma_dosha_catalog ADD COLUMN attribution_state text
    CONSTRAINT brahma_dosha_catalog_attribution_state_check CHECK (attribution_state IS NULL OR attribution_state IN ('sourced','unsourced','refuted'));
ALTER TABLE public.brahma_yoga_catalog ADD COLUMN attribution_state text
    CONSTRAINT brahma_yoga_catalog_attribution_state_check CHECK (attribution_state IS NULL OR attribution_state IN ('sourced','unsourced','refuted'));
"""
TOKEN = [{"text_id": "classical_tradition"}]
REAL = [{"text_id": "bphs", "chapter": 35}]


def _bindir(version: str) -> Path | None:
    for cand in (os.environ.get(f"PG{version}_BIN"), f"/opt/homebrew/opt/postgresql@{version}/bin",
                 f"/usr/local/opt/postgresql@{version}/bin", f"/usr/lib/postgresql/{version}/bin"):
        if cand and (Path(cand) / "initdb").exists():
            return Path(cand)
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Cluster:
    """Disposable cluster (unix socket only). Tables are owned by amjis_app; the writers run as `data_plane_builder`,
    a NOSUPERUSER NOINHERIT login role holding exactly SELECT/INSERT/UPDATE/DELETE on them (production ACL), with USAGE
    but no CREATE on schema public."""

    def __init__(self, version: str, bindir: Path):
        self.version, self.bindir = version, bindir
        self.data = tempfile.mkdtemp(prefix=f"attrpg{version}_")
        self.sock = tempfile.mkdtemp(prefix="p", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self._n = 0
        self.started = False

    def _run(self, exe: str, *args: str) -> None:
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=120, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self) -> None:
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        self._run("pg_ctl", "-D", self.data, "-o", f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                  "-c fsync=off -c max_connections=40 -c shared_buffers=16MB", "-w", "-t", "60", "-l", os.path.join(self.data, "server.log"), "start")
        self.started = True
        with self.connect("postgres", "postgres", autocommit=True) as c:
            c.execute("CREATE ROLE data_plane_schema_owner NOLOGIN NOINHERIT")
            c.execute("CREATE ROLE amjis_app LOGIN NOINHERIT NOSUPERUSER")
            c.execute("CREATE ROLE data_plane_builder LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB")

    def stop(self) -> None:
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db: str, user: str, autocommit: bool = False, dict_rows: bool = False) -> psycopg.Connection:
        return psycopg.connect(host=self.sock, port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10,
                               row_factory=dict_row if dict_rows else None)


@pytest.fixture(scope="module", params=VERSIONS)
def cluster(request):
    version = request.param
    bindir = _bindir(version)
    if bindir is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail(f"PostgreSQL {version} binaries not found and REQUIRE_PG_BINARIES=1")
        pytest.skip(f"PostgreSQL {version} binaries not found")
    cl = Cluster(version, bindir)
    try:
        cl.start()
        yield cl
    finally:
        cl.stop()


class Env:
    def __init__(self, cl: Cluster, with_column: bool = True):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
            c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
            c.execute("GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner")
            c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, data_plane_builder")
            c.execute(WRITERS_DDL)
            if with_column:
                c.execute(ATTR_DDL)
            for t in TABLES:
                c.execute(f"ALTER TABLE public.{t} OWNER TO amjis_app")
                c.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON public.{t} TO data_plane_builder")

    def admin(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "postgres", autocommit=True)

    def builder(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "data_plane_builder", dict_rows=True)  # the writers read dict rows

    def rows(self, sql: str, params=None) -> list[tuple]:
        with self.admin() as c:
            return c.execute(sql, params).fetchall()

    def run(self, sql: str, params=None) -> None:
        with self.admin() as c:
            c.execute(sql, params)

    def states(self, table: str) -> dict[str, str | None]:
        return dict(self.rows(f"SELECT canonical_id, attribution_state FROM public.{table}"))

    def drop(self) -> None:
        with self.cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001
        return exc


def _msg(exc) -> str:
    return "" if exc is None else str(exc).splitlines()[0]


def rebuild_doshas(env: Env) -> None:
    conn = env.builder()
    try:
        l0_doshas.seed_doshas(conn, autocommit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rebuild_yogas(env: Env) -> None:
    conn = env.builder()
    try:
        l0_yogas.seed_yogas(conn, autocommit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _no_corpus(monkeypatch):
    """bg_yogas also extracts yogas from classical_text_chunks; the fixture database has no corpus, so extraction is empty."""
    monkeypatch.setattr(l0_yogas, "extract_yogas_from_corpus", lambda _conn: [])


def _install(monkeypatch, mod):
    """The writers import the helper lazily at call time, so patching the helper module's functions reaches both."""
    monkeypatch.setattr(attr_module, "capture", mod.capture)
    monkeypatch.setattr(attr_module, "restore", mod.restore)


# --------------------------------------------------------------------------------------------- scenarios
def sc_rebuild_keeps_values(monkeypatch, cl: Cluster) -> list[str]:
    """The 1268 state (161 unsourced = 53 dosha + 1 yoga + ..., plus refuted/sourced styles) survives TWO rebuilds."""
    v: list[str] = []
    env = Env(cl)
    try:
        rebuild_doshas(env)
        rebuild_yogas(env)
        d0, y0 = env.states("brahma_dosha_catalog"), env.states("brahma_yoga_catalog")
        # first build in a database that already has the column: only the default rule applies
        if sum(1 for x in d0.values() if x == "unsourced") != 53 or sum(1 for x in y0.values() if x == "unsourced") != 1:
            v.append(f"default rule on a first build: dosha {collections.Counter(d0.values())}, yoga {collections.Counter(y0.values())}")
        # SS-style classifications that no writer derives (a later re-sourcing / refutation): set them directly
        dosha_ids = sorted(k for k, s in d0.items() if s is None)
        yoga_ids = sorted(k for k, s in y0.items() if s is None)
        env.run("UPDATE public.brahma_dosha_catalog SET attribution_state = 'refuted' WHERE canonical_id = ANY(%s)", (dosha_ids[:3],))
        env.run("UPDATE public.brahma_dosha_catalog SET attribution_state = 'sourced' WHERE canonical_id = ANY(%s)", (dosha_ids[3:5],))
        env.run("UPDATE public.brahma_yoga_catalog SET attribution_state = 'sourced' WHERE canonical_id = ANY(%s)", (yoga_ids[:7],))
        env.run("UPDATE public.brahma_yoga_catalog SET attribution_state = 'refuted' WHERE canonical_id = ANY(%s)", (yoga_ids[7:9],))
        # a placeholder row whose state was later changed by hand: the carried state must beat the default rule
        token_id = sorted(k for k, s in d0.items() if s == "unsourced")[0]
        env.run("UPDATE public.brahma_dosha_catalog SET attribution_state = 'refuted' WHERE canonical_id = %s", (token_id,))
        want_d, want_y = env.states("brahma_dosha_catalog"), env.states("brahma_yoga_catalog")
        for i in (1, 2):
            rebuild_doshas(env)
            rebuild_yogas(env)
            if env.states("brahma_dosha_catalog") != want_d:
                v.append(f"rebuild {i}: brahma_dosha_catalog states changed")
            if env.states("brahma_yoga_catalog") != want_y:
                v.append(f"rebuild {i}: brahma_yoga_catalog states changed")
        counts = (env.rows("SELECT count(*) FROM public.brahma_dosha_catalog")[0][0], env.rows("SELECT count(*) FROM public.reference_doshas")[0][0],
                  env.rows("SELECT count(*) FROM public.brahma_yoga_catalog")[0][0], env.rows("SELECT count(*) FROM public.reference_yogas")[0][0])
        if counts != (79, 79, 148, 148):
            v.append(f"projection counts after rebuilds: {counts}")
        return v
    finally:
        env.drop()


def sc_new_removed_recited(monkeypatch, cl: Cluster) -> list[str]:
    """A NEW entry gets the default rule; a REMOVED entry's value is dropped with its row (and not resurrected when it
    comes back); a RE-CITED entry's old state is dropped (it described the old citation)."""
    v: list[str] = []
    env = Env(cl)
    try:
        rebuild_doshas(env)
        base = list(l0_doshas.DOSHAS)
        victim, recited = base[0]["canonical_id"], base[1]["canonical_id"]
        env.run("UPDATE public.brahma_dosha_catalog SET attribution_state = 'sourced' WHERE canonical_id = ANY(%s)", ([victim, recited],))
        new_token = {**copy.deepcopy(base[2]), "canonical_id": "zz_new_token_dosha", "classical_citations": TOKEN}
        new_real = {**copy.deepcopy(base[2]), "canonical_id": "zz_new_real_dosha", "classical_citations": REAL}
        changed = {**copy.deepcopy(base[1]), "classical_citations": REAL if base[1].get("classical_citations") != REAL else TOKEN}
        # removed + new + re-cited in one rebuild
        monkeypatch.setattr(l0_doshas, "DOSHAS", [changed] + base[2:] + [new_token, new_real])
        rebuild_doshas(env)
        st = env.states("brahma_dosha_catalog")
        if victim in st:
            v.append("a removed entry's row survived the rebuild")
        if st.get("zz_new_token_dosha") != "unsourced":
            v.append(f"new placeholder entry should default to unsourced, got {st.get('zz_new_token_dosha')}")
        if st.get("zz_new_real_dosha") is not None:
            v.append(f"new entry with a real citation should stay NULL, got {st.get('zz_new_real_dosha')}")
        expect_recited = "unsourced" if changed["classical_citations"] == TOKEN else None
        if st.get(recited) != expect_recited:
            v.append(f"a re-cited entry kept a stale state: {st.get(recited)!r} (expected {expect_recited!r})")
        # the removed entry comes back later: it must NOT get its old 'sourced' value back
        monkeypatch.setattr(l0_doshas, "DOSHAS", base)
        rebuild_doshas(env)
        back = env.states("brahma_dosha_catalog").get(victim)
        expect_back = "unsourced" if base[0].get("classical_citations") == TOKEN else None
        if back != expect_back:
            v.append(f"a removed entry's old value was resurrected: {back!r} (expected {expect_back!r})")
        return v
    finally:
        env.drop()


def sc_yogas_new_removed(monkeypatch, cl: Cluster) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        rebuild_yogas(env)
        core = list(l0_yogas.YOGAS_CORE)
        victim = core[0]["canonical_id"]
        env.run("UPDATE public.brahma_yoga_catalog SET attribution_state = 'sourced' WHERE canonical_id = %s", (victim,))
        new_token = {**copy.deepcopy(core[1]), "canonical_id": "zz_new_token_yoga", "classical_citations": TOKEN}
        monkeypatch.setattr(l0_yogas, "YOGAS_CORE", core[1:] + [new_token])
        rebuild_yogas(env)
        st = env.states("brahma_yoga_catalog")
        if victim in st:
            v.append("a removed yoga's row survived")
        if st.get("zz_new_token_yoga") != "unsourced":
            v.append(f"new placeholder yoga should default to unsourced, got {st.get('zz_new_token_yoga')}")
        if st.get("kala_sarpa_yoga") != "unsourced":
            v.append("kala_sarpa_yoga lost its unsourced state")
        return v
    finally:
        env.drop()


def sc_column_absent(monkeypatch, cl: Cluster) -> list[str]:
    """A writer deployed before migration 1268: no column, no error, no column created, projections complete."""
    v: list[str] = []
    env = Env(cl, with_column=False)
    try:
        exc = _try(lambda: (rebuild_doshas(env), rebuild_yogas(env)))
        if exc is not None:
            return [f"writer fails when the column does not exist yet: {_msg(exc)}"]
        if env.rows("SELECT count(*) FROM information_schema.columns WHERE column_name = 'attribution_state'")[0][0] != 0:
            v.append("the writer created the column (only migration 1268 may)")
        return v
    finally:
        env.drop()


def sc_rolls_back_with_the_transaction(monkeypatch, cl: Cluster) -> list[str]:
    """The restore runs inside the orchestrator's transaction: a failed rebuild leaves the previous states untouched."""
    v: list[str] = []
    env = Env(cl)
    try:
        rebuild_doshas(env)
        want = env.states("brahma_dosha_catalog")
        broken = copy.deepcopy(list(l0_doshas.DOSHAS))
        broken.append(copy.deepcopy(broken[0]))  # duplicate canonical_id -> PK violation after the DELETE
        monkeypatch.setattr(l0_doshas, "DOSHAS", broken)
        if _try(lambda: rebuild_doshas(env)) is None:
            v.append("the broken rebuild did not fail")
        if env.states("brahma_dosha_catalog") != want:
            v.append("a failed rebuild changed the stored states (not atomic)")
        return v
    finally:
        env.drop()


SCENARIOS = [sc_rebuild_keeps_values, sc_new_removed_recited, sc_yogas_new_removed, sc_column_absent, sc_rolls_back_with_the_transaction]


def all_violations(monkeypatch, cl: Cluster) -> list[str]:
    out: list[str] = []
    for sc in SCENARIOS:
        try:
            out += [f"{sc.__name__}: {x}" for x in sc(monkeypatch, cl)]
        except Exception as exc:  # noqa: BLE001
            out.append(f"{sc.__name__}: scenario crashed: {_msg(exc)}")
    return out


def test_real_writers_keep_the_state(monkeypatch, cluster):
    assert all_violations(monkeypatch, cluster) == []


def test_without_the_change_a_rebuild_resets_the_state(monkeypatch, cluster):
    """Falsifier for the whole feature: with capture/restore neutered (what main does today) the same scenarios fail."""
    noop = types.SimpleNamespace(capture=lambda *a, **k: None, restore=lambda *a, **k: {})
    _install(monkeypatch, noop)
    viol = all_violations(monkeypatch, cluster)
    assert any("sc_rebuild_keeps_values" in x for x in viol), viol


# --------------------------------------------------------------------------------------------- mutants of the helper
HELPER_SRC = (Path(__file__).resolve().parents[1] / "brahmagyan" / "l0_attribution_state.py").read_text(encoding="utf-8")
MUTANTS = [
    ("restore never writes back", ("    if saved:\n", "    if False:\n"), None),
    ("citation not compared", ("AND t.{citation_col}::text = v.c", ""), None),
    ("key not compared (all rows get the first state)", ("WHERE t.{key_col} = v.k AND", "WHERE true AND"), None),
    ("default rule disabled", ("WHERE attribution_state IS NULL AND {citation_col} = %s::jsonb", "WHERE false AND {citation_col} = %s::jsonb"), None),
    ("default rule applied to every NULL row", ("WHERE attribution_state IS NULL AND {citation_col} = %s::jsonb", "WHERE attribution_state IS NULL AND {citation_col} <> %s::jsonb OR true"), None),
    ("default rule overwrites carried states", ("WHERE attribution_state IS NULL AND {citation_col} = %s::jsonb", "WHERE {citation_col} = %s::jsonb"), None),
    ("capture only keeps unsourced rows", ("FROM {table} WHERE attribution_state IS NOT NULL ORDER BY", "FROM {table} WHERE attribution_state = 'unsourced' ORDER BY"), None),
    ("capture reports the column absent", ("    if not has_attribution_column(cur, table):\n        return None\n", "    return None\n"), None),
    ("restore creates a missing column", ("    if saved is None:\n        return {", "    if saved is None:\n        cur.execute(f'ALTER TABLE {table} ADD COLUMN attribution_state text')\n        return {"), None),
]


def _helper_module(spec):
    src = HELPER_SRC if spec is None else mutate(HELPER_SRC, spec[0], spec[1])
    mod = types.ModuleType("mutant_attribution_state")
    exec(compile(src, "mutant_attribution_state.py", "exec"), mod.__dict__)
    return mod


def mutate(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, f"mutation anchor not unique/present: {old!r} x{src.count(old)}"
    return src.replace(old, new)


def test_helper_unmutated_matches_the_module(monkeypatch, cluster):
    _install(monkeypatch, _helper_module(None))
    assert all_violations(monkeypatch, cluster) == []


@pytest.mark.parametrize("name,spec,_x", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_every_mutant_is_killed(monkeypatch, cluster, name, spec, _x):
    _install(monkeypatch, _helper_module(spec))
    viol = all_violations(monkeypatch, cluster)
    assert viol != [], f"mutant survived: {name}"
    assert any("scenario crashed" not in x for x in viol), f"mutant only crashed the harness: {name}: {viol[:2]}"
    log = os.environ.get("MUTATION_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(f"PG{cluster.version} | {name} | KILLED by {len(viol)} violation(s); first: {viol[0][:160]}\n")


def test_integration_points_in_the_writers_are_mutation_checked(monkeypatch, cluster):
    """Removing the writer-side call (capture before the DELETE, or restore after the INSERTs) must be detected."""
    real_capture, real_restore = attr_module.capture, attr_module.restore
    monkeypatch.setattr(attr_module, "capture", lambda *a, **k: None)  # restore then sees 'column absent' and does nothing
    assert any("sc_rebuild_keeps_values" in x for x in all_violations(monkeypatch, cluster))
    monkeypatch.setattr(attr_module, "capture", real_capture)
    monkeypatch.setattr(attr_module, "restore", lambda *a, **k: {})
    assert any("sc_rebuild_keeps_values" in x for x in all_violations(monkeypatch, cluster))
    monkeypatch.setattr(attr_module, "restore", real_restore)  # (the unmutated pass is test_real_writers_keep_the_state)
