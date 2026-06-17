---
brief_id: M2_B4_PATTERN_EXPANSION
karn_session_name: KARN-W3-R3-PATTERN-EXPANSION
wave: 3
stream: C
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30
authored_for: Claude Code execution + native arbitration as needed (discovery session)
session_type: corpus expansion (Gemini-led discovery; Claude reviews and reconciles)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none
  blocks: M2_D7 (per-tool planner uses pattern_ids as planning hints), M2_E2_EVAL_HARNESS (eval harness scores against pattern coverage)
parallel_stream_note: |
  W3-R1 (CHUNKER_COMPLETION) and W3-R2 (CLUSTER_RECLUSTER) run concurrently.
  This brief operates entirely in JSON/MD-output land
  (035_DISCOVERY_LAYER/REGISTERS/) and never touches source code or migrations.
  Disjoint scope.
estimated_time: 3 days (multiple Gemini batches + Claude reviews per batch)

scope_summary: |
  Expand PATTERN_REGISTER from 22 → ≥ 70 patterns, covering:
  - Domain gaps: every domain in {career, finance, psychology, health,
    relationships, spiritual, children, parents, travel, wealth, cross_domain}
    must have ≥ 5 patterns. Currently finance has 0; health, parents,
    relationships, travel each have 1; children and wealth each have 2.
  - Dasha epoch coverage: current 22 patterns are concentrated on Mercury MD
    (ongoing) and Saturn MD (upcoming). Need dedicated coverage of:
    * Mercury MD sub-period remainders (Saturn AD 2024-2027, Ketu AD beyond)
    * Saturn MD (2027-2046) — multiple ADs
    * Ketu MD / cross-dasha transitions
    * Retrodictive patterns (past dashas validated against LEL)
  - AK/AmK function: every new pattern must explicitly declare which karaka
    (AK = Saturn, AmK = Mercury) function it exercises.
  - ≥ 50% of all patterns (≥ 35 of ≥ 70) must be forward-looking with a
    time-indexed falsifier (verification_window_start/end + falsifier_conditions).
  - Two-pass protocol per batch: Gemini proposes, Claude reviews + reconciles.
    Native arbitrates only on unreconcilable disagreements.

  Output: PATTERN_REGISTER_v1_1.json + .md.
  v1_0 is preserved (status: SUPERSEDED).

