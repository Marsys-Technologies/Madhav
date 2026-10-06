"""Citation Pass 2 (decision OS-2026-10-05-CITATIONS) applied to bg_transit_rules: the six Rahu/Ketu house-vedha rows.

What this pins, offline and on a disposable Postgres (never the project database):
  * the six rows (graha rahu/ketu x primary_house 3/6/11, rule_type favourable) carry the SS-ruled FORM (b) citation (starts with UNSOURCED for the vedha partner,
    then the K1 transit result with its machine locus and excerpt) and the decided rule_notes clause; the vedha loader (services/gochara_rules/vedha_derive.py)
    accepts the rebuilt rows and returns the same pairs; EVERY other seed row is unchanged (the seed is hashed against a pin) and no row is added or removed;
  * the Ldgr detector reads no placeholder among the six (the census's real SQL predicate, run on the seeded table);
  * migration 1320 reseals the integrity pin: the PRE-change seed reproduces the pin applied by migration 1078 (so the table
    reconstruction here is faithful to production), the POST-change seed satisfies the resealed stored check, the migration is
    idempotent and refuses an unrecognised prior state.
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
sys.path.insert(0, str(HERE.parents[2]))                                  # platform/python-sidecar
sys.path.insert(0, str(REPO / "platform" / "scripts" / "governance"))     # the census (asset_census.py)

from brahmagyan import l0_transit as T  # noqa: E402
from tests.pg_disposable import HAVE_PG, new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIG = REPO / "platform" / "migrations"
SUP = REPO / "platform" / "supabase" / "migrations"
F1303 = MIG / "1320_nirmana_l0_transit_rules_citation_pass2_reseal.sql"

VE = "UNSOURCED (vedha partner: inference, not in the cited verses) \u2014 transit result: "
# Both verses are named on ALL six rows, as the decision TSV has it: sl.2 (PG321, the nodes are like the Sun) and sl.24 (PG331, Rahu's transit effects). The census shape allows ONE bracketed machine locus:
# the verse that states the row's own house result (sl.24 for Rahu, sl.2 for Ketu); the other verse's locus is named in the locus words. Excerpts are sub-sequences of the decision's quotations (<= 25 words).
WORDS = "Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects)"
SUN36 = "Sun ... in the 6th, 3rd and 10th ..."
SUN11 = "all planets in the 11th ..."
TAIL = "Rahu and Ketu are similar to the Sun; effects caused by Rahu ... ({h}) happiness"


def _cite(g, h):
    loc = "phaladeepika:PG331:C1" if g == "rahu" else "phaladeepika:PG321:C1"
    return VE + f'{WORDS} [machine locus {loc}] "' + (SUN11 if h == 11 else SUN36) + " " + TAIL.format(h=h) + '"'


EXPECTED = {   # (graha, primary_house) -> the citation (form (b)); excerpts are sub-sequences of the quotations the decision records
    ("rahu", 3): _cite("rahu", 3), ("rahu", 6): _cite("rahu", 6), ("rahu", 11): _cite("rahu", 11),
    ("ketu", 3): _cite("ketu", 3), ("ketu", 6): _cite("ketu", 6), ("ketu", 11): _cite("ketu", 11),
}
# a copy of asset_census.SPLIT_SHAPE_RE (suvarna/engine-ldgr-split-citation): the shape the census judges on the K1 part; checked against the engine's own constant when it is present
SHAPE = re.compile(r'^UNSOURCED \(vedha partner: ([^()]{1,200})\) — transit result: ([^\[\]"]{3,200}) \[machine locus ([a-z][a-z0-9_]*):PG([0-9]{1,4}):C([0-9]{1,2})\] "([^"]{1,255})"$')
NOTE_CLAUSE = "disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence"
SIX = {("rahu", 3), ("rahu", 6), ("rahu", 11), ("ketu", 3), ("ketu", 6), ("ketu", 11)}
OLD_PIN = "1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d"      # migration 1078's applied pin
NEW_PIN = "dce17ed02e1ba05eb4db5d0a46777a70c1f5832160fa3add253f7119bbf7ea8d"      # the rebuilt content (this PR)
RULES_HASH_SQL = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,classical_citation,rule_notes)::text,"
                  " E'\\n' ORDER BY graha COLLATE \"C\",rule_type COLLATE \"C\",primary_house),''),'UTF8')),'hex') FROM bg_transit_rules")


def _six():
    return [r for r in T.BG_TRANSIT_RULES if r["rule_type"] == "favourable" and (r["graha"], r["primary_house"]) in SIX]


# ───────────────────────── pure: the seed ─────────────────────────

def test_the_six_rows_carry_the_form_b_citation_and_note_clause():
    rows = _six()
    assert len(rows) == 6 and {(r["graha"], r["primary_house"]) for r in rows} == SIX
    for r in rows:
        assert r["classical_citation"] == EXPECTED[(r["graha"], r["primary_house"])], (r["graha"], r["primary_house"])
        assert NOTE_CLAUSE in r["rule_notes"] and "unsourced" not in r["rule_notes"].lower()
        assert r["rule_notes"].startswith(("Rahu", "Ketu")) and "L0 repair item 3: vedha_house retained" in r["rule_notes"]
    assert {(r["graha"], r["primary_house"]): r["vedha_house"] for r in rows} == {("rahu", 3): 9, ("rahu", 6): 12, ("rahu", 11): 5, ("ketu", 3): 9, ("ketu", 6): 12, ("ketu", 11): 5}


def test_the_form_b_text_has_the_shape_the_census_judges_and_the_vedha_field_is_not_cited():
    for (g, ph), text in EXPECTED.items():
        m = SHAPE.match(text)
        assert m, text
        _vedha, locus_words, text_id, page, chunk, excerpt = m.groups()
        assert text.startswith("UNSOURCED") and len(excerpt.split()) <= 25
        assert (text_id, page, chunk) == ("phaladeepika", "331" if g == "rahu" else "321", "1")           # the chunk the pass-2 read resolved: phaladeepika_pg0331_c01 / pg0321_c01
        assert "phaladeepika:PG321:C1" in locus_words and "phaladeepika:PG331:C1" in locus_words and "Śl. 2 / 24" in locus_words   # BOTH verses on every row (decision TSV)
        assert "vedha_house" not in text and "PG322" not in text and "PG323" not in text                    # the vedha field is never cited
    try:
        import asset_census as ac
    except ImportError:
        return
    if hasattr(ac, "SPLIT_SHAPE_RE"):
        assert ac.SPLIT_SHAPE_RE == SHAPE.pattern


def test_the_old_constant_is_gone():
    assert not hasattr(T, "RAHU_KETU_HOUSE_VEDHA_UNSOURCED")


# ───────────────────────── real SQL: the seeded tables ─────────────────────────

def _db(pg_port):
    """A database holding the three transit tables as production does: the DDL of migrations 266 / 397 / 401, migration 397's seven double_transit rows, then the seed."""
    import psycopg2
    import psycopg2.extras
    db = new_db(pg_port)
    t266 = (MIG / "266_bg_transit_tables.sql").read_text(encoding="utf-8")
    for pat in (r"(CREATE TABLE IF NOT EXISTS bg_transit_engine.*?\);)\s*COMMENT ON TABLE bg_transit_engine", r"(CREATE TABLE IF NOT EXISTS bg_transit_rules.*?\n\);)"):
        r = psql(pg_port, db, re.search(pat, t266, re.S).group(1)); assert r.returncode == 0, r.stderr
    t397 = (SUP / "397_bg_transit_av_gates.sql").read_text(encoding="utf-8")
    r = psql(pg_port, db, "ALTER TABLE bg_transit_rules DROP CONSTRAINT IF EXISTS bg_transit_rules_rule_type_check; ALTER TABLE bg_transit_rules ADD CONSTRAINT "
                          "bg_transit_rules_rule_type_check CHECK (rule_type IN ('favourable','unfavourable','vedha','double_transit'));"); assert r.returncode == 0, r.stderr
    r = psql(pg_port, db, re.search(r"(INSERT INTO bg_transit_rules .*?ON CONFLICT \(graha, rule_type, primary_house\) DO NOTHING;)", t397, re.S).group(1)); assert r.returncode == 0, r.stderr
    t401 = (SUP / "401_bg_transit_moorti.sql").read_text(encoding="utf-8")
    r = psql(pg_port, db, re.search(r"(CREATE TABLE IF NOT EXISTS bg_transit_moorti.*?\n\);)", t401, re.S).group(1)); assert r.returncode == 0, r.stderr
    conn = psycopg2.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        T.seed_transit_rules(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def _stored_checks():
    """(the check migration 1078 stored, 1079's description): the registry state migration 1320 starts from."""
    t = (SUP / "1078_nirmana_l0_transit_rules_integrity_reseal.sql").read_text(encoding="utf-8")
    chk = re.search(r"new_rules_check constant text := \$check\$(.*?)\$check\$;", t, re.S).group(1)
    t79 = (SUP / "1079_nirmana_l0_transit_rules_description_truthfulness.sql").read_text(encoding="utf-8")
    desc = re.search(r"truthful_description constant text :=\s*'(.*?)';\n", t79, re.S).group(1).replace("''", "'")
    return chk, desc


@requires_pg
def test_REAL_SQL_the_seeded_rows_hash_to_the_new_pin_and_the_pre_change_pin_is_what_1078_applied(pg):
    db = _db(pg)
    chk, _ = _stored_checks()
    assert OLD_PIN in chk                                                                 # 1078 pinned the pre-change content
    assert q(pg, db, RULES_HASH_SQL) == NEW_PIN
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules") == "76"
    assert q(pg, db, "SELECT count(*) FILTER (WHERE rule_type='favourable'), count(*) FILTER (WHERE rule_type='unfavourable'), count(*) FILTER (WHERE rule_type='double_transit') FROM bg_transit_rules") == "43|26|7"
    # reconstruction fidelity: put the six rows back to their pre-change text and the table must hash to the pin 1078 applied (the engine and moorti parts of the stored check hold too)
    assert q(pg, db, chk.strip().rstrip(";")) == "f"                                      # the stored (old-pin) check is FALSE on the corrected rows
    r = psql(pg, db, "UPDATE bg_transit_rules SET classical_citation = 'UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, "
                     "phaladeepika:PG322:C1-PG323:C1, name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) "
                     "and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.', "
                     "rule_notes = replace(rule_notes, '" + NOTE_CLAUSE.replace("'", "''") + "', 'disposition unsourced (never a claimed-cited nullification)') "
                     "WHERE rule_type = 'favourable' AND graha IN ('rahu','ketu') AND primary_house IN (3,6,11)")
    assert r.returncode == 0, r.stderr
    assert q(pg, db, RULES_HASH_SQL) == OLD_PIN
    assert q(pg, db, chk.strip().rstrip(";")) == "t"                                      # the applied 1078 check holds on the reconstructed PRE state


def _registry(pg, db, chk, desc, floor=76):
    r = psql(pg, db, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, english_description text, target_floor int)"); assert r.returncode == 0, r.stderr
    r = psql(pg, db, "INSERT INTO asset_registry VALUES ('bg_transit_rules', $c$" + chk + "$c$, $d$" + desc + "$d$, " + str(floor) + ")"); assert r.returncode == 0, r.stderr


@requires_pg
def test_REAL_SQL_migration_1320_reseals_the_pin_and_the_stored_check_holds_on_the_rebuilt_rows(pg):
    db = _db(pg)
    chk, desc = _stored_checks()
    _registry(pg, db, chk, desc)
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry").strip().rstrip(";") and q(pg, db, chk.strip().rstrip(";")) == "f"
    r = psql(pg, db, file=F1303); assert r.returncode == 0, r.stderr
    new_chk = q(pg, db, "SELECT integrity_check_sql FROM asset_registry")
    assert NEW_PIN in new_chk and OLD_PIN not in new_chk
    assert new_chk == chk.strip().replace(OLD_PIN, NEW_PIN)                                  # ONLY the hash changed
    assert q(pg, db, new_chk.rstrip(";")) == "t"                                            # the resealed stored check holds on the rebuilt content
    # english_description is NOT touched (SS / Pravaha rule: leave it UNCHANGED; it still matches platform/scripts/seed/asset_registry_seed.ts)
    assert q(pg, db, "SELECT english_description FROM asset_registry") == desc
    # idempotent: a second application changes nothing and does not raise
    before = q(pg, db, "SELECT md5(integrity_check_sql || english_description) FROM asset_registry")
    r = psql(pg, db, file=F1303); assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql || english_description) FROM asset_registry") == before


