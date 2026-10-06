import {afterEach,it,expect,vi} from 'vitest'
import {render,screen,cleanup} from '@testing-library/react'
const state=vi.hoisted(()=>({path:'/admin/activity',search:'scope=user&userId=selected&from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z&channel=mcp&aggregation=transport'}))
vi.mock('next/navigation',()=>({usePathname:()=>state.path,useSearchParams:()=>new URLSearchParams(state.search)}))
vi.mock('@/components/observatory/ObservatoryScope',()=>({useObservatoryScope:()=>({userId:'actor'})}))
import {AdminNavigation} from '@/components/admin/AdminNavigation'
afterEach(cleanup)
it('preserves selected-user authority and the normalized filters across both activity navigation links',()=>{
 render(<AdminNavigation />)
 for(const name of ['Analytics','System Observatory']){
  const url=new URL(screen.getByRole('link',{name}).getAttribute('href')!,'http://local')
  expect(url.searchParams.get('scope')).toBe('user');expect(url.searchParams.get('userId')).toBe('selected');expect(url.searchParams.get('channel')).toBe('mcp');expect(url.searchParams.get('from')).toBe('2026-10-01T00:00:00Z')
 }
 expect(screen.queryByRole('link',{name:'Query Trace'})).toBeNull()
})
