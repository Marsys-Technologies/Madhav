/** Run only against the task's disposable PostgreSQL instance, never an application database. */
import { Pool } from "pg";
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
const connection = "postgresql://consultation_test@127.0.0.1:55439/postgres";
if (process.env.CONSULTATION_TEST_DATABASE !== connection)
  throw new Error("Disposable database guard failed");
process.env.DATABASE_URL = connection;
const pool = new Pool({ connectionString: connection, max: 5 });
const correction = await pool.connect();
try {
  await pool.query(`CREATE TABLE conversations(id uuid PRIMARY KEY,chart_id uuid,user_id text,module text,title text,created_at timestamptz DEFAULT now(),updated_at timestamptz,archived_at timestamptz,archive_reason text);
    CREATE TABLE conversation_messages(id uuid PRIMARY KEY,conversation_id uuid,role text,created_at timestamptz DEFAULT now(),parts_json jsonb DEFAULT '[]',metadata_json jsonb DEFAULT '{}',schema_version int);
    CREATE TABLE message_parts(id uuid, message_id uuid,seq int,kind text,body jsonb);`);
  const migration = await readFile(
    new URL(
      "../../supabase/migrations/1307_consultation_tags.sql",
      import.meta.url,
    ),
    "utf8",
  );
  await pool.query(migration);
  await pool.query(migration);
  const { setConsultationTag, consultationHistory, consultationMessages } =
    await import("../../src/lib/conversations/consultation");
  const { getPool } = await import("../../src/lib/db/client");
  const id = "11111111-1111-4111-8111-111111111111",
    chart = "22222222-2222-4222-8222-222222222222",
    message = "33333333-3333-4333-8333-333333333333",
    question = "44444444-4444-4444-8444-444444444444";
  await pool.query(
    "INSERT INTO conversations(id,chart_id,user_id,module,title) VALUES($1,$2,'owner','consume','Fictional test')",
    [id, chart],
  );
  await pool.query(
    'INSERT INTO conversation_messages(id,conversation_id,role,metadata_json,parts_json,schema_version) VALUES($1,$2,\'assistant\',\'{"acharya_reading_receipt":{}}\',\'[{"type":"text","text":"Saved answer"}]\',1),($3,$2,\'user\',\'{}\',\'[{"type":"text","text":"Saved question"}]\',1)',
    [message, id, question],
  );
  assert.equal(
    await setConsultationTag(id, "someone-else", true, message),
    false,
  );
  assert.equal(await setConsultationTag(id, "owner", true, message), true);
  assert.equal(await setConsultationTag(id, "owner", true), true);
  assert.equal((await consultationHistory(chart, "owner"))[0].tagged, true);
  assert.equal(
    (await consultationHistory(chart, "owner"))[0].tagged_answers[0].text,
    "Saved answer",
  );
  assert.equal(
    (await consultationMessages(id))[0].metadata_json?.acharya_reading_receipt,
    undefined,
    "invalid stored receipt is not presented as verified",
  );
  await pool.query("UPDATE conversation_messages SET parts_json='[]'");
  await pool.query(
    "INSERT INTO message_parts(message_id,seq,kind,body) VALUES($1,0,'text','{\"text\":\"Canonical answer\"}'),($2,0,'text','{\"text\":\"Canonical question\"}')",
    [message, question],
  );
  const canonicalHistory = (await consultationHistory(chart, "owner"))[0];
  assert.equal(canonicalHistory.first_message_snippet, "Canonical question");
  assert.equal(canonicalHistory.tagged_answers[0].text, "Canonical answer");
  await setConsultationTag(id, "owner", false, message);
  await correction.query("BEGIN");
  await correction.query(
    "UPDATE conversations SET archived_at=now(),archive_reason='chart_details_changed' WHERE id=$1",
    [id],
  );
  let finished = false;
  const pending = setConsultationTag(id, "owner", true, message).then(
    (result) => {
      finished = true;
      return result;
    },
  );
  let waiting = false;
  for (let i = 0; i < 40; i++) {
    const { rows } = await pool.query(
      "SELECT count(*)::int AS n FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT id FROM conversations%'",
    );
    if (rows[0].n > 0) {
      waiting = true;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  assert.equal(
    waiting,
    true,
    "real tag writer waits for parent correction lock",
  );
  assert.equal(finished, false);
  await correction.query("COMMIT");
  assert.equal(
    await pending,
    false,
    "correction wins: tagging is refused after lock recheck",
  );
  const tagged = await pool.query(
    "SELECT consultation_tagged FROM conversation_messages WHERE id=$1",
    [message],
  );
  assert.equal(tagged.rows[0].consultation_tagged, false);
  assert.equal(await setConsultationTag(id, "owner", true), false);
  await (await getPool()).end();
  console.log(
    JSON.stringify({
      postgres: "17",
      migrationAppliedTwice: true,
      ownership: true,
      historySql: true,
      canonicalHistory: true,
      invalidReceiptRejected: true,
      realCorrectionRace: "PASS",
      productionAccess: false,
    }),
  );
} finally {
  try {
    await correction.query("ROLLBACK");
  } catch {}
  correction.release();
  await pool.end();
}
