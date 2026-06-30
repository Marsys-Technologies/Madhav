/**
 * Google Cloud Error Reporting initializer.
 * Automatically captures unhandled errors in production and reports to GCP.
 * No-ops in development/test.
 */

let _initialized = false

export function initErrorReporting(): void {
  if (_initialized) return
  if (process.env.NODE_ENV !== 'production') return
  if (!process.env.GOOGLE_CLOUD_PROJECT) return

  _initialized = true

  // Catch unhandled promise rejections
  process.on('unhandledRejection', (reason) => {
    console.error('[error-reporting] Unhandled rejection:', reason)
    // The @google-cloud/error-reporting auto-hooks into this event when initialized
  })

  try {
    // Dynamic import to avoid build-time errors if package not installed
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { ErrorReporting } = require('@google-cloud/error-reporting')
    new ErrorReporting({
      projectId: process.env.GOOGLE_CLOUD_PROJECT,
      reportMode: 'production',
    })
    console.log('[error-reporting] Cloud Error Reporting initialized')
  } catch (err) {
    console.warn('[error-reporting] Could not initialize Cloud Error Reporting:', err)
  }
}
