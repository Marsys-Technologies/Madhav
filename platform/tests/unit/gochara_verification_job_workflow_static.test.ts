/** The Gochara verification-job definition workflow (act 6): static properties a reviewer must be able to rely on. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'
import { ancestryGit, runWorkflowShell } from './helpers/gochara_workflow_shell'

const root = resolve(__dirname, '../../..')
const text = readFileSync(resolve(root, '.github/workflows/gochara-verification-job-deploy.yml'), 'utf8')
const wf = parse(text) as any
const job = wf.jobs.define
const code = text.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')
const deploy = (job.steps as any[]).find((s) => String(s.run ?? '').includes('gcloud run jobs deploy'))

describe('gochara-verification-job-deploy.yml', () => {
  it.each(['yes', 'no'])('executes the reviewed-ancestor guard when contained by main: %s', contained => {
    const guard = job.steps.find((s: any) => String(s.name).startsWith('Bind the definition'))
    const result = runWorkflowShell(guard.run, { git: ancestryGit }, {
      GITHUB_SHA: 'a'.repeat(40), J56_REVIEWED_ON_MAIN: contained,
    })
    expect(result.status, result.stderr).toBe(contained === 'yes' ? 0 : 1)
    expect(result.calls.at(-1)?.args).toEqual(['merge-base', '--is-ancestor', 'a'.repeat(40), 'origin/main'])
  })

  it('executes deploy and readback with one task and the same pinned timeout and resources', () => {
    const readback = job.steps.find((s: any) => String(s.run).includes('gochara_verification_job_readback.py'))
    const result = runWorkflowShell(`${deploy.run}\n${readback.run}`, {
      gcloud: 'if (args.includes("describe")) console.log("{}");',
      curl: 'console.log("{}");', python3: '',
    }, { ...wf.env, IMAGE_DIGEST: `sha256:${'b'.repeat(64)}`, GITHUB_SHA: 'a'.repeat(40) })
    expect(result.status, result.stderr).toBe(0)
    const calls = result.calls.filter(c => c.command === 'gcloud' && c.args[2] === 'deploy')
    expect(calls).toHaveLength(1)
    const deployed = calls[0].args
    const checked = result.calls.find(c => c.command === 'python3')!.args
    const value = (args: string[], flag: string) => {
      expect(args.filter(a => a === flag)).toHaveLength(1)
      return args[args.indexOf(flag) + 1]
    }
    expect(value(deployed, '--tasks')).toBe('1')
    expect(value(deployed, '--task-timeout')).toBe('7200')
    expect(value(checked, '--timeout-seconds')).toBe('7200')
    for (const [flag, expected] of [['--memory', '8Gi'], ['--cpu', '2']]) {
      expect(value(deployed, flag)).toBe(expected)
      expect(value(checked, flag)).toBe(expected)
    }
  })

  it.each([0, 23])('executes the isolation preflight and propagates its exit %i', exit => {
    const preflight = job.steps.find((s: any) => String(s.name).startsWith('Run the secret-isolation preflight'))
    const result = runWorkflowShell(preflight.run, { npx: `process.exit(${exit});` })
    expect(result.status, result.stderr).toBe(exit)
    expect(result.calls).toHaveLength(1)
    expect(result.calls[0].command).toBe('npx')
    expect(result.calls[0].args).toEqual(['tsx', 'scripts/data-plane-secret-isolation-preflight.ts'])
    expect(result.calls[0].cwd).toMatch(/\/platform$/)
  })

  it('is workflow_dispatch only, from main, behind an exact confirmation phrase', () => {
    expect(Object.keys(wf.on)).toEqual(['workflow_dispatch'])
    expect(job.if).toContain("github.ref == 'refs/heads/main'")
    expect(job.if).toContain("inputs.confirm == 'DEFINE-GOCHARA-VERIFICATION-JOB'")
    expect(wf.permissions).toEqual({ contents: 'read', 'id-token': 'write' })
  })
  it('names the one job, the verifier identity and the one secret that act 7\'s gate permits', () => {
    expect(wf.env.VERIFICATION_JOB).toBe('gochara-verification-job')
    expect(wf.env.VERIFIER_SERVICE_ACCOUNT).toBe('gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com')
    expect(wf.env.VERIFIER_SECRET).toBe('gochara-verifier-db-url')
  })
  it('deploys the verifier entry point with exactly one secret and the commit-pinned image and runner identity', () => {
    const run = String(deploy.run)
    expect(run).toContain('--command "python,-m,pipeline.orchestrator.verification_job"')
    expect(run).toContain('--clear-args')
    expect(run).toContain('--service-account "$VERIFIER_SERVICE_ACCOUNT"')
    expect(run).toContain('--set-secrets "GOCHARA_VERIFIER_DB_URL=${VERIFIER_SECRET}:latest"')
    expect(run).toContain('--set-env-vars "GOCHARA_RUNNER_COMMIT=${GITHUB_SHA},GOCHARA_RUNNER_IMAGE_DIGEST=${IMAGE_DIGEST}"')   // ST-WIRE-2: the verifier records both as the brief's producer
    expect(run).toContain('--image "${PIPELINE_IMAGE_REPO}@${IMAGE_DIGEST}"')                       // by IMMUTABLE digest, never a tag
    expect(run).not.toContain('${PIPELINE_IMAGE_REPO}:${GITHUB_SHA}')
    expect(run).toContain('--max-retries 0')
    expect(run.match(/--set-secrets/g)).toHaveLength(1)
    expect(run).not.toMatch(/--update-secrets|--add-secrets|--remove-secrets/)
  })
  it('never touches the builder identity, the builder secret or the sealer, and never runs or builds anything', () => {
    expect(code).not.toMatch(/data-plane-builder|DATABASE_URL=|brahma-build-pipeline-job|GOCHARA_SEALER|gochara-sealer/)
    expect(code).not.toMatch(/gcloud run jobs execute|docker\/build-push-action|secrets versions|environment:/)
  })
  it('refuses to define the job unless an image exists for the dispatched commit, deploys by its digest, and reads the WHOLE definition back', () => {
    const steps = job.steps as any[]
    const check = steps.findIndex((s) => String(s.run ?? '').includes('gcloud artifacts docker images describe'))
    const dep = steps.indexOf(deploy)
    expect(check).toBeGreaterThanOrEqual(0)
    expect(check).toBeLessThan(dep)
    const readback = steps.findIndex((s) => String(s.run ?? '').includes('gochara_verification_job_readback.py'))
    expect(readback).toBeGreaterThan(dep)
    const rb = String(steps[readback].run)
    for (const flag of ['--image-digest', '--service-account', '--runner-commit', '--secret-name', '--cloudsql-instance', '--timeout-seconds', '--memory', '--cpu']) expect(rb).toContain(flag)
  })
  it('R13-3: INVOKES the #2961 isolation preflight explicitly, after the deploy, in strict mode', () => {
    const steps = job.steps as any[]
    const pre = steps.findIndex((s) => String(s.run ?? '').includes('data-plane-secret-isolation-preflight.ts'))
    expect(pre).toBeGreaterThan(steps.indexOf(deploy))
    expect(steps[pre].env.DATA_PLANE_SECRET_ISOLATION_MODE).toBe('strict')
    expect(steps[pre].env.GOOGLE_CLOUD_PROJECT).toBe('madhav-astrology')
    expect(steps[pre].env.DATA_PLANE_VERIFIER_PHASE).toBe('deployable')   // R15-1: the phase is declared, never inferred
    expect(steps[pre].env.DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS).toBe('${{ vars.DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS }}')   // F-R16-2: the declared-exceptions channel is wired
  })
  it('R13-3: shares ONE concurrency group with the sealing workflow', () => {
    expect(wf.concurrency.group).toBe('gochara-verification-and-sealing')
    expect(wf.concurrency['cancel-in-progress']).toBe(false)
  })
  it('F-R15-3: reads maxRetries from the v2 REST representation (a presence-bearing union member) in addition to the v1 describe', () => {
    const steps = job.steps as any[]
    const rb = steps.find((st) => String(st.run ?? '').includes('gochara_verification_job_readback.py'))
    expect(String(rb.run)).toContain('https://run.googleapis.com/v2/projects/madhav-astrology/locations/')
    expect(String(rb.run)).toContain('--v2-job-file job.v2.json')
  })
})
