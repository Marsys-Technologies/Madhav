import { spawn } from 'node:child_process'
import { StringDecoder } from 'node:string_decoder'

const SAFE_MODEL = /^[^-\u0000-\u001f\u007f][^\u0000-\u001f\u007f]{0,511}$/
const SAFE_EFFORT = /^[a-z][a-z0-9_]{0,31}$/

/** Metadata-only protocols: never open a thread, start a turn, or submit a prompt. */
export function startCatalogProcess({ cliId, executable, args, cwd, env, limits, signal,
  error = code => Object.assign(new Error(code), { code }), cleanup = async () => {} }) {
  if (signal?.aborted) throw error('AI_EXECUTION_FAILED')
  const child = spawn(executable, args, { shell: false, detached: true, cwd, env,
    stdio: ['pipe', 'pipe', 'pipe'] })
  if (!child.pid) {
    child.on('error', () => {})
    throw error('AI_CLI_UNREACHABLE')
  }
  let settled = false, stdoutBytes = 0, stderrBytes = 0, buffer = '', nextId = 3, pages = 0
  let expectedId = cliId === 'codex' ? 1 : 'catalog'
  let stage = 'initialize'
  const decoder = new StringDecoder('utf8'), models = [], cursors = new Set()
  let resolveCompletion, rejectCompletion, timer
  const completion = new Promise((resolve, reject) => { resolveCompletion = resolve; rejectCompletion = reject })
  void completion.catch(() => {})
  const finish = (failure, value) => {
    if (settled) return
    settled = true
    clearTimeout(timer)
    signal?.removeEventListener('abort', onAbort)
    void terminate(child.pid, limits.killGraceMs).then(cleanup).then(() => {
      if (failure) rejectCompletion(failure)
      else resolveCompletion({ stdout: JSON.stringify(value), exitCode: 0, signal: null })
    }).catch(() => rejectCompletion(error('AI_EXECUTION_FAILED')))
  }
  const send = value => child.stdin.write(`${JSON.stringify(value)}\n`)
  const onAbort = () => finish(error('AI_EXECUTION_FAILED'))
  child.stdin.on('error', () => finish(error('AI_CLI_UNREACHABLE')))
  child.stdout.on('data', chunk => {
    if (settled) return
    stdoutBytes += chunk.byteLength
    if (stdoutBytes > limits.stdoutBytes) return finish(error('AI_CLI_OUTPUT_LIMIT'))
    buffer += decoder.write(chunk)
    for (let newline; (newline = buffer.indexOf('\n')) >= 0 && !settled;) {
      const line = buffer.slice(0, newline); buffer = buffer.slice(newline + 1)
      if (!line.trim()) continue
      try {
        const message = JSON.parse(line)
        if (cliId === 'claude_code') {
          if (message.type !== 'control_response' || message.response?.request_id !== expectedId) continue
          if (message.response.subtype !== 'success') throw error('AI_CLI_AUTH_UNAVAILABLE')
          const listed = message.response.response?.models
          if (!Array.isArray(listed)) throw error('AI_EXECUTION_FAILED')
          models.push(...listed.filter(model => !model.hidden).map(model => projectModel({
            modelId: model.value, displayName: model.displayName,
            supportedEfforts: model.supportsEffort ? model.supportedEffortLevels : [],
            defaultEffort: model.defaultEffort ?? null, isDefault: model.value === 'default',
          }, error)))
          return finish(null, uniqueModels(models, error))
        }
        // Unsolicited server requests are refused; no tool or approval is ever executed.
        if (message.method && message.id !== undefined) {
          send({ id: message.id, error: { code: -32601, message: 'Metadata client supports no server requests' } })
          continue
        }
        if (message.id !== expectedId) continue
        if (message.error) throw error('AI_CLI_AUTH_UNAVAILABLE')
        if (stage === 'initialize') {
          send({ method: 'initialized', params: {} })
          stage = 'account'; expectedId = 2
          send({ id: expectedId, method: 'account/read', params: { refreshToken: false } })
        } else if (stage === 'account') {
          if (message.result?.account?.type !== 'chatgpt') throw error('AI_CLI_AUTH_UNAVAILABLE')
          stage = 'models'; expectedId = nextId++
          send({ id: expectedId, method: 'model/list', params: { limit: 100, includeHidden: false } })
        } else {
          const result = message.result
          if (!result || !Array.isArray(result.data) || ++pages > 16) throw error('AI_EXECUTION_FAILED')
          models.push(...result.data.filter(model => model.hidden === false).map(model => projectModel({
            modelId: model.model, displayName: model.displayName,
            supportedEfforts: model.supportedReasoningEfforts?.map(option => option.reasoningEffort),
            defaultEffort: model.defaultReasoningEffort, isDefault: model.isDefault,
          }, error)))
          if (models.length > 100) throw error('AI_CLI_OUTPUT_LIMIT')
          if (result.nextCursor == null) return finish(null, uniqueModels(models, error))
          if (typeof result.nextCursor !== 'string' || result.nextCursor.length > 4096
            || cursors.has(result.nextCursor)) throw error('AI_EXECUTION_FAILED')
          cursors.add(result.nextCursor); expectedId = nextId++
          send({ id: expectedId, method: 'model/list', params: {
            cursor: result.nextCursor, limit: 100, includeHidden: false,
          } })
        }
      } catch (failure) { finish(failure?.code ? failure : error('AI_EXECUTION_FAILED')) }
    }
  })
  child.stderr.on('data', chunk => {
    stderrBytes += chunk.byteLength
    if (stderrBytes > limits.stderrBytes) finish(error('AI_CLI_OUTPUT_LIMIT'))
  })
  child.on('error', () => finish(error('AI_CLI_UNREACHABLE')))
  child.on('close', () => { if (!settled) finish(error('AI_CLI_UNREACHABLE')) })
  timer = setTimeout(() => finish(error('AI_CLI_TIMEOUT')), Math.min(limits.timeoutMs, 20_000))
  signal?.addEventListener('abort', onAbort, { once: true })
  if (cliId === 'codex') send({ id: 1, method: 'initialize', params: {
    clientInfo: { name: 'madhav-ai-console', version: '1' }, capabilities: {},
  } })
  else send({ type: 'control_request', request_id: expectedId, request: { subtype: 'initialize' } })
  return Object.freeze({ pid: child.pid, completion, cancel: onAbort })
}

