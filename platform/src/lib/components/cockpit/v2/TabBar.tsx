'use client'

type Tab = 'data' | 'workflow' | 'agents'

interface Props {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

const TABS: { id: Tab; label: string; emoji: string }[] = [
  { id: 'data', label: 'Data Assets', emoji: '🗄️' },
  { id: 'workflow', label: 'Workflow', emoji: '🔄' },
  { id: 'agents', label: 'Agents', emoji: '👥' },
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
            <span>{tab.emoji}</span>
            <span>{tab.label}</span>
          </button>
        )
      })}
    </div>
  )
}
