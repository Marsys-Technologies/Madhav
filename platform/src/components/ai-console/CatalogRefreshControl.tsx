'use client'

import { RefreshCw } from 'lucide-react'
import { formatCheckedAt, type CatalogRefreshStatus } from './types'

interface Props {
  name: string
  kind: 'connection' | 'cli'
  refreshedAt?: string | null
  errorCode?: string | null
  status?: CatalogRefreshStatus
  onRefresh: () => void
}

export function CatalogRefreshControl({ name, kind, refreshedAt, errorCode, status, onRefresh }: Props) {
  const error = status?.error ?? (errorCode ? 'The last refresh failed. The previous model list is retained. Try refreshing again.' : null)
  return <div className="aic-catalog-refresh">
    <div className="aic-catalog-refresh-line">
      <span className="aic-meta">{status?.pending ? 'Refreshing models and effort levels…' : `Models refreshed · ${refreshedAt ? formatCheckedAt(refreshedAt) : 'Not refreshed yet'}`}</span>
      <button className="aic-button aic-icon-button" type="button"
        aria-label={`Refresh ${name} ${kind === 'cli' ? 'version, models, and effort levels' : 'models and effort levels'}`}
        title={kind === 'cli' ? 'Refresh installed version, subscription models, and effort levels' : 'Refresh provider model catalog and known effort levels; no generation request'}
        disabled={status?.pending} aria-busy={status?.pending || undefined} onClick={onRefresh}>
        <RefreshCw aria-hidden="true" className={status?.pending ? 'aic-refresh-spinning' : undefined} />
      </button>
    </div>
    {error && <p className="aic-failure-guidance" role="status">{error}</p>}
  </div>
}
