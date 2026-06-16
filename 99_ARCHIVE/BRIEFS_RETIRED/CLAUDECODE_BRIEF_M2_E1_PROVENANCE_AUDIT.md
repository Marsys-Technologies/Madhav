---
brief_id: M2_E1_PROVENANCE_AUDIT
karn_session_name: KARN-W6-R3-PROVENANCE-AUDIT
wave: 6
stream: F
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 6 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: audit (3 read-only provenance audits + 1 advisory embedding check; no DB mutations)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F1
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W2-R1-MSR-ETL (A2 — msr_signals columns + re-ingest),
    KARN-W2-R2-CHART-FACTS-ETL (A3 — chart_facts 795-row baseline),
    KARN-W4-R1-A-MINOR (A5 — Vimshottari/pada/chalit) — all COMPLETE.
  blocks: KARN-W7-R1-EVAL-HARNESS (eval harness cannot score retrieval quality without
          knowing provenance coverage; audit results are the baseline)
parallel_stream_note: |
  Two other Wave-6 briefs run concurrently:
  - KARN-W6-R1-COMPOSITION-RULES (Stream D — TypeScript only; zero overlap)
  - KARN-W6-R2-PER-TOOL-PLANNER (Stream D — TypeScript only; zero overlap)
  W6-R3 is FULLY READ-ONLY. It creates audit scripts and output markdown.
  It does NOT modify source documents, DB rows, or rag_chunks. No deploy required.
estimated_time: 1 day single Claude Code session

carry_forward_notes:
  - "MSR v3_0 has 499 signals (target from execution plan) + 1 introduction section = 500
     entries in the file. Grep confirms 498 occurrences of 'v6_ids_consumed' — indicating
     ~99.6% coverage already (2 signals may lack the field). Audit 1 target is ≥95%.
     Expect a PASS finding but confirm by enumerating signals without the field."
  - "UCN v4_0 has 57 MSR signal citations (grep count from W6 orientation).
     The audit must compute % of PARAGRAPHS citing a specific MSR signal ID (not total
     citations). The UCN is structured as narrative paragraphs — define 'paragraph' as
     any block between blank lines containing ≥ 20 words."
  - "CGM SUPPORTS edges: the l25_cgm_edges table has edge_type TEXT column and
     source_signals TEXT[] column. SUPPORTS edges are those where edge_type='SUPPORTS'
     (or similar — confirm exact value in PF.4 by inspecting the table).
     The source_signals column carries the MSR signal IDs that the edge derives from.
     Audit 3 checks what % of SUPPORTS-type edges have a non-empty source_signals array
     that maps to at least one valid MSR signal ID."
  - "Advisory check (W5 carry-forward): W5-R2-D234-BUNDLE noted that l4_remedial and
     l5_timeline chunks have NULL embedding vectors (Vertex AI not triggered in standalone
     chunker run). The provenance audit should check this status and report it. This is
     NOT a FAIL condition — it is an advisory that documents the embedding gap and confirms
     whether a full pipeline build has since populated the embeddings."
  - "Output file: 00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md (create new).
     This is the primary deliverable of the session."
  - "Audit scripts: create in platform/scripts/integrity/ (same directory pattern as
     existing governance scripts). Python or Node — use whichever is most natural for the
     data access (Python for MSR/UCN markdown parsing; Python psycopg2 for DB queries).
     Scripts should be reusable standalone tools, not one-off hacks."
  - "The brief's FAIL-but-continue policy: if any audit is below target, the audit records
     FAIL and lists the sub-target items, but does NOT halt the session close. The output
     document makes the gap visible for remediation in a future session."

scope_summary: |
  Three read-only audits that measure provenance coverage:
  1. MSR → FORENSIC: what % of MSR signals have valid v6_ids_consumed → FORENSIC fact IDs.
     Target ≥ 95%. Enumerates any signal missing or with invalid FORENSIC cross-reference.
  2. UCN → MSR: what % of UCN v4_0 narrative paragraphs cite at least one specific MSR
     signal ID. Target ≥ 90%. Lists paragraphs that cite no signal.
  3. CGM SUPPORTS → MSR: what % of SUPPORTS-type edges in l25_cgm_edges have at least
     one valid MSR signal ID in their source_signals array. Target ≥ 95%.

  Advisory check (W5 carry-forward):
  4. Embedding status: count of l4_remedial + l5_timeline rag_chunks with NULL embedding
     vectors. Report gap; do not halt.

  Deliverable: 00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md

