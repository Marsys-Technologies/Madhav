/** The gate-proof workflow (Codex R13-6): it must stay a NO-SECRET, NO-OP, environment-gated workflow, or it proves nothing about the gate. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'

const root = resolve(__dirname, '../../..')
const text = readFileSync(resolve(root, '.github/workflows/gochara-seal-gate-proof.yml'), 'utf8')
const wf = parse(text) as any
const job = wf.jobs.gate
const code = text.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')

describe('gochara-seal-gate-proof.yml', () => {
  it('is workflow_dispatch only, behind an exact phrase, with exactly one job gated by the gochara-seal environment', () => {
    expect(Object.keys(wf.on)).toEqual(['workflow_dispatch'])
    expect(Object.keys(wf.jobs)).toEqual(['gate'])
    expect(job.environment).toBe('gochara-seal')
    expect(job.if).toContain("inputs.confirm == 'PROVE-GOCHARA-SEAL-GATE'")
  })
  it('reads no secret, assumes no cloud identity and writes nothing', () => {
    expect(wf.permissions).toEqual({ contents: 'read', actions: 'read' })
    expect(code).not.toMatch(/secrets\./)
    expect(code).not.toMatch(/id-token|google-github-actions|gcloud|GOCHARA_SEALER|workload_identity/)
    expect(code).not.toMatch(/psql|psycopg|DATABASE_URL|proxy/i)
    expect(code).not.toMatch(/git push|gh (pr|release|workflow run)|--method (POST|PUT|PATCH|DELETE)|-X (POST|PUT|PATCH|DELETE)/)
  })
  it('records the approval history exactly as the API returns it and does not rely on its order', () => {
    const run = (job.steps as any[]).map((s) => String(s.run ?? '')).join('\n')
    expect(run).toContain('actions/runs/${GITHUB_RUN_ID}/approvals')
    expect(run).toContain('to_entries')            // prints every position as returned
    expect(run).not.toMatch(/\.\[-1\]|last\(|\| reverse|sort_by/)   // it never picks "latest" or re-orders: ordering is evidence only
  })
  it('has a bounded runtime and a concurrency group of its own', () => {
    expect(job['timeout-minutes']).toBeLessThanOrEqual(10)
    expect(wf.concurrency.group).toBe('gochara-seal-gate-proof')
  })
})
