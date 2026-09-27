import {
  getConversationSelection, listAiConsoleState, setConversationSelection,
} from '@/lib/ai-console/repository'
import {
  AiChoiceRefSchema, ConversationAiSelectionSchema, type AiChoiceRef, type AiRole,
} from '@/lib/ai-console/types'
import {
  IdSchema, json, projectCliCards, projectState, readBody, readId, withAiConsole, withAiConsoleMutation,
  type IdContext,
} from '@/app/api/ai-console/_shared'

export const dynamic = 'force-dynamic'

const PersistenceChoiceSchema = AiChoiceRefSchema.refine(choice => {
  if (choice.kind === 'provider_model') return IdSchema.safeParse(choice.connectionId).success
  if (choice.kind === 'custom_configuration') return IdSchema.safeParse(choice.configurationId).success
  return true
})
const SelectionInputSchema = ConversationAiSelectionSchema.refine(selection =>
  selection.kind === 'default' || PersistenceChoiceSchema.safeParse(selection.choice).success)

const ALL_ROLES: readonly AiRole[] = ['synthesizer', 'planner', 'deep_planner', 'worker']
const DEFAULT_REMEDIATION = 'Choose a default in AI Console before asking a question.'
const BROKEN_REMEDIATION = 'This AI choice is unavailable. Repair it in AI Console or choose another available option.'

type ConsoleProjection = ReturnType<typeof projectState>
type CliProjection = ReturnType<typeof projectCliCards>

function hasEveryRole(roles: readonly AiRole[]): boolean {
  return ALL_ROLES.every(role => roles.includes(role))
}

function describeChoice(choice: AiChoiceRef, state: ConsoleProjection, clis: CliProjection): { label: string; usable: boolean } {
  if (choice.kind === 'provider_model') {
    const connection = state.connections.find(row => row.id === choice.connectionId)
    const model = state.models.find(row => row.connectionId === choice.connectionId && row.modelId === choice.modelId)
    const connectionUsable = !!connection && !connection.deletedAt && connection.confirmedValid
      && (connection.validationState === 'validated' || connection.validationState === 'validating')
    const usable = connectionUsable && !!model && model.available && hasEveryRole(model.compatibleRoles)
    const label = connection
      ? `${connection.name} · ${model?.displayName ?? choice.modelId}`
      : 'Unavailable provider choice'
    return { label, usable }
  }

  if (choice.kind === 'custom_configuration') {
    const configuration = state.configurations.find(row => row.id === choice.configurationId)
    if (!configuration) return { label: 'Unavailable custom configuration', usable: false }
    const usable = !configuration.deletedAt && ALL_ROLES.every(role => {
      const target = configuration.roles[role]
      return target ? describeChoice(target, state, clis).usable : false
    })
    return { label: configuration.name, usable }
  }

  const cli = clis.find(row => row.cliId === choice.cliId)
  // Do not disclose host/auth/model detail for an ungranted or revoked CLI.
  if (!cli || cli.state === 'not_granted') return { label: 'Unavailable local CLI choice', usable: false }
  const model = cli.models.find(row => row.modelId === choice.modelId)
  return {
    label: `${cli.productName} · ${model?.displayName ?? 'Unavailable model'}`,
    usable: cli.state === 'reachable' && !!model && hasEveryRole(model.compatibleRoles),
  }
}

function presentSelection(
  selectionInput: unknown,
  state: ConsoleProjection,
  clis: CliProjection,
) {
  const selection = ConversationAiSelectionSchema.parse(selectionInput)
  const defaultView = state.defaultChoice ? describeChoice(state.defaultChoice, state, clis) : null

  if (!defaultView) {
    const selectedView = selection.kind === 'explicit' ? describeChoice(selection.choice, state, clis) : null
    return { selection, availability: 'default_required' as const, label: selectedView?.label ?? 'Default',
      resolvedLabel: null, remediation: DEFAULT_REMEDIATION }
  }

  if (!defaultView.usable) {
    return { selection, availability: 'selection_broken' as const,
      label: selection.kind === 'explicit' ? describeChoice(selection.choice, state, clis).label : 'Default',
      resolvedLabel: selection.kind === 'default' ? defaultView.label : null,
      remediation: BROKEN_REMEDIATION }
  }

  if (selection.kind === 'default') {
    return { selection, availability: 'ready' as const, label: 'Default', resolvedLabel: defaultView.label, remediation: null }
  }

  const selectedView = describeChoice(selection.choice, state, clis)
  return { selection, availability: selectedView.usable ? 'ready' as const : 'selection_broken' as const,
    label: selectedView.label, resolvedLabel: null,
    remediation: selectedView.usable ? null : BROKEN_REMEDIATION }
}

async function loadView(userId: string, conversationId: string) {
  const [selection, state] = await Promise.all([
    getConversationSelection(userId, conversationId),
    listAiConsoleState(userId),
  ])
  return presentSelection(selection, projectState(state), projectCliCards(state))
}

export async function GET(_request: Request, context: IdContext) {
  return withAiConsole(async userId => {
    const conversationId = await readId(context)
    return json(await loadView(userId, conversationId))
  })
}

export async function PUT(request: Request, context: IdContext) {
  return withAiConsoleMutation(async userId => {
    const conversationId = await readId(context)
    const selection = await readBody(request, SelectionInputSchema)
    await setConversationSelection(userId, conversationId, selection)
    return json(await loadView(userId, conversationId))
  })
}
