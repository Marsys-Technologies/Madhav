import "server-only";
import { query, withTransaction } from "@/lib/db/client";
import { resolveChartPageAccess } from "@/lib/auth/chart-page-guard";
import { AcharyaReadingReceiptSchema } from "@/lib/pariprashna/receipt/schema";
import { validateAcharyaReadingReceipt } from "@/lib/pariprashna/receipt/validate";
import { getConversation } from "@/lib/conversations";
import { isCanonicalSchemaVersionSupported, parsePartContent } from "@/lib/pariprashna/store/schema";

export const uuidLike =
  /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;

/** Chart entitlement is rechecked on every read and mutation, including restored history. */
export async function consultationAccess(chartId: string) {
  if (!uuidLike.test(chartId)) return null;
  const access = await resolveChartPageAccess(chartId);
  return access && access.permission !== "deny" ? access : null;
}

export async function ownedConsultation(id: string, userId: string) {
  if (!uuidLike.test(id)) return null;
  // A super-admin's chart access does not grant ownership of another user's tags.
  const conversation = await getConversation({
    id,
    userId,
    isSuperAdmin: false,
  });
  if (!conversation || conversation.module !== "consume") return null;
  const access = await consultationAccess(conversation.chart_id);
  return access?.user.uid === userId ? conversation : null;
}

export async function consultationHistory(chartId: string, userId: string) {
  const { rows } = await query(
    `
    SELECT c.id, c.chart_id, c.title, c.created_at, c.updated_at, c.archived_at,
           c.archive_reason, c.consultation_tagged AS tagged,
           (SELECT LEFT(COALESCE(
                (SELECT string_agg(mp.body->>'text', E'\n' ORDER BY mp.seq)
                   FROM message_parts mp WHERE mp.message_id=m.id AND mp.kind='text'),
                string_agg(p->>'text', E'\n')),120)
              FROM conversation_messages m LEFT JOIN LATERAL jsonb_array_elements(m.parts_json) p
                ON p->>'type'='text'
             WHERE m.id = (SELECT id FROM conversation_messages WHERE conversation_id=c.id
                           AND role='user' ORDER BY created_at, id LIMIT 1)
               GROUP BY m.id) AS first_message_snippet,
           COALESCE((SELECT jsonb_agg(jsonb_build_object('id',m.id,'text',
                    LEFT(COALESCE(
                      (SELECT string_agg(mp.body->>'text', E'\n' ORDER BY mp.seq)
                         FROM message_parts mp WHERE mp.message_id=m.id AND mp.kind='text'),
                      (SELECT string_agg(p->>'text', E'\n') FROM jsonb_array_elements(m.parts_json) p
                          WHERE p->>'type'='text')),160)) ORDER BY m.created_at, m.id)
                      FROM conversation_messages m WHERE m.conversation_id=c.id
                      AND m.role='assistant' AND m.consultation_tagged), '[]'::jsonb) AS tagged_answers
      FROM conversations c
     WHERE c.chart_id=$1 AND c.user_id=$2 AND c.module='consume'
       AND (c.archived_at IS NULL OR c.archive_reason='chart_details_changed')
       AND EXISTS (SELECT 1 FROM conversation_messages m WHERE m.conversation_id=c.id
                    AND m.role='assistant' AND m.metadata_json ? 'acharya_reading_receipt')
     ORDER BY COALESCE(c.updated_at,c.created_at) DESC, c.id LIMIT 100`,
    [chartId, userId],
  );
  return rows;
}

export class StoredTurnIntegrityError extends Error {
  constructor() { super("Stored turn identity or reader data is inconsistent."); this.name = "StoredTurnIntegrityError"; }
}

export interface StoredTurnIdentity {
  turnId: string;
  conversationId: string;
  chartId: string;
  snapshotId: string;
}

interface ConsultationMessageRow {
  id: string;
  role: string;
  created_at: string;
  parts_json: unknown;
  metadata_json: Record<string, unknown> | null;
  schema_version: number | null;
  tagged: boolean;
  canonical_parts: unknown;
}

