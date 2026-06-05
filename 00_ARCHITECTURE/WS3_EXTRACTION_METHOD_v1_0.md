---
artifact: WS3_EXTRACTION_METHOD_v1_0.md
canonical_id: WS3_EXTRACTION_METHOD
version: 1.0
status: CURRENT
wave: ws3
branch: feature/ws3-rule-base
session: method-and-rubric
authored_by: WS-3 Conductor (Racayitā role) 2026-06-05
reviewed_by: Cowork second-AI reviewer (same session; see §6)
changelog:
  - v1.0 (2026-06-05): Initial method authored and reviewed.
---

# WS-3 Rule Extraction Method v1.0

This document governs every rule extracted by WS-3. The Pramāṇa role reads this document
before verifying any rule. The Review Swarm reads §4 (quality bar) and §5 (rejection protocol).
The Conductor reads §7 (session scope bounds).

---

## §1 — Source text selection and canonical IDs

WS-3 extracts from exactly four texts, in priority order. All four are already ingested into
the M8 corpus (via `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/scripts/`). Rule extraction
reads from the DB/GCS corpus — NOT from re-fetched web sources.

| canonical_id | text_key | Title | School | Translation | Tier | WS-3 target |
|---|---|---|---|---|---|---|
| `BPHS` | `bphs` | Brihat Parashara Hora Shastra | parashari | R. Santhanam | 1 | Primary (pilot + full) |
| `JAIMINI` | `jaimini_sutra` | Jaimini Sutras | jaimini | Iranganti Rangacharya | 2 | Full canon |
| `KP` | `kp_texts` | KP Readers Vols 1–4 | kp | K.S. Krishnamurti (original) | 3 | Full canon |
| `TAJAKA` | `tajaka` | Tajaka Neelakanthi | tajaka | (matched to corpus ingestion) | 3 | Full canon |

**Note on Tajaka:** If `tajaka` is absent from the M8 corpus (not confirmed ingested), the
bphs-pilot session proceeds without it; canon-extraction spawns a one-off ingestion step first.
This is a Tier-2 event (Smṛti log + auto-resolve), not a HALT.

**Texts explicitly excluded from WS-3:**
- Nadi texts (BNN, CKN, Dhruva) — aphorism-style, not rule-structured; belong in WS-2 L2-Bodha
- Phaladeepika, Saravali, Hora Sara, Brihat Jataka, Brihat Samhita, Prashna Marga —
  secondary references; if a rule is cross-confirmed by these, that raises confidence per §3;
  they are NOT primary extraction sources for WS-3

---

## §2 — Verse identification convention

Every rule must cite a specific verse. The verse_ref format:

```
<TEXT_ABBREV>.<CHAPTER>.<VERSE_NUMBER>
```

Examples:
- `BPHS.9.3` — BPHS Chapter 9, verse 3
- `BPHS.9.3-5` — BPHS Chapter 9, verses 3–5 (if rule spans a verse range)
- `JAIMINI.1.1.25` — Jaimini Sutras Adhyaya 1, Pada 1, Sutra 25
- `KP.2.ch7.p42` — KP Vol 2, Chapter 7, page 42 (KP is page-referenced, not verse-numbered)
- `TAJAKA.ch3.v12` — Tajaka chapter + verse

**Chunking alignment:** The M8 ingestion chunks texts at ~600-token overlapping windows with
chapter boundaries preserved. The verse_ref must be locatable within the M8 chunk where the
text_excerpt comes from. If the verse_ref is ambiguous (prose commentary, not sutra), use
`BPHS.9.prose` or similar — and mark confidence ≤0.5 for prose-only extractions.

**Fallback when verse numbering is uncertain:** Mark `verse_ref: BPHS.9.APPROX.3` and cap
confidence at 0.55. Do NOT fabricate a specific verse number.

---

## §3 — Rule schema (mandatory fields for every extracted rule)

Every rule is a YAML object with exactly these fields. No field may be omitted; use `null`
only for `caveats` when none exist.

