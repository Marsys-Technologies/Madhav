/**
 * M0-T44 / SQ-08 / V-3 residual RES-1 — the migrator must ASSERT "already up to date",
 * never leave it to be inferred from silence.
 *
 * The defect this file detects: before the fix, `main()`'s success path printed exactly
 * nothing when `ran` was empty (`ran.forEach(name => console.log('Applied: ' + name))` over
 * an empty array), so a deploy log showing no migration output was byte-identical between
 *   (a) every migration was already applied — fine, and
 *   (b) the migrator never executed at all — ships an unmigrated schema.
 * CLAUDE.md §N.4 names (b) as the real hazard behind its own doctrine, and §N.8 names the
 * shape: a success signal with no detector able to distinguish "unnecessary" from "never
 * happened".
 *
 * These tests are the detector. Each asserts POSITIVE content — a printed claim carrying
 * checkable counts — never a bare absence, except the two cases where the absence is the
 * whole point (a failed run must NOT print the sentinel), and those pair the absence with a
 * positive assertion that the run really did fail.
 */
import { describe, it, expect, vi } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import crypto from 'crypto'
import { execFileSync } from 'child_process'
import type { PoolClient } from 'pg'

import {
  runCli,
  formatMigrationSummary,
  MIGRATE_COMPLETION_SENTINEL,
  type MigrationRunSummary,
} from '../migrate'

function sha256(sql: string): string {
  return crypto.createHash('sha256').update(sql).digest('hex')
}

interface Row {
  filename: string
  sha256: string
  sql_identity: string | null
}

/**
 * Mock PoolClient over an in-memory `_migrations_applied`. Deliberately a local copy rather
 * than an import of the implementation's own helpers — a test that borrows the code under
 * test can pass for the wrong reason.
 */
function makeClient(applied: Row[], opts: { failOnApply?: boolean } = {}) {
  const client = {
    query: vi.fn(async (text: string, values?: unknown[]) => {
      const q = String(text).trim()
      if (q.includes('SELECT filename, sha256, sql_identity FROM _migrations_applied')) {
        return { rows: applied.map(r => ({ ...r })) }
      }
      if (q.includes('UPDATE _migrations_applied SET sql_identity')) {
        const [identity, filename] = (values ?? []) as [string, string]
        const row = applied.find(r => r.filename === filename)
        if (row && row.sql_identity === null) row.sql_identity = identity
        return { rows: [] }
      }
      if (q.startsWith('INSERT INTO _migrations_applied')) {
        const [filename, hash, identity] = (values ?? []) as [string, string, string]
        applied.push({ filename, sha256: hash, sql_identity: identity })
        return { rows: [] }
      }
      if (opts.failOnApply && q.startsWith('SELECT 1')) {
        throw new Error('Simulated apply failure')
      }
      return { rows: [] }
    }),
    release: vi.fn(),
  } as unknown as PoolClient
  return client
}

/**
 * Each file gets DISTINCT sql — and distinct in its STATEMENTS, not merely in a comment.
 * The runner's renumbered-migration guard compares a comment/whitespace-normalised
 * `sql_identity`, so two files differing only by a comment still look like a renumber, and a
 * fixture that fights an unrelated guard tells you nothing about the reporting under test.
 */
function fixture(files: string[]): { dir: string; sqlOf: (name: string) => string } {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migrate-report-'))
  const sqlOf = (name: string) => `SELECT ${parseInt(name, 10)};\n`
  for (const name of files) fs.writeFileSync(path.join(dir, name), sqlOf(name), 'utf8')
  return { dir, sqlOf }
}

/** The one line a deploy step can grep for. Parsed back into a record so the numbers in it
 *  are asserted as data, not as a substring that merely looks right. */
function parseSentinel(lines: string[]): Record<string, string> {
  const line = lines.find(l => l.includes(MIGRATE_COMPLETION_SENTINEL))
  expect(line, 'no completion sentinel line was printed').toBeDefined()
  const fields: Record<string, string> = {}
  for (const [, k, v] of (line as string).matchAll(/(\w+)=([^\s]+)/g)) fields[k] = v
  return fields
}

