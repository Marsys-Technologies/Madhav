"""Reuse the campaign's guarded throwaway-database lifecycle, never production."""
from pathlib import Path
import uuid

import psycopg
import pytest


CHART='00000000-0000-0000-0000-000000000001'
NATAL='00000000-0000-0000-0000-000000000002'
BUILD='00000000-0000-0000-0000-000000000003'
MIGRATION=Path(__file__).resolve().parents[5]/'migrations/1383_ka_3a_vedha_candidate_intervals.sql'


@pytest.fixture
def conn(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as c:
        # Each test rolls back its entire isolated schema; the suite owns and
        # drops the database through kala_db_dsn, including on failure.
        schema='vedha_'+uuid.uuid4().hex
        c.execute(f'CREATE SCHEMA "{schema}"')
        c.execute(f'SET search_path TO "{schema}", public')
        c.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid NOT NULL)')
        c.execute('CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, build_id uuid, ayanamsha_id text, fact_category text, fact_subject text, fact_key text, fact_value_num numeric)')
        c.execute('CREATE TABLE bg_transit_rules (graha text, primary_house integer, vedha_house integer, classical_citation text, rule_type text)')
        c.execute('CREATE TABLE bg_phaladeepika_latta (graha text, count_from_graha integer, direction text, source_citation text, verse_ref text)')
        c.execute('CREATE TABLE classical_text_chunks (chunk_id text, text_id text, chapter integer, verse_start integer, verse_end integer, content_en text)')
        from tests.l3.ka_vedha_gochara.test_overlays import ROWS
        for row in ROWS:
            c.execute('INSERT INTO bg_transit_rules VALUES (%s,%s,%s,%s,%s)', row)
        c.execute('CREATE TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid, state text, conventions jsonb, PRIMARY KEY(chart_id,generation))')
        c.execute('CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY,generation text)')
        c.execute('CREATE TABLE kala_layer_candidate_grain (chart_id uuid,generation text,grain_key text,result_state text,input_vector text,recorded_at timestamptz DEFAULT now(),PRIMARY KEY(chart_id,generation,grain_key))')
        c.execute('CREATE TABLE kala_vedha_gochara (id uuid PRIMARY KEY, chart_id uuid, detail jsonb, window_start date, UNIQUE(chart_id,window_start))')
        c.execute("INSERT INTO build_runs VALUES (%s,%s),(%s,%s)",(BUILD,CHART,NATAL,CHART))
        c.execute("INSERT INTO chart_facts VALUES ('moon-ref',%s,%s,'lahiri_chitrapaksha','graha_position','MOON','longitude_sidereal',300)",(CHART,NATAL))
        c.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate-1',%s,'building',%s::jsonb)",
            (CHART,BUILD,'{"natal":{"build_id":"'+NATAL+'","ayanamsha_id":"lahiri_chitrapaksha"}}'))
        c.execute("INSERT INTO kala_vedha_gochara VALUES (%s,%s,'{\"retained\":true}','2025-01-01')",(str(uuid.uuid4()),CHART))
        assert MIGRATION.exists(), 'KA-3a protected migration missing'
        c.execute(MIGRATION.read_text().replace('public.',f'"{schema}".'))
        try:
            yield c
        finally:
            c.rollback()
