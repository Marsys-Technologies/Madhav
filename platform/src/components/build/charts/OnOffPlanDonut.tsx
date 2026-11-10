'use client'

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { isOnPlan } from '../colors'
import type { SessionIndex } from '@/lib/build/types'

interface Props {
  sessions: SessionIndex[]
  height?: number
}

export function OnOffPlanDonut({ sessions, height = 120 }: Props) {
  const onPlan = sessions.filter((s) => isOnPlan(s.class)).length
  const offPlan = sessions.length - onPlan
  const data = [
    { name: 'On-plan', value: onPlan, color: '#3b82f6' },
    { name: 'Off-plan', value: offPlan, color: '#a855f7' },
  ].filter((d) => d.value > 0)

  const pct = sessions.length > 0 ? Math.round((onPlan / sessions.length) * 100) : 0

  return (
    <div className="flex flex-col items-center">
      <p className="bt-label mb-2">On vs off plan</p>
      <div className="relative" style={{ height }}>
        <ResponsiveContainer width={height} height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={height * 0.28}
              outerRadius={height * 0.44}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={((v: number, name: string) => [`${v} sessions`, name]) as never}
              contentStyle={{ fontSize: 11 }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="bt-num text-lg">{pct}%</span>
          <span className="bt-label">on-plan</span>
        </div>
      </div>
    </div>
  )
}
