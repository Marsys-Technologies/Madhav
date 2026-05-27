/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * 308 Permanent Redirect to /api/chat/consult/continue.
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

export async function GET(request: Request) {
  return redirect(request)
}

export async function POST(request: Request) {
  return redirect(request)
}
