import { afterAll,beforeAll,describe,expect,it } from 'vitest'
import { Client } from 'pg'
import { readFile } from 'node:fs/promises'
import { insertAttempt,insertReceipt,importRateCard,importRateCards,type MeteringDb } from '../repository'
import { parseUsageFilter,usageEvents,usageSummary,usageBreakdown,usageCsv } from '../queries'
import { normalizeSdkUsage } from '../usage'
import { recoverReceipts } from '../service'
import type { AttemptStart,AttemptReceipt } from '../types'
import type { RecoveryEnvelope,RecoveryStore } from '../recovery'
const enabled=!!process.env.AI_METERING_TEST_DATABASE_URL
const client=new Client({connectionString:process.env.AI_METERING_TEST_DATABASE_URL})
const db:MeteringDb={query:async(sql,params)=>{const result=await client.query(sql,params);return{rows:result.rows,rowCount:result.rowCount??0}}}
const attempt=(userId='alice',extra:Partial<AttemptStart>={}):AttemptStart=>({attemptId:crypto.randomUUID(),userId,conversationId:'conversation',turnId:'turn',operationId:crypto.randomUUID(),
 channel:'web',purpose:'customer',payer:'user',provider:'openai',model:'model',role:'planner',aggregation:'transport',startedAt:'2026-09-29T10:00:00.000Z',...extra})
const receipt=(start:AttemptStart):AttemptReceipt=>({attemptId:start.attemptId,finishedAt:'2026-09-29T10:00:01.000Z',status:'success',
 usage:normalizeSdkUsage({inputTokens:{total:100,cacheRead:20,cacheWrite:0},outputTokens:{total:10,reasoning:3}}),
 providerRequestId:'req-safe',finishReason:'stop',firstTokenAt:'2026-09-29T10:00:00.500Z',providerCostUsd:null})
const filter=(params='')=>parseUsageFilter(new URL(`http://localhost/api/usage?from=2026-09-29T00:00:00Z&to=2026-09-30T00:00:00Z&${params}`),{ownerId:'alice'})
const rate=(effectiveFrom='2026-09-01T00:00:00.000Z',inputPerMillion='2')=>({id:crypto.randomUUID(),provider:'openai',model:'model',effectiveFrom,observedAt:'2026-09-29T09:00:00.000Z',sourceUrl:'https://openai.com/api/pricing/',inputPerMillion,outputPerMillion:'8',cacheReadPerMillion:'0.2',cacheWritePerMillion:null,reasoningPerMillion:null,outputIncludesReasoning:true,maxInputTokens:null})