describe('migrate.ts completion report — the no-op path states its result', () => {
  it('prints a checkable "nothing to apply" claim when every migration is already applied', async () => {
    const { dir, sqlOf } = fixture(['001_a.sql', '002_b.sql'])
    try {
      const client = makeClient([
        { filename: '001_a.sql', sha256: sha256(sqlOf('001_a.sql')), sql_identity: null },
        { filename: '002_b.sql', sha256: sha256(sqlOf('002_b.sql')), sql_identity: null },
        // A ledger row whose file is gone from disk — production has 7 of these, so the
        // report must not conflate "ledger rows" with "on-disk migrations recorded applied".
        { filename: '999_gone.sql', sha256: 'legacy', sql_identity: null },
      ])
      const lines: string[] = []
      const summary = await runCli(client, [dir], {}, l => lines.push(l))

      // The whole defect: this path used to produce zero output.
      expect(lines.length).toBeGreaterThan(0)

      const f = parseSentinel(lines)
      expect(f.mode).toBe('apply')
      expect(f.files_on_disk).toBe('2')
      expect(f.ledger_rows).toBe('3')
      expect(f.on_disk_applied).toBe('2')
      expect(f.pending).toBe('0')
      expect(f.applied_this_run).toBe('0')

      // The counts must be internally checkable by a reader, not three unrelated numbers.
      expect(Number(f.files_on_disk) - Number(f.on_disk_applied)).toBe(Number(f.pending))

      // And the claim itself must be stated in words, not left to arithmetic.
      expect(lines.join('\n')).toMatch(/every migration on disk is already recorded as applied/i)

      // The sentinel is terminal: a log truncated before the end cannot show it.
      expect(lines[lines.length - 1]).toContain(MIGRATE_COMPLETION_SENTINEL)

      expect(summary).toMatchObject({ pending: 0, appliedThisRun: 0, filesOnDisk: 2, ledgerRows: 3 })
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('still reports each applied migration, and says how many are left', async () => {
    const { dir, sqlOf } = fixture(['001_a.sql', '002_b.sql'])
    try {
      const client = makeClient([{ filename: '001_a.sql', sha256: sha256(sqlOf('001_a.sql')), sql_identity: null }])
      const lines: string[] = []
      await runCli(client, [dir], {}, l => lines.push(l))

      expect(lines).toContain('Applied: 002_b.sql')
      const f = parseSentinel(lines)
      expect(f.applied_this_run).toBe('1')
      expect(f.pending).toBe('0')
      expect(f.files_on_disk).toBe('2')
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('reports the dry-run preview with its own mode, and applies nothing', async () => {
    const { dir, sqlOf } = fixture(['001_a.sql', '002_b.sql'])
    try {
      const applied = [{ filename: '001_a.sql', sha256: sha256(sqlOf('001_a.sql')), sql_identity: null }]
      const client = makeClient(applied)
      const lines: string[] = []
      await runCli(client, [dir], { dryRun: true }, l => lines.push(l))

      const f = parseSentinel(lines)
      expect(f.mode).toBe('dry-run')
      expect(f.pending).toBe('1')
      expect(f.applied_this_run).toBe('0')
      expect(lines.join('\n')).toContain('002_b.sql')
      // A dry run must not have written a ledger row.
      expect(applied.map(r => r.filename)).toEqual(['001_a.sql'])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('does NOT print the sentinel when the run throws — the claim is earned, not decorative', async () => {
    const { dir } = fixture(['001_a.sql'])
    try {
      const client = makeClient([], { failOnApply: true })
      const lines: string[] = []
      // Paired positive: the run provably failed (it threw the simulated error) …
      await expect(runCli(client, [dir], {}, l => lines.push(l))).rejects.toThrow(
        'Simulated apply failure'
      )
      // … and only then is the absence of the sentinel meaningful.
      expect(lines.join('\n')).not.toContain(MIGRATE_COMPLETION_SENTINEL)
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('formats a zero-migration corpus honestly rather than claiming success over nothing', () => {
    const empty: MigrationRunSummary = {
      mode: 'apply',
      filesOnDisk: 0,
      ledgerRows: 0,
      onDiskApplied: 0,
      pending: 0,
      pendingNames: [],
      appliedThisRun: 0,
      appliedNames: [],
    }
    const out = formatMigrationSummary(empty).join('\n')
    expect(out).toContain('files_on_disk=0')
    expect(out).toMatch(/no migration files were found/i)
    // It must NOT claim everything is applied when there was nothing to look at.
    expect(out).not.toMatch(/every migration on disk is already recorded as applied/i)
  })
})

describe('migrate.ts completion report — as the deploy step actually invokes it', () => {
  it('a run that cannot reach the database exits non-zero and prints no sentinel', () => {
    const platformDir = path.resolve(__dirname, '../..')
    let stdout = ''
    let status = 0
    try {
      stdout = execFileSync('npx', ['tsx', 'scripts/migrate.ts'], {
        cwd: platformDir,
        // Explicitly unreachable. Never a real DATABASE_URL: this test must be incapable of
        // touching a live database even if one is configured in the ambient environment.
        env: { ...process.env, DATABASE_URL: 'postgresql://nobody@127.0.0.1:1/nodb' },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 120_000,
      })
    } catch (err) {
      const e = err as { status?: number; stdout?: string; stderr?: string }
      status = e.status ?? -1
      stdout = `${e.stdout ?? ''}${e.stderr ?? ''}`
    }
    // Paired positive first: the process really did fail on the connection …
    expect(stdout).toContain('ECONNREFUSED')
    expect(status).not.toBe(0)
    // … so the missing sentinel is a produced result, not an empty probe.
    expect(stdout).not.toContain(MIGRATE_COMPLETION_SENTINEL)
  }, 120_000)
})

/**
 * Why this block exists, recorded because the omission is the interesting part.
 *
 * The subprocess test above asserts a failed run prints no sentinel — but the only failure it
 * can reach without a database is `pool.connect()` throwing, and that throw happens OUTSIDE
 * `main()`'s try block. So it never exercises the catch. A mutation that printed the sentinel
 * from inside `main()`'s catch (i.e. "the migrator completed" on the failure path) survived the
 * whole suite: the author's own mutation C passed 6/6. A completion signal that also fires on
 * failure is the exact defect class M0-T44 was dispatched to close, one level up — so the gap
 * had to be closed rather than noted.
 *
 * This is a STRUCTURAL guard, and it is worth being precise about what that means: it does not
 * observe behaviour, it asserts that the sentinel has exactly ONE emission point in the source
 * — the summary line a completed run earns. It cannot prove that emission point is reached; the
 * behavioural tests above do that. It proves no OTHER path can emit it.
 */
describe('migrate.ts completion report — the sentinel has exactly one emission point', () => {
  it('is never logged from any path other than the summary a completed run earned', () => {
    const sourcePath = path.resolve(__dirname, '../migrate.ts')
    const source = fs.readFileSync(sourcePath, 'utf8')
    const lines = source.split('\n')
    const LOGGER = /(?:\blog|console\.\w+)\s*\(/

    // Paired positives first — an empty-offenders result means nothing unless the scan
    // provably read the right file and the pattern provably fires on it.
    expect(source, 'did not read migrate.ts').toContain(
      "export const MIGRATE_COMPLETION_SENTINEL = 'MIGRATE_RUNNER_COMPLETE'"
    )
    expect(
      lines.filter(l => LOGGER.test(l)).length,
      'the logging-call pattern matched nothing — the scan is vacuous'
    ).toBeGreaterThan(0)

    const offenders = lines
      .map((line, i) => ({ n: i + 1, line: line.trim() }))
      .filter(
        ({ line }) =>
          LOGGER.test(line) &&
          (line.includes('MIGRATE_COMPLETION_SENTINEL') ||
            line.includes(MIGRATE_COMPLETION_SENTINEL))
      )

    expect(
      offenders,
      'the completion sentinel is logged from somewhere other than formatMigrationSummary — ' +
        'a second emission point can fire on a path the run did not complete'
    ).toEqual([])
  })
})
