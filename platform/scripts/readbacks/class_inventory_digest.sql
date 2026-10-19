WITH
-- class_inventory_digest.sql — READ-ONLY readback for F-SHARED-GEOMETRY (SR-DG9-DECIDE: one readback_sql file, no new kind).
-- One SELECT/WITH accepted by executor readback_sql (fleet/readback_sql.sh: single statement, no backslash).
--
-- What it gives: for each event class of the LATEST COMPLETED ka_gochara_v5 generation of the canonical chart,
-- an ordered, digested inventory, so classes that share a full record set can be compared by digest alone
-- (the J-3d run found 7 groups of classes sharing full record sets).
--
-- "Latest completed generation" = among this chart's ka_gochara_search_inventory generations, the one whose rows
-- are ALL finalized (count(*) = count(finalized_at); migration 1206, kgsi_final_pair_ck), newest by
-- max(finalized_at), generation DESC as the tie-break. No generation is hard-coded.
--
-- Per class (columns of migrations 1155, 1206):
--   stored_*_digest          the writer's own ka_gochara_search_inventory digests, read, never recomputed here
--   record_set_digest        sha256 over the ordered record_id list of ka_gochara_relationship_record
--   record_content_digest    sha256 over the ordered CLASS-INDEPENDENT record tuples (path_id, rule_version, agent,
--                            relation, object_id, object_role, affected_person, frame_kind, frame_arg, contact_id).
--                            record_id hashes the event_class (1155), so two classes with the same records have
--                            different record_set_digest; THIS column is the one equal for shared record sets.
--   obligation_content_digest  the same for ka_gochara_search_obligation (path_id, rule_version, agent, relation,
--                            object_role, target, frame, person) — ob_id omitted for the same reason
--   pin_content_digest       the same for ka_gochara_search_path_pin (path_id, rule_version, disposition)
--   record_group_size / record_group_first_class   how many classes carry the same record_content_digest, and the
--                            first of them by class name; NULL when the class has no records (an empty set is not a share)
-- Ordering inside digests is COLLATE "C" (collation-independent). Output ORDER BY event_class is total: the
-- inventory primary key is (chart_id, generation, event_class).
-- Chart-scoped to 482012f1-710e-4a25-994a-93821f5871aa. Counts and sha256 digests only; no personal data.
latest AS (
  SELECT generation
    FROM ka_gochara_search_inventory
   WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
   GROUP BY generation
  HAVING count(*) = count(finalized_at)
   ORDER BY max(finalized_at) DESC, generation DESC
   LIMIT 1
),
inv AS (
  SELECT i.generation, i.event_class, i.input_digest, i.inventory_digest, i.ledger_digest
    FROM ka_gochara_search_inventory i
    JOIN latest l ON l.generation = i.generation
   WHERE i.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
),
rec_rows AS (
  SELECT r.event_class, r.record_id,
         concat_ws('|', r.path_id, r.rule_version, r.agent, r.relation, r.object_id::text, r.object_role,
                   r.affected_person, r.frame_kind, coalesce(r.frame_arg, '-'), coalesce(r.contact_id::text, '-')) AS content
    FROM ka_gochara_relationship_record r
    JOIN latest l ON l.generation = r.generation
   WHERE r.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
),
rec AS (
  SELECT event_class, count(*) AS record_count,
         encode(sha256(convert_to(string_agg(record_id::text, chr(10) ORDER BY record_id::text COLLATE "C"), 'UTF8')), 'hex') AS record_set_digest,
         encode(sha256(convert_to(string_agg(content, chr(10) ORDER BY content COLLATE "C"), 'UTF8')), 'hex') AS record_content_digest
    FROM rec_rows
   GROUP BY event_class
),
obl_rows AS (
  SELECT o.event_class,
         concat_ws('|', o.path_id, o.rule_version, o.agent, o.relation, o.object_role, o.target, o.frame, o.person) AS content
    FROM ka_gochara_search_obligation o
    JOIN latest l ON l.generation = o.generation
   WHERE o.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
),
obl AS (
  SELECT event_class, count(*) AS obligation_count,
         encode(sha256(convert_to(string_agg(content, chr(10) ORDER BY content COLLATE "C"), 'UTF8')), 'hex') AS obligation_content_digest
    FROM obl_rows
   GROUP BY event_class
),
pin_rows AS (
  SELECT p.event_class, concat_ws('|', p.path_id, p.rule_version, p.disposition) AS content
    FROM ka_gochara_search_path_pin p
    JOIN latest l ON l.generation = p.generation
   WHERE p.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
),
pin AS (
  SELECT event_class, count(*) AS pin_count,
         encode(sha256(convert_to(string_agg(content, chr(10) ORDER BY content COLLATE "C"), 'UTF8')), 'hex') AS pin_content_digest
    FROM pin_rows
   GROUP BY event_class
)
SELECT inv.generation,
       inv.event_class,
       inv.input_digest        AS stored_input_digest,
       inv.inventory_digest    AS stored_inventory_digest,
       inv.ledger_digest       AS stored_ledger_digest,
       coalesce(rec.record_count, 0)     AS record_count,
       rec.record_set_digest,
       rec.record_content_digest,
       CASE WHEN rec.record_content_digest IS NULL THEN NULL
            ELSE count(*) OVER (PARTITION BY rec.record_content_digest) END AS record_group_size,
       CASE WHEN rec.record_content_digest IS NULL THEN NULL
            ELSE min(inv.event_class COLLATE "C") OVER (PARTITION BY rec.record_content_digest) END AS record_group_first_class,
       coalesce(obl.obligation_count, 0) AS obligation_count,
       obl.obligation_content_digest,
       coalesce(pin.pin_count, 0)        AS pin_count,
       pin.pin_content_digest
  FROM inv
  LEFT JOIN rec USING (event_class)
  LEFT JOIN obl USING (event_class)
  LEFT JOIN pin USING (event_class)
 ORDER BY inv.event_class COLLATE "C"
