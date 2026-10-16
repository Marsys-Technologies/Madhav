/** Execute workflow shell against recording command shims in a disposable checkout.
 * No git repository, cloud executable, credentials or network are used.
 */
import { spawnSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

export function runWorkflowShell(run: string, commands: Record<string, string>, env: Record<string, string> = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'gochara-workflow-'))
  const bin = join(dir, 'bin')
  const log = join(dir, 'calls.jsonl')
  try {
    mkdirSync(bin)
    mkdirSync(join(dir, 'platform'))
    writeFileSync(log, '')
    for (const [name, body] of Object.entries(commands)) {
      writeFileSync(join(bin, name), `#!${process.execPath}\n` +
        `const fs = require('node:fs'); const args = process.argv.slice(2);\n` +
        `fs.appendFileSync(process.env.J56_SHIM_LOG, JSON.stringify({command: ${JSON.stringify(name)}, args, cwd: process.cwd()}) + '\\n');\n` +
        body, { mode: 0o755 })
    }
    // Deliberately omit ambient credentials and cloud/Git configuration.
    const result = spawnSync('/bin/bash', ['--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', run], {
      cwd: dir,
      env: { PATH: bin, J56_SHIM_LOG: log, ...env },
      encoding: 'utf8', timeout: 10_000,
    })
    if (result.error) throw result.error
    return { status: result.status, stdout: result.stdout, stderr: result.stderr,
      calls: readFileSync(log, 'utf8').trim().split('\n').filter(Boolean)
        .map(line => JSON.parse(line) as { command: string; args: string[]; cwd: string }) }
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
}

// Model two known commit graphs: reviewed HEAD is an ancestor after main advances,
// or origin/main is an ancestor of an unmerged dispatch. The directions differ.
export const ancestryGit = `
if (args.join(' ') === 'rev-parse HEAD') { console.log(process.env.GITHUB_SHA); process.exit(0); }
if (JSON.stringify(args) === JSON.stringify(['fetch', '--no-tags', 'origin', 'main'])) process.exit(0);
if (args[0] === 'merge-base' && args[1] === '--is-ancestor' && args.length === 4) {
  const forward = args[2] === process.env.GITHUB_SHA && args[3] === 'origin/main';
  const reverse = args[2] === 'origin/main' && args[3] === process.env.GITHUB_SHA;
  if (!forward && !reverse) process.exit(98);
  process.exit((process.env.J56_REVIEWED_ON_MAIN === 'yes') === forward ? 0 : 1);
}
process.exit(99);
`