```yaml
rule_id: <TEXT_ABBREV>.<CHAPTER>.<VERSE_REF>.<SEQUENCE>
  # TEXT_ABBREV: BPHS, JAIMINI, KP, TAJAKA
  # CHAPTER: numeric chapter number (or adhyaya-pada for Jaimini)
  # VERSE_REF: verse number(s) or APPROX.N
  # SEQUENCE: 1-indexed integer if multiple rules from same verse; else 1
  # Example: BPHS.9.3.1, BPHS.9.3.2, JAIMINI.1.1.25.1

source_verse:
  canonical_id: BPHS            # one of: BPHS, JAIMINI, KP, TAJAKA
  verse_ref: "9.3"              # chapter.verse (exact format per §2)
  text_excerpt: |               # verbatim source text, ≤500 chars
    "...exact text from the corpus chunk..."

condition: |                    # antecedent — chart configuration that triggers the rule
  # Must be derivable from text_excerpt. Use chart-element vocabulary:
  # graha names (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu)
  # bhava numbers (1H–12H), signs (Aries–Pisces), dignities (exalted/debilitated/own sign)
  # dasha lords, yoga triggers, etc.
  # Write in plain English; be specific (not "a planet in a good position")

assertion: |                    # consequent — predicted result or quality
  # Must be derivable from text_excerpt. Plain English.
  # Use probabilistic framing if the source uses qualifiers (e.g., "inclines toward X")

scope: graha                    # one of: graha | bhava | yoga | dasha | divisional |
                                # ashtakavarga | nakshatra | transit | muhurta | remedy | misc

school: parashari               # one of: parashari | jaimini | kp | tajaka

confidence: 0.72                # float 0.0–1.0; computed per §3 rubric below

caveats: |                      # classical qualifications from the text itself
  # null if none; otherwise verbatim or close-paraphrase of qualifications in the source
```

---

## §3.1 — Confidence rubric (principled; not a guess)

Confidence = `textual_strength × cross_text_corroboration`

**Factor A — Textual strength** (0.2 – 1.0):

| Condition | Score |
|---|---|
| Sutra-style declarative (active voice, no hedge): "X in Y gives Z" | 1.0 |
| Sloka with qualifier ("usually", "tends to", "may"): "X in Y generally gives Z" | 0.8 |
| Prose commentary or explanatory gloss of a sutra | 0.6 |
| Prose with multiple conditionals or "if/but/unless" chains | 0.5 |
| Approximate verse ref (APPROX.N) | ×0.7 multiplier on above |

**Factor B — Cross-text corroboration** (0.7 – 1.3, multiplicative):

| Cross-text status | Multiplier |
|---|---|
| ≥2 other texts (from the M8 CLASSICAL_ATTRIBUTION_REGISTRY) confirm or extend | 1.3 |
| 1 other text confirms or extends | 1.15 |
| No cross-text data (silent) | 1.0 |
| 1 other text partially contradicts | 0.85 |
| ≥2 other texts contradict | 0.7 |

**Final confidence = min(1.0, A × B)**

**Examples:**
- Sutra "Rahu in 6H from Lagna destroys enemies" (JAIMINI direct sutra, 1 confirming text):
  confidence = min(1.0, 1.0 × 1.15) = 1.0 → cap at 1.0; use 0.95 (never claim perfect certainty)
- BPHS sloka "Moon in 12H may cause expenditure" (qualifier "may", no cross-text):
  confidence = 0.8 × 1.0 = 0.80
- Prose gloss in KP (approximate verse ref, no cross-text):
  confidence = 0.6 × 0.7 × 1.0 = 0.42

**Minimum extractable confidence: 0.30.** Rules below 0.30 are STUBBED with a TODO marker
(Pramāṇa records the failure; the rule is retained as a stub for future review).

---

## §4 — Quality bar (gates and thresholds)

### Pilot quality bar (Gate A threshold):

- **Pramāṇa pass rate ≥ 85%:** Of rules submitted, ≥85% have condition AND assertion
  provably derivable from text_excerpt. The remaining ≤15% are rejected and re-extracted
  (up to 3 attempts per rule; then STUB).
- **Review Swarm consensus ≥ 80%:** Of rules in a batch, ≥80% receive agreement (not
  "reject") from at least 3 of the 5 Review Swarm reviewers.
- **Cowork adversarial agreement ≥ 70%:** Cowork's independent re-extraction of the same
  verses should agree on rule_id / condition / assertion in ≥70% of sampled rules.
  Disagreement rate >15% → Tier-2 escalation (method revision consideration, not HALT).
  Disagreement rate >30% → deep-fix escalation (§B.1 pattern).

### Canon quality bar (Gate B threshold):

- Same thresholds apply per-source batch.
- Additionally: cross-source convergence check — for topics covered by ≥2 texts,
  the concordance draft must show ≥60% of topic-pairs have explicit agree/qualify/conflict
  (not "unclassified") status.

