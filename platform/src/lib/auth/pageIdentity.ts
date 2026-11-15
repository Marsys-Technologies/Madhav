import 'server-only'
import { query } from '@/lib/db/client'

/**
 * Identity-owned page projections. Callers retain their existing admission guards,
 * sequencing, null handling and error policy. These reads grant no access.
 */

export function readPageProfileRole(uid: string) {
  return query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
}

export function readDashboardProfile(uid: string) {
  return query<{ id: string; role: string; name: string | null; username: string | null; email: string | null; status: string }>('SELECT id, role, name, username, email, status FROM profiles WHERE id=$1', [uid])
}

export function readAccountSetupProfile(uid: string) {
  return query<{ username: string | null; email: string }>("SELECT username,email FROM profiles WHERE id=$1", [uid])
}
