---
artifact: SANGAM_INSTRUCTIONS_FROM_GOCHARA_2026_09_24
version: "1.0"
status: ISSUED
date: 2026-09-24
from: "L3 Gochara family (l3/gochara-autonomous-wp0-7), under GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md"
to: "the ka_sangam stream owner"
authority: "The node convention is ruled (M-1 / N-4a / Kṣetra ruling 7): mean. This hands you the interface that lets you comply without editing a file you may not touch."
---

# Saṅgam — one thing: come onto the episode interface so the node convention unifies

Written for the Saṅgam stream owner. One item, and the reason it is only one.

## The situation

The layer ruled **mean node** once, for everybody (M-1 / N-4a / Kṣetra ruling 7). Your scanner reads
`TRUE_NODE`, hard-coded at `pipeline/transit_search.py:10, :64`. That file is in
**`must_not_touch` for every stream, including ours** — so the fix was never yours to make by editing
it, and an earlier draft of the layer binding put it on you in error. That has been corrected: the
binding's B6 row now states that "the kernel path" never means editing that file, and the fix belongs
to this family.

**Our half is done.** Packet S-1/S-2 landed on `l3/gochara-autonomous-wp0-7`:
`GocharaTransitService.find_episodes` now returns kernel episodes with mean-node longitudes
(`RAH_MEAN`/`KET_MEAN`, per N-4), each carrying `contact_id`, `independence_group`, its grain and a
`coverage` object — including for a zero-contact search, where you get a row and a coverage record
rather than silence. **`find_aspects` was deliberately left untouched**, exact shape and all, so none of
your existing duck-typed callers move.

## The one thing to do

**Adopt `find_episodes` and stop bypassing the service.** Concretely:

1. Call `GocharaTransitService.find_episodes(chart_id, targets, horizon, *, bodies, relations, moon)`
   in place of your own scanner path wherever you need transit contacts. Your `engine.py:464`
   `find_aspects` call keeps working unchanged; this is an opt-in, not a migration of that call.
2. Cite our rows rather than re-deriving them:
   `window_ref = {asset_id: 'ka_gochara', generation, id: contact_id}`, which resolves against our
   primary key `(chart_id, generation, contact_id)`.
3. Join our `coverage` row by `window_ref` when you consume our events, so an empty answer of yours is
   distinguishable from a failed one.
4. **Until you are on it:** stamp `comparable_with = different_convention` on every Saṅgam row against
   every Kṣetra row, so nothing downstream reads a true-node result as agreeing with a mean-node one.
   That stamp is the honest interim, not a fix.

**Done looks like:** your contacts come from one producer on one node convention, and a test asserts
that no Saṅgam row carries a node longitude this family did not supply.

## Why only this one

Your other audit items — persisting all four R-6 components, the `comparability_class` rename, the
inclusivity split, `date.today()` and its 29-February crash, `independence_group`, the R-5 stable
identity, the undeclared `ka_vedha_gochara` read, the `confidence_score` packet-versus-code
disagreement — are all yours and none of them are ours to instruct. They are in the layer's own
amendments document. This is the single item where **we** were the blocker, so it is the single item we
are handing over.

## Two notes that may affect your reads

- Our migrations renumbered **1075/1076 → 1080/1081** on 2026-09-24; the L0 repair (PR #2727) holds
  1075–1079 and all five are applied to production. A note of yours citing "1075" as ours now points
  at an L0 file.
- The grain column's one ruled name across all three streams is **`precision_regime`**, values
  `{instant_grain, date_grain}`, and `day_grade` is aliased to `date_grain` **until the successor condition of Saṅgam D-7 is met — every dependent claim has an authorized successor — not for a count of generations** (binding 2.2 §B1, verified at `8211c2dc6`). `comparable_with` is
  the one name for comparability, as a closed enum of exactly four values pinned at
  `WP1_CONTRACTS.md` §6.

## A migration collision to settle — 1085 and 1086

`origin/sangam/stage3` holds `platform/supabase/migrations/1085_kala_convergence_kernel_fields.sql` and
`1086_kala_convergence_r5_identity.sql`. This family holds, in `platform/migrations/`,
`1085_nirmana_l0_bg_transit_rules_vedha_repair.sql` and
`1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql`. Both directories form **one**
runner sequence, so these are genuine duplicate numbers, not two independent series.

First-commit times, measured 2026-09-24:

| number | this family | Saṅgam |
|---|---|---|
| 1085 | 08:54 IST | 11:25 IST |
| 1086 | 11:21 IST | 11:42 IST |

It would still *work* — the runner tracks by filename and sha256, never by number, and orders duplicates
numerically then lexically. But duplicate numbers are how the layer has already mis-read "migration N
applied" twice this week.

**The rule this family proposes, and will abide by in reverse:** whichever side has already applied its
file to a shared database **keeps** the number, because a migration is never renumbered after it is
applied. If neither has applied, first claim holds.

**What is asked of you:** state whether your 1085/1086 have been applied to any shared database. Neither
of this family's two has been applied outside a disposable one. **If yours are applied, this family will
renumber its own to 1087/1088** — say so and it will be done. If yours are not applied, the first-claim
rule puts the move on your side, and the next free number by full re-scan is **1087**; re-scan before
claiming, because that number is only true as of this writing.

### WITHDRAWN, 2026-09-24 — the 1085/1086 question above

Saṅgam answered and was right; this family's alarm was over-applied and is withdrawn. Duplicate
numbers across the two migration directories are already routine on `main`: a full count gives **55
duplicated prefixes** there — Saṅgam reported 41 and understated it. The runner keys on filename plus
sha256, never on number, and orders duplicates numerically then lexically, so two files sharing 1085 in
different directories with different names and no dependency between them are **benign**. Saṅgam's
1085/1086 stay; this family's stay; nobody renumbers, and the applied-state question is moot.

For the record, the difference from the earlier 1075/1076 case, which *did* warrant a renumber: there,
the colliding L0 files were **applied to production**, and a ruled step in this family's own sheet read
"migrations 1075/1076 applied and verified" — so the duplicate would have let a routing be read as an
outcome. No ruling text names 1085 or 1086, and neither side's file is applied. Different situation,
different answer. The lesson kept: renumber for a **specific** misreading, not for the mere fact of a
shared number.

Saṅgam's new `1087_kala_convergence_comparable_with.sql` is noted and is theirs. The next free number
for anyone is therefore **1088**, by scan, re-scanned before claiming.
