"""
Migration 1364 (certification; held with the one-canonical-nakshatra-spelling PR): bo_nakshatra_semantic's registered integrity_check_sql,
vocabulary conjunct widened to accept BOTH nakshatra spellings during the merge-to-rebuild window.

Migration 669 bounds configuration_jsonb->>'nakshatra' to 27 hard-coded OLD L1 spellings (Mrigashira, Mula, Dhanishta). Once L1 writes the L0
lexicon's spellings (Mrigasira, Moola, Dhanishtha) the native's Jupiter (in Moola) would fail that conjunct. 1364 replaces the text with one
whose list is the lexicon's 27 names plus the three legacy L1 spellings.

Two tiers:
  * STATIC (always runs): the OLD text is re-derived from migration 669's file and hashes to the md5 the migration guards on; the NEW text is
    OLD with exactly the one list replaced; the list is PINNED TO THE LEXICON (brahmagyan.nakshatra_vocabulary: canonical names + legacy keys);
    guard / idempotent / post-check shape; data-only; unique number.
  * LIVE (needs PostgreSQL server binaries AND psycopg AND CI=true or MARSYS_PG_LIVE_1364=1; it never starts a cluster on a developer machine by
    accident): applies the REAL on-disk migration to a DISPOSABLE cluster created with initdb in a temp dir. OLD vs NEW on a synthetic
    bodha_msr_signals: the OLD text reads FALSE for a Moola row (the defect), the NEW text reads TRUE for the lexicon spelling and for the legacy
    one, and FALSE for an unknown name; apply is guarded / idempotent / loud on a silent no-op.
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

from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES, LEGACY_L1_SPELLINGS

_REPO = Path(__file__).resolve().parents[3]
_MIGRATIONS = _REPO / "platform" / "migrations"
_M669 = _MIGRATIONS / "669_bo_nakshatra_semantic_integrity_check.sql"
_M1364 = _MIGRATIONS / "1364_bo_nakshatra_semantic_integrity_accept_canonical_spelling.sql"

OLD_MD5, OLD_LEN = "24f6f27a4d7a941445def16ebe95e899", 2481
NEW_MD5, NEW_LEN = "819cb0d44572c41dd26129dfce1679d6", 2865

# The 27 OLD L1 spellings, spelled here independently of the lexicon and of the migration (what migration 669 held).
OLD_27 = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

_LIST_RE = re.compile(r"      AND configuration_jsonb->>'nakshatra' NOT IN \(\n(.*?)\n      \)\n", re.S)


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("--"))


OLD_TEXT = re.search(r"\$ic\$(.*?)\$ic\$", _M669.read_text(encoding="utf-8"), re.S).group(1)
SQL = _M1364.read_text(encoding="utf-8")
NEW_TEXT = re.search(r"\$nt\$(.*?)\$nt\$", SQL, re.S).group(1)


def _list_of(text: str) -> list[str]:
    block = _LIST_RE.search(text).group(1)
    code = "\n".join(l for l in block.splitlines() if not l.lstrip().startswith("--"))
    return re.findall(r"'([^']*)'", code)


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_old_text_is_migration_669_s_body_and_has_the_named_md5():
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN
    assert tuple(_list_of(OLD_TEXT)) == OLD_27, "migration 669's list is the 27 OLD L1 spellings"


def test_static_no_other_migration_sets_this_assets_integrity_check_sql():
    """The OLD text is the live text only if nothing but 669 (and 1364) sets it: search every migration that names the asset."""
    setters = []
    for p in sorted(_MIGRATIONS.glob("*.sql")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if "bo_nakshatra_semantic" not in t:
            continue
        code = "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("--"))
        if re.search(r"UPDATE\s+asset_registry[^;]*?integrity_check_sql[^;]*?asset_id\s*=\s*'bo_nakshatra_semantic'", code):
            setters.append(p.name)
    assert sorted(setters) == sorted([_M669.name, _M1364.name]), setters


def test_static_new_text_has_the_named_md5_and_length():
    assert _md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == NEW_LEN
    assert f"'{NEW_MD5}'" in SQL and f"'{OLD_MD5}'" in SQL


def test_static_new_is_old_with_exactly_the_one_list_replaced():
    assert _LIST_RE.subn("<LIST>\n", OLD_TEXT)[1] == 1 and _LIST_RE.subn("<LIST>\n", NEW_TEXT)[1] == 1
    assert _LIST_RE.sub("<LIST>\n", OLD_TEXT) == _LIST_RE.sub("<LIST>\n", NEW_TEXT)


def test_static_the_list_is_pinned_to_the_lexicon():
    """The proof the list is built from the lexicon: canonical names in nakshatra order, then the legacy L1 spellings."""
    assert _list_of(NEW_TEXT) == list(CANONICAL_NAKSHATRA_NAMES) + list(LEGACY_L1_SPELLINGS)
    assert len(_list_of(NEW_TEXT)) == 30 and len(set(_list_of(NEW_TEXT))) == 30


def test_static_the_list_is_exactly_old_names_plus_canonical_names_of_the_three_respelled_nakshatras():
    assert set(_list_of(NEW_TEXT)) == set(OLD_27) | set(CANONICAL_NAKSHATRA_NAMES)
    assert set(CANONICAL_NAKSHATRA_NAMES) - set(OLD_27) == {"Mrigasira", "Moola", "Dhanishtha"}
    assert set(OLD_27) - set(CANONICAL_NAKSHATRA_NAMES) == {"Mrigashira", "Mula", "Dhanishta"}
    assert set(LEGACY_L1_SPELLINGS) == set(OLD_27) - set(CANONICAL_NAKSHATRA_NAMES)


def test_static_the_list_accepts_the_names_l1_and_the_emitter_actually_write():
    from pyjhora_adapter._names import NAKSHATRA_NAMES
    from bodha_writers.nakshatra_semantic_emitter import NAKSHATRA_ORDER

    accepted = set(_list_of(NEW_TEXT))
    assert set(NAKSHATRA_NAMES[1:]) <= accepted and set(NAKSHATRA_ORDER) <= accepted
    assert "Moola" in accepted and "Mula" in accepted, "the native's Jupiter (Moola) reads TRUE after the rebuild AND before it"


def test_static_every_other_conjunct_is_untouched_eight_conjuncts_remain():
    body = _LIST_RE.sub("", NEW_TEXT)
    for frag in ("HAVING count(*) != 9", "NOT BETWEEN 1 AND 4", "'house_d1')::int NOT BETWEEN 1 AND 12",
                 "'tara_position')::int NOT BETWEEN 1 AND 9", "NOT IN (1,3,5,7)", "NOT LIKE 'gandanta_%'",
                 "jsonb_array_length(configuration_jsonb->'dispositor_chain')"):
        assert frag in body
    assert OLD_TEXT.count("NOT EXISTS") == NEW_TEXT.count("NOT EXISTS") == 8


def test_static_one_guarded_update_of_integrity_check_sql_only_lock_timeout_first():
    code = _code(_M1364)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", ""), re.I) == ["integrity_check_sql"]
    assert "AND md5(integrity_check_sql) = c_old_md5;" in code and "c_old_md5  constant text := '" + OLD_MD5 + "'" in code
    assert "c_new_md5  constant text := '" + NEW_MD5 + "'" in code
    assert code.count("UPDATE asset_registry") == 1 and "WHERE asset_id = 'bo_nakshatra_semantic'" in code
    outside = re.sub(r"\$nt\$.*?\$nt\$", "", code, flags=re.S)       # the DDL/DML ban applies to the migration, not to the check text it stores
    assert not re.search(r"\b(COMMIT|ROLLBACK|CREATE|ALTER|DROP|INSERT|DELETE|TRUNCATE)\b", outside)


def test_static_noop_notices_come_before_the_update_and_the_raise_after_it():
    code = _code(_M1364)
    i_new, i_old, i_upd, i_raise = (code.index("v_md5 = c_new_md5"), code.index("IS DISTINCT FROM c_old_md5"),
                                    code.index("UPDATE asset_registry"), code.index("RAISE EXCEPTION"))
    assert i_new < i_upd and i_old < i_upd < i_raise
    assert code.count("RAISE EXCEPTION") == 1 and "IS DISTINCT FROM c_new_md5" in code.split("RAISE EXCEPTION")[0].split("UPDATE asset_registry")[1]


def test_static_header_states_why_what_guard_trigger_effect_verification_rollback():
    head = SQL.split("SET LOCAL lock_timeout", 1)[0]
    for needle in ("WHY.", "WHAT.", "GUARD AND WHAT HAPPENS", "SERVING EFFECT AT APPLY", "nirmana_registry_receipt_invalidation",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK", "Moola", NEW_MD5, OLD_MD5):
        assert needle in head, needle


def test_static_unique_number_and_routine_migration():
    assert [p.name for p in _MIGRATIONS.glob("1364_*.sql")] == [_M1364.name]


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
    in_ci = os.environ.get("CI", "").lower() in ("true", "1")
    if not in_ci and os.environ.get("MARSYS_PG_LIVE_1364") != "1":
        pytest.skip("live tier runs in CI (CI=true) or with MARSYS_PG_LIVE_1364=1; it never starts a cluster by accident")
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1364pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m64", dir="/tmp"))
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
    name = f"u{_n}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host=sock, port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


CANON = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHAS = ("lahiri", "raman", "krishnamurti", "fagan_bradley", "surya_siddhanta_classical")
GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

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
CREATE TABLE bodha_msr_signals (
    id serial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, signal_type_class text NOT NULL,
    configuration_jsonb jsonb NOT NULL);
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


def _cfg(nakshatra: str) -> str:
    return json.dumps({"nakshatra": nakshatra, "pada": 2, "house_d1": 3, "tara_position": 2, "tara_favorable": True,
                       "gandanta_flag": False, "gandanta_zone": "not_applicable", "dispositor_chain": ["Sun"],
                       "dispositor_chain_length": 1})


def _setup(connect, text: str = OLD_TEXT, with_row: bool = True, jupiter: str = "Moola"):
    """A clean 9-row-per-(chart, ayanamsha) bodha_msr_signals; Jupiter (the native's Moola) is the row under test."""
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql, scope, has_writer) "
                      "VALUES ('bo_nakshatra_semantic','bodha',%s,'per_chart',true)", (text,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, integrity_check_sql) VALUES ('bo_other','bodha','SELECT true')")
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES "
                      "('bo_nakshatra_semantic', %s, 'fresh'), ('bo_other', %s, 'fresh')", (CANON, CANON))
        for ay in AYANAMSHAS:
            for g in GRAHAS:
                nak = jupiter if g == "Jupiter" else "Purva Bhadrapada"
                c.execute("INSERT INTO bodha_msr_signals (chart_id, ayanamsha_id, signal_type_class, configuration_jsonb) "
                          "VALUES (%s,%s,'nakshatra_semantic',%s::jsonb)", (CANON, ay, _cfg(nak)))
        c.commit()


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(SQL)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _set_nakshatra(connect, name: str):
    with connect() as c:
        c.execute("UPDATE bodha_msr_signals SET configuration_jsonb = jsonb_set(configuration_jsonb, '{nakshatra}', to_jsonb(%s::text)) "
                  "WHERE configuration_jsonb->>'nakshatra' <> 'Purva Bhadrapada'", (name,))
        c.commit()


