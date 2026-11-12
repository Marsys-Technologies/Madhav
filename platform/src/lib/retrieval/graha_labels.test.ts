/**
 * graha_labels.test.ts — Unit tests for the client-safe graha label/code vocabulary
 * extracted from address_resolver.ts (ADHIṢṬHĀNA build-break fix, 2026-08-08).
 *
 * The pure owner and compatibility vocabulary load with zero I/O. The resolver
 * compatibility identity check uses a refusing database double:
 * it must be importable from a 'use client' component without pulling in
 * `server-only`. These tests both lock in grahaCodeOf()/GRAHA_CODE_TO_NAME's exact
 * prior behavior (unchanged by the move) and stand as a regression guard against
 * this module ever growing a `@/lib/db/client` import again.
 */

import { describe, it, expect, vi } from 'vitest'
import { AddressResolutionError, GRAHA_CODE_TO_NAME, grahaCodeOf } from './graha_labels'
import * as fs from 'node:fs'
import * as path from 'node:path'
import * as ts from 'typescript'
import * as owner from '../brahmagyan/grahaIdentity'
import * as compatibility from './graha_labels'
import semanticRelease from '../../../python-sidecar/brahmagyan/l0_semantic_release_v1.json'

describe('GRAHA_CODE_TO_NAME', () => {
  it('maps every canonical fact_subject code to its classical graha name', () => {
    expect(GRAHA_CODE_TO_NAME.SUN).toBe('Sun')
    expect(GRAHA_CODE_TO_NAME.MOON).toBe('Moon')
    expect(GRAHA_CODE_TO_NAME.MAR).toBe('Mars')
    expect(GRAHA_CODE_TO_NAME.MER).toBe('Mercury')
    expect(GRAHA_CODE_TO_NAME.JUP).toBe('Jupiter')
    expect(GRAHA_CODE_TO_NAME.VEN).toBe('Venus')
    expect(GRAHA_CODE_TO_NAME.SAT).toBe('Saturn')
    expect(GRAHA_CODE_TO_NAME.RAH_MEAN).toBe('Rahu')
    expect(GRAHA_CODE_TO_NAME.KET_MEAN).toBe('Ketu')
  })
})

describe('grahaCodeOf', () => {
  it('normalizes canonical short codes (case-insensitive)', () => {
    expect(grahaCodeOf('SUN')).toBe('SUN')
    expect(grahaCodeOf('sun')).toBe('SUN')
    expect(grahaCodeOf('RAH_MEAN')).toBe('RAH_MEAN')
  })

  it('normalizes English long-form names', () => {
    expect(grahaCodeOf('Saturn')).toBe('SAT')
    expect(grahaCodeOf('Mars')).toBe('MAR')
    expect(grahaCodeOf('Rahu')).toBe('RAH_MEAN')
    expect(grahaCodeOf('Ketu')).toBe('KET_MEAN')
  })

  it('normalizes 2-letter shorthand aliases', () => {
    expect(grahaCodeOf('su')).toBe('SUN')
    expect(grahaCodeOf('ma')).toBe('MAR')
    expect(grahaCodeOf('ra')).toBe('RAH_MEAN')
    expect(grahaCodeOf('ke')).toBe('KET_MEAN')
  })

  it('normalizes bare "rah"/"ket" (Lane A2 cross-language parity aliases)', () => {
    expect(grahaCodeOf('rah')).toBe('RAH_MEAN')
    expect(grahaCodeOf('ket')).toBe('KET_MEAN')
  })

  it('normalizes classical Sanskrit names', () => {
    expect(grahaCodeOf('shani')).toBe('SAT')
    expect(grahaCodeOf('surya')).toBe('SUN')
    expect(grahaCodeOf('chandra')).toBe('MOON')
    expect(grahaCodeOf('guru')).toBe('JUP')
    expect(grahaCodeOf('brihaspati')).toBe('JUP')
    expect(grahaCodeOf('shukra')).toBe('VEN')
    expect(grahaCodeOf('mangala')).toBe('MAR')
    expect(grahaCodeOf('kuja')).toBe('MAR')
    expect(grahaCodeOf('budha')).toBe('MER')
  })

  it('round-trips grahaCodeOf -> GRAHA_CODE_TO_NAME for every canonical name', () => {
    for (const name of Object.values(GRAHA_CODE_TO_NAME)) {
      expect(GRAHA_CODE_TO_NAME[grahaCodeOf(name)]).toBe(name)
    }
  })

  it('throws AddressResolutionError on an unrecognized name (B.10 — no silent fallback)', () => {
    expect(() => grahaCodeOf('Pluto')).toThrow(AddressResolutionError)
    expect(() => grahaCodeOf('not-a-graha')).toThrow(AddressResolutionError)
  })
})

