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
    // exactly two steps of the GATED job see it: the orchestrator (the seal) and the read-only reconcile that follows it
    expect(sealUses).toHaveLength(2)
    expect(sealUses[0].run).toBe('bash platform/scripts/gochara-seal-approved.sh')
    expect(String(sealUses[1].run)).toContain('gochara_seal_reconcile.py')
    expect(String(sealUses[1].run)).not.toMatch(/gochara_seal_approval|seal_job|INSERT|UPDATE/)
    // the secret appears nowhere else in the whole file
    expect((text.match(/secrets\.GOCHARA_SEALER_DB_URL/g) ?? []).length).toBe(2)
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
    expect(code(text)).not.toMatch(/continue-on-error|\|\|\s*true/)
    expect(code(text)).not.toMatch(/set -x|xtrace/)
    // `set +e` exists ONLY in the two steps that are best-effort BY DESIGN: the cancel of a still-running execution and the reconcile — and the reconcile re-raises 11/12
    for (const j of [brief, seal]) for (const st of j.steps as any[]) {
      if (String(st.run ?? '').includes('set +e')) expect(String(st.name)).toMatch(/^(Cancel a still-running execution|Reconcile)/)
    }
    const reconcile = (seal.steps as any[]).find((st) => String(st.name).startsWith('Reconcile'))
    expect(String(reconcile.run)).toContain('0|10) exit 0 ;; *) exit "$RC"')
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
  it('R13-3: binds the brief to the EXECUTED resource — image digest, execution id, service account, runner commit — and cancels a still-running execution', () => {
    const steps = brief.steps as any[]
    const names = steps.map((st) => String(st.name))
    const run = (st: any) => String(st.run ?? '')
    const image = steps.find((st) => st.id === 'image'), exec = steps.find((st) => st.id === 'execute'), wait = steps.find((st) => st.id === 'wait'), check = steps.find((st) => st.id === 'check')
    expect(run(image)).toContain('gcloud artifacts docker images describe')
    expect(run(image)).toContain('gochara_seal_execution_check.py job-image')
    expect(run(image)).toContain('--image-repo "$PIPELINE_IMAGE_REPO"')
    expect(run(image)).toContain('--runner-commit "$GITHUB_SHA" --secret-name "$VERIFIER_SECRET"')
    expect(run(exec)).toContain('--async')                                               // the execution id is recorded BEFORE the wait, so a cancelled wait can still cancel it
    expect(run(exec)).not.toContain('--wait')
    expect(wait['timeout-minutes']).toBeLessThanOrEqual(brief['timeout-minutes'])
    expect(run(wait)).toContain('gcloud run jobs executions describe')
    const cancel = steps.find((st) => String(st.name).startsWith('Cancel a still-running execution'))
    expect(String(cancel.if)).toContain('always()')
    expect(String(cancel.if)).toContain("steps.wait.outcome != 'success'")
    expect(run(cancel)).toContain('gcloud run jobs executions cancel')
    expect(run(check)).toContain('gochara_seal_execution_check.py build-envelope')
    expect(run(check)).toContain('--image-digest "$IMAGE_DIGEST"')
    expect(run(check)).toContain('--image-repo "$PIPELINE_IMAGE_REPO"')
    expect(names.indexOf(String(image.name))).toBeLessThan(names.indexOf(String(exec.name)))
    expect(names.indexOf(String(exec.name))).toBeLessThan(names.indexOf(String(wait.name)))
    expect(wf.env.VERIFIER_SERVICE_ACCOUNT).toBe('gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(wf.env.VERIFICATION_JOB).toBe('gochara-verification-job')
  })
  it('R13-4: artifacts carry run id AND attempt (a seal-only re-run finds none), the approval grammar carries the brief id, and the seal step is followed by a reconcile', () => {
    const upload = (brief.steps as any[]).find((st) => st.uses?.startsWith('actions/upload-artifact'))
    expect(upload.with.name).toBe('seal-brief-${{ github.run_id }}-${{ github.run_attempt }}')
    expect(String(upload.with.path)).toContain('brief.envelope.json')
    const download = (seal.steps as any[]).find((st) => st.uses?.startsWith('actions/download-artifact'))
    expect(download.with.name).toBe('seal-brief-${{ github.run_id }}-${{ github.run_attempt }}')
    const record = (seal.steps as any[]).find((st) => st.uses?.startsWith('actions/upload-artifact'))
    expect(record.with.name).toContain('${{ github.run_attempt }}')
    expect(text).toContain('brief-digest: $DIGEST  run: $GITHUB_RUN_ID  attempt: $GITHUB_RUN_ATTEMPT  brief-id: $BRIEF_ID')
    const names = (seal.steps as any[]).map((st) => String(st.name))
    expect(names.findIndex((n) => n.startsWith('Reconcile'))).toBeGreaterThan(names.findIndex((n) => n.startsWith('Verify the approval and call the seal job')))
    const rec = (seal.steps as any[]).find((st) => String(st.name).startsWith('Reconcile'))
    expect(String(rec.if)).toContain('always()')
    expect(String(rec.if)).toContain("steps.seal.conclusion != 'skipped'")
    expect(orch).toContain('--brief-id "$BRIEF_ID"')
    expect(orch).toContain('check-envelope')
  })
  it('R13-3: shares ONE concurrency group with the job-definition workflow, and states its capacity basis', () => {
    expect(wf.concurrency.group).toBe('gochara-verification-and-sealing')
    expect(wf.concurrency['cancel-in-progress']).toBe(false)
    expect(brief['timeout-minutes']).toBeGreaterThanOrEqual(150)                        // the verification job's own task timeout is 7200 s (#2976)
    expect(seal['timeout-minutes']).toBe(30)
    expect(text).toContain('CAPACITY:')
  })
  it('R14-5: smokes the sealing job\'s dependencies (install + import of psycopg, swisseph, seal_job, verification_job, seal_flow, seal_brief) in the BRIEF job, before any approval', () => {
    const steps = brief.steps as any[]
    const smoke = steps.findIndex((st) => String(st.name ?? '').startsWith('Smoke the sealing job'))
    expect(smoke).toBeGreaterThanOrEqual(0)
    const run = String(steps[smoke].run)
    for (const needle of ['requirements-ci.txt', 'import psycopg, swisseph', 'seal_job', 'verification_job', 'seal_flow', 'seal_brief']) expect(run).toContain(needle)
    expect(smoke).toBeLessThan(steps.findIndex((st) => String(st.id ?? '') === 'execute'))
  })
  it('F-R15-3: reads maxRetries of the job AND of the execution from the v2 REST representation as well as v1', () => {
    const steps = brief.steps as any[]
    const image = steps.find((st) => st.id === 'image'), check = steps.find((st) => st.id === 'check')
    expect(String(image.run)).toContain('/jobs/${VERIFICATION_JOB}"')
    expect(String(image.run)).toContain('--v2-job-file job.v2.json')
    expect(String(check.run)).toContain('/executions/${EXECUTION}"')
    expect(String(check.run)).toContain('--v2-execution-file execution.v2.json')
  })
})
