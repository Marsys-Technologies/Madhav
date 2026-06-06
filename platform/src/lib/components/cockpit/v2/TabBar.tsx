'use client'

type Tab = 'data' | 'workflow' | 'agents'

interface Props {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

// Inline SVG components — 16×16 viewBox on 24px grid, currentColor
function IconDatabase() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
      <path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3" />
    </svg>
  )
}

function IconWorkflow() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="3" width="5" height="5" rx="1" />
      <rect x="16" y="3" width="5" height="5" rx="1" />
      <rect x="9.5" y="16" width="5" height="5" rx="1" />
      <path d="M5.5 8v3a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8" />
      <path d="M12 13v3" />
    </svg>
  )
}

function IconAgents() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="9" cy="7" r="4" />
      <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      <path d="M21 21v-2a4 4 0 0 0-3-3.85" />
    </svg>
  )
}

const TABS: { id: Tab; label: string; Icon: () => React.ReactElement }[] = [
  { id: 'data',     label: 'Data assets', Icon: IconDatabase },
  { id: 'workflow', label: 'Workflow',    Icon: IconWorkflow },
  { id: 'agents',   label: 'Agents',      Icon: IconAgents },
]

export function TabBar({ activeTab, onTabChange }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        gap: '4px',
        marginBottom: '8px',
        borderBottom: '1px solid var(--black-line)',
        paddingBottom: '0',
      }}
    >
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              fontFamily: 'var(--ui-stack)',
              cursor: 'pointer',
              border: 'none',
              borderBottom: isActive
                ? '2px solid var(--gold-engrave)'
                : '2px solid transparent',
              background: isActive ? 'var(--black-raised)' : 'transparent',
              color: isActive ? 'var(--gold-high)' : 'var(--on-dark-mut)',
              borderRadius: '4px 4px 0 0',
              transition: 'color 0.15s, background 0.15s',
            }}
          >
            <tab.Icon />
            <span>{tab.label}</span>
          </button>
        )
      })}
    </div>
  )
}
