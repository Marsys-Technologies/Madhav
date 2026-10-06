import type {AiConsoleStateDto,CliStateDto} from './types'
export function describeDefault(state: AiConsoleStateDto | undefined, clis: CliStateDto['clis']): string {
  if (!state) return 'Checking your selection…'
  const choice = state.defaultChoice
  if (!choice) return 'No default selected'
  if (choice.kind === 'custom_configuration') {
    return state.configurations.find(item => item.id === choice.configurationId)?.name ?? 'Saved configuration unavailable'
  }
  if (choice.kind === 'provider_model') {
    return `${state.connections.find(item => item.id === choice.connectionId)?.name ?? 'Provider'} · ${choice.modelId}`
  }
  return `${clis.find(item => item.cliId === choice.cliId)?.productName ?? 'Local CLI'} · ${choice.modelId ?? 'Built-in default'}`
}
