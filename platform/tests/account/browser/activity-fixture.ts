/** Every displayed fixture count is derived from the same fictional ledger. */
const connection = "11111111-1111-4111-8111-111111111111";
const ledger = [
  {
    id: "11111111-1111-4111-8111-111111111101",
    day: "2026-10-01",
    status: "success",
    aggregation: "transport",
    provider: "openrouter",
    model: "anthropic/fictional",
    connection_id: connection,
    input: 120,
    output: 30,
    cost: "0.002",
    latency: 1400,
  },
  {
    id: "11111111-1111-4111-8111-111111111102",
    day: "2026-10-02",
    status: "error",
    aggregation: "transport",
    provider: "openrouter",
    model: "anthropic/fictional",
    connection_id: connection,
    input: null,
    output: null,
    cost: null,
    latency: null,
  },
  {
    id: "11111111-1111-4111-8111-111111111103",
    day: "2026-10-03",
    status: "success",
    aggregation: "transport",
    provider: "openrouter",
    model: "anthropic/fictional",
    connection_id: connection,
    input: 80,
    output: 20,
    cost: "0.002",
    latency: 1400,
  },
  {
    id: "11111111-1111-4111-8111-111111111104",
    day: "2026-10-03",
    status: "success",
    aggregation: "cli_aggregate",
    provider: "claude_code",
    model: "fictional-cli",
    connection_id: null,
    input: null,
    output: null,
    cost: null,
    latency: null,
  },
].map((r) => ({
  ...r,
  user_id: "fictional-account",
  conversation_id: null,
  turn_id: r.id,
  operation_id: r.id,
  parent_operation_id: null,
  channel: "web",
  purpose: "customer",
  role: "synthesizer",
  evidence: "metered",
  started_at: r.day + "T12:00:00Z",
  finished_at: r.latency == null ? null : r.day + "T12:00:01.400Z",
  usage:
    r.input == null
      ? null
      : { input: r.input, output: r.output, source: "provider" },
  computed_cost_usd: r.cost,
  provider_cost_usd: null,
  pricing_status: r.cost == null ? "unpriced" : "estimated",
  pricing_snapshot: null,
  provider_request_id: null,
}));
type Row = (typeof ledger)[number];
function totals(rows: Row[]) {
  const api = rows.filter((r) => r.aggregation === "transport"),
    cli = rows.filter((r) => r.aggregation === "cli_aggregate"),
    sum = (key: "input" | "output") =>
      api.some((r) => r[key] != null)
        ? String(api.reduce((n, r) => n + (r[key] ?? 0), 0))
        : null;
  return {
    records: rows.length,
    transport_attempts: api.length,
    transport_success: api.filter((r) => r.status === "success").length,
    transport_failed: api.filter((r) => r.status === "error").length,
    transport_pending: 0,
    customer_attempts: api.length,
    validation_attempts: 0,
    cli_executions: cli.length,
    complete_usage: api.filter((r) => r.input != null && r.output != null)
      .length,
    transport_unpriced: api.filter((r) => r.cost == null).length,
    input_tokens: sum("input"),
    output_tokens: sum("output"),
    known_transport_cost_usd: api.some((r) => r.cost != null)
      ? String(api.reduce((n, r) => n + Number(r.cost ?? 0), 0))
      : null,
    provider_transport_cost_usd: null,
    provider_reported_cost_usd: null,
    cli_input_tokens: null,
    cli_output_tokens: null,
    legacy_records: 0,
    legacy_estimate_usd: null,
    p50_success_ms: api.some((r) => r.latency != null) ? 1400 : null,
  };
}
export function fixtureActivity(q: URLSearchParams) {
  const rows = ledger.filter(
    (r) =>
      (!q.get("from") || r.started_at >= q.get("from")!) &&
      (!q.get("to") || r.started_at < q.get("to")!) &&
      ["channel", "purpose", "provider", "model", "aggregation"].every(
        (key) => !q.get(key) || String(r[key as keyof Row]) === q.get(key),
      ) &&
      (!q.get("connectionId") || r.connection_id === q.get("connectionId")) &&
      (!q.get("recordId") || r.id === q.get("recordId")),
  );
  const view = q.get("view");
  if (view === "summary") return totals(rows);
  if (view === "breakdown")
    return {
      groups: [...new Set(rows.map((r) => r.day))].map((name) => ({
        name,
        ...totals(rows.filter((r) => r.day === name)),
      })),
    };
  if (view === "connections") {
    const keys = [
      ...new Set(
        rows.map(
          (r) => `${r.aggregation}:${r.provider}:${r.model}:${r.connection_id}`,
        ),
      ),
    ];
    return {
      groups: keys.map((key) => {
        const group = rows.filter(
            (r) =>
              `${r.aggregation}:${r.provider}:${r.model}:${r.connection_id}` ===
              key,
          ),
          r = group[0];
        return {
          ...totals(group),
          aggregation: r.aggregation,
          provider: r.provider,
          model: r.model,
          connection_id: r.connection_id,
        };
      }),
      totalGroups: keys.length,
      truncated: false,
    };
  }
  if (view === "conversations")
    return {
      conversations: rows
        .filter((r) => r.aggregation === "transport")
        .map((r) => ({
          key: r.id,
          conversation_id: null,
          user_id: r.user_id,
          channel: r.channel,
          purpose: r.purpose,
          model: r.model,
          first_at: r.started_at,
          last_at: r.started_at,
          turns: 1,
          attempts: 1,
          success: r.status === "success" ? 1 : 0,
          incomplete_usage: r.usage ? 0 : 1,
          unpriced: r.cost ? 0 : 1,
          input_tokens: r.input == null ? null : String(r.input),
          output_tokens: r.output == null ? null : String(r.output),
          known_cost_usd: r.cost,
          snippet: null,
        })),
      nextCursor: null,
    };
  return { events: rows, nextCursor: null };
}
