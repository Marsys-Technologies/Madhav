'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { ScopedActivity } from '@/components/account/PersonalActivity'
import { operatorActivityFilters } from '@/lib/admin/activity-filters'
import { PageTitle } from '@/components/journey1/Titles'
import { AccountingRecords } from './AccountingRecords'

export function OperatorActivity({ view }: { view: 'observatory' | 'consumption' }) {
  const search = useSearchParams(), router = useRouter(), path = usePathname()
  const { userId, users, usersLoading, usersError } = useObservatoryScope()
  const [now] = useState(() => new Date())
  let filter: ReturnType<typeof operatorActivityFilters>
  try { filter = operatorActivityFilters(search, userId, now) } catch {
    return <div role="alert" className="j5-panel">Choose a valid scope and a period of up to 90 days. <Link href={path}>Reset filters</Link></div>
  }
  const label = filter.scope === 'portal' ? 'Portal activity · all users and unattributed records'
    : filter.scope === 'mine' ? 'My activity · your recorded calls only'
    : `Selected user activity · ${users.find(user => user.id === filter.target)?.name ?? (filter.target || 'choose a user')}`
  function change(scope: string, selected = '') {
    const params = new URLSearchParams(filter.params)
    params.delete('userId')
    params.set('scope', scope)
    if (scope === 'user' && selected) params.set('userId', selected)
    router.push(`${path}?${params}`, { scroll: false })
  }
  const shared = new URLSearchParams(filter.params)
  shared.delete('userId')
  const personal = shared.toString()
  filter.navigation.forEach((value,key) => shared.set(key,value))
  return <>
    <PageTitle name={view === 'observatory' ? 'systemObservatory' : 'analytics'} />
    <p className="j1-note">One activity ledger across My Account and Administration. Selected-user inspection does not change that person’s preferences, personas or AI defaults.</p>
    <div className="j6-scope">
      <label>Activity scope<select value={filter.scope} onChange={event => change(event.target.value)}>
        <option value="portal">Portal activity</option><option value="mine">My activity</option><option value="user">Selected user activity</option>
      </select></label>
      {filter.scope === 'user' && <label>Selected user<select value={filter.target ?? ''} onChange={event => change('user',event.target.value)}>
        <option value="">Choose a user</option>{users.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
      </select></label>}
    </div>
    {filter.scope === 'user' && usersLoading && <p role="status">Loading user choices…</p>}
    {filter.scope === 'user' && usersError && <p role="alert">User choices could not be read. Reload to try again. A bookmarked selection retains its recorded identity.</p>}
    <p className="j5-eyebrow">{label}</p>
    <div className="j6-links">
      <Link href={`/admin/activity?${shared}`}>System Observatory</Link>
      <Link href={`/admin/analytics?${shared}`}>Consumption and reconciliation</Link>
      <Link href={`/account/ai-cockpit/${view}?${personal}`}>Open my activity</Link>
    </div>
    {filter.ready ? <ScopedActivity key={`${userId}:${view}:${filter.params}`} operator view={view} params={filter.params} scopeLabel={label} authorityParams={filter.navigation} />
      : <div className="j5-panel">Choose a user to inspect recorded activity.</div>}
    {view === 'consumption' && <AccountingRecords />}
  </>
}
