'use client'
import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { operatorActivityFilters } from '@/lib/admin/activity-filters'
export const ADMIN_BLOCKS = [
  { label: 'People and access', href: '/admin?tab=pending', description: 'Requests, users, chart access, AI grants, administration log and client keys.' },
  { label: 'Activity and AI accounting', href: '/admin/activity', description: 'Portal and selected-user activity, consumption and reconciliation.' },
  { label: 'System diagnostics', href: '/admin/foundation', description: 'Foundation, measured tool health and recorded query traces.' },
  { label: 'Assets, programme and learning', href: '/admin/assets', description: 'Canonical asset definitions, programme records and read-only learning evidence.' },
] as const
export function AdminNavigation() {
  const path = usePathname(), search = useSearchParams()
  const {userId} = useObservatoryScope()
  let activityQuery = ''
  if (path === '/admin/activity' || path === '/admin/analytics') {
    try { const filter=operatorActivityFilters(search,userId);const params=new URLSearchParams(filter.params)
      params.delete('userId');filter.navigation.forEach((value,key)=>params.set(key,value));activityQuery=`?${params}`
    } catch { /* Invalid saved filters are handled on the activity page. */ }
  }
  const block = path === '/admin' ? (search.get('tab') ? 'people' : 'overview') : path.includes('/users/') || path.includes('/mcp/keys') || path.includes('/administration-log') ? 'people' : path.includes('/activity') || path.includes('/analytics') ? 'activity' : path.includes('/foundation') || path.includes('/mcp/health') || path.includes('/trace') ? 'diagnostics' : 'assets'
  const sections: Record<string,{label:string;href:string}[]> = {
    people:[{label:'Access Requests',href:'/admin?tab=pending'},{label:'Users',href:'/admin?tab=users'},{label:'Chart Management',href:'/admin?tab=charts'},...(process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true' ? [{label:'AI Access',href:'/admin?tab=ai-access'}] : []),{label:'Administration Log',href:'/admin/administration-log'},{label:'MCP / Client Keys',href:'/admin/mcp/keys'}],
    activity:[{label:'System Observatory',href:'/admin/activity'+activityQuery},{label:'Analytics',href:'/admin/analytics'+activityQuery}],
    diagnostics:[{label:'System Foundation',href:'/admin/foundation'},{label:'MCP Health',href:'/admin/mcp/health'}],
    assets:[{label:'Asset Register',href:'/admin/assets'},{label:'Programme Record',href:'/admin/programme'},{label:'Learning Review',href:'/admin/learning'}],
  }
  return <><nav className="j6-nav" aria-label="Administration blocks">
    <Link href="/admin" aria-current={block === 'overview' ? 'page' : undefined}>Overview</Link>
    {ADMIN_BLOCKS.map(block => <Link key={block.href} href={block.href === '/admin/activity' ? block.href+activityQuery : block.href}>{block.label}</Link>)}
    <Link href="/account">My Account</Link>
  </nav>{sections[block] && <nav className="j6-links" aria-label="Block sections">{sections[block].map(section => <Link key={section.href} href={section.href}>{section.label}</Link>)}</nav>}</>
}
