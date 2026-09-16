import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { load } from 'js-yaml'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
const purnaPostflight = readFileSync(resolve(__dirname, '../../scripts/purna-inquiry-ownership-postflight.ts'), 'utf8')
const purnaStatus = readFileSync(resolve(__dirname, '../../scripts/purna-inquiry-ownership-status.ts'), 'utf8')
const jobs = (load(workflow) as { jobs: Record<string, {
  environment?: string
  steps: Array<{ name?: string; if?: string; env?: Record<string, string>; run?: string }>
}> }).jobs

describe('Nirmana ownership deployment attestation', () => {
  it('keeps the one-shot owner handoff privileged but reattests marked state on every routine deployment', () => {
    const bootstrap = jobs['privileged-bootstrap']
    const migrate = jobs.migrate
    const preflight = bootstrap.steps.find((step) => step.name === 'One-shot Nirmana evidence ownership preflight')
    const marker = bootstrap.steps.find((step) => step.name === 'Attest Nirmana ownership handoff as deployment-only migrator')
    const routineAttestation = migrate.steps.find((step) => step.name === 'Re-attest Nirmana evidence ownership state with routine credential')

    expect(bootstrap.environment).toBe('data-plane-production-cutover')
    expect(preflight?.if).toBe("steps.bootstrap-state.outputs.nirmana == 'unmarked'")
    expect(marker?.if).toContain("steps.bootstrap-state.outputs.nirmana == 'unmarked'")
    expect(marker?.if).toContain("steps.bootstrap-state.outputs.purna != 'marked'")
    expect(marker?.run).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(routineAttestation?.env).toEqual({ DATABASE_URL: '${{ secrets.PROD_DATABASE_URL }}' })
    expect(routineAttestation?.run).toContain('nirmana-evidence-ownership-status.ts')
    expect(JSON.stringify(migrate)).not.toContain('NIRMANA_MIGRATOR_DATABASE_URL')
  })

  it('serializes and health-checks the production, Pūrṇa admin, and restore-validation listeners', () => {
    const bootstrap = jobs['privileged-bootstrap']
    const prodProxy = bootstrap.steps.find((step) => step.name === 'Start Cloud SQL Auth Proxy')
    const adminProxy = bootstrap.steps.find((step) => step.name === 'Start one-shot Pūrṇa admin proxy')
    const release = bootstrap.steps.find((step) => step.name === 'Release one-shot Pūrṇa admin proxy port')
    const cutover = bootstrap.steps.find((step) => step.name === 'Execute protected cutover under backup, restore, lease, quiescence and independent approval')

    expect(prodProxy?.run).toContain('--port 5432')
    expect(prodProxy?.run).toContain('proxy_5432_pid=$!')
    expect(prodProxy?.run).toContain('kill -0 "$proxy_5432_pid"')
    expect(prodProxy?.run).not.toContain('--port 5433')
    expect(adminProxy?.run).toContain('--port 5433')
    expect(adminProxy?.run).toContain('proxy_5433_pid=$!')
    expect(adminProxy?.run).toContain('kill -0 "$proxy_5433_pid"')
    expect(release?.run).toContain('kill "$PURNA_PROXY_PID"')
    expect(release?.run).toContain('/dev/tcp/127.0.0.1/5433')
    expect(cutover?.run).toContain('--port 5433')
    expect(cutover?.run).toContain('kill -0 "$validation_proxy_pid"')
  })

  it('always validates PROD but requires the one-shot route only while ownership needs it', () => {
    const stateProdRoute = jobs['migration-state'].steps.find((step) => step.name === 'Validate production migration database route')
    const routineProdRoute = jobs.migrate.steps.find((step) => step.name === 'Validate production migration database route')
    const adminRoute = jobs['privileged-bootstrap'].steps.find((step) => step.name === 'Validate one-shot Pūrṇa admin database route')
    const postflight = jobs['privileged-bootstrap'].steps.find((step) => step.name === 'Close and attest Pūrṇa protected-owner handoff')

    for (const prodRoute of [stateProdRoute, routineProdRoute]) {
      expect(prodRoute?.env).toEqual({ PROD_DATABASE_URL: '${{ secrets.PROD_DATABASE_URL }}' })
      expect(prodRoute?.run).toContain('validate-migration-database-routes.ts --prod')
      expect(JSON.stringify(prodRoute)).not.toContain('PURNA_INQUIRY_ADMIN_DATABASE_URL')
    }
    expect(adminRoute?.if).toContain("steps.bootstrap-state.outputs.purna == 'armed'")
    expect(adminRoute?.if).toContain("steps.bootstrap-state.outputs.purna == 'interrupted'")
    expect(adminRoute?.if).toContain("steps.bootstrap-state.outputs.purna == 'cleanup_required'")
    expect(adminRoute?.env).toEqual({ PURNA_INQUIRY_ADMIN_DATABASE_URL: '${{ secrets.PURNA_INQUIRY_ADMIN_DATABASE_URL }}' })
    expect(adminRoute?.run).toContain('validate-migration-database-routes.ts --purna-admin')
    expect(postflight?.if).toContain("steps.purna-admin-route.outcome == 'success'")
    expect(JSON.stringify(jobs.migrate)).not.toContain('PURNA_INQUIRY_ADMIN_DATABASE_URL')
  })

  it('orders Pūrṇa cleanup and port release before Nirmana attestation and data-plane restore proof', () => {
    const bootstrap = jobs['privileged-bootstrap']
    const preflight = bootstrap.steps.find((step) => step.name === 'One-shot Nirmana evidence ownership preflight')
    const marker = bootstrap.steps.find((step) => step.name === 'Attest Nirmana ownership handoff as deployment-only migrator')
    const stateIndex = workflow.indexOf('- name: Refresh protected bootstrap state under the exclusive lock')
    const adminProxyIndex = workflow.indexOf('- name: Start one-shot Pūrṇa admin proxy')
    const adminRouteIndex = workflow.indexOf('- name: Validate one-shot Pūrṇa admin database route')
    const purnaPreflightIndex = workflow.indexOf('- name: One-shot Pūrṇa protected-owner preflight')
    const purnaMigrationIndex = workflow.indexOf('- name: Apply exact Pūrṇa protected-owner migrations')
    const purnaPostflightIndex = workflow.indexOf('- name: Close and attest Pūrṇa protected-owner handoff')
    const purnaReleaseIndex = workflow.indexOf('- name: Release one-shot Pūrṇa admin proxy port')
    const nirmanaMarkerIndex = workflow.indexOf('- name: Attest Nirmana ownership handoff as deployment-only migrator')
    const dataPlaneCutoverIndex = workflow.indexOf('- name: Execute protected cutover under backup, restore, lease, quiescence and independent approval')

    expect(preflight?.if).toBe("steps.bootstrap-state.outputs.nirmana == 'unmarked'")
    expect(marker?.run).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(stateIndex).toBeGreaterThan(-1)
    expect(adminProxyIndex).toBeGreaterThan(stateIndex)
    expect(adminRouteIndex).toBeGreaterThan(adminProxyIndex)
    expect(purnaPreflightIndex).toBeGreaterThan(adminRouteIndex)
    expect(purnaMigrationIndex).toBeGreaterThan(purnaPreflightIndex)
    expect(purnaPostflightIndex).toBeGreaterThan(purnaMigrationIndex)
    expect(purnaReleaseIndex).toBeGreaterThan(purnaPostflightIndex)
    expect(nirmanaMarkerIndex).toBeGreaterThan(purnaReleaseIndex)
    expect(dataPlaneCutoverIndex).toBeGreaterThan(nirmanaMarkerIndex)
  })

  it('retires the watchdog secret bridge and explicitly removes serialized comment variables', () => {
    const deployWeb = workflow.match(/- name: Deploy web to Cloud Run \(no traffic\)[\s\S]*?(?=\n      - name: Resolve web candidate URL)/)?.[0]
    const envVars = deployWeb?.match(/          env_vars: \|\n([\s\S]*?)(?=          secrets: \|)/)?.[1]

    expect(deployWeb).toContain('--remove-secrets=WATCHDOG_SECRET')
    expect(deployWeb).toContain('--remove-env-vars="^|^WATCHDOG_LEGACY_FALLBACK_ENABLED|# ── 4.observability')
    expect(deployWeb).not.toContain('WATCHDOG_SECRET=watchdog-secret:1')
    expect(envVars).not.toContain('WATCHDOG_LEGACY_FALLBACK_ENABLED=')
    expect(envVars).not.toMatch(/^\s*#/m)
    expect(envVars).not.toContain('WATCHDOG_SECRET=')
  })

  it('pins newline-free Pūrṇa serving and lifecycle secret versions', () => {
    const deployWeb = workflow.match(/- name: Deploy web to Cloud Run \(no traffic\)[\s\S]*?(?=\n      - name: Resolve web candidate URL)/)?.[0]

    expect(deployWeb).toContain('DB_INQUIRY_PASSWORD=amjis-inquiry-db-password:2')
    expect(deployWeb).toContain('INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT=inquiry-lifecycle-signing-key:2')
    expect(deployWeb).not.toContain('DB_INQUIRY_PASSWORD=amjis-inquiry-db-password:1')
    expect(deployWeb).not.toContain('INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT=inquiry-lifecycle-signing-key:1')
  })

  it('removes one-shot bootstrap ACL dependencies before final marked attestation', () => {
    expect(purnaPostflight).toContain('GRANT amjis_app TO purna_inquiry_bootstrap')
    expect(purnaPostflight).toContain('REVOKE SELECT ON TABLE public._migrations_applied FROM purna_inquiry_bootstrap')
    expect(purnaPostflight).toContain('REVOKE USAGE ON SCHEMA public FROM purna_inquiry_bootstrap')
    expect(purnaPostflight).toContain("dependency.deptype='a'")
    expect(purnaPostflight).toContain('final.bootstrap_acl_dependencies !== 0')
    expect(purnaStatus).toContain("dependency.deptype='a'")
    expect(purnaStatus).toContain("return 'rearm_required'")
    expect(purnaStatus).toContain('row.bootstrap_acl_dependencies !== 0')
  })
})
