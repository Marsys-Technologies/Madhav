---
artifact: ROOT_FILE_POLICY.md
canonical_id: ROOT_FILE_POLICY
version: 1.0
status: CURRENT
authored_by: Claude (Cowork) 2026-05-04
purpose: >
  Governs where every file type belongs in the MARSYS-JIS project tree.
  Every Claude session must consult this before creating or placing any file
  at the project root or in a new location. Eliminates root-directory sprawl.
---

# MARSYS-JIS Root File Policy

## §1 — The Golden Rule

**Nothing lands at the project root unless it is explicitly listed in §2.**

Every other file — brief, report, image, script, plan, doc, prompt — goes into
the appropriate subfolder defined in §3. If no existing folder fits, use `99_ARCHIVE/`
and flag it for triage. Do not create new root-level files speculatively.

---

## §2 — Files that belong at the project root (exhaustive list)

| File | Reason |
|---|---|
| `CLAUDE.md` | Session orientation surface — must be at root per §C.1 |
| `CLAUDECODE_BRIEF.md` | Active session dispatcher — must be at root per §C.0; replaced at each session open |
| `BUILD.md` | Standard project build instructions |
| `cloudbuild.yaml` | GCP Cloud Build config — must be at root for `gcloud builds submit` |
| `.env.rag` | Environment variables for RAG pipeline |
| `.env.rag.example` | Template for the above |
| `.gcloudignore` | GCP deploy exclusions |
| `.gitignore` | Git exclusions |
| `.geminirules` | Gemini-side governance surface (mirror pair MP.1) |

Dot-folders (`.git`, `.github`, `.gemini`, `.vscode`, `.claude`, `.kilo`, `.tools`,
`.venv`, `.memory`, `.pytest_cache`, `.playwright-mcp`, `.continue`, `.superpowers`)
are tools/runtime state — they stay at root by convention, not by choice.

---

## §3 — Folder destinations by file type

### `00_ARCHITECTURE/` — Governance and architecture artifacts
Canonical governance documents, architecture plans, phase plans, session logs,
disagreement registers, capability manifests, policy files (including this one).

**Sub-folder `00_ARCHITECTURE/briefs/`** — Execution and session briefs
All `EXEC_BRIEF_*.md`, `CLAUDECODE_BRIEF_*.md` (historical, completed sessions),
migration prompts, verification briefs, working-aid prompts, runbooks, and
any other brief authored to drive a specific session or sprint.

Rule: once a session closes and its brief is no longer the active dispatcher,
move it to `00_ARCHITECTURE/briefs/`.

### `00_NAK/` — Project NAK artifacts
All files prefixed `NAK_*` — NAK briefs, exec briefs, design docs, trackers,
runbooks, SOPs, audit reports specific to the NAK sub-project.

### `01_FACTS_LAYER/` — L1 canonical facts
FORENSIC chart data, Life Event Log, and other L1 source-of-truth files.
No interpretations or derivations at this layer.

### `025_HOLISTIC_SYNTHESIS/` — L2.5 synthesis artifacts
MSR, UCN, CDLM, RM, CGM and other holistic synthesis documents.

### `035_DISCOVERY_LAYER/` — L3 discovery artifacts
Pattern register, resonance register, contradiction register, cluster atlas,
and related discovery-layer outputs.

### `03_DOMAIN_REPORTS/` — Domain-specific reports
Per-domain interpretive reports (career, relationships, health, etc.).

### `04_REMEDIAL_CODEX/` — Remedial codex
Remedial and corrective astrological texts and structured codex entries.

### `05_TEMPORAL_ENGINES/` — Temporal computation artifacts
Dasha engines, transit calculations, temporal animation outputs.

### `06_LEARNING_LAYER/` — Learning layer artifacts
Prediction logs, outcome records, calibration data, learning layer scaffolding.
Held-out data is sacrosanct — never expose outcome before prediction is logged.

### `99_ARCHIVE/` — Retired and superseded artifacts
Files that are explicitly retired, superseded, or no longer load-bearing.
Retain in place — do not delete. Mark with `status: ARCHIVED` or `SUPERSEDED`
in frontmatter. `.hold` files go here.

