import 'server-only'
import { z } from 'zod'
import { query } from '@/lib/db/client'

const filters = z.object({ source: z.enum(['all','administration','ai_configuration']).default('all'),
  action: z.string().max(128).optional(), target: z.string().max(512).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(100),
  cursor: z.string().max(1500).optional() }).strict()
const cursorSchema = z.object({ time: z.string().datetime({ offset: true }), id: z.string().min(1).max(256) }).strict()
const SAFE_DETAIL = new Set(['key_id','cli_id','enabled','old_role','new_role','username','old_username','new_username',
  'chart_id','role','configuration_id','connection_id','configuration_version','error_code','deleted_user_id'])
export function safeAuditDetail(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return Object.fromEntries(Object.entries(value).filter(([key, v]) => SAFE_DETAIL.has(key) &&
    (v == null || typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')))
}
/** One read view, two canonical audit sources; no duplicated audit writer. */
export async function readAudit(url: URL) {
  const input = filters.parse(Object.fromEntries(url.searchParams))
  const values: unknown[] = []
  const clauses: string[] = []
  for (const [column, value] of [['source',input.source === 'all' ? undefined : input.source],['action',input.action],['target_user_id',input.target]]) {
    if (value) { values.push(value); clauses.push(`${column}=$${values.length}`) }
  }
  if (input.cursor) {
    const cursor = cursorSchema.parse(JSON.parse(Buffer.from(input.cursor,'base64url').toString()))
    values.push(cursor.time,cursor.id)
    clauses.push(`(created_at,id)<($${values.length-1}::timestamptz,$${values.length}::text)`)
  }
  values.push(input.limit+1)
  const result = await query<{
    id: string; actor_id: string | null; actor_name: string | null; actor_email: string | null; action: string;
    target_user_id: string | null; target_name: string | null; target_email: string | null;
    detail: unknown; created_at: string; cursor_at?: string; source: string
  }>(`WITH records AS (
    SELECT 'administration:'||l.id::text AS id,l.actor_id,l.action,l.target_user_id,l.detail,l.created_at,
      'administration'::text AS source FROM admin_audit_log l
    UNION ALL
    SELECT 'ai_configuration:'||a.id::text,a.actor_user_id,a.event,a.user_id,
      jsonb_build_object('connection_id',a.connection_id,'configuration_id',a.configuration_id,
      'configuration_version',a.configuration_version,'cli_id',a.cli_id,'error_code',a.error_code),
      a.created_at,'ai_configuration' FROM ai_configuration_audit_log a
  ), selected AS (SELECT * FROM records ${clauses.length ? 'WHERE '+clauses.join(' AND ') : ''})
  SELECT s.*,to_char(s.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') AS cursor_at,
    actor.name AS actor_name,actor.email AS actor_email,target.name AS target_name,target.email AS target_email
  FROM selected s LEFT JOIN profiles actor ON actor.id=s.actor_id LEFT JOIN profiles target ON target.id=s.target_user_id
  ORDER BY s.created_at DESC,s.id DESC LIMIT $${values.length}`,values)
  const rows = result.rows.slice(0,input.limit).map(row => ({ ...row, detail: safeAuditDetail(row.detail) }))
  const last = rows.at(-1)
  return { entries: rows, nextCursor: result.rows.length>input.limit && last
    ? Buffer.from(JSON.stringify({ time: last.cursor_at ?? new Date(last.created_at).toISOString(),id:last.id })).toString('base64url') : null,
    coverage: 'Recorded administration and AI configuration actions. Older administration writes are best-effort; this is not a complete or immutable activity history.' }
}
