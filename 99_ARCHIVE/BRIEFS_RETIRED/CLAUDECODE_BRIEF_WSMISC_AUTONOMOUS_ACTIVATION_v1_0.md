---
artifact: CLAUDECODE_BRIEF_WSMISC_AUTONOMOUS_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WSMISC_AUTONOMOUS_ACTIVATION
version: 1.0
status: READY_FOR_EXECUTION (parallel to WS-1/WS-2/WS-3; no overlap with their file trees)
project_codename: Brahma — Misc Cleanup (GCS Purge + CAPABILITY_MANIFEST Re-base + Migration Squash)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code in Antigravity — Conductor mode
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + AUTONOMOUS_MODE
predecessor: tag `legacy-cleanup-arc-complete` (ccc66c77)
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMisc
branch: feature/wsmisc-cleanup
no_backup: true  # GCS purge is forward-only per native directive
human_gates: NONE
---

# WS-Misc Autonomous Activation — Cleanup Tail

Three deferred-cleanup items from `BRAHMA_DEFERRED_FEATURES.md` + WS-0C §8 + WS-0C-2. Run as one Conductor session in parallel with the three waves; zero file overlap (GCS bucket contents, JSON manifest, archived migrations). Migration squash runs LAST and depends on WS-2 having stabilized the schema.

## §1 Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../MadhavMisc -b feature/wsmisc-cleanup legacy-cleanup-arc-complete
cd MadhavMisc
mkdir -p 00_ARCHITECTURE/CONDUCTOR/wsmisc
```

## §2 Conductor queue

```yaml
# 00_ARCHITECTURE/CONDUCTOR/wsmisc/session_queue.yaml
wave: wsmisc
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMisc
branch: feature/wsmisc-cleanup
mode: AUTONOMOUS_MODE
max_run_budget_usd: 1500
max_spend_per_asset_usd: 300

sessions:
  - id: gcs-purge
    role: Śilpī + Pramāṇa
    scope: |
      Per WS-0 §8 #1 — purge legacy contents of GCS buckets that the cleanup arc
      deliberately deferred:
      - madhav-marsys-build-artifacts: legacy JSONL artifacts under l25/, rag/, msr/,
        chart_facts/, classical/, panchanga_daily/, build_manifests/ prefixes.
        KEEP under: brahmagyan/, ganita/, bodha/, kala/, phala/, mimamsa/, current builds/.
      - chart-attachments + chart-documents: scan for orphaned objects belonging to
        deleted charts (chart_id not in `charts` table).

      Method:
        1. gsutil ls + classify each prefix as KEEP / DELETE / UNCLASSIFIED per the allowlist
        2. DRY-RUN: print the delete candidate list; HALT pause for native review
        3. Native confirms via Smṛti escalation OR auto-resume if zero UNCLASSIFIED
        4. Execute deletes; verify allowlist-only remains
    acceptance: |
      Per-bucket allowlist sweep returns zero strays; orphan objects gone; KEEP prefixes
      untouched by row count + timestamp diff vs pre-purge snapshot.
    notes: |
      Should run BEFORE WS-2's L0 ephemeris / L1 ganita writers start writing to these
      buckets so the bucket state is clean when the deterministic writers run.

  - id: capability-manifest-rebase
    role: Racayitā + Śilpī + Pramāṇa + Cowork adversarial review
    scope: |
      Per WS-0 §8 #2 — re-base 00_ARCHITECTURE/CAPABILITY_MANIFEST.json off the legacy
      A1–A22 + META DAG and onto the L0–L5 + new-assets set from MASTER_ARCHITECTURE v2.1.
      Each manifest entry maps to one asset/unit in the new world (Brahma layer prefix +
      asset name + canonical-path + retrieval tools + channels + status).
      Migrate every entry; drop entries that map to nothing in v2.1.
    acceptance: |
      Validator passes (drift_detector reads the new manifest cleanly); every entry has a
      live canonical-path; zero references to deleted A1–A22 codenames in non-archive files.
    notes: |
      Touches 00_ARCHITECTURE/CAPABILITY_MANIFEST.json — usually `must_not_touch` in other
      waves; whitelisted explicitly here as the asset is the work product.

  - id: migration-squash
    depends_on: [ws2-tag:ws2-depth-build-complete]
    role: Śilpī + Pramāṇa + Cowork adversarial review
    scope: |
      Per WS-0 §8 #3 — once WS-2 stabilizes the schema, snapshot the live schema and squash
      historical migrations under platform/supabase/migrations/0*.sql into a single
      0001_brahma_baseline.sql (or a small Brahma-era set).
      Method:
        1. pg_dump --schema-only against prod → reference schema
        2. Author 0001_brahma_baseline.sql that creates the live schema from scratch
        3. Spin up an empty Postgres in CI, apply 0001 to it, diff against the live
           schema → zero structural diffs
        4. Archive the original migrations to platform/supabase/migrations/_archive/
        5. Update the migration tracker (insert a "squashed" sentinel)
    acceptance: |
      Empty DB + 0001_brahma_baseline.sql → schema bit-identical to live prod.
      Migration tracker has the squashed sentinel + 0001 recorded.
      All existing tests that run against an empty DB still pass with the squashed baseline.
    notes: |
      LAST in the queue — depends on WS-2 closing so the schema is stable. If WS-2 churns
      late additions, the squash runs after that churn settles.

  - id: wave-close
    depends_on: [migration-squash]
    role: Sūtradhāra
    scope: tag `wsmisc-cleanup-complete`; close the wave.
```

## §3 Hard stops — none synchronous

The wave runs to completion without native intervention. All exceptional events route through `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`. Notable per-WS-Misc routings:

- **gcs-purge DRY-RUN UNCLASSIFIED prefix** → Tier-2 disposition classifier (§B.2) decides per prefix; confidence < 0.6 → STUB (keep the prefix; flag in Smṛti for future decision); never deletes blindly.
- **capability-manifest-rebase orphan entry** (no v2.1 successor) → Tier-2 classifier defaults to remove + log to BRAHMA_DEFERRED_FEATURES.md; reversible via manifest edit if needed.
- **migration-squash schema diff non-empty** → Tier-2 deep-fix escalation (§B.1): regenerate the baseline migration with the diff incorporated; re-test against empty DB; max 6 attempts before parking the squash session (the wave's other two sessions stand committed regardless).
- **Wave hits absolute $1.5k ceiling** → Tier-3 (only event): async notification per pattern §E.

## §4 Acceptance criteria

- AC-1: GCS bucket contents conform to the Brahma allowlist; orphan objects gone
- AC-2: CAPABILITY_MANIFEST.json validates cleanly; zero references to A1–A22 in non-archive code/docs
- AC-3: Migration squash diff-clean against live prod schema
- AC-4: Tag `wsmisc-cleanup-complete` pushed

## §5 Out of WS-Misc scope

- Anything in the three main waves' file trees (no overlap by design)
- Any Brahma data writes — this wave only deletes / re-bases / squashes; no new data
- Cloud SQL instance changes (right-sizing, HA, etc.) — separate infra work, not legacy cleanup

---

*End of WS-Misc Autonomous Activation. GCS purge → manifest re-base → migration squash (after WS-2). Smallest of the four waves; runs to completion in parallel.*