may_touch:
  - 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_1.json             # CREATE (new version)
  - 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_1.md               # CREATE (mirror)
  - 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json             # ONLY frontmatter status: SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.md               # ONLY frontmatter status: SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/INDEX.json                             # UPDATE to point at v1_1
  - 035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_pattern_expansion_batch<N>_raw.md  # CREATE
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_pattern_expansion_pass2.md         # CREATE (one per batch)
  - 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl                       # APPEND (one event per new pattern)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B4_PATTERN_EXPANSION.md   # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_B4_VERIFICATION_<DATE>.txt                 # CREATE summary

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                           # UI/UX stream
  - All other CLAUDECODE_BRIEF_M2_*.md                                   # other briefs
  - 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_*                        # W3-R2 scope
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_*                   # M2_B5 scope
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_*               # M2_B5 scope
  - platform/**                                                          # all code off-limits
  - 025_HOLISTIC_SYNTHESIS/**                                            # source-of-truth read-only
  - 01_FACTS_LAYER/**                                                     # source-of-truth read-only
  - platform/migrations/**                                               # no migrations

acceptance_criteria:
  AC.1: |
    PATTERN_REGISTER_v1_1.json exists with ≥ 70 entries in .patterns[].
    Each entry has all schema fields:
    pattern_id, claim_text, mechanism, domain, signals_referenced[],
    counter_cases[], classical_basis, alternatives[], validator_results{},
    confidence, significance, is_forward_looking, time_indexed_falsifier{},
    ledger_event_ids[], prediction_ledger_ref (nullable), created_at,
    created_by_session, pass_1_actor, re_validation_status.
    NEW required field: ak_amk_function (string — which karaka(s) the
    pattern exercises and how).
  AC.2: |
    Every domain in {career, finance, psychology, health, relationships,
    spiritual, children, parents, travel, wealth, cross_domain} has ≥ 5
    patterns with that domain as the primary `domain` field.
    (Note: the existing v1_0 uses "mind" where the target domain list uses
    "psychology" — accept both as equivalent for this count.)
  AC.3: |
    ≥ 35 patterns (≥ 50% of ≥ 70) have is_forward_looking = true, AND
    each such pattern has a non-null time_indexed_falsifier with
    verification_window_start, verification_window_end, and ≥ 1
    falsifier_conditions[].
  AC.4: |
    Every pattern (v1_0 carry-forwards AND new patterns) has a non-null,
    non-empty ak_amk_function field. For the 22 v1_0 patterns carried
    forward, this field is backfilled during the reconciliation pass.
  AC.5: |
    Dasha coverage: at least 3 patterns with claim_text or mechanism
    referencing "Saturn MD" (or "Saturn Mahadasha" or "Saturn period
    2027"), at least 3 patterns referencing "Ketu MD" (or "Ketu Mahadasha"
    or "Ketu period"), and at least 5 retrodictive patterns with
    verification anchored against a named LEL event (EVT.xxxx.xx.xx.xx).
  AC.6: |
    Two-pass protocol followed for each Gemini batch:
    - Each batch's raw Gemini response saved to
      035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_pattern_expansion_batch<N>_raw.md
    - Claude pass-2 review saved to
      035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_pattern_expansion_pass2_batch<N>.md
    - Reconciliation decisions documented inline in the pass-2 file
    - Each new pattern has pass_1_actor = "gemini-web-<date>"
  AC.7: |
    06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl appended with one event
    per NEW pattern (v1_0 carry-forwards do not need new ledger events).
    Each event:
    { event_id, event_type='pattern_proposal', actor, pattern_id,
      accepted_at, gemini_response_ref, claude_response_ref,
      accepted_by_session='M2_B4_PATTERN_EXPANSION' }
  AC.8: |
    All signal_ids in signals_referenced[] are valid SIG.MSR.xxx IDs
    that exist in MSR_v3_0.md. No fabricated signal IDs.
    Verified by grep cross-check against MSR_v3_0.md.
  AC.9: |
    PATTERN_REGISTER_v1_0 frontmatter updated to status: SUPERSEDED with
    successor: PATTERN_REGISTER_v1_1 and superseded_at: <ISO>.
    Same update to PATTERN_REGISTER_v1_0.md.
  AC.10: |
    INDEX.json updated to point the pattern_register entry at v1_1.
    Previous version preserved in a previous_versions[] field.
  AC.11: |
    PATTERN_REGISTER_v1_1.md is a rendered mirror of the JSON (same
    structural coverage — per-pattern H2 sections with claim, mechanism,
    domain, ak_amk_function, is_forward_looking, falsifier, signals).
  AC.12: |
    M2_B4_VERIFICATION_<DATE>.txt summarizes:
    - Pre-state (v1_0: 22 patterns, per-domain counts, forward-looking %)
    - Post-state (v1_1: N patterns, per-domain counts, forward-looking %)
    - Dasha epoch coverage table (Mercury MD / Saturn MD / Ketu MD / retrodictive)
    - AK/AmK function coverage
    - AC.8 signal validation report (any invalid IDs found + resolved)
    - Pass-1 and pass-2 actor signatures per batch
  AC.13: |
    This brief's frontmatter `status` flipped to COMPLETE.
  AC.14: |
    git status shows ONLY: 2 new register files (json + md), v1_0 frontmatter
    updates, INDEX.json update, prompts/responses additions, ledger appends,
    this brief's status flip, and verification txt. No other files.

halt_conditions:
  - Branch is not redesign/r0-foundation
  - Pre-existing uncommitted modifications to PATTERN_REGISTER_* files
  - MSR_v3_0.md missing or SIG.MSR. IDs unrecognizable (> 5% invalid IDs
    in a batch after cross-check)
  - Two-pass disagreement that pass-2 cannot reconcile (escalate to native)
  - ≥ 70 pattern target cannot be achieved without fabricating signals
    (halt; report maximum achievable count with valid signals)
  - FORENSIC data required for a pattern is absent from the DB/source
    (mark pattern as [EXTERNAL_COMPUTATION_REQUIRED] with spec; count it
    but flag; do NOT fabricate the computation)
---

# CLAUDECODE_BRIEF — M2_B4_PATTERN_EXPANSION (Wave 3, Stream C)

## §1 — Why this session

The Pattern Register v1.0 contains 22 patterns, all authored during Phase B.5 discovery sessions. They are concentrated in spiritual (5 patterns), cross_domain (3), mind (3), and career (3). Multiple domains are critically underrepresented: **finance has 0 patterns**; health, parents, relationships, and travel have 1 each. The Saturn MD (2027-2046) and Ketu MD periods have minimal forward-looking coverage. The 22 patterns represent < 4% of the 499 MSR signals — a retrieval system that only surfaces 4% of available analytical depth is not yet operational.

The target of ≥ 70 patterns achieves:
- **Domain parity**: every life domain is represented at discovery-query level
- **Dasha coverage**: Saturn MD and Ketu MD are the native's next 19+ years — these are the highest-value prediction windows
- **Retrodictive validation**: grounding patterns in LEL events (PERIOD.xxx, EVT.xxx) makes them falsifiable against recorded history and supports the Learning Layer substrate
- **AK/AmK function tagging**: makes the per-tool planner's cluster selection more precise when patterns are proposed as query hints

This is a discovery session. Output is JSON + markdown. No code changes.

## §2 — Pre-flight self-diagnostics

### §2.1 — Branch + working tree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || echo "[HALT] wrong branch"
git status --short
# HALT if any of these have uncommitted modifications:
#   035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_*
#   06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl
```

### §2.2 — Source data presence

```bash
test -f 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md || echo "[HALT] MSR source missing"
test -f 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json || echo "[HALT] v1_0 missing"
test -f 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl || echo "[HALT] ledger missing"
test -f 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md || echo "[HALT] LEL source missing"
```

### §2.3 — Existing pattern baseline

```bash
python3 -c "
import json
with open('035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json') as f:
    reg = json.load(f)
pats = reg.get('patterns', [])
from collections import Counter
domains = Counter(p['domain'] for p in pats)
fwd = sum(1 for p in pats if p.get('is_forward_looking'))
print(f'Total: {len(pats)} patterns')
print(f'Forward-looking: {fwd}')
print(f'Domain counts: {dict(domains)}')
"
```

Expected: 22 patterns, 11 forward-looking, domains per the v1_0 content.

### §2.4 — MSR signal universe

```bash
grep -c "^### SIG.MSR\." 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
# Expected: ~499
```

## §3 — Orientation: current state and target gaps

Before launching Gemini batches, orient on the gaps by reading:
1. `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json` — 22 existing patterns, their domains, forward-looking status, signals referenced
2. `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — source of 499 signals; note signal_type distribution
3. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` §4 + §5 — 6 chronic patterns + 5 period summaries to anchor retrodictive patterns
4. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` §5.1 — Vimshottari dasha timeline for Saturn MD (2027-2046) and Ketu MD sub-periods

**Gap summary at v1_0:**

| Domain | v1_0 count | Needed (≥5) | Gap |
|---|---|---|---|
| career | 3 | 5 | +2 |
| finance | 0 | 5 | +5 |
| psychology/mind | 3 | 5 | +2 |
| health | 1 | 5 | +4 |
| relationships | 1 | 5 | +4 |
| spiritual | 5 | 5 | 0 |
| children | 2 | 5 | +3 |
| parents | 1 | 5 | +4 |
| travel | 1 | 5 | +4 |
| wealth | 2 | 5 | +3 |
| cross_domain | 3 | 5 | +2 |

**Minimum new patterns to satisfy AC.2:** 33. Total minimum to reach ≥ 70: 48 new patterns.

**Target batch plan (adjust based on what Gemini produces):**
- Batch 1: Finance (5–8 patterns) + Relationships (5–6 patterns) — ~12 patterns
- Batch 2: Health (5–6 patterns) + Parents (5–6 patterns) + Travel (4–5 patterns) — ~14 patterns
- Batch 3: Career additions (2–3) + Wealth additions (3–4) + Cross-domain additions (2–3) + Psychology additions (2–3) — ~10 patterns
- Batch 4: Saturn MD forward-looking patterns across domains — ~8 patterns
- Batch 5: Ketu MD forward-looking patterns + retrodictive patterns anchored in LEL events — ~8 patterns
- Batch 6 (if needed): Gap-fill and ak_amk_function backfill for v1_0 carry-forwards

Adjust batch count based on yield. The goal is ≥ 70 total with all AC gates satisfied, not exactly 48 new patterns.

## §4 — Implementation steps

### §4.1 — Carry forward v1_0 patterns into v1_1

The v1_1 register INCLUDES all 22 v1_0 patterns (carry-forward), plus the new patterns. Do NOT discard v1_0 patterns. Carry-forward patterns are identified with their original PAT.001–PAT.022 IDs.

For each carried-forward pattern, **backfill the ak_amk_function field** during the consolidation pass (§4.7). This field was not in v1_0 schema. Add it to each v1_0 pattern based on reading its mechanism field — no new Gemini call needed, this is Claude's own synthesis work.

### §4.2 — Compose Gemini prompt structure

For each batch, construct a prompt that provides:
1. **Context block** — native's chart summary (AK=Saturn, AmK=Mercury, Lagna=Aries, Moon=Gemini D1-3H, Jupiter-9H Sagittarius, Saturn-7H Libra exalted, Mars-Saturn conjunction 7H, current dasha period, Sade Sati status)
2. **Existing patterns** — brief list of already-covered claim_texts to avoid duplication
3. **Target domain(s)** — which domain(s) this batch should focus on
4. **Target dasha epoch(s)** — Mercury MD sub-periods, Saturn MD, Ketu MD, or retrodictive
5. **Schema instruction** — full JSON schema per AC.1 including the new ak_amk_function field
6. **Signal pool** — the relevant MSR signals for the target domain(s) (pull from MSR_v3_0.md by filtering on domains_affected)
7. **Output format** — JSON array of pattern objects matching the schema

**Important chart facts to include in every prompt:**
- AK = Saturn (Atmakaraka), AmK = Mercury (Amatyakaraka)
- Vimshottari: Mercury MD runs to ~2027; Saturn MD follows (2027–2046)
- Sade Sati Cycle 2 active (Saturn transit Aquarius→Pisces, impact on Moon in Gemini D1-3H)
- D9 Karakamsa = Mercury in Virgo (soul purpose linked to analytical/tech spine)
- Saturn-7H exalted: karaka for marriage, partnerships, foreign lands, service
- Mars-Saturn 7H conjunction: structural tension in all 7H significations
- 12H Pisces: foreign delivery, retreat, moksha gateway
- 8H Scorpio: Ketu in 8H, inheritance, moksha, hidden structures

Save each batch prompt in the responses directory as the raw Gemini output.

### §4.3 — Pass 1: Gemini proposal (per batch)

Run each Gemini prompt and save raw response:

```
035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_pattern_expansion_batch<N>_raw.md
```

Collect all proposed patterns.

### §4.4 — Pass 2: Claude review + reconciliation (per batch)

For each Gemini-proposed pattern in the batch:

**Validation checks:**
1. **Signal ID validity**: every SIG.MSR.xxx in signals_referenced[] must exist in MSR_v3_0.md. Cross-check with `grep "^### SIG.MSR.NNN" MSR_v3_0.md`. Drop or replace invalid IDs.
2. **Domain coherence**: dominant domain matches the majority of the referenced signals' domains_affected field.
3. **Mechanism soundness**: the causal chain in `mechanism` is internally consistent with the chart facts listed above. Flag if mechanism inverts classical Jyotish conventions without justification.
4. **AK/AmK function**: every pattern must declare how Saturn-AK or Mercury-AmK (or both) exercises its karaka function to produce the claimed pattern.
5. **Falsifier quality** (for forward-looking): falsifier_conditions must name specific observable events, not vague outcomes. E.g., "native takes a foreign posting for ≥6 months during 2028-2030" is good; "things go well abroad" is bad.
6. **Counter-case discipline**: counter_cases[] must name the classical textbook expectation this pattern overrides or qualifies.
7. **Retrodictive anchor** (for retrodictive patterns): must reference a specific LEL event ID (EVT.xxx) or period ID (PERIOD.xxx). No free-floating retrodictive claims.

**Reconciliation decisions** (document in pass-2 file):
- Signal dropped (invalid ID) → state replacement or omission
- Domain reassigned → state reason
- Mechanism revised → state what changed and why
- Pattern merged with another (overlap) → state which one survives
- Pattern rejected → state reason

**Halt trigger**: if a Gemini proposal is unreconcilable after 2 revision attempts (Gemini insists on a position Claude considers factually wrong), halt with a structured disagreement note for native arbitration.

Save pass-2 review:
```
035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_pattern_expansion_pass2_batch<N>.md
```

### §4.5 — Consolidation: build PATTERN_REGISTER_v1_1.json

After all batches are reconciled, build the complete register:

**Top-level structure:**
```json
{
  "schema": "06_LEARNING_LAYER/SCHEMAS/pattern_schema_v0_1.json",
  "version": "1.1",
  "produced_by_session": "M2_B4_PATTERN_EXPANSION",
  "produced_at": "<ISO>",
  "supersedes": "PATTERN_REGISTER_v1_0",
  "total_patterns": <N>,
  "forward_looking_count": <M>,
  "retrodictive_count": <R>,
  "domain_counts": { "career": <c>, "finance": <f>, ... },
  "patterns": [ ... ]
}
```

**Pattern ID numbering:** carry-forward patterns keep PAT.001–PAT.022. New patterns start at PAT.023 and increment sequentially.

**New required field on ALL patterns (v1_0 carry-forwards + new):**
```json
"ak_amk_function": "Saturn AK: [what Saturn does in this pattern]; Mercury AmK: [what Mercury does]"
```
For patterns where only one of AK/AmK is activated, still include both with the inactive one noted as "not primary in this pattern."

**validator_results fields** (carry-forward from v1_0 + add if absent):
```json
"validator_results": { "P5": true, "P1": true, "P2": true, "P7": true, "P8": true, "P9": true }
```

### §4.6 — Signal ID validation (AC.8)

After assembling all patterns, run a final cross-check:

```bash
python3 -c "
import json, re, subprocess, sys

with open('035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_1.json') as f:
    reg = json.load(f)

# Get valid signal IDs from MSR
result = subprocess.run(
    ['grep', '-oP', r'(?<=^### )SIG\.MSR\.\d+[a-z]?', '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'],
    capture_output=True, text=True
)
valid_ids = set(result.stdout.strip().splitlines())
print(f'Valid MSR signal IDs: {len(valid_ids)}')

invalid = []
for p in reg['patterns']:
    for sig in p.get('signals_referenced', []):
        if sig not in valid_ids:
            invalid.append((p['pattern_id'], sig))

if invalid:
    print(f'INVALID SIGNAL IDs ({len(invalid)}):')
    for pid, sid in invalid:
        print(f'  {pid}: {sid}')
    sys.exit(1)
else:
    print('All signal IDs valid.')
"
```

If > 5% of referenced IDs are invalid, HALT. Otherwise fix inline (drop or correct) and re-run check.

### §4.7 — ak_amk_function backfill for v1_0 carry-forwards

For each of the 22 carried-forward patterns, read the `mechanism` field and derive the `ak_amk_function` based on the chart's AK/AmK structure:
- Saturn AK: career authority, structural pressure, longevity, moksha, foreign delivery, karmic weight
- Mercury AmK: professional execution, communication, analytical capacity, tech/programming spine, career vehicle

Write a 1–2 sentence ak_amk_function for each. This is Claude's own synthesis — no Gemini call.

### §4.8 — Compose PATTERN_REGISTER_v1_1.md (mirror)

Render the JSON into markdown with frontmatter:
```yaml
---
canonical_id: PATTERN_REGISTER_v1_1
status: CURRENT
supersedes: PATTERN_REGISTER_v1_0
produced_at: <ISO>
produced_by_session: M2_B4_PATTERN_EXPANSION
register_summary:
  total_patterns: <N>
  forward_looking: <M>
  retrodictive: <R>
  per_domain_count: { career: <c>, finance: <f>, ... }
  saturn_md_patterns: <count>
  ketu_md_patterns: <count>
---
```

Body: per-pattern H2 section with:
- `## PAT.NNN — <claim_text[:60]>...`
- Fields: domain, ak_amk_function, is_forward_looking, signals_referenced (count), mechanism (1st sentence), falsifier window (if forward-looking)

### §4.9 — Update v1_0 frontmatter to SUPERSEDED

Edit PATTERN_REGISTER_v1_0.json and PATTERN_REGISTER_v1_0.md frontmatter only:
- `status: SUPERSEDED`
- `successor: PATTERN_REGISTER_v1_1`
- `superseded_at: <ISO>`

Do NOT modify v1_0 content. It is the historical record.

### §4.10 — Update INDEX.json

Edit `035_DISCOVERY_LAYER/REGISTERS/INDEX.json`:
- Add or update the pattern_register entry to point at v1_1
- Include `previous_versions: ["PATTERN_REGISTER_v1_0"]`

### §4.11 — Append to two_pass_events.jsonl

Append one JSONL line per NEW pattern (PAT.023+):

```jsonl
{"event_id":"<uuid_short>","event_type":"pattern_proposal","pattern_id":"PAT.023","actor":"gemini-web-<DATE>","claude_review":"claude-cowork-<DATE>","accepted_at":"<ISO>","gemini_response_ref":"035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_pattern_expansion_batch1_raw.md","claude_response_ref":"035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_pattern_expansion_pass2_batch1.md","accepted_by_session":"M2_B4_PATTERN_EXPANSION"}
```

Do NOT append events for v1_0 carry-forwards (PAT.001–PAT.022 already have their events).

### §4.12 — Verification metrics + status flip

Run AC verification:

```bash
python3 -c "
import json
from collections import Counter

with open('035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_1.json') as f:
    reg = json.load(f)
pats = reg['patterns']
domains = Counter(p['domain'] for p in pats)
fwd = sum(1 for p in pats if p.get('is_forward_looking'))
has_ak = sum(1 for p in pats if p.get('ak_amk_function'))
saturn_md = sum(1 for p in pats if 'saturn md' in (p.get('mechanism','') + p.get('claim_text','')).lower())
ketu_md = sum(1 for p in pats if 'ketu md' in (p.get('mechanism','') + p.get('claim_text','')).lower())

print(f'Total patterns: {len(pats)}')
print(f'Forward-looking: {fwd} ({100*fwd/len(pats):.0f}%)')
print(f'With ak_amk_function: {has_ak}')
print(f'Saturn MD refs: {saturn_md}')
print(f'Ketu MD refs: {ketu_md}')
print(f'Domain counts: {dict(sorted(domains.items()))}')
domain_gaps = {d: c for d, c in domains.items() if c < 5}
print(f'Domain gaps (<5): {domain_gaps}')
if len(pats) < 70: print('[FAIL] AC.1: < 70 patterns')
if fwd / len(pats) < 0.5: print('[FAIL] AC.3: < 50% forward-looking')
if has_ak < len(pats): print('[FAIL] AC.4: missing ak_amk_function on some patterns')
if domain_gaps: print(f'[FAIL] AC.2: domain gaps: {domain_gaps}')
"
```

Write all results to `00_ARCHITECTURE/BRIEFS/M2_B4_VERIFICATION_<DATE>.txt`. Include per-AC PASS/FAIL.

Flip this brief's `status` to COMPLETE.

## §5 — Hard constraints

- **No code edits, no migrations, no deploys.** JSON + markdown outputs only.
- **No fabricated signals.** Every SIG.MSR.xxx in signals_referenced[] must exist in MSR_v3_0.md. If a pattern's mechanism requires a signal that doesn't exist, reference the closest real signal and document the gap.
- **No fabricated chart computations.** If a pattern requires a planetary degree, dasha date, or divisional chart value not already in FORENSIC_ASTROLOGICAL_DATA_v8_0.md, mark it `[EXTERNAL_COMPUTATION_REQUIRED: <spec>]` in the mechanism field and count it as a pattern but flag it.
- **v1_0 preserved as historical record.** Only frontmatter status updated.
- **Two-pass discipline.** Every new pattern has documented pass_1 + pass_2 + ledger entry.
- **HALT on unreconcilable disagreement.** Native arbitrates.
- **Coverage ≥ 70 total patterns with all domain ACs met.** Hard floor.

## §6 — Closing checklist

- [ ] Pre-flight §2.1–§2.4 PASS
- [ ] PATTERN_REGISTER_v1_1.json has ≥ 70 patterns
- [ ] Every domain has ≥ 5 patterns (AC.2)
- [ ] ≥ 50% forward-looking with time-indexed falsifiers (AC.3)
- [ ] All patterns have ak_amk_function (AC.4)
- [ ] Saturn MD: ≥ 3 pattern references; Ketu MD: ≥ 3 pattern references (AC.5)
- [ ] Retrodictive patterns: ≥ 5 anchored in LEL event/period IDs (AC.5)
- [ ] Two-pass artifacts in PROMPTS/gemini and PROMPTS/claude per batch (AC.6)
- [ ] Ledger appended with one event per new pattern (AC.7)
- [ ] All signal IDs validated against MSR_v3_0.md (AC.8)
- [ ] v1_0 frontmatter SUPERSEDED (AC.9)
- [ ] INDEX.json updated to v1_1 (AC.10)
- [ ] .md mirror rendered from .json (AC.11)
- [ ] M2_B4_VERIFICATION_<DATE>.txt has all metrics + AC checklist (AC.12)
- [ ] git status shows only expected files (AC.14)
- [ ] Brief status COMPLETE
- [ ] Session log entry appended to PROJECT_KARN_SESSION_LOG.md

---

*End of M2_B4_PATTERN_EXPANSION. Status: PENDING.*

## Kickoff prompt

```
You are running KARN-W3-R3-PATTERN-EXPANSION.

Read 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B4_PATTERN_EXPANSION.md
as the governing scope. Branch is redesign/r0-foundation. Do NOT read
CLAUDECODE_BRIEF.md at the project root — UI/UX stream owns it.

This session is part of Project KARN. For cross-session context:
- 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (operating rules)
- 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (history)
- 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §3 (autonomous brief contract)

This is a discovery session: expand PATTERN_REGISTER from 22 → ≥ 70 patterns
covering all domains (≥5 each), Saturn MD + Ketu MD dasha epochs, ≥50%
forward-looking with falsifiers, and AK/AmK function tags on every pattern.
Two-pass protocol (Gemini propose, Claude review + reconcile) per batch.
Output is JSON + markdown only — no code, no migrations, no deploys.
Carry forward all 22 v1_0 patterns into v1_1 (do not discard).
Halt only on unreconcilable two-pass disagreement or halt_conditions.
Otherwise complete fully.

At session close, append a standardized closing entry to
PROJECT_KARN_SESSION_LOG.md per the protocol §3.1 entry format. Use
karn_session_name = KARN-W3-R3-PATTERN-EXPANSION.
```
