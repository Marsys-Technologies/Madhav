export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { initErrorReporting } = await import('./lib/observability/error-reporting')
    initErrorReporting()
  }
}
