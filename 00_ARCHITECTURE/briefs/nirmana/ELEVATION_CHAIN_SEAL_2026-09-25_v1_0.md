---
artifact: ELEVATION_CHAIN_SEAL_2026-09-25
canonical_id: ELEVATION_CHAIN_SEAL_2026_09_25
version: "1.0"
status: SEALED
date: 2026-09-25
decision_owner: Native
authority: "NATIVE_DECISIONS_2026-09-25_v1_0.md v1.4, decision 13. Signed under ruling 9 — the reviewer, the native or the session may sign a document that has been reviewed."
role: "The seal record for tiers 1-3 of the elevation derivation chain: what is sealed, at which exact content, on which review, and what remains open beneath it."
---

# Elevation chain — tiers 1 to 3 sealed, 2026-09-25

The chain is `product definition → data plane → layer template → layer instance → asset template →
asset instance`. As of today **the first three are sealed** and the last three are open. That is the
whole state, and it is the reason the seal is worth recording: everything above the line stops moving,
so everything below it has a fixed thing to derive from.

## What is sealed, and at what exact content

| tier | artefact | version | sha256 at seal |
|---|---|---|---|
| 1 | `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` | FINAL | `b9c098cd390dd3b1d1ab99738f342ca95e01f3609ffcaca70a37e3f7979a52f5` |
| 2 | `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` | FINAL | `68b991f349edae92519935d5845b6a90f78624f631866c1cbd87a99ca874ec86` |
| 3 | `00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` | FINAL | `bb88bee1e024b349470b74301159114aaedd6880a0e35f76e86ba74819e0ae42` |

These three hashes are the seal. `CAPABILITY_MANIFEST.json` carries the same values per entry, and
`drift_detector.py` recomputes and compares them on every run — so a silent edit to a sealed document
is a HIGH finding on the next pass rather than something a reader has to notice. That is the whole
mechanism; there is nothing else to trust.

**The template's filename keeps `_v1_0`** although its version is FINAL. Renaming it would break the
inheritance lines in the L0 instance, the reviews and the manifest to fix nothing; the identity of
record is the fingerprint above, not the number in the name.

## The review each seal rests on

Ruling 9 requires that a review happened, not that a particular party signs. For each:

- **Tier 1** — `briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md`, verdict ACCEPT, 11 MAJOR + 14 MINOR
  folded. Its two 2026-09-25 elevations (the three planes and the compositional identity in §1.3; the
  Domain correctness obligation in §14, now carrying the owner that decision 11 gave it) are
  native-directed content recorded in its own changelog.
- **Tier 2** — `briefs/reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md`, verdict REJECT on the version
  reviewed, with all 22 findings discharged before this seal: 20 by edit, 1 restated and 1 withdrawn by
  native ruling 11. That review also audited its predecessor's 21 findings one by one against the file
  and found the "all 21 folded" claim untrue — 10 fully, 6 partly, 5 not at all. Both sets are closed now.
- **Tier 3** — `briefs/reviews/KIMI_K3_REVIEW_LAYER_TEMPLATE_v1_0.md`, external fresh-context review,
  findings folded at v1.1. **Stated plainly rather than implied:** the v1.2 delta that followed (§2.7
  rescoped to source carriage, the `Dom` → `Carr` gate, §5.4's signature rule) is a transcription of
  native rulings 9 and 11, not new content, and it was verified line-by-line against those rulings
  before sealing. A seal that rested on an unexamined delta would be exactly the defect this chain has
  spent two days removing.

## What the seal means, operationally

1. **A sealed document is not edited in place on a session's own judgement.** It reopens only by native
   ruling, and the reopen is recorded in its changelog naming that ruling. Fixing a typo is not a
   reopen; changing an obligation, a contract, a count or a scope is.
2. **A derived artefact may not contradict a sealed one.** Where a layer instance or an asset brief
   needs something the sealed tier does not give it, that is a finding against the instance or a
   request to reopen — never a local invention. This is the rule that the L0 instance's own review
   already enforced once, and it now has a seal behind it.
3. **The counts and conventions above the line are settled.** In particular: the data plane is scored
   on **ten** of the parent's eleven §14 obligations, because Domain correctness is discharged above the
   data plane (decision 11); the layer-plan element list is **ten items** (1, 1a, 1b, 2–8); the
   disposition hierarchy is **eight**; the evidence states are **six**; the edge types are **five**. A
   session that "corrects" any of these numbers has broken a seal, not fixed a document.

## What remains open beneath the seal

| tier | artefact | state today |
|---|---|---|
| 3 (instance) | `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md` | `REVISED_PENDING_REVIEW` — its own frontmatter says so, and the manifest's `doc_status` now mirrors that rather than claiming CURRENT. L1–L5 instances not written; decision 8 holds them until L0 closes. |
| 4 (template) | `ASSET_ELEVATION_TEMPLATE_v1_0.md` | v1.1, `READY_FOR_USE`, not sealed. |
| 4 (instance) | per-asset briefs | Open; the eight-gate map in the layer template §5.2 is what each must fill. |

Nothing else in the chain is open. The three sealed tiers are the fixed points the rest is derived
from, and the fingerprints above are how anyone checks that they still are.
