import type { CallType } from '@/lib/models/registry'

const SYNTHESIS_PROBE = `You are a Jyotish analysis assistant. In one short paragraph (3-5 sentences),
describe the significance of Mars in the 7th house for a native with Aries ascendant.
Be concise and precise. Do not use headers or bullet points.`

const PLANNER_PROBE = `You are a query planning assistant. Return a JSON object with this exact shape:
{"plan": ["step_1", "step_2"], "confidence": 0.9, "reasoning": "brief reason"}
Plan for this query: "What is the significance of Jupiter in the 5th house?"`

const WORKER_PROBE = `Summarize in exactly one sentence:
The ascendant (lagna) is the first house in a Jyotish chart, representing the self and body.`

const EVAL_PROBE = `Rate the following astrological claim on a scale of 1-10 for accuracy and depth.
Claim: "Saturn in the 10th house indicates a disciplined career focus."
Respond with only: {"score": <number>, "rationale": "<one sentence>"}`

const CHECKPOINT_PROBE = `Is the following query clear and unambiguous? Answer with only: {"clear": true} or {"clear": false, "issue": "<brief reason>"}
Query: "What does Jupiter transit the 5th house mean for Aries ascendant?"`

export function getProbePrompt(callType: CallType): string {
  switch (callType) {
    case 'synthesis':
    case 'context_assembly':
    case 'smoke_synth':
      return SYNTHESIS_PROBE
    case 'planner_deep':
    case 'planner_fast':
      return PLANNER_PROBE
    case 'worker':
      return WORKER_PROBE
    case 'eval_judge':
    case 'eval_generator':
      return EVAL_PROBE
    case 'checkpoint_4_5':
    case 'checkpoint_5_5':
    case 'checkpoint_8_5':
      return CHECKPOINT_PROBE
  }
}
