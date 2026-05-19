import type { LucideIcon } from 'lucide-react'

/** Command for the ⌘K keyboard palette */
export interface Command {
  id: string
  label: string
  hint?: string
  icon: LucideIcon
  keywords?: string
  run: () => void
  section?: string
}

/** Command for the inline / slash trigger */
export interface SlashCommand {
  id: string
  name: string
  description: string
  template?: string
  run?: () => void
}

export const COMMANDS: SlashCommand[] = [
  {
    id: 'dasha',
    name: 'dasha',
    description: 'Dasha period analysis',
    template: 'Analyse the current Dasha period and its major themes for ',
  },
  {
    id: 'chart',
    name: 'chart',
    description: 'Full chart reading',
    template: 'Give a detailed chart reading focusing on ',
  },
  {
    id: 'prediction',
    name: 'prediction',
    description: 'Time-indexed prediction',
    template: 'Make a time-indexed prediction for the period ',
  },
  {
    id: 'transit',
    name: 'transit',
    description: 'Transit analysis',
    template: 'Analyse current planetary transits and their impact on ',
  },
  {
    id: 'yoga',
    name: 'yoga',
    description: 'Yoga identification and interpretation',
    template: 'Identify and interpret the active yogas in the chart relevant to ',
  },
  {
    id: 'navamsa',
    name: 'navamsa',
    description: 'Navamsa chart reading',
    template: 'Read the Navamsa chart and cross-reference with the Rasi chart for ',
  },
]
