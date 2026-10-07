"""CITATION-PASS2 (decision OS-2026-10-05-CITATIONS) — bg_ontology: the dosha partition of brahma_ontology and migration 1325.

The 53 brahma_ontology entity_class=dosha rows of PASS2_DECISIONS.tsv are written by the bg_doshas writer (seed_doshas); bg_ontology's own writer (seed_ontology) leaves the 'dosha' class to
that co-writer. LIVE tier on a DISPOSABLE local PostgreSQL (skipped loudly without server binaries): the REAL seed_ontology and seed_doshas fill brahma_ontology twice (authored dosha list vs
the pass-2 list); rows are compared by natural key (entity_class, canonical_id). Then the REAL migration 1325 is applied to a registry row carrying migration 606's text.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

import psycopg
import pytest
from psycopg.rows import dict_row

from brahmagyan import l0_doshas, l0_ontology
from tests._citation_pass2_ldgr import citation_lacks_source
from tests.pg_disposable import new_db, psql, q, pg  # noqa: F401  (pg is a fixture)

_REPO = pathlib.Path(__file__).resolve().parents[4]
_MIG = _REPO / "platform" / "migrations" / "1325_bg_ontology_citation_pass2_integrity_reseal.sql"
_M606 = _REPO / "platform" / "supabase" / "migrations" / "606_nirmana_l0_wave0_integrity_contracts.sql"
OLD_TEXT = re.search(r"ontology_check CONSTANT TEXT := \$check\$(.*?)\$check\$;", _M606.read_text(), re.S).group(1)
NEW_TEXT = re.search(r"\$ic\$(.*?)\$ic\$", _MIG.read_text(), re.S).group(1)
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

REMOVED = {f"kala_sarpa_{v}" for v in ("anant", "kulik", "vasuki", "shankhpal", "padma", "mahapadma", "takshak", "karkotak", "shankhachud", "ghatak", "vishdhar", "sheshnag")} | {"vish_dosha"}
DDL = """
CREATE TABLE brahma_dosha_catalog(canonical_id text primary key,name_sa text,name_en text,category text,formation_rule_jsonb jsonb,formation_text text,effects_text text,severity_grades jsonb,cancellation_conditions jsonb,classical_citations jsonb,source_chunk_ids bigint[],associated_remedies uuid[],school text,created_at timestamptz);
CREATE TABLE brahma_ontology(entity_class text,canonical_id text,canonical_name_en text,canonical_name_sa text,synonyms text[],description text,source_citation text,created_at timestamptz,primary key(entity_class,canonical_id));
CREATE TABLE reference_doshas(canonical_id text primary key,name_en text,category text);
CREATE TABLE asset_registry(asset_id text primary key, integrity_check_sql text, target_floor bigint, volume_explanation text);
"""
COLS = "entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation"


def _db(port):
    db = new_db(port)
    assert psql(port, db, DDL).returncode == 0
    return db, psycopg.connect(f"host=127.0.0.1 port={port} user=postgres dbname={db}", row_factory=dict_row)


def _seed(conn, authored: bool, monkeypatch):
    if authored:
        monkeypatch.setattr(l0_doshas, "pass2_doshas", lambda: [dict(d) for d in l0_doshas.DOSHAS])
    l0_ontology.seed_ontology(conn, autocommit=False)
    l0_doshas.seed_doshas(conn, autocommit=False)
    conn.commit()
    with conn.cursor() as c:
        c.execute(f"SELECT {COLS} FROM brahma_ontology ORDER BY entity_class COLLATE \"C\", canonical_id COLLATE \"C\"")
        return {(r["entity_class"], r["canonical_id"]): r for r in c.fetchall()}


@pytest.fixture
def both(pg, monkeypatch):
    out = {}
    for name, authored in (("before", True), ("after", False)):
        db, conn = _db(pg)
        try:
            out[name] = _seed(conn, authored, monkeypatch)
        finally:
            conn.close()
        monkeypatch.undo()
    return out


def test_ontology_total_falls_by_exactly_the_13_removed_dosha_nodes(both):
    b, a = both["before"], both["after"]
    assert len(b) - len(a) == 13
    assert {k for k in b if k not in a} == {("dosha", c) for c in REMOVED} | {("dosha", "kemadruma_compat_kuja")}
    assert {k for k in a if k not in b} == {("dosha", "kuja_dosha_from_venus")}


def test_every_non_dosha_class_is_byte_identical(both):
    b, a = both["before"], both["after"]
    for k, row in a.items():
        if k[0] != "dosha":
            assert row == b[k], k
    assert sum(1 for k in a if k[0] != "dosha") == sum(1 for k in b if k[0] != "dosha")


def test_the_26_undecided_dosha_rows_are_identical_and_the_decided_ones_carry_a_real_source(both):
    from brahmagyan import citation_pass2_doshas as C
    b, a = both["before"], both["after"]
    decided = set(C.PASS2_DOSHA_EDITS)
    for k, row in a.items():
        if k[0] != "dosha" or k[1] == "kuja_dosha_from_venus":
            continue
        if k[1] in decided:
            assert row["source_citation"] != b[k]["source_citation"], k
            assert not citation_lacks_source(row["source_citation"]), k
            assert row["source_citation"].startswith(("K1 — ", "K2 — ", "K1_UNVERIFIED — ")), k
        else:
            assert row == b[k], k
    assert len([k for k in a if k[0] == "dosha"]) == 66 and len(decided) == 40


def test_ontology_dosha_rows_mirror_the_catalog_name_and_effects(both):
    for (ec, cid), row in both["after"].items():
        if ec != "dosha":
            continue
        d = next(x for x in l0_doshas.pass2_doshas() if x["canonical_id"] == cid)
        assert row["canonical_name_en"] == d["name_en"] and row["canonical_name_sa"] == d["name_sa"]
        assert row["description"] == (d["effects_text"][:200] if d.get("effects_text") else None)


def test_punarphoo_node_absorbs_vish_dosha_and_the_rename(both):
    a = both["after"]
    assert a[("dosha", "punarphoo")]["synonyms"] == ["vish_dosha", "Vish Dosha", "Punarphoo", "Chandra-Shani yuti"]
    assert a[("dosha", "punarphoo")]["canonical_name_en"] == 'Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")'
    assert ("dosha", "vish_dosha") not in a
    n = a[("dosha", "kuja_dosha_from_venus")]
    assert n["canonical_name_sa"] == "Śukrāt Kuja-doṣa" and n["source_citation"].startswith("K1_UNVERIFIED — ")
    assert [k for k, r in a.items() if k[0] == "dosha" and r["synonyms"]] == [("dosha", "punarphoo")]


def test_source_citation_text_carries_machine_and_human_locus_for_k1_rows(both):
    for cid in ("dhaiya", "sade_sati", "varna_dosha", "nadi_dosha", "mool_dosha", "bhakoot_dosha", "daridra"):
        txt = both["after"][("dosha", cid)]["source_citation"]
        assert re.search(r" — (phaladeepika|bphs|muhurta_chintamani|jataka_parijata):PG\d+:C\d+", txt), cid
        assert txt.startswith("K1 — ")
    assert "OS-2026-10-05-CITATIONS" in both["after"][("dosha", "angarak")]["source_citation"]


# ---- migration 1325 ----------------------------------------------------------------------------------------------------

def _check(conn, sql) -> bool:
    with conn.cursor() as c:
        c.execute(sql)
        return list(c.fetchone().values())[0] is True


def test_static_texts_and_the_single_replacement():
    assert md5(OLD_TEXT) == "5fc7ea8d12969043a8258696cebcc1bc" and md5(NEW_TEXT) == "dad6e9189baa2ccda4579aaf36e07bad"
    assert NEW_TEXT == OLD_TEXT.replace("COUNT(*) >= 737", "COUNT(*) >= 728") and OLD_TEXT.count("COUNT(*) >= 737") == 1


def test_live_floor_checks_the_rebuilt_table_and_still_bites(pg, monkeypatch):
    db, conn = _db(pg)
    try:
        rows = _seed(conn, False, monkeypatch)
        with conn.cursor() as c:
            for i in range(728 - len(rows)):                      # the yoga / dasha_system co-writers' classes, stood in for by filler rows
                c.execute("INSERT INTO brahma_ontology VALUES ('yoga', %s, 'f', 'f', '{}', NULL, 'f', now())", (f"zz_filler_{i}",))
        conn.commit()
        assert _check(conn, NEW_TEXT) is True and _check(conn, OLD_TEXT) is False        # 728 rows: the old 737 floor would fail, the new one holds
        with conn.cursor() as c:
            c.execute("DELETE FROM brahma_ontology WHERE canonical_id = 'zz_filler_0'")
        assert _check(conn, NEW_TEXT) is False                                            # 727: the floor still bites
        conn.rollback()
        with conn.cursor() as c:
            c.execute("UPDATE brahma_ontology SET source_citation = NULL WHERE canonical_id = 'angarak'")
        assert _check(conn, NEW_TEXT) is False                                            # the NOT NULL conjunct is unchanged
        conn.rollback()
    finally:
        conn.close()


def test_live_migration_applies_once_is_guarded_and_idempotent(pg):
    db, conn = _db(pg)
    with conn.cursor() as c:
        c.execute("INSERT INTO asset_registry VALUES ('bg_ontology', %s, 737, 'old')", (OLD_TEXT,))
    conn.commit()
    conn.close()
    r = psql(pg, db, file=_MIG, single_transaction=True)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql)||' '||target_floor FROM asset_registry WHERE asset_id='bg_ontology'") == "dad6e9189baa2ccda4579aaf36e07bad 728"
    r2 = psql(pg, db, file=_MIG, single_transaction=True)
    assert r2.returncode == 0 and "already carries the citation-pass-2 floor" in r2.stderr
    db2 = new_db(pg)
    assert psql(pg, db2, DDL).returncode == 0
    assert psql(pg, db2, "INSERT INTO asset_registry VALUES ('bg_ontology','SELECT true',737,'x')").returncode == 0
    r3 = psql(pg, db2, file=_MIG, single_transaction=True)
    assert r3.returncode == 0 and "NO-OP" in r3.stderr
    assert psql(pg, db2, "UPDATE asset_registry SET integrity_check_sql = $t$" + OLD_TEXT + "$t$, target_floor = 999").returncode == 0
    r4 = psql(pg, db2, file=_MIG, single_transaction=True)
    assert r4.returncode != 0 and "update did not take" in r4.stderr



def test_there_is_no_ontology_expected_change_file():
    """SS 2026-10-05: the dosha partition moves in the bg_doshas rebuild, so a bg_ontology expected-change dispatch could never be MET; bg_ontology runs in the default mode afterwards."""
    assert not (_REPO / "00_ARCHITECTURE" / "control" / "expected_change" / "EXPECTED_CHANGE_bg_ontology_citation_pass2.json").exists()
    assert "NO expected-change file" in _MIG.read_text()
