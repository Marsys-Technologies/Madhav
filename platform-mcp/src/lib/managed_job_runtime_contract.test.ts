import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const bridgeSource = readFileSync(resolve(__dirname, 'prashna_ask_bridge.ts'), 'utf8')
const storeSource = readFileSync(resolve(__dirname, 'managed_prashna_jobs.ts'), 'utf8')
const deployWorkflow = readFileSync(resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')

describe('managed Prashna worker deadline hierarchy', () => {
  it('preserves the planner budget and reserves time before web timeout and lease expiry', () => {
    expect(bridgeSource).toContain('const ENGINE_CALL_TIMEOUT_MS = 330_000')
    expect(storeSource).toContain('lease_seconds: 450')

    const webDeploy = deployWorkflow.match(
      /service: amjis-web[\s\S]*?flags: >-([\s\S]*?)env_vars:/,
    )?.[1]
    const mcpDeploy = deployWorkflow.match(
      /service: amjis-mcp[\s\S]*?flags: ([^\n]+)/,
    )?.[1]
    expect(webDeploy).toContain('--timeout=360s')
    expect(mcpDeploy).toContain('--timeout=360s')
    expect(mcpDeploy).toContain('--no-cpu-throttling')
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
