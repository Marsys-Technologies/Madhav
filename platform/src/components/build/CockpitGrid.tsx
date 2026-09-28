import type { BuildState } from '@/lib/build/types'
import { JourneyStrip } from './JourneyStrip'
import { ProgressBar } from './ProgressBar'
import { CorpusDensityHero } from './CorpusDensityHero'
import { BuildVelocityStrip } from './BuildVelocityStrip'
import { InsightCards } from './InsightCards'
import { deriveInsights } from '@/lib/build/insights'
import { ActiveChartsWidget } from './ActiveChartsWidget'
import { getClassColor } from './colors'
import {
  computeTodayProgress,
  phaseCompletionPercent,
  macroCompletionPercent,
  friendlySessionTitle,
  plainSummary,
  relativeDay,
} from '@/lib/build/derive'

function Card({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`rounded-lg border border-border bg-card p-4 ${className}`}>
      {children}
    </div>
  )
}

function ClassPill({ cls }: { cls: string }) {
  const color = getClassColor(cls)
  const label = cls.replace(/_/g, ' ').replace(/m2 corpus/, 'corpus')
  return (
    <span
      className="bt-label shrink-0 rounded-full px-2 py-0.5"
      style={{ background: `${color}22`, color }}
    >
      {label}
    </span>
  )
}