@requires_pg
def test_REAL_SQL_migration_1320_refuses_an_unrecognised_prior_state(pg):
    db = _db(pg)
    chk, desc = _stored_checks()
    _registry(pg, db, chk.replace(OLD_PIN, "0" * 64), desc)                                  # a pin that is neither the old nor the new one
    r = psql(pg, db, file=F1303)
    assert r.returncode != 0 and "refuses" in r.stderr
    assert "english_description" not in F1303.read_text(encoding="utf-8").split("DO $$", 1)[1]      # the migration never reads or writes the description


# ───────────────────────── the Ldgr detector, offline (the census's own SQL predicate on the seeded table) ─────────────────────────

@requires_pg
def test_REAL_SQL_the_generic_ldgr_predicate_flags_only_the_six_and_the_declared_split_reads_them_as_sourced(pg):
    """The census's generic placeholder predicate treats a string starting with UNSOURCED as a placeholder: exactly the six rows (form (b) keeps the prefix on purpose, the vedha loader
    needs it). They are read as sourced ONLY through the declared `split_citation` exception of the engine (suvarna/engine-ldgr-split-citation: the transit result must resolve to a
    corpus chunk); that half of the test runs when the engine code is present."""
    import asset_census as ac
    db = _db(pg)
    lacking = ac._ldgr_lacking("classical_citation", "text")
    assert q(pg, db, f"SELECT count(*) FROM bg_transit_rules WHERE {lacking}") == "6"
    assert q(pg, db, f"SELECT string_agg(graha || primary_house, ',' ORDER BY graha, primary_house) FROM bg_transit_rules WHERE {lacking}") == "ketu3,ketu6,ketu11,rahu3,rahu6,rahu11"
    if not hasattr(ac, "_split_selected"):
        pytest.skip("the engine's split_citation is not in this checkout (branch suvarna/engine-ldgr-split-citation); that branch's test_ldgr_split_citation.py runs the same six seed texts through the engine")
    r = psql(pg, db, "CREATE TABLE classical_text_chunks (chunk_id text); INSERT INTO classical_text_chunks VALUES ('phaladeepika_pg0331_c01'), ('phaladeepika_pg0321_c01');")
    assert r.returncode == 0, r.stderr
    entry = {"column": "classical_citation", "kinds": ["K1"], "split_citation": {
        "vedha_prefix": "UNSOURCED (vedha partner:", "applies_to": [{"column": "rule_type", "equals": "favourable"}, {"column": "graha", "in": ["rahu", "ketu"]}, {"column": "vedha_house", "not_null": True}],
        "why": "vedha partner unsourced, awaiting the owner ruling ND-NODE-VEDHA", "evidence": "platform/python-sidecar/services/gochara_rules/vedha_derive.py:129"}}
    pred, why = ac._source_entry_lacking_core(entry, {"classical_citation": "text"})
    assert why is None and q(pg, db, f"SELECT count(*) FROM bg_transit_rules WHERE {pred}") == "0"
    r = psql(pg, db, "DELETE FROM classical_text_chunks WHERE chunk_id = 'phaladeepika_pg0331_c01'"); assert r.returncode == 0
    assert q(pg, db, f"SELECT count(*) FROM bg_transit_rules WHERE {pred}") == "3"          # the three Rahu rows cite a locus that no longer resolves: lacking


