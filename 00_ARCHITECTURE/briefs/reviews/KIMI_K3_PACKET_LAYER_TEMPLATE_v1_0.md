# Adversarial review request — LAYER_DEFINITION_AND_STRATEGY_TEMPLATE v1.0

You are an independent adversarial reviewer. Fresh context. **Read-only: do not edit, commit, or
message anyone.** Produce one review document as your output. Effort: maximum.

## Repository

`/Users/Dev/madhav-l3/layer-briefs` (git worktree, branch `l3/kala-layer-briefs`, HEAD `657fc6ef4`).
You have shell and read-only production Postgres access. **Use them.** The author of this template has
produced wrong figures repeatedly in one day by inferring rather than measuring; assume nothing in
this packet is true until you have checked what you can check.

## What to review

**Primary — the artefact under review:**
`00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (~4,300 words)

**Its parents (governing; the template must not contradict them):**
- `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` (tier 1)
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` (tier 2)

**Its only instance, which is the evidence of whether it works:**
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md` (tier 3, ~11,400 words)
- and that instance's own independent review: `00_ARCHITECTURE/briefs/reviews/REVIEW_L0_STRATEGY_v2_0.md`

**Context, not under review:**
- `00_ARCHITECTURE/briefs/nirmana/ELEVATION_DERIVATION_CHAIN_v1_0.md` — the map of the four-tier chain
- `00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v1_0.md` — tier 4, which hangs off this
  template's §4.4 hook

## What this template is for

It is the tier-3 template. One instance per layer (L0…L5). Each instance must be **derivable from the
two parents without inventing a criterion**, and each asset brief (tier 4) must in turn be derivable
from the instance. It has been stamped **once** — L0 — and that instance's review returned REJECT with
two blockers and twelve majors, of which ten were defects in **this template** rather than in the
instance. Those ten are recorded in the instance's §6 and were repaired here.

So the template has been stress-tested once and revised three times in place. It has **never been
independently reviewed.** That is what you are doing.

## The decisions that shape it — do not recommend reversing these

These were ruled by the project owner. Critique their *implementation*, not the rulings.

1. **Value first.** A layer's definition begins from the value it contributes to the customer (Part 0);
   every later section must `traces_to:` that value or be struck.
2. **A layer is the sum of its assets and services.** Value decomposes into individual + synergistic +
   cross-layer terms (Part 1), and the shortfall against the objective *is* the elevation delta.
3. **Reference layers.** L0 is perennial knowledge. Its assets exist because they are the tradition,
   not because a chart reads them. Its individual term is **fidelity**, never ablation; ablation
   applies to a reference layer only cross-layer, to verify consumers, and is never grounds to
   disposition an asset.
4. **Controlled vocabulary.** One canonical id and one closed alias set per thing, owned by L0; every
   other layer conforms (template §2.6).
5. **Three verdicts** — ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT — with the document-vs-thing
   distinction and two anti-rot guards (§5.4).
6. **Certification per criterion, not per definition revision** (§5.3).

## What to judge — report each explicitly

1. **DOES IT PRODUCE A DERIVABLE INSTANCE?** The single most important question. The template's
   promise is that a layer instance built from it lets an asset brief be written with zero
   inventions. Its one instance failed that: the review found seven inventions needed for
   `bg_ontology` and that `bg_vidhi_floors` traced to nothing. §5.2 now requires the 32 criteria be
   mapped to §4.4's inheritance list — **is that repair sufficient, or does the template still permit
   an instance that cannot be derived from?** Test it: pick any section and ask what an asset-brief
   author would do if the instance's author filled it thinly.

2. **THE THREE-TERM ACCOUNTING (Part 1).** individual + synergistic + cross-layer. Is it coherent?
   Is it *measurable* — or does it require an instrument (an ablation harness) that does not exist,
   in which case what does an instance honestly record? §1.5 now says the synergistic fraction is
   recorded only where a harness exists. Is that an honest fallback or an escape hatch?

3. **THE REFERENCE-LAYER CLAUSE.** Ruling 3 was applied in §1.2, §1.5 and §5.1. Is it applied
   *consistently*? Is there anywhere the template still scores a reference layer by contribution?
   Is "fidelity" defined sharply enough to be evaluated, or is it a word?

4. **`measured_by:` MUST NAME THE POPULATION.** This rule was added because three of the L0
   instance's nine wrong figures came from unstated scope. Read the rule as written — does it
   actually prevent the three failure modes it names (an unstated grep scope; a count over a shared
   table compared against one partition; a join whose right key was never checked)? Would a
   conscientious author still get it wrong?

5. **THE ALIGNMENT TEST.** Every section carries `traces_to:`. In the one instance, is the test
   doing work, or is it decorative — sections naming a trace that does not hold? What would make it
   enforceable rather than declarative?

6. **PARENT CONFORMANCE.** Anything in the template that contradicts the product definition or the
   data plane. Any parent obligation for a layer plan — particularly data plane §13.3's eight
   required elements, and product §16's requirements of every layer and asset brief — that the
   template does not carry.

7. **THE VERDICT SCALE AND ITS GUARDS (§5.4).** ACCEPT_WITH_CORRECTIONS is where a process like this
   normally rots. Two guards are specified: every correction names the gate it blocks; the verdict
   becomes ACCEPT only by re-verification. **Are they sufficient?** Name the concrete path by which
   this scale still decays into "accepted, corrections forgotten."

8. **CERTIFICATION PER CRITERION (§5.3).** The record is
   `asset · criterion · criterion_version · evidence · verdict · verified_by · verified_on`.
   Is that enough to survive a criterion revision without either wiping earned work or silently
   keeping stale passes? What is missing from the record?

9. **WHAT THE TEMPLATE MAKES EASY TO GET WRONG.** Not what it forbids — what it *permits* a
   well-intentioned author to do badly. The L0 instance is your evidence: read it as the output of
   this template and ask which of its defects the template invited.

10. **WHAT DOES NOT EARN ITS PLACE.** ~4,300 words for a template. Name what could be cut without
    losing a derivation, a measurement or a guard.

## Constraints on your recommendations

Do not pad toward a governance charter. Do not add process, ceremony or compliance language. If a
recommendation adds words it must buy more than it costs — a shorter, sharper template beats a more
complete one. **Quote exact text when you cite it; never paraphrase and then critique the paraphrase.**
Where you can check a claim against the repository or the database, check it, and say what you ran.

## Output

Write your review to:
`00_ARCHITECTURE/briefs/reviews/KIMI_K3_REVIEW_LAYER_TEMPLATE_v1_0.md`

Structure:
- **Verdict:** ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT (the template's own three-verdict scale)
- **Findings**, numbered, each with severity (BLOCKER / MAJOR / MINOR), the exact section, what is
  wrong, and specific proposed replacement text
- **"Derivability"** — your assessment of question 1, with the concrete test you ran
- **"What this template invites"** — question 9, the most valuable section you can write
- **"What I checked at source"** — every claim you verified, with the command or query and the result
- **"What I could not check"** — stated, not glossed

Be concise. No preamble. Begin.
