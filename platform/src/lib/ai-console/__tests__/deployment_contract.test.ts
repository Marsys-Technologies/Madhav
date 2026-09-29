import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repositoryRoot = resolve(__dirname, '../../../../..')
const workflow = readFileSync(resolve(repositoryRoot, '.github/workflows/deploy.yml'), 'utf8')
const dockerfile = readFileSync(resolve(repositoryRoot, 'platform/Dockerfile'), 'utf8')
const snapshotRepair = readFileSync(
  resolve(repositoryRoot, 'platform/migrations/1125_ai_snapshot_shape_operator_precedence.sql'),
  'utf8',
)
const liveProbe = readFileSync(resolve(repositoryRoot, 'platform/scripts/probe/ask.ts'), 'utf8')

describe('AI Console production deployment contract', () => {
  it('bakes the browser flag into both PR and production images', () => {
    expect(dockerfile).toContain('ARG NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK')
    expect(dockerfile).toContain('ENV NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK=$NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK')
    expect(workflow.match(/NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK=true/g)).toHaveLength(2)
  })

  it('enables the server flag and mounts a versioned credential vault only at runtime', () => {
    expect(workflow).toContain('MARSYS_FLAG_AI_CONSOLE_BYOK=true')
    expect(workflow).toContain('MARSYS_AI_ACTIVE_KEK_VERSION=V1')
    expect(workflow).toContain('MARSYS_AI_KEK_V1=marsys-ai-kek-v1:1')
    expect(workflow).toContain('MARSYS_AI_FINGERPRINT_SECRET=marsys-ai-fingerprint-secret:1')
    expect(dockerfile).not.toMatch(/MARSYS_AI_(?:KEK|FINGERPRINT)/)
  })

  it('keeps subscription-backed local CLI processes disabled on the public host', () => {
    expect(workflow).toContain('MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED=false')
    expect(workflow).not.toContain('MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED=true')
  })

  it('routes CLI calls to the private VM bridge with a versioned secret and private-only VPC egress', () => {
    expect(workflow).toContain('MARSYS_AI_CLI_BRIDGE_URL=http://10.160.0.2:8787')
    expect(workflow).toContain('MARSYS_AI_CLI_BRIDGE_TOKEN=marsys-ai-cli-bridge-token:1')
    expect(workflow).toContain('--network=default')
    expect(workflow).toContain('--subnet=default')
    expect(workflow).toContain('--network-tags=amjis-web-cli-egress')
    expect(workflow).toContain('--vpc-egress=private-ranges-only')
  })

  it('applies AI Console schema functions only through the protected migration window', () => {
    expect(snapshotRepair).toContain('CREATE OR REPLACE FUNCTION ai_snapshot_shape')
    expect(workflow).toContain('migrations+=(1124_ai_console_byok_routing.sql)')
    expect(workflow).toContain('migrations+=(1125_ai_snapshot_shape_operator_precedence.sql)')
    expect(workflow).toContain('migrations+=(1151_ai_console_model_shortlist.sql)')
  })

  it('keeps the standing Pariprashna probe on the mandatory account default', () => {
    expect(liveProbe).toContain("ai_selection: { kind: 'default' }")
  })
})
