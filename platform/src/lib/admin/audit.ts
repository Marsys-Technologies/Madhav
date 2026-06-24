import 'server-only'
import { query } from '@/lib/db/client'

export type AuditAction =
  | 'create_user'
  | 'edit_username'
  | 'disable_user'
  | 'enable_user'
  | 'delete_user'
  | 'role_change'
  | 'reset_password'

export async function writeAuditLog(
  actorId: string,
  action: AuditAction,
  targetUserId: string | null,
  detail?: Record<string, unknown>,
): Promise<void> {
  try {
    await query(
      `INSERT INTO admin_audit_log (actor_id, action, target_user_id, detail)
       VALUES ($1, $2, $3, $4)`,
      [actorId, action, targetUserId, detail ? JSON.stringify(detail) : null],
    )
  } catch (err) {
    // Audit failures must never break the primary action.
    console.error('[admin/audit] Failed to write audit log entry', { action, err })
  }
}
