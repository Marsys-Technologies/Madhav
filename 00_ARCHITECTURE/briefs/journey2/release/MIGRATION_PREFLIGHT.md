---
artifact: JOURNEY2_PRODUCTION_MIGRATION_PREFLIGHT
version: 1.0
status: READ_ONLY_PREFLIGHT_COMPLETE_APPLICATION_OPEN
---

# Migration 1312 production preflight

Read-only production connector identified database `amjis`, role `amjis_app`. At 2026-10-07 approximately 11:52 IST: conversations 2,409 rows, conversation_messages 3,400 rows, conversation_shares 0 rows. Both consultation_tagged prerequisite columns exist. Applied tracker records `1307_consultation_tags.sql` with SHA256 `fe9f8c56493a60eb6800fb79875944ee2c26192ed0e356acd8eca7da5259e95f`. Migration1312 and share.message_id are absent. No lock was visible on these three relations at inspection; that snapshot cannot guarantee future lock acquisition.

Compared the complete filenames from BOTH local migration directories against the production tracker with a read-only VALUES join. The sole pending file is `1312_journey2_exchange_shares.sql`; no unrelated pending SQL is authorized by this release. Existing predecessor deployment's routine migration job succeeded; its web/sidecar builds were still running.

Migration1312 uses runner-owned transaction, 5s lock timeout, 30s statement timeout, nullable answer FK with ON DELETE CASCADE and non-null partial index. The empty live share relation supports bounded ordinary index creation. Dedicated disposable PostgreSQL applied exact file twice and asserted one FK/index; static migration guard previously judged it safe. Production migration must use existing tracked routine deployment runner, and applied tracker hash/schema must be verified afterward. No direct production SQL write occurred during preflight.
