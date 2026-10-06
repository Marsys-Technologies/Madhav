'use client'
import {useEffect,useState,type ReactNode} from 'react'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'

/** Privileged caches live only within this authenticated actor's admin layout. */
export function AdminQueryBoundary({children}:{children:ReactNode}) {
  const [client]=useState(()=>new QueryClient())
  useEffect(()=>()=>{void client.cancelQueries();client.clear()},[client])
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
