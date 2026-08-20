import 'server-only'
/**
 * pariprashna/receipt/store.ts — persistence + audit-read for
 * `AcharyaReadingReceipt` (lane G3-A, PPR-01).
 *
 * Same convention as `provenance/stamp.ts`'s `withProvenanceStamp` /
 * `getLastTurnStamp`: the receipt rides as an ADDITIVE sub-object of
 * `conversation_messages.metadata_json` (the existing free-form jsonb
 * column) — no migration, no new table, no schema change. This is the ONLY
 * place the receipt is written, and `getLastTurnReceipt` is the ONLY read
 * path — the audit affordance (a UI surface reading via this function)
 * consumes exactly what was persisted, Zod-validated on the way back out so
 * a malformed/legacy row cannot masquerade as a valid receipt.
 */

import { query } from '@/lib/db/client'
import { AcharyaReadingReceiptSchema, type AcharyaReadingReceipt } from './schema'

const RECEIPT_METADATA_KEY = 'acharya_reading_receipt' as const

/**
 * Attach the receipt to a `metadata_json` object as an additive sub-object
 * (never replaces existing keys, e.g. `provenance_stamp` or `custom`).
 */
export function withAcharyaReadingReceipt(
  metadata: Record<string, unknown>,
  receipt: AcharyaReadingReceipt,
): Record<string, unknown> {
  return { ...metadata, [RECEIPT_METADATA_KEY]: receipt }
}

/**
 * Read the most recently PERSISTED assistant turn's receipt for a
 * conversation — the audit affordance's read path. Returns `null` when the
 * conversation has no prior receipt-bearing assistant turn (flag was off,
 * or the turn predates this lane) or when the stored value fails schema
 * validation (a legacy/malformed row is reported as absent, never coerced).
 */
export async function getLastTurnReceipt(conversationId: string): Promise<AcharyaReadingReceipt | null> {
  const { rows } = await query<{ metadata_json: unknown }>(
    `SELECT metadata_json
       FROM conversation_messages
      WHERE conversation_id = $1 AND role = 'assistant'
      ORDER BY created_at DESC
      LIMIT 1`,
    [conversationId],
  )
  const metadata = rows[0]?.metadata_json as Record<string, unknown> | null | undefined
  const candidate = metadata?.[RECEIPT_METADATA_KEY]
  const parsed = AcharyaReadingReceiptSchema.safeParse(candidate)
  return parsed.success ? parsed.data : null
}

/** Read a SPECIFIC message's receipt by message id — the audit-drawer's per-turn lookup. */
export async function getTurnReceiptByMessageId(messageId: string): Promise<AcharyaReadingReceipt | null> {
  const { rows } = await query<{ metadata_json: unknown }>(
    `SELECT metadata_json FROM conversation_messages WHERE id = $1 AND role = 'assistant' LIMIT 1`,
    [messageId],
  )
  const metadata = rows[0]?.metadata_json as Record<string, unknown> | null | undefined
  const candidate = metadata?.[RECEIPT_METADATA_KEY]
  const parsed = AcharyaReadingReceiptSchema.safeParse(candidate)
  return parsed.success ? parsed.data : null
}