def test_the_seed_hash_pin_for_every_unchanged_row():
    """Every row other than the six is byte-for-byte what the repo seeded before this change: one hash over the 63 other writer-owned rows."""
    rest = [r for r in T.BG_TRANSIT_RULES if not (r["rule_type"] == "favourable" and (r["graha"], r["primary_house"]) in SIX)]
    assert len(rest) == 63
    blob = json.dumps([[r["rule_type"], r["graha"], r["primary_house"], r.get("vedha_house"), r["phala"], r["classical_citation"], r.get("rule_notes")] for r in sorted(
        rest, key=lambda r: (r["graha"], r["rule_type"], r["primary_house"]))], ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(blob.encode("utf-8")).hexdigest() == PINNED_OTHER_ROWS


PINNED_OTHER_ROWS = "f0ee32798309dc41ba900caf7f2a4f383c32f1a72ddd3d7641a8a87a92b4468d"


# ───────────────────────── the vedha loader (Pravaha) accepts the rebuilt rows and returns the same pairs ─────────────────────────

OLD_NODE_TEXT = ("UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1, "
                 "name only the seven classical grahas; BPHS Ch.29 does not exist in this corpus). Retained per B.10 (writers emit, serve-time governs; never silently dropped) "
                 "and Gochara N-14 (no graha-drishti cast from the nodes) — see KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.5.")


def _load(pg, db):
    import psycopg2
    from services.gochara_rules import vedha_derive as vd
    conn = psycopg2.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db)
    try:
        return vd.load_pairs(conn.cursor())
    finally:
        conn.close()


