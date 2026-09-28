-- Migration 1121: Jātaka correction-archive write guard (JATAKA-REQ-02).
--
-- Number: reserved on origin/campaign-coordination by JATAKA-REQ-02 (native-
-- authorized Phase-A hardening, 2026-09-27) after a fresh origin/main + complete
-- open-PR sweep; outside the Pūrṇa (1042–1069) and L3 Kāla (1070–1119)
-- partitions. Authored under CCD-014; NOT applied in that phase.
--
-- Purpose: a conversation archived because its chart's birth details were
-- corrected (archive_reason = 'chart_details_changed', migration 1120) is
-- historical, read-only material. The application refuses new turns and
-- branches at every door and re-checks at the persistence boundary, but a
-- reading that started before the correction could still reach its insert in
-- the instant between that re-check and the write. This trigger closes that
-- window inside the database: every insert into conversation_messages or
-- conversation_branches takes a share lock on the parent conversation row and
-- refuses the write if that conversation is correction-archived.
--
-- Concurrency: the correction transaction UPDATEs the conversation rows it
-- archives, so an insert that has not yet taken its share lock waits for the
-- correction to commit and then sees the archive reason; an insert that took
-- the share lock first commits before the correction's UPDATE proceeds, and its
-- row becomes part of the archived history.
--
-- Idempotent: CREATE OR REPLACE FUNCTION, DROP TRIGGER IF EXISTS + CREATE
-- TRIGGER (the repository's trigger idiom). No data is read or changed; manual
-- archives (archive_reason NULL) keep their existing behaviour.
--
-- Security disposition (Jātaka Phase-A2 item 5, determined not assumed): this
-- function runs SECURITY INVOKER (the default — no SECURITY DEFINER clause).
-- Invoker rights CAN safely perform the required check: `role_web_serve` is
-- the only role migration 576 (576_pariprashna_roles_rls_arm3.sql) grants
-- INSERT on `conversation_messages`/`conversation_branches` (§3d, "conversation
-- store R/W"), and that same migration's blanket `GRANT SELECT ON ALL TABLES
-- IN SCHEMA public TO role_web_serve` (§3a) is never revoked for
-- `conversations` — it names `conversations` in neither the C3 FULL WALL list
-- (§3b: the calibration surfaces) nor the C3 WRITE WALL list (§3c: the
-- prediction ledgers) — so the trigger's own `SELECT archive_reason FROM
-- public.conversations` runs under the inserting role's own, already-adequate
-- privilege. No other role writes either guarded table: `role_sidecar` is
-- walled from every conversation-store table entirely (§3h), and `role_jobs`
-- writes only `conversation_summaries` (§3i), never these two. A DEFINER
-- function would therefore add privilege escalation this trigger does not
-- need. If the running database's actual grants ever diverge from migration
-- 576's own text (verified only by re-reading the applied grants, not
-- assumed), this determination must be re-made before this migration is
-- applied — not silently trusted.

CREATE OR REPLACE FUNCTION public.jataka_refuse_write_to_correction_archive()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  current_reason TEXT;
BEGIN
  SELECT archive_reason INTO current_reason
    FROM public.conversations
   WHERE id = NEW.conversation_id
     FOR SHARE;
  IF current_reason = 'chart_details_changed' THEN
    RAISE EXCEPTION 'CONVERSATION_ARCHIVED_READ_ONLY: conversation % is correction-archived history', NEW.conversation_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.jataka_refuse_write_to_correction_archive() IS
  'Refuses inserts into correction-archived (chart_details_changed) conversations; see migration 1121.';

DROP TRIGGER IF EXISTS jataka_correction_archive_guard ON public.conversation_messages;
CREATE TRIGGER jataka_correction_archive_guard
  BEFORE INSERT ON public.conversation_messages
  FOR EACH ROW EXECUTE FUNCTION public.jataka_refuse_write_to_correction_archive();

DROP TRIGGER IF EXISTS jataka_correction_archive_guard ON public.conversation_branches;
CREATE TRIGGER jataka_correction_archive_guard
  BEFORE INSERT ON public.conversation_branches
  FOR EACH ROW EXECUTE FUNCTION public.jataka_refuse_write_to_correction_archive();
