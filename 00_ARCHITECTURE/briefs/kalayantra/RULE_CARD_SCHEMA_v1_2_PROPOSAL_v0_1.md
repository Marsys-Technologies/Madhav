---
artifact: RULE_CARD_SCHEMA_v1_2_PROPOSAL_v0_1.md
version: 0.1
status: PROPOSAL (doc only; goes to the panel as a change-register amendment)
date: 2026-10-28
authored_by: Claude (Rule Book engine packet E1 builder)
parent: Rule Card schema v1.1; ENGINE_PLAN v0.2 §2.1; E0 operand coverage v0.1 §5; E1 quarantine census v0.1
---

# Rule Card schema v1.2 — minimum amendment proposal

## 0. Why

The E1 compiler (`platform/python-sidecar/services/rulebook/`) quarantines 25 of the 41 Wave-0 cards. Two groups account for 22 of them:

- **15 vedha cards** for the Sun, Moon and Mercury (C016–C025, C035–C039). Each cited verse names one graha that does **not** cause vedha for the transiting graha. The verse states this; v1.1 has no field to carry it (`VEDHA_EXEMPTION_NOT_ENCODABLE`).
- **7 aṣṭakavarga cards** (C002, C003, C004, C012, C013, C014, C015). They have no comparator, no stated count convention, and no link between the transited sign and the bindus operand that is read.

This proposal adds the fewest fields needed to make those cards expressible. It does **not** make them evaluable by itself. Section 3 lists what each card still needs from the panel.

## 1. Rules that bind every new field

1. **Verse-only population.** A field is filled only from the cited passage(s). Each new value carries `quote_terms`: the passage's own words that state it, one-to-one, checked like every other operand.
2. **No invented values.**
   - The schema supplies no default threshold, obstructor, exemption or convention.
   - A "more than 4 bindus" default, or any other number the verse does not give, is forbidden.
   - Where the verse is silent, the field takes an explicit **typed absence** (`"undeclared"` or an empty list with `stated: false`). The compiler then quarantines the card or reads the window as NOT_ASSESSED. It never fills in a value.
3. **Backward compatible.** A v1.1 card is a valid v1.2 card. A missing new field means "not stated", never "false".
4. **Hash-only quotes.** The restricted-edition quote policy is unchanged (M5).

## 2. Fields

### F1 — `vedha` block on a `vedha_by` operand (exemption, verse-sourced)

```jsonc
"vedha": {
  "primary": "<graha>",                  // must equal the operand's doctrinal_graha
  "vedha_bhavas": [<1..12>],             // replaces target_bhavas for vedha_by (v1.1 alias kept)
  "exempt": {
    "stated": true | false,
    "grahas": ["<graha>", ...],          // empty when stated = false
    "quote_terms": ["<verse words naming the exemption>"]
  }
}
```

- **What it does.** It lets the panel encode, for example, "the Sun's vedha is not caused by Saturn" as an exemption on one obstructor. v1.1 `field6_exceptions.cancels` cannot do this, because it cancels the whole card.
- **Compiler rule.**
  - `stated: true` requires non-empty `grahas` and `quote_terms` found in the cited passage.
  - `stated: false` is allowed only when no exemption words appear in the vedha clause. The E1 lexical detector keeps checking this, so a dropped exemption still quarantines the card.
- **L0 counterpart.** There is still no machine-readable exemption column at L0 (E0 §1.2). The engine reads the exemption from the card, not from `services/gochara_rules/vedha.py`.

### F2 — obstructor-set declaration (nodes and the Moon)

```jsonc
"vedha": {
  ...
  "obstructors": {
    "nodes": "obstruct" | "do_not_obstruct" | "undeclared",
    "moon":  "obstruct" | "do_not_obstruct" | "undeclared",
    "quote_terms": ["<verse words, when stated>"]
  }
}
```

- **Typed absence.** `undeclared` is a typed absence, not a default. With `undeclared`, a window in which only a node, or only the Moon, occupies the vedha place reads NOT_ASSESSED. The other grahas form the determinate part of the set. This is how the 9 Venus cards compile today (convention `vedha_obstructor_status_moon_nodes`).
- **Corpus-wide ruling.** If the panel wants one ruling for the whole corpus rather than per verse, it goes in the change register as a cited convention, not in card defaults.
- **Related open item (E0 hazard 14).** The existing L3 `kala_vedha_gochara_interval` CHECKs exclude the Moon and the nodes as obstructors. That exclusion is not adopted.

### F3 — bindu comparator and count convention on a `bindus` operand

