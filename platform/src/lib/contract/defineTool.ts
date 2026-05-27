/**
 * defineTool — author-side helper for declaring a tool contract.
 *
 * Single entry point so authors don't repeat the `per_chart` / `ayanamsha_id`
 * defaulting logic. The returned `ToolContract` is the canonical artifact
 * downstream code consumes.
 */

import { z } from 'zod'
import {
  type ToolContract,
  type ToolRole,
  type ToolFamily,
  type DataDependency,
  type AyanamshaRole,
  type ToolAnnotations,
  DEFAULT_AYANAMSHA_BY_ROLE,
} from './types'

export interface DefineToolInput<TInput> {
  canonical_name: string
  input_schema: z.ZodType<TInput>
  description: string
  role: ToolRole
  family: ToolFamily
  data_dependency: DataDependency
  /**
   * Ayanamsha role. Required key, but may be `null` for non-chart tools.
   * (We force callers to think about it; null is the explicit opt-out.)
   */
  ayanamsha_role: AyanamshaRole
  /** Optional override for the default ayanamsha id. */
  ayanamsha_id?: string | null
  /** Optional annotations (defaults to {readOnly:true, idempotent:true}). */
  annotations?: ToolAnnotations
  /**
   * Optional explicit override. If omitted, per_chart is inferred from
   * whether the input schema has a required `chart_id` field. We infer
   * rather than re-declare to avoid mismatches between schema and flag.
   */
  per_chart?: boolean
}

/** Heuristic — does the input schema require `chart_id`? Uses native zod v4 introspection. */
function schemaRequiresChartId(schema: z.ZodType<unknown>): boolean {
  try {
    const json = z.toJSONSchema(schema) as {
      properties?: Record<string, unknown>
      required?: string[]
    }
    const required = Array.isArray(json.required) ? json.required : []
    return required.includes('chart_id')
  } catch {
    return false
  }
}

export function defineTool<TInput>(
  spec: DefineToolInput<TInput>
): ToolContract<TInput> {
  const per_chart =
    spec.per_chart ?? schemaRequiresChartId(spec.input_schema as z.ZodType<unknown>)

  const ayanamsha_id =
    spec.ayanamsha_id !== undefined
      ? spec.ayanamsha_id
      : spec.ayanamsha_role === null
        ? null
        : DEFAULT_AYANAMSHA_BY_ROLE[spec.ayanamsha_role]

  const annotations: ToolAnnotations = {
    readOnly: spec.role !== 'write',
    idempotent: spec.role !== 'write',
    ...(spec.annotations ?? {}),
  }

  return {
    canonical_name: spec.canonical_name,
    input_schema: spec.input_schema,
    description: spec.description,
    annotations,
    role: spec.role,
    family: spec.family,
    data_dependency: spec.data_dependency,
    ayanamsha_role: spec.ayanamsha_role,
    ayanamsha_id,
    per_chart,
  }
}
