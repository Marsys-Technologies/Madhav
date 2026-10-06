import {expect,it,vi} from 'vitest'
vi.mock('@/lib/auth/access-control',()=>({getServerUserWithProfile:vi.fn()}))
import {activityDestination} from '@/lib/admin/legacy-activity'
it('preserves compatible filters while stripping operator authority for personal bookmarks',()=>{
 const url=new URL(activityDestination(false,'observatory',{userId:'another',scope:'portal',channel:'mcp',provider:'provider',from:'2026-10-01T00:00:00Z'}),'https://example.test')
 expect(url.pathname).toBe('/account/ai-cockpit/observatory');expect(url.searchParams.has('userId')).toBe(false);expect(url.searchParams.has('scope')).toBe(false);expect(url.searchParams.get('channel')).toBe('mcp')
})
it('preserves explicit operator population and the legacy personal default',()=>{
 expect(activityDestination(true,'observatory',{})).toBe('/admin/activity?scope=mine')
 expect(activityDestination(true,'consumption',{scope:'user',userId:'selected',aggregation:'transport'})).toBe('/admin/analytics?aggregation=transport&scope=user&userId=selected')
 expect(activityDestination(true,'consumption',{userId:['actor','selected']})).toBe('/admin/analytics?scope=mine')
})
