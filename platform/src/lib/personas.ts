import 'server-only'
import { query } from '@/lib/db/client'
import type { Persona } from '@/types/personas'

export type { Persona }

export async function listPersonas(userId: string): Promise<Persona[]> {
  const { rows } = await query<Persona>(
    `SELECT id, user_id, name, system_prompt, default_style, default_stack, is_default, created_at, updated_at
     FROM personas
     WHERE user_id = $1
     ORDER BY is_default DESC, name ASC`,
    [userId],
  )
  return rows
}

export async function getPersona(id: string, userId: string): Promise<Persona | null> {
  const { rows } = await query<Persona>(
    `SELECT id, user_id, name, system_prompt, default_style, default_stack, is_default, created_at, updated_at
     FROM personas WHERE id = $1 AND user_id = $2`,
    [id, userId],
  )
  return rows[0] ?? null
}

export async function createPersona(params: {
  userId: string
  name: string
  systemPrompt: string
  defaultStyle?: string | null
  defaultStack?: string | null
  isDefault?: boolean
}): Promise<Persona> {
  const isDefault = params.isDefault ?? false

  // Atomic: unset any existing default for this user, then insert.
  if (isDefault) {
    await query(
      `UPDATE personas SET is_default = FALSE, updated_at = now() WHERE user_id = $1 AND is_default = TRUE`,
      [params.userId],
    )
  }

  const { rows } = await query<Persona>(
    `INSERT INTO personas (user_id, name, system_prompt, default_style, default_stack, is_default)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING id, user_id, name, system_prompt, default_style, default_stack, is_default, created_at, updated_at`,
    [params.userId, params.name, params.systemPrompt, params.defaultStyle ?? null, params.defaultStack ?? null, isDefault],
  )
  const row = rows[0]
  if (!row) throw new Error('Failed to create persona')
  return row
}

export async function updatePersona(
  id: string,
  userId: string,
  updates: {
    name?: string
    system_prompt?: string
    default_style?: string | null
    default_stack?: string | null
    is_default?: boolean
  },
): Promise<Persona | null> {
  // Atomic default-swap: unset any existing default before setting the new one.
  if (updates.is_default === true) {
    await query(
      `UPDATE personas SET is_default = FALSE, updated_at = now()
       WHERE user_id = $1 AND is_default = TRUE AND id != $2`,
      [userId, id],
    )
  }

  const setClauses: string[] = []
  const values: unknown[] = []
  let idx = 1

  if (updates.name !== undefined) { setClauses.push(`name = $${idx++}`); values.push(updates.name) }
  if (updates.system_prompt !== undefined) { setClauses.push(`system_prompt = $${idx++}`); values.push(updates.system_prompt) }
  if ('default_style' in updates) { setClauses.push(`default_style = $${idx++}`); values.push(updates.default_style ?? null) }
  if ('default_stack' in updates) { setClauses.push(`default_stack = $${idx++}`); values.push(updates.default_stack ?? null) }
  if (updates.is_default !== undefined) { setClauses.push(`is_default = $${idx++}`); values.push(updates.is_default) }

  if (setClauses.length === 0) return getPersona(id, userId)
  setClauses.push(`updated_at = now()`)

  const { rows } = await query<Persona>(
    `UPDATE personas SET ${setClauses.join(', ')}
     WHERE id = $${idx++} AND user_id = $${idx++}
     RETURNING id, user_id, name, system_prompt, default_style, default_stack, is_default, created_at, updated_at`,
    [...values, id, userId],
  )
  return rows[0] ?? null
}

export async function deletePersona(id: string, userId: string): Promise<{ deleted: boolean; lastPersona: boolean }> {
  const countResult = await query<{ count: string }>(
    `SELECT COUNT(*) AS count FROM personas WHERE user_id = $1`,
    [userId],
  )
  const count = parseInt(countResult.rows[0]?.count ?? '0', 10)
  if (count <= 1) return { deleted: false, lastPersona: true }

  const { rowCount } = await query(
    `DELETE FROM personas WHERE id = $1 AND user_id = $2`,
    [id, userId],
  )
  return { deleted: (rowCount ?? 0) > 0, lastPersona: false }
}

/** Look up a persona by ID scoped to user. Used by consume route for synthesis injection. */
export async function getPersonaForSynthesis(
  personaId: string,
  userId: string,
): Promise<Pick<Persona, 'id' | 'system_prompt' | 'default_style' | 'default_stack'> | null> {
  const { rows } = await query<Pick<Persona, 'id' | 'system_prompt' | 'default_style' | 'default_stack'>>(
    `SELECT id, system_prompt, default_style, default_stack FROM personas WHERE id = $1 AND user_id = $2`,
    [personaId, userId],
  )
  return rows[0] ?? null
}