may_touch:
  - platform/scripts/integrity/audit_msr_forensic.py    # CREATE
  - platform/scripts/integrity/audit_ucn_msr.py         # CREATE
  - platform/scripts/integrity/audit_cgm_supports.py    # CREATE
  - 00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md  # CREATE (primary deliverable)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_E1_PROVENANCE_AUDIT.md  # status flip

must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md                  # source — read-only
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md                  # source — read-only
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                  # source — read-only
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md  # source — read-only
  - platform/migrations/**
  - platform/src/**
  - platform/src/app/**
  - 03_DOMAIN_REPORTS/**
  - 04_REMEDIAL_CODEX/**
  - 05_TEMPORAL_ENGINES/**
---

# KARN-W6-R3-PROVENANCE-AUDIT — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before writing any audit scripts.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F1`.

This session performs three provenance audits and one advisory embedding check. It is
READ-ONLY for all source data and the database (no UPDATE, DELETE, or INSERT). The only
files created are audit scripts and the output results document.

**What provenance means here:** Every interpretive claim in the MARSYS-JIS corpus is
supposed to trace back to an L1 fact in FORENSIC_ASTROLOGICAL_DATA_v8_0.md. The audits
measure how well this discipline is actually maintained across three corpus layers.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean. This session creates new scripts only.

# PF.3 — Source file sizes
wc -l 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md \
       025_HOLISTIC_SYNTHESIS/UCN_v4_0.md \
       025_HOLISTIC_SYNTHESIS/CGM_v9_0.md \
       01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
# Record line counts. Large files may need chunked reading in audit scripts.

# PF.4 — CGM edge_type values in l25_cgm_edges
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT edge_type, COUNT(*) FROM l25_cgm_edges
   GROUP BY edge_type ORDER BY count DESC LIMIT 20;"
# Note exact edge_type string for SUPPORTS (it may be 'SUPPORTS', 'supports', or other).
# Also note: do SUPPORTS edges have source_signals populated?

# PF.5 — Spot-check source_signals on SUPPORTS edges
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT id, edge_type, source_signals, status
   FROM l25_cgm_edges
   WHERE edge_type = 'SUPPORTS'  -- adjust if PF.4 shows different casing
   LIMIT 5;"
# If no SUPPORTS rows exist at all → the audit runs on whatever edge_type most
# represents 'derived from MSR signal' (e.g. YOGA_MEMBERSHIP may be more relevant).
# Document in pre-flight and adjust audit_cgm_supports.py accordingly.

# PF.6 — MSR v6_ids_consumed spot-check
grep -c "v6_ids_consumed" 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
# Expected: ~498. Note exact count.
grep -c "^SIG\.MSR\." 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 2>/dev/null || \
  grep -c "^  signal_name:" 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
# This gives total signal count (expected ~499). Use as denominator for Audit 1.

# PF.7 — UCN MSR citation spot-check
grep -c "MSR\." 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
# Expected: ~57 total citation occurrences. Note count.

# PF.8 — Embedding gap check (advisory)
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT doc_type, COUNT(*) as total,
          SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as null_embeddings
   FROM rag_chunks
   WHERE doc_type IN ('l4_remedial','l5_timeline','domain_report')
   GROUP BY doc_type;"
# Record: null_embedding count per doc_type. Advisory only — not a halt condition.

# PF.9 — Confirm integrity scripts dir exists or create it
ls platform/scripts/integrity/ 2>/dev/null || echo "(directory does not exist — will create)"
# Create if needed: mkdir -p platform/scripts/integrity/

# PF.10 — Python psycopg2 available
python3 -c "import psycopg2; print('psycopg2 OK')" 2>/dev/null || echo "pip install psycopg2-binary"
```

---

## §2 — Audit 1: MSR → FORENSIC traceability

**Create `platform/scripts/integrity/audit_msr_forensic.py`:**

### §2.1 — What to measure

For each MSR signal (SIG.MSR.001 through SIG.MSR.499):
- Does it have a `v6_ids_consumed:` field?
- Does that field contain at least one ID that appears in FORENSIC_ASTROLOGICAL_DATA_v8_0.md?

**Valid FORENSIC IDs** are any identifier pattern in FORENSIC that MSR signals reference.
From spot-checks: `v6_ids_consumed` values use patterns like `PLN.SATURN`, `HSE.7`,
`SBL.SAT`, `D9.VENUS`, `YOG.SASHA_MPY`. These same IDs appear in the FORENSIC file.
Build the valid-ID set by extracting all `fact_id` values from the FORENSIC file OR by
treating any ID appearing in the FORENSIC file matching the pattern `[A-Z]{2,4}\.[A-Z0-9_.]+`
as valid.

### §2.2 — Script structure

```python
#!/usr/bin/env python3
"""
audit_msr_forensic.py — Audit 1: MSR → FORENSIC traceability.
Measures: % of MSR signals with valid v6_ids_consumed → FORENSIC fact IDs.
Target: ≥ 95%.

Usage: python3 platform/scripts/integrity/audit_msr_forensic.py
Output: prints results to stdout + writes to M2_PROVENANCE_AUDIT_RESULTS.md (appended by caller)

KARN-W6-R3. READ-ONLY.
"""

import re, sys, json
from pathlib import Path

ROOT = Path(__file__).parents[3]  # repo root
MSR_PATH = ROOT / "025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
FORENSIC_PATH = ROOT / "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md"

def extract_forensic_ids(forensic_text: str) -> set[str]:
    """Extract all IDs from FORENSIC that could be referenced by MSR."""
    # Pattern: 2-5 uppercase letters, dot, alphanumeric+dots+underscores
    return set(re.findall(r'\b[A-Z]{2,5}\.[A-Z0-9_.]+', forensic_text))

def parse_msr_signals(msr_text: str) -> list[dict]:
    """
    Parse MSR v3_0.md into a list of signal dicts.
    Each dict: { id, signal_name, v6_ids_consumed: list[str] | None }
    MSR format: YAML-like blocks starting with 'SIG.MSR.NNN:'
    """
    signals = []
    # Split on signal boundaries
    # Pattern: line starting with SIG.MSR. or a line of form "SIG.MSR.NNN:"
    signal_blocks = re.split(r'\n(?=SIG\.MSR\.\d{3}:)', msr_text)
    for block in signal_blocks:
        if not block.strip().startswith('SIG.MSR.'):
            continue
        # Extract signal ID
        id_match = re.match(r'(SIG\.MSR\.\d{3}):', block)
        if not id_match:
            continue
        sig_id = id_match.group(1)
        # Extract signal_name
        name_match = re.search(r'signal_name:\s*["\']?(.+?)["\']?\s*$', block, re.MULTILINE)
        signal_name = name_match.group(1).strip() if name_match else ''
        # Extract v6_ids_consumed
        v6_match = re.search(r'v6_ids_consumed:\s*\[([^\]]*)\]', block)
        if v6_match:
            raw = v6_match.group(1)
            ids = [i.strip().strip('"\'') for i in raw.split(',') if i.strip()]
        else:
            ids = None
        signals.append({'id': sig_id, 'signal_name': signal_name, 'v6_ids_consumed': ids})
    return signals

def run_audit() -> dict:
    msr_text = MSR_PATH.read_text(encoding='utf-8')
    forensic_text = FORENSIC_PATH.read_text(encoding='utf-8')

    forensic_ids = extract_forensic_ids(forensic_text)
    signals = parse_msr_signals(msr_text)

    total = len(signals)
    missing_field = []   # signals with no v6_ids_consumed field
    invalid_refs = []    # signals with v6_ids_consumed but none map to FORENSIC
    valid = []           # signals with ≥1 valid FORENSIC ref

    for s in signals:
        if s['v6_ids_consumed'] is None:
            missing_field.append(s['id'])
        else:
            has_valid = any(ref in forensic_ids for ref in s['v6_ids_consumed'])
            if has_valid:
                valid.append(s['id'])
            else:
                invalid_refs.append({'id': s['id'], 'refs': s['v6_ids_consumed']})

    coverage_pct = (len(valid) / total * 100) if total > 0 else 0
    target_met = coverage_pct >= 95.0

    return {
        'total_signals': total,
        'valid_count': len(valid),
        'missing_field_count': len(missing_field),
        'invalid_ref_count': len(invalid_refs),
        'coverage_pct': round(coverage_pct, 2),
        'target_met': target_met,
        'missing_field_ids': missing_field[:20],   # cap to 20 for readability
        'invalid_ref_sample': invalid_refs[:10],
        'forensic_id_count': len(forensic_ids),
    }

if __name__ == '__main__':
    result = run_audit()
    status = 'PASS' if result['target_met'] else 'FAIL'
    print(f"\n=== Audit 1: MSR → FORENSIC ===")
    print(f"Status: {status}")
    print(f"Total signals: {result['total_signals']}")
    print(f"Valid coverage: {result['valid_count']} / {result['total_signals']} = {result['coverage_pct']}%")
    print(f"Target: ≥95% → {'MET' if result['target_met'] else 'NOT MET'}")
    print(f"Signals missing v6_ids_consumed: {result['missing_field_count']}")
    print(f"Signals with invalid refs: {result['invalid_ref_count']}")
    if result['missing_field_ids']:
        print(f"Missing field (first 20): {result['missing_field_ids']}")
    if result['invalid_ref_sample']:
        print(f"Invalid ref sample (first 10): {json.dumps(result['invalid_ref_sample'], indent=2)}")
    # Machine-readable result for caller
    print(f"\nJSON_RESULT: {json.dumps(result)}")
```

---

## §3 — Audit 2: UCN → MSR traceability

**Create `platform/scripts/integrity/audit_ucn_msr.py`:**

### §3.1 — What to measure

For each narrative paragraph in UCN v4_0.md (block of ≥20 words between blank lines):
- Does it cite at least one MSR signal ID? (e.g. `MSR.413`, `MSR.396`, `SIG.MSR.001`)
- Count: cited paragraphs / total paragraphs ≥ 20 words

Target: ≥ 90%.

### §3.2 — Script structure

```python
#!/usr/bin/env python3
"""
audit_ucn_msr.py — Audit 2: UCN → MSR traceability.
Measures: % of UCN v4_0 narrative paragraphs citing ≥1 MSR signal ID.
Target: ≥ 90%.

A 'paragraph' is a block of text between blank lines containing ≥ 20 words.
An MSR citation matches: MSR\.\d{3} or SIG\.MSR\.\d{3} or \bMSR\.\w+

KARN-W6-R3. READ-ONLY.
"""

import re, json
from pathlib import Path

ROOT = Path(__file__).parents[3]
UCN_PATH = ROOT / "025_HOLISTIC_SYNTHESIS/UCN_v4_0.md"

MSR_CITATION_RE = re.compile(r'\bMSR\.\d{3}\b|\bSIG\.MSR\.\d{3}\b|\bMSR\.[A-Z0-9_.]+')

def parse_ucn_paragraphs(ucn_text: str) -> list[str]:
    """Split UCN into paragraphs (blank-line-delimited blocks with ≥20 words)."""
    # Strip YAML frontmatter
    if ucn_text.startswith('---'):
        end = ucn_text.find('\n---\n', 3)
        if end > -1:
            ucn_text = ucn_text[end+5:]
    raw_blocks = re.split(r'\n\s*\n', ucn_text)
    paragraphs = []
    for block in raw_blocks:
        stripped = block.strip()
        if stripped.startswith('#'):
            continue  # skip headers
        word_count = len(stripped.split())
        if word_count >= 20:
            paragraphs.append(stripped)
    return paragraphs

def run_audit() -> dict:
    ucn_text = UCN_PATH.read_text(encoding='utf-8')
    paragraphs = parse_ucn_paragraphs(ucn_text)

    total = len(paragraphs)
    cited = []
    uncited = []

    for i, para in enumerate(paragraphs):
        citations = MSR_CITATION_RE.findall(para)
        if citations:
            cited.append({'index': i, 'citations': list(set(citations))[:5]})
        else:
            uncited.append({'index': i, 'preview': para[:100]})

    coverage_pct = (len(cited) / total * 100) if total > 0 else 0
    target_met = coverage_pct >= 90.0

    return {
        'total_paragraphs': total,
        'cited_count': len(cited),
        'uncited_count': len(uncited),
        'coverage_pct': round(coverage_pct, 2),
        'target_met': target_met,
        'uncited_sample': uncited[:10],  # first 10 uncited paragraphs
        'citation_examples': cited[:5],
    }

if __name__ == '__main__':
    result = run_audit()
    status = 'PASS' if result['target_met'] else 'FAIL'
    print(f"\n=== Audit 2: UCN → MSR ===")
    print(f"Status: {status}")
    print(f"Total paragraphs (≥20 words): {result['total_paragraphs']}")
    print(f"Paragraphs citing MSR: {result['cited_count']} / {result['total_paragraphs']} = {result['coverage_pct']}%")
    print(f"Target: ≥90% → {'MET' if result['target_met'] else 'NOT MET'}")
    if result['uncited_sample']:
        print(f"\nUncited paragraphs (first 10 previews):")
        for u in result['uncited_sample']:
            print(f"  [{u['index']}] {u['preview']}")
    print(f"\nJSON_RESULT: {json.dumps(result)}")
```

---

## §4 — Audit 3: CGM SUPPORTS → MSR traceability

**Create `platform/scripts/integrity/audit_cgm_supports.py`:**

### §4.1 — What to measure

For each edge in l25_cgm_edges where `edge_type = 'SUPPORTS'` (or equivalent — per PF.4):
- Does its `source_signals TEXT[]` column contain at least one valid MSR signal ID?
- Valid MSR ID format: `SIG.MSR.NNN` or `MSR.NNN` (3-digit).

Target: ≥ 95%.

**If PF.4 shows zero SUPPORTS edges:** Run the audit on the edge_type with the highest
count and document the substitution. Common alternative: `YOGA_MEMBERSHIP` or
`EXALT_DEBIL_AFFINITY` edges are most likely to carry MSR source traceability.

### §4.2 — Script structure

```python
#!/usr/bin/env python3
"""
audit_cgm_supports.py — Audit 3: CGM SUPPORTS → MSR traceability.
Measures: % of SUPPORTS-type edges with ≥1 valid MSR signal in source_signals.
Target: ≥ 95%.

Connects to local Postgres proxy on 127.0.0.1:5433.
DB: amjis, user: amjis-app.

KARN-W6-R3. READ-ONLY (SELECT only).
"""

import re, json, sys
import psycopg2
import psycopg2.extras
from pathlib import Path

DB_DSN = "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app"
MSR_ID_RE = re.compile(r'\bSIG\.MSR\.\d{3}\b|\bMSR\.\d{3}\b')

def run_audit(edge_type_override: str | None = None) -> dict:
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Discover edge types if needed
    cur.execute("SELECT edge_type, COUNT(*) n FROM l25_cgm_edges GROUP BY edge_type ORDER BY n DESC")
    edge_type_counts = {r['edge_type']: r['n'] for r in cur.fetchall()}

    target_edge_type = edge_type_override or 'SUPPORTS'
    if target_edge_type not in edge_type_counts:
        # Fall back to the highest-count edge_type
        target_edge_type = max(edge_type_counts, key=edge_type_counts.get)
        print(f"WARNING: 'SUPPORTS' not found in edge types. Using '{target_edge_type}' instead.")

    # Fetch all edges of target type
    cur.execute(
        "SELECT id, edge_type, source_signals, status FROM l25_cgm_edges WHERE edge_type = %s",
        (target_edge_type,)
    )
    edges = cur.fetchall()
    cur.close()
    conn.close()

    total = len(edges)
    if total == 0:
        return {
            'total_edges': 0,
            'target_edge_type': target_edge_type,
            'edge_type_counts': edge_type_counts,
            'coverage_pct': 0.0,
            'target_met': False,
            'note': 'No edges found for target edge type',
        }

    with_valid_source = []
    without_valid_source = []

    for edge in edges:
        sigs = edge['source_signals'] or []
        has_valid = any(MSR_ID_RE.search(sig) for sig in sigs) if sigs else False
        if has_valid:
            with_valid_source.append(str(edge['id']))
        else:
            without_valid_source.append({
                'id': str(edge['id']),
                'source_signals': sigs[:5],  # cap for readability
            })

    coverage_pct = (len(with_valid_source) / total * 100) if total > 0 else 0
    target_met = coverage_pct >= 95.0

    return {
        'total_edges': total,
        'target_edge_type': target_edge_type,
        'edge_type_counts': edge_type_counts,
        'with_valid_source_count': len(with_valid_source),
        'without_valid_source_count': len(without_valid_source),
        'coverage_pct': round(coverage_pct, 2),
        'target_met': target_met,
        'without_valid_source_sample': without_valid_source[:10],
    }

if __name__ == '__main__':
    override = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_audit(edge_type_override=override)
    status = 'PASS' if result['target_met'] else 'FAIL'
    print(f"\n=== Audit 3: CGM {result['target_edge_type']} → MSR ===")
    print(f"Status: {status}")
    print(f"Total {result['target_edge_type']} edges: {result['total_edges']}")
    print(f"With valid MSR source: {result.get('with_valid_source_count',0)} / {result['total_edges']} = {result['coverage_pct']}%")
    print(f"Target: ≥95% → {'MET' if result['target_met'] else 'NOT MET'}")
    if result.get('without_valid_source_sample'):
        print(f"\nEdges without valid MSR source (first 10):")
        for e in result['without_valid_source_sample']:
            print(f"  id={e['id']}  source_signals={e['source_signals']}")
    print(f"\nAll edge types in DB: {json.dumps(result['edge_type_counts'])}")
    print(f"\nJSON_RESULT: {json.dumps(result)}")
```

---

## §5 — Advisory check: embedding gap

Run the DB query from PF.8 and capture results. This is not a separate script — run inline
during the results document assembly and record:
- l4_remedial: total rows, null_embedding count
- l5_timeline: total rows, null_embedding count
- domain_report: total rows, null_embedding count (baseline; should be 0 null)

---

## §6 — Assemble results document

**Create `00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md`:**

```markdown
---
artifact: M2_PROVENANCE_AUDIT_RESULTS.md
status: CURRENT
authored_by: KARN-W6-R3-PROVENANCE-AUDIT
authored_at: <ISO timestamp>
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F1
---

# M2 Provenance Audit Results

**Produced by:** KARN-W6-R3-PROVENANCE-AUDIT  
**Branch:** redesign/r0-foundation  
**Audit date:** <ISO date>

---

## Executive summary

| Audit | Target | Result | Status |
|---|---|---|---|
| Audit 1: MSR → FORENSIC | ≥95% | X.XX% | PASS / FAIL |
| Audit 2: UCN → MSR | ≥90% | X.XX% | PASS / FAIL |
| Audit 3: CGM SUPPORTS → MSR | ≥95% | X.XX% | PASS / FAIL |
| Advisory: l4/l5 embedding gap | (advisory) | N null / M total | INFO |

**Overall corpus integrity verdict:** <PASS (all 3 audits met targets) | PARTIAL FAIL (N audits below target) | FAIL (all below target)>

---

## Audit 1: MSR → FORENSIC traceability

**Script:** `platform/scripts/integrity/audit_msr_forensic.py`

**Method:** For each of the 499 MSR signals, verify `v6_ids_consumed` field is present and contains at least one ID appearing in FORENSIC_ASTROLOGICAL_DATA_v8_0.md.

**Results:**
- Total signals: <N>
- Signals with valid FORENSIC cross-reference: <N> (<PCT>%)
- Signals missing `v6_ids_consumed` field: <N>
- Signals with field but invalid refs: <N>
- FORENSIC ID universe size: <N> unique IDs

**Status:** PASS / FAIL (target ≥95%)

**Sub-target items (if any):**
<list of signal IDs without valid FORENSIC cross-reference, or "None — all signals meet target">

---

## Audit 2: UCN → MSR traceability

**Script:** `platform/scripts/integrity/audit_ucn_msr.py`

**Method:** For each UCN v4_0 narrative paragraph (≥20 words, between blank lines), verify at least one MSR signal ID is cited. MSR citation patterns: `MSR.NNN`, `SIG.MSR.NNN`.

**Results:**
- Total qualifying paragraphs (≥20 words): <N>
- Paragraphs citing ≥1 MSR signal: <N> (<PCT>%)
- Uncited paragraphs: <N>

**Status:** PASS / FAIL (target ≥90%)

**Uncited paragraph sample (first 10 previews):**
<list or "None — all qualifying paragraphs cite MSR signals">

---

## Audit 3: CGM SUPPORTS → MSR traceability

**Script:** `platform/scripts/integrity/audit_cgm_supports.py`

**Method:** For each edge of type SUPPORTS in l25_cgm_edges, verify `source_signals` array contains ≥1 valid MSR signal ID (`SIG.MSR.NNN` or `MSR.NNN`).

**Note:** <If SUPPORTS edge type was absent and a substitute was used, document here.>

**Results:**
- Total SUPPORTS edges: <N>
- Edge type used for audit: <SUPPORTS or substitute>
- Edges with valid MSR source_signals: <N> (<PCT>%)
- Edges without valid source_signals: <N>
- All edge types in DB: <JSON from script output>

**Status:** PASS / FAIL (target ≥95%)

**Sub-target items (if any):**
<list of edge IDs without valid MSR source, or "None — all edges meet target">

---

## Advisory: Embedding gap (l4/l5 rag_chunks)

**Method:** `SELECT doc_type, COUNT(*), SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) FROM rag_chunks WHERE doc_type IN ('l4_remedial','l5_timeline','domain_report') GROUP BY doc_type`

**Results:**

| doc_type | total_chunks | null_embeddings | coverage |
|---|---|---|---|
| l4_remedial | <N> | <N> | <PCT>% |
| l5_timeline | <N> | <N> | <PCT>% |
| domain_report | <N> | <N> | <PCT>% |

**Advisory verdict:** <"Embeddings fully populated for all three types" | "l4_remedial and/or l5_timeline have NULL embeddings from standalone chunker run (W5-R2-D234-BUNDLE). Will populate on next full pipeline build. Vector search against these doc_types will return empty until embeddings land. Remediate by running full pipeline build (triggers Vertex AI embedding).">

---

## Remediation notes

<For each FAIL item: one-paragraph description of what would fix it, estimated effort, and which future session should pick it up.>

<For embedding gap: "Run full Cloud Build pipeline to trigger Vertex AI embedding for l4_remedial and l5_timeline chunks. No code change required. Estimated: 30 minutes unattended build time.">
```

---

## §7 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — Three audit scripts created
```bash
ls platform/scripts/integrity/audit_msr_forensic.py
ls platform/scripts/integrity/audit_ucn_msr.py
ls platform/scripts/integrity/audit_cgm_supports.py
```
All three exist.

### AC.3 — All three audits execute without errors
```bash
python3 platform/scripts/integrity/audit_msr_forensic.py
python3 platform/scripts/integrity/audit_ucn_msr.py
python3 platform/scripts/integrity/audit_cgm_supports.py
```
Each script completes (exit code 0 or output produced) without Python exceptions.
FAIL result (coverage below target) is acceptable — it must NOT produce an unhandled exception.

### AC.4 — Results document created
```bash
ls 00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md
```
File exists and is non-empty.

### AC.5 — Results document has all four sections
```bash
grep -c "Audit 1\|Audit 2\|Audit 3\|Advisory" \
  00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md
```
≥ 4 section headers present.

### AC.6 — Executive summary table populated with actual numbers
```bash
grep "%" 00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md | head -5
```
Shows actual percentages (not placeholder `X.XX%`).

### AC.7 — FAIL items documented (if any)
If any audit shows coverage below target: the results document lists the sub-target items
(signal IDs, paragraph previews, or edge IDs). This is a quality gate on the document,
not on the audit result itself.

### AC.8 — Source files unmodified
```bash
git diff 025_HOLISTIC_SYNTHESIS/ 01_FACTS_LAYER/
```
Empty diff. Source files are untouched.

### AC.9 — No DB mutations
```bash
# Confirm audit scripts only use SELECT
grep -n "INSERT\|UPDATE\|DELETE\|DROP\|CREATE" \
  platform/scripts/integrity/audit_msr_forensic.py \
  platform/scripts/integrity/audit_ucn_msr.py \
  platform/scripts/integrity/audit_cgm_supports.py
```
No DML statements in audit scripts.

---

## §8 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **audit_msr_forensic.py fails to parse any signals** (returns 0 signals): MSR format may
   have changed. Inspect the actual format, adjust the regex, and proceed. If unable to
   parse after 3 attempts — HALT with the format sample that's failing.
3. **psycopg2 unavailable and cannot be installed:** CGM audit cannot run. HALT with
   instructions for the native to install `psycopg2-binary` and re-run.
4. **Python exception in any audit script that cannot be caught** (unrecoverable parse
   error or DB connection failure): HALT with full traceback.

Non-halting: SUPPORTS edges absent (use substitute edge_type per §4.2); any audit FAIL
(document and continue); embedding gap (advisory only — document and continue).

---

## §9 — Closing summary template

```
SESSION CLOSE — M2_E1_PROVENANCE_AUDIT — <ISO timestamp>

Pre-flight findings:
  MSR v6_ids_consumed occurrences: <count from PF.6>
  MSR total signal count: <count from PF.6>
  UCN MSR citation count (total): <count from PF.7>
  CGM SUPPORTS edge count: <count from PF.4>
  CGM edge_type used for audit: <SUPPORTS or substitute>
  Embedding gap (l4_remedial / l5_timeline null): <N / M>

Audit results:
  Audit 1 (MSR → FORENSIC): <PASS|FAIL> — <PCT>% coverage (<N>/<N> signals)
    Sub-target count: <N>
  Audit 2 (UCN → MSR):      <PASS|FAIL> — <PCT>% coverage (<N>/<N> paragraphs)
    Uncited paragraph count: <N>
  Audit 3 (CGM SUPPORTS → MSR): <PASS|FAIL> — <PCT>% coverage (<N>/<N> edges)
    Without valid source_signals: <N>
  Advisory (embedding gap):  <"No gap" | "l4_remedial: N null; l5_timeline: N null">

ACs result:
  AC.1: <PASS|FAIL> — branch redesign/r0-foundation
  AC.2: <PASS|FAIL> — three audit scripts created
  AC.3: <PASS|FAIL> — all scripts execute without exceptions
  AC.4: <PASS|FAIL> — M2_PROVENANCE_AUDIT_RESULTS.md created
  AC.5: <PASS|FAIL> — results document has 4 sections
  AC.6: <PASS|FAIL> — actual percentages in executive summary
  AC.7: <PASS|FAIL> — FAIL items documented (or N/A if all PASS)
  AC.8: <PASS|FAIL> — source files unmodified
  AC.9: <PASS|FAIL> — no DB mutations in audit scripts

Files created:
  platform/scripts/integrity/audit_msr_forensic.py  (CREATE)
  platform/scripts/integrity/audit_ucn_msr.py       (CREATE)
  platform/scripts/integrity/audit_cgm_supports.py  (CREATE)
  00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md  (CREATE)

DB changes: NONE (SELECT queries only)
Cloud Run: NONE (no deploy)

Halt-and-report cases: <none | description>
Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: KARN-W7-R1-EVAL-HARNESS (sequential, Wave 7)
```

After emitting closing summary, append session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1,
and flip `status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_E1_PROVENANCE_AUDIT v1.0 (authored 2026-04-30 — Wave 6 open).*
