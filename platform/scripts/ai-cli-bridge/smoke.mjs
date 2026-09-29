#!/usr/bin/env node

import { readFile } from 'node:fs/promises'

const endpoint = process.env.MARSYS_AI_CLI_BRIDGE_URL ?? 'http://10.160.0.2:8787'
const tokenFile = process.env.MARSYS_AI_CLI_BRIDGE_TOKEN_FILE ?? '/etc/marsys-ai-cli-bridge/token'
const token = (await readFile(tokenFile, 'utf8')).trim()
const definitions = [
  { cliId: 'codex', version: '0.158.0', auth: true },
  { cliId: 'claude_code', version: '2.1.284', auth: true },
  { cliId: 'gemini_antigravity', version: '1.2.12', auth: false },
  { cliId: 'kimi_code', version: '2.1.1', auth: false },
]

async function invoke(payload) {
  const response = await fetch(new URL('/v1/invoke', endpoint), {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await response.json()
  if (!response.ok) throw new Error(`${payload.cliId}:${payload.operation}:${body.error ?? response.status}`)
  return body
}

for (const definition of definitions) {
  const identity = await invoke({ operation: 'inspect', cliId: definition.cliId })
  const version = await invoke({ operation: 'version', cliId: definition.cliId })
  if (!version.stdout.includes(definition.version)) throw new Error(`${definition.cliId}:version-mismatch`)
  await invoke({ operation: definition.auth ? 'auth' : 'catalog', cliId: definition.cliId })
  const probe = await invoke({ operation: 'probe', cliId: definition.cliId, stdin: 'Reply with exactly OK.' })
  if (typeof probe.stdout !== 'string' || !probe.stdout.length) throw new Error(`${definition.cliId}:empty-probe`)
  await invoke({ operation: 'confirm', cliId: definition.cliId, identity,
    version: definition.version, modelIds: [null] })
  process.stdout.write(`${definition.cliId}: PASS\n`)
}
