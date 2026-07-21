/**
 * Synthesis Prompt Registry
 *
 * Versioned prompt templates per query class, enabling M5 calibration to swap
 * in learned prompts without touching the Synthesis Orchestrator (Stream D).
 *
 * Templates are keyed by (query_class, strategy). `audience_tier` was excised
 * (C-2, tier_excision doctrine / DG1 ruling): the field never differentiated
 * template content — only `single_model` templates are registered and audience
 * adaptation is handled by the style suffix — so it is no longer part of the key.
 */

import type { QueryClass, SynthesisStrategy, PromptTemplate } from './types'
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
   * Look up a template by (query_class, strategy).
   *
   * Throws if no template is found.
   */
  get(
    query_class: QueryClass,
    strategy: SynthesisStrategy,
  ): PromptTemplate

  /** Register a template, replacing any existing entry with the same key. */
  register(template: PromptTemplate): void

  /** Return all registered templates. */
  list(): PromptTemplate[]
}

function makeKey(
  query_class: QueryClass,
  strategy: SynthesisStrategy,
): string {
  return `${query_class}::${strategy}`
}

class PromptRegistryImpl implements PromptRegistry {
  private readonly store = new Map<string, PromptTemplate>()

  register(template: PromptTemplate): void {
    this.store.set(makeKey(template.query_class, template.strategy), template)
  }

  get(
    query_class: QueryClass,
    strategy: SynthesisStrategy,
  ): PromptTemplate {
    const direct = this.store.get(makeKey(query_class, strategy))
    if (direct !== undefined) return direct

    throw new Error(
      `PromptRegistry: no template found for (query_class="${query_class}", strategy="${strategy}")`,
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
