---
brief_id: M2_B5_RES_CON_EXPANSION
karn_session_name: KARN-W5-R3-RES-CON-EXPANSION
wave: 5
stream: C
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 4 close
authored_for: Claude Code execution (autonomous, long-running — discovery session)
session_type: discovery (two-pass protocol; JSON register expansion; no code, no migrations)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §C3
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none (resonance + contradiction registers are independent of corpus ETL)
  blocks: M2_E1_PROVENANCE_AUDIT (W6-R3 audits register provenance)
parallel_stream_note: |
  Two other Wave-5 briefs run concurrently:
  - KARN-W5-R1-TEMPORAL-EXTENSION (Stream B — TypeScript + sidecar; no code overlap)
  - KARN-W5-R2-D234-BUNDLE (Stream B — TypeScript + Python chunkers; no code overlap)
  W5-R3 is pure discovery — no code, no DB writes, no deploys. File scope is entirely
  within 035_DISCOVERY_LAYER/REGISTERS/, which neither sibling touches.
estimated_time: 1 day (2 discovery passes, possibly split across 2 sessions)

carry_forward_notes:
  - "CURRENT STATE: resonances 12 (RESONANCE_REGISTER_v1_0.json), contradictions 8
     (CONTRADICTION_REGISTER_v1_0.json). Both v1_0 files are the live registers.
     This session creates v1_1 of both, superseding v1_0."
  - "RESONANCE schema (resonance_id, claim_text, mechanism, domains_bridged,
     signals_referenced, cdlm_cells_referenced, counter_cases, classical_basis,
     alternatives, validator_results, confidence, significance, is_forward_looking,
     time_indexed_falsifier, ledger_event_ids, prediction_ledger_ref, pass_1_actor,
     created_at, created_by_session). NEW resonances must have all these fields."
  - "CONTRADICTION schema (contradiction_id, contradiction_class, hypothesis_text,
     mechanism, domains_implicated, signals_in_conflict, l1_references,
     claude_severity_prior, resolution_options, gemini_verdict, gemini_rationale,
     dr_entry_id, ledger_event_ids, pass_1_actor, created_at, created_by_session).
     NEW contradictions must have all these fields."
  - "CONTRADICTION CLASSES (4): signal_polarity_conflict, system_divergence,
     temporal_paradox, frame_conflict. All 4 must have ≥5 contradictions each in v1_1."
  - "Two-pass protocol: Pass 1 proposes (Claude) → Pass 2 reviews and reconciles (Claude).
     For this session Claude acts as BOTH proposer and reviewer — there is no Gemini
     involvement in W5-R3 (unlike W3-R2 and W3-R3 which had Gemini Pass 1).
     Reason: resonances and contradictions are analytical synthesis, not signal-type
     routing; Claude's cross-domain analytical strength is the right Pass 1 actor here."
  - "MSR_v3_0.md has 499 signals. Reference specific signal IDs (SIG.MSR.XXX) for all
     signals_referenced and signals_in_conflict fields — validate IDs against MSR source."
  - "Pattern register domain labels: use 'mind' not 'psychology' (W3 carry-forward;
     pattern_register uses 'mind'. Resonance register can use either; be consistent
     with whichever v1_0 used — check the existing domain labels first.)"
  - "CLUSTER_ATLAS_v1_1 has 34 clusters across all domains — consult for signal groupings
     when constructing resonances that bridge clusters."
  - "PATTERN_REGISTER_v1_1 has 70 patterns — some patterns embed resonance-adjacent
     mechanism descriptions. Cross-reference to avoid duplication, and to find
     existing resonance claims that should be formalized in the register."
  - "Moon in Purva Bhadrapada (Jupiter-ruled). Dasha sequence:
     Jupiter MD (1984→1991), Saturn MD (1991→2010), Mercury MD (2010→2027),
     Ketu MD (2027→2034), Venus MD (2034→2054). Use accurate dasha references."
  - "RM_v2_0.md (28 elements) is the existing L2.5 Resonance Matrix — READ IT before
     proposing new resonances. RM elements are at higher abstraction than register
     resonances, but there must be no direct contradiction between them."

