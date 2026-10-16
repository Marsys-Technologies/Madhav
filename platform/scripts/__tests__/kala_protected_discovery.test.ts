import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { discoverKalaProtectedMigrations } from '../migrate'

describe('automatic Kāla protected migration membership', () => {
  it('uses the shared privilege detector for a new DDL migration without a list edit', () => {
    const root = mkdtempSync(path.join(tmpdir(), 'ci-protected-'))
    try {
      mkdirSync(path.join(root, 'platform/scripts'), { recursive: true })
      mkdirSync(path.join(root, 'platform/migrations'), { recursive: true })
      writeFileSync(path.join(root, 'platform/scripts/kala_protected_migrations.txt'), '1330_legacy.sql\n')
      writeFileSync(path.join(root, 'platform/migrations/9001_new.sql'), 'CREATE TABLE public.example (id int);\n')
      writeFileSync(path.join(root, 'platform/migrations/9002_dml.sql'), 'UPDATE example SET id=1;\n')
      expect([...discoverKalaProtectedMigrations(root)]).toEqual(['1330_legacy.sql', '9001_new.sql'])
      writeFileSync(path.join(root, 'platform/scripts/kala_protected_migrations.txt'), 'broken\n')
      expect(() => discoverKalaProtectedMigrations(root)).toThrow()
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