describe.skipIf(!enabled)('disposable PostgreSQL ledger',()=>{
 beforeAll(async()=>{
  await client.connect()
  await client.query(`CREATE ROLE amjis_app;CREATE ROLE browser_reader;
   CREATE TABLE llm_usage_events(event_id uuid PRIMARY KEY, user_id text,conversation_id text,prompt_id text,parent_prompt_id text,channel text,
   provider text,model text,pipeline_stage text,started_at timestamptz,finished_at timestamptz,status text,parameters jsonb,
   input_tokens bigint,output_tokens bigint,cache_read_tokens bigint,cache_write_tokens bigint,reasoning_tokens bigint,provider_request_id text,computed_cost_usd numeric)`)
  const sql=await readFile('supabase/migrations/1202_ai_metering_ledger.sql','utf8')
  await client.query('BEGIN');await client.query(sql);await client.query('COMMIT')
  await client.query('BEGIN');await client.query(sql);await client.query('COMMIT')
  // Production's referenced table is owned by the app role, not postgres.
  // The FK's FOR KEY SHARE therefore needs the owner's key-column privilege.
  await client.query('ALTER TABLE ai_metering_attempts OWNER TO amjis_app')
  const repair=await readFile('supabase/migrations/1203_ai_metering_receipt_fk_permission.sql','utf8')
  await client.query('BEGIN');await client.query(repair);await client.query('COMMIT')
  await client.query('BEGIN');await client.query(repair);await client.query('COMMIT')
 },30000)
 afterAll(async()=>{await client.end()})
 it('applies idempotently and gates browser roles with RLS',async()=>{
  await client.query('SET ROLE browser_reader')
  await expect(client.query('SELECT * FROM ai_metering_attempts')).rejects.toThrow(/permission denied/)
  await client.query('RESET ROLE')
  await client.query('SET ROLE amjis_app');expect((await client.query('SELECT count(*) FROM ai_metering_attempts')).rows[0].count).toBe('0');await client.query('RESET ROLE')
 })
 it('persists terminal receipts as the production app role while evidence stays immutable',async()=>{
  const start=attempt('fk-test-owner'),done=receipt(start)
  await client.query('SET ROLE amjis_app')
  try {
   await insertAttempt(start,db)
   await insertReceipt(start,done,db)
   expect((await client.query('SELECT count(*) FROM ai_metering_receipts WHERE attempt_id=$1',[start.attemptId])).rows[0].count).toBe('1')
   await expect(client.query('UPDATE ai_metering_attempts SET attempt_id=attempt_id WHERE attempt_id=$1',[start.attemptId])).rejects.toThrow(/append-only/)
  } finally {await client.query('RESET ROLE')}
 })
 it('records disjoint quantities, freezes decimal cost and deduplicates deliveries',async()=>{
  await importRateCard(rate(),db)
  const start=attempt();await insertAttempt(start,db);await insertAttempt(start,db)
  await insertReceipt(start,receipt(start),db);await insertReceipt(start,receipt(start),db)
  const data=await client.query('SELECT *,computed_cost_usd::text AS computed_cost_usd FROM ai_metering_receipts WHERE attempt_id=$1',[start.attemptId])
  expect(data.rows).toHaveLength(1);expect(data.rows[0].computed_cost_usd).toBe('0.000244000000')
  await importRateCard(rate('2026-09-29T09:30:00.000Z','10'),db)
  expect((await client.query('SELECT computed_cost_usd::text FROM ai_metering_receipts WHERE attempt_id=$1',[start.attemptId])).rows[0].computed_cost_usd).toBe('0.000244000000')
 })
 it('rejects updates, deletes and truncation on every evidence table',async()=>{
  for(const table of ['ai_metering_attempts','ai_metering_receipts','ai_metering_rate_cards']) {
   await expect(client.query(`UPDATE ${table} SET recorded_at=now()`)).rejects.toThrow(/append-only/)
   await expect(client.query(`DELETE FROM ${table}`)).rejects.toThrow(/append-only/)
   await expect(client.query(`TRUNCATE ${table} CASCADE`)).rejects.toThrow(/append-only/)
  }
 })
 it('separates owners, preserves unknown costs and pages without dropping ties',async()=>{
  const alice=attempt('alice',{model:'no-rate'}),bob=attempt('bob'),pending=attempt()
  await insertAttempt(alice,db);await insertReceipt(alice,receipt(alice),db)
  await insertAttempt(bob,db);await insertReceipt(bob,receipt(bob),db);await insertAttempt(pending,db)
  const total=await usageSummary(filter(),{ownerId:'alice'},db)
  expect(total.attempts).toBe(3);expect(total.pending).toBe(1);expect(total.unpriced).toBe(2);expect(total.unknown_usage).toBe(1)
  const page=await usageEvents(filter('limit=1'),{ownerId:'alice'},db);expect(page.events).toHaveLength(1);expect(page.nextCursor).toBeTruthy()
  const next=await usageEvents(filter(`limit=1&cursor=${page.nextCursor}`),{ownerId:'alice'},db)
  expect(next.events[0].id).not.toBe(page.events[0].id);expect(next.events[0].user_id).toBe('alice')
  const detail=await usageEvents(filter('view=trace&turnId=turn'),{ownerId:'alice'},db);expect(detail.events).toHaveLength(3)
  expect((await usageSummary({...filter(),model:'absent'},{ownerId:'alice'},db)).known_cost_usd).toBeNull()
  const grouped=await usageBreakdown(filter('groupBy=channel'),{ownerId:'alice'},db);expect(grouped.groups[0].name).toBe('web')
 })
 it('does not duplicate a compatibility aggregate and labels historical usage',async()=>{
  const start=attempt();await insertAttempt(start,db)
  const insert=`INSERT INTO llm_usage_events(event_id,user_id,prompt_id,provider,model,pipeline_stage,channel,started_at,finished_at,status,input_tokens,output_tokens,computed_cost_usd) VALUES($1,'alice',$2,'openai','old','planner','web','2026-09-29T10:00:00Z','2026-09-29T10:00:01Z','success',2,3,0.2)`
  await client.query(insert,[crypto.randomUUID(),start.operationId]);await client.query(insert,[crypto.randomUUID(),'historic-operation'])
  const data=await usageEvents(filter(),{ownerId:'alice'},db)
  expect(data.events.filter(row=>row.evidence==='legacy')).toHaveLength(1)
  expect(data.events.find(row=>row.evidence==='legacy')?.computed_cost_usd).toBeNull()
 })
 it('preserves sub-millisecond legacy ordering in cursor pagination',async()=>{
  const ids=[crypto.randomUUID(),crypto.randomUUID()]
  for(let i=0;i<2;i++)await client.query(`INSERT INTO llm_usage_events(event_id,user_id,prompt_id,provider,model,pipeline_stage,started_at,finished_at,status,input_tokens,output_tokens)
   VALUES($1::uuid,'alice',$1::uuid::text,'openai','microsecond','planner',$2,$2,'success',1,1)`,[ids[i],`2026-09-29T11:00:00.12345${6-i}Z`])
  const first=await usageEvents(filter('model=microsecond&limit=1'),{ownerId:'alice'},db)
  const second=await usageEvents(filter(`model=microsecond&limit=1&cursor=${first.nextCursor}`),{ownerId:'alice'},db)
  expect(first.events[0].id).toBe(ids[0]);expect(second.events).toHaveLength(1);expect(second.events[0].id).toBe(ids[1])
 })
 it('replays safe buffered receipts idempotently and refuses injected payloads',async()=>{
  const start=attempt(),envelope:RecoveryEnvelope={version:1,start,receipt:receipt(start)}
  let removed=0
  const store:RecoveryStore={put:async()=>{},list:async()=>[start.attemptId],read:async()=>envelope,remove:async()=>{removed++}}
  expect(await recoverReceipts({db,recovery:store})).toEqual({recovered:1,failed:0})
  expect(await recoverReceipts({db,recovery:store})).toEqual({recovered:1,failed:0});expect(removed).toBe(2)
  const bad={...envelope,receipt:{...envelope.receipt,usage:{...envelope.receipt.usage,raw:{secret:1}}}}
  store.read=async()=>bad as RecoveryEnvelope
  expect(await recoverReceipts({db,recovery:store})).toEqual({recovered:0,failed:1});expect(removed).toBe(2)
 })
 it('imports a catalog in one idempotent append',async()=>{
  const card={...rate(),provider:'openrouter',model:'bulk-rate',sourceUrl:'https://openrouter.ai/api/v1/models'}
  expect(await importRateCards([card],db)).toBe(1);expect(await importRateCards([card],db)).toBe(0)
  await expect(importRateCards([{...card,id:crypto.randomUUID(),model:'unsafe',sourceUrl:'https://attacker.invalid'}],db)).rejects.toThrow()
 })
 it('rejects conflicting start metadata during replay',async()=>{
  const start=attempt();await insertAttempt(start,db)
  await expect(insertAttempt({...start,userId:'bob'},db)).rejects.toThrow('Conflicting attempt evidence')
 })
 it('enforces valid pricing states in the database',async()=>{
  const start=attempt();await insertAttempt(start,db)
  await expect(client.query(`INSERT INTO ai_metering_receipts(attempt_id,finished_at,status,usage,pricing_status,pricing_snapshot)
    VALUES($1,now(),'success','{}','priced','{}')`,[start.attemptId])).rejects.toThrow(/check constraint/)
 })
 it('exports metadata without spreadsheet formulas or content',async()=>{
  const data=await usageEvents(filter(),{ownerId:'alice'},db)
  const csv=usageCsv([{...data.events[0],model:'=HYPERLINK("bad")'}])
  expect(csv).toContain("'=HYPERLINK");expect(csv).not.toContain('pricing_snapshot');expect(csv).not.toContain('prompt_text')
 })
})
