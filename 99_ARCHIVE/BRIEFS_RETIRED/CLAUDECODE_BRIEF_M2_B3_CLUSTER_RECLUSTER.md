---
brief_id: M2_B3_CLUSTER_RECLUSTER
karn_session_name: KARN-W3-R2-CLUSTER-RECLUSTER
wave: 3
stream: C
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution + native arbitration as needed (discovery session)
session_type: corpus expansion (Gemini-led discovery; Claude reviews and reconciles)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none
  blocks: M2_D7 (per-tool planner cluster_atlas planning leverages new clusters), F2 (eval harness benefits from broader coverage)
parallel_stream_note: |
  Three other Wave-1 briefs run concurrently. This brief operates entirely
  in JSON-output land (035_DISCOVERY_LAYER/REGISTERS/) and never touches
  source code or migrations. Disjoint scope.
estimated_time: 1 day discovery session (multiple Gemini batches + Claude reviews)

scope_summary: |
  Re-cluster MSR signals to achieve ≥80% coverage. Currently 12 clusters
  house 170 of 499 signals (34%). Target: 25–35 clusters housing ≥400
  signals (≥80% coverage), with every domain represented by ≥2 clusters
  and every planet centered in ≥1 cluster.

  Two-pass protocol per existing convention:
    Pass 1 (Gemini): propose new clusters using MSR signals as input.
    Pass 2 (Claude): review proposal, surface contradictions, reconcile.
    Native arbitrates ONLY if pass-2 disagreement can't be resolved.

  Output: 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json + .md.
  v1_0 is preserved (status: SUPERSEDED).

