// Derived metrics computed client-side from BuildState.
// These belong in the sidecar long-term but are derived here so the UI
// ships independently of sidecar changes.

import type { BuildState, SessionIndex } from './types'

const IST_OFFSET_MIN = 5 * 60 + 30

function toISTDateKey(iso: string | null | undefined): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (isNaN(d.getTime())) return null
  const istMs = d.getTime() + IST_OFFSET_MIN * 60 * 1000
  return new Date(istMs).toISOString().slice(0, 10)
}

export function todayISTKey(): string {
  return toISTDateKey(new Date().toISOString())!
}

export interface TodayProgress {
  date_key: string
  sessions_closed: SessionIndex[]
  files_touched_count: number
  deliverables: string[]
}

// Aggregate "what landed today" from sessions whose closed_at falls in current IST day.
// Prefers the sidecar-precomputed `today_progress` block when present (richer:
// includes files_touched_count); falls back to a client-side roll-up otherwise.
export function computeTodayProgress(state: BuildState): TodayProgress {
  const today = todayISTKey()
  const sessions_closed = state.sessions_index.filter(
    (s) => toISTDateKey(s.date) === today
  )

  const sidecar = state.today_progress
  if (sidecar && sidecar.date_key === today) {
    return {
      date_key: sidecar.date_key,
      sessions_closed,
      files_touched_count: sidecar.files_touched_count,
      deliverables: sidecar.deliverables,
    }
  }

  const deliverables = sessions_closed
    .map((s) => s.deliverable_one_liner)
    .filter((d): d is string => Boolean(d))
  return {
    date_key: today,
    sessions_closed,
    files_touched_count: 0,
    deliverables,
  }
}

export function phaseCompletionPercent(state: BuildState): number {
  const subs = state.phase_plan.sub_phases
  if (!subs.length) return 0
  const done = subs.filter((s) => s.status === 'completed').length
  return Math.round((done / subs.length) * 100)
}

export function macroCompletionPercent(state: BuildState): number {
  const arc = state.macro_phase.macro_arc
  if (!arc.length) return 0
  const closedMacros = arc.filter((m) => m.status === 'completed').length
  const activeEntry = arc.find((m) => m.status === 'active')
  const activeFraction = activeEntry ? phaseCompletionPercent(state) / 100 : 0
  return Math.round(((closedMacros + activeFraction) / arc.length) * 100)
}

// Convert a session_id like "S15-GOVERNANCE-BASELINE-CLOSE" into a friendly title.
export function friendlySessionTitle(s: SessionIndex): string {
  if (s.title) return s.title
  const id = s.session_id
  // Drop a leading "S<number>-" prefix and humanize.
  const stripped = id.replace(/^S\d+[-_]/i, '')
  const words = stripped.split(/[-_]/).filter(Boolean)
  if (!words.length) return id
  const cased = words
    .map((w, i) => (i === 0 ? w[0]!.toUpperCase() + w.slice(1).toLowerCase() : w.toLowerCase()))
    .join(' ')
  return cased
}

export function plainSummary(s: SessionIndex): string {
  return s.deliverable_one_liner ?? '—'
}

export function relativeDay(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const todayKey = todayISTKey()
  const dKey = toISTDateKey(iso)
  if (dKey === todayKey) return 'today'
  const days = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24))
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}