@requires_pg
def test_REAL_SQL_the_vedha_loader_accepts_the_rebuilt_rows_and_every_checked_field_is_unchanged(pg):
    """`pairs_from_rows` run on the rebuilt table (the real loader, its real SQL): no VedhaPairsError, the same 36 classical pairs and 3 + 3 node rows (census total 42), the same
    mapping as on the PRE-change rows. The citation text sits inside `pairs_content_digest`, so that digest differs: said so in the PR body."""
    db = _db(pg)
    post = _load(pg, db)
    assert len(post) == 36 and post.census == {"classical": {"Sun": 4, "Moon": 6, "Mars": 3, "Mercury": 6, "Jupiter": 5, "Venus": 9, "Saturn": 3}, "node_rows": {"Rahu": 3, "Ketu": 3}, "total": 42}
    r = psql(pg, db, "UPDATE bg_transit_rules SET classical_citation = $o$" + OLD_NODE_TEXT + "$o$ WHERE rule_type = 'favourable' AND graha IN ('rahu','ketu') AND primary_house IN (3,6,11)")
    assert r.returncode == 0, r.stderr
    pre = _load(pg, db)
    assert dict(pre) == dict(post) and pre.census == post.census                       # every field the loader checks, and the pairs it returns, are the same
    assert pre.content_digest != post.content_digest and len(post.content_digest) == 64   # the text IS in the digest (L0 binding of the AM-16 input vector)
    # the unchanged checked fields, row by row
    assert q(pg, db, "SELECT count(*) FROM bg_transit_rules WHERE vedha_house IS NOT NULL") == "42"
    assert q(pg, db, "SELECT string_agg(graha || primary_house || ':' || vedha_house || rule_type, ',' ORDER BY graha, primary_house) FROM bg_transit_rules WHERE graha IN ('rahu','ketu') AND vedha_house IS NOT NULL") \
        == "ketu3:9favourable,ketu6:12favourable,ketu11:5favourable,rahu3:9favourable,rahu6:12favourable,rahu11:5favourable"


