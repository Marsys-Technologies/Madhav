"""test_f3_msr_fk_drop.py -- F-3 (N-32): migration 1214 and the dangling-reference detector.

Three layers.
  1. STATIC (runs in CI, no DB): the migration is ALTER-only, IF EXISTS, lock_timeout, names exactly the
     five kala keys migration 403 created, the number is free, and it does not touch the admitted-context
     guard (assert_l2_msr_delete_safe in migration 1036 keeps its admitted-asset check).
  2. PURE (runs in CI): the detector's decision logic (classify / scan / regeneration effect / verdict).
  3. DB (skips without F3_DISPOSABLE_DATABASE_URL): the F3.PROOF on a disposable Postgres. The cascade is
     reproduced BEFORE the migration, the Kala rows are intact AFTER it, stable ids keep references valid,
     a changed or removed id is detected, and the guard still refuses an unadmitted MSR delete.

The DB layer CREATES and DROPS tables, roles and a function, so it refuses any URL that is not an explicit
loopback host:port with database exactly `f3_msr_fk_test`.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import msr_dangling_signal_refs as det  # noqa: E402

PLATFORM = HERE.parents[2]
MIG_DIRS = (PLATFORM / "supabase" / "migrations", PLATFORM / "migrations")
MIGRATION = PLATFORM / "supabase" / "migrations" / "1214_f3_drop_kala_msr_signal_fks.sql"
M403 = PLATFORM / "supabase" / "migrations" / "403_kala_signal_fk_cascade.sql"
M1036 = PLATFORM / "supabase" / "migrations" / "1036_data_plane_l2_producer_generations.sql"
M661 = PLATFORM / "migrations" / "661_l2_bodha_signal_identity.sql"

KALA = ("kala_activation", "kala_bhavishya", "kala_convergence", "kala_darshana", "kala_obstruction")
EXPECTED_FKS = {t: f"{t}_signal_id_fkey" for t in KALA}


def _statements(sql: str) -> list[str]:
    """Executable statements: comments stripped, split on semicolons, whitespace collapsed."""
    no_comments = "\n".join(re.sub(r"--.*$", "", line) for line in sql.splitlines())
    return [re.sub(r"\s+", " ", s).strip() for s in no_comments.split(";") if s.strip()]


# --------------------------------------------------------------------------- static

def test_migration_is_alter_only_with_lock_timeout_and_nothing_else():
    stmts = _statements(MIGRATION.read_text())
    assert stmts[0] == "SET LOCAL lock_timeout = '5s'"
    alters = stmts[1:]
    assert len(alters) == 5
    for s in alters:
        assert re.fullmatch(r"ALTER TABLE (kala_\w+) DROP CONSTRAINT IF EXISTS (kala_\w+_signal_id_fkey)", s), s
    assert {(m.group(1), m.group(2)) for s in alters
            for m in [re.fullmatch(r"ALTER TABLE (\w+) DROP CONSTRAINT IF EXISTS (\w+)", s)]} == \
        set(EXPECTED_FKS.items())


def test_migration_names_exactly_the_keys_migration_403_created():
    created = set(re.findall(r"ADD\s+CONSTRAINT\s+(kala_\w+_signal_id_fkey)", M403.read_text()))
    assert created == set(EXPECTED_FKS.values())


def test_migration_number_is_unique_across_both_directories():
    hits = [p.name for d in MIG_DIRS if d.is_dir() for p in d.glob("1214_*.sql")]
    assert hits == [MIGRATION.name]


def test_migration_does_not_touch_the_admitted_context_guard_or_l2_owned_tables():
    body = " ".join(_statements(MIGRATION.read_text()))
    for forbidden in ("assert_l2_msr_delete_safe", "bodha_contradictions", "bodha_signal_embeddings",
                      "bodha_msr_signals", "GRANT", "REVOKE", "CREATE", "DELETE", "UPDATE", "INSERT",
                      "DROP TABLE", "TRUNCATE", "ADD CONSTRAINT", "OWNER"):
        assert forbidden not in body, forbidden


def test_guard_in_migration_1036_still_keeps_its_admitted_context_branch():
    src = M1036.read_text()
    guard = src.split("CREATE OR REPLACE FUNCTION public.assert_l2_msr_delete_safe", 1)[1] \
        .split("CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs", 1)[0]
    assert "session_user <> 'data_plane_builder'" in guard
    assert "outside admitted asset context" in guard
    assert "FOR UPDATE" in guard


def test_detector_fk_dropped_tier_equals_the_dropped_keys():
    assert {s.table for s in det.REF_SITES if s.tier == det.FK_DROPPED} == set(KALA)
    assert all(s.column == "signal_id" for s in det.REF_SITES if s.tier == det.FK_DROPPED)


# --------------------------------------------------------------------------- pure detector

def test_classify_reference_each_outcome():
    idx = {"a": "c1", "b": "c2"}
    assert det.classify_reference(None, "c1", idx) == "null_ref"
    assert det.classify_reference("a", "c1", idx) == "ok"
    assert det.classify_reference("zz", "c1", idx) == "dangling"
    assert det.classify_reference("b", "c1", idx) == "cross_chart"


def test_scan_ignores_null_refs_and_counts_per_chart():
    idx = {"a": "c1", "b": "c1"}
    site = det.REF_SITES[0]
    res = det.scan_references(site, [("a", "c1"), (None, "c1"), ("x", "c1"), ("b", "c2")], idx)
    by = {r.chart_id: r for r in res}
    assert (by["c1"].referencing, by["c1"].dangling, by["c1"].cross_chart) == (2, 1, 0)
    assert (by["c2"].referencing, by["c2"].dangling, by["c2"].cross_chart) == (1, 0, 1)


def test_regeneration_effect_keeps_stable_ids_and_orphans_removed_ones():
    eff = det.regeneration_effect({"a", "b", "c"}, {"a", "b", "d"}, ["a", "a", "c", "c", "c"])
    assert (eff.kept, eff.disappeared, eff.new, eff.orphaned_refs) == (2, 1, 1, 3)
    same = det.regeneration_effect({"a", "b"}, {"a", "b"}, ["a", "b"])
    assert (same.disappeared, same.orphaned_refs) == (0, 0)


def test_failing_results_tiering_and_vacuity():
    mk = lambda tier, d: det.SiteResult("t", "c", tier, "c1", 5, d, 0)  # noqa: E731
    assert det.failing_results([mk(det.FK_DROPPED, 1)], strict=False)
    assert not det.failing_results([mk(det.UNCONSTRAINED, 9)], strict=False)
    assert det.failing_results([mk(det.UNCONSTRAINED, 9)], strict=True)
    assert not det.failing_results([mk(det.FK_DROPPED, 0)], strict=True)


def test_sql_builders_filter_null_refs_and_only_accept_declared_sites():
    for site in det.REF_SITES:
        sql = det.dangling_sql(site, chart_scoped=True)
        assert f"k.{site.column} IS NOT NULL" in sql and "LEFT JOIN bodha_msr_signals" in sql
        assert "k.chart_id = %s" in sql
        assert "k.chart_id = %s" not in det.dangling_sql(site, chart_scoped=False)
    with pytest.raises(ValueError):
        det.dangling_sql(det.RefSite("kala_x; DROP TABLE y", "signal_id", det.FK_DROPPED), chart_scoped=False)
    with pytest.raises(ValueError):
        det.would_orphan_sql(det.RefSite("kala_activation", "chart_id", det.FK_DROPPED))


def test_main_exit_codes_failing_unreadable_clean_and_vacuous(monkeypatch, capsys):
    site = det.REF_SITES[1]  # kala_activation
    ok = det.SiteResult(site.table, site.column, det.FK_DROPPED, "c1", 3, 0, 0)
    bad = det.SiteResult(site.table, site.column, det.FK_DROPPED, "c1", 3, 1, 0)
    unat = det.SiteResult(site.table, site.column, det.FK_DROPPED, "c1", 3, 0, 0, 1)
    scanned = [site]
    err = ["t.c: InsufficientPrivilege"]
    cases = [  # (results, unreadable, scanned, argv, exit)
        ([ok], [], scanned, [], 0), ([bad], [], scanned, [], 1), ([unat], [], scanned, [], 1),
        ([ok], err, scanned, [], 2), ([bad], err, scanned, [], 1),
        ([], [], scanned, [], 3), ([], [], scanned, ["--require-nonvacuous"], 1),
        ([], [], scanned, ["--allow-vacuous"], 0), ([ok], [], scanned, ["--require-nonvacuous"], 0),
        # PER SITE: one populated site must not vouch for an empty one
        ([ok], [], scanned + [det.REF_SITES[0]], [], 3),
        ([ok], [], scanned + [det.REF_SITES[0]], ["--require-nonvacuous"], 1),
    ]
    for results, unreadable, sc, argv, code in cases:
        monkeypatch.setattr(det, "_scan_live", lambda *_a, _r=(results, unreadable, sc), **_k: _r)
        assert det.main(argv) == code, (results, unreadable, argv)
        out = capsys.readouterr().out
        assert ("VACUOUS" in out) == bool(det.vacuous_sites(results, sc)), out
    monkeypatch.setattr(det, "_scan_live", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("no db")))
    assert det.main([]) == 2


def test_unknown_tier_is_an_error_not_an_empty_scan(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(det, "_scan_live", lambda *a, **k: called.append(a) or ([], [], []))
    for bad in ("bogus", "", "fk_dropped,bogus", "fk_dropped,,l2_internal"):
        assert det.main(["--tiers", bad]) == 2, bad
    assert called == []                                   # refused before any scan
    assert det.parse_tiers(None) is None and det.parse_tiers("fk_dropped, l2_internal") == ("fk_dropped", "l2_internal")


def test_vacuity_is_judged_per_site_and_unattributable_rows_are_reported():
    a, b = det.REF_SITES[0], det.REF_SITES[1]
    res = [det.SiteResult(a.table, a.column, a.tier, "c1", 4, 0, 0)]
    assert det.vacuous_sites(res, [a, b]) == [b]
    assert det.vacuous_sites(res, [a]) == []
    assert det.vacuous_sites([det.SiteResult(a.table, a.column, a.tier, "c1", 0, 0, 0)], [a]) == [a]
    idx = {"s1": "c1"}
    assert det.classify_reference("s1", None, idx) == "unattributable"
    assert det.classify_reference("gone", None, idx) == "dangling"
    r = det.scan_references(a, [("s1", None), ("s1", "c1")], idx)
    by = {x.chart_id: x for x in r}
    assert by[det.NULL_CHART].unattributable == 1 and by[det.NULL_CHART].broken == 1 and by["c1"].broken == 0
    assert "IS DISTINCT FROM" in det.dangling_sql(a, chart_scoped=False)
    assert "k.chart_id IS NULL AND s.chart_id = %s" in det.dangling_sql(a, chart_scoped=True)


def test_detector_self_test_passes():
    assert det._run_self_test() == 0


# --------------------------------------------------------------------------- DB layer (F3.PROOF)

DISPOSABLE_DB = "f3_msr_fk_test"
URL_ENV = "F3_DISPOSABLE_DATABASE_URL"


def validate_disposable_url(url: str) -> str:
    """Refuse anything that is not an explicit loopback host:port with database exactly f3_msr_fk_test."""
    u = urlsplit(url)
    if u.scheme not in ("postgres", "postgresql") or u.fragment:
        raise ValueError("scheme/fragment")
    if (u.hostname or "") not in ("localhost", "127.0.0.1", "::1") or u.port is None:
        raise ValueError("host must be explicit loopback with explicit port")
    if u.path != "/" + DISPOSABLE_DB:
        raise ValueError(f"database must be exactly {DISPOSABLE_DB}")
    if not set(re.findall(r"([^=&?]+)=", u.query)) <= {"application_name", "sslmode"}:
        raise ValueError("query option not allowed")
    return url


def test_disposable_url_validator_refuses_everything_but_the_throwaway():
    ok = f"postgresql://postgres@127.0.0.1:54329/{DISPOSABLE_DB}"
    assert validate_disposable_url(ok) == ok
    for bad in (f"postgresql://postgres@10.0.0.5:5432/{DISPOSABLE_DB}",
                f"postgresql://postgres@localhost/{DISPOSABLE_DB}",
                "postgresql://postgres@localhost:5432/postgres",
                f"postgresql://postgres@localhost:5432/{DISPOSABLE_DB}?host=prod.example",
                f"postgresql://postgres@localhost:5432//{DISPOSABLE_DB}",
                f"mysql://postgres@localhost:5432/{DISPOSABLE_DB}"):
        with pytest.raises(ValueError):
            validate_disposable_url(bad)


CHART, CHART2 = "10000000-0000-0000-0000-0000000000c1", "10000000-0000-0000-0000-0000000000c2"
ADMIT = dict(asset="bo_laksana", gen="gen1", part="part1", build="build1")

# Mutants of the guard function body (applied only when F3_GUARD_MUTANT=<index>); each must be killed.
GUARD_MUTANTS = [
    ("session_user <> 'data_plane_builder'", "false"),
    ("IS DISTINCT FROM p_chart_id::text", "IS NOT DISTINCT FROM p_chart_id::text"),
    ("AND g.state='building'", "AND g.state<>'building'"),
    ("AND i.build_id=v_build", "AND true"),
    ("AND i.partition_key=v_partition", "AND true"),
    ("RAISE EXCEPTION 'L2 MSR delete authorization is outside admitted asset context'",
     "RAISE NOTICE 'L2 MSR delete authorization is outside admitted asset context'"),
    ("IF v_exists THEN", "IF false THEN"),
    ("AND i.generation_id=v_generation", "AND true"),
]


def test_every_guard_mutant_applies_to_the_real_guard_source():
    guard = _guard_sql()
    for old, _new in GUARD_MUTANTS:
        assert guard.count(old) >= 1, old


def _guard_sql() -> str:
    src = M1036.read_text()
    start = src.index("CREATE OR REPLACE FUNCTION public.assert_l2_msr_delete_safe(")
    return src[start:src.index("CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs", start)]


def _identity_sql() -> str:
    src = M661.read_text()
    start = src.index("CREATE OR REPLACE FUNCTION bodha_signal_identity_namespace()")
    return src[start:src.index("COMMENT ON FUNCTION bodha_signal_identity(uuid", start)]


_TABLES_DDL = """
DROP TABLE IF EXISTS kala_activation, kala_bhavishya, kala_convergence, kala_darshana, kala_obstruction,
  bodha_contradictions, bodha_signal_embeddings, bodha_msr_signals,
  l2_data_plane_run_intents, data_plane_l2_producer_generations CASCADE;
