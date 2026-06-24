---
artifact: SOURCE_AUTHORITY_WEIGHTED_MODEL_v1_0.md
canonical_id: SOURCE_AUTHORITY_WEIGHTED_MODEL
version: 1.0
status: SCOPING NOTE — do not build; read before implementing any classical-text disagreement
created: 2026-06-24
author: Claude Code (Sonnet 4.6) — prompted by native correction on Rahu/Ketu handling
scope: General instrument-wide model for how to represent classical-text disagreements
---

# SOURCE-AUTHORITY-WEIGHTED Disclosure Model

## §1 — The problem this solves

Classical Jyotish texts disagree on some positions. A naive instrument has two failure modes:

1. **Flat-contested / confidence-averaged:** treats every disagreement as a coin-flip and reduces the
   confidence of the primary reading by some factor. This is wrong when one source is dominant and
   others are documented minorities.

2. **Silent:** picks one value with no record of the disagreement. Loses audibility.

The SOURCE-AUTHORITY-WEIGHTED model is the correct alternative.

## §2 — The model

For any classical fact where textual traditions disagree:

| Element | What it contains | Where it lives |
|---|---|---|
| Canonical value | The dominant source's position, at full confidence | The actual data column (e.g. `exaltation_sign`) |
| Confidence | 1.0 if dominant source is unambiguous; lower only if dominant source is itself internally contested | The dignity_score or signal confidence |
| Variant disclosure | Structured list of alternative positions with source + authority tagging | `variant_traditions JSONB` (or equivalent disclosure field) |

**Authority tier vocabulary:**
- `"primary"` — the dominant text for this instrument (BPHS for Parashari; Jaimini Sutras for Jaimini; etc.)
- `"minority"` — documented tradition with a different position but lower authority ranking
- `"contested_primary"` — reserved for cases where the dominant source itself contains both positions (rare)

**Confidence reduction rule:**
> Confidence drops only when the dominant source is genuinely ambiguous or explicitly conditional.
> A minority tradition's competing position is NOT grounds for reducing the dominant source's confidence.

## §3 — Canonical example: Rahu/Ketu exaltation

**BPHS Ch.3 (Santanam):** "Rahu exalted in Taurus, Ketu in Scorpio" — the Parashari mainstream.
Supported by Phaladeepika Ch.1, Saravali, JH/PL software defaults.

**Kerala Jyotish school (Harihara / Prashna Marga lineage):** Rahu in Gemini, Ketu in Sagittarius.

**Exclusionist position:** Some modern scholars omit nodal exaltation entirely.

**Correct representation in this instrument:**
```
bg_dignity_reference (L0):
  exaltation_sign = 'Taurus'          ← canonical per BPHS (full confidence)
  variant_traditions = [
    {"sign":"Taurus",  "authority":"primary",  "label":"Parashari mainstream", ...},
    {"sign":"Gemini",  "authority":"minority",  "label":"Kerala school", ...},
    {"sign":null,      "authority":"minority",  "label":"Exclusionist position", ...}
  ]

ga_condition_composite (L1):
  dignity_d1      = 'exalted'         ← derived from canonical BPHS value
  dignity_score_d1 = 1.0              ← full confidence (BPHS is unambiguous primary)
```

**Prior wrong approach (superseded):** A 0.85 partial-contradiction multiplier was applied to the
`bg_rules` entry for Rahu exaltation, reducing conf from 0.65 to 0.55. This treated the Kerala minority
as a confidence-reducer on the BPHS primary. It is now SUPERSEDED by this model.

## §4 — When to apply this model

Apply SOURCE-AUTHORITY-WEIGHTED treatment whenever:
- A classical fact varies across traditions
- One tradition is clearly dominant for this instrument (BPHS for Parashari, etc.)
- The dominant source is internally consistent on this point

**Do NOT flatten-contest:**
- If BPHS says X and Kerala says Y, the BPHS value is canonical at full confidence; Kerala is disclosed.
- Only if BPHS itself says "some authorities hold X, others hold Y" does confidence moderation apply
  (and even then, model as `contested_primary`, not as minority-vs-primary dilution).

## §5 — Implementation pattern

**L0 schema change required:** Add `variant_traditions JSONB` (or equivalent disclosure column) to
whichever reference table holds the classical value. Pattern:

```sql
ALTER TABLE <reference_table>
    ADD COLUMN IF NOT EXISTS variant_traditions JSONB DEFAULT NULL;
```

**L0 writer change:** Populate `variant_traditions` for every graha/fact where traditions diverge.
Leave NULL for facts where there is no documented disagreement. Structure:
```json
[
  {"sign|value": "<primary value>", "source": "<primary citation>", "authority": "primary", "label": "<human label>"},
  {"sign|value": "<alt value>",     "source": "<alt citation>",     "authority": "minority", "label": "<tradition name>"},
  ...
]
```

**L1 and above:** DO NOT store variant_traditions in L1+ tables. The disclosure lives in L0.
L1 reads the canonical L0 value and computes with it. If a downstream L2+ consumer needs to display
the variants, it JOINs `bg_dignity_reference.variant_traditions` directly — disclosure is available,
not baked into the L1 computation output.

**Cross-table guard:** The guard tests (e.g. `test_bg_dignity_reference.py`) govern the CANONICAL
value column, not `variant_traditions`. They assert agreement between tables on the primary-authority
value. This is correct and does not need changing.

## §6 — Scope of current implementation

As of 2026-06-24, `variant_traditions` is populated for:
- `bg_dignity_reference`: Rahu and Ketu only (the only grahas with documented tradition disagreement
  on exaltation sign).

Other reference tables have no documented tradition disagreements that have been identified. When a
future L2+ session surfaces a new case, apply this pattern:
1. Open `bg_dignity_reference` (or relevant L0 table) and add `variant_traditions` for that entry.
2. DO NOT change the canonical column.
3. DO NOT reduce the L1 confidence.
4. Document in the session close.

## §7 — Application to other instrument layers

This model applies at any layer where classical text disagreements appear:
- **L0 (bg_rules / sutravali_rules):** A rule's confidence should reflect the primary source's own
  certainty, not the existence of minority alternatives. If BPHS states a rule clearly, its confidence
  stays at its textual_strength value; a Kerala commentary disagreeing does not reduce it.
- **L2 Bodha (bo_laksana / bo_sangati):** Interpretation signals should cite their primary source and
  mark variant readings in a disclosure field if they differ by tradition.
- **L3+ (Kāla / Phala):** Predictive signals inherit the source-authority structure from L1 facts.
  If the L1 fact has full confidence (BPHS-primary), the derived prediction inherits that confidence
  unless the prediction logic itself introduces uncertainty.

---
*End of SOURCE_AUTHORITY_WEIGHTED_MODEL_v1_0.md — scoping note only; no build implied.*
