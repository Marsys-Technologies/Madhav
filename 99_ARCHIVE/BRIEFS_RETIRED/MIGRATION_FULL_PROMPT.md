SUPABASE → GOOGLE CLOUD — COMPLETE MIGRATION
=============================================
MARSYS-JIS Platform · App DB + Storage · Single-session execution

PRE-FLIGHT (run in terminal BEFORE opening this session):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md CLAUDECODE_BRIEF.md.hold

POST-SESSION (run in terminal AFTER Claude Code confirms MIGRATION COMPLETE):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md.hold CLAUDECODE_BRIEF.md

==========================================================================
CONTEXT
==========================================================================
The MARSYS-JIS platform currently stores all application data in Supabase
(database + file storage). This migration replaces Supabase with Google
Cloud (Cloud SQL for the database, GCS for storage).

WHAT IS ALREADY DONE — do not redo:
  - RAG database (rag_chunks, pgvector) — already on Cloud SQL
  - App hosting — Cloud Run + Load Balancer + madhav.marsys.in
  - Firebase Auth — already migrated, working
  - Migration 006 + 007 — applied to Supabase only, NOT yet to Cloud SQL
  - Cloud Build pipeline — working (platform/cloudbuild.yaml)

WHAT THIS SESSION DOES:
  Part A (Infrastructure): Apply schema to Cloud SQL, migrate data,
                           create GCS buckets, migrate storage files
  Part B (Code):           Replace @supabase/supabase-js with pg +
                           @google-cloud/cloud-sql-connector +
                           @google-cloud/storage across 29 source files
  Part C (Deploy):         Update Cloud Run config, build, deploy,
                           smoke test

KEY FILES:
  .env.rag          — GCP credentials (DATABASE_URL, INSTANCE_CONNECTION_NAME,
                      GCP_PROJECT, GCP_REGION, DB_USER, DB_NAME)
  platform/.env.local — Supabase URL + service role key for data export
  platform/cloudbuild.yaml — Cloud Build config

==========================================================================
PART A — INFRASTRUCTURE
==========================================================================

──────────────────────────────────────────────────────────────────────────
A.1  START CLOUD SQL AUTH PROXY
──────────────────────────────────────────────────────────────────────────
Source .env.rag and start the proxy:

  set -o allexport && source .env.rag && set +o allexport
  cloud-sql-proxy "$INSTANCE_CONNECTION_NAME" --port=5433 &
  PROXY_PID=$!
  sleep 6

