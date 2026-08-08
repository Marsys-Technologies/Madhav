import type { ForensicChart } from '@/lib/forensic/snapshot'
import { cn } from '@/lib/utils'
import { grahaCodeOf } from '@/lib/retrieval/address_resolver'

export interface RasiChartSVGProps {
  chart: ForensicChart
  size?: number
  style?: 'north' | 'south'
  className?: string
  paused?: boolean
}

// Abbreviated display names for planets. Derived from the graha SSoT
// (address_resolver.grahaCodeOf) rather than hardcoded literals —
// ADHIṢṬHĀNA Lane A2: the SSoT's own canonical short code's first 2
// characters, Title-cased, always yield this component's established
// 2-letter display convention.
const ABBREV: Record<string, string> = Object.fromEntries(
  ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].map(name => {
    const short = grahaCodeOf(name).slice(0, 2)
    return [name, short.charAt(0) + short.slice(1).toLowerCase()]
  }),
)

// North Indian 4×4 grid layout.
// Cell [row][col] = house number (0 = center filler, -1 = unused).
// Layout:
//   [12]  [1]  [2]  [3]
//   [11]  [C]  [C]  [4]
//   [10]  [C]  [C]  [5]
//    [9]  [8]  [7]  [6]
const GRID: number[][] = [
  [12, 1, 2, 3],
  [11, 0, 0, 4],
  [10, 0, 0, 5],
  [9, 8, 7, 6],
]

// Which corner cells get a diagonal? [row, col, x1,y1,x2,y2] (relative to cell origin)
// The diagonal connects the two inner corners of each corner cell, drawing the diamond.
const CORNER_DIAGONALS: [number, number, number, number, number, number][] = [
  [0, 0, 1, 0, 0, 1], // H12: top-right inner to bottom-left inner (as fraction of cell)
  [0, 3, 0, 0, 1, 1], // H03: top-left inner to bottom-right inner
  [3, 0, 0, 0, 1, 1], // H09: top-left inner to bottom-right inner
  [3, 3, 1, 0, 0, 1], // H06: top-right inner to bottom-left inner
]

// Sign abbreviation for label
const SIGN_ABBREV: Record<string, string> = {
  Aries: 'Ar', Taurus: 'Ta', Gemini: 'Ge', Cancer: 'Ca',
  Leo: 'Le', Virgo: 'Vi', Libra: 'Li', Scorpio: 'Sc',
  Sagittarius: 'Sg', Capricorn: 'Cp', Aquarius: 'Aq', Pisces: 'Pi',
}

