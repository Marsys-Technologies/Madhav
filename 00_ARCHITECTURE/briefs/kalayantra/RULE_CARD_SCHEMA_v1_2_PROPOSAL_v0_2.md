---
artifact: RULE_CARD_SCHEMA_v1_2_PROPOSAL_v0_2.md
version: 0.2
status: PROPOSAL (to the panel as change-register amendment CR-006)
date: 2026-10-28
authored_by: Claude (Rule Book engine packet E1 builder)
supersedes: RULE_CARD_SCHEMA_v1_2_PROPOSAL_v0_1.md
review: Grok 4.7 independent review, verdict ADOPT-WITH-FIXES (six defects, six MISSING items); surrogate rulings CR-006
machine_readable: platform/python-sidecar/services/rulebook/data/RULE_CARD_SCHEMA_v1_2.json
---

# Rule Card schema v1.2 — proposal v0.2

## 0. What changed from v0.1

v0.2 accepts all six Grok defects and applies the surrogate rulings (CR-006). The main changes:

- **Versioning.**
  - The new version is `rule-card-v1.2`, and the new keys are legal only on it.
  - A v1.1 card is valid unchanged.
  - `field2` takes exactly one of `class_group` or `class_groups`.
- **Vedha.**
  - One list of obstructors, one entry per graha, replaces the `obstructors`/`exempt` blocks.
  - A universal "any graha except …" is its own quoted operator.
  - Vedha is stated as quoted pairs; there is no flat house list and no `primary`.
  - The obstructor relation has no default.
  - A typed `counter_vedha` field is added.
- **Bindu.**
  - The count term is an enum, with quote terms.
  - The count convention is `undeclared` unless the passage states it, and there is no `8 − n` rewrite.
  - Rank comparators carry a quoted domain.
  - The varga owner is required.
  - `bindu_gate` and `bindus_of_8` cannot both appear.
  - A typed `sodhana_stage` field is added.
- **Frame.**
  - New relation `moolatrikona`.
  - `target_sign` gains a quoted `locus` and loses `kind`.
  - `of_role` must name a graha-bearing operand.
  - `frame_terms` are checked.
- **Quotes.** Restricted editions use `quote_form: sha256`. Every witness is a passage id plus token offsets.
- **Per-text convention map.** It no longer asserts any BPHS polarity (§2.2).

## 1. Binding rules for every new field

1. **Verse-only.** Every new value carries quote terms: clear words of the cited passages, or witnesses (§2.5). The verifier checks each one against the cited span, like any other operand.
2. **No defaults.**
   - The schema has no `default` keyword anywhere (a test asserts this).
   - A missing optional key means "not stated". Where it matters it evaluates to NOT_ASSESSED, or it quarantines the card. Nothing fills it in.
   - Every validation test asserts that the card is unchanged after validation.
3. **Filing labels are exempt from quote terms.** These are `card_id`, `drafter`, `round`, `class_group` / `class_groups`, `classical_descriptors` and `confidence_notes`. `gate_term` stays a clear single word, as in v1.1.
4. **Backward compatible.** v1 and v1.1 cards validate unchanged against the v1.2 schema. The v1.2 keys are rejected on those versions.
5. **Validation only, for now.** The E1 compiler validates every v1.2 field. A card that uses one is quarantined as `V12_FIELD_NOT_EVALUATED` until the panel ratifies v1.2 and the evaluator reads the field. A v1.2 card that uses only `class_groups` (a filing label) compiles as before.

## 2. Fields

### 2.1 Vedha (`vedha`, on a `vedha_by` operand; `doctrinal_graha` required)

| Key | Rule |
|---|---|
| `vedha_pairs` | Required, ≥ 1: `[{transit_bhava, vedha_bhava, quote_terms}]`.<br>Each transit house appears once, and no pair maps a house to itself.<br>Every house that the same graha's transit operand names must have a pair.<br>`target_bhavas` is forbidden on the operand (no flat list). There is no `primary`: the primary is the operand's `doctrinal_graha`. |
| `obstructor_relation` | Optional: `{relation: occupies \| aspects, quote_terms}`.<br>**Absent means undeclared.** Use `occupies` only on occupation or transit words, and `aspects` only on dṛṣṭi words. |
| `obstructors` | Required list, possibly empty: `[{graha, status: obstruct \| exempt, quote_terms}]`.<br>One entry per graha, and never the primary itself.<br>**A graha in neither this list nor `universal` is undeclared, and its occupancy reads NOT_ASSESSED.** |
| `universal` | Optional: `{operator: "all_seven_grahas_except_listed_exempt", quote_terms}`. This is the verse's "any planet (other than …)".<br>It covers the seven grahas surya…shani, minus the primary and minus the listed exempt grahas. Rāhu and Ketu are covered only by their own entry: the gochara-vedha verses do not name them (Grok, classical check). |
| `exemption` | Required: `{stated, clause_span}`.<br>`stated: true` needs at least one `exempt` entry.<br>`stated: false` forbids `exempt` entries and requires `clause_span`, the span of the whole vedha clause. The verifier then confirms that the span carries no exemption words. |
| `counter_vedha` | Optional typed field: `{kind: "obstructor_itself_under_vedha_does_not_obstruct", quote_terms}`. **Absent means undeclared.** |

