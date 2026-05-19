export interface Project {
  id: string
  user_id: string
  name: string
  system_prompt_addition: string | null
  chart_id: string | null
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface ProjectFile {
  id: string
  project_id: string
  storage_path: string
  filename: string
  mime_type: string
  created_at: string
}

export interface ProjectConversation {
  project_id: string
  conversation_id: string
}

export interface ProjectDetail extends Project {
  conversation_ids: string[]
  files: ProjectFile[]
}
