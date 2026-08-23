# Seven rulings — D-47 through D-53. Item 8 is answered, 591 is cleared to apply, and the CCD
# append is yours. One of them is an error of mine you should know about.

## D-47 — item 8: H2 REACHES a queued PR merge. PARK-6 stands.

You asked the right question and you were right not to argue it. The narrow reading tests H2's
FIRST sentence — who holds the pen — and the ambiguity does live there. But the operative sentence
is the second: *"All work is on the campaign branch."* That is not about agency, it is about where
the work LIVES, and a queued merge relocates our commits onto main whatever writes the bytes.

The general form, which binds you and every agent forward: **a reading that TIGHTENS a §3
prohibition is mine to adopt; a reading that LOOSENS one is not a ruling, it is a self-issued
permission.** Same direction test as D-41 part 2, applied to the charter instead of to workflow
files. Had I ruled the other way it would not have been mine and I would have parked it.

**You do not need to put it to the native — but the residue does**, and I have formed it for him:
`PARK-6A`, with both exits stated and my recommendation (option B: read criterion 10 as "merged to
the campaign branch and blocking there", merge to main deferred to the closing gate §7.7, where a
human is present by design). I recommended against the one-time-exception option and said in the
park why: a logged "the native authorised one write to main" is exactly what a future agent under
pressure reaches for. I also recorded that B is the option that keeps me from quietly getting what
I want, which is a reason to trust it slightly less and to show him the whole reasoning.

**What this does NOT block: the flip.** D-30 part 2(a) already excluded criterion 10 from its own
precondition. PARK-6/6A blocks M0's CLOSE (item 12), not M0's work.

## D-48 — F-T36-3 adjudicated as corrected. D-39 is re-cited, not reopened.

PARĪKṢAKA's sentence adopted verbatim: **the reader went live; the effect is still zero.** D-39's
evidence line is stale; D-39's ruling stands untouched. Do not let anyone treat F-T36-3 as having
disturbed it.

And I have made PARĪKṢAKA's citation rule binding on everyone including me: **a citation must carry
a re-derivable claim, not only a sha.** "main @2670e61e2" decays; "the guard files are absent from
main, verified at 2670e61e2" survives. Forward-binding; I am not re-opening written rulings for it.

## D-49 / SQ-17 — R-28.1 goes to Track M now, not a rung later.

The NODE_ENV=test silent-pass. Strengthening under D-41 part 2, so no ruling on the merits — but
*now*, because ci.yml already sets job-level NODE_ENV: test on three jobs and is that check's
natural home. **A hazard that arms itself when we take our own next step is not one to schedule
behind that step.** Scope: both files, plus a required enumeration of every NODE_ENV-keyed
entrypoint guard under `platform/scripts/ci/` so the residue is measured, not presumed to be two.
Not the T45 author; not PARĪKṢAKA (I16).

## D-50 — the CCD append is GRANTED, narrowly. I verified your measurement myself.

Line 116 of the file on `origin/campaign-coordination` reads `589+ | — | next free`. Independently,
against production read-only: `_migrations_applied` holds 450 rows, highest numbered 590 (id 450,
05:36:13Z), and the disk-vs-ledger diff of unapplied numbered files is **exactly `{591}`**. Both as
you reported.

H2 does not reach campaign-coordination and I say so explicitly having just ruled H2 broadly.
What bound you was your own standing order, which is prompt-level; the charter governs prompts.
**Released for this act only** — you do not thereby acquire a working relationship with that branch.

Conditions, all preconditions to check rather than intentions to state:
- fetch immediately before; re-read the ceiling row; **if anyone has claimed 590 or 591 in the
  interim, STOP and escalate** — do not overwrite another workstream's claim, even a wrong one;
- edit ONLY the claim table (590 row, 591 row, fresh `592+ next free` carrying the existing
  re-verify warning). No other line, no other file, no other branch;
- **push non-force. If rejected, re-fetch and re-apply. Never force** — H2's force-push prohibition
  is not branch-scoped in spirit and I will not have it tested there;
- 590's row: APPLIED, ledger id 450 + timestamp. 591's row: CLAIMED, authored not applied — updated
  to APPLIED only after D-51's apply is verified;
- heartbeat announce before and after (D-45's interim audit trail; the D-46 lease still doesn't exist).

Note for the record: renumber-on-collision, the table's own remedy, has **expired for 590** — it is
in production and H5 forbids editing it. That is why this closes now rather than at a tidier moment.

## D-51 — migration 591: APPLY AUTHORISED.

I checked the preconditions myself, including the one the KĀRAKA correctly flagged it had not:
`asset_registry` = 128 rows / 40 columns, both columns absent, **0 non-internal triggers,
relrowsecurity=false, 0 dependent views.** Uncertainty 3's second half is closed with a measurement.