export function CockpitGrid({ state }: { state: BuildState }) {
  const {
    macro_phase,
    phase_plan,
    last_session,
    next_session,
    sessions_index,
    current_brief,
    staleness_register,
    native_directives,
    corpus_state,
  } = state

  const today = computeTodayProgress(state)
  const macroPct = macroCompletionPercent(state)
  const phasePct = phaseCompletionPercent(state)
  const insights = deriveInsights(state)

  const lastSessionIndex = last_session
    ? sessions_index.find((s) => s.session_id === last_session.id)
    : undefined
  const lastTitle = lastSessionIndex ? friendlySessionTitle(lastSessionIndex) : last_session?.id
  const lastSummary =
    last_session?.deliverable_summary ??
    (lastSessionIndex ? plainSummary(lastSessionIndex) : '—')

  // AC.15: show 7 sessions (newest-first; sessions_index is already sorted newest-first)
  const recent = sessions_index.slice(0, 7)
  const openNDs = native_directives.entries.filter((d) => d.status === 'open')

  return (
    <div className="space-y-6">
      {/* Journey strip */}
      <section>
        <p className="bt-label mb-2">The journey</p>
        <JourneyStrip arc={macro_phase.macro_arc} activeId={macro_phase.id} />
      </section>

      {/* AC.12: Corpus density hero */}
      <section>
        <p className="bt-label mb-3">What&apos;s been built</p>
        <CorpusDensityHero corpus={corpus_state} />
      </section>

      {/* Where I am + Today's progress */}
      <section className="grid gap-4 lg:grid-cols-3">
        {/* Where I am — wide */}
        <Card className="lg:col-span-2">
          <p className="bt-label mb-3">Where I am</p>

          <div className="space-y-5">
            {/* Active phase */}
            <div>
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="bt-heading">
                  {macro_phase.id} — {macro_phase.title}
                </h2>
                <span className="bt-body text-muted-foreground">
                  Sub-phase {phase_plan.sub_phase} · {phase_plan.status.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="mt-3 space-y-2">
                <ProgressBar
                  percent={phasePct}
                  label={`Sub-phases completed in ${macro_phase.id}`}
                  tone="active"
                />
                <ProgressBar
                  percent={macroPct}
                  label="Overall journey (M1 → M10)"
                />
              </div>
            </div>

            {/* Just finished + Working on next */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="bt-label mb-1.5">Just finished</p>
                {last_session ? (
                  <div>
                    <p className="bt-body font-medium">{lastTitle}</p>
                    <p className="bt-body mt-0.5 text-muted-foreground line-clamp-2">
                      {lastSummary}
                    </p>
                    <p className="bt-label mt-1">{relativeDay(last_session.closed_at)}</p>
                  </div>
                ) : (
                  <p className="bt-body text-muted-foreground">—</p>
                )}
              </div>

              <div>
                <p className="bt-label mb-1.5">Working on next</p>
                {next_session?.objective ? (
                  <div>
                    <p className="bt-body line-clamp-3">
                      {next_session.objective}
                    </p>
                    {next_session.proposed_cowork_thread_name && (
                      <p className="bt-label mt-1">
                        thread · {next_session.proposed_cowork_thread_name}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="bt-body text-muted-foreground">No objective set.</p>
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* Today's progress */}
        <Card>
          <div className="flex items-baseline justify-between">
            <p className="bt-label">Today</p>
            <p className="bt-label">{today.date_key}</p>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-3">
            <div>
              <p className="bt-num">{today.sessions_closed.length}</p>
              <p className="bt-body text-muted-foreground">
                {today.sessions_closed.length === 1 ? 'session' : 'sessions'}
              </p>
            </div>
            <div>
              <p className="bt-num">{today.deliverables.length}</p>
              <p className="bt-body text-muted-foreground">
                {today.deliverables.length === 1 ? 'deliverable' : 'deliverables'}
              </p>
            </div>
            <div>
              <p className="bt-num">{today.files_touched_count}</p>
              <p className="bt-body text-muted-foreground">
                {today.files_touched_count === 1 ? 'file' : 'files'}
              </p>
            </div>
          </div>
          {today.deliverables.length > 0 ? (
            <ul className="mt-4 space-y-1.5 border-t border-border pt-3">
              {today.deliverables.slice(0, 5).map((d, i) => (
                <li key={i} className="bt-body line-clamp-2 before:mr-2 before:content-['·']">
                  {d}
                </li>
              ))}
            </ul>
          ) : (
            <p className="bt-body mt-4 border-t border-border pt-3 text-muted-foreground">
              Nothing closed yet today.
            </p>
          )}
        </Card>
      </section>

      {/* AC.13: Build velocity strip */}
      <BuildVelocityStrip sessions={sessions_index} />

      {/* AC.14: Insight cards */}
      {insights.length > 0 && <InsightCards insights={insights} />}

      {/* Priorities + Pending */}
      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <p className="bt-label mb-3">Immediate priorities</p>
          {current_brief ? (
            <div className="space-y-2">
              <p className="bt-body">
                Active brief:{' '}
                <span className="font-medium">
                  {current_brief.session_id}
                </span>
              </p>
              <p className="bt-body text-muted-foreground">
                {current_brief.ac_passed_known} of {current_brief.ac_total} acceptance criteria
                verified.
              </p>
              {current_brief.may_touch?.length > 0 && (
                <p className="bt-body text-muted-foreground">
                  In scope: {current_brief.may_touch.slice(0, 3).join(', ')}
                  {current_brief.may_touch.length > 3 ? ' …' : ''}
                </p>
              )}
            </div>
          ) : (
            <p className="bt-body text-muted-foreground">No active brief.</p>
          )}

          {openNDs.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="bt-label mb-2">Open instructions from you</p>
              <ul className="space-y-1">
                {openNDs.slice(0, 4).map((nd) => (
                  <li key={nd.nd_id} className="bt-body">
                    {nd.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>

        <Card>
          <p className="bt-label mb-3">Pending / carry-forward</p>
          {staleness_register.length === 0 ? (
            <p className="bt-body text-muted-foreground">Nothing flagged stale.</p>
          ) : (
            <ul className="space-y-2">
              {staleness_register.slice(0, 5).map((s) => (
                <li key={s.path}>
                  <p className="bt-body line-clamp-1">{s.reason}</p>
                  <p className="bt-label mt-0.5">{s.path.split('/').pop()}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>

      {/* R6: Active charts — live links into per-chart profiles */}
      <ActiveChartsWidget />

      {/* AC.15: Recent activity — 7 sessions with class pills */}
      <section>
        <p className="bt-label mb-3">Recent activity</p>
        <Card className="p-0">
          {recent.length === 0 ? (
            <p className="bt-body p-4 text-muted-foreground">No sessions yet.</p>
          ) : (
            <ul className="divide-y divide-border">
              {recent.map((s) => (
                <li key={s.session_id} className="px-4 py-2.5 first:pt-3 last:pb-3">
                  <div className="flex items-baseline gap-3">
                    <span className="bt-label w-20 shrink-0">{relativeDay(s.date)}</span>
                    <div className="min-w-0 flex-1">
                      <p className="bt-body font-medium">
                        {friendlySessionTitle(s)}
                      </p>
                      <p className="bt-body line-clamp-1 text-muted-foreground">
                        {plainSummary(s)}
                      </p>
                    </div>
                    <ClassPill cls={s.class} />
                    {s.phase_id && (
                      <span className="bt-label shrink-0">{s.phase_id}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>
    </div>
  )
}
