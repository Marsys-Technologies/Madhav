import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

// Pravāha A2.5's runner remains packaged in the pipeline image, but the
// separate century job must not be deployed by the routine pipeline: it
// cannot share the one named build job's credential/identity (DP-SD-020).
// The Gochara lane must provision an independent approved credential boundary
// before restoring its job in a separately governed operation.

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

describe('Gochara century runner packaging and isolation (A2.5)', () => {
  it('keeps the runner in the image without deploying the job', () => {
    expect(workflow).not.toContain('gcloud run jobs deploy brahma-gochara-century-job')
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
