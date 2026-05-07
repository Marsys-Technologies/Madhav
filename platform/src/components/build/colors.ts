// Build tracker color system — single source of truth.
// Status values resolve via CSS design tokens defined in globals.css.

export const statusColors = {
  completed:   'var(--status-success)',
  active:      'var(--brand-gold)',
  in_progress: 'var(--brand-gold)',
  pending:     'var(--muted-foreground)',
  blocked:     'var(--status-halt)',
  unknown:     'var(--muted-foreground)',
} as const

export const statusBg = {
  completed:   'bg-status-success-bg',
  active:      'bg-[rgba(var(--brand-gold-rgb),0.15)]',
  in_progress: 'bg-[rgba(var(--brand-gold-rgb),0.15)]',
  pending:     'bg-muted',
  blocked:     'bg-status-halt-bg',
  unknown:     'bg-muted',
} as const

export const statusText = {
  completed:   'text-status-success',
  active:      'text-brand-gold',
  in_progress: 'text-brand-gold',
  pending:     'text-muted-foreground',
  blocked:     'text-status-halt',
  unknown:     'text-muted-foreground',
} as const

// CHART_PALETTE — hex literals intentionally kept for recharts SVG stroke/fill props.
// CSS variable references cannot be passed to recharts data-series color props directly.
// Session-class palette — 8 classes from SESSION_LOG_SCHEMA enum
export const classColors: Record<string, string> = {
  m2_corpus_execution:  '#3b82f6',  // blue
  governance_aside:     '#a855f7',  // purple
  planning_only:        '#06b6d4',  // cyan
  fix_session:          '#f97316',  // orange
  red_team:             '#ef4444',  // red
  brief_authoring:      '#84cc16',  // yellow-green
  native_intervention:  '#ec4899',  // pink
  cowork_orchestration: '#78716c',  // warm-neutral
  unknown:              '#a8a29e',
}

export function getClassColor(cls: string): string {
  return classColors[cls] ?? classColors.unknown
}

// Is this class "on-plan" (M2 corpus work) or "off-plan" (meta / infra)?
export function isOnPlan(cls: string): boolean {
  return cls === 'm2_corpus_execution'
}

// CHART_PALETTE — hex literals kept for recharts SVG props (see note above).
// Severity palette for governance findings
export const severityColors = {
  baseline: '#22c55e',  // green — exit 2, accepted residuals
  medium:   '#f59e0b',  // amber — new findings
  high:     '#ef4444',  // red — regressions
  info:     '#78716c',  // neutral
} as const

// CHART_PALETTE — hex literals kept for recharts SVG props (see note above).
// Exit code → color mapping (used by health trends)
export const exitCodeColor: Record<number, string> = {
  0: '#22c55e',
  1: '#86efac',
  2: '#fbbf24',
  3: '#f97316',
  4: '#ef4444',
}

// Status → short label
export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    completed: 'Done',
    active: 'Active',
    in_progress: 'In progress',
    pending: 'Pending',
    blocked: 'Blocked',
    unknown: '—',
  }
  return map[status] ?? status.replace(/_/g, ' ')
}
