import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')

describe('Nirmana ownership deployment attestation', () => {
  it('runs the one-shot preflight conditionally and reattests after Pūrṇa cleanup on every deployment', () => {
    const preflight = workflow.match(/- name: One-shot Nirmana evidence ownership preflight[\s\S]*?(?=\n      - name: Inspect Pūrṇa inquiry protected-owner handoff)/)?.[0]
    const marker = workflow.match(/- name: Attest Nirmana ownership handoff as deployment-only migrator[\s\S]*?(?=\n      - name: (?:Require explicit bootstrap rearm|Run general database migrations))/)?.[0]
    const purnaPostflightIndex = workflow.indexOf('- name: Close and attest Pūrṇa protected-owner handoff')
    const nirmanaMarkerIndex = workflow.indexOf('- name: Attest Nirmana ownership handoff as deployment-only migrator')

    expect(preflight).toContain("if: steps.nirmana-ownership.outputs.state == 'unmarked'")
    expect(marker).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(marker).not.toMatch(/^\s*if:/m)
    expect(purnaPostflightIndex).toBeGreaterThan(-1)
    expect(nirmanaMarkerIndex).toBeGreaterThan(purnaPostflightIndex)
  })
})
