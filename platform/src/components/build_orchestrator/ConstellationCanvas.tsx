'use client'

// ConstellationCanvas — SVG natal wheel + animated asset nodes build visualization
// Full implementation: H-02 through H-13
// H-02: SVG natal wheel integrated
// H-04: BuildWaveAnimation layered over NatalWheelSVG

import NatalWheelSVG from './NatalWheelSVG'
import BuildWaveAnimation, { type AyanamshaWaveState } from './BuildWaveAnimation'

interface ConstellationCanvasProps {
  chartId: string | Promise<string>
  /** Optional wave states to drive the progress sweep animation (H-04).
   *  Defaults to an empty array (idle) until the SSE consumer (H-09) wires in live data. */
  waveStates?: AyanamshaWaveState[]
}

export default function ConstellationCanvas({
  chartId,
  waveStates = [],
}: ConstellationCanvasProps) {
  return (
    <div
      className="constellation-canvas w-full h-screen flex items-center justify-center bg-slate-950"
      data-testid="constellation-canvas"
    >
      <div className="flex flex-col items-center space-y-4 w-full max-w-lg px-4">
        <div className="text-2xl font-semibold text-foreground">
          Build Constellation
        </div>
        <div className="text-sm text-muted-foreground">
          Multi-ayanamsha chart build visualization
        </div>

        {/* H-02 + H-04: natal wheel with wave animation overlaid */}
        <div
          className="relative w-full aspect-square max-w-md"
          data-testid="natal-wheel-container"
        >
          {/* Base layer: 12-house natal wheel */}
          <NatalWheelSVG />

          {/* Overlay layer: per-ayanamsha progress sweep (H-04) */}
          <div className="absolute inset-0" data-testid="wave-animation-overlay">
            <BuildWaveAnimation
              ayanamshaStates={waveStates}
              size={400}
              className="w-full h-full"
            />
          </div>
        </div>

        {/* H-03: Asset nodes */}
        {/* H-05: Detail panel */}
        {/* H-06: Command bar */}
        {/* H-08: 5-ayanamsha multi-pulse */}
        {/* H-09: SSE consumer */}
      </div>
    </div>
  )
}