function projectModel(value, error) {
  if (typeof value.modelId !== 'string' || !SAFE_MODEL.test(value.modelId)
    || typeof value.displayName !== 'string' || !value.displayName.trim()
    || value.displayName.length > 120 || /[\u0000-\u001f\u007f]/.test(value.displayName)
    || !Array.isArray(value.supportedEfforts) || value.supportedEfforts.length > 16
    || value.supportedEfforts.some(effort => typeof effort !== 'string' || !SAFE_EFFORT.test(effort))
    || new Set(value.supportedEfforts).size !== value.supportedEfforts.length
    || (value.defaultEffort != null && !value.supportedEfforts.includes(value.defaultEffort))
    || typeof value.isDefault !== 'boolean') throw error('AI_EXECUTION_FAILED')
  return { modelId: value.modelId, displayName: value.displayName.trim(),
    supportedEfforts: value.supportedEfforts, defaultEffort: value.defaultEffort ?? null,
    isDefault: value.isDefault, isCatalogDiscovered: true }
}

function uniqueModels(models, error) {
  if (!models.length || models.length > 100 || new Set(models.map(model => model.modelId)).size !== models.length) {
    throw error('AI_EXECUTION_FAILED')
  }
  return models
}

async function terminate(pid, graceMs) {
  const send = name => { try { process.kill(-pid, name) } catch (failure) {
    if (failure.code !== 'ESRCH') throw failure
  } }
  send('SIGTERM')
  const deadline = Date.now() + graceMs
  const cleanupDeadline = deadline + 1_000
  let killed = false
  while (true) {
    try { process.kill(-pid, 0) } catch (failure) {
      if (failure.code === 'ESRCH') return
      if (failure.code !== 'EPERM') throw failure
    }
    if (Date.now() >= deadline && !killed) { send('SIGKILL'); killed = true }
    if (Date.now() >= cleanupDeadline) throw new Error('AI_CLI_TIMEOUT')
    await new Promise(resolve => setTimeout(resolve, 10))
  }
}
