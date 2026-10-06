"""Citation Pass 2 (decision OS-2026-10-05-CITATIONS) applied to bg_vastu_directions: the Southwest / Rahu row.

Pinned offline and on a disposable Postgres (never the project database): the one row carries the decided K1 string and nothing else moves (the other seven
directions and all 24 remedial rows are hashed against pins); the Ldgr predicate of the census finds no placeholder citation in the seeded table; migration 1321
reseals the integrity pin (the PRE-change seed reproduces the pin migration 612 applied, so this reconstruction is faithful; the POST-change seed satisfies the
resealed stored check; the migration is idempotent and refuses an unrecognised prior state); the dispatch expected-change file loads and matches the rebuilt unit.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(REPO / "platform" / "scripts" / "governance"))

from brahmagyan import l0_vastu_directions as V  # noqa: E402
from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIG = REPO / "platform" / "migrations"
SUP = REPO / "platform" / "supabase" / "migrations"
F1304 = MIG / "1321_nirmana_l0_vastu_directions_citation_pass2_reseal.sql"
EC = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "citation_pass2" / "expected_change_bg_vastu_directions.json"

K1 = ('K1 — Muhurta Chintamani Gocara-prakaraṇa v.9 ṭīkā — muhurta_chintamani:PG66:C1 — "Mars\'s coral in the south, Rāhu\'s gomeda in the nairṛtya (south-west), '
      'Saturn\'s blue sapphire in the west" ; K1_ANALOGUE — Hora Sara Ch.2 translator\'s direction table — hora_sara:PG16:C1–PG17:C1 — "Rahu — South West '
      '(as per Brihat Jataka, Ch. II, sloka 6)" ; NOTE — Brihat Jataka II.6 mūla page not located in corpus this pass')
OLD_LABEL = "Vastu Shastra tradition (Nairitya corner)"
OLD_PIN = "1d18e307f87fa65932cb96ea4cff1dc8487262986ff5de4c969ab0b48497bb07"       # migration 612's applied pin for bg_vastu_directions
NEW_PIN = "27155f5759d7443900f3bb41bfa24356a7d4a68ba23086af0c1a6cf11eca90a2"       # the rebuilt content
REMEDIALS_PIN = "0c9c3378e7f7ddb5205996d6f1d0a1b9ef5e47b7334f65d0225c5c88f2cbffe7"  # unchanged by this PR
H_DIR = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(direction,direction_deg,ruling_graha,secondary_graha,favorable_color,element,"
         "classical_citation)::text, E'\\n' ORDER BY direction COLLATE \"C\"),''),'UTF8')),'hex') FROM bg_vastu_directions")
H_REM = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(direction,remedy_type,remedy_description,classical_citation)::text, "
         "E'\\n' ORDER BY direction COLLATE \"C\",remedy_type COLLATE \"C\"),''),'UTF8')),'hex') FROM bg_vastu_direction_remedials")


def _sw():
    return [d for d in V.VASTU_DIRECTIONS if d["direction"] == "Southwest"][0]


# ───────────────────────── pure: the seed ─────────────────────────

def test_the_southwest_row_carries_exactly_the_decided_k1_string_and_nothing_else_moves():
    sw = _sw()
    assert sw["classical_citation"] == K1 and sw["favorable_color"] is None                  # the colour stays NULL: no source, not invented
    assert (sw["direction_deg"], sw["ruling_graha"], sw["secondary_graha"], sw["element"]) == (225, "Rahu", None, "Earth")
    segs = [s.strip() for s in K1.split(" ; ")]
    assert [s.split(" — ")[0] for s in segs] == ["K1", "K1_ANALOGUE", "NOTE"] and "muhurta_chintamani:PG66:C1" in segs[0] and "hora_sara:PG16:C1" in segs[1]
    assert OLD_LABEL not in sw["classical_citation"]


def test_the_other_seven_directions_and_the_remedials_are_unchanged():
    assert len(V.VASTU_DIRECTIONS) == 8 and len(V.VASTU_DIRECTION_REMEDIALS) == 24
    rest = [d for d in V.VASTU_DIRECTIONS if d["direction"] != "Southwest"]
    assert all(d["classical_citation"] == V.MAYAMATA_CH6 for d in rest)
    blob = json.dumps([[d["direction"], d["direction_deg"], d["ruling_graha"], d["secondary_graha"], d["favorable_color"], d["element"], d["classical_citation"]]
                       for d in sorted(rest, key=lambda d: d["direction"])], ensure_ascii=False)
    assert hashlib.sha256(blob.encode("utf-8")).hexdigest() == PINNED_OTHER_SEVEN
    # the Southwest REMEDIAL row cites the same bare tradition label: not part of the decision, deliberately left (see E5.7/CITATION_AMBIGUOUS.md)
    sw_rem = [r for r in V.VASTU_DIRECTION_REMEDIALS if r["direction"] == "Southwest"]
    assert sw_rem and any(r["classical_citation"] == OLD_LABEL for r in sw_rem)
    assert V.VASTU_TRADITION == OLD_LABEL


def test_the_fingerprint_declarations_evidence_lines_still_name_the_write_statements():
    lines = (REPO / "platform" / "python-sidecar" / "brahmagyan" / "l0_vastu_directions.py").read_text(encoding="utf-8").splitlines()
    assert "INSERT INTO bg_vastu_directions" in lines[298] and "INSERT INTO bg_vastu_direction_remedials" in lines[320]


PINNED_OTHER_SEVEN = "a780349cdc4aad6cf4c20d5e2359a96c3d6c2c07ff2638b26976b76b6f4a5ef4"


# ───────────────────────── real SQL ─────────────────────────

def _db(pg_port):
    import psycopg2
    db = new_db(pg_port)
    t = (MIG / "284_bg_vastu_directions.sql").read_text(encoding="utf-8")
    for pat in (r"(CREATE TABLE IF NOT EXISTS bg_vastu_directions.*?\n\);)", r"(CREATE TABLE IF NOT EXISTS bg_vastu_direction_remedials.*?\n\);)"):
        r = psql(pg_port, db, re.search(pat, t, re.S).group(1)); assert r.returncode == 0, r.stderr
    conn = psycopg2.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db)
    try:
        V.seed_vastu_directions(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def _stored():
    """(the check migration 612 stored for bg_vastu_directions, 643's description): the registry state migration 1321 starts from."""
    t = (SUP / "612_nirmana_l0_vastu_medical_integrity_contract.sql").read_text(encoding="utf-8")
    chk = re.search(r"vastu_check constant text := \$check\$(.*?)\$check\$;", t, re.S).group(1)
    t643 = (MIG / "643_nirmana_l0_w3_batch2_registry_accuracy.sql").read_text(encoding="utf-8")
    blk = t643[:t643.index("WHERE asset_id = 'bg_vastu_directions'")]
    blk = blk[blk.rindex("SET english_description ="):]
    desc = "".join(re.findall(r"'((?:[^']|'')*)'", blk)).replace("''", "'")
    return chk, desc


def _registry(pg, db, chk, desc):
    r = psql(pg, db, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, english_description text)"); assert r.returncode == 0, r.stderr
    r = psql(pg, db, "INSERT INTO asset_registry VALUES ('bg_vastu_directions', $c$" + chk + "$c$, $d$" + desc + "$d$)"); assert r.returncode == 0, r.stderr


@requires_pg
def test_REAL_SQL_the_seeded_table_hashes_to_the_new_pin_and_the_pre_change_state_is_what_612_applied(pg):
    db = _db(pg)
    chk, _ = _stored()
    assert OLD_PIN in chk and REMEDIALS_PIN in chk
    assert q(pg, db, H_DIR) == NEW_PIN and q(pg, db, H_REM) == REMEDIALS_PIN
    assert q(pg, db, "SELECT count(*) FROM bg_vastu_directions") == "8" and q(pg, db, "SELECT count(*) FROM bg_vastu_direction_remedials") == "24"
    assert q(pg, db, chk.strip().rstrip(";")) == "f"                                           # the stored (old-pin) check is FALSE on the corrected row
    r = psql(pg, db, "UPDATE bg_vastu_directions SET classical_citation = '" + OLD_LABEL + "' WHERE direction = 'Southwest'"); assert r.returncode == 0
    assert q(pg, db, H_DIR) == OLD_PIN                                                         # reconstruction fidelity: the pre-change content IS the applied pin
    assert q(pg, db, chk.strip().rstrip(";")) == "t"


@requires_pg
def test_REAL_SQL_migration_1321_reseals_the_pin_and_the_stored_check_holds_on_the_rebuilt_rows(pg):
    db = _db(pg)
    chk, desc = _stored()
    _registry(pg, db, chk, desc)
    r = psql(pg, db, file=F1304); assert r.returncode == 0, r.stderr
    new_chk = q(pg, db, "SELECT integrity_check_sql FROM asset_registry")
    assert NEW_PIN in new_chk and OLD_PIN not in new_chk and REMEDIALS_PIN in new_chk
    assert new_chk == chk.strip().replace(OLD_PIN, NEW_PIN)                                    # ONLY the directions hash changed
    assert q(pg, db, new_chk.rstrip(";")) == "t"
    d = q(pg, db, "SELECT english_description FROM asset_registry")
    assert d.startswith(desc.split("(Mayamata Ch.6)")[0]) and "OS-2026-10-05-CITATIONS" in d and d.endswith("(24 rows) with 2-3 remedies per direction.")
    before = q(pg, db, "SELECT md5(integrity_check_sql || english_description) FROM asset_registry")
    r = psql(pg, db, file=F1304); assert r.returncode == 0, r.stderr                           # idempotent
    assert q(pg, db, "SELECT md5(integrity_check_sql || english_description) FROM asset_registry") == before


@requires_pg
def test_REAL_SQL_migration_1321_refuses_an_unrecognised_pin_and_only_notices_a_changed_description(pg):
    chk, desc = _stored()
    db = _db(pg)
    _registry(pg, db, chk.replace(OLD_PIN, "0" * 64), desc)
    r = psql(pg, db, file=F1304)
    assert r.returncode != 0 and "refuses" in r.stderr
    # a description someone else changed is a COSMETIC drift: NOTICE and leave it, still reseal the pin (never block a deploy over prose)
    db2 = _db(pg)
    _registry(pg, db2, chk, desc + " edited")
    r = psql(pg, db2, file=F1304)
    assert r.returncode == 0 and "left as stored" in r.stderr
    assert q(pg, db2, "SELECT english_description FROM asset_registry") == desc + " edited"
    assert NEW_PIN in q(pg, db2, "SELECT integrity_check_sql FROM asset_registry")


@requires_pg
def test_REAL_SQL_the_census_ldgr_predicate_finds_no_placeholder_citation_in_bg_vastu_directions(pg):
    import asset_census as ac
    db = _db(pg)
    lacking = ac._ldgr_lacking("classical_citation", "text")
    assert q(pg, db, f"SELECT count(*) FILTER (WHERE {lacking}) FROM bg_vastu_directions") == "0"
    r = psql(pg, db, "UPDATE bg_vastu_directions SET classical_citation = '" + OLD_LABEL + "' WHERE direction = 'Southwest'"); assert r.returncode == 0
    assert q(pg, db, f"SELECT count(*) FILTER (WHERE {lacking}) FROM bg_vastu_directions") == "1"     # not vacuous: the old bare label IS the placeholder the census counted


@requires_pg
def test_REAL_SQL_the_expected_change_file_is_loadable_and_its_fingerprint_is_the_rebuilt_unit(pg):
    import fingerprint_declarations as fd
    import psycopg
    import suvarna_global_asset_dispatch as gad
    spec, _sha = gad.load_expected_change(str(EC), "bg_vastu_directions")
    db = _db(pg)
    decls = gad.load_declarations_or_refuse(fd.DEFAULT_DECLARATIONS)
    unit = gad.declared_unit_or_refuse(decls, "bg_vastu_directions", gad.writer_siblings(str(REPO), "bg_vastu_directions"))

    def connect():
        c = psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db)
        c.autocommit = False
        c.read_only = True
        return c
    post = gad.read_fingerprint(connect, decls, unit)
    print("UNIT", unit, "COMPOSITE", post["composite"], {t: v["rows"] for t, v in post["tables"].items()})
    assert sum(v["rows"] for v in post["tables"].values()) == spec["expected_post_row_count"] == 32
    assert post["composite"] == spec["expected_post_fingerprint"] and spec["decision"] == "OS-2026-10-05-CITATIONS"
