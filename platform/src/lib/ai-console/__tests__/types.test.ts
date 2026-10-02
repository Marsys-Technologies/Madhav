import { describe, expect, expectTypeOf, it } from 'vitest'
import { DEFAULT_FLAGS, type FeatureFlag } from '../../config/feature_flags'
import {
  AI_ROLES, PROVIDER_IDS, CLI_IDS, AiRoleSchema, ProviderIdSchema, CliIdSchema,
  AiChoiceRefSchema, ConversationAiSelectionSchema, ConnectionValidationStateSchema,
  SafeProviderConnectionSchema, ProviderModelSchema, RoleAssignmentsSchema,
  RoutingSnapshotSchema, type AiChoiceRef, type ConversationAiSelection,
} from '../types'

const provider = { kind: 'provider_model' as const, connectionId: 'connection-1', modelId: 'model-1' }
const cli = { kind: 'local_cli' as const, cliId: 'codex' as const, modelId: null }
const configuration = { kind: 'custom_configuration' as const, configurationId: 'configuration-1' }
const roles = { synthesizer: provider, planner: provider, deep_planner: cli, worker: cli }
const snapshot = {
  source: 'pariprashna', userId: 'user-1', correlationId: 'request-1',
  conversationId: 'conversation-1', selection: { kind: 'default' },
  resolvedChoice: configuration, configurationVersion: 1,
  roles: Object.fromEntries(Object.entries(roles).map(([role, target]) => [role,
    target.kind === 'provider_model' ? { ...target, providerId: 'openai' } : target])),
}

