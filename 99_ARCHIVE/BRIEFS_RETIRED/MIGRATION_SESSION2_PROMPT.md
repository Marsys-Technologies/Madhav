SUPABASE FULL MIGRATION — SESSION 2: CODE + DEPLOY
===================================================

PRE-FLIGHT (run in terminal before starting this session):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md CLAUDECODE_BRIEF.md.hold

  Verify Session 1 is complete:
  grep -q "GCS_BUCKET_CHAT" .env.rag && echo "Session 1 COMPLETE" || echo "ERROR: run Session 1 first"

POST-SESSION (run in terminal after Claude Code confirms complete):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md.hold CLAUDECODE_BRIEF.md

---

OBJECTIVE
---------
Replace @supabase/supabase-js with native pg + @google-cloud/cloud-sql-connector
for database access. Replace Supabase Storage with @google-cloud/storage.
Rewrite all 20 affected source files. Update Cloud Run configuration. Deploy.
After this session, Supabase is fully decommissioned from the app.

---

ENVIRONMENT
-----------
.env.rag at project root has: DATABASE_URL (proxy), INSTANCE_CONNECTION_NAME,
GCP_PROJECT, DB_USER, DB_NAME, DB_PASSWORD, GCS_BUCKET_CHAT_ATTACHMENTS,
GCS_BUCKET_CHART_DOCUMENTS.

Cloud Run service: amjis-web in project madhav-astrology, region asia-south1.

---

PHASE 1: INSTALL NEW PACKAGES, REMOVE OLD ONES
------------------------------------------------
In platform/:
  npm install pg @google-cloud/cloud-sql-connector @google-cloud/storage
  npm install --save-dev @types/pg
  npm uninstall @supabase/supabase-js @supabase/ssr

---

