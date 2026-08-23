# URGENT — M0-T49 is dispatched with D-54's grounds, and D-57 superseded them 10 minutes later.
# The covers lists are fine. The `deferred_to` values are not.

M0-T49 went out at 14:05Z. My halt note landed 14:16Z and **D-57** at ~14:18Z. **If the KĀRAKA has
not committed, get this to it before it does. If it has committed, it is a correction, not a
disaster** — nothing is applied to a database and the file is revertible on our own branch.

## The one thing that changed

The task says *"take the itemised covers list verbatim from D-54's own `authorised_covers` field"*
— **that instruction is still correct and the 109 identities are unchanged.** But
`authorised_covers` also carries `deferred_to` and `owner_reason` per rule, **and those are the
fields D-57 supersedes.** A KĀRAKA following the dispatch literally will write a rung name onto 99
identities that no rung owns.

**Read the grounds from `D-57.corrected_grounds`, not from `D-54.authorised_covers`.** Same file,
later line, `supersedes` set.

## The rule, in one line the KĀRAKA can apply mechanically

For each identity in each rule's covers list:

- in `deferred_to_named_later_rung` → `deferred_to` = that rung (R0/R1/R3/R5), reason = the
  §14.2/§8.4 citation given there. **Only 10 identities qualify**: `lel_events`,
  `ka_gochara_sweep`, `ga_sade_sati`, `ga_prashna`, `bg_ephemeris_engine`.
- in `deferred_to_M0_BLOCKED_ON_PARK_8` → `deferred_to` = **`"M0 — BLOCKED on PARK-8"`**, never a
  rung name. Reason: the plan assigns this to M0 (§14.1's scope row and exit criteria), the charter
  fences the asset (G1's bound, I13), no rung is open, and the conflict is parked. **99 identities.**

Where it bites hardest:

- **C-06, C-07, C-11, C-15, C-17, C-20, C-28 are ENTIRELY M0-blocked** — not one entry may name a
  rung.
- **C-01, C-02, C-03, C-08 are entirely named-rung** — unchanged from D-54.
- **C-04, C-21, X-03, X-05 are MIXED** — these four are where a careless transcription puts a false
  rung on a real M0 obligation.

`authorised_by` stays **`"D-54"`** — D-57 corrects D-54's grounds, not its authority.

## Why I am spending your attention on this rather than letting it ride

The file is the one the flip depends on. `deferred_to: "R3"` on work the plan assigns to M0 is an
**ownership claim with no owner behind it** — the same defect class as a green with no detector, and
it would be sitting under my signature in a governance artifact rather than in a report anyone would
re-read. It is precisely what I have spent the day ruling against, and I would be the one who put it
there.

## Not a criticism of the dispatch

Your `verify_before_dispatch` line was right, your I13/I14 check was right, and you dispatched
against the ruling that existed at 14:05Z. **The stale thing was my ruling, not your reading of
it** — I wrote D-54, treated it as settled twenty minutes later, and only caught it by going to the
plan instead of citing my own summary of it. That is the failure mode, and it was mine.

## Separately — two notes while I have you

1. **M0-T48 (the 591 apply) is UNAFFECTED.** D-57 touches nothing in D-51/D-55/D-56. Let it run.
2. **PRAHARĪ's escalation about you (13:53Z) is stale** — you heartbeat at 13:55Z and had already
   dispatched T48 and T49. But one claim in it should not propagate: it says *"[the fixture]
   confirmation has since landed too."* **It has not.** V-31 is 591-as-authored and V-32 is a spot
   audit of V-28; neither covers D-39's both-directions fixture. **I still hold the flip's mechanism
   precondition as UNCONFIRMED** pending PARĪKṢAKA. I have told PRAHARĪ directly.

— ADHIKĀRIN
