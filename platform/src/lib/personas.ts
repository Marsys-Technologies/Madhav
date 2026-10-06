import 'server-only'
import { query, withTransaction } from '@/lib/db/client'
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
  return withTransaction(async client => {
    await client.query('SELECT id FROM profiles WHERE id=$1 FOR UPDATE', [params.userId])
    const existing = await client.query('SELECT id FROM personas WHERE user_id=$1', [params.userId])
    const isDefault = params.isDefault === true || existing.rows.length === 0
    if (isDefault) await client.query('UPDATE personas SET is_default=FALSE,updated_at=now() WHERE user_id=$1 AND is_default=TRUE', [params.userId])
    const { rows } = await client.query<Persona>(
      `INSERT INTO personas(user_id,name,system_prompt,default_style,default_stack,is_default) VALUES($1,$2,$3,$4,$5,$6)
       RETURNING id,user_id,name,system_prompt,default_style,default_stack,is_default,created_at,updated_at`,
      [params.userId,params.name,params.systemPrompt,params.defaultStyle ?? null,params.defaultStack ?? null,isDefault])
    if (!rows[0]) throw new Error('Failed to create persona')
    return rows[0]
  })
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
  return withTransaction(async client => {
    await client.query('SELECT id FROM profiles WHERE id=$1 FOR UPDATE', [userId])
    const owned = (await client.query<Persona>('SELECT * FROM personas WHERE id=$1 AND user_id=$2', [id,userId])).rows[0]
    if (!owned) return null
    // Keep one default: clearing the current default without a replacement is
    // unsupported. Setting another persona default swaps both atomically.
    if (updates.is_default === false && owned.is_default) updates = {...updates,is_default:true}
    if (updates.is_default === true) await client.query('UPDATE personas SET is_default=FALSE,updated_at=now() WHERE user_id=$1 AND is_default=TRUE AND id<>$2',[userId,id])
    const allowed = ['name','system_prompt','default_style','default_stack','is_default'] as const
    const values:unknown[]=[];const set:string[]=[]
    for (const key of allowed) if (Object.prototype.hasOwnProperty.call(updates,key)) {values.push(updates[key] ?? null);set.push(`${key}=$${values.length}`)}
    if (!set.length) return owned
    values.push(id,userId)
    const {rows}=await client.query<Persona>(`UPDATE personas SET ${set.join(',')},updated_at=now() WHERE id=$${values.length-1} AND user_id=$${values.length} RETURNING id,user_id,name,system_prompt,default_style,default_stack,is_default,created_at,updated_at`,values)
    return rows[0] ?? null
  })
}

export async function deletePersona(id:string,userId:string):Promise<{deleted:boolean;lastPersona:boolean}> {
  return withTransaction(async client=>{
    await client.query('SELECT id FROM profiles WHERE id=$1 FOR UPDATE',[userId])
    const {rows}=await client.query<Persona>('SELECT * FROM personas WHERE user_id=$1 ORDER BY created_at,id',[userId])
    const owned=rows.find(row=>row.id===id)
    if(!owned)return {deleted:false,lastPersona:false}
    if(rows.length<=1)return {deleted:false,lastPersona:true}
    await client.query('DELETE FROM personas WHERE id=$1 AND user_id=$2',[id,userId])
    if(owned.is_default)await client.query('UPDATE personas SET is_default=TRUE,updated_at=now() WHERE id=$1 AND user_id=$2',[rows.find(row=>row.id!==id)!.id,userId])
    return {deleted:true,lastPersona:false}
  })
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
