"""
Migrations 1371 / 1372 / 1373 (vocabulary-consistency round, SS N-538/N-556): data-only, guarded, post-checked UPDATEs of existing
asset_registry rows.
  1371  ga_structural: target_table + natural_key_partition (1358 convention; the 82 owned categories, BYTE-SORTED, md5 844a2086...).
  1372  bg_concordance: volume_explanation prose "3,002-rule" -> "2,994-rule" (nothing else).
  1373  floors: ga_vichara 8249 -> 7774, bg_parihara_rules 449 -> 440, ga_yoga 63 -> 53 (exact-floor guarded). (1369 sits inside the protected
        applied range 1300-1370, so the owner's rule assigns the next free number.)

Two tiers, as in test_migration_1357_1358_registry_target_tables.py:
  * STATIC (always runs): the files' own SQL text; the 1371 partition is recomputed here from the ownership rows and the byte-sorted
    category list and must equal the stored text and its md5 in all three places; each migration names only its own asset(s).
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk files in the migrate.ts shape (psql --single-transaction) to a
    DISPOSABLE cluster (tests/pg_disposable.py); skipped, loudly, when initdb/pg_ctl/psql are absent. Never the project database.
It does NOT prove production state (read the registry columns as the read-only role after deploy; Trap 103).
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

import pytest

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, q, pg  # noqa: F401

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1371 = _MIG / "1371_ga_structural_target_table_and_natural_key_partition.sql"
_M1372 = _MIG / "1372_bg_concordance_volume_explanation_2994_rule_projection.sql"
_M1373 = _MIG / "1373_ga_vichara_bg_parihara_rules_ga_yoga_target_floor_repin.sql"
_M1219 = _MIG / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_count_sql.sql"

EXPECT_MD5 = "844a2086ddb289cab723eb8b70d47b1b"
EXPECT_LEN = 2028
_PREFIX = "chart_facts.fact_category IN ("


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _partition_text() -> str:
    return re.search(r"\$nkp\$(.*?)\$nkp\$", _M1371.read_text(), re.S).group(1)


def _partition_cats(text: str) -> list[str]:
    assert text.startswith(_PREFIX) and text.endswith(")"), text[:80]
    return text[len(_PREFIX):-1].split(", ")


def _load_extractor():
    p = Path(__file__).resolve().parent / "test_l1_emitted_categories_have_ownership.py"
    spec = importlib.util.spec_from_file_location("_l1_extractor_for_1371", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_1371_partition_is_82_unique_byte_sorted_categories_with_the_pinned_md5():
    t = _partition_text()
    cats = _partition_cats(t)
    assert len(cats) == 82 and len(set(cats)) == 82
    assert cats == sorted(cats, key=lambda s: s.encode())
    assert t == _PREFIX + ", ".join(sorted(cats, key=lambda s: s.encode())) + ")"
    assert len(t) == EXPECT_LEN and hashlib.md5(t.encode()).hexdigest() == EXPECT_MD5


def test_static_1371_every_md5_in_the_file_is_the_one_pinned_value():
    text = _M1371.read_text()
    hexes = set(re.findall(r"\b[0-9a-f]{32}\b", text))
    assert hexes == {EXPECT_MD5}                # header, pre-check, rollback and post-check carry the one value; no other digest
    assert text.count(EXPECT_MD5) >= 4
    assert "f922f0ea" not in text               # the collation-ordered text of the first draft


def test_static_1371_names_only_its_own_asset_anywhere_in_the_file_comments_included():
    """By the build-window rule a migration names only its own asset, and comments count: scan the WHOLE text for registry asset ids."""
    text = _M1371.read_text()
    assert set(re.findall(r"\b(?:bg|ga|bo|ka|ph|mi)_[a-z0-9_]+\b", text)) == {"ga_structural"}
    assert "ga_strength" not in text


def test_static_1371_post_check_verifies_the_exact_values_not_just_not_null():
    post = _code(_M1371).split("DO $post$", 1)[1]
    assert "v_tt IS DISTINCT FROM 'chart_facts'" in post
    assert f"md5(v_nkp) IS DISTINCT FROM '{EXPECT_MD5}'" in post
    assert post.count("RAISE EXCEPTION") == 2 and "RAISE NOTICE" not in post


def test_static_1371_pre_check_raises_on_a_foreign_value_instead_of_a_notice():
    pre = _code(_M1371).split("DO $pre$", 1)[1].split("$pre$;", 1)[0]
    assert pre.count("RAISE EXCEPTION") == 2          # a foreign target_table, a foreign partition
    assert "refusing" in pre


def test_static_1371_partition_is_exactly_the_categories_ga_structural_owns_and_emits():
    ex = _load_extractor()
    others = [(c, a) for c, a in ex.effective_owner_pairs() if c in set(_partition_cats(_partition_text())) and a != "ga_structural"]
    assert others == []
    cats = set(_partition_cats(_partition_text()))
    effective = {c for c, a in ex.effective_owner_pairs() if a == "ga_structural"}
    assert cats == effective


def test_static_1371_overlaps_no_other_assets_partition():
    cats = set(_partition_cats(_partition_text()))
    for f in sorted(_MIG.glob("*.sql")):
        if f.name.startswith("1371_"):
            continue
        for m in re.finditer(r"natural_key_partition\s*=\s*'chart_facts\.fact_category IN \(([^)]*)\)'", f.read_text()):
            other = {c.strip() for c in m.group(1).split(",")}
            assert not (other & cats), (f.name, sorted(other & cats))


def test_static_1371_one_guarded_update_of_exactly_two_columns_of_one_asset():
    code = _code(_M1371)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    upd = code.split("UPDATE asset_registry", 1)[1].split("DO $post$", 1)[0]
    assert re.findall(r"\b(target_table|natural_key_partition)\s*=\s*COALESCE", upd) == ["target_table", "natural_key_partition"]
    assert "asset_id = 'ga_structural'" in upd and "(target_table IS NULL OR natural_key_partition IS NULL)" in upd
    assert set(re.findall(r"asset_id\s*=\s*'([a-z_]+)'", code)) == {"ga_structural"}
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    assert code.split("DO $post$", 1)[1].count("RAISE EXCEPTION") == 2


def test_static_1372_updates_only_volume_explanation_of_bg_concordance():
    code = _code(_M1372)
    assert code.count("UPDATE asset_registry") == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", "")) == ["volume_explanation"]
    assert set(re.findall(r"asset_id\s*=\s*'([a-z_]+)'", code)) == {"bg_concordance"}
    old = re.search(r"\$oldexpl\$(.*?)\$oldexpl\$", code, re.S).group(1)
    new = re.search(r"\$newexpl\$(.*?)\$newexpl\$", code, re.S).group(1)
    assert old.replace("3,002-rule", "2,994-rule") == new and "3,002" not in new
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)


def test_static_1372_new_text_equals_the_seed_text():
    seed = (_REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts").read_text()
    new = re.search(r"\$newexpl\$(.*?)\$newexpl\$", _code(_M1372), re.S).group(1)
    assert new in seed


def test_static_1373_three_exact_floor_guarded_updates_and_nothing_else():
    code = _code(_M1373)
    ups = re.findall(r"UPDATE asset_registry SET target_floor = (\d+) WHERE asset_id = '([a-z_]+)' AND target_floor = (\d+);", code)
    assert ups == [("7774", "ga_vichara", "8249"), ("440", "bg_parihara_rules", "449"), ("53", "ga_yoga", "63")]
    assert code.count("UPDATE asset_registry") == 3
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    assert "1369" not in code and code.count("RAISE EXCEPTION") == 3


# -- LIVE tier ----------------------------------------------------------------------------------------------------------

requires_pg = pytest.mark.skipif(not HAVE_PG, reason="DB-backed migration test NOT RUN: " + PG_SKIP_REASON)

_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, scope text, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    has_writer boolean, target_table text, count_sql text, target_floor integer, natural_key_partition text,
    health_probe text, integrity_check_sql text, asset_kind text, asset_type text, volume_explanation text);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
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
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _lit(v):
    return "NULL" if v is None else "'" + v.replace("'", "''") + "'"


def _old_expl() -> str:
    return re.search(r"\$oldexpl\$(.*?)\$oldexpl\$", _M1372.read_text(), re.S).group(1)


def _setup(port, *, tt=None, nkp=None, floors=(8249, 449, 63), concord_floor=721, expl=None, rows=True):
    db = new_db(port)
    q(port, db, _DDL)
    if rows:
        q(port, db, f"""
          INSERT INTO asset_registry (asset_id, layer, scope, has_writer, target_table, natural_key_partition, target_floor, volume_explanation) VALUES
            ('ga_structural','ganita','per_chart', true, {_lit(tt)}, {_lit(nkp)}, 1000, NULL),
            ('ga_strength','ganita','per_chart', true, 'chart_facts', 'chart_facts.fact_category IN (x)', 32, NULL),
            ('ga_vichara','ganita','per_chart', true, NULL, NULL, {floors[0]}, NULL),
            ('bg_parihara_rules','brahmagyan','global', true, NULL, NULL, {floors[1]}, NULL),
            ('ga_yoga','ganita','per_chart', true, NULL, NULL, {floors[2]}, NULL),
            ('bg_concordance','brahmagyan','global', true, NULL, NULL, {concord_floor}, {_lit(expl if expl is not None else _old_expl())});
          INSERT INTO asset_freshness (asset_id, chart_id, freshness_state)
            SELECT asset_id, '{CHART}', 'fresh' FROM asset_registry;""")
    return db


def _apply(port, db, path):
    return psql(port, db, file=path, single_transaction=True)


def _snap(port, db, *, exclude):
    return q(port, db, f"SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id <> '{exclude}'")


@requires_pg
def test_live_1371_sets_both_columns_stales_only_ga_structural_and_matches_the_pinned_md5(pg):
    db = _setup(pg)
    other = _snap(pg, db, exclude="ga_structural")
    fresh = q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'ga_structural'")
    r = _apply(pg, db, _M1371)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT target_table || '|' || natural_key_partition FROM asset_registry WHERE asset_id='ga_structural'") == "chart_facts|" + _partition_text()
    assert q(pg, db, "SELECT md5(natural_key_partition) || length(natural_key_partition) FROM asset_registry WHERE asset_id='ga_structural'") == EXPECT_MD5 + str(EXPECT_LEN)
    assert _snap(pg, db, exclude="ga_structural") == other
    assert q(pg, db, "SELECT freshness_state || reasons::text FROM asset_freshness WHERE asset_id='ga_structural'") == 'stale["registry_changed"]'
    assert q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'ga_structural'") == fresh


@requires_pg
def test_live_1371_idempotent_partial_state_foreign_values_and_empty_registry(pg):
    db = _setup(pg)
    assert _apply(pg, db, _M1371).returncode == 0
    x1 = q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'")
    r = _apply(pg, db, _M1371)
    assert r.returncode == 0 and "already set; nothing to do" in r.stderr
    assert q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_structural'") == x1
    db2 = _setup(pg, tt="chart_facts")                                  # partial: only the partition is filled
    assert _apply(pg, db2, _M1371).returncode == 0
    assert q(pg, db2, "SELECT natural_key_partition FROM asset_registry WHERE asset_id='ga_structural'") == _partition_text()
    # a foreign target_table or a foreign partition is REFUSED (a mismatched pair is never written), and nothing changes
    db3 = _setup(pg, tt="other_table", nkp="chart_facts.fact_category IN (x)")
    r3 = _apply(pg, db3, _M1371)
    assert r3.returncode != 0 and "refusing" in r3.stderr
    assert q(pg, db3, "SELECT target_table || '|' || natural_key_partition FROM asset_registry WHERE asset_id='ga_structural'") == "other_table|chart_facts.fact_category IN (x)"
    db3b = _setup(pg, tt="other_table")
    r3b = _apply(pg, db3b, _M1371)
    assert r3b.returncode != 0 and "not NULL, not chart_facts" in r3b.stderr
    assert q(pg, db3b, "SELECT coalesce(natural_key_partition,'<NULL>') FROM asset_registry WHERE asset_id='ga_structural'") == "<NULL>"
    db3c = _setup(pg, nkp="chart_facts.fact_category IN (x)")
    r3c = _apply(pg, db3c, _M1371)
    assert r3c.returncode != 0 and "different text" in r3c.stderr
    assert q(pg, db3c, "SELECT coalesce(target_table,'<NULL>') FROM asset_registry WHERE asset_id='ga_structural'") == "<NULL>"
    r4 = _apply(pg, _setup(pg, rows=False), _M1371)
    assert r4.returncode == 0 and "no ga_structural registry row" in r4.stderr


@requires_pg
def test_live_1371_post_check_raises_when_the_update_did_not_take(pg):
    db = _setup(pg)
    q(pg, db, "CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ga_structural' DO INSTEAD NOTHING")
    r = _apply(pg, db, _M1371)
    assert r.returncode != 0 and "after the update (expected chart_facts)" in r.stderr


@requires_pg
def test_live_1372_changes_only_the_prose_of_bg_concordance_and_is_idempotent(pg):
    db = _setup(pg)
    other = _snap(pg, db, exclude="bg_concordance")
    cols = q(pg, db, "SELECT to_jsonb(r) - 'volume_explanation' FROM asset_registry r WHERE asset_id='bg_concordance'")
    r = _apply(pg, db, _M1372)
    assert r.returncode == 0, r.stderr
    new = q(pg, db, "SELECT volume_explanation FROM asset_registry WHERE asset_id='bg_concordance'")
    assert "2,994-rule" in new and "3,002" not in new
    assert q(pg, db, "SELECT to_jsonb(r) - 'volume_explanation' FROM asset_registry r WHERE asset_id='bg_concordance'") == cols
    assert _snap(pg, db, exclude="bg_concordance") == other
    x1 = q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_concordance'")
    r2 = _apply(pg, db, _M1372)
    assert r2.returncode == 0 and "already names the 2,994-rule projection" in r2.stderr
    assert q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_concordance'") == x1


@requires_pg
def test_live_1372_foreign_prose_or_floor_is_left_alone_and_post_check_raises(pg):
    db = _setup(pg, expl="something else")
    r = _apply(pg, db, _M1372)
    assert r.returncode == 0 and "NO-OP" in r.stderr
    assert q(pg, db, "SELECT volume_explanation FROM asset_registry WHERE asset_id='bg_concordance'") == "something else"
    db2 = _setup(pg, concord_floor=999)
    assert "NO-OP" in _apply(pg, db2, _M1372).stderr
    db3 = _setup(pg)
    q(pg, db3, "CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bg_concordance' DO INSTEAD NOTHING")
    r3 = _apply(pg, db3, _M1372)
    assert r3.returncode != 0 and "did not take" in r3.stderr


@requires_pg
def test_live_1373_repins_exactly_three_floors_and_is_idempotent(pg):
    db = _setup(pg)
    other = q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id NOT IN ('ga_vichara','bg_parihara_rules','ga_yoga')")
    r = _apply(pg, db, _M1373)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT string_agg(asset_id || '=' || target_floor, ',' ORDER BY asset_id) FROM asset_registry WHERE asset_id IN ('ga_vichara','bg_parihara_rules','ga_yoga')") \
        == "bg_parihara_rules=440,ga_vichara=7774,ga_yoga=53"
    assert q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id NOT IN ('ga_vichara','bg_parihara_rules','ga_yoga')") == other
    assert q(pg, db, "SELECT count(*) FROM asset_freshness WHERE freshness_state='stale'") == "3"
    x1 = q(pg, db, "SELECT string_agg(xmin::text, ',' ORDER BY asset_id) FROM asset_registry")
    r2 = _apply(pg, db, _M1373)
    assert r2.returncode == 0 and r2.stderr.count("nothing to do") == 3
    assert q(pg, db, "SELECT string_agg(xmin::text, ',' ORDER BY asset_id) FROM asset_registry") == x1


@requires_pg
def test_live_1373_unknown_floor_is_a_noop_and_post_check_raises(pg):
    db = _setup(pg, floors=(1234, 449, 63))
    r = _apply(pg, db, _M1373)
    assert r.returncode == 0 and "NO-OP" in r.stderr
    assert q(pg, db, "SELECT target_floor FROM asset_registry WHERE asset_id='ga_vichara'") == "1234"
    assert q(pg, db, "SELECT target_floor FROM asset_registry WHERE asset_id='ga_yoga'") == "53"
    db2 = _setup(pg)
    q(pg, db2, "CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ga_yoga' DO INSTEAD NOTHING")
    r2 = _apply(pg, db2, _M1373)
    assert r2.returncode != 0 and "did not take" in r2.stderr
    assert q(pg, db2, "SELECT target_floor FROM asset_registry WHERE asset_id='ga_vichara'") == "8249"   # whole transaction rolled back
