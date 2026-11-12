import 'server-only'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { SHARE_DEFAULT_TTL_DAYS } from '@/lib/share/constants'
import { listActiveConversationShares } from '@/lib/share/list_active_conversation_shares'

interface ConversationActor {
  conversationId: string
  /** Supplied only by a verified server session, never from the request body. */
  verifiedUserId: string
}

type ActiveShares = Awaited<ReturnType<typeof listActiveConversationShares>>
export interface ConversationShares {
  share: ActiveShares[number] | null
  shares: ActiveShares
}

// A share is ACTIVE when it is not revoked and not expired. Rows with
// expires_at NULL (pre-TTL shares) stay active until revoked.
const ACTIVE_SHARE_PREDICATE = 'revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())'
const SHARE_COLUMNS = 'slug, created_at, expires_at, revoked_at, hide_reasoning, hide_methodology'

type ShareRow = {
  slug: string
  created_at: string
  expires_at: string | null
  revoked_at: string | null
  hide_reasoning: boolean
  hide_methodology: boolean
}

function isActiveShare(row: ShareRow, nowMs: number): boolean {
  if (row.revoked_at) return false
  if (row.expires_at && new Date(row.expires_at).getTime() <= nowMs) return false
  return true
}

// URL-safe 10-char slug (~58 bits of entropy). A convenience link, not the only
// credential: the share page also requires a verified, active session.
function generateSlug(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(10))
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let out = ''
  for (const b of bytes) out += chars[b % chars.length]
  return out
}

async function resolveAccess(userId: string) {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId]
  )
  return result.rows[0]?.role === 'super_admin'
}

async function conversationExistsForActor(conversationId: string, verifiedUserId: string): Promise<boolean> {
  const isSuperAdmin = await resolveAccess(verifiedUserId)
  const conversation = await getConversation({ id: conversationId, userId: verifiedUserId, isSuperAdmin })
  return Boolean(conversation)
}

/** null means the conversation is missing or inaccessible to the verified actor. */
export async function listConversationSharesForActor({ conversationId, verifiedUserId }: ConversationActor): Promise<ConversationShares | null> {
  if (!await conversationExistsForActor(conversationId, verifiedUserId)) return null
  const rows = await listActiveConversationShares(conversationId)
  return { share: rows[0] ?? null, shares: rows }
}

export async function createConversationShareForActor({ conversationId, verifiedUserId, hideReasoning, hideMethodology }: ConversationActor & {
  hideReasoning: boolean
  hideMethodology: boolean
}): Promise<{ slug: string } | null> {
  if (!await conversationExistsForActor(conversationId, verifiedUserId)) return null
  // SS N-383: reuse an ACTIVE share of this conversation only when it has exactly
  // the requested hide options (effective values: booleans, false when the flag
  // is off). Different options mint a NEW share; the old link keeps its own
  // options and stays active. The SQL filter is authoritative; isActiveShare is a
  // defensive re-check so an expired or revoked row can never be handed back.
  const existing = await query<ShareRow>(
    `SELECT ${SHARE_COLUMNS} FROM conversation_shares WHERE conversation_id=$1 AND ${ACTIVE_SHARE_PREDICATE} ORDER BY created_at DESC`,
    [conversationId]
  )
  const nowMs = Date.now()
  const match = existing.rows.find(
    (row) =>
      isActiveShare(row, nowMs) &&
      row.hide_reasoning === hideReasoning &&
      row.hide_methodology === hideMethodology,
  )
  if (match) return { slug: match.slug }

  const slug = generateSlug()
  await query(
    "INSERT INTO conversation_shares (conversation_id, slug, created_by, hide_reasoning, hide_methodology, expires_at) VALUES ($1,$2,$3,$4,$5, now() + make_interval(days => $6::int)) RETURNING *",
    [conversationId, slug, verifiedUserId, hideReasoning, hideMethodology, SHARE_DEFAULT_TTL_DAYS]
  )
  return { slug }
}

export async function revokeConversationSharesForActor({ conversationId, verifiedUserId }: ConversationActor): Promise<{ ok: true } | null> {
  if (!await conversationExistsForActor(conversationId, verifiedUserId)) return null
  // Revoke every non-revoked row, including expired rows; this is not an active-list filter.
  await query(
    'UPDATE conversation_shares SET revoked_at=now() WHERE conversation_id=$1 AND revoked_at IS NULL',
    [conversationId]
  )
  return { ok: true }
}
