'use client'

// ConstellationCanvas — SVG natal wheel + animated asset nodes build visualization
// Full implementation: H-02 through H-13
// H-02: SVG natal wheel integrated

import NatalWheelSVG from './NatalWheelSVG'

interface ConstellationCanvasProps {
  chartId: string | Promise<string>
}

export default function ConstellationCanvas({ chartId }: ConstellationCanvasProps) {
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

        {/* H-02: SVG natal wheel */}
        <div className="w-full aspect-square max-w-md" data-testid="natal-wheel-container">
          <NatalWheelSVG />
        </div>

        {/* H-03: Asset nodes */}
        {/* H-04: Wave animation */}
        {/* H-05: Detail panel */}
        {/* H-06: Command bar */}
        {/* H-08: 5-ayanamsha multi-pulse */}
        {/* H-09: SSE consumer */}
      </div>
    </div>
  )
}