describe('AI Console safe contracts', () => {
  it('closes the provider, CLI, and four-role vocabularies', () => {
    expect(AI_ROLES).toEqual(['synthesizer', 'planner', 'deep_planner', 'worker'])
    expect(PROVIDER_IDS).toEqual(['openai', 'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter'])
    expect(CLI_IDS).toEqual(['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'])
    for (const role of AI_ROLES) expect(AiRoleSchema.parse(role)).toBe(role)
    for (const id of PROVIDER_IDS) expect(ProviderIdSchema.parse(id)).toBe(id)
    for (const id of CLI_IDS) expect(CliIdSchema.parse(id)).toBe(id)
    expect(AiRoleSchema.safeParse('inspector').success).toBe(false)
    expect(ProviderIdSchema.safeParse('mistral').success).toBe(false)
    expect(CliIdSchema.safeParse('arbitrary_cli').success).toBe(false)
  })

  it('exposes precisely the approved choice and selection unions', () => {
    expectTypeOf<AiChoiceRef>().toEqualTypeOf<
      | { kind: 'provider_model'; connectionId: string; modelId: string }
      | { kind: 'custom_configuration'; configurationId: string }
      | { kind: 'local_cli'; cliId: 'codex' | 'claude_code' | 'gemini_antigravity' | 'kimi_code'; modelId: string | null }
    >()
    expectTypeOf<ConversationAiSelection>().toEqualTypeOf<
      { kind: 'default' } | { kind: 'explicit'; choice: AiChoiceRef }
    >()
    for (const choice of [provider, cli, { ...cli, modelId: 'model-2' }, configuration]) {
      expect(AiChoiceRefSchema.parse(choice)).toEqual(choice)
      expect(ConversationAiSelectionSchema.parse({ kind: 'explicit', choice })).toEqual({ kind: 'explicit', choice })
    }
    expect(ConversationAiSelectionSchema.parse({ kind: 'default' })).toEqual({ kind: 'default' })
  })

  it.each([
    { kind: 'provider_model', connectionId: 'c' },
    { ...provider, modelId: null }, { ...provider, connectionId: '' },
    { ...provider, modelId: ' ' }, { ...provider, cliId: 'codex' },
    { ...configuration, configurationId: '' }, { kind: 'local_cli', cliId: 'codex' },
    { ...cli, cliId: 'shell' }, { kind: 'default' },
  ])('rejects incomplete or mixed choices: %j', choice => {
    expect(AiChoiceRefSchema.safeParse(choice).success).toBe(false)
  })

  it('requires exactly four concrete assignments, with no nested configuration or Inspector', () => {
    expect(RoleAssignmentsSchema.parse(roles)).toEqual(roles)
    expect(RoleAssignmentsSchema.parse({ ...roles, planner: { ...provider, effort: 'medium' } }).planner)
      .toEqual({ ...provider, effort: 'medium' })
    expect(RoleAssignmentsSchema.safeParse({ ...roles, planner: { ...provider, effort: 'extreme' } }).success).toBe(false)
    expect(AiChoiceRefSchema.safeParse({ ...provider, effort: 'medium' }).success).toBe(false)
    expect(RoleAssignmentsSchema.safeParse({ ...roles, inspector: provider }).success).toBe(false)
    const incomplete = { synthesizer: provider, planner: provider, deep_planner: cli }
    expect(RoleAssignmentsSchema.safeParse(incomplete).success).toBe(false)
    expect(RoleAssignmentsSchema.safeParse({ ...roles, worker: configuration }).success).toBe(false)
  })

  it('defines all six validation states without treating unreachable as invalid', () => {
    for (const state of ['untested', 'validating', 'validated', 'needs_attention', 'invalid', 'unreachable']) {
      expect(ConnectionValidationStateSchema.parse(state)).toBe(state)
    }
    expect(ConnectionValidationStateSchema.safeParse('ready').success).toBe(false)
  })

  it.each(['apiKey', 'ciphertext', 'wrappedKey', 'nonce', 'tag', 'authorization', 'cliToken', 'unknown'])('rejects extra %s fields at every safe boundary', field => {
    const extra = { [field]: 'SYNTHETIC_SENSITIVE_SENTINEL' }
    const connection = { id: 'c', providerId: 'openai', name: 'Personal', maskedSuffix: '••••1234', validationState: 'validated', confirmedValid: true }
    const model = { connectionId: 'c', modelId: 'm', displayName: 'Model', compatibleRoles: ['worker'], available: true, supportsTools: false, supportsStructuredOutput: true }
    expect(SafeProviderConnectionSchema.safeParse({ ...connection, ...extra }).success).toBe(false)
    expect(ProviderModelSchema.safeParse({ ...model, ...extra }).success).toBe(false)
    expect(AiChoiceRefSchema.safeParse({ ...provider, ...extra }).success).toBe(false)
    expect(ConversationAiSelectionSchema.safeParse({ kind: 'default', ...extra }).success).toBe(false)
    expect(ConversationAiSelectionSchema.safeParse({ kind: 'explicit', choice: { ...cli, ...extra } }).success).toBe(false)
    expect(RoutingSnapshotSchema.safeParse({ ...snapshot, ...extra }).success).toBe(false)
    expect(RoutingSnapshotSchema.safeParse({ ...snapshot, roles: { ...snapshot.roles, worker: { ...cli, ...extra } } }).success).toBe(false)
  })

  it('round-trips only safe catalog metadata and immutable routing data', () => {
    const connection = { id: 'c', providerId: 'openai', name: 'Personal', maskedSuffix: '••••1234', validationState: 'validated', confirmedValid: true }
    expect(SafeProviderConnectionSchema.parse(connection)).toEqual(connection)
    expect(SafeProviderConnectionSchema.safeParse(({ ...connection, confirmedValid: undefined })).success).toBe(false)
    const model = { connectionId: 'c', modelId: 'm', displayName: 'Model', compatibleRoles: ['worker'], available: true, supportsTools: false, supportsStructuredOutput: true }
    expect(ProviderModelSchema.parse(model)).toEqual(model)
    expect(ProviderModelSchema.safeParse({ ...model, compatibleRoles: ['inspector'] }).success).toBe(false)
    const parsed = RoutingSnapshotSchema.parse(snapshot)
    expect(JSON.parse(JSON.stringify(parsed))).toEqual(snapshot)
    expect(Object.isFrozen(parsed)).toBe(true)
    expect(Object.isFrozen(parsed.roles)).toBe(true)
    expect(Object.isFrozen(parsed.roles.worker)).toBe(true)
    expect(Object.isFrozen(parsed.selection)).toBe(true)
    expect(Object.isFrozen(parsed.resolvedChoice)).toBe(true)
  })

  it('requires a positive version for resolved configurations only', () => {
    for (const version of [null, 0, -1, 1.5]) {
      expect(RoutingSnapshotSchema.safeParse({ ...snapshot, configurationVersion: version }).success).toBe(false)
    }
    expect(RoutingSnapshotSchema.safeParse({ ...snapshot, resolvedChoice: provider }).success).toBe(false)
    const directSnapshot = { ...snapshot, resolvedChoice: provider, configurationVersion: null,
      roles: Object.fromEntries(AI_ROLES.map(role => [role, { ...provider, providerId: 'openai' }])) }
    expect(RoutingSnapshotSchema.parse(directSnapshot)).toEqual(directSnapshot)
  })

  it('ships the server cutover flag disabled', () => {
    const flag: FeatureFlag = 'AI_CONSOLE_BYOK'
    expect(DEFAULT_FLAGS[flag]).toBe(false)
  })
})
