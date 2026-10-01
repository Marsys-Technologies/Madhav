import { describe,expect,it,vi } from 'vitest'
import { generateText,stepCountIs,tool,jsonSchema } from 'ai'
import type { LanguageModelV3 } from '@ai-sdk/provider'
import { meterModel } from '../model'
const usage={inputTokens:{total:10,noCache:10,cacheRead:0,cacheWrite:0},outputTokens:{total:2,text:2,reasoning:0}}
describe('actual AI SDK tool loop',()=>{
 it('accounts for two transport calls without recording SDK aggregate usage again',async()=>{
  const query=vi.fn(async(sql:string,params?:unknown[])=>{ expect(sql).toBeTruthy(); if(params)expect(Array.isArray(params)).toBe(true); return {rows:[],rowCount:1} })
  let calls=0
  const model:LanguageModelV3={specificationVersion:'v3',provider:'test',modelId:'test',supportedUrls:{},doStream:vi.fn(),
   doGenerate:async()=>({usage,warnings:[],finishReason:{unified:calls++===0?'tool-calls':'stop',raw:'stop'},
    content:calls===1?[{type:'tool-call',toolCallId:'lookup-1',toolName:'lookup',input:'{}'}]:[{type:'text',text:'complete'}]})}
  const wrapped=meterModel(model,{userId:'alice',conversationId:'conv',turnId:'query',operationId:'planner',channel:'mcp',purpose:'customer',payer:'user',provider:'openai',model:'test',role:'planner',aggregation:'transport'},
   {db:{query},recovery:{put:vi.fn(),read:vi.fn(),remove:vi.fn(),list:async()=>[]}})
  const result=await generateText({model:wrapped,prompt:'test',maxRetries:0,stopWhen:stepCountIs(3),tools:{lookup:tool({inputSchema:jsonSchema({type:'object',properties:{}}),execute:async()=>({ok:true})})}})
  expect(result.steps).toHaveLength(2);expect(result.totalUsage.inputTokens).toBe(20)
  const starts=query.mock.calls.filter(args=>String(args[0]).includes('INSERT INTO ai_metering_attempts'))
  const ends=query.mock.calls.filter(args=>String(args[0]).includes('INSERT INTO ai_metering_receipts'))
  expect(starts).toHaveLength(2);expect(ends).toHaveLength(2)
 })
})
