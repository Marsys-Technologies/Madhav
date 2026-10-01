---
artifact: IDENTITY_CANONICAL_BYTES_CONTRACT
version: "1.0"
status: DRAFT CONTRACT — closes follow-up F-3 (identity bytes) at spec level; folds into the v1.5 spec at the A5.5 gate; not a frozen spec
date: 2026-10-02
author: stream-B (Exec B) — steward M20261001T223012-e877 item (2)
implementation_read: "Stream A's services/gochara_kernel/{targets,substrate,evaluator,materialise}.py on pravaha/a53-registered-writer @ 8560409b7 (read-only); Stream B's services/gochara_rules/records.py"
depends_on: "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.7 §AM-1, §AM-2, §AM-5, §AM-7, §AM-11"
authority: "Specifies bytes; authorises no code. Every expected UUID below was computed from Stream A's REAL implementation and independently re-derived with hashlib."
---

# Identity canonical-bytes contract (F-3)

**One rule for every identity.** UTF-8 bytes → SHA-256 → first 16 bytes → version nibble 8, variant `10` →
UUID (AM-2; RFC 9562 §5.8). No SHA-1/UUIDv5, no timestamp inside any identity, and **comparison on the
canonical tuple before UUID deduplication** (a UUID alone can collide after the 6 masked bits).

## 1. Storage-domain mapping (what each byte field IS in the stored schema)

| field | stored domain (1153/1155) | canonical token | normalisation / refusal |
|---|---|---|---|
| `body` | `kgpo_body_domain_ck`: 9 lowercase grahas | lowercase name (`mars`, `rahu`) | **lowercase only; the builder REFUSES any other case.** Title-case names (`Mars`) are an *input convenience* mapped by `DB_BODY`, never identity text |
| `relation_kind` (physical) | 8 kinds: `residence aspect conjunction sign_ingress nakshatra_ingress kakshya_crossing station eclipse_instant` | as stored, lowercase | the three transit relations of a record (`residence/aspect/conjunction`) are the same strings; natal relations (`dispositorship …`) are never physical kinds |
| `canonical_target` | `kgpo_target_form_ck` | `point:<λ>` / `span:<1-12>` / `star:<1-27>` (§3–§5) | writer validates the stricter grammar (`targets.validate_canonical_target`) |
| `convention_id` | `ka_gochara_sky_convention.convention_id` | the **full** `sha256:<64 hex>` of the AM-1 vector — `sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3` for the `'5.0'` family | `c0`/`c1` in earlier examples are **test stand-ins only** |
| `occurrence_ordinal` | integer ≥ 1 | decimal, no padding/sign | assigned over the FULL-domain ordered crossing set, append-only |
| `affected_person` | `native father mother spouse child sibling` | as stored | **`native`** — AM-5's earlier illustrative `self` is withdrawn (see §9) |
| `frame` | `kind` or `kind:arg` (`moon lagna dasha_lord graha:<x> bhavat_bhavam:<1-12>`) | `Frame.render()`: arg omitted when absent | graha arg lowercase |
| `agent` (record) | `kgrr_agent_ck`: 9 lowercase grahas | lowercase | a period-role agent is a *role token* only in the AM-5 inventory (AM-11 pin e); records carry the concrete graha |
| `object_role` | 10 values (v1.0 nine + `av_qualifier`) | as stored | |
| `event_class` | the 27 values of `kgrr_event_class_ck` | as stored | |
| `path_id`, `rule_version` | as registered (case preserved for the FK) | **lowercased in AM-5 preimages and obligation bytes only**; the record natural key keeps the registered case | two different cases are two different keys at the FK; the registry must not register case-variants |

## 2. Identity tuples (exhaustive, ordered)

* **Physical object:** `body|relation_kind|canonical_target|convention_id` (4 fields, `|`-joined, no trailing byte).
* **Contact:** physical-object bytes `|` `occurrence_ordinal`.
* **Sky event:** same family (1153 `ka_gochara_sky_event`): `event_id` = hash of `(physical_object_id, occurrence_ordinal)` as the contact — one occurrence, two ledgers.
* **Record:** §7. **Window:** §8 [P]. **Obligation:** AM-5 §1 (9 fields).

