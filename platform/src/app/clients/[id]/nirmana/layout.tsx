import type { ReactNode } from 'react'
import { ZoneRoot } from '@/components/shared/ZoneRoot'

export default function BuildLayout({ children }: { children: ReactNode }) {
  return (
    <ZoneRoot zone="vellum" style={{ display: 'contents' }}>
      {children}
    </ZoneRoot>
  )
}
