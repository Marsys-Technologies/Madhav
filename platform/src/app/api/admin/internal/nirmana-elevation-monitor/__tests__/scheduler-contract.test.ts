// @vitest-environment node
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const schedulerMain = resolve(process.cwd(), '../infra/scheduler/main.tf')
const monitorBackend = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/backend.tf')
const monitorMain = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/main.tf')
const monitorApply = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/apply.sh')
const monitorReadme = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/README.md')

function resourceBlock(terraform: string, resourceStart: string): string {
  const start = terraform.indexOf(resourceStart)
  expect(start, `missing ${resourceStart}`).toBeGreaterThanOrEqual(0)
  const nextResource = terraform.indexOf('\nresource ', start + resourceStart.length)
  return terraform.slice(start, nextResource === -1 ? undefined : nextResource)
}

describe('Nirmana elevation monitor scheduler contract', () => {
  it('uses a dedicated least-privilege OIDC principal and bounded monitor job', () => {
    const schedulerTerraform = readFileSync(schedulerMain, 'utf8')
    const backend = readFileSync(monitorBackend, 'utf8')
    const terraform = readFileSync(monitorMain, 'utf8')
    const applyScript = readFileSync(monitorApply, 'utf8')
    const readme = readFileSync(monitorReadme, 'utf8')

    expect(schedulerTerraform).not.toContain('nirmana_elevation_monitor')
    expect(schedulerTerraform).not.toContain('amjis-nirmana-elevation-monitor')
    expect(backend).toContain('backend "gcs"')
    expect(applyScript).toContain('STATE_PREFIX="scheduler/nirmana-elevation-monitor"')
    const schedulerIdentity = resourceBlock(terraform, 'resource "google_service_account" "nirmana_elevation_monitor"')
    const invokerBinding = resourceBlock(terraform, 'resource "google_cloud_run_v2_service_iam_member" "nirmana_elevation_monitor_invokes_web"')
    const tokenMintBinding = resourceBlock(terraform, 'resource "google_service_account_iam_member" "cloud_scheduler_mints_nirmana_monitor_oidc"')
    const monitorJob = resourceBlock(terraform, 'resource "google_cloud_scheduler_job" "nirmana_elevation_monitor"')

    expect(schedulerIdentity).toContain('account_id   = "amjis-nirmana-monitor"')
    expect(schedulerIdentity).toContain('project      = var.gcp_project')

    expect(invokerBinding).toContain('project  = var.gcp_project')
    expect(invokerBinding).toContain('location = var.gcp_region')
    expect(invokerBinding).toContain('name     = "amjis-web"')
    expect(invokerBinding).toContain('role     = "roles/run.invoker"')
    expect(invokerBinding).toContain('member   = "serviceAccount:${google_service_account.nirmana_elevation_monitor.email}"')
    expect(tokenMintBinding).toContain('service_account_id = google_service_account.nirmana_elevation_monitor.name')
    expect(tokenMintBinding).toContain('role               = "roles/iam.serviceAccountOpenIdTokenCreator"')
    expect(tokenMintBinding).not.toContain('roles/iam.serviceAccountTokenCreator')
    expect(tokenMintBinding).toContain('service-${data.google_project.nirmana_elevation_monitor.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com')

    expect(monitorJob).toContain('name             = "amjis-nirmana-elevation-monitor"')
    expect(monitorJob).toContain('schedule         = "*/5 * * * *"')
    expect(monitorJob).toContain('/api/admin/internal/nirmana-elevation-monitor')
    expect(monitorJob).toContain('service_account_email = google_service_account.nirmana_elevation_monitor.email')
    expect(monitorJob).not.toContain('service_account_email = var.scheduler_invoker_sa')
    expect(monitorJob).toContain('audience              = var.amjis_web_url')
    expect(monitorJob).toContain('retry_count          = 2')
    expect(monitorJob).toContain('attempt_deadline = "120s"')
    expect(monitorJob).not.toContain('headers')
    expect(monitorJob).not.toContain('ignore_changes')

    expect(readme).toContain('amjis-nirmana-elevation-monitor')
    expect(readme).toContain('https://amjis-web-938361928218.asia-south1.run.app')
    expect(readme).toContain('amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com')
    expect(readme).toContain('iam.serviceAccounts.actAs')
  })
})
