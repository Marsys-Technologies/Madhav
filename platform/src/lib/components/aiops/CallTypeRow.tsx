import type { CallType } from '@/lib/models/registry'
import { CALL_TYPE_SPECS } from '@/lib/aiops/specs/call_type_specs'

interface CallTypeRowProps {
  callType:      CallType
  primaryModel:  string
  fallbackModel: string
}

export function CallTypeRow({ callType, primaryModel, fallbackModel }: CallTypeRowProps) {
  const spec = CALL_TYPE_SPECS[callType]

  return (
    <div className="grid grid-cols-[160px_1fr_1fr] items-start gap-x-4 border-b border-border py-3 last:border-0">
      <div>
        <p className="text-sm font-medium text-foreground">{callType}</p>
        {spec.notes && (
          <p className="mt-0.5 text-xs text-muted-foreground">{spec.notes}</p>
        )}
      </div>
      <div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Primary</span>
        <p className="mt-0.5 truncate text-xs font-mono text-foreground">{primaryModel || '—'}</p>
      </div>
      <div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Fallback</span>
        <p className="mt-0.5 truncate text-xs font-mono text-foreground">{fallbackModel || '—'}</p>
      </div>
    </div>
  )
}
