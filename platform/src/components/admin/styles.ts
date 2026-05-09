// Shared Tailwind class strings for the admin module — keeps the bullion
// gold-on-black palette consistent across tables, dialogs, and buttons.

export const adminInput =
  'w-full rounded-[10px] border border-[rgba(var(--brand-gold-rgb),0.18)] bg-brand-ink px-3.5 py-3 text-sm text-brand-gold-cream placeholder:text-muted-foreground focus:border-brand-gold focus:outline-none focus:ring-2 focus:ring-brand-gold/20'

export const adminPrimaryBtn =
  'rounded-[10px] bg-gradient-to-b from-brand-gold-light to-brand-gold-deep px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.16em] text-brand-charcoal shadow-[0_0_0_1px_var(--brand-gold-hairline)] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50'

export const adminGhostBtn =
  'rounded-[10px] border border-[rgba(var(--brand-gold-rgb),0.22)] bg-transparent px-4 py-2.5 text-xs font-medium uppercase tracking-[0.16em] text-brand-gold transition-colors hover:border-brand-gold hover:text-brand-gold-cream disabled:cursor-not-allowed disabled:opacity-50'

export const adminDestructiveBtn =
  'rounded-[10px] border border-red-900/60 bg-transparent px-4 py-2.5 text-xs font-medium uppercase tracking-[0.16em] text-red-400 transition-colors hover:border-red-500 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-50'

export const adminCard =
  'rounded-2xl border border-[rgba(var(--brand-gold-rgb),0.15)] bg-brand-ink shadow-[0_2px_24px_rgba(0,0,0,0.4)]'

export const adminDialog =
  'border-[var(--brand-gold-hairline)] bg-brand-ink text-brand-gold-cream'

export const adminLabel = 'text-[11px] uppercase tracking-[0.18em] text-muted-foreground'

export const adminTableTh =
  'px-4 py-3 text-left text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground'

export const adminTableTd = 'px-4 py-3 text-sm text-brand-gold-cream'

export const adminTableRow = 'border-t border-[rgba(var(--brand-gold-rgb),0.12)] hover:bg-brand-ink/60'
