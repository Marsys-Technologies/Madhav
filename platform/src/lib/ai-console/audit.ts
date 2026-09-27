import 'server-only'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { CliIdSchema } from './types'

const AuditSchema = z.object({
  event: z.enum(['connection_created', 'connection_updated', 'connection_renamed',
    'connection_credential_replaced', 'connection_validated', 'connection_deleted',
    'configuration_created', 'configuration_updated', 'configuration_duplicated',
    'configuration_deleted', 'default_selected', 'conversation_selected']),
  connectionId: z.string().uuid().optional(),
  configurationId: z.string().uuid().optional(),
  cliId: CliIdSchema.optional(),
  configurationVersion: z.number().int().positive().optional(),
}).strict()
export type AiAuditEvent = z.infer<typeof AuditSchema>

/** Closed identifiers only; audit failure rolls back the owning mutation. */
export async function writeAiAudit(client: Pick<PoolClient, 'query'>, userId: string, input: unknown): Promise<void> {
  const event = AuditSchema.parse(input)
  await client.query(`INSERT INTO ai_configuration_audit_log
    (user_id,actor_user_id,event,connection_id,configuration_id,cli_id,configuration_version)
    VALUES($1,$1,$2,$3,$4,$5,$6)`,
  [userId, event.event, event.connectionId ?? null, event.configurationId ?? null,
    event.cliId ?? null, event.configurationVersion ?? null])
}
