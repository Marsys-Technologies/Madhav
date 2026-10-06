import {describe,it,expect,vi} from 'vitest'
import {readOperations} from '@/lib/admin/operations'
describe('read-only operational evidence',()=>{
  it('keeps a failed source distinct from an empty successful source and never returns its error',async()=>{
    const read=vi.fn(async(sql:string)=>{if(sql.includes('capability_tool_registry'))throw Error('credential=private');return {rows:[]}})
    const data=await readOperations('health',read)
    expect(data.sources[0]).toMatchObject({available:false,rows:[]})
    expect(data.sources[1]).toMatchObject({available:true,rows:[]})
    expect(JSON.stringify(data)).not.toContain('credential')
    expect(data.notes.join(' ')).toContain('unavailable')
    for(const [sql] of read.mock.calls)expect(sql).not.toMatch(/\b(INSERT|UPDATE|DELETE|DROP|CALL)\b/i)
  })
  it('uses the governed external layer names and does not treat count contracts as counts',async()=>{
    const data=await readOperations('assets',async(sql)=>({rows:sql.includes('asset_registry')?[{asset_id:'ga_fact',layer:'L1',english_name:'Facts',has_count_contract:true}]:[]}))
    expect(data.sources[0].rows[0]).toMatchObject({layer:'Gaṇita',count_contract:true})
    expect(data.sources[0].note).toContain('not a measured count')
    expect(JSON.stringify(data)).not.toContain('"L1"')
  })
  it('reports configuration presence without leaking its value or claiming reachability',async()=>{
    vi.stubEnv('GCS_BUCKET_NAME','private-bucket-location')
    try{const data=await readOperations('foundation',async()=>({rows:[]}));expect(data.sources[2].rows[0]).toMatchObject({configured:true,reachability:'Not measured'});expect(JSON.stringify(data)).not.toContain('private-bucket-location')}finally{vi.unstubAllEnvs()}
  })
  it('does not read a database or advance a campaign when reading historical programme declarations',async()=>{
    const read=vi.fn();const data=await readOperations('programme',read)
    expect(read).not.toHaveBeenCalled();expect(data.sources[0].note).toContain('superseded')
  })
  it('keeps learning read-only and does not certify stored publication labels',async()=>{
    const read=vi.fn(async(_sql:string)=>({rows:[]}));const data=await readOperations('learning',read)
    expect(data.sources[0].note).toContain('not certification')
    expect(data.notes.join(' ')).toContain('independent co-sign')
    for(const [sql] of read.mock.calls)expect(sql).not.toMatch(/\b(INSERT|UPDATE|DELETE|CALL)\b/i)
  })
})
