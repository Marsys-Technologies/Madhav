import { z } from 'zod'

/** A historical display identity; the enclosing asset_id remains the execution identity. */
export const NirmanaLegacyAliasSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
}).strict()

export type NirmanaLegacyAlias = z.infer<typeof NirmanaLegacyAliasSchema>
