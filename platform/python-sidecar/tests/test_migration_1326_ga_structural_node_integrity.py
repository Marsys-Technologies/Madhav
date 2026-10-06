"""Migration 1326 (Suvarna routine migration; reviewer finding (d) of PR #3215): ga_structural's registered integrity_check_sql
conjunct (b4) gets a NODE exclusion on its retrograde composite downgrade, and nothing else changes.

(b4) re-derives graha_composite_state_classification from graha_position.retrograde_flag ('retrograde' -> 'weak'). Once PR #3205
stores 'retrograde' for the mean nodes Rahu/Ketu, the writer still keeps the downgrade OFF the nodes (N-185 / N-187), so their 30
rows stay 'neutral' and the OLD check would flag every one of them on a correct build. The NEW text excludes fact_subject
RAH_MEAN / KET_MEAN in that one WHEN line.

Two tiers:
  * STATIC (always runs): the pinned fixture of the live OLD text hashes to the production md5 (c56f9e12...); NEW = OLD with exactly
    the one line replaced and hashes to the md5 the migration names; the migration's two literals equal this test's independently
    spelled ones; guard shape (one UPDATE, lock_timeout first, no DDL / transaction control, NOTICE paths, one RAISE).
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration to a DISPOSABLE cluster this module creates with
    initdb in a temp dir (own port, trust auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found.

LIVE proves, with synthetic chart_facts rows and the FULL 208 KB registry SQL: node rows 'neutral' with flag 'retrograde' PASS under
NEW and FAIL under OLD (the defect); a tara graha (Mars) that is retrograde and NOT downgraded still FAILS under NEW (the exclusion is
only for the nodes); a node wrongly downgraded to 'weak' FAILS under NEW; the rest of the (b4) tree and other conjuncts
(including (c7), which is NOT relaxed) still bite on mutants; the UPDATE is guarded (foreign text untouched, NOTICE, no failure),
idempotent (xmin unchanged), changes no other column, stales ONLY ga_structural's asset_freshness rows through the production
trigger body, and a silent no-op is caught by the post-check. It does NOT prove production state (read from production structure
after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1326 = _REPO / "platform" / "migrations" / "1326_ga_structural_integrity_node_composite_exclusion.sql"
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ga_structural_1326" / "live_integrity_check_sql_pre1326_2026-10-07.sql"

OLD_MD5 = "c56f9e12b2002269eb5f27a7abc42105"
NEW_MD5 = "fcd217e25127653ee28ad41c629946aa"
OLD_LEN, NEW_LEN = 207959, 208378

OLD_LINE = "          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'\n"
NEW_BLOCK = (
    "          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores\n"
    "          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the\n"
    "          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.\n"
    "          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'\n"
)
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


# The fixture file IS the live text, byte for byte (it ends with the live text's own single trailing newline).
OLD_TEXT = _FIXTURE.read_bytes().decode("utf-8")
NEW_TEXT = OLD_TEXT.replace(OLD_LINE, NEW_BLOCK)


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_old_text_fixture_is_the_live_production_text():
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN


def test_static_the_replaced_line_is_present_exactly_once_and_is_the_only_retrograde_flag_branch():
    assert OLD_TEXT.count(OLD_LINE) == 1
    assert OLD_TEXT.count("re.retrograde_flag = 'retrograde'") == 1
    assert "NOT IN ('RAH_MEAN', 'KET_MEAN')" not in OLD_TEXT and NEW_TEXT.count("NOT IN ('RAH_MEAN', 'KET_MEAN')") == 1


def test_static_new_text_has_the_named_md5_and_length():
    assert _md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == NEW_LEN


def test_static_new_text_is_the_old_text_with_exactly_the_one_line_replaced():
    assert NEW_TEXT != OLD_TEXT
    head, tail = OLD_TEXT.split(OLD_LINE)
    assert NEW_TEXT == head + NEW_BLOCK + tail
    # every OLD line except the replaced one survives, in order; the only added lines are the four of NEW_BLOCK
    old_lines, new_lines = OLD_TEXT.splitlines(), NEW_TEXT.splitlines()
    assert len(new_lines) == len(old_lines) + 3
    i = old_lines.index(OLD_LINE.rstrip("\n"))
    assert new_lines[:i] == old_lines[:i] and new_lines[i + 4:] == old_lines[i + 1:]


def test_static_migration_literals_equal_the_independently_spelled_ones():
    sql = _M1326.read_text()
    old = re.search(r"\$ol\$(.*?)\$ol\$", sql, re.S).group(1)
    new = re.search(r"\$nl\$(.*?)\$nl\$", sql, re.S).group(1)
    assert old == OLD_LINE and new == NEW_BLOCK
    assert f"c_old_md5  constant text := '{OLD_MD5}'" in sql and f"c_new_md5  constant text := '{NEW_MD5}'" in sql


def test_static_one_guarded_update_of_integrity_check_sql_only_lock_timeout_first():
    code = _code(_M1326)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    assert "AND md5(integrity_check_sql) = c_old_md5;" in code
    assert code.count("WHERE asset_id = 'ga_structural'") >= 2
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code.replace("BEGIN\n", ""))
    assert not re.search(r"^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b", code, re.I | re.M)
    assert code.count("RAISE EXCEPTION") == 1 and "update did not take" in code
    assert "is not the text this migration was written against" in code and "NO-OP" in code


# -- LIVE tier: disposable PostgreSQL -------------------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1326pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m26", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"t{_n}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


# chart_facts / chart_divisionals / ga_yoga_firings: the production column names and types the text reads (read from
# information_schema 2026-10-07); NOT NULL text columns the check never reads carry defaults so synthetic rows stay short.
_FIXTURE_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE TABLE chart_facts (
    fact_id text NOT NULL DEFAULT gen_random_uuid()::text, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
    build_id uuid NOT NULL DEFAULT '00000000-0000-4000-8000-000000000001', fact_category text NOT NULL, fact_subject text NOT NULL,
    fact_key text NOT NULL, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, unit text,
    citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '', source_calculation text NOT NULL DEFAULT '',
    verification_pass_status text NOT NULL DEFAULT 'two_pass_verified', engine_version text NOT NULL DEFAULT 'test',
    salience_formula_ver text, computed_at timestamptz NOT NULL DEFAULT now(), tolerance_arcsec double precision,
    near_sign_boundary_flag boolean, near_nakshatra_boundary_flag boolean, vargottama_flag_at_point boolean,
    formula_provenance_text text, cross_ayanamsha_divergence_arcsec double precision, formula_id text);
CREATE TABLE chart_divisionals (
    id uuid NOT NULL DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, graha text, ayanamsha_id text NOT NULL, varga text NOT NULL,
    sign text, sign_number smallint, degree_in_sign numeric, house smallint, vargottama boolean,
    source_citation text NOT NULL DEFAULT '', build_id text NOT NULL DEFAULT 'b', created_at timestamptz NOT NULL DEFAULT now(),
    fact_category text, fact_key text, fact_value_text text, fact_value_num numeric, fact_subject text, build_id_uuid uuid,
    verification_pass_status text, engine_version text, citation_ref text, citation_human text, source_calculation text,
    computed_at timestamptz, tolerance_arcsec numeric, near_sign_boundary_flag boolean, near_nakshatra_boundary_flag boolean,
    vargottama_flag_at_point boolean, formula_provenance_text text, cross_ayanamsha_divergence_arcsec numeric);
CREATE TABLE ga_yoga_firings (
    id serial PRIMARY KEY, chart_id uuid NOT NULL, build_id uuid, ayanamsha_id text NOT NULL, yoga_canonical_id text NOT NULL,
    fired boolean NOT NULL, constituent_fact_ids jsonb, constituent_planets jsonb, constituent_houses jsonb, strength numeric,
    is_partial boolean, bhanga_active boolean, computed_at timestamptz);
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type,
                scope, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""


def _fact(c, cat: str, subj: str, key: str, text: str | None = None, num=None, js: dict | None = None, chart: str = CANON):
    c.execute("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text, "
              "fact_value_num, fact_value_jsonb) VALUES (%s,'lahiri',%s,%s,%s,%s,%s,%s)",
              (chart, cat, subj, key, text, num, json.dumps(js) if js is not None else None))


_EXALT = {"SUN": "Aries", "MOON": "Taurus", "MAR": "Capricorn", "MER": "Virgo", "JUP": "Cancer", "VEN": "Pisces", "SAT": "Libra"}
_DEBIL = {"SUN": "Libra", "MOON": "Scorpio", "MAR": "Cancer", "MER": "Pisces", "JUP": "Capricorn", "VEN": "Virgo", "SAT": "Aries"}


def _graha(c, subj: str, sign: str, retro: str, composite: str, *, comb: str = "not_combust", rollup_retro: bool | None = None):
    """One graha's position facts, its composite classification row and its special-state rollup (consistent with the position
    facts unless rollup_retro overrides). The rollup's exalted/debilitated flags follow the sign."""
    _fact(c, "graha_position", subj, "sign", sign)
    _fact(c, "graha_position", subj, "combustion_state", comb)
    _fact(c, "graha_position", subj, "retrograde_flag", retro)
    _fact(c, "graha_composite_state_classification", subj, "composite_state", composite)
    r = (retro == "retrograde") if rollup_retro is None else rollup_retro
    _fact(c, "graha_special_state_rollup", subj, "is_combust", "true" if comb == "combust" else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_retrograde", "true" if r else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_debilitated", "true" if _DEBIL.get(subj) == sign else "false")
    _fact(c, "graha_special_state_rollup", subj, "is_exalted", "true" if _EXALT.get(subj) == sign else "false")


