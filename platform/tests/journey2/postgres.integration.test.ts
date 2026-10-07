/** Real application SQL against the task-owned, disposable PostgreSQL only. */
import { beforeAll, beforeEach, afterAll, describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { Pool } from 'pg'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { ReadingView } from '@/components/chat/ReadingView'
const identity = vi.hoisted(() => ({ uid: 'journey2-owner' }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: async () => ({ uid: identity.uid }) }))
vi.mock('next/cache', () => ({ revalidatePath: vi.fn() }))
vi.mock('next/navigation', () => ({ redirect: (url: string) => { throw new Error(`redirect:${url}`) }, notFound: () => { throw new Error('not-found') } }))
import { query, getPool, withTransaction } from '@/lib/db/client'
import { POST as share, GET as currentShare, DELETE as revoke } from '@/app/api/conversations/[id]/share/route'
import { GET as exportReading } from '@/app/api/conversations/[id]/export/route'
import { GET as restoreConsultation, PATCH as tagConsultation } from '@/app/api/conversations/[id]/consultation/route'
import LegacyReading from '@/app/readings/[id]/page'
import { POST as logPrediction } from '@/app/api/pariprashna/samiksha/confirm/route'
import { publicReading } from '@/lib/share/publicReading'
import { readingContext, readingMessages } from '@/lib/conversations/reading'
import { setConsultationTag, consultationHistory } from '@/lib/conversations/consultation'
import { batchResolveAction, confirmCandidateAction, editCandidateAction } from '@/app/clients/[id]/samiksha/actions'
import { createLedgerRow, transitionLifecycle } from '@/lib/pariprashna/samiksha/writer'
import { recordConversationalOutcome } from '@/lib/pariprashna/samiksha/outcome_recorder'
import { captureDetectedCandidates } from '@/lib/pariprashna/samiksha/capture'
import { runDailyJob } from '@/lib/pariprashna/samiksha/daily_job'
import { RecordingTransport } from '@/lib/pariprashna/samiksha/digest'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
const url = process.env.JOURNEY2_TEST_DATABASE_URL
let pool: Pool
const chart = '22222222-2222-4222-8222-222222222222'
const conversation = '11111111-1111-4111-8111-111111111111'
const q1 = '33333333-3333-4333-8333-333333333333', a1 = '44444444-4444-4444-8444-444444444444'
const q2 = '55555555-5555-4555-8555-555555555555', a2 = '66666666-6666-4666-8666-666666666666'
const candidatePart = '77777777-7777-4777-8777-777777777777'
const stamp = { build_id: 'source-build', priors_version: 'source-priors', formula_versions: { salience_formula_ver: null }, ranking_config: { mode: 'composite_v1' }, now_context_date: '2026-10-01', computed_at: '2026-10-01T10:00:00Z' }
const ctx = { params: Promise.resolve({ id: conversation }) }
const request = (body: unknown, method = 'POST', suffix = '') => new Request(`http://localhost/api/conversations/${conversation}/share${suffix}`, { method, headers: { 'content-type': 'application/json', origin: 'http://localhost' }, ...(method === 'POST' ? { body: JSON.stringify(body) } : {}) })
const makeShare = async (body: object = {}) => {
  const response = await share(request(body), ctx)
  expect(response.status).toBe(200)
  return (await response.json()).slug as string
}
const text = (messages: unknown) => JSON.stringify(messages)
async function ledger(state: 'detected' | 'window_closed' = 'window_closed', part?: string) {
  const row = await createLedgerRow({ chart_id: chart, message_part_id: part ?? null, claim_text: 'A synthetic prediction', window: { start: '2026-01-01', end: '2026-01-31' }, confidence: { low: .5, high: .7 } })
  if (state === 'detected') return row
  await transitionLifecycle(row.id, 'confirmed', { stamp })
  await transitionLifecycle(row.id, 'open')
  return transitionLifecycle(row.id, 'window_closed')
}
const candidate = { claim_text: 'FORGED CLIENT CLAIM', domain: null, window_start: null, window_end: null, direction: null, technique_refs: ['FORGED_GROUNDING'], grounding_fact_ids: [], score: .9, horizon_text: null }
const confirmRequest = (extra = {}) => new Request('http://localhost/api/pariprashna/samiksha/confirm', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action: 'confirm', chartId: chart, conversationId: conversation, messagePartId: candidatePart, candidate, confidence: { low: .6, high: .8 }, ...extra }) })

