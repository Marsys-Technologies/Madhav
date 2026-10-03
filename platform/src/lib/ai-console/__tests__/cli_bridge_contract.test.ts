import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repositoryRoot = resolve(__dirname, '../../../../..')
const bridge = readFileSync(resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/server.mjs'), 'utf8')
const smoke = readFileSync(resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/smoke.mjs'), 'utf8')
const service = readFileSync(
  resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/marsys-ai-cli-bridge.service'),
  'utf8',
)

describe('private AI CLI bridge contract', () => {
  it('allows only fixed operations and executable paths', () => {
    expect(bridge).toContain("['inspect', 'confirm', 'version', 'auth', 'catalog', 'probe', 'probe_model', 'execute']")
    expect(bridge).toContain("path: join(HOME, '.local/bin/codex')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/claude')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/agy')")
    expect(bridge).toContain("versions: ['1.2.12', '1.2.13', '1.2.15']")
    expect(bridge).toContain('definition.versions.includes(payload.version)')
    expect(bridge).toContain("path: join(HOME, '.kimi-code/bin/kimi')")
    expect(bridge).not.toMatch(/raw\.(?:args|command|executable)/)
    expect(bridge).not.toContain('shell: true')
    expect(bridge.match(/return await runCommand/g)).toHaveLength(3)
    expect(bridge).toContain('return await runKimiAcp')
  })

  it('limits execution effort to known CLI model IDs and fixed arguments', () => {
    expect(bridge).toContain('const SAFE_EFFORT = /^[a-z][a-z0-9_]{0,31}$/')
    expect(bridge).toContain('models.get(modelId)?.includes(effort)')
    expect(bridge).toContain("if (effort) args.push('-c', `model_reasoning_effort=${effort}`)")
    expect(bridge).toContain("if (effort) args.push('--effort', effort)")
    expect(bridge).toContain("!['codex', 'claude_code'].includes(cliId)")
  })

  it('requires a file-backed bearer token and constant-time comparison', () => {
    expect(bridge).toContain("if (!TOKEN_FILE) throw new Error('MARSYS_AI_CLI_BRIDGE_TOKEN_FILE is required')")
    expect(bridge).toContain('timingSafeEqual(supplied, expected)')
    expect(bridge).toContain("response.setHeader('Cache-Control', 'no-store')")
  })

  it('smoke-tests every supported Antigravity version and confirms the detected one', () => {
    expect(smoke).toContain("versions: ['1.2.12', '1.2.13', '1.2.15']")
    expect(smoke).toContain('version: acceptedVersion')
  })

  it('runs as the non-root CLI owner with basic systemd isolation', () => {
    expect(service).toContain('User=mail_abhisek_mohanty_gmail_com')
    expect(service).toContain('NoNewPrivileges=true')
    expect(service).toContain('PrivateTmp=true')
    expect(service).toContain('ProtectSystem=strict')
    expect(service).toContain('MARSYS_AI_CLI_BRIDGE_HOST=10.160.0.2')
  })
})