def _setup(connect, grahas: list[tuple] | None = None, text: str = OLD_TEXT, with_row: bool = True):
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql, target_table, scope, has_writer) "
                      "VALUES ('ga_structural','ganita',%s,'chart_facts','per_chart',true)", (text,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql) VALUES ('ga_other','ganita','SELECT true')")
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES "
                      "('ga_structural', %s, 'fresh'), ('ga_structural', %s, 'fresh'), ('ga_other', %s, 'fresh')", (CANON, OTHER, CANON))
        for g in grahas or []:
            _graha(c, *g[:4], **(g[4] if len(g) > 4 else {}))
        c.commit()


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1326.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _check(connect, text: str) -> bool:
    return _q(connect, text)[0][0]


def _txt(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_structural'")[0][0]


# A today-like baseline: nodes still 'direct' and 'neutral'; Mars direct and neutral (Taurus is neutral for Mars); Moon neutral.
_TODAY = [("RAH_MEAN", "Gemini", "direct", "neutral"), ("KET_MEAN", "Sagittarius", "direct", "neutral"),
          ("MAR", "Taurus", "direct", "neutral"), ("MOON", "Gemini", "direct", "neutral")]
# The post-#3205 world: the nodes store 'retrograde' (rollup true, via #3215) and stay 'neutral'; Mars is direct.
_NODES_RETRO = [("RAH_MEAN", "Gemini", "retrograde", "neutral"), ("KET_MEAN", "Sagittarius", "retrograde", "neutral"),
                ("MAR", "Taurus", "direct", "neutral"), ("MOON", "Gemini", "direct", "neutral")]


def test_live_fixture_sanity_both_texts_pass_on_the_today_baseline_and_on_empty_tables(db):
    _setup(db, _TODAY)
    assert _check(db, OLD_TEXT) is True
    assert _check(db, NEW_TEXT) is True
    with db() as c:
        c.execute("DELETE FROM chart_facts")
        c.commit()
    assert _check(db, OLD_TEXT) is True and _check(db, NEW_TEXT) is True


def test_live_node_rows_neutral_with_retrograde_flag_pass_new_and_fail_old(db):
    _setup(db, _NODES_RETRO)
    assert _check(db, OLD_TEXT) is False, "the defect: the old (b4) re-derives 'weak' for the retrograde nodes and flags 'neutral'"
    assert _check(db, NEW_TEXT) is True


@pytest.mark.parametrize("node", ["RAH_MEAN", "KET_MEAN"])
def test_live_each_node_alone_is_excluded(db, node):
    _setup(db, [(node, "Gemini", "retrograde", "neutral"), ("MAR", "Taurus", "direct", "neutral")])
    assert _check(db, OLD_TEXT) is False and _check(db, NEW_TEXT) is True


def test_live_a_tara_graha_retrograde_and_not_downgraded_still_fails_new(db):
    _setup(db, [("MAR", "Taurus", "retrograde", "neutral")])
    assert _check(db, NEW_TEXT) is False
    assert _check(db, OLD_TEXT) is False


@pytest.mark.parametrize("g,sign", [("SUN", "Gemini"), ("MOON", "Gemini"), ("MAR", "Taurus"), ("MER", "Taurus"),
                                    ("JUP", "Taurus"), ("VEN", "Gemini"), ("SAT", "Gemini")])
def test_live_every_tara_graha_still_needs_the_retrograde_downgrade(db, g, sign):
    _setup(db, [(g, sign, "retrograde", "neutral")])
    assert _check(db, NEW_TEXT) is False, f"{g}: retrograde 'neutral' must still be flagged"
    with db() as c:
        c.execute("UPDATE chart_facts SET fact_value_text='weak' WHERE fact_category='graha_composite_state_classification'")
        c.commit()
    assert _check(db, NEW_TEXT) is True and _check(db, OLD_TEXT) is True, f"{g}: retrograde 'weak' is the correct row"


def test_live_a_node_wrongly_downgraded_to_weak_fails_new(db):
    """The exclusion is not a free pass: a node must be exactly 'neutral' (its dignity is neutral and it is not combust)."""
    _setup(db, [("RAH_MEAN", "Gemini", "retrograde", "weak"), ("MAR", "Taurus", "direct", "neutral")])
    assert _check(db, NEW_TEXT) is False
    assert _check(db, OLD_TEXT) is True, "old text agrees with a 'weak' node: this is exactly the contradiction the migration resolves"


def test_live_the_rest_of_the_b4_tree_is_unchanged(db):
    _setup(db, [("MAR", "Taurus", "direct", "neutral"), ("RAH_MEAN", "Gemini", "direct", "neutral")])  # no retrograde node: OLD must agree
    assert _check(db, NEW_TEXT) is True and _check(db, OLD_TEXT) is True
    cases = {
        # retrograde does not demote an exalted/own-sign graha (well_placed branch precedes the retrograde branch)
        "exalted_retro_is_well_placed": (("MAR", "Capricorn", "retrograde", "well_placed"), True),
        "exalted_retro_weak_is_wrong": (("MAR", "Capricorn", "retrograde", "weak"), False),
        "own_sign_direct_well_placed": (("MAR", "Aries", "direct", "well_placed"), True),
        "debilitated_plain": (("MAR", "Cancer", "direct", "debilitated"), True),
        "debilitated_retro_stays_debilitated": (("MAR", "Cancer", "retrograde", "debilitated"), True),
        "debilitated_combust_severe": (("MAR", "Cancer", "direct", "severely_afflicted", {"comb": "combust"}), True),
        "combust_afflicted": (("MAR", "Taurus", "direct", "afflicted", {"comb": "combust"}), True),
        "combust_wrong": (("MAR", "Taurus", "direct", "neutral", {"comb": "combust"}), False),
        "direct_neutral_wrong_weak": (("MAR", "Taurus", "direct", "weak"), False),
    }
    for name, (g, ok) in cases.items():
        with db() as c:
            c.execute("DELETE FROM chart_facts WHERE fact_subject='MAR'")
            _graha(c, g[0], g[1], g[2], g[3], **(g[4] if len(g) > 4 else {}))
            c.commit()
        assert _check(db, NEW_TEXT) is ok, f"case {name}"
        assert _check(db, OLD_TEXT) is ok, f"case {name} (old text must agree: nothing but the node line changed)"


def test_live_other_conjuncts_still_bite_including_c7_which_is_not_relaxed(db):
    _setup(db, _NODES_RETRO)
    assert _check(db, NEW_TEXT) is True
    mutants = {
        "a_amplification_domain": "INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
                                  f"VALUES ('{CANON}','lahiri','graha_vargottama_amplification_factor','SUN','amplification_factor',2.0)",
        "k_yuddha_names_a_node": "INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_jsonb) "
                                 f"VALUES ('{CANON}','lahiri','graha_yuddha_per_varga','D1_MAR_VEN','within_1deg',"
                                 "'{\"graha1\":\"Rahu\",\"graha2\":\"Mars\",\"orb_deg\":0.5}'::jsonb)",
        "a4_composite_domain": "UPDATE chart_facts SET fact_value_text='bogus' WHERE fact_category='graha_composite_state_classification' "
                               "AND fact_subject='MOON'",
        "b7_combust_rollup": "UPDATE chart_facts SET fact_value_text='true' WHERE fact_category='graha_special_state_rollup' "
                             "AND fact_key='is_combust' AND fact_subject='MOON'",
        "c7_node_rollup_disagrees_with_flag": "UPDATE chart_facts SET fact_value_text='false' WHERE "
                                              "fact_category='graha_special_state_rollup' AND fact_key='is_retrograde' "
                                              "AND fact_subject='RAH_MEAN'",
        "a7_rollup_domain": "UPDATE chart_facts SET fact_value_text='maybe' WHERE fact_category='graha_special_state_rollup' "
                            "AND fact_key='is_exalted' AND fact_subject='MOON'",
    }
    for name, sql in mutants.items():
        with db() as c:
            c.execute("SAVEPOINT m")
            c.execute(sql)
            assert c.execute(NEW_TEXT).fetchone()[0] is False, f"mutant {name} was not caught"
            c.execute("ROLLBACK TO SAVEPOINT m")
            assert c.execute(NEW_TEXT).fetchone()[0] is True, f"fixture not restored after {name}"


def test_live_apply_installs_the_new_text_and_the_installed_text_judges_like_the_file(db):
    _setup(db, _NODES_RETRO)
    assert _check(db, _txt(db)) is False
    _apply(db)
    assert _md5(_txt(db)) == NEW_MD5 and len(_txt(db)) == NEW_LEN and _txt(db) == NEW_TEXT
    assert _check(db, _txt(db)) is True


def test_live_apply_touches_only_integrity_check_sql_and_stales_only_ga_structural(db):
    _setup(db, _NODES_RETRO)
    before = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_other'")[0][0] == "SELECT true"
    fr = {(a, c): (s, r) for a, c, s, r in _q(db, "SELECT asset_id, chart_id::text, freshness_state, reasons::text FROM asset_freshness")}
    assert fr[("ga_structural", CANON)][0] == "stale" and "registry_changed" in fr[("ga_structural", CANON)][1]
    assert fr[("ga_structural", OTHER)][0] == "stale"
    assert fr[("ga_other", CANON)] == ("fresh", "[]")


def test_live_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _setup(db, _NODES_RETRO)
    _apply(db)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'")
    with db() as c:
        c.execute("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]' WHERE asset_id='ga_structural'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'") == x1
    assert any("already carries the node exclusion" in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness WHERE asset_id='ga_structural'")} == {"fresh"}


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = OLD_TEXT + "\n-- edited by hand\n"
    _setup(db, text=foreign)
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n and _md5(foreign) in n for n in notes)
    assert {s for (s,) in _q(db, "SELECT freshness_state FROM asset_freshness")} == {"fresh"}


def test_live_null_text_is_a_noop_not_a_failure(db):
    _setup(db)
    with db() as c:
        c.execute("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='ga_structural'")
        c.commit()
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) is None and any("NO-OP" in n for n in notes)


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no ga_structural registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ga_structural' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _txt(db) == OLD_TEXT
