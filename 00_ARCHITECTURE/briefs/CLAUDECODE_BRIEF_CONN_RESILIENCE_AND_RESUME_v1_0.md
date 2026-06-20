# Connection Resilience + Safe Resume (paste into Claude Code / Antigravity)

**Context:** An interrupted ga_sensitive build (pid 799394) left an idle-in-transaction connection holding
RowExclusiveLock on `chart_facts` + all 13 indexes → connection-exhaustion near Cloud SQL `max_connections=50`.
Stuck connection terminated, locks released, 10/50 conns now. TWO problems: the REAL bug = orphaned-txn-on-
interrupt; the AMPLIFIER = tight connection ceiling. Native-ratified plan: cap parallelism now + both durable
guards + verify-before-resume. Standards: surgical only; only `482012f1`; no silent failures; the fix must not
itself touch the FROZEN orchestrator contract (guards are additive robustness, not contract changes — if a guard
seems to need a contract change, HALT and raise).

---

## STEP 0 — VERIFY-BEFORE-RESUME (read-only): did the killed build commit partial rows?

The interrupted ga_sensitive build was INSERTing into `chart_facts` for `482012f1`. L1 idempotency is
delete-then-insert, so a clean rebuild replaces — but confirm no ORPHANED COMMITTED PARTIAL exists. Read-only:
1. `SELECT count(*), count(DISTINCT fact_category) FROM chart_facts WHERE chart_id=:c AND fact_category IN
   (<the ga_sensitive categories incl. the Amendment-3 ones: gulika/mandi, sun-upagrahas, special_lagna,
   beeja/kshetra sphuta, yogi_graha/dagdha_rashi, + the existing sensitive categories>)` — compare against the
   expected complete count. A count BETWEEN zero and complete = a committed partial (the txn committed some
   batches before dying).
2. Check for any half-written ayanamsha: `... GROUP BY ayanamsha_id` — if some ayanamshas have rows and others
   don't for the same category, that's a partial.
3. Confirm NO idle-in-transaction connection remains: `SELECT pid, state, query_start, wait_event_type FROM
   pg_stat_activity WHERE state='idle in transaction' ORDER BY query_start` — expect none.
Report: clean (nothing committed / fully complete) OR partial-found. If partial-found, the ga_sensitive resume
(STEP 3) will delete-then-insert and replace it — that's fine — but note it so the resume is a known clean
rebuild, not an accrete-on-partial.

---

## STEP 1 — Cap orchestrator worker parallelism (the amplifier; no restart)

Bound concurrent DB connections so a parallel build can't approach the 50 ceiling. In the orchestrator's
worker/run config (the build-run dispatcher that opens per-worker connections):
- Set a max-concurrent-workers (or max-concurrent-DB-connections) cap to a SAFE number. Budget: 50 ceiling −
  headroom for the app/portal/other clients (~10–15) − margin → cap orchestrator concurrency so worst-case
  orchestrator connections stay ≲ 25–30. Pick the exact number from the actual per-worker connection count
  (inspect: how many connections does ONE asset build open? multiply by the intended parallelism).
- This is a config/dispatch change, NOT a contract change. Verify a multi-asset build now stays well under 50
  via `SELECT count(*) FROM pg_stat_activity` sampled during a build.
Do NOT raise max_connections (raises the ceiling, needs a restart, doesn't fix the leak). PgBouncer is the
correct long-term pooler — LOG it as a dedicated post-closure brahma-pipeline task, do NOT build it here.

---

## STEP 2 — Both durable guards against orphaned transactions

**Guard A — DB-level backstop (idle_in_transaction_session_timeout).** So any FUTURE stranded txn self-
terminates and releases its locks instead of holding them indefinitely. Set it at the role/database level for
the build/writer role (e.g. `ALTER ROLE <build_role> SET idle_in_transaction_session_timeout = '<N>s'` — choose
N longer than the longest legitimate single-statement gap in a build but short enough to auto-release, e.g.
60–120s; verify against the orchestrator's real substep timing so it doesn't kill healthy long substeps). This
is a setting, not a restart-requiring instance param.

**Guard B — finally/rollback in the build path (the ROOT-CAUSE fix).** So a killed/crashed/interrupted build
cannot leave a txn open. In the writer/orchestrator DB-execution path that owns the transaction (NOT the writer
internals — the orchestrator's per-substep txn manager, respecting `owns_conn`): wrap the substep execution so
that on ANY exception OR interrupt (KeyboardInterrupt/SIGTERM), the open transaction is rolled back and the
connection released in a `finally`. Confirm the savepoint/txn-per-substep manager already does this on normal
exceptions; ADD interrupt/signal handling if the gap is that SIGTERM/kill bypasses the rollback. The
orchestrator remains the sole transaction owner (frozen contract) — this hardens its existing txn management,
it does not change the WriterBase contract. If it can't be done without a contract change → HALT and raise.

---

## STEP 3 — Resume the L1 closure / ga_sensitive build

With parallelism capped (STEP 1) and STEP 0 verified, resume the interrupted work: re-run the ga_sensitive build
(and continue the L1 closure pass per `KICKOFF_L1_CLOSURE_AUTONOMOUS.md`) for `482012f1`. Because L1 is
delete-then-insert, the resume cleanly replaces any partial. Sample `pg_stat_activity` during the run to confirm
connections stay under the cap and no idle-in-transaction appears.

---

## STEP 4 — Record + log

- Apply Guard-A/B via surgical migration (number above main's current max) + ledger entry; PR.
- Update the L1 closure Smṛti / a robustness note: incident root cause (orphaned txn), the parallelism cap value
  chosen, the idle-timeout value chosen, and the finally/rollback hardening.
- LOG the PgBouncer pooler as a tracked post-closure brahma-pipeline task (the real long-term connection fix).
- Report back: STEP-0 clean/partial result, the cap value, the two guards applied, and confirmation the resumed
  build runs under the cap with no idle-in-transaction.
