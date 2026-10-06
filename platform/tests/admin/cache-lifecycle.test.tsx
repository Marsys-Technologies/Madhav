// @vitest-environment jsdom
import React from 'react'
import {act,render,screen,waitFor} from '@testing-library/react'
import {expect,it} from 'vitest'
import {useQuery,useQueryClient,type QueryClient} from '@tanstack/react-query'
import {AdminQueryBoundary} from '@/components/admin/AdminQueryBoundary'
it('isolates cached and late privileged results across an actor switch',async()=>{
 let resolveOld!:(value:string)=>void,oldClient!:QueryClient
 const pending=new Promise<string>(resolve=>{resolveOld=resolve})
 function Record({actor}:{actor:string}){const client=useQueryClient();if(actor==='a')oldClient=client;const query=useQuery({queryKey:['legacy-grant'],queryFn:()=>actor==='a'?pending:Promise.resolve('actor-b-record')});return <p>{query.data??'Loading record'}</p>}
 const view=render(<AdminQueryBoundary key='a'><Record actor='a'/></AdminQueryBoundary>)
 await waitFor(()=>expect(oldClient.getQueryCache().getAll()).toHaveLength(1))
 view.rerender(<AdminQueryBoundary key='b'><Record actor='b'/></AdminQueryBoundary>)
 await screen.findByText('actor-b-record')
 await act(async()=>resolveOld('actor-a-private-record'))
 expect(screen.queryByText('actor-a-private-record')).toBeNull()
 expect(oldClient.getQueryCache().getAll()).toHaveLength(0)
})
