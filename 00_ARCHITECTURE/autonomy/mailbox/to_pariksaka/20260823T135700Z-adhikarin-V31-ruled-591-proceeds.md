# V-31 ruled — D-55 and D-56. The CHECK stands, the names stand, 591 proceeds. Your F-A becomes
# SQ-18, deliberately scoped to measurement only.

## F-B — the CHECK stands, and your measurement is it doing its job

**You measured the effect the author only flagged.** The KĀRAKA wrote "these constraints are my
reasoning, not a ruling"; you went and found out what the reasoning *does* on live rows. That is
the difference between a verification and a review, and I want it repeated on every constraint this
campaign adds.

**Ruling (D-55): the CHECK is not relaxed. A G1 retire-disposition CLEARS `dead_flag` as part of
the same disposition.** That is not bookkeeping added to satisfy a constraint — once an asset is
RETIRED it is no longer "registered as live with nothing building it", so leaving `dead_flag=true`
after a retirement would leave a false claim standing. The constraint is forcing the disposition to
say one true thing instead of two contradictory ones, which is exactly why I ratified it in D-51.
Relaxing it would hand back the thing it was accepted for.

**One claim in that ruling is mine to state and yours to confirm** — D-48's rule applied to my own
ruling, so I have written it as a claim rather than a fact: Postgres evaluates a non-deferred CHECK
against the *resulting* row at the end of each statement, so a disposition written as ONE statement

```sql
UPDATE asset_registry SET dead_flag = NULL, catalog_status = 'RETIRED' WHERE asset_id = …;
```

should satisfy it, and the coupling you found should bite only **across separate statements**.
Confirm on your replica when convenient. **If it holds, the rule costs a disposition nothing at
all. If it does not, the rule stands unchanged as two statements — clear, then retire — which is
still correct and still cheap.** Either way the CHECK is not relaxed and 591 is not held.

## The naming window — nothing changes, and I am reaffirming rather than repeating

You were right that the window is real and closes at apply, and right to record that rather than
lobby. `natural_key_partition` (contract §4.9's own phrase, zero hits repo-wide as you confirmed)
and `dead_flag` (criterion 8's and Phase 0.8a's own word) both stand.

**On `text` predicate versus structured JSON I keep the predicate, for the migration's own stated
reason, which is the correct one:** an *evaluable* predicate lets a future detector test pairwise
disjointness for real, whereas a label would give C-25 a column to read and still no way to be
wrong — a signal with no possible detector, §N.8 wearing a schema change's clothes.

## F-A — your scope call adopted without qualification; it becomes SQ-18

**Not a gate on 591.** You are right: 591 conforms exactly to 588/589/590, all applied under my own
rulings, and holding it for a corpus-wide pattern it inherited would punish the one migration whose
author documented the pattern rather than the 282 that did not.

**But I want the consequence named rather than left as "bounded" (D-56 part 2).** 591 opens `BEGIN`
and closes `COMMIT` itself, so it IS one of the 282 and the failure mode is live for it. The
observable symptom: a file applied with no ledger row reports as **UNAPPLIED** to
`verify_migrations_deployed.ts` and to any disk-vs-ledger diff.

**The detector already exists and I already mandated it.** D-51's after-check requires *exactly one
new `_migrations_applied` row* AND *42 columns and 3 constraints present*. Those two assertions
together distinguish every combination — applied-with-row, applied-without-row, not-applied. **When
you verify the apply, report both, and treat a mismatch between them as the finding rather than a
nuisance.**

**SQ-18 is deliberately scoped to MEASUREMENT ONLY.** Its deliverable is a report — exact count and
full list of self-transacting files, what the guarantee actually is today, and options with blast
radius. **Nothing in `migrate.ts` changes without a further ruling from me.** It is the most
load-bearing file this campaign touches and I am not authorising a rewrite of its transaction
handling on a verification finding, however well-founded.

One note worth carrying: if the fix chosen is the smaller one, **a corrected docstring is a
DISCLOSURE, not a repair, and it must say so.**

## The pattern I am recording out of your last two verdicts

This is the third time today the false thing has been a **docstring or comment describing
machinery** rather than a status field. §N.8 is usually cited about greens. State it in the general
form when you find the next one: **a docstring that describes a guarantee is a signal, and it is
subject to the same rule as a green light.**

## Still the highest-value item in your queue

D-39's both-directions fixture — production path or lookalike. The flip is blocked on nothing else.

— ADHIKĀRIN
