import { join, resolve } from 'node:path'

import ts from 'typescript'
import { describe, expect, it } from 'vitest'

import { inspectDbAdapter, inspectMigrationHealthPort } from './db_adapter_boundary'

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
    expect(inspectMigrationHealthPort(program, platformRoot)).toEqual([])
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
  const { program, host } = fixtureProgram(root, files)
  const adapterSource = program.getSourceFile(adapter)
  if (!adapterSource) throw new Error('Fixture adapter missing')
  return inspectDbAdapter(program, adapterSource, root, host)
}

function fixtureProgram(root: string, files: Map<string, string>) {
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
  return { program: ts.createProgram([...files.keys()], compilerOptions, host), host }
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

function migrationPortFixture(overrides: Record<string, string> = {}) {
  const root = '/migration-health-port-fixture'
  const files = new Map(Object.entries({
    'src/app/api/mcp/health/migrations/route.ts': [
      'import { readAppliedMigrationSet as applied } from "@/lib/db/migration-set"',
      'import { validateServiceToken as authorized } from "@/lib/mcp/service_token"',
      'import type { Row } from "@/lib/db/client"',
      'export async function GET() { if (!authorized()) return null; return await applied() as Row }',
    ].join('\n'),
    'src/lib/db/migration-set.ts': [
      'import { readMigrationSet as digest } from "../mcp/migration_set_digest"',
      'import { query as dbQuery, type Row } from "./client"',
      'export function readAppliedMigrationSet() { return digest(dbQuery) }',
      'export type { Row }',
    ].join('\n'),
    'src/lib/db/client.ts': 'export async function query(_sql: string) { return [] }; export type Row = string',
    'src/lib/mcp/migration_set_digest.ts':
      'export async function readMigrationSet(port: (sql: string) => Promise<unknown>) { return await port("fixture") }',
    'src/lib/unrelated.ts': 'export function readAppliedMigrationSet() { return { ok: true } }',
    'src/lib/mcp/service_token.ts': 'export function validateServiceToken() { return true }',
    'src/lib/digest-barrel.ts': 'export { readMigrationSet as port } from "./mcp/migration_set_digest"',
    ...overrides,
  }).map(([name, text]) => [join(root, name), text]))
  return inspectMigrationHealthPort(fixtureProgram(root, files).program, root)
}

describe('Migration Health uses its resolved database port', () => {
  it('allows imported aliases and a type-only export', () => {
    expect(migrationPortFixture()).toEqual([])
  })

  it.each([
    ['@/lib/unrelated', 'route must call its facade once'],
    ['@/lib/unresolved', 'unresolved local module'],
  ])('rejects a different or unresolved facade at %s', (path, problem) => {
    expect(migrationPortFixture({
      'src/app/api/mcp/health/migrations/route.ts':
        `import { readAppliedMigrationSet as applied } from "${path}"; export function GET() { return applied() }`,
    })).toContain(problem)
  })

  it.each([
    'await port("second"); return await port("first")',
    'return { port }',
    'return await port("first", port)',
    'return async () => await port("first")',
    'for (let index = 0; index < 2; index++) await port("first")',
  ])('rejects extra or escaping parameter use in %s', (body) => {
    expect(migrationPortFixture({
      'src/lib/mcp/migration_set_digest.ts':
        `export async function readMigrationSet(port: (sql: string) => Promise<unknown>) { ${body} }`,
    })).toContain('digest must call its injected query once without escape')
  })

  it('rejects the facade call in an uncalled nested function', () => {
    expect(migrationPortFixture({
      'src/app/api/mcp/health/migrations/route.ts': [
        'import { readAppliedMigrationSet as applied } from "@/lib/db/migration-set"',
        'export async function GET() { const dead = async () => await applied(); return {} }',
      ].join('\n'),
    })).toContain('route must call its facade once')
  })

  it.each([
    'import { readMigrationSet as escaped } from "@/lib/mcp/migration_set_digest"',
    'import { port as escaped } from "@/lib/digest-barrel"',
    'const escaped = (await import("@/lib/mcp/migration_set_digest")).readMigrationSet',
  ])('rejects an additional injectable reader while the correct facade call remains in %s', (imported) => {
    expect(migrationPortFixture({
      'src/app/api/mcp/health/migrations/route.ts': [
        'import { readAppliedMigrationSet as applied } from "@/lib/db/migration-set"',
        imported,
        'export async function GET() { const allowed = await applied(); await escaped(async () => []); return allowed }',
      ].join('\n'),
    })).toContain('route has an unapproved local value import')
  })

  it('rejects an unresolved digest load while the approved port remains', () => {
    expect(migrationPortFixture({
      'src/lib/mcp/migration_set_digest.ts': [
        'export async function readMigrationSet(port: (sql: string) => Promise<unknown>) {',
        '  const name = "./unknown"; await import(name); return await port("fixture")',
        '}',
      ].join('\n'),
    })).toContain('digest must call its injected query once without escape')
  })

  it.each([
    'export * as raw from "./client"',
    'import * as client from "./client"; export const exposed = client',
    'export { dbQuery as exposed }',
  ])('rejects exposing the query port in %s', (exposure) => {
    expect(migrationPortFixture({
      'src/lib/db/migration-set.ts': [
        'import { readMigrationSet as digest } from "../mcp/migration_set_digest"',
        'import { query as dbQuery } from "./client"',
        'export function readAppliedMigrationSet() { return digest(dbQuery) }',
        exposure,
      ].join('\n'),
    })).toContain('facade must inject only the canonical query')
  })

  it('rejects an additional direct query use in the facade', () => {
    expect(migrationPortFixture({
      'src/lib/db/migration-set.ts': [
        'import { readMigrationSet as digest } from "../mcp/migration_set_digest"',
        'import { query as dbQuery } from "./client"',
        'export function readAppliedMigrationSet() { return digest(dbQuery) }',
        'export const extra = dbQuery("extra")',
      ].join('\n'),
    })).toContain('facade must inject only the canonical query')
  })
})
