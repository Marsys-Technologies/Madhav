import 'server-only'
import { z } from 'zod'
import { meteringDb, type MeteringDb } from './repository'
import { PROBE_USER_ID } from './attribution'

const Filter = z.object({ from: z.string().datetime({ offset: true }), to: z.string().datetime({ offset: true }),
  channel: z.enum(['web','mcp','api','backend','scheduled','unknown']).optional(),
  purpose: z.enum(['customer','admin_test','validation','evaluation','background','legacy']).optional(),
  provider: z.string().max(64).optional(), model: z.string().max(256).optional(),
  conversationId: z.string().min(1).max(512).optional(), turnId: z.string().min(1).max(512).optional(),
  recordId: z.string().uuid().optional(),
  userId: z.string().min(1).max(512).optional(), cursor: z.string().max(1500).optional(),
  limit: z.coerce.number().int().min(1).max(1000).default(100),
  groupBy: z.enum(['day','channel','purpose','provider','model','role','conversation','turn','user']).default('model'),
  view: z.enum(['summary','events','breakdown','conversations','trace','export']).default('summary') }).strict()
export type UsageFilter = z.infer<typeof Filter>
export interface UsageScope { ownerId: string | null }
export function parseUsageFilter(url: URL, scope: UsageScope, now = new Date()): UsageFilter {
  const raw = Object.fromEntries(url.searchParams)
  if (scope.ownerId && ('userId' in raw || raw.groupBy === 'user')) throw new Error('Owner scope cannot be overridden')
  const input = Filter.parse({ ...raw, from: raw.from ?? new Date(now.getTime()-30*86400000).toISOString(), to: raw.to ?? now.toISOString() })
  const elapsed = Date.parse(input.to)-Date.parse(input.from)
  if (elapsed <= 0 || elapsed > 90*86400000) throw new Error('Choose a period of up to 90 days')
  if (input.view === 'trace' && !input.turnId && !input.conversationId && !input.recordId) throw new Error('Choose a conversation, turn, or call')
  return input
}
// Historical aggregates remain visible, but carry their own evidence class.
// Exact invocation IDs exclude compatibility observations already represented by transport leaves.
const DATA = `WITH evidence AS (
 SELECT a.attempt_id::text AS id,a.user_id,a.conversation_id,a.turn_id,a.operation_id,a.parent_operation_id,
 CASE WHEN a.user_id='${PROBE_USER_ID}' AND a.purpose='customer' AND a.channel='web' THEN 'api' ELSE a.channel END AS channel,
 CASE WHEN a.user_id='${PROBE_USER_ID}' AND a.purpose='customer' THEN 'validation' ELSE a.purpose END AS purpose,
 a.payer,a.provider,a.model,a.role,a.connection_id,a.snapshot_id,a.test_run_id,a.aggregation,
 a.started_at,r.finished_at,COALESCE(r.status,'pending') AS status,
 r.usage,r.provider_request_id,r.finish_reason,r.first_token_at,r.provider_cost_usd::text,
 r.computed_cost_usd::text,r.pricing_status,r.pricing_snapshot,'metered'::text AS evidence,
 NULL::text AS legacy_cost_usd
 FROM ai_metering_attempts a LEFT JOIN ai_metering_receipts r USING(attempt_id)
 UNION ALL
 SELECT e.event_id::text,e.user_id,e.conversation_id::text,e.prompt_id::text,e.prompt_id::text,e.parent_prompt_id::text,
 CASE WHEN e.channel IN ('web','mcp') THEN e.channel ELSE 'unknown' END,'legacy','unknown',e.provider,e.model,e.pipeline_stage,
 NULL,NULL,NULL,'legacy_aggregate',e.started_at,e.finished_at,e.status,
 jsonb_build_object('input',CASE WHEN e.status='success' THEN e.input_tokens END,
 'output',CASE WHEN e.status='success' THEN e.output_tokens END,
 'cacheRead',CASE WHEN e.status='success' THEN e.cache_read_tokens END,
 'cacheWrite',CASE WHEN e.status='success' THEN e.cache_write_tokens END,
 'reasoning',CASE WHEN e.status='success' THEN e.reasoning_tokens END,'source','legacy_reported'),
 e.provider_request_id,NULL,NULL,NULL,NULL,'legacy_estimate',NULL,'legacy',e.computed_cost_usd::text
 FROM llm_usage_events e WHERE COALESCE(e.parameters->>'metering_represented','false') <> 'true' AND NOT EXISTS (SELECT 1 FROM ai_metering_attempts a WHERE a.operation_id=e.prompt_id::text)
), filtered AS (SELECT * FROM evidence WHERE `
function where(input: UsageFilter, scope: UsageScope) {
  const params: unknown[] = [input.from,input.to]
  const clauses = ['started_at >= $1','started_at < $2']
  const owner = scope.ownerId ?? input.userId
  if (owner) { params.push(owner); clauses.push(`user_id=$${params.length}`) }
  for (const [key,column] of Object.entries({ channel:'channel',purpose:'purpose',provider:'provider',model:'model',conversationId:'conversation_id',turnId:'turn_id',recordId:'id' })) {
    const value = input[key as keyof UsageFilter]
    if (value !== undefined) { params.push(value); clauses.push(`${column}=$${params.length}`) }
  }
  return { params, cte: DATA+clauses.join(' AND ')+') ' }
}
export interface UsageEvent {
  id:string; cursor_at?:string; user_id:string; conversation_id:string|null; turn_id:string; operation_id:string; parent_operation_id:string|null;
  channel:string; purpose:string; payer:string; provider:string; model:string; role:string;
  connection_id:string|null; snapshot_id:string|null; test_run_id:string|null; aggregation:string;
  started_at:string; finished_at:string|null; status:string; evidence:'metered'|'legacy';
  usage: { input?:number|null; output?:number|null; cacheRead?:number|null; cacheWrite?:number|null; reasoning?:number|null; source?:string } | null;
  provider_request_id:string|null; finish_reason:string|null; first_token_at:string|null;
  provider_cost_usd:string|null; computed_cost_usd:string|null; legacy_cost_usd:string|null;
  pricing_status:string|null; pricing_snapshot:unknown;
}
const safeCursor = z.object({ time: z.string().datetime({ offset:true }), id: z.string().min(1).max(128) }).strict()
export async function usageEvents(input: UsageFilter, scope: UsageScope, db: MeteringDb = meteringDb()) {
  const { params,cte } = where(input,scope)
  let after = ''
  if (input.cursor) {
    const cursor = safeCursor.parse(JSON.parse(Buffer.from(input.cursor,'base64url').toString()))
    params.push(cursor.time,cursor.id); after = `WHERE (started_at,id)<($${params.length-1}::timestamptz,$${params.length}::text)`
  }
  params.push(input.limit+1)
  const { rows } = await db.query<UsageEvent>(cte+`SELECT *,to_char(started_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS cursor_at FROM filtered ${after} ORDER BY started_at DESC,id DESC LIMIT $${params.length}`,params)
  const events = rows.slice(0,input.limit)
  const last = events.at(-1)
  const nextCursor = rows.length > input.limit && last
    ? Buffer.from(JSON.stringify({ time:last.cursor_at ?? new Date(last.started_at).toISOString(),id:last.id })).toString('base64url') : null
  return { events,nextCursor }
}
const TOTALS = `count(*)::int AS records,
 count(*) FILTER(WHERE evidence='metered')::int AS attempts,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport')::int AS transport_attempts,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND purpose='customer')::int AS customer_attempts,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND purpose='validation')::int AS validation_attempts,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status='success')::int AS transport_success,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status IN ('error','timeout','cancelled','incomplete'))::int AS transport_failed,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status='pending')::int AS transport_pending,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND usage->>'input' IS NOT NULL AND usage->>'output' IS NOT NULL)::int AS complete_usage,
 count(*) FILTER(WHERE evidence='metered' AND aggregation='transport' AND computed_cost_usd IS NULL)::int AS transport_unpriced,
 count(*) FILTER(WHERE evidence='legacy')::int AS legacy_records,
 count(*) FILTER(WHERE evidence='metered' AND status='pending')::int AS pending,
 count(*) FILTER(WHERE evidence='metered' AND status='pending' AND started_at < now()-interval '15 minutes')::int AS stale_pending,
 count(*) FILTER(WHERE evidence='metered' AND status IN ('error','timeout','cancelled','incomplete'))::int AS failed,
 count(*) FILTER(WHERE evidence='metered' AND (usage->>'input' IS NULL OR usage->>'output' IS NULL))::int AS unknown_usage,
 count(*) FILTER(WHERE evidence='metered' AND computed_cost_usd IS NULL)::int AS unpriced,
 sum((usage->>'input')::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS input_tokens,
 sum((usage->>'output')::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS output_tokens,
 sum((usage->>'cacheRead')::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS cache_read_tokens,
 sum((usage->>'cacheWrite')::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS cache_write_tokens,
 sum((usage->>'reasoning')::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS reasoning_tokens,
 sum((usage->>'input')::numeric) FILTER(WHERE aggregation='cli_aggregate')::text AS cli_input_tokens,
 sum((usage->>'output')::numeric) FILTER(WHERE aggregation='cli_aggregate')::text AS cli_output_tokens,
 sum((usage->>'input')::numeric) FILTER(WHERE evidence='legacy')::text AS legacy_input_tokens,
 sum((usage->>'output')::numeric) FILTER(WHERE evidence='legacy')::text AS legacy_output_tokens,
 sum(computed_cost_usd::numeric)::text AS known_cost_usd,
 sum(computed_cost_usd::numeric) FILTER(WHERE evidence='metered' AND aggregation='transport')::text AS known_transport_cost_usd,
 sum(provider_cost_usd::numeric)::text AS provider_reported_cost_usd,
 sum(legacy_cost_usd::numeric)::text AS legacy_estimate_usd,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY extract(epoch FROM finished_at-started_at)*1000) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status='success') AS p50_ms,
 percentile_cont(0.95) WITHIN GROUP(ORDER BY extract(epoch FROM finished_at-started_at)*1000) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status='success') AS p95_ms,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY extract(epoch FROM finished_at-started_at)*1000) FILTER(WHERE evidence='metered' AND aggregation='transport' AND status='success') AS p50_success_ms`
