/**
 * Synthesis Prompt Registry
 *
 * Versioned prompt templates per query class, enabling M5 calibration to swap
 * in learned prompts without touching the Synthesis Orchestrator (Stream D).
 *
 * AUDIENCE TIER FALLBACK POLICY
 * ------------------------------
 * Phase 3 only registers `super_admin` × `single_model` templates.
 * When `get()` is called with `audience_tier: 'acharya_reviewer'` and no
 * explicit acharya_reviewer template is registered, it falls back to the
 * super_admin template for the same (query_class, strategy) combination.
 * Callers that need the methodology-disclosure preamble for the acharya_reviewer
 * audience should apply ACHARYA_REVIEWER_PREAMBLE from ./templates/shared
 * to the rendered output, or register a dedicated acharya_reviewer template.
 */

import type { QueryClass, AudienceTier, SynthesisStrategy, PromptTemplate } from './types'
import { template as factualTemplate } from './templates/factual'
import { template as interpretiveTemplate } from './templates/interpretive'
import { template as predictiveTemplate } from './templates/predictive'
import { template as crossDomainTemplate } from './templates/cross_domain'
import { template as discoveryTemplate } from './templates/discovery'
import { template as holisticTemplate } from './templates/holistic'
import { template as remedialTemplate } from './templates/remedial'
import { template as crossNativeTemplate } from './templates/cross_native'
import { template as multiSchoolTemplate } from './templates/multi_school_triangulation'
import { template as classicalGroundingTemplate } from './templates/classical_grounding'

export type { QueryClass, AudienceTier, SynthesisStrategy, PromptTemplate, StyleSuffix } from './types'
export { renderTemplate } from './types'

export interface PromptRegistry {
  /**
   * Look up a template by (query_class, audience_tier, strategy).
   *
   * Falls back to the super_admin template when the audience_tier is
   * 'acharya_reviewer' and no explicit acharya_reviewer template is
   * registered for this combination.
   *
   * Throws if no template is found even after fallback.
   */
  get(
    query_class: QueryClass,
    audience_tier: AudienceTier,
    strategy: SynthesisStrategy,
  ): PromptTemplate

  /** Register a template, replacing any existing entry with the same key. */
  register(template: PromptTemplate): void

  /** Return all registered templates. */
  list(): PromptTemplate[]
}

function makeKey(
  query_class: QueryClass,
  audience_tier: AudienceTier,
  strategy: SynthesisStrategy,
): string {
  return `${query_class}::${audience_tier}::${strategy}`
}

class PromptRegistryImpl implements PromptRegistry {
  private readonly store = new Map<string, PromptTemplate>()

  register(template: PromptTemplate): void {
    this.store.set(makeKey(template.query_class, template.audience_tier, template.strategy), template)
  }

  get(
    query_class: QueryClass,
    audience_tier: AudienceTier,
    strategy: SynthesisStrategy,
  ): PromptTemplate {
    // Direct lookup
    const direct = this.store.get(makeKey(query_class, audience_tier, strategy))
    if (direct !== undefined) return direct

    // Fallback: acharya_reviewer and client → super_admin
    // Phase 3 only registers super_admin templates; client-specific templates
    // are deferred to a later phase. Style suffix handles audience adaptation.
    if (audience_tier === 'acharya_reviewer' || audience_tier === 'client') {
      const fallback = this.store.get(makeKey(query_class, 'super_admin', strategy))
      if (fallback !== undefined) return fallback
    }

    throw new Error(
      `PromptRegistry: no template found for (query_class="${query_class}", audience_tier="${audience_tier}", strategy="${strategy}")` +
        (audience_tier === 'acharya_reviewer' || audience_tier === 'client'
          ? ' — fallback to super_admin also failed'
          : ''),
    )
  }

  list(): PromptTemplate[] {
    return Array.from(this.store.values())
  }
}

/**
 * Returns a fresh PromptRegistryImpl instance pre-loaded with all 10
 * super_admin × single_model templates. Each call returns a new, independent
 * instance — useful for isolated testing or per-request registries.
 */
export function createRegistry(): PromptRegistry {
  const registry = new PromptRegistryImpl()

  registry.register(factualTemplate)
  registry.register(interpretiveTemplate)
  registry.register(predictiveTemplate)
  registry.register(crossDomainTemplate)
  registry.register(discoveryTemplate)
  registry.register(holisticTemplate)
  registry.register(remedialTemplate)
  registry.register(crossNativeTemplate)
  registry.register(multiSchoolTemplate)         // NEW
  registry.register(classicalGroundingTemplate)  // NEW

  return registry
}

let _defaultRegistry: PromptRegistry | undefined

/**
 * Returns the singleton default registry, pre-loaded with all 10
 * super_admin × single_model templates.
 */
export function getDefaultRegistry(): PromptRegistry {
  if (_defaultRegistry !== undefined) return _defaultRegistry
  _defaultRegistry = createRegistry()
  return _defaultRegistry
}
