import 'server-only'
import { RecoveryEnvelopeSchema } from './schema'
import type { AttemptStart, AttemptReceipt, MeteringContext } from './types'
import { insertAttempt, insertReceipt, type MeteringDb } from './repository'
import { recoveryStore, type RecoveryStore } from './recovery'

export interface MeteringDependencies { db?: MeteringDb; recovery?: RecoveryStore }
export async function startAttempt(context: MeteringContext, dependencies: MeteringDependencies = {}): Promise<AttemptStart> {
  // Resolve recovery configuration before charging a provider, not only after a failure.
  if (!dependencies.recovery) recoveryStore()
  const start: AttemptStart = { ...context, attemptId: crypto.randomUUID(), startedAt: new Date().toISOString() }
  await insertAttempt(start, dependencies.db)
  return start
}
export async function finishAttempt(start: AttemptStart, receipt: AttemptReceipt, dependencies: MeteringDependencies = {}): Promise<void> {
  try { await insertReceipt(start,receipt,dependencies.db) }
  catch {
    await (dependencies.recovery ?? recoveryStore()).put({ version: 1,start,receipt })
  }
}
export async function recoverReceipts(dependencies: MeteringDependencies = {}, limit = 100) {
  const store = dependencies.recovery ?? recoveryStore()
  let recovered = 0, failed = 0
  for (const id of await store.list(Math.min(Math.max(limit,1),500))) {
    try {
      const envelope = RecoveryEnvelopeSchema.parse(await store.read(id))
      if (envelope.version !== 1 || envelope.start.attemptId !== id || envelope.receipt.attemptId !== id) throw new Error('Invalid recovery envelope')
      await insertAttempt(envelope.start,dependencies.db)
      await insertReceipt(envelope.start,envelope.receipt,dependencies.db)
      await store.remove(id); recovered++
    } catch { failed++ }
  }
  return { recovered, failed }
}
