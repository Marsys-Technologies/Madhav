/** Match the browser-facing origin when a trusted gateway forwards to an internal URL. */
export function isAllowedRequestOrigin(request: Request): boolean {
  const origin = request.headers.get('origin')
  if (!origin || origin === new URL(request.url).origin) return true

  const appUrl = process.env.APP_URL
  if (!appUrl) return false
  try {
    const configured = new URL(appUrl)
    return (configured.protocol === 'https:' || configured.protocol === 'http:') &&
      configured.origin === origin
  } catch {
    return false
  }
}
