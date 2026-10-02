/** The Gochara approved-seal workflow (R12-2): static properties a reviewer must be able to rely on. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'

const root = resolve(__dirname, '../../..')
const text = readFileSync(resolve(root, '.github/workflows/gochara-seal-approved.yml'), 'utf8')
const orch = readFileSync(resolve(root, 'platform/scripts/gochara-seal-approved.sh'), 'utf8')
const wf = parse(text) as any
const brief = wf.jobs.brief
const seal = wf.jobs.seal
const code = (t: string) => t.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')

describe('gochara-seal-approved.yml', () => {
  it('is workflow_dispatch only, from main, behind an exact confirmation phrase', () => {
    expect(Object.keys(wf.on)).toEqual(['workflow_dispatch'])
    expect(brief.if).toContain("github.ref == 'refs/heads/main'")
    expect(brief.if).toContain("inputs.confirm == 'SEAL-GOCHARA-CANDIDATE'")
    expect(wf.permissions).toEqual({ contents: 'read', 'id-token': 'write', actions: 'read' })
  })
  it('confines the sealer credential and the approval gate to the seal job; the brief job has neither', () => {
    expect(brief.environment).toBeUndefined()
    expect(seal.environment).toBe('gochara-seal')
    expect(seal.needs).toBe('brief')
    const briefText = JSON.stringify(brief)
    expect(briefText).not.toMatch(/GOCHARA_SEALER_DB_URL/)
    const sealUses = (seal.steps as any[]).filter((s) => JSON.stringify(s).includes('secrets.GOCHARA_SEALER_DB_URL'))
    expect(sealUses).toHaveLength(1)
    expect(sealUses[0].run).toBe('bash platform/scripts/gochara-seal-approved.sh')
    // the secret appears nowhere else in the whole file
    expect((text.match(/secrets\.GOCHARA_SEALER_DB_URL/g) ?? []).length).toBe(1)
  })
  it('binds both jobs to one reviewed revision: github.sha, an ancestor of origin/main, passed forward and re-checked', () => {
    for (const j of [brief, seal]) {
      const run = (j.steps as any[]).map((s) => s.run ?? '').join('\n')
      expect(run).toContain('git merge-base --is-ancestor')
    }
    expect(brief.outputs.sealing_commit).toBe('${{ github.sha }}')
    expect(JSON.stringify(seal.steps)).toContain('needs.brief.outputs.sealing_commit')
    expect(JSON.stringify(brief.steps)).toContain('--sealing-commit,${GITHUB_SHA}')
  })
  it('displays and retains the brief before the gate, and retrieves THIS run\'s approval from the approval API', () => {
    const bs = JSON.stringify(brief.steps)
    expect(bs).toContain('GITHUB_STEP_SUMMARY')
    expect(bs).toContain('upload-artifact')
    expect(bs).toContain('brief-digest: $DIGEST  run: $GITHUB_RUN_ID  attempt: $GITHUB_RUN_ATTEMPT')
    expect(JSON.stringify(seal.steps)).toContain('actions/runs/${GITHUB_RUN_ID}/approvals')
    expect(JSON.stringify(seal.steps)).toContain('download-artifact')
  })
  it('verifies the Cloud SQL proxy download against a pinned sha256, states in the brief that the approval is not independent, and passes the triggering actor for the mechanical note', () => {
    const proxy = (seal.steps as any[]).find((x) => x.name === 'Start Cloud SQL Auth Proxy')
    expect(proxy.run).toContain('276139ff5d5dc484c51e1a9c065d69a9f6e47d5b726f94dced253b0227df2056  cloud-sql-proxy')
    expect(proxy.run.indexOf('sha256sum -c')).toBeLessThan(proxy.run.indexOf('chmod +x'))
    expect(JSON.stringify(brief.steps)).toContain('NOT an independent human check')
    expect(text).toContain('TRIGGERING_ACTOR: ${{ github.triggering_actor }}')
  })
  it('reads the execution logs only through the single-job log view (act 12), never the whole project log', () => {
    const read = (brief.steps as any[]).find((x) => x.name === 'Retrieve the brief from the execution\'s logs')
    expect(read.run).toContain('--bucket=_Default --location=global --view=gochara_verification_job')
  })
  it('passes inputs only through env and never swallows a failure', () => {
    for (const j of [brief, seal]) for (const s of j.steps as any[]) if (s.run) expect(s.run).not.toContain('${{')
    expect(code(text)).not.toMatch(/continue-on-error|\|\|\s*true|set \+e/)
    expect(code(text)).not.toMatch(/set -x|xtrace/)
  })
  it('the seal job calls only the orchestrator, which checks everything BEFORE the seal job and propagates its status', () => {
    const c = code(orch)
    expect(c.indexOf('gochara_seal_brief_check.py')).toBeLessThan(c.indexOf('$SEAL_JOB_CMD'))
    expect(c.indexOf('gochara_seal_approval.py')).toBeLessThan(c.indexOf('$SEAL_JOB_CMD'))
    expect(c).toContain('exit "$rc"')
    expect(c).toContain('--approval-file "$APPROVAL_FILE"')
    expect(c).not.toMatch(/\|\|\s*true/)
  })
  it('asks the verification job for the brief (always chunked since a289b38eb) and carries BOTH brief files (the brief bytes and the compact result) to the gated job', () => {
    const exec = (brief.steps as any[]).find((s) => String(s.run ?? '').includes('gcloud run jobs execute'))
    expect(String(exec.run)).toContain('--brief,--sealing-commit')
    expect(String(exec.run)).not.toContain('--brief-chunks')                          // Stream A a289b38eb: the chunk transport is ALWAYS on; the flag no longer exists
    const extract = (brief.steps as any[]).find((s) => String(s.run ?? '').includes('gochara_seal_brief_extract.py'))
    expect(String(extract.run)).toContain('--out-brief brief.json --out-compact brief.compact.json')
    const chk = (brief.steps as any[]).find((s) => String(s.run ?? '').includes('gochara_seal_brief_check.py'))
    expect(String(chk.run)).toContain('--brief-file brief.json --compact-file brief.compact.json')
    const upload = (brief.steps as any[]).find((s) => s.uses?.startsWith('actions/upload-artifact'))
    expect(String(upload.with.path)).toContain('brief.json')
    expect(String(upload.with.path)).toContain('brief.compact.json')
    const sealStep = (seal.steps as any[]).find((s) => s.run === 'bash platform/scripts/gochara-seal-approved.sh')
    expect(sealStep.env.BRIEF_FILE).toBe('brief.json')
    expect(sealStep.env.BRIEF_COMPACT_FILE).toBe('brief.compact.json')
  })
})
