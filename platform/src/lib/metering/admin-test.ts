import 'server-only'
import { generateText } from 'ai'
import { listAiConsoleState } from '@/lib/ai-console/repository'
import { createConnectionRuntimeBinding } from '@/lib/ai-console/providers'
import { ProviderIdSchema,AiRoleSchema } from '@/lib/ai-console/types'
import { meterModel } from './model'
/** Runs only an authenticated administrator's own validated connection. */
export async function runMeteredTest(userId:string,connectionId:string,modelId:string,signal?:AbortSignal) {
  const state=await listAiConsoleState(userId)
  const connection=state.connections.find(row=>row.id===connectionId && !row.deleted_at && row.validation_state==='validated')
  const model=state.models.find(row=>row.connection_id===connectionId && row.model_id===modelId && row.available)
  if(!connection || !model) throw new Error('Owned validated model required')
  const discovered={ modelId,displayName:String(model.display_name),
    compatibleRoles:Array.isArray(model.compatible_roles)?model.compatible_roles.map(role=>AiRoleSchema.parse(role)):[],
    supportsTools:model.supports_tools===true,supportsStructuredOutput:model.supports_structured_output===true }
  const binding=await createConnectionRuntimeBinding({ userId,connectionId,
    providerId:ProviderIdSchema.parse(connection.provider_id),credentialVersion:Number(connection.credential_version) },discovered)
  const testRunId=crypto.randomUUID()
  try {
    await generateText({ model:meterModel(binding.model,{ userId,conversationId:null,turnId:testRunId,operationId:crypto.randomUUID(),
      channel:'backend',purpose:'admin_test',payer:'user',provider:binding.providerId,model:modelId,role:'admin_test',
      connectionId,testRunId,aggregation:'transport' }),prompt:'Reply OK.',maxOutputTokens:16,maxRetries:0,
      abortSignal:AbortSignal.any([AbortSignal.timeout(30000),...(signal?[signal]:[])]) })
    return { testRunId,status:'completed' }
  } finally { binding.dispose() }
}
