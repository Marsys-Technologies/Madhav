/**
 * Role-gated navigation helpers (Unit 3.consult_nav).
 *
 * Single source of truth for "which top-level surfaces does role R see?"
 * Used by AppShellRail + dashboard + tests. Pure logic — no Next/React.
 *
 * Roles:
 *   - super_admin: full instrument operator. Roster + Panchang + Cockpit +
 *     Audit + Performance + AIOps + Admin.
 *   - guest: legacy 'client' role rolled into 'guest' per Unit 2c. Sees only
 *     their owned + granted charts + the global Panchang surface.
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
}

export const NAV_ITEMS: readonly NavItemDescriptor[] = [
  { key: 'roster',      href: '/dashboard',   label: 'Roster',      roles: ['super_admin', 'guest'] },
  { key: 'panchang',    href: '/panchang',    label: 'Panchang',    roles: ['super_admin', 'guest'] },
  { key: 'cockpit',     href: '/cockpit',     label: 'Cockpit',     roles: ['super_admin'], admin: true },
  { key: 'audit',       href: '/audit',       label: 'Audit',       roles: ['super_admin'], admin: true },
  { key: 'aiops',       href: '/aiops',       label: 'AIOps',       roles: ['super_admin'], admin: true },
  { key: 'performance', href: '/performance', label: 'Performance', roles: ['super_admin'], admin: true },
  { key: 'admin',       href: '/admin',       label: 'Admin',       roles: ['super_admin'], admin: true },
] as const

export function visibleNavItems(role: NavRole | string): NavItemDescriptor[] {
  const normalized: NavRole = role === 'super_admin' ? 'super_admin' : 'guest'
  return NAV_ITEMS.filter((item) => (item.roles as readonly string[]).includes(normalized))
}

export function isAdminSurface(href: string): boolean {
  return NAV_ITEMS.find((i) => i.href === href)?.admin === true
}

/**
 * Legacy 'client' rolls into 'guest'; super_admin stays super_admin.
 * Tests + page-level role resolution use this to normalize.
 */
export function normalizeRole(raw: string | null | undefined): NavRole {
  return raw === 'super_admin' ? 'super_admin' : 'guest'
}
