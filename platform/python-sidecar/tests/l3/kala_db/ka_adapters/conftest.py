"""Use only the existing guarded throwaway database fixture."""
from pathlib import Path
import uuid

import psycopg
import pytest
from psycopg.types.json import Jsonb

from tests.l3.ka_adapters.test_candidates import CHART,NATAL,BUILD,MOORTI,RINGS

MIGRATION=Path(__file__).resolve().parents[5]/'migrations/1384_ka_3b_contested_candidates.sql'


@pytest.fixture
def conn(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as c:
        schema='adapters_'+uuid.uuid4().hex
        c.execute(f'CREATE SCHEMA "{schema}"')
        c.execute(f'SET search_path TO "{schema}", public')
        c.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid NOT NULL)')
        c.execute('CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, build_id uuid, ayanamsha_id text, fact_category text, fact_subject text, fact_key text, fact_value_num numeric, fact_value_text text)')
        c.execute('CREATE TABLE bg_transit_moorti (nakshatra_offset integer, moorti_name text, quality_tier integer, phala_brief text, classical_citation text)')
        c.execute('CREATE TABLE bg_kota_chakra_rings (ring_name text, ring_position integer,table_version text,citation text)')
        for r in MOORTI:
            c.execute('INSERT INTO bg_transit_moorti VALUES (%s,%s,%s,%s,%s)',tuple(r.values()))
        for r in RINGS:
            c.execute('INSERT INTO bg_kota_chakra_rings VALUES (%s,%s,%s,%s)',tuple(r.values()))
        c.execute('CREATE TABLE kala_layer_candidate (chart_id uuid,generation text,build_id uuid,state text,conventions jsonb,PRIMARY KEY(chart_id,generation))')
        c.execute('CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY,generation text)')
        c.execute('CREATE TABLE kala_layer_candidate_grain (chart_id uuid,generation text,grain_key text,result_state text,input_vector text,recorded_at timestamptz DEFAULT now(),PRIMARY KEY(chart_id,generation,grain_key))')
        c.execute('INSERT INTO build_runs VALUES (%s,%s),(%s,%s)',(BUILD,CHART,NATAL,CHART))
        c.execute("INSERT INTO chart_facts VALUES ('moon-ref',%s,%s,'lahiri_chitrapaksha','graha_position','MOON','longitude_sidereal',300,NULL)",(CHART,NATAL))
        for subject,value in [('LAGNA','Aries'),('MOON','Aries'),('SUN','Capricorn')]:
            c.execute("INSERT INTO chart_facts VALUES (%s,%s,%s,'lahiri_chitrapaksha','graha_position',%s,'sign',NULL,%s)",(subject.lower()+'-sign',CHART,NATAL,subject,value))
        c.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate-1',%s,'building',%s)",
            (CHART,BUILD,Jsonb({'natal':{'build_id':NATAL,'ayanamsha_id':'lahiri_chitrapaksha'}})))
        for family in ('moorti_nirnaya','kota_chakra','tithi_pravesha','sudarshana_varsha'):
            c.execute(f'CREATE TABLE kala_{family} (id uuid PRIMARY KEY,chart_id uuid,legacy_value jsonb)')
            if family=='moorti_nirnaya': c.execute('ALTER TABLE kala_moorti_nirnaya ADD COLUMN upstream_fingerprint jsonb')
            c.execute(f'INSERT INTO kala_{family} (id,chart_id,legacy_value) VALUES (%s,%s,%s)',(str(uuid.uuid4()),CHART,Jsonb({'retained':['exact',1,None]})))
        assert MIGRATION.exists(), 'KA-3b protected migration missing'
        c.execute(MIGRATION.read_text().replace('public.',f'"{schema}".'))
        try: yield c
        finally: c.rollback()