---

## §5 — Pramāṇa verse-trace verification protocol

For every rule, Pramāṇa executes:

1. **Read** the `text_excerpt` and the `verse_ref` — confirm they match (the excerpt is
   actually from that verse/chapter, not a neighboring one).
2. **Test condition derivability:** Is the `condition` (the antecedent chart configuration)
   explicitly stated, strongly implied, or necessarily entailed by the text_excerpt?
   - PASS: explicitly stated in the excerpt
   - PASS: strongly implied (e.g., text says "Rahu in 6th house" → condition "Rahu in 6H" implied)
   - FAIL: condition requires inference beyond the text (e.g., text says nothing about house placement)
3. **Test assertion derivability:** Is the `assertion` (the consequent) explicitly stated,
   strongly implied, or necessarily entailed by the text_excerpt?
   - Same PASS/FAIL criteria as condition
4. **Check fabrication signal:** Does the rule claim specifics (house numbers, planet names,
   exact effects) NOT present in text_excerpt? If yes → automatic FAIL.

**Verification outcomes:**
- Both PASS → rule ACCEPTED (Pramāṇa writes `verified: true` to the rule object)
- Either FAIL → rule REJECTED (first attempt)
  - Rejection message logged: which field failed and why
  - Executor re-extracts (up to 3 attempts with the same verse)
  - After 3 failures: STUB the rule with `stub: true`, `stub_reason: "pramana_failure"`,
    retain `text_excerpt` + `verse_ref` for future human review

---

## §6 — Cowork second-AI reviewer slot

Per CLAUDECODE_BRIEF_WS3_AUTONOMOUS_ACTIVATION §4, between WS-3 sessions the Conductor
writes batches of extracted rules to:

```
00_ARCHITECTURE/CONDUCTOR/ws3/cowork_review_batch_N.md
```

Each batch contains:
- The verse_ref + text_excerpt (verbatim source)
- The extracted rule (condition + assertion + confidence)
- Space for Cowork's independent re-extraction

**Cowork's task (performed in this same session as the second-AI review of the method):**

**METHOD REVIEW (Cowork, acting as second AI):**

Review of WS3_EXTRACTION_METHOD_v1_0.md by Cowork (2026-06-05):

Strengths of the method:
1. The three-tier source hierarchy (BPHS tier 1, Jaimini tier 2, KP/Tajaka tier 3) is
   principled and matches classical tradition's own authority ordering.
2. The confidence rubric (textual_strength × cross_text_corroboration) is explicitly
   quantified — this makes the rubric auditable and reproducible, not a guess.
3. The Pramāṇa verse-trace protocol correctly requires that BOTH condition AND assertion be
   derivable from text_excerpt. This is the right bar — many rule-extraction systems only
   check the assertion.
4. Stubbing on 3-failure rather than silent drop is correct — stubs are recoverable; drops
   are not.
5. Minimum confidence floor of 0.30 is appropriate — below this, the rule is more noise
   than signal.

Revisions required (incorporated below in §6.1):

R1. **KP verse-ref convention needs clarification.** KP texts are prose (Readers 1–4), not
    sutras with verse numbers. The `KP.2.ch7.p42` convention (page-based) is workable but
    page numbers can vary by edition. Clarify: use chapter + section heading as the
    canonical verse_ref for KP, with page as a secondary locator.

R2. **Scope vocabulary is under-specified.** `misc` is a catch-all that will attract
    ambiguous rules. Add: `compound_yoga` (for multi-factor combinations), `shadbala`
    (strength calculation rules), `varshaphal` (annual chart rules), `transit_yoga`
    (transit-specific rules that require birth chart reference).

R3. **The confidence rubric doesn't handle sutras with implicit conditions.** Jaimini sutras
    are famously terse — "Putra bhava from Putrakāraka" implies the entire chart configuration
    for child prediction without stating it. This IS the sutra's full content. The rubric
    should add: "sutra with implicit chart context" → textual_strength = 0.85 (not 1.0, since
    inference is required to unpack the implicit context, but not 0.5 either).

These three revisions are incorporated into §6.1 below.

### §6.1 — Method amendments from Cowork review

**Amendment R1 — KP verse-ref:**
KP texts use chapter + section heading as canonical ref: `KP.<VOL>.ch<N>.<SECTION_SLUG>`.
Example: `KP.3.ch5.significators_for_marriage`. Page number appended as `p<N>` only when
the section spans multiple pages and pinpoint location matters.

