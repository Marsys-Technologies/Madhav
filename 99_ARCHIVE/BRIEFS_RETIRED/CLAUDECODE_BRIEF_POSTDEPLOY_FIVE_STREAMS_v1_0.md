---
artifact: CLAUDECODE_BRIEF_POSTDEPLOY_FIVE_STREAMS_v1_0.md
canonical_id: CLAUDECODE_BRIEF_POSTDEPLOY_FIVE_STREAMS
version: 1.0
status: READY_FOR_EXECUTION
project_codename: Brahma — Post-Deploy Five-Stream Activation
authored_by: Claude (Cowork) 2026-06-05
authored_for: Claude Code in Antigravity — Conductor mode (5 parallel)
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + AUTONOMOUS_MODE + AUTONOMY_RESILIENCE_PATTERN
predecessor: BRAHMA_FOUR_WAVE_COMPLETE (eb1a6c0f); tag `ws2-depth-build-complete` (e7b5758b)
worktrees: MadhavPostA, MadhavPostB, MadhavPostC, MadhavPostD, MadhavPostE
no_backup: true
human_gates: NONE (per AUTONOMY_RESILIENCE_PATTERN — Tier-3 catastrophic-runaway cap only)
---

# Brahma Post-Deploy — Five-Stream Autonomous Activation

The four-wave instrument is built. Eight operator actions remain (per BRAHMA_FOUR_WAVE_COMPLETE §7); they decompose into five parallel streams. One master paste kicks all five conductors. Same AUTONOMOUS_MODE + AUTONOMY_RESILIENCE_PATTERN as the four-wave launch — zero synchronous native gates fired; Tier-3 catastrophic-runaway cap ($2k absolute ceiling here — smaller than wave caps because these are bounded ops) is the only event that ever reaches the native.

## §1 Stream A — L0 Production Activation (4 sub-actions, internally serial)

Branch: `feature/postdeploy-a-l0-activation`. Worktree: `MadhavPostA`. Budget cap: $500.

### A.1 Apply L0 migrations to prod

```bash
psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 --single-transaction \
  -f platform/supabase/migrations/ws2_l0_ephemeris.sql
psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 --single-transaction \
  -f platform/supabase/migrations/ws2_l0_remedy_corpus.sql

# Verify both schemas land
psql_prod -c "\dt ephemeris_daily ephemeris_bodies brahmagyan_remedy_corpus" 2>&1 | head
```

Both migrations must apply clean. Schema verification before A.2/A.3 release.

### A.2 Ephemeris build (1980–2060 DE441) — LONG-POLE

```bash
# Invoke the Cloud Run Job that runs build_ephemeris() across the full date range × bodies
gcloud --impersonate-service-account=brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com \
  run jobs execute brahmagyan-ephemeris-build \
  --region=asia-south1 \
  --update-env-vars="START_DATE=1980-01-01,END_DATE=2060-12-31,EPHEMERIS_FILE=de441" \
  --wait

# Verify row count post-completion (target: bodies × days; ~8M rows for 9 grahas × ~30k days)
psql_prod -c "SELECT count(*) FROM ephemeris_daily;"
psql_prod -c "SELECT body, count(*) FROM ephemeris_daily GROUP BY body ORDER BY body;"
```

This is the long-running step (hours). The Cloud Run Job streams progress to Smṛti so the conductor doesn't sleep idle. AUTONOMY_RESILIENCE_PATTERN §B.4 engine self-repair applies: if the build job fails on a date range, pin the previous PyJHora version OR swap to Swiss direct path OR file upstream issue + continue on safe path.

### A.3 Remedy corpus seed (parallel with A.2)

```bash
gcloud --impersonate-service-account=brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com \
  run jobs execute brahmagyan-remedy-seed \
  --region=asia-south1 \
  --wait

# Verify
psql_prod -c "SELECT count(*) FROM brahmagyan_remedy_corpus;"
psql_prod -c "SELECT count(*) FROM rag_chunks WHERE source = 'remedy_corpus';"
```

### A.4 Verify rag_chunks total

```bash
psql_prod -c "SELECT count(*) FROM rag_chunks;"
# AC: count ≥ 4,589 (BPHS + Jaimini + KP + Tajaka + Remedy)
```

**A wave-close:** all four ACs green → tag `postdeploy-a-l0-activated`.

---

## §2 Stream B — V1.3 LEL strip (C2-002 fix)

Branch: `feature/postdeploy-b-lel-strip`. Worktree: `MadhavPostB`. Budget cap: $200.

