'use client'

import { useEffect } from 'react'

export function ReviewSourceFocus({ answerId }: { answerId: string }) {
  useEffect(() => {
    document.getElementById(answerId)?.focus()
  }, [answerId])
  return null
}
