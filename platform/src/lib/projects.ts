import 'server-only'
import { query } from '@/lib/db/client'
import type { Project, ProjectFile, ProjectDetail } from '@/types/projects'

export type { Project, ProjectFile, ProjectDetail }

export async function listProjects(userId: string): Promise<Project[]> {
  const { rows } = await query<Project>(
    `SELECT id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at
     FROM projects
     WHERE user_id = $1 AND deleted_at IS NULL
     ORDER BY updated_at DESC`,
    [userId],
  )
  return rows
}

export async function getProject(id: string, userId: string): Promise<ProjectDetail | null> {
  const { rows } = await query<Project>(
    `SELECT id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at
     FROM projects
     WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
    [id, userId],
  )
  const project = rows[0]
  if (!project) return null

  const [convsResult, filesResult] = await Promise.all([
    query<{ conversation_id: string }>(
      `SELECT conversation_id FROM project_conversations WHERE project_id = $1`,
      [id],
    ),
    query<ProjectFile>(
      `SELECT id, project_id, storage_path, filename, mime_type, created_at
       FROM project_files WHERE project_id = $1 ORDER BY created_at DESC`,
      [id],
    ),
  ])

  return {
    ...project,
    conversation_ids: convsResult.rows.map(r => r.conversation_id),
    files: filesResult.rows,
  }
}

export async function createProject(params: {
  userId: string
  name: string
  systemPromptAddition?: string | null
  chartId?: string | null
}): Promise<Project> {
  const { rows } = await query<Project>(
    `INSERT INTO projects (user_id, name, system_prompt_addition, chart_id)
     VALUES ($1, $2, $3, $4)
     RETURNING id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at`,
    [params.userId, params.name, params.systemPromptAddition ?? null, params.chartId ?? null],
  )
  const row = rows[0]
  if (!row) throw new Error('Failed to create project')
  return row
}

export async function updateProject(
  id: string,
  userId: string,
  updates: { name?: string; system_prompt_addition?: string | null; chart_id?: string | null },
): Promise<Project | null> {
  const setClauses: string[] = []
  const values: unknown[] = []
  let idx = 1

  if (updates.name !== undefined) {
    setClauses.push(`name = $${idx++}`)
    values.push(updates.name)
  }
  if ('system_prompt_addition' in updates) {
    setClauses.push(`system_prompt_addition = $${idx++}`)
    values.push(updates.system_prompt_addition ?? null)
  }
  if ('chart_id' in updates) {
    setClauses.push(`chart_id = $${idx++}`)
    values.push(updates.chart_id ?? null)
  }

  if (setClauses.length === 0) return getProject(id, userId)

  setClauses.push(`updated_at = now()`)

  const { rows } = await query<Project>(
    `UPDATE projects SET ${setClauses.join(', ')}
     WHERE id = $${idx++} AND user_id = $${idx++} AND deleted_at IS NULL
     RETURNING id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at`,
    [...values, id, userId],
  )
  return rows[0] ?? null
}

export async function softDeleteProject(id: string, userId: string): Promise<boolean> {
  const { rowCount } = await query(
    `UPDATE projects SET deleted_at = now(), updated_at = now()
     WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
    [id, userId],
  )
  return (rowCount ?? 0) > 0
}

export async function addConversationToProject(
  projectId: string,
  conversationId: string,
): Promise<void> {
  await query(
    `INSERT INTO project_conversations (project_id, conversation_id)
     VALUES ($1, $2)
     ON CONFLICT (project_id, conversation_id) DO NOTHING`,
    [projectId, conversationId],
  )
}

export async function removeConversationFromProject(
  projectId: string,
  conversationId: string,
): Promise<boolean> {
  const { rowCount } = await query(
    `DELETE FROM project_conversations WHERE project_id = $1 AND conversation_id = $2`,
    [projectId, conversationId],
  )
  return (rowCount ?? 0) > 0
}

/** Look up the project (if any) that owns a given conversation_id.
 *  Returns null when the conversation does not belong to any project. */
export async function getProjectForConversation(
  conversationId: string,
): Promise<Project | null> {
  const { rows } = await query<Project>(
    `SELECT p.id, p.user_id, p.name, p.system_prompt_addition, p.chart_id,
            p.deleted_at, p.created_at, p.updated_at
     FROM projects p
     INNER JOIN project_conversations pc ON pc.project_id = p.id
     WHERE pc.conversation_id = $1 AND p.deleted_at IS NULL
     LIMIT 1`,
    [conversationId],
  )
  return rows[0] ?? null
}

/** Verify that a project exists and is owned by the given user.
 *  Returns the project row or null if not found / not owned. */
export async function verifyProjectOwnership(
  projectId: string,
  userId: string,
): Promise<Project | null> {
  const { rows } = await query<Project>(
    `SELECT id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at
     FROM projects WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
    [projectId, userId],
  )
  return rows[0] ?? null
}
