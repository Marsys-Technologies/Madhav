// @vitest-environment node
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const schedulerMain = resolve(process.cwd(), '../infra/scheduler/main.tf')

describe('Nirmana elevation monitor scheduler contract', () => {
  it('schedules the authenticated monitor against production every five minutes', () => {
    const terraform = readFileSync(schedulerMain, 'utf8')
    const resourceStart = 'resource "google_cloud_scheduler_job" "nirmana_elevation_monitor"'

    expect(terraform).toContain(resourceStart)
    const resource = terraform.slice(terraform.indexOf(resourceStart))
    expect(resource).toContain('name             = "amjis-nirmana-elevation-monitor"')
    expect(resource).toContain('schedule         = "*/5 * * * *"')
    expect(resource).toContain('/api/admin/internal/nirmana-elevation-monitor')
    expect(resource).toContain('service_account_email = var.scheduler_invoker_sa')
    expect(resource).toContain('audience              = var.amjis_web_url')
    expect(resource).toContain('x-marsys-cron-secret')
    expect(resource).toContain('retry_count          = 2')
    expect(resource).toContain('attempt_deadline = "120s"')
  })
})