describe.skipIf(!url)('Journey Two real PostgreSQL integration', () => {
  beforeAll(async () => {
    const target = new URL(url!)
    if (target.hostname !== '127.0.0.1' || target.port !== '60260' || target.pathname !== '/journey2_test' || target.username !== 'postgres') throw new Error('Refusing non-task-owned test database')
    process.env.DATABASE_URL = url
    pool = await getPool()
    await query('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
    const baseline = readFileSync('migrations/001_baseline.sql', 'utf8')
    for (const name of ['profiles', 'charts', 'chart_grants', 'conversations', 'conversation_messages', 'conversation_shares']) {
      const ddl = baseline.match(new RegExp(`CREATE TABLE(?: IF NOT EXISTS)? public\\.${name} \\([\\s\\S]*?\\n\\);`))?.[0]
      if (!ddl) throw new Error(`Missing authoritative DDL for ${name}`)
      await query(ddl)
    }
    // Unrelated build-run fields are not exercised; this FK target is a test scaffold.
    await query('CREATE TABLE build_runs (id uuid PRIMARY KEY)')
    for (const file of ['467_pariprashna_canonical_message_parts.sql', '470_pariprashna_samiksha_prediction_ledger.sql', '1120_jataka_conversation_archive_context.sql', '1307_consultation_tags.sql','588_samiksha_digest_journal.sql']) await query(readFileSync(`supabase/migrations/${file}`, 'utf8'))
    const staleness = readFileSync('supabase/migrations/1123_jataka_context_staleness_deferred_surfaces.sql', 'utf8')
    await query(staleness.match(/ALTER TABLE public\.brahma_mimamsa_prediction_ledger[\s\S]*?;/)![0])
    for (let i = 0; i < 2; i++) await withTransaction(async client => { await client.query(readFileSync('migrations/1312_journey2_exchange_shares.sql', 'utf8')) })
  }, 30_000)
  beforeEach(async () => {
    identity.uid = 'journey2-owner'
    await query('TRUNCATE pariprashna_samiksha_digest_journal, brahma_mimamsa_prediction_ledger, message_parts, conversation_shares, conversation_messages, conversations, chart_grants, charts, profiles CASCADE')
    await query("INSERT INTO profiles(id,role) VALUES ('journey2-owner','guest'),('journey2-other','guest'),('journey2-admin','super_admin')")
    await query("INSERT INTO charts(id,name,birth_date,birth_time,birth_place,owner_id) VALUES ($1,'Synthetic Journey Two','2000-01-01','12:00','Synthetic','journey2-owner')", [chart])
    await query("INSERT INTO conversations(id,chart_id,user_id,module,title) VALUES ($1,$2,'journey2-owner','consume','Synthetic consultation')", [conversation, chart])
    for (const [id, role, content, at] of [[q1,'user','First question','2026-10-01T10:00:00Z'],[a1,'assistant','LEGACY SHADOW','2026-10-01T10:00:01.123456Z'],[q2,'user','Second question','2026-10-02T10:00:00Z'],[a2,'assistant','Later answer','2026-10-02T10:00:01Z']]) await query('INSERT INTO conversation_messages(id,conversation_id,role,parts_json,metadata_json,created_at) VALUES($1,$2,$3,$4,$5,$6)', [id, conversation, role, JSON.stringify([{ type:'text',text:content }]), JSON.stringify({ provenance_stamp: id === a1 ? stamp : { ...stamp, build_id:'later-build' }, provider_secret:'PRIVATE_METADATA', acharya_reading_receipt:{} }), at])
    await query('UPDATE conversation_messages SET schema_version=1 WHERE id=$1', [a1])
    await query("INSERT INTO message_parts(message_id,seq,kind,body,model_visible) VALUES ($1,0,'text',$2,true),($1,1,'reasoning',$3,false),($1,2,'tool_result',$4,false)", [a1, JSON.stringify({text:'Canonical first answer\n\n## Methodology\nPRIVATE_METHOD\n\n## Next steps\nVisible guidance'}), JSON.stringify({text:'OPTIONAL_REASONING'}), JSON.stringify({provider_payload:'PRIVATE_TOOL'})])
    await query("INSERT INTO message_parts(message_id,seq,kind,body,model_visible) VALUES($1,4,'citation',$2,false)",[a1,JSON.stringify({index:1,signal_id:'ACTUAL_SOURCE',layer:'L0',snippet:'Source excerpt',reader_label:'Reader source'})])
    await query("INSERT INTO message_parts(id,message_id,seq,kind,body,model_visible) VALUES($1,$2,3,'prediction_candidate',$3,false)", [candidatePart,a1,JSON.stringify({claim:'A synthetic prediction',confidence:.9,window:'January 2026'})])
  })
  afterAll(async () => { if (pool) { await pool.end(); delete (globalThis as { __pgPool?: Pool }).__pgPool } })
  it('applies migration twice without duplicate FK/index', async () => {
    const { rows } = await query("SELECT count(*)::int n FROM pg_constraint WHERE conrelid='conversation_shares'::regclass AND confrelid='conversation_messages'::regclass")
    expect(rows[0].n).toBe(1)
    expect((await query("SELECT indexdef FROM pg_indexes WHERE indexname='idx_conversation_shares_message'")).rows[0].indexdef).toContain('WHERE (message_id IS NOT NULL)')
  })
  it('shares only the selected question/answer using canonical prose and disclosure options', async () => {
    const slug = await makeShare({messageId:a1,hide_reasoning:true,hide_methodology:true})
    const reading = await publicReading(slug)
    expect(reading.state).toBe('ready')
    const output = text(reading)
    expect(output).toContain('First question'); expect(output).toContain('Canonical first answer'); expect(output).toContain('Visible guidance'); expect(output).toContain('Reader source'); expect(output).toContain('Source excerpt')
    for (const privateText of ['Second question','Later answer','LEGACY SHADOW','PRIVATE_METHOD','OPTIONAL_REASONING','PRIVATE_METADATA','PRIVATE_TOOL']) expect(output).not.toContain(privateText)
    expect((await currentShare(request(null,'GET',`?messageId=${a1}`),ctx)).status).toBe(200)
  })
  it('never exposes an excluded question through the selected answer title or export', async () => {
    await query("UPDATE conversations SET title='PRIVATE_FIRST_QUESTION_TOPIC' WHERE id=$1",[conversation])
    const reading = await publicReading(await makeShare({messageId:a2}))
    expect(reading.state).toBe('ready')
    if (reading.state === 'ready') expect(reading.title).toBe('Consultation answer')
    for (const excluded of ['PRIVATE_FIRST_QUESTION_TOPIC','First question','Canonical first answer']) expect(text(reading)).not.toContain(excluded)
    for (const format of ['json','md']) {
      const response = await exportReading(new Request(`http://localhost/export?format=${format}&messageId=${a2}`),ctx)
      expect(response.status).toBe(200)
      const output = await response.text()
      expect(output).toContain('Later answer'); expect(output).not.toContain('PRIVATE_FIRST_QUESTION_TOPIC')
    }
  })
  it('restores, forwards and tags genuine receipt-less answers while preserving access and archive guards', async () => {
    await query("UPDATE conversation_messages SET metadata_json=metadata_json-'acharya_reading_receipt' WHERE conversation_id=$1",[conversation])
    expect((await query("SELECT count(*)::int n FROM conversation_messages WHERE metadata_json ? 'acharya_reading_receipt'")).rows[0].n).toBe(0)
    const response = await restoreConsultation(new Request('http://localhost/consultation'),ctx)
    expect(response.status).toBe(200)
    const restored = await response.json()
    expect(restored.messages.some((m: {id:string})=>m.id===a2)).toBe(true)
    await expect(LegacyReading({params:Promise.resolve({id:a2})})).rejects.toThrow(`redirect:/clients/${chart}/pariprashna?thread=${conversation}&answer=${a2}#pp-answer-${a2}`)
    const patch = (messageId?:string) => tagConsultation(new Request('http://localhost/consultation',{method:'PATCH',headers:{'content-type':'application/json',origin:'http://localhost'},body:JSON.stringify({tagged:true,...(messageId?{messageId}:{})})}),ctx)
    expect((await patch(a2)).status).toBe(200)
    expect((await patch()).status).toBe(200)
    expect((await patch(q2)).status).toBe(409)
    const history = await consultationHistory(chart,identity.uid)
    expect(history).toHaveLength(1); expect(history[0].tagged).toBe(true)
    expect(history[0].tagged_answers).toEqual([{id:a2,text:'Later answer'}])
    identity.uid='journey2-other'
    expect((await restoreConsultation(new Request('http://localhost/consultation'),ctx)).status).toBe(404)
    expect((await patch(a2)).status).toBe(404)
    identity.uid='journey2-owner'
    await query("UPDATE conversations SET archived_at=now(),archive_reason='chart_details_changed',archived_chart_snapshot='{}' WHERE id=$1",[conversation])
    expect((await restoreConsultation(new Request('http://localhost/consultation'),ctx)).status).toBe(200)
    expect((await patch(a2)).status).toBe(409)
  })
  it('explicit reasoning visibility exposes text only, never provider metadata', async () => {
    const reading = await publicReading(await makeShare({messageId:a1}))
    expect(text(reading)).toContain('OPTIONAL_REASONING'); expect(text(reading)).not.toContain('PRIVATE_TOOL'); expect(text(reading)).not.toContain('PRIVATE_METADATA')
  })
  it('serializes concurrent identical link creation', async () => {
    const slugs = await Promise.all([makeShare({messageId:a1}),makeShare({messageId:a1}),makeShare({messageId:a1})])
    expect(new Set(slugs).size).toBe(1)
    expect((await query('SELECT count(*)::int n FROM conversation_shares')).rows[0].n).toBe(1)
  })
  it('revokes one exchange without revoking the conversation or another exchange', async () => {
    const first = await makeShare({messageId:a1}), second = await makeShare({messageId:a2}), whole = await makeShare()
    expect((await revoke(request(null,'DELETE',`?messageId=${a1}`),ctx)).status).toBe(200)
    expect((await publicReading(first)).state).toBe('unavailable')
    expect((await publicReading(second)).state).toBe('ready'); expect((await publicReading(whole)).state).toBe('ready')
  })
  it('hides expired links, creates a fresh replacement, rejects invalid scopes and cross-origin writes', async () => {
    const old = await makeShare({messageId:a1})
    await query("UPDATE conversation_shares SET expires_at=now()-interval '1 second' WHERE slug=$1",[old])
    expect((await publicReading(old)).state).toBe('unavailable')
    expect(await makeShare({messageId:a1})).not.toBe(old)
    expect((await share(request({messageId:q1}),ctx)).status).toBe(404)
    const foreign = request({}); foreign.headers.set('origin','https://foreign.invalid')
    expect((await share(foreign,ctx)).status).toBe(403)
  })
  it('deleting the selected legacy answer cascades its share', async () => {
    const slug = await makeShare({messageId:a2})
    await query('DELETE FROM conversation_messages WHERE id=$1',[a2])
    expect((await publicReading(slug)).state).toBe('missing')
  })
  it('does not give another user or super-admin ownership of private shares/exports', async () => {
    for (const uid of ['journey2-other','journey2-admin']) {
      identity.uid=uid
      expect((await share(request({}),ctx)).status).toBe(404)
      expect((await exportReading(new Request('http://localhost/export?format=json'),ctx)).status).toBe(404)
    }
  })
  it('rechecks active membership and revoked chart grants for existing public links', async () => {
    const slug = await makeShare()
    await query("UPDATE charts SET owner_id='journey2-other' WHERE id=$1",[chart])
    await query("INSERT INTO chart_grants(chart_id,principal_id,granted_by) VALUES($1,'journey2-owner','journey2-other')",[chart])
    expect((await publicReading(slug)).state).toBe('ready')
    await query('DELETE FROM chart_grants')
    expect((await publicReading(slug)).state).toBe('unavailable')
    await query("UPDATE profiles SET status='disabled' WHERE id='journey2-owner'")
    expect(await resolveChartPageAccess(chart)).toBeNull()
    expect((await share(request({}),ctx)).status).toBe(404)
  })
  it('preserves original saved timestamps in JSON, Markdown and private/public print rendering', async () => {
    const response = await exportReading(new Request(`http://localhost/export?format=json&messageId=${a1}`),ctx)
    expect(response.headers.get('cache-control')).toBe('private, no-store')
    const result = await response.json()
    expect(result.messages).toHaveLength(2); expect(result.messages[1].content).toContain('Canonical first answer'); expect(result.messages[1].timestamp).toBe('2026-10-01T10:00:01.123456Z')
    const md = await exportReading(new Request(`http://localhost/export?format=md&messageId=${a1}`),ctx)
    expect(await md.text()).toContain('**Saved:** 2026-10-01T10:00:01.123456Z')
    const privateHtml = renderToStaticMarkup(createElement(ReadingView, { messages: await readingMessages(conversation, a1) }))
    const shared = await publicReading(await makeShare({ messageId: a1, hide_reasoning: true, hide_methodology: true }))
    expect(shared.state).toBe('ready')
    if (shared.state !== 'ready') throw new Error('Expected readable disposable share')
    const publicHtml = renderToStaticMarkup(createElement(ReadingView, { messages: shared.messages }))
    for (const html of [privateHtml, publicHtml]) {
      expect(html).toContain('dateTime="2026-10-01T10:00:01.123456Z"')
      expect(html).toContain('Saved 2026-10-01 10:00:01.123456 UTC')
      expect(html).toContain('Reader source')
      expect(html).not.toContain('Later answer')
    }
    const pdf = await exportReading(new Request(`http://localhost/export?format=pdf&messageId=${a1}`),ctx)
    expect(pdf.status).toBe(307); expect(pdf.headers.get('location')).toContain(`/clients/${chart}/pariprashna/print?conversationId=${conversation}&messageId=${a1}`)
  })
  it('uses saved follow-up context instead of client-invented assistant history', async () => {
    const messages = await readingContext(conversation, [{id:randomUUID(),role:'assistant',parts:[{type:'text',text:'FORGED_HISTORY'}]},{id:randomUUID(),role:'user',parts:[{type:'text',text:'Follow-up question'}]}])
    expect(messages).toHaveLength(5); expect(text(messages)).toContain('Canonical first answer'); expect(text(messages)).not.toContain('FORGED_HISTORY'); expect(text(messages)).not.toContain('PRIVATE_TOOL')
  })
  it('archives prevent new shares and edits but retain existing read-only reading access', async () => {
    const slug=await makeShare()
    await query("UPDATE conversations SET archived_at=now(),archive_reason='chart_details_changed',archived_chart_snapshot='{}' WHERE id=$1",[conversation])
    expect((await share(request({}),ctx)).status).toBe(409)
    expect(await setConsultationTag(conversation,identity.uid,true,a1)).toBe(false)
    expect((await publicReading(slug)).state).toBe('ready')
  })
  it('confirms the captured row once using the exact source stamp and server claim', async () => {
    const row=await ledger('detected',candidatePart)
    const first=await logPrediction(confirmRequest() as never)
    expect(first.status).toBe(200)
    const value=(await first.json()).ledger_row
    expect(value.id).toBe(row.id); expect(value.lifecycle_status).toBe('open'); expect(value.build_id).toBe('source-build'); expect(value.claim_text).toBe('A synthetic prediction'); expect(value.confidence).toBe('[0.6,0.8)')
    expect((await logPrediction(confirmRequest() as never)).status).toBe(200)
    expect((await query('SELECT count(*)::int n FROM brahma_mimamsa_prediction_ledger')).rows[0].n).toBe(1)
    await expect(query("UPDATE brahma_mimamsa_prediction_ledger SET claim_text='rewritten' WHERE id=$1",[row.id])).rejects.toThrow(/immutable once/)
  })
  it('review confirmation copies the source answer instead of a later turn', async () => {
    const row=await ledger('detected',candidatePart)
    await query('UPDATE brahma_mimamsa_prediction_ledger SET confidence=NULL WHERE id=$1',[row.id])
    await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.7})
    const saved=(await query('SELECT * FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0]
    expect(saved.build_id).toBe('source-build'); expect(saved.lifecycle_status).toBe('open')
    await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.1})
    expect((await query('SELECT * FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0]).toEqual(saved)
    await expect(editCandidateAction({chartId:chart,rowId:row.id,claimText:'changed'})).rejects.toThrow(/no longer editable/)
  })
  it('accepts a stale review confirmation after stream confirmation without changing the settled row', async () => {
    const row=await ledger('detected',candidatePart)
    expect((await logPrediction(confirmRequest() as never)).status).toBe(200)
    const saved=(await query('SELECT * FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0]
    await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.1})
    expect((await query('SELECT * FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0]).toEqual(saved)
    await transitionLifecycle(row.id,'window_closed')
    await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.1})
    expect((await query('SELECT lifecycle_status FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0].lifecycle_status).toBe('window_closed')
  })
  it('confirms through a one-connection pool without nested checkout', async () => {
    const row=await ledger('detected',candidatePart)
    const single=new Pool({connectionString:url,max:1,connectionTimeoutMillis:300})
    const cache=globalThis as {__pgPool?:Pool}
    const previous=cache.__pgPool
    cache.__pgPool=single
    try {
      await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.7})
      expect((await query('SELECT lifecycle_status FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0].lifecycle_status).toBe('open')
      await confirmCandidateAction({chartId:chart,rowId:row.id,probability:.1})
    } finally { cache.__pgPool=previous; await single.end() }
  }, 3000)
  it('refuses confirmation of dismissed, lapsed or stale candidates', async () => {
    for (const state of ['dismissed','lapsed_unconfirmed'] as const) {
      const row=await ledger('detected')
      await transitionLifecycle(row.id,state)
      await expect(confirmCandidateAction({chartId:chart,rowId:row.id,probability:.7})).rejects.toThrow(/unavailable/)
    }
    const stale=await ledger('detected',candidatePart)
    await query('UPDATE brahma_mimamsa_prediction_ledger SET chart_context_stale_at=now() WHERE id=$1',[stale.id])
    await expect(confirmCandidateAction({chartId:chart,rowId:stale.id,probability:.7})).rejects.toThrow(/unavailable/)
  })
  it('missing provenance rolls back confirmation and confidence edits', async () => {
    const row=await ledger('detected',candidatePart)
    await query("UPDATE conversation_messages SET metadata_json='{}' WHERE id=$1",[a1])
    expect((await logPrediction(confirmRequest() as never)).status).toBe(409)
    expect((await query('SELECT lifecycle_status,confidence::text confidence FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[row.id])).rows[0]).toEqual({lifecycle_status:'detected',confidence:'[0.5,0.7)'})
  })
  it('a failed batch rolls back earlier outcomes and a successful batch commits all', async () => {
    const first=await ledger(), second=await ledger('detected')
    await expect(batchResolveAction({chartId:chart,items:[{rowId:first.id,outcome:'happened'},{rowId:second.id,outcome:'did_not_happen'}]})).rejects.toThrow(/window_closed/)
    expect((await query('SELECT lifecycle_status,outcome FROM brahma_mimamsa_prediction_ledger WHERE id=$1',[first.id])).rows[0]).toEqual({lifecycle_status:'window_closed',outcome:null})
    await transitionLifecycle(second.id,'confirmed',{stamp}); await transitionLifecycle(second.id,'open'); await transitionLifecycle(second.id,'window_closed')
    await batchResolveAction({chartId:chart,items:[{rowId:first.id,outcome:'happened'},{rowId:second.id,outcome:'unverifiable'}]})
    expect((await query("SELECT outcome_value FROM brahma_mimamsa_prediction_ledger WHERE id=$1",[second.id])).rows[0].outcome_value).toBeNull()
    const cross = await ledger(); await query('UPDATE brahma_mimamsa_prediction_ledger SET chart_id=$2 WHERE id=$1',[cross.id,randomUUID()])
    await expect(batchResolveAction({chartId:chart,items:[{rowId:cross.id,outcome:'happened'}]})).rejects.toThrow(/unavailable/)
  })
  it('persists outcome and Brier inputs honestly while reporting the parked calibration bridge', async () => {
    const row=await ledger()
    const result=await recordConversationalOutcome(row.id,{outcome:'happened'})
    expect(result.brier).toBeCloseTo(.16)
    expect(result.ledger_row.lifecycle_status).toBe('outcome_recorded'); expect(result.calibration_persisted).toBe(false)
  })
  it('capture is repeatable without duplicate human-confirmation rows', async () => {
    const input={chartId:chart,messageId:a1,candidates:[{text:'A synthetic prediction',score:.9,horizon:'January 2026',offset:0}],nowDate:'2026-10-01'}
    const first=await captureDetectedCandidates(input)
    const again=await captureDetectedCandidates(input)
    expect(first.created).toHaveLength(1); expect(again.created).toHaveLength(0); expect(again.skippedExisting).toBe(1)
  })
  it('closes due windows through the daily job and journals the digest once', async () => {
    const row=await ledger('detected')
    await transitionLifecycle(row.id,'confirmed',{stamp}); await transitionLifecycle(row.id,'open')
    const transport=new RecordingTransport()
    const first=await runDailyJob({asOf:'2026-10-07',chartId:chart,transport})
    expect(first.closed_row_ids).toContain(row.id)
    const again=await runDailyJob({asOf:'2026-10-07',chartId:chart,transport})
    expect(again.digest_dispatched).toBe(false); expect(transport.sent).toHaveLength(1)
    expect((await query('SELECT count(*)::int n FROM pariprashna_samiksha_digest_journal')).rows[0].n).toBe(1)
  })

  it('pairs an exchange correctly when question and answer share a timestamp', async () => {
    await query('UPDATE conversation_messages SET id=$2,created_at=(SELECT created_at FROM conversation_messages WHERE id=$3) WHERE id=$1',[q1,'ffffffff-ffff-4fff-8fff-ffffffffffff',a1])
    const reading=await publicReading(await makeShare({messageId:a1}))
    expect(text(reading)).toContain('First question')
  })

})
