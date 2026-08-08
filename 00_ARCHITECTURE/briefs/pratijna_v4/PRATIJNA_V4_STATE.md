# PRATIJÑĀ v4 Campaign Ledger

**Campaign:** PRATIJÑĀ v4 — Campaign B of the ratified MASTER PLAN.
**Plan of record:** `00_ARCHITECTURE/briefs/adhisthana/MASTER_PLAN_v1_0.md` §5 (governs this
campaign) + `V4_RUBRIC_SPEC_v1_0.md` (this campaign home) + `RUNG_P3_HAND_WORKED_v1_0.md` +
`A8_FACTOR_FACT_COVERAGE_MATRIX_v1_0.md` (both `00_ARCHITECTURE/briefs/adhisthana/`) +
`ADHISTHANA_STATE.md` (prior campaign's closed ledger, read for context).
**Integration branch:** `pratijna-v4/integration` (cut from `main` @ `4d725359b`, 2026-08-08).
**Conductor:** Sonnet 5 (Opus role per campaign spec — running as Sonnet 5 this session), this
session. Interactive: if interrupted, re-pasting the same governing prompt resumes from this
ledger.
**Status:** Stage 0 in progress (ratification record).

---

## Governing rulings (quoted per campaign instructions)

**R20 — AMENDMENT PROTOCOL.** v1.0 is immutable. A spec amendment is legitimate ONLY as: (1) blind
definition — rule + band + weight + citation authored and COMMITTED before its effect on any chart
is computed (CI check: the amendment doc's commit must precede any scoring run that includes it);
(2) applied only in a vNEXT engine version; (3) v1.0 and vNext scored SIDE BY SIDE on all charts,
both published; (4) adoption decided from the comparison + classical merit, recorded as a ruling.
Debates become measurements.

**R21 — REGISTRY HARMONIZATION** as per CHECKPOINT RECORD Decision 2. The karyatva registry
changes (a)(b)(c) are ratified blind (no scoring effect was computed for any of them) and belong in
v1.0's engine build.

**Standing (carried):** R13 absolute (PARĪKṢAKA audits every constant; any weight or rule
traceable to the native's outcomes = REFUSED) · R18 bounded rubric · R19 L1 sealed · R16
scope+detector citations · R14 measurement discipline (#1 permanent baseline; #2 superseded; this
campaign produces #3).

---

## Stage 0 — Ratification record (this session)

| Item | Detector | Result |
|---|---|---|
| `main` == `origin/main` | `git fetch origin main && git rev-parse main origin/main` | Both `4d725359b…` — MATCH |
| Integration branch cut | `git checkout -b pratijna-v4/integration main` | Done, from `4d725359b` |
| Campaign home created | `00_ARCHITECTURE/briefs/pratijna_v4/` | `V4_RUBRIC_SPEC_v1_0.md`, `CHECKPOINT_RECORD_v1_0.md`, this ledger |
| Spec ratified byte-identical | `diff` of bodies after frontmatter, v0.9 vs v1.0 | `BODY IDENTICAL` — verified via `awk`-extracted body diff, only frontmatter changed (version 0.9→1.0, status DRAFT→RATIFIED, `ratified_at` added) |
| Checkpoint record committed | this file + `CHECKPOINT_RECORD_v1_0.md`, verbatim from governing prompt | Done |

**Next:** commit these three files to `pratijna-v4/integration`, then open Lane B0 (registry
harmonization) in a fresh builder worktree.

---

## Roles + rails (unchanged from prior campaigns)

CONDUCTOR: orchestration, merge-train, ledger; no product code. BUILDERS (Sonnet ≤6, fresh
worktrees, TDD, lane PRs, deadlines). PARĪKṢAKA (Opus fresh per verdict; default-REFUTED;
mutation/negative-case/citation/R13/R16 standards; probes re-run at acceptance). ANTARYĀMIN (Opus
max; reversible rulings; hard-reserved items PARK). GATE-EXECUTOR (Opus fresh per gate; own-query
verification; pre-verifies static packet floors early). Isolation rail verbatim; hot files
conductor-only; migrations claim-at-PR-open; zero unpushed work at close; silence is not health;
queued ≠ merged.

## Lane status

| Lane | Description | Status |
|---|---|---|
| B0 | Registry harmonization (R21) | NOT STARTED |
| B1 | Chart Reader (thin selection API) | NOT STARTED — blocked on B0 |
| — | Rung P4 (reader ≡ probe_p2_tracer) | PENDING |
| B2 | The v4 engine (library) + writer | NOT STARTED — blocked on P4 |
| — | Rung P5 (offline grades vs P3 hand-worked numbers) | PENDING |
| — | Rung P6 (DB rows byte-agree with P5) | PENDING |
| B3 | Three-tier verification (snapshot fixture + property tests + CI) | NOT STARTED |
| B4 | Consumer audit (ph_nimitta, ka_*, mi_darshana, query_pratijna) | NOT STARTED |
| — | Rung P7 (one class through consumers) | PENDING |
| B5 | Gate + deploy + rebuild | NOT STARTED |
| — | Rung P8 (single-chart full acceptance, 482012f1 first) | PENDING |
| B6 | Measurement #3 (temporal skill, R15 event set) | NOT STARTED |
| B7 | Promise-layer scoreboard v0 | NOT STARTED |
| — | CLOSE | PENDING |

## DB access (verified pattern; never park on this)

```
DBURL=$(gcloud secrets versions access latest --secret=amjis-pipeline-db-url \
  | python3 -c "
import sys, urllib.parse as u
s=sys.stdin.read().strip(); p=u.urlsplit(s)
print(u.urlunsplit((p.scheme, f'{p.username}:{p.password}@127.0.0.1:5433', p.path, '', '')))
")
```
Never print credentials. ECONNREFUSED → restart proxy, continue:
```
nohup cloud-sql-proxy --address 127.0.0.1 --port 5433 \
  madhav-astrology:asia-south1:amjis-postgres &
```

## State at open (verified)

ADHIṢṬHĀNA merged to main: `chart_fact_identity` live (375,856 rows, 100% coverage, 3 charts) ·
graha/domain/event-class SSoTs adopted (removal-census enforced) · `brahma_ontology` complete
(varga class, storage-code synonyms) · probes P1/P2 green and committed under
`platform/scripts/probes/`. The old `bo_pratijna` v3 rows in production are STALE (broken-matcher
content) — known, this campaign replaces them.

**Note on stale worktrees:** `git worktree list` at session open shows several worktrees left over
from the ADHIṢṬHĀNA campaign (branches already merged to `main`, e.g. `lane/a2-graha-ssot`,
`adhisthana/lane-a6-gates`, etc.). Not cleaned up by this session — out of scope for PRATIJÑĀ v4
unless they collide with a lane branch name. Flagged for hygiene, not blocking.