```jsonc
"bindu_gate": {
  "reads_sign_of": "<operand id>",       // the transit (or bhava) operand whose sign is read
  "comparator": "eq" | "ge" | "le" | "gt" | "lt" | "max_among_signs" | "min_among_signs",
  "value": <0..8> | null,                // required for eq/ge/le/gt/lt; null for *_among_signs
  "count_term": "rekha" | "bindu" | "benefic_dot" | "<other verse term>",
  "count_convention": "benefic" | "malefic" | "undeclared",
  "quote_terms": ["<verse words for the comparator and the count term>"]
}
```

- **Purpose.** It ties one bindus operand to its comparator and its sign. Today v1.1 relies on the loose field-7 `bindus_of_8` list plus an overloaded `target_role`, and E1 has to quarantine any binding that is not unique (`AMBIGUOUS_COMPARATOR_BINDING`, `BINDU_TARGET_UNLINKED`).
- **Rank comparators.** `max_among_signs` and `min_among_signs` encode verse words such as "highest" or "maximum" as a rank comparison across the 12 signs of the same BAV. They carry no threshold.
- **Still quarantined.** "More", "larger" and "a good number" have no comparator and stay quarantined. The panel withdraws such a card only if its verse gives no comparator at all.
- **"Without rekhās".** The panel may amend it to `eq 0` (ENGINE_PLAN v0.2 §2.1).
- **Count convention.**
  - Stored L1 values are **benefic-point counts**.
  - `count_convention` must agree with the per-text convention map, `services/rulebook/data/bindu_conventions.json`. That map currently declares BPHS "rekhā" = benefic, and treats "benefic dot" as declared by the verse itself.
  - `malefic` would mean the engine reads 8 − value, and only after the map declares that text.
  - `undeclared` quarantines the card (`BINDU_CONVENTION_UNDECLARED`).

### F4 — `class_group` as an array

```jsonc
"field2_target_scope": { "class_groups": ["<class_group>", ...], ... }   // minItems 1, uniqueItems
```

- This matches the `l0_rule_book_card_classes` join table (ENGINE_PLAN v0.2 §1, F-S10).
- A v1.1 `class_group` value `x` reads as `["x"]`.

### F5 — `sign_intrinsic` frame

- **New frame value.** Add `"sign_intrinsic"` to `field3_reference_frame.frame`.
- **Meaning.** A sign is named by an intrinsic property relative to a role, not counted from a reference point. It is valid on any plane, unlike `sign_of_transit_only`, which is transit-only. It needs one companion field on the positional operand:

  ```json
  "target_sign": { "of_role": "<operand id>", "kind": "exaltation" | "debilitation" | "own" | "moolatrikona" }
  ```

- **Which cards.** It makes the two daśā cards C010 and C011 expressible. They are now `FRAME_PLANE_CONTRADICTION`, since they are daśā cards on `sign_of_transit_only` (F-S3).
- **Inimical sign.** C010's "inimical sign" branch also needs a friendship-table pin (naisargika or tātkālika). That kind is left out of this proposal until the panel names it.

## 3. What each card still needs after v1.2

| Card(s) | With v1.2 | Still needed (panel, via change register) |
|---|---|---|
| C016–C025, C035–C039 (15) | F1 exemption, F2 `undeclared` | Nothing more for evaluability. They become partial-NA like the Venus cards until F2 is stated. |
| C003 | F3 (`eq 0` for "without") | Bind the BAV graha, since the card names none. Link the BAV to Mars's transit. |
| C004 | F3 link | "Larger" has no comparator. Stays quarantined unless the verse supplies one. |
| C002 | F3 link | "More" has no comparator. The mean-Jupiter branch stays `MEAN_OPERAND`; the panel may split off the Sun branch. |
| C012, C014 | F3 `max_among_signs` | Bind the transiting graha or class. Pin the karaka school (`formula_id`, E0). C014 also needs its benefic ∨ malefic OR removed (tautological), and DF-01. |
| C013 | F3 | "Good number" has no comparator. The role/relation mismatch must be fixed. The karaka school must be pinned. |
| C015 | F3 | A kakṣyā-cell operand (field 7 `kakshya_cell`). Kakṣyā-crossing instants are an L0 gap (E0b option g). |
| C010, C011 | F5 + `target_sign` | C010 also needs the "inimical" friendship pin. |
| all | F4 | — (no Wave-0 card is multi-class yet) |

## 4. Not proposed

- No default thresholds.
- No corpus-wide obstructor ruling.
- No new relation or role beyond `target_sign`.
- No daśā-system field. C041's "Moola daśā" reading stays as E0 left it.
- The E1 compiler targets v1.1. Compiling the v1.2 fields is a follow-on, after the panel ratifies them.
