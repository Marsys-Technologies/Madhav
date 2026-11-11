-- Migration 1415: Bind temporary chat uploads to issued owner receipts
-- Created: 2026-11-11

BEGIN;

-- The protected migrator owns this relation through the trusted application
-- role. Verified request identity and active-profile checks live in the owned
-- application interface. The relation ACL restricts access to other roles.
CREATE TABLE public.chat_upload_receipts (
  token uuid PRIMARY KEY,
  owner_uid text NOT NULL CHECK (owner_uid <> ''),
  bucket_name text NOT NULL CHECK (bucket_name <> ''),
  object_key text NOT NULL CHECK (object_key = 'chat-uploads/v1/' || token::text),
  filename text NOT NULL CHECK (char_length(filename) BETWEEN 1 AND 200),
  content_type text NOT NULL CHECK (content_type IN (
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'
  )),
  expected_size integer NOT NULL CHECK (expected_size BETWEEN 1 AND 52428800),
  issued_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  upload_until timestamptz NOT NULL CHECK (upload_until = issued_at + interval '15 minutes'),
  bytes_sha256 bytea CHECK (octet_length(bytes_sha256) = 32),
  object_generation text CHECK (object_generation ~ '^[1-9][0-9]*$'),
  completed_at timestamptz,
  read_until timestamptz,
  UNIQUE (bucket_name, object_key),
  CONSTRAINT chat_upload_receipts_completion_shape CHECK (
    (completed_at IS NULL AND object_generation IS NULL AND read_until IS NULL)
    OR (completed_at IS NOT NULL AND object_generation IS NOT NULL AND read_until IS NOT NULL
      AND bytes_sha256 IS NOT NULL
      AND completed_at >= issued_at AND completed_at < upload_until
      AND read_until = completed_at + interval '1 hour')
  )
);

REVOKE ALL PRIVILEGES ON TABLE public.chat_upload_receipts FROM PUBLIC;

-- Creator default privileges can grant named roles access at CREATE time.
-- Remove those grants only from the new relation, keeping shared defaults intact.
DO $acl$
DECLARE
  granted_role name;
BEGIN
  FOR granted_role IN
    SELECT DISTINCT role.rolname
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN LATERAL pg_catalog.aclexplode(relation.relacl) AS privilege
    JOIN pg_catalog.pg_roles AS role ON role.oid = privilege.grantee
    WHERE relation.oid = 'public.chat_upload_receipts'::regclass
      AND privilege.grantee <> relation.relowner
  LOOP
    EXECUTE pg_catalog.format(
      'REVOKE ALL PRIVILEGES ON TABLE public.chat_upload_receipts FROM %I', granted_role
    );
  END LOOP;

  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN LATERAL pg_catalog.aclexplode(relation.relacl) AS privilege
    WHERE relation.oid = 'public.chat_upload_receipts'::regclass
      AND privilege.grantee <> relation.relowner
  ) THEN
    RAISE EXCEPTION 'chat_upload_receipts ACL must be limited to its owner';
  END IF;
END;
$acl$;

COMMIT;
