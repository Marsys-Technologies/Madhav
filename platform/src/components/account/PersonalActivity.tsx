"use client";
import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useObservatoryScope } from "@/components/observatory/ObservatoryScope";
import {
  Consumption,
  useMetering,
  type Totals,
  type Conversation,
} from "@/components/observatory/ObservatoryDashboard";
import { personalActivityFilters } from "@/lib/account/activity-filters";
import { useAiAccountState } from "./useAiAccountState";
import type { UsageEvent, UsageConnectionGroup } from "@/lib/metering/queries";

type PersonalTotals = Totals & {
  cli_executions: number;
  provider_transport_cost_usd: string | null;
};
type Day = PersonalTotals & { name: string };
const count = (n: number | string | null | undefined) =>
  n == null ? "Not reported" : Number(n).toLocaleString("en-IN");
const cost = (n: number | string | null | undefined) =>
  n == null ? "Not reported" : `$${Number(n).toFixed(4)}`;
const duration = (n: number | null | undefined) =>
  n == null ? "Not reported" : `${(n / 1000).toFixed(2)} s`;
function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <div className="j5-panel">
      <p className="j5-eyebrow">{label}</p>
      <p className="j5-metric">{value}</p>
      {note && <p className="j1-note">{note}</p>}
    </div>
  );
}