@requires_pg
def test_REAL_SQL_the_loader_still_refuses_a_node_row_that_does_not_start_with_unsourced(pg):
    """Why the citation MUST start with UNSOURCED: a node row cited any other way refuses the whole load (ND-NODE-VEDHA is open)."""
    from services.gochara_rules import vedha_derive as vd
    db = _db(pg)
    r = psql(pg, db, "UPDATE bg_transit_rules SET classical_citation = 'K1 — ' || classical_citation WHERE graha = 'rahu' AND primary_house = 3 AND rule_type = 'favourable'")
    assert r.returncode == 0, r.stderr
    with pytest.raises(vd.VedhaPairsError, match="ND-NODE-VEDHA"):
        _load(pg, db)


# ───────────────────────── the dispatch expected-change file ─────────────────────────

EC = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "citation_pass2" / "expected_change_bg_transit_rules.json"


def test_the_fingerprint_declarations_evidence_lines_still_name_the_write_statements():
    """FINGERPRINT_DECLARATIONS.json cites the INSERT / DELETE statements of this seed BY LINE NUMBER (1077, 1102, 1145, 1186): an edit above them must not move them."""
    lines = (REPO / "platform" / "python-sidecar" / "brahmagyan" / "l0_transit.py").read_text(encoding="utf-8").splitlines()
    assert "INSERT INTO bg_transit_engine" in lines[1076] and "INSERT INTO bg_transit_rules" in lines[1101]
    assert "DELETE FROM bg_transit_rules" in lines[1144] and "INSERT INTO bg_transit_moorti" in lines[1185]


@requires_pg
def test_REAL_SQL_the_expected_change_file_is_loadable_and_its_fingerprint_is_the_rebuilt_unit(pg):
    """The file the operator passes to `--expected-change`: it loads through the dispatch tool's own loader, and its row count and fingerprint are what the tool's
    fingerprint reader returns on the rebuilt tables (the unit of bg_transit_rules is the group grp_bg_transit_seed: rules 76 + engine 9 + moorti 27)."""
    import fingerprint_declarations as fd
    import psycopg
    import suvarna_global_asset_dispatch as gad
    spec, _sha = gad.load_expected_change(str(EC), "bg_transit_rules")
    db = _db(pg)
    decls = gad.load_declarations_or_refuse(fd.DEFAULT_DECLARATIONS)
    unit = gad.declared_unit_or_refuse(decls, "bg_transit_rules", gad.writer_siblings(str(REPO), "bg_transit_rules"))

    def connect():
        c = psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db)
        c.autocommit = False
        c.read_only = True
        return c
    post = gad.read_fingerprint(connect, decls, unit)
    assert unit == "grp_bg_transit_seed"
    assert sum(v["rows"] for v in post["tables"].values()) == spec["expected_post_row_count"] == 112
    assert post["composite"] == spec["expected_post_fingerprint"]
    assert spec["decision"] == "OS-2026-10-05-CITATIONS"
