import { GoogleAuth, type IdTokenClient } from 'google-auth-library'
import type { Principal } from '../types.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
let cachedClient: IdTokenClient | null = null

async function identityToken(): Promise<string> {
  if (process.env['SERVICE_TOKEN']) return process.env['SERVICE_TOKEN'] as string
  try {
    cachedClient ??= await new GoogleAuth().getIdTokenClient(PLATFORM_URL)
    const headers = await cachedClient.getRequestHeaders(PLATFORM_URL)
    const value = (headers as Record<string, string>)['Authorization'] ?? ''
    return value.startsWith('Bearer ') ? value.slice(7) : value
  } catch {
    return MCP_INTERNAL_TOKEN
  }
}
export async function callInquiryLifecycle(principal: Principal, body: Record<string, unknown>): Promise<Record<string, unknown>> {
  const token = await identityToken()
  const response = await fetch(`${PLATFORM_URL}/api/mcp/inquiry`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60_000),
  })
  let payload: Record<string, unknown>
  try { payload = await response.json() as Record<string, unknown> }
  catch { payload = { ok: false, error: `Platform returned non-JSON (${response.status})` } }
  return payload
}