**Amendment R2 — Extended scope vocabulary:**

| scope value | meaning |
|---|---|
| `graha` | Planetary nature, dignity, placement rules |
| `bhava` | House signification, lord placement rules |
| `yoga` | Named yoga conditions (Gajakesari, Neecha Bhanga, etc.) |
| `compound_yoga` | Multi-factor combinations not reducible to a single named yoga |
| `dasha` | Dasha-antardasha period rules |
| `divisional` | Divisional chart (D9, D10, D60, etc.) rules |
| `ashtakavarga` | Ashtakavarga calculation + interpretation rules |
| `shadbala` | Planetary strength calculation rules |
| `nakshatra` | Nakshatra-based rules |
| `transit` | Gochar (transit) rules |
| `transit_yoga` | Transit-over-natal combinations |
| `varshaphal` | Annual chart (Tajaka) rules |
| `muhurta` | Election / muhurta rules |
| `remedy` | Remedial measure rules |
| `misc` | Only for rules genuinely uncategorizable above |

**Amendment R3 — Jaimini implicit-condition sutras:**
Add to Factor A textual strength table:

| Condition | Score |
|---|---|
| Jaimini-style sutra with fully implicit chart context (classic terse form) | 0.85 |

---

## §7 — Session scope bounds

**WS-3 may touch:**
- `08_CLASSICAL_CROSS_REFERENCE/` — adding rule extraction artifacts
- `platform/python-sidecar/brahmagyan/rules/` — new `brahmagyan.rules` sub-package (to be created)
- `00_ARCHITECTURE/CONDUCTOR/ws3/` — conductor state, smriti, gate artifacts
- `00_ARCHITECTURE/WS3_EXTRACTION_METHOD_v1_0.md` — this file

**WS-3 must NOT touch:**
- `platform/` source code outside `brahmagyan/rules/` — no API routes, no migrations
- `025_HOLISTIC_SYNTHESIS/` — L2 re-grounding belongs to WS-2
- `00_ARCHITECTURE/BRIEFS/` — governed documents; do not amend
- Any `*_CLOSE_*.md` sealing artifacts from prior workstreams
- `main` branch — all work on `feature/ws3-rule-base` only

---

## §8 — Storage layout for extracted rules

Rules are stored as YAML files in:

```
08_CLASSICAL_CROSS_REFERENCE/brahmagyan_rules/
  bphs_rules.yaml          # BPHS full canon
  jaimini_rules.yaml       # Jaimini Sutras
  kp_rules.yaml            # KP Readers Vols 1-4
  tajaka_rules.yaml        # Tajaka Neelakanthi
  concordance.yaml         # Cross-school concordance (concordance-build session)
  rule_index.json          # Flat index: rule_id → {school, scope, confidence, stub}
  EXTRACTION_RUN_LOG.md    # Per-session extraction log (count, stub rate, quality bar result)
```

Each YAML file uses:
```yaml
# bphs_rules.yaml
metadata:
  source: BPHS
  extraction_session: bphs-pilot  # or canon-extraction
  total_rules: N
  stubbed_rules: N
  pramana_pass_rate: 0.NN
  extraction_date: YYYY-MM-DD

rules:
  - rule_id: BPHS.9.3.1
    source_verse:
      canonical_id: BPHS
      verse_ref: "9.3"
      text_excerpt: |
        ...
    condition: |
      ...
    assertion: |
      ...
    scope: graha
    school: parashari
    confidence: 0.80
    caveats: null
    verified: true         # set by Pramāṇa
    stub: false            # true only for pramana_failure stubs
    stub_reason: null
```

---

## §9 — Conductor-to-session interface

The Conductor passes this document path to each sub-agent. Sub-agents read §3 (schema),
§3.1 (rubric), §5 (Pramāṇa protocol), §8 (storage), and §7 (scope bounds) before
extracting any rule.

The FINAL_SUMMARY from each session reports:
- `rules_extracted:` count of `verified: true` rules
- `rules_stubbed:` count of `stub: true` rules
- `quality_bar_met:` true/false (per §4 thresholds)

---

*End of WS3_EXTRACTION_METHOD v1.0 — authored by WS-3 Conductor (method-and-rubric session),
reviewed and amended by Cowork second-AI reviewer. Three Cowork amendments incorporated inline
(KP verse-ref convention, extended scope vocabulary, Jaimini implicit-sutra textual strength).
This method is the governing document for all WS-3 rule extraction.*
