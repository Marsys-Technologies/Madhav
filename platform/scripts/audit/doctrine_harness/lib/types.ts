export type AssertionStatus = 'green' | 'red'

export type AssertionResult = {
  id: string
  title: string
  status: AssertionStatus
  evidence: string
  register_row?: string
}

export type AssertionDef = {
  id: string
  title: string
  register_row: string
  run: (ctx: RunContext) => Promise<AssertionResult>
}

export type RunContext = {
  client: import('./mcp_client').McpClient
  chartId: string
  secondChartId: string
}
