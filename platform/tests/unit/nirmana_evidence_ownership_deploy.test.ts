import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
const purnaPostflight = readFileSync(resolve(__dirname, '../../scripts/purna-inquiry-ownership-postflight.ts'), 'utf8')
const purnaStatus = readFileSync(resolve(__dirname, '../../scripts/purna-inquiry-ownership-status.ts'), 'utf8')

describe('Nirmana ownership deployment attestation', () => {
  it('starts and health-checks both migration proxy listeners', () => {
    const proxy = workflow.match(/- name: Start Cloud SQL Auth Proxy[\s\S]*?(?=\n      - name: Set up Node\.js for migration runner)/)?.[0]

    expect(proxy).toContain('--port 5432')
    expect(proxy).toContain('--port 5433')
    expect(proxy).toContain('proxy_5432_pid=$!')
    expect(proxy).toContain('proxy_5433_pid=$!')
    expect(proxy).toContain('for route in "5432:$proxy_5432_pid" "5433:$proxy_5433_pid"')
    expect(proxy).toContain('kill -0 "$pid"')
    expect(proxy).toContain('/dev/tcp/127.0.0.1/$port')
  })

  it('always validates PROD but requires the one-shot route only while ownership needs it', () => {
    const prodRoute = workflow.match(/- name: Validate production migration database route[\s\S]*?(?=\n      - name: Inspect Nirmana evidence ownership handoff marker)/)?.[0]
    const adminRoute = workflow.match(/- name: Validate one-shot Pūrṇa admin database route[\s\S]*?(?=\n      - name: One-shot Pūrṇa protected-owner preflight)/)?.[0]
    const postflight = workflow.match(/- name: Close and attest Pūrṇa protected-owner handoff[\s\S]*?(?=\n      # While Pūrṇa is armed)/)?.[0]

    expect(prodRoute).toContain('PROD_DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}')
    expect(prodRoute).toContain('validate-migration-database-routes.ts --prod')
    expect(prodRoute).not.toContain('PURNA_INQUIRY_ADMIN_DATABASE_URL')
    expect(adminRoute).toContain("steps.purna-ownership.outputs.state == 'armed'")
    expect(adminRoute).toContain("steps.purna-ownership.outputs.state == 'interrupted'")
    expect(adminRoute).toContain("steps.purna-ownership.outputs.state == 'cleanup_required'")
    expect(adminRoute).toContain('PURNA_INQUIRY_ADMIN_DATABASE_URL: ${{ secrets.PURNA_INQUIRY_ADMIN_DATABASE_URL }}')
    expect(adminRoute).toContain('validate-migration-database-routes.ts --purna-admin')
    expect(postflight).toContain("steps.purna-admin-route.outcome == 'success'")
  })

  it('runs the one-shot preflight conditionally and reattests after Pūrṇa cleanup on every deployment', () => {
    const preflight = workflow.match(/- name: One-shot Nirmana evidence ownership preflight[\s\S]*?(?=\n      - name: Inspect Pūrṇa inquiry protected-owner handoff)/)?.[0]
    const marker = workflow.match(/- name: Attest Nirmana ownership handoff as deployment-only migrator[\s\S]*?(?=\n      - name: (?:Require explicit bootstrap rearm|Run general database migrations))/)?.[0]
    const proxyIndex = workflow.indexOf('- name: Start Cloud SQL Auth Proxy')
    const purnaStateIndex = workflow.indexOf('- name: Inspect Pūrṇa inquiry protected-owner handoff')
    const adminRouteIndex = workflow.indexOf('- name: Validate one-shot Pūrṇa admin database route')
    const purnaPreflightIndex = workflow.indexOf('- name: One-shot Pūrṇa protected-owner preflight')
    const purnaMigrationIndex = workflow.indexOf('- name: Apply exact Pūrṇa protected-owner migrations')
    const purnaPostflightIndex = workflow.indexOf('- name: Close and attest Pūrṇa protected-owner handoff')
    const nirmanaMarkerIndex = workflow.indexOf('- name: Attest Nirmana ownership handoff as deployment-only migrator')

    expect(preflight).toContain("if: steps.nirmana-ownership.outputs.state == 'unmarked'")
    expect(marker).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(marker).not.toMatch(/^\s*if:/m)
    expect(proxyIndex).toBeGreaterThan(-1)
    expect(purnaStateIndex).toBeGreaterThan(proxyIndex)
    expect(adminRouteIndex).toBeGreaterThan(purnaStateIndex)
    expect(purnaPreflightIndex).toBeGreaterThan(adminRouteIndex)
    expect(purnaMigrationIndex).toBeGreaterThan(purnaPreflightIndex)
    expect(purnaPostflightIndex).toBeGreaterThan(purnaMigrationIndex)
    expect(nirmanaMarkerIndex).toBeGreaterThan(purnaPostflightIndex)
  })

  it('converts the watchdog credential from a literal to a secret without serializing comments as variables', () => {
    const deployWeb = workflow.match(/- name: Deploy web to Cloud Run \(no traffic\)[\s\S]*?(?=\n      - name: Resolve web candidate URL)/)?.[0]
    const envVars = deployWeb?.match(/          env_vars: \|\n([\s\S]*?)(?=          secrets: \|)/)?.[1]

    expect(deployWeb).toContain('--remove-env-vars=WATCHDOG_SECRET')
    expect(deployWeb).toContain('WATCHDOG_SECRET=watchdog-secret:1')
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