Extract the database password from DATABASE_URL and set a local URL:

  DB_PASSWORD=$(grep "^DATABASE_URL=" .env.rag | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|')
  LOCAL_DB_URL="postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME"

Verify the proxy is working:
  psql "$LOCAL_DB_URL" -c "SELECT version();" | grep PostgreSQL

──────────────────────────────────────────────────────────────────────────
A.2  APPLY MIGRATIONS 006 AND 007 TO CLOUD SQL
──────────────────────────────────────────────────────────────────────────
Cloud SQL does not have Supabase's auth schema or storage schema.
Strip the three incompatible lines from migration 006 before applying.

  sed \
    '/on_auth_user_created ON auth\.users/d;
     /DROP POLICY.*storage\.objects/d' \
    platform/supabase/migrations/006_firebase_uid_schema.sql \
    > /tmp/006_cloud_sql.sql

  psql "$LOCAL_DB_URL" -f /tmp/006_cloud_sql.sql
  psql "$LOCAL_DB_URL" -f platform/supabase/migrations/007_user_management.sql

Verify: profiles.id should now be text type with username/email/status cols.
  psql "$LOCAL_DB_URL" -c "\d profiles"

──────────────────────────────────────────────────────────────────────────
A.3  MIGRATE APP TABLE DATA FROM SUPABASE TO CLOUD SQL
──────────────────────────────────────────────────────────────────────────
Write a Python script /tmp/migrate_app_data.py.

The script must:
1. Read NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from
   platform/.env.local (fall back to platform/.env.production).
2. Read DATABASE_URL from .env.rag for Cloud SQL.
3. pip install psycopg2-binary requests --break-system-packages -q
4. For each table, GET all rows from Supabase PostgREST API:
     {SUPABASE_URL}/rest/v1/{table}?select=*
     Headers: apikey: {KEY}, Authorization: Bearer {KEY}, Range: 0-9999
5. INSERT each row into Cloud SQL using psycopg2.
   Use ON CONFLICT DO NOTHING for all tables.
   Parameterize all values — do NOT use string interpolation for values.
6. Print: table name | rows from Supabase | rows inserted into Cloud SQL.

Migrate in this exact FK-safe order (parent before child):
  profiles → charts → conversations → messages → pyramid_layers →
  documents → reports → message_feedback → chat_attachments →
  conversation_shares → access_requests

Run:
  pip install psycopg2-binary requests --break-system-packages -q
  python /tmp/migrate_app_data.py

Verify row counts in Cloud SQL:
  psql "$LOCAL_DB_URL" -c "
    SELECT 'profiles'           AS tbl, COUNT(*) FROM profiles
    UNION ALL SELECT 'charts',           COUNT(*) FROM charts
    UNION ALL SELECT 'conversations',    COUNT(*) FROM conversations
    UNION ALL SELECT 'messages',         COUNT(*) FROM messages
    UNION ALL SELECT 'pyramid_layers',   COUNT(*) FROM pyramid_layers
    UNION ALL SELECT 'documents',        COUNT(*) FROM documents
    UNION ALL SELECT 'reports',          COUNT(*) FROM reports
    UNION ALL SELECT 'message_feedback', COUNT(*) FROM message_feedback
    UNION ALL SELECT 'chat_attachments', COUNT(*) FROM chat_attachments
    UNION ALL SELECT 'conversation_shares', COUNT(*) FROM conversation_shares
    UNION ALL SELECT 'access_requests',  COUNT(*) FROM access_requests
    ORDER BY tbl;"

──────────────────────────────────────────────────────────────────────────
A.4  CREATE GCS BUCKETS
──────────────────────────────────────────────────────────────────────────
  gcloud storage buckets create "gs://${GCP_PROJECT}-chat-attachments" \
    --location="$GCP_REGION" --uniform-bucket-level-access --project="$GCP_PROJECT"

  gcloud storage buckets create "gs://${GCP_PROJECT}-chart-documents" \
    --location="$GCP_REGION" --uniform-bucket-level-access --project="$GCP_PROJECT"

Set CORS on chat-attachments (for signed-URL browser uploads):
  cat > /tmp/cors.json << 'EOF'
  [{"origin":["https://madhav.marsys.in","http://localhost:3000"],
    "method":["GET","PUT","POST","HEAD"],
    "responseHeader":["Content-Type","Content-Length","Authorization"],
    "maxAgeSeconds":3600}]
  EOF
  gcloud storage buckets update "gs://${GCP_PROJECT}-chat-attachments" \
    --cors-file=/tmp/cors.json

Verify both buckets exist:
  gcloud storage buckets list --project="$GCP_PROJECT" | grep "${GCP_PROJECT}-"

──────────────────────────────────────────────────────────────────────────
A.5  MIGRATE SUPABASE STORAGE FILES TO GCS
──────────────────────────────────────────────────────────────────────────
Write /tmp/migrate_storage.py. The script must:
1. Load NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from
   platform/.env.local or platform/.env.production.
2. Load GCP_PROJECT from .env.rag.
3. List all Supabase storage buckets:
     GET {SUPABASE_URL}/storage/v1/bucket
4. For each bucket, list objects:
     POST {SUPABASE_URL}/storage/v1/object/list/{bucket}
     Body: {"prefix":"","limit":1000,"offset":0}
5. For each object, download from Supabase and upload to GCS:
     Download: GET {SUPABASE_URL}/storage/v1/object/{bucket}/{path}
     Upload: use subprocess to run:
       gcloud storage cp - "gs://{GCP_PROJECT}-{bucket}/{path}"
6. If a bucket is empty, print "{bucket}: 0 files, skipped".

Run:
  python /tmp/migrate_storage.py

──────────────────────────────────────────────────────────────────────────
A.6  STOP PROXY AND COMMIT INFRASTRUCTURE
──────────────────────────────────────────────────────────────────────────
Kill the proxy:
  kill $PROXY_PID 2>/dev/null || pkill -f "cloud-sql-proxy" || true

Append bucket names to .env.rag if not already present:
  grep -q "GCS_BUCKET_CHAT" .env.rag || cat >> .env.rag << ENVEOF

# GCS Storage Buckets (added by migration)
GCS_BUCKET_CHAT_ATTACHMENTS=${GCP_PROJECT}-chat-attachments
GCS_BUCKET_CHART_DOCUMENTS=${GCP_PROJECT}-chart-documents
ENVEOF

  git add .env.rag
  git commit -m "infra: app DB + storage migrated to Cloud SQL + GCS

  - Migrations 006 (uuid→text) + 007 (super_admin, user mgmt) on Cloud SQL
  - App tables migrated from Supabase (row counts verified)
  - GCS buckets: \${GCP_PROJECT}-chat-attachments, \${GCP_PROJECT}-chart-documents
  - Storage files migrated from Supabase
  - .env.rag: GCS_BUCKET_* added"

==========================================================================
PART B — CODE: REPLACE @supabase/supabase-js
==========================================================================

──────────────────────────────────────────────────────────────────────────
B.1  INSTALL / REMOVE PACKAGES
──────────────────────────────────────────────────────────────────────────
In platform/:
  npm install pg @google-cloud/cloud-sql-connector @google-cloud/storage
  npm install --save-dev @types/pg
  npm uninstall @supabase/supabase-js @supabase/ssr

──────────────────────────────────────────────────────────────────────────
B.2  CREATE platform/src/lib/db/client.ts
──────────────────────────────────────────────────────────────────────────
Create this file exactly:

  import 'server-only'
  import { Pool, QueryResult, QueryResultRow } from 'pg'

  let _pool: Pool | null = null

  async function initPool(): Promise<Pool> {
    if (process.env.DATABASE_URL) {
      // Local dev: Cloud SQL Auth Proxy via DATABASE_URL from .env.rag
      return new Pool({ connectionString: process.env.DATABASE_URL })
    }
    // Production (Cloud Run): cloud-sql-connector authenticates via ADC
    const { Connector } = await import('@google-cloud/cloud-sql-connector')
    const connector = new Connector()
    const clientOpts = await connector.getOptions({
      instanceConnectionName: process.env.INSTANCE_CONNECTION_NAME!,
    })
    return new Pool({
      ...clientOpts,
      user: process.env.DB_USER!,
      password: process.env.DB_PASSWORD!,
      database: process.env.DB_NAME!,
    })
  }

  export async function getPool(): Promise<Pool> {
    if (!_pool) _pool = await initPool()
    return _pool
  }

  export async function query<T extends QueryResultRow = QueryResultRow>(
    sql: string,
    params?: unknown[]
  ): Promise<QueryResult<T>> {
    const pool = await getPool()
    return pool.query<T>(sql, params)
  }

──────────────────────────────────────────────────────────────────────────
B.3  CREATE platform/src/lib/storage/client.ts
──────────────────────────────────────────────────────────────────────────
Create this file exactly:

  import 'server-only'
  import { Storage, Bucket } from '@google-cloud/storage'

  let _storage: Storage | null = null
  function gcs() {
    if (!_storage) _storage = new Storage({ projectId: process.env.GCP_PROJECT })
    return _storage
  }

  export function chatBucket(): Bucket {
    return gcs().bucket(process.env.GCS_BUCKET_CHAT_ATTACHMENTS!)
  }

  export function chartDocsBucket(): Bucket {
    return gcs().bucket(process.env.GCS_BUCKET_CHART_DOCUMENTS!)
  }

  /** Upload a Buffer to GCS. Overwrites if the path already exists. */
  export async function gcsUpload(
    bucket: Bucket,
    destPath: string,
    data: Buffer | string,
    contentType: string
  ): Promise<void> {
    const buf = typeof data === 'string' ? Buffer.from(data, 'utf-8') : data
    await bucket.file(destPath).save(buf, { contentType })
  }

  /** Download a file from GCS. Returns text content. */
  export async function gcsDownloadText(
    bucket: Bucket,
    filePath: string
  ): Promise<string | null> {
    try {
      const [buf] = await bucket.file(filePath).download()
      return buf.toString('utf-8')
    } catch {
      return null
    }
  }

  /** Delete a file from GCS. Silently ignores if not found. */
  export async function gcsDelete(bucket: Bucket, filePath: string): Promise<void> {
    try {
      await bucket.file(filePath).delete()
    } catch { /* ignore */ }
  }

  /** Generate a signed download URL (default 1h TTL). */
  export async function gcsSignedDownload(
    bucket: Bucket,
    filePath: string,
    ttlMs = 60 * 60 * 1000
  ): Promise<string> {
    const [url] = await bucket.file(filePath).getSignedUrl({
      action: 'read',
      expires: Date.now() + ttlMs,
    })
    return url
  }

  /** Generate a signed upload URL (default 10min TTL). */
  export async function gcsSignedUpload(
    bucket: Bucket,
    filePath: string,
    contentType: string,
    ttlMs = 10 * 60 * 1000
  ): Promise<string> {
    const [url] = await bucket.file(filePath).getSignedUrl({
      action: 'write',
      expires: Date.now() + ttlMs,
      contentType,
    })
    return url
  }

──────────────────────────────────────────────────────────────────────────
B.4  RENAME TYPES FILE
──────────────────────────────────────────────────────────────────────────
  cp platform/src/lib/supabase/types.ts platform/src/lib/db/types.ts

Do NOT edit the content — the type definitions are reusable as-is.
Update all imports of '@/lib/supabase/types' to '@/lib/db/types' across
the codebase with:
  grep -r "lib/supabase/types" platform/src --include="*.ts" --include="*.tsx" -l

Then replace in each file found.

──────────────────────────────────────────────────────────────────────────
B.5  REWRITE ALL SOURCE FILES
──────────────────────────────────────────────────────────────────────────
IMPORT RULES for every file:
  Remove:  import { createServiceClient } from '@/lib/supabase/server'
  Add:     import { query } from '@/lib/db/client'
  Add storage imports only where a file uses storage operations:
           import { chatBucket, chartDocsBucket, gcsUpload, gcsDownloadText,
                    gcsDelete, gcsSignedDownload, gcsSignedUpload } from '@/lib/storage/client'

QUERY PATTERN REFERENCE:
  .from('t').select('c1,c2').eq('id',v).single()
    → const { rows } = await query('SELECT c1,c2 FROM t WHERE id=$1',[v])
      const row = rows[0] ?? null

  .from('t').select('*').eq('col',v).order('created_at',{ascending:false})
    → const { rows } = await query('SELECT * FROM t WHERE col=$1 ORDER BY created_at DESC',[v])

  .from('t').insert({c1:v1,c2:v2}).select().single()
    → const { rows } = await query('INSERT INTO t (c1,c2) VALUES ($1,$2) RETURNING *',[v1,v2])
      const row = rows[0]

  .from('t').update({c1:v1}).eq('id',v).select().single()
    → const { rows } = await query('UPDATE t SET c1=$1 WHERE id=$2 RETURNING *',[v1,v])
      const row = rows[0]

  .from('t').delete().eq('id',v)
    → await query('DELETE FROM t WHERE id=$1',[v])

  .upsert({chart_id,layer,sublayer,status,updated_at},{onConflict:'chart_id,layer,sublayer'})
    → await query(
        'INSERT INTO pyramid_layers (chart_id,layer,sublayer,status,updated_at)
         VALUES ($1,$2,$3,$4,$5)
         ON CONFLICT (chart_id,layer,sublayer) DO UPDATE
         SET status=$4, updated_at=$5',
        [chart_id,layer,sublayer,status,updated_at]
      )

  .ilike('col',v) → WHERE lower(col) = lower($1)
  .order('col')   → ORDER BY col ASC
  .limit(1)       → LIMIT 1
  .maybeSingle()  → same as single() but rows[0] ?? null (no error if 0 rows)

──────────────────────────────────────────────────────────────────────────
FILE-BY-FILE REWRITE GUIDE
──────────────────────────────────────────────────────────────────────────

── LIB FILES ─────────────────────────────────────────────────────────────

FILE: platform/src/lib/auth/access-control.ts
  SELECT id, role, status FROM profiles WHERE id = $1

FILE: platform/src/lib/conversations.ts
  Read all .from() chains and convert each to SQL.
  conversations table: SELECT/INSERT/UPDATE/DELETE
  messages table: SELECT/INSERT/DELETE

FILE: platform/src/lib/claude/consume-tools.ts
  This file has a private helper readDocumentContent(storage_path).
  Replace the Supabase storage download in that helper:
    OLD: supabase.storage.from('chart-documents').download(path) → blob.text()
    NEW: gcsDownloadText(chartDocsBucket(), path)  ← returns string|null directly

  Tool by tool:
  get_birth_data:
    SELECT name,birth_date,birth_time,birth_place,birth_lat,birth_lng,
           ayanamsa,house_system FROM charts WHERE id=$1

  get_planetary_positions:
    SELECT birth_date,birth_time,birth_lat,birth_lng FROM charts WHERE id=$1
    (rest is Python sidecar fetch — keep as-is)

  get_dasha_periods:
    SELECT storage_path FROM documents
    WHERE chart_id=$1 AND layer='L1' AND lower(name) LIKE '%forensic%'
    ORDER BY updated_at DESC LIMIT 1
    then call gcsDownloadText(chartDocsBucket(), storage_path)

  get_layer_document:
    SELECT name,layer,version,storage_path FROM documents
    WHERE chart_id=$1 AND layer=$2 AND name=$3
    then call gcsDownloadText(chartDocsBucket(), storage_path)

  search_signals:
    SELECT name,layer,storage_path FROM documents WHERE chart_id=$1
    then for each: gcsDownloadText(chartDocsBucket(), storage_path)

  get_domain_report:
    Main query:
      SELECT title,domain,version,storage_path,updated_at FROM reports
      WHERE chart_id=$1 AND lower(domain)=lower($2)
      ORDER BY updated_at DESC LIMIT 1
    Fallback (no report found):
      SELECT DISTINCT domain FROM reports WHERE chart_id=$1 ORDER BY domain
    Download content: gcsDownloadText(chartDocsBucket(), report.storage_path)

  get_transits:
    SELECT birth_lat,birth_lng FROM charts WHERE id=$1
    (rest is Python sidecar — keep as-is)

  get_pyramid_status:
    SELECT layer,sublayer,status,version,updated_at FROM pyramid_layers
    WHERE chart_id=$1 ORDER BY layer ASC, sublayer ASC

FILE: platform/src/lib/claude/build-tools.ts
  Tool by tool:

  list_documents:
    let sql = 'SELECT id,name,layer,version,updated_at FROM documents WHERE chart_id=$1'
    params = [chart_id]
    if (layer) { sql += ' AND layer=$2'; params.push(layer) }
    sql += ' ORDER BY layer, name'
    return rows

  read_document:
    const { rows } = await query(
      'SELECT id,name,layer,version,storage_path FROM documents WHERE chart_id=$1 AND name=$2',
      [chart_id, name]
    )
    const row = rows[0] ?? null
    if (!row) return { error: 'Document not found' }
    const content = await gcsDownloadText(chartDocsBucket(), row.storage_path)
    if (!content) return { error: 'Download failed' }
    return { name: row.name, layer: row.layer, version: row.version, content }

  create_document:
    const storage_path = `charts/${chart_id}/${layer}/${name}_v1.0.md`
    await gcsUpload(chartDocsBucket(), storage_path, content, 'text/markdown')
    const { rows } = await query(
      'INSERT INTO documents (chart_id,layer,name,storage_path,version) VALUES ($1,$2,$3,$4,$5) RETURNING id,name,storage_path,version',
      [chart_id, layer, name, storage_path, '1.0']
    )
    If insert fails: await gcsDelete(chartDocsBucket(), storage_path) then return error

  update_document:
    const { rows } = await query(
      'SELECT id,storage_path,version FROM documents WHERE chart_id=$1 AND name=$2',
      [chart_id, name]
    )
    const row = rows[0]; if (!row) return { error: 'Document not found' }
    const oldMajor = parseInt(row.version.split('.')[0], 10)
    const newVersion = `${oldMajor + 1}.0`
    const newPath = row.storage_path.replace(`_v${row.version}.md`, `_v${newVersion}.md`)
    await gcsUpload(chartDocsBucket(), newPath, content, 'text/markdown')
    await query(
      'UPDATE documents SET storage_path=$1, version=$2, updated_at=now() WHERE id=$3',
      [newPath, newVersion, row.id]
    )
    return { name, old_version: row.version, new_version: newVersion, changelog }

  append_to_document:
    const { rows } = await query(
      'SELECT storage_path FROM documents WHERE chart_id=$1 AND name=$2',
      [chart_id, name]
    )
    const row = rows[0]; if (!row) return { error: 'Document not found' }
    const existing = await gcsDownloadText(chartDocsBucket(), row.storage_path)
    if (existing === null) return { error: 'Download failed' }
    const combined = existing + '\n\n---\n\n' + content
    await gcsUpload(chartDocsBucket(), row.storage_path, combined, 'text/markdown')
    await query(
      'UPDATE documents SET updated_at=now() WHERE chart_id=$1 AND name=$2',
      [chart_id, name]
    )
    return { name, bytes_appended: content.length }

  update_layer_status:
    await query(
      `INSERT INTO pyramid_layers (chart_id,layer,sublayer,status,updated_at)
       VALUES ($1,$2,$3,$4,now())
       ON CONFLICT (chart_id,layer,sublayer) DO UPDATE
       SET status=$4, updated_at=now()`,
      [chart_id, layer, sublayer, status]
    )
    return { layer, sublayer, status }

  search_in_document:
    const { rows } = await query(
      'SELECT storage_path FROM documents WHERE chart_id=$1 AND name=$2',
      [chart_id, name]
    )
    const row = rows[0]; if (!row) return { error: 'Document not found' }
    const text = await gcsDownloadText(chartDocsBucket(), row.storage_path)
    if (!text) return { error: 'Download failed' }
    const matches = text.split('\n').filter(l => l.toLowerCase().includes(query.toLowerCase()))
    return { name, matches, total_matches: matches.length }

  get_pyramid_status (in build-tools):
    SELECT layer,sublayer,status,version,updated_at FROM pyramid_layers
    WHERE chart_id=$1 ORDER BY layer ASC, sublayer ASC

  run_ephemeris + run_computation:
    No DB/storage — keep as-is, just remove the createServiceClient import.

── API ROUTE FILES ────────────────────────────────────────────────────────

FILE: platform/src/app/api/auth/session/route.ts
  Profile SELECT: SELECT id,role,status FROM profiles WHERE id=$1
  Profile INSERT:
    INSERT INTO profiles (id,role,status,name,email)
    VALUES ($1,$2,$3,$4,$5)
    ON CONFLICT (id) DO NOTHING
    (role = user email === SUPER_ADMIN_EMAIL ? 'super_admin' : 'client')

FILE: platform/src/app/api/auth/resolve-username/route.ts
  SELECT email,status FROM profiles
  WHERE lower(username)=lower($1) AND status='active'
  LIMIT 1

FILE: platform/src/app/api/access-requests/route.ts
  Check duplicate: SELECT id FROM access_requests
                   WHERE lower(email)=lower($1) AND status='pending'
  Insert: INSERT INTO access_requests (full_name,email,reason,status)
          VALUES ($1,$2,$3,'pending') RETURNING id

FILE: platform/src/app/api/clients/route.ts
  GET: SELECT charts.*, profiles.name AS client_name
       FROM charts LEFT JOIN profiles ON charts.client_id=profiles.id
       ORDER BY charts.created_at DESC
  POST chart: INSERT INTO charts (client_id,name,birth_date,birth_time,birth_place,
              birth_lat,birth_lng) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *
  POST pyramid bulk insert: use a loop over layers to INSERT one row at a time,
    each: INSERT INTO pyramid_layers (chart_id,layer,sublayer,status)
          VALUES ($1,$2,$3,'not_started') ON CONFLICT DO NOTHING

FILE: platform/src/app/api/chat/build/route.ts
  Profile role: SELECT role FROM profiles WHERE id=$1
  Chart: SELECT id,name,birth_date,birth_time,birth_place FROM charts WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/api/chat/consume/route.ts
  Chart: SELECT id,name,birth_date,birth_time,birth_place,client_id FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Reports: SELECT domain,title,version FROM reports WHERE chart_id=$1
  INSERT conversations: INSERT INTO conversations (chart_id,user_id,module,title)
                        VALUES ($1,$2,$3,$4) RETURNING *
  DELETE messages: DELETE FROM messages WHERE conversation_id=$1
  INSERT message: INSERT INTO messages (id,conversation_id,role,content,tool_calls)
                  VALUES ($1,$2,$3,$4,$5)

FILE: platform/src/app/api/chat/upload/route.ts
  Replace Supabase storage with GCS signed upload URL:
    import { chatBucket, gcsSignedUpload } from '@/lib/storage/client'
    const uploadUrl = await gcsSignedUpload(chatBucket(), storagePath, mimeType)
  DB: INSERT INTO chat_attachments (user_id,storage_path,mime,size_bytes)
      VALUES ($1,$2,$3,$4) RETURNING id

FILE: platform/src/app/api/conversations/route.ts
  Uses listConversations from lib/conversations.ts — that file is rewritten
  above so this route may only need its import updated.

FILE: platform/src/app/api/conversations/[id]/route.ts
  Profile role: SELECT role FROM profiles WHERE id=$1
  Conversation: SELECT * FROM conversations WHERE id=$1
  Messages: SELECT id,role,content,tool_calls,created_at FROM messages
            WHERE conversation_id=$1 ORDER BY created_at ASC
  UPDATE title: UPDATE conversations SET title=$1 WHERE id=$2
  DELETE: DELETE FROM conversations WHERE id=$1

FILE: platform/src/app/api/conversations/[id]/feedback/route.ts
  Profile role: SELECT role FROM profiles WHERE id=$1
  Feedback SELECT: SELECT message_id,rating,comment FROM message_feedback
                   WHERE conversation_id=$1 AND user_id=$2
  DELETE feedback: DELETE FROM message_feedback
                   WHERE message_id=$1 AND user_id=$2
  UPSERT feedback:
    INSERT INTO message_feedback (conversation_id,message_id,user_id,rating,comment)
    VALUES ($1,$2,$3,$4,$5)
    ON CONFLICT (message_id,user_id) DO UPDATE SET rating=$4, comment=$5

FILE: platform/src/app/api/conversations/[id]/share/route.ts
  Profile role: SELECT role FROM profiles WHERE id=$1
  Shares: SELECT slug,created_at,expires_at,revoked_at
          FROM conversation_shares WHERE conversation_id=$1
  INSERT share: INSERT INTO conversation_shares (conversation_id,slug,created_by)
                VALUES ($1,$2,$3) RETURNING *
  Revoke: UPDATE conversation_shares SET revoked_at=now() WHERE slug=$1

FILE: platform/src/app/api/pyramid/route.ts
  Chart client: SELECT client_id FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/api/reports/[chartId]/[domain]/route.ts
  Replace Supabase storage with GCS signed download URL:
    import { chartDocsBucket, gcsSignedDownload } from '@/lib/storage/client'
    const url = await gcsSignedDownload(chartDocsBucket(), report.storage_path)
  Chart client: SELECT client_id FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Report: SELECT title,domain,version,storage_path FROM reports
          WHERE chart_id=$1 AND domain=$2 ORDER BY version DESC LIMIT 1

FILE: platform/src/app/api/admin/access-requests/route.ts
  SELECT id,full_name,email,reason,status,requested_at,reviewed_at
  FROM access_requests ORDER BY requested_at DESC

FILE: platform/src/app/api/admin/access-requests/[id]/approve/route.ts
  Fetch: SELECT id,full_name,email,status FROM access_requests WHERE id=$1
  Profile INSERT:
    INSERT INTO profiles (id,role,status,name,username,email,approved_at,approved_by)
    VALUES ($1,'client','active',$2,$3,$4,now(),$5) ON CONFLICT (id) DO NOTHING
  Update request:
    UPDATE access_requests SET status='approved',reviewed_at=now(),
    reviewed_by=$1,approved_user_id=$2 WHERE id=$3

FILE: platform/src/app/api/admin/access-requests/[id]/reject/route.ts
  Fetch: SELECT status FROM access_requests WHERE id=$1
  Update: UPDATE access_requests SET status='rejected',reviewed_at=now(),
          reviewed_by=$1 WHERE id=$2

FILE: platform/src/app/api/admin/users/route.ts
  GET: SELECT id,role,status,name,username,email,created_at,approved_at
       FROM profiles ORDER BY created_at DESC
  POST INSERT: INSERT INTO profiles (id,role,status,name,username,email,
               approved_at,approved_by) VALUES ($1,$2,$3,$4,$5,$6,now(),$7) RETURNING *

FILE: platform/src/app/api/admin/users/[id]/route.ts
  PATCH: build a dynamic UPDATE only for fields present in request body
    e.g.: UPDATE profiles SET username=$1, status=$2, updated_at=now() WHERE id=$3
  DELETE: DELETE FROM profiles WHERE id=$1

FILE: platform/src/app/api/admin/users/[id]/send-reset/route.ts
  SELECT email FROM profiles WHERE id=$1

── PAGE FILES (server components) ────────────────────────────────────────

FILE: platform/src/app/clients/[id]/layout.tsx
  Profile role: SELECT role FROM profiles WHERE id=$1
  Chart owner: SELECT client_id FROM charts WHERE id=$1
  Keep the same redirect logic: non-super_admin + not owner → redirect('/dashboard')

FILE: platform/src/app/clients/[id]/build/page.tsx
  Profile: SELECT role FROM profiles WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/clients/[id]/consume/page.tsx
  Profile: SELECT role FROM profiles WHERE id=$1
  Chart: SELECT name,birth_date,birth_place,client_id FROM charts WHERE id=$1
  Reports: SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain ASC

FILE: platform/src/app/clients/[id]/consume/[conversationId]/page.tsx
  Same as consume/page.tsx plus:
  Conversation: SELECT * FROM conversations WHERE id=$1

FILE: platform/src/app/dashboard/page.tsx
  Profile: SELECT id,role,name,username,email,status FROM profiles WHERE id=$1
  Charts (super_admin): SELECT * FROM charts ORDER BY created_at DESC
  Charts (client): SELECT * FROM charts WHERE client_id=$1 ORDER BY created_at DESC
  Pyramid: SELECT chart_id,layer,sublayer,status FROM pyramid_layers
           WHERE chart_id = ANY($1::text[])
           (pass array of chart IDs from the charts query above)

FILE: platform/src/app/share/[slug]/page.tsx
  Share: SELECT * FROM conversation_shares WHERE slug=$1
         AND revoked_at IS NULL
         AND (expires_at IS NULL OR expires_at > now())
  Conversation: SELECT * FROM conversations WHERE id=$1
  Chart: SELECT name,birth_date,birth_place FROM charts WHERE id=$1

──────────────────────────────────────────────────────────────────────────
B.6  DELETE SUPABASE FILES
──────────────────────────────────────────────────────────────────────────
After all rewrites compile cleanly:
  rm platform/src/lib/supabase/server.ts
  rm platform/src/lib/supabase/types.ts
  rmdir platform/src/lib/supabase/ 2>/dev/null || true

Verify no remaining imports:
  grep -r "lib/supabase" platform/src --include="*.ts" --include="*.tsx"
  grep -r "createServiceClient" platform/src --include="*.ts" --include="*.tsx"
Both commands must return zero lines. Fix any that remain.

──────────────────────────────────────────────────────────────────────────
B.7  LOCAL BUILD CHECK
──────────────────────────────────────────────────────────────────────────
  cd platform && npm run build 2>&1 | tail -40

Fix all TypeScript errors before proceeding. Do NOT continue to Part C
if the build fails — diagnose and fix first.

==========================================================================
PART C — DEPLOY
==========================================================================

──────────────────────────────────────────────────────────────────────────
C.1  GRANT IAM ROLES TO CLOUD RUN SERVICE ACCOUNT
──────────────────────────────────────────────────────────────────────────
  SA_EMAIL=$(gcloud run services describe amjis-web \
    --region=asia-south1 --project=madhav-astrology \
    --format='value(spec.template.spec.serviceAccountName)')

  gcloud projects add-iam-policy-binding madhav-astrology \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudsql.client"

  gcloud projects add-iam-policy-binding madhav-astrology \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"

──────────────────────────────────────────────────────────────────────────
C.2  UPDATE CLOUD RUN ENVIRONMENT
──────────────────────────────────────────────────────────────────────────
  gcloud run services update amjis-web \
    --region=asia-south1 \
    --project=madhav-astrology \
    --set-env-vars="\
INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres,\
DB_USER=amjis_app,\
DB_NAME=amjis,\
GCP_PROJECT=madhav-astrology,\
GCS_BUCKET_CHAT_ATTACHMENTS=madhav-astrology-chat-attachments,\
GCS_BUCKET_CHART_DOCUMENTS=madhav-astrology-chart-documents" \
    --set-secrets="DB_PASSWORD=amjis-db-password:latest" \
    --remove-env-vars="NEXT_PUBLIC_SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY"

──────────────────────────────────────────────────────────────────────────
C.3  COMMIT, BUILD, DEPLOY
──────────────────────────────────────────────────────────────────────────
  git add -A
  git commit -m "feat: replace Supabase with Cloud SQL + GCS

  DB: @supabase/supabase-js removed; replaced with pg +
      @google-cloud/cloud-sql-connector
  Storage: @supabase/ssr removed; replaced with @google-cloud/storage
  - lib/db/client.ts: Pool singleton (Auth Proxy local / connector prod)
  - lib/storage/client.ts: GCS upload/download/delete/signed-URL helpers
  - lib/db/types.ts: migrated from lib/supabase/types.ts
  - 29 source files rewritten (API routes, page files, lib files)
  - lib/claude/build-tools.ts: full GCS + pg rewrite (documents table)
  - lib/claude/consume-tools.ts: full GCS + pg rewrite
  - Cloud Run: DB_PASSWORD secret, INSTANCE_CONNECTION_NAME, GCS_BUCKET_*
    added; SUPABASE_* vars removed"

  cd platform
  gcloud builds submit --config=cloudbuild.yaml --project=madhav-astrology .

Wait for build to complete. If it fails, read logs:
  gcloud builds log $(gcloud builds list --limit=1 --project=madhav-astrology \
    --format='value(id)') --project=madhav-astrology

──────────────────────────────────────────────────────────────────────────
C.4  SMOKE TESTS
──────────────────────────────────────────────────────────────────────────
  BASE=https://madhav.marsys.in

  echo "Login page:"; curl -s -o /dev/null -w "%{http_code}\n" $BASE/login
  echo "Dashboard redirect:"; curl -s -o /dev/null -w "%{http_code}\n" $BASE/dashboard
  echo "API auth guard:"; curl -s -o /dev/null -w "%{http_code}\n" $BASE/api/conversations
  echo "Root:"; curl -s -o /dev/null -w "%{http_code}\n" $BASE

Expected: 200, 307, 401, 200. All four must pass.

If any fail, read Cloud Run logs:
  gcloud run services logs read amjis-web \
    --region=asia-south1 --project=madhav-astrology --limit=50

Fix errors and redeploy before declaring MIGRATION COMPLETE.

──────────────────────────────────────────────────────────────────────────
C.5  FINAL SUMMARY
──────────────────────────────────────────────────────────────────────────
Print a MIGRATION COMPLETE block showing:
  ✓ Cloud SQL: migrations 006+007 applied, row counts per table
  ✓ GCS: bucket names
  ✓ Storage: files migrated (count per bucket)
  ✓ Packages: removed @supabase/supabase-js, added pg + cloud-sql-connector + storage
  ✓ Files rewritten: count (should be 29+)
  ✓ Build: SUCCEEDED
  ✓ Smoke tests: 200 / 307 / 401 / 200
  ✓ Status: SUPABASE FULLY DECOMMISSIONED
