# Domain A — Campaign Evidence Integrity

Audit of `nirmana_evidence.nirmana_elevation_campaign_definitions` /
`nirmana_elevation_campaign_events` and the read-only audit tooling in
`platform/scripts/nirmana/`. Read-only DB access only (`amjis_app` role);
no file was mutated except this report.

## 1. Definition lineage (confirmed)

```
definition_revision            | definition_status | created_at                  | superseded_at
t0-2026-08-25-4a78a5c4          | superseded         | 2026-08-25 06:52:44.130275  | 2026-08-26 07:14:17.036316
t0-2026-08-26-faa4d6b0          | superseded         | 2026-08-26 07:14:14.594565  | 2026-09-01 12:17:42.580073
t0-2026-09-01-0e5b06fb          | superseded         | 2026-09-01 12:17:42.380739  | 2026-09-08 09:34:55.461511
t1-2026-09-08-be255ffe          | superseded         | 2026-09-08 09:34:55.161628  | 2026-09-10 06:17:23.778836
t2-2026-09-10-057e53eb          | superseded         | 2026-09-10 06:17:23.409570  | 2026-09-11 12:02:54.797548
t3-2026-09-11-8b884eac          | frozen             | 2026-09-11 12:02:54.493869  | (null)
```

Six definitions total: five superseded + one frozen, matching the brief's premise. Lineage
itself (created_at/superseded_at chain) is internally consistent — no gaps, no overlaps.

**Gap found:** the two earliest superseded definitions
(`t0-2026-08-25-4a78a5c4`, `t0-2026-08-26-faa4d6b0`) have **zero events** tagged with their
`definition_revision` anywhere in `nirmana_elevation_campaign_events` (confirmed via the
`event_type, definition_revision, count(*)` breakdown — only four revision values appear:
`t0-2026-09-01-0e5b06fb`, `t1-2026-09-08-be255ffe`, `t2-2026-09-10-057e53eb`,
`t3-2026-09-11-8b884eac`). Either those two definitions were pure same-day planning
iterations with no real campaign activity recorded against them, or event-level
`definition_revision` tagging wasn't wired up until the `t0-09-01` revision. Not fatal on
its own, but it means the evidence trail for the campaign's first ~6 days is not
reconstructable from `nirmana_elevation_campaign_events` at all.

## 2. `definition_superseded_mid_campaign` events

Exactly 3 such events exist, tagged to `t1`, `t2`, and `t3` respectively (one per transition
from `t0-09-01→t1`, `t1→t2`, `t2→t3`). None tagged to the `t0-08-25→t0-08-26` or
`t0-08-26→t0-09-01` transitions — consistent with the gap in §1.

## 3. The core finding: the audit instrument shares the F1 defect class

`egate.sql` is documented (per the task brief) as having a critical, separately-tracked bug:
it fails to filter `nirmana_elevation_campaign_events` by `definition_revision`. This audit
did not touch `egate.sql` itself, per instructions. But the broader question — "does
anything else in the evidence-integrity surface have the same hole?" — has a clear answer:
**yes**, and in the one file that is explicitly supposed to be the safety net.

`platform/scripts/nirmana/capsule_audit.sql` is self-described in its own header as:

> "...written early and run continuously so the campaign's terminal claims are checked as
> they are made rather than all at once at the end... §1 and §2 are the load-bearing ones:
> both are written so that a PASS requires a real absence of violations... An audit that
> could only ever print 'clean' would be the §N.8 defect wearing an auditor's coat."

`grep -n "definition_revision"` against `capsule_audit.sql` returns **zero matches**. All
three of its queries (§1 incomplete-evidence-chain check, §2 identity-separation check, §3
per-layer position) `GROUP BY entity_id` / join on `entity_id` with **no WHERE clause
scoping to the current frozen `definition_revision`**. They aggregate
`bool_or(event_type = ...)` across the *entire history* of every superseded definition an
asset has ever passed through, not just the currently-frozen `t3-2026-09-11-8b884eac`
manifest.

This matters concretely, not just in principle. The event-count breakdown shows the same
`entity_id` space being re-processed across revisions:

```
event_type      | t0-09-01 | t1  | t2 | t3
asset_frozen     |    77    | 19  | 7  | 8   → 111 total asset_frozen events
integrity_verified|   77    | 20  | 7  | 8   → 112 total
asset_analysis_accepted | 115 | 37 | 21 | 9
optimization_verdict_accepted | 115 | 37 | 24 | 10
```

§3's own per-layer rollup reports **98 total frozen assets** in the *current* manifest, but
`asset_frozen` fired **111 times** across the table — i.e. at least 13 entities were
"frozen" more than once, under more than one campaign definition. Because §1/§2 never filter
by `definition_revision`, an asset frozen under `t3` today can have its
`w2_analysis` / `w2_verdict` / `integrity_verified` / `terminal_acceptance` booleans
satisfied by events logged against a **superseded** definition (`t0`, `t1`, or `t2`) whose
manifest, scope, or acceptance criteria may differ from the current frozen one. Running the
script live:

- **§1 (incomplete evidence chain): 0 rows** — reads as PASS.
- **§2 (identity separation): 0 crossings** — reads as PASS.
- **§3 (per-layer position):** L3 = 23 assets, 13 frozen, 7 routed-not-frozen, 3 unrouted
  (56.5% frozen). L3's 23-asset count (not 22) is explainable — it includes the retired,
  protected-history `ka_gochara_sweep` alongside the 22 active identities per CLAUDE.md — but
  a reader computing "Accepted N/22" against this table without knowing to exclude that one
  row would get the wrong denominator.

The §1/§2 "0 rows" PASS is genuine evidence that *no violation has ever been logged for any
entity under any definition* — but it is **not** evidence that the *current* frozen
definition's 98 frozen assets each have a complete, `t3`-scoped evidence chain. Given that
asset composition and acceptance criteria changed across five superseded definitions (the
whole reason the campaign iterated at all), and given that entities carry forward the same
`entity_id`/`asset_id` across revisions, it is entirely possible for an asset's
`integrity_verified` or `w2_verdict` to date from a now-superseded manifest generation and
never have been re-checked against `t3-2026-09-11-8b884eac`. The audit tool cannot currently
distinguish "verified under the current definition" from "verified at some point, under some
definition, ever."

This is the exact defect class the task brief names as F1 in `egate.sql` — present a second
time, undocumented, in the tool whose own docstring claims it exists specifically to prevent
this failure mode ("would report a violation if one existed").

## 4. Identity-separation check (§2) — no crossings found

All 20 `(event_type, source_kind, writer_identity)` combinations resolve to `ok`; no
`implementer == certifier` crossing was found anywhere in the table's full history. This
check is less exposed to the revision-scoping gap than §1, since it's a per-event structural
check (source_kind/writer_identity pairing), not a cross-revision aggregation — its PASS is
more trustworthy than §1's.

## 5. Files touching `nirmana_elevation_campaign_events`

Only two files in `platform/scripts/nirmana/` reference the table at all:
`capsule_audit.sql` (this report's subject) and `egate.sql` (the separately-tracked F1 bug,
not touched here). Both lack `definition_revision` filtering. No other script in that
directory queries the events table, so there is no third instance to check and no evidence
of a correctly-scoped reference implementation elsewhere in the repo to compare against.

## Classification: **NOT READY**

**What would need to be true for READY:** `capsule_audit.sql` §1 and §3 (and ideally §2,
for defense in depth) would need to scope their event aggregation to
`WHERE definition_revision = (SELECT definition_revision FROM
nirmana_elevation_campaign_definitions WHERE definition_status = 'frozen')`, and the "0
rows" / "98 frozen, complete" results would need to be re-verified under that scoping before
being relied on as proof the current 22-identity campaign's evidence chain is genuinely
complete. As it stands, the campaign's own audit instrument cannot currently tell the
difference between "this asset's evidence chain is complete under the frozen definition" and
"this asset has, at some point across six campaign definitions since 2026-08-25, accumulated
matching event types" — which is a materially weaker claim, and given the observed
111-events-across-98-frozen-assets overlap, not a hypothetical one.

**Secondary, non-blocking finding:** the two earliest superseded definitions
(`t0-2026-08-25-4a78a5c4`, `t0-2026-08-26-faa4d6b0`) have no events traceable to them by
`definition_revision` at all — an evidence-lineage gap for the campaign's first six days,
worth a footnote in whatever record closes this audit but not itself campaign-blocking.

## ADDENDUM (cycle 8, conductor, not the original authoring subagent)

The F1 sibling-sweep fix (PR #2706, merged into `origin/main` as `9b3c3b219`) applied the scoping
this report's §3 called for: `capsule_audit.sql` now joins all three sections on
`WHERE definition_revision = (SELECT definition_revision FROM frozen_def)`. Re-ran it live,
read-only (`amjis_app`, `default_transaction_read_only=on`):

```
§1 (incomplete evidence chain): 0 rows
§2 (identity separation): 11 rows, all verdict = 'ok'
§3 (per-layer position, t3-scoped):
 layer | assets | frozen | routed_not_frozen | unrouted | pct_frozen
 L0    |     40 |      0 |                 0 |       40 |        0.0
 L1    |     19 |      0 |                 0 |       19 |        0.0
 L2    |     22 |      8 |                 0 |       14 |       36.4
 L3    |     23 |      0 |                 0 |       23 |        0.0
 L4    |      9 |      0 |                 0 |        9 |        0.0
 L5    |     15 |      0 |                 0 |       15 |        0.0
       |    128 |      8 |                 0 |      120 |        6.3
```

**Revised classification: READY (as an instrument).** The tool can now genuinely distinguish
"verified under `t3`" from "verified at some point, under some definition, ever" — the exact gap
this report's original NOT READY verdict identified is closed.

**But the now-trustworthy output itself is a severe finding.** Under the old unscoped aggregation,
§3 read L3 as 13/23 frozen (56.5%) — a picture of real progress. Correctly scoped, **L3 is 0/23
frozen under `t3`**; every prior "13 frozen" reading was contamination from superseded definitions.
This corroborates, via a second independent instrument, F2's and the readiness query's own finding
that 22/23 assets read `NOT_READY-BLOCKED-ANCESTORS` with zero READY-shaped rows. Not a new
campaign-blocking defect beyond what F2 already names — folded into the readiness audit's
decision-list item 1 as corroboration, and item 18 (which called for exactly this re-run) is now
closed.
