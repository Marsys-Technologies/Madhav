/**
 * Lane P2-C (PPR-09/16) — the composer's Model pill, made honest.
 *
 * Before this lane, `Composer.tsx`'s `MODEL_ROWS` was a hand-written mockup
 * list ('Claude Opus', 'GPT-4.1', 'Kimi K2 · OpenRouter', …) whose `value`
 * strings did not correspond to any real `@/lib/models/registry` id. Even had
 * the composer wired the selection through to the request body (it did not —
 * `model` was local state the submit handler never read), `isValidModelId`
 * would have rejected every one of those labels and silently fallen back to
 * the stack's synthesis primary — a second, independent way the pill lied.
 *
 * This module derives the picker rows from the SAME registry the server binds
 * `model_id` against (`bindTurnParams` in `pipeline/safety_gate.ts`), so a
 * selection here is always a valid id there. No wrapper-local constant
 * duplicates the registry's data (§N.7 item 3) — a model added, renamed, or
 * retired in the registry changes this list on the next render, not on the
 * next edit to this file.
 */

import { MODELS, type ModelTier } from '@/lib/models/registry'
import type { PickerRow } from './PickerPopover'
import type { AiRole, CliId, ProviderId } from '@/components/ai-console/types'
import type { AiChoiceOption, ConversationSelection, SelectionView } from '../hooks/useAiChoices'

/** Registry `label` substrings that mark a row as not meant for a user picker
 *  (deprecated, unavailable, an internal-only alias, EOL, or degraded). */
const NOT_USER_FACING = /\[(unavailable|deprecated|internal label only|eol|degraded)\]/i

const TIER_META: Record<ModelTier, string> = {
  premium: 'A · deepest',
  mid: 'B · balanced',
  worker: 'C · fast',
}

/**
 * Synthesis-capable, user-facing models, in registry order. `role` filters to
 * 'synthesis' | 'both' — a 'planner'/'worker'-only routing entry is never
 * something a reader should pick as their reading's synthesis model.
 */
export function getSynthesisModelRows(): PickerRow<string>[] {
  const rows: PickerRow<string>[] = [{ value: 'auto', label: 'Auto', detail: 'best available' }]
  for (const m of MODELS) {
    if (m.role !== 'synthesis' && m.role !== 'both') continue
    if (NOT_USER_FACING.test(m.label)) continue
    rows.push({ value: m.id, label: m.label, meta: TIER_META[m.tier] })
  }
  return rows
}

export interface AiChoicesAggregateDto {
  connections: Array<{
    id: string
    providerId: ProviderId
    name: string
    validationState: 'untested' | 'validating' | 'validated' | 'needs_attention' | 'invalid' | 'unreachable'
    confirmedValid: boolean
    deletedAt: string | null
  }>
  models: Array<{
    connectionId: string
    modelId: string
    displayName: string
    compatibleRoles: AiRole[]
    available: boolean
  }>
  configurations: Array<{
    id: string
    name: string
    version: number
    deletedAt: string | null
    roles: Record<AiRole, ProviderChoiceDto | CliChoiceDto>
  }>
  defaultChoice: ChoiceDto | null
}

export interface AiChoicesCliDto {
  clis: Array<
    | { cliId: CliId; productName: string; state: 'not_granted' }
    | {
        cliId: CliId
        productName: string
        state: 'untested' | 'validating' | 'reachable' | 'not_installed' | 'auth_unavailable' | 'unreachable' | 'needs_attention'
        models: Array<{ modelId: string | null; displayName: string; compatibleRoles: AiRole[] }>
      }
  >
}

type ProviderChoiceDto = { kind: 'provider_model'; connectionId: string; modelId: string }
type ConfigurationChoiceDto = { kind: 'custom_configuration'; configurationId: string }
type CliChoiceDto = { kind: 'local_cli'; cliId: CliId; modelId: string | null }
type ChoiceDto = ProviderChoiceDto | ConfigurationChoiceDto | CliChoiceDto

const ALL_ROLES: readonly AiRole[] = ['synthesizer', 'planner', 'deep_planner', 'worker']

function supportsEveryRole(roles: readonly AiRole[]): boolean {
  return ALL_ROLES.every(role => roles.includes(role))
}

function supportsRole(roles: readonly AiRole[], role: AiRole): boolean {
  return roles.includes(role)
}

export function selectionKey(selection: ConversationSelection): string {
  if (selection.kind === 'default') return 'default'
  const choice = selection.choice
  if (choice.kind === 'provider_model') return `provider:${choice.connectionId}:${choice.modelId}`
  if (choice.kind === 'custom_configuration') return `configuration:${choice.configurationId}`
  return `cli:${choice.cliId}:${choice.modelId ?? 'builtin'}`
}

function explicit(choice: ChoiceDto): ConversationSelection {
  return { kind: 'explicit', choice }
}

function providerUsable(aggregate: AiChoicesAggregateDto, choice: ProviderChoiceDto): boolean {
  const connection = aggregate.connections.find(row => row.id === choice.connectionId)
  const model = aggregate.models.find(row => row.connectionId === choice.connectionId && row.modelId === choice.modelId)
  return !!connection && !connection.deletedAt && connection.confirmedValid
    && (connection.validationState === 'validated' || connection.validationState === 'validating')
    && !!model && model.available && supportsEveryRole(model.compatibleRoles)
}

