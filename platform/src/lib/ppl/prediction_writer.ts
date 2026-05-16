/**
 * MARSYS Chat V2 — PPL Prediction Writer (γ3)
 *
 * Writes a prediction to the predictions table via POST /api/predictions.
 * This is the client-side writer that the PredictionLogModal uses.
 *
 * Learning Layer rule #4: outcome is NEVER sent at write time.
 */

export interface PredictionWriteInput {
  query_id: string
  conversation_id: string | null
  prediction_text: string
  confidence: number | null  // 0–1
  horizon: string | null
  falsifier: string | null
}

export interface PredictionWriteResult {
  id: string
  logged_at: string
}

export async function writePrediction(
  input: PredictionWriteInput,
): Promise<PredictionWriteResult> {
  const res = await fetch('/api/predictions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { error?: string }
    throw new Error(err.error ?? `Prediction write failed: ${res.status}`)
  }

  return res.json() as Promise<PredictionWriteResult>
}
