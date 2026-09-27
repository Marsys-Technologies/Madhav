import { mkdtemp, mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import {
  auditImportGraph,
  type ImportAuditConfig,
} from '../../../../scripts/ai-console/shared_key_route_audit'

const scratch: string[] = []

async function fixture(files: Record<string, string>): Promise<string> {
  const root = await mkdtemp(join(tmpdir(), 'ai-console-route-audit-'))
  scratch.push(root)
  await Promise.all(Object.entries(files).map(async ([path, source]) => {
    const target = join(root, path)
    await mkdir(join(target, '..'), { recursive: true })
    await writeFile(target, source)
  }))
  return root
}

function config(root: string, roots = ['src/root.ts']): ImportAuditConfig {
  return {
    platformRoot: root,
    roots,
    forbidden: [
      { ruleId: 'AIC_SHARED_PROVIDER_ENV', sourcePatterns: [/process\.env\.OPENAI_API_KEY/] },
      { ruleId: 'AIC_LEGACY_MODEL_AUTHORITY', paths: ['src/lib/models/runtime_config.ts'] },
    ],
  }
}

afterEach(async () => {
  const { rm } = await import('node:fs/promises')
  await Promise.all(scratch.splice(0).map(path => rm(path, { recursive: true, force: true })))
})

describe('AI Console shared-key route import audit', () => {
  it('passes a clean graph while resolving relative, alias, export, and literal dynamic edges through cycles', async () => {
    const root = await fixture({
      'src/root.ts': "import './relative'; export { clean } from '@/lib/clean'; void import('./lazy')\n",
      'src/relative.ts': "import '@/lib/clean'\n",
      'src/lazy/index.ts': "import '../relative'\n",
      'src/lib/clean.ts': "import '../relative'\nexport const clean = true\n",
    })

    const result = await auditImportGraph(config(root))

    expect(result).toEqual({ violations: [], scannerErrors: [], visitedFiles: 4 })
  })

  it('reports only the rule and repository-relative shortest chain to a forbidden sink', async () => {
    const root = await fixture({
      'src/root.ts': "import { route } from '@/route'\n",
      'src/route.ts': "export { read } from './lib/models/runtime_config'\n",
      'src/lib/models/runtime_config.ts': 'export const read = () => process.env.OPENAI_API_KEY\n',
    })

    const result = await auditImportGraph(config(root))

    expect(result.scannerErrors).toEqual([])
    expect(result.violations).toEqual([
      {
        ruleId: 'AIC_LEGACY_MODEL_AUTHORITY',
        chain: ['src/root.ts', 'src/route.ts', 'src/lib/models/runtime_config.ts'],
      },
      {
        ruleId: 'AIC_SHARED_PROVIDER_ENV',
        chain: ['src/root.ts', 'src/route.ts', 'src/lib/models/runtime_config.ts'],
      },
    ])
    expect(JSON.stringify(result)).not.toContain('OPENAI_API_KEY')
  })

  it('fails closed when a local or alias edge cannot be resolved', async () => {
    const root = await fixture({ 'src/root.ts': "import '@/missing/internal'\n" })

    const result = await auditImportGraph(config(root))

    expect(result.violations).toEqual([])
    expect(result.scannerErrors).toEqual([{
      ruleId: 'AIC_IMPORT_UNRESOLVED',
      chain: ['src/root.ts', 'src/missing/internal'],
    }])
  })

  it('does not treat external package imports or import-like comments as graph edges', async () => {
    const root = await fixture({
      'src/root.ts': "import { z } from 'zod'\n// import '@/missing/comment'\nconst text = \"import('@/missing/string')\"\nexport { z, text }\n",
    })

    await expect(auditImportGraph(config(root))).resolves.toMatchObject({
      violations: [], scannerErrors: [], visitedFiles: 1,
    })
  })
})
