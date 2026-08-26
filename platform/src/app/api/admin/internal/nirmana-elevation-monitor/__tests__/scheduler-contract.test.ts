// @vitest-environment node
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const schedulerMain = resolve(process.cwd(), '../infra/scheduler/main.tf')
const schedulerReadme = resolve(process.cwd(), '../infra/scheduler/README.md')

function resourceBlock(terraform: string, resourceStart: string): string {
  const start = terraform.indexOf(resourceStart)
  expect(start, `missing ${resourceStart}`).toBeGreaterThanOrEqual(0)
  const nextResource = terraform.indexOf('\nresource ', start + resourceStart.length)
  return terraform.slice(start, nextResource === -1 ? undefined : nextResource)
}

describe('Nirmana elevation monitor scheduler contract', () => {
  it('uses a dedicated least-privilege OIDC principal and bounded monitor job', () => {
    const terraform = readFileSync(schedulerMain, 'utf8')
    const readme = readFileSync(schedulerReadme, 'utf8')
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
    expect(tokenMintBinding).toContain('service-${data.google_project.scheduler.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com')

    expect(monitorJob).toContain('name             = "amjis-nirmana-elevation-monitor"')
    expect(monitorJob).toContain('schedule         = "*/5 * * * *"')
    expect(monitorJob).toContain('/api/admin/internal/nirmana-elevation-monitor')
    expect(monitorJob).toContain('service_account_email = google_service_account.nirmana_elevation_monitor.email')
    expect(monitorJob).not.toContain('service_account_email = var.scheduler_invoker_sa')
    expect(monitorJob).toContain('audience              = var.amjis_web_url')
    expect(monitorJob).toContain('retry_count          = 2')
    expect(monitorJob).toContain('attempt_deadline = "120s"')
    expect(monitorJob).toContain('ignore_changes = [http_target[0].headers]')

    expect(readme).toContain('amjis-nirmana-elevation-monitor')
    expect(readme).toContain('--project=madhav-astrology')
    expect(readme).toContain('--location=asia-south1')
    expect(readme).toContain('X-Marsys-Cron-Secret')
    expect(readme).toContain('outside Terraform')
    expect(readme).toContain('gcloud scheduler jobs describe')
  })
})
