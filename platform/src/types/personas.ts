export interface Persona {
  id: string
  user_id: string
  name: string
  system_prompt: string
  default_style: string | null
  default_stack: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface PersonaCreate {
  name: string
  system_prompt: string
  default_style?: string | null
  default_stack?: string | null
  is_default?: boolean
}

export interface PersonaUpdate {
  name?: string
  system_prompt?: string
  default_style?: string | null
  default_stack?: string | null
  is_default?: boolean
}
