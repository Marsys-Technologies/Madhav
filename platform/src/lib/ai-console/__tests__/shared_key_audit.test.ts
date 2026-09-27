import { mkdtemp, mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import {
  auditImportGraph,
  defaultImportAuditConfig,
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
      { ruleId: 'AIC_SHARED_PROVIDER_ENV' },
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

  it('includes credential replacement PATCH and every validation/revalidation entry root', () => {
    expect(defaultImportAuditConfig('/platform').roots).toEqual(expect.arrayContaining([
      'src/app/api/ai-console/connections/route.ts',
      'src/app/api/ai-console/connections/[id]/route.ts',
      'src/app/api/ai-console/connections/[id]/validate/route.ts',
      'src/app/api/admin/cron/revalidate-ai-connections/route.ts',
    ]))
  })

  it('traverses static require and TypeScript import-equals edges', async () => {
    const root = await fixture({
      'src/root.ts': "const one = require('./one'); import two = require('./two'); export { one, two }\n",
      'src/one.ts': "export { read } from './lib/models/runtime_config'\n",
      'src/two.ts': 'export const two = true\n',
      'src/lib/models/runtime_config.ts': 'export const read = true\n',
    })
    const result = await auditImportGraph(config(root))
    expect(result.scannerErrors).toEqual([])
    expect(result.violations).toContainEqual({
      ruleId: 'AIC_LEGACY_MODEL_AUTHORITY',
      chain: ['src/root.ts', 'src/one.ts', 'src/lib/models/runtime_config.ts'],
    })
  })

  it('detects provider environment destructuring, aliases, and static computed access', async () => {
    const root = await fixture({
      'src/root.ts': "import './destructure'; import './alias'; import './computed'\n",
      'src/destructure.ts': 'const { OPENAI_API_KEY: key } = process.env; export { key }\n',
      'src/alias.ts': 'const env = process.env; export const key = env.OPENAI_API_KEY\n',
      'src/computed.ts': "const name = 'OPENAI_API_KEY'; export const key = process.env[name]\n",
    })
    const result = await auditImportGraph(config(root))
    expect(result.violations.filter(row => row.ruleId === 'AIC_SHARED_PROVIDER_ENV')).toHaveLength(3)
  })

  it('derives every legacy provider key and implicit sink from one guarded registry', async () => {
    const keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_GENERATIVE_AI_API_KEY', 'DEEPSEEK_API_KEY',
      'NVIDIA_NIM_API_KEY', 'XAI_API_KEY', 'KIMI_API_KEY', 'MOONSHOT_API_KEY', 'OPENROUTER_API_KEY']
    const files = Object.fromEntries(keys.map((key, index) => [`src/key-${index}.ts`, `export const value = process.env.${key}\n`]))
    const root = await fixture({
      'src/root.ts': keys.map((_, index) => `import './key-${index}'`).join('\n')
        + "\nimport './lib/providers/nvidia/adapter'\n",
      'src/lib/providers/nvidia/adapter.ts': 'export const sharedSingleton = true\n',
      ...files,
    })
    const defaults = defaultImportAuditConfig(root)
    const result = await auditImportGraph({ ...defaults, roots: ['src/root.ts'] })
    expect(result.scannerErrors).toEqual([])
    expect(result.violations.filter(row => row.ruleId === 'AIC_SHARED_PROVIDER_ENV')).toHaveLength(keys.length)
    expect(result.violations).toContainEqual({
      ruleId: 'AIC_LEGACY_PROVIDER_SINK',
      chain: ['src/root.ts', 'src/lib/providers/nvidia/adapter.ts'],
    })
  })

  it('propagates process and environment taint through wrappers, assignments, defaults, and computed aliases', async () => {
    const root = await fixture({
      'src/root.ts': [
        'const ENV = ("env" as const); const KEY = ("NVIDIA_" + "NIM_API_KEY") as const;',
        'let p, e; p = (process); e = (p.env as NodeJS.ProcessEnv); const one = e[KEY];',
        'const { env: other } = process; const two = other.OPENAI_API_KEY;',
        'function read(from = process.env) { return from["ANTHROPIC_API_KEY"] }',
        'function readProcess(proc = process) { return proc[ENV].DEEPSEEK_API_KEY }',
        'export { one, two, read, readProcess }',
      ].join('\n'),
    })
    const result = await auditImportGraph(config(root))
    expect(result.violations).toEqual([{ ruleId: 'AIC_SHARED_PROVIDER_ENV', chain: ['src/root.ts'] }])
    expect(result.scannerErrors).toEqual([])
  })

  it('fails closed on a dynamic key read from a tainted environment', async () => {
    const root = await fixture({ 'src/root.ts': 'const e = process.env; export const value = e[getCredentialName()]\n' })
    const result = await auditImportGraph(config(root))
    expect(result.scannerErrors).toEqual([{
      ruleId: 'AIC_PROVIDER_ENV_UNSUPPORTED', chain: ['src/root.ts', 'dynamic-environment-key'],
    }])
  })

  it('traverses createRequire and module.require aliases and fails closed on dynamic loader calls', async () => {
    const root = await fixture({
      'src/root.ts': [
        "import { createRequire as make } from 'node:module';",
        'const load = make(import.meta.url);',
        "load('./one'); module['require']('./two');",
        "const direct = require; direct('./three');",
        'const bound = module.require.bind(module); bound(target);',
      ].join('\n'),
      'src/one.ts': "export { read } from './lib/models/runtime_config'\n",
      'src/two.ts': 'export const value = true\n',
      'src/three.ts': 'export const value = process.env.NVIDIA_NIM_API_KEY\n',
      'src/lib/models/runtime_config.ts': 'export const read = true\n',
    })
    const result = await auditImportGraph(config(root))
    expect(result.violations).toContainEqual({
      ruleId: 'AIC_LEGACY_MODEL_AUTHORITY',
      chain: ['src/root.ts', 'src/one.ts', 'src/lib/models/runtime_config.ts'],
    })
    expect(result.scannerErrors).toContainEqual({
      ruleId: 'AIC_IMPORT_UNSUPPORTED', chain: ['src/root.ts', 'dynamic-require'],
    })
    expect(result.violations).toContainEqual({
      ruleId: 'AIC_SHARED_PROVIDER_ENV', chain: ['src/root.ts', 'src/three.ts'],
    })
  })

  it('fails closed on unsupported dynamic internal import edges', async () => {
    const root = await fixture({ 'src/root.ts': "const target = './internal'; void import(target)\n" })
    const result = await auditImportGraph(config(root))
    expect(result.scannerErrors).toEqual([{
      ruleId: 'AIC_IMPORT_UNSUPPORTED', chain: ['src/root.ts', 'dynamic-import'],
    }])
  })
})
