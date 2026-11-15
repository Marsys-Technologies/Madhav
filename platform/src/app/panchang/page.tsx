/**
 * /panchang — Panchang Day View (server component)
 *
 * Fetches today's Panchang for default location (Bhubaneswar) on the server
 * by calling the Python sidecar directly (same as queryPanchanga's callSidecar
 * but without needing a full QueryPlan — the RetrievalTool is designed for
 * LLM orchestration, not SSR page entry points).
 *
 * Passes data to PanchangClientView as initialData to avoid client-side loading flash.
 * Subsequent navigation (date/location changes) handled client-side via usePanchangDay.
 *
 * Phase: 4C-4-S1 (Item 2)
 */

import { Suspense } from 'react'
import { format } from 'date-fns'
import { PanchangClientView } from './components/PanchangClientView'
import { readPanchangPageData } from '@/lib/kala/panchangPageData'
import { requireActiveUserPage } from '@/lib/auth/active-user-page-guard'
import type { SearchParams } from 'next/dist/server/request/search-params'

// Default location: Bhubaneswar (per brief D1 decisions + query_panchanga.ts constants)
const DEFAULT_LAT = 20.27
const DEFAULT_LON = 85.84
const DEFAULT_TZ = 330 // IST +05:30

interface PanchangPageProps {
  searchParams: Promise<SearchParams>
}

export default async function PanchangPage({ searchParams }: PanchangPageProps) {
  // SS N-398: the page verifies the login itself, BEFORE the sidecar fetch.
  // panchang/layout.tsx checks too, but a crafted RSC request can skip a layout
  // (see clients/[id]/layout.tsx), and proxy.ts only checks the cookie's shape.
  // Plain /login: only /share/ and /clients/ are allowed to carry `?next=`.
  await requireActiveUserPage()

  const params = await searchParams
  const today = format(new Date(), 'yyyy-MM-dd')

  // Resolve date from URL (default: today)
  const dateParam = typeof params['d'] === 'string' ? params['d'] : today
  const date = /^\d{4}-\d{2}-\d{2}$/.test(dateParam) ? dateParam : today

  // Resolve location from URL (default: Bhubaneswar)
  const latParam = typeof params['lat'] === 'string' ? parseFloat(params['lat']) : DEFAULT_LAT
  const lonParam = typeof params['lon'] === 'string' ? parseFloat(params['lon']) : DEFAULT_LON
  const resolvedLat = isNaN(latParam) ? DEFAULT_LAT : latParam
  const resolvedLon = isNaN(lonParam) ? DEFAULT_LON : lonParam

  const initialData = await readPanchangPageData(date, resolvedLat, resolvedLon, DEFAULT_TZ)

  return (
    <div className="relative min-h-full overflow-hidden">
      {/* Brand background gradient — matches dashboard aesthetic */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_30%,rgba(212,175,55,0.03)_0%,transparent_60%)]" />

      <div className="relative z-10">
        <Suspense fallback={null}>
          <PanchangClientView
            initialData={initialData}
            initialDate={date}
            initialLat={resolvedLat}
            initialLon={resolvedLon}
          />
        </Suspense>
      </div>
    </div>
  )
}
