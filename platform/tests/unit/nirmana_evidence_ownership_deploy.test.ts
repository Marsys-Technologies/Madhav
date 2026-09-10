import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')

describe('Nirmana ownership deployment attestation', () => {
  it('runs preflight only before the initial marker but reattests on every deployment', () => {
    const preflight = workflow.match(/- name: One-shot Nirmana evidence ownership preflight[\s\S]*?(?=\n      - name: Attest Nirmana ownership handoff)/)?.[0]
    const marker = workflow.match(/- name: Attest Nirmana ownership handoff as deployment-only migrator[\s\S]*?(?=\n      - name: Run general database migrations)/)?.[0]

    expect(preflight).toContain("if: steps.nirmana-ownership.outputs.state == 'unmarked'")
    expect(marker).toContain('npx tsx scripts/nirmana-evidence-ownership-marker.ts')
    expect(marker).not.toMatch(/^\s*if:/m)
  })
})
