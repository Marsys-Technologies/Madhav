import { Suspense } from 'react'
import { TraceHistory } from '@/components/admin/TraceHistory'
export default function Page() { return <Suspense fallback={<p>Loading…</p>}><TraceHistory /></Suspense> }
