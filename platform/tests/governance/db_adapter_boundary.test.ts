import { join, resolve } from 'node:path'

import ts from 'typescript'
import { describe, expect, it } from 'vitest'

import { inspectDbAdapter } from './db_adapter_boundary'

const platformRoot = resolve(__dirname, '../..')
const closedAdapters = [
  'src/app/clients/[id]/page.tsx',
  'src/app/api/mcp/health/migrations/route.ts',
  'src/app/api/classical-texts/[text_key]/summary/route.ts',
  'src/app/api/build/data-readiness/route.ts',
]

describe('database capability stays inside its owner', () => {
  it('keeps the scoped adapters free of raw database imports and SQL', () => {
    const config = ts.readConfigFile(join(platformRoot, 'tsconfig.json'), ts.sys.readFile)
    expect(config.error).toBeUndefined()
    const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, platformRoot)
    expect(parsed.errors).toEqual([])
    const files = closedAdapters.map((file) => join(platformRoot, file))
    const program = ts.createProgram(files, { ...parsed.options, noLib: true, types: [] })
    for (const file of files) {
      const adapter = program.getSourceFile(file)
      if (!adapter) throw new Error(`Closed adapter missing: ${file}`)
      expect(inspectDbAdapter(program, adapter, platformRoot), file).toEqual([])
    }
  })
})

function fixture(source: string) {
  const root = '/boundary-fixture'
  const adapter = `${root}/src/app/route.ts`
  const files = new Map(Object.entries({
    [adapter]: source,
    [`${root}/src/lib/db/client.ts`]: 'export const query = () => 1; export type Row = number',
    [`${root}/src/lib/owner.ts`]: 'import { query } from "@/lib/db/client"; export const summary = () => query()',
    [`${root}/src/lib/barrel.ts`]: 'export { query as raw, type Row } from "@/lib/db/client"; export { summary } from "./owner"',
    [`${root}/src/lib/second.ts`]: 'export { raw as twice, summary } from "./barrel"',
    [`${root}/src/lib/value-alias.ts`]: 'import * as driver from "./db/client"; export const assigned = driver.query',
    [`${root}/src/lib/namespaced.ts`]: 'export * as exposed from "./second"; export * as owner from "./owner"',
    [`${root}/src/lib/type-barrel.ts`]: 'export type { query } from "./db/client"',
    [`${root}/src/lib/storage/index.ts`]: 'export function getStorageClient() { return {} }; export type StorageClient = object',
  }))
  const compilerOptions: ts.CompilerOptions = {
    module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    paths: { '@/*': [`${root}/src/*`] },
    noLib: true,
    types: [],
  }
  const host: ts.CompilerHost = {
    ...ts.createCompilerHost(compilerOptions),
    fileExists: (name) => files.has(name),
    readFile: (name) => files.get(name),
    directoryExists: (name) => [...files.keys()].some((file) => file.startsWith(`${name}/`)),
    getSourceFile: (name, version) => {
      const contents = files.get(name)
      return contents === undefined ? undefined : ts.createSourceFile(name, contents, version, true)
    },
  }
  const program = ts.createProgram([...files.keys()], compilerOptions, host)
  const adapterSource = program.getSourceFile(adapter)
  if (!adapterSource) throw new Error('Fixture adapter missing')
  return inspectDbAdapter(program, adapterSource, root, host)
}

describe('boundary detector fixtures', () => {
  it.each([
    'import { query as renamed } from "@/lib/db/client"',
    'import * as driver from "../lib/db/client"',
    'import { twice as renamed } from "@/lib/second"',
    'import { assigned } from "@/lib/value-alias"',
    'import { exposed } from "@/lib/namespaced"; exposed.twice()',
    'import { getStorageClient as storage } from "../lib/storage"',
    'export { query as leaked } from "../lib/db/client"',
    'export * from "../lib/second"',
    'const { query } = await import("../lib/db/client")',
    'const { twice } = await import("../lib/second")',
    'const { query } = require("../lib/db/client")',
    'const { twice } = require("../lib/second")',
    'import { Pool } from "pg"',
  ])('rejects a raw value edge in %s', (source) => {
    expect(fixture(source)).toEqual([expect.objectContaining({ line: 1, kind: 'raw database import' })])
  })

  it('rejects computed loading and adapter-authored SQL', () => {
    expect(fixture('const path = "./target"; await import(path); const sql = "SELECT name FROM things"'))
      .toEqual([
        expect.objectContaining({ kind: 'unresolved module load' }),
        expect.objectContaining({ kind: 'adapter SQL' }),
      ])
  })

  it('fails when a runtime load cannot be resolved', () => {
    expect(fixture('await import("./missing")')).toEqual([
      expect.objectContaining({ kind: 'unresolved module load' }),
    ])
  })

  it('rejects interpolated adapter SQL', () => {
    expect(fixture('const col = "name"; const sql = `SELECT ${col} FROM things`')).toEqual([
      expect.objectContaining({ kind: 'adapter SQL' }),
    ])
  })

  it('allows scoped facades and type-only references without following the facade into its implementation', () => {
    expect(fixture([
      'import { summary } from "@/lib/second"',
      'import { owner } from "@/lib/namespaced"',
      'import * as onlyTypes from "@/lib/type-barrel"',
      'import type { Row } from "../lib/db/client"',
      'import { type Pool } from "pg"',
      'export type { Row } from "../lib/barrel"',
      'export const result: Row = summary()',
    ].join('\n'))).toEqual([])
  })
})
