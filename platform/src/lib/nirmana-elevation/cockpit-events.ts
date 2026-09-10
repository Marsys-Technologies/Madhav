import 'server-only'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

export async function publishCockpitEvent(event: { type: string; [key: string]: unknown }): Promise<void> {
  if (process.env.PUBSUB_DISABLED || !process.env.GOOGLE_CLOUD_PROJECT) return
  try {
    const { PubSub } = await import('@google-cloud/pubsub')
    const client = new PubSub({ projectId: process.env.GOOGLE_CLOUD_PROJECT })
    const topic = client.topic(process.env.PUBSUB_TOPIC ?? 'cockpit-events')
    const payload = { chart_id: CANONICAL_CHART_ID, ...event }
    await topic.publishMessage({
      data: Buffer.from(JSON.stringify(payload)),
      attributes: { chart_id: CANONICAL_CHART_ID, type: String(event.type) },
    })
  } catch (err) {
    console.error('[nirmana-elevation/cockpit-events] publish failed:', (err as Error).message)
  }
}
