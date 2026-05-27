/**
 * invariants.ts — runtime assertion that every contract satisfies the
 * cross-channel rules. Called once at module load (and by the G3 test).
 */

import { z } from 'zod'
import type { ToolContract } from './types'
import { TOOL_CONTRACTS } from './registry'

export interface InvariantViolation {
  canonical_name: string
  rule: string
  detail: string
}

/** Returns the list of violations; empty array means GREEN. */
export function checkContractInvariants(
  contracts: readonly ToolContract<unknown>[] = TOOL_CONTRACTS
): InvariantViolation[] {
  const violations: InvariantViolation[] = []

  for (const c of contracts) {
    let jsonSchema: { properties?: Record<string, unknown>; required?: string[] } = {}
    try {
      jsonSchema = z.toJSONSchema(c.input_schema as z.ZodType<unknown>) as typeof jsonSchema
    } catch (err) {
      violations.push({
        canonical_name: c.canonical_name,
        rule: 'json_schema_generation',
        detail: `zod-to-json-schema threw: ${(err as Error).message}`,
      })
      continue
    }
    const props = jsonSchema.properties ?? {}
    const required = Array.isArray(jsonSchema.required) ? jsonSchema.required : []

    // Rule 1: every per_chart tool requires chart_id in its input schema.
    if (c.per_chart) {
      if (!('chart_id' in props)) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'per_chart_requires_chart_id',
          detail: 'per_chart=true but input_schema has no chart_id field',
        })
      } else if (!required.includes('chart_id')) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'per_chart_requires_chart_id',
          detail: 'chart_id present but not required',
        })
      }
    }

    // Rule 2: every chart-binding contract declares a non-null ayanamsha_role
    // AND accepts an optional ayanamsha_id field.
    if (c.per_chart) {
      if (c.ayanamsha_role === null) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'per_chart_requires_ayanamsha_role',
          detail: 'per_chart=true but ayanamsha_role is null',
        })
      }
      if (!('ayanamsha_id' in props)) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'ayanamsha_dependent_accepts_id_override',
          detail: 'per_chart tool input_schema missing ayanamsha_id field',
        })
      } else if (required.includes('ayanamsha_id')) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'ayanamsha_id_is_optional',
          detail: 'ayanamsha_id must be optional (defaults to role default)',
        })
      }
    }

    // Rule 3: any non-null ayanamsha_role must accept the optional override.
    if (c.ayanamsha_role !== null) {
      if (!('ayanamsha_id' in props)) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'ayanamsha_dependent_accepts_id_override',
          detail: 'ayanamsha_role declared but input_schema missing ayanamsha_id field',
        })
      }
      if (!c.ayanamsha_id) {
        violations.push({
          canonical_name: c.canonical_name,
          rule: 'ayanamsha_role_has_default_id',
          detail: 'non-null ayanamsha_role must have a default ayanamsha_id',
        })
      }
    }

    // Rule 4: canonical_name must be a non-empty, lowercase-snake string.
    if (!c.canonical_name || !/^[a-z][a-z0-9_]*$/.test(c.canonical_name)) {
      violations.push({
        canonical_name: c.canonical_name,
        rule: 'canonical_name_shape',
        detail: 'must match /^[a-z][a-z0-9_]*$/',
      })
    }
  }

  return violations
}

/** Throws if any invariant fails. */
export function assertContractInvariants(
  contracts: readonly ToolContract<unknown>[] = TOOL_CONTRACTS
): void {
  const violations = checkContractInvariants(contracts)
  if (violations.length > 0) {
    const lines = violations.map(v => `  - [${v.canonical_name}] ${v.rule}: ${v.detail}`)
    throw new Error(
      `Tool contract invariant violations (${violations.length}):\n${lines.join('\n')}`
    )
  }
}
