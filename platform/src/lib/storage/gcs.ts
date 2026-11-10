import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'
import { Storage } from '@google-cloud/storage'
import { telemetry } from '../telemetry/index'

let _storage: Storage | null = null

function getStorage(): Storage {
  if (!_storage) {
    _storage = new Storage({ projectId: readGoogleCloudEnv('GOOGLE_CLOUD_PROJECT') })
  }
  return _storage
}

export const gcsAdapter = {
  async readObject(bucket: string, path: string): Promise<Buffer> {
    const start = Date.now()
    const [buf] = await getStorage().bucket(bucket).file(path).download()
    telemetry.recordLatency('storage.gcs', 'readObject', Date.now() - start)
    return buf as Buffer
  },

  async writeObject(bucket: string, path: string, content: Buffer | string, contentType?: string): Promise<void> {
    const start = Date.now()
    const buf = typeof content === 'string' ? Buffer.from(content, 'utf-8') : content
    await getStorage().bucket(bucket).file(path).save(buf, contentType ? { contentType } : undefined)
    telemetry.recordLatency('storage.gcs', 'writeObject', Date.now() - start)
  },

  async objectExists(bucket: string, path: string): Promise<boolean> {
    const start = Date.now()
    const [exists] = await getStorage().bucket(bucket).file(path).exists()
    telemetry.recordLatency('storage.gcs', 'objectExists', Date.now() - start)
    return exists
  },
}
