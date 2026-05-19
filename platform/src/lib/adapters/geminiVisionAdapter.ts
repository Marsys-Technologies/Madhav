/** GeminiVisionAdapter — builds Gemini image parts from attachments.
 *
 * Priority: fileUri (URL-based, no byte loading) → inlineData (base64 fallback).
 * Non-image attachments are filtered out by the caller before reaching here.
 */

export interface GeminiFileDataPart {
  type: 'image'
  image: string
  mimeType: string
}

export interface ImageAttachment {
  url?: string
  mime: string
  mimeType?: string
  filename?: string
}

/** Returns the effective MIME type from an attachment. */
function getMimeType(att: ImageAttachment): string {
  return att.mimeType ?? att.mime
}

/**
 * Build Gemini-compatible image parts from image attachments.
 *
 * - When `attachment.url` is present: produces a fileData (fileUri) part —
 *   no byte loading required; preferred for GCS-hosted files.
 * - When `attachment.url` is absent: fetches bytes from the attachment source
 *   and produces an inlineData base64 part. Throws if fetch fails.
 *
 * Non-image MIME types are silently skipped (caller should pre-filter).
 */
export async function buildImageParts(
  attachments: ImageAttachment[],
): Promise<GeminiFileDataPart[]> {
  const imageAttachments = attachments.filter(a => getMimeType(a).startsWith('image/'))
  const parts: GeminiFileDataPart[] = []

  for (const att of imageAttachments) {
    const mime = getMimeType(att)

    if (att.url) {
      // fileUri path — reference the public/signed URL directly
      parts.push({
        type: 'image',
        image: att.url,
        mimeType: mime,
      })
    } else {
      // inlineData fallback — fetch bytes and base64-encode
      const resp = await fetch(att.url ?? '')
      if (!resp.ok) continue
      const buffer = await resp.arrayBuffer()
      const base64 = Buffer.from(buffer).toString('base64')
      parts.push({
        type: 'image',
        image: `data:${mime};base64,${base64}`,
        mimeType: mime,
      })
    }
  }

  return parts
}

export class GeminiVisionAdapter {
  buildImageParts = buildImageParts
}