```bash
# Locate where phala.anchors writes its notes field
grep -rEn "anchors.*notes|notes.*anchor" platform/python-sidecar/phala/ \
  --include='*.py' 2>/dev/null

# C2-002 finding: notes field contains LEL citation text like "per LEL event 2007-03-14".
# The strip is: remove any substring matching r"\bper LEL\b.*?(?:\.|$)" or similar
# event-citation patterns. The actual events stay isolated in mimamsa.lel_events;
# only the citation pattern in the public notes field needs scrubbing.
```

Author the strip function, run it across existing `phala_anchors` rows, verify the strip leaves the rest of the notes intact, commit + add a regression test.

**B wave-close:** zero rows in `phala_anchors` contain LEL citation text → tag `postdeploy-b-lel-stripped`.

---

## §3 Stream C — Empty-DB migration squash test

Branch: `feature/postdeploy-c-migration-test`. Worktree: `MadhavPostC`. Budget cap: $100.

```bash
# Auto-detect Docker availability
docker ps >/dev/null 2>&1 || {
  echo "Docker unavailable — logging deferral to Smṛti and exiting Stream C clean."
  cat > 00_ARCHITECTURE/CONDUCTOR/postdeploy-c/smriti/DOCKER_UNAVAILABLE.md <<'EOF'
Stream C deferred: Docker not available on the conductor's runner.
Re-run when Docker is present: `bash docker_available_resume.sh`.
EOF
  exit 0
}

# Docker present: spin clean Postgres, apply 0001_brahma_baseline.sql, structural diff
docker run --rm -d --name brahma-test-pg -e POSTGRES_PASSWORD=test -p 5435:5432 postgres:15
sleep 5
docker exec brahma-test-pg psql -U postgres -c "CREATE DATABASE brahma_test;"
docker exec brahma-test-pg psql -U postgres -d brahma_test \
  -f /tmp/0001_brahma_baseline.sql

# Dump test schema
docker exec brahma-test-pg pg_dump --schema-only -U postgres brahma_test > /tmp/test_schema.sql

# Dump prod schema
pg_dump --schema-only "$PROD_DB_URL" > /tmp/prod_schema.sql

# Structural diff (normalize whitespace, ignore comments)
diff <(grep -vE "^--|^$" /tmp/prod_schema.sql | sort) \
     <(grep -vE "^--|^$" /tmp/test_schema.sql | sort) \
  | tee /tmp/schema_diff.txt

# AC: diff is empty (or only contains documented acceptable variations)
docker stop brahma-test-pg
```

**C wave-close:** empty diff or documented variations → tag `postdeploy-c-migration-squash-validated` (or `postdeploy-c-deferred-docker` if Docker absent).

---

## §4 Stream D — Governance hygiene (8 drift findings)

Branch: `feature/postdeploy-d-governance-hygiene`. Worktree: `MadhavPostD`. Budget cap: $400.

Per V.1 audit item: 8 HIGH findings — 6× `fingerprint_mismatch` + 2× `phantom_reference`. All pre-existing, not WS regressions; safe to address as a single hygiene session.

### D.1 Enumerate the findings

```bash
python platform/scripts/governance/drift_detector.py 2>&1 \
  | tee /tmp/postdeploy_d_drift.txt

# Filter to HIGH severity
grep -E "HIGH.*fingerprint_mismatch|HIGH.*phantom_reference" /tmp/postdeploy_d_drift.txt \
  | tee /tmp/postdeploy_d_targets.txt
```

### D.2 Per-finding disposition

For each fingerprint_mismatch: re-hash the source file and update the manifest's stored fingerprint (assuming the source file is intentionally at its current state).

For each phantom_reference: either (a) the referenced file should exist and is missing — restore from git or recreate per spec, or (b) the reference is stale — remove from manifest.

Use the AUTONOMY_RESILIENCE_PATTERN §B.2 autonomous disposition classifier: read the finding + the referenced file's git history → decide UPDATE_FINGERPRINT / REMOVE_PHANTOM / RESTORE_FILE.

### D.3 Apply + re-verify

```bash
python platform/scripts/governance/drift_detector.py 2>&1 \
  | grep -E "HIGH" | wc -l
# AC: 0
```

**D wave-close:** zero HIGH drift findings → tag `postdeploy-d-governance-clean`.

---

## §5 Stream E — V1.3 Multi-school architecture (sub-wave)

Branch: `feature/postdeploy-e-multi-school`. Worktree: `MadhavPostE`. Budget cap: $800.

Per V.7 audit item: KP-vs-Lahiri concurrent multi-school assessment requires two separate planetary position tables. Currently one `ganita_positions` table per chart with a single ayanamsha; V1.3 architecture is **dual ayanamsha tables** so BPHS/Lahiri analysis and KP/stellar analysis can run simultaneously without overwriting each other.