**Direction.** Store only the direction the cited passage names. The converse (for example Saturn's vedha by the Sun) is filled only from the other half of the same passage, never by symmetry.

**Wave-0 effect.**
- The 15 Sun, Moon and Mercury cards become expressible once the panel verse-fills their lists. Each verse names one exempt graha and uses a universal "planets other than …".
- They stay partial-NA for Rāhu and Ketu until a verse or a cited change-register entry declares the nodes.
- The Venus convention (nodes and Moon undeclared) is applied only from such an entry, never by default.

### 2.2 Aṣṭakavarga gate (`bindu_gate`, on a `bindus` operand)

| Key | Rule |
|---|---|
| `varga_owner` | Required: one of the 7 grahas, `sav`, or `undeclared`.<br>Any value other than `undeclared` needs `varga_owner_terms`.<br>A graha owner needs role `ashtakavarga_bav` and must equal `doctrinal_graha` if one is set. `sav` needs role `ashtakavarga_sav`. |
| `reads_sign_of` | Required. It must name another declared operand that is positional: a transiting graha, or an operand with a house. |
| `comparator` | Required: `eq`, `ge`, `le`, `gt`, `lt`, `max_among_signs` or `min_among_signs`. |
| relational (`eq` … `lt`) | Require `value` and `value_terms`, and forbid `rank_domain`.<br>`value` runs 0–8 for a BAV owner and 0–56 for SAV; with an undeclared owner it must be ≤ 8. |
| rank (`*_among_signs`) | Require `rank_domain: {scope: all_twelve_signs \| listed_bhavas, bhavas?, quote_terms}`, and forbid `value`. |
| `count_term` | Required enum: `rekha`, `bindu` or `benefic_dot`, plus `count_term_quote_terms`. |
| `count_convention` | Required: `benefic`, `malefic` or `undeclared`.<br>Any value other than `undeclared` needs `convention_terms` found in the passage or its `frame_citation`.<br>**There is no `8 − n` rewrite:** a `malefic` card is stored but never evaluated. |
| `sodhana_stage` | Required typed field: `prastara`, `trikona`, `ekadhipatya` or `undeclared`. Any value other than `undeclared` needs `sodhana_terms`. `ekadhipatya` means the count after both reductions. |
| field 7 | `bindus_of_8` and `bindu_gate` are mutually exclusive on a card. |

**Per-text map** (`services/rulebook/data/bindu_conventions.json`):
- Grok reads BPHS *bindu* and Phaladīpikā *rekhā* both as the benefic point. Fable's earlier reading differs. The map therefore asserts **no** text-wide polarity: BPHS `rekha` and `bindu` are `undeclared`.
- Polarity now comes only from the verse's own words, such as "benefic dots".
- Effect on the census: C002, C003 and C004 (BPHS) gain `BINDU_CONVENTION_UNDECLARED`. They were already quarantined, so the split stays at 16 active / 25 quarantined.

### 2.3 `sign_intrinsic` frame, `target_sign` and `moolatrikona`

**Frame.**
- `sign_intrinsic` is valid on any plane.
- It requires `frame_terms`, which are checked against the cited passage like every frame.
- It requires at least one operand that carries `target_sign`.

**Relation.** Add `moolatrikona`. The dignity always comes from the operand's own relation (`exalted`, `debilitated`, `own_sign` or `moolatrikona`). `target_sign` therefore has no `kind`, so the two can never contradict each other.

**`target_sign`.** It is `{of_role, locus: natal | transit | dasha_period, locus_terms}`.
- It reads: "the operand's graha, at `locus`, is in the sign where `of_role`'s graha holds this dignity."
- `of_role` must name another operand that bears a graha.
- `locus` must agree with the role: a transiting graha is read at `transit`, a natal graha at `natal`, and a daśā lord at `natal` or `dasha_period`.
- **Wave-0 effect:** C010 and C011 become expressible. The "inimical sign" branch of C010 remains a known gap (§4).

### 2.4 `class_groups`

`field2` takes exactly one of `class_group` (a string) or `class_groups` (minItems 1, unique), and `class_groups` is legal only on v1.2. It is a filing label: no quote terms are needed.

### 2.5 Quote form and witnesses (restricted editions)

**Hash form.** In `field1_citation`, `frame_citation` and exception citations, `quote_form: "sha256"` means three things:
- there is **no** `quote`;
- `quote_sha256` is required;
- `witnesses` are required.

**Witness.** A witness is `{passage_id, token_start, token_end}`, with `token_end` exclusive. Tokens are the matches of `[a-z0-9]+|[Devanagari]+` in the bank's normalised passage text (`verify_cards.norm`).

**`quote_sha256`.** It is the sha256 of the witness tokens of the quote, joined by single spaces.

**Rules.**
- Every quote-term list may hold witnesses in place of strings: `quote_terms`, `frame_terms`, `*_terms` and `clause_span`.
- On a hash-form card, every term must be a witness, and every citation on the card must be in hash form.
- A witness must lie inside a passage the card cites, and its token range must be non-empty. The harness resolves each witness in the bank and runs the same operand checks on the resolved text.

**Clear form.** `quote_form` absent or `clear` behaves as in v1.1. It is for drafting and for public-domain editions. The licence lint still fails clear quote text from restricted editions.

## 3. Cross-field rules (enforced in code, not expressible in JSON Schema)

`services/rulebook/schema.py` holds these as `semantic_errors`. The harness verifier mirrors the passage-dependent ones.

- Witness range is non-empty, and the witness's passage is cited by the card.
- The hash form covers all citations and all terms.
- **Vedha:**
  - no duplicate graha;
  - the primary is never an obstructor;
  - `exemption.stated` agrees with the `exempt` entries;
  - a `stated: false` clause span carries no exemption words;
  - pairs are unique and never map a house to itself;
  - every transit house has a pair.
- **Bindu:**
  - `reads_sign_of` resolves to a positional operand;
  - the owner agrees with the role and the graha;
  - a value above 8 needs `sav`;
  - `bindu_gate` and field-7 `bindus_of_8` are exclusive.
- **Target sign:**
  - the frame is `sign_intrinsic`;
  - `of_role` is graha-bearing;
  - `locus` agrees with the role;
  - `sign_intrinsic` has `frame_terms` and a `target_sign` operand.

## 4. Known gaps, deferred to v1.3 (listed, not encoded)

| Gap | Why deferred |
|---|---|
| Banded phala (0, a middle band and a high band in one verse) | One comparator holds one cut; bands need an ordered list of cuts and results. |
| Kakṣyā owner ("Jupiter's kakṣyā") | `kakshya_cell` is an index 1–8 with no owner, and the order of the kakṣyās has no typed absence. |
| Friendship table: mitra-, śatru- and sama-kṣetra; naisargika vs tātkālika | "Inimical sign" (C010) has nowhere to go until the panel names the table. |
| SAV verses with stated totals above 8 | v1.2 admits SAV values 0–56 for a single relational cut. The verse types that state banded or summed SAV totals, and their L1 source checks, wait for v1.3. |
| Vipareeta vedha (an obstructor that cancels an adverse transit) | Not one of the six Grok items. Only one `counter_vedha` kind is typed. |

## 5. What each Wave-0 card needs after v1.2

| Card(s) | v1.2 makes it expressible | Still needed from the panel |
|---|---|---|
| C016–C025, C035–C039 (15) | `vedha_pairs`, `universal`, the exempt entry, `exemption.stated` | Verse-filled lists. The nodes stay undeclared (partial NA) unless a cited change-register entry rules on them. |
| C026–C034 (Venus, 9, active under v1.1) | They may migrate to `vedha` with `exemption.stated: false` and a `clause_span` | — |
| C003 | `bindu_gate` (`eq 0` on "without", varga owner) | A BAV graha bound by the verse. A count convention stated in the passage; otherwise it stays undeclared. |
| C002, C004 | `reads_sign_of`, varga owner | "More" / "larger" give no value, so they stay quarantined. C002's mean-Jupiter branch stays `MEAN_OPERAND`. |
| C012, C014 | `max_among_signs` with a quoted domain | The transiting graha bound. The karaka school pinned. C014's tautological OR removed, and DF-01. |
| C013 | — | "Good number" gives no comparator. The role/relation mismatch fixed. The karaka school pinned. |
| C015 | — | Kakṣyā owner (a v1.3 gap). |
| C010, C011 | `sign_intrinsic` + `target_sign` (locus `transit`) | C010's inimical branch (a v1.3 gap). |

## 6. Evidence on the branch

**Schema files.**
- `services/rulebook/data/RULE_CARD_SCHEMA_v1_2.json` is generated deterministically from v1.1.
- `RULE_CARD_SCHEMA_v1_1.json` sits alongside it for the parity tests.

**Tests.** `tests/rulebook/test_rulebook_schema_v12.py` covers:
- v1 and v1.1 cards validate under both schemas, and accept/reject parity holds;
- every v1.2 key is rejected on v1.1;
- 57 "rejects a default" cases;
- six typed-absence cases, each checked to leave the card unchanged;
- the convention map asserts no polarity;
- the schema has no `default` keyword.

**Schema interpreter.** `schema.py` interprets the schema without third-party packages, because `jsonschema` is not in the CI requirements. A local cross-check against `jsonschema` 4.26 gave 0 disagreements on 133 cards: the fixtures, the mutations and the 48 Wave-0 member cards. All 48 Wave-0 member cards validate unchanged under v1.2.
