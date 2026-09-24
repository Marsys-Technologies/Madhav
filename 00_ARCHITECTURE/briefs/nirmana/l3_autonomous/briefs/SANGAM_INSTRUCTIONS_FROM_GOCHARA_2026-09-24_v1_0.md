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
  `{instant_grain, date_grain}`, with `day_grade` a read-alias for one generation. `comparable_with` is
  the one name for comparability, as a closed enum of exactly four values pinned at
  `WP1_CONTRACTS.md` §6.
