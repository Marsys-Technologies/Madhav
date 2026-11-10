import { parse } from 'yaml'

export interface WorkflowStep {
  id?: string
  name?: string
  run?: string
  uses?: string
  if?: string
  env?: Record<string, string>
  with?: Record<string, unknown>
  'timeout-minutes'?: number
}

interface WorkflowJob {
  steps: WorkflowStep[]
  if?: string
  needs?: string
  environment?: string
  env?: Record<string, string>
  outputs?: Record<string, string>
  'runs-on'?: string
  'timeout-minutes'?: number
}

interface Workflow {
  jobs: Record<string, WorkflowJob>
  on: Record<string, unknown>
  permissions: Record<string, string>
  env: Record<string, string>
  concurrency: { group: string; 'cancel-in-progress': boolean }
}

export function parseWorkflow(text: string): Workflow {
  return parse(text) as Workflow
}

export function parseCompositeSteps(text: string): WorkflowStep[] {
  const action = parse(text) as { runs: { steps: WorkflowStep[] } }
  return action.runs.steps
}

export function requireStep(steps: WorkflowStep[], predicate: (step: WorkflowStep) => unknown): WorkflowStep {
  const step = steps.find(predicate)
  if (!step) throw new Error(`Missing workflow step matching ${predicate}`)
  return step
}

export function shellSource(step: WorkflowStep): string {
  if (typeof step.run !== 'string') throw new Error(`Missing run script for step ${step.name ?? step.id}`)
  return step.run
}

export function timeoutMinutes(item: WorkflowStep | WorkflowJob): number {
  const timeout = item['timeout-minutes']
  if (typeof timeout !== 'number') throw new Error('Missing numeric workflow timeout')
  return timeout
}
