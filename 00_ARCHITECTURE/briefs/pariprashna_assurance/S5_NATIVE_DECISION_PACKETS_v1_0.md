---
artifact: S5_NATIVE_DECISION_PACKETS
version: "1.0"
status: AWAITING NATIVE DECISION — prepared, not acted upon. Checked the ledger
  first: zero `decision_recorded`/`native_acceptance` events exist for either
  item (all 26 tracker decisions on S5's lineage are SURROGATE DECISIONs, none
  native). Both items therefore stay PARKED per the convergence-pass
  instruction — this document exists to make the decision fast and informed,
  not to make it.
stream_id: S5
date: 2026-08-29
---

# S5 — Two native-decision packets (E-001, B-002)

Both re-verified LIVE, read-only, against production, 2026-08-29. Neither
acted upon. `S5:remediation` is hard-blocked on E-001 specifically (it is
the one frozen remediation-plan entry — `S5-R-005-e001-audit-log-grant-
narrowing-NATIVE-SIGNOFF-GATED` — that cannot be marked implemented without
this decision).

## Packet 1 — E-001 (PPR-26): `amjis_app` audit-trail over-privilege

**The ask:** merge PR #1615 (migration 634, `REVOKE DELETE, TRUNCATE ON
TABLE public.audit_log FROM amjis_app`) — yes or no. This is the single
unblock for `S5:remediation`.

**Re-verified live today, read-only, via a self-started/self-stopped
cloud-sql-proxy:**

| Fact | Current state |
|---|---|
| `amjis_app` grants on `public.audit_log` | DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE — unchanged since first observed |
| `audit_log` row count | **0** (empty) |
| `audit_log` protective trigger | none |
| PR #1615 merge state | OPEN, never merged, auto-merge never armed |

**The reframing this re-verification surfaces — read before deciding:**
`audit_log` is not the table doing the real work. The actual append-only
audit ledger this app writes to in production is `pariprashna_safety_decisions`
(**319 rows** today, growing — hard-stop/safety decisions, hash-chained via
`prev_hash`/`entry_hash` columns). It has:

- `amjis_app` grants: DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE,
  UPDATE — the SAME over-broad set as `audit_log`.
- A real protective trigger, `trg_pariprashna_safety_decisions_append_only`
  (`pg_trigger.tgtype = 27` = `BEFORE ROW` on `UPDATE` + `DELETE`).
  **This trigger does NOT cover `TRUNCATE`** — Postgres row-level triggers
  never fire on `TRUNCATE`, which requires a separate statement-level
  trigger that does not exist here. So `amjis_app` can still destroy the
  ENTIRE real audit ledger in one `TRUNCATE pariprashna_safety_decisions;`
  statement today, trigger notwithstanding.

Separately, `mimamsa_predictions` (**195 rows**, real prediction records —
directly J8/prediction-lifecycle relevant) has the SAME over-broad
`amjis_app` grant set and **zero protective trigger of any kind** (only a
bare primary-key constraint). No migration anywhere in this campaign
proposes touching it.

**So, stated plainly:** PR #1615 as scoped narrows a grant on a table that
is currently empty and not the table doing the real audit work. It does not
close the TRUNCATE gap on the table that matters (`pariprashna_safety_decisions`),
and it does not touch the table with zero protection at all
(`mimamsa_predictions`). This does not mean PR #1615 is wrong — REVOKing an
unused destructive grant is still a legitimate, zero-risk hardening step,
and closing `audit_log`'s door is worth doing regardless of `audit_log`'s
current emptiness (a future write path may populate it). But merging #1615
alone should not be read as "E-001 is closed" — the load-bearing exposure is
elsewhere.

**Options for the native:**
1. **Merge #1615 as-is** (narrow, zero-risk, real but partial value)
   — unblocks `S5:remediation`'s frozen plan entry, closes the least
   important instance of the pattern.
2. **Merge #1615 AND commission two follow-on migrations** (same
   `REVOKE DELETE, TRUNCATE` pattern, plus for `pariprashna_safety_decisions`
   specifically a statement-level `TRUNCATE` trigger or an equivalent
   REVOKE) targeting `pariprashna_safety_decisions` and `mimamsa_predictions`
   — closes the exposure that actually matters. Larger ask, still additive-
   only and low-risk (same REVOKE pattern, no new infrastructure).
3. **Decline to merge anything this cycle**, record the accepted risk
   explicitly (all three tables), leave `S5:remediation` at 8/9 — this is a
   legitimate choice already exercised for B-002 below; consistent
   governance would extend the same "record, don't force" posture here too.

No option is executed without your explicit instruction — this stream does
not merge production-privilege migrations autonomously.

## Packet 2 — B-002 (E-002/E-015): `chart_facts`/`chart_dashas` RLS gap

**The ask:** commission the 8-step live remediation build (session-context
plumbing, `role_web_serve` cutover, policy spec extension, `FORCE ROW
LEVEL SECURITY`) — or record this as an accepted, standing risk and stop
re-litigating it every session.

**Re-verified live today, read-only:**

| Table | `relrowsecurity` | `relforcerowsecurity` | Policies |
|---|---|---|---|
| `chart_facts` | false | false | 0 |
| `chart_dashas` | false | false | 0 |
| `chart_divisionals` | **true** | false | (has policies, from migration 576) |

**Unchanged from every prior check this campaign.** `chart_facts`/
`chart_dashas` still carry zero RLS objects at all (E-002); `chart_divisionals`
demonstrates the E-015 hazard even where RLS IS nominally on — `amjis_app`
owns every table in `public`, and Postgres exempts a table owner from its
own RLS policies unless `FORCE ROW LEVEL SECURITY` is set, which it is
nowhere. A policy-only fix for `chart_facts`/`chart_dashas` would produce a
green `relrowsecurity=true` / populated `pg_policies` signal that protects
nothing for the app's actual connection — the exact false-positive-signal
CLAUDE.md §N.8 forbids.

**The frame, unchanged:** this is a **commission-the-8-step-build** vs
**record-accepted-risk** decision, not a technical question — the technical
facts have not moved since the narrowed-proof session first surfaced them.
The 8-step build's own blocking fact also has not moved: `setChartContext()`/
`withChartContext` session-context plumbing has **zero production callers**
across 162 files today, so any live RLS arming without first landing that
plumbing (steps 1–4 of 8) either no-ops safely (pre-cutover) or breaks the
L1 build path (post-cutover) — there is no safe partial state to land
autonomously.

**Options for the native:**
1. **Commission the 8-step build** as a dedicated, scoped follow-on session
   (not squeezed into a convergence pass) — real remediation, real risk, real
   session budget required.
2. **Record accepted risk explicitly** — a native `decision_recorded` event
   stating chart_facts/chart_dashas cross-chart read exposure via
   `amjis_app`'s owner-bypass is a known, accepted risk pending future
   capacity — closes the repeated re-litigation, does not close the gap.
3. **Something narrower** — e.g. commission only the scratch-DB detector
   hardening (already exists) plus a monitoring/alerting control on
   `amjis_app`'s query patterns against these two tables, as a stopgap
   between now and a future full build.

No option is executed without your explicit instruction.
