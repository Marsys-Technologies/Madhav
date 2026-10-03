#!/usr/bin/env node

import { createHash, timingSafeEqual } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { lstat, mkdtemp, readFile, realpath, rm, stat, writeFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { homedir, tmpdir } from 'node:os'
import { join } from 'node:path'
import { spawn } from 'node:child_process'
import { StringDecoder } from 'node:string_decoder'
import { startCatalogProcess } from './catalog-protocol.mjs'

const PORT = readPositiveInteger(process.env.MARSYS_AI_CLI_BRIDGE_PORT ?? '8787', 65_535)
const HOST = process.env.MARSYS_AI_CLI_BRIDGE_HOST ?? '127.0.0.1'
const TOKEN_FILE = process.env.MARSYS_AI_CLI_BRIDGE_TOKEN_FILE
const HOME = homedir()
const MAX_BODY_BYTES = 300 * 1024
const MAX_STDOUT_BYTES = 1024 * 1024
const MAX_STDERR_BYTES = 64 * 1024
const TIMEOUT_MS = 120_000
const KILL_GRACE_MS = 500
const GLOBAL_CONCURRENCY = 4
const PER_CLI_CONCURRENCY = 2
const SAFE_MODEL = /^[^-\u0000-\u001f\u007f][^\u0000-\u001f\u007f]{0,511}$/
const SAFE_EFFORT = /^[a-z][a-z0-9_]{0,31}$/

if (!TOKEN_FILE) throw new Error('MARSYS_AI_CLI_BRIDGE_TOKEN_FILE is required')
const token = (await readFile(TOKEN_FILE, 'utf8')).trim()
if (token.length < 32) throw new Error('Bridge token is invalid')

const definitions = Object.freeze({
  codex: Object.freeze({
    path: join(HOME, '.local/bin/codex'), versions: ['0.155.1', '0.158.0'], versionArgs: ['--version'],
    authArgs: ['login', 'status'],
    catalogArgs: ['app-server', '--stdio', '-c', 'model_provider="openai"'],
  }),
  claude_code: Object.freeze({
    path: join(HOME, '.local/bin/claude'), versions: ['2.1.239', '2.1.284'], versionArgs: ['--version'],
    authArgs: ['auth', 'status'],
    catalogArgs: ['-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
      '--no-session-persistence', '--tools', '', '--setting-sources', '', '--mcp-config', '{"mcpServers":{}}',
      '--strict-mcp-config', '--permission-mode', 'dontAsk'],
  }),
  gemini_antigravity: Object.freeze({
    path: join(HOME, '.local/bin/agy'), versions: ['1.2.12', '1.2.13', '1.2.15'], versionArgs: ['--version'],
    catalogArgs: ['models'],
  }),
  kimi_code: Object.freeze({
    path: join(HOME, '.kimi-code/bin/kimi'), versions: ['2.1.1'], versionArgs: ['--version'],
    catalogArgs: ['provider', 'list', '--json'],
  }),
})

const activeByCli = new Map()
let active = 0
const queue = []
const catalogEfforts = new Map()

const server = createServer(async (request, response) => {
  response.setHeader('Cache-Control', 'no-store')
  response.setHeader('Content-Type', 'application/json; charset=utf-8')
  try {
    if (request.method !== 'POST' || request.url !== '/v1/invoke') return send(response, 404, { error: 'not_found' })
    if (!authorized(request.headers.authorization)) return send(response, 401, { error: 'unauthorized' })
    const payload = validatePayload(await readJsonBody(request))
    const result = await withSlot(payload.cliId, () => invoke(payload))
    return send(response, 200, result)
  } catch (error) {
    const code = safeError(error)
    const status = code === 'AI_CLI_TIMEOUT' ? 504
      : code === 'AI_CLI_OUTPUT_LIMIT' || code === 'AI_MODEL_UNAVAILABLE' ? 422
        : code === 'AI_CLI_NOT_INSTALLED' || code === 'AI_CLI_AUTH_UNAVAILABLE' ? 503
          : code === 'AI_EXECUTION_FAILED' ? 500 : 503
    return send(response, status, { error: code })
  }
})

server.requestTimeout = TIMEOUT_MS + 10_000
server.headersTimeout = 10_000
server.listen(PORT, HOST, () => {
  process.stdout.write(`marsys-ai-cli-bridge listening on ${HOST}:${PORT}\n`)
})

async function invoke(payload) {
  const definition = definitions[payload.cliId]
  if (!definition) throw bridgeError('AI_CLI_NOT_INSTALLED')
  if (payload.operation === 'inspect') return inspectInstallation(payload.cliId, definition)
  if (payload.operation === 'confirm') {
    const current = await inspectInstallation(payload.cliId, definition)
    if (JSON.stringify(current) !== JSON.stringify(payload.identity)) throw bridgeError('AI_CLI_UNREACHABLE')
    const version = await runCommand(payload.cliId, definition.path, definition.versionArgs, '')
    if (!definition.versions.includes(payload.version) || !containsVersion(version.stdout, payload.version)) {
      throw bridgeError('AI_CLI_UNREACHABLE')
    }
    if (!payload.modelIds.includes(null)) throw bridgeError('AI_CLI_UNREACHABLE')
    return { ok: true }
  }
  if (payload.operation === 'version') {
    return runCommand(payload.cliId, definition.path, definition.versionArgs, '')
  }
  if (payload.operation === 'auth') {
    if (!definition.authArgs) throw bridgeError('AI_CLI_AUTH_UNAVAILABLE')
    const result = await runCommand(payload.cliId, definition.path, definition.authArgs, '', undefined, 'AI_CLI_AUTH_UNAVAILABLE')
    assertSubscriptionAuth(payload.cliId, result.stdout)
    return processResult('')
  }
  if (payload.operation === 'catalog') {
    return { models: await readCatalog(payload.cliId, definition) }
  }
  if (payload.operation === 'probe' || payload.operation === 'probe_model' || payload.operation === 'execute') {
    return runGeneration(payload, definition)
  }
  throw bridgeError('AI_EXECUTION_FAILED')
}

async function readCatalog(cliId, definition) {
  if (!definition.catalogArgs) throw bridgeError('AI_CLI_AUTH_UNAVAILABLE')
  const identity = await inspectInstallation(cliId, definition)
  const version = await runCommand(cliId, definition.path, definition.versionArgs, '')
  if (!definition.versions.some(value => containsVersion(version.stdout, value))) throw bridgeError('AI_CLI_UNREACHABLE')
  let models
  if (cliId === 'codex' || cliId === 'claude_code') {
    if (cliId === 'claude_code') {
      const auth = await runCommand(cliId, definition.path, definition.authArgs, '', undefined, 'AI_CLI_AUTH_UNAVAILABLE')
      assertSubscriptionAuth(cliId, auth.stdout)
    }
    const cwd = await mkdtemp(join(tmpdir(), 'marsys-ai-cli-catalog-'))
    try {
      const process = startCatalogProcess({ cliId, executable: identity.entrypoint.realpath,
        args: definition.catalogArgs, cwd, env: safeEnvironment(), error: bridgeError,
        limits: { stdoutBytes: MAX_STDOUT_BYTES, stderrBytes: MAX_STDERR_BYTES, timeoutMs: 20_000,
          killGraceMs: KILL_GRACE_MS },
      })
      const result = await process.completion
      models = JSON.parse(result.stdout)
    } finally { await rm(cwd, { recursive: true, force: true }) }
  } else {
    const result = await runCommand(cliId, definition.path, definition.catalogArgs, '', undefined, 'AI_CLI_AUTH_UNAVAILABLE')
    models = safeCatalogModels(cliId, result.stdout)
  }
  const after = await inspectInstallation(cliId, definition)
  if (JSON.stringify(identity) !== JSON.stringify(after)) throw bridgeError('AI_CLI_UNREACHABLE')
  catalogEfforts.set(cliId, { sha256: after.entrypoint.sha256,
    models: new Map(models.map(model => [model.modelId, model.supportedEfforts ?? []])) })
  return models
}

function assertSubscriptionAuth(cliId, stdout) {
  if (cliId !== 'claude_code') return
  let auth
  try { auth = JSON.parse(stdout) } catch { throw bridgeError('AI_CLI_AUTH_UNAVAILABLE') }
  if (auth.loggedIn !== true || auth.authMethod !== 'claude.ai' || auth.apiProvider !== 'firstParty') {
    throw bridgeError('AI_CLI_AUTH_UNAVAILABLE')
  }
}

/** Return model labels only. Never forward provider/account metadata from a CLI catalog. */
function safeCatalogModels(cliId, stdout) {
  let models
  if (cliId === 'gemini_antigravity') {
    models = stdout.split(/\r?\n/).filter(Boolean).map(line => {
      const fields = line.split('\t')
      if (fields.length !== 2) throw bridgeError('AI_EXECUTION_FAILED')
      return { modelId: fields[0], displayName: fields[1] }
    })
  } else if (cliId === 'kimi_code') {
    let catalog
    try { catalog = JSON.parse(stdout) } catch { throw bridgeError('AI_EXECUTION_FAILED') }
    if (!catalog || typeof catalog !== 'object' || Array.isArray(catalog)
      || !catalog.providers || !Object.hasOwn(catalog.providers, 'managed:kimi-code')
      || !catalog.models || typeof catalog.models !== 'object' || Array.isArray(catalog.models)) {
      throw bridgeError('AI_EXECUTION_FAILED')
    }
    models = Object.entries(catalog.models).filter(([, value]) => value?.provider === 'managed:kimi-code')
      .map(([modelId, value]) => ({ modelId, displayName: value.displayName }))
  } else throw bridgeError('AI_CLI_AUTH_UNAVAILABLE')
  if (models.length === 0 || models.length > 100 || new Set(models.map(model => model.modelId)).size !== models.length
    || models.some(model => typeof model.modelId !== 'string' || !SAFE_MODEL.test(model.modelId)
      || typeof model.displayName !== 'string' || model.displayName.trim().length === 0
      || model.displayName.length > 120 || /[\u0000-\u001f\u007f]/.test(model.displayName))) {
    throw bridgeError('AI_EXECUTION_FAILED')
  }
  return models.map(model => ({ modelId: model.modelId, displayName: model.displayName.trim() }))
}

async function runGeneration(payload, definition) {
  const modelId = payload.operation === 'execute' || payload.operation === 'probe_model' ? payload.modelId : null
  if (modelId !== null && !SAFE_MODEL.test(modelId)) throw bridgeError('AI_MODEL_UNAVAILABLE')
  if (payload.cliId === 'codex') await readCatalog(payload.cliId, definition)
  else if (payload.cliId === 'claude_code') {
    const auth = await runCommand(payload.cliId, definition.path, definition.authArgs, '', undefined, 'AI_CLI_AUTH_UNAVAILABLE')
    assertSubscriptionAuth(payload.cliId, auth.stdout)
  }
  const effort = payload.operation === 'execute' ? payload.effort : undefined
  if (effort) {
    const identity = await inspectInstallation(payload.cliId, definition)
    if (catalogEfforts.get(payload.cliId)?.sha256 !== identity.entrypoint.sha256) {
      await readCatalog(payload.cliId, definition)
    }
    if (!catalogEfforts.get(payload.cliId)?.models.get(modelId)?.includes(effort)) {
      throw bridgeError('AI_MODEL_UNAVAILABLE')
    }
  }
  const cwd = await mkdtemp(join(tmpdir(), 'marsys-ai-cli-'))
  try {
    let schemaPath
    if (payload.operation === 'execute' && payload.responseSchema !== undefined) {
      const schema = JSON.stringify(payload.responseSchema)
      if (Buffer.byteLength(schema) > 64 * 1024) throw bridgeError('AI_CLI_OUTPUT_LIMIT')
      schemaPath = join(cwd, 'output-schema.json')
      await writeFile(schemaPath, schema, { mode: 0o600, flag: 'wx' })
    }
    if (payload.cliId === 'codex') {
      const args = ['exec', '--sandbox', 'read-only', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--skip-git-repo-check', '--color', 'never', '--json', '--cd', cwd]
      if (modelId) args.push('--model', modelId)
      if (effort) args.push('-c', `model_reasoning_effort=${effort}`)
      if (schemaPath) args.push('--output-schema', schemaPath)
      args.push('-')
      return await runCommand(payload.cliId, definition.path, args, payload.stdin, cwd)
    }
    if (payload.cliId === 'claude_code') {
      const args = ['-p', '--input-format', 'text', '--output-format', 'json', '--no-session-persistence',
        '--disable-slash-commands', '--tools', '', '--setting-sources', '', '--mcp-config', '{"mcpServers":{}}',
        '--strict-mcp-config', '--permission-mode', 'dontAsk']
      if (modelId) args.push('--model', modelId)
      if (effort) args.push('--effort', effort)
      if (schemaPath) args.push('--json-schema', schemaPath)
      return await runCommand(payload.cliId, definition.path, args, payload.stdin, cwd)
    }
    if (payload.cliId === 'gemini_antigravity') {
      const args = ['--sandbox', '--disable-slash-commands', '--input-format', 'stream-json',
        '--output-format', 'stream-json', '--print-timeout', '2m']
      if (modelId) args.push('--model', modelId)
      if (schemaPath) args.push('--json-schema', schemaPath)
      return await runCommand(payload.cliId, definition.path, args,
        `${JSON.stringify({ event: 'user', message: { content: payload.stdin } })}\n`, cwd)
    }
    if (payload.cliId === 'kimi_code') {
      if (schemaPath) throw bridgeError('AI_EXECUTION_FAILED')
      return await runKimiAcp(definition.path, cwd, payload.stdin, modelId)
    }
    throw bridgeError('AI_CLI_NOT_INSTALLED')
  } finally {
    await rm(cwd, { recursive: true, force: true })
  }
}

async function runKimiAcp(executable, cwd, promptText, modelId) {
  const child = spawn(executable, ['acp'], { shell: false, detached: true, cwd, env: safeEnvironment(),
    stdio: ['pipe', 'pipe', 'pipe'] })
  if (!child.pid) throw bridgeError('AI_CLI_UNREACHABLE')
  let sessionId
  let answer = ''
  let lineBuffer = ''
  let stdoutBytes = 0
  let stderrBytes = 0
  let settled = false
  let promptRequestId
  const decoder = new StringDecoder('utf8')
  const sendRpc = value => child.stdin.write(`${JSON.stringify(value)}\n`)
  const terminate = () => terminateGroup(child.pid)
  const completion = new Promise((resolvePromise, rejectPromise) => {
    const timer = setTimeout(() => finish(bridgeError('AI_CLI_TIMEOUT')), TIMEOUT_MS)
    const finish = (error, value) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      void terminate().finally(() => error ? rejectPromise(error) : resolvePromise(value))
    }
    const prompt = () => {
      promptRequestId = 5
      sendRpc({ jsonrpc: '2.0', id: promptRequestId, method: 'session/prompt', params: {
        sessionId, prompt: [{ type: 'text', text: promptText }],
      } })
    }
    const handle = message => {
      if (!message || typeof message !== 'object') return finish(bridgeError('AI_EXECUTION_FAILED'))
      if (message.method === 'session/request_permission' && message.id !== undefined) {
        sendRpc({ jsonrpc: '2.0', id: message.id, result: { outcome: { outcome: 'cancelled' } } })
        return
      }
      if (message.method === 'session/update') {
        const update = message.params?.update
        if (message.params?.sessionId !== sessionId || !update || typeof update.sessionUpdate !== 'string') {
          return finish(bridgeError('AI_EXECUTION_FAILED'))
        }
        if (update.sessionUpdate === 'agent_message_chunk') {
          if (update.content?.type !== 'text' || typeof update.content.text !== 'string') {
            return finish(bridgeError('AI_EXECUTION_FAILED'))
          }
          answer += update.content.text
          if (Buffer.byteLength(answer) > MAX_STDOUT_BYTES) finish(bridgeError('AI_CLI_OUTPUT_LIMIT'))
        } else if (update.sessionUpdate.includes('tool_call')) finish(bridgeError('AI_EXECUTION_FAILED'))
        return
      }
      if (message.id === 1) {
        if (message.result?.protocolVersion !== 1) return finish(bridgeError('AI_CLI_UNREACHABLE'))
        sendRpc({ jsonrpc: '2.0', id: 2, method: 'session/new', params: { cwd, mcpServers: [] } })
      } else if (message.id === 2) {
        if (typeof message.result?.sessionId !== 'string') return finish(bridgeError('AI_CLI_UNREACHABLE'))
        sessionId = message.result.sessionId
        sendRpc({ jsonrpc: '2.0', id: 3, method: 'session/set_config_option', params: {
          sessionId, configId: 'mode', value: 'plan',
        } })
      } else if (message.id === 3) {
        if (message.error) return finish(bridgeError('AI_CLI_UNREACHABLE'))
        if (modelId === null) prompt()
        else sendRpc({ jsonrpc: '2.0', id: 4, method: 'session/set_config_option', params: {
          sessionId, configId: 'model', value: modelId,
        } })
      } else if (message.id === 4) {
        if (message.error) return finish(bridgeError('AI_MODEL_UNAVAILABLE'))
        prompt()
      } else if (message.id === promptRequestId) {
        if (message.result?.stopReason !== 'end_turn' || !answer) return finish(bridgeError('AI_EXECUTION_FAILED'))
        finish(null, processResult(JSON.stringify({ text: answer })))
      } else if (message.id !== undefined || message.method !== undefined) {
        finish(bridgeError('AI_EXECUTION_FAILED'))
      }
    }
    child.stdout.on('data', chunk => {
      stdoutBytes += chunk.byteLength
      if (stdoutBytes > MAX_STDOUT_BYTES) return finish(bridgeError('AI_CLI_OUTPUT_LIMIT'))
      lineBuffer += decoder.write(chunk)
      let newline = lineBuffer.indexOf('\n')
      while (newline >= 0) {
        const line = lineBuffer.slice(0, newline).trim()
        lineBuffer = lineBuffer.slice(newline + 1)
        if (line) {
          try { handle(JSON.parse(line)) } catch { return finish(bridgeError('AI_EXECUTION_FAILED')) }
        }
        newline = lineBuffer.indexOf('\n')
      }
    })
    child.stderr.on('data', chunk => {
      stderrBytes += chunk.byteLength
      if (stderrBytes > MAX_STDERR_BYTES) finish(bridgeError('AI_CLI_OUTPUT_LIMIT'))
    })
    child.stdin.on('error', () => finish(bridgeError('AI_CLI_UNREACHABLE')))
    child.on('error', error => {
      logChildFailure('kimi_code', 'spawn', error.code)
      finish(bridgeError('AI_CLI_UNREACHABLE'))
    })
    child.on('close', (code, signal) => {
      if (!settled) {
        logChildFailure('kimi_code', 'close', `${code ?? 'null'}:${signal ?? 'none'}`)
        finish(bridgeError('AI_CLI_UNREACHABLE'))
      }
    })
  })
  sendRpc({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {
    protocolVersion: 1, clientCapabilities: {}, clientInfo: { name: 'MARSYS-JIS', version: '1' },
  } })
  return completion
}

async function runCommand(cliId, executable, args, input, cwd, failureCode = 'AI_CLI_UNREACHABLE') {
  if (Buffer.byteLength(input) > 256 * 1024) throw bridgeError('AI_CLI_OUTPUT_LIMIT')
  const child = spawn(executable, args, { shell: false, detached: true, cwd, env: safeEnvironment(),
    stdio: ['pipe', 'pipe', 'pipe'] })
  if (!child.pid) throw bridgeError('AI_CLI_UNREACHABLE')
  const stdout = []
  let stdoutBytes = 0
  let stderrBytes = 0
  const completion = new Promise((resolvePromise, rejectPromise) => {
    let settled = false
    const timer = setTimeout(() => finish(bridgeError('AI_CLI_TIMEOUT')), TIMEOUT_MS)
    const finish = (error, value) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      void terminateGroup(child.pid).finally(() => error ? rejectPromise(error) : resolvePromise(value))
    }
    child.stdout.on('data', chunk => {
      stdoutBytes += chunk.byteLength
      if (stdoutBytes > MAX_STDOUT_BYTES) return finish(bridgeError('AI_CLI_OUTPUT_LIMIT'))
      stdout.push(Buffer.from(chunk))
    })
    child.stderr.on('data', chunk => {
      stderrBytes += chunk.byteLength
      if (stderrBytes > MAX_STDERR_BYTES) finish(bridgeError('AI_CLI_OUTPUT_LIMIT'))
    })
    child.on('error', error => {
      logChildFailure(cliId, 'spawn', error.code)
      finish(bridgeError('AI_CLI_UNREACHABLE'))
    })
    child.on('close', (code, signal) => {
      if (code !== 0) {
        logChildFailure(cliId, 'close', `${code ?? 'null'}:${signal ?? 'none'}`)
        return finish(bridgeError(failureCode))
      }
      let decoded
      try { decoded = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(stdout)) }
      catch { return finish(bridgeError('AI_EXECUTION_FAILED')) }
      finish(null, processResult(decoded))
    })
  })
  child.stdin.on('error', () => undefined)
  child.stdin.end(input)
  return completion
}

