import { Pool } from 'pg'
const connectionString=process.env.JOURNEY2_TEST_DATABASE_URL
if (!connectionString) throw new Error('Task-owned fixture database URL required')
const target=new URL(connectionString)
if (target.hostname!=='127.0.0.1' || target.port!=='60260' || target.pathname!=='/journey2_test' || target.username!=='postgres') throw new Error('Refusing non-task-owned fixture database')
const pool=new Pool({connectionString})
const conversation='11111111-1111-4111-8111-111111111111', answer='44444444-4444-4444-8444-444444444444'
try {
  await pool.query("UPDATE conversations SET title='PRIVATE_FIRST_QUESTION_TOPIC' WHERE id=$1",[conversation])
  // Fixture identity only; never attach this script to an application database.
  await pool.query("INSERT INTO conversation_shares(conversation_id,message_id,created_by,slug,hide_reasoning,hide_methodology,expires_at) VALUES($1,$2,'journey2-owner','journey2-browser-ready',true,true,NULL),($1,$2,'journey2-owner','journey2-browser-expired',true,true,now()-interval '1 day') ON CONFLICT(slug) DO UPDATE SET revoked_at=NULL,expires_at=EXCLUDED.expires_at",[conversation,answer])
} finally { await pool.end() }