### `Assets/` — Static assets
`Assets/Logo.png` — project logo.
`Assets/screenshots/` — UI screenshots, build screenshots, QA captures.
Any image file that is not a deployed web asset goes here.
(Deployed web assets belong in `platform/public/`.)

### `docs/` — External tool configs and supplementary docs
Tool-specific config directories (e.g. `docs/superpowers/`).
Reference documents (`.docx`, `.pdf`) that are not canonical governance artifacts.

### `JHora/` — JHora software files
JHora chart exports and related files.

### `Plans/` — Informal planning notes
Lightweight planning documents that predate the formal governance structure.
New planning work should go into `00_ARCHITECTURE/` instead.

### `platform/` — Next.js application code
All application source code, migrations, scripts, tests, and platform config.
Nothing from the governance/corpus layer belongs inside `platform/`.

### `scripts/` — Data-processing scripts
Python or shell scripts used for data cleaning, migration prep, or one-off
corpus processing (e.g. `clean_msr.py`, `clean_cdlm.py`). Not application code.

### `verification_artifacts/` — Audit and smoke reports
Pipeline smoke audit reports, portal audit reports, data integrity reports,
verification briefs and findings, migration audit outputs.
Timestamped report files from `schema_validator.py` or `drift_detector.py`
belong here (though they are gitignored per project policy).

---

## §4 — Decision tree for new files

```
Is it the active session dispatcher?
  YES → CLAUDECODE_BRIEF.md at root (overwrite)
  NO ↓

Is it a canonical governance artifact (plan, registry, protocol, log)?
  YES → 00_ARCHITECTURE/
  NO ↓

Is it an execution brief, session prompt, or working aid?
  YES → 00_ARCHITECTURE/briefs/
  NO ↓

Is it an image or screenshot?
  YES → Assets/screenshots/
  NO ↓

Is it an audit report, smoke report, or verification finding?
  YES → verification_artifacts/
  NO ↓

Is it a data-processing script (.py, .sh)?
  YES → scripts/
  NO ↓

Is it a NAK sub-project file (NAK_* prefix)?
  YES → 00_NAK/
  NO ↓

Is it retired or superseded?
  YES → 99_ARCHIVE/
  NO ↓

Does it belong to a specific corpus layer (L1/L2.5/L3/domain/remedial/temporal)?
  YES → the appropriate layer folder (01_FACTS_LAYER, 025_HOLISTIC_SYNTHESIS, etc.)
  NO ↓

→ Flag it. Discuss with native before placing.
  Default holding location: 99_ARCHIVE/ with a TODO comment in frontmatter.
```

---

## §5 — What this policy does NOT cover

- Files inside `platform/` — governed by Next.js conventions and `platform/` structure.
- Files inside `.git*` dot-directories — git internals, hands off.
- Files inside `00_ARCHITECTURE/schema_reports/` — gitignored; local-only governance outputs.

---

## §6 — Logged root exceptions

A file placed at project root that does NOT appear in §2's exhaustive list is a policy violation
unless logged here with its authorizing directive and a removal/relocation plan. This section
exists so root exceptions are visible and time-bounded, not silently accreted.

| File | Authorized by | Reason | Disposition |
|---|---|---|---|
| `NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md` | Native directive, 2026-07-18 (D-3 closeout + D-4 staging, item 4) | One-time native-facing handoff artifact (blind date-tightening questionnaire for D-4's LEL corpus); root placement makes it immediately visible to the native without navigating the doctrine_waves briefs tree. Canonical copy lives at `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md` — the root copy is a delivery convenience, not a second source of truth. | Root copy to be removed once the native has retrieved/answered it (next session's hygiene sweep); canonical copy stays in the doctrine_waves folder permanently. |

---

*End of ROOT_FILE_POLICY v1.0 — authored 2026-05-04. §6 added 2026-07-18 (D-3 closeout
directive) — no prior exception-ledger section existed; created per the directive's
either/or instruction since neither an exception ledger nor a declared handoff folder existed.*
