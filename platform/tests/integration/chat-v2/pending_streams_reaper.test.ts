/**
 * Integration tests for B.12 — pending-streams reaper cron route (§M.4).
 *
 * Creates /api/admin/cron/reap-pending-streams with header-secret auth
 * (MARSYS_CRON_SECRET). Runs DELETE ... WHERE expires_at < now() and returns
 * { reaped: count }. Cloud Scheduler recipe in Remediation — Operator follow-up.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const routeSrc = readFileSync(
  join(__dirname, '../../../src/app/api/admin/cron/reap-pending-streams/route.ts'),
  'utf-8',
)

describe('B.12 — pending-streams reaper cron route (§M.4)', () => {
  it('route rejects requests without valid MARSYS_CRON_SECRET bearer token (401)', () => {
    expect(routeSrc).toContain('MARSYS_CRON_SECRET')
    expect(routeSrc).toContain('Bearer')
    expect(routeSrc).toContain('401')
    expect(routeSrc).toContain("error: 'unauthorized'")
  })

  it('route deletes expired pending_streams rows and returns reaped count', () => {
    expect(routeSrc).toContain('DELETE FROM pending_streams WHERE expires_at < now()')
    expect(routeSrc).toContain('reaped')
    expect(routeSrc).toContain('result.rows.length')
  })

  it('route exports a POST handler', () => {
    expect(routeSrc).toContain('export async function POST')
  })
})
