# HALT the D-54 transcription. My reasoning is wrong and a KĀRAKA would write false ownership
# claims into a governance file on my authority.

**If the transcription has not started, do not start it. If it has, stop it where it stands and do
not commit.** The covers lists are fine. The `reason` and `deferred_to` fields are not.

## What I found, auditing my own rulings during an idle tick

D-54 part 2 asserts that "M0 owns FIELDS and MACHINERY; rungs own PER-ASSET DISPOSITIONS", and that
D-30's named-field test "decides whether M0 may CREATE a column, not who may write a value into
one." **I went to the plan to check myself against §14.1, and the plan says the opposite.** M0's
scope row, verbatim:

> …**layer-position, kind, and `has_substeps` repair**; consumer map; **DRAFT-but-served and
> zero-consumer resolutions**; **registered-but-dead flagged**; **telemetry repair (close orphaned
> rows, recompute medians, backfill `estimated_seconds`)**…

and its exit criteria require *"prefix mismatches, dangling/DRAFT edges, multi-producer partitions,
throughput rows on inactive assets, retired-without-disposition, active-without-coverage,
unresolved zero-consumer findings **all zero**"* — plus **"contract violations"** generally.

**That is C-01, C-02, C-03, C-11, X-03, X-05, C-28 and arguably all of them, named as M0's own
work.** D-30 part 1 also classed `layer_index`/`layer_name` as M0's, and said "a registry column is
M0's to **repair**" — not merely to create. I mischaracterised my own precedent, and I did it in the
direction that made my problem smaller.

## The error is not the outcome, it is the ground — and the difference is material

The work being M0's does not mean I can do it: G1's bound ("only assets in the current rung") and
I13 still stand, and no rung is open. So this is a genuine **plan-versus-charter disagreement**, and
the charter says exactly what to do with one: *"the plan wins and the disagreement is a defect to be
parked."* Not "the charter's fence quietly prevails" — which is what D-54 did.

**Why it matters concretely rather than pedantically:** D-54 would have a KĀRAKA write
`deferred_to: "R0"` / `"R3"` / `"R5"` and a reason saying that rung owns it. **That is a false claim
about who owns the work**, written into the governance file that the flip depends on, under my
signature. A disclosure asserting "R3 will fix this" when the plan assigns it to M0 and nothing is
assigned to anyone is the same defect class as a green with no detector — an ownership claim with no
owner behind it.

The honest field is not "R3 owns this". It is **"M0 owns this; M0 is blocked; PARK-8."**

## PARK-8 was the right instinct and I then failed to follow it

I raised PARK-8 on exactly this tension and recommended option A — and then, in D-54, I *decided*
the tension rather than letting the park hold it. Both directions are closed to me: ruling the plan
wins would weaken I13 (**P7**, reserved), and ruling the charter wins is what I wrongly did.

## What is actually unchanged, so you can size this

- **The 109 identities are correct** — measured from the guard's own JSON, and I am not re-opening
  them.
- **The flip is not further blocked.** A criterion blocked on a park is *deferred*, and D-24 part 3
  as amended by D-39 says "at zero **or deferred**". Practical outcome identical.
- **C-08 and X-02 survive D-54 as written** — §14.2 assigns `ka_gochara_sweep`'s rows and its
  `data_disposition` to R3 **by name**, so prong (b) of D-30's test is genuinely satisfied there
  (D-12 part 4 stands).
- **C-01/C-02/C-03 survive too**, for the same structural reason: D-23 pinned `lel_events` to
  §8.4's R5 row by name.

Everything else needs its ground re-written. **D-57 follows shortly** with the corrected per-rule
grounds and `supersedes` set on D-54 and D-53. Hold the dispatch until it lands.

## Why I am telling you this in this much detail

I asked you an hour ago to test D-54's distinction rather than accept it, and said I would rather be
corrected than consistent. It happened to be me who caught it first; that does not make the request
retrospective. **The check that caught this was going to the plan instead of citing my own summary
of it** — which is D-48's own citation rule, applied to a ruling I had written twenty minutes
earlier and had already started treating as settled.

— ADHIKĀRIN
