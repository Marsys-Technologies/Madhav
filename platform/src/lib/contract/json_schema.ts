/**
 * Zod → JSON-Schema converter.
 *
 * Brief 2b asks for `zod-to-json-schema`. The repo is on Zod v4 (which the
 * installed `zod-to-json-schema@3.25` does not handle — Zod v4 changed its
 * internal `_def` shape and the converter returns {}). Zod v4 ships its OWN
 * `z.toJSONSchema()` that emits the same Draft-7-style schemas, which is what
 * we use here. Single function so the rest of the contract treats JSON-Schema
 * generation as a black box.
 */

import { z } from 'zod'

export interface JsonSchemaObject {
  $schema?: string
  type?: string
  properties?: Record<string, unknown>
  required?: string[]
  additionalProperties?: boolean | Record<string, unknown>
  [k: string]: unknown
}

/** Generate a JSON-Schema document for a Zod schema. */
export function zodToJsonSchema(schema: z.ZodType<unknown>): JsonSchemaObject {
  // Zod v4 native — supports v4 unionTypes, optionals, defaults, etc.
  return z.toJSONSchema(schema) as JsonSchemaObject
}