async function terminateGroup(pid) {
  const signal = name => { try { process.kill(-pid, name) } catch (error) {
    if (error.code !== 'ESRCH') throw error
  } }
  signal('SIGTERM')
  const deadline = Date.now() + KILL_GRACE_MS
  while (true) {
    try { process.kill(-pid, 0) } catch (error) {
      if (error.code === 'ESRCH') return
      if (error.code !== 'EPERM') throw error
    }
    if (Date.now() >= deadline) signal('SIGKILL')
    await new Promise(resolveWait => setTimeout(resolveWait, 10))
  }
}

async function inspectInstallation(cliId, definition) {
  let candidate
  try { await lstat(definition.path); candidate = await realpath(definition.path) }
  catch (error) { throw bridgeError(error.code === 'ENOENT' ? 'AI_CLI_NOT_INSTALLED' : 'AI_CLI_UNREACHABLE') }
  if (!(candidate === HOME || candidate.startsWith(`${HOME}/`))) throw bridgeError('AI_CLI_UNREACHABLE')
  const before = await stat(candidate)
  if (!before.isFile() || (before.mode & 0o111) === 0 || (before.mode & 0o022) !== 0
    || (before.uid !== 0 && before.uid !== process.getuid())) throw bridgeError('AI_CLI_UNREACHABLE')
  const hash = createHash('sha256')
  for await (const chunk of createReadStream(candidate)) hash.update(chunk)
  const after = await stat(candidate)
  if (before.dev !== after.dev || before.ino !== after.ino || before.size !== after.size
    || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs) throw bridgeError('AI_CLI_UNREACHABLE')
  return { cliId, entrypoint: { candidate: definition.path, realpath: candidate, device: String(after.dev),
    inode: String(after.ino), size: after.size, modifiedMs: after.mtimeMs, changedMs: after.ctimeMs,
    mode: after.mode, uid: after.uid, sha256: hash.digest('hex') } }
}

