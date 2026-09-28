import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repositoryRoot = resolve(__dirname, '../../../../..')
const workflow = readFileSync(resolve(repositoryRoot, '.github/workflows/deploy.yml'), 'utf8')
const dockerfile = readFileSync(resolve(repositoryRoot, 'platform/Dockerfile'), 'utf8')

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
})
