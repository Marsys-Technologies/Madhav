import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migration = fs.readFileSync(path.resolve(process.cwd(),
  'supabase/migrations/621_nirmana_l0_dasha_systems_integrity_contract.sql'),'utf8')
const url = process.env.NIRMANA_L0_DASHAS_TEST_DATABASE_URL
const digests = [
  '30742da6005fc977124192ae27ee1ca0bb29dd5363267860dfd8260e8bb3173a',
  '58a2b8b98dddcc6bb5dec73af8de386af3768457d2b3e2aea739bc435c83d4c9',
  '46ec3fd9da97e6e91ec60acd34a1ece858f7e7adefecd7b6955620980f120a04',
]
const explanation = '60 owned rows = 20 deterministic dasha-system definitions × 3 reconciled projections (catalog + dasha-system ontology partition + reference_dasha_systems), including the governed KP subdivision identity.'
const countSql = `SELECT
  (SELECT count(*) FROM brahma_dasha_systems) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dasha_system') +
  (SELECT count(*) FROM reference_dasha_systems) AS count`

describe('migration 621 — dasha systems integrity',()=>{
  it('is fail-closed and seed-aligned',()=>{
    for(const digest of digests) expect(migration).toContain(digest)
    expect(migration).toContain('migration 621 refuses unknown bg_dasha_systems registry contract')
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(ASSETS.find(a=>a.asset_id==='bg_dasha_systems')).toMatchObject({
      target_floor:60,count_sql:countSql,volume_explanation:explanation,
    })
  })
})

if(url){const u=new URL(url);if(!['localhost','127.0.0.1'].includes(u.hostname)
  ||u.pathname!=='/nirmana_l0_dashas_integrity_test')throw new Error('unsafe dasha test database')}

describe.skipIf(!url)('migration 621 — real PostgreSQL',()=>{
  async function prepared(){const c=new Client({connectionString:url});await c.connect();await c.query(`
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    DROP TABLE IF EXISTS reference_dasha_systems,brahma_ontology,brahma_dasha_systems,asset_registry CASCADE;
    CREATE TABLE asset_registry(asset_id text primary key,layer text,sort_order int,scope text,asset_kind text,catalog_status text,is_active bool,has_writer bool,target_table text,count_sql text,target_floor bigint,depends_on text[],natural_key_partition text,data_disposition text,integrity_check_sql text,english_description text,volume_explanation text);
    CREATE TABLE brahma_dasha_systems(canonical_id text primary key,name_sa text,name_en text,total_cycle_years numeric,base_unit text,sequence_jsonb jsonb,computation_method text,computation_pseudocode text,conditions_for_use text,school text,classical_citations jsonb,source_chunk_ids bigint[],python_impl_module text);
    CREATE TABLE brahma_ontology(entity_class text,canonical_id text,canonical_name_en text,canonical_name_sa text,synonyms text[],description text,source_citation text,primary key(entity_class,canonical_id));
    CREATE TABLE reference_dasha_systems(canonical_id text primary key,name_en text,school text);
    INSERT INTO brahma_dasha_systems SELECT CASE WHEN i=20 THEN 'kp' ELSE 'd'||lpad(i::text,2,'0') END,'N'||i,'N'||i,120,'unit','[]','method','steps','conditions',CASE WHEN i=20 THEN 'kp' ELSE 'parashari' END,'[]','{}',NULL FROM generate_series(1,20)i;
    INSERT INTO brahma_ontology SELECT 'dasha_system',canonical_id,name_en,name_sa,ARRAY[name_en],name_en||' — 120-year '||school||' dasha system','source' FROM brahma_dasha_systems;
    INSERT INTO reference_dasha_systems SELECT canonical_id,name_en,school FROM brahma_dasha_systems;
    INSERT INTO asset_registry VALUES('bg_dasha_systems','brahmagyan',10,'global','data','CURRENT',true,true,'brahma_dasha_systems',$c$${countSql}$c$,60,ARRAY['bg_ontology'],NULL,NULL,NULL,'Classical dasha system definitions — sequence rules, computation methods, conditions for use',$e$${explanation}$e$);
  `);return c}
  async function fixture(c:Client){const qs=[
    `SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_sa,name_en,total_cycle_years,base_unit,sequence_jsonb,computation_method,computation_pseudocode,conditions_for_use,school,classical_citations,source_chunk_ids,python_impl_module)::text,E'\\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') d FROM brahma_dasha_systems`,
    `SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)::text,E'\\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') d FROM brahma_ontology WHERE entity_class='dasha_system'`,
    `SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_en,school)::text,E'\\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') d FROM reference_dasha_systems`];let m=migration;for(let i=0;i<3;i++)m=m.replaceAll(digests[i],(await c.query(qs[i])).rows[0].d);return m}
  async function detector(c:Client){const r=await c.query("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_dasha_systems'");return Object.values((await c.query(r.rows[0].integrity_check_sql)).rows[0])[0]===true}
  it('installs, replays, and detects mutations',async()=>{const c=await prepared();try{const m=await fixture(c);await c.query(m);await c.query(m);expect(await detector(c)).toBe(true);await c.query("UPDATE reference_dasha_systems SET school='drift' WHERE canonical_id='kp'");expect(await detector(c)).toBe(false)}finally{await c.end()}})
  it('accepts live legacy metadata and rejects unknown drift',async()=>{const c=await prepared();try{await c.query("UPDATE asset_registry SET target_floor=18,count_sql='SELECT count(*) FROM brahma_dasha_systems',volume_explanation='18 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per actual build count.'");const m=await fixture(c);await c.query(m);expect(await detector(c)).toBe(true);await c.query("UPDATE asset_registry SET target_floor=1");await expect(c.query(m)).rejects.toThrow('migration 621 refuses unknown')}finally{await c.end()}})
})
