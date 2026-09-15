import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { load } from 'js-yaml'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
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
    expect(marker?.if).toBe("steps.bootstrap-state.outputs.nirmana == 'unmarked'")
    expect(marker?.run).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(routineAttestation?.env).toEqual({ DATABASE_URL: '${{ secrets.PROD_DATABASE_URL }}' })
    expect(routineAttestation?.run).toContain('nirmana-evidence-ownership-status.ts')
    expect(JSON.stringify(migrate)).not.toContain('NIRMANA_MIGRATOR_DATABASE_URL')
  })
})