export function PersonalActivity({
  view,
}: {
  view: "observatory" | "consumption";
}) {
  const search = useSearchParams(),
    [now] = useState(() => new Date()),
    { userId } = useObservatoryScope();
  let params: URLSearchParams;
  try {
    params = personalActivityFilters(search, now);
  } catch {
    return (
      <div className="j5-panel" role="alert">
        Choose a valid period of up to 90 days and valid activity filters.{" "}
        <a href={`/account/ai-cockpit/${view}`}>Reset filters</a>
      </div>
    );
  }
  return <Activity key={`${userId}:${params}`} view={view} params={params} />;
}
function Activity({
  view,
  params,
}: {
  view: "observatory" | "consumption";
  params: URLSearchParams;
}) {
  const ai = useAiAccountState();
  const connectionNames = new Map(
    ai.state?.connections.map((c) => [c.id, c.name]),
  );
  const query = params.toString(),
    base = `/api/usage?${query}`;
  const summary = useMetering<PersonalTotals>(`${base}&view=summary`);
  const daily = useMetering<{ groups: Day[] }>(
    view === "observatory" ? `${base}&view=breakdown&groupBy=day` : null,
  );
  const connections = useMetering<{
    groups: UsageConnectionGroup[];
    truncated: boolean;
    totalGroups: number;
  }>(`${base}&view=connections`);
  const conversations = useMetering<{
    conversations: Conversation[];
    nextCursor: string | null;
  }>(view === "consumption" ? `${base}&view=conversations&limit=25` : null);
  const error =
    summary.error || daily.error || connections.error || conversations.error;
  const loading =
    summary.loading ||
    daily.loading ||
    connections.loading ||
    conversations.loading;
  return (
    <div className="j5-activity">
      <p className="j1-note">
        Your recorded activity only. Dates use UTC. These filters apply to
        totals, charts and details on both activity pages.
      </p>
      <ActivityFilters
        params={params}
        groups={connections.data?.groups ?? []}
        names={connectionNames}
      />
      {loading && (
        <p className="j5-panel" role="status">
          Loading activity…
        </p>
      )}
      {error && (
        <div className="j5-panel" role="alert">
          {error}{" "}
          <button
            type="button"
            className="j1-btn"
            onClick={() => {
              summary.retry();
              daily.retry();
              connections.retry();
              conversations.retry();
            }}
          >
            Retry activity
          </button>
        </div>
      )}
      {!loading && !error && summary.data && (
        <>
          <div className="j5-metrics">
            <Metric
              label="API calls"
              value={count(summary.data.transport_attempts)}
              note="Each recorded provider transport counted once"
            />
            <Metric
              label="CLI executions"
              value={count(summary.data.cli_executions)}
              note="Execution summaries; may include API calls already counted"
            />
            <Metric
              label="Successful API calls"
              value={count(summary.data.transport_success)}
              note={`${count(summary.data.transport_pending)} pending`}
            />
            <Metric
              label="Median API response"
              value={duration(summary.data.p50_success_ms)}
              note="Successful calls with recorded duration"
            />
          </div>
          <div className="j5-metrics">
            <Metric
              label="Provider-reported cost"
              value={cost(summary.data.provider_transport_cost_usd)}
              note="Reported API receipts only; partial when absent"
            />
            <Metric
              label="Calculated estimate"
              value={cost(summary.data.known_transport_cost_usd)}
              note={`${count(summary.data.transport_unpriced)} API calls unpriced; not a provider invoice`}
            />
          </div>
          {!summary.data.transport_attempts &&
            !summary.data.cli_executions &&
            !summary.data.legacy_records && (
              <p className="j5-panel">No recorded activity in this period.</p>
            )}
          {view === "observatory" ? (
            <>
              <ActivityChart days={daily.data?.groups ?? []} />
              <ConnectionHierarchy
                groups={connections.data?.groups ?? []}
                truncated={connections.data?.truncated ?? false}
                totalGroups={connections.data?.totalGroups ?? 0}
                names={connectionNames}
              />
              <p className="j1-note">
                Connection and model names reflect recorded attribution.
                Tool-family taxonomy remains provisional; tool health is not
                inferred from call success.
              </p>
            </>
          ) : (
            <>
              <Consumption
                summary={summary.data}
                initial={conversations.data}
                baseUrl={base}
                portal={false}
              />
              <CliExecutions baseUrl={base} />
            </>
          )}
        </>
      )}
    </div>
  );
}
function ActivityFilters({
  params,
  groups,
  names,
}: {
  params: URLSearchParams;
  groups: UsageConnectionGroup[];
  names: Map<string, string>;
}) {
  const router = useRouter(),
    path = usePathname(),
    [draft, setDraft] = useState(() => Object.fromEntries(params)),
    [error, setError] = useState<string | null>(null);
  const options = new Map(
    groups
      .filter((g) => g.connection_id)
      .map((g) => [
        g.connection_id!,
        `${g.provider} · ${names.get(g.connection_id!) ?? "Recorded connection " + g.connection_id!.slice(0, 8)}`,
      ]),
  );
  if (draft.connectionId && !options.has(draft.connectionId))
    options.set(
      draft.connectionId,
      names.get(draft.connectionId) ?? "Selected recorded connection",
    );
  const [fromDate, setFromDate] = useState(params.get("from")!.slice(0, 10)),
    [toDate, setToDate] = useState(
      new Date(Date.parse(params.get("to")!) - 1).toISOString().slice(0, 10),
    ),
    [dateDirty, setDateDirty] = useState(false);
  function apply(e: React.FormEvent) {
    e.preventDefault();
    try {
      const next = new URLSearchParams(draft);
      if (dateDirty) {
        next.set("from", new Date(`${fromDate}T00:00:00Z`).toISOString());
        next.set(
          "to",
          new Date(Date.parse(`${toDate}T00:00:00Z`) + 86400000).toISOString(),
        );
      }
      router.replace(`${path}?${personalActivityFilters(next)}`);
      setError(null);
    } catch {
      setError(
        "Choose valid UTC dates, no more than 90 days, and a valid connection ID.",
      );
    }
  }
  return (
    <form className="j5-panel j5-filter" onSubmit={apply}>
      <div className="j5-filter-fields">
        <label>
          From · UTC
          <input
            type="date"
            value={fromDate}
            onChange={(e) => {
              setFromDate(e.target.value);
              setDateDirty(true);
            }}
            required
          />
        </label>
        <label>
          Through · UTC
          <input
            type="date"
            value={toDate}
            onChange={(e) => {
              setToDate(e.target.value);
              setDateDirty(true);
            }}
            required
          />
        </label>
        <label>
          Channel
          <select
            value={draft.channel ?? ""}
            onChange={(e) => setDraft({ ...draft, channel: e.target.value })}
          >
            <option value="">All channels</option>
            {["web", "mcp", "api", "backend", "scheduled", "unknown"].map(
              (c) => (
                <option key={c}>{c}</option>
              ),
            )}
          </select>
        </label>
        <label>
          Purpose
          <select
            value={draft.purpose ?? ""}
            onChange={(e) => setDraft({ ...draft, purpose: e.target.value })}
          >
            <option value="">All purposes</option>
            {[
              "customer",
              "admin_test",
              "validation",
              "evaluation",
              "background",
              "legacy",
            ].map((p) => (
              <option key={p} value={p}>
                {p.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label>
          Source
          <select
            value={draft.aggregation ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, aggregation: e.target.value })
            }
          >
            <option value="">API and CLI · separate counts</option>
            <option value="transport">API provider calls</option>
            <option value="cli_aggregate">CLI execution summaries</option>
            <option value="legacy_aggregate">Historical estimates</option>
          </select>
        </label>
        <label>
          Connection
          <select
            value={draft.connectionId ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, connectionId: e.target.value })
            }
          >
            <option value="">All recorded connections</option>
            {[...options].map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        {(["provider", "model"] as const).map((key) => (
          <label key={key}>
            {key === "provider" ? "Provider or CLI product" : "Model"}
            <input
              value={draft[key] ?? ""}
              onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
              placeholder="All"
              maxLength={key === "model" ? 256 : 64}
            />
          </label>
        ))}
      </div>
      <div className="j5-actions">
        <button type="submit" className="j1-btn j1-btn-gold">
          Apply filters
        </button>
        <a className="j1-btn" href={path}>
          Reset
        </a>
      </div>
      {error && (
        <p role="alert" className="j1-error">
          {error}
        </p>
      )}
    </form>
  );
}
function ActivityChart({ days }: { days: Day[] }) {
  const sorted = [...days].sort((a, b) => a.name.localeCompare(b.name)),
    maxCalls = Math.max(1, ...sorted.map((d) => d.transport_attempts)),
    maxSeconds = Math.max(
      1,
      ...sorted.map((d) => (d.p50_success_ms ?? 0) / 1000),
    );
  const x = (i: number) => 60 + ((i + 0.5) * 560) / Math.max(1, sorted.length),
    paths: string[] = [];
  let path = "";
  for (const [i, d] of sorted.entries()) {
    if (d.p50_success_ms == null) {
      if (path) paths.push(path);
      path = "";
    } else {
      path += `${path ? " L" : "M"}${x(i)},${190 - (d.p50_success_ms / 1000 / maxSeconds) * 140}`;
    }
  }
  if (path) paths.push(path);
  return (
    <section className="j5-panel">
      <h2>Activity and response time</h2>
      <p className="j1-note">
        Gold bars: API calls. Green bars: successful API calls. Cream line:
        median response seconds. Missing duration leaves a gap. CLI executions
        are separate in the values below.
      </p>
      {!sorted.length ? (
        <p>No activity to chart.</p>
      ) : (
        <>
          <div className="j5-chart-scroll">
            <svg
              viewBox="0 0 720 250"
              role="img"
              aria-label="Daily API call counts and median response seconds, UTC"
            >
              <text x="16" y="20" fill="#c5a059">
                API calls
              </text>
              <text x="630" y="20" fill="#e8dfc9">
                Seconds
              </text>
              {[0, 0.5, 1].map((t) => (
                <g key={t}>
                  <line
                    x1="60"
                    x2="620"
                    y1={190 - t * 140}
                    y2={190 - t * 140}
                    stroke="#382b18"
                  />
                  <text
                    x="45"
                    y={195 - t * 140}
                    textAnchor="end"
                    fill="#a99c82"
                  >
                    {Math.round(maxCalls * t)}
                  </text>
                  <text x="635" y={195 - t * 140} fill="#a99c82">
                    {(maxSeconds * t).toFixed(1)}
                  </text>
                </g>
              ))}
              {sorted.map((d, i) => (
                <g key={d.name}>
                  <rect
                    x={x(i) - Math.min(20, 220 / sorted.length)}
                    y={190 - (d.transport_attempts / maxCalls) * 140}
                    width={Math.min(20, 220 / sorted.length)}
                    height={(d.transport_attempts / maxCalls) * 140}
                    fill="#c5a059"
                  />
                  <rect
                    x={x(i)}
                    y={190 - (d.transport_success / maxCalls) * 140}
                    width={Math.min(20, 220 / sorted.length)}
                    height={(d.transport_success / maxCalls) * 140}
                    fill="#8caa90"
                  />
                  {d.p50_success_ms != null && (
                    <circle
                      cx={x(i)}
                      cy={190 - (d.p50_success_ms / 1000 / maxSeconds) * 140}
                      r="3"
                      fill="#e8dfc9"
                    />
                  )}
                  <title>
                    {d.name}: {d.transport_attempts} API calls;{" "}
                    {d.transport_success} successful;{" "}
                    {duration(d.p50_success_ms)}
                  </title>
                </g>
              ))}
              {paths.map((p, i) => (
                <path
                  key={i}
                  d={p}
                  fill="none"
                  stroke="#e8dfc9"
                  strokeWidth="2"
                />
              ))}
              <text x="60" y="225" fill="#a99c82">
                {sorted[0].name} · UTC
              </text>
              <text x="620" y="225" textAnchor="end" fill="#a99c82">
                {sorted.at(-1)?.name} · UTC
              </text>
            </svg>
          </div>
          <details>
            <summary>View daily values</summary>
            <div className="j5-table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Day · UTC</th>
                    <th>API calls</th>
                    <th>Successful</th>
                    <th>CLI executions</th>
                    <th>Median · seconds</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((d) => (
                    <tr key={d.name}>
                      <td>{d.name}</td>
                      <td>{count(d.transport_attempts)}</td>
                      <td>{count(d.transport_success)}</td>
                      <td>{count(d.cli_executions)}</td>
                      <td>{duration(d.p50_success_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </section>
  );
}
function ConnectionHierarchy({
  groups,
  truncated,
  totalGroups,
  names,
}: {
  groups: UsageConnectionGroup[];
  truncated: boolean;
  totalGroups: number;
  names: Map<string, string>;
}) {
  const buckets = new Map<string, UsageConnectionGroup[]>();
  for (const g of groups) {
    const key =
      g.aggregation === "transport"
        ? `API · ${g.provider} · ${g.connection_id ? (names.get(g.connection_id) ?? "Recorded connection " + g.connection_id.slice(0, 8)) : "Connection not recorded"}`
        : g.aggregation === "cli_aggregate"
          ? `CLI · ${g.provider}`
          : `Historical · ${g.provider}`;
    buckets.set(key, [...(buckets.get(key) ?? []), g]);
  }
  return (
    <section className="j5-panel">
      <h2>Connections and models</h2>
      <p className="j1-note">
        API connections → recorded model. CLI product → recorded model.
        Aggregator names and the underlying model are retained as recorded.
      </p>
      {!buckets.size && <p>No attributed activity in this scope.</p>}
      {[...buckets].map(([name, rows]) => (
        <details key={name} className="j5-connection">
          <summary>{name}</summary>
          {rows.map((g) => (
            <div
              key={`${g.aggregation}:${g.provider}:${g.connection_id}:${g.model}`}
            >
              <h3>{g.model || "Model not recorded"}</h3>
              <p>
                {g.aggregation === "transport"
                  ? `${count(g.transport_attempts)} API calls · ${count(g.transport_success)} successful · ${duration(g.p50_success_ms == null ? null : Number(g.p50_success_ms))} median`
                  : `${count(g.records)} ${g.aggregation === "cli_aggregate" ? "CLI executions" : "historical records"}`}
              </p>
              <p className="j1-note">
                {g.aggregation === "transport"
                  ? `Provider-reported ${cost(g.provider_transport_cost_usd)} · calculated estimate ${cost(g.known_transport_cost_usd)}`
                  : g.aggregation === "cli_aggregate"
                    ? `Reported input ${count(g.cli_input_tokens)} · output ${count(g.cli_output_tokens)} · cost ${cost(g.provider_reported_cost_usd)}`
                    : `Historical estimate ${cost(g.legacy_estimate_usd)}`}
              </p>
            </div>
          ))}
        </details>
      ))}
      {truncated && (
        <p role="status">
          Showing 200 of {count(totalGroups)} model groups. Narrow your filters
          for the remaining groups.
        </p>
      )}
    </section>
  );
}
function CliExecutions({ baseUrl }: { baseUrl: string }) {
  const initial = useMetering<{
      events: UsageEvent[];
      nextCursor: string | null;
    }>(`${baseUrl}&view=events&aggregation=cli_aggregate&limit=25`),
    [extra, setExtra] = useState<UsageEvent[]>([]),
    [cursor, setCursor] = useState<string | null | undefined>(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null);
  const next = cursor === undefined ? initial.data?.nextCursor : cursor;
  async function more() {
    if (!next || busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await fetch(
        `${baseUrl}&view=events&aggregation=cli_aggregate&limit=25&cursor=${encodeURIComponent(next)}`,
        { cache: "no-store" },
      );
      if (!r.ok) throw Error();
      const d = (await r.json()) as {
        events: UsageEvent[];
        nextCursor: string | null;
      };
      setExtra([...extra, ...d.events]);
      setCursor(d.nextCursor);
    } catch {
      setError("More CLI executions could not be loaded. Try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="j5-panel">
      <h2>CLI executions</h2>
      <p className="j1-note">
        Execution summaries can overlap with API calls. Reported usage remains
        separate; absent tokens or cost are unknown.
      </p>
      {initial.loading && <p role="status">Loading CLI executions…</p>}
      {(initial.error || error) && (
        <p role="alert">
          {initial.error ?? error}{" "}
          {initial.error && (
            <button onClick={initial.retry} className="j1-btn">
              Retry
            </button>
          )}
        </p>
      )}
      {[...(initial.data?.events ?? []), ...extra].map((e) => (
        <details className="j5-connection" key={e.id}>
          <summary>
            {e.provider} · {e.model} · {e.status}
          </summary>
          <p>
            {new Date(e.started_at).toLocaleString("en-IN", {
              timeZone: "UTC",
            })}{" "}
            · UTC · {e.channel} · {e.purpose}
          </p>
          <p>
            Input {count(e.usage?.input)} · output {count(e.usage?.output)} ·
            provider-reported cost {cost(e.provider_cost_usd)}
          </p>
          <p className="j1-note">
            Usage source: {e.usage?.source ?? "Not reported"}
          </p>
        </details>
      ))}
      {!initial.loading && !initial.error && !initial.data?.events.length && (
        <p>No CLI execution summaries recorded in this scope.</p>
      )}
      {next && (
        <button className="j1-btn" disabled={busy} onClick={() => void more()}>
          {busy ? "Loading…" : "Show more CLI executions"}
        </button>
      )}
    </section>
  );
}