### E sub-sessions (Conductor queue topology)

```yaml
sessions:
  - id: e1-schema-design
    role: Racayitā + Cowork adversarial review
    scope: |
      Design the dual-ayanamsha schema. Options:
        - Table-per-ayanamsha: ganita_positions_lahiri, ganita_positions_kp (clean isolation)
        - Discriminator column: ganita_positions with ayanamsha column + composite PK
      Decision: prefer discriminator column (composite PK on chart_id + body + date + ayanamsha)
      unless writer-side or query-side perf surfaces a reason to split.
    acceptance: schema design committed as 00_ARCHITECTURE/V1_3_MULTI_SCHOOL_SCHEMA.md

  - id: e2-migration
    depends_on: [e1-schema-design]
    scope: |
      Author + apply the migration that converts ganita_positions to its dual-ayanamsha shape.
      Existing rows get ayanamsha='lahiri' as the migration default.
    acceptance: migration applies clean; existing data preserved with default ayanamsha.

  - id: e3-writer-changes
    depends_on: [e2-migration]
    scope: |
      Update ganita.positions writer to emit rows for both Lahiri AND KP ayanamshas per
      chart-build. Ephemeris is invariant (tropical); only the sidereal projection differs.
    acceptance: a fresh chart-build produces 2× position row count (one per ayanamsha).

  - id: e4-l2-rederivation
    depends_on: [e3-writer-changes]
    scope: |
      Update bodha.signals derivation to consume ayanamsha-aware positions. Each signal
      now carries an `ayanamsha_context` field; signals derived from Lahiri positions
      carry 'lahiri', from KP carry 'kp'.
      Re-derive existing signals for the native's chart against both ayanamshas; produce
      2× signal count.
    acceptance: signals double in count for the test chart; ayanamsha_context populated.

  - id: e5-concordance-c3
    depends_on: [e4-l2-rederivation]
    scope: |
      Resolve the C3 concordance flag from WS-3 (KP-vs-Lahiri orthogonality).
      The concordance index now distinguishes "agree" vs "ayanamsha-system-dependent".
      Update mimamsa.concordance writer to flag rules whose conclusion changes across
      ayanamshas; surface as a separate concordance class.
    acceptance: C3 flag in WS-3 concordance moved from ORTHOGONAL to RESOLVED.

  - id: e-wave-close
    depends_on: [e5-concordance-c3]
    scope: PR + CI + auto-merge + tag.
    acceptance: tag `postdeploy-e-multi-school-v1-3`.
```

---

## §6 ACs (wave-complete across all 5 streams)

- AC-1: All 5 wave-close tags present
- AC-2: `rag_chunks ≥ 4,589` rows (Stream A)
- AC-3: Zero LEL citation text in `phala_anchors` notes (Stream B)
- AC-4: Migration squash schema-diff empty OR Stream C deferred-Docker entry in Smṛti (Stream C)
- AC-5: Zero HIGH drift findings (Stream D)
- AC-6: Multi-school dual-ayanamsha architecture live; C3 concordance flag resolved (Stream E)
- AC-7: Total run spend ≤ $2k absolute ceiling

## §7 Hard stops — none synchronous

Per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`. All exceptional events route through Tier-1 / Tier-2. Only Tier-3 (catastrophic-runaway $2k cap) emits async notification — and that's per-stream, so a single stream hitting the cap doesn't stop the other four.

## §8 must_not_touch (per-stream)

- Stream A → only DB ops + migrations; do not touch code outside `platform/supabase/migrations/`
- Stream B → only `platform/python-sidecar/phala/` writers + tests
- Stream C → no source-tree changes; verification only
- Stream D → only manifest + drift_detector config; do not touch governance source files
- Stream E → all of Brahma `ganita/` + `bodha/` + new migration; **MAY conflict with D if D touches manifest entries for these dirs** — Stream E waits 1 cycle for D to commit before touching the manifest

## §9 Out of post-deploy scope

| # | Item | Future arc |
|---|------|-----------|
| 1 | C2-001 STUB confidence inflation fix | V1.4 grounding engine (separate arc; the WS-2 §5 C2 finding tracks it) |
| 2 | M5-A prospective testing wake-up | post-V1.3 macro-phase per master arch |
| 3 | Learning multiplier movement from 1.0 scaffold | M5-A naturally drives this |
| 4 | Relational / Spatial modules | post-single-chart per master arch §I.4 |

---

*End of POSTDEPLOY_FIVE_STREAMS v1.0. Five parallel streams, one master paste, full AUTONOMY_RESILIENCE_PATTERN. Streams A–D close in hours; Stream E in a day or two; wave seal triggers `brahma-postdeploy-v1-3-complete`.*