scope_summary: |
  Expand the resonance and contradiction registers from their v1_0 baselines to v1_1.

  Targets:
  - RESONANCE_REGISTER_v1_1.json: 12 → ≥ 24 resonances
    - ≥ 24 of 36 possible domain-pair combinations covered (36 = 9 choose 2 + 9 self-pairs)
    - All resonances have confidence ≥ 0.70
    - ≥ 8 are forward_looking with time_indexed_falsifier
    - All cite specific MSR signal IDs
  - CONTRADICTION_REGISTER_v1_1.json: 8 → ≥ 20 contradictions
    - All 4 contradiction_class values have ≥ 5 entries each
    - All contradictions cite specific MSR signal IDs in signals_in_conflict
    - claude_severity_prior on each: 'low' | 'medium' | 'high' | 'critical'
    - resolution_options: ≥ 2 options per contradiction

  Two-pass protocol (Claude-only for this session):
  - Pass 1 (Proposal): Generate new resonances and contradictions in batches of 6-8.
    Produce raw proposal text + tentative JSON.
  - Pass 2 (Review): For each batch, review for: signal ID validity, schema completeness,
    non-duplication with v1_0 entries, internal consistency of mechanism, domain coverage.
    Accept, revise, or reject each proposed item.
  - Produce final v1_1 JSON files incorporating all accepted items.

  Deliverables:
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json (CREATE)
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.md (CREATE — markdown companion)
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json (CREATE)
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.md (CREATE)
  - Update v1_0 files: status → SUPERSEDED
  - Update 035_DISCOVERY_LAYER/REGISTERS/INDEX.json (both register entries → v1_1)
  - Append two_pass_events.jsonl entries (≥ 12 for resonances + ≥ 12 for contradictions)

may_touch:
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json       # CREATE
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.md         # CREATE
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json       # MODIFY — status→SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.md         # MODIFY — status→SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json   # CREATE
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.md     # CREATE
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json   # MODIFY — status→SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.md     # MODIFY — status→SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/INDEX.json                         # MODIFY — point both → v1_1
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<date>_resonance_pass1.md    # CREATE — Pass 1 artifact
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<date>_resonance_pass2.md    # CREATE — Pass 2 artifact
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<date>_contradiction_pass1.md  # CREATE
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<date>_contradiction_pass2.md  # CREATE
  - 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl                   # MODIFY — append events
  - 035_DISCOVERY_LAYER/M2_B5_VERIFICATION_<DATE>.txt                # CREATE — AC verification
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B5_RES_CON_EXPANSION.md  # status flip
  - 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md                      # append session entry

