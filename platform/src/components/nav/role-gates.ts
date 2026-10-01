/**
 * Role-gated navigation helpers (Unit 3.consult_nav).
 *
 * Single source of truth for "which top-level surfaces does role R see?"
 * Used by AppShellRail + dashboard + tests. Pure logic — no Next/React.
 *
 * Roles:
 *   - super_admin: full instrument operator. Jātakas + Panchang + Cockpit +
 *     Audit + Performance + Admin. AI Console and Observatory live inside
 *     Cockpit.
 *   - guest: legacy 'client' role rolled into 'guest' per Unit 2c. Sees their
 *     owned + granted charts, Panchang, and AI Console when it is enabled.
 *
 * Per-chart visibility (Build vs Profile/Consult/Panchang) is decided by
 * `authorizeChartAccess` (2c) at the per-chart layout level. This helper only
 * answers the top-level nav question.
 *
 * No tier/depth selector anywhere — tier excision is a concurrent unit
 * (3.tier_excision); this module never branches on a tier value.
 */

export type NavRole = 'super_admin' | 'guest'

export interface NavItemDescriptor {
  key: string
  href: string
  label: string
  /** Roles permitted to see this top-level nav entry. */
  roles: readonly NavRole[]
  /** Admin surface? Helps tests assert "guest does not see admin." */
  admin?: boolean
  /** Optional public client-side feature visibility gate. */
  feature?: 'aiConsoleByok' | 'aiMetering'
}

export interface NavVisibility {
  aiConsoleByok?: boolean
  aiMetering?: boolean
}

export interface InformationNavItemDescriptor {
  key: string
  href: string
  label: string
  roles: readonly NavRole[]
  admin?: boolean
}

export const NAV_ITEMS: readonly NavItemDescriptor[] = [
  { key: 'roster',      href: '/dashboard',   label: 'Jātakas',     roles: ['super_admin', 'guest'] },
  { key: 'panchang',    href: '/panchang',    label: 'Panchang',    roles: ['super_admin', 'guest'] },
  { key: 'cockpit',     href: '/cockpit',     label: 'Cockpit',     roles: ['super_admin'], admin: true },
  // Super Admin reaches AI Console through Cockpit's section menu. Guests keep
  // this direct entry because Cockpit itself is an admin-only surface.
  { key: 'ai-console',  href: '/ai-console',  label: 'AI Console',  roles: ['guest'], feature: 'aiConsoleByok' },
  { key: 'usage', href: '/usage', label: 'My AI usage', roles: ['super_admin','guest'], feature: 'aiMetering' },
  { key: 'audit',       href: '/audit',       label: 'Audit',       roles: ['super_admin'], admin: true },
  { key: 'performance', href: '/performance', label: 'Performance', roles: ['super_admin'], admin: true },
  { key: 'admin',       href: '/admin',       label: 'Admin',       roles: ['super_admin'], admin: true },
] as const

/**
 * Secondary destinations shown beneath the bottom-aligned Information rail item.
 * Keep this ordered: the first item is the top entry in the Information menu.
 */
export const INFORMATION_NAV_ITEMS: readonly InformationNavItemDescriptor[] = [
  {
    key: 'atlas',
    href: '/information/atlas',
    label: 'Atlas',
    roles: ['super_admin'],
    admin: true,
  },
] as const

export function visibleNavItems(
  role: NavRole | string,
  visibility: NavVisibility = {},
): NavItemDescriptor[] {
  const normalized: NavRole = role === 'super_admin' ? 'super_admin' : 'guest'
  return NAV_ITEMS.filter((item) => {
    if (!(item.roles as readonly string[]).includes(normalized)) return false
    if (item.feature === 'aiMetering') return visibility.aiMetering === true
    if (item.feature === 'aiConsoleByok') return visibility.aiConsoleByok === true
    return true
  })
}

export function visibleInformationNavItems(
  role: NavRole | string
): InformationNavItemDescriptor[] {
  const normalized: NavRole = role === 'super_admin' ? 'super_admin' : 'guest'
  return INFORMATION_NAV_ITEMS.filter((item) =>
    (item.roles as readonly string[]).includes(normalized)
  )
}

/** Cockpit remains the selected parent while one of its child instruments is open. */
export function isNavItemActive(key: string, href: string, pathname: string): boolean {
  if (key === 'roster') return pathname === '/dashboard' || pathname === '/'
  if (key === 'cockpit') {
    return pathname.startsWith('/cockpit') || pathname.startsWith('/ai-console')
      || pathname.startsWith('/observatory')
  }
  return pathname.startsWith(href)
}

export function isAdminSurface(href: string): boolean {
  return (
    NAV_ITEMS.find((item) => item.href === href)?.admin === true ||
    INFORMATION_NAV_ITEMS.find((item) => item.href === href)?.admin === true
  )
}

/**
 * Legacy 'client' rolls into 'guest'; super_admin stays super_admin.
 * Tests + page-level role resolution use this to normalize.
 */
export function normalizeRole(raw: string | null | undefined): NavRole {
  return raw === 'super_admin' ? 'super_admin' : 'guest'
}
