import {describe,it,expect} from 'vitest'
import {operatorActivityFilters} from '@/lib/admin/activity-filters'
import {personalActivityFilters} from '@/lib/account/activity-filters'
const now=new Date('2026-10-06T00:00:00Z')
describe('operator authority and shared filter semantics',()=>{
  it('ignores an inherited user id in portal scope',()=>{
    const value=operatorActivityFilters(new URLSearchParams('scope=portal&userId=another&channel=mcp'),'actor',now)
    expect(value.target).toBeNull();expect(value.params.has('userId')).toBe(false);expect(value.params.get('channel')).toBe('mcp')
  })
  it('binds mine to the actor and retains selected-user navigation separately from API authority',()=>{
    expect(operatorActivityFilters(new URLSearchParams('scope=mine&userId=another'),'actor',now).target).toBe('actor')
    const value=operatorActivityFilters(new URLSearchParams('scope=user&userId=another&aggregation=transport'),'actor',now)
    expect(value.params.get('userId')).toBe('another');expect(value.navigation.get('userId')).toBe('another')
    expect(personalActivityFilters(value.params,now).has('userId')).toBe(false)
  })
  it('requires an explicit selected user and never substitutes the administrator',()=>{
    expect(operatorActivityFilters(new URLSearchParams('scope=user'),'actor',now)).toMatchObject({ready:false,target:''})
  })
  it('rejects invalid scope and overlong activity periods',()=>{
    expect(()=>operatorActivityFilters(new URLSearchParams('scope=impersonate'),'actor',now)).toThrow()
    expect(()=>operatorActivityFilters(new URLSearchParams('from=2026-01-01T00:00:00Z&to=2026-10-01T00:00:00Z'),'actor',now)).toThrow()
  })
})
