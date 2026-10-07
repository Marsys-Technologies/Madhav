import "server-only";
import { query, withTransaction } from "@/lib/db/client";
import { resolveChartPageAccess } from "@/lib/auth/chart-page-guard";
import { AcharyaReadingReceiptSchema } from "@/lib/pariprashna/receipt/schema";
import { validateAcharyaReadingReceipt } from "@/lib/pariprashna/receipt/validate";
import { getConversation } from "@/lib/conversations";

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
                    AND m.role='assistant')
     ORDER BY COALESCE(c.updated_at,c.created_at) DESC, c.id LIMIT 100`,
    [chartId, userId],
  );
  return rows;
}

export async function consultationMessages(id: string) {
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
      FROM conversation_messages m WHERE m.conversation_id=$1
      ORDER BY m.created_at, CASE m.role WHEN 'user' THEN 0 ELSE 1 END, m.id`,
    [id],
  );
  return rows.map((row) => {
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
        AND role='assistant' RETURNING id`,
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
        AND m.role='assistant') RETURNING c.id`,
    [id, userId, tagged],
  );
  return rows.length === 1;
}
