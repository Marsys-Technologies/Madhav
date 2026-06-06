'use client'

import { motion } from 'framer-motion'

interface AssetProgressBarProps {
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated'
  actualRows: number | null
  targetVolume: number | null
}

const STATE_COLORS: Record<string, {
  fill: string; stroke: string; pill: string; pillColor: string
}> = {
  dormant:      { fill: 'rgba(122,86,24,0.0)',    stroke: 'rgba(122,86,24,0.4)',    pill: 'NOT BUILT',     pillColor: 'rgba(155,131,80,0.8)' },
  building:     { fill: 'rgba(212,166,72,0.6)',    stroke: 'rgba(212,166,72,0.8)',   pill: 'BUILDING',      pillColor: 'rgba(120,180,255,0.9)' },
  lit:          { fill: 'rgba(236,197,106,0.85)',  stroke: 'rgba(236,197,106,1.0)',  pill: 'LIVE',          pillColor: 'rgba(140,210,140,0.95)' },
  stale:        { fill: 'rgba(212,140,72,0.6)',    stroke: 'rgba(212,140,72,0.8)',   pill: 'OUT OF SYNC',   pillColor: 'rgba(232,180,108,0.95)' },
  error:        { fill: 'rgba(232,108,108,0.55)',  stroke: 'rgba(232,108,108,0.85)', pill: 'FAILED',        pillColor: 'rgba(232,108,108,1)' },
  not_migrated: { fill: 'rgba(80,70,50,0.0)',      stroke: 'rgba(80,70,50,0.3)',     pill: 'NOT MIGRATED',  pillColor: 'rgba(120,110,90,0.7)' },
}

export function AssetProgressBar({ state, actualRows, targetVolume }: AssetProgressBarProps) {
  const colors = STATE_COLORS[state] ?? STATE_COLORS.dormant
  const pct = (actualRows !== null && targetVolume && targetVolume > 0)
    ? Math.min(100, Math.round((actualRows / targetVolume) * 100))
    : 0

  const numericText = (actualRows !== null && targetVolume)
    ? `${actualRows.toLocaleString()} / ${targetVolume.toLocaleString()}`
    : (actualRows !== null ? actualRows.toLocaleString() : '—')

  return (
    <div className="relative h-[22px] w-full">
      {/* Track */}
      <div
        className="absolute inset-0 rounded-[3px] border"
        style={{ borderColor: colors.stroke, background: 'rgba(15,12,8,0.6)' }}
      />

      {/* Fill — animated width */}
      <motion.div
        className="absolute top-0 bottom-0 left-0 rounded-l-[3px]"
        style={{ background: colors.fill }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      />

      {/* Building shimmer overlay */}
      {state === 'building' && (
        <motion.div
          className="absolute inset-0 rounded-[3px] pointer-events-none overflow-hidden"
        >
          <motion.div
            className="absolute top-0 bottom-0 w-[40%]"
            style={{
              background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.18) 50%, transparent 100%)',
            }}
            animate={{ left: ['-40%', '140%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
        </motion.div>
      )}

      {/* Numeric overlay — centered monospace */}
      <div className="absolute inset-0 flex items-center justify-center px-2 font-mono text-[10px] text-white/85">
        {numericText}
      </div>

      {/* State pill — right edge inside the bar */}
      <div
        className="absolute top-[2px] right-[2px] bottom-[2px] flex items-center px-1.5 rounded-[2px] font-mono text-[8px] uppercase"
        style={{
          background: 'rgba(10,8,6,0.85)',
          color: colors.pillColor,
          letterSpacing: '0.06em',
        }}
      >
        {colors.pill}
      </div>
    </div>
  )
}
