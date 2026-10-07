import { Pool } from 'pg'
const pool=new Pool({connectionString:'postgresql://postgres:journey2-test-only@127.0.0.1:60260/journey2_test'})
const conversation='11111111-1111-4111-8111-111111111111', answer='44444444-4444-4444-8444-444444444444'
try {
  // Fixture identity only; never attach this script to an application database.
  await pool.query("INSERT INTO conversation_shares(conversation_id,message_id,created_by,slug,hide_reasoning,hide_methodology,expires_at) VALUES($1,$2,'journey2-owner','journey2-browser-ready',true,true,NULL),($1,$2,'journey2-owner','journey2-browser-expired',true,true,now()-interval '1 day') ON CONFLICT(slug) DO UPDATE SET revoked_at=NULL,expires_at=EXCLUDED.expires_at",[conversation,answer])
} finally { await pool.end() }
