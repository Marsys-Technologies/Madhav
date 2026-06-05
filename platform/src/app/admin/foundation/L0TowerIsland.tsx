'use client'

/**
 * L0TowerIsland — client island that renders a single-band LayerTower
 * for L0 (Brahmagyan) on the /admin/foundation page.
 *
 * Isolated as a client component so the parent server page avoids being
 * converted to 'use client' just for LayerTower's useCallback.
 *
 * WS-1-S3-C
 */

import { LayerTower } from '@/components/brahma/LayerTower'
import type { Layer } from '@/components/brahma/LayerTower'

export function L0TowerIsland({ layer }: { layer: Layer }) {
  return (
    <LayerTower
      layers={[layer]}
      // No asset click handler in the foundation view (no inspector on this page)
      // No consult click — L0 is infra, not client-consult eligible
    />
  )
}
