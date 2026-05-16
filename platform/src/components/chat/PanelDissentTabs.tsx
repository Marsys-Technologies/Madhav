'use client'

/**
 * PanelDissentTabs — γ1
 *
 * Tabbed view of per-member panel answers and the adjudicator rationale footer.
 *
 * Disclosure tier gating:
 *   super_admin  — full member answer text + model IDs shown
 *   all others   — "Panel dissent summary" with member count + alignment note;
 *                  individual answers redacted to a single-line blurb.
 */

import { useState } from 'react'
import type { PanelMemberPart } from '@/lib/streams/data_parts'

interface PanelDissentTabsProps {
  members: PanelMemberPart[]
  adjudicatorRationale?: string
  /** Whether the viewing user is super_admin. */
  isSuperAdmin: boolean
  'data-testid'?: string
}

function MemberLabel({
  member,
  isSuperAdmin,
}: {
  member: PanelMemberPart
  isSuperAdmin: boolean
}) {
  if (isSuperAdmin) {
    return (
      <span>
        <span className="font-mono text-[10px] opacity-70 mr-1">{member.provider_family}</span>
        {member.model_id.split('/').pop() ?? `M${member.member_index + 1}`}
      </span>
    )
  }
  return <span>Member {member.member_index + 1}</span>
}

function MemberContent({
  member,
  isSuperAdmin,
}: {
  member: PanelMemberPart
  isSuperAdmin: boolean
}) {
  if (member.status === 'failed') {
    return (
      <p className="text-xs text-red-400 italic py-2">
        This panel member failed to respond.
      </p>
    )
  }

  if (!isSuperAdmin) {
    return (
      <div className="py-2">
        <p className="text-xs text-zinc-500 italic">
          Panel member responses are restricted to super-admin tier.
        </p>
        <p className="mt-1 text-[10px] text-zinc-600">
          Latency: {member.latency_ms.toLocaleString()} ms
        </p>
      </div>
    )
  }

  return (
    <div className="py-2 space-y-1">
      <p className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
        {member.answer ?? '(no content)'}
      </p>
      <p className="text-[10px] text-zinc-600 pt-1">
        Latency: {member.latency_ms.toLocaleString()} ms
      </p>
    </div>
  )
}

function NonAdminSummary({ members }: { members: PanelMemberPart[] }) {
  const succeeded = members.filter(m => m.status === 'success').length
  const failed = members.filter(m => m.status === 'failed').length
  return (
    <div className="px-3 py-3 text-xs text-zinc-400 space-y-1">
      <p>
        <span className="text-zinc-200 font-medium">{members.length}</span> panel members contributed to this answer.
      </p>
      <p>
        {succeeded} responded successfully{failed > 0 ? `; ${failed} failed` : ''}.
        Individual responses are restricted to super-admin tier.
      </p>
    </div>
  )
}

export function PanelDissentTabs({
  members,
  adjudicatorRationale,
  isSuperAdmin,
  'data-testid': testId,
}: PanelDissentTabsProps) {
  const [activeTab, setActiveTab] = useState(0)

  if (members.length === 0) return null

  const tabIds = members.map((_, i) => `panel-member-tab-${i}`)
  const panelIds = members.map((_, i) => `panel-member-panel-${i}`)

  return (
    <div
      id="panel-dissent-tabs"
      className="rounded-md border border-zinc-800 bg-zinc-900/50 overflow-hidden"
      data-testid={testId ?? 'panel-dissent-tabs'}
      role="region"
      aria-label="Panel dissent"
    >
      {/* Tab list — always rendered for screen readers */}
      {isSuperAdmin ? (
        <>
          <div
            className="flex border-b border-zinc-800 overflow-x-auto"
            role="tablist"
            aria-label="Panel member responses"
          >
            {members.map((member, i) => (
              <button
                key={member.member_index}
                type="button"
                role="tab"
                id={tabIds[i]}
                aria-controls={panelIds[i]}
                aria-selected={activeTab === i}
                onClick={() => setActiveTab(i)}
                className={`shrink-0 px-3 py-2 text-xs font-medium transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-indigo-400 ${
                  activeTab === i
                    ? 'border-b-2 border-indigo-400 text-indigo-300 bg-indigo-900/10'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                } ${member.status === 'failed' ? 'text-red-400' : ''}`}
                data-testid={`panel-tab-${i}`}
              >
                <MemberLabel member={member} isSuperAdmin={isSuperAdmin} />
                {member.status === 'failed' && (
                  <span className="ml-1 text-[9px] text-red-400" aria-label="failed">✕</span>
                )}
              </button>
            ))}
          </div>

          {/* Tab panels */}
          {members.map((member, i) => (
            <div
              key={member.member_index}
              role="tabpanel"
              id={panelIds[i]}
              aria-labelledby={tabIds[i]}
              hidden={activeTab !== i}
              className="px-3"
              data-testid={`panel-panel-${i}`}
            >
              <MemberContent member={member} isSuperAdmin={isSuperAdmin} />
            </div>
          ))}
        </>
      ) : (
        <NonAdminSummary members={members} />
      )}

      {/* Adjudicator rationale footer — super_admin only */}
      {isSuperAdmin && adjudicatorRationale && (
        <div className="border-t border-zinc-800 px-3 py-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600 mb-1">
            Adjudicator rationale
          </p>
          <p className="text-xs text-zinc-400 whitespace-pre-wrap leading-relaxed">
            {adjudicatorRationale}
          </p>
        </div>
      )}
    </div>
  )
}
