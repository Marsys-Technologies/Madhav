---
artifact: D_PINS_A5_4_PINS_READMISSION_AUTHORITY
version: 1.0
status: PINS_READMISSION_AUTHORIZED
date: 2026-09-30
decision: D-PINS-A5.4
campaign: pravaha
item: A5.4
---

# D-PINS-A5.4 — Nirmāṇa analysis-layer pins re-admission authority (PR #2769, pravaha/a5-tier0s-repairs)

## The decision, verbatim

From `/Users/Dev/pravaha/run/EVENTS.jsonl`, 2026-09-30T13:02:03+00:00, actor `steward` — the formal decision record:

> {"kind":"decision","actor":"steward","decision":"D-PINS-A5.4","state":"decided","detail":"Steward, on the native's 2026-09-30 standing authority: authorise the Nirmāṇa L3 analysis-layer pins successor admission for PR #2769 (A5.4 Tier 0-S repairs) — own-module edits to ka_gochara, ka_gochara_resonance, ka_gochara_v3_century_materialize, ka_moorti_nirnaya, ka_vedha_gochara. Append-only on top of main's current protected baseline (the D-PINS-A2 successor l3:f4c69a6d0cd4:829354703812 — never rewrite it); identity-bound authority evidence doc; per-asset delta classification from import closures; census refresh with explicit provenance; receipts test re-base (rewind convention); delivery-topology check on a simulated squash onto the then-current main.","ts":"2026-09-30T13:02:03+00:00"}

And the steward's execution message to stream A (same timestamp, message M20260930T130203-0531), verbatim:

> {"kind":"message","actor":"steward","to":"A","msg_id":"M20260930T130203-0531","ref":"A5.4","detail":"D-PINS-A5.4 DECIDED by the steward (tracker decision; quote it verbatim in the authority evidence doc). Run the A2.3-precedent sequence on #2769: (1) merge current origin/main into the branch first; (2) authority evidence doc (identity-bound) → register binding → admit ONE append-only L3 successor whose changed_assets exactly equal the 5-asset own-module delta, on top of main's protected baseline l3:f4c69a6d0cd4:829354703812 — the 'baseline was rewritten' error means your branch altered that entry: restore it byte-identical from origin/main before admitting; (3) census refresh with --generated-at/--source-revision = the admission commit; (4) receipts test re-base (rewind convention); (5) delivery-topology check on a simulated squash onto current main + pins pytest in delivery mode — paste output. Then CI green and report --ref A5.4. After that, #2769 gets an independent review (repairs are in the A5.5 gate scope) before I queue it; the native's resonance rebuild follows merge + deploy.","ts":"2026-09-30T13:02:03+00:00"}

Recorded by the steward on the native's standing authority of 2026-09-30 (the
autonomy addendum: the campaign runs headless; the steward decides or delegates
everything not reserved to the native — a pins readmission is not a reserved
decision). Quoted verbatim; nothing paraphrased.

## Scope of the authority granted

This authority is narrow. It authorises exactly one operation: fail-closed
successor admission (`nirmana_analysis_layer_pins.py --admit-successor`) for the
ONE stale analysis layer detected on branch `pravaha/a5-tier0s-repairs` (PR
#2769) after merging `origin/main` (`16e3725cee360ec003f6bf5e85b1f5524fc9b4f8`),
per `MERGE_HYGIENE_12_10c_RUNBOOK.md` step 2 and the D-PINS-A2 precedent
(Pravāha A2.3):

- **L3** (`ka_` prefix): successor over the Pravāha A5.4 Tier 0-S repairs
  changeset delta, on top of main's protected baseline generation
  `l3:f4c69a6d0cd4:829354703812` (the D-PINS-A2 successor, delivered to main by
  the A2.3 merge). The protected baseline entry is **not** rewritten: the
  committed `nirmana-analysis-layer-pins.json` on this branch is byte-identical
  to `origin/main`'s, and the admission archives that generation whole with its
  writer snapshot reconstructed from the protected baseline commit as its
  historical snapshot.

It does **not** grant a general re-pin capability, does not touch any other
layer (L0/L1/L2/L4/L5 verify clean in delivery topology on this branch), and
does not authorise membership changes (none occurred — the changed set is
digest drift on existing writers only).

## Why the pin went stale

The branch's A5.4 repairs edited three writers' own modules
(`services/ka_gochara_resonance/writer.py`,
`services/ka_moorti_nirnaya/{logic,writer}.py`,
`services/ka_vedha_gochara/{logic,writer}.py`) and the shared
`services/gochara_grammar/*` / `services/gochara_v3/*` surfaces, moving the
provenance closures of five L3 writers. The committed pin still names the
D-PINS-A2 successor aggregate (`829354703812…`, admitted at the A2.3 merge);
the branch tree derives the new aggregate (`be13d85ab725…`). Detector-correct
staleness: the writer sources moved; the receipt did not. Per ADK-0026 the
receipt is re-admitted, not the detector weakened.

The "protected baseline generation was rewritten" gate failure is the same
shape as A2.3's pre-admission failure, not an actual edit: the baseline
generation is the *active* pin on this branch, and the branch's regenerated
writer inventory (`nirmana-writer-digests.json`, commit `454dab041`) no longer
matches its archived snapshot. `git diff origin/main HEAD --
platform/src/generated/nirmana-analysis-layer-pins.json` is empty — the
protected entry is byte-identical to `origin/main`. The admission restores the
invariant by archiving the baseline generation with its original writer
digests from the historical snapshot (`origin/main`, `16e3725ce…`).

## Per-asset delta classification

Computed by materialising each writer's provenance closure
(`asset_runner._writer_source_files(_writer_source_paths(asset_id))` — the
exact inputs of `get_writer_source_hash`) at HEAD and diffing every closure
path against `origin/main` (`16e3725ce…`).

| Asset | Classification | Cause |
|---|---|---|
| `ka_gochara` | `derived_import_change` | no own-module edit; closure moved via `services/gochara_grammar/{dasha_data,primitives}.py` |
| `ka_gochara_resonance` | `approved_intentional_change` | own-module edit only (`services/ka_gochara_resonance/writer.py`); no foreign movement |
| `ka_gochara_v3_century_materialize` | `derived_import_change` | no own-module edit; closure moved via `services/gochara_grammar/*` and `services/gochara_v3/{context,engine,mechanisms/w23_tara_bala}.py` |
| `ka_moorti_nirnaya` | `approved_intentional_change` | own-module edits only (`services/ka_moorti_nirnaya/{logic,writer}.py`); no foreign movement |
| `ka_vedha_gochara` | `approved_intentional_and_derived_import_change` | own-module edits (`services/ka_vedha_gochara/{logic,writer}.py`) plus closure movement via `services/gochara_grammar/*` |

All foreign movement is inside the branch's own A5.4 changeset; no
`unapproved_foreign_source`. Membership unchanged.

## Authority identity

The immutable approval identity for this authority is the commit that first
introduced this document: `AUTHORITY_IDENTITY_PENDING_FIRST_COMMIT` (replaced by
the identity-bound amendment commit, same pattern as D-E022's `f4cba9d6` and
D-PINS-A2's `fa0b0a9a0`).
