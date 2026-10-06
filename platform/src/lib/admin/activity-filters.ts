import { personalActivityFilters } from '@/lib/account/activity-filters'
import { z } from 'zod'

/** UI state is distinct from the API authority; only the guarded operator API consumes userId. */
export function operatorActivityFilters(search: Pick<URLSearchParams, 'get'>, actorId: string, now = new Date()) {
  const scope = z.enum(['mine','portal','user']).parse(search.get('scope') ?? (search.get('userId') ? 'user' : 'portal'))
  const selected = z.string().max(512).parse(search.get('userId') ?? '').trim()
  const target = scope === 'mine' ? actorId : scope === 'user' ? selected : null
  const params = personalActivityFilters(search, now)
  if (target) params.set('userId', target)
  const navigation = new URLSearchParams({ scope })
  if (scope === 'user' && selected) navigation.set('userId', selected)
  return { scope, target, params, navigation, ready: scope !== 'user' || Boolean(selected) }
}
