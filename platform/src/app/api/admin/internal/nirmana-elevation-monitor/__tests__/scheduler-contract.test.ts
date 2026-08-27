// @vitest-environment node
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'

const schedulerMain = resolve(process.cwd(), '../infra/scheduler/main.tf')
const monitorBackend = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/backend.tf')
const monitorMain = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/main.tf')
const monitorApply = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/apply.sh')
const monitorLock = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/.terraform.lock.hcl')
const monitorReadme = resolve(process.cwd(), '../infra/nirmana_elevation_monitor/README.md')
const monitorRunbook = resolve(process.cwd(), '../docs/runbooks/ntap-tracker-monitor.md')
const iacWorkflow = resolve(process.cwd(), '../.github/workflows/iac-apply.yml')
const monitorRoute = resolve(process.cwd(), 'src/app/api/admin/internal/nirmana-elevation-monitor/route.ts')

const productionAudience = 'https://amjis-web-938361928218.asia-south1.run.app'
const schedulerPrincipal = 'amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'

function resourceBlock(terraform: string, resourceStart: string): string {
  const start = terraform.indexOf(resourceStart)
  expect(start, `missing ${resourceStart}`).toBeGreaterThanOrEqual(0)
  const nextResource = terraform.indexOf('\nresource ', start + resourceStart.length)
  return terraform.slice(start, nextResource === -1 ? undefined : nextResource)
}

function invokeMonitorApply(environment: Record<string, string | undefined>) {
  const tempDirectory = mkdtempSync(join(tmpdir(), 'nirmana-monitor-apply-'))
  const planFile = join(tempDirectory, 'monitor.tfplan')
  writeFileSync(planFile, 'not-a-real-terraform-plan')
  try {
    return spawnSync('bash', [monitorApply, 'apply', planFile], {
      encoding: 'utf8',
      env: { ...process.env, ...environment },
    })
  } finally {
    rmSync(tempDirectory, { recursive: true, force: true })
  }
}

describe('Nirmana elevation monitor scheduler contract', () => {
  it('uses a dedicated least-privilege OIDC principal and bounded monitor job', () => {
    const schedulerTerraform = readFileSync(schedulerMain, 'utf8')
    const backend = readFileSync(monitorBackend, 'utf8')
    const terraform = readFileSync(monitorMain, 'utf8')
    const applyScript = readFileSync(monitorApply, 'utf8')
    const lockfile = readFileSync(monitorLock, 'utf8')
    const readme = readFileSync(monitorReadme, 'utf8')
    const runbook = readFileSync(monitorRunbook, 'utf8')
    const workflow = readFileSync(iacWorkflow, 'utf8')
    const route = readFileSync(monitorRoute, 'utf8')

    expect(schedulerTerraform).not.toContain('nirmana_elevation_monitor')
    expect(schedulerTerraform).not.toContain('amjis-nirmana-elevation-monitor')
    expect(backend).toContain('backend "gcs"')
    expect(applyScript).toContain('STATE_PREFIX="scheduler/nirmana-elevation-monitor"')
    expect(applyScript).toContain('terraform plan -out="$PLAN_FILE"')
    expect(applyScript).toContain('terraform apply "$PLAN_FILE"')
    expect(applyScript).not.toContain('terraform apply -auto-approve')
    expect(applyScript).not.toContain('destroy)')
    expect(applyScript).toContain('IAC_APPLY_ENVIRONMENT:-')
    expect(applyScript).toContain('GOOGLE_CLOUD_RELEASE_APPROVAL:-')
    expect(applyScript).toContain('gcloud auth application-default print-access-token')
    expect(applyScript).toContain('GOOGLE_APPLICATION_CREDENTIALS:-')
    expect(applyScript).not.toContain('GITHUB_REF:-')
    expect(applyScript).toContain('terraform init -lockfile=readonly')
    expect(lockfile).toContain('provider "registry.terraform.io/hashicorp/google"')
    expect(lockfile).toContain('version     = "8.0.0"')
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
    expect(terraform).toContain('locals {')
    expect(terraform).toContain(`monitor_oidc_audience = "${productionAudience}"`)
    expect(terraform).not.toContain('variable "amjis_web_url"')
    expect(terraform).toContain('condition     = var.gcp_project == "madhav-astrology"')
    expect(terraform).toContain('condition     = var.gcp_region == "asia-south1"')
    expect(monitorJob).toContain('audience              = local.monitor_oidc_audience')
    expect(monitorJob).toContain('retry_count          = 2')
    expect(monitorJob).toContain('attempt_deadline = "120s"')
    expect(monitorJob).not.toContain('headers')
    expect(monitorJob).not.toContain('ignore_changes')

    expect(readme).toContain('amjis-nirmana-elevation-monitor')
    expect(readme).toContain(productionAudience)
    expect(readme).toContain(schedulerPrincipal)
    expect(readme).toContain('iam.serviceAccounts.actAs')
    const monitorJobPermissionRow = readme.split('\n').find((line) => line.includes('| This monitor job only'))
    expect(monitorJobPermissionRow).toContain('cloudscheduler.jobs.enable')
    expect(monitorJobPermissionRow).not.toContain('cloudscheduler.jobs.update')
    expect(readme).toContain('Application Default Credentials')
    expect(readme).toContain('Cloud Audit Logs')
    expect(workflow).not.toContain('nirmana_elevation_monitor')
    expect(workflow).toContain('GitHub Actions does not apply Terraform')

    expect(route).toContain(`const SCHEDULER_OIDC_AUDIENCE = '${productionAudience}'`)
    expect(route).toContain(`const SCHEDULER_SERVICE_ACCOUNT = '${schedulerPrincipal}'`)

    expect(runbook).toContain('OIDC')
    expect(runbook).toContain(productionAudience)
    expect(runbook).toContain(schedulerPrincipal)
    expect(runbook).not.toContain('MARSYS_CRON_SECRET')
    expect(runbook).not.toContain('X-Marsys-Cron-Secret')
  })

  it('rejects an unapproved GCP-native apply before Terraform can initialize', () => {
    const applyScript = readFileSync(monitorApply, 'utf8')
    if (!applyScript.includes('GOOGLE_CLOUD_RELEASE_APPROVAL:-')) {
      // Keep the RED run offline: a wrapper without the native approval guard
      // would initialize the real backend when presented with a local saved-plan
      // placeholder.
      expect(applyScript).toContain('GOOGLE_CLOUD_RELEASE_APPROVAL:-')
      return
    }

    for (const environment of [
      {
        IAC_APPLY_ENVIRONMENT: 'staging',
        GOOGLE_CLOUD_RELEASE_APPROVAL: 'CHG-1234',
      },
      {
        IAC_APPLY_ENVIRONMENT: 'production',
      },
      {
        IAC_APPLY_ENVIRONMENT: 'production',
        GOOGLE_CLOUD_RELEASE_APPROVAL: 'short',
      },
    ]) {
      const result = invokeMonitorApply(environment)
      expect(result.status).toBe(2)
      expect(result.stderr).toContain('GCP-native reviewed release')
    }
  })
})
