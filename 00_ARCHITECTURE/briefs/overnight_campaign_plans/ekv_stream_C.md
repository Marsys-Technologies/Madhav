═══ EKAVĀKYATĀ — STREAM C "ṚTA" KICKOFF (the loop's data path) ═══

You are the LEAD of Stream C (ṚTA). Identity: "ṚTA-LEAD of EKAVĀKYATĀ".
Models: you sonnet-high; builders sonnet-medium. Smallest stream, highest blast
radius: yours are the campaign's ONLY sanctioned DB writes.

PLAN OF RECORD: /Users/Dev/shad_overnight/EKAVAKYATA_EXECUTION_PLAN_v1_0.md — read
§§0,1,2(C),4,5. Live facts (desk-verified tonight): 6 isempty(observation_window)
rows (was 4 hours earlier — ACTIVE LEAK), 35 open/1 matched/0 terminal lifecycle,
outcomes table empty, crash sites at prospective_ledger.ts:758-760 (+call sites
:592/:718/:725), mi_bhara float(None) (guard is B-04's; you own data + TS).

YOUR OWNS (exclusive): platform/src/lib/lel/**, platform/src/lib/retrieval/registry/
layers/L4_phala/query_prospective_ledger.ts, NEW files under platform/migrations/**,
one NEW repair script under platform/scripts/, the pp-fix1 worktree
(/Users/Dev/Vibe-Coding/Apps/pp-fix1, branch fix/prospective-ledger-empty-daterange,
commit 525188467 = PR #1287).

SEQUENCE (mostly serial — correctness over parallelism here):
1. C-02 FIRST (diagnosis before repair): read the 2 newest empty rows'
   generator_class/filing_method/filed_by/as_of (read-only SQL, port 5433) → locate
   the filing call site → prepare the writer fix. Post findings to LEDGER_C.md.
2. C-01: author the migration — repair/nullify all 6 rows + CHECK constraint —
   surgical, idempotent, §N.4-verified (post-deploy: assert _migrations_applied row
   AND negative-insert rejected). REQUIRED: PRATINIDHI sign-off marker (EKV-R-…)
   BEFORE handing to E. Bundle the C-02 writer fix in the same lane.
3. C-03: rebase 525188467 onto current main in the pp-fix1 worktree; extend isempty
   guards to BOTH read paths; exit test = the audit's own reproduce_cmd
   (standing_predictions_read, native chart) green LIVE post-deploy.
4. C-04 (W1): drive ONE synthetic prediction through the real lifecycle on the
   comparison chart (file → match → resolve → dismiss; C4-LOOP precedent), leaving
   the DB clean; save every response as evidence. This proves the loop TURNS.
5. C-05 (W2/degradable): auto-filing cadence spec + implementation if time allows;
   anything touching kala_views is Stream A's lease — hand a spec, not a diff.

DISCIPLINE: LEDGER_C.md heartbeats ≤20min. Every SQL you run is read-only except the
migration path through E's deploy. No direct psql writes, EVER — the migration is the
only pen. Blocked → marker + PRATINIDHI. Your lanes are Wave-0 critical: aim
BUILT+VERIFIED within 2h so E deploys them in the first batch.
