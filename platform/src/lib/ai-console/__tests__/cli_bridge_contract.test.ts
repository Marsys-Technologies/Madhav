import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repositoryRoot = resolve(__dirname, '../../../../..')
const bridge = readFileSync(resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/server.mjs'), 'utf8')
const service = readFileSync(
  resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/marsys-ai-cli-bridge.service'),
  'utf8',
)

describe('private AI CLI bridge contract', () => {
  it('allows only fixed operations and executable paths', () => {
    expect(bridge).toContain("['inspect', 'confirm', 'version', 'auth', 'catalog', 'probe', 'execute']")
    expect(bridge).toContain("path: join(HOME, '.local/bin/codex')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/claude')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/agy')")
    expect(bridge).toContain("path: join(HOME, '.kimi-code/bin/kimi')")
    expect(bridge).not.toMatch(/raw\.(?:args|command|executable)/)
    expect(bridge).not.toContain('shell: true')
    expect(bridge.match(/return await runCommand/g)).toHaveLength(3)
    expect(bridge).toContain('return await runKimiAcp')
  })

  it('requires a file-backed bearer token and constant-time comparison', () => {
    expect(bridge).toContain("if (!TOKEN_FILE) throw new Error('MARSYS_AI_CLI_BRIDGE_TOKEN_FILE is required')")
    expect(bridge).toContain('timingSafeEqual(supplied, expected)')
    expect(bridge).toContain("response.setHeader('Cache-Control', 'no-store')")
  })

  it('runs as the non-root CLI owner with basic systemd isolation', () => {
    expect(service).toContain('User=mail_abhisek_mohanty_gmail_com')
    expect(service).toContain('NoNewPrivileges=true')
    expect(service).toContain('PrivateTmp=true')
    expect(service).toContain('ProtectSystem=strict')
    expect(service).toContain('MARSYS_AI_CLI_BRIDGE_HOST=10.160.0.2')
  })
})
