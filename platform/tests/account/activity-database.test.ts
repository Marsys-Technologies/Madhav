import { beforeAll, afterAll, describe, it, expect } from "vitest";
import { Pool } from "pg";
import {
  parseUsageFilter,
  usageSummary,
  usageConnections,
  usageEvents,
} from "@/lib/metering/queries";
const url = process.env.JOURNEY5_TEST_DATABASE_URL;
if (url) {
  const u = new URL(url);
  if (
    !["localhost", "127.0.0.1"].includes(u.hostname) ||
    !u.pathname.startsWith("/ai_console_test_")
  )
    throw Error("Requires named disposable localhost database");
}
const pool = new Pool({
  connectionString: url,
  options: "-c search_path=j5_usage",
  max: 1,
});
const db = {
  query: async <T>(sql: string, values?: unknown[]) => {
    const r = await pool.query(sql, values);
    return { rows: r.rows as T[] };
  },
};
const scope = { ownerId: "alice" };
const filter = (extra = "") =>
  parseUsageFilter(
    new URL(
      "http://localhost/api/usage?from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z&" +
        extra,
    ),
    scope,
  );
describe
  .skipIf(!url)
  .sequential("personal activity uses one PostgreSQL population", () => {
    beforeAll(async () => {
      await pool.query(`CREATE SCHEMA IF NOT EXISTS j5_usage;DROP TABLE IF EXISTS ai_metering_receipts,ai_metering_attempts,llm_usage_events;
 CREATE TABLE ai_metering_attempts(attempt_id uuid,user_id text,conversation_id text,turn_id text,operation_id text,parent_operation_id text,channel text,purpose text,payer text,provider text,model text,role text,connection_id uuid,snapshot_id uuid,test_run_id uuid,aggregation text,started_at timestamptz);
 CREATE TABLE ai_metering_receipts(attempt_id uuid,finished_at timestamptz,status text,usage jsonb,provider_request_id text,finish_reason text,first_token_at timestamptz,provider_cost_usd numeric,computed_cost_usd numeric,pricing_status text,pricing_snapshot jsonb);
 CREATE TABLE llm_usage_events(event_id uuid,user_id text,conversation_id text,prompt_id text,parent_prompt_id text,channel text,provider text,model text,pipeline_stage text,started_at timestamptz,finished_at timestamptz,status text,parameters jsonb,input_tokens bigint,output_tokens bigint,cache_read_tokens bigint,cache_write_tokens bigint,reasoning_tokens bigint,provider_request_id text,computed_cost_usd numeric)`);
      for (const [
        owner,
        provider,
        model,
        connection,
        aggregation,
        cost,
        tokens,
      ] of [
        [
          "alice",
          "openrouter",
          "anthropic/claude",
          "11111111-1111-4111-8111-111111111111",
          "transport",
          0.02,
          100,
        ],
        [
          "alice",
          "openrouter",
          "anthropic/claude",
          "22222222-2222-4222-8222-222222222222",
          "transport",
          null,
          null,
        ],
        ["alice", "claude_code", "claude", null, "cli_aggregate", null, 500],
        [
          "bob",
          "openrouter",
          "anthropic/claude",
          "11111111-1111-4111-8111-111111111111",
          "transport",
          100,
          9000,
        ],
      ] as const) {
        const id = crypto.randomUUID();
        await pool.query(
          `INSERT INTO ai_metering_attempts VALUES($1::uuid,$2,'conversation','turn',$1::text,NULL,'web','customer','user',$3,$4,'synthesizer',$5,NULL,NULL,$6,'2026-10-01T12:00:00Z')`,
          [id, owner, provider, model, connection, aggregation],
        );
        await pool.query(
          `INSERT INTO ai_metering_receipts(attempt_id,finished_at,status,usage,computed_cost_usd,provider_cost_usd) VALUES($1,'2026-10-01T12:00:01Z','success',$2,$3,$4)`,
          [
            id,
            JSON.stringify({ input: tokens, output: tokens }),
            cost,
            cost === null ? null : 0.03,
          ],
        );
      }
    });
    afterAll(() => pool.end());
    it("separates API calls from CLI summaries and preserves unknown price", async () => {
      const s = await usageSummary(filter(), scope, db);
      expect(s).toMatchObject({
        transport_attempts: 2,
        cli_executions: 1,
        transport_unpriced: 1,
        input_tokens: "100",
        cli_input_tokens: "500",
        known_transport_cost_usd: "0.02",
      });
      const c = await usageConnections(filter("view=connections"), scope, db);
      expect(c.groups).toHaveLength(3);
      expect(c.groups.reduce((n, g) => n + Number(g.records), 0)).toBe(3);
      expect(
        c.groups.find((g) => g.aggregation === "cli_aggregate")
          ?.known_transport_cost_usd,
      ).toBeNull();
    });
    it("uses the exact same connection filter for totals and the hierarchy", async () => {
      const f = filter("connectionId=22222222-2222-4222-8222-222222222222");
      expect(await usageSummary(f, scope, db)).toMatchObject({
        records: 1,
        transport_attempts: 1,
        cli_executions: 0,
        known_transport_cost_usd: null,
      });
      expect((await usageConnections(f, scope, db)).groups).toHaveLength(1);
    });
    it("filters CLI event pagination before the limit without leaking transport or foreign records", async () => {
      const result = await usageEvents(
        filter("view=events&aggregation=cli_aggregate&limit=1"),
        scope,
        db,
      );
      expect(result.events).toHaveLength(1);
      expect(result.events[0]).toMatchObject({
        user_id: "alice",
        aggregation: "cli_aggregate",
        provider: "claude_code",
        computed_cost_usd: null,
      });
      expect(result.nextCursor).toBeNull();
    });
    it("rejects an owner override even with a valid connection filter", () => {
      expect(() =>
        filter("userId=bob&connectionId=11111111-1111-4111-8111-111111111111"),
      ).toThrow("Owner scope");
    });
  });