/** The existing stored-reader shape, narrowed for an exact recovered assistant. */
export interface SafeStoredAssistantMessage {
  id: string;
  role: 'assistant';
  created_at: string;
  tagged: boolean;
  schema_version: number | null;
  parts_json: Array<{ type: 'text'; text: string }>;
  metadata_json: { acharya_reading_receipt: import('@/lib/pariprashna/receipt/schema').AcharyaReadingReceipt };
  canonical_parts: Array<{ kind: 'text' | 'citation' | 'prediction_candidate'; body: unknown }>;
}

function sameUuid(value: unknown, expected: string): boolean {
  return typeof value === 'string' && uuidLike.test(value) && value.toLowerCase() === expected.toLowerCase();
}

/** Check RAW identities before reducing any metadata or parts. Never spread a raw row. */
export function safeStoredMessage(row: ConsultationMessageRow, expected: StoredTurnIdentity): SafeStoredAssistantMessage {
  const parsed = AcharyaReadingReceiptSchema.safeParse(row.metadata_json?.acharya_reading_receipt);
  const custom = row.metadata_json?.custom;
  if (row.role !== 'assistant' || !parsed.success || !validateAcharyaReadingReceipt(parsed.data).ok
    || parsed.data.turn_id !== expected.turnId
    || !sameUuid(parsed.data.conversation_id, expected.conversationId)
    || !sameUuid(parsed.data.chart_id, expected.chartId)
    || !custom || typeof custom !== 'object' || Array.isArray(custom)) throw new StoredTurnIntegrityError();
  const identity = custom as Record<string, unknown>;
  if (identity.queryId !== expected.turnId
    || !sameUuid(identity.conversationId, expected.conversationId)
    || !sameUuid(identity.ai_routing_snapshot_id, expected.snapshotId)
    || (row.schema_version != null && !isCanonicalSchemaVersionSupported(row.schema_version))) throw new StoredTurnIntegrityError();

  const canonical: SafeStoredAssistantMessage['canonical_parts'] = [];
  if (!Array.isArray(row.canonical_parts)) throw new StoredTurnIntegrityError();
  try {
    for (const part of row.canonical_parts) {
      if (!part || typeof part !== 'object') throw new StoredTurnIntegrityError();
      const { kind, body } = part as { kind?: unknown; body?: unknown };
      if (kind !== 'text' && kind !== 'citation' && kind !== 'prediction_candidate') continue;
      const validated = parsePartContent(kind, body);
      canonical.push({ kind, body: validated.body });
    }
  } catch { throw new StoredTurnIntegrityError(); }
  const legacy: SafeStoredAssistantMessage['parts_json'] = [];
  // Canonical prose wins; do not ship a second, possibly stale legacy answer.
  if (!canonical.some(p => p.kind === 'text')) {
    for (const part of Array.isArray(row.parts_json) ? row.parts_json : []) {
      if (part && typeof part === 'object' && part.type === 'text' && typeof part.text === 'string') {
        legacy.push({ type: 'text', text: part.text });
      }
    }
  }
  if (!canonical.some(p => p.kind === 'text' && (p.body as { text: string }).text.trim())
    && !legacy.some(p => p.text.trim())) throw new StoredTurnIntegrityError();
  return {
    id: row.id, role: 'assistant', created_at: row.created_at, tagged: row.tagged,
    schema_version: row.schema_version, parts_json: legacy, canonical_parts: canonical,
    metadata_json: { acharya_reading_receipt: parsed.data },
  };
}