DROP FUNCTION IF EXISTS public.assert_l2_msr_delete_safe(uuid, text[], text[], text[]);
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='amjis_app') THEN CREATE ROLE amjis_app LOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_l2_owner') THEN CREATE ROLE data_plane_l2_owner; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_builder') THEN CREATE ROLE data_plane_builder LOGIN; END IF;
END $$;
CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
  signal_type_id text NOT NULL, signal_type_class text NOT NULL, varga_id text,
  configuration_jsonb jsonb NOT NULL DEFAULT '{}', producer_asset_id text NOT NULL);
CREATE TABLE bodha_contradictions (id serial PRIMARY KEY, chart_id uuid NOT NULL,
  signal_a_id uuid NOT NULL REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE,
  signal_b_id uuid NOT NULL REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE);
CREATE TABLE bodha_signal_embeddings (id serial PRIMARY KEY, chart_id uuid NOT NULL,
  signal_id uuid NOT NULL REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE);
CREATE TABLE l2_data_plane_run_intents (chart_id uuid, asset_id text, generation_id text, partition_key text, build_id text);
CREATE TABLE data_plane_l2_producer_generations (chart_id uuid, asset_id text, generation_id text, state text);
ALTER TABLE bodha_msr_signals OWNER TO data_plane_l2_owner;
ALTER TABLE bodha_contradictions OWNER TO data_plane_l2_owner;
ALTER TABLE bodha_signal_embeddings OWNER TO data_plane_l2_owner;
GRANT ALL ON bodha_msr_signals TO data_plane_builder;
"""


def _kala_ddl() -> str:
    parts = []
    for t in KALA:
        notnull = "NOT NULL" if t == "kala_activation" else ""
        parts.append(f"CREATE TABLE {t} (id serial PRIMARY KEY, chart_id uuid NOT NULL, signal_id uuid {notnull} "
                     f"REFERENCES bodha_msr_signals(signal_id) ON DELETE CASCADE); "
                     f"ALTER TABLE {t} OWNER TO amjis_app;")
    return "\n".join(parts)


SPECS = [  # (signal_type_id, varga_id, configuration)
    ("yoga:a", None, {"fact_key": "k1", "v": 1}),
    ("yoga:b", "D9", {"fact_key": "k2", "v": 2}),
    ("yoga:c", "D10", {"fact_key": "k3", "v": 3}),
    ("dasha:d", None, {"fact_key": "k4", "v": 4}),
]


def _insert_signals(conn, chart, specs, producer="bo_laksana"):
    for t, v, cfg in specs:
        conn.execute(
            "INSERT INTO bodha_msr_signals (signal_id, chart_id, ayanamsha_id, signal_type_id, signal_type_class, "
            "varga_id, configuration_jsonb, producer_asset_id) VALUES "
            "(bodha_signal_identity(%s::uuid,'lahiri',%s,%s,%s::jsonb), %s::uuid,'lahiri',%s,'class',%s,%s::jsonb,%s)",
            [chart, t, v, json.dumps(cfg), chart, t, v, json.dumps(cfg), producer])


def _ids(conn, chart) -> dict[str, str]:
    return {r[0]: str(r[1]) for r in conn.execute(
        "SELECT signal_type_id, signal_id FROM bodha_msr_signals WHERE chart_id=%s::uuid", [chart]).fetchall()}


def _seed(conn):
    """Signals for two charts, and one referencing row per signal in every dependent table."""
    _insert_signals(conn, CHART, SPECS)
    _insert_signals(conn, CHART2, SPECS)
    for chart in (CHART, CHART2):
        for sid in _ids(conn, chart).values():
            for t in KALA:
                conn.execute(f"INSERT INTO {t} (chart_id, signal_id) VALUES (%s::uuid, %s::uuid)", [chart, sid])
            conn.execute("INSERT INTO bodha_signal_embeddings (chart_id, signal_id) VALUES (%s::uuid,%s::uuid)", [chart, sid])
    ids = list(_ids(conn, CHART).values())
    conn.execute("INSERT INTO bodha_contradictions (chart_id, signal_a_id, signal_b_id) VALUES (%s::uuid,%s::uuid,%s::uuid)",
                 [CHART, ids[0], ids[1]])


def _counts(conn, chart) -> dict[str, int]:
    return {t: conn.execute(f"SELECT count(*) FROM {t} WHERE chart_id=%s::uuid", [chart]).fetchone()[0]
            for t in (*KALA, "bodha_signal_embeddings", "bodha_contradictions")}


def _fk_names(conn) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT conname FROM pg_constraint WHERE contype='f' AND confrelid='public.bodha_msr_signals'::regclass")}


# ------- DB fixtures and the proof scenarios

_PROOF: list[str] = []


def _log(msg: str) -> None:
    _PROOF.append(msg)
    print("[F3.PROOF]", msg)


@pytest.fixture(scope="module", autouse=True)
def _write_proof_log():
    yield
    out = os.environ.get("F3_PROOF_OUT")
    if out and _PROOF:
        Path(out).write_text("\n".join(_PROOF) + "\n")


def _url() -> str:
    raw = os.environ.get(URL_ENV)
    if not raw:
        pytest.skip(f"{URL_ENV} not supplied (disposable Postgres proof)")
    return validate_disposable_url(raw)


@pytest.fixture
def make_db():
    psycopg = pytest.importorskip("psycopg")
    url = _url()
    conns: list = []

    def build(*, apply_migration: bool):
        admin = psycopg.connect(url, autocommit=True)
        conns.append(admin)
        admin.execute(_TABLES_DDL)
        admin.execute(_kala_ddl())
        admin.execute(_identity_sql())
        guard = _guard_sql()
        idx = os.environ.get("F3_GUARD_MUTANT")
        if idx is not None:
            old, new = GUARD_MUTANTS[int(idx)]
            assert old in guard
            guard = guard.replace(old, new, 1)
        admin.execute(guard)
        admin.execute("INSERT INTO l2_data_plane_run_intents VALUES (%s::uuid,%s,%s,%s,%s)",
                      [CHART, ADMIT["asset"], ADMIT["gen"], ADMIT["part"], ADMIT["build"]])
        admin.execute("INSERT INTO data_plane_l2_producer_generations VALUES (%s::uuid,%s,%s,'building')",
                      [CHART, ADMIT["asset"], ADMIT["gen"]])
        _seed(admin)
        if apply_migration:
            apply_1214(url)
        return admin

    def builder_session(**override):
        """A data_plane_builder session carrying the admitted-asset context (override fields to break it)."""
        c = psycopg.connect(url)
        conns.append(c)
        c.execute("SET SESSION AUTHORIZATION data_plane_builder")
        ctx = {**ADMIT, "chart": CHART, **override}
        for k, v in (("asset_id", ctx["asset"]), ("generation_id", ctx["gen"]), ("partition_key", ctx["part"]),
                     ("build_id", ctx["build"]), ("chart_id", ctx["chart"])):
            c.execute("SELECT set_config(%s, %s, false)", [f"madhav.l2_{k}", v])
        return c

    build.builder = builder_session
    yield build
    for c in conns:
        try:
            c.close()
        except Exception:
            pass


def apply_1214(url: str) -> None:
    """Apply the migration exactly as the runner does: one transaction, as the owner of the kala tables."""
    import psycopg
    with psycopg.connect(url) as c:
        c.execute("SET ROLE amjis_app")
        c.execute(MIGRATION.read_text())
        c.commit()


def _regenerate(conn, specs, chart=CHART):
    conn.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [chart])
    conn.execute("DELETE FROM bodha_msr_signals WHERE chart_id=%s::uuid AND producer_asset_id='bo_laksana'", [chart])
    _insert_signals(conn, chart, specs)


def _dangling(conn, chart, tiers=(det.FK_DROPPED,)):
    res = []
    for site in det.REF_SITES:
        if site.tier in tiers:
            for cid, ref, dang, cross, unat in conn.execute(
                    det.dangling_sql(site, chart_scoped=True), [chart, chart]).fetchall():
                res.append(det.SiteResult(site.table, site.column, site.tier, str(cid), ref, dang, cross, unat))
    return res


def test_db_before_migration_the_cascade_deletes_kala_rows(make_db):
    import psycopg
    admin = make_db(apply_migration=False)
    before = _counts(admin, CHART)
    assert all(before[t] == 4 for t in KALA)
    assert _fk_names(admin) >= set(EXPECTED_FKS.values())
    admin.execute("DELETE FROM bodha_msr_signals WHERE chart_id=%s::uuid", [CHART])  # the historic unguarded replacement
    after = _counts(admin, CHART)
    _log(f"BEFORE migration, unguarded MSR replace: kala rows chart C {before} -> {after}")
    assert all(after[t] == 0 for t in KALA)                      # bug reproduced: five Kala tables erased
    assert _counts(admin, CHART2)["kala_convergence"] == 4        # other chart untouched
    # the guard added later (migration 1036) turns the silent erase into a refusal while the keys exist
    admin.execute(f"INSERT INTO l2_data_plane_run_intents VALUES ('{CHART2}','bo_laksana','gen1','part1','build1')")
    admin.execute(f"INSERT INTO data_plane_l2_producer_generations VALUES ('{CHART2}','bo_laksana','gen1','building')")
    b = make_db.builder(chart=CHART2)
    with pytest.raises(psycopg.errors.RaiseException, match="cross-layer dependent"):
        b.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART2])
    _log("BEFORE migration, admitted guard with FKs present: REFUSES (cross-layer dependent rows)")


def test_db_after_migration_regeneration_leaves_kala_rows_intact_and_ids_stable(make_db):
    admin = make_db(apply_migration=True)
    names = _fk_names(admin)
    assert not names & set(EXPECTED_FKS.values())
    assert names == {"bodha_contradictions_signal_a_id_fkey", "bodha_contradictions_signal_b_id_fkey",
                     "bodha_signal_embeddings_signal_id_fkey"}   # owner-path keys untouched
    before_ids, before, c2_before = _ids(admin, CHART), _counts(admin, CHART), _counts(admin, CHART2)
    b = make_db.builder()
    _regenerate(b, SPECS)                                         # guard passes: no refusal
    b.commit()
    after = _counts(admin, CHART)
    _log(f"AFTER migration, admitted regenerate (same logic): counts {before} -> {after}; ids stable={_ids(admin, CHART) == before_ids}")
    assert _ids(admin, CHART) == before_ids                       # deterministic ids: same signals, same ids
    assert all(after[t] == before[t] for t in KALA)               # Kala rows intact
    assert _counts(admin, CHART2) == c2_before                     # other chart untouched
    assert not det.failing_results(_dangling(admin, CHART), strict=False)
    assert sum(r.referencing for r in _dangling(admin, CHART)) == 20   # non-vacuous: 4 refs x 5 tables
    _log("AFTER migration: detector fk_dropped sites referencing=20 dangling=0 cross_chart=0")


def test_db_changed_and_removed_signals_are_detected_and_downstream_rebuild_restores(make_db):
    admin = make_db(apply_migration=True)
    old = _ids(admin, CHART)
    referenced = [r[0] for t in KALA for r in admin.execute(f"SELECT signal_id::text FROM {t} WHERE chart_id=%s::uuid", [CHART])]
    changed = [(t, v, {**c, "v": 99}) if t == "yoga:b" else (t, v, c) for t, v, c in SPECS]   # yoga:b changes identity
    changed = [x for x in changed if x[0] != "dasha:d"]                                         # dasha:d disappears
    impact = sum(admin.execute(det.would_orphan_sql(s), [CHART, "bo_laksana", None, None, None, None, None, None]).fetchone()[0]
                 for s in det.REF_SITES if s.tier == det.FK_DROPPED)
    b = make_db.builder()
    _regenerate(b, changed)
    b.commit()
    new = _ids(admin, CHART)
    eff = det.regeneration_effect(set(old.values()), set(new.values()), referenced)
    found = _dangling(admin, CHART)
    broken = sum(r.dangling for r in found)
    _log(f"changed+removed: kept={eff.kept} disappeared={eff.disappeared} new={eff.new} predicted_orphans={eff.orphaned_refs} "
         f"detected_dangling={broken} pre-delete would_orphan(upper bound)={impact}")
    assert eff.disappeared == 2 and eff.kept == 2 and eff.new == 1
    assert new["yoga:a"] == old["yoga:a"] and new["yoga:b"] != old["yoga:b"]
    assert broken == eff.orphaned_refs == 10                       # 2 lost ids x 5 tables, found exactly
    assert det.failing_results(found, strict=False) and impact >= broken
    # downstream rebuild in its wave re-points the rows; the detector goes clean
    for t in KALA:
        for tid in ("yoga:b", "dasha:d"):
            admin.execute(f"DELETE FROM {t} WHERE signal_id = %s::uuid", [old[tid]])
        admin.execute(f"INSERT INTO {t} (chart_id, signal_id) VALUES (%s::uuid, %s::uuid)", [CHART, new["yoga:b"]])
    assert not det.failing_results(_dangling(admin, CHART), strict=False)
    _log("downstream rebuild (re-point to new ids): detector clean")
    # a reference into ANOTHER chart's signal is also flagged
    other = next(iter(_ids(admin, CHART2).values()))
    admin.execute("INSERT INTO kala_darshana (chart_id, signal_id) VALUES (%s::uuid, %s::uuid)", [CHART, other])
    assert sum(r.cross_chart for r in _dangling(admin, CHART)) == 1
    _log("cross-chart reference detected: 1")


def test_db_guard_still_refuses_unadmitted_delete_before_and_after_migration(make_db):
    import psycopg
    for applied in (False, True):
        admin = make_db(apply_migration=applied)
        # (a) no admitted context at all (superuser session)
        with pytest.raises(psycopg.errors.RaiseException, match="outside admitted asset context"):
            admin.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
        # (b) complete admitted context but the session is not data_plane_builder
        for k, v in (("asset_id", "bo_laksana"), ("generation_id", "gen1"), ("partition_key", "part1"),
                     ("build_id", "build1"), ("chart_id", CHART)):
            admin.execute("SELECT set_config(%s,%s,false)", [f"madhav.l2_{k}", v])
        with pytest.raises(psycopg.errors.RaiseException, match="outside admitted asset context"):
            admin.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
        # (c)-(g) builder with one wrong admission field each
        for bad in ({"chart": CHART2}, {"build": "other"}, {"part": "other"}, {"gen": "other"}, {"asset": "bo_arudha"}):
            b = make_db.builder(**bad)
            with pytest.raises(psycopg.errors.RaiseException, match="outside admitted asset context"):
                b.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
            b.rollback()
        # (h) generation no longer 'building'
        admin.execute("UPDATE data_plane_l2_producer_generations SET state='complete'")
        b = make_db.builder()
        with pytest.raises(psycopg.errors.RaiseException, match="outside admitted asset context"):
            b.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
        b.rollback()
        admin.execute("UPDATE data_plane_l2_producer_generations SET state='building'")
        # (i) fully admitted passes (after the migration; before it, the FKs make it refuse on dependants instead)
        b = make_db.builder()
        if applied:
            b.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
        else:
            with pytest.raises(psycopg.errors.RaiseException, match="cross-layer dependent"):
                b.execute("SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)", [CHART])
        _log(f"guard (migration applied={applied}): unadmitted/wrong-context refused x8; admitted "
             f"{'passes' if applied else 'refuses on FK dependants'}")


def test_db_migration_is_idempotent_and_owner_path_keys_need_their_owner(make_db):
    import psycopg
    url = _url()
    admin = make_db(apply_migration=True)
    apply_1214(url)                                                # second application: no error, no change
    assert not _fk_names(admin) & set(EXPECTED_FKS.values())
    with psycopg.connect(url) as c:
        c.execute("SET ROLE amjis_app")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("ALTER TABLE bodha_signal_embeddings DROP CONSTRAINT IF EXISTS bodha_signal_embeddings_signal_id_fkey")
    _log("migration idempotent; amjis_app cannot drop the data_plane_l2_owner-owned keys (owner-path)")


def test_db_blocked_migration_fails_loudly_within_lock_timeout_and_changes_nothing(make_db):
    import psycopg
    import time
    url = _url()
    admin = make_db(apply_migration=False)
    with psycopg.connect(url) as holder:
        holder.execute("SELECT count(*) FROM bodha_msr_signals")          # ACCESS SHARE held until rollback
        t0 = time.monotonic()
        with pytest.raises(psycopg.errors.LockNotAvailable):
            apply_1214(url)
        waited = time.monotonic() - t0
        holder.rollback()
    _log(f"blocked migration (reader holds bodha_msr_signals): LockNotAvailable after {waited:.1f}s; keys all still present")
    assert 4.5 < waited < 9
    assert _fk_names(admin) >= set(EXPECTED_FKS.values())


def test_db_null_chart_row_vacuous_site_and_deleted_row_limits(make_db):
    admin = make_db(apply_migration=True)
    # NULL chart_id referencing a live signal of the chart: reported unattributable (scoped and global)
    admin.execute("ALTER TABLE kala_darshana ALTER COLUMN chart_id DROP NOT NULL")
    sid = next(iter(_ids(admin, CHART).values()))
    admin.execute("INSERT INTO kala_darshana (chart_id, signal_id) VALUES (NULL, %s::uuid)", [sid])
    scoped = [r for r in _dangling(admin, CHART) if r.table == "kala_darshana"]
    assert sum(r.unattributable for r in scoped) == 1 and det.failing_results(scoped, strict=False)
    site = next(s for s in det.REF_SITES if s.table == "kala_darshana")
    glob = admin.execute(det.dangling_sql(site, chart_scoped=False)).fetchall()
    assert [(g[0], g[4]) for g in glob if g[0] is None] == [(None, 1)]
    admin.execute("DELETE FROM kala_darshana WHERE chart_id IS NULL")
    # a site with zero referencing rows is vacuous even though other sites are populated
    admin.execute("DELETE FROM kala_bhavishya")
    res = _dangling(admin, CHART)
    assert [v.table for v in det.vacuous_sites(res, [s for s in det.REF_SITES if s.tier == det.FK_DROPPED])] == ["kala_bhavishya"]
    # a DELETED referencing row leaves no trace in the table: the detector cannot see it (that is PF-2)
    admin.execute("DELETE FROM kala_activation WHERE id = (SELECT min(id) FROM kala_activation WHERE chart_id=%s::uuid)", [CHART])
    ka = [r for r in _dangling(admin, CHART) if r.table == "kala_activation"]
    assert ka[0].referencing == 3 and ka[0].broken == 0
    _log("detector: NULL-chart row unattributable; per-site vacuity; a deleted row is invisible (needs PF-2 before-state counts)")


# ---- PREREQUISITE for the owner-path drop of the three L2 keys (reviewer caveat; F3 doc section 5) ----------

sys.path.insert(0, str(PLATFORM / "python-sidecar"))


class _PlainConn:
    """Not a psycopg-module object, so _assert_msr_delete_safe is skipped: this isolates the CHILD-DELETE SCOPE."""

    def __init__(self, c):
        self._c = c

    def execute(self, sql, params=None):
        return self._c.execute(sql, params)


def _l2_dangling(conn, chart) -> int:
    return conn.execute(
        "SELECT (SELECT count(*) FROM bodha_signal_embeddings e LEFT JOIN bodha_msr_signals s USING (signal_id) "
        " WHERE e.chart_id=%s::uuid AND s.signal_id IS NULL) + "
        "(SELECT count(*) FROM bodha_contradictions c LEFT JOIN bodha_msr_signals a ON a.signal_id=c.signal_a_id "
        " WHERE c.chart_id=%s::uuid AND a.signal_id IS NULL)", [chart, chart]).fetchone()[0]


@pytest.mark.parametrize("keys_dropped,snapshot,expected_dangling", [
    (False, "empty", 0),      # today: the FK cascade removes the L2 children
    (True, "empty", 5),       # keys dropped, snapshot empty (an L1-only vector, as bo_laksana binds): children DANGLE
    (True, "live", 0),        # keys dropped, snapshot == live delete scope: explicit child deletes suffice
])
def test_db_l2_key_drop_is_safe_only_if_the_child_delete_snapshot_equals_the_live_scope(
        make_db, keys_dropped, snapshot, expected_dangling):
    from bodha_writers._idempotency import replace_prior_msr_signals
    url = _url()
    admin = make_db(apply_migration=True)
    if keys_dropped:   # emulate the owner-path drop (as superuser on the disposable DB)
        admin.execute("ALTER TABLE bodha_contradictions DROP CONSTRAINT bodha_contradictions_signal_a_id_fkey, "
                      "DROP CONSTRAINT bodha_contradictions_signal_b_id_fkey")
        admin.execute("ALTER TABLE bodha_signal_embeddings DROP CONSTRAINT bodha_signal_embeddings_signal_id_fkey")
    import psycopg
    with psycopg.connect(url) as c:
        # the writer's `pg_temp.bodha_msr_signals` is the bound-input snapshot (bind_l2_exact_inputs), not the live table
        if snapshot == "empty":
            c.execute("CREATE TEMP TABLE bodha_msr_signals ON COMMIT DROP AS SELECT * FROM public.bodha_msr_signals WHERE false")
        else:
            c.execute("CREATE TEMP TABLE bodha_msr_signals ON COMMIT DROP AS SELECT * FROM public.bodha_msr_signals")
        rows = [{"chart_id": CHART, "ayanamsha_id": "lahiri", "signal_type_id": t} for t, _v, _c in SPECS]
        replace_prior_msr_signals(_PlainConn(c), rows)
        c.commit()
    d = _l2_dangling(admin, CHART)
    _log(f"L2-key prerequisite (keys_dropped={keys_dropped}, snapshot={snapshot}): dangling L2 children after MSR delete = {d}")
    assert d == expected_dangling
