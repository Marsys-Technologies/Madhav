import { describe, expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

/**
 * Pravāha B6.0 / Codex round 19 R19-1 — the owner's dispatch (`gh workflow run deploy.yml -f gochara_contracts_schema_migration=true`) must
 * hand `migrate.ts --only` EXACTLY the Gochara protected window: 1153–1157 and the five pending files 1204, 1206, 1232, 1233, 1240, in
 * ascending order, and never 1241 (1241 is a routine file that waits for SETTLED-1).
 *
 * This test does not grep: it EXTRACTS the real shell block of the step "Apply exact protected public-schema migrations" from
 * .github/workflows/deploy.yml and EXECUTES it under `bash -e` (GitHub's default shell for `run:`), with `npx` replaced by a stub that prints its
 * arguments, then asserts what was selected. A selection the SQL hash checks cannot see (the files are right, the workflow does not name them) is
 * exactly the defect this guards: the round-18 integration carried #2961's older 1153–1157-only list and would have applied NOTHING at row 8.
 *
 * Run it on #2961's head, on the integration ref and — as the merge control of the protected train — on merged `main` with
 * WINDOW_MERGE_CONTROL=1 (then every selected file must exist on the tree, the selection must equal migrate.ts's protected set for the Gochara
 * files, and no 1241_* file may be present).
 */
const repoRoot = path.resolve(__dirname, '../../..')
const workflowText = fs.readFileSync(path.join(repoRoot, '.github/workflows/deploy.yml'), 'utf8')
const STEP = 'Apply exact protected public-schema migrations'

export const WINDOW_FILES = [
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
  '1204_gochara_av_qualifier_object_role.sql',
  '1206_gochara_search_inventory_completeness.sql',
  '1232_gochara_search_moon_scope_domain.sql',
  '1233_gochara_p1_period_anchor.sql',
  '1240_gochara_window_verification_gate.sql',
  '1308_gochara_near_miss_storage.sql',
]
const PENDING_SIX = WINDOW_FILES.slice(5)     // 1204, 1206, 1232, 1233, 1240, 1308 (1308 = the ND-P2 near-miss storage, second window)

/** The `run: |` block scalar of the named step, de-indented — extracted by indentation, no YAML library needed. */
function stepScript(name: string): string {
  const lines = workflowText.split('\n')
  const at = lines.findIndex((l) => l.trim() === `- name: ${name}`)
  if (at < 0) throw new Error(`step not found in deploy.yml: ${name}`)
  const runAt = lines.findIndex((l, i) => i > at && /^\s+run: \|\s*$/.test(l))
  if (runAt < 0) throw new Error(`no run: | block after step ${name}`)
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

interface Outcome { status: number | null; only: string[] | null; out: string }

/** Execute the extracted block with the given workflow inputs; `npx` is a stub that records its arguments. */
function run(inputs: Record<string, string>): Outcome {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'window-selection-'))
  try {
    fs.mkdirSync(path.join(dir, 'platform'))
    fs.mkdirSync(path.join(dir, 'bin'))
    fs.writeFileSync(path.join(dir, 'bin', 'npx'), '#!/bin/sh\nfor a in "$@"; do echo "NPX_ARG:$a"; done\n', { mode: 0o755 })
    const env: Record<string, string> = {
      PATH: `${path.join(dir, 'bin')}:${process.env.PATH ?? ''}`,
      APPLY_JATAKA_SCHEMA_MIGRATIONS: 'false',
      APPLY_AI_CONSOLE_SCHEMA_MIGRATION: 'false',
      APPLY_AI_METERING_SCHEMA_MIGRATION: 'false',
      APPLY_GOCHARA_SCHEMA_MIGRATION: 'false',
      APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'false',
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

describe('owner dispatch — the protected window selection, executed from deploy.yml', () => {
  it('gochara_contracts_schema_migration=true selects exactly 1153–1157 then 1204, 1206, 1232, 1233, 1240, 1308, in that order', () => {
    const r = run({ APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'true' })
    expect(r.status, r.out).toBe(0)
    expect(r.only).toEqual(WINDOW_FILES)
  })

  it('the ordered pending six are the last six of the selection and are strictly ascending by number', () => {
    const r = run({ APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'true' })
    expect(r.only!.slice(-6)).toEqual(PENDING_SIX)
    const nums = r.only!.map((f) => Number(f.split('_')[0]))
    expect(nums).toEqual([...nums].sort((a, b) => a - b))
  })

  it('never selects 1241 (a routine file that waits for SETTLED-1) in ANY input combination', () => {
    const flags = ['APPLY_JATAKA_SCHEMA_MIGRATIONS', 'APPLY_AI_CONSOLE_SCHEMA_MIGRATION', 'APPLY_AI_METERING_SCHEMA_MIGRATION', 'APPLY_GOCHARA_SCHEMA_MIGRATION', 'APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION']
    for (let mask = 1; mask < 1 << flags.length; mask++) {
      const inputs = Object.fromEntries(flags.map((f, i) => [f, mask & (1 << i) ? 'true' : 'false']))
      const r = run(inputs)
      expect(r.status, JSON.stringify(inputs) + r.out).toBe(0)
      expect(r.only!.filter((f) => f.startsWith('1241')), JSON.stringify(inputs)).toEqual([])
    }
  }, 120_000)

  it('selects nothing and refuses when no window is authorised', () => {
    const r = run({})
    expect(r.status).toBe(1)
    expect(r.only).toBeNull()
    expect(r.out).toContain('No protected public-schema migration was explicitly authorized')
  })

  it('every Gochara file migrate.ts refuses as protected is one the window selects (the runner can never refuse a file the window omits)', () => {
    const set = fs.readFileSync(path.join(repoRoot, 'platform/scripts/migrate.ts'), 'utf8').match(/PROTECTED_PUBLIC_SCHEMA_MIGRATIONS = new Set\(\[([\s\S]*?)\]\)/)
    expect(set, 'PROTECTED_PUBLIC_SCHEMA_MIGRATIONS not found in migrate.ts').not.toBeNull()
    const refused = [...set![1].matchAll(/'([^']+\.sql)'/g)].map((m) => m[1]).filter((f) => /gochara/.test(f))
    const selected = new Set(run({ APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: 'true' }).only!)
    expect(refused.filter((f) => !selected.has(f))).toEqual([])
  })

  it("keeps #2961's phase and exception wiring in the same file (the composed workflow carries both)", () => {
    expect((workflowText.match(/DATA_PLANE_VERIFIER_PHASE: \$\{\{ vars\.DATA_PLANE_VERIFIER_PHASE \}\}/g) ?? []).length).toBeGreaterThanOrEqual(4)
    expect((workflowText.match(/DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS: \$\{\{ vars\.DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS \}\}/g) ?? []).length).toBeGreaterThanOrEqual(4)
  })

  // The merge control of the protected train (checklist row 7): run with WINDOW_MERGE_CONTROL=1 on merged main. Reported SKIPPED, not passed, elsewhere.
  describe.runIf(process.env.WINDOW_MERGE_CONTROL === '1')('merge control on merged main', () => {
    it('every selected file exists on this tree and the Gochara protected set in migrate.ts equals the selection', () => {
      const dir = path.join(repoRoot, 'platform/migrations')
      expect(WINDOW_FILES.filter((f) => !fs.existsSync(path.join(dir, f)))).toEqual([])
      const set = fs.readFileSync(path.join(repoRoot, 'platform/scripts/migrate.ts'), 'utf8').match(/PROTECTED_PUBLIC_SCHEMA_MIGRATIONS = new Set\(\[([\s\S]*?)\]\)/)!
      const refused = [...set[1].matchAll(/'([^']+\.sql)'/g)].map((m) => m[1]).filter((f) => /gochara/.test(f))
      expect(refused.sort()).toEqual([...WINDOW_FILES].sort())
    })

    it('no 1241_* file is present on main (it is applied only after SETTLED-1)', () => {
      expect(fs.readdirSync(path.join(repoRoot, 'platform/migrations')).filter((f) => f.startsWith('1241_'))).toEqual([])
    })
  })
})