def _txt(connect) -> str:
    return _q(connect, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_nakshatra_semantic'")[0][0]


def test_live_old_text_reads_false_for_the_canonical_spelling_new_text_reads_true_for_both_and_false_for_an_unknown_name(db):
    _setup(db, jupiter="Mula")
    assert _q(db, OLD_TEXT)[0][0] is True and _q(db, NEW_TEXT)[0][0] is True        # the legacy spelling: both read true
    _set_nakshatra(db, "Moola")
    assert _q(db, OLD_TEXT)[0][0] is False, "the defect: the OLD list rejects the lexicon's own spelling of the native's Jupiter"
    assert _q(db, NEW_TEXT)[0][0] is True
    for canon, legacy in (("Mrigasira", "Mrigashira"), ("Dhanishtha", "Dhanishta")):
        _set_nakshatra(db, canon)
        assert _q(db, NEW_TEXT)[0][0] is True
        _set_nakshatra(db, legacy)
        assert _q(db, NEW_TEXT)[0][0] is True
    _set_nakshatra(db, "Mulaa")
    assert _q(db, NEW_TEXT)[0][0] is False
    _set_nakshatra(db, "moola")                      # no case folding in the stored vocabulary: a case variant is still not a nakshatra name
    assert _q(db, NEW_TEXT)[0][0] is False


def test_live_every_lexicon_name_and_every_legacy_name_reads_true(db):
    _setup(db)
    for name in list(CANONICAL_NAKSHATRA_NAMES) + list(LEGACY_L1_SPELLINGS):
        _set_nakshatra(db, name)
        assert _q(db, NEW_TEXT)[0][0] is True, name


def test_live_the_other_conjuncts_still_bite_in_the_new_text(db):
    _setup(db)
    assert _q(db, NEW_TEXT)[0][0] is True
    with db() as c:
        c.execute("DELETE FROM bodha_msr_signals WHERE id = (SELECT min(id) FROM bodha_msr_signals)")   # tiling: 8 rows in one group
        c.commit()
    assert _q(db, NEW_TEXT)[0][0] is False


def test_live_apply_installs_the_new_text_which_judges_like_the_file(db):
    _setup(db, jupiter="Moola")
    assert _q(db, _txt(db))[0][0] is False
    _apply(db)
    assert _md5(_txt(db)) == NEW_MD5 and len(_txt(db)) == NEW_LEN
    assert _q(db, _txt(db))[0][0] is True


def test_live_apply_touches_only_integrity_check_sql_and_stales_only_this_asset(db):
    _setup(db)
    before = _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id")
    other = _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_other'")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bo_other'") == other
    states = dict(_q(db, "SELECT asset_id, freshness_state FROM asset_freshness"))
    assert states == {"bo_nakshatra_semantic": "stale", "bo_other": "fresh"}


def test_live_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _setup(db)
    _apply(db)
    with db() as c:
        c.execute("UPDATE asset_freshness SET freshness_state='fresh', reasons='[]'::jsonb")
        c.commit()
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_nakshatra_semantic'")
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_nakshatra_semantic'") == x1
    assert any("already accepts both nakshatra spellings" in n for n in notes)
    assert {s for (_, s) in _q(db, "SELECT asset_id, freshness_state FROM asset_freshness")} == {"fresh"}


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = OLD_TEXT + "\n-- hand edit\n"
    _setup(db, foreign)
    notes: list[str] = []
    _apply(db, notes)
    assert _txt(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n for n in notes)


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no bo_nakshatra_semantic registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bo_nakshatra_semantic' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _txt(db) == OLD_TEXT
