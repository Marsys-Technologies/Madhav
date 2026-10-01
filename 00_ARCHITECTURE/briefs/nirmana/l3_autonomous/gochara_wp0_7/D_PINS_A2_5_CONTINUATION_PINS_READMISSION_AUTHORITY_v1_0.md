---
artifact: D_PINS_A2_5_CONTINUATION_PINS_READMISSION_AUTHORITY
version: 1.0
status: PINS_READMISSION_AUTHORIZED
date: 2026-10-01
decision: D-PINS-A2.5-CONTINUATION
campaign: pravaha
item: A2.5
---

# D-PINS-A2.5-CONTINUATION — pins re-admission authority (PR #2799, ASTRA v1.0 rework successor)

## The decision, verbatim

From `/Users/Dev/pravaha/run/EVENTS.jsonl`, 2026-10-01T12:14:51+00:00, actor `steward`, message
M20261001T121451-1a8d — the grant clause:

> "(1) D-PINS-A2.5 continuation GRANTED: admit ONE append-only L3 successor over
> l3:639eece63be3:df2b966b1d97 with exactly the delta you listed (candidate =
> approved_intentional_change with the declared source closure; v3_century_materialize /
> moorti_nirnaya / sangam = derived_import_change via episodes.py only), #2793-continuation
> mechanics; delivery-check residual lines byte-identical to main's."

Recorded by the steward on the native's standing authority of 2026-09-30 (the autonomy
addendum). Quoted verbatim; nothing paraphrased.

## Scope of the authority granted

Exactly one operation: fail-closed successor admission
(`nirmana_analysis_layer_pins.py --admit-successor`) of ONE L3 successor over the pin
admitted under D-PINS-A2.5 (`l3:639eece63be3:df2b966b1d97`, archived whole with its writer
snapshot, never rewritten). The delta — verified from content-hashed closures of
`f6cb3914e` (ASTRA v1.0 PUSH 3 head) against the predecessor inventory at `348c8e7fc`:

| writer | classification | why |
|---|---|---|
| `ka_gochara_v4_41_candidate` | `approved_intentional_change` | ASTRA v1.0 rework PUSH 1–3; complete source closure now declared via source_paths (own module + 4 step06 modules + gochara_kernel/ledger.py + legacy_semantics.py) |
| `ka_gochara_v3_century_materialize` | `derived_import_change` | import closure via services/gochara_kernel/episodes.py only (A2 half-open backstop); no own-module edits |
| `ka_moorti_nirnaya` | `derived_import_change` | same closure |
| `ka_sangam` | `derived_import_change` | same closure |

Membership is unchanged (23 `ka_` writers before and after); no other layer moves.

## Why the pin went stale

The ASTRA v1.0 review of PR #2799 (findings A1–A10) required a rework that changed the
admitted writer inventory's digests; the admitted successor `l3:639eece63be3:df2b966b1d97`
no longer matches source. ASTRA amendment rank 3: regenerate + re-admit.

## Authority identity

The immutable approval identity of this authority is the commit that first
introduced this document: `53a3d1f85abaa581ff5c1441eb7e29584a82d120`.

## v1.1 addendum — second successor under the same continuation (2026-10-01)

The ASTRA v1.1 closure check on #2799 (REJECT, narrowed: A1/A2/A7 partly closed)
required a further rework of the same four-writer surface, moving the same four
digests again. The steward's v1.1 verdict (EVENTS.jsonl 2026-10-01T14:04:14Z,
message M20261001T140414-f44d) closes with the operative clause, verbatim:

> "Then refresh digests/pins/census (continuation authority stands), CI green, report."

Scope of THIS admission, under that standing continuation authority: exactly ONE
append-only L3 successor over `l3:f6cb3914e7f1:bf1dba54ee01` (archived whole,
never rewritten) with the same four-writer delta as above —
`ka_gochara_v4_41_candidate` (`approved_intentional_change`, declared source
closure) and `ka_gochara_v3_century_materialize` / `ka_moorti_nirnaya` /
`ka_sangam` (`derived_import_change` via `services/gochara_kernel/episodes.py`
only) — verified from content-hashed closures of the v1.1 rework tree against
the predecessor inventory at `8626bb6da`. Membership unchanged (23 `ka_`
writers); no other layer moves. The source commit is the v1.1 rework's
digest-re-derivation head, whose committed writer inventory is byte-identical
to the derived inventory (`provenance_inventory --check` green).

## v1.2 addendum — third successor under the same continuation (2026-10-01)

Stream A reported a suspected kernel defect to the steward (message
M20261001T172758-6f81): `episodes.in_orb_intervals` resolved ONE unwrapped
band representative per segment (nearest the segment midpoint), so a
stationless body (Sun — never split by stations, one segment spanning the
whole domain) emitted at most ONE in-orb band per level; every other
revolution's occurrence was silently ABSENT (N3-class). The steward's ruling
(EVENTS.jsonl 2026-10-01T17:28:24Z, message M20261001T172824-ebbd), operative
clauses verbatim:

> "RULING on the in_orb_intervals finding: FIX NOW, in #2799's current rework
> push — not deferred to A2.6. … (4) include it in the single pins
> re-admission. Then CI green → report → Codex closure."

Scope of THIS admission, under that standing continuation authority: exactly
ONE append-only L3 successor over `l3:89f788c67827:50e2c3392350` (archived
whole, never rewritten) with the same four-writer delta as above —
`ka_gochara_v4_41_candidate` (`approved_intentional_change`, declared source
closure) and `ka_gochara_v3_century_materialize` / `ka_moorti_nirnaya` /
`ka_sangam` (`derived_import_change` via `services/gochara_kernel/episodes.py`
only — the multi-revolution band enumeration fix; no own-module edits) —
verified from content-hashed closures of the v1.2 rework tree against the
predecessor inventory at `89f788c67`. Membership unchanged (23 `ka_`
writers); no other layer moves. The source commit is the v1.2 rework's
digest-re-derivation head, whose committed writer inventory is byte-identical
to the derived inventory (`provenance_inventory --check` green).

### v1.2 scope expansion — six classifications (steward ruling M20261001T180917-6bd5)

The origin/main merge (`c096f834b`) carried #2823 (`066c58587`, Suvarṇa Track
I-1/I-2), which moved `ka_avadhi` and `ka_vighnakara` on main WITHOUT an L3
pins readmission (main's active pin `l3:4f4a1993c6ad:1ddd6f117934` predates
it). The generator therefore derives a SIX-writer delta predecessor→candidate.
The steward's ruling (EVENTS.jsonl 2026-10-01T18:09:17Z, message
M20261001T180917-6bd5), operative clause verbatim:

> "PINS RULING: (a) — expand the admission to SIX classifications. ka_avadhi
> and ka_vighnakara = derived_import_change, reason text: 'moved on main by
> #2823 (066c58587, Suvarṇa Track I-1/I-2) without an L3 readmission; carried
> here by the origin/main merge; not changed by this PR'. Your four stay as
> authorised. … Residual delivery-check lines must still be byte-identical to
> main's."

Scope of THIS admission is accordingly: exactly ONE append-only L3 successor
over `l3:89f788c67827:50e2c3392350` (archived whole, never rewritten) with
exactly the six-writer delta — the four A2.5 writers above plus
`ka_avadhi` / `ka_vighnakara` (`derived_import_change`, moved on main by
#2823 without an L3 readmission; carried by the origin/main merge; not
changed by this PR). Membership unchanged (23 `ka_` writers); no other layer
moves.
