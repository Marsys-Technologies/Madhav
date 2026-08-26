import fs from 'node:fs'
import path from 'node:path'
import { Client } from 'pg'
import { describe, expect, it } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const migration=fs.readFileSync(path.resolve(process.cwd(),'supabase/migrations/622_nirmana_l0_doshas_integrity_contract.sql'),'utf8')
const url=process.env.NIRMANA_L0_DOSHAS_TEST_DATABASE_URL
const digests=['cfb21a5342bda3a911f55597cac3367b727a79953ccef3349ad7f49c98acfcd4','ee5dedf6e9934f42883ff268c3e485648577c6e528bfb76b7b839937b4572984','3fd442d6e8bfcb54fa5f4752907a2ef057ab1f49ec12aad9536a833b4e04d9a4']
const explanation='237 owned rows = 79 deterministic dosha definitions × 3 reconciled projections (catalog + dosha ontology partition + reference_doshas). Production and clean-source replay were byte-identical before convergence hardening.'
const countSql=`SELECT
  (SELECT count(*) FROM brahma_dosha_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dosha') +
  (SELECT count(*) FROM reference_doshas) AS count`

describe('migration 622 — doshas integrity',()=>{it('is fail-closed and seed-aligned',()=>{
  for(const d of digests)expect(migration).toContain(d)
  expect(migration).toContain('migration 622 refuses unknown bg_doshas registry contract')
  expect(migration).not.toMatch(/^BEGIN;/m)
  expect(ASSETS.find(a=>a.asset_id==='bg_doshas')).toMatchObject({target_floor:237,count_sql:countSql,volume_explanation:explanation})
})})

if(url){const u=new URL(url);if(!['localhost','127.0.0.1'].includes(u.hostname)||u.pathname!=='/nirmana_l0_doshas_integrity_test')throw new Error('unsafe dosha test database')}
describe.skipIf(!url)('migration 622 — real PostgreSQL',()=>{
 async function prep(){const c=new Client({connectionString:url});await c.connect();await c.query(`
 CREATE EXTENSION IF NOT EXISTS pgcrypto;DROP TABLE IF EXISTS reference_doshas,brahma_ontology,brahma_dosha_catalog,asset_registry CASCADE;
 CREATE TABLE asset_registry(asset_id text primary key,layer text,sort_order int,scope text,asset_kind text,catalog_status text,is_active bool,has_writer bool,target_table text,count_sql text,target_floor bigint,depends_on text[],natural_key_partition text,data_disposition text,integrity_check_sql text,english_description text,volume_explanation text);
 CREATE TABLE brahma_dosha_catalog(canonical_id text primary key,name_sa text,name_en text,category text,formation_rule_jsonb jsonb,formation_text text,effects_text text,severity_grades jsonb,cancellation_conditions jsonb,classical_citations jsonb,source_chunk_ids bigint[],associated_remedies uuid[],school text);
 CREATE TABLE brahma_ontology(entity_class text,canonical_id text,canonical_name_en text,canonical_name_sa text,synonyms text[],description text,source_citation text,primary key(entity_class,canonical_id));CREATE TABLE reference_doshas(canonical_id text primary key,name_en text,category text);
 INSERT INTO brahma_dosha_catalog SELECT 'd'||lpad(i::text,2,'0'),'N'||i,'N'||i,'other','{}','formation','effect','{}','{}','[]','{}','{}','parashari' FROM generate_series(1,79)i;
 INSERT INTO brahma_ontology SELECT 'dosha',canonical_id,name_en,name_sa,'{}',effects_text,'source' FROM brahma_dosha_catalog;INSERT INTO reference_doshas SELECT canonical_id,name_en,category FROM brahma_dosha_catalog;
 INSERT INTO asset_registry VALUES('bg_doshas','brahmagyan',11,'global','data','CURRENT',true,true,'brahma_dosha_catalog',$c$${countSql}$c$,237,ARRAY['bg_ontology'],NULL,NULL,NULL,'Classical dosha definitions — formation rules, effects, severity, cancellation conditions',$e$${explanation}$e$);`);return c}
 async function fixture(c:Client){const qs=[`SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,effects_text,severity_grades,cancellation_conditions,classical_citations,source_chunk_ids,associated_remedies,school)::text,E'\\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')d FROM brahma_dosha_catalog`,`SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)::text,E'\\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex')d FROM brahma_ontology WHERE entity_class='dosha'`,`SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_en,category)::text,E'\\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')d FROM reference_doshas`];let m=migration;for(let i=0;i<3;i++)m=m.replaceAll(digests[i],(await c.query(qs[i])).rows[0].d);return m}
 async function detector(c:Client){const r=await c.query("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_doshas'");return Object.values((await c.query(r.rows[0].integrity_check_sql)).rows[0])[0]===true}
 it('installs, replays, and catches semantic drift',async()=>{const c=await prep();try{const m=await fixture(c);await c.query(m);await c.query(m);expect(await detector(c)).toBe(true);await c.query("UPDATE brahma_dosha_catalog SET effects_text='drift' WHERE canonical_id='d01'");expect(await detector(c)).toBe(false)}finally{await c.end()}})
 it('accepts live legacy and rejects unknown registry drift',async()=>{const c=await prep();try{await c.query("UPDATE asset_registry SET target_floor=50,count_sql='SELECT count(*) FROM brahma_dosha_catalog',volume_explanation='Catalog of named dosha patterns (Manglik, Kala-sarpa, Kemadruma, etc.) per design §3.11'");const m=await fixture(c);await c.query(m);expect(await detector(c)).toBe(true);await c.query('UPDATE asset_registry SET target_floor=1');await expect(c.query(m)).rejects.toThrow('migration 622 refuses unknown')}finally{await c.end()}})
})
