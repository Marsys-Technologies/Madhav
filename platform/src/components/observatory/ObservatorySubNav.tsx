'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/observatory', label: 'Overview' },
  { href: '/observatory/analytics', label: 'Analytics' },
  { href: '/observatory/consumption', label: 'Consumption' },
]

export function ObservatorySubNav() {
  const pathname = usePathname()
  return (
    <nav aria-label="Observatory sections" className="flex flex-wrap gap-1 border-b border-[#392c16] px-4 py-2 sm:px-8">
      {links.map(({ href, label }) => {
        const active = pathname === href
        return <Link key={href} href={href} aria-current={active ? 'page' : undefined}
          className={`rounded-md px-4 py-2 text-sm transition-colors ${active ? 'bg-[#a87c2a] text-[#0a0806]' : 'text-[#c9b482] hover:bg-[#211a10] hover:text-[#ecc56a]'}`}>{label}</Link>
      })}
    </nav>
  )
}