must_not_touch:
  - All platform/** code
  - All migrations
  - CLUSTER_ATLAS_v1_1.json (read-only reference)
  - PATTERN_REGISTER_v1_1.json (read-only reference)
  - MSR_v3_0.md (read-only reference; do not modify signal text)
  - RM_v2_0.md (read-only reference)
  - UCN_v4_0.md (read-only reference)
  - CDLM_v1_1.md (read-only reference)
---

# KARN-W5-R3-RES-CON-EXPANSION — Execution Brief

## §0 — Context

This is an autonomous Claude Code session running in **discovery mode**. There is no code to
write, no DB to migrate, no deploy. The entire output is JSON register files + markdown
companions + two-pass artifacts.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §C3`.

You are expanding two corpus registers: resonances (cross-domain signal harmonics) and
contradictions (intra-chart tensions). These registers are consumed by the `resonance_register`
and `contradiction_register` TypeScript retrieval tools that already exist and are live.
Expanding the registers immediately improves retrieval quality for synthesis queries.

**Two-pass protocol:** Unlike W3-R2 and W3-R3 (which had Gemini as Pass 1 actor), this
session runs Claude as both proposer (Pass 1) and reviewer (Pass 2). Proceed in batches.
Save Pass 1 raw output as a response artifact before beginning Pass 2.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation.

# PF.2 — Working tree clean
git status --short

# PF.3 — Confirm source registers exist and count current entries
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json'))
c = json.load(open('035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json'))
print('Resonances v1_0:', len(r.get('resonances', [])))
print('Contradictions v1_0:', len(c.get('contradictions', [])))
print('Resonance IDs:', [x['resonance_id'] for x in r.get('resonances', [])])
print('Contradiction classes:', set(x['contradiction_class'] for x in c.get('contradictions', [])))
print('Contradiction IDs:', [x['contradiction_id'] for x in c.get('contradictions', [])])
"
# Expected: 12 resonances (RES.001–RES.012), 8 contradictions (CON.001–CON.008)

# PF.4 — Read reference materials
# Read RM_v2_0.md resonance elements (existing L2.5 synthesis):
grep -n "^## RM\." 025_HOLISTIC_SYNTHESIS/RM_v2_0.md | head -30
# Read existing v1_0 resonances (understand what's already covered):
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json'))
for x in r['resonances']:
    print(x['resonance_id'], x['domains_bridged'], x['claim_text'][:80])
"
# Read existing v1_0 contradictions:
python3 -c "
import json
c = json.load(open('035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json'))
for x in c['contradictions']:
    print(x['contradiction_id'], x['contradiction_class'], x['hypothesis_text'][:80])
"

# PF.5 — Check CLUSTER_ATLAS for domain topology
python3 -c "
import json
ca = json.load(open('035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json'))
clusters = ca.get('clusters', [])
print('Total clusters:', len(clusters))
for cl in clusters[:5]:
    print(cl['cluster_id'], cl.get('dominant_domain','?'), cl.get('name','?'))
"

# PF.6 — Scan MSR_v3_0.md for signal count and domain distribution
grep -c "^SIG.MSR\." 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 2>/dev/null || \
  grep -c "signal_id:" 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 2>/dev/null
# Record: confirms 499 signals available for citation.
```

---

## §2 — Discovery approach

### §2.0 — Domain-pair coverage inventory

Before proposing new resonances, compute the current domain-pair coverage from v1_0:

Domains: career, children, finance/wealth, health, mind/psychology, parents, relationships,
         spiritual, travel, cross_domain.

For each resonance in v1_0, note its `domains_bridged` pair. Identify uncovered or
undercovered domain pairs — these are the priority targets for new resonances.

Required: ≥ 24 of 36 domain-pair combinations covered in v1_1. "Self-pair" (career × career =
within-domain resonance) counts as 1 of the 36 if it appears. Cross-domain resonances that
involve 3+ domains count for each pair they bridge.

### §2.1 — Resonance proposal batches

Propose new resonances in **3 batches of 4–5 each** (targeting ≥ 12 new resonances
to reach 24 total from the v1_0 baseline of 12).

**Priority domain gaps to fill (determine from PF.4 + §2.0 inventory):**
- Domain pairs currently at zero or one resonance get priority.
- Ensure health × finance, children × spiritual, travel × career,
  health × mind, parents × finance have entries.
- ≥ 8 of the new resonances must have `is_forward_looking: true` with a
  `time_indexed_falsifier` that references a specific future dasha window
  (e.g., "Ketu MD 2027-2034", "Venus MD 2034-2054", "Jupiter transit 2025-2026").

**Schema template for each new resonance:**
```json
{
  "resonance_id": "RES.013",
  "claim_text": "<specific, falsifiable claim about cross-domain signal harmony>",
  "mechanism": "<astrological structural reason — cite specific planetary positions, house lords, yoga memberships>",
  "domains_bridged": ["domain_a", "domain_b"],
  "signals_referenced": ["SIG.MSR.XXX", "SIG.MSR.YYY"],
  "cdlm_cells_referenced": [],
  "counter_cases": "<when would this resonance fail? what would disprove it?>",
  "classical_basis": "<classical text or principle cited>",
  "alternatives": "<alternative explanations rejected and why>",
  "validator_results": {"pass_1_accepted": true, "pass_2_accepted": null},
  "confidence": 0.80,
  "significance": 0.85,
  "is_forward_looking": false,
  "time_indexed_falsifier": null,
  "ledger_event_ids": [],
  "prediction_ledger_ref": null,
  "pass_1_actor": "claude",
  "created_at": "2026-04-30",
  "created_by_session": "KARN-W5-R3-RES-CON-EXPANSION"
}
```

**Quality bar for resonances:**
- `claim_text` must be specific enough to be falsifiable — not "career and spirituality are connected"
  but "the Saturn AK/AmK dual-function means professional authority actions directly discharge
  karmic debt, making career performance a form of tapas — financial setbacks in career are
  simultaneously dharmic purification events."
- `mechanism` must cite specific placements (e.g., "Saturn 7H exaltation as AK+AmK, D60 Saturn
  at Lagna") not generalities.
- `signals_referenced` must be real signal IDs from MSR_v3_0.md — validate each.
- `confidence` must be justified — high confidence (≥0.85) requires strong L1 grounding.

### §2.2 — Contradiction proposal batches

Propose new contradictions in **2 batches of 6–7 each** (targeting ≥ 12 new contradictions
to reach 20 total from the v1_0 baseline of 8).

**Contradiction class targets for v1_1 (all 4 must have ≥ 5):**
- `signal_polarity_conflict` — two MSR signals with the same planetary trigger predicting opposite outcomes
- `system_divergence` — Parashari vs Jaimini vs KP vs Tajika systems giving different readings on same planet/house
- `temporal_paradox` — a signal active in one dasha period seeming to contradict outcomes from a different period
- `frame_conflict` — a signal's meaning in one domain (e.g., Saturn delay in relationships) conflicting with its meaning in another domain (Saturn discipline in career)

Check v1_0 class distribution: likely 3-4 are signal_polarity_conflict. Prioritize underrepresented classes.

**Schema template for each new contradiction:**
```json
{
  "contradiction_id": "CON.009",
  "contradiction_class": "system_divergence",
  "hypothesis_text": "<specific claim that X and Y are in contradiction>",
  "mechanism": "<why these signals/systems produce opposite predictions for the same phenomenon>",
  "domains_implicated": ["domain_a", "domain_b"],
  "signals_in_conflict": ["SIG.MSR.XXX", "SIG.MSR.YYY"],
  "l1_references": ["FORENSIC §N", "FORENSIC §M"],
  "claude_severity_prior": "medium",
  "resolution_options": [
    "resolution_1: <how to adjudicate — e.g., prioritize Parashari over KP for natal events>",
    "resolution_2: <alternative adjudication — e.g., use dasha lord as tiebreaker>"
  ],
  "gemini_verdict": null,
  "gemini_rationale": null,
  "dr_entry_id": null,
  "ledger_event_ids": [],
  "pass_1_actor": "claude",
  "created_at": "2026-04-30",
  "created_by_session": "KARN-W5-R3-RES-CON-EXPANSION"
}
```

**Priority contradiction territory (prioritise these themes, not exhaustively):**
- Saturn AK delays vs Saturn AmK enables: same planet as both soul-purpose anchor and career enabler — how does delay function against ambition?
- Ketu 8H exaltation (moksha, detachment) vs. Mars 7H Lagna lord (drive, assertion): same chart, divergent motivational vectors
- Mercury 5H (intellect, children, speculation) vs. Mercury Atmakaraka being Saturn (soul weight) — is Mercury the vehicle or Saturn?
- Jupiter 9H own sign (dharma abundance) vs. Jupiter as 11H lord (gains, networks) — expansion toward what?
- Rahu 2H speech (amplified, destabilized family speech) vs. Rahu as ambition amplifier — does Rahu serve wealth or destabilize it?
- System divergence: Vimshottari MD sequence vs. Chara Dasha MD sequence for the same life period
- Temporal paradox: a signal activated in Mercury MD but retroactive to Saturn MD events

**Quality bar for contradictions:**
- `hypothesis_text` must name both sides of the conflict specifically, not vaguely.
- `signals_in_conflict` must be real MSR signal IDs — validate each.
- `resolution_options` must offer ≥ 2 distinct resolution frameworks (not just "consult the native").
- `claude_severity_prior` is your assessment: 'low' (interesting curiosity), 'medium' (real interpretive risk), 'high' (meaningful prediction divergence), 'critical' (could produce systematically wrong outputs if unresolved).

---

## §3 — Two-pass protocol

### §3.1 — Pass 1 (Proposal)

Work through resonances first, then contradictions.

For each batch:
1. Write raw proposals as structured prose (not yet JSON) in a response artifact:
   `035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass1.md`
   `035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass1.md`

2. Save the artifact file before moving to Pass 2.

### §3.2 — Pass 2 (Review + Reconciliation)

For each proposed item, check:
- **Signal ID validity:** Does SIG.MSR.XXX exist in MSR_v3_0.md? If not, find the correct ID or remove the citation.
- **Non-duplication:** Is this substantially the same as an existing v1_0 entry? If yes, reject or merge.
- **Schema completeness:** All required fields present and non-null (except nullable fields).
- **Confidence calibration:** Is the confidence score justified by the mechanism strength?
- **Falsifiability:** Is the claim specific enough to be tested against LEL events or future dasha windows?
- **For contradictions:** Are resolution_options genuinely distinct approaches?

Record Pass 2 decisions in:
`035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass2.md`
`035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass2.md`

Format per item: `RES.0XX: ACCEPTED | REVISED | REJECTED — [reason]`

### §3.3 — Construct v1_1 files

v1_1 = v1_0 entries (carry forward all 12 resonances + 8 contradictions, unchanged) +
       all Pass 2 ACCEPTED or REVISED items.

Update IDs sequentially: new resonances start at RES.013, new contradictions at CON.009.

**v1_1 top-level schema for resonances:**
```json
{
  "schema": "resonance_register_v1",
  "version": "1.1",
  "produced_by_session": "KARN-W5-R3-RES-CON-EXPANSION",
  "produced_at": "2026-04-30",
  "supersedes": "RESONANCE_REGISTER_v1_0",
  "resonances": [ ... ]
}
```

**v1_1 top-level schema for contradictions:**
```json
{
  "schema": "contradiction_register_v1",
  "version": "1.1",
  "produced_by_session": "KARN-W5-R3-RES-CON-EXPANSION",
  "produced_at": "2026-04-30",
  "supersedes": "CONTRADICTION_REGISTER_v1_0",
  "contradictions": [ ... ]
}
```

### §3.4 — Markdown companions

Create `.md` companion files for both v1_1 registers. Format:

```markdown
---
register_id: RESONANCE_REGISTER
version: 1.1
status: CURRENT
...
---

# Resonance Register v1.1

| ID | Domains | Confidence | Forward-Looking | Claim (truncated) |
|---|---|---|---|---|
| RES.001 | career × spiritual | 0.90 | N | Saturn AK/AmK ... |
...

## Full entries (by ID)

### RES.001 ...
[full detail]
```

---

### §3.5 — Update INDEX.json

In `035_DISCOVERY_LAYER/REGISTERS/INDEX.json`, update the resonance and contradiction entries:
- `current_version` → `RESONANCE_REGISTER_v1_1` / `CONTRADICTION_REGISTER_v1_1`
- `current_path` → updated paths
- `status` → `CURRENT`
- `supersedes` → the v1_0 entries

### §3.6 — Append two_pass_events.jsonl

For each accepted resonance and contradiction, append an event to
`06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl` per the existing format:

```json
{"event_id": "EVT.RES.013", "event_type": "resonance_proposal", "item_id": "RES.013", "pass_1_actor": "claude", "pass_2_actor": "claude", "outcome": "ACCEPTED", "session": "KARN-W5-R3-RES-CON-EXPANSION", "created_at": "2026-04-30"}
{"event_id": "EVT.CON.009", "event_type": "contradiction_proposal", "item_id": "CON.009", "pass_1_actor": "claude", "pass_2_actor": "claude", "outcome": "ACCEPTED", "session": "KARN-W5-R3-RES-CON-EXPANSION", "created_at": "2026-04-30"}
```

### §3.7 — Mark v1_0 files as SUPERSEDED

In `RESONANCE_REGISTER_v1_0.json` and `CONTRADICTION_REGISTER_v1_0.json`, add or update:
`"status": "SUPERSEDED"` in the top-level object.
Same for corresponding `.md` files — add `status: SUPERSEDED` to frontmatter.

---

## §4 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — Resonances: ≥ 24 in v1_1
```bash
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json'))
print('Count:', len(r['resonances']))
"
```
Returns ≥ 24.

### AC.3 — Contradictions: ≥ 20 in v1_1
```bash
python3 -c "
import json
c = json.load(open('035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json'))
print('Count:', len(c['contradictions']))
classes = {}
for x in c['contradictions']:
    classes[x['contradiction_class']] = classes.get(x['contradiction_class'], 0) + 1
print('Classes:', classes)
"
```
Returns ≥ 20 total. All 4 contradiction classes have ≥ 5 each.

### AC.4 — Domain-pair coverage: ≥ 24 pairs
```bash
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json'))
pairs = set()
for x in r['resonances']:
    db = x['domains_bridged']
    if len(db) >= 2:
        pairs.add(tuple(sorted(db[:2])))
    elif len(db) == 1:
        pairs.add((db[0], db[0]))
print('Covered pairs:', len(pairs))
print('Pairs:', sorted(pairs))
"
```
Returns ≥ 24 unique domain pairs.

### AC.5 — Forward-looking resonances: ≥ 8
```bash
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json'))
fwd = [x for x in r['resonances'] if x.get('is_forward_looking')]
print('Forward-looking:', len(fwd))
"
```
Returns ≥ 8.

### AC.6 — Signal IDs validated
All `signals_referenced` in resonances and `signals_in_conflict` in contradictions are
real MSR signal IDs. Verify by spot-checking ≥ 5 citations against MSR_v3_0.md source.

### AC.7 — Two-pass artifacts saved
```bash
ls 035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass1.md
ls 035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass2.md
ls 035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass1.md
ls 035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass2.md
```
All 4 files exist.

### AC.8 — v1_0 files marked SUPERSEDED
```bash
python3 -c "
import json
r = json.load(open('035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json'))
c = json.load(open('035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json'))
print('Resonance v1_0 status:', r.get('status'))
print('Contradiction v1_0 status:', c.get('status'))
"
```
Both return `SUPERSEDED`.

### AC.9 — INDEX.json updated
```bash
python3 -c "
import json
idx = json.load(open('035_DISCOVERY_LAYER/REGISTERS/INDEX.json'))
for e in idx.get('entries', []):
    if 'RESONANCE' in e.get('register_id','') or 'CONTRADICTION' in e.get('register_id',''):
        print(e['register_id'], '→', e.get('current_version'), e.get('status'))
"
```
Both registers show v1_1 as current version.

### AC.10 — Companion markdown files exist
```bash
ls 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.md
ls 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.md
```
Both exist and are non-empty.

### AC.11 — two_pass_events.jsonl appended
```bash
grep -c "KARN-W5-R3" 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl
```
Returns ≥ 12 (new events from this session).

### AC.12 — JSON files are valid
```bash
python3 -m json.tool 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json > /dev/null && echo "valid"
python3 -m json.tool 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json > /dev/null && echo "valid"
```
Both return `valid` (no JSON parse errors).

---

## §5 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **Signal ID validation fails repeatedly:** If > 20% of proposed signal IDs don't exist
   in MSR_v3_0.md, HALT. This means the signal ID format or file structure is different
   than expected — investigate before proposing more items.
3. **Two-pass disagreement unresolvable:** If a proposed item has fundamental internal
   contradictions that cannot be resolved within this session (e.g., a resonance whose
   mechanism directly contradicts an L1 fact), mark it REJECTED and document. Do not include
   rejected items in v1_1. If more than 30% of proposals are rejected, HALT and report.
4. **v1_1 JSON would fail schema validation:** If any required field is missing from a
   finalized item, fix before committing.

Non-halting: slightly fewer than targeted items (e.g., 22 resonances instead of 24) —
document the shortfall and note which domain pairs remain uncovered; continue to commit.
The ≥ targets are minimums, not absolute requirements for the session to claim COMPLETE.
A shortfall of ≤2 on resonances or ≤2 on contradictions is acceptable if documented.

---

## §6 — Closing summary template

```
SESSION CLOSE — M2_B5_RES_CON_EXPANSION — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — resonances ≥24 in v1_1 (actual: <N>)
  AC.3:  <PASS|FAIL> — contradictions ≥20, all 4 classes ≥5 (actual: <N>)
  AC.4:  <PASS|FAIL> — domain-pair coverage ≥24 (actual: <N>)
  AC.5:  <PASS|FAIL> — forward-looking resonances ≥8 (actual: <N>)
  AC.6:  <PASS|FAIL> — signal IDs validated (spot-check)
  AC.7:  <PASS|FAIL> — two-pass artifacts saved (4 files)
  AC.8:  <PASS|FAIL> — v1_0 files marked SUPERSEDED
  AC.9:  <PASS|FAIL> — INDEX.json updated
  AC.10: <PASS|FAIL> — companion markdown files exist
  AC.11: <PASS|FAIL> — two_pass_events.jsonl appended (≥12 events)
  AC.12: <PASS|FAIL> — JSON files valid

Files created/modified:
  035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.json (CREATE — <N> resonances)
  035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_1.md (CREATE)
  035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json (MODIFY — status→SUPERSEDED)
  035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.md (MODIFY — status→SUPERSEDED)
  035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.json (CREATE — <N> contradictions)
  035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_1.md (CREATE)
  035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json (MODIFY — status→SUPERSEDED)
  035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.md (MODIFY — status→SUPERSEDED)
  035_DISCOVERY_LAYER/REGISTERS/INDEX.json (MODIFY — both registers → v1_1)
  035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass1.md (CREATE)
  035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_resonance_pass2.md (CREATE)
  035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass1.md (CREATE)
  035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_contradiction_pass2.md (CREATE)
  06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl (MODIFY — +<N> events)

DB changes: None — discovery session; no migrations, no deploys.
Cloud Run: None.
Tests: None — JSON output only.

Pass 1 → Pass 2 outcomes:
  Resonances proposed: <N>
  Resonances accepted: <N>
  Resonances revised: <N>
  Resonances rejected: <N>
  Contradictions proposed: <N>
  Contradictions accepted: <N>
  Contradictions revised: <N>
  Contradictions rejected: <N>
  Unresolvable two-pass disagreements: <none | description>

Domain pairs newly covered (by this session):
  <list of domain-pair tuples added in v1_1>

Contradiction class distribution in v1_1:
  signal_polarity_conflict: <N>
  system_divergence: <N>
  temporal_paradox: <N>
  frame_conflict: <N>

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next pointer: Wave 5 close pending (W5-R1 TEMPORAL-EXTENSION and W5-R2 D234-BUNDLE
  status determines wave readiness).
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_B5_RES_CON_EXPANSION v1.0 (authored 2026-04-30 — Wave 4 close).*