function validatePayload(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw bridgeError('AI_EXECUTION_FAILED')
  const operation = raw.operation
  const cliId = raw.cliId
  if (!['inspect', 'confirm', 'version', 'auth', 'catalog', 'probe', 'probe_model', 'execute'].includes(operation)
    || !Object.hasOwn(definitions, cliId)) throw bridgeError('AI_EXECUTION_FAILED')
  const allowed = operation === 'confirm' ? ['operation', 'cliId', 'identity', 'version', 'modelIds']
    : operation === 'probe' ? ['operation', 'cliId', 'stdin']
      : operation === 'probe_model' ? ['operation', 'cliId', 'modelId', 'stdin']
      : operation === 'execute' ? ['operation', 'cliId', 'modelId', 'stdin', 'effort', 'responseSchema', 'maxOutputTokens']
        : ['operation', 'cliId']
  if (Object.keys(raw).some(key => !allowed.includes(key))) throw bridgeError('AI_EXECUTION_FAILED')
  if ((operation === 'probe' || operation === 'probe_model' || operation === 'execute') && (typeof raw.stdin !== 'string'
    || Buffer.byteLength(raw.stdin) > 256 * 1024)) throw bridgeError('AI_CLI_OUTPUT_LIMIT')
  if ((operation === 'execute' || operation === 'probe_model') && raw.modelId !== null
    && (typeof raw.modelId !== 'string' || !SAFE_MODEL.test(raw.modelId))) throw bridgeError('AI_MODEL_UNAVAILABLE')
  if (operation === 'probe_model' && (!['codex', 'claude_code'].includes(cliId)
    || typeof raw.modelId !== 'string' || !SAFE_MODEL.test(raw.modelId))) throw bridgeError('AI_MODEL_UNAVAILABLE')
  if (operation === 'execute' && raw.effort !== undefined
    && (typeof raw.effort !== 'string' || !SAFE_EFFORT.test(raw.effort) || !['codex', 'claude_code'].includes(cliId)
      || typeof raw.modelId !== 'string')) {
    throw bridgeError('AI_MODEL_UNAVAILABLE')
  }
  if (operation === 'confirm' && (typeof raw.version !== 'string' || !Array.isArray(raw.modelIds)
    || raw.modelIds.length > 257 || !raw.identity || typeof raw.identity !== 'object')) {
    throw bridgeError('AI_EXECUTION_FAILED')
  }
  return raw
}