const ownerPath = path.resolve(__dirname, '../brahmagyan/grahaIdentity.ts')
const compatibilityPath = path.join(__dirname, 'graha_labels.ts')
const semanticImport = '../../../python-sidecar/brahmagyan/l0_semantic_release_v1.json'
const compatibilityNames = [
  'AddressResolutionError', 'AmbiguousAddressResolutionError', 'GRAHA_CODE_TO_NAME',
  'L0_SEMANTIC_RELEASE_ID', 'L0_SEMANTIC_RELEASE_DIGEST', 'grahaCodeOf', 'grahaIdentityOf',
].sort()

function moduleDependencies(file: string, source: string): string[] {
  const parsed = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true)
  const dependencies: string[] = []
  function visit(node: ts.Node) {
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
      if (node.moduleSpecifier) {
        expect(ts.isStringLiteral(node.moduleSpecifier)).toBe(true)
        dependencies.push((node.moduleSpecifier as ts.StringLiteral).text)
      }
    }
    if (ts.isImportEqualsDeclaration(node)
      || (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword
        || (ts.isIdentifier(node.expression) && node.expression.text === 'require')))) {
      throw new Error('Graha owner dependency must use its explicit JSON import')
    }
    ts.forEachChild(node, visit)
  }
  visit(parsed)
  return dependencies
}

function assertGrahaDependencyClosure(ownerSource: string, compatibilitySource: string) {
  expect(moduleDependencies(ownerPath, ownerSource)).toEqual([semanticImport])
  expect(moduleDependencies(compatibilityPath, compatibilitySource)).toEqual(['../brahmagyan/grahaIdentity'])
  const facade = ts.createSourceFile(compatibilityPath, compatibilitySource, ts.ScriptTarget.Latest, true)
  expect(facade.statements).toHaveLength(1)
  const statement = facade.statements[0]
  expect(ts.isExportDeclaration(statement)).toBe(true)
  const exports = (statement as ts.ExportDeclaration).exportClause
  expect(exports && ts.isNamedExports(exports)).toBe(true)
  expect((exports as ts.NamedExports).elements.map(element => element.name.text).sort()).toEqual(compatibilityNames)
}

describe('Brahmagyan Graha ownership and client-safe dependency closure', () => {
  it('loads the actual implementation owner and preserves every compatibility object', () => {
    expect(Object.keys(compatibility).sort()).toEqual(compatibilityNames)
    for (const name of compatibilityNames) {
      expect(compatibility[name as keyof typeof compatibility]).toBe(owner[name as keyof typeof owner])
    }
    expect(compatibility.grahaIdentityOf('Sun')).toBe(owner.grahaIdentityOf('Sun'))
    expect(owner.L0_SEMANTIC_RELEASE_ID).toBe(semanticRelease.semantic_release_id)
    expect(owner.L0_SEMANTIC_RELEASE_DIGEST).toBe(semanticRelease.content_sha256)
    expect(owner.grahaIdentityOf('Sun')).toBe(semanticRelease.entities.find(entity => entity.canonical_subject_code === 'SUN'))
  })

  it('retains the resolver compatibility identities while refusing any database work', async () => {
    const query = vi.fn(() => { throw new Error('database access is outside this identity test') })
    vi.doMock('@/lib/db/client', () => ({ query }))
    try {
      const resolver = await import('./address_resolver')
      expect(resolver.AddressResolutionError).toBe(owner.AddressResolutionError)
      expect(resolver.GRAHA_CODE_TO_NAME).toBe(owner.GRAHA_CODE_TO_NAME)
      expect(resolver.grahaCodeOf).toBe(owner.grahaCodeOf)
      expect(query).not.toHaveBeenCalled()
    } finally {
      vi.doUnmock('@/lib/db/client')
    }
  })

  it('checks the actual owner dependency and the explicit compatibility export', () => {
    assertGrahaDependencyClosure(
      fs.readFileSync(ownerPath, 'utf8'), fs.readFileSync(compatibilityPath, 'utf8'),
    )
    expect(path.resolve(path.dirname(ownerPath), semanticImport)).toBe(
      path.resolve(__dirname, semanticImport),
    )
  })

  it.each([
    "import 'server-only'",
    "import { query } from '@/lib/db/client'",
    "export * from './serverBridge'",
    "const dependency = require('node:fs')",
    "const dependency = import('@/lib/db/client')",
  ])('rejects an extra runtime dependency in the implementation owner: %s', dependency => {
    const ownerSource = fs.readFileSync(ownerPath, 'utf8')
    const compatibilitySource = fs.readFileSync(compatibilityPath, 'utf8')
    expect(() => assertGrahaDependencyClosure(ownerSource + '\n' + dependency, compatibilitySource)).toThrow()
  })

  it('rejects a compatibility facade that adds a server dependency or copies a map', () => {
    const ownerSource = fs.readFileSync(ownerPath, 'utf8')
    const facade = fs.readFileSync(compatibilityPath, 'utf8')
    for (const addition of ["export * from './address_resolver'", 'const copied = {}']) {
      expect(() => assertGrahaDependencyClosure(ownerSource, facade + '\n' + addition)).toThrow()
    }
  })
})
