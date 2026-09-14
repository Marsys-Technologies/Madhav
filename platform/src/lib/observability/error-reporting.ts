/**
 * Google Cloud Error Reporting initializer.
 * Automatically captures unhandled errors in production and reports to GCP.
 * No-ops in development/test.
 */

import { createRequire } from 'node:module'

const loadOptionalModule = createRequire(import.meta.url)

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
    // Synchronous optional load preserves fire-and-forget initialization without
    // creating a hard build-time dependency in deployments that omit this package.
    const { ErrorReporting } = loadOptionalModule('@google-cloud/error-reporting') as {
      ErrorReporting: new (options: { projectId: string; reportMode: string }) => object
    }
    new ErrorReporting({
      projectId: process.env.GOOGLE_CLOUD_PROJECT,
      reportMode: 'production',
    })
    console.log('[error-reporting] Cloud Error Reporting initialized')
  } catch (err) {
    console.warn('[error-reporting] Could not initialize Cloud Error Reporting:', err)
  }
}
