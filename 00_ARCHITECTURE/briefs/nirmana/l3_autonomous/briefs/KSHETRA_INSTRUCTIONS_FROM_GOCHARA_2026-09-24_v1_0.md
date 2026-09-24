---
artifact: KSHETRA_INSTRUCTIONS_FROM_GOCHARA_2026_09_24
version: "1.0"
status: ISSUED
date: 2026-09-24
from: "L3 Gochara family (l3/gochara-autonomous-wp0-7), under GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md"
to: "the ka_kshetra stream owner"
authority: "Items 1 and 2 are your own ratified rulings 8 and 4, unexecuted. Item 3 is this family's answer on a vocabulary it owns at WP1 under N-7. Item 4 is not ours to rule and is flagged, not instructed."
---

# Kṣetra — three things owed to the layer, and one flag

Written for the Kṣetra stream owner. Each item names the file and what "done" looks like. Nothing here
authorizes a production write; sequence these behind your own gates.

## 1. Stop being a second producer of two verdicts

Your rulings **8** (house-vedha) and **4** (mūrti) are ratified and name a single producer each:
`ka_vedha_gochara` for vedha, `ka_moorti_nirnaya` for mūrti. Your `build_vedha_primitive` and
`build_moorti_primitive` still compute both independently, so the layer answers the same instant twice
with code that cannot see it is disagreeing.

**Do:** retire both, after **one** `evaluation`-generation cross-check against the owning producers'
rows, and consume the producers' rows by `window_ref` instead. Keep the cross-check's disagreement
report; it is the evidence your ruling asked for.

**Done looks like:** a test that fails if two writers emit a vedha verdict for one instant, and the
same for mūrti. That detector is the binding's B6 test.

**What you now get from us, already landed:** `kala_vedha_gochara` and `kala_moorti_nirnaya` carry the
three stamp columns of the shared-consumer contract — `source_qualification`, `corpus_verifiable`,
`precision_regime` — written by WP9 migration 1082 on this branch, with the writers populating them.
The vocabulary you adopted now has rows behind it. Mūrti is additionally graded at the **true kernel
sign-ingress instant** with its day-grade misclassification rate reported, so `precision_regime` on a
mūrti row is `instant_grain`, not `date_grain`.

## 2. Reconcile your contact producer with our kernel

`services/ka_kshetra/stage0_kinematics.py:329 find_contact_episodes` produces contact episodes with
its own `episode_id`, alongside our kernel's `contact_id`. Two producers, one physical event, reconciled
in no packet. The native ratified our family as the **sole contact-episode producer** (binding B6,
ruling D-S3).

**Do one of these two, and declare which:**

- **Consume.** Read `kala_gochara_contacts` and cite our rows as
  `window_ref = {asset_id: 'ka_gochara', generation, id: contact_id}`. That handle resolves against
  our existing primary key `(chart_id, generation, contact_id)`. No schema change is needed on our side
  and none is wanted: plan R2 means this family imports nothing from you, so the citation runs one way.
- **Or declare evaluation-only.** Keep your episodes, mark them `evaluation` in their epistemic class
  and stamp `comparable_with = different_convention` on every row, so nothing downstream can read them
  as agreeing with ours.

**Also:** remove the `'v1'` COALESCE fall-through at `writer.py:2330-2347` and
`stage4_field.py:1386-1389`, and cite the retired sweep corpus by `window_ref`. A silent fall-through to
a retired generation is a provenance hole.

## 3. `unstable_key` is declined as a `comparable_with` value

`comparable_with` is pinned at `WP1_CONTRACTS.md` §6 under this family's N-7 condition, as a closed
enum of four: `self`, `same_convention_same_inputs`, `same_convention_newer_inputs`,
`different_convention`. Every value answers "may these two rows be compared, and against what".

`unstable_key` names a property of **one row's identity** — that it cannot be re-found across a
rebuild — not a relation between two rows. Admitting it would let a row assert a comparability class
while being unidentifiable, which is the same "a routing recorded as an outcome" defect the layer has
been closing all week, in a new column. **Declined.** The enum stays at four.

**Use these two instead, both already in the contract:**

- On the **comparison record**: `self` for a surrogate-keyed row is `NOT_RUN` with reason
  `unstable_key` — exactly the way `different_convention` already works as a reason code.
- On the **row**: its identity claim is F06 `unqualified` until the content-addressed key lands. Your
  `_routes.path_edge_ids` bigserial gap is already recorded as MUST FIX under binding B3.

If you want the interim machine-visible on your own rows, an additive
`id_basis ∈ {content_addressed, surrogate_unstable}` column **on your own table** touches no Gochara
contract and we have no objection to it.

## 4. Flagged, not instructed — your t-axis defect

Not ours to rule, and we are not asking you to reorder your work. But it is the most serious open
correctness defect the layer's audit found, so it should not sit in a list of vocabulary items:
`stage0_kinematics` emits days-since-**J2000** and `stage4_field.load_kinematics_breakpoints` merges
them into the **birth-relative** axis with no offset (`stage4_field.py:1361-1369` →
`writer.py:2049`). If that read is right, every field row using kinematic breakpoints is wrong, and the
packet does not mention it. Verify it at source before anything else on this list; a vocabulary rename
on top of a wrong time axis is polish on a broken instrument.

## 5. One thing we changed that may affect your reads

Our two migrations renumbered **1075/1076 → 1080/1081** on 2026-09-24, because the L0 vedha-and-frame
repair (PR #2727) claimed 1075–1079 and all five are applied to production. If any Kṣetra file or note
cites "migration 1075" or "1076" meaning ours, it now means the L0 files. Also: `precision_regime` is
the one ruled name for the grain across all three streams, and `day_grade` is aliased to `date_grain` **until the successor condition of Saṅgam D-7 is met — every dependent claim has an authorized successor — not for a count of generations** (binding 2.2 §B1, verified at `8211c2dc6`).

## 6. Correction on migration numbers — **1082 is taken**

You were told on relay that 1082 was the next free number after this family's 1080/1081. **It is not.**
This family's WP9 stamp-column migration is
`platform/migrations/1082_nirmana_l3_vedha_moorti_stamp_columns.sql`, and 1083, 1084, 1085 and 1086 are
claimed too. A full re-scan of every `origin/*` head on 2026-09-24 puts the highest prefix at **1086**,
so the next free is **1087** — and **re-scan again before you claim it**, across both
`platform/migrations/` and `platform/supabase/migrations/`, which form one runner sequence.

Note also that `origin/sangam/stage3` has independently claimed 1085 and 1086, which collide with this
family's files of the same numbers. That is being resolved between this family and Saṅgam on the rule
"whoever has applied theirs keeps the number; if neither has applied, first claim holds". It does not
affect you except as a reason to scan rather than trust any number quoted in a message, including the
one in this paragraph.

### Update, 2026-09-24 — the Saṅgam collision paragraph above is withdrawn; and 1087 is now taken too

Saṅgam answered: duplicate numbers across the two migration directories are already routine on `main`
(**55** duplicated prefixes, counted), the runner keys on filename and sha256 rather than number, and
two same-numbered files in different directories with different names are benign. Nobody renumbers.
Saṅgam has since taken **1087** (`1087_kala_convergence_comparable_with.sql`). So the next free number
is **1088** as of this writing — which is exactly why you scan rather than trust a quoted number.

The substantive point for you is unchanged: **1082 is this family's**, and so are 1083, 1084, 1085 and
1086.
