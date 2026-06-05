'use client'

const SWARM_ROLES = [
  'Sūtradhāra',
  'Śilpī',
  'Pramāṇa',
  'Sambandha',
  'Smṛti',
  'Nirīkṣaka',
  'Racayitā',
  'Pratiṣṭhā',
  'Drashta',
  'Darpaṇa',
  'Praharī',
  'Vimarśaka',
  'Tier-1 Severity Remediator',
]

export function AgentsView() {
  return (
    <div
      style={{
        padding: '32px 24px',
        color: 'var(--on-dark-mut)',
        fontFamily: 'var(--ui-stack)',
      }}
    >
      <p style={{ fontSize: '14px' }}>Agent activity — coming in M7</p>
      <p
        style={{
          fontSize: '12px',
          marginTop: '8px',
          color: 'var(--on-dark-faint)',
        }}
      >
        Swarm roles: {SWARM_ROLES.join(' · ')}
      </p>
    </div>
  )
}