export async function usageSummary(input: UsageFilter, scope: UsageScope, db: MeteringDb = meteringDb()) {
  const { params,cte } = where(input,scope)
  const { rows } = await db.query<Record<string,number|string|null>>(cte+`SELECT ${TOTALS} FROM filtered`,params)
  return rows[0]
}
const GROUPS = { day:"to_char(started_at AT TIME ZONE 'UTC','YYYY-MM-DD')",channel:'channel',purpose:'purpose',provider:'provider',model:'model',role:'role',conversation:'conversation_id',turn:'turn_id',user:'user_id' }
export async function usageBreakdown(input: UsageFilter, scope: UsageScope, db: MeteringDb = meteringDb()) {
  if (scope.ownerId && input.groupBy==='user') throw new Error('Owner scope cannot be overridden')
  const { params,cte } = where(input,scope)
  const { rows } = await db.query<Record<string,number|string|null>>(cte+`SELECT ${GROUPS[input.groupBy]} AS name, ${TOTALS}
    FROM filtered GROUP BY 1 ORDER BY sum(computed_cost_usd::numeric) DESC NULLS LAST,count(*) DESC LIMIT 200`,params)
  return { groups:rows,limit:200,timezone:'UTC' }
}
export interface UsageConversation {
  key:string; conversation_id:string|null; user_id:string; channel:string; purpose:string; model:string;
  first_at:string; last_at:string; cursor_at:string; turns:number; attempts:number; success:number;
  incomplete_usage:number; unpriced:number; input_tokens:string|null; output_tokens:string|null;
  known_cost_usd:string|null; snippet:string|null;
}
const conversationCursor = z.object({ time: z.string().datetime({ offset:true }), key: z.string().min(1).max(512),
  userId: z.string().min(1).max(512) }).strict()
