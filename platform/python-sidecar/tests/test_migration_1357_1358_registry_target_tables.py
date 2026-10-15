"""
Migrations 1357 / 1358 (certification, SS N-425): asset_registry.target_table for bg_prashna_rules (1357) and target_table +
natural_key_partition for ga_strength (1358). Data-only, guarded, post-checked UPDATEs of existing registry rows.

Two tiers:
  * STATIC (always runs): the files' own SQL text; the 1358 partition is DERIVED here from the writer (the repo's own AST extractor in
    test_l1_emitted_categories_have_ownership.py) and from the 1219 ownership rows, and must equal the partition text byte for byte; it
    must not overlap any other asset's partition.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migrations, in the migrate.ts shape (psql --single-transaction),
    to a DISPOSABLE cluster that tests/pg_disposable.py creates with initdb in a temp dir (own port, trust auth, removed at the end).
    Skipped, loudly, when no initdb/pg_ctl/psql is found. Never the project database.

LIVE proves: each migration sets exactly the column(s) it names and nothing else; the nirmana trigger body stales ONLY the touched asset's
freshness rows; the UPDATE is guarded (a foreign value is left alone with a NOTICE), idempotent (a second run rewrites nothing, xmin
unchanged), a partial state is completed without overwriting; the post-check RAISES (whole transaction rolled back) when the UPDATE did
not take; and, for 1358, the real provenance.py consumers (_registry_partition + build_receipt) see has_cowriters AND a declared partition,
i.e. no partition_undeclared, while target_table alone WOULD produce it.
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
_M1357 = _MIG / "1357_bg_prashna_rules_target_table.sql"
_M1358 = _MIG / "1358_ga_strength_target_table_and_natural_key_partition.sql"
_M1219 = _MIG / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_count_sql.sql"


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _load_extractor():
    p = Path(__file__).resolve().parent / "test_l1_emitted_categories_have_ownership.py"
    spec = importlib.util.spec_from_file_location("_l1_extractor_for_1358", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _partition_text() -> str:
    return re.search(r"\$nkp\$(.*?)\$nkp\$", _M1358.read_text(), re.S).group(1)


def _partition_cats(text: str) -> list[str]:
    m = re.fullmatch(r"chart_facts\.fact_category IN \(([^)]*)\)", text)
    assert m, text
    return [c.strip() for c in m.group(1).split(",")]


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_1357_one_guarded_update_of_target_table_only():
    code = _code(_M1357)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", ""), re.I) == ["target_table"]
    upd = code.split("UPDATE asset_registry", 1)[1].split(";", 1)[0]
    assert "target_table = 'bg_prashna_tajik_yogas'" in upd
    assert "asset_id = 'bg_prashna_rules'" in upd and "target_table IS NULL" in upd
    assert code.count("UPDATE asset_registry") == 1
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    post = code.split("DO $post$", 1)[1].split("$post$;", 1)[0]
    assert "RAISE EXCEPTION" in post and "IS NULL" in post and "RAISE NOTICE" not in post


def test_static_1357_table_is_one_of_the_five_the_writer_seeds():
    src = (_REPO / "platform" / "python-sidecar" / "brahmagyan" / "l0_prashna.py").read_text()
    written = set(re.findall(r"INSERT INTO (bg_prashna_\w+)", src))
    assert len(written) == 5 and "bg_prashna_tajik_yogas" in written


def test_static_1358_one_guarded_update_of_exactly_two_columns():
    code = _code(_M1358)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert code.count("UPDATE asset_registry") == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", ""), re.I) == ["target_table"]
    upd = code.split("UPDATE asset_registry", 1)[1].split(";", 1)[0]
    assert "target_table = COALESCE(target_table, 'chart_facts')" in upd
    assert "natural_key_partition = COALESCE(natural_key_partition, $nkp$" in upd
    assert "asset_id = 'ga_strength'" in upd and "(target_table IS NULL OR natural_key_partition IS NULL)" in upd
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)
    post = code.split("DO $post$", 1)[1].split("$post$;", 1)[0]
    assert post.count("RAISE EXCEPTION") == 2 and "RAISE NOTICE" not in post


def test_static_1358_partition_is_exactly_the_categories_the_writer_emits_and_owns():
    ex = _load_extractor()
    res, unresolved, _ = ex.extract()
    assert unresolved == []
    emitted = ex.emitted_by_asset(res)["ga_strength"]
    owned_1219 = set(re.findall(r"\('([a-z_]+)', 'ga_strength'\)", _M1219.read_text()))
    cats = _partition_cats(_partition_text())
    assert len(cats) == 32 and cats == sorted(cats) and len(set(cats)) == 32
    assert set(cats) == emitted == owned_1219
    assert _partition_text() == "chart_facts.fact_category IN (" + ", ".join(cats) + ")"


def test_static_1358_partition_matches_the_registered_count_predicate():
    """The 1219 strength_new predicate (also the seed text) selects exactly these 32 category names."""
    cats = _partition_cats(_partition_text())

    def like(c: str, pat: str) -> bool:
        return re.fullmatch(pat.replace("%", ".*"), c) is not None

    def in_predicate(c: str) -> bool:
        return (like(c, "graha_shadbala_%") or c in ("graha_ishta_phala", "graha_kashta_phala") or like(c, "graha_vimsopaka_%")
                or (like(c, "ashtakavarga_%") and c != "ashtakavarga_anubindu") or like(c, "house_bhava_bala_%")
                or like(c, "graha_%_bala_per_varga"))

    assert all(in_predicate(c) for c in cats)
    assert "ashtakavarga_anubindu" not in cats


def test_static_1358_partition_overlaps_no_other_assets_partition_and_no_other_owner():
    cats = set(_partition_cats(_partition_text()))
    for f in sorted(_MIG.glob("*.sql")):
        if f.name.startswith("1358_"):
            continue
        for m in re.finditer(r"natural_key_partition\s*=\s*'chart_facts\.fact_category IN \(([^)]*)\)'", f.read_text()):
            other = {c.strip() for c in m.group(1).split(",")}
            assert not (other & cats), (f.name, sorted(other & cats))
    ex = _load_extractor()
    others = [(c, a) for c, a in ex.effective_owner_pairs() if c in cats and a != "ga_strength"]
    assert others == []


def test_static_1358_header_md5_and_length_pin_the_partition_text():
    t = _partition_text()
    md5 = hashlib.md5(t.encode()).hexdigest()
    hdr = _M1358.read_text()
    assert f"md5 {md5}, length {len(t)}" in hdr
    assert hdr.count(md5) >= 3          # header expectation, rollback guard, pre-check NOTICE guard


# -- LIVE tier ----------------------------------------------------------------------------------------------------------

requires_pg = pytest.mark.skipif(not HAVE_PG, reason="DB-backed migration test NOT RUN: " + PG_SKIP_REASON)

_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, scope text, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    has_writer boolean, target_table text, count_sql text, target_floor integer, natural_key_partition text,
    health_probe text, integrity_check_sql text, asset_kind text, asset_type text);
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
PRASHNA_COUNT = ("SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) AS count")
NKP_NAKSHATRA = "chart_facts.fact_category IN (graha_nakshatra_join, graha_pada_join)"


def _setup(port, *, prashna_tt=None, strength_tt=None, strength_nkp=None, rows=True):
    db = new_db(port)
    q(port, db, _DDL)
    if rows:
        q(port, db, f"""
          INSERT INTO asset_registry (asset_id, layer, scope, has_writer, target_table, count_sql, natural_key_partition) VALUES
            ('bg_prashna_rules','brahmagyan','global', true, {_lit(prashna_tt)}, '{PRASHNA_COUNT}', NULL),
            ('bg_other','brahmagyan','global', true, NULL, 'SELECT 1', NULL),
            ('ga_strength','ganita','per_chart', true, {_lit(strength_tt)}, 'SELECT 1 WHERE $1 IS NOT NULL', {_lit(strength_nkp)}),
            ('ga_nakshatra','ganita','per_chart', true, 'chart_facts', 'SELECT 1 WHERE $1 IS NOT NULL', '{NKP_NAKSHATRA}');
          INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES
            ('bg_prashna_rules','{CHART}','fresh'), ('bg_other','{CHART}','fresh'),
            ('ga_strength','{CHART}','fresh'), ('ga_nakshatra','{CHART}','fresh');""")
    return db


def _lit(v):
    return "NULL" if v is None else "'" + v.replace("'", "''") + "'"


def _apply(port, db, path):
    """migrate.ts shape: one transaction, rolled back whole on any error. Returns the CompletedProcess (stderr carries NOTICEs)."""
    return psql(port, db, file=path, single_transaction=True)


def _row(port, db, asset):
    return q(port, db, f"SELECT coalesce(target_table,'<NULL>') || '|' || coalesce(natural_key_partition,'<NULL>') "
                       f"FROM asset_registry WHERE asset_id='{asset}'")


@requires_pg
def test_live_1357_sets_target_table_only_and_stales_only_its_own_freshness(pg):
    db = _setup(pg)
    other_before = q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id <> 'bg_prashna_rules'")
    fresh_before = q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'bg_prashna_rules'")
    cols_before = q(pg, db, "SELECT to_jsonb(r) - 'target_table' FROM asset_registry r WHERE asset_id = 'bg_prashna_rules'")
    r = _apply(pg, db, _M1357)
    assert r.returncode == 0, r.stderr
    assert _row(pg, db, "bg_prashna_rules") == "bg_prashna_tajik_yogas|<NULL>"
    assert q(pg, db, "SELECT to_jsonb(r) - 'target_table' FROM asset_registry r WHERE asset_id = 'bg_prashna_rules'") == cols_before
    assert q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id <> 'bg_prashna_rules'") == other_before
    # trigger: target_table is a staling column -> the touched asset's freshness is staled, every other asset's is not
    assert q(pg, db, "SELECT freshness_state || reasons::text FROM asset_freshness WHERE asset_id='bg_prashna_rules'") == 'stale["registry_changed"]'
    assert q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'bg_prashna_rules'") == fresh_before


@requires_pg
def test_live_1357_idempotent_second_run_rewrites_nothing(pg):
    db = _setup(pg)
    assert _apply(pg, db, _M1357).returncode == 0
    x1 = q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_prashna_rules'")
    r = _apply(pg, db, _M1357)
    assert r.returncode == 0 and "already bg_prashna_tajik_yogas" in r.stderr
    assert q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bg_prashna_rules'") == x1


@requires_pg
def test_live_1357_foreign_value_untouched_and_empty_registry_noop(pg):
    db = _setup(pg, prashna_tt="something_else")
    r = _apply(pg, db, _M1357)
    assert r.returncode == 0 and "already something_else" in r.stderr and "NO-OP" in r.stderr
    assert _row(pg, db, "bg_prashna_rules") == "something_else|<NULL>"
    db2 = _setup(pg, rows=False)
    r2 = _apply(pg, db2, _M1357)
    assert r2.returncode == 0 and "no bg_prashna_rules registry row" in r2.stderr


@requires_pg
def test_live_1357_post_check_raises_when_the_update_did_not_take(pg):
    db = _setup(pg)
    q(pg, db, "CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bg_prashna_rules' DO INSTEAD NOTHING")
    r = _apply(pg, db, _M1357)
    assert r.returncode != 0 and "update did not take" in r.stderr
    assert _row(pg, db, "bg_prashna_rules") == "<NULL>|<NULL>"


@requires_pg
def test_live_1358_sets_both_columns_exactly_and_stales_only_ga_strength(pg):
    db = _setup(pg)
    cols_before = q(pg, db, "SELECT to_jsonb(r) - 'target_table' - 'natural_key_partition' FROM asset_registry r WHERE asset_id = 'ga_strength'")
    other_before = q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id <> 'ga_strength'")
    fresh_before = q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'ga_strength'")
    r = _apply(pg, db, _M1358)
    assert r.returncode == 0, r.stderr
    assert _row(pg, db, "ga_strength") == "chart_facts|" + _partition_text()
    assert q(pg, db, "SELECT to_jsonb(r) - 'target_table' - 'natural_key_partition' FROM asset_registry r WHERE asset_id = 'ga_strength'") == cols_before
    assert q(pg, db, "SELECT string_agg(r::text, ';' ORDER BY asset_id) FROM asset_registry r WHERE asset_id <> 'ga_strength'") == other_before
    assert q(pg, db, "SELECT freshness_state || reasons::text FROM asset_freshness WHERE asset_id='ga_strength'") == 'stale["registry_changed"]'
    assert q(pg, db, "SELECT string_agg(f::text, ';' ORDER BY asset_id) FROM asset_freshness f WHERE asset_id <> 'ga_strength'") == fresh_before
    assert q(pg, db, "SELECT md5(natural_key_partition) FROM asset_registry WHERE asset_id='ga_strength'") == hashlib.md5(_partition_text().encode()).hexdigest()


@requires_pg
def test_live_1358_idempotent_second_run_rewrites_nothing(pg):
    db = _setup(pg)
    assert _apply(pg, db, _M1358).returncode == 0
    x1 = q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_strength'")
    r = _apply(pg, db, _M1358)
    assert r.returncode == 0 and "already set; nothing to do" in r.stderr
    assert q(pg, db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ga_strength'") == x1


@requires_pg
def test_live_1358_partial_state_is_completed_and_foreign_values_are_never_overwritten(pg):
    # target_table already chart_facts, partition NULL -> only the partition is filled
    db = _setup(pg, strength_tt="chart_facts")
    assert _apply(pg, db, _M1358).returncode == 0
    assert _row(pg, db, "ga_strength") == "chart_facts|" + _partition_text()
    # a foreign partition (and a foreign target_table) are left as they are, with NOTICEs; the NULL column is still filled
    db2 = _setup(pg, strength_tt="other_table", strength_nkp="chart_facts.fact_category IN (x)")
    r = _apply(pg, db2, _M1358)
    assert r.returncode == 0 and "already set; nothing to do" in r.stderr
    assert "already other_table" in r.stderr and "different text" in r.stderr
    assert _row(pg, db2, "ga_strength") == "other_table|chart_facts.fact_category IN (x)"
    db3 = _setup(pg, strength_nkp="chart_facts.fact_category IN (x)")
    r3 = _apply(pg, db3, _M1358)
    assert r3.returncode == 0 and "different text" in r3.stderr
    assert _row(pg, db3, "ga_strength") == "chart_facts|chart_facts.fact_category IN (x)"


@requires_pg
def test_live_1358_empty_registry_is_a_noop(pg):
    db = _setup(pg, rows=False)
    r = _apply(pg, db, _M1358)
    assert r.returncode == 0 and "no ga_strength registry row" in r.stderr


@requires_pg
def test_live_1358_post_check_raises_when_the_update_did_not_take(pg):
    db = _setup(pg)
    q(pg, db, "CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ga_strength' DO INSTEAD NOTHING")
    r = _apply(pg, db, _M1358)
    assert r.returncode != 0 and "target_table update did not take" in r.stderr
    assert _row(pg, db, "ga_strength") == "<NULL>|<NULL>"


@requires_pg
def test_live_1358_post_check_raises_when_only_the_partition_did_not_take(pg):
    db = _setup(pg)
    q(pg, db, """CREATE FUNCTION nullify_nkp() RETURNS trigger LANGUAGE plpgsql AS $$
                 BEGIN NEW.natural_key_partition := NULL; RETURN NEW; END; $$;
                 CREATE TRIGGER zz_nullify BEFORE UPDATE ON asset_registry FOR EACH ROW
                 WHEN (NEW.asset_id = 'ga_strength') EXECUTE FUNCTION nullify_nkp();""")
    r = _apply(pg, db, _M1358)
    assert r.returncode != 0 and "natural_key_partition update did not take" in r.stderr
    assert _row(pg, db, "ga_strength") == "<NULL>|<NULL>"          # the whole transaction rolled back, target_table too


@requires_pg
def test_live_1358_provenance_consumers_see_cowriters_and_a_declared_partition(pg):
    """The reason both columns go together: provenance.py's own SQL and build_receipt, run against the migrated row."""
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    from pipeline.orchestrator import provenance as prov

    def inputs(db):
        with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db, row_factory=dict_row) as c, c.cursor() as cur:
            return prov._registry_partition(cur, "ga_strength")

    def reasons(nkp, cow):
        return prov.build_receipt(asset_id="ga_strength", chart_id=CHART, code_digest="c", config={}, upstream_digest="u",
                                  upstream_receipts=[], partition_declaration=nkp, has_cowriters=cow, output_digest="o",
                                  output_digest_spec_sha256="s").unknown_reasons

    before = _setup(pg)
    nkp, cow = inputs(before)
    assert (nkp, cow) == (None, False)                                 # today: no co-writers, so no partition is needed
    assert "partition_undeclared" not in reasons(nkp, cow)
    # the trap: target_table alone makes ga_strength a chart_facts co-writer WITHOUT a partition
    q(pg, before, "UPDATE asset_registry SET target_table='chart_facts' WHERE asset_id='ga_strength'")
    nkp, cow = inputs(before)
    assert (nkp, cow) == (None, True)
    assert "partition_undeclared" in reasons(nkp, cow)
    # the migration: both together
    after = _setup(pg)
    assert _apply(pg, after, _M1358).returncode == 0
    nkp, cow = inputs(after)
    assert cow is True and nkp == _partition_text()
    assert reasons(nkp, cow) == ()