function cliUsable(clis: AiChoicesCliDto, choice: CliChoiceDto): boolean {
  const cli = clis.clis.find(row => row.cliId === choice.cliId)
  if (!cli || cli.state !== 'reachable') return false
  const model = cli.models.find(row => row.modelId === choice.modelId)
  return !!model && supportsEveryRole(model.compatibleRoles)
}

function providerUsableForRole(aggregate: AiChoicesAggregateDto, choice: ProviderChoiceDto, role: AiRole): boolean {
  const connection = aggregate.connections.find(row => row.id === choice.connectionId)
  const model = aggregate.models.find(row => row.connectionId === choice.connectionId && row.modelId === choice.modelId)
  return !!connection && !connection.deletedAt && connection.confirmedValid
    && (connection.validationState === 'validated' || connection.validationState === 'validating')
    && !!model && model.available && supportsRole(model.compatibleRoles, role)
}

function cliUsableForRole(clis: AiChoicesCliDto, choice: CliChoiceDto, role: AiRole): boolean {
  const cli = clis.clis.find(row => row.cliId === choice.cliId)
  if (!cli || cli.state !== 'reachable') return false
  const model = cli.models.find(row => row.modelId === choice.modelId)
  return !!model && supportsRole(model.compatibleRoles, role)
}

function choiceUsable(aggregate: AiChoicesAggregateDto, clis: AiChoicesCliDto, choice: ChoiceDto): boolean {
  if (choice.kind === 'provider_model') return providerUsable(aggregate, choice)
  if (choice.kind === 'local_cli') return cliUsable(clis, choice)
  const configuration = aggregate.configurations.find(row => row.id === choice.configurationId)
  return !!configuration && !configuration.deletedAt && ALL_ROLES.every(role => {
    const target = configuration.roles[role]
    return target.kind === 'provider_model'
      ? providerUsableForRole(aggregate, target, role)
      : cliUsableForRole(clis, target, role)
  })
}

function choiceLabel(aggregate: AiChoicesAggregateDto, clis: AiChoicesCliDto, choice: ChoiceDto): string {
  if (choice.kind === 'provider_model') {
    const connection = aggregate.connections.find(row => row.id === choice.connectionId)
    const model = aggregate.models.find(row => row.connectionId === choice.connectionId && row.modelId === choice.modelId)
    return connection ? `${connection.name} · ${model?.displayName ?? choice.modelId}` : 'Unavailable provider choice'
  }
  if (choice.kind === 'custom_configuration') {
    return aggregate.configurations.find(row => row.id === choice.configurationId)?.name ?? 'Unavailable custom configuration'
  }
  const cli = clis.clis.find(row => row.cliId === choice.cliId)
  if (!cli || cli.state === 'not_granted') return 'Unavailable local CLI choice'
  const model = cli.models.find(row => row.modelId === choice.modelId)
  return `${cli.productName} · ${model?.displayName ?? 'Unavailable model'}`
}

/** Client presentation only. Server ownership/availability remains authoritative. */
export function buildAiChoiceOptions(
  aggregate: AiChoicesAggregateDto,
  clis: AiChoicesCliDto,
  view: SelectionView,
): AiChoiceOption[] {
  const defaultLabel = aggregate.defaultChoice && choiceUsable(aggregate, clis, aggregate.defaultChoice)
    ? `Default — ${choiceLabel(aggregate, clis, aggregate.defaultChoice)}`
    : 'Default — unavailable'
  const options: AiChoiceOption[] = [{
    key: 'default', group: null, label: defaultLabel, selection: { kind: 'default' },
    disabled: !aggregate.defaultChoice || !choiceUsable(aggregate, clis, aggregate.defaultChoice),
  }]

  for (const connection of aggregate.connections) {
    for (const model of aggregate.models.filter(row => row.connectionId === connection.id)) {
      const choice: ProviderChoiceDto = { kind: 'provider_model', connectionId: connection.id, modelId: model.modelId }
      if (!choiceUsable(aggregate, clis, choice)) continue
      const selection = explicit(choice)
      options.push({ key: selectionKey(selection), group: 'Provider connections', label: `${connection.name} · ${model.displayName}`, selection, disabled: false })
    }
  }

  for (const configuration of aggregate.configurations) {
    const choice: ConfigurationChoiceDto = { kind: 'custom_configuration', configurationId: configuration.id }
    if (!choiceUsable(aggregate, clis, choice)) continue
    const selection = explicit(choice)
    options.push({ key: selectionKey(selection), group: 'Custom configurations', label: configuration.name, selection, disabled: false })
  }

  for (const cli of clis.clis) {
    if (cli.state !== 'reachable') continue
    for (const model of cli.models) {
      const choice: CliChoiceDto = { kind: 'local_cli', cliId: cli.cliId, modelId: model.modelId }
      if (!choiceUsable(aggregate, clis, choice)) continue
      const selection = explicit(choice)
      options.push({ key: selectionKey(selection), group: 'Local CLIs', label: `${cli.productName} · ${model.displayName}`, selection, disabled: false })
    }
  }

  const selectedKey = selectionKey(view.selection)
  if (!options.some(option => option.key === selectedKey)) {
    options.splice(1, 0, { key: selectedKey, group: null, label: view.label || 'Unavailable AI choice',
      detail: view.remediation ?? 'Repair this choice in AI Console.', selection: view.selection, disabled: true })
  }
  return options
}