export function RasiChartSVG({
  chart,
  size = 480,
  className,
}: RasiChartSVGProps) {
  const cell = size / 4
  const gold = 'var(--brand-gold)'
  const goldLight = 'var(--brand-gold-light)'
  const goldFaint = 'var(--brand-gold-faint, oklch(0.78 0.13 80 / 0.12))'
  const charcoal = 'var(--brand-charcoal)'

  // Build house lookup: house number → { sign, planets }
  const houseData = Object.fromEntries(
    chart.houses.map((h) => [h.house, h]),
  )

  if (chart.isEmpty) {
    return (
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width={size}
        height={size}
        className={cn('block', className)}
        role="img"
        aria-label="L1 facts not yet ingested for this chart"
      >
        <rect width={size} height={size} fill={charcoal} />
        <text
          x={size / 2}
          y={size / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={gold}
          fontSize={13}
          fontFamily="var(--font-sans, Inter, sans-serif)"
        >
          L1 facts not yet ingested
        </text>
      </svg>
    )
  }

  // Build aria-label from placements
  const planetList = chart.houses
    .filter((h) => h.planets.length > 0)
    .map((h) => `${h.planets.join(', ')} in ${h.sign}`)
    .join('; ')
  const ariaLabel = `Rasi chart, Lagna ${chart.lagnaSign} ${chart.lagnaDegreeDms}. ${planetList}`

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      width={size}
      height={size}
      className={cn('block', className)}
      role="img"
      aria-label={ariaLabel}
    >
      {/* Background */}
      <rect width={size} height={size} fill={charcoal} />

      {/* Center diamond fill */}
      <polygon
        points={`${cell * 2},0 ${size},${cell * 2} ${cell * 2},${size} 0,${cell * 2}`}
        fill={goldFaint}
        stroke={gold}
        strokeWidth="1.5"
      />

      {/* Outer square border */}
      <rect
        x={0.75}
        y={0.75}
        width={size - 1.5}
        height={size - 1.5}
        fill="none"
        stroke={gold}
        strokeWidth="1.5"
      />

      {/* Grid cells and content */}
      {GRID.map((row, ri) =>
        row.map((houseNum, ci) => {
          if (houseNum === 0) return null // center
          const x = ci * cell
          const y = ri * cell

          const hd = houseData[houseNum]
          const signAbbr = hd ? (SIGN_ABBREV[hd.sign] ?? hd.sign.slice(0, 2)) : ''
          const planets = hd?.planets ?? []

          // Determine if this is a corner cell
          const isCorner = (ri === 0 || ri === 3) && (ci === 0 || ci === 3)

          // Lagna notch: small triangle on H1 (ri=0,ci=1) inner bottom-left corner
          const isLagna = houseNum === 1

          return (
            <g key={`cell-${ri}-${ci}`}>
              {/* Cell border (outer grid lines) */}
              <rect
                x={x}
                y={y}
                width={cell}
                height={cell}
                fill="none"
                stroke={gold}
                strokeWidth="1"
              />

              {/* Corner diagonal */}
              {isCorner && (() => {
                const def = CORNER_DIAGONALS.find(([dr, dc]) => dr === ri && dc === ci)
                if (!def) return null
                const [, , fx1, fy1, fx2, fy2] = def
                return (
                  <line
                    x1={x + fx1 * cell}
                    y1={y + fy1 * cell}
                    x2={x + fx2 * cell}
                    y2={y + fy2 * cell}
                    stroke={gold}
                    strokeWidth="1"
                  />
                )
              })()}

              {/* Lagna notch — small filled triangle at inner corner of H1 */}
              {isLagna && (
                <polygon
                  points={`${x},${y + cell} ${x + 14},${y + cell} ${x},${y + cell - 14}`}
                  fill={gold}
                />
              )}

              {/* House number — top-left in small text */}
              <text
                x={x + 6}
                y={y + 13}
                fontSize={9}
                fill={gold}
                fontFamily="var(--font-sans, Inter, sans-serif)"
                opacity={0.6}
              >
                {houseNum}
              </text>

              {/* Sign abbreviation — top-right */}
              <text
                x={x + cell - 6}
                y={y + 13}
                textAnchor="end"
                fontSize={9}
                fill={gold}
                fontFamily="var(--font-sans, Inter, sans-serif)"
                opacity={0.55}
              >
                {signAbbr}
              </text>

              {/* Planet glyphs — stacked in center of cell */}
              {planets.map((planet, pi) => {
                const abbr = ABBREV[planet] ?? planet.slice(0, 2)
                const totalH = planets.length * 18
                const startY = y + (cell - totalH) / 2 + 14 + pi * 18
                return (
                  <text
                    key={planet}
                    x={x + cell / 2}
                    y={startY}
                    textAnchor="middle"
                    fontSize={14}
                    fill={goldLight}
                    fontFamily="var(--font-serif, 'Source Serif 4', Georgia, serif)"
                    fontWeight="400"
                  >
                    {abbr}
                  </text>
                )
              })}
            </g>
          )
        }),
      )}

      {/* Center cross lines (complete the diamond interior division) */}
      <line
        x1={cell * 2}
        y1={0}
        x2={cell * 2}
        y2={size}
        stroke={gold}
        strokeWidth="0.75"
        opacity={0.4}
      />
      <line
        x1={0}
        y1={cell * 2}
        x2={size}
        y2={cell * 2}
        stroke={gold}
        strokeWidth="0.75"
        opacity={0.4}
      />
    </svg>
  )
}
