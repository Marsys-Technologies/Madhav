export type QueryClass =
  | 'factual'
  | 'interpretive'
  | 'predictive'
  | 'cross_domain'
  | 'discovery'
  | 'holistic'
  | 'remedial'
  | 'cross_native'
  | 'classical_grounding'
  | 'multi_school_triangulation'

/**
 * @deprecated for prompt-template keying (C-2 tier_excision): templates are no
 * longer keyed by audience tier. Retained because the panel synthesis path
 * (SynthesisRequest.audience_tier → adjudicator/member prompt rendering) still
 * consumes it.
 */
export type AudienceTier = 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'

export type SynthesisStrategy = 'single_model' | 'panel'

export type StyleSuffix = 'acharya' | 'brief' | 'client'

export interface PromptTemplate {
  template_id: string
  version: string
  query_class: QueryClass
  strategy: SynthesisStrategy
  body: string
  style_suffixes: {
    acharya: string
    brief: string
    client: string
  }
  /** List of {{xxx}} placeholder names expected in body */
  required_placeholders: string[]
}

/**
 * Renders a prompt template by substituting {{key}} placeholders with the
 * provided variables map, then appending the appropriate style suffix.
 *
 * Throws if any required_placeholder is absent from variables.
 */
export function renderTemplate(
  template: PromptTemplate,
  variables: Record<string, string>,
  style: StyleSuffix,
): string {
  for (const placeholder of template.required_placeholders) {
    if (!(placeholder in variables)) {
      throw new Error(
        `renderTemplate: required placeholder "{{${placeholder}}}" is missing from variables for template "${template.template_id}"`,
      )
    }
  }

  let rendered = template.body
  for (const [key, value] of Object.entries(variables)) {
    rendered = rendered.replaceAll(`{{${key}}}`, value)
  }

  rendered += template.style_suffixes[style]

  return rendered
}
