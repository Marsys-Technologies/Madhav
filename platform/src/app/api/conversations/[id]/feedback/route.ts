// message_feedback table dropped in WS-0. Endpoint returns empty/ok stubs.
// TODO(ws-2): restore once message-feedback is added to conversation_messages JSONB or
// a new dedicated table is created in the Brahma schema.
import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'

export async function GET(_req: Request, _ctx: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  return Response.json({ feedback: [] })
}

export async function POST(req: Request, _ctx: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  try {
    const body = await req.json() as { rating?: unknown }
    return Response.json({ ok: true, rating: body?.rating ?? null })
  } catch {
    return res.badRequest('invalid body')
  }
}