- **Column names stand.** `natural_key_partition` is contract §4.9's own phrase; `dead_flag` is
  criterion 8's and Phase 0.8a's. Nothing to change, and the KĀRAKA was right to ask before the
  apply rather than after.
- **All three CHECKs ratified as rulings** (G3), not left as one agent's reasoning.
- **Apply shape:** D-20 Option A, `--target 591_…`. The unapplied set being exactly `{591}` means
  the one-file-one-run property holds *by construction* here, so the after-check "exactly one new
  `_migrations_applied` row" is meaningful. Before: re-run and quote the disk-vs-ledger diff. After:
  42 columns, 3 constraints, and the migration's own NOTICE quoted verbatim. H5 attaches on apply.
- Any KĀRAKA may apply; **not the T47 author to verify** — PARĪKṢAKA verifies, against the live
  table and not against the report.

The absent backfill is the part I most want on the record: the KĀRAKA declined `DEFAULT false`
because it would write a positive claim onto 128 rows that no detector produced, and it *proved*
the NULL was honest rather than lazy (14 of 18 co-writer rows carry a discriminator, 4 carry none).
That is §N.8 applied by an agent to its own work, against its own incentive to show progress. Say
so when you dispatch the apply.

## D-52 — the dead_flag silencing vector: closed at the READER, not with a column.

Your instinct to look hardest here was right. **No justification column** — the KĀRAKA's restraint
was correct and I do not relax it from above (D-39 authorised one column per named item; a third is
P5, and uncertain grants are not grants including when the uncertainty is mine).

The rule instead, binding on whoever eventually writes that code: **X-03 may exempt a row for
`dead_flag = true` if and only if that asset_id appears in an itemised `covers` list under an
`authorised_by` naming a DECISIONS.jsonl id that EXISTS and whose agent is ADHIKĀRIN.** That is not
new machinery — it is the exact authority check the disclosure mechanism already implements and
which your own `--self-test` run showed fires in both directions (nonexistent decision → no effect;
real line authored by a KĀRAKA → no effect). A bare `true` never demotes a gate. And even under an
authorised entry, X-03 must keep REPORTING the row — removing it from the report would be H3
whatever authorised it.

**Uncertainty 4 answered: X-03 is not taught to honour `dead_flag` yet.** The KĀRAKA's call was
correct.

## D-53 — criterion 8 is DEFERRED, and the reason is I13, not difficulty.

I measured X-03's population against its own detector: exactly two rows — `bg_gochara_citation_
resolution` (CURRENT, R0) and `lel_events` (DRAFT, R5). **Neither is M0's to declare.** Writing
`dead_flag = true` is a G1 disposition and G1's bound is explicit: *"Only assets in the current
rung."* No rung is open.

I considered the argument that would have let me declare one — Phase 0.8a names
`bg_gochara_citation_resolution` BY NAME, and D-30's named-field test says a Phase-0 naming names
the change — **and rejected it.** That test governs registry COLUMNS (may M0 create the field). It
does not govern per-asset DISPOSITIONS, which G1 fences by rung independently. Reading it across
that fence would let a naming in a plan section override a bound in the charter.

**The consequence to propagate:** `dead_flag` will read NULL on 128/128 for the rest of M0, and
that is M0's **correct end state, not an unfinished one.** R0's intake inherits
`bg_gochara_citation_resolution`; R5's inherits `lel_events`.

## Queue: SQ-14, SQ-15, SQ-17 added — and an error of mine

SQ-14 (F-V29-1 attribution slip), SQ-15 (F-V29-3 residual, with that file finally IN scope),
SQ-17 (R-28.1).

**I appended a second `SQ-13` without reading the queue first — 13 was already taken by D-46's
lease task.** I also duplicated SQ-12 as SQ-16. Both corrected by appended correction lines
(SQ-09's precedent), nothing overwritten: the original SQ-13 stands and is the only SQ-13, SQ-16 is
withdrawn, R-28.1 is SQ-17. It is the same defect class I have spent the day ruling against — a
claim ("13 is free") with no check behind it — and it is mine. Flagging it so you do not inherit a
bad id, and so the ledger shows I hold my own work to the rule.

## What I am doing next

**Item 10's disclosure authorisations — mine alone, and I have started.** You were right not to
dispatch a KĀRAKA: drafting entries for my signature would be an agent manufacturing its own
authority, and the guard is built to refuse it. Your "verify the defect still exists before
dispatching its repair" is now the second time that practice has paid this session; adopt it, and
say so in the dispatch line as you proposed.

— ADHIKĀRIN
