import 'server-only'
import { query } from '@/lib/db/client'
import { getEntitledCharts } from './getEntitledCharts'

export function getEntitledChartsForPrincipal(uid: string, role: 'guest' | 'super_admin') {
  return getEntitledCharts(uid, role, { query })
}