may_touch:
  - 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json             # CREATE (new version)
  - 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.md               # CREATE (mirror)
  - 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json             # ONLY to update frontmatter status: SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.md               # ONLY to update frontmatter status: SUPERSEDED
  - 035_DISCOVERY_LAYER/REGISTERS/INDEX.json                          # update to point at v1_1
  - 035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_cluster_recluster_*.md  # CREATE batch responses
  - 035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_cluster_recluster_pass2.md  # CREATE
  - 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl                    # APPEND ledger entries
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B3_CLUSTER_RECLUSTER.md  # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_B3_VERIFICATION_<DATE>.txt              # CREATE summary

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                       # UI/UX
  - All other CLAUDECODE_BRIEF_M2_*.md (other Wave-1 briefs)
  - 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_*                 # M2_B4 scope
  - 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_*               # M2_B5 scope
  - 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_*           # M2_B5 scope
  - platform/**                                                      # ALL code off-limits
  - 025_HOLISTIC_SYNTHESIS/**                                        # source-of-truth read-only
  - platform/migrations/**                                           # NO migrations
  - 01_FACTS_LAYER/**                                                # source-of-truth

acceptance_criteria:
  AC.1: |
    CLUSTER_ATLAS_v1_1.json contains 25–35 cluster entries.
    Each entry has: cluster_id, cluster_label, dominant_domain, sub_domains[],
    signal_ids[], chunk_ids[], centroid_method, cluster_size_n, pass_1_actor,
    confidence, significance, annotation, ledger_event_ids[], created_at, created_by_session.
  AC.2: |
    Σ cluster_size_n across all clusters ≥ 400 (≥80% MSR signal coverage).
  AC.3: |
    Every domain in {career, finance, psychology, health, relationships, spiritual, children, parents, travel}
    has ≥ 2 clusters with that domain as dominant_domain or sub_domain.
  AC.4: |
    Every planet in {sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu}
    is centered (named in cluster_label or signal_ids signature) in ≥ 1 cluster.
  AC.5: |
    Two-pass protocol followed:
    - Gemini batch responses committed to 035_DISCOVERY_LAYER/PROMPTS/gemini/responses/
    - Claude pass-2 review committed to 035_DISCOVERY_LAYER/PROMPTS/claude/responses/
    - Reconciliation documented in the .md mirror file
    - Each cluster has pass_1_actor=gemini-web-<date>; ledger_event_ids reference two_pass_events.jsonl entries
  AC.6: |
    06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl appended with one event per cluster.
    Each event: { event_id, event_type='cluster_proposal', actor, cluster_id, accepted_at, gemini_response_ref, claude_response_ref }
  AC.7: |
    CLUSTER_ATLAS_v1_0.json + .md updated only in their frontmatter to status: SUPERSEDED with successor: CLUSTER_ATLAS_v1_1.
  AC.8: |
    INDEX.json updated to point at v1_1.
  AC.9: |
    .md mirror is rendered from .json (per V-shift1-drift validator) — they match.
  AC.10: |
    M2_B3_VERIFICATION_<DATE>.txt summarizes:
    - Pre-state (v1_0: 12 clusters, 170 signals housed, 34% coverage)
    - Post-state (v1_1: <N> clusters, <M> signals housed, <P>% coverage)
    - Per-domain cluster count
    - Per-planet cluster centering
    - Pass-1 and pass-2 actor signatures
  AC.11: |
    This brief's frontmatter `status` flipped to COMPLETE.
  AC.12: |
    git status shows ONLY: 2 new register files (json + md), the v1_0 frontmatter
    updates, INDEX.json update, prompts/responses additions, ledger append, this brief's
    status flip, and the verification txt.

halt_conditions:
  - Two-pass disagreement that pass-2 cannot reconcile (escalate to native via halt summary)
  - MSR_v3_0.md missing or signal IDs unrecognizable (data integrity issue)
  - Coverage target ≥80% cannot be reached with 25–35 clusters (cluster size or count constraint conflict)
  - Branch is not redesign/r0-foundation
  - Pre-existing uncommitted modifications to 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_*
---

# CLAUDECODE_BRIEF — M2_B3_CLUSTER_RECLUSTER (Wave 1, Stream C)

## §1 — Why this session

The current `CLUSTER_ATLAS_v1_0.json` contains 12 clusters housing 170 of the 499 MSR signals (34% coverage). 329 signals are orphaned from any cluster. The `cluster_atlas` retrieval tool consequently returns only narrow slices when queried by domain — exactly half the work the tool should be doing.

Re-clustering with broader coverage:
- Gives `cluster_atlas` retrieval a much richer return surface.
- Gives the per-tool LLM planner (M2-D.7, future wave) better cluster-id hints to choose from.
- Gives the eval harness (F2, future wave) more meaningful cluster-membership signals to score against.

This is a discovery session, not a code change. Output is JSON + markdown.

## §2 — Pre-flight self-diagnostics

### §2.1 — Branch + working tree
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"
git status --short
# HALT if any of these have uncommitted modifications:
#   035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_*
#   06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl
```

### §2.2 — Source data presence
```bash
test -f 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md || HALT "MSR source missing"
test -f 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json || HALT "v1_0 missing (no baseline to supersede)"
test -f 06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl || HALT "ledger missing"
```

### §2.3 — Existing v1_0 row count baseline
```bash
jq '.clusters | length' 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json
# Expected: 12.
```

### §2.4 — MSR signal universe
```bash
grep -c "^### SIG.MSR\." 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
# Expected: ~499.
```

## §3 — Implementation steps

### §3.1 — Read current state (orientation)

Read:
- `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json` — see existing schema + 12 clusters.
- `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — the 499 source signals you're clustering.
- `035_DISCOVERY_LAYER/PROMPTS/gemini/cluster_proposal_v1_0.md` (or whatever the cluster-proposal prompt template is — find via grep). If no prompt template exists yet for clustering, model on PATTERN_REGISTER's existing prompt.

Identify:
- The 329 signals NOT in any v1_0 cluster.
- The 9 signal_type values in MSR (yoga, convergence, dignity, etc.).
- The 9 domains (career, finance, ..., travel).

### §3.2 — Pass 1: Gemini proposal

Compose a Gemini prompt that asks for 25–35 clusters covering all 499 signals (≥80% coverage). Each cluster has:
- A coherent theme (e.g., "Saturn Dual-Karaka Career Authority", "Mercury Vargottama Intellectual Command").
- A dominant_domain.
- A sub_domains[] (1–3).
- A signal_ids[] (10–25 signals per cluster).
- A cluster_label (human-readable).
- An annotation explaining the theme.
- centroid_method: "semantic_thematic" (or whatever the convention is).

Run the Gemini prompt as multiple batches if the signal count requires it (e.g., 5 batches of ~70 signals each, then a consolidation pass). Save each batch response to `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<DATE>_cluster_recluster_batch<N>_raw.md`.

### §3.3 — Pass 2: Claude review + reconciliation

For each Gemini-proposed cluster:
- Verify all signal_ids[] reference real MSR signals (cross-check against MSR_v3_0.md).
- Verify dominant_domain matches the majority of signals' domains_affected.
- Surface inconsistencies: signals that appear in multiple clusters with different theme assignments — decide which cluster owns each.
- Verify the 25–35 clusters together cover ≥400 unique signals.
- Flag any cluster with < 5 signals as too narrow (potentially merge).
- Flag any cluster with > 30 signals as too broad (potentially split).

If a Gemini proposal has a structural error (e.g., signal_id doesn't exist), reconcile in pass 2: drop the bad ID, suggest replacement, document the fix.

If a Gemini proposal is semantically wrong (e.g., assigns a Mercury yoga signal to a Saturn-dominated cluster), reconcile in pass 2: re-assign with rationale.

If a Gemini proposal is unreconcilable (e.g., Gemini insists on a clustering Claude considers fundamentally wrong AND the disagreement cannot be resolved through factual evidence), HALT and report. Native arbitrates.

Save Claude pass-2 review to `035_DISCOVERY_LAYER/PROMPTS/claude/responses/<DATE>_cluster_recluster_pass2.md`.

### §3.4 — Compose CLUSTER_ATLAS_v1_1.json

Build the new register. Top-level structure:

```json
{
  "schema_version": "1.0",
  "register_id": "CLUSTER_ATLAS_v1_1",
  "supersedes": "CLUSTER_ATLAS_v1_0",
  "created_at": "<ISO>",
  "created_by_session": "M2_B3_CLUSTER_RECLUSTER",
  "msr_source_version": "MSR_v3_0",
  "total_signals_in_msr": 499,
  "total_signals_clustered": <N>,
  "coverage_percent": <P>,
  "clusters": [
    {
      "cluster_id": "CLUS.001",
      "cluster_label": "Saturn Dual-Karaka Career Authority",
      "dominant_domain": "career",
      "sub_domains": ["wealth", "spiritual"],
      "signal_ids": ["SIG.MSR.018", "SIG.MSR.019", ...],
      "chunk_ids": [],
      "centroid_method": "semantic_thematic",
      "cluster_size_n": 18,
      "pass_1_actor": "gemini-web-2026-04-29",
      "pass_2_actor": "claude-cowork-2026-04-29",
      "confidence": 0.86,
      "significance": 0.82,
      "annotation": "...",
      "ledger_event_ids": ["EVT.CLUS.001"],
      "created_at": "<ISO>"
    },
    ...
  ]
}
```

Renumber clusters CLUS.001 through CLUS.0NN sequentially. Preserve old cluster_ids in the annotation if a v1_1 cluster directly inherits a v1_0 cluster's content.

### §3.5 — Compose CLUSTER_ATLAS_v1_1.md (mirror)

Render the JSON into markdown with frontmatter:
```yaml
---
canonical_id: CLUSTER_ATLAS_v1_1
status: CURRENT
supersedes: CLUSTER_ATLAS_v1_0
created_at: <ISO>
register_summary:
  total_clusters: <N>
  signals_covered: <M>
  coverage_percent: <P>
  per_domain_count: { career: <c>, finance: <f>, ... }
  per_planet_centered: { sun: <s>, ... }
---
```

Body: per-cluster section with cluster_label as H2, full annotation, signal IDs as a list. The mirror enforcer (V-shift1-drift) will validate that .md is rendered from .json.

### §3.6 — Update v1_0 frontmatter to SUPERSEDED

Edit `CLUSTER_ATLAS_v1_0.json`:
- frontmatter: `status: SUPERSEDED`
- frontmatter: `successor: CLUSTER_ATLAS_v1_1`
- frontmatter: `superseded_at: <ISO>`

Same for `CLUSTER_ATLAS_v1_0.md`. Do NOT modify the content of v1_0 — it stays as a historical record.

### §3.7 — Update INDEX.json

Edit `035_DISCOVERY_LAYER/REGISTERS/INDEX.json`:
- Update the cluster_atlas entry to point at v1_1.
- Preserve a `previous_versions: [v1_0]` field for audit trail.

### §3.8 — Append to ledger

Append to `06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl` — one JSONL line per cluster:

```jsonl
{"event_id":"EVT.CLUS.001","event_type":"cluster_proposal","cluster_id":"CLUS.001","actor":"gemini-web-2026-04-29","claude_review":"claude-cowork-2026-04-29","accepted_at":"<ISO>","gemini_response_ref":"035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-29_cluster_recluster_batch1_raw.md","claude_response_ref":"035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-29_cluster_recluster_pass2.md","accepted_by_session":"M2_B3_CLUSTER_RECLUSTER"}
```

One line per cluster.

### §3.9 — Verification

Compute aggregate metrics:

```bash
TOTAL=$(jq '[.clusters[].signal_ids[]] | unique | length' 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json)
COVERAGE=$(echo "scale=1; $TOTAL * 100 / 499" | bc)
N_CLUSTERS=$(jq '.clusters | length' 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json)
PER_DOMAIN=$(jq '[.clusters | group_by(.dominant_domain) | map({domain: .[0].dominant_domain, count: length})]' 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json)

# Halt if:
# TOTAL < 400 OR COVERAGE < 80 OR N_CLUSTERS < 25 OR N_CLUSTERS > 35
# any domain count < 2 (per AC.3)
```

Capture all metrics + the per-domain table to `00_ARCHITECTURE/BRIEFS/M2_B3_VERIFICATION_<DATE>.txt`.

### §3.10 — Closing summary + status flip

Print closing summary per execution plan §3.4. Flip brief status to COMPLETE.

## §4 — Hard constraints

- **JSON + markdown outputs only.** No code edits, no migrations, no deploys.
- **v1_0 is preserved.** Only its frontmatter status is updated.
- **Two-pass discipline.** Every cluster has a documented pass_1 + pass_2 + ledger entry.
- **Coverage ≥ 80% of MSR signals.** Hard floor.
- **HALT on unreconcilable disagreement.** Native arbitrates.

## §5 — Closing checklist

- [ ] Pre-flight §2.1–§2.4 PASS
- [ ] v1_1.json has 25–35 clusters
- [ ] Σ cluster_size_n ≥ 400
- [ ] Coverage ≥ 80%
- [ ] Every domain has ≥ 2 clusters
- [ ] Every planet centered ≥ 1 cluster
- [ ] Two-pass artifacts in PROMPTS/gemini and PROMPTS/claude
- [ ] Ledger appended with one event per cluster
- [ ] v1_0 frontmatter SUPERSEDED
- [ ] INDEX.json updated
- [ ] M2_B3_VERIFICATION_<DATE>.txt has metrics
- [ ] git status shows only expected files
- [ ] Brief status COMPLETE

---

*End of M2_B3_CLUSTER_RECLUSTER. Status: PENDING.*

## Kickoff prompt

```
You are running KARN-W3-R2-CLUSTER-RECLUSTER.

Read 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B3_CLUSTER_RECLUSTER.md
as the governing scope. Branch is redesign/r0-foundation. Do NOT read
CLAUDECODE_BRIEF.md at the project root — UI/UX stream owns it.

This session is part of Project KARN. For cross-session context:
- 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (operating rules)
- 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (history)
- 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §3 (autonomous brief contract)

This is a discovery session: re-cluster MSR_v3_0 signals into 25–35
clusters with ≥80% coverage. Two-pass protocol (Gemini propose, Claude
review + reconcile). Output is JSON + markdown only — no code edits, no
migrations, no deploys. Halt only on unreconcilable two-pass disagreement
or on conditions in halt_conditions. Otherwise complete fully.

At session close, append a standardized closing entry to
PROJECT_KARN_SESSION_LOG.md per the protocol §2 entry format. Use
karn_session_name = KARN-W3-R2-CLUSTER-RECLUSTER.
```
