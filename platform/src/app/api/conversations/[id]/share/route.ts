import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'
import { getFlag } from '@/lib/config/index'
import { createConversationShareForActor, listConversationSharesForActor, revokeConversationSharesForActor } from '@/lib/conversations/shareLifecycle'
import { shareMutationLimiter } from '@/lib/share/share_rate_limit'

// Share create/revoke is limited per VERIFIED user (SS N-376 / PR-S4). Call only
// after getServerUser() succeeded; the key is the verified uid, never client input.
function rateLimitShareMutation(uid: string) {
  const verdict = shareMutationLimiter.check(`share:${uid}`)
  if (verdict.allowed) return null
  return res.rateLimited(
    'Too many share link changes. Please wait before creating or revoking more links.',
    verdict.retryAfterSeconds,
  )
}

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const result = await listConversationSharesForActor({ conversationId: id, verifiedUserId: user.uid })
    if (!result) return res.notFound('conversation')

    // SS N-383: a conversation can hold several active shares (one per distinct
    // hide-option pair). `share` keeps its old shape (the most recent active share)
    // so existing clients are unaffected; `shares` additively lists all of them.

    // SS N-379: tell the dialog whether hide options are OFFERED on a NEW share.
    // (The share PAGE applies a stored share's options regardless of this flag.)
    return Response.json({
      share: result.share,
      shares: result.shares,
      selective_share_enabled: getFlag('R10_SELECTIVE_SHARE'),
    })
  } catch {
    return res.dbError()
  }
}

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  const limited = rateLimitShareMutation(user.uid)
  if (limited) return limited

  // R10_SELECTIVE_SHARE only controls whether hide options are OFFERED on a NEW
  // share: flag off -> the body is not even read and both options are stored false.
  // Stored options of existing shares are always honoured by the page (SS N-379).
  let hideReasoning = false
  let hideMethodology = false
  if (getFlag('R10_SELECTIVE_SHARE')) {
    try {
      const body = await req.json() as { hide_reasoning?: boolean; hide_methodology?: boolean }
      hideReasoning = body.hide_reasoning === true
      hideMethodology = body.hide_methodology === true
    } catch {}
  }

  try {
    const result = await createConversationShareForActor({ conversationId: id, verifiedUserId: user.uid, hideReasoning, hideMethodology })
    if (!result) return res.notFound('conversation')
    return Response.json(result)
  } catch {
    return res.dbError()
  }
}

export async function DELETE(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  const limited = rateLimitShareMutation(user.uid)
  if (limited) return limited

  try {
    const result = await revokeConversationSharesForActor({ conversationId: id, verifiedUserId: user.uid })
    if (!result) return res.notFound('conversation')
    return Response.json(result)
  } catch {
    return res.dbError()
  }
}
