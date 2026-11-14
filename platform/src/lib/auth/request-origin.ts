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

/** Account setup uses the configured first-party URL behind a gateway. */
export function accountSetupContinueUrl(request: Request): string | null {
  try {
    const app = new URL(process.env.APP_URL ?? request.url)
    if ((app.protocol !== 'https:' && app.protocol !== 'http:') ||
        app.username || app.password ||
        app.hostname === '0.0.0.0' || app.hostname === '[::]') return null
    return new URL('/setup-account', app.origin).href
  } catch {
    return null
  }
}
