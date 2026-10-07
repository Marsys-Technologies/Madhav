"""_formgap_support.py: the shared fixtures of the FORM-GAP tests (SS N-191 / N-192, 2026-10-07): the real DDL of the migrations on a DISPOSABLE PostgreSQL, a measure() stand-in that runs the engine's own
`_measure_prose` (catalog read, writer scope, closure SQL, form reads, `prose_checks`) on it, and the two-chart helper. Offline apart from the throw-away loopback cluster (deleted at exit)."""
from __future__ import annotations

import copy
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import point_psql_at  # noqa: E402

REPO = HERE.parents[3]
MIG = REPO / "platform" / "migrations"
SMIG = REPO / "platform" / "supabase" / "migrations"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"          # the measured (canonical) chart
CHART_B = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"          # another chart (never the dead phantom)
RUN_1 = "11111111-1111-4111-8111-111111111111"
RUN_2 = "22222222-2222-4222-8222-222222222222"
NA, FAIL, NO_DET, PARTIAL, PASS = ac.NA, ac.FAIL, ac.NO_DET, ac.PARTIAL, ac.PASS
CELLS = ac.NARR_CHECKS + ac.NULL_CHECKS
EV = "platform/scripts/governance/asset_census.py:1"
WHY = "the reviewed reason this declaration is true"


