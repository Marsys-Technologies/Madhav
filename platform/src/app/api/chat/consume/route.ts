/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * Returns 308 Permanent Redirect to /api/chat/consult for one release so any
 * in-flight client still calling the old path doesn't break. Remove after
 * one release cycle once telemetry confirms no traffic on /api/chat/consume.
 */
const TARGET = '/api/chat/consult'

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
