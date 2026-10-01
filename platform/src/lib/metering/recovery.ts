import 'server-only'
import { RecoveryEnvelopeSchema } from './schema'
import { Storage } from '@google-cloud/storage'
import { mkdir, writeFile, rename, readdir, readFile, unlink } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import type { AttemptStart, AttemptReceipt } from './types'

export interface RecoveryEnvelope { version: 1; start: AttemptStart; receipt: AttemptReceipt }
export interface RecoveryStore {
  put(envelope: RecoveryEnvelope): Promise<void>
  list(limit: number): Promise<string[]>
  read(id: string): Promise<RecoveryEnvelope>
  remove(id: string): Promise<void>
}

export function recoveryStore(): RecoveryStore {
  const bucketName = process.env.AI_METERING_RECOVERY_BUCKET
  if (bucketName) {
    const bucket = new Storage().bucket(bucketName)
    const path = (id: string) => `ai-metering/v1/${id}.json`
    return {
      async put(envelope) { envelope = RecoveryEnvelopeSchema.parse(envelope); await bucket.file(path(envelope.start.attemptId)).save(JSON.stringify(envelope),
        { resumable: false, contentType: 'application/json', preconditionOpts: { ifGenerationMatch: 0 } }) },
      async list(limit) { const [files] = await bucket.getFiles({ prefix: 'ai-metering/v1/', maxResults: limit, autoPaginate: false })
        return files.map(file => file.name.slice('ai-metering/v1/'.length).replace(/\.json$/, '')) },
      async read(id) { const [data] = await bucket.file(path(id)).download(); return JSON.parse(data.toString()) },
      async remove(id) { await bucket.file(path(id)).delete({ ignoreNotFound: true }) },
    }
  }
  if (process.env.NODE_ENV === 'production' || !process.env.AI_METERING_RECOVERY_DIR) {
    throw new Error('Durable metering recovery storage must be configured before enabling metering')
  }
  const directory = resolve(process.env.AI_METERING_RECOVERY_DIR)
  const file = (id: string) => {
    if (!/^[0-9a-f-]{36}$/.test(id)) throw new Error('Invalid receipt identity')
    return join(directory, `${id}.json`)
  }
  return {
    async put(envelope) { envelope = RecoveryEnvelopeSchema.parse(envelope); await mkdir(directory, { recursive: true, mode: 0o700 })
      const target = file(envelope.start.attemptId), temp = `${target}.${crypto.randomUUID()}.tmp`
      await writeFile(temp, JSON.stringify(envelope), { mode: 0o600 }); await rename(temp,target) },
    async list(limit) { await mkdir(directory,{ recursive: true,mode: 0o700 })
      return (await readdir(directory)).filter(name => /^[0-9a-f-]{36}\.json$/.test(name)).slice(0,limit).map(name => name.slice(0,-5)) },
    async read(id) { return JSON.parse(await readFile(file(id),'utf8')) },
    async remove(id) { await unlink(file(id)).catch(error => { if (error.code !== 'ENOENT') throw error }) },
  }
}
