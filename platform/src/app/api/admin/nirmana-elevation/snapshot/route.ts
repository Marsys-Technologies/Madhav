import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { loadNirmanaElevationRawSources, NirmanaElevationSourceError, projectNirmanaElevationSnapshot, unavailableNirmanaElevationSnapshot } from '@/lib/nirmana-elevation/snapshot'

export const dynamic = 'force-dynamic'
export const maxDuration = 15

function snapshotResponse(body: Awaited<ReturnType<typeof projectNirmanaElevationSnapshot>>, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: { 'Cache-Control': 'no-store', ETag: `"${body.generation}"` },
  })
}

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) {
    auth.headers.set('Cache-Control', 'no-store')
    return auth
  }

  try {
    return snapshotResponse(projectNirmanaElevationSnapshot(await loadNirmanaElevationRawSources()))
  } catch (error) {
    if (error instanceof NirmanaElevationSourceError) {
      return snapshotResponse(unavailableNirmanaElevationSnapshot(error), 503)
    }
    console.error('[api/admin/nirmana-elevation/snapshot] unexpected failure', error)
    return snapshotResponse(unavailableNirmanaElevationSnapshot(new NirmanaElevationSourceError('asset_registry', error)), 503)
  }
}
