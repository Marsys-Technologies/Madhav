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
const mcpDeployJob = deployWorkflow.split('\n  deploy-mcp:')[1]?.split('\n  deploy-pipeline-job:')[0] ?? ''
const watchdogProvisioner = readFileSync(resolve(
  __dirname,
  '../../../platform/scripts/provision_watchdog_scheduler.sh',
), 'utf8')

describe('managed Prashna worker deadline hierarchy', () => {
  it('preserves the worker hierarchy in the reviewed Cloud Run runtime contract', () => {
    expect(bridgeSource).toContain('const ENGINE_CALL_TIMEOUT_MS = 330_000')
    expect(storeSource).toContain('lease_seconds: 450')
    expect(deployWorkflow).toContain('--timeout=360s')
    expect(deployWorkflow).toContain('--no-cpu-throttling')
    expect(deployWorkflow).toContain('INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID=inquiry-v1')
    expect(deployWorkflow).toContain(
      'INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT=inquiry-lifecycle-signing-key:1',
    )
    expect(deployWorkflow).toContain('Wait for matching web revision and inquiry routes')
    expect(deployWorkflow).toContain('traffic_sha" = "$DEPLOY_SHA')
    expect(deployWorkflow).toContain('/api/mcp/inquiry')
    expect(deployWorkflow).toContain('/api/mcp/prashna_jobs')
    expect(deployWorkflow).toContain('refusing MCP traffic promotion')
    expect(deployWorkflow).toContain('DB_INQUIRY_USER=amjis_inquiry_serve')
    expect(deployWorkflow).toContain('DB_INQUIRY_PASSWORD=amjis-inquiry-db-password:1')
    expect(deployWorkflow).toContain('Pūrṇa inquiry signing and RLS candidate canary')
    expect(deployWorkflow).toContain('/api/mcp/inquiry/readiness')
    expect(deployWorkflow).toContain('PURNA_READINESS_CANARY_KEY_ID=mcp_prod_tDO7obNw')
    expect(deployWorkflow).toContain('.database.cross_principal_rows == 0')
    expect(deployWorkflow).toContain('refusing traffic promotion')
    expect(deployWorkflow).toContain('WATCHDOG_LEGACY_FALLBACK_ENABLED=true')
    expect(deployWorkflow).toContain('WATCHDOG_SECRET=watchdog-secret:1')
    expect(deployWorkflow).toContain('Transitional bridge only')
    expect(deployWorkflow).toContain('WATCHDOG_SCHEDULER_SERVICE_ACCOUNT=amjis-scheduler@')
    expect(watchdogProvisioner).toContain('--oidc-service-account-email="$SCHEDULER_SERVICE_ACCOUNT"')
    expect(watchdogProvisioner).toContain('--oidc-token-audience="$OIDC_AUDIENCE"')
    expect(watchdogProvisioner).toContain('--clear-headers')
    expect(watchdogProvisioner).not.toContain('x-watchdog-auth')
    expect(watchdogProvisioner).not.toContain('watchdog-secret')
    expect(mcpDeployJob).toContain('--remove-secrets=MCP_CANARY_KEY')
    expect(mcpDeployJob).not.toContain('MCP_CANARY_KEY=mcp-canary-key:latest')
    expect(mcpDeployJob).toContain('Prove MCP runtime OIDC and shared-token path')
    expect(mcpDeployJob).toContain('name:"prashna_status"')
    expect(mcpDeployJob).not.toContain('it does\n      # NOT have')
    expect(authorityPacket).toContain('amjis-web request timeout 360 seconds')
    expect(authorityPacket).toContain('amjis-mcp request timeout 360 seconds and instance-based CPU')
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
