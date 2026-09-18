/** Read-only command adapter for merge_queue_supervisor.ts. */
import { evaluateQueueObservation, type QueueSupervisorObservation } from './merge_queue_supervisor'

function main(): void {
  const raw = process.env.MERGE_QUEUE_SUPERVISOR_OBSERVATION_JSON
  if (!raw) {
    throw new Error('MERGE_QUEUE_SUPERVISOR_OBSERVATION_JSON is required')
  }
  const observation = JSON.parse(raw) as QueueSupervisorObservation
  const decision = evaluateQueueObservation(observation)
  process.stdout.write(`${JSON.stringify(decision)}\n`)
}

main()
