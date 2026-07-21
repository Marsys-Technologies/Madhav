import type { PromptTemplate } from '../types'
import {
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

/**
 * STUB — Phase 7+ feature.
 *
 * Cross-native comparison requires multi-chart L1 data, a comparative MSR
 * schema, and the synastry/composite computation layer — none of which exist
 * before Phase 7. This template is registered so the registry does not throw
 * on a cross_native lookup; the body explicitly signals the stub status.
 */
export const template: PromptTemplate = {
  template_id: 'cross_native_super_admin_single_model_v1',
  version: '2.0',
  query_class: 'cross_native',
  strategy: 'single_model',
  body: `Cross-native comparison is not yet implemented. This is a Phase 7 deliverable.`,
  style_suffixes: { ...STYLE_SUFFIXES },
  // Stub template has no required placeholders — the body is a fixed message.
  required_placeholders: [],
}
