import { AI_ROLES, type CliId, type RoleAssignments } from './types'

export type ConfigurationKind = 'provider_preset' | 'cli_preset' | 'custom_api' | 'custom_cli' | 'legacy_mixed'

export function configurationKindMatchesRoles(
  kind: ConfigurationKind,
  roles: RoleAssignments,
  ownerConnectionId: string | null,
  ownerCliId: CliId | null,
): boolean {
  if (kind === 'legacy_mixed') return false
  const targets = AI_ROLES.map(role => roles[role])
  if (kind === 'provider_preset') return Boolean(ownerConnectionId) && ownerCliId === null
    && targets.every(target => target.kind === 'provider_model' && target.connectionId === ownerConnectionId)
  if (kind === 'cli_preset') return Boolean(ownerCliId) && ownerConnectionId === null
    && targets.every(target => target.kind === 'local_cli' && target.cliId === ownerCliId)
  if (ownerConnectionId !== null || ownerCliId !== null) return false
  return targets.every(target => target.kind === (kind === 'custom_api' ? 'provider_model' : 'local_cli'))
}
