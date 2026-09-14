'use client'

import { useSyncExternalStore } from 'react'

const subscribe = () => () => {}
const getClientSnapshot = () => true
const getServerSnapshot = () => false

/**
 * Reports whether the component is rendering on a hydrated client.
 *
 * Portals use this to avoid touching `document.body` during server rendering
 * without scheduling a synchronous state update from an effect.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(subscribe, getClientSnapshot, getServerSnapshot)
}
