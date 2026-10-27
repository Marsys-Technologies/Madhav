"""Migration 1412 (FOURQ-CLOSURE-20261027; provenance DOUBLE-TRANSIT-PROVENANCE-20261027): the 7 migration-owned
Jupiter–Saturn `double_transit` rows of bg_transit_rules are RETIRED (status retired_pending_reauthor as a citation prefix,
the non-existent citation struck for an honest attribution, a marker in rule_notes) and the registry's integrity pin is
resealed from migration 1320's hash to the post-change hash.

Offline and on a DISPOSABLE Postgres (never the project database), the same reconstruction tests/l0/test_citation_pass2_transit.py
uses for migration 1320: the DDL of migrations 266 / 397 / 401 (so the REAL CHECK constraints are in force), migration 397's
seven double_transit rows, then the seed (brahmagyan/l0_transit.py). What this pins:
  * the reconstruction hashes to migration 1320's pin (so it is faithful to the state 1320 describes) and the citation census
    the new english_description states is MEASURED on it (36 / 6 / 19 / 8 / 7);
  * applying the REAL migration SQL (one transaction, the migrate.ts shape) relabels exactly the 7 rows -- ids, rule_type,
    graha, houses and phala untouched, 76 = 43 + 26 + 7 unchanged, no CHECK constraint rejects the new text, no row cites the
    struck passage -- reseals the stored check to the pinned POST hash, and the stored check then HOLDS; the vedha loader
    (the only other reader of the table) still loads the same pairs; a second run changes nothing (idempotent);
  * an unrecognised prior state (pin absent, half-migrated rows, a description that is not migration 1079's) is REFUSED and the
    rows are left as they were;
  * static: no public DDL (the Kāla protected-window detector sees nothing), the attribution and the prefix are byte-identical
    to the code's vocabulary (citations.py), and the TS registry seed carries the same description (1320's parity rule).
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[2]))                                  # platform/python-sidecar
sys.path.insert(0, str(REPO / "platform" / "scripts" / "governance"))     # check_public_schema_migration_privilege

from brahmagyan import l0_transit as T  # noqa: E402
from services.gochara_grammar import citations as C  # noqa: E402
from tests.pg_disposable import HAVE_PG, new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIG = REPO / "platform" / "migrations"
SUP = REPO / "platform" / "supabase" / "migrations"
MIGRATION = MIG / "1412_bg_transit_rules_double_transit_testimony_reseal.sql"
SEED_TS = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
SQL = MIGRATION.read_text(encoding="utf-8")

PIN_1078 = "1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d"
PIN_1320 = "dce17ed02e1ba05eb4db5d0a46777a70c1f5832160fa3add253f7119bbf7ea8d"
RULING = "FOURQ-CLOSURE-20261027"
PROVENANCE = "DOUBLE-TRANSIT-PROVENANCE-20261027"
STRUCK = "Phaladeepika ch.26 §double-gochara"
HASH_SQL = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,classical_citation,rule_notes)::text,"
            " E'\\n' ORDER BY graha COLLATE \"C\",rule_type COLLATE \"C\",primary_house),''),'UTF8')),'hex') FROM bg_transit_rules")
COUNTS_SQL = ("SELECT count(*), count(*) FILTER (WHERE rule_type='favourable'), count(*) FILTER (WHERE rule_type='unfavourable'),"
              " count(*) FILTER (WHERE rule_type='double_transit') FROM bg_transit_rules")
SEVEN_SQL = "SELECT id, rule_type, graha, primary_house, vedha_house, phala FROM bg_transit_rules WHERE rule_type='double_transit' ORDER BY id"


def _const(name: str) -> str:
    """A `name constant text := '...'` literal of the migration, unescaped."""
    m = re.search(name + r" constant text :=\s*'(.*?)';\n", SQL, re.S)
    assert m, name
    return m.group(1).replace("''", "'")


NEW_PIN = re.search(r"new_pin constant text := '([0-9a-f]{64})'", SQL).group(1)
ATTRIBUTION = _const("attribution")
RETIRED_CITATION = _const("retired_citation")
RETIRED_NOTE = _const("retired_note")
RETIRED_PREFIX = _const("retired_prefix")
PRIOR_DESCRIPTION = _const("prior_description")
NEW_DESCRIPTION = _const("new_description")


def _lit(s: str) -> str:
    return "$q$" + s + "$q$"


# ───────────────────────── static ─────────────────────────

def test_static_no_public_ddl_rulings_named_vocabulary_identical_to_the_code_and_seed_parity():
    from check_public_schema_migration_privilege import find_violations
    assert find_violations(SQL) == []                       # DML only: never a Kāla protected-window member
    assert "ALTER TABLE" not in SQL and "CREATE " not in SQL.replace("-- ", "")
    assert RULING in SQL and PROVENANCE in SQL and STRUCK in SQL
    assert re.search(r"prior_pin constant text := '" + PIN_1320 + "'", SQL)
    assert NEW_PIN not in (PIN_1320, PIN_1078)
    # the vocabulary the code and the rows share
    assert ATTRIBUTION == C.DOUBLE_TRANSIT_COMMENTARIAL_ATTRIBUTION
    assert RETIRED_PREFIX == C.RETIRED_CITATION_PREFIX == "RETIRED_PENDING_REAUTHOR"
    assert RETIRED_CITATION == f"{RETIRED_PREFIX} ({C.FOURQ_CLOSURE_RULING_REF}) — {ATTRIBUTION}"
    assert RETIRED_NOTE.startswith(C.STATUS_RETIRED_PENDING_REAUTHOR + ":") and RULING in RETIRED_NOTE and PROVENANCE in RETIRED_NOTE
    assert "double-gochara" not in ATTRIBUTION and "K.N. Rao" in ATTRIBUTION
    # the prior description is migration 1079's truthful_description, verbatim
    t79 = (SUP / "1079_nirmana_l0_transit_rules_description_truthfulness.sql").read_text(encoding="utf-8")
    desc79 = re.search(r"truthful_description constant text :=\s*'(.*?)';\n", t79, re.S).group(1).replace("''", "'")
    assert PRIOR_DESCRIPTION == desc79
    assert "RETIRED_PENDING_REAUTHOR" in NEW_DESCRIPTION and RULING in NEW_DESCRIPTION
    # parity: the TS registry seed carries the NEW description (single-quoted TS string, apostrophe escaped)
    seed = SEED_TS.read_text(encoding="utf-8")
    assert NEW_DESCRIPTION.replace("'", "\\'") in seed
    assert PRIOR_DESCRIPTION.replace("'", "\\'") not in seed


# ───────────────────────── real SQL ─────────────────────────

def _connect(pg_port, db):
    try:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db,
                                cursor_factory=psycopg2.extras.RealDictCursor)
    except ImportError:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db, row_factory=dict_row)


def _db(pg_port):
    """The three transit tables as production has them: migrations 266 / 397 / 401 DDL (real CHECKs), 397's seven
    double_transit rows, the seed."""
    db = new_db(pg_port)
    t266 = (MIG / "266_bg_transit_tables.sql").read_text(encoding="utf-8")
    for pat in (r"(CREATE TABLE IF NOT EXISTS bg_transit_engine.*?\);)\s*COMMENT ON TABLE bg_transit_engine",
                r"(CREATE TABLE IF NOT EXISTS bg_transit_rules.*?\n\);)"):
        r = psql(pg_port, db, re.search(pat, t266, re.S).group(1)); assert r.returncode == 0, r.stderr
    t397 = (SUP / "397_bg_transit_av_gates.sql").read_text(encoding="utf-8")
    r = psql(pg_port, db, "ALTER TABLE bg_transit_rules DROP CONSTRAINT IF EXISTS bg_transit_rules_rule_type_check; ALTER TABLE bg_transit_rules "
                          "ADD CONSTRAINT bg_transit_rules_rule_type_check CHECK (rule_type IN ('favourable','unfavourable','vedha','double_transit'));")
    assert r.returncode == 0, r.stderr
    r = psql(pg_port, db, re.search(r"(INSERT INTO bg_transit_rules .*?ON CONFLICT \(graha, rule_type, primary_house\) DO NOTHING;)", t397, re.S).group(1))
    assert r.returncode == 0, r.stderr
    t401 = (SUP / "401_bg_transit_moorti.sql").read_text(encoding="utf-8")
    r = psql(pg_port, db, re.search(r"(CREATE TABLE IF NOT EXISTS bg_transit_moorti.*?\n\);)", t401, re.S).group(1)); assert r.returncode == 0, r.stderr
    conn = _connect(pg_port, db)
    try:
        T.seed_transit_rules(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def _check_1320() -> str:
    """The stored check migration 1320 left: migration 1078's new_rules_check with the pin replaced (1320's guarded replace)."""
    t = (SUP / "1078_nirmana_l0_transit_rules_integrity_reseal.sql").read_text(encoding="utf-8")
    chk = re.search(r"new_rules_check constant text := \$check\$(.*?)\$check\$;", t, re.S).group(1)
    assert chk.count(PIN_1078) == 1
    return chk.replace(PIN_1078, PIN_1320)


def _registry(pg_port, db, chk, desc, floor=76):
    r = psql(pg_port, db, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, english_description text, target_floor int)")
    assert r.returncode == 0, r.stderr
    r = psql(pg_port, db, "INSERT INTO asset_registry VALUES ('bg_transit_rules', $c$" + chk + "$c$, " + _lit(desc) + ", " + str(floor) + ")")
    assert r.returncode == 0, r.stderr


def _apply(pg_port, db):
    return psql(pg_port, db, file=MIGRATION, single_transaction=True)


def _load_pairs(pg_port, db):
    from services.gochara_rules import vedha_derive as vd
    conn = _connect(pg_port, db)
    try:
        return vd.load_pairs(conn.cursor())
    finally:
        conn.close()


@requires_pg
def test_REAL_SQL_the_reconstruction_hashes_to_migration_1320s_pin_and_measures_the_census_the_description_states(pg):
    db = _db(pg)
    assert q(pg, db, HASH_SQL) == PIN_1320                       # faithful to the state 1320 pins
    assert q(pg, db, COUNTS_SQL) == "76|43|26|7"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%'") == "36"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'UNSOURCED%'") == "6"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation = 'BPHS Ch.29 (Gochara Phala — Transit Results)'") == "19"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation IN (" + _lit(T.PD_CH26) + ", " + _lit(T.PD_ADH26_S2_8_21) + ")") == "8"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE rule_type = 'double_transit' AND classical_citation LIKE " + _lit(STRUCK + "%")) == "7"
    # the table has no status / provenance column: the status must ride in the text (its only CHECKs are rule_type and the house ranges)
    cols = q(pg, db, "SELECT string_agg(column_name, ',' ORDER BY ordinal_position) FROM information_schema.columns WHERE table_name = 'bg_transit_rules'")
    assert cols == "id,rule_type,graha,primary_house,vedha_house,phala,classical_citation,rule_notes"
    checks = q(pg, db, "SELECT string_agg(pg_get_constraintdef(oid), ' | ' ORDER BY conname) FROM pg_constraint WHERE conrelid = 'bg_transit_rules'::regclass AND contype = 'c'")
    assert "rule_type" in checks and "classical_citation" not in checks and "rule_notes" not in checks


@requires_pg
def test_REAL_SQL_migration_1412_retires_exactly_the_seven_rows_reseals_the_pin_keeps_the_loader_and_is_idempotent(pg):
    db = _db(pg)
    _registry(pg, db, _check_1320(), PRIOR_DESCRIPTION)
    seven_before = q(pg, db, SEVEN_SQL)
    others_before = q(pg, db, "SELECT md5(string_agg(t::text, E'\\n' ORDER BY id)) FROM bg_transit_rules t WHERE rule_type <> 'double_transit'")
    pairs_before = _load_pairs(pg, db)

    r = _apply(pg, db)
    assert r.returncode == 0, r.stderr                           # the real CHECK constraints accept the new text
    assert q(pg, db, HASH_SQL) == NEW_PIN                        # the pinned POST hash is what the rows really hash to
    assert q(pg, db, COUNTS_SQL) == "76|43|26|7"                 # shape unchanged: still 7 double_transit rows (the frozen count)
    assert q(pg, db, SEVEN_SQL) == seven_before                  # ids, rule_type, graha, houses, phala untouched
    assert q(pg, db, "SELECT md5(string_agg(t::text, E'\\n' ORDER BY id)) FROM bg_transit_rules t WHERE rule_type <> 'double_transit'") == others_before
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE '%double-gochara%'") == "0"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'RETIRED_PENDING_REAUTHOR%'") == "7"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE rule_type='double_transit' AND classical_citation = " + _lit(RETIRED_CITATION)) == "7"
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE rule_type='double_transit' AND rule_notes LIKE " + _lit(RETIRED_NOTE + "%")) == "7"
    # the original notes survive after the marker (two rows had NULL notes: marker only)
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE rule_type='double_transit' AND rule_notes = " + _lit(RETIRED_NOTE)) == "2"
    # the vedha loader (vedha_house IS NOT NULL rows only) is untouched by the relabel
    pairs_after = _load_pairs(pg, db)
    assert dict(pairs_after) == dict(pairs_before) and pairs_after.census == pairs_before.census and len(pairs_after) == 36
    assert pairs_after.content_digest == pairs_before.content_digest
    # the stored check is 1320's text with exactly the pin substituted, and it HOLDS on the retired rows
    chk = q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules'")
    assert chk == _check_1320().replace(PIN_1320, NEW_PIN).strip()
    assert q(pg, db, chk.strip().rstrip(";")) == "t"
    assert q(pg, db, "SELECT english_description FROM asset_registry WHERE asset_id = 'bg_transit_rules'") == NEW_DESCRIPTION
    # idempotent: a second run is accepted and changes nothing
    rows_after = q(pg, db, "SELECT md5(string_agg(t::text, E'\\n' ORDER BY id)) FROM bg_transit_rules t")
    reg_after = q(pg, db, "SELECT md5(t::text) FROM asset_registry t")
    r2 = _apply(pg, db)
    assert r2.returncode == 0, r2.stderr
    assert q(pg, db, "SELECT md5(string_agg(t::text, E'\\n' ORDER BY id)) FROM bg_transit_rules t") == rows_after
    assert q(pg, db, "SELECT md5(t::text) FROM asset_registry t") == reg_after


@requires_pg
def test_REAL_SQL_migration_1412_refuses_unrecognised_prior_states_and_leaves_the_rows_alone(pg):
    struck_sql = "SELECT count(*) FROM bg_transit_rules WHERE rule_type='double_transit' AND classical_citation LIKE " + _lit(STRUCK + "%")
    # (a) the stored check carries neither pin
    db = _db(pg); _registry(pg, db, _check_1320().replace(PIN_1320, "0" * 64), PRIOR_DESCRIPTION)
    r = _apply(pg, db)
    assert r.returncode != 0 and "migration 1412 refuses" in r.stderr
    assert q(pg, db, struck_sql) == "7" and q(pg, db, HASH_SQL) == PIN_1320
    # (b) the description is not migration 1079's text
    db = _db(pg); _registry(pg, db, _check_1320(), "some other description")
    r = _apply(pg, db)
    assert r.returncode != 0 and "english_description is not migration 1079" in r.stderr
    assert q(pg, db, struck_sql) == "7" and q(pg, db, HASH_SQL) == PIN_1320
    # (c) half-migrated: the rows already relabelled but the registry still on 1320's pin
    db = _db(pg); _registry(pg, db, _check_1320(), PRIOR_DESCRIPTION)
    r = psql(pg, db, "UPDATE bg_transit_rules SET classical_citation = " + _lit(RETIRED_CITATION) + " WHERE rule_type='double_transit'")
    assert r.returncode == 0, r.stderr
    r = _apply(pg, db)
    assert r.returncode != 0 and "expected all 7 double_transit rows to carry the struck citation" in r.stderr
    assert q(pg, db, "SELECT count(*) FROM asset_registry WHERE position(" + _lit(PIN_1320) + " IN integrity_check_sql) > 0") == "1"