PHASE 2: CREATE lib/db/client.ts
---------------------------------
Create platform/src/lib/db/client.ts with this exact implementation:

  import 'server-only'
  import { Pool, QueryResult, QueryResultRow } from 'pg'

  let _pool: Pool | null = null

  async function initPool(): Promise<Pool> {
    if (process.env.DATABASE_URL) {
      // Local dev: Auth Proxy connection via .env.rag / .env.local
      return new Pool({ connectionString: process.env.DATABASE_URL })
    }
    // Production (Cloud Run): cloud-sql-connector uses ADC automatically
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

---

PHASE 3: CREATE lib/storage/client.ts
---------------------------------------
Create platform/src/lib/storage/client.ts:

  import 'server-only'
  import { Storage } from '@google-cloud/storage'

  let _storage: Storage | null = null
  function gcs() {
    if (!_storage) _storage = new Storage({ projectId: process.env.GCP_PROJECT })
    return _storage
  }

  export function chatBucket() {
    return gcs().bucket(process.env.GCS_BUCKET_CHAT_ATTACHMENTS!)
  }

  export function chartDocsBucket() {
    return gcs().bucket(process.env.GCS_BUCKET_CHART_DOCUMENTS!)
  }

  export async function uploadBuffer(
    bucket: ReturnType<typeof chatBucket>,
    destPath: string,
    data: Buffer,
    contentType: string
  ): Promise<void> {
    await bucket.file(destPath).save(data, { contentType })
  }

  export async function signedDownloadUrl(
    bucket: ReturnType<typeof chatBucket>,
    filePath: string,
    ttlMs = 60 * 60 * 1000
  ): Promise<string> {
    const [url] = await bucket.file(filePath).getSignedUrl({
      action: 'read',
      expires: Date.now() + ttlMs,
    })
    return url
  }

  export async function signedUploadUrl(
    bucket: ReturnType<typeof chatBucket>,
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

---

PHASE 4: MIGRATE lib/db/types.ts (rename from supabase/types.ts)
------------------------------------------------------------------
Copy platform/src/lib/supabase/types.ts to platform/src/lib/db/types.ts.
The type definitions are reusable as-is — no content changes needed.

---

PHASE 5: REWRITE ALL SOURCE FILES
-----------------------------------
For every file listed below, replace createServiceClient() with query() from
'@/lib/db/client'. Import { query } from '@/lib/db/client'.
Replace all .from('table').select/insert/update/delete/upsert chains with
parameterized SQL via query(). Use $1, $2, etc. for parameters.
Update any import of '@/lib/supabase/types' to '@/lib/db/types'.

The existing Supabase query patterns map to SQL as follows:
  .from('t').select('c1,c2').eq('id', v).single()
    → query('SELECT c1,c2 FROM t WHERE id=$1',[v]) then rows[0] ?? null

  .from('t').select('*')
    → query('SELECT * FROM t') then rows

  .from('t').select('*').eq('col',v).order('created_at',{ascending:false})
    → query('SELECT * FROM t WHERE col=$1 ORDER BY created_at DESC',[v]) then rows

  .from('t').insert({...}).select().single()
    → query('INSERT INTO t (c1,c2) VALUES ($1,$2) RETURNING *',[v1,v2]) then rows[0]

  .from('t').update({...}).eq('id',v).select().single()
    → query('UPDATE t SET c1=$1,c2=$2 WHERE id=$3 RETURNING *',[v1,v2,v]) then rows[0]

  .from('t').delete().eq('id',v)
    → query('DELETE FROM t WHERE id=$1',[v])

  .from('t').upsert({...},{onConflict:'col'})
    → query('INSERT INTO t (...) VALUES (...) ON CONFLICT (col) DO UPDATE SET ...',[...])

Supabase PostgREST join syntax like profiles!client_id(name) maps to a JOIN:
  SELECT charts.*, profiles.name AS client_name
  FROM charts LEFT JOIN profiles ON charts.client_id = profiles.id

FILE-BY-FILE INSTRUCTIONS:

FILE: platform/src/lib/auth/access-control.ts
  Replace createServiceClient() with query().
  The profile lookup is: SELECT id, role, status FROM profiles WHERE id=$1

FILE: platform/src/lib/conversations.ts
  Replace all createServiceClient() calls with query().
  Convert each .from() chain to parameterized SQL.

FILE: platform/src/app/api/auth/session/route.ts
  Replace createServiceClient() with query().
  Profile SELECT: SELECT id, role, status FROM profiles WHERE id=$1
  Profile INSERT: INSERT INTO profiles (id,role,status,name,email)
                  VALUES ($1,$2,$3,$4,$5) ON CONFLICT (id) DO NOTHING

FILE: platform/src/app/api/auth/resolve-username/route.ts
  Replace createServiceClient() with query().
  Query: SELECT email, status FROM profiles
         WHERE lower(username) = lower($1) AND status='active'

FILE: platform/src/app/api/chat/build/route.ts
  Replace createServiceClient() with query().
  Profile role: SELECT role FROM profiles WHERE id=$1
  Chart: SELECT id,name,birth_date,birth_time,birth_place FROM charts WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/api/chat/consume/route.ts
  Replace createServiceClient() with query().
  Charts with client check: SELECT id,name,birth_date,birth_time,birth_place,client_id
                             FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Reports: SELECT domain,title,version FROM reports WHERE chart_id=$1

FILE: platform/src/app/api/chat/upload/route.ts
  Replace Supabase storage with @google-cloud/storage.
  Import { chatBucket, signedUploadUrl } from '@/lib/storage/client'.
  The bucket name for the upload: use chatBucket().name.
  Replace supabase.storage.from('chat-attachments').createSignedUploadUrl(path)
  with signedUploadUrl(chatBucket(), path, mimeType).
  Replace the DB INSERT with query().
  Keep: INSERT INTO chat_attachments (user_id,storage_path,mime,size_bytes)
        VALUES ($1,$2,$3,$4) RETURNING id

FILE: platform/src/app/api/conversations/route.ts
  Replace createServiceClient() or the listConversations helper call with query().
  The conversations query is in lib/conversations.ts — that file will be updated
  in the lib phase above, so this route may only need the import update.

FILE: platform/src/app/api/conversations/[id]/route.ts
  Replace createServiceClient() with query().
  Profile role: SELECT role FROM profiles WHERE id=$1
  Conversation: SELECT * FROM conversations WHERE id=$1
  Messages: SELECT id,role,content,tool_calls,created_at FROM messages
            WHERE conversation_id=$1 ORDER BY created_at ASC

FILE: platform/src/app/api/conversations/[id]/feedback/route.ts
  Replace createServiceClient() with query().
  Feedback SELECT: SELECT message_id,rating,comment FROM message_feedback
                   WHERE conversation_id=$1 AND user_id=$2
  Feedback UPSERT: INSERT INTO message_feedback
                   (conversation_id,message_id,user_id,rating,comment)
                   VALUES ($1,$2,$3,$4,$5)
                   ON CONFLICT (message_id,user_id) DO UPDATE
                   SET rating=$4, comment=$5

FILE: platform/src/app/api/conversations/[id]/share/route.ts
  Replace createServiceClient() with query().
  Shares SELECT: SELECT slug,created_at,expires_at,revoked_at
                 FROM conversation_shares WHERE conversation_id=$1
  Share INSERT: INSERT INTO conversation_shares
                (conversation_id,slug,created_by) VALUES ($1,$2,$3)
  Revoke UPDATE: UPDATE conversation_shares SET revoked_at=now() WHERE slug=$1

FILE: platform/src/app/api/clients/route.ts
  Replace createServiceClient() with query().
  GET: SELECT charts.*, profiles.name AS client_name
       FROM charts LEFT JOIN profiles ON charts.client_id=profiles.id
       ORDER BY charts.created_at DESC
  POST chart INSERT: INSERT INTO charts (client_id,name,birth_date,birth_time,
                     birth_place,birth_lat,birth_lng) VALUES (...) RETURNING *
  POST pyramid INSERT: bulk INSERT INTO pyramid_layers (chart_id,layer,sublayer,status)
                       VALUES ... — use a single multi-row INSERT or loop

FILE: platform/src/app/api/pyramid/route.ts
  Replace createServiceClient() with query().
  Chart client check: SELECT client_id FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/api/reports/[chartId]/[domain]/route.ts
  Replace createServiceClient() with query() and replace Supabase storage
  with @google-cloud/storage.
  Import { chartDocsBucket, signedDownloadUrl } from '@/lib/storage/client'.
  Chart client check: SELECT client_id FROM charts WHERE id=$1
  Profile role: SELECT role FROM profiles WHERE id=$1
  Report: SELECT title,domain,version,storage_path FROM reports
          WHERE chart_id=$1 AND domain=$2 ORDER BY version DESC LIMIT 1
  Replace supabase.storage.from('chart-documents').createSignedUrl(path,3600)
  with signedDownloadUrl(chartDocsBucket(), storagePath)

FILE: platform/src/app/api/access-requests/route.ts
  Replace createServiceClient() with query().
  Check existing: SELECT id FROM access_requests WHERE lower(email)=lower($1)
                  AND status='pending'
  INSERT: INSERT INTO access_requests (full_name,email,reason,status)
          VALUES ($1,$2,$3,'pending') RETURNING id

FILE: platform/src/app/api/admin/access-requests/route.ts
  Replace createServiceClient() with query().
  SELECT id,full_name,email,reason,status,requested_at,reviewed_at
  FROM access_requests ORDER BY requested_at DESC

FILE: platform/src/app/api/admin/access-requests/[id]/approve/route.ts
  Replace createServiceClient() with query().
  Fetch request: SELECT id,full_name,email,status FROM access_requests WHERE id=$1
  Profile INSERT: INSERT INTO profiles (id,role,status,name,username,email,
                  approved_at,approved_by) VALUES (...) ON CONFLICT (id) DO NOTHING
  Request UPDATE: UPDATE access_requests SET status='approved',reviewed_at=now(),
                  reviewed_by=$1,approved_user_id=$2 WHERE id=$3

FILE: platform/src/app/api/admin/access-requests/[id]/reject/route.ts
  Replace createServiceClient() with query().
  Fetch: SELECT status FROM access_requests WHERE id=$1
  UPDATE: UPDATE access_requests SET status='rejected',reviewed_at=now(),
          reviewed_by=$1 WHERE id=$2

FILE: platform/src/app/api/admin/users/route.ts
  Replace createServiceClient() with query().
  GET: SELECT id,role,status,name,username,email,created_at,approved_at
       FROM profiles ORDER BY created_at DESC
  POST INSERT: INSERT INTO profiles (id,role,status,name,username,email,
               approved_at,approved_by) VALUES (...) RETURNING *

FILE: platform/src/app/api/admin/users/[id]/route.ts
  Replace createServiceClient() with query().
  PATCH: UPDATE profiles SET username=$1,status=$2 WHERE id=$3 RETURNING *
         (only update fields that are actually in the request body)
  DELETE: DELETE FROM profiles WHERE id=$1

FILE: platform/src/app/api/admin/users/[id]/send-reset/route.ts
  Replace createServiceClient() with query().
  SELECT email FROM profiles WHERE id=$1

PAGE FILES (server components — also use createServiceClient directly):

FILE: platform/src/app/clients/[id]/layout.tsx
  Replace createServiceClient() with query().
  Role check: SELECT role FROM profiles WHERE id=$1
  Chart auth: SELECT client_id FROM charts WHERE id=$1
  Redirect to /dashboard if role != 'super_admin' AND chart.client_id != user.uid

FILE: platform/src/app/clients/[id]/build/page.tsx
  Replace createServiceClient() with query().
  Profile: SELECT role FROM profiles WHERE id=$1
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=$1

FILE: platform/src/app/clients/[id]/consume/page.tsx
  Replace createServiceClient() with query().
  Profile: SELECT role FROM profiles WHERE id=$1
  Chart: SELECT name,birth_date,birth_place,client_id FROM charts WHERE id=$1
  Reports: SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain

FILE: platform/src/app/clients/[id]/consume/[conversationId]/page.tsx
  Replace createServiceClient() with query().
  Same as consume/page.tsx plus:
  Conversation: SELECT * FROM conversations WHERE id=$1

FILE: platform/src/app/dashboard/page.tsx
  Replace createServiceClient() with query().
  Profile: SELECT id,role,name,username,email,status FROM profiles WHERE id=$1
  Charts (super_admin): SELECT * FROM charts ORDER BY created_at DESC
  Charts (client): SELECT * FROM charts WHERE client_id=$1 ORDER BY created_at DESC
  Pyramid: SELECT layer,sublayer,status FROM pyramid_layers WHERE chart_id=ANY($1)
           (bulk fetch for all chart IDs returned above)

FILE: platform/src/app/share/[slug]/page.tsx
  Replace createServiceClient() with query().
  Share: SELECT * FROM conversation_shares WHERE slug=$1
         AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())
  Conversation: SELECT * FROM conversations WHERE id=$1
  Chart: SELECT name,birth_date,birth_place FROM charts WHERE id=$1

LIB/CLAUDE FILES (complex — both DB and GCS storage):

FILE: platform/src/lib/claude/build-tools.ts
  This file uses BOTH the documents table (DB) and the chart-documents
  storage bucket. Replace all createServiceClient() calls.

  Import { query } from '@/lib/db/client'
  Import { chartDocsBucket, uploadBuffer, signedDownloadUrl } from '@/lib/storage/client'
  Import { Storage } from '@google-cloud/storage'

  DB operations on documents table:
    List:   SELECT id,title,storage_path,created_at FROM documents WHERE chart_id=$1
    Fetch:  SELECT id,title,storage_path FROM documents WHERE id=$1
    Insert: INSERT INTO documents (chart_id,title,storage_path,created_at)
            VALUES ($1,$2,$3,now()) RETURNING *
    Delete: DELETE FROM documents WHERE id=$1

  Storage operations (replace supabase.storage.from('chart-documents')):
    .download(path)      → chartDocsBucket().file(path).download() → returns [Buffer]
    .upload(path, data)  → chartDocsBucket().file(path).save(data, {contentType:'text/markdown'})
    .remove([path])      → chartDocsBucket().file(path).delete()

  The file content downloaded from GCS is a Buffer; convert to string with
  buffer.toString('utf-8') where text content is expected.

FILE: platform/src/lib/claude/consume-tools.ts
  This file also uses both documents/reports tables and chart-documents bucket.

  Import { query } from '@/lib/db/client'
  Import { chartDocsBucket } from '@/lib/storage/client'

  DB operations:
    Charts:    SELECT * FROM charts WHERE id=$1
    Documents: SELECT id,title,storage_path FROM documents WHERE id=$1
               SELECT id,title,storage_path FROM documents WHERE chart_id=$1
               INSERT INTO documents (chart_id,title,storage_path) VALUES ($1,$2,$3) RETURNING *
    Reports:   SELECT title,domain,version,storage_path FROM reports
               WHERE chart_id=$1 AND domain=$2 ORDER BY version DESC LIMIT 1

  Storage operations (replace supabase.storage.from('chart-documents')):
    .download(storage_path) → chartDocsBucket().file(storage_path).download()
                              returns [Buffer] — convert with buf.toString('utf-8')

---

PHASE 6: CLEAN UP REMOVED FILES
---------------------------------
After all rewrites are complete and TypeScript compiles cleanly:
  Delete: platform/src/lib/supabase/server.ts
  Delete: platform/src/lib/supabase/types.ts
  Delete the platform/src/lib/supabase/ directory if now empty

---

PHASE 7: LOCAL BUILD CHECK
----------------------------
In platform/:
  npm run build 2>&1 | tail -30

Fix any TypeScript or build errors before proceeding to Cloud Run deployment.
Do not proceed to Phase 8 if the build fails.

---

PHASE 8: CONFIGURE CLOUD RUN ENVIRONMENT
------------------------------------------
Source .env.rag to get the GCP variables.

Get the Cloud Run service account email:
  SA_EMAIL=$(gcloud run services describe amjis-web \
    --region=asia-south1 --project=madhav-astrology \
    --format='value(spec.template.spec.serviceAccountName)')

Grant Cloud SQL Client role to the Cloud Run service account (needed for
the cloud-sql-connector to authenticate via ADC):
  gcloud projects add-iam-policy-binding madhav-astrology \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudsql.client"

  gcloud projects add-iam-policy-binding madhav-astrology \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"

Add new env vars + secrets to Cloud Run:
  gcloud run services update amjis-web \
    --region=asia-south1 \
    --project=madhav-astrology \
    --set-env-vars="INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,\
DB_USER=$DB_USER,DB_NAME=$DB_NAME,\
GCP_PROJECT=madhav-astrology,\
GCS_BUCKET_CHAT_ATTACHMENTS=${GCP_PROJECT}-chat-attachments,\
GCS_BUCKET_CHART_DOCUMENTS=${GCP_PROJECT}-chart-documents" \
    --set-secrets="DB_PASSWORD=amjis-db-password:latest"

Remove the now-unused Supabase env vars from Cloud Run:
  gcloud run services update amjis-web \
    --region=asia-south1 \
    --project=madhav-astrology \
    --remove-env-vars="NEXT_PUBLIC_SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY"

---

PHASE 9: BUILD AND DEPLOY
--------------------------
  git add -A
  git commit -m "feat: replace Supabase with Cloud SQL + GCS

  DB: @supabase/supabase-js removed; pg + @google-cloud/cloud-sql-connector
  Storage: @supabase/ssr removed; @google-cloud/storage
  - lib/db/client.ts: Pool singleton (Auth Proxy local / connector prod)
  - lib/storage/client.ts: GCS upload, download, signed URL helpers
  - lib/db/types.ts: moved from lib/supabase/types.ts
  - 20 source files rewritten: all createServiceClient() replaced with query()
  - Storage routes: Supabase Storage replaced with GCS signed URLs
  - Cloud Run: INSTANCE_CONNECTION_NAME, DB_USER, DB_NAME, DB_PASSWORD,
    GCS_BUCKET_* added; SUPABASE_* vars removed"

  cd platform && gcloud builds submit \
    --config=cloudbuild.yaml \
    --project=madhav-astrology \
    .

Wait for the build to complete. Stream the logs:
  gcloud builds log $(gcloud builds list --limit=1 --project=madhav-astrology \
    --format='value(id)') --project=madhav-astrology

---

PHASE 10: SMOKE TESTS
----------------------
After the build completes:

  BASE=https://madhav.marsys.in

  echo "--- Health ---"
  curl -s -o /dev/null -w "%{http_code}" $BASE/login
  # Expected: 200

  echo "--- Auth redirect ---"
  curl -s -o /dev/null -w "%{http_code}" $BASE/dashboard
  # Expected: 307 (redirect to /login)

  echo "--- API auth guard ---"
  curl -s -o /dev/null -w "%{http_code}" $BASE/api/conversations
  # Expected: 401

  echo "--- Static check ---"
  curl -s -o /dev/null -w "%{http_code}" https://madhav.marsys.in
  # Expected: 200

All four must pass. If any fail, read Cloud Run logs:
  gcloud run services logs read amjis-web \
    --region=asia-south1 --project=madhav-astrology --limit=50

Fix errors and redeploy before declaring complete.

---

PHASE 11: COMPLETION SUMMARY
------------------------------
Print a summary confirming:
  - Packages removed: @supabase/supabase-js, @supabase/ssr
  - Packages added: pg, @google-cloud/cloud-sql-connector, @google-cloud/storage
  - Files rewritten: list all 20+
  - Cloud Run env vars: new ones added, Supabase ones removed
  - Build: SUCCEEDED
  - Smoke tests: all 4 passed
  - Status: SUPABASE FULLY DECOMMISSIONED