export async function usageConversations(input: UsageFilter, scope: UsageScope, db: MeteringDb = meteringDb()) {
  const { params,cte } = where(input,scope)
  // Portal-wide rollups show metadata only; a focused owner/user scope may read text.
  params.push(Boolean(scope.ownerId || input.userId))
  const showSnippet = params.length
  let after = ''
  if (input.cursor) {
    const cursor = conversationCursor.parse(JSON.parse(Buffer.from(input.cursor,'base64url').toString()))
    params.push(cursor.time,cursor.key,cursor.userId)
    after = `WHERE (last_at,key,user_id)<($${params.length-2}::timestamptz,$${params.length-1}::text,$${params.length}::text)`
  }
  params.push(input.limit+1)
  const sql = cte+`, grouped AS (
    SELECT COALESCE(conversation_id,id) AS key, user_id, max(conversation_id) AS conversation_id,
      min(started_at) AS first_at, max(started_at) AS last_at,
      CASE WHEN count(DISTINCT channel)=1 THEN min(channel) ELSE 'mixed' END AS channel,
      CASE WHEN count(DISTINCT purpose)=1 THEN min(purpose) ELSE 'mixed' END AS purpose,
      min(model) AS model, count(DISTINCT turn_id)::int AS turns, count(*)::int AS attempts,
      count(*) FILTER(WHERE status='success')::int AS success,
      count(*) FILTER(WHERE usage->>'input' IS NULL OR usage->>'output' IS NULL)::int AS incomplete_usage,
      count(*) FILTER(WHERE computed_cost_usd IS NULL)::int AS unpriced,
      sum((usage->>'input')::numeric)::text AS input_tokens,
      sum((usage->>'output')::numeric)::text AS output_tokens,
      sum(computed_cost_usd::numeric)::text AS known_cost_usd
    FROM filtered WHERE evidence='metered' AND aggregation='transport'
    GROUP BY COALESCE(conversation_id,id),user_id
  ), paged AS (
    SELECT * FROM grouped ${after} ORDER BY last_at DESC,key DESC,user_id DESC LIMIT $${params.length}
  ), enriched AS (
    SELECT g.*, CASE WHEN $${showSnippet}::boolean THEN LEFT(COALESCE(
      (SELECT NULLIF(BTRIM(p.body->>'text'),'')
       FROM conversation_messages m JOIN message_parts p ON p.message_id=m.id
       WHERE m.conversation_id=c.id AND m.role='user' AND p.kind='text'
       ORDER BY m.created_at,m.id,p.seq LIMIT 1),
      (SELECT elem->>'text' FROM conversation_messages m,
        jsonb_array_elements(m.parts_json) elem
       WHERE m.conversation_id=c.id AND m.role='user' AND elem->>'type'='text'
       ORDER BY m.created_at,m.id LIMIT 1),NULLIF(BTRIM(c.title),'')),120) END AS snippet
    FROM paged g LEFT JOIN conversations c ON c.id::text=g.conversation_id AND c.user_id=g.user_id
  ) SELECT *,to_char(last_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS cursor_at
    FROM enriched ORDER BY last_at DESC,key DESC,user_id DESC`
  const { rows } = await db.query<UsageConversation>(sql,params)
  const conversations = rows.slice(0,input.limit)
  const last = conversations.at(-1)
  const nextCursor = rows.length > input.limit && last
    ? Buffer.from(JSON.stringify({time:last.cursor_at,key:last.key,userId:last.user_id})).toString('base64url') : null
  return { conversations,nextCursor }
}
export function usageCsv(events: UsageEvent[]) {
  const columns: (keyof UsageEvent)[] = ['id','user_id','conversation_id','turn_id','operation_id','channel','purpose','payer','provider','model','role','aggregation','evidence','status','started_at','finished_at','computed_cost_usd','provider_cost_usd','legacy_cost_usd','pricing_status']
  const cell = (value: unknown) => { let text = value == null ? '' : String(value)
    if (/^[\s]*[=+@-]/.test(text)) text = "'"+text
    return '"'+text.replaceAll('"','""')+'"' }
  const tokens = ['input','output','cacheRead','cacheWrite','reasoning'] as const
  return [...columns,...tokens].join(',')+'\r\n'+events.map(e => [...columns.map(c=>e[c]),...tokens.map(c=>e.usage?.[c])].map(cell).join(',')).join('\r\n')
}
