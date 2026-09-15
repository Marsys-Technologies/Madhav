import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const bridgeSource = readFileSync(resolve(__dirname, 'prashna_ask_bridge.ts'), 'utf8')
const storeSource = readFileSync(resolve(__dirname, 'managed_prashna_jobs.ts'), 'utf8')
const deployWorkflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
const authorityPacket = readFileSync(resolve(
  __dirname,
  '../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/W7_COMPLETION_AUTHORITY_PACKET_v1.json',
), 'utf8')

describe('managed Prashna worker deadline hierarchy', () => {
  it('preserves source-local budgets while fencing deployment settings behind external authority', () => {
    expect(bridgeSource).toContain('const ENGINE_CALL_TIMEOUT_MS = 330_000')
    expect(storeSource).toContain('lease_seconds: 450')
    expect(deployWorkflow).not.toContain('--timeout=360s')
    expect(deployWorkflow).not.toContain('--no-cpu-throttling')
    expect(authorityPacket).toContain('amjis-web request timeout 360 seconds')
    expect(authorityPacket).toContain('amjis-mcp request timeout 360 seconds and instance-based CPU')
    expect(authorityPacket).toContain('NOT_RUN')
  })

  it('bounds post-response worker concurrency and lets status polls resubmit recovery', () => {
    const askTool = readFileSync(resolve(__dirname, '../tools/register_prashna_ask.ts'), 'utf8')
    const statusTool = readFileSync(resolve(__dirname, '../tools/register_prashna_status.ts'), 'utf8')
    expect(askTool).toContain('MAX_ACTIVE_MANAGED_PRASHNA_WORKERS = 2')
    expect(askTool).toContain('MAX_QUEUED_MANAGED_PRASHNA_JOBS = 32')
    expect(statusTool).toContain('scheduleManagedPrashnaJob(job.job_id, principal)')
    expect(askTool).toContain('retry waits for lease expiry')
    expect(askTool).not.toContain('setTimeout(() => scheduleManagedPrashnaJob')
  })

  it('derives OAuth credential identity from the full token hash, never a token prefix', () => {
    const serverSource = readFileSync(resolve(__dirname, '../server.ts'), 'utf8')
    expect(serverSource).toContain("'oauth_sha256:' + createHash('sha256').update(token).digest('hex')")
    expect(serverSource).not.toContain("'oauth:' + token.slice")
  })

  it('bounds engine response bytes before buffering a full terminal line', () => {
    expect(bridgeSource).toContain('const MAX_ENGINE_RESPONSE_BYTES = 2 * 1024 * 1024')
    expect(bridgeSource).toContain('receivedBytes += value.byteLength')
    expect(bridgeSource).toContain("'storage_contract'")
  })
})
