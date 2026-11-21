"""Verify migration 1420 reseals bg_nakshatra from migration 625 to the fixed seed."""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[3]
GOV_TESTS = ROOT / "platform" / "scripts" / "governance" / "__tests__"
if str(GOV_TESTS) not in sys.path:
    sys.path.insert(0, str(GOV_TESTS))

from _disposable_pg import disposable_pg  # noqa: E402,F401
from brahmagyan import l0_nakshatra  # noqa: E402

BEFORE_CHECK_MD5 = "3a1bc82c78ed3f79aae62d18a4d29f0e"
AFTER_CHECK_MD5 = "c17250e197373669b61e56baaf487db0"
PRIOR_ROW_PIN = "bbbf686205c208efe0a7f6dbd192b27e63931a9b37f442d194d8d17b72ee3fde"
NEW_ROW_PIN = "57279a04f69f3b7672020bc20b0577c60db76b11c8cc45b74fac30a131f2aa1c"


def _literal(sql: str, tag: str) -> str:
    marker = f"${tag}$"
    assert sql.count(marker) == 2
    return sql.split(marker)[1]


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def test_reseal_splice_matches_migration_625():
    m625 = (ROOT / "platform/supabase/migrations/625_nirmana_l0_nakshatra_exact_contract.sql").read_text()
    m1420 = (ROOT / "platform/supabase/migrations/1420_bg_nakshatra_nadi_gandanta_integrity_reseal.sql").read_text()

    check_sql = _literal(m625, "check")
    assert _md5(check_sql) == BEFORE_CHECK_MD5
    assert check_sql.count(PRIOR_ROW_PIN) == 1

    resealed_sql = check_sql.replace(PRIOR_ROW_PIN, NEW_ROW_PIN)
    assert _md5(resealed_sql) == AFTER_CHECK_MD5

    assert f"expected_before constant text := '{BEFORE_CHECK_MD5}'" in m1420
    assert f"expected_after  constant text := '{AFTER_CHECK_MD5}'" in m1420
    assert f"prior_pin constant text := '{PRIOR_ROW_PIN}'" in m1420
    assert f"new_pin   constant text := '{NEW_ROW_PIN}'" in m1420
    assert len(re.findall(r"^\s*UPDATE public\.asset_registry\b", m1420, re.M)) == 1


def test_resealed_integrity_check_passes_on_seeded_rows(disposable_pg):
    conn = psycopg2.connect(disposable_pg.url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE public.asset_registry (
              asset_id text PRIMARY KEY,
              layer text,
              sort_order integer,
              scope text,
              asset_kind text,
              catalog_status text,
              is_active boolean,
              has_writer boolean,
              target_table text,
              count_sql text,
              target_floor integer,
              depends_on text[],
              data_disposition text,
              natural_key_partition text,
              integrity_check_sql text
            );
            INSERT INTO public.asset_registry (
              asset_id, layer, sort_order, scope, asset_kind, catalog_status,
              is_active, has_writer, target_table, count_sql, target_floor, depends_on
            ) VALUES (
              'bg_nakshatra', 'brahmagyan', 15, 'global', 'data', 'CURRENT',
              true, true, 'reference_nakshatra',
              'SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count',
              2857, ARRAY[]::text[]
            );
            """
        )
        cur.execute((ROOT / "platform/supabase/migrations/238_bg_nakshatra_tables.sql").read_text())
        cur.execute((ROOT / "platform/supabase/migrations/625_nirmana_l0_nakshatra_exact_contract.sql").read_text())
        cur.execute((ROOT / "platform/supabase/migrations/1420_bg_nakshatra_nadi_gandanta_integrity_reseal.sql").read_text())
        # Idempotency check
        cur.execute((ROOT / "platform/supabase/migrations/1420_bg_nakshatra_nadi_gandanta_integrity_reseal.sql").read_text())

        l0_nakshatra.seed_nakshatra(conn, "test-1420")
        cur.execute("SELECT integrity_check_sql FROM public.asset_registry WHERE asset_id = 'bg_nakshatra'")
        (check_sql,) = cur.fetchone()
        cur.execute(check_sql)
        assert cur.fetchone() == (True,)
    finally:
        cur.close()
        conn.close()
