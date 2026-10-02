/** The Gochara verification-job definition workflow (act 6): static properties a reviewer must be able to rely on. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parse } from 'yaml'

const root = resolve(__dirname, '../../..')
const text = readFileSync(resolve(root, '.github/workflows/gochara-verification-job-deploy.yml'), 'utf8')
const wf = parse(text) as any
const job = wf.jobs.define
const code = text.split('\n').filter((l) => !l.trim().startsWith('#')).join('\n')
const deploy = (job.steps as any[]).find((s) => String(s.run ?? '').includes('gcloud run jobs deploy'))

describe('gochara-verification-job-deploy.yml', () => {
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
    expect(run).toContain('--set-env-vars "GOCHARA_RUNNER_COMMIT=${GITHUB_SHA}"')
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
  })
  it('R13-3: shares ONE concurrency group with the sealing workflow', () => {
    expect(wf.concurrency.group).toBe('gochara-verification-and-sealing')
    expect(wf.concurrency['cancel-in-progress']).toBe(false)
  })
})