## 3. Decimal / point normalisation — and the quantization question, SETTLED

`canonical_target = point:<λ>` is the **natal target's** longitude (an L1 value), never a solved time.

1. λ is wrapped to `[0, 360)`; `360.0 → 0.0`; `-0.0 → 0.0`.
2. Rendered as the **shortest round-trip decimal of the float64** (Python `repr`), fixed notation with **no
   exponent** (`1e-05 → 0.00001`), digits as produced; **no quantization, no rounding mode, no seam rule.**
   The six-decimal rule of earlier drafts is **permanently withdrawn**: `198.5200001` and `198.5200004` are two
   different objects (UUIDs `8df1d125…` vs `b284f87b…` with the real convention).
3. **Round-trip guard (new):** the L1 numeric the value comes from must satisfy
   `Decimal(repr(float(x))) == x.normalize()`; otherwise the builder refuses (an L1 value with more digits than a
   float64 carries would silently lose precision before hashing). `point:198.5200` and `point:198.52` are the same
   object — trailing zeros are never written.
4. The regex `^point:(0|[1-9]\d?|[12]\d\d|3[0-5]\d)(\.\d+)?$` (1153) is the SQL floor; the writer additionally
   forbids a leading-zero integer part and any exponent.

## 4. Sign normalisation

Absolute numerals only: `span:1 … span:12` (1 = Meṣa), no leading zero. A sign **name** (`Libra`, `libra`) is accepted
by `targets.span_target()` as *input* and converted; `span:libra`, `span:07`, `span:13`, `sign:7` are refused
(`sign:` fails the SQL shape; the other three the writer). House numbers never appear in identity — a house is
resolved to its absolute sign through the **frame and the natal lagna** before the object is created.

## 5. Star normalisation

Stored 1-based: `star:1 … star:27`; the tārā oracle's zero-based indices map `star_zero = star_stored − 1` and are
**never** written. **Name → index** (the missing normaliser behind the strict-xfail `O-P6-TARA name→index`): input
text is NFKD-decomposed, diacritics dropped, case-folded, non-alphanumerics removed, then matched **exactly** against
the same normalisation of the 27 canonical names in `ashtakavarga.NAKSHATRAS` (Ashwini = 1 … Revati = 27). No fuzzy
or alias matching and none from memory; an unmatched name **raises**. (Implementation: `p6.nakshatra_index`, Stream B,
when scheduled.)

## 6. The correction component — named, and NOT in the bytes

No time, no precision, no solver method and no correction counter is hashed. A **correction is a new identity**:

| case | allowed | identity effect |
|---|---|---|
| NULL/truncated → solved | UPDATE (enrichment): `t_exact`, `delta_lambda`, `delta_t`, `precision_regime`, `t_out`, `coverage.truncated`, `solver_method` leave their placeholders (1153 flip predicate) | **none** — same UUIDs, no supersedes edge |
| a published non-NULL reading changes | **never an UPDATE** | a NEW physical object under a **corrected `canonical_target`** or a **new `convention_id`** (new `method_version` ⇒ new legacy id too, AM-1 rule 1), same `body` and `relation_kind`; its contacts restart at ordinal 1; the new contact row carries `supersedes_contact_id → the retired predecessor` (chain, never a tree; once only) |

Example (real convention `c₀ = sha256:eac922d4…`, a hypothetical corrected `c₁`): contact
`mars|conjunction|point:198.52|c₀|1` is superseded by `mars|conjunction|point:198.52|c₁|1`; the ordinals of `c₀`'s
object are untouched.

## 7. `record_id` (relationship record) — as implemented

