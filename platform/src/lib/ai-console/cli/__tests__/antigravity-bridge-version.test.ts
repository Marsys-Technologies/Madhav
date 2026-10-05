import { spawn, type ChildProcess } from 'node:child_process'
import { mkdtemp, mkdir, readFile, realpath, rm, writeFile } from 'node:fs/promises'
import { createServer } from 'node:net'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'

const bridgePath = resolve(__dirname, '../../../../../scripts/ai-cli-bridge/server.mjs')
const token = 'fixture-private-bridge-token-'.repeat(3)
const fixtures: { root: string; child: ChildProcess }[] = []

afterEach(async () => {
  for (const { root, child } of fixtures.splice(0)) {
    if (child.exitCode === null) {
      const stopped = new Promise<void>(done => child.once('exit', () => done()))
      child.kill('SIGTERM')
      await stopped
    }
    await rm(root, { recursive: true, force: true })
  }
})

async function startFixture(version: string) {
  const root = await realpath(await mkdtemp(join(tmpdir(), 'madhav-agy-version-')))
  const bin = join(root, '.local/bin')
  await mkdir(bin, { recursive: true, mode: 0o700 })
  const marker = join(root, 'operations.jsonl')
  await writeFile(join(bin, 'agy'), `#!${process.execPath}
    const fs=require('node:fs'); const operation=process.argv[2];
    fs.appendFileSync(${JSON.stringify(marker)},JSON.stringify(operation)+'\\n');
    if(operation==='--version')process.stdout.write(${JSON.stringify(`${version}\n`)});
    else if(operation==='models')process.stdout.write('gemini-3.8-flash-low\\tGemini 3.8 Flash (Low)\\n');
    else throw Error('Inference forbidden in metadata test');
  `, { mode: 0o755 })
  const tokenFile = join(root, 'token')
  await writeFile(tokenFile, token, { mode: 0o600 })
  const portReservation = createServer()
  await new Promise<void>(done => portReservation.listen(0, '127.0.0.1', done))
  const address = portReservation.address()
  if (!address || typeof address === 'string') throw Error('Missing fixture port')
  const port = address.port
  await new Promise<void>((done, reject) => portReservation.close(error => error ? reject(error) : done()))
  const child = spawn(process.execPath, [bridgePath], {
    env: { NODE_ENV: 'test', HOME: root, PATH: process.env.PATH, USER: process.env.USER, LOGNAME: process.env.LOGNAME,
      MARSYS_AI_CLI_BRIDGE_HOST: '127.0.0.1', MARSYS_AI_CLI_BRIDGE_PORT: String(port),
      MARSYS_AI_CLI_BRIDGE_TOKEN_FILE: tokenFile },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  fixtures.push({ root, child })
  await new Promise<void>((done, reject) => {
    const timer = setTimeout(() => { child.kill('SIGKILL'); reject(Error('Fixture startup timed out')) }, 5_000)
    child.once('error', error => { clearTimeout(timer); reject(error) })
    child.once('exit', () => { clearTimeout(timer); reject(Error('Fixture exited before startup')) })
    child.stdout!.on('data', chunk => {
      if (String(chunk).includes('marsys-ai-cli-bridge listening')) { clearTimeout(timer); done() }
    })
  })
  return { marker, invoke: async (operation: string) => {
    const response = await fetch(`http://127.0.0.1:${port}/v1/invoke`, {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ operation, cliId: 'gemini_antigravity' }), signal: AbortSignal.timeout(5_000),
    })
    return { status: response.status, body: await response.json() }
  } }
}

describe('Antigravity private bridge version admission', () => {
  it('discovers metadata for the inspected native 1.2.15 protocol without generation', async () => {
    const fixture = await startFixture('1.2.15')
    await expect(fixture.invoke('catalog')).resolves.toEqual({ status: 200, body: { models: [
      { modelId: 'gemini-3.8-flash-low', displayName: 'Gemini 3.8 Flash (Low)' },
    ] } })
    expect(await readFile(fixture.marker, 'utf8')).toBe('"--version"\n"models"\n')
  })

  it('rejects an uninspected 1.2.16 before requesting its catalogue or generating', async () => {
    const fixture = await startFixture('1.2.16')
    await expect(fixture.invoke('catalog')).resolves.toEqual({ status: 503,
      body: { error: 'AI_CLI_UNREACHABLE' } })
    expect(await readFile(fixture.marker, 'utf8')).toBe('"--version"\n')
  })
})
