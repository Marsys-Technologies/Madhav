import { describe, expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { loadKalaProtectedMigrations } from '../migrate'

/**
 * Kāla protected public-schema window (2026-10-08) — `gh workflow run deploy.yml -f kala_schema_migration=true` must hand
 * `migrate.ts --only` EXACTLY the files of platform/scripts/kala_protected_migrations.txt, comments and blank lines skipped,
 * ascending. Same technique as gochara_window_dispatch_selection.test.ts: the real `run:` block of the step is EXTRACTED from
 * deploy.yml and EXECUTED under `bash -e` with `npx` stubbed, against a planted list file.
 */
const repoRoot = path.resolve(__dirname, '../../..')
const workflowText = fs.readFileSync(path.join(repoRoot, '.github/workflows/deploy.yml'), 'utf8')
const STEP = 'Apply exact protected public-schema migrations'

function stepScript(name: string): string {
  const lines = workflowText.split('\n')
  const at = lines.findIndex((l) => l.trim() === `- name: ${name}`)
  if (at < 0) throw new Error(`step not found in deploy.yml: ${name}`)
  const runAt = lines.findIndex((l, i) => i > at && /^\s+run: \|\s*$/.test(l))
  const runIndent = lines[runAt].match(/^\s*/)![0].length
  const body: string[] = []
  for (let i = runAt + 1; i < lines.length; i++) {
    const l = lines[i]
    if (l.trim() !== '' && l.match(/^\s*/)![0].length <= runIndent) break
    body.push(l)
  }
  const indent = Math.min(...body.filter((l) => l.trim() !== '').map((l) => l.match(/^\s*/)![0].length))
  return body.map((l) => l.slice(indent)).join('\n')
}

const SCRIPT = stepScript(STEP)

function run(inputs: Record<string, string>, listText: string | null): { status: number | null; only: string[] | null; out: string } {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'kala-window-'))
  try {
    fs.mkdirSync(path.join(dir, 'platform', 'scripts'), { recursive: true })
    fs.mkdirSync(path.join(dir, 'bin'))
    if (listText !== null) fs.writeFileSync(path.join(dir, 'platform/scripts/kala_protected_migrations.txt'), listText)
    fs.writeFileSync(path.join(dir, 'bin', 'npx'), '#!/bin/sh\nfor a in "$@"; do echo "NPX_ARG:$a"; done\n', { mode: 0o755 })
    const env: Record<string, string> = {
      PATH: `${path.join(dir, 'bin')}:${process.env.PATH ?? ''}`,
      APPLY_JATAKA_SCHEMA_MIGRATIONS: 'false',
      APPLY_AI_CONSOLE_SCHEMA_MIGRATION: 'false',
      APPLY_AI_METERING_SCHEMA_MIGRATION: 'false',
      APPLY_GOCHARA_SCHEMA_MIGRATION: 'false',
      APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'false',
      APPLY_KALA_SCHEMA_MIGRATION: 'false',
      ...inputs,
    }
    const r = spawnSync('bash', ['-e', '-c', SCRIPT], { cwd: dir, env, encoding: 'utf8' })
    const out = `${r.stdout}${r.stderr}`
    const args = out.split('\n').filter((l) => l.startsWith('NPX_ARG:')).map((l) => l.slice('NPX_ARG:'.length))
    const i = args.indexOf('--only')
    return { status: r.status, only: i >= 0 ? args[i + 1].split(',') : null, out }
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}

describe('owner dispatch — the Kāla protected window selection, executed from deploy.yml', () => {
  it('kala_schema_migration=true selects exactly the listed files, comments/blank lines skipped, ascending', () => {
    const r = run({ APPLY_KALA_SCHEMA_MIGRATION: 'true' }, '# header\n\n1334_b.sql   # trailing note\n  1330_a.sql\n# 1399_commented_out.sql\n')
    expect(r.status, r.out).toBe(0)
    expect(r.only).toEqual(['1330_a.sql', '1334_b.sql'])
  })

  it('selects the checked-in list verbatim (same set and order migrate.ts loads)', () => {
    const text = fs.readFileSync(path.join(repoRoot, 'platform/scripts/kala_protected_migrations.txt'), 'utf8')
    const r = run({ APPLY_KALA_SCHEMA_MIGRATION: 'true' }, text)
    expect(r.status, r.out).toBe(0)
    expect(r.only).toEqual([...loadKalaProtectedMigrations()])
  })

  it('refuses a missing or empty list instead of dispatching an empty window', () => {
    expect(run({ APPLY_KALA_SCHEMA_MIGRATION: 'true' }, null).status).toBe(1)
    const empty = run({ APPLY_KALA_SCHEMA_MIGRATION: 'true' }, '# nothing yet\n')
    expect(empty.status).toBe(1)
    expect(empty.out).toContain('lists no migration')
  })

  it('does not touch the selection when the Kāla input is off (Gochara window unchanged)', () => {
    const r = run({ APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'true' }, '1330_a.sql\n')
    expect(r.status, r.out).toBe(0)
    expect(r.only!.some((f) => f.startsWith('1330'))).toBe(false)
  })
})
