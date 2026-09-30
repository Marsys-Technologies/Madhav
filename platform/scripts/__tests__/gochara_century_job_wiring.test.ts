import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

// Pravāha A2.5 fix-forward (steward M20260930T153249-3c6e): #2772 created
// brahma-gochara-century-job pointing at /app/platform/python-sidecar/scripts/
// kala_gochara_cutover/century_run_4_1.sh, but (1) Dockerfile.pipeline never
// COPYed scripts/ into the image and (2) PIPELINE_PATTERN excluded scripts/,
// so the pipeline-image job never ran and the job was never created. These
// tests pin the wiring so the job command path must exist in the image and
// changes to the scripts must retrigger the image build + job deploy.

const repoRoot = path.resolve(__dirname, '../../..')

const dockerfile = fs.readFileSync(
  path.join(repoRoot, 'platform/python-sidecar/Dockerfile.pipeline'),
  'utf8',
)
const workflow = fs.readFileSync(
  path.join(repoRoot, '.github/workflows/deploy.yml'),
  'utf8',
)

const SCRIPT_DIR = 'platform/python-sidecar/scripts/kala_gochara_cutover'
const RUNNER = `${SCRIPT_DIR}/century_run_4_1.sh`

function pipelinePattern(): RegExp {
  const m = workflow.match(/PIPELINE_PATTERN='([^']+)'/)
  if (!m) throw new Error('PIPELINE_PATTERN not found in deploy.yml')
  return new RegExp(m[1])
}

describe('Gochara century runner wiring (A2.5)', () => {
  // The dedicated brahma-gochara-century-job mounted the builder credential on
  // a second Cloud Run job, violating the one-named-build-job invariant
  // (data-plane-secret-isolation-preflight.ts) and skipping every deploy. It
  // must never come back: the builder secret/identity appear on exactly one job.
  it('deploy.yml creates no second job with the builder credential or identity', () => {
    expect(workflow).not.toContain('brahma-gochara-century-job')
    const jobDeploys = [...workflow.matchAll(/gcloud run jobs (?:deploy|update|create) ([a-z0-9-]+)[\s\S]*?--quiet/g)]
    for (const m of jobDeploys) {
      if (m[1] === 'brahma-build-pipeline-job') continue
      expect(m[0], m[1]).not.toContain('data-plane-builder-db-url')
      expect(m[0], m[1]).not.toContain('data-plane-builder-runtime@')
    }
  })

  it('the runner script is COPYed into the brahma-pipeline image', () => {
    expect(dockerfile).toContain(
      `COPY ${SCRIPT_DIR}/ ./${SCRIPT_DIR}/`,
    )
  })

  it('the runner script and its chain exist in the repo at the COPYed path', () => {
    for (const f of [
      'century_run_4_1.sh',
      'common.py',
      'step06_enumerate_episodes.py',
      'step06_candidate_build.py',
      'step06b_windows_projection.py',
    ]) {
      expect(fs.existsSync(path.join(repoRoot, SCRIPT_DIR, f)), f).toBe(true)
    }
  })

  it('PIPELINE_PATTERN covers the scripts dir, so script changes rebuild the image', () => {
    const pattern = pipelinePattern()
    expect(pattern.test(RUNNER)).toBe(true)
    expect(pattern.test(`${SCRIPT_DIR}/step06_enumerate_episodes.py`)).toBe(true)
    expect(pattern.test(`${SCRIPT_DIR}/common.py`)).toBe(true)
  })

  it('PIPELINE_PATTERN covers Dockerfile.pipeline itself, so image changes rebuild it', () => {
    expect(pipelinePattern().test('platform/python-sidecar/Dockerfile.pipeline')).toBe(true)
  })
})
