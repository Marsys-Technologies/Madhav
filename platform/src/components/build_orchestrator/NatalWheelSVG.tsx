'use client'

// NatalWheelSVG — circular 12-house natal wheel with build state indicators
// H-02: initial implementation

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

export type BuildState = 'idle' | 'building' | 'complete' | 'failed'

export interface WheelSegment {
  house: number        // 1-12
  sign: string         // e.g., 'Aries'
  startAngle: number   // degrees
  state: BuildState
  ayanamsha?: string
}

export interface NatalWheelSVGProps {
  segments?: WheelSegment[]
  size?: number              // SVG viewBox size, default 400
  activeAyanamshas?: string[] // which ayanamshas are being built
}

const STATE_COLORS: Record<BuildState, string> = {
  idle: '#374151',      // gray-700
  building: '#2563EB',  // blue-600
  complete: '#16A34A',  // green-600
  failed: '#DC2626',    // red-600
}

const STATE_STROKE: Record<BuildState, string> = {
  idle: '#4B5563',      // gray-600
  building: '#3B82F6',  // blue-500
  complete: '#22C55E',  // green-500
  failed: '#EF4444',    // red-500
}

function polarToCartesian(
  cx: number,
  cy: number,
  r: number,
  angleDeg: number,
): { x: number; y: number } {
  const rad = (angleDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function buildSegmentPath(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number,
  startAngle: number,
  endAngle: number,
): string {
  const outerStart = polarToCartesian(cx, cy, outerR, startAngle)
  const outerEnd = polarToCartesian(cx, cy, outerR, endAngle)
  const innerStart = polarToCartesian(cx, cy, innerR, startAngle)
  const innerEnd = polarToCartesian(cx, cy, innerR, endAngle)

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${outerR} ${outerR} 0 0 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${innerR} ${innerR} 0 0 0 ${innerStart.x} ${innerStart.y}`,
    'Z',
  ].join(' ')
}

export default function NatalWheelSVG({
  segments,
  size = 400,
  activeAyanamshas = [],
}: NatalWheelSVGProps) {
  const cx = size / 2
  const cy = size / 2
  const outerR = size * 0.45
  const innerR = size * 0.25
  const labelR = (outerR + innerR) / 2

  // Default 12 equal segments if none provided
  const defaultSegments: WheelSegment[] = Array.from({ length: 12 }, (_, i) => ({
    house: i + 1,
    sign: SIGN_NAMES[i],
    startAngle: i * 30 - 90, // start from 12 o'clock
    state: 'idle' as BuildState,
    ayanamsha: undefined,
  }))

  const allSegments = segments ?? defaultSegments

  const centerLabel = activeAyanamshas.length > 0
    ? `${activeAyanamshas.length} ayanamsha${activeAyanamshas.length > 1 ? 's' : ''}`
    : 'Idle'

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="w-full h-full max-w-md"
      data-testid="natal-wheel-svg"
      aria-label="Natal wheel build state visualization"
    >
      {/* Outer background circle */}
      <circle
        cx={cx}
        cy={cy}
        r={outerR + 10}
        fill="#0F172A"
        data-testid="wheel-background"
      />

      {/* 12 house segments */}
      {allSegments.map((seg) => {
        const startAngle = seg.startAngle
        const endAngle = startAngle + 30

        const d = buildSegmentPath(cx, cy, outerR, innerR, startAngle, endAngle)
        const midAngle = startAngle + 15
        const labelPos = polarToCartesian(cx, cy, labelR, midAngle)

        return (
          <g
            key={seg.house}
            data-testid={`wheel-segment-${seg.house}`}
            data-state={seg.state}
            data-house={seg.house}
          >
            <path
              d={d}
              fill={STATE_COLORS[seg.state]}
              fillOpacity={0.75}
              stroke={STATE_STROKE[seg.state]}
              strokeWidth={1.5}
            >
              {seg.state === 'building' && (
                <animate
                  attributeName="fillOpacity"
                  values="0.4;0.9;0.4"
                  dur="1.6s"
                  repeatCount="indefinite"
                />
              )}
            </path>

            {/* House number label */}
            <text
              x={labelPos.x}
              y={labelPos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="white"
              fontSize={size * 0.042}
              fontWeight="500"
              className="select-none"
              data-testid={`wheel-label-${seg.house}`}
            >
              {seg.house}
            </text>
          </g>
        )
      })}

      {/* Spoke dividers between houses */}
      {allSegments.map((seg) => {
        const spokeEnd = polarToCartesian(cx, cy, outerR + 2, seg.startAngle)
        const spokeStart = polarToCartesian(cx, cy, innerR - 2, seg.startAngle)
        return (
          <line
            key={`spoke-${seg.house}`}
            x1={spokeStart.x}
            y1={spokeStart.y}
            x2={spokeEnd.x}
            y2={spokeEnd.y}
            stroke="#0F172A"
            strokeWidth={1}
          />
        )
      })}

      {/* Center circle */}
      <circle
        cx={cx}
        cy={cy}
        r={innerR - 4}
        fill="#0F172A"
        stroke="#1E293B"
        strokeWidth={1}
        data-testid="wheel-center"
      />

      {/* Center text — "Build" */}
      <text
        x={cx}
        y={cy - size * 0.04}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#94A3B8"
        fontSize={size * 0.045}
        fontWeight="600"
        className="select-none"
        data-testid="wheel-center-title"
      >
        Build
      </text>

      {/* Center text — active ayanamshas / idle */}
      <text
        x={cx}
        y={cy + size * 0.04}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#64748B"
        fontSize={size * 0.032}
        className="select-none"
        data-testid="wheel-center-subtitle"
      >
        {centerLabel}
      </text>
    </svg>
  )
}
