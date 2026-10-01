import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest'
const mocks=vi.hoisted(()=>({role:vi.fn(),start:vi.fn(),finish:vi.fn(),observe:vi.fn()}))
vi.mock('@/lib/ai-console/repository',()=>({insertRoleInvocationReceipt:mocks.role}))
vi.mock('../service',()=>({startAttempt:mocks.start,finishAttempt:mocks.finish}))
vi.mock('@/lib/ai-console/observability',()=>({observeRoleInvocation:mocks.observe}))
import { trackRoleExecutor } from '@/lib/ai-console/execution/tracked-executor'
import { AiConsoleError } from '@/lib/ai-console/errors'
import type { RoleExecutor } from '@/lib/ai-console/execution/provider-executor'
beforeEach(()=>{
 vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED','true');mocks.role.mockResolvedValue(undefined);mocks.observe.mockResolvedValue(undefined)
 mocks.start.mockImplementation(async context=>({...context,attemptId:crypto.randomUUID(),startedAt:new Date().toISOString()}));mocks.finish.mockResolvedValue(undefined)
})
afterEach(()=>{vi.unstubAllEnvs();vi.clearAllMocks()})
describe('authenticated tracker attribution',()=>{
 it('keeps fallback consumption in the original customer query',async()=>{
  const delegate:RoleExecutor={descriptor:{role:'planner',providerId:'openai',connectionId:'connection',modelId:'model'},stream:vi.fn(),
   generate:vi.fn(async()=>({text:'ok',toolCalls:[],finishReason:'stop',usage:{inputTokens:1,outputTokens:1,totalTokens:2},retryCount:0,fallbackUsed:false,activeModelId:'model'}))}
  const tracked=trackRoleExecutor(delegate,{userId:'alice',snapshotId:'snapshot',observation:{snapshot:{correlationId:'fallback-route',conversationId:'conversation',source:'mcp'},fallback:{fromCorrelationId:'customer-query'}} as never})
  await tracked.generate({systemPrompt:'private',messages:[]})
  expect(vi.mocked(delegate.generate).mock.calls[0][0].meteringContext).toMatchObject({userId:'alice',turnId:'customer-query',conversationId:'conversation',channel:'mcp',parentOperationId:null})
 })
 it('records a known CLI deadline as timeout with unavailable usage',async()=>{
  const delegate:RoleExecutor={descriptor:{role:'planner',cliId:'codex',modelId:null},stream:vi.fn(),generate:vi.fn(async()=>{throw new AiConsoleError('AI_CLI_TIMEOUT')})}
  const tracked=trackRoleExecutor(delegate,{userId:'alice',snapshotId:'snapshot'})
  await expect(tracked.generate({systemPrompt:'private',messages:[]})).rejects.toMatchObject({code:'AI_CLI_TIMEOUT'})
  expect(mocks.finish.mock.calls[0][1]).toMatchObject({status:'timeout',usage:{input:null,output:null,source:'unavailable'}})
  expect(mocks.start.mock.calls[0][0]).toMatchObject({payer:'subscription',aggregation:'cli_aggregate'})
 })
})
