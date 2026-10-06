import {
  beforeAll,
  afterAll,
  beforeEach,
  describe,
  it,
  expect,
  vi,
} from "vitest";
import { Pool } from "pg";
import { readFileSync } from "node:fs";
const h = vi.hoisted(() => ({ pool: null as Pool | null }));
vi.mock("@/lib/db/client", () => ({
  query: (sql: string, args: unknown[]) => h.pool!.query(sql, args),
  withTransaction: async (fn: (c: unknown) => Promise<unknown>) => {
    const c = await h.pool!.connect();
    try {
      await c.query("BEGIN");
      const result = await fn(c);
      await c.query("COMMIT");
      return result;
    } catch (e) {
      await c.query("ROLLBACK");
      throw e;
    } finally {
      c.release();
    }
  },
}));
import {
  createPersona,
  updatePersona,
  deletePersona,
  listPersonas,
} from "@/lib/personas";
const url = process.env.JOURNEY5_TEST_DATABASE_URL;
if (url) {
  const u = new URL(url);
  if (
    !["localhost", "127.0.0.1"].includes(u.hostname) ||
    !u.pathname.startsWith("/ai_console_test_")
  )
    throw Error("Requires named disposable localhost database");
}
describe.skipIf(!url).sequential("Journey5 real PostgreSQL contracts", () => {
  beforeAll(async () => {
    h.pool = new Pool({ connectionString: url, max: 4 });
    await h.pool.query(
      `CREATE TABLE IF NOT EXISTS profiles(id text PRIMARY KEY,status text DEFAULT 'active',updated_at timestamptz DEFAULT now());CREATE TABLE IF NOT EXISTS personas(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),user_id text NOT NULL,name text NOT NULL,system_prompt text NOT NULL,default_style text,default_stack text,is_default boolean DEFAULT false,created_at timestamptz DEFAULT now(),updated_at timestamptz DEFAULT now());CREATE UNIQUE INDEX IF NOT EXISTS idx_personas_user_default ON personas(user_id) WHERE is_default=true`,
    );
    const sql = readFileSync(
      "migrations/1310_journey5_account_preferences.sql",
      "utf8",
    );
    await h.pool.query("BEGIN");
    await h.pool.query(sql);
    await h.pool.query("COMMIT");
    await h.pool.query("BEGIN");
    await h.pool.query(sql);
    await h.pool.query("COMMIT");
  });
  afterAll(async () => {
    await h.pool?.end();
  });
  beforeEach(async () => {
    await h.pool!.query("TRUNCATE personas,profiles");
    await h.pool!.query("INSERT INTO profiles(id) VALUES('alice'),('bob')");
  });
  it("additive preferences survives repeated migration and concurrent disjoint edits", async () => {
    await Promise.all([
      h.pool!.query(
        "UPDATE profiles SET account_preferences=account_preferences || '{\"navPinned\":true}'::jsonb WHERE id='alice'",
      ),
      h.pool!.query(
        "UPDATE profiles SET account_preferences=account_preferences || '{\"titles\":\"en\"}'::jsonb WHERE id='alice'",
      ),
    ]);
    expect(
      (
        await h.pool!.query(
          "SELECT account_preferences FROM profiles WHERE id='alice'",
        )
      ).rows[0].account_preferences,
    ).toEqual({ navPinned: true, titles: "en" });
    expect(
      (
        await h.pool!.query(
          "SELECT account_preferences FROM profiles WHERE id='bob'",
        )
      ).rows[0].account_preferences,
    ).toEqual({});
  });
  it("foreign default target cannot clear own existing default", async () => {
    const a = await createPersona({
      userId: "alice",
      name: "A",
      systemPrompt: "A",
      isDefault: true,
    });
    const b = await createPersona({
      userId: "bob",
      name: "B",
      systemPrompt: "B",
    });
    expect(await updatePersona(b.id, "alice", { is_default: true })).toBeNull();
    expect(
      (await listPersonas("alice")).find((p) => p.id === a.id)?.is_default,
    ).toBe(true);
  });
  it("concurrent default swaps complete with exactly one default", async () => {
    const a = await createPersona({
      userId: "alice",
      name: "A",
      systemPrompt: "A",
      isDefault: true,
    });
    const b = await createPersona({
      userId: "alice",
      name: "B",
      systemPrompt: "B",
    });
    const c = await createPersona({
      userId: "alice",
      name: "C",
      systemPrompt: "C",
    });
    const result = await Promise.allSettled([
      updatePersona(b.id, "alice", { is_default: true }),
      updatePersona(c.id, "alice", { is_default: true }),
    ]);
    expect(result.map((r) => r.status)).toEqual(["fulfilled", "fulfilled"]);
    expect(
      (await listPersonas("alice")).filter((p) => p.is_default),
    ).toHaveLength(1);
    expect(
      (await listPersonas("alice")).find((p) => p.id === a.id)?.is_default,
    ).toBe(false);
  });
  it("concurrent deletes preserve the final persona and a default", async () => {
    const a = await createPersona({
      userId: "alice",
      name: "A",
      systemPrompt: "A",
      isDefault: true,
    });
    const b = await createPersona({
      userId: "alice",
      name: "B",
      systemPrompt: "B",
    });
    await Promise.all([
      deletePersona(a.id, "alice"),
      deletePersona(b.id, "alice"),
    ]);
    const rows = await listPersonas("alice");
    expect(rows).toHaveLength(1);
    expect(rows[0].is_default).toBe(true);
  });
});
