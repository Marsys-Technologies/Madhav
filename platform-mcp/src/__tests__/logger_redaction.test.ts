/**
 * logger_redaction.test.ts — CAN-FAIL proof for B-MCP-LOG-REDACT (DVA Ruling 64 /
 * SAMAPTI_DVARAPALA_LEDGER.md INC-4).
 *
 * Demonstrates, against the real `log`/`logError`/`redactCredentials` code path in
 * `platform-mcp/src/lib/logger.ts`:
 *
 *   BEFORE (this test's own "raw input" assertions): a synthetic request URL /
 *   message carrying `?api_key=test-fake-key-do-not-use` contains the literal
 *   credential — i.e. this is genuinely what an unredacted log line would contain
 *   if a caller passed it through `log()`/`logError()` (this is exactly the shape
 *   `httpRequest.requestUrl` takes on in Cloud Run's automatic request log, and
 *   exactly what `mcp_end_to_end_smoke.sh`'s old Probe 4 caused, every deploy, with
 *   the real `mcp-canary-key`).
 *
 *   AFTER (the `console.log`/`console.error` spy assertions): the same string,
 *   routed through this repo's `log()` / `logError()`, is written with the
 *   credential redacted — proving the fix is live on the actual write path, not
 *   just present as an unused helper.
 *
 * Only an obviously-fake placeholder credential is used ('test-fake-key-do-not-use')
 * — never a real Secret Manager value.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { log, logError, logWarn, redactCredentials } from '../lib/logger.js'

const FAKE_KEY = 'test-fake-key-do-not-use'
const SYNTHETIC_URL = `https://amjis-mcp-938361928218.asia-south1.run.app/mcp?api_key=${FAKE_KEY}`

describe('BEFORE: raw string genuinely contains the literal credential', () => {
  it('the synthetic request URL contains the fake key in plaintext', () => {
    // This is what an unredacted httpRequest.requestUrl / log message looks like —
    // establishing the input this fix must neutralize actually carries the secret.
    expect(SYNTHETIC_URL).toContain(FAKE_KEY)
    expect(SYNTHETIC_URL).toContain(`api_key=${FAKE_KEY}`)
  })
})

describe('AFTER: redactCredentials() strips the credential value', () => {
  it('redacts a bare api_key= query parameter', () => {
    const redacted = redactCredentials(SYNTHETIC_URL)
    expect(redacted).not.toContain(FAKE_KEY)
    expect(redacted).toContain('api_key=[REDACTED]')
  })

  it('redacts api_key= wherever it appears in a free-text message', () => {
    const msg = `Unexpected response for POST /mcp?api_key=${FAKE_KEY}&foo=bar: 500`
    const redacted = redactCredentials(msg)
    expect(redacted).not.toContain(FAKE_KEY)
    expect(redacted).toContain('api_key=[REDACTED]')
    expect(redacted).toContain('&foo=bar') // unrelated params survive
  })

  it('is a no-op on strings with no credential', () => {
    const msg = 'MCP request completed in 42ms'
    expect(redactCredentials(msg)).toBe(msg)
  })
})

describe('AFTER: log() / logError() / logWarn() never write the raw credential to stdout/stderr', () => {
  let logSpy: ReturnType<typeof vi.spyOn>
  let errorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined)
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('log() redacts a credential-bearing message before writing', () => {
    log({
      request_id: 'req-test-1',
      outcome: 'ok',
      message: `Forwarded ${SYNTHETIC_URL}`,
    })

    expect(logSpy).toHaveBeenCalledTimes(1)
    const written = logSpy.mock.calls[0]?.[0] as string
    expect(written).not.toContain(FAKE_KEY)
    expect(written).toContain('[REDACTED]')
  })

  it('logWarn() redacts a credential-bearing message before writing', () => {
    logWarn({
      request_id: 'req-test-2',
      message: `Retrying ${SYNTHETIC_URL}`,
    })

    const written = logSpy.mock.calls[0]?.[0] as string
    expect(written).not.toContain(FAKE_KEY)
    expect(written).toContain('[REDACTED]')
  })

  it('logError() redacts a credential-bearing error field before writing', () => {
    logError({
      request_id: 'req-test-3',
      outcome: 'error',
      message: 'Upstream fetch failed',
      error: `fetch ${SYNTHETIC_URL} -> ECONNRESET`,
    })

    expect(errorSpy).toHaveBeenCalledTimes(1)
    const written = errorSpy.mock.calls[0]?.[0] as string
    expect(written).not.toContain(FAKE_KEY)
    expect(written).toContain('[REDACTED]')
  })

  it('a message with no credential passes through unchanged (redaction is not lossy)', () => {
    log({ request_id: 'req-test-4', outcome: 'ok', message: 'Tool dispatch completed' })
    const written = logSpy.mock.calls[0]?.[0] as string
    expect(written).toContain('Tool dispatch completed')
  })
})
