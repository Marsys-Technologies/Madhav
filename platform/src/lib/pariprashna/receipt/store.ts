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
 * consumes exactly what was persisted, Zod-validated AND coherence-validated
 * on the way back out so a malformed/legacy row cannot masquerade as a valid
 * receipt.
 *
 * The read path runs the SAME two-step check the write path already runs
 * before persisting (`persistence_stage.ts`'s call to
 * `validateAcharyaReadingReceipt` ahead of `withAcharyaReadingReceipt`):
 * first `AcharyaReadingReceiptSchema.safeParse` (shape only), then
 * `validateAcharyaReadingReceipt` (the §N.8 structural-coherence check —
 * hash-matches-content, measured/unavailable field coherence, etc.). A row
 * that is shape-valid but incoherent (a tampered/hand-authored fake with a
 * `receipt_hash` that does not match its own content, or a `status:
 * 'measured'` field missing its data) is exactly what Zod's shape check
 * alone CANNOT catch — `safeParse` has no opinion on whether a hash matches
 * its own content. Both checks failing is reported the same way: `null`,
 * never a throw (this is a read path serving a UI, not the persistence
 * guard) — a malformed OR incoherent row is reported as absent, never
 * coerced or surfaced as if it were trustworthy.
 */

import { query } from '@/lib/db/client'
import { AcharyaReadingReceiptSchema, type AcharyaReadingReceipt } from './schema'
import { validateAcharyaReadingReceipt } from './validate'

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
 * or the turn predates this lane), when the stored value fails schema
 * validation (a legacy/malformed row is reported as absent, never coerced),
 * or when it fails the §N.8 coherence check (a shape-valid but
 * hash-mismatched/internally-incoherent row — see module docblock).
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
  if (!parsed.success) return null
  return validateAcharyaReadingReceipt(parsed.data).ok ? parsed.data : null
}

/**
 * Read a SPECIFIC message's receipt by message id — the audit-drawer's
 * per-turn lookup. Same two-step shape + coherence check as
 * `getLastTurnReceipt`; see module docblock.
 */
export async function getTurnReceiptByMessageId(messageId: string): Promise<AcharyaReadingReceipt | null> {
  const { rows } = await query<{ metadata_json: unknown }>(
    `SELECT metadata_json FROM conversation_messages WHERE id = $1 AND role = 'assistant' LIMIT 1`,
    [messageId],
  )
  const metadata = rows[0]?.metadata_json as Record<string, unknown> | null | undefined
  const candidate = metadata?.[RECEIPT_METADATA_KEY]
  const parsed = AcharyaReadingReceiptSchema.safeParse(candidate)
  if (!parsed.success) return null
  return validateAcharyaReadingReceipt(parsed.data).ok ? parsed.data : null
}