`record_id = UUIDv8( UTF-8( JSON(natural_key) ) )` with **JSON = `sort_keys=True`, separators `(",", ":")`,
`ensure_ascii=False`**, over exactly these 14 fields (`records.NATURAL_KEY_FIELDS`):
`chart_id, generation, event_class, affected_person, frame, agent, relation, object_id, object_role, contact_id,
path_id, rule_version, prerequisites, source_text`.
Renderings: UUIDs as lowercase hyphenated strings; `object_id` = the **physical-object UUID**; `contact_id` is JSON
`null` on natal rows; `frame` = `Frame.render()`; `prerequisites` = the path's declared list as an **ordered** array of
`[predicate_id, rule_version]` pairs (declared order, never sorted); `source_text` may be `null`; there are no floats in
the key. **Not in the key** (and so never able to distinguish two records): `source_page`, `provenance`,
`operator_role`, `ruling_ref`, `object_kind`, temporal support, coverage, precision, scores — two writer paths that
differ only in those collide **by design** and must be reconciled before insert (equal payloads ⇒ replay; unequal ⇒
loud failure). The **older** `records.RelationshipRecord.record_id` property still returns a `sha256:`-tagged hex
string over the same bytes; the DB type is UUID, so the writer's `evaluator.record_uuid` is the identity and the
string form must not be stored or compared.

## 8. `window_id` — [P] proposal (frozen v1.4 is silent beyond the field list)

`window_id = UUIDv8( UTF-8( JSON{chart_id, generation, event_class, path_id, rule_version, interval_lower,
interval_upper} ) )`, same JSON rules, interval bounds as whole-second UTC `YYYY-MM-DDTHH:MM:SSZ` (a window is the
product of one class × path × version search over one admitted interval; peak, score and evidence are *content*,
not identity). Needs a ruling before the window writer lands.

## 9. Class census and version scope (F-3 residuals)

* **Class census:** the 27 classes of the CHECK **minus `birth_anchor`** (zero rows by design, O-CF-N6) = **26 census
  classes**. Serving iterates the **census, never the existing inventories**, so a class with no inventory reads
  `not_searched`. A seal does not require all 26.
* **Registry-version selection:** the inventory pins *every* sealed `(path_id, rule_version)`; per path **exactly one**
  version may be `included` for a class and any earlier/later version is `excluded` — so nothing disappears and nothing
  double-counts interpretively. **Needs two additions to migration 1206 (not applied until Codex returns):** a new
  non-degrading closed reason **`superseded_by_version`** and a seal check **`multiple_included_versions`**.
* **Obligation tokens (AM-5 §1) made normative:** `agent` = lowercase graha or `period_lord:md|ad|pd`; `relation` =
  record vocabulary; `object_role` = the 10-value vocabulary; `target` = the natal object's **canonical_target**
  (`span:7`, `point:<λ>`, `star:<n>`) — the illustrative `lord_of:7` / `occupant_of:7` are **withdrawn**; `frame` as §1;
  `person` = the **stored** `affected_person` (`native`). Candidate invalidation: any change of the snapshot
  (`input_digest`) invalidates the whole dependent chain (AM-5 item 0(d)); verification rows and derived
  contacts/records/windows of a replaced snapshot are deleted in dependency order and rebuilt — outputs computed under
  the previous inputs never survive a replaced snapshot.

## 10. Expected UUID vectors — real convention `sha256:eac922d4…`, computed from Stream A's code, re-derived independently