async function readJsonBody(request) {
  const declared = Number(request.headers['content-length'] ?? '0')
  if (!Number.isFinite(declared) || declared > MAX_BODY_BYTES) throw bridgeError('AI_CLI_OUTPUT_LIMIT')
  const chunks = []
  let size = 0
  for await (const chunk of request) {
    size += chunk.byteLength
    if (size > MAX_BODY_BYTES) throw bridgeError('AI_CLI_OUTPUT_LIMIT')
    chunks.push(Buffer.from(chunk))
  }
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks))) }
  catch { throw bridgeError('AI_EXECUTION_FAILED') }
}

function authorized(header) {
  if (typeof header !== 'string' || !header.startsWith('Bearer ')) return false
  const supplied = Buffer.from(header.slice(7))
  const expected = Buffer.from(token)
  return supplied.length === expected.length && timingSafeEqual(supplied, expected)
}

function safeEnvironment() {
  const environment = { PATH: `${HOME}/.local/bin:${HOME}/.kimi-code/bin:/usr/local/bin:/usr/bin:/bin`,
    HOME, USER: process.env.USER, LOGNAME: process.env.LOGNAME, LANG: process.env.LANG ?? 'C.UTF-8' }
  for (const key of ['LC_ALL', 'TMPDIR', 'XDG_CONFIG_HOME', 'CODEX_HOME']) {
    if (process.env[key] && !process.env[key].includes('\0')) environment[key] = process.env[key]
  }
  return environment
}

