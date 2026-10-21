/** The Gochara approved-seal workflow (R12-2): static properties a reviewer must be able to rely on. */
import { chmodSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'
import { ancestryGit, runWorkflowShell } from './helpers/gochara_workflow_shell'

const root = resolve(__dirname, '../../..')
const text = readFileSync(resolve(root, '.github/workflows/gochara-seal-approved.yml'), 'utf8')
const orch = readFileSync(resolve(root, 'platform/scripts/gochara-seal-approved.sh'), 'utf8')
const wf = parse(text) as any
const brief = wf.jobs.brief
const seal = wf.jobs.seal
const code = (t: string) => t.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')

describe('gochara-seal-approved.yml', () => {
  it.each([
    ['brief', 'yes'], ['brief', 'no'], ['seal', 'yes'], ['seal', 'no'],
  ])('executes the %s revision guard when reviewed HEAD is on main: %s', (name, contained) => {
    const guard = wf.jobs[name].steps.find((s: any) => String(s.name).startsWith('Bind to the reviewed sealing revision'))
    const result = runWorkflowShell(guard.run, { git: ancestryGit }, {
      GITHUB_SHA: 'a'.repeat(40), EXPECTED_SEALING_COMMIT: 'a'.repeat(40), J56_REVIEWED_ON_MAIN: contained,
    })
    expect(result.status, result.stderr).toBe(contained === 'yes' ? 0 : 1)
    expect(result.calls.at(-1)?.args).toEqual(['merge-base', '--is-ancestor', 'a'.repeat(40), 'origin/main'])
  })

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
    expect(briefText).not.toMatch(/GOCHARA_SEALER_DB_URL|gochara-sealer-db-url|SEALER_SECRET/)
    // C-02: the Secret Manager read happens in exactly two steps of the GATED job: the orchestrator (the seal) and the read-only reconcile that follows it
    const sealReads = (seal.steps as any[]).filter((s) => String(s.run ?? '').includes('gcloud secrets versions access'))
    expect(sealReads).toHaveLength(2)
    expect(String(sealReads[0].run)).toContain('bash platform/scripts/gochara-seal-approved.sh')
    expect(String(sealReads[1].run)).toContain('gochara_seal_reconcile.py')
    expect(String(sealReads[1].run)).not.toMatch(/gochara_seal_approval|seal_job|INSERT|UPDATE/)
    expect((text.match(/gcloud secrets versions access/g) ?? []).length).toBe(2)
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
    expect(String(reconcile.run)).toContain('exit "$RC"')
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
    const sealStep = (seal.steps as any[]).find((s) => String(s.run ?? '').includes('bash platform/scripts/gochara-seal-approved.sh'))
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
  it('F-R16-4a: the log read is bounded by an explicit timestamp from the execution\'s own startTime — `--freshness` (a no-op with --order=asc) is NOT used', () => {
    const steps = brief.steps as any[]
    const read = steps.find((st) => String(st.name ?? '').startsWith('Retrieve the brief'))
    const run = String(read.run)
    expect(run).toContain('--order=asc')
    expect(run).not.toMatch(/--freshness(?!`)/)                    // the flag may be mentioned in the comment only (followed by a backtick there)
    expect(run).toContain('status')
    expect(run).toContain('startTime')
    expect(run).toContain('AND timestamp>=')
    expect(run).toContain('cannot bound the log read')            // a missing startTime refuses, it does not silently read everything
  })
})


describe('P08 rebuilt operation boundary', () => {
  it.each([
    [0, 'SEALED'], [10, 'NOT_SEALED'], [11, 'INCONSISTENT'], [12, 'UNREADABLE'],
  ])('requires a measured SEALED result for workflow success (reconcile exit %s)', (exit, state) => {
    const step = seal.steps.find((s: { name?: string }) => String(s.name).startsWith('Reconcile'))
    const dir = mkdtempSync(join(process.env.JOB_SCRATCH ?? tmpdir(), 'j5s-reconcile-'))
    try {
      // Execute the actual workflow shell; only the read-only DB command is replaced.
      const python = join(dir, 'python3')
      writeFileSync(python, `#!/bin/sh\nprintf '%s\\n' '{"state":"${state}"}'\nexit ${exit}\n`)
      chmodSync(python, 0o755)
      // C-02: the step now reads the sealer DSN with gcloud; stub it so the test never reaches a real gcloud (slow on a CI runner)
      const gcloud = join(dir, 'gcloud')
      writeFileSync(gcloud, `#!/bin/sh\nprintf '%s\\n' 'postgresql://gochara_sealer:fake-Zq9-marker@127.0.0.1:5432/amjis'\nexit 0\n`)
      chmodSync(gcloud, 0o755)
      const result = spawnSync('bash', ['-c', step.run], {
        cwd: dir, encoding: 'utf8', timeout: 10_000,
        env: { PATH: `${dir}:${process.env.PATH}`, SEALER_SECRET: 'gochara-sealer-db-url', CHART_ID: '482012f1-710e-4a25-994a-93821f5871aa',
          GENERATION: '5.0', BRIEF_DIGEST: 'a'.repeat(64), GITHUB_RUN_ID: '17', GITHUB_RUN_ATTEMPT: '1',
          GITHUB_STEP_SUMMARY: join(dir, 'summary.md') },
      })
      expect(result.error).toBeUndefined()
      expect(result.status).toBe(exit)
      expect(JSON.parse(readFileSync(join(dir, 'reconcile.json'), 'utf8')).state).toBe(state)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })
  it('pins the only full candidate and chart before executing a verifier with comma-separated overrides', () => {
    const step = brief.steps.find((s: any) => s.id === 'candidate')
    expect(step).toBeDefined()
    expect(step.run).toContain('482012f1-710e-4a25-994a-93821f5871aa')
    expect(step.run).toContain('"$GENERATION" = "5.0"')
    expect(brief.steps.indexOf(step)).toBeLessThan(brief.steps.findIndex((s: any) => s.id === 'execute'))
  })
  it('reads Cloud SQL and task count in the pre-execution definition as well as task fields', () => {
    const image = brief.steps.find((s: any) => s.id === 'image')
    expect(image.run).toContain('--cloudsql-instance "$CLOUDSQL_INSTANCE"')
  })
  it('tears down its proxy on every outcome and retains reconciliation with its approval', () => {
    const start = seal.steps.find((s: any) => s.name === 'Start Cloud SQL Auth Proxy')
    expect(start.id).toBe('proxy')
    expect(start.run).toContain('pid=$proxy_pid')
    const stop = seal.steps.find((s: any) => s.id === 'stop-proxy')
    expect(stop.if).toContain('always()')
    expect(stop.run).toContain('kill "$PROXY_PID"')
    const rec = seal.steps.find((s: any) => String(s.name).startsWith('Reconcile'))
    expect(rec.run).toContain('reconcile.json')
    const record = seal.steps.find((s: any) => s.uses?.startsWith('actions/upload-artifact'))
    expect(record.with.path).toContain('reconcile.json')
  })
})

// C-02 (BEFORE_SEAL): the sealer DSN is written to Secret Manager `gochara-sealer-db-url` by the sealer-credential stage
// (platform/scripts/gochara-provision-roles.sh) and NOTHING wrote the GitHub environment secret the workflow used to read.
describe('gochara-seal-approved.yml sealer DSN from Secret Manager (C-02)', () => {
  const dsn = 'postgresql://gochara_sealer:fake-Zq9-marker@127.0.0.1:5432/amjis'
  const pw = 'fake-Zq9-marker'
  const sealStep = (seal.steps as any[]).find((s) => String(s.run ?? '').includes('gochara-seal-approved.sh'))
  const reconcileStep = (seal.steps as any[]).find((s) => String(s.run ?? '').includes('gochara_seal_reconcile.py'))
  const gcloudOk = `process.stdout.write(${JSON.stringify(dsn + '\n')}); process.exit(0);`
  const orchestrator = `console.log('ORCH_DSN_MATCH=' + (process.env.GOCHARA_SEALER_DB_URL === process.env.EXPECT_DSN)); process.exit(0);`

  it('no longer references the GitHub environment secret anywhere in the workflow, comments included', () => {
    expect(text).not.toMatch(/secrets\.GOCHARA_SEALER_DB_URL/)
    expect(text).not.toMatch(/secrets\.GOCHARA_SEALER/)
  })
  it('reads the ONE named secret at run time through the existing Workload Identity step, which precedes the read', () => {
    const names = (seal.steps as any[]).map((s) => String(s.name))
    const auth = names.findIndex((n) => n === 'Authenticate to Google Cloud')
    expect(auth).toBeGreaterThan(-1)
    expect(auth).toBeLessThan((seal.steps as any[]).indexOf(sealStep))
    expect(sealStep.env.SEALER_SECRET).toBe('gochara-sealer-db-url')
    expect(reconcileStep.env.SEALER_SECRET).toBe('gochara-sealer-db-url')
    expect(String(sealStep.run)).toContain('gcloud secrets versions access latest --secret="$SEALER_SECRET" --project=madhav-astrology')
  })
  it('passes the DSN only through the environment of the steps that need it: never job/workflow env, GITHUB_ENV, GITHUB_OUTPUT or an artifact', () => {
    expect(wf.env.GOCHARA_SEALER_DB_URL).toBeUndefined()
    expect(seal.env).toBeUndefined()
    for (const s of seal.steps as any[]) expect(s.env?.GOCHARA_SEALER_DB_URL).toBeUndefined()
    const lines = code(text).split('\n').filter((l) => l.includes('GOCHARA_SEALER_DB_URL'))
    for (const l of lines) expect(l).not.toMatch(/GITHUB_ENV|GITHUB_OUTPUT|GITHUB_STEP_SUMMARY|\.json|upload-artifact/)
  })
  it('never echoes the DSN: every use of the variable is an assignment, a test, a mask, an export/unset or the read-only reconcile call', () => {
    const allowed = [
      /^\s*if ! GOCHARA_SEALER_DB_URL="\$\(gcloud secrets versions access latest .* 2>\/dev\/null\)" \|\| \[ -z "\$GOCHARA_SEALER_DB_URL" \]; then$/,
      /^\s*if GOCHARA_SEALER_DB_URL="\$\(gcloud secrets versions access latest .* 2>\/dev\/null\)" && \[ -n "\$GOCHARA_SEALER_DB_URL" \]; then$/,
      /^\s*echo "::add-mask::\$GOCHARA_SEALER_DB_URL"$/,
      /^\s*SEALER_PASSWORD="\$\{GOCHARA_SEALER_DB_URL#\*:\/\/\*:\}"$/,
      /^\s*export GOCHARA_SEALER_DB_URL$/,
      /^\s*unset GOCHARA_SEALER_DB_URL$/,
    ]
    const offenders = code(text).split('\n').filter((l) => l.includes('GOCHARA_SEALER_DB_URL') && !allowed.some((a) => a.test(l)))
    expect(offenders).toEqual([])
    expect(code(text)).not.toMatch(/set -[a-z]*x|xtrace|\bprintenv\b|(^|\s)env(\s|$)/m)
    expect(code(text).split('\n').filter((l) => /(echo|printf|cat)[^\n]*\$\{?SEALER_PASSWORD/.test(l) && !/echo "::add-mask::\$SEALER_PASSWORD"/.test(l))).toEqual([])
  })
  it('executes: reads the secret, masks DSN and password, hands the DSN to the orchestrator, and prints it nowhere', () => {
    const r = runWorkflowShell(sealStep.run, { gcloud: gcloudOk, bash: orchestrator }, { SEALER_SECRET: 'gochara-sealer-db-url', EXPECT_DSN: dsn })
    expect(r.status, r.stderr).toBe(0)
    expect(r.calls.find((c) => c.command === 'gcloud')?.args).toEqual(['secrets', 'versions', 'access', 'latest', '--secret=gochara-sealer-db-url', '--project=madhav-astrology'])
    expect(r.calls.find((c) => c.command === 'bash')?.args).toEqual(['platform/scripts/gochara-seal-approved.sh'])
    expect(r.stdout).toContain('ORCH_DSN_MATCH=true')
    const lines = r.stdout.split('\n')
    expect(lines).toContain(`::add-mask::${dsn}`)
    expect(lines).toContain(`::add-mask::${pw}`)
    // the secret appears ONLY on the two mask commands (the runner's mask directive), never anywhere else, and never on stderr
    expect(lines.filter((l) => l.includes(pw) && !l.startsWith('::add-mask::'))).toEqual([])
    expect(r.stderr).not.toContain(pw)
    // masks are issued before the orchestrator runs
    expect(lines.findIndex((l) => l.startsWith('::add-mask::'))).toBeLessThan(lines.findIndex((l) => l.startsWith('ORCH_DSN_MATCH')))
  })
  it.each([
    ['the read is refused (no secretAccessor / no enabled version)', `process.stderr.write('PERMISSION_DENIED ${'x'}'); process.exit(1);`],
    ['the read succeeds with an empty payload', `process.exit(0);`],
  ])('fails closed with a named error BEFORE the orchestrator when %s', (_n, gcloud) => {
    const r = runWorkflowShell(sealStep.run, { gcloud, bash: orchestrator }, { SEALER_SECRET: 'gochara-sealer-db-url', EXPECT_DSN: dsn })
    expect(r.status).not.toBe(0)
    expect(r.stdout).toContain('::error::sealer-dsn-unavailable')
    expect(r.stdout).toContain('gochara-sealer-db-url')
    expect(r.calls.some((c) => c.command === 'bash')).toBe(false)
  })
  it('reconcile: reads the same secret, masks it, passes it to the reconcile script and prints it nowhere', () => {
    const py = `console.log(JSON.stringify({state: 'SEALED', dsn_match: process.env.GOCHARA_SEALER_DB_URL === process.env.EXPECT_DSN})); process.exit(0);`
    const r = runWorkflowShell(reconcileStep.run, { gcloud: gcloudOk, python3: py }, {
      SEALER_SECRET: 'gochara-sealer-db-url', EXPECT_DSN: dsn, CHART_ID: 'c', GENERATION: '5.0', BRIEF_DIGEST: 'd',
      GITHUB_RUN_ID: '1', GITHUB_RUN_ATTEMPT: '1', GITHUB_STEP_SUMMARY: '/dev/null',
    })
    expect(r.status, r.stderr).toBe(0)
    expect(r.stdout).toContain('"dsn_match":true')
    expect(r.stdout.split('\n').filter((l) => l.includes(pw) && !l.startsWith('::add-mask::'))).toEqual([])
  })
  it('reconcile: an unreadable secret leaves the variable unset, is named, and the reconcile script reports UNREADABLE (never "not sealed")', () => {
    const py = `if (process.env.GOCHARA_SEALER_DB_URL !== undefined) process.exit(99); console.log(JSON.stringify({state: 'UNREADABLE'})); process.exit(12);`
    const r = runWorkflowShell(reconcileStep.run, { gcloud: 'process.exit(1);', python3: py }, {
      SEALER_SECRET: 'gochara-sealer-db-url', CHART_ID: 'c', GENERATION: '5.0', BRIEF_DIGEST: 'd',
      GITHUB_RUN_ID: '1', GITHUB_RUN_ATTEMPT: '1', GITHUB_STEP_SUMMARY: '/dev/null',
    })
    expect(r.status).toBe(12)
    expect(r.stdout).toContain('::error::sealer-dsn-unavailable')
    expect(r.stdout).toContain('UNREADABLE')
  })
})