| canonical bytes (`<c>` = the full convention id) | UUIDv8 |
|---|---|
| PO `mars\|conjunction\|point:198.52\|<c>` | `21219d8f-5e7e-89b3-ba66-aa5bf6b8c2f9` |
| contact `…\|<c>\|1` / `\|2` | `37772ce5-a6af-879f-8e6b-d12bebda58b2` / `41bcff90-631a-836d-9367-126daa8a30e1` |
| PO `mars\|residence\|span:7\|<c>` | `3506e433-a930-8822-a184-a039e17b84a2` |
| contact `…\|1` / `\|2` | `5f55cfe2-3b3b-8581-ac82-1b0970528662` / `2b49b11d-15c9-8c76-b61d-d7941bd63b3d` |
| PO `saturn\|residence\|span:7\|<c>` | `38bff29b-3482-8336-a055-ecf516c1d887` |
| contact `…\|1` / `\|2` | `0020cbe9-90cb-83c6-bcca-6e50c99d32e5` / `c2522448-be48-83c6-b9a9-cd0e610acf7b` |
| PO `moon\|nakshatra_ingress\|star:24\|<c>` | `f292de1b-9d0b-85df-ae49-5d463a6cf643` |
| contact `…\|1` / `\|2` | `cc081945-a36e-8806-9486-7cb82346740c` / `b4dafa7b-8b61-880f-942a-4033b623c6bd` |
| PO `jupiter\|aspect\|point:202.43\|<c>` | `6362f630-bc26-8c33-bae1-26a08ade30ce` |
| contact `…\|1` / `\|2` | `214426b0-166b-8b38-915e-9b88b4b1f486` / `b8f5ece0-3f83-8d67-a809-a9f0ebba44e0` |
| PO `mars\|conjunction\|point:198.5200001\|<c>` | `8df1d125-0ca0-8d67-b4b2-5396034fac6d` |
| PO `mars\|conjunction\|point:198.5200004\|<c>` | `b284f87b-0f3a-83fc-85d8-5810d4df6de5` (differs: no quantization) |
| record (key in §7; marriage / `native` / `lagna` / `mars` / `residence` / `span:7` object / contact above / `P3` `1.0.0`) | `81a5c2b9-69d7-8ac4-84b3-c20acd3c5c33` |

Point strings: `point_target(198.52) = point:198.52`, `(360.0) = point:0.0`, `(1e-5) = point:0.00001`,
`(198.5200001) = point:198.5200001`, `(-0.0) = point:0.0`.

### Which existing vectors change (O-RX-1a successor oracle file; frozen v1.4 untouched)

1. **Unchanged:** the five pinned `c0` vectors of AM-2 (`23276d7c…`, `b6cd1a15…`, `c523b443…`, `8e423fdf…`, uppercase
   `87b023cc…`) and the masked-bit pair — they remain valid as **stand-in-convention** vectors; Stream A's
   `test_a53_targets.py` already carries the lowercase set.
2. **Frozen O-RX-1 (uppercase `Mars|…|c0|n`)** stays in the frozen v1.4 file as history. Stream B's
   `test_a55_substrate_oracles.py` (which builds `body="Mars"`) **must move to lowercase** once
   `PhysicalObjectId` refuses non-lowercase body/relation — O-RX-1a is the executable oracle.
3. **AM-5 W1 vectors change** (`self` → `native`; obligation targets are illustrative): A =
   `ae75da7e-45cf-87a5-adf6-9f5ad0c0b227`, B = `c69d8fe0-ee47-8de6-839b-7a36b0736150`; two-pin W1 inventory digest
   `eeb2ff3ec96187342b8fe6a597ae9b1b093c19a77362d8b17ee347187be4c872` (was `fb278bb9…`); ledgers
   `3320910241d2fb586a6f66dfcdd32f0b734b23c5cc1e4ceb0daa9265a27c2983` (H1) / `afaf3432c267b74cc91ad15744cac8cddc8eb5f1f867bba9bc540cbccccdb8a3` (H2)
   (were `bfab9224…` / `b43e3157…`). **Applied to the 1206 live suite only after Codex returns** (it is under review);
   the input digest `800d572c…` is unchanged.
4. **New vectors** (§10 table) with the real convention id; the `c0` stand-ins stop being the only pinned family.

## 11. Code changes this contract implies (not made here)

* Stream A: `PhysicalObjectId.__post_init__` refuses non-lowercase `body`/`relation_kind`; add the §3 round-trip guard
  to `point_target`; mint only `evaluator.record_uuid` (never the `sha256:` property).
* Stream B: `p6.nakshatra_index` (§5); successor oracle O-RX-1a vectors (§10).
* Migration 1206 (after Codex): `superseded_by_version` reason + `multiple_included_versions` check; W1 vector update.
