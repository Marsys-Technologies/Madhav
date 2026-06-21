'use client'

import { motion, AnimatePresence } from 'framer-motion'

interface AssetProgressBarProps {
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated' | 'reconnecting'
  actualRows: number | null
  targetVolume: number | null
}

const STATE_COLORS: Record<string, {
  fill: string; stroke: string; pill: string; pillColor: string
}> = {
  dormant:      { fill: 'rgba(122,86,24,0.0)',    stroke: 'rgba(122,86,24,0.4)',    pill: 'NOT BUILT',     pillColor: 'rgba(155,131,80,0.8)' },
  building:     { fill: 'rgba(168,124,48,0.7)',    stroke: 'rgba(200,154,70,0.75)',  pill: 'BUILDING',      pillColor: 'rgba(236,197,106,0.95)' },
  lit:          { fill: 'rgba(176,137,58,0.92)',   stroke: 'rgba(212,166,72,0.9)',   pill: 'LIVE',          pillColor: 'rgba(140,210,140,0.95)' },
  stale:        { fill: 'rgba(166,108,52,0.7)',    stroke: 'rgba(196,128,64,0.75)',  pill: 'OUT OF SYNC',   pillColor: 'rgba(232,180,108,0.95)' },
  error:        { fill: 'rgba(232,108,108,0.55)',  stroke: 'rgba(232,108,108,0.85)', pill: 'FAILED',        pillColor: 'rgba(232,108,108,1)' },
  not_migrated: { fill: 'rgba(80,70,50,0.0)',      stroke: 'rgba(80,70,50,0.3)',     pill: 'NOT MIGRATED',  pillColor: 'rgba(120,110,90,0.7)' },
  reconnecting: { fill: 'rgba(236,197,106,0.1)',   stroke: 'rgba(236,197,106,0.4)', pill: 'RECONNECTING',  pillColor: 'rgba(236,197,106,0.9)' },
}

export function AssetProgressBar({ state, actualRows, targetVolume }: AssetProgressBarProps) {
  const colors = STATE_COLORS[state] ?? STATE_COLORS.dormant
  const pct = (actualRows !== null && targetVolume && targetVolume > 0)
    ? Math.min(100, Math.round((actualRows / targetVolume) * 100))
    : (state === 'lit' && actualRows != null && actualRows > 0 ? 100 : 0)

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

      {/* Fill — full-width track scaled on X (transform, not layout-triggering width) */}
      <motion.div
        className="absolute top-0 bottom-0 left-0 right-0 rounded-l-[3px] origin-left"
        style={{ background: colors.fill }}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: pct / 100 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
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

      {/* Numeric overlay — centered monospace. Right padding reserves room for
          the state pill so the centered text never collides with it; the text
          shadow keeps it legible over both filled and unfilled portions. */}
      <div
        className="absolute inset-0 flex items-center justify-center pl-2 pr-[60px] font-mono text-[10px] text-white"
        style={{ textShadow: '0 1px 2px rgba(0,0,0,0.6)' }}
      >
        {numericText}
      </div>

      {/* State pill — right edge inside the bar; label cross-fades on state change */}
      <div
        className="absolute top-[2px] right-[2px] bottom-[2px] flex items-center px-1.5 rounded-[2px] font-mono text-[8px] uppercase overflow-hidden"
        style={{ background: 'rgba(10,8,6,0.85)', letterSpacing: '0.06em' }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={colors.pill}
            initial={{ opacity: 0, y: 3 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            style={{ color: colors.pillColor, display: 'block' }}
          >
            {colors.pill}
          </motion.span>
        </AnimatePresence>
      </div>
    </div>
  )
}
