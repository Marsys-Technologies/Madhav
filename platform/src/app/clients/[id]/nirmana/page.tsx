import Link from 'next/link'
import { ChevronLeft } from 'lucide-react'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import { query } from '@/lib/db/client'

// v2 cockpit — replaces legacy ConstellationCanvas per VISUAL_CONTRACT v2 §C-S8.5.
// CockpitShell assembles LiveDependencyGraph, OverallProgress, TelemetryStrip,
// AssetTable, and BuildControlsBar with built-in polling + SSE subscriptions.

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const { rows } = await query<{ subject_name: string | null }>(
    'SELECT subject_name FROM charts WHERE id=$1',
    [id]
  ).catch(() => ({ rows: [] }))
  const name = rows[0]?.subject_name ?? 'Chart'
  return { title: `Nirmāṇa · ${name} — MARSYS-JIS` }
}

export default async function BuildPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')

  // Build is owner/super_admin only. View-only grantees are explicitly NOT
  // allowed in (per Unit 3.consult_nav AC.1 — granted chart shows no Build).
  if (!access.canBuild) redirect(`/clients/${id}`)

  // Prefetch chart metadata server-side so CockpitShell doesn't show "Loading chart…"
  const { rows: chartRows } = await query<{ subject_name: string | null; birth_date: string | null; birth_time: string | null; birth_place: string | null }>(
    'SELECT subject_name, birth_date, birth_time::text, birth_place FROM charts WHERE id=$1',
    [id]
  ).catch(() => ({ rows: [] }))
  const initialChartMeta = chartRows[0] ?? null

  return (
    <div data-testid="build-page-root" data-permission={access.permission} className="h-screen flex flex-col overflow-hidden pt-3">
      {/* ── Nirmāṇa page header — centered wordmark, kept slim so the instrument fills the view ── */}
      <div className="relative flex items-center justify-center w-full mt-1 mb-1 shrink-0">
        <Link
          href="/dashboard"
          aria-label="Back to dashboard"
          className="absolute left-0 flex items-center justify-center w-8 h-8 rounded-full transition-colors duration-150 text-[oklch(0.58_0.025_80)] hover:text-brand-gold"
        >
          <ChevronLeft size={20} strokeWidth={1.5} />
        </Link>
        <h1 className="bt-display text-brand-gold-cream">
          <span className="opacity-55 text-brand-gold font-serif mr-1" aria-hidden="true">॥</span>
          Nirmāṇa
          <span className="opacity-55 text-brand-gold font-serif ml-1" aria-hidden="true">॥</span>
        </h1>
      </div>
      <p className="bt-label bt-label-upper text-brand-gold/55 mb-2 shrink-0" style={{ textAlign: 'center' }}>Build Tracker</p>
      <div className="flex-1 min-h-0">
        <CockpitShell chartId={id} initialChartMeta={initialChartMeta} />
      </div>
    </div>
  )
}
