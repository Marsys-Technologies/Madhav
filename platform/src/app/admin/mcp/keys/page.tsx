/**
 * /admin/mcp/keys — MCP API key management page.
 *
 * Super-admin only (enforced by /admin/layout.tsx). Lists all keys,
 * provides a "Create new key" form (shows full key once in a modal),
 * and a per-row revoke button.
 */

import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { McpKeysClient } from './McpKeysClient'

export default async function McpKeysPage() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/admin')

  return <McpKeysClient />
}
