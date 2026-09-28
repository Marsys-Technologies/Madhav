/**
 * Shared served-generation handling for composite (assembling) capabilities: query_planet and
 * graha_portrait (Packet A of the fence-and-successor-envelope follow-up).
 *
 * A composite calls several leaf capabilities whose rows are build-generation scoped. It resolves the
 * chart's served generation once; with one, every generation-sensitive leaf is fenced to it. Without
 * one it must NOT fall back to the chart's current rows: it withholds the generation-sensitive
 * components, names each one in a machine-readable `components_unavailable` list, and still returns
 * everything that does not depend on a generation. One schema, defined here, serves both tools.
 */
import { resolveChartServedGeneration, servedGenerationIdentity } from './served_generation'

/** Why a generation-sensitive component was withheld. Stable, machine-readable. */
export type UnavailableComponentCode = 'served_generation_unresolved' | 'no_served_generation'

export interface UnavailableComponent {
  readonly component: string
  readonly code: UnavailableComponentCode
  /** Fixed text per code — never raw exception or database text. */
  readonly reason: string
}

/** A component the composite tried to read under a valid fence but whose read failed. */
export interface ComponentFailure {
  readonly component: string
  readonly code: 'component_read_failed'
}

/** The one failure list both composites emit (fixed code only; the raw error stays in the server log). */
export function componentFailures(components: readonly string[]): ComponentFailure[] {
  return components.map((component) => ({ component, code: 'component_read_failed' as const }))
}

export type CompositeFence =
  | { readonly fenced: true; readonly build_ids: readonly string[] }
  | { readonly fenced: false; readonly code: UnavailableComponentCode }

/**
 * How a component relates to the served generation (the audit each composite records):
 * - `independent`: a pure function of the request (no chart-scoped, build-scoped read).
 * - `sensitive`: reads build-scoped rows; served only through a fence, withheld without one.
 * - `self_fenced`: its handler resolves and applies the served generation itself and has no
 *   unfenced fallback, so it is safe with or without the composite's own resolution.
 */
export type ComponentGenerationClass = 'independent' | 'sensitive' | 'self_fenced'

export interface ComponentClassification {
  readonly class: ComponentGenerationClass
  readonly reason: string
}

const REASON: Record<UnavailableComponentCode, string> = {
  served_generation_unresolved:
    'served-generation resolution failed; component withheld rather than read from unfenced current rows',
  no_served_generation:
    'no served generation is resolved for this chart; component withheld rather than read from unfenced current rows',
}

// Any hex UUID (the same acceptance Postgres and the rest of the repo apply), not only RFC-versioned ones.
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/** True for a well-formed chart UUID. A malformed id is a caller error, not a served-generation outage. */
export function isChartUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID_RE.test(value)
}

/** Resolve the chart's served generation. Never throws; a failure is logged server-side only. */
export async function resolveCompositeFence(chartId: string, toolName: string): Promise<CompositeFence> {
  try {
    const generation = await resolveChartServedGeneration(chartId, null)
    if (servedGenerationIdentity(generation) && generation.served_build_ids.length > 0) {
      return { fenced: true, build_ids: generation.served_build_ids }
    }
    return { fenced: false, code: 'no_served_generation' }
  } catch (error) {
    console.error(`[${toolName}] served-generation resolution failed`, error)
    return { fenced: false, code: 'served_generation_unresolved' }
  }
}

export function unavailableComponents(
  components: readonly string[],
  code: UnavailableComponentCode,
): UnavailableComponent[] {
  return components.map((component) => ({ component, code, reason: REASON[code] }))
}

/** The `generation_fence` disclosure: machine-readable in both states, fixed note text. */
export function compositeGenerationFence(fence: CompositeFence, withheldCount?: number): {
  fenced: boolean
  build_ids: readonly string[] | null
  code: UnavailableComponentCode | null
  note: string
} {
  return fence.fenced
    ? {
        fenced: true,
        build_ids: fence.build_ids,
        code: null,
        note: "generation-sensitive components were read fenced to the chart's served build set",
      }
    : {
        fenced: false,
        build_ids: null,
        code: fence.code,
        note: withheldCount === 0
          ? 'no served generation is resolved for this chart; no generation-sensitive component was requested, so nothing was withheld'
          : REASON[fence.code],
      }
}

/**
 * Partition requested components: which are served and which are withheld. With a fence everything
 * is served. Without one only `sensitive` components are withheld. An unclassified component throws:
 * every section a composite assembles must appear in its audit table, so the audit cannot rot.
 */
export function splitByGenerationClass(
  classification: Readonly<Record<string, ComponentClassification>>,
  requested: readonly string[],
  fenced: boolean,
): { serve: string[]; withhold: string[] } {
  const serve: string[] = []
  const withhold: string[] = []
  for (const component of requested) {
    const entry = classification[component]
    if (!entry) throw new Error(`composite component "${component}" has no generation classification`)
    if (!fenced && entry.class === 'sensitive') withhold.push(component)
    else serve.push(component)
  }
  return { serve, withhold }
}