export function consultationMessages(id: string, exact: { messageId: string; recoveryIdentity: StoredTurnIdentity }): Promise<SafeStoredAssistantMessage[]>;
export function consultationMessages(id: string, exact?: { messageId: string }): Promise<ConsultationMessageRow[]>;
export async function consultationMessages(id: string, exact?: { messageId: string; recoveryIdentity?: StoredTurnIdentity }) {
  const { rows } = await query<{
    id: string;
    role: string;
    created_at: string;
    parts_json: unknown;
    metadata_json: Record<string, unknown> | null;
    schema_version: number | null;
    tagged: boolean;
    canonical_parts: unknown;
  }>(
    `
    SELECT m.id, m.role, m.created_at, m.parts_json, m.metadata_json,
           m.schema_version, m.consultation_tagged AS tagged,
           COALESCE((SELECT jsonb_agg(jsonb_build_object('kind',p.kind,'body',p.body)
                                      ORDER BY p.seq)
                       FROM message_parts p WHERE p.message_id=m.id AND p.kind IN ('text','citation','prediction_candidate')), '[]'::jsonb) AS canonical_parts
      FROM conversation_messages m WHERE m.conversation_id=$1${exact ? ' AND m.id=$2' : ''}
      ORDER BY m.created_at, CASE m.role WHEN 'user' THEN 0 ELSE 1 END, m.id`,
    exact ? [id, exact.messageId] : [id],
  );
  return rows.map((row) => {
    if (exact?.recoveryIdentity) {
      if (row.id !== exact.messageId || !sameUuid(id, exact.recoveryIdentity.conversationId)) throw new StoredTurnIntegrityError();
      return safeStoredMessage(row, exact.recoveryIdentity);
    }
    const parsed = AcharyaReadingReceiptSchema.safeParse(
      row.metadata_json?.acharya_reading_receipt,
    );
    return {
      ...row,
      metadata_json:
        parsed.success && validateAcharyaReadingReceipt(parsed.data).ok
          ? { acharya_reading_receipt: parsed.data }
          : {},
    };
  });
}

/** Exact canonical assistant lookup; never replace it with the latest or a whole history read. */
export async function recoverConsultationTurn(expected: StoredTurnIdentity): Promise<SafeStoredAssistantMessage | null> {
  const { rows } = await query<{ id: string }>(
    `SELECT m.id FROM conversation_messages m
     WHERE m.conversation_id=$1 AND m.role='assistant'
       AND m.metadata_json #>> '{acharya_reading_receipt,turn_id}'=$2
     LIMIT 2`, [expected.conversationId, expected.turnId],
  );
  if (!rows.length) return null;
  if (rows.length !== 1 || !uuidLike.test(rows[0].id)) throw new StoredTurnIntegrityError();
  const messages = await consultationMessages(expected.conversationId, { messageId: rows[0].id, recoveryIdentity: expected });
  if (messages.length !== 1) throw new StoredTurnIntegrityError();
  return messages[0];
}

export async function setConsultationTag(
  id: string,
  userId: string,
  tagged: boolean,
  messageId?: string,
) {
  if (messageId)
    return withTransaction(async (client) => {
      // Lock the PARENT first. A message UPDATE ... FROM conversations alone does
      // not lock the parent, and its snapshot could outlive a racing correction.
      const parent = await client.query(
        `SELECT id FROM conversations
      WHERE id=$1 AND user_id=$2 AND module='consume' AND archived_at IS NULL
        AND archive_reason IS DISTINCT FROM 'chart_details_changed' FOR UPDATE`,
        [id, userId],
      );
      if (parent.rows.length !== 1) return false;
      const { rows } = await client.query(
        `UPDATE conversation_messages
      SET consultation_tagged=$3 WHERE conversation_id=$1 AND id=$2
        AND role='assistant' AND metadata_json ? 'acharya_reading_receipt' RETURNING id`,
        [id, messageId, tagged],
      );
      return rows.length === 1;
    });
  // This targets the parent itself; PostgreSQL rechecks the predicate after a
  // concurrent correction's row lock is released.
  const { rows } = await query(
    `UPDATE conversations c SET consultation_tagged=$3
    WHERE c.id=$1 AND c.user_id=$2 AND c.module='consume' AND c.archived_at IS NULL
      AND c.archive_reason IS DISTINCT FROM 'chart_details_changed'
      AND EXISTS (SELECT 1 FROM conversation_messages m WHERE m.conversation_id=c.id
        AND m.role='assistant' AND m.metadata_json ? 'acharya_reading_receipt') RETURNING c.id`,
    [id, userId, tagged],
  );
  return rows.length === 1;
}
