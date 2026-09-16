import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')

describe('Nirmana ownership deployment attestation', () => {
  it('starts and health-checks both migration proxy listeners', () => {
    const proxy = workflow.match(/- name: Start Cloud SQL Auth Proxy[\s\S]*?(?=\n      - name: Set up Node\.js for migration runner)/)?.[0]

    expect(proxy).toContain('--port 5432')
    expect(proxy).toContain('--port 5433')
    expect(proxy).toContain('for port in 5432 5433')
    expect(proxy).toContain('/dev/tcp/127.0.0.1/$port')
  })

  it('fails closed unless both credentials route to the same database through their approved listeners', () => {
    const routes = workflow.match(/- name: Validate migration database routes[\s\S]*?(?=\n      - name: Inspect Nirmana evidence ownership handoff marker)/)?.[0]

    expect(routes).toContain('PROD_DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}')
    expect(routes).toContain('PURNA_INQUIRY_ADMIN_DATABASE_URL: ${{ secrets.PURNA_INQUIRY_ADMIN_DATABASE_URL }}')
    expect(routes).toContain('npx tsx scripts/validate-migration-database-routes.ts')
  })

  it('runs the one-shot preflight conditionally and reattests after Pūrṇa cleanup on every deployment', () => {
    const preflight = workflow.match(/- name: One-shot Nirmana evidence ownership preflight[\s\S]*?(?=\n      - name: Inspect Pūrṇa inquiry protected-owner handoff)/)?.[0]
    const marker = workflow.match(/- name: Attest Nirmana ownership handoff as deployment-only migrator[\s\S]*?(?=\n      - name: (?:Require explicit bootstrap rearm|Run general database migrations))/)?.[0]
    const proxyIndex = workflow.indexOf('- name: Start Cloud SQL Auth Proxy')
    const purnaPreflightIndex = workflow.indexOf('- name: One-shot Pūrṇa protected-owner preflight')
    const purnaMigrationIndex = workflow.indexOf('- name: Apply exact Pūrṇa protected-owner migrations')
    const purnaPostflightIndex = workflow.indexOf('- name: Close and attest Pūrṇa protected-owner handoff')
    const nirmanaMarkerIndex = workflow.indexOf('- name: Attest Nirmana ownership handoff as deployment-only migrator')

    expect(preflight).toContain("if: steps.nirmana-ownership.outputs.state == 'unmarked'")
    expect(marker).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(marker).not.toMatch(/^\s*if:/m)
    expect(proxyIndex).toBeGreaterThan(-1)
    expect(purnaPreflightIndex).toBeGreaterThan(proxyIndex)
    expect(purnaMigrationIndex).toBeGreaterThan(purnaPreflightIndex)
    expect(purnaPostflightIndex).toBeGreaterThan(purnaMigrationIndex)
    expect(nirmanaMarkerIndex).toBeGreaterThan(purnaPostflightIndex)
  })
})