def psql(pg, sql=None, path=None):
    args = [str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-v", "ON_ERROR_STOP=1"] + (["-f", str(path)] if path is not None else ["-c", sql])
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    assert p.returncode == 0, (path or sql, p.stderr.strip()[:400])
    return p.stdout


def create_table_ddl(path, table):
    """The CREATE TABLE statement of `table` in a migration file (balanced parentheses, comments dropped): those files also INSERT registry rows / create triggers this database does not have."""
    txt = re.sub(r"--[^\n]*", "", pathlib.Path(path).read_text(encoding="utf-8"))
    i = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?" + re.escape(table) + r"\s*\(", txt).start()
    j, depth = txt.index("(", i), 0
    for k in range(j, len(txt)):
        depth += (txt[k] == "(") - (txt[k] == ")")
        if depth == 0:
            return txt[i: k + 1] + ";"
    raise AssertionError(f"unbalanced CREATE TABLE {table}")


def install_run_tables(pg):
    """The REAL build_runs / build_run_assets (supabase migration 171) and asset_provenance_receipts (596) DDL, with the two parents they reference stubbed (charts, asset_registry)."""
    for t in ("asset_provenance_receipts", "build_run_assets", "build_runs", "charts", "asset_registry"):
        psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    psql(pg, "CREATE TABLE charts (id uuid PRIMARY KEY)")
    psql(pg, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY)")
    psql(pg, create_table_ddl(SMIG / "171_build_runs.sql", "build_runs"))
    psql(pg, create_table_ddl(SMIG / "171_build_runs.sql", "build_run_assets"))
    psql(pg, create_table_ddl(SMIG / "596_nirmana_provenance_receipts.sql", "asset_provenance_receipts"))
    for c in (CHART_A, CHART_B):
        psql(pg, f"INSERT INTO charts VALUES ('{c}')")


def add_run(pg, run_id, asset_id, chart_id=CHART_A, state="complete", receipt=False):
    psql(pg, f"INSERT INTO build_runs (id, chart_id, scope, action, plan, triggered_by) VALUES ('{run_id}', '{chart_id}', 'asset', 'build', '[]'::jsonb, 'test') ON CONFLICT DO NOTHING")
    psql(pg, f"INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ('{run_id}', '{asset_id}', 1, '{state}') ON CONFLICT DO NOTHING")
    if receipt:
        psql(pg, f"INSERT INTO asset_registry VALUES ('{asset_id}') ON CONFLICT DO NOTHING")
        psql(pg, f"INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id) VALUES ('{asset_id}', NULL, 'p', 'v1', 'proven', '{run_id}')")


def drop_tables(pg, *tables):
    for t in tables:
        psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def decl_with(prose_none, **kw):
    d = {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": dict(why=WHY, closed_columns=[], **prose_none)}
    d.update(kw)
    return d


def measure(aid, db, monkeypatch, files, target, tables, decl, scope=None, registry=None):
    """What `measure()` does for one prose-declared asset: the catalog of the produced tables, the writer scope, the closure SQL and the FORM-GAP reads, through `_measure_prose` itself. `scope` installs the
    measured-chart read scope ({table: {where, label}}) for the duration of the call."""
    point_psql_at(db, monkeypatch)
    cat = ac.catalog(list(dict.fromkeys([target] + list(tables))))
    decls = {a: {"prose_fields": None} for a in ()}
    vocab = ac.prose_vocabulary({aid: decl}, {aid: set(tables) | {target}})
    ac.set_read_scope(scope or {})
    try:
        return ac._measure_prose(aid, decl, dict(registry or {}, target_table=target), files, cat, list(tables), {}, (), vocab)
    finally:
        ac.set_read_scope(None)


def all_na(got):
    assert sorted(got) == sorted(CELLS), sorted(got)
    bad = {c: (v["v"], v["measured"][:400]) for c, v in got.items() if v["v"] != NA}
    assert not bad, bad
    for c in CELLS:
        b = got[c]["prose_none"]
        assert b["checked"] is True and b["open"] == [] and b["contradicted"] == [] and b["unread"] == [], (c, b)
        assert ac.prose_none_na_problem(c, got[c]) is None


def verdicts(got):
    return {c: got[c]["v"] for c in CELLS}


def clone(d):
    return copy.deepcopy(d)


# ───────────────────────── L1 fixtures: the position facts the L1 writers read, on the real chart_facts DDL ─────────────────────────

AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAKSHATRA27 = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
               "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
               "Uttara Bhadrapada", "Revati"]
# a hand-built chart: (sign index 0..11, degree in sign, whole-sign house); the Lagna is Aries (the canonical chart's Moon is in Purva Bhadrapada)
CHART_POS = {"Lagna": (0, 12.5, 1), "Sun": (9, 21.8, 10), "Moon": (10, 5.0, 11), "Mars": (7, 3.0, 8), "Mercury": (9, 10.0, 10), "Jupiter": (5, 2.0, 6),
             "Venus": (9, 2.0, 10), "Saturn": (6, 28.0, 7), "Rahu": (3, 5.0, 4), "Ketu": (9, 5.0, 10)}
SUBJECT = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER", "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA"}


def install_chart_facts(pg):
    """The REAL chart_facts DDL (supabase migrations 204, 215, 216) plus the column migration 209 adds and the delete-authorisation stub the L1 writers call."""
    psql(pg, "DROP TABLE IF EXISTS chart_facts CASCADE")
    for f in ("204_chart_facts.sql", "215_chart_facts_formula_id.sql", "216_chart_facts_partial_indexes.sql"):
        psql(pg, path=SMIG / f)
    psql(pg, "ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS formula_provenance_text TEXT")
    psql(pg, "CREATE OR REPLACE FUNCTION public.authorize_l1_chart_facts_delete(uuid, text[], text[], text[]) RETURNS void LANGUAGE plpgsql AS $$ BEGIN END $$")


def seed_positions(pg, chart=CHART_A, ayanamshas=AYANAMSHAS, pos=CHART_POS):
    """The graha_position facts the real ga_positions writer stores (categories, keys and the sign / nakshatra names of the pyjhora adapter), for one chart: ONE statement."""
    vals = []
    for aya in ayanamshas:
        for g, (sn, deg, house) in pos.items():
            lon = sn * 30 + deg
            nak = "Purva Bhadrapada" if g == "Moon" else NAKSHATRA27[int(lon // (360 / 27)) % 27]
            for cat, key, vtxt, vnum in (("graha_position", "longitude_sidereal", None, lon), ("graha_position", "sign", SIGNS[sn], None), ("graha_position", "nakshatra", nak, None),
                                         ("graha_position", "house_d1", None, house), ("graha_sign_attributes", "sign_num", None, sn + 1), ("graha_sign_attributes", "degree_in_sign", None, deg)):
                vals.append(f"('{chart}|{aya}|{g}|{cat}|{key}', '{chart}', '{aya}', gen_random_uuid(), '{cat}', '{SUBJECT[g]}', '{key}', "
                            f"{'NULL' if vtxt is None else repr(vtxt)}, {'NULL' if vnum is None else vnum}, 'fixture', 'fixture', 'fixture', 'single', 'fixture', now())")
    psql(pg, "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num, "
             "citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at) VALUES " + ", ".join(vals))
