import { lstat, readFile } from 'node:fs/promises'

export interface LeakageBaseline {
  readonly path: string
  readonly dev: number
  readonly ino: number
  readonly size: number
  readonly mtimeMs: number
}

export async function captureLeakageBaseline(path: string): Promise<LeakageBaseline> {
  const status = await lstat(path)
  if (!status.isFile() || status.isSymbolicLink()) throw new Error('AIC_E2E_LEAKAGE_INPUT_INVALID')
  return { path, dev: status.dev, ino: status.ino, size: status.size, mtimeMs: status.mtimeMs }
}

function hasCurrentTimestamp(text: string, startedAt: number): boolean {
  return [...text.matchAll(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z/g)]
    .some(match => Date.parse(match[0]) >= startedAt)
}

export async function readFreshLeakageEvidence(
  baseline: LeakageBaseline,
  expected: { readonly runStartedAtMs: number; readonly markers: readonly string[] },
): Promise<string> {
  const status = await lstat(baseline.path)
  if (!status.isFile() || status.isSymbolicLink()) throw new Error('AIC_E2E_LEAKAGE_INPUT_INVALID')
  const bytes = await readFile(baseline.path)
  const sameFile = status.dev === baseline.dev && status.ino === baseline.ino
  const offset = sameFile && status.size >= baseline.size ? baseline.size : 0
  const fresh = bytes.subarray(offset).toString('utf8')
  const changed = !sameFile || status.size !== baseline.size || status.mtimeMs > baseline.mtimeMs
  const marked = expected.markers.some(marker => marker.length > 0 && fresh.includes(marker))
    || hasCurrentTimestamp(fresh, expected.runStartedAtMs)
  if (!changed || !fresh.trim() || !marked) throw new Error('AIC_E2E_LEAKAGE_INPUT_STALE')
  return fresh
}

const CREDENTIAL_PATTERN = /(?:authorization\s*[:=]\s*bearer\s+\S+|\bsk-(?:proj-|ant-)?[a-z0-9_-]{8,}|\bAIza[0-9A-Za-z_-]{20,}|\bxox[baprs]-[0-9A-Za-z-]{8,}|\bgh[pousr]_[0-9A-Za-z]{20,}|\beyJ[a-zA-Z0-9_-]{8,}\.eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,})/i

function forbiddenField(key: string): boolean {
  const normalized = key.replace(/[^a-z0-9]/gi, '').toLowerCase()
  return /(?:ciphertext|nonce|wrapped(?:data)?key|apikey|credential)/.test(normalized)
    || /(?:^|auth)tag$/.test(normalized)
    || /(?:refresh|access|session)?token$/.test(normalized)
    || /(?:authorization|auth|cookie|prompt|body|stdout|stderr|path)$/.test(normalized)
}

function forbiddenObject(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(forbiddenObject)
  if (!value || typeof value !== 'object') return false
  return Object.entries(value).some(([key, child]) => forbiddenField(key) || forbiddenObject(child))
}

export function containsForbiddenLeakage(text: string, secrets: readonly string[]): boolean {
  if (secrets.some(secret => secret.length > 0 && text.includes(secret)) || CREDENTIAL_PATTERN.test(text)) return true
  const documents: unknown[] = []
  try { documents.push(JSON.parse(text)) } catch {
    for (const line of text.split('\n').filter(Boolean)) {
      try { documents.push(JSON.parse(line)) } catch { /* non-JSON log line is scanned above */ }
    }
  }
  return documents.some(forbiddenObject)
}