async function withSlot(cliId, work) {
  await new Promise((resolveSlot, rejectSlot) => {
    if (queue.length >= 32) return rejectSlot(bridgeError('AI_CLI_UNREACHABLE'))
    const item = { cliId, resolve: resolveSlot, reject: rejectSlot }
    queue.push(item)
    pump()
  })
  try { return await work() } finally {
    active--
    const remaining = (activeByCli.get(cliId) ?? 1) - 1
    if (remaining) activeByCli.set(cliId, remaining); else activeByCli.delete(cliId)
    pump()
  }
}

function pump() {
  for (let index = 0; index < queue.length;) {
    const item = queue[index]
    if (active >= GLOBAL_CONCURRENCY || (activeByCli.get(item.cliId) ?? 0) >= PER_CLI_CONCURRENCY) {
      index++
      continue
    }
    queue.splice(index, 1)
    active++
    activeByCli.set(item.cliId, (activeByCli.get(item.cliId) ?? 0) + 1)
    item.resolve()
  }
}

function containsVersion(output, version) {
  return new RegExp(`(?:^|\\s)${version.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\s|$|\\))`).test(output.trim())
}

function processResult(stdout) { return { stdout, exitCode: 0, signal: null } }
function send(response, status, body) { response.statusCode = status; response.end(JSON.stringify(body)) }
function bridgeError(code) { return Object.assign(new Error(code), { code }) }
function logChildFailure(cliId, phase, detail) {
  process.stderr.write(`bridge child failure cli=${cliId} phase=${phase} detail=${detail ?? 'unknown'}\n`)
}
function safeError(error) {
  return error && typeof error === 'object' && [
    'AI_CLI_NOT_INSTALLED', 'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_UNREACHABLE', 'AI_CLI_TIMEOUT',
    'AI_CLI_OUTPUT_LIMIT', 'AI_MODEL_UNAVAILABLE', 'AI_EXECUTION_FAILED',
  ].includes(error.code) ? error.code : 'AI_EXECUTION_FAILED'
}
function readPositiveInteger(value, ceiling) {
  const parsed = Number(value)
  if (!Number.isSafeInteger(parsed) || parsed <= 0 || parsed > ceiling) throw new Error('Invalid positive integer')
  return parsed
}

function shutdown() { server.close(() => process.exit(0)) }
process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)
