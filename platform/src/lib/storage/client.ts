import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'
import 'server-only'
import { Storage, Bucket } from '@google-cloud/storage'

let _storage: Storage | null = null
function gcs() {
  if (!_storage) _storage = new Storage({ projectId: readGoogleCloudEnv('GOOGLE_CLOUD_PROJECT') })
  return _storage
}

export function chatBucket(): Bucket {
  return gcs().bucket(process.env.GCS_BUCKET_CHAT_ATTACHMENTS!)
}

export function chartDocsBucket(): Bucket {
  return gcs().bucket(process.env.GCS_BUCKET_CHART_DOCUMENTS!)
}

/** Upload a Buffer to GCS. Overwrites if the path already exists. */
export async function gcsUpload(
  bucket: Bucket,
  destPath: string,
  data: Buffer | string,
  contentType: string
): Promise<void> {
  const buf = typeof data === 'string' ? Buffer.from(data, 'utf-8') : data
  await bucket.file(destPath).save(buf, { contentType })
}

/** Download a file from GCS. Returns text content. */
export async function gcsDownloadText(
  bucket: Bucket,
  filePath: string
): Promise<string | null> {
  try {
    const [buf] = await bucket.file(filePath).download()
    return buf.toString('utf-8')
  } catch {
    return null
  }
}

/** Delete a file from GCS. Silently ignores if not found. */
export async function gcsDelete(bucket: Bucket, filePath: string): Promise<void> {
  try {
    await bucket.file(filePath).delete()
  } catch { /* ignore */ }
}

/** Generate a signed download URL (default 1h TTL). */
export async function gcsSignedDownload(
  bucket: Bucket,
  filePath: string,
  ttlMs = 60 * 60 * 1000
): Promise<string> {
  const [url] = await bucket.file(filePath).getSignedUrl({
    action: 'read',
    expires: Date.now() + ttlMs,
  })
  return url
}

/** Generate a signed upload URL (default 10min TTL). */
export async function gcsSignedUpload(
  bucket: Bucket,
  filePath: string,
  contentType: string,
  ttlMs = 10 * 60 * 1000
): Promise<string> {
  const [url] = await bucket.file(filePath).getSignedUrl({
    action: 'write',
    expires: Date.now() + ttlMs,
    contentType,
  })
  return url
}
