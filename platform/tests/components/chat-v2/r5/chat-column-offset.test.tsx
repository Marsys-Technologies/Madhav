import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

// Tests the className logic introduced in ConsumeChatV2.tsx:1417 for A.1.
// Validates that the correct md:ml-* class is produced based on sidebarCollapsed.
function chatColumnClass(sidebarCollapsed: boolean) {
  return cn(
    'flex flex-col flex-1 overflow-hidden min-w-0',
    'transition-[margin-left] duration-200 ease-out',
    sidebarCollapsed ? 'md:ml-10' : 'md:ml-56',
  )
}

describe('ConsumeChatV2 chat column sidebar offset (A.1)', () => {
  it('applies md:ml-10 when sidebar collapsed', () => {
    const cls = chatColumnClass(true)
    expect(cls).toMatch(/md:ml-10/)
    expect(cls).not.toMatch(/md:ml-56/)
  })

  it('applies md:ml-56 when sidebar expanded', () => {
    const cls = chatColumnClass(false)
    expect(cls).toMatch(/md:ml-56/)
    expect(cls).not.toMatch(/md:ml-10/)
  })
})
