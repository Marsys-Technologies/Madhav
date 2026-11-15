/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * POST: 308 Permanent Redirect to /api/chat/consult/continue.
 * GET: explicitly unavailable; continuation requires POST.
 */
const TARGET = '/api/chat/consult/continue'

function redirect(request: Request): Response {
  const url = new URL(request.url)
  url.pathname = TARGET
  return new Response(null, {
    status: 308,
    headers: { Location: url.toString() },
  })
}

export async function GET(_request: Request) {
  return Response.json(
    {
      error: 'GET continuation is unavailable. Use POST /api/chat/consult/continue.',
      code: 'ENDPOINT_GONE',
    },
    { status: 410 },
  )
}

export async function POST(request: Request) {
  return redirect(request)
}
